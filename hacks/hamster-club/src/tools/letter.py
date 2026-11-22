"""Hand-lettering engine for the Hamster Club art redraws.

Letters are drawn from a stroke alphabet (polylines in a 4x6 box, cap height 6),
rendered at 4x with round brush ends, then reduced to 1x. Slant, per-point
wobble, per-letter bounce, stroke weight and spacing give each piece its own
hand-drawn look, so nothing here is a computer font.

    mask = letter.render("KOFF", cap=7, weight=2, slant=0.25, wobble=0.3, seed=1)
    -> list of rows of 0/1 (1 = ink)

Effects (outline, shadow) work on these masks; sheet.py paints them into tiles.
"""
import math, random
from PIL import Image, ImageDraw

A = {
 'A': [[(0,6),(2,0),(4,6)], [(0.9,3.8),(3.1,3.8)]],
 'B': [[(0,6),(0,0),(3,0),(4,0.9),(4,2.1),(3,3),(0,3)], [(3,3),(4,3.9),(4,5.1),(3,6),(0,6)]],
 'C': [[(4,1),(3,0),(1,0),(0,1),(0,5),(1,6),(3,6),(4,5)]],
 'D': [[(0,0),(0,6),(2.4,6),(4,4.4),(4,1.6),(2.4,0),(0,0)]],
 'E': [[(4,0),(0,0),(0,6),(4,6)], [(0,3),(3,3)]],
 'F': [[(4,0),(0,0),(0,6)], [(0,3),(3,3)]],
 'G': [[(4,1),(3,0),(1,0),(0,1),(0,5),(1,6),(3,6),(4,5),(4,3.5),(2.4,3.5)]],
 'H': [[(0,0),(0,6)], [(4,0),(4,6)], [(0,3),(4,3)]],
 'I': [[(2,0),(2,6)], [(1,0),(3,0)], [(1,6),(3,6)]],
 'J': [[(4,0),(4,5),(3,6),(1,6),(0,5)]],
 'K': [[(0,0),(0,6)], [(4,0),(0,3.6)], [(1.4,2.6),(4,6)]],
 'L': [[(0,0),(0,6),(4,6)]],
 'M': [[(0,6),(0,0),(2,3.6),(4,0),(4,6)]],
 'N': [[(0,6),(0,0),(4,6),(4,0)]],
 'O': [[(1,0),(3,0),(4,1),(4,5),(3,6),(1,6),(0,5),(0,1),(1,0)]],
 'P': [[(0,6),(0,0),(3,0),(4,1),(4,2.5),(3,3.5),(0,3.5)]],
 'Q': [[(1,0),(3,0),(4,1),(4,5),(3,6),(1,6),(0,5),(0,1),(1,0)], [(2.4,4.4),(4.3,6.3)]],
 'R': [[(0,6),(0,0),(3,0),(4,1),(4,2.5),(3,3.5),(0,3.5)], [(2,3.5),(4,6)]],
 'S': [[(4,1),(3,0),(1,0),(0,1),(0,2),(1,3),(3,3),(4,4),(4,5),(3,6),(1,6),(0,5)]],
 'T': [[(0,0),(4,0)], [(2,0),(2,6)]],
 'U': [[(0,0),(0,5),(1,6),(3,6),(4,5),(4,0)]],
 'V': [[(0,0),(2,6),(4,0)]],
 'W': [[(0,0),(1,6),(2,2.4),(3,6),(4,0)]],
 'X': [[(0,0),(4,6)], [(4,0),(0,6)]],
 'Y': [[(0,0),(2,3),(4,0)], [(2,3),(2,6)]],
 'Z': [[(0,0),(4,0),(0,6),(4,6)]],
 '!': [[(2,0),(2,3.9)], [(2,5.9)]],
 '?': [[(0,1),(1,0),(3,0),(4,1),(4,2),(2,3.4),(2,4.1)], [(2,5.9)]],
 '-': [[(0.4,3),(3.6,3)]],
 '~': [[(0,3.6),(1,2.6),(2,3),(3,3.4),(4,2.4)]],
 '.': [[(2,5.9)]],
 ',': [[(2.2,5.6),(1.6,6.8)]],
 "'": [[(2,0),(1.6,1.6)]],
 '♥': [[(2,6),(0.2,3),(0,1.5),(0.8,0.3),(2,1.2),(3.2,0.3),(4,1.5),(3.8,3),(2,6)]],
 '…': [[(0.4,5.9)], [(2,5.9)], [(3.6,5.9)]],
}
NARROW = {'I': 0.6, '!': 0.35, '.': 0.35, ',': 0.35, "'": 0.35, '-': 0.8, 'M': 1.2, 'W': 1.2}

