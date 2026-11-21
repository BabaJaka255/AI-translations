"""Extra English label art for window labels whose original graphics are stored compressed:
status window (体力/お金/経験 -> HP/Yen/EXP) and the battle command title (命令 -> Cmd).
The art is DMA'd over the original tiles each time those windows are drawn."""
import labels
ART=0x184000          # ROM offset == $30:C000
ART_SNES=(0x30,0xC000)
def tiles_from_img(img,ncols):
    top=bytearray(); bot=bytearray()
    for half,buf in ((0,top),(1,bot)):
        for c in range(ncols):
            for y in range(8):
                p0=p1=0
                for x in range(8):
                    v=img[half*8+y][c*8+x]; p0|=(v&1)<<(7-x); p1|=(v>>1)<<(7-x)
                buf+=bytes([p0,p1])
    return bytes(top),bytes(bot)
def label_img(parts,colw):
    """parts: list of texts, each placed left-aligned (1px margin) in a colw-column slot."""
    W=len(parts)*colw*8
    img=[[1]*W for _ in range(16)]
    for i,t in enumerate(parts):
        r=labels.render(t,colw*8,1) or labels.render(t,colw*8,0)
        assert r,t
        # shift left: find first ink column
        cols=[x for x in range(colw*8) if any(r[y][x]==3 for y in range(16))]
        sh=min(cols)-1 if cols else 0
        for y in range(16):
            for x in range(colw*8):
                sx=x+sh
                img[y][i*colw*8+x]=r[y][sx] if 0<=sx<colw*8 else 1
    return img
def dma(src_lo,bank,dest,size):
    b=bytearray()
    for val,dp in ((src_lo,0x42),(bank,0x44),(dest,0x46),(size,0x3E)):
        b+=bytes([0xA9,val&255,val>>8,0x85,dp])
    b+=bytes([0x22,0x6A,0xDA,0x00])   # JSL $00DA6A (VRAM DMA)
    return b
def apply(rom,orig,lo):
    st_top,st_bot=tiles_from_img(label_img(['HP','Yen','EXP'],4),12)
    cm_img=labels.render('Cmd',32,1)
    cm_img[0]=[3]*32   # keep the window's top border line
    cm_top,cm_bot=tiles_from_img(cm_img,4)
    data=st_top+st_bot+cm_top+cm_bot
    rom[ART:ART+len(data)]=data
    base=ART_SNES[1]
    s1=dma(base,0x30,0x1A20,0xC0)+dma(base+0xC0,0x30,0x1AA0,0xC0)+bytes([0xAD,0x62,0x08,0x85,0x3E,0x60])
    s2=dma(base+0x180,0x30,0x1B30,0x40)+dma(base+0x1C0,0x30,0x1BB0,0x40)+bytes([0xA9,0x40,0x1C,0x85,0x46,0x60])
    A1=0xFD00; A2=A1+len(s1)
    rom[lo(A1):lo(A1)+len(s1)]=s1; rom[lo(A2):lo(A2)+len(s2)]=s2
    for addr,old,sub in ((0x8281,bytes([0xAD,0x62,0x08,0x85,0x3E]),A1),(0x8476,bytes([0xA9,0x40,0x1C,0x85,0x46]),A2)):
        assert orig[lo(addr):lo(addr)+5]==old,hex(addr)
        rom[lo(addr):lo(addr)+5]=bytes([0x20,sub&255,sub>>8,0xEA,0xEA])
    return data
