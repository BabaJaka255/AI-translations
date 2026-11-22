import sys,pickle,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
rom=open(sys.argv[1],'rb').read(); N=int(sys.argv[2],16)
def bits(g):
    a=0x40000+((g&0xFF8)<<5)+((g&7)<<4); arr=np.zeros((16,16),np.float32)
    for qy in range(2):
        for qx in range(2):
            for y in range(8):
                v=rom[a+qy*0x80+qx*8+y]
                for x in range(8): arr[qy*8+y,qx*8+x]=(v>>(7-x))&1
    return arr
def sj(hi,lo):
    try: return bytes([hi,lo]).decode('shift_jis')
    except: return None
L1=[];L2=[]
for hi in range(0x88,0xEA):
    for lo in list(range(0x40,0x7F))+list(range(0x80,0xFD)):
        ch=sj(hi,lo)
        if ch and ('一'<=ch<='鿿' or ch=='々'): (L1 if ((hi<<8)|lo)<0x9873 else L2).append(ch)
F=ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',96)
def norm(im):
    bb=im.getbbox()
    if not bb: return None
    return np.asarray(im.crop(bb).resize((14,14),Image.LANCZOS),np.float32)/255
def fe(a):
    v=np.asarray(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)),np.float32).ravel(); v-=v.mean(); return v/(np.linalg.norm(v)+1e-6)
chars=[];feats=[]
for ch in L1+L2:
    im=Image.new('L',(120,120),0);ImageDraw.Draw(im).text((10,0),ch,font=F,fill=255)
    a=norm(im)
    if a is not None: chars.append(ch);feats.append(fe(a))
M=np.stack(feats); isL1=np.array([c in set(L1) for c in chars])
res={}
for g in range(N):
    b=bits(g)
    if b.sum()<8: res[g]=None; continue
    s=M@fe(norm(Image.fromarray((b*255).astype(np.uint8)))); o=np.argsort(-(s+0.02*isL1))[:5]
    res[g]=[(chars[i],round(float(s[i]),3)) for i in o]
pickle.dump(res,open(sys.argv[3],'wb'))
