import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import lzss
A=_o.path.join(P.ROOT,'data','dumps')+'/'  # dumps renamed: VideoRamSign.dmp etc.
rom=open(P.ROM,'rb').read()
def cands():
    for o in range(0,len(rom)-2):
        if rom[o]==0 and rom[o+1]%4==0 and 4<=rom[o+1]<=0xC0: yield o
def run(target_tiles):
    res=[]
    for o in cands():
        try: d,n=lzss.decompress(rom,o)
        except Exception: continue
        if len(d)!=(rom[o+1]<<8): continue
        k=sum(1 for t in target_tiles if t in d)
        if k: res.append((o,len(d),n,k))
    return res
if __name__=='__main__':
    v=open(A+sys.argv[1],'rb').read(); s,e=int(sys.argv[2],16),int(sys.argv[3],16)
    ts=[v[o:o+32] for o in range(s,e,32) if len(set(v[o:o+32]))>8][:40]
    for r in run(ts): print('%06X len %5d clen %5d hits %d'%r)
