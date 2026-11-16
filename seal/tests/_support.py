"""Shared fixtures. Standard library only."""
from __future__ import annotations

import json
import pathlib
import tempfile

PROG_V1 = 'print("total: 42")\n'
PROG_V2_SIDE_EFFECT = (
    'print("total: 42")\n'
    'with open("audit.log", "w", encoding="utf-8") as f:\n'
    '    f.write("telemetry=on\\n")\n'
)
PROG_V2_STDOUT = 'print("total: 43")\n'


def manifest_dict(*, scope=None, nondeterminism=None, allowed=None,
                  timeout=10, cap=1048576, command=None, probes=None):
    return {
        "schema": 1,
        "target": {"command": ["python3", "main.py"] if command is None else command},
        "probes": probes or [{"name": "p1", "args": [], "stdin": "", "env": {}}],
        "normalization": {"crlf": True, "ansi": False, "timestamps": False},
        "nondeterminism": nondeterminism or [],
        "intent": {"scope": scope or [], "description": "declared scope"},
        "policy": {
            "timeout_seconds": timeout,
            "max_output_bytes": cap,
            "allowed_commands": ["python3"] if allowed is None else allowed,
            "allow_network": False,
        },
    }


class Workspace:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="seal-test-")
        self.root = pathlib.Path(self.tmp.name)

    def write(self, rel: str, text: str) -> pathlib.Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def manifest(self, **kwargs) -> pathlib.Path:
        p = self.root / "sealfile.json"
        p.write_text(json.dumps(manifest_dict(**kwargs), indent=2) + "\n", encoding="utf-8")
        return p

    def subject(self, name: str, code: str) -> pathlib.Path:
        return self.write(f"{name}/main.py", code)

    def close(self):
        self.tmp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
