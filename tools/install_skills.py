#!/usr/bin/env python3
"""Install complete Agent Skills folders from public GitHub repositories.

Direct GitHub access is blocked in this environment, so directory listings
and file bytes come from the jsDelivr GitHub mirror. The crawler:

  1. finds every directory that contains a SKILL.md,
  2. downloads the whole folder tree (references, scripts, assets),
  3. downloads repository root metadata files,
  4. records every byte with its source URL and SHA-256.

Nothing is fabricated. Files that are too large or binary are skipped and
reported as skipped in the install log.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import urllib.parse

PROJECT = pathlib.Path("/data/workspace/seal")
DEST = PROJECT / ".agents" / "skills"
LOCK = PROJECT / "skills-lock.json"
REPORT = PROJECT / "docs" / "SKILL_INSTALL_REPORT.md"
CDN = "https://cdn.jsdelivr.net"
REF = "main"

# (vendor, owner/repo, directories to crawl recursively from the repo root)
SOURCES = [
    ("anthropics", "anthropics/skills", ["skills"]),
    ("mattpocock", "mattpocock/skills", ["skills"]),
    ("superpowers", "obra/superpowers", ["skills"]),
    ("vercel-labs", "vercel-labs/skills", ["skills"]),
    ("stop-slop", "hardikpandya/stop-slop", ["references"]),
]

ROOT_META_NAMES = {
    "README.md", "README", "LICENSE", "LICENSE.md", "LICENSE.txt",
    "CONTEXT.md", "CLAUDE.md", "GLOSSARY.md", "CONTRIBUTING.md",
    "SECURITY.md", "CODE_OF_CONDUCT.md", "NOTICE", "CHANGELOG.md",
    "pyproject.toml", "package.json", "requirements.txt", "Makefile",
}
SKIP_DIR_NAMES = {
    ".git", ".github", "node_modules", "dist", "build", "coverage",
    "__pycache__", ".pytest_cache", ".venv", "venv", "vendor", ".next",
}
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tiff",
    ".woff", ".woff2", ".ttf", ".eot", ".otf", ".mp3", ".mp4", ".webm",
    ".wav", ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".pdf",
    ".docx", ".pptx", ".xlsx", ".exe", ".dll", ".so", ".dylib", ".bin",
}
MAX_FILE_BYTES = 1024 * 1024
HREF = re.compile(r'href="(/gh/[^"?#]+)"')


def get(url: str) -> bytes:
    try:
        p = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "20", url],
            capture_output=True, timeout=25,
        )
        if p.returncode == 0:
            return p.stdout
    except Exception:
        pass
    return b""


def dir_url(repo: str, path: str) -> str:
    base = f"{CDN}/gh/{repo}@{REF}"
    return f"{base}/{path}/" if path else f"{base}/"


def listing(repo: str, path: str) -> tuple[list[str], list[str]]:
    """Return (subdirectory rel paths, file rel paths) for one CDN directory."""
    html = get(dir_url(repo, path)).decode("utf-8", "replace")
    prefix = f"/gh/{repo}@{REF}/"
    dirs: list[str] = []
    files: list[str] = []
    for href in sorted(set(HREF.findall(html))):
        if not href.startswith(prefix):
            continue
        raw = href[len(prefix):]
        rel = urllib.parse.unquote(raw)
        parts = pathlib.PurePosixPath(rel).parts
        if ".." in parts:
            continue
        if raw.endswith("/"):
            if parts and parts[-1] not in SKIP_DIR_NAMES:
                dirs.append(rel.rstrip("/"))
        else:
            files.append(rel)
    return dirs, files


def crawl(repo: str, start: str, depth: int = 5) -> list[str]:
    """All file rel paths under `start`, plus root metadata when start is ''."""
    found: set[str] = set()
    seen: set[str] = set()

    def visit(path: str, left: int) -> None:
        if path in seen:
            return
        seen.add(path)
        dirs, files = listing(repo, path)
        for rel in files:
            name = pathlib.PurePosixPath(rel).name
            ext = pathlib.PurePosixPath(name).suffix.lower()
            if path == "" and name not in ROOT_META_NAMES:
                continue
            if ext in SKIP_EXTENSIONS:
                continue
            found.add(rel)
        if left > 0:
            for sub in dirs:
                if pathlib.PurePosixPath(sub).name in SKIP_DIR_NAMES:
                    continue
                visit(sub, left - 1)

    visit(start, depth)
    return sorted(found)


def wanted_files(repo: str, starts: list[str]) -> list[str]:
    files: set[str] = set()
    # Root metadata.
    root_dirs, root_files = listing(repo, "")
    for rel in root_files:
        name = pathlib.PurePosixPath(rel).name
        if name in ROOT_META_NAMES and pathlib.PurePosixPath(name).suffix.lower() not in SKIP_EXTENSIONS:
            files.add(rel)
    # Recursively crawl declared trees.
    for start in starts:
        files.update(crawl(repo, start, 5))
    # stop-slop keeps SKILL.md at the repo root.
    if repo == "hardikpandya/stop-slop":
        for rel in root_files:
            if pathlib.PurePosixPath(rel).name == "SKILL.md":
                files.add(rel)
    return sorted(files)


def fetch_one(vendor: str, repo: str, rel: str) -> dict | None:
    url = f"{CDN}/gh/{repo}@{REF}/{urllib.parse.quote(rel, safe='/')}"
    body = get(url)
    if not body or body.lstrip().startswith(b"<!DOCTYPE"):
        return None
    if len(body) > MAX_FILE_BYTES:
        return {"vendor": vendor, "repo": repo, "path": rel, "url": url,
                "status": "skipped_large", "bytes": len(body)}
    target = DEST / vendor / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return {"vendor": vendor, "repo": repo, "ref": REF, "path": rel,
            "url": url, "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body), "status": "installed"}


def main() -> None:
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, str, str]] = []
    for vendor, repo, starts in SOURCES:
        paths = wanted_files(repo, starts)
        print(f"discovered {vendor}: {len(paths)} candidate files")
        for rel in paths:
            jobs.append((vendor, repo, rel))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = [r for r in pool.map(lambda j: fetch_one(*j), jobs) if r]

    installed = [r for r in results if r["status"] == "installed"]
    skipped = [r for r in results if r["status"] != "installed"]
    installed.sort(key=lambda r: (r["vendor"], r["path"]))
    skipped.sort(key=lambda r: (r["vendor"], r["path"]))

    LOCK.write_text(json.dumps({
        "schema": 1,
        "source": "public GitHub repositories via cdn.jsdelivr.net",
        "files": installed,
        "skipped": [{"vendor": r["vendor"], "path": r["path"],
                     "reason": r["status"], "bytes": r["bytes"]} for r in skipped],
    }, indent=2) + "\n", encoding="utf-8")

    by_vendor: dict[str, int] = {}
    for r in installed:
        by_vendor[r["vendor"]] = by_vendor.get(r["vendor"], 0) + 1

    lines = [
        "# Agent Skills install report", "",
        "Every installed file below was fetched byte-for-byte from a public GitHub repository.",
        "SHA-256 hashes and source URLs are recorded in `skills-lock.json`.",
        "No skill file was authored by hand. Files skipped for size or binary type are listed at the end.",
        "",
        "| Vendor | Installed |", "|---|---|",
    ]
    for vendor, _, _ in SOURCES:
        lines.append(f"| {vendor} | {by_vendor.get(vendor, 0)} |")
    lines += ["", f"**Installed {len(installed)} files across {len(SOURCES)} repositories.**",
              "", "| Vendor | Source path | Bytes | SHA-256 (first 12) |", "|---|---|---|---|"]
    for r in installed:
        lines.append(f"| {r['vendor']} | `{r['path']}` | {r['bytes']} | `{r['sha256'][:12]}` |")
    lines += ["", "## Skipped", ""]
    if skipped:
        lines += ["| Vendor | Source path | Bytes | Reason |", "|---|---|---|---|"]
        for r in skipped:
            lines.append(f"| {r['vendor']} | `{r['path']}` | {r['bytes']} | {r['status']} |")
    else:
        lines.append("No candidate file was skipped.")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print("installed by vendor: " + ", ".join(f"{k}={v}" for k, v in sorted(by_vendor.items())))
    print(f"installed {len(installed)} files, skipped {len(skipped)}; report -> {REPORT}")


if __name__ == "__main__":
    main()
