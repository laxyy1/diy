# Future Codex procedure / one new woodworking product

1. **Protect prior work.** Inspect instructions and Git status. Work in the existing
   isolated checkout on a new development branch, not a new worktree. Record hashes
   of any prior release that must remain immutable. Never overwrite an output run.
2. **Read images and the brief.** Record visible members, count, arrangement and
   apparent joints separately from inferred hidden structure. Use reference images
   only as reference; do not reuse publication text or artwork.
3. **Resolve essential unknowns.** Create an explicit design brief with proposed
   overall/usable dimensions, actual stock, joinery, intended use and assumptions.
   Ask for confirmation where an essential structural or dimensional choice cannot
   be established reliably. Do not infer hidden measurements from photographs or
   invent capacities. Continue independent research and tool preparation meanwhile.
4. **Choose a product model.** For a new structure create a separate adapter under
   `woodplan/products/`; no universal bookshelf-to-table conversion. Use the shared
   `Design`/`Part` records and metric units. Document unsupported parameter ranges
   and constraints that require a fresh engineering decision.
5. **Build the original parametric design.** Define actual CAD members and joints;
   generate unique IDs, a complete catalog, nominal drill/screw sites, connections
   and ordered steps. Derive quantities from geometry/connection records. Author
   independent ID, size, bbox, volume, hardware and fit oracles.
6. **Generate new outputs.** Register the adapter explicitly in `run.py`; use a new
   config and output path. Generate the assembly and each component, schedules,
   purchasing layouts, orthographic/isometric/exploded and assembly views, enlarged
   joint details and full-size patterns when relevant.
7. **Validate before calling it ready.** Run applicable artifact, CAD, unit, kerf,
   reference, hardware and paper-scale checks. Do not disable failing tests to ship.
   Record assumptions separately. Add deliberate wrong quantities, missing parts,
   dimension/unit mistakes, interferences and template faults. Each must trigger
   the intended named failure, not merely a generic exception.
8. **Generate the English manual.** Preserve cream, forest green, natural wood and
   refined serif/sans typography. Supply buildable sequential instructions with
   IDs and illustrated joints; display metric dimensions plus rounded inches.
   Let page count follow content. Keep internal validation/engineering calculations
   separate while retaining required safety and installation instructions.
9. **Inspect every exported page.** Rasterize manual and templates. Inspect all
   pages at readable resolution and the actual-scale template seams/calibration.
   Check tables, labels, units, callout endpoints, contrast, crop, overflow, sequence
   and complex joints. Fix findings and rerun affected checks; record review only
   for the final hash. Automated QA is not human inspection.
10. **Close the technical package.** Include CAD/source/configuration, CSVs,
    purchasing layouts, drawing/pattern exports, internal validation, engineering
    assumptions, commercial checklist, dependency pins and provenance. State all
    failures, not-run checks and unavailable manufacturer/material evidence.
11. **Release deliberately.** Commission independent prototype and qualified
    physical testing before a commercial claim. Commit on the development branch.
    Push only within the user's authorization; verify the remote commit and actual
    files before giving GitHub download links. Never claim a fully generalized
    workflow until a second structurally different product has passed this process.

The current examples establish regression only for one bookshelf at two widths.
Neither is a physical product certification or evidence for another structure.
