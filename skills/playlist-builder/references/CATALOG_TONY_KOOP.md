# Tony Koop's catalog — public, opt-in

Tony Koop is a Heifer Zephyr yoga instructor who has curated ~1,130 tracks across 5 energy banks over 36+ public vinyasa classes. He's offered the catalog for use by teacher trainees.

## How to access

Tony's catalog lives on **SoundCloud**: [soundcloud.com/tonykoop](https://soundcloud.com/tonykoop)

The five banks are public playlists:

| Bank | Playlist on SoundCloud | Energy / role |
|---|---|---|
| A | "A Bank: First & Last" | Opening + closing, ambient, no-percussion |
| B | "B Bank: Rising Energy" | Warmup, building, progressive house & melodic electronica |
| C | "C Bank: Theme Anchor" | Lyrics-prominent tracks for theme songs |
| D | "Song Bank: High Energy - 15th-40th Minute" | Peak, house / dance / EDM |
| E | "E Bank: Descending Energy" | Cooldown, downtempo, melodic |

## How the skill uses it

When a user picks "Tony Koop's public catalog" in the intake form, the skill:

1. Checks whether a concrete, machine-readable Mode B track snapshot is available.
2. If concrete tracks exist, treats those tracks as the user's starting catalog (Mode B) and emits `search-assisted` output with row-level certainty.
3. If only bank metadata/documentation exists, emits `bank-scaffold` output: phase slots, bank roles, search strings, and verification instructions, but no named track claims.
4. Maintains a separate exclusion file per user (each trainee has their own "what I've used" set, distinct from Tony's).

The machine-readable bank-reference path is `references/tony-mode-b-snapshot.json`. It is intentionally documentation-only until a categorized track export is available.

## How to mirror to Spotify

Most of Tony's catalog is on Spotify too. To mirror the SoundCloud banks to Spotify for trainees who prefer Spotify:

1. Use **Soundiiz** (soundiiz.com) — free tier handles ≤200 tracks/transfer, paid handles bulk.
2. Or **TuneMyMusic** (tunemymusic.com) — similar service.
3. Or write a small script that reads the xlsx, queries Spotify search for each track, and writes a categorized JSON catalog.

Note: ~10–15% of tracks may be SoundCloud-exclusive (uploads from individual artists not on Spotify). Those get flagged "**not on Spotify**" in the generated tracklist; the user can substitute or skip.

## Attribution

When trainees publish playlists built using Tony's catalog, the suggested attribution line is:

> Catalog seeded from Tony Koop's vinyasa banks · github.com/tonykoop/playlist-builder

This isn't a license requirement — it's good karma.

## Limits

- Tony's banks are **not** auto-categorized by Spotify audio-features — they're hand-curated. The bank assignments reflect Tony's taste and class style. Trainees with very different taste profiles may want to use Tony's catalog as inspiration / reference rather than as their primary source.
- The catalog continues to grow as Tony teaches new classes. The xlsx in `references/TonyKoop_Yoga_Playlists.xlsx` is a snapshot — refresh periodically.
- A public bank reference is not the same as a verified track snapshot. Do not mark Mode B rows as `verified` unless the local JSON contains concrete platform IDs or the platform lookup has been run.