def render(text, cap=7, weight=2.0, width=None, slant=0.0, wobble=0.0, bounce=0.0,
           spacing=1, seed=0, sizes=None, S=4, thresh=0.45, angle=0.0):
    """Return a mask (list of rows of 0/1). width = letter width in px (default cap*0.7).
    sizes: optional per-letter scale factors. angle: rotate the whole word (degrees)."""
    rnd = random.Random(seed)
    width = width if width is not None else max(3, round(cap * 0.7))
    sizes = sizes or [1.0] * len(text)
    glyphs = []
    x = 0.0
    hmax = max(cap * s for s in sizes)
    for ch, sc in zip(text, sizes):
        if ch == ' ':
            x += width * 0.8 * sc; continue
        strokes = A[ch.upper()] if ch.upper() in A else A['?']
        w = width * sc * NARROW.get(ch.upper(), 1.0); h = cap * sc
        full = width * sc
        dy = rnd.uniform(-bounce, bounce)
        base = hmax - h + dy
        pts = []
        for st in strokes:
            q = []
            for (px, py) in st:
                gx = (px - 2) / 4 * full + w / 2 if ch.upper() in NARROW else px / 4 * w
                gy = base + py / 6 * h
                gx += rnd.uniform(-wobble, wobble); gy += rnd.uniform(-wobble, wobble)
                q.append((x + gx, gy))
            pts.append(q)
        glyphs.append(pts)
        x += w + spacing + weight
    total_w = x + abs(slant) * hmax + 4
    W = int(math.ceil(total_w)) + 4; H = int(math.ceil(hmax + weight + 2 * bounce)) + 4
    img = Image.new('L', (W * S, H * S), 0)
    d = ImageDraw.Draw(img)
    r = weight * S / 2
    off = 2 + weight / 2
    for pts in glyphs:
        for st in pts:
            sp = [((px + off + slant * (hmax - py)) * S, (py + off + bounce) * S) for (px, py) in st]
            if len(sp) > 1:
                d.line(sp, fill=255, width=max(1, int(round(weight * S))), joint='curve')
            for (a, b) in sp:
                d.ellipse((a - r, b - r, a + r, b + r), fill=255)
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    small = img.resize((img.width // S, img.height // S), Image.BOX)
    m = [[1 if small.getpixel((i, j)) >= 255 * thresh else 0 for i in range(small.width)] for j in range(small.height)]
    return trim(m)

def trim(m):
    rows = [j for j, r in enumerate(m) if any(r)]
    cols = [i for i in range(len(m[0])) if any(r[i] for r in m)] if rows else []
    if not rows: return [[0]]
    return [r[cols[0]:cols[-1] + 1] for r in m[rows[0]:rows[-1] + 1]]

def dilate(m, n=1, diag=True):
    h, w = len(m), len(m[0])
    out = [[0] * (w + 2 * n) for _ in range(h + 2 * n)]
    for j in range(h):
        for i in range(w):
            if m[j][i]:
                for dj in range(-n, n + 1):
                    for di in range(-n, n + 1):
                        if diag or abs(di) + abs(dj) <= n:
                            out[j + n + dj][i + n + di] = 1
    return out

def show(m):
    return '\n'.join(''.join('#' if v else '.' for v in r) for r in m)

if __name__ == '__main__':
    import sys
    print(show(render(sys.argv[1], cap=int(sys.argv[2]) if len(sys.argv) > 2 else 7, weight=2, slant=0.2)))
