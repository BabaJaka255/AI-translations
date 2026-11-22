"""Self-test on synthetic data: python3 -m unittest discover -s tests (from the toolkit folder)."""
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rhtk import compress, gfx, patch, qa, rominfo, search  # noqa: E402
from rhtk.address import Mapper  # noqa: E402
from rhtk.script import dump_block, insert_block  # noqa: E402
from rhtk.table import Table  # noqa: E402

KANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
JP_TBL = "\n".join(f"{i + 0x10:02X}={c}" for i, c in enumerate(KANA)) + "\n/FF=<end>\n*FE=<br>\n$F0=<name>,1\n$F1=<wait>,0\n"
EN_TBL = "\n".join(f"{i + 0x10:02X}={c}" for i, c in enumerate(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")) + "\n50= \n51=!\n52=.\n53=,\n54='\n/FF=<end>\n*FE=<br>\n$F0=<name>,1\n$F1=<wait>,0\n"


class TableTest(unittest.TestCase):
    def test_roundtrip(self):
        t = Table.parse(JP_TBL)
        text = "あいう<br>\nか<name 02>き<wait><end>"
        data = t.encode(text)
        self.assertEqual(t.decode(data)[0], text)
        self.assertEqual(t.decode(b"\x10\x99\xFF")[0], "あ[99]<end>")
        self.assertEqual(t.encode("あ[99]<end>"), b"\x10\x99\xFF")

    def test_multibyte_longest_match(self):
        t = Table.parse("81=x\n8140=　\n82=y\n")
        self.assertEqual(t.decode(b"\x81\x40\x81", stop_at_end=False)[0], "　x")
        t2 = Table.parse("10=t\n11=h\n20=th\n")
        self.assertEqual(t2.encode("th"), b"\x20")


def make_rom():
    t = Table.parse(JP_TBL)
    rom = bytearray(b"\x00" * 0x10000)
    strings = ["あいう<end>", "かきくけこ<br>\nさし<end>", "<name 01>たち<wait><end>"]
    off = 0x5000
    ptrs = []
    for s in strings:
        b = t.encode(s)
        rom[off:off + len(b)] = b
        ptrs.append(off)
        off += len(b)
    ptrs.append(ptrs[0])  # shared pointer
    # banked 16-bit pointers: bank 1 at window 0x4000 -> file 0x4000-0x7FFF
    for i, p in enumerate(ptrs):
        rom[0x100 + 2 * i:0x102 + 2 * i] = (p - 0x4000 + 0x4000).to_bytes(2, "little")
    return rom, len(strings)


BLOCK = {"name": "dlg", "ptr_table": "0x100", "count": 4, "ptr_size": 2,
         "mapping": {"type": "bank", "bank": 1, "bank_size": "0x4000", "window": "0x4000"},
         "free_space": [["0x7000", "0x7FFF"], ["0x9000", "0x9FFF"]],
         "box": {"max_chars": 12, "max_lines": 2, "page_tokens": ["<wait>"]}}


class ScriptTest(unittest.TestCase):
    def test_dump_insert(self):
        rom, n = make_rom()
        jp, en = Table.parse(JP_TBL), Table.parse(EN_TBL)
        script = dump_block(bytes(rom), BLOCK, jp)
        self.assertEqual(len(script["entries"]), n)
        self.assertEqual(script["entries"][0]["pointers"], ["0x100", "0x106"])
        self.assertEqual(script["entries"][1]["jp"], "かきくけこ<br>\nさし<end>")
        script["entries"][0]["en"] = "Hello there, this is a much longer line!<end>"
        script["entries"][2]["en"] = "<name 01>Hi.<wait><end>"
        out = bytearray(rom)
        st = insert_block(out, BLOCK, script, en)
        self.assertGreaterEqual(st["moved"], 1)
        again = dump_block(bytes(out), BLOCK, en)
        self.assertEqual(again["entries"][0]["jp"], "Hello there, this is a much longer line!<end>")
        self.assertEqual(again["entries"][0]["pointers"], ["0x100", "0x106"])
        # nothing may land in 0x9000 (outside bank 1)
        self.assertTrue(all(b == 0xFF for b in out[0x9000:0xA000]))

    def test_fixed_fields(self):
        jp, en = Table.parse(JP_TBL), Table.parse(EN_TBL)
        rom = bytearray(0x400)
        rom[0x200:0x20C] = bytes([0x10, 0x11, 0xEE, 0xEE, 0x12, 0xEE, 0xEE, 0xEE, 0x13, 0x14, 0x15, 0x16])
        block = {"name": "menu", "mode": "fixed", "pad": "0xEE", "fields": [["0x200", 4, 2], ["0x208", 4]]}
        s = dump_block(bytes(rom), block, jp)
        self.assertEqual([e["jp"] for e in s["entries"]], ["あい", "う", "えおかき"])
        self.assertEqual([e["length"] for e in s["entries"]], [4, 4, 4])
        s["entries"][0]["en"] = "Hi"
        s["entries"][2]["en"] = "Tool"
        insert_block(rom, block, s, en)
        self.assertEqual(bytes(rom[0x200:0x20C]), bytes([0x17, 0x32, 0xEE, 0xEE, 0x12, 0xEE, 0xEE, 0xEE,
                                                         0x23, 0x38, 0x38, 0x35]))
        s["entries"][2]["en"] = "Tools"
        self.assertTrue(any("too long for its field" in m for _, m in qa.check_entry(s["entries"][2], en, block)))
        with self.assertRaises(ValueError):
            insert_block(rom, block, s, en)

    def test_length_prefix(self):
        jp, en = Table.parse(JP_TBL), Table.parse(EN_TBL)
        rom = bytearray(0x8000)
        rom[0x5000:0x5003] = bytes([2, 0x10, 0x11])          # あい
        rom[0x5003:0x5007] = bytes([3, 0x12, 0x13, 0x14])    # うえお
        rom[0x100:0x104] = bytes([0x00, 0x50, 0x03, 0x50])
        block = {"name": "ann", "ptr_table": "0x100", "count": 2, "length_prefix": 1,
                 "mapping": {"type": "bank", "bank": 1}, "free_space": [["0x7000", "0x7FFF"]]}
        s = dump_block(bytes(rom), block, jp)
        self.assertEqual([e["jp"] for e in s["entries"]], ["あい", "うえお"])
        self.assertEqual([e["length"] for e in s["entries"]], [3, 4])
        s["entries"][0]["en"] = "Hello there"
        insert_block(rom, block, s, en)
        again = dump_block(bytes(rom), block, en)
        self.assertEqual(again["entries"][0]["jp"], "Hello there")
        # the untranslated string keeps its bytes, length prefix included
        off = int(again["entries"][1]["offset"], 0)
        self.assertEqual(bytes(rom[off:off + 4]), bytes([3, 0x12, 0x13, 0x14]))

    def test_qa(self):
        en = Table.parse(EN_TBL)
        e = {"id": "x", "jp": "<name 01>あ<wait><end>", "en": "Hello there friend<br>Hi<end>"}
        msgs = [m for _, m in qa.check_entry(e, en, BLOCK)]
        self.assertTrue(any("control codes differ" in m for m in msgs))
        self.assertTrue(any("line too long" in m for m in msgs))
        e["en"] = "<name 01>Hi!<wait><end>"
        self.assertEqual(qa.check_entry(e, en, BLOCK), [])
        e["en"] = "<name 01>あ<wait><end>"
        self.assertTrue(any(s == "error" for s, _ in qa.check_entry(e, en, BLOCK)))
        # undocumented raw bytes must survive translation too
        e = {"id": "y", "jp": "あ[99]<end>", "en": "Hi<end>"}
        self.assertTrue(any("control codes differ" in m for _, m in qa.check_entry(e, en, BLOCK)))
        e["en"] = "Hi[99]<end>"
        self.assertEqual(qa.check_entry(e, en, BLOCK), [])
        # a token used fewer times than in the original is named in the error
        e = {"id": "w", "jp": "<name 01>あ<name 01><end>", "en": "<name 01> hi<end>"}
        msgs = [m for _, m in qa.check_entry(e, en, BLOCK)]
        self.assertTrue(any("missing ['<name 01>']" in m for m in msgs), msgs)
        # a name token can be given its on-screen width
        e = {"id": "z", "jp": "<name 01>あ<end>", "en": "<name 01> is here<end>"}
        self.assertEqual(qa.check_entry(e, en, BLOCK), [])
        wide = {**BLOCK, "box": {**BLOCK["box"], "token_widths": {"<name 01>": 8}}}
        self.assertTrue(any("line too long (16/12)" in m for _, m in qa.check_entry(e, en, wide)))
        # an entry's own max_chars overrides the block's
        e = {"id": "v", "jp": "あ<end>", "en": "Hello there<end>", "max_chars": 5}
        self.assertTrue(any("line too long (11/5)" in m for _, m in qa.check_entry(e, en, BLOCK)))

    def test_plugin_block(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "tools"))
            with open(os.path.join(d, "tools", "fmt.py"), "w") as f:
                f.write("def dump(rom, block, table):\n"
                        "    return {'block': block['name'], 'entries': [{'id': 'a', 'jp': table.decode(rom, 0)[0]}]}\n"
                        "def insert(rom, block, script, table, log):\n"
                        "    rom[0] = 0x11\n"
                        "    return {'block': block['name'], 'strings': 1, 'translated': 1, 'moved': 0}\n")
            blk = {"name": "ev", "mode": "plugin", "module": "tools/fmt.py"}
            jp = Table.parse(JP_TBL)
            self.assertEqual(dump_block(b"\x10\xFF", blk, jp, root=d)["entries"][0]["jp"], "あ<end>")
            rom = bytearray(2)
            self.assertEqual(insert_block(rom, blk, {}, jp, root=d)["translated"], 1)
            self.assertEqual(rom[0], 0x11)


class AddressTest(unittest.TestCase):
    def test_snes(self):
        lo = Mapper({"type": "snes-lorom"})
        self.assertEqual(lo.to_file(0x018000), 0x8000)
        self.assertEqual(lo.to_ptr(0x8000), 0x018000)
        hi = Mapper({"type": "snes-hirom"})
        self.assertEqual(hi.to_file(hi.to_ptr(0x12345)), 0x12345)
        self.assertEqual(Mapper({"type": "gba"}).to_ptr(0x100), 0x08000100)


class GfxTest(unittest.TestCase):
    def test_roundtrip_all_formats(self):
        rnd = random.Random(1)
        for fmt, bpp in gfx.BPP.items():
            data = bytes(rnd.randrange(256) for _ in range(gfx.tile_bytes(fmt) * 20))
            img = gfx.rip(data, 0, 20, fmt, 8)
            self.assertEqual(gfx.pack(img, fmt, 20), data, fmt)

    def test_obj8x16_and_subpalettes(self):
        rnd = random.Random(3)
        data = bytes(rnd.randrange(256) for _ in range(16 * 12))
        self.assertEqual(gfx.tile_pos(3, 4, "obj8x16"), (8, 8))
        self.assertEqual(gfx.tile_pos(8, 4, "obj8x16"), (0, 16))
        pal = [(i, i, i) for i in range(32)]
        subs = [t % 8 for t in range(12)]
        img = gfx.rip(data, 0, 12, "2bpp_gb", 4, pal, "obj8x16", subs)
        self.assertEqual(img.size, (32, 32))
        self.assertTrue(any(v >= 4 for v in img.getdata()))  # sub-palettes in use
        self.assertEqual(gfx.pack(img, "2bpp_gb", 12, "obj8x16"), data)

    def test_known_2bpp(self):
        # GB: row 0 = pixel values 0..3 pattern
        tile = gfx.decode_tile(bytes([0b01010101, 0b00110011] + [0] * 14), "2bpp_gb")
        self.assertEqual(tile[0], [0, 1, 2, 3, 0, 1, 2, 3])


class CompressTest(unittest.TestCase):
    def test_lz10_rle(self):
        rnd = random.Random(2)
        src = bytes(rnd.choice(b"aaab\0\0\0xyz") for _ in range(3000)) + bytes(500)
        packed = compress.lz10_compress(src)
        self.assertLess(len(packed), len(src))
        self.assertEqual(compress.lz10_decompress(packed)[0], src)
        self.assertEqual(compress.rle_decompress(compress.rle_compress(src))[0], src)
        blob = bytes(64) + packed
        self.assertIn(64, [o for o, _, _ in compress.scan_lz10(blob)])


class PatchTest(unittest.TestCase):
    def test_bps_expanded_run(self):
        rnd = random.Random(3)
        src = bytes(rnd.randrange(256) for _ in range(5000))
        dst = bytearray(src) + b"\xFF" * 100000 + b"tail" + b"\x00" * 40
        dst[10:20] = b"\x01" * 10
        dst[100:200] = b"\x07" * 100
        p = patch.bps_create(src, bytes(dst))
        self.assertLess(len(p), 1000)
        self.assertEqual(patch.bps_apply(src, p), bytes(dst))

    def test_ips_bps(self):
        rnd = random.Random(3)
        src = bytes(rnd.randrange(256) for _ in range(50000))
        dst = bytearray(src)
        for _ in range(200):
            i = rnd.randrange(len(dst))
            dst[i] ^= 0xFF
        dst += b"extra data" * 50
        dst = bytes(dst)
        self.assertEqual(patch.ips_apply(src, patch.ips_create(src, dst)), dst)
        self.assertEqual(patch.bps_apply(src, patch.bps_create(src, dst)), dst)
        short = dst[:40000]
        self.assertEqual(patch.ips_apply(src, patch.ips_create(src, short)), short)
        self.assertEqual(patch.bps_apply(src, patch.bps_create(src, short)), short)
        with self.assertRaises(ValueError):
            patch.bps_apply(b"wrong" + src[5:], patch.bps_create(src, dst))


class SearchTest(unittest.TestCase):
    def test_relative(self):
        rom, _ = make_rom()
        hits = list(search.relative_search(bytes(rom), "かきくけこ", search.KANA_ORDERS["hira_plain"]))
        self.assertEqual(hits[0], (0x5004, 0x15))
        tbl = Table.parse(search.table_guess("かきく", 0x15, search.KANA_ORDERS["hira_plain"]))
        self.assertEqual(tbl.decode(bytes([0x10, 0x11]), stop_at_end=False)[0], "あい")
        latin = b"\x00\x21\x22\x23\x24"  # 'b','c','d','e' shifted
        self.assertEqual(list(search.relative_search(latin, "bcde")), [(1, 0x21)])

    def test_sjis(self):
        data = b"\x00\x00" + "こんにちは世界".encode("cp932") + b"\x00"
        self.assertEqual(list(search.find_sjis(data)), [(2, "こんにちは世界")])


class ChecksumTest(unittest.TestCase):
    def test_gba_gb(self):
        rom = bytearray(0x200)
        rom[0x04:0x08] = bytes.fromhex("24FFAE51"); rom[0xB2] = 0x96
        rominfo.fix_checksum(rom, "gba")
        self.assertEqual((sum(rom[0xA0:0xBE]) + 0x19) & 0xFF, 0)
        self.assertEqual(rominfo.detect(rom)["platform"], "gba")

    def test_gb_expand_header(self):
        rom = bytearray(0x200000)
        self.assertEqual(rominfo.set_rom_size(rom, "gbc"), "header ROM size 0x06")
        rom.extend(b"\xFF" * 0x200000)
        rominfo.set_rom_size(rom, "gbc")
        self.assertEqual(rom[0x148], 0x07)
        self.assertRaises(ValueError, rominfo.set_rom_size, rom + b"\0", "gb")


class Sm83Test(unittest.TestCase):
    def test_disasm(self):
        from rhtk import disasm
        code = bytes.fromhex("21506609 2a ea acd8 18fe cb37 e09c fe e8 38 29 c7")
        out = [(a, m, o) for a, _, m, o in disasm.disassemble(code, 0, len(code), "sm83", 0x3253)]
        self.assertEqual(out[0], (0x3253, "ld", "hl, $6650"))
        self.assertEqual(out[1][1:], ("add", "hl, bc"))
        self.assertEqual(out[2][1:], ("ld", "a, [hl+]"))
        self.assertEqual(out[3][1:], ("ld", "[$D8AC], a"))
        self.assertEqual(out[4], (0x325B, "jr", "$325B"))  # jr -2 loops on itself
        self.assertEqual(out[5][1:], ("swap", "a"))
        self.assertEqual(out[6][1:], ("ldh", "[$FF9C], a"))
        self.assertEqual(out[7][1:], ("cp", "$E8"))
        self.assertEqual(out[9][1:], ("rst", "$00"))


class CliTest(unittest.TestCase):
    def test_project_end_to_end(self):
        rom, _ = make_rom()
        with tempfile.TemporaryDirectory() as d:
            rp = os.path.join(d, "game.bin")
            with open(rp, "wb") as f:
                f.write(rom)
            proj = os.path.join(d, "proj")
            run = lambda *a: subprocess.run([sys.executable, "-m", "rhtk", *a], cwd=ROOT,
                                            capture_output=True, text=True)
            r = run("init", proj, "--rom", rp)
            self.assertEqual(r.returncode, 0, r.stderr)
            cfg = json.load(open(os.path.join(proj, "project.json")))
            cfg["blocks"] = [BLOCK]
            json.dump(cfg, open(os.path.join(proj, "project.json"), "w"))
            open(os.path.join(proj, "tables/jp.tbl"), "w").write(JP_TBL)
            open(os.path.join(proj, "tables/en.tbl"), "w").write(EN_TBL)
            r = run("dump", proj)
            self.assertEqual(r.returncode, 0, r.stderr)
            sp = os.path.join(proj, "script/dlg.json")
            s = json.load(open(sp, encoding="utf-8"))
            s["entries"][0]["en"] = "Hello!<end>"
            json.dump(s, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
            r = run("dump", proj)  # re-dump keeps translations
            self.assertEqual(json.load(open(sp, encoding="utf-8"))["entries"][0]["en"], "Hello!<end>")
            r = run("build", proj)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            out = os.path.join(proj, "build/proj-en.bin")
            bps = os.path.join(proj, "build/proj-en.bps")
            self.assertEqual(patch.bps_apply(rom, open(bps, "rb").read()), open(out, "rb").read())
            r = run("qa", proj)
            self.assertIn("1/3 translated", r.stdout)


if __name__ == "__main__":
    unittest.main()
