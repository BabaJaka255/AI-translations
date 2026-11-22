# Tsuri Tarou (SFC, 1994, Pack-In-Video): engine notes

Addresses are SNES `bank:addr` (LoROM, SlowROM banks $00-$1F) unless marked **ROM** (file offset, no header).
`ROM = (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)`

## Cartridge
| | |
|---|---|
| ROM | 8 Mbit LoROM, 1,048,576 bytes, no copier header, CRC32 `BBBFF8D8` |
| Header | title `ﾂﾘﾀﾛｳ` (half-width kana), map $20, SRAM 2 KB, licensee $99 |
| Vectors | reset `$00:804E`, NMI `$00:8591`, IRQ `$00:860D` |
| Free space | none: no 0x00/0xFF run of 2 KB or more anywhere. English patch must expand the ROM (16 Mbit, banks $20-$3F) |
| Compression | none found. Fonts, screen tilemaps and label art seen so far are all stored raw |

## Not the Nushi Tsuri engine
Different code base from Kawa no Nushi Tsuri 2 / Umi no Nushi Tsuri. No `CC` line breaks, no `E0-EF xx` kanji,
no 16x16 1bpp font, no LZSS loaders, no `$82` text loops. Only the methods carry over.

## Text, three kinds
1. **F0-terminated strings** (8x8 font codes). So far only the fish guide: 15 fish x 5 lines at `$01:E141-E751`.
   Reader `$01:E099` (JSL `$01:8012`) picks the fish block by `$08D6`; drawn by `$00:BAD9` to VRAM `$41C7`, `$4207`... (5 lines).
2. **Raw screen tilemaps** (32x32 words, stored column-major, written with VMAIN=$81). Story/prologue pages and other
   full screens. Loader around `$00:A01A-A31F` picks a source by screen id `$080C`. Prologue page 1 = ROM `0x40000`.
   Also `0x37800`, `0x87800`, ... Text tiles are `0x100 + code`, dakuten/handakuten sit on the row above.
3. **Pre-rendered label art** (2bpp, 8x16 halves of 16x16 glyphs) at ROM `0x3A000-0x3AFFF`: menu headers
   (名前を入れて下さい, 日付を入れて下さい, はじめる, データを消す, 名前 / 釣りの力 / 歩く力 ...).

## 8x8 encoding (`data/tt_8x8.tbl`)
Code = tile index in the font at ROM `0xAE000` (4bpp, also loaded into VRAM tiles $100-$1FF).
Gojuon grid: low nibble = consonant column, high nibble = vowel row (あ=10 い=20 う=30 え=40 お=50, か=11 ...).
`1A` = dakuten, `2A` = handakuten, both placed **before** the kana and drawn one row up. `FF` = space, `F0` = end of line.
A second copy of the font at ROM `0x1B000` (story font) has different glyphs in $60-$7F: 「 」 、 山 日 女 目 大 PASWORD 三 人 川 六.

## Screens and how to reach them in the emulator (`tools/emu.py`, stable-retro snes9x)
* Boot: waterfall attract scene. It waits until three dragonflies are caught (`$09B2/$09B4/$09B6` = 2). Poke all three to 2
  (and `$08BE`=0) to get the title (`states/intro_waterfall.bin` -> poke -> title -> file select).
* File select (`states/fileselect.bin`), A = new game -> name entry. Cursor index `$0AA6` (low nibble col, high nibble row);
  `$96` = おわり. Then date entry: cursor `$0AA6`, `$0A` = おわり, day must not be 00 (`states/date_done.bin`).
* Prologue story (raw tilemap pages, revealed column by column by `$00:A783` / NMI `$00:E256`).
* Overworld map (`states/after_prologue.bin`), HUD つりの力 / 歩く力.

## Tools
* `tools/emu.py` headless driver; `tools/s9xstate.py` reads/patches RAM/VRAM in savestates (block header is `XXX:NNNNNN:`).
* `tools/trace.py` runs the CPU from a savestate in `cpu65816.py` (from the River King toolkit, with RTI added),
  fakes NMI/APU/`$4212`, and lists ROM data reads by PC. This is how the prologue tilemap source was found.
* `tools/dis65.py` disassembler (renamed from `dis.py` so it doesn't shadow Python's `dis`).
* `tools/chart.py`, `tools/tiles.py` render fonts and tiles; `tools/ttlib.py` decodes 8x8 text.

## Step 1 survey results (text inventory)
* Main loop mode `$0872`: 0 attract/title, 3 overworld map, 4 fishing. On the map, A enters a spot when `$0A94`=1;
  `$00:A3D8` switches to mode 4 and draws the spot sign (fish header + 5 lines from `$01:E141`, spot id `$08D6`).
  Shortcut: `states/map_spot1_poked.bin` (map with `$0A94`=1, `$08D6`=1), then press A.
