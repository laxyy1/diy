"""Alderline X4 design rules. This is not a universal furniture model."""
import math,copy
from collections import Counter
from ..common import Design,hardware_counts,measure,metric
from .alderline_geometry import geometry,brace_poly,COLORS

def derive(p):
    if p.get('units')!='mm':raise ValueError('Only canonical millimetres are accepted; convert explicitly before modeling.')
    for k in ['frame_width','frame_depth','height','post','panel_thickness','brace_width','brace_thickness']:
        if not isinstance(p.get(k),(int,float)) or not math.isfinite(p[k]) or p[k]<=0:raise ValueError('Invalid positive dimension: '+k)
    def finite_tree(value):
        if isinstance(value,dict):return all(finite_tree(v) for v in value.values())
        if isinstance(value,list):return all(finite_tree(v) for v in value)
        if isinstance(value,(int,float)):return math.isfinite(value)
        return True
    if not finite_tree(p):raise ValueError('Nonfinite parameter in design/stock/hardware/engineering input.')
    if any(v<=0 for v in p['stock'].values()):raise ValueError('Stock dimensions, kerf and trims must be positive.')
    if p['engineering']['assumed_E_MPa']<=0:raise ValueError('Assumed E must be positive; this is not material verification.')
    d=copy.deepcopy(p);n=len(p['rail_bottoms'])
    if not n or len(p['brace_z_stations'])!=n+1:raise ValueError('Alderline needs one X bay per shelf and a terminating station.')
    if p['rail_thickness']!=p['post']:raise ValueError('Side rails must match the post thickness in this joinery.')
    h=p['brace_z_stations'][1]-p['brace_z_stations'][0]
    if h<=0 or any(abs(b-a-h)>1e-7 for a,b in zip(p['brace_z_stations'],p['brace_z_stations'][1:])):raise ValueError('Repeated X bays require equal positive heights.')
    d.update(post_length=p['height']-p['panel_thickness'],opening=p['frame_width']-2*p['post'],rail_length=p['frame_depth']-2*p['post'])
    d.update(top_rail_height=d['post_length']-p['top_rail_bottom'],shelf_width=d['opening']-2*p['shelf_side_clearance'],
       shelf_depth=p['frame_depth']-2*p['shelf_end_setback'],top_width=p['frame_width']+2*p['top_overhang'],top_depth=p['frame_depth']+2*p['top_overhang'])
    if min(d[k] for k in ['post_length','opening','rail_length','top_rail_height','shelf_width','shelf_depth'])<=0:raise ValueError('Inverted or collapsed furniture geometry.')
    b=p['brace_y_max']-p['brace_y_min'];w=p['brace_width']
    if not 0<w<b or not p['post']<=p['brace_y_min']<p['brace_y_max']<=p['frame_depth']-p['post']:raise ValueError('X slat width/end coordinates cannot fit the side bay.')
    if abs(p['brace_y_min']+p['brace_y_max']-p['frame_depth'])>1e-7:raise ValueError('Alderline end-screw rules require centred side-X extents; asymmetric placement needs a new joinery decision.')
    lo,hi=w,b
    for _ in range(90):
        q=(lo+hi)/2
        if q*h/math.hypot(h,b-q)>w:hi=q
        else:lo=q
    q=(lo+hi)/2;run=b-q;angle=math.atan2(h,run)
    d.update(brace_height=h,brace_run=run,brace_end_cut=q,brace_long_edge=math.hypot(h,run),brace_angle=math.degrees(angle),
      brace_miter=90-math.degrees(angle),brace_blank_min=math.hypot(h,run)+q*math.cos(angle),lap_along_edge=w/abs(math.sin(2*angle)),
      strap_hole_pitch=math.hypot(p['frame_width']-p['post'],p['strap_top_z']-p['strap_bottom_z']),side_overall_width=p['frame_width']+2*p['brace_thickness'])
    d['strap_cut_length']=d['strap_hole_pitch']+2*p['strap_end_allowance'];d['shelf_undersides']=[z+p['rail_height'] for z in p['rail_bottoms']]
    d['shelf_tops']=[z+p['panel_thickness'] for z in d['shelf_undersides']]
    d['shelf_screw_x']=[p['post']+p['cleat']/2,p['frame_width']-p['post']-p['cleat']/2]
    d['angle_x']=[p['post']+d['opening']*f for f in [.25,.75]]
    return d

