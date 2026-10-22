#!/usr/bin/env python3
"""Run the Codex production pipeline. A filesystem CLI, not an application/API."""
import argparse,json,os,sys
from pathlib import Path
os.environ.setdefault('XDG_CACHE_HOME','/tmp/woodplanner-cache')
from woodplan.common import dump,preserve_p1,sha
from woodplan.export import export_design
from woodplan.pdf import build_manual,qa_pdf
from woodplan.validate import validate
from woodplan.template_checks import check_templates
from woodplan.products import alderline,alderline_checks,alderline_manual,alderline_drawings

REPO=Path(__file__).resolve().parents[1]

def run(config,out):
    out=Path(out).resolve();config=Path(config).resolve()
    if preserve_p1(REPO):raise RuntimeError('P1 preservation check failed before production')
    if out.is_relative_to(REPO/'deliverables'):raise ValueError('Original deliverables are protected; choose a new production output directory.')
    if out.exists():raise FileExistsError('Output directory exists; choose a new path rather than overwrite it: '+str(out))
    p=json.loads(config.read_text())
    if p.get('product_type')!='alderline_x4':raise ValueError('No adapter for this product type. Create and review a separate model.')
    design=alderline.build(p);out.mkdir(parents=True)
    import importlib.metadata
    sources=sorted((REPO/'production/woodplan').rglob('*.py'))+[Path(__file__).resolve()]
    dump(out/'provenance.json',dict(parameters_sha256=sha(config),source_sha256={str(p.relative_to(REPO)):sha(p) for p in sources},
       dependencies={name:importlib.metadata.version(name) for name in ['cadquery','reportlab','numpy','Pillow','PyMuPDF','ezdxf']}))
    print('CAD and schedules:',out,flush=True);layouts=export_design(design,out)
    print('Drawings and fabrication templates',flush=True);alderline_drawings.generate(design,out)
    print('Customer manual',flush=True);build_manual(alderline_manual.content(design,out,layouts),out)
    print('Artifact validation and PDF rendering',flush=True);report=validate(design,out,alderline_checks)
    templates=check_templates(out,alderline_checks.template_areas(design.dimensions));report['checks'].extend(templates)
    report['failed']=[c['id'] for c in report['checks'] if not c['passed']];report['passed']=not report['failed']
    qas={'manual':qa_pdf(out/'manual.pdf',out/'qa/manual')}
    for paper in ['A4','Letter']:qas[paper]=qa_pdf(out/f'template_{paper}.pdf',out/f'qa/template_{paper}')
    dump(out/'validation.json',report);dump(out/'engineering_assumptions.json',alderline.engineering(design.dimensions));dump(out/'qa/summary.json',qas)
    if preserve_p1(REPO):raise RuntimeError('P1 preservation check failed after production')
    md='# Internal production validation\n\n'+('PASS' if report['passed'] else 'FAIL')+f' / {len(report["checks"])} checks. Digital checks do not prove safety.\n\n'
    for c in report['checks']:md+=f'- {"PASS" if c["passed"] else "FAIL"} `{c["id"]}` — {c["detail"]}. Scope: {c["scope"]}\n'
    md+='\n## Engineering and release limitations\n\n'+''.join('- '+s+'\n' for s in report['assumptions'])
    md+='\nSee engineering_assumptions.json for the assumed E, UDL equations and width-dependent results. These are illustrative calculations, not structural acceptance tests. See docs/COMMERCIAL_RELEASE.md for human/physical gates.\n'
    md+='\n## Document review\n\nAll pages rendered. Automated QA reports are in qa/. Human visual review is pending until recorded in the reviewed output reports; no page count maximum is enforced.\n'
    (out/'INTERNAL_VALIDATION.md').write_text(md)
    print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'failed':report['failed'],'pdf_qa':{k:v['passed'] for k,v in qas.items()},'manual_pages':qas['manual']['pages']},indent=2),flush=True)
    return report,qas

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--config',required=True,type=Path);a.add_argument('--out',required=True,type=Path);args=a.parse_args()
    report,qas=run(args.config,args.out)
    sys.exit(0 if report['passed'] and all(q['passed'] for q in qas.values()) else 1)
