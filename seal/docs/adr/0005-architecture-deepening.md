# ADR 0005: One module owns all human-readable text

Date: 2026-11-11
Status: accepted

## Context

`compare.py` exposed classification and a human renderer through one interface. `demo.py` exposed a second renderer with the same job. Three callers reached across the seam. The `improve-codebase-architecture` skill's deletion test showed that removing the renderers from their old modules concentrates presentation complexity in one place.

The brief forbids changing any program function during the architecture pass.

## Decision

Create `src/seal/render.py` with `render_report` and `render_demo`, moved verbatim. `compare.py` keeps classification. `demo.py` keeps the fixture. `cli.py`, `bundle.py` and `demo.py` import from `render.py`. No verdict constant, exit code, JSON key, digest, policy rule, or CLI flag changes.

Rejected alternatives: extracting CLI JSON helpers (fails the deletion test, one adapter), and splitting safety validation out of `runner.py` (real seam, but moves code hardened by review rounds 3, 4 and 5; deferred to v2).

## Verification obligations

`tests/behavior_lock.py --check` must print the same hash as the pre-refactor baseline. The 36-test suite and all eight review rounds must keep their results. `docs/05_architecture_refactor.md` holds the before and after hashes.

## Consequences

`compare.py` becomes a deeper module with one interface. The seam between classification and presentation now has one adapter on each side, so it is real. A future HTML or JSON renderer enters through `render.py` without touching the verdict model.
