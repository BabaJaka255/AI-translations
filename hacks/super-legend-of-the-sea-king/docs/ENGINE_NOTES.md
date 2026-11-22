# Umi no Nushi Tsuri: differences from Kawa no Nushi Tsuri 2

Read the River King `ENGINE_NOTES.md` first; this lists only what is different. FastROM banks ($80+).

| | Umi |
|---|---|
| ROM | 16 Mbit LoROM, header map $30, CRC32 C985F568. Patch expands to 32 Mbit (size byte 0x7FD7 = $0C); new data in banks $C0+ |
| LZSS | decoder $80:92C6; loaders `JSL $80:85D0` (VRAM) / `JSL $80:85CC` (WRAM, bank in $44). Same format, `lzss.py` works |
| Data bank | $86. Header at $86:8000 (12 table pointers); $86:8016 -> script table |
| Script | 710 pointers at $86:9B25, text $86:A0B2-$86:E677. 67 of the targets are small binary records stored between strings (`umilib.data_ids`) |
| Encoding | same as Kawa 2. Codes CD-DB used (DB = place/point name); DC-DF unused |
| Fonts | single-byte font $87:8000 (glyph b-1); kanji $88:8000 (954 glyphs, Kawa 2 order up to $2B3) |
| Text loops | A $82:843B (also all insert codes), B $82:8956 (typewriter dialogue), C $82:B19E (wrapping windows, width $1E, line start $1C) |
| String pointer | `[$12]`, bank $14. Column $18 (4 units per 16 px; 8 px glyphs subtract 2) |
| Glyph blitter | `JSR $82:875F` with glyph address in $0E/$10; column table $82:882B; staging 7F:F000 |
| Dialogue window | 2 lines x 24 half-width columns; line 2 starts at column $30; CC on line 2 scrolls. The page-end arrow covers column 23, so English lines stop at 22 |
| Free space | $82:EB76-FFFF (patch code at $82:EC00), $B4:9D45 (58 KB), others ~1-13 KB |

## English engine (build_patch.py)
* `DF` sets bit $0100 of $14 (byte $15) = English mode; bytes $20-$7E are ASCII from the 8x16 font at $C0:A000.
* Entry hooks clear $15 after `xl`, so only a `DF` string is English, except bank words $0100 and $0170,
  which callers use to ask for English (player names in WRAM $00:1452 and the save slots $70:xx1C).
