# Developer-Tools Market Gaps in the Agent Era: Verification, Containment, and Executable Context (Research as of 2026-11)

## Executive summary: velocity has outrun verification, but the highest-value gap is operational rather than generative

Agentic coding has not created a shortage of generative ideas. It has exposed a shortage of **verifiable execution controls**. Anthropic’s Agent Skills format gives agents a portable packaging convention, while MCP provides a common transport for external tools and data [1][6]. Neither proves that a skill is correct, that an agent’s context is current, that a tool call is authorized, that a tool result is trustworthy, or that generated code satisfies the user’s real task. These gaps are operationally distinct from text generation and remain unresolved despite the rapid growth of adjacent projects.

This report identifies 10 high-frequency pain points and finds that none is unqualified “greenfield.” At least four candidate concepts already have public projects claiming to address them, and another—GitHub MCP server policy configuration—is supported by the official product itself. For example, ScopeGate targets ephemeral agent credentials, MCP Guardrails Proxy intercepts tool calls and tool results, and the public AARC artifact describes a reference monitor with conformance tests [8][9][12].

Three concepts survive adversarial screening only under deliberately narrow definitions:

1. **Repository-local executable context contracts.** A project that converts prose instructions into runnable invariants, then continuously evaluates them against live repositories, would differ from format specifications and context checkers if it could demonstrate measurable drift reduction and successful prevention of real bad edits.
2. **Offline agent replay with cryptographically reconstructable workspace state.** This requires bit-for-bit model and tool responses, file snapshots, shell traces, and seedable nondeterminism, not merely request logging or general browser replay.
3. **Task-to-diff verification artifacts that are independently re-executable and safe for third parties.** CodeVetter and AARC demonstrate that adjacent tooling exists; the differentiator must therefore be cross-agent portability, strict evidence packaging, and external reproducibility rather than another verdict badge.

A project should not claim novelty after searching GitHub alone. Credible verification requires at least six channels: GitHub and GitLab; npm, PyPI, crates.io, and relevant language registries; MCP and skills directories; curated lists; Software Heritage; and source-code or AST searches for the underlying mechanism.

The most credible opportunity is therefore not a new agent, a new skill, or another model wrapper. It is infrastructure that makes agent actions **legible, least-privilege, replayable, and independently checkable**.

## 1. Open standards removed integration friction, but operational correctness remains outside their scope

**The first generation of agent standards solved interoperability, not assurance.** MCP standardizes how an application connects to tools, content, and prompts; the official documentation describes it as an open protocol analogous to a USB-C port [6]. The Agent Skills specification similarly defines a folder containing `SKILL.md`, with at least `name`, `description`, and instructions. It also describes a progressive-disclosure mechanism that loads full instructions only when a task matches a skill [1].

These standards lower integration and packaging costs. They do not establish the truth of a skill’s claims, the legitimacy of a tool result, or the safety of a delegated action. The resulting market gap is not “agents need better instructions.” It is that repositories increasingly contain instructions, memories, prompts, generated code, tool definitions, and tool outputs that lack a shared operational contract.

The 2026 Agentic Applications Top 10 maps directly to this gap. OWASP identifies prompt injection, tool misuse or policy bypass, excessive permissions, agent supply chain, memory poisoning, and unbounded resource consumption [7]. The threat model has expanded from untrusted model output to untrusted context. Repository files, dependency documentation, web content, and tool outputs can all influence an agent’s next action.

The operational implication is that prompt filtering and test generation are insufficient. Security boundaries must be enforced below the model, at tool dispatch, capability grant, shell execution, and audit layers. This does not make the model layer irrelevant, but it prevents the model from remaining the sole policy authority.

Novelty claims should therefore be framed at the level of **mechanism and invariant**, not category. “An agent security tool,” “an MCP dashboard,” and “a SKILL.md validator” are not defensible unique propositions. A credible claim must specify the exact boundary being enforced and prove that no existing project enforces it in the same place, at the same stage, and with the same evidence output.

