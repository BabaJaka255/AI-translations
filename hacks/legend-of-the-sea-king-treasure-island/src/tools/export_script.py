"""Export the script as script/script.tsv: one row per string, Japanese next to English.
Run from src/: python3 tools/export_script.py
Japanese is out/script_jp.json (dumped from SLPS_021.72 by tools/dump.py), English is text/en_*.txt ('id|text'),
which is what tools/build.py reads. Edit text/en_*.txt, not this file.
Messages are wrapped by the inserter to the 224 px box (2 lines per page); menus and labels keep the Japanese
geometry (tools/insert.py layout()). {E} newline, {D} next page, {>N} tab, {7:n} name, {A}/{B}/{C:n} inserts
(see docs/ENGINE_NOTES.md)."""
import os, sys, csv, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(os.path.dirname(HERE))
from textfmt import load_en
from insert import is_message
S = {o['id']: o for o in json.load(open('out/script_jp.json'))}
en = load_en()
os.makedirs('script', exist_ok=True)
with open('script/script.tsv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['id', 'location', 'japanese', 'english', 'limit', 'notes'])
    n = 0
    for i in sorted(S):
        o = S[i]; t = en.get(i, '')
        refs = ' '.join('%s@%s' % (r['kind'], r.get('at2') or r.get('at') or '?') for r in o['refs'][:4]) + (' ...' if len(o['refs']) > 4 else '')
        loc = 'SLPS_021.72 RAM %s (%d words)' % (o['addr'], o['n']) + ('; refs ' + refs if refs else '; no reference found')
        if not t: lim = ''
        elif is_message(o['words'], t): lim = 'message box: 224 px per line, 2 lines per page (relocated, no byte limit)'
        else: lim = 'menu/label: Japanese line widths and line count'
        note = ''
        if not t: note = 'not translated: no code or data reference (dead text), or not text'
        elif o['unref']: note = 'unreferenced in the original; written in place'
        w.writerow([i, loc, o['jp'], t, lim, note]); n += bool(t)
print(len(S), 'rows,', n, 'translated -> script/script.tsv')
