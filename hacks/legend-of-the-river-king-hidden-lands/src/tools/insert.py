"""Insert the English script into SLPS_015.36.

Steps: read text/en_*.txt, wrap each string to its window, pick dictionary entries, encode,
then place each string in its own slot or, when it does not fit, move it into free space and
repoint its references (code lui/addiu pairs or data pointers).
"""
import sys, json, struct, re, glob, collections
sys.path.insert(0, 'tools')
from strings import EXE, BASE, REGIONS
from refs import refs
from hook import ENG_BASE, SPACE_W
import font_en

import os
PROJ = os.environ.get('HK_PROJ', '.')    # working copy of hikyou/ (text/, out/)
NARROW = 22                     # glyphs 0-21 are 8px wide
W_A, W_NAME, W_B = 84, 46, 24   # width guesses for {A} inserts, names and {B} numbers

_, WID = font_en.build()
def text_px(s):
    return sum(SPACE_W if c == ' ' else WID.get(ord(c), 6) for c in s)

# ---------------------------------------------------------------- parsing
TOK = re.compile(r'\{([^}]*)\}')
def tokens(s):
    """English source -> list of (kind, value). kinds: t text, nl, pg, w (raw words, px)."""
    out = []; pos = 0
    for m in TOK.finditer(s):
        if m.start() > pos: out.append(('t', s[pos:m.start()]))
        k = m.group(1); pos = m.end()
        if k == 'E': out.append(('nl', None))
        elif k == 'D': out.append(('pg', [0xfffd]))
        elif k == '9': out.append(('pg', [0xfff9]))
        elif k in ('5', '6'): out.append(('w', ([0xfff0 | int(k, 16)], 0)))
        elif k == 'A': out.append(('w', ([0xfffa], W_A)))
        elif k == 'B': out.append(('w', ([0xfffb], W_B)))
        elif k.startswith('C:'): out.append(('w', ([0xfffc, int(k[2:])], 8 * int(k[2:]))))
        elif k.startswith('7:'): out.append(('w', ([0xfff7, int(k[2:])], W_NAME)))
        elif k.startswith('8:'): out.append(('w', ([0xfff8, int(k[2:])], 0)))
        elif k.startswith('>'): out.append(('tab', int(k[1:])))
        elif re.fullmatch(r'[0-9a-fA-F]{4}', k): out.append(('w', ([int(k, 16)], 16)))
        else: raise ValueError('bad control {%s} in %r' % (k, s))
    if pos < len(s): out.append(('t', s[pos:]))
    return out

# ---------------------------------------------------------------- window geometry from the Japanese
def jp_geometry(jp):
    """(max line px, max lines per page, pages) of the original string."""
    jp = re.sub(r'\{[789C]\}.', lambda m: '\x01' if m.group(0)[1] == '7' else ('\x02' if m.group(0)[1] == 'C' else ''), jp)
    pages = re.split(r'\{[D9]\}', jp)
    mx = 0; ml = 0
    for p in pages:
        lines = p.split('{E}')
        ml = max(ml, len(lines))
        for ln in lines:
            ln = re.sub(r'\{[56]\}', '', ln)
            px = 0
            for t in re.findall(r'\{A\}|\{B\}|.', ln):
                if t == '{A}': px += 16 * 6
                elif t == '{B}': px += W_B
                elif t == '\x01': px += 64
                elif t == '\x02': px += 24
                elif t == '\u3000': px += 8       # the full-width space is a narrow glyph
                else: px += 16
            mx = max(mx, px)
    return mx, ml, len(pages)

