---
name: yoga-playlist-builder
description: "Build yoga class playlists from Tony's SoundCloud song banks. Use this skill whenever the user wants to: create a new yoga playlist, generate a class playlist, build a vinyasa flow playlist, pick songs for a yoga class, curate music for a yoga session, or asks about the energy arc of a yoga class. Also trigger when the user mentions song banks (A/B/C/D/E banks), energy phases, class themes, or wants to analyze existing playlists for patterns. This skill knows Tony's complete music library (1,130 tracks across 5 song banks) and the energy arc model derived from 36 past yoga playlists. IMPORTANT: also use this skill when the user wants to create a SoundCloud playlist from a generated tracklist — it includes browser automation steps."
---

# Yoga Playlist Builder

You are building a ~65-minute yoga class playlist for Tony, a yoga instructor who curates electronic/ambient music to match the energy arc of a vinyasa flow class. The extra minutes beyond 60 provide a meditation buffer — if Tony's class runs slightly long, calming music is still playing during final savasana.

## How Tony's System Works

Tony organizes music into **song banks** by energy level, then assembles class playlists that follow a specific arc. Think of it like a DJ set — the music IS the class experience, guiding students through warmup, peak flow, cooldown, and meditation.

### The Song Banks

| Bank | Name | Energy | Track Count | Purpose |
|------|------|--------|-------------|---------|
| A | First & Last | Very Low | 50 | Opening meditation & closing savasana |
| B | Rising Energy | Low → Mid | 150 | Warmup, building momentum |
| C | Theme Anchor | Variable | 47 | Lyrical songs matching the class theme |
| D | High Energy | High | 93 | Peak flow sequences, power poses |
| E | Descending Energy | Mid → Low | 154 | Cooldown, floor work, stretching |

### The Energy Arc

Derived from analyzing 36 of Tony's actual class playlists:

```
  Energy
  9 │                    ██                         <- PEAK (D Bank)
  8 │                ██  ██  ██
  7 │            [C] ██  ██  ██
  6 │                ██  ██  ██  ██
  5 │        ██  ██  ██  ██  ██  ██                 <- BUILD (B Bank)
  4 │    ██  ██  ██  ██  ██  ██  ██  ██
  3 │██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  2 │██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  1 │██                                      ██  ██ <- CALM (A/E Banks)
    └─────────────────────────────────────────────
     0    5   10   15   20   25   30   35   42   57   65+ min
                          ^C inserted here (20-45 min)
```

### The 6 Phases

1. **Opening (0-5 min)** — 1-2 tracks from **A Bank**
   - Ambient, no percussion, grounding. Students are arriving, settling in.
   - Genres: Ambient, New Age, Meditation, Downtempo

2. **Rising (5-20 min)** — 3-4 tracks from **B Bank**
   - Gentle build. Sun salutations begin. Progressive house, melodic electronica.
   - Tony does theme-setting and intention talk during the first 15 minutes, so the music supports but doesn't overshadow his voice.
   - Genres: Progressive House, Melodic House, Electronica

3. **Theme Anchor (20-45 min)** — 1 track from **C Bank**
   - A lyrical song whose words connect to the class theme.
   - IMPORTANT: This track must NOT appear before the 20-minute mark. Tony spends the first 15+ minutes talking about the theme/intention, so the theme song lands AFTER that talk, during peak energy. It sits within the Peak phase, placed at or after minute 20 and before minute 45.
   - This is the emotional heart of the playlist — pick based on theme keywords.

4. **Peak (20-40 min)** — 4-5 tracks from **D Bank**
   - Highest energy. Standing power sequences, warriors, balances.
   - The Theme Anchor (C) is inserted among these tracks, typically as the 1st or 2nd peak track.
   - Genres: House, Dance, EDM, Trance, Progressive

5. **Descent (42-57 min)** — 3-4 tracks from **E Bank**
   - Cooling down. Floor work, hip openers, twists, forward folds.
   - Genres: Downtempo, Chillout, Melodic, Electronica

6. **Closing (57-69 min)** — 1-2 tracks from **A Bank**
   - Final rest / savasana. No percussion, ambient drones, meditation music.
   - Provides meditation buffer so calming music continues if class runs long.
   - Genres: Ambient, Meditation, Drone

