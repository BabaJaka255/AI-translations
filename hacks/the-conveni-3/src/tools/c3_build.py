"""Build the English disc image of The Conveni 3.

Usage: python3 c3_build.py <original.iso> <out.iso> [--report build/report.json] [--only-translated]

Reads script/elf.json and script/cn3.json (entries with a non-empty "en"), then:
  1. ELF: space advance 15 -> SPACE_PX, fonts small/large/talk rebuilt with letter-pair glyphs
     (pairs ranked from all the English in the script), English written into each string's slot.
  2. ALLDATA.PAC: truefont.tex replaced (font pages), checksums fixed in the ELF.
  3. PAC/CN3.PAC: English written into every location of each entry, members recompressed.
  4. The image is copied and the three files replaced (rhtk ps2 patch).
A string that doesn't fit is left in Japanese and listed in the report with its byte count and limit.
The original image is never modified. Make it once with `rhtk ps2 to-iso` from the .bin in rom/*.7z.
"""
import argparse
import json
import os
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get("RHTK", os.path.join(GAME, "toolkit")))
import c3_glyphs as G  # noqa: E402
import c3_gfx  # noqa: E402
import c3_pad  # noqa: E402
import c3_gcode  # noqa: E402
import c3_wordwrap  # noqa: E402
import c3_title  # noqa: E402
import c3_yen  # noqa: E402
from c3pac import fix_sum, lzs_compress, lzs_decompress, pac_build, pac_read  # noqa: E402
from rhtk import ps2  # noqa: E402

SPACE_PX = 6
SPACE_SITES = (0x1BB9F0, 0x1BBA2C, 0x1BBF8C, 0x1BBFC8, 0x1BC920, 0x1BC95C, 0x1BCCF8, 0x1BCD34)
FIELDS = (16, 32, 64, 128, 224, 256, 259)  # slot sizes seen in CN3 records
ELF_DELTA = 0x10F000  # vaddr - file offset
# ELF ranges left unused once tools/c3_yen.py replaces the 億/万 money code (file offsets, [start, end)):
# the old money format strings and the string-table entries only the old formatter read
FREE = [(0x418420, 0x418468), (0x418518, 0x418538), (0x426C08, 0x426C68)]
FALLBACK_CORPUS = os.path.join(GAME, "toolkit", "docs", "STYLE_GUIDE.md")


def elf_off(vaddr):
    return vaddr - 0x110000 + 0x1000


def field_cap(jp_bytes, measured):
    """Bytes a translation may use (terminator excluded): the measured zero run, but not past the
    smallest standard field that holds the Japanese (the zero run can continue into an empty field)."""
    std = next((f for f in FIELDS if f >= jp_bytes + 1), None)
    return min(measured, std - 1) if std else measured


