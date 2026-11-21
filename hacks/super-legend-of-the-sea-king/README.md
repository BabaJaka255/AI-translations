# Super Legend of the Sea King
An English translation of *Umi no Nushi Tsuri* (Super Famicom, 1996, Pack-In-Video), the sea-going follow-up to *Kawa no Nushi Tsuri 2*. Pick a family member, fish along the coast and the islands, and hunt for the king of the sea. The patch covers:
* all dialogue, story scenes, fishing tips, Fish News and the five letters;
* all menus, shop and item names, bait, lures and gear;
* the Fishing Notes: contents, maps, captions and every fish entry;
* name entry and the Family Board, through English keyboards;
* graphics: the title logo, menu labels, status windows, town plaques, the fish market, the cup ranking board, envelopes, item icons and the Fish News masthead.

It is built on the same toolkit as [Super Legend of the River King](../super-legend-of-the-river-king/README.md) and uses the same glossary.

## Base game
- Platform: Super Famicom / SNES
- Required file: `Umi no Nushi Tsuri (Japan) (Rev 1).sfc` (No-Intro). Rev 0 is not supported.
- Size / header: 2,097,152 bytes (16 Mbit), no copier header
- CRC32: `C985F568` / SHA-1: `6f01bee87737de87e756f75b7b05e9cedb63faf6`
- Patched result: 4,194,304 bytes. CRC32: `35B3E1F3` / SHA-1: `17475c88f6db5695e4b20e1a9ebeae6f21ccdb29`

## How to apply
1. Get `patches/UmiNoNushiTsuri_EN_v1.1.ips`.
2. Apply it to a copy of the ROM with Flips (Floating IPS), Lunar IPS or Rom Patcher JS.
3. If your file is 2,097,664 bytes it has a 512-byte copier header. Remove the header first.

The patched ROM grows to 4 MB (32 Mbit).

Secret: name the older brother **BoatTaro** (the original ふね太郎) for 1000 yen and a fully stocked tackle box.

## Status and testing
Version 1.1.

- **Emulator:** the tester playtested every work-in-progress build in their emulator and reported issues with screenshots. With a separate area-warp test build (not part of this patch) they visited every zone and then declared v1.0 done.
- **v1.1** renames terms to match the series glossary (Title Case names, Yen, New Game, Arai/Bottarga). It was rebuilt and checked byte for byte, but has **not been playtested** as a whole.
- **Not played start to finish** in one run. **Not tested on real hardware.**

Known issues:
- Saves from the Japanese game or from older test builds can show garbled names. Start a new game or rename the characters.
- Long fish names are kept to 14 letters, and the fish market's daily special uses short forms for names over 12 letters.
- Empty gear slots are blank, as in the Japanese game.

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering, all of the ROM-hacking code (English text mode, keyboards, graphics replacement), and the whole translation.

The human tester directed the project, chose the names and English titles, playtested the builds in emulators and reported bugs with screenshots, and drew the title logo.

## Credits
- Testing, direction and title logo art: the project's tester
- Translation and ROM hacking: Claude (Anthropic)
- Original game: *Umi no Nushi Tsuri* © 1996 Pack-In-Video. This is an unofficial fan translation. Please distribute the patch, not patched ROMs.

## Changelog
- **1.1:** Names and terms match the Super Legend of the River King glossary (v1.3): Title Case fish, bait, gear and item names, Yen, New Game / Erase Data, Arai, Bottarga and Kabayaki. Sea Louse is now Sea Slater and the Olive Sinker is the Date Sinker.
- **1.0:** First release.
