# Spec: MarkerWalk v0.1.0

## Objective

MarkerWalk is an offline command-line tool for cemetery and local-history volunteers who
photograph marker surveys from an explicit manifest. It answers four reviewable questions:

1. Which marker/view combinations are already covered by referenced local files?
2. Which referenced files are missing, duplicated across markers, or outside the survey folder?
3. Which unreferenced image files need reconciliation before upload?
4. In what deterministic order should incomplete markers be revisited?

The tool does not replace a cemetery records system or a GPS photo-sharing service. It does not
identify people, interpret inscriptions, upload photos, or promise a safe walking route.

## Tech Stack

- Python 3.11+ and the standard library at runtime.
- Hatchling for wheel/sdist builds.
- Pytest, Ruff, mypy, coverage, build, and pip-audit as release-only tooling.
- JSON input; stable JSON, CSV, Markdown, SVG, and script-free HTML output.

## Commands

```text
uv sync --extra dev --locked
uv run markerwalk audit examples/lantern-hill/survey.json --json build/audit.json
uv run markerwalk plan examples/lantern-hill/survey.json --output build/visit
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv build
uv run python scripts/check.py
```

Exit codes are part of the public contract:

- `0`: valid input and the command's success condition is met.
- `1`: `audit` found actionable coverage gaps or unreferenced images.
- `2`: invalid JSON, schema, path, or I/O input; no requested output is written.

`plan` returns `0` after producing a valid revisit plan, even though the plan exists because
coverage is incomplete.

## Input Contract

The manifest is a UTF-8 JSON object with:

- `schema_version`: exactly `1`.
- `survey`: `name`, optional `photo_root`, required `views`, `start`, optional `end`, and optional
  rectangular `bounds`. Coordinates are finite numbers in a project-defined metre grid.
- `markers`: unique `id`, human-readable `label`, `x`, `y`, non-empty `required_views`, `photos`,
  and optional `attempts`.
- `photos`: relative `path` plus one or more declared `views` that the file covers.
- `attempts`: ISO date, outcome (`not_found`, `obstructed`, `weather`, `access`, or `other`), and
  optional note. Attempts remain visible but do not satisfy photo coverage.

Paths are resolved relative to the manifest directory. Absolute paths, parent traversal, and
resolved paths outside that directory are rejected. A referenced path may belong to only one
marker. Image discovery under `photo_root` is limited to `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`,
and `.webp` files.

## Analysis and Routing

- Coverage is the set union of declared views on existing referenced files.
- A marker is incomplete when any required view is not covered.
- Unreferenced images under `photo_root` are actionable reconciliation findings.
- The revisit route contains incomplete markers only, starting at `survey.start` and ending at
  `survey.end` when supplied.
- For at most 14 incomplete markers, Held-Karp dynamic programming returns a proven shortest
  Euclidean route. Larger visits use deterministic nearest-neighbour plus 2-opt and explicitly
  report `optimal: false`.
- Ties are resolved by marker ID so identical inputs produce byte-stable outputs.

## Project Structure

```text
src/markerwalk/       Core models, validation, analysis, routing, rendering, CLI
tests/                Unit and CLI integration tests
examples/             Synthetic complete, incomplete, and invalid surveys
docs/                 Format, architecture, troubleshooting, and release notes
scripts/check.py      One-command local release gate
.github/workflows/    Cross-platform CI and tag-driven release automation
tasks/                Implementation plan and completion checklist
```

## Code Style

Prefer typed immutable records and explicit errors. Example:

```python
@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

def distance(left: Point, right: Point) -> float:
    return math.hypot(left.x - right.x, left.y - right.y)
```

Public JSON keys use `snake_case`. Output ordering is deliberate and deterministic. External
input is validated once at the loader boundary; internal functions trust typed models.

## Testing Strategy

- Unit tests cover schema/path validation, coverage calculation, deterministic route choice,
  exact optimality on small cases, heuristic labelling, and escaping.
- Integration tests run the real CLI on temporary surveys, assert exit codes, artifact sets,
  invalid-input atomicity, and deterministic bytes.
- Coverage must remain at or above 90% branch coverage. No tests may be skipped.
- The release gate additionally runs formatting, lint, strict typing, examples, package build,
  isolated wheel installation, and installed console-entrypoint acceptance.

## Boundaries

- Always: validate external JSON and paths, escape generated markup, write via a temporary
  sibling before replacing a requested file/directory, preserve deterministic ordering.
- Ask first: add runtime dependencies, change the schema version, add network or upload features.
- Never: infer inscription text, scrape third-party accounts, store credentials, claim route
  safety/accessibility, follow paths outside the survey directory, or silently accept bad input.

## Success Criteria

- The incomplete example returns audit exit `1` with exact missing views and an unreferenced file.
- Planning it creates stable JSON/CSV/Markdown/SVG/HTML artifacts and a valid revisit order.
- The complete example returns audit exit `0`; invalid examples return `2` and create no output.
- The full local gate passes with at least 90% branch coverage and clean artifact installation.
- GitHub CI passes on Linux and Windows, an annotated `v0.1.0` exists, and the public Release
  contains wheel, sdist, and example bundle assets.
- Public repository metadata, contributor history, Release assets, and a fresh installed run are
  verified before the Gmail delivery notice is sent.

## Open Questions

None for v0.1. Coordinate calibration, obstacle-aware routing, EXIF ingestion, mobile capture, and
platform uploads are explicitly deferred rather than implied.

