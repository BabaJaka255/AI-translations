"""Encode the English script and pack it (with the text engine) into the exe's text pool.
Code references keep their lui (hi16): a string moves only inside its references' 64 KB window."""
import sys, json, struct, re, collections
sys.path.insert(0, 'tools')
from textfmt import tokens, load_en
from engine import engine, ENG_BASE, SPACE_W
from font_en import advance
from refs import refs
BASE = 0x80010000 - 0x800
W_INSERT, W_NAME, W_NUM = 72, 56, 24
BOX_W, BOX_L = 224, 2
HONOR_E = True

# ------------------------------------------------------------------ geometry
def jp_geometry(words):
    """max line px, max lines per page, pages of a Japanese string"""
    mx = ml = 0; x = 0; ln = 1; pages = 1; i = 0
    while i < len(words):
        w = words[i]
        if w == 0xfffe: mx = max(mx, x); x = 0; ln += 1
        elif w == 0xfffd: mx = max(mx, x); ml = max(ml, ln); x = 0; ln = 1; pages += 1
        elif w in (0xfffc, 0xfff7, 0xfff8):
            if w == 0xfffc: x += 8 * words[i + 1]
            elif w == 0xfff7: x += W_NAME
            i += 1
        elif w == 0xfffa: x += W_INSERT
        elif w == 0xfffb: x += W_NUM
        elif w >= 0xfff0: pass
        else: x += 8 if w < 0x16 else 16
        i += 1
    mx = max(mx, x); ml = max(ml, ln)
    return mx, ml, pages

# Widest name each message's {A} can receive (px): fish 96, animals 105, items/bait/gear 121.
# Messages not listed use W_INSERT. Keeps inserted names from running off the 224 px box.
_FISH, _ANIMAL, _ITEM = 96, 105, 121
INSERT_W = {38: _FISH, 223: _FISH, 224: _FISH, 225: _FISH, 219: _FISH, 229: _FISH, 230: _FISH, 231: _FISH,
            249: _ITEM, 248: _ITEM, 259: _ITEM, 279: _ITEM, 286: _FISH, 288: _FISH, 291: _ITEM, 306: _ITEM,
            308: _ITEM, 347: _ITEM, 358: _ITEM, 365: _ITEM, 372: _ITEM, 1405: _FISH, 1752: _FISH, 1753: _FISH,
            1754: _FISH, **{k: _ANIMAL for k in range(388, 409)}}

class Metrics:
    ins_w = None
    def text(self, s): return advance(s)
    def tok(self, t):
        k, v = t
        if k == 't': return self.text(v)
        if k == 'c':
            c = v[0]
            if c == 0xfffa: return self.ins_w or W_INSERT
            if c == 0xfffb: return W_NUM
            if c == 0xfffc: return 8 * v[1]
            if c == 0xfff7: return W_NAME
        return 0

def is_message(jp_words, en):
    mx, ml, pages = jp_geometry(jp_words)
    if '{>' in en and pages == 1: return False
    if '{D}' in en or pages > 1: return True
    jp = [w for w in jp_words if w < 0xfff0]
    if re.match(r'^\{[46]\}', en) and ':' in en[:30]: return True
    return ml <= 2 and len(jp) >= 8 and jp_words and jp_words[-1 if jp_words[-1] < 0xfff0 else -2] in (2, 6, 7)

def wrap_tokens(toks, W, M):
    """word-wrap a token list (no {E}/{D} inside) -> list of lines (token lists)"""
    # split text tokens into words keeping spaces attached
    items = []
    for k, v in toks:
        if k == 't':
            for piece in re.findall(r'\S+|\s+', v): items.append(('t', piece))
        else: items.append((k, v))
    lines = [[]]; x = 0
    for it in items:
        if it[0] == 't' and it[1].isspace():
            if lines[-1]: lines[-1].append(it); x += M.tok(it)
            continue
        w = M.tok(it)
        if x + w > W and lines[-1]:
            cur = lines[-1]
            # break at the last space so a word split by control codes ({8:6} pauses) moves as a whole
            sp = max((k for k, t in enumerate(cur) if t[0] == 't' and t[1].isspace()), default=None)
            if lines[-1][-1][0] == 't' and lines[-1][-1][1].isspace() or sp is None:
                carry = []
            else:
                carry = cur[sp + 1:]; del cur[sp + 1:]
            while cur and cur[-1][0] == 't' and cur[-1][1].isspace(): cur.pop()
            lines.append(carry); x = sum(M.tok(t) for t in carry)
        lines[-1].append(it); x += w
    while lines[-1] and lines[-1][-1][0] == 't' and lines[-1][-1][1].isspace(): lines[-1].pop()
    return lines

