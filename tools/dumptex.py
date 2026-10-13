import sys,os,glob,json
sys.path.insert(0,os.path.dirname(__file__))
from drv3 import *; from srdtex import *
out='work/tex'; index=[]
files=sorted(set(glob.glob('orig/**/*.spc',recursive=True)+glob.glob('orig/**/*.SPC',recursive=True)))
for f in files:
    try: spc=spc_read(open(f,'rb').read())
    except Exception as ex: continue
    E={e.name:e.data for e in spc['entries']}
    for n,d in E.items():
        if not n.endswith('.srd'): continue
        v=E.get(n+'v') or E.get(n[:-4]+'.srdv')
        if not v: continue
        try: ts=textures(d)
        except Exception: continue
        key=f.replace('orig/','').replace('/','__')
        for t in ts:
            try: im=decode(t,v)
            except Exception as ex: index.append((f,n,t['name'],t['w'],t['h'],t['fmt'],'ERR')); continue
            p=f'{out}/all/{key}__{t["name"]}'
            if not p.endswith('.png'): p+='.png'
            os.makedirs(os.path.dirname(p),exist_ok=True); im.save(p)
            index.append((f,n,t['name'],t['w'],t['h'],t['fmt'],p))
json.dump(index,open(f'{out}/index.json','w'),indent=0)
print(len(index), sum(1 for x in index if x[-1]=='ERR'))
