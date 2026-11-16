#!/usr/bin/env python3
"""Spawn complete_install.py detached and exit."""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/data/workspace")
LOG = ROOT / "complete_install.log"
PID = ROOT / "complete_install.pid"

with LOG.open("wb") as log:
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "complete_install.py")],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
PID.write_text(str(proc.pid) + "\n", encoding="utf-8")
print(f"started pid {proc.pid}")