* `xl` handles strings in banks $86 and $87: index $C0:8000 ($86) and $C0:8100 ($87), 128 words each, pointing
  into the table at $C0:8200 (old ptr, new ptr, new bank; each bank's run ends with FFFF). Strings from $C1:8000.
* Hooks: A `843B`/`8447`, B `8956`/`8962`, C `B1A1`/`B1AD` (C also runs the wrap check `JSR $B213`).
* Player names are plain ASCII without `DF`, up to 8 letters ($1452-$1459; 4 kanji in Japanese).

## Script
* `build/translations.py` merges `tr_system.py` (189-461), `tr_story.py` (469-586), `tr_town.py` (587-709),
  `tr_notes.py` (news, fishing tips, letters; also the held character names) and an optional `user_edits.py`.
* Limits (`translations.limits`): dialogue 22 columns; fishing tips/news 3 x 32; letters keep the Japanese size.
* `build/reflow.py 22 [ids]` re-wraps too-long dialogue lines in place.
* `tr_misc.py`: file select, place names, tournament titles, region captions, NPC names.
* `tr_names.py`: names in the bank $86 data tables (by pointer) and the fish records (by record number).
* Still held: packed labels 9, 13, 22, 78, 79 (screens not found yet), postcard keyboards 75-77,
  insert-only strings 462-468.

## Data tables and records
| What | Where |
|---|---|
| Bait / hooks / lures / rods / food / items / floats+sinkers / creatures | name strings in bank $86, e.g. $86:8392 bait, $86:86CE hooks, $86:88C2 lures, $86:8ACE rods, $86:8C61 food, $86:8D4B items, $86:8F3E floats, $86:9A71 creatures. Inserts CE/CF/D1/D2/D3/D5/D6/D9 point at them |
| Fish | 113 records of $21 bytes from $87:C200. Pointers at +$19 name, +$1B alias, +$1D description, +$1F cooking (copied to $1D08-$1D0E; D8 = $1D08, bank $87) |
| Fish page | `$81:BC00`: name centred from a byte-length table at $81:BE23 (start = 16 - 2*len, 4px units; `fishdata.center_code` hooks $81:BC0C to use 16 - letters for English); description via loop C from column $0E, width $3C, next lines from $02, 4 lines (0x1000 staging). English: 22 letters on line 1, then 28 |

## Graphics and screens
| What | Where | Done in |
|---|---|---|
| Menu label art | ROM 0x48000-0x4BBFF, 12-tile rows to 0x4A3FF, then 16-tile rows; bg 1 / ink 3 | `labels.py` |
| Window UI font | LZSS $90:9A71 (1 loader) and $89:BBFF (7 loaders); tile t top, t+$10 bottom. Digits 2-B, 円 C, cm D-E, 尾 F, 体力 48, お金 4C, 魚種 6C, 合計 8C, はい CA-CD, いいえ CC CD CC CD CE CF | `labels.py` (moved to $B5:8000/$B5:8500) |
| Yes/No window template | $82:C70F | `labels.py` |
| Fishing Note contents | tilemap LZSS $90:C057 (ROM 0xB7F5); string 14 drawn into tiles $140- (3 staging lines only) | `content_page.py` |
| Character select | tilemap LZSS $90:AC59 (ROM 0x909F, 2 screens); string 3 drawn in pieces from offsets 0, 8, 12, 14 | `cs_panel.py` |
| Name entry | grid row $7F09BA / column $7F09B8; kana `81:9D72`, kanji `81:9DB8`; length check `81:9BF7`; names drawn at `81:983A`, `81:9E0E` | `name_entry.py` |
| Default names | copied at `81:A134` from strings 4-7 | `name_entry.py` (ASCII table at $C0:F000) |
| Letters | `81:DDBE` copies string 505/579/63/66/69/609 to $00:111A | `name_entry.py` (`lcp`) |

## Not done yet
The board keyboard's 、。 keys (UI font $89:BBFF tiles $2A/$3A) are drawn as a comma and a full stop, and the
disabled ゛゜ keys (tiles $21/$31) are blank. There is no postcard feature in this game.

## Cup ranking board (`rank_board.py`)
Drawn at $81:D380 (jump-table entry $81:8010; event step $097C = $0A at $85:B207). Cup title = strings 23-29 by
place ($1442) into tiles $140-, header string 22 into tiles $160- (16 columns, one per letter). The tilemaps
(LZSS $90:C45F cm boards, $90:C6B0 count boards with unit tile $0F; pointers at $81:D976) reused the header's 位
($162/$163) after each rank digit; they are re-tiled so the header reads Rank / Name / Record and each digit gets
a full stop. Rival names (strings 30-61) are copied into 8-letter slots, so the build rejects longer ones.

## Letter envelopes (`letters.py`)
$81:DB07, five letters. Sender address / name strings by letter from tables $81:DD5B / $81:DD6F (16 and 8
columns), the addressee's address is string 62 (16 columns) and the name comes from the save slot ($70:001C +
$500 per member, bank word patched to $0170 in `name_entry.py`). The stamp, postmark, 〒 and 様 are label-sheet
row 0x4BA00 (VRAM $2100/$2180); 〒 and 様 (tiles 8-11) are blanked.

## Fish market special (`market.py`)
$82:A66A draws the daily special's name (fish $7F:0C3A - 1, record +$19) into 12 columns, price at a fixed column
after it. Names over 12 letters swap to a short form from the table at $C0:F600 (helper hooked at $82:A66D).
The first entries of the bait ($86:838A) and creature ($86:9A6C) tables are not preceded by a 00 byte, so scans
that split the data on 00 miss them.

## Testing screens you can't reach quickly
Copy the ROM and point a bank $81 jump-table entry that the Fishing Note uses ($81:800C, `JSR $A9DF`) at the
screen's routine, then open the Fishing Note from the Item menu. `analysis/ramset.py` edits WRAM in a save state to
set the inputs (e.g. $7F:09B4/$7F:09B6 for the envelopes).

## VRAM-direct LZSS sources must stay in banks $80-$BF
The graphics decompressor ($80:92C6, via JSL $80:85D0) sets the data bank to the source bank and writes
VRAM with absolute `STA $2118`. Banks $C0-$FF have no I/O mirror, so a block moved there decompresses into
ROM space and VRAM keeps whatever was there (this broke every window frame, the age digits and the status
labels). Such blocks live in bank $B5 (ROM 0x1A8000, zero padding in the original). Tilemaps loaded through
other routines (contents page, character select at $F2) are fine in high banks.

## Title screen (`title.py`)
Block LZSS $8F:964F (0xC000 bytes, loader ROM 0x8102, VRAM word $2000; OBJ tiles at +$8000), rebuilt at $B5:9000.
Title sprites are metasprites: pointers at $81:852F (10), each a count then 8-byte entries (y, x, tile 9 bits,
attribute, size 0 = 16x16 / 2 = 32x32). Entry 0 is the logo; the new list (42 16x16 sprites) is at $81:FC20.
OBJ palette 0 is at ROM 0x36A38 ($86:EA38); colour 1 must stay white (START and the cursor use it). The START
cursor is tile block $0E, set from code, so it is not in the metasprite lists. The logo art is the tester's
"Super Legend of The Sea King" mock-up (build/data/logo_mockup.png), scaled to 176 px wide and cut to 15 colours.
はじめる = 16x16 sprites A0, C0, E0, E2 at y=104, colour 1. Map captions on the Fishing Note maps are strings
15-21 (3 glyph cells, 6 letters).

