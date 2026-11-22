"""The Conveni 3 textures.

TIM (Masterpiece variant of the PS1 TIM): u32 0x10, u32 flags (low 2 bits: 0=4bpp, 1=8bpp, 2=16bpp,
3=24bpp; bit 3 = has CLUT), then blocks of u32 length (incl. 12-byte header), u16 x, y, w, h, data.
CLUT entries are 32-bit RGBA (PS2 alpha, 0x80 = opaque). Image width is in pixels.
TEX: "TEX\\0----", u32 count, u32 names_off (64-byte names), u32 ?, then (u32 offset, u32 size) pairs of TIMs at 0x14.
"""
import struct
import sys


def tim_parse(d, base=0):
    magic, flags = struct.unpack_from("<II", d, base)
    if magic != 0x10:
        raise ValueError("not a TIM")
    bpp = {0: 4, 1: 8, 2: 16, 3: 24}[flags & 3]
    o = base + 8
    clut = None
    if flags & 8:
        L, x, y, w, h = struct.unpack_from("<IHHHH", d, o)
        raw = d[o + 12:o + L]
        clut = {"off": o + 12, "n": len(raw) // 4,
                "colors": [(raw[i], raw[i + 1], raw[i + 2], min(255, raw[i + 3] * 2)) for i in range(0, len(raw) - 3, 4)]}
        o += L
    L, x, y, w, h = struct.unpack_from("<IHHHH", d, o)
    return {"bpp": bpp, "clut": clut, "img_off": o + 12, "img_len": L - 12, "w": w, "h": h}


def tim_image(d, base=0, pal=0):
    from PIL import Image
    t = tim_parse(d, base)
    w, h, bpp = t["w"], t["h"], t["bpp"]
    raw = d[t["img_off"]:t["img_off"] + t["img_len"]]
    if bpp == 4 and len(raw) < w * h // 2:
        w *= 4  # width given in 16-bit units
    if bpp == 8 and len(raw) < w * h:
        w *= 2
    if bpp in (4, 8):
        if bpp == 4:
            px = bytearray(w * h)
            for i in range(min(w * h, len(raw) * 2)):
                b = raw[i >> 1]
                px[i] = (b >> 4) if i & 1 else (b & 15)
        else:
            px = raw[:w * h]
        n = 1 << bpp
        cols = (t["clut"]["colors"] if t["clut"] else [(i, i, i, 255) for i in range(256)])[pal * n:(pal + 1) * n]
        img = Image.frombytes("P", (w, h), bytes(px))
        img.putpalette([c for col in cols for c in col] + [0] * (4 * (256 - len(cols))), rawmode="RGBA")
        return img
    raise NotImplementedError(f"{bpp}bpp")


def tex_entries(d):
    assert d[:4] == b"TEX\0"
    n, = struct.unpack_from("<I", d, 8)
    out = []
    o = 0x14
    while len(out) < n and o + 8 <= len(d):
        off, size = struct.unpack_from("<II", d, o)
        if off and off + size <= len(d) and struct.unpack_from("<I", d, off)[0] == 0x10:
            out.append((off, size))
        o += 8
    return out


if __name__ == "__main__":
    import os
    src, dest = sys.argv[1:3]
    d = open(src, "rb").read()
    os.makedirs(dest, exist_ok=True)
    bases = [b for b, _ in tex_entries(d)] if d[:4] == b"TEX\0" else [0]
    for k, b in enumerate(bases):
        try:
            tim_image(d, b).save(os.path.join(dest, f"{os.path.basename(src)}_{k:02d}.png"))
        except Exception as e:
            print(src, k, e)
