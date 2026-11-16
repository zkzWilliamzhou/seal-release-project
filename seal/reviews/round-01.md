# Review round 01: Correctness and public contracts

Owner: A5 (QA lead). Manager: coordinating agent. Date: 2026-11-11.

## Scope

Unit suite, CLI version output, demo, digest stability, clean and unexpected verdicts.

## Commands executed

```console
$ python3 reviews/run_rounds.py before
round 01: 5 passed, 1 failed
$ python3 reviews/run_rounds.py after
round 01: 6 passed, 0 failed
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
```

Elapsed: 1.98s before, 1.63s after.
Logs: `reviews/logs/round-01-before.json`, `reviews/logs/round-01-after.json`.

## Baseline checks

| Check | Status | Detail |
|---|---|---|
| unit suite passes | FAIL | IndexError: list index out of range |
| --version is stable | PASS | ok |
| demo detects hidden change | PASS | ok |
| identical subjects give CLEAN | PASS | ok |
| stdout change gives UNEXPECTED | PASS | ok |
| digest ignores key order | PASS | ok |

## Findings and required rework

### H-01-1 (Harness defect)

**Location:** `reviews/run_rounds.py:unit`

**Problem:** The harness read the unittest summary from stdout. unittest writes its summary to stderr, so `splitlines()[-2]` raised IndexError while the suite was actually green.

**Required fix:** Read the 'Ran N tests' line from p.stderr. No production code changed.

## Fixes applied

- reviews/run_rounds.py:unit reads stderr
- re-ran the round: 6/6 PASS

## Final checks

| Check | Status | Detail |
|---|---|---|
| unit suite passes | PASS | Ran 36 tests in 0.881s |
| --version is stable | PASS | ok |
| demo detects hidden change | PASS | ok |
| identical subjects give CLEAN | PASS | ok |
| stdout change gives UNEXPECTED | PASS | ok |
| digest ignores key order | PASS | ok |

## Manager verdict

ACCEPTED AFTER REWORK. 0 failing checks remain. The re-run command and its exit code are recorded above. The behaviour-lock hash is unchanged, so no fix altered a program function.
