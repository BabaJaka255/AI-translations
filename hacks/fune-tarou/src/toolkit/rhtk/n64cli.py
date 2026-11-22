"""`rhtk n64 ...` subcommands. See rhtk/n64.py and docs/N64.md."""
from __future__ import annotations

import json
import os
import sys

from . import n64


def _int(v):
    return int(v, 0) if isinstance(v, str) else v


def _read(p):
    with open(p, "rb") as f:
        return f.read()


def _write(p, data):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)


def c_info(a):
    print(json.dumps(n64.info(_read(a.rom)), indent=1, ensure_ascii=False))


def c_normalize(a):
    raw = _read(a.rom)
    order = n64.byte_order(raw)
    _write(a.out, n64.to_z64(raw))
    print(f"{order} -> z64: {a.out}")


def c_fixcrc(a):
    raw = _read(a.rom)
    order = n64.byte_order(raw)
    data = n64.to_z64(raw)
    out, cic, (c1, c2) = n64.fix_crc(data, _int(a.cic) if a.cic else None)
    _write(a.out or a.rom, n64.from_z64(out, order))
    print(f"CIC {cic}: CRC1 {c1:08X} CRC2 {c2:08X} -> {a.out or a.rom}")


def c_scan(a):
    data = n64.to_z64(_read(a.rom))
    rows = sorted(n64.scan_compressed(data, verify=not a.fast), key=lambda r: r["offset"])
    for r in rows:
        ok = {True: "ok", False: "BAD", None: "?"}[r["ok"]]
        print(f"0x{r['offset']:08X}  {r['kind']}  -> {r['size']:8d} bytes  {ok}")
    print(f"{len(rows)} blocks", file=sys.stderr)


def c_unpack(a):
    data = n64.to_z64(_read(a.rom))
    off = _int(a.offset)
    kind = data[off:off + 4].decode("latin-1")
    if kind not in n64.CODECS:
        sys.exit(f"no MIO0/Yay0/Yaz0 header at 0x{off:X}")
    out = n64.CODECS[kind](data, off)
    _write(a.out, out)
    print(f"{kind} 0x{off:X} -> {len(out)} bytes: {a.out}")


def c_pack(a):
    raw = _read(a.file)
    out = n64.mio0_compress(raw) if a.kind == "MIO0" else n64.yaz0_compress(raw)
    _write(a.out, out)
    print(f"{a.kind}: {len(raw)} -> {len(out)} bytes: {a.out}")


def c_text(a):
    data = n64.to_z64(_read(a.rom))
    n = 0
    for off, s in n64.text_runs(data, a.encoding, a.min_kana):
        print(f"0x{off:08X}  {s}")
        n += 1
    print(f"{n} runs", file=sys.stderr)


def c_xref(a):
    data = n64.to_z64(_read(a.rom))
    target = _int(a.target)
    if a.segment:
        segs = [tuple(_int(x) for x in s.split(":")) for s in a.segment]
    else:
        segs = [n64.boot_segment(data)]
    for off in n64.word_refs(data, target):
        print(f"0x{off:08X}  32-bit word")
    for hi, lo, op in n64.mips_hilo_refs(data, segs, target):
        print(f"0x{hi:08X}  lui + {op} at 0x{lo:08X}")


def register(sub):
    p = sub.add_parser("n64", help="N64 ROMs: byte order, header/CIC/CRC, MIO0/Yay0/Yaz0, refs (docs/N64.md)")
    s2 = p.add_subparsers(dest="n64cmd", required=True)
    s = s2.add_parser("info", help="header, byte order, CIC, whether the CRC is valid")
    s.add_argument("rom"); s.set_defaults(fn=c_info)
    s = s2.add_parser("normalize", help="write a big-endian .z64 copy (from .v64/.n64)")
    s.add_argument("rom"); s.add_argument("out"); s.set_defaults(fn=c_normalize)
    s = s2.add_parser("fixcrc", help="recompute the header CRC (keeps the input byte order)")
    s.add_argument("rom"); s.add_argument("--out"); s.add_argument("--cic", help="6101/6102/6103/6105/6106")
    s.set_defaults(fn=c_fixcrc)
    s = s2.add_parser("scan", help="find MIO0/Yay0/Yaz0 blocks")
    s.add_argument("rom"); s.add_argument("--fast", action="store_true", help="don't test-decompress")
    s.set_defaults(fn=c_scan)
    s = s2.add_parser("unpack", help="decompress the block at an offset")
    s.add_argument("rom"); s.add_argument("offset"); s.add_argument("out"); s.set_defaults(fn=c_unpack)
    s = s2.add_parser("pack", help="compress a file as MIO0 or Yaz0")
    s.add_argument("kind", choices=["MIO0", "Yaz0"]); s.add_argument("file"); s.add_argument("out")
    s.set_defaults(fn=c_pack)
    s = s2.add_parser("text", help="list Shift-JIS or EUC-JP runs that contain kana")
    s.add_argument("rom"); s.add_argument("--encoding", choices=["sjis", "euc"], default="sjis")
    s.add_argument("--min-kana", type=int, default=2); s.set_defaults(fn=c_text)
    s = s2.add_parser("xref", help="find words and lui/addiu pairs that point at an address")
    s.add_argument("rom"); s.add_argument("target", help="RAM address (0x80xxxxxx) or ROM offset")
    s.add_argument("--segment", action="append",
                   help="VADDR:ROM_OFFSET:SIZE of a code segment (default: boot segment from the header)")
    s.set_defaults(fn=c_xref)
