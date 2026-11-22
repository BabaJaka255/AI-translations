"""Headless PC Engine CD driver around the libretro Beetle PCE Fast core (ctypes).

    e = Emu(cue, sysdir)      # sysdir holds syscard3.pce
    e.run(frames, buttons=0)  # buttons: bitmask of B_* below
    e.ram()                   # 8 KB work RAM ($2000-$3FFF)
    e.save(path) / e.load(path)
    e.shot(path)              # PNG of the last frame
"""
import ctypes as C, os, numpy as np
from PIL import Image
CORE='/usr/lib/x86_64-linux-gnu/libretro/mednafen_pce_fast_libretro.so'
B_B,B_Y,B_SEL,B_START,B_UP,B_DOWN,B_LEFT,B_RIGHT,B_A=1,2,4,8,16,32,64,128,256
# PCE pad: I = libretro A, II = libretro B, RUN = START, SELECT = SELECT
I,II,RUN,SEL,UP,DOWN,LEFT,RIGHT=B_A,B_B,B_START,B_SEL,B_UP,B_DOWN,B_LEFT,B_RIGHT
class GameInfo(C.Structure): _fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
class Var(C.Structure): _fields_=[('key',C.c_char_p),('value',C.c_char_p)]
ENVF=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p)
VIDF=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
AUDF=C.CFUNCTYPE(None,C.c_int16,C.c_int16)
AUDBF=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t)
POLLF=C.CFUNCTYPE(None)
STATEF=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
class Emu:
    def __init__(s,cue,sysdir,opts=None):
        s.lib=C.CDLL(CORE); s.buttons=0; s.frame=None; s.fmt=0
        s.sysdir=C.c_char_p(os.path.abspath(sysdir).encode())
        s.opts={b'pce_fast_cdimagecache':b'enabled',b'pce_nospritelimit':b'enabled'}
        s.opts.update(opts or {}); s._keep=[]
        s._env=ENVF(s.env); s._vid=VIDF(s.vid); s._aud=AUDF(lambda l,r:None)
        s._audb=AUDBF(lambda d,n:n); s._poll=POLLF(lambda:None); s._st=STATEF(s.inp)
        L=s.lib
        L.retro_set_environment(s._env); L.retro_init()
        L.retro_set_video_refresh(s._vid); L.retro_set_audio_sample(s._aud)
        L.retro_set_audio_sample_batch(s._audb); L.retro_set_input_poll(s._poll); L.retro_set_input_state(s._st)
        gi=GameInfo(os.path.abspath(cue).encode(),None,0,None)
        L.retro_load_game.restype=C.c_bool
        if not L.retro_load_game(C.byref(gi)): raise RuntimeError('load failed')
        L.retro_serialize_size.restype=C.c_size_t
        L.retro_get_memory_data.restype=C.c_void_p; L.retro_get_memory_size.restype=C.c_size_t
    def env(s,cmd,data):
        cmd&=0xffff
        if cmd in (9,31,30): # system / save directory
            C.cast(data,C.POINTER(C.c_char_p))[0]=s.sysdir.value; return True
        if cmd==10: s.fmt=C.cast(data,C.POINTER(C.c_int))[0]; return True
        if cmd==15:
            v=C.cast(data,C.POINTER(Var))[0]; val=s.opts.get(v.key)
            if val is None: return False
            b=C.c_char_p(val); s._keep.append(b); C.cast(data,C.POINTER(Var))[0].value=val; return True
        if cmd in (3,): C.cast(data,C.POINTER(C.c_bool))[0]=True; return True
        return False
    def vid(s,data,w,h,pitch):
        if not data: return
        if s.fmt==2:
            a=np.ctypeslib.as_array(C.cast(data,C.POINTER(C.c_uint16)),(h,pitch//2))[:, :w].astype(np.uint32)
            s.frame=np.dstack([((a>>11)&31)*255//31,((a>>5)&63)*255//63,(a&31)*255//31]).astype(np.uint8)
        else:
            a=np.ctypeslib.as_array(C.cast(data,C.POINTER(C.c_uint32)),(h,pitch//4))[:, :w]
            s.frame=np.dstack([(a>>16)&255,(a>>8)&255,a&255]).astype(np.uint8)
    def inp(s,port,dev,idx,id):
        return 1 if port==0 and dev==1 and (s.buttons>>id)&1 else 0
    def run(s,n=1,buttons=0):
        s.buttons=buttons
        for _ in range(n): s.lib.retro_run()
        s.buttons=0
    def tap(s,b,hold=4,after=20): s.run(hold,b); s.run(after)
    def ram(s):
        p=s.lib.retro_get_memory_data(2); n=s.lib.retro_get_memory_size(2)
        return bytearray(C.string_at(p,n)) if p else None
    def poke(s,addr,val):
        p=s.lib.retro_get_memory_data(2); C.cast(p,C.POINTER(C.c_uint8))[addr&0x1fff]=val
    def state(s):
        n=s.lib.retro_serialize_size(); buf=C.create_string_buffer(n)
        assert s.lib.retro_serialize(buf,C.c_size_t(n)); return buf.raw
    def save(s,path): open(path,'wb').write(s.state())
    def load(s,path):
        d=open(path,'rb').read(); s.lib.retro_unserialize(d,C.c_size_t(len(d)))
    def shot(s,path,scale=2):
        im=Image.fromarray(s.frame); im.resize((im.width*scale,im.height*scale),Image.NEAREST).save(path)
