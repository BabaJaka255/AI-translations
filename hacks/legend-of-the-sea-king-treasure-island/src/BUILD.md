# Building legend-of-the-sea-king-treasure-island

The build was checked on 23 Nov 2026: a fresh copy of this folder plus the original disc below rebuilt the published patch **byte for byte**.

## You need
- The original, not included: **Umi no Nushi Tsuri - Takarajima ni Mukatte (Japan).bin**, copied to `src/rom/orig.bin`
  - 117,844,608 bytes (single-track MODE2/2352 BIN, no header)
  - CRC32 `DAD222F2`, SHA-1 `ee6bce2a7b06df79c73f69ba8e86a3f5f9f61e0c`
- Python 3.13 (3.10 or newer should work) with Pillow 12, NumPy 2, SciPy 1.18 and OpenCV 4/5 (`pip install pillow numpy scipy opencv-python-headless`), keystone-engine 0.9.2 for the MIPS hooks (`pip install keystone-engine`), and capstone 5 for the disassembly tools (`pip install capstone`).
- DejaVu Sans Bold (`apt install fonts-dejavu-core`, checked with 2.37): the English text font is rendered from it at build time, so another version of the font or of FreeType could change the bytes.
- xdelta3 3.0.11 (`apt install xdelta3`). The xdelta stores the input and output file names, so the build runs it on the fixed names `orig.bin` and `test.bin` to reproduce the published bytes.
- About 350 MB of free disk: the build extracts the disc's files into `files/` and writes a full patched image (both git-ignored).

## Build
```
cd src
./build.sh
```
It extracts the disc (`tools/iso.py`), dumps the Japanese script (`tools/dump.py`, same as the committed `out/script_jp.json`), draws the English graphics (`tools/gfx_build.py` -> `gfx_out/`), inserts text, font, hooks and map labels (`tools/build.py` -> `test.bin`), makes the xdelta and re-exports `script/script.tsv`. It takes about 15 seconds.

## Expected output
| Built file | Same bytes as | SHA-1 |
|---|---|---|
| `src/UmiNoNushiTsuriTakarajima_EN_v1.0.xdelta` | `patches/UmiNoNushiTsuriTakarajima_EN_v1.0.xdelta` | `960c66e9bb59d66b4455d30f10d45502a861a7d7` |

Patched result `src/test.bin`: 117,844,608 bytes, CRC32 `563EA50F`, SHA-1 `158cf248e71d3aec9436fddbf0da15c34bab7473`.

The build prints a few layout warnings and a `STUCK` list of 11 string ids. Both are expected: the STUCK strings have no reference anywhere in the game code (dead text) and their English doesn't fit in place, so they stay Japanese.

## What's here
- `tools/`: the build and everything used to make it.
  - Build: `build.py`, `insert.py` (script encoder, layout and wrapping, relocation into the exe's text pool), `engine.py` (the English text engine and all code patches, assembled with Keystone), `font_en.py`, `textfmt.py`, `labels.py` (Fishing Note map labels), `gfx_build.py` + `gfx.py` + `letters.py` (redrawn art with hand-built brush lettering) and `credits.py` (staff roll), `tim.py`, `iso.py`, `cdsector.py` (sector EDC/ECC), `dump.py`, `dec.py`, `refs.py`, `scan.py`, `table.py`, `timdump.py`, `export_script.py`.
  - Analysis: `mdis.py` (MIPS disassembler with symbol names), `sym.py` (PsyQ MAIN.SYM parser), `font_ocr.py`, `font_dp.py`, `glyphsheet.py` (reading the kanji font), `fitcheck.py`, `warns.py`, `tabs.py` (layout checks), `tm.py`, `worksheet.py` (translation memory from the other Nushi Tsuri scripts in this repo), `keyboard.py` (generates `text/en_kbd.txt`).
  - Emulator testing (Beetle PSX libretro core through ctypes; needs `apt install libretro-beetle-psx` and a SCPH-5500 BIOS in `src/sys/`, neither included): `emu.py`, `play.py`, `run.py`, `walk.py`, `auto.py`, `fresh.py`, `freshboot.sh`, `newgame.py`, `tojetty.py`, `strview.py` (shows any string id in a real message box), `vramfix.py`.
  - `logo/`: the code that drew the title logo, kept as a record. The build does not run it; it reads the finished `gfx/title_logo.png`. Its reference pictures (other games' logos) are not included.
- `text/`: the English script (`en_*.txt`, `id|English`) and the Japanese as plain text (`jp_all.txt`).
- `out/script_jp.json`: the Japanese dump (id, address, length, references, glyph words).
- `script/script.tsv`: Japanese next to English (exported, see below).
- `gfx/`: `title_logo.png` (build input: the finished logo band, 256x144), the logo as separate layers, the alternate colouring, and before/after pictures of the other redrawn graphics.
- `data/`: `sym.txt` (functions and variables from the disc's PsyQ `TIM/MAIN.SYM`, which is from a slightly earlier build, so addresses drift) and `listing.txt` (disc file list with LBAs).

## Changing the text
Edit `text/en_*.txt` and run `./build.sh`. Messages are wrapped automatically to the 224 px box; menus and labels keep the Japanese line layout, and `tools/warns.py` lists lines that grew wider than the Japanese. Text control codes are listed at the top of `tools/textfmt.py`.

`script/script.tsv` is an export for reading, diffing or translating into another language: one row per string with an id, its location, the Japanese, the English, its limit and notes. The build does not read it, so changes there need to be copied back into `text/`.

See [../docs/ENGINE_NOTES.md](../docs/ENGINE_NOTES.md) for how the game works and [../DEVLOG.md](../DEVLOG.md) for how this was made.
