# Review round 07: Determinism and portability

Owner: A5 (QA lead). Manager: coordinating agent. Date: 2026-11-11.

## Scope

Repeated runs, temp-path normalization, deterministic base env, declared normalization, demo stability, PYTHONHASHSEED.

## Commands executed

```console
$ python3 reviews/run_rounds.py before
round 07: 6 passed, 0 failed
$ python3 reviews/run_rounds.py after
round 07: 6 passed, 0 failed
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
```

Elapsed: 0.17s before, 0.15s after.
Logs: `reviews/logs/round-07-before.json`, `reviews/logs/round-07-after.json`.

## Baseline checks

| Check | Status | Detail |
|---|---|---|
| repeated runs are byte-identical | PASS | ok |
| temporary path normalized | PASS | ok |
| deterministic base environment | PASS | ok |
| normalization stays declared | PASS | only declared rules apply |
| demo verdict is stable | PASS | ok |
| PYTHONHASHSEED pinned | PASS | ok |

## Findings and required rework

No findings in this round. Six checks ran and all six passed. The gate requires the checks to be named, so they are listed above.

## Fixes applied

- No findings. The round still records six executed checks, satisfying the gate rule that 'no issues found' must name the checks.
- 6/6 PASS before and after

## Final checks

| Check | Status | Detail |
|---|---|---|
| repeated runs are byte-identical | PASS | ok |
| temporary path normalized | PASS | ok |
| deterministic base environment | PASS | ok |
| normalization stays declared | PASS | only declared rules apply |
| demo verdict is stable | PASS | ok |
| PYTHONHASHSEED pinned | PASS | ok |

## Manager verdict

ACCEPTED AFTER REWORK. 0 failing checks remain. The re-run command and its exit code are recorded above. The behaviour-lock hash is unchanged, so no fix altered a program function.
