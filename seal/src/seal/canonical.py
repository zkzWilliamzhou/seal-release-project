"""Canonical serialization, digests, redaction and declared normalization.

Nothing in this module guesses. A byte is replaced only when the manifest
declares the corresponding normalization rule, or when the value is the
per-run temporary working directory (which must be replaced for any two
runs to be comparable at all).
"""
from __future__ import annotations

import hashlib
import json
import re

SCHEMA = 1

CHANNELS = ("status", "stdout", "stderr", "exit_code", "files_delta", "env_names")

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
TIMESTAMP_RE = re.compile(
    r"\b(?:20[0-9]{2}-[01][0-9]-[0-3][0-9][T ][0-2][0-9]:[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-2][0-9]:[0-5][0-9])?|1[0-9]{9})\b"
)
WORKDIR_TOKEN = "<WORKDIR>"


def canonical(obj: object) -> str:
    """Stable, key-sorted, ASCII-safe JSON text used for every digest."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def digest(obj: object) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def redact(text: str, secret_values: list[str]) -> str:
    """Replace known secret values before any text reaches a bundle."""
    for value in secret_values:
        if value and len(value) >= 4:
            text = text.replace(value, "<redacted>")
    return text


def normalize(text: str, workdir: str, rules: dict) -> str:
    """Apply only declared normalizations. Unknown rules are ignored silently
    by the caller's manifest validation, which rejects unknown keys."""
    if workdir:
        text = text.replace(workdir, WORKDIR_TOKEN)
    if rules.get("crlf", True):
        text = text.replace("\r\n", "\n")
    if rules.get("ansi", False):
        text = ANSI_RE.sub("", text)
    if rules.get("timestamps", False):
        text = TIMESTAMP_RE.sub("<TIMESTAMP>", text)
    return text


def observation_digest(body: dict) -> str:
    return digest(body)
