"""Deterministic JSON, CSV, Markdown, SVG, and HTML renderers."""

from __future__ import annotations

import csv
import html
import io
import json
from collections.abc import Mapping

from markerwalk.audit import AuditReport, MarkerAudit
from markerwalk.model import Point, SurveyProject
from markerwalk.route import RoutePlan


def _json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _distance(value: float) -> float:
    return round(value, 3)


def _marker_payload(item: MarkerAudit) -> dict[str, object]:
    return {
        "attempts": [
            {
                "date": attempt.date.isoformat(),
                "note": attempt.note,
                "outcome": attempt.outcome,
            }
            for attempt in item.marker.attempts
        ],
        "covered_views": list(item.covered_views),
        "label": item.marker.label,
        "marker_id": item.marker.id,
        "missing_files": list(item.missing_files),
        "missing_views": list(item.missing_views),
        "x": item.marker.point.x,
        "y": item.marker.point.y,
    }


def audit_payload(report: AuditReport) -> dict[str, object]:
    return {
        "markers": [_marker_payload(item) for item in report.markers],
        "photo_root_exists": report.photo_root_exists,
        "project": report.project_name,
        "schema_version": 1,
        "summary": {
            "complete": report.complete,
            "incomplete_markers": len(report.incomplete_marker_ids),
            "markers": len(report.markers),
            "unmatched_files": len(report.unmatched_files),
        },
        "unmatched_files": list(report.unmatched_files),
    }


def render_audit_json(report: AuditReport) -> str:
    return _json(audit_payload(report))


def _route_payload(route: RoutePlan) -> dict[str, object]:
    return {
        "optimal": route.optimal,
        "stops": [
            {
                "cumulative_distance": _distance(stop.cumulative_distance),
                "label": stop.marker.label,
                "marker_id": stop.marker.id,
                "segment_distance": _distance(stop.segment_distance),
                "x": stop.marker.point.x,
                "y": stop.marker.point.y,
            }
            for stop in route.stops
        ],
        "strategy": route.strategy,
        "total_distance": _distance(route.total_distance),
        "units": "m",
    }


def render_plan_json(report: AuditReport, route: RoutePlan) -> str:
    payload = audit_payload(report)
    payload["route"] = _route_payload(route)
    return _json(payload)


def render_route_csv(report: AuditReport, route: RoutePlan) -> str:
    audits = {item.marker.id: item for item in report.markers}
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "stop",
            "marker_id",
            "label",
            "x",
            "y",
            "missing_views",
            "missing_files",
            "segment_m",
            "cumulative_m",
        ]
    )
    for index, stop in enumerate(route.stops, start=1):
        audit = audits[stop.marker.id]
        writer.writerow(
            [
                index,
                stop.marker.id,
                stop.marker.label,
                stop.marker.point.x,
                stop.marker.point.y,
                ";".join(audit.missing_views),
                ";".join(audit.missing_files),
                f"{stop.segment_distance:.3f}",
                f"{stop.cumulative_distance:.3f}",
            ]
        )
    return output.getvalue()


def _markdown(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|")


def render_field_sheet(project: SurveyProject, report: AuditReport, route: RoutePlan) -> str:
    audits = {item.marker.id: item for item in report.markers}
    route_quality = "proven shortest" if route.optimal else "deterministic heuristic"
    lines = [
        f"# {_markdown(project.name)} revisit field sheet",
        "",
        f"Route: {len(route.stops)} stops, {route.total_distance:.3f} m, {route_quality}.",
        "",
        "> Coordinates use the survey's local metre grid. This route does not model terrain,",
        "> access restrictions, hazards, or accessibility. Confirm field conditions before",
        "> walking.",
        "",
    ]
    if not route.stops:
        lines.extend(["No marker revisit is required.", ""])
    for index, stop in enumerate(route.stops, start=1):
        item = audits[stop.marker.id]
        lines.extend(
            [
                f"## {index}. {_markdown(stop.marker.id)} — {_markdown(stop.marker.label)}",
                "",
                f"Position: `{stop.marker.point.x:g}, {stop.marker.point.y:g}`; "
                f"walk from prior stop: `{stop.segment_distance:.3f} m`.",
                "",
            ]
        )
        for view in item.missing_views:
            lines.append(f"- [ ] Capture `{_markdown(view)}`")
        for missing_file in item.missing_files:
            lines.append(f"- [ ] Reconcile missing file `{_markdown(missing_file)}`")
        if item.marker.attempts:
            lines.extend(["", "Previous attempts:"])
            for attempt in item.marker.attempts:
                note = f" — {_markdown(attempt.note)}" if attempt.note else ""
                lines.append(f"- {attempt.date.isoformat()}: `{attempt.outcome}`{note}")
        lines.append("")
    if report.unmatched_files:
        lines.extend(["## Unreferenced images", ""])
        lines.extend(f"- [ ] `{_markdown(path)}`" for path in report.unmatched_files)
        lines.append("")
    return "\n".join(lines)


def _canvas_point(point: Point, points: tuple[Point, ...]) -> tuple[float, float]:
    min_x = min(item.x for item in points)
    max_x = max(item.x for item in points)
    min_y = min(item.y for item in points)
    max_y = max(item.y for item in points)
    x_span = max(max_x - min_x, 1.0)
    y_span = max(max_y - min_y, 1.0)
    x = 60 + (point.x - min_x) / x_span * 780
    y = 540 - (point.y - min_y) / y_span * 480
    return x, y


def render_route_svg(project: SurveyProject, route: RoutePlan) -> str:
    route_points = (project.start, *(stop.marker.point for stop in route.stops))
    if project.end is not None and route.stops:
        route_points = (*route_points, project.end)
    canvas = tuple(_canvas_point(point, route_points) for point in route_points)
    polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y in canvas)
    title = html.escape(f"{project.name} revisit route")
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" '
        'viewBox="0 0 900 600" role="img" aria-labelledby="title desc">',
        f'<title id="title">{title}</title>',
        '<desc id="desc">Obstacle-free Euclidean route through incomplete markers.</desc>',
        '<rect width="900" height="600" fill="#f7f4ec"/>',
        '<path d="M60 40H840V560H60Z" fill="none" stroke="#d6cdbd"/>',
    ]
    if len(canvas) > 1:
        elements.append(
            f'<polyline points="{polyline}" fill="none" stroke="#315f5b" '
            'stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>'
        )
    start_x, start_y = canvas[0]
    elements.append(
        f'<rect x="{start_x - 8:.2f}" y="{start_y - 8:.2f}" width="16" height="16" '
        'fill="#c45d3c"/><text x="{:.2f}" y="{:.2f}" font-family="sans-serif" '
        'font-size="15">Start</text>'.format(start_x + 12, start_y - 12)
    )
    for index, stop in enumerate(route.stops, start=1):
        x, y = canvas[index]
        label = html.escape(f"{index}. {stop.marker.id} — {stop.marker.label}")
        elements.extend(
            [
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="#315f5b"/>',
                f'<text x="{x + 14:.2f}" y="{y - 12:.2f}" font-family="sans-serif" '
                f'font-size="15">{label}</text>',
            ]
        )
    if project.end is not None and route.stops:
        end_x, end_y = canvas[-1]
        elements.append(
            f'<rect x="{end_x - 7:.2f}" y="{end_y - 7:.2f}" width="14" height="14" fill="#8b5a2b"/>'
        )
    elements.append("</svg>\n")
    return "\n".join(elements)


