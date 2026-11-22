# Development log: Legend of the River King 3 ~ From the Mysterious Forest ~

How the English patch for *Kawa no Nushi Tsuri 5: Fushigi no Mori kara* (Game Boy Advance, 2001) was made, in order. All dates are 2026. "The tester" is the human who started the project, made the naming and art calls, and playtested; "Claude" is the AI that did the hacking and translation. Addresses are in [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md).

## Starting point (27 Oct)
The tester asked for English patches for the GBA games in the series. Kawa 5 got its own project, separate from the 3 & 4 compilation. Base: the No-Intro ROM (4 MB, CRC32 `4A8F2F62`). No earlier translation was known. It followed the series glossary and the conventions of the earlier patches.

## Phase 1: engine (about 15 minutes of work)
- **Tools.** Claude set up headless mGBA (libretro) with a debugger, plus a unicorn-based ARM runner (`tools/k5lib.py`). The runner calls the game's own decompressor to unpack data, so the compression never had to be reimplemented.
- **Script.** Shift-JIS in 284 compressed blocks, with a pointer table behind the literal at `0x0803EBE0`. The scripts are bytecode, and their text ops carry the strings.
- **Font.** The font already had half-width English letters, so no new font was needed for dialogue.
- **Insertion.** The ROM is padded to 8 MB. The scripts are stored uncompressed from `0x08400000`, and a hook at `0x083F6000` copies them and tail-calls the decompressor for everything else. An English test line showed in game.

## Phase 2: translation and v0.9
- **Script.** 1,548 unique dialogue strings, plus about 800 pointer-referenced UI candidates (`tools/ui_strings.py`; many are false positives).
- **Translation.** Claude translated all of it, following the series glossary: dialogue in `src/text/script_en_*.txt`, and menus, items, 49 fish, the Fishing Note and the staff roll in `src/text/ui_en.txt`. `tools/wrap_script.py` wraps it to the 36-column, 3-line box.
- **Player name.** A hook converts full-width letters to ASCII with a capital first letter, so KEITA shows as "Keita" in dialogue. The default name is Keita (渓太). Claude chose this, and the tester accepted it.
- **Other choices by Claude:**
  - Money stays as G, as in the original.
  - The status labels are Pow/Skl, because only 4 columns fit.
  - The name-entry side buttons became ab, ★♪, ≪, ≫ and ok. The original buttons were compared by their kanji, so the replacements had to be characters that can't be typed.
- **Checked in the emulator:** menus, name entry, saving and the opening scenes. **Not checked:** the Fishing Note, shops, catching fish, the ending.
- **Title.** On a decision card about the English title, the tester chose to send their own mock-up.

## Phase 3: first playtest and logo (v0.9.1)
The tester found:
- the built-in English letter page on the name screen ("Guess that means we won't need to make an English keyboard!");
- a squashed letter m;
- runs of repeated ellipses from the original ("Perhaps in places where more than one ellipsis was used, we just use one?");
- Japanese 装備 graphics on equipped gear;
- "Comple" cut off on the Fishing Note;
- untranslated place names baked into the Fishing Note maps.

They noted that the fish entries and shop text looked good. They also sent logo art as one full image plus its parts, because the title animates in three stages.

Claude:
- built the logo from those parts (`tools/logo.py`, `src/art/river_king_3_*.png`): "Legend of / The River King" fades in, the 3 spins in where the original's 5 did, and the subtitle "~ From the Mysterious Forest ~" follows;
- changed the menu to New Game / Continue;
- cut every run of dots to one "...";
- changed "Comple" to "Done";
- widened the m to 5 pixels.

Claude also misread one of the tester's screenshots as a separate "big logo" screen. The tester explained it was only showing the three-part animation.

## Phase 4: v0.9.2
- **Subtitle m.** The tester pointed out that the subtitle still used the squat m, since it is drawn as text. It now uses the wide m and M.
- **Tester's save.** The tester sent their save file, which got Claude to the remaining screens.
- **Gear tag.** 装備 became **EQUIP** (`tools/tags.py`).
- **Map labels.** All six maps got English place names on lengthened scrolls: Nushikiri Village, Oven Kingdom, Cold Park, Coconut Village, Fairy Town and Mysterious Forest (`tools/maplabels.py`). Only one map was reachable with the save. The other five were checked by drawing the game's own map data.

The tester played on (28 Oct): "As far as I've played, I've not run into any more issues." v0.9.2 is the current release.

## Phase 5: publishing (21-22 Nov)
Published here; then the source, docs and this log were added. Rebuilding needed one change: the "New Game / Continue" letters were rendered with Noto Sans Condensed Bold, and that exact font file wasn't available. Claude decoded the two letter masks from the published patch into `src/art/menu_new_game.png` and `src/art/menu_continue.png`. `tools/logo.py` now reads those masks and only renders from the font when they're missing. With that, both patches were rebuilt from this folder and matched byte for byte. ROM paths that pointed at the original workspace were made relative (`src/rom/k5.gba`, or `K5_ROM`).

## How Claude worked
- **Tools it wrote:** a script decoder and encoder, a UI string scanner, the wrapper, the logo, tag and map-label builders, a THUMB disassembler (`tools/disarm.py`) and a libretro driver (`tools/retro.py`).
- **Checking its work:** screenshots from mGBA, checking both patch formats give the same ROM, and drawing screens from game data when they couldn't be reached.
- **What it couldn't do:** reach late-game screens without the tester's save, or tell which screenshot showed what without asking.

## Known gaps and ideas
- **Not played start to finish.** The ending and staff roll haven't been seen in play.
- **Map labels.** Five of the six were only checked by rendering.
- **Staff names.** Some are romanised best guesses.
- **Version note.** An older project note listed this game as v0.9.4. No such build exists; v0.9.2 is the newest.
