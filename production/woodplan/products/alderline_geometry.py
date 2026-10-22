"""Alderline-only timber joinery CAD. Refactored from preserved P1; no shared globals."""
import cadquery as cq
import numpy as np
from ..common import Part

from ..cad import box,cyl,yz_prism

def brace_poly(D,z,ascending=True):
    a,b=D['brace_y_min'],D['brace_y_max']; q=D['brace_end_cut']; h=D['brace_height']
    pp=[(a,z),(a+q,z),(b,z+h),(b-q,z+h)]
    if not ascending: pp=[(a+b-y,zz) for y,zz in pp][::-1]
    return pp

COLORS={'A':(0.64,0.43,0.26),'B':(0.72,0.52,0.32),'C':(0.72,0.52,0.32),
 'D':(0.82,0.67,0.46),'E':(0.85,0.71,0.51),'F':(0.74,0.55,0.35),
 'G':(0.65,0.49,0.32),'H':(0.76,0.57,0.36),'J':(0.24,0.28,0.29)}


def geometry(D):
    parts=[]
    def add(id,group,shape,meta=None):
        parts.append(Part(id,group,shape,meta or {}))
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
                    solid=solid.cut(cyl(x+post/2,yy,z+dz,0,direction,0,D['brace_dowel_diameter']/2,D['rail_dowel_embed']))
            for dz in D['top_dowel_z_offsets']:
                xx=post if side=='L' else W-post; sign=-1 if side=='L' else 1
                solid=solid.cut(cyl(xx,D['panel_thickness']/2 if end=='F' else T-D['panel_thickness']/2,D['top_rail_bottom']+dz,sign,0,0,D['apron_dowel_diameter']/2,D['apron_dowel_embed']))
            add('A-'+side+end,'A',solid,dict(side=side,end=end))
        for i,(z,h,g) in enumerate(rails):
            s=box(x,post,z,post,D['rail_length'],h)
            offsets=D['rail_dowel_z_offsets'] if g=='B' else D['top_dowel_z_offsets']
            for dz in offsets:
                s=s.cut(cyl(x+post/2,post,z+dz,0,1,0,D['brace_dowel_diameter']/2,D['rail_dowel_embed']))
                s=s.cut(cyl(x+post/2,T-post,z+dz,0,-1,0,D['brace_dowel_diameter']/2,D['rail_dowel_embed']))
            add(f'{g}-{side}{i+1}',''+g,s,dict(side=side,station=i,z=z))
        for i,z in enumerate(D['rail_bottoms']):
            xc=post if side=='L' else W-post-D['cleat']
            add(f'G-{side}{i+1}','G',box(xc,post,z+D['rail_height']-D['cleat'],D['cleat'],D['rail_length'],D['cleat']),dict(side=side,station=i))
        for i,z in enumerate(D['brace_z_stations'][:-1]):
            xx=-D['brace_thickness'] if side=='L' else W
            p=yz_prism(brace_poly(D,z,True),xx,D['brace_thickness'])
            n=yz_prism(brace_poly(D,z,False),xx,D['brace_thickness'])
            # Remove complementary halves of the shared rhombus at the crossing.
            shared=p.intersect(n)
            half=D['brace_thickness']/2
            outer=box(xx,0,0,half,T,H) if side=='L' else box(xx+half,0,0,half,T,H)
            inner=box(xx+half,0,0,half,T,H) if side=='L' else box(xx,0,0,half,T,H)
            add(f'H-{side}{i+1}a','H',p.cut(shared.intersect(outer)),dict(side=side,station=i,ascending=True,z=z))
            add(f'H-{side}{i+1}b','H',n.cut(shared.intersect(inner)),dict(side=side,station=i,ascending=False,z=z))
    for i,z in enumerate(D['rail_bottoms']):
        add(f'D-{i+1}','D',box(post+D['shelf_side_clearance'],D['shelf_end_setback'],z+D['rail_height'],D['shelf_width'],D['shelf_depth'],D['panel_thickness']),dict(station=i))
    add('E-1','E',box(-D['top_overhang'],-D['top_overhang'],H,D['top_width'],D['top_depth'],D['panel_thickness']))
    for end,y in [('F',0),('R',T-D['panel_thickness'])]:
        s=box(post,y,D['top_rail_bottom'],D['opening'],D['panel_thickness'],D['top_rail_height'])
        for dz in D['top_dowel_z_offsets']:
            for xx,sign in [(post,1),(W-post,-1)]:
                s=s.cut(cyl(xx,y+D['panel_thickness']/2,D['top_rail_bottom']+dz,sign,0,0,D['apron_dowel_diameter']/2,D['apron_dowel_embed']))
        add('F-'+end,'F',s,dict(end=end))
    for i in range(2):
        start=np.array([post/2,D['strap_bottom_z']]); end=np.array([W-post/2,D['strap_top_z']])
        if i: start[0],end[0]=end[0],start[0]
        v=(end-start)/np.linalg.norm(end-start); n=np.array([-v[1],v[0]])*D['strap_width']/2
        a=start-v*D['strap_end_allowance']; b=end+v*D['strap_end_allowance']
        vertices=[cq.Vector(x,T+i*D['strap_thickness'],z) for x,z in [a+n,a-n,b-n,b+n]]
        s=cq.Solid.extrudeLinear(cq.Wire.makePolygon(vertices,close=True),[],cq.Vector(0,D['strap_thickness'],0))
        for c in [start,end]: s=s.cut(cyl(c[0],T+i*D['strap_thickness'],c[1],0,1,0,D['hardware']['strap_hole_diameter']/2,D['strap_thickness']))
        add(f'J-{i+1}','J',s,dict(station=i))
    return parts

