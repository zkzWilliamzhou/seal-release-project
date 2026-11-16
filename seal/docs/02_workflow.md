# Workflow and Quality Gates

The program is built as a staged pipeline. Each stage has one owner, a written charter, a fixed input, a fixed output, and an acceptance checklist. The manager rejects any output that fails a checklist item. Rejected work returns to the same owner with a written reason and a required rework scope. Nothing moves downstream on a verbal assurance.

## Pipeline

```
G0  Skill adoption         -> .agents/skills/**, skills-lock.json
        |
G1  Brainstorm + grill     -> docs/00_brainstorming_and_grilling.md  [HARD GATE]
        |
G2  Plan + prior art       -> docs/01_plan.md, docs/07_prior_art.md, docs/adr/**
        |
G3  TDD implementation     -> src/seal/**, tests/**, evidence/baseline/**
        |
G4  Threat model           -> docs/THREAT_MODEL.md
        |
G5  Eight review rounds    -> reviews/round-01.md ... round-08.md  [8 ROUNDS MINIMUM]
        |
G6  Architecture pass      -> docs/05_architecture_refactor.md + unchanged-proof  [BEHAVIOR LOCK]
        |
G7  Release gate           -> README.md, docs/06_launch_scorecard.md, demo recording
```

## Gate definitions

| Gate | Owner | Accept only when | Reject when |
|---|---|---|---|
| G0 | Platform agent | Every installed file has a source URL and SHA-256 in the lock. Zero fabricated files. | A file is missing and someone wrote a substitute by hand. |
| G1 | Product architect + manager | Design names the invariant, the mechanism, the non-goals, and the conditional novelty claim. Grill has at least 15 answered questions. Manager signed the hard gate. | Category-level novelty claim, or a promise about star counts. |
| G2 | Prior-art analyst + architect | Six prior-art channels recorded. Every module has one responsibility. Every command has a testable contract. | A module owns two unrelated concerns, or a prior-art claim has no source. |
| G3 | Core engineer | Tests written first, all tests pass, every CLI command has a fixture, no third-party imports. | A test asserts the implementation instead of the contract, or a dependency was added. |
| G4 | Security auditor | Threat model covers command execution, path traversal, symlinks, output bombs, secret leakage, timeouts, and tampering. Each threat has a mitigation and a test. | A threat is listed with no test. |
| G5 | QA lead | Eight rounds, each with a distinct scope, at least one executable check, findings with file and line, fixes, and a re-run that proves the fix. | A round says "no issues found" without naming the checks that ran. |
| G6 | Architect | A golden behaviour baseline exists before the refactor. The same probes produce byte-identical verdicts after it. Zero changes to the verdict model or safety policy. | Any CLI output, exit code, or bundle schema changes. |
| G7 | Release editor | All 14 scorecard criteria have public evidence. `seal demo` runs on a clean machine in under 30 seconds. Prose passes the stop-slop checks. | A criterion is marked yes without an artifact. |

## Manager rules

1. An owner submits an artifact, never a summary of work. The manager opens the artifact.
2. A rejection names the exact failing checklist item, the file, and the required rework.
3. Rework is re-reviewed against the same checklist plus the original failure. Two consecutive rejections on the same item escalate to a redesign of that component.
4. No agent declares its own work complete. `verification-before-completion` applies: evidence or it did not happen.
5. Faked output, invented evidence, or a claim without a reproducible run causes an immediate full rejection of that stage.
6. The manager keeps a rejection log with dates and outcomes. See `docs/03_agent_charters.md`.

## Skills bound to each gate

The installed skills are instructions, not decorations. Each gate names the skills its owner must follow.

| Gate | Bound skills |
|---|---|
| G1 | superpowers/brainstorming, mattpocock/grill-me |
| G2 | superpowers/writing-plans, anthropics/skill-creator (format reference), mattpocock/zoom-out |
| G3 | superpowers/test-driven-development, mattpocock/tdd, superpowers/verification-before-completion |
| G4 | superpowers/defense-in-depth, mattpocock/diagnose |
| G5 | superpowers/systematic-debugging, superpowers/requesting-code-review, superpowers/receiving-code-review, mattpocock/code-review |
| G6 | mattpocock/improve-codebase-architecture, superpowers/test-driven-development |
| G7 | stop-slop/stop-slop, superpowers/verification-before-completion, vercel-labs/find-skills |

`docs/ACTIVE_SKILLS.md` lists the ones selected as useful for this program and why the others were left available but unbound.

## Evidence discipline

Every claim in a report points at an artifact: a file, a command, a test name, or a recorded run. Round reports include the exact command and its exit code. The architecture pass includes a before and after verdict comparison produced by the program itself. This makes the project eat its own dog food: `seal` verifies that the `seal` refactor changed nothing.
