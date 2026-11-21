import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import numpy as np, sys, pickle
from PIL import Image, ImageDraw, ImageFont, ImageFilter
exec(open('match_kanji.py').read().split("# candidate chars")[0])
ttc='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
F=ImageFont.truetype(ttc,96,index=0)
# JIS level1 (SJIS lead 0x88-0x9F, plus 0xE0-0xE3 up to 0x889F..0x9872 = L1) ; level2 = rest
def sj(hi,lo):
    try: return bytes([hi,lo]).decode('shift_jis')
    except: return None
L1=[];L2=[]
for hi in range(0x88,0xEA):
    for lo in list(range(0x40,0x7F))+list(range(0x80,0xFD)):
        ch=sj(hi,lo)
        if ch and ('一'<=ch<='鿿' or ch=='々'):
            code=(hi<<8)|lo
            (L1 if code<0x9873 or False else L2).append(ch)
print(len(L1),len(L2))
S=16
def norm_img(im):
    bb=im.getbbox()
    if not bb: return None
    im=im.crop(bb).resize((14,14),Image.LANCZOS)
    a=np.asarray(im,np.float32)/255.0
    return a
def fe(a,blur=0.7):
    im=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    v=np.asarray(im,np.float32).ravel(); v=v-v.mean(); return v/(np.linalg.norm(v)+1e-6)
def cfeat(ch):
    im=Image.new('L',(120,120),0);ImageDraw.Draw(im).text((10,0),ch,font=F,fill=255)
    a=norm_img(im); return None if a is None else fe(a)
cand={}
for ch in L1+L2:
    f=cfeat(ch)
    if f is not None: cand[ch]=f
chars=list(cand);M=np.stack([cand[c] for c in chars]);isL1=np.array([c in set(L1) for c in chars])
res={}
for g in range(0x2C0):
    b=glyph_bits(g)
    if b.sum()<8: res[g]=None;continue
    im=Image.fromarray((b*255).astype(np.uint8))
    a=norm_img(im)
    f=fe(a)
    s=M@f
    # prefer level1 slightly
    s2=s+0.02*isL1
    o=np.argsort(-s2)[:5]
    res[g]=[(chars[i],round(float(s[i]),3)) for i in o]
known={0xBC:'山',0x20A:'奥',0x132:'端',0x91:'発',0x4:'流',0x9C:'渓',0x20B:'谷'}
for g,c in known.items(): print(hex(g),c,res[g][:3])
pickle.dump(res,open('match_res2.pkl','wb'))
