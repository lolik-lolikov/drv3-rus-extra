"""Все текстуры в orig_src и cur (с вложенными SPC). Сравнение: изменена ли текстура.
Пишет audit/scan.json: [file, inner, srd, tex, w, h, fmt, changed(None если файла нет в cur), png_orig, png_cur]"""
import os, sys, json, glob, hashlib
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from drv3 import spc_read
from srdtex import textures, decode
import numpy as np
SRC = os.path.join(ROOT, 'orig_src'); CUR = os.path.join(ROOT, 'cur')
PO = os.path.join(ROOT, 'audit/png/o'); PC = os.path.join(ROOT, 'audit/png/c')

def walk(spc, inner=''):
    E = {e.name: e for e in spc['entries']}
    for n, e in E.items():
        if n.lower().endswith('.spc'):
            try:
                yield from walk(spc_read(e.data), (inner + '/' if inner else '') + n)
            except Exception as ex:
                print('nested fail', n, ex)
        elif n.endswith('.srd'):
            v = E.get(n + 'v')
            if v is None: continue
            try:
                ts = textures(e.data)
            except Exception:
                continue
            for t in ts:
                yield inner, n, t, v.data

def texmap(path):
    out = {}
    spc = spc_read(open(path, 'rb').read())
    for inner, n, t, v in walk(spc):
        try:
            im = decode(t, v)
        except Exception as ex:
            im = None
        out[(inner, n, t['name'])] = (t, im)
    return out

res = []
files = sorted(os.path.relpath(p, SRC).replace(os.sep, '/') for p in glob.glob(SRC + '/**/*', recursive=True) if os.path.isfile(p))
if len(sys.argv) > 1:
    files = [f for f in files if any(x in f for x in sys.argv[1:])]
for rel in files:
    if not rel.lower().endswith('.spc'): continue
    try:
        om = texmap(os.path.join(SRC, rel))
    except Exception as ex:
        print('FAIL', rel, ex); continue
    cm = texmap(os.path.join(CUR, rel)) if os.path.exists(os.path.join(CUR, rel)) else None
    for key, (t, im) in om.items():
        inner, n, tn = key
        safe = (rel + '__' + inner + '__' + (n[:-4] + '__' if n not in ('texture.srd',) else '') + tn).replace('/', '__')
        po = os.path.join(PO, safe + ('' if safe.endswith('.png') else '.png'))
        changed = None; pc = None
        if im is not None:
            os.makedirs(PO, exist_ok=True)
            if not os.path.exists(po): im.save(po)
        if cm is not None:
            ct = cm.get(key)
            if ct and ct[1] is not None and im is not None:
                a = np.array(im); b = np.array(ct[1])
                changed = bool(a.shape != b.shape or np.abs(a.astype(int) - b.astype(int)).max() > 8)
                if changed:
                    pc = os.path.join(PC, safe + ('' if safe.endswith('.png') else '.png'))
                    os.makedirs(PC, exist_ok=True); ct[1].save(pc)
            else:
                changed = 'missing'
        res.append([rel, inner, n, tn, t['w'], t['h'], t['fmt'], changed, po if im is not None else None, pc])
if len(sys.argv) > 1 and os.path.exists(os.path.join(ROOT, 'audit/scan.json')):
    # частичный пересчёт: заменить записи этих файлов в общем scan.json
    old = json.load(open(os.path.join(ROOT, 'audit/scan.json')))
    done = set(r[0] for r in res)
    res = [r for r in old if r[0] not in done] + res
json.dump(res, open(os.path.join(ROOT, 'audit/scan.json'), 'w'), ensure_ascii=False, indent=0)
import collections
print('textures', len(res))
print(collections.Counter(str(r[7]) for r in res))
