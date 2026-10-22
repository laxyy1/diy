---
name: woodworking-plan-production
description: Produce and validate original DIYWOODPLANNER woodworking plan packages in Codex using product-specific parametric CAD, shared production scripts and branded English documentation.
---

# Woodworking plan production

Use Codex and the existing isolated checkout; do not build an application, API,
website or UI, or create a worktree unless requested. Preserve every prior release
and output. Inspect Git state and instructions before changes.

Read `production/README.md`, `production/docs/NEW_PRODUCT_WORKFLOW.md` and
`production/docs/ARCHITECTURE.md` from the repository root. For checks and limits,
read `production/docs/VALIDATION.md` and `COMMERCIAL_RELEASE.md`.

1. Analyze reference images, separating visible structure from unknown hidden
   dimensions/joints. Establish an explicit original brief; request confirmation
   when an essential unknown prevents a defensible design. Never invent capacities.
2. Use a product-specific geometry/instruction/check adapter. Only Alderline X4 is
   implemented; do not pretend the same model represents all furniture. Keep mm
   canonical; derive all dimensions/quantities/IDs and rounded inch displays.
3. Generate into a new path with
   `python production/run.py --config <config.json> --out <new-directory>`.
   It must produce CAD, complete schedules/layouts, drawings, illustrated assembly,
   customer PDF, paper-specific calibrated templates and separate internal reports.
4. Run `python -m unittest discover -s production/tests -v` for current regression
   fixtures; add independent positive and targeted deliberate-error tests for new
   structures. Diagnose failures, correct their causes and rerun affected checks.
5. Preserve cream/forest-green/wood colors, serif/sans typography, clear technical
   figures, readable tables and detailed joints. Let pagination follow complexity.
6. Render and inspect every final manual/template page at readable scale. Fix
   clipping, contrast, labels, leader endpoints, units and sequence errors. Record
   visual approval against final PDF hashes, separately from automated checks.
7. Report exact passes/failures, assumptions and physical/manufacturer evidence
   still missing. Never infer a safe working load or structural certification from
   mathematical checks. Keep commercial release gates explicit.

Save work on an appropriate development branch. Publish only as authorized and
verify remote files before claiming delivery. No fully generalized production
claim is permitted until a second structurally different product is tested.
