# ROM notes: Hamster Club (ハムスター倶楽部), GBC

Jorudan, 1999. Dual-mode GB/GBC cartridge, MBC5 + RAM + battery (0x1B), 2 MiB
(header 0x148 = 0x06). Title in header: `HAMSTERCLUBAJNJ`.

## Source ROM

the project lead's own dump, uploaded 2026-10-30.

```
size 2097152, crc32 8A4D86A0, md5 08261d984f5e0d103191d7bbae8fba50,
sha1 6ab81c4dec3263502a1781b600218285836c5302
```

Header checksum (0x35) and global checksum (0x4B2F) are both correct. Not yet
compared against the No-Intro DAT: a web search (2026-10-31) found no published
hash, and the DAT itself needs a download from datomatic.no-intro.org.

## Tools for this game

- Emulator: PyBoy (`pip install pyboy`) runs it headless in CGB mode. Good enough
  for screenshots, VRAM dumps and save states: `PyBoy(rom, window="null", cgb=True)`,
  `pb.button("a")`, `pb.tick(n, True)`, `pb.screen.image.save(...)`,
  `pb.memory[bank, 0x8000:0x9800]` for VRAM, `pb.save_state(f)`.
- Disassembly: `rhtk disasm <rom> <offset> sm83 --address <cpu addr>`.
- `tools/make_jp_tbl.py` generates `tables/jp.tbl`.
- `tools/hcscript.py` parses the event script; it is the `events` block's plugin.

## Text

### Encoding (tables/jp.tbl)
- One byte per glyph, glyph index = byte. Font: ROM 0xFE250 (bank 0x3F, CPU
  0x6250), 2bpp, 16 bytes per glyph, 256 glyphs. The interpreter computes
  `0x6250 + char*16`.
- 0x00 space, 0x01-0x2E hiragana (gojūon, あ=01), 0x2F-0x37 small hiragana,
  0x38-0x64 katakana (no ヘ: the game uses へ 0x1D for both), 0x65-0x6D small
  katakana, 0x6E ヶ, 0x6F-0x78 digits 0-9, 0x79 〜, 0x7A ー, 0x7B ！, 0x7C ？,
  0x7F-0x98 A-Z, 0x99 ’, 0x9A ，, 0x9B ／, 0x9C ％, 0x9D 。, 0x9E 、, 0x9F ：,
  0xA0 ・, 0xA1 …, 0xA2-0xA5 & * ♂ ♀, 0xB3/0xB4 corner brackets (used like 「」),
  0xB7-0xBA ▼▲▶◀, 0xE0-0xE9 父母．♡？上下左右走. 0xC0-0xDF are UI frame tiles.
- Dakuten 0x7E and handakuten 0x7D come *after* the kana and are drawn on the
  row above without moving the cursor. The table maps the pairs (e.g. `067E=が`).
- No lowercase Latin and no Latin punctuation: the English font has to replace
  kana glyphs (see Font plan below).

### Event script (block `events`, plugin `tools/hcscript.py`)
- Scene table at ROM 0xE650: 51 entries of (bank byte, addr16). Banks used: 0x03,
  0x0B, 0x0C. Scene index is in RAM D8A6; the loader is at 0x324A (bank 0).
- One more scene at 0x2F5FD (bank 0x0B, breeding explanation) has no table entry;
  it's listed as `extra_scenes` so it gets dumped. UNSURE whether it's reachable.
- Each scene starts with a setup byte (initial portrait, stored to D8A0), then
  bytecode. Interpreter: bank 0 0x32A3; script pointer D8A8/D8A9, bank D8AC
  (re-selected before every byte, so the script can live in any bank).
- Bytes < 0xE8 are glyphs. 0xA3 returns from an F2 string (jumps to D8AA/D8AB).
- Line = 18 tiles, 2 lines per box, text auto-wraps at 18. Text tiles are
  rendered one tile per character into VRAM 0x8C00+ (cursor D8A7, 0..0x23).
