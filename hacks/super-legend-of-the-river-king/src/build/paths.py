"""Where everything lives. Every script imports this instead of using fixed paths.

The original ROM is not included. Put it in  <toolkit>/rom/  (any file name ending in .sfc),
or point the KNT2_ROM environment variable at it."""
import os, glob, zlib
BUILD=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(BUILD)
ANALYSIS=os.path.join(ROOT,'analysis')
OUT=os.path.join(ROOT,'out')
ROM_CRC32=0x716D3EFF            # Kawa no Nushi Tsuri 2 (Japan).sfc, no header

def _find_rom():
    if os.environ.get('KNT2_ROM'): return os.environ['KNT2_ROM']
    c=sorted(glob.glob(os.path.join(ROOT,'rom','*.sfc'))+glob.glob(os.path.join(ROOT,'rom','*.smc')))
    return c[0] if c else os.path.join(ROOT,'rom','Kawa no Nushi Tsuri 2 (Japan).sfc')
ROM=_find_rom()
WRAM=os.path.join(BUILD,'data','sample_wram.dmp')   # a Mesen-S work-RAM dump used by the CPU simulator
REG_IPS=os.environ.get('KNT2_REG_IPS',os.path.join(OUT,'baseline.ips'))  # older patch to compare against

def b(x): return os.path.join(BUILD,x)
def a(x): return os.path.join(ANALYSIS,x)
def data(x): return os.path.join(BUILD,'data',x)
def font(x): return os.path.join(BUILD,'fonts',x)
def out(x):
    p=os.path.join(OUT,x); os.makedirs(os.path.dirname(p),exist_ok=True); return p

def check_rom():
    if not os.path.exists(ROM):
        raise SystemExit('Original ROM not found. Put it in %s or set KNT2_ROM.'%os.path.join(ROOT,'rom'))
    d=open(ROM,'rb').read()
    if len(d)%0x8000==512: raise SystemExit('ROM has a 512-byte copier header; remove it first.')
    crc=zlib.crc32(d)&0xFFFFFFFF
    if crc!=ROM_CRC32: print('WARNING: ROM CRC32 is %08X, expected %08X'%(crc,ROM_CRC32))

def script_json():
    """script.json is not shipped (it is the game's own text). Make it with analysis/dump_script.py."""
    for c in (os.path.join(BUILD,'script.json'),os.path.join(OUT,'script.json')):
        if os.path.exists(c): return c
    raise SystemExit('script.json not found. Run  python3 analysis/dump_script.py  first (it reads your ROM).')
