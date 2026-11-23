# Iso Tsuri: Ritou-hen (SFC): engine notes

Everything found while making the English patch, with addresses. Code addresses are bank $80 unless stated.
The tools named here are in `src/tools/`.

## ROM
- File: `Isozuri - Ritou Hen (Japan).sfc` (No-Intro name)
- 2,097,152 bytes, no copier header, HiROM + FastROM (map $31), SRAM 8 KB. CRC32 `3D35D085`, SHA-1 `49741c14e923bdaa0ff5776744508544921cbb2d`.
- Pack-In-Video, (C) 1995. Vectors: NMI $00:FEFB, RESET $00:FE3F. Main loop waits on $0D94 at $80:825E.
- No free space to speak of (all banks used). Plan: expand to 32 Mbit, new data in banks $E0+.

## Tools
- `cpu.py` + `run.py`: Python 65816 interpreter that runs from a snes9x save state (stable-retro get_state()),
  with NMI injection, DMA, VRAM port, mul/div. SPC handshake at $C2:07BB is faked (copies A to $2140).
  Exec/read/write hooks for tracing. ~5k instructions per frame, fast enough for traces.
- `drive.py`: stable-retro (snes9x) driver. D-pad needs ~10-frame holds to move menu cursors.
- `d65.py` / `lst.py`: 65816 disassembler and bank listing; `s9x_state.py` reads WRAM/VRAM/CGRAM out of a snes9x state;
  `vview.py` tile/VRAM viewer; `islz.py` the game's LZ codec; `extract.py` dumped the Japanese script.

## Text engine (bank $80 code)
- Text is plain Shift-JIS, all in bank $C1 (ROM 0x15EE0-0x17E05, about 8 KB). Reader `$80:9272`: pointer `$049F`;
  if < $2000 it reads WRAM (player names), else bank $C1 (hard-coded `LDA #$C1` at $80:9281).
- Codes: `/` (2F) end, `]` (5D) newline, `^` (5E) record cursor position (menu item, list at $04A9),
  `~` (7E) skip/no-op, `<` (3C) katakana mode, `>` (3E) hiragana mode (+$80 to half-width index, $04A5).
- Bytes 81-9F/E0-EF start a 2-byte SJIS char: looked up in a 376-entry SJIS table at $81:916F (ROM 0x1916F)
  -> 16x16 glyph index. Other single bytes are looked up in a 256-byte table at $81:945F (ROM 0x1945F)
  -> half-width glyph index | $8000; DE/DF after a kana add a dakuten glyph (bit $4000, index in $04A3).
- 16x16 font: LZ block at $C0:0000 (ROM 0x0000, decompressed by `$80:EF1C` to $7E:C000), 32 bytes/glyph,
  1bpp tiles TL,TR,BL,BR, same order as the SJIS table.
- 8x8 half-width font: raw 1bpp at $DF:CC34 (ROM 0x1FCC34), pointer at $81:84C0. Katakana set, +$80 hiragana set.
- Drawing: `$80:92E1` draws one char into a 2bpp line buffer $7F:4600/$7F:4800 (row = $054B, 0x200 bytes per
  tile row; column = $0549, 8 px). Full-width = 2 columns, half-width = 1 column drawn in the lower tile row only.
  `$80:9346`/`9362` half-width path, `$80:9300` full-width path. Colour masks $01/$02 from table $80:9126.
- Entry points: `$80:91A8` set pointer (A) and reset; `$80:9143` draw whole string; `$80:92C9` draw X characters
  (fixed-width fields; X counts characters, not bytes). 15 + 23 call sites, all in bank $80.
- Many strings are fixed-width tables indexed by code (base + i*stride), drawn with `92C9`:
  e.g. $C1:6880 fishing methods (12 bytes), $C1:6A60 (6), $C1:6F50 spot names (18), $C1:7190 islands (8),
  $C1:7204 (8), $C1:5FCC, $C1:6170, $C1:62C4, $C1:72A7 (6).

## Screens seen so far
Title -> menu (出発 / 釣り人の変更, angler list) -> name entry (6 kana) -> intro story (2-line crawl, lines
cut at the right edge in the original) -> sea map (sail the boat; touch an island) -> island map (time HUD,
place label, flags = spots) -> spot map (label) -> A at a flag -> fishing view (method label; X = underwater
view with bait label; B = leave).

## Story crawl ($80:DE20 / DF15 / E109)
- Original: its own glyph drawer `$80:E109` writes 16x16 cells into $7F:4800: a cell is tiles (TL,TR) at +cell*$20
  (+$200 for cells 8-15) and the bottom tile row at +$100; one line = $400 bytes. `$08E1` = cell counter (starts at 2),
  `$08E3` line. Japanese lines longer than 14 cells are simply cut at the screen edge in the original.
- `$DF6F LDX #7` = frames per character (2 while A is held). FFFC / FFFD = scene changes (reload BG and the 16x16 font).

