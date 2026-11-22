# 7 Blades (English, Japanese disc): development log

How the patch was made, in order. "The lead" is the human who ran the project; "Claude" is the AI (Anthropic's
Claude, working in a cloud sandbox with a Python toolkit, a MIPS cross-compiler and a headless PCSX2).

## Starting point (2026-11-09)
- *7 Blades* (セブンブレイズ, Konami, 2000) came out in Japan (SLPM-65008) and was localized only in Europe
  (SLES-50109, English/French/German text, Japanese voices, 50 Hz). The lead wanted the existing European English
  moved onto the Japanese disc, which runs at 60 Hz. No earlier patch for the Japanese disc was found.
- **Scope, set by the lead:** "we don't need to retranslate the text. We're simply trying to transplant the
  localization that already exists in the PAL copy onto the Japanese copy." English only; no fixes to the English
  unless the lead flags a particularly bad line.
- The lead's discs were copied from their PC: the Japanese image whole (split into parts and checked), and only
  the needed files from the European one.

## Phase 1: survey (2026-11-09)
- Claude cracked the European subtitle format quickly: `EFF/SUBTITLE.NCB` holds per-movie scripts (English,
  French, German), LZ-compressed, timed in 1/30 s units. 1,217 English lines across 72 movies were dumped
  (`src/script/subs_pal.json`). The cutscenes have no burned-in text.
