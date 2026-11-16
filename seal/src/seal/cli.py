"""Command line interface. One entry point, five commands, stable exit codes."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from . import __version__
from .bundle import build_bundle, check_bundle, reproduce
from .canonical import digest
from .compare import compare_records
from .demo import demo_json, run_demo
from .errors import EXIT_OK, EXIT_UNEXPECTED, EXIT_ERROR, SealError, UsageError
from .manifest import load, manifest_digest, write_default
from .render import render_demo, render_report
from .runner import build_record

TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _write_json(path: str, obj: dict) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                 encoding="utf-8")


def _read_json(path: str) -> dict:
    p = pathlib.Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SealError(f"cannot read JSON file {p}: {exc}") from exc
    if not isinstance(raw, dict):
        raise SealError(f"expected a JSON object in {p}")
    return raw


def _check_tag(tag: str) -> None:
    if not TAG_RE.fullmatch(tag):
        raise UsageError("tag must be 1-64 characters: letters, digits, dot, dash, underscore")


def cmd_init(args: argparse.Namespace) -> int:
    write_default(args.manifest, force=args.force)
    print(f"wrote {args.manifest}")
    print("edit target.command, probes and intent.scope, then run: seal record --subject DIR --tag NAME")
    return EXIT_OK


def cmd_record(args: argparse.Namespace) -> int:
    _check_tag(args.tag)
    manifest, _ = load(args.manifest)
    record = build_record(manifest, manifest_digest(manifest), args.tag, args.subject)
    out = args.out or f"{args.tag}.record.json"
    _write_json(out, record)
    print(f"recorded {len(manifest['probes'])} probe(s) from {args.subject} -> {out}")
    for name, obs in record["probes"].items():
        print(f"  {name}: status={obs['status']} exit={obs['exit_code']} "
              f"created={len(obs['files_delta']['created'])} "
              f"modified={len(obs['files_delta']['modified'])}")
    return EXIT_OK


def cmd_compare(args: argparse.Namespace) -> int:
    old = _read_json(args.old)
    new = _read_json(args.new)
    manifest, _ = load(args.manifest)
    if digest(manifest) != old.get("manifest_digest"):
        raise SealError("manifest on disk differs from the manifest that produced these records")
    report = compare_records(old, new, manifest)
    if args.bundle:
        _write_json(args.bundle, build_bundle(old, new, report, manifest))
        print(f"wrote evidence bundle -> {args.bundle}")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(render_report(report), end="")
    if report["overall"] == "UNEXPECTED":
        return EXIT_UNEXPECTED
    if args.strict_unknown and report["overall"] == "INCOMPLETE":
        return EXIT_UNEXPECTED
    return EXIT_OK


def cmd_verify(args: argparse.Namespace) -> int:
    if not args.trust:
        raise UsageError(
            "verify executes commands from the bundle. Re-run with --trust only after "
            "reading the manifest and running it in a network-isolated sandbox")
    bundle = _read_json(args.bundle)
    check_bundle(bundle)
    result = reproduce(bundle, args.old, args.new)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"verification: {result['status']}")
        print(f"  recorded verdict: {result['recorded_overall']}")
        print(f"  fresh verdict   : {result['fresh_overall']}")
        if result["mismatches"]:
            print("  mismatches:")
            for item in result["mismatches"][:20]:
                print(f"    {item}")
        print(f"  verdict reproduced: {result['verdict_reproduced']}")
    if result["status"] != "REPRODUCED":
        return EXIT_UNEXPECTED
    return EXIT_OK


def cmd_demo(args: argparse.Namespace) -> int:
    result = run_demo(keep=args.keep)
    if args.json:
        print(demo_json(result))
    else:
        print(render_demo(result))
    return EXIT_OK if result["passed"] else EXIT_ERROR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seal",
        description="Show what a change actually changed, and hand the proof to somebody who was not there.",
    )
    parser.add_argument("--version", action="version", version=f"seal {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="write a default sealfile.json")
    p_init.add_argument("--manifest", default="sealfile.json")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_rec = sub.add_parser("record", help="run probes and capture observations")
    p_rec.add_argument("--subject", required=True, help="directory holding one version of the program")
    p_rec.add_argument("--tag", required=True)
    p_rec.add_argument("--manifest", default="sealfile.json")
    p_rec.add_argument("--out", default=None)
    p_rec.set_defaults(func=cmd_record)

    p_cmp = sub.add_parser("compare", help="classify differences between two records")
    p_cmp.add_argument("old")
    p_cmp.add_argument("new")
    p_cmp.add_argument("--manifest", default="sealfile.json")
    p_cmp.add_argument("--bundle", default=None, help="write a self-contained evidence bundle")
    p_cmp.add_argument("--json", action="store_true")
    p_cmp.add_argument("--strict-unknown", action="store_true",
                       help="exit 1 when any channel is UNKNOWN")
    p_cmp.set_defaults(func=cmd_compare)

    p_ver = sub.add_parser("verify", help="re-execute an evidence bundle in a clean sandbox")
    p_ver.add_argument("bundle")
    p_ver.add_argument("--old", required=True, help="directory for the recorded old version")
    p_ver.add_argument("--new", required=True, help="directory for the recorded new version")
    p_ver.add_argument("--trust", action="store_true",
                       help="required acknowledgement that bundle commands will be executed")
    p_ver.add_argument("--json", action="store_true")
    p_ver.set_defaults(func=cmd_verify)

    p_demo = sub.add_parser("demo", help="30-second self-contained demonstration")
    p_demo.add_argument("--json", action="store_true")
    p_demo.add_argument("--keep", action="store_true", help="keep the temporary fixture directory")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except SealError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
