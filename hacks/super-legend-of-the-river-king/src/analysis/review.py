import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,pickle; sys.path.insert(0,'.')
from knt2lib import *
from PIL import Image, ImageDraw
import numpy as np
exec(open(P.a('match_kanji.py')).read().split("# candidate chars")[0])
rom=open(ROMPATH,'rb').read(); single=load_single()
use,ctx,low=pickle.load(open(P.data('usage.pkl'),'rb'))
res=pickle.load(open(P.data('match_res2.pkl'),'rb'))
kanji=load_kanji()
low=sorted(low,key=lambda t:-t[1])
ptrs,tg,ends=strings(rom)
def context(g,r):
    s=decode(rom,r,ends[r],single,{**kanji,g:'■'}).replace("\n","/")
    k=s.find('■'); return s[max(0,k-9):k+10]
def sheet(batch,fn):
    cols=8; rows=(len(batch)+cols-1)//cols
    W=60;H=70
    img=Image.new('RGB',(cols*W,rows*H),(30,30,30)); d=ImageDraw.Draw(img)
    for n,(g,c,v) in enumerate(batch):
        b=glyph_bits(g); im=Image.fromarray((b*255).astype(np.uint8)).resize((48,48),Image.NEAREST).convert('RGB')
        x=(n%cols)*W; y=(n//cols)*H
        img.paste(im,(x+6,y+2)); d.text((x+6,y+52),str(n),fill=(255,220,80))
    img.save(fn)
start=int(sys.argv[1]);size=int(sys.argv[2])
batch=low[start:start+size]
sheet(batch,P.out('rev_%d.png')%start)
for n,(g,c,v) in enumerate(batch):
    cand=" ".join("%s%.2f"%(ch,s) for ch,s in v[:4]) if v else "-"
    r=ctx[g][0]
    print("%2d K%03X x%-3d %s | %s"%(n,g,c,cand,context(g,r)))
