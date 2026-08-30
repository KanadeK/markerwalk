# Troubleshooting

## `audit` exits 1

This means MarkerWalk ran successfully and found work. Read `summary`, each marker's
`missing_views`/`missing_files`, and `unmatched_files`. Capture or reconcile those items, update the
manifest, and run the same audit again. Exit 0 means the declared contract is complete.

## `audit` or `plan` exits 2

The error on stderr identifies the invalid field or path. Fix the manifest; do not suppress the
check. MarkerWalk intentionally creates no requested output for invalid input.

Common repairs:

- `schema_version must be 1`: keep v0.1 input on schema 1.
- `unknown field`: correct the misspelling or remove the unsupported field.
- `must stay inside the survey directory`: move the photo into the survey folder and use a relative
  path. Do not weaken path containment.
- `assigned to more than one marker`: decide the authoritative marker assignment; duplicate the
  file only if it genuinely represents two distinct retained records.
- `photo_root must resolve to a directory`: create the declared directory or correct the path.
- `output directory already exists`: choose a new output directory or review and archive/remove the
  old generated packet yourself. MarkerWalk will not merge generations.

## `uv` cannot use the default cache or temporary directory on Windows

Keep both inside the repository for that command:

```powershell
New-Item -ItemType Directory -Path .tmp -Force | Out-Null
$markerwalkTemp = (Resolve-Path .tmp).Path
$env:TEMP = $markerwalkTemp
$env:TMP = $markerwalkTemp
uv sync --cache-dir .uv-cache --extra dev --locked
uv run --cache-dir .uv-cache --no-sync python scripts/check.py
```

`.tmp`, `.uv-cache`, and `.venv` are ignored. Do not disable tests or unlock dependencies to work
around a machine-level permission problem.

## A route looks unsafe or inaccessible

Do not follow it. MarkerWalk optimizes straight-line distance between declared points; it has no
terrain, obstacle, access, weather, or mobility model. Adjust the manifest/field plan outside the
tool and use the output only as a coverage checklist.

## Release gate fails

Read the first failing command printed by `scripts/check.py`, repair the root cause, and rerun once.
Do not skip a failing test, lower coverage, disable lint, or publish artifacts from a partial gate.
Build/install failures should be reproduced from the committed lockfile with
`uv sync --extra dev --locked`.

