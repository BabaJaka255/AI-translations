"""Name tables are keyed by a hash of the Japanese text, not the text itself, so the repo
carries no game text. Look-ups still use the Japanese string decoded from your ROM."""
import hashlib
def h(jp): return jp if jp.startswith('h:') else 'h:'+hashlib.sha1(jp.encode('utf-8')).hexdigest()[:16]
class HDict(dict):
    def __init__(self,*a,**k): super().__init__(); self.update(*a,**k)
    def __contains__(self,k): return super().__contains__(h(k))
    def __getitem__(self,k): return super().__getitem__(h(k))
    def __setitem__(self,k,v): super().__setitem__(h(k),v)
    def get(self,k,d=None): return super().get(h(k),d)
    def update(self,*a,**k):
        for m in a+(k,):
            for kk,v in (m.items() if hasattr(m,'items') else m): self[kk]=v
