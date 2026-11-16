"""Self-contained demo: catch a behaviour change that a passing test misses.

Two versions of a tiny program print the same line. The second one also
writes a file. A stdout assertion passes on both. A normal review of the
printed output sees nothing. seal records the full observation surface and
reports an UNEXPECTED channel.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import tempfile

from .compare import compare_records, UNEXPECTED
from .manifest import validate
from .canonical import digest
from .render import render_report
from .runner import build_record

V1 = 'print("order total: 42")\n'
V2 = ('print("order total: 42")\n'
      'with open("audit.log", "w", encoding="utf-8") as f:\n'
      '    f.write("telemetry=on\\n")\n')

MANIFEST = {
    "schema": 1,
    "target": {"command": ["python3", "main.py"]},
    "probes": [{"name": "prints_total", "args": [], "stdin": "", "env": {}}],
    "normalization": {"crlf": True, "ansi": False, "timestamps": False},
    "nondeterminism": [],
    "intent": {"scope": [], "description": "no behaviour change was declared"},
    "policy": {
        "timeout_seconds": 10,
        "max_output_bytes": 1048576,
        "allowed_commands": ["python3"],
        "allow_network": False,
    },
}


def run_demo(*, keep: bool = False) -> dict:
    root = pathlib.Path(tempfile.mkdtemp(prefix="seal-demo-"))
    try:
        v1 = root / "v1"
        v2 = root / "v2"
        v1.mkdir()
        v2.mkdir()
        (v1 / "main.py").write_text(V1, encoding="utf-8")
        (v2 / "main.py").write_text(V2, encoding="utf-8")
        manifest = validate(MANIFEST)
        mdigest = digest(manifest)
        old = build_record(manifest, mdigest, "before", v1)
        new = build_record(manifest, mdigest, "after", v2)
        report = compare_records(old, new, manifest)
        unexpected = report["counts"][UNEXPECTED]
        result = {
            "demo": "behaviour change hidden from stdout assertions",
            "stdout_before": old["probes"]["prints_total"]["stdout"].strip(),
            "stdout_after": new["probes"]["prints_total"]["stdout"].strip(),
            "unexpected_channels": [
                f"{probe}/{channel}"
                for probe, channels in report["results"].items()
                for channel, item in channels.items()
                if item["verdict"] == UNEXPECTED
            ],
            "overall": report["overall"],
            "report": render_report(report),
            "passed": unexpected >= 1,
            "kept_dir": str(root) if keep else None,
        }
        return result
    finally:
        if not keep:
            shutil.rmtree(root, ignore_errors=True)


def demo_json(result: dict) -> str:
    return json.dumps({k: v for k, v in result.items() if k != "report"},
                      indent=2, ensure_ascii=False)
