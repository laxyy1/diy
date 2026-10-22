"""Independent artifact checks. Return named failures; never repair inputs to pass."""
import csv,json,math,itertools,re
from collections import Counter
from pathlib import Path
import numpy as np
import cadquery as cq
import fitz
from .common import bbox,hardware_counts,inch,read_csv

SCOPES={
 'catalog':'Verifies exported IDs, dimensions and counts against independent product rules, not material grade or physical fit.',
 'geometry':'Verifies delivered CAD validity, bounds, analytic volumes and clashes; cannot establish strength or fabrication quality.',
 'connections':'Verifies referenced parts, nominal bore/screw paths and counted sites; does not assign fastener capacities.',
 'stock':'Verifies coverage, stock dimensions, kerf, end trims and arithmetic waste; assumes sound stock and is not an optimized saw sequence.',
 'document':'Verifies visible PDF data against schedules and unit conversion; human visual review is separate.'}

def segment_distance(a,b,c,d):
    """Closest separation of two finite line segments, including parallel axes."""
    a,b,c,d=map(lambda x:np.asarray(x,float),[a,b,c,d]);u=b-a;v=d-c;w=a-c
    aa=u@u;bb=u@v;cc=v@v;dd=u@w;ee=v@w;den=aa*cc-bb*bb
    candidates=[]
    if den>1e-12:
        s=(bb*ee-cc*dd)/den;t=(aa*ee-bb*dd)/den
        if 0<=s<=1 and 0<=t<=1:candidates.append(np.linalg.norm(w+s*u-t*v))
    for p,x,y in [(a,c,d),(b,c,d),(c,a,b),(d,a,b)]:
        vv=y-x;t=np.clip(((p-x)@vv)/(vv@vv),0,1);candidates.append(np.linalg.norm(p-x-t*vv))
    return float(min(candidates))

