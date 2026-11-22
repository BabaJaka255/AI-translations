"""Export the script as script/dialogue.tsv and script/ui.tsv: one row per string, Japanese next to English.
Run from src/ after tools/wrap_script.py: python3 tools/export_script.py
  dialogue.tsv  out/script.json: the Japanese, the wrapped English as inserted, and every place it is used
                ('block:offset:op' in the 284 script blocks). Edit text/script_en_*.txt, not this file.
  ui.tsv        text/ui_en.txt joined with out/ui_jp.json (menus, items, fish, Fishing Note, staff roll).
Box: 36 half-width columns, 3 lines per page. [xx] are control codes, see docs/ENGINE_NOTES.md."""
import os, json, csv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
os.makedirs('script', exist_ok=True)
def write(name, rows):
    with open('script/' + name, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(['id', 'location', 'japanese', 'english', 'limit', 'notes'])
        for r in rows: w.writerow([str(c).replace('\n', '\\n') for c in r])
    print(len(rows), 'rows,', sum(1 for r in rows if r[3]), 'translated -> script/' + name)
S = json.load(open('out/script.json', encoding='utf-8'))
write('dialogue.tsv', [['d%04d' % i, ' '.join(e['where']), e['jp'], e['en'], '36 cols x 3 lines per page', '']
                       for i, e in enumerate(S)])
UI = json.load(open('out/ui_jp.json', encoding='utf-8')); rows = []
for line in open('text/ui_en.txt', encoding='utf-8'):
    line = line.rstrip('\n')
    if not line or line.startswith('#'): continue
    i, t = line.split('\t', 1)
    if i.startswith('@'):
        rows.append(['ui_' + i[1:], 'ROM %s (pointers found by scanning)' % i[1:], '', t, 'its window (repointed, so no byte limit; not checked by the build)', 'not in the UI dump'])
    else:
        e = UI[int(i)]
        rows.append(['ui%03d' % int(i), 'ROM %s, pointers at %s' % (e['addr'], ' '.join(e['refs'])), e['jp'], t, 'its window (repointed, so no byte limit; not checked by the build)', ''])
write('ui.tsv', rows)
