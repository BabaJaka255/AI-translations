"""Upload COMM.TIM from a built disc into an emulator's VRAM, so old save states show new font/labels."""
import ctypes as C, tim
from iso import read_extent, listing

def comm_from(binf, name='TIM/COMM.TIM'):
    for n, l, sz in listing(binf):
        if n.split(';')[0].lstrip('/') == name:
            return read_extent(open(binf, 'rb'), l, sz)

def upload(e, binf='test.bin'):
    comm = comm_from(binf)
    st = bytearray(e.state()); o = st.find(b'GPURAM[0][0]') + 16
    p = 0
    while p + 8 <= len(comm):
        try: t = tim.parse(comm, p)
        except AssertionError: break
        for part in (t['clut'], t['img']):
            if part is None: continue
            for y in range(part['h']):
                a = o + (((part["y"] + y) % 512) * 1024 + part['x']) * 2
                st[a:a + part['w'] * 2] = part['data'][y].tobytes()
        p = t['end']
    e.lib.retro_unserialize(bytes(st), C.c_size_t(len(st)))
