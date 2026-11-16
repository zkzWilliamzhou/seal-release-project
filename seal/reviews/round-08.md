# Review round 08: End-to-end pipeline and release artifacts

Owner: A5 (QA lead). Manager: coordinating agent. Date: 2026-11-11.

## Scope

Full CLI pipeline, module and launcher entry points, stdlib-only scan, release documents, prose gate, star-count promise.

## Commands executed

```console
$ python3 reviews/run_rounds.py before
round 08: 4 passed, 3 failed
$ python3 reviews/run_rounds.py after
round 08: 7 passed, 0 failed
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
```

Elapsed: 1.65s before, 1.0s after.
Logs: `reviews/logs/round-08-before.json`, `reviews/logs/round-08-after.json`.

## Baseline checks

| Check | Status | Detail |
|---|---|---|
| full CLI pipeline | PASS | record/compare/bundle/verify all correct |
| python -m seal works | PASS | ok |
| ./seal launcher works | PASS | ok |
| runtime has zero third-party imports | PASS | ok |
| release documents exist | FAIL | AssertionError: missing: ['README.md', 'CONTRIBUTING.md', 'SECURITY.md', 'GLOSSARY.md', 'docs/THREAT_MODEL.md', 'docs/06_launch_scorecard.md', 'docs/05_architecture_refactor.md', 'docs/07_prior_art.md', '.github/workflow |
| README passes prose gate | FAIL | FileNotFoundError: [Errno 2] No such file or directory: '/data/workspace/seal/README.md' |
| no star-count promise | FAIL | FileNotFoundError: [Errno 2] No such file or directory: '/data/workspace/seal/README.md' |

## Findings and required rework

### F-08-1 (Release defect)

**Location:** `repository root`

**Problem:** README.md, CONTRIBUTING.md, SECURITY.md, GLOSSARY.md, the threat model, the scorecard, prior art, the architecture report and CI were missing.

**Required fix:** Write all nine artifacts plus troubleshooting, good-first-issue drafts and the demo transcript.

### F-08-2 (Release defect)

**Location:** `README.md`

**Problem:** The stop-slop prose gate could not run. No text existed to check for em dashes, binary contrasts, vague declaratives or absolute novelty claims.

**Required fix:** Write README.md with concrete commands and outputs. The gate checks three pattern classes.

### F-08-3 (Release defect)

**Location:** `README.md`

**Problem:** The no-star-promise check could not run.

**Required fix:** README.md states that adoption sits outside the codebase. The scorecard records why the 105,000-star target became 14 checkable criteria.

## Fixes applied

- 12 release artifacts added
- .github/workflows/ci.yml runs unit suite, eight rounds and behaviour lock on five Python versions
- re-ran the round: 7/7 PASS

## Final checks

| Check | Status | Detail |
|---|---|---|
| full CLI pipeline | PASS | record/compare/bundle/verify all correct |
| python -m seal works | PASS | ok |
| ./seal launcher works | PASS | ok |
| runtime has zero third-party imports | PASS | ok |
| release documents exist | PASS | ok |
| README passes prose gate | PASS | ok |
| no star-count promise | PASS | ok |

## Manager verdict

ACCEPTED AFTER REWORK. 0 failing checks remain. The re-run command and its exit code are recorded above. The behaviour-lock hash is unchanged, so no fix altered a program function.
