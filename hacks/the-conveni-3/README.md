# The Conveni 3: Corner the Market!
An English translation of *The Conveni 3: Ano Machi o Dokusen seyo* (ザ・コンビニ3 ～あの町を独占せよ～, Hamster, PS2), a convenience-store business sim. All menus, the tutorial, the advisor angel, staff, events, scenario text and the map tickers are in English, plus the menu buttons, headers, memory card labels and the title screen subtitle. Money shows in yen with commas (¥230,000,000). Real chain names (LAWSON and others) are kept, and "conveni" is kept as the word for the stores (explained once in the tutorial).

## Base game
- Platform: PlayStation 2 (CD, SLPM-62322)
- Required file: `Conveni 3, The - Ano Machi o Dokusen seyo (Japan).bin` (Redump), or a 2048-byte-sector ISO made from it
- Size / header: bin 750,753,696 bytes (MODE2/2352); ISO 653,717,504 bytes
- Redump bin CRC32: `2143FE1F` / SHA-1: `597f58e9bef568d7ab07273210c625fd0252386d`
- ISO CRC32: `E2F31095` / SHA-1: `4fa209d0a691238593adcd4738096c5bd7c5fdcd`
- Patched result (both patches give the same ISO): 656,054,272 bytes. CRC32: `A3BAF439` / SHA-1: `cd45eacc2a16f2f502c7b19bac4e5984e41a133c`

## How to apply
Pick the patch that matches your image:
- `patches/Conveni3_EN_v0.9.6-beta_RedumpBin.xdelta` for the Redump .bin
- `patches/Conveni3_EN_v0.9.6-beta_ISO.xdelta` for an ISO made from that bin

Use xdelta UI, Delta Patcher, or the command line:
```
xdelta3 -d -B 1073741824 -s "<your image>" "<patch>.xdelta" "Conveni3-EN.iso"
```
`-B` lets xdelta read the whole source image; GUI patchers handle this themselves. Play the resulting .iso in PCSX2 or with your usual loader.

## Status and testing
Version 0.9.6 **beta**.

- **Emulator:** tested in PCSX2: boot, title, tutorial, menus, store setup, map, Store Status, tickers, clerk and fixture panels. Every text slot is checked by the build for length and missing glyphs.
- **Playtests:** the project lead played the betas in an emulator and sent three rounds of feedback, which led to v0.9.1 to v0.9.6. **Not tested on real hardware.**
- The Clerk Info changes in v0.9.5 and v0.9.6 were checked in the built files but not seen on screen.
- **Not every random event popup was seen in play.**
- Both patches were re-applied to clean images before publishing and give the result hashes above.

Known issues:
- The clock uses the Japanese 12-hour style (PM 0:25 = 12:25 PM).
- Signs and posters drawn inside event pictures stay in Japanese, as does the ザ・コンビニ 3 logo.
- Some long staff names are shortened (for example "Family G.") to fit the staff panels.
- A few of the angel's tips that show as two short bubbles still move on by themselves.

## Build on this
Full source is in [`src/`](src/BUILD.md): the build and insertion tools, the `rhtk` toolkit, the script (Japanese and English, one entry per string, edited through TSV files), texture edits and the font used for the speech-bubble letters. One command builds the English ISO from your own disc. The build was **verified byte for byte**: a fresh copy rebuilt the same patched ISO, and the ISO patch re-encoded identically. Formats, code changes, addresses and box sizes are in [`docs/ENGINE_NOTES.md`](docs/ENGINE_NOTES.md), the glossary in [`docs/`](docs/), screenshots and text previews in [`docs/images/`](docs/images/), and how it was made in [`DEVLOG.md`](DEVLOG.md).

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering (archives, compression, file checksums, fonts), the code and data changes (letter-pair glyphs, word wrap, yen formatting, redrawn textures and fonts), and the translation of the script. The human project lead chose the game, supplied their own disc image, approved the glossary and title, played the betas and reported what needed fixing.

## License
Code, tools and docs made for this project: MIT. Translation text and new art: CC BY 4.0. Inter (in `src/tools/fonts/`) is under the SIL Open Font License 1.1, included next to it. Extracted game material (original script, screenshots) remains the property of its rights holders and is included for research and modding.

## Credits
- Direction, glossary approval and playtesting: the project lead
- Translation and hacking: Claude (Anthropic)
- Tools: PCSX2, xdelta3
- Speech-bubble Latin letters drawn from Inter (SIL Open Font License)
- Original game: *The Conveni 3* © Hamster / Masterpiece. This is an unofficial fan translation. Please share the patch, not the game.

## Changelog
- **0.9.6 beta:** Clerk career lines read "Moved to #2" and "Moved to Main (buyout)"; the Japanese ditto mark (〃) is gone.
- **0.9.5 beta:** Clerk Info age line is "22, M" so it fits; career line reads "Joined your Main".
- **0.9.4 beta:** Fixture details break between words; fixture names fixed; Edit Interior prices with commas; "Can't place" stamp; event tips wait for a button; scenario goals rewritten; encyclopedia answers rewrapped.
- **0.9.3 beta:** Tutorial bubbles rewrapped with a safer margin; map marker "1"; 4-store view tabs; "#2" style store names; "Cap"/"Pull" in Fixture Info; help bubbles pre-wrapped.
- **0.9.2 beta:** Main store map marker reads "Main".
- **0.9.1 beta:** Smoother speech-bubble lettering; tutorial wraps per bubble; owner name screen banner; 12 staff names shortened.
- **0.9 beta:** First public beta.
