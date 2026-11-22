# Building The Conveni 3 English patch

This folder rebuilds the English disc image, and from it the two xdelta patches in `../patches/`.
**Verified 2026-11-22:** a fresh copy of this folder plus the Redump disc built an ISO identical to the published
patches' output (CRC32 `A3BAF439`), and re-encoding the ISO patch as below gave the published `.xdelta` byte for byte.

## Requirements
- Linux or WSL with Python 3.10+ (tested with 3.13), `pip install -r toolkit/requirements.txt` (Pillow).
- `xdelta3` (to make or apply patches) and `7z` (to unpack the Redump archive). On Debian/Ubuntu:
  `apt-get install xdelta3 p7zip-full`.
- Optional, for testing: PCSX2 2.4.0 with your own BIOS (`toolkit/scripts/pcsx2-setup.sh`), Xvfb, xdotool, ImageMagick.

The toolkit (`rhtk`) is included in `toolkit/`. Tools find it there or through the `RHTK` environment variable.

## The disc
Use your own Redump dump and convert it to a 2048-byte-sector ISO in the git-ignored `src/rom/`:

| | |
|---|---|
| Redump file | `Conveni 3, The - Ano Machi o Dokusen seyo (Japan).bin`, MODE2/2352, 750,753,696 bytes |
| bin CRC32 / SHA-1 | `2143FE1F` / `597f58e9bef568d7ab07273210c625fd0252386d` |
| ISO (after conversion) | 653,717,504 bytes, CRC32 `E2F31095`, SHA-1 `4fa209d0a691238593adcd4738096c5bd7c5fdcd` |

```sh
cd src
sh toolkit/rhtk.sh ps2 to-iso "rom/Conveni 3, The - Ano Machi o Dokusen seyo (Japan).bin" rom/conveni3.iso
```

## Build
```sh
python3 tools/c3_build.py rom/conveni3.iso build/conveni3-en.iso --report build/report.json
```
About 15 to 25 minutes, mostly recompressing the PAC archives. The original ISO is never modified.
`build/report.json` lists any string that didn't fit (it stays Japanese); the release build has none.

Expected result: `build/conveni3-en.iso`, 656,054,272 bytes, CRC32 `A3BAF439`,
SHA-1 `cd45eacc2a16f2f502c7b19bac4e5984e41a133c`.

Make the patches. xdelta stores the input file names in its header, so the published files were made from copies
named `c3.iso` (original) and `b44.iso` (build 44):
```sh
cp rom/conveni3.iso c3.iso; cp build/conveni3-en.iso b44.iso
xdelta3 -e -9 -S lzma -B 1073741824 -s c3.iso b44.iso ../patches/Conveni3_EN_v0.9.6-beta_ISO.xdelta
xdelta3 -e -9 -S lzma -B 1073741824 -s "rom/Conveni 3, The - Ano Machi o Dokusen seyo (Japan).bin" b44.iso ../patches/Conveni3_EN_v0.9.6-beta_RedumpBin.xdelta
```
Tested with xdelta3 3.0.11. Other versions may produce different patch bytes with the same result; the check
that matters is the patched ISO's hash above.

## What the build does (tools/c3_build.py)
1. **ELF (SLPM_623.22):** space advance 15 -> 6 px; the small, large and talk fonts are rebuilt with letter-pair
   glyphs (`c3_glyphs.py`: the most common English letter pairs get one Shift-JIS code each, ranked from all the
   English in the script, so English costs about 1 byte per letter); English is written into each string's
   fixed slot; the money formatter is replaced (`c3_yen.py`: ¥230,000,000 instead of 2億3000万円); clock and date
   padding (`c3_pad.py`, new `/Qn` code: "AM 7:06"), money with commas in fixture prices (`c3_gcode.py`, new `/Gn` code), fixture-panel word wrap (`c3_wordwrap.py`), title subtitle
   (`c3_title.py`).
2. **ALLDATA.PAC:** the font texture (truefont.tex) and texture labels (`c3_gfx.py`, from `gfx/edits.json`);
   ONETEX.PAC where an edit needs it.
3. **PAC/CN3.PAC:** English written into every location of each map-data string; members recompressed (LZS).
4. **Checksums:** the ELF holds two checksum tables over 126 files; every changed file is re-summed
   (`c3pac.fix_sum`), or the game hangs on a black screen.
5. The ISO is copied and the changed files replaced (`rhtk ps2 patch`).

## The script
- `script/elf.json` (1,822 strings from the program) and `script/cn3.json` (1,083 unique strings from the map
  archive, each listing every member/offset/slot where it appears). Each entry has `id`, the location
  (`offset` and `length` for the ELF; `where` = [member, offset, slot size] and `cap` for CN3), `jp`, `en`,
  `notes`, and `skip`/`kind` for code bytes that only look like text.
- **Translations are edited in `script/tr/*.tsv`**, not in the JSON. Each line is `id<TAB>english` (or
  `japanese<TAB>english` for `addjp` files); `id!` means "no letter pairs" (strings drawn with the name font).
  `python3 tools/c3_merge.py` re-merges every TSV into the JSON in the canonical order (later files win) and runs
  the width and size checks. Always re-merge everything; adding one TSV alone once reverted the tutorial wrap.
  Set `C3_ELF` to an extracted ELF (from a built ISO, so the widths match the English fonts):
  `sh toolkit/rhtk.sh ps2 extract build/conveni3-en.iso build/disc`.
- Control codes in strings: `/n` line, `/r` soft line, `/p` page, `/w045` wait, `/k` + letter key prompt,
  `/Qn` 2-digit number, `/Gn` money with commas, `/0`-`/9` numbers, other `/X` codes (see `../docs/ENGINE_NOTES.md`). Never put `/X` codes other than `/n` in fixture
  descriptions (View Details freezes).
- Limits: slot sizes are fixed (ELF `length`, CN3 16/32/64/128/224/256/259 bytes); box widths and line counts
  per box type are in ENGINE_NOTES. `tools/c3_preview.py <built.iso>` draws every box in the game's own fonts and
  flags splits and overflows (`../docs/images/preview/`).
- Wrapping helpers: `c3_wrap_pages.py` (tutorial pages, margin 75), `c3_wrap.py`, `c3_wrap_desc.py`, `c3_wrap_qa.py`.

## Other tools
`c3_dump.py`, `c3_cn3dump.py` (the original dumps), `c3pac.py` (PAC/LZS), `c3tex.py`, `c3_texdump.py` (textures),
`c3font.py`, `font_proof.py`, `c3_ram_patch.py`, `c3_state_test.py`, `p2s.py` (PCSX2 save-state experiments),
`emu*.sh` (drive PCSX2 headless with xdotool), `tools/fonts/Inter-ExtraBold.otf` (SIL OFL, used to draw the
speech-bubble Latin letters), `tools/attic/` (an older word-wrap attempt that froze the game, kept for reference).
`data/elf_strings_scan.json` is a raw text scan of the ELF.
