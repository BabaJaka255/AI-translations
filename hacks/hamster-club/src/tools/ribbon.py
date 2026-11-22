"""Wavy text ribbons drawn into a repeating BG pattern (tricks 3 and 76).

The original lettering runs along sine-like ribbons across the whole screen and
the tilemap reuses the same few tiles for it. Here each ribbon is found on
screen, the English unit is laid along the same curve with the same period, and
every tile pixel takes the value most of its on-screen copies want (a vote over
all saved frames), so the shared tiles stay consistent.
"""
from collections import Counter, defaultdict
import tricks
from frame import Frame

TINY = {
 'A': ".#.|#.#|###|#.#|#.#", 'B': "##.|#.#|##.|#.#|##.", 'C': ".##|#..|#..|#..|.##",
 'D': "##.|#.#|#.#|#.#|##.", 'E': "###|#..|##.|#..|###", 'F': "###|#..|##.|#..|#..",
 'G': ".##|#..|#.#|#.#|.##", 'H': "#.#|#.#|###|#.#|#.#", 'I': "#|#|#|#|#",
 'K': "#.#|#.#|##.|#.#|#.#", 'L': "#..|#..|#..|#..|###", 'M': "#...#|##.##|#.#.#|#...#|#...#",
 'N': "#..#|##.#|#.##|#..#|#..#", 'O': ".#.|#.#|#.#|#.#|.#.", 'P': "##.|#.#|##.|#..|#..",
 'R': "##.|#.#|##.|#.#|#.#", 'S': ".##|#..|.#.|..#|##.", 'T': "###|.#.|.#.|.#.|.#.",
 'U': "#.#|#.#|#.#|#.#|###", 'W': "#...#|#...#|#.#.#|##.##|#...#", 'Y': "#.#|#.#|.#.|.#.|.#.",
 'Z': "###|..#|.#.|#..|###", '!': "#|#|#|.|#", '-': "...|...|###|...|...", "'": "#|#|.|.|.",
 'm': "#...#|##.##|#.#.#|#...#",
}

def glyph(ch):
    return [[c == '#' for c in row] for row in TINY[ch].split('|')]

def unit_layout(text, gap=1):
    """[(dx, glyph)] for one repeat of `text` (space = 2px)."""
    out, x = [], 0
    for ch in text:
        if ch == ' ': x += 2; continue
        g = glyph(ch); out.append((x, g)); x += len(g[0]) + gap
    return out

def components(mask, rx=5, ry=2):
    H, W = len(mask), len(mask[0])
    lab = [[0] * W for _ in range(H)]; n = 0
    pts = [(x, y) for y in range(H) for x in range(W) if mask[y][x]]
    ptset = set(pts)
    for p in pts:
        if lab[p[1]][p[0]]: continue
        n += 1; stack = [p]; lab[p[1]][p[0]] = n
        while stack:
            x, y = stack.pop()
            for dy in range(-ry, ry + 1):
                for dx in range(-rx, rx + 1):
                    q = (x + dx, y + dy)
                    if q in ptset and not lab[q[1]][q[0]]:
                        lab[q[1]][q[0]] = n; stack.append(q)
    groups = defaultdict(list)
    for x, y in pts: groups[lab[y][x]].append((x, y))
    return list(groups.values())

