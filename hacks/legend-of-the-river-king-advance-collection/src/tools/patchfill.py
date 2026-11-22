# Exemplar-based inpainting (Criminisi-style): fill the masked area patch by patch from the best matching
# fully known patch elsewhere in the picture.
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as win
LOC = 2.0
def fill(rgb, hole, P=9, exclude=None):
    img = rgb.astype(np.float32).copy(); hole = hole.copy(); r = P // 2
    H, W = hole.shape
    src_ok = ~hole if exclude is None else (~hole & ~exclude)
    # candidate source patches: completely known (and outside the excluded area)
    okw = win(src_ok, (P, P)).all(axis=(2, 3))
    cy, cx = np.nonzero(okw)
    while hole.any():
        known = ~hole
        # front pixels: in the hole, next to known; priority = known neighbours count
        k = known.astype(np.float32)
        kp = np.pad(k, r)
        cnt = win(kp, (P, P)).sum(axis=(2, 3))
        front = hole & (np.pad(known, 1)[1:-1, 2:] | np.pad(known, 1)[1:-1, :-2] |
                        np.pad(known, 1)[2:, 1:-1] | np.pad(known, 1)[:-2, 1:-1])
        fy, fx = np.nonzero(front)
        i = np.argmax(cnt[fy, fx]); y, x = fy[i], fx[i]
        y0, x0 = min(max(y - r, 0), H - P), min(max(x - r, 0), W - P)
        tgt = img[y0:y0 + P, x0:x0 + P]; m = known[y0:y0 + P, x0:x0 + P]
        # SSD over known pixels against every candidate
        patches = win(img, (P, P, 3))[:, :, 0]          # (H-P+1, W-P+1, P, P, 3)
        cand = patches[cy, cx]
        d = (((cand - tgt) ** 2).sum(-1) * m).sum(axis=(1, 2))
        # mild preference for nearby sources keeps the texture local
        d = d + LOC * ((cy - y0) ** 2 + (cx - x0) ** 2)
        j = np.argmin(d); sy, sx = cy[j], cx[j]
        src = img[sy:sy + P, sx:sx + P]
        upd = ~m
        tgt[upd] = src[upd]
        hole[y0:y0 + P, x0:x0 + P] = False
    return img.astype(np.uint8)
