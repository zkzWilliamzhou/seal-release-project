# Agent Charters and Rejection Log

Six specialist agents own one stage each. The manager owns acceptance. A charter is a contract: it states what the agent may decide, what it must produce, and the exact conditions under which the manager sends the work back.

## A1 Prior-art analyst

**Mission:** Attack the novelty claim before code exists.
**Inputs:** the approved design, six search channels, the two research reports.
**Outputs:** `docs/07_prior_art.md`, a nearest-neighbour matrix, a conditional novelty statement.
**Definition of done:** each channel has recorded queries and results, each nearest neighbour has a source URL, and the differentiation is stated at mechanism level.
**Reject when:** a claim of absolute novelty, a missing source, or an unexamined package registry.

## A2 Product architect

**Mission:** Turn the approved design into module boundaries and CLI contracts.
**Inputs:** design doc, prior-art doc, adoption playbook.
**Outputs:** `docs/01_plan.md`, `docs/adr/0001-*.md` through `0004-*.md`, `docs/02_workflow.md`.
**Definition of done:** each module has one responsibility, each CLI command has an input, an output, an exit code, and a failure mode, and every non-goal from the design appears in the plan.
**Reject when:** a module owns two concerns, a command has no failure mode, or scope grew beyond the gate.

## A3 Core engineer

**Mission:** Implement the CLI test-first.
**Inputs:** plan, ADRs, workflow.
**Outputs:** `src/seal/**`, `tests/**`, `evidence/baseline/**`, `pyproject.toml`.
**Definition of done:** all tests pass, every command has a fixture, imports stay inside the Python standard library, and `seal demo` completes.
**Reject when:** a test mirrors implementation details, a dependency appears, or a command returns a code the plan did not specify.

## A4 Security auditor

**Mission:** Assume the tool is an attack surface.
**Inputs:** implementation, threat scenarios.
**Outputs:** `docs/THREAT_MODEL.md`, security tests.
**Definition of done:** every threat has a mitigation, a test name, and a recorded pass.
**Reject when:** a mitigation has no test, or the default policy executes commands from an untrusted bundle.

## A5 QA lead

**Mission:** Run eight review rounds with different scopes.
**Inputs:** implementation, tests, threat model.
**Outputs:** `reviews/round-01.md` through `round-08.md`, fixes, re-run logs.
**Definition of done:** each round lists checks executed, findings with file and line, fixes, and a re-run exit code.
**Reject when:** a round contains "looks fine" without a command, a fix has no regression test, or a round repeats the previous scope.

## A6 Release editor

**Mission:** Make the first run work for a stranger.
**Inputs:** everything above, adoption playbook, stop-slop rules.
**Outputs:** `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/06_launch_scorecard.md`, demo script.
**Definition of done:** 14 scorecard criteria each carry an artifact, prose passes the stop-slop checks, demo runs clean.
**Reject when:** a criterion is marked yes with no evidence, or prose contains AI filler, em dashes, or vague declaratives.

## Manager

The manager opens every artifact, checks it against the gate table, and records one of `ACCEPTED`, `REJECTED: <reason>`, or `ACCEPTED AFTER REWORK`. The manager does not write code on behalf of an owner. If an owner fails twice on the same item, the manager redesigns the component and reassigns it.

## Rejection log

This log is filled during execution. It records real findings, not staged ones.

| # | Date | Owner | Gate | Failing item | Reason | Rework required | Outcome |
|---|---|---|---|---|---|---|---|
| R1 | 2026-11-11 | A1 | G2 | Novelty claim | The first draft of the positioning said the function "does not exist anywhere". Six search channels cannot support an absolute claim. | Rewrite as a dated, conditional mechanism-level claim with a nearest-neighbour matrix in `docs/07_prior_art.md`. | ACCEPTED AFTER REWORK |
| R2 | 2026-11-11 | A3 | G3 | Safety policy | The first runner accepted `LD_PRELOAD` and `PYTHONPATH` from `probe.env`, resolved subject-relative executables against the original tree, and killed only the direct child on timeout. Rounds 3, 4 and 5 found all three. | Add `RESERVED_ENV_KEYS`, remap executables into the copied workdir, and kill the process group with `os.killpg`. | ACCEPTED AFTER REWORK |
| R3 | 2026-11-11 | A5 | G5 | Executable evidence | The first review plan described checks in prose. No command had been run, so the gate could not verify any finding. | Build `reviews/run_rounds.py` with eight rounds of executable checks and JSON logs. | ACCEPTED AFTER REWORK |
| R4 | 2026-11-11 | A6 | G7 | Release artifacts | The first G7 submission had no README, no license check in the harness, no CI, and no scorecard. Round 8 failed three checks. | Write README, CONTRIBUTING, SECURITY, GLOSSARY, THREAT_MODEL, scorecard, troubleshooting, CI and the demo transcript. | ACCEPTED AFTER REWORK |
| R5 | 2026-11-11 | A5 | G5 | Harness accuracy | Round 1 and two round-2 checks failed because the harness parsed unittest stdout (unittest writes to stderr) and used `or` fallbacks that swallowed empty fixtures. | Fix the harness, then re-run. These were harness defects, not program defects. The distinction is recorded in `reviews/round-01.md` and `round-02.md`. | ACCEPTED AFTER REWORK |

Additional rows are appended if further rejections occur during the eight rounds.

## What the manager will not accept

- A passing test suite presented as proof of novelty.
- A security section with no executable tests.
- A review round that found nothing and ran nothing.
- An architecture refactor that changed a verdict string, an exit code, or a bundle field.
- Any statement about achieved GitHub stars. Stars are external and cannot be produced by this pipeline.
