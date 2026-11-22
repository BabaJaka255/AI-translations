# Development log: Legend of the River King CD

How the English patch for *Kawa no Nushi Tsuri: Shizen-ha* (PC Engine CD-ROM2, 1992) was made, in order. All dates are 2026. "The tester" is the human who started the project, made the naming and art calls, and playtested; "Claude" is the AI that did the hacking and translation. Addresses are in [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md).

## Starting point (27 Oct)
After two Super Famicom patches in the series, the tester asked for "something new": the same franchise on "an entirely different platform", the PC Engine CD. Claude didn't recognise the title, so it asked for the exact game rather than guess. The tester named it: a remake of the Famicom original "with enhanced graphics, sound effects, and CD-quality music". They supplied the .cue and the Track 02 data .bin; tracks 3 to 30 are audio and weren't needed. The tester said to use System Card 3.0, "the bios my emulator seems to be using", and supplied it on request. No earlier translation was known.

## Phase 1: disc and engine
- **Disc tools.** Claude wrote helpers for the disc: cooked sector reads, the Mode 1 EDC/ECC rewrite (`tools/cdsector.py`), a HuC6280 disassembler and assembler, and a small CPU model.
- **Emulator.** Testing ran in Beetle PCE (libretro) on a test disc made from the real data track plus silent audio tracks (`tools/make_disc.py`).
- **Text format.** Text is little-endian Shift-JIS words ending in `0000`, drawn with the System Card's own 16x16 kanji font (EX_GETFNT). All data is stored twice on the disc, the second copy 1,478 sectors later, so every change is written to both.
- **Where the font goes.** The game's memory was nearly full. The easy home for an English font was the extra RAM that only System Card 3.0 has. Claude put this to the tester on a decision card, recommending 3.0, and the tester chose **"Require System Card 3.0"**. The font lives in bank `$68`.
- **The font.** An 8x16 font based on the X11 `koi8x16` font. Each 16-pixel kanji cell holds two letters, so a line fits 24 letters instead of 12.

## Phase 2: script and v0.9
- **Dump:** 516 strings (`tools/dump_script.py`).
- **Dialogue:** Claude translated the 284 dialogue strings (`tools/tr_main.py`, keyed by the Japanese). They fit the original boxes without layout changes.
- **Menus:** menus and status windows use a separate glyph list (`tools/tr_menus.py`). The title menu (Start / Resume / Guide) is sprites (`tools/title_sprites.py`).
- **Other text:** the backup-memory messages, and the fish guide with its names, labels and cooking notes (`tools/fish_guide.py`).
- **v0.9 test release:** the title logo was left in Japanese at first. The Item window, the ending and every guide page had not been seen.

## Phase 3: first playtest (v0.9.1)
The tester reported four problems:
- **Empty battle menu.** The three labels Fight / Eat / Run were in the patch's menu data, but Claude had taken them for unused placeholders and blanked them.
- **Caught fish in Japanese.** They come from a separate name list (`tools/catch_names.py`), which is now translated. The space before " landed!" was being dropped too.
- **Empty Specs box.** Traced: the game never prints text there. It is the same in Japanese, so it was left alone.
- **Signs and banner.** Redrawn: INN, ROD, a fish picture, DANGO. The plaques only hold 3 letters.

The tester confirmed: "These are all fixed!"

## Phase 4: consistency (v0.9.2)
The tester asked for "a pass over the script for consistency and sensible localization" across all the series patches. Claude:
- started a shared glossary ([docs/series_glossary.md](docs/series_glossary.md)), matching fish names and cooking terms to the Umi and Tsuri Tarou patches;
- fixed punctuation in short messages;
- kept Magnet / Sparks / Cake / Spud / Mint, because the item and food windows only hold 4 to 6 letters.

## Phase 5: title logo (v0.9.3, v0.9.4)
- **v0.9.3.** On a decision card the tester chose the title **"Legend of the River King CD"**. Claude drew a logo in the Sea King style, inside the 44 sprites the original logo used (`tools/logo.py`).
- **v0.9.4.** The tester then supplied their own mock-up ("See if you can't get this to fit on the title screen"). Claude scaled it to 200x60 in 43 sprites with 13 colours. The flame gradient bands a little, and the white outline blends into the clouds in places. The tester: "I think that's good!"

## Phase 6: English names and Umi-style signs (v0.9.5)
The tester asked:
- to "emphasize English names for fish and terminology where possible";
- for the signs to match the Umi patch;
- for a picture of a dango on the banner instead of the word.

Claude:
- reused Umi's plaque art (INN, hook, fish) (`tools/signs.py`);
- drew a three-ball dango skewer. The banner palette has no pink, so tan stands in for the pink ball;
- renamed romanised fish to English (Cherry trout, Ricefish, Amur stickleback...). Tanuki became "Raccoon", since "raccoon dog" doesn't fit 9 letters.

The thread ran out of attachment slots here and continued in a new one.

## Phase 7: series glossary (v0.9.6, 27 Oct)
The tester then supplied their *Super Legend of the River King* v1.3 glossary and asked that every patch follow it. That superseded part of v0.9.5:
- Title Case glossary names: Masu Trout, Redspot Trout, Stone Moroko, Itomoroko, Pike Gudgeon...
- **Tanuki** came back, reversing the earlier Raccoon change.
- Mt. Bat, Deer and Macaque.
- Arai, Kabayaki and Bottarga in the cooking notes; paste bait.

A rebuild of the v0.9.5 sources reproduced v0.9.5 exactly before the change, so the build is reproducible. **v0.9.6 has not been fully playtested.**

## Phase 8: publishing (21-22 Nov)
Published here; then the source, docs and this log were added. Both the IPS and the xdelta were rebuilt from this folder and matched byte for byte.

## How Claude worked
- **Wrote all the tooling:** the CPU model, the disassembler and assembler, the sector checksum code, the script dumper and checker, and the template, BAT and sprite renderers.
- **Checked its work:** screenshots from a fresh boot in Beetle PCE, and rebuilding the patch from source.
- **What it couldn't do itself:** get into fights or land catches quickly, play to the ending, or judge the art. The tester covered the fights and catches.

## Known gaps and ideas
- **The ending has never been seen on screen.**
- **System Card 1.0/2.0 is not supported.** It would need a smaller, compressed font in base memory.
- **Short menu words:** some stay short because the slots are tiny (Item window 6 letters, food window 4).