- Commands (jump table at 0x32C5):

| Byte | Params | Meaning |
|---|---|---|
| E8 | 0 | end of scene |
| E9 xx | 1 | play music xx |
| EA xx | 1 | play sound effect xx |
| EB xx [..] | 1 (+1 for subs 07, 0D; +2 for sub 11) | misc engine calls (22 subs, table at 0x351A) |
| EC aaaa | 2 | goto (same bank) |
| ED n t1..tn t0 [prices] | 1 + 2(n+1) | menu with n options; t0 = B-button target or 0000. n=5/6: cage picker, 2 targets. In shop mode, prices follow; never run as code |
| EE | 0 | clear box (`<clr>`) |
| EF | 0 | new line (`<br>`) |
| F0 | 0 | wait for button (`<wait>`) |
| F1 xx | 1 | open a sub-screen (name entry etc.) |
| F2 xx | 1 | insert string xx (`<name xx>`): 00 player name, 01 hamster name, 02 honorific the player chose, 03 name the player gave the rival girl, 04 cage list, 05 cage list for swapping |
| F3 v x | 2 | flag[v] = x |
| F4 v x | 2 | flag[v] += x |
| F5 s x | 2 | stat[s] += x (clamped at 0xFA) |
| F6 xx | 1 | change portrait (continues) |
| F7 sub [..] aaaa | 1 + 0-2 + 2 | if condition then goto aaaa (11 subs, table at 0x3A3D) |
| F8 xx | 1 | engine call |
| F9 s t1 t2 t3 t4 | 1 + 8 | branch on a hamster stat band (4 targets) |

- Messages: `hcscript.messages()` groups glyphs with EE/EF/F0/F2 into one entry,
  split at every jump target. 465 entries, about 17 KB of Japanese.
- Menu option text sits right before the ED command: options start with a 0x00
  space where the cursor goes. Two columns, cursor at columns 0 and 9, so an
  option label can be 8 characters at most.
- Portrait ids seen (script `face` field): 00 shop owner, 0B shop owner (sad),
  01-04 rival girl (02 laughing), 05 rival boy, 06 rival boy (flustered),
  07-09 narration screens, 0A player reaction.

### Other text (not dumped yet)
Found by scanning for kana runs outside the script; each needs its own block:
- Fixed-width tables padded with 0xA3 (＊): hamster tricks, cleanliness states,
  food names and amounts, training levels, contest names (around 0x2A8D-0x2E00).
- Care-result messages and item names (around 0x3DBA3, 0x3ED61).
- Contest announcer scripts (0x10A03 charm contest, 0x1CB8B frog-jump contest,
  0x21DD6 Pretty Cup) in a different format with their own codes.
- NPC hamster name list (around 0x11300, `＊`-separated), repeated at 0x1CA9D,
  0x2123A.
- Cup/rank UI strings (0x6818, 0x9421, 0x3CA3F), link-cable/breeding check
  (0x31935), name entry keyboard (kana grid, 【カナ】【AB】 modes, 8 characters).
- Title logo ハムスター倶楽部 and the Jorudan / Nekogumi logos are graphics.

## Graphics
- Font: see above. `rhtk gfx-rip rom/original.gbc 0xFE250 2bpp_gb gfx/orig/font.png --count 256`.
- Compression: none seen around the font.

## Free space
- ROM is 2 MiB of a possible 8 MiB on MBC5. Plan: `expand_to` 4 MiB and put
  relocated English text in banks 0x80+ (guaranteed unused).
