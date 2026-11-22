"""Show a BAT-word window template using the menu glyph dictionary (tiles $700 + 4*glyph + quadrant)."""
DIC = '渓上中下流河口体力お金経験命令え弁当釣具びく道川虫ねり赤さしみず牛乳ぱんはもちあ容量針鍵寄せ磁石め火ぬい竿リーご花がね斧たら竹ル'
def show(words, width):
    out = []
    for r in range(0, len(words), width):
        row = ''
        for w in words[r:r + width]:
            t = w & 0x7FF
            if 0x700 <= t < 0x800:
                k, q = divmod(t - 0x700, 4); row += DIC[k] if q == 0 else '·,;'[q - 1]
            else: row += '.' if t == 0x8f or t == 0x72 else '#'
        out.append(row)
    return '\n'.join(out)
