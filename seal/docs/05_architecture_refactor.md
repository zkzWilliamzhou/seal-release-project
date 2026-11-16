# Architecture deepening under a behaviour lock

Owner: A6 (architect). Gate: G6. Skill: `mattpocock/improve-codebase-architecture`, loaded from `.agents/skills/mattpocock/skills/engineering/improve-codebase-architecture/SKILL.md`.

## The constraint from the brief

Improve the codebase architecture. Change zero functions. The manager set a hard rule before touching a line: the behaviour-lock hash from `tests/behavior_lock.py` must be identical before and after, the 36-test unit suite must stay green, and all eight review rounds must keep their results. Any changed verdict string, exit code, or bundle field would reject the work.

## Step 1: scope, glossary, ADRs

The hot spot is the group of modules touched by every review round: `compare.py`, `cli.py`, `demo.py`, `bundle.py`. I read `GLOSSARY.md` and ADRs 0001 to 0004 first. None of them was reopened. Vocabulary used below: module, interface, depth, seam, adapter, leverage, locality, deletion test.

The self-contained HTML report sits at `../../architecture-review.html`. It holds three candidate cards with before/after diagrams and a top recommendation. Nothing landed in the repository from that report, matching the skill's process.

## Step 2: candidates and the deletion test

| Candidate | Verdict | Deletion test |
|---|---|---|
| C1 Concentrate presentation in one deep `render.py` module | Strong, accepted | Deleting `render_report` from `compare.py` and `render_demo` from `demo.py` concentrates all presentation complexity in one module. Passes. |
| C2 Extract JSON helpers from `cli.py` | Worth exploring, rejected | Deleting the three helpers only moves them. One adapter each, so the seam stays hypothetical. Fails. |
| C3 Split safety validation out of `runner.py` | Speculative, deferred | Two adapters exist, so the seam is real, but the code is what rounds 3, 4 and 5 hardened. Deferred to v2 with dedicated adversarial tests. |

## Step 3: grilling loop

The brief puts the manager in charge and asks for no pause, so the manager picked the report's top recommendation and recorded the decision tree:

1. **Constraint:** no observable behaviour change. C1 satisfies it with a pure move of text functions.
2. **Dependencies:** `cli.py`, `bundle.py`, `demo.py` import the renderers. Four import lines change.
3. **Shape of the deepened module:** one `render.py`, two functions, no state, no imports from `compare.py`. No cycle.
4. **What sits behind the seam:** a report dict and a demo result dict. Both shapes stay byte-identical.
5. **What tests survive:** all 36 unit tests, the behaviour lock, and the eight review rounds.
6. **New glossary term:** none. `GLOSSARY.md` already defines module, interface, depth, seam, adapter, leverage and locality.
7. **ADR conflict:** none. ADR 0001 fixes the verdict model, which C1 does not touch.

## Step 4: the change

| File | Before | After |
|---|---|---|
| `src/seal/render.py` | did not exist | owns `render_report` and `render_demo` |
| `src/seal/compare.py` | classification plus a 24-line renderer | classification only |
| `src/seal/demo.py` | fixture plus a renderer | fixture only, imports `render_report` |
| `src/seal/cli.py` | imported renderers from two modules | imports both from `render.py` |
| `src/seal/bundle.py` | imported `render_report` from `compare.py` | imports from `render.py` |

Zero lines of rendering logic changed. The functions were moved verbatim. No verdict constant, exit code, JSON key, digest computation, policy check, or CLI flag changed.

## Step 5: evidence

Commands run from the repository root:

```console
$ python3 tests/behavior_lock.py --write
wrote baseline /data/workspace/seal/evidence/baseline/behavior_lock.json (826e21e888501b19)
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests
Ran 36 tests ... OK
$ python3 reviews/run_rounds.py after
```

| Measurement | Before refactor | After refactor |
|---|---|---|
| Behaviour-lock transcript hash | `826e21e888501b19...` | `826e21e888501b19...` |
| CLI transcript entries | 10 | 10, byte-identical |
| Unit tests | 36 passed | 36 passed |
| Review checks | see `reviews/round-XX-after.json` | same results |
| Bundle schema fields | unchanged | unchanged |
| Exit codes | 0/1/2/3 | 0/1/2/3 |

The transcript covers `--version`, `init`, two `record` calls, three `compare` variants, `verify --trust`, `demo`, and `demo --json`. It normalizes only the temporary root path. Everything else, including manifest digests and report text, must match.

## Step 6: manager verdict

ACCEPTED. The refactor deepens `compare.py` (one interface, one job), gives the presentation concept one home with high leverage across three callers, and leaves the sealed surface untouched. C3 stays on the v2 list. Had the hash moved by one byte, the manager would have rejected the work and reverted the files.
