"""Customer-facing Alderline instructions, generated from the canonical design graph."""
import json,math
from ..common import measure,metric,size,imperial_size,hardware_counts,read_csv

def content(design,out,layouts):
    d=design.dimensions;m=measure;f=metric;sections=[]
    text=lambda s:dict(type='text',text=s)
    fig=lambda name,**kwargs:dict(type='figure',name=name,**kwargs)
    def section(title,*items):sections.append(dict(title=title,items=list(items)))
    section('Alderline X4',text('FOUR-SHELF X-FRAME BOOKSHELF • ORIGINAL WORKSHOP PLAN'),
      text('An open bookshelf with timber posts, repeated half-lapped side Xs, plywood shelves and a separate top. Rear steel cross-straps brace the open back. This is a prototype plan: build and test before commercial release.'),
      fig('hero',height=370),text(f"Maximum size: {m(d['side_overall_width'])} wide × {m(d['top_depth'])} deep × {m(d['height'])} high. Intermediate skill; dowel jig, controlled half-lap routing and two-person final assembly."),
      text('Metric dimensions control; imperial values are rounded decimal-inch equivalents. No safe working load has been established. Wall restraints are required before loading.'))
    section('Measured front elevation',fig('front',height=405,dimensions=True),
      *[text(f'{label}: {m(d[key])}') for label,key in [('Frame width','frame_width'),('Opening','opening'),('Shelf length','shelf_width'),('Top width','top_width'),('Overall width','side_overall_width')]],
      text(f"The X slats project {m(d['brace_thickness'])} beyond each frame side. Height excludes foot pads and wall restraint fittings."))
    levels=[[str(i+1),m(z),m(d['shelf_tops'][i])] for i,z in enumerate(d['shelf_undersides'])]
    section('Side geometry & shelf levels',fig('side',height=370,dimensions=True),
      dict(type='table',headers=['Shelf','Underside above floor','Top above floor'],rows=levels,widths=[60,228,228]),
      text(f"Shelf bearing on each cleat: {m(d['cleat']-d['shelf_side_clearance'])} wide × {m(d['rail_length'])} long. Side clearance: {m(d['shelf_side_clearance'])} each; front/rear setback: {m(d['shelf_end_setback'])} each."))
    section('Cut list / finished parts',text('Thickness × width × length. Use actual finished stock. Inspect plywood bearing edges for voids; orient face grain along the shelf length. H length is along either long edge, not the rough blank.'),
      dict(type='table',headers=['ID / QTY','Part & material','Finished dimensions','Cutting detail'],widths=[58,123,164,171],rows=[
        [f"{r['id']} / {r['qty']}",r['name']+'<br/>'+r['material'],size(r)+'<br/>'+imperial_size(r),r['note']] for r in design.catalog]))
    section('Hardware & joint schedule',text('Installed quantities below are counted from connection sites. Buy spare fasteners and test actual pilot sizes in matching scrap. Purchased products remain to be selected and verified.'),
      dict(type='table',headers=['ID / QTY','Hardware','Allocation'],widths=[65,255,196],rows=[
        [f"{r['id']} / {r['quantity']}",r['description'],allocation(r['id'],d)] for r in design.hardware]),
      text('Use wood adhesive appropriate to the selected timber and follow its cure instructions. Top angles assume two steel wings with one hole each. Do not substitute wall fixings without checking the actual wall and chosen restraint system.'))
    buy=read_csv(out/'purchasing.csv')
    section('Material purchasing & plywood',text('Layouts are feasible purchasing maps, not optimized saw sequences. They reserve end trims and kerf; buy additional stock for knots, tear-out and defects.'),
      dict(type='table',headers=['Stock','Quantity','Purchase basis'],rows=[[r['id'],r['quantity'],r['description']] for r in buy],widths=[60,60,396]),
      text(f"Crosscut kerf {m(d['stock']['kerf'])}; end trim {m(d['stock']['end_trim'])}; sheet separation at least {m(max(d['stock']['nest_gap'],d['stock']['kerf']))}. All plywood grain runs horizontally in the maps."),
      *[dict(type='stock',record=s,plywood=True) for s in layouts['plywood']])
    section('Lumber cutting maps',text('Each band represents one purchased board. Dimensions label rough blank lengths. B and C share wider stock; rip B to its listed height after crosscutting. H blanks include angled-end allowance.'),
      *[dict(type='stock',record=b) for b in layouts['lumber']],
      text('Residual material includes crosscut kerfs, end trims and offcuts. Ripping waste and defects are not quantified. Never use a small offcut where safe clamping or a guarded cut cannot be maintained.'))
    spec={'height':220,'rects':[],'holes':[],'labels':[]}
    for x,g,w,h,offsets,diam in [(20,'B',d['post'],d['rail_height'],d['rail_dowel_z_offsets'],d['brace_dowel_diameter']),
        (190,'C',d['post'],d['top_rail_height'],d['top_dowel_z_offsets'],d['brace_dowel_diameter']),
        (370,'F',d['panel_thickness'],d['top_rail_height'],d['top_dowel_z_offsets'],d['apron_dowel_diameter'])]:
        scale=1.5;spec['rects'].append([x,30,w*scale,h*scale]);spec['holes'] += [[x+w*scale/2,30+z*scale,diam*scale/2] for z in offsets]
        spec['labels'] += [[x,200,f'{g} END / Ø{f(diam)} mm'],[x,180,f'{f(w)} × {f(h)} mm'],[x,12,'Bores centred in thickness']]
    bore_rows=[]
    for i,z in enumerate(d['rail_bottoms']):bore_rows.append([f'B station {i+1}',m(z),' / '.join(f(z+o) for o in d['rail_dowel_z_offsets'])+' mm'])
    bore_rows.append(['C and F',m(d['top_rail_bottom']),' / '.join(f(d['top_rail_bottom']+o) for o in d['top_dowel_z_offsets'])+' mm'])
    section('Dowel joints / enlarged end views',dict(type='diagram',spec=spec),
      dict(type='table',headers=['Joint','Member bottom level','Post bore heights from foot'],rows=bore_rows,widths=[110,180,226]),
      text(f"Side rail/post mating bores: Ø{f(d['brace_dowel_diameter'])}, nominal embed {m(d['rail_dowel_embed'])} per member. Apron/post bores: Ø{f(d['apron_dowel_diameter'])}, nominal embed {m(d['apron_dowel_embed'])} per member. Drill each blind hole {m(d['design_rules']['bore_bottom_clearance'])} deeper than nominal embed using a stop."),
      text(f"A side-rail bores are on the front/rear post faces facing the side rails, centred {m(d['post']/2)} across the face. Apron bores face across the opening, {m(d['panel_thickness']/2)} from the front/rear outside post edge. Mirror left/right and front/rear posts. Use one finished foot datum for every height. Test the complete joint on scrap before drilling parts."))
    section('The half-lapped X / close-up',fig('lap-closeup',height=300,labels=['H-R1a','H-R1b']),
      text(f"Complementary laps remove {m(d['brace_thickness']/2)} from opposite faces. The overlap is a rhombus with {m(d['lap_along_edge'])} along either long edge; its boundaries parallel the mating slat edges. The close-up separates the members for inspection."),
      text(f"End cut: {d['brace_miter']:.2f}° off square. Finished long-edge length {m(d['brace_long_edge'])}; minimum projected extremity length {m(d['brace_blank_min'])}. Start from {m(d['brace_rough_blank_length'])} rough blanks. The horizontal end-cut projection is {m(d['brace_end_cut'])}."),
      text('Use a full-size scrap bay jig. Mark the true crossed overlap, route/saw waste in shallow controlled passes, and keep faces flat. Test for a flush, non-forced fit before repeating. The supplied 1:1 A4/Letter PDFs must be printed at actual size and calibrated with a ruler; they are patterns, not safe router fixtures.'))
    for i,step in enumerate(design.steps,1):
        last=len(d['rail_bottoms'])
        callouts={'side-frames':['A-RF','A-RR','B-R1',f'C-R{last+1}'],'x-slats':['H-R1a','H-R1b','B-R1',f'C-R{last+1}'],
          'cleats':['G-R1',f'G-R{last}','B-R1','A-RF'],'join-frame':['F-F','F-R','A-LF','A-RF'],
          'shelves-top':['E-1','D-1',f'D-{last}','G-L1','F-F'],'back-restraints':['J-1','J-2','A-LR','A-RR'],'finish':[]}
        qty=hardware_counts([c for c in design.connections if c['step']==step['id']]);hw=', '.join(f'{k} ×{n}' for k,n in qty.items())
        section(f'{i:02d} / {step["title"]}',fig(step['id'],height=320,labels=callouts[step['id']]),text('Part identifiers: '+', '.join(step['parts'])),text('Hardware for this step: '+(hw or 'None.')),text(step['text']))
    section('Complete exploded assembly',fig('exploded',height=500,labels=['A-LF','D-2','E-1','F-F','H-R1a','J-2']),
      text('Part offsets are illustrative. Use the dimensions and sequence in this manual, not distances measured from this exploded drawing. The dashed J-2 callout identifies the strap behind the apron; see the rear assembly view for its visible connection. Connection/pilot holes and purchased brackets/restraints are not fully represented as CAD hardware.'))
    section('Print, inspect & maintain',text('Print the manual on US Letter at a comfortable reading scale. The separate template_A4.pdf and template_Letter.pdf files are actual-size fabrication patterns: disable “fit”, print at 100%, check the 100 mm horizontal and 50 mm vertical bars, then trim and tape matching coordinates with the documented overlap.'),
      text('Before use: check all four feet bear evenly; every shelf bears fully; no splits, loose dowels, open glue joints, proud screw tips or sharp steel remain. Confirm both restraints and sound wall structure according to the manufacturer. Recheck after relocation and whenever rocking or looseness develops.'),
      text('Before commercial sale: commission an independent prototype build, verify selected materials and hardware, and obtain qualified strength, sustained-load creep, racking, impact, tip and installation testing. The plan assigns no safe working load. A dimension change requires renewed review; digital fit checks do not replace physical evidence.'),
      text('Use guarded tools, clamps, dust extraction and suitable eye/hearing protection. Check for concealed services before wall drilling. Follow adhesive/finish ventilation and waste-handling guidance. Keep heavy contents low; do not climb or sit on the case.'))
    return dict(title=f"DIYWOODPLANNER Alderline X4 / frame {f(d['frame_width'])} mm",short_title=f"ALDERLINE X4 / {f(d['frame_width'])} mm / DEVELOPMENT",sections=sections)

def allocation(id,d):
    return {'K1':'Two per rail end into A.','K2':'Two per apron end into A.','K3':f"{len(d['cleat_screw_y'])} per G into B.",'K4':f"{2*len(d['shelf_screw_y'])} per D into G.",'K5':'One at each H end into B/C.','K6':'One per J end into rear posts.','K7':'Behind both ends of J-2.','K8':'Two on each F, supporting E.','K9':'One per angle wing.','K10':'One at each rear post; product-specific wall fixings.','K11':'One per A foot.'}[id]
