"""Edit the pixels of an rh2 texture in place (same size, same palette, same uploads).

get(x) -> (index image [h, w], palette RGBA [n, 4] with alpha 0-255)
put(x, idx) -> rh2 bytes with the pixel uploads rewritten so the texture reads back as idx.
The uploads are replayed into a GS memory model, the new indices are written in the texture's own
format, and each pixel upload is read back in its transfer format (native or the CT32 trick)."""
import struct, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b7_gs

CB = 0x3000


def _uploads(x):
    """[(reg dict, data offset, data length)] like b7_rh2.uploads, with the offsets."""
    i = struct.unpack_from('<I', x, 0x10)[0]; out = []; reg = {}; blt = []
    while i + 16 <= len(x):
        lo, hi = struct.unpack_from('<QQ', x, i); nloop = lo & 0x7fff; flg = (lo >> 58) & 3
        if lo == 0 and hi == 0: i += 16; continue
        if flg == 2:
            reg[0x50] = blt[len(out)] if len(out) < len(blt) else blt[-1]
            out.append((dict(reg), i + 16, nloop * 16)); i += 16 + nloop * 16
        elif flg == 0 and (hi & 0xf) == 0xe:
            for k in range(nloop):
                v, r = struct.unpack_from('<QQ', x, i + 16 + 16 * k); reg[r & 0xff] = v
                if r & 0xff == 0x50: blt.append(v)
            i += 16 + 16 * nloop
        else:
            i += 16
    return out


def _load(x):
    gs = b7_gs.GS(); pb = 0; ups = []
    for k, (reg, o, n) in enumerate(_uploads(x)):
        b = reg[0x50]; dbw = (b >> 48) & 63; dpsm = (b >> 56) & 63
        rg = reg[0x52]; w, h = rg & 0xfff, (rg >> 32) & 0xfff
        assert reg.get(0x51, 0) == 0
        bp = CB if k == 0 else pb
        gs.write(dpsm, bp, dbw, 0, 0, w, h, x[o:o + n])
        if k: ups.append((dpsm, bp, dbw, w, h, o, n)); pb += -(-n // 256)
    t = struct.unpack_from('<Q', x, 0x30)[0]
    tex = (t & 0x3fff, (t >> 14) & 63, (t >> 20) & 63, (t >> 51) & 15)
    w, h = struct.unpack_from('<4H', x, 0x50)[2:]
    return gs, ups, tex, w, h


def get(x):
    gs, ups, (tbp, tbw, psm, cpsm), w, h = _load(x)
    idx = gs.read(psm, tbp, tbw, w, h).astype(np.uint8)
    c = gs.clut(cpsm, CB, 256 if psm == 0x13 else 16)
    pal = np.stack([(c >> s) & 255 for s in (0, 8, 16, 24)], -1).astype(np.int32)
    pal[:, 3] = np.minimum(pal[:, 3] * 2, 255)
    return idx, pal


def put(x, idx):
    gs, ups, (tbp, tbw, psm, cpsm), w, h = _load(x)
    idx = np.asarray(idx, np.uint8)
    if psm == 0x14:
        f = idx.ravel(); data = (f[0::2] | (f[1::2] << 4)).astype(np.uint8).tobytes()
    else:
        data = idx.tobytes()
    gs.write(psm, tbp, tbw, 0, 0, w, h, data)
    out = bytearray(x)
    for dpsm, bp, dbw, uw, uh, o, n in ups:
        v = gs.read(dpsm, bp, dbw, uw, uh)
        if dpsm == 0x14:
            f = v.ravel().astype(np.uint8); b = (f[0::2] | (f[1::2] << 4)).astype(np.uint8).tobytes()
        else:
            b = np.ascontiguousarray(v).tobytes()
        out[o:o + n] = b[:n]
    assert np.array_equal(get(bytes(out))[0], idx)
    return bytes(out)
