# Brainstorming and Self-Grilling Record

Date: 2026-11-11
Method: design-first brainstorming, followed by an adversarial grill of every idea, followed by a hard gate before implementation.
Manager: the coordinating agent. No implementation started before the design in section 5 was approved.

## 0. What the brief actually demands

1. A program whose function has no public implementation in the world.
2. A function that makes a real difference.
3. A credible shot at 105,000 GitHub stars.
4. A workflow with specialised agents and strict manager review.
5. Eight or more review rounds covering bugs and unsafe parts.
6. An architecture pass that changes zero observable behaviour.

Item 3 needs an early correction. Star counts are a delayed, external outcome. No engineering process can produce 105,000 stars. The `adoption_playbook.md` research says the same: 100,000 stars is a compound event requiring a packaged core workflow, repeated exposure, and years of compounding. I converted the star target into a checkable launch scorecard and kept star count as a trailing indicator. I will not claim the project reached 105,000 stars.

## 1. What the prior-art research changed

Two research reports were produced before any design work:

- `../../research/opensource_gap_research.md` examined ten daily pain points in the 2026 agent-tooling ecosystem. Every one has an adjacent open-source tool. AARC, CodeVetter, ScopeGate, MCP Guardrails Proxy, OrcaReplay, ctx, and skill validators already occupy the obvious categories.
- `research/adoption_playbook.md` examined what makes developer tools spread and produced a 14-point launch scorecard.

The first report forced a narrower rule. Novelty has to live at the level of a specific mechanism and a specific invariant. Category-level claims such as "the first AI code security tool" are false on arrival.

The surviving systemic gap is this: agent standards solve packaging and transport, while nothing gives a reviewer an independently reproducible answer to a question every developer asks after a patch lands.

> What did this change actually change, beyond the part I asked for?

Git shows edited lines. A test suite shows the assertions somebody already wrote. An agent shows a confident summary. None of them shows the full observable behaviour of the program before and after, verified by a third party who did not watch the edit happen.

## 2. Ten candidates and why nine died

| # | Candidate | Closest existing work | Kill question | Verdict |
|---|---|---|---|---|
| 1 | Another agent skill pack | anthropics/skills, mattpocock/skills, obra/superpowers | Which of these three does your pack replace? | Dead on arrival |
| 2 | MCP policy proxy | MCP Guardrails Proxy, mcp-warden, ScopeGate | What boundary do you enforce that they miss? | Dead |
| 3 | SKILL.md validator | public skill-validator projects | Can you enforce a contract across runtimes, or only lint prose? | Dead |
| 4 | AI patch provenance badge | AARC, CodeVetter, SLSA, git | Is a badge evidence or a claim? | Dead |
| 5 | Offline agent replay debugger | OrcaReplay | Can you reach byte-identical replay without the model vendor cooperating? | Dead for this MVP |
| 6 | AGENTS.md context checker | ctx, Serena memories, AGENTS.md | Can a textual checker distinguish a stale fact from a valid preference? | Too narrow |
| 7 | Semantic API version diff | cargo-semver-checks, japicmp, apidiff | Does an API diff see runtime behaviour at all? | Dead |
| 8 | Golden snapshot test runner | approvaltests, insta, pytest-snapshot | Who writes the assertions, and does it work on a black box? | Dead |
| 9 | Behaviour seal for arbitrary executables | None found at this mechanism level | Can a third party reproduce the verdict in a clean sandbox? | Survives |
| 10 | Portable evidence container | AARC event schemas, CodeVetter local checks | Does it survive outside the originating agent and repo? | Merged into 9 |

Candidate 9 survives only under a precise definition. A tool that runs a list of probes against two versions of any executable, records every observable effect, normalises declared nondeterminism, classifies each difference against the declared intent, and packages the whole thing into a safe, independently re-runnable artifact. A golden test runner requires a human to write expectations. An API diff reads symbols. A replay debugger reconstructs a session. This tool measures behaviour and hands the proof to somebody else.

## 3. The grill: 18 questions I had to answer before writing code

**Q1. Is this just snapshot testing with a new name?**
A. Snapshot testing stores expected output inside the project and compares one version against that expectation. `seal` compares two real executions and stores both. It works on a compiled binary, a shell script, or a CLI in any language. Nobody writes an expected value.

