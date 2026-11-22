"""Show how English lines wrap in the 2x18 line buffer.  python3 tools/knt_fit.py "text" ..."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from knt_build import Encoder, ROW
enc = Encoder()
for s in sys.argv[1:]:
    try:
        r1, r2 = enc.layout(s)
        rows = [r for r in (r1, r2) if r is not None]
        txt = ["".join(v if t == "ch" else f"<{v}>" for t, v in r) for r in rows]
        ok = all(enc.width(r) <= ROW for r in rows)
        print(("OK " if ok else "BAD"), " | ".join(f"{x:<18}" for x in txt))
    except Exception as e:
        print("BAD", e)
