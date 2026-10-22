"""Render every page and detect clipping, unexpected text collisions and missing deliverables."""
from pathlib import Path
import fitz,json,itertools,hashlib
from PIL import Image,ImageDraw
from model import ROOT,OUT

def run():
    doc=fitz.open(OUT/'DIYWOODPLANNER_Alderline_X4.pdf');problems=[];collisions=[];thumbs=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5));pix.save(OUT/f'qa/page_{i+1:02d}.png')
        spans=[]
        for block in page.get_text('dict')['blocks']:
            if 'lines' not in block:continue
            for line in block['lines']:
                for span in line['spans']:
                    r=fitz.Rect(span['bbox']);spans.append((r,span['text']))
                    if r.x0<34 or r.x1>580 or r.y0<12 or r.y1>774:problems.append([i+1,span['text'],list(r)])
        for a,b in itertools.combinations(spans,2):
            intersection=a[0]&b[0]
            if intersection.width>3 and intersection.height>3:
                collisions.append([i+1,a[1],b[1],list(intersection)])
        if len(page.get_text())<200:problems.append([i+1,'Unexpected empty/near-empty page'])
        im=Image.open(OUT/f'qa/page_{i+1:02d}.png').convert('RGB');im.thumbnail((306,396));thumbs.append(im)
    contact=Image.new('RGB',(1224,416*4),'#ddd8cc');d=ImageDraw.Draw(contact)
    for i,im in enumerate(thumbs):
        x=i%4*306;y=i//4*416;contact.paste(im,(x,y));d.text((x+8,y+397),str(i+1),fill='black')
    contact.save(OUT/'qa/contact_sheet.png')
    for i,name in [(1,'dimensioned_elevations'),(4,'post_boring_map'),(5,'brace_fabrication'),(14,'exploded_assembly')]:
        (OUT/f'drawings/{name}.svg').write_text(doc[i].get_svg_image())
    import ezdxf
    pattern=ezdxf.readfile(OUT/'drawings/H_brace_1to1.dxf')
    assert pattern.units==4
    assert len(pattern.modelspace().query('LWPOLYLINE'))==2
    assert len(doc)==15
    report=dict(pages=len(doc),rendered_pages=len(thumbs),page_bounds_issues=problems,text_overlap_candidates=collisions,
       brace_DXF_units='mm',brace_pattern_closed_polylines=2,
       pdf_sha256=hashlib.sha256((OUT/'DIYWOODPLANNER_Alderline_X4.pdf').read_bytes()).hexdigest())
    (OUT/'qa/pdf_qa.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if problems or collisions:raise RuntimeError('Review detected PDF text issues')

if __name__=='__main__':run()
