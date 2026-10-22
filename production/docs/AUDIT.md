# P1 audit and preservation

P1 consists of 68 package files plus the complete ZIP. Every file's path, byte size
and SHA-256 is recorded in `p1_preservation_manifest.json`. `P1_CODE_INVENTORY.json`
records numeric literals and module-level globals by source file and line. Literal
counts include valid typography/layout constants; they are not counts of defects.

| P1 component | Reusable idea | Alderline-specific or hardcoded behavior | Development treatment |
|---|---|---|---|
| `parameters.json` | Metric input/explicit assumptions | One fixed product, mixed geometry and engineering values | Separate two width configs; explicit stock/hardware/design-rule sections |
| `model.py` (185 lines; 161 numeric literals) | CAD primitives, parametric solids, STEP tessellation/export | Global P/D/OUT; 4/8/16 quantities; literal 9 mm laps, 8/6 mm bores, apron centres; geometry and exports coupled | Shared CAD primitives/exporter; product-only geometry takes D argument; actual half thickness, bore dimensions and centres derive from input |
| `render.py` (73; 121 literals) | Orthographic projection, shading and z-buffer | Global mesh; group-specific explode distances/selections; fixed output path | Pure shared renderer with passed mesh/path/offsets; product camera/selection module |
| `export_patterns.py` (65; 55 literals) | Polygon clipping, DXF/SVG units | Specific brace transforms; fixed 35/9 mm data; fixed plywood nesting; no tiled paper output | Shared convex clip/pattern/tile writers; adapter supplies profile; tested A4/Letter scale/coverage |
| `build_manual.py` (336; 763 literals) | Cream/green/wood palette, serif/sans identity | Fixed page coordinates/count, global canvas, P1 SHA guard; repeated 900/810/809 values and quantities; internal checks in customer PDF | Flow-based reusable document engine; product-specific parameterized prose, dimensions, IDs and diagrams; separate internal reports |
| `validate.py` (115; 187 literals) | STEP read-back, interference and lap math | Hardcoded bounds/stock/holes; several checks compare constants with constants; no CSV hardware or visible PDF count checks; no fault-injection suite | Per-component CAD/stock/graph/export/PDF checks with independent product oracles and named failures; explicit negative tests |
| `qa_pdf.py` (42; 41 literals) | Page rasterization, bounds/overlap detection | Exactly 15 pages, fixed sheet indexes and contact dimensions | Page count independent; all generated pages rasterized; text QA separate from visual review |
| Cut list/hardware/purchasing | Legible original schedules | Hardware literal tuple; purchase text not a checked data artifact | Cut counts from actual components; hardware from connection sites; independent topology recipe; purchasing/layout files cross-checked |
| Original STEP, 1:1 pattern, 15-page PDF and reports | Regression evidence | Original dimensions, prototype status; no physical performance evidence | Preserved unchanged; original cut sizes, 47 CAD solid volumes/bounds and checksums are regression fixtures |

## Confirmed risks in P1

The nominal dowel-count check is `10*2*2 == 40`, with no link to hardware.csv. A
dimension variation could leave labels, screw coordinates and CSV quantities
stale. The guard appropriately refused unreviewed variants but did not create a
reusable parameterized manual. Fixed page count and fixed SVG page indexes would
reject a valid longer manual. No deliberate-error tests demonstrated sensitivity.
The engineering calculation used assumed E and an illustrative load; those are
not structural acceptance criteria and are now kept in the internal report only.

## Changes and scope

No P1 source, PDF, ZIP, CAD, report, drawing or metadata file was changed. Source
and generated development outputs are new. The nominal P1 CAD shape (including
nominal embed bores) is retained; the documented extra blind-drilling depth is
still a fabrication instruction, not an undocumented geometry change. Purchasing
allocation was improved after a feasible but wasteful first layout used a second
sheet. Test results and physical evidence must remain distinct.
