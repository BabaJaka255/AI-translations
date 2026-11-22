import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,json; sys.path.insert(0,'.')
from knt2lib import *
rom=open(ROMPATH,'rb').read(); single=load_single(); kanji=load_kanji()
ptrs,tg,ends=strings(rom)
first={}
for i,r in enumerate(tg): first.setdefault(r,i)
uniq=sorted(first.items(),key=lambda kv:kv[1])
entries=[]
for r,i in uniq:
    aliases=[j for j,x in enumerate(tg) if x==r and j!=i]
    raw=rom[r:ends[r]]
    entries.append({"id":i,"rom":"%06X"%r,"snes":"05:%04X"%ptrs[i],"aliases":aliases,
                    "jp":decode(rom,r,ends[r],single,kanji),"raw":raw.hex(),"en":""})
json.dump(entries,open(P.out('script.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
with open(P.out('script_dump.txt'),'w',encoding='utf-8') as f:
    f.write("# Kawa no Nushi Tsuri 2 - main script dump (%d unique strings, %d pointers)\n"%(len(entries),len(ptrs)))
    f.write("# {CD}-{DA} = inline name/number insert codes. Kanji were read from the font bitmaps; a few may still be wrong.\n\n")
    for e in entries:
        f.write("[%03d] %s %s%s\n"%(e["id"],e["snes"],e["rom"],("  (also #%s)"%",".join(map(str,e["aliases"]))) if e["aliases"] else ""))
        for ln in e["jp"].split("\n"): f.write("JP| %s\n"%ln)
        f.write("EN|\n\n")
print(len(entries),"entries written")