## 2. Existing agent standards cover transport and packaging, but leave governance to the operator

**MCP and Agent Skills are format solutions, not enforcement solutions.** MCP provides a common interface, while Agent Skills standardizes how knowledge and workflows can be attached to an agent. Their design boundary stops short of deciding whether a particular instruction is true, whether a tool call is authorized in context, or whether an agent’s resulting changes satisfy the task.

MCP explicitly places operational controls outside the protocol’s guarantees. Its security guidance describes malicious startup commands, OAuth URL validation, SSRF, session hijacking, and the need for sandboxing and least privilege [2]. It states that clients must validate authorization URLs, reject dangerous schemes, and avoid shell execution when opening URLs. These requirements define responsibilities; they do not constitute a universal authorization service or runtime policy engine.

Agent Skills defines a way to package a capability and disclose it progressively. The specification does not describe enforcement of semantic correctness, maintainer identity, script provenance, or testable behavior [1]. A SKILL.md file can therefore declare a workflow without proving that the workflow remains compatible with the current repository, that its scripts are safe, or that its recommendations are still valid.

This distinction matters for product positioning. A project that merely adds another context file, skill folder, or dashboard does not close the assurance gap. A project that intercepts tool calls, constrains capability grants, records external effects, or proves context validity operates beneath the model and can remain useful across multiple agents and skill formats.

The correct framing is therefore not “replace skills or MCP.” It is to add an independently inspectable control plane around them. Such a control plane should produce evidence that humans and automated systems can evaluate without trusting the agent’s prose summary.

## 3. Ten pain points recur daily, but every one already has an adjacent tool that must be disproved

**The highest-frequency gaps are observable in daily workflows, yet none is completely untouched.** The following table lists concrete pain points, the closest existing open-source tools, and the precise reason each tool does not resolve the underlying operational problem. This is an evidence-backed shortlist, not a count of every repository in the ecosystem.

| # | Daily pain point | Closest existing open-source tools | Why it remains unsolved |
|---|---|---|---|
| 1 | Repository instructions drift as code changes | AGENTS.md; `ctx`; Serena memories | AGENTS.md is unstructured Markdown with no required fields and no conformance test [3]. Public context-hygiene tools are early, often agent-specific, and typically inspect prose rather than prove that a stated invariant still holds. |
| 2 | Skills look authoritative but may be stale, malicious, or incompatible | `skill-validator` projects; skill linters | Public validators demonstrate demand, but discovery results include low-star repositories and loosely specified “quality” checks. They do not establish a universal, machine-checkable contract across all skills and runtimes. |
| 3 | Agents receive overly broad tokens or shell access | ScopeGate; Codex CLI sandbox | ScopeGate is a self-described ephemeral-credential gateway, while Codex documents per-command approval and OS sandboxing [8][11]. Neither constitutes a common control plane across every agent, MCP server, operating system, and cloud identity provider. |
| 4 | A permitted tool can still perform a destructive or disproportionate action | MCP Guardrails Proxy; `mcp-warden` | These projects demonstrate the proxy direction, including policy rules, audits, budgets, and approvals [9][10]. Public packages still leave gaps around cross-server policy composition, verifiable audit completeness, and robust semantic argument analysis. |
| 5 | Retrieved files and tool results can inject instructions into agent context | NVIDIA `garak`; OWASP scanners; proxy injection scanning | Static scanners and red-team tooling test applications or scan result content. They do not prove that an agent isolated untrusted text before the model used it to select its next tool call. |
| 6 | Reviewers cannot reproduce what the agent actually did | OrcaReplay; LangSmith/OpenTelemetry-style tracing | OrcaReplay claims local interception of model traffic, shell commands, file changes, and MCP calls, together with offline replay and forking [13]. It is new and self-reported, not an established general standard for deterministic multi-agent replay. |
| 7 | Passing tests do not prove task completion | CodeVetter; `gh`-based checks; conventional CI | CodeVetter binds a task to a change and executes project checks, but its available evidence concerns one project ecosystem and local execution [14]. General, portable task-to-diff verification artifacts remain uncommon. |
| 8 | AI-generated PRs create review debt without provenance | `git`; `gh`; CodeQL; Dependabot; GitHub code scanning | These tools provide history and alerts. They do not trace which prompt, model version, context files, tool calls, and approved actions produced a patch, nor do they provide replayable execution evidence. |
| 9 | MCP server versions change tools and permissions silently | GitHub MCP server toolsets and configuration lockfile | The GitHub MCP server supports toolsets and lock files, but its documentation explicitly states that not all GitHub data is accessible through the server or REST API [15]. “Allowed tools” configuration is not cross-server semantic policy enforcement. |
| 10 | Supply-chain checks miss agent-installed packages, skills, and docs | OpenSSF Scorecard; GitHub Advisory Database; npm audit; SLSA | OpenSSF reports scanning about 1.2 million repositories while explicitly acknowledging difficulty in accurately detecting every condition [4]. Scorecard is heuristic, and registry or advisory coverage does not establish the provenance of every agent-installed artifact. |

