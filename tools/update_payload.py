"""Обновить pkg/payload из build/: для каждого файла в build/ — новый патч DRVP к оригиналу (или FULL),
строки манифеста с теми же целями заменяются, новые добавляются; остальные (текст, шрифты, имена) не трогаются.
python3 tools/update_payload.py"""
import os, sys, glob, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from mkdelta import delta, apply, find_orig

PAY = 'pkg/payload'
man = [l.rstrip('\r\n').split('\t') for l in open(os.path.join(PAY, 'manifest.txt'), encoding='utf-8') if l.strip()]
idx = {t: i for i, (k, f, t) in enumerate(man)}
used_before = set(f for k, f, t in man)
n_new = n_upd = 0; tot = 0
for f in sorted(glob.glob('build/**/*', recursive=True)):
    if os.path.isdir(f): continue
    rel = os.path.relpath(f, 'build').replace(os.sep, '/')
    if 'wrd_script' in rel or '/rsc/text/' in rel or '/rsc/font/' in rel or 'game_resident' in rel:
        continue   # эти файлы в этой сборке не пересобираются
    target = ('BYNAME:' + rel[7:]) if rel.startswith('BYNAME/') else rel
    o = find_orig(rel)
    assert o, 'нет оригинала для ' + rel
    orig = open(o, 'rb').read(); new = open(f, 'rb').read()
    d = delta(orig, new)
    assert apply(orig, d) == new, rel
    pn = 'patch/' + rel.replace('/', '__') + '.dpatch'
    os.makedirs(os.path.join(PAY, 'patch'), exist_ok=True)
    open(os.path.join(PAY, pn), 'wb').write(d); tot += len(d)
    line = ['PATCH', pn, target]
    if target in idx:
        man[idx[target]] = line; n_upd += 1
    else:
        idx[target] = len(man); man.append(line); n_new += 1
# удалить файлы патчей, на которые больше никто не ссылается
used = set(f for k, f, t in man)
for f in used_before - used:
    p = os.path.join(PAY, f)
    if os.path.exists(p): os.remove(p)
with open(os.path.join(PAY, 'manifest.txt'), 'w', encoding='utf-8', newline='\r\n') as fh:
    for m in man: fh.write('\t'.join(m) + '\n')
print('updated', n_upd, 'new', n_new, 'entries', len(man), 'patch bytes', tot)
