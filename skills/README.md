# skills/

This directory holds the actual skill bundles that ship with playlist-builder. Each subfolder is a self-contained context profile — a SKILL.md, scripts, and references for a specific use case.

## Current skills

- **[yoga-playlist-builder](./yoga-playlist-builder/)** — the original. Builds 65-min vinyasa class playlists from the author's SoundCloud song banks, with browser automation for SoundCloud playlist creation.

## Planned skills

The pluggable-profile vision in [issue #1](../../../issues/1) adds these as siblings:

- `spin-playlist-builder` — 45-min spin class, BPM-aware
- `spa-playlist-builder` — 60–120 min ambient
- `group-fitness-playlist-builder` — circuit-style, BPM-locked per segment
- `party-playlist-builder` — long-form, peak in middle third

Each will share the core abstractions (energy arc, song banks, exclusion tracking) and differ in profile-specific details.

## Skill format

These follow the [Anthropic skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) convention:

```
skills/<name>/
├── SKILL.md        # frontmatter (name + description) + instructions
├── scripts/        # executable code the skill calls
└── references/     # data files the skill reads (catalog, etc.)
```

The skill is invoked by Claude (via Cowork, Claude Code, or any Agent SDK host) when the user's request matches the SKILL.md description.
