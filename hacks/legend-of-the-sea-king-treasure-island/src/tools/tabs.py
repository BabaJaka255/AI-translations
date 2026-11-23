"""Compare EN tab stops with JP column starts (JP space glyph 0 is 8 px)."""
import sys, json, re; sys.path.insert(0, 'tools')
from insert import W_INSERT, W_NAME, W_NUM
from textfmt import load_en
S = {o['id']: o for o in json.load(open('out/script_jp.json'))}
en = load_en()
def jp_cols(words):
    lines = [[]]; x = 0; i = 0; prev_sp = True
    while i < len(words):
        w = words[i]
        if w in (0xfffe, 0xfffd): lines.append([]); x = 0; prev_sp = True; i += 1; continue
        if w >= 0xfff0:
            adv = 0
            if w == 0xfffc: adv = 8 * words[i + 1]; i += 1
            elif w in (0xfff7, 0xfff8): adv = W_NAME if w == 0xfff7 else 0; i += 1
            elif w == 0xfffa: adv = W_INSERT
            elif w == 0xfffb: adv = W_NUM
            if adv:
                if prev_sp: lines[-1].append(x)
                prev_sp = False; x += adv
            i += 1; continue
        if w == 0: x += 8; prev_sp = True
        else:
            if prev_sp: lines[-1].append(x)
            prev_sp = False; x += 8 if w < 0x16 else 16
        i += 1
    return lines
for i in sorted(en):
    if '{>' not in en[i] or i not in S: continue
    jl = jp_cols(S[i]['words'])
    el = [[int(t) for t in re.findall(r'\{>(\d+)\}', ln)] for ln in re.split(r'\{[ED]\}', en[i])]
    print(i, '|', ' / '.join(','.join(map(str, c)) for c in jl), '|', ' / '.join(','.join(map(str, c)) for c in el), '|', en[i][:70])
