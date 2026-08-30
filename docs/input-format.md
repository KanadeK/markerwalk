# MarkerWalk input format

MarkerWalk v0.1 accepts one UTF-8 JSON object with `schema_version: 1`. Unknown fields are rejected
so misspellings cannot silently change a survey.

## Survey fields

| Field | Required | Meaning |
|---|---:|---|
| `name` | yes | Human-readable project name, 1–200 characters |
| `photo_root` | no | Relative directory scanned for unreferenced images; defaults to `.` |
| `views` | yes | Unique allowed view names used by every marker |
| `start` | yes | Route start `{x, y}` in the survey's local metre grid |
| `end` | no | Route end; omitted means the route may finish at its last marker |
| `bounds` | no | Inclusive `{min_x, min_y, max_x, max_y}` validation rectangle |

Coordinates must be finite numbers. Bounds validate declared coordinates; they do not model fences,
paths, slopes, steps, vegetation, traffic, opening hours, or permission.

## Marker fields

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Unique stable marker ID |
| `label` | yes | Human-readable field label |
| `x`, `y` | yes | Local metre-grid coordinate |
| `required_views` | yes | Non-empty subset of `survey.views` |
| `photos` | yes | Array of declared photo objects; may be empty |
| `attempts` | no | Prior field attempts that remain visible but never satisfy coverage |

A photo object contains a relative `path` and a non-empty `views` array. One path cannot be assigned
to two markers. A photo contributes its declared views only when the path resolves to an existing
regular file.

Attempts contain an ISO date, one outcome from `not_found`, `obstructed`, `weather`, `access`, or
`other`, and an optional note.

## Path and discovery rules

- Absolute paths and `..` escapes are rejected.
- Resolved paths, including existing symlink targets, must remain under the manifest directory.
- Discovery under `photo_root` includes `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, and `.webp`,
  case-insensitively.
- A discovered image not referenced by any marker is reported for reconciliation.
- Marker identity and view coverage are never inferred from names, EXIF, pixels, or third parties.

## Output compatibility

The input schema and output JSON both carry `schema_version: 1`. A future incompatible contract
will use a new schema version and reject old data explicitly rather than guessing.

