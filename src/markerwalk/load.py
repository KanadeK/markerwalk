"""Strict JSON loader and path-containment boundary."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, NoReturn

from markerwalk.errors import InputError
from markerwalk.model import Attempt, Bounds, Marker, Photo, Point, SurveyProject

_OUTCOMES = frozenset({"not_found", "obstructed", "weather", "access", "other"})


def _fail(location: str, message: str) -> NoReturn:
    raise InputError(f"{location}: {message}")


def _object(value: object, location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(location, "must be an object")
    return value


def _array(value: object, location: str, *, non_empty: bool = False) -> Sequence[Any]:
    if not isinstance(value, list) or (non_empty and not value):
        suffix = "a non-empty array" if non_empty else "an array"
        _fail(location, f"must be {suffix}")
    return value


def _keys(value: Mapping[str, Any], location: str, allowed: set[str], required: set[str]) -> None:
    missing = sorted(required - value.keys())
    if missing:
        _fail(location, f"missing required field(s): {', '.join(missing)}")
    extra = sorted(value.keys() - allowed)
    if extra:
        _fail(location, f"unknown field(s): {', '.join(extra)}")


def _text(value: object, location: str, *, maximum: int = 200) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(location, "must be a non-empty string")
    cleaned = value.strip()
    if len(cleaned) > maximum:
        _fail(location, f"must be at most {maximum} characters")
    return cleaned


def _number(value: object, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(location, "must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        _fail(location, "must be a finite number")
    return result


def _unique_texts(value: object, location: str) -> tuple[str, ...]:
    items = tuple(
        _text(item, f"{location}[{index}]", maximum=40)
        for index, item in enumerate(_array(value, location, non_empty=True))
    )
    if len(items) != len(set(items)):
        _fail(location, "must not contain duplicates")
    return items


def _point(value: object, location: str) -> Point:
    data = _object(value, location)
    _keys(data, location, {"x", "y"}, {"x", "y"})
    return Point(_number(data["x"], f"{location}.x"), _number(data["y"], f"{location}.y"))


def _bounds(value: object, location: str) -> Bounds:
    data = _object(value, location)
    fields = {"min_x", "min_y", "max_x", "max_y"}
    _keys(data, location, fields, fields)
    result = Bounds(
        *(
            _number(data[field], f"{location}.{field}")
            for field in ("min_x", "min_y", "max_x", "max_y")
        )
    )
    if result.min_x > result.max_x or result.min_y > result.max_y:
        _fail(location, "minimum coordinates must not exceed maximum coordinates")
    return result


def _contained_path(root: Path, value: object, location: str) -> tuple[Path, str]:
    relative = _text(value, location, maximum=500).replace("\\", "/")
    declared = Path(relative)
    if declared.is_absolute():
        _fail(location, "must be relative to the survey directory")
    resolved = (root / declared).resolve()
    if not resolved.is_relative_to(root):
        _fail(location, "must stay inside the survey directory")
    return resolved, declared.as_posix()


def _assert_in_bounds(point: Point, bounds: Bounds | None, location: str) -> None:
    if bounds is not None and not bounds.contains(point):
        _fail(location, "must be inside survey.bounds")


def load_manifest(path: Path) -> SurveyProject:
    """Load and validate one survey manifest without guessing missing structure."""
    manifest_path = path.resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read JSON manifest {path}: {exc}") from exc

    top = _object(raw, "manifest")
    _keys(
        top,
        "manifest",
        {"schema_version", "survey", "markers"},
        {"schema_version", "survey", "markers"},
    )
    if top["schema_version"] != 1:
        _fail("manifest", "schema_version must be 1")

    root = manifest_path.parent
    survey = _object(top["survey"], "survey")
    _keys(
        survey,
        "survey",
        {"name", "photo_root", "views", "start", "end", "bounds"},
        {"name", "views", "start"},
    )
    name = _text(survey["name"], "survey.name")
    views = _unique_texts(survey["views"], "survey.views")
    start = _point(survey["start"], "survey.start")
    end = _point(survey["end"], "survey.end") if "end" in survey else None
    bounds = _bounds(survey["bounds"], "survey.bounds") if "bounds" in survey else None
    _assert_in_bounds(start, bounds, "survey.start")
    if end is not None:
        _assert_in_bounds(end, bounds, "survey.end")
    photo_root, photo_root_relative = _contained_path(
        root, survey.get("photo_root", "."), "survey.photo_root"
    )

    marker_rows = _array(top["markers"], "markers", non_empty=True)
    marker_ids: set[str] = set()
    assigned_photos: dict[Path, str] = {}
    markers: list[Marker] = []
    for marker_index, marker_value in enumerate(marker_rows):
        location = f"markers[{marker_index}]"
        marker = _object(marker_value, location)
        _keys(
            marker,
            location,
            {"id", "label", "x", "y", "required_views", "photos", "attempts"},
            {"id", "label", "x", "y", "required_views", "photos"},
        )
        marker_id = _text(marker["id"], f"{location}.id", maximum=80)
        if marker_id in marker_ids:
            _fail(f"{location}.id", f"duplicate marker id {marker_id!r}")
        marker_ids.add(marker_id)
        point = Point(_number(marker["x"], f"{location}.x"), _number(marker["y"], f"{location}.y"))
        _assert_in_bounds(point, bounds, location)
        required_views = _unique_texts(marker["required_views"], f"{location}.required_views")
        unknown_required = sorted(set(required_views) - set(views))
        if unknown_required:
            _fail(f"{location}.required_views", f"unknown view(s): {', '.join(unknown_required)}")

        photos: list[Photo] = []
        for photo_index, photo_value in enumerate(_array(marker["photos"], f"{location}.photos")):
            photo_location = f"{location}.photos[{photo_index}]"
            photo = _object(photo_value, photo_location)
            _keys(photo, photo_location, {"path", "views"}, {"path", "views"})
            resolved, relative = _contained_path(root, photo["path"], f"{photo_location}.path")
            if resolved in assigned_photos:
                first_marker = assigned_photos[resolved]
                _fail(
                    f"{photo_location}.path",
                    f"is assigned to more than one marker ({first_marker} and {marker_id})",
                )
            assigned_photos[resolved] = marker_id
            photo_views = _unique_texts(photo["views"], f"{photo_location}.views")
            unknown_photo_views = sorted(set(photo_views) - set(views))
            if unknown_photo_views:
                _fail(
                    f"{photo_location}.views", f"unknown view(s): {', '.join(unknown_photo_views)}"
                )
            photos.append(Photo(resolved, relative, photo_views))

        attempts: list[Attempt] = []
        for attempt_index, attempt_value in enumerate(
            _array(marker.get("attempts", []), f"{location}.attempts")
        ):
            attempt_location = f"{location}.attempts[{attempt_index}]"
            attempt = _object(attempt_value, attempt_location)
            _keys(attempt, attempt_location, {"date", "outcome", "note"}, {"date", "outcome"})
            raw_date = _text(attempt["date"], f"{attempt_location}.date", maximum=10)
            try:
                attempt_date = date.fromisoformat(raw_date)
            except ValueError as exc:
                raise InputError(f"{attempt_location}.date: must be an ISO date") from exc
            outcome = _text(attempt["outcome"], f"{attempt_location}.outcome", maximum=20)
            if outcome not in _OUTCOMES:
                _fail(
                    f"{attempt_location}.outcome", f"must be one of {', '.join(sorted(_OUTCOMES))}"
                )
            note = (
                _text(attempt["note"], f"{attempt_location}.note", maximum=500)
                if "note" in attempt
                else None
            )
            attempts.append(Attempt(attempt_date, outcome, note))

        markers.append(
            Marker(
                marker_id,
                _text(marker["label"], f"{location}.label"),
                point,
                required_views,
                tuple(photos),
                tuple(attempts),
            )
        )

    return SurveyProject(
        name,
        root,
        photo_root,
        photo_root_relative,
        views,
        start,
        end,
        bounds,
        tuple(markers),
    )
