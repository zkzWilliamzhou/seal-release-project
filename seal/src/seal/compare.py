"""Four-state difference classification.

SAME        byte-identical after declared normalization
INTENDED    differs, and the channel is inside the declared intent scope
UNEXPECTED  differs, and nothing declares it
UNKNOWN     a timeout, a capped output, a declared nondeterministic source,
            a missing probe, or an unverifiable digest blocks a verdict

UNKNOWN is never silently converted to SAME.
"""
from __future__ import annotations

from .canonical import CHANNELS, canonical, digest
from .errors import SealError
from .runner import observation_body, verify_observation_digest, verify_record_digest

SAME = "SAME"
INTENDED = "INTENDED"
UNEXPECTED = "UNEXPECTED"
UNKNOWN = "UNKNOWN"
VERDICT_ORDER = (UNEXPECTED, UNKNOWN, INTENDED, SAME)


def _unknown_reason(channel: str, old: dict, new: dict, manifest: dict) -> str | None:
    if channel in manifest.get("nondeterminism", []):
        return "declared nondeterministic source"
    for side, obs in (("old", old), ("new", new)):
        if not all(ch in obs for ch in CHANNELS):
            return f"{side} observation is malformed"
        if obs.get("status") != "ok":
            return f"{side} probe status is {obs.get('status')}"
        if not verify_observation_digest(obs):
            return f"{side} observation digest is invalid"
    return None


def classify_channel(channel: str, old: dict, new: dict, manifest: dict) -> dict:
    reason = _unknown_reason(channel, old, new, manifest)
    old_value = old.get(channel)
    new_value = new.get(channel)
    if old_value == new_value and reason is None:
        return {"verdict": SAME, "reason": ""}
    if reason is not None:
        return {"verdict": UNKNOWN, "reason": reason}
    if channel in manifest["intent"]["scope"]:
        return {"verdict": INTENDED,
                "reason": "channel listed in intent.scope: " + manifest["intent"]["description"]}
    return {"verdict": UNEXPECTED, "reason": "difference outside declared intent scope"}


def compare_records(old: dict, new: dict, manifest: dict) -> dict:
    if old.get("manifest_digest") != new.get("manifest_digest"):
        raise SealError("records were produced by different manifests")
    if not verify_record_digest(old) or not verify_record_digest(new):
        raise SealError("record digest is invalid or a record has no probes")
    if set(old["probes"]) != set(new["probes"]):
        raise SealError("records contain different probe sets")

    old_probes = old["probes"]
    new_probes = new["probes"]
    names = sorted(set(old_probes) | set(new_probes))
    results: dict = {}
    for name in names:
        if name not in old_probes or name not in new_probes:
            results[name] = {ch: {"verdict": UNKNOWN, "reason": "probe missing from one record"}
                             for ch in CHANNELS}
            continue
        o, n = old_probes[name], new_probes[name]
        results[name] = {ch: classify_channel(ch, o, n, manifest) for ch in CHANNELS}

    counts = {v: 0 for v in VERDICT_ORDER}
    for per_probe in results.values():
        for item in per_probe.values():
            counts[item["verdict"]] += 1
    if counts[UNEXPECTED]:
        overall = "UNEXPECTED"
    elif counts[UNKNOWN]:
        overall = "INCOMPLETE"
    elif counts[INTENDED]:
        overall = "INTENDED"
    else:
        overall = "CLEAN"

    report = {
        "schema": 1,
        "old_tag": old.get("tag"),
        "new_tag": new.get("tag"),
        "manifest_digest": old.get("manifest_digest"),
        "overall": overall,
        "counts": counts,
        "channels": list(CHANNELS),
        "results": results,
    }
    report["digest"] = digest({k: v for k, v in report.items() if k != "digest"})
    return report


def report_body(report: dict) -> dict:
    return {k: v for k, v in report.items() if k != "digest"}


def canonical_report(report: dict) -> str:
    return canonical(report_body(report))
