# Repaint the game 3 / game 4 title pictures with the tester's logos: inpaint the old logo where the new one leaves it
# showing, paste the new logo, requantize to 256 colours.  python3 titlecomp.py t3 W X Y
import sys, numpy as np
from PIL import Image
from logo_mask import mask, dil
PATCH = 7
# where background texture may be copied from (keeps the characters out of the fill)
SOURCE = {'t4': [(0, 92, 240, 160), (0, 40, 30, 100)]}
NOSOURCE = {'t3': [(100, 20, 200, 84)], 't4': [(88, 70, 160, 122)]}
LOGO = {'t3': 'logos/k3.png', 't4': 'logos/k4.png'}
def load_logo(path, w):
    im = Image.open(path).convert('RGBA'); im = im.crop(im.getbbox())
    h = round(im.height * w / im.width)
    # premultiplied resize so the transparent surround doesn't bleed dark fringes
    a = np.asarray(im).astype(float); a[..., :3] *= a[..., 3:4] / 255
    r = Image.fromarray(a.astype(np.uint8)).resize((w, h), Image.LANCZOS)
    r = np.asarray(r).astype(float)
    al = r[..., 3]; rgb = np.where(al[..., None] > 0, r[..., :3] * 255 / np.maximum(al[..., None], 1), 0)
    return np.clip(rgb, 0, 255).astype(np.uint8), al > 110
def inpaint(rgb, m, iters=400):
    out = rgb.astype(float); known = ~m
    # coarse-to-fine: fill from a blurred pyramid, then relax with neighbour averages
    acc = out.copy()
    for _ in range(iters):
        s = (np.roll(acc, 1, 0) + np.roll(acc, -1, 0) + np.roll(acc, 1, 1) + np.roll(acc, -1, 1)) / 4
        acc = np.where(known[..., None], out, s)
    return acc.astype(np.uint8)
def compose(nm, W, X, Y):
    rgb, old = mask(nm)
    lrgb, lm = load_logo(LOGO[nm], W)
    h, w = lm.shape
    new = np.zeros(old.shape, bool); new[Y:Y + h, X:X + w] = lm[:160 - Y, :240 - X]
    resid = dil(old, 1) & ~new
    import patchfill
    # only the part of the old logo the new one leaves showing needs real background
    ex = dil(old, 2)
    if nm in SOURCE:
        allow = np.zeros(old.shape, bool)
        for x0, y0, x1, y1 in SOURCE[nm]: allow[y0:y1, x0:x1] = True
        for x0, y0, x1, y1 in NOSOURCE.get(nm, []): allow[y0:y1, x0:x1] = False
        ex = ex | ~allow
    if nm in SOURCE:
        fill = patchfill.fill(rgb, resid, PATCH, exclude=ex)
    else:
        # game 3: flat sky and hills, a smooth fill looks better than copied patches
        hole = dil(old, 1)
        base = rgb.copy(); base[hole] = 0
        fill = inpaint(base, hole, 600)
    out = fill.copy()
    reg = out[Y:Y + h, X:X + w]; sel = lm[:reg.shape[0], :reg.shape[1]]
    reg[sel] = lrgb[:reg.shape[0], :reg.shape[1]][sel]
    return out, resid
if __name__ == '__main__':
    nm, W, X, Y = sys.argv[1], *map(int, sys.argv[2:5])
    out, resid = compose(nm, W, X, Y)
    Image.fromarray(out).save(nm + '_new.png')
    v = out.copy(); v[resid] = [255, 0, 255]
    s = Image.new('RGB', (720, 960)); s.paste(Image.fromarray(out).resize((720, 480), Image.NEAREST), (0, 0))
    s.paste(Image.fromarray(v).resize((720, 480), Image.NEAREST), (0, 480)); s.save(nm + '_new3.png')
    print('residue px', resid.sum())
