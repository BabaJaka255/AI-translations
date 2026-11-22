"""`rhtk ps2 ...` subcommands. See rhtk/ps2.py and docs/PS2.md."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

from . import ps2


def _int(v):
    return int(v, 0) if isinstance(v, str) else v


def c_info(a):
    print(json.dumps(ps2.info(a.image), indent=1))


def c_ls(a):
    with ps2.Iso(a.image) as iso:
        for e in sorted(iso.entries(), key=lambda e: e.lba):
            kind = "d" if e.is_dir else "-"
            print(f"{kind} {e.lba:8d} {e.size:11d}  {e.path}")


def c_extract(a):
    m = ps2.extract(a.image, a.dest)
    print(f"extracted {sum(not f['dir'] for f in m['files'])} files to {a.dest} (manifest: _iso.json)")


def c_cat(a):
    with ps2.Iso(a.image) as iso:
        data = iso.read_file(a.path)
    if a.out:
        with open(a.out, "wb") as f:
            f.write(data)
    else:
        sys.stdout.buffer.write(data)


def c_to_iso(a):
    ps2.to_iso(a.image, a.out)
    print(f"wrote {a.out}")


def _changed_files(image, folder):
    """ISO path -> local file, for every file under folder that differs from the disc."""
    out = {}
    with ps2.Iso(image) as iso:
        for e in iso.files():
            local = os.path.join(folder, e.path.lstrip("/"))
            if not os.path.isfile(local):
                continue
            if os.path.getsize(local) != e.size or _differs(iso, e, local):
                out[e.path] = local
    return out


def _differs(iso, e, local, chunk=1 << 20):
    with open(local, "rb") as f:
        lba, left = e.lba, e.size
        while left > 0:
            n = min(chunk, left)
            if f.read(n) != iso.read(lba, n):
                return True
            lba += n // ps2.SECTOR
            left -= n
    return False


def c_patch(a):
    reps = {}
    if a.dir:
        reps.update(_changed_files(a.image, a.dir))
    for spec in a.file or []:
        ipath, local = spec.split("=", 1)
        reps[ipath] = local
    if not reps:
        sys.exit("nothing to replace: every file matches the disc")
    report = ps2.patch_iso(a.image, a.out, reps)
    if a.report:
        with open(a.report, "w") as f:
            json.dump(report, f, indent=1)


def c_scan(a):
    rows = ps2.scan(a.dir)
    shown = rows if a.all else [r for r in rows if r["sjis_chars"] or r["utf16_runs"]][:a.top]
    print("sjis_chars\tsjis_runs\tutf16\tsize\ttype\tpath")
    for r in shown:
        print(f"{r['sjis_chars']}\t{r['sjis_runs']}\t{r['utf16_runs']}\t{r['size']}\t{r['type']}\t{r['path']}")
    types = {}
    for r in rows:
        types[r["type"] or "?"] = types.get(r["type"] or "?", 0) + 1
    print("\nfile types: " + ", ".join(f"{k} x{v}" for k, v in sorted(types.items(), key=lambda kv: -kv[1])),
          file=sys.stderr)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rows, f, indent=1)


def c_elf(a):
    with open(a.elf, "rb") as f:
        data = f.read()
    entry = int.from_bytes(data[0x18:0x1C], "little")
    print(f"entry 0x{entry:08X}")
    for vaddr, off, size in ps2.elf_segments(data):
        print(f"load vaddr 0x{vaddr:08X}  file 0x{off:08X}  size 0x{size:X}")
    print('mapping for project.json: {"type": "elf", "segments": '
          + json.dumps([[hex(v), hex(o), hex(s)] for v, o, s in ps2.elf_segments(data)]) + "}")


def c_afs_unpack(a):
    names = ps2.afs_unpack(a.archive, a.dest)
    print(f"{len(names)} files -> {a.dest} (order in _afs.json)")


def c_afs_pack(a):
    ps2.afs_pack(a.src, a.out)
    print(f"wrote {a.out}")


def c_tim2_info(a):
    with open(a.file, "rb") as f:
        data = f.read()
    for i, p in enumerate(ps2.tim2_pictures(data)):
        print(f"#{i}: {p['width']}x{p['height']} {ps2.TIM2_BPP.get(p['image_type'], '?')}bpp "
              f"clut {p['clut_colors']} colours (type 0x{p['clut_type']:02X}), mipmaps {p['mipmaps']}")


def c_tim2_rip(a):
    with open(a.file, "rb") as f:
        data = f.read()
    ps2.tim2_to_image(data, a.index, a.clut).save(a.png)
    print(f"wrote {a.png}")


def c_tim2_insert(a):
    from PIL import Image
    with open(a.file, "rb") as f:
        data = f.read()
    out = ps2.tim2_from_image(data, Image.open(a.png), a.index, a.clut)
    with open(a.out or a.file, "wb") as f:
        f.write(out)
    print(f"wrote {a.out or a.file}")


def c_xdelta(a):
    if not shutil.which("xdelta3"):
        sys.exit("xdelta3 is missing: apt-get install -y xdelta3")
    cmd = ["xdelta3", "-f", "-e", "-9", "-S", "djw", "-s", a.original, a.patched, a.out]
    subprocess.run(cmd, check=True)
    print(f"wrote {a.out} ({os.path.getsize(a.out)} bytes)")


def register(sub):
    p = sub.add_parser("ps2", help="PS2/PS1 disc images, ELF, AFS archives, TIM2 textures (docs/PS2.md)")
    s2 = p.add_subparsers(dest="ps2cmd", required=True)

    s = s2.add_parser("info", help="hashes, serial, boot ELF, volume (streams; fine for 4 GB)")
    s.add_argument("image"); s.set_defaults(fn=c_info)
    s = s2.add_parser("ls", help="list files with LBA and size")
    s.add_argument("image"); s.set_defaults(fn=c_ls)
    s = s2.add_parser("extract", help="extract all files plus an _iso.json manifest")
    s.add_argument("image"); s.add_argument("dest"); s.set_defaults(fn=c_extract)
    s = s2.add_parser("cat", help="read one file from the image")
    s.add_argument("image"); s.add_argument("path"); s.add_argument("-o", "--out"); s.set_defaults(fn=c_cat)
    s = s2.add_parser("to-iso", help="convert a raw 2352-byte .bin to a 2048-byte .iso")
    s.add_argument("image"); s.add_argument("out"); s.set_defaults(fn=c_to_iso)
    s = s2.add_parser("patch", help="write a new image with replaced files (in place when they fit)")
    s.add_argument("image"); s.add_argument("out")
    s.add_argument("--dir", help="folder laid out like the disc; files that differ are replaced")
    s.add_argument("--file", action="append", help="ISO_PATH=LOCAL_FILE (repeatable)")
    s.add_argument("--report", help="write the move report as JSON")
    s.set_defaults(fn=c_patch)
    s = s2.add_parser("scan", help="classify extracted files and rank them by Japanese text")
    s.add_argument("dir"); s.add_argument("--top", type=int, default=40)
    s.add_argument("--all", action="store_true"); s.add_argument("--json")
    s.set_defaults(fn=c_scan)
    s = s2.add_parser("elf", help="ELF entry point and load segments (for --mapping elf)")
    s.add_argument("elf"); s.set_defaults(fn=c_elf)
    s = s2.add_parser("afs-unpack", help="unpack an AFS archive")
    s.add_argument("archive"); s.add_argument("dest"); s.set_defaults(fn=c_afs_unpack)
    s = s2.add_parser("afs-pack", help="rebuild an AFS archive from an afs-unpack folder")
    s.add_argument("src"); s.add_argument("out"); s.set_defaults(fn=c_afs_pack)
    s = s2.add_parser("tim2-info", help="list the pictures in a TIM2 file")
    s.add_argument("file"); s.set_defaults(fn=c_tim2_info)
    s = s2.add_parser("tim2-rip", help="TIM2 picture -> PNG (indexed keeps the palette)")
    s.add_argument("file"); s.add_argument("png")
    s.add_argument("--index", type=int, default=0); s.add_argument("--clut", type=int, default=0)
    s.set_defaults(fn=c_tim2_rip)
    s = s2.add_parser("tim2-insert", help="PNG -> TIM2 picture (same size; palette kept)")
    s.add_argument("file"); s.add_argument("png"); s.add_argument("-o", "--out")
    s.add_argument("--index", type=int, default=0); s.add_argument("--clut", type=int, default=0)
    s.set_defaults(fn=c_tim2_insert)
    s = s2.add_parser("xdelta", help="make the release patch (xdelta3/VCDIFF; BPS is impractical at DVD size)")
    s.add_argument("original"); s.add_argument("patched"); s.add_argument("out"); s.set_defaults(fn=c_xdelta)
