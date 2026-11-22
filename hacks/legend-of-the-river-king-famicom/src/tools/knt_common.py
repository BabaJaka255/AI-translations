"""Shared constants and helpers for the Kawa no Nushi Tsuri (FC) tools."""
HEADER = 16
PRG_ORIG = 0x20000
JP = {}
_rows = {
    0x00: "0123456789*アイウエオ",
    0x10: "あかさたなはまやらわ゛カキクケコ",
    0x20: "いきしちにひみゃりょ゜サシスセソ",
    0x30: "うくすつぬふむゆるをざタチツテト",
    0x40: "えけせてねへめゅれっ!ナニヌネノ",
    0x50: "おこそとのほもよろんョハヒフヘホ",
    0x60: "┏┗┓┛?ボ。ーワcッマミムメモ",
    0x70: "┃━┃━じ¥ラスルレロヤャユュヨ",
}
for b, s in _rows.items():
    for i, c in enumerate(s):
        JP[b + i] = c
JP[0x77] = "グ"
JP[0xFE] = "　"


def prg(rom):
    return rom[HEADER:HEADER + PRG_ORIG]


def decode_jp(P, off):
    """Decode one FF-terminated line; dakuten prefixes 1A/2A are merged into the next kana."""
    import unicodedata
    s = ""; i = off; pend = ""
    while P[i] != 0xFF:
        x = P[i]
        if x == 0x1A: pend = "゙"
        elif x == 0x2A: pend = "゚"
        elif x < 0x80 or x == 0xFE:
            c = JP.get(x, f"[{x:02X}]")
            s += unicodedata.normalize("NFC", c + pend) if pend else c
            pend = ""
        else:
            s += f"<{x:02X}>"
        i += 1
    return s
