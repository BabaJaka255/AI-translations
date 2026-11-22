"""Letter envelopes (81:DB07, five letters, string ids in tables $81:DD5B / $81:DD6F). The envelope art is the
label-sheet row at ROM 0x4BA00 (16 tiles, loaded to VRAM $2100/$2180 at $81:DB3C): tiles 0-7 the stamp and the
postmark, 8-9 〒 (before both addresses) and 10-11 様 (after the addressee's name). In English both marks are
dropped, as on a Western envelope. Addresses are drawn in 16 columns, the sender's name in 8, the addressee's
name comes from the save slot."""
from labels import write_px
ROW=0x4BA00
ADDRESS=(62,64,67,70,503,580); SENDER=(65,68,71,504,581)
def apply(rom,orig):
    assert orig[0xDB41:0xDB44]==bytes([0xA9,0x00,0xBA])
    write_px(rom,ROW,16,8,4,[[1]*32 for _ in range(16)])
