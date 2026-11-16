# Review round 05: Filesystem, special files and resource limits

Owner: A5 (QA lead). Manager: coordinating agent. Date: 2026-11-11.

## Scope

Symlinks, escaping symlinks, FIFOs, subject size, workdir cleanup, odd file names.

## Commands executed

```console
$ python3 reviews/run_rounds.py before
round 05: 4 passed, 2 failed
$ python3 reviews/run_rounds.py after
round 05: 6 passed, 0 failed
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
```

Elapsed: 0.52s before, 0.7s after.
Logs: `reviews/logs/round-05-before.json`, `reviews/logs/round-05-after.json`.

## Baseline checks

| Check | Status | Detail |
|---|---|---|
| symlink inside subject refused | PASS | raised PolicyError |
| symlink escaping subject refused | PASS | raised PolicyError |
| FIFO / non-regular file refused | FAIL | AssertionError: unexpected error: eturn _copytree(entries=entries, src=src, dst=dst, symlinks=symlinks,   File "/usr/lib/python3.10/shutil.py", line 513, in _copytree     raise Error(errors) shutil.Error: [('/tmp/seal-te |
| subject size cap enforced | FAIL | ManifestError: manifest.policy has unknown keys |
| temporary workdirs cleaned up | PASS | no leftovers |
| odd file names captured | PASS | captured |

## Findings and required rework

### F-05-1 (Program defect, unsafe)

**Location:** `src/seal/runner.py:copytree`

**Problem:** A FIFO in the subject tree reached shutil.copytree and raised an opaque shutil.Error. A device node could hang the runner while reading bytes.

**Required fix:** Add _validate_subject_tree: reject symlinks and every non-regular file before any copy or read.

### F-05-2 (Program defect, unsafe)

**Location:** `src/seal/manifest.py:POLICY_KEYS`

**Problem:** No bound existed on the subject tree size. A multi-gigabyte subject could exhaust disk during the copy.

**Required fix:** Add policy.max_subject_bytes (default 64 MiB, bound 1 KiB to 512 MiB) and sum st_size during validation.

## Fixes applied

- src/seal/runner.py:_validate_subject_tree added
- src/seal/manifest.py:max_subject_bytes validated and merged
- re-ran the round: 6/6 PASS

## Final checks

| Check | Status | Detail |
|---|---|---|
| symlink inside subject refused | PASS | raised PolicyError |
| symlink escaping subject refused | PASS | raised PolicyError |
| FIFO / non-regular file refused | PASS | non-regular file refused promptly |
| subject size cap enforced | PASS | raised PolicyError |
| temporary workdirs cleaned up | PASS | no leftovers |
| odd file names captured | PASS | captured |

## Manager verdict

ACCEPTED AFTER REWORK. 0 failing checks remain. The re-run command and its exit code are recorded above. The behaviour-lock hash is unchanged, so no fix altered a program function.