# ---------------------------------------------------------------- wrapping
def wrap(toks, W, L, paging):
    """Greedy word wrap. Returns (tokens with nl/pg inserted, list of warnings)."""
    # split text tokens into words (keeping the space with the following word)
    items = []
    for k, v in toks:
        if k == 't':
            for part in re.split(r'( )', v):
                if part: items.append(('t', part))
        else: items.append((k, v))
    out = []; x = 0; lines = 1; warn = []
    def px(it):
        k, v = it
        if k == 't': return text_px(v)
        if k == 'w': return v[1]
        return 0
    i = 0
    while i < len(items):
        k, v = items[i]
        if k == 'nl':
            out.append(('nl', None)); x = 0; lines += 1
            if lines > L and paging:
                out[-1] = ('pg', [0xfffd]); lines = 1
            i += 1; continue
        if k == 'pg':
            out.append((k, v)); x = 0; lines = 1; i += 1; continue
        if k == 'tab':
            out.append((k, v)); x = v; i += 1; continue
        # a word: text run up to the next space, together with glued controls
        j = i; wpx = 0
        while j < len(items) and items[j][0] in ('t', 'w') and not (j > i and items[j] == ('t', ' ')):
            wpx += px(items[j]); j += 1
        if items[i] == ('t', ' '):
            # leading space: belongs to this word
            j = i + 1; wpx = SPACE_W
            while j < len(items) and items[j][0] in ('t', 'w') and items[j] != ('t', ' '):
                wpx += px(items[j]); j += 1
        word = items[i:j]
        if x + wpx > W and x > 0:
            # break the line before this word (drop the leading space)
            if word and word[0] == ('t', ' '): word = word[1:]; wpx -= SPACE_W
            lines += 1
            if lines > L and paging:
                out.append(('pg', [0xfffd])); lines = 1
            else:
                out.append(('nl', None))
            x = 0
        out.extend(word); x += wpx
        if x > W: warn.append('line too wide (%d > %d)' % (x, W))
        i = j
    if lines > L and not paging: warn.append('%d lines > %d' % (lines, L))
    # merge text
    m = []
    for k, v in out:
        if k == 't' and m and m[-1][0] == 't': m[-1] = ('t', m[-1][1] + v)
        else: m.append((k, v))
    return m, warn

# ---------------------------------------------------------------- 2-line message box pages
BOX_W = 228          # usable width of the dialogue box: text x 16..243, inner frame 13..246 (measured)

def _soft(toks):
    """Line breaks become spaces, except before a tab (a Yes/No row keeps its own line)."""
    out = []
    for n, (k, v) in enumerate(toks):
        if k == 'nl' and not (n + 1 < len(toks) and toks[n + 1][0] == 'tab'):
            if out and out[-1][0] == 't' and out[-1][1].endswith(' '): continue
            out.append(('t', ' '))
        elif k == 't' and out and out[-1] == ('t', ' ') and v.startswith(' '):
            out.append(('t', v[1:]))
        else: out.append((k, v))
    m = []
    for k, v in out:
        if k == 't' and m and m[-1][0] == 't': m[-1] = ('t', m[-1][1] + v)
        elif (k, v) != ('t', ''): m.append((k, v))
    if m and m[0][0] == 't': m[0] = ('t', m[0][1].lstrip(' '))
    if m and m[-1][0] == 't': m[-1] = ('t', m[-1][1].rstrip(' '))
    return [(k, v) for k, v in m if (k, v) != ('t', '')]

def _lines(t, W):
    w, _ = wrap(t, W, 99, False)
    return w, 1 + sum(1 for k, v in w if k == 'nl')

def _words(u):
    """Flowing text -> list of words; each word is a token list (controls glued to their word)."""
    words = [[]]
    for k, v in u:
        if k != 't': words[-1].append((k, v)); continue
        for n, part in enumerate(v.split(' ')):
            if n: words.append([])
            if part: words[-1].append(('t', part))
    return [w for w in words if w]

def _wtext(w):
    return ''.join(v for k, v in w if k == 't')

def _wpx(w):
    return sum(text_px(v) if k == 't' else (v[1] if k == 'w' else 0) for k, v in w)

