# Building the Iso Tsuri: Ritou-hen English patch

This folder rebuilds `patches/IsoTsuri_RitouHen_SFC_EN_v1.0.bps` from a clean ROM. The build was checked byte for
byte on 2026-11-23: a fresh copy of this folder plus the original ROM gave the published BPS exactly.

## Requirements
- Python 3.10 or newer (tested with 3.13).
- Pillow (tested with 12.3): `pip install pillow`. It reads the koi8x16 PCF font and draws the title logo.
- The romhack toolkit (`rhtk`) that writes the BPS is included in `toolkit/`. Set `RHTK` to use another copy.
- Only for the emulator scripts in `tools/test/`: `pip install stable-retro numpy`.

## The ROM
Put your own dump in `src/rom/` (this folder is git-ignored; any `.sfc` name works, it is found by SHA-1):

| | |
|---|---|
| Game | Isozuri - Ritou Hen (Japan), Super Famicom, HiROM + FastROM, 16 Mbit |
| Size / header | 2,097,152 bytes, no copier header |
| CRC32 / SHA-1 | `3D35D085` / `49741c14e923bdaa0ff5776744508544921cbb2d` |

## Build
From `src/`:
```sh
python3 tools/build.py
```
The build:
1. Expands the ROM to 32 Mbit and copies the text bank $C1 to $E0.
2. Writes the fonts (8x16 menu font from `tools/fonts/koi8x16.pcf`, bold story font from `data/font_story.txt`).
3. Assembles the hooks in `tools/build.py` with `tools/asm65.py` and patches every call site (original bytes are
   asserted, so a wrong ROM stops the build).
4. Writes the script from `script/strings.json` and `script/tables.json` (`tools/script_en.py`).
5. Draws the hand-made title logo (`tools/title_logo.py`, `title_letters.py`, `brush.py`) and inserts it LZ-compressed.
6. Fixes the checksum and writes `build/` (git-ignored):

| Output | Size | CRC32 | SHA-1 |
|---|---|---|---|
| `build/iso_en.sfc` | 4,194,304 | `1D167192` | `ed32c85e7af1da0dc8162d9b8a9a88816d23d696` |
| `build/iso_en.bps` | 73,995 | | `3f73fdb1b19eeaa4ea77506bdead47cf4c88aa59`, identical to `patches/IsoTsuri_RitouHen_SFC_EN_v1.0.bps` |

(A BPS file ends with its own CRC32, so compare SHA-1 for the patch file.)

## Editing the text
- Edit only the `en` (and `notes`) fields in `script/strings.json` and `script/tables.json`, then rebuild.
  `script/script.tsv` is a read-only view for diffing: `python3 tools/export_tsv.py` regenerates it.
- In strings: `]` newline, `^` menu cursor stop, `~` no-op, `{FFFC}`/`{FFFD}` scene change in the crawls,
  `{center}` centres a crawl line, `{nbsp}` a space that does not end a label word.
- Table entries have fixed column widths (see `limit` in the TSV); the build stops if one does not fit.
- The crawls are wrapped automatically at 224 px of the story font.

## Title logo
- `tools/title_logo.py` draws the logo from the brush strokes in `tools/title_letters.py`. Run it on its own to
  write a preview to `gfx/edit/title_logo_bg3.png`.
- To use your own art instead, save a 256x224 PNG as `gfx/edit/title_logo.png` in the BG3 colours (see
  `gfx/orig/title_logo_jp_layer.png`: one of red/dark red/black, yellow/dark yellow/black or white/black per 8x8
  tile, at most ~236 unique tiles, rows from y 184 down left for the copyright line). The build picks it up.

## Where things are
| Path | What |
|---|---|
| `tools/build.py` | ROM layout, hooks (65816 source in the file), fonts, checksum, BPS. |
| `tools/script_en.py` | Writes every string and table: relocation into $E0:8000+, column fitting, keyboard, crawl wrap. |
| `tools/inventory.py` | Every string (address, pointer operand sites) and fixed table (base, count, stride, columns). |
| `tools/textcodec.py` | English text codec and control codes. `tools/extract.py` dumped the Japanese script. |
| `tools/islz.py` | The game's LZ format: decompressor and compatible compressor. |
| `tools/asm65.py`, `d65.py`, `lst.py` | 65816 assembler, disassembler, bank listing. |
| `tools/cpu.py`, `run.py`, `mkmenu.py` | Python 65816 interpreter that runs from a snes9x save state, for tracing. |
| `tools/drive.py`, `s9x_state.py`, `vview.py` | Emulator driver (stable-retro), save-state reader, tile viewer. |
| `tools/test/` | Emulator scripts used for testing (see its README). |
| `data/font_story.txt` | Bold proportional font for the opening and ending crawls. |
| `gfx/orig/` | The original title logo layer and title screens (for editing). `gfx/edit/` the drawn logo preview. |
| `toolkit/` | Vendored `rhtk` (BPS writer). |
