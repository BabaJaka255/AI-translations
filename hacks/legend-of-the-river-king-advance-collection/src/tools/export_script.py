"""Export the script as script/kawa3.tsv and script/kawa4.tsv: one row per string, Japanese next to English.
Run from src/: python3 tools/export_script.py
Japanese comes from tools/g3_jp.json / g4_jp.json (the dump), English from tools/tr_g3_*.py / tr_g4_*.py (dicts
keyed by ROM offset), which is what tools/insert.py reads. This file is not read by the build.
Text is word-wrapped by the build at 128 px per line (136 px for the Uocchi help), 2 lines per box page.
{fa}{fb f0}{f2} is a page break; other {..} are control codes (see docs/ENGINE_NOTES.md)."""
import os, sys, json, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)
def load_T(game):          # same as insert.load_T, without importing the ROM-reading modules
    T = {}
    for n in (('tr_g4_a', 'tr_g4_b', 'tr_g4_c') if game == 'g4' else ('tr_g3_a', 'tr_g3_b')):
        T.update(__import__(n).T)
    return T
os.makedirs('../script', exist_ok=True)
for game, name in (('g3', 'kawa3'), ('g4', 'kawa4')):
    J = json.load(open('%s_jp.json' % game, encoding='utf-8')); T = load_T(game)
    rows, seen = [], set()
    for e in J:
        a = e['addr']; seen.add(a); en = T.get(a)
        rows.append(['%s_%05x' % (game, a), 'ROM %06X-%06X, pointers at %s' % (a, e['end'], ' '.join('%06X' % r for r in e['refs'])),
                     e['jp'], en if en is not None else '', '128 px x 2 lines per page',
                     '' if en is not None else 'not in the translation tables (debug text, graphics label or unused)'])
    for a in sorted(set(T) - seen):
        rows.append(['%s_%05x' % (game, a), 'ROM %06X' % a, '', T[a], '128 px x 2 lines per page', 'string not in the dump'])
    with open('../script/%s.tsv' % name, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(['id', 'location', 'japanese', 'english', 'limit', 'notes'])
        for r in rows: w.writerow([str(c).replace('\n', '\\n') for c in r])
    print(len(rows), 'rows,', sum(1 for r in rows if r[3]), 'translated -> script/%s.tsv' % name)
