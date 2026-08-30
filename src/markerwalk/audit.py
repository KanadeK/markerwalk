"""Photo coverage analysis over a validated survey."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from markerwalk.errors import InputError
from markerwalk.model import Marker, SurveyProject

_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"})


@dataclass(frozen=True, slots=True)
class MarkerAudit:
    marker: Marker
    covered_views: tuple[str, ...]
    missing_views: tuple[str, ...]
    missing_files: tuple[str, ...]

    @property
    def incomplete(self) -> bool:
        return bool(self.missing_views or self.missing_files)


@dataclass(frozen=True, slots=True)
class AuditReport:
    project_name: str
    photo_root_exists: bool
    markers: tuple[MarkerAudit, ...]
    unmatched_files: tuple[str, ...]

    @property
    def incomplete_marker_ids(self) -> tuple[str, ...]:
        return tuple(item.marker.id for item in self.markers if item.incomplete)

    @property
    def complete(self) -> bool:
        return (
            self.photo_root_exists and not self.unmatched_files and not self.incomplete_marker_ids
        )


def _relative(project: SurveyProject, path: Path) -> str:
    return path.relative_to(project.root).as_posix()


def _discover_images(project: SurveyProject) -> set[Path]:
    if not project.photo_root.exists():
        return set()
    if not project.photo_root.is_dir():
        raise InputError("survey.photo_root: must resolve to a directory")

    discovered: set[Path] = set()
    for candidate in project.photo_root.rglob("*"):
        if not candidate.is_file() or candidate.suffix.lower() not in _IMAGE_SUFFIXES:
            continue
        resolved = candidate.resolve()
        if not resolved.is_relative_to(project.root):
            raise InputError(f"discovered image must stay inside the survey directory: {candidate}")
        discovered.add(resolved)
    return discovered


def audit_project(project: SurveyProject) -> AuditReport:
    """Compare declared coverage with existing local photo files."""
    marker_reports: list[MarkerAudit] = []
    referenced: set[Path] = set()
    for marker in project.markers:
        covered: set[str] = set()
        missing_files: list[str] = []
        for photo in marker.photos:
            referenced.add(photo.path)
            if photo.path.is_file():
                covered.update(photo.views)
            else:
                missing_files.append(photo.relative_path)
        covered_views = tuple(view for view in project.views if view in covered)
        missing_views = tuple(view for view in marker.required_views if view not in covered)
        marker_reports.append(
            MarkerAudit(marker, covered_views, missing_views, tuple(sorted(missing_files)))
        )

    discovered = _discover_images(project)
    unmatched = tuple(sorted(_relative(project, path) for path in discovered - referenced))
    return AuditReport(
        project.name,
        project.photo_root.is_dir(),
        tuple(marker_reports),
        unmatched,
    )
