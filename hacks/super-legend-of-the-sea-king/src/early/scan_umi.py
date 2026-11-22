import sys,re,struct,lzss
rom=open(sys.argv[1],'rb').read()
pat=re.compile(rb'\xa9(..)\x85\x3e\xa9(.)\x00\x85\x40\xa9(..)\x85\x42(?:\xa9(.)\x00\x85\x44)?\x22(\xd0|\xcc)\x85\x80',re.S)
blocks={}
for m in pat.finditer(rom):
    a=struct.unpack('<H',m.group(1))[0]; b=m.group(2)[0]; dst=struct.unpack('<H',m.group(3))[0]
    blocks.setdefault((b,a),[]).append((m.start(),dst,m.group(5)[0]))
print(len(blocks),'blocks', sum(len(v) for v in blocks.values()),'sites')
ok=0
for (b,a),sites in sorted(blocks.items()):
    try: d,n=lzss.decompress(rom,lzss.lo(b,a)); ok+=1
    except Exception as e: print('fail %02X:%04X'%(b,a)); continue
    print('%02X:%04X len %5d comp %5d sites %s'%(b,a,len(d),n,[('%05X'%s,'%04X'%dst,'vram' if k==0xd0 else 'wram') for s,dst,k in sites][:3]))
print('ok',ok)
