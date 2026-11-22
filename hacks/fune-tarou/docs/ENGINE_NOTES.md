# Fune Tarou (SFC): engine notes

Base: `Fune Tarou (Japan).sfc`, CRC32 `5D6BA598`, HiROM 16 Mbit, no header. Addresses are SNES addresses in banks
$C0-$FF (ROM offset = address - $C00000) unless marked as ROM offsets. All patches are applied by `src/tools/engine.py`,
and each one asserts the original bytes it replaces, so the file doubles as a list of every change.

## ROM map
- $C0: main code. DB is usually $01 or $81, so absolute $0000-$1FFF reads WRAM through the mirror.
- $C1: strings, lists, tables, screen resource table. $D0: fonts. $CD and others: LZ-compressed graphics and tilemaps.
- The English ROM is 32 Mbit. The new upper half starts as a byte copy of the lower half, so a stray mirror read
  still sees the same data:
  - $E1 (the copy of $C1) holds the English strings. Untouched strings keep their addresses there, and longer
    strings are relocated to $E1:8000 and up.
  - $F0:0000-$F0:00FF: small hooks. $F0:0100-07FF: opening-speech renderer. $F0:0800-0FFF: catch list tilemap.
  - $F0:1000-1FFF: the 8x8 text font, 512 tiles in 1bpp.
  - $F0:2000-307F: the speech font (128 glyphs x 16 rows x 16 bits, then 128 advances).
  - $F0:3100 and $F0:3180: title subtitle hooks. $F0:3200: its VRAM records, $F0:3700 its OAM entries, $F0:3720
    its palette.

## Text
- The string reader is $C0:7924 (character) and $C0:79E1 (byte). The bank comes from `LDA #$C1` at $C0:79F0;
  the label-bubble measuring routine has its own copy at $C0:7F5D. Both now say $E1.
- Encoding: Shift-JIS two-byte characters (16x16 font) mixed with single bytes. In Japanese the single bytes are
  ASCII and half-width kana, looked up in the 96-byte table $C1:939B, and their 8x8 glyphs at $D0:8D0B fill only
  the bottom 8 lines of a 16-line text row.
- Controls (single bytes):

  | Byte | Meaning |
  |---|---|
  | `]` $5D | newline |
  | `/` $2F | end |
  | `^` $5E | cursor or slot mark, zero width, recorded at $08C1 |
  | `~` $7E | skipped |
  | `>` $3E | $08BD = $80 |
  | `<` $3C | $08BD = 0 |

  In Japanese, $08BD = $80 selected the hiragana half of the single-byte font.
- $C0:791A clears $08BD at the start of each string. Lists drawn by $C0:7A8A do not reset it.
- Text is drawn on BG3 through a tilemap buffer at $7F:4000. Pointers below $2000 read RAM: number buffers, and
  the angler names at $0867.
- Fixed-stride lists are read through immediates: stride, base, column and count. There are fish names
  (x17 for record titles, x12 for the catch window), chapter (x19), spot (x12), island (x11), mode (x15) and
  lures (x20). Their sites are in `build.py` `LISTS`.
- Stage labels are bubbles ($C0:7F54) sized by measuring the text up to a plain space, so labels use a no-break
  space ($5F) between words.
- Records: $C0:70F0 builds each row at $0867 (6 name bytes, a space, the number) with $08BD = $80.
- Catch list (Y on the sea map): one long string, with cursor slots in the order given by $C1:9106 (slot to
  fish id + 1).
- HUD numbers ($C0:7A38: fuel, hooks, sizes) use 2bpp tiles at $C1:93FB indexed by the character's position in
  $C1:939B.
- Opening speech: the script at $C1:C580 calls $C0:C5DE once per line. That routine clears the line bitmap
  $7F:5000-$57FF and sets $0C61 = 2 (column) and $0C63 = 0 (row). It reads characters and draws them with
  $C0:C730 as 16x16 cells. A cell's offset is (row << 10) + (col & 7) * 32 + (col & 8 ? $200 : 0), with the
  top-left tile at +0, top-right +16, bottom-left +$100 and bottom-right +$110 (2bpp). The wait after each
  character is at $C0:C61F, and the scroll between lines is $C0:C65C, 1 px every 6 frames.

## Compression
LZSS, decompressor at $C0:D6C9, reimplemented in `tools/lz.py` with a compatible greedy compressor:
- Byte 0 is unused, then a u16 item count.
- Then flag bytes, read LSB first: 1 means a literal, followed by 8 items.
- A reference is 2 bytes: offset = (b0 | (b1 & 15) << 8) + 1 and n = b1 >> 4, giving length n + 2. When n is 0,
  a third byte follows and the length is that byte + 18.

Screen resources are 8-byte entries at $C1:8760 (tilemap pointer, palette pointer, ...). The catch-list tilemap
($CD:3F36) is a 6-byte header plus an LZ stream of a 64x32-word map, which the game splits into a 32x64 screen:
screen row k < 32 is data row 2k, and screen row 32 + k is data row 2k + 1.

