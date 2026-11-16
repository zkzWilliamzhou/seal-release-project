# Review round 02: Boundary conditions and input validation

Owner: A5 (QA lead). Manager: coordinating agent. Date: 2026-11-11.

## Scope

Manifest bounds, unknown keys, duplicate probes, NUL bytes, allowlist shape, malformed tags and missing files.

## Commands executed

```console
$ python3 reviews/run_rounds.py before
round 02: 16 passed, 2 failed
$ python3 reviews/run_rounds.py after
round 02: 18 passed, 0 failed
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
```

Elapsed: 0.01s before, 0.01s after.
Logs: `reviews/logs/round-02-before.json`, `reviews/logs/round-02-after.json`.

## Baseline checks

| Check | Status | Detail |
|---|---|---|
| reject: timeout zero | PASS | raised ManifestError |
| reject: timeout bool | PASS | raised ManifestError |
| reject: timeout 301 | PASS | raised ManifestError |
| reject: timeout string | PASS | raised ManifestError |
| reject: cap zero | PASS | raised ManifestError |
| reject: cap bool | PASS | raised ManifestError |
| reject: cap too large | PASS | raised ManifestError |
| reject: empty command | FAIL | AssertionError: expected an exception, none raised |
| reject: nul in arg | PASS | raised ManifestError |
| reject: duplicate probes | PASS | raised ManifestError |
| reject: bad scope | PASS | raised ManifestError |
| reject: bad nondeterminism | PASS | raised ManifestError |
| reject: empty allowlist | FAIL | AssertionError: expected an exception, none raised |
| reject: path in allowlist | PASS | raised ManifestError |
| reject unknown normalization key | PASS | raised ManifestError |
| reject env key containing '=' | PASS | raised ManifestError |
| missing manifest gives clean error | PASS | ok |
| path-traversal tags refused | PASS | 5 tags refused |

## Findings and required rework

### H-02-1 (Harness defect)

**Location:** `tests/_support.py:manifest_dict`

**Problem:** `command or [...]` replaced an intentionally empty command list with the default, so the empty-command rejection check never reached validate().

**Required fix:** Use `if command is None` instead of `or`.

### H-02-2 (Harness defect)

**Location:** `tests/_support.py:manifest_dict`

**Problem:** `allowed or ["python3"]` replaced an empty allowlist with the default, hiding the second rejection check.

**Required fix:** Use `if allowed is None` instead of `or`.

## Fixes applied

- tests/_support.py fixed both fallbacks
- manifest.py validate() already enforced both rules; no production change needed
- re-ran the round: 18/18 PASS

## Final checks

| Check | Status | Detail |
|---|---|---|
| reject: timeout zero | PASS | raised ManifestError |
| reject: timeout bool | PASS | raised ManifestError |
| reject: timeout 301 | PASS | raised ManifestError |
| reject: timeout string | PASS | raised ManifestError |
| reject: cap zero | PASS | raised ManifestError |
| reject: cap bool | PASS | raised ManifestError |
| reject: cap too large | PASS | raised ManifestError |
| reject: empty command | PASS | raised ManifestError |
| reject: nul in arg | PASS | raised ManifestError |
| reject: duplicate probes | PASS | raised ManifestError |
| reject: bad scope | PASS | raised ManifestError |
| reject: bad nondeterminism | PASS | raised ManifestError |
| reject: empty allowlist | PASS | raised ManifestError |
| reject: path in allowlist | PASS | raised ManifestError |
| reject unknown normalization key | PASS | raised ManifestError |
| reject env key containing '=' | PASS | raised ManifestError |
| missing manifest gives clean error | PASS | ok |
| path-traversal tags refused | PASS | 5 tags refused |

## Manager verdict

ACCEPTED AFTER REWORK. 0 failing checks remain. The re-run command and its exit code are recorded above. The behaviour-lock hash is unchanged, so no fix altered a program function.
