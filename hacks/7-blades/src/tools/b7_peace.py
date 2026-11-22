"""EFF/PEACE.NCB (menus, item/save/load screens, title, game over): swap Japanese graphics for PAL English.

NCB: u32 count, then 32-byte entries (name[24], offset, size); data 0x800-aligned.
Each .r member is "1.\\." LZ around an inner archive: 32-byte entries (name[0x18], size, offset),
count = first offset / 32, then an empty entry whose offset is the total size. Inner members are
"1\\0\\0\\0" + BE size + LZ tokens (or raw).

PAL keeps its English images as extra members named <jp>_u.rh2 (or _e) in the same .r, or in a
separate <name>_e.r. The JP program opens the Japanese names, so their data is replaced in place
and the code is left alone. A swap is taken only when the decoded rh2 header (format, size, VRAM
placement) matches the Japanese one.
"""
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b7_lz


def ncb_list(d):
    out = []
    for k in range(struct.unpack_from('<I', d)[0]):
        i = 4 + 32 * k; name = d[i:i + 24].split(b'\0')[0]
        o, n = struct.unpack_from('<II', d, i + 24); out.append((name.decode(), o, n))
    return out


def ncb_build(items, hsize=0x800):
    """items: [(name, bytes)] -> NCB bytes (header padded to hsize)"""
    hdr = bytearray(struct.pack('<I', len(items))); body = bytearray(); pos = hsize
    assert 4 + 32 * len(items) <= hsize
    for name, b in items:
        hdr += name.encode().ljust(24, b'\0') + struct.pack('<II', pos, len(b))
        pad = -len(b) % 0x800; body += b + bytes(pad); pos += len(b) + pad
    return bytes(hdr.ljust(hsize, b'\0') + body)


def r_unpack(z):
    d = b7_lz.decompress(z) if z[:4] == b'1.\\.' else z
    n = struct.unpack_from('<I', d, 0x1c)[0] // 32
    ents = []
    for k in range(n):
        e = d[32 * k:32 * k + 32]; name = e[:0x18].split(b'\0')[0].decode()
        sz, o = struct.unpack_from('<II', e, 0x18)
        if not name: break
        ents.append((name, sz, o))
    offs = sorted(o for _, _, o in ents) + [len(d)]
    return [(nm, sz, d[o:offs[offs.index(o) + 1]]) for nm, sz, o in ents]


def tighten(raw):
    """re-pack an LZ'd member with the optimal-parse compressor when that is smaller (same decoded bytes);
    rebuilt archives then stay within the room the originals had (movie streams must not grow)."""
    if raw[:4] != b'1\0\0\0': return raw
    c = b'1\0\0\0' + b7_lz.compress(member_dec(raw))[4:]
    return c if len(c) < len(raw) else raw


def r_pack(members):
    """members: [(name, size, raw)] -> compressed .r"""
    n = len(members) + 1; pos = 32 * n; hdr = bytearray(); body = bytearray()
    for nm, sz, raw in members:
        hdr += nm.encode().ljust(0x18, b'\0') + struct.pack('<II', sz, pos); body += raw; pos += len(raw)
    hdr += bytes(0x18) + struct.pack('<II', 0, pos)
    return b7_lz.compress(bytes(hdr + body))


def member_dec(raw):
    return b7_lz.decompress(b'1.\\.' + raw[4:]) if raw[:4] == b'1\0\0\0' else raw


# Swaps the JP code cannot use as-is (none left: the options sheets FONT1-3_u are cut by my_optspr)
EXCLUDE = set()


# PAL images the JP archives lack, added for code ported from PAL (status captions: my_status_draw)
ADD = {'load.r': [('font3.rh2', 'load_e.r', 'font3_u.rh2')], 'item.r': [('font3.rh2', 'load_e.r', 'font3_u.rh2')],   # options: PAL's third sheet (my_optload*)
       'effect.r': ['kai_e.rh2', 'ki_e.rh2', 'kin_e.rh2', 'con_e.rh2', 'kana_e.rh2', 'gen_e.rh2', 'gou_e.rh2',
                    'conra_e.rh2', 'jyaku_e.rh2', 'hiri_e.rh2', 'fudo_e.rh2']}


# JP members whose PAL English counterpart has another name: kill counter digits + label; save/load map
# location labels (PAL lays them out horizontally: the label table at JP 0x46ac80 comes from PAL too,
# see b7_build_jp.py 'save')
RENAME = {('effect.r', 'girisuji.rh2'): ('effect.r', 'giri_u.rh2')}
for _a in ('load.r', 'save.r'):
    for _i in '123':
        RENAME[(_a, 'mapfont%s.rh2' % _i)] = ('load_e.r', 'mapft%s_u.rh2' % _i)


# PAL's button prompts follow the European layout (cross = confirm, circle = back). The JP program
# confirms with circle, so the icons are swapped in the PAL images: (pal archive, member) ->
# [(x, y) of the cross, (x, y) of the circle] (top left of an 18x18 cell holding the icon and its
# outline), circle None = no circle in that image, take it from load2_u.
BUTTON_SWAP = {('load_e.r', 'mapft3_u.rh2'): [(3, 211), (3, 235)],   # map: Decision / Return
               ('load_e.r', 'load2_u.rh2'): [(123, 52), (123, 76)],  # load: Start / Return
               ('load_e.r', 'chk_u.rh2'): [(321, 291), None]}        # "To start the game press the X button"


