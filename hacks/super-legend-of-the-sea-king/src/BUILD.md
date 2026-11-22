# Building super-legend-of-the-sea-king

The build was checked on 22 Nov 2026: a fresh copy of this folder plus the original file below rebuilt every published patch **byte for byte**.

## You need
- The original, not included: **Umi no Nushi Tsuri (Japan) (Rev 1).sfc**
  - 2,097,152 bytes (16 Mbit), no copier header
  - CRC32 `C985F568`, SHA-1 `6f01bee87737de87e756f75b7b05e9cedb63faf6`
  - Put it in `src/rom/ (any .sfc name)` or point `UMI_ROM` at it.
- Python 3.13 (3.10 or newer should work) with Pillow 12: `pip install pillow`. DejaVu Sans Bold is bundled in `build/fonts/`. IPA Gothic (`apt install fonts-ipafont-gothic`) is only needed by the kanji matching tools in `analysis/` and `early/`.

## Build
```
cd src
./build.sh
```

## Expected output
| Built file | Same bytes as | SHA-1 |
|---|---|---|
| `src/out/umi_en.ips` | `patches/UmiNoNushiTsuri_EN_v1.1.ips` | `0f10e7e222c15198b6babbb23590bf0a4d805cb6` |

Patched result: out/umi_en.sfc: 4,194,304 bytes, CRC32 `35B3E1F3`, SHA-1 `17475c88f6db5695e4b20e1a9ebeae6f21ccdb29`.

## What's here
- `build/`: the build (`build_patch.py` and one module per screen or graphic), the LZSS codec, the 65816 assembler, the kanji and single-byte tables (`umi_kanji.tbl`, `umi_single_byte.tbl`) and the English script (`tr_*.py`). `build/warp_test.py` makes the separate zone-warp test build; it is not part of the release.
- `analysis/`: the dumper, disassembler, pointer finder, graphics loader scanner, emulator driver and RAM poker.
- `early/`: the first engine-comparison tools and the kanji matching data from the start of the project.
- `out/`: the dump (`script.json`, `script_dump.txt`, `fish.json`) and the review spreadsheet.
- `script/`: `script.tsv`, `names.tsv` and `fish.tsv`, Japanese next to English (exported, see below).
- `README.md`: the toolkit's own notes.

## Changing the text
Edit `build/tr_*.py` (the script by string id, names and fish records) and run `./build.sh`. The build checks that each string fits its slot or box and stops if one doesn't.

`src/script/` is an export for reading, diffing or translating into another language: one row per string with an id, its location, the Japanese, the English, its limit and notes. Regenerate it with `python3 analysis/export_script.py` (from `src/`, after a build). The build does not read it, so changes there need to be copied back into the files above.

See [../docs/ENGINE_NOTES.md](../docs/ENGINE_NOTES.md) for how the game works and [../DEVLOG.md](../DEVLOG.md) for how this was made.
