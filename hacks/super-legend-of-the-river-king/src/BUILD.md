# Building Super Legend of the River King

The source in this folder rebuilds the published v1.3 patch **byte for byte** from a clean ROM. This was verified on 2026-11-22 by copying the folder to an empty directory, adding the ROM, running the steps below and comparing the output with `../patches/KawaNoNushiTsuri2_EN_v1.3.ips`.

## 1. Requirements

* **ROM:** `Kawa no Nushi Tsuri 2 (Japan).sfc` (No-Intro)

  | | |
  |---|---|
  | Size | 1,572,864 bytes (12 Mbit), **no** 512-byte copier header |
  | CRC32 | `716D3EFF` |
  | SHA-1 | `c2103dd94e2a1a65a495fc02adc2e7d040f31212` |
  | MD5 | `120f97e5855bfe8e31961fbf387e4150` |

* **Python 3.10 or newer.** The build was verified with Python 3.13.
* **Python packages:**

      pip install pillow openpyxl numpy

  The build was verified with Pillow 12.3 and openpyxl 3.1.5. `numpy` is only needed by some of the analysis tools.
* **Fonts:** included in `gfx/fonts/source/`, so nothing extra is needed for the build.

## 2. Put the ROM in place

Copy the ROM into `src/rom/` (any file name ending in `.sfc`), or point an environment variable at it:

    export KNT2_ROM=/path/to/Kawa\ no\ Nushi\ Tsuri\ 2\ \(Japan\).sfc

`src/rom/` and `src/out/` are git-ignored, so a ROM or patched output can't be committed by accident.

## 3. Build

From `src/`:

    python3 build/build_patch2.py

This writes:
* `out/knt2_en.ips`, the patch;
* `out/knt2_en.sfc`, the patched ROM, for testing only. Don't distribute it.

Expected results:

| | |
|---|---|
| `out/knt2_en.ips` | 538,367 bytes, identical to `patches/KawaNoNushiTsuri2_EN_v1.3.ips` |
| Patched ROM size | 2,097,152 bytes |
| Patched ROM CRC32 | `8F2E0D10` |
| Patched ROM SHA-1 | `e8c94a106e9aafb5d85cb67b2b6266a474f31c47` |
| Patched ROM MD5 | `e3b152d65f862fcde556ae04ba5e2d47` |

The last line printed should be `ok strings 1003 ips 538367`. Every patch module checks the original bytes before it writes, so a wrong ROM or a changed address stops the build with an assertion instead of producing a broken patch.

## 4. Editing the script

There are two ways to change the text.

**Using the spreadsheet** (easiest). It shows the Japanese and English side by side, with the limit for each line:

    python3 build/script_io.py export out/script.xlsx    # edit in Excel or LibreOffice
    python3 build/script_io.py import out/script.xlsx    # checks every line, then writes build/user_edits.py
    python3 build/build_patch2.py

The import checks:
* characters the font can't draw;
* broken insert codes (`{CD}`, `{D8}` and the others);
* line widths;
* the 5-line postcard limit;
* Fishing Note wrapping;
* name lengths.

If anything fails, it lists the problems and leaves the old edits in place. `script/SuperLegendOfTheRiverKing_script_v1.2.xlsx` is the workbook as it stood for v1.2/v1.3.

**Editing the Python sources directly:** `build/translations.py`, `tr_batch2.py` and `tr_batch3.py` (dialogue by string id), `zones_en.py` (names) and `fish_desc_en.py` (Fishing Note descriptions). `user_edits.py` is applied last and overrides them all.

After changing text, refresh the plain-text copies in `script/`:

    python3 tools/export_script_csv.py

## 5. Other useful commands (from `src/`)

| Command | What it does |
|---|---|
| `python3 tools/dump_script.py` | Re-dumps the Japanese script from the ROM to `out/script.json`. This should match `script/script.json` exactly |
| `python3 tools/reinsert.py` | Round-trips the original script. It should report `round trip identical: True` |
| `python3 tools/sim.py` | Runs the game's own dialogue routine in the 65816 interpreter and renders a text box to `out/` |
| `KNT2_REG_IPS=old.ips python3 tools/regression.py` | Renders every string with an old patch and with the current build, and lists the ones that changed |
| `python3 tools/export_assets.py` | Re-renders the fonts and before/after graphics sheets in `gfx/` from the latest build |
| `python3 tools/glossary_gen.py && python3 tools/glossary_build.py` | Rebuilds `docs/glossary.{csv,xlsx,html}` |
| `python3 tools/dis65816.py <rom> <hex offset> <count>` | Disassembles 65816 code |

## 6. Where things are

| Folder | Contents |
|---|---|
| `build/` | The patch modules. `build_patch2.py` runs them in order, and each module's docstring says what it patches. `paths.py` holds every file location |
| `tools/` | Analysis tools: the disassembler, the 65816 interpreter and simulators, the script dumper and reinserter, the kanji matcher and the graphics finders (`tools/gfx/`). `tools/experiments/` has one-off scripts kept for reference |
| `script/` | `script.json` (raw dump), `strings.csv`/`.json` (one row per string: id, location, Japanese, English, limits, notes), `names.csv`, `fish_notes.csv`, the v1.2 workbook |
| `tables/` | `knt2_single_byte.tbl`, `knt2_kanji.tbl`, `kanji_overrides.txt` |
| `gfx/` | `fonts/source` (input fonts with licences), `fonts/made` (the fonts made for this patch), `logo/` (title logo art and template), `sheets/` (before/after sheets of every replaced graphic) |
| `data/` | `zones.pkl` (name-list ranges), `match_res2.pkl` (kanji font-matching results), `usage.pkl` (kanji usage contexts), and `dumps/` (Mesen-S VRAM/CGRAM/WRAM dumps of the screens used during development) |

## Notes

* **`build/logo_art.py`** draws the earlier generated logo. It's only used if `gfx/logo/logo_custom.png` is missing, and it needs the Poppins font, which isn't included (SIL OFL; get it from Google Fonts into `gfx/fonts/source/`).
* **`build/ui_hooks.py`** is an earlier approach to the window labels (v0.9) and isn't used by the build. It's kept for reference.
* **Patch format:** the IPS includes the whole expanded 512 KB region, which is why it's large. A BPS made from `out/knt2_en.sfc` would be smaller and adds checksum validation.
