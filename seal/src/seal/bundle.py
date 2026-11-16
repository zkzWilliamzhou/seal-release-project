"""Self-contained evidence bundle and independent reproduction.

A bundle is one JSON file. It contains the manifest, both observation sets,
the classification report, and digests over each part. Verification recomputes
every digest before executing anything, then re-runs the declared probes in a
clean sandbox and compares its own observation to the stored one.
"""
from __future__ import annotations

import pathlib

from .canonical import digest
from .compare import compare_records
from .errors import SealError, TamperError
from .manifest import validate
from .render import render_report
from .runner import build_record, canonical_observations, verify_record_digest


def build_bundle(old: dict, new: dict, report: dict, manifest: dict) -> dict:
    if not verify_record_digest(old) or not verify_record_digest(new):
        raise SealError("cannot bundle a record with an invalid digest")
    bundle = {
        "schema": 1,
        "kind": "seal-evidence-bundle",
        "manifest": manifest,
        "records": {"old": old, "new": new},
        "report": report,
        "provenance": {
            "manifest_digest": digest(manifest),
            "old_record_digest": old["digest"],
            "new_record_digest": new["digest"],
            "report_digest": report["digest"],
        },
    }
    bundle["bundle_digest"] = digest(_without_digest(bundle))
    return bundle


def _without_digest(bundle: dict) -> dict:
    return {k: v for k, v in bundle.items() if k != "bundle_digest"}


def check_bundle(bundle: dict) -> None:
    """Reject a bundle whose content does not match its own hashes."""
    if not isinstance(bundle, dict) or bundle.get("kind") != "seal-evidence-bundle":
        raise TamperError("not a seal evidence bundle")
    expected = digest(_without_digest(bundle))
    if bundle.get("bundle_digest") != expected:
        raise TamperError("bundle digest mismatch: content was modified")
    manifest = validate(bundle.get("manifest", {}))
    prov = bundle.get("provenance", {})
    if prov.get("manifest_digest") != digest(manifest):
        raise TamperError("manifest digest mismatch")
    records = bundle.get("records", {})
    for side in ("old", "new"):
        record = records.get(side, {})
        if not verify_record_digest(record):
            raise TamperError(f"{side} record digest mismatch")
        if prov.get(f"{side}_record_digest") != record.get("digest"):
            raise TamperError(f"{side} provenance digest mismatch")
    for obs in records.get("old", {}).get("probes", {}).values():
        _check_obs(obs)
    for obs in records.get("new", {}).get("probes", {}).values():
        _check_obs(obs)
    report = bundle.get("report", {})
    if report.get("digest") != digest({k: v for k, v in report.items() if k != "digest"}):
        raise TamperError("report digest mismatch")
    if prov.get("report_digest") != report.get("digest"):
        raise TamperError("report provenance digest mismatch")


def _check_obs(obs: dict) -> None:
    from .runner import verify_observation_digest
    if not verify_observation_digest(obs):
        raise TamperError("observation digest mismatch")


def reproduce(bundle: dict, old_dir: str, new_dir: str, *,
              workdir_root: str | None = None) -> dict:
    """Re-execute both sides and compare against the stored evidence.

    Callers must have required explicit trust before reaching this function.
    """
    check_bundle(bundle)
    manifest = validate(bundle["manifest"])
    manifest_digest_hex = digest(manifest)
    fresh_old = build_record(manifest, manifest_digest_hex,
                             bundle["records"]["old"]["tag"], pathlib.Path(old_dir),
                             workdir_root=workdir_root)
    fresh_new = build_record(manifest, manifest_digest_hex,
                             bundle["records"]["new"]["tag"], pathlib.Path(new_dir),
                             workdir_root=workdir_root)

    mismatches: list[str] = []
    for side, fresh, stored in (("old", fresh_old, bundle["records"]["old"]),
                                ("new", fresh_new, bundle["records"]["new"])):
        for probe_name, stored_obs in stored["probes"].items():
            fresh_obs = fresh["probes"].get(probe_name)
            if fresh_obs is None:
                mismatches.append(f"{side}/{probe_name}: probe not reproduced")
                continue
            for channel in ("status", "stdout", "stderr", "exit_code",
                            "files_delta", "env_names"):
                if fresh_obs.get(channel) != stored_obs.get(channel):
                    mismatches.append(f"{side}/{probe_name}/{channel}")
    fresh_report = compare_records(fresh_old, fresh_new, manifest)
    verdict_reproduced = (fresh_report["overall"] == bundle["report"]["overall"]
                          and fresh_report["counts"] == bundle["report"]["counts"])
    return {
        "schema": 1,
        "status": "REPRODUCED" if not mismatches and verdict_reproduced else "MISMATCH",
        "verdict_reproduced": verdict_reproduced,
        "mismatches": mismatches,
        "fresh_overall": fresh_report["overall"],
        "recorded_overall": bundle["report"]["overall"],
        "fresh_counts": fresh_report["counts"],
        "recorded_counts": bundle["report"]["counts"],
        "canonical_old_observations": canonical_observations(fresh_old),
        "report_preview": render_report(fresh_report).splitlines()[0],
    }
