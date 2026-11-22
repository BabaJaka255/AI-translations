"""Dump every texture of ALLDATA.PAC and ONETEX.PAC to PNG, plus contact sheets for a quick look.

Usage: python3 c3_texdump.py <original.iso> <outdir>
Names: alldata_<member>_<name>_<tim>.png, onetex_<member>.png; sheets/sheet_NN.png (labelled thumbnails).
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get("RHTK", os.path.join(HERE, "..", "toolkit")))
import c3tex  # noqa: E402
from c3pac import lzs_decompress, pac_read  # noqa: E402
from rhtk import ps2  # noqa: E402


def names_of(pac, n):
    first = struct.unpack_from("<I", pac, 12)[0]
    return [m.decode("ascii", "replace") for m in pac[12 + 8 * n:first].split(b"\0") if m]


def main(iso_path, out):
    from PIL import Image, ImageDraw
    os.makedirs(out, exist_ok=True)
    with ps2.Iso(iso_path) as iso:
        alldata = iso.read_file("ALLDATA.PAC")
        onetex = iso.read_file("ONETEX.PAC")
    done = []
    files = pac_read(alldata)
    nm = names_of(alldata, len(files))
    for i, m in enumerate(files):
        d = lzs_decompress(m) if m[:4] == b"LZS\0" else m
        if d[:4] != b"TEX\0":
            continue
        for k, (b, _) in enumerate(c3tex.tex_entries(d)):
            p = os.path.join(out, f"alldata_{i:02d}_{nm[i] if i < len(nm) else ''}_{k:02d}.png")
            try:
                c3tex.tim_image(d, b).save(p)
                done.append(p)
            except Exception as e:  # 16/24 bpp or odd layouts
                print("alldata", i, k, e)
    for i, m in enumerate(pac_read(onetex)):
        d = lzs_decompress(m) if m[:4] == b"LZS\0" else m
        p = os.path.join(out, f"onetex_{i:03d}.png")
        try:
            if d[:4] == b"TEX\0":
                for k, (b, _) in enumerate(c3tex.tex_entries(d)):
                    q = p.replace(".png", f"_{k:02d}.png")
                    c3tex.tim_image(d, b).save(q)
                    done.append(q)
            else:
                c3tex.tim_image(d, 0).save(p)
                done.append(p)
        except Exception as e:
            print("onetex", i, e)
    os.makedirs(os.path.join(out, "sheets"), exist_ok=True)
    T = 300
    per = 12
    for s in range(0, len(done), per):
        sheet = Image.new("RGB", (T * 4, (T + 14) * 3), (40, 40, 40))
        dr = ImageDraw.Draw(sheet)
        for j, p in enumerate(done[s:s + per]):
            im = Image.open(p).convert("RGBA")
            im.thumbnail((T, T))
            x, y = (j % 4) * T, (j // 4) * (T + 14)
            sheet.paste(im, (x, y + 14), im)
            dr.text((x + 2, y), os.path.basename(p)[:44], fill=(255, 255, 0))
        sheet.save(os.path.join(out, "sheets", f"sheet_{s // per:02d}.png"))
    print(len(done), "textures")


if __name__ == "__main__":
    main(*sys.argv[1:3])
