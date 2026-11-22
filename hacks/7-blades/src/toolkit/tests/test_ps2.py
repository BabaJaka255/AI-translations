"""PS2 tools on synthetic data: python3 -m unittest discover -s tests (from the toolkit folder)."""
import os
import struct
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rhtk import ps2  # noqa: E402
from rhtk.address import Mapper  # noqa: E402

S = 2048


def _rec(name: bytes, lba: int, size: int, is_dir: bool) -> bytes:
    n = 33 + len(name)
    n += n & 1
    r = bytearray(n)
    r[0] = n
    r[2:10] = struct.pack("<I", lba) + struct.pack(">I", lba)
    r[10:18] = struct.pack("<I", size) + struct.pack(">I", size)
    r[25] = 2 if is_dir else 0
    r[32] = len(name)
    r[33:33 + len(name)] = name
    return bytes(r)


def make_iso(files: dict[str, bytes], gap: int = 0) -> bytes:
    """Tiny ISO9660 image: root + one subdirectory DATA. files keys: 'NAME' or 'DATA/NAME'."""
    root_files = {k: v for k, v in files.items() if "/" not in k}
    sub_files = {k.split("/")[1]: v for k, v in files.items() if k.startswith("DATA/")}
    lba = 22
    layout = {}
    for k, v in list(root_files.items()) + [("DATA/" + k, v) for k, v in sub_files.items()]:
        layout[k] = lba
        lba += max(1, -(-len(v) // S)) + gap
    total = lba
    img = bytearray(total * S)
    pvd = bytearray(S)
    pvd[0:6] = b"\x01CD001"
    pvd[40:72] = b"TESTVOL".ljust(32)
    pvd[80:88] = struct.pack("<I", total) + struct.pack(">I", total)
    pvd[156:190] = _rec(b"\x00", 20, S, True)
    img[16 * S:17 * S] = pvd
    img[17 * S:17 * S + 6] = b"\xffCD001"
    root = _rec(b"\x00", 20, S, True) + _rec(b"\x01", 20, S, True) + _rec(b"DATA", 21, S, True)
    for k, v in root_files.items():
        root += _rec(k.encode() + b";1", layout[k], len(v), False)
    img[20 * S:20 * S + len(root)] = root
    sub = _rec(b"\x00", 21, S, True) + _rec(b"\x01", 20, S, True)
    for k, v in sub_files.items():
        sub += _rec(k.encode() + b";1", layout["DATA/" + k], len(v), False)
    img[21 * S:21 * S + len(sub)] = sub
    for k, v in files.items():
        img[layout[k] * S:layout[k] * S + len(v)] = v
    return bytes(img)


class IsoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.files = {"SYSTEM.CNF": b"BOOT2 = cdrom0:\\SLPS_123.45;1\r\nVER = 1.00\r\nVMODE = NTSC\r\n",
                      "SLPS_123.45": b"\x7fELF" + b"\0" * 3000,
                      "DATA/MSG.BIN": "こんにちは、せかい".encode("cp932") * 10,
                      "DATA/LAST.BIN": b"z" * 100}
        self.iso = os.path.join(self.d, "game.iso")
        with open(self.iso, "wb") as f:
            f.write(make_iso(self.files))

    def tearDown(self):
        self.tmp.cleanup()

    def test_info_and_extract(self):
        info = ps2.info(self.iso)
        self.assertEqual(info["platform"], "ps2")
        self.assertEqual(info["serial"], "SLPS-12345")
        self.assertEqual(info["boot_path"], "/SLPS_123.45")
        out = os.path.join(self.d, "x")
        ps2.extract(self.iso, out)
        for k, v in self.files.items():
            with open(os.path.join(out, k), "rb") as f:
                self.assertEqual(f.read(), v)
        rows = ps2.scan(out)
        self.assertEqual(rows[0]["path"], os.path.join("DATA", "MSG.BIN"))
        self.assertEqual(rows[0]["type"], "")

    def test_patch_in_place_and_moved(self):
        small = os.path.join(self.d, "small")
        with open(small, "wb") as f:
            f.write(b"hello")
        big = os.path.join(self.d, "big")
        with open(big, "wb") as f:
            f.write(b"B" * (S * 3 + 7))
        out = os.path.join(self.d, "out.iso")
        rep = ps2.patch_iso(self.iso, out, {"DATA/MSG.BIN": small, "SLPS_123.45": big}, log=lambda *_: None)
        moved = {r["path"]: r["moved"] for r in rep}
        self.assertEqual(moved, {"/DATA/MSG.BIN": False, "/SLPS_123.45": True})
        with ps2.Iso(out) as iso:
            self.assertEqual(iso.read_file("DATA/MSG.BIN"), b"hello")
            self.assertEqual(iso.read_file("SLPS_123.45"), b"B" * (S * 3 + 7))
            self.assertEqual(iso.read_file("DATA/LAST.BIN"), b"z" * 100)
            self.assertEqual(iso.volume_sectors * S, os.path.getsize(out))

    def test_raw_bin(self):
        img = make_iso(self.files)
        raw = bytearray()
        for i in range(0, len(img), S):
            raw += b"\0" * 24 + img[i:i + S] + b"\0" * 280
        p = os.path.join(self.d, "game.bin")
        with open(p, "wb") as f:
            f.write(raw)
        with ps2.Iso(p) as iso:
            self.assertEqual(iso.raw, 2352)
            self.assertEqual(iso.read_file("DATA/MSG.BIN"), self.files["DATA/MSG.BIN"])
        back = os.path.join(self.d, "back.iso")
        ps2.to_iso(p, back)
        with open(back, "rb") as f:
            self.assertEqual(f.read(), img)


class ElfTest(unittest.TestCase):
    def test_segments_mapping_and_hilo(self):
        elf = bytearray(0x2000)
        elf[:5] = b"\x7fELF\x01"
        struct.pack_into("<I", elf, 0x1C, 0x34)
        struct.pack_into("<HH", elf, 0x2A, 32, 1)
        struct.pack_into("<5I", elf, 0x34, 1, 0x1000, 0x00100000, 0x00100000, 0x1000)
        # lui a0, 0x0010 ; addiu a0, a0, 0x0800  -> 0x00100800 (file 0x1800)
        struct.pack_into("<II", elf, 0x1000, (0x0F << 26) | (4 << 16) | 0x0010,
                         (0x09 << 26) | (4 << 21) | (4 << 16) | 0x0800)
        segs = ps2.elf_segments(bytes(elf))
        self.assertEqual(segs, [(0x00100000, 0x1000, 0x1000)])
        m = Mapper({"type": "elf", "segments": segs})
        self.assertEqual(m.to_file(0x00100800), 0x1800)
        self.assertEqual(m.to_ptr(0x1800), 0x00100800)
        hits = list(ps2.mips_hilo_refs(bytes(elf), segs, 0x00100800))
        self.assertEqual(hits, [(0x1000, 0x1004, "addiu")])


class AfsTim2Test(unittest.TestCase):
    def test_afs_roundtrip(self):
        files = [b"one", b"two" * 1000, b""]
        names = [{"name": n, "date": [2003, 1, 2, 3, 4, 5]} for n in ("a.bin", "b.bin", "c.bin")]
        data = ps2.afs_build(files, names)
        got, gnames, layout = ps2.afs_read(data)
        self.assertEqual(got, files)
        self.assertEqual([n["name"] for n in gnames], ["a.bin", "b.bin", "c.bin"])
        self.assertEqual(ps2.afs_build(got, gnames, layout["align"], layout["header_end"]), data)

    def test_tim2_8bpp_roundtrip(self):
        w, h = 16, 8
        pix = bytes((x * 7 + y) & 0xFF for y in range(h) for x in range(w))
        clut = bytes(c for i in range(256) for c in (i, 255 - i, i // 2, 0x80))
        hdr = struct.pack("<IIIHHBBBBHH", 48 + len(pix) + len(clut), len(clut), len(pix), 48, 256,
                          0, 1, 3, 5, w, h) + b"\0" * 24
        data = b"TIM2" + bytes([4, 0]) + struct.pack("<H", 1) + b"\0" * 8 + hdr + pix + clut
        img = ps2.tim2_to_image(data)
        self.assertEqual(img.size, (w, h))
        self.assertEqual(ps2.tim2_from_image(data, img), data)
        # an RGBA edit maps back to the same indices
        self.assertEqual(ps2.tim2_from_image(data, img.convert("RGBA")), data)

    def test_tim2_4bpp(self):
        w, h = 8, 2
        pix = bytes(range(8))
        clut = bytes(c for i in range(16) for c in (i * 16, i * 8, 0, 0x80))
        hdr = struct.pack("<IIIHHBBBBHH", 48 + len(pix) + len(clut), len(clut), len(pix), 48, 16,
                          0, 1, 3, 4, w, h) + b"\0" * 24
        data = b"TIM2" + bytes([4, 0]) + struct.pack("<H", 1) + b"\0" * 8 + hdr + pix + clut
        img = ps2.tim2_to_image(data)
        self.assertEqual(list(img.getdata())[:4], [0, 0, 1, 0])
        self.assertEqual(ps2.tim2_from_image(data, img), data)


if __name__ == "__main__":
    unittest.main()


class Mips64Test(unittest.TestCase):
    def test_ee_doubleword_ops(self):
        from rhtk import disasm
        code = bytes.fromhex("a000b0ff" "a000b0df")  # sd s0,0xa0(sp); ld s0,0xa0(sp)
        mn = [m for _a, _r, m, _o in disasm.disassemble(code, 0, 8, "mips64")]
        self.assertEqual(mn, ["sd", "ld"])
