"""Build the patched Japanese ELF: compile code/subtitle (English movie subtitles), add it as a second
PT_LOAD segment at 0x6d3200, move the libc heap start past it, and patch the hook calls.
usage: b7_build_jp.py [out_elf]   (default build/SLPM_650.08)"""
import json, os, struct, subprocess, sys
G = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(G, 'code/subtitle')
TMP = os.environ.get('B7_TMP', os.path.join(G, 'build', 'tmp'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b7_strings
CC = 'mips64el-linux-gnuabi64-'
CF = ('-march=r5900 -mfix-r5900 -mabi=n32 -msoft-float -mno-abicalls -fno-pic -G0 -O2 '
      '-ffreestanding -fno-builtin -Wall').split()
# fx.c does float maths and calls game routines that take floats: hard float, odd FPU regs left alone
CF_FX = tuple(x for x in CF if x != '-msoft-float') + ('-mhard-float', '-msingle-float', '-ffixed-f21', '-ffixed-f23',
        '-ffixed-f25', '-ffixed-f27', '-ffixed-f29', '-ffixed-f31')
SEG = 0x6d3200
HEAP_END = 0x700000

def run(*a):
    subprocess.run(a, check=True)

def jal(t): return 0x0c000000 | ((t >> 2) & 0x3ffffff)
def lui(r, v): return 0x3c000000 | (r << 16) | (v & 0xffff)
def addiu(rt, rs, v): return 0x24000000 | (rs << 21) | (rt << 16) | (v & 0xffff)
def hilo(v): return ((v + 0x8000) >> 16) & 0xffff, v & 0xffff

def build(out):
    os.makedirs(TMP, exist_ok=True)
    run('python3', os.path.join(SRC, 'gen_data.py'), os.path.join(SRC, 'eu_font.rh2'), os.path.join(TMP, 'subdata.c'))
    objs = []
    for c in (os.path.join(SRC, 'sub.c'), os.path.join(SRC, 'fx.c'), os.path.join(SRC, 'pressure.c'), os.path.join(TMP, 'subdata.c')):
        hard = c.endswith(('fx.c', 'pressure.c'))
        o = os.path.join(TMP, os.path.basename(c)[:-2] + '.o'); run(CC + 'gcc', *(CF_FX if hard else CF), '-c', c, '-o', o); objs.append(o)
    elf = os.path.join(TMP, 'sub.elf'); binf = os.path.join(TMP, 'sub.bin')
    run(CC + 'ld', '-m', 'elf32ltsmipn32', '-T', os.path.join(SRC, 'link.ld'), '-o', elf, *objs)
    run(CC + 'objcopy', '-O', 'binary', elf, binf)
    sym = {}
    for line in subprocess.run([CC + 'nm', elf], capture_output=True, text=True, check=True).stdout.split('\n'):
        p = line.split()
        if len(p) == 3: sym[p[2]] = int(p[0], 16)
    blob = open(binf, 'rb').read()
    end = sym['_end']; blob += b'\0' * (end - SEG - len(blob))
    assert len(blob) == end - SEG
    heap = int(os.environ.get('B7_HEAP') or '0', 16) or (end + 0xff) & ~0xff
    assert heap <= 0x6f2f20, hex(heap)  # leave the libc heap at least as much room as PAL's (0x6f2f20-0x700000)

    d = bytearray(open(os.path.join(G, 'rom/jp/SLPM_650.08'), 'rb').read())
    def w(va, new, old=None):
        o = va - 0x200000 + 0x1000
        if old is not None:
            cur = struct.unpack_from('<I', d, o)[0]
            assert cur == old, f'{va:x}: {cur:08x} != {old:08x}'
        struct.pack_into('<I', d, o, new)
    # hooks (B7_HOOKS=play,pic,send to test a subset)
    hooks = os.environ.get('B7_HOOKS', 'play,pic,send,tut,str,font,status,kills,save,fx,press,opt').split(',')
    if 'play' in hooks: w(0x385db0, jal(sym['my_play']), jal(0x385e10))
    if 'pic' in hooks: w(0x387b9c, jal(sym['my_getpic']), jal(0x3c5738))
    if 'tut' in hooks:   # tutorial message builder 0x22fb40: replace the jump-table dispatch (Gokurakumaru, Yuri)
        for at, fn, cont in ((0x22fc4c, 'tut_fill_goku', 0x2311a8), (0x231264, 'tut_fill_yuri', 0x232618)):
            w(at, 0x02802021)                              # move a0, s4   (message index)
            w(at + 4, jal(sym[fn]))
            w(at + 8, 0x02202821)                          # move a1, s1   (line 0 of the record)
            w(at + 12, 0x10000000 | (((cont - (at + 16)) >> 2) & 0xffff))   # b cont
            w(at + 16, 0x2402015c)                         # addiu v0, zero, 0x15c
        # tutorial draw 0x232940 centres each line at 0x140 - count*12; count (0x232ea0) becomes half the
        # proportional pixel width (tut_width) and the factor 1, as PAL centres with its width function
        w(0x232ea0, 0x08000000 | ((sym['tut_width'] >> 2) & 0x3ffffff), 0x80820000)   # j tut_width
        w(0x232ea4, 0, 0x0000302d)                                                      # nop
        w(0x232bc0, 0x24070001, 0x2407000c)
    if 'str' in hooks:   # pointer slots repointed to English strings (b7_strings.py): freed JP string space, then the segment
        st = json.load(open(os.path.join(TMP, 'strings.json')))
        for va, b in st['placed'].items():
            o = int(va, 16) - 0x200000 + 0x1000; b = bytes.fromhex(b) + b'\0'; d[o:o + len(b)] = b
        for slot, va in st['slots'].items(): w(int(slot, 16), int(va, 16))
        for va, (jt, et) in b7_strings.INLINE.items():
            o = va - 0x200000 + 0x1000; jb, eb = jt.encode('cp932'), et.encode('cp932')
            assert d[o:o + len(jb) + 1] == jb + b'\0' and len(eb) < 0x20
            d[o:o + 0x20] = eb + bytes(0x20 - len(eb))
        for k, v in sym.items():
            if k.startswith('sp_'):
                w(int(k[3:], 16), v)
    if 'font' in hooks:   # eu_font instead of kanji1, PAL's proportional renderer instead of 0x2f3600
        w(0x2f346c, jal(sym['my_install']), jal(0x2f8010))
        w(0x2f3600, 0x08000000 | ((sym['pal_text'] >> 2) & 0x3ffffff), 0x27bdff20)   # j pal_text
        w(0x2f3604, 0, 0x8f82b760)                                                     # nop (was lw v0, -0x48a0(gp))
        # PAL's English text sizes and layouts (the project lead 2026-11-10: compare with PAL). Same screen coordinates in
        # both programs; PAL shrank these from 24/32 to 16 and gave the message boxes a 4th row (JP's 4th row
        # sat at 0,0, which showed as "@ knocked out." top left once its blank string was reused).
        w(0x229150, 0x24040010, 0x24040020); w(0x229158, 0x24050010, 0x24050020)   # enemy name label 32 -> 16
        w(0x36ffc8, 0x24040010, 0x24040018); w(0x36ffd0, 0x24050010, 0x24050018)   # item name label 24 -> 16
        w(0x3790f8, 0x24040010, 0x24040018); w(0x379100, 0x24050010, 0x24050018)   # command labels 24 -> 16
        w(0x3790b8, 0x24100174, 0x24100170)   # Use / Quick y
        w(0x379090, 0x2410018c, 0x24100188)   # Drop y
        w(0x3790ac, 0x2410015c, 0x24100158)   # Remove y
        w(0x3790a4, 0x241100d8, 0x24110098)   # Remove x (PAL English)
        w(0x3790b4, 0x241100d8, 0x241100e0)   # Quick x (PAL English)
        w(0x37911c, jal(sym['my_cmd_label']), jal(0x2f35f0))   # + PAL's "Item" under "Quick"
        pal = open(os.path.join(G, 'rom/pal/SLES_501.09'), 'rb').read()
        for jva, pva, n in ((0x474f48, 0x4987fc, 20),   # message box: size, x[4], y[4]
                            (0x4749e8, 0x4976a4, 28),   # weapon box: size, x[5], y[5] (code 0x37a8cc)
                            (0x474d20, 0x498244, 20),   # weapon / quick item box
                            (0x474308, 0x495e98, 6),    # food name: size, x, y
                            (0x474658, 0x496c4c, 8)):   # food comments: size, x, y1, y2
            o = jva - 0x200000 + 0x1000; po = pva - 0x200000 + 0x1000
            d[o:o + n] = pal[po:po + n]
    if 'status' in hooks:   # status popups get PAL's English caption (my_status_load / my_status_draw)
        for at in (0x2e7c0c, 0x2e7ca4, 0x2e7d3c, 0x2e7dd4, 0x2e7e6c, 0x2e7f04, 0x2e7f9c, 0x2e8034, 0x2e80cc, 0x2e8164, 0x2e81fc):
            w(at, jal(sym['my_status_load']), jal(0x2f81f8))
        w(0x2e7678, 0x08000000 | ((sym['my_status_draw'] >> 2) & 0x3ffffff), 0x24030090)   # j my_status_draw
        w(0x2e767c, 0, 0x27bdff80)
    if 'kills' in hooks:   # kill counter: effect.r girisuji.rh2 becomes PAL giri_u.rh2 (b7_peace RENAME), label 48 -> 64 texels
        # like PAL: white art tinted 0x808008, label "Defeated" 64x16 texels. JP lays out [digits][label] centred
        # at x 470 with the label 3 digit-widths wide; it becomes 4 wide (same 1.25 scale as JP).
        for at, old in ((0x3ba47c, 0x34a58080), (0x3ba4cc, 0x34848080), (0x3ba510, 0x34638080)):
            w(at, (old & ~0xffff) | 0x8008, old)
        w(0x3ba560, 0x24030004, 0x24030003)   # li v1, 4   (centring count: digits + label width)
        w(0x3ba708, 0x00141880, 0x00141840)   # sll v1, s4, 2   (label width 4 * digit width)
        w(0x3ba70c, 0x24c60006, 0x00741821)   # addiu a2, a2, 6   (label x0: a 6 px gap after the digits; was addu v1, v1, s4)
        w(0x3ba738, 0x24636c60, 0x24636c00)   # label x1 + 6 px as well
        w(0x3ba74c, 0x34420400, 0x34420300)   # label uv1 u 48 -> 64
    if 'save' in hooks:   # save screen: PAL English sprite rectangles + PAL's extra lines (my_save_fix / my_save_draw)
        w(0x3610a0, 0x08000000 | ((sym['my_save_fix'] >> 2) & 0x3ffffff), 0x03e00008)   # j my_save_fix (was jr ra)
        w(0x3621b0, jal(sym['my_save_draw']), jal(0x363fc0))
        w(0x35c538, 0x08000000 | ((sym['my_load_fix'] >> 2) & 0x3ffffff), 0x03e00008)   # load sprite setup 0x35bf80: j my_load_fix
        w(0x35d0fc, jal(sym['my_load_draw']), jal(0x35f378))
        # map location labels (2 characters x 64 entries x 0x20: screen x/y, u/v, w/h, sheet): PAL's English
        # block (0x47f7c0 + (language + 2) * 0x800) for the horizontal mapft*_u labels
        pal = open(os.path.join(G, 'rom/pal/SLES_501.09'), 'rb').read()
        o = 0x46ac80 - 0x200000 + 0x1000; po = 0x47f7c0 + 0x1000 - 0x200000 + 0x1000
        assert d[o:o + 0x800] == pal[po - 0x1000:po - 0x800]
        d[o:o + 0x800] = pal[po:po + 0x800]
    if 'opt' in hooks:   # options screens: PAL's English labels drawn into the JP layout (my_optspr, optfix.h)
        for at in (0x36bfd4, 0x36bff4, 0x36c090, 0x36c0b8, 0x36c15c, 0x36c1d8, 0x36c250,          # title options
                   0x380218, 0x380238, 0x380310, 0x380338, 0x382408, 0x382508, 0x382590, 0x382610, 0x382648):  # in-game
            w(at, jal(sym['my_optspr']), jal(0x37b538))
        w(0x368d9c, jal(sym['my_optload_title']), jal(0x2f81f8))   # Font2 load + FONT3 (PAL's third sheet)
        w(0x3823a8, jal(sym['my_optload_game']), jal(0x2f81f8))
        w(0x37dec8, 0x08000000 | ((sym['my_optfix_game'] >> 2) & 0x3ffffff), 0x03e00008)    # setups end in j my_optfix_* (cursor bars)
        w(0x36a6fc, 0x08000000 | ((sym['my_optfix_title'] >> 2) & 0x3ffffff), 0x03e00008)
    if 'fx' in hooks:   # PAL's sword trail (code/subtitle/fx.c) as effect 77's program
        w(0x433738 + 77 * 4, sym['my_eff77'], 0x2dffc8)
        w(0x433738 + 10 * 4, sym['my_eff10'], 0x202b08)   # Gokuu's trail with PAL's strength glow + sparks
        w(0x4333d0 + 10 * 4, sym['my_load10'], 0x203890)
    if 'press' in hooks:   # PAL's pressure-sensitive attacks (code/subtitle/pressure.c); needs 'fx' for the glow
        def j(t): return 0x08000000 | ((t >> 2) & 0x3ffffff)
        def lwc1(ft, off, base=1): return 0xc4000000 | (base << 21) | (ft << 16) | (off & 0xffff)
        for at in (0x3b4e40, 0x3baa6c): w(at, jal(sym['my_padget']), jal(0x384568))   # pad read + sampling
        w(0x258d88, jal(sym['st_act_in']), jal(0x383950))       # action function: remember the action
        w(0x259f04, jal(sym['st_act_out']), jal(0x383870))      # ... and start / clear the level at its end
        w(0x27df5c, jal(sym['st_hitbox']), jal(0x3920b8))       # hitbox: level + reach
        for at, reg, var, old in ((0x27e038, 22, 'rng_near', 0x42480000), (0x27e044, 23, 'rng_far', 0x42c80000),
                                  (0x27ea4c, 22, 'rng_near', 0x42480000), (0x27ea80, 23, 'rng_far', 0x42c80000)):
            hi, lo = hilo(sym[var])
            w(at, lui(1, hi), lui(1, old >> 16)); w(at + 4, lwc1(reg, lo), 0x44810000 | (reg << 11))
        w(0x27e950, j(sym['st_arc']), 0x2404ffff)                 # swing sectors
        w(0x27f018, j(sym['st_arc2']), 0x0040182d); w(0x27f01c, 0, 0x10600007)
        w(0x27f198, j(sym['st_arc3']), 0x8e620100)
        w(0x27f744, jal(sym['st_recA']), jal(0x3a5828)); w(0x27f7a0, jal(sym['st_recB']), jal(0x3a5828))
        w(0x260608, j(sym['st_hit']), 0x1602000e)                 # hit: level + damage x1.5 / x0.5
        w(0x265cc4, j(sym['st_light']), 0x1040005b)
        w(0x2694a4, j(sym['st_clr']), 0x8ce200cc)
        w(0x2c2d78, jal(sym['st_throw']), 0x3c014080); w(0x2c2d7c, 0, 0x44810000)
        # Yuri's copy (PAL gp-17128): her action fn, shot speed, swing, shot damage, and PAL's own hit routine
        w(0x2cb078, j(sym['st_yact']), 0x27bdffa0); w(0x2cb07c, 0, 0xffb40040)
        w(0x2cb4b4, j(sym['st_ystart']), 0x1000019b)               # action 243 ...
        for act in (229, 233): w(0x4dc7e0 + (act - 1) * 4, sym['st_ystart'], 0x2cbb24)   # ... and 229 / 233 (jump table)
        w(0x2d14bc, j(sym['st_yshot']), 0x3c013fc0); w(0x2d14c0, 0, 0x44810000)
        w(0x2d1c98, j(sym['st_yswing']), 0x8ca200ac)
        w(0x244cfc, j(sym['st_ydmg']), 0x3c013fc0); w(0x244d00, 0, 0x4481a800)
        hi, lo = hilo(sym['my_yuri_hit'])
        for lu, ad, r in ((0x2c7308, 0x2c7338, 10), (0x315cc0, 0x315cd0, 4)):   # entity +108 = hit routine
            w(lu, lui(r, hi), lui(r, 0x3a)); w(ad, addiu(r, r, lo), addiu(r, r, 0x6188))
    if 'send' in hooks:
        w(0x385b10, jal(sym['my_send']), jal(0x3bd7a0))
        w(0x385b60, jal(sym['my_send']), jal(0x3bd7a0))
    # libc heap: sbrk's start pointer (initialised to &end) and SetupHeap(start, size) in crt0
    w(0x4ba66c, heap, SEG)
    hi, lo = hilo(heap); w(0x20006c, lui(4, hi), lui(4, 0x6d)); w(0x200074, addiu(4, 4, lo), addiu(4, 4, 0x3200))
    hi, lo = hilo(HEAP_END - heap); w(0x200070, lui(5, hi), lui(5, 3)); w(0x200078, addiu(5, 5, lo), addiu(5, 5, -0x3200))
    # second program header
    phoff, phentsize, phnum = struct.unpack_from('<I', d, 28)[0], *struct.unpack_from('<HH', d, 42)
    assert phnum == 1 and phentsize == 32 and not any(d[phoff + 32:phoff + 64])
    off = ((len(d) + 0xfff) & ~0xfff) + (SEG & 0xfff)
    d += b'\0' * (off - len(d)); d += blob
    struct.pack_into('<8I', d, phoff + 32, 1, off, SEG, SEG, len(blob), len(blob), 7, 0x1000)
    struct.pack_into('<H', d, 44, 2)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(d)
    print(f'{out}: segment {SEG:x}-{end:x} ({len(blob)} bytes), heap {heap:x}-{HEAP_END:x}')
    for k in ('my_play', 'my_getpic', 'my_send'): print(f'  {k} {sym[k]:x}')

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(G, 'build/SLPM_650.08'))
