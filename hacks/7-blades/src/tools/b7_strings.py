"""In-game text for the JP program: which JP pointer slots get PAL English, and where the strings go.

The JP ELF keeps its menu/item/hint text as tables of string pointers. PAL has the same tables with
extra language blocks after the Japanese one (the JP ELF even has an unused dev-English block at the
same stride). For each table: JP block range, PAL Japanese block, PAL English block offset.
The JP code reads only the Japanese block, so those slots are repointed.

Strings are placed first into JP string space freed by the repointing (old Japanese text and the
unused dev-English text, never referenced by code), the rest into the new segment (gen_data.py).
"""
import struct, re, json, os

BASE = 0x200000 - 0x1000
off = lambda v: v - BASE
GP_JP = 0x4f4df0

# (jp_start, jp_end, pal_start, pal_en_delta, jp_dev_en_delta, what)
TABLES = [
    (0x4735b8, 0x4738b8, 0x494100, 0x300, 0x300, 'mission hints [char][stage][i] (ptr, flag)'),
    (0x4740c8, 0x4741b8, 0x495910, 0x2c8, 0x248, 'food names'),
    (0x474558, 0x474628, 0x4969c0, 0x14c, 0x108, 'food comments'),
    (0x474768, 0x4749e8, 0x497188, 0x29c, 0x29c, 'weapons: name + 4 lines'),
    (0x474ca0, 0x474d20, 0x498130, 0x94, 0x94, 'quick items'),
    (0x474dc8, 0x474de8, 0x4984a8, 0x20, 0x20, 'keys'),
    (0x474e08, 0x474f08, 0x498568, 0x154, 0x154, 'item-screen messages'),
]
# item-screen command menu: PAL's English block has another order (Drop, Use, Remove, Quick, Item)
MENU = {0x4750b0: 0x495834, 0x4750b4: 0x495830, 0x4750b8: 0x495838}   # Use, Drop, Remove
# PAL swapped the yes/no buttons for Europe; the JP program confirms with circle
FIX = {'×　Ｙｅｓ': '○　Ｙｅｓ', '○　Ｎｏ': '×　Ｎｏ'}
EXTRA = {0x4750bc: 'Ｑｕｉｃｋ'}
# Left in Japanese by PAL too; our own English (the project lead 2026-11-10: "if PAL didn't translate them, we can").
# Written in ASCII here, stored full-width like PAL's English. Wording follows PAL's item text (Quick = 胴乱).
fw = lambda t: ''.join(chr(ord(c) + 0xfee0) if '!' <= c <= '~' else '　' if c == ' ' else c for c in t).replace('＇', '’').replace('－', 'ー')   # eu_font's table: ' = 0x8166, - = 0x815b
EXTRA.update({
    0x4748e4: fw('Seven-Branch Cannon'),            # 七支砲 (Yuri's hidden weapon; a play on the 七支刀 sword)
    0x4748e8: fw("Don't know what it is,"),          # なんだかよくわかんないけど
    0x4748ec: fw('but it looks like one hell'),       # すごそうな大砲だよ
    0x4748f0: fw('of a cannon.'),
    0x474ca0: fw('Elixir'),                           # 金丹
    0x474ca4: fw('Keep it in Quick and it will'),     # 胴乱に入れておくと体力が
    0x474ca8: fw('restore my health when'),           # なくなった時に回復してくれるぜ
    0x474cac: fw('I run out.'),
    0x474cb0: fw('Folding fan'),                      # 扇子
    0x474cb4: fw("Guess I'll show 'em"),              # 俺様の得意の舞いでも
    0x474cb8: fw('my famous dance.'),                 # 見せるとするか
})
# inline 0x20-byte strings (tutorial button names, copied to 0x3fbebc at run time): PAL spells these out
INLINE = {0x3faeb0: ('セレクト', 'ＳＥＬＥＣＴ'), 0x3faed0: ('スタート', 'ＳＴＡＲＴ')}   # 胴乱 (quick-item pouch) label; PAL splits it into Quick / Item

isjp = lambda t: re.search('[぀-ヿ一-鿿]', t) is not None


def u32(d, va): return struct.unpack_from('<I', d, off(va))[0]
def cz(d, va): o = off(va); return d[o:d.index(b'\0', o)]


def name_slots(jp, pal):
    """Character/enemy names: JP pairs (jp, en) at 0x3f9db0, PAL quads (jp, en, fr, de) at 0x400c70,
    same 82 entries in the same order. The JP code reads the first pointer."""
    return {0x3f9db0 + 8 * k: cz(pal, u32(pal, 0x400c70 + 16 * k + 4)) for k in range(82)}


