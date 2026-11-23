"""Translation memory from the SFC Sea King and Hikyou scripts: normalized JP -> EN."""
import csv, re, json, sys, os, collections
HUB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')   # the hacks/ folder of the hub repo
SRC = [os.path.join(HUB, 'super-legend-of-the-sea-king/src/script/%s.tsv' % n) for n in ('script', 'names', 'fish')]
SRC.append(os.path.join(HUB, 'legend-of-the-river-king-hidden-lands/src/script/script.tsv'))
import unicodedata
def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'\{[^}]*\}', '', s)
    s = s.replace('\\n', '').replace('\n', '')
    s = re.sub(r'[\s　]', '', s)
    s = s.replace('､', '、')
    return s
def load():
    tm = collections.defaultdict(list)
    for fn in SRC:
        try:
            rows = list(csv.reader(open(fn, encoding='utf-8'), delimiter='\t'))
        except FileNotFoundError: continue
        hdr = rows[0]
        ji, ei = hdr.index('japanese') if 'japanese' in hdr else 2, hdr.index('english') if 'english' in hdr else 3
        for r in rows[1:]:
            if len(r) <= max(ji, ei): continue
            j, e = r[ji], r[ei]
            if norm(j) and e.strip(): tm[norm(j)].append((e, fn.split('/')[-4] if 'hacks' in fn else fn))
    return tm
if __name__ == '__main__':
    tm = load()
    S = json.load(open('out/script_jp.json'))
    hit = 0; out = {}
    for o in S:
        k = norm(re.sub(r'\{[0-9A-F]:\d+\}', '', o['jp']))
        if k in tm:
            hit += 1; out[o['id']] = tm[k][0][0]
    print(len(tm), 'tm entries;', hit, 'of', len(S), 'strings matched')
    json.dump(out, open('out/tm_hits.json', 'w'), ensure_ascii=False, indent=0)