- Bank 0 has 119 zero bytes at 0x3F89-0x3FFF (candidate for the far-jump hook;
  verify it's never read).
- Bank 0x4C is all zeros (16 KiB). Not verified unused.

### Other text map
`tools/textscan.py` scores byte bigrams against the dumped script to find the
rest of the Japanese. Its output for banks 0x00-0x0F is in
`notes/text-candidates.txt` (banks 0x12+ only give graphics noise). Areas:
- bank 00 0x2200-0x2E80: personality traits, tricks, cleaning/health states,
  food names and amounts, training levels (fixed width, ＊-padded)
- bank 01 0x4BF9-0x7880: care events (sick, died, babies), cup names, item lists
- bank 02 0x9290-0xB350: training menu, breed list, cup list, breed descriptions
- bank 03 0xD4CB-0xDACD: cage names (fixed width)
- bank 04 0x10A0F-0x11390, bank 07 0x1CA0A-, bank 08 0x211A7-0x22BB5: contest
  announcers and NPC hamster names
- bank 09 0x2528C-0x25426: controls help for the race
- bank 0C 0x314C7-0x32D9A: save prompt, breeding compatibility, printer
- bank 0F 0x3C5A9-0x3ED76: schedule, care results, items
- Name entry (title あなたの、なまえは？ and the keyboard grid) draws with the
  same font codes, so it shows English letters in place of kana until its
  tables are translated.
- Name entry keyboard data is in bank 02 around 0xB600-0xBB90: the AB page's
  character grid is at 0xBB59 (ABCDE PQRST 01234 ’，。、・＆！？ ... FGHIJ UVWXY
  56789：…〜ー／『』【】 KLMNO Z), and the kana pages and their cursor
  neighbor tables sit just before it (0xB813-0xBB58). Code that edits the name
  (dakuten handling, cursor, 8-character limit, D895/D899) is at 0xB6C0-0xB800.
  Plan: hiragana page -> lowercase + punctuation, keep the AB page.
  Done 2026-10-30 (tools/make_keyboard.py -> patches/keyboard.ips):
  three pages, each a 32x18 tile map in bank 0x36 (hiragana 0xD8000, katakana
  0xD8800, AB 0xD9000; title on row 1, keys on rows 8-16) plus the character
  list the cursor reads (bank 02: 0xB981 and 0xB9BA, 57 positions; AB 0xBB5B,
  55). Cursor x/y per kana position: 0xB905 / 0xB943 (tile = x/8-1, y/8-1).
  Neighbor tables: kana 0xB80D/0xB84B/0xB889/0xB8C7, AB 0xB9F3/0xBA2F/0xBA6B/0xBAA7.
  Positions 0x39+ (kana) / 0x37+ (AB) are the buttons: page switch, Sp, Bs, Ed.
  D8A3 picks the title: 0 player (map row 1), 1 hamster (15-byte string at
  0xB348 drawn at 0x9822, gender tile A4+n at 0x9828), 2 cage (tiles D7-DA,
  "ケージ", written at 0x9824 over the player title; make_font.py redraws them
  as "Cage"). 7E/7D on a page trigger dakuten merging, so they're gone from
  the English pages. Default names (しげっち etc., ＊-padded) are in the bank 03
  tables at 0xD7D1 and still Japanese.
There are 22 separate print routines (`ld hl,$6250` sites) across banks, so
each screen's strings need checking for their own codes and lengths.

## Code hacks (implemented in tools/hcscript.py insert())
- Far jump for the script: commands FA bb aaaa (set D8AC=bb, pointer=aaaa)
  and FB (no-op), via `jp $3FA0` over `cp $E8 / jr c` at 0x32BC; hook code at
  bank 0 0x3FA0-0x3FCA. Translated messages that don't fit in place become
  `FA` to the English text in banks 0x80+, which ends with `FA` back to the end
  of the original message. A message shorter than 4 bytes takes the following
  non-jump commands along with it. Tested in the emulator 2026-10-30: works,
  status box intact.
- `<br>` fix: 0x3446 `cp $12` -> `cp $13`. Text auto-wraps at 18, and the
  original EF jumped past the box after a full 18-character line, drawing over
  the date/money tiles. Now a `<br>` after a full line is harmless, so
  translators can always write `<br>`.
- English font over hiragana 0x01-0x20 (`tools/make_font.py`): a-z . , - " ; +
  plus the game's own capitals, digits and punctuation. `…` is one tile (0xA1),
  so use it instead of "..." to save space. Apostrophe is the game's ’ glyph,
  typed as a straight `'`.
- ROM expanded to 4 MiB (`expand_to`), header 0x148 updated by rhtk.
- Honorific (F2 02): code at 0x389D copies 3 bytes from 0x38D4 (さん, C303=1),
  0x38D7 (ちゃん, 2) or 0x38DA (クン, 3) into the D8AF buffer; C303=0 (no
  honorific) returns at once. insert() repoints the three `ld hl` immediates
  (0x38A5, 0x38AC, 0x38B1) to 6-byte strings at bank 0 0x3FD0 and changes the
  copy length at 0x38B7 to 6 (project.json `honorifics`). Tested: all four
  choices print correctly.
- The blinking "press A" icon covers the 18th column of line 2. The Japanese
  script only puts punctuation there; tools/hc_tr.py enforces the same.

### Fixed-width tables in bank 00 (dumped 2026-10-31)
- Index helpers in bank 0: 0x0A85 = word pointer table lookup, 0x0A92 = hl += a*8,
  0x0AA5 = hl += a*16. Draw routine 0x0C90 (bank 2 wrappers 0x643B / 0x6448):
  hl = string, de = tile buffer (one tile per glyph), bc = the dakuten row,
  a = length. 0xA3 padding is skipped (draws nothing), so a short string leaves
  the rest of its tiles alone.
- 0x2005 body types x16 (8), 0x2085 traits x16 (91, through 0x2625), 0x2635 mood
  ratings x8 (5), 0x265D tricks x16 (88), 0x2BDD cleanliness x8, 0x2C1D cleaning
  results x16, 0x2C9D health x8, 0x2CDD food x16 (10), 0x2D7D food left x8 (9),
  0x2DC5 training progress x16 (11).
- Status window (bank 02 0x8D70-0x8E2E): label "Mood:"/"Cond:" at column 0, value
  tiles follow; patches/hacks.ips moves the values from column 4 to 5, so they
  have 5 columns. Body type follows "Wt.:" at column 4 (6 columns). Trait at
  column 1 (8 columns).

### Home menu graphics
- Tileset 0xD4740 (0x32 tiles to 0x9000, loader 0xA092), BG map 0xDB000 (menu
  scrolls; 10 items on rows 2-20), window map 0xDB800 (trick list). Kana tiles
  are used only by these maps; tools/make_homemenu.py redraws 25 of them as letters.

### Contest announcers and NPC names (dumped 2026-10-31)
- Announcer messages are length-prefixed (1 byte, then text) and auto-wrap at 18
  columns; the Japanese pads line 1 with spaces, so the English does too (2 lines).
  Pointer tables: bank 04 0x109DA (21, Charm Awards), bank 07 0x1CB80 (4 used;
  entries 4-5 point past the text, at code), bank 08 0x21DAD (20, Pretty Cup).
  Each bank's draw code is the same: index*2 into the table, then 0x0CEB with
  hl = text, de = 0x8C00, which renders to the WRAM buffer at 0xD000 for VBlank
  to copy. Blocks announce04/07/08 (rhtk `length_prefix`).
- NPC hamster names: 34 word pointers, names end in 0xA3 (read with
  tables/jp_names.tbl / en_names.tbl, which make 0xA3 the end code). The counter at
  0x0CD6 stops at 0xA3 or 8 letters, so names are 8 letters max. Tables: bank 04
  0x112A6, bank 07 0x1C9B9, bank 08 0x21156 (same 34 names in each bank).
- Hamster name-entry title (0xB348) is written by patches/keyboard.ips
  (make_keyboard.py PET_TITLE), not by a script block.
- Home screen hamster box, age line (window map row 3, attributes at 0xDBC00):
  "生NNヶ月" is now "<cake>NNmo". make_homemenu.py redraws the 生 tile (0x14) as a
  cake and ヶ月 (0x15) as "m"; make_hacks.py moves the digits (ld hl,$9C66 at
  0xA1EC) one column left.
- Debugging trick: from a save state, write a stub at 0xC800 that sets the ROM bank
  (0x2000 and HRAM 0x9C/0x9D, which 0x09FE restores after each glyph copy) and
  calls the draw code, then read the 0xD000 buffer.

### Found in the fresh-game playtest (2026-10-31)
- Hamster list line 2 = training policy (0x3C582, 8x5, lists block) + habit.
- Room screen captions and cage-view icon captions are tile maps in a small font:
  tools/make_roomlabels.py -> patches/roomlabels.ips (details in its docstring).
  The cage-view hamster box age line is there too.
- Event names: bank 00 0x2E85, 16x8 (block eventnames), 9 columns max because of
  the contest list window.
- Schedule header "<M>がつ <W>しゅうめ" is written tile by tile by code at
  0x3C7C7; make_hacks.py makes it "<M>mo <W>wk". Rank digit is drawn at column 13
  after the "HAM'S Cup  Rk" strings, so those are exactly 13 columns.
- Cage cleanliness words: 4 letters max (cage view draws them into 4 tiles at
  0x8940, then the cage name at 0x8980; a longer word spills into the name).
- Cage status food line: food name, separator tile (code at 0x3E8E4, now ':'),
  のこり (now a space), amount. Food screen: message box is 13 columns; the
  amount after "Left" is moved one tile right (0x3CF1F).
- Weekly report stat labels: bank 01 0x4D55-0x4D6F, back to back, drawn by code
  at 0x4B26-0x4B6C (inline01 entries 27-32).
- Contest entry banners: tools/make_banners.py -> patches/banners.ips; table of
  tileset/map per event in its docstring.

### Contest screens (played through 2026-10-31)
- Forcing a contest in testing: on the room screen poke C2A5 (week index) and
  C2E8=1 (HAM'S Cup entry, hamster 1), then Next Week. The week's cup is
  table[0x318A + C2A5*2] (alt table 0x31EA if C31F), written to D8DA (high
  nibble = rank, low = event 1-8). Week indexes for rank-1 events: Pretty 0,
  100m 1, Leapfrog 4, Lovely 6, Snack 9, Bars 12, Seed 16, Wheel 20. The Charm
  Awards (Lovely) loop forever if the hamster knows no trick (record +0x30..37,
  hamster 1 at 0xC4BF), so poke C4EF.. too.
- Help screen titles: bank 09 0x250DD, 8 x 18 bytes, drawn by 0x0C77 -> block
  racetitles.
- announce08 has 21 entries (the last, 0x21FF0, is the goodbye line).
- tools/make_contest.py -> patches/contest.ips: the "Contestant N"/"-san" lines
  the code builds with immediate stores (banks 04/07/08), the Pretty Cup score
  template (0x22B92) and Leapfrog result templates (0x1D3E8, 0x1D40B), the
  Seed Catch score bar labels and the podium screen boards. Details and
  offsets in its docstring. UNSURE: the Leapfrog "0M65.83" format; kept as
  "0m65.83" (meters, then cm?).
- Podium screen: tilesets 0xBE190/0xBD9B0/0xBD1B0, maps 0xB9800 (results),
  0xBA000/0xBB000/0xB4000/0xB5000 (1st/2nd/3rd/last), 0xBA800/0xBB800/0xB4800/
  0xB5800 (grading stamps). 12 board tiles are still free.
- Sound-effect lettering in the trick animations is art: see "Baked-in art" below.

### Review pass (2026-11-02)

- Last leftover string: the vacuum accident popup すいこんじゃった！ at 0x3C2D4
  (bank 0F 0x417C). It fires on A/B in the cage-clean screen when D8D8==3 (the
  "Outside" cage), a hamster is in C4A2-C4A5 and random < 7. Drawn by
  `ld hl,$42D4` at 0x3C280 / `ld a,$0A` at 0x3C289 to 0x99A0; the hamster name
  goes to 0x99E2. Now in block inline0f. To force it in testing, use a copy of
  the build with 0x3C19F changed from 7 to 0xFF.
- Contest result box (bank 01 0x75D0-0x76A0): "Prize " (0x7830, max 6) at
  0x9961, then the amount, then "G won!"; points: the number at 0x9901, then
  " points" (0x783C, max 7) at 0x9903. The portrait starts at column 10, so
  the points line must end by column 9.
- Weekly report events: state FFA2=5 is the report (bank 01 0x4000). Per
  hamster flags D8E8 sick, D8F8 missing, D908 cat, D918 death. Poke one to 1 at
  the moment FFA2 becomes 5 to force that event (from a room save state: Next
  Week = down, down, down, A, right, A).
- Graphics loads all go through the copy routine 0x09FE (a=bank, hl=source,
  de=VRAM/RAM destination, bc=length); hooking it logs every load.
  Palettes are staged at C0A0 (BG) and C0E0 (OBJ), BGR555.

### Baked-in art (2026-11-02)

Everything with Japanese lettering drawn into the pixels is ripped to
`gfx/orig/art/` (README.md there lists each sheet, what it says and a
suggested English version) and listed in project.json `gfx`. The build only
reinserts sheets that exist in `gfx/edit/art/`, so the project lead's redraws go there.
Each sheet packs back to the original bytes, and reinserting the unedited
sheets leaves the build identical.

- Report events: ACCIDENT banner 0x6F550 (60 tiles, 8x16 sprites, 10x3
  cells, OBJ palettes from 0x6F910); the two-kanji labels 0x6F920 (40 tiles,
  rows 出産 死亡 事故 病気 逃亡, each two 16x16 halves sliding in from both
  sides). Pictures: illness 0xC5FE0 (0x590, has red ケン cough marks, four copies of one 2x4-tile block: tiles 3,4 / 6,blank / 10,11 / blank,18; demo redraw in gfx/demo/), missing
  0xC6A80, cat 0x65A90, death 0xC6CE0 (no lettering); the orange background is
  0x64000/0x64800.
- Boot: BG 0x12E230 (0x800 to 9000) and 0x12EA30 (0x290 to 8800); sprites
  0xE7680. Title: BG 0xE4800 (0x510) and 0xE4000 (0x800); sprites 0xE4D60
  (PUSH START, already English).
- Trick animations: 88 tricks, each with its own tile loads. Forced by loading
  a Pretty Cup (week 0) state and setting all 8 trick slots C4EF..C4F6 to the
  trick number (1-based: trick N is tricks.json entry N-1). Loads shared by
  every trick (not lettering): 0xE7390, 0xFEA50, 0xFE250, 0x6DCC0, 0x70410,
  0xBF3D0, 0xB0800, 0xB0000, 0xB09E0. 62 tricks have lettering (68 sheets);
  sprite sheets use rhtk's new `obj8x16` order.
- Pressing A during a trick skips to its end, so captures that press A miss
  lettering that only appears late (17 tricks). Start the trick, then stop
  pressing buttons. Trick code is a state machine on FFA5; its sprites come
  from ROM tables of [y, x, tile, attr] entries (OAM coordinates) copied to
  shadow OAM at C000 with `ld hl,table; ld de,C000; ld bc,len; call 09F5`
  (for example trick 4: 0x14851 hamster, 0x14871 lettering; trick 8: 0x153FD).
  Lettering sprites only cover the glyph shapes, so new words must stay inside
  that coverage (tools/frame.py reports ink that has no tile).
- Not seen yet: the birth event (出産 label exists, so it may have its own
  picture).

