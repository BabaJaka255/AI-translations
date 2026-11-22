"""Read/modify snes9x savestates produced by stable-retro (get_state)."""
import re
def blocks(st):
    out={}
    for m in re.finditer(rb'([A-Z]{3}):(\d{6})',st):
        n=int(m.group(2)); out.setdefault(m.group(1).decode(),(m.end()+1,n))
    return out
def get(st,name):
    o,n=blocks(st)[name]; return st[o:o+n]
def put(st,name,data):
    o,n=blocks(st)[name]; assert len(data)==n; return st[:o]+bytes(data)+st[o+n:]
