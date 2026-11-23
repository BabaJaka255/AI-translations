# Development log: Legend of the Sea King: To Treasure Island (PS1)

This was written by Claude from the working session's notes and chat, in the order things happened. Dates are 2026, times UTC.

## Starting point
*Umi no Nushi Tsuri: Takarajima ni Mukatte* (Victor Interactive Software / Pack-In-Soft, 1999) is the PlayStation sea-fishing entry of the Nushi Tsuri series (known in English as *Legend of the River King*). It never had an English release or fan translation. The tester asked for English patches for every Nushi Tsuri game still missing one, and this repo already had the Hidden Lands PS1 patch (same engine family) and the Super Legend of the Sea King SFC patch (same developer, same fish and gear data). Those two were the starting points: Hidden Lands for the code, Sea King for the names.

The base is the Redump single-track BIN (CRC32 `DAD222F2`), dumped by the tester from their own disc. Claude copied it read-only from the tester's ROM folder and also needed a Japanese PS1 BIOS for emulator testing, which the tester provided.

## Phase 1: mapping the game (22 Nov, early hours)
- Extracted the disc's ISO9660 tree (`iso.py`). The main exe is `SLPS_021.72`; the font is in `TIM/COMM.TIM`.
- Lucky find: the disc ships `TIM/MAIN.SYM`, a PsyQ debug symbol file. Its addresses are from a slightly earlier build and drift (`msg()` sits 0xBCC lower in the real exe), but the names made the printer, the glyph drawer and the control-code table quick to find. `sym.py` turns it into `data/sym.txt`.
- The text format matched Hidden Lands closely: u16 glyph numbers, FFFF end, FFF4-FFFE control words. Kana were read from the font sheet; the 780 kanji were read by OCR against IPA Gothic followed by a dynamic-programming pass that uses Shift-JIS order (`font_ocr.py`, `font_dp.py`), then checked by hand. About 90 extra glyphs past the Shift-JIS block were read by hand.
- `refs.py` and `dump.py` found every string in the exe's text pool and every pointer to it (lui/addiu pairs and data words): about 1,890 strings.

## Phase 2: English text engine and first text (22 Nov)
- Ported the Hidden Lands design: 872 kanji glyph slots become English "cells" (1-4 letters of a DejaVu Sans Bold variable-width font per 16x16 tile), a `draw_word()` hook on the printer's three glyph sites, ASCII letter pairs and a dictionary of common words to keep strings short, and an inserter that relocates every string and rewrites its references.
- First English text appeared in the opening scene about 15 minutes after the engine was written.
- English name entry: the Japanese keyboard stored one kana per word and allowed 4 words. The patch pairs two letters into one word, so names go up to 8 letters, and backspace splits a pair.

## Phase 3: translation (22 Nov)
- Wrote a glossary and a character sheet first (`docs/glossary.md`, `docs/characters.md`). Fish, bait, gear and food names come from the Sea King SFC patch through a translation memory over that script and the Hidden Lands script (`tm.py`, `worksheet.py`).
- Translated about 1,870 strings in batches. Policy: keep honorifics as spoken (Yuko-san, Hachi-san), translate kinship words (Brother, Grandpa), American spelling, and keep the Mito Komon parody characters' period flavour. The tackle-shop owner おやじ became "Pops", which Claude flagged to the tester as unsure.
- Layout: messages are re-wrapped to the 224 px box; menus keep the Japanese column positions (`tabs.py` copies the Japanese tab stops). `warns.py` and `fitcheck.py` list anything wider than its box.
- **Test build 1** (03:53): full script, engine, name entry, menus and a first title logo. The xdelta round trip was checked, but fishing bites could not be triggered in the emulator, so catch results, shops, travel and the ending were untested at that point.

## Phase 4: art (22 Nov)
- **Test build 2:** all redrawn art switched from system fonts to hand-built brush lettering (`letters.py`: each letter is a skeleton of strokes, then shaded). The tester's standing rule for these hacks is that lettering is drawn in the style of the original, not typed in a font.
- **Title logo:** the tester asked whether the logo had to share a sheet with the START button and the water. It does: one 256x256 texture with one palette, so the logo must stay in rows 64-207. The tester showed some logos made with another AI image tool, rejected them, and asked for a dedicated logo thread. A separate Claude session drew the logo from the tester's references (the Legend of the River King GB box logo and the unreleased Sea King GB title screen). Feedback rounds: the lettering had to really match the localized logos; the marlin needed its tail and then had to be the original marlin reconstructed, not a new fish; the rod must not span the logo; the orange ball is a coconut by the palm. Version 3 in the yellow-on-top colouring was approved ("B looks great. Very good."). The code is kept in `src/tools/logo/`; the finished band is `src/gfx/title_logo.png`.
- **Test build 3:** the approved logo in the game, checked on the title screen.
- **Test build 4:** faint banner "...REVIVING!..." hand-pixelled in the original's block style (the second copy is the first turned 180 degrees, as in the original), and the staff roll and "The End" redrawn on all 15 pages. No romanized credit list was found online (the big credit databases refused automated access), so the readings of names written only in kanji are Claude's guesses: 陳奇明 Qiming Chen, 三間規公 Norihiro Mima, 鈴木智満 Tomomitsu Suzuki, 石橋由布子 Yuko Ishibashi, 玄田貢一郎 Koichiro Genda, 関根彰規 Akinori Sekine, 瀬高智恵子 Chieko Setaka, 吉岡宏夫 Hiroo Yoshioka, 鈴木寿枝 Hisae Suzuki, 唐戸光博 Mitsuhiro Karato, トゥキャン Toucan Ltd., 遊遊 Yuyu Ltd. 小池幸恵 = Sachie Koike is confirmed by the voice credit.
- Dead end: setting HP to 0 in RAM does not trigger a faint, so the banner could not be seen in the emulator yet.

