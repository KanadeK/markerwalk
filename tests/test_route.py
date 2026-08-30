from __future__ import annotations

import json
import math
from pathlib import Path

from markerwalk.audit import audit_project
from markerwalk.load import load_manifest
from markerwalk.route import plan_route


def _write_manifest(tmp_path: Path, points: list[tuple[str, float, float]]) -> Path:
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Route",
            "views": ["front"],
            "start": {"x": 0, "y": 0},
            "end": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": marker_id,
                "label": marker_id,
                "x": x,
                "y": y,
                "required_views": ["front"],
                "photos": [],
            }
            for marker_id, x, y in points
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_exact_route_finds_the_shortest_round_trip(tmp_path: Path) -> None:
    path = _write_manifest(
        tmp_path,
        [("C", 0, 2), ("A", 2, 0), ("B", 2, 2)],
    )
    project = load_manifest(path)

    plan = plan_route(project, audit_project(project))

    assert plan.optimal is True
    assert plan.strategy == "held-karp"
    assert tuple(stop.marker.id for stop in plan.stops) == ("A", "B", "C")
    assert math.isclose(plan.total_distance, 8.0)
    assert plan.stops[-1].cumulative_distance == 6.0


def test_exact_route_breaks_equal_cost_ties_by_marker_id(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path, [("B", 1, 0), ("A", -1, 0)])
    project = load_manifest(path)

    plan = plan_route(project, audit_project(project))

    assert tuple(stop.marker.id for stop in plan.stops) == ("A", "B")
    assert math.isclose(plan.total_distance, 4.0)


def test_large_route_is_deterministic_and_labelled_heuristic(tmp_path: Path) -> None:
    points = [(f"M-{index:02d}", float(index), float(index % 3)) for index in range(15)]
    path = _write_manifest(tmp_path, list(reversed(points)))
    project = load_manifest(path)
    report = audit_project(project)

    first = plan_route(project, report)
    second = plan_route(project, report)

    assert first == second
    assert first.optimal is False
    assert first.strategy == "nearest-neighbour-2opt"
    assert len(first.stops) == 15


def test_complete_survey_needs_no_route(tmp_path: Path) -> None:
    photo = tmp_path / "done.jpg"
    photo.write_bytes(b"done")
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Done",
            "views": ["front"],
            "start": {"x": 0, "y": 0},
            "end": {"x": 10, "y": 10},
        },
        "markers": [
            {
                "id": "A",
                "label": "A",
                "x": 1,
                "y": 1,
                "required_views": ["front"],
                "photos": [{"path": "done.jpg", "views": ["front"]}],
            }
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    project = load_manifest(path)

    plan = plan_route(project, audit_project(project))

    assert plan.stops == ()
    assert plan.total_distance == 0
    assert plan.optimal is True
    assert plan.strategy == "empty"
