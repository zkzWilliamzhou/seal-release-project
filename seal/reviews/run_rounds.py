#!/usr/bin/env python3
"""Eight executable review rounds.

Each round runs real checks against the implementation and records
PASS/FAIL with a detail string. Nothing is asserted on faith. Usage:

    python3 reviews/run_rounds.py before
    python3 reviews/run_rounds.py after

Results land in reviews/logs/round-XX-<suffix>.json.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from seal.bundle import build_bundle, check_bundle, reproduce  # noqa: E402
from seal.canonical import digest, normalize  # noqa: E402
from seal.cli import main  # noqa: E402
from seal.compare import compare_records  # noqa: E402
from seal.errors import SealError  # noqa: E402
from seal.manifest import validate  # noqa: E402
from seal.runner import build_record  # noqa: E402
from _support import PROG_V1, PROG_V2_SIDE_EFFECT, Workspace, manifest_dict  # noqa: E402

LOGDIR = ROOT / "reviews" / "logs"
LOGDIR.mkdir(parents=True, exist_ok=True)


def check(name: str, fn):
    try:
        detail = fn()
        return {"check": name, "status": "PASS", "detail": str(detail)[:400] or "ok"}
    except Exception as exc:  # noqa: BLE001 - review harness must catch everything
        return {"check": name, "status": "FAIL",
                "detail": f"{type(exc).__name__}: {exc}"[:400]}


def expect(cond, msg="condition false"):
    if not cond:
        raise AssertionError(msg)
    return "ok"


def expect_raises(fn, exc_type=Exception):
    try:
        fn()
    except exc_type as exc:
        return f"raised {type(exc).__name__}"
    raise AssertionError("expected an exception, none raised")


def records(w, v2=PROG_V2_SIDE_EFFECT, **kwargs):
    m = validate(manifest_dict(**kwargs))
    d = digest(m)
    old = build_record(m, d, "before", w.subject("v1", PROG_V1).parent)
    new = build_record(m, d, "after", w.subject("v2", v2).parent)
    return m, old, new


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------- round 1
def round1():
    r = []

    def unit():
        p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=ROOT, env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'tests'}"},
                           capture_output=True, text=True, timeout=180)
        expect(p.returncode == 0, p.stdout[-800:] + p.stderr[-800:])
        summary = [line for line in p.stderr.strip().splitlines() if line.startswith("Ran ")]
        return summary[-1] if summary else "unit suite green"

    r.append(check("unit suite passes", unit))
    r.append(check("--version is stable", lambda: expect(
        "seal 0.1.0" in subprocess.run([sys.executable, str(ROOT / "seal"), "--version"],
                                       capture_output=True, text=True).stdout)))
    r.append(check("demo detects hidden change", lambda: expect(
        __import__("seal.demo", fromlist=["run_demo"]).run_demo()["passed"])))
    r.append(check("identical subjects give CLEAN", lambda: _clean_check()))
    r.append(check("stdout change gives UNEXPECTED", lambda: _unexpected_check()))
    r.append(check("digest ignores key order", lambda: expect(
        digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1}))))
    return r


def _clean_check():
    with Workspace() as w:
        m, old, new = records(w, v2=PROG_V1)
        return expect(compare_records(old, new, m)["overall"] == "CLEAN")


def _unexpected_check():
    with Workspace() as w:
        m, old, new = records(w)
        return expect(compare_records(old, new, m)["overall"] == "UNEXPECTED")


# ---------------------------------------------------------------- round 2
def round2():
    r = []
    bad_manifests = {
        "timeout zero": manifest_dict(timeout=0),
        "timeout bool": manifest_dict(timeout=True),
        "timeout 301": manifest_dict(timeout=301),
        "timeout string": manifest_dict(timeout="10"),
        "cap zero": manifest_dict(cap=0),
        "cap bool": manifest_dict(cap=True),
        "cap too large": manifest_dict(cap=65 * 1048576),
        "empty command": manifest_dict(command=[]),
        "nul in arg": manifest_dict(command=["python3", "x\x00y"]),
        "duplicate probes": manifest_dict(probes=[{"name": "a"}, {"name": "a"}]),
        "bad scope": manifest_dict(scope=["magic"]),
        "bad nondeterminism": manifest_dict(nondeterminism=["magic"]),
        "empty allowlist": manifest_dict(allowed=[]),
        "path in allowlist": manifest_dict(allowed=["/bin/sh"]),
    }
    for label, raw in bad_manifests.items():
        r.append(check(f"reject: {label}", lambda raw=raw: expect_raises(lambda: validate(raw), SealError)))

    def unknown_normalization():
        raw = manifest_dict()
        raw["normalization"]["magic"] = True
        return expect_raises(lambda: validate(raw), SealError)

    def env_key_equals():
        raw = manifest_dict()
        raw["probes"][0]["env"] = {"A=B": "x"}
        return expect_raises(lambda: validate(raw), SealError)

    def missing_manifest():
        with Workspace() as w:
            code, _, err = run_cli("record", "--subject", str(w.root), "--tag", "x",
                                   "--manifest", str(w.root / "nope.json"))
            return expect(code == 2 and "manifest" in err, f"code={code} err={err}")

    def bad_tags():
        for tag in ("../escape", "a b", "", "x" * 65, "/tmp/x", "a\x00b"):
            code, _, _ = run_cli("record", "--subject", ".", "--tag", tag)
            expect(code == 3, f"tag {tag!r} accepted")
        return "5 tags refused"

    r.append(check("reject unknown normalization key", unknown_normalization))
    r.append(check("reject env key containing '='", env_key_equals))
    r.append(check("missing manifest gives clean error", missing_manifest))
    r.append(check("path-traversal tags refused", bad_tags))
    return r


# ---------------------------------------------------------------- round 3
def round3():
    r = []

    def disallowed():
        with Workspace() as w:
            w.subject("v1", PROG_V1)
            return expect_raises(lambda: records(w, allowed=["node"]), SealError)

    def absolute_exe():
        with Workspace() as w:
            w.subject("v1", PROG_V1)
            return expect_raises(lambda: records(w, command=["/bin/echo", "hi"]), SealError)

    def parent_exe():
        with Workspace() as w:
            w.subject("v1", PROG_V1)
            return expect_raises(lambda: records(w, command=["../main.py"]), SealError)

    def no_shell():
        with Workspace() as w:
            subj = w.subject("v1", "import sys; print(sys.argv[1:])\n").parent
            raw = manifest_dict()
            raw["probes"] = [{"name": "p1", "args": ["a; touch /tmp/seal_pwned"],
                              "stdin": "", "env": {}}]
            m = validate(raw)
            rec = build_record(m, digest(m), "t", subj)
            expect("/tmp/seal_pwned" in rec["probes"]["p1"]["stdout"],
                   "argument was not passed literally")
            expect(not pathlib.Path("/tmp/seal_pwned").exists(), "shell executed the metacharacter")
            return "argv literal, no shell"

    def static_no_shell():
        text = (ROOT / "src" / "seal" / "runner.py").read_text()
        return expect("shell=True" not in text and "os.system" not in text,
                      "shell execution found in runner")

    def exe_runs_from_copy():
        with Workspace() as w:
            subj = w.subject("v1", "#!/usr/bin/env python3\n"
                                   "import os; print(os.path.dirname(os.path.abspath(__file__)))\n").parent
            (subj / "main.py").chmod(0o755)
            raw = manifest_dict(command=["./main.py"])
            m = validate(raw)
            rec = build_record(m, digest(m), "t", subj)
            out = rec["probes"]["p1"]["stdout"]
            expect("<WORKDIR>" in out, f"executable ran outside the copied workdir: {out!r}")
            return "path normalized to <WORKDIR>"

    def group_kill():
        with Workspace() as w:
            marker = w.root / "survived.txt"
            code = ("import subprocess, sys, os, time\n"
                    "subprocess.Popen([sys.executable, '-c', "
                    "\"import time,os; time.sleep(1.2); open(os.environ['SURVIVE_PATH'],'w').write('1')\"])\n"
                    "time.sleep(5)\n")
            subj = w.subject("v1", code).parent
            raw = manifest_dict(timeout=0.3)
            raw["probes"] = [{"name": "p1", "args": [], "stdin": "",
                              "env": {"SURVIVE_PATH": str(marker)}}]
            m = validate(raw)
            build_record(m, digest(m), "t", subj)
            time.sleep(1.6)
            expect(not marker.exists(), "grandchild survived the timeout and wrote outside the sandbox")
            return "process group terminated"

    r.append(check("disallowed executable refused", disallowed))
    r.append(check("absolute executable outside subject refused", absolute_exe))
    r.append(check("parent-directory executable refused", parent_exe))
    r.append(check("shell metacharacters stay literal", no_shell))
    r.append(check("static scan: no shell execution", static_no_shell))
    r.append(check("subject executable runs from workdir copy", exe_runs_from_copy))
    r.append(check("timeout kills the whole process group", group_kill))
    return r


# ---------------------------------------------------------------- round 4
def round4():
    r = []

    def secret_absent():
        with Workspace() as w:
            subj = w.subject("v1", "import os; print(os.environ['API_TOKEN'])\n").parent
            raw = manifest_dict()
            raw["probes"] = [{"name": "p1", "env": {"API_TOKEN": "supersecret-1234"}}]
            m = validate(raw)
            rec = build_record(m, digest(m), "t", subj)
            expect("supersecret-1234" not in json.dumps(rec))
            return "secret value absent"

    def host_secret_absent():
        with Workspace() as w:
            subj = w.subject("v1", "print('HOST_SECRET_MARKER_998877')\n").parent
            os.environ["SEAL_TEST_TOKEN"] = "HOST_SECRET_MARKER_998877"
            try:
                m = validate(manifest_dict())
                rec = build_record(m, digest(m), "t", subj)
                expect("HOST_SECRET_MARKER_998877" not in json.dumps(rec))
                return "host secret value absent"
            finally:
                del os.environ["SEAL_TEST_TOKEN"]

    def reserved_env():
        reserved = ["LD_PRELOAD", "PYTHONPATH", "PATH", "HOME", "BASH_ENV",
                    "LD_LIBRARY_PATH", "IFS", "PYTHONSTARTUP"]
        for key in reserved:
            raw = manifest_dict()
            raw["probes"] = [{"name": "p1", "env": {key: "/tmp/evil"}}]
            expect_raises(lambda raw=raw: validate(raw), SealError)
        return f"{len(reserved)} reserved keys refused"

    def env_names_only():
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            raw = manifest_dict()
            raw["probes"] = [{"name": "p1", "env": {"MY_VAR": "visible-value"}}]
            m = validate(raw)
            rec = build_record(m, digest(m), "t", subj)
            expect("visible-value" not in json.dumps(rec["probes"]["p1"]["env_names"]))
            return "names only"

    def stderr_cap():
        with Workspace() as w:
            subj = w.subject("v1", "import sys; sys.stderr.write('e' * 100000)\n").parent
            m = validate(manifest_dict(cap=256))
            rec = build_record(m, digest(m), "t", subj)
            expect(len(rec["probes"]["p1"]["stderr"]) == 256)
            return "capped at 256"

    def unicode_safe():
        with Workspace() as w:
            subj = w.subject("v1", "import sys; sys.stdout.buffer.write(b'\\xff\\xfe ok')\n").parent
            m = validate(manifest_dict())
            rec = build_record(m, digest(m), "t", subj)
            expect("ok" in rec["probes"]["p1"]["stdout"])
            return "replacement decoding"

    r.append(check("probe secret is redacted", secret_absent))
    r.append(check("host secret is redacted", host_secret_absent))
    r.append(check("reserved environment keys refused", reserved_env))
    r.append(check("only env names recorded", env_names_only))
    r.append(check("stderr output cap enforced", stderr_cap))
    r.append(check("invalid UTF-8 does not crash", unicode_safe))
    return r


# ---------------------------------------------------------------- round 5
def round5():
    r = []

    def symlink_inside():
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            (subj / "link.txt").symlink_to(subj / "main.py")
            return expect_raises(lambda: records(w), SealError)

    def symlink_escape():
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            outside = w.root / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            (subj / "link.txt").symlink_to(outside)
            return expect_raises(lambda: records(w), SealError)

    def fifo_refused():
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            os.mkfifo(subj / "pipe")
            script = (
                "import sys; sys.path.insert(0, r'{src}');\n"
                "from seal.runner import build_record\n"
                "from seal.manifest import validate\n"
                "from seal.canonical import digest\n"
                "from _support import manifest_dict\n"
                "m = validate(manifest_dict());\n"
                "build_record(m, digest(m), 't', r'{subj}')\n"
            ).format(src=ROOT / "src", subj=subj)
            p = subprocess.run([sys.executable, "-c", script], capture_output=True,
                               text=True, timeout=8,
                               env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'tests'}"})
            expect(p.returncode != 0, "FIFO subject was accepted without an error")
            expect("PolicyError" in p.stderr or "SealError" in p.stderr,
                   f"unexpected error: {p.stderr[-300:]}")
            return "non-regular file refused promptly"

    def subject_size_cap():
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            (subj / "big.bin").write_bytes(b"x" * (2 * 1048576))
            raw = manifest_dict()
            raw["policy"]["max_subject_bytes"] = 1048576
            m = validate(raw)
            return expect_raises(lambda: build_record(m, digest(m), "t", subj), SealError)

    def cleanup():
        before = set(pathlib.Path(tempfile.gettempdir()).glob("seal-probe-*"))
        with Workspace() as w:
            records(w)
        after = set(pathlib.Path(tempfile.gettempdir()).glob("seal-probe-*"))
        expect(not (after - before), f"leftover workdirs: {after - before}")
        return "no leftovers"

    def weird_names():
        with Workspace() as w:
            subj = w.subject("v1", "open('a b\\t c.log','w').write('x')\n").parent
            m = validate(manifest_dict())
            rec = build_record(m, digest(m), "t", subj)
            expect(any("a b" in k for k in rec["probes"]["p1"]["files_delta"]["created"]))
            return "captured"

    r.append(check("symlink inside subject refused", symlink_inside))
    r.append(check("symlink escaping subject refused", symlink_escape))
    r.append(check("FIFO / non-regular file refused", fifo_refused))
    r.append(check("subject size cap enforced", subject_size_cap))
    r.append(check("temporary workdirs cleaned up", cleanup))
    r.append(check("odd file names captured", weird_names))
    return r


# ---------------------------------------------------------------- round 6
def round6():
    r = []

    def tamper_matrix():
        with Workspace() as w:
            m, old, new = records(w)
            report = compare_records(old, new, m)
            base = build_bundle(old, new, report, m)
            cases = {
                "record stdout": lambda b: b["records"]["new"]["probes"]["p1"].update(stdout="hacked"),
                "report overall": lambda b: b["report"].update(overall="CLEAN"),
                "provenance": lambda b: b["provenance"].update(old_record_digest="0" * 64),
                "manifest command": lambda b: b["manifest"]["target"].update(command=["sh", "-c", "rm -rf /"]),
                "observation digest": lambda b: b["records"]["old"]["probes"]["p1"].update(digest="0" * 64),
            }
            for label, mutate in cases.items():
                b = json.loads(json.dumps(base))
                mutate(b)
                expect_raises(lambda b=b: check_bundle(b), SealError)
            return f"{len(cases)} tamper cases refused"

    def malformed_obs():
        with Workspace() as w:
            m, old, new = records(w)
            b = build_bundle(old, new, compare_records(old, new, m), m)
            del b["records"]["old"]["probes"]["p1"]["exit_code"]
            return _clean_error(lambda: check_bundle(b))

    def empty_probes():
        with Workspace() as w:
            m, old, new = records(w)
            old["probes"] = {}
            old["digest"] = digest({k: v for k, v in old.items() if k != "digest"})
            return _clean_error(lambda: compare_records(old, new, m))

    def no_unknown_clean():
        with Workspace() as w:
            m = validate(manifest_dict())
            d = digest(m)
            good = build_record(m, d, "a", w.subject("v1", PROG_V1).parent)
            bad = build_record(m, d, "b", w.subject("v1", PROG_V1).parent)
            bad["probes"]["p1"]["status"] = "timeout"
            bad["probes"]["p1"]["digest"] = digest(
                {k: bad["probes"]["p1"][k] for k in
                 ("status", "stdout", "stderr", "exit_code", "files_delta", "env_names")})
            bad["digest"] = digest({k: v for k, v in bad.items() if k != "digest"})
            rep = compare_records(good, bad, m)
            return expect(rep["overall"] != "CLEAN", "a timeout was reported as CLEAN")

    def swap_subject():
        with Workspace() as w:
            m, old, new = records(w)
            b = build_bundle(old, new, compare_records(old, new, m), m)
            res = reproduce(b, str(w.root / "v1"), str(w.root / "v1"))
            return expect(res["status"] == "MISMATCH")

    def no_trust():
        with Workspace() as w:
            m, old, new = records(w)
            b = build_bundle(old, new, compare_records(old, new, m), m)
            bp = w.root / "b.json"
            bp.write_text(json.dumps(b), encoding="utf-8")
            code, _, err = run_cli("verify", str(bp), "--old", str(w.root / "v1"),
                                   "--new", str(w.root / "v2"))
            expect(code == 3 and "--trust" in err)
            return "refused"

    r.append(check("five tamper cases refused", tamper_matrix))
    r.append(check("malformed observation gives clean error", malformed_obs))
    r.append(check("record with no probes gives clean error", empty_probes))
    r.append(check("timeout verdict is never CLEAN", no_unknown_clean))
    r.append(check("swapped subject detected", swap_subject))
    r.append(check("verify without --trust refused", no_trust))
    return r


def _clean_error(fn):
    try:
        fn()
    except SealError as exc:
        return f"clean {type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"unclean failure {type(exc).__name__}: {exc}") from exc
    raise AssertionError("expected an error, none raised")


# ---------------------------------------------------------------- round 7
def round7():
    r = []

    def repeatable():
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            m = validate(manifest_dict())
            d = digest(m)
            a = build_record(m, d, "a", subj)
            b = build_record(m, d, "b", subj)
            strip = lambda o: {k: v for k, v in o.items() if k not in ("duration_ms",)}  # noqa: E731
            return expect(strip(a["probes"]["p1"]) == strip(b["probes"]["p1"]),
                          "two runs of the same subject differ")

    def path_normalized():
        with Workspace() as w:
            subj = w.subject("v1", "import os; print(os.getcwd())\n").parent
            m = validate(manifest_dict())
            rec = build_record(m, digest(m), "t", subj)
            return expect("<WORKDIR>" in rec["probes"]["p1"]["stdout"])

    def fixed_env():
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            m = validate(manifest_dict())
            names = build_record(m, digest(m), "t", subj)["probes"]["p1"]["env_names"]
            return expect({"TZ", "LC_ALL", "PYTHONHASHSEED", "LANG", "HOME", "PATH"} <= set(names))

    def declared_normalization():
        rules = {"crlf": True, "ansi": False, "timestamps": False}
        expect(normalize("a\r\n", "/w", rules) == "a\n")
        expect("2026-01-02T03:04:05Z" in normalize("2026-01-02T03:04:05Z", "/w", rules))
        return "only declared rules apply"

    def demo_stable():
        from seal.demo import run_demo
        a, b = run_demo(), run_demo()
        return expect(a["unexpected_channels"] == b["unexpected_channels"]
                      and a["overall"] == b["overall"])

    def python_hash_seed():
        with Workspace() as w:
            subj = w.subject("v1", "print(hash('seal'))\n").parent
            m = validate(manifest_dict())
            d = digest(m)
            a = build_record(m, d, "a", subj)["probes"]["p1"]["stdout"]
            b = build_record(m, d, "b", subj)["probes"]["p1"]["stdout"]
            return expect(a == b, "PYTHONHASHSEED not fixed")

    r.append(check("repeated runs are byte-identical", repeatable))
    r.append(check("temporary path normalized", path_normalized))
    r.append(check("deterministic base environment", fixed_env))
    r.append(check("normalization stays declared", declared_normalization))
    r.append(check("demo verdict is stable", demo_stable))
    r.append(check("PYTHONHASHSEED pinned", python_hash_seed))
    return r


# ---------------------------------------------------------------- round 8
def round8():
    r = []

    def full_pipeline():
        with Workspace() as w:
            w.subject("v1", PROG_V1)
            w.subject("v2", PROG_V2_SIDE_EFFECT)
            mf = w.manifest()
            a, b, bundle = w.root / "a.json", w.root / "b.json", w.root / "bundle.json"
            code, _, err = run_cli("record", "--subject", str(w.root / "v1"), "--tag", "before",
                                   "--manifest", str(mf), "--out", str(a))
            expect(code == 0, err)
            code, _, err = run_cli("record", "--subject", str(w.root / "v2"), "--tag", "after",
                                   "--manifest", str(mf), "--out", str(b))
            expect(code == 0, err)
            code, out, err = run_cli("compare", str(a), str(b), "--manifest", str(mf),
                                     "--bundle", str(bundle))
            expect(code == 1 and "UNEXPECTED" in out, out + err)
            code, out, err = run_cli("verify", str(bundle), "--old", str(w.root / "v1"),
                                     "--new", str(w.root / "v2"), "--trust")
            expect(code == 0 and "REPRODUCED" in out, out + err)
            return "record/compare/bundle/verify all correct"

    def module_entry():
        p = subprocess.run([sys.executable, "-m", "seal", "demo", "--json"],
                           cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                           capture_output=True, text=True, timeout=60)
        return expect(p.returncode == 0 and '"passed": true' in p.stdout,
                      p.stdout[-300:] + p.stderr[-300:])

    def launcher_entry():
        p = subprocess.run([sys.executable, str(ROOT / "seal"), "demo", "--json"],
                           capture_output=True, text=True, timeout=60)
        return expect(p.returncode == 0 and '"passed": true' in p.stdout)

    def stdlib_only():
        third_party = {"pytest", "requests", "yaml", "click", "rich", "numpy", "pydantic"}
        bad = []
        for f in (ROOT / "src" / "seal").glob("*.py"):
            for line in f.read_text().splitlines():
                m = re.match(r"\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
                if m and m.group(1) in third_party:
                    bad.append(f"{f.name}: {line.strip()}")
        return expect(not bad, f"third-party imports: {bad}")

    def docs_present():
        needed = ["README.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "GLOSSARY.md",
                  "docs/THREAT_MODEL.md", "docs/06_launch_scorecard.md",
                  "docs/05_architecture_refactor.md", "docs/07_prior_art.md",
                  ".github/workflows/ci.yml"]
        missing = [p for p in needed if not (ROOT / p).exists()]
        return expect(not missing, f"missing: {missing}")

    def prose_gate():
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        problems = []
        if "—" in text or "–" in text:
            problems.append("em dash")
        if re.search(r"not\s+\w+,\s+it'?s", text, re.IGNORECASE):
            problems.append("not X it's Y contrast")
        if re.search(r"\b(no tool in the world|never existed|first ever)\b", text, re.IGNORECASE):
            problems.append("absolute novelty claim")
        return expect(not problems, f"prose issues: {problems}")

    def no_star_promise():
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        return expect("105,000 stars" not in text or "cannot" in text,
                      "README promises a star count")

    r.append(check("full CLI pipeline", full_pipeline))
    r.append(check("python -m seal works", module_entry))
    r.append(check("./seal launcher works", launcher_entry))
    r.append(check("runtime has zero third-party imports", stdlib_only))
    r.append(check("release documents exist", docs_present))
    r.append(check("README passes prose gate", prose_gate))
    r.append(check("no star-count promise", no_star_promise))
    return r


ROUNDS = {
    "01": ("Correctness and public contracts", round1),
    "02": ("Boundary conditions and input validation", round2),
    "03": ("Command execution and sandbox escape", round3),
    "04": ("Secrets, environment and output handling", round4),
    "05": ("Filesystem, special files and resource limits", round5),
    "06": ("Evidence integrity and tampering", round6),
    "07": ("Determinism and portability", round7),
    "08": ("End-to-end pipeline and release artifacts", round8),
}


def main_run(suffix: str) -> int:
    all_results = {}
    for key, (title, fn) in ROUNDS.items():
        started = time.time()
        results = fn()
        payload = {"round": key, "title": title, "elapsed_seconds": round(time.time() - started, 2),
                   "checks": results,
                   "passed": sum(1 for x in results if x["status"] == "PASS"),
                   "failed": sum(1 for x in results if x["status"] == "FAIL")}
        (LOGDIR / f"round-{key}-{suffix}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        all_results[key] = payload
        print(f"round {key}: {payload['passed']} passed, {payload['failed']} failed  ({title})")
        for item in results:
            if item["status"] == "FAIL":
                print(f"    FAIL {item['check']}: {item['detail'][:180]}")
    total_failed = sum(p["failed"] for p in all_results.values())
    total_checks = sum(len(p["checks"]) for p in all_results.values())
    print(f"TOTAL: {total_checks - total_failed}/{total_checks} checks passed")
    return 1 if total_failed else 0


if __name__ == "__main__":
    sys.exit(main_run(sys.argv[1] if len(sys.argv) > 1 else "run"))
