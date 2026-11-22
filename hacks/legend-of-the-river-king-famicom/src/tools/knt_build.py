"""Build the English Kawa no Nushi Tsuri (FC) ROM and BPS patch.

  python3 tools/knt_build.py            # from the game folder

Steps: expand PRG 128K -> 256K (original banks 0-13 stay put, the fixed
banks 14/15 move to 30/31, banks 14-29 are new), draw the English font,
assemble the text hooks, place every translated line in the text banks
(14-17) and point the game's stubs at them.
"""
import json, os, subprocess, sys, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import knt_font
import knt_windows
import knt_names
import knt_gfx
import knt_logo
from knt_common import HEADER, PRG_ORIG

BANK = 0x2000
NEW_PRG = 0x40000
TEXT_BANKS = [14, 15, 16, 17]          # index 0-3 in the pointer encoding
ROW = 18
WIDTH = {"B1": 15, "A0": 2, "B0": 1, "C0": 3, "C1": 3, "C2": 3, "C3": 3, "C5": 3,
         "F0": 3, "F1": 17, "F2": 17, "F3": 17, "B2": 2, "B3": 4, "D0": 0}
NEWROW = 0x1A                          # row-break code inside English lines (see text_hook.s)
TMP = os.environ.get("KNT_TMP", "/tmp/knt_build")


def expand(rom):
    hdr = bytearray(rom[:HEADER]); P = rom[HEADER:HEADER + PRG_ORIG]; C = rom[HEADER + PRG_ORIG:]
    newp = bytearray(b"\xff" * NEW_PRG)
    newp[0:14 * BANK] = P[0:14 * BANK]
    newp[30 * BANK:32 * BANK] = P[14 * BANK:16 * BANK]
    hdr[4] = NEW_PRG // 0x4000
    return bytearray(hdr) + newp + bytearray(C)


def bank_off(b):
    return HEADER + b * BANK


def cpu_fixed(addr):
    """File offset of a CPU address in the fixed banks of the expanded ROM."""
    return bank_off(30) + (addr - 0xC000)


class Encoder:
    def __init__(self):
        self.codes = dict(knt_font.CODES)
        for i in range(10):
            self.codes[str(i)] = i
        self.codes[" "] = 0xFE

    def tokens(self, s):
        out = []; i = 0
        while i < len(s):
            if s[i] == "<":
                j = s.index(">", i); out.append(("code", s[i + 1:j])); i = j + 1
            elif s[i] == "|":
                out.append(("row", None)); i += 1
            else:
                out.append(("ch", s[i])); i += 1
        return out

    def width(self, toks):
        return sum(1 if t == "ch" else WIDTH.get(v, 0) if t == "code" else 0 for t, v in toks)

    def layout(self, s):
        """Return (row1, row2) token lists; row1 None if the line fits one row."""
        toks = self.tokens(s)
        if any(t == "row" for t, _ in toks):
            k = [t for t, _ in toks].index("row")
            return toks[:k], toks[k + 1:]
        if self.width(toks) <= ROW:
            return None, toks
        # break at the last space that keeps row 1 within 18
        best = None
        for k, (t, v) in enumerate(toks):
            if t == "ch" and v == " " and self.width(toks[:k]) <= ROW:
                best = k
        if best is None:
            raise ValueError(f"cannot wrap: {s!r}")
        return toks[:best], toks[best + 1:]

    def enc_toks(self, toks):
        b = bytearray()
        for t, v in toks:
            if t == "ch":
                if v not in self.codes:
                    raise KeyError(f"no glyph for {v!r}")
                b.append(self.codes[v])
            else:
                b.append(int(v, 16))
        return b

    def line(self, s):
        r1, r2 = self.layout(s)
        if r2 is not None and self.width(r2) > ROW:
            raise ValueError(f"line too long ({self.width(r1 or [])}+{self.width(r2)}): {s!r}")
        b = bytearray()
        if r1 is not None:
            w = self.width(r1)
            if w > ROW:
                raise ValueError(f"row 1 too long: {s!r}")
            b += self.enc_toks(r1) + bytes([NEWROW])   # the hook pads the top row at run time
        b += self.enc_toks(r2) + b"\xff"
        return b


