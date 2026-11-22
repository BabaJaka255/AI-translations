# Building legend-of-the-river-king-cd

The build was checked on 22 Nov 2026: a fresh copy of this folder plus the original file below rebuilt every published patch **byte for byte**.

## You need
- The original, not included: **Kawa no Nushitsuri - Shizen-ha (Japan) (Track 02).bin**
  - 7,832,160 bytes (raw 2352-byte sectors, the data track of the Redump BIN/CUE)
  - CRC32 `269CFEAF`, SHA-1 `660c5950bf93a35a095b53116379b760875d07f3`
  - Put it in `src/rom/` or point `KS_TRACK` at it.
- Python 3.13 (3.10 or newer should work) with Pillow 12 and NumPy 2: `pip install pillow numpy`
- xdelta3 3.0.11: `apt install xdelta3`. The xdelta stores the input and output file names, so the build runs it on fixed names to reproduce the published bytes.

## Build
```
cd src
./build.sh
```

## Expected output
| Built file | Same bytes as | SHA-1 |
|---|---|---|
| `src/out_build/KawaNoNushiTsuriShizenha_EN_v0.9.6.ips` | `patches/KawaNoNushiTsuriShizenha_EN_v0.9.6.ips` | `7a778896e17360aa42042df521e084c7299ddf7b` |
| `src/out_build/KawaNoNushiTsuriShizenha_EN_v0.9.6.xdelta` | `patches/KawaNoNushiTsuriShizenha_EN_v0.9.6.xdelta` | `ad57cebcc1b0f75feb9017c12f856c0fe93e22b9` |

Patched result: out_build/en_track02.bin: 7,832,160 bytes, CRC32 `FF28D7BD`, SHA-1 `875467e90fbc90462e483c45dd8ae49556e94b00`.

## What's here
- `tools/`: the build (`build_patch.py`, `encode.py`, `templates.py`, `signs.py`, `logo.py`, `title_sprites.py`, `fish_guide.py`, `catch_names.py`), the sector EDC/ECC code (`cdsector.py`), the HuC6280 disassembler, assembler and CPU model, the dumper and checker, the test-disc maker and the Beetle PCE driver. `extract_iso.py` turns the raw track into the 2048-byte data the dumper reads.
- `data/`: the English font (`font_en.bin`, made from koi8x16) and the original .cue.
- `art/`: the tester's logo mock-up and a preview of it on the title.
- `out/`: the dump (`script.json`, `script_dump.txt`, `scan_raw.txt`).
- `script/`: `script.tsv` and `names.tsv`, Japanese next to English (exported, see below).
- System Card 3.0 is needed to play, not to build.

## Changing the text
Edit `tools/tr_main.py` (dialogue, keyed by the Japanese), `tools/tr_menus.py`, `tools/fish_guide.py` and `tools/catch_names.py` and run `./build.sh`. The build checks that each string fits its slot or box and stops if one doesn't.

`src/script/` is an export for reading, diffing or translating into another language: one row per string with an id, its location, the Japanese, the English, its limit and notes. Regenerate it with `python3 tools/export_script.py` (from `src/`, after a build). The build does not read it, so changes there need to be copied back into the files above.

See [../docs/ENGINE_NOTES.md](../docs/ENGINE_NOTES.md) for how the game works and [../DEVLOG.md](../DEVLOG.md) for how this was made.
