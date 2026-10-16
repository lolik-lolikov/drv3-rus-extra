"""Карты Смерти (minigame/rsc/card/card_[nsu]_XXX_US.spc): стираем английский текст на сетчатых панелях
и пишем русский — цитата сверху, имя и талант снизу.

Чтобы патчи были маленькими:
  * в BC7 перекодируются только блоки 4×4, в которых что-то изменилось (остальные байты — как в оригинале);
  * сжатый поток SPC собирается из кусков оригинального потока и заново сжатых кусков вокруг изменений
    (окно LZ — 1024 байта, поэтому оригинальный поток можно продолжать через 1024 байта после изменения).
python3 tools/cards.py [preview.png] [id ...]"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import cv2
from PIL import Image, ImageDraw
import texedit
from drv3 import spc_read, spc_write, spc_dec, spc_cmp, BITREV
from srdtex import textures, decode

ROOT = os.path.join(os.path.dirname(__file__), '..')
SRC = os.path.join(ROOT, 'orig', '02_us', 'data', 'win', 'minigame', 'rsc', 'card')
OUT = os.path.join(ROOT, 'build', 'data', 'win', 'minigame', 'rsc', 'card')

NAMES = {'000': 'Шуичи Сайхара', '001': 'Кайто Момота', '002': 'Рёма Хоши', '003': 'Рантаро Амами', '004': 'Гонта Гокухара',
         '005': 'Кокичи Ома', '006': 'Корекиё Шингуджи', '007': 'К1-Б0', '008': 'Кируми Тоджо', '009': 'Химико Юмено',
         '010': 'Маки Харукава', '011': 'Тенко Чабашира', '012': 'Цумуги Широгане', '013': 'Анджи Ёнага', '014': 'Миу Ирума',
         '015': 'Каэде Акамацу', '020': 'Монокума', '100': 'Макото Наэги', '101': 'Киётака Ишимару', '102': 'Бьякуя Тогами',
         '103': 'Мондо Овада', '104': 'Леон Кувата', '105': 'Хифуми Ямада', '106': 'Ясухиро Хагакурэ', '107': 'Чихиро Фуджисаки',
         '108': 'Саяка Майзоно', '109': 'Кёко Киригири', '110': 'Аой Асахина', '111': 'Токо Фукава', '112': 'Геноцид Джек',
         '113': 'Сакура Огами', '114': 'Селестия Люденберг', '115': 'Джунко Эношима', '116': 'Джунко Эношима (Мукуро)',
         '120': 'Хаджимэ Хината', '121': 'Нагито Комаэда', '122': 'Бьякуя Тогами (Самозванец)', '123': 'Гандам Танака',
         '124': 'Казуичи Сода', '125': 'Тэрутэру Ханамура', '126': 'Нэкомару Нидай', '127': 'Фуюхико Кузурю', '128': 'Аканэ Овари',
         '129': 'Чиаки Нанами', '130': 'Соня Невермайнд', '131': 'Хиёко Сайонджи', '132': 'Махиру Коидзуми', '133': 'Микан Цумики',
         '134': 'Ибуки Миода', '135': 'Пеко Пекояма', '136': 'Изуру Камукура', '137': 'Мономи', '138': 'Усами'}
A = 'Абсолютный '; AF = 'Абсолютная '
TALENTS = {'000': A + 'Детектив', '001': A + 'Астронавт', '002': A + 'Теннисист', '003': A + '???', '004': A + 'Энтомолог',
           '005': A + 'Верховный Лидер', '006': A + 'Антрополог', '007': A + 'Робот', '008': AF + 'Горничная', '009': AF + 'Фокусница',
           '010': AF + 'Воспитательница', '011': A + 'Мастер Айкидо', '012': AF + 'Косплеерша', '013': AF + 'Художница',
           '014': AF + 'Изобретательница', '015': AF + 'Пианистка', '020': 'Директор', '100': A + 'Счастливчик',
           '101': A + 'Моральный Ориентир', '102': A + 'Наследник', '103': A + 'Лидер Байкеров', '104': AF + 'Звезда Бейсбола',
           '105': A + 'Автор Фанфиков', '106': A + 'Ясновидящий', '107': A + 'Программист', '108': AF + 'Поп-Звезда',
           '109': A + 'Детектив', '110': AF + 'Пловчиха', '111': AF + 'Писательница', '112': AF + 'Убийца-Маньячка',
           '113': A + 'Боец', '114': A + 'Игрок', '115': 'Абсолютное Отчаяние', '116': AF + 'Модница', '120': A + '???',
           '121': A + 'Счастливчик', '122': A + 'Самозванец', '123': A + 'Заводчик', '124': A + 'Механик', '125': A + 'Повар',
           '126': A + 'Менеджер', '127': A + 'Якудза', '128': AF + 'Гимнастка', '129': A + 'Геймер', '130': AF + 'Принцесса',
           '131': AF + 'Танцовщица', '132': AF + 'Фотограф', '133': AF + 'Медсестра', '134': A + 'Музыкант', '135': AF + 'Мечница',
           '136': AF + 'Надежда', '137': 'Сестра Монокумы', '138': 'Учитель Академии Пик Надежды'}
TALENT_U = {'003': A + 'Выживший', '010': A + 'Киллер', '116': A + 'Солдат'}

QUOTE_BOX = (96, 30, 1196, 84)    # где стираем цитату
NAME_BOX = (4, 688, 676, 812)     # где стираем имя и талант
MODEL_TOP = (96, 2, 1196, 96)     # область сетки для модели
MODEL_BOT = (4, 677, 682, 818)
WHITE = (255, 255, 255, 255)
QUOTE = dict(font='roboto4', fill=WHITE, align='left', valign='top', cap=32.5, tracking=1.2, minh=0.66)
NAME = dict(font='roboto', fill=WHITE, align='left', valign='top', cap=34, tracking=-0.4, minh=0.62)


def load_quotes():
    q = {}
    for l in open(os.path.join(ROOT, 'work', 'cards_ru.tsv'), encoding='utf-8'):
        if l.startswith('#') or '\t' not in l: continue
        k, v = l.rstrip('\n').split('\t', 1); q[k] = v
    return q


def grid_model(a, box):
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1, :3].astype(np.float32)
    lum = sub.mean(2)
    h = sub[np.arange(y1 - y0), lum.argmin(1)]
    v = sub[lum.argmin(0), np.arange(x1 - x0)]
    return np.maximum(h[:, None, :], v[None, :, :])


def erase(a, model_box, box):
    """Стереть белый текст в box (координаты картинки). Сетка восстанавливается по модели,
    поверх рисунка персонажа (если он заходит на панель) — заливкой inpaint."""
    m_full = grid_model(a, model_box)
    mx0, my0 = model_box[0], model_box[1]
    x0, y0, x1, y1 = box
    m = m_full[y0 - my0:y1 - my0, x0 - mx0:x1 - mx0]
    sub = a[y0:y1, x0:x1, :3].astype(np.float32)
    lum = sub.mean(2); ml = m.mean(2)
    sat = sub.max(2) - sub.min(2)
    core = (sat < 28) & (lum > 150) & (lum - ml > 60)
    halo = cv2.dilate(core.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2) > 0
    kill = halo & (((lum > ml + 3) & (sat < 40)) | core)
    # «рисунок» — пиксели, сильно отличающиеся от сетки и не текст
    art = (np.abs(sub - m).mean(2) > 18) & ~halo
    near_art = cv2.dilate(art.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    out = a.copy()
    s = out[y0:y1, x0:x1, :3]
    fill = m.astype(np.uint8)
    use_inp = kill & near_art
    if use_inp.any():
        inp = cv2.inpaint(np.ascontiguousarray(s), (kill * 255).astype(np.uint8), 4, cv2.INPAINT_TELEA)
        fill = np.where(use_inp[:, :, None], inp, fill)
    s[kill] = fill[kill]
    return out


def render_card(img, quote, name, talent):
    a = np.array(img.convert('RGBA'))
    a = erase(a, MODEL_TOP, QUOTE_BOX)
    a = erase(a, MODEL_BOT, NAME_BOX)
    im = Image.fromarray(a)
    W, H = im.size
    lay = texedit.make_text_layer(dict(QUOTE, text=quote, maxw=1185 - 115), (W, H), (115, 37, 1188, 72))
    im = Image.alpha_composite(im, lay)
    for i, t in enumerate((name, talent)):
        y0 = 707 + 48 * i
        lay = texedit.make_text_layer(dict(NAME, text=t, maxw=668 - 31), (W, H), (31, y0, 670, y0 + 34))
        im = Image.alpha_composite(im, lay)
    return im


# ---------------- BC7: только изменённые блоки ----------------
def bc7_merge(orig_data, orig_img, new_img, w, h):
    import etcpak
    o = np.array(orig_img.convert('RGBA')); n = np.array(new_img.convert('RGBA'))
    newd = etcpak.compress_bc7(n.tobytes(), w, h)
    out = bytearray(orig_data)
    bw = w // 4
    diff = (o != n).any(2)
    changed = 0
    for by in range(h // 4):
        row = diff[by * 4:by * 4 + 4]
        if not row.any(): continue
        cols = row.reshape(4, bw, 4).any(axis=(0, 2))
        for bx in np.where(cols)[0]:
            k = (by * bw + bx) * 16
            out[k:k + 16] = newd[k:k + 16]; changed += 1
    return bytes(out), changed


# ---------------- склейка сжатого потока SPC ----------------
def scan_groups(raw):
    """[(позиция байта флагов, позиция в распакованных данных, токенов в группе)]"""
    g = []; p = 0; o = 0; n = len(raw)
    while p < n:
        gp, go = p, o
        flag = BITREV[raw[p]]; p += 1; k = 0
        for bit in range(8):
            if p >= n: break
            if flag & 1:
                o += 1; p += 1
            else:
                if p + 1 >= n: break
                b = raw[p] | (raw[p + 1] << 8); o += (b >> 10) + 2; p += 2
            flag >>= 1; k += 1
        g.append((gp, go, k))
    return g, o


def tokens_of(c):
    """Разобрать сжатый поток на токены: ('L', байт) или ('M', длина, смещение-поле)."""
    t = []; p = 0; n = len(c)
    while p < n:
        flag = BITREV[c[p]]; p += 1
        for bit in range(8):
            if p >= n: break
            if flag & 1:
                t.append(('L', c[p])); p += 1
            else:
                b = c[p] | (c[p + 1] << 8); p += 2
                t.append(('M', (b >> 10) + 2, b & 0x3FF))
            flag >>= 1
    return t


def serialize(t):
    out = bytearray()
    for i in range(0, len(t), 8):
        grp = t[i:i + 8]; bits = 0; body = bytearray()
        for k, x in enumerate(grp):
            if x[0] == 'L':
                bits |= 1 << k; body.append(x[1])
            else:
                body += struct.pack('<H', ((x[1] - 2) << 10) | x[2])
        out.append(BITREV[bits]); out += body
    return bytes(out)


def compress_aligned(data, final):
    """Сжать data так, чтобы число токенов было кратно 8 (кроме последнего куска потока):
    лишние токены получаем, отрезая от совпадений последний байт в виде литерала."""
    c = spc_cmp(data)
    if final or not data: return c
    t = tokens_of(c)
    need = (8 - len(t) % 8) % 8
    i = len(t) - 1
    while need and i >= 0:
        x = t[i]
        if x[0] == 'M':
            # конец совпадения: позиция в данных
            pos = sum(1 if y[0] == 'L' else y[1] for y in t[:i])
            last = data[pos + x[1] - 1]
            if x[1] >= 3:
                t[i:i + 1] = [('M', x[1] - 1, x[2]), ('L', last)]
            else:
                t[i:i + 1] = [('L', data[pos]), ('L', last)]
            need -= 1
            continue   # тот же индекс: можно резать дальше
        i -= 1
    if need:
        raise RuntimeError('cannot align')
    out = serialize(t)
    assert spc_dec(out) == data
    return out


def splice(raw, old, new, window=1024):
    assert len(old) == len(new)
    d = np.frombuffer(old, np.uint8) != np.frombuffer(new, np.uint8)
    idx = np.where(d)[0]
    if not len(idx): return raw
    # диапазоны изменений (склеиваем, если между ними меньше 4 КБ)
    rng = []; s = idx[0]; e = idx[0] + 1
    for i in idx[1:]:
        if i - e > 4096: rng.append((s, e)); s = i
        e = i + 1
    rng.append((s, e))
    groups, total = scan_groups(raw)
    assert total == len(old)
    starts = [x[1] for x in groups]
    import bisect
    segs = []
    for s, e in rng:
        gi = bisect.bisect_right(starts, s) - 1
        ge = bisect.bisect_left(starts, e + window)
        if segs and gi <= segs[-1][1]: segs[-1] = (segs[-1][0], max(ge, segs[-1][1]))
        else: segs.append((gi, ge))
    out = bytearray(); prev_stream = 0
    for gi, ge in segs:
        out += raw[prev_stream:groups[gi][0]]
        a = groups[gi][1]
        final = ge >= len(groups)
        b = len(new) if final else groups[ge][1]
        out += compress_aligned(new[a:b], final)
        prev_stream = len(raw) if final else groups[ge][0]
    out += raw[prev_stream:]
    out = bytes(out)
    assert spc_dec(out) == new, 'splice verify failed'
    return out


def build_card(cid, quotes, preview=None):
    nm = 'card_%s_US.spc' % cid
    src = open(os.path.join(SRC, nm), 'rb').read()
    spc = spc_read(src)
    E = {e.name: e for e in spc['entries']}
    srd = E['card_%s_US.srd' % cid]; srdv = E['card_%s_US.srdv' % cid]
    t = textures(srd.data)[0]
    orig_img = decode(t, srdv.data)
    num = cid.split('_')[1]; rar = cid[0]
    talent = TALENT_U.get(num, TALENTS[num]) if rar == 'u' else TALENTS[num]
    new_img = render_card(orig_img, quotes[cid], NAMES[num], talent)
    off, size, _, _ = t['res'][0]
    tex_old = srdv.data[off:off + size]
    tex_new, nchg = bc7_merge(tex_old, orig_img, new_img, t['w'], t['h'])
    newv = srdv.data[:off] + tex_new + srdv.data[off + size:]
    raw = splice(srdv.raw, srdv.data, newv)
    srdv.data = newv; srdv._orig = newv; srdv.raw = raw
    out = spc_write(spc, compress=True)
    chk = spc_read(out)
    assert [e.data for e in chk['entries']][1] == newv
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, nm), 'wb').write(out)
    if preview is not None:
        preview.append((cid, orig_img, decode(t, newv)))
    return len(src), len(out), nchg


if __name__ == '__main__':
    import time
    quotes = load_quotes()
    prev = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith('.png') else None
    ids = [a for a in sys.argv[1:] if not a.endswith('.png')] or sorted(quotes)
    pv = []
    t0 = time.time()
    for cid in ids:
        a, b, n = build_card(cid, quotes, pv)
        print(cid, a, b, 'blocks', n, '%.0fs' % (time.time() - t0), flush=True)
    if prev:
        rows = []
        for cid, o, n in pv:
            rows.append(n.resize((600, 410)))
        cols = 3
        C = Image.new('RGBA', (600 * cols, 410 * ((len(rows) + cols - 1) // cols)), (0, 0, 0, 255))
        for i, r in enumerate(rows): C.alpha_composite(r, ((i % cols) * 600, (i // cols) * 410))
        C.convert('RGB').save(prev)
