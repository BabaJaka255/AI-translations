# Tsuri Tarou (English)
An English translation of *Tsuri Tarou* (Super Famicom), a river-fishing game. The patch translates the title and file select, the name and date entry (with an English letter keyboard), the opening and end-of-day story pages, the map labels, all 15 fishing-spot signs, the SELECT fish list and records screen, and the Erase Data prompt. Names follow the same glossary as the *Super Legend of the River King* patch (River King, Masu Trout, White Crucian). The original Japanese title logo is kept on purpose.

## Base game
- Platform: Super Famicom / SNES
- Required file: `Tsuri Tarou (Japan).sfc` (No-Intro)
- Size / header: 1,048,576 bytes (8 Mbit), no copier header
- CRC32: `BBBFF8D8` / SHA-1: `4cb107cbef4fa5907ed0f2123de7a475bad7aa34`
- Patched result: 2,097,152 bytes. CRC32: `7CF11509` / SHA-1: `09d63e18d2b6d7d250769f126450b9ca9c76147b`

## How to apply
1. Get `patches/TsuriTarou_EN_v0.9.1.ips`.
2. Apply it to a copy of the ROM with Flips (Floating IPS), Lunar IPS or Rom Patcher JS.
3. If your file is 1,049,088 bytes it has a 512-byte copier header. Remove the header first.

The patched ROM grows to 2 MB (16 Mbit).

## Status and testing
Version 0.9.1 (test release).

- **Emulator:** the tester played v0.9 in their emulator and reported no problems. Claude checked the signs, the opening page and the menus in snes9x (stable-retro).
- **v0.9.1** only renames terms to match the series glossary (spot signs 2, 4 and 15, the fish list, story pages). It has **not been playtested** yet.
- **Not seen running:** the Erase Data confirmation and the ending page were only rendered from the game's tile data, never reached live.
- **Not tested on real hardware.**

Known issues:
- Story pages can't show the digit 0 (that tile is the blank on those screens). The current text doesn't need it.
- The 8x8 font raises the tails of g, j, p, q and y, so they can look a little like 9.
- The records screen draws the fish name with a very short screen blank. A one-frame flicker there is possible.

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering of the text and graphics engine, all of the ROM-hacking code (relocated text, English keyboard, 8x16 sign letters), and the whole translation.

The human tester directed the project, chose the names and English titles, playtested the builds in emulators and reported bugs with screenshots.

## Credits
- Testing and direction: the project's tester
- Translation and ROM hacking: Claude (Anthropic)
- Original game: *Tsuri Tarou* (Super Famicom). This is an unofficial fan translation. Please distribute the patch, not patched ROMs.

## Changelog
- **0.9.1:** Terms follow the series glossary: River King, Masu Trout, White Crucian (W.Crucian in the fish list), paste bait, "Got" on the records screen, and the hero is Taro.
- **0.9:** First test release.
