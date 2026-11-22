"""English title screen: TIM/TITLE.TIM (256x256 8bpp, CLUT at 0,500).
The Japanese logo and the katakana copyright line are painted out (diffusion fill from the
surrounding forest), then the "Legend of the River King" logo from the earlier hacks and a new
subtitle are laid on top. The image is re-quantised to 255 colours (index 0 stays transparent)."""
import os, sys, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, 'tools')
import tim

ART = 'art/title_art.png'
LOGO_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'art', 'logos', 'collection.png')
LOGO_CROP = (0, 0, 1971, 640)          # "Legend of / The River King" (+ the g's descender)
SUBTITLE = '~ In Search of the Secret Land ~'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
LOGO_BOX = (22, 12, 230, 138)           # old logo area to paint out
COPY_BOX = (24, 202, 232, 222)          # old copyright line

def rgb_of(t):
    idx = tim.indices(t)
    lut = np.array([tim.c15(v) for v in t['clut']['data'][0]], np.uint8)
    return idx, lut[idx][..., :3].astype(float)

def diffuse(img, mask, iters=600):
    img = img.copy()
    m = mask.astype(bool)
    img[m] = img[~m].mean(0)
    for _ in range(iters):
        p = np.pad(img, ((1, 1), (1, 1), (0, 0)), mode='edge')
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4
        img[m] = avg[m]
    return img

def logo_mask(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    forest = (g >= r - 4) & (g >= b - 4) & (rgb.max(-1) < 200)
    m = np.zeros(rgb.shape[:2], bool)
    x0, y0, x1, y1 = LOGO_BOX
    m[y0:y1, x0:x1] = ~forest[y0:y1, x0:x1]
    x0, y0, x1, y1 = COPY_BOX
    bright = rgb.max(-1) > 110
    m[y0:y1, x0:x1] |= bright[y0:y1, x0:x1]
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    return np.array(im) > 0

def outlined_text(size, text, font, fill_top, fill_bot, outline=(24, 16, 8), ow=1):
    f = ImageFont.truetype(font, size)
    w = int(f.getlength(text)) + 6; h = size + 8
    a = Image.new('L', (w, h)); ImageDraw.Draw(a).text((3, 2), text, font=f, fill=255)
    a = np.array(a) > 110
    out = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * ow + 1))
    out = np.array(out) > 0
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[out] = (*outline, 255)
    ys = np.linspace(0, 1, h)[:, None]
    grad = (np.array(fill_top)[None, None] * (1 - ys[..., None]) + np.array(fill_bot)[None, None] * ys[..., None])
    grad = np.broadcast_to(grad, (h, w, 3))
    rgba[a, :3] = grad[a]; rgba[a, 3] = 255
    return Image.fromarray(rgba, 'RGBA')

def compose(t):
    idx, rgb = rgb_of(t)
    top = rgb[:240]
    m = logo_mask(top)
    top = diffuse(top, m)
    # light grain so the filled area doesn't look flat
    rng = np.random.default_rng(1)
    top[m] += rng.normal(0, 6, top[m].shape)
    base = Image.fromarray(np.clip(top, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    logo = Image.open(LOGO_SRC).convert('RGBA').crop(LOGO_CROP)
    la = np.array(logo)
    la[560:, :1690, 3] = 0             # "Advance Collection" (only the g of King hangs lower)
    ys = np.nonzero(la[..., 3].max(1))[0]
    logo = Image.fromarray(la).crop((0, 0, la.shape[1], ys.max() + 1))
    lw = 236; lh = round(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    a = np.array(logo); a[..., 3] = np.where(a[..., 3] > 110, 255, 0); logo = Image.fromarray(a)
    base.alpha_composite(logo, ((256 - lw) // 2, 14))
    sub = outlined_text(12, SUBTITLE, BOLD, (255, 250, 150), (150, 220, 60), ow=1)
    base.alpha_composite(sub, ((256 - sub.width) // 2, 14 + lh + 2))
    cp = outlined_text(9, '©1998 Victor Interactive Software', BOLD, (235, 235, 235), (205, 205, 205), outline=(30, 30, 30))
    base.alpha_composite(cp, ((256 - cp.width) // 2, 204))
    return idx, np.array(base.convert('RGB'))

def build(src):
    d = bytearray(src)
    t = tim.parse(bytes(d), 0)
    import os
    if os.path.exists(ART):           # the tester's finished title art (256x240) replaces the generated one
        top = np.array(Image.open(ART).convert('RGB'))[:240, :256]
    else:
        idx, top = compose(t)
    old = tim.indices(t)
    lut = np.array([tim.c15(v) for v in t['clut']['data'][0]], np.uint8)[..., :3]
    full = lut[old].copy()
    full[:240] = top
    keep0 = old == 0
    q = Image.fromarray(full.astype(np.uint8), 'RGB').quantize(255, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = np.array(q.getpalette()[:255 * 3]).reshape(-1, 3)
    qi = np.array(q).astype(int) + 1
    qi[keep0] = 0
    cl = [0] + [max(1, (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)) for r, g, b in pal]
    cl += [0x7fff] * (256 - len(cl))
    struct.pack_into('<256H', d, t['clut']['off'], *cl)
    words = (qi[:, 0::2] | (qi[:, 1::2] << 8)).astype('<u2')
    o = t['img']['off']
    d[o:o + words.nbytes] = words.tobytes()
    return bytes(d)

if __name__ == '__main__':
    out = build(open('files/TIM/TITLE.TIM', 'rb').read())
    t = tim.parse(out, 0)
    tim.to_image(t).resize((768, 768), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else 'shots/title_en.png')
