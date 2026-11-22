"""Level data carried in the movies: give each stage archive the same English image swaps as PEACE.NCB.

66 movies carry the next stage's files in PES 0xBD (b7_remux). Each of those archives (same NCB format,
header 0x1800) holds its own copies of effect.r, Geffect.r, Gover.r, Gparam.r and item.r, byte-identical
to the PEACE.NCB ones, and the game uses these copies during the stage (HUD panel, item screen, game over).
Any member byte-identical to a JP PEACE.NCB member is replaced with the rebuilt PEACE member.

usage: b7_stagedata.py jp.iso new_PEACE.NCB outdir   -> outdir/<MOVIE_path>.PSS + map.json
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b7_peace, b7_remux

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def swaps(jp_peace, new_peace):
    """{original member bytes: replacement bytes} for every member the new PEACE.NCB changed"""
    A = {n: jp_peace[o:o + s] for n, o, s in b7_peace.ncb_list(jp_peace)}
    B = {n: new_peace[o:o + s] for n, o, s in b7_peace.ncb_list(new_peace)}
    return {A[n]: B[n] for n in A if A[n] != B[n]}


def patch_stream(data, sw):
    if len(data) < 0x800: return None, []
    L = b7_peace.ncb_list(data)
    if not L: return None, []
    items = []; changed = []
    for n, o, s in L:
        b = data[o:o + s]
        if b in sw: b = sw[b]; changed.append(n)
        items.append((n, b))
    if not changed: return None, []
    return b7_peace.ncb_build(items, L[0][1]), changed


def main(iso, peace_new, outdir):
    sys.path.insert(0, os.path.join(G, 'toolkit'))
    from rhtk import ps2
    jp_peace = open(os.path.join(G, 'rom/jp/EFF/PEACE.NCB'), 'rb').read()
    sw = swaps(jp_peace, open(peace_new, 'rb').read())
    os.makedirs(outdir, exist_ok=True); out = {}
    I = ps2.Iso(iso)
    names = [l.strip() for l in open(os.path.join(G, 'rom/jp/FILES.TXT'), encoding='ascii') if l.strip().upper().endswith('.PSS')]
    for nm in names:
        path = '/' + nm.replace(chr(92), '/')
        pss = I.read_file(path)
        data = b7_remux.extract(pss)
        new, changed = patch_stream(data, sw)
        if new is None: continue
        res = b7_remux.remux(pss, new)
        assert len(res) == len(pss), (path, len(pss), len(res))
        fn = os.path.join(outdir, path.strip('/').replace('/', '_'))
        open(fn, 'wb').write(res); out[path] = {'file': fn, 'members': changed}
        print(path, ', '.join(changed))
    json.dump(out, open(os.path.join(outdir, 'map.json'), 'w'), indent=1)
    return out


if __name__ == '__main__':
    main(*sys.argv[1:4])
