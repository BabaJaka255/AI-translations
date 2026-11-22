# Building legend-of-the-river-king-advance-collection

The build was checked on 22 Nov 2026: a fresh copy of this folder plus the original file below rebuilt every published patch **byte for byte**.

## You need
- The original, not included: **Kawa no Nushi Tsuri 3 & 4 (Japan).gba, renamed to k34.gba**
  - 4,194,304 bytes, no header
  - CRC32 `4F09CA00`, SHA-1 `043ccd64f04fff2cd2f19ba679dc3c7a1250b97c`
  - Put it in `src/rom/`.
- Python 3.13 (3.10 or newer should work) with Pillow 12 and NumPy 2: `pip install pillow numpy`
- keystone-engine 0.9.2, unicorn 2.1 and capstone 5: `pip install keystone-engine unicorn capstone` (the VWF hook is assembled with keystone; unicorn runs the game's own LZ77 code)
- xdelta3 3.0.11: `apt install xdelta3`. The xdelta stores the input and output file names, so the build runs it on fixed names to reproduce the published bytes.

## Build
```
cd src
./build.sh
```

## Expected output
| Built file | Same bytes as | SHA-1 |
|---|---|---|
| `src/out_build/Kawa no Nushi Tsuri 3 & 4 (English) v1.0.ips` | `patches/KawaNoNushiTsuri3and4_EN_v1.0.ips` | `de84a631c5a18c8303c5b04d12ab6b2df820fdf5` |
| `src/out_build/Kawa no Nushi Tsuri 3 & 4 (English) v1.0.xdelta` | `patches/KawaNoNushiTsuri3and4_EN_v1.0.xdelta` | `5fa2ed3539c64a6c8a8633936c78d066df4405f3` |

Patched result: 4,194,304 bytes, CRC32 `24573A7E`, SHA-1 `38aa069a368cd714b595eeef3ecaa080402a4536`.

## What's here
- `tools/`: everything. The build is `make_release.py` -> `insert.py` (with `vwf.py`, `menus.py`, `gfx.py`, `namekbd.py`, the `g3*`/`g4*` window modules, `gbasigns.py`, `gbalogos.py`). Analysis: the small GBA emulator (`gba.py`), disassembler (`kdis.py`), tracers, relative search and pointer scans, OCR, tile and map viewers. `g3_jp.json`/`g4_jp.json` are the Japanese dumps, `logos/` holds the tester's logo art, and the `.pkl` files are cached pointer and kanji data used by the tools.
- The tools expect to run from `tools/` and read `../rom/k34.gba`.
- `out/`: text dumps of both games.
- `script/`: `kawa3.tsv` and `kawa4.tsv`, Japanese next to English (exported, see below).

## Changing the text
Edit `tools/tr_g3_*.py` and `tools/tr_g4_*.py` (dicts keyed by ROM offset) and run `./build.sh`. The build checks that each string fits its slot or box and stops if one doesn't.

`src/script/` is an export for reading, diffing or translating into another language: one row per string with an id, its location, the Japanese, the English, its limit and notes. Regenerate it with `python3 tools/export_script.py` (from `src/`, after a build). The build does not read it, so changes there need to be copied back into the files above.

See [../docs/ENGINE_NOTES.md](../docs/ENGINE_NOTES.md) for how the game works and [../DEVLOG.md](../DEVLOG.md) for how this was made.
