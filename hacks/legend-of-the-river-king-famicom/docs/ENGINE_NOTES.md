# ROM notes: Kawa no Nushi Tsuri (FC, 1990, Pack-In-Video / Yuu Yuu)

Source: `rom/original.nes` = "Kawa no Nushi Tsuri (Japan).nes", 262160 bytes, CRC32 4F5C3D34
(headerless F4E5DF0E), NES 2.0 header, mapper 4 (MMC3), PRG 128K (16x8K), CHR 128K.
The 2013 Pikachumanson v0.91 patch was looked at for reference only; nothing of it is used.

## Banks (PRG, 8K)
- 0-5: area map data (R6/$8000 = area number $7B, 1-5). 6 is all FF but IS mapped by $C5E5 when $DB==$1E;
  7 is mapped when $07FC is 1/2. Don't reuse 6/7.
- 8-13: code + text, mapped at $A000 (R7) by the $D109-$D145 helpers (bank 8..13).
- 14/15: fixed at $C000/$E000. Jump table at $C010+ ($C037 = print one line = $F11A).
- Free: bank 15 $FE42-$FFCF (398 bytes, used by asm/text_hook.s).
- $C5E5 re-selects the right $8000 bank (uses $07FC, $DB, $0793, $7B). Reset at $FFD0.

## Text encoding (tile = byte)
Font page = CHR 0x1000-0x17FF (PPU $0000 when R0=4). Table in tools/knt_common.py.
00-09 digits, 0A '*', kana in a gojuon grid 0B-5F, 60-63/70-73 window borders, 64 ?, 65 ボ, 66 。,
67 ー, 68 ワ, 69 c (cm), 6A-7F katakana, 74 じ, 75 ¥, 77 グ. FE space, FF end of line.
1A/2A = dakuten/handakuten PREFIX: printed into the row above (the line buffer has two 18-tile rows).
Katakana ン is drawn with ソ (2E).

## Line printer $F11A
`$12/$13` = pointer. Buffer $0650 (upper/dakuten row, 18) + $0662 (text row, 18) = 36 bytes;
$F480 scrolls $0650 -> $0674 -> $0698 -> $06BC (3 lines in the box). $07BC = columns to reveal;
NMI $E559 reveals one column (both rows) per tick. Control codes: F0 number, F1-F3 password rows,
D0 continue at fixed suffix string ($074A = D1/D2/D3 -> $F4BB "got away"/$F4C5 "caught"/$F4CF "let go"),
C0-C3,C5 numbers, A0 number, B0 raw tile $07D8, B1 enemy name ($F4EE table, offsets $F4D8 by $0756),
B2/B3 numbers.

## Where the pointers are
- Stubs `LDX #hi / LDY #lo / JMP common` (or fall through) per bank; commons: b8 $BE07, b9 $B134,
  b10 $AA57 + $B242, b12 $B0DB, b13 $A573 + $B718. 284 stubs.
- Sequential: intro bank 11 ($B15A, 17 lines, LDA #hi/STA $13 at PRG 0x1710F), ending bank 8 ($BAC8, 16 lines).
- Fish names: bank 10 $A151: base per area ($AF6E/$AFB2/$AFED/$B02F/$B072) + byte offset from $AF33[x];
  each name ends with D0 (so the suffix string follows).
- Window templates (tile maps with borders, dakuten rows included): see tools/knt_windows.py (b9 $13ED3 status,
  b13 bait/items/shop windows, b15 command/fight/yes-no windows).

## English hack (tools/knt_build.py, asm/text_hook.s)
- PRG expanded to 256K: banks 0-13 unchanged, 14-29 new, original 14/15 -> 30/31.
- English line pointer: $13 bit7 clear: bits 6-5 = text bank index (banks 14-17), bits 4-0 = addr bits 12-8
  in the $8000 window. TXT_BEGIN (at $F127) maps it with a verify loop (byte 0 of each text bank = its number);
  TXT_END (at $F1EB) restores via $C5E5 and lays the line out: <=18 tiles go to the lower row, longer lines
  use both rows. So each line = up to 2x18 tiles and the box shows 6 rows.
- RAM used: $078B, $078E, $0795, $0799 (no code references them).
- Two-row reveal: PHASE = $07D5 (free RAM). REVEAL (NMI $E56E) writes the lower row and blanks the upper
  while PHASE is set; REVEALEND ($E5A0) restarts the reveal on the upper row, so row 1 types out, then row 2.
- NEWROW code $1A in an English line pads the upper row at run time (replaces `sta $0C / txa` at $F13C),
  so variable-length B1 creature names (15 wide) don't break the layout.
- Creature names: offset table at text-bank header +$10, names at +$30 (copy in every text bank);
  $F3E0 -> `ldy $8010,x`, $F3E5 -> `lda $8030,y`.
- Fish catch lines: bank 10 $A8F4 -> jsr FISHPTR (asm/fish10.s, $BD65): fish number*3 + ($074A-$D1)
  indexes FLO/FHI, each pointing to a whole English sentence ("The char got away." etc.).
- Menus (tools/knt_windows.py, asm/menu13.s at bank 13 $B985, asm/status9.s at bank 9 $BFAB):
  food/items use a one-column list (LISTSLOT rows), shops put names on odd rows and prices on even rows.
  Cursor: bank 13 $A5ED/$A60B/$A63A call LRCHK/UPCALC/DNCALC; start row from INITY ($E4DC).
  STYLE: list = $0757<>0 or mode $10/$12; shop = mode 2 and $07A4=$0C ($0B = fish buyer, $0D = nobody).
- Graphics: tools/knt_gfx.py (plaques INN/hook/fish in town CHR page tiles 2-7/18-23, TEA banner
  tiles 52 53 62 63 00 01 10 58), tools/knt_logo.py (title logo, packets at file 0x177A1).
- Free space left: bank 13 after the menu code, bank 9 $BFAB area, bank 10 after FHI.
- Title logo source: gfx/title_logo.png (256x96, colours sky/shadow/outline/fill, nearest-colour match). Only cells inside ALLOWED in tools/knt_logo.py may be inked; at most 137 unique 8x8 tiles (98 used by the current logo). `python3 tools/knt_logo.py export out.png` redraws the text version.

## Fishing (bank 8 / bank 10)
- Bank 8 $A734..$A8A0: float drift and bites. A bite starts ($07C6=1) only when the float is on a water
  tile whose class ($078A from $C013) is $40 and $07E2 is set; the fish is $C02E's pick for the spot, and it
  only takes the bait if $A9DF[bait $07C1] equals $AA2D[fish]. Then $07E1=1 / $07C6=2 (float under).
- For testing, a copy of the ROM with bank 8 $A7D6 -> `4C E2 A7` and $A864 -> `4C 8C A8` bites at once.
- The reel window's distance ("4.4m") is drawn with sprites, not window tiles.
- Catch result: $074A = D1 got away / D2 landed / D3 let go, set in bank 10 ($A780, $A7AE, $A8CB, $A8E5).

## Methods that worked
- Text: relative search on kana values, then the $F11A printer and its stubs (`LDX #hi / LDY #lo / JMP`).
- Windows: the templates are plain tile maps; they were found by searching for the border tiles 60 72 .. 62.
- Testing: headless cynes (pip install cynes) with scripted input and save states made from boot; states
  from an older build break when code moves, so they are always regenerated.
- Graphics: screen blocks were matched against CHR pages to find the plaque, banner and logo tiles.
