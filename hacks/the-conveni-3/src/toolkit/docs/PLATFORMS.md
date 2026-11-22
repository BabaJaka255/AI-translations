# Per-platform tool choices

**In this cloud workspace** we have Python, Pillow, Capstone, ndspy, UnityPy
(`pip install -r requirements.txt`), Java (so Ghidra works), and `rhtk`. PyBoy
(`pip install pyboy`) runs GB/GBC games headless here. Emulators
with debuggers run on the project lead's machine. When a step needs one (breakpoints,
watching text draw), ask the project lead to run it, or use a remote session on their
computer.

Tool names change over time. Check that a tool is still maintained
before you depend on it.

## Cartridge era

| Platform | Tiles | Pointers (typical) | Debugger (desktop) | Assembler | Notes |
|---|---|---|---|---|---|
| NES / Famicom | `2bpp_nes` (CHR) | 16-bit LE, banked; `{"type":"bank","bank_size":"0x4000","window":"0x8000","header":16}` (match the mapper) | Mesen, FCEUX | asm6f, ca65 | Fonts are often in CHR-ROM. Space is tight, so expand by changing to a bigger mapper (e.g. MMC3) or use DTE |
| Game Boy / Color | `2bpp_gb` | 16-bit LE into the `0x4000` window, `{"type":"bank","bank":N}` | BGB, Emulicious, SameBoy | rgbds | `rhtk disasm <rom> <off> sm83`. PyBoy (`pip install pyboy`) runs games headless for screenshots, VRAM dumps and save states. `expand_to` also updates header byte 0x148 (MBC5 goes to 8 MiB). Fix checksum `gb` |
| SNES / Super Famicom | `2bpp_gb`, `4bpp_snes` | 16-bit + implied bank (`ptr_or`) or 24-bit; `snes-lorom` / `snes-hirom` | Mesen 2, bsnes-plus | asar | VWF is standard practice. Custom LZ compression is common. `rhtk disasm <rom> <off> 65816` (M/X flag width can confuse it). Strip any 512-byte copier header before you start |
| Mega Drive / Genesis | `4bpp_md` | 32-bit **big endian**, linear | BlastEm, Exodus, Gens KMod | vasm, asm68k | Set `"endian": "big"`. Fix checksum `megadrive`. Nemesis/Kosinski compression is common in Sega first-party games |
| PC Engine HuCard | `4bpp_snes`-like planar (check) | 16-bit LE, banked 8 KiB | Mesen 2, Mednafen | pceas | CD-ROM² games follow the disc route |
| Game Boy Advance | `4bpp_gba`, `8bpp` | 32-bit LE, `gba` mapping | mGBA (with gdb), no$gba | armips | BIOS LZ10/RLE everywhere: `rhtk lz scan`. Code is Thumb/ARM: `rhtk disasm <rom> <off> thumb`. Fix checksum `gba`. Can expand up to 32 MiB |

## Disc and file-system era

Extract the files first, change them, then rebuild the image or file system.

| Platform | Unpack / repack | Text and graphics formats | Debugger |
|---|---|---|---|
| Nintendo DS | `ndspy` (Python), ndstool, Tinke | BMG text, NFTR fonts, NCGR/NCLR/NSCR graphics, NARC archives, LZ10/LZ11 (`rhtk lz`) | melonDS, no$gba |
| Nintendo 3DS | 3dstool, ctrtool; mods via LayeredFS | MSBT/MSBP text, BCFNT fonts, BCLIM, SARC/ZSTD | Azahar (Citra fork) |
| PlayStation | dumpsxiso / mkpsxiso | Shift-JIS in executables and data files, TIM images, custom archives | DuckStation, no$psx, Mednafen |
| PlayStation 2 | `rhtk ps2` (info, ls, extract, scan, patch, AFS, TIM2, ELF xref); see docs/PS2.md | Shift-JIS, CRI middleware (CPK/ACB/USM), TIM2 textures | PCSX2 debugger (needs the project lead's BIOS) |
| PSP | UMD-Gen, or extract the ISO; CRI CPK tools | Shift-JIS/UTF-8, GIM images, PGF fonts | PPSSPP debugger |
| Saturn | ISO tools; SH-2 code (`rhtk disasm <rom> <off> sh2`) | Custom | Mednafen, Yabause |
| Switch | Dump from your own console (nxdumptool), hactool; mods through LayeredFS | MSBT, BFFNT, SARC, plus engine formats below | Ryujinx-family emulators |

## Engine-based games (modern console and PC)

Most new games use an engine. Don't disassemble them. Use the engine's asset tools:

| Engine | Tools | Where the text is |
|---|---|---|
| Unity | UnityPy (scriptable here), AssetStudio, UABEA | TextAsset, MonoBehaviour fields, I2 Localization sheets, TMP font assets |
| Unreal | FModel, repak, UAssetGUI, UnrealLocres | `.locres` files are made for localization, and adding an `en` culture is often enough |
| RPG Maker MV/MZ | Plain JSON in `data/` | `Map*.json`, `CommonEvents.json`. Translator++ is the usual GUI |
| RPG Maker XP/VX/Ace | rvpacker-txt, RPGMakerTrans | rxdata/rvdata2 (Ruby Marshal) |
| Ren'Py | unrpa, unrpyc | Has built-in `tl/` translation support: `renpy.sh . translate english` |
| KiriKiri (TVP) | KrkrExtract, xp3 tools | `.ks` scenario scripts, usually Shift-JIS or UTF-16 |
| Godot | gdsdecomp | `.translation`/CSV, `.pck` |
| CRI middleware | CriPakTools / YACpkTool | CPK archives (any platform) |

## Choosing an approach for a new game

1. Is there an existing fan translation or documented format (romhacking.net
   archives, datacrystal.tcrf.net, TCRF)? Read it first. Never reuse someone
   else's translation text without permission. Their documentation of the
   hacking is fine to use with credit.
2. Use a known format tool → extract with it, then convert to our script JSON (one entry per
   message, same field layout) so `rhtk qa` and the translation workflow still
   apply. Put the converter in the game folder under `tools/`.
3. Custom engine with custom encoding → follow the full workflow (table, xref, dump).
