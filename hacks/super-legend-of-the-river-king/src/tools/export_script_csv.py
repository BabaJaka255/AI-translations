"""Write the script as plain, diff-friendly files in src/script/ (UTF-8):

  strings.csv / strings.json   the 526 main-script strings: id, location, Japanese, English, limits, notes
  names.csv                    fish, gear, item and creature names (+ cooking notes), with width limits
  fish_notes.csv               the Fishing Note description for each fish

These are generated from the build sources (translations.py, tr_batch2/3.py, zones_en.py, fish_desc_en.py,
user_edits.py). To change the text, edit the workbook with build/script_io.py (see BUILD.md) or the
.py sources, then rerun this script so the CSVs stay in step.

    python3 tools/export_script_csv.py"""
import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import os, csv, json, struct
import script_io as SI
from knt2lib import load_single, load_kanji, decode

OUTDIR=os.path.join(P.ROOT,'script')
EN,Z,FD,FS,MS=SI.current()
script=json.load(open(P.b('script.json'),encoding='utf-8'))
rom=open(P.ROM,'rb').read(); single=load_single(); kanji=load_kanji()

def box(i):
    if i in SI.POSTCARD: return 'postcard/letter','28','5'
    if i in (289,297): return 'wide window','32',''
    if i==53: return 'Fishing Note contents','48 (8 fixed slots)','1'
    if i in SI.FIXED: return 'fixed columns','see note','1'
    if i in (6,7,8,9): return 'default name','8','1'
    return 'dialogue','23',''

UNTR={3:'Character-select relation labels; removed by cs_names.py instead of translated.',
 **{i:'Name-entry kana/kanji palette; replaced by the English keyboard (name_entry.py).' for i in (10,11,13,14,15,16)},
 **{i:'Contains only an insert code; nothing to translate.' for i in range(136,145)}}
rows=[]
for e in script:
    i=e['id']; kind,width,lines=box(i)
    en=EN.get(i,'')
    rows.append({'id':i,'snes':e['snes'],'rom':e['rom'],'aliases':' '.join(map(str,e['aliases'])),
                 'box':kind,'max_cols':width,'max_lines':lines,'jp':e['jp'],'en':en,
                 'translated':'yes' if en else 'no','note':SI.NOTES.get(i,'') or UNTR.get(i,'')})
H=list(rows[0])
with open(os.path.join(OUTDIR,'strings.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,H); w.writeheader(); w.writerows(rows)
json.dump(rows,open(os.path.join(OUTDIR,'strings.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

fishnames=SI.fish_record_names()
nrows=[]
for zn,jp in SI.used_names():
    if jp not in Z: continue
    kind=SI.ZONE_LABEL[zn]
    if zn=='fish' and jp not in fishnames: kind='How to eat'
    en=Z[jp]
    nrows.append({'kind':kind,'jp':jp,'en':en,'max_len':SI.ZONE_LIMIT.get(zn,16),
                  'fishery_short':FS.get(en,'') if kind=='Fish' else '','map_short':MS.get(en,'') if kind=='Fish' else ''})
with open(os.path.join(OUTDIR,'names.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,list(nrows[0])); w.writeheader(); w.writerows(nrows)

frows=[]
for i in sorted(FD):
    o=0x28018+i*23
    np_,dp=struct.unpack('<H',rom[o+0x11:o+0x13])[0],struct.unpack('<H',rom[o+0x13:o+0x15])[0]
    def s(p): a=0x28000+(p&0x7FFF); return decode(rom,a,rom.index(b'\0',a),single,kanji)
    jpn=s(np_)
    frows.append({'fish_index':i,'record_rom':'%06X'%o,'name_jp':jpn,'name_en':Z.get(jpn,''),
                  'desc_jp':s(dp),'desc_en':FD[i],'limit':'22 cols on line 1, 27 after, max 4 lines (wrapped by the build)'})
with open(os.path.join(OUTDIR,'fish_notes.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,list(frows[0])); w.writeheader(); w.writerows(frows)
print('strings',len(rows),'names',len(nrows),'fish notes',len(frows))
