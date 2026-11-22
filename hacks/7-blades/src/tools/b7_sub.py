"""Subtitle scripts (EFF/SUBTITLE.NCB in PAL). Per movie: <name>.GSC (English), .GSF (French), .GSG (German).
Each is b7_lz compressed. Decompressed: records of 3 LE u32 (start, end, text_offset), ended by (0,0,0xffffffff);
then NUL-terminated strings, TAB = line break. Times look like 1/30 s ticks (G0180: last end 337 in a 12.0 s movie)."""
import struct,sys,json,os
sys.path.insert(0,os.path.dirname(__file__))
import b7_lz,b7_ncb
def parse(u):
    recs=[];i=0
    while True:
        s,e,t=struct.unpack_from('<III',u,i); i+=12
        if t==0xffffffff: break
        recs.append((s,e,t))
    return [dict(start=s,end=e,text=u[t:u.index(b'\0',t)].decode('latin-1').replace('\t','\n')) for s,e,t in recs]
def build(lines):
    head=bytearray(); body=bytearray(); base=12*(len(lines)+1)
    for L in lines:
        head+=struct.pack('<III',L['start'],L['end'],base+len(body)); body+=L['text'].replace('\n','\t').encode('latin-1')+b'\0'
    head+=struct.pack('<III',0,0,0xffffffff); return bytes(head+body)
def load(ncb):
    d=open(ncb,'rb').read(); E=b7_ncb.entries(d); offs=sorted(o for _,o,_ in E)+[len(d)]
    return {n:parse(b7_lz.decompress(d[o:offs[offs.index(o)+1]])) for n,o,_ in E}
if __name__=='__main__':
    subs=load(sys.argv[1]); out={}
    for n,lines in subs.items():
        mv,ext=n.split('.'); lang={'GSC':'en','GSF':'fr','GSG':'de'}[ext]
        m=out.setdefault(mv,[])
        for i,L in enumerate(lines):
            if len(m)<=i: m.append(dict(id=f'{mv}-{i:02d}',start=L['start'],end=L['end']))
            m[i]['pal_'+lang]=L['text']
            if (m[i]['start'],m[i]['end'])!=(L['start'],L['end']): m[i].setdefault('timing_diff',{})[lang]=[L['start'],L['end']]
    json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
    print(len(out),'movies',sum(len(v) for v in out.values()),'lines')
