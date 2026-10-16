"""Пересобрать только указанные архивы целиком (все их описания): python3 tools/build_arch.py имя_архива [имя ...]
(имя — подстрока имени файла архива, например ainori_day_change_US.spc)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
from texedit import build_all, expand_specs
from tex_specs import SPECS
names = sys.argv[1:]
specs = expand_specs(SPECS)
archs = sorted(set(s['arch'] for s in specs if any(n == os.path.basename(s['arch']) or n in os.path.basename(s['arch']) for n in names)))
sel = [s for s in specs if s['arch'] in archs]
print('архивы:', archs, '| описаний:', len(sel))
build_all(sel)
