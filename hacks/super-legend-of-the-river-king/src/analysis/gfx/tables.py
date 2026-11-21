import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,struct; sys.path.insert(0,P.BUILD)
import lzss
rom=open(P.ROM,'rb').read()
def lo(b,a): return (b&0x7F)*0x8000+(a&0x7FFF)
TABLES=[(0x04,0xBB0C,8,0),(0x04,0xBB0C,8,4),(0x01,0xD84C,4,0),(0x01,0xDE09,4,0),(0x01,0xEAED,4,0),(0x02,0xDD5A,4,0),
        (0x03,0xE6AF,8,0),(0x03,0xE6AF,8,4),(0x03,0xE637,4,0),(0x04,0xBD54,4,0),(0x04,0xB812,8,0),(0x04,0xB812,8,4)]
found={}
for b,a,st,off in TABLES:
    for i in range(64):
        o=lo(b,a)+i*st+off
        p=struct.unpack('<H',rom[o:o+2])[0]; bk=struct.unpack('<H',rom[o+2:o+4])[0]
        if bk<0x05 or bk>0x2F or p<0x8000: break
        try: d,n=lzss.decompress(rom,lo(bk,p))
        except Exception: break
        if len(d)<32 or len(d)>0x10000: break
        found.setdefault((bk,p),[]).append(('%02X:%04X'%(b,a),i,off))
for k,v in sorted(found.items()):
    d,_=lzss.decompress(rom,lo(*k)); print('%02X:%04X'%k,len(d),v[:3])
import pickle; pickle.dump(sorted(found),open(P.out('gfx/tbl.pkl'),'wb'))
