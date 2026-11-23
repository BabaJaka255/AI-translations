"""Static overflow check: for each string drawn by a msg() call (0x80018ab8) with constant x, find the
window boxes (0x80018984: a1 x, a2 y, a3 w, [sp+0x10] h) opened in the same function and report lines
whose right edge passes the box's inner edge. python3 tools/fitcheck.py"""
import sys, json, struct; sys.path.insert(0, 'tools')
from insert import layout, Metrics, tokens
from textfmt import load_en
from refs import refs
EXE = open('build_exe.bin', 'rb').read()
BASE = 0x80010000 - 0x800
def ins(a): return struct.unpack_from('<I', EXE, a - BASE)[0]
def imm_load(a, reg):
    """value of 'addiu/ori reg, zero, imm' at a, else None"""
    w = ins(a); op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; im = w & 0xffff
    if rt == reg and rs == 0 and op in (0x09, 0x0d): return im - 0x10000 if (op == 9 and im & 0x8000) else im
    if op == 0 and (w & 0x3f) == 0x21 and ((w >> 11) & 31) == reg and rs == 0 and rt == 0: return 0
    return None
def find_args(call, regs, back=24):
    out = {}
    for a in range(call + 4, call - back * 4, -4):     # include delay slot
        for r in regs:
            if r in out: continue
            v = imm_load(a, r)
            if v is not None: out[r] = v
            else:
                w = ins(a); dst = None; op = w >> 26
                if op == 0: dst = (w >> 11) & 31
                elif op in (8, 9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x20, 0x21, 0x23, 0x24, 0x25): dst = (w >> 16) & 31
                if dst == r and a != call + 4: out[r] = None
    return out
def func_bounds(a):
    lo = a
    while lo > 0x80010000:
        w = ins(lo)
        if w >> 16 == 0x27bd and w & 0x8000: break      # addiu sp, sp, -n
        lo -= 4
    hi = a
    while ins(hi) != 0x03e00008: hi += 4                 # jr ra
    return lo, hi
def boxes(lo, hi):
    bx = []
    for a in range(lo, hi, 4):
        if ins(a) == 0x0c000000 | (0x80018984 >> 2 & 0x3ffffff):
            ar = find_args(a, (5, 6, 7))
            # [sp+0x10] h: look for sw $v0,0x10($sp) after addiu v0
            if None not in (ar.get(5), ar.get(7)) and 5 in ar and 7 in ar: bx.append((a, ar[5], ar.get(6), ar[7]))
    return bx
def line_widths(toks, M):
    ws = []; x = 0; x0 = 0
    for t in toks:
        if t in (('c', [0xfffe]), ('c', [0xfffd])): ws.append(x); x = 0; continue
        if t[0] == 'tab': x = t[1]; continue
        x += M.tok(t)
    ws.append(x); return ws
if __name__ == '__main__':
    S = {o['id']: o for o in json.load(open('out/script_jp.json'))}
    en = load_en(); M = Metrics()
    by_addr = {int(o['addr'], 16): o for o in S.values()}
    JAL_MSG = 0x0c000000 | (0x80018ab8 >> 2 & 0x3ffffff)
    n = 0
    for i in sorted(en):
        o = S.get(i)
        if not o: continue
        toks, _ = layout(en[i], o['words'], M)
        ws = line_widths(toks, M)
        for r in o['refs']:
            if r['kind'] != 'code': continue
            at = int(r['at2'], 16)
            call = next((a for a in range(at, at + 40, 4) if ins(a) == JAL_MSG), None)
            if call is None: continue
            ar = find_args(call, (5,))
            x = ar.get(5)
            if x is None: continue
            lo, hi = func_bounds(call)
            bx = [b for b in boxes(lo, hi) if b[1] <= x < b[1] + b[3]]
            if not bx: continue
            right = min(b[1] + b[3] for b in bx) - 6
            over = [w for w in ws if x + w > right]
            if over:
                n += 1
                print('%d @%s x=%d box_right=%d widest=%d  over by %d | %s' % (i, hex(call), x, right + 6, max(ws), x + max(ws) - right, en[i][:70]))
    print(n, 'possible overflows')
