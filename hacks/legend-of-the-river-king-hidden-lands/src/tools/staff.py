"""English staff roll: redraws ENDING/STAF01-14.TIM (8bpp, 256x240).
Each original line (found as a band of non-transparent rows) is replaced by the English line in
the same place: role titles in the pink ramp (palette 33-47), names in the white ramp (1-15),
both italic with a dark lower-right edge like the originals. STAF14 is the closing "The End"."""
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tim

FONT_I = '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'
FONT_B = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'

# T = role title, N = name line; one entry per line of the original card, top to bottom
CREDITS = {
    1: [('T', 'Produced by'), ('N', 'Victor Interactive Software'), ('N', 'Pack-In-Soft Division')],
    2: [('T', 'Developed by'), ('N', 'Access Co., Ltd.'), ('T', 'Development Support'), ('N', 'Zero Two Ltd.')],
    3: [('T', 'Executive Producer'), ('N', 'Seiichi Kizu'), ('T', 'Planning Producer'), ('N', 'Toru Miyazawa')],
    4: [('T', 'Original Concept'), ('N', 'Kazuhiro Arita'), ('T', 'Art Director'), ('N', 'Chiho Tomita'),
        ('T', 'Package Illustration'), ('N', 'Toshikuni Okubo')],
    5: [('T', 'Production Managers'), ('N', 'Akinori Sekine'), ('N', 'Miki Miyagi'),
        ('T', 'Coordination, Concept & Direction'), ('N', 'Koichiro Genda')],
    6: [('T', 'Publicity'), ('N', 'Masa Saito'), ('T', 'Instruction Manual'), ('N', '100% Co., Ltd.')],
    7: [('T', 'Game Design'), ('N', 'Kenji Ishikawa'), ('T', 'Character Design'), ('N', 'Yumiko Sawada'),
        ('N', 'Atsushi Kume')],
    8: [('T', 'Programming'), ('N', 'Kimei Chin'), ('N', 'Noritaka Mima'), ('T', 'Sound'), ('N', 'Hiroaki Shibata'),
        ('N', 'Hiroshi Iizuka')],
    9: [('T', 'Graphic Design'), ('N', 'Junko Nakamura'), ('N', 'Shigeki Hayashi'), ('N', 'Chieko Setaka'),
        ('N', 'Yukie Koike'), ('N', 'Ryoko Kiyomi'), ('C', ('Chef', 'Tomomitsu Suzuki')), ('N', 'Nazoman & D-Drill')],
    10: [('T', 'Opening Movie'), ('N', 'Kojiro Hayashi'), ('N', 'Hiroo Yoshioka'), ('N', 'Masahiro'),
         ('N', 'Shunsuke Wada'), ('N', 'Koji Yasuda'), ('N', 'Studio Loft')],
    11: [('T', 'Debugging'), ('N', 'Takashi Sugawara'), ('N', 'Masaomi Konuma'), ('N', 'Fuyuki Tawara'),
         ('N', 'Yasuhiro Hirano'), ('N', 'Goro Ishiuchi'), ('N', 'Tomoharu Iwashima')],
    12: [('T', 'Debugging'), ('N', 'Ryo Kajikawa'), ('N', 'Masahide Takada'), ('N', 'Yoshiyuki Tsuchida'),
         ('N', 'Mashito Yamaoka'), ('N', 'Koichi Urano')],
    13: [('T', 'Special Thanks'), ('N', 'Yoshiharu Takaoka'), ('N', 'Nobuaki Kimura'), ('N', 'Nobuyuki Saito'),
         ('N', 'Ryutaro Ono'), ('N', 'Affect Co., Ltd.'), ('N', 'Kawase Ko'), ('N', 'Mugen Design Studio Inc.')],
}

def bands(idx, cl, bg):
    content = (idx != bg) & (cl[idx] != 0)
    rows = content.any(1); out = []; y = 0
    while y < 240:
        if rows[y]:
            y0 = y
            while y < 240 and rows[y]: y += 1
            out.append((y0, y - 1))
        y += 1
    return out

