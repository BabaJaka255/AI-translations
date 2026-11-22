"""Keep net / cooler window: the names of the fish in a slot pair. $82:A46F and $82:A4A9 copy the fish name
([$0E], bank $87, from $1D08) into $0C04 and draw the copy from bank $00, so the name skips the English
lookup. Both copies get a helper that looks the name up first (the English copy starts with DF, which
switches the drawing to English)."""
def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)
def code(rom,orig,place):
    lab=place("""
knl: LDA $12
    PHA
    LDA $14
    PHA
    LDA $0E
    STA $12
    LDA $10
    STA $14
    JSR xl
    LDA $12
    STA $0E
    LDA $14
    AND #$00FF
    STA $10
    PLA
    STA $14
    PLA
    STA $12
    .db $E2,$20,$A6,$12
    LDY #$0000
    RTL
""")
    a=lab['knl']; old=bytes.fromhex('8510e220a612a00000')
    for site in (0x82A469,0x82A4A3):
        o=lo(site>>16,site&0xFFFF); assert orig[o:o+9]==old,(hex(site),orig[o:o+9].hex())
        rom[o:o+9]=bytes([0x85,0x10,0x22,a&255,(a>>8)&255,0x82,0xEA,0xEA,0xEA])
