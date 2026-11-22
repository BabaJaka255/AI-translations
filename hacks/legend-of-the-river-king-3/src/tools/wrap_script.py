"""Merge text/script_en_*.txt into out/script.json, wrapping dialogue to the text box.

Box: 36 half-width columns, 3 lines per page; a speaker line 【...】 takes the first line of the first page.
"|" = new page, "/" = forced line break, a leading "=" means use the text as written.
"""
import glob, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS, LINES = 36, 3
VAR_W = {'03': 6, '04': 10, '05': 2, '06': 3, '07': 6, '0A': 3, '0B': 3}

def width(s):
    w = 0; i = 0
    while i < len(s):
        m = re.match(r'\[([0-9A-F]{2})\]', s[i:])
        if m: w += VAR_W.get(m.group(1), 0); i += 4; continue
        w += 2 if ord(s[i]) > 0x7f else 1; i += 1
    return w

def wrap_para(text, first_lines):
    """Wrap one paragraph into lines; '/' forces a break."""
    lines = []
    for chunk in text.split('/'):
        words = chunk.split(' '); cur = ''
        for wd in words:
            cand = wd if not cur else cur + ' ' + wd
            if width(cand) <= COLS or not cur: cur = cand
            else: lines.append(cur); cur = wd
        lines.append(cur)
    return lines

def fmt(en, jp):
    end = '[02]' if jp.endswith('[02]') else ''
    if en.startswith('='):
        s = en[1:].replace('/', '\n')
        return s if s.endswith('[02]') or not end else s + end
    speaker = None
    m = re.match(r'(【.*?】)/?', en)
    if m: speaker = m.group(1); en = en[m.end():]
    pages = []
    first = True
    for para in en.split('|'):
        lines = wrap_para(para.strip(), None)
        avail = LINES - (1 if first and speaker else 0)
        while lines:
            take, lines = lines[:avail], lines[avail:]
            pages.append(take); first = False; avail = LINES
    out = []
    for k, pg in enumerate(pages):
        body = '\n'.join(pg)
        if k == 0 and speaker: body = speaker + '\n' + body
        out.append(body)
    s = '[02]'.join(out)
    return s + end if end else s

def load_en():
    tr = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'text', 'script_en_*.txt'))):
        for line in open(f, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line or line.startswith('#'): continue
            k, v = line.split('\t', 1)
            tr[int(k)] = v
    return tr

def main():
    jp = json.load(open(os.path.join(ROOT, 'out', 'script_jp.json')))
    tr = load_en(); bad = []
    for i, e in enumerate(jp):
        if i in tr:
            e['en'] = fmt(tr[i], e['jp'])
            for ln in re.split(r'\n|\[02\]', e['en']):
                if width(ln) > COLS: bad.append((i, ln))
    json.dump(jp, open(os.path.join(ROOT, 'out', 'script.json'), 'w'), ensure_ascii=False, indent=1)
    for i, ln in bad: print('WIDE %04d %d %s' % (i, width(ln), ln))
    print(len(tr), 'translated;', len(bad), 'over-wide lines')

if __name__ == '__main__':
    main()
