"""Independent template areas, exact paper sizes, tile coverage and vector calibration."""
import json,math
import fitz,ezdxf
from reportlab.lib.pagesizes import A4,letter
from .common import polygon_area

def check_templates(out,expected_areas):
    checks=[]
    def add(id,ok,detail):checks.append(dict(id=id,passed=bool(ok),detail=detail,category='template',scope='Digital scale and coverage only; printer scaling and physical fit require ruler/scrap verification.'))
    doc=ezdxf.readfile(out/'drawings/brace_1to1.dxf');polys=list(doc.modelspace().query('LWPOLYLINE'))
    areas={p.dxf.layer:polygon_area([[v[0],v[1]] for v in p]) for p in polys}
    add('template.dxf',doc.units==4 and len(polys)==2 and all(p.closed for p in polys),'DXF mm; exactly two closed profile/lap polylines')
    add('template.analytic_area',abs(areas.get('PROFILE',0)-expected_areas['PROFILE'])<1e-5 and abs(areas.get('LAP',0)-expected_areas['LAP'])<1e-5,'DXF profile and rhombus areas vs independent equations')
    for paper,size in [('A4',A4),('Letter',letter)]:
        meta=json.loads((out/f'template_{paper}.json').read_text());pdf=fitz.open(out/f'template_{paper}.pdf')
        ok=len(pdf)==len(meta['tiles']) and abs(meta['scale_pt_per_mm']-72/25.4)<1e-10
        bars=True
        for p in pdf:
            ok &= abs(p.rect.width-size[0])<.01 and abs(p.rect.height-size[1])<.01
            lengths=[]
            for drawing in p.get_drawings():
                for item in drawing['items']:
                    if item[0]=='l':
                        a,b=item[1:];lengths.append((abs(a.x-b.x),abs(a.y-b.y)))
            bars &= any(abs(dx-100*72/25.4)<.01 and dy<.01 for dx,dy in lengths) and any(abs(dy-50*72/25.4)<.01 and dx<.01 for dx,dy in lengths)
        add('template.paper_scale.'+paper,ok and bars,'Page dimensions and actual PDF vector 100/50 mm calibration bars checked')
        tiles=meta['tiles'];coverage=max(t['x0_mm']+t['width_mm'] for t in tiles)>=meta['pattern_extent_mm'][0] and max(t['y0_mm']+t['height_mm'] for t in tiles)>=meta['pattern_extent_mm'][1]
        for row in set(t['row'] for t in tiles):
            rowtiles=sorted([t for t in tiles if t['row']==row],key=lambda t:t['col'])
            coverage &= rowtiles[0]['x0_mm']==0
            for a,b in zip(rowtiles,rowtiles[1:]):coverage &= abs(a['x0_mm']+a['width_mm']-b['x0_mm']-meta['overlap_mm'])<1e-7
        for col in set(t['col'] for t in tiles):
            coltiles=sorted([t for t in tiles if t['col']==col],key=lambda t:t['row']);coverage &= coltiles[0]['y0_mm']==0
            for a,b in zip(coltiles,coltiles[1:]):coverage &= abs(a['y0_mm']+a['height_mm']-b['y0_mm']-meta['overlap_mm'])<1e-7
        add('template.coverage.'+paper,coverage and meta['overlap_mm']>0,'Tile union covers profile; overlaps and start coordinates agree')
    return checks
