# Engine notes: Umi no Nushi Tsuri: Takarajima ni Mukatte (PS1, SLPS-02172)

Addresses are RAM addresses in the main executable unless noted. The engine is the same family as *Kawa no Nushi Tsuri: Hikyou o Motomete* (see `../legend-of-the-river-king-hidden-lands/docs/ENGINE_NOTES.md`); its English hook was the model for this one.

## Disc
- Single-track MODE2/2352 BIN, 117,844,608 bytes, CRC32 `DAD222F2`.
- Main executable `SLPS_021.72` at LBA 35795, 997,376 bytes, loads at 0x80010000 (file offset = RAM - 0x8000F800).
- `TIM/COMM.TIM` at LBA 33469: 6 TIMs of 33,312 bytes (4bpp, 64x256 halfwords each). Image 0 is UI art and the Fishing Note map label atlas; images 1-5 are the font (256 glyphs of 16x16 each).
- `TIM/MAIN.SYM` (1.4 MB) is a PsyQ debug symbol file from a slightly **earlier** build. Function and variable names are right, but addresses drift (`main` matches; `msg()` is 0xBCC lower in the real exe). `src/tools/sym.py` parses it into `src/data/sym.txt`; `src/tools/mdis.py` uses the names.
- Files are written back sector by sector with fresh EDC/ECC (`src/tools/cdsector.py`); every replaced file keeps its size and LBA.

## Text
- Strings are u16 glyph numbers ending in FFFF. Glyph g draws from texture page (g>>8)+0x1B, u = (g&15)*16, v = g&0xF0.
- Japanese table (`src/tools/table.py`): 0-31 symbols (0 = full-width space, 8 px), 32-111 hiragana, 112-190 katakana, 191 磯?, 192 アミ, 193 ルア, 194 ー, 195 cm, 196-975 kanji in Shift-JIS order (OCR + dynamic programming + hand check), 976-1067 extra kanji and kana pairs (hand read). 1068 and up are speech-bubble sprites, not text.
- Glyphs below 0x16 (space, punctuation, digits, brackets) advance 8 px, all others 16.
- Printer `msg()` at 0x80018AB8 (a0 window, a1 x, a2 y, a3 string). Control words go through the jump table at 0x800101D0 (index w - 0xFFF4):
  - FFFE newline, FFFD page (waits for a button), FFF9 wait
  - FFFA insert: five pointer slots at 0x80102F10, F54, F58, F60, F64
  - FFFB / FFFC number (FFFC is followed by a width word). Number slots at 0x80102FFC, 3068, 306C, 3070...
  - FFF7 n: player name n (0 = current player), FFF8 n: sound, FFF6 / FFF4 / FFF5: colour
- Standard message box: 0x800197C0(str, a1, a2, a3), box x=8 w=240, text at x=14. English lines are laid out to 224 px.
- Glyph drawer 0x80019328 (a0 window, a1 x, a2 y, a3 glyph, [sp+0x10] attribute). Window 0 is a ring of 0x8C sprites (index byte 0x80102FD8, array 0x801049B0, 36 bytes each; only entries below the index are drawn). Window N uses an array at 0x8011A6E8 + (N-1)*0x630 with a count byte at 0x80182C77+N.
- **Sprite x is stored in 8 bits**, so anything drawn past x=256 wraps to the left edge. This caused the rankings board bug (see below).
- The script lives in the exe's text pool 0x800CE000-0x800E5000. `src/tools/refs.py` finds every reference (lui/addiu pairs and data words); `src/tools/dump.py` writes `out/script_jp.json`. Eleven strings have no reference at all and are treated as dead text.

## The English text engine (`src/tools/engine.py`, `src/tools/insert.py`)
- Glyphs 196-1067 (872 slots in COMM pages 1-4) are overwritten with English "cells": 16x16 tiles holding 1-4 letters rendered from DejaVu Sans Bold 11 as a variable-width font. Cell 0 is a space (no sprite, 4 px). The cells are picked per build from the script (most frequent letter runs first).
- `draw_word()` replaces `msg()`'s three glyph sites. Word meanings:
  - below 196: original glyph
  - 196+k: cell k
  - 0x1Ecc: tab to line start + cc px
  - 0x1Fcc: one ASCII letter
  - 0x2020-0x7E7E: an ASCII letter pair (low byte first)
  - 0x8000+k: dictionary entry k (a list of cells), so common words cost one u16