def layout(en, jp_words, M):
    """-> (token list with {E}/{D}, warnings)"""
    warn = []
    mx, ml, pages = jp_geometry(jp_words)
    if not is_message(jp_words, en) and ml > 1 and pages == 1 and '{E}' not in en and '{>' not in en:
        # multi-line description written as one run: wrap to the JP box (widen up to 16 px if needed)
        for W in (mx, mx + 8, mx + 16):
            lines = wrap_tokens(tokens(en), W, M)
            if len(lines) <= ml: break
        else: warn.append('wrapped to %d lines > JP %d' % (len(lines), ml))
        out = []
        for li, ln in enumerate(lines):
            if li: out.append(('c', [0xfffe]))
            out.extend(ln)
        return out, warn
    if not is_message(jp_words, en):
        toks = tokens(en)
        x = 0
        for t in toks:
            if t == ('c', [0xfffe]) or t == ('c', [0xfffd]): x = 0; continue
            if t[0] == 'tab': x = t[1]; continue
            x += M.tok(t)
            if x > max(mx, 16) + 8: warn.append('menu line %dpx > JP %dpx' % (x, mx)); x = -9999
        return toks, warn
    L = ml if ml > 2 else BOX_L
    W = max(mx, BOX_W) if L > 2 else BOX_W
    out = []
    for pi, page in enumerate(en.split('{D}')):
        segs = page.split('{E}')
        choice = None
        if '{>' in segs[-1]: choice = segs.pop()
        body = ' '.join(s.strip() for s in segs if s.strip() != '' or True).strip()
        body = re.sub(r' +', ' ', body)
        lines = wrap_tokens(tokens(body), W, M) if body else []
        # strings with a long insert: keep the script's own {E} breaks when every line fits
        own = [tokens(re.sub(r' +', ' ', s.strip())) for s in segs]
        if HONOR_E and M.ins_w and len(own) > 1 and all(own) and all(sum(M.tok(t) for t in ln) <= W for ln in own):
            lines = own
        for ln in lines:
            if sum(M.tok(t) for t in ln) > W: warn.append('word too wide')
        groups = []
        cap = L
        while lines:
            groups.append(lines[:cap]); lines = lines[cap:]
        if choice is not None:
            if not groups or len(groups[-1]) >= L: groups.append([])
            groups[-1].append(tokens(choice))
        if not groups: groups = [[]]
        for gi, g in enumerate(groups):
            if out: out.append(('c', [0xfffd]))
            for li, ln in enumerate(g):
                if li: out.append(('c', [0xfffe]))
                out.extend(ln)
    return out, warn

# ------------------------------------------------------------------ dictionary + encoding
def pick_dictionary(runs, max_entries=1500, min_gain=2):
    PUA = 0xE000; corpus = list(runs); chosen = []
    for rnd in range(80):
        cnt = collections.Counter()
        for r in corpus:
            n = len(r)
            starts = [0] + [i for i in range(1, n) if r[i - 1] == ' ' or r[i] == ' ']
            for a in starts:
                if any(ord(c) >= PUA for c in r[a:a + 3]): continue
                for b in range(a + 3, min(n, a + 24) + 1):
                    if ord(r[b - 1]) >= PUA: break
                    if b == n or r[b] == ' ' or r[b - 1] == ' ': cnt[r[a:b]] += 1
        scored = []
        for s, c in cnt.items():
            if c < 2: continue
            gain = c * (len(s) / 2 - 1) - (len(s) + 1 + 4) / 2
            if gain >= min_gain: scored.append((gain, s))
        if not scored: break
        scored.sort(reverse=True); picked = []
        for g, s in scored:
            if any(s in p or p in s for p in picked): continue
            picked.append(s)
            if len(picked) >= 40: break
        for s in picked:
            k = len(chosen); chosen.append(s); mark = chr(PUA + k)
            corpus = [r.replace(s, mark) for r in corpus]
        if len(chosen) >= max_entries: break
    return chosen

NCELLS = 1068 - ENG_BASE

