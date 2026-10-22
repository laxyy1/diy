# Architecture / reusable tools and product adapters

The production environment is Codex plus Python files. There is no application
state, service, API, database or interface to deploy.

| Stage | Shared tools | Product-specific responsibility |
|---|---|---|
| A. Image/spec analysis | `NEW_PRODUCT_WORKFLOW.md`, design brief/review records | Identify visible structure and unknowns; establish original dimensions and joinery |
| B. Parametric CAD | `cad.py`: primitives; `common.py`: records/units | `products/alderline_geometry.py`: actual assembly, bores, laps and strap geometry |
| C. Schedules/materials | `export.py`, `stock.py`: STEP/CSV/JSON writers, blank allocation, unrotated free-rectangle packing | `alderline.py`: catalog/material semantics, stock families, angled blank lengths, connection graph |
| D. Computational checks | `validate.py`, `template_checks.py`: exported-data, CAD and print-scale mechanisms | `alderline_checks.py`: independent IDs/counts, stock sizes, bbox/volume equations, dowel sites, joinery rules |
| E. Drawings | `render.py`: projection/depth buffer; `templates.py`: DXF/SVG/paper tiling | `alderline_drawings.py`: view cameras, explode transforms, dimensions, lap crop/profile |
| F. Assembly | Shared records and ID/reference checking | `alderline.py`: ordered connection allocation and actual construction narrative |
| G. Branded PDF | `pdf.py`: fonts, colors, flow layout, repeating table headers, legends and stock figures | `alderline_manual.py`: part-specific sections and joint diagrams |
| H. Final QA | `qa_pdf`, template scale checks and fault-injection mechanisms | Expert visual/technical review of every page and physical prototype evidence |
| I. Commercial release | `COMMERCIAL_RELEASE.md` gates | Product-specific materials, hardware, markets, evidence and reviewer sign-off |

`run.py` explicitly registers only `alderline_x4`. A new furniture structure needs
a new adapter and independent tests; do not pass it through Alderline rules. The
shared layer remains a candidate reusable library, not a proven universal system.

## Records and one source of truth

Canonical input is a JSON configuration with `units: mm`. `derive` calculates
opening, shelf/cap dimensions, brace geometry, angle locations and clearances.
`Part` carries a unique component ID, group, CAD solid and non-dimensional
placement metadata. The catalog obtains quantities from actual components.
Connections name component IDs, hardware counts and exactly one assembly step.
Hardware totals sum actual connection-site records. Independent topology recipes
provide a second path to expected quantities, rather than simply accepting the
generated values.

Exports are disposable evidence in a new directory; they are not input sources.
Individual CAD bounds/volumes are checked against independent product equations.
The annotated front/side images use the same CAD projection transform as their
dimension endpoints. Part callouts project actual CAD bbox centres or explicit
product-selected close-up points. Layout coordinates are typography/illustration
choices; they do not define furniture dimensions.

## Limits of the current shared contracts

- Material schedule groups use explicit adapter families; the current sheet packer
  assumes one cabinet-plywood thickness and an unrotated grain direction per batch.
- Feasible free-rectangle packing is deterministic, not a globally optimal cutting
  solution or a certified safe saw sequence. Kerf, end trims and residual material
  are checked; defects and ripping waste are not estimated.
- Shared geometric mechanisms assume exact nominal CAD and finite straight screw
  shank paths. Pilot diameters, countersink heads, purchased angle holes and wall
  restraint hardware need manufacturer-specific data and physical review.
- PDF flow does not impose a 15-page limit. Visual checks still require a reviewer;
  bounds checks alone cannot establish legibility, contrast or useful drawings.
- Product oracles deliberately duplicate physical equations, not generated output
  values. Every new joinery type needs appropriate new oracles and negative tests.
