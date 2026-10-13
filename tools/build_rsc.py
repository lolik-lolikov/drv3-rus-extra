"""Merge work/rtr translations into rsc_text_package_US.spc."""
import sys,os,json,re
sys.path.insert(0,os.path.dirname(__file__))
from drv3 import *
from tmlib import load_rtm
SRC='orig/08_batch1/1/rsc_text_package_US.spc'
OUT='build/data/win/minigame/rsc/text/rsc_text_package_US.spc'
def unesc(s): return s.replace('\\r','\r').replace('\\n','\n')
def esc(s): return s.replace('\r','\\r').replace('\n','\\n')
def main():
    tm=load_rtm()
    spc=spc_read(open(SRC,'rb').read())
    ents={e.name:e for e in spc['entries']}
    tabs={n:rsct_read(e.data) for n,e in ents.items() if n.endswith('.rsct')}
    idx=json.load(open('work/rsc_index.json'))
    done=tot=0
    for name,f,start,n in idx:
        p=f'work/rtr/{name}.tsv'; tr={}
        if os.path.exists(p):
            for l in open(p):
                if '\t' in l:
                    i,t=l.rstrip('\n').split('\t',1); tr[int(i)]=t
        S=tabs[f]['strings']
        for i in range(n):
            h,s=S[start+i]; tot+=1
            e=esc(s)
            if i in tr: new=tr[i]
            elif e in tm: new=tm[e]
            else: continue
            S[start+i]=(h,unesc(new)); done+=1
    for n,r in tabs.items():
        d=rsct_write(r)
        assert rsct_read(d)['strings']==r['strings']
        ents[n].data=d
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    open(OUT,'wb').write(spc_write(spc,compress=True))
    print(f'translated {done}/{tot} strings ->',OUT)
if __name__=='__main__': main()
