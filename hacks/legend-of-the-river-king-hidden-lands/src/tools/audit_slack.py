import sys,re,math
sys.path.insert(0,'tools')
import insert as I
S=I.load_script(); en=I.load_en()
toks,_=I.prepare(en,S)
out=[]
for i,t in sorted(toks.items()):
    if '{9}' in en[i] or '{>' in en[i]: continue
    pages=1+sum(1 for k,v in t if k=='pg')
    if pages<2: continue
    if any(k=='nl' for k,v in t) is False: pass
    # only 2-line dialogue
    seg=[[]]
    for k,v in t:
        if k=='pg': seg.append([]); continue
        seg[-1].append((k,v))
    if any(sum(1 for k,v in s if k=='nl')>1 for s in seg): continue
    tot=sum(I.text_px(v) if k=='t' else (v[1] if k=='w' else 0) for k,v in t)+4*(len(seg)-1)
    lb=math.ceil(tot/430)
    if pages>lb: out.append((pages-lb,tot,i))
out.sort(key=lambda x:(-x[0],x[1]))
for d,tot,i in out: print(i,'pages-lb=%d'%d,tot,'|',en[i])
print(len(out))
