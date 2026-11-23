"""PS1 TIM image reader/writer helpers."""
import struct
import numpy as np
from PIL import Image

def parse(d, off=0):
    magic, flags = struct.unpack_from('<II', d, off)
    assert magic == 0x10, hex(magic)
    bpp = flags & 3
    p = off + 8
    clut = None
    if flags & 8:
        ln, cx, cy, cw, ch = struct.unpack_from('<IHHHH', d, p)
        clut = dict(x=cx, y=cy, w=cw, h=ch, off=p + 12,
                    data=np.frombuffer(d, '<u2', cw * ch, p + 12).reshape(ch, cw))
        p += ln
    ln, ix, iy, iw, ih = struct.unpack_from('<IHHHH', d, p)
    img = dict(x=ix, y=iy, w=iw, h=ih, off=p + 12,
               data=np.frombuffer(d, '<u2', iw * ih, p + 12).reshape(ih, iw))
    return dict(bpp=bpp, clut=clut, img=img, end=p + ln)

def c15(v):
    r = (v & 31) << 3; g = ((v >> 5) & 31) << 3; b = ((v >> 10) & 31) << 3
    a = 0 if v == 0 else 255
    return r, g, b, a

def indices(t):
    w = t['img']['data']
    if t['bpp'] == 0:
        b = w.astype(np.uint32)
        return np.stack([(b >> s) & 15 for s in (0, 4, 8, 12)], -1).reshape(w.shape[0], -1)
    if t['bpp'] == 1:
        b = w.astype(np.uint32)
        return np.stack([b & 255, b >> 8], -1).reshape(w.shape[0], -1)
    return None

def to_image(t, pal=0):
    if t['bpp'] == 2:
        w = t['img']['data']
        arr = np.array([[c15(v) for v in row] for row in w], np.uint8)
        return Image.fromarray(arr, 'RGBA')
    idx = indices(t)
    cl = t['clut']['data'][pal]
    lut = np.array([c15(v) for v in cl], np.uint8)
    return Image.fromarray(lut[idx], 'RGBA')
