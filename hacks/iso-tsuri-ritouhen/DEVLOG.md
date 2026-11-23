# Development log: Iso Tsuri: Ritou-hen English translation

All times are UTC. The work happened in one project thread between Claude (Anthropic) and the project lead.

## Starting point (2026-11-22)
- The project lead asked for an English patch of every Nushi Tsuri / River King game that still lacked a full one,
  including the two Super Famicom spin-offs (this game and Fune Tarou).
- No earlier translation or documentation of *Iso Tsuri: Ritou-hen* was found.
- The lead's earlier fishing patches in this repository gave the conventions. Fish names had to match the
  *Super Legend of the Sea King* glossary.
- Rules from the lead:
  - Translate for quality and respect the Japanese setting.
  - Glossary first.
  - Releases are patches only.
- The lead supplied the ROM from their own collection. It is the No-Intro dump `Isozuri - Ritou Hen (Japan).sfc`.

## Phase 1: finding the text engine (about 02:19-02:40)
- **Emulator.** Claude ran the game in snes9x through `stable-retro` and saved states at each screen. It drove
  the game with a small input script (`drive.py`) and looked at the screens as images.
- **Debugger.** A debugging emulator (Mesen2) couldn't be downloaded through the session's network proxy, so Claude
  wrote its own. `cpu.py` and `run.py` are a small Python 65816 interpreter that starts from a snes9x save state.
  - It has hooks on execute, read and write.
  - The sound CPU handshake at $C2:07BB is faked.
  - It was fast enough to trace a few frames of menu code.
- **Fonts.** VRAM dumps (`s9x_state.py`, `vview.py`) showed the two fonts:
  - a 16x16 kanji/kana font, LZ-compressed at $C0:0000 and decompressed by $80:EF1C;
  - an 8x8 half-width kana font, raw at $DF:CC34.
- **Text.** Tracing the menu led to the reader at $80:9272. Text is plain Shift-JIS in bank $C1, and double-byte
  characters go through a 376-entry SJIS table at $81:916F.
  - All script is in one 8 KB block. Claude split it on the `/` terminator.
  - Pointers were found from the call sites of $91A8/$9143/$92C9 and from `LDA #imm` operands that equal a string
    start. Everything is in `tools/inventory.py`.
- **Free space.** There was none, so the plan became to expand to 32 Mbit and use banks $E0/$E1.
- **Tools written:** `d65.py`/`lst.py` (disassembler and bank listing) and `asm65.py` (assembler for the hooks).

## Phase 2: English engine and script (about 02:40-03:04)
- **Text bank.** Bank $C1 is copied to $E0, and the reader's hard-coded `LDA #$C1` is changed to $E0. Every old
  pointer still works, and English strings are written to $E0:8000+ with their pointer operands repointed.
- **Menu font.** koi8x16, the 8x16 font already used by the Sea King patch, is drawn by hooks at $9229 (character
  lookup) and $9346 (half-width draw). The HUD row keeps the game's 8x8 digits.
- **Story crawl.** The crawl has its own 16x16 drawer at $E109, so it got its own hook.
  - The first version wrote to the wrong place in the line buffer, and the text came out garbled. Reading $E109
    showed the real layout: a 16 px cell is two tiles at +cell*$20, the bottom row is $100 further, and cells 8-15
    are $200 further. Fixed.
- **Glossary.** Fish names came from the Sea King glossary. Two fish were new to the series: イスズミ Brassy Chub and
  フエフキダイ Emperor Bream. Islands and spots are romanized.
- **Fitting English into fixed boxes.** These were fixed one at a time after screenshots in the emulator:
  - **Main menu:** "Change Angler" was too long, so the menu was re-laid out.
  - **Records-by-island menu:** it overflowed its box, so it now uses short island names (Udone, Shikine, Kozu).
  - **Records-by-fish menu:** it overflowed in two columns. It is now alphabetical per column, and a small lookup
    table (hooked at $89E0) maps menu slots back to fish ids.
  - **Menu cursor:** it now sits one column before each item ($9055).
  - **Record lines:** they ran past column 30. The rank and the "cm" after the size were dropped, and the spot/island
    table was relocated to a 32-byte stride.
  - **"New Record!":** it overlapped the fish name on the catch screen, so it became "Record!".
  - **Default record holder:** いそたろう became "Taro", because the field holds 6 letters.
  - **Map labels:** the label boxes size themselves to the first word, so inner spaces became a non-breaking blank
    ($A0).
- **Name entry.** It got a new English keyboard.
- **Crawl speed.** The English crawl took about 6 minutes at the original speed. Frames per character went from
  7 to 2, and from 2 to 1 while A is held.
- **Reaching screens.** Some screens were hard to reach by playing, so Claude reached them with test ROMs:
  - **Catch screen:** A in the fishing view jumps straight to it, with a fish faked in RAM.
  - **Map labels:** forced label indexes.
  - **Ending:** the intro pointer is swapped for the ending's.
  - **Erased-records message:** the game boots with corrupted SRAM.
- **First full build:** delivered at 03:04.

