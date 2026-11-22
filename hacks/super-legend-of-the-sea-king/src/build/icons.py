"""Item icons with words on them: the two records (ステレオ, モノラル) become STEREO and MONO.

The icon sheet is LZSS $8F:8ACD (0x1C00 bytes, 4bpp, 16 tiles per row), read at $82:8F3F and $82:91F4.
Each icon is 32x16 (4 tiles wide, two rows). The records sit at tiles $4C and $60; the word is drawn in
colour 15 across rows 10-14, over the disc (colour 4). The disc is redrawn from its upper half (it is
symmetric about row 8, apart from the label) and the English word is set in the 5x8 font.
The rebuilt sheet goes in bank $BF (zero padding in the original), so it is readable from any bank setting."""
import paths as P
from PIL import PcfFontFile
from lzss import decompress, compress, lo
SRC=(0x8F,0x8ACD); DST=(0xBF,0xC000); SITES=[0x10F3F,0x111F4]
ICONS={0x4C:'STEREO',0x60:'MONO'}
TEXT,BG=15,1
pcf=PcfFontFile.PcfFontFile(open(P.font('koi5x8.pcf'),'rb'))

def get(d,t0):
    img=[[0]*32 for _ in range(16)]
    for y in range(16):
        for x in range(32):
            o=(t0+(y//8)*16+x//8)*32; yy=y%8; c=0
            for k,a in enumerate((o+2*yy,o+2*yy+1,o+16+2*yy,o+17+2*yy)): c|=((d[a]>>(7-x%8))&1)<<k
            img[y][x]=c
    return img
def put(d,t0,img):
    for ty in range(2):
        for tx in range(4):
            o=(t0+ty*16+tx)*32
            for yy in range(8):
                p=[0,0,0,0]
                for xx in range(8):
                    v=img[ty*8+yy][tx*8+xx]
                    for k in range(4): p[k]|=((v>>k)&1)<<(7-xx)
                d[o+2*yy]=p[0]; d[o+2*yy+1]=p[1]; d[o+16+2*yy]=p[2]; d[o+17+2*yy]=p[3]
def word(text):
    cols=[]
    for i,ch in enumerate(text):
        im=pcf.glyph[ord(ch)][3].convert('1'); px=im.load()
        if i: cols.append([0]*8)
        for x in range(4): cols.append([1 if px[x,y] else 0 for y in range(8)])
    return cols            # list of columns, 8 rows each (ink on rows 1-6)

def fix(img,text):
    for y in range(10,15):                 # disc without the word: mirror of rows 16-y
        for x in range(32):
            v=img[16-y][x]; img[y][x]=4 if v==10 else v
    cols=word(text); x0=(32-len(cols))//2
    for i,col in enumerate(cols):
        for y in range(1,7):
            if col[y]: img[8+y][x0+i]=TEXT
    return img

def apply(rom,orig):
    d=bytearray(decompress(orig,lo(*SRC))[0]); assert len(d)==0x1C00
    for t0,text in ICONS.items(): put(d,t0,fix(get(d,t0),text))
    blob=compress(bytes(d)); o=lo(*DST)
    assert DST[1]+len(blob)<=0x10000 and set(orig[o:o+len(blob)])<={0} and set(rom[o:o+len(blob)])<={0}
    rom[o:o+len(blob)]=blob
    for a in SITES:
        assert orig[a:a+10]==bytes([0xA9,SRC[1]&255,SRC[1]>>8,0x85,0x3E,0xA9,SRC[0],0x00,0x85,0x40]),hex(a)
        rom[a+1:a+3]=bytes([DST[1]&255,DST[1]>>8]); rom[a+6]=DST[0]
    return len(blob)
