"""Build the patched disc: python3 tools/build.py out.bin"""
import sys, os, json, struct
sys.path.insert(0, 'tools')
import numpy as np
import tim
from cdsector import write_file
from engine import ENG_BASE
from font_en import compose
from insert import insert
from textfmt import load_en
EXE_LBA, COMM_LBA = 35795, 33469

def patch_font(comm, cells):
    comm = bytearray(comm)
    for k, text in enumerate(cells):
        cell = compose(text) if text.strip() else np.zeros((16, 16), int)
        p, r = divmod(ENG_BASE + k, 256)
        base = tim.parse(comm, 33312 * (p + 1))['img']['off']
        for y in range(16):
            row = base + ((r // 16) * 16 + y) * 128 + (r % 16) * 8
            for x in range(0, 16, 2):
                comm[row + x // 2] = int(cell[y, x]) | int(cell[y, x + 1]) << 4
    return bytes(comm)

def build(src, out, verbose=True):
    img = bytearray(open(src, 'rb').read())
    exe = open('files/SLPS_021.72', 'rb').read()
    comm = open('files/TIM/COMM.TIM', 'rb').read()
    S = {o['id']: o for o in json.load(open('out/script_jp.json'))}
    en = load_en()
    exe2, rep, words, cells = insert(exe, en, S)
    comm2 = patch_font(comm, cells)
    import labels
    comm2, place, _ = labels.apply(comm2, en)          # Fishing Note map labels
    exe2 = labels.patch_exe(exe2, place)
    assert len(exe2) == len(exe)
    write_file(img, EXE_LBA, exe2)
    write_file(img, COMM_LBA, comm2)
    from iso import listing
    lba = {n.split(';')[0].lstrip('/'): (l, sz) for n, l, sz in listing(src)}
    for root, _, fs in os.walk('gfx_out'):
        for f in fs:
            rel = os.path.relpath(os.path.join(root, f), 'gfx_out')
            data = open(os.path.join(root, f), 'rb').read()
            l, sz = lba[rel]; assert len(data) == sz, rel
            write_file(img, l, data)
    open(out, 'wb').write(img)
    open('build_exe.bin', 'wb').write(exe2)
    if verbose:
        print({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items()})
        for w in rep['warnings'][:40]: print('  warn', w)
        if rep['homeless']: print('  HOMELESS', rep['homeless'][:30])
        if rep['stuck']: print('  STUCK', rep['stuck'][:30])
    return rep

if __name__ == '__main__':
    build('orig.bin', sys.argv[1])
