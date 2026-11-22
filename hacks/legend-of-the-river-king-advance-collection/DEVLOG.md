# Development log: Legend of the River King Advance Collection

How the English patch for *Kawa no Nushi Tsuri 3 & 4* (Game Boy Advance, 2003) was made, in order. All dates are 2026. "The tester" is the human who started the project, made the naming and art calls, and playtested; "Claude" is the AI that did the hacking and translation. Addresses are in [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md).

## Starting point (27 Oct)
The tester asked for English patches for the GBA entries of the series. The 3 & 4 compilation got its own project, separate from *Kawa no Nushi Tsuri 5*. Base: the No-Intro ROM (4 MB, CRC32 `4F09CA00`). No earlier translation was known, though both games had been released in the West in other versions: Kawa 3 as *Legend of the River King GB/GBC* and Kawa 4 as *Legend of the River King 2*.

## Phase 1: engine and tools
- **No ready-made emulator.** Building mGBA from source was refused in this environment, so Claude wrote its own small GBA emulator (`tools/gba.py`). It is CPU emulation through unicorn, plus a high-level BIOS and a numpy PPU, and it's good enough to boot both games, poke RAM and take screenshots. It is less accurate than a real emulator, which mattered later.
- **Text encoding.** Both games share one 8-bit encoding: 0-9, A-Z at `0A-23`, kana from `24`, and `F0-FF` control codes. The fonts are at `0xD2220` (game 4) and `0x1B51DC` (game 3).
- **English text.** English is drawn by a variable-width font hook on the glyph blit (`tools/vwf.py`, assembled with keystone). Code `0xEE` pads to the next tile.
- **Finding strings.** The Japanese was dumped with relative search and pointer scans (`tools/relsearch.py`, `tools/ptrscan.py`, `tools/sjscan.py`). Kanji labels were read with a small OCR (`tools/ocr.py`).
- **Menus.** Game 4 builds its menus from 16-bit tile streams and one label string per menu, rendered into tiles `E0+`. The patch rebuilds each stream (`tools/menus.py`). The kanji labels 体力 / お金 / 命令 and はい / いいえ are LZ77 graphics, replaced with HP / Yen / Cmd / Yes / No (`tools/gfx.py`).

## Phase 2: translation and v0.5
- **Translation.** Claude translated all dialogue in both games: about 400 lines in game 3 and 1,000 in game 4 (`tools/tr_g3_*.py`, `tools/tr_g4_*.py`).
- **Screens.** Also translated: title and file menus, name entry, game 4's menus and brother choice, and game 3's status panel and item windows.
- **Logos.** The tester chose on a decision card to send their own logo mock-ups. The first builds kept the Japanese logos.
- **Checking.** Claude confirmed both patch files reproduce the expected ROM.

## Phase 3: playtest rounds
The tester played each build in their own emulator and sent screenshots.

**v0.6 fixes, from the first round:**
- Game 3's Yes/No (save statue, inn) drew raw Japanese letters that the English font had overwritten.
- Game 4's command menu broke after the Gear window. A second routine was redrawing the menu at its old position.
- The Canoe Master's dialogue was garbled. That line had been missed by the first dump, so Claude rescanned both games and found no other misses.
- The Uocchi screens were translated, with fixes to the feeding window's garbled title and damaged bait icon.
- The Fishing Memo now reads Best / Avg. / Total.
- One report, "esEat" in the Fish slot at Plains Lake, could not be reproduced at first.

**v0.7 fixes, from the second round:**
- The Uocchi help text overflowed its box. It's now wrapped at 136 px.
- Game 3 shop titles and item pictures were garbled. Item names were translated, and prices use ¥ because the unit slot holds one character.
- Game 4 shop titles were garbled ("Hool"). Claude couldn't reach a game 4 shop from its saves, so it drew those windows by calling the game's own shop loader (`tools/g4force.py`).
- The "Go" command by the Plains Lake shops was the earlier "esEat" bug.
- The Fishing Memo stamps now read "Raised" and "Big One".

**v0.8, signs:**
- Building signboards in both games became pictures, matching the Umi and Shizen-ha patches: hook, fish, INN, and a shopping bag for game 4's general store.
- The tester liked it: "good job on being proactive with the grocery store sign".

**v0.9 fixes, from the third round:**
- The fish shop's "will you sell?" prompt ran off its box in both games. Yes/No now sit on the cells the cursor expects, using the pad code.
- The graphics of game 4's four memo books (fish, shell, bug, flower) were translated. Claude chose "Size" for 基本 and offered to match game 3's "Avg." instead.

## Phase 4: logos (v0.95, 28 Oct)
The tester sent three logos, explaining the naming: the collection logo, plus "Legend of the River King GBC" for Kawa 3 and "Legend of the River King 2" for Kawa 4 ("Classic, getting the games out of order lol"). Claude:
- put them on the start screen, including its zoom-in, and on the game select screen;
- painted the Japanese logos out of both title pictures (`tools/gbalogos.py`, `tools/titlecomp.py`, `tools/logo_mask.py`);
- gave every title sprite its own scaling matrix, because the engine had shared 8.

On Kawa 4's title the new logo covers the boy's chin, and the rocks behind it are partly redrawn.

## Phase 5: last graphics and script pass (v1.0, 28 Oct)
The tester asked to "make sure any graphics are translated, then do the pass". Claude:
- checked game 4's file panel with a real save, and game 3's tackle, creel and battle panels;
- found that game 4's rumble ON/OFF graphics never appear on screen, so left them alone;
- read about 1,440 lines and reworded about 75;
- matched item names across the two games (Pole S/L, Worms, Rubber Worm, Fly);
- made long boxes turn the page at the end of a sentence (`split_page` in `tools/insert.py`), so no page is left with one word.

Claude noted that its emulator could only spot-check the new text, and that changes this big deserve a playtest. **v1.0 has not been replayed by the tester.**

## Phase 6: publishing (21-22 Nov)
Published here; then the source, docs and this log were added. Both patches were rebuilt from this folder and matched byte for byte.

## How Claude worked
- **Wrote everything:** the emulator, disassembler (`tools/kdis.py`), tracers (`tools/ktrace.py`, `tools/strtrace.py`), map and tile viewers, the OCR, screenshot scripts for every release, and the release builder.
- **Checked its work:** screenshots from its own emulator, forcing screens it couldn't reach by calling the game's loaders, and checking that both patch formats give the same ROM.
- **What it couldn't do:** run a reference-accurate emulator, or play far enough to reach most NPCs and game 4's shops. Several real bugs (glitched menus, overflowing boxes) were only found by the tester.

## Known gaps and ideas
- **Untested saves:** saves made with the Japanese version have not been tested.
- **Untested sell prompt:** the game 4 fish shop sell prompt was fixed in layout but never seen live by Claude.
- **Unused rumble graphics:** game 4's rumble setting graphics are unused and untranslated.
