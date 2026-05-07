# Install — for yoga teachers, fitness instructors, and other non-developers

This skill lets you build a yoga (or spin, sculpt, spa) class playlist by chatting with an AI assistant. You don't need to know code. You do need:

1. A free [Anthropic Claude](https://claude.ai) account (or another LLM agent that supports skills — ChatGPT with a custom GPT, Cursor, etc.)
2. A Spotify or SoundCloud account, optionally
3. About 5 minutes

## The fastest path — Claude Desktop

If you have Claude Desktop on your computer:

1. Download this repo as a ZIP from GitHub: click the green **Code** button → **Download ZIP**.
2. Unzip it. You'll have a folder called `playlist-builder-main` (or similar).
3. Inside that folder, find `skills/playlist-builder/`.
4. Move that `playlist-builder` folder into Claude's skills directory:
   - **macOS:** `~/Library/Application Support/Claude/skills/`
   - **Windows:** `%APPDATA%\Claude\skills\`
5. Restart Claude Desktop.
6. Open a new chat and say: *"Build me a yoga playlist."* Claude will pick up the skill automatically.

## Using Claude on the web (claude.ai)

The web version doesn't yet support local skills, but you can paste the skill instructions directly:

1. Open `skills/playlist-builder/SKILL.md` in your browser or a text editor.
2. Copy everything between `---` and the end of the file.
3. Paste it as the **first message** in a new Claude conversation, with the prefix:
   *"Use the following instructions for our conversation:"*
4. Then say what you want: *"Build me a 60-minute power vinyasa yoga playlist with the theme 'aparigraha'."*

## Using ChatGPT, Cursor, or another LLM

Same as above — paste the contents of `SKILL.md` as your first instruction, then describe the class you want.

## What happens when you ask for a playlist

The skill will:

1. Open `intake/intake.html` in your browser to collect class details (or ask conversationally).
2. Generate a tracklist that follows the energy arc for that class type.
3. Optionally create the playlist on Spotify or SoundCloud (it'll ask permission first).
4. Save the tracklist as a markdown file you can keep for reference.

## I don't have my own music library yet

That's fine — the skill ships with **seed banks**, small starter libraries of public-domain and streaming-licensed tracks. You'll be able to build 8–10 classes before the seed banks run dry. By then you'll have a sense of what sounds work for you, and you can start collecting your own.

## Privacy

Nothing leaves your machine without your permission. The skill never automatically uploads your music history, library, or preferences anywhere. When it does call out to Spotify or SoundCloud, it asks first.

## Troubleshooting

**"Claude doesn't know about the skill."** Make sure the `playlist-builder` folder is directly inside the skills directory — not nested an extra level deep.

**"The intake form doesn't open."** It's a single HTML file at `skills/playlist-builder/intake/intake.html`. You can open it directly by double-clicking. If Claude can't open it for you, just open it yourself, fill it out, copy the JSON, and paste it back into chat.

**"Spotify says it can't find a track."** The auto-search occasionally picks the wrong version (live vs. studio, remix vs. original). Tell Claude: "Track 4 is the wrong version, look for the studio one." It'll fix it.

**"Some tracks don't have SoundCloud links."** That's expected — not every Spotify track is on SoundCloud and vice versa. The skill will warn you and skip them, or ask if you want a manual replacement.

---

Built for the [Heifer Zephyr](https://github.com/tonykoop) yoga teacher training cohort, but useful for anyone who DJs their classes from a curated library.
