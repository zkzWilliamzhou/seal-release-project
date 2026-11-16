# Implementation plan

Input: the approved design in `docs/00_brainstorming_and_grilling.md`. Owner: A2. Gate: G2.

## One invariant

A third party can reproduce the answer to "what did this change change?" without trusting the producer's prose. Every module below protects one part of that invariant.

## Module boundaries

| Module | One responsibility | Interface | Does not own |
|---|---|---|---|
| `errors.py` | Stable error types and exit codes | `SealError`, `UsageError`, `ManifestError`, `PolicyError`, `TamperError` | Any I/O |
| `canonical.py` | Canonical JSON, digests, declared normalization, redaction | `canonical`, `digest`, `normalize`, `redact` | Verdicts, execution |
| `manifest.py` | Parse, validate and fill the declared contract | `validate`, `load`, `write_default`, `manifest_digest` | Running probes |
| `runner.py` | Sandboxed execution and observation capture | `run_probe`, `build_record`, digest helpers | Comparing, rendering |
| `compare.py` | Four-state classification and the human report | `compare_records`, `render_report` | Execution, bundles |
| `bundle.py` | Self-contained evidence, tamper checks, reproduction | `build_bundle`, `check_bundle`, `reproduce` | CLI parsing |
| `demo.py` | A 30-second self-contained proof | `run_demo`, `render_demo` | Any CLI flag |
| `cli.py` | Argument parsing, dispatch, exit codes, JSON output | `main`, `build_parser` | Business rules |

## Command contracts

| Command | Required input | Output | Success | Failure |
|---|---|---|---|---|
| `init` | none | `sealfile.json` | 0 | 2 if the file exists without `--force` |
| `record` | subject dir, tag, manifest | record JSON | 0 | 2 policy or manifest error, 3 bad tag |
| `compare` | two record JSON files, matching manifest | report text or JSON, optional bundle | 0 clean / intended, 1 unexpected | 2 digest or manifest mismatch |
| `verify` | bundle, old dir, new dir, `--trust` | reproduction result | 0 reproduced | 1 mismatch, 2 tamper, 3 missing trust |
| `demo` | none | report text or JSON | 0 when the hidden change is caught | 2 when the demo itself fails |

## Observation surface

Six channels per probe: `status`, `stdout`, `stderr`, `exit_code`, `files_delta`, `env_names`. `duration_ms` is diagnostic data and never enters a verdict. File effects are the delta between the copied subject and the post-run workdir.

## Test plan

`tests/` uses `unittest`. Coverage obligations:

- manifest validation: every rejected key, bound, and type
- runner: capture, timeout, output cap, redaction, symlinks, special files, size cap, process groups
- compare: all four verdicts, manifest drift, tampered records
- bundle: five tamper cases, reproduction, swapped subject
- CLI: full pipeline, exit codes, tag traversal, `--trust` gate
- `tests/behavior_lock.py`: golden CLI transcript used by the architecture pass

## Non-goals carried over from the design

No cloud, no plugin system, no dashboard, no automatic input discovery, no cryptographic signing, no deterministic replay of networked programs, no star-count claim.

## Rejected scope

| Proposal | Why it was rejected |
|---|---|
| `--auto-normalize` | Hidden normalization can erase a real regression |
| A web report | Adds a dependency and moves the demo away from the terminal |
| Agent plugin | Day one needs one command, not an integration surface |
| Automatic probe generation | Requires program understanding the MVP does not have |

## ADRs

- `0001-four-verdicts.md` the verdict model
- `0002-deny-by-default-verification.md` the trust gate
- `0003-declared-normalization.md` normalization policy
- `0004-stdlib-only.md` dependency policy
- `0005-architecture-deepening.md` the behavior-locked refactor
