import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,json,struct; sys.path.insert(0,'.')
from knt2lib import *
def rebuild(rom,new_bytes_by_id=None,text_start=0x2BF07,limit=0x2F379):
    """Lay out unique strings contiguously from text_start, rewrite 537 pointers. Returns new ROM."""
    ptrs,tg,ends=strings(rom)
    first={}
    for i,r in enumerate(tg): first.setdefault(r,i)
    out=bytearray(rom); pos=text_start; newptr={}
    for r,i in sorted(first.items(),key=lambda kv:kv[1]) if False else sorted(first.items(),key=lambda kv:kv[0]):
        data=(new_bytes_by_id or {}).get(i, rom[r:ends[r]])+b'\x00'
        assert pos+len(data)<=limit,"text region overflow by %d bytes"%(pos+len(data)-limit)
        out[pos:pos+len(data)]=data; newptr[r]=0x8000|(pos-0x28000)&0x7FFF; pos+=len(data)
    for i,r in enumerate(tg): struct.pack_into('<H',out,TABLE_OFF+2*i,newptr[r])
    if pos<limit: out[pos:limit]=b'\xFF'*(limit-pos)
    return bytes(out),pos
if __name__=="__main__":
    rom=open(ROMPATH,'rb').read()
    new,pos=rebuild(rom)
    print("round trip identical:",new==rom,"| text ends at %06X (region limit 2F379)"%pos)
