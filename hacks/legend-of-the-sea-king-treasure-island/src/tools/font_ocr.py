"""OCR the 1280 16x16 glyphs of COMM.TIM pages 1-5 against IPAGothic, all SJIS chars."""
import numpy as np, json
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
def norm(a):
    a = ndimage.gaussian_filter(a.astype(float), 0.8)
    ys, xs = np.nonzero(a > 0.15)
    if len(ys) == 0: return None
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    a = ndimage.shift(a, (7.5 - cy, 7.5 - cx), order=1)
    a = a - a.mean(); n = np.linalg.norm(a)
    return (a / n).ravel() if n else None
def sjis_chars():
    out = []
    for hi in list(range(0x88, 0xa0)) + list(range(0xe0, 0xeb)):
        for lo in range(0x40, 0xfd):
            try: ch = bytes([hi, lo]).decode('cp932')
            except Exception: continue
            if len(ch) == 1: out.append((hi << 8 | lo, ch))
    return out
g = np.load('view/glyphs.npy')
gv = [norm((x >= 5).astype(float)) for x in g]
cands = sjis_chars()
fonts = [ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', s) for s in (14, 15, 16)]
C = []
for code, ch in cands:
    vs = []
    for f in fonts:
        im = Image.new('L', (16, 16)); ImageDraw.Draw(im).text((8, 8), ch, font=f, fill=255, anchor='mm')
        vs.append(norm(np.array(im) / 255.0))
    C.append(vs)
C = np.array([[v if v is not None else np.zeros(256) for v in vs] for vs in C])  # n,3,256
S = np.zeros((len(g), len(cands)))
for i, v in enumerate(gv):
    if v is None: continue
    S[i] = (C @ v).max(1)
np.save('view/ocr_scores.npy', S.astype(np.float32))
json.dump([c for c in cands], open('view/ocr_cands.json', 'w'), ensure_ascii=False)
best = S.argmax(1)
for row in range(len(g) // 16):
    print(f'{row*16:4d} ' + ''.join(cands[b][1] if gv[row*16+k] is not None else '□' for k, b in enumerate(best[row*16:row*16+16])))
