"""Build the patched disc image: patched executable + English font cells in COMM.TIM."""
import sys, struct, json
sys.path.insert(0, 'tools')
import numpy as np
import tim
from cdsector import write_file
from hook import engine, ENG_BASE
from font_en import build as build_font
from strings import BASE
EXE_LBA, COMM_LBA = 19494, 20015
NOTE_LBA, TITLE_LBA = 20274, 20612
T = 0x8000f800   # RAM address of exe file offset 0

def encode_en(s, dictionary=None):
    """English text -> list of words. {X} controls pass through as 0xFFFX, {hex} raw word, {>N} tab to N px."""
    out = []; i = 0; buf = ''
    def flush():
        nonlocal buf
        for k in range(0, len(buf) - 1, 2):
            out.append(ord(buf[k]) | ord(buf[k + 1]) << 8)
        if len(buf) % 2: out.append(0x1f00 | ord(buf[-1]))
        buf = ''
    while i < len(s):
        if s[i] == '{':
            j = s.index('}', i); tok = s[i + 1:j]; flush()
            if tok[0] == '>': out.append(0x1e00 | int(tok[1:])); i = j + 1; continue
            out.append(0xfff0 | int(tok, 16) if len(tok) == 1 else int(tok, 16)); i = j + 1
        else:
            buf += s[i]; i += 1
    flush()
    return out

def patch_font(comm):
    cells, widths = build_font()
    comm = bytearray(comm)
    for c, cell in cells.items():
        idx = ENG_BASE + c - 0x21
        p, r = divmod(idx, 256)
        base = tim.parse(comm, 33312 * (p + 1))['img']['off']
        for y in range(16):
            row = base + ((r // 16) * 16 + y) * 128 + (r % 16) * 8
            for x in range(0, 16, 2):
                comm[row + x // 2] = cell[y, x] | cell[y, x + 1] << 4
    return bytes(comm), [widths[c] for c in range(0x21, 0x7f)]

# small layout tweaks: RAM address -> instruction word
# Command menu cursor: right column cursor 41px over instead of 40 (col is 0 or 1: x = 142 + (-col & 41)),
# centred between "Gear" and the right column text at {>40}.
CODE_PATCHES = {
    0x8003b45c: 'subu $v0, $zero, $a1\nandi $v0, $v0, 41\naddiu $v0, $v0, 0x8e\nnop',
    0x8003b7dc: 'subu $v0, $zero, $v1\nandi $v0, $v0, 41\naddiu $v0, $v0, 0x8e\nnop',
    0x800765b8: 'addiu $v0, $v0, 6',      # postcard keyboard cursor 2px left (rows 2-6)
}
LAYOUT = {
    0x80015d6c: 0x34020020,   # status window weather/time icon: y 0x10 -> 0x20 (HP row) to free the area-name row
}

def build(src_bin, out_bin, texts=None):
    """texts=None: insert the whole English script (tools/insert.py); else a test list of (addr, slot, english)."""
    img = bytearray(open(src_bin, 'rb').read())
    comm, widths = patch_font(open('files/TIM/COMM.TIM', 'rb').read())
    if texts is None:
        import insert
        exe, dict_ptr, dic, rep, words = insert.insert()
        # a string that neither fits its slot nor can be moved would stay Japanese: never ship that
        assert not rep['stuck'] and not rep['homeless'], ('untranslated strings', rep['stuck'], rep['homeless'])
    else:
        exe = bytearray(open('files/SLPS_015.36', 'rb').read()); dict_ptr = 0x80000000; rep = None
        for addr, slot, s in texts:
            w = encode_en(s) + [0xffff]
            assert len(w) <= slot, (s, len(w), slot)
            o = addr - T
            exe[o:o + 2 * len(w)] = struct.pack('<%dH' % len(w), *w)
    patches, dw, end = engine(widths, dict_ptr)
    for a, b in patches.items():
        exe[a - T:a - T + len(b)] = b
    import names
    for a, b in names.patch().items():
        exe[a - T:a - T + len(b)] = b
    for a, w in LAYOUT.items():
        struct.pack_into('<I', exe, a - T, w)
    from hook import asm
    for a, src in CODE_PATCHES.items():
        b = asm(src, a); exe[a - T:a - T + len(b)] = b
    import debug                       # compact secret-name gift + Select+step area warp (test helper)
    for a, b in debug.patch().items():
        exe[a - T:a - T + len(b)] = b
    write_file(img, EXE_LBA, bytes(exe))
    open('build_exe.bin', 'wb').write(exe)
    import labels, title, note
    write_file(img, COMM_LBA, labels.patch(comm))
    write_file(img, TITLE_LBA, title.build(open('files/TIM/TITLE.TIM', 'rb').read()))
    write_file(img, NOTE_LBA, note.build(open('files/TIM/NOTE.TIM', 'rb').read()))
    import signs
    lba = {l.split()[2][5:-2]: int(l.split()[0]) for l in open('files.txt') if l.split()[2].startswith('/MAP/')}
    maps = signs.build_all(lambda f: open('files/MAP/' + f, 'rb').read())
    for f, (data, hits) in maps.items():
        assert len(data) == len(open('files/MAP/' + f, 'rb').read())
        write_file(img, lba[f], data)
    if rep is not None: rep['signs'] = sum(len(h) for _, h in maps.values())
    import staff
    elba = {l.split()[2][8:-2]: int(l.split()[0]) for l in open('files.txt') if l.split()[2].startswith('/ENDING/')}
    for f, data in staff.build(lambda f: open('files/ENDING/' + f, 'rb').read()).items():
        assert len(data) == len(open('files/ENDING/' + f, 'rb').read())
        write_file(img, elba[f], data)
    open(out_bin, 'wb').write(img)
    return rep

if __name__ == '__main__':
    rep = build('orig.bin', sys.argv[1] if len(sys.argv) > 1 else 'test.bin')
    print({k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()})
