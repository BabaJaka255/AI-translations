"""Find pointer-referenced Shift-JIS strings in the ROM (menus, item/fish names, descriptions)."""
import struct, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from textcodec import decode

def is_text(b):
    if not b: return False
    i = 0; jp = 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0x84 or 0x88 <= c <= 0x9f or 0xe0 <= c <= 0xea:
            if i + 1 >= len(b) or not (0x40 <= b[i+1] <= 0xfc) or b[i+1] == 0x7f: return False
            try: b[i:i+2].decode('cp932')
            except UnicodeDecodeError: return False
            jp += 1; i += 2
        elif 0x20 <= c < 0x7f or c in (1, 2, 3, 4, 5, 6, 0x0a, 0x0b, 0x0e, 0x0f, 0x10) or 0xa1 <= c <= 0xdf: i += 1
        else: return False
    return jp >= 1

def find(d, lo=0x08000000, hi=None, skip=((0x08330000, 0x0835A000),)):
    hi = hi or 0x08000000 + len(d)
    refs = {}
    for o in range(0, len(d) - 3, 4):
        v = struct.unpack_from('<I', d, o)[0]
        if not (lo <= v < hi) or v & 3: continue
        if any(a <= v < b for a, b in skip): continue
        refs.setdefault(v, []).append(o)
    out = {}
    for v, rs in refs.items():
        a = v - 0x08000000
        end = d.find(b'\0', a)
        if end < 0 or end - a > 400: continue
        b = d[a:end]
        if is_text(b): out[v] = (b, rs)
    return out

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    res = find(d)
    items = [{'addr': '%07X' % (v - 0x08000000), 'refs': ['%07X' % r for r in rs], 'jp': decode(b), 'en': ''}
             for v, (b, rs) in sorted(res.items())]
    json.dump(items, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print(len(items))
