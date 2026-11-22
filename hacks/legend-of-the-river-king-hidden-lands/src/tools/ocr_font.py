"""Guess each 16x16 game glyph's character by matching against IPAGothic renders."""
import sys, json, numpy as np
sys.path.insert(0, 'tools')
import tim
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

def game_glyphs():
    d = open('files/TIM/COMM.TIM', 'rb').read()
    lum = np.array([((v & 31) + ((v >> 5) & 31) + ((v >> 10) & 31)) / 93 for v in range(1)])
    out = []
    for page in range(1, 6):
        t = tim.parse(d, 33312 * page)
        cl = t['clut']['data'][0].astype(np.int64)
        lut = ((cl & 31) + ((cl >> 5) & 31) + ((cl >> 10) & 31)) / 93.0
        img = lut[tim.indices(t)]
        for r in range(16):
            for c in range(16):
                out.append(img[r*16:r*16+16, c*16:c*16+16])
    return out

def norm(a):
    a = ndimage.gaussian_filter(a.astype(float), 0.8)
    # centre by bounding box of ink
    ys, xs = np.nonzero(a > 0.15)
    if len(ys) == 0: return None
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    a = ndimage.shift(a, (7.5 - cy, 7.5 - cx), order=1)
    a = a - a.mean(); n = np.linalg.norm(a)
    return (a / n).ravel() if n else None

def candidates():
    chars = []
    for hi in range(0x81, 0xa0):
        for lo in range(0x40, 0xfd):
            try: ch = bytes([hi, lo]).decode('cp932')
            except: continue
            if len(ch) == 1: chars.append(ch)
    for hi in range(0xe0, 0xeb):
        for lo in range(0x40, 0xfd):
            try: ch = bytes([hi, lo]).decode('cp932')
            except: continue
            if len(ch) == 1: chars.append(ch)
    return chars

def render(ch, font):
    im = Image.new('L', (16, 16)); d = ImageDraw.Draw(im)
    d.text((8, 8), ch, font=font, fill=255, anchor='mm')
    return np.array(im) / 255.0

if __name__ == '__main__':
    gl = game_glyphs()
    # foreground only: shadow is darker; keep bright pixels
    gv = [norm(np.where(g > 0.55, g, 0)) for g in gl]
    font = ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', 15)
    chars = candidates()
    cv = []; keep = []
    for ch in chars:
        v = norm(render(ch, font))
        if v is not None: cv.append(v); keep.append(ch)
    C = np.array(cv)
    res = []
    for i, v in enumerate(gv):
        if v is None: res.append(['', 0, '', 0]); continue
        s = C @ v; o = np.argsort(-s)[:3]
        res.append([keep[o[0]], float(s[o[0]]), keep[o[1]] + keep[o[2]], float(s[o[1]])])
    json.dump(res, open('ocr.json', 'w'), ensure_ascii=False)
    for row in range(len(res) // 16):
        print(f'{row*16:4d} ' + ''.join(r[0] or '□' for r in res[row*16:row*16+16]) + '   ' +
              ' '.join(f'{r[1]:.2f}' for r in res[row*16:row*16+16]))
