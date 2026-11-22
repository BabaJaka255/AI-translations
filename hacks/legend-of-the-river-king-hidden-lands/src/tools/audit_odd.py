import sys,re
sys.path.insert(0,'tools')
import insert as I
S=I.load_script(); en=I.load_en()
toks,_=I.prepare(en,S)
res=[]
for i,t in toks.items():
    pages=[[]]
    for k,v in t:
        if k=='pg': pages.append([]); continue
        pages[-1].append((k,v))
    if len(pages)<2: continue
    # skip non-dialogue (wrap-L>2) strings
    if any(sum(1 for k,v in p if k=='nl')>1 for p in pages): continue
    # pages with a single line that is not ended by a sentence end
    for n,p in enumerate(pages):
        nl=sum(1 for k,v in p if k=='nl')
        txt=''.join(v for k,v in p if k=='t')
        if nl==0 and not any(k=='tab' for k,v in p):
            res.append((i,n,len(pages),txt))
for r in res: print(r)
print(len(res), len(set(r[0] for r in res)))
print('-----')
cand=[]
for i,n,np_,txt in res:
    if np_!=2: continue
    t=toks[i]
    tot=sum(I.text_px(v) if k=='t' else (v[1] if k=='w' else 0) for k,v in t)+4
    cand.append((tot,i))
cand.sort()
for tot,i in cand:
    if tot<=560: print(i,tot,'|',en[i])
