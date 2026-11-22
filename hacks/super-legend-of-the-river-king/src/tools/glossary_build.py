"""Step 2 of the glossary: write docs/glossary.csv, .xlsx and a searchable .html from out/glossary_rows.json."""
import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
rows=json.load(open(P.out('glossary_rows.json'),encoding='utf-8'))
for r in rows:
    if r['cat']=='Characters' and not r['romaji']: r['romaji']=r['en']
ORDER=['Terms','Fish','Other catch','Creatures','Bait','Hooks','Floats & sinkers','Lures','Flies','Rods','Food','Items','Places','Characters','Fishing Note: how to eat']
rows.sort(key=lambda r:ORDER.index(r['cat']))
wb=Workbook(); ws=wb.active; ws.title='Glossary'
H=['Category','Japanese','Romaji','English','Map label','Fishery label','Scientific name (reference)','Notes']
ws.append(H)
for r in rows: ws.append([r['cat'],r['jp'],r['romaji'],r['en'],r.get('map',''),r.get('fishery',''),r.get('sci',''),r.get('note','')])
hf=PatternFill('solid',fgColor='1F4E5A')
for c in ws[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=hf
for col,w in zip('ABCDEFGH',(18,22,24,28,12,14,40,70)): ws.column_dimensions[col].width=w
for row in ws.iter_rows(min_row=2):
    row[1].font=Font(name='Meiryo')
    row[7].alignment=Alignment(wrap_text=True,vertical='top')
ws.freeze_panes='B2'; ws.auto_filter.ref=ws.dimensions
n=wb.create_sheet('Read me')
for l in ["Super Legend of the River King: translation glossary (patch v1.3)","",
"Every name and term in the English patch, next to the original Japanese.",
"Japanese was read from the game's font; obvious misreads were corrected by hand. One cooking note is marked as unverified.",
"Romaji is Hepburn, with macrons only for katakana long marks (ー) and hand-written readings.",
"Map label / Fishery label: shortened forms used where the screen is narrow (9 and 13 characters).",
"Scientific names were added for reference and do not appear in the game.",
"Fish names follow common English names; Japanese names are kept where no English name exists (Itomoroko, Mugitsuku, Tamoroko, Wataka, Higai).",
"Herabuna (white crucian carp) is shortened to 'W.Crucian' wherever space is tight."]:
    n.append([l])
n.column_dimensions['A'].width=120
import os,csv
DOCS=os.path.join(os.path.dirname(P.ROOT),'docs'); os.makedirs(DOCS,exist_ok=True)
wb.save(os.path.join(DOCS,'glossary.xlsx'))
with open(os.path.join(DOCS,'glossary.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(H)
    for r in rows: w.writerow([r['cat'],r['jp'],r['romaji'],r['en'],r.get('map',''),r.get('fishery',''),r.get('sci',''),r.get('note','')])
tpl=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'glossary_page_template.html'),encoding='utf-8').read()
open(os.path.join(DOCS,'glossary.html'),'w',encoding='utf-8').write(tpl.replace('__DATA__',json.dumps(rows,ensure_ascii=False).replace('</','<\\/')))
print(len(rows))
