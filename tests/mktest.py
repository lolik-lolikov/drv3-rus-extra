"""Синтетическая копия игры для проверки установщика: CPK как у игры, payload как у настоящего
(те же типы строк и цели), но содержимое случайное.
python3 tests/mktest.py OUT  -> OUT/clean (чистая игра), OUT/payload, OUT/expect.json"""
import os, sys, json, random, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from cpkmake import build
from mkdelta import delta, apply
OUT = sys.argv[1]
random.seed(7)
def rnd(n): return bytes(random.getrandbits(8) for _ in range(n))
man = [l.rstrip('\r\n').split('\t') for l in open(os.path.join(os.path.dirname(__file__), '..', 'pkg', 'payload', 'manifest.txt'), encoding='utf-8') if l.strip()]
us = {}; res = {}; base = {}
def target_paths(t):
    if t.startswith('BYNAME:'):
        sub = t[7:]
        if '/' in sub: return ['flash/success/' + sub]
        if sub.startswith('effect_'): return ['minigame/rsc/effect/' + sub, 'minigame/rsc/effect2/' + sub]   # одно имя в двух папках
        return ['flash/misc/' + sub]
    return [t.replace('data/win/', '', 1)]
pay = os.path.join(OUT, 'payload'); os.makedirs(os.path.join(pay, 'full'), exist_ok=True); os.makedirs(os.path.join(pay, 'patch'), exist_ok=True)
expect = {}
mf = []
full_cache = {}
for kind, f, t in man:
    paths = target_paths(t)
    if kind == 'FULL':
        if f not in full_cache: full_cache[f] = rnd(3000)
        new = full_cache[f]
        open(os.path.join(pay, f), 'wb').write(new)
        for p in paths:
            (res if p.startswith('game_resident') else us)[p] = rnd(2500)
            expect[p] = hashlib.sha1(new).hexdigest()
        mf.append((kind, f, t)); continue
    # PATCH/PATCHA: один исходник на все цели (как в игре: одинаковые файлы в разных папках)
    orig = rnd(4000 + random.randint(0, 3000))
    new = bytearray(orig); new[100:140] = rnd(40); new += rnd(500); new = bytes(new)
    d = delta(orig, new); assert apply(orig, d) == new
    open(os.path.join(pay, f), 'wb').write(d)
    for p in paths:
        (res if p.startswith('game_resident') else us)[p] = orig
        expect[p] = hashlib.sha1(new).hexdigest()
    mf.append((kind, f, t))
with open(os.path.join(pay, 'manifest.txt'), 'w', encoding='utf-8', newline='\r\n') as fh:
    for m in mf: fh.write('\t'.join(m) + '\n')
for i in range(40): us['model/m%02d/file_%02d_US.spc' % (i % 7, i)] = rnd(1000 + i * 50)
for i in range(8): res['font/f%02d.spc' % i] = rnd(1500)
main = {'boot/boot_%d.spc' % i: rnd(800) for i in range(10)}
G = os.path.join(OUT, 'clean'); W = os.path.join(G, 'data', 'win'); os.makedirs(W, exist_ok=True)
open(os.path.join(G, 'Dangan3Win.exe'), 'wb').write(b'MZ fake')
def mk(name, d):
    files = sorted(((p.rsplit('/', 1)[0], p.rsplit('/', 1)[1], b) for p, b in d.items()), key=lambda x: (x[0], x[1]))
    build(os.path.join(W, name), files)
mk('partition_data_win_us.cpk', us); mk('partition_resident_win.cpk', res); mk('partition_data_win.cpk', main)
json.dump({'translated': expect, 'us': {p: hashlib.sha1(b).hexdigest() for p, b in us.items()},
           'res': {p: hashlib.sha1(b).hexdigest() for p, b in res.items()}}, open(os.path.join(OUT, 'expect.json'), 'w'), indent=0)
# «основной русификатор»: все файлы распакованы, шрифт свой, один переводимый файл им изменён
R = os.path.join(OUT, 'mainrus'); RW = os.path.join(R, 'data', 'win'); os.makedirs(RW, exist_ok=True)
open(os.path.join(R, 'Dangan3Win.exe'), 'wb').write(b'MZ fake')
import shutil; shutil.copy(os.path.join(W, 'partition_data_win.cpk'), RW)
for p, b in list(us.items()) + list(res.items()):
    q = os.path.join(RW, p); os.makedirs(os.path.dirname(q), exist_ok=True)
    if p == 'game_resident/game_resident_US.spc': b = b'RUSFONT' + rnd(3000)
    if p.endswith('casino_coin_US.spc'): b = b + b'mainrus'
    open(q, 'wb').write(b)
print('ok', len(us), len(res), len(mf))
