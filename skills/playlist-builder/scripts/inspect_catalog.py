#!/usr/bin/env python3
"""Inspect local playlist-builder catalog/auth state and recommend an output mode."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

BANKS = "ABCDE"


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        return {"_malformed": str(exc)}


def _bank_counts_from_catalog(catalog: dict | None) -> dict[str, int]:
    counts = {bank: 0 for bank in BANKS}
    if not catalog or "_malformed" in catalog:
        return counts
    for bank, tracks in catalog.get("banks", {}).items():
        if bank in counts and isinstance(tracks, list):
            counts[bank] = len(tracks)
    return counts


def _seed_bank_state(skill_dir: Path) -> dict:
    seed_dir = skill_dir / "seed-banks"
    counts = {}
    malformed = []
    for bank in BANKS:
        path = seed_dir / f"{bank}.json"
        data = _read_json(path)
        if isinstance(data, list):
            counts[bank] = len(data)
        elif isinstance(data, dict) and "_malformed" in data:
            counts[bank] = 0
            malformed.append(str(path))
        else:
            counts[bank] = 0
    return {
        "counts": counts,
        "total_count": sum(counts.values()),
        "any_bank_rich": any(count >= 8 for count in counts.values()),
        "all_banks_empty": all(count == 0 for count in counts.values()),
        "malformed_files": malformed,
        "rich_bank_threshold": 8,
    }


def _auth_state() -> dict:
    spotify_signals = [name for name in ("SPOTIFY_ACCESS_TOKEN", "SPOTIFY_CLIENT_ID") if os.environ.get(name)]
    soundcloud_signals = [name for name in ("SOUNDCLOUD_ACCESS_TOKEN", "SOUNDCLOUD_CLIENT_ID") if os.environ.get(name)]
    return {
        "spotify_reachable": bool(spotify_signals),
        "spotify_signals": spotify_signals,
        "soundcloud_reachable": bool(soundcloud_signals),
        "soundcloud_signals": soundcloud_signals,
        "any_platform_auth_available": bool(spotify_signals or soundcloud_signals),
    }


def _mode_b_state(skill_dir: Path, snapshot_path: Path | None) -> dict:
    doc_path = skill_dir / "references" / "CATALOG_TONY_KOOP.md"
    default_snapshot = skill_dir / "references" / "tony-mode-b-snapshot.json"
    path = snapshot_path or default_snapshot
    snapshot = _read_json(path)
    snapshot_loaded = isinstance(snapshot, dict) and "_malformed" not in snapshot
    counts = {bank: 0 for bank in BANKS}
    if snapshot_loaded:
        for bank, entry in snapshot.get("banks", {}).items():
            if bank in counts and isinstance(entry, dict):
                tracks = entry.get("tracks", [])
                counts[bank] = len(tracks) if isinstance(tracks, list) else 0
    return {
        "documentation_present": doc_path.exists(),
        "documentation_path": str(doc_path) if doc_path.exists() else None,
        "snapshot_path": str(path),
        "snapshot_loaded": snapshot_loaded,
        "snapshot_malformed": snapshot.get("_malformed") if isinstance(snapshot, dict) else None,
        "track_counts": counts,
        "track_count": sum(counts.values()),
        "documentation_only": doc_path.exists() and (not snapshot_loaded or sum(counts.values()) == 0),
    }


def recommend_mode(auth: dict, user_catalog: dict, seed_banks: dict, mode_b: dict) -> tuple[str, str]:
    if auth["any_platform_auth_available"]:
        return "verified", "Platform auth is available; exact IDs can be verified."
    if user_catalog["track_count"] >= 30:
        return "search-assisted", "A concrete user catalog is loaded; row-level verification status can be emitted."
    if seed_banks["any_bank_rich"]:
        return "verified", "A bundled bank is rich enough to emit verified seed-bank rows."
    if mode_b["track_count"] >= 30:
        return "search-assisted", "A concrete Tony Mode B snapshot is loaded; rows can be selected from a machine-readable catalog."
    if mode_b["documentation_only"]:
        return "bank-scaffold", "Only Tony Mode B documentation/bank references are available; emit scaffold rows, not track claims."
    if seed_banks["total_count"] > 0:
        return "sparse", "Only sparse bundled tracks are available; keep verified rows visually separate from curation scaffolding."
    return "manual-curation", "No concrete catalog, seed tracks, or platform auth is available."


def inspect(skill_dir: Path, catalog_path: Path | None = None, tony_snapshot: Path | None = None) -> dict:
    catalog = _read_json(catalog_path) if catalog_path else None
    auth = _auth_state()
    user_counts = _bank_counts_from_catalog(catalog)
    user_catalog = {
        "loaded": bool(catalog and "_malformed" not in catalog),
        "path": str(catalog_path) if catalog_path else None,
        "track_counts": user_counts,
        "track_count": sum(user_counts.values()),
        "malformed": catalog.get("_malformed") if isinstance(catalog, dict) else None,
    }
    seed_banks = _seed_bank_state(skill_dir)
    mode_b = _mode_b_state(skill_dir, tony_snapshot)
    mode, explanation = recommend_mode(auth, user_catalog, seed_banks, mode_b)
    return {
        "schema_version": 2,
        "skill_dir": str(skill_dir),
        "auth": auth,
        "platform_auth_available": auth["any_platform_auth_available"],
        "user_catalog": user_catalog,
        "seed_banks": seed_banks,
        "mode_b_tony_catalog": mode_b,
        "recommended_output_mode": mode,
        "mode_explanation": explanation,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True, type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--tony-snapshot", type=Path)
    args = parser.parse_args()

    result = inspect(args.skill_dir, catalog_path=args.catalog, tony_snapshot=args.tony_snapshot)
    print(f"recommended_output_mode: {result['recommended_output_mode']}")
    print(result["mode_explanation"])
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
