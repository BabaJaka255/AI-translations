# Development log: Tsuri Tarou (English)

How this patch was made, in order. All dates are 2026. "The tester" is the human who asked for the project, made the calls on naming and art, and playtested; "Claude" is the AI that did the hacking and translation. Details on every address are in [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md).

## Starting point (26 Oct)
The tester had just worked with Claude on English patches for *Kawa no Nushi Tsuri 2* and *Umi no Nushi Tsuri*, and picked *Tsuri Tarou* (Super Famicom, 1994, Pack-In-Video) as a from-scratch test, saying it probably "doesn't use the same engine as the previous two". No earlier translation or documentation was known. The base was the No-Intro ROM (8 Mbit, CRC32 `BBBFF8D8`).

## Phase 1: engine survey
- **Identifying the engine.** Header and vectors read by hand. Claude confirmed it is a different code base from the Nushi Tsuri games: no LZSS, no 16x16 kanji font, no `$82` text loops. Only the methods carried over, not the code.
- **Getting into the game.** The headless emulator (snes9x through stable-retro, `tools/emu.py`) booted into a looping waterfall attract scene. It only ends after three dragonflies are caught, so Claude poked the three counters (`$09B2/$09B4/$09B6`) to reach the title. Save states for each milestone are in `src/states/`.
- **Finding the text.** The 8x8 font was found uncompressed at ROM `0xAE000`, and its kana-grid encoding was mapped (`src/data/tt_8x8.tbl`). The fish-guide strings decoded straight away. The prologue was not stored as text at all: a trace of ROM reads while the page typed out (`tools/trace.py`, running the River King toolkit's 65816 simulator from a save state) showed it is a raw 32x32 screen tilemap at `0x40000`.
- **Result:** three kinds of text (F0-terminated strings, raw story tilemaps, pre-drawn 2bpp label art), no compression, and no free space anywhere in the ROM.

## Phase 2: script inventory
Claude walked every reachable screen and wrote `out/script.json` / `out/script.xlsx`: 183 entries with ROM location, Japanese, and the space available (15 spot signs x 5 lines at 22 columns, 5 story pages, 29 menu labels, fish names in 3 places, the backup-error message, the HUD). The "PASWORD" glyphs in the font turned out to be unused.

## Phase 3: expansion
`tools/expand.py` doubles the ROM to 16 Mbit and fixes the checksum. Checked two ways: about 5,000 frames of play (boot, title, file select, prologue, map, fish list, a sign, fishing) were identical to the original, and code traces from five save points never touched the new area.

## Phase 4: font
English A-Z, a-z, digits and punctuation were drawn as plain-text pixel art (`src/data/en_font.txt`) and written into both copies of the font (main at `0xAE000`, story font at `0x1B000`). Tested on a sign and a story page. One limit was found: story pages can't show the digit 0, because that tile is the blank on those screens.

## Phase 5: translation and insertion
- **Who translated:** asked whether to supply the English, the tester said: "go ahead and do it yourself." Claude wrote the whole translation (`src/text/signs_en.txt`, `src/text/story_en.txt`).
- **Spot signs:** each bullet got up to two 21-column lines where the Japanese used one, written on the sign's own text layer and repointed into the new space.
- **Story pages:** written back into the page tilemaps. The opening was checked live; the other four were first rendered with the game's font, then forced on screen through memory flags in phase 7.
- **Name entry:** the tester chose an English-only keyboard ("I think just English is fine").
- **Menus:** labels redrawn in a new 8x16 font made from the 8x8 one.
- **Fish names:** drawn as 8x16 letters on the signs. The records screen needed a small code hook, because the game loads that screen before the fish is chosen.
- **Logo:** the tester chose to keep the original つり太郎 logo.

## Phase 6: testing (v0.9)
The tester asked how Claude planned a full playthrough ("I seem to recall you had to modify memory just to get past the title screen") and offered to test in their own emulator instead. Claude agreed this was the better test: it could press buttons but could not actually play (it hooked a fish and couldn't land it). Claude forced the remaining story pages and the ending through memory edits, built the IPS, checked that it reproduced the build exactly, and wrote a checklist (`docs/TESTING_v0.9.md`). The tester played it and reported: "It all looks good!"

## Phase 7: series glossary (v0.9.1, 27 Oct)
The tester asked that all the patches use the names from their *Super Legend of the River King* v1.3 glossary. Claude changed River Nushi to River King, Yamame to Masu Trout, and Herabuna to White Crucian ("W.Crucian" in the 11-letter fish list). Dough bait became paste bait, the records column 釣果 became "Got", and the boy became Taro. Claude rebuilt and checked the changed screens in the emulator. **v0.9.1 has not been playtested by the tester.**

## Phase 8: publishing (21-22 Nov)
Patch published to this repository, then this source, docs and log were added. The published patch was rebuilt from this folder and matched byte for byte.

## How Claude worked
- Wrote its own tools: emulator driver, savestate reader/patcher, 65816 tracer, VRAM-to-ROM mapper, tilemap and font renderers, and the build and IPS scripts.
- Checked its work with screenshots from the emulator, frame-by-frame comparisons against the original, code traces, and by re-applying the patch to a clean ROM.
- Couldn't do itself: play the game properly, reach the erase-confirm screen with a real save, or judge whether the result feels right. Those were the tester's.

## Known gaps and ideas
- The Erase Data confirmation was only rendered, never seen live.
- The records screen blanks the screen briefly while drawing the fish name; a one-frame flicker is possible.
- An English logo was discussed and left for a later version.
