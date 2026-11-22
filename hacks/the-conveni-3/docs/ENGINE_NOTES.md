# ROM notes: The Conveni 3 (ザ・コンビニ3 ～あの町を独占せよ～), PS2

## Disc
- Serial SLPM-62322, VER 1.30, NTSC-J. Hamster / Masterpiece, 2002-2003. PS2 **CD** (MODE2/2352, 1 track).
- the project lead's image: `rom/Conveni 3, The - Ano Machi o Dokusen seyo (Japan).7z` → .bin CRC32 2143FE1F,
  SHA-1 597f58e9bef568d7ab07273210c625fd0252386d (Redump naming). Converted with `rhtk ps2 to-iso` →
  an ISO with CRC32 E2F31095 (2048-byte sectors; this is what we patch and test). rom/ only holds the .7z
  (rom/ is read-only for us), so each session: `7z x` the .bin into a scratch folder, `rhtk ps2 to-iso` it,
  check the CRC32, and pass that path to tools/c3_build.py and tools/emu.sh.
- BIOS: your own dump (an SCPH-39001 BIOS was used); never share it.
- Top level: SLPM_623.22 (ELF, 4.4 MB), IRX/ (IOP modules), SOUND/ (HD/BD banks), DATA/GAMEDAT1-4.DAT
  (1/2/4 start with zeros; 3 starts with a WAVE header, likely streamed audio/voice), PAC/*.PAC, ONETEX.PAC,
  ALLDATA.PAC, STEREO/*.VGS + MONO/*.VGM (music), MOV/MOVIE00-01.PSS (video).

## Containers
- PAC: "PAC\0", u32 header_size (=12+8n), u32 count n, then n x (u32 offset, u32 size), data 0x800-aligned.
- LZS: "LZS\0", u32 unpacked size, Okumura LZSS (flags LSB-first, 1=literal; ref = b0 | (b1&0xF0)<<4,
  len (b1&0x0F)+3; 4 KB ring zero-filled, start 0xFEE). `tools/c3pac.py` reads/writes both;
  recompression round-trips (tested on ALLDATA #1: 48846 → 49183 bytes, a little larger than the original).
- ALLDATA.PAC: 53 entries; 31 LZS→"TEX\0", 12 raw "LSC\0", 4 raw "TEX\0".
- ONETEX.PAC: 307 entries, all start 10 00 00 00 (PS1 TIM-style, e.g. flag 9 = 8bpp+CLUT). Textures.
- PAC/CN3.PAC: 34 entries (33 LZS). Text dumped by `tools/c3_cn3dump.py` → `script/cn3.json` (1083 unique
  strings, 11.7k chars, 15k locations; identical text is one entry listing every [member, offset, cap]).
  All text sits in fixed zero-padded slots, so it is replaced in place (no pointers).
  - #000-#013, #016-#023, #027-#033: one per map/scenario, 568,784 bytes each. Report templates in 259-byte
    slots at 0xC80F (給料アップ, 返済, 誘致, …), scenario text at ~0x10AC8, and the staff roster (30 names,
    schools, hobbies, licenses; 32/64/128-byte fields) repeated in every map.
  - #023 also holds staff career-history lines (年 4月 貴社6号店 入社 …, 59-byte fields, built with numbers).
  - #024: angel advice per event, 224-byte slots, three voices each (polite / brisk わよ / drawl ～ですの～).
  - #026: customer types (80-byte records with stats) and their barks, products (16-byte name fields: only 7
    full-width chars), fixtures and blurbs (64-byte), events (デフレ, 不景気).
  - `cap` is measured to the next non-zero byte, so the last slot in a region shows a huge cap; real fields
    are 16/32/64/128/224/256/259 bytes. UNSURE: clamp to those when inserting.
  - Half-width text would double every limit; 16-byte product names make it close to required.
- PAC/LSC_*.PAC: LZS→"UNI\0". LAYOUT.PAC: save layout data.

## Text
- Encoding: Shift-JIS. Main script is in the ELF (SLPM_623.22): ~740 clean runs, ~10.6k chars found by a
  strict scan (help text, menu descriptions, product descriptions at 0x41EDE0+, assistant lines at 0x24B9F9+).
  ELF mapping is in project.json `elf.mapping`; `rhtk xref SLPM_623.22 <off> --mapping elf` also finds lui/addiu.
- The in-game font draws full-width Latin, Greek and kana; the name entry offers A-Z/a-z. Message boxes look
  proportional (half-width digits are narrower), to be confirmed.
- ELF strings (`notes/elf_strings_scan.json`, from a strict scan): 926 clean strings, ~29.4k chars. 726 have a stored
  32-bit pointer somewhere in the data segment; most of the rest are fixed fields inside 0x88-byte map-tile /
  building records (樹（広葉樹）, コンビニ店舗 …) or reached by lui/addiu (memory card messages at 0x4237F0+).
- Control codes (ASCII inside SJIS text; counts across both dumps). Keep them exactly; UNSURE = guessed from context:
  - `/n` newline (705). `/N` newline in report lines. `/r` new paragraph/page inside a box (UNSURE).
  - `/kA` `/kB` `/kV` `/kE` wait for a button, then continue (letter = which box/mode, UNSURE).
  - `/s00` speaker/box select (`/s10`, `/s98`, `/s99` too); `/i10` portrait/icon id; `/fNN` angel facial expression.
  - `/p` clear the box. `/wNNN` pause NNN frames; a bare `/w` in labels is a small fixed space (UNSURE: half-width step,
    useful for English spacing). `/m(…)(…)` moves/opens a highlight window in the tutorial (coordinates, keep).
  - `/c1` `/c2` `/c3` colour on, `/c0` colour off. `/b…/b` boxed/small text (（/b平/b）, UNSURE).
  - `/g1` `/g2` inline marker icons; `/I100` = "メモリーカード(PS2)" graphic, `/I101` = "メモリーカード差込口1", `/I103` button icons.
  - `/0` `/1` `/2` numeric fields, `/d4` date field; `%s` `%d` printf arguments (keep count and order or the game reads garbage).
- Font test (2026-11-02, gfx/screens/font_test_2.png; patched ELF strings in place, booted to the main menu):
  full-width uppercase Ａ-Ｚ and full-width space render, and the font is **proportional** (narrow letters).
  Full-width lowercase ａ-ｚ is **skipped** (no glyphs). An ASCII byte (e.g. "1") **ends the string**.
  Header fields clip at a fixed width (メインメニュー header showed 6-7 letters).
  So English needs: lowercase glyphs added to the font (and ideally single-byte ASCII support in the renderer).
- **Font found**: ALLDATA.PAC #51 `truefont.tex` (LZS → TEX). PAC files carry a name table right after the
  offset table (ALLDATA: 53 alphabetical names; ONETEX names are angelNN.ext …). TEX = "TEX\0----", u32 count,
  u32 names_off (64-byte names), u32 ?, then (u32 off, u32 size) pairs at 0x14, each a TIM.
  truefont.tex holds 12 TIMs: large_24_00-02, small_20_00-02, talk_00-02 (4bpp glyph atlases, 256 wide),
  truefont_dec11/dec20/inport (small 8bpp). The ELF loads them by name at 0x1249CC (file 0x159CC); the call
  0x1BC6B8(a0=0, a1="small_20_00.ext", a2=0x2912, a3=20, t0=1) sets up a font.
  It is a **subset font**: only characters the script uses, in Shift-JIS order (、。・：？！々ー／～… then
  ０-９, then only the capitals used: ＡＢＣＤＥＦＫＬＭＯＰＱＴＶＸ, then kana, kanji). That is why ＧＨ and
  lowercase vanished in the test.
- **Glyph map found** (2026-11-02): the draw routine at 0x1BB298 turns a Shift-JIS code into an index
  (code <= 0xE03F: code - 0x813F, else code - 0xC190; max index 0x2912) and reads a 4-byte entry from the font's
  table (pointer list at RAM 0x2804E0). Entry byte0 = 0xFF means "no glyph" (skipped); otherwise
  (b0 row, b1 x, b2 ?, b3 width): a packed proportional atlas. Four tables, all inside the ELF, one entry per
  possible code (0x2912 x 4 bytes, so no relocation needed to add glyphs):
  vaddr 0x258BF0 (1937 glyphs), 0x263038 (1263), 0x26BC50 (798), 0x276098 (1801); ELF file offset =
  vaddr - 0x205700 + 0xF6700. Which table goes with large_24 / small_20 / talk is still to pin down.
  Table ↔ atlas: 0x258BF0 = small (20px, truefont TIMs 3-5), 0x263038 = large (24px, TIMs 0-2),
  0x26BC50 = talk (28px, TIMs 6-8), 0x276098 = name entry (26px, sel_name.tex). small/talk/name already
  have full Ａ-Ｚ ａ-ｚ ０-９; only **large** lacked G-J, N, R, S, U, W, Y, Z, all lowercase, ．，－.
- **Proof works (2026-11-02, gfx/screens/english_menu_proof.png)**: `tools/font_proof.py` copies those glyphs
  from the name font into free space on large page 2 (row tails 0-2 + rows 3-4, 24 of 26 rows, shifted up 1)
  and fills the table entries; menu header/description then show "Pick owner.", "Build a store chain and win!".
  Text is written as full-width Shift-JIS (`c3font.fw()`), `/n` stays ASCII. To do: narrow the full-width space
  (0x8140) entry width; real 24px glyph art instead of the borrowed 26px ones; maybe half-width ASCII support.
- **Space width** (2026-11-02): the draw routine (0x1BB910) and the measure routine hard-code a 15 px advance for
  ASCII ' ' and '　' (8 immediates, listed in tools/font_proof.py). Patched to 6 px; ASCII ' ' is a 1-byte space.
- **Renderer facts**: any byte other than ' ', '<', '>' (font index -/+), '/' (control code) starts a 2-byte code.
  Advance = table width x scale + per-font gap (RAM 0x41F118 halfwords: 2, 2, 2, 4 at run time). If the word at
  0x41F140 is non-zero the font is drawn fixed-pitch (glyph centred in that cell). Font pointer list at 0x2804E0:
  0 small, 1 large, 2 talk, 3 name.
- **Letter-pair glyphs** (`tools/c3_glyphs.py`, proof 2026-11-02, gfx/screens/pair_glyph_*.png): English gets the
  room it needs without code hacks. Fonts 0-2 are rebuilt with the non-kanji glyphs, a few kanji (KEEP_KANJI),
  Latin singles, and ~490 two-character glyphs ("th", "e ", " a"…) drawn with the renderer's 2 px gap inside,
  so they look like two letters. They take kanji codes from 0x889F up. `encode()` picks the fewest bytes:
  about 1.05 bytes per English character instead of 2. The pair list should be re-ranked from the real
  translation (`pair_ranking`) at build time. Side effect: any leftover Japanese kanji shows as pairs, so every
  string drawn with fonts 0-2 must be translated. The name font (3) is untouched.
  Use ’ and ” for apostrophes/quotes (ASCII ' and " have no glyph); never put ASCII '/', '<' or '>' in text.
- **File checksums**: the ELF stores (size, sum32, xor32) of the raw/compressed bytes for 126 files and every
  ALLDATA member, in two tables (vaddr 0x283930 rows of name ptr+size+sum+xor, and 0x283EA0). Any mismatch =
  black screen at boot. `c3pac.fix_sum(elf, old_bytes, new_bytes)` updates every copy. Always run it.
- LZS repacking: `c3pac.lzs_compress` uses optimal parsing and comes out ~2% smaller than the original packer
  (truefont.tex 534883 → 523356), so repacked members fit their old slots.
- The name-entry font sel_name.tex (ALLDATA #25, 26px) is complete JIS with lowercase; owner names like
  "S s" render from it on the owner card, fixed-width.
- `font.tex` (#8) is a separate fixed 16px ASCII sheet with lowercase (debug/system use?).
- DATA/GAMEDAT1/2/4.DAT are all zeros (padding: ~340 MB of free disc space for relocated files).
  GAMEDAT3.DAT is a leftover RAR of dev assets (wave/*.wav, bmp.rar with 45 BMPs: bg*, mail_*, title).

## Build
- `python3 tools/c3_build.py <original.iso> <out.iso>`: space patch, pair fonts ranked from the script's English,
  ELF + CN3.PAC text insertion, checksums, ISO patch. Strings that don't fit stay Japanese and are listed in
  build/report.json. ~5 min (the Python LZS packer on 30 CN3 members). Test build 2026-11-02 boots fine.
  `--script DIR` builds from another copy of the script files, `--extra` adds raw ELF test strings.
- Savestates hold the old program and fonts in RAM, so they can't show new text: test by playing from boot.
- "ptr" ELF strings that don't fit will need repointing into free ELF space (not written yet).

## Graphics
- Menu headings (メインメニュー, キャンペーン, オーナー選択 …), main-menu buttons and map labels (出店場所選択) are
  textures: the redraw list will be long. Title logo too.
- Real chain names appear (ローソン with the LAWSON STATION logo, プラスマート, ハムケット = Hamster's own).

## Emulator
- PCSX2 2.4.0 under Xvfb: `sh <workspace>/romhack-toolkit/scripts/pcsx2-setup.sh rom/bios/SCPH-39001.bin`,
  then `sh tools/emu.sh start|key|shot|stop`. Boots at full speed with the software renderer.
- Memory card must be formatted on first save (the game offers to). `states/` has slot 1 at the first map
  (campaign scenario 1, Lawson); copy to /opt/pcsx2/cfg/PCSX2/sstates/ and press F3 to load.
- Path through the menus: title Start → owner slot ○ → name entry (□ ends) → はい → format はい → main menu.

## CN3 record layouts found while translating (2026-11-02)
- Per-map files: 0x10AC8 scenario description (256-byte field), 0x10BC8 scenario title, 0x10BE8 and 0x10C08 the
  two town names (32 bytes each), 0x10CA8 short goal. Bytes after a terminator inside these fields are leftover
  junk from older strings, so the measured zero run under-reports the room. cn3.json entries carry `field` (slot
  size) where the layout is known; both c3_build and c3_tr use it instead of the measured cap.
- Member 23 news templates: 259-byte slots (`field` 259).
- Staff career lines: 64-byte records "   Y年 M月 event". The year digits sit in the 4 bytes before the dumped
  string. Entries have `lead` 4; write `{y}` in the English and the build fills in each copy's year
  ("Yr {y}, Apr: Joined your main store").
- Member 26 fixtures: name 32, short name 16, description 64 bytes. Products: long name 32, short name 16.
  Customer names 16 or 32.
- A "/" before a letter is a control code to the renderer ("w/chair" would be read as a colour code).
  c3_tr check flags these as SLASH.
- Talk-box text: tools/c3_wrap.py inserts /r breaks so English never relies on the game's own wrapping.

## Money format (tools/c3_yen.py, applied by c3_build unless --no-yen)
- 0x1447F0 fmt_money(a0 = amount, 64-bit; a1 = out; a2 = 0 none / 1 per month / 2 per day). Original built
  兆/億/万 pieces with sprintf (0x1F3FC0), strcat (0x1F4050), __divdi3 (0x1EF398), __moddi3 (0x1EFA30), then the
  half-to-full-width converter 0x160958 (table at RAM 0x358280: ASCII ',' -> ，, '-' -> －, digits -> ０-９;
  '/' is treated as a control code). Replaced in place by a routine that prints ￥ + comma groups (+ ／mo, ／day).
- 0x112AA8 funds window drew 億/万 with param codes (/0 /1 at RAM 0x41F158) and draw 0x1BB910. Now it calls
  fmt_money and draws the result; its unused tail holds helper 0x112B18 (amount = params[1]*10000+params[0], in
  10,000 yen units, drawn as ¥). Call sites 0x1161A4, 0x116264 (store info prices) and 0x11CA5C call it.
- String table at 0x359BE8 (vaddr): 158 entries of (jp, 0), read by getstr 0x18D6D8(id, column).

## Control codes with a letter (2026-11-02)
- `/kA` … `/kV` are one code: "/k" plus the letter (wait for a button / a tutorial action). c3_glyphs.CTRL keeps the
  letter as ASCII. Before this fix the letter was written as a full-width glyph and the angel advice box crashed.

## Angel advice box
- Member 24 tips (224-byte slots) and the ELF chatter lines at 0x24B9F9+ (129-byte records: a voice byte + 128-byte
  text, `field` 128). The box wraps by pixel width by itself: c3_wrap.py --width 320 keeps the game from splitting
  words; at most 3 lines.
- The ELF dumper now also accepts strings after a byte 0x01–0x0F (these records), which found 4 more lines.

## Textures (tools/c3_gfx.py, gfx/edits.json)
- ALLDATA #9 game.tex: TIM 3 = screen header buttons (2×16 cells of 128×32), TIM 4 = Menu/Choose Site/Store
  Size/Choose Store, TIM 11 = interior category buttons (selected / not selected). #38 stay.tex TIM 8 = OK/Back/
  Switch buttons, ON/OFF hour tiles, Licenses label; TIM 20 = loan stamps. #41 title.tex TIM 0 help topics,
  4 "New Record!!", 8 main menu, 9 chain names/new game/rank headers. #16 layout91 = results screen. #50 TIM 2
  memory card. ONETEX 221–240 = item/character cards (plain TIMs, edited in place).
- Erase modes: bg, col:X, row:Y, copy:X,Y, hgrad:XA,XB,Y, vote:H:N; "pad", "vbox" (label split over two TIMs),
  "rotate". Pixels are mapped to the texture's own palette.
- Left in Japanese on purpose: signs and posters inside event illustrations. Still open: title logo subtitle,
  "独占" banner (ONETEX 171/172).

## Number params with 2 digits: /Qn (tools/c3_pad.py, 2026-11-02)
- The clock string is "午前/0時/1分" (params at RAM 0x41F158, drawn by 0x1BABA0(out, value, min_digits) with
  min_digits 0), so English "AM 7:6". The text drawer 0x1BB910 and measurer 0x1BC8C8 jump on "/" + char via tables
  at 0x5417A0 / 0x541860 ('0'..'W', lower case folded). "/Q" was unused: c3_pad points it at two stubs (0x112BA0,
  dead code of the old funds window) that call 0x1BABA0 with min_digits 2. Clock is now "AM/w/0:/Q1" = "AM 7:06".
  c3_tr check counts /Qn as /n.
- Note: elf 1822 "%02d分" / 1823 "午%s%02d時" are NOT the map clock (patching them changed nothing).

## Script merge order (2026-11-02)
- elf.json / cn3.json are the merged result of the TSVs, and later files override earlier ones. Re-merging one old
  file alone reverts later fixes (happened once: names and shortened labels came back). To rebuild from the TSVs:
  elf: `addjp elf_labels.tsv`, then every `elf_NNN*.tsv` in sorted order (elf_000_tutorial788 first), then `elf_angel.tsv`.
  cn3: every `cn3_NNN*.tsv` sorted, then cn3_career, cn3_names, cn3_angel.
  New fixes go in a new, higher-numbered file (elf_014, cn3_010) and never by editing the JSON by hand.
- Use `python3 tools/c3_merge.py` to re-merge (canonical order; cn3 files named *_fit go after cn3_names).
  Adding elf_014 alone after elf_015 once reverted the tutorial wrap (v0.9 shipped with it: words split, pages
  overflowed and auto-advanced, a lone "done" showed). Entry 1829 (owner name banner, 0x423668) was added to
  elf.json by hand: the dump missed it because non-NUL data sits right before it.
- Tutorial prompts after /s07 and /s08 continue the same page, so page + prompt must fit 4 lines.
- Talk font English (c3_glyphs._talk_latin): A-Z, a-z, digits and punctuation are drawn from
  tools/fonts/Inter-ExtraBold.otf at 22.5 px (baseline row 21) in the talk style (AA white fill, 1 px black
  outline, 2 px shadow down-right, key colour outside). Widths are within ~1% of the old glyphs.

## Speech box (talk renderer) quirks (2026-11-02, build 15 tutorial)
- The speech box (tutorial, angel advice and chatter) drops ASCII spaces: only spaces inside pair glyphs showed
  ("build astore"). c3_glyphs.build now adds a blank glyph (mapping key " ", 4 px + 2 px gap = 6 px) and
  encode() writes an unpaired space as that code when the text has speech-box codes (/r /p /k /sNN /fNN;
  G.is_talk). Costs 1 byte per unpaired space in those strings only.
- Punctuation the talk font lacks (, ' & + # * ¥) is borrowed from the name font. It used to be inverted, which
  gave a yellow background with no transparent palette match: ’ and , drew as solid bars. Now redrawn in the
  talk style (white fill, black outline, the talk font's key colour) by c3_glyphs._talk_style.
- The fixed-pitch word 0x41F140 is set by 0x1BDFA8(a0) from 0x156E7C (26), 0x1571E0 (28), 0x160FF0 (20);
  zeroing 0x1571DC or 0x160FF4 did not change the speech box, so it is not the cause.

## Title picture (tools/c3_title.py)
- ALLDATA #43 title_eb.tex = six 32-bit TIMs (RGBA, alpha 0-128) tiling 640x512. c3_title erases the subtitle
  box (377-536, 207-231) with the plain gradient beside it and writes "~Corner the Market!~". Logo kept.
- The title screen draws from ALLDATA #42 title_eb.eb, not #43: the .eb embeds its own byte-identical copy of the
  LZS title_eb.tex at 0x1AC (offset word at 0x14, padded length at 0x18). c3_title replaces both copies.
- Tutorial pages (elf 787, 788): the box is ~340 px wide (talk font) and 4 lines tall, and the game splits words
  when it wraps by itself. tools/c3_wrap_pages.py rewraps every page with /r (run with C3_ELF = a built ELF so the
  widths are the English fonts') and splits a page over 4 lines at a sentence end with "/w045/kB/s00/p".
  Source text: elf_014b_tutorial_fit.tsv (unwrapped); result: elf_015_tutorial_wrap.tsv. 787 is within 32 bytes
  of its 6687-byte slot.

## Staff name width (Hire/Fire slot)
- The staff slot on Hire/Fire draws the stat icons over the end of the name: about 140 px by c3_tr._width with
  the small font ("Matsumoto Y" shows, its "." is covered; "Mochizuki Mai" lost the "i"). It is neither a byte
  nor a glyph-count limit. cn3_013_staff_fit.tsv gives the 12 wider names the "Family G." form.
- Event popups: in cn3_012 id 5 drops "ads" (the %s is already "Newspaper ad"). Popup %s in 43-47 is a store
  name; "%s in "Popular Stores"!" is ~445 px with "Store #12", borderline for the ~440 px box.

## Tutorial bubble sizes (2026-11-02, build 25)
- Each tutorial page's bubble is set by /m(4,x,y)(t,x,y,W,L): W = bubble width, L = lines. Text area is about
  W - 65 (talk-font units, c3_tr._width); before the first /m the bubble is ~400 wide (wrap 350).
- Source: script/tr/tutorial_src.tsv (unwrapped, not merged). c3_wrap_pages.py --src ... --margin 75 (was 65; a W=360 page still scrolled) rewraps
  each page to its own bubble into elf_019_tutorial_wrap.tsv. Pages that still overflow need a sentence break
  in the source (the tool splits pages only at sentence ends).

### Store List panel (side panel "Store List / Rating/Sales")
- Drawn at 0x114130.. (also 0x115908, 0x118048, 0x11bd8c for other store pickers). Per row (4 rows, 0x30 apart):
  name at x = fp+0x1e6, y = 0xcc+0x30*i: "Main" = 0x5273f8 (id 1280, 4 /w pads), else pad 0x527408 when the
  number < 10, then 0x527410 (id 1281 '/w/0号/b店'). Stars: 5 sprites via 0x1c69f8 at x = fp+0x224 + 15*k, same y.
  Sales via 0x112aa8 at x = fp+0x1ea, y = name y + 24. Only ~62 px fit before the stars, so id 1281 is "/w#/0"
  ("#2", matching the map marker and the quad-view tabs). Moving the stars to the sales line was rejected because
  sales of 7+ characters would run into them.
- Star string builder for pop-up messages: 0x144ce8(rating, buf, half) using ★ 0x52db10 / ☆ 0x52db18.
- ALLDATA #38 TIM 15 is the 88x104 "no portrait" placeholder (未); edited to "?".

### Fixture records (CN3 #26, 0x94-byte records) and the Fixture details panel (2026-11-03)
- Per record: long name (32 bytes) at desc-0x30, short name (16) at desc-0x10, description (64) at desc. The
  details panel title uses the LONG name, the side Fixture Info panel the short one. The first dump missed most
  long names (identical Japanese to the short name): cn3.json ids 1083-1178 added by hand (field 32), 1179 = short
  name of 池 (Pond). Leftover kanji show as garbage pair glyphs ("fr") because kanji codes are reused for pairs.
- Descriptions are shown twice: the Edit Interior bar (one line, ~440 px, drawer 0x1BB910: /n would put the rest
  on a hidden 2nd line) and the details panel (View Details on a fixture in the store view). The panel copies the
  text without /n (0x1BE3E0); 0x157D08 runs it through han2zen (ASCII space -> 0x8140, all cells 2 bytes) and
  lays it out with 0x166670 (a3 width 0x102; 8-byte cell records on its stack, x at +4, line left x at sp+0x400).
  Before a break it backs up through the kinsoku check called at 0x1667EC (a0 = cell, s0 = previous record).
  Fixed 2026-11-03 (build 41, tools/c3_wordwrap.py): space pairs get their own code pages (blank + "e " pairs
  on lead 0x88, " w" pairs on 0x89, c3_glyphs.build(pick=...)) and a stub at 0x112C50 allows a break only next
  to a space, or after a line's first cell. Verified in game: "A register that also / takes photo orders".
  Lines start ~6 px in when the break falls before a " w" pair (its own space). Dropping pairs with a space
  costs ~20 strings too long (tutorials 787/788 most), so keep them.
  Any "/X" code other than /n in a description freezes View Details (/L and /A tried): keep descriptions plain.
- Edit Interior side panel prices use "/Gn" (tools/c3_gcode.py: param n through the yen formatter, "¥45,000").
- The "置けません" stamp under unplaceable fixtures is ALLDATA #9 TIM 10 (two copies at y 492-512): "Can't place".
### Speech-box wait codes (tested 2026-11-03)
- Event advice tips (CN3 #24) ended with /kA (close on a timer); now /kB (wait for a button, as the help bubble).
- Conveni Encyclopedia answer box: ~390 px, 7 lines, no paging: "/kB" mid-text freezes it, "/s00" prints the
  owner name. Answers wrapped by tools/c3_wrap_qa.py (elf_024).
- Let's Play! scenario goals in the scenario-list bubble are ELF 357/358/359/361/363 (not cn3 1062-1072, which
  changed nothing in game): ~235 px, 4 lines, byte caps 23/55/55/15/31 (elf_025). Repointing is possible
  ("repoint" key, c3_build FREE) but FREE is only ~200 bytes and mostly used by the bottom bar.
- Never start a line with a digit: "/n3" is read as a code (merge check DIGIT warning). c3_wrap_qa carries the
  word before a digit down with it.
- A string the build reports as too long is left in Japanese, which shows as garbage pairs: keep too_long at 0.
### Preview tool
- tools/c3_preview.py <built.iso> [out]: draws each box type with the real glyphs and flags re-wraps/overflow.
  Tutorial pages that are only a /m(...) box still set the next bubble's size (keep_boxes). Copy of the sheets
  for the project lead in preview/ (index.html).
