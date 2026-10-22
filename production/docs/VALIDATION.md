# Validation contract / what passes mean

The authoritative results are each example's `validation.json` and
`INTERNAL_VALIDATION.md`, plus the final test report. Check counts may grow; they
are not acceptance targets. Every check has an ID, pass/fail, observation, category
and scope. Failure produces a nonzero runner/test exit status.

| Check family | Verifies | Does not verify |
|---|---|---|
| Catalog and IDs | Expected component set, unique IDs, per-group counts and numeric stock dimensions in JSON/CSV | Species, grade or usable defect-free material |
| CAD read-back | Each delivered STEP has one valid positive solid; independent bbox and analytic volume; assembly/component agreement; >0.01 mm³ clashes | Strength, every possible machining tolerance, finish quality |
| Dowel geometry | Unique expected site IDs, positions/radii/embeds and empty nominal mating-bore paths | Real bit runout, adhesive bond strength or stock swelling |
| Screws | Nominal tip containment, inter-axis clearance, timber receiving/attached shank paths, angle-embed arithmetic | Manufacturer capacities, head/countersink volume, pilot size, wall/fitting geometry |
| Hardware and steps | Connection-site counts vs independent topology vs CSV vs visible PDF rows; references and exact once-only connection allocation | Whether actual selected fittings are suitable or available |
| Purchasing/layouts | Every piece allocated once; section/length fit; end trims/kerfs; sheet bounds and gaps; waste arithmetic; purchase count agreement | Optimal nesting, defect allowance adequacy or safe saw sequence |
| PDF content | Unique visible cut/hardware rows, canonical dimension facts, mm/25.4 conversion and rounding, internal report separation | Every prose statement's interpretation or practical buildability |
| PDF visual automation | Renderable pages, bounds and text-span collisions | Contrast, material identification, leader usefulness or complete human review |
| Templates | Closed DXF mm profiles, analytic areas, exact paper bounds, actual vector calibration lengths, tile starts/overlaps/coverage | Printer driver scaling, paper stretch, physical jig safety or fit |
| Regression/provenance | P1 hashes, old CAD/cut sizes, changed-width outputs, source hashes, deterministic data and PDF output | Generality beyond Alderline or structural safety |

Metric is canonical; inches are display equivalents rounded to 0.001 in. The unit
check permits only the corresponding 0.0005 in display error, not arbitrary unit
conversion tolerance. STEP tolerances are numerical limits for these nominal
parts, not fabrication tolerances or acceptance standards.

## Negative tests

The suite copies a verified example into a disposable temporary directory and
deliberately corrupts hardware CSV, connection count, component IDs/counts, cut
dimensions, units, collapsed/nonfinite parameters, assembly references, purchase
quantities, lumber kerf, plywood placement, screw length, DXF units, tile scale or
coverage, visible PDF hardware/conversions, an actual STEP position and a dowel
site. A targeted failure ID must be present. The suite also preserves positive
regressions; a validator that always rejects is not acceptable.

The CAD clash test translates a post into shelves and must fail both geometry and
interference checks. PDF tests edit a copied actual PDF, rather than only mutating
a table data structure. Template scale checks inspect actual vector bar lengths
in the PDF as well as exported metadata. No output is altered to hide a failure.

## Engineering assumptions are separate

The assumed-E simply-supported uniform-load shelf calculation is internal only.
It shows a width-dependent scenario, not an allowed load. It excludes creep,
orthotropy, defects, connection slip/capacities, racking, impact and tipping.
There is no allowable-stress or safe-working-load acceptance check. Wider shelves
require renewed engineering/prototype review even when geometric checks pass.
