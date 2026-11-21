# Super Legend of the River King
An English translation of *Kawa no Nushi Tsuri 2* (Super Famicom, 1995, Pack-In-Video), a fishing RPG in which one of four family members travels down a river to catch the legendary River King. The patch covers:
* all dialogue, story scenes, letters, postcards and endings;
* menus, item and gear names, and the Fishing Note;
* name entry and postcards, through new English keyboards;
* graphics: the title logo, town signs, shop banners, map labels and icons.

Fish use their common English names. Terminology follows the Game Boy *Legend of the River King* games.

## Base game
- Platform: Super Famicom / SNES
- Required file: `Kawa no Nushi Tsuri 2 (Japan).sfc` (No-Intro)
- Size / header: 1,572,864 bytes (12 Mbit), no copier header
- CRC32: `716D3EFF` / SHA-1: `c2103dd94e2a1a65a495fc02adc2e7d040f31212`
- Patched result: 2,097,152 bytes (expanded to 16 Mbit). CRC32: `8F2E0D10` / SHA-1: `e8c94a106e9aafb5d85cb67b2b6266a474f31c47`

## How to apply
1. Get `patches/KawaNoNushiTsuri2_EN_v1.3.ips`. It is also inside `patches/SuperLegendOfTheRiverKing_v1.3.zip`, along with the player README.
2. Apply it to a copy of the ROM with Flips (Floating IPS), Lunar IPS or Rom Patcher JS.
3. If your file is 1,573,376 bytes, it has a 512-byte copier header. Remove the header first, or the patch will corrupt the game.

To use the hidden stocked-tackle-box name from the original game, name the older brother **FishTaro**.

## Status and testing
Version 1.3.

- **Emulator:** the tester played the game in Mesen-S through each version. They reached every area with the game's built-in area-warp code, and checked the menus, keyboards, signs and map. Each change was then verified from screenshots and RAM/VRAM dumps.
- **Not tested on real hardware or a flash cart.**
- **Not played start to finish:** the full game and every ending were not played through in one run. Every text box was checked in a simulator that runs the game's own text code, so line overflow should be caught.
- **v1.3 change (empty gear-slot labels):** checked in the graphics data only, not yet seen in the emulator.

Known issues:
- Saves from the Japanese game can show old names as garbled letters. Start a new game or rename the characters.
- Some long fish names are shortened on the Fishing Note map (9 letters) and in the fishery price window (13).

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did:
- the reverse engineering of the text engine, compression and graphics;
- all of the ROM-hacking code, including the English keyboards, text relocation and graphics replacement;
- the first-draft translation of the whole script.

The human tester:
- directed the project and tested every build in Mesen-S;
- captured the screenshots and RAM/VRAM dumps used to find graphics;
- found the area-warp code and the hidden name;
- revised the script through the editing workbook;
- drew the title logo.

## Credits
- Testing, direction, script edits and title logo: the project's tester
- Translation and ROM hacking: Claude (Anthropic)
- Fonts: X11 `koi8x16` and `koi5x8` (public domain), DejaVu Sans
- Original game: *Kawa no Nushi Tsuri 2* © 1995 Pack-In-Video / Yuu Yuu. This is an unofficial fan translation. Please distribute the patch, not patched ROMs.

The full build, tools and engine notes are in [`src/`](src/README.md).

## Changelog
- **1.3:** Empty gear slots in the tackle window read ROD, FLOAT, SINKER, HOOK and NONE.
- **1.2:** The secret name works with the English keyboard (FishTaro). One villager line reworded.
- **1.1:** Script revision by the tester: speaker names, a fuller opening, and reworded contest and save messages. The ending letters now fit their postcard frame.
- **1.0:** First release.
