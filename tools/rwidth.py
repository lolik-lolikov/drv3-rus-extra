"""Pixel width of a string in the rebuilt minigame font."""
import sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
from drv3 import spc_read
from spft import parse_srd_font
_W=None
def widths():
    global _W
    if _W is None:
        spc=spc_read(open(os.path.join(os.path.dirname(__file__),'..','build/data/win/minigame/rsc/font/rsc_font00_US.spc'),'rb').read())
        f=parse_srd_font({e.name:e for e in spc['entries']}['v3_rsc_font00.stx'].data)
        sa=lambda v:v-256 if v>127 else v
        _W={chr(c):sa(e['a'])+e['w']+sa(e['b']) for c,e in zip(f['chars'],f['ents'])}
    return _W
def width(s):
    W=widths(); s=re.sub(r'<[^>]*>','',s)
    s=re.sub(r'\$\{[^}]*\}','XXXXXXXX',s)
    return sum(W.get(ch,W.get('m',30)) for ch in s)
if __name__=='__main__':
    for a in sys.argv[1:]: print(width(a),a)
