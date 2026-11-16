# Delivery manifest

Date: 2026-11-11 (Asia/Shanghai)
Archive: `seal-release.zip`

## What is in this archive

| Path | Contents |
|---|---|
| `seal/` | The complete `seal` project: source, tests, docs, eight review reports, CI, skills, evidence |
| `research/` | `opensource_gap_research.md`, `adoption_playbook.md`, and the figure used by the latter |
| `architecture-review.html` | Self-contained HTML candidate report from the `improve-codebase-architecture` pass |
| `tools/` | The GitHub skills installer, the link-driven finisher, and its detached launcher |
| `skill_install_final.log` | Final skills-install log |
| `FINAL_VALIDATION.txt` | Commands, exit codes, and custom checks from the final validation run |
| `CHECKSUMS.sha256` | SHA-256 for every file in this archive except itself |
| `DELIVERY_MANIFEST.md` | This file |

## Skills installed from GitHub

621 real files from five public repositories. Counts by vendor: anthropics=368, mattpocock=138, stop-slop=7, superpowers=99, vercel-labs=9. Direct GitHub returned HTTP 403 in the build sandbox, so the installer used the jsDelivr GitHub mirror. A full directory crawl hit a sandbox timeout; discovery finished from cached bytes plus relative Markdown link resolution. Every installed file has a source URL and SHA-256 in `seal/skills-lock.json`. `seal/docs/SKILL_INSTALL_REPORT.md` lists every file and records the method. No skill file was authored by hand. Upstream skill Markdown may link to companion files that are not installed; those links sit in `.agents/skills/` and are excluded from the project link check.

## Verification summary

- 36 unit tests pass.
- Eight executable review rounds pass 62/62 checks. Baseline was 50/62. Twelve failures were fixed and re-run.
- `python3 tests/behavior_lock.py --check` prints `BEHAVIOUR LOCKED (826e21e888501b19)`. The architecture pass changed zero observable functions.
- `./seal demo` catches a hidden file-creation side effect that a stdout assertion misses.
- `FINAL_VALIDATION.txt` holds the exact commands and outputs.

## Path conventions

Paths written as `docs/foo.md` inside project documentation are relative to the `seal/` repository root. Paths written `../../research/...` from `seal/docs/` point to the archive root. The HTML architecture report is `../../architecture-review.html` from `seal/docs/`.

## Honest limits

1. The brief asked for a shot at 105,000 GitHub stars. No build process produces star counts. `seal/docs/06_launch_scorecard.md` converts the target into 14 checkable release criteria: 11 pass, 2 need a human, 1 passes with a terminal transcript. This is a release candidate.
2. The novelty claim in `seal/docs/07_prior_art.md` is conditional and dated. Six search channels cannot prove the absence of private or unindexed implementations.
3. Bundle digests detect modification, not forgery. Network isolation and Windows process-group safety remain operator and platform responsibilities. See `seal/SECURITY.md`.
4. Two administrative scorecard items need named maintainers and published GitHub issues.

## Quick start

```console
$ cd seal
$ ./seal demo
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests -v
$ python3 reviews/run_rounds.py final
$ python3 tests/behavior_lock.py --check
```

`seal/README.md` is the first file a reviewer should open.
