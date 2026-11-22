# Hikyou o Motomete (PS1) – hacking notes

## Disc
- The disc is a single MODE2/2352 BIN, SHA-1 915522f8…66e6b.
- Files are rewritten in place with Form-1 EDC/ECC regenerated (`tools/cdsector.py`).
- File locations:
  - SLPS_015.36 is at LBA 19494, loaded to 0x80010000 (file offset = RAM − 0x8000F800).
  - COMM.TIM (font and UI) is at LBA 20015.
  - NOTE.TIM is at LBA 20274.
  - TITLE.TIM is at LBA 20612.

## Text
- Strings are u16 glyph words. Control codes:
  - FFFF end, FFFE newline, FFFD page, FFF9 wait.
  - FFFA insert, FFFB number, FFFC+n number of width n.
  - FFF7+n family name, FFF8+n pause/sound, FFF6/FFF5 colour.
- The English engine (`tools/hook.py`, in the old mode-0 glyph path at 0x8002027C) adds these word types:
  - glyph < 0x500: original glyph.
  - 177+c: one English letter.
  - 0x1Fcc: one letter.
  - 0x1Ecc: tab to line start + cc.
  - 0x2020–0x7F7F: two letters.
  - 0x8000+k: dictionary entry (ASCII; ~400 entries, chosen automatically).
- `tools/insert.py` handles the English script:
  - It wraps it (menus are left as written).
  - It encodes it.
  - It moves strings that no longer fit. A lui/addiu pair or a data pointer has to be found for each one.
- Gap strings between the main text regions are ids 2491+ (`tools/dump_extra.py` → out/script_extra.json).
- Message reflow:
  - In 2-line boxes, `{E}` is a soft break unless a tab follows it (Yes/No rows).
  - In "Name:" dialogue without a Yes/No row, `{D}` is also reflowed when that saves a page.

## Names and postcards (`tools/names.py`)
- Name entry: the -O0 append block at 0x8006A6CC/0x8006A728 is rewritten. Two letters typed in a row are packed into one pair word, so the 4-word buffer holds 8 letters.
- The grid lookup tables are strings 57/58 (name entry) and 74–76 (postcard pages). Their display rows are 52–56, 47/49 and 64–73. They are written as raw words in text/en_names.txt.
- Postcards:
  - The three glyph-store sites (0x80075698/0x80075700/0x80075774) jump to a merge routine at 0x800201A4, which is dead space in the old glyph path.
  - The buffer has rows of 29 words.
- Test cheat: set 0x801764ED = 7 to add a postcard item, and 0x801768CA = 2 so the father counts as a recipient.

## Graphics
- `tools/title.py`: TITLE.TIM (8bpp). The old logo is painted out by diffusion fill, then the logo from kawa34/tools/logos/collection.png and a new subtitle and copyright line are drawn on top.
- `tools/note.py`: the NOTE.TIM header.
- `tools/labels.py`: 72 map fish tags on COMM.TIM page 0. Each is a 64×8 sprite, and the English is drawn in a 3×5 capitals font.

## Misc
- Status window: the weather/time icon was moved to the HP row (0x80015D6C, y 0x10→0x20) so area and time fit on one line.

## Build
- Scratch dir layout: files/ holds the extracted disc files, orig.bin is the original image, and `python3 tools/build.py test.bin` builds.
- Emulator tests use `tools/emu.py` (Beetle PSX libretro). `Emu.refresh()` copies a new build's exe into an old save state's RAM.

