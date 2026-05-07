# playlist-builder v2 — design notes

> Brainstorm + architecture sketch for the v2 generalization. Audience: Tony, future contributors, trainees curious how it works.

## TL;DR

v1 (current `yoga-playlist-builder`) is hard-coded to **one user** (Tony), **one context** (vinyasa yoga), **one platform** (SoundCloud), and **one catalog** (Tony's curated 1,130-track library). It's an excellent specialist tool — but a teacher trainee can't pick it up and use it without forking the whole catalog.

v2 makes four orthogonal things pluggable:

| Axis | v1 | v2 |
|---|---|---|
| **Context** (the arc shape) | hard-coded vinyasa | `contexts/*.json` profiles — Power Vinyasa, Sustained Power Flow, Sculpt, Restorative, spa, spin, party… |
| **Platform** (where playlists live) | SoundCloud only | SoundCloud + Spotify (read library + create), with adapter pattern for future Apple Music / YouTube Music |
| **Catalog** (the source of tracks) | Tony's xlsx of 1,130 hand-categorized tracks | three modes: (a) bring-your-own (user's Spotify/SoundCloud library, auto-categorized), (b) ship-with seed banks for catalog-less users, (c) Tony's catalog (still works as before for him) |
| **Intake** (how the user provides class params) | conversational | standalone HTML intake form bundled with the skill, plus conversational fallback |

## The core insight, restated

Three ingredients do all the work, regardless of context:

1. **Energy arc** — a named sequence of phases with target durations and an energy profile.
2. **Song banks** — the catalog partitioned by energetic role; each phase pulls from one or more banks.
3. **Exclusion tracking** — what's been used, so the system never repeats.

A power-vinyasa flow, a spin class, and a spa massage soundtrack all use the same machinery — they just plug different arcs and different bank schemas into it.

## What changes from v1

### 1. Pluggable context profiles → `contexts/*.json`

Each context is a JSON file that fully specifies the arc:

```jsonc
{
  "id": "yoga-power",
  "name": "Power Vinyasa (60-min, heated)",
  "duration_min": 60,
  "duration_acceptable": [58, 64],
  "padding_default_min": 5,            // user-overridable in intake
  "phases": [
    { "name": "Opening",      "bank": "A", "min_tracks": 1, "max_tracks": 2, "window_min": [0, 5],   "energy": 1 },
    { "name": "Rising",       "bank": "B", "min_tracks": 3, "max_tracks": 4, "window_min": [5, 20],  "energy": 4 },
    { "name": "Peak",         "bank": "D", "min_tracks": 4, "max_tracks": 5, "window_min": [20, 42], "energy": 9 },
    { "name": "Descent",      "bank": "E", "min_tracks": 3, "max_tracks": 4, "window_min": [42, 57], "energy": 4 },
    { "name": "Closing",      "bank": "A", "min_tracks": 1, "max_tracks": 2, "window_min": [57, 65], "energy": 1 }
  ],
  "theme_anchor": {
    "bank": "C",
    "window_min": [20, 45],
    "tracks": 1,
    "rationale": "Lyrics land after the teacher's intention talk."
  },
  "track_count_target": [13, 17],
  "notes": "Generic 60-min heated power vinyasa format used at most heated-yoga studios."
}
```

**Initial profiles to ship:**

| Profile | Duration | Distinct features |
|---|---|---|
| `yoga-power` | 60 min + buffer | Heated power vinyasa, steady build through Sun A, peak through Sun B (this is essentially v1 generalized) |
| `yoga-power-sustained` | 60 min + buffer | Slower build, longer Peak with more sustained intensity, dedicated drill block |
| `yoga-sculpt` | 60 min + buffer | Block-based: warmup → cardio block 1 → strength → cardio 2 → cooldown. Higher BPM throughout. No theme anchor in the same way (more "drop" moments) |
| `yoga-restorative` | 75 min + buffer | Slow throughout, no Peak, deep Descent, very long savasana |
| `spa-massage` | 60–90 min flat | Single low-energy "phase" that gently drifts, no peak |
| `spin-bike` | 45–60 min | Warmup → climb → sprint intervals → sprint → cooldown; BPM-locked phases |
| `party` | flexible | Rise → peak → afterparty; 1–2 "moment" tracks (theme anchors) |

**Key generalization:** the theme anchor concept becomes optional + multi-anchor. Sculpt has none. Party has 1–2.

### 2. Platform adapters → `platforms/`

Each platform is a small module with two methods: `read_library(user)` and `create_playlist(name, track_uris)`.

| Platform | Read | Write | Auth |
|---|---|---|---|
| SoundCloud | scrape from xlsx (current) or Selenium-style browser nav | browser automation (current) | manual login |
| Spotify | Web API `/me/tracks`, `/me/playlists`, `/audio-features` | Web API `POST /playlists/{id}/tracks` | OAuth (Claude Desktop already has the connector) |
| Apple Music | (later) MusicKit | MusicKit | (later) |

For the weekend MVP: **Spotify connector only** as the second platform. The Claude Desktop Spotify connector you have enabled exposes `search`, `create_playlist`, and `get_currently_playing`. We'll need:

- `mcp__spotify__search` — used to find seed-bank track URIs by `artist + title` for users without their own library
- `mcp__spotify__create_playlist` — used at the end to actually ship the playlist

