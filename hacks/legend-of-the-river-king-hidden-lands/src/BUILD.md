# Building legend-of-the-river-king-hidden-lands

The build was checked on 22 Nov 2026: a fresh copy of this folder plus the original file below rebuilt every published patch **byte for byte**.

## You need
- The original, not included: **Kawa no Nushi-tsuri - Hikyou o Motomete (Japan).bin, renamed to orig.bin**
  - 85,412,880 bytes (single-track MODE2/2352 BIN)
  - CRC32 `98CED29A`, SHA-1 `915522f856709f07b3952a4588a3550729466e6b`
  - Put it in `src/rom/`.
- Python 3.13 (3.10 or newer should work) with Pillow 12 and NumPy 2: `pip install pillow numpy`, plus keystone-engine 0.9.2 for the MIPS hooks and capstone 5 for the disassembler (`pip install keystone-engine capstone`)
- xdelta3 3.0.11: `apt install xdelta3`. The xdelta stores the input and output file names, so the build runs it on fixed names to reproduce the published bytes.
- Fonts used to draw the new images: Noto Sans Black (`apt install fonts-noto-core fonts-noto-extra`), DejaVu Sans Bold (`fonts-dejavu-core`), Liberation Sans Bold and Bold Italic (`fonts-liberation`). IPA Gothic (`fonts-ipafont-gothic`) is only used by the OCR tools.
- About 250 MB of free disk: the build extracts the disc's files into `files/` (git-ignored).

## Build
```
cd src
./build.sh
```

## Expected output
| Built file | Same bytes as | SHA-1 |
|---|---|---|
| `src/KawaNoNushiTsuriHikyou_EN_v0.9.6.xdelta` | `patches/KawaNoNushiTsuriHikyou_EN_v0.9.6.xdelta` | `d337df419ba1e9af1444a12881466851add619d0` |

Patched result: rel096.bin: 85,412,880 bytes, CRC32 `9CA3F94C`, SHA-1 `40dba261e4b54dc72f20d4ac8fef47b4f7e1510a`.

## What's here
- `tools/`: the build (`build.py`, `insert.py` with the paginator and dictionary packer, `font_en.py`, `hook.py`, `names.py`, `note.py`, `labels.py`, `signs.py`, `staff.py`, `title.py`, `tim.py`), the disc reader and sector writer (`iso.py`, `cdsector.py`), the MIPS disassembler (`mdis.py`), the Beetle PSX driver (`emu.py`, `play.py`), the layout audits (`audit_*.py`) and the dumpers.
- `art/`: the tester's title art, the original title picture for reference, and the River King logo (`logos/collection.png`) reused for the title.
- `text/`: the English script (`en_*.txt`) and the Japanese as plain text (`jp_all.txt`).
- `out/`: the dumps (`script_jp.json`, `script_extra.json`).
- `script/script.tsv`: Japanese next to English (exported, see below).

## Changing the text
Edit `text/en_*.txt` (`id|English`) and run `./build.sh`. The build checks that each string fits its slot or box and stops if one doesn't.

`src/script/` is an export for reading, diffing or translating into another language: one row per string with an id, its location, the Japanese, the English, its limit and notes. Regenerate it with `python3 tools/export_script.py` (from `src/`, after a build). The build does not read it, so changes there need to be copied back into the files above.

See [../docs/ENGINE_NOTES.md](../docs/ENGINE_NOTES.md) for how the game works and [../DEVLOG.md](../DEVLOG.md) for how this was made.
