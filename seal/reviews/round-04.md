# Review round 04: Secrets, environment and output handling

Owner: A5 (QA lead). Manager: coordinating agent. Date: 2026-11-11.

## Scope

Probe secrets, host secrets, reserved environment keys, env names only, stderr cap, invalid UTF-8.

## Commands executed

```console
$ python3 reviews/run_rounds.py before
round 04: 5 passed, 1 failed
$ python3 reviews/run_rounds.py after
round 04: 6 passed, 0 failed
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
```

Elapsed: 0.07s before, 0.08s after.
Logs: `reviews/logs/round-04-before.json`, `reviews/logs/round-04-after.json`.

## Baseline checks

| Check | Status | Detail |
|---|---|---|
| probe secret is redacted | PASS | secret value absent |
| host secret is redacted | PASS | host secret value absent |
| reserved environment keys refused | FAIL | AssertionError: expected an exception, none raised |
| only env names recorded | PASS | names only |
| stderr output cap enforced | PASS | capped at 256 |
| invalid UTF-8 does not crash | PASS | replacement decoding |

## Findings and required rework

### F-04-1 (Program defect, unsafe)

**Location:** `src/seal/manifest.py:validate`

**Problem:** probe.env accepted LD_PRELOAD, PYTHONPATH, PATH, HOME, BASH_ENV, LD_LIBRARY_PATH, IFS and PYTHONSTARTUP. A malicious bundle could redirect execution or move writes outside the workdir.

**Required fix:** Add RESERVED_ENV_KEYS and reject any reserved key during manifest validation. Eight keys are checked by the round.

## Fixes applied

- src/seal/manifest.py:RESERVED_ENV_KEYS added and enforced
- src/seal/runner.py keeps PATH, HOME, LANG, LC_ALL, TZ, PYTHONHASHSEED fixed
- re-ran the round: 6/6 PASS

## Final checks

| Check | Status | Detail |
|---|---|---|
| probe secret is redacted | PASS | secret value absent |
| host secret is redacted | PASS | host secret value absent |
| reserved environment keys refused | PASS | 8 reserved keys refused |
| only env names recorded | PASS | names only |
| stderr output cap enforced | PASS | capped at 256 |
| invalid UTF-8 does not crash | PASS | replacement decoding |

## Manager verdict

ACCEPTED AFTER REWORK. 0 failing checks remain. The re-run command and its exit code are recorded above. The behaviour-lock hash is unchanged, so no fix altered a program function.
