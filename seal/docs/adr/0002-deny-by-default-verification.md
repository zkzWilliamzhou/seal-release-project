# ADR 0002: Verification denies execution by default

Date: 2026-11-11
Status: accepted

## Context

`verify` must re-execute probes from a bundle to be evidence rather than testimony. A bundle is a JSON file that can arrive from a stranger, a pull request, or an agent. Executing its commands by default turns a reviewer tool into a remote code execution path.

## Decision

`seal verify` exits 3 without `--trust`. With `--trust`, `check_bundle` runs before any execution and rejects the file if any digest fails. The runner then applies the allowlist, rejects reserved environment keys, copies the subject into a fresh workdir, bounds time and output, and kills the process group on timeout.

## Consequences

Users read the manifest before they trust it. The CLI refuses to be a silent installer. Network isolation stays the operator's job and is documented in `SECURITY.md`.
