"""Where everything lives. Every script imports this instead of using fixed paths.

The original ROM is not included. Put it in  <toolkit>/rom/  (any file name ending in .sfc),
or point the UMI_ROM environment variable at it."""
import os, glob, zlib
BUILD=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(BUILD)
ANALYSIS=os.path.join(ROOT,'analysis')
OUT=os.path.join(ROOT,'out')
ROM_CRC32=0xC985F568            # Umi no Nushi Tsuri (Japan) (Rev 1).sfc, no header

def _find_rom():
    if os.environ.get('UMI_ROM'): return os.environ['UMI_ROM']
    c=sorted(glob.glob(os.path.join(ROOT,'rom','*.sfc'))+glob.glob(os.path.join(ROOT,'rom','*.smc')))
    return c[0] if c else os.path.join(ROOT,'rom','Umi no Nushi Tsuri (Japan) (Rev 1).sfc')
ROM=_find_rom()

def b(x): return os.path.join(BUILD,x)
def a(x): return os.path.join(ANALYSIS,x)
def data(x): return os.path.join(BUILD,'data',x)
def font(x): return os.path.join(BUILD,'fonts',x)
def out(x):
    p=os.path.join(OUT,x); os.makedirs(os.path.dirname(p),exist_ok=True); return p

def check_rom():
    if not os.path.exists(ROM):
        raise SystemExit('Original ROM not found. Put it in %s or set UMI_ROM.'%os.path.join(ROOT,'rom'))
    d=open(ROM,'rb').read()
    if len(d)%0x8000==512: raise SystemExit('ROM has a 512-byte copier header; remove it first.')
    crc=zlib.crc32(d)&0xFFFFFFFF
    if crc!=ROM_CRC32: print('WARNING: ROM CRC32 is %08X, expected %08X'%(crc,ROM_CRC32))
