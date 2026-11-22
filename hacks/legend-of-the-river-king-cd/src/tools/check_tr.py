"""Report translations that don't fit their slots.  usage: check_tr.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from encode import encode, wrap
from tr_main import DIALOGUE
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = json.load(open(os.path.join(ROOT, 'out', 'script.json')))
size = {}
for it in items: size[it['jp']] = min(size.get(it['jp'], 999), it['size'])
bad = 0; missing = [j for j in size if j not in DIALOGUE]
for jp, en in DIALOGUE.items():
    if en is None: continue
    if jp not in size: print('NOT IN DUMP', jp); continue
    b = encode(en)
    if len(b) > size[jp]:
        bad += 1; print('%3d > %3d  %s\n           %s' % (len(b), size[jp], en.replace('\n', '|'), ' | '.join(l for l, w in wrap(en))))
print(bad, 'too long;', len(missing), 'untranslated')
if '-m' in sys.argv:
    for j in missing: print('  ', size[j] - 2, j)
