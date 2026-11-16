"""Contract tests. Written before the implementation was accepted."""
from __future__ import annotations

import json
import unittest

from seal.canonical import canonical, digest, normalize, redact
from seal.compare import compare_records
from seal.errors import ManifestError
from seal.manifest import load, validate, write_default
from seal.runner import build_record

from _support import PROG_V1, PROG_V2_SIDE_EFFECT, PROG_V2_STDOUT, Workspace, manifest_dict


class CanonicalTests(unittest.TestCase):
    def test_key_order_does_not_change_digest(self):
        self.assertEqual(digest({"a": 1, "b": 2}), digest({"b": 2, "a": 1}))

    def test_unicode_is_stable(self):
        self.assertEqual(canonical({"k": "中文"}), '{"k":"中文"}')

    def test_normalization_is_declared_not_automatic(self):
        rules = {"crlf": True, "ansi": False, "timestamps": False}
        self.assertEqual(normalize("a\r\nb", "/tmp/x", rules), "a\nb")
        self.assertIn("<TIMESTAMP>", normalize("2026-01-02T03:04:05Z", "/tmp/x",
                                              {**rules, "timestamps": True}))
        self.assertIn("2026-01-02T03:04:05Z", normalize("2026-01-02T03:04:05Z", "/tmp/x", rules))
        self.assertEqual(normalize("/tmp/x/out.txt", "/tmp/x", rules), "<WORKDIR>/out.txt")

    def test_redaction_replaces_secret_values(self):
        self.assertEqual(redact("token=abc12345 end", ["abc12345"]), "token=<redacted> end")
        self.assertEqual(redact("short", ["ab"]), "short")


class ManifestTests(unittest.TestCase):
    def test_defaults_are_complete(self):
        m = validate(manifest_dict())
        self.assertEqual(m["policy"]["timeout_seconds"], 10)
        self.assertEqual(m["intent"]["scope"], [])
        self.assertEqual(m["normalization"]["timestamps"], False)

    def test_unknown_policy_key_rejected(self):
        raw = manifest_dict()
        raw["policy"]["shell"] = True
        with self.assertRaises(ManifestError):
            validate(raw)

    def test_duplicate_probe_names_rejected(self):
        raw = manifest_dict(probes=[{"name": "a"}, {"name": "a"}])
        with self.assertRaises(ManifestError):
            validate(raw)

    def test_bad_scope_rejected(self):
        with self.assertRaises(ManifestError):
            validate(manifest_dict(scope=["stdout", "magic"]))

    def test_timeout_bounds(self):
        for value in (0, -1, 301, "10", True):
            with self.subTest(value=value), self.assertRaises(ManifestError):
                validate(manifest_dict(timeout=value))

    def test_nul_in_command_rejected(self):
        with self.assertRaises(ManifestError):
            validate(manifest_dict(command=["python3", "bad\x00arg"]))

    def test_allowed_commands_must_be_basenames(self):
        with self.assertRaises(ManifestError):
            validate(manifest_dict(allowed=["/bin/sh"]))

    def test_init_refuses_overwrite(self):
        with Workspace() as w:
            p = w.root / "sealfile.json"
            write_default(p)
            with self.assertRaises(ManifestError):
                write_default(p)
            write_default(p, force=True)
            loaded, _ = load(p)
            self.assertEqual(loaded["schema"], 1)


