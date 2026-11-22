"""Minimal libretro host (ctypes) for driving the mGBA core headlessly."""
import ctypes as C, os
from PIL import Image

CORE = '/usr/lib/x86_64-linux-gnu/libretro/mgba_libretro.so'
KEYS = {'B':0,'Y':1,'SELECT':2,'START':3,'UP':4,'DOWN':5,'LEFT':6,'RIGHT':7,'A':8,'X':9,'L':10,'R':11}

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]

ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VID = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
INP = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

class Emu:
    def __init__(self, rom, sysdir='sys'):
        os.makedirs(sysdir, exist_ok=True)
        self.lib = C.CDLL(CORE)
        self.fmt = 0
        self.frame = None
        self.pressed = set()
        self._sysdir = C.c_char_p(sysdir.encode())
        def env(cmd, data):
            cmd &= 0xffff
            if cmd in (9, 31):  # system / save directory
                C.cast(data, C.POINTER(C.c_char_p))[0] = self._sysdir; return True
            if cmd == 10:
                self.fmt = C.cast(data, C.POINTER(C.c_int))[0]; return True
            if cmd == 15:  # GET_VARIABLE
                return False
            if cmd == 3: C.cast(data, C.POINTER(C.c_bool))[0] = True; return True
            return False
        def vid(data, w, h, pitch):
            if data:
                self.frame = (C.string_at(data, pitch * h), w, h, pitch)
        self._cbs = [ENV(env), VID(vid), AUD(lambda l, r: None), AUDB(lambda d, n: n), POLL(lambda: None),
                     INP(lambda p, d, i, k: 1 if (p == 0 and d == 1 and k in self.pressed) else 0)]
        L = self.lib
        L.retro_set_environment(self._cbs[0]); L.retro_set_video_refresh(self._cbs[1])
        L.retro_set_audio_sample(self._cbs[2]); L.retro_set_audio_sample_batch(self._cbs[3])
        L.retro_set_input_poll(self._cbs[4]); L.retro_set_input_state(self._cbs[5])
        L.retro_init()
        self.rom = open(rom, 'rb').read()
        self._rombuf = C.create_string_buffer(self.rom, len(self.rom))
        gi = GameInfo(rom.encode(), C.cast(self._rombuf, C.c_void_p), len(self.rom), None)
        assert L.retro_load_game(C.byref(gi))
        L.retro_serialize_size.restype = C.c_size_t
        L.retro_get_memory_data.restype = C.c_void_p
        L.retro_get_memory_size.restype = C.c_size_t

    def run(self, n=1, keys=()):
        self.pressed = {KEYS[k] for k in keys}
        for _ in range(n): self.lib.retro_run()
        self.pressed = set()

    def press(self, key, hold=4, after=20):
        self.run(hold, [key] if isinstance(key, str) else key); self.run(after)

    def save(self, path=None):
        n = self.lib.retro_serialize_size(); b = C.create_string_buffer(n)
        assert self.lib.retro_serialize(b, n)
        if path: open(path, 'wb').write(b.raw)
        return b.raw

    def load(self, src):
        data = open(src, 'rb').read() if isinstance(src, str) else src
        b = C.create_string_buffer(data, len(data))
        assert self.lib.retro_unserialize(b, len(data))

    def mem(self, kind=2):
        p = self.lib.retro_get_memory_data(kind); n = self.lib.retro_get_memory_size(kind)
        return (C.c_ubyte * n).from_address(p) if p else None

    def image(self):
        data, w, h, pitch = self.frame
        if self.fmt == 1:
            im = Image.frombuffer('RGBA', (w, h), data, 'raw', 'BGRA', pitch, 1).convert('RGB')
        else:
            import numpy as np
            a = np.frombuffer(data, dtype='<u2').reshape(h, pitch // 2)[:, :w].astype('u4')
            if self.fmt == 2: r, g, b = (a >> 11) & 31, (a >> 5) & 63, a & 31; g = g >> 1
            else: r, g, b = (a >> 10) & 31, (a >> 5) & 31, a & 31
            im = Image.fromarray(np.dstack([(r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2)]).astype('u1'))
        return im

    def shot(self, path, scale=2):
        im = self.image()
        im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)

# mGBA serialized state layout
def st_vram(s): return s[0x1000:0x19000]
def st_iwram(s): return s[0x19000:0x21000]
def st_ewram(s): return s[0x21000:0x61000]
def st_io(s): return s[0x400:0x800]
def st_pal(s): return s[0x800:0xC00]
def st_oam(s): return s[0xC00:0x1000]

def sheet(images, cols=4, path='sheet.png'):
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    out = Image.new('RGB', (w * cols, h * rows), (40, 40, 40))
    for i, im in enumerate(images): out.paste(im, ((i % cols) * w, (i // cols) * h))
    out.save(path); return out