- Script format (`text/en_*.txt`, `id|text`): `{E}` newline, `{D}` page, `{>n}` tab, `{#hhhh}` raw word, `{A}` `{B}` `{C:n}` inserts, `{7:n}` name, `‹SINK|ER›` a tiny two-row 3x5-pixel label cell (gear window). The full list is in `src/tools/textfmt.py`.
- Layout (`insert.layout`): messages (anything with a speaker or several pages) are re-wrapped to 224 px, two lines per page. Menus and labels keep the Japanese line count and widths; tab stops copy the Japanese columns (the JP space glyph is 8 px, so a JP column is 8 px per space). Inserts are measured at their widest value: fish name 96 px, creature 105, item 121; player names 56.
- Every string is relocated: the inserter rebuilds the text pool, puts the engine code and dictionary table in the freed space, and rewrites every reference.

## Code patches (all in `engine()` in `src/tools/engine.py`)
1. Main text loop 0x800192B4: calls draw_word.
2. FFFA insert loop 0x80018E30.
3. FFF7 name loop 0x80018FEC (x advance in 0x80019034's delay slot removed).
4. Name entry, add key 0x8007E3EC: pairs two letters into one word (4 words = 8 letters).
5. Name entry, back key 0x8007E4F4: splits a pair before removing a word.
6. Name entry cursor 0x8007D254: x = drawn width of the name + 12.
7. Fishing Note fish page 0x80087374: title centred on x=128 by its drawn width. It loads the `{A}` template (string 3), so insert.py adds this site as a reference.
8. Shop menu box (Rod/Float/...) 0x8003E0A4 / 0x8003E0AC: 8 px wider.
9. Message board pencil x 0x8008A1E8 = drawn width of the current line + 16.
10. Message board word add 0x80089840 and backspace 0x80089174 pass the measured width to the pencil animators 0x8008A264 / 0x8008A498; line-up rescan 0x80089124 (board_fix); full-line test 0x8008941C (width < 216 and fewer than 27 words); row-2 keys 0x80089630 type `, . " :` (board_p), with the dakuten handlers skipped at 0x80088DD4 / 0x80088F00.
11. Rankings board 0x8008B764: columns moved (0x8008B310 / 570 / 380 / 5E0), and the place column swaps in "Treasure Isl." (string 76 without its tab, pointer at 0x80010510) for "Treasure Island" (place_ptr at 0x8008B36C / 0x8008B5CC), because the long name crossed x=256 and wrapped.
12. Fish shop / keep net sell list: string 424 (size and price) drawn at x=0x8C instead of 0x9C at 0x80097818 / 998 / B18 / C98.

Gotchas from writing these: Keystone turns `jal label` inside position-independent source into a `$gp` load, so internal calls use `bgezal $zero, label`. Never put a jump in a branch delay slot.

Message board variables: line index 0x8014E021, word count 0x8014DFE9, cursor column/row 0x8014DFE8 / 0x8014E020, page 0x8015A028, buffer 0x80103BC0 (58 bytes per line), width counter 0x80102E6C (a line breaks at 0xD8). Key tables at 0x800CF260 / 2C8 / 330 + ((row-1)*10+col-1)*2.

## Fishing Note map labels (`src/tools/labels.py`)
- Each caught fish's name on an area map is cut from a pre-rendered atlas in COMM.TIM image 0 (4bpp, originally rows 48-151 of katakana). The (u, v, w) bytes at fish_table + i*52 + 48 (fish table 0x800E4CF8, 97 entries of 52 bytes) say where.
- The English labels are drawn in a tiny 8 px mixed-case pixel font and packed into the old atlas rows plus clear gaps elsewhere on the page.
- **The name of entry i is the string its word 7 points at, not string 740+i.** Entry 32 points at an empty string and later entries skip ids, so counting from 740 put 65 of 97 labels on the wrong fish (fixed in 1.0). Ten entries have an empty Japanese name and get no label.

## Graphics replaced (`src/tools/gfx_build.py`, `credits.py`, `letters.py`)
| File | What | How |
|---|---|---|
| `TIM/TITLE.TIM` image 1 | title logo band (rows 64-207) and copyright line | `src/gfx/title_logo.png` pasted in and matched to the page palette |
| `TIM/NAMEBG.TIM` | OK button on name entry | inpainted, brush lettering |
| `TIM/NOTE.TIM` | "Fishing Note" header | inpainted, per-letter brush lettering |
| `TIM/DENGON.TIM` | "Family Message Board" header | inpainted, chalk-style lettering |
| `TIM/G_OVER.TIM` | "...REVIVING!..." faint banner (second copy turned 180 degrees, as in the original) | hand-pixelled block capitals |
| `TIM/KEIKOKU.TIM` | developer warning screen | English text |
| `ENDING/STAF01-15.TIM` | staff roll and "The End" | same line positions, slanted rounded strokes like the original italic gothic |
| `MAP/BOHATE, ISO, KAIGAN, TAKARA.TIM` | shop plaques | the series icons: fish (fish shop), hook (tackle shop), INN |
| `TIM/COMM.TIM` | English font cells and map label atlas | `build.py` / `labels.py` |

The letters of the redrawn art are built from brush skeletons (`letters.py`), not typed in a system font. The ending movie `END2S.STR` keeps one Japanese shop sign; it was not re-encoded.

## RAM variables found
- Player record 0x80174204 + p*0xE46: [1] x tile, [2] y tile, [5] facing; HP halfword at +6 (0x8017420A); Yen halfword at 0x80174210; name words at 0x80174212 (letter pairs, FFFF-terminated, up to 4 words). Current player index byte 0x80102BCF.
- Area byte 0x80102BCE (0 Jetty, 1 home). Main mode byte 0x80103093 drives the dispatcher at 0x800135C4 (table at 0x80010000; entry 99 is the ending).
- Keep net: fish ids at 0x8017435D + slot, lengths at 0x80174386 + slot.
- Rankings: 5 boards of 66 bytes. cm halfwords at 0x80177B1C + t*66 + k*2, names at 0x80177B26 + t*66 + k*10 (5 words), place bytes at 0x80177B58 + t*66 + k. Place-name table at 0x800CD42C (strings 104-113), also used by the file select (0x8007D5D4).
- Fishing Note test data: area byte 0x801743C8+fish (1 = Jetty), x/y halfwords at 0x80174438 / +0xE0, Got 0x801745F8+fish, bites 0x801746D8+fish (must be above 0, the rate divides by it).

## Useful entry points (for testing)
- Shop dispatcher 0x8008F498(a0): 1 inn, 2 tackle shop, 5 fish shop, 6 save, 8 boatman.
- Rankings board 0x8008B764, staff roll 0x800A5844, faint banner 0x80013A84, faint routine 0x80066DCC.
- NPC dispatcher tail at 0x8009F4F0 calls the rankings when the NPC id is 0x11. Writing 0 to 0x8009F4F8 and `jal <fn>` to 0x8009F500 (with `addiu $a0, $zero, n` in the delay slot at 0x8009F504) makes the Jetty cat (tile 10, 9; stand at 11, 9) run any of the above after its line. That is how the shops, rankings, staff roll and faint banner were checked in the emulator.

## Methods that worked
- Kanji font: OCR every 16x16 glyph against IPA Gothic, then a dynamic-programming pass that uses Shift-JIS order, then hand checks (`font_ocr.py`, `font_dp.py`).
- References: scan for lui/addiu pairs and data words that land on string starts (`refs.py`); strings with none are dead text (checked again by hand for the 11 that didn't fit).
- Layout: a static overflow check over every `msg()` call with a constant x and the window boxes opened in the same function (`fitcheck.py`), plus `warns.py` and `tabs.py`.
- In-game checks: a headless Beetle PSX driver (`emu.py`), fresh boot states made from the current build (old save states keep stale glyph numbers and show garbled text after a rebuild), and `strview.py`, which overwrites one NPC line in RAM with any string id so a message can be seen in a real box with the longest inserts.