def table_slots(jp, pal):
    out = {}
    for a, b, pa, dl, _, _ in TABLES:
        for js in range(a, b, 4):
            jw = u32(jp, js)
            if not 0x4e0000 <= jw < 0x4f2000: continue
            pw = u32(pal, pa + (js - a) + dl)
            if not 0x500000 <= pw < 0x520000: continue
            en = cz(pal, pw); t = en.decode('cp932')
            if isjp(t) or en == cz(jp, jw): continue
            out[js] = FIX.get(t, t).encode('cp932')
    for js, pv in MENU.items(): out[js] = cz(pal, u32(pal, pv))
    for js, t in EXTRA.items(): out[js] = t.encode('cp932')
    return out


def english_slots(jp, pal):
    s = name_slots(jp, pal); s.update(table_slots(jp, pal)); return s


def _strings(d, lo, hi):
    pat = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]|[\x09\x0a\x20-\x7e])+\x00')
    for m in pat.finditer(d, lo, hi):
        if m.start() % 4 == 0 and re.search(rb'[\x81-\x9f\xe0-\xfc]', m.group()):
            yield m.start() + BASE, len(m.group())


def free_ranges(jp, slots):
    """String space no longer referenced once `slots` are repointed. A string is free when no code
    refers to it (lui/addiu or gp-relative) and every data pointer to it is a repointed slot or lies
    in one of the dev-English blocks the JP code never reads."""
    ph = struct.unpack_from('<I', jp, 28)[0]; _, o, va0, _, fs, _, _, _ = struct.unpack_from('<8I', jp, ph)
    words = struct.unpack_from('<%dI' % (fs // 4), jp, o)
    strs = dict(_strings(jp, off(0x4b0000), off(0x4f2000)))
    refs = {}
    for i, w in enumerate(words):
        if w in strs: refs.setdefault(w, []).append(va0 + 4 * i)
    code = set()
    for i, w in enumerate(words):
        op = w >> 26
        if op == 0xf:
            rt = (w >> 16) & 31; hi = (w & 0xffff) << 16
            for x in words[i + 1:i + 24]:
                if x >> 26 in (9, 0xd) and (x >> 21) & 31 == rt:
                    v = (hi + ((x & 0xffff) ^ 0x8000) - 0x8000) & 0xffffffff if x >> 26 == 9 else hi | (x & 0xffff)
                    code.add(v)
                    break
        elif op == 9 and (w >> 21) & 31 == 28:
            code.add((GP_JP + ((w & 0xffff) ^ 0x8000) - 0x8000) & 0xffffffff)
    dev = [(a + jd, b + jd) for a, b, _, _, jd, _ in TABLES]
    dead = lambda r: r in slots or any(x <= r < y for x, y in dev)
    free = sorted((v, n) for v, n in strs.items() if v not in code and v in refs and all(map(dead, refs[v])))
    # Merge neighbours only across zero padding that nothing points at: the gaps hold shared empty
    # strings (e.g. 0x4f0ac0, the blank line of many tables) that must stay empty.
    pointed = set(words) | code
    out = []
    for v, n in free:
        if out and out[-1][1] <= v and not any(jp[off(out[-1][1]):off(v)]) \
                and not any(x in pointed for x in range(out[-1][1], v)):
            out[-1][1] = v + n
        else: out.append([v, v + n])
    return [tuple(r) for r in out]


def allocate(jp, pal):
    """-> (placed {va: bytes}, slot_to_va {slot: va}, rest {slot: bytes} for the segment)"""
    slots = english_slots(jp, pal)
    ranges = [list(r) for r in free_ranges(jp, slots)]
    by_text = {}
    for sl, b in slots.items(): by_text.setdefault(b, []).append(sl)
    placed, where, rest = {}, {}, {}
    for b in sorted(by_text, key=len, reverse=True):
        n = len(b) + 1
        fit = [r for r in ranges if r[1] - r[0] >= n]
        if fit:
            r = min(fit, key=lambda r: r[1] - r[0])
            va = r[0]; r[0] += n
            placed[va] = b
            for sl in by_text[b]: where[sl] = va
        else:
            for sl in by_text[b]: rest[sl] = b
    return placed, where, rest, ranges


if __name__ == '__main__':
    G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    jp = open(os.path.join(G, 'rom/jp/SLPM_650.08'), 'rb').read()
    pal = open(os.path.join(G, 'rom/pal/SLES_501.09'), 'rb').read()
    s = english_slots(jp, pal)
    fr = free_ranges(jp, s)
    placed, where, rest, left = allocate(jp, pal)
    print(f'{len(s)} slots, {len(set(s.values()))} strings ({sum(len(b) + 1 for b in set(s.values()))} bytes)')
    print(f'free {sum(b - a for a, b in fr)} bytes in {len(fr)} ranges; placed {len(placed)} in place, '
          f'{len(set(rest.values()))} strings ({sum(len(b) + 1 for b in set(rest.values()))} bytes) to the segment')
