# Building the Fune Tarou English patch

This folder rebuilds `patches/FuneTarou_SFC_EN_v1.0.bps` from a clean ROM. The build was checked byte for byte
on 2026-11-22. A fresh copy of this folder plus the original ROM gave the published BPS exactly.

## Requirements
- Python 3.10 or newer (tested with 3.13).
- Pillow (tested with 12.3): `pip install pillow`. It is used for the title subtitle PNG.
- The romhack toolkit (`rhtk`) that writes the BPS is included in `toolkit/`. Set `RHTK` to use another copy;
  it needs the SourceCopy support in `rhtk/patch.py` to give the same 16 KB patch.

## The ROM
Put your own dump at `src/rom/Fune Tarou (Japan).sfc` (this folder is git-ignored), or set `FT_ROM` to its path:

| | |
|---|---|
| Game | Fune Tarou (Japan), Super Famicom, HiROM, 16 Mbit |
| Size / header | 2,097,152 bytes, no copier header |
| CRC32 / SHA-1 | `5D6BA598` / `2c26f7432fe35c58545063ae44ea7daacbd50de3` |

## Build
From `src/`:
```sh
python3 tools/build.py
```
The build does the following:
1. Doubles the ROM to 32 Mbit.
2. Applies the engine hooks in `tools/engine.py`.
3. Draws the three fonts from `data/`.
4. Places every string and list entry from `script/`.
5. Builds the catch list tilemap and the title subtitle sprites.
6. Writes `build/` (git-ignored):

| Output | Size | CRC32 | SHA-1 |
|---|---|---|---|
| `build/fune-tarou-en.sfc` | 4,194,304 | `B440B1B2` | `b4485371a627a90c7bc7500b12d4c8c394c29c1c` |
| `build/Fune Tarou (English).bps` | 15,978 | | `9b15c5e1c1e9f87c46380cf282fbe543093f7128`, identical to `patches/FuneTarou_SFC_EN_v1.0.bps` |

(A BPS file ends with its own CRC32, so the CRC32 of any BPS file is the same constant. Compare SHA-1 instead.)

`python3 tools/build.py OUT.sfc` writes only a ROM, which is handy for test copies.

The build stops with `ERROR` lines when something does not fit. For example, a list entry may be wider than
its box, or an opening-speech line wider than 224 px.

## Where things are
| Path | What |
|---|---|
| `tools/build.py` | Text insertion: strings, fixed-stride lists, relocation into bank $E1, catch list layout and order, BPS. |
| `tools/engine.py` | Every code and data patch, with the original bytes asserted: text hooks, fonts, speech renderer, title subtitle. |
| `tools/ftlib.py` | Addresses, the English/Japanese text codec and font loader. |
| `tools/lz.py` | The game's LZSS: decompressor and a compatible compressor. |
| `tools/asm.py` | A tiny 65816 assembler (hex bytes, labels, branches) used by `engine.py`. |
| `tools/make_script.py` | Made the first draft of `script/*.json` from the ROM. It refuses to overwrite them without `--force`. |
| `tools/export_tsv.py` | Writes `script/script.tsv` from the JSON. |
| `tools/make_title_subtitle.py` | Draws `gfx/edit/title-subtitle.png` from the hand-drawn letter shapes in the file. |
| `script/strings.json` | The 9 strings: id, ROM offset, room in place, pointer operand sites, Japanese, English, notes. |
| `script/lists.json` | The fixed-stride lists (fish names, stage labels, lures): Japanese, English, notes. |
| `script/script.tsv` | Both together, one row per string, with location and limits, for reading and diffing. |
| `data/font_en.txt` | Tall 8x16 font for boxes that held full-width Japanese (from GNU Unifont, plus ligatures and macrons). |
| `data/font_low.txt` | Compact font for boxes that held half-width kana (from X11 misc-fixed 6x10). |
| `data/font_speech.txt` | Proportional opening-speech font (from X11 misc-fixed 9x15 bold, trimmed, with advances). |
| `gfx/edit/title-subtitle.png` | The title subtitle art the build reads (16 px tall, at most 128 px wide and 15 colors). |
| `gfx/orig/` | The title screen as extracted: the logo layer (BG1, top 112 lines), its palette, and the whole screen. |
| `toolkit/` | The rhtk romhack toolkit (MIT); the build uses only `rhtk/patch.py`. |

## Changing things
- **Text:** edit `en` in `script/strings.json` or `script/lists.json`, rebuild, then run
  `python3 tools/export_tsv.py`. Strings pick fonts with zero-width controls: `>` switches to the compact
  font and `<` back to the tall one. `^` marks a cursor or slot and `~` is skipped. List widths and alignment are
  in `build.py` (`LISTS`).
- **Catch list names** are cut to 12 columns. `SHORT` in `build.py` holds the abbreviations, and the ll/il/fi
  ligature glyphs keep most names whole.
- **Fonts:** edit the text art in `data/`. Each glyph is a code line followed by 16 rows of `#` and `.`.
- **Title subtitle:** edit `gfx/edit/title-subtitle.png` directly. To start over from the hand-drawn shapes, run
  `python3 tools/make_title_subtitle.py`.
