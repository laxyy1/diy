"""Canonical parametric wood geometry. Millimetres. No application/UI.

Run: XDG_CACHE_HOME=/tmp/woodplanner-cache python source/model.py
Wood parts, dowel bores, X half laps and steel straps are exact CAD solids.
Fastener pilot holes, purchased brackets/restraints and finish are not modeled.
"""
from pathlib import Path
import json, math, os
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/woodplanner-cache')
import cadquery as cq
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output'
P = json.loads((ROOT/'source/parameters.json').read_text())

def derive(p):
    d = dict(p)
    d['post_length'] = p['height']-p['panel_thickness']
    d['opening'] = p['frame_width']-2*p['post']
    d['rail_length'] = p['frame_depth']-2*p['post']
    d['top_rail_height'] = d['post_length']-p['top_rail_bottom']
    d['shelf_width'] = d['opening']-2*p['shelf_side_clearance']
    d['shelf_depth'] = p['frame_depth']-2*p['shelf_end_setback']
    d['top_width'] = p['frame_width']+2*p['top_overhang']
    d['top_depth'] = p['frame_depth']+2*p['top_overhang']
    h = p['brace_z_stations'][1]-p['brace_z_stations'][0]
    b = p['brace_y_max']-p['brace_y_min']
    w = p['brace_width']
    # Solve horizontal end-cut length q so normal distance between long edges = w.
    lo,hi = w,b
    for _ in range(90):
        q=(lo+hi)/2
        if q*h/math.hypot(h,b-q)>w: hi=q
        else: lo=q
    q=(lo+hi)/2; run=b-q
    theta=math.atan2(h,run)
    d.update(brace_height=h,brace_end_cut=q,brace_run=run,
             brace_long_edge=math.hypot(h,run),brace_angle=math.degrees(theta),
             brace_miter=90-math.degrees(theta),
             brace_blank_min=math.hypot(h,run)+q*math.cos(theta),
             lap_along_edge=w/abs(math.sin(2*theta)))
    d['strap_hole_pitch']=math.hypot(p['frame_width']-p['post'],p['strap_top_z']-p['strap_bottom_z'])
    d['strap_cut_length']=d['strap_hole_pitch']+2*p['strap_end_allowance']
    d['side_overall_width']=p['frame_width']+2*p['brace_thickness']
    return d

D=derive(P)

def box(x,y,z,dx,dy,dz):
    return cq.Solid.makeBox(dx,dy,dz,cq.Vector(x,y,z))

def cyl(x,y,z,dx,dy,dz,r,length):
    return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(dx,dy,dz))

def yz_prism(poly,x,t):
    wire=cq.Wire.makePolygon([cq.Vector(x,y,z) for y,z in poly],close=True)
    return cq.Solid.extrudeLinear(wire,[],cq.Vector(t,0,0))

def brace_poly(z,ascending=True):
    a,b=D['brace_y_min'],D['brace_y_max']; q=D['brace_end_cut']; h=D['brace_height']
    pp=[(a,z),(a+q,z),(b,z+h),(b-q,z+h)]
    if not ascending: pp=[(a+b-y,zz) for y,zz in pp][::-1]
    return pp

COLORS={'A':(0.64,0.43,0.26),'B':(0.72,0.52,0.32),'C':(0.72,0.52,0.32),
 'D':(0.82,0.67,0.46),'E':(0.85,0.71,0.51),'F':(0.74,0.55,0.35),
 'G':(0.65,0.49,0.32),'H':(0.76,0.57,0.36),'J':(0.24,0.28,0.29)}

