# The Conveni 3: development log

How the English patch was made, in order. "The lead" is the human who ran the project; "Claude" is the AI
(Anthropic's Claude, working in a cloud sandbox with a Python toolkit and a headless PCSX2).

## Starting point (2026-11-02)
- The lead wanted to try a PS2 game and picked *The Conveni 3: Ano Machi o Dokusen seyo* (Hamster /
  Masterpiece, SLPM-62322), a convenience-store chain management sim on a PS2 CD. No earlier fan translation was
  found. The lead supplied their own Redump dump and BIOS, and approved running PCSX2 in the cloud sandbox.
- Before the disc arrived, Claude added PS2 support to the toolkit (`rhtk ps2`: ISO read/extract/rebuild,
  text-density ranking, MIPS pointer search, AFS, TIM2), tested on a disc image it built itself.
- Release format decision (Claude): xdelta, not BPS, because BPS is impractical at disc size.

## Phase 1: survey (2026-11-02)
- The game booted at full speed in headless PCSX2; Claude played to the first map and saved a state.
- Most text is plain Shift-JIS in the program (SLPM_623.22). Map data, reports and customer types are in
  `PAC/CN3.PAC`, a PAC archive of LZS-compressed members; Claude cracked both formats (`tools/c3pac.py`).
- Many headings and buttons are textures.

## Phase 2: getting English to draw (2026-11-02)
- **First test:** English in the main menu showed only some capitals; lowercase and letters like G were skipped,
  and ASCII ended the line. The game ships a trimmed font holding only the characters its script uses.
- **The lead's tip:** the name-entry keyboard has full English lowercase. Claude confirmed it uses a second,
  complete font, then found the per-character glyph table in the ELF: every Shift-JIS code already has a slot,
  missing letters just point nowhere. So English needed glyphs drawn into the font texture and their slots filled,
  with no code change (`tools/font_proof.py`, `tools/c3font.py`).
- **Black-screen hang:** the ELF checksums 126 files in two tables; any changed file must be re-summed.
- **Space problem:** every string has a fixed slot and a Japanese character takes 2 bytes, so English had half the
  room it needed (a product name had 7 letters). Claude rebuilt the fonts so one character code draws a letter
  pair ("th", "e "), ranked by frequency across the English script. English now costs about 1 byte per letter,
  with no code change (`tools/c3_glyphs.py`). Spaces were narrowed from 15 to 6 px.

## Phase 3: script and glossary (2026-11-02)
- Dumps: 973 program strings first (`tools/c3_dump.py`), later 1,822 after a second pass found about 850 short
  kanji labels the first scan missed; 1,083 unique map-data strings (`tools/c3_cn3dump.py`).
- Claude drafted the glossary and voices with four questions. **The lead's decisions:**
  - title "The Conveni 3: Corner the Market!" (the lead's wording, replacing Claude's "Monopolize the Town");
  - money as ¥50,000,000 via a code change ("If you think it can be done, I like it");
  - ワゴン = "bargain bin";
  - pun place names translated, plain ones in romaji (Claude's suggestion);
  - and, on the lead's own idea, "conveni" kept as the word for the stores, like "tycoon", explained once in the
    tutorial.
- Kept as is (Claude, per the project's style guide): real chain names like LAWSON, "Angel-san", and three distinct
  voices for the tutorial angels.
- **Decision (lead, from a card):** staff names over 13 letters show as "Fukushima H." (family name kept whole,
  since coworkers in Japan go by family name).

## Phase 4: translation and code changes (2026-11-02)
- All 1,079 map strings and nearly all program strings drafted by Claude.
- **Money:** Claude rewrote the money routine (`tools/c3_yen.py`), freeing the old format strings.
- **Clock:** "AM 3:8" became "AM 3:08" through a new `/Q` text code (`tools/c3_pad.py`).
- **Bugs found in play:** a digit eaten after line breaks; apostrophes and commas drawn as bars in speech bubbles;
  tutorial words split across lines ("take i / t"); labels running past their edges.
- **Title screen:** the subtitle reads "~Corner the Market!~". The game draws the title from a second copy of the
  picture inside another file, so both copies are patched (`tools/c3_title.py`). The ザ・コンビニ3 logo was kept
  as the brand mark.
- Builds took about 11 minutes (recompressing archives), later about 25.
- **v0.9 beta** (released 2026-11-02): patches for the Redump bin and the ISO, both checked to
  rebuild the tested image byte for byte.

## Playtest round 1, v0.9.1 (2026-11-02)
The lead played v0.9 in their emulator and reported: the owner-name banner still Japanese; button-prompt text
flickering; "choppy and rough" font; poor tutorial wrapping; two-bubble dialogue advancing before it can be read.
- Cause of the wrapping, overflow, early advance and a stray "done": v0.9 had shipped an older, unwrapped copy of
  the tutorial text. Rewrapped per bubble (`tools/c3_wrap_pages.py`).
- Speech-bubble Latin letters redrawn from Inter ExtraBold in the game's outline style.
- Owner banner translated; the empty-name "Back" label restored. The flicker is the original game's behaviour.

## v0.9.2 (2026-11-02)
- The lead asked why the map marker said "Books". 本 is short for 本店 (main store) but also means "book";
  the label list had translated it on its own. Claude's mistake; fixed to "Main".

## Playtest round 2, v0.9.3 (2026-11-02 to 2026-11-03)
The lead: "Main" doesn't fit the marker; stars overlap store names in the 4-store view; Fixture Info text runs
into numbers; some angel bubbles still auto-advance; keep sweeping for untranslated screens.
- Marker is "1" (like "2" for store #2). Store tabs "Main", "#2"...; Store List uses "#2" so names clear the stars.
  Claude kept the stars in place rather than moving them bottom-right, because sales figures grow into that space.
- Fixture Info labels "Cap"/"Pull".
- Real cause of the remaining auto-advance: a few lines were slightly too wide, so the game re-wrapped them and
  scrolled the bubble. Rewrapped with a margin of 75 px (65 still scrolled) and reworded six lines.
- Texture sweep: the last Japanese tile (未 on the blank staff portrait) became "?".

## Playtest round 3, v0.9.4 (2026-11-03)
The lead: fixture names broken ("fr"), oden pot untranslated, freezer title missing, words split in descriptions,
challenge goals curt, angel two-bubble tips still auto-advance. And: "Figuring out some way to visualize the UI,
dialogue boxes, and description fields without needing to see them in-game would be useful."
- 96 fixture titles come from a second, longer name field the dump had missed. Translated with sizes.
- The 44 angel event tips ended with the game's auto-close code; switched to the button-wait code. The general
  two-bubble case could not be fixed: the game sets each bubble's size per tip.
- **Preview tool (the lead's idea):** `tools/c3_preview.py` draws every string in the game's own fonts and box
  sizes and flags splits and overflows.
- Encyclopedia answers rewrapped; challenge goals rewritten as fuller sentences.
- **Fixture details word wrap, with dead ends:** the panel ignores line breaks and wraps itself. A first code patch
  froze the game on View Details and was reverted (`tools/attic/`). Claude then found the panel converts spaces to
  full-width first, which explained the freeze, and wrote a word-break rule for its layout routine 0x166670
  (`tools/c3_wordwrap.py`). Rule found the hard way: never put `/X` codes other than `/n` in fixture descriptions.
- Edit Interior: descriptions on one line, prices with commas through a new `/G` code (`tools/c3_gcode.py`),
  the 置けません stamp reads "Can't place".

## v0.9.5 and v0.9.6 (2026-11-06)
- The lead: the Clerk Info age line runs off screen, and asked whether the font is monospace. It is variable
  width; the bottom button bar puts each letter in a full-width cell (no pairs), and some glyphs carry built-in
  blank space. The age line became "22, M"; career line "Joined your Main".
- The lead asked whether the career fix covered every event type. It did not: each event type has its own
  template. Claude fixed the two transfer templates ("Moved to #2", "Moved to Main (buyout)") and removed the
  Japanese ditto mark 〃 from the rest. Claude could not open the Clerk Info panel in the emulator, so these last
  changes were checked in the built files only.

## Testing summary
- Claude: PCSX2 2.4.0 headless (Xvfb + xdotool): boot, title, owner registration, tutorial, menus, store setup,
  map, Store Status, tickers, fixture panels, quad view, encyclopedia. Not every random event popup was seen.
  Clerk Info changes in v0.9.5/v0.9.6 were not seen in game.
- The lead: three rounds of playtesting in their own emulator. No real-hardware test is recorded.
- Every release: both patches decode to the same ISO, whose hash is in the README.

## How Claude worked and what it could not do
- It ran the game headless, took screenshots and read RAM from save states, but could not reach every screen by
  hand; some fixes were confirmed only in the built files.
- Its own checks: the build's per-string fit report (0 strings too long in releases), the width and size checks in
  `c3_tr.py`, the preview tool, and decoding every patch back to the tested image.
- It made mistakes the lead caught: the shipped unwrapped tutorial (v0.9) and "Books" for 本.

## Known gaps and ideas
- Signs and posters inside event pictures and the ザ・コンビニ3 logo are still Japanese.
- The clock uses Japanese 12-hour style (PM 0:25).
- Two-bubble angel tips with per-tip bubble sizes still move on by themselves.
- The bottom button bar is monospaced ("B a c k"); it could use letter pairs.
- Real-hardware test.
