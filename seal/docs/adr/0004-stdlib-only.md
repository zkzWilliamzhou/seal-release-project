# ADR 0004: Standard library only at runtime

Date: 2026-11-11
Status: accepted

## Context

The tool executes untrusted artifacts and asks reviewers to trust its verdict. Every runtime dependency adds code the reviewer must audit and a supply chain the tool itself depends on.

## Decision

`src/seal/**` imports the Python standard library only. Tests use `unittest`. `pyproject.toml` lists no runtime dependencies. setuptools appears only as a build requirement for `pip install .`.

## Consequences

The whole implementation fits in one reading session. Windows process-group handling, richer sandboxing, and HTML reports are deferred until they can be built without adding runtime dependencies.
