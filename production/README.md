# DIYWOODPLANNER production workflow

Codex-assisted woodworking plan production: **no website, desktop app, API or GUI**.
This development system has been tested on Alderline X4 at frame widths of 900 and
1000 mm. It is **not fully generalized**: no second structurally different product
has been modeled or validated. Digital checks do not prove structural safety.

The original P1 package under `../deliverables/` is immutable. New source lives here;
examples and reports are separate from P1. The development branch is
`development/woodworking-plan-production`.

## Run in Codex

Use the existing isolated checkout; no Git worktree is needed. Python 3.12 and the
pinned dependencies in `requirements.txt` were available in the task environment.
No service startup, credentials, background server or external API is required for
production. On a new machine, use a virtual environment and install those pins with
normal TLS/checksum verification.

From the repository root, always choose a **new** output path:

```sh
python production/run.py --config production/configs/alderline_900.json --out /tmp/woodplan-run-900
python production/run.py --config production/configs/alderline_1000.json --out /tmp/woodplan-run-1000
python -m unittest discover -s production/tests -v
```

The test suite uses the two committed example builds as fixtures, verifies their
source provenance and P1 regression, and injects faults into temporary copies. It
never modifies the fixtures or P1. To adopt a new example revision, build into a new
directory, review it and its report, then deliberately update the example fixtures
on a development branch. The runner refuses existing output directories and all
paths under `deliverables/`; a failure does not authorize deleting old artifacts.

## Find the outputs

- `examples/alderline_900/manual.pdf`: customer manual for original dimensions.
- `examples/alderline_1000/manual.pdf`: wider regression example, **not approved for
  physical use without renewed engineering/prototype review**.
- Each example has all 47 individual STEP components and an assembly; cut/hardware
  CSVs; connections and step references; plywood/lumber layouts; shaded stage views
  and orthographic/isometric SVG drawings; exact-unit DXF/SVG brace patterns;
  separate `template_A4.pdf` and `template_Letter.pdf`; and every rendered PDF page.
- `INTERNAL_VALIDATION.md` and `validation.json` are internal digital checks.
  `engineering_assumptions.json` contains an assumed material/UDL illustration,
  separately from the customer manual. It provides no safe working load.
- `provenance.json` records parameter/source hashes and dependency versions.
- `docs/TECHNICAL_REPORT.md` records actual final results and remaining limitations.

## Production responsibilities

Read [the audit](docs/AUDIT.md), [architecture](docs/ARCHITECTURE.md),
[new-product procedure](docs/NEW_PRODUCT_WORKFLOW.md),
[validation contract](docs/VALIDATION.md), and
[commercial release gates](docs/COMMERCIAL_RELEASE.md).

The project skill is at
`../.agents/skills/woodworking-plan-production/SKILL.md`. In Codex clients that
discover project `.agents/skills`, invoke `$woodworking-plan-production`; otherwise
read that file explicitly. It is a repository skill file, not an installed cloud
plugin. The script fails closed for unknown `product_type` values. New structures
require a new reviewed geometry/instruction/check adapter.
