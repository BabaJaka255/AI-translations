import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),"..","build")); import paths as P
import struct
from umilib import *
def rebuild(rom,new_bytes_by_id=None,text_start=TEXT_START,limit=TEXT_END):
    """Lay out unique strings contiguously from text_start, rewrite the 710 pointers. Returns new ROM."""
    ptrs,tg,ends=strings(rom)
    first={}
    for i,r in enumerate(tg): first.setdefault(r,i)
    out=bytearray(rom); pos=text_start; newptr={}
    for r,e in chunks(rom):
        i=first[r]
        if e<=ends[r]: data=rom[r:e]                  # target sits inside the next string: keep the bytes as they are
        elif new_bytes_by_id and i in new_bytes_by_id: data=new_bytes_by_id[i]+b'\x00'+rom[ends[r]+1:e]
        else: data=rom[r:e]
        assert pos+len(data)<=limit,"text region overflow by %d bytes"%(pos+len(data)-limit)
        out[pos:pos+len(data)]=data; newptr[r]=r2p(pos); pos+=len(data)
    for i,r in enumerate(tg): struct.pack_into('<H',out,TABLE_OFF+2*i,newptr[r])
    if pos<limit: out[pos:limit]=b'\xFF'*(limit-pos)
    return bytes(out),pos
if __name__=="__main__":
    rom=open(ROMPATH,'rb').read()
    new,pos=rebuild(rom)
    print("round trip identical:",new==rom,"| text ends at %06X (region limit %06X)"%(pos,TEXT_END))