def build():
    parts=[]
    def add(id,group,shape,meta=None):
        parts.append(dict(id=id,group=group,shape=shape,color=COLORS[group],meta=meta or {}))
    W,T,H=D['frame_width'],D['frame_depth'],D['post_length']; post=D['post']
    rails=[(z,D['rail_height'],'B') for z in D['rail_bottoms']]+[(D['top_rail_bottom'],D['top_rail_height'],'C')]
    # Bores have exact nominal depth; bottom clearance is a drilling instruction, not CAD.
    for side,x in [('L',0),('R',W-post)]:
        for end,y in [('F',0),('R',T-post)]:
            solid=box(x,y,0,post,post,H)
            yy=post if end=='F' else T-post; direction=-1 if end=='F' else 1
            for z,h,g in rails:
                offsets=D['rail_dowel_z_offsets'] if g=='B' else D['top_dowel_z_offsets']
                for dz in offsets:
                    solid=solid.cut(cyl(x+post/2,yy,z+dz,0,direction,0,4,D['rail_dowel_embed']))
            for dz in D['top_dowel_z_offsets']:
                xx=post if side=='L' else W-post; sign=-1 if side=='L' else 1
                solid=solid.cut(cyl(xx,9 if end=='F' else T-9,D['top_rail_bottom']+dz,sign,0,0,3,D['apron_dowel_embed']))
            add('A-'+side+end,'A',solid,dict(side=side,end=end))
        for i,(z,h,g) in enumerate(rails):
            s=box(x,post,z,post,D['rail_length'],h)
            offsets=D['rail_dowel_z_offsets'] if g=='B' else D['top_dowel_z_offsets']
            for dz in offsets:
                s=s.cut(cyl(x+post/2,post,z+dz,0,1,0,4,D['rail_dowel_embed']))
                s=s.cut(cyl(x+post/2,T-post,z+dz,0,-1,0,4,D['rail_dowel_embed']))
            add(f'{g}-{side}{i+1}',''+g,s,dict(side=side,station=i,z=z))
        for i,z in enumerate(D['rail_bottoms']):
            xc=post if side=='L' else W-post-D['cleat']
            add(f'G-{side}{i+1}','G',box(xc,post,z+D['rail_height']-D['cleat'],D['cleat'],D['rail_length'],D['cleat']),dict(side=side,station=i))
        for i,z in enumerate(D['brace_z_stations'][:-1]):
            xx=-D['brace_thickness'] if side=='L' else W
            p=yz_prism(brace_poly(z,True),xx,D['brace_thickness'])
            n=yz_prism(brace_poly(z,False),xx,D['brace_thickness'])
            # Remove complementary halves of the shared rhombus at the crossing.
            shared=p.intersect(n)
            outer=box(xx,0,0,9,T,H) if side=='L' else box(xx+9,0,0,9,T,H)
            inner=box(xx+9,0,0,9,T,H) if side=='L' else box(xx,0,0,9,T,H)
            add(f'H-{side}{i+1}a','H',p.cut(shared.intersect(outer)),dict(side=side,station=i,ascending=True,z=z))
            add(f'H-{side}{i+1}b','H',n.cut(shared.intersect(inner)),dict(side=side,station=i,ascending=False,z=z))
    for i,z in enumerate(D['rail_bottoms']):
        add(f'D-{i+1}','D',box(post+D['shelf_side_clearance'],D['shelf_end_setback'],z+D['rail_height'],D['shelf_width'],D['shelf_depth'],D['panel_thickness']),dict(station=i))
    add('E-1','E',box(-D['top_overhang'],-D['top_overhang'],H,D['top_width'],D['top_depth'],D['panel_thickness']))
    for end,y in [('F',0),('R',T-D['panel_thickness'])]:
        s=box(post,y,D['top_rail_bottom'],D['opening'],D['panel_thickness'],D['top_rail_height'])
        for dz in D['top_dowel_z_offsets']:
            for xx,sign in [(post,1),(W-post,-1)]:
                s=s.cut(cyl(xx,y+9,D['top_rail_bottom']+dz,sign,0,0,3,D['apron_dowel_embed']))
        add('F-'+end,'F',s,dict(end=end))
    for i in range(2):
        start=np.array([post/2,D['strap_bottom_z']]); end=np.array([W-post/2,D['strap_top_z']])
        if i: start[0],end[0]=end[0],start[0]
        v=(end-start)/np.linalg.norm(end-start); n=np.array([-v[1],v[0]])*D['strap_width']/2
        a=start-v*D['strap_end_allowance']; b=end+v*D['strap_end_allowance']
        vertices=[cq.Vector(x,T+i*D['strap_thickness'],z) for x,z in [a+n,a-n,b-n,b+n]]
        s=cq.Solid.extrudeLinear(cq.Wire.makePolygon(vertices,close=True),[],cq.Vector(0,D['strap_thickness'],0))
        for c in [start,end]: s=s.cut(cyl(c[0],T+i,c[1],0,1,0,2.75,1))
        add(f'J-{i+1}','J',s,dict(station=i))
    return parts