def pick_cells(corpus, ncells=NCELLS, rounds=4):
    """Choose the English cells: cell 0 is a space, then every character used, then the most useful
    2-4 character pieces that fit a 16 px cell. Fewer cells per line = fewer sprites."""
    chars = sorted({c for r in corpus for c in r if c != ' '} | {chr(c) for c in range(0x21, 0x7f)})
    singles = [' '] + chars
    cand = collections.Counter()
    for r in corpus:
        n = len(r)
        for i in range(n):
            for L in (2, 3, 4):
                if i + L > n: break
                p = r[i:i + L]
                if p.strip() == '' : continue
                if advance(p) > 16: break
                cand[p] += 1
    room = ncells - len(singles)
    ranked = sorted(cand, key=lambda p: -cand[p] * (len(p) - 1))
    multi, ranked = ranked[:room], ranked[room:]
    for _ in range(rounds):
        enc = Encoder([], singles + multi)
        use = collections.Counter()
        for r in corpus:
            for k in enc.cell_parse(r): use[k] += 1
        keep = [p for p in multi if use[p] >= 2]
        fresh, ranked = ranked[:room - len(keep)], ranked[room - len(keep):]
        multi = keep + fresh
    return singles + multi

class Encoder:
    def __init__(self, dictionary, cells):
        self.cells = cells; self.cid = {c: k for k, c in enumerate(cells)}
        self.first = collections.defaultdict(list)
        for c in cells: self.first[c[0]].append(('c', c, self.cid[c]))
        for k, s in enumerate(dictionary): self.first[s[0]].append(('d', s, k))
    def _dp(self, s, allow_dict=True):
        n = len(s); INF = 1 << 30
        best = [INF] * (n + 1); how = [None] * (n + 1); best[n] = 0
        for i in range(n - 1, -1, -1):
            for kind, e, k in self.first.get(s[i], ()):
                if kind == 'd' and not allow_dict: continue
                if s.startswith(e, i) and best[i + len(e)] + 1 < best[i]:
                    best[i] = best[i + len(e)] + 1; how[i] = (kind, len(e), k, e)
        if best[0] >= INF: raise ValueError('cannot encode %r' % s)
        out = []; i = 0
        while i < n:
            out.append(how[i]); i += how[i][1]
        return out
    def cell_parse(self, s):
        return [h[3] for h in self._dp(s, False)]
    def cells_of(self, s):
        return [ENG_BASE + h[2] for h in self._dp(s, False)]
    def text(self, s):
        return [ENG_BASE + h[2] if h[0] == 'c' else 0x8000 + h[2] for h in self._dp(s)]
    def encode(self, toks):
        w = []
        for k, v in toks:
            if k == 't': w += self.text(v)
            elif k == 'c': w += v
            elif k == 'tab': w.append(0x1e00 | v)
        return w + [0xffff]

# ------------------------------------------------------------------ references / placement
def window(rs):
    """allowed [lo, hi) for a string's new address, from its code refs"""
    lo_, hi_ = 0, 1 << 32
    for r in rs:
        if r[0] != 'code': continue
        h = r[4] - (r[4] & 0xffff) if r[3] == 0x0d else ((r[4] + 0x8000) & 0xffff0000)
        a, b = (h, h + 0x10000) if r[3] == 0x0d else (h - 0x8000, h + 0x8000)
        lo_, hi_ = max(lo_, a), min(hi_, b)
    return lo_, hi_

def repoint(d, r, new):
    if r[0] in ('data', 'rdata'):
        struct.pack_into('<I', d, r[1] - BASE, new); return
    _, lui_a, lo_a, op, old = r
    ins = struct.unpack_from('<I', d, lo_a - BASE)[0]
    if op == 0x0d:
        assert new >> 16 == old >> 16
        struct.pack_into('<I', d, lo_a - BASE, (ins & 0xffff0000) | (new & 0xffff)); return
    assert ((new + 0x8000) >> 16) == ((old + 0x8000) >> 16), (hex(old), hex(new))
    struct.pack_into('<I', d, lo_a - BASE, (ins & 0xffff0000) | (new & 0xffff))

