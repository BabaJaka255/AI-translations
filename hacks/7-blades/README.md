# 7 Blades (English, Japanese disc)
An English patch for the Japanese release of *7 Blades* (セブンブレイズ, Konami, PS2, SLPM-65008). It keeps the Japanese game and its 60 Hz program, and brings over the English text and assets of the official European release (SLES-50109). The English script is the European one, unchanged; nothing was retranslated. The European code was not run or converted: its subtitle engine and a few features were rebuilt for the Japanese program.

English in this build:
- movie subtitles (the European subtitle engine, rebuilt for the Japanese program);
- tutorial, item, weapon and food text, mission hints, character and enemy names;
- title screen, character select, item screen, game over, save and load screens, map labels, status popups and the kill counter, with the European English images and layouts;
- options screens (from the title and in game), with button prompts that follow the Japanese controls (Circle = confirm, Cross = back);
- new English for the three items the European release left in Japanese: 七支砲 Seven-Branch Cannon, 金丹 Elixir, 扇子 Folding fan.

European extras added to the Japanese program:
- the European sword trails, including Gokuu's glow and blue sparks;
- the European pressure-sensitive attacks for Gokuu and Yuri: how hard you press the attack button sets the strength (a hard press gives 1.5x damage, longer reach and the glowing trail; a light press does half damage). This needs a DualShock 2; emulator keyboard bindings usually count every press as hard.

## Base game
- Platform: PlayStation 2 (DVD, SLPM-65008)
- Required file: 7 Blades (Japan) SLPM-65008 disc image (.iso). Not yet compared against Redump.
- Size / header: 4,596,269,056 bytes, 2048-byte sectors
- CRC32: `CC8D415A` / SHA-1: `faa45d3fa1d382b6f78ad31463981382885f24c4`
- Patched result: 4,599,506,944 bytes. CRC32: `5395EE5E` / SHA-1: `96474e2e3c1ecd752c4dd192d7e721d73f9ae4ea`

## How to apply
Use xdelta UI, Delta Patcher, or the command line:
```
xdelta3 -d -B 1073741824 -s "7 Blades (Japan) SLPM-65008.iso" 7Blades_EN_test-2026-11-10.xdelta "7 Blades (English).iso"
```
Play the result in PCSX2 or with your usual loader.

## Status and testing
**Test build** of 2026-11-10 (`en-test`), not a finished release.

- **Emulator:** tested in PCSX2: movie subtitles, the tutorial, item and save/load screens, options screens, and the pressure attacks (glow and sparks seen). Yuri's pressure moves were not reached by hand.
- **Real hardware:** the project lead ran an earlier test build on a real PS2 (Neutrino loader, network streaming) and confirmed the movie subtitles work after a fix for garbled subtitles. This exact build, with the options screens and swapped button prompts, has not been run on hardware.
- **Not played start to finish.**
- The patch was re-applied to a clean copy of the disc image before publishing and gives the result hashes above.

Known issues:
- HUD weapon names stay in kanji (the European release shows these in kanji too).

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering of both releases, rebuilt the European subtitle engine, text renderer, sword effects and pressure attacks as new code for the Japanese program, moved the European English text and images onto the Japanese disc, and wrote the three missing item names. The human project lead chose the project and its rules (build on the Japanese program, keep the European English as is), supplied their own disc images, compared screens against the European release and tested on a real PS2.

## Credits
- Direction, comparison and hardware testing: the project lead
- Porting and hacking: Claude (Anthropic)
- English script and assets: from the official European release of *7 Blades*
- Original game: *7 Blades* © 2000 Konami. This is an unofficial fan patch. Please share the patch, not the game.

## Changelog
- **en-test 2026-11-10:** First published test build: subtitles, in-game text and screens with the European layouts and sizes, options screens, Japanese-style button prompts, European sword trails and pressure-sensitive attacks.
