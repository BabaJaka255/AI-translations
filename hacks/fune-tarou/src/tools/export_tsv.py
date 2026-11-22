"""Writes script/script.tsv (tab-separated; \\n = newline, \\t = tab, \\\\ = backslash): every string and list entry with its location, limits, Japanese and English.
python3 tools/export_tsv.py   (reads script/strings.json and script/lists.json; the JSON files are the source)"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ftlib import GAME
import build

def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')

strings = json.load(open(os.path.join(GAME, 'script', 'strings.json'), encoding='utf-8'))
lists = json.load(open(os.path.join(GAME, 'script', 'lists.json'), encoding='utf-8'))
out = open(os.path.join(GAME, 'script', 'script.tsv'), 'w', encoding='utf-8', newline='')
class W:
    def writerow(self, row):
        out.write('\t'.join(row) + '\n')
w = W()
w.writerow(['id', 'location', 'limits', 'jp', 'en', 'notes'])
for e in strings['entries']:
    loc = '$C1:%04X (pointer operands at ROM %s)' % (int(e['offset'], 16) & 0xFFFF, ', '.join(e['refs']) or 'none: fixed address')
    lim = '%d bytes in place, else relocated to $E1:8000+' % e['length']
    if e['id'] == 'intro':
        lim = 'speech font, each line <= 224 px'
    w.writerow([e['id'], loc, lim, esc(e['jp']), esc(e['en']), esc(e['notes'])])
for name, L in lists.items():
    width = build.LISTS[name]['new'][3] - (1 if build.LISTS[name].get('label') else 0)
    for i, e in enumerate(L['entries']):
        loc = '%s list, entry %d (Japanese at $C1:%04X, stride %d)' % (name, i, int(L['base'], 16) + i * L['stride'] & 0xFFFF, L['stride'])
        w.writerow([e['id'], loc, '%d columns' % width, esc(e['jp']), esc(e['en']), esc(e['notes'])])
out.close()
print('wrote script/script.tsv')