The evidence supports a narrow conclusion. Each pain point has an existing tool or category, but no tool listed above simultaneously provides a universal contract, runtime enforcement, complete evidence capture, and independent reproducibility. The gap is therefore systemic rather than isolated.

The market implication is equally narrow: broad claims such as “the first AI coding security tool” are not credible. A viable project must choose one enforcement boundary, identify the specific existing tool that appears closest, and demonstrate why that tool’s output or scope is insufficient for the claimed use case.

## 4. Existing controls cover fragments of assurance, but none composes them into a complete causal record

**The most damaging failure mode is not a single bad output; it is the loss of causal traceability.** Generated code, a successful test, a skill instruction, a tool call, and a merged PR are individually inspectable in many workflows. Their causal relationships are often not.

A repository may contain a plausible patch, passing CI, and an agent transcript, yet still leave unanswered which instruction authorized the change, which credential permitted it, what untrusted text the agent had read, and whether the recorded result was the actual text used during execution. The problem is not that evidence is absent everywhere; it is fragmented across Git history, shell history, logs, dashboards, scanner alerts, and agent memory.

Tool-specific checks make this fragmentation worse. GitHub code scanning, advisory databases, Scorecard, and SLSA each operate at different layers and expose different interfaces [4][5]. A skill validator can inspect `SKILL.md`. A proxy can inspect tool calls. A CI system can execute tests. None of these guarantees, by itself, that a downstream reviewer can reconstruct the path from a user objective to a deployed change.

The missing layer is an **evidence graph** with stable identifiers and explicit boundaries. Such a graph should link objectives, context versions, model and agent versions, credentials, tool schemas, tool calls and results, filesystem and shell effects, and post-conditions. A graph is not valuable because it aggregates logs. It is valuable only if the links are independently reconstructable and can distinguish a checked property from an unchecked assumption.

This is also where many “AI audit” ideas fail. Recording more JSON does not establish trust. An evidence graph must make completeness falsifiable: either a required edge exists with valid provenance, or the system must mark the corresponding assurance claim as unverified.

## 5. Credentials and broad tool permissions remain the most concrete operational hazard

**Agent permissions are still commonly expressed as ambient authority rather than bounded capability.** A long-lived GitHub token, an unrestricted shell, and broad filesystem access each allow an agent to perform operations far beyond the current task. MCP’s security documentation identifies local server compromise, malicious startup commands, OAuth session risks, and inadequate sandboxing as concrete attack patterns [2].

Tool availability and command approval are not equivalent to least privilege. An agent may be authorized to call a write tool while lacking any constraint on the resource, duration, identity, rate, or downstream effect of that call. The protocol standardizes access; it does not make every authorized action proportionate.

