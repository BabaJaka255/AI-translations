import sys; sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from build_font import ENC
from expand import fix_checksum
r=bytearray(open('ttf.sfc','rb').read())
enc=lambda s:bytes(ENC[c] for c in s)
# spot 1: keep each line's byte length
o=0xE141; lines=["Lives in cold, high","mountain streams.","Grows to 30-80 cm.","Quick brown fox jumps","over the lazy dog!?"]
for t in lines:
    n=r.index(0xF0,o)-o; b=enc(t); assert len(b)<=n,(t,n)
    r[o:o+n]=b+b'\xff'*(n-len(b)); o+=n+1
# story page 0x40000: rewrite text rows 1-13
m=0x40000
story=["Deep in the mountains lived a","family of three, happy as can","be. But one morning, little","Kyoko fell ill with a terrible","fever. Her worried mother","remembered the legend of the","River Nushi, and said to her","son: \"Find the River Nushi,","and be sure to catch it!\"","So Tarou took his rod and","set off for the river."]
def W(i): return r[m+2*i]|r[m+2*i+1]<<8
attr=None
for c in range(32):
    for row in range(1,14):
        i=c*32+row; t=W(i)&0x3FF
        if 0x100<=t<0x174:
            attr=attr or (W(i)&0xFC00); v=0x100|attr; r[m+2*i]=v&0xFF; r[m+2*i+1]=v>>8
for k,t in enumerate(story):
    row=2+k
    for j,ch in enumerate(t):
        code=0 if ch==' ' else ENC[ch]
        i=(1+j)*32+row; v=(0x100+code)|attr; r[m+2*i]=v&0xFF; r[m+2*i+1]=v>>8
fix_checksum(r); open('ttt.sfc','wb').write(r); print('attr %04X'%attr)
