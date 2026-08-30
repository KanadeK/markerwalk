# Contributing to MarkerWalk

Use Python 3.11+ and uv. Keep runtime code dependency-free unless a proposal demonstrates that a
new dependency is necessary for the current contract.

```console
uv sync --extra dev --locked
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run python scripts/check.py
```

Behavior changes start with a failing test. Preserve exit codes, deterministic output, manifest
authority, path containment, markup escaping, and honest route-quality labels. Update the spec and
changelog with public-contract changes. Do not add image recognition, uploads, or account handling
as incidental features.

Submit focused commits using `feat:`, `fix:`, `test:`, `docs:`, or `chore:` prefixes. Never commit
real cemetery survey data, credentials, personal contact information, build output, or photo files
without explicit permission from their rights holder.

