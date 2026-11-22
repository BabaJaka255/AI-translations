"""Read VRAM / WRAM / CGRAM out of a snes9x save state (stable-retro get_state())."""
import re,sys
def blocks(d):
    out={}; i=d.index(b'\n')+1
    while i<len(d):
        m=re.match(rb'([A-Z]{3}):(\d{6}):',d[i:i+11])
        if not m: break
        n=int(m.group(2)); out[m.group(1).decode()]=d[i+11:i+11+n]; i+=11+n
    return out
def load(path):
    b=blocks(open(path,'rb').read())
    return {'vram':b['VRA'],'wram':b['RAM'],'ppu':b['PPU']}
