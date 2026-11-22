# PlayStation 2 (and PS1) workflow

PS2 games are disc images with a real filesystem, so the work is file-based:
pull the files out, find which ones hold text and graphics, change those files,
and write them back into a copy of the image. All commands are under `rhtk ps2`.

Setup each session (besides `requirements.txt`): `apt-get install -y xdelta3 xorriso`.
xdelta3 makes release patches; xorriso is only for independent checks.

## 1. Get the disc image in

the project lead supplies the image (we never download games). A full DVD image is 1 to 4.5 GB,
which can be too big for a chat upload. Ways in, best first:

1. the project lead's computer is linked to the thread: request access to the folder holding
   the image, split it there (`split -b 300M game.iso game.iso.part-`), stage the
   parts, and `cat` them back together into `games/<id>/rom/`. Check the CRC32 against
   the one computed on the device before and after.
2. A chat upload, if it goes through.
3. Only the files that matter (the boot ELF and the text/graphics archives), staged
   from the project lead's own extraction. Enough to translate, but a full image is needed to build and test.

Keep the image in `games/<id>/rom/` (git-ignored, never shared) and record its CRC32,
serial and, when known, the Redump entry in `notes/rom.md`.

## 2. Look around

```sh
rhtk ps2 info rom/game.iso          # serial (SLPS-12345), boot ELF, volume, UDF bridge, hashes
rhtk ps2 ls rom/game.iso            # every file with LBA and size, in disc order
rhtk ps2 extract rom/game.iso work/disc     # all files + work/disc/_iso.json manifest
rhtk ps2 scan work/disc             # file types, and which files hold Japanese text
rhtk ps2 elf work/disc/SLPS_123.45  # load segments of the executable
```

`scan` ranks files by Shift-JIS text (runs that are at least a quarter kana)
and flags UTF-16 kana. Unknown types show their first four bytes as a tag, which
is usually the archive format's name.

Japanese PS2 games mostly use Shift-JIS. Text is commonly in:
- the boot ELF (menus, item names, system messages);
- script files or archives (`.BIN`, `.DAT`, AFS, CRI CPK), often compressed;
- textures with baked-in lettering (TIM2, or a game-specific format).

## 3. Pointers in the ELF

A plain stored pointer is a 32-bit virtual address. MIPS code usually builds the
address with a `lui` + `addiu` (or a load/store) pair instead. One command finds both:

```sh
rhtk xref work/disc/SLPS_123.45 0x2A3F40 --mapping elf   # target is a file offset
```

For project.json pointer blocks, use the mapping `ps2 elf` prints. Code-built
addresses can't be repointed by `rhtk build`; patch the instruction pair or keep
strings in place. ELFs rarely have free space. Options: shorter text in place,
unused debug strings, or a new segment appended at the end (the game's memory map
must allow it).

## 4. Archives and textures

- AFS (Sega, many others): `ps2 afs-unpack` / `ps2 afs-pack` keep order, names and alignment.
- TIM2: `ps2 tim2-info`, `ps2 tim2-rip` (indexed PNG with the game's palette and
  alpha), `ps2 tim2-insert` (same size; RGBA edits are mapped to the nearest palette colour).
  PS2 alpha 0x80 is opaque; the tools convert to and from 0-255.
- CRI CPK, game-specific packers and compression: write a per-game tool under
  `games/<id>/tools/` first, and move it into `rhtk/` once a second game needs it.

## 5. Fonts

Many games draw only full-width Shift-JIS from a fixed-width font, so English looks
spaced out. In order of effort: use the font's full-width Latin as is, then add
half-width glyphs, then hook the text renderer for variable width (look at the
glyph width table or the advance after each character).

## 6. Rebuild and test

```sh
rhtk ps2 patch rom/game.iso build/game-en.iso --dir work/mod --report build/moves.json
```

`work/mod` mirrors the disc layout and holds only changed files. A file that
still fits in the sectors before the next file is written in place; otherwise it
goes after the last sector and its directory record is repointed. Some games
locate files by hard-coded LBA (a table in the ELF or an archive); after a move,
update that table or make the file fit. The UDF bridge on DVD images is left
alone. The console and PCSX2 read ISO9660.

Raw CD images (`.bin`, 2352-byte sectors) can be read directly; run `ps2 to-iso` once
and patch the `.iso`.

Testing: `sh scripts/pcsx2-setup.sh games/<id>/rom/bios/<BIOS>.bin` sets up PCSX2 2.4.0
headless (Xvfb, software renderer, no audio). the project lead okayed running it in the cloud on 2026-11-02
and supplied a BIOS from their own console. Drive it with xdotool keys and capture the screen with
ImageMagick `import`; `games/conveni3-ps2/tools/emu.sh` is a working example. F1 saves a state.

## 7. Release

BPS is impractical at DVD size, so PS2 patches are xdelta (VCDIFF), the format
PS2 translation patches use:

```sh
rhtk ps2 xdelta rom/game.iso build/game-en.iso build/game-en.xdelta
```

Users apply it with xdelta UI, DeltaPatcher or `xdelta3 -d -s game.iso game-en.xdelta out.iso`.
Publish the CRC32 or Redump hash of the expected image in the readme.