def _flow(words, W):
    """Greedy wrap of a word list: list of lines (each a list of words)."""
    lines = [[]]; x = 0
    for w in words:
        px = _wpx(w)
        if lines[-1] and x + SPACE_W + px > W:
            lines.append([]); x = 0
        x += (SPACE_W if lines[-1] else 0) + px
        lines[-1].append(w)
    return lines

def _emit(lines):
    out = []
    for n, ln in enumerate(lines):
        if n: out.append(('nl', None))
        for m, w in enumerate(ln):
            if m: out.append(('t', ' '))
            out.extend(w)
    return out

def _box(words, W):
    """Lay out one box (at most 2 lines). A second line holding a lone short word is avoided
    by wrapping a little narrower when that still fits in two lines."""
    lines = _flow(words, W)
    if len(lines) == 2 and len(lines[1]) == 1 and len(words) > 3 and _wpx(lines[1][0]) < W * 0.4:
        for W2 in range(W - 4, int(W * 0.6), -4):
            l2 = _flow(words, W2)
            if len(l2) > 2: break
            if len(l2[1]) >= 2: lines = l2; break
    return lines

END_S = ('.', '!', '?', '!"', '?"', '."', '!)', '?)', '.)', '...', '…')
END_C = (',', ';', ':', '--')
GOOD = {'to', 'and', 'but', 'so', 'or', 'with', 'for', 'because', 'until', 'when', 'if', 'then', 'that',
        'in', 'on', 'at', 'from', 'by', 'about', 'of', 'than', 'who', 'which', 'saying', 'while', 'since'}

def _layout(words, W):
    """Split a flowing speech into boxes of two lines. Fewest boxes first; among those, boxes
    break at sentence ends, then at commas; a box never holds just a word or two."""
    n = len(words)
    INF = float('inf')
    depth = []; d = 0                       # open parentheses after each word
    for w in words:
        t = _wtext(w); d = max(0, d + t.count('(') - t.count(')')); depth.append(d)
    best = [INF] * (n + 1); nxt = [None] * (n + 1); best[n] = 0
    for i in range(n - 1, -1, -1):
        x = 0; lines = 1; nw = 0
        for j in range(i + 1, n + 1):
            px = _wpx(words[j - 1])
            if x and x + SPACE_W + px > W:
                lines += 1; x = px; nw = 1
            else:
                x += (SPACE_W if x else 0) + px; nw += 1
            if lines > 2: break
            last = _wtext(words[j - 1])
            nxtw = _wtext(words[j]).lower() if j < n else ''
            if j == n or (last.endswith(END_S) and depth[j - 1] == 0): brk = 0
            elif last.endswith(':') and j <= 4: brk = 3          # never strand a speaker label
            elif last.endswith(END_S) or last.endswith(END_C): brk = 0.8
            elif nxtw in GOOD: brk = 1.3
            else: brk = 1.6
            short = 0
            if lines == 1 and (i > 0 or j < n):
                if x < W * 0.45: short = 0.5
                if j < n: short += 0.3 * (1 - x / W)
            elif lines == 2 and j < n:
                bl = _box(words[i:j], W)
                xl = sum(_wpx(w) for w in bl[-1]) + SPACE_W * (len(bl[-1]) - 1)
                short = 0.2 * (1 - xl / W) + (0.4 if len(bl[-1]) == 1 else 0)
            c = 1 + brk + short + best[j]
            if c < best[i]: best[i] = c; nxt[i] = j
    out = []; i = 0
    while i < n:
        j = nxt[i]
        if out: out.append(('pg', [0xfffd]))
        out.extend(_emit(_box(words[i:j], W)))
        i = j
    return out