def expected_ids(d):
    ids={f'A-{s}{e}' for s in ['L','R'] for e in ['F','R']}
    for s in ['L','R']:
        ids.add(f'C-{s}{len(d["rail_bottoms"])+1}')
        for i in range(1,len(d['rail_bottoms'])+1):ids.update([f'B-{s}{i}',f'G-{s}{i}',f'H-{s}{i}a',f'H-{s}{i}b'])
    ids.update(f'D-{i+1}' for i in range(len(d['rail_bottoms'])));ids.update(['E-1','F-F','F-R','J-1','J-2'])
    return ids

def catalog(d,parts):
    counts=Counter(p.group for p in parts)
    data=[('A','Posts',d['post'],d['post'],d['post_length'],'Hardwood','Square ends; matched finished stock.'),
      ('B','Shelf side rails',d['rail_thickness'],d['rail_height'],d['rail_length'],'Hardwood','Two rail dowels per end.'),
      ('C','Upper side rails',d['rail_thickness'],d['top_rail_height'],d['rail_length'],'Hardwood','Two rail dowels per end.'),
      ('D','Shelf panels',d['panel_thickness'],d['shelf_depth'],d['shelf_width'],'Cabinet plywood','Face grain along span; no notches.'),
      ('E','Top panel',d['panel_thickness'],d['top_depth'],d['top_width'],'Cabinet plywood',f"Overhang from frame: {measure(d['top_overhang'])}."),
      ('F','Front/rear top aprons',d['panel_thickness'],d['top_rail_height'],d['opening'],'Cabinet plywood','Two apron dowels per end.'),
      ('G','Shelf support cleats',d['cleat'],d['cleat'],d['rail_length'],'Hardwood','Transverse screws into side rails.'),
      ('H','X slats',d['brace_thickness'],d['brace_width'],d['brace_long_edge'],'Hardwood',f"{d['brace_miter']:.2f} deg off square; {measure(d['brace_thickness']/2)} lap; length along long edge."),
      ('J','Rear steel straps',d['strap_thickness'],d['strap_width'],d['strap_cut_length'],'Bracing steel',f"End-hole pitch {measure(d['strap_hole_pitch'])}; measure on squared case.")]
    return [dict(id=id,name=name,qty=counts[id],t=t,w=w,length=l,material=mat,note=note) for id,name,t,w,l,mat,note in data]

