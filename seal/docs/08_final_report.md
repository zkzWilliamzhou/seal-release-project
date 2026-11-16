# Final report

Date: 2026-11-11. Manager: coordinating agent.

## What shipped

A zero-dependency Python CLI named `seal`. It runs declared probes against two versions of any executable, captures six observation channels, classifies each difference against an intent scope declared before recording, and writes a self-contained evidence bundle that a third party re-executes in a clean sandbox.

```console
$ ./seal demo
...
UNEXPECTED files_delta (difference outside declared intent scope)
verdict: UNEXPECTED
```

`evidence/demo_run.txt` holds the verbatim run. `./seal demo` needs no install, no config and no network.

## What the brief produced, item by item

| Request | Result |
|---|---|
| Install anthropics, mattpocock, vercel-labs, stop-slop, brainstorming and superpowers skills from GitHub | 621 real files from five repositories, each with a source URL and SHA-256 in `skills-lock.json`. Direct GitHub returned 403, so the installer used the jsDelivr GitHub mirror, then finished discovery from cached bytes plus two passes of relative Markdown link resolution after a sandbox timeout. `docs/SKILL_INSTALL_REPORT.md` lists every file. |
| Brainstorm, deep-think and grill yourself | `docs/00_brainstorming_and_grilling.md`: ten candidates, nine killed, 18 answered grill questions, a hard design gate, and four design changes recorded before implementation. |
| A program with a function that does not exist yet and can make a difference | `docs/07_prior_art.md` states a conditional mechanism-level novelty claim with six search channels and ten nearest neighbours. The difference it targets: review cost rose while patch production cost fell. |
| 105,000 GitHub stars | Not delivered, and no build process can deliver it. `docs/06_launch_scorecard.md` converts the target into 14 checkable release criteria. 11 pass, 2 need a human, 1 passes with a terminal transcript. The repository is a release candidate. |
| Organize a workflow and specialized agents | `docs/02_workflow.md` (G0 to G7), `docs/03_agent_charters.md` (six owners plus manager, five recorded rejections). |
| Install the skills you believe useful in the program | `docs/ACTIVE_SKILLS.md` binds 15 skills to gates and explains why the rest stay available but unbound. |
| Work until done, with a strict manager | `reviews/run_rounds.py` runs 62 executable checks. Baseline 50/62. Twelve failures. All twelve fixed and re-run to 62/62. Eight round reports with before/after logs. |
| Examine over 8 rounds for bugs and unsafe parts | Eight rounds, scopes listed in `docs/04_review_summary.md`. Five unsafe defects and one false-clean defect fixed: workdir remap, process-group kill, reserved env keys, special files, subject size, empty-probe false CLEAN. `docs/THREAT_MODEL.md` maps 18 threats to tests and names three residual risks. |
| Use improve-codebase-architecture, changing zero functions | `docs/05_architecture_refactor.md` and ADR 0005. Behaviour-lock hash `826e21e888501b19` before and after. 36 tests and 62 review checks unchanged. HTML candidate report at `../../architecture-review.html`. |

## Verification commands

```console
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests -v
Ran 36 tests ... OK
$ python3 reviews/run_rounds.py after
TOTAL: 62/62 checks passed
$ python3 reviews/run_rounds.py final
TOTAL: 62/62 checks passed
$ python3 tests/behavior_lock.py --check
BEHAVIOUR LOCKED (826e21e888501b19)
$ ./seal demo --json
```

## What I am refusing to claim

1. **105,000 stars.** Stars are an external, delayed outcome. The brief asked for a shot at them. The scorecard is the shot.
2. **Absolute novelty.** Six channels cannot prove the absence of private or unindexed implementations. The claim is conditional and dated.
3. **Cryptographic authorship.** Bundle digests detect modification, not forgery. `SECURITY.md` says so.
4. **Network isolation.** `policy.allow_network` is a declaration. The operator must isolate the network.
5. **Windows process-group safety.** Tested on Linux and macOS paths. Windows needs a Job Object implementation.
6. **A public launch.** Two administrative scorecard items need named maintainers and published issues.

## Files a reviewer should open first

1. `README.md`
2. `docs/07_prior_art.md`
3. `docs/04_review_summary.md`
4. `docs/05_architecture_refactor.md`
5. `docs/THREAT_MODEL.md`
6. `docs/06_launch_scorecard.md`