def validate(design,out,rules,include_cad=True):
    d=design.dimensions;checks=[]
    def test(id,ok,detail,category):
        checks.append(dict(id=id,passed=bool(ok),detail=detail,category=category,scope=SCOPES[category]))
    load=lambda name:json.loads((out/name).read_text())
    rows=load('cut_list.json');csvrows=read_csv(out/'cut_list.csv');index=load('parts.json')
    expected=rules.expected_ids(d);counts=rules.expected_counts(d);sizes=rules.expected_sizes(d)
    idxids=[p['id'] for p in index];groups=[r['id'] for r in rows]
    test('parts.unique_ids',len(idxids)==len(set(idxids)),str(idxids),'catalog')
    test('parts.expected_ids',set(idxids)==expected,f'missing {sorted(expected-set(idxids))}; unexpected {sorted(set(idxids)-expected)}','catalog')
    test('catalog.groups',len(groups)==len(set(groups)) and set(groups)==set(counts),'One row per designed group','catalog')
    test('catalog.cad_counts',Counter(p['group'] for p in index)==Counter(counts),'Part index group counts match product topology','catalog')
    for label,rr in [('json',rows),('csv',csvrows)]:
        valid=len(rr)==len(counts) and {r['id'] for r in rr}==set(counts)
        for r in rr:
            valid &= r['id'] in sizes and int(r['qty'])==counts.get(r['id'],-1)
            valid &= r['id'] in sizes and all(abs(float(r[k])-sizes[r['id']][i])<1e-5 for i,k in enumerate(['t','w','length']))
        test('catalog.'+label,valid,'Finished mm sizes and quantities independently checked','catalog')
    for part in index:
        g=part['group'];ok=g in sizes and all(abs(part['stock_dimensions'][k]-sizes[g][i])<1e-5 for i,k in enumerate(['t','w','length']))
        test('part.stock.'+part['id'],ok,'Each CAD component mapped to its cut-stock dimensions','catalog')
    cons=load('connections.json');hw=read_csv(out/'hardware.csv');steps=load('assembly_steps.json')
    expectedhw=rules.expected_hardware(d);actualhw=hardware_counts(cons)
    test('hardware.connection_recipe',dict(actualhw)==expectedhw,'Connection-site totals vs independent topology recipe','connections')
    test('hardware.csv',len(hw)==len(expectedhw) and {r['id']:int(r['quantity']) for r in hw}==expectedhw,'Exported hardware quantities vs connection sites and topology','connections')
    test('connections.unique',len(cons)==len({c['id'] for c in cons}),'No duplicate connection IDs','connections')
    test('connections.references',all(set(c['targets'])<=expected and c['targets'] for c in cons),'Every connection names existing component IDs','connections')
    stepids={s['id'] for s in steps};connectionids={c['id'] for c in cons}
    test('assembly.references',len(stepids)==len(steps) and all(set(s['parts'])<=expected and set(s['connection_ids'])<=connectionids for s in steps) and all(c['step'] in stepids for c in cons),'Step and connection references resolve uniquely','connections')
    uses=Counter(id for s in steps for id in s['connection_ids'])
    test('assembly.connection_coverage',uses==Counter({c['id']:1 for c in cons}),'Each connection is allocated to exactly one step','connections')
    test('assembly.part_coverage',set(p for s in steps for p in s['parts'])==expected,'Every component appears in an assembly step','connections')
    screws=load('screws.json');bad=[]
    for s in screws:
        embed=s['length']-s['through']
        if not 0<embed<s['receiver']:bad.append(s['id'])
    test('screws.tip_containment',not bad,f'Nominal tip containment; bad screws {bad}','connections')
    close=[]
    for a,b in itertools.combinations(screws,2):
        if not set(a['targets'])&set(b['targets']):continue
        end=lambda s:(np.array(s['start'])+np.array(s['axis'])*s['length']).tolist()
        sep=segment_distance(a['start'],end(a),b['start'],end(b))
        required=max((a['diameter']+b['diameter'])/2+1,design.parameters.get('design_rules',{}).get('min_axis_clearance',0))
        if sep<required:close.append([a['id'],b['id'],sep])
    test('screws.axis_clearance',not close,str(close),'connections')
    for id,ok,detail in rules.scalar_checks(d):test(id,ok,detail,'stock' if id=='brace.blank' else 'connections')
    layouts=load('cutting_layouts.json');stock=d['stock'];lumber=layouts['lumber'];sheets=layouts['plywood'];stockok=True
    coverage=Counter();stockgroups=rules.stock_groups(d)
    for b in lumber:
        last=stock['end_trim'];lengthsum=0
        for cut in b['cuts']:
            g=cut['group'];need=stockgroups['rough_lengths'].get(g,sizes[g][2])
            stockok &= cut['start']>=last-1e-6 and abs(cut['length']-need)<1e-6
            stockok &= b['t']>=sizes[g][0] and b['w']>=sizes[g][1]
            last=cut['start']+cut['length']+stock['kerf'];lengthsum+=cut['length'];coverage[g]+=1
        stockok &= last<=b['length']-stock['end_trim']+1e-6 and abs(b['length']-lengthsum-b['waste_length'])<1e-5 and b['length']==stock['board_length']
    test('stock.lumber',stockok,'Every blank, inter-cut kerf, end trim, section and residual length checked','stock')
    test('stock.lumber_coverage',coverage==Counter({g:counts[g] for g in stockgroups['lumber']}),'Every lumber part allocated once','stock')
    plyok=True;coverage=Counter();pieceids=[]
    for s in sheets:
        used=0
        for p in s['pieces']:
            coverage[p['group']]+=1;pieceids.append(p['id']);used+=p['length']*p['width']
            plyok &= abs(p['length']-sizes[p['group']][2])<1e-6 and abs(p['width']-sizes[p['group']][1])<1e-6
            plyok &= p['x']>=stock['end_trim'] and p['y']>=stock['end_trim'] and p['x']+p['length']<=s['length']-stock['end_trim']+1e-6 and p['y']+p['width']<=s['width']-stock['end_trim']+1e-6
        for a,b in itertools.combinations(s['pieces'],2):
            gx=max(a['x'],b['x'])-min(a['x']+a['length'],b['x']+b['length']);gy=max(a['y'],b['y'])-min(a['y']+a['width'],b['y']+b['width'])
            plyok &= max(gx,gy)>=stock['kerf']-1e-6
        plyok &= abs(s['length']*s['width']-used-s['waste_area_mm2'])<1e-5
        plyok &= abs(s['waste_area_mm2']/(s['length']*s['width'])-s['waste_fraction'])<1e-7
    test('stock.plywood',plyok,'Unrotated sheet bounds, piece dimensions, kerf separation and waste checked','stock')
    test('stock.plywood_coverage',coverage==Counter({g:counts[g] for g in stockgroups['sheet']}) and len(pieceids)==len(set(pieceids)),'Each plywood part allocated once, face grain follows span','stock')
    buy=read_csv(out/'purchasing.csv');buycounts={r['id']:int(r['quantity']) for r in buy}
    needbuy=dict(Counter(b['family'] for b in lumber));needbuy.update(PLY=len(sheets),**stockgroups['extra_purchases'])
    test('stock.purchasing',len(buy)==len(needbuy) and buycounts==needbuy,'Purchase quantities match boards, sheets and steel parts','stock')
    if include_cad:
        solids={};files=list((out/'cad/parts').glob('*.step'))
        test('cad.file_coverage',{p.stem for p in files}==expected and len(files)==len(expected),'One STEP file per distinct component ID','geometry')
        for file in files:
            try:
                ss=cq.importers.importStep(str(file)).val().Solids();s=ss[0];solids[file.stem]=s
                good=len(ss)==1 and s.isValid() and s.Volume()>0
                test('cad.valid.'+file.stem,good,'One valid positive solid after STEP read-back','geometry')
                if file.stem in expected:
                    bb=bbox(s);eb=rules.expected_bbox(d,file.stem);vol=rules.expected_volume(d,file.stem.split('-')[0])
                    test('cad.dimensions.'+file.stem,max(abs(a-b) for a,b in zip(bb,eb))<1e-5 and abs(s.Volume()-vol)<.02,
                      f'Bounds {bb}; volume residual {s.Volume()-vol:.8f} mm3 vs independent stock/bores/lap equations','geometry')
            except Exception as e:test('cad.valid.'+file.stem,False,str(e),'geometry')
        assembly=cq.importers.importStep(str(out/'cad/assembly.step')).val();assys=assembly.Solids()
        test('cad.assembly_count',len(assys)==sum(counts.values()),str(len(assys)),'geometry')
        test('cad.assembly_vs_parts',len(assys)==len(solids) and all(abs(a-b)<.02 for a,b in zip(sorted(s.Volume() for s in assys),sorted(s.Volume() for s in solids.values()))),'Assembly vs individual STEP volume multiset','geometry')
        clashes=[]
        for (ia,a),(ib,b) in itertools.combinations(solids.items(),2):
            ba,bb=bbox(a),bbox(b)
            if any(min(ba[j+3],bb[j+3])-max(ba[j],bb[j])<1e-5 for j in range(3)):continue
            if a.intersect(b).Volume()>.01:clashes.append([ia,ib])
        test('cad.intersections',not clashes,str(clashes),'geometry')
        from .cad import cyl
        paths=load('dowels.json');blocked=[];targetbad=[];contract=rules.expected_dowels(d)
        test('cad.dowel_site_contract',len(paths)==len(contract) and {p['id'] for p in paths}==set(contract) and all(p['id'] in contract and max(abs(a-b) for a,b in zip(p['start']+[p['radius'],p['length']],contract[p['id']]))<1e-6 for p in paths),'Unique bore IDs, positions, diameters and embeds vs independent mating-joint equations','connections')
        for p in paths:
            probe=cyl(*p['start'],*p['axis'],p['radius'],p['length'])
            for target in p['targets']:
                if target not in solids or solids[target].intersect(probe).Volume()>.01:blocked.append(p['id'])
            if p['id'] not in contract or abs(p['length']-contract[p['id']][-1])>1e-6:targetbad.append(p['id'])
        test('cad.dowel_paths',len(paths)==expectedhw['K1']+expectedhw['K2'] and not blocked and not targetbad,f'Nominal bore paths checked; blocked {blocked}','connections')
        missing=[];throughbad=[]
        for s in screws:
            if s['length']<=s['through']:missing.append(s['id']);continue
            entry=np.array(s['start'])+np.array(s['axis'])*s['through'];embed=s['length']-s['through']
            probe=cyl(*entry,*s['axis'],s['diameter']/2,embed)
            receiver=solids.get(s['targets'][1]);vol=probe.Volume()
            if receiver is None or abs(receiver.intersect(probe).Volume()-vol)>.02:missing.append(s['id'])
            first=s['targets'][0];group=next((p['group'] for p in index if p['id']==first),None)
            if group in stockgroups['lumber']+stockgroups['sheet']:
                attached=solids.get(first);body=cyl(*s['start'],*s['axis'],s['diameter']/2,s['through'])
                if attached is None or abs(attached.intersect(body).Volume()-body.Volume())>.02:throughbad.append(s['id'])
        test('cad.screw_receiving_paths',not missing,f'Full nominal shank envelope in receiving timber; unsupported paths {missing}','connections')
        test('cad.screw_attached_paths',not throughbad,f'Shank through attached wood; invalid paths {throughbad}; purchased washer/steel clearance holes excluded','connections')
    pdf=out/'manual.pdf'
    if pdf.exists():
        with fitz.open(pdf) as doc:text='\n'.join(p.get_text() for p in doc)
        group_pattern='|'.join(re.escape(g) for g in sorted(counts,key=lambda g:(-len(g),g)))
        rawhw=re.findall(r'\b(K\d+)\s*/\s*(\d+)\b',text);rawcuts=re.findall(r'\b('+group_pattern+r')\s*/\s*(\d+)\b',text)
        found={k:int(q) for k,q in rawhw};cuts={k:int(q) for k,q in rawcuts}
        test('pdf.hardware_table',len(rawhw)==len(expectedhw) and found==expectedhw,f'Unique visible ID / quantity rows: {found}','document')
        test('pdf.cut_table',len(rawcuts)==len(counts) and cuts==counts,f'Unique visible cut-list ID / quantity rows: {cuts}','document')
        entries=re.findall(r'\b('+group_pattern+r')\s*/\s*\d+\b(.*?)(?=\b(?:'+group_pattern+r')\s*/\s*\d+\b|$)',text,re.S)
        triples={}
        for group,body in entries:
            match=re.search(r'([\d.]+)\s*×\s*([\d.]+)\s*×\s*([\d.]+)\s*mm',body)
            if match:triples[group]=list(map(float,match.groups()))
        test('pdf.cut_dimensions',set(triples)==set(sizes) and all(max(abs(a-b) for a,b in zip(triples[g],sizes[g]))<=.0051 for g in triples),'Visible finished-size triples vs independent CAD/cut dimensions; 0.01 mm display rounding only','document')
        refs=set(re.findall(r'\b(?:'+group_pattern+r')-[A-Z0-9][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*\b',text))
        # Stock-family/blank IDs are a separate declared namespace, e.g. B-C and
        # F-1/F-2 sheet blanks which become F-F/F-R assembly components.
        stockids={b['id'] for b in lumber}|{b['family'] for b in lumber}|{p['id'] for s in sheets for p in s['pieces']}
        test('pdf.assembly_references',refs<=expected|stockids and expected<=refs,f'Visible component references with explicit stock-board IDs; unknown {sorted(refs-expected-stockids)}, missing {sorted(expected-refs)}','document')
        facts=rules.pdf_facts(d)
        measurements={k:float(v) for k,v in re.findall('('+'|'.join(re.escape(k) for k in facts)+r'):\s*([\d.]+)\s*mm',text)}
        test('pdf.dimensions',measurements==facts,str(measurements),'document')
        conversions=re.findall(r'([\d.]+)\s*mm\s*/\s*([\d.]+)\s*in',text)
        test('pdf.unit_conversions',len(conversions)>=10 and all(abs(float(mm)/25.4-float(ii))<=.00051 for mm,ii in conversions),f'{len(conversions)} visible conversions; 25.4 mm/in, 0.001 in display rounding','document')
        test('pdf.internal_report_separation','INDEPENDENT CHECKS' not in text and 'assumed_effective_E_MPa' not in text,'No internal test result or assumed load scenario advertised in customer manual','document')
    else:test('pdf.exists',False,'Customer manual not generated','document')
    return dict(passed=all(c['passed'] for c in checks),checks=checks,failed=[c['id'] for c in checks if not c['passed']],
      assumptions=['Physical timber, plywood properties, purchased fittings and wall construction unverified.','No physical prototype or load/stability/creep tests performed.','Passing digital checks does not establish safety or a safe working load.'])
