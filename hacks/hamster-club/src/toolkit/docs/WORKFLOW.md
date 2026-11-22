# Workflow: from ROM to English patch

Every game follows the same nine phases. Each phase ends with something saved
in the game's folder, so any thread can pick the work up where the last one
stopped. Track status in `notes/progress.md`.

Paths below are relative to the game folder, `games/<game-id>/`.

## 0. Intake

1. the project lead supplies the ROM or disc image (uploaded to the project). We never
   download ROMs.
2. `rhtk info <file>`: record platform, CRC32, SHA-1 and header in
   `notes/rom.md`. Compare the hashes against the No-Intro / Redump entry
   so we know it's a clean, verified dump. Patches are built against that exact
   dump.
3. `rhtk init games/<game-id> --rom <file>` creates the folder from the
   template and pins the CRC32 in `project.json`.
4. Decide the route:
   - **Cartridge games (NES through GBA)**: the ROM *is* the data. Go to phase 1.
   - **Disc and file-system games (PS1 onward, NDS, 3DS, Switch, PC)**:
     extract the file system first (see PLATFORMS.md). Text usually sits in
     separate files in a known format (BMG, MSBT, JSON, Unity assets, Shift-JIS
     blobs). Use an existing format tool where one exists, then treat each
     extracted file as a "ROM" for the steps below.

## 1. Find the text encoding (build `tables/jp.tbl`)

- Older games use their own encodings. Find a word that appears on screen early
  in the game and run
  `rhtk search rom.bin たたかう --order hira_jis --tbl tables/jp.tbl`.
  Try every `--order`, plus `--width 2` for 16-bit encodings. A hit gives a
  starter table for one script. Extend it by viewing the font tiles
  (`rhtk gfx-rip`) and matching each glyph to its index.
- Newer games are usually Shift-JIS (`rhtk sjis`), UTF-8 or UTF-16. Use the
  standard codec and skip the custom table except for control codes.
- Control codes: when bytes show up as `[XX]` in decoded text, watch what the
  game does there in an emulator: new line, wait for button, character name,
  colour, portrait. Name each one in the table (`*FE=<br>`, `/FF=<end>`,
  `$F0=<name>,1`). Undocumented codes stay as `[XX]` and must be kept as-is.

## 2. Find the pointers

- Take the offset of a known string and run `rhtk xref rom.bin 0x123456 --mapping snes-lorom`
  (or `gba`, or a bank mapping). Several evenly spaced hits in a row make up a
  pointer table. Note the start, count, size and stride.
- No hits? The game may use offsets relative to a block, split pointers (low and
  high bytes in separate tables), or compute addresses in code. Set a read
  breakpoint on the string in an emulator debugger and follow the code back
  to where the address comes from. Write down what you find in `notes/rom.md`.
- Record each table as a block in `project.json`. Use `"mode": "range"` only for
  text that's read sequentially with no pointers (fixed-length menus and names).

## 3. Dump

`rhtk dump games/<game-id>` writes `script/<block>.json`. Check the dump:
no stray `[XX]` in the middle of words, strings start and end cleanly, and the
counts look right. Running dump again refreshes the Japanese and keeps every
`en` and `notes` field.

## 4. Graphics survey

Rip everything that contains Japanese: the font, title logo, menus, battle
UI, and any text baked into images. `rhtk gfx-rip` (add `--lz10` for compressed
data, `--pal-offset` for real colours) writes indexed PNGs to `gfx/orig/`.
Edited copies go in `gfx/edit/`, and each one gets an entry in the
project's `gfx` list so `build` reinserts it.

## 5. Plan the font and space

- Eight by eight fixed-width kana fonts fit about half as many English
  letters per line as they could. Options, from cheapest to best:
  1. Fixed-width English font over the kana tiles.
  2. Dual-tile encoding (two narrow letters per tile, "dte"/"mte" table entries).
  3. A variable-width font (VWF) routine written in assembly. Best result. Most
     SNES, GBA and DS projects do this.
- Make `tables/en.tbl` match the font you insert.
- Find free space (long runs of `FF` or `00` that the game never reads, confirmed
  with a debugger) and list it under `free_space`. Expand the ROM
  (`expand_to`) when the cartridge format allows it.
- Write assembly hacks with the platform's assembler (asar, armips, ca65,
  rgbds), build them to an IPS file, and list it under `patches` in project.json.

## 6. Translate

Follow `docs/TRANSLATING.md` and `docs/STYLE_GUIDE.md`. Before anyone
translates script text, write the glossary and character sheets in `notes/`.

## 7. Build and check

```
rhtk qa games/<game-id>        # must report 0 errors
rhtk build games/<game-id>     # writes build/<id>-en.*, plus .bps and .ips
```

`build` inserts the script, reinserts graphics, applies the assembly patches,
fixes the checksum, and creates the patches. Untranslated strings keep
their original bytes, so a part-translated build still runs.

## 8. Playtest

Boot the build in an accurate emulator. Play through every new text path you
can reach, and use save states at branches. Record overflows, text that runs
past its box, wrong names, and crashes in `notes/progress.md` with a save state
or the string ID. QA catches most of the mechanical errors, so playtesting
is mainly for pacing, line breaks that look wrong, and tone.

## 9. Release

Ship only the `.bps` patch, plus a readme with: the required source ROM (name
and CRC32/SHA-1), credits, a changelog, and the translation notes worth sharing.
Never distribute the ROM or a pre-patched ROM.