## Records
- Record line built in WRAM $044F by `$80:8B02`: rank, `>` name `<` (until column 8), size via `$9A32`/`$88C9`,
  "cm ", then the spot+island string from `$C1:62E1 + spot*16` (direct long read at $8B67) until column 28 ($8B73).
  `$80:8BA2` appends a byte and counts columns (not for DE DF 7E 3C 3E).
- Records-by-fish menu slot -> fish: `$89E0` (row-major pairs; English uses a lookup table).
- Default record holder name: 12 bytes at `$81:90E1` (copied to $1296 by $8D1A for fresh saves).
- Label boxes on the maps: `$981C` measures the first word (stops at $20), `$9835` counts leading spaces; both read
  bank $C1 directly (`LDA #$C1` at $981D / $9836).
- Menu cursor sprite x = column*8 - 6 at `$9055` (`$904A`, used by every ^ menu).

## Methods that worked
- Text: the Python 65816 interpreter (`cpu.py`/`run.py`) traced the menu code from a snes9x save state, which led to
  the LZ decompressor ($EF1C, font to $7E:C000) and the draw routines. The SJIS lookup table at $81:916F was decoded
  against the font, the strings in $C1 were split on their `/` terminators, and every pointer was found by scanning
  bank $80 for call sites of $91A8/$9143/$92C9 and for immediate operands (`LDA #$xxxx`) equal to a string start.
- Graphics: VRAM/CGRAM dumps from save states (`s9x_state.py`) plus the BG register writes found in the trace.
- Gameplay checks: lockstep runs (`tools/test/lock.py`, `fuzz1.py`) of the Japanese and English ROM from the same save
  state with the same inputs, comparing WRAM snapshots. Only the stack and hook scratch differ.

## English patch layout (tools/build.py, tools/script_en.py)
- ROM expanded to 32 Mbit. $E0 = copy of $C1, text reader bank `$9281` -> $E0; `$981D`/`$9836` -> $E0 too.
- $E1:1000 koi8x16 font, $E1:2000/2100 old 8x8 <-> ASCII maps, $E1:2200 fish menu map, $E1:3000 code,
  $E1:4000/$E1:6000 title BG3 tiles/map (LZ), $E1:8000 bold story font (16 rows x 16 bits per glyph), $E1:9000 its advances.
- Hooks: `$9229` char lookup (ASCII 20-7E -> glyph $100|c), `$9346` half-width draw (8x16; row 0 = HUD uses the old
  8x8 digits), `$E109` story char (proportional: pixel column at $7E:1D00, free RAM; the line's $400 bytes are cleared when
  `$08E1` = 2, i.e. at the first character of a line; frames per char $DF70 7 -> 2, $DF7B 2 -> 1 with A held), `$8B60` record stride 32, `$89E0` fish menu map.
- Strings relocated to $E0:8000+ (pointer operands listed in tools/inventory.py). Fixed tables rewritten in place in
  $E0 except: record spot/island (32-byte stride, 18 cols), catch-screen fish name (16-byte stride, 14 cols at col 9),
  angler place (8 cols). Inner spaces in measured labels are $A0 (draws blank, not a word break for $981C).
- Record line: rank and "cm" dropped, cols 1-29. Icon letters A-M in the half-width table moved to codes 01-0D
  (and in the icon strings at $71C8/$7204).

## Title screen
- Mode 1. BG1/BG2 (4bpp, chars $0000, maps $4000/$4400) = scenery and animated sea; the fisherman is sprites.
- Logo + copyright on BG3 (2bpp, chars $5000, map $4C00, priority bit OR'd in at $DC4B). Tiles LZ at $C5:ABE6
  (pointer $81:8636, size $8639 = $1000), map LZ at $C5:B406+6 (pointer $81:8648). BG3 palettes 0-2 from $80:AF5C:
  0 = white text, 1 = black / red / dark red, 2 = black / yellow / dark yellow.
- LZ format: see tools/islz.py (decompressor $80:EF1C).

## Fishing ($80:9EA3 main loop)
- Fishing view: A ($80:9F6D) = cast/act by method ($12BA: 0-4, jump table $9F8C; "Casting" = 4), X = underwater
  view, Y = $9F3B, B = leave, R = $89BA, L = $8641. Joypad: $0D96 held, $0D98 new.
- Cast ($A46D/$A510): holding A longer throws farther (A 4 frames -> hook y $AA, 20 -> $72, 36 -> $52; smaller y =
  farther); LEFT/RIGHT during the flight aims. Hook at $061C/$061E.
- Fish shadows are the 32 entries at $0FEB (x, y, flag, ?). $A8A0 bites when one is within a few px of the hook;
  method 4 then goes to the underwater scene ($BB29, per-method code $BC01/$BC0B; Casting $B8D8/$B8DF).
- Underwater: A held reels the rig in ($07CB = 1), B = 2. Fish follows the twitched rig; fish state $07EF
  (3 = hooked, set at $C888/$C974). Claude did not script a full landing; the project lead landed fish by hand
  ("a proper battle"). The fight after the hook is not documented yet.
