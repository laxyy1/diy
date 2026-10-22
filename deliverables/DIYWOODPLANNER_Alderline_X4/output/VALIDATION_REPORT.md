# DIYWOODPLANNER Alderline X4 / P1 validation

GEOMETRY CHECKS PASS

These are computational and document checks, not evidence of structural safety.

- PASS — Delivered STEP solid count: 47 solids vs schedule 47
- PASS — Valid positive CAD solids: OpenCascade validity and positive volume on every STEP solid
- PASS — Overall envelope: X -18.000..918.000; Y -10.000..360.000; Z 0.000..1800.000 mm
- PASS — No unintended solid interpenetration: 8 bounding-box candidates; positive intersections >0.01 mm3: []
- PASS — Shelf assembly clearance: 0.5 mm per side; dry-fit and trim only within measured opening
- PASS — Shelf bearing: 29.5 mm minimum bearing width on each side cleat; bearing length 260 mm
- PASS — Shelf levels: Undersides: [160.0, 560.0, 960.0, 1360.0]; tops [178.0, 578.0, 978.0, 1378.0] mm
- PASS — Brace width and end geometry: Independent normal-distance calculation 35.000000 mm; end-cut projection 39.163960 mm
- PASS — Brace stock sufficiency: 490 mm blank > 465.161 mm theoretical extremity length + 10 mm allowance
- PASS — Half-lap removal: 16 slats match theoretical volume 268233.632 mm3; 9+9=18 mm lap thickness
- PASS — Dowel quantity: 40 of 8 x 50; 8 of 6 x 40. Two embeds per dowel: 25+25 and 20+20 mm
- PASS — All dowel mating bores align in STEP: 48 independently placed nominal dowel cylinders have no wood interference; blocked paths []
- PASS — Dowel edge ligaments: 8 mm bores: 18.5 mm side ligament; 6 mm apron bores: 6 mm face ligament. Physical joint tests still required
- PASS — Blind drilling through-wall allowance: 26 mm post/rail bore and 21 mm apron bore drilling depth; dowel embed remains 25/20 mm
- PASS — Nominal screw tip containment: {'K3': 30, 'K4': 22, 'K5': 27, 'K6first': 34, 'K6second': 33, 'K9': 14} mm; nominal, not capacities; verify actual hardware
- PASS — Brace screw rail backing: First ascending lower screw (y,z)=(84.624,145); upper=(265.376,505) mm; 15 mm min rail-edge distance
- PASS — Opposing brace/cleat screw clearance: Minimum centreline spacing 25.376 mm; 4 and 5 mm screw axes remain distinct. Cleat Y stations 110/175/240
- PASS — Strap hole pitch: 1814.118 mm centre pitch; 25 mm end allowance each
- PASS — Stock layout A: 4 boards; 1 blanks per board; conservative length use 1805 / 2400 mm
- PASS — Stock layout B/C: 2 boards; 5 blanks per board; conservative length use 1335 / 2400 mm
- PASS — Stock layout G: 1 boards; 8 blanks per board; conservative length use 2124 / 2400 mm
- PASS — Stock layout H: 4 boards; 4 blanks per board; conservative length use 1992 / 2400 mm
- PASS — Plywood nesting: 1 sheet 2440 x 1220 x 18; seven pieces with >=20 mm gaps in diagram layout
- PASS — Beam calculation units and finite results: N, mm, MPa throughout; gross-section simply-supported UDL illustration only

## Engineering illustration

```json
{
  "span_mm": 810.0,
  "assumed_E_MPa": 6000.0,
  "breadth_mm": 348.0,
  "thickness_mm": 18.0,
  "I_mm4": 169128.0,
  "assumed_contents_mass_kg": 20,
  "panel_self_mass_kg": 3.2939244,
  "total_force_N": 228.51339836400004,
  "instant_deflection_mm": 1.5582557640325299,
  "bending_stress_MPa": 1.2312144308405175
}
```

E = 6,000 MPa is an assumed effective bending modulus, not a supplier property. Span 810 mm is a conservative full-opening idealization; real bearing is 29.5 mm on each cleat. Face grain runs along span. Uniform contents load of 20 kg plus self-weight is an illustrative scenario, not a recommended load. Formula: I=bt³/12; w=F/L; delta=5wL⁴/(384EI); sigma=wL²t/(16I). No allowable stress comparison is made. Orthotropy, defects, duration, creep, impact, fastener slip, connections, bracing, wall construction and tipping are excluded. No fastener capacities have been assigned.

## Unresolved / commercial release gates

- No physical prototype, structural load, creep, racking or tip testing performed.
- Purchased hardware and wall restraint product not selected or capacity-verified.
- Wood species/grade, moisture, plywood stiffness and exact manufactured thickness unverified.
- No safe working load or commercial-release certification established.
- Pilot holes and purchased brackets/restraints are diagrammatic, not detailed CAD hardware.

## Scope and tolerances

Metric dimensions control. Overall envelope excludes foot pads and installed wall restraints. Cut square parts to ±0.5 mm, matched rails to ±0.25 mm, and jig-bored hole centres to ±0.25 mm as workshop targets, not guaranteed fit. Blind bores drill 1 mm beyond nominal dowel embed using a stop. Lap depth target 9.0 mm per member; fit on scrap first. Exact 18/45 mm finished stock is required; a change in actual stock requires updating parameters and regenerating/rechecking before cutting.

## Drawing and document QA

All 15 final PDF pages were rendered and visually inspected. Automated page-bound and text-overlap checks found zero issues. The DXF reports millimetre units and two closed polylines (profile and lap). The brace profile area and lap rhombus area passed separate analytic checks. Dimensioned, boring-map, brace-fabrication and exploded SVG sheets were exported from the final PDF. See `qa/pdf_qa.json` for the final PDF hash.

Resolved during production: a candidate opposing screw-line clash, table column overprinting, a note crossing the drilling map, missing saw-kerf spacing in a preliminary sheet layout, crowded lower page spacing and disconnected apron callouts. These have been corrected in the delivered issue. No unresolved computational failure remains. Physical testing and purchased-product verification remain unperformed.

The CAD model is parametric; the P1 prose and presentation annotations are release-controlled by a parameter-file SHA-256 guard. Dimensional variants require a narrative/annotation review before issuing a new PDF.

Commercial release checklist: see `../COMMERCIAL_REVIEW_CHECKLIST.md` and manual page 14.
