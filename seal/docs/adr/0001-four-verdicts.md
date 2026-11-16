# ADR 0001: Four verdicts, with UNKNOWN as a first-class state

Date: 2026-11-11
Status: accepted

## Context

A binary pass/fail comparison forces a tool to guess when evidence is incomplete. A timeout, a truncated output, a declared nondeterministic source, and a malformed observation all look like "different bytes". Calling them failures produces noise. Calling them passes produces false confidence.

## Decision

Every channel receives one of `SAME`, `INTENDED`, `UNEXPECTED`, `UNKNOWN`.

- `SAME`: canonical values match and no unknown condition applies.
- `INTENDED`: values differ and the channel sits in `intent.scope`.
- `UNEXPECTED`: values differ outside `intent.scope`.
- `UNKNOWN`: a blocking condition exists. It never converts to `SAME`.

`UNEXPECTED` sets exit code 1. `INCOMPLETE` (no unexpected, some unknown) sets exit code 0 unless `--strict-unknown` is given.

## Consequences

Producers declare intent before recording. The scope is hashed into the manifest and printed in the report. A reviewer can see exactly what the producer claimed. Precision beats coverage: a useful report has few `UNKNOWN` channels.