def paginate(toks, W):
    """Re-page a 2-line message. The text between hard breaks ({9}: postcard / scene steps) is
    treated as one flowing speech and laid out by _layout; a Yes/No row stays in the box with
    its question."""
    warn = []
    parts = [[]]
    for k, v in toks:
        if k == 'pg' and v != [0xfffd]: parts.append(('hard', v)); parts.append([]); continue
        parts[-1].append((k, v))
    out = []
    for part in parts:
        if isinstance(part, tuple): out.append(('pg', part[1])); continue
        units = [[]]
        for k, v in part:
            if k == 'pg': units.append([]); continue
            units[-1].append((k, v))
        pages = []
        block = []
        for u in units:
            if any(k == 'tab' for k, v in u):
                # question + choice row: the choice row keeps its own line
                q = []; row = []
                for n, (k, v) in enumerate(u):
                    if k == 'nl' and n + 1 < len(u) and u[n + 1][0] == 'tab': row = u[n:]; break
                    q.append((k, v))
                q = _soft(q)
                if block: pages.append(_layout(_words(_soft(block)), W)); block = []
                ql = _flow(_words(q), W)
                if len(ql) > 1:
                    warn.append('question over one line above a choice row')
                    pages.append(_layout(_words(q), W)); pages.append(row[1:])
                else:
                    pages.append(_emit(ql) + row)
            else:
                block = block + ([('t', ' ')] if block else []) + u
        if block: pages.append(_layout(_words(_soft(block)), W))
        for n, pg in enumerate(pages):
            if n: out.append(('pg', [0xfffd]))
            out.extend(pg)
    x = 0; ln = 0
    for k, v in out:
        if k == 'nl': x = 0; ln += 1
        elif k == 'pg': x = 0; ln = 0
        elif k == 'tab': x = v
        elif k == 't': x += text_px(v)
        elif k == 'w': x += v[1]
        if x > W: warn.append('line too wide (%d > %d)' % (x, W)); x = -10 ** 6
        if ln > 1: warn.append('3 lines in a box'); ln = -10 ** 6
    return out, warn

# ---------------------------------------------------------------- dictionary
def pick_dictionary(runs, max_entries=4000, min_gain=2):
    """Greedy choice of substrings that save the most words. runs: list of text runs."""
    PUA = 0xE000
    corpus = list(runs)
    chosen = []
    for rnd in range(60):
        cnt = collections.Counter()
        for r in corpus:
            n = len(r)
            starts = [0] + [i for i in range(1, n) if r[i - 1] == ' ' or r[i] == ' ']
            for a in starts:
                if any(ord(c) >= PUA for c in r[a:a + 3]): continue
                for b in range(a + 3, min(n, a + 24) + 1):
                    if ord(r[b - 1]) >= PUA: break
                    if b == n or r[b] == ' ' or r[b - 1] == ' ':
                        cnt[r[a:b]] += 1
        scored = []
        for s, c in cnt.items():
            if c < 2: continue
            gain = c * (len(s) / 2 - 1) - (len(s) + 1 + 4) / 2
            if gain >= min_gain: scored.append((gain, s))
        if not scored: break
        scored.sort(reverse=True)
        picked = []
        for g, s in scored:
            if any(s in p or p in s for p in picked): continue
            picked.append(s)
            if len(picked) >= 40: break
        for s in picked:
            k = len(chosen); chosen.append(s)
            mark = chr(PUA + k)
            corpus = [r.replace(s, mark) for r in corpus]
        if len(chosen) >= max_entries: break
    return chosen

