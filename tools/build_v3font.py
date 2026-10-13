"""Add Cyrillic glyphs to the main dialogue font v3_font00 (game_resident_US.spc, vanilla) — for installs without the main russifier."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from drv3 import *
from tex import bc4_decode, bc4_encode
from spft import parse_srd_font

SRC = 'orig/10_vanilla/game_resident/game_resident_US.spc'
OUT = 'build/data/win/game_resident/game_resident_US.spc'
TTF_CYR = os.environ.get('V3_CYR', 'work/fonts2/pt-sans_cyrillic_400.ttf')
TTF_LAT = os.environ.get('V3_LAT', 'work/fonts2/pt-sans_latin_400.ttf')
NEW = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя«»№–„“'
BASELINE = 43
STROKE = int(os.environ.get('V3_STROKE', '1'))
CAP = float(os.environ.get('V3_CAP', '37.0'))
SS = 4  # supersampling


def block(typ, data, sub=b'', unk=0):
    out = bytearray(typ + struct.pack('>III', len(data), len(sub), unk) + data)
    out += b'\0' * ((-len(out)) % 16)
    out += sub
    out += b'\0' * ((-len(out)) % 16)
    return bytes(out)


def main():
    spc = spc_read(open(SRC, 'rb').read())
    ents = {e.name: e for e in spc['entries']}
    srd = ents['v3_font00.stx'].data
    f = parse_srd_font(srd)
    txr = f['txr']
    W, H = struct.unpack_from('<HH', txr, 6)
    tex = bc4_decode(ents['v3_font00.srdv'].data, W, H)

    glyphs = {}  # char -> (bitmap ndarray, a, b, c)
    for ch, e in zip(f['chars'], f['ents']):
        bm = tex[e['y']:e['y'] + e['h'], e['x']:e['x'] + e['w']].copy()
        sa = lambda v: v - 256 if v > 127 else v
        glyphs[ch] = (bm, sa(e['a']), sa(e['b']), e['c'])

    # calibrate
    ref = ImageFont.truetype(TTF_LAT, 400)
    bb = ref.getbbox('H')
    size = 400 * CAP / (bb[3] - bb[1])
    fc = ImageFont.truetype(TTF_CYR, int(round(size * SS)))
    fl = ImageFont.truetype(TTF_LAT, int(round(size * SS)))
    from fontTools.ttLib import TTFont
    CMAP_LAT = set(TTFont(TTF_LAT).getBestCmap()); CMAP_CYR = set(TTFont(TTF_CYR).getBestCmap())
    for chs in NEW:
        ch = ord(chs)
        if ch in glyphs:
            continue
        font = fl if ch in CMAP_LAT else fc
        if ch not in CMAP_LAT and ch not in CMAP_CYR:
            raise SystemExit('no glyph for %r' % chs)
        TOPPAD = 12  # запас сверху: у Ё/Й надстрочный знак выше заглавных
        canvas = Image.new('L', (int(120 * SS), int((70 + TOPPAD) * SS)), 0)
        d = ImageDraw.Draw(canvas)
        ox = 20 * SS
        # anchor 'ls' = left, baseline
        d.text((ox, (BASELINE + TOPPAD) * SS), chs, font=font, fill=255, anchor='ls', stroke_width=STROKE, stroke_fill=255)
        small = canvas.resize((canvas.width // SS, canvas.height // SS), Image.LANCZOS)
        a = np.array(small)
        ys, xs = np.where(a > 8)
        if len(xs) == 0:
            continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        bm = a[y0:y1, x0:x1]
        y0 -= TOPPAD
        if y0 < 0:
            # не помещается над строкой: сжимаем просвет между знаком и буквой, затем сам знак
            need = -y0
            rows = bm.max(axis=1) > 8
            blank = [i for i in range(len(rows)) if not rows[i]]
            gap = [i for i in blank if i > 0 and rows[:i].any()]
            gap = [i for i in gap if rows[i:].any()]
            cut = gap[:max(0, min(need, len(gap) - 1))]
            bm = np.delete(bm, cut, axis=0); need -= len(cut)
            if need > 0:
                rows = bm.max(axis=1) > 8
                k = 0
                while k < len(rows) and rows[k]: k += 1
                acc = bm[:k]
                nh = max(2, k - need)
                acc = np.array(Image.fromarray(acc).resize((acc.shape[1], nh), Image.LANCZOS))
                bm = np.vstack([acc, bm[k:]]); need -= k - nh
            y0 = max(0, need)
        adv = font.getlength(chs) / SS
        la = int(x0 - 20)
        rb = int(round(adv - (x1 - 20)))
        glyphs[ch] = (bm, la, rb, int(y0))

    # pack
    chars = sorted(glyphs)
    rowh = max(g[0].shape[0] for g in glyphs.values()) + 2
    x, y = 1, 1
    place = {}
    for ch in chars:
        bm = glyphs[ch][0]
        h, w = bm.shape
        if x + w + 1 > W:
            x = 1; y += rowh
        place[ch] = (x, y)
        x += w + 1
    NH = y + rowh
    NH4 = (NH + 3) // 4 * 4
    img = np.zeros((NH4, W), dtype=np.uint8)
    for ch in chars:
        bm = glyphs[ch][0]; px, py = place[ch]
        img[py:py + bm.shape[0], px:px + bm.shape[1]] = bm
    Image.fromarray(img).save('work/v3_font_new.png')
    texdata = bc4_encode(img)

    # SpFt
    sp = f['sp']
    maxc = f['maxc']
    bml = (maxc + 7) // 8
    bitmap = bytearray(bml)
    for ch in chars:
        bitmap[ch // 8] |= 1 << (ch % 8)
    nidx = (maxc + 31) // 32
    idx = bytearray()
    cnt = 0; ci = 0
    for k in range(nidx):
        while ci < len(chars) and chars[ci] < 32 * k:
            ci += 1
        idx += struct.pack('<I', ci)
    gtab = bytearray()
    for ch in chars:
        bm, la, rb, c = glyphs[ch]
        px, py = place[ch]
        h, w = bm.shape
        gtab += bytes([px & 0xff, ((px >> 8) & 0x0f) | ((py & 0x0f) << 4), (py >> 4) & 0xff,
                       w, h, la & 0xff, rb & 0xff, c & 0xff])
    name = sp[f['name_off']:]
    bm_off = 0x2c
    idx_off = (bm_off + bml + 3) // 4 * 4
    gi_off = idx_off + len(idx)
    kern_off = gi_off + len(gtab)
    name_off = kern_off + 16
    body = bytearray(struct.pack('<4sIIIIIIIIHHI', b'SpFt', f['ver'], maxc, f['size'], name_off, len(chars),
                                 gi_off, bm_off, idx_off, f['lh'], f['asc'], kern_off))
    body += bitmap
    body += b'\0' * (idx_off - len(body))
    body += idx + gtab + struct.pack('<IIII', name_off, name_off, name_off, name_off) + name
    # RSI
    rsi_old = f['rsi']
    names = rsi_old[struct.unpack_from('<I', rsi_old, 0x0c)[0]:]
    names = names.split(b'\0')
    res_name = names[0] + b'\0'; tab_name = names[1] + b'\0'
    sp_off = 0x30
    rn_off = sp_off + len(body)
    tn_off = rn_off + len(res_name)
    rsi = bytearray(rsi_old[:0x30])
    struct.pack_into('<I', rsi, 0x0c, rn_off)
    struct.pack_into('<I', rsi, 0x14, len(texdata))
    struct.pack_into('<III', rsi, 0x20, tn_off, sp_off, len(body))
    rsi += body + res_name + tab_name
    txr2 = bytearray(txr)
    struct.pack_into('<H', txr2, 8, NH)
    rsi_blk = block(b'$RSI', bytes(rsi))
    ct0 = block(b'$CT0', b'')
    newsrd = block(b'$CFH', b'', unk=1) + block(b'$TXR', bytes(txr2), rsi_blk + ct0) + ct0
    # verify parse
    g = parse_srd_font(newsrd)
    assert [chr(c) for c in g['chars']] == [chr(c) for c in chars], 'chars mismatch'
    tex2 = bc4_decode(texdata, W, NH)
    ents['v3_font00.stx'].data = newsrd
    ents['v3_font00.srdv'].data = texdata
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'wb').write(spc_write(spc, compress=True))
    print('glyphs', len(chars), 'tex', W, NH, 'srd', len(newsrd), 'srdv', len(texdata))


if __name__ == '__main__':
    main()
