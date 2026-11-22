import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,re,struct; sys.path.insert(0,P.BUILD)
import lzss
rom=open(P.ROM,'rb').read()
# LDA #src STA $3E ; LDA #bank STA $40 ; LDA #dest STA $42 ; JSL DA62/DA66
pat=re.compile(rb'\xa9(..)\x85\x3e\xa9(.)\x00\x85\x40\xa9(..)\x85\x42(?:\xa9..\x85\x44)?\x22(\x62|\x66)\xda\x00',re.S)
blocks={}
for m in pat.finditer(rom[:0x80000]):
    a=struct.unpack('<H',m.group(1))[0]; b=m.group(2)[0]; dst=struct.unpack('<H',m.group(3))[0]
    key=(b,a)
    blocks.setdefault(key,[]).append((m.start(),dst,m.group(4)[0]))
print(len(blocks))
out=[]
for (b,a),sites in sorted(blocks.items()):
    try: d,n=lzss.decompress(rom,lzss.lo(b,a))
    except Exception as e: print('fail',hex(b),hex(a)); continue
    out.append(((b,a),len(d),sites))
    print('%02X:%04X len %5d sites %s'%(b,a,len(d),[('%05X'%s,'%04X'%dst,'vram' if k==0x66 else 'wram') for s,dst,k in sites][:4]))
import pickle; pickle.dump(out,open(P.out('gfx/blocks.pkl'),'wb'))
