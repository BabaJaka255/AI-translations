"""Title logo from the tester's mock-up (art/logo_mockup.png): "Legend of The River King CD".

The mock-up is resampled to 200 px wide (block mode of 9-bit colours), mapped to 13 colours and cut into
16x16 sprites placed freely (row bands, greedy left-to-right). The 44 SAT entries of the original logo are
reused; their x/y come from `lda #imm / sta $28xx` pairs in the sector-34 overlay, so the immediates are patched.
Palette: title sprite palette 0 at data.iso 0x14DE80. Entries 1 (blinks), 3 and 15 are shared with the
cursor/menu/copyright: 15 (white) is used as is, 1 and 3 are left alone.
"""
import os, collections
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCKUP = os.path.join(ROOT, 'art', 'logo_mockup.png')
ENTRIES = [1, 16, 32, 33, 48, 2, 3, 18, 19, 34, 35, 50, 51, 4, 5, 20, 21, 36, 37, 52, 53, 6, 7, 22, 23, 38, 39,
           55, 8, 9, 24, 25, 40, 41, 56, 57, 10, 11, 26, 27, 42, 43, 58, 59]
WIDTH = 200
SCREEN_X, SCREEN_Y = 28, 6          # top-left of the logo on screen
BG = np.array([72, 159, 239])
# palette index -> (r, g, b) in 0-7
PAL = {2: (0, 0, 1), 4: (7, 6, 0), 5: (7, 5, 0), 6: (7, 4, 0), 7: (7, 3, 0), 8: (7, 2, 0), 9: (7, 1, 0),
       10: (7, 0, 0), 11: (0, 5, 4), 12: (0, 4, 4), 13: (0, 6, 5), 14: (5, 0, 0), 15: (7, 7, 7)}
SPRITE_BASE = 0x45000       # data.iso: SAT entry i pattern at +i*128
PALETTE = 0x14DE80
OVERLAY = 34                # sector of the overlay that sets the SAT buffer ($2800) at $8000

def grb(c): r, g, b = c; return g << 6 | r << 3 | b

def image():
    A = np.array(Image.open(MOCKUP).convert('RGB')).astype(int)
    fg = np.abs(A - BG).sum(2) > 90
    ys, xs = np.nonzero(fg); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    W = WIDTH; H = round((y1 - y0) * W / (x1 - x0)); sx = (x1 - x0) / W; sy = (y1 - y0) / H
    q = np.round(A / 36).clip(0, 7).astype(int)
    keys = np.array(list(PAL)); cols = np.array([PAL[k] for k in keys])
    out = np.zeros((H, W), np.uint8)
    for y in range(H):
        for x in range(W):
            a0 = int(y0 + (y + .2) * sy); a1 = int(y0 + (y + .8) * sy) + 1
            b0 = int(x0 + (x + .2) * sx); b1 = int(x0 + (x + .8) * sx) + 1
            blk = [tuple(q[i, j]) if fg[i, j] else None for i in range(a0, a1) for j in range(b0, b1)]
            c = collections.Counter(blk).most_common(1)[0][0]
            if c is None: continue
            d = ((cols - np.array(c)) ** 2).sum(1)
            d[keys == 2] -= 2 if sum(c) <= 2 else 0           # black and navy both become the dark outline
            out[y, x] = keys[d.argmin()]
    return out

def cover(img):
    H, W = img.shape; best = None
    for oy in range(16):
        P = np.zeros((H + 16, W), np.uint8); P[oy:oy + H] = img
        sp = []
        for r in range(0, H + 16, 16):
            cols = P[r:r + 16].any(0); x = 0
            while x < W:
                if cols[x]: sp.append((x, r - oy)); x += 16
                else: x += 1
        if best is None or len(sp) < len(best): best = sp
    return best

def pattern(img, x, y):
    H, W = img.shape; b = bytearray(128)
    for p in range(4):
        for yy in range(16):
            w = 0
            for xx in range(16):
                Y, X = y + yy, x + xx
                if 0 <= Y < H and 0 <= X < W and (int(img[Y, X]) >> p) & 1: w |= 0x8000 >> xx
            b[p * 32 + yy * 2] = w & 255; b[p * 32 + yy * 2 + 1] = w >> 8
    return bytes(b)

def patch(t):
    img = image(); sp = cover(img)
    assert len(sp) <= len(ENTRIES), len(sp)
    chunk = b''.join(t.read(OVERLAY + i) for i in range(4))
    def imm(addr):                          # offset of the immediate in "lda #imm / sta addr"
        k = chunk.find(bytes([0x8D, addr & 255, addr >> 8]))
        assert k > 0 and chunk[k - 2] == 0xA9 and chunk.find(bytes([0x8D, addr & 255, addr >> 8]), k + 1) < 0, hex(addr)
        return k - 1
    for n, e in enumerate(ENTRIES):
        if n < len(sp):
            x, y = sp[n]; sx, sy = SCREEN_X + x + 32, SCREEN_Y + y + 64
            data = pattern(img, x, y)
        else:
            sx, sy, data = 0, 0, bytes(128)  # unused: off screen, blank
        for off, v in ((0, sy), (2, sx)):
            assert v < 256
            o = imm(0x2800 + e * 8 + off); t.write(OVERLAY, o, bytes([v]))
        sec, o = divmod(SPRITE_BASE + e * 128, 2048); t.write(sec, o, data)
    sec, o = divmod(PALETTE, 2048); pal = bytearray(t.read(sec, o, 32))
    for i, c in PAL.items():
        if i == 15: continue
        v = grb(c); pal[i * 2] = v & 255; pal[i * 2 + 1] = v >> 8
    t.write(sec, o, bytes(pal))
    return len(sp)

if __name__ == '__main__':
    import sys
    img = image(); print(img.shape, 'sprites', len(cover(img)))
    rgb = np.zeros(img.shape + (3,), np.uint8) + np.array([72, 159, 239], np.uint8)
    for k, c in PAL.items(): rgb[img == k] = np.array(c) * 36
    Image.fromarray(rgb).resize((img.shape[1] * 4, img.shape[0] * 4), Image.NEAREST).save(sys.argv[1])
