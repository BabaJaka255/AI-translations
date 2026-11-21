"""Creel window: the fish name is copied from [$06] (bank 5) into $1A29 at $82:A9CA and $82:A9FF without going
through the translation lookup. Replace 'LDA $120A / STA $06 / LDA #5 / STA $08' with a JSL to a helper that
runs the lookup and returns the (possibly relocated) pointer in $06/$08."""
SITES=(0xA9CA,0xA9FF)
OLD=bytes([0xAD,0x0A,0x12,0x85,0x06,0xA9,0x05,0x00,0x85,0x08])
def apply(rom,orig,lo,xl,at=0xFD00):
    x=xl
    code=bytes([0xDA,0xA5,0x0A,0x48,0xA5,0x0C,0x48,            # PHX / push $0A,$0C
                0xAD,0x0A,0x12,0x85,0x0A,0xA9,0x05,0x00,0x85,0x0C, # $0A=$120A, $0C=5
                0x20,x&255,x>>8,                               # JSR xl
                0xA5,0x0A,0x85,0x06,0xA5,0x0C,0x85,0x08,       # $06/$08 = result
                0x68,0x85,0x0C,0x68,0x85,0x0A,0xFA,0x6B])      # restore, PLX, RTL
    rom[lo(at):lo(at)+len(code)]=code
    for s in SITES:
        assert orig[lo(s):lo(s)+10]==OLD,hex(s)
        rom[lo(s):lo(s)+10]=bytes([0x22,at&255,at>>8,0x02])+b'\xEA'*6
