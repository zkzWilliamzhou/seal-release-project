# Skills installed and bound to this program

## Installation facts

`skills-lock.json` records 621 files fetched byte-for-byte from five public GitHub repositories through the jsDelivr GitHub mirror on 2026-11-11. Direct GitHub access returned HTTP 403 in the build sandbox, so the installer used CDN directory listings and two passes of relative Markdown link resolution. Every installed file has a source URL and SHA-256. `docs/SKILL_INSTALL_REPORT.md` lists every file. No skill file was authored by hand. The first full directory crawl hit a sandbox timeout, so a companion file that no installed Markdown links to may be absent; `skills-lock.json` records the discovery method and any unresolved link target.

| Repository | Files | Role here |
|---|---|---|
| `anthropics/skills` | 368 | SKILL.md format reference, skill-creator, document skills |
| `mattpocock/skills` | 138 | grilling, architecture deepening, TDD, review, diagnosis |
| `obra/superpowers` | 99 | brainstorming, plans, TDD, debugging, review, verification |
| `vercel-labs/skills` | 9 | the `npx skills` CLI reference (`skills/find-skills`) |
| `hardikpandya/stop-slop` | 7 | prose quality gate for README and launch copy |

`vercel-labs/skills` contributes 9 files from its `skills/find-skills/` tree and root metadata. The install report records every resolved link target; none failed to fetch.

## Skills bound to the workflow

| Skill | Used at | What it enforced |
|---|---|---|
| `superpowers/brainstorming` | G1 | Design before code. Hard gate at `docs/00_brainstorming_and_grilling.md` section 6. |
| `mattpocock/grill-me` | G1 | 18 adversarial questions before approval. |
| `superpowers/writing-plans` | G2 | Module table, command contracts, test plan in `docs/01_plan.md`. |
| `mattpocock/zoom-out` | G2 | Cut the plugin, dashboard and cloud service from the MVP. |
| `superpowers/test-driven-development`, `mattpocock/tdd` | G3 | Tests in `tests/` precede implementation acceptance. |
| `superpowers/verification-before-completion` | G3, G7 | No "done" without a command and an exit code. |
| `superpowers/defense-in-depth` | G4 | Multiple validation layers in `bundle.check_bundle`. |
| `mattpocock/diagnosing-bugs` | G4, G5 | Root cause before each fix in the review rounds. |
| `superpowers/systematic-debugging` | G5 | Reproduce, isolate, fix, verify. Eight rounds in `reviews/`. |
| `superpowers/requesting-code-review`, `receiving-code-review`, `mattpocock/code-review` | G5 | Findings name a file, a line and a failing check. |
| `mattpocock/improve-codebase-architecture` | G6 | Vocabulary from `GLOSSARY.md`, deletion test, deepening opportunities in `docs/05_architecture_refactor.md`. |
| `stop-slop/stop-slop` | G7 | Eight prose rules applied to README. Round 8 checks em dashes, binary contrasts and vague claims. |
| `anthropics/skill-creator` | format reference | SKILL.md frontmatter shape for any future project skill. |
| `vercel-labs/find-skills` | G7 | Discovery reference for the skills ecosystem. |

## Skills installed but not bound

The remaining installed skills cover document generation (docx, pdf, pptx, xlsx), visual design, internal communications, TypeScript workflows, git worktrees, and agent meta-skills. This program ships a CLI and a README. Loading those skills would add process without adding a deliverable. They stay available in `.agents/skills/` for future work.

## Skills I would add for a v2

A real `SKILL.md` inside this repository so agents can invoke `seal` from their own workflow, written with `anthropics/skill-creator`. It is out of scope for day one because the release gate needs one command, not an integration surface.
