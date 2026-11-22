"""Save screen messages: PAL's English sprite rectangles for the JP save screen.

Both programs build the save/load screen sprites (stride 0x2c, JP 0x46da48 / PAL 0x48e588) in one
setup routine (JP 0x35f860, PAL 0x3612c0) from constants; PAL picks per-language values (0x4990a8,
0 = English). This runs both routines in an emulator (unicorn, with the R5900 3-operand mult/mult1
done in hooks; the routines call nothing), diffs the sprite tables and writes the English values as
a C table (code/subtitle/savefix.h) that my_save_fix applies after the JP routine returns.

The load screen's message sprites (JP 0x35bf80 / PAL 0x35d358, arrays 0x46a030 / 0x47eb60) get the
same treatment. Only fields that differ are written; sprites PAL points at save4 (French/German only)
are left out. PAL also draws a few extra sprites in some states (my_save_draw / my_load_draw in sub.c).
usage: b7_savefix.py  (needs: pip install unicorn)
"""
import os, struct
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_0, UC_MIPS_REG_LO, UC_MIPS_REG_HI, UC_MIPS_REG_RA, UC_MIPS_REG_SP, UC_MIPS_REG_GP

G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
R = [UC_MIPS_REG_0 + i for i in range(32)]
N = 62


def s32(x): x &= 0xffffffff; return x - (1 << 32) if x & 0x80000000 else x
def sx(x): return s32(x) & 0xffffffffffffffff


def elf_segs(d):
    ph = struct.unpack_from('<I', d, 28)[0]; n = struct.unpack_from('<H', d, 44)[0]
    for i in range(n):
        t, o, va, _, fs, _, _, _ = struct.unpack_from('<8I', d, ph + 32 * i)
        if t == 1: yield va, d[o:o + fs]


def mulhook(w, lo1):
    fn = w & 63; rs = (w >> 21) & 31; rt = (w >> 16) & 31; rd = (w >> 11) & 31; mmi = w >> 26 == 0x1c
    def h(u, *_):
        a = u.reg_read(R[rs]); b = u.reg_read(R[rt])
        if fn in (0x18, 0x19):
            p = s32(a) * s32(b) if fn == 0x18 else (a & 0xffffffff) * (b & 0xffffffff)
            lo, hi = sx(p), sx(p >> 32)
            if mmi: lo1[:] = [lo, hi]
            else: u.reg_write(UC_MIPS_REG_LO, lo); u.reg_write(UC_MIPS_REG_HI, hi)
            if rd: u.reg_write(R[rd], lo)
        elif fn == 0x12: u.reg_write(R[rd], lo1[0])
        elif fn == 0x10: u.reg_write(R[rd], lo1[1])
        else: raise NotImplementedError(hex(w))
    return h


def run_setup(elf, gp, fn, pokes):
    d = open(elf, 'rb').read()
    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 | UC_MODE_LITTLE_ENDIAN); mu.mem_map(0, 0x2000000); lo1 = [0, 0]
    for va, b in elf_segs(d):
        mu.mem_write(va, b)
        for i, w in enumerate(struct.unpack_from('<%dI' % (len(b) // 4), b)):
            if (w >> 26 == 0 and w & 63 in (0x18, 0x19) and (w >> 11) & 31 and not (w >> 6) & 31) or \
               (w >> 26 == 0x1c and w & 63 in (0x18, 0x19, 0x10, 0x12)):
                a = va + 4 * i; mu.mem_write(a, bytes(4)); mu.hook_add(UC_HOOK_CODE, mulhook(w, lo1), begin=a, end=a)
    for a, v in pokes.items(): mu.mem_write(a, struct.pack('<I', v))
    stop = 0x1ff0000
    mu.reg_write(UC_MIPS_REG_RA, stop); mu.reg_write(UC_MIPS_REG_SP, 0x1f00000); mu.reg_write(UC_MIPS_REG_GP, gp)
    mu.emu_start(fn, stop, count=20_000_000)
    return mu


def diff(jfn, pfn, jarr, parr, n, jtags, ptags):
    """-> fields [(sprite, offset, PAL value)], handles [(sprite, JP handle variable)]"""
    jm = run_setup(os.path.join(G, 'rom/jp/SLPM_650.08'), 0x4f4df0, jfn, jtags)
    pm = run_setup(os.path.join(G, 'rom/pal/SLES_501.09'), 0x520b70, pfn, ptags)
    fields, handles = [], []
    for k in range(n):
        a = bytes(jm.mem_read(jarr + 0x2c * k, 0x2c)); b = bytes(pm.mem_read(parr + 0x2c * k, 0x2c))
        ha, hb = struct.unpack_from('<I', a, 0xc)[0], struct.unpack_from('<I', b, 0xc)[0]
        if hb == SAVE4: continue                # save4: French/German sheets only
        if ha != hb: handles.append((k, hb))
        for o in range(0, 0x2c, 2):
            if o in (0xc, 0xe): continue
            x, y = struct.unpack_from('<h', a, o)[0], struct.unpack_from('<h', b, o)[0]
            if x != y: fields.append((k, o, y))
    return fields, handles


# texture handle variables, tagged with the JP variable's address in both programs
JTAGS = {a: a for a in list(range(0x46a8f0, 0x46a940, 4)) + list(range(0x46f2b0, 0x46f350, 4))}
PTAGS = {a: a - 0x14b30 for a in range(0x47f420, 0x47f470, 4)}          # load screen sheets
PTAGS.update({a: a - 0x20b40 for a in range(0x48fdf0, 0x48fe90, 4)})    # save screen sheets (save1 0x48fe64 = JP 0x46f324)
SAVE4 = 0x46f330


def tables():
    save = diff(0x35f860, 0x3612c0, 0x46da48, 0x48e588, 62, JTAGS, PTAGS)
    load = diff(0x35bf80, 0x35d358, 0x46a030, 0x47eb60, 52, JTAGS, PTAGS)
    return save, load


def c_table(name, fields, handles):
    out = ['static const short %s[][3] = {' % name] + ['    {%d, 0x%x, %d},' % f for f in fields] + ['};']
    out += ['static const int %s_handle[][2] = {' % name] + ['    {%d, 0x%x},' % h for h in handles]
    if not handles: out.append('    {-1, 0},')
    return out + ['};']


if __name__ == '__main__':
    (sf, sh), (lf, lh) = tables()
    out = ['/* generated by tools/b7_savefix.py: PAL English sprite fields for the save and load screens',
           '   ({sprite, byte offset, value}; {sprite, JP texture handle variable}) */']
    out += c_table('save_fix', sf, sh) + c_table('load_fix', lf, lh) + ['']
    open(os.path.join(G, 'code/subtitle/savefix.h'), 'w').write('\n'.join(out))
    print(f'save: {len(sf)} fields, {len(sh)} handles; load: {len(lf)} fields, {len(lh)} handles')
