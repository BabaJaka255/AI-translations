"""Fish market window: the daily special. $82:A66A reads the fish name pointer (record +$19, bank $87) and
draws it into 12 columns of staging ($82:A67E DMAs 12 tiles), with the price at a fixed column after it.
Names over 12 letters get a short form for this window only: the read is replaced by a helper that swaps
the pointer for one in a (Japanese pointer, short pointer) table at SHORT_A; the short strings start with DF."""
from lzss import lo
SHORT_A=(0xC0,0xF600)
MAXLEN=12
SITE=(0x82,0xA66D); OLD=bytes.fromhex('b70e8512a987008514')
SHORT={'Sunrise Perch':'Sunrise Prch','Jack Mackerel':'Jack Mackerl','Gold Tilefish':'Gold Tilefsh',
 'White Tilefish':'Wht Tilefish','Spot Beakfish':'Spot Beakfsh','Stone Flounder':'Stn Flounder',
 'Giant Sea Bass':'Giant S.bass','Dogtooth Tuna':'Dogtth. Tuna','Horse Filefish':'Hrs Filefish',
 'Devil Stinger':'Devil Stingr','Black Trevally':'Blk Trevally','Yellowfin Tuna':'Yellowfin',
 'Young Bluefin':'Yng Bluefin','Mantis Shrimp':'Mantis Shrmp','Black Rockfish':'Blk Rockfish',
 'Longfin Bigeye':'L.fin Bigeye','Crimson Bream':'Crimsn Bream','Rainbow Runner':'Rnbw Runner',
 'Porcupinefish':'Porcupinefsh','Swimming Crab':'Swim. Crab','Yellowtail Fry':'Ytail Fry',
 'Jr. Yellowtail':'Jr. Ytail','Big Yellowtail':'Big Ytail','Red Sea Bream':'Red S.bream',
 'Purple Puffer':'Purpl Puffer','Bullhead Shark':'Bullhd Shark'}
def apply(rom,orig,place,names):
    """names: {bank-$87 name pointer: English name} for every fish record."""
    pairs=[]
    for p,en in sorted(names.items()):
        if len(en)>MAXLEN:
            sh=SHORT[en]; assert len(sh)<=MAXLEN,sh; pairs.append((p,sh))
    tb,sa=SHORT_A; base=sa+4*len(pairs)+2; tbl=bytearray(); strs=bytearray()
    for p,sh in pairs:
        q=base+len(strs); tbl+=bytes([p&255,p>>8,q&255,q>>8]); strs+=b'\xDF'+sh.encode()+b'\0'
    tbl+=b'\0\0'; o=lo(*SHORT_A); assert set(rom[o:o+len(tbl)+len(strs)])<={0xFF}
    rom[o:o+len(tbl)+len(strs)]=tbl+strs
    lab=place(f"""
mkt: LDA [$0E],Y
    STA $12
    LDA #$0087
    STA $14
    .db $DA
    LDX #$0000
mkl: LDA ${tb:02X}{sa:04X},X
    BEQ mkn
    CMP $12
    BEQ mkh
    INX
    INX
    INX
    INX
    BRA mkl
mkh: LDA ${tb:02X}{sa+2:04X},X
    STA $12
    LDA #$00{tb:02X}
    STA $14
mkn: .db $FA
    RTL
""")
    a=lab['mkt']; o=lo(*SITE); assert orig[o:o+9]==OLD,orig[o:o+9].hex()
    rom[o:o+9]=bytes([0x22,a&255,(a>>8)&255,0x82,0xEA,0xEA,0xEA,0xEA,0xEA])
    return len(pairs)