- **Key finding:** the Japanese program has no subtitle system at all; the European release added one.
- Claude first estimated "weeks" for a full port and put three options on a card. The lead pushed back ("Why
  would this take weeks?? ... it should only take hours at most") and restated the transplant-only scope. On a
  closer look the subtitle engine is about four small functions, and the Japanese movie player is identical to the
  European one apart from two missing calls. Claude withdrew the estimate.

## Wrong turn: running the European program (2026-11-09)
- To move fast, Claude started running the European executable and data on the Japanese disc with a 60 Hz video
  mode patch. It reached gameplay, but the HUD drew font fragments after the Japanese tutorial movie.
- Cause found: 66 of the 94 Japanese movies carry the next stage's data inside them, so the European program
  loaded Japanese-layout HUD files mid-stage.
- **The lead stopped this route:** they had specifically wanted to avoid converting European code to NTSC, and
  asked for the opposite: build on the Japanese program, add the European subtitle system to it, and edit the
  level data where the English changes its layout. Claude agreed it had drifted from the brief, deleted the 60 Hz
  patch and the European-on-Japanese image builder, and the project memory gained a firm rule: always build on the
  Japanese code and data, never run or 60 Hz-patch the European code.
- Kept from the detour: the subtitle dump, the archive and compression tools, and the knowledge that movies carry
  level data (which mattered later for the English images).

## Phase 2: subtitles on the Japanese program (2026-11-09)
- Claude ported the European subtitle engine to C (`src/code/subtitle/sub.c`), compiled it for the R5900 with a
  stock MIPS cross-GCC, and added it to the Japanese ELF as a new load segment at 0x6d3200 (heap start moved past
  it). It hooks the Japanese movie player where each frame is decoded. The English scripts, the European kerning
  table and font are embedded, so no disc files are added (`src/tools/b7_build_jp.py`, `gen_data.py`).
- Tested on the first Gokurakumaru movie in PCSX2: timing matched, lines centred under the video, the game's own
  Japanese text still drew afterwards.

## Phase 3: in-game text and images (2026-11-09)
- **Tutorial:** the Japanese game builds each tutorial message from fragments; the European one stores whole
  messages under the same numbers, so each Japanese slot is filled with the European English for that number.
  All matched.
- **Names, items, weapons, hints:** copied from the European tables (`b7_strings.py`).
- **Font:** the Japanese kanji font was replaced with the European proportional English font and a port of the
  European renderer (`pal_text`), as the European release does. The European font has no ○△✕□, so Claude drew
  those (`b7_font.py`).
- **Images:** the European English textures for title, character select, item, game over, save and load screens
  went into `EFF/PEACE.NCB` (`b7_peace.py`), and into the copies of those files inside the 66 movies
  (`b7_stagedata.py`; the movies must not grow). Save/load sprite layouts were made to match by running both
  games' setup routines in the unicorn CPU emulator and diffing the results (`b7_savefix.py` -> `savefix.h`).
- First test patch 2026-11-09.

## Feedback round 1 (2026-11-10)
- **The lead:** the font looks "ballooned"; letters overlap. Claude first shrank all text to 3/4, then, after the
  lead compared with the European release, dropped the blanket shrink and copied the European per-screen sizes and
  box layouts 1:1 (16 px item screen and names, 24 px tutorial, 2 px shadow, 4-5 row boxes). Third description
  lines like "Holds 6 bullets." now show.
- **The lead, on real hardware:** fully garbled movie subtitles in the Nagasaki movie (G0070) on a PS2 running the
  Neutrino loader with network streaming and compatibility mode 7. Claude could not reproduce it in PCSX2. Cause:
  the subtitle code read the font from a fixed video-memory address. It now reads the font's live location from the
  game's texture slot table every frame, like the game's own text code. **The lead confirmed the fix on hardware.**
- **The lead:** "@ knocked out." at the top left of the pause screen. Claude's bug: the Japanese message box has a
  normally blank 4th row at the corner, and the string packer had reused its blank string as free space. The packer
  no longer merges across pointed-to addresses.
- **Decision (lead):** "if PAL didn't translate them, we can." Claude wrote English for the three items the European
  release left in Japanese: 七支砲 Seven-Branch Cannon, 金丹 Elixir, 扇子 Folding fan.

## Feedback round 2: sword effects and pressure attacks (2026-11-10)
- **The lead** noticed more sword effects in the European version. Claude found the European release rewrote the
  weapon trail (effect 77) for the other blade wielders and gave Gokuu's trail (effect 10) a glow and sparks. Two
  other new European effects turned out to be water ripples for one stage. The lead corrected their own report: the
  "blue aura" was the trail itself.
- The glow and sparks come from a **pressure-sensitive attack system** only the European release has: how hard the
  attack button is pressed sets the level (hard = 1.5x damage, longer reach, wider swing, sparks; light = half
  damage). Emulator keyboards always register a full press, which is why the lead saw sparks on every swing.
- **Decision (lead, from a card):** port the full system, damage included, rather than visuals only.
- Ported as C (`fx.c`, `pressure.c`), with hooks into hitbox reach, swing arc, hit damage and the thrown blade.
  Yuri's separate copy of the system was ported too. A boot hang in the first test build was debugged and fixed. PCSX2 showed the glow and sparks on hard presses; light presses and Yuri's three
  special moves could not be tested from a keyboard.

## Feedback round 3: options and button prompts (2026-11-10)
- **The lead:** "the options menu still untranslated and glyphs swapped": European images say ✕ to select, but the
  Japanese controls use ○. Claude swapped ○ and ✕ in the three European prompt images (stage-select map, load
  menu, memory card message).
- Options screens (title and in-game): the European menu has extra Language/Text rows, so its English labels were
  mapped onto the Japanese sprite layout with a draw-time remap generated from both programs' setup code
  (`b7_optfix.py` -> `optfix.h`). Tested in PCSX2: main, Volume, Control, "Return to title?".
- The stage-select map could not be opened in PCSX2 (no save on its memory card); the edited images were checked in
  the built files.

## Testing summary
- Claude: PCSX2 2.4.0 headless, using the TCRF debug menu (stage select, movie viewer) to reach scenes: subtitles,
  tutorial, item/save/load screens, options, hard-press attacks.
- The lead: compared against the European release in an emulator, and ran builds on a real PS2 (Neutrino, network
  streaming); confirmed the subtitle fix there. The final build (options and button prompts) has not been run on
  hardware.
- Not tested: light presses, Yuri's pressure moves, a full playthrough.
- Each test patch was checked to decode to the built image. Published 2026-11-21 after re-applying it to a clean copy
  of the Japanese image.

## How Claude worked and what it could not do
- Reverse engineering with capstone and Ghidra (scripts in `src/tools/ghidra/`; `b7_r5900_sanitize.py` makes a
  Ghidra-readable copy since stock Ghidra doesn't know R5900 opcodes), diffing the two programs function by function.
- New features are written in C against the Japanese program's own routines, not patched European code.
- It could not use a pressure-sensitive pad, play on hardware, or reach some screens without save data.

## Known gaps and ideas
- HUD weapon names stay in kanji (the European release shows them in kanji too).
- Test light presses and Yuri's moves on a DualShock 2.
- A hardware run of the final build.
- The English is the European localization as shipped; an edit pass against the Japanese audio was out of scope.
