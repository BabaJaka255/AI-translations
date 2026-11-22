hira='あいうえおかきくけこさしすせそたちつってとなにぬねのはひふへほまみむめもやゃゆゅよょらりるれろわをん'
kata='アァイィウゥエェオォカキクケコサシスセソタチツッテトナニヌネノハヒフヘホマミムメモヤャユュヨョラリルレロワヲン'
T={}
for i in range(10): T[i]=str(i)
for i in range(26): T[0x0a+i]=chr(65+i)
for i,c in enumerate(hira): T[0x24+i]=c
for i,c in enumerate(kata): T[0x56+i]=c
def dec(data,ctrl=True):
    s=''
    for b in data: s+=T.get(b,'[%02x]'%b)
    return s
