import sys;sys.path.insert(0,'tools')
from texedit import build_all, expand_specs; from tex_specs import SPECS
from PIL import Image
S='scratch/'
flt=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>2 else 'prev'
sel=[s for s in expand_specs(SPECS) if flt in s['tex'] or flt in s['arch']]
print(len(sel),'specs')
build_all(sel,preview=S+out+'.png')
im=Image.open(S+out+'.png'); bg=Image.new('RGBA',im.size,(40,40,50,255)); bg.alpha_composite(im); bg.save(S+out+'.png'); print(im.size)
