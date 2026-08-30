# ADR-0001: Manifest authority and a standard-library runtime

## Status

Accepted

## Date

2026-08-30

## Context

Survey volunteers may work offline with sensitive local project notes and inconsistent file names.
The v0.1 product must produce inspectable results without accounts, external APIs, image
classification, a database, or a browser server. It must also reject ambiguous marker identity.

## Decision

Use one strict JSON manifest as the only identity and view-coverage authority. Reconcile it against
the local filesystem, but never infer identity from file names or pixels. Implement the runtime with
Python's standard library and keep build/test tools optional.

Use Held-Karp for a proven shortest route through at most 14 incomplete markers. Above that bound,
use deterministic nearest-neighbour plus 2-opt and label the result as heuristic.

## Alternatives considered

### EXIF and filename inference

Rejected because convenient guesses can attach a photo to the wrong person or mark an unverified
view complete. Explicit review is the product's purpose.

### Platform API integration

Rejected for v0.1 because accounts, rate limits, platform terms, network failures, and mutable
remote state would weaken the offline evidence boundary.

### Always-exact routing

Rejected because exponential cost becomes an unbounded denial-of-service surface. The bounded exact
mode preserves a strong small-project result while the labelled heuristic remains useful at scale.

### Web application first

Rejected because a UI without trustworthy reconciliation and routing would be a shell. Stable core
artifacts make a later UI possible without creating a second authority.

## Consequences

- Users must author or export a manifest instead of receiving automatic identity guesses.
- Runtime installation is small and offline after package acquisition.
- JSON/CSV/Markdown/SVG/HTML remain portable and reviewable.
- Route geometry is intentionally limited and must not be treated as a field-safety model.

