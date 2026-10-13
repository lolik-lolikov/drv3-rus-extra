"""Rebalance line breaks in work/rtr/<name>.tsv for dialogue lines exceeding pixel width.
usage: rwrap.py name [name...]   (only touches lines whose widest line > LIMIT)"""
import sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
from rwidth import width
LIMIT=1350
def best_split(text, nlines):
    if nlines==1: return [text]
    cuts=[m.start() for m in re.finditer(' ',text)]+[m.end() for m in re.finditer(r'-(?=[^ ])',text)]
    best=None
    for c in cuts:
        a=text[:c].rstrip(' '); b=text[c:].lstrip(' ')
        w=max(width(a),width(b))
        if re.search(r'(^|\s)[вскиаоуВСКИАОУ]$',a) or re.search(r'(^|\s)(на|по|за|из|от|до|не|ни|об|во|со|ко)$',a): w+=400
        if best is None or w<best[0]: best=(w,[a,b])
    return best[1] if best else [text]
def fix(r):
    if '\\r' in r: return r
    segs=r.split('\\n')
    if max(width(s) for s in segs)<=LIMIT and len(segs)<=2: return r
    flat=' '.join(s.strip() for s in segs)
    if width(flat)<=LIMIT: return flat
    return '\\n'.join(best_split(flat,2))
for n in sys.argv[1:]:
    p=f'work/rtr/{n}.tsv'; out=[]; ch=0
    for l in open(p):
        l=l.rstrip('\n')
        if '\t' in l:
            i,t=l.split('\t',1); t2=fix(t)
            if t2!=t: ch+=1
            out.append(f'{i}\t{t2}')
        elif l: out.append(l)
    open(p,'w').write('\n'.join(out)+'\n')
    if ch: print(n,'rewrapped',ch)
