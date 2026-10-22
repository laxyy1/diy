# DIYWOODPLANNER — Alderline X4 / P1

Original four-shelf X-frame bookshelf plan. **Product artifacts, no app or UI.**

Start with `output/DIYWOODPLANNER_Alderline_X4.pdf` (15 pages). All dimensions are in millimetres. The reference images were used only to identify the visible structural idea; their artwork, wording, dimensions and page layout were not reused.

## Deliverables

- `output/cad/Alderline_X4.step`: named, colored assembly, 47 solids. Exact timber, plywood and steel strap solids include mating dowel bores and complementary half laps. Dowels/screws, their pilot holes, purchased top angles, wall restraints and finishing are not detailed CAD hardware.
- `output/cad/part_*.step`: representative wood components, including both half-lap hands; coordinates remain in the assembly reference system.
- `output/drawings/`: generated isometric/front/side/rear SVGs, dimensioned elevations, post boring map, exploded assembly, brace fabrication sheet, 1:1 brace profile/lap DXF and SVG, plywood nesting map, and shaded assembly-stage illustrations.
- `output/cut_list.csv`, `output/hardware.csv`: installed quantities and finished dimensions; purchasing allowance appears in the PDF.
- `output/VALIDATION_REPORT.md`, `output/validation.json`: independent geometry and arithmetic checks, engineering assumptions and unresolved release gates.
- `output/qa/`: rendered PDF pages, contact sheet, layout bounds and PDF inspection results.
- `source/parameters.json`: canonical geometry input. `derived_dimensions.json` and cut lists are generated outputs, not editable inputs.

## Reproduce

Use the existing checkout/workspace. Each cloud task is already isolated; do not create a Git worktree unless explicitly requested. No services, keys, external APIs or runtime startup are required. All dependencies were already installed in the task machine.

From this directory:

```sh
export XDG_CACHE_HOME=/tmp/woodplanner-cache
python source/model.py
python source/export_patterns.py
python source/validate.py
python source/render.py
python source/build_manual.py
python source/qa_pdf.py
```

`requirements.txt` records the versions used here. Install into an isolated virtual environment if reproducing elsewhere. CAD is millimetres and actual stock sizes control. The model, schedules, shaded figures and fabrication pattern derive from the canonical input. The English narrative and some presentation annotations describe the P1 issue; the manual builder has a parameter SHA-256 guard so changed parameters cannot silently issue stale instructions. A dimensional variant requires revising/reviewing the narrative and annotations, rechecking physical joinery and updating that release guard before issuing a new manual. Do not change the guard alone.

The assembly's origin is at the left-front frame foot: X right, Y rear, Z up. Left/right identifiers are viewed from the front. Maximum X width is 936 (outer X slats), top width 920, frame width 900; maximum depth 370; height 1800, excluding pads/restraint fittings. The overall side-frame rectangle is 350 × 1782.

The DXF uses mm; the SVG has explicit physical mm dimensions. Print at 100%, check the 100 mm calibration bar, and validate against a scrap bay before using a pattern. A pattern is not a guarded router fixture. Drawings embedded in the PDF are not full size.

## Review status and limitations

The current issue is a **complete prototype plan, not a tested commercial release**. Computational checks do not prove structural safety. The nominal 20 kg contents example is an engineering scenario, not a working-load recommendation. Wood and plywood properties are assumptions pending supplier verification. Hardware manufacturers/products and wall structure remain to be selected and checked. No fastener capacity has been invented.

Before sale: commission an independent full-size build; verify materials and joints; conduct qualified load, creep, racking, impact and tip/anchor tests with a documented protocol; verify intended-market product requirements; proof the technical text, drawings and printing scale. See PDF page 14 and the validation report for specific release gates. No commercial load rating or certification is provided.

## Visual QA

Every exported PDF page is rasterized for inspection. The scripted check tests page bounds, text overlaps, expected page count, nonempty pages and DXF units/profile count. Human visual review examines each rendered page, not only the contact sheet. The saved reports distinguish these document checks from CAD and physical tests.
