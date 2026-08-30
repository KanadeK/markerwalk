# MarkerWalk

**Offline photo-coverage QA and revisit routing for cemetery survey volunteers.**

MarkerWalk turns a reviewed JSON survey manifest plus a local photo folder into evidence you can
inspect before uploading anywhere:

- exact missing marker/view combinations;
- referenced files that are absent and image files that are not referenced;
- previous unsuccessful field attempts kept beside the next checklist;
- a deterministic revisit order, route CSV, printable Markdown sheet, SVG map, and script-free
  HTML report.

It performs real filesystem reconciliation and route solving. For 14 or fewer incomplete markers,
the route is proven shortest in the declared Euclidean coordinate grid; larger visits use a
deterministic nearest-neighbour + 2-opt heuristic and say so in every report.

MarkerWalk does **not** recognize inscriptions, infer identities, upload photos, replace cemetery
records, or promise that a geometric route is safe or accessible. Confirm terrain, permissions,
opening hours, and field conditions yourself.

## Why this exists

GPS photo platforms are useful for capture and publication, but local project teams still need a
reviewable handoff between a planned survey, the actual files on disk, unsuccessful attempts, and a
return visit. MarkerWalk keeps that QA step offline and manifest-authoritative: no image is silently
assigned to a marker and no missing view is guessed away.

See [the research and novelty boundary](docs/research-and-novelty.md) for the dated comparison with
adjacent products and the limits of the uniqueness claim.

## Quick start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```console
git clone https://github.com/KanadeK/markerwalk.git
cd markerwalk
uv sync --locked

# Incomplete example: exit 1 is expected because it found work to do.
uv run markerwalk audit examples/lantern-hill/survey.json --json build/audit.json

# Build the offline revisit packet.
uv run markerwalk plan examples/lantern-hill/survey.json --output build/lantern-visit
```

Open `build/lantern-visit/report.html` locally. No server is required.

## Input in one minute

```json
{
  "schema_version": 1,
  "survey": {
    "name": "Lantern Hill",
    "photo_root": "photos",
    "views": ["front", "inscription", "context"],
    "start": {"x": 0, "y": 0},
    "end": {"x": 0, "y": 0}
  },
  "markers": [
    {
      "id": "A-01",
      "label": "North row, marker 1",
      "x": 12.5,
      "y": 4,
      "required_views": ["front", "inscription", "context"],
      "photos": [
        {"path": "photos/A-01-front.jpg", "views": ["front", "inscription"]}
      ],
      "attempts": [
        {"date": "2026-08-12", "outcome": "weather", "note": "glare"}
      ]
    }
  ]
}
```

Paths are relative to the manifest and must remain inside that directory after resolution. See
[the complete input contract](docs/input-format.md).

## Commands and exit codes

| Command | Result |
|---|---|
| `markerwalk audit MANIFEST [--json FILE]` | Reconcile coverage and local image files |
| `markerwalk plan MANIFEST --output DIRECTORY` | Create JSON, CSV, Markdown, SVG, and HTML |
| `markerwalk --version` | Print the installed version |

- `0`: valid input and command success. A valid `plan` returns 0 after creating a packet.
- `1`: `audit` found coverage gaps, missing referenced files, a missing photo root, or unreferenced
  images. This is an actionable result, not a crash.
- `2`: invalid JSON/schema/path/I/O. Requested output is not created.

The plan output directory must not already exist. This prevents an old and new field packet from
being silently mixed.

## Acceptance

```console
uv sync --extra dev --locked
uv run python scripts/check.py
```

The full gate runs formatting, lint, strict typing, branch coverage, all three example outcomes,
package build, dependency audit, an isolated wheel install, the installed console command, and a
deterministic example bundle. See [troubleshooting](docs/troubleshooting.md) for exact repair paths.

## Design boundaries

- The manifest is the only identity authority. File names and image contents are never guessed.
- Declared view coverage counts only when the referenced file exists.
- An attempt documents field history but never satisfies a required photo view.
- Distances use the manifest's local metre grid and ignore obstacles.
- Exact routing is capped at 14 incomplete markers to bound exponential work.
- Outputs are deterministic for identical input bytes and filesystem evidence.

Architecture and rejected alternatives are documented in
[ADR-0001](docs/decisions/0001-manifest-authority-and-standard-library.md).

## 中文说明

MarkerWalk 是一个完全离线的墓园碑石摄影巡查工具。它以人工确认的 JSON 清单为唯一真源，
核对本地照片是否真实存在、每块碑的必拍角度是否齐全、是否有未归档照片，并为缺拍碑石生成
回访顺序、CSV、现场勾选表、SVG 路线图和单文件 HTML 报告。

它不会识别碑文、猜测人物身份、连接或上传到第三方平台，也不会把平面直线距离说成安全路线。
`audit` 返回 1 表示发现了需要处理的缺口；返回 2 才表示输入无效。完整验收命令是：

```console
uv sync --extra dev --locked
uv run python scripts/check.py
```

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development loop and [SECURITY.md](SECURITY.md) for
private vulnerability reporting. MarkerWalk is available under the [MIT License](LICENSE).
