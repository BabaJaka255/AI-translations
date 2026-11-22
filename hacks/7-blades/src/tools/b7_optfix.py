"""Options screens (title options and the in-game one): PAL's English labels in the JP layout.

Both programs keep the options sprites in one table (80 records of 0x2c bytes, JP 0x478f3c / PAL
0x49cbcc: +0xc texture handle, +0x18 u0 v0 u1 v1, +0x20 x0 y0 x1 y1) and fill it from constants:
in-game setup JP 0x37bd10 / PAL 0x381780, title setup JP 0x368e08 / PAL 0x36da50, control-screen
values JP 0x37ded0 / PAL 0x383e18 (button glyphs and Hold/Switch/Normal/Reverse per the pad config
at JP 0x478830 / PAL 0x49c4c0). PAL draws from three sheets (FONT1-3_u); the JP program loads two.
PAL also adds rows JP does not have (Language, Text), so the JP rows stay where they are.

Rather than porting PAL's option code, every option sprite is translated as it is drawn: the JP
sprite builder 0x37b538 is reached through my_optspr (sub.c), which looks the record's JP sheet and
source rectangle up in opt_map (-> PAL sheet and rectangle, or hidden) and moves it by opt_dx[k]
(PAL's x offset for that slot); the width follows the English image. The pairs come from running
the setup routines of both programs in an emulator (unicorn, as b7_savefix.py) and pairing slot by
slot, plus the values the JP code writes at run time (MANUAL). Writes code/subtitle/optfix.h.
usage: b7_optfix.py  (needs: pip install unicorn)
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b7_savefix as S
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_RA, UC_MIPS_REG_SP, UC_MIPS_REG_GP

JELF = os.path.join(S.G, 'rom/jp/SLPM_650.08'); PELF = os.path.join(S.G, 'rom/pal/SLES_501.09')
JGP, PGP = 0x4f4df0, 0x520b70
JREC, PREC, N = 0x478f3c, 0x49cbcc, 91   # 0-79 options, 80-87 unused, 88-90 in-game "Return to title?" dialog
JTAG = {0x47a3f8: 0xAAA00000, 0x47a3fc: 0xAAA10000}                      # sheet handle variables
PTAG = {0x49e088: 0xAAA00000, 0x49e08c: 0xAAA10000, 0x49e090: 0xAAA20000}
JCFG, PCFG = 0x478830, 0x49c4c0
PADS = [0x20, 0x10, 0x40, 0x80, 4, 8, 0x100, 0x800, 2, 1]             # circle triangle cross square L1 R1 SELECT START R2 L2


def movhook(w):
    rs, rt, rd, z = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w & 63) == 0x0a
    def h(u, *_):
        if (u.reg_read(S.R[rt]) == 0) == z: u.reg_write(S.R[rd], u.reg_read(S.R[rs]))
    return h


def run(elf, gp, fn, pokes, stubs=()):
    """b7_savefix.run_setup plus movz/movn (not in unicorn's MIPS III core) and stubbed calls"""
    d = open(elf, 'rb').read(); lo1 = [0, 0]
    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 | UC_MODE_LITTLE_ENDIAN); mu.mem_map(0, 0x2000000)
    for va, b in S.elf_segs(d):
        mu.mem_write(va, b)
        for i, w in enumerate(struct.unpack_from('<%dI' % (len(b) // 4), b)):
            a = va + 4 * i
            if (w >> 26 == 0 and w & 63 in (0x18, 0x19) and (w >> 11) & 31 and not (w >> 6) & 31) or \
               (w >> 26 == 0x1c and w & 63 in (0x18, 0x19, 0x10, 0x12)):
                mu.mem_write(a, bytes(4)); mu.hook_add(UC_HOOK_CODE, S.mulhook(w, lo1), begin=a, end=a)
            elif w >> 26 == 0 and w & 63 in (0x0a, 0x0b) and not (w >> 6) & 31:
                mu.mem_write(a, bytes(4)); mu.hook_add(UC_HOOK_CODE, movhook(w), begin=a, end=a)
    for a, v in pokes.items(): mu.mem_write(a, struct.pack('<I', v))
    for a in stubs: mu.mem_write(a, struct.pack('<II', 0x03e00008, 0))
    mu.reg_write(UC_MIPS_REG_RA, 0x1ff0000); mu.reg_write(UC_MIPS_REG_SP, 0x1f00000); mu.reg_write(UC_MIPS_REG_GP, gp)
    mu.emu_start(fn, 0x1ff0000, count=20_000_000)
    return mu


def recs(m, base):
    out = []
    for k in range(N):
        b = bytes(m.mem_read(base + 0x2c * k, 0x2c)); h = struct.unpack_from('<I', b, 0xc)[0]
        out.append(((h >> 16) - 0xaaa0 if h >> 20 == 0xaaa else -1, struct.unpack_from('<8h', b, 0x18)))
    return out


def cfg(base, pads, tog):
    return {base + 4 * i: v for i, v in enumerate(list(pads) + list(tog))}


def screens():
    """[(JP records, PAL records)] for the in-game setup, the title setup and the control values per pad"""
    out = [(recs(run(JELF, JGP, 0x37bd10, {**JTAG, **cfg(JCFG, PADS, (0, 1, 1))}), JREC),
            recs(run(PELF, PGP, 0x381780, {**PTAG, **cfg(PCFG, PADS, (0, 1, 1))}), PREC)),
           (recs(run(JELF, JGP, 0x368e08, JTAG, [0x37bd10]), JREC),
            recs(run(PELF, PGP, 0x36da50, PTAG, [0x381780]), PREC))]
    for p in PADS:
        for t in (0, 1):
            out.append((recs(run(JELF, JGP, 0x37ded0, {**JTAG, **cfg(JCFG, [p] * 10, (t, t, t))}), JREC),
                        recs(run(PELF, PGP, 0x383e18, {**PTAG, **cfg(PCFG, [p] * 10, (t, t, t))}), PREC)))
    return out


# PAL x offset per slot (PAL's left column is 32 px wider, value columns moved); checked against the
# setups in main(). Slots 40/41 are the two-button glyphs, 74-79 the control-screen values.
DX = {7: 16, 9: -16, 10: -16, 11: -16, 15: -8, 28: -32, 39: 16, 40: 16, 41: 16, 46: 16, 49: 16, 52: 64, 53: 64}
DX.update({k: -32 for k in range(18, 27)}); DX.update({k: 32 for k in range(74, 80)}); DX.update({k: 24 for k in (88, 89, 90)})

H = None   # hidden: the English image covers it (second half of a split Japanese word)
# JP (sheet, u0, v0, u1, v1) -> PAL (sheet, u0, v0, u1, v1) or H, for what the setups do not pair
MANUAL = {
    (0, 192, 72, 240, 96): (1, 0, 48, 128, 72),       # モノ -> Monaural (ラル hidden)
    (0, 192, 96, 240, 120): H,
    (0, 192, 48, 240, 72): H,                         # レオ (ステ -> Stereo)
    (0, 0, 96, 96, 120): (0, 0, 96, 128, 120),        # 音量設定 Volume (title row 3 = PAL row 4)
    (0, 0, 120, 96, 144): (0, 0, 120, 128, 144),      # 操作設定 Control
    (0, 96, 216, 256, 240): (0, 0, 216, 256, 240),    # タイトルに戻る Return to title
    (1, 96, 168, 192, 192): (2, 128, 72, 256, 96),    # 反転 Reverse
    (1, 96, 120, 120, 144): (2, 144, 168, 168, 192),  # ? (button being assigned)
    (1, 0, 216, 256, 240): (2, 0, 216, 256, 240),     # タイトルに戻りますか? Return to title?
}
# slot-specific pairs where one JP image means two things in PAL
SLOT = {49: ((1, 192, 48, 240, 72), (1, 0, 216, 104, 240))}   # 必殺 after ・ -> "· Special" (the ・ is hidden)


def pairs(scr):
    m = {}; bad = []
    for A, B in scr:
        for k in range(N):
            (js, ju), (ps, pu) = A[k], B[k]
            if not any(ju[:4]) or k in SLOT or js < 0 or (ps < 0 and any(pu[:4])): continue   # untagged: handle set elsewhere
            key = (js,) + ju[:4]
            val = (ps,) + pu[:4] if any(pu[:4]) else H
            if key in MANUAL: continue
            if key in m and m[key] != val: bad.append((k, key, m[key], val)); continue
            m[key] = val
    m.update(MANUAL)
    return m, bad


def main():
    scr = screens()
    m, bad = pairs(scr)
    for b in sorted(set(bad)): print('conflict (first pair kept)', b)
    for A, B in scr[:2]:                      # report slots whose x offset is not DX
        for k in list(range(64)) + [88, 89, 90]:
            if any(A[k][1][:4]) and any(B[k][1][:4]) and B[k][1][4] - A[k][1][4] != DX.get(k, 0) and B[k][1][5] == A[k][1][5]:
                print('dx check', k, A[k], B[k])
    out = ['/* generated by tools/b7_optfix.py: options screen sprites, JP image -> PAL English image',
           '   {JP sheet, u0, v0, u1, v1, PAL sheet (-1 = hide), u0, v0, u1, v1} */',
           'static const short opt_map[][10] = {']
    for k, v in sorted(m.items(), key=lambda kv: kv[0]):
        out.append('    {%d, %d, %d, %d, %d, ' % k + ('%d, %d, %d, %d, %d},' % v if v else '-1, 0, 0, 0, 0},'))
    out += ['};', 'static const short opt_slot[][11] = {   /* slot, then as above */']
    for k, (a, b) in SLOT.items(): out.append('    {%d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d},' % ((k,) + a + b))
    out += ['};', 'static const signed char opt_dx[%d] = {' % N]
    out.append('    ' + ', '.join(str(DX.get(k, 0)) for k in range(N)))
    out += ['};', '']
    open(os.path.join(S.G, 'code/subtitle/optfix.h'), 'w').write('\n'.join(out))
    print(f'{len(m)} images mapped')


if __name__ == '__main__':
    main()
