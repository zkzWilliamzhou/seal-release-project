# Good first issue drafts

Publish these on GitHub with the `good first issue` label. Each has one file, one acceptance criterion, and one test.

## 1. Add a `ports` normalization rule

**File:** `src/seal/canonical.py`, `src/seal/manifest.py`, `tests/test_core.py`
**Problem:** Some CLIs print a random local port. A producer has no declared way to normalize it.
**Acceptance:** `manifest.normalization.ports` is a boolean. When true, `normalize()` replaces `:5[0-9]{4}` with `:<PORT>`. When false, the bytes stay. Unknown keys still raise `ManifestError`.
**Test:** `test_ports_normalization_is_declared` in `tests/test_core.py`.
**Guardrail:** `tests/behavior_lock.py --check` must stay green. ADR 0003 stays in force.

## 2. Add a Node.js probe example

**File:** `docs/TROUBLESHOOTING.md`, `tests/test_core.py`
**Problem:** Every example uses Python. A reader cannot tell whether the target can be any executable.
**Acceptance:** The troubleshooting page has one manifest whose `target.command` is `["node", "app.js"]`. A test runs it when `node` exists and skips otherwise.
**Test:** `test_node_probe_example_runs` using `unittest.skipUnless(shutil.which("node"))`.
**Guardrail:** No runtime dependency added. ADR 0004 stays in force.

## 3. Improve the missing-probe error message

**File:** `src/seal/compare.py`, `tests/test_core.py`
**Problem:** `records contain different probe sets` names no probe.
**Acceptance:** The error lists the symmetric difference of probe names, sorted.
**Test:** `test_probe_set_error_names_the_probes`.
**Guardrail:** Exit code stays 2. `docs/05_architecture_refactor.md` stays valid.
