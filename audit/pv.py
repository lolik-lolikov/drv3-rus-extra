"""Быстрый предпросмотр: python3 audit/pv.py OUT.png scale tex1 [tex2 ...]
Для каждой текстуры (по точному имени или подстроке; можно arch_substr:tex) — оригинал | текущий (v2.3) | новый (по tex_specs)."""
import os, sys, json, importlib
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
os.chdir(ROOT)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import texedit
from tex_specs import SPECS
from drv3 import spc_read
from srdtex import textures, decode
res = json.load(open('audit/scan.json'))
out = sys.argv[1]; scale = float(sys.argv[2]); names = sys.argv[3:]
specs = texedit.expand_specs(SPECS)
F = ImageFont.truetype('work/fonts/rubik_400.ttf', 14)
def orig_img(s):
    spc = texedit.load_arch(s['arch']); tgt = spc
    if s.get('inner'):
        tgt = spc_read([e for e in spc['entries'] if e.name == s['inner']][0].data)
    E = {e.name: e for e in tgt['entries']}
    for n in E:
        if n.endswith('.srd') and n + 'v' in E and (not s.get('srd') or s['srd'] == n):
            for t in textures(E[n].data):
                if t['name'] == s['tex']: return decode(t, E[n + 'v'].data)
def cur_img(s):
    base = os.path.basename(s['arch'])
    for r in res:
        if os.path.basename(r[0]) == base and r[3] == s['tex'] and (not s.get('inner') or s['inner'] in r[1]) and (not s.get('srd') or s['srd'] == r[2]):
            return Image.open(r[9]).convert('RGBA') if r[9] else Image.open(r[8]).convert('RGBA')
def checker(w, h):
    im = Image.new('RGBA', (w, h), (80, 80, 90, 255)); d = ImageDraw.Draw(im)
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            if (x // 16 + y // 16) % 2: d.rectangle((x, y, x + 15, y + 15), fill=(110, 110, 120, 255))
    return im
rows = []; seen = set()
for nm in names:
    a_f, t_f = (nm.split(':', 1) if ':' in nm else ('', nm))
    for s in specs:
        if (s['tex'] == t_f or (t_f.endswith('*') and t_f[:-1] in s['tex'])) and a_f in s['arch'] + '|' + s.get('inner', ''):
            key = (s['tex'], s.get('srd'), os.path.basename(s['arch']).split('_US')[0][:8] if 'rsc' not in s['arch'] else s['tex'])
            if key in seen and not os.environ.get('ALL'): continue
            seen.add(key)
            o = orig_img(s); c = cur_img(s); n = texedit.apply_spec(o, s)
            ab = texedit.allowed_box(o, dict(s))
            a = np.array(n)[:, :, 3]; ys, xs = np.where(a > 40)
            bad = len(xs) and not (xs.min() >= ab[0] and ys.min() >= ab[1] and xs.max() < ab[2] and ys.max() < ab[3])
            rows.append(('%s:%s%s' % (os.path.basename(s['arch']), s['tex'], '  !!! КРАЙ' if bad else ''), [o, c, n]))
W = max(sum(int(i.width * scale) + 10 for i in ims if i is not None) for _, ims in rows)
H = sum(int(ims[0].height * scale) + 20 for _, ims in rows)
C = Image.new('RGBA', (max(W, 400), H), (30, 30, 36, 255)); d = ImageDraw.Draw(C); y = 0
for lab, ims in rows:
    d.text((2, y), lab, font=F, fill=(255, 120, 120, 255) if '!!!' in lab else (255, 230, 80, 255)); y += 18; x = 0
    for i in ims:
        if i is None: continue
        i2 = i.resize((max(1, int(i.width * scale)), max(1, int(i.height * scale))), Image.LANCZOS if scale < 1 else Image.NEAREST)
        C.alpha_composite(checker(*i2.size), (x, y)); C.alpha_composite(i2, (x, y)); x += i2.width + 10
    y += int(ims[0].height * scale) + 2
C.convert('RGB').save(out); print(len(rows), 'rows', C.size, 'EDGE:', [r[0] for r in rows if '!!!' in r[0]])