**Q2. Tests already tell me if something broke. Why run this?**
A. Tests cover assertions somebody remembered. `seal` covers the whole recorded observation surface: stdout, stderr, exit status, files created or modified, and declared environment effects. It finds changes nobody wrote a test for. That is the entire point.

**Q3. Nondeterminism will swamp the output with false alarms. What do you do?**
A. I do not hide it. Every observation carries a status. `SAME` means byte-identical. `INTENDED` means the difference sits inside the declared scope. `UNEXPECTED` means the difference sits outside it. `UNKNOWN` means a declared nondeterministic source or a missing ground truth prevents a verdict. A tool that calls a flaky timestamp a regression loses trust on day one.

**Q4. How can you claim this does not exist?**
A. I cannot, absolutely. The research section 10 lists six prior-art channels and states that no absolute absence claim is defensible. My claim is conditional: across the searched channels and as of 2026-11-11, no public general-purpose implementation was found that combines black-box probe execution, whole-surface observation capture, intent-scoped classification, and third-party re-executable evidence in one artifact. Section 7 records the exact searches.

**Q5. Why would a maintainer trust an artifact handed to them by an AI agent?**
A. They should not trust it. They run `seal verify`. Verification re-executes the declared probes in a fresh sandbox and compares its own verdict to the recorded one. Trust moves from the producer's prose to a reproducible run.

**Q6. Your tool executes arbitrary commands from a downloaded file. Is that a remote code execution service?**
A. It would be, if I were careless. The default policy refuses to execute anything from a bundle. Verification requires an explicit `--trust` flag, a command allowlist pinned in the bundle, a fresh temporary working directory, a wall-clock timeout, an output cap, and secret scrubbing. Round 3 and round 5 of the review exist specifically to attack this.

**Q7. What stops someone from tampering with the evidence file?**
A. Hashes over canonical JSON for every observation and probe, plus a bundle digest. Tampering changes the digest and verification reports `TAMPERED`. I do not claim cryptographic signing against a malicious producer. That would need a key infrastructure this MVP does not have. The limit is documented.

**Q8. What is the smallest thing that must be true for this to matter?**
A. One real, unintentional behaviour change must be caught by the tool and missed by a normal diff plus a passing test suite. The demo builds exactly that case.

**Q9. Why does this matter more in 2026 than in 2016?**
A. Patches now arrive from agents that can edit hundreds of files in one turn, and reviewers cannot read every line. Supply-chain attacks can hide in a dependency bump. The cost of review rose while the cost of producing a patch fell. A verifier that scales with the number of patches addresses the asymmetry.

**Q10. Who is the first user?**
A. A maintainer reviewing an agent-generated pull request, and a developer doing a refactor who needs to prove behaviour stayed fixed. The second user is exactly the task I was given for the architecture pass.

**Q11. What is the 30-second demo?**
A. `seal demo` creates two tiny programs, one with a deliberate side effect that the diff does not reveal, records both, and prints a verdict with `UNEXPECTED: 1`. No install, no config, no network.

**Q12. Why zero dependencies?**
A. A verifier people run on untrusted artifacts must be auditable in one sitting. Python 3 standard library only. No package install, no supply chain of its own.

**Q13. What if the program needs network, a database, or a GPU?**
A. The MVP marks those observations `UNKNOWN` and records the missing ground truth. It does not pretend to have verified them. The manifest declares the boundary.

**Q14. Could a user just diff the file trees of two runs?**
A. Yes, for files. They would still need exit codes, stderr, ordering, nondeterminism labels, intent scoping, and a portable reproduction bundle. The value is the contract and the reproduction, not the comparison loop.

**Q15. What kills this project?**
A. Noisy verdicts. If `UNKNOWN` dominates, or if normalisation hides real regressions, users stop reading the report. Precision beats coverage.

**Q16. Is `INTENDED` scope just a way to let the tool rubber-stamp anything?**
A. Scope is declared in the manifest before recording, hashed into the bundle, and printed in the report. A reviewer can see exactly what the producer claimed. Changing the scope after the fact breaks the digest.