def connections(d,parts):
    cons=[];dowels=[];screws=[];W,T=d['frame_width'],d['frame_depth'];a=d['post'];n=len(d['rail_bottoms']);h=d['hardware']
    def add(id,targets,hardware,step):cons.append(dict(id=id,targets=targets,hardware=hardware,step=step))
    def screw(id,k,targets,start,axis,through,receiver):
        screws.append(dict(id=id,hardware=k,targets=targets,start=start,axis=axis,through=through,receiver=receiver,**h[k]))
    for p in parts:
        m=p.meta;side=m.get('side');x=0 if side=='L' else W-a
        if p.group in ['B','C']:
            z=m['z'];offs=d['rail_dowel_z_offsets'] if p.group=='B' else d['top_dowel_z_offsets']
            for e,y in [('F',a),('R',T-a)]:
                add(p.id+'-'+e,[p.id,f'A-{side}{e}'],{'K1':len(offs)},'side-frames')
                for off in offs:dowels.append(dict(id=f'{p.id}-{e}-{off:g}',start=[x+a/2,y-d['rail_dowel_embed'],z+off],axis=[0,1,0],radius=d['brace_dowel_diameter']/2,length=2*d['rail_dowel_embed'],targets=[p.id,f'A-{side}{e}']))
        if p.group=='F':
            y=d['panel_thickness']/2 if m['end']=='F' else T-d['panel_thickness']/2
            for side,xx in [('L',a),('R',W-a)]:
                add(p.id+'-'+side,[p.id,f'A-{side}{m["end"]}'],{'K2':len(d['top_dowel_z_offsets'])},'join-frame')
                for off in d['top_dowel_z_offsets']:dowels.append(dict(id=f'{p.id}-{side}-{off:g}',start=[xx-d['apron_dowel_embed'],y,d['top_rail_bottom']+off],axis=[1,0,0],radius=d['apron_dowel_diameter']/2,length=2*d['apron_dowel_embed'],targets=[p.id,f'A-{side}{m["end"]}']))
        if p.group=='G':
            rail=f'B-{side}{m["station"]+1}';z=d['shelf_undersides'][m['station']]-d['cleat']/2
            for i,y in enumerate(d['cleat_screw_y']):
                id=f'{p.id}-s{i+1}';add(id,[p.id,rail],{'K3':1},'cleats')
                screw(id,'K3',[p.id,rail],[a+d['cleat'] if side=='L' else W-a-d['cleat'],y,z],[-1 if side=='L' else 1,0,0],d['cleat'],a)
        if p.group=='D':
            for s,x in zip(['L','R'],d['shelf_screw_x']):
                for i,y in enumerate(d['shelf_screw_y']):
                    id=f'{p.id}-{s}-s{i+1}';target=f'G-{s}{m["station"]+1}';add(id,[p.id,target],{'K4':1},'shelves-top')
                    screw(id,'K4',[p.id,target],[x,y,d['shelf_tops'][m['station']]],[0,0,-1],d['panel_thickness'],d['cleat'])
        if p.group=='H':
            off=d['brace_end_screw_z_offset'];base=m['z'];rise=d['brace_height'];lower=d['brace_y_min']+d['brace_end_cut']/2+d['brace_run']*off/rise
            for i,(yy,zz) in enumerate([(lower,base+off),(T-lower,base+rise-off)]):
                if not m['ascending']:yy=T-yy
                ri=m['station']+i;rail=f'B-{side}{ri+1}' if ri<n else f'C-{side}{n+1}'
                id=f'{p.id}-s{i+1}';add(id,[p.id,rail],{'K5':1},'x-slats')
                screw(id,'K5',[p.id,rail],[-d['brace_thickness'] if side=='L' else W+d['brace_thickness'],yy,zz],[1 if side=='L' else -1,0,0],d['brace_thickness'],a)
        if p.group=='J':
            for i,z in enumerate([d['strap_bottom_z'],d['strap_top_z']]):
                side=('L' if i==0 else 'R') if p.id=='J-1' else ('R' if i==0 else 'L');xx=a/2 if side=='L' else W-a/2
                id=f'{p.id}-end{i+1}';amount={'K6':1}
                if p.id=='J-2':amount['K7']=1
                add(id,[p.id,f'A-{side}R'],amount,'back-restraints')
                th=d['strap_thickness']+(h['washer_thickness'] if p.id=='J-2' else 0)
                screw(id,'K6',[p.id,f'A-{side}R'],[xx,T+th,z],[0,-1,0],th,a)
    for end in ['F','R']:
        for i,x in enumerate(d['angle_x']):add(f'angle-{end}{i+1}',[f'F-{end}','E-1'],{'K8':1,'K9':2},'shelves-top')
    for side in ['L','R']:add('restraint-'+side,[f'A-{side}R'],{'K10':1},'back-restraints')
    for p in parts:
        if p.group=='A':add('pad-'+p.id,[p.id],{'K11':1},'finish')
    return cons,dowels,screws

