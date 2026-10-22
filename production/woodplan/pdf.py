"""Reusable branded flow layout, CAD callouts, stock diagrams and PDF QA.

No furniture joinery rules. Content is supplied by product adapters.
"""
from pathlib import Path
import json,math,itertools
import fitz
from PIL import Image as PILImage,ImageDraw
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Flowable,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from .common import measure,metric,size,imperial_size,dump,sha

CREAM=HexColor('#faf7f1');GREEN=HexColor('#243d37');TEXT=HexColor('#34443f');PALE=HexColor('#e9ede4');WOOD=HexColor('#d8b98c');RUST=HexColor('#a55230')
for n,f in [('WP','DejaVuSans.ttf'),('WP-Bold','DejaVuSans-Bold.ttf'),('WP-Serif','DejaVuSerif.ttf')]:
    if n not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(n,'/usr/share/fonts/truetype/dejavu/'+f))
BODY=ParagraphStyle('body',fontName='WP',fontSize=9.2,leading=14,textColor=TEXT,spaceAfter=9)
SMALL=ParagraphStyle('small',parent=BODY,fontSize=8.0,leading=11,spaceAfter=4)
TITLE=ParagraphStyle('title',parent=BODY,fontName='WP-Serif',fontSize=25,leading=31,textColor=GREEN,spaceAfter=15)
SUB=ParagraphStyle('sub',parent=BODY,fontName='WP-Bold',fontSize=12,leading=17,textColor=GREEN,spaceAfter=10)

def P(text,style=BODY):return Paragraph(str(text).replace('\n','<br/>'),style)

class CADFigure(Flowable):
    def __init__(self,out,name,height=360,dimensions=False,labels=None):
        super().__init__();self.width=516;self.height=height;self.out=out;self.name=name;self.dimensions=dimensions;self.labels=labels or []
    def draw(self):
        c=self.canv;data=json.loads((self.out/'drawings/views.json').read_text())[self.name];p=data['projection']
        ih=self.height-65;iw=ih*p['width']/p['height'];ix=(self.width-iw)/2;iy=30
        # ImageReader makes PDF object IDs depend on pixels, not absolute paths.
        c.drawImage(ImageReader(str(self.out/f'drawings/{self.name}.png')),ix,iy,width=iw,height=ih)
        def point(v):
            xx=sum(a*b for a,b in zip(v,p['u']));yy=sum(a*b for a,b in zip(v,p['v']))
            px=(xx-p['mid'][0])*p['scale']+p['width']/2;py=p['height']/2-(yy-p['mid'][1])*p['scale']
            return ix+px/p['width']*iw,iy+(p['height']-py)/p['height']*ih
        c.setStrokeColor(GREEN);c.setFillColor(TEXT);c.setLineWidth(.55)
        if self.dimensions:
            for dim in data.get('dimensions',[]):
                x1,y1=point(dim['a']);x2,y2=point(dim['b']);label=measure(dim['value'])
                if dim['orientation']=='horizontal':
                    left,right=sorted([x1,x2]);yy=max(y1,y2)+17;c.line(left,y1,left,yy+3);c.line(right,y2,right,yy+3);c.line(left,yy,right,yy)
                    for xx in [left,right]:c.line(xx-2,yy-2,xx+2,yy+2)
                    tw=pdfmetrics.stringWidth(label,'WP',7.3);c.setFillColor(CREAM);c.rect((left+right-tw)/2-3,yy+2,tw+6,11,fill=1,stroke=0);c.setFillColor(TEXT);c.setFont('WP',7.3);c.drawCentredString((left+right)/2,yy+4,label)
                else:
                    xx=min(x1,x2)-22;c.line(xx,y1,xx,y2);c.line(x1,y1,xx-3,y1);c.line(x2,y2,xx-3,y2)
                    c.saveState();c.translate(xx-5,(y1+y2)/2);c.rotate(90);c.setFont('WP',7.3);c.drawCentredString(0,0,label);c.restoreState()
        if self.labels:
            records={r['id']:r for r in json.loads((self.out/'parts.json').read_text())}
            callouts=[]
            for id in self.labels:
                if id not in data['ids']:continue
                b=records[id]['bbox'];base=data.get('label_points',{}).get(id,[(b[j]+b[j+3])/2 for j in range(3)])
                v=[base[j]+data['offsets'].get(id,[0,0,0])[j] for j in range(3)];px,py=point(v)
                callouts.append((id,px,py))
            last={0:self.height-20,1:self.height-20}
            for id,px,py in sorted(callouts,key=lambda a:-a[2]):
                side=0 if px<self.width/2 else 1;yy=max(35,min(py,last[side]-23));last[side]=yy
                x=4 if side==0 else self.width-80
                hidden=id in data.get('hidden_callouts',[])
                c.setFont('WP-Bold',7.5);c.drawString(x,yy,id+(' (hidden)' if hidden else ''))
                if hidden:c.setDash(3,2)
                c.line(x+52 if side==0 else x-5,yy+2,px,py);c.circle(px,py,1.6,stroke=1,fill=0);c.setDash()

