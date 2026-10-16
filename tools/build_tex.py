import sys;sys.path.insert(0,'tools')
from texedit import build_all
from tex_specs import SPECS
S='scratch/'
pv=build_all(SPECS,preview=S+'all_prev.png')
print('textures',len(pv))
