import sys,struct,json,zlib
sys.path.insert(0,'.')
import encode_en, vwf
GAMES={
 'g4':dict(font=0x0d2220, st=0x03000020, blit=0x08045c5c),
 'g3':dict(font=0x1b51dc, st=0x03000b10, blit=0x08094fd4),
}
FREE_CODE=0x300000
class Rom:
    def __init__(s,data): s.d=bytearray(data); s.alloc=0x240000
    def w(s,off,b): s.d[off:off+len(b)]=b
    def put(s,b,align=1):
        s.alloc=(s.alloc+align-1)//align*align
        a=s.alloc; s.w(a,b); s.alloc+=len(b); return a
def hook(rom,addr,target):
    # ldr r1,[pc,#0]; bx r1; .word target|1   (addr must be 4-aligned+0? needs literal aligned)
    o=addr-0x08000000
    assert (o+4)%4==0 or True
    lit=((addr+4)&~3)
    code=bytearray()
    # place: at addr: ldr r1,[pc,#k]; bx r1; [pad]; word
    k=(lit-((addr+4)&~3))
    rom.w(o,struct.pack('<HH',0x4900|(k//4),0x4708))
    rom.w(lit-0x08000000 if lit>=addr+4 else 0, b'')
    rom.w(((addr+4)&~3)-0x08000000, struct.pack('<I',target|1))
def build(src,out,tests=None):
    rom=Rom(open(src,'rb').read())
    code_at=FREE_CODE
    for g,info in GAMES.items():
        tiles=encode_en.font_tiles()
        for c,t in tiles.items(): rom.w(info['font']+c*32,t)
        wid=encode_en.WIDTHS[g]
        wa=code_at; rom.w(wa,wid); code_at+=256
        var=0x03006ff0 if g=='g4' else 0x03006ff4
        c=vwf.assemble(vwf.vwf_src(info['st'],var,0x08000000+wa,0x08000000+info['font']),0x08000000+code_at)
        rom.w(code_at,c); hook(rom,info['blit'],0x08000000+code_at); code_at+=(len(c)+3)&~3
    if tests:
        for ptr_off,text,g in tests:
            b=encode_en.encode(text,g)
            a=rom.put(b)
            rom.w(ptr_off,struct.pack('<I',0x08000000+a))
    open(out,'wb').write(rom.d)
    return rom
if __name__=='__main__':
    import pickle
    refs=pickle.load(open('refs.pkl','rb'))
    t=0x18041
    tests=[(r,"I'm Yuki. Thank you for coming, all of you! There's something I must ask of you here...{fa fb f0 f2}I've waited so long for you. My precious treasure was split in two and stolen!{fa fb f0}",'g4') for r in refs[t]]
    tests+=[(r,"Which save file would you like to play? Quickly now!",'g3') for r in refs[0x1b559]]
    build('../rom/k34.gba','test.gba',tests)