The credible product direction is a **capability broker** that translates a task intent into a short-lived, revocable, resource-specific grant. Codex demonstrates that per-command approval and sandboxing are already practical [11]. ScopeGate demonstrates that credential virtualization and time-bounded grants are being attempted [8]. A new project cannot claim novelty merely by minting tokens or requesting approval.

The defensible differentiator is a policy runtime that operates across heterogeneous agents and servers, attaches a verifiable authorization receipt to each external effect, and allows a denied action to be reconstructed without trusting the agent’s transcript. Such a system would be valuable because it narrows the consequences of prompt injection even when the model has already been manipulated. It would still fail if it introduced latency, false denials, or dependency on a central service that developers would not install.

## 6. Context quality is a validation problem, not a documentation-format problem

**More agent context does not improve decisions if the context is stale, contradictory, or unverifiable.** AGENTS.md now describes itself as a simple open format used across agents and tools, with no required fields [3]. Agent Skills standardizes packaging but not the validity of the packaged instructions [1].

A context file may tell an agent to run `pnpm test`, state an incorrect minimum Rust version, preserve an outdated architecture diagram, or recommend a dependency that the project no longer uses. The file remains syntactically valid in both formats. The cost is not merely cosmetic: an agent can confidently execute obsolete instructions, create files that violate current structure, or introduce dependencies that do not match the supported toolchain.

Format convergence is therefore not assurance convergence. Multiple overlapping context files can agree with one another while all diverging from the repository. Conversely, a correct instruction may be rejected by a naive textual checker because it uses different wording. A robust system must distinguish factual claims, preferences, procedures, and out-of-scope guidance.

The practical requirement is a **typed context contract**. A claim such as “Node 20 is the minimum supported version” should resolve to an inspectable assertion about a `package.json` `engines` field, a Dockerfile, or a CI configuration. A rule such as “run tests before merging” should remain prose unless it can be compiled into a runnable check with a defined scope and exit criterion.

This direction must avoid becoming a documentation generator. Its value is not measured by the number of Markdown files produced. It is measured by whether factual claims can be validated, whether stale claims are detected before execution, and whether procedures change behavior when the underlying repository changes.

## 7. Deterministic replay is unusually credible, but must prove bit identity rather than narrative similarity

**A local replay system can reduce “it worked for the agent” to testable evidence, but it must reconstruct state exactly.** The core user need is not a chat log. It is the ability to show what model input produced which command, which command altered which files, and which subsequent model call observed the altered state.

OrcaReplay claims to capture model messages, shell commands and exit codes, file changes, and MCP calls, while also offering offline replay and forks from a checkpoint [13]. This evidence is sufficient to reject the simplistic claim that no replay project exists. It is not sufficient to establish maturity, broad compatibility, or deterministic replay under real multi-agent workloads.

The unresolved technical burden is exact reconstruction:

| Required component | Why the component is necessary |
|---|---|
| Bit-identical model request and response capture | Prevents the replay from substituting a semantically similar but different model decision |
| File-system snapshots and command environment capture | Reconstructs the exact state observed and modified by each command |
| Shell stdin, stdout, stderr, and exit-code capture | Preserves command-level causality rather than summarizing the action |
| MCP request, response, and schema capture | Identifies changes in tool definitions or tool behavior between runs |
| Seedable nondeterminism | Controls sources of variance without falsifying the original execution |
| Reversible time and clock effects | Reduces irrelevant differences that would otherwise break byte-level comparison |

A replay project that only stores a narrative or approximate event log cannot prove that the observed behavior was the same as the original run. It may help debugging, but it cannot support strong claims about reproducibility or independent verification.

The strongest failure mode is therefore environmental rather than algorithmic: local sockets, vendor APIs, network state, container behavior, and secret handling may prevent byte-identical replay. The credible answer is not to hide that limitation. A minimum viable system should support a “best-effort sandbox replay” mode with explicit nondeterminism labels and evidence tiers, while reserving strict replay for controlled environments.

## 8. Three concepts remain plausible only under narrow, testable definitions

