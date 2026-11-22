"""rh2 texture -> PNG (for checking images; PSMT8/PSMT4 uploaded in their own format).
Header: +0x30 TEX0, +0x50 u16 psm, +0x54 u16 w, h. The body is GIF packets (A+D with BITBLTBUF/
TRXREG, then IMAGE); the first upload is the CLUT (CT32), the last the pixels."""
import struct, sys
import numpy as np, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def uploads(x):
    i = struct.unpack_from('<I', x, 0x10)[0]; out = []; reg = {}; blt = []
    while i + 16 <= len(x):
        lo, hi = struct.unpack_from('<QQ', x, i); nloop = lo & 0x7fff; flg = (lo >> 58) & 3
        if lo == 0 and hi == 0: i += 16; continue
        if flg == 2:
            reg[0x50] = blt[len(out)] if len(out) < len(blt) else blt[-1]
            out.append((dict(reg), x[i + 16:i + 16 + nloop * 16])); i += 16 + nloop * 16
        elif flg == 0 and (hi & 0xf) == 0xe:
            for k in range(nloop):
                v, r = struct.unpack_from('<QQ', x, i + 16 + 16 * k); reg[r & 0xff] = v
                if r & 0xff == 0x50: blt.append(v)
            i += 16 + 16 * nloop
        else:
            i += 16
    return out


def decode(x):
    """-> RGBA image of the texture as the header's TEX0 describes it, (psm, w, h)."""
    import b7_gs
    gs = b7_gs.GS()
    CB = 0x3000   # the game puts the CLUT (first upload) in its own slot; pixel chunks follow page by page
    pb = 0
    for k, (reg, data) in enumerate(uploads(x)):
        b = reg[0x50]; dbw = (b >> 48) & 63; dpsm = (b >> 56) & 63
        pos = reg.get(0x51, 0); rg = reg[0x52]; w, h = rg & 0xfff, (rg >> 32) & 0xfff
        gs.write(dpsm, CB if k == 0 else pb, dbw, (pos >> 32) & 0x7ff, (pos >> 48) & 0x7ff, w, h, data)
        if k: pb += -(-len(data) // 256)
    t = struct.unpack_from('<Q', x, 0x30)[0]
    tbp, tbw, psm = t & 0x3fff, (t >> 14) & 63, (t >> 20) & 63
    cbp, cpsm = (t >> 37) & 0x3fff, (t >> 51) & 15
    _, _, w, h = struct.unpack_from('<4H', x, 0x50)
    idx = gs.read(psm, tbp, tbw, w, h)
    c = gs.clut(cpsm, CB, 256 if psm == 0x13 else 16)
    rgba = c[idx]
    img = np.stack([(rgba >> s) & 255 for s in (0, 8, 16, 24)], -1).astype(np.uint16)
    img[..., 3] = np.minimum(img[..., 3] * 2, 255)
    return img.astype(np.uint8), (psm, w, h)


def to_png(x, path, scale=1):
    from PIL import Image
    img, _ = decode(x)
    im = Image.fromarray(img, 'RGBA')
    bg = Image.new('RGBA', im.size, (60, 60, 90, 255)); bg.alpha_composite(im)
    if scale != 1: bg = bg.resize((im.width * scale, im.height * scale), Image.NEAREST)
    bg.convert('RGB').save(path)


if __name__ == '__main__':
    to_png(open(sys.argv[1], 'rb').read(), sys.argv[2])