def mask(text, size, font=FONT_I, scale=4):
    """Text as a bool mask: tight left/right, rows from the cap top to the descender bottom so
    every line at one size shares a baseline."""
    f = ImageFont.truetype(font, size * scale)
    asc, desc = f.getmetrics()
    W = int(f.getlength(text)) + 16 * scale
    im = Image.new('L', (W, asc + desc + 8 * scale), 0)
    ImageDraw.Draw(im).text((4 * scale, 4 * scale), text, font=f, fill=255)
    im = im.resize((im.width // scale, im.height // scale), Image.LANCZOS)
    a = np.array(im) > 110
    ref = Image.new('L', (40 * scale, asc + desc + 8 * scale), 0)
    ImageDraw.Draw(ref).text((4 * scale, 4 * scale), 'Hg', font=f, fill=255)
    r = np.array(ref.resize((ref.width // scale, ref.height // scale), Image.LANCZOS)) > 110
    ry = np.where(r.any(1))[0]
    xs = np.where(a.any(0))[0]
    return a[ry.min():ry.max() + 1, xs.min():xs.max() + 1]

def fit(text, size, maxw=240, font=FONT_I):
    while True:
        m = mask(text, size, font)
        if m.shape[1] <= maxw or size <= 8: return m
        size -= 1

def stamp(idx, m, x0, y0, ramp, edge):
    h, w = m.shape
    # dark edge one pixel down/right, then the face with a top-to-bottom ramp
    for dy, dx in ((1, 1), (0, 1), (1, 0)):
        ys, xs = np.where(m)
        idx[ys + y0 + dy, xs + x0 + dx] = edge
    for y in range(h):
        c = ramp[min(len(ramp) - 1, y * len(ramp) // h)]
        xs = np.where(m[y])[0]
        idx[y0 + y, x0 + xs] = c

TITLE = [47, 47, 46, 45, 44, 43, 42, 41]
NAME = [15, 15, 15, 14, 13, 12, 11, 10]

def card(d, k):
    t = tim.parse(d)
    idx = tim.indices(t).astype(np.uint8).copy()
    cl = np.array(t['clut']['data'][0], np.int64)
    bg = int(np.bincount(idx.ravel()).argmax())
    bs = bands(idx, cl, bg)
    lines = CREDITS[k]
    assert len(bs) == len(lines), (k, len(bs), len(lines))
    out = np.full_like(idx, bg)
    for (y0, y1), (kind, text) in zip(bs, lines):
        if kind == 'C':
            mt = fit(text[0], 12); mn = fit(text[1], 13)
            w = mt.shape[1] + 6 + mn.shape[1]; x = 128 - w // 2
            cy = (y0 + y1) // 2
            stamp(out, mt, x, cy - mt.shape[0] // 2, TITLE, 33)
            stamp(out, mn, x + mt.shape[1] + 6, cy - mn.shape[0] // 2, NAME, 1)
            continue
        m = fit(text, 12 if kind == 'T' else 13)
        x = 128 - m.shape[1] // 2; y = (y0 + y1) // 2 - m.shape[0] // 2
        stamp(out, m, x, y, TITLE if kind == 'T' else NAME, 33 if kind == 'T' else 1)
    return put(d, t, out)

def put(d, t, idx):
    d = bytearray(d)
    words = idx[:, 0::2].astype(np.uint16) | (idx[:, 1::2].astype(np.uint16) << 8)
    o = t['img']['off']
    d[o:o + words.size * 2] = words.astype('<u2').tobytes()
    return bytes(d)

def the_end(d):
    """STAF14: "The End" in a white face with a thick green-to-orange rim, like the original."""
    t = tim.parse(d)
    idx = tim.indices(t).astype(np.uint8)
    cl = np.array([tim.c15(int(v))[:3] for v in t['clut']['data'][0]], np.int64)
    bg = int(np.bincount(idx.ravel()).argmax())
    usable = [i for i in range(256) if t['clut']['data'][0][i] != 0]
    def nearest(rgb):
        dd = ((cl[usable] - np.array(rgb)) ** 2).sum(1)
        return usable[int(dd.argmin())]
    face = mask('The End', 34, FONT_B)
    h, w = face.shape
    R = 3
    big = np.zeros((h + 2 * R + 2, w + 2 * R + 2), bool)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            if dx * dx + dy * dy <= R * R + 1:
                big[R + 1 + dy:R + 1 + dy + h, R + 1 + dx:R + 1 + dx + w] |= face
    outer = np.zeros_like(big)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            outer[1 + dy:1 + dy + big.shape[0] - 2, 1 + dx:1 + dx + big.shape[1] - 2] |= big[1:-1, 1:-1]
    out = np.full_like(idx, bg)
    H, Wd = big.shape
    x0 = 128 - Wd // 2; y0 = 83 - H // 2
    top = np.array([40, 168, 24]); mid = np.array([232, 216, 40]); bot = np.array([224, 120, 24])
    dark = nearest((32, 72, 16))
    for y in range(H):
        f = y / (H - 1)
        rim = top + (mid - top) * (f / 0.5) if f < 0.5 else mid + (bot - mid) * ((f - 0.5) / 0.5)
        ci = nearest(tuple(int(v) for v in rim)); white = nearest((248, 248, 240))
        for x in range(Wd):
            if outer[y, x] and not big[y, x]: out[y0 + y, x0 + x] = dark
            if big[y, x]: out[y0 + y, x0 + x] = ci
    fy, fx = np.where(face)
    out[fy + y0 + R + 1, fx + x0 + R + 1] = nearest((248, 248, 240))
    return put(d, t, out)

def build(read):
    """read(name) -> bytes of ENDING/<name>. Returns {name: new bytes}."""
    out = {}
    for k in range(1, 14):
        n = 'STAF%02d.TIM' % k
        out[n] = card(read(n), k)
    out['STAF14.TIM'] = the_end(read('STAF14.TIM'))
    return out
