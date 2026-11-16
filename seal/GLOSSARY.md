# GLOSSARY.md

Shared vocabulary for `docs/adr/` and the architecture pass. The `improve-codebase-architecture` skill uses these terms exactly.

| Term | Meaning in this codebase |
|---|---|
| **module** | One Python file under `src/seal/`. Each has a single responsibility. |
| **interface** | The public functions a module exports and the JSON shapes they accept. |
| **depth** | Ratio of work done to surface exposed. A deep module hides a lot behind a small interface. |
| **seam** | A place where two modules meet. One adapter across a seam is hypothetical. Two adapters make it real. |
| **adapter** | Code that translates between an external shape and an internal one. |
| **leverage** | How many call sites benefit from one change inside a module. |
| **locality** | Related behaviour sits in one place, so a reader does not jump between files. |
| **probe** | A declared invocation of the target program with fixed args, stdin and env. |
| **observation** | The captured surface of one probe: status, stdout, stderr, exit code, file delta, env names. |
| **channel** | One field of an observation. Six channels exist. |
| **verdict** | One of `SAME`, `INTENDED`, `UNEXPECTED`, `UNKNOWN`. |
| **record** | All observations from one version of a subject, plus digests. |
| **bundle** | A self-contained JSON file holding the manifest, two records and the report. |
| **intent scope** | The set of channels the producer declared as expected to change. |
| **sealed surface** | The set of channels whose verdicts must not change across a refactor. |

The deletion test: if deleting a module would concentrate complexity in its callers rather than move it elsewhere, the module is shallow. `docs/05_architecture_refactor.md` applies this test before moving any code.