**The three strongest candidate concepts are not empty categories; each fills a specific missing invariant.** They remain defensible only because existing alternatives solve adjacent problems or solve the whole problem at a different layer. All novelty claims below should be treated as provisional rather than absolute.

| Candidate concept | One-sentence description | Primary target user | Why now (2026-specific) | Why it could plausibly reach 100k+ stars | Strongest reason it would fail | Minimal credible MVP must prove |
|---|---|---|---|---|---|---|
| Repository-local executable context contracts | Convert human agent instructions into versioned, machine-checkable predicates and continuously evaluate them against the live repository | Lead developers, platform engineers, and OSS maintainers operating multi-agent repositories | Skills, `AGENTS.md`, rules, and memories proliferate without a shared validity layer | A self-contained CLI that prevents real bad edits is more observable than another policy framework | Context extractors misclassify prose, produce noisy false positives, and become expensive to maintain | Extract at least 20 claim types from real repositories, validate them against authoritative files, and demonstrate both precision and actionable fix suggestions |
| Offline agent replay with cryptographically reconstructable workspace state | Record an agent run’s model traffic, shell effects, file deltas, and tool calls, then replay it offline from a fixed initial state | Agent developers and teams debugging regressions | Agents now operate shells and MCP tools over long-running sessions | A reliable “debug my agent” tool could spread rapidly across individual developers | Exact replay is defeated by proprietary models, APIs, clocks, and stateful services | Replay one supported agent on 20 public tasks with byte-level request equality where mocked and with reproducible file outcomes |
| Portable, independently re-executable task-to-diff verification artifacts | Bind a task statement, model and agent version, context snapshot, code diff, and runnable checks into an artifact that any reviewer can rerun safely | OSS maintainers and engineering teams reviewing agent-generated PRs | Generated PR volume is rising faster than review capacity | Trusted “proof a patch does what it claims” infrastructure could become a developer default | Verdicts depend on hidden environments, and users will not accept untrusted execution | Produce an artifact containing all required inputs or a declared gap, execute it in a clean sandbox, and independently reproduce the same pass or fail result |

The first two concepts can be stated precisely. Executable context contracts add a semantic validity layer beneath documentation formats. Replay with reconstructable state adds environmental fidelity beneath event logs.

The third concept requires more caution. AARC already describes a machine-verifiable audit and reliability contract, including runtime-event and state-vector schemas, authorization receipts, and a conformance suite [12]. CodeVetter already focuses on binding a task to an agent change and executing repository checks [14]. A new task-to-diff verification project therefore cannot succeed by bundling tests after the fact. Its specific contribution must be portability across agents, safe external execution, and reproducible evidence packaging.

## 9. Every candidate must prove both a missing invariant and a measurable operational improvement

**Novelty is only the entry condition; usefulness must be demonstrated separately.** The first two candidates can be framed as invariant-enforcement problems, while the third must be framed as an evidence-portability problem.

### 9.1 Executable context contracts must prevent stale instructions from becoming executable authority

**A context contract is useful only if it changes agent behavior before an invalid instruction causes an effect.** AGENTS.md’s own documentation states that its instructions can include commands an agent will attempt to execute, such as running tests before committing [3]. This creates a direct path from stale documentation to undesirable action.

A credible implementation should parse or embed typed claims such as versions, paths, available commands, architectural boundaries, and release procedures. It should then compile those claims into checks that return a clear status: satisfied, contradicted, unknown, or not applicable. A mismatch should block or warn the agent before execution rather than merely comment on a Markdown file after the fact.

The MVP must run locally and offline against at least three stacks, such as Node, Python, and Go. It must demonstrate two outcomes:

- independently recoverable ground truth for each claim; and
- a measurable reduction in stale or contradictory claims without requiring developers to rewrite all instructions.

Success is not a high “context score.” The relevant metric is the rate of detected invalid operational instructions and the number of those detections that lead to corrected context before an edit.