**Q17. What did the adoption research force you to change?**
A. I cut the plugin system, the web dashboard, and the cloud service. Day one is one command, one visible verdict, one demo. The 14-point scorecard gates the release.

**Q18. What are you refusing to promise?**
A. 105,000 stars, absolute novelty, cryptographic nonrepudiation, deterministic replay of networked programs, and full automatic input discovery. Each refusal is written into the README.

## 4. Deep thinking: the invariant worth building

Every software change makes two claims: "I changed X" and "everything else stayed the same". Version control records the first claim. Tests sample the second. Nothing certifies the second claim across the whole observable surface, and nothing lets a stranger re-run the certification.

AI agents broke the economics of the second claim. Producing a patch now costs seconds. Reading it costs hours. Reviewers either rubber-stamp or become the bottleneck. A tool that turns "everything else stayed the same" into a reproducible artifact changes which side of that trade has the cheap operation. That is the difference this program can make.

The same invariant governs my own architecture pass later in this task. If I restructure the code and the behaviour seal still says `SAME`, I have evidence rather than an assertion.

## 5. Approved design

**Name:** `seal` (Behavior Seal)
**One sentence:** Show what a change actually changed, and hand the proof to somebody who was not there.
**Interface:** a single Python CLI, Python 3.9+, standard library only.

Commands:

| Command | Job |
|---|---|
| `seal init` | Write a `sealfile.json` manifest: target command, probes, normalisation rules, declared intent scope, safety policy |
| `seal record --tag NAME` | Run every probe in an isolated temp workspace and capture the full observation surface |
| `seal compare OLD NEW` | Classify each observation as `SAME`, `INTENDED`, `UNEXPECTED`, or `UNKNOWN`; print a report and write JSON |
| `seal verify BUNDLE --trust` | Re-execute declared probes in a clean sandbox and confirm the recorded verdict |
| `seal demo` | Self-contained 30-second demonstration that catches one hidden behaviour change |

Observation surface per probe: stdout, stderr, exit status, created and modified files with content hashes, and declared environment variable names. Durations are recorded for diagnostics and excluded from verdicts by default.

Verdict rules:

- `SAME`: canonical observation is byte-identical after declared normalisation.
- `INTENDED`: observation differs, and the difference falls inside the manifest's declared intent scope.
- `UNEXPECTED`: observation differs outside declared scope. Exit code 1 in CI mode.
- `UNKNOWN`: a declared nondeterministic source, a timeout, or missing ground truth blocks a verdict. Never silently converted to `SAME`.

Evidence bundle: a single canonical JSON file with manifest, probe definitions, both observation sets, per-observation digests, bundle digest, environment fingerprint, and verification policy. Secret values never enter the bundle. Names are kept, values are replaced with a salted digest or dropped.

Explicit non-goals, printed in the README: no cloud, no agent integration, no automatic program understanding, no cryptographic signing, no deterministic replay of networked programs, no star-count promises.

## 6. Hard gate

The brainstorming discipline requires an approved design before implementation. I read the design in section 5, ran the grill in section 3 against it, and recorded these changes from earlier drafts:

- Automatic input discovery was cut (Q18). Probes are explicit and auditable.
- "AI-native PR badge" framing was cut (Q4, Q5). The artifact and its re-execution are the product.
- A proposed `--auto-normalize` mode was cut (Q3, Q15). Hidden normalisation can erase real regressions.
- Bundle execution defaults changed from allowed to denied (Q6).

Approved by the manager on 2026-11-11. Implementation may start. Any change to the verdict model or the safety policy requires a new gate.

## 7. Novelty claim, stated carefully

No public, general-purpose implementation combining (a) black-box probe execution against two revisions, (b) whole-surface observation capture, (c) intent-scoped difference classification with an explicit `UNKNOWN` tier, and (d) a self-contained, third-party re-executable evidence bundle was identified in the searched channels as of 2026-11-11. Channels checked: GitHub and GitLab repository search, npm and PyPI, the agent-skills and MCP directories, curated lists, and source-level searches for the underlying mechanism. This is a conditional claim. It does not assert that no private implementation exists. `docs/07_prior_art.md` records the searches and the nearest neighbours.
