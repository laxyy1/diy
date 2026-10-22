"""Independent analytic Alderline expectations; no generated CAD metadata as oracle."""
import math
from .alderline import expected_ids

def expected_counts(d):
    n=len(d['rail_bottoms']);return {'A':4,'B':2*n,'C':2,'D':n,'E':1,'F':2,'G':2*n,'H':4*n,'J':2}

def expected_hardware(d):
    n=len(d['rail_bottoms']);r=len(d['rail_dowel_z_offsets']);u=len(d['top_dowel_z_offsets'])
    return dict(K1=2*(2*n*r+2*u),K2=4*u,K3=2*n*len(d['cleat_screw_y']),K4=2*n*len(d['shelf_screw_y']),K5=8*n,K6=4,K7=2,K8=4,K9=8,K10=2,K11=4)

def stock_groups(d):return {'lumber':['A','B','C','G','H'],'sheet':['D','E','F'],'rough_lengths':{'H':d['brace_rough_blank_length']},'extra_purchases':{'STEEL':2}}

def pdf_facts(d):return {'Frame width':d['frame_width'],'Opening':d['opening'],'Shelf length':d['shelf_width'],'Top width':d['top_width'],'Overall width':d['side_overall_width']}

def scalar_checks(d):
    h=d['hardware'];embed=h['K9']['length']-h['angle_thickness']
    edge=d['design_rules']['min_screw_rail_edge'];off=d['brace_end_screw_z_offset'];endok=True
    yy=d['brace_y_min']+d['brace_end_cut']/2+d['brace_run']*off/d['brace_height']
    for i,z in enumerate(d['brace_z_stations'][:-1]):
        for j,zz in [(i,z+off),(i+1,z+d['brace_height']-off)]:
            lo=d['rail_bottoms'][j] if j<len(d['rail_bottoms']) else d['top_rail_bottom']
            hi=lo+d['rail_height'] if j<len(d['rail_bottoms']) else d['post_length']
            endok &= min(zz-lo,hi-zz,yy-d['post'],d['frame_depth']-d['post']-yy)>=edge-1e-7
    return [('joinery.bearing',d['cleat']-d['shelf_side_clearance']>=d['design_rules']['min_shelf_bearing'] and d['shelf_side_clearance']>0,'Positive gap and configured minimum bearing; minimum is a geometric design rule, not strength evidence'),
      ('joinery.bore_depth',d['rail_dowel_embed']+d['design_rules']['bore_bottom_clearance']<d['post'] and d['apron_dowel_embed']+d['design_rules']['bore_bottom_clearance']<d['post'],'Blind drill stop leaves timber beyond nominal bore'),
      ('brace.blank',d['brace_rough_blank_length']>=d['brace_blank_min']+d['design_rules']['blank_allowance'],'Angled-end extremity plus trimming allowance fits rough blank'),
      ('hardware.angle_tip_containment',0<embed<d['panel_thickness'],f'Assumed angle thickness leaves {embed:g} mm K9 embed; actual hardware needs verification'),
      ('joinery.brace_rail_edge',endok,f'Every X end screw centre meets the configured {edge:g} mm rail-edge rule; geometric rule only, no capacity inferred')]

def expected_dowels(d):
    result={};a=d['post'];W=d['frame_width'];T=d['frame_depth']
    for side,x in [('L',a/2),('R',W-a/2)]:
        stations=[('B',i+1,z,d['rail_dowel_z_offsets']) for i,z in enumerate(d['rail_bottoms'])]+[('C',len(d['rail_bottoms'])+1,d['top_rail_bottom'],d['top_dowel_z_offsets'])]
        for g,i,z,offsets in stations:
            for end,y in [('F',a),('R',T-a)]:
                for off in offsets:result[f'{g}-{side}{i}-{end}-{off:g}']=[x,y-d['rail_dowel_embed'],z+off,d['brace_dowel_diameter']/2,2*d['rail_dowel_embed']]
    for end,y in [('F',d['panel_thickness']/2),('R',T-d['panel_thickness']/2)]:
        for side,x in [('L',a),('R',W-a)]:
            for off in d['top_dowel_z_offsets']:result[f'F-{end}-{side}-{off:g}']=[x-d['apron_dowel_embed'],y,d['top_rail_bottom']+off,d['apron_dowel_diameter']/2,2*d['apron_dowel_embed']]
    return result

