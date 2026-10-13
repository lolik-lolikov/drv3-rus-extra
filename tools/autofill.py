"""Fill formulaic lines (stat increases) into work/rtr files across all rsrc files."""
import sys,os,re,glob
sys.path.insert(0,os.path.dirname(__file__))
from statgen import tr as stat_tr
from rpggen import tr as rpg_tr
tot=0
for f in sorted(glob.glob('work/rsrc/*.txt')):
    n=os.path.basename(f)[:-4]; p=f'work/rtr/{n}.tsv'
    have={}
    if os.path.exists(p):
        for l in open(p):
            if '\t' in l: i,t=l.rstrip('\n').split('\t',1); have[int(i)]=t
    add={}
    for l in open(f):
        i,s,t=l.rstrip('\n').split('\t',2); i=int(i)
        t=re.sub(r' \[TM: .*\]$','',t)
        if i in have: continue
        r=stat_tr(t) or (rpg_tr(t) if n.startswith('ui__RPGText') else None)
        if r: add[i]=r
    if add:
        have.update(add); tot+=len(add)
        open(p,'w').write(''.join(f'{i}\t{have[i]}\n' for i in sorted(have)))
        print(n,len(add))
print('total',tot)
