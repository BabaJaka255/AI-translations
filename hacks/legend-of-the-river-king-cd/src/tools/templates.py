"""Find menu templates (BAT words using the glyph dictionary) and show them as grids.
usage: templates.py data.iso [sector_from sector_to]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from bat_tmpl import DIC
def is_glyph(w): return (w >> 12) == 7 and 0x700 <= (w & 0x7FF) < 0x800
def q(w): return (w & 0x7FF) - 0x700
def find_labels(d, lo, hi):
    """Yield (top_offset, bottom_offset, n_words, japanese) for each label segment."""
    out = []; seen = set()
    for par in (0, 1):
        p = lo + par
        while p < hi - 1:
            w = d[p] | d[p + 1] << 8
            if is_glyph(w) and q(w) % 4 == 0 and p not in seen:
                # bottom row: same column, word = top + 2
                cand = None
                for stride in range(4, 160, 2):
                    b = p + stride
                    if b + 1 < len(d) and (d[b] | d[b + 1] << 8) == w + 2: cand = stride; break
                if cand:
                    # extend the segment to the right while words are glyph tiles or short gaps
                    e = p; last = p; gaps = 0
                    while e + 1 < hi:
                        x = d[e] | d[e + 1] << 8
                        if is_glyph(x) and q(x) % 4 in (0, 1): last = e; gaps = 0
                        elif (x & 0xFFF) in (0x28F, 0x272) and gaps < 3: gaps += 1
                        else: break
                        e += 2
                    n = (last - p) // 2 + 1
                    jp = ''
                    for k in range(n):
                        x = d[p + 2 * k] | d[p + 2 * k + 1] << 8
                        if is_glyph(x): jp += DIC[q(x) // 4] if q(x) % 4 == 0 else ''
                        else: jp += '_'
                    for k in range(n): seen.add(p + 2 * k)
                    out.append((p, p + cand, n, jp))
                    p += 2 * n; continue
            p += 2
    return sorted(out)
if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    lo = int(sys.argv[2]) * 2048 if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) * 2048 if len(sys.argv) > 3 else 1478 * 2048
    for p, b, n, jp in find_labels(d, lo, hi):
        print('%06x s%03d +%3d n=%2d %s' % (p, p // 2048, b - p, n, jp))