### 9.2 Replay must reconstruct state exactly, not merely resemble the original run

**Replay value is determined by environmental fidelity, not by the volume of captured events.** Exact request and response capture is necessary, but insufficient when shell commands depend on network resources, mutable APIs, system time, or local credentials.

The MVP should support deterministic mode for mocked services and explicitly label nondeterministic mode for live external systems. It should capture model messages, tool protocol traffic, command environment, exit codes, file deltas, and secrets-free audit output.

Reproducibility must be measured at three levels:

| Level | Required result | Acceptable outcome for nondeterministic mode |
|---|---|---|
| Strict | Byte-identical requests and controlled responses reproduce the original run | Should not be claimed |
| Structural | File changes and tool-call graph reproduce the original run | Permitted only with an explicit nondeterminism label |
| Diagnostic | Failures can be localized and understood | Permitted, but not sufficient for strict replay claims |

Without these distinctions, replay products risk conflating narrative similarity with reproducibility.

### 9.3 Portable task-to-diff artifacts must prevent credential and environment laundering

**A verification artifact is credible only when it avoids hiding the conditions required to reach its verdict.** It must include or explicitly omit the task, model and agent, repository state, context files, prompt and configuration snapshots, commands, tool outputs, and check definitions.

Secrets should not be embedded. Third-party rerunners should not inherit the repository’s production credentials. The artifact should instead include a policy describing what authority and environment are needed, plus a safe way to run only the declared verification sequence.

AARC provides related event and provenance machinery, so a new product must focus on interoperability rather than reimplementing an event schema [12]. CodeVetter shows that execution-backed verification is already being attempted [14]. The opportunity is therefore not another local verifier. It is a **portable evidence container** that can move across agents and reviewers without transferring unnecessary authority.

## 10. Cross-channel prior-art checks prevent false novelty claims, but cannot prove absolute novelty

**The purpose of prior-art search is to make a narrower, defensible claim, not to declare a category vacant.** A developer-tools project should search GitHub and GitLab repositories, then examine source, license, README, release history, open issues, and recent commits. Repository search alone is inadequate because the same mechanism may be embedded in a CLI, SDK, proxy, GitHub Action, or language-specific package.

| Channel | Search strategy | What it can show | What it cannot prove |
|---|---|---|---|
| GitHub and GitLab | Full-phrase and component-phrase searches for the mechanism; filter by recency and language | Repository claims, code, license, release history, issue activity | Absolute absence across non-indexed forges |
| Package registries | Search npm, PyPI, crates.io, and relevant language ecosystems for exact capability names and mechanism fragments | Published implementations and distribution channels | Undisclosed proprietary products or private repositories |
| MCP and skills directories | Inspect official and community server and skill lists; check transport, tool schemas, permissions, and configuration | Whether the capability is already shipped as a server or skill | Quality, completeness, or long-term maintenance |
| Curated lists and discussions | Review dependency dashboards, Awesome lists, Hacker News, and developer forums | Naming variants and early projects that search engines under-index | Whether a listed project is operationally viable |
| Software Heritage | Search archived origins and trigger archiving for candidate repositories; preserve source snapshots | Historical existence and source preservation | Future changes or unpublished forks |
| AST and source search | Search for distinctive functions, policy predicates, schema fields, CLI verbs, and replay mechanisms | Prior implementations even when names differ | Guaranteed absence across all private code |

Software Heritage is particularly useful for historical claims. It harvests publicly available source code, allows searches for archived origins and archive visits, and provides API access [4]. It cannot prove that a capability has never existed in private code, but it can establish that a project or source snapshot was publicly preserved by a given date.

A credible novelty statement should use conditional language: “No public, general-purpose implementation combining X, Y, and Z was identified across the searched channels as of the search date.” It should not claim that no implementation exists anywhere. This distinction is essential when projects are new, naming is inconsistent, and some tools are not indexed by package registries.

## 11. Candidate claims must be falsifiable, evidence-grounded, and limited to observed scope

