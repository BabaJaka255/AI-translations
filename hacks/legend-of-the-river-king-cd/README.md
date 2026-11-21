# Legend of the River King CD
An English translation of *Kawa no Nushi Tsuri: Shizen-ha* (PC Engine CD-ROM2, 1992, Pack-In-Video), the CD remake of the Famicom original. Fish down the river from the mountain glen to the bay, fight off the wildlife and hunt for the River King. The patch translates all dialogue, the opening story, battle messages and the ending; all menus and windows; animal and fish names; the title menu; the fish guide; the backup memory messages; and the village signs (drawn as pictures). The title logo reads "Legend of the River King CD". Names follow the series glossary.

## Base game
- Platform: PC Engine CD-ROM2 / TurboGrafx-CD. **Needs the Super System Card 3.0** (or a Duo / Super CD-ROM2): the English font is kept in Super CD-ROM2 RAM, so System Cards 1.0 and 2.0 will not work.
- Required file: `Kawa no Nushitsuri - Shizen-ha (Japan) (Track 02).bin` from the Redump-style BIN/CUE set (30 tracks; only the data track 02 is patched)
- Size / header: 7,832,160 bytes, no header
- CRC32: `269CFEAF` / SHA-1: `660c5950bf93a35a095b53116379b760875d07f3`
- Patched result: 7,832,160 bytes. CRC32: `FF28D7BD` / SHA-1: `875467e90fbc90462e483c45dd8ae49556e94b00`

## How to apply
1. Back up the whole game folder.
2. Patch `(Track 02).bin` with **one** of:
   - `patches/KawaNoNushiTsuriShizenha_EN_v0.9.6.xdelta` (xdelta3, Delta Patcher or Rom Patcher JS)
   - `patches/KawaNoNushiTsuriShizenha_EN_v0.9.6.ips` (Flips or Lunar IPS)
3. Give the patched file the original name so the .cue still finds it. The .cue and the 29 audio tracks stay as they are.

The patch also rewrites the sector EDC/ECC, so the image stays valid for burning or CHD conversion. Load from a fresh boot, not an old save state.

## Status and testing
Version 0.9.6 (test release).

- **Emulator:** tested with the Super System Card 3.0 (Beetle PCE in the build environment, and the tester's own emulator). The tester playtested earlier versions and reported fixes up to v0.9.5.
- **v0.9.6** renames fish, animals and cooking notes to match the series glossary. It has **not been fully playtested** since that change.
- **Not verified:** the ending has not been seen running.
- **Not tested on real hardware.**

Known issues:
- Each Japanese character cell holds two English letters, so text uses a narrow 8x16 font. Some menu words are short because the slots are tiny (Item window 6 letters, food window 4).
- Save states from older versions keep old graphics in memory.

## About AI use
This project was made with substantial help from Claude (Anthropic). Claude did the reverse engineering of the HuC6280 code and text format, all of the hacking code (font in CD RAM, sector checksum repair, sign and logo graphics), and the whole translation.

The human tester directed the project, chose the names and English titles, playtested the builds in emulators and reported bugs with screenshots, and designed the title logo.

## Credits
- Testing, direction and title logo design: the project's tester
- Translation and hacking: Claude (Anthropic)
- Font: based on the X11 `koi8x16` font (public domain)
- Original game: *Kawa no Nushi Tsuri: Shizen-ha* © 1992 Pack-In-Video. This is an unofficial fan translation. Please distribute the patch, not patched images.

## Changelog
- **0.9.6:** Names follow the Super Legend of the River King glossary (v1.3): Masu Trout, Redspot Trout, Stone Moroko, Itomoroko and others in Title Case; Tanuki; cooking notes Arai, Kabayaki, Bottarga; paste bait.
- **0.9.5:** English fish names; village signs redrawn; dango banner.
- **0.9.4:** New title logo from the tester's design.
- **0.9.3:** English title logo.
- **0.9.2:** Consistency pass with the other series patches.
- **0.9.1:** Fixed the empty battle command menu, Japanese catch names, sign and banner text, and spacing.
- **0.9:** First test release.