class Encoder:
    def __init__(self, dictionary):
        self.d = dictionary
        self.first = collections.defaultdict(list)
        for k, s in enumerate(dictionary): self.first[s[0]].append((s, k))
    def text(self, s):
        n = len(s); INF = 1 << 30
        best = [INF] * (n + 1); how = [None] * (n + 1); best[n] = 0
        for i in range(n - 1, -1, -1):
            if best[i + 1] + 1 < best[i]: best[i] = best[i + 1] + 1; how[i] = ('1', 1)
            if i + 2 <= n and best[i + 2] + 1 < best[i]: best[i] = best[i + 2] + 1; how[i] = ('2', 2)
            for e, k in self.first.get(s[i], ()):
                if s.startswith(e, i) and best[i + len(e)] + 1 <= best[i]:
                    best[i] = best[i + len(e)] + 1; how[i] = ('d', len(e), k)
        out = []; i = 0
        while i < n:
            h = how[i]
            if h[0] == '1': out.append(0x1f00 | ord(s[i]))
            elif h[0] == '2': out.append(ord(s[i]) | ord(s[i + 1]) << 8)
            else: out.append(0x8000 + h[2])
            i += h[1]
        return out
    def encode(self, toks):
        w = []
        for k, v in toks:
            if k == 't': w += self.text(v)
            elif k == 'nl': w.append(0xfffe)
            elif k == 'pg': w += v
            elif k == 'w': w += v[0]
            elif k == 'tab': w.append(0x1e00 | v)
        return w + [0xffff]

# ---------------------------------------------------------------- references
def ref_table(d):
    """value -> list of patchable refs; also the set of lui offsets that are shared."""
    R = refs(d, [(0xbfb04, 0xdc612)])     # the main regions and the gaps between them
    by_lui = collections.defaultdict(set)
    for r in R:
        if r[0] == 'code': by_lui[r[1]].add(r[4])
    tab = collections.defaultdict(list)
    for r in R: tab[r[4]].append(r)
    return tab, by_lui

def lui_exclusive(d, lui_off, lows):
    """True when every read of the lui's register, until it is overwritten or control leaves
    the block, is one of the instructions in `lows`."""
    reg = (struct.unpack_from('<I', d, lui_off)[0] >> 16) & 31
    end = None
    i = lui_off + 4
    while i < lui_off + 0x100 and (end is None or i <= end):
        x = struct.unpack_from('<I', d, i)[0]
        op = x >> 26; rs = (x >> 21) & 31; rt = (x >> 16) & 31; rd = (x >> 11) & 31; fn = x & 0x3f
        if op == 0:
            reads = {rs, rt}; writes = {rd}; jump = fn in (8, 9)
        elif op in (2, 3):
            reads = set(); writes = {31} if op == 3 else set(); jump = True
        elif op in (4, 5):
            reads = {rs, rt}; writes = set(); jump = True
        elif op in (1, 6, 7):
            reads = {rs}; writes = set(); jump = True
        elif op == 0x0f:
            reads = set(); writes = {rt}; jump = False
        elif op >= 0x28:
            reads = {rs, rt}; writes = set(); jump = False
        else:
            reads = {rs}; writes = {rt}; jump = False
        if reg in reads and i not in lows: return False
        if reg in writes: return True
        if jump and end is None: end = i + 4
        i += 4
    return True

def lo16(v): return v & 0xffff
def hi16(v): return ((v + 0x8000) >> 16) & 0xffff

def repoint(d, r, new):
    kind = r[0]
    if kind == 'data':
        struct.pack_into('<I', d, r[1], new); return
    _, lui_off, lo_off, op, old = r
    ins = struct.unpack_from('<I', d, lui_off)[0]
    struct.pack_into('<I', d, lui_off, (ins & 0xffff0000) | hi16(new))
    ins = struct.unpack_from('<I', d, lo_off)[0]
    if op == 0x0d: raise ValueError('ori ref')
    struct.pack_into('<I', d, lo_off, (ins & 0xffff0000) | lo16(new))

# ---------------------------------------------------------------- main
def load_script():
    S = {o['id']: o for o in json.load(open(PROJ + '/out/script_jp.json'))}
    S.update({o['id']: o for o in json.load(open(PROJ + '/out/script_extra.json'))})
    return S

