# Threat model

Owner: A4. Gate: G4. Every row has a mitigation and an executable test. Round 3, 4, 5 and 6 of `reviews/run_rounds.py` run those tests.

## Assets

1. The host filesystem outside the temporary workdir.
2. Secrets in the parent environment and in probe environment values.
3. The reviewer's verdict. A false `SAME` or `CLEAN` is worse than a crash.
4. Host CPU, memory, disk and process slots.

## Trust boundaries

- `sealfile.json` arrives from the user. It is validated but still user code.
- An evidence bundle arrives from a stranger. It is untrusted input.
- A subject directory is copied into a sandbox. The program inside it is arbitrary code.

## Threats

| # | Threat | Attack | Mitigation | Test |
|---|---|---|---|---|
| T1 | Shell injection | `args: ["a; rm -rf /"]` | `shell=False`, argv passed literally | round 3 `shell metacharacters stay literal` |
| T2 | Command substitution | `target.command: ["sh", "-c", "..."]` | `policy.allowed_commands` restricts basenames; `sh` is not in the default demo allowlist | round 3 `disallowed executable refused` |
| T3 | Executable outside subject | `target.command: ["/bin/echo"]` or `["../x"]` | `_check_command` resolves against the subject root and rejects escapes | round 3 two checks |
| T4 | Executing the original subject | A subject-relative `./main.py` | The path is remapped into the copied workdir | round 3 `subject executable runs from workdir copy` |
| T5 | Orphan child survives timeout | Probe spawns a grandchild that writes after the parent dies | `start_new_session=True`, `os.killpg` on timeout | round 3 `timeout kills the whole process group` |
| T6 | Environment redirection | `LD_PRELOAD`, `PYTHONPATH`, `PATH`, `HOME` in `probe.env` | `RESERVED_ENV_KEYS` rejected by `validate` | round 4 `reserved environment keys refused` |
| T7 | Secret leakage into evidence | Probe prints an API token, or the host has one | Pattern-based redaction; only env names stored | round 4 two checks |
| T8 | Output bomb | Probe writes 100 MiB to stdout or stderr | `max_output_bytes` cap, `output_capped` status | round 1 unit test and round 4 stderr cap |
| T9 | Symlink escape | Subject contains a symlink to a file outside the tree | `_validate_subject_tree` rejects every symlink | round 5 two checks |
| T10 | Special file hangs the runner | FIFO or device node in the subject | Non-regular files rejected before `copytree` | round 5 `FIFO / non-regular file refused` |
| T11 | Disk exhaustion | Subject contains a multi-gigabyte file | `policy.max_subject_bytes` checked before copying | round 5 `subject size cap enforced` |
| T12 | Tampered bundle | Edit a record, report, provenance or manifest | Five recomputed digests, checked before execution | round 6 `five tamper cases refused` |
| T13 | Malformed evidence crashes the tool | Missing channel or empty probe set | Clean `SealError` / `TamperError`, no traceback, no false `CLEAN` | round 6 two checks |
| T14 | Silent execution on verify | Bundle arrives from a PR | `--trust` flag required, documented refusal | round 6 `verify without --trust refused` |
| T15 | False clean from a timeout | A timed-out probe compared to a healthy one | `UNKNOWN` never becomes `SAME`; `INCOMPLETE` is its own overall state | round 6 `timeout verdict is never CLEAN` |
| T16 | Evidence laundering | A producer recomputes every digest after editing content | Not mitigated. Documented in `SECURITY.md`. | documented, not solved |
| T17 | Network egress | Probe reaches an internal service | Not mitigated by the tool. Operator must isolate the network. | documented, not solved |
| T18 | Memory and thread exhaustion | Probe forks or allocates without bound | Not mitigated. Use OS limits. | documented, not solved |

## Rounds that attacked this model

Round 3 found T4 and T5. Round 4 found T6. Round 5 found T10 and T11. Round 6 found T13. Each finding produced a code change, a test, and a re-run recorded in `reviews/round-XX.md`.

## What a security reviewer should try next

Windows process-group handling, symlink races between validation and copy, `/proc` visibility, and a signed-bundle design. Each needs a decision record before implementation.
