import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,pickle; sys.path.insert(0,'.')
from knt2lib import *
from PIL import Image,ImageDraw,ImageFont
import numpy as np
exec(open(P.a('match_kanji.py')).read().split("# candidate chars")[0])
kanji=load_kanji()
use,ctx,low=pickle.load(open(P.data('usage.pkl'),'rb'))
ov={int(l.split('=')[0],16) for l in open(P.b('kanji_overrides.txt'),encoding='utf-8') if '=' in l}
auto=sorted([g for g in use if g not in ov])
F=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',34,index=0)
def sheet(gs,fn,cols=6):
    rows=(len(gs)+cols-1)//cols; W=104;H=54
    img=Image.new('RGB',(cols*W,rows*H),(30,30,30)); d=ImageDraw.Draw(img)
    for n,g in enumerate(gs):
        x=(n%cols)*W;y=(n//cols)*H
        b=Image.fromarray((glyph_bits(g)*255).astype(np.uint8)).resize((48,48),Image.NEAREST).convert('RGB')
        img.paste(b,(x+2,y+2)); d.text((x+54,y+6),kanji[g],font=F,fill=(120,220,255))
    img.save(fn)
per=84
for i in range(0,len(auto),per): sheet(auto[i:i+per],P.out('ver_%d.png')%(i//per))
print(len(auto))