def hardware(d,cons):
    h=d['hardware'];qty=hardware_counts(cons)
    names={'K1':f"Fluted dowel {metric(d['brace_dowel_diameter'])} × {metric(2*d['rail_dowel_embed'])} mm",'K2':f"Fluted dowel {metric(d['apron_dowel_diameter'])} × {metric(2*d['apron_dowel_embed'])} mm",
      **{k:f"{'Pan-head ' if k=='K6' else ''}wood screw {metric(h[k]['diameter'])} × {metric(h[k]['length'])} mm" for k in ['K3','K4','K5','K6','K9']},
      'K7':f"Washer {metric(h['washer_thickness'])} mm thick; clearance for K6",'K8':f"Steel angle {metric(h['angle_wing'])} × {metric(h['angle_wing'])} × {metric(h['angle_width'])} mm; one hole/wing",'K10':'Commercial furniture-to-wall restraint kit','K11':'Equal non-slip foot pad'}
    return [dict(id=k,quantity=qty[k],description=names[k]) for k in sorted(names,key=lambda k:int(k[1:]))]

def steps(d,parts,cons):
    ids=lambda gs:[p.id for p in parts if p.group in gs];levels=lambda a:' / '.join(metric(x) for x in a);n=len(d['rail_bottoms']);m=measure
    messages=[('side-frames','Build the two matched sides','ABC',
      f"Label left/right and front/rear posts viewed from the front. Set side rail bottoms at {levels(d['rail_bottoms'])} mm from the finished feet; upper rail starts at {m(d['top_rail_bottom'])}. Seat two {m(d['brace_dowel_diameter'])} dowels per rail end. Rail end bores are thickness-centred; lower rail height offsets are {levels(d['rail_dowel_z_offsets'])} mm; upper offsets {levels(d['top_dowel_z_offsets'])} mm. Drill {m(d['rail_dowel_embed']+d['design_rules']['bore_bottom_clearance'])} deep for {m(d['rail_dowel_embed'])} nominal embed in each member. Dry-fit, glue, clamp flat and square; matched side depth {m(d['frame_depth'])}."),
      ('x-slats','Fit the repeated exterior Xs','ABCH',
      f"Make {2*n} complementary pairs of slats. Clamp a scrap jig with end planes {m(d['brace_height'])} apart and outside edges {m(d['brace_y_max']-d['brace_y_min'])} apart. End cuts are parallel, {d['brace_miter']:.2f} degrees off square. Finished long-edge length {m(d['brace_long_edge'])}; use {m(d['brace_rough_blank_length'])} rough blanks. Mark the intersection rhombus and remove {m(d['brace_thickness']/2)} from opposite faces. Test before batch cutting. End planes are {levels(d['brace_z_stations'])} mm. One K5 screw per end, centred across each slat and {m(d['brace_end_screw_z_offset'])} vertically in from the cut plane. Clamp, pilot and drive flush. Glue only a well-fitted lap."),
      ('cleats','Install the inward shelf cleats','ABCGH',
      f"Keep G tops level with the B tops at {levels(d['shelf_undersides'])} mm. Cleats project {m(d['cleat'])} into the opening. At each cleat drive K3 from its inside face toward B, at y = {levels(d['cleat_screw_y'])} mm and {m(d['cleat']/2)} below its top. Do not move screws onto the X end screw lines. Check straightness and full bearing."),
      ('join-frame','Connect sides with the two aprons','ABCFGH',
      f"Use a helper. Maintain {m(d['opening'])} between inner post faces and {m(d['frame_width'])} across the frame. Aprons occupy z = {metric(d['top_rail_bottom'])}–{metric(d['post_length'])} mm; outer faces flush to front/rear posts. Two {m(d['apron_dowel_diameter'])} dowels per apron end: thickness centre {m(d['panel_thickness']/2)}, height offsets {levels(d['top_dowel_z_offsets'])} mm. Drill {m(d['apron_dowel_embed']+d['design_rules']['bore_bottom_clearance'])} deep for {m(d['apron_dowel_embed'])} embed in each member. Dry-fit, glue and clamp square. Keep temporary support until cured and back bracing is installed."),
      ('shelves-top','Secure the shelves and separate top','ABCDEFGH',
      f"Shelf underside levels: {levels(d['shelf_undersides'])} mm; tops: {levels(d['shelf_tops'])} mm. Maintain {m(d['shelf_side_clearance'])} side clearance and {m(d['shelf_end_setback'])} front/rear setback. Four K4 per shelf: x = {levels(d['shelf_screw_x'])}, y = {levels(d['shelf_screw_y'])} mm. Clearance-drill the shelf, pilot the cleat and countersink flush. Centre the top for {m(d['top_overhang'])} overhang from the frame. Fix two K8 angles to the inner face of each apron at x = {levels(d['angle_x'])} mm. Use one K9 into the apron and one into the top per angle. Actual fitting is the drill template; verify tips cannot emerge."),
      ('back-restraints','Brace the rear and anchor to the wall','ABCDEFGHIJ',
      f"Square the case. Rear strap anchors are at post centres x = {metric(d['post']/2)} / {metric(d['frame_width']-d['post']/2)} mm and z = {metric(d['strap_bottom_z'])} / {metric(d['strap_top_z'])} mm. Target hole pitch {m(d['strap_hole_pitch'])}; leave {m(d['strap_end_allowance'])} beyond each end hole. Drill clearance {m(d['hardware']['strap_hole_diameter'])}; deburr. Fit J-1 against the back, J-2 behind it with K7 washers at both ends. Use K6; snug without bowing the case. Fit two manufacturer-selected wall restraints near z = {m(d['restraint_z'])}. Avoid bores and concealed services; verify actual wall structure and screw paths. Do not load before restraint installation."),
      ('finish','Finish, level and inspect before use','ABCDEFGHIJ',
      'Ease accessible edges, sand to the finish maker’s guidance and keep glue faces clean. Cure all adhesive and finish fully. Fit equal non-slip pads and confirm four-foot bearing without rocking. Check every joint, shelf bearing, exposed screw and steel edge. Recheck restraints after relocation. Place heavier contents low; do not climb or sit on shelves. No safe working load has been established.')]
    return [dict(id=id,title=title,parts=ids(gs),connection_ids=[c['id'] for c in cons if c['step']==id],groups=gs,text=text) for id,title,gs,text in messages]

