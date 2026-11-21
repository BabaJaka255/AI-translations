"""Fishing Note map: the little fish-name labels (81:D143..D1AB) copy the Japanese name and draw it with a
small 8x8 katakana font (LZSS 06:F000, 80 tiles, loaded at 81:C0F6), tile = code + $84 (code $5C = slot 0).
We replace the font with an English 8x8 font and copy the English name instead, converting ASCII to slot codes."""
import paths as P
import gzip
from PIL import PcfFontFile
from lzss import decompress, compress, lo
SRC=(0x06,0xF000); DST=(0x3B,0x8000); SITE=0xC0F6
MAP_A=0xCF80            # bank $38: ASCII -> code table (128 bytes)
SHORT_BANK=0x3F; SHORT_A=0x8000   # map-only short names (pointer, string) table
MAXLEN=9
SHORT={'Masu Trout':'Masu Tr.','Redspot Trout':'Redspot','Rainbow Trout':'Rainbow','Brown Trout':'Brown Tr.',
 'Brook Trout':'Brook Tr.','Pond Smelt':'Smelt','Black Bass':'Bl. Bass','Dark Sleeper':'Sleeper','Stone Moroko':'Moroko',
 'Bagrid Catfish':'Bagrid','Masu Salmon':'M. Salmon','Bighead Carp':'Bighead','Silver Carp':'Silver C.',
 'Biwa Gudgeon':'Biwa Gud.','Rough Sculpin':'R.Sculpin','Gold Crucian':'G.Crucian','Crucian Carp':'Crucian',
 'Torrent Catfish':'T.Catfish','Aucha Perch':'Aucha','Stickleback':'Sticklbk.','White Crucian':'W.Crucian',
 'Three-lips':'Threelips','Pike Gudgeon':'P.Gudgeon','False Gudgeon':'F.Gudgeon','Spined Loach':'S.Loach',
 'Amur Snakehead':'A.Snakehd','Grass Carp':'GrassCarp','Black Carp':'BlackCarp','Barbel Steed':'Barbel',
 'Pacific Redfin':'Redfin','Japanese Lates':'J. Lates','Bitterling':'Bitterlng','Black Porgy':'Porgy',
 'Starry Flounder':'Flounder','Grass Puffer':'Puffer','Paradise Fish':'Paradise','River Prawn':'Prawn',
 'Redspot Salmon':'R.Salmon','Softshell Turtle':'Softshell','Sea-run Char':'Sea Char'}
HELPER=0xFD80           # bank $82
KEEP={77}               # slot 77 = the ▸ marker
CHARS=" ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.'()&/"
def font():
    import os
    path=P.out('koi5x8')
    if not os.path.exists(path+'.pil'):
        PcfFontFile.PcfFontFile(gzip.open(P.font('koi5x8.pcf.gz'))).save(path)
    from PIL import ImageFont
    return ImageFont.load(path+'.pil')
