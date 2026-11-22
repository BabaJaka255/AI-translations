import sys, struct
sys.path.insert(0, 'tools')
from table import T
def ch(w):
    if w >= 0xfff0: return '{%X}' % (w & 0xf)
    return T.get(w, '[%x]' % w)
def dec(d, a, b):
    return ''.join(ch(struct.unpack_from('<H', d, i)[0]) for i in range(a, b, 2))
if __name__ == '__main__':
    d = open('files/SLPS_015.36', 'rb').read()
    a, b = int(sys.argv[1], 16), int(sys.argv[2], 16)
    print(dec(d, a, b))
