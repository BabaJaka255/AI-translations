import sys,re
sys.path.insert(0,'tools')
import insert as I
S=I.load_script(); en=I.load_en()
toks,_=I.prepare(en,S)
END=I.END_S
for i,t in sorted(toks.items()):
    if '{9}' in en[i]: continue
    txt=''
    for k,v in t:
        if k=='t': txt+=v
        elif k=='pg' and v==[0xfffd]: txt+='|PG|'
        elif k=='w' and v[0][0]==0xfff7: txt+='NAME'
        elif k=='w' and v[0][0]==0xfffa: txt+='<A>'
        elif k=='w' and v[0][0]==0xfffb: txt+='<B>'
        elif k=='nl': txt+=' '
    segs=txt.split('|PG|')
    bad=[s for s in segs[:-1] if not s.rstrip().endswith(END)]
    if bad and not any('{>' in en[i] for _ in [0]): print(i,'|',' // '.join(segs))
