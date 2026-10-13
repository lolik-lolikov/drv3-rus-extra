import sys;sys.path.insert(0,'tools')
from texedit import build_all
from tex_specs import SPECS
S='/tmp/claude-0/-home-claude/4936e529-f043-5c61-947c-25fc9b8e788c/scratchpad/'
pv=build_all(SPECS,preview=S+'all_prev.png')
print('textures',len(pv))
