"""Export the script as script/*.tsv: one row per string, Japanese next to English.
Run from src/ after analysis/dump_script.py: python3 analysis/export_script.py   (needs the ROM, see build/paths.py)
  script/script.tsv  the main script (out/script.json + build/translations.py)
  script/names.tsv   item and bait names from the bank $86 tables (build/tr_names.py NAMES86)
  script/fish.tsv    the 113 fish records: name, alias, description, cooking (out/fish.json + tr_names.FISH)
The build reads build/tr_*.py, not these files. Limits are what build_patch.py checks."""
import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),"..","build")); import paths as P
import json, csv, os
from umilib import *
import translations as T, tr_names, fishdata, name_entry, board, content_page, rank_board, cs_panel
rom=open(ROMPATH,'rb').read(); single=load_single(); kanji=load_kanji()
S=json.load(open(P.out('script.json'),encoding='utf-8'))
F=json.load(open(P.out('fish.json'),encoding='utf-8'))
os.makedirs(os.path.join(P.ROOT,'script'),exist_ok=True)
def write(name,head,rows):
    with open(os.path.join(P.ROOT,'script',name),'w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(head)
        for r in rows: w.writerow([str(c).replace('\n','\\n') for c in r])
    print(len(rows),'rows ->','script/'+name)
# strings drawn by special-case code in build_patch.py rather than through translations.EN
SPECIAL={3:' | '.join(cs_panel.SEGS.values()),13:'Qty BestRateUsesInfo',14:content_page.TEXT,22:rank_board.TEXT}
SPECIAL.update({4+k:n+' (default name)' for k,n in enumerate(name_entry.DEFAULT_NAMES)})
SPECIAL.update(name_entry.DISPLAY); SPECIAL.update(board.DISPLAY)
rows=[]
for e in S:
    i=e['id']; jw,jl=jp_width(bytes.fromhex(e['raw']))
    cols,nl=T.limits(i,jw,jl)
    lim='%d cols'%cols+(', %d lines'%nl if nl else ', pages')
    note='also used by #'+','.join(map(str,e['aliases'])) if e['aliases'] else ''
    en=T.EN.get(i,SPECIAL.get(i,''))
    if not en: note=(note+'; ' if note else '')+'not translated as text: a name insert code, the Yes/No graphic or an unused string'
    rows.append([i,'%s (ROM %s)'%(e['snes'],e['rom']),e['jp'],en,lim,note])
write('script.tsv',['id','location','japanese','english','limit','notes'],rows)
rows=[]
for ptr,en in sorted(tr_names.NAMES86.items()):
    r=p2r(ptr); rows.append(['86:%04X'%ptr,'ROM %06X'%r,decode(rom,r,strend(rom,r),single,kanji),en,'18 letters',''])
write('names.tsv',['id','location','japanese','english','limit','notes'],rows)
rows=[]
for x in F:
    n=x['n']; name,alias,cook=tr_names.FISH.get(n,('','',''))
    desc=tr_names.FISH_DESC.get(n,'')
    for k,(part,en,lim) in enumerate([('name',name,'18 letters'),('alias',alias or '','18 letters'),
                                      ('desc',desc,'22 letters, then 28; 4 lines (wrapped by the build)'),
                                      ('cook',cook,'20 letters')]):
        rows.append(['fish%03d_%s'%(n,part),'record ROM %06X'%x['rec'],x['jp'][k],en,lim,''])
write('fish.tsv',['id','location','japanese','english','limit','notes'],rows)
