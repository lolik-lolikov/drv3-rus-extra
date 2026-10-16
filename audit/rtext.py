import sys,re
sys.path.insert(0,'tools')
from drv3 import spc_read, rsct_read
p=[l.rstrip('\r\n').split('\t') for l in open('pkg/payload/manifest.txt',encoding='utf-8')]
f=[x for x in p if 'rsc_text_package' in x[2]][0][1]
s=spc_read(open('pkg/payload/'+f,'rb').read())
o=spc_read(open('orig_src/minigame/rsc/text/rsc_text_package_US.spc','rb').read())
O={e.name:rsct_read(e.data)['strings'] for e in o['entries']}
R={e.name:rsct_read(e.data)['strings'] for e in s['entries']}
pat=re.compile(sys.argv[1], re.I)
for k in O:
    rd=dict(R.get(k,[]))
    for h,t in O[k]:
        r=rd.get(h,'')
        if pat.search(t) or pat.search(r):
            print(k, h, repr(t)[:90], '=>', repr(r)[:90])
