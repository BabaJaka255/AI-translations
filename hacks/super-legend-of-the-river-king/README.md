# Super Legend of the River King
A complete English translation of *Kawa no Nushi Tsuri 2* (Super Famicom, 1995, Pack-In-Video). In this fishing RPG you pick one of four family members and travel down a river, from mountain streams to the sea, to catch the legendary River King. The patch translates:
* all dialogue, story scenes, letters, postcards and endings;
* menus, item and gear names, and the Fishing Note;
* name entry and postcards, through new English keyboards;
* graphics: the title logo, town signs, the shop banner, map labels and item icons.

Fish use their common English names. The title and the "River King" terminology follow the Game Boy *Legend of the River King* games.

## Base game
- Platform: Super Famicom / SNES
- Required file: `Kawa no Nushi Tsuri 2 (Japan).sfc` (No-Intro)
- Size / header: 1,572,864 bytes (12 Mbit), no copier header
- CRC32: `716D3EFF` / SHA-1: `c2103dd94e2a1a65a495fc02adc2e7d040f31212`
- Patched result: 2,097,152 bytes (expanded to 16 Mbit)
  - CRC32: `8F2E0D10`
  - SHA-1: `e8c94a106e9aafb5d85cb67b2b6266a474f31c47`

## How to apply
1. Get `patches/KawaNoNushiTsuri2_EN_v1.3.ips`. It's also inside `patches/SuperLegendOfTheRiverKing_v1.3.zip`, along with the player README.
2. Apply it to a **copy** of the ROM with Flips (Floating IPS), Lunar IPS or Rom Patcher JS.
3. If your file is 1,573,376 bytes, it has a 512-byte copier header. Remove the header first.

Secret: naming the older brother **FishTaro** unlocks the original game's stocked tackle box (つり太郎 in Japanese).

## Status and testing
Version 1.3.

**Tested in an emulator only.** The tester played every build in Mesen-S.
- They checked each changed screen with screenshots and memory dumps.
- They used the game's area-warp code to sweep every area for leftover Japanese.

**Not tested:**
- **Real hardware:** it has not been run on a real SNES or a flash cart.
- **A full playthrough:** the game hasn't been played from start to finish in one run. Every text box was rendered with the game's own code in a simulator to catch overflow.
- **The v1.3 gear-slot labels:** checked in the graphics data, not yet confirmed in the emulator.

**Known issues:**
- Saves from the Japanese game show old names as garbled letters. Start a new game or rename the characters.
- Some long fish names are shortened on the Fishing Note map (9 letters) and in the fishery window (13).
- One hook keeps its Japanese name ("Shibi"), and the 〒 postal mark stays on postcards.

## Build on this
- **[`src/BUILD.md`](src/BUILD.md)** rebuilds this exact patch from a clean ROM with one command (`python3 build/build_patch2.py`). The build was **verified byte for byte** against the published IPS from a fresh copy of this folder.
- **[`src/script/`](src/script/)** has the whole script as plain CSV/JSON: one row per string, with location, Japanese, English, limits and notes. It also has the name list, the Fishing Note text, and the spreadsheet round-trip tool.
- **[`docs/ENGINE_NOTES.md`](docs/ENGINE_NOTES.md)** covers the ROM map, text encoding, LZSS format, every hook and free-space address, the RAM variables, where each graphic lives, and the methods that worked for finding things.
- **[`docs/glossary.html`](docs/glossary.html)** (and `.csv`/`.xlsx`) is a searchable Japanese→English list of every fish, creature, item, place and term.
- **[`DEVLOG.md`](DEVLOG.md)** records how it was made, version by version: dead ends, the bugs the tester found, and who decided what.

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude:
- reverse-engineered the ROM: text encoding, kanji table, pointer tables, LZSS compression and graphics locations;
- wrote all the tools and patch code, including a 65816 disassembler, an interpreter used as a text simulator, the English keyboards, text relocation and the graphics replacement;
- wrote the first-draft translation of the whole script and all the generated art except the title logo.

A human tester:
- directed the project and tested every build in Mesen-S;
- supplied the screenshots and VRAM/WRAM dumps that located the graphics;
- made the naming decisions, including "River King" and the title;
- found the warp code, the secret name and the remaining Japanese;
- edited the script through the workbook (43 edits);
- drew the title logo.

## License
Code, tools and docs made for this project: MIT. Translation text and new art: CC BY 4.0. Extracted game material (the Japanese script, tables, graphics sheets and RAM dumps) remains the property of its rights holders and is included for research and modding.

Bundled fonts keep their own licences:
- X11 `koi8x16` and `koi5x8`: freely redistributable / public domain.
- DejaVu Sans Bold: Bitstream Vera licence, included in `src/gfx/fonts/source/`.

## Credits
- **Testing, direction, script edits and title logo:** the project's tester
- **Translation, reverse engineering and ROM hacking:** Claude (Anthropic)
- **Fonts:** X11 `koi8x16` and `koi5x8` bitmap fonts (xfonts-cyrillic); DejaVu Sans
- **Kanji identification:** done against Noto Sans CJK JP (not included)
- **Testing emulator:** Mesen-S
- **Original game:** *Kawa no Nushi Tsuri 2* © 1995 Pack-In-Video / Yuu Yuu. This is an unofficial fan translation. Please distribute the patch, not patched ROMs.

## Changelog
- **1.3:** Empty gear slots in the tackle window read ROD, FLOAT, SINKER, HOOK and NONE.
- **1.2:** The secret name works with the English keyboard (FishTaro). One villager line reworded.
- **1.1:** Script revision by the tester (speaker names, a fuller opening, reworded contest and save messages). The ending letters now fit their postcard frame.
- **1.0:** First release.
- **Repository update (2026-11-22):** added the full source, the script as CSV/JSON, the tables, graphics, dumps, the engine notes, the glossary and the development log. The patch is unchanged.