**The evidence supports specific opportunities, not universal conclusions.** All candidate claims should be read as provisional rather than absolute.

1. Agent Skills provides a common packaging format, not proof of semantic validity or testable behavior [1].
2. MCP provides a common integration protocol, while its security documentation leaves sandboxing, consent, and least privilege to client and server implementations [2].
3. AGENTS.md adoption does not eliminate drift: the format has no required fields and can contain executable commands [3].
4. ScopeGate, MCP Guardrails Proxy, and `mcp-warden` mean that agent authorization and MCP security are not untouched categories [8][9][10].
5. OrcaReplay, AARC, and CodeVetter mean that replay, runtime contracts, and task verification are also not untouched [12][13][14].
6. A project’s novelty must therefore be stated as a narrower mechanism, such as policy placement, evidence format, execution boundary, or replay identity, and supported by multi-source search.
7. OpenSSF Scorecard’s own disclosure of detection difficulty makes clear that broad repository-security scores are not definitive proof of safety [4].
8. The most credible high-leverage bet is a developer-installable control plane for agent actions, not another model, dashboard, or context file.
9. Any verification product must clearly distinguish passing an executed check from proving task correctness or factual truth.
10. The evidence reviewed here is sufficient to support product prioritization, but not a final legal or comprehensive patent prior-art search.

The final strategic test is practical. A new project should be able to state, in one sentence, which edge of the agent execution path it controls and which existing project it outperforms at that edge. If it cannot do so, it is likely a marginal addition to an already crowded toolchain rather than a genuine infrastructure gap.

## Data sources

[1] https://skill.md/
> “A standardized way to give AI agents new capabilities and expertise.”

[2] https://modelcontextprotocol.io/docs/2024-11-05/tutorials/security/security_best_practices
> “MCP clients MUST validate authorization URLs and reject dangerous schemes.”

[3] https://agents.md/
> “AGENTS.md is just standard Markdown. Use any headings you like; the agent simply parses the text you provide.”

[4] https://openssf.org/?p=5041
> “We regularly scan 1.2 million repos, and make the results available on our website.”

[5] https://slsa.dev/?ref=blog.phylum.io
> “SLSA is for everyone involved in producing, consuming, and providing infrastructure for software.”

[6] https://modelcontextprotocol.io/
> “MCP is an open protocol for connecting AI applications to external systems.”

[7] https://www.endorlabs.com/learn/adlc-compliance
> “The most relevant OWASP risks for coding agents are prompt injection, sensitive information disclosure, supply chain, and excessive agency.”

[8] https://scopegate.io/
> “ScopeGate is an open-source ephemeral-credentials gateway for coding agents.”

[9] https://theagenttimes.com/agents/article/developers-race-to-build-the-human-agent-communication-layer-e752412e
> “None handles the full lifecycle of a persistent agent that needs to pause, ask a human for approval, and resume.”

[10] https://www.npmjs.com/package/mcp-warden
> “mcp-warden enforces a security boundary before and after every tool execution.”

[11] https://theagenttimes.com/agents/article/half-of-our-swe-bench-wins-would-fail-human-code-review-449fb64d
> “Roughly half of the pull requests we generate that pass SWE-bench Verified’s automated test suite would be rejected by actual open-source maintainers.”

[12] https://dx.doi.org/10.5281/zenodo.23107335
> “AARC is a model- and policy-engine-independent runtime contract for externally observable execution by tool-using AI agents.”

[13] https://www.softwareheritage.org/
> “You can search which software origins have already been archived and when we have visited it.”

[14] https://replay.io/
> “Autonomous QA for teams shipping faster than ever before.”

[15] https://intelligenttools.co/tools/codevetter
> “CodeVetter binds the requested task to the exact change the agent made.”

[16] https://theagenttimes.com/agents/article/half-of-our-swe-bench-wins-would-fail-human-code-review-449fb64d
> “Half of Our SWE-bench Wins Would Fail Human Code Review.”
