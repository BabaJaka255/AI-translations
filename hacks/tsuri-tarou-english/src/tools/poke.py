"""Poke WRAM bytes in a snes9x savestate: poke.py IN OUT ADDR=VAL [ADDR=VAL ...] (hex, ADDR is a $7E offset)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s9xstate as S
st = open(sys.argv[1], 'rb').read(); ram = bytearray(S.get(st, 'RAM'))
for kv in sys.argv[3:]:
    a, v = kv.split('='); ram[int(a, 16)] = int(v, 16)
open(sys.argv[2], 'wb').write(S.put(st, 'RAM', bytes(ram)))
