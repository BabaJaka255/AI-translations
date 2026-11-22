"""Export the script as script/*.tsv: one row per string, Japanese next to English.
Run from src/ after tools/dump_script.py: python3 tools/export_script.py
  script/script.tsv  every dumped string (out/script.json) with its English from tools/tr_main.py DIALOGUE
  script/names.tsv   menu labels, fish guide and catch names, animals (tr_menus, fish_guide, catch_names, tr_main)
The build reads the tools/tr_*.py tables, not these files."""
import os, sys, json, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(os.path.dirname(HERE))
import tr_main, tr_menus, fish_guide, catch_names
os.makedirs('script', exist_ok=True)
def write(name, rows):
    with open('script/' + name, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(['id', 'location', 'japanese', 'english', 'limit', 'notes'])
        for r in rows: w.writerow([str(c).replace('\n', '\\n') for c in r])
    print(len(rows), 'rows -> script/' + name)
rows = []
for it in json.load(open('out/script.json', encoding='utf-8')):
    en = tr_main.DIALOGUE.get(it['jp'])
    note = '' if en is not None else 'kept in Japanese (unused, a menu template, or drawn elsewhere)'
    rows.append([it['id'], 'sector %d +%04X (file offset %06X)' % (it['sector'], it['off'] % 2048, it['off']), it['jp'],
                 en or '', '%d bytes; 24 letters x 2 lines per page' % it['size'], note])
for off, (size, en) in tr_main.FIXED.items():
    rows.append(['fixed_%06X' % off, 'file offset %06X' % off, '', en, '%d bytes' % size, 'fixed-size string'])
write('script.tsv', rows)
rows = []
for jp, en in tr_menus.LABELS.items(): rows.append(['menu', 'window templates', jp, en, 'template width', '_ = blank cell'])
for jp, en in fish_guide.FISH.items(): rows.append(['guide_fish', 'fish guide pool', jp, en, '18 letters', ''])
for jp, en in fish_guide.USES.items(): rows.append(['guide_use', 'fish guide pool', jp, en, '10 letters', ''])
for jp, en in fish_guide.LABELS.items(): rows.append(['guide_label', 'fish guide pool', jp, en, '18 letters', ''])
for jp, en in fish_guide.AREAS.items(): rows.append(['guide_area', 'fish guide pool', jp, en, '', 'used in "(Glen fish 1)"'])
for jp, en in catch_names.EXTRA.items(): rows.append(['catch_name', 'sector %d' % catch_names.SECTOR, jp, en, '', 'plus the fish guide names'])
for n, en in enumerate(tr_main.ANIMALS): rows.append(['animal_%02d' % n, 'main $C89F', '', en, '9 letters', '{B1} insert; Japanese in the ROM table'])
write('names.tsv', rows)
