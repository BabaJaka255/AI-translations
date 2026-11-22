# Building legend-of-the-river-king-3

The build was checked on 22 Nov 2026: a fresh copy of this folder plus the original file below rebuilt every published patch **byte for byte**.

## You need
- The original, not included: **Kawa no Nushi Tsuri 5 - Fushigi no Mori kara (Japan).gba, renamed to k5.gba**
  - 4,194,304 bytes, no header
  - CRC32 `4A8F2F62`, SHA-1 `418d61ddd992ceeaa10a102deaf9eb15a2fb7328`
  - Put it in `src/rom/` or point `K5_ROM` at it.
- Python 3.13 (3.10 or newer should work) with Pillow 12 and NumPy 2: `pip install pillow numpy`
- keystone-engine 0.9.2, unicorn 2.1 and capstone 5: `pip install keystone-engine unicorn capstone`
- xdelta3 3.0.11: `apt install xdelta3`. The xdelta stores the input and output file names, so the build runs it on fixed names to reproduce the published bytes.
- Fonts: the New Game / Continue letters are stored as masks in `art/`, so no font is needed. Only if you delete those masks does `tools/logo.py` render them from Noto Sans Condensed Bold (`apt install fonts-noto-extra`).

## Build
```
cd src
./build.sh
```

## Expected output
| Built file | Same bytes as | SHA-1 |
|---|---|---|
| `src/release/Kawa no Nushi Tsuri 5 (English) v0.9.2.ips` | `patches/KawaNoNushiTsuri5_EN_v0.9.2.ips` | `be35d35fb622bfa74a07badee266013c948de5f1` |
| `src/release/Kawa no Nushi Tsuri 5 (English) v0.9.2.xdelta` | `patches/KawaNoNushiTsuri5_EN_v0.9.2.xdelta` | `390a15bfd5937b382e6a1a353c79f536171ad48f` |

Patched result: 8,388,608 bytes, CRC32 `D0293080`, SHA-1 `7759e2811f34b9640e14fb93509313aa3be54311`.

## What's here
- `tools/`: the build (`make_release.py`, `build_patch.py`, `wrap_script.py`, `logo.py`, `tags.py`, `maplabels.py`), the script codec (`script.py`, `textcodec.py`, `charmap.py`, `lz.py`), the unicorn ARM runner `k5lib.py` that calls the game's own decompressor, the THUMB disassembler and the mGBA libretro driver.
- `art/`: the tester's logo parts and the menu letter masks.
- `text/`: the English script.
- `out/`: the dumps (`script_jp.json`, `ui_jp.json`) and the merged `script.json`.
- `script/`: `dialogue.tsv` and `ui.tsv`, Japanese next to English (exported, see below).

## Changing the text
Edit `text/script_en_*.txt` (dialogue) and `text/ui_en.txt` (menus, items, fish, Fishing Note, staff roll) and run `./build.sh`. The build checks that each string fits its slot or box and stops if one doesn't.

`src/script/` is an export for reading, diffing or translating into another language: one row per string with an id, its location, the Japanese, the English, its limit and notes. Regenerate it with `python3 tools/export_script.py` (from `src/`, after a build). The build does not read it, so changes there need to be copied back into the files above.

See [../docs/ENGINE_NOTES.md](../docs/ENGINE_NOTES.md) for how the game works and [../DEVLOG.md](../DEVLOG.md) for how this was made.
