import os,sys,re,collections,json
sys.path.insert(0,'tools')
from drv3 import *
root='orig'
files={}
for d in sorted(os.listdir(root)):
    for dp,dn,fn in os.walk(os.path.join(root,d)):
        for f in fn:
            full=os.path.join(dp,f); rel=os.path.relpath(full,os.path.join(root,d))
            if rel.lower().endswith('.spc'): files.setdefault(rel,full)
cyr=re.compile('[А-Яа-яЁё]'); lat=re.compile('[A-Za-z]'); jp=re.compile('[぀-ヿ一-鿿]')
report=[]
for rel,full in sorted(files.items()):
    buf=open(full,'rb').read()
    try: spc=spc_read(buf)
    except Exception as ex:
        report.append((rel,'ERR '+str(ex)[:80])); continue
    exts=collections.Counter(os.path.splitext(e.name)[1] for e in spc['entries'])
    nstr=0;nc=0;nl=0;nj=0
    for e in spc['entries']:
        if e.name.endswith('.stx'):
            try:
                st=stx_read(e.data)
            except Exception as ex:
                continue
            for _,s in st['strings']:
                nstr+=1
                if cyr.search(s): nc+=1
                elif jp.search(s): nj+=1
                elif lat.search(s): nl+=1
    report.append((rel,f"{len(spc['entries'])} ent {dict(exts)} | stx strings {nstr}: ru={nc} en={nl} jp={nj}"))
for r in report: print(r[0],'::',r[1])
