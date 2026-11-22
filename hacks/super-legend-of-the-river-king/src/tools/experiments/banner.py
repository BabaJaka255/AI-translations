import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,pickle,struct; sys.path.insert(0,'.')
from match import *
from PIL import Image
shot=_o.path.join(_o.path.dirname(P.ROOT),'docs','images','screenshots','shot_55.png')
im=Image.open(shot).convert('RGB'); px=im.load()
blocks=[k for k,_,_ in pickle.load(open('blocks.pkl','rb'))]+pickle.load(open('tbl.pkl','rb'))
# add field table blocks
for o in range(0x74E,0x7B6,4):
    a,b=struct.unpack('<HH',rom[o:o+4]); blocks.append((b,a))
blocks=sorted(set(blocks))
crop=[]
for oy in range(8):
    for ox in range(8):
        for by in range(50+oy,90,8):
            for bx in range(160+ox-8,180,8):
                blk=canon(tuple(px[bx+x,by+y] for y in range(8) for x in range(8)))
                if len(set(blk))>=3: crop.append(((ox,oy,bx,by),blk))
for b,a in blocks:
    for bpp in (4,):
        try: d,_=lzss.decompress(rom,lzss.lo(b,a))
        except Exception: continue
        H=index(tiles_of(d))
        hits=[k for k,blk in crop if blk in H]
        if len(hits)>=2: print('%02X:%04X'%(b,a),len(hits),hits[:6])
