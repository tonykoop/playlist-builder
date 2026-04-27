#!/usr/bin/env python3
"""
Yoga Playlist Generator
Builds a ~65-minute yoga class playlist from Tony's SoundCloud song banks,
following the energy arc pattern derived from 36 existing class playlists.

Target: 65 min (acceptable: 63-69 min, never exceed 70 min).
The extra minutes beyond 60 provide a meditation buffer at the end of class.
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("Error: openpyxl required. Install with: pip install openpyxl --break-system-packages")
    sys.exit(1)


# Energy arc phases: (phase_name, bank, min_tracks, max_tracks, target_minutes)
# Theme Anchor (C) is NOT a sequential phase — it gets inserted into the
# timeline between minutes 20-45 (after Tony finishes theme-setting talk).
# The arc runs: Opening → Rising → Peak → Descent → Closing, and the
# Theme Anchor replaces one slot in Peak or early Descent.
PHASES = [
    ("Opening",       "A", 1, 2, (0, 5)),
    ("Rising",        "B", 3, 4, (5, 20)),
    ("Peak",          "D", 4, 5, (20, 42)),
    ("Descent",       "E", 3, 4, (42, 57)),
    ("Closing",       "A", 1, 2, (57, 69)),
]

# Target: 65 min (acceptable: 63-69 min, never exceed 70 min)
TARGET_DURATION_MIN = 65
MAX_DURATION_MIN = 69
MIN_DURATION_MIN = 63

# Theme Anchor is placed separately — inserted at the 20-45 min mark
THEME_ANCHOR_WINDOW = (20, 45)  # minutes

BANK_PLAYLISTS = {
    "A": "A Bank: First & Last",
    "B": "B Bank: Rising Energy",
    "C": "C Bank: Theme Anchor",
    "D": "Song Bank: High Energy - 15th-40th Minute",
    "E": "E Bank: Descending Energy",
}


def load_song_banks(spreadsheet_path):
    """Load all tracks organized by bank from the spreadsheet."""
    wb = openpyxl.load_workbook(spreadsheet_path, data_only=True)
    ws = wb['All Tracks']

    banks = defaultdict(list)
    used_in_numbered = defaultdict(set)  # track_url -> set of numbered playlist names

    for r in range(2, ws.max_row + 1):
        playlist = ws.cell(r, 1).value
        if not playlist:
            continue

        track = {
            'playlist': playlist,
            'position': ws.cell(r, 8).value,
            'title': ws.cell(r, 9).value or '',
            'artist': ws.cell(r, 10).value or '',
            'duration_ms': ws.cell(r, 11).value or 0,
            'duration_fmt': ws.cell(r, 12).value or '',
            'url': ws.cell(r, 13).value or '',
            'genre': ws.cell(r, 14).value or '',
            'bpm': ws.cell(r, 15).value,
            'play_count': ws.cell(r, 16).value or 0,
            'tags': ws.cell(r, 17).value or '',
        }

        # Categorize into banks
        for bank_letter, bank_name in BANK_PLAYLISTS.items():
            if playlist == bank_name:
                banks[bank_letter].append(track)

        # Track numbered playlist usage
        first_part = playlist.split('.')[0].strip()
        try:
            int(first_part)
            if track['url']:
                used_in_numbered[track['url']].add(playlist)
        except ValueError:
            pass

    return banks, used_in_numbered


def score_theme_match(track, theme_keywords):
    """Score how well a track matches a theme based on title, tags, and genre."""
    if not theme_keywords:
        return 0

    text = f"{track['title']} {track['tags']} {track['genre']}".lower()
    score = 0
    for kw in theme_keywords:
        kw_lower = kw.lower()
        if kw_lower in text:
            score += 2
        # Partial match
        for word in text.split():
            if kw_lower in word or word in kw_lower:
                score += 1
    return score


def select_tracks_for_phase(bank_tracks, count, target_dur_range_ms, theme_keywords=None,
                            exclude_urls=set(), prefer_theme=False):
    """Select tracks for a phase, considering duration targets and theme matching."""
    available = [t for t in bank_tracks if t['url'] not in exclude_urls and t['duration_ms'] > 0]

    if not available:
        return []

    if prefer_theme and theme_keywords:
        # Sort by theme relevance for C bank
        available.sort(key=lambda t: score_theme_match(t, theme_keywords), reverse=True)
        # Return top match
        return available[:count]

    # For other banks, use weighted random selection based on duration fit
    # Prefer tracks that fit the target duration well
    target_total_ms = (target_dur_range_ms[1] - target_dur_range_ms[0]) * 60000
    target_per_track_ms = target_total_ms / count if count > 0 else 240000

    # Score tracks by how close they are to ideal duration
    scored = []
    for t in available:
        dur_diff = abs(t['duration_ms'] - target_per_track_ms)
        # Normalize: closer to target = higher score
        dur_score = max(0, 1 - dur_diff / target_per_track_ms)
        # Add some randomness
        final_score = dur_score * 0.6 + random.random() * 0.4
        scored.append((final_score, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [t for _, t in scored[:count * 3]]  # Take top candidates

    # Pick from candidates ensuring variety (different artists)
    result = []
    used_artists = set()
    for t in selected:
        if len(result) >= count:
            break
        artist_key = t['artist'].lower().strip()
        if artist_key in used_artists:
            continue
        result.append(t)
        used_artists.add(artist_key)

    # If we didn't get enough (due to artist dedup), fill from remaining
    if len(result) < count:
        for t in selected:
            if len(result) >= count:
                break
            if t not in result:
                result.append(t)

    return result[:count]


def generate_playlist(banks, theme="", target_duration_min=TARGET_DURATION_MIN, exclude_urls=set()):
    """Generate a complete yoga class playlist following the energy arc.

    The Theme Anchor (C bank) is inserted between minutes 20-45, after Tony
    finishes his intention-setting talk in the first 15 minutes of class.
    """
    theme_keywords = [w.strip() for w in theme.split() if len(w.strip()) > 2] if theme else []

    playlist = []
    all_used_urls = set(exclude_urls)

    # Build the base arc (without theme anchor)
    for phase_name, bank_letter, min_tracks, max_tracks, time_range in PHASES:
        bank_tracks = banks.get(bank_letter, [])
        count = random.randint(min_tracks, max_tracks)

        target_dur_range = (time_range[0], time_range[1])

        selected = select_tracks_for_phase(
            bank_tracks, count, target_dur_range,
            theme_keywords=theme_keywords,
            exclude_urls=all_used_urls,
        )

        for t in selected:
            playlist.append({
                **t,
                'phase': phase_name,
                'bank': bank_letter,
            })
            if t['url']:
                all_used_urls.add(t['url'])

    # Now insert the Theme Anchor (C bank) at the right moment (20-45 min)
    theme_tracks = select_tracks_for_phase(
        banks.get('C', []), 1, THEME_ANCHOR_WINDOW,
        theme_keywords=theme_keywords,
        exclude_urls=all_used_urls,
        prefer_theme=True,
    )

    if theme_tracks:
        theme_track = {**theme_tracks[0], 'phase': 'Theme Anchor', 'bank': 'C'}
        # Find the right insertion point: first track whose cumulative start >= 20 min
        cum_ms = 0
        insert_idx = None
        for i, t in enumerate(playlist):
            if cum_ms >= THEME_ANCHOR_WINDOW[0] * 60000 and t['phase'] in ('Peak', 'Descent'):
                insert_idx = i
                break
            cum_ms += t['duration_ms']

        if insert_idx is not None:
            playlist.insert(insert_idx, theme_track)
        else:
            # Fallback: insert after the Rising phase
            for i, t in enumerate(playlist):
                if t['phase'] == 'Peak':
                    playlist.insert(i, theme_track)
                    break

    # --- Duration enforcement ---
    # Target: 65 min, acceptable: 63-69 min, never exceed 70 min
    total_ms = sum(t['duration_ms'] for t in playlist)
    total_min = total_ms / 60000

    # If too short (< MIN_DURATION_MIN), add an extra Descent (E) or Closing (A) track
    attempts = 0
    while total_min < MIN_DURATION_MIN and attempts < 3:
        # Try adding an E bank track before the Closing phase
        closing_idx = next((i for i, t in enumerate(playlist) if t['phase'] == 'Closing'), len(playlist))
        extra = select_tracks_for_phase(
            banks.get('E', []), 1, (40, 57),
            exclude_urls=all_used_urls,
        )
        if extra:
            playlist.insert(closing_idx, {**extra[0], 'phase': 'Descent', 'bank': 'E'})
            all_used_urls.add(extra[0]['url'])
            total_ms = sum(t['duration_ms'] for t in playlist)
            total_min = total_ms / 60000
        attempts += 1

    # If too long (> MAX_DURATION_MIN), remove the shortest non-anchor non-opening/closing track
    while total_min > MAX_DURATION_MIN:
        removable = [(i, t) for i, t in enumerate(playlist)
                     if t['phase'] not in ('Opening', 'Closing', 'Theme Anchor')]
        if not removable:
            break
        # Remove shortest track to minimize disruption
        removable.sort(key=lambda x: x[1]['duration_ms'])
        rm_idx = removable[0][0]
        playlist.pop(rm_idx)
        total_ms = sum(t['duration_ms'] for t in playlist)
        total_min = total_ms / 60000

    print(f"  Final duration: {total_min:.1f} min ({len(playlist)} tracks)", file=sys.stderr)

    return playlist


def format_playlist(playlist, theme=""):
    """Format the playlist as a readable report."""
    lines = []
    lines.append(f"# Yoga Playlist: {theme or 'Untitled'}")
    lines.append("")

    total_ms = sum(t['duration_ms'] for t in playlist)
    total_min = total_ms / 60000
    lines.append(f"**Total Duration:** {int(total_min)}:{int((total_ms % 60000) / 1000):02d}")
    lines.append(f"**Track Count:** {len(playlist)}")
    lines.append("")

    # Energy arc visualization
    lines.append("## Energy Arc")
    lines.append("```")
    phase_energy = {"Opening": 1, "Rising": 4, "Theme Anchor": 7, "Peak": 9, "Descent": 4, "Closing": 1}
    cum_time = 0
    for t in playlist:
        dur_min = t['duration_ms'] / 60000
        energy = phase_energy.get(t['phase'], 5)
        bar = "█" * energy + "░" * (9 - energy)
        lines.append(f"  {cum_time:5.1f} min  {bar}  {t['phase'][:7]:7s}")
        cum_time += dur_min
    lines.append("```")
    lines.append("")

    # Track listing
    lines.append("## Tracklist")
    lines.append("")
    lines.append("| # | Time | Phase | Bank | Artist | Title | Duration | Genre |")
    lines.append("|---|------|-------|------|--------|-------|----------|-------|")

    cum_time = 0
    for i, t in enumerate(playlist, 1):
        dur_min = t['duration_ms'] / 60000
        dur_fmt = f"{int(dur_min)}:{int((t['duration_ms'] % 60000) / 1000):02d}"
        time_str = f"{int(cum_time)}:{int((cum_time % 1) * 60):02d}"
        lines.append(f"| {i} | {time_str} | {t['phase']} | {t['bank']} | {t['artist'][:25]} | {t['title'][:40]} | {dur_fmt} | {t['genre'][:20]} |")
        cum_time += dur_min

    lines.append("")

    # SoundCloud URLs
    lines.append("## SoundCloud Links")
    lines.append("")
    for i, t in enumerate(playlist, 1):
        if t['url']:
            lines.append(f"{i}. [{t['artist']} - {t['title'][:50]}]({t['url']})")

    return "\n".join(lines)


def format_json(playlist, theme=""):
    """Format playlist as JSON for programmatic use."""
    total_ms = sum(t['duration_ms'] for t in playlist)
    return {
        'theme': theme,
        'total_duration_ms': total_ms,
        'total_duration_formatted': f"{int(total_ms/60000)}:{int((total_ms%60000)/1000):02d}",
        'track_count': len(playlist),
        'tracks': [{
            'position': i + 1,
            'phase': t['phase'],
            'bank': t['bank'],
            'title': t['title'],
            'artist': t['artist'],
            'duration_ms': t['duration_ms'],
            'duration_formatted': f"{int(t['duration_ms']/60000)}:{int((t['duration_ms']%60000)/1000):02d}",
            'url': t['url'],
            'genre': t['genre'],
            'bpm': t['bpm'],
            'tags': t['tags'],
        } for i, t in enumerate(playlist)]
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a yoga class playlist')
    parser.add_argument('--theme', type=str, default='', help='Class theme (e.g., "resilience", "letting go")')
    parser.add_argument('--spreadsheet', type=str, required=True, help='Path to TonyKoop_Yoga_Playlists.xlsx')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path (optional, prints to stdout if omitted)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--exclude-urls', type=str, help='Comma-separated URLs to exclude (for tracks not yet in spreadsheet)')
    parser.add_argument('--exclude-from-playlist', type=int, default=1,
                        help='Exclude tracks from numbered playlists >= this number (default: 1, i.e. all)')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    print("Loading song banks...", file=sys.stderr)
    banks, used_in_numbered = load_song_banks(args.spreadsheet)

    for letter, tracks in sorted(banks.items()):
        print(f"  Bank {letter}: {len(tracks)} tracks", file=sys.stderr)

    # Collect URLs used in ANY numbered playlist to avoid repeats
    # Tony's rule: a song should only appear on one numbered playlist ever
    used_urls = set()
    for url, playlists in used_in_numbered.items():
        for pl in playlists:
            num = pl.split('.')[0].strip()
            try:
                if int(num) >= args.exclude_from_playlist:
                    used_urls.add(url)
            except ValueError:
                pass

    # Also exclude manually-specified URLs (e.g. from playlists not yet in spreadsheet)
    if args.exclude_urls:
        manual_excludes = [u.strip() for u in args.exclude_urls.split(',') if u.strip()]
        used_urls.update(manual_excludes)
        print(f"  + {len(manual_excludes)} manually excluded URLs", file=sys.stderr)

    print(f"\nExcluding {len(used_urls)} tracks used in numbered playlists (>= {args.exclude_from_playlist})", file=sys.stderr)
    print(f"Generating playlist with theme: '{args.theme or '(none)'}'\n", file=sys.stderr)

    playlist = generate_playlist(banks, theme=args.theme, exclude_urls=used_urls)

    if args.format == 'json':
        output = json.dumps(format_json(playlist, args.theme), indent=2)
    else:
        output = format_playlist(playlist, args.theme)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)
