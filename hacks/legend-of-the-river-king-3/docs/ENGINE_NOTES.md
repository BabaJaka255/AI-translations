# Kawa no Nushi Tsuri 5 (GBA) — hacking notes

ROM: AN5J / KAWANUSI5, 4 MB, SHA-1 418d61ddd992ceeaa10a102deaf9eb15a2fb7328. Build: `python3 tools/build_patch.py ORIG OUT`;
release: `python3 tools/make_release.py ORIG VERSION` (writes release/*.ips, *.xdelta, prints hashes).

## Script
- 284 compressed blocks (custom Huffman+LZ, header byte 0x70, size = word>>8). Table pointer literal at 0x0803EBE0 → 0x08150CFC.
- Loader 0x0803EBC4 calls decompress `bl 0x08040D20` at 0x0803EC04 (r0 src, r1 dst); the same routine unpacks graphics.
- Patch: ROM padded to 8 MB, scripts stored uncompressed from 0x08400000 with header byte 0x00; hook at 0x083F6000 copies
  those and tail-calls the decompressor for the rest.
- Format: "[SCRIPT]" + u32 size + ops [op][len][u16]…; text ops 0x16 (dialogue), 0x1b (choice) carry u32 len + SJIS text.
  Jump fields to relocate (value+12 = file pos): ops 0x0a–0x0f at +20, 0x12/0x13 at +4.
- Codes: 01 newline, 02 page, 03 player name, 04 number/fish, 05 m, 06 cm, 07 money, 09 pause, 0A/0B values,
  0F…0E blue (names), 10…0E highlight. Box 36 half-width columns × 3 lines; ASCII is 6 px.
- English in text/script_en_*.txt ("NNNN<TAB>text": | page, / newline, leading = literal); tools/wrap_script.py wraps
  into out/script.json (VAR_W gives assumed widths of the variables).

## Player name
- Name buffer = [0x03000400] (0x0200E068) + 0x5C, 10 bytes SJIS + 0. Code 03 handler 0x08012B98 calls identity 0x0800D810.
- Hook at 0x083F6100 (BL at 0x08012BB6) copies the name to 0x0203FFC0, converting full-width A–Z/0–9 to ASCII, first letter
  capital, rest lower, dropping full-width spaces. Default name pointer literal 0x0800D800 → "ＫＥＩＴＡ" at 0x083F6200.

## UI strings
- tools/ui_strings.py → out/ui_jp.json (808 pointer-referenced candidates; many false positives). English in text/ui_en.txt
  ("index<TAB>text", or "@hexaddr<TAB>text" to scan for pointers); the build writes copies after the scripts and repoints.
- Strings are concatenated in code into 0x80-byte buffers, usually "<name>" + "は" + newline + "rest", so English pieces
  are written as "<name>" / " " / "swam off happily!" etc.
- Status labels are 4 half-width columns (Pow, Skl). Menu title box is 11 columns (Fish Note). Fishing Note / item
  description lines are separate strings, ≤ 34 columns each.
- ﾚﾍﾞﾙ (Lv) lives at 0x1019F8 and 0x1029F0 (half-width kana, missed by the dump).

## Name entry
- Grid: u16 little-endian SJIS cells at 0xFB718 (kana page, 12 per row; columns 10–11 are the side buttons), alphabet and
  symbol pages follow. The button handler compared the cell under the cursor with 英 記 戻 進 終 (binary search at
  0x0800688C); replaced by a jump to a compare chain at 0x083F6300. New labels: ａｂ ★♪ ≪ ≫ ｏｋ (first chars must not be
  typeable on any page).

## RAM (EWRAM offsets, player object 0x0200E068)
- 0xE0C4 name; 0xE0D3 HP, 0xE0D4 max HP, 0xE0D5 Skill, 0xE0D6 Power, 0xE0D7 Lv.
- Inventory std::vectors (begin/end/cap) at 0xE128 food, 0xE134 items, 0xE140 bait/lure, 0xE14C tackle, 0xE158 ?,
  0xE164 creel; 8-byte elements, u16 id + u16 count + 4. Handy for testing menus.
- Controls: SELECT opens the menu, A examines, B casts.

## Not done yet
- Title logo (graphic). Fishing Note screen and shops not yet seen in game. Credits roll not seen.

## Title screen (v0.9.1, tools/logo.py)
- Title sprites: tiles = compressed 32 KB block 0x08365D40 (refs 0x56C4, 0x3DD5C) → OBJ VRAM, 2D mapping; frames bank
  0x08368D18 (refs 0x56DC, 0x3DD74) addressed by u16 offset tables 0x15153C (8 frames) and 0x15154C (8 anim records);
  OBJ palette raw at 0x08369098 (logo uses entries 32-127, Keita 128-207).
- Frames: 0 logo words (fade/slide), 1 the number (64x64 affine, tile 768; spin starts with a zero matrix, so its centre
  texel must be transparent), 2 finished logo + subtitle, 3 Keita, 4 copyright, 5 PUSH START, 6 はじめから (tiles 79-87),
  7 つづきから (tiles 88-95), 4bpp, colours 9-c fill, f outline, 1-4 rim.
- The build stores the tile block raw (header byte 0x00); 0x08040D20 now jumps to a hook that copies raw blocks for
  every caller. New logo from art/river_king_3_*.png (the tester), subtitle drawn with the dialogue font (art/font_sample.png).
- Dialogue font: 0x0832F538, 20 bytes/glyph (10 rows u16, bit 8 = left pixel); no 'O' glyph, so 'P'+ are one slot
  lower. 'm' widened to 5 px.

## Graphics with baked-in Japanese (v0.9.2)
- 装備 tag: raw 4bpp sprite tiles at 0x36FC5C (32x32 item frame, 1D mapping, OBJ pal 10). tools/tags.py redraws
  the box (colour a) with EQUIP in colour b. Patched in place.
- Fishing Note maps: pointer tables 0x14AB8C tiles (0x5000), 0x14ABA8 tilemaps (0x800), 0x14ABC4 palettes (13x16),
  7 entries each, entry 0 = entry 1. Map order: Nushikiri Village, Oven Kingdom, Cold Park, Coconut Village,
  Fairy Town, Mysterious Forest. Every tile is unique with a per-tile palette, so tools/maplabels.py renders to RGB,
  pastes a scroll built from the Oven Kingdom scroll (left/right rolls + 4-px body strip) sized for the English name,
  then picks the best palette per touched tile. Tiles and tilemaps are stored raw (header 0x00) and repointed.
- The dialogue font has no 'O' glyph: render 'O' with the '0' glyph.
- Testing: the tester's .sav (EEPROM; reverse every 8-byte block for mGBA libretro). Tackle tab = menu RIGHT x3, A.