def ribbons(tid, tiles, text_v, bg_v, period, text, frames=None, gap=1, min_len=24, phase_shift=0):
    sh = tricks.sheets(tid)
    votes = defaultdict(Counter)
    layout = unit_layout(text, gap)
    for fr in (frames if frames is not None else range(tricks.nframes(tid))):
        f = Frame(tricks.state(tid, fr), sh)
        src = {}
        T = [[0] * 160 for _ in range(144)]
        for y in range(144):
            for x in range(160):
                t = f.top(x, y)
                if t and t[4] == 'bg' and t[1] in tiles:
                    src[(x, y)] = t
                    if f.value(t) == text_v: T[y][x] = 1
        if not src: continue
        want = {p: bg_v for p in src}
        for comp in components(T):
            xs = [p[0] for p in comp]
            if max(xs) - min(xs) < min_len: continue
            cols = defaultdict(list)
            for x, y in comp: cols[x].append(y)
            def yc(x):
                ys = [y for xx in range(x - 6, x + 7) for y in cols.get(xx, [])]
                return sum(ys) / len(ys) if ys else None
            cnt = {x: len(v) for x, v in cols.items()}
            phase = min(range(period), key=lambda ph: sum(c for x, c in cnt.items() if x % period == ph))
            x0, x1 = min(xs), max(xs)
            u = x0 - period + ((phase + 1 + phase_shift - (x0 - period)) % period)
            while u <= x1 + period:
                for dx, g in layout:
                    gx = u + dx; c = yc(gx + len(g[0]) // 2)
                    if c is None: continue
                    gy = round(c - len(g) / 2)
                    for j, row in enumerate(g):
                        for i, on in enumerate(row):
                            if on and (gx + i, gy + j) in want: want[(gx + i, gy + j)] = text_v
                u += period
        for p, t in src.items():
            votes[t[:4]][want[p]] += 1
    for key, c in votes.items():
        f_any = key
        name, tile, tx, ty = key
        sheet = sh[name][0]
        # same mapping as Frame.xy for a linear BG sheet
        W = sheet.w // 8
        sheet.put((tile % W) * 8 + tx, (tile // W) * 8 + ty, c.most_common(1)[0][0])
    return len(votes)


def anchored(tid, tiles, text_v, bg_v, text, is_anchor, frames=None, gap=1, dx0=0, conn=1, text_weight=4, blank=(), next_slope=None):
    """Lay one English unit on every anchor glyph (a connected run of text pixels
    picked by is_anchor(w, h, n)), centred on it and tilted with it; everything
    else in the lettering tiles becomes background. Tile pixels take the value
    most of their on-screen copies want."""
    sh = tricks.sheets(tid)
    votes = defaultdict(Counter)
    layout = unit_layout(text, gap)
    uw = max(dx + len(g[0]) for dx, g in layout)
    for fr in (frames if frames is not None else range(tricks.nframes(tid))):
        f = Frame(tricks.state(tid, fr), sh)
        src = {}; open_ = set()
        T = [[0] * 160 for _ in range(144)]
        for y in range(144):
            for x in range(160):
                t = f.top(x, y)
                if t and t[4] == 'bg' and t[1] in blank: open_.add((x, y))
                if t and t[4] == 'bg' and t[1] in tiles:
                    src[(x, y)] = t; open_.add((x, y))
                    if f.value(t) == text_v: T[y][x] = 1
        if not src: continue
        want = {p: bg_v for p in src}
        comps = components(T, conn, conn)
        cents = []
        for comp in comps:
            xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
            w = max(xs) - min(xs) + 1; h = max(ys) - min(ys) + 1
            if is_anchor(w, h, len(comp)): cents.append((sum(xs) / len(xs), sum(ys) / len(ys)))
        for comp in comps:
            xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
            w = max(xs) - min(xs) + 1; h = max(ys) - min(ys) + 1
            if not is_anchor(w, h, len(comp)): continue
            # skip glyphs cut by the screen edge or by something drawn over them
            ring = {(x + dx, y + dy) for x, y in comp for dx in (-2, 0, 2) for dy in (-2, 0, 2)}
            if any(p not in open_ for p in ring): continue
            n = len(comp); cx = sum(xs) / n; cy = sum(ys) / n
            vx = sum((x - cx) ** 2 for x in xs) or 1
            slope = sum((x - cx) * (y - cy) for x, y in comp) / vx
            if next_slope:
                lo, hi = next_slope
                nb = [(ox, oy) for ox, oy in cents if lo <= ox - cx <= hi and abs(oy - cy) < 10]
                pb = [(ox, oy) for ox, oy in cents if lo <= cx - ox <= hi and abs(oy - cy) < 10]
                if nb: slope = (nb[0][1] - cy) / (nb[0][0] - cx)
                elif pb: slope = (cy - pb[0][1]) / (cx - pb[0][0])
                else: slope = 0
            ux = round(cx - uw / 2) + dx0
            for dx, g in layout:
                gx = ux + dx; gcx = gx + len(g[0]) / 2
                gy = round(cy + slope * (gcx - cx) - len(g) / 2)
                for j, row in enumerate(g):
                    for i, on in enumerate(row):
                        if on and (gx + i, gy + j) in want: want[(gx + i, gy + j)] = text_v
        for p, t in src.items():
            votes[t[:4]][want[p]] += text_weight if want[p] == text_v else 1
    bad = 0
    for key, c in votes.items():
        name, tile, tx, ty = key
        sheet = sh[name][0]; W = sheet.w // 8
        v, k = c.most_common(1)[0]
        bad += sum(c.values()) - k
        sheet.put((tile % W) * 8 + tx, (tile // W) * 8 + ty, v)
    return bad


def substitute(tid, tiles, text_v, bg_v, subs, frames=None, text_weight=4, align='center', strict=True):
    """Glyph-for-letter swap in a repeating BG pattern. subs: [(template, letters)]
    with template rows like ".#..|####" ('#' = text pixel). Every exact match of a
    template on screen is replaced by `letters` (TINY font), bottom-aligned and
    centred on it; other text pixels in the tiles become background. Votes as in
    anchored()."""
    sh = tricks.sheets(tid)
    votes = defaultdict(Counter)
    temps = []
    for sub in subs:
        t, letters = sub[0], sub[1]; dy = sub[2] if len(sub) > 2 else None
        rows = t.split('|'); pts = [(i, j) for j, r in enumerate(rows) for i, c in enumerate(r) if c == '#']
        offs = [(i, j) for j, r in enumerate(rows) for i, c in enumerate(r) if c == '.']
        temps.append((pts, offs, len(rows[0]), len(rows), unit_layout(letters), dy))
    for fr in (frames if frames is not None else range(tricks.nframes(tid))):
        f = Frame(tricks.state(tid, fr), sh)
        src = {}; T = set()
        for y in range(144):
            for x in range(160):
                t = f.top(x, y)
                if t and t[4] == 'bg' and t[1] in tiles:
                    src[(x, y)] = t
                    if f.value(t) == text_v: T.add((x, y))
        if not src: continue
        want = {p: bg_v for p in src}
        for pts, offs, w, h, lay, ddy in temps:
            for (x, y) in T:
                ox, oy = x - pts[0][0], y - pts[0][1]
                if all((ox + i, oy + j) in T for i, j in pts) and not (strict and any((ox + i, oy + j) in T for i, j in offs)):
                    lw = max(dx + len(g[0]) for dx, g in lay)
                    bx = ox + (w - lw + 1) // 2 if align == 'center' else ox
                    for dx, g in lay:
                        gy = oy + h - len(g) if ddy is None else oy + ddy
                        for j, row in enumerate(g):
                            for i, on in enumerate(row):
                                q = (bx + dx + i, gy + j)
                                if on and q in want: want[q] = text_v
        for p, t in src.items():
            votes[t[:4]][want[p]] += text_weight if want[p] == text_v else 1
    for key, c in votes.items():
        name, tile, tx, ty = key
        sheet = sh[name][0]; W = sheet.w // 8
        sheet.put((tile % W) * 8 + tx, (tile // W) * 8 + ty, c.most_common(1)[0][0])
    return len(votes)