def render_report_html(
    project: SurveyProject, report: AuditReport, route: RoutePlan, route_svg: str
) -> str:
    audits = {item.marker.id: item for item in report.markers}
    rows: list[str] = []
    for index, stop in enumerate(route.stops, start=1):
        item = audits[stop.marker.id]
        missing = ", ".join(item.missing_views) or "file reconciliation only"
        rows.append(
            "<tr>"
            f"<td>{index}</td><td>{html.escape(stop.marker.id)}</td>"
            f"<td>{html.escape(stop.marker.label)}</td>"
            f"<td>{html.escape(missing)}</td><td>{stop.segment_distance:.3f}</td>"
            "</tr>"
        )
    unmatched = (
        "".join(f"<li><code>{html.escape(path)}</code></li>" for path in report.unmatched_files)
        or "<li>None</li>"
    )
    quality = "proven shortest" if route.optimal else "deterministic heuristic"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(project.name)} — MarkerWalk report</title>
<style>
:root {{ color-scheme: light; font-family: system-ui, sans-serif; color: #292720;
background: #eee8dc; }}
body {{ margin: 0 auto; max-width: 1080px; padding: 2rem; }}
main {{ background: #fffdf8; border: 1px solid #d6cdbd; border-radius: 18px; padding: 2rem; }}
h1, h2 {{ color: #315f5b; }}
.summary {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
.card {{ background: #f3eee4; border-radius: 12px; padding: 1rem; min-width: 10rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #ddd3c4; padding: .65rem; text-align: left; }}
svg {{ max-width: 100%; height: auto; }}
.boundary {{ border-left: 5px solid #c45d3c; padding-left: 1rem; }}
</style>
</head>
<body><main>
<h1>{html.escape(project.name)}</h1>
<p class="boundary">Coordinates are a local metre grid. The route ignores terrain, access,
hazards, and accessibility; confirm field conditions before walking.</p>
<div class="summary">
<div class="card"><strong>{len(route.stops)}</strong><br>revisit stops</div>
<div class="card"><strong>{route.total_distance:.3f} m</strong><br>route distance</div>
<div class="card"><strong>{html.escape(quality)}</strong><br>route method</div>
<div class="card"><strong>{len(report.unmatched_files)}</strong><br>unreferenced images</div>
</div>
<h2>Route map</h2>
{route_svg}
<h2>Revisit stops</h2>
<table><thead><tr><th>#</th><th>ID</th><th>Marker</th><th>Needed</th>
<th>From prior (m)</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
<h2>Unreferenced images</h2><ul>{unmatched}</ul>
<p>Generated offline by MarkerWalk 0.1.0. No image recognition or upload was performed.</p>
</main></body></html>
"""


def render_plan_artifacts(
    project: SurveyProject, report: AuditReport, route: RoutePlan
) -> Mapping[str, str]:
    route_svg = render_route_svg(project, route)
    return {
        "field-sheet.md": render_field_sheet(project, report, route),
        "plan.json": render_plan_json(report, route),
        "report.html": render_report_html(project, report, route, route_svg),
        "route.csv": render_route_csv(report, route),
        "route.svg": route_svg,
    }
