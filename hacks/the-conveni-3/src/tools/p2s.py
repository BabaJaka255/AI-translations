"""Extract members of a PCSX2 save state (.p2s is a zip with Zstd members). Usage: p2s.py state.p2s outdir [member...]"""
import os, sys, zipfile, zstandard
src, dest, *want = sys.argv[1:]
os.makedirs(dest, exist_ok=True)
z = zipfile.ZipFile(src)
for i in z.infolist():
    if want and i.filename not in want:
        continue
    raw = z.open(i) if i.compress_type != 93 else None
    if i.compress_type == 93:
        z.fp.seek(i.header_offset); h = z.fp.read(30)
        n, m = int.from_bytes(h[26:28], "little"), int.from_bytes(h[28:30], "little")
        z.fp.seek(i.header_offset + 30 + n + m)
        data = zstandard.ZstdDecompressor().decompress(z.fp.read(i.compress_size), max_output_size=i.file_size)
    else:
        data = raw.read()
    open(os.path.join(dest, i.filename), "wb").write(data)
    print(i.filename, len(data))
