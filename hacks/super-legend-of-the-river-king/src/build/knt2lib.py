import paths as P
import struct, pickle, os
ROMPATH=P.ROM
TABLE_OFF=0x2BAD5; TABLE_N=537; TEXT_END=0x2F379
def p2r(p): return 0x28000+(p&0x7FFF)
def load_single(path=P.b('knt2_single_byte.tbl')):
    t={}
    for l in open(path,encoding='utf-8'):
        if l.startswith('#') or '=' not in l: continue
        k,v=l.rstrip('\n').split('=',1); t[int(k,16)]=v
    return t
def load_kanji(match=P.data('match_res2.pkl'),over=P.b('kanji_overrides.txt')):
    res=pickle.load(open(match,'rb')); k={}
    for g,v in res.items():
        if v: k[g]=v[0][0]
    if os.path.exists(over):
        for l in open(over,encoding='utf-8'):
            l=l.strip()
            if not l or l.startswith('#'): continue
            a,b=l.split('=',1); k[int(a,16)]=b
    return k
def strings(rom):
    ptrs=[struct.unpack('<H',rom[TABLE_OFF+2*i:TABLE_OFF+2*i+2])[0] for i in range(TABLE_N)]
    tg=[p2r(p) for p in ptrs]
    def end(r):
        i=r
        while rom[i]!=0: i+= 2 if 0xE0<=rom[i]<=0xEF else 1
        return i
    return ptrs,tg,{r:end(r) for r in set(tg)}
def decode(rom,start,end,single,kanji):
    out=[];i=start
    while i<end:
        b=rom[i]
        if b==0xCC: out.append("\n")
        elif b>=0xCD and b<0xE0: out.append("{%02X}"%b)
        elif 0xE0<=b<=0xEF:
            g=((b&0xF)<<8)|rom[i+1]; out.append(kanji.get(g,"<K%03X>"%g)); i+=1
        else: out.append(single.get(b,"<%02X>"%b))
        i+=1
    return "".join(out)
