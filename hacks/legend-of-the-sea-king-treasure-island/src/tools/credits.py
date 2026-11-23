"""English staff roll: redraw ENDING/STAF01-15.TIM. Same line positions as the Japanese pages; roles in pink,
names in white, slanted rounded strokes like the original's italic gothic, all drawn with letters.py."""
import sys, os; sys.path.insert(0, 'tools')
from gfx import *
from letters import render, style, paste
from gfx_build import put_rgba

P, W = 'P', 'W'
PAGES = {
 1: [(P, 'Produced and Published by'), (W, 'Victor Interactive Software, Inc.'), (W, 'Pack-In-Soft Division')],
 2: [(P, 'Production'), (W, 'DDL Limited Partnership'), (P, 'Development'), (W, 'Access Co., Ltd.')],
 3: [(P, 'Production Support'), (W, 'Digimation, Inc.'), (W, 'Toru Miyazawa (Toucan Ltd.)'), (W, 'Zero Two Ltd.'), (W, 'Masahiro'), (W, 'Studio Loft Ltd.')],
 4: [(P, 'Original Concept'), (W, 'Kazuhiro Arita (Yuyu Ltd.)'), (P, 'Production Management'), (W, 'Akinori Sekine (Pack-In-Soft)'), (W, 'Miki Miyagi (Pack-In-Soft)')],
 5: [(P, 'Publicity'), (W, 'Masa Saito (Pack-In-Soft)'), (P, 'Manual'), (W, '100% Inc.')],
 6: [(P, 'Package Illustration'), (W, 'Koji Sasaki (blue island)'), (P, 'Art Director'), (W, 'Chiho Tomita')],
 7: [(P, 'Producer and Director'), (W, 'Koichiro Genda (DDL)'), (P, 'Game Design'), (W, 'Kenji Ishikawa')],
 8: [(P, 'Graphic Design'), (W, 'Junko Nakamura'), (W, 'Shigeki Hayashi'), (W, 'Chieko Setaka'), (W, 'Tomomitsu Suzuki')],
 9: [(P, 'Graphic Design'), (W, 'Takuma Sugawara'), (W, 'Tomomi Yokota'), (W, 'Yuko Ishibashi'), (W, 'Sachie Koike')],
 10: [(P, 'Programming'), (W, 'Qiming Chen'), (W, 'Norihiro Mima')],
 11: [(P, 'Sound'), (W, 'Hiroshi Iizuka'), (P, 'Character Voices'), (W, 'Sachie Koike'), (W, 'YUKI'), (W, 'C.S'), (W, 'Shiro')],
 12: [(P, 'Debugging'), (W, 'Takashi Sugawara'), (W, 'Fuyuki Tawara'), (W, 'Yasuhiro Hirano'), (W, 'Goro Ishiuchi')],
 13: [(P, 'Movies'), (W, 'Kojiro Hayashi'), (W, 'Hiroo Yoshioka'), (W, 'Atsuko Imai'), (W, 'Emi Kawaguchi')],
 14: [(P, 'Movies'), (W, 'Aya Kawasaki'), (W, 'Hisae Suzuki'), (W, 'Mitsuhiro Karato'), (W, 'Masahiro')],
}
COL = {P: (248, 192, 192), W: (240, 240, 240)}

def lines(a):
    al = a[..., 3] > 0; rows = al.any(1); out = []; s = None
    for y in range(a.shape[0] + 1):
        v = rows[y] if y < a.shape[0] else False
        if v and s is None: s = y
        if not v and s is not None: out.append((s, y - 1)); s = None
    return out

def line_art(text, col, maxw=236):
    for cap in (10, 9.5, 9, 8.5, 8):
        m, base = render(text, cap, weight=0.2, spacing=1.15, tilt=0, bounce=0, seed=1, slant=0.24, swell=0.04, space=3.6, scale_var=0)
        xs = np.nonzero(m.max(0) > 0.05)[0]
        if xs.max() - xs.min() <= maxw: break
    art = np.zeros(m.shape + (4,)); art[..., :3] = col; art[..., 3] = np.clip(m * 1.15, 0, 1)
    return art, base, cap, (xs.min() + xs.max()) / 2

def page(i):
    src = 'files/ENDING/STAF%02d.TIM' % i
    T = Tim(src); a = np.array(Image.open('view/tim/STAF%02d_0.png' % i))
    rgba = np.zeros(a.shape, np.uint8)
    if i == 15:
        m, base = render('The End', 22, weight=0.34, spacing=0.9, tilt=4, bounce=0.04, seed=3, slant=0.12, swell=0.2, space=4)
        art = style(m, (248, 248, 248), (248, 232, 232), (248, 0, 0), shine_a=0.0, dark=0.0, outline_w=2.2,
                    shadow=(112, 0, 0), shadow_off=(1, 1))[0]
        ys = np.nonzero(art[..., 3].max(1) > 0.05)[0]; xs = np.nonzero(art[..., 3].max(0) > 0.05)[0]
        art = art[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        paste(rgba, art, 130, 103)
    else:
        L = lines(a); assert len(L) == len(PAGES[i]), (i, len(L))
        for (y0, y1), (c, text) in zip(L, PAGES[i]):
            art, base, cap, cx = line_art(text, COL[c])
            top = int(round((y0 + y1) / 2 - (base - cap / 2)))   # centre the cap height on the Japanese line
            left = int(round(128 - cx))
            h, w = art.shape[:2]
            sub = np.zeros((h, 256, 4)); 
            X0, X1 = max(0, left), min(256, left + w)
            sub[:, X0:X1] = art[:, X0 - left:X1 - left]
            for yy in range(h):
                Y = top + yy
                if 0 <= Y < 240:
                    al = sub[yy, :, 3:4]
                    rgba[Y, :, :3] = np.clip(rgba[Y, :, :3] * (1 - al) + sub[yy, :, :3] * al, 0, 255)
                    rgba[Y, :, 3] = np.maximum(rgba[Y, :, 3], (al[:, 0] * 255).astype(np.uint8))
    # anti-aliased edges stay opaque dark shades, as on the original pages
    op = rgba[..., 3] > 40
    out = rgba.copy(); out[..., :3] = (rgba[..., :3].astype(float) * np.where(op, 1, 0)[..., None]).astype(np.uint8)
    out[..., 3] = np.where(op, 255, 0)
    put_rgba(T, out, (0, 0, 256, 240))
    p = 'gfx_out/ENDING/STAF%02d.TIM' % i; os.makedirs('gfx_out/ENDING', exist_ok=True); T.save(p)
    return T

def all_pages():
    S = Image.new('RGB', (1024, 960))
    for i in range(1, 16):
        T = page(i)
        S.paste(Image.fromarray(T.rgb()), (((i - 1) % 4) * 256, ((i - 1) // 4) * 240))
    S.save('view/credits_en.png'); return T

if __name__ == '__main__': all_pages()
