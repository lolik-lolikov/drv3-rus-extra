"""Наложить pkg/payload на оригиналы orig_src -> cur/<путь data/win>. Проверка SHA1 базы."""
import os, sys, struct, hashlib, glob
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from mkdelta import apply
PAY = os.path.join(ROOT, 'pkg/payload')
SRC = os.path.join(ROOT, 'orig_src')
OUT = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'cur')
allf = [os.path.relpath(p, SRC).replace(os.sep, '/') for p in glob.glob(SRC + '/**/*', recursive=True) if os.path.isfile(p)]
ok = bad = 0
for l in open(os.path.join(PAY, 'manifest.txt'), encoding='utf-8'):
    k, f, t = l.rstrip('\r\n').split('\t')
    if t.startswith('BYNAME:'):
        sub = t[7:]
        c = [p for p in allf if p.lower().endswith('/' + sub.lower())]
        assert len(c) == 1, (t, c)
        rel = c[0]
    else:
        rel = t[len('data/win/'):]
    if k == 'FULL':
        new = open(os.path.join(PAY, f), 'rb').read()
    else:
        sp = os.path.join(SRC, rel)
        if not os.path.exists(sp):
            print('NO ORIG', rel); bad += 1; continue
        orig = open(sp, 'rb').read(); p = open(os.path.join(PAY, f), 'rb').read()
        osz = struct.unpack_from('<Q', p, 8)[0]; osha = p[16:36]
        if osz != len(orig) or hashlib.sha1(orig).digest() != osha:
            print('BASE MISMATCH', rel); bad += 1; continue
        new = apply(orig, p)
        nsha = p[44:64]
        assert hashlib.sha1(new).digest() == nsha, rel
    o = os.path.join(OUT, rel); os.makedirs(os.path.dirname(o), exist_ok=True)
    open(o, 'wb').write(new); ok += 1
print('ok', ok, 'bad', bad)
