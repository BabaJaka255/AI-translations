"""Patch RAM in a PCSX2 savestate: c3_ram_patch.py in.p2s out.p2s ADDR=HEXBYTES|ADDR="text" ...
Also: c3_ram_patch.py in.p2s - dump ADDR LEN   (print RAM bytes)."""
import sys, zipfile, zstandard

def members(path):
    z = zipfile.ZipFile(path)
    for i in z.infolist():
        if i.compress_type == 93:
            z.fp.seek(i.header_offset); h = z.fp.read(30)
            n, m = int.from_bytes(h[26:28], "little"), int.from_bytes(h[28:30], "little")
            z.fp.seek(i.header_offset + 30 + n + m)
            yield i.filename, zstandard.ZstdDecompressor().decompress(z.fp.read(i.compress_size), max_output_size=i.file_size)
        else:
            yield i.filename, z.open(i).read()

def main(src, dst, *args):
    if dst == "-":
        ram = dict(members(src))["eeMemory.bin"]
        a, n = int(args[1], 16), int(args[2], 0)
        print(ram[a:a + n]); print(ram[a:a + n].hex(" "))
        return
    out = zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED)
    for name, data in members(src):
        if name == "eeMemory.bin":
            ram = bytearray(data)
            for p in args:
                a, v = p.split("=", 1)
                b = v[1:-1].encode("cp932") if v.startswith('"') else bytes.fromhex(v)
                ram[int(a, 16):int(a, 16) + len(b)] = b
            data = bytes(ram)
        out.writestr(name, data)
    out.close()

if __name__ == "__main__":
    main(*sys.argv[1:])
