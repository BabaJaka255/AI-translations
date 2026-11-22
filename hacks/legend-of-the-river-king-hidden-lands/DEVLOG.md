# Development log: Legend of the River King ~ In Search of Hidden Lands ~

How the English patch for *Kawa no Nushi Tsuri: Hikyou o Motomete* (PlayStation, 1998) was made, in order. All dates are 2026. "The tester" is the human who started the project, made the naming and art calls, and playtested; "Claude" is the AI that did the hacking and translation. Addresses are in [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md).

## Starting point (28 Oct)
The tester asked for an English patch of the PlayStation game, a remake of the Super Famicom *Kawa no Nushi Tsuri 2* with extras such as postcards. They supplied the disc image (single-track BIN/CUE, CRC32 `98CED29A`), a save with one fish already caught, and a BIOS for the emulator. No earlier translation was known. It followed the series glossary and the conventions of the earlier patches.

On decision cards the tester chose:
- an English title that reuses the River King logo with a redrawn subtitle, "~ In Search of Hidden Lands ~";
- an xdelta patch only, since the disc image is large.

## Phase 1: engine and v0.9
- **Text.** The script is stored as 16-bit glyph numbers in the main executable `SLPS_015.36`, not as Shift-JIS. The font is a picture inside `COMM.TIM`. Claude mapped the glyph numbers by drawing the font sheet.
- **English font.** A variable-width font is drawn by a hook in the glyph routine, with a paginator that wraps lines and turns pages by itself.
- **A real bug found early.** Claude's first hook broke because of the R3000's load-delay slot: a register was used the instruction after it was loaded. The hook was reordered.
- **Space.** English is longer than the Japanese, so the strings are packed with a small dictionary compression and relocated into free space.
- **Translation.** Claude translated all 2,490 strings.
- **Name entry** packs two letters into each slot, so names can be 8 letters. The postcard writing screen got an English keyboard.
- **Graphics.** The Fishing Note header, the 72 fish tags on the area maps and the logo subtitle were redrawn.

## Phase 2: playtest rounds
The tester played each build in Beetle PSX with a SCPH-5500 BIOS and sent screenshots.

**v0.9.1:**
- The tester asked for the unedited title graphic, and sent back their own edited title art, which the patch uses.
- Shop plaques became pictures: fish, hook, INN and EAT. EAT for the お plaque is Claude's guess at what that shop is.
- The tester reported that some text sat too far right. Claude couldn't reproduce it at first.

**v0.9.2:**
- The tester pointed out the problem was visible in Claude's own screenshots: "I'm using the same emulator as you". Claude then fixed the command menu, the keyboards and the gear window titles. "Longest" became "Best".

**v0.9.3:**
- The cause of the offsets was found: the Japanese full-width space is 8 pixels wide in this engine, not 16. All 18 Yes/No prompts were re-tabbed.
- The contest "Record" label was moved, and the gift command became "Give gift".

**v0.9.4:**
- The tester asked for natural, high-quality English, and for Claude to find problems before they did.
- A postcard bug was fixed: a pointer into the middle of a string had been broken by relocation.
- The Info labels and the Fishing Level pages were translated.
- Long boxes were re-paged, and about 35 lines were reworded.

## Phase 3: audit (v0.9.5, 30 Oct)
The tester was not satisfied with how the work was going and asked for it to be handed to a fresh thread for an audit. The second pass first rebuilt v0.9.4 byte for byte from the sources, so it started from a known state. Then:
- the staff roll and "The End" card were redrawn in English;
- 2 strings that were still in Japanese were fixed, and the build now stops with an error if any Japanese string is left;
- the paging was rewritten;
- about 110 lines were reworded;
- 4 fish cards and several cursor positions were fixed.

The inn, the shops and contest entry were checked on screen. The ending was not played.

## Phase 4: test helpers (v0.9.6)
The tester asked for cheats to speed up testing, and suggested かわ太郎 as a possible secret name. Claude searched the code and found the game's real secret name, つり太郎, which gives a full tackle box. It is typed as **FishTaro** in the English name entry. Along the way:
- name entry was fixed: a 7-letter cap and a delete key that removed two letters;
- an area warp was added for testing: hold SELECT while taking a step to go to the next area, SELECT + L1 to go back;
- the gear "R d" labels were fixed;
- 7 lines were reworded.

v0.9.6 is the current release.

## Phase 5: publishing (21-22 Nov)
Published here; then the source, docs and this log were added. The xdelta was rebuilt from this folder and matched byte for byte. Rebuilding needs the fonts the images were drawn with (Noto Sans Black, DejaVu and Liberation), and the title art file was renamed to `src/art/title_art.png`.

## How Claude worked
- **Tools it wrote:** a disc reader and sector writer with checksums (`tools/iso.py`, `tools/cdsector.py`), a MIPS disassembler built on capstone (`tools/mdis.py`), a Beetle PSX driver (`tools/emu.py`), the script dumper and inserter, layout audits that print every box line by line (`tools/audit_*.py`), and the image builders for the logo, plaques, maps and credits.
- **Checking its work:** screenshots from Beetle PSX, the layout checker for screens it couldn't reach, the build's check that no Japanese string is left, and rebuilding the patch from source.
- **What it couldn't do:** play to the ending, or see the misplaced text in its own screenshots until the tester pointed it out.

## Known gaps and ideas
- **The ending has never been seen in play.** Only the redrawn images and the layout tool were checked.
- **Credit names:** some are written in kanji with no reading, so the readings are best guesses.
- **Memory card title:** the save's title is still Japanese.
- **Postcard digits:** the digit row uses the Japanese digit style (page 3 has English digits).
- **The warp** is in the release build. It should be removed or hidden for a final version.
