"""Write the English story pages (text/story_en.txt) into the five story tilemaps in place.
The pages are raw 32x32 column-major BG maps; text tiles are 0x100+code with the page's attribute bits, and tile 0x100
(code 00) is the blank. The Japanese used rows 1-13 (kana on even rows, marks on odd rows); English gets rows 2-12
as plain single-spaced lines in cols 1-30. Rows 14+ are the picture and are left alone."""
import os, sys, textwrap
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from build_font import ENC
WIDTH, FIRST, LAST, COL0 = 30, 2, 12, 1
def load(path=os.path.join(HERE, '..', 'text', 'story_en.txt')):
    pages = []; cur = None
    for l in open(path, encoding='utf-8'):
        l = l.rstrip('\n')
        if l.startswith('## '):
            cur = [int(l.split()[1], 16), l.split(None, 2)[2], ['']]; pages.append(cur)
        elif l.startswith('#'): continue
        elif cur:
            if l.strip(): cur[2][-1] += (' ' if cur[2][-1] else '') + l.strip()
            elif cur[2][-1]: cur[2].append('')
    return [(m, t, [p for p in ps if p]) for m, t, ps in pages]
def layout(paras):
    n = LAST - FIRST + 1
    wrapped = [textwrap.wrap(p, WIDTH) for p in paras]
    gaps = [True] * (len(wrapped) - 1)
    while True:                                          # drop paragraph gaps from the top until the page fits
        rows = wrapped[0][:]
        for g, w in zip(gaps, wrapped[1:]): rows += ([''] if g else []) + w
        if len(rows) <= n: return rows
        if not any(gaps): raise ValueError('page too long: %d rows' % len(rows))
        gaps[gaps.index(True)] = False
def patch_story(r):
    out = []
    for m, title, paras in load():
        rows = layout(paras)
        W = lambda i: r[m + 2*i] | r[m + 2*i + 1] << 8
        attr = None
        for c in range(32):
            for row in range(1, 14):
                t = W(c*32 + row) & 0x3FF
                if 0x100 <= t < 0x174:
                    attr = attr if attr is not None else W(c*32 + row) & 0xFC00
        assert attr is not None, hex(m)
        def put(row, col, code):
            v = (0x100 + code) | attr; i = col*32 + row; r[m + 2*i] = v & 0xFF; r[m + 2*i + 1] = v >> 8
        for c in range(32):
            for row in range(1, 14):
                if 0x100 <= W(c*32 + row) & 0x3FF < 0x174: put(row, c, 0)
        for k, line in enumerate(rows):
            for j, ch in enumerate(line):
                if ch == '0': raise ValueError('story font has no 0 digit')
                put(FIRST + k, COL0 + j, 0 if ch == ' ' else ENC[ch])
        out.append((m, title, rows))
    return out
if __name__ == '__main__':
    for m, title, paras in load():
        print('== %06X %s' % (m, title))
        for l in layout(paras): print('  |%-30s|' % l)
