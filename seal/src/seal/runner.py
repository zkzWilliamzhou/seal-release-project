"""Sandboxed probe execution and observation capture.

Safety decisions live here and nowhere else:
  * no shell, argv only
  * a fresh temporary working directory per probe
  * the subject tree is copied, never executed in place
  * symlinks and non-regular files in the subject are rejected
  * the subject tree size is bounded
  * a subject-relative executable is remapped into the copied workdir
  * wall-clock timeout kills the whole process group
  * output cap
  * secret values are redacted before anything is stored
  * only declared environment names are recorded
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import platform
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import time

from .canonical import CHANNELS, canonical, digest, normalize, redact
from .errors import PolicyError

SECRET_NAME_RE = re.compile(
    r"(TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL|PRIVATE|AUTH)", re.IGNORECASE
)
BASE_ENV_KEYS = ("PATH", "LANG", "LC_ALL", "TZ", "PYTHONHASHSEED", "HOME")


def _validate_subject_tree(root: pathlib.Path, max_bytes: int) -> None:
    """Reject anything that can escape, hang, or exhaust the runner."""
    root = root.resolve()
    total = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames:
            p = pathlib.Path(dirpath) / name
            if p.is_symlink():
                raise PolicyError(f"symlink in subject tree is refused: {p.relative_to(root)}")
            try:
                p.resolve().relative_to(root)
            except ValueError as exc:
                raise PolicyError(f"directory escapes subject tree: {p}") from exc
        dirnames.sort()
        for name in sorted(filenames):
            p = pathlib.Path(dirpath) / name
            if p.is_symlink():
                raise PolicyError(f"symlink in subject tree is refused: {p.relative_to(root)}")
            info = p.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise PolicyError(
                    f"non-regular file in subject tree is refused: {p.relative_to(root)}")
            total += info.st_size
            if total > max_bytes:
                raise PolicyError(
                    f"subject tree exceeds policy.max_subject_bytes ({max_bytes} bytes)")
    if total == 0:
        raise PolicyError("subject tree contains no regular files")


def _snapshot(root: pathlib.Path) -> dict:
    out: dict = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            p = pathlib.Path(dirpath) / name
            rel = str(p.relative_to(root))
            try:
                data = p.read_bytes()
            except OSError:
                out[rel] = {"error": "unreadable"}
                continue
            out[rel] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    return out


def _delta(before: dict, after: dict) -> dict:
    result: dict = {"created": {}, "modified": {}, "deleted": []}
    for rel, info in after.items():
        if rel not in before:
            result["created"][rel] = info
        elif before[rel] != info:
            result["modified"][rel] = info
    for rel in before:
        if rel not in after:
            result["deleted"].append(rel)
    result["deleted"].sort()
    return result


def _env_for(probe_env: dict, workdir: str) -> tuple[dict, list[str]]:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONHASHSEED": "0",
        "HOME": workdir,
    }
    for key in BASE_ENV_KEYS:
        env.setdefault(key, "")
    for key, value in probe_env.items():
        env[key] = value
    return env, sorted(env.keys())


def _check_command(argv: list[str], allowed: list[str],
                   subject: pathlib.Path) -> str | None:
    """Return the subject-relative executable path, or None for a basename."""
    if not argv:
        raise PolicyError("empty command")
    exe = argv[0]
    if "\x00" in exe:
        raise PolicyError("NUL in executable")
    for arg in argv[1:]:
        if "\x00" in arg:
            raise PolicyError("NUL in argument")
    if "/" in exe or "\\" in exe:
        candidate = (subject / exe).resolve() if not os.path.isabs(exe) else pathlib.Path(exe).resolve()
        try:
            rel = candidate.relative_to(subject.resolve())
        except ValueError as exc:
            raise PolicyError(f"executable path escapes subject: {exe}") from exc
        if not candidate.is_file():
            raise PolicyError(f"executable not found inside subject: {exe}")
        return str(rel)
    if exe not in allowed:
        raise PolicyError(f"executable not in policy.allowed_commands: {exe}")
    return None


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _run_argv(argv: list[str], cwd: str, env: dict, stdin: str,
              timeout: float) -> tuple[str, bytes, bytes, int | None]:
    """Run argv in its own session. On timeout, kill the whole group."""
    proc = subprocess.Popen(
        argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=False, start_new_session=True,
    )
    try:
        stdout_b, stderr_b = proc.communicate(input=stdin.encode("utf-8"), timeout=timeout)
        return "ok", stdout_b, stderr_b, proc.returncode
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        try:
            stdout_b, stderr_b = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            stdout_b, stderr_b = exc.stdout or b"", exc.stderr or b""
        return "timeout", stdout_b, stderr_b, None


def run_probe(manifest: dict, subject: pathlib.Path, probe: dict,
              *, workdir_root: str | None = None) -> dict:
    """Run one probe in a fresh copy of ``subject`` and return its observation."""
    policy = manifest["policy"]
    rules = manifest["normalization"]
    subject = subject.resolve()
    if not subject.is_dir():
        raise PolicyError(f"subject is not a directory: {subject}")
    _validate_subject_tree(subject, policy["max_subject_bytes"])

    root = pathlib.Path(workdir_root or tempfile.mkdtemp(prefix="seal-probe-"))
    created_root = workdir_root is None
    workdir = root / "work"
    try:
        workdir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(subject, workdir, dirs_exist_ok=True, symlinks=False)
        before = _snapshot(workdir)

        argv = list(manifest["target"]["command"]) + list(probe.get("args", []))
        exe_rel = _check_command(argv, policy["allowed_commands"], subject)
        if exe_rel is not None:
            # Remap into the copy so the executed program cannot read or write
            # the original subject tree through its own path.
            argv = [str(workdir / exe_rel)] + argv[1:]

        env, env_names = _env_for(probe.get("env", {}), str(workdir))
        secret_values = [v for k, v in probe.get("env", {}).items()
                         if SECRET_NAME_RE.search(k)] + [
            os.environ.get(k, "") for k in os.environ if SECRET_NAME_RE.search(k)
        ]
        secret_values = [v for v in secret_values if v]

        cap = policy["max_output_bytes"]
        started = time.monotonic()
        try:
            status, stdout_b, stderr_b, exit_code = _run_argv(
                argv, str(workdir), env, probe.get("stdin", ""),
                policy["timeout_seconds"])
        except (OSError, ValueError) as exc:
            status, stdout_b, stderr_b, exit_code = (
                "error", b"", str(exc).encode("utf-8"), None)
        elapsed_ms = int((time.monotonic() - started) * 1000)

        capped = False
        if len(stdout_b) > cap:
            stdout_b, capped = stdout_b[:cap], True
        if len(stderr_b) > cap:
            stderr_b, capped = stderr_b[:cap], True
        if capped:
            status = "output_capped"

        stdout = normalize(redact(_decode(stdout_b), secret_values), str(workdir), rules)
        stderr = normalize(redact(_decode(stderr_b), secret_values), str(workdir), rules)
        after = _snapshot(workdir)
        files_delta = _delta(before, after)
        files_delta = {
            "created": {normalize(k, str(workdir), rules): v for k, v in files_delta["created"].items()},
            "modified": {normalize(k, str(workdir), rules): v for k, v in files_delta["modified"].items()},
            "deleted": [normalize(k, str(workdir), rules) for k in files_delta["deleted"]],
        }

        body = {
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "files_delta": files_delta,
            "env_names": env_names,
        }
        return {**body, "duration_ms": elapsed_ms, "digest": digest(body)}
    finally:
        if created_root:
            shutil.rmtree(root, ignore_errors=True)


def build_record(manifest: dict, manifest_digest_hex: str, tag: str,
                 subject: str | os.PathLike, *, workdir_root: str | None = None) -> dict:
    subject_path = pathlib.Path(subject)
    probes: dict = {}
    for probe in manifest["probes"]:
        probes[probe["name"]] = run_probe(manifest, subject_path, probe,
                                          workdir_root=workdir_root)
    record = {
        "schema": 1,
        "tag": tag,
        "manifest_digest": manifest_digest_hex,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "system": platform.system(),
            "machine": platform.machine(),
            "seal_version": __import__("seal").__version__,
            "policy": manifest["policy"],
        },
        "probes": probes,
    }
    record["digest"] = digest({k: v for k, v in record.items() if k != "digest"})
    return record


def record_body(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "digest"}


def verify_record_digest(record: dict) -> bool:
    probes = record.get("probes")
    if not isinstance(probes, dict) or not probes:
        return False
    return record.get("digest") == digest(record_body(record))


def observation_body(observation: dict) -> dict | None:
    if not all(k in observation for k in CHANNELS):
        return None
    return {k: observation[k] for k in CHANNELS}


def verify_observation_digest(observation: dict) -> bool:
    body = observation_body(observation)
    return body is not None and observation.get("digest") == digest(body)


def canonical_observations(record: dict) -> str:
    return canonical(record["probes"])
