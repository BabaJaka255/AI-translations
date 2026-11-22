"""Export the script as script/script.tsv: one row per string, Japanese next to English.
Run from src/: python3 tools/export_script.py
Rows come from out/script.json (the inventory). English comes from the files the build reads:
text/signs_en.txt, text/story_en.txt and the tables in tools/insert_menus.py. Story pages were rewrapped as a whole,
so each page is one row (Japanese rows joined). The build does not read this file; edit the sources above."""
import os, sys, json, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import insert_signs, insert_story, insert_menus as M
os.chdir(os.path.dirname(HERE))
S = json.load(open('out/script.json', encoding='utf-8'))
signs = insert_signs.load(); pages = {m: (t, ps) for m, t, ps in insert_story.load()}
MENU = {'menu_name_01': 'Enter your name', 'menu_date_01': 'Enter the date', 'menu_date_02': '/', 'menu_date_03': '/',
        'menu_date_04': '(blank)', 'menu_records_04': 'Cm (kept)', 'menu_records_05': '/', 'menu_records_06': '/',
        'menu_records_07': '(blank)', 'menu_records_11': '(blank)', 'menu_records_12': '% (kept)', 'menu_title_01': 'START', 'menu_file_01': 'Start', 'menu_file_02': 'Erase Data', 'menu_file_03': 'Name',
        'menu_file_04': 'Fishing', 'menu_file_05': 'Walking', 'menu_records_01': 'Angler', 'menu_records_02': 'Size',
        'menu_records_03': 'Date', 'menu_records_08': 'Angler', 'menu_records_09': 'Got', 'menu_records_10': 'Success',
        'menu_confirm_01': 'Are you sure?', 'menu_confirm_02': 'Yes', 'menu_confirm_03': 'No',
        'menu_kbd_01': 'English keyboard: ' + ' '.join(M.KEYS), 'menu_kbd_02': 'End',
        'menu_title_02': '© 1994 PACK-IN-VIDEO', 'spr_backup': ' / '.join(t for _, t in M.BACKUP_LINES),
        'spr_hud_power': 'Fish', 'spr_hud_walk': 'Walk', 'logo': '(kept in Japanese)'}
rows, done = [], set()
for x in S:
    i, en, loc = x['id'], MENU.get(x['id'], ''), x['rom']
    if i.startswith('spot'):
        n, l = int(i[4:6]), int(i.split('_l')[1]); en = signs[n - 1][l - 1]
    elif i.startswith('story_'):
        m = int(i.split('_')[1], 16)
        if m in done: continue
        done.add(m); title, ps = pages[m]
        jp = '\n'.join(y['jp'] for y in S if y['id'].startswith('story_%06X_' % m) and y['jp'].strip())
        rows.append(['story_%06X' % m, '%06X' % m, jp, '\n\n'.join(ps), '30 cols x 11 rows (rows 2-12)', title + ' page. ' + x['notes']])
        continue
    elif i.startswith('fishhdr_'):
        en = M.FISH_ORDER[int(i[-2:]) - 1]
    elif i.startswith('fishlist_'):
        en = M.FISH_EN[x['jp']]
    rows.append([i, loc, x['jp'], en, x['limit'], x['notes']])
os.makedirs('script', exist_ok=True)
with open('script/script.tsv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['id', 'rom_offset', 'japanese', 'english', 'limit', 'notes'])
    for r in rows: w.writerow([c.replace('\n', '\\n') for c in map(str, r)])
print(len(rows), 'rows -> script/script.tsv')
