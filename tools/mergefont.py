"""Склейка подмножеств fontsource (latin + cyrillic) в один TTF.
python3 tools/mergefont.py OUT.ttf in1.woff in2.woff ..."""
import sys
from fontTools.ttLib import TTFont
from fontTools.merge import Merger
out, ins = sys.argv[1], sys.argv[2:]
tmp = []
for i, p in enumerate(ins):
    f = TTFont(p); f.flavor = None
    t = '/tmp/_mf_%d.ttf' % i; f.save(t); tmp.append(t)
m = Merger().merge(tmp)
m.save(out)
print(out, len(m.getGlyphOrder()))
