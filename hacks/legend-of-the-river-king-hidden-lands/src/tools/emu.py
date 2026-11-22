"""Headless PS1 driver around the libretro Beetle PSX core (ctypes).

    e = Emu(cue, sysdir, memcard=None)  # sysdir holds scph5500.bin
    e.run(frames, buttons=0)            # buttons: bitmask of B_* below
    e.ram()                             # 2 MB main RAM (0x80000000-)
    e.save(path) / e.load(path) / e.shot(path)
"""
import ctypes as C, os, numpy as np
from PIL import Image
CORE = '/usr/lib/x86_64-linux-gnu/libretro/mednafen_psx_libretro.so'
# libretro joypad ids: B=0 Y=1 SELECT=2 START=3 UP=4 DOWN=5 LEFT=6 RIGHT=7 A=8 X=9 L=10 R=11
# PS1 mapping: Cross=B, Square=Y, Circle=A, Triangle=X
CROSS, SQUARE, SELECT, START, UP, DOWN, LEFT, RIGHT, CIRCLE, TRIANGLE, L1, R1 = [1 << i for i in range(12)]
class GameInfo(C.Structure): _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]
class Var(C.Structure): _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]
ENVF = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDF = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDF = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDBF = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLLF = C.CFUNCTYPE(None)
STATEF = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

class Emu:
    def __init__(s, cue, sysdir, memcard=None, opts=None):
        s.lib = C.CDLL(CORE); s.buttons = 0; s.frame = None; s.fmt = 0
        s.sysdir = C.c_char_p(os.path.abspath(sysdir).encode())
        s.opts = {b'beetle_psx_cdimagecache': b'enabled'}
        s.opts.update(opts or {}); s._keep = []
        s._env = ENVF(s.env); s._vid = VIDF(s.vid); s._aud = AUDF(lambda l, r: None)
        s._audb = AUDBF(lambda d, n: n); s._poll = POLLF(lambda: None); s._st = STATEF(s.inp)
        L = s.lib
        L.retro_set_environment(s._env); L.retro_init()
        L.retro_set_video_refresh(s._vid); L.retro_set_audio_sample(s._aud)
        L.retro_set_audio_sample_batch(s._audb); L.retro_set_input_poll(s._poll); L.retro_set_input_state(s._st)
        gi = GameInfo(os.path.abspath(cue).encode(), None, 0, None)
        L.retro_load_game.restype = C.c_bool
        if not L.retro_load_game(C.byref(gi)): raise RuntimeError('load failed')
        L.retro_serialize_size.restype = C.c_size_t
        L.retro_get_memory_data.restype = C.c_void_p; L.retro_get_memory_size.restype = C.c_size_t
        if memcard:
            d = open(memcard, 'rb').read()
            p = L.retro_get_memory_data(0); n = L.retro_get_memory_size(0)
            assert p and n == len(d), (p, n, len(d))
            C.memmove(p, d, n)
    def env(s, cmd, data):
        cmd &= 0xffff
        if cmd in (9, 31, 30):
            C.cast(data, C.POINTER(C.c_char_p))[0] = s.sysdir.value; return True
        if cmd == 10: s.fmt = C.cast(data, C.POINTER(C.c_int))[0]; return True
        if cmd == 15:
            v = C.cast(data, C.POINTER(Var))[0]; val = s.opts.get(v.key)
            if val is None: return False
            C.cast(data, C.POINTER(Var))[0].value = val; return True
        if cmd == 3: C.cast(data, C.POINTER(C.c_bool))[0] = True; return True
        return False
    def vid(s, data, w, h, pitch):
        if not data: return
        if s.fmt == 2:
            a = np.ctypeslib.as_array(C.cast(data, C.POINTER(C.c_uint16)), (h, pitch // 2))[:, :w].astype(np.uint32)
            s.frame = np.dstack([((a >> 11) & 31) * 255 // 31, ((a >> 5) & 63) * 255 // 63, (a & 31) * 255 // 31]).astype(np.uint8)
        elif s.fmt == 1:
            a = np.ctypeslib.as_array(C.cast(data, C.POINTER(C.c_uint32)), (h, pitch // 4))[:, :w]
            s.frame = np.dstack([(a >> 16) & 255, (a >> 8) & 255, a & 255]).astype(np.uint8)
        else:
            a = np.ctypeslib.as_array(C.cast(data, C.POINTER(C.c_uint16)), (h, pitch // 2))[:, :w].astype(np.uint32)
            s.frame = np.dstack([((a >> 10) & 31) * 255 // 31, ((a >> 5) & 31) * 255 // 31, (a & 31) * 255 // 31]).astype(np.uint8)
    def inp(s, port, dev, idx, id):
        return 1 if port == 0 and (dev & 0xff) == 1 and (s.buttons >> id) & 1 else 0
    def run(s, n=1, buttons=0):
        s.buttons = buttons
        for _ in range(n): s.lib.retro_run()
        s.buttons = 0
    def tap(s, b, hold=4, after=30): s.run(hold, b); s.run(after)
    RAMOFF = None
    def _ramoff(s, st):
        if s.RAMOFF is None:
            i = st.find(b'MainRAM.data8'); s.RAMOFF = i + 17
        return s.RAMOFF
    def ram(s):
        st = s.state(); o = s._ramoff(st)
        return bytearray(st[o:o + 0x200000])
    def write(s, addr, data):
        st = bytearray(s.state()); o = s._ramoff(st) + (addr & 0x1fffff)
        st[o:o + len(data)] = bytes(data)
        s.lib.retro_unserialize(bytes(st), C.c_size_t(len(st)))
    def memcard(s):
        p = s.lib.retro_get_memory_data(0); n = s.lib.retro_get_memory_size(0)
        return bytes(C.string_at(p, n))
    def state(s):
        n = s.lib.retro_serialize_size(); buf = C.create_string_buffer(n)
        assert s.lib.retro_serialize(buf, C.c_size_t(n)); return buf.raw
    def refresh(s, new='build_exe.bin', old='files/SLPS_015.36'):
        """Copy a rebuilt exe's changed bytes into RAM (so old save states show new text)."""
        a = open(old, 'rb').read(); b = open(new, 'rb').read()
        st = bytearray(s.state()); o = s._ramoff(st) + 0xf800
        for i in range(0x800, len(b)):
            if a[i] != b[i]: st[o + i] = b[i]
        for lo, hi in ((0x800, 0x4400), (0xbfb04, 0xdc612)):   # text + pointer tables: whole ranges,
            st[o + lo:o + hi] = b[lo:hi]                       # an older build may have changed them
        s.lib.retro_unserialize(bytes(st), C.c_size_t(len(st)))
    def save(s, path): open(path, 'wb').write(s.state())
    def load(s, path):
        d = open(path, 'rb').read(); s.lib.retro_unserialize(d, C.c_size_t(len(d)))
    def shot(s, path, scale=1):
        im = Image.fromarray(s.frame)
        if scale != 1: im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        im.save(path)