## Phase 3: title logo (03:04-07:03, approved 19:43)
- Claude asked how to handle the Japanese logo 磯釣り 離島篇 (keep it, the lead draws one, or Claude draws one). The
  lead chose "Claude makes an English logo".
- The logo is on BG3 (2bpp, three palettes) and LZ-compressed. Claude wrote `islz.py` (decompressor and a
  compatible compressor) and repointed the tile and map pointers at $81:8636/$81:8648.
- **First version:** typed in a stock font (Inter). The lead then asked for the original logo to edit themselves.
  Claude exported the layer in the exact BG3 colours with a list of rules:
  - one palette per 8x8 tile;
  - about 236 unique tiles;
  - keep the copyright rows and the fisherman's head clear.

  A PNG at `gfx/edit/title_logo.png` would replace the drawn logo.
- **Second version.** In the meantime the lead set a rule for every project, in another thread: lettering that
  replaces art should be hand-drawn with the character of the original ("the japanese characters aren't a 'font',
  they were drawn with character"). Claude redrew the logo without fonts:
  - "Rock Fishing" is made of hand-placed brush strokes (`title_letters.py`) rendered by a small brush renderer
    (`brush.py`). The renderer has a tilted nib, a heavy press where each stroke starts and dry-brush tails where it
    ends. It is shaded like 磯釣り: red body, dark red on the lit edge, black drop shadow.
  - "REMOTE ISLANDS" is pixelled by hand in the style of 離島篇: 2-pixel yellow strokes, a black outline and small
    ticks at the stroke ends.
  - One bug came up: the "g" descender shared 8x8 tiles with the yellow subtitle and turned yellow. The subtitle
    was moved to its own tile rows.
  - The lead approved it: "Much better!" They never sent their own edit.

## Phase 4: playtest (2026-11-22 20:12 to 2026-11-23 00:47)
The lead reported two things.
- **"The opening crawl's text looks a bit narrow"** (the same note they gave on Fune Tarou).
  - The crawl now uses that patch's bold proportional font (from X11 9x15 bold). It is drawn by a new $E109 hook at
    any pixel column (kept at $7E:1D00, free RAM).
  - The hook clears the line buffer at the start of each line and ORs each glyph in across two tiles.
  - Lines are wrapped at 224 px, and the glyphs sit one row lower to look centred in the box.
  - Checked in the emulator through every scene of the intro and the ending.
- **They couldn't land a fish.** Claude checked whether the patch could be the cause.
  - The same save state was run on the Japanese and the English ROM with identical inputs, in separate emulator
    processes (`tools/test/lock.py`). The runs covered 30,000 frames after a cast, and a scripted far cast, bite and
    underwater sequence.
  - WRAM matched except for a few bytes of stack/hook scratch, so the patch doesn't change gameplay.
  - From the code, Claude worked out:
    - the cast: how long A is held sets the distance, and Left/Right steers;
    - the bite: a fish shadow must be within a few pixels of the rig;
    - the start of the underwater scene.
  - Claude did not manage to script a full catch. In 4,000-frame searches the fish followed the twitched bait but
    never bit.
- Later the lead landed a Scorpionfish and set a record: "Finally got one! Fishing in this game is a proper battle,
  though I suppose that makes sense as it's ocean fishing. Everything looks good I think." They then chose to publish.

## Decisions and who made them
| Decision | Who |
|---|---|
| Translate the whole game; fish names follow the Sea King glossary | Project lead |
| Island and spot names romanized; short forms in narrow menus | Claude |
| Default record holder "Taro"; rank and "cm" dropped from record lines; "Record!" | Claude |
| English title "Rock Fishing: Remote Islands" | Claude proposed, lead approved |
| Claude draws the logo; hand-drawn lettering, no stock fonts | Project lead |
| Bold proportional crawl font, same as Fune Tarou | Project lead asked, Claude implemented |
| Crawl speed raised to 2 frames per letter | Claude |
| Publish v1.0 | Project lead |

## How Claude worked
- **Checking its own work:**
  - Every hook patch asserts the original bytes, so a wrong ROM or a misplaced patch stops the build.
  - The BPS was re-applied to a clean ROM after each build.
  - Before publishing, the whole `src/` folder was copied to an empty directory and rebuilt. The output matched the
    published patch byte for byte.
- **Seeing the game:** every screen was checked from emulator screenshots (snes9x via stable-retro). The lockstep
  RAM comparison was the check that gameplay was untouched.
- **What it couldn't do itself:**
  - play the game the way a person does, including the fishing fights;
  - judge whether the art and fonts looked right without the lead's review;
  - test on real hardware.

## Known gaps and ideas
- **Untested:** real hardware.
- **Fishing:** the fight after the hook isn't documented. The variables found so far are in
  `docs/ENGINE_NOTES.md` under Fishing.
- **Old saves:** names saved by the Japanese game still show in kana.
- **Your own logo:** replace the title logo by saving a PNG at `src/gfx/edit/title_logo.png` (rules in
  `src/BUILD.md`).
