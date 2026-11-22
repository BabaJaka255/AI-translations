# Legend of the River King Advance Collection
An English translation of *Kawa no Nushi Tsuri 3 & 4* (Game Boy Advance, 2003, Marvelous Interactive), two River King games on one cartridge. Both games are translated: all dialogue, signposts and story scenes (about 400 lines in game 3 and 1,000 in game 4), title menus and file panels, an English name-entry page, all menus, shop windows, the memo books, the Uocchi fish-raising screens, and the building signboards (drawn as pictures). English title logos read "Legend of the River King Advance Collection", "Legend of the River King GBC" (game 3) and "Legend of the River King 2" (game 4). Names follow the series glossary.

## Base game
- Platform: Game Boy Advance
- Required file: `Kawa no Nushi Tsuri 3 & 4 (Japan).gba` (No-Intro)
- Size / header: 4,194,304 bytes (32 Mbit), no header
- CRC32: `4F09CA00` / SHA-1: `043ccd64f04fff2cd2f19ba679dc3c7a1250b97c`
- Patched result: 4,194,304 bytes. CRC32: `24573A7E` / SHA-1: `38aa069a368cd714b595eeef3ecaa080402a4536`

## How to apply
Patch a copy of the ROM with **one** of:
- `patches/KawaNoNushiTsuri3and4_EN_v1.0.xdelta` (xdelta3, Delta Patcher or Rom Patcher JS)
- `patches/KawaNoNushiTsuri3and4_EN_v1.0.ips` (Flips or Lunar IPS)

The patched ROM stays 4 MB. Load from an in-game save, not an old save state.

## Status and testing
Version 1.0.

- **Emulator:** the tester playtested v0.5 to v0.9 in their emulator and reported bugs, which were fixed. Claude checked screens in a small home-made GBA emulator built for this project, which is less accurate than mGBA.
- **v1.0** is a script pass (about 75 lines reworded, page breaks at sentence ends). A few panels were checked in game; the full game has **not been replayed** on v1.0.
- **Not tested:** saves made with the Japanese version. **Not tested on real hardware.**

Known issues:
- None known. Game 4 has rumble-setting graphics (しんどう ON/OFF) that never appear on screen and are left alone.

## Build on this
- [src/BUILD.md](src/BUILD.md): how to rebuild the patch from your own copy of the game. The build was verified byte for byte against the published patches.
- [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md): how the game stores its text, fonts and graphics, with addresses and hooks.
- `src/script/` (`kawa3.tsv`, `kawa4.tsv`): the whole script, Japanese next to English, one row per string.
- [DEVLOG.md](DEVLOG.md): how the patch was made, what was tested, and what went wrong along the way.

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering, all of the ROM-hacking code (a variable-width font hook, rebuilt menu tile streams, the title sprite engine change, graphics replacement), and the whole translation.

The human tester directed the project, chose the names and English titles, playtested the builds in emulators and reported bugs with screenshots, and drew the three title logos.

## License
Code, tools and docs made for this project: MIT. Translation text and new art: CC BY 4.0. Extracted game material (the Japanese script dumps, tables and graphics in `src/`) remains the property of its rights holders and is included for research and modding.

## Credits
- Testing, direction and logo art: the project's tester
- Translation and hacking: Claude (Anthropic)
- Original game: *Kawa no Nushi Tsuri 3 & 4* © 2003 Marvelous Interactive. This is an unofficial fan translation. Please distribute the patch, not patched ROMs.
- Tools: Unicorn, Keystone and Capstone (CPU emulation, assembly, disassembly); xdelta3

## Changelog
- **1.0:** Script pass over both games, matched item names, Max HP, page breaks at sentence ends.
- **0.95:** English title logos on the start, game select and title screens.
- **0.9:** Fish shop prompt fix; game 4 memo book graphics.
- **0.8:** Building signboards drawn as pictures.
- **0.7:** Playtest fixes (Uocchi help, game 3 tackle shop, prices, game 4 shop titles and Go command); fish price boards and Catalog.
- **0.6:** Playtest fixes; Uocchi screens, Fishing Memo, window headers, lure and fly lists.
- **0.5:** First test release.