def expected_sizes(d):
    return {'A':[d['post'],d['post'],d['post_length']],'B':[d['rail_thickness'],d['rail_height'],d['rail_length']],
      'C':[d['rail_thickness'],d['top_rail_height'],d['rail_length']],'D':[d['panel_thickness'],d['shelf_depth'],d['shelf_width']],
      'E':[d['panel_thickness'],d['top_depth'],d['top_width']],'F':[d['panel_thickness'],d['top_rail_height'],d['opening']],
      'G':[d['cleat'],d['cleat'],d['rail_length']],'H':[d['brace_thickness'],d['brace_width'],d['brace_long_edge']],
      'J':[d['strap_thickness'],d['strap_width'],d['strap_cut_length']]}

def expected_volume(d,g):
    t,w,l=expected_sizes(d)[g];v=t*w*l
    r=d['brace_dowel_diameter']/2;a=d['apron_dowel_diameter']/2
    if g=='A':v-= (len(d['rail_bottoms'])*len(d['rail_dowel_z_offsets'])+len(d['top_dowel_z_offsets']))*math.pi*r*r*d['rail_dowel_embed']+len(d['top_dowel_z_offsets'])*math.pi*a*a*d['apron_dowel_embed']
    if g in ['B','C']:v-=2*len(d['rail_dowel_z_offsets'] if g=='B' else d['top_dowel_z_offsets'])*math.pi*r*r*d['rail_dowel_embed']
    if g=='F':v-=2*len(d['top_dowel_z_offsets'])*math.pi*a*a*d['apron_dowel_embed']
    if g=='H':v-=d['brace_thickness']/2*d['brace_width']**2/abs(math.sin(2*math.radians(d['brace_angle'])))
    if g=='J':v-=2*math.pi*(d['hardware']['strap_hole_diameter']/2)**2*d['strap_thickness']
    return v

def expected_bbox(d,id):
    g=id[0];a=d['post'];W=d['frame_width'];T=d['frame_depth'];P=d['panel_thickness']
    side='L' if '-L' in id else 'R';x=0 if side=='L' else W-a
    if g=='A':y=0 if id[-1]=='F' else T-a;return [x,y,0,x+a,y+a,d['post_length']]
    if g in ['B','C']:
        z=d['rail_bottoms'][int(id[3:])-1] if g=='B' else d['top_rail_bottom'];h=d['rail_height'] if g=='B' else d['top_rail_height'];return [x,a,z,x+a,T-a,z+h]
    if g=='G':z=d['shelf_undersides'][int(id[3:])-1];x=a if side=='L' else W-a-d['cleat'];return [x,a,z-d['cleat'],x+d['cleat'],T-a,z]
    if g=='H':x=-d['brace_thickness'] if side=='L' else W;z=d['brace_z_stations'][int(id[3:-1])-1];return [x,d['brace_y_min'],z,x+d['brace_thickness'],d['brace_y_max'],z+d['brace_height']]
    if g=='D':z=d['shelf_undersides'][int(id[2:])-1];return [a+d['shelf_side_clearance'],d['shelf_end_setback'],z,W-a-d['shelf_side_clearance'],T-d['shelf_end_setback'],z+P]
    if g=='E':o=d['top_overhang'];return [-o,-o,d['post_length'],W+o,T+o,d['height']]
    if g=='F':y=0 if id[-1]=='F' else T-P;return [a,y,d['top_rail_bottom'],W-a,y+P,d['post_length']]
    if g=='J':
        dx=W-a;dz=d['strap_top_z']-d['strap_bottom_z'];L=math.hypot(dx,dz);e=d['strap_end_allowance'];w=d['strap_width']/2
        extx=e*dx/L+w*dz/L;extz=e*dz/L+w*dx/L;i=int(id[-1])-1
        return [a/2-extx,T+i*d['strap_thickness'],d['strap_bottom_z']-extz,W-a/2+extx,T+(i+1)*d['strap_thickness'],d['strap_top_z']+extz]
    raise ValueError(id)


def template_areas(d):
    return {'PROFILE':d['brace_width']*d['brace_long_edge'],'LAP':d['brace_width']**2/abs(math.sin(2*math.radians(d['brace_angle'])))}