def insert(exe, en, S, verbose=False):
    d = bytearray(exe)
    M = Metrics()
    R = refs(); tab = collections.defaultdict(list)
    for r in R: tab[r[4]].append(r)
    toks = {}; warns = []
    for i, t in en.items():
        o = S[i]
        if not o['jp'] and not o['words']: continue
        M.ins_w = INSERT_W.get(i)
        tk, w = layout(t, o['words'], M)
        M.ins_w = None
        toks[i] = tk
        warns += [(i, x) for x in w]
    runs = [v for t in toks.values() for k, v in t if k == 't']
    dic = pick_dictionary(runs)
    cells = pick_cells(runs + dic)
    enc = Encoder(dic, cells)
    widths = [advance(c) for c in cells]
    words = {}
    for o in S.values():
        i = o['id']
        words[i] = enc.encode(toks[i]) if i in toks else o['words'] + [0xffff]
    # pool: extents of referenced strings (+ zero padding up to next 4-byte boundary)
    pool = []
    for o in S.values():
        if o['unref']: continue
        a = int(o['addr'], 16); n = 2 * (o['n'] + 1)
        e = a + n
        while e % 4 and d[e - BASE] == 0 and e - a < o['slot']: e += 1
        pool.append([a, e])
    pool.sort(); merged = []
    for a, b in pool:
        if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    free = merged
    total_pool = sum(b - a for a, b in free)
    for a, b in free: d[a - BASE:b - BASE] = b'\0' * (b - a)
    def alloc(n, lo_=0, hi_=1 << 32, align=2, low=False):
        best = None
        for k, (a, b) in enumerate(free):
            x = max((a + align - 1) & ~(align - 1), (lo_ + align - 1) & ~(align - 1))
            if x + n <= min(b, hi_) and (best is None or (low and a < free[best][0]) or
                                         (not low and b - a < free[best][1] - free[best][0])): best = k
        if best is None: return None
        a, b = free.pop(best)
        x = max((a + align - 1) & ~(align - 1), (lo_ + align - 1) & ~(align - 1))
        if x > a: free.append([a, x])
        if x + n < b: free.append([x + n, b])
        free.sort()
        return x
    # unreferenced strings: in place, must fit
    stuck = []
    for o in S.values():
        if not o['unref'] or o['id'] not in toks: continue
        w = words[o['id']]
        if len(w) > o['n'] + 1: stuck.append(o['id']); continue
        a = int(o['addr'], 16) - BASE
        d[a:a + 2 * (o['n'] + 1)] = struct.pack('<%dH' % len(w), *w) + b'\0' * (2 * (o['n'] + 1 - len(w)))
    # engine + dictionary table first (any window)
    code_size = len(engine(0x80100000, widths, 0x80100000, [0] * 94)[0][0x80100000])
    code_at = alloc(code_size + 4 * len(dic) + 8, align=4, low=True)
    assert code_at, 'no room for engine'
    dict_ptr = (code_at + code_size + 3) & ~3
    asc = [ENG_BASE + enc.cid.get(chr(c), 0) for c in range(0x21, 0x7f)]
    P, _ = engine(code_at, widths, dict_ptr, asc)
    for a, b in P.items(): d[a - BASE:a - BASE + len(b)] = b
    # engine patch 7 (note page fish name) loads the {A} template (string 3) at 0x80087394/98
    assert struct.unpack_from('<I', d, 0x80087398 - BASE)[0] & 0xffff == 0xe24c
    tab[0x800ce24c].append(('code', 0x80087394, 0x80087398, 0x09, 0x800ce24c))
    homeless = []
    order = sorted((o for o in S.values() if not o['unref']),
                   key=lambda o: (window(tab[int(o['addr'], 16)])[1] - window(tab[int(o['addr'], 16)])[0], -len(words[o['id']])))
    placed = {}
    for o in order:
        a0 = int(o['addr'], 16); w = words[o['id']]
        lo_, hi_ = window(tab[a0])
        x = alloc(2 * len(w), lo_, hi_)
        if x is None: homeless.append(o['id']); continue
        d[x - BASE:x - BASE + 2 * len(w)] = struct.pack('<%dH' % len(w), *w)
        placed[o['id']] = x
        for r in tab[a0]: repoint(d, r, x)
    for k, s in enumerate(dic):
        cw = enc.cells_of(s) + [0]
        b = struct.pack('<%dH' % len(cw), *cw)
        x = alloc(len(b), low=True)
        assert x, 'no room for dictionary'
        d[x - BASE:x - BASE + len(b)] = b
        struct.pack_into('<I', d, dict_ptr - BASE + 4 * k, x)
    dcount = [sum(1 for c in enc.cells_of(s) if c != ENG_BASE) for s in dic]
    def sprites(ws):
        pages = [0]; i = 0
        while i < len(ws):
            x = ws[i]
            if x == 0xfffd: pages.append(0)
            elif x in (0xfffc, 0xfff7, 0xfff8): i += 1
            elif x >= 0xfff0: pass
            elif x >= 0x8000: pages[-1] += dcount[x - 0x8000]
            elif x >> 8 in (0x1e,): pass
            elif x != ENG_BASE: pages[-1] += 1
            i += 1
        return max(pages)
    for i in toks:
        e, j = sprites(words[i]), sprites(S[i]['words'])
        if e > max(j, 40): warns.append((i, 'sprites %d > JP %d' % (e, j)))
    rep = dict(pool=total_pool, free_left=sum(b - a for a, b in free), dict=len(dic), homeless=homeless,
               stuck=stuck, code=hex(code_at), warnings=warns, cells=len(cells))
    return bytes(d), rep, words, cells
