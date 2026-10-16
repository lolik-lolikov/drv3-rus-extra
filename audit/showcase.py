"""Листы «оригинал → перевод v2.4» для пользователя: python3 audit/showcase.py <папка_вывода>
Группы и текстуры заданы ниже (архив, текстура, [srd]); несколько текстур в одной строке кладутся рядом."""
import os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
os.chdir(ROOT)
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import texedit
from drv3 import spc_read
from srdtex import textures, decode

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
F = ImageFont.truetype('work/fonts/rubik_500.ttf', 26)
F2 = ImageFont.truetype('work/fonts/rubik_400.ttf', 17)
cache = {}


def find(name):
    o = [p for p in glob.glob('orig/**/' + name, recursive=True) if '00_test' not in p and '10_vanilla' not in p]
    b = [p for p in glob.glob('build/**/' + name, recursive=True)]
    return (o[0] if o else None), (b[0] if b else None)


def tex(path, name, srd=None):
    if path not in cache:
        spc = spc_read(open(path, 'rb').read())
        cache[path] = {e.name: e for e in spc['entries']}
    E = cache[path]
    for n in E:
        if n.endswith('.srd') and n + 'v' in E and (not srd or srd == n):
            for t in textures(E[n].data):
                if t['name'] == name:
                    return decode(t, E[n + 'v'].data)


def crop_ink(im, pad=6):
    a = np.asarray(im)[:, :, 3]
    ys, xs = np.where(a > 10)
    if not len(xs):
        return im
    return im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad)))


GROUPS = [
    ('Ловля лосося', [
        [('sake_no_tukamidori_US.SPC', 'title_%02d_US.png' % i, 't_sake_start.srd') for i in (0, 1, 2, 3, 4)],
        [('sake_no_tukamidori_US.SPC', 'title_%02d_US.png' % i, 't_sake_start.srd') for i in (6, 7)] +
        [('sake_no_tukamidori_US.SPC', 'title_%02d_US.png' % i, 't_sake_finish.srd') for i in (0, 1, 2, 3)],
        [('sake_no_tukamidori_US.SPC', 'time_US.png', None), ('sake_no_tukamidori_US.SPC', 't_sake_score_tx_US.png', None),
         ('sake_no_tukamidori_US.SPC', 'get_US.png', None)],
        [('sake_no_tukamidori_US.SPC', 'mis_US.png', None), ('sake_no_tukamidori_US.SPC', 'combo_tx_US.png', None)],
        [('sake_no_tukamidori_US.SPC', 'text_ex_US.png', None), ('sake_no_tukamidori_US.SPC', 'text_order_US.png', None),
         ('sake_no_tukamidori_US.SPC', 'title_US.png', None)],
        [('sake_no_tukamidori_US.SPC', 't_casino_combo_tx_3_US.png', None), ('sake_no_tukamidori_US.SPC', 't_drive_cutin_miss_tx_US.png', None)],
    ]),
    ('Беззаконный пробег', [
        [('towa_run_US.SPC', 't_drive_towa_stencil_tx_000_US.png', None), ('towa_run_US.SPC', 't_drive_towa_tx_US_DXT1.png', None)],
        [('towa_run_US.SPC', 't_casino_drive_speedup_tx_US_DXT1.png', None), ('towa_run_US.SPC', 't_towa_finish_tx_US_DXT1.png', None)],
        [('towa_run_US.SPC', 't_casino_drive_time_tx_US.png', None), ('towa_run_US.SPC', 't_casino_score_tx_US.png', None),
         ('towa_run_US.SPC', 't_casino_drive_meter_tx_kmh_US.png', None)],
    ]),
    ('Монолит', [
        [('monolith_US.SPC', 't_monolith_start_tx_otakara_US.png', 't_monolith_start.srd'),
         ('monolith_US.SPC', 't_monolith_start_tx_monolith_US.png', 't_monolith_start.srd')],
        [('monolith_US.SPC', 't_monolith_start_tx_start_US.png', None), ('monolith_US.SPC', 't_casino_hkt_last_tx_timeup1_US.png', None),
         ('monolith_US.SPC', 't_casino_hkt_score_tx_DXT1_US.png', None)],
        [('monolith_US.SPC', 't_casino_hkt_last_tx_perfect3_US.png', None), ('monolith_US.SPC', 't_casino_hkt_last_tx_nomore2_US.png', None)],
        [('monolith_US.SPC', 't_hkt_get_tx_%s_US.png' % k, None) for k in ('sake', 'monomi', 'kumas')],
    ]),
    ('Слоты и Мономоно-автомат', [
        [('slot_bonus_count_US.spc', 'ef_%02d_US_DXT1.png' % i, None) for i in range(10)],
        [('slot_machine_US.SPC', 'text_DXT1.png', None), ('slot_machine_US.SPC', 'detail_DXT1.png', None)],
        [('m_left_US.spc', 'juhuku_00_US.png', None), ('m_left_US.spc', 'juhuku_01_US.png', None), ('m_left_US.spc', 'juhuku_02_US.png', None),
         ('m_machine_US.spc', 'title_ef_n_DXT1_US.png', None)],
        [('m_guide_US.spc', 'help_US.png', None), ('m_guide_US.spc', 'list_US.png', None), ('m_lucky_US.spc', 'lucky_s_DXT1.png', None)],
    ]),
    ('Любовь через Вселенную (Salmon Team)', [
        [('ainori_sindan_US.spc', 'monokumaz_US.png', None)],
        [('ainori_day_change_US.spc', 'day_lang_000_US.png', None), ('ainori_day_change_US.spc', 'day_lang_001_US.png', None),
         ('ainori_day_US.spc', 'day_day_US.png', None)],
        [('ainori_day_change_US.spc', 'day_day_%s_US.png' % k, None) for k in 'day'] +
        [('ainori_common_page_US.spc', 'auto_u_day_US.png', None), ('ainori_date_view_US.spc', 'text_go_US.png', None)],
    ]),
    ('План развития и Подземелье Отчаяния', [
        [('success_chara_select_list_US.spc', 'new_US.png', None), ('rpg_party_status_US.spc', 'LV_US.png', None),
         ('success_skill_list_US.spc', 'headline_01_US.png', None), ('success_skill_list_US.spc', 'lv_max_US.png', None)],
        [('success_hud_course_check_US.spc', 'check_guide_win_az_US.png', None)],
        [('rpg_staffroll_US.spc', 'staffroll_staff_18_US.png', None)],
        [('rpg_staffroll_US.spc', 'staffroll_position_05_US.png', None)],
        [('effect_0%s_US.spc' % k, 'effect_0%s_US.png' % k, None) for k in ('11', '13', '19', '25', '29')],
        [('rpg_cutin_US.spc', 'telop_kakusei_US.png', None), ('success_skill_tab_US.spc', 'tab_off_01_US.png', None)],
        [('success_step_US.spc', 'rest_lang_US.png', None), ('success_page_cursor_US.spc', 'page_cursor_US.png', None)],
    ]),
]