### Key Constraints

- **Target duration**: 65 minutes (acceptable: 63-69 min, NEVER exceed 70 min)
- **Track count**: 13-17 tracks (median 15)
- **No repeats**: Never use a song that appeared in ANY numbered playlist (check against all numbered playlists >= 1)
- **Genre flow**: Transitions between tracks should feel natural — avoid jarring genre shifts
- **Theme song placement**: The C Bank track MUST land between minutes 20-45 (after Tony's theme talk)

## How to Generate a Playlist

### Step 1: Get the theme (if not provided)
Ask the user for:
- **Class theme** (e.g., "resilience", "letting go", "gratitude")
- **Playlist number and name** (e.g., "41. inner strength") for SoundCloud
- **Any must-include songs** (optional)
- **Any songs to avoid** (optional)
- **Target duration** (default: ~63 minutes)

### Step 2: Generate the tracklist
Run the playlist generator script:
```bash
python <skill-path>/scripts/generate_playlist.py --theme "theme name" --spreadsheet <path-to-spreadsheet>
```

If no spreadsheet path is available, check these locations:
- `references/TonyKoop_Yoga_Playlists.xlsx` (bundled with skill)
- The user's cowork_inbox folder
- Ask the user to provide it

### Step 3: Review and refine
Present the generated playlist showing:
- Track order with timestamps
- Bank/phase assignment
- Total duration
- The energy arc visualization

Ask if the user wants to swap any tracks, adjust energy, or modify the theme song choice.

### Step 4: Output the markdown
Save as a formatted markdown file showing the final playlist with all metadata and SoundCloud links.

### Step 5: Create the SoundCloud playlist (browser automation)
If the user wants to create the playlist on SoundCloud, use the Claude in Chrome browser tools. The user MUST be logged into SoundCloud first.

**The automation flow:**

#### For the FIRST track (creates the playlist):
1. Navigate to the first track's SoundCloud URL
2. Click the "..." (More) button using JavaScript:
   ```javascript
   document.querySelector('.listenEngagement .sc-button-more').click();
   ```
3. Wait ~1 second, then click "Add to Playlist" from the dropdown menu
4. In the modal, click the **"Create a playlist"** tab
5. Type the playlist name (e.g., "41. inner strength")
6. Toggle the privacy to **Private**
7. Click **Save**

#### For EACH subsequent track (adds to existing playlist):
1. Navigate to the track's SoundCloud URL
2. Click the "..." (More) button:
   ```javascript
   document.querySelector('.listenEngagement .sc-button-more').click();
   ```
3. Wait ~1 second, then click "Add to Playlist" from the dropdown
4. In the modal, the "Add to playlist" tab shows all playlists. Find the target playlist by name and click its **"Add to Playlist"** button
   - Use the Filter input at the top to search by playlist name if needed
5. Close the modal (click X or press Escape)
6. Proceed to the next track

#### Important automation notes:
- Wait 1-2 seconds between major actions (page navigation, modal opening) for SoundCloud to load
- After navigating to a track URL, wait for the page to fully load before clicking buttons
- The "More" dropdown has two items: "Add to Playlist" and "Station" — click "Add to Playlist"
- The modal has two tabs: "Add to playlist" (list of existing playlists) and "Create a playlist"
- Each playlist row shows the name, track count, privacy badge, and an "Add to Playlist" button
- After adding, the button changes to "Added" — use this to verify success
- Ask the user for permission before starting the browser automation, since it will click buttons on their behalf
- Process tracks IN ORDER (track 1 first, track 2 second, etc.) to maintain playlist order on SoundCloud

## For Analysis Tasks

If the user asks about patterns in their playlists (most-used artists, genre distribution, BPM analysis, etc.), use the spreadsheet data in `references/TonyKoop_Yoga_Playlists.xlsx` which contains all 1,130 tracks across 45 playlists with full metadata.

Read the spreadsheet with:
```python
import openpyxl
wb = openpyxl.load_workbook('<path>/TonyKoop_Yoga_Playlists.xlsx', data_only=True)
# Sheets: 'All Tracks', 'Playlist Summary', 'Artist Summary', 'Genre Summary'
```
