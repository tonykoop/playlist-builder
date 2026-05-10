#!/usr/bin/env python3
"""
Playlist Builder v2 -- generalized generator.

Reads a context profile JSON and, when a concrete categorized catalog is
available, produces a tracklist that follows the arc. When the local state only
has documentation-level bank references, it emits a bank scaffold instead of
pretending to know exact tracks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

BANK_LABELS = {
    "A": "opening / closing",
    "B": "rising energy",
    "C": "theme anchor",
    "D": "peak energy",
    "E": "descent",
}


def load_context(path: Path) -> dict:
    return json.loads(path.read_text())


def load_catalog(path: Path) -> dict:
    data = json.loads(path.read_text())
    if isinstance(data, list) and path.stem in BANK_LABELS:
        return {
            "version": 1,
            "source": "seed-bank-file",
            "banks": {
                bank: data if bank == path.stem else []
                for bank in BANK_LABELS
            },
            "exclusions": [],
        }
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a categorized catalog JSON object")
    return data


def _track_id(track: dict) -> str:
    return (
        track.get("spotify_uri")
        or track.get("soundcloud_url")
        or f"{track.get('artist','')}|{track.get('title','')}"
    )


def _duration_text(duration_ms: int | None) -> str:
    if not duration_ms:
        return "~"
    total_sec = int(duration_ms / 1000)
    return f"{total_sec // 60}:{total_sec % 60:02d}"


def score_theme_match(track: dict, theme_keywords: list) -> int:
    if not theme_keywords:
        return 0
    tags = track.get("tags") or []
    tags_str = " ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
    text = " ".join(
        [
            str(track.get("title", "")),
            str(track.get("artist", "")),
            tags_str,
            str(track.get("genre", "")),
        ]
    ).lower()
    score = 0
    for kw in theme_keywords:
        kw_l = kw.lower()
        if kw_l in text:
            score += 2
        for word in text.split():
            if kw_l in word or word in kw_l:
                score += 1
    return score


def select_for_phase(
    bank_tracks,
    count,
    window_min,
    theme_keywords=None,
    exclude_ids=None,
    prefer_theme=False,
):
    exclude_ids = exclude_ids or set()
    available = [
        t
        for t in bank_tracks
        if _track_id(t) not in exclude_ids and (t.get("duration_ms") or 0) > 0
    ]
    if not available:
        return []
    if prefer_theme and theme_keywords:
        available.sort(key=lambda t: score_theme_match(t, theme_keywords), reverse=True)
        return available[:count]
    random.shuffle(available)
    return available[:count]


def generate_playlist(context, catalog, theme="", extra_excludes=None):
    theme_keywords = [w.strip() for w in theme.split() if w.strip()] if theme else []
    excludes = set(catalog.get("exclusions", []))
    if extra_excludes:
        excludes.update(extra_excludes)

    playlist = []
    used_in_run = set()

    for phase in context["phases"]:
        bank = catalog["banks"].get(phase["bank"], [])
        target = (phase["min_tracks"] + phase["max_tracks"]) // 2
        picks = select_for_phase(
            bank,
            target,
            tuple(phase["window_min"]),
            theme_keywords=theme_keywords,
            exclude_ids=excludes | used_in_run,
        )
        for p in picks:
            playlist.append({**p, "phase": phase["name"], "bank": phase["bank"]})
            used_in_run.add(_track_id(p))

    anchor = context.get("theme_anchor")
    if anchor and theme_keywords:
        anchor_bank = catalog["banks"].get(anchor["bank"], [])
        anchor_picks = select_for_phase(
            anchor_bank,
            anchor.get("tracks", 1),
            tuple(anchor["window_min"]),
            theme_keywords=theme_keywords,
            exclude_ids=excludes | used_in_run,
            prefer_theme=True,
        )
        if anchor_picks:
            anchor_track = {**anchor_picks[0], "phase": "Theme Anchor", "bank": anchor["bank"]}
            cum_ms = 0
            window_start_ms = anchor["window_min"][0] * 60_000
            insert_idx = len(playlist)
            for i, t in enumerate(playlist):
                if cum_ms >= window_start_ms:
                    insert_idx = i
                    break
                cum_ms += t.get("duration_ms", 0)
            playlist.insert(insert_idx, anchor_track)
            used_in_run.add(_track_id(anchor_track))

    return playlist


def _suggest_tags(context, theme):
    base = {
        "yoga-power": ["yoga", "vinyasa", "power-flow", "heated"],
        "yoga-power-sustained": ["yoga", "vinyasa", "power-flow", "sustained"],
        "yoga-sculpt": ["yoga", "sculpt", "strength", "cardio"],
        "yoga-restorative": ["yoga", "restorative", "yin", "slow"],
        "yoga-vinyasa": ["yoga", "vinyasa", "flow"],
        "spa-massage": ["spa", "massage", "ambient", "relaxation"],
        "spin-bike": ["spin", "cycling", "indoor-cycling", "intervals"],
        "party": ["party", "dance", "house"],
    }
    tags = list(base.get(context["id"], ["yoga", context["id"]]))
    if theme:
        tags.extend(t.strip().replace(" ", "-") for t in theme.split() if len(t) > 2)
    seen, out = set(), []
    for t in tags:
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(k)
    return ", ".join(out)


def _row_status(track: dict, forced_mode: str) -> tuple[str, bool]:
    has_exact_id = bool(track.get("spotify_uri") or track.get("soundcloud_url"))
    if forced_mode == "verified" and has_exact_id:
        return "verified", False
    if has_exact_id:
        return "verified", False
    return "unverified", True


def format_markdown(playlist, context, theme, playlist_number=None, output_mode="verified"):
    total_ms = sum(t.get("duration_ms", 0) for t in playlist)
    total_min = total_ms / 60_000
    title = f"{playlist_number}. {theme}" if playlist_number and theme else (theme or "Untitled")
    arc_summary = " -> ".join(p["name"] for p in context["phases"])

    if output_mode == "search-assisted":
        certainty_note = (
            "Search-assisted output: rows without a platform URI/URL are candidates, "
            "not paste-ready tracks."
        )
    else:
        certainty_note = "Exact playlist output: every usable row should include a verified platform ID."

    lines = [
        f"# Playlist - {context.get('name','Untitled')}: {title}",
        "",
        f"**Context:** `{context['id']}` * **Total duration:** {int(total_min)}:{int((total_ms % 60000) / 1000):02d} * **Tracks:** {len(playlist)}",
        "",
        f"**Output mode:** `{output_mode}`",
        "",
        certainty_note,
        "",
        "## Suggested description (copy-paste into SoundCloud / Spotify / Apple Music)",
        "",
        "```",
        f"{int(total_min)}-min {context.get('name','yoga')} class * Theme: {theme or '(none)'}",
        f"Energy arc: {arc_summary}",
        "Built with playlist-builder * github.com/tonykoop/playlist-builder",
        "```",
        "",
        "## Suggested tags",
        "",
        "```",
        _suggest_tags(context, theme),
        "```",
        "",
        "## Tracklist",
        "",
        "| # | Time | Phase | Bank | Artist | Title | Duration | exact_id_status | verification_required |",
        "|---|------|-------|------|--------|-------|----------|---|---|",
    ]
    cum_min = 0.0
    for i, t in enumerate(playlist, 1):
        dur = (t.get("duration_ms") or 0) / 60_000
        time_str = f"{int(cum_min)}:{int((cum_min % 1) * 60):02d}"
        dur_str = _duration_text(t.get("duration_ms", 0))
        artist = (t.get("artist") or "")[:25]
        ttl = (t.get("title") or "")[:40]
        status, requires_verification = _row_status(t, output_mode)
        lines.append(
            f"| {i} | {time_str} | {t.get('phase','')} | {t.get('bank','')} | {artist} | {ttl} | {dur_str} | {status} | {str(requires_verification).lower()} |"
        )
        cum_min += dur

    sc_links = [t.get("soundcloud_url") for t in playlist if t.get("soundcloud_url")]
    sp_uris = [t.get("spotify_uri") for t in playlist if t.get("spotify_uri")]

    if sc_links:
        lines.append("")
        lines.append("## SoundCloud links")
        lines.append("")
        for i, t in enumerate(playlist, 1):
            if t.get("soundcloud_url"):
                lines.append(f"{i}. [{t.get('artist','')} - {(t.get('title') or '')[:50]}]({t['soundcloud_url']})")

    if sp_uris:
        lines.append("")
        lines.append("## Spotify URIs (bulk-add via desktop search bar)")
        lines.append("")
        lines.append("```")
        for u in sp_uris:
            lines.append(u)
        lines.append("```")

    if output_mode == "search-assisted":
        lines.extend(
            [
                "",
                "## Verification checklist",
                "",
                "- [ ] Search every unverified row on the target platform.",
                "- [ ] Confirm runtime is close enough for the slot.",
                "- [ ] Confirm explicit-content status before teaching.",
                "- [ ] Recheck final playlist duration after substitutions.",
            ]
        )

    return "\n".join(lines) + "\n"


def _phase_duration(phase: dict) -> int:
    start, end = phase.get("window_min", [0, 0])
    return max(0, int(end) - int(start))


def _bank_search_hint(bank: str, phase: dict, theme: str) -> str:
    parts = []
    if theme:
        parts.append(theme)
    parts.extend(
        [
            str(phase.get("name", "")),
            BANK_LABELS.get(bank, "playlist bank"),
            str(phase.get("notes", "")),
            "clean non explicit",
        ]
    )
    return " ".join(p for p in parts if p).strip()


def _load_mode_b_snapshot(skill_dir: Path | None, explicit_path: Path | None) -> dict | None:
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    if skill_dir:
        candidates.append(skill_dir / "references" / "tony-mode-b-snapshot.json")

    for path in candidates:
        if path and path.exists():
            return json.loads(path.read_text())
    return None


def _bank_reference(snapshot: dict | None, bank: str) -> str:
    if not snapshot:
        return ""
    banks = snapshot.get("banks", {})
    entry = banks.get(bank, {})
    return entry.get("public_playlist_url") or entry.get("playlist_name") or ""


def format_bank_scaffold(context, theme, skill_dir=None, tony_snapshot=None, include_examples=False):
    title = theme or "Untitled"
    lines = [
        f"# Bank Scaffold - {context.get('name','Untitled')}: {title}",
        "",
        "**Output mode:** `bank-scaffold`",
        "",
        "This is a documentation-only bank scaffold. It is useful for curation, but it is not an exact playlist and it is not a search-assisted tracklist.",
        "",
        "Use this when Tony Mode B bank references are present but no machine-readable categorized track snapshot with concrete tracks is available locally.",
        "",
        "## Slot plan",
        "",
        "| slot | phase | window_min | bank | bank_role | target_tracks | search_string | exact_id_status | verification_required | platform_auth_available | bank_reference |",
        "|---:|---|---:|---|---|---:|---|---|---|---|---|",
    ]

    slot = 1
    for phase in context.get("phases", []):
        bank = phase["bank"]
        target = (phase["min_tracks"] + phase["max_tracks"]) // 2
        window = f"{phase['window_min'][0]}-{phase['window_min'][1]}"
        search = _bank_search_hint(bank, phase, theme)
        lines.append(
            f"| {slot} | {phase['name']} | {window} | {bank} | {BANK_LABELS.get(bank, '')} | {target} | `{search}` | requires_auth | true | false | {_bank_reference(tony_snapshot, bank)} |"
        )
        slot += 1

    anchor = context.get("theme_anchor")
    if anchor:
        bank = anchor["bank"]
        window = f"{anchor['window_min'][0]}-{anchor['window_min'][1]}"
        search = " ".join(p for p in [theme, "theme anchor clean vocals", BANK_LABELS.get(bank, "")] if p)
        lines.append(
            f"| {slot} | Theme Anchor | {window} | {bank} | {BANK_LABELS.get(bank, '')} | {anchor.get('tracks', 1)} | `{search}` | requires_auth | true | false | {_bank_reference(tony_snapshot, bank)} |"
        )

    lines.extend(
        [
            "",
            "## Curation prompt",
            "",
            f"Build a {context.get('duration_min', 'class-length')}-minute playlist for `{context.get('id')}` with theme `{theme or '(none)'}`.",
            "Use the bank roles above. Return only tracks that you can verify on the chosen platform, with runtime, explicit-content status, and a platform URL or URI.",
            "",
            "## Verification checklist",
            "",
            "- [ ] Replace every scaffold row with verified tracks before teaching.",
            "- [ ] Confirm each track's runtime and clean-content status.",
            "- [ ] Confirm the final playlist fits the context duration.",
            "- [ ] Do not mark any row `verified` unless it has a real platform URL or URI.",
        ]
    )

    if include_examples:
        lines.extend(
            [
                "",
                "## Optional example search candidates",
                "",
                "These are search strings, not track claims:",
                "",
            ]
        )
        for phase in context.get("phases", []):
            lines.append(f"- {phase['name']} ({phase['bank']}): `{_bank_search_hint(phase['bank'], phase, theme)}`")

    return "\n".join(lines) + "\n"


def _env_auth_available() -> bool:
    auth_names = (
        "SPOTIFY_ACCESS_TOKEN",
        "SPOTIFY_CLIENT_ID",
        "SOUNDCLOUD_ACCESS_TOKEN",
        "SOUNDCLOUD_CLIENT_ID",
    )
    return any(os.environ.get(name) for name in auth_names)


def _catalog_track_count(catalog: dict | None) -> int:
    if not catalog:
        return 0
    return sum(len(v) for v in catalog.get("banks", {}).values() if isinstance(v, list))


def choose_output_mode(requested: str, catalog: dict | None, tony_snapshot: dict | None) -> str:
    if requested != "auto":
        return requested
    if _env_auth_available():
        return "verified"
    track_count = _catalog_track_count(catalog)
    if track_count >= 30:
        return "search-assisted"
    if tony_snapshot:
        snapshot_tracks = sum(
            len(v.get("tracks", []))
            for v in tony_snapshot.get("banks", {}).values()
            if isinstance(v, dict)
        )
        return "search-assisted" if snapshot_tracks >= 30 else "bank-scaffold"
    return "manual-curation"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--context", required=True, type=Path)
    p.add_argument("--catalog", type=Path)
    p.add_argument(
        "--catalog-state",
        choices=["auto", "verified", "search-assisted", "bank-scaffold", "sparse", "manual-curation"],
        default="auto",
        help="Output certainty mode. 'auto' chooses from catalog/auth/snapshot state.",
    )
    p.add_argument("--skill-dir", type=Path, help="Skill root, used for default Tony Mode B snapshot lookup.")
    p.add_argument("--tony-snapshot", type=Path, help="Machine-readable Tony Mode B snapshot JSON.")
    p.add_argument("--include-example-candidates", action="store_true")
    p.add_argument("--theme", default="")
    p.add_argument("--output", type=Path)
    p.add_argument("--seed", type=int)
    p.add_argument("--exclude-ids", default="")
    p.add_argument("--number", type=int)
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    context = load_context(args.context)
    catalog = load_catalog(args.catalog) if args.catalog else None
    tony_snapshot = _load_mode_b_snapshot(args.skill_dir, args.tony_snapshot)
    mode = choose_output_mode(args.catalog_state, catalog, tony_snapshot)

    if mode in {"bank-scaffold", "manual-curation", "sparse"}:
        md = format_bank_scaffold(
            context,
            args.theme,
            skill_dir=args.skill_dir,
            tony_snapshot=tony_snapshot,
            include_examples=args.include_example_candidates,
        )
        print(f"  Generated {mode} output", file=sys.stderr)
    else:
        if catalog is None:
            raise SystemExit("--catalog is required for verified/search-assisted tracklist output")
        extras = {x.strip() for x in args.exclude_ids.split(",") if x.strip()}
        playlist = generate_playlist(context, catalog, theme=args.theme, extra_excludes=extras)
        md = format_markdown(playlist, context, args.theme, playlist_number=args.number, output_mode=mode)
        total_ms = sum(t.get("duration_ms", 0) for t in playlist)
        print(f"  Generated {len(playlist)} tracks, {total_ms/60000:.1f} min ({mode})", file=sys.stderr)

    if args.output:
        args.output.write_text(md)
        print(f"  Saved to {args.output}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
