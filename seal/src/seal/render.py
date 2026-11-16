"""All human-readable text. One module owns every renderer.

This module exists because of the G6 deepening pass documented in
docs/05_architecture_refactor.md. Classification lives in compare.py.
Nothing here decides a verdict, an exit code, or a digest.
"""
from __future__ import annotations

VERDICT_ORDER = ("UNEXPECTED", "UNKNOWN", "INTENDED", "SAME")


def render_report(report: dict) -> str:
    lines = ["seal behaviour report",
             f"  {report['old_tag']} -> {report['new_tag']}",
             f"  manifest: {report['manifest_digest'][:12]}",
             ""]
    for probe, channels in report["results"].items():
        changed = {k: v for k, v in channels.items() if v["verdict"] != "SAME"}
        lines.append(f"probe: {probe}")
        if not changed:
            lines.append("  all channels SAME")
        else:
            for channel, item in changed.items():
                suffix = f" ({item['reason']})" if item["reason"] else ""
                lines.append(f"  {item['verdict']:<10} {channel}{suffix}")
    counts = report["counts"]
    lines += ["",
              f"verdict: {report['overall']}",
              "counts: " + ", ".join(f"{k}={counts[k]}" for k in VERDICT_ORDER),
              ""]
    return "\n".join(lines)


def render_demo(result: dict) -> str:
    lines = [
        "seal demo: two programs, one hidden behaviour change",
        "",
        f"  stdout before : {result['stdout_before']}",
        f"  stdout after  : {result['stdout_after']}",
        "  a stdout assertion passes on both",
        "",
        result["report"].rstrip(),
        "",
        "unexpected channels: " + ", ".join(result["unexpected_channels"]),
        "",
        "seal caught: " + (result["unexpected_channels"][0]
                           if result["unexpected_channels"] else "nothing"),
        "next: seal init, then seal record --subject DIR --tag NAME",
    ]
    return "\n".join(lines)
