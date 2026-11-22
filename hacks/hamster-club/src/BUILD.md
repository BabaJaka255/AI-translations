# Building the Hamster Club English patch

This folder rebuilds `patches/HamsterClub_EN_v0.12.bps` from a clean ROM. The build was checked byte for byte
on 2026-11-22: a fresh copy of this folder plus the original ROM gave the published BPS exactly.

## Requirements
- Python 3.10 or newer (tested with 3.13).
- `pip install -r toolkit/requirements.txt` (only Pillow is needed for the build).
- For the art tools only: `pip install pyboy` (tested with PyBoy 2.9.0; headless Game Boy Color emulator).

The toolkit (`rhtk`, the project's own romhacking CLI) is included in `toolkit/`. The tools look for it there,
or in the folder named by the `RHTK` environment variable.

## The ROM
Put your own dump at `src/rom/original.gbc` (this folder is git-ignored):

| | |
|---|---|
| Game | Hamster Club (Japan), GB/GBC dual mode, header title `HAMSTERCLUBAJNJ` |
| Size / header | 2,097,152 bytes, no copier header |
| CRC32 | `8A4D86A0` |
| SHA-1 | `6ab81c4dec3263502a1781b600218285836c5302` |

## Build
From `src/`:
```sh
sh toolkit/rhtk.sh build
```
It inserts every script block from `script/*.json` (repointing into the expanded ROM where text grew), inserts
the graphics listed in `project.json` `gfx` (English font, redrawn art in `gfx/edit/`), applies the code and
graphics IPS files in `patches/`, fixes the header and global checksums, and writes `build/`:

| Output | Size | CRC32 | SHA-1 |
|---|---|---|---|
| `build/hamster-club-gbc-en.gbc` | 4,194,304 | `A1F37DD7` | `f9b36061ab4e1a1f3f0d173cae2bcc8267a59335` |
| `build/hamster-club-gbc-en.bps` | 64,047 | | identical to `patches/HamsterClub_EN_v0.12.bps` |

Run `sh toolkit/rhtk.sh qa` before a build after any script change; it must show 0 errors (one expected warning,
entry 0178, which is `????` in the original too).

## Regenerating the inputs
The build itself only reads committed files. These tools regenerate those files; all of them were rerun on
2026-11-22 and gave identical output, except where noted.

| Tool | Writes | Notes |
|---|---|---|
| `tools/hc_tr.py script/events_en.txt` | `script/events.json` `en` fields | The event script is written in `events_en.txt` (format in the tool's docstring); the tool word-wraps it to the 18x2 box and enforces the "only punctuation in column 18 of line 2" rule. |
| `tools/make_font.py` | `gfx/edit/font.png` | English font over the kana tiles. |
| `tools/make_keyboard.py` | `patches/keyboard.ips` | English name-entry screen. |
| `tools/make_homemenu.py` | `patches/homemenu.ips` | Home menu labels (they are tiles, not text). |
| `tools/make_hacks.py` | `patches/hacks.ips` | Small code changes (age line, etc.). |
| `tools/make_roomlabels.py` | `patches/roomlabels.ips` | Room and cage captions. |
| `tools/make_banners.py` | `patches/banners.ips` | Contest entry banners. |
| `tools/make_contest.py` | `patches/contest.ips` | Contest text built by code, scoreboards, stamps. |
| `tools/make_art.py [item ...]` | `gfx/edit/art/*.png` | Needs PyBoy and the save states in `gfx/states/`. Every item reproduces byte for byte **except `title` and `boot`**, whose states (`boot_240.state`, `boot_1080.state`) were not kept. To redo those two, boot the patched ROM in PyBoy, save states at frames 240 and 1080 into `gfx/states/boot/`, or set `HC_STATES`. |
| `tools/make_jp_tbl.py` | `tables/jp.tbl` | From the font. |
| `tools/textscan.py` | report | Scans the built ROM for Japanese text the patch does not touch. |

## Script format
`script/<block>.json` holds one entry per string: `id`, `offset` (ROM file offset), `length` (original bytes),
`pointers`, `jp` (original), `en` (translation) and `notes`. Box limits per block are in `project.json`
(`box`: `max_chars`, `max_lines`, line and page tokens). Control codes are written as tokens: `<br>` line,
`<clr>` new page, `<wait>` button wait, `<name NN>` inserted name. Event-script entries also carry `scene` and `face`.
Edit `en` and `notes` only; for the event script edit `events_en.txt` and rerun `hc_tr.py`.

## Folder map
- `tools/` game-specific build, insertion and art tools; `toolkit/` the general `rhtk` toolkit (MIT).
- `script/` the text, `tables/` the .tbl character maps.
- `gfx/orig/` ripped original graphics (with `gfx/orig/art/README.md`, what each piece of lettering says),
  `gfx/edit/` the English versions the build inserts, `gfx/demo/` the two KOFF demo styles and a before/after sheet,
  `gfx/states/` PyBoy save states used by the art tools (RAM/VRAM only, no ROM data).
- `data/text-candidates.txt` raw output of an early text scan.
