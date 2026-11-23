"""Dump the Japanese script to script/*.json, keeping any English already written there.

python3 tools/extract.py
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); GAME = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from textcodec import decode
from inventory import STRINGS, TABLES
from build import load_rom

def load(name):
    p = os.path.join(GAME, 'script', name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}

def save(name, obj):
    p = os.path.join(GAME, 'script', name)
    json.dump(obj, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', p)

def main():
    rom = load_rom(); C1 = rom[0x10000:0x20000]
    old = load('strings.json'); out = {}
    for k, (a, ptrs, notes) in STRINGS.items():
        jp, _ = decode(C1, a)
        o = old.get(k, {})
        out[k] = {'addr': '$C1:%04X' % a, 'jp': jp, 'en': o.get('en', ''), 'notes': o.get('notes', notes)}
    save('strings.json', out)
    old = load('tables.json'); out = {}
    for k, (base, n, stride, cols, notes) in TABLES.items():
        o = old.get(k, {}); oe = {e['i']: e for e in o.get('entries', [])}
        ents = []
        for i in range(n):
            raw = C1[base + i * stride:base + (i + 1) * stride]
            if raw.strip(b' ') == b'': continue
            jp, _ = decode(C1, base + i * stride, base + (i + 1) * stride, stop=False)
            ents.append({'i': i, 'jp': jp.strip(' 　~'), 'en': oe.get(i, {}).get('en', '')})
        out[k] = {'base': '$C1:%04X' % base, 'stride': stride, 'columns': cols,
                  'notes': o.get('notes', notes), 'entries': ents}
    save('tables.json', out)

if __name__ == '__main__':
    main()
