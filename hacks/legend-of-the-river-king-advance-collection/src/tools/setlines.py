# Replace whole translation entries "0xADDR: <expr>," in tr_*.py files. fixes file: lines "0xADDR: <expr>,"
import sys, re, glob
fix = {}
for ln in open(sys.argv[1], encoding='utf8'):
    m = re.match(r'(0x[0-9a-f]+):\s', ln)
    if m: fix[int(m.group(1), 16)] = ln.rstrip('\n')
done = set()
for f in sorted(glob.glob('work/tr_g%s_*.py' % sys.argv[2])):
    L = open(f, encoding='utf8').read().split('\n'); ch = False
    for i, ln in enumerate(L):
        m = re.match(r'(0x[0-9a-f]+):\s', ln)
        if m and int(m.group(1), 16) in fix:
            L[i] = fix[int(m.group(1), 16)]; done.add(int(m.group(1), 16)); ch = True
    if ch: open(f, 'w', encoding='utf8').write('\n'.join(L))
print('applied', len(done), 'missing', [hex(a) for a in fix if a not in done])