class TextBanks:
    def __init__(self, rom, header_size=0x100):
        self.rom = rom
        self.pos = {i: header_size for i in range(len(TEXT_BANKS))}
        for i, b in enumerate(TEXT_BANKS):
            rom[bank_off(b)] = b          # signature checked by TXT_BEGIN

    def put(self, data):
        for i, b in enumerate(TEXT_BANKS):
            if self.pos[i] + len(data) <= BANK:
                o = self.pos[i]; self.pos[i] += len(data)
                self.rom[bank_off(b) + o:bank_off(b) + o + len(data)] = data
                return i, 0x8000 + o
        raise RuntimeError("text banks full")

    @staticmethod
    def enc_ptr(idx, addr):
        return (idx << 5) | ((addr >> 8) & 0x1F), addr & 0xFF


def assemble(src="text_hook.s", cfg="hook.cfg"):
    os.makedirs(TMP, exist_ok=True)
    asm = os.path.join(HERE, "..", "asm")
    name = os.path.splitext(src)[0]
    subprocess.run(["ca65", "-g", os.path.join(asm, src), "-o", f"{TMP}/{name}.o"], check=True)
    subprocess.run(["ld65", "-C", os.path.join(asm, cfg), f"{TMP}/{name}.o", "-o", f"{TMP}/{name}.bin",
                    "-Ln", f"{TMP}/{name}.lbl"], check=True)
    labels = {}
    for ln in open(f"{TMP}/{name}.lbl"):
        _, a, n = ln.split()
        if not n.startswith(".@"):
            labels[n.lstrip(".")] = int(a, 16)
    return open(f"{TMP}/{name}.bin", "rb").read(), labels


def load_en(path):
    en = {}
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("#") or "\t" not in ln:
            continue
        i, t = ln.rstrip("\n").split("\t", 1)
        en[i] = t
    return en