## Shop plaques (v0.9.1, tools/signs.py)
- Plaques are 16x16 in MAP/*.TIM (8bpp, two 256x256 pages), split into 8-row top/bottom halves stored apart
  (tops mostly page 1 y=216, bottoms page 0 x=0/16/32). KAKOU keeps whole plaques at page 1 (192/208/224, 239).
- signs.py finds halves by luminance correlation with the KEIRYU / SANJYO originals (>0.7, whole plaques >0.8),
  repaints the face (x/y 3..13) with fish / hook / INN / EAT art; both halves use the top half's colours.
  52 halves in KAKOU, KARYU, KARYUA, KARYUB, KEIRYU, MIZUMI, SANJYO, SEIRYU. SANJYO's お plaque taken as the eatery.
- Title: art/title_art.png (the tester's, "In Search of Hidden Lands") is used as is by title.py.
- v0.9.1 patched BIN CRC32 61F0195F.

## Menu alignment (v0.9.2)
- Command menu cursor: x = 142 + 40*col at 0x8003B45C and 0x8003B7DC; now 142 + (-col & 38) (build.py CODE_PATCHES).
  Box frame is x 140..231, so string 98 uses {>2} for the header and {>38} for the right column.
- Postcard keyboard cursor (rows 2-6): x = 24*col + 8 at 0x800765B8 (delay slot), now +6. Keyboard rows are drawn at
  x=16 (0x8001F550 call, a1=0x10). Grid tabs in en_names.txt moved 5px left (name entry shares rows 52-54, 64, 65, 69).
- Overlay panel behind the postcard keyboard is x 12..243.
- v0.9.2 patched BIN CRC32 54A8EFA6.

## Yes/No and fixed cursor spots (v0.9.3)
- The Japanese full-width space is a narrow glyph (8px), so JP layouts must be measured with space=8, kana=16.
  Choice cursors sit about 12px before the choice text: "　　はい　　　　いいえ" -> {>16}Yes{>80}No; the erase
  prompt (string 30) -> {>32}Yes{>96}No.
- Contest board header line starts at x=48; numbers end at ~200, so "Record" is {>112}.
- v0.9.3 patched BIN CRC32 D8CB1E05.

## v0.9.4 (text sweep)
- Postcards in the family intros: the event code points into the middle of strings 1120 (3 refs) and 1157 (1 ref),
  just after each {9}. insert.py now finds every reference into the middle of a string and points it at the
  matching {9} segment of the English (report key mid_refs = 4). The English must keep the same number of {9}.
- jp_geometry counts the full-width space as 8px. Dialogue pages (2-line box, BOX_W 228, names counted as 48px)
  are built by paginate(): {D} pages are merged when they fit, text is packed by sentences, a sentence longer
  than a box is split at a clause or a balanced word break, and stub lines are evened out.
- Messages also include any string whose Japanese starts with "Name：".
- v0.9.4 patched BIN CRC32 1A298318.

## v0.9.5 (second-pass audit)
- Tools now run from the hikyou/ folder: insert.py reads text/ and out/ under $HK_PROJ (default "."), title.py reads
  art/title_art.png relative. Build: `python3 tools/build.py out.bin` (needs files/ extracted disc + orig.bin).
- build.py asserts rep['stuck'] and rep['homeless'] are empty: a stuck string silently stays Japanese.
- Dialogue paginator rewritten (insert.py _layout): DP over break points. BOX_W 228 (frame at x=12/247, text from 16),
  W_NAME 46 (widest default name). Costs: page 1; sentence end 0; comma 0.8; before GOOD words 1.3; other 1.6;
  speaker label 3; penalties for short pages and single-word last lines. Yes/No row stays with its question.
- Audit helpers: tools/audit_pages.py dumps every message as laid out (pages_new.txt); audit_odd/slack/midbreak list
  suspicious pages. tools/play.py drives Beetle PSX from save states (holds: hD:6 for one menu step; hD:20 repeats).
- Staff roll: tools/staff.py redraws ENDING/STAF01-14.TIM (8bpp 256x240; palette 1-15 white ramp for names,
  33-47 pink for titles; STAF14 is "The End"). English for each card is in staff.CREDITS.
- Command menu: text {>40}, right cursor 142+41. Shop category menu (string 121): {>2} left, {>40} right column;
  the shop cursor follows the text start, Items ends ~4px inside the frame.
- Creel title (117) "Capacity {B}" at {>56}.
- Walking: CIRCLE dismisses field text; X closes menus; walking into an NPC talks. From Bro's save (jizo): R R then
  U U enters the inn; R R U U U R ... the hook-sign tackle shop is up the path; the contest official is the NPC by
  the riverside sign (R R U U L U L).
- v0.9.5 patched BIN CRC32 E1355AEC.

## v0.9.6 (test helpers)
- Secret name: string 59 (つり太郎 -> "FishTaro") is compared with the 5-word name buffer at 0x8006AFD0; if it
  matches and the record (byte 0x80108700) is 0 (Bro), 0x8006B068 fills the tackle box. tools/debug.py rewrites that
  8.8 KB unrolled routine as a table walk (verified byte-identical with unicorn) and uses the freed space.
- Name entry cap was sltiu 4 words at 0x8006A67C, so with letter pairs only 7 letters fit. Now 5, and names.py's
  append refuses a 5th word (8th letter merges into the 4th). Delete (0x8006A404 X button, 0x8006A818 "<") now
  splits a letter pair back to a lone glyph instead of dropping the word.
- Records: 1410 bytes each at 0x80176348 + 1410*rec: +0 area (1 Stream, 2 Alpine, 3 Creek, 4 Lake, 5 Plains,
  6 Coast, 7 Secret), +1 map, +2 x, +4 y (only updated on map changes).
- Travel: byte 0x80108702 = destination 1..12 (set by trigger tiles in the step handler 0x8003A600); after a step the
  field loop (0x8002E3E4 / 0x8002E4DC) reads it and switches main state 0x80108CD4 to 13 (0x80037C60 travel scene).
  Destinations: 1 Alpine, 2 Stream (village), 3 Creek, 4 Stream (map 13), 5 Lake, 6 Creek (map 31), 7 Plains,
  8 Creek (map 31), 9 Coast, 10 Plains (map 42), 11 Secret, 12 Stream (map 6).
- Warp hook (debug.py): both reads become jal to a routine that, while Select is held (game pad word 0x80108840:
  Select 0x100, L1 4, R1 8, O 0x20, X 0x40, Up 0x1000, Right 0x2000, Down 0x4000, Left 0x8000), writes the next
  area's destination (L1: previous), then returns the byte.
- insert.py: one-kana-per-line strings (gear window slot labels 108/109/111/112) are menus, not messages, so their
  {E} stays a newline (v0.9.5 joined them into "R d").
- Name entry navigation: from the J key, Up reaches OK.
- v0.9.6 patched BIN CRC32 9CA3F94C.