* Map: UP/DOWN walk along paths and use 歩く力; SELECT opens the fish list. Fishing shows no text, only the HUD.
* Story pages (story font, `data/tt_story.tbl`): 0x40000 opening, 0x0A0800 next morning, 0x37800 / 0x87800 came home
  without the Nushi, 0x40800 ending.
* Menu screens are raw tilemaps (name entry = ROM 0xA0000, screen id $0E) over a 16 px glyph sheet
  (ROM 0x36800-0x377FF, 0x3A000-0x3BFFF, 2bpp, loaded by `$01:BAD6` and `$00:DBCF`).
* `tools/dump_text.py` writes `out/script_dump.txt` with all text found so far.
* `tools/vram_src.py` maps a savestate's VRAM tiles back to ROM; `tools/render_map.py` renders a story tilemap.

## Step 2: script file
- `tools/build_script.py ROM out` writes `out/script.json` and `out/script.xlsx` (183 entries: 75 spot sign lines, 30 story rows, 29 menu labels, 45 fish names, 3 sprite texts, logo).
- Spot sign lines draw at col 7 (bullet col 5) and the board ends near col 28, so the limit is 22 cols x 5 lines. Screenshot: `screens/spot_sign.png`.
- Story rows use even rows 2-12 only because kana marks take the odd rows; English can use every row.
- SELECT fish list (0x3D800) names are BG tiles 0x180+code with the same codes as the sprite kana sheet; rows 3..24 step 3, left col 4, right col 19.
- Fish header sets: sign set 0x3E9F4 (15 entries), second set 0x3EBD4 (15 entries, x/y 0x18). Entry 15 tiles C8-CE are not in the kana sheet.
- Backup-error sprite text uses a sprite font that differs from tt_8x8.tbl in places (AF=ン, F4=じ), so it is transcribed by hand.
- Decode slips fixed in the script: ロ->口 (spot 13), ジ->じ (spot 15).

## Step 3: 16 Mbit expansion
- `tools/expand.py IN OUT` pads to 2 MB with 0xFF, sets the size byte $7FD7 to 0x0B and fixes the checksum ($7FDC/$7FDE). Free space: ROM 0x100000-0x1FFFFF (banks $20-$3F, or $A0-$BF for FastROM mirrors).
- Verified: the expanded ROM gives frame-identical output to the original over boot/title, file select, prologue/map/SELECT list and a spot sign + fishing (about 5,000 frames hashed). Interpreter traces from 5 savestates (1.5M instructions each) show no reads from banks $20-$3F, so the game does not rely on 8 Mbit mirroring.
- The ROM itself stays out of the project folder; rebuild with expand.py.

