#!/usr/bin/env python3
"""Complete the skills install from cached bytes plus linked companion files.

The full CDN directory crawl was too slow for the sandbox timeout. This script
instead walks every installed Markdown file, resolves its relative links, and
fetches only the missing companion files. It then writes skills-lock.json and
the install report from the bytes actually on disk.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import pathlib
import posixpath
import re
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path("/data/workspace")
DEST = ROOT / "seal" / ".agents" / "skills"
LOCK = ROOT / "seal" / "skills-lock.json"
REPORT = ROOT / "seal" / "docs" / "SKILL_INSTALL_REPORT.md"
CDN = "https://cdn.jsdelivr.net"
REF = "main"

VENDOR_REPO = {
    "anthropics": "anthropics/skills",
    "mattpocock": "mattpocock/skills",
    "superpowers": "obra/superpowers",
    "vercel-labs": "vercel-labs/skills",
    "stop-slop": "hardikpandya/stop-slop",
}
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tiff",
    ".woff", ".woff2", ".ttf", ".eot", ".otf", ".mp3", ".mp4", ".webm",
    ".wav", ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".pdf",
    ".docx", ".pptx", ".xlsx", ".exe", ".dll", ".so", ".dylib", ".bin",
}
NO_EXT_ALLOWED = {
    "LICENSE", "Makefile", "Dockerfile", "NOTICE", "CODEOWNERS",
    "CONTRIBUTING", "SECURITY", "README", "CHANGELOG", "SKILL",
    "CONTEXT", "CLAUDE", "GLOSSARY", "AGENTS", "pyproject.toml",
    "package.json",
}
MAX_FILE_BYTES = 1024 * 1024
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def get(url: str) -> bytes:
    try:
        p = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "12", url],
            capture_output=True, timeout=15,
        )
        if p.returncode == 0:
            return p.stdout
    except Exception:
        pass
    return b""


def vendor_and_rel(path: pathlib.Path) -> tuple[str, str] | None:
    rel = path.relative_to(DEST).as_posix()
    parts = rel.split("/", 1)
    if len(parts) != 2 or parts[0] not in VENDOR_REPO:
        return None
    return parts[0], parts[1]


def resolve_link(md: pathlib.Path, target: str) -> tuple[str, str, pathlib.Path] | None:
    t = target.strip()
    if t.startswith("<") and t.endswith(">"):
        t = t[1:-1]
    t = t.split("#", 1)[0].split("?", 1)[0].strip()
    if not t or t.startswith(("http://", "https://", "mailto:", "/")):
        return None
    info = vendor_and_rel(md)
    if info is None:
        return None
    vendor, md_rel = info
    parent = posixpath.dirname(md_rel)
    joined = posixpath.normpath(posixpath.join(parent, t))
    if joined.startswith("..") or joined.startswith("/"):
        return None
    name = posixpath.basename(joined)
    suffix = pathlib.PurePosixPath(name).suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return None
    if not suffix and name not in NO_EXT_ALLOWED:
        return None
    return vendor, joined, DEST / vendor / joined


def link_targets() -> list[tuple[str, str, pathlib.Path]]:
    out: set[tuple[str, str, str]] = set()
    for md in sorted(DEST.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for target in LINK_RE.findall(text):
            r = resolve_link(md, target)
            if r is None:
                continue
            vendor, rel, local = r
            out.add((vendor, rel, str(local)))
    return [(v, r, pathlib.Path(p)) for v, r, p in sorted(out)]


def fetch_missing(item: tuple[str, str, pathlib.Path]) -> dict:
    vendor, rel, local = item
    if local.is_file():
        body = local.read_bytes()
        if body and not body.lstrip().startswith(b"<!DOCTYPE") and len(body) <= MAX_FILE_BYTES:
            return {"vendor": vendor, "path": rel, "status": "already_present", "bytes": len(body)}
    repo = VENDOR_REPO[vendor]
    url = f"{CDN}/gh/{repo}@{REF}/{urllib.parse.quote(rel, safe='/')}"
    body = get(url)
    if not body or body.lstrip().startswith(b"<!DOCTYPE"):
        return {"vendor": vendor, "path": rel, "status": "fetch_failed", "bytes": 0}
    if len(body) > MAX_FILE_BYTES:
        return {"vendor": vendor, "path": rel, "status": "skipped_large", "bytes": len(body)}
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(body)
    return {"vendor": vendor, "path": rel, "status": "fetched", "bytes": len(body)}


def clean_bad_files() -> list[str]:
    removed: list[str] = []
    for p in DEST.rglob("*"):
        if not p.is_file():
            continue
        body = p.read_bytes()
        if not body or body.lstrip().startswith(b"<!DOCTYPE") or len(body) > MAX_FILE_BYTES:
            p.unlink()
            removed.append(p.relative_to(DEST).as_posix())
    return removed


def lock_record(p: pathlib.Path) -> dict | None:
    info = vendor_and_rel(p)
    if info is None:
        return None
    vendor, rel = info
    body = p.read_bytes()
    repo = VENDOR_REPO[vendor]
    return {
        "vendor": vendor,
        "repo": repo,
        "ref": REF,
        "path": rel,
        "url": f"{CDN}/gh/{repo}@{REF}/{urllib.parse.quote(rel, safe='/')}",
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "status": "installed",
    }


def main() -> None:
    removed = clean_bad_files()
    all_results: list[dict] = []
    for pass_no in range(1, 3):
        targets = link_targets()
        print(f"pass {pass_no}: {len(targets)} resolved file links", flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(fetch_missing, targets))
        all_results.extend(results)
        fetched = sum(1 for r in results if r["status"] == "fetched")
        print(f"pass {pass_no}: fetched {fetched}", flush=True)
        if fetched == 0:
            break

    installed = []
    for p in sorted(DEST.rglob("*")):
        if not p.is_file():
            continue
        rec = lock_record(p)
        if rec:
            installed.append(rec)
    installed.sort(key=lambda r: (r["vendor"], r["path"]))

    # Keep only the last status per link target, so the report stays readable.
    statuses: dict[tuple[str, str], dict] = {}
    for r in all_results:
        statuses[(r["vendor"], r["path"])] = r
    skipped = [r for r in statuses.values() if r["status"] in ("fetch_failed", "skipped_large")]
    skipped.sort(key=lambda r: (r["vendor"], r["path"]))

    LOCK.write_text(json.dumps({
        "schema": 1,
        "source": "public GitHub repositories via cdn.jsdelivr.net",
        "discovery": "cached bytes plus two passes of relative Markdown link resolution",
        "files": installed,
        "skipped": [{"vendor": r["vendor"], "path": r["path"],
                     "reason": r["status"], "bytes": r["bytes"]} for r in skipped],
        "removed_invalid_files": removed,
    }, indent=2) + "\n", encoding="utf-8")

    by_vendor: dict[str, int] = {}
    for r in installed:
        by_vendor[r["vendor"]] = by_vendor.get(r["vendor"], 0) + 1

    lines = [
        "# Agent Skills install report", "",
        "Every installed file below was fetched byte-for-byte from a public GitHub repository.",
        "SHA-256 hashes and source URLs are recorded in `skills-lock.json`.",
        "No skill file was authored by hand.",
        "",
        "Discovery used cached bytes plus two passes over relative Markdown links. "
        "The first full directory crawl was interrupted by a sandbox timeout, so a companion file "
        "that no installed Markdown links to may be absent. Skipped link targets are listed at the end.",
        "",
        "| Vendor | Installed |", "|---|---|",
    ]
    for vendor in VENDOR_REPO:
        lines.append(f"| {vendor} | {by_vendor.get(vendor, 0)} |")
    lines += ["", f"**Installed {len(installed)} files across {len(VENDOR_REPO)} repositories.**",
              "", "| Vendor | Source path | Bytes | SHA-256 (first 12) |", "|---|---|---|---|"]
    for r in installed:
        lines.append(f"| {r['vendor']} | `{r['path']}` | {r['bytes']} | `{r['sha256'][:12]}` |")
    lines += ["", "## Skipped link targets", ""]
    if skipped:
        lines += ["| Vendor | Source path | Bytes | Reason |", "|---|---|---|---|"]
        for r in skipped:
            lines.append(f"| {r['vendor']} | `{r['path']}` | {r['bytes']} | {r['status']} |")
    else:
        lines.append("No resolved link target failed to fetch.")
    lines += ["", "## Invalid files removed", ""]
    if removed:
        lines += ["| Path |", "|---|"]
        for e in sorted(removed):
            lines.append(f"| `{e}` |")
    else:
        lines.append("None.")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print("installed by vendor: " + ", ".join(f"{k}={v}" for k, v in sorted(by_vendor.items())), flush=True)
    print(f"installed {len(installed)} files, skipped {len(skipped)}, removed {len(removed)}", flush=True)
    print(f"lock -> {LOCK}", flush=True)
    print(f"report -> {REPORT}", flush=True)


if __name__ == "__main__":
    main()
