import struct,sys,pickle,json
sys.path.insert(0,'.')
from jpdec import dec
rom=open('../rom/k34.gba','rb').read()
refs_all=pickle.load(open('refs.pkl','rb'))
REG={'g4':(0xfa20,0x19a00),'g3':(0x1b2dd,0x1e617)}
TABLES={'g4':[(0x11860,0x12068)],'g3':[]}
def addrlike(v): return (v>>24) in (2,3,4,5,6,7,8)
def true_refs(t):
    out=[]
    for r in refs_all.get(t,[]):
        nb=[struct.unpack_from('<I',rom,r+d)[0] for d in (-4,4)]
        if any(addrlike(x) for x in nb): out.append(r)
    return out
def strings(name):
    a,b=REG[name]
    tabs=TABLES[name]
    starts=[]
    for t in sorted(refs_all):
        if not (a<=t<b): continue
        if any(x<=t<y for x,y in tabs): continue
        if rom[t-1]!=0xf0 and t!=a: continue
        tr=true_refs(t)
        if tr: starts.append((t,tr))
    out=[]
    for i,(s,tr) in enumerate(starts):
        nxt=starts[i+1][0] if i+1<len(starts) else b
        for x,y in tabs:
            if s<x<nxt: nxt=x
        e=s
        while e<nxt:
            if rom[e]==0xf0:
                e+=1
                if e<nxt and rom[e]==0xf2: continue
                break
            e+=1
        out.append(dict(addr=s,end=e,refs=tr,raw=rom[s:e].hex(),jp=dec(rom[s:e],name)))
    return out
if __name__=='__main__':
    for n in REG:
        S=strings(n)
        json.dump(S,open('%s_jp.json'%n,'w'),ensure_ascii=False,indent=0)
        with open('%s_dump.txt'%n,'w') as f:
            for i,s in enumerate(S):
                f.write('%s%04d %05x | %s\n'%(n,i,s['addr'],s['jp']))
        print(n,len(S),sum(len(s['refs']) for s in S))
