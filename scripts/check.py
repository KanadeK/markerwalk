"""Run MarkerWalk's complete local release gate."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

from markerwalk import __version__

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / ".tmp" / f"release-gate-{os.getpid()}"
DIST = ROOT / "dist"
RELEASE = ROOT / "release"


def run(
    *command: str, expected: int = 0, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=capture,
    )
    if result.returncode != expected:
        if capture:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(
            f"command returned {result.returncode}; expected {expected}: {' '.join(command)}"
        )
    return result


def clean_generated() -> None:
    for path in (DIST, RELEASE):
        if path.exists():
            resolved = path.resolve()
            if not resolved.is_relative_to(ROOT):
                raise SystemExit(f"refusing to clean outside repository: {resolved}")
            shutil.rmtree(resolved)
    GATE.mkdir(parents=True)
    RELEASE.mkdir()


def verify_examples(python: str, label: str) -> None:
    incomplete = ROOT / "examples" / "lantern-hill" / "survey.json"
    complete = ROOT / "examples" / "complete" / "survey.json"
    invalid = ROOT / "examples" / "invalid-path" / "survey.json"
    run(
        python,
        "-m",
        "markerwalk",
        "audit",
        str(incomplete),
        "--json",
        str(GATE / "audit.json"),
        expected=1,
    )
    run(python, "-m", "markerwalk", "audit", str(complete))
    invalid_output = GATE / "invalid.json"
    run(
        python,
        "-m",
        "markerwalk",
        "audit",
        str(invalid),
        "--json",
        str(invalid_output),
        expected=2,
    )
    if invalid_output.exists():
        raise SystemExit("invalid example unexpectedly created output")
    visit = GATE / f"visit-{label}"
    run(python, "-m", "markerwalk", "plan", str(incomplete), "--output", str(visit))
    expected = {"field-sheet.md", "plan.json", "report.html", "route.csv", "route.svg"}
    actual = {path.name for path in visit.iterdir()}
    if actual != expected:
        raise SystemExit(f"example artifact mismatch: {sorted(actual)}")


def build_example_bundle() -> Path:
    output = RELEASE / f"markerwalk-examples-{__version__}.zip"
    files = sorted(path for path in (ROOT / "examples").rglob("*") if path.is_file())
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return output


def isolated_install(python: str) -> None:
    wheels = sorted(DIST.glob("markerwalk-*.whl"))
    sdists = sorted(DIST.glob("markerwalk-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("build must create exactly one wheel and one source distribution")

    environment = GATE / "installed"
    venv.EnvBuilder(with_pip=True, clear=True).create(environment)
    installed_python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(str(installed_python), "-m", "pip", "install", "--no-deps", str(wheels[0]))
    version = run(str(installed_python), "-m", "markerwalk", "--version", capture=True)
    if version.stdout.strip() != f"markerwalk {__version__}":
        raise SystemExit(f"installed version mismatch: {version.stdout.strip()}")
    verify_examples(str(installed_python), "installed")


def main() -> int:
    clean_generated()
    expected_tag = (
        os.environ.get("GITHUB_REF_NAME") if os.environ.get("GITHUB_REF_TYPE") == "tag" else None
    )
    if expected_tag and expected_tag != f"v{__version__}":
        raise SystemExit(f"tag {expected_tag} does not match package version {__version__}")

    python = sys.executable
    run(python, "-m", "ruff", "format", "--check", ".")
    run(python, "-m", "ruff", "check", ".")
    run(python, "-m", "mypy")
    run(python, "-m", "pytest", "--basetemp", str(GATE / "pytest"))
    verify_examples(python, "source")
    audit_requirements = GATE / "audit-requirements.txt"
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv is required to export the committed lockfile")
    run(
        uv,
        "export",
        "--cache-dir",
        str(ROOT / ".uv-cache"),
        "--locked",
        "--all-extras",
        "--no-hashes",
        "--no-emit-project",
        "--output-file",
        str(audit_requirements),
    )
    run(
        python,
        "-m",
        "pip_audit",
        "--requirement",
        str(audit_requirements),
        "--strict",
        "--disable-pip",
        "--no-deps",
        "--progress-spinner",
        "off",
        "--cache-dir",
        str(GATE / "pip-audit-cache"),
    )
    run(python, "-m", "build", "--outdir", str(DIST))
    isolated_install(python)
    bundle = build_example_bundle()
    print(
        "MARKERWALK_RELEASE_GATE=PASS "
        f"version={__version__} wheel={next(DIST.glob('*.whl')).name} "
        f"sdist={next(DIST.glob('*.tar.gz')).name} examples={bundle.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
