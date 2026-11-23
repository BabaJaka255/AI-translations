"""Edit 8bpp/4bpp TIM images: decode to RGB, inpaint text, draw English, quantize back to the CLUT."""
import sys, struct
sys.path.insert(0, 'tools')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import tim
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SERIFB = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'

class Tim:
    def __init__(self, path, k=0):
        self.path = path; self.d = bytearray(open(path, 'rb').read())
        off = 0
        for _ in range(k): off = tim.parse(bytes(self.d), off)['end']
        self.t = tim.parse(bytes(self.d), off)
        cl = self.t['clut']['data'][0]
        self.raw = cl.copy()
        self.pal = np.array([tim.c15(int(v))[:3] for v in cl], int)
        self.idx = tim.indices(self.t).astype(int)
    def rgb(self): return self.pal[self.idx].astype(np.uint8)
    def put(self, rgb, region=None, keep=None):
        """quantize rgb (HxWx3) back into indices inside region=(x0,y0,x1,y1); keep: bool mask of pixels left alone"""
        x0, y0, x1, y1 = region or (0, 0, self.idx.shape[1], self.idx.shape[0])
        usable = np.nonzero(self.raw != 0)[0]
        P = self.pal[usable]
        sub = rgb[y0:y1, x0:x1].reshape(-1, 3).astype(int)
        dist = ((sub[:, None, :] - P[None, :, :]) ** 2).sum(-1)
        new = usable[dist.argmin(1)].reshape(y1 - y0, x1 - x0)
        if keep is not None: new = np.where(keep[y0:y1, x0:x1], self.idx[y0:y1, x0:x1], new)
        self.idx[y0:y1, x0:x1] = new
    def save(self, out):
        img = self.t['img']; h, w = img['h'], img['w']
        if self.t['bpp'] == 1:
            words = (self.idx[:, 0::2] | (self.idx[:, 1::2] << 8)).astype('<u2')
        else:
            i = self.idx
            words = (i[:, 0::4] | (i[:, 1::4] << 4) | (i[:, 2::4] << 8) | (i[:, 3::4] << 12)).astype('<u2')
        self.d[img['off']:img['off'] + 2 * w * h] = words.tobytes()
        open(out, 'wb').write(self.d)

def inpaint(rgb, mask, r=3):
    return cv2.inpaint(rgb, mask.astype(np.uint8) * 255, r, cv2.INPAINT_TELEA)

def text_layer(size, text, font, pos, fill, shadow=None, shadow_off=(1, 1), outline=None, grad=None, anchor='la', stroke=0):
    """RGBA layer with text; grad=(top_rgb, bottom_rgb) for a vertical gradient fill"""
    W, H = size
    lay = Image.new('RGBA', size, (0, 0, 0, 0))
    def draw_mask(off, sw=0):
        m = Image.new('L', size, 0); ImageDraw.Draw(m).text((pos[0] + off[0], pos[1] + off[1]), text, font=font, fill=255, anchor=anchor, stroke_width=sw, stroke_fill=255)
        return m
    if shadow is not None:
        sm = draw_mask(shadow_off, stroke)
        lay.paste(Image.new('RGBA', size, shadow + (255,)), (0, 0), sm)
    if outline is not None:
        om = draw_mask((0, 0), stroke or 1)
        lay.paste(Image.new('RGBA', size, outline + (255,)), (0, 0), om)
    m = draw_mask((0, 0))
    if grad:
        bb = m.getbbox() or (0, 0, W, H)
        g = np.zeros((H, W, 4), np.uint8)
        for y in range(H):
            t = min(1, max(0, (y - bb[1]) / max(1, bb[3] - bb[1] - 1)))
            g[y, :, :3] = [int(a + (b - a) * t) for a, b in zip(*grad)]
        g[..., 3] = 255
        lay.paste(Image.fromarray(g, 'RGBA'), (0, 0), m)
    else:
        lay.paste(Image.new('RGBA', size, fill + (255,)), (0, 0), m)
    return lay

def compose(rgb, lay):
    base = Image.fromarray(rgb).convert('RGBA')
    base.alpha_composite(lay)
    return np.array(base.convert('RGB'))
