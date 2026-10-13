"""Листы текстур _US, которых нет в tex_specs (кандидаты на перевод)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont
import texedit
from tex_specs import SPECS
OUT = sys.argv[1]; flt = sys.argv[2:] 
os.makedirs(OUT, exist_ok=True)
done = set(s['tex'] for s in SPECS)
ix = json.load(open('work/tex/index.json'))
F = ImageFont.truetype('work/fonts/rubik_400.ttf', 14)
rows = []; seen = set()
for f, n, t, w, h, fmt, p in ix:
    if p == 'ERR' or '_US' not in t or t in done: continue
    if flt and not any(x in f for x in flt): continue
    if f.startswith('orig/10_vanilla'): continue
    key = (os.path.basename(f), t)
    if key in seen: continue
    seen.add(key)
    im = Image.open(p).convert('RGBA')
    k = min(1.0, 520 / im.width, 200 / im.height)
    rows.append(('%s : %s (%dx%d)' % (os.path.basename(f), t, w, h), im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))))))
page = 0; i = 0
while i < len(rows):
    chunk = []; H = 0
    while i < len(rows) and (H + rows[i][1].height + 20 < 1500 or not chunk):
        chunk.append(rows[i]); H += rows[i][1].height + 20; i += 1
    W = 1100
    C = Image.new('RGBA', (W, H), (70, 70, 85, 255)); d = ImageDraw.Draw(C); y = 0
    for lab, im in chunk:
        d.text((4, y + 2), lab, font=F, fill=(255, 230, 80, 255)); y += 18
        C.alpha_composite(im, (0, y)); y += im.height + 2
    C.convert('RGB').save(os.path.join(OUT, 'u_%02d.png' % page)); page += 1
print('textures', len(rows), 'pages', page)
