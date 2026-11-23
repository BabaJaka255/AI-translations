import numpy as np, json, sys
S = np.load('view/ocr_scores.npy'); cands = json.load(open('view/ocr_cands.json'))
a, b = int(sys.argv[1]), int(sys.argv[2])
sub = S[a:b]; n, m = sub.shape
best = np.full((n, m), -1e9); back = np.zeros((n, m), int)
best[0] = sub[0]
for i in range(1, n):
    # prefix max of best[i-1] over k<j
    pm = np.maximum.accumulate(best[i-1]); pa = np.zeros(m, int)
    arg = 0
    am = np.zeros(m, int); cur = -1e18
    for j in range(m):
        if best[i-1][j] > cur: cur = best[i-1][j]; arg = j
        am[j] = arg
    prev = np.concatenate([[-1e9], pm[:-1]]); parg = np.concatenate([[0], am[:-1]])
    best[i] = sub[i] + prev; back[i] = parg
j = int(best[-1].argmax()); path = [j]
for i in range(n - 1, 0, -1):
    j = back[i][j]; path.append(int(j))
path = path[::-1]
out = {}
for i, j in enumerate(path):
    top = int(sub[i].argmax())
    out[a + i] = [cands[j][1], float(sub[i][j]), cands[top][1], float(sub[i][top])]
json.dump(out, open('view/kanji_dp.json', 'w'), ensure_ascii=False)
for r in range(a, b, 16):
    print(r, ''.join(out[k][0] for k in range(r, min(b, r + 16))), ' ', ''.join('!' if out[k][1] < 0.55 else '.' for k in range(r, min(b, r+16))))
