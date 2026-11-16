"""The sealfile manifest: the only place where intent and policy are declared."""
from __future__ import annotations

import copy
import json
import os
import pathlib

from .canonical import CHANNELS, canonical, digest
from .errors import ManifestError

DEFAULT_MANIFEST: dict = {
    "schema": 1,
    "target": {"command": ["python3", "main.py"]},
    "probes": [
        {"name": "default", "args": [], "stdin": "", "env": {}},
    ],
    "normalization": {"crlf": True, "ansi": False, "timestamps": False},
    "nondeterminism": [],
    "intent": {"scope": [], "description": ""},
    "policy": {
        "timeout_seconds": 10,
        "max_output_bytes": 1048576,
        "max_subject_bytes": 64 * 1048576,
        "allowed_commands": ["python3", "python", "sh", "bash", "node", "cat", "echo"],
        "allow_network": False,
    },
}

NORMALIZATION_KEYS = {"crlf", "ansi", "timestamps"}
POLICY_KEYS = {"timeout_seconds", "max_output_bytes", "max_subject_bytes",
               "allowed_commands", "allow_network"}

# Keys that can redirect execution, load code, or move writes outside the
# sandbox. A probe may never set them, even when verify runs with --trust.
RESERVED_ENV_KEYS = frozenset({
    "LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "LD_DEBUG",
    "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH",
    "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT",
    "PATH", "HOME", "SHELL", "IFS", "BASH_ENV", "ENV", "CDPATH",
    "TMPDIR", "TEMP", "TMP", "NODE_OPTIONS", "JAVA_TOOL_OPTIONS",
    "GIT_EXEC_PATH", "PERL5LIB", "RUBYLIB",
})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def validate(raw: dict) -> dict:
    """Validate and fill defaults. Unknown keys are rejected so a typo can
    never silently relax a safety rule."""
    _require(isinstance(raw, dict), "manifest must be a JSON object")
    _require(raw.get("schema") == 1, "manifest.schema must equal 1")

    target = raw.get("target")
    _require(isinstance(target, dict), "manifest.target must be an object")
    command = target.get("command")
    _require(isinstance(command, list) and len(command) >= 1,
             "manifest.target.command must be a non-empty array")
    _require(all(isinstance(part, str) and part and "\x00" not in part
                 for part in command),
             "manifest.target.command entries must be non-empty strings without NUL")
    _require(set(target) == {"command"}, "manifest.target accepts only 'command'")

    probes = raw.get("probes")
    _require(isinstance(probes, list) and len(probes) >= 1,
             "manifest.probes must be a non-empty array")
    seen: set[str] = set()
    for probe in probes:
        _require(isinstance(probe, dict), "each probe must be an object")
        _require(set(probe) <= {"name", "args", "stdin", "env"},
                 "probe has unknown keys: " + ", ".join(sorted(set(probe) - {"name", "args", "stdin", "env"})))
        name = probe.get("name")
        _require(isinstance(name, str) and name and name not in seen,
                 "probe names must be unique non-empty strings")
        seen.add(name)
        args = probe.get("args", [])
        _require(isinstance(args, list) and all(isinstance(a, str) and "\x00" not in a for a in args),
                 "probe.args must be an array of strings without NUL")
        _require(isinstance(probe.get("stdin", ""), str), "probe.stdin must be a string")
        env = probe.get("env", {})
        _require(isinstance(env, dict) and all(isinstance(k, str) and isinstance(v, str)
                                               for k, v in env.items()),
                 "probe.env must map strings to strings")
        _require(all("\x00" not in k and "=" not in k for k in env),
                 "probe.env keys must not contain NUL or '='")
        _require(all(k not in RESERVED_ENV_KEYS for k in env),
                 "probe.env must not set reserved keys: "
                 + ", ".join(sorted(set(env) & RESERVED_ENV_KEYS)))

    normalization = raw.get("normalization", DEFAULT_MANIFEST["normalization"])
    _require(isinstance(normalization, dict) and set(normalization) <= NORMALIZATION_KEYS,
             "manifest.normalization has unknown keys")
    _require(all(isinstance(v, bool) for v in normalization.values()),
             "normalization values must be booleans")

    nondeterminism = raw.get("nondeterminism", [])
    _require(isinstance(nondeterminism, list)
             and all(isinstance(x, str) and x in CHANNELS for x in nondeterminism),
             "manifest.nondeterminism must list observation channels")

    intent = raw.get("intent", DEFAULT_MANIFEST["intent"])
    _require(isinstance(intent, dict) and set(intent) <= {"scope", "description"},
             "manifest.intent has unknown keys")
    scope = intent.get("scope", [])
    _require(isinstance(scope, list) and all(isinstance(x, str) and x in CHANNELS for x in scope),
             "manifest.intent.scope must list observation channels")
    _require(isinstance(intent.get("description", ""), str),
             "manifest.intent.description must be a string")

    policy = raw.get("policy", DEFAULT_MANIFEST["policy"])
    _require(isinstance(policy, dict) and set(policy) <= POLICY_KEYS,
             "manifest.policy has unknown keys")
    timeout = policy.get("timeout_seconds", 10)
    _require(isinstance(timeout, (int, float)) and not isinstance(timeout, bool)
             and 0 < timeout <= 300, "policy.timeout_seconds must be in (0, 300]")
    cap = policy.get("max_output_bytes", 1048576)
    _require(isinstance(cap, int) and not isinstance(cap, bool) and 0 < cap <= 64 * 1048576,
             "policy.max_output_bytes must be in (1, 64 MiB]")
    allowed = policy.get("allowed_commands", DEFAULT_MANIFEST["policy"]["allowed_commands"])
    _require(isinstance(allowed, list) and len(allowed) >= 1
             and all(isinstance(x, str) and x and "/" not in x and "\\" not in x
                     and "\x00" not in x for x in allowed),
             "policy.allowed_commands must be non-empty executable basenames")
    _require(isinstance(policy.get("allow_network", False), bool),
             "policy.allow_network must be a boolean")
    subject_cap = policy.get("max_subject_bytes", 64 * 1048576)
    _require(isinstance(subject_cap, int) and not isinstance(subject_cap, bool)
             and 1024 <= subject_cap <= 512 * 1048576,
             "policy.max_subject_bytes must be in [1 KiB, 512 MiB]")

    merged = copy.deepcopy(DEFAULT_MANIFEST)
    merged["target"] = {"command": list(command)}
    merged["probes"] = [
        {"name": p["name"], "args": list(p.get("args", [])),
         "stdin": p.get("stdin", ""), "env": dict(p.get("env", {}))}
        for p in probes
    ]
    merged["normalization"] = {k: normalization.get(k, v)
                               for k, v in DEFAULT_MANIFEST["normalization"].items()}
    merged["nondeterminism"] = list(nondeterminism)
    merged["intent"] = {"scope": list(scope), "description": intent.get("description", "")}
    merged["policy"] = {
        "timeout_seconds": timeout,
        "max_output_bytes": cap,
        "max_subject_bytes": subject_cap,
        "allowed_commands": list(allowed),
        "allow_network": policy.get("allow_network", False),
    }
    return merged


def load(path: str | os.PathLike) -> tuple[dict, str]:
    p = pathlib.Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {p}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest {p}: {exc}") from exc
    validated = validate(raw)
    return validated, digest(validated)


def write_default(path: str | os.PathLike, *, force: bool = False) -> str:
    p = pathlib.Path(path)
    if p.exists() and not force:
        raise ManifestError(f"refusing to overwrite existing manifest: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(DEFAULT_MANIFEST, indent=2, ensure_ascii=False) + "\n"
    p.write_text(text, encoding="utf-8")
    return text


def manifest_digest(manifest: dict) -> str:
    return digest(manifest)


def summary(manifest: dict) -> str:
    return canonical({
        "probes": [p["name"] for p in manifest["probes"]],
        "intent": manifest["intent"]["scope"],
        "timeout": manifest["policy"]["timeout_seconds"],
        "allowed": manifest["policy"]["allowed_commands"],
    })