class RunnerTests(unittest.TestCase):
    def test_captures_full_surface(self):
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            m = validate(manifest_dict())
            rec = build_record(m, digest(m), "before", subj)
            obs = rec["probes"]["p1"]
            self.assertEqual(obs["stdout"], "total: 42\n")
            self.assertEqual(obs["exit_code"], 0)
            self.assertEqual(obs["status"], "ok")
            self.assertEqual(obs["files_delta"]["created"], {})

    def test_detects_side_effect_that_stdout_assertion_misses(self):
        with Workspace() as w:
            m = validate(manifest_dict())
            d = digest(m)
            old = build_record(m, d, "before", w.subject("v1", PROG_V1).parent)
            new = build_record(m, d, "after", w.subject("v2", PROG_V2_SIDE_EFFECT).parent)
            self.assertEqual(old["probes"]["p1"]["stdout"], new["probes"]["p1"]["stdout"])
            self.assertIn("audit.log", new["probes"]["p1"]["files_delta"]["created"])

    def test_secrets_are_never_stored(self):
        with Workspace() as w:
            subj = w.subject("v1", "import os; print(os.environ.get('API_TOKEN'))\n").parent
            raw = manifest_dict()
            raw["probes"] = [{"name": "p1", "args": [], "stdin": "",
                              "env": {"API_TOKEN": "supersecret-1234"}}]
            m = validate(raw)
            rec = build_record(m, digest(m), "before", subj)
            out = json.dumps(rec)
            self.assertNotIn("supersecret-1234", out)
            self.assertIn("<redacted>", rec["probes"]["p1"]["stdout"])

    def test_env_values_are_not_recorded(self):
        with Workspace() as w:
            subj = w.subject("v1", PROG_V1).parent
            raw = manifest_dict()
            raw["probes"] = [{"name": "p1", "env": {"MY_VAR": "visible-value"}}]
            rec = build_record(validate(raw), digest(validate(raw)), "before", subj)
            self.assertIn("MY_VAR", rec["probes"]["p1"]["env_names"])
            self.assertNotIn("visible-value", json.dumps(rec["probes"]["p1"]["env_names"]))

    def test_timeout_produces_unknown_status(self):
        with Workspace() as w:
            subj = w.subject("v1", "import time; time.sleep(5)\n").parent
            m = validate(manifest_dict(timeout=0.2))
            rec = build_record(m, digest(m), "before", subj)
            self.assertEqual(rec["probes"]["p1"]["status"], "timeout")

    def test_output_cap_is_enforced(self):
        with Workspace() as w:
            subj = w.subject("v1", "print('x' * 100000)\n").parent
            m = validate(manifest_dict(cap=512))
            rec = build_record(m, digest(m), "before", subj)
            obs = rec["probes"]["p1"]
            self.assertEqual(obs["status"], "output_capped")
            self.assertEqual(len(obs["stdout"]), 512)


class CompareTests(unittest.TestCase):
    def _pair(self, scope=None, nondeterminism=None, v2=PROG_V2_STDOUT):
        w = Workspace()
        m = validate(manifest_dict(scope=scope, nondeterminism=nondeterminism))
        d = digest(m)
        old = build_record(m, d, "before", w.subject("v1", PROG_V1).parent)
        new = build_record(m, d, "after", w.subject("v2", v2).parent)
        return w, m, old, new

    def test_clean_when_identical(self):
        w, m, old, new = self._pair(v2=PROG_V1)
        try:
            report = compare_records(old, new, m)
            self.assertEqual(report["overall"], "CLEAN")
            self.assertEqual(report["counts"]["UNEXPECTED"], 0)
        finally:
            w.close()

    def test_unexpected_outside_scope(self):
        w, m, old, new = self._pair()
        try:
            report = compare_records(old, new, m)
            self.assertEqual(report["overall"], "UNEXPECTED")
            self.assertEqual(report["results"]["p1"]["stdout"]["verdict"], "UNEXPECTED")
        finally:
            w.close()

    def test_intended_inside_scope(self):
        w, m, old, new = self._pair(scope=["stdout"])
        try:
            report = compare_records(old, new, m)
            self.assertEqual(report["overall"], "INTENDED")
            self.assertEqual(report["results"]["p1"]["stdout"]["verdict"], "INTENDED")
        finally:
            w.close()

    def test_unknown_never_becomes_same(self):
        w, m, old, new = self._pair(nondeterminism=["stdout"])
        try:
            report = compare_records(old, new, m)
            self.assertEqual(report["results"]["p1"]["stdout"]["verdict"], "UNKNOWN")
            self.assertEqual(report["overall"], "INCOMPLETE")
        finally:
            w.close()

    def test_manifest_drift_refused(self):
        w, m, old, new = self._pair()
        try:
            new["manifest_digest"] = "0" * 64
            with self.assertRaises(Exception):
                compare_records(old, new, m)
        finally:
            w.close()

    def test_tampered_record_refused(self):
        w, m, old, new = self._pair()
        try:
            old["probes"]["p1"]["stdout"] = "hacked"
            with self.assertRaises(Exception):
                compare_records(old, new, m)
        finally:
            w.close()


if __name__ == "__main__":
    unittest.main()