def checker(w, h, c1=(58, 58, 68), c2=(78, 78, 90)):
    im = Image.new('RGBA', (w, h), c1 + (255,)); d = ImageDraw.Draw(im)
    for y in range(0, h, 12):
        for x in range(0, w, 12):
            if (x // 12 + y // 12) % 2: d.rectangle((x, y, x + 11, y + 11), fill=c2 + (255,))
    return im


MAXW = 1500
pages = []; page = []; ph = 0
for title, rows in GROUPS:
    blocks = []
    for row in rows:
        cells = []
        for arch, name, srd in row:
            op, bp = find(arch)
            if not op or not bp:
                print('нет', arch); continue
            o = tex(op, name, srd); n = tex(bp, name, srd)
            if o is None or n is None:
                print('нет текстуры', arch, name); continue
            box = None
            ao = np.asarray(o)[:, :, 3]; an = np.asarray(n)[:, :, 3]
            m = (ao > 10) | (an > 10)
            ys, xs = np.where(m)
            if len(xs) and ao.min() < 200:
                box = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(o.width, xs.max() + 7), min(o.height, ys.max() + 7))
                o = o.crop(box); n = n.crop(box)
            cells.append((o, n))
        if not cells:
            continue
        # масштаб: строка из пар «оригинал | перевод» по вертикали, ширина ≤ MAXW
        gap = 16
        tw = sum(o.width for o, n in cells) + gap * (len(cells) - 1)
        mh = max(o.height for o, n in cells)
        sc = min(MAXW / tw, 170 / mh, 1.6)
        cells = [(o.resize((max(1, int(o.width * sc)), max(1, int(o.height * sc))), Image.LANCZOS),
                  n.resize((max(1, int(n.width * sc)), max(1, int(n.height * sc))), Image.LANCZOS)) for o, n in cells]
        rh = max(o.height for o, n in cells)
        blk = Image.new('RGBA', (MAXW, rh * 2 + 10), (24, 24, 30, 255))
        x = 0
        for o, n in cells:
            c = checker(*o.size); c.alpha_composite(o); blk.paste(c, (x, 0))
            c = checker(*n.size); c.alpha_composite(n); blk.paste(c, (x, rh + 10))
            x += o.width + gap
        blocks.append(blk)
    hdr = Image.new('RGBA', (MAXW, 44), (24, 24, 30, 255)); d = ImageDraw.Draw(hdr)
    d.text((0, 8), title, font=F, fill=(255, 214, 90, 255))
    d.text((MAXW - 470, 14), 'верх — оригинал, низ — перевод v2.4', font=F2, fill=(170, 170, 180, 255))
    group = [hdr] + blocks
    gh = sum(b.height + 22 for b in group)
    if page and ph + gh > 2300:
        pages.append(page); page = []; ph = 0
    page += group; ph += gh
if page:
    pages.append(page)
for i, pg in enumerate(pages, 1):
    H = sum(b.height + 22 for b in pg) + 20
    C = Image.new('RGB', (MAXW + 40, H), (24, 24, 30)); y = 20
    for b in pg:
        C.paste(b.convert('RGB'), (20, y)); y += b.height + 22
    p = os.path.join(OUT, 'сравнение_картинок_v2.4_%d.png' % i)
    C.save(p, optimize=True); print(p, C.size)
