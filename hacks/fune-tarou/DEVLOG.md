# Development log: Fune Tarou (Super Famicom)

All work happened on 2026-11-22 in one long session. Claude did the hacking, translating and testing, and the
project lead directed the work and reviewed it from screenshots.

## Starting point
The project lead wanted every River King / Nushi Tsuri related game that still lacked a full English patch
translated. *Fune Tarou* (Pack-In-Video, 1997), the boat-fishing spin-off, had no English patch and no public
documentation of its text engine that we found. The lead supplied their own dump of `Fune Tarou (Japan).sfc`
(CRC32 5D6BA598). It was copied read-only into the workspace, and nothing was downloaded.

Fish names were taken from the English Umi no Nushi Tsuri (Sea King) patch already in this repository, so the
series reads the same. The lead's standing style rules applied: series names first, a glossary decided before
the script, and natural English over literal English.

## Phase 1: finding the text
- Searching for Shift-JIS and half-width kana runs found the strings in bank $C1. The character and byte readers
  ($C0:7924 and $C0:79E1) were found by disassembling around the code that read those addresses (Capstone, with
  a small 65816 helper).
- The control bytes were worked out from the reader: `]` newline, `/` end, `^` cursor slot, `~` skip. The byte $80
  written to $08BD by the records code selects the second half of the font, which later became the `>` code.
- The fixed-stride name lists (fish, chapters, spots, islands, styles, baits) use immediates for stride, base,
  column and count, so each list site was located and recorded in `tools/build.py`.
- The opening speech has its own renderer ($C0:C730) that draws 16x16 cells into a bitmap at $7F:5000. The
  cell layout was found by dumping that RAM from emulator save states.
- `tools/lz.py` was written for the game's LZSS format ($C0:D6C9), needed for the wide font and the catch list
  tilemap.

## Phase 2: the engine
- The ROM was expanded from 16 to 32 Mbit with the upper half starting as a copy of the lower half, so any read
  that misses a moved table still finds the original. Strings moved to bank $E1, and new code, fonts and data
  went in bank $F0.
- Single-byte characters were made 8x16 glyphs (two tiles each) through the old dakuten branch, with a new font
  built from GNU Unifont. HUD numbers, the fishhook icon and the records screen each read the old table index
  and needed small fixes (listed in `docs/ENGINE_NOTES.md`).
- The catch list boxes were too narrow for English fish names. Its tilemap was decompressed, stretched and
  stored in bank $F0. A few long names use narrow hand-drawn ll/il/fi ligatures to fit.
- The catch order screen lists fish in the game's slot order, which was rewritten to English alphabetical order.
- The toolkit's BPS writer only emitted literal data at first, which made a 2 MB patch for the doubled ROM. It
  was changed to emit SourceCopy for the mirrored half, and the patch dropped to about 10 KB (16 KB with
  everything in v1.0).

## Phase 3: translation
The full script was drafted with `tools/make_script.py` and then edited by hand in `script/strings.json` and
`script/lists.json`. The glossary (`docs/glossary.md`) was settled before the script. Place names that could not
be confirmed are marked UNSURE in it. The lead read the glossary and kept it as is.

## Phase 4: the lead's review and fixes
The lead reviewed screenshots of each screen. Their reports, and what changed:

1. **Letters touching the top of boxes.** The lead asked: "Does it seem like the text sits in the boxes wrong?
   The top of the letters are hitting the top of the field." A 2-pixel drop was tried first. The lead said it
   was "prevalent across almost every text box" and suggested 3 or 4 pixels. A uniform BG3 scroll could not do
   that, because the name box and the name field share scanlines, and moving one moved the other out of place.
   That approach was dropped. The fix was a second, compact font (from X11 misc-fixed 6x10, ink in the lower
   rows) for the boxes the Japanese filled with half-width kana. Strings select it with `>`.
   - This exposed a leak: `>` from the catch list carried over into the records screen's fish title. The font
     half ($08BD) is now reset at every screen setup.
2. **"This font in the intro is too narrow."** The first English intro put two letters in each 16x16 cell. It
   was replaced with a proportional renderer and a bold font (from X11 misc-fixed 9x15 bold), and the speech was
   rewrapped by pixel width. `build.py` checks every line against the 224-pixel width. A stray pixel at the
   window top while scrolling was fixed by moving the font up one row. A few lines were reworded to fit the new
   wrapping.
3. **Title graphic.** The lead raised the title logo and was offered choices on a decision card. They chose to
   keep the Japanese logo and add an English subtitle. The lead also asked for the title graphic as editable
   files, which are in `src/gfx/orig/`.
4. **Subtitle lettering.** The first subtitle used a stock font on BG3. The lead's view: "not even 'fonts', just
   draw them... the japanese characters aren't a 'font', they were drawn with character." The subtitle was
   redrawn by hand (`tools/make_title_subtitle.py` holds the letter shapes): a forward lean, red-to-orange bands,
   a yellow edge and a purple shadow, taken from the logo's own palette. It is shown as eight sprites, so the
   logo layer itself is unchanged. The lead approved it: "Oh, I actually like that a lot. Much better!"

## Decisions and who made them
- The lead chose the game, set the style rules, approved the glossary and the reworked text layout, chose to keep
  the Japanese logo with an English subtitle, and asked for hand-drawn lettering instead of fonts.
- Claude made the wording calls within those rules: fish names from the Sea King patch, short list forms
  ("Blk Trevally"), the rewording of intro lines to fit, and the use of `Fune Tarō` with a macron.
- Claude chose the technical approach: ROM expansion, the two box fonts, the proportional speech renderer and the
  sprite subtitle.

## How Claude worked
- Wrote all tools in `src/tools/`: the builder, the 65816 assembler helper, the engine hooks, the LZSS codec, the
  script exporter and the subtitle drawing script.
- Tested in snes9x through stable-retro, driven by Python scripts that press buttons, save states and take
  screenshots. The window placement checks counted ink pixels per row inside each box. Screens that are hard to
  reach in play (the catch result and the lure window) were opened with throwaway test copies of the ROM.
- Every build was re-applied as BPS to the clean ROM and checked against the expected hashes. Before publishing,
  the repository folder was copied to a fresh directory and rebuilt from the clean ROM, and the result matched the
  published BPS byte for byte.
- Claude could not judge the art and the feel of the text by itself. The lead's screenshot reviews caught the box
  and intro font problems and the stock-font subtitle.

## Known gaps and ideas
- Not tested on real hardware.
- Not seen on screen: GAME OVER, the hidden sound test and the "Records were erased." message. A real catch in
  normal play was not waited out (the catch window was only checked with a test ROM).
- Angler names typed in kana in an old Japanese save show as odd symbols.
- The PACK IN VIDEO logo and the Japanese title logo are left as they are. The original logo layer and palette are
  in `src/gfx/orig/` for anyone who wants to redraw the logo. Reimporting it means re-packing the title's BG1 tiles
  and map (the LZ resources loaded by $C0:C171-C1CA).
- Place names marked UNSURE in the glossary could use a check by someone who knows the Izu islands.