def build(p):
    d=derive(p);parts=geometry(d);cat=catalog(d,parts);cons,dowels,screws=connections(d,parts)
    plan={'families':[('A',['A']),('B-C',['B','C']),('G',['G']),('H',['H'])],'blank_lengths':{'H':d['brace_rough_blank_length']},
      'sheet_description':f"Cabinet plywood {d['panel_thickness']:g} x {d['stock']['sheet_width']:g} x {d['stock']['sheet_length']:g} mm",
      'extra_purchases':[dict(id='STEEL',quantity=sum(p.group=='J' for p in parts),description=f"Bracing strip {d['strap_thickness']:g} x {d['strap_width']:g}; rough length at least {d['strap_cut_length']+d['stock']['end_trim']*2:.1f} mm")]}
    return Design(p,d,parts,cat,cons,hardware(d,cons),steps(d,parts,cons),dowels,screws,{'colors':COLORS},plan)

def engineering(d):
    """Illustrative assumptions only. No accept/reject structural criterion."""
    e=d['engineering'];L=d['opening'];t=d['panel_thickness'];b=d['shelf_depth'];I=b*t**3/12
    mass=d['shelf_width']*b*t*e['assumed_plywood_density_kg_m3']/1e9;F=(e['illustrative_mass_kg_per_shelf']+mass)*e['gravity_m_s2'];w=F/L
    return dict(status='ASSUMPTION-BASED ILLUSTRATION; NOT A LOAD RATING',assumed_effective_E_MPa=e['assumed_E_MPa'],span_mm=L,
      assumed_contents_mass_kg=e['illustrative_mass_kg_per_shelf'],self_mass_kg=mass,I_mm4=I,
      instantaneous_deflection_mm=5*w*L**4/(384*e['assumed_E_MPa']*I),bending_stress_MPa=w*L**2*t/(16*I),
      limitations=['Effective E and density not supplier-verified.','Gross section; simply supported; uniform load; no creep, impact, defects, orthotropy, connections, racking or tipping.',
       'No allowable stress, fastener capacity, acceptance threshold or working load assigned.','Width variant requires a new structural review and physical tests.'])
