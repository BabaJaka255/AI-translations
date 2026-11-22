"""Fishing Note map: the little fish-name labels. $81:BBAC copies the Japanese name ([$12], bank $87) to $111A,
then $81:BBC2 writes each byte + $84 as a tile (attr $28) into the map. The 8x8 katakana font is LZSS
$B1:9700 (80 tiles, 2bpp, loaded at $81:AC67 to VRAM $2700, i.e. tile $E0 + slot; code $5C = slot 0).
Same scheme as Kawa no Nushi Tsuri 2: the font becomes an English 8x8 font with a transparent background
and a dark outline, and the copy loop is replaced by a helper that copies the English name (or a short
map-only name) and converts ASCII to slot codes. Slot 77 (the ▸ marker) and 78 (ー) are kept."""
import paths as P
from PIL import PcfFontFile, Image, ImageDraw
from lzss import decompress, compress, lo
SRC=(0xB1,0x9700); DST=(0xBF,0xB780); SITE=0xAC67
MAP_A=(0xC0,0xF100)              # ASCII -> code (128 bytes)
SHORT_A=(0xC0,0xF200)            # (Japanese name pointer, short name pointer) pairs, 0-terminated, then strings
MAXLEN=10
KEEP={77,78}
SHORT={'Black Porgy':'Porgy','Spear Squid':'Spear Sqd','Cutlassfish':'Cutlass','Bigeye Tuna':'Bigeye',
 'Toby Puffer':'Toby Puff.','Tongue Sole':'Tong. Sole','Meichi Bream':'Meichi','Flying Squid':'Fly. Squid',
 'Grass Puffer':'Grass Puff','Yellow Bream':'Yel. Bream','Bluefin Tuna':'Bluefin','Blue Snapper':'Bl.snapper',
 'Scorpionfish':'Scorpion','Striped Jack':'Str. Jack','Gizzard Shad':'Gizzard','Red Tilefish':'Red Tile',
 'Bulgy Wrasse':'Bulgy Wr.','Ruby Snapper':'Ruby Snap.','Young Mullet':'Yg. Mullet','Marbled Sole':'Marb. Sole',
 'Blue Marlin':'Bl. Marlin','Mantis Shrimp':'Mantis','Devil Stinger':'Stinger','Swimming Crab':'Swim. Crab',
 'Red Sea Bream':'Red Bream','Young Bluefin':'Yg.bluefin','Sunrise Perch':'Sunrise','Dogtooth Tuna':'Dogtooth',
 'Crimson Bream':'Crimson','Porcupinefish':'Porcupine','Spot Beakfish':'Beakfish','Jack Mackerel':'Jack Mack.',
 'Horse Filefish':'Filefish','Yellowfin Tuna':'Yellowfin','Stone Flounder':'St.flound.','White Tilefish':'Wh. Tile',
 'Black Rockfish':'Bl.rockfsh','Giant Sea Bass':'Gt.seabass','Bullhead Shark':'Bullhead','Longfin Bigeye':'Longfin',
 'Rainbow Runner':'Rainbow','Black Trevally':'Bl.trevly.','Yellow Tilefish':'Yel. Tile','Webfoot Octopus':'Webfoot',
 'Threadfin Bream':'Threadfin','Spanish Mackerel':'Sp. Mack.','Yellowtail Fry':'Ytail Fry',
 'Jr. Yellowtail':'Jr. Ytail','Rice Octopus':'Rice Octo.','Gold Tilefish':'Gold Tile',
 'Bigeye Bream':'Bigeye Brm','Big Yellowtail':'Big Ytail','Purple Puffer':'Pur.puffer',
 'Large-eye Bream':'Large-eye','Kelp Grouper':'Kelp Grpr.'}
CHARS=" ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.'()&/,"
pcf=PcfFontFile.PcfFontFile(open(P.font('koi5x8.pcf'),'rb'))

def glyph(ch):
    im=pcf.glyph[ord(ch)][3].convert('1'); px=im.load()
    return {(x+1,y) for x in range(im.size[0]) for y in range(min(8,im.size[1])) if px[x,y]}

def apply(rom,orig,place,names):
    d=bytearray(decompress(orig,lo(*SRC))[0]); assert len(d)==80*16
    slots=[s for s in range(80) if s not in KEEP]; assert len(CHARS)<=len(slots)
    amap=bytearray(128)
    def put(slot,ch):
        ink=glyph(ch) if ch!=' ' else set()
        edge={(x+dx,y+dy) for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}-ink
        for y in range(8):
            p0=p1=0
            for x in range(8):
                if (x,y) in ink: p0|=0x80>>x; p1|=0x80>>x         # colour 3 (light)
                elif (x,y) in edge: p0|=0x80>>x                    # colour 1 (dark outline)
            d[slot*16+2*y]=p0; d[slot*16+2*y+1]=p1                 # colour 0 = transparent
    for ch,s in zip(CHARS,slots): put(s,ch); amap[ord(ch)]=0x5C+s
    amap[ord('-')]=0x5C+78
    for c in range(0x20,0x7F):
        if amap[c]==0: amap[c]=0x5C+slots[0]
    blob=compress(bytes(d)); o=lo(*DST)
    assert DST[1]+len(blob)<=0xC000 and set(orig[o:o+len(blob)])<={0},len(blob)
    rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,SRC[1]&255,SRC[1]>>8,0x85,0x3E,0xA9,SRC[0],0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    o=lo(*MAP_A); assert set(rom[o:o+128])<={0xFF}; rom[o:o+128]=amap
    # short names for the map
    pairs=[]
    for p,en in sorted(names.items()):
        if len(en)>MAXLEN:
            sh=SHORT[en]; assert len(sh)<=MAXLEN,sh; pairs.append((p,sh))
    tb,sa=SHORT_A; base=sa+4*len(pairs)+2; tbl=bytearray(); strs=bytearray()
    for p,sh in pairs:
        q=base+len(strs); tbl+=bytes([p&255,p>>8,q&255,q>>8]); strs+=sh.encode()+b'\0'
    tbl+=b'\0\0'; o=lo(*SHORT_A); assert set(rom[o:o+len(tbl)+len(strs)])<={0xFF}
    rom[o:o+len(tbl)+len(strs)]=tbl+strs
    mb,ma=MAP_A
    lab=place(f"""
mlb: .db $C2,$20
    LDX #$0000
mll: LDA ${tb:02X}{sa:04X},X
    BEQ mln
    CMP $12
    BEQ mlh
    INX
    INX
    INX
    INX
    BRA mll
mlh: LDA ${tb:02X}{sa+2:04X},X
    STA $12
    LDA #$00{tb:02X}
    STA $14
    BRA mlc
mln: JSR xl
mlc: .db $E2,$20
    LDY #$0000
    LDX #$0000
    LDA [$12],Y
    .db $C9,$DF
    BNE mlg
    INY
mlg: LDA [$12],Y
    BEQ mle
    PHX
    .db $EB,$A9,$00,$EB
    TAX
    LDA ${mb:02X}{ma:04X},X
    PLX
    .db $9D,$1A,$11
    INX
    INY
    CPX #${MAXLEN:04X}
    BCC mlg
mle: .db $A9,$00,$9D,$1A,$11
    RTL
""")
    o=lo(0x81,0xBBAC)
    assert orig[o:o+16]==bytes.fromhex('a00000b712f0069 91a11c880f699 1a11'.replace(' ','')),orig[o:o+16].hex()
    a=lab['mlb']; rom[o:o+16]=bytes([0x22,a&255,(a>>8)&255,0x82])+bytes([0xEA]*12)
    return len(blob)
