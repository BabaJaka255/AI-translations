# Umi no Nushi Tsuri toolkit

English translation work for *Umi no Nushi Tsuri* (SFC, Rev 1), built on the River King toolkit
(the *Kawa no Nushi Tsuri 2* patch). The engine is the same; see `UMI_NOTES.md` for what moved.

The ROM is not included. Put `Umi no Nushi Tsuri (Japan) (Rev 1).sfc` (CRC32 `C985F568`, no header)
in `rom/`, or set `UMI_ROM`.

    pip install pillow numpy
    python3 analysis/reinsert.py       # sanity check: byte-identical round trip
    python3 analysis/dump_script.py    # writes out/script.json and out/script_dump.txt (needed by the build)
    python3 build/build_patch.py       # writes out/umi_en.sfc and out/umi_en.ips

Testing without an emulator window: `pip install stable-retro` (bundles snes9x), then

    python analysis/emu_drive.py out/umi_en.sfc shot_ "wait:400 press:START wait:120 press:START wait:120 press:A wait:90 shot:menu"

| Path | Contents |
|---|---|
| `build/umilib.py` | addresses, tables, decoder, binary-record detection |
| `build/umi_single_byte.tbl`, `build/umi_kanji.tbl` | text tables (all 954 kanji glyphs checked by eye) |
| `build/build_patch.py` | 32 Mbit expansion, ASCII font, string relocation, text hooks, checksum, IPS |
| `build/translations.py` | the English script (id -> text) |
| `analysis/` | disassembler, script dump, reinsert, graphics loader scan, pointer-table finder, kanji matcher, emulator driver |
