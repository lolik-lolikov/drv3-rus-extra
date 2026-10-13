# usage: show.py name [name...]  -> prints lines needing translation, with TM'd lines as context
import sys,re,json,os
sys.path.insert(0,os.path.dirname(__file__))
from tmlib import load_tm
tm=load_tm()
for n in sys.argv[1:]:
    tr={}
    p=f'work/tr/{n}.tsv'
    if os.path.exists(p):
        for l in open(p):
            if '\t' in l: i,t=l.rstrip('\n').split('\t',1); tr[int(i)]=t
    print('###',n)
    for l in open(f'work/src/{n}.txt'):
        i,s,t=l.rstrip('\n').split('\t',2)
        t=re.sub(r' \[TM: .*\]$','',t)
        if int(i) in tr: print(f'{i}|{s}|{t}  ==> {tr[int(i)]}')
        elif t in tm: print(f'{i}|{s}|= {tm[t]}')
        elif not re.search('[A-Za-z]',t): print(f'{i}|{s}|= {t}')
        else: print(f'{i}|{s}|{t}')
