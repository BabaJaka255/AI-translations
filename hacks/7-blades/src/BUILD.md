# Building the 7 Blades English patch (Japanese disc)

**Status: unverified.** This source has not yet been rebuilt into the full disc image and compared with the
published patch, because the Japanese disc image wasn't available when it was published. On 2026-11-22 the first two build
steps were rerun from a clean copy of this folder and completed without errors (results below), but the disc
step needs the full ISO. If you rebuild it, compare your image with the expected hashes at the end.

## Requirements
- Linux or WSL, Python 3.10+ (tested with 3.13), `pip install -r toolkit/requirements.txt` (Pillow).
- MIPS cross tools: `apt-get install gcc-mips64el-linux-gnuabi64 binutils-mips64el-linux-gnuabi64`
  (tested with Ubuntu 24.04's packages). The new code is compiled for the R5900 (`-march=r5900 -mabi=n32`).
- `xdelta3`. Optional: `pip install unicorn` (only to regenerate `code/subtitle/savefix.h`), Ghidra (scripts in
  `tools/ghidra/`), PCSX2 2.4.0 for testing (`toolkit/scripts/pcsx2-setup.sh`, `tools/emu.sh`).

The toolkit (`rhtk`) is included in `toolkit/`.

## The discs
You need **both** releases; the European one supplies the English text, font, images and subtitle scripts.
Put everything in the git-ignored `src/rom/`:

| | Japanese (target) | European (source of the English) |
|---|---|---|
| Serial | SLPM-65008 | SLES-50109 |
| Image | 4,596,269,056 bytes, CRC32 `CC8D415A`, SHA-1 `faa45d3fa1d382b6f78ad31463981382885f24c4` | 4,628,742,144 bytes, CRC32 `1E348FC5`, SHA-1 `1919d69221124fd5e89a90481290b8b980547d56` |
| Put at | `rom/jp.iso`, plus its files extracted to `rom/jp/` | its files extracted to `rom/pal/` |

```sh
cd src
sh toolkit/rhtk.sh ps2 extract rom/jp.iso rom/jp
sh toolkit/rhtk.sh ps2 extract rom/pal.iso rom/pal      # only SLES_501.09 and EFF/ are read
```
Files read: `rom/jp/SLPM_650.08`, `rom/jp/EFF/PEACE.NCB`, `rom/jp/FILES.TXT`, `rom/pal/SLES_501.09`,
`rom/pal/EFF/PEACE.NCB`, `rom/pal/EFF/SUBTITLE.NCB`, and the movies inside `rom/jp.iso`.

## Build
```sh
bash tools/build_iso.sh rom/jp.iso build/7blades-en.iso
```
Steps (work files in `build/work/`):
1. `tools/b7_build_jp.py` compiles `code/subtitle/*.c` (subtitle engine, text renderer, sword effects, pressure
   attacks, options and save fixes) plus `subdata.c`, which `code/subtitle/gen_data.py` generates from the European
   SUBTITLE.NCB, ELF tables and `eu_font.rh2`. It links them as a new PT_LOAD segment at 0x6d3200, moves the heap
   start past it, patches the hook calls in the Japanese ELF and writes the English strings (`tools/b7_strings.py`,
   from the European ELF, plus three new item names).
2. `tools/b7_peace.py` rebuilds `EFF/PEACE.NCB` with the European English images (and ○/✕ swapped prompts).
3. `tools/b7_stagedata.py` gives the level data carried inside 66 movies the same image swaps (movies must not grow).
4. The ISO is copied and those files replaced (`rhtk.ps2.patch_iso`).

Make the patch: `xdelta3 -e -9 -S djw -s rom/jp.iso build/7blades-en.iso ../patches/7Blades_EN_test-2026-11-10.xdelta`.

Expected (the published patch's output): `7blades-en.iso`, 4,599,506,944 bytes, CRC32 `5395EE5E`,
SHA-1 `96474e2e3c1ecd752c4dd192d7e721d73f9ae4ea`.

Results of steps 1 and 2 from this source on 2026-11-22 (not yet compared with the release):
`SLPM_650.08` 3,236,752 bytes, MD5 `e99e837ecd002f41fe4baf44f926230a`; `PEACE.NCB` 9,578,496 bytes,
MD5 `0d0b4267f8e52c4b309f24912de497ee`.

`B7_HOOKS` (default `play,pic,send,tut,str,font,status,kills,save,fx,press,opt`) turns individual hooks on or off
for bisecting. The debug menu used for testing is described in `../docs/ENGINE_NOTES.md` ("Debug menu").

## The script
- `script/subs_pal.json`: every European movie subtitle, per movie (G0010...), in English, French and German,
  each line with `id`, `start` and `end` (frames at 30 fps; they line up with the Japanese movies) and `text`.
  The Japanese movies have no written script (voice only), so there is no Japanese column. The build reads the
  subtitles from SUBTITLE.NCB directly; this file is the readable dump (`tools/b7_sub.py`).
- In-game text (tutorial, item/weapon/food names and descriptions, hints, names) is copied at build time from the
  European ELF by `tools/b7_strings.py`, matched to the Japanese message numbers and tables. Our own English for the
  three items the European release left in Japanese is in `b7_strings.py` (`EXTRA`). Rules: '-' must be ー (0x815B)
  and ' must be ’ for eu_font.

## Other tools
`b7_lz.py`/`b7_lz.c` (the "1.\." LZ), `b7_ncb.py`, `b7_peace.py` (NCB and .r archives), `b7_rh2.py`,
`b7_rh2edit.py`, `b7_gs.py` (RH2 textures and a GS memory model), `b7_font.py`, `b7_remux.py` (level data inside PSS
movies), `b7_optfix.py` (generates `optfix.h`), `b7_savefix.py` (generates `savefix.h` by running both games' setup
routines in unicorn), `b7_elfstr.py`, `b7_dis.py`, `b7_r5900_sanitize.py`, `b7_iso_add.py`, `emu.sh`, `ghidra/`.
`code/subtitle/eu_font.rh2` is the European release's font texture, extracted (`b7_font.py` adds the ○✕△□ button glyphs, which are blank in the European font).