## Phase 5: the tester's first playtest (23 Nov)
The tester played test build 4 and reported:
- Fainting comes from exhausting yourself swimming or from a fight; "The banner looks good."
- "Shop signs are untranslated graphics. In the shops, the options are off-center of their menu box and run off the edge."
- "Fish names are untranslated on the Fishing Note map screen."
- "I caught a fish - the fish name is slightly offcenter."

**Test build 5** fixed all four: shop plaques redrawn on the four village maps; the shop menu box widened 8 px (two immediates at 0x8003E0A4/AC) with re-spaced columns; English Fishing Note map labels in a tiny hand-pixelled font packed into the label atlas (`labels.py`); the fish page title centred by its measured width (this also caught a bug where the title template would have printed "Caught {A}!"); and the name-entry cursor following the name, with one-letter backspace. Claude also translated the developer warning screen (KEIKOKU.TIM) and swept every TIM on the disc for Japanese.

The tester then pointed out that the shop plaques in these hacks always use the same icons: "The fishery had, a fish obviously. The Bait shop had a fish hook, and the inn was the only one that actually read out a word, 'Inn'." Claude had that convention in its notes but hadn't checked it. **Test build 6** used the same 11x11 icon art as the Hidden Lands and Sea King patches.

The tester also said not to re-encode the ending movie, so the one Japanese shop sign inside END2S.STR stays.

## Phase 6: Claude's own sweep (23 Nov, overnight)
The tester asked for the remaining work to be finished without supervision: no missed strings or graphics, no text run-off, no glitches.
- **Family message board (test build 7):** the board's pencil cursor and line-full test counted 8 or 16 px per word, so the English pencil drifted and lines broke after about 13 letters. New engine routines measure the drawn width (board_x, board_w, board_fix, board_room); lines now hold 27 letters (the Japanese word limit), and the row-2 keys that typed 、。゛゜ now type `, . " :`. Two mistakes along the way: a `jal` inside the engine source was assembled by Keystone as a `$gp`-relative load (fixed with `bgezal $zero`), and a jump was first placed in a branch delay slot (moved). A test that typed a dictionary word on OK turned out to be a stale save state, not a bug.
- **Reaching untested screens:** fish bites never came in the emulator. Claude wrote `strview.py`, which overwrites one NPC's line in RAM with any string id, to see every catch, got-away, damage and item message in a real box with the longest names (Bartail Flathead, Polarized (Shallow), Humpback Whale). Then it found the shop dispatcher, rankings, staff roll and faint banner routines, and pointed the Jetty cat's NPC code at each one in RAM, so they could be opened and played (recipe in `docs/ENGINE_NOTES.md`).
- **Bugs found that way (test build 8):**
  - Rankings board: the long place name "Treasure Island" crossed x=256. Sprite x is 8-bit, so the rest wrapped to the left edge and showed "and." there. Fixed with "Treasure Isl." in that column (a new place_ptr routine) and the columns moved left; the header became "Size".
  - Fish shop and keep net sell list: "yen" ran past the box edge. The size/price column moved 16 px left and the headers moved to match.
  - Five lines were missing a space after the speaker's name.
- Also seen in the emulator: selling fish (all and one at a time), buying a rod, the inn, saving, the boatman's fare, the full staff roll to "The End" and the REVIVING! banner, the whole opening story, diving ("Found Small Abalone.") and fishing mode.
- Eleven strings could not be written in place and have no reference anywhere in the code or data (checked for lui/addiu halves and pointers in the original exe). They are dead text and stay Japanese.

## Phase 7: the tester's second playtest and 1.0 (23 Nov, afternoon)
The tester played test build 8 on a phone and reported: "When I check the fishing note, however, the option for the Black Porgy page on the map says Bluefin Tuna. Either an uncaught fish still populates the map with an entry ... or the labels themselves are incorrect per fish."

It was the labels. `labels.py` assumed fish table entry i is named by string 740+i. The table's own name pointers drift away from that: entry 32 points at an empty string and later entries skip ids, so 65 of the 97 labels were on the wrong fish. The test data used for test build 5 only covered early entries, which were right. The labels now come from each entry's own name pointer, and the ten entries with an empty Japanese name get no label. Checked on the Jetty map in the emulator. The tester then called the patch done, and that build is 1.0.

## How Claude worked
- Wrote all the tools in `src/tools/`: disc reader and sector writer, dumpers, OCR, inserter and engine, graphics builders, layout audits and a headless Beetle PSX driver for screenshots.
- Checks: every test build was re-applied to the original with xdelta and compared; static layout audits after each script change; in-game screenshots from fresh boot states (old states keep stale glyph numbers and look garbled after a rebuild, which cost some time early on). Before publishing, a fresh copy of this folder rebuilt the 1.0 patch byte for byte.
- What Claude could not do: hold a controller or play in real time, so fishing (bites and fights) was only played by the tester; Claude also couldn't judge the art the way a person does, so the logo went through the tester's review rounds. It never ran the game on real hardware.

## Known gaps and ideas
- The ending movie END2S.STR still shows one Japanese shop sign (an MDEC re-encode would fix it).
- Staff-roll name readings are guesses (listed above).
- Boat travel to the other areas and the tournaments in later areas were not played through by Claude; their text was checked with the layout tools and the string viewer only.
- Not tested on real hardware.
- Short system lines keep the Japanese two-line shape on purpose ("Found / Small Abalone."), since the layout follows the Japanese width for non-dialogue strings. A pass to join those would be cosmetic.
