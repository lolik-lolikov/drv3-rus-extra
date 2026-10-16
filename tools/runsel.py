import sys,re;sys.path.insert(0,'tools')
from texedit import build_all, expand_specs; from tex_specs import SPECS
from PIL import Image
S='scratch/'
pat=re.compile(sys.argv[1]); out=sys.argv[2]
sel=[s for s in expand_specs(SPECS) if pat.search(s['tex'])]
build_all(sel,preview=S+out+'.png')
im=Image.open(S+out+'.png'); bg=Image.new('RGBA',im.size,(40,40,50,255)); bg.alpha_composite(im)
sc=float(sys.argv[3]) if len(sys.argv)>3 else 0.5
bg.resize((int(im.width*sc),int(im.height*sc))).save(S+out+'.png'); print(im.size)
