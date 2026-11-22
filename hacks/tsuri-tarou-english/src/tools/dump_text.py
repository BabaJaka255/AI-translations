"""Dump the known Japanese text: spot info strings and story tilemap pages.
dump_text.py ROM OUT.txt"""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ttlib import decode, T, TS, mark
rom=open(sys.argv[1],'rb').read()
out=[]
# spot info: pointer table at $01:E141.. picked by $08D6 (15 spots, 5 lines each)
o=0x0E141; end=0x0E752
lines=rom[o:end].split(b'\xf0')[:-1] if rom[end-1]==0xF0 else rom[o:end].split(b'\xf0')
p=o
out.append('# Spot info text ($01:E141-E751), 5 lines per spot, F0 ends each line')
for i,s in enumerate(lines):
    if i%5==0: out.append('\n## spot %d'%(i//5+1))
    out.append('%06X  %s'%(p,decode(s))); p+=len(s)+1
out.append('\n# Story pages (raw 32x32 tilemaps, column-major, text tiles 0x100+code)')
for m in (0x40000,0x037800,0x087800,0x040800,0x0A0800):
    out.append('\n## tilemap ROM %06X'%m)
    w=[rom[m+2*i]|rom[m+2*i+1]<<8 for i in range(1024)]
    def ch(r,c):
        t=w[c*32+r]&0x3FF
        if t in (0,0x100): return ' '
        return TS.get(t&0xFF,'?') if 0x100<=t<0x200 else '#'
    for r in range(32):
        row=[]
        for c in range(32):
            k=ch(r,c); above=ch(r-1,c) if r else ' '
            if k in ('゛','゜'): k=' '
            elif above in ('゛','゜') and k.strip(): k=mark(k,above)
            row.append(k)
        line=''.join(row).rstrip()
        if line.strip(' #'): out.append('r%02d %s'%(r,line))
open(sys.argv[2],'w',encoding='utf-8').write('\n'.join(out)+'\n')
