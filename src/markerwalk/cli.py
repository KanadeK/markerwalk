"""MarkerWalk command-line interface."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from markerwalk import __version__
from markerwalk.audit import audit_project
from markerwalk.errors import InputError
from markerwalk.load import load_manifest
from markerwalk.render import render_audit_json, render_plan_artifacts
from markerwalk.route import plan_route


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="markerwalk",
        description="Audit survey photo coverage and plan deterministic marker revisits.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    audit = commands.add_parser("audit", help="Report coverage gaps and unreferenced images.")
    audit.add_argument("manifest", type=Path)
    audit.add_argument("--json", dest="json_output", type=Path)

    plan = commands.add_parser("plan", help="Create a complete offline revisit packet.")
    plan.add_argument("manifest", type=Path)
    plan.add_argument("--output", type=Path, required=True)
    return parser


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _write_plan_directory(output: Path, artifacts: dict[str, str]) -> None:
    if output.exists():
        raise InputError(f"output directory already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for name, content in sorted(artifacts.items()):
            (temporary / name).write_text(content, encoding="utf-8", newline="\n")
        temporary.rename(output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _audit_command(manifest: Path, json_output: Path | None) -> int:
    report = audit_project(load_manifest(manifest))
    if json_output is not None:
        _atomic_text(json_output, render_audit_json(report))
    print(
        f"MarkerWalk audit: {len(report.incomplete_marker_ids)}/{len(report.markers)} "
        f"markers incomplete; {len(report.unmatched_files)} unreferenced image(s)."
    )
    return 0 if report.complete else 1


def _plan_command(manifest: Path, output: Path) -> int:
    project = load_manifest(manifest)
    report = audit_project(project)
    route = plan_route(project, report)
    artifacts = dict(render_plan_artifacts(project, report, route))
    _write_plan_directory(output, artifacts)
    quality = "optimal" if route.optimal else "heuristic"
    print(
        f"MarkerWalk plan: wrote {len(artifacts)} artifacts to {output} "
        f"({len(route.stops)} stops, {route.total_distance:.3f} m, {quality})."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "audit":
            return _audit_command(args.manifest, args.json_output)
        return _plan_command(args.manifest, args.output)
    except (InputError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
