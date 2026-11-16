# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | yes |

## Reporting

Send a private report to the maintainers through GitHub Security Advisories. Include the manifest, the subject fixture, the exact command, and the observed effect. Do not attach production secrets. Maintainers reply within 7 days and publish a fix or a documented mitigation within 30 days.

## What seal executes

`seal record` runs the commands you declare in `sealfile.json`. `seal verify --trust` runs commands stored inside an evidence bundle. Both paths execute arbitrary code with your user privileges. Treat every foreign bundle as untrusted input.

## Enforced controls

| Control | Where |
|---|---|
| `shell=False`, argv only | `src/seal/runner.py` |
| Fresh temporary workdir per probe | `runner.py` |
| Subject tree copied, never executed in place | `runner.py` |
| Symlinks and non-regular files rejected | `runner.py:_validate_subject_tree` |
| Subject size bounded by `policy.max_subject_bytes` | `manifest.py`, `runner.py` |
| Subject-relative executables remapped into the copy | `runner.py:_check_command` |
| Allowlist of executable basenames | `manifest.py:validate` |
| Reserved environment keys refused | `manifest.py:RESERVED_ENV_KEYS` |
| Process group killed on timeout | `runner.py:_run_argv` |
| Output capped | `runner.py` |
| Secret values redacted before storage | `runner.py`, `canonical.py:redact` |
| Bundle digests checked before execution | `bundle.py:check_bundle` |
| `--trust` required for verification | `cli.py:cmd_verify` |

## Residual risks you must handle

1. **Network access.** `policy.allow_network` is a declaration. The runner does not create a network namespace. Run `verify` inside a container with no network interface, or on a machine with egress filtering.
2. **CPU, memory and disk.** Timeouts bound wall clock. They do not bound memory, threads, or disk writes inside the workdir. Use OS limits (`ulimit`, cgroups) for untrusted subjects.
3. **Device access.** The runner cleans `PATH`, `HOME`, `LC_ALL`, `TZ`, and `PYTHONHASHSEED`. It does not hide `/dev`, `/proc`, or the host filesystem from a subject program.
4. **Digests are integrity, not authorship.** A producer can recompute `bundle_digest` after changing the content. `check_bundle` catches modification after the fact. Use signed tags or an external transparency log if you need authenticity.
5. **Probe design.** A probe that reads the clock, a random source, or a live service produces `UNKNOWN` or a false `UNEXPECTED`. Declare `nondeterminism` and keep probes deterministic.

## Out of scope

Cryptographic signing, hardware isolation, multi-tenant sandboxing, and Windows process-group semantics. The runner is tested on Linux. macOS uses the same `os.killpg` path. Windows needs a Job Object implementation before this tool should verify untrusted Windows bundles.
