"""Fill untranslated lines from already translated identical lines (same speaker+English) in other rtr files.
usage: rtmfill.py [name ...]  (default: all)"""
import sys,os,re,glob
def load(n):
    src=[l.rstrip('\n').split('\t',2) for l in open(f'work/rsrc/{n}.txt')]
    tr={}
    p=f'work/rtr/{n}.tsv'
    if os.path.exists(p):
        for l in open(p):
            if '\t' in l: i,t=l.rstrip('\n').split('\t',1); tr[int(i)]=t
    return src,tr
names=[os.path.basename(f)[:-4] for f in sorted(glob.glob('work/rsrc/*.txt'))]
mem={}
for n in names:
    if n.startswith('ui__'): continue
    src,tr=load(n)
    for i,s,t in src:
        if int(i) in tr: mem.setdefault((s,t),tr[int(i)])
targets=sys.argv[1:] or names
tot=0
for n in targets:
    if n.startswith('ui__'): continue
    src,tr=load(n); add=0
    for i,s,t in src:
        i=int(i)
        if i not in tr and (s,t) in mem: tr[i]=mem[(s,t)]; add+=1
    if add:
        open(f'work/rtr/{n}.tsv','w').write(''.join(f'{i}\t{tr[i]}\n' for i in sorted(tr)))
        print(n,add); tot+=add
print('filled',tot)