def load_en():
    en = {}
    for fn in sorted(glob.glob(PROJ + '/text/en_*.txt')):
        for ln in open(fn, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln or ln.startswith('#'): continue
            i, t = ln.split('|', 1)
            en[int(i)] = t
    return en

def prepare(en, S):
    """Wrap every English string. Returns {id: tokens}, warnings.
    Menus (tabs, or 3+ short lines) are never wrapped; messages go to the 224px, 2-line box
    unless the Japanese shows a bigger window (fish notes, letters)."""
    out = {}; warns = []
    for i, s in sorted(en.items()):
        o = S[i]
        mx, ml, pages = jp_geometry(o['jp'])
        toks = tokens(s)
        jp_plain = re.sub(r'\{[^}]*\}', '', o['jp'])
        # multi-page strings with a Yes/No row are still messages (the row before a tab is kept)
        # one kana per line (the gear window's vertical slot labels) is never a message either
        menu = ('{>' in s and pages == 1) or (ml >= 3 and pages == 1 and mx < 208) or '{6}' in s or (pages == 1 and mx <= 16)
        message = not menu and (pages > 1 or ml >= 2 or (len(jp_plain) >= 6 and re.search('[。！？]$', jp_plain)) or re.match(r'[^：]{1,12}：', jp_plain) is not None)
        if message:
            W = min(max(mx, 224), 232); L = max(ml, 2)
            paging = pages > 1 or ml <= 2
            if L == 2:
                W = BOX_W
                toks, w = paginate(toks, W)
            else:
                toks, w = wrap(toks, W, L, paging)
        else:
            w = []
            for ln in s.split('{E}'):
                lt = tokens(ln)
                px = max([0] + [v for k, v in lt if k == 'tab']) + sum(text_px(v) if k == 't' else (v[1] if k == 'w' else 0) for k, v in lt)
                if px > max(mx, 16) + 16: w.append('label %dpx > %dpx' % (px, mx))
        out[i] = toks
        for x in w: warns.append((i, x))
    return out, warns

def insert(exe_in=EXE, verbose=True):
    d = bytearray(open(exe_in, 'rb').read())
    d0 = bytes(d)
    S = load_script()
    en = load_en()
    toks, warns = prepare(en, S)
    runs = [v for t in toks.values() for k, v in t if k == 't']
    dic = pick_dictionary(runs)
    tab, by_lui = ref_table(bytes(d))
    # placement
    def movable(i):
        rs = tab.get(S[i]['addr'], [])
        if not rs: return False
        for r in rs:
            if r[0] == 'code':
                lows = {q[2] for q in rs if q[0] == 'code' and q[1] == r[1]}
                if len(by_lui[r[1]]) > 1 or r[3] == 0x0d or not lui_exclusive(d, r[1], lows): return False
        return True
    def orig_words(i):
        o = S[i]
        return list(struct.unpack_from('<%dH' % (o['n'] + 1), d, o['off']))
    # strings that cannot move but do not fit get their text runs as whole dictionary entries
    for rnd in range(3):
        enc = Encoder(dic)
        words = {i: enc.encode(t) for i, t in toks.items()}
        over = [i for i, w in words.items() if len(w) > S[i]['slot']]
        stuck = [i for i in over if not movable(i)]
        add = [v for i in stuck for k, v in toks[i] if k == 't' and len(v) > 2 and v not in dic]
        if not add: break
        dic += sorted(set(add))
    stuck = [i for i in over if not movable(i)]
    moved = set(over) - set(stuck)
    # a run of neighbouring movable strings is emptied to make one block for the dictionary table
    need = 4 * len(dic)
    ids = sorted((i for i in S if i), key=lambda i: S[i]['off'])
    best = None
    for k in range(len(ids)):
        tot = 0
        for j in range(k, len(ids)):
            i = ids[j]
            if j > k and S[ids[j - 1]]['off'] + 2 * S[ids[j - 1]]['slot'] != S[i]['off']: break
            if not movable(i): break
            tot += 2 * S[i]['slot']
            if tot >= need:
                if best is None or tot < best[0]: best = (tot, ids[k:j + 1])
                break
    if best is None: raise RuntimeError('no run of movable strings for the dictionary table')
    for i in best[1]:
        moved.add(i)
        if i not in words: words[i] = orig_words(i)
    free = []
    for i, o in S.items():
        if i == 0: continue
        if i in moved: used = 0
        elif i in stuck: used = o['slot']
        elif i in words: used = len(words[i])
        else: used = o['slot']          # untranslated: leave alone
        tail = o['slot'] - used
        if tail > 0: free.append([o['off'] + 2 * used, 2 * tail])
    free.sort()
    mf = []
    for a, n in free:
        if mf and mf[-1][0] + mf[-1][1] == a: mf[-1][1] += n
        else: mf.append([a, n])
    free = mf
    def alloc(nbytes, align=2):
        best = None
        for f in free:
            a = (f[0] + align - 1) & ~(align - 1)
            if a + nbytes <= f[0] + f[1] and (best is None or f[1] < best[1]): best = f
        if best is None: return None
        a = (best[0] + align - 1) & ~(align - 1)
        free.remove(best)
        if a > best[0]: free.append([best[0], a - best[0]])
        if best[0] + best[1] > a + nbytes: free.append([a + nbytes, best[0] + best[1] - a - nbytes])
        return a
    report = dict(strings=len(words), dict_entries=len(dic), moved=len(moved), stuck=stuck,
                  free_bytes=sum(n for a, n in free))
    ptr = alloc(need, 4)
    homeless = []
    moved_at = {}
    for i in sorted(moved, key=lambda i: -len(words[i])):
        w = words[i]; a = alloc(2 * len(w), 2)
        if a is None: homeless.append(i); continue
        d[a:a + 2 * len(w)] = struct.pack('<%dH' % len(w), *w)
        moved_at[i] = a
        for r in tab[S[i]['addr']]: repoint(d, r, a + BASE)
    for k, s in enumerate(dic):
        b = s.encode('ascii') + b'\0'
        a = alloc(len(b), 1)
        if a is None: raise RuntimeError('no room for dictionary text')
        d[a:a + len(b)] = b
        struct.pack_into('<I', d, ptr + 4 * k, a + BASE)
    for i, w in words.items():
        if i in moved or i in stuck: continue
        o = S[i]
        d[o['off']:o['off'] + 2 * len(w)] = struct.pack('<%dH' % len(w), *w)
    # code that shows a postcard page by page points into the middle of the string, just after
    # each {9}: point those at the matching {9} segment of the English text
    starts_ = {o['addr']: i for i, o in S.items()}
    by_off = sorted((o['addr'], i) for i, o in S.items() if i)
    import bisect
    mids = 0
    for v, rs in tab.items():
        if v in starts_: continue
        k = bisect.bisect_right(by_off, (v, 1 << 30)) - 1
        if k < 0: continue
        a0, i = by_off[k]
        o = S[i]
        if not (a0 < v < a0 + 2 * o['slot']) or i not in words: continue
        jw = list(struct.unpack_from('<%dH' % (o['n'] + 1), d0, o['off']))
        nseg = jw[:(v - a0) // 2].count(0xfff9)
        if nseg == 0: continue
        w = words[i]
        pos = [n + 1 for n, x in enumerate(w) if x == 0xfff9]
        assert len(pos) >= nseg, (i, 'English has fewer {9} than the Japanese')
        base = (moved_at[i] if i in moved_at else o['off'])
        for r in rs: repoint(d, r, base + 2 * pos[nseg - 1] + BASE)
        mids += 1
    report['mid_refs'] = mids
    report['homeless'] = homeless
    report['free_left'] = sum(n for a, n in free)
    report['warnings'] = warns
    return d, ptr + BASE, dic, report, words

if __name__ == '__main__':
    d, ptr, dic, rep, words = insert()
    print({k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()})
    print('stuck', rep['stuck'][:40], 'homeless', rep['homeless'][:40])
    for w in rep['warnings'][:80]: print(w)
    print(dic[:60])
