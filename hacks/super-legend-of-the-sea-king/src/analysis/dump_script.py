import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),"..","build")); import paths as P
import json
from umilib import *
rom=open(ROMPATH,'rb').read(); single=load_single(); kanji=load_kanji()
ptrs,tg,ends=strings(rom)
DATA=set(data_ids(rom))
first={}
for i,r in enumerate(tg): first.setdefault(r,i)
entries=[]
for r,i in sorted(first.items(),key=lambda kv:kv[1]):
    if i in DATA: continue
    aliases=[j for j,x in enumerate(tg) if x==r and j!=i]
    entries.append({"id":i,"rom":"%06X"%r,"snes":"86:%04X"%ptrs[i],"aliases":aliases,
                    "jp":decode(rom,r,ends[r],single,kanji),"raw":rom[r:ends[r]].hex(),"en":"","data":i in DATA})
json.dump(entries,open(P.out('script.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
with open(P.out('script_dump.txt'),'w',encoding='utf-8') as f:
    f.write("# Umi no Nushi Tsuri - main script dump (%d unique strings, %d pointers; %d binary records left out)\n"%(len(entries),len(ptrs),len(DATA)))
    f.write("# {CD}-{DB} = inline name/number insert codes. Kanji were read from the font bitmaps; a few may still be wrong.\n\n")
    for e in entries:
        f.write("[%03d] %s %s%s\n"%(e["id"],e["snes"],e["rom"],("  (also #%s)"%",".join(map(str,e["aliases"]))) if e["aliases"] else ""))
        for ln in e["jp"].split("\n"): f.write("JP| %s\n"%ln)
        f.write("EN|\n\n")
print(len(entries),"entries written")
