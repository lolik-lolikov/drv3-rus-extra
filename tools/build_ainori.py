import sys,os,re,time
sys.path.insert(0,os.path.dirname(__file__))
from drv3 import *
from check import result
out,problems,missing=result(verbose=False)
src='orig/01_salmon_team/data/win/wrd_script/007/ainori_text_US.SPC'
spc=spc_read(open(src,'rb').read())
changed=0
for e in spc['entries']:
    n=e.name[:-4]
    if n not in out: continue
    st=stx_read(e.data)
    new=[]
    for i,(sid,s) in enumerate(st['strings']):
        if i in out[n]:
            r=out[n][i].replace('\\n','\n')
            if r!=s: changed+=1
            new.append((sid,r))
        else: new.append((sid,s))
    st['strings']=new
    e.data=stx_write(st)
# правки поверх текста основного русификатора (файлы, которых нет в work/src): work/tr_main/<имя>.tsv
for e in spc['entries']:
    p=f'work/tr_main/{e.name[:-4]}.tsv'
    if not os.path.exists(p): continue
    st=stx_read(e.data); new=list(st['strings'])
    for l in open(p,encoding='utf-8'):
        if '\t' not in l: continue
        i,t=l.rstrip('\n').split('\t',1); i=int(i)
        r=t.replace('\\n','\n').replace('\\r','\r')
        if new[i][1]!=r: changed+=1
        new[i]=(new[i][0],r)
    st['strings']=new
    e.data=stx_write(st)
t=time.time()
data=spc_write(spc,compress=True)
print('strings changed',changed,'size',len(data),'time',round(time.time()-t,1))
os.makedirs('build/data/win/wrd_script',exist_ok=True)
for d in ['003','004','005','006','007']:
    os.makedirs(f'build/data/win/wrd_script/{d}',exist_ok=True)
    open(f'build/data/win/wrd_script/{d}/ainori_text_US.SPC','wb').write(data)
# verify
v=spc_read(data)
for a,b in zip(v['entries'],spc['entries']):
    assert a.name==b.name and a.data==b.data
    stx_read(a.data)
print('verify ok')
