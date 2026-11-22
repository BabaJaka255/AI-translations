# Savestate RAM patch used to find the angel crash (2026-11-02). BASE = member 24 in RAM for build 12.
"""Make a patched savestate: mkstate.py in.p2s out.p2s variant"""
import os, sys, zipfile, zstandard, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src, dst, var = sys.argv[1:4]
z = zipfile.ZipFile(src)
def member(i):
    if i.compress_type == 93:
        z.fp.seek(i.header_offset); h = z.fp.read(30)
        n, m = int.from_bytes(h[26:28], "little"), int.from_bytes(h[28:30], "little")
        z.fp.seek(i.header_offset + 30 + n + m)
        return zstandard.ZstdDecompressor().decompress(z.fp.read(i.compress_size), max_output_size=i.file_size)
    return z.open(i).read()
BASE = 0x1D7DFC8
es = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "script", "cn3.json")))["entries"]
tips = [e for e in es if any(w[0] == 24 for w in e["where"])]
orig = open("/tmp/c3/m24_orig.bin", "rb").read()
out = zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED)
for i in z.infolist():
    data = member(i)
    if i.filename == "eeMemory.bin":
        ram = bytearray(data)
        for e in tips:
            for w in e["where"]:
                if w[0] != 24: continue
                o = int(w[1], 16)
                if var == "jp":
                    s = e["jp"].encode("cp932")
                elif var.startswith("jp+"):
                    s = (var[3:] + e["jp"]).encode("cp932")
                else:
                    import c3_glyphs as G
                    text = {"fw": "Add plants and decor for/rbetter service./kA",
                            "fws": "Add plants and decor./kA",
                            "short": "Add plants./kA",
                            "shortk": "Add plants.ね/kA",
                            "four": "Add plants and decor/rfor better service,/rand your rating/rwill rise, I promise./kA",
                            "shortk0": "ねAdd plants./kA"}[var]
                    b = G.encode(text, {})
                    s = b if var in ("short", "four") else b.replace(b" ", b"\x81\x40")
                ram[BASE + o:BASE + o + 224] = s + b"\0" * (224 - len(s))
        data = bytes(ram)
    out.writestr(i.filename, data)
out.close()
print("ok", var)
