# Legend of the River King 3 ~ From the Mysterious Forest ~
An English translation of *Kawa no Nushi Tsuri 5: Fushigi no Mori kara* (Game Boy Advance, 2001, Victor Interactive Software). Keita follows a talking squirrel into the Mysterious Forest and fishes through five lands to save people turned into fish. The patch translates all 1,548 lines of dialogue, all menus, every item and fish name and description, the save screens, the staff roll, name entry, the EQUIP tag and the Fishing Note map labels. The title screen reads "Legend of the River King 3" with the subtitle "From the Mysterious Forest". Money stays G, as in the original.

## Base game
- Platform: Game Boy Advance
- Required file: `Kawa no Nushi Tsuri 5 - Fushigi no Mori kara (Japan).gba` (No-Intro)
- Size / header: 4,194,304 bytes (32 Mbit), no header
- CRC32: `4A8F2F62` / SHA-1: `418d61ddd992ceeaa10a102deaf9eb15a2fb7328`
- Patched result: 8,388,608 bytes. CRC32: `D0293080` / SHA-1: `7759e2811f34b9640e14fb93509313aa3be54311`

## How to apply
Patch a copy of the ROM with **one** of:
- `patches/KawaNoNushiTsuri5_EN_v0.9.2.xdelta` (xdelta3, Delta Patcher or Rom Patcher JS)
- `patches/KawaNoNushiTsuri5_EN_v0.9.2.ips` (Flips or Lunar IPS)

The patched ROM grows to 8 MB; the English text lives in the added half. Saves from the Japanese version keep working.

## Status and testing
Version 0.9.2 (test release).

- **Emulator:** the tester playtested v0.9.2 in their emulator and found no further issues. Claude checked screens in mGBA (libretro) with the tester's save.
- **Not played start to finish** in one run. **Not tested on real hardware.**

Known issues:
- Staff names are romanised from the Japanese credits; a few readings are best guesses.
- Save states from older versions can show old text already in memory.

## Build on this
- [src/BUILD.md](src/BUILD.md): how to rebuild the patch from your own copy of the game. The build was verified byte for byte against the published patches.
- [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md): how the game stores its text, fonts and graphics, with addresses and hooks.
- `src/script/` (`dialogue.tsv`, `ui.tsv`): the whole script, Japanese next to English, one row per string.
- [DEVLOG.md](DEVLOG.md): how the patch was made, what was tested, and what went wrong along the way.

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering, all of the ROM-hacking code (expanded ROM, text and name hooks, logo and tag graphics), and the whole translation.

The human tester directed the project, chose the names and English titles, playtested the builds in emulators and reported bugs with screenshots, and designed the title logo.

## License
Code, tools and docs made for this project: MIT. Translation text and new art: CC BY 4.0. Extracted game material (the Japanese script dumps, tables and graphics in `src/`) remains the property of its rights holders and is included for research and modding.

The New Game / Continue letter masks in `src/art/` were rendered from Noto Sans Condensed Bold (SIL Open Font License 1.1).

## Credits
- Testing, direction and title logo design: the project's tester
- Translation and hacking: Claude (Anthropic)
- Original game: *Kawa no Nushi Tsuri 5: Fushigi no Mori kara* © 2001 Victor Interactive Software. This is an unofficial fan translation. Please distribute the patch, not patched ROMs.
- Fonts: Noto Sans Condensed Bold (menu letters)
- Tools: mGBA (libretro) for testing; Unicorn, Keystone and Capstone; xdelta3

## Changelog
- **0.9.2:** Wide m/M; EQUIP tag; English place names on the six Fishing Note maps.
- **0.9.1:** English title logo and subtitle; New Game / Continue; ellipses; "Done" on the Fishing Note.
- **0.9:** First test release.
