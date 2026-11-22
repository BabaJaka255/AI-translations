# Building the Legend of the River King (Famicom) English patch

This folder rebuilds `patches/KawaNoNushiTsuri_FC_EN_v1.0.bps` from a clean ROM. The build was checked byte for
byte on 2026-11-22: a fresh copy of this folder plus the original ROM gave the published BPS exactly.

## Requirements
- Python 3.10 or newer (tested with 3.13) and Pillow (tested with 12.3): `pip install pillow`.
- cc65's `ca65` and `ld65` on the PATH (tested with cc65 2.19, `apt install cc65`).
- The romhack toolkit (`rhtk`) used to write the BPS is included in `toolkit/`; set `RHTK` to use another copy.

## The ROM
Put your own dump at `src/rom/original.nes` (this folder is git-ignored):

| | |
|---|---|
| Game | Kawa no Nushi Tsuri (Japan), Famicom, mapper 4 (MMC3) |
| Size / header | 262,160 bytes, 16-byte iNES header included |
| CRC32 / SHA-1 (with header) | `4F5C3D34` / `8ad15b4d26610d164f19754e15f9afb8c1804796` |
| CRC32 / SHA-1 (without header, No-Intro) | `F4E5DF0E` / `9693d51f52ca9c94fd6bd769fa377acc571b6d5d` |

## Build
From `src/`:
```sh
python3 tools/knt_build.py
```
It expands the program ROM from 128 to 256 KiB, draws the English font, assembles `asm/*.s`, rewrites the
window templates and menu code, places all 317 lines and the fish/creature names, draws the town signs and
the title logo, then writes `build/` (git-ignored):

| Output | Size | CRC32 | SHA-1 |
|---|---|---|---|
| `build/kawa-no-nushi-tsuri-fc-en.nes` | 393,232 | `27F72AA2` | `65d1ab2ea1f6672669a566d4803e3efbedf6a95c` |
| `build/kawa-no-nushi-tsuri-fc-en.bps` | 130,154 | `2144DF1C` | identical to `patches/KawaNoNushiTsuri_FC_EN_v1.0.bps` |

## Where things are
| Path | What |
|---|---|
| `tools/knt_build.py` | The build. Line layout rules (`WIDTH`, two rows of 18 tiles) are at the top. |
| `tools/knt_font.py` | The English 8x8 font, drawn from text art in the file. |
| `tools/knt_windows.py` | Every menu window (tile maps) and the menu code patches, with the original bytes asserted. |
| `tools/knt_names.py` | Fish (59) and creature (22) names, and the catch sentences. |
| `tools/knt_gfx.py` | Town plaques (INN, hook, fish) and the TEA banner. |
| `tools/knt_logo.py` | Cuts `gfx/title_logo.png` into the Japanese logo's tiles. |
| `asm/` | 6502 code: text hooks and two-row typewriter (`text_hook.s`), menu lists (`menu13.s`), area titles (`status9.s`), fish catch pointers (`fish10.s`). |
| `script/en_lines.txt` | The English script the build reads (`ID <TAB> text`). |
| `script/lines.json` | Ids, pointer locations and the Japanese, as extracted. |
| `script/script.tsv` | Both together, one row per line, for reading and diffing. |
| `tables/` | `jp.tbl` (original text) and `en.tbl` (patched ROM). |
| `gfx/` | The title logo source and a guide to the cells it may use. |

## Changing things
- **Text:** edit `script/en_lines.txt`. `python3 tools/knt_fit.py "text"` shows how a line wraps; the build
  stops on a line that does not fit. Re-export the TSV with `python3 tools/knt_export_tsv.py > script/script.tsv`.
- **Title logo:** edit `gfx/title_logo.png` (256x96, four colours: sky, shadow, outline, fill). Only the cells
  left clear in `gfx/title_logo_guide.png` may be inked, and the logo may use at most 137 distinct 8x8 tiles;
  the build checks both. Without the PNG the build draws a text logo with the Inter Display font
  (`/usr/share/fonts/opentype/inter/`, OFL).
- **Do not rerun `tools/knt_extract.py`** unless you mean to start over: it rewrites `script/lines.json`.
- `KNT_TMP` sets the folder for assembler output (default `/tmp/knt_build`).
