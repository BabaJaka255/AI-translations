# Development log: Legend of the River King (Famicom)

All work happened on 2026-11-22 in one long session, with Claude doing the hacking and the project lead
directing and reviewing.

## Starting point
The project lead wanted every River King / Nushi Tsuri game that still lacked a complete English patch
translated, and this Famicom original was one of them. The lead supplied their own dump of
`Kawa no Nushi Tsuri (Japan).nes`; nothing was downloaded.

Two earlier patches existed: Disconnected Translations v0.15 (1999, menus only) and Pikachumanson v0.91 (2013).
v0.91 kept the original one-row, 18-letter box, which forced cut-down sentences and truncated names. The lead
asked for a fresh, complete translation with item and fish names that fit in full, expanding tables or pointers
where needed, so this patch is built on a new text engine. Both earlier
patches are credited; none of their files were used. Names follow the series glossary already used by the other
River King patches in this repo.

## Phase 1: finding the text
- Relative search on kana values found the tile-per-byte encoding (kana in a gojuon grid, digits at 00-09,
  dakuten as a prefix byte 1A/2A printed into the row above).
- The printer at $F11A and its control codes (numbers, enemy name, password rows, the D0 "suffix" used for
  catch messages) were traced by disassembling the fixed bank.
- The 284 pointer stubs (`LDX #hi / LDY #lo / JMP common`) and two sequential blocks (intro, ending) were
  scanned for; `tools/knt_extract.py` wrote all 317 lines with their locations to `script/lines.json`.

## Phase 2: the engine
- The program ROM was expanded from 128 to 256 KiB: banks 0-13 stay put, the fixed banks move to the end,
  and banks 14-17 hold the English text.
- A hook (`asm/text_hook.s`) maps an English line's bank in and lays it out on both rows of the box, so a line
  can be 2 x 18 tiles instead of 18. A new English font was drawn over the kana tiles (`tools/knt_font.py`).
- First version revealed both rows at once; it was changed so the typewriter shows the top row, then the bottom.
- Enemy names are 15 letters at most, but padding them statically broke short names ("Mt. Bat    appeared").
  Fixed with a run-time row-break code ($1A inside English lines) that pads the top row as the line prints.

## Phase 3: translation
All 317 lines were translated into `script/en_lines.txt`, then menus, fish and creatures. Wording calls were
mostly Claude's within the lead's standing rules (series names first, Title Case in menus, lower case in
dialogue). Short menu slots reuse forms from the series' other English releases: Caddis, Midge, Paste, Bag
(the creel), K.Hook, K.Bait. Catch messages were rebuilt as whole sentences per fish ("The char got away." /
"You landed a char!" / "You let the char go.") instead of the Japanese name + suffix, through a new pointer
table in bank 10 (`asm/fish10.s`).

## Phase 4: menus and graphics
- Every window template was rewritten (`tools/knt_windows.py`). Food and items became one-column lists so the
  names fit; that needed new cursor-movement code (`asm/menu13.s`) and new first-letter checks where the game
  compares item names. Shops show the name on one row and the price under it.
- Town plaques became pictures, as in the other series patches (INN, a hook for the tackle shop, a fish for the
  fish buyer), and the tea stall banner says TEA (`tools/knt_gfx.py`). The first banner edit landed on roof
  tiles; the right tiles were found by matching screen blocks against the CHR page.
- Title logo: Claude first drew "Legend of the / RIVER KING" from the Inter Display font, cut into the 137 tiles
  the Japanese logo used, in the same palette (`tools/knt_logo.py`). After review, the lead asked for the logo
  as an editable image, and Claude exported it as a 4-colour PNG with a guide to the usable cells. The lead
  returned a redrawn "Legend of The River King" (made with another AI image tool); it fit the limits (98 tiles)
  and is the logo in v1.0. The build now reads `gfx/title_logo.png`.

## Testing
- Claude tested in the cynes emulator, driving it with scripts and save states, and read screenshots:
  title, intro, town, every command window, eating, buying, the fish buyer, battles, casting, the reeling
  window and catch messages.
- Old save states crash on newer builds whenever code moves, so states were always regenerated from boot.
- Getting a fish to bite by playing was slow: a bite needs a suitable water tile and the right bait for the
  fish there. The bite routine was found in bank 8, and a test copy of the ROM was patched to bite at once,
  which showed the reel window (the distance is drawn with sprites) and the line-break and catch messages.
  The "landed" sentence was checked by also patching the result code in the test copy.
- What looked like a stray block after a damage number turned out to be the bold "1" glyph; no change made.
- The project lead reviewed screenshots and the patch ("Looks good") and supplied the logo. Not seen on
  screen: the ending and the in-battle Eat list.
- Every BPS was re-applied to the original ROM and compared with the build; the published source was rebuilt
  in a fresh folder and gave the same BPS byte for byte.

## How Claude worked
Claude wrote all tools in Python and the hooks in 6502 assembly (cc65), checked code patches against the
original bytes before writing them, and used the build's own errors to catch lines that do not fit. It could
not judge the art by eye the way a player would, and did not play the game end to end.

## Known gaps and ideas
- Play through to the ending on real hardware or a full emulator and check the ending text and Eat list.
- Free space left for more changes: bank 13 after the menu code, bank 9 near $BFAB, bank 10 after the fish
  pointer table, and text banks 16-17 are empty.
