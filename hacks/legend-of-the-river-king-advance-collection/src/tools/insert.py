# Full build: font + VWF hook, menus, then every translated string re-encoded, word-wrapped, placed in
# free space and repointed.
import sys, json, re, struct, zlib
sys.path.insert(0, '.')
import encode_en, vwf, menus, gfx, pickle, namekbd, tilestr, g3panel, g3win, g4win, g3uo, g3yn, gbasigns, g4memo, gbalogos
from build import GAMES, FREE_CODE, Rom, hook

PAGE = '{fa}{fb f0}{f2}'
LINE_PX = {'g4': 128, 'g3': 128}
UOCCHI_PX = 136
VAR_PX = {'f6': 36, 'f9': 48}

def load_T(game):
    T = {}
    if game == 'g4':
        import tr_g4_a, tr_g4_b, tr_g4_c
        for m in (tr_g4_a, tr_g4_b, tr_g4_c): T.update(m.T)
    else:
        import importlib
        for n in ('tr_g3_a', 'tr_g3_b'):
            try: T.update(importlib.import_module(n).T)
            except ImportError: pass
    return T

TOK = re.compile(r'(?:\{[^}]*\}|[^\s{])+|\s+')
SUB = re.compile(r'\{[^}]*\}|[^{]+')

def tok_px(t, game):
    if not t.isspace() and len(SUB.findall(t)) > 1:
        return sum(tok_px(u, game) for u in SUB.findall(t))
    if t.startswith('{'):
        h = t[1:-1].split()
        if h and h[0] in VAR_PX: return VAR_PX[h[0]]
        if h and h[0] in ('c8', 'c9', 'b0', 'c5'): return 8
        return 0
    if t.isspace(): return 3 * len(t)
    return sum(encode_en.WIDTHS[game][encode_en.CODES.get(c, 0x95 if c == '…' else 0)] for c in t)

# where a page has to be split, prefer sentence ends, then clause ends, over a cut after the second line
SENT = re.compile(r'(?<=[.!?~)"])(?:\{[^}]*\})* +(?=\S)')
CLAUSE = re.compile(r'(?<=,) +(?=\S)')

def split_page(text, game, maxpx, lines_per_page=2):
    """Cut an overflowing page (no {f1}) at sentence/clause boundaries so that every page fits.
    Returns a list of page texts, or None when no such cut exists."""
    cuts = {m.end(): 0 for m in CLAUSE.finditer(text)}
    cuts.update({m.end(): -1 for m in SENT.finditer(text)})
    pos = [0] + sorted(cuts) + [len(text)]
    fits = lambda a, b: len(wrap_page(text[a:b].strip(), game, maxpx, lines_per_page, smart=False)[0]) <= lines_per_page \
        and len(wrap_page(text[a:b].strip(), game, maxpx, lines_per_page, smart=False)) == 1
    best = {0: (0, [])}
    for j in range(1, len(pos)):
        for i in range(j):
            if pos[i] in best and fits(pos[i], pos[j]):
                c = best[pos[i]][0] + 10 + (cuts.get(pos[j], 0) + 1) * 3 * (j < len(pos) - 1)
                if pos[j] not in best or c < best[pos[j]][0]:
                    best[pos[j]] = (c, best[pos[i]][1] + [(pos[i], pos[j])])
    if len(text) not in best: return None
    return [text[a:b].strip() for a, b in best[len(text)][1]]

def wrap_page(text, game, maxpx, lines_per_page=2, smart=True):
    """Wrap one page of text (no page breaks inside). Returns list of pages, each a list of lines."""
    if smart and '{f1}' not in text:
        pages = wrap_page(text, game, maxpx, lines_per_page, smart=False)
        if len(pages) > 1:
            parts = split_page(text, game, maxpx, lines_per_page)
            if parts and len(parts) <= len(pages) + 1:
                return [wrap_page(t, game, maxpx, lines_per_page, smart=False)[0] for t in parts]
        return pages
    lines = []
    for seg in text.split('{f1}'):
        cur, w = '', 0
        for t in TOK.findall(seg):
            tw = tok_px(t, game)
            if t.isspace():
                if cur: cur += t; w += tw
                continue
            # tokens glued to the previous word (no space before) are handled as one unit by TOK already
            if w + tw > maxpx and cur.strip():
                lines.append(cur.rstrip()); cur, w = '', 0
            cur += t; w += tw
        lines.append(cur.rstrip())
    return [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]

# split a dialogue string at page-break tokens, keep the breaks
BREAK = re.compile(r'(\{fa\}\{fb f0\}\{f2\}|\{fb 80\}\{f2\}|\{fb f0\}\{f2\}|\{f7\}\{f2\})')
TAIL = re.compile(r'((?:\{(?:f7|f0|fb f0|fb 80|ff|fe|f4|f5)\})+)$')

def wrap(text, game, maxpx=None):
    maxpx = maxpx or LINE_PX[game]
    # keep emote symbols (sweat, anger, heart, note) on the line of the word before them
    text = re.sub(r' +(\{(?:c8|c9|b0|c5)\})', r'\1', text)
    parts = BREAK.split(text)
    out = ''
    for i in range(0, len(parts), 2):
        body = parts[i]
        brk = parts[i + 1] if i + 1 < len(parts) else ''
        m = TAIL.search(body)
        tail = m.group(1) if m else ''
        if tail: body = body[:m.start()]
        # leading control codes (sound, speed) stay in front
        nl_end = body.endswith('{f1}')
        if nl_end: body = body[:-4]
        pages = wrap_page(body, game, maxpx, smart=not nl_end)
        if nl_end:
            if len(pages[-1]) > 1: WARN.append('choice after 2 lines: ' + text[:50])
            pages[-1].append('')
        out += PAGE.join('{f1}'.join(p) for p in pages) + tail + brk
    return out

