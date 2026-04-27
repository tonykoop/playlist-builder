# references/

This folder is where the song-bank spreadsheet lives at runtime — `TonyKoop_Yoga_Playlists.xlsx`.

It is **not** committed to this repo. The spreadsheet contains the author's personal music curation: 1,130 SoundCloud tracks across 5 song banks (A–E), plus the full history of 45 numbered playlists used for exclusion tracking.

## If you're forking this skill for your own use

You'll need your own catalog spreadsheet with this schema. Required sheets:

- **All Tracks** — every track in your catalog, one row per track
- **Playlist Summary** *(optional, used for analysis)*
- **Artist Summary** *(optional)*
- **Genre Summary** *(optional)*

### `All Tracks` columns (the script expects these positions)

| Column | Field | Required |
|--------|-------|----------|
| 1 | Playlist (which bank or numbered playlist this track belongs to) | yes |
| 8 | Position | yes |
| 9 | Title | yes |
| 10 | Artist | yes |
| 11 | Duration (ms) | yes |
| 12 | Duration (formatted, e.g. `4:23`) | optional |
| 13 | URL | yes |
| 14 | Genre | optional |
| 15 | BPM | optional |
| 16 | Play count | optional |
| 17 | Tags (space-separated keywords for theme matching) | optional |

### Bank naming

The `Playlist` column should use these exact names for the script to recognize banks:

- `A Bank: First & Last`
- `B Bank: Rising Energy`
- `C Bank: Theme Anchor`
- `Song Bank: High Energy - 15th-40th Minute`
- `E Bank: Descending Energy`

Numbered playlists (e.g. `41. inner strength`) are picked up automatically — anything starting with a number followed by a period.

## Generalizing beyond yoga

This whole reference structure is yoga-specific. The roadmap (see [issue #1](../../../../issues/1)) is to make it pluggable so spin / spa / party profiles each define their own bank schema and arc.
