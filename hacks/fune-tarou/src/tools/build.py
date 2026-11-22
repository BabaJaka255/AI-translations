"""Build the English ROM and patch.
python3 tools/build.py [OUT.sfc]   (ROM from rom/Fune Tarou (Japan).sfc or $FT_ROM)
Writes build/fune-tarou-en.sfc and build/Fune Tarou (English).bps unless OUT is given."""
import json, os, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ftlib import *
import engine

E1 = NEW_TEXT - 0x10000   # ROM offset in bank C1 + E1 = same address in bank E1
RELOC = 0x218000          # $E1:8000..$E1:FFFF: room for relocated strings and lists (bank E1 is text only)


class Space:
    def __init__(s, start, end):
        s.p = start; s.end = end
    def take(s, n):
        a = s.p; s.p += n
        assert s.p <= s.end, 'out of relocation space'
        return a


def put16(rom, off, val, expect=None):
    if expect is not None:
        assert rom[off] | rom[off + 1] << 8 == expect, 'operand at %05X is %04X, expected %04X' % (off, rom[off] | rom[off + 1] << 8, expect)
    rom[off] = val & 0xFF; rom[off + 1] = (val >> 8) & 0xFF


def put8(rom, off, val, expect=None):
    if expect is not None:
        assert rom[off] == expect, 'byte at %05X is %02X, expected %02X' % (off, rom[off], expect)
    rom[off] = val


def check(ok, msg, errors):
    if not ok:
        errors.append(msg)


# ---- list layouts: where each list is drawn and how the English version is laid out
# keys: stride/base operand sites, count and column operands (ROM offsets of the operand bytes)
LISTS = {
    # record screen title: fish name, $C0:70C2 (x17), col 7 row 4, 16 columns
    'fish_title': dict(stride_op=0x70C3, base_op=0x70CE, col_op=0x70D4, cnt_op=0x70E0,
                       old=(17, 0x4588, 7, 0x10), new=(17, None, 7, 0x10), align='center'),
    # catch screen: fish name at col 1 row 15, 12 columns; x12 done with shifts at $C0:7D19 -> x16
    'fish_name': dict(base_op=None, cnt_op=0x7D39, old=(12, 0x510B, 1, 0x0C), new=(16, None, 1, 0x0F), align='left'),
    # stage labels ($C0:7F54 bubble): mode (bottom left), chapter (top right), spot (middle), island (bottom right)
    'mode': dict(stride_op=0x7E63, base_op=0x7E6E, col_op=0x7E74, cnt_op=0x7E80,
                 old=(15, 0x4ECC, 2, 0x0F), new=(15, None, 1, 0x0F), align='left', label=True),
    'chapter': dict(stride_op=0x7E9B, base_op=0x7EA6, col_op=0x7EAC, cnt_op=0x7EB8,
                    old=(19, 0x5387, 0x0C, 0x13), new=(24, None, 0x08, 0x18), align='right', label=True),
    'spot': dict(stride_op=0x7ED4, base_op=0x7EDF, col_op=0x7EE5, cnt_op=0x7EFC,
                 old=(12, 0x585A, 0x0A, 0x0C), new=(20, None, 0x06, 0x14), align='center', label=True),
    'island': dict(stride_op=0x7F18, base_op=0x7F23, col_op=0x7F29, cnt_op=0x7F35,
                   old=(11, 0x5B66, 0x14, 0x0B), new=(15, None, 0x11, 0x0F), align='right', label=True),
    # bait/lure window, x20 with shifts at $C0:7CAA, col 6 row 21, 20 columns: stays in place
    'bait': dict(inplace=True, old=(20, 0x4F17, 6, 0x14), new=(20, 0x4F17, 6, 0x14), align='center'),
}


def lay_out(en, width, align, label):
    if label:
        en = en.replace(' ', ' ')      # a plain space would end the label bubble early
    n = len(en)
    if align == 'left':
        s = en + ' ' * (width - n)
    elif align == 'right':
        s = ' ' * (width - n - (1 if label else 0)) + en + (' ' if label else '')
    else:
        left = (width - n) // 2
        s = ' ' * left + en + ' ' * (width - n - left)
    return s


def insert_lists(rom, lists, space, errors):
    for name, L in LISTS.items():
        data = lists[name]
        ostride, obase, ocol, ocnt = L['old']
        stride, base, col, cnt = L['new']
        width = cnt
        blob = bytearray()
        for e in data['entries']:
            en = e['en']
            if len(en) > width - (1 if L.get('label') else 0):
                errors.append('%s: "%s" is %d columns, limit %d' % (e['id'], en, len(en), width - (1 if L.get('label') else 0)))
                en = en[:width - 1]
            s = lay_out(en, width, L['align'], L.get('label'))
            b = encode_en(s)
            assert len(b) == width, (e['id'], s)
            blob += b + b' ' * (stride - width)
        if L.get('inplace'):
            off = NEW_TEXT + obase
            assert len(blob) == ostride * data['count']
            rom[off:off + len(blob)] = blob
            continue
        addr = space.take(len(blob) + 2)
        rom[addr:addr + len(blob)] = blob
        rom[addr + len(blob):addr + len(blob) + 2] = b'  '     # label measuring stops at a space
        new_base = addr & 0xFFFF
        if name == 'fish_name':
            # $C0:7D19: LDA $0B96 / ASL / ASL / STA $08B7 / ASL / CLC / ADC $08B7 / ADC #$510B
            #        -> LDA $0B96 / ASL x4 / NOP x6 / ADC #base  (x16, carry is clear after ASL of a small id)
            o = 0x7D19
            assert rom[o:o + 16] == bytes.fromhex('ad960b0a0a8db7080a186db708690b51')
            rom[o:o + 16] = bytes.fromhex('ad960b0a0a0a0a18eaeaeaeaea69') + bytes([new_base & 0xFF, new_base >> 8])
        else:
            put8(rom, L['stride_op'], stride, ostride)
            put16(rom, L['base_op'], new_base, obase)
            put16(rom, L['col_op'], col, ocol)
        put16(rom, L['cnt_op'], cnt, ocnt)


