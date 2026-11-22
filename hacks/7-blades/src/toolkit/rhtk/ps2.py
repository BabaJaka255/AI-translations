"""PlayStation 2 support: disc images, boot ELF, file scanning, AFS archives, TIM2 textures.

Everything streams from disk, so multi-GB DVD images are fine.

Disc images
    ISO9660 is what the PS2 BIOS and PCSX2 read. DVD games also carry a UDF
    bridge; it is left untouched (and goes stale) when files change, which the
    console and PCSX2 ignore. Raw 2352-byte CD images (.bin) can be listed and
    extracted, and converted to a 2048-byte .iso with `to_iso` before patching.

    `patch_iso` rewrites changed files in place when they still fit in the sectors
    before the next file, and otherwise appends them after the last sector and
    repoints the directory record. Some games read files by hard-coded LBA or by
    their own table of contents (often inside the ELF or an archive); moving such
    a file breaks it, so the command reports every move.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import struct
import zlib

SECTOR = 2048
DVD5_SECTORS = 2295104  # single-layer DVD capacity


# ------------------------------------------------------------------ ISO9660

class Entry:
    __slots__ = ("path", "lba", "size", "is_dir", "rec_pos")

    def __init__(self, path, lba, size, is_dir, rec_pos):
        self.path, self.lba, self.size, self.is_dir, self.rec_pos = path, lba, size, is_dir, rec_pos

    @property
    def sectors(self) -> int:
        return max(1, -(-self.size // SECTOR))

    def as_dict(self):
        return {"path": self.path, "lba": self.lba, "size": self.size, "dir": self.is_dir}


class Iso:
    """Read-only view of an ISO9660 image (2048-byte or raw 2352-byte sectors)."""

    def __init__(self, path: str):
        self.path = path
        self.f = open(path, "rb")
        self.file_size = os.path.getsize(path)
        for raw, hdr in ((SECTOR, 0), (2352, 24), (2352, 16)):
            self.f.seek(16 * raw + hdr)
            if self.f.read(6)[1:6] == b"CD001":
                self.raw, self.hdr = raw, hdr
                break
        else:
            raise ValueError(f"{path}: no ISO9660 volume descriptor found")
        pvd = self.read(16, SECTOR)
        self.volume_id = pvd[40:72].decode("ascii", "replace").strip()
        self.volume_sectors = struct.unpack_from("<I", pvd, 80)[0]
        root = pvd[156:156 + 34]
        self.root = Entry("/", struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0],
                          True, 16 * SECTOR + 156)
        self.udf = any(self.read(s, 6)[1:6] in (b"BEA01", b"NSR02", b"NSR03") for s in range(17, 24))
        self._entries = None

    def close(self):
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def read(self, lba: int, length: int) -> bytes:
        if self.raw == SECTOR:
            self.f.seek(lba * SECTOR)
            return self.f.read(length)
        out = bytearray()
        while len(out) < length:
            self.f.seek(lba * self.raw + self.hdr)
            out += self.f.read(min(SECTOR, length - len(out)))
            lba += 1
        return bytes(out)

    def entries(self) -> list[Entry]:
        """Every file and directory, depth first. rec_pos is the byte offset of the
        directory record in 2048-byte sector space (lba*2048 + offset)."""
        if self._entries is not None:
            return self._entries
        out, seen = [], set()

        def walk(d: Entry):
            if d.lba in seen:
                return
            seen.add(d.lba)
            data = self.read(d.lba, d.size)
            i = 0
            while i < len(data):
                n = data[i]
                if n == 0:  # records never cross a sector boundary
                    i = (i // SECTOR + 1) * SECTOR
                    continue
                rec = data[i:i + n]
                name_len = rec[32]
                name = rec[33:33 + name_len]
                if name not in (b"\x00", b"\x01"):
                    lba = struct.unpack_from("<I", rec, 2)[0]
                    size = struct.unpack_from("<I", rec, 10)[0]
                    is_dir = bool(rec[25] & 2)
                    text = name.decode("ascii", "replace").split(";")[0]
                    if not is_dir and text.endswith("."):
                        text = text[:-1]
                    path = (d.path.rstrip("/") + "/" + text)
                    e = Entry(path, lba, size, is_dir, d.lba * SECTOR + i)
                    out.append(e)
                    if is_dir:
                        walk(e)
                i += n

        walk(self.root)
        self._entries = out
        return out

    def files(self) -> list[Entry]:
        return [e for e in self.entries() if not e.is_dir]

    def find(self, path: str) -> Entry | None:
        p = "/" + path.strip("/").replace("\\", "/")
        for e in self.entries():
            if e.path.upper() == p.upper():
                return e
        return None

    def read_file(self, e: Entry | str) -> bytes:
        if isinstance(e, str):
            found = self.find(e)
            if not found:
                raise FileNotFoundError(e)
            e = found
        return self.read(e.lba, e.size)

    def copy_file(self, e: Entry, dest: str, chunk: int = 512 * SECTOR):
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "wb") as out:
            left, lba = e.size, e.lba
            while left > 0:
                n = min(chunk, left)
                out.write(self.read(lba, n))
                lba += n // SECTOR
                left -= n


def system_cnf(iso: Iso) -> dict:
    """Parse SYSTEM.CNF: BOOT2 (PS2) or BOOT (PS1), VER, VMODE. Adds 'serial' and 'boot_path'."""
    try:
        text = iso.read_file("SYSTEM.CNF").decode("ascii", "replace")
    except FileNotFoundError:
        return {}
    cnf = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            cnf[k.strip()] = v.strip()
    boot = cnf.get("BOOT2") or cnf.get("BOOT")
    if boot:
        path = boot.split(":", 1)[-1].lstrip("\\/").split(";")[0].replace("\\", "/")
        cnf["boot_path"] = "/" + path
        name = path.rsplit("/", 1)[-1]
        cnf["serial"] = name.replace("_", "-").replace(".", "")
    return cnf


def info(path: str) -> dict:
    """Identify a disc image: hashes (streamed), volume, boot ELF, serial."""
    crc, md5, sha1 = 0, __import__("hashlib").md5(), __import__("hashlib").sha1()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 22):
            crc = zlib.crc32(chunk, crc)
            md5.update(chunk)
            sha1.update(chunk)
    out = {"crc32": f"{crc:08X}", "md5": md5.hexdigest(), "sha1": sha1.hexdigest(),
           "size": os.path.getsize(path)}
    with Iso(path) as iso:
        cnf = system_cnf(iso)
        out.update(platform="ps2" if "BOOT2" in cnf else ("ps1" if "BOOT" in cnf else "iso9660"),
                   sector_size=iso.raw, volume_id=iso.volume_id, volume_sectors=iso.volume_sectors,
                   udf_bridge=iso.udf, files=len(iso.files()))
        for k in ("serial", "boot_path", "VER", "VMODE"):
            if k in cnf:
                out[k.lower()] = cnf[k]
        if iso.raw == SECTOR and iso.file_size > iso.volume_sectors * SECTOR + 32 * SECTOR:
            out["note"] = ("image is larger than the ISO9660 volume: probably dual-layer (DVD9). "
                           "Second-layer files have their own descriptor at the layer break.")
    return out


def extract(path: str, dest: str) -> dict:
    """Extract every file to dest/ and write a manifest (path, LBA, size per file) to dest/_iso.json."""
    with Iso(path) as iso:
        for e in iso.entries():
            target = os.path.join(dest, e.path.lstrip("/"))
            if e.is_dir:
                os.makedirs(target, exist_ok=True)
            else:
                iso.copy_file(e, target)
        manifest = {"image": os.path.basename(path), "volume_id": iso.volume_id,
                    "volume_sectors": iso.volume_sectors, "sector_size": iso.raw,
                    "files": [e.as_dict() for e in sorted(iso.entries(), key=lambda e: e.lba)]}
    with open(os.path.join(dest, "_iso.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def to_iso(src: str, dest: str):
    """Convert a raw 2352-byte image to a plain 2048-byte ISO."""
    with Iso(src) as iso, open(dest, "wb") as out:
        total = iso.file_size // iso.raw
        for lba in range(0, total, 256):
            out.write(iso.read(lba, min(256, total - lba) * SECTOR))


def _put_both(buf, off, value):  # ISO9660 "both-endian" 32-bit field
    buf.seek(off)
    buf.write(struct.pack("<I", value) + struct.pack(">I", value))


def patch_iso(src: str, dest: str, replacements: dict[str, str], log=print) -> list[dict]:
    """Copy src to dest and replace files. replacements maps an ISO path to a local file.

    Returns one record per replaced file: {path, old_lba, lba, size, moved}."""
    with Iso(src) as iso:
        if iso.raw != SECTOR:
            raise ValueError("raw 2352-byte image: convert it with `ps2 to-iso` first")
        ents = iso.entries()
        starts = sorted({e.lba for e in ents} | {iso.volume_sectors})
        targets = []
        for ipath, local in replacements.items():
            e = iso.find(ipath)
            if e is None or e.is_dir:
                raise FileNotFoundError(f"{ipath} is not a file on the disc")
            targets.append((e, local))
        volume_sectors = iso.volume_sectors
    if os.path.abspath(src) != os.path.abspath(dest):
        shutil.copyfile(src, dest)
    report = []
    end = max(volume_sectors, -(-os.path.getsize(dest) // SECTOR))
    with open(dest, "r+b") as out:
        for e, local in targets:
            size = os.path.getsize(local)
            need = max(1, -(-size // SECTOR))
            nxt = next(s for s in starts if s > e.lba)
            room = nxt - e.lba
            if need <= room:
                lba, moved = e.lba, False
                # clear the old extent so stale bytes don't linger in the slack
                out.seek(lba * SECTOR)
                out.write(b"\0" * (e.sectors * SECTOR if e.sectors <= room else room * SECTOR))
            else:
                lba, moved = end, True
                end += need
            out.seek(lba * SECTOR)
            with open(local, "rb") as f:
                shutil.copyfileobj(f, out, 1 << 20)
            pad = need * SECTOR - size
            if pad:
                out.write(b"\0" * pad)
            _put_both(out, e.rec_pos + 2, lba)
            _put_both(out, e.rec_pos + 10, size)
            report.append({"path": e.path, "old_lba": e.lba, "lba": lba, "size": size, "moved": moved})
            log(f"{e.path}: {e.size} -> {size} bytes" + (f", moved {e.lba} -> {lba}" if moved else ", in place"))
        if end > volume_sectors:
            _put_both(out, 16 * SECTOR + 80, end)
            out.truncate(end * SECTOR)
            if end > DVD5_SECTORS:
                log(f"warning: image is now {end} sectors, past single-layer DVD size ({DVD5_SECTORS})")
    if any(r["moved"] for r in report):
        log("note: moved files get a new LBA. If the game finds files through its own LBA table "
            "(ELF or archive TOC), update that table too, or shrink the file to fit in place.")
    return report


# ------------------------------------------------------------------ ELF

def elf_segments(data: bytes) -> list[tuple[int, int, int]]:
    """(vaddr, file_offset, filesz) for each PT_LOAD segment of a 32-bit little-endian ELF."""
    if data[:4] != b"\x7fELF" or data[4] != 1:
        raise ValueError("not a 32-bit ELF")
    phoff, = struct.unpack_from("<I", data, 0x1C)
    phentsize, phnum = struct.unpack_from("<HH", data, 0x2A)
    segs = []
    for i in range(phnum):
        p_type, p_off, p_vaddr, _pa, p_filesz = struct.unpack_from("<5I", data, phoff + i * phentsize)
        if p_type == 1 and p_filesz:
            segs.append((p_vaddr, p_off, p_filesz))
    return segs


# ------------------------------------------------------------------ scanning

SJIS_RUN = re.compile(rb"(?:[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]){4,}")
SJIS_KANA = re.compile(rb"\x82[\x9F-\xF1]|\x83[\x40-\x96]")
UTF16_KANA = re.compile(rb"(?:[\x41-\xFC]\x30){4,}")  # hiragana/katakana in UTF-16LE
MAGICS = [
    (b"TIM2", "TIM2 texture"), (b"CLT2", "TIM2 palette"), (b"\x7fELF", "ELF/IRX"),
    (b"AFS\x00", "AFS archive"), (b"CPK ", "CRI CPK archive"), (b"@UTF", "CRI @UTF table"),
    (b"PK\x03\x04", "ZIP"), (b"\x1f\x8b", "gzip"), (b"\x00\x00\x01\xba", "MPEG-PS video (PSS)"),
    (b"VAGp", "VAG audio"), (b"IECSsreV", "SCEI HD/BD sound bank"), (b"RIFF", "RIFF/WAV"),
    (b"\x89PNG", "PNG"), (b"BM", "BMP"), (b"\x10\x00\x00\x00", "PS1 TIM (maybe)"),
    (b"\x80\x00", "CRI ADX audio (maybe)"), (b"GIM", "GIM texture"), (b"FORM", "IFF"),
]


def sniff(head: bytes) -> str:
    for magic, name in MAGICS:
        if head.startswith(magic):
            return name
    if head[:4].isascii() and head[:4].isalnum():
        return f"tag {head[:4].decode()!r}"
    return ""


def scan(root: str, max_read: int = 64 << 20) -> list[dict]:
    """Classify every file under root and count Japanese text, to show where the script lives."""
    rows = []
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            p = os.path.join(dirpath, name)
            if name == "_iso.json":
                continue
            size = os.path.getsize(p)
            with open(p, "rb") as f:
                data = f.read(max_read)
            # a run only counts if at least a quarter of it is kana: random bytes rarely manage that
            sj = [r for r in SJIS_RUN.findall(data) if len(SJIS_KANA.findall(r)) * 8 >= len(r)]
            u16 = UTF16_KANA.findall(data)
            rows.append({"path": os.path.relpath(p, root), "size": size, "type": sniff(data[:16]),
                         "sjis_runs": len(sj), "sjis_chars": sum(len(r) for r in sj) // 2,
                         "utf16_runs": len(u16)})
    rows.sort(key=lambda r: (-r["sjis_chars"], -r["utf16_runs"], r["path"]))
    return rows


# ------------------------------------------------------------------ AFS

def afs_read(data: bytes) -> tuple[list[bytes], list[dict] | None, dict]:
    """Return (files, names or None, layout) for an AFS archive."""
    if data[:4] != b"AFS\x00":
        raise ValueError("not an AFS archive")
    n, = struct.unpack_from("<I", data, 4)
    toc = [struct.unpack_from("<II", data, 8 + i * 8) for i in range(n)]
    files = [data[o:o + s] for o, s in toc]
    nt_off, nt_size = struct.unpack_from("<II", data, 8 + n * 8)
    first = min((o for o, s in toc if o), default=len(data))
    if not nt_off and first >= 8:
        nt_off, nt_size = struct.unpack_from("<II", data, first - 8)
    names = None
    if nt_off and nt_off + n * 0x30 <= len(data):
        names = []
        for i in range(n):
            r = data[nt_off + i * 0x30:nt_off + (i + 1) * 0x30]
            names.append({"name": r[:32].split(b"\0")[0].decode("cp932", "replace"),
                          "date": list(struct.unpack_from("<6H", r, 32)), "raw_tail": r[44:48].hex()})
    align = 0x800
    for o, _s in toc:
        if o % 0x800:
            align = 0x10 if o % 0x10 == 0 else 1
            break
    return files, names, {"align": align, "header_end": first}


def afs_build(files: list[bytes], names: list[dict] | None, align: int = 0x800,
              header_end: int | None = None) -> bytes:
    n = len(files)
    table_end = 8 + n * 8 + 8
    pos = max(header_end or 0, -(-table_end // align) * align)
    out = bytearray(pos)
    out[:8] = b"AFS\x00" + struct.pack("<I", n)
    for i, d in enumerate(files):
        struct.pack_into("<II", out, 8 + i * 8, len(out), len(d))
        out += d
        out += b"\0" * (-len(out) % align)
    if names is not None:
        nt = bytearray()
        for i, (d, nm) in enumerate(zip(files, names)):
            raw = nm["name"].encode("cp932")[:32].ljust(32, b"\0")
            nt += raw + struct.pack("<6H", *nm.get("date", [0] * 6)) + struct.pack("<I", len(d))
        struct.pack_into("<II", out, 8 + n * 8, len(out), len(nt))
        out += nt
        out += b"\0" * (-len(out) % align)
    return bytes(out)


def afs_unpack(path: str, dest: str):
    with open(path, "rb") as f:
        files, names, layout = afs_read(f.read())
    os.makedirs(dest, exist_ok=True)
    order = []
    for i, d in enumerate(files):
        base = names[i]["name"] if names and names[i]["name"] else f"{i:05d}.bin"
        fname = f"{i:05d}_{base}" if names else base
        with open(os.path.join(dest, fname), "wb") as f:
            f.write(d)
        order.append(fname)
    with open(os.path.join(dest, "_afs.json"), "w", encoding="utf-8") as f:
        json.dump({"files": order, "names": names, **layout}, f, indent=1, ensure_ascii=False)
    return order


def afs_pack(src: str, out_path: str):
    with open(os.path.join(src, "_afs.json"), encoding="utf-8") as f:
        m = json.load(f)
    files = []
    for name in m["files"]:
        with open(os.path.join(src, name), "rb") as f:
            files.append(f.read())
    with open(out_path, "wb") as f:
        f.write(afs_build(files, m["names"], m["align"], m["header_end"]))


# ------------------------------------------------------------------ TIM2

TIM2_BPP = {1: 16, 2: 24, 3: 32, 4: 4, 5: 8}


def _ps2_alpha(a: int) -> int:
    return min(255, a * 255 // 128)


def _alpha_ps2(a: int) -> int:
    return (a * 128 + 127) // 255


def _csm1(i: int) -> int:  # CSM1 256-colour CLUT swizzle (its own inverse)
    return (i & ~0x18) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)


def _decode_colors(raw: bytes, bits: int) -> list[tuple[int, int, int, int]]:
    out = []
    if bits == 16:
        for (v,) in struct.iter_unpack("<H", raw[:len(raw) // 2 * 2]):
            out.append(((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31,
                        255 if v & 0x8000 else 0))
    elif bits == 24:
        for i in range(0, len(raw) - 2, 3):
            out.append((raw[i], raw[i + 1], raw[i + 2], 255))
    else:
        for i in range(0, len(raw) - 3, 4):
            out.append((raw[i], raw[i + 1], raw[i + 2], _ps2_alpha(raw[i + 3])))
    return out


def _encode_colors(cols, bits: int) -> bytes:
    out = bytearray()
    for r, g, b, a in cols:
        if bits == 16:
            out += struct.pack("<H", (r * 31 // 255) | (g * 31 // 255) << 5 | (b * 31 // 255) << 10
                               | (0x8000 if a >= 128 else 0))
        elif bits == 24:
            out += bytes((r, g, b))
        else:
            out += bytes((r, g, b, _alpha_ps2(a)))
    return bytes(out)


def tim2_pictures(data: bytes) -> list[dict]:
    if data[:4] != b"TIM2":
        raise ValueError("not a TIM2 file")
    count, = struct.unpack_from("<H", data, 6)
    pos = 0x80 if data[5] == 1 else 0x10
    pics = []
    for _ in range(count):
        (total, clut_size, image_size, header_size, clut_colors, pict_format, mipmaps, clut_type,
         image_type, w, h) = struct.unpack_from("<IIIHHBBBBHH", data, pos)
        img_off = pos + header_size
        pics.append({"pos": pos, "total": total, "clut_size": clut_size, "image_size": image_size,
                     "header_size": header_size, "clut_colors": clut_colors, "mipmaps": mipmaps,
                     "clut_type": clut_type, "image_type": image_type, "width": w, "height": h,
                     "image_off": img_off, "clut_off": img_off + image_size})
        pos += total
    return pics


def _clut(data, p, which=0):
    bits = {1: 16, 2: 24, 3: 32}.get(p["clut_type"] & 0x3F, 32)
    raw = data[p["clut_off"]:p["clut_off"] + p["clut_size"]]
    cols = _decode_colors(raw, bits)
    n = 16 if p["image_type"] == 4 else 256
    if n == 256 and not p["clut_type"] & 0x80:
        cols = [cols[_csm1(i)] if _csm1(i) < len(cols) else (0, 0, 0, 0) for i in range(len(cols))]
    return cols[which * n:(which + 1) * n], bits


def tim2_to_image(data: bytes, index: int = 0, clut: int = 0):
    """Picture `index` as a PIL image: mode P (with RGBA palette) for indexed, RGBA otherwise."""
    from PIL import Image
    p = tim2_pictures(data)[index]
    w, h, t = p["width"], p["height"], p["image_type"]
    raw = data[p["image_off"]:p["image_off"] + p["image_size"]]
    if t in (4, 5):
        if t == 4:
            px = bytearray(w * h)
            for i in range(w * h):
                b = raw[i >> 1]
                px[i] = (b >> 4) if i & 1 else (b & 15)
        else:
            px = raw[:w * h]
        cols, _bits = _clut(data, p, clut)
        img = Image.frombytes("P", (w, h), bytes(px))
        flat = [c for col in cols for c in col]
        img.putpalette(flat, rawmode="RGBA")
        return img
    cols = _decode_colors(raw, TIM2_BPP[t])
    img = Image.new("RGBA", (w, h))
    img.putdata(cols[:w * h])
    return img


def _nearest(c, pal):
    return min(range(len(pal)), key=lambda i: sum((a - b) ** 2 for a, b in zip(c, pal[i])))


def tim2_from_image(data: bytes, img, index: int = 0, clut: int = 0) -> bytes:
    """Write img into picture `index`, keeping the original palette and size.

    A mode-P image is written index for index; RGB/RGBA is mapped to the nearest palette entry."""
    p = tim2_pictures(data)[index]
    w, h, t = p["width"], p["height"], p["image_type"]
    if img.size != (w, h):
        raise ValueError(f"image is {img.size}, texture is {(w, h)}")
    out = bytearray(data)
    if t in (4, 5):
        if img.mode == "P":
            px = list(img.getdata())
        else:
            pal, _ = _clut(data, p, clut)
            cache = {}
            px = []
            for c in img.convert("RGBA").getdata():
                if c not in cache:
                    cache[c] = _nearest(c, pal)
                px.append(cache[c])
        limit = 16 if t == 4 else 256
        if max(px) >= limit:
            raise ValueError(f"pixel index {max(px)} does not fit a {limit}-colour texture")
        if t == 4:
            raw = bytearray(w * h // 2)
            for i, v in enumerate(px):
                raw[i >> 1] |= v << 4 if i & 1 else v
        else:
            raw = bytes(px)
    else:
        raw = _encode_colors(img.convert("RGBA").getdata(), TIM2_BPP[t])
    out[p["image_off"]:p["image_off"] + len(raw)] = raw
    return bytes(out)


# ------------------------------------------------------------------ MIPS references

def mips_hilo_refs(data: bytes, segments, target: int, window: int = 64):
    """Find MIPS code that builds address `target` with lui + addiu/ori/load/store.

    PS2 code rarely stores string pointers as plain words; it loads them with a
    lui/addiu pair. Yields (file_offset_of_lui, file_offset_of_low, low_mnemonic)."""
    hi_signed = ((target + 0x8000) >> 16) & 0xFFFF  # for sign-extending low ops
    hi_plain = (target >> 16) & 0xFFFF               # for ori
    lo = target & 0xFFFF
    low_ops = {0x09: "addiu", 0x0D: "ori", 0x20: "lb", 0x21: "lh", 0x23: "lw", 0x24: "lbu",
               0x25: "lhu", 0x28: "sb", 0x29: "sh", 0x2B: "sw", 0x1E: "lq", 0x1F: "sq"}
    for _vaddr, foff, size in segments:
        end = foff + size - (size % 4)
        words = struct.unpack_from(f"<{(end - foff) // 4}I", data, foff)
        for i, w in enumerate(words):
            if w >> 26 != 0x0F:  # lui
                continue
            imm, rt = w & 0xFFFF, (w >> 16) & 31
            if imm not in (hi_signed, hi_plain):
                continue
            for j in range(i + 1, min(len(words), i + 1 + window // 4)):
                v = words[j]
                op, rs = v >> 26, (v >> 21) & 31
                if rs == rt and op in low_ops and (v & 0xFFFF) == lo:
                    if imm == (hi_plain if op == 0x0D else hi_signed):
                        yield foff + i * 4, foff + j * 4, low_ops[op]
                        break
                if op == 0x0F and (v >> 16) & 31 == rt:  # register reloaded
                    break