## Step 4: English 8x8 font
- Glyphs live in `data/en_font.txt` (editable # / . art). `tools/build_font.py IN OUT` writes them into the main font 0xAE000 and the story font 0x1B000 and regenerates `data/en.tbl`.
- Codes: A-P 0A-19, Q-Z 1B-24, a-e 25-29, f-z 2B-3F, punctuation 40-4F (. , ! ? ' " - : ( ) / & % ~ ; *). Digits 00-09 stay, space FF, line end F0. 1A/2A are skipped because the sign renderer ($00:BAD9) treats them as dakuten prefixes.
- Story font: digits copied to 01-09; code 00 stays blank (story maps use tile 0x100 as space), so write "0" as O there or remap later.
- Glyphs keep row 7 empty (descenders are raised) so lines can be single-spaced on story pages without touching.
- Tested in the emulator (`tools/font_test.py`, run from the scratch dir): spot sign 1 and the opening story page. Screens: `screens/en_font_sign_test.png`, `screens/en_font_story_test.png`. The sign board fits about 23 columns from col 7.
- Story pages fit 11 single-spaced lines of 30 columns above the picture (rows 2-12); the opening text came out at about 300 characters.

## Step 5: spot signs in English
- `text/signs_en.txt` holds the English (15 spots x 5 lines). `tools/insert_signs.py` encodes it into ROM 0x100000 ($20:8000) and repoints the 15 `LDA $01:xxxx,X` operands at $01:E0E8+6n. `tools/build.py ORIGINAL OUT` now runs expand + font + signs.
- The sign text sits on its own BG layer (VRAM map $4000, blank tile FF), so a line wraps onto the next row by padding to 32 tiles. Each of the 5 lines may take 2 rows of 21 columns (cols 7-27), so rows 14-23 are used. The bullets are board-layer tiles (font slots CA/DA/EA/FA) at rows 14,16,18,20; line 5 has no bullet.
- Checked all 15 signs in the emulator (`tools/signs_test.py` pokes $08D6 into a copy of map_spot1_poked.bin). Screens: `screens/signs_en_1-8.png`, `screens/signs_en_9-15.png`.
- Fish name headers above the signs are still katakana sprites (step 7).

## Step 6: story pages in English
- `text/story_en.txt` holds the 5 pages (paragraphs). `tools/insert_story.py` rewrites the text tiles of each tilemap in place: rows 2-12, cols 1-30, single-spaced, keeping paragraph gaps when there is room. Run by `tools/build.py`.
- Story maps use char base 0 (tile 0x100+code); text attribute is read from each page's existing text tiles. No "0" digit in the story font.
- Opening page checked live in the emulator (typing effect works on English). Pages 2-5 checked by rendering their tilemaps with the in-game VRAM (`render_vram_map.py tten.sfc st1_state.bin MAP 0 4 OUT 1`); a live check comes with the step 8 playthrough.

## Step 7: menus, keyboard, fish names, HUD
All in `tools/insert_menus.py`, called by `tools/build.py`.
- Name entry: codes come from the table at $00:D67F (ROM 0x567F, 16 per cursor row); names are sprites using the main
  font (OBJ tile = code), so English codes just work. Keyboard art is the 0xA0000 tilemap (cells at row 6+2r / 17+2(r-5),
  col 7+2c). Layout A-Z, a-z, digits, punctuation; cursor shape unchanged (9,9,9,9,9,7,6,6,6,6). "End" replaces おわり on
  name and date screens. Max name length is 6.
- 16 px labels: an 8x16 font built from the 8x8 font (rows doubled, strokes widened, proper descenders), placed as
  top/bottom tile pairs in freed tiles of the glyph sheet 0x3A000. LABELS table covers name/date titles, file select,
  records, erase confirm, and the SELECT fish list names (which used the katakana sheet at VRAM 0x180+).
  年/月 -> "/", 日 and 匹 blanked (records and date screens).
- Title: はじめる (title map 0x80800 rows 21-22, title tiles at ROM 0x10000, palette 1) redrawn as "START".
- Sign fish names: drawn on the sign text layer in 8x16 letters made from spare main-font codes (FREE_CODES); the sign
  line table at $00:BB6C word 0 moved to row 7 col 0, and each spot's line 1 starts with the name + padding.
- Records screen (fish list -> A) loads its map with the fish list, before the fish is picked, so $00:BC0E now starts
  with PHP; JSL $20:FF00; NOP. The hook writes the name (64-byte word lists at $20:F000) to VRAM $4063/$4083 under a
  moment of forced blank and restores $2100 = $0F.
- Katakana header sprite lists (0x3E9F4 sign, 0x3EBD4 records) are parked at y=$F0.
- Bad-save message: sprite list at 0x3E90C (58 slots, tile = code+0x80, attr $31). Force it with the PAR cheat
  7E0AAC01 from power-on (`tools/bkmsg.py ROM OUT.png 500`).
- HUD: sprite sheet 0x36800 tiles 28-2B (つりの力 -> "Fish") and 2C-2E (歩く力 -> "Walk"), row below for the outline.
- Savestates carry VRAM from the ROM they were made with; a screen only shows the new build after it reloads. Use
  `tools/poke.py` and fresh boots (title: boot 400 frames, poke 9B2/9B4/9B6=2, 8BE=0).
- Checked live: title, file select, name entry, date entry, fish list, records header, all 15 signs, map HUD,
  bad-save message. Erase-confirm box checked by rendering its map with the game's VRAM only.

## Step 8: patch and handoff
- Story page logic ($00:A611): $0A72==0 -> opening (id 9); $09EC==4 -> next morning (id $0D); $09EC==3 -> day ended
  without the Nushi (id $0C); otherwise $04D0+$0050 == 0 -> came home (id $0B), else ending (id 9 with $089E=1, map
  offset $800). Force any page from date_done.bin with tools/poke.py (A72=1, 9EC=..., 4D0=...), then DOWN, A.
  All five pages checked live: screens/story_en_opening.png, screens/story_en_live_2-5.png.
- `tools/make_ips.py ORIGINAL BUILD OUT.ips` writes the IPS (RLE records for the 0xFF expansion, EOF + size) and
  re-applies it to check it reproduces the build. v0.9: release/Tsuri Tarou (English) v0.9.ips, original CRC32
  BBBFF8D8 -> D5678007 (2 MB). release/TESTING.md is the checklist for the tester.

## v0.9.1: River King glossary (2026-10-27)
- Names follow glossary/series_glossary.md (master: glossary/RiverKing_Glossary_v1.3.xlsx): River King, Masu Trout,
  White Crucian (W.Crucian in the fish list right column, 11 letters), paste bait, Taro, records column "Got".
- release/Tsuri Tarou (English) v0.9.1.ips, patched CRC32 7CF11509. v0.9 is in release/old/.
- Checked live: signs 2/4/15, SELECT fish list, records header. Story pages checked with insert_story.py layout.
