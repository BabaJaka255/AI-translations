"""Export the script as script/script.tsv: one row per string, Japanese next to English.
Run from src/: python3 tools/export_script.py
Japanese is out/script_jp.json + out/script_extra.json (dumped from SLPS_015.36), English is text/en_*.txt
('id|text'), which is what tools/insert.py reads. Edit text/en_*.txt, not this file.
Messages are wrapped by the builder to the 224 px, 2-line box; menus (tabs, or 3+ short lines) are not.
{E} newline, {D} next page, {>N} tab, {7:n} name, {A}/{B}/{C:n} inserts (see docs/ENGINE_NOTES.md).
[nnnn] in the Japanese is a glyph with no known reading."""
import os, sys, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(os.path.dirname(HERE))
import insert as I
S = I.load_script(); en = I.load_en()
os.makedirs('script', exist_ok=True)
with open('script/script.tsv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['id', 'location', 'japanese', 'english', 'limit', 'notes'])
    n = 0
    for i in sorted(S):
        o = S[i]; t = en.get(i, '')
        refs = ' '.join('%s@%X' % tuple(r[:2]) for r in o['refs'][:6]) + (' ...' if len(o['refs']) > 6 else '')
        w.writerow([i, 'SLPS_015.36 +%06X (RAM %08X)%s' % (o['off'], o['addr'], ', refs ' + refs if refs else ''),
                    o['jp'], t, '224 px x 2 lines per page (relocated, so no byte limit)',
                    '' if t else 'kept as is (unused, debug or not text)'])
        n += bool(t)
print(len(S), 'rows,', n, 'translated -> script/script.tsv')