def insert_strings(strings, rom, space, errors):
    for e in strings['entries']:
        off = int(e['offset'], 16)
        en = e['en']
        if not en:
            errors.append('%s: no English' % e['id']); continue
        b = encode_en(en) + bytes([END])
        if e['id'] == 'save_lost':
            # keep both entry points ($4200, $4210): the text must start at $4211 or later
            assert en.startswith('\n' * 11)
            body = encode_en(en[11:].lstrip(' '))
            pad = 0x11 - 0x0B
            blk = encode_en('\n' * 11) + b' ' * pad + body + bytes([END])
            check(len(blk) <= e['length'], 'save_lost: too long (%d > %d)' % (len(blk), e['length']), errors)
            rom[E1 + off:E1 + off + len(blk)] = blk
            continue
        if len(b) <= e['length']:
            rom[E1 + off:E1 + off + len(b)] = b
        else:
            addr = space.take(len(b))
            rom[addr:addr + len(b)] = b
            for r in e['refs']:
                put16(rom, int(r, 16), addr & 0xFFFF, off & 0xFFFF)


def patch_catch_order(rom, lists):
    """Catch list (Y on the map) in English alphabetical order, read down the left column then the right.
    $C1:9106 maps cursor slot -> fish id + 1 (slots alternate left/right per row)."""
    names = [e['en'] for e in lists['fish_name']['entries'][:52]]
    order = sorted(range(52), key=lambda i: names[i].lower())
    slots = []
    for r in range(26):
        slots += [order[r], order[26 + r]]
    rom[0x19106:0x19106 + 52] = bytes(i + 1 for i in slots)
    return names, order


def cols_of(n):
    return len(encode_en(n))


def catch_list_text(names, order, width=12):
    """Two columns of 26 names, ^ = cursor slot; boxes are cols 1-14 and 17-30 (see engine.py)."""
    s = '\n' * 5 + '      Catch by Species\n\n\n>'      # '>': names in the compact font
    rows = []
    for r in range(26):
        a = names[order[r]]; b = names[order[26 + r]]
        assert cols_of(a) <= width and cols_of(b) <= width, (a, b)
        rows.append('   ^' + a + ' ' * (width + 3 - cols_of(a)) + '^' + b)
    return s + '\n\n'.join(rows)


def build(out_sfc=None):
    orig = load_rom()
    rom = engine.apply(orig)
    strings = json.load(open(os.path.join(GAME, 'script', 'strings.json'), encoding='utf-8'))
    lists = json.load(open(os.path.join(GAME, 'script', 'lists.json'), encoding='utf-8'))
    errors = []
    space = Space(RELOC, RELOC + 0x8000)
    names, order = patch_catch_order(rom, lists)
    for e in strings['entries']:
        if e['id'] == 'catch_list' and not e['en']:
            e['en'] = catch_list_text([short_name(n) for n in names], order)
    for e in strings['entries']:
        if e['id'] == 'intro':
            for ln in e['en'].split('\n'):
                check(engine.speech_width(ln) <= engine.SPEECH_WIDTH, 'intro: line too wide: %r' % ln, errors)
    insert_strings(strings, rom, space, errors)
    insert_lists(rom, lists, space, errors)
    rom = snes_checksum(rom)
    for m in errors:
        print('ERROR', m)
    out = out_sfc or os.path.join(GAME, 'build', 'fune-tarou-en.sfc')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'wb').write(rom)
    if not out_sfc:
        tk = os.path.join(GAME, 'toolkit')            # vendored copy in the published source
        sys.path.insert(0, os.environ.get('RHTK') or tk)
        from rhtk import patch
        bps = patch.bps_create(orig, rom, 'Fune Tarou (Japan) English translation')
        assert patch.bps_apply(orig, bps) == rom
        open(os.path.join(GAME, 'build', 'Fune Tarou (English).bps'), 'wb').write(bps)
        print('wrote Fune Tarou (English).bps (%d bytes)' % len(bps))
    print('wrote %s  CRC32 %08X  (%d relocation bytes used)' % (out, zlib.crc32(rom), space.p - RELOC))
    return rom, errors


# Catch list boxes hold 12 columns. Narrow ligatures ({01} ll, {02} il, {03} fi, data/font_en.txt)
# keep most names whole; the rest are abbreviated there only.
LIG = [('ll', '{01}'), ('il', '{02}'), ('fi', '{03}')]
SHORT = {'Blue Parrotfish': 'Blue Parrot', 'Jack Mackerel': 'J. Mackerel', 'Rainbow Runner': 'Rainbow Run.',
         'Black Trevally': 'Blk Trevally', 'Red Sea Bream': 'Red Seabream'}


def short_name(n, width=12):
    n = SHORT.get(n, n)
    if len(n) > width:
        for a, b in LIG:
            n = n.replace(a, b)
    return n


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else None)
