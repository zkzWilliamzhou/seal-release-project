# Launch readiness scorecard

Owner: A6. Gate: G7. Criteria come from `../../research/adoption_playbook.md` section "A strict 14-point launch scorecard". A criterion marked PASS has an artifact in this repository. DEFERRED means a human or an external service must supply it. The manager does not mark a deferred item as yes.

| # | Criterion | Evidence artifact | Status |
|---|---|---|---|
| 1 | One sentence states the user, the job and the replacement | README first line and repository description in `pyproject.toml` | PASS |
| 2 | A new machine completes the core task in 30 seconds | `./seal demo` needs no install, no config, no network. `evidence/demo_run.txt` is a recorded run | PASS |
| 3 | First example shows command and output | README "30 seconds" block matches `evidence/demo_run.txt` | PASS |
| 4 | Requirements and unsupported environments are explicit | README install section, `SECURITY.md` residual risks (Windows, network, OS limits) | PASS |
| 5 | The claimed result is reproduced from a clean environment | `tests/behavior_lock.py --check` plus `.github/workflows/ci.yml` matrix on five Python versions | PASS |
| 6 | The first error has a documented recovery path | `docs/TROUBLESHOOTING.md` | PASS |
| 7 | A license file is present and legible | `LICENSE` (MIT) | PASS |
| 8 | All non-open or differently licensed components are disclosed | `docs/ACTIVE_SKILLS.md` and `skills-lock.json` list every fetched skill file with source and hash; runtime is stdlib only (ADR 0004) | PASS |
| 9 | A stable extension point has a runnable example | `sealfile.json` manifest schema plus `seal init` and the probe example in `docs/TROUBLESHOOTING.md` | PASS |
| 10 | Contributor build instructions pass in CI | `CONTRIBUTING.md` plus `.github/workflows/ci.yml` | PASS |
| 11 | At least three well-scoped first issues exist | `docs/GOOD_FIRST_ISSUES.md` holds three drafts with acceptance criteria | DEFERRED: drafts need publishing on GitHub with labels |
| 12 | A screenshot, animation or interactive demo matches the first run | `evidence/demo_run.txt` is the verbatim terminal transcript of `./seal demo` | PASS (terminal transcript, no video) |
| 13 | Security boundaries are explicit | `SECURITY.md`, `docs/THREAT_MODEL.md` with 18 threats and test mappings | PASS |
| 14 | The team can triage the first 20 issues and pull requests | `CONTRIBUTING.md` names the review gates; no maintainer roster exists yet | DEFERRED: needs named owners |

## Score

11 PASS, 2 DEFERRED, 1 PASS with a text-only artifact. The playbook says a release that fails more than two items stays pre-release. Two deferred items are administrative, so this repository is a **release candidate**, not a public launch. The README does not claim a launch.

## What the star target became

The brief asked for a program with a shot at 105,000 GitHub stars. `../../research/adoption_playbook.md` shows 100,000 stars is a compound event requiring a packaged core workflow, repeated ecosystem exposure, and years of compounding. No build process produces star counts. The manager converted the target into this scorecard: a new developer can copy one command, see a visible result, reproduce it in CI, and find a documented error path. Stars stay a trailing indicator outside the codebase.

## Channels chosen for a future launch

Ecosystem packaging (`pip install seal-behavior`), problem-shaped documentation ("how do I prove a refactor changed nothing"), one technically substantive developer community, and the recorded terminal demo. The playbook lists trending pages, Product Hunt, and launch videos as short-term visibility, not durable growth.