def jp_buttons(pa, pn, x, P):
    """swap the cross/circle icons in a PAL image (decoded rh2 bytes) -> new rh2 bytes"""
    import b7_rh2edit as E, numpy as np
    (cx, cy), circ = BUTTON_SWAP[(pa, pn)]
    idx, pal = E.get(x); idx = idx.copy(); S = 18
    if circ:
        ox, oy = circ
        a = idx[cy:cy + S, cx:cx + S].copy(); idx[cy:cy + S, cx:cx + S] = idx[oy:oy + S, ox:ox + S]; idx[oy:oy + S, ox:ox + S] = a
        return E.put(x, idx)
    # no circle here: copy load2_u's, mapping its colours onto this palette. This palette has no red,
    # so a duplicate white entry (same colour as entry 2) gives its slot to the red.
    src = member_dec(next(m[2] for m in P['load_e.r'] if m[0] == 'load2_u.rh2'))
    sidx, spal = E.get(src); sx, sy = BUTTON_SWAP[('load_e.r', 'load2_u.rh2')][1]
    red = spal[1]; assert red[0] > 150 and red[1] < 80
    free = next(i for i in range(1, len(pal)) if (pal[i] == pal[2]).all() and i != 2)
    idx[idx == free] = 2; pal = pal.copy(); pal[free] = red
    x = _set_clut16(x, free, _clut16_raw(src, 1))
    blk = sidx[sy:sy + S, sx:sx + S]
    lut = np.array([int(np.argmin(((pal - c) ** 2).sum(1))) for c in spal], np.uint8)
    idx[cy:cy + S, cx:cx + S] = lut[blk]
    return E.put(x, idx)


def _clut16_raw(x, i):
    import b7_rh2edit as E
    reg, o, n = E._uploads(x)[0]; assert (reg[0x50] >> 56) & 63 == 2 and n >= 32
    return x[o + 2 * i:o + 2 * i + 2]


def _set_clut16(x, i, v):
    import b7_rh2edit as E
    reg, o, n = E._uploads(x)[0]; assert (reg[0x50] >> 56) & 63 == 2 and n >= 32
    return x[:o + 2 * i] + v + x[o + 2 * i + 2:]


def rh2_sig(b):
    return b[:0x30]


def plan(jp_ncb, pal_ncb):
    """-> {archive: {jp_member: (pal_archive, pal_member)}}, skipped [(archive, member, pal, why)]"""
    J = {n: r_unpack(jp_ncb[o:o + s]) for n, o, s in ncb_list(jp_ncb) if n.endswith('.r')}
    P = {n: r_unpack(pal_ncb[o:o + s]) for n, o, s in ncb_list(pal_ncb) if n.endswith('.r')}
    out = {}; skipped = []
    for a, mem in J.items():
        jnames = {m[0].lower() for m in mem}
        cands = {}
        for pa in (a, a[:-2] + '_e.r'):
            for nm, sz, raw in P.get(pa, []): cands[nm.lower()] = (pa, nm, sz, raw)
        for nm, sz, raw in mem:
            stem = nm[:-4].lower()
            if (a, nm) in RENAME:
                ra, rn = RENAME[(a, nm)]
                c = next((ra, m[0], m[1], m[2]) for m in P[ra] if m[0].lower() == rn)
                if rh2_sig(member_dec(raw)) == rh2_sig(member_dec(c[3])) and c[2] == sz:
                    out.setdefault(a, {})[nm] = (c[0], c[1])
                else:
                    skipped.append((a, nm, c[1], 'header differs'))
                continue
            for suf in ('_u', '_e'):
                c = cands.get(stem + suf + '.rh2')
                if c and c[1].lower() not in jnames: break
            else:
                continue
            pa, pn, psz, praw = c
            if (a, nm) in EXCLUDE:
                skipped.append((a, nm, pn, 'layout differs (options screen)')); continue
            if rh2_sig(member_dec(raw)) != rh2_sig(member_dec(praw)) or psz != sz:
                skipped.append((a, nm, pn, 'header differs')); continue
            out.setdefault(a, {})[nm] = (pa, pn)
    return out, skipped, J, P


def build(jp_ncb, pal_ncb):
    pl, skipped, J, P = plan(jp_ncb, pal_ncb)
    items = []
    for n, o, s in ncb_list(jp_ncb):
        b = jp_ncb[o:o + s]
        if n in pl or n in ADD:
            src = {(pa, m[0]): m for pa in P for m in P[pa]}
            sw = pl.get(n, {})
            mem = [(nm, sz, src[sw[nm]][2]) if nm in sw else (nm, sz, raw) for nm, sz, raw in J[n]]
            mem = [(nm, sz, b'1\0\0\0' + b7_lz.compress(jp_buttons(*sw[nm], member_dec(raw), P))[4:])
                   if sw.get(nm) in BUTTON_SWAP else (nm, sz, raw) for nm, sz, raw in mem]
            mem += [(a[0], src[(a[1], a[2])][1], src[(a[1], a[2])][2]) if isinstance(a, tuple) else src[(n, a)] for a in ADD.get(n, [])]
            b = r_pack([(nm, sz, tighten(raw)) for nm, sz, raw in mem])
        items.append((n, b))
    return ncb_build(items), pl, skipped


if __name__ == '__main__':
    G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    jp = open(os.path.join(G, 'rom/jp/EFF/PEACE.NCB'), 'rb').read()
    pal = open(os.path.join(G, 'rom/pal/EFF/PEACE.NCB'), 'rb').read()
    pl, sk, J, P = plan(jp, pal)
    for a in pl:
        print(a, ', '.join(f'{k}<-{v[1]}' for k, v in pl[a].items()))
    for s in sk: print('skip', s)
    if len(sys.argv) > 1:
        out, _, _ = build(jp, pal)
        open(sys.argv[1], 'wb').write(out)
        print(f'{len(jp)} -> {len(out)} bytes')
