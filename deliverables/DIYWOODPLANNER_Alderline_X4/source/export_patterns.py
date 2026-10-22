"""1:1 brace fabrication pattern and plywood nesting from canonical dimensions."""
import math,json
import numpy as np
import ezdxf
from model import D, OUT, brace_poly, ROOT

def clip(subject,clipper):
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    result=subject
    for a,b in zip(clipper,clipper[1:]+clipper[:1]):
        result2=[]
        for s,e in zip(result[-1:]+result[:-1],result):
            ins=cross(np.array(b)-a,np.array(s)-a)>=-1e-8
            ine=cross(np.array(b)-a,np.array(e)-a)>=-1e-8
            if ins!=ine:
                ray=np.array(e)-s;edge=np.array(b)-a
                t=cross(np.array(a)-s,edge)/cross(ray,edge)
                result2.append((np.array(s)+t*ray).tolist())
            if ine:result2.append(e)
        result=result2
    return result

def export():
    a=brace_poly(D['brace_z_stations'][0],True);b=brace_poly(D['brace_z_stations'][0],False)
    intersection=clip(a,b)
    theta=math.radians(D['brace_angle']);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]])
    origin=np.array(a[0]);
    def flat(poly):return [[float((np.array(p)-origin)@u),float((np.array(p)-origin)@v)+D['brace_width']] for p in poly]
    outer,lap=flat(a),flat(intersection)
    doc=ezdxf.new('R2010');doc.units=4;msp=doc.modelspace()
    doc.layers.new('PROFILE',dxfattribs={'color':7});doc.layers.new('LAP_9_DEEP',dxfattribs={'color':1})
    msp.add_lwpolyline(outer,close=True,dxfattribs={'layer':'PROFILE'})
    msp.add_lwpolyline(lap,close=True,dxfattribs={'layer':'LAP_9_DEEP'})
    msp.add_line((0,-20),(100,-20));msp.add_text('100 mm CHECK BAR - UNITS mm',height=4).set_placement((0,-30))
    msp.add_text('H: lap 9 mm from opposite faces on paired members. Profile is not a safe router jig.',height=4).set_placement((0,-45))
    doc.saveas(OUT/'drawings/H_brace_1to1.dxf')
    # 1 mm = 1 SVG physical mm, a 100 mm calibration bar, no browser scaling.
    def pts(pp):return ' '.join(f'{x+10:.6f},{65-y:.6f}' for x,y in pp)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="490mm" height="120mm" viewBox="0 0 490 120">
<rect width="490" height="120" fill="white"/>
<polygon points="{pts(outer)}" fill="none" stroke="#243d37" stroke-width="0.25"/>
<polygon points="{pts(lap)}" fill="none" stroke="#a55230" stroke-width="0.25"/>
<path d="M10 85H110M10 82V88M110 82V88" stroke="black" stroke-width="0.25"/>
<g font-family="sans-serif" font-size="4"><text x="10" y="98">100 mm check bar. Print at actual size; verify with a ruler.</text>
<text x="10" y="110">H / lap 9 mm deep from opposite faces on paired slats. Millimetres. P1 / DIYWOODPLANNER.</text></g></svg>'''
    (OUT/'drawings/H_brace_1to1.svg').write_text(svg)
    # Validate area of rhombus and full profile without importing the model's solid calculation.
    def area(pp):return abs(sum(x*yy-xx*y for (x,y),(xx,yy) in zip(pp,pp[1:]+pp[:1])))/2
    assert abs(area(outer)-35*D['brace_long_edge'])<1e-6
    assert abs(area(lap)-35**2/abs(math.sin(2*theta)))<1e-6
    data={'units':'mm','profile':outer,'lap':lap,'profile_area_mm2':area(outer),'lap_area_mm2':area(lap)}
    (OUT/'drawings/H_brace_pattern.json').write_text(json.dumps(data,indent=2))
    # Export an SVG sheet map with 20 mm spacing, all face grain in X.
    rects=[('E',0,0,D['top_width'],D['top_depth'])]
    for j in range(2):
        for i in range(2):rects.append((f'D-{j*2+i+1}',i*(D['shelf_width']+20),D['top_depth']+20+j*(D['shelf_depth']+20),D['shelf_width'],D['shelf_depth']))
    for i in range(2):rects.append((f'F-{i+1}',D['top_width']+20,i*(D['top_rail_height']+20),D['opening'],D['top_rail_height']))
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="550" viewBox="-50 -50 2540 1370"><rect x="0" y="0" width="2440" height="1220" fill="#faf7f1" stroke="#243d37" stroke-width="3"/>'
    for label,x,y,w,h in rects:
        svg+=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#d8b98c" stroke="#243d37" stroke-width="2"/><text x="{x+20}" y="{y+50}" font-family="sans-serif" font-size="30">{label}: {w:g} x {h:g}</text>'
    svg+='<text x="0" y="1300" font-family="sans-serif" font-size="30">2440 x 1220 sheet / Face grain runs horizontally / Drawing is a nesting map, not a saw sequence</text></svg>'
    (OUT/'drawings/plywood_nesting.svg').write_text(svg)
    print('DXF/SVG fabrication patterns exported; independent area checks passed.')

if __name__=='__main__':export()
