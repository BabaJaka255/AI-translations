# Legend of the River King ~ In Search of Hidden Lands ~
An English translation of *Kawa no Nushi Tsuri: Hikyou o Motomete* (PlayStation, 1998, Victor Interactive Software / Pack-In-Soft), a remake of *Kawa no Nushi Tsuri 2*. The patch translates all 2,490 script lines in a new variable-width English font, all menus, every fish, item and gear name and description, the Fishing Note, name entry and postcard writing (English keyboards), and the graphics: the staff roll and "The End" card, the title logo and subtitle, the shop plaques, the Fishing Note header and the 72 fish tags on the area maps.

Test helpers: name Bro **FishTaro** for a full tackle box (the game's own cheat), and hold SELECT while taking a step to warp to the next area (SELECT + L1 goes back). The warp was added by this patch for testing; keep a separate save for real play.

## Base game
- Platform: Sony PlayStation (NTSC-J, SLPS-01536)
- Required file: `Kawa no Nushi-tsuri - Hikyou o Motomete (Japan).bin`, single-track BIN/CUE
- Size / header: 85,412,880 bytes, no header
- CRC32: `98CED29A` / SHA-1: `915522f856709f07b3952a4588a3550729466e6b`
- Patched result: 85,412,880 bytes. CRC32: `9CA3F94C` / SHA-1: `40dba261e4b54dc72f20d4ac8fef47b4f7e1510a`

## How to apply
1. Patch a copy of the .bin with `patches/KawaNoNushiTsuriHikyou_EN_v0.9.6.xdelta` using xdelta3, Delta Patcher or Rom Patcher JS.
2. Keep the original .cue. If you rename the .bin, change the FILE line in the .cue to match.

The patched .bin is the same size.

## Status and testing
Version 0.9.6 (test release).

- **Emulator:** tested in Beetle PSX (Mednafen) with a SCPH-5500 BIOS. Checked on screen: title, file select, status and command menus, all item windows, the Fishing Note and maps, village dialogue and plaques, name entry and postcards, the family intros, the inn, every shop category and contest entry. Existing Japanese saves load.
- **Not played on screen:** the end-game scenes and the ending. They were checked with a layout tool and the redrawn staff roll images only.
- **Not tested on real hardware.**

Known issues:
- Some credit names are written in kanji with no reading given; these readings are best guesses.
- The memory card save title is still Japanese.
- Digits typed on the postcard digit row use the original Japanese digit style (page 3 has English digits).

## Build on this
- [src/BUILD.md](src/BUILD.md): how to rebuild the patch from your own copy of the game. The build was verified byte for byte against the published patch.
- [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md): how the game stores its text, fonts and graphics, with addresses and hooks.
- `src/script/script.tsv`: the whole script, Japanese next to English, one row per string.
- [DEVLOG.md](DEVLOG.md): how the patch was made, what was tested, and what went wrong along the way.

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering of the MIPS code and text format, all of the hacking code (variable-width font, paginator, keyboards, area warp, image redraws), and the whole translation.

The human tester directed the project, chose the names and English titles, playtested the builds in emulators and reported bugs with screenshots in Beetle PSX, and drew the title screen art.

## License
Code, tools and docs made for this project: MIT. Translation text and new art: CC BY 4.0. Extracted game material (the Japanese script dumps, tables and graphics in `src/`) remains the property of its rights holders and is included for research and modding.

The English font and new images are rendered at build time from DejaVu Sans Bold (Bitstream Vera license), Noto Sans Black and Liberation Sans (SIL Open Font License 1.1); the fonts themselves are not included.

## Credits
- Testing, direction and title screen art: the project's tester
- Translation, hacking and graphics: Claude (Anthropic)
- Original game: *Kawa no Nushi Tsuri: Hikyou o Motomete* © 1998 Victor Interactive Software / Pack-In-Soft. This is an unofficial fan translation. Please distribute the patch, not patched images.
- Fonts: DejaVu Sans Bold (the English text font), Noto Sans Black, Liberation Sans
- Tools: Beetle PSX (libretro) for testing; Keystone and Capstone; xdelta3

## Changelog
- **0.9.6:** FishTaro secret name works; SELECT + step area warp; 8-letter names; gear window empty-slot labels fixed; seven lines reworded.
- **0.9.5:** Staff roll and "The End" in English; two missed lines translated; dialogue paging rewritten; about 110 lines reworded; fish card and menu fixes.
- **0.9.4:** Family intro postcards fixed; dialogue re-paged; menus re-aligned; last untranslated labels done.
- **0.9.3:** Yes/No alignment; contest board; "Give gift".
- **0.9.2:** Menu and keyboard alignment.
- **0.9.1:** Title screen art; shop plaques as pictures.
- **0.9:** First test release.
