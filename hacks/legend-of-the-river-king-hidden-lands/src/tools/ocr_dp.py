"""Kanji glyphs are stored in Shift-JIS order: assign them by a monotone DP over match scores."""
import sys, json, numpy as np
sys.path.insert(0, 'tools')
from ocr_font import game_glyphs, norm, render
from PIL import ImageFont
gl = game_glyphs()
font = ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', 15)
chars = []
for hi in list(range(0x88, 0xa0)) + list(range(0xe0, 0xeb)):
    for lo in range(0x40, 0xfd):
        if hi == 0x88 and lo < 0x9f: continue
        try: ch = bytes([hi, lo]).decode('cp932')
        except: continue
        if len(ch) == 1: chars.append(ch)
cv = []; keep = []
for ch in chars:
    v = norm(render(ch, font))
    if v is not None: cv.append(v); keep.append(ch)
C = np.array(cv)
A, B = int(sys.argv[1]), int(sys.argv[2])
G = np.array([norm(np.where(gl[i] > 0.55, gl[i], 0)) for i in range(A, B)])
S = G @ C.T                     # (glyphs, chars)
n, m = S.shape
dp = np.full((n, m), -1e9); bk = np.zeros((n, m), int)
dp[0] = S[0]
for i in range(1, n):
    prev = dp[i - 1]
    pm = np.maximum.accumulate(prev)               # best over j' <= j
    pa = np.zeros(m, int); best = -1e18; bi = 0
    arg = np.zeros(m, int)
    # argmax prefix
    idx = np.arange(m); am = np.where(prev == pm, idx, 0); am = np.maximum.accumulate(am)
    dp[i, 1:] = pm[:-1] + S[i, 1:]
    bk[i, 1:] = am[:-1]
j = int(np.argmax(dp[-1])); out = [None] * n
for i in range(n - 1, -1, -1):
    out[i] = j; j = bk[i, j]
res = {A + i: (keep[out[i]], float(S[i, out[i]]), keep[int(np.argmax(S[i]))]) for i in range(n)}
json.dump(res, open(f'ocr_dp_{A}_{B}.json', 'w'), ensure_ascii=False)
for r in range(A, B, 16):
    print(f'{r:4d} ' + ''.join(res[k][0] for k in range(r, min(r + 16, B))) + '  low: ' +
          ' '.join(f'{k}:{res[k][0]}/{res[k][2]}:{res[k][1]:.2f}' for k in range(r, min(r + 16, B)) if res[k][1] < 0.85))
