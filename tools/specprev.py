"""Предпросмотр описаний без сборки архивов: python3 tools/specprev.py <regex по tex|arch> <out.png> [масштаб]"""
import sys, re, json, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
from PIL import Image, ImageDraw
import texedit
from tex_specs import SPECS
pat = re.compile(sys.argv[1]); out = sys.argv[2]; sc = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
res = json.load(open('audit/scan.json'))
idx = {}
for r in res:
    if r[8]:
        idx.setdefault((os.path.basename(r[0]), r[3]), []).append(r)
sel = [s for s in texedit.expand_specs(SPECS) if pat.search(s['tex']) or pat.search(s['arch'])]
print(len(sel), 'specs')
def checker(w, h):
    im = Image.new('RGBA', (w, h), (70, 70, 80, 255)); d = ImageDraw.Draw(im)
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            if (x // 16 + y // 16) % 2: d.rectangle((x, y, x + 15, y + 15), fill=(100, 100, 110, 255))
    return im
rows = []
for s in sel:
    key = (os.path.basename(s.get('inner') or s['arch']), s['tex'])
    cand = idx.get(key, [])
    if s.get('srd'):
        cand = [r for r in cand if r[2] == s['srd']] or cand
    if not cand:
        print('no png for', key); continue
    o = Image.open(cand[0][8]).convert('RGBA')
    n = texedit.apply_spec(o, s)
    rows.append((s['arch'].split('/')[-1] + ':' + s['tex'], o, n))
W = 0; H = 0; prepared = []
for name, o, n in rows:
    f = min(sc, 900 / o.width)
    a = o.resize((max(1, int(o.width * f)), max(1, int(o.height * f))), Image.LANCZOS)
    b = n.resize(a.size, Image.LANCZOS)
    prepared.append((name, a, b)); W = max(W, a.width * 2 + 30); H += a.height + 22
C = Image.new('RGBA', (W, H), (30, 30, 36, 255)); d = ImageDraw.Draw(C); y = 0
for name, a, b in prepared:
    d.text((2, y), name, fill=(255, 255, 0, 255)); y += 14
    c1 = checker(*a.size); c1.alpha_composite(a); C.paste(c1, (0, y))
    c2 = checker(*b.size); c2.alpha_composite(b); C.paste(c2, (a.width + 20, y)); y += a.height + 8
C.save(out); print(C.size)
