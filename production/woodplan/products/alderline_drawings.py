"""Alderline-specific camera selection, exploded offsets, dimensions and lap profile."""
import json,math
from ..render import render
from ..common import clip,dump
from ..templates import export_pattern
from .alderline_geometry import brace_poly

def pattern(d):
    poly=brace_poly(d,d['brace_z_stations'][0],True);other=brace_poly(d,d['brace_z_stations'][0],False);lap=clip(poly,other)
    theta=math.radians(d['brace_angle']);c,s=math.cos(theta),math.sin(theta);a,b=poly[0]
    flat=lambda points:[[c*(y-a)+s*(z-b),-s*(y-a)+c*(z-b)+d['brace_width']] for y,z in points]
    profile=flat(poly)
    return dict(units='mm',width=max(x for x,y in profile),height=d['brace_width'],lap_depth=d['brace_thickness']/2,polygons={'PROFILE':profile,'LAP':flat(lap)})

def generate(design,out):
    d=design.dimensions;mesh=json.loads((out/'cad/mesh.json').read_text());offsets={}
    for p in design.parts:
        off=[0.,0.,0.];g=p.group
        if g in 'ABCGH':off[0]=(-1 if p.meta['side']=='L' else 1)*d['frame_width']*.22
        if g=='D':off[2]=d['brace_height']*.25
        if g=='E':off[2]=d['height']*.15
        if g=='F':off[1]=(-1 if p.meta['end']=='F' else 1)*d['frame_depth']*.5
        if g=='J':off[1]=d['frame_depth']*.65
        offsets[p.id]=off
    views={}
    def draw(name,groups=None,off=None,view=(1.6,-2.6,1.5),selection=None):
        sel=selection or (lambda m:groups is None or m['group'] in groups)
        projection=render(mesh,out/f'drawings/{name}.png',selection=sel,offsets=off,view=view)
        views[name]=dict(projection=projection,offsets=off or {},ids=[m['id'] for m in mesh if sel(m)])
    draw('hero');draw('exploded',off=offsets);draw('front',view=(0,-1,0));draw('side',view=(1,0,0));draw('rear',view=(0,1,0))
    for step in design.steps:
        draw(step['id'],step['groups'],off=offsets if step['id'] in ['join-frame','shelves-top'] else None,
             view=(-3,-2,1.3) if step['id']=='cleats' else ((-1.5,3,1.4) if step['id']=='back-restraints' else (1.6,-2.6,1.5)),
             selection=(lambda m,groups=step['groups']:m['group'] in groups and m['meta'].get('side')=='R') if step['id'] in ['side-frames','x-slats','cleats'] else None)
    strap_points={'J-1':[d['post']/2+(d['frame_width']-d['post'])*.75,d['frame_depth']+d['strap_thickness']/2,d['strap_bottom_z']+(d['strap_top_z']-d['strap_bottom_z'])*.75],
      'J-2':[d['frame_width']-d['post']/2-(d['frame_width']-d['post'])*.75,d['frame_depth']+1.5*d['strap_thickness'],d['strap_bottom_z']+(d['strap_top_z']-d['strap_bottom_z'])*.75]}
    for name in ['exploded','back-restraints']:views[name]['label_points']=strap_points
    views['exploded']['hidden_callouts']=['J-2']
    members=[p for p in design.parts if p.id in ['H-R1a','H-R1b']]
    jointoff={p.id:[d['brace_thickness']*3*(1 if p.meta['ascending'] else -1),0,0] for p in members}
    # Crop the actual CAD to the crossing, rather than merely enlarging the whole X.
    from ..cad import box
    from ..common import bbox
    jointmesh=[];cy=(d['brace_y_min']+d['brace_y_max'])/2;cz=d['brace_z_stations'][0]+d['brace_height']/2
    extent=d['brace_width']*2
    window=box(d['frame_width']-1,cy-extent,cz-extent,d['brace_thickness']+2,2*extent,2*extent)
    for p in members:
        shape=p.shape.intersect(window);vs,ts=shape.tessellate(.2,.3)
        jointmesh.append(dict(id=p.id,group=p.group,meta=p.meta,color=design.drawings['colors'][p.group],vertices=[[v.x,v.y,v.z] for v in vs],triangles=ts))
    projection=render(jointmesh,out/'drawings/lap-closeup.png',offsets=jointoff,view=(-3,-2,1.3))
    views['lap-closeup']=dict(projection=projection,offsets=jointoff,ids=list(jointoff),label_points={p.id:[d['frame_width']+d['brace_thickness']/2,cy,cz] for p in members})
    views['front']['dimensions']=[{'a':[-d['brace_thickness'],0,d['height']],'b':[d['frame_width']+d['brace_thickness'],0,d['height']],'value':d['side_overall_width'],'orientation':'horizontal'},
      {'a':[0,0,0],'b':[0,0,d['height']],'value':d['height'],'orientation':'vertical'},
      {'a':[d['post'],0,d['shelf_tops'][-1]+100],'b':[d['frame_width']-d['post'],0,d['shelf_tops'][-1]+100],'value':d['opening'],'orientation':'horizontal'}]
    views['side']['dimensions']=[{'a':[0,-d['top_overhang'],d['height']],'b':[0,d['frame_depth']+d['top_overhang'],d['height']],'value':d['top_depth'],'orientation':'horizontal'},
      {'a':[0,0,0],'b':[0,d['frame_depth'],0],'value':d['frame_depth'],'orientation':'horizontal'}]
    dump(out/'drawings/views.json',views);export_pattern(pattern(d),out)
    return views