class StockFigure(Flowable):
    def __init__(self,record,plywood=False):
        super().__init__();self.record=record;self.plywood=plywood;self.width=516;self.height=225 if plywood else 36
    def draw(self):
        c=self.canv;r=self.record;c.setFont('WP-Bold',8);c.setFillColor(GREEN)
        if self.plywood:
            c.drawString(0,self.height-12,f'{r["id"]} / {measure(r["length"])} × {measure(r["width"])} / grain →')
            sc=min(510/r['length'],180/r['width']);ox=0;oy=18;c.setFillColor(PALE);c.rect(ox,oy,r['length']*sc,r['width']*sc,fill=1,stroke=0)
            for p in r['pieces']:
                x=ox+p['x']*sc;y=oy+(r['width']-p['y']-p['width'])*sc
                c.setFillColor(WOOD);c.setStrokeColor(GREEN);c.rect(x,y,p['length']*sc,p['width']*sc,fill=1,stroke=1);c.setFillColor(GREEN);c.setFont('WP',7);c.drawString(x+3,y+5,p['id'])
            c.setFont('WP',8);c.drawString(0,3,f'Geometric waste incl. kerf/trim/offcuts: {r["waste_fraction"]:.1%}. Map is not a saw sequence.')
        else:
            sc=510/r['length'];c.drawString(0,26,f'{r["id"]} / stock {metric(r["t"])} × {metric(r["w"])} × {metric(r["length"])} mm')
            c.setFillColor(PALE);c.rect(0,4,510,15,fill=1,stroke=0)
            for p in r['cuts']:
                x=p['start']*sc;c.setFillColor(WOOD);c.setStrokeColor(GREEN);c.rect(x,4,p['length']*sc,15,fill=1,stroke=1);c.setFillColor(GREEN);c.setFont('WP',6.7);c.drawString(x+3,9,f'{p["group"]} {metric(p["length"])}')

class Diagram(Flowable):
    """Adapter-supplied dimensioned geometry in normalized technical-sheet units."""
    def __init__(self,spec):super().__init__();self.spec=spec;self.width=516;self.height=spec['height']
    def draw(self):
        c=self.canv
        for r in self.spec.get('rects',[]):
            c.setStrokeColor(GREEN);c.setFillColor(WOOD);c.rect(*r,fill=1,stroke=1)
        for x,y,rad in self.spec.get('holes',[]):c.setFillColor(GREEN);c.circle(x,y,rad,fill=1,stroke=0)
        for x,y,s in self.spec.get('labels',[]):c.setFont('WP',8);c.setFillColor(TEXT);c.drawString(x,y,s)
        for xy in self.spec.get('lines',[]):c.setStrokeColor(GREEN);c.line(*xy)

