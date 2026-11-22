# Hamster Club
An English translation of *Hamster Club* (ハムスター倶楽部, Jorudan, 1999), a hamster-raising sim for the Game Boy Color. The patch covers:
* the whole story and event script (465 messages), with an English font;
* English name entry for you, your hamsters and your cages, with a choice of honorific (-san, -kun, -chan or none) that the shop staff use;
* all menus and care screens: home menu, status, stats, lineage, tricks, habits, items, food, cages, schedule, weekly report and the save prompt;
* all eight contests: announcers, rival names, title banners, help screens, judges' scores and results boards;
* artwork lettering redrawn in English: the title logo, boot and copyright screens, event banners and the sound effects in 60 trick animations.

Japanese honorifics are kept on purpose. The game caps names at 8 letters, so a few long names are shortened (for example ジョセフィーヌ is "Josefine").

## Base game
- Platform: Game Boy Color (GB/GBC dual mode)
- Required file: Hamster Club (Japan), header title `HAMSTERCLUBAJNJ`. Not yet compared against the No-Intro DAT.
- Size / header: 2,097,152 bytes (2 MiB), no header. Header and global checksums are correct.
- CRC32: `8A4D86A0` / SHA-1: `6ab81c4dec3263502a1781b600218285836c5302`
- Patched result: 4,194,304 bytes (expanded to 4 MiB for the English text). CRC32: `A1F37DD7` / SHA-1: `f9b36061ab4e1a1f3f0d173cae2bcc8267a59335`

## How to apply
1. Get `patches/HamsterClub_EN_v0.12.bps`.
2. Apply it to a copy of the ROM with Floating IPS (Flips), beat, or Rom Patcher JS. BPS checks the source checksum, so a different dump is refused.
3. The result is 4 MiB; that is expected. Play it in an accurate GBC emulator or on a flash cart.

## Status and testing
Version 0.12, a **test build**.

- **Emulator only:** played in PyBoy (headless, CGB mode). A fresh game was played through week 3 (intro, naming, shop, room, cage care, schedule, weekly report, contest entry). All eight contests were reached through RAM pokes and checked from screenshots.
- **Not tested on real hardware or a flash cart.**
- **Not played start to finish.** The birth event has not been seen, and the Breeders' Cup versions of the contests have not been played (they use the same screens as the HAM'S Cup ones).
- The lead played builds in their own emulator and reported the contest problems fixed in v0.10.
- The patch was re-applied to a clean copy of the ROM before publishing and matches the build hashes above.

Known issues:
- Some sound-effect words in the redrawn art are loose choices (for example CHI, WAG, RUB) and may change after review.
- Tricks 19 and 57 keep their original sweat and pain marks; two bits of lettering in tricks 84 and 85 never appeared in testing and were left alone.

## Build on this
Full source is in [`src/`](src/BUILD.md): the build tools, the `rhtk` toolkit, the script (Japanese and English, one entry per string), tables, original and edited graphics, and the emulator save states the art tools use. One command rebuilds the patch, and the published BPS was **verified byte for byte** from a clean copy. Engine details (encoding, bytecode, hooks, addresses, free space) are in [`docs/ENGINE_NOTES.md`](docs/ENGINE_NOTES.md), the glossary and voice sheet in [`docs/`](docs/), and the full story of how it was made in [`DEVLOG.md`](DEVLOG.md).

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering of the text engine and graphics, all of the ROM-hacking code (font, text relocation, name entry, contest screens), the translation of the whole script, and the English redraw of the baked-in artwork. The human project lead chose the game, supplied their own cartridge dump, approved the glossary and character voices, made wording calls (such as "Heal" in the shop) and reported bugs from play.

## License
Code, tools and docs made for this project: MIT. Translation text and new art: CC BY 4.0. Extracted game material (original script, ripped graphics, save states) remains the property of its rights holders and is included for research and modding.

## Credits
- Direction, review and bug reports: the project lead
- Translation, ROM hacking and art redraw: Claude (Anthropic)
- Tools: PyBoy (emulation for screenshots and VRAM), Pillow
- Original game: *Hamster Club* © 1999 Jorudan / Medetai / Aoba Shuppan. This is an unofficial fan translation. Please share the patch, not patched ROMs.

## Changelog
- **0.12:** All Japanese lettering in the artwork is now English: title logo, boot and copyright screens, the ACCIDENT banner and its BIRTH/DEATH/ACCIDENT/SICK/ESCAPE labels, the cough marks in the illness picture, and the sound effects in 60 trick animations.
- **0.11:** Last leftover line translated (vacuum accident in the "Outside" cage); contest result box lines; the four sports events named Snack, Bars, Seeds and Wheel everywhere; the shop's heal option is "Heal".
- **0.10:** Contest screens fixed: event titles, contestant lines, judges' scores, Leapfrog results, Seed Catch score bar, results boards, the Pretty Cup's goodbye line.
- **0.9:** First complete test build.
