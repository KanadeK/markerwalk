# Implementation Plan: MarkerWalk v0.1.0

## Overview

Build one offline CLI pipeline from a reviewed survey manifest to coverage evidence and a
revisit packet, then package and release the exact verified source state.

## Architecture Decisions

- Use standard-library runtime code to keep field use offline and installation small.
- Treat the JSON manifest as the only authority; the photo tree supplies existence and
  reconciliation evidence but never guesses marker identity.
- Separate typed loading, analysis, routing, and rendering so each has a narrow test surface.
- Use exact routing only where its cost is bounded; label heuristic results honestly.

## Dependency Graph

```text
schema + path loader
    -> coverage analysis
        -> revisit routing
            -> artifact renderers
                -> CLI + examples
                    -> release gate + CI + package
```

## Phases

### Phase 1: Foundation

- Define public schema, typed model, validation errors, and path containment.
- Add failing tests for valid, invalid, and path-escape manifests; implement until green.

### Checkpoint: Foundation

- Focused model tests pass and invalid input creates no output.

### Phase 2: Real analysis

- Add failing coverage tests; implement missing-view, missing-file, attempt, and unmatched-file
  findings.
- Add failing exact/heuristic routing tests; implement deterministic routing.

### Checkpoint: Core

- Unit suite passes; exact routes match brute-force fixtures.

### Phase 3: User flow

- Add CLI integration tests first, then JSON/CSV/Markdown/SVG/HTML rendering and atomic outputs.
- Add three synthetic examples and document input, limits, acceptance, and repair steps.

### Checkpoint: Product

- Real commands exhibit exit `0`, `1`, and `2`; artifact contents are inspectable and stable.

### Phase 4: Release engineering

- Add full local gate, cross-platform CI, tag release workflow, changelog, security and
  contribution docs.
- Build and install artifacts in an isolated environment; verify contributor hygiene.
- Create public GitHub repository, push main, wait for CI, tag v0.1.0, wait for Release, verify
  public assets and fresh install, then send Gmail.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Accidental outside-folder reads | High | Resolve and contain every declared/discovered path |
| Markup injection from labels/notes | Medium | Escape every HTML/SVG/text field at render time |
| Route described as guaranteed safe | High | State Euclidean/obstacle-free boundary in outputs/docs |
| Exact routing grows exponentially | Medium | Exact cap at 14; deterministic labelled heuristic above |
| Release state differs from tested state | High | Tag only clean tested commit; verify remote SHA and assets |

## Open Questions

None within v0.1 scope.

