#!/usr/bin/env python3
"""Behaviour lock for the architecture pass.

Runs a fixed CLI transcript and stores a normalized golden copy. The manager
runs `--check` before and after any refactor. A single changed byte fails.

    python3 tests/behavior_lock.py --write   # create the baseline
    python3 tests/behavior_lock.py --check  # verify against the baseline
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from seal.canonical import canonical, digest  # noqa: E402
from seal.cli import main  # noqa: E402
from _support import PROG_V1, PROG_V2_SIDE_EFFECT, manifest_dict  # noqa: E402

BASELINE = ROOT / "evidence" / "baseline" / "behavior_lock.json"


def _run_cli(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(args)
    return {"args": args, "exit_code": code, "stdout": out.getvalue(), "stderr": err.getvalue()}


def transcript() -> tuple[list[dict], str]:
    with tempfile.TemporaryDirectory(prefix="seal-lock-") as td:
        root = pathlib.Path(td)
        v1, v2 = root / "v1", root / "v2"
        v1.mkdir()
        v2.mkdir()
        (v1 / "main.py").write_text(PROG_V1, encoding="utf-8")
        (v2 / "main.py").write_text(PROG_V2_SIDE_EFFECT, encoding="utf-8")
        mf = root / "sealfile.json"
        mf.write_text(json.dumps(manifest_dict(), indent=2) + "\n", encoding="utf-8")
        a, b, bundle = root / "a.json", root / "b.json", root / "bundle.json"

        results = []
        p = subprocess.run([sys.executable, str(ROOT / "seal"), "--version"],
                           capture_output=True, text=True)
        results.append({"args": ["--version"], "exit_code": p.returncode,
                        "stdout": p.stdout, "stderr": p.stderr})
        results.append(_run_cli(["init", "--manifest", str(mf), "--force"]))
        mf.write_text(json.dumps(manifest_dict(), indent=2) + "\n", encoding="utf-8")
        results.append(_run_cli(["record", "--subject", str(v1), "--tag", "before",
                                 "--manifest", str(mf), "--out", str(a)]))
        results.append(_run_cli(["record", "--subject", str(v2), "--tag", "after",
                                 "--manifest", str(mf), "--out", str(b)]))
        results.append(_run_cli(["compare", str(a), str(b), "--manifest", str(mf)]))
        results.append(_run_cli(["compare", str(a), str(b), "--manifest", str(mf),
                                 "--json"]))
        results.append(_run_cli(["compare", str(a), str(b), "--manifest", str(mf),
                                 "--bundle", str(bundle)]))
        results.append(_run_cli(["verify", str(bundle), "--old", str(v1),
                                 "--new", str(v2), "--trust"]))
        results.append(_run_cli(["demo"]))
        results.append(_run_cli(["demo", "--json"]))

        def walk(obj):
            if isinstance(obj, dict):
                return {k: walk(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [walk(v) for v in obj]
            if isinstance(obj, str):
                return obj.replace(str(root), "<ROOT>").replace(td, "<ROOT>")
            return obj
        normalized = walk(results)
        return normalized, digest(normalized)


def main_run() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = ap.parse_args()
    current, current_hash = transcript()
    if args.write:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(
            {"schema": 1, "hash": current_hash, "transcript": current},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote baseline {BASELINE} ({current_hash[:16]})")
        return 0
    try:
        saved = json.loads(BASELINE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read baseline: {exc}", file=sys.stderr)
        return 2
    if saved["hash"] != current_hash or saved["transcript"] != current:
        print("BEHAVIOUR CHANGED")
        print(f"  recorded: {saved['hash'][:16]}")
        print(f"  current : {current_hash[:16]}")
        for old, new in zip(saved["transcript"], current):
            if old != new:
                print(f"  first difference in: {new.get('args')}")
                print(f"    recorded stdout: {old.get('stdout', '')[:200]!r}")
                print(f"    current  stdout: {new.get('stdout', '')[:200]!r}")
                break
        return 1
    print(f"BEHAVIOUR LOCKED ({current_hash[:16]})")
    return 0


if __name__ == "__main__":
    sys.exit(main_run())
