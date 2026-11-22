# Romhacking and translation toolkit (`rhtk`)

A shared foundation for taking Japanese games apart, pulling out their script and
graphics, and putting them back together in English. Every game project in this
workspace uses the same layout, tools and style guide, so any thread can pick up
any game.

## Layout

```
<workspace>/
  romhack-toolkit/        this toolkit (code, docs, template)
    rhtk/                 Python package (CLI: sh rhtk.sh)
    docs/WORKFLOW.md      the nine phases from ROM to patch
    docs/PLATFORMS.md     which tools to use for each console or engine
    docs/PS2.md           PS2 disc workflow (extract, scan, patch, xdelta)
    docs/STYLE_GUIDE.md   translation and localization rules
    docs/TRANSLATING.md   the translation process and its passes
    templates/game-project/
    tests/                python3 -m unittest discover -s tests
  games/<game-id>/        one folder per game (made by `rhtk init`)
    project.json          ROM, tables, pointer blocks, gfx, build settings
    rom/                  the source ROM the project lead supplies (never shared)
    tables/jp.tbl en.tbl  decode and encode tables
    script/<block>.json   dumped script, with translations filled into "en"
    gfx/orig/ gfx/edit/   ripped graphics and edited versions to reinsert
    notes/                rom.md, glossary.md, characters.md, progress.md
    build/                patched ROM + .bps/.ips (only the .bps is released)
```

`<game-id>` is short, lowercase and ASCII, with the platform last, e.g. `mother-fc`.

## Quick start

```sh
TK=<workspace>/romhack-toolkit
pip install -r $TK/requirements.txt        # once per session (Pillow, Capstone, ndspy, UnityPy)
# the project mount ignores the exec bit, so run the wrapper through sh
rhtk() { sh $TK/rhtk.sh "$@"; }
rhtk info <workspace>/uploads/hearth/<file>
rhtk init <workspace>/games/<game-id> --rom <workspace>/uploads/hearth/<file>
cd <workspace>/games/<game-id>
rhtk search rom/original.sfc たたかう --order hira_jis --tbl tables/jp.tbl
rhtk xref rom/original.sfc 0x1A2B3C --mapping snes-lorom
#   ...add the pointer blocks to project.json...
rhtk dump
#   ...translate script/*.json...
rhtk qa
rhtk build
```

## Commands

| Command | Purpose |
|---|---|
| `info` | Identify the platform and header, print CRC32/MD5/SHA-1 |
| `init` | Create a game folder from the template (copies ROM, pins CRC32) |
| `search` | Relative search (Latin or kana) to discover a custom encoding. `--tbl` writes a starter table |
| `sjis` | List Shift-JIS text runs (DS, PSP, PS1/2, PC) |
| `decode` | Decode raw bytes at an offset with a table |
| `xref` | Find pointers to an offset, to locate pointer tables (linear, gba, snes-lorom/hirom, banked, elf with MIPS lui/addiu pairs) |
| `disasm` | Disassemble: 6502, 65816, ARM, Thumb, MIPS, M68K, SH2, x86 (Capstone), and SM83 for GB/GBC (built in). Arch is positional: `disasm rom 0x150 sm83 --address 0x150` |
| `dump` | Pointer, range and plugin blocks → `script/*.json` (keeps existing translations). `"mode": "plugin"` hands a bytecode script to a game's own `tools/*.py` (see `rhtk/script.py`) |
| `qa` | Check control codes, leftover Japanese, encodability, line/box limits, typos |
| `build` | Insert script (repoints into free space, keeps bank limits) + gfx + ASM patches, fix checksum, write BPS/IPS |
| `gfx-rip` / `gfx-insert` | Tiles ⇄ indexed PNG: 1bpp, 2bpp GB/SNES, 2bpp NES, 4bpp SNES/GBA/MD, 8bpp, BGR555 palettes, LZ10 |
| `lz` | GBA/NDS LZ10/LZ11/RLE scan, unpack, pack |
| `patch` | Make or apply IPS/BPS |
| `fixsum` | Fix the header checksum for GB/GBC, GBA, SNES, Mega Drive (`init` turns this on in project.json for those platforms) |
| `ps2 ...` | PS2/PS1 disc images: info, ls, extract, scan for text, patch files back in, AFS, TIM2, ELF segments, xdelta release (docs/PS2.md) |

## Table file format

Thingy-style, with extensions: `XX=あ`, multi-byte keys `8140=　`, `/FF=<end>` (end
of string), `*FE=<br>` (line break), `$F0=<name>,1` (control code with 1 parameter
byte, shown as `<name 02>`), `;` comment lines. Unknown bytes appear as `[XX]` and
round-trip unchanged. Put preferred spellings first: the first mapping of
a string wins when encoding.

## Ground rules

- the project lead supplies every ROM or disc image. We don't download game data.
- Only BPS patches ever leave this workspace. ROMs and patched builds stay in
  `rom/` and `build/`.
- Never edit `rom/`. Everything is rebuilt from the original by `rhtk build`.
- Write anything learned about a game into that game's `notes/`, so the next
  thread doesn't have to rediscover it.
- Format-specific scripts for one game go in `games/<id>/tools/`. Anything useful
  for two or more games moves into `rhtk` and gets a test.
