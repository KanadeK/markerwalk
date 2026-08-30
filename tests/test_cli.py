from __future__ import annotations

import json
from pathlib import Path

from markerwalk.cli import main


def _incomplete_survey(tmp_path: Path) -> Path:
    photos = tmp_path / "photos"
    photos.mkdir()
    (photos / "A-front.jpg").write_bytes(b"front")
    (photos / "unmatched.webp").write_bytes(b"extra")
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Lantern & Hill",
            "photo_root": "photos",
            "views": ["front", "inscription", "context"],
            "start": {"x": 0, "y": 0},
            "end": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": "A-01",
                "label": "Ada <North>",
                "x": 2,
                "y": 0,
                "required_views": ["front", "inscription"],
                "photos": [{"path": "photos/A-front.jpg", "views": ["front"]}],
                "attempts": [{"date": "2026-08-01", "outcome": "weather", "note": "glare | rain"}],
            },
            {
                "id": "B-01",
                "label": "B marker",
                "x": 2,
                "y": 2,
                "required_views": ["context"],
                "photos": [],
            },
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_audit_writes_json_and_returns_one_for_actionable_gaps(
    tmp_path: Path, capsys: object
) -> None:
    manifest = _incomplete_survey(tmp_path)
    output = tmp_path / "result" / "audit.json"

    exit_code = main(["audit", str(manifest), "--json", str(output)])

    assert exit_code == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["summary"] == {
        "complete": False,
        "incomplete_markers": 2,
        "markers": 2,
        "unmatched_files": 1,
    }
    assert payload["markers"][0]["missing_views"] == ["inscription"]
    assert payload["unmatched_files"] == ["photos/unmatched.webp"]


def test_plan_writes_five_stable_artifacts_and_escapes_markup(tmp_path: Path) -> None:
    manifest = _incomplete_survey(tmp_path)
    first = tmp_path / "first-plan"
    second = tmp_path / "second-plan"

    assert main(["plan", str(manifest), "--output", str(first)]) == 0
    assert main(["plan", str(manifest), "--output", str(second)]) == 0

    expected = {"plan.json", "route.csv", "field-sheet.md", "route.svg", "report.html"}
    assert {path.name for path in first.iterdir()} == expected
    assert {path.name for path in second.iterdir()} == expected
    for name in expected:
        assert (first / name).read_bytes() == (second / name).read_bytes()

    plan = json.loads((first / "plan.json").read_text(encoding="utf-8"))
    assert plan["route"]["optimal"] is True
    assert [stop["marker_id"] for stop in plan["route"]["stops"]] == ["A-01", "B-01"]
    html = (first / "report.html").read_text(encoding="utf-8")
    svg = (first / "route.svg").read_text(encoding="utf-8")
    assert "Ada <North>" not in html
    assert "Ada &lt;North&gt;" in html
    assert "Ada <North>" not in svg


def test_invalid_input_returns_two_without_creating_requested_output(
    tmp_path: Path, capsys: object
) -> None:
    manifest = tmp_path / "broken.json"
    manifest.write_text("{not-json", encoding="utf-8")
    output = tmp_path / "audit.json"

    exit_code = main(["audit", str(manifest), "--json", str(output)])

    assert exit_code == 2
    assert not output.exists()


def test_existing_plan_directory_is_not_overwritten(tmp_path: Path) -> None:
    manifest = _incomplete_survey(tmp_path)
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    exit_code = main(["plan", str(manifest), "--output", str(output)])

    assert exit_code == 2
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert {path.name for path in output.iterdir()} == {"keep.txt"}
