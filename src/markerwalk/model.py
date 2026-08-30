"""Typed survey records used after boundary validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def contains(self, point: Point) -> bool:
        return self.min_x <= point.x <= self.max_x and self.min_y <= point.y <= self.max_y


@dataclass(frozen=True, slots=True)
class Photo:
    path: Path
    relative_path: str
    views: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Attempt:
    date: date
    outcome: str
    note: str | None


@dataclass(frozen=True, slots=True)
class Marker:
    id: str
    label: str
    point: Point
    required_views: tuple[str, ...]
    photos: tuple[Photo, ...]
    attempts: tuple[Attempt, ...]


@dataclass(frozen=True, slots=True)
class SurveyProject:
    name: str
    root: Path
    photo_root: Path
    photo_root_relative: str
    views: tuple[str, ...]
    start: Point
    end: Point | None
    bounds: Bounds | None
    markers: tuple[Marker, ...]
