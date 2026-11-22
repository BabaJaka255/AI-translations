"""Add a new file to an existing ISO9660 directory in place (needs free room in the directory extent).
Data is appended after the last sector; PVD volume size is updated. usage: b7_iso_add.py iso ISO_PATH local"""
import sys,os,struct
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'toolkit'))
from rhtk.ps2 import Iso,SECTOR,_put_both
def both(v,n): return struct.pack('<'+('I' if n==4 else 'H'),v)+struct.pack('>'+('I' if n==4 else 'H'),v)
def add(iso_path,ipath,local):
    d,name=os.path.split('/'+ipath.strip('/'))
    with Iso(iso_path) as iso:
        de=iso.find(d) if d!='/' else iso.root
        if iso.find(ipath): raise SystemExit(ipath+' exists')
        data=bytearray(iso.read(de.lba,de.size)); vol=iso.volume_sectors
        tmpl=None; i=0; last=0
        while i<len(data):
            n=data[i]
            if n==0: i=(i//SECTOR+1)*SECTOR; continue
            rec=data[i:i+n]
            if rec[32]>1 and not rec[25]&2: tmpl=bytes(rec)
            last=i+n; i+=n
    fid=(name.upper()+';1').encode(); L=33+len(fid); L+=L&1
    cap=-(-len(data)//SECTOR)*SECTOR
    if last//SECTOR != (last+L-1)//SECTOR or last+L>cap: raise SystemExit('no room in directory sector')
    newdir=max(len(data),last+L)
    size=os.path.getsize(local); lba=vol
    rec=bytearray(L); rec[0]=L; rec[2:10]=both(lba,4); rec[10:18]=both(size,4); rec[18:25]=tmpl[18:25]
    rec[25]=0; rec[28:32]=both(1,2); rec[32]=len(fid); rec[33:33+len(fid)]=fid
    with open(iso_path,'r+b') as f:
        f.seek(de.lba*SECTOR+last); f.write(rec)
        if newdir!=len(data):  # grow the directory size in its parent record and its own '.' record
            _put_both(f,de.rec_pos+10,newdir); _put_both(f,de.lba*SECTOR+10,newdir)
        f.seek(lba*SECTOR); f.write(open(local,'rb').read()); f.write(b'\0'*(-size%SECTOR))
        end=lba+(-(-size//SECTOR)); _put_both(f,16*SECTOR+80,end)
    print(f'added {ipath} at lba {lba}, {size} bytes; volume {vol}->{end}')
if __name__=='__main__': add(*sys.argv[1:4])
