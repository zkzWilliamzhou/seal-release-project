# ADR 0003: Normalization is declared, never guessed

Date: 2026-11-11
Status: accepted

## Context

A tool that silently rewrites timestamps, hashes, or ports can hide a real regression. A tool that rewrites nothing produces noise from the temporary workdir path.

## Decision

`manifest.normalization` accepts three boolean rules: `crlf`, `ansi`, `timestamps`. Unknown keys are rejected. The temporary workdir path is always replaced with `<WORKDIR>` because two runs cannot be compared otherwise. Every other byte stays. Declared `nondeterminism` lists channels whose differences become `UNKNOWN`.

## Consequences

`docs/00_brainstorming_and_grilling.md` records the rejected `--auto-normalize` proposal. A user who needs more normalization edits the manifest and sees the change in the manifest digest.
