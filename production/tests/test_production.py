"""Deterministic regressions and explicit fault injections against real artifacts.

Run after both example builds: python -m unittest discover -s production/tests -v
Every mutant is a disposable COPY. P1 and checked-in examples are never edited.
"""
import unittest,json,csv,copy,shutil,tempfile,sys,math
from pathlib import Path
import fitz,cadquery as cq
import ezdxf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from woodplan.common import dump,preserve_p1,sha,measure,read_csv
from woodplan.products import alderline,alderline_checks,alderline_manual
from woodplan.validate import validate,segment_distance
from woodplan.template_checks import check_templates
from woodplan.stock import plywood_layout
from woodplan.pdf import build_manual

REPO=Path(__file__).resolve().parents[2];BASE=REPO/'production/examples/alderline_900';WIDE=REPO/'production/examples/alderline_1000'

class ProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((REPO/'production/configs/alderline_900.json').read_text());cls.design=alderline.build(cls.config)
    def mutant(self):
        t=tempfile.TemporaryDirectory(prefix='woodplan-negative-');self.addCleanup(t.cleanup)
        path=Path(t.name)/'copy';shutil.copytree(BASE,path);return path
    def load(self,path,name):return json.loads((path/name).read_text())
    def result(self,path,cad=False):return validate(self.design,path,alderline_checks,include_cad=cad)
    def detects(self,result,id):
        self.assertFalse(result['passed']);self.assertIn(id,result['failed'])
    def csv_mutate(self,path,name,field,id,value):
        rows=read_csv(path/name);next(r for r in rows if r['id']==id)[field]=value
        with (path/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    def test_01_p1_files_unchanged(self):self.assertEqual(preserve_p1(REPO),[])
    def test_02_original_run_all_checks_pass(self):
        r=self.load(BASE,'validation.json');self.assertTrue(r['passed'],r['failed']);self.assertGreater(len(r['checks']),100)
    def test_03_original_cut_list_regression(self):
        old=read_csv(REPO/'deliverables/DIYWOODPLANNER_Alderline_X4/output/cut_list.csv');new=self.load(BASE,'cut_list.json')
        self.assertEqual([r['id'] for r in old],[r['id'] for r in new])
        for a,b in zip(old,new):
            for k in ['qty','t','w','length']:self.assertAlmostEqual(float(a[k]),b[k],places=6)
    def test_04_original_step_regression(self):
        a=cq.importers.importStep(str(REPO/'deliverables/DIYWOODPLANNER_Alderline_X4/output/cad/Alderline_X4.step')).val().Solids()
        b=cq.importers.importStep(str(BASE/'cad/assembly.step')).val().Solids();self.assertEqual(len(a),len(b))
        for x,y in zip(sorted(s.Volume() for s in a),sorted(s.Volume() for s in b)):self.assertAlmostEqual(x,y,places=2)
        old=self.load(REPO/'deliverables/DIYWOODPLANNER_Alderline_X4/output','cad/assembly_mesh.json');new={r['id']:r for r in self.load(BASE,'parts.json')}
        for m in old:
            vertices=m['vertices'];bb=[min(v[j] for v in vertices) for j in range(3)]+[max(v[j] for v in vertices) for j in range(3)]
            for a,b in zip(bb,new[m['id']]['bbox']):self.assertAlmostEqual(a,b,places=5)
    def test_05_width_1000_regression(self):
        r=self.load(WIDE,'validation.json');self.assertTrue(r['passed'],r['failed']);d=self.load(WIDE,'dimensions.json')
        for k,v in dict(frame_width=1000,opening=910,shelf_width=909,top_width=1020,side_overall_width=1036).items():self.assertEqual(d[k],v)
        self.assertEqual(d['shelf_screw_x'],[60,940]);self.assertEqual(d['angle_x'],[272.5,727.5])
        a=read_csv(BASE/'hardware.csv');b=read_csv(WIDE/'hardware.csv');self.assertEqual(a,b)
        self.assertGreater(self.load(WIDE,'engineering_assumptions.json')['instantaneous_deflection_mm'],self.load(BASE,'engineering_assumptions.json')['instantaneous_deflection_mm'])
        for paper in ['A4','Letter']:self.assertEqual(sha(BASE/f'template_{paper}.pdf'),sha(WIDE/f'template_{paper}.pdf'))
    def test_06_two_deterministic_validation_runs(self):self.assertEqual(self.result(BASE),self.result(BASE))
    def test_07_unit_conversion_exact_definition(self):
        self.assertEqual(measure(25.4),'25.4 mm / 1.000 in');self.assertEqual(measure(0),'0 mm / 0.000 in')
    def test_08_stock_layout_deterministic_and_one_sheet(self):
        d=self.design.dimensions;a=plywood_layout(self.design.catalog,d['stock']);b=plywood_layout(self.design.catalog,d['stock'])
        self.assertEqual(a,b);self.assertEqual(len(a),1)
    def test_09_bad_hardware_csv_detected(self):
        p=self.mutant();self.csv_mutate(p,'hardware.csv','quantity','K3','25');self.detects(self.result(p),'hardware.csv')
    def test_10_missing_connection_detected(self):
        p=self.mutant();c=self.load(p,'connections.json');index=next(i for i,row in enumerate(c) if 'K3' in row['hardware']);c.pop(index);dump(p/'connections.json',c)
        self.detects(self.result(p),'hardware.connection_recipe')
    def test_11_duplicate_part_detected(self):
        p=self.mutant();rows=self.load(p,'parts.json');rows.append(copy.deepcopy(rows[0]));dump(p/'parts.json',rows)
        self.detects(self.result(p),'parts.unique_ids')
    def test_12_missing_component_detected(self):
        p=self.mutant();rows=self.load(p,'parts.json');rows.pop();dump(p/'parts.json',rows);self.detects(self.result(p),'parts.expected_ids')
    def test_13_bad_cut_dimension_detected(self):
        p=self.mutant();self.csv_mutate(p,'cut_list.csv','length','D','819');self.detects(self.result(p),'catalog.csv')
    def test_14_invalid_units_rejected(self):
        p=copy.deepcopy(self.config);p['units']='in';self.assertRaisesRegex(ValueError,'millimetres',alderline.derive,p)
    def test_15_collapsed_geometry_rejected(self):
        p=copy.deepcopy(self.config);p['frame_width']=80;self.assertRaisesRegex(ValueError,'collapsed',alderline.derive,p)
    def test_16_nonfinite_geometry_rejected(self):
        p=copy.deepcopy(self.config);p['height']=float('nan');self.assertRaisesRegex(ValueError,'positive dimension',alderline.derive,p)
    def test_17_broken_assembly_reference_detected(self):
        p=self.mutant();s=self.load(p,'assembly_steps.json');s[0]['parts'].append('A-NOT-A-PART');dump(p/'assembly_steps.json',s);self.detects(self.result(p),'assembly.references')
    def test_18_wrong_purchase_quantity_detected(self):
        p=self.mutant();self.csv_mutate(p,'purchasing.csv','quantity','A','3');self.detects(self.result(p),'stock.purchasing')
    def test_19_missing_lumber_kerf_detected(self):
        p=self.mutant();s=self.load(p,'cutting_layouts.json');b=next(b for b in s['lumber'] if len(b['cuts'])>1)
        b['cuts'][1]['start']=b['cuts'][0]['start']+b['cuts'][0]['length'];dump(p/'cutting_layouts.json',s);self.detects(self.result(p),'stock.lumber')
    def test_20_overlapping_plywood_detected(self):
        p=self.mutant();s=self.load(p,'cutting_layouts.json');a,b=s['plywood'][0]['pieces'][:2];b['x'],b['y']=a['x'],a['y'];dump(p/'cutting_layouts.json',s);self.detects(self.result(p),'stock.plywood')
    def test_21_overlength_screw_detected(self):
        p=self.mutant();s=self.load(p,'screws.json');s[0]['length']=100;dump(p/'screws.json',s);self.detects(self.result(p),'screws.tip_containment')
    def test_22_wrong_template_scale_detected(self):
        p=self.mutant();meta=self.load(p,'template_A4.json');meta['scale_pt_per_mm']=1;dump(p/'template_A4.json',meta)
        self.assertFalse(next(c for c in check_templates(p,alderline_checks.template_areas(self.design.dimensions)) if c['id']=='template.paper_scale.A4')['passed'])
    def test_23_wrong_dxf_units_detected(self):
        p=self.mutant();d=ezdxf.readfile(p/'drawings/brace_1to1.dxf');d.units=1;d.saveas(p/'drawings/brace_1to1.dxf')
        self.assertFalse(next(c for c in check_templates(p,alderline_checks.template_areas(self.design.dimensions)) if c['id']=='template.dxf')['passed'])
    def replace_pdf_text(self,p,needle,replacement):
        doc=fitz.open(p/'manual.pdf');done=False
        for page in doc:
            boxes=page.search_for(needle)
            if boxes:
                rect=boxes[0];page.add_redact_annot(rect,fill=(1,1,1));page.apply_redactions();page.insert_text((rect.x0,rect.y1-2),replacement,fontsize=8);done=True;break
        self.assertTrue(done);doc.save(p/'mutated.pdf');doc.close();(p/'mutated.pdf').replace(p/'manual.pdf')
    def test_24_wrong_pdf_hardware_detected(self):
        p=self.mutant();self.replace_pdf_text(p,'K4 / 16','K4 / 99');self.detects(self.result(p),'pdf.hardware_table')
    def test_25_wrong_pdf_conversion_detected(self):
        p=self.mutant();self.replace_pdf_text(p,'Frame width: 900 mm / 35.433 in','Frame width: 900 mm / 99.999 in');self.detects(self.result(p),'pdf.unit_conversions')
    def test_26_missing_step_file_detected(self):
        p=self.mutant();(p/'cad/parts/A-LF.step').unlink();self.detects(self.result(p,True),'cad.file_coverage')
    def test_27_actual_cad_collision_detected(self):
        p=self.mutant();file=p/'cad/parts/A-LF.step';s=cq.importers.importStep(str(file)).val();cq.exporters.export(s.translate((10,0,0)),str(file));r=self.result(p,True)
        self.detects(r,'cad.intersections');self.assertIn('cad.dimensions.A-LF',r['failed'])
    def test_28_pdf_build_deterministic(self):
        p=self.mutant();before=sha(p/'manual.pdf');build_manual(alderline_manual.content(self.design,p,self.load(p,'cutting_layouts.json')),p);self.assertEqual(sha(p/'manual.pdf'),before)
    def test_29_no_internal_report_in_customer_manual(self):
        for folder in [BASE,WIDE]:
            doc=fitz.open(folder/'manual.pdf');text='\n'.join(p.get_text() for p in doc)
            self.assertNotIn('24 OF 24',text);self.assertNotIn('instantaneous_deflection_mm',text);self.assertIn('No safe working load',text)
    def test_30_segment_distance_independent_examples(self):
        self.assertEqual(segment_distance([0,0,0],[10,0,0],[5,-5,0],[5,5,0]),0)
        self.assertEqual(segment_distance([0,0,0],[10,0,0],[0,3,0],[10,3,0]),3)
    def test_31_all_final_pdf_qa_pass(self):
        for folder in [BASE,WIDE]:
            for q in self.load(folder,'qa/summary.json').values():self.assertTrue(q['passed']);self.assertGreater(q['pages'],0)
    def test_32_wrong_dowel_position_detected(self):
        p=self.mutant();paths=self.load(p,'dowels.json');paths[0]['start'][2]+=1;dump(p/'dowels.json',paths)
        r=self.result(p,True);self.detects(r,'cad.dowel_paths');self.assertIn('cad.dowel_site_contract',r['failed'])
    def test_33_missing_template_tile_detected(self):
        p=self.mutant();meta=self.load(p,'template_A4.json');meta['tiles'].pop(1);dump(p/'template_A4.json',meta)
        self.assertFalse(next(c for c in check_templates(p,alderline_checks.template_areas(self.design.dimensions)) if c['id']=='template.coverage.A4')['passed'])
    def test_34_duplicate_pdf_hardware_row_detected(self):
        p=self.mutant();doc=fitz.open(p/'manual.pdf');doc[-1].insert_text((42,650),'K1 / 40',fontsize=8);doc.save(p/'mutated.pdf');doc.close();(p/'mutated.pdf').replace(p/'manual.pdf')
        self.detects(self.result(p),'pdf.hardware_table')
    def test_35_provenance_matches_executed_sources(self):
        for folder in [BASE,WIDE]:
            for file,digest in self.load(folder,'provenance.json')['source_sha256'].items():self.assertEqual(sha(REPO/file),digest)
    def test_36_unknown_pdf_part_reference_detected(self):
        p=self.mutant();doc=fitz.open(p/'manual.pdf');doc[-1].insert_text((42,650),'A-Z99',fontsize=8);doc.save(p/'mutated.pdf');doc.close();(p/'mutated.pdf').replace(p/'manual.pdf')
        self.detects(self.result(p),'pdf.assembly_references')
    def test_37_wrong_pdf_cut_dimension_detected(self):
        p=self.mutant();self.replace_pdf_text(p,'18 × 348 × 809 mm','18 × 348 × 819 mm');self.detects(self.result(p),'pdf.cut_dimensions')
    def test_38_configured_minimum_screw_spacing_enforced(self):
        p=self.mutant();design=copy.copy(self.design);design.parameters=copy.deepcopy(design.parameters);design.parameters['design_rules']['min_axis_clearance']=100
        self.detects(validate(design,p,alderline_checks,include_cad=False),'screws.axis_clearance')

if __name__=='__main__':unittest.main(verbosity=2)
