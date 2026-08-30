from __future__ import annotations

import json
from pathlib import Path

import pytest

from markerwalk.errors import InputError
from markerwalk.load import load_manifest


def test_loads_a_valid_manifest_into_typed_records(tmp_path: Path) -> None:
    photo_dir = tmp_path / "photos"
    photo_dir.mkdir()
    (photo_dir / "A-01-front.jpg").write_bytes(b"synthetic-photo")
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Lantern Hill",
            "photo_root": "photos",
            "views": ["front", "inscription", "context"],
            "start": {"x": 0, "y": 0},
            "end": {"x": 1, "y": 1},
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 20, "max_y": 10},
        },
        "markers": [
            {
                "id": "A-01",
                "label": "Ada North",
                "x": 3,
                "y": 2,
                "required_views": ["front", "inscription"],
                "photos": [{"path": "photos/A-01-front.jpg", "views": ["front"]}],
                "attempts": [{"date": "2026-08-01", "outcome": "weather", "note": "glare"}],
            }
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    project = load_manifest(path)

    assert project.name == "Lantern Hill"
    assert project.root == tmp_path.resolve()
    assert project.photo_root == photo_dir.resolve()
    assert project.start.x == 0
    assert project.end is not None and project.end.y == 1
    assert project.markers[0].required_views == ("front", "inscription")
    assert project.markers[0].photos[0].path == (photo_dir / "A-01-front.jpg").resolve()
    assert project.markers[0].attempts[0].outcome == "weather"


def test_rejects_a_photo_path_that_escapes_the_manifest_directory(tmp_path: Path) -> None:
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Escape",
            "photo_root": "photos",
            "views": ["front"],
            "start": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": "A-01",
                "label": "Outside",
                "x": 1,
                "y": 1,
                "required_views": ["front"],
                "photos": [{"path": "../outside.jpg", "views": ["front"]}],
            }
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(InputError, match="must stay inside the survey directory"):
        load_manifest(path)


def test_rejects_one_photo_assigned_to_two_markers(tmp_path: Path) -> None:
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Duplicate",
            "views": ["front"],
            "start": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": marker_id,
                "label": marker_id,
                "x": index,
                "y": 1,
                "required_views": ["front"],
                "photos": [{"path": "same.jpg", "views": ["front"]}],
            }
            for index, marker_id in enumerate(("A-01", "A-02"), start=1)
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(InputError, match="assigned to more than one marker"):
        load_manifest(path)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("schema_version", 2, "schema_version must be 1"),
        ("markers", [], "markers: must be a non-empty array"),
    ],
)
def test_rejects_invalid_top_level_contract(
    tmp_path: Path, field: str, replacement: object, message: str
) -> None:
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Contract",
            "views": ["front"],
            "start": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": "A-01",
                "label": "A-01",
                "x": 1,
                "y": 1,
                "required_views": ["front"],
                "photos": [],
            }
        ],
    }
    manifest[field] = replacement
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(InputError, match=message):
        load_manifest(path)
