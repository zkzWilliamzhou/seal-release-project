# Review round 03: Command execution and sandbox escape

Owner: A5 (QA lead). Manager: coordinating agent. Date: 2026-11-11.

## Scope

Disallowed executables, absolute and parent paths, shell metacharacters, static shell scan, executable origin, process-group cleanup.

## Commands executed

```console
$ python3 reviews/run_rounds.py before
round 03: 5 passed, 2 failed
$ python3 reviews/run_rounds.py after
round 03: 7 passed, 0 failed
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
```

Elapsed: 1.93s before, 1.94s after.
Logs: `reviews/logs/round-03-before.json`, `reviews/logs/round-03-after.json`.

## Baseline checks

| Check | Status | Detail |
|---|---|---|
| disallowed executable refused | PASS | raised PolicyError |
| absolute executable outside subject refused | PASS | raised PolicyError |
| parent-directory executable refused | PASS | raised PolicyError |
| shell metacharacters stay literal | PASS | argv literal, no shell |
| static scan: no shell execution | PASS | ok |
| subject executable runs from workdir copy | FAIL | AssertionError: executable ran outside the copied workdir: '' |
| timeout kills the whole process group | FAIL | AssertionError: grandchild survived the timeout and wrote outside the sandbox |

## Findings and required rework

### F-03-1 (Program defect, unsafe)

**Location:** `src/seal/runner.py:run_probe`

**Problem:** A subject-relative executable such as `./main.py` was resolved to an absolute path in the ORIGINAL subject tree. The probe ran outside the copied workdir and could read or write the original files.

**Required fix:** _check_command now returns the subject-relative path. run_probe remaps argv[0] to `workdir / rel` before Popen.

### F-03-2 (Program defect, unsafe)

**Location:** `src/seal/runner.py:_run_argv`

**Problem:** subprocess.run killed only the direct child on timeout. A grandchild survived and wrote to a path outside the sandbox after the record returned.

**Required fix:** Use Popen(start_new_session=True) and os.killpg(proc.pid, SIGKILL) on TimeoutExpired, then drain pipes with a bounded communicate().

## Fixes applied

- src/seal/runner.py rewritten with both fixes
- round 3 checks: disallowed exe, absolute exe, parent exe, literal argv, static shell scan, workdir remap, group kill
- re-ran the round: 7/7 PASS

## Final checks

| Check | Status | Detail |
|---|---|---|
| disallowed executable refused | PASS | raised PolicyError |
| absolute executable outside subject refused | PASS | raised PolicyError |
| parent-directory executable refused | PASS | raised PolicyError |
| shell metacharacters stay literal | PASS | argv literal, no shell |
| static scan: no shell execution | PASS | ok |
| subject executable runs from workdir copy | PASS | path normalized to <WORKDIR> |
| timeout kills the whole process group | PASS | process group terminated |

## Manager verdict

ACCEPTED AFTER REWORK. 0 failing checks remain. The re-run command and its exit code are recorded above. The behaviour-lock hash is unchanged, so no fix altered a program function.
