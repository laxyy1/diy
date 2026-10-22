# Development implementation report

Implemented in `development/woodworking-plan-production`. P1 is preserved unchanged.
This is a Codex production workflow, not an application, service, API or interface.

## Executed evidence

| Run | Result |
|---|---|
| Canonical 900 mm frame | **187/187 artifact checks pass**; 47 individual STEP solids plus assembly; 18-page customer manual |
| Separate 1000 mm frame configuration | **187/187 artifact checks pass**; same topology/hardware quantities; changed geometry, schedules, annotations and narrative |
| Regression/negative suite | **38 tests pass; 0 failures/errors/skips**; 25 deliberate faults are correctly rejected |
| PDF QA | Both 18-page manuals and each 3-page A4/Letter template rendered; no automated clipping or text-span overlaps |
| Visual inspection | All 36 manual pages reviewed; final page 17 rechecked after correction. All paper-template pages reviewed; wider templates are byte-identical to original-width templates |
| Preservation | All 68 P1 package files and the original complete ZIP match the pre-change manifest; no tracked P1 changes |

Machine-readable results: `../reports/tests_final.json`, each example's
`validation.json`, `provenance.json`, `qa/summary.json`, and
`../reports/visual_review.json`. Full final test output is in
`../reports/tests_final.txt`. Review was performed by the Codex assistant; human
commercial proofread, printer/ruler verification and physical tests remain undone.

## What the width regression changes

| Dimension | 900 mm frame | 1000 mm frame |
|---|---:|---:|
| Clear opening | 810 mm | 910 mm |
| Finished shelf length | 809 mm | 909 mm |
| Cap width | 920 mm | 1020 mm |
| Maximum width across side Xs | 936 mm | 1036 mm |
| Right shelf screw X station | 840 mm | 940 mm |
| Top-angle X stations | 247.5 / 652.5 mm | 272.5 / 727.5 mm |
| Rear-strap hole pitch | 1814.12 mm | 1863.34 mm |

The frame depth, shelf count, side-bay geometry, hardware counts and brace patterns
stay unchanged for this width-only test. The cut/CAD regression at 900 mm matches
P1 stock sizes, component bounds and solid-volume multiset. The 1:1 patterns are
identical across widths because the side frames do not change.

**Explicit development layout decision:** top angles are now at quarter points of
the clear opening. At 900 mm this is 247.5/652.5 rather than P1's literal 250/650 mm.
No P1 file was changed; these purchased angles were not modeled P1 solids. The new
layout is a stated development assumption requiring actual fitting/access review,
not a capacity claim or proof that wider shelves are suitable for service.

The internal assumed-E UDL example increases from approximately **1.558 mm** to
**2.248 mm** instantaneous deflection, and **1.231 MPa** to **1.407 MPa** bending
stress. E=6000 MPa and material density are assumptions; the 20 kg contents scenario
is not a recommended load. No allowable stress/deflection or safe-working-load
acceptance criterion is used. A wider product requires renewed structural and
prototype review even when digital geometry passes.

## Reusable versus product-specific

Reusable candidates: explicit records and exact unit conversion; CAD primitives
and exports; JSON/CSV writers; deterministic stock allocation; z-buffer rendering;
flow-based branded PDF layout; DXF/SVG and overlapping paper-template generation;
artifact comparison, paper-scale and page QA mechanisms; reports and fault-injection
workflow. Geometry, joinery decisions, material/hardware recipes, analytic oracles,
camera/label selections, drill rules and assembly prose remain Alderline-specific
under `woodplan/products/`. The project Skill and procedure document how to add a
new reviewed adapter; unknown product types fail closed.

**Not fully generalized:** no second structurally different product was created
or tested. The current shared contracts are exercised only through Alderline.
Stock packing assumes one sheet thickness and unrotated grain per batch; it is
feasible, not optimal, and does not prescribe a safe machine-cut sequence.

## Detected failures and corrections

- Initial 31-test run: one negative fixture had a variable-shadowing error; one
  deterministic-PDF test failed because absolute image paths affected ReportLab
  image object names. The fixture was corrected and embedding changed to pixel
  content. The byte-for-byte repeatability assertion was retained and now passes.
  The original full failed log is preserved in `../reports/history/first_test_run_31.txt`.
- Initial packing was feasible but used a nearly empty second sheet; deterministic
  free-rectangle packing now fits all plywood on one checked sheet at both widths.
- Visual review found header contrast, an insufficient joint close-up, hidden
  cleats/front-facing rear-brace illustrations and crossing callouts. Headers now
  use visible white text, the lap is cropped from actual CAD, appropriate inside/
  rear cameras are used, and labels are ordered by projected position. An occluded
  strap in the exploded sheet is explicitly labeled hidden with a dashed leader.
- Template viewport height was corrected to stay below the header, including
  future multi-row patterns. Exact calibration lengths and tile coverage pass.
- New PDF reference validation initially treated declared lumber-family/sheet
  blank IDs as nonexistent assembly parts. It now recognizes these separate
  namespaces from the exported layouts. The deliberate unknown `A-Z99` PDF test
  still fails the intended check, and all actual component IDs remain required.
- One scratch validation read raced with archiving an intermediate directory and
  encountered a missing file. It supplied no readiness evidence; final builds and
  tests were sequenced after their inputs existed and completed successfully.

Intermediate digital checks and issues above are resolved; all final checks pass.
Physical/material/manufacturer uncertainties below are not resolved by these fixes.

## Outstanding release work

No physical prototype, material verification, joint/load/creep/racking/impact/tip
or installed-restraint test has been performed. Actual plywood/timber properties,
adhesive practice, pilot sizes, purchased bracket/restraint products, head geometry
and wall construction remain to be selected and tested. CAD represents nominal
dowel embeds; the extra blind-drill clearance is a fabrication instruction. Exact
purchased hardware and pilot holes are not detailed solids. No fastener capacities,
structural certification or safe working load have been inferred.

Next validation of reuse should be a structurally different product with its own
explicit brief, geometry/joinery adapter, independent oracles, negative tests,
illustrated manual, page review and physical commercial-release process.