def apply(rom,orig,xl,names):
    d=bytearray(decompress(orig,lo(*SRC))[0]); assert len(d)==80*16
    f=font()
    slots=[s for s in range(80) if s not in KEEP and s!=78]
    assert len(CHARS)<=len(slots)
    amap=bytearray(128)
    from PIL import Image, ImageDraw
    def put(slot,ch):
        img=Image.new('1',(8,8),0); px=img.load()
        if ch=='.': px[2,5]=px[3,5]=px[2,6]=px[3,6]=1
        else: ImageDraw.Draw(img).text((1,0),ch,font=f,fill=1)
        ink={(x,y) for x in range(8) for y in range(8) if px[x,y]}
        edge={(x+dx,y+dy) for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}-ink
        for y in range(8):
            p0=0; p1=0
            for x in range(8):
                if (x,y) in ink: p0|=0x80>>x; p1|=0x80>>x        # colour 3 (light)
                elif (x,y) in edge: p0|=0x80>>x                   # colour 1 (dark outline)
            d[slot*16+2*y]=p0; d[slot*16+2*y+1]=p1   # transparent background
    for ch,s in zip(CHARS,slots):
        put(s,ch); amap[ord(ch)]=0x5C+s
    put(78,'-'); amap[ord('-')]=0x5C+78
    for c in range(0x20,0x7F):
        if amap[c]==0: amap[c]=0x5C+slots[0]          # unknown -> space
    blob=compress(bytes(d)); o=lo(*DST); rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,0x00,0xF0,0x85,0x3E,0xA9,0x06,0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    o=lo(0x38,MAP_A); rom[o:o+128]=amap
    # map-only short names
    tbl=bytearray(); strs=bytearray(); pairs=[]
    for p,en in sorted(names.items()):
        if len(en)>MAXLEN: sh=SHORT[en]; assert len(sh)<=MAXLEN,sh; pairs.append((p,sh))
    base=SHORT_A+4*len(pairs)+2
    for p,sh in pairs:
        tbl+=bytes([p&255,p>>8,(base+len(strs))&255,(base+len(strs))>>8]); strs+=b'\xdf'+sh.encode()+b'\x00'
    tbl+=b'\0\0'; o=lo(SHORT_BANK,SHORT_A); assert all(x==0xFF for x in rom[o:o+len(tbl)+len(strs)])
    rom[o:o+len(tbl)+len(strs)]=tbl+strs
    # helper in bank 2
    S=SHORT_A; M=MAP_A; code=bytearray(); fix=[]; L={}
    def e(*b): code.extend(b)
    def br(op,lab): e(op,0); fix.append((len(code)-1,lab))
    e(0xDA,0x5A,0x08,0xC2,0x30, 0xAD,0x0A,0x12, 0x85,0x0A, 0xA2,0,0)
    L['sl']=len(code); e(0xBF,S&255,S>>8,SHORT_BANK); br(0xF0,'nos'); e(0xC5,0x0A); br(0xF0,'hit'); e(0xE8,0xE8,0xE8,0xE8); br(0x80,'sl')
    L['hit']=len(code); e(0xBF,(S+2)&255,(S+2)>>8,SHORT_BANK, 0x85,0x0A, 0xA9,SHORT_BANK,0x00, 0x85,0x0C); br(0x80,'cp')
    L['nos']=len(code); e(0xA9,0x05,0x00, 0x85,0x0C, 0x20,xl&255,xl>>8)
    L['cp']=len(code); e(0xA0,0,0, 0xB7,0x0A, 0x29,0xFF,0x00, 0xC9,0xDF,0x00); br(0xD0,'c0'); e(0xC8)
    L['c0']=len(code); e(0xA2,0,0)
    L['c1']=len(code); e(0xB7,0x0A, 0x29,0xFF,0x00); br(0xF0,'c2')
    e(0xDA,0xAA, 0xBF,M&255,M>>8,0x38, 0x29,0xFF,0x00, 0xFA, 0x9D,0x34,0x05, 0xE8,0xC8); br(0x80,'c1')
    L['c2']=len(code); e(0x9D,0x34,0x05, 0x28,0x7A,0xFA,0x6B)
    for pos,lab in fix:
        dlt=L[lab]-(pos+1); assert -128<=dlt<=127; code[pos]=dlt&255
    o=lo(2,HELPER); assert all(b==0xFF for b in rom[o:o+len(code)]); rom[o:o+len(code)]=code
    o=lo(1,0xD143); assert orig[o:o+10]==bytes.fromhex('ad0a12850aa90500850c')
    rom[o:o+10]=bytes([0x22,HELPER&255,HELPER>>8,0x82])+b'\xEA'*6
    o=lo(1,0xD17D); assert orig[o:o+3]==bytes.fromhex('a00000') and orig[lo(1,0xD18D):lo(1,0xD18D)+3]==bytes.fromhex('a20000')
    rom[o:o+3]=bytes([0x4C,0x8D,0xD1])
    return len(code)
