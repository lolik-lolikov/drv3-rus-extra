"""Контактные листы текстур. python3 audit/contact.py OUTPREFIX mode [filters...]
mode: unchanged | changed | all"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.join(os.path.dirname(__file__), '..')
res = json.load(open(os.path.join(ROOT, 'audit/scan.json')))
out, mode = sys.argv[1], sys.argv[2]; flt = sys.argv[3:]
F = ImageFont.truetype(os.path.join(ROOT, 'work/fonts/rubik_400.ttf'), 13)
TW, TH = int(os.environ.get('TW', 360)), int(os.environ.get('TH', 260))
items = []
for r in res:
    if r[8] is None: continue
    if mode == 'unchanged' and r[7] is True: continue
    if mode == 'changed' and r[7] is not True: continue
    if flt and not any(f in r[0] + '|' + r[1] + '|' + r[3] for f in flt): continue
    if any(x in r[0] for x in os.environ.get('EXCL', '').split(',') if x): continue
    items.append(r)
def checker(w, h):
    im = Image.new('RGBA', (w, h), (95, 95, 105, 255)); d = ImageDraw.Draw(im)
    for y in range(0, h, 12):
        for x in range(0, w, 12):
            if (x // 12 + y // 12) % 2: d.rectangle((x, y, x + 11, y + 11), fill=(125, 125, 135, 255))
    return im
W = 1500; page = 0; x = y = 0; rowh = 0
C = None; labels = []
def flush():
    global C, page
    if C is not None:
        C.convert('RGB').save(f'{out}_{page:02d}.png'); page += 1
    C = None
idx = 0
lst = open(out + '_list.txt', 'w')
for r in items:
    im = Image.open(r[8]).convert('RGBA')
    if mode == 'changed' and r[9]:
        b = Image.open(r[9]).convert('RGBA')
        comb = Image.new('RGBA', (im.width * 2 + 8, im.height), (0, 0, 0, 0))
        comb.paste(im, (0, 0)); comb.paste(b, (im.width + 8, 0)); im = comb
    k = min(1.0, TW / im.width, TH / im.height)
    th = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    cw, ch = max(th.width, 200), th.height + 16
    if C is None:
        C = Image.new('RGBA', (W, 1700), (40, 40, 48, 255)); x = y = 0; rowh = 0
    if x + cw > W:
        x = 0; y += rowh + 6; rowh = 0
    if y + ch > 1700:
        flush(); C = Image.new('RGBA', (W, 1700), (40, 40, 48, 255)); x = y = 0; rowh = 0
    d = ImageDraw.Draw(C)
    lab = '#%d %s:%s %dx%d' % (idx, os.path.basename(r[0]).replace('_US', '').replace('.spc', '').replace('.SPC', ''), r[3].replace('.png', ''), r[4], r[5])
    d.text((x + 2, y), lab[:int(cw / 6.5)], font=F, fill=(255, 230, 80, 255))
    C.alpha_composite(checker(th.width, th.height), (x, y + 16)); C.alpha_composite(th, (x, y + 16))
    lst.write('#%d\t%s\t%s\t%s\t%dx%d\t%s\n' % (idx, r[0], r[1], r[3], r[4], r[5], r[8]))
    x += cw + 8; rowh = max(rowh, ch); idx += 1
flush()
print(len(items), 'items', page, 'pages')