## Fonts
- **Single-byte text is 8x16.** $C0:79CE now gives glyph = byte, with no table search. The draw routine's
  dakuten branch ($C0:7B8A) always draws a top tile, glyph 256 + (code + $08BD) & $FF, one row above the bottom
  tile, glyph code + $08BD. $C0:7BCE takes the font address as immediates ($F0:1000) instead of from the
  resource table, which sprite text still uses.
- **Two fonts share the 512 tiles.**
  - Tall font (`data/font_en.txt`, codes $00-$7F, from GNU Unifont): caps on rows 4-13, for boxes that held
    16-px-wide Japanese.
  - Compact font (`data/font_low.txt`, codes $80-$FF, from X11 misc-fixed 6x10): ink on rows 7-15 only, for
    boxes made for half-width kana. These boxes are short and expect text low in the row.
  - `>` in a string picks the compact font through the same $08BD offset the hiragana used. It is used for the
    keyboard, the name field and End, the title-menu angler list, the records rows, the catch list names and the
    sound test.
  - $08BD is also cleared at every screen setup ($C0:D89F) and at the catch-list exits ($C0:6F7A and $C0:7087),
    so lists drawn later (labels, fish names) stay tall.
- **A single-byte space draws nothing.** Hook at $C0:7AA4 to $F0:0000: the space blanks its two tilemap cells and
  steps one column, so the many English spaces don't overwrite box graphics.
- **The HUD fishhook icon** was byte $74 ('t') drawn through the text path ($C0:808D). It is now code $5C, which
  gets a copy of the old icon glyph.
- **The HUD number path** ($C0:7A3C to $F0:0060) converts the byte back to its old table index, masking off $80.
- **The opening speech is proportional.**
  - $C0:C615 calls $F0:0100. Single-byte characters are ORed into the line bitmap at pixel column P, kept at
    $7F:F008, from `data/font_speech.txt` (16-bit rows, so glyphs are at most 9 px wide), and P advances by the
    glyph's advance.
  - A new line is detected when $0C61 is 2. Lines start at P = 16 and must end by 240; `build.py` checks this.
  - Two-byte characters still use the original 16x16 path. The delay is 4 frames per letter (it was 12 per
    16x16 character).

## Other hooks
- **Catch list boxes:** widened from 10 to 13 columns by a re-stretched copy of the tilemap resource at
  $F0:0800, with the $C1:8760 pointer changed. The order is rewritten to English alphabetical order, read down
  the left column and then the right.
- **Title subtitle** (art in `src/gfx/edit/title-subtitle.png`):
  - $C0:C1E2 runs at the start of the title fade-in, still in forced blank, and calls $F0:3100. That routine
    writes the art to OBJ tiles 480-511 (VRAM word $7E00) and its colors to OBJ palette 7 in the CGRAM buffer
    ($15D1, uploaded when $17D3 = 1), then sets the flag $7F:F040 = 1.
  - $C0:69A6, inside the wait-for-frame routine after the sprite builders and before the OAM upload, calls
    $F0:3180. While the flag is 1, that routine fills OAM buffer entries 120-127 ($1349 + 480; the title uses
    0-107). The next screen setup sets the flag to 2, and the hook then hides the entries once.

## Graphics
- The title is set up at $C0:C171. The logo, the boat behind it, the island and the railing are all on BG1 (4bpp,
  chr at word $0000, map at word $4C00, palettes 1 and 2). The sky and sea are on BG2. The boy is about 100 sprites.
  BG3 is empty on the title.
- The screen-setup routine $C0:D871 takes a 24-byte parameter table: layer sizes, map and character bases,
  and OBSEL.
- 8x8 1bpp text font at $D0:8D0B (256 glyphs), 16x16 font as LZ at $D0:78C9 (index $C1:812C).
- The CGRAM buffer is $15D1 (512 bytes), and the OAM buffer is $1349 (544 bytes).

## RAM
- $08BD: font offset (see above). $08BB: glyph and flags for the draw routine. $0961 and $0963: text cursor
  column and row.
- $0C61 and $0C63: speech cell column and row. $0C5B: speech line counter.
- $1276: frame-wait flag. $1282: brightness shadow, $80 = forced blank. $127A: pad.
- $0C70-$0C7F looks free in a static scan, but the game clears it.
- $7F:7A20-$7F:FF00 stays at the power-on fill in every state checked, so the patch uses $7F:F000-$7F:F040.

## Methods that worked
- **Finding the text:** a Shift-JIS scan of the ROM found the strings. Every pointer operand was found by
  searching for `A9 lo hi` / `A2 lo hi` near the reader calls and confirmed by changing one in an emulator.
- **Emulator:** stable-retro's snes9x core, scripted from Python. Save states give RAM, VRAM and SRAM blocks.
- **Finding code:** to find the code behind a screen, read the CPU registers from a save state (S, D, PC), then
  walk the return addresses on the stack. That is how the title code and the frame-wait routine were found.
- **Test ROMs:** small test patches that jump straight to a window (for example the catch window at $C0:7E4D)
  made rare screens quick to check.
- **Placement checks:** text placement was measured from pixel profiles of screenshots: box interiors against
  where the ink sits.
