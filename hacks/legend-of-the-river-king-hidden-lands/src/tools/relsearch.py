import sys, struct
def relsearch(d, vals, width=1, step=None):
    step = step or width
    diffs = [vals[i+1]-vals[i] for i in range(len(vals)-1)]
    n = len(vals)
    fmt = {1:'B',2:'<H'}[width]
    hits=[]
    for off in range(0, len(d) - n*step, 1):
        v0 = struct.unpack_from(fmt, d, off)[0]
        ok = True
        for k in range(1, n):
            if struct.unpack_from(fmt, d, off + k*step)[0] - v0 != vals[k]-vals[0]:
                ok = False; break
        if ok: hits.append((off, v0))
    return hits
