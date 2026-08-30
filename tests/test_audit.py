from __future__ import annotations

import json
from pathlib import Path

from markerwalk.audit import audit_project
from markerwalk.load import load_manifest


def test_audit_reports_covered_missing_and_unmatched_photos(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    photos.mkdir()
    (photos / "A-01-front.JPG").write_bytes(b"front")
    (photos / "unmatched.png").write_bytes(b"extra")
    (photos / "notes.txt").write_text("not an image", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Coverage",
            "photo_root": "photos",
            "views": ["front", "inscription", "context"],
            "start": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": "A-01",
                "label": "First",
                "x": 1,
                "y": 0,
                "required_views": ["front", "inscription"],
                "photos": [{"path": "photos/A-01-front.JPG", "views": ["front"]}],
            },
            {
                "id": "A-02",
                "label": "Second",
                "x": 2,
                "y": 0,
                "required_views": ["front", "context"],
                "photos": [{"path": "photos/A-02-missing.jpg", "views": ["front", "context"]}],
                "attempts": [{"date": "2026-08-02", "outcome": "not_found", "note": "no marker"}],
            },
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = audit_project(load_manifest(path))

    assert report.complete is False
    assert report.photo_root_exists is True
    assert report.unmatched_files == ("photos/unmatched.png",)
    first, second = report.markers
    assert first.marker.id == "A-01"
    assert first.covered_views == ("front",)
    assert first.missing_views == ("inscription",)
    assert first.missing_files == ()
    assert second.covered_views == ()
    assert second.missing_views == ("front", "context")
    assert second.missing_files == ("photos/A-02-missing.jpg",)
    assert second.marker.attempts[0].outcome == "not_found"
    assert report.incomplete_marker_ids == ("A-01", "A-02")


def test_audit_is_complete_when_every_required_view_has_an_existing_file(tmp_path: Path) -> None:
    (tmp_path / "front.jpg").write_bytes(b"front and inscription")
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Complete",
            "views": ["front", "inscription"],
            "start": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": "A-01",
                "label": "Complete marker",
                "x": 1,
                "y": 1,
                "required_views": ["front", "inscription"],
                "photos": [{"path": "front.jpg", "views": ["front", "inscription"]}],
            }
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = audit_project(load_manifest(path))

    assert report.complete is True
    assert report.incomplete_marker_ids == ()
    assert report.unmatched_files == ()


def test_missing_photo_root_is_an_actionable_audit_result(tmp_path: Path) -> None:
    manifest = {
        "schema_version": 1,
        "survey": {
            "name": "Missing root",
            "photo_root": "photos",
            "views": ["front"],
            "start": {"x": 0, "y": 0},
        },
        "markers": [
            {
                "id": "A-01",
                "label": "Marker",
                "x": 1,
                "y": 1,
                "required_views": ["front"],
                "photos": [],
            }
        ],
    }
    path = tmp_path / "survey.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report = audit_project(load_manifest(path))

    assert report.photo_root_exists is False
    assert report.complete is False