def data_table(headers,rows,widths):
    heading=ParagraphStyle('th',parent=SMALL,textColor=white,fontName='WP-Bold')
    t=Table([[P(h,heading) for h in headers]]+[[P(v,SMALL) for v in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),GREEN),('ROWBACKGROUNDS',(0,1),(-1,-1),[PALE,CREAM]),
      ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,GREEN)]))
    return t

def build_manual(content,out):
    """Auto-pagination: no product-specific page limit or canvas text coordinates."""
    story=[]
    for section in content['sections']:
        if story:story.append(PageBreak())
        story.append(P(section['title'],TITLE))
        for item in section['items']:
            kind=item['type']
            if kind=='text':story.append(P(item['text']))
            elif kind=='sub':story.append(P(item['text'],SUB))
            elif kind=='figure':story.append(CADFigure(out,item['name'],item.get('height',360),item.get('dimensions',False),item.get('labels')))
            elif kind=='table':story.append(data_table(item['headers'],item['rows'],item['widths']))
            elif kind=='stock':story.append(StockFigure(item['record'],item.get('plywood',False)))
            elif kind=='diagram':story.append(Diagram(item['spec']))
            else:raise ValueError('Unsupported manual item: '+kind)
            story.append(Spacer(1,7))
    def decorate(c,doc):
        W,H=doc.pagesize;c.saveState();c.setFillColor(CREAM);c.rect(0,0,W,H,fill=1,stroke=0)
        c.setFillColor(GREEN);c.setFont('WP-Bold',10);c.drawString(42,H-35,'DIYWOODPLANNER');c.setFont('WP',8);c.drawRightString(W-42,H-35,content['short_title'])
        c.setStrokeColor(PALE);c.line(42,H-47,W-42,H-47);c.line(42,42,W-42,42)
        c.setFont('WP',7);c.drawString(42,28,'Prototype plan • Metric controls; inches rounded • No load rating');c.drawRightString(W-42,28,str(doc.page));c.restoreState()
    doc=SimpleDocTemplate(str(out/'manual.pdf'),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=70,bottomMargin=58,
      title=content['title'],author='DIYWOODPLANNER',invariant=1)
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)

def qa_pdf(pdf,out):
    """Bounds and span collisions plus full rasterization; not a human inspection."""
    out.mkdir(parents=True,exist_ok=True);doc=fitz.open(pdf);issues=[];overlaps=[];thumbs=[]
    for i,p in enumerate(doc):
        pix=p.get_pixmap(matrix=fitz.Matrix(1.4,1.4));pix.save(out/f'page_{i+1:02d}.png');spans=[]
        for b in p.get_text('dict')['blocks']:
            for line in b.get('lines',[]):
                for s in line['spans']:
                    r=fitz.Rect(s['bbox']);spans.append((r,s['text']))
                    if r.x0<28 or r.x1>p.rect.width-28 or r.y0<12 or r.y1>p.rect.height-12:issues.append([i+1,s['text'],list(r)])
        for a,b in itertools.combinations(spans,2):
            r=a[0]&b[0]
            if r.width>3 and r.height>3:overlaps.append([i+1,a[1],b[1]])
        im=PILImage.open(out/f'page_{i+1:02d}.png').convert('RGB');im.thumbnail((306,396));thumbs.append(im)
    # Separate sheets, at most eight thumbnails each, to remain inspectable.
    for start in range(0,len(thumbs),8):
        sheet=PILImage.new('RGB',(1224,832),'#ddd8cc');draw=ImageDraw.Draw(sheet)
        for j,im in enumerate(thumbs[start:start+8]):
            x=j%4*306;y=j//4*416;sheet.paste(im,(x,y));draw.text((x+6,y+399),str(start+j+1),fill='black')
        sheet.save(out/f'contact_{start//8+1:02d}.png')
    report=dict(passed=not issues and not overlaps,pages=len(doc),page_bounds_issues=issues,text_overlap_candidates=overlaps,pdf_sha256=sha(pdf),visual_review_status='pending',
      limitations='Automated bounds/collisions cannot establish drawing legibility or technical correctness; inspect rendered pages.')
    dump(out/'pdf_qa.json',report);return report