def main():
    rom = expand(open("rom/original.nes", "rb").read())
    # font (CHR 0x1000, after the expanded PRG)
    knt_font.apply(rom, HEADER + NEW_PRG + 0x1000)
    knt_gfx.apply(rom, HEADER + NEW_PRG)
    print("title logo tiles:", knt_logo.apply(rom, HEADER + NEW_PRG))
    # hooks
    code, lab = assemble()
    o = cpu_fixed(0xFE42); rom[o:o + len(code)] = code
    tb, te = lab["TXT_BEGIN"], lab["TXT_END"]
    rom[cpu_fixed(0xF127):cpu_fixed(0xF127) + 4] = bytes([0x20, tb & 0xFF, tb >> 8, 0xEA])
    rom[cpu_fixed(0xF1EB):cpu_fixed(0xF1EB) + 7] = bytes([0x20, te & 0xFF, te >> 8, 0xEA, 0xEA, 0xEA, 0xEA])
    nr = lab["NEWROW"]
    knt_windows.patch(rom, 15, 0xF13C, [0x85, 0x0C, 0x8A], [0x4C, nr & 0xFF, nr >> 8])
    # typewriter: top row first, then bottom row
    rv, re_ = lab["REVEAL"], lab["REVEALEND"]
    knt_windows.patch(rom, 15, 0xE56E, [0xBD, 0x50, 0x06, 0x8D, 0x07, 0x20, 0xB9, 0x50, 0x06, 0x8D, 0x07, 0x20],
                      [0x20, rv & 0xFF, rv >> 8] + [0xEA] * 9)
    knt_windows.patch(rom, 15, 0xE5A0, [0xCE, 0xBC, 0x07, 0xD0, 0x31], [0x20, re_ & 0xFF, re_ >> 8, 0xD0, 0x31])
    # menu windows
    knt_windows.apply(rom, assemble("menu13.s", "menu13.cfg"), assemble("status9.s", "status9.cfg"), (code, lab))
    # text
    enc = Encoder(); banks = TextBanks(rom)
    lines = json.load(open("script/lines.json"))
    en = load_en("script/en_lines.txt")
    for e in lines:
        e["en"] = en.get(e["id"], "")
    done = 0; errors = []
    seqs = {}
    for e in lines:
        if not e["en"]:
            continue
        try:
            data = enc.line(e["en"])
        except Exception as ex:
            errors.append(f"{e['id']}: {ex}"); continue
        ref0 = e["refs"][0]
        if ref0["type"] == "seq":
            seqs.setdefault(ref0["at"], {})[ref0["index"]] = (data, ref0["count"])
            continue
        idx, addr = banks.put(data)
        hi, lo = banks.enc_ptr(idx, addr)
        for r in e["refs"]:
            at = HEADER + r["at"]        # PRG offsets below bank 14 are unchanged
            assert rom[at] == 0xA2 and rom[at + 2] == 0xA0
            rom[at + 1] = hi; rom[at + 3] = lo
        done += 1
    for at, parts in seqs.items():
        count = next(iter(parts.values()))[1]
        if len(parts) != count:
            errors.append(f"seq {at:05X}: {len(parts)}/{count} lines translated, left in Japanese"); continue
        blob = b"".join(parts[i][0] for i in range(count))
        idx, addr = banks.put(blob)
        hi, lo = banks.enc_ptr(idx, addr)
        a = HEADER + at
        assert rom[a] == 0xA9 and rom[a + 4] == 0xA9
        rom[a + 1] = hi; rom[a + 5] = lo
        done += count
    # catch messages: three whole lines per fish, pointed at by FISHPTR (bank 10)
    fcode, fl = assemble("fish10.s", "fish10.cfg")
    o = knt_windows.off(10, 0xBD65); rom[o:o + len(fcode)] = fcode
    for i, (_, name, art) in enumerate(knt_names.FISH):
        for v, cands in enumerate(knt_names.catch_lines(name, art)):
            data = None
            for text in cands:
                try:
                    data = enc.line(text); break
                except ValueError:
                    pass
            if data is None:
                errors.append(f"fish {i}: no candidate fits: {cands}"); continue
            idx, addr = banks.put(data)
            hi, lo = banks.enc_ptr(idx, addr)
            rom[knt_windows.off(10, fl["FLO"]) + i * 3 + v] = lo
            rom[knt_windows.off(10, fl["FHI"]) + i * 3 + v] = hi
    knt_windows.patch(rom, 10, 0xA8F4, [0x20, 0x51, 0xA1], [0x20, fl["FISHPTR"] & 0xFF, fl["FISHPTR"] >> 8])
    # creature names (<B1>): copied into every text bank header, read while the line's bank is mapped
    offs = bytearray(); names = bytearray()
    for _, n in knt_names.CREATURES:
        offs.append(len(names)); names += enc.enc_toks(enc.tokens(n)) + b"\xff"
    assert 0x30 + len(names) <= 0x100
    for b in TEXT_BANKS:
        rom[bank_off(b) + 0x10:bank_off(b) + 0x10 + len(offs)] = offs
        rom[bank_off(b) + 0x30:bank_off(b) + 0x30 + len(names)] = names
    knt_windows.patch(rom, 15, 0xF3E0, [0xBC, 0xD8, 0xF4], [0xBC, 0x10, 0x80])
    knt_windows.patch(rom, 15, 0xF3E5, [0xB9, 0xEE, 0xF4], [0xB9, 0x30, 0x80])
    for er in errors:
        print("ERROR", er)
    os.makedirs("build", exist_ok=True)
    out = "build/kawa-no-nushi-tsuri-fc-en.nes"
    open(out, "wb").write(rom)
    print(f"{done} lines placed; text bank use:", {TEXT_BANKS[i]: hex(p) for i, p in banks.pos.items()})
    print(out, f"CRC32 {zlib.crc32(rom):08X}")
    if not errors:
        make_bps(out)
    return 1 if errors else 0


def make_bps(out):
    """Write the BPS next to the ROM with the romhack toolkit (rhtk), if it can be found:
    $RHTK, ../toolkit (published source tree) or ../../../romhack-toolkit (workspace)."""
    for d in (os.environ.get("RHTK"), os.path.join(HERE, "..", "toolkit"),
              os.path.join(HERE, "..", "..", "..", "romhack-toolkit")):
        if d and os.path.exists(os.path.join(d, "rhtk.sh")):
            bps = os.path.splitext(out)[0] + ".bps"
            subprocess.run(["sh", os.path.join(d, "rhtk.sh"), "patch", "make", "rom/original.nes", out, bps], check=True)
            return
    print("rhtk toolkit not found: skipped the BPS (set RHTK to the toolkit folder)")


if __name__ == "__main__":
    sys.exit(main())
