import sys,struct,pickle,json,collections
TK=sys.argv[3] if len(sys.argv)>3 else 'RiverKingToolkit/build'
rom=open(sys.argv[1],'rb').read()
TABLE_OFF=0x31B25; TABLE_N=710
def p2r(p): return 0x30000+(p&0x7FFF)
single={}
for l in open(TK+'/knt2_single_byte.tbl',encoding='utf-8'):
    if l.startswith('#') or '=' not in l: continue
    k,v=l.rstrip('\n').split('=',1); single[int(k,16)]=v
res=pickle.load(open(TK+'/data/match_res2.pkl','rb'))
kanji={g:v[0][0] for g,v in res.items() if v}
for l in open(TK+'/kanji_overrides.txt',encoding='utf-8'):
    l=l.strip()
    if l and not l.startswith('#') and '=' in l: a,b=l.split('=',1); kanji[int(a,16)]=b
ptrs=[struct.unpack_from('<H',rom,TABLE_OFF+2*i)[0] for i in range(TABLE_N)]
def end(r):
    i=r
    while rom[i]!=0: i+=2 if 0xE0<=rom[i]<=0xEF else 1
    return i
used=collections.Counter(); kused=collections.Counter(); unknown=collections.Counter()
out=[]; seen={}
for i,p in enumerate(ptrs):
    r=p2r(p)
    if r in seen: continue
    seen[r]=i; e=end(r); s=[]; j=r
    while j<e:
        b=rom[j]; used[b]+=1
        if b==0xCC: s.append('\n')
        elif 0xCD<=b<0xE0: s.append('{%02X}'%b)
        elif 0xE0<=b<=0xEF:
            g=((b&0xF)<<8)|rom[j+1]; kused[g]+=1
            if g in kanji: s.append(kanji[g])
            else: s.append('<K%03X>'%g); unknown[g]+=1
            j+=1
        else: s.append(single.get(b,'<%02X>'%b))
        j+=1
    out.append((i,p,r,''.join(s)))
with open(sys.argv[2],'w',encoding='utf-8') as f:
    for i,p,r,s in out:
        f.write('[%03d] 86:%04X %06X\n'%(i,p,r))
        for ln in s.split('\n'): f.write('JP| '+ln+'\n')
        f.write('\n')
print('unique strings',len(out))
print('control/unused bytes', {('%02X'%k):v for k,v in sorted(used.items()) if k>=0xCC and k<0xE0})
print('single bytes not in KNT2 table', {('%02X'%k):v for k,v in sorted(used.items()) if k<0xCC and k not in single})
print('kanji glyphs used',len(kused),'max index %03X'%max(kused),'not in KNT2 table',len(unknown), 'occurrences',sum(unknown.values()))
