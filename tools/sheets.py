"""Листы сравнения: оригинал | перевод. python3 tools/sheets.py OUTDIR [фильтр]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont
import texedit
from tex_specs import SPECS
OUT = sys.argv[1]; flt = sys.argv[2].split(',') if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)
specs = texedit.expand_specs(SPECS)
seen = set(); items = []
for s in specs:
    key = s['tex'] + '|' + s.get('inner', '') if s.get('inner') else s['tex']
    if key in seen: continue
    if flt and not any(f in s['arch'] + ':' + s['tex'] for f in flt): continue
    seen.add(key); items.append(s)
from drv3 import spc_read
from srdtex import textures, decode
cache = {}
def orig_img(s):
    spc = texedit.load_arch(s['arch'])
    tgt = spc
    if s.get('inner'):
        tgt = spc_read([e for e in spc['entries'] if e.name == s['inner']][0].data)
    E = {e.name: e for e in tgt['entries']}
    for n in E:
        if n.endswith('.srd') and n + 'v' in E:
            for t in textures(E[n].data):
                if t['name'] == s['tex']: return decode(t, E[n + 'v'].data)
F = ImageFont.truetype(os.path.join(texedit.ROOT, 'work/fonts/rubik_400.ttf'), 15)
def checker(w, h):
    im = Image.new('RGBA', (w, h), (90, 90, 100, 255)); d = ImageDraw.Draw(im)
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            if (x // 16 + y // 16) % 2: d.rectangle((x, y, x + 15, y + 15), fill=(120, 120, 130, 255))
    return im
rows = []
for s in items:
    try:
        o = orig_img(s); n = texedit.apply_spec(o, s)
    except Exception as ex:
        print('ERR', s['tex'], ex); continue
    k = min(1.0, 700 / o.width, 260 / o.height)
    sz = (max(1, int(o.width * k)), max(1, int(o.height * k)))
    rows.append((s, o.resize(sz, Image.LANCZOS), n.resize(sz, Image.LANCZOS)))
page = 0; i = 0
while i < len(rows):
    chunk = []; H = 0
    while i < len(rows) and (H + rows[i][1].height + 26 < 1500 or not chunk):
        chunk.append(rows[i]); H += rows[i][1].height + 26; i += 1
    W = max(r[1].width for r in chunk) * 2 + 30
    C = Image.new('RGBA', (W, H), (40, 40, 48, 255)); d = ImageDraw.Draw(C); y = 0
    for s, o, n in chunk:
        lab = '%s  [%s]  %s' % (s['tex'], s['arch'].split('/')[-1], (s.get('text') or '').replace('\n', ' / '))
        d.text((4, y + 2), lab[:120], font=F, fill=(255, 230, 80, 255))
        y += 22
        C.alpha_composite(checker(*o.size), (0, y)); C.alpha_composite(o, (0, y))
        C.alpha_composite(checker(*n.size), (o.width + 30, y)); C.alpha_composite(n, (o.width + 30, y))
        y += o.height + 4
    C.convert('RGB').save(os.path.join(OUT, 'sheet_%02d.png' % page)); page += 1
    if len(sys.argv) > 3 and page >= int(sys.argv[3]): break
print('items', len(rows), 'pages', page)