def schedule():
    return [
      dict(id='A',name='Posts',qty=4,t=D['post'],w=D['post'],length=D['post_length'],material='Straight kiln-dried hardwood',note='Square ends; matched lengths.'),
      dict(id='B',name='Shelf side rails',qty=8,t=D['rail_thickness'],w=D['rail_height'],length=D['rail_length'],material='Hardwood',note='Two 8 mm dowels per end.'),
      dict(id='C',name='Upper side rails',qty=2,t=D['rail_thickness'],w=D['top_rail_height'],length=D['rail_length'],material='Hardwood',note='Two 8 mm dowels per end.'),
      dict(id='D',name='Shelf panels',qty=4,t=D['panel_thickness'],w=D['shelf_depth'],length=D['shelf_width'],material='Cabinet plywood',note='Face grain along length; no notches.'),
      dict(id='E',name='Top panel',qty=1,t=D['panel_thickness'],w=D['top_depth'],length=D['top_width'],material='Cabinet plywood',note='10 mm overhang on all frame edges.'),
      dict(id='F',name='Front/rear top aprons',qty=2,t=D['panel_thickness'],w=D['top_rail_height'],length=D['opening'],material='Cabinet plywood',note='Two 6 mm dowels per end.'),
      dict(id='G',name='Shelf support cleats',qty=8,t=D['cleat'],w=D['cleat'],length=D['rail_length'],material='Hardwood',note='Three transverse screws per cleat.'),
      dict(id='H',name='X slats',qty=16,t=D['brace_thickness'],w=D['brace_width'],length=D['brace_long_edge'],material='Hardwood',note=f"Parallel {D['brace_miter']:.2f} deg end cuts; 9 mm complementary half laps."),
      dict(id='J',name='Rear steel straps',qty=2,t=D['strap_thickness'],w=D['strap_width'],length=D['strap_cut_length'],material='Commercial bracing steel',note='Cut/drill to actual jig; deburr all edges.')]

HARDWARE=[
 ('K1','Fluted hardwood dowels, 8 x 50 mm',40,'4 per B/C rail; buy 50'),
 ('K2','Fluted hardwood dowels, 6 x 40 mm',8,'4 per F apron; buy 12'),
 ('K3','Wood screws, 5 x 60 mm',24,'3 per G cleat; 30 mm nominal rail embed'),
 ('K4','Wood screws, 4 x 40 mm',16,'4 per D shelf; 22 mm nominal cleat embed'),
 ('K5','Wood screws, 4 x 45 mm',32,'2 per H slat; 27 mm nominal rail embed'),
 ('K6','Pan-head wood screws, 5 x 35 mm',4,'1 per J end; 33-34 mm nominal post embed'),
 ('K7','Steel washers, 1 mm thick, 5.5 mm bore',2,'At both J-2 ends to match crossing offset'),
 ('K8','25 x 25 x 20 mm steel angle, one hole/wing',4,'Two per F apron; hole centres about 12 mm'),
 ('K9','Wood screws, 4 x 16 mm',8,'2 per K8; do not countersink thin steel'),
 ('K10','Commercial furniture-to-wall restraint kit',2,'Both rear posts to suitable wall structure; kit-specific fixings'),
 ('K11','Non-slip foot pads, matching thickness',4,'Do not include pad thickness in nominal height')]

def export(parts):
    (OUT/'cad').mkdir(exist_ok=True,parents=True)
    assy=cq.Assembly(name='DIYWOODPLANNER_Alderline_X4_P1')
    for a in parts: assy.add(a['shape'],name=a['id'],color=cq.Color(*a['color']))
    assy.export(str(OUT/'cad/Alderline_X4.step'))
    # One of each wood part, including the complementary X slat lap.
    for g in 'ABCDEFGH':
        a=next(a for a in parts if a['group']==g)
        cq.exporters.export(a['shape'],str(OUT/f'cad/part_{g}.step'))
    for asc in [True,False]:
        a=next(a for a in parts if a['group']=='H' and a['meta']['ascending']==asc)
        cq.exporters.export(a['shape'],str(OUT/f"cad/part_H_{'a' if asc else 'b'}.step"))
    (OUT/'derived_dimensions.json').write_text(json.dumps(D,indent=2))
    (OUT/'cut_list.json').write_text(json.dumps(schedule(),indent=2))
    import csv
    with (OUT/'cut_list.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=schedule()[0].keys()); writer.writeheader(); writer.writerows(schedule())
    with (OUT/'hardware.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['id','description','quantity','allocation']);w.writerows(HARDWARE)
    mesh=[]
    for a in parts:
        vs,ts=a['shape'].tessellate(0.4,0.3)
        mesh.append(dict(id=a['id'],group=a['group'],meta=a['meta'],color=a['color'],
                         vertices=[[v.x,v.y,v.z] for v in vs],triangles=ts))
    (OUT/'cad/assembly_mesh.json').write_text(json.dumps(mesh))
    for name,direction in [('isometric',(1,-1,0.7)),('front',(0,-1,0)),('side',(-1,0,0)),('rear',(0,1,0))]:
        cq.exporters.export(cq.Compound.makeCompound([a['shape'] for a in parts]),str(OUT/f'drawings/{name}.svg'),
          opt={'projectionDir':direction,'showHidden':False,'strokeWidth':0.6,'width':1100,'height':1500,'marginLeft':30,'marginTop':30})
    print(f'Exported {len(parts)} solids and STEP/SVG schedules.',flush=True)

if __name__=='__main__':
    parts=build();export(parts)