def put(buf, off, data, cap):
    buf[off:off + cap + 1] = data + b"\0" * (cap + 1 - len(data))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iso")
    ap.add_argument("out")
    ap.add_argument("--report", default=os.path.join(GAME, "build", "report.json"))
    ap.add_argument("--script", default=os.path.join(GAME, "script"), help="folder with elf.json and cn3.json")
    ap.add_argument("--extra", default=None, help="JSON list of [elf_offset, english] test strings")
    ap.add_argument("--no-yen", action="store_true", help="keep the original 億/万 money format")
    a = ap.parse_args()

    elf_s = json.load(open(os.path.join(a.script, "elf.json"), encoding="utf-8"))["entries"]
    cn3_s = json.load(open(os.path.join(a.script, "cn3.json"), encoding="utf-8"))["entries"]
    extra = json.load(open(a.extra, encoding="utf-8")) if a.extra else []
    english = [e["en"] for e in elf_s + cn3_s if e.get("en") and not e.get("skip")] + [s for _, s in extra]
    corpus = "\n".join(english)
    if len(corpus) < 5000:  # early builds: pad the ranking with ordinary English
        corpus += "\n" + open(FALLBACK_CORPUS, encoding="utf-8").read()

    with ps2.Iso(a.iso) as iso:
        elf = bytearray(iso.read_file("SLPM_623.22"))
        alldata = iso.read_file("ALLDATA.PAC")
        cn3 = iso.read_file("PAC/CN3.PAC")
        onetex = iso.read_file("ONETEX.PAC") if any(e["pac"] == "ONETEX" for e in c3_gfx.load_edits()) else None
    orig_elf = bytes(elf)

    for v in SPACE_SITES:
        o = elf_off(v)
        w = struct.unpack_from("<I", elf, o)[0]
        assert w & 0xFFFF == 0xF, hex(v)
        struct.pack_into("<I", elf, o, (w & 0xFFFF0000) | SPACE_PX)

    if not a.no_yen:  # Western money format: ¥230,000,000 (tools/c3_yen.py)
        c3_yen.patch(elf)
        c3_pad.patch(elf)  # /Qn = number param with 2 digits (clock minutes)
        c3_gcode.patch(elf)  # /Gn = number param as ¥ with commas (fixture panel price/upkeep)

    files = pac_read(alldata)
    first = struct.unpack_from("<I", alldata, 12)[0]
    names = [m.decode() for m in alldata[12 + 8 * len(files):first].split(b"\0") if m]
    tf_i, sn_i = names.index("truefont.tex"), names.index("sel_name.tex")
    tf = bytearray(lzs_decompress(files[tf_i]))
    fonts = G.build(elf, tf, lzs_decompress(files[sn_i]), G.pair_ranking(corpus),
                    pick=None if a.no_yen else c3_wordwrap.picker())
    pairs = fonts["pairs"]
    if not a.no_yen:  # word wrap in the Fixture details panel (tools/c3_wordwrap.py)
        c3_wordwrap.check(pairs)
        c3_wordwrap.patch(elf)
    report = {"pairs": len(pairs), "elf": {"written": 0, "too_long": []}, "cn3": {"written": 0, "too_long": []},
              "no_glyph": []}

    def enc(text, where, nopairs=False):
        try:
            return G.encode(text, {} if nopairs else pairs)
        except ValueError as e:
            report["no_glyph"].append({"where": where, "error": str(e)})
            return None

    repoint = []
    for e in elf_s:
        if not e.get("en") or e.get("skip"):
            continue
        if e.get("repoint"):  # written into free space after the pass, pointers updated
            repoint.append(e)
            continue
        off = int(e["offset"], 16)
        b = enc(e["en"], e["offset"], e.get("nopairs"))
        if b is None:
            continue
        cap = e["length"]
        if e.get("field"):  # record layout known
            cap = min(cap, e["field"] - 1)
        elif e["kind"] == "code":
            cap = field_cap(len(e["jp"].encode("cp932")), cap)
        if len(b) > cap:
            report["elf"]["too_long"].append({"id": e["id"], "offset": e["offset"], "bytes": len(b), "cap": cap,
                                              "en": e["en"]})
            continue
        put(elf, off, b, cap)
        report["elf"]["written"] += 1
    # strings that need more room than their slot: move them into space the yen patch freed
    free = [list(r) for r in (FREE if not a.no_yen else [])]
    for e in sorted(repoint, key=lambda e: -len(e["en"])):
        b = enc(e["en"], e["offset"], e.get("nopairs"))
        if b is None:
            continue
        slot = next((r for r in free if r[1] - r[0] >= len(b) + 1), None)
        if slot is None or not e["pointers"]:
            report["elf"]["too_long"].append({"id": e["id"], "offset": e["offset"], "bytes": len(b), "cap": 0,
                                              "en": e["en"], "why": "no free space to repoint"})
            continue
        at = slot[0]
        elf[at:at + len(b) + 1] = b + b"\0"
        slot[0] = (at + len(b) + 1 + 3) & ~3
        for ptr in e["pointers"]:
            struct.pack_into("<I", elf, int(ptr, 16), at + ELF_DELTA)
        report["elf"]["written"] += 1
    # name-entry "Back" (id 429, a 7-byte slot that "Ｂａｃｋ" overflows; the bar can't draw pairs): point its two
    # lui/addiu users at the repointed copy of the bottom bar's own "Back" (id 566, pointer at 0x249894)
    back = struct.unpack_from("<I", elf, 0x249894)[0]
    if elf[back - ELF_DELTA:back - ELF_DELTA + 8] == "Ｂａｃｋ".encode("cp932"):
        for lui, addiu in ((0x48058, 0x48064), (0x481CC, 0x481D0)):
            assert struct.unpack_from("<I", orig_elf, lui)[0] == 0x3C050053, hex(lui)
            assert struct.unpack_from("<I", orig_elf, addiu)[0] == 0x24A526A0, hex(addiu)
            struct.pack_into("<I", elf, lui, 0x3C050000 | ((back + 0x8000) >> 16))
            struct.pack_into("<I", elf, addiu, 0x24A50000 | (back & 0xFFFF))
        report["elf"]["too_long"] = [t for t in report["elf"]["too_long"] if t["id"] != 429]
    for off, text in extra:
        off = int(off, 16)
        j = orig_elf.index(b"\0", off)
        while orig_elf[j] == 0:
            j += 1
        b = G.encode(text, pairs)
        assert len(b) < j - off, (text, len(b), j - off)
        put(elf, off, b, j - off - 1)

    # CN3.PAC
    members = pac_read(cn3)
    raw = {i: bytearray(lzs_decompress(m)) if m[:4] == b"LZS\0" else bytearray(m) for i, m in enumerate(members)}
    changed = set()
    for e in cn3_s:
        if not e.get("en"):
            continue
        if e.get("lead"):  # career lines: "   Y" sits before the entry; {y} in the English moves it
            lead = e["lead"]
            for m, o, _ in e["where"]:
                o = int(o, 16)
                y = bytes(raw[m][o - lead:o]).decode("ascii").strip()
                b = enc(e["en"].replace("{y}", y), f"cn3 #{e['id']}", e.get("nopairs"))
                if b is None or len(b) > e["cap"] + lead:
                    report["cn3"]["too_long"].append({"id": e["id"], "cap": e["cap"] + lead, "en": e["en"]})
                    break
                put(raw[m], o - lead, b, e["cap"] + lead)
                changed.add(m)
            else:
                report["cn3"]["written"] += 1
            continue
        b = enc(e["en"], f"cn3 #{e['id']}", e.get("nopairs"))
        if b is None:
            continue
        # many copies: the smallest zero run over all of them is the field; a single copy may run on
        # into an empty neighbouring field, so clamp it to a standard size
        cap = e["cap"] if len(e["where"]) >= 3 or e.get("field") else field_cap(len(e["jp"].encode("cp932")), e["cap"])
        if e.get("field"):  # slot size known from the record layout
            cap = min(e["cap"], e["field"] - 1)
        cap = min(cap, 258)
        if len(b) > cap:
            report["cn3"]["too_long"].append({"id": e["id"], "bytes": len(b), "cap": cap, "en": e["en"]})
            continue
        for m, o, _ in e["where"]:
            put(raw[m], int(o, 16), b, cap)
            changed.add(m)
        report["cn3"]["written"] += 1
    if changed:
        for m in changed:
            new = lzs_compress(bytes(raw[m])) if members[m][:4] == b"LZS\0" else bytes(raw[m])
            try:
                fix_sum(elf, members[m], new)
            except KeyError:
                pass
            members[m] = new
        cfirst = struct.unpack_from("<I", cn3, 12)[0]
        new_cn3 = pac_build(members, first=cfirst, header=cn3[:cfirst])
        try:
            fix_sum(elf, cn3, new_cn3)
        except KeyError:
            report["cn3_whole_file_checksum"] = "no record"
    else:
        new_cn3 = None

    old_tf = files[tf_i]
    files[tf_i] = lzs_compress(bytes(tf))
    fix_sum(elf, old_tf, files[tf_i])
    # texture labels (gfx/edits.json)
    gfx = c3_gfx.load_edits()
    for m, (old, new) in c3_gfx.apply_alldata(files, gfx, lzs_decompress, lzs_compress).items():
        try:
            fix_sum(elf, old, new)
        except KeyError:
            report.setdefault("gfx_no_checksum", []).append(m)
    report["gfx_edits"] = len(gfx)
    for m, old, new in c3_title.apply(files, lzs_decompress, lzs_compress):  # title subtitle (32-bit picture)
        try:
            fix_sum(elf, old, new)
        except KeyError:
            report.setdefault("gfx_no_checksum", []).append(m)
    new_onetex = None
    if onetex is not None:  # plain TIM members, edited in place (same sizes)
        ot = pac_read(onetex)
        changed_ot = c3_gfx.apply_onetex(ot, gfx)
        buf = bytearray(onetex)
        for m, (old, new) in changed_ot.items():
            at = buf.find(old)
            assert at >= 0 and len(old) == len(new)
            buf[at:at + len(new)] = new
            try:
                fix_sum(elf, old, new)
            except KeyError:
                pass
        try:
            fix_sum(elf, onetex, bytes(buf))
        except KeyError:
            pass
        new_onetex = bytes(buf)
    new_all = pac_build(files, first=first, header=alldata[:first])

    with tempfile.TemporaryDirectory() as tmp:
        rep = {}
        for name, data in (("SLPM_623.22", elf), ("ALLDATA.PAC", new_all), ("PAC/CN3.PAC", new_cn3),
                           ("ONETEX.PAC", new_onetex)):
            if data is None:
                continue
            p = os.path.join(tmp, name.replace("/", "_"))
            open(p, "wb").write(data)
            rep[name] = p
        moves = ps2.patch_iso(a.iso, a.out, rep, log=lambda *x: None)
    report["moved_files"] = [m["path"] for m in moves if m["moved"]]
    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    json.dump(report, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pairs {len(pairs)}; ELF {report['elf']['written']} written, {len(report['elf']['too_long'])} too long; "
          f"CN3 {report['cn3']['written']} written, {len(report['cn3']['too_long'])} too long; "
          f"{len(report['no_glyph'])} without glyphs; moved: {report['moved_files']}")


if __name__ == "__main__":
    main()
