"""Fishing Note header: TIM/NOTE.TIM (256x240 8bpp). The katakana 釣りノート title is painted out
and "Fishing Note" drawn in the same navy-to-blue with a white offset shadow."""
import sys, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, 'tools')
import tim
from title import rgb_of, diffuse

FONT = '/usr/share/fonts/truetype/noto/NotoSans-Black.ttf'
BOX = (40, 12, 236, 58)

def compose(t):
    idx, rgb = rgb_of(t)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    text = ((b > g + 12) & (b > r + 12)) | (rgb.min(-1) > 200)
    m = np.zeros(rgb.shape[:2], bool)
    x0, y0, x1, y1 = BOX
    m[y0:y1, x0:x1] = text[y0:y1, x0:x1]
    m = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    m[y1:] = False
    img = diffuse(rgb, m)
    img[m] += np.random.default_rng(2).normal(0, 5, img[m].shape)
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    f = ImageFont.truetype(FONT, 30)
    txt = 'Fishing Note'
    w = int(f.getlength(txt)); x = (256 - w) // 2; y = 8
    a = Image.new('L', (256, 70)); ImageDraw.Draw(a).text((x, y), txt, font=f, fill=255)
    a = np.array(a) > 120
    lay = np.zeros((70, 256, 4), np.uint8)
    sh = np.zeros_like(a); sh[2:, 2:] = a[:-2, :-2]
    lay[sh & ~a] = (235, 240, 250, 255)
    ys = np.linspace(0, 1, 70)[:, None, None]
    grad = np.array([0, 20, 90]) * (1 - ys) + np.array([30, 90, 210]) * ys
    grad = np.broadcast_to(grad, (70, 256, 3))
    lay[a, :3] = grad[a]; lay[a, 3] = 255
    base.alpha_composite(Image.fromarray(lay), (0, 0))
    return idx, np.array(base.convert('RGB'))

def build(src):
    d = bytearray(src)
    t = tim.parse(bytes(d), 0)
    old, img = compose(t)
    keep0 = old == 0
    q = Image.fromarray(img.astype(np.uint8), 'RGB').quantize(255, method=Image.MEDIANCUT, dither=Image.NONE)
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
    out = build(open('files/TIM/NOTE.TIM', 'rb').read())
    tim.to_image(tim.parse(out, 0)).resize((768, 720), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else 'shots/note_en.png')
