"""Where everything lives. Every build script and tool imports this instead of using fixed paths.

Layout (relative to src/):
  build/   patch code          tools/  analysis tools        script/  script dump + workbook
  tables/  character tables    gfx/    fonts, logo, sheets   data/    extracted data and RAM dumps
  rom/     your ROM (git-ignored)                            out/     build output (git-ignored)

The original ROM is not included. Put it in src/rom/ (any *.sfc), or set KNT2_ROM=/path/to/rom.sfc."""
import os, glob, zlib
BUILD=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(BUILD)
ANALYSIS=os.path.join(ROOT,'tools')
OUT=os.environ.get('KNT2_OUT',os.path.join(ROOT,'out'))
ROM_CRC32=0x716D3EFF            # Kawa no Nushi Tsuri 2 (Japan).sfc, no header

def _find_rom():
    if os.environ.get('KNT2_ROM'): return os.environ['KNT2_ROM']
    c=sorted(glob.glob(os.path.join(ROOT,'rom','*.sfc'))+glob.glob(os.path.join(ROOT,'rom','*.smc')))
    return c[0] if c else os.path.join(ROOT,'rom','Kawa no Nushi Tsuri 2 (Japan).sfc')
ROM=_find_rom()
WRAM=os.path.join(ROOT,'data','dumps','WorkRamDialogue.dmp')   # Mesen-S work-RAM dump used by the CPU simulator
REG_IPS=os.environ.get('KNT2_REG_IPS',os.path.join(OUT,'baseline.ips'))  # older patch to compare against

_HOME={'script.json':'script','script_dump.txt':'script',
       'knt2_single_byte.tbl':'tables','kanji_overrides.txt':'tables','knt2_kanji.tbl':'tables',
       'logo_custom.png':os.path.join('gfx','logo')}
def b(x): return os.path.join(ROOT,_HOME[x],x) if x in _HOME else os.path.join(BUILD,x)
def a(x): return os.path.join(ANALYSIS,x)
def data(x): return os.path.join(ROOT,_HOME[x],x) if x in _HOME else os.path.join(ROOT,'data',x)
def font(x): return os.path.join(ROOT,'gfx','fonts','source',x)
def out(x):
    p=os.path.join(OUT,x); os.makedirs(os.path.dirname(p),exist_ok=True); return p

def check_rom():
    if not os.path.exists(ROM):
        raise SystemExit('Original ROM not found. Put it in %s or set KNT2_ROM.'%os.path.join(ROOT,'rom'))
    d=open(ROM,'rb').read()
    if len(d)%0x8000==512: raise SystemExit('ROM has a 512-byte copier header; remove it first.')
    crc=zlib.crc32(d)&0xFFFFFFFF
    if crc!=ROM_CRC32: print('WARNING: ROM CRC32 is %08X, expected %08X'%(crc,ROM_CRC32))
