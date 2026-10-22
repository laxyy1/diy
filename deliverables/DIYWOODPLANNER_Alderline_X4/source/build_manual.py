"""Compose the original English woodworking manual. Drawings use model parameters."""
from pathlib import Path
import json, math, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from model import D, ROOT, OUT, schedule, HARDWARE, brace_poly
import hashlib
# Narrative and joint instructions are release-controlled. A geometric variant must
# receive an editorial/technical review rather than silently keeping stale prose.
P1_PARAMETER_SHA256='e4255b2a6a0abe28afab4884dfb912c2bbe10c4d3a4d7e8b9b57f2a77c720084'
if hashlib.sha256((ROOT/'source/parameters.json').read_bytes()).hexdigest()!=P1_PARAMETER_SHA256:
    raise RuntimeError('P1 parameters changed: revise and review the manual prose/annotations before issuing a new manual; then update the release hash.')

for name,file in [('Sans','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf'),('Serif','DejaVuSerif.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
INK=HexColor('#243d37');TEXT=HexColor('#34443f');MUTED=HexColor('#64716a');PAPER=HexColor('#faf7f1');TAN=HexColor('#d8b98c');LINE=HexColor('#d4d7ca');RUST=HexColor('#a55230');PALE=HexColor('#e9ede4')
W,H=612,792;M=42
c=canvas.Canvas(str(OUT/'DIYWOODPLANNER_Alderline_X4.pdf'),pagesize=(W,H))
c.setTitle('Alderline X4 | Four-shelf X-frame bookshelf | DIYWOODPLANNER')
c.setAuthor('DIYWOODPLANNER')
page_no=0; text_boxes=[]

def txt(x,y,s,size=10,font='Sans',color=TEXT):
    c.setFillColor(color);c.setFont(font,size);c.drawString(x,y,s)
    text_boxes.append((page_no,x,y,pdfmetrics.stringWidth(s,font,size),size,s))

def para(x,y,s,width=528,size=10,leading=15,color=TEXT,font='Sans'):
    # Explicit breaks create paragraphs; wrap by font metrics, not character count.
    for paragraph in s.split('\n'):
        words=paragraph.split();line=''
        for word in words:
            cand=(line+' '+word).strip()
            if pdfmetrics.stringWidth(cand,font,size)>width and line:
                txt(x,y,line,size,font,color);y-=leading;line=word
            else:line=cand
        if line:txt(x,y,line,size,font,color);y-=leading
        y-=4
    return y

def rect(x,y,w,h,fill=PALE,stroke=None):
    c.setFillColor(fill);c.setStrokeColor(stroke or fill);c.rect(x,y,w,h,stroke=bool(stroke),fill=1)

def line(x1,y1,x2,y2,color=LINE,width=.7):
    c.setStrokeColor(color);c.setLineWidth(width);c.line(x1,y1,x2,y2)

def page(kicker,title,subtitle=None):
    global page_no
    if page_no:c.showPage()
    page_no+=1;rect(0,0,W,H,PAPER)
    txt(M,758,'DIYWOODPLANNER',10,'Bold',INK)
    c.setFont('Sans',8);c.setFillColor(MUTED);c.drawRightString(570,758,'ALDERLINE X4  /  P1')
    line(M,745,570,745)
    txt(M,723,kicker.upper(),8,'Bold',RUST)
    txt(M,690,title,25,'Serif',INK)
    if subtitle:para(M,668,subtitle,size=9.5,leading=14,color=MUTED)
    line(M,42,570,42)
    txt(M,27,'P1 PROTOTYPE REVIEW  •  Metric dimensions control  •  Not a load rating',7,'Sans',MUTED)
    txt(548,27,f'{page_no:02d}',8,'Bold',INK)

def image(name,x,y,w,h):
    c.drawImage(str(OUT/'drawings'/f'{name}.png'),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')

def badge(x,y,num,title,body,width=250):
    rect(x,y-3,24,24,INK);txt(x+7,y+4,str(num),11,'Bold',white)
    txt(x+34,y+5,title,11,'Bold',INK)
    return para(x+34,y-14,body,width-34,9.4,14)

def note(x,y,title,body,w=528):
    c.setFillColor(RUST);c.rect(x,y-4,3,42,fill=1,stroke=0)
    txt(x+12,y+24,title,9,'Bold',RUST)
    return para(x+12,y+8,body,w-20,9,13)

def dim(x1,y1,x2,y2,label,offset=15,size=8):
    # Horizontal/vertical dimension with outward extension lines.
    if abs(y2-y1)<1e-6:
        yy=y1+offset;line(x1,y1,x1,yy+4,MUTED,.5);line(x2,y2,x2,yy+4,MUTED,.5);line(x1,yy,x2,yy,MUTED,.6)
        for x,sign in [(x1,1),(x2,-1)]:
            line(x,yy,x+sign*4,yy+2,MUTED);line(x,yy,x+sign*4,yy-2,MUTED)
        tw=pdfmetrics.stringWidth(label,'Sans',size);rect((x1+x2-tw)/2-3,yy+2,tw+6,size+3,PAPER);txt((x1+x2-tw)/2,yy+4,label,size)
    else:
        xx=x1+offset;line(x1,y1,xx+4,y1,MUTED,.5);line(x2,y2,xx+4,y2,MUTED,.5);line(xx,y1,xx,y2,MUTED,.6)
        for y,sign in [(y1,1),(y2,-1)]:
            line(xx,y,xx+2,y+sign*4,MUTED);line(xx,y,xx-2,y+sign*4,MUTED)
        c.saveState();c.translate(xx-4,(y1+y2)/2);c.rotate(90);c.setFont('Sans',size);c.setFillColor(TEXT);c.drawCentredString(0,0,label);c.restoreState()

def poly(points,fill=TAN,stroke=INK):
    p=c.beginPath();p.moveTo(*points[0])
    for a in points[1:]:p.lineTo(*a)
    p.close();c.setFillColor(fill);c.setStrokeColor(stroke);c.setLineWidth(.55);c.drawPath(p,fill=1,stroke=1)

def front(x,y,s=.22,rear=False,dims=False):
    def r(a,b,w,h,col=TAN):rect(x+a*s,y+b*s,w*s,h*s,col,INK)
    if not rear:
        for a,b in [((D['post']/2,D['strap_bottom_z']),(D['frame_width']-D['post']/2,D['strap_top_z'])),((D['frame_width']-D['post']/2,D['strap_bottom_z']),(D['post']/2,D['strap_top_z']))]:
            line(x+a[0]*s,y+a[1]*s,x+b[0]*s,y+b[1]*s,MUTED,1)
    for xx in [-D['brace_thickness'],D['frame_width']]:
        r(xx,D['brace_z_stations'][0],D['brace_thickness'],D['brace_z_stations'][-1]-D['brace_z_stations'][0],HexColor('#c59f6e'))
    for xx in [0,D['frame_width']-D['post']]:r(xx,0,D['post'],D['post_length'])
    for z in D['rail_bottoms']:r(D['post']+.5,z+D['rail_height'],D['shelf_width'],18,HexColor('#e1cba8'))
    r(45,D['top_rail_bottom'],810,D['top_rail_height'])
    r(-10,D['post_length'],D['top_width'],18,HexColor('#e1cba8'))
    if rear:
        for a,b in [((22.5,125),(877.5,1725)),((877.5,125),(22.5,1725))]:
            line(x+a[0]*s,y+a[1]*s,x+b[0]*s,y+b[1]*s,INK,2)
            for xx,zz in [a,b]:c.setFillColor(white);c.circle(x+xx*s,y+zz*s,2,fill=1,stroke=0)
    if dims:
        dim(x-10*s,y+1800*s,x+910*s,y+1800*s,'920 top',18)
        dim(x-18*s,y+1800*s,x+918*s,y+1800*s,'936 maximum',37)
        dim(x,y,x+900*s,y,'900 frame',-25)
        dim(x,y,x,y+1800*s,'1800',-26)
        dim(x+45*s,y+1550*s,x+855*s,y+1550*s,'810 opening',0)
    return x,y,s

def side(x,y,s=.24,braces=True,dims=False,labels=False):
    for z in D['rail_bottoms']:
        rect(x+D['shelf_end_setback']*s,y+(z+D['rail_height'])*s,D['shelf_depth']*s,D['panel_thickness']*s,HexColor('#e1cba8'),INK)
    for yy in [0,305]:rect(x+yy*s,y,45*s,1782*s,TAN,INK)
    for i,z in enumerate(D['rail_bottoms']+[D['top_rail_bottom']]):
        h=D['rail_height'] if i<4 else D['top_rail_height']
        rect(x+45*s,y+z*s,260*s,h*s,TAN,INK)
        if labels:txt(x+110*s,y+(z+h/2)*s,('B' if i<4 else 'C')+str(i+1 if i<4 else ''),7,'Bold')
    if braces:
        for z in D['brace_z_stations'][:-1]:
            for asc in [True,False]:poly([(x+a*s,y+b*s) for a,b in brace_poly(z,asc)],HexColor('#c59f6e'))
    rect(x-10*s,y+1782*s,370*s,18*s,HexColor('#e1cba8'),INK)
    if dims:
        dim(x-10*s,y+1800*s,x+360*s,y+1800*s,'370 top',18)
        dim(x,y,x+350*s,y,'350 frame',-25)
    return x,y,s

def table(x,y,width,columns,rows,widths,fontsize=9,rowheight=31):
    rect(x,y-24,width,24,INK)
    xx=x
    for col,w in zip(columns,widths):txt(xx+7,y-16,col,8,'Bold',white);xx+=w
    yy=y-24
    for i,row in enumerate(rows):
        if i%2==0:rect(x,yy-rowheight,width,rowheight,PALE)
        xx=x
        for content,w in zip(row,widths):
            para(xx+7,yy-15,str(content),w-12,fontsize,11)
            xx+=w
        line(x,yy-rowheight,x+width,yy-rowheight)
        yy-=rowheight
    return yy

def pdf():
    v=json.loads((OUT/'validation.json').read_text());eng=v['engineering']
    page('Workshop collection / 01','Alderline X4')
    txt(M,654,'FOUR-SHELF X-FRAME BOOKSHELF',13,'Bold',INK)
    para(M,630,'Warm timber. Open storage. A measured build.',310,11,16)
    image('hero',220,118,335,495)
    rect(42,365,168,210,PALE)
    txt(56,552,'THE PROJECT',9,'Bold',RUST)
    para(56,530,f"Four shelves + separate top\n{D['side_overall_width']:.0f} W × {D['top_depth']:.0f} D × {D['height']:.0f} H mm maximum\nIntermediate skill\nDowel joinery + half laps\nTwo-person final assembly",140,10,15)
    para(42,283,'An original plan inspired by the visible post, shelf and side-X structure in the supplied reference images. Dimensions, connections, rear bracing and page design are newly developed.',170,9.5,14)
    note(42,108,'BUILD A PROTOTYPE BEFORE RELEASE','Geometry checked; physical performance untested. This plan establishes no safe working load.')

    page('01 / design definition','Know the envelope','All dimensions are millimetres. Illustrations are not full-size templates unless specifically identified.')
    front(110,190,.225,dims=True);side(420,190,.225,dims=True)
    txt(170,146,'FRONT',9,'Bold');txt(432,146,'SIDE',9,'Bold')
    para(42,124,f"Maximum width is {D['side_overall_width']:.0f}: the side X slats project 18 beyond each frame edge. The top is 920 × 370; the frame is 900 × 350. Nominal height excludes foot pads and wall restraints.",528,9.5,14)
    para(42,82,'Shelf tops: 178 / 578 / 978 / 1378 above floor. Clear space between shelves: 382. Upper front opening: 312 below apron. Shelf undersides: 160 / 560 / 960 / 1360.',528,9,13)
    # Standalone dimensioned drawing export from this canonical PDF page later.

    page('02 / cutting & purchasing','Every part, accounted for','Finished sizes: thickness × width × length. Measure actual stock before cutting; nominal lumber names do not control.')
    rows=[]
    for a in schedule():
        length=f"{a['length']:.1f}" if a['id'] in ['H','J'] else f"{a['length']:.0f}"
        rows.append([a['id'],a['name'],a['qty'],f"{a['t']:.0f} × {a['w']:.0f} × {length}"])
    table(42,628,528,['ID','PART','QTY','FINISHED SIZE / mm'],rows,[32,214,44,238],9,30)
    para(42,312,f"H length {D['brace_long_edge']:.1f} is measured along either long edge between parallel end cuts. It is not the rough blank length. Prepare sixteen 490 mm blanks; keep eight of each complementary lap hand. J length is a fabrication target; drill to the measured end-hole pitch.",528,9,13)
    txt(42,242,'PURCHASE BASIS',10,'Bold',INK)
    para(42,221,'4 hardwood blanks 45 × 45 × 2400 for A; 2 boards 45 × at least 92 × 2400 for B/C (rip eight rails to 70); 1 board 30 × 30 × 2400 for G; 4 boards 18 × 35 × 2400 for H. Add defect allowance beyond this minimum.',528,9.5,14)
    para(42,161,'1 sheet cabinet plywood, 2440 × 1220 × 18, for D/E/F. Require sound void-free bearing edges and verified actual thickness. Use exposed, sanded and sealed edges; no edge band thickness is included.',528,9.5,14)
    note(42,82,'STOCK & CUTTING ALLOWANCE','Layouts allow 3 mm kerfs and at least 10 mm end trim. Choose straight, dry stock; allow more material for knots and tear-out.')

    page('03 / hardware & tools','Connections with a purpose','Quantities below are installed quantities. Buy spare screws and dowels. Choose compatible heads, pilot sizes and corrosion protection.')
    rows=[]
    for id,desc,n,allocation in HARDWARE:rows.append([id,desc,n])
    table(42,628,528,['ID','HARDWARE','QTY'],rows,[38,437,53],8.5,25)
    para(42,313,'K8 angles must have one hole in each wing; 2 mm steel thickness is assumed for K9 embed. Verify the actual fitting before purchase. K10 wall and furniture fixings follow the chosen manufacturer; no universal anchor or screw capacity is specified.',528,9.2,13.5)
    txt(42,245,'JOINT ALLOCATION',10,'Bold')
    para(42,225,'B/C to A: K1 + wood adhesive. F to A: K2 + adhesive. G to B: K3, three per cleat. D to G: K4, four per shelf. H to B/C: K5, one at each slat end; glue only the fitted lap. J to A: K6 and K7 at J-2 ends. E to F: K8/K9. K11: one per foot.',528,9.3,14)
    txt(42,143,'PREPARE THE BENCH',10,'Bold')
    para(42,123,'Saw with repeatable angle stop; router and depth control; matched dowel jig and brad-point bits; drill stops, countersink, clamps, square, tape, straightedge, stud detector and appropriate steel drilling/deburring tools. Also wood adhesive, abrasives 120/180/220, finish, eye/hearing protection and dust extraction.',528,9.3,14)

    page('04 / layout & drilling','Make the joints repeatable','Required stock: actual 45 mm posts/rails and 18 mm panels/slats. Re-parameterize and regenerate if your stock differs.')
    # Post face maps, same elevations as CAD.
    for x,title,offsets in [(80,'SIDE RAIL JOINT / 8 mm',None),(250,'APRON JOINT / 6 mm',None)]:
        scale=.215;rect(x,205,45*scale,1782*scale,TAN,INK)
        elevations=([z+o for z in D['rail_bottoms'] for o in D['rail_dowel_z_offsets']]+[1690+o for o in D['top_dowel_z_offsets']]) if x==80 else [1690+o for o in D['top_dowel_z_offsets']]
        for z in elevations:
            c.setFillColor(INK);c.circle(x+22.5*scale,205+z*scale,1.5,fill=1,stroke=0)
        txt(x-20,610,title,8,'Bold')
        if x==80:
            for i,z in enumerate(D['rail_bottoms']):txt(x+26,205+(z+35)*scale,f'{int(z+20)} / {int(z+50)}',8)
            txt(x+26,205+1736*scale,'1710 / 1762',8)
        else:txt(x+26,205+1736*scale,'1710 / 1762',8)
    para(365,535,'A post side bores: centred 22.5 across the 45 mm face, drilled into the front/rear post faces facing the side rails. A apron bores: 9 from the front or rear outside edge, drilled from the faces facing across the 810 opening.',195,9,13)
    para(365,365,'Label A-LF, A-LR, A-RF, A-RR (left/right and front/rear, viewed from front). Mirror the drilling, not the height datums. Reference every height from the same finished foot end.',195,9,13)
    txt(42,167,'BORE SCHEDULE',10,'Bold')
    para(42,147,'B: two Ø8 end bores, thickness centre 22.5; 20 and 50 above rail bottom. C: same centre; 20 and 72 above bottom. Drill 26 deep in both rail and post for 25 embed each. F: two Ø6 end bores, 9 through thickness; 20 and 72 above bottom. Drill 21 deep in apron and post for 20 embed each.',528,9.4,14)
    para(42,76,'Dry-fit one complete joint on scrap first. Use stop collars; clear chips and glue squeeze-out. Target bore centres ±0.25 mm; do not force mismatched dowels or drill through a post.',528,9,13)

    page('05 / X-slat fabrication','One bay. Eight repeated Xs.','H is a flat 18 × 35 slat. Make eight rising and eight falling members with complementary 9 mm laps.')
    x,y,s=67,352,.65
    for asc,col in [(False,HexColor('#ddc9a9')),(True,HexColor('#bc8f5b'))]:poly([(x+a*s,y+(b-125)*s) for a,b in brace_poly(125,asc)],col)
    dim(x+55*s,y,x+295*s,y,'240 overall',-23)
    dim(x+295*s,y,x+295*s,y+400*s,'400 end-plane spacing',22)
    txt(42,304,f"PARALLEL END CUTS  /  {D['brace_miter']:.2f}° OFF SQUARE",10,'Bold')
    para(42,284,f"Finished length on either long edge: {D['brace_long_edge']:.2f}. End cut projects {D['brace_end_cut']:.2f} horizontally. Start with 490 blanks; the minimum projected blank length is {D['brace_blank_min']:.2f}. Make a full-size scrap bay jig with end planes 400 apart and outer edges 240 apart. Saw settings are nominal: confirm the jig fit before batch cutting.",528,9.4,14)
    # Half lap section and lap rhombus illustration.
    rect(350,485,175,18,TAN,INK);rect(420,485,35,9,PAPER,INK)
    rect(350,459,175,18,HexColor('#ddc9a9'),INK);rect(420,468,35,9,PAPER,INK)
    txt(350,526,'LAP SECTION / schematic',8,'Bold');txt(350,438,'9 deep from opposite faces',8)
    para(350,408,'Mark the true overlap by crossing two slats in the jig. Remove the intersection rhombus, not a square notch. Preserve the 35 mm width.',185,8.7,13)
    para(42,187,f"Centre each lap at the bay centre: y = 175, z = 325 for the first bay. The rhombus is {D['lap_along_edge']:.2f} along either long edge; its two boundaries run parallel to the mating slat edges. Rout/saw waste in stages to a flat 9.0 depth. Use the 1:1 DXF/SVG outline to verify the marked shape; test print scale before use.",528,9.4,14)
    note(42,82,'FIT WITHOUT FORCE','Assembled lap thickness must equal 18. Test on scrap; target flush faces within 0.2 mm. Do not thin both members until the joint becomes loose.')

    page('06 / assembly 1','Build two side frames','Parts A ×4, B ×8, C ×2. K1 ×40. Assemble on a flat bench with cauls and matched spacers.')
    image('side_frame',42,183,225,440)
    y=598
    y=badge(285,y,1,'Label and dry-fit','Use the post identities from page 5. Rail bottoms are 90, 490, 890 and 1290 above each foot. Upper rail C starts at 1690. Keep all outer side faces flush.',270)-24
    y=badge(285,y,2,'Glue one side','Spread adhesive on the dowels and bore walls to the adhesive maker’s guidance. Seat B/C between the front and rear posts. Clamp gently across the 350 frame depth; protect the posts with cauls.',270)-24
    y=badge(285,y,3,'Square before cure','Check the outside post rectangle: 350 wide × 1782 high. Equal opposite diagonals are approximately 1816.0. Check straightness and twist, then recheck all five rail elevations.',270)-24
    y=badge(285,y,4,'Repeat as a matched pair','Build the second side on the same spacer setup. Match front-to-front post lengths and each rail level. Allow the specified full clamp/cure time before handling.',270)
    para(42,133,'SIDE FRAME DATUMS: A foot = 0. B bottoms = 90 / 490 / 890 / 1290. B tops = 160 / 560 / 960 / 1360. C = 1690–1782. Rail length = 260 between post faces. Finished side depth = 350.',528,9.2,14)
    note(42,73,'CHECKPOINT','Both frames must sit flat with matching rail heights. An out-of-square frame is corrected now, before adding X slats.')

    page('07 / assembly 2','Add the Xs and shelf cleats','Parts H ×16, G ×8. K5 ×32 and K3 ×24. Outer X slats attach to the side rail faces; cleats attach inside.')
    image('side_complete',42,185,225,443)
    y=598
    y=badge(285,y,5,'Seat the repeated Xs','End planes are 125/525/925/1325/1725 above the feet. Slat outer depth edges are y = 55 and 295. Glue the fitted lap; clamp it flush. Both slats sit directly on the outer rail faces.',270)-22
    y=badge(285,y,6,'Fasten each slat end','At each end, place one K5 screw on the slat centreline, 20 vertically in from the end plane. In the first rising slat the centres are (y,z) = (84.62,145) and (265.38,505); mirror for the falling slat. Repeat every 400 in height.',270)-22
    y=badge(285,y,7,'Fix the inner cleats','G tops align with B tops. Left cleats occupy x = 45–75; right = 825–855; both y = 45–305. Drive three K3 through each cleat into B at y = 110/175/240 and 15 below its top.',270)
    para(42,143,'Drill screw clearance through the attached part and species-appropriate pilots into the receiving timber. Countersink wood heads only to flush; do not bury heads. Clamp before driving. Confirm screw lengths on a scrap joint.',528,9.3,14)
    note(42,75,'SCREW CLEARANCE MATTERS','Keep the cleat screw positions shown. Moving them to the X end-screw lines can make opposing screws collide inside the rail.')

    page('08 / assembly 3','Connect the two sides','Parts F ×2 and K2 ×8. Use a helper and a flat, level surface; protect the finished edges.')
    image('frame_join',92,315,430,330)
    txt(240,321,'Xs and cleats omitted for clarity',7,'Sans',MUTED)
    txt(67,550,'F-F / FRONT APRON',8,'Bold');line(177,553,280,572,MUTED)
    txt(392,620,'F-R / REAR APRON',8,'Bold');line(390,616,355,610,MUTED)
    badge(42,276,8,'Dry-fit the full frame','Set the side frames 810 apart between their inner post faces. Fit the front and rear F aprons at z = 1690–1782, with outer faces flush with the front/back post faces. Use 6 × 40 dowels, two per apron end.',528)
    badge(42,173,9,'Glue, clamp and verify','Glue F joints and clamp across the width using long cauls. Check 900 frame width and 350 depth, equal diagonals in plan (about 965.7), and a square front elevation. Keep temporary braces/clamps until the rear straps are fitted and the adhesive is cured.',528)
    para(42,72,'The exploded drawing separates parts for identification; it does not show a stable unsupported construction stage. Do not leave the tall frame standing unattended before bracing and wall restraint installation.',528,9,13)

    page('09 / assembly 4','Fit shelves and the top','Parts D ×4, E ×1. K4 ×16; K8 ×4; K9 ×8. Four shelves sit between the side frames; the top caps the posts.')
    image('shelf_top',42,271,310,375)
    txt(357,582,'E / TOP',10,'Bold');para(357,562,'920 × 370 × 18. Centre for a 10 overhang from each frame edge. It does not overhang the proud X faces.',200,9.3,14)
    txt(357,470,'D / FOUR SHELVES',10,'Bold');para(357,450,'809 × 348 × 18. Side clearance 0.5 each; front/rear setback 1.0 each. Bearing on each cleat is 29.5 wide × 260 long.',200,9.3,14)
    badge(42,235,10,'Screw shelves to their cleats','Install bottom to top. Keep shelf undersides at 160/560/960/1360. Drill K4 clearance through D, pilot G, and countersink flush. Four screws per shelf: x = 60 and 840; y = 90 and 260. Recheck square as each shelf seats.',528)
    badge(42,132,11,'Attach the plywood top','Place two K8 angles on the inner face of each F apron, centred x = 250 and 650 from the left frame edge. The horizontal wing meets the underside of E. Use one K9 into F and one into E per angle. Predrill and stop below the show face.',528)
    para(42,65,'Use the actual angle as the drilling template (about 12 mm hole offset). A 2 mm wing leaves about 14 mm screw embed in 18 mm plywood. Verify screw tips cannot emerge.',528,8.7,12)

    page('10 / assembly 5','Brace the back. Anchor the case.','Parts J ×2, K6 ×4, K7 ×2 and two K10 restraint kits. Wall restraints are required before loading.')
    front(65,192,.235,rear=True)
    txt(68,635,'REAR / straps shown schematically',8,'Bold')
    para(318,610,f"Fit two commercial 20 × 1 steel cross-straps to rear post centres: x = 22.5 and 877.5. Lower screw level = 125; upper = 1725. Target end-hole pitch is {D['strap_hole_pitch']:.1f}; cut length about {D['strap_cut_length']:.1f}, with 25 beyond each end hole.",240,9.4,14)
    para(318,487,'Measure the squared case first. Use a timber drilling jig to transfer holes rather than rounding both strap lengths independently. Drill Ø5.5 clearance, deburr and round sharp corners. Do not use steel strapping with unknown brittleness or damaged holes.',240,9.3,14)
    para(318,364,'Fit J-1 against the post backs. J-2 crosses behind J-1; place a 1 mm K7 washer behind J-2 at each post so its end plane matches the crossing offset. One pan-head K6 per end. Snug both straps with the case square; do not overtighten and bow the frame.',240,9.3,14)
    para(42,145,'Install two furniture-to-wall restraint kits at the rear posts near z = 1750. Select the complete system for the actual wall and attach to sound structure per its instructions. Check for services before drilling. Keep fittings clear of the C dowels at z = 1710 and 1762; verify the chosen furniture screw path before drilling.',528,9.3,14)
    note(42,71,'RESTRAINT VERIFICATION','Do not substitute plasterboard alone for a structural fixing. A competent installer must verify the wall, hardware and installation; no fixing capacities are assumed.')

    page('11 / finishing & handover','Bring it into service carefully','Finish adhesion, screw seating and wall restraint installation are separate checks; none is replaced by the CAD model.')
    image('hero',355,306,197,322)
    y=608
    y=badge(42,y,12,'Prepare surfaces','After a complete dry-fit, ease accessible edges by about 1 mm. Sand 120 then 180, or to the finish maker’s guidance. Keep dowel holes, lap glue faces and adhesive surfaces free of finish.',300)-24
    y=badge(42,y,13,'Apply and cure','Pre-finish hard-to-reach areas if useful, then touch up after assembly. Coat exposed plywood edges. Ventilate, manage dust and oily finishing waste, and allow full cure before books contact the surfaces.',300)-24
    y=badge(42,y,14,'Level and restrain','Fit four equal non-slip pads; shim only with a stable full-bearing solution. Confirm all four feet bear evenly. Install and check both wall restraints before adding contents.',300)
    txt(42,272,'PRE-USE WALKTHROUGH',11,'Bold')
    items=['No rocking, open glue joints, loose laps or split stock.',
      'All shelf edges bear on cleats; no missing or protruding screws.',
      'Back cross-straps are straight and snug; edges are deburred.',
      'Wall connections are checked to the selected kit instructions.',
      'Finish is cured; feet are supported; no climbing or sitting on shelves.']
    y=247
    for s in items:
        c.setStrokeColor(MUTED);c.rect(43,y-2,7,7,stroke=1,fill=0);para(60,y,s,497,9.5,14);y-=29
    note(42,75,'USE & MAINTENANCE','Keep heavier contents low and distribute contents evenly. Recheck joints and restraints after relocation. No safe working load is assigned by this plan.')

    page('12 / engineering & validation','What the calculations establish','Computational checks support geometry review. They do not demonstrate strength, stability or suitability for sale.')
    rect(42,490,528,140,PALE)
    txt(57,608,'ILLUSTRATIVE SHELF BENDING',10,'Bold')
    para(57,587,f"Assume E = {eng['assumed_E_MPa']:.0f} MPa, an 810 mm simply supported span and 348 × 18 gross section. Face grain follows span. Uniform contents mass = 20 kg; assumed plywood density = 650 kg/m³ gives {eng['panel_self_mass_kg']:.2f} kg self-mass. Total gravity force = {eng['total_force_N']:.1f} N.",498,9.4,14)
    txt(57,516,f"Instantaneous deflection ≈ {eng['instant_deflection_mm']:.2f} mm    |    Bending stress ≈ {eng['bending_stress_MPa']:.2f} MPa",10,'Bold',INK)
    para(42,466,'I = bt³/12; w = F/L; deflection = 5wL⁴/(384EI); stress = (wL²/8)(t/2)/I. Units: N, mm and MPa. Full-opening span is a conservative bearing idealization; actual cleats support the shelf edges. No allowable stress or deflection acceptance limit has been selected.',528,9.5,14)
    para(42,383,'E is an assumption, not a verified plywood property. This idealization omits orthotropy, local defects, creep, moisture, duration, impact, connection slip, racking and tipping. No fastener capacities or safe working loads are inferred. The 20 kg scenario is not a load recommendation.',528,9.5,14)
    txt(42,292,f"INDEPENDENT CHECKS  /  {sum(a['passed'] for a in v['checks'])} OF {len(v['checks'])} PASSED",10,'Bold')
    para(42,270,'STEP read-back: valid solids and schedule count; dimensional envelope; no positive solid clashes above 0.01 mm³. Reconstructed slat width and lap volume agree. Shelf bearing, clearance, levels, stock nesting, dowel counts, screw tip containment and opposing screw spacing were checked programmatically.',528,9.5,14)
    note(42,139,'NOT TESTED','No physical assembly, load test, sustained-load test, racking test, tip test or wall-anchor test has been performed. Purchased hardware remains to be selected and verified.')
    para(42,75,'See VALIDATION_REPORT.md and validation.json for the individual checks, equations, measured values, scope and unresolved issues.',528,9,13)

    page('13 / release review','Before this plan is sold','P1 is a complete prototype plan package. Commercial release remains subject to the following human and physical checks.')
    y=610
    gates=[('Build from the manual','An independent woodworker builds one full-size prototype using only this package. Record actual stock thicknesses, tool access, clamp sequence, fit, screw paths and every correction.'),
      ('Test the selected materials and joints','Verify species/grade, moisture, plywood quality and stiffness. Evaluate dowel glue joints, cleat fixings, lap fit, rear bracing, screw withdrawal/splitting and purchased bracket suitability using an agreed test protocol.'),
      ('Assess strength and stability','A qualified reviewer sets defensible acceptance criteria and tests loading, sustained-load creep, racking, impact and tip resistance with the selected restraint system. Derive any future published load claim from evidence.'),
      ('Verify installation and instructions','Trial the wall restraint instructions for the intended wall types. Review entrapment, climbing, sharp edges and hardware hazards for the intended market; obtain applicable product/consumer-safety review.'),
      ('Proof the commercial edition','Cross-check all drawings against the prototype, verify 1:1 print scale, review English and hardware availability, and confirm original artwork/text rights and the DIYWOODPLANNER brand authorization.')]
    for i,(title,body) in enumerate(gates,1):
        y=badge(42,y,i,title,body,528)-20
    txt(42,156,'FILES IN THIS PACKAGE',10,'Bold')
    para(42,136,'PDF manual • named STEP assembly and representative part STEP files • SVG orthographic drawings • 1:1 brace profile/lap DXF and SVG • CSV cut/hardware lists • canonical JSON parameters • Python model, renderer, manual and validation sources • machine-readable and written validation report.',528,9.2,14)
    para(42,66,'A fresh prototype and review are required after dimensional, stock, joinery or hardware changes. Do not edit drawing labels alone; regenerate from the canonical model.',528,8.8,13)

    page('14 / assembly atlas','The complete assembly','Exploded view from the same canonical CAD geometry. Separation distances are illustrative, not assembly dimensions.')
    image('exploded',102,223,410,420)
    txt(42,594,'E / top ×1',9,'Bold');line(105,590,273,611,MUTED)
    txt(42,499,'A / posts ×4',9,'Bold');line(118,496,198,492,MUTED)
    txt(42,398,'D / shelves ×4',9,'Bold');line(137,402,307,441,MUTED)
    txt(421,565,'F / aprons ×2',9,'Bold');line(417,559,381,573,MUTED)
    txt(433,474,'C / top rails ×2',8,'Bold');line(429,478,406,525,MUTED)
    txt(433,400,'H / X slats ×16',8,'Bold');line(429,404,406,488,MUTED)
    txt(421,610,'J / rear straps ×2',8,'Bold');line(417,606,406,557,MUTED)
    txt(42,195,'SHELF SUPPORT / schematic section',9,'Bold')
    # Left side section: outer face X, thick B rail, inward cleat and shelf.
    sx,sy,sc=65,92,.95
    rect(sx-18*sc,sy,18*sc,70*sc,HexColor('#bc8f5b'),INK)
    rect(sx,sy,45*sc,70*sc,TAN,INK)
    rect(sx+45*sc,sy+40*sc,30*sc,30*sc,HexColor('#b89c76'),INK)
    rect(sx+45.5*sc,sy+70*sc,110*sc,18*sc,HexColor('#e1cba8'),INK)
    txt(sx-14,sy+20,'H',8,'Bold');txt(sx+15,sy+20,'B',8,'Bold');txt(sx+47,sy+38,'G',8,'Bold');txt(sx+108,sy+73,'D',8,'Bold')
    line(sx+75*sc,sy+55*sc,sx+15*sc,sy+55*sc,INK,1.5)
    para(240,170,'B is 45 thick. G projects 30 inward, flush to the rail top; D has 0.5 side clearance and 29.5 bearing. The line shows one K3 screw direction. H is shown for orientation on the outer face. Pilot holes and purchased fittings are omitted from the CAD.',315,9.2,14)
    c.save()
    # Physical page bounds check for all manually drawn text.
    problems=[b for b in text_boxes if b[1]<36 or b[1]+b[3]>578 or b[2]<24 or b[2]+b[4]>775]
    (OUT/'qa/layout_bounds.json').write_text(json.dumps(dict(page_count=page_no,text_items=len(text_boxes),out_of_bounds=problems),indent=2))
    print(f'PDF {page_no} pages; {len(problems)} text bounds violations',flush=True)
    if problems:print(problems)

if __name__=='__main__':pdf()
