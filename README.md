# playlist-builder

Context-aware playlist generator. Builds energy-mapped tracklists from a curated music library and creates them on a streaming platform.

Started as a yoga-class playlist tool I use every week. Generalizing to other contexts where music carries an emotional arc — spin, group fitness, spa, parties — and to multiple streaming platforms.

---

## Status

**v0.1** — yoga + SoundCloud only. Mature and used in production by the author. Multi-context and multi-platform expansion is the next milestone (see [#1](../../issues/1)).

---

## What it does today

The `yoga-playlist-builder` skill (runs as a [Cowork](https://www.anthropic.com) plugin / Claude Agent SDK skill) generates a 65-minute vinyasa class playlist mapped to a 6-phase energy arc:

```
Opening (A) → Rising (B) → Peak (D) → Theme Anchor (C) → Descent (E) → Closing (A)
                                       ↑ placed 20–45 min in
```

**Inputs:** a class theme (e.g. "surrender", "letting go", "showing up") and an optional playlist number.

**Outputs:** a markdown tracklist with energy-arc visualization, and (optionally) a SoundCloud playlist created via browser automation.

---

## The model

Three concepts do all the work:

**1. Energy arc.** A named sequence of phases with target durations. Each phase has a distinct energetic role. The arc is derived empirically from 36+ existing playlists.

**2. Song banks.** The catalog (1,130 tracks for the yoga build) is partitioned into banks (A–E) by energetic role. Each phase pulls from a specific bank.

| Bank | Role | Used in phases |
|---|---|---|
| A | Gentle, opening/closing | Opening, Closing |
| B | Rising, building energy | Rising |
| C | Theme anchor (lyrically prominent) | Theme Anchor |
| D | Peak energy | Peak |
| E | Descending, gentle | Descent |

**3. Exclusion tracking.** Once a track is used in a numbered playlist, it's excluded from future builds. No repeats across the catalog. This is what makes it possible to teach 50+ classes without recycling.

A fourth piece — **theme matching** — picks the C-bank track whose lyrics best fit the class theme. This is the only track in a yoga set with prominent lyrics and it's where the class's emotional message lands.

---

## How to use it

1. Open Cowork, install the `yoga-playlist-builder` skill.
2. Ask: *"Create playlist 43 about surrender"* or *"Build a yoga playlist with lyrics about letting go."*
3. Review the generated tracklist (you can iterate — swap tracks, adjust the C-bank pick, etc.).
4. Optionally have the skill create the SoundCloud playlist for you. Chrome must be open and logged in to soundcloud.com — the skill drives the UI directly.

If you create playlists outside the tool, pass `--exclude-urls` with those track URLs so they're added to the exclusion set.

---

## Where this is going

The energy-arc / song-bank / exclusion pattern isn't yoga-specific. Any context where music shapes an experience over time has the same components:

| Context | Arc shape | Bank schema | Theme anchor? | Exclusion |
|---|---|---|---|---|
| Yoga vinyasa | 6-phase up-and-down | A–E by phase role | Yes (C bank) | Lifetime (no repeats ever) |
| Spin class | warmup → climbs → sprints → cooldown | warmup / climb / sprint / cool | No | Per quarter |
| Group fitness | circuit-style, BPM-locked | by BPM band | No | Per month |
| Spa | low ambient throughout, drift down | ambient / deep ambient / sleep | No | Optional |
| Party | rise → peak → afterparty | starter / peak / comedown | Yes (1–2 moment tracks) | Per event |

Adding **pluggable context profiles** + **pluggable platform connectors** is the v1 roadmap. See [#1](../../issues/1).

---

## Roadmap

- [ ] Spotify connector (Web API + OAuth) — [#1](../../issues/1)
- [ ] Context profiles for spin, group fitness, spa, party — [#1](../../issues/1)
- [ ] Catalog import + auto-categorization (BPM, valence, energy) from existing Spotify/SoundCloud libraries
- [ ] Web UI for non-Cowork users
- [ ] Apple Music / YouTube Music connectors

---

## License

MIT — see [LICENSE](./LICENSE). The author's personal song-bank catalog is not included in this repo.

---

*Built by [@tonykoop](https://github.com/tonykoop) — mechanical R&D engineer by day, yoga teacher by evening, AI-augmented in both.*