## Item icons (`icons.py`)
Icon sheet LZSS $8F:8ACD (0x1C00 bytes, 4bpp, 16 tiles/row, read at $82:8F3F/$82:91F4 through $82:B242, loaded
when the field loads). Icons are 32x16; the records with ステレオ/モノラル are at tiles $4C and $60. Rebuilt at
$BF:C000.

## Fish page (`fishdata.py`)
The name is centred at $81:BC0C. In English the start column ($18, 4px units) is 16 minus the letter count,
and must be even, or loop C draws nothing (this is why the names vanished).

## Family message board (`board.py`)
Input code $81:CD14-D2D8, buffer $111A, palettes strings 75-77 (ASCII at string+6). Every mode is made one
byte per cell, the fixed keys insert ASCII, and the line measure counts one cell per byte (28 per line).
The board view draws its four messages ($7F:09F2 + $60*k) with bank word $017F, so the entry stub keeps the
$0100 bit for $017F as well as $0100 and $0170. Mode button art: label sheet row at ROM 0x4B600, tiles 4/8/12.
String 74 (the board title) is "Family Board".

## Map fish labels (`map_labels.py`)
$81:BBAC copies the name and $81:BBC2 writes byte + $84 as tiles. The 8x8 font LZSS $B1:9700 is rebuilt at
$BF:B780 as a 5x8 font with a dark outline and a transparent background (slots 77 ▸ and 78 ー kept).
ASCII map at $C0:F100, short map names (10 letters max) at $C0:F200.

## Town plaques (`field_signs.py`)
Town tileset LZSS $91:856B (0x7800 bytes), named by area table entries at ROM $1902, $191A, $192A, loaded by
$80:98F0 straight to VRAM $2200. The plaques are 16x16: tiles F5/F6 over 100/101 (宿), F7/F8 over 102/103 (魚),
F9/FA over 104/105 (釣); black interior colour 1, ink F. Redrawn as INN, a fish and a hook, rebuilt at
$B4:9D55 (zero padding).

## Tackle shop item window (`shop.py`)
$83:97F4 copies the item name to $0C04, adds CC DA E0 00 (price + 円) and draws it from bank $00, bypassing the
lookup. A helper looks the name up first and ends an English name with " yen".

## Secret name
$81:98F2 compares the brother's 8-byte name ($1452) with $81:995B (originally ふね太郎). The patch sets it to
`BoatTaro` (as Kawa 2's つり太郎 became FishTaro). Tested: the brother starts with 1000 yen and a stocked
tackle box.

## Board keyboard key label
Strings 79 (改行) and 78 (決定, on the last line) are the Line key's label: "Line" / "Done".

## Fishing paper (`fish_news.py`, strings 98-181)
Bought at the bait counter (Item shelf) for 10 yen. Characters LZSS $B1:995C (shared with 5 other screens; only
the logo's own tiles change), tilemap LZSS $B1:F010. The logo box only owns 39 tiles, so FISH NEWS is two tiles
tall. Headlines (98-101) are 14 letters wide, articles 3 lines of 30.

## Keep net / cooler window (`keepnet.py`)
$82:A469/$82:A4A3 copy fish names ([$0E], bank $87) to $0C04 and draw from bank $00; a helper runs the lookup
first. The name column holds about 19 letters before the size.

## Width rules (build_patch.py `EN_WID`, translations.limits)
Dialogue 22 columns. Paper tips 30x3, paper headlines 14x2 (checked in the emulator), tournament news 32x3.
Inserts count as their longest English name: fish 14 (so fish names are capped at 14), bait 16, hooks 15,
lures 17, rods 17, food 13, items 15, creatures 15, places 10.

## Zone warp, test build only (`warp_test.py`)
Not part of the release patch. Run after build_patch.py: it reads out/umi_en.sfc and writes out/umi_warp_test.sfc
and .ips. Areas ($1442): 1 town jetty, 2 beach (left of 1), 3 hill (right of 1), 4 sea by boat, 5 islet,
6 open sea by boat, 7 far isle, 8 inside buildings. Exits set $1442/$1444/$1446, play $80:951A and $80:9CB0,
then $141A = 1 reloads the area (the loader at $80:B1EE picks walking or boat mode by area). The hook replaces
LDA $141A / BEQ at $80:B234 in the field loop with a JSL to $82:FE00. A new R press goes to the next zone, L to
the previous one, only while $141A = 2 (field running, not in menus or while fishing). Spawn table at $82:FF00.

## v1.1: River King glossary (2026-10-27)
Names in tr_names.py (and the market / map short tables) are Title Case like Super Legend of the River King;
status label お金 = Yen (labels.py), file select New Game / Erase Data (cs_panel.py, tr_misc.py), cooking notes
Arai / Bottarga / Kabayaki. Deliberate differences from River King are in glossary/series_glossary.md.
Release: release/UmiNoNushiTsuri_EN_v1.1.ips, patched CRC32 35B3E1F3 (v1.0 in release/old/).
