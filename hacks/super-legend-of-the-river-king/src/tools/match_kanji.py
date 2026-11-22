import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import numpy as np, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
rom=open(P.ROM,'rb').read()
def addrA(g): return 0x30000+((g&0x0FF8)<<5)+((g&7)<<4)
def glyph_bits(g):
    a=addrA(g)
    TL=rom[a:a+8];TR=rom[a+8:a+16];BL=rom[a+0x80:a+0x88];BR=rom[a+0x88:a+0x90]
    arr=np.zeros((16,16),np.float32)
    for y in range(8):
        for x in range(8):
            arr[y,x]=(TL[y]>>(7-x))&1; arr[y,8+x]=(TR[y]>>(7-x))&1
            arr[8+y,x]=(BL[y]>>(7-x))&1; arr[8+y,8+x]=(BR[y]>>(7-x))&1
    return arr
# candidate chars: JIS X 0208 kanji (rows 16-84) via shift_jis
cands=[]
for hi in range(0x88,0xEA):
    for lo in list(range(0x40,0x7F))+list(range(0x80,0xFD)):
        try: ch=bytes([hi,lo]).decode('shift_jis')
        except: continue
        if '一'<=ch<='鿿' or ch in '々': cands.append(ch)
cands=sorted(set(cands))
print(len(cands),"candidates",file=sys.stderr)
ttc='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font=ImageFont.truetype(ttc,64,index=0)  # index 0 is JP in most Noto CJK ttc
def render(ch):
    im=Image.new('L',(80,80),0);d=ImageDraw.Draw(im)
    d.text((8,4),ch,font=font,fill=255)
    bb=im.getbbox()
    if not bb: return None
    im=im.crop(bb)
    # normalize bbox to fill 14x14 region like the bitmap would
    return im
def feat(arr):
    # blur+normalize
    im=Image.fromarray((arr*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))
    a=np.asarray(im,np.float32).ravel(); a=a-a.mean(); n=np.linalg.norm(a); return a/(n+1e-6)
def bbox_norm_bitmap(arr):
    ys,xs=np.where(arr>0)
    if len(ys)==0: return None
    return arr[ys.min():ys.max()+1, xs.min():xs.max()+1]
# precompute candidate features: render glyph, resize bbox-fit to match bitmap bbox? use two variants: full-em at 15px and bbox-normalized
import pickle
cf={}
for ch in cands:
    im=Image.new('L',(64,64),0);d=ImageDraw.Draw(im);d.text((0,-6),ch,font=ImageFont.truetype(ttc,60,index=0),fill=255)
    r=im.resize((16,16),Image.LANCZOS)
    cf[ch]=feat(np.asarray(r,np.float32)/255.0)
pickle.dump(cf,open('cand_feats.pkl','wb'))
print("done")
