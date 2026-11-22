# Building tsuri-tarou-english

The build was checked on 22 Nov 2026: a fresh copy of this folder plus the original file below rebuilt every published patch **byte for byte**.

## You need
- The original, not included: **Tsuri Tarou (Japan).sfc**
  - 1,048,576 bytes (8 Mbit), no copier header
  - CRC32 `BBBFF8D8`, SHA-1 `4cb107cbef4fa5907ed0f2123de7a475bad7aa34`
  - Put it in `src/rom/` or point `TT_ROM` at it.
- Python 3.13 (3.10 or newer should work) with Pillow 12 and NumPy 2: `pip install pillow numpy`, plus openpyxl only for the spreadsheet in `tools/dump_text.py`

## Build
```
cd src
./build.sh
```

## Expected output
| Built file | Same bytes as | SHA-1 |
|---|---|---|
| `src/out_build/TsuriTarou_EN_v0.9.1.ips` | `patches/TsuriTarou_EN_v0.9.1.ips` | `838a2e24c0f8ea83b5e06349ae8f6617c51977be` |

Patched result: out_build/tt_en.sfc: 2,097,152 bytes, CRC32 `7CF11509`, SHA-1 `09d63e18d2b6d7d250769f126450b9ca9c76147b`.

## What's here
- `tools/`: the build (`build.py`, `expand.py`, `build_font.py`, `insert_*.py`, `make_ips.py`) and the analysis tools (65816 disassembler and tracer `dis65.py`/`cpu65816.py`/`trace.py`, emulator driver `emu.py`, savestate reader `s9xstate.py`, VRAM/tilemap renderers).
- `data/`: the character tables (`tt_8x8.tbl`, `tt_sprite_kana.tbl`) and the English font as text pixel art (`en_font.txt`).
- `text/`: the English script.
- `out/`: the script inventory (`script.json`, `script.xlsx`, `script_dump.txt`).
- `states/`: snes9x save states at each milestone, used by the tracer and the test scripts.
- `script/script.tsv`: the script, Japanese next to English (exported, see below).

## Changing the text
Edit `text/signs_en.txt` (spot signs), `text/story_en.txt` (story pages) and the tables in `tools/insert_menus.py` (menus, fish names, keyboard) and run `./build.sh`. The build checks that each string fits its slot or box and stops if one doesn't.

`src/script/` is an export for reading, diffing or translating into another language: one row per string with an id, its location, the Japanese, the English, its limit and notes. Regenerate it with `python3 tools/export_script.py` (from `src/`, after a build). The build does not read it, so changes there need to be copied back into the files above.

See [../docs/ENGINE_NOTES.md](../docs/ENGINE_NOTES.md) for how the game works and [../DEVLOG.md](../DEVLOG.md) for how this was made.
