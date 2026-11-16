"""Bundle, verification and CLI tests."""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import unittest

from seal.bundle import build_bundle, check_bundle, reproduce
from seal.canonical import digest
from seal.cli import main
from seal.compare import compare_records
from seal.demo import run_demo
from seal.errors import SealError
from seal.manifest import validate
from seal.runner import build_record

from _support import PROG_V1, PROG_V2_SIDE_EFFECT, Workspace, manifest_dict


def make_records(w: Workspace, v2: str = PROG_V2_SIDE_EFFECT):
    m = validate(manifest_dict())
    d = digest(m)
    old = build_record(m, d, "before", w.subject("v1", PROG_V1).parent)
    new = build_record(m, d, "after", w.subject("v2", v2).parent)
    return m, old, new


class BundleTests(unittest.TestCase):
    def test_roundtrip_and_reproduction(self):
        with Workspace() as w:
            m, old, new = make_records(w)
            report = compare_records(old, new, m)
            bundle = build_bundle(old, new, report, m)
            check_bundle(bundle)
            result = reproduce(bundle, str(w.root / "v1"), str(w.root / "v2"))
            self.assertEqual(result["status"], "REPRODUCED", result["mismatches"])
            self.assertTrue(result["verdict_reproduced"])

    def test_any_edit_is_detected(self):
        with Workspace() as w:
            m, old, new = make_records(w)
            bundle = build_bundle(old, new, compare_records(old, new, m), m)
            bundle["records"]["new"]["probes"]["p1"]["stdout"] = "changed"
            with self.assertRaises(SealError):
                check_bundle(bundle)

    def test_report_tamper_is_detected(self):
        with Workspace() as w:
            m, old, new = make_records(w)
            bundle = build_bundle(old, new, compare_records(old, new, m), m)
            bundle["report"]["overall"] = "CLEAN"
            with self.assertRaises(SealError):
                check_bundle(bundle)

    def test_provenance_tamper_is_detected(self):
        with Workspace() as w:
            m, old, new = make_records(w)
            bundle = build_bundle(old, new, compare_records(old, new, m), m)
            bundle["provenance"]["old_record_digest"] = "0" * 64
            with self.assertRaises(SealError):
                check_bundle(bundle)

    def test_reproduction_detects_a_swapped_subject(self):
        with Workspace() as w:
            m, old, new = make_records(w)
            bundle = build_bundle(old, new, compare_records(old, new, m), m)
            result = reproduce(bundle, str(w.root / "v1"), str(w.root / "v1"))
            self.assertEqual(result["status"], "MISMATCH")
            self.assertTrue(result["mismatches"])


class CliTests(unittest.TestCase):
    def test_demo_finds_hidden_change(self):
        result = run_demo()
        self.assertTrue(result["passed"])
        self.assertIn("prints_total/files_delta", result["unexpected_channels"])
        self.assertEqual(result["stdout_before"], result["stdout_after"])

    def test_demo_cli_exit_zero(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["demo"])
        self.assertEqual(code, 0)
        self.assertIn("seal caught", out.getvalue())

    def test_verify_without_trust_is_refused(self):
        with Workspace() as w:
            m, old, new = make_records(w)
            report = compare_records(old, new, m)
            bundle = build_bundle(old, new, report, m)
            bp = w.root / "bundle.json"
            bp.write_text(json.dumps(bundle), encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = main(["verify", str(bp), "--old", str(w.root / "v1"),
                             "--new", str(w.root / "v2")])
            self.assertEqual(code, 3)
            self.assertIn("--trust", err.getvalue())

    def test_init_record_compare_pipeline(self):
        with Workspace() as w:
            w.subject("v1", PROG_V1)
            w.subject("v2", PROG_V2_SIDE_EFFECT)
            mf = w.manifest()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["init", "--manifest", str(mf), "--force"]), 0)
            # init writes defaults; overwrite with the fixture manifest
            mf.write_text(json.dumps(manifest_dict(), indent=2) + "\n", encoding="utf-8")
            old_path, new_path = w.root / "a.json", w.root / "b.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["record", "--subject", str(w.root / "v1"),
                                       "--tag", "before", "--manifest", str(mf),
                                       "--out", str(old_path)]), 0)
                self.assertEqual(main(["record", "--subject", str(w.root / "v2"),
                                       "--tag", "after", "--manifest", str(mf),
                                       "--out", str(new_path)]), 0)
            self.assertTrue(old_path.is_file())
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["compare", str(old_path), str(new_path),
                             "--manifest", str(mf)])
            self.assertEqual(code, 1)
            self.assertIn("UNEXPECTED", out.getvalue())

    def test_tag_rejects_path_traversal(self):
        with Workspace() as w:
            w.subject("v1", PROG_V1)
            mf = w.manifest()
            with contextlib.redirect_stderr(io.StringIO()):
                code = main(["record", "--subject", str(w.root / "v1"),
                             "--tag", "../escape", "--manifest", str(mf)])
            self.assertEqual(code, 3)

    def test_version_flag(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            main(["--version"])
        self.assertIn("seal 0.1.0", out.getvalue())

    def test_verify_cli_reproduces(self):
        with Workspace() as w:
            m, old, new = make_records(w)
            report = compare_records(old, new, m)
            bundle = build_bundle(old, new, report, m)
            bp = w.root / "bundle.json"
            bp.write_text(json.dumps(bundle), encoding="utf-8")
            err = io.StringIO()
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main(["verify", str(bp), "--old", str(w.root / "v1"),
                             "--new", str(w.root / "v2"), "--trust"])
            self.assertEqual(code, 0, out.getvalue() + err.getvalue())
            self.assertIn("REPRODUCED", out.getvalue())


if __name__ == "__main__":
    unittest.main()