If Spotify's MCP doesn't expose library-read, the catalog import flow uses the public Spotify Web API directly via OAuth (separate path; documented but not in MVP).

### 3. Three catalog modes

```
                    ┌─────────────────┐
                    │  Intake form    │
                    │  asks: do you   │
                    │  have a library?│
                    └────┬─────┬──────┘
                         │     │
                  YES ───┘     └─── NO
                   │                  │
                   ▼                  ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ Catalog import   │  │ Seed banks       │
        │ + auto-categorize│  │ (ship with skill)│
        └─────────┬────────┘  └─────────┬────────┘
                  │                     │
                  └──────────┬──────────┘
                             ▼
                  ┌──────────────────────┐
                  │  Bank-partitioned    │
                  │  track pool (A–E)    │
                  └──────────┬───────────┘
                             ▼
                  generate_playlist.py
```

**Catalog auto-categorization** uses Spotify's `audio-features` endpoint (or SoundCloud's tags as a weaker proxy) to bin tracks into A–E:

| Bank | Energy | Valence | Tempo | Acousticness | Notes |
|---|---|---|---|---|---|
| A (Opening/Closing) | < 0.3 | any | < 80 BPM | high | Ambient, meditative |
| B (Rising) | 0.3–0.6 | 0.3–0.7 | 90–115 BPM | mid | Building |
| C (Theme Anchor) | 0.4–0.8 | high | any | low | **Lyrics-prominent** — speechiness or detected vocals are the differentiator |
| D (Peak) | > 0.7 | > 0.5 | 115–135 BPM | low | Driving |
| E (Descent) | 0.3–0.6 | mid | 80–110 BPM | mid-high | Cooling |

Heuristics, not rules — the user can override any track's bank in the intake.

**Seed banks** are small (~30 tracks/bank, ~150 total) curated public libraries that ship with the skill. They're enough to build 8–10 playlists before exclusion runs out. The trainee can grow them by adding their own tracks after each class. We seed with tracks that:

- Are on Spotify (universally accessible)
- Have streaming licenses (no rare/regional)
- Cover the genre breadth Tony actually uses (electronic / ambient / melodic house / world music)

### 4. Standalone HTML intake form → `intake/intake.html`

A single self-contained HTML file with no external dependencies (everything inline). The skill instructs the LLM agent to open this file in the user's browser. The form posts JSON back to the agent (via copy-paste or `cowork.callMcpTool` if running in Cowork).

**Intake fields** (matching what you described):

| Field | Options | Default |
|---|---|---|
| Platform | Spotify / SoundCloud / Both / "I'll just take the tracklist" | Spotify |
| Class type | Power Vinyasa / Sustained Power Flow / Sculpt / Restorative / Yin / Massage-Spa / Spin-Bike / Party / Custom | Power Vinyasa |
| Duration | 30 / 45 / 60 / 75 / 90 min | 60 |
| Padding after | 0 / 1 / 5 / 10 min | 5 |
| Theme / intention | free text | (empty) |
| Catalog source | My Spotify library / My SoundCloud library / Seed banks (no library) | Seed banks |
| Must-include track | free text (artist + title) | — |
| Avoid track | free text | — |
| Repeat policy | Never (lifetime) / Per-quarter / Per-month / Allow | Never |

The form renders the energy arc dynamically as the user picks a class type, so they can see what they're committing to before clicking Generate.

## Open design questions

1. **Where does exclusion state live for non-Tony users?** Tony's xlsx tracks every numbered playlist. For trainees, we need a per-user exclusion file — probably `~/.playlist-builder/used_tracks.json` keyed by platform + track URI. Cleared by user command.

2. **Theme song selection without lyric data.** Tony's C bank is hand-curated for lyric prominence. For auto-categorized libraries, we'd ideally have lyrics (Genius API or Musixmatch) to score theme match. Without it, we fall back to title + tag matching, which is what v1 does. **For weekend MVP:** title + tag matching is fine.

3. **Class theme as energy modifier.** A "letting go" theme leans the playlist mellower; "fire and breath" leans it harder. The intake could have a 0–10 intensity slider that biases bank selection within the arc. **Not MVP.**

4. **Cowork artifact vs. standalone HTML.** We chose standalone HTML for portability across LLM agents. A future enhancement could detect Cowork and use a live artifact instead — but the standalone version is the lowest common denominator and works everywhere.

## What ships this weekend

| Item | Status target |
|---|---|
| Generalized SKILL.md describing the v2 skill | scaffolded with TODOs |
| 4 context profiles (Power Vinyasa, Sustained Power Flow, Sculpt, Restorative) as JSON | scaffolded; Power Vinyasa is fully specified, others are stubs with sensible defaults |
| `intake.html` intake form | functional standalone form; energy-arc preview is a stretch goal |
| Seed banks (small, public, ~150 tracks total) | folder structure + 1 example bank (A); rest are stubs to fill in |
| Spotify connector spec | written in `platforms/spotify.md`; no code yet |
| Generalized `generate_playlist.py` | scaffolded; reads context JSON instead of hard-coded constants |
| `INSTALL.md` for non-technical trainees | written |
| Updated repo `README.md` | already in good shape; light touch-up |

## Out of scope for v2 weekend ship

- Spotify Web API OAuth flow (catalog import) — design only
- Apple Music / YouTube Music — design only
- Class theme intensity slider
- Lyric-based theme matching
- Cowork artifact mode of the intake form
