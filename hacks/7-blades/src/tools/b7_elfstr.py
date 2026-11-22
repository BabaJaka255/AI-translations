"""List NUL-terminated Shift-JIS strings (with at least one double-byte char) in an ELF data area."""
import re,sys,json
def strings(d,lo=0x1f0000,hi=None):
    hi=hi or len(d); out=[]; i=lo
    pat=re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]|[\x09\x0a\x20-\x7e])+\x00')
    for m in pat.finditer(d,lo,hi):
        s=m.group()[:-1]
        if not re.search(rb'[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]',s): continue
        try: t=s.decode('cp932')
        except UnicodeDecodeError: continue
        if len(t)<2 or m.start()%4: continue
        out.append((m.start(),t))
    return out
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    for o,t in strings(d): print(hex(o),t)