PARAM = {0xf8, 0xf9, 0xfb, 0xfc, 0xfd}
def terminate(b):
    i = 0; ended = False
    while i < len(b):
        c = b[i]
        if c in PARAM: i += 2; ended = False; continue
        ended = (c == 0xf0); i += 1
    return b if ended else b + bytes([0xf0])

def is_dialogue(addr, game):
    if game == 'g4':
        return 0x0fd70 <= addr < 0x10cf0 and addr not in LISTS_G4 or addr >= 0x11860
    return True

LISTS_G4 = set()
WARN = []

def build_all(src, out, games=('g4', 'g3'), report=None):
    rom = Rom(open(src, 'rb').read())
    code_at = FREE_CODE
    for g, info in GAMES.items():
        for c, t in encode_en.font_tiles().items(): rom.w(info['font'] + c * 32, t)
        wa = code_at; rom.w(wa, encode_en.WIDTHS[g]); code_at += 256
        var = 0x03006ff0 if g == 'g4' else 0x03006ff4
        c = vwf.assemble(vwf.vwf_src(info['st'], var, 0x08000000 + wa, 0x08000000 + info['font']), 0x08000000 + code_at)
        rom.w(code_at, c); hook(rom, info['blit'], 0x08000000 + code_at); code_at += (len(c) + 3) & ~3
    warn = WARN
    for g in games:
        T = load_T(g)
        if g == 'g4':
            T.update(menus.apply(rom.d))
            gfx.apply(rom, pickle.load(open('allrefs.pkl', 'rb')))
            namekbd.apply(rom, pickle.load(open('allrefs.pkl', 'rb')), 'g4')
            tilestr.apply_g4_title(rom, pickle.load(open('allrefs.pkl', 'rb')))
            tilestr.apply_g4_file(rom, pickle.load(open('allrefs.pkl', 'rb')))
            g4win.apply(rom, pickle.load(open('allrefs.pkl', 'rb')))
            g4memo.apply(rom, pickle.load(open('allrefs.pkl', 'rb')))
            print('sign tilesets', gbasigns.apply(rom, pickle.load(open('allrefs.pkl', 'rb'))))   # both games
            print('logo pieces', gbalogos.apply(rom, pickle.load(open('allrefs.pkl', 'rb'))))   # start, select, both titles
        if g == 'g3':
            namekbd.apply(rom, pickle.load(open('allrefs.pkl', 'rb')), 'g3')
            tilestr.apply_g3_file(rom, pickle.load(open('allrefs.pkl', 'rb')))
            tilestr.apply_g3_title(rom, pickle.load(open('allrefs.pkl', 'rb')))
            g3panel.apply(rom, pickle.load(open('allrefs.pkl', 'rb')))
            print('g3 window tiles left', g3win.apply(rom, pickle.load(open('allrefs.pkl', 'rb'))))
            g3yn.apply(rom)
            print('g3 uocchi tiles left', g3uo.apply(rom, pickle.load(open('allrefs.pkl', 'rb'))))
        strings = {x['addr']: x for x in json.load(open('%s_jp.json' % g))}
        for addr, text in sorted(T.items()):
            if addr not in strings:
                warn.append('%s %x: not a string start' % (g, addr)); continue
            x = strings[addr]
            if '\n' in text: warn.append('%s %x: newline in text' % (g, addr))
            t2 = wrap(text, g) if ('{f7}' in text or PAGE in text or '{fb' in text) else text
            if g == 'g3' and 0x1b5f1 <= addr < 0x1b75c:
                t2 = wrap(text, g, UOCCHI_PX)   # Uocchi help line under the tank: two lines, no page breaks
            raw = bytes.fromhex(x['raw'])
            sp = encode_en.SPACE[g]
            if g == 'g3' and (raw.endswith(bytes([sp, 0xf0])) or 0x1e2e2 <= addr <= 0x1e49a) and t2.endswith('{f0}'):
                # fixed-width field: the Japanese pads with spaces to wipe the old text; pad to the same width
                cells = sum(1 for c in raw[:-1] if c not in (0x8d, 0x8e) and c < 0xf0)
                body = t2[:-4]
                w = sum(tok_px(u, g) for u in TOK.findall(body))
                if w > cells * 8: warn.append('%s %x: %r is %dpx, field %dpx' % (g, addr, body, w, cells * 8))
                body += ' ' * max(0, -(-(cells * 8 - w) // 3))
                t2 = body + '{f0}'
            try:
                b = encode_en.encode(t2, g)
            except KeyError as e:
                warn.append('%s %x: bad char %r' % (g, addr, e.args[0])); continue
            b = terminate(b)
            a = rom.put(b)
            for ref in x['refs']:
                rom.w(ref, struct.pack('<I', 0x08000000 + a))
    open(out, 'wb').write(rom.d)
    if report:
        open(report, 'w').write('\n'.join(warn))
    return rom, warn

if __name__ == '__main__':
    rom, warn = build_all('../rom/k34.gba', 'k34_en.gba')
    print('text end', hex(rom.alloc), 'warnings', len(warn))
    for w in warn[:40]: print(w)
