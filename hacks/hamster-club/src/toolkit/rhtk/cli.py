"""rhtk: romhacking and translation toolkit.

Run `python3 -m rhtk --help` from the toolkit folder, or put the folder on
PYTHONPATH. Every subcommand prints what it did; nothing writes to the
original ROM file.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import zlib

from . import compress, disasm, gfx, patch, qa, rominfo, search
from .address import Mapper
from .script import dump_block, insert_block, load_script, save_script
from .table import Table

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "templates", "game-project")
EXTS = {"nes": ".nes", "snes": ".sfc", "gb": ".gb", "gbc": ".gbc", "gba": ".gba", "nds": ".nds",
        "megadrive": ".md"}


def _int(v):
    return int(v, 0) if isinstance(v, str) else v


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _write(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        with open(self.path("project.json"), encoding="utf-8") as f:
            self.cfg = json.load(f)

    def path(self, *p):
        return os.path.join(self.root, *p)

    def rom(self) -> bytes:
        data = _read(self.path(self.cfg["rom"]))
        want = self.cfg.get("rom_crc32")
        got = f"{zlib.crc32(data):08X}"
        if want and want.upper() != got:
            sys.exit(f"ROM CRC32 is {got} but project.json expects {want}. "
                     f"Use the clean dump listed in notes/rom.md.")
        return data

    def table(self, block, for_insert=False):
        key = "insert_table" if for_insert else "table"
        p = block.get(key) or self.cfg.get(key) or block.get("table") or self.cfg.get("table")
        return Table.load(self.path(p))

    def blocks(self, only=None):
        bs = self.cfg.get("blocks", [])
        if only:
            bs = [b for b in bs if b["name"] in only]
            if not bs:
                sys.exit(f"no block named {only}")
        return bs

    def script_path(self, block):
        return self.path("script", f"{block['name']}.json")


# ---------------------------------------------------------------- commands

def cmd_info(a):
    data = _read(a.rom)
    print(json.dumps({**rominfo.hashes(data), **rominfo.detect(data, a.rom)}, indent=1))


def cmd_init(a):
    dest = os.path.abspath(a.dest)
    if os.path.exists(dest):
        sys.exit(f"{dest} already exists")
    shutil.copytree(TEMPLATE, dest)
    cfg_path = os.path.join(dest, "project.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["name"] = os.path.basename(dest)
    if a.rom:
        data = _read(a.rom)
        info = rominfo.detect(data, a.rom)
        # uploads often arrive without an extension; emulators want one
        ext = os.path.splitext(a.rom)[1] or EXTS.get(info["platform"], ".bin")
        shutil.copy(a.rom, os.path.join(dest, "rom", "original" + ext))
        cfg.update(rom=f"rom/original{ext}", rom_crc32=f"{zlib.crc32(data):08X}",
                   platform=info["platform"], output=f"build/{cfg['name']}-en{ext}")
        if info["platform"] in rominfo.CHECKSUM_PLATFORMS:
            # a bad header checksum stops a real Game Boy from booting
            cfg["checksum"] = {"platform": info["platform"], "mapping": info.get("mapping", "lorom")}
        with open(os.path.join(dest, "notes", "rom.md"), "a", encoding="utf-8") as f:
            f.write(f"\n## Source ROM\n\n```\n{json.dumps({**rominfo.hashes(data), **info}, indent=1)}\n```\n")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    print(f"created {dest}")


def cmd_search(a):
    data = _read(a.rom)
    order = search.KANA_ORDERS.get(a.order) if a.order else None
    hits = list(search.relative_search(data, a.word, order, a.width, max_hits=a.max))
    for off, val in hits:
        print(f"0x{off:06X}  first char = 0x{val:0{2 * a.width}X}")
    if hits and a.tbl:
        with open(a.tbl, "w", encoding="utf-8") as f:
            f.write(search.table_guess(a.word, hits[0][1], order, a.width))
        print(f"wrote starter table from first hit to {a.tbl}")
    if not hits:
        print("no hits: try another --order, --width 2, or a different word", file=sys.stderr)


def cmd_sjis(a):
    data = _read(a.rom)
    for off, text in search.find_sjis(data, a.min):
        print(f"0x{off:08X}\t{text}")


def cmd_decode(a):
    data = _read(a.rom)
    text, n = Table.load(a.table).decode(data, _int(a.offset), stop_at_end=False, limit=_int(a.length))
    print(text)


def cmd_dump(a):
    p = Project(a.project)
    rom = p.rom()
    for b in p.blocks(a.block):
        out = p.script_path(b)
        script = dump_block(rom, b, p.table(b), root=p.root)
        if os.path.exists(out) and not a.force:
            # keep existing translations, refresh source text and offsets
            old = {e["id"]: e for e in load_script(out)["entries"]}
            for e in script["entries"]:
                if e["id"] in old:
                    e["en"] = old[e["id"]].get("en", "")
                    e["notes"] = old[e["id"]].get("notes", "")
        save_script(out, script)
        print(f"{b['name']}: {len(script['entries'])} strings -> {os.path.relpath(out)}")


def _apply_gfx(p, rom):
    for g in p.cfg.get("gfx", []):
        png = p.path(g["png"])
        if not os.path.exists(png):
            continue
        from PIL import Image
        data = gfx.pack(Image.open(png), g["format"], g.get("count"), g.get("order", "linear"))
        off = _int(g["offset"])
        if g.get("compression") == "lz10":
            old_size = compress.lz10_decompress(rom, off)[1]
            data = compress.lz10_compress(data)
            if len(data) > old_size:
                sys.exit(f"gfx {g['name']}: compressed to {len(data)} bytes, original slot is "
                         f"{old_size}. Move it to free space and repoint.")
        rom[off:off + len(data)] = data
        print(f"gfx {g['name']}: inserted {len(data)} bytes at 0x{off:X}")


def cmd_build(a):
    p = Project(a.project)
    orig = p.rom()
    rom = bytearray(orig)
    if p.cfg.get("expand_to"):
        rom.extend(b"\xFF" * (_int(p.cfg["expand_to"]) - len(rom)))
        note = rominfo.set_rom_size(rom, p.cfg.get("platform", ""))
        if note:
            print(f"expanded to 0x{len(rom):X}: {note}")
    for b in p.blocks(a.block):
        sp = p.script_path(b)
        if not os.path.exists(sp):
            print(f"{b['name']}: no script file, skipped")
            continue
        st = insert_block(rom, b, load_script(sp), p.table(b, for_insert=True), root=p.root)
        print(f"{b['name']}: {st['translated']}/{st['strings']} translated, {st['moved']} moved, "
              f"{st.get('free_left', 0)} bytes free")
    _apply_gfx(p, rom)
    for asm_patch in p.cfg.get("patches", []):  # hand-made IPS/BPS (e.g. font, VWF hacks)
        rom = bytearray(patch.apply_any(bytes(rom), _read(p.path(asm_patch))))
        print(f"applied {asm_patch}")
    cs = p.cfg.get("checksum")
    if cs:
        print("checksum:", rominfo.fix_checksum(rom, cs.get("platform", p.cfg.get("platform")),
                                                cs.get("mapping", "lorom")))
    out = p.path(p.cfg.get("output", "build/output.bin"))
    _write(out, rom)
    stem = os.path.splitext(out)[0]
    _write(stem + ".bps", patch.bps_create(orig, bytes(rom), p.cfg.get("name", "")))
    if len(rom) <= 0x1000000:
        _write(stem + ".ips", patch.ips_create(orig, bytes(rom)))
    print(f"wrote {os.path.relpath(out)} and patches")


def cmd_qa(a):
    p = Project(a.project)
    reports = []
    for b in p.blocks(a.block):
        sp = p.script_path(b)
        if not os.path.exists(sp):
            continue
        try:
            t = p.table(b, for_insert=True)
        except (OSError, TypeError):
            t = None
        r = qa.check_script(load_script(sp), t, b)
        reports.append(r)
        print(f"{r['block']}: {r['translated']}/{r['total']} translated, "
              f"{r['errors']} errors, {r['warnings']} warnings")
        for i in r["issues"][: a.limit]:
            print(f"  {i['severity']:5} {i['id']}: {i['message']}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=1)
    if any(r["errors"] for r in reports):
        sys.exit(1)


def cmd_gfx_rip(a):
    data = _read(a.rom)
    if a.lz10:
        data, _ = compress.lz10_decompress(data, _int(a.offset))
        off = 0
    else:
        off = _int(a.offset)
    pal = None
    if a.pal_offset:
        pal = gfx.read_palette_bgr555(_read(a.pal_file or a.rom), _int(a.pal_offset),
                                      1 << gfx.BPP[a.format])
    count = _int(a.count) if a.count else (len(data) - off) // gfx.tile_bytes(a.format)
    img = gfx.rip(data, off, count, a.format, a.width, pal, a.order)
    from PIL.PngImagePlugin import PngInfo
    meta = PngInfo()
    meta.add_text("rhtk_tiles", str(count))  # lets gfx-insert skip the padding tiles
    img.save(a.out, pnginfo=meta)
    print(f"wrote {a.out} ({count} tiles, {a.format})")


def cmd_gfx_insert(a):
    from PIL import Image
    rom = bytearray(_read(a.rom))
    data = gfx.pack(Image.open(a.png), a.format, _int(a.count) if a.count else None, a.order)
    off = _int(a.offset)
    rom[off:off + len(data)] = data
    _write(a.out, rom)
    print(f"inserted {len(data)} bytes at 0x{off:X} -> {a.out}")


def cmd_lz(a):
    data = _read(a.file)
    if a.action == "scan":
        for off, size, used in compress.scan_lz10(data):
            print(f"0x{off:08X}  {used:6d} -> {size:6d} bytes")
    elif a.action == "unpack":
        fn = {0x10: compress.lz10_decompress, 0x11: compress.lz11_decompress,
              0x30: compress.rle_decompress}[data[_int(a.offset)]]
        out, used = fn(data, _int(a.offset))
        _write(a.out, out)
        print(f"{used} compressed bytes -> {len(out)} bytes in {a.out}")
    else:
        _write(a.out, compress.lz10_compress(data))
        print(f"wrote {a.out}")


def cmd_patch(a):
    src = _read(a.original)
    if a.action == "make":
        dst = _read(a.modified)
        fn = patch.bps_create if a.out.lower().endswith(".bps") else patch.ips_create
        _write(a.out, fn(src, dst))
    else:
        _write(a.out, patch.apply_any(src, _read(a.modified)))
    print(f"wrote {a.out}")


def cmd_fixsum(a):
    rom = bytearray(_read(a.rom))
    platform = a.platform or rominfo.detect(rom, a.rom)["platform"]
    print(rominfo.fix_checksum(rom, platform, a.mapping))
    _write(a.out or a.rom, rom)


def cmd_disasm(a):
    data = _read(a.rom)
    base = _int(a.address) if a.address else None
    for addr, raw, mn, ops in disasm.disassemble(data, _int(a.offset), _int(a.length), a.arch, base):
        print(f"{addr:08X}  {raw:<24} {mn} {ops}")


def cmd_xref(a):
    data = _read(a.rom)
    mapping = json.loads(a.mapping) if a.mapping.startswith("{") else {"type": a.mapping}
    sizes = (2, 3, 4)
    if mapping["type"] == "elf":
        from . import ps2
        mapping.setdefault("segments", ps2.elf_segments(data))
        sizes = (4,)
    for off, size in disasm.xrefs(data, _int(a.target), mapping, sizes=sizes, endian=a.endian,
                                  ptr_or=_int(a.ptr_or)):
        print(f"0x{off:08X}  {size}-byte pointer")
    if mapping["type"] == "elf":
        for hi, lo, op in ps2.mips_hilo_refs(data, mapping["segments"], Mapper(mapping).to_ptr(_int(a.target))):
            print(f"0x{hi:08X}  lui + {op} at 0x{lo:08X}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rhtk", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("info", help="identify a ROM and print hashes/header")
    s.add_argument("rom"); s.set_defaults(fn=cmd_info)

    s = sub.add_parser("init", help="create a new game project from the template")
    s.add_argument("dest"); s.add_argument("--rom"); s.set_defaults(fn=cmd_init)

    s = sub.add_parser("search", help="relative search for a word to discover the text encoding")
    s.add_argument("rom"); s.add_argument("word")
    s.add_argument("--order", choices=list(search.KANA_ORDERS))
    s.add_argument("--width", type=int, default=1)
    s.add_argument("--max", type=int, default=50)
    s.add_argument("--tbl", help="write a starter table from the first hit")
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("sjis", help="list Shift-JIS text runs (DS/PSP/PS1/PS2/PC games)")
    s.add_argument("rom"); s.add_argument("--min", type=int, default=4); s.set_defaults(fn=cmd_sjis)

    s = sub.add_parser("decode", help="decode raw bytes with a table (for exploring)")
    s.add_argument("rom"); s.add_argument("table"); s.add_argument("offset")
    s.add_argument("--length", default="0x200"); s.set_defaults(fn=cmd_decode)

    for name, fn, hlp in (("dump", cmd_dump, "dump script blocks to script/*.json"),
                          ("build", cmd_build, "insert script + gfx, write ROM and BPS/IPS"),
                          ("qa", cmd_qa, "check translations for errors")):
        s = sub.add_parser(name, help=hlp)
        s.add_argument("project", nargs="?", default=".")
        s.add_argument("--block", action="append")
        if name == "dump":
            s.add_argument("--force", action="store_true", help="discard existing translations")
        if name == "qa":
            s.add_argument("--limit", type=int, default=50)
            s.add_argument("--json")
        s.set_defaults(fn=fn)

    s = sub.add_parser("gfx-rip", help="tiles -> indexed PNG")
    s.add_argument("rom"); s.add_argument("offset"); s.add_argument("format", choices=list(gfx.BPP))
    s.add_argument("out"); s.add_argument("--count"); s.add_argument("--width", type=int, default=16)
    s.add_argument("--pal-offset"); s.add_argument("--pal-file")
    s.add_argument("--lz10", action="store_true", help="data at offset is LZ10 compressed")
    s.add_argument("--order", choices=gfx.ORDERS, default="linear",
                   help="tile layout on the sheet (obj8x16: GB 8x16 sprite pairs)")
    s.set_defaults(fn=cmd_gfx_rip)

    s = sub.add_parser("gfx-insert", help="indexed PNG -> tiles, written into a copy of the ROM")
    s.add_argument("rom"); s.add_argument("png"); s.add_argument("offset")
    s.add_argument("format", choices=list(gfx.BPP)); s.add_argument("out"); s.add_argument("--count")
    s.add_argument("--order", choices=gfx.ORDERS, default="linear")
    s.set_defaults(fn=cmd_gfx_insert)

    s = sub.add_parser("lz", help="GBA/NDS LZ10/LZ11/RLE: scan, unpack, pack")
    s.add_argument("action", choices=["scan", "unpack", "pack"]); s.add_argument("file")
    s.add_argument("--offset", default="0"); s.add_argument("--out")
    s.set_defaults(fn=cmd_lz)

    s = sub.add_parser("patch", help="make or apply IPS/BPS patches")
    s.add_argument("action", choices=["make", "apply"]); s.add_argument("original")
    s.add_argument("modified", help="modified ROM (make) or patch file (apply)"); s.add_argument("out")
    s.set_defaults(fn=cmd_patch)

    s = sub.add_parser("fixsum", help="fix header checksum")
    s.add_argument("rom"); s.add_argument("--platform"); s.add_argument("--mapping", default="lorom")
    s.add_argument("--out"); s.set_defaults(fn=cmd_fixsum)

    s = sub.add_parser("disasm", help="disassemble with Capstone (6502/65816/ARM/Thumb/MIPS/M68K/SH2/x86)")
    s.add_argument("rom"); s.add_argument("offset"); s.add_argument("arch", choices=list(disasm.ARCHS))
    s.add_argument("--length", default="0x100"); s.add_argument("--address", help="CPU address of offset")
    s.set_defaults(fn=cmd_disasm)

    s = sub.add_parser("xref", help="find pointers to a file offset (locates pointer tables)")
    s.add_argument("rom"); s.add_argument("target")
    s.add_argument("--mapping", default="linear",
                   help='linear, gba, snes-lorom, snes-hirom, elf (also finds MIPS lui/addiu pairs), or a JSON mapping like \'{"type":"bank","bank":3}\'')
    s.add_argument("--endian", default="little"); s.add_argument("--ptr-or", default="0")
    s.set_defaults(fn=cmd_xref)

    from . import ps2cli
    ps2cli.register(sub)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
