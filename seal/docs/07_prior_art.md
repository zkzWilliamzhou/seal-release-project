# Prior art and the novelty claim

Owner: A1. Date of search: 2026-11-11. Gate: G2.

## The claim, stated so it can be checked

Across the channels listed below, as of 2026-11-11, no public general-purpose implementation was found that combines all four of:

1. black-box probe execution against two revisions of an arbitrary executable,
2. whole-surface observation capture (stdout, stderr, exit status, file effects, env names),
3. four-state difference classification against an intent scope declared before recording, with `UNKNOWN` as a first-class state, and
4. a self-contained evidence bundle a third party re-executes in a clean sandbox.

This is a conditional claim. It does not say no private implementation exists, and it does not say no tool solves a neighbouring problem. Absolute novelty claims were rejected at gate G2 (rejection R1).

## Channels searched

| Channel | Queries used | Result |
|---|---|---|
| GitHub and GitLab repository search | "compare runtime behavior of two program versions", "differential testing CLI", "behavioral diff artifact", "golden behavior contract" | Adjacent tools found. See the matrix below. |
| npm | skill validators, MCP guardrails, agent replay packages | `mcp-warden` and adjacent policy tools found [10]. No four-part combination. |
| PyPI | approval testing, snapshot testing, behavior diff | `approvaltests` and snapshot runners found. No two-revision executable verifier. |
| crates.io | `cargo-semver-checks` and API diff tooling | Symbol-level diff tools found. No runtime observation capture. |
| Agent skills and MCP directories | brainstorming, grill-me, improve-codebase-architecture, guardrails, replay skills | Workflow skills found. No behaviour-seal skill. Installed copies are in `.agents/skills/`. |
| Curated lists and secondary sources | Awesome lists, developer discussions, the two research reports in `research/` | Agent verification, replay, and supply-chain categories all have occupants. |

Two research reports back this file: `../../research/opensource_gap_research.md` and `../../research/adoption_playbook.md`. Both were produced before the design gate. The first one lists ten daily pain points and names an existing neighbour for each, which is why the program targets a mechanism rather than a category.

## Nearest neighbours

| Project | What it does | Where it stops |
|---|---|---|
| Approval Tests (`https://github.com/approvals/ApprovalTests.Python`) | Stores an approved output and compares one run against it | A human writes the expectation. One version. Host-language fixtures. |
| `insta` (`https://github.com/mitsuhiko/insta`) | Snapshot testing for Rust | Same. Snapshots live in the project and assert a recorded value. |
| `cargo-semver-checks` (`https://github.com/obi1kenobi/cargo-semver-checks`) | Detects breaking API changes between crate versions | Reads types and symbols. Never runs the program. |
| `japicmp` (`https://github.com/siom79/japicmp`) | Binary and source API comparison for Java | Same boundary. |
| `diffoscope` (`https://diffoscope.org/`) | In-depth comparison of files and archives | Compares static artifacts. No execution, no intent scope, no verdict. |
| OrcaReplay, described in `../../research/opensource_gap_research.md` [13] | Captures model traffic, shell commands, file changes, MCP calls; offline replay | Reconstructs an agent session. Requires exact model and tool responses. |
| AARC (`https://dx.doi.org/10.5281/zenodo.23107335`) | Runtime event and state-vector contract with authorization receipts and a conformance suite | Defines schema and policy. Does not ship a third-party re-executable CLI evidence bundle. |
| CodeVetter (`https://intelligenttools.co/tools/codevetter`) | Binds a task to a change and runs project checks | Local checks in one project ecosystem. Not a portable black-box artifact. |
| OpenSSF Scorecard (`https://openssf.org/?p=5041`), SLSA (`https://slsa.dev/`) | Repository security heuristics and provenance levels | Heuristic scores and provenance, not runtime behaviour comparison. |
| MCP Guardrails Proxy, ScopeGate (`https://scopegate.io/`), `mcp-warden` (`https://www.npmjs.com/package/mcp-warden`) | Intercept tool calls, mint short-lived credentials, enforce policy | Operate at the authorization boundary. They do not compare two program revisions. |

The report in `../../research/opensource_gap_research.md` also records that roughly half of SWE-bench Verified passes would fail human code review [11][16]. That gap motivates the project. It does not prove novelty.

## What would falsify the claim

A public repository, package, or paper that ships all four parts above. The quickest check is a source search for any CLI that both runs a probe against two directories and emits a re-executable JSON bundle. If such a project appears, this file must be rewritten and the README's positioning changed.

## Limits of this search

Direct GitHub access was blocked in the build sandbox, so repository and registry results came from indexed search and the two research reports, not from a raw GitHub code-search API. Package versions and star counts are deliberately omitted. A legal prior-art search, patent databases, and private commercial products fall outside this check.
