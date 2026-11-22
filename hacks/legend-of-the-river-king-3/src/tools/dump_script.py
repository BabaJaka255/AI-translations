"""Dump all script strings to out/script.json: unique Japanese strings with their locations."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from k5lib import Rom
from script import parse
from textcodec import decode

def dump(rom_path, out_path):
    r = Rom(rom_path)
    ps = r.script_ptrs()[:284]
    entries = {}; order = []
    for i, p in enumerate(ps):
        size, ins = parse(r.decompress(p))
        for off, op, raw, t in ins:
            if t is None: continue
            jp = decode(t)
            if jp not in entries:
                entries[jp] = {'jp': jp, 'en': '', 'where': []}; order.append(jp)
            entries[jp]['where'].append('%03d:%04X:%02X' % (i, off, op))
    json.dump([entries[k] for k in order], open(out_path, 'w'), ensure_ascii=False, indent=1)
    return len(order)

if __name__ == '__main__':
    print(dump(sys.argv[1], sys.argv[2]))
