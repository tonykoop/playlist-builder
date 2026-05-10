# Honesty modes

Playlist-builder must match its output shape to the catalog certainty available
in the local environment.

## `verified`

Use when platform auth is available or a bundled/user catalog contains verified
platform IDs rich enough to fill the requested context. Rows may be treated as
paste-ready only when they include a real Spotify URI or SoundCloud URL.

## `search-assisted`

Use when a concrete machine-readable catalog is loaded but some rows may be
search-string-only. Emit a tracklist, but every row must carry row-level
certainty fields such as `exact_id_status` and `verification_required`.

This mode requires concrete tracks. A Markdown reference to Tony's public banks
is not enough.

## `bank-scaffold`

Use when Tony Mode B documentation or bank metadata is present, but no concrete
track snapshot is available locally. Emit bank roles, phase slots, search
strings, and verification instructions. Do not emit named track claims except
for separately verified seed-bank tracks.

This is the Round 8 fix: it gives teachers useful bank-by-bank curation
scaffolding without implying that documentation-only Mode B references are a
search-assisted playlist.

## `sparse`

Use when only a few verified seed-bank rows exist. Keep verified rows visually
separate from scaffold or candidate rows.

## `manual-curation`

Use when no concrete catalog, seed tracks, platform auth, or bank references are
available. Emit only the energy arc and a curation prompt.

## Quick decision table

| local state | output mode |
|---|---|
| Platform auth available | `verified` |
| User catalog has concrete tracks | `search-assisted` |
| Tony Mode B snapshot has concrete tracks | `search-assisted` |
| Tony Mode B documentation/reference only | `bank-scaffold` |
| Only sparse seed tracks | `sparse` |
| No catalog/auth/bank references | `manual-curation` |
