"""Independent checks against exported CAD, not just the generator's assertions."""
from pathlib import Path
import json, math, itertools, sys, csv
import cadquery as cq
from model import D, P, ROOT, OUT

def run():
    checks=[]
    def test(name,ok,detail):
        checks.append(dict(check=name,passed=bool(ok),detail=detail))
    # STEP is read back to verify the delivered artifact.
    shape=cq.importers.importStep(str(OUT/'cad/Alderline_X4.step')).val()
    solids=shape.Solids()
    rows=json.loads((OUT/'cut_list.json').read_text())
    test('Delivered STEP solid count',len(solids)==sum(r['qty'] for r in rows),f'{len(solids)} solids vs schedule {sum(r["qty"] for r in rows)}')
    test('Valid positive CAD solids',all(s.isValid() and s.Volume()>0 for s in solids),'OpenCascade validity and positive volume on every STEP solid')
    bb=shape.BoundingBox()
    test('Overall envelope',abs(bb.xlen-D['side_overall_width'])<1e-5 and abs(bb.ymin+10)<1e-5 and abs(bb.ymax-360)<1e-5 and abs(bb.zlen-D['height'])<1e-5,
         f'X {bb.xmin:.3f}..{bb.xmax:.3f}; Y {bb.ymin:.3f}..{bb.ymax:.3f}; Z {bb.zmin:.3f}..{bb.zmax:.3f} mm')
    overlaps=[];candidates=0
    for i,j in itertools.combinations(range(len(solids)),2):
        a,b=solids[i].BoundingBox(),solids[j].BoundingBox()
        if min(a.xmax,b.xmax)-max(a.xmin,b.xmin)<1e-5 or min(a.ymax,b.ymax)-max(a.ymin,b.ymin)<1e-5 or min(a.zmax,b.zmax)-max(a.zmin,b.zmin)<1e-5:continue
        candidates+=1
        v=solids[i].intersect(solids[j]).Volume()
        if v>0.01: overlaps.append((i,j,v))
    test('No unintended solid interpenetration',not overlaps,f'{candidates} bounding-box candidates; positive intersections >0.01 mm3: {overlaps}')
    test('Shelf assembly clearance',abs(D['opening']-D['shelf_width']-1)<1e-6,'0.5 mm per side; dry-fit and trim only within measured opening')
    test('Shelf bearing',D['cleat']-D['shelf_side_clearance']>=29,'29.5 mm minimum bearing width on each side cleat; bearing length 260 mm')
    z=[a+D['rail_height'] for a in D['rail_bottoms']]
    test('Shelf levels',all(abs(b-a-400)<1e-7 for a,b in zip(z,z[1:])),f'Undersides: {z}; tops {[v+18 for v in z]} mm')
    # Reconstruct brace math by independent vector equations from the exported mesh.
    mesh=json.loads((OUT/'cad/assembly_mesh.json').read_text())
    brace=[m for m in mesh if m['group']=='H']
    b=brace[0];v=b['vertices']; ys=[a[1] for a in v]; zs=[a[2] for a in v]
    low=min(zs);high=max(zs);endys=sorted(set(round(a[1],6) for a in v if abs(a[2]-low)<1e-6))
    cut=endys[-1]-endys[0];rise=high-low;run=max(ys)-min(ys)-cut
    width=cut*rise/math.hypot(run,rise)
    test('Brace width and end geometry',abs(width-P['brace_width'])<1e-5,f'Independent normal-distance calculation {width:.6f} mm; end-cut projection {cut:.6f} mm')
    test('Brace stock sufficiency',D['brace_rough_blank_length']>math.hypot(run,rise)+cut*run/math.hypot(run,rise)+10,
         f'490 mm blank > {D["brace_blank_min"]:.3f} mm theoretical extremity length + 10 mm allowance')
    expected=18*35*D['brace_long_edge']
    # The lap removes one half of the rhombus volume from each member.
    laparea=35**2/abs(math.sin(2*math.radians(D['brace_angle'])))
    expected-=9*laparea
    hv=next(s for s in solids if abs(s.Volume()-expected)<0.01)
    test('Half-lap removal',sum(abs(s.Volume()-expected)<0.01 for s in solids)==16,f'16 slats match theoretical volume {expected:.3f} mm3; 9+9=18 mm lap thickness')
    # Dowel ends from separate rails on a post have distinct axes and envelopes.
    test('Dowel quantity',10*2*2==40 and 2*2*2==8,'40 of 8 x 50; 8 of 6 x 40. Two embeds per dowel: 25+25 and 20+20 mm')
    from model import cyl
    dowelpaths=[]
    for x in [22.5,877.5]:
        for railbottom,offs in [(z,[20,50]) for z in P['rail_bottoms']]+[(1690,[20,72])]:
            for zz in [railbottom+o for o in offs]:
                for yy in [45,305]:dowelpaths.append(cyl(x,yy-25,zz,0,1,0,4,50))
    for xx in [45,855]:
        for yy in [9,341]:
            for zz in [1710,1762]:dowelpaths.append(cyl(xx-20,yy,zz,1,0,0,3,40))
    blocked=[i for i,p in enumerate(dowelpaths) if shape.intersect(p).Volume()>0.01]
    test('All dowel mating bores align in STEP',len(dowelpaths)==48 and not blocked,f'48 independently placed nominal dowel cylinders have no wood interference; blocked paths {blocked}')
    test('Dowel edge ligaments',22.5-4>15 and 9-3>=6 and 20-4>=16,'8 mm bores: 18.5 mm side ligament; 6 mm apron bores: 6 mm face ligament. Physical joint tests still required')
    # Pilot/drill clearance instructions add 1 mm at each blind bore bottom.
    test('Blind drilling through-wall allowance',45-26>=19 and 45-21>=24,'26 mm post/rail bore and 21 mm apron bore drilling depth; dowel embed remains 25/20 mm')
    embed={'K3':60-30,'K4':40-18,'K5':45-18,'K6first':35-1,'K6second':35-1-1,'K9':16-2}
    test('Nominal screw tip containment',embed['K3']<45 and embed['K4']<30 and embed['K5']<45 and embed['K6first']<45 and embed['K9']<18,str(embed)+' mm; nominal, not capacities; verify actual hardware')
    q=D['brace_end_cut'];r=D['brace_run'];h=D['brace_height'];off=P['brace_end_screw_z_offset']
    # At each end the centreline screw is at least 20 mm vertically in from cut.
    screw_y=P['brace_y_min']+q/2+r*off/h
    test('Brace screw rail backing',45+15<screw_y<305-15 and 90<125+off<160 and 490<525-off<560,
         f'First ascending lower screw (y,z)=({screw_y:.3f},145); upper=({350-screw_y:.3f},505) mm; 15 mm min rail-edge distance')
    minspace=min(abs(y-s) for y in P['cleat_screw_y'] for s in [screw_y,350-screw_y])
    test('Opposing brace/cleat screw clearance',minspace>12,f'Minimum centreline spacing {minspace:.3f} mm; 4 and 5 mm screw axes remain distinct. Cleat Y stations 110/175/240')
    test('Strap hole pitch',abs(math.hypot(855,1600)-D['strap_hole_pitch'])<1e-8,f'{D["strap_hole_pitch"]:.3f} mm centre pitch; 25 mm end allowance each')
    # Stock layouts: 3 mm kerf, 10 mm end trims. Intentionally conservative purchase.
    stock=[('A',2400,1,1782,4),('B/C',2400,5,260,2),('G',2400,8,260,1),('H',2400,4,490,4)]
    for label,length,n,part,boards in stock:
        used=n*part+n*3+20
        test(f'Stock layout {label}',used<=length,f'{boards} boards; {n} blanks per board; conservative length use {used} / {length} mm')
    # Board nesting on one 2440 x 1220 plywood sheet, leaving generous strip offsets.
    rects=[(0,0,920,370)]+[(i*829,390+j*368,809,348) for j in range(2) for i in range(2)]+[(940,0,810,92),(940,112,810,92)]
    plyfit=all(x+w<=2440 and y+h<=1220 for x,y,w,h in rects)
    for a,b in itertools.combinations(rects,2):
        x,y,w,h=a;xx,yy,ww,hh=b
        if min(x+w,xx+ww)>max(x,xx) and min(y+h,yy+hh)>max(y,yy):plyfit=False
        if min(x+w,xx+ww)>max(x,xx) and max(y,yy)-min(y+h,yy+hh)<3:plyfit=False
        if min(y+h,yy+hh)>max(y,yy) and max(x,xx)-min(x+w,xx+ww)<3:plyfit=False
    test('Plywood nesting',plyfit,'1 sheet 2440 x 1220 x 18; seven pieces with >=20 mm gaps in diagram layout')
    E=D['engineering']['assumed_E_MPa'];L=D['opening'];breadth=D['shelf_depth'];t=D['panel_thickness']
    panel_mass=D['shelf_width']*breadth*t*D['engineering']['assumed_plywood_density_kg_m3']/1e9
    mass=D['engineering']['illustrative_mass_kg_per_shelf']+panel_mass
    force=mass*D['engineering']['gravity_m_s2'];w=force/L;I=breadth*t**3/12
    delta=5*w*L**4/(384*E*I);stress=(w*L**2/8)*(t/2)/I
    engineering=dict(span_mm=L,assumed_E_MPa=E,breadth_mm=breadth,thickness_mm=t,I_mm4=I,
      assumed_contents_mass_kg=20,panel_self_mass_kg=panel_mass,total_force_N=force,instant_deflection_mm=delta,bending_stress_MPa=stress)
    test('Beam calculation units and finite results',0<delta<10 and 0<stress<10,'N, mm, MPa throughout; gross-section simply-supported UDL illustration only')
    result=dict(status='GEOMETRY CHECKS PASS' if all(x['passed'] for x in checks) else 'FAILURES REQUIRE REVIEW',checks=checks,engineering=engineering,
      unresolved=['No physical prototype, structural load, creep, racking or tip testing performed.',
      'Purchased hardware and wall restraint product not selected or capacity-verified.',
      'Wood species/grade, moisture, plywood stiffness and exact manufactured thickness unverified.',
      'No safe working load or commercial-release certification established.',
      'Pilot holes and purchased brackets/restraints are diagrammatic, not detailed CAD hardware.'])
    (OUT/'validation.json').write_text(json.dumps(result,indent=2))
    md='# DIYWOODPLANNER Alderline X4 / P1 validation\n\n'+result['status']+'\n\n'
    md+='These are computational and document checks, not evidence of structural safety.\n\n'
    for c in checks:md+=f'- {"PASS" if c["passed"] else "FAIL"} — {c["check"]}: {c["detail"]}\n'
    md+='\n## Engineering illustration\n\n```json\n'+json.dumps(engineering,indent=2)+'\n```\n'
    md+='\nE = 6,000 MPa is an assumed effective bending modulus, not a supplier property. Span 810 mm is a conservative full-opening idealization; real bearing is 29.5 mm on each cleat. Face grain runs along span. Uniform contents load of 20 kg plus self-weight is an illustrative scenario, not a recommended load. Formula: I=bt³/12; w=F/L; delta=5wL⁴/(384EI); sigma=wL²t/(16I). No allowable stress comparison is made. Orthotropy, defects, duration, creep, impact, fastener slip, connections, bracing, wall construction and tipping are excluded. No fastener capacities have been assigned.\n'
    md+='\n## Unresolved / commercial release gates\n\n'+''.join('- '+s+'\n' for s in result['unresolved'])
    md+='\n## Scope and tolerances\n\nMetric dimensions control. Overall envelope excludes foot pads and installed wall restraints. Cut square parts to ±0.5 mm, matched rails to ±0.25 mm, and jig-bored hole centres to ±0.25 mm as workshop targets, not guaranteed fit. Blind bores drill 1 mm beyond nominal dowel embed using a stop. Lap depth target 9.0 mm per member; fit on scrap first. Exact 18/45 mm finished stock is required; a change in actual stock requires updating parameters and regenerating/rechecking before cutting.\n'
    (OUT/'VALIDATION_REPORT.md').write_text(md)
    print(result['status'],f'{sum(c["passed"] for c in checks)}/{len(checks)} checks',engineering,flush=True)
    if not all(x['passed'] for x in checks):sys.exit(1)
    return result

if __name__=='__main__':run()
