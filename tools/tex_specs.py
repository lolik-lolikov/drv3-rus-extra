"""Texture translation specs."""
import json,os
ROOT=os.path.join(os.path.dirname(__file__),'..')
G=json.load(open(os.path.join(ROOT,'work/names_full.json')))
SPECS=[]
def add(arch,tex,text,**kw):
    d=dict(arch=arch,tex=tex,text=text); d.update(kw); SPECS.append(d)

# ---------- Salmon Team (ainori) ----------
A='01_salmon_team/data/win/flash/ainori/'
AN={'000':'Шуичи Сайхара','001':'Кайто Момота','002':'Рёма Хоши','003':'Рантаро Амами','004':'Гонта Гокухара','005':'Кокичи Ома',
'006':'Корекиё Шингуджи','007':'К1-Б0','008':'Кируми Тоджо','009':'Химико Юмено','010':'Маки Харукава','011':'Тенко Чабашира',
'012':'Цумуги Широгане','013':'Анджи Ёнага','014':'Миу Ирума','015':'Каэде Акамацу','020':'Монокума','021':'Монотаро','022':'Моноске',
'023':'Монофани','024':'Монодам','025':'Монокид','026':'Экзисал','027':'Монокубы','028':'Монокубы','029':'Монокубы','030':'Монокубы'}
for k,v in AN.items():
    add(A+'spcpack/chara_name_US.spc',f'chara_name_{k}_US.png',v,inner=f'chara_name_{k}.spc',font='days',
        fill=(255,255,255,255) if k=='000' else (0,0,0,255),box=(0,17,512,51),cap=34,valign='top',maxw=470)
add(A+'ainori_window_name_US.spc','chara_name_001_US.png','Кайто Момота',font='days',fill=(0,0,0,255),box=(0,17,512,51),cap=34,valign='top',maxw=470)
add(A+'ainori_title_sele_US.spc','mes_back_US.png','Назад',font='days',fill=(255,255,255,255),box=(0,15,512,53),cap=31,maxw=440)
add(A+'ainori_title_sele_US.spc','mes_load_US.png','Продолжить',font='days',fill=(255,255,255,255),box=(0,15,512,53),cap=31,maxw=440)
add(A+'ainori_title_sele_US.spc','mes_start_US.png','С самого начала',font='days',fill=(255,255,255,255),box=(0,15,512,53),cap=31,maxw=470)
add(A+'ainori_date_list_US.spc','date_US.png','Выберите место свидания',font='days',fill=(0,0,0,255),box=(0,14,512,50),cap=30,align='left',maxw=508)
import texedit as _te
add(A+'ainori_day_change_US.spc','text_day_US.png','',custom=_te.arc_text,font='rubik9',fill='auto',cap=38,r0=197,maxstretch=1.9,
    arcs=[('ВРЕМЯ ДНЯ',218,342),('ЧУДЕСНЫЙ ДЕНЬ',18,192)])
add(A+'ainori_day_change_US.spc','text_night_US.png','',custom=_te.arc_text,font='rubik9',fill='auto',cap=38,r0=197,maxstretch=1.9,
    arcs=[('ВРЕМЯ НОЧИ',218,12),('СПОКОЙНОЙ НОЧИ',38,212)])
NEON_B=dict(fill=(215,235,255,255),strokes=[(2.5,(70,140,255,255))],glow=(6,(60,130,255,255)),glow_gain=1.6)
NEON_P=dict(fill=(255,225,255,255),strokes=[(3,(235,40,230,255))],glow=(7,(230,30,220,255)),glow_gain=1.8)
add(A+'ainori_title_US.spc','title_US.png','',custom=_te.arc_text,font='days',cap=25,r0=250,center=(256,290),
    arcs=[('Любовь через Вселенную',222,318)],maxstretch=1.2,**NEON_B)
add(A+'ainori_sindan_US.spc','sindan_US.png','Диагноз',font='russo',box=(130,80,384,165),cap=50,**NEON_P)
add(A+'ainori_sindan_US.spc','kazari_US.png','Любовный\nтест\nМонокумы',font='days',box=(20,62,236,200),cap=24,line_gap=0.95,rotate=20,**NEON_P)
add(A+'ainori_date_view_US.spc','text_view_US.png','ОБЗОР',font='russo',fill=(255,255,255,255),stroke=3,stroke_fill=(0,0,0,255),box=(2,8,126,56),cap=26)

# ---------- Casino ----------
GOLD=[(240,238,228),(222,212,140),(205,170,80),(225,200,120)]
G_SANS=dict(font='ubuntu',gradient=GOLD,stroke=1.2,stroke_fill=(10,6,0,255),capratio=0.95)
G_SCRIPT=dict(font='marck',gradient=GOLD,stroke=1.2,stroke_fill=(10,6,0,255),glow=(3,(255,230,150,255)),glow_gain=0.6,capratio=0.68)
G_IT=dict(font='ubuntu',gradient=GOLD,stroke=1.0,stroke_fill=(10,6,0,255),italic=0.18,capratio=0.95)
def gadd(tex,text,st,**kw):
    d=dict(st); d.update(kw); add(None,tex,text,**d)
gadd('casino_top_tx_US.png','Добро пожаловать\nв Казино',G_SCRIPT,capratio=0.42,line_gap=0.9)
gadd('casino_top_title_tx_towa_US.png','БЕЗЗАКОННЫЙ ПРОБЕГ',G_IT)
gadd('casino_top_title_tx_sake_US.png','ЛОВЛЯ ЛОСОСЯ',G_IT)
gadd('casino_top_title_tx_mono_US.png','ОХОТНИК ЗА СОКРОВИЩАМИ! Монолит',G_IT)
gadd('casino_top_coin_tx_US.png','Монеты',G_SCRIPT)
gadd('casino_top_bet_tx_US.png','Ставка',G_SCRIPT)
gadd('casino_top_hs_tx_US.png','Рекорд',G_SANS,capratio=0.7,align='left')
gadd('casino_top_diff_tx_normal_US.png','Обычный',G_SANS,capratio=0.75)
gadd('casino_top_diff_tx_hard_US.png','Злой',G_SANS,capratio=0.75)
gadd('casino_top_diff_tx_easy_US.png','Добрый',G_SANS,capratio=0.75)
gadd('casino_detail_tx_US.png','Подробно',G_SCRIPT)
gadd('casino_detail_sub_tx_score_US.png','Очки',G_SANS,capratio=0.78,align='left')
gadd('casino_detail_sub_tx_rank_US.png','Ранг',G_SANS,capratio=0.78,align='left')
gadd('casino_result_sub_tx_score_US.png','Очки',G_SANS,capratio=0.78,align='left')
gadd('casino_result_sub_tx_rank_US.png','Ранг',G_SANS,capratio=0.78,align='left')
gadd('casino_result_sub_tx_bet_US.png','СТАВКА',G_IT,align='left')
gadd('casino_result_shokin_tx_US.png','Выигрыш',G_SANS,italic=0.12,capratio=0.75,align='left')
gadd('casino_result_tx_US.png','Итоги',G_SCRIPT)
gadd('casino_hanyo_tx_US.png','Внимание',G_SCRIPT)
gadd('casino_kankin_tx_US.png','Обмен',G_SCRIPT)
gadd('casino_kankin_choice_tx_change_US.png','Обменять',G_SANS,capratio=0.75)
gadd('casino_kankin_choice_tx_cancel_US.png','Отмена',G_SANS,capratio=0.75)
gadd('casino_kankin_shoji_tx_000_US.png','В наличии',G_SANS,capratio=0.75)
gadd('casino_kankin_shoji_medal_tx_001_US.png','Монеты',G_SCRIPT)
gadd('casino_kankin_shoji_medal_tx_000_US.png','Мономонеты',G_SCRIPT)
gadd('casino_keihin_tx_US.png','Обмен призов',G_SCRIPT)
gadd('casino_keihin_tab_tx_theme_US.png','Темы блокнота',G_SANS,italic=0.12,capratio=0.75)
gadd('casino_keihin_tab_tx_skill_US.png','Навыки',G_SANS,italic=0.12,capratio=0.75)
gadd('casino_keihin_tab_tx_present_US.png','Подарки',G_SANS,italic=0.12,capratio=0.75)
gadd('casino_keihin_present_shoyu_tx_US.png','В наличии',G_SANS,capratio=0.75)

# ---------- Talent Plan (Ultimate Talent Development Plan) ----------
B='1/'   # 08_batch1 flattened files (installed by name)
WHITE=(255,255,255,255); BLACK=(0,0,0,255); NAVY=(36,36,140,255)
PINK_G=[(255,20,140),(255,120,190),(255,215,235)]
POP_PINK=dict(font='rubik9',italic=0.08,gradient=PINK_G,strokes=[(11,BLACK),(7,WHITE)],shadow=(6,8,(0,0,0,200)),capratio=0.62)
POP_MONTH=dict(font='rubik9',italic=0.08,gradient=PINK_G,strokes=[(12,NAVY),(7,WHITE)],shadow=(8,10,NAVY),capratio=0.6)
def tadd(tex,text,st,**kw):
    d=dict(st); d.update(kw); add(None,tex,text,**d)
# logo: "U"+"ltimate" -> "А"+"бсолютный"; "Talent Development Plan" -> "План развития талантов"
tadd('logo_tyou_US.png','А',dict(font='rubik9',italic=0.12,fill=WHITE,strokes=[(10,(20,60,200,255)),(6,(40,200,255,255))],capratio=0.78))
tadd('logo_koukou_US.png','бсолютный',dict(font='rubik9',italic=0.12,gradient=[(30,120,230),(120,200,255),(220,245,255)],strokes=[(8,(20,40,120,255)),(5,WHITE)],capratio=0.62,align='left',maxw=550))
tadd('logo_ikusei_US.png','План развития талантов',dict(font='rubik9',italic=0.1,gradient=[(230,20,60),(255,120,40),(255,220,60)],strokes=[(10,(60,0,30,255)),(6,WHITE)],capratio=0.66,maxw=1900))
# title menu
for t,x in [('menu_card_US.png','Вытянуть Карты Смерти'),('menu_exit_US.png','Выйти'),('menu_load_US.png','Продолжить'),('menu_start_US.png','Новая игра')]:
    tadd(t,x,dict(font='rubik',fill='auto',capratio=0.95,valign='center'))
tadd('goal_telop_00_US.png','Финиш!',POP_PINK)
MON=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
SEASON_G={'w':[(40,90,230),(110,170,255),(225,238,255)],'sp':PINK_G,'su':[(20,160,40),(110,215,90),(230,255,200)],'au':[(235,90,10),(255,160,60),(255,232,170)]}
SEAS=['w','w','sp','sp','sp','su','su','su','au','au','au','w']
for i,m in enumerate(MON):
    tadd(f'month_{i+1:02d}_US.png',m,dict(POP_MONTH,gradient=SEASON_G[SEAS[i]]))
    tadd(f'season_month_{i+1:02d}_US.png',m,dict(font='oswald',fill=BLACK,capratio=0.95,maxw=160))
for i,y in enumerate(['1-й год','2-й год','3-й год']):
    tadd(f'year_{i+1:02d}_US.png',y,POP_PINK)
    tadd(f'season_year_{i+1:02d}_US.png',y,dict(font='rubik9',fill='auto',capratio=0.95))
# close buttons: icon kept, text replaced
for t in ['guide_close_US.png','guide_close_xone_US.png','guide_close_win_US.png','guide_close_cir_US.png']:
    tadd(t,'Закрыть',dict(font='mpr5',fill=WHITE,clear='box',clearbox=(62,0,256,64),box=(70,14,252,52),align='left',capratio=0.85,widen=False))
tadd('title_coursesele_US.png','Выберите курс обучения',dict(font='oswald',italic=0.1,fill=WHITE,strokes=[(5,NAVY)],capratio=0.7))
tadd('title_charasele_US.png','Выберите персонажа',dict(font='oswald',italic=0.1,fill=WHITE,strokes=[(5,NAVY)],capratio=0.7))
tadd('type_variety_US.png','Разносторонний тип',dict(font='mpr5',fill='auto',capratio=0.85,align='left'))
tadd('type_sports_US.png','Спортивный тип',dict(font='mpr5',fill='auto',capratio=0.85,align='left'))
tadd('type_intelli_US.png','Интеллектуальный тип',dict(font='mpr5',fill='auto',capratio=0.85,align='left'))
import sys as _sys; _sys.path.insert(0,os.path.dirname(__file__))
from build_names import IDX as _IDX, EN2RU as _EN2RU
for k,en in _IDX.items():
    tadd(f'charasele_name_{k}_US.png',_EN2RU[en],dict(font='rubik5',fill=WHITE,capratio=0.7,align='left',box=(8,10,531,61)))
# course names / map
for t,x in [('course_name_04_US.png','Курс Будущего'),('course_name_03_US.png','Курс Отчаяния'),('course_name_02_US.png','Курс Дружбы'),
            ('course_name_01_US.png','Курс Таланта'),('course_name_00_US.png','Обычный курс')]:
    tadd(t,x,dict(font='rubik9',fill=(255,0,140,255),strokes=[(6,BLACK),(3.5,WHITE)],capratio=0.56))
for t,x in [('course_03_US.png','Курс Будущего'),('course_02_US.png','Курс Дружбы'),('course_01_US.png','Курс Таланта'),('course_00_US.png','Обычный курс')]:
    tadd(t,x,dict(font='oswald',fill='auto',capratio=0.85))
tadd('goal_finish_US.png','Финиш\nпройден!',dict(font='rubik',fill=BLACK,strokes=[(4,WHITE)],capratio=0.9,align='left'))
tadd('goal_info_US.png','клетк. до\nфиниша',dict(font='rubik',fill=WHITE,strokes=[(2,BLACK)],capratio=0.85))
tadd('root_unit_US.png','Клетки',dict(font='oswald',italic=0.1,fill=WHITE,strokes=[(4,NAVY)],capratio=0.75))
tadd('root_min_US.png','Мин. путь',dict(font='oswald',italic=0.1,fill=NAVY,strokes=[(3,WHITE)],capratio=0.8))
tadd('root_max_US.png','Макс. путь',dict(font='oswald',italic=0.1,fill=NAVY,strokes=[(3,WHITE)],capratio=0.8))
for t in ['check_guide_US.png','check_guide_xone_US.png','check_guide_win_US.png']:
    tadd(t,'Быстрый ход',dict(font='mpr5',fill=WHITE,clear='box',clearbox=(378,0,736,80),box=(389,16,730,69),align='left',capratio=0.7,widen=False))
tadd('page_cursor_US.png','АВТО',dict(font='rubik9',fill=(255,240,0,255),strokes=[(3,BLACK)],capratio=0.9))
tadd('rest_US.png','клеток\nосталось',dict(font='rubik5',fill=WHITE,capratio=0.85,align='left',box=(360,23,548,108)))
tadd('rest_lang_US.png','клеток\nосталось',dict(font='rubik5',fill=WHITE,capratio=0.85))
for t in ['step_guide_US.png','step_guide_xone_US.png','step_guide_win_US.png']:
    tadd(t,'Подтвердить курс',dict(font='mpr5',fill=WHITE,capratio=0.7,clear='box',clearbox=(150,0,736,80),box=(150,19,730,67),align='left',widen=False))
tadd('skill_kakera_US.png','Осколки Таланта',dict(font='mpr5',fill=WHITE,strokes=[(3,(60,60,70,255))],capratio=0.8,align='right'))
tadd('headline_02_US.png','Конц.',dict(font='mpr',fill=WHITE,strokes=[(4,(60,60,70,255))],capratio=0.8))
tadd('headline_00_US.png','Список навыков',dict(font='mpr5',fill='auto',capratio=0.9,align='left'))
tadd('skill_title_US.png','Получить навык',dict(font='rubik9',italic=0.08,fill=(255,30,150,255),strokes=[(2,WHITE)],capratio=0.8,align='left',clear='box',clearbox=(140,0,1000,128),box=(146,30,990,100),widen=False))
tadd('result_title_US.png','Итоги',dict(font='rubik9',italic=0.08,fill=(255,30,150,255),strokes=[(3,WHITE)],capratio=0.8))
TABC=[(235,70,70),(30,150,235),(20,190,60),(160,120,230),(130,130,130)]
for i,x in enumerate(['Спорт','Интеллект','Разное','Прочее','Получено']):
    c=TABC[i]; dark=tuple(int(v*0.45) for v in c)+(255,); light=tuple(int(v+(255-v)*0.45) for v in c)+(255,)
    tadd(f'tab_on_0{i}_US.png',x,dict(font='rubik9',italic=0.1,fill=WHITE,strokes=[(3,dark)],bg='auto',capratio=0.7))
    tadd(f'tab_off_0{i}_US.png',x,dict(font='rubik9',italic=0.1,fill=light,strokes=[(3,WHITE)],bg='auto',capratio=0.7))
tadd('charalist_title_US.png','Список карт',dict(font='rubik9',fill=WHITE,strokes=[(3,BLACK)],capratio=0.8,align='left'))
tadd('lv_max_US.png','МАКС. УР.',dict(font='rubik9',fill=WHITE,strokes=[(3,NAVY)],capratio=0.8))

# ---------- Despair Dungeon (RPG) ----------
tadd('title_US.png','Меню базы',dict(font='rubik9',fill=WHITE,strokes=[(3,BLACK)],capratio=0.8,align='left',only=['rpg_base_title']))
tadd('chara_select_title_US.png','Выбор участников',dict(font='rubik9',fill=WHITE,strokes=[(4,BLACK)],capratio=0.8,align='left'))
tadd('create_title_US.png','Создание снаряжения',dict(font='rubik9',fill=WHITE,strokes=[(4,BLACK)],capratio=0.8,align='left'))
tadd('material_money_US.png','Средства',dict(font='rubik',fill=WHITE,strokes=[(4,BLACK)],capratio=0.75,align='left'))
tadd('material_cost_US.png','Стоимость',dict(font='rubik',fill=WHITE,strokes=[(3,(60,60,60,255))],capratio=0.75))
tadd('material_button_02_US.png','Не хватает средств',dict(font='rubik5',fill=WHITE,bg='auto',capratio=0.8))
tadd('material_button_01_US.png','Не хватает материалов',dict(font='rubik5',fill=WHITE,bg='auto',capratio=0.8))
tadd('telop_kakusei_US.png','Пробуждение!',dict(font='russo',italic=0.15,fill=(30,50,220,255),strokes=[(8,(250,250,110,255))],rotate=8,capratio=0.35))
tadd('guide_02b_US.png','L1 / R1 : Смена вкладки',dict(font='rubik5',fill=WHITE,strokes=[(3,BLACK)],capratio=0.75,align='left',box=(8,11,316,52)))
add('1/rpg_title_logo_US.spc','logo_main_US.png','',custom=None)  # placeholder replaced below
SPECS.pop()
tadd('logo_main_US.png','',dict(custom=None))
SPECS.pop()
import texedit as _te2
tadd('logo_main_US.png','',dict(custom=_te2.layers_custom,layers=[
    dict(text='Тест',font='rubik9',italic=0.15,gradient=[(230,20,20),(255,110,30),(255,200,40)],strokes=[(14,(40,0,0,255)),(9,WHITE)],shadow=(6,8,(0,0,0,160)),box=(330,120,1420,470),capratio=0.78),
    dict(text='Монокумы',font='rubik9',gradient=[(150,0,30),(220,40,60),(255,120,120)],strokes=[(10,(40,0,0,255)),(6,WHITE)],box=(620,455,1560,595),capratio=0.7),
]))
tadd('logo_sub_US.png','Подземелье Отчаяния',dict(font='rubik',fill=BLACK,strokes=[(6,WHITE)],glow=(6,(255,255,255,255)),capratio=0.75))

# ---------- Card Death machine ----------
tadd('box_mark_US.png','',dict(custom=_te2.layers_custom,layers=[
    dict(text='Автомат',font='rubik9',fill=(220,10,20,255),strokes=[(3,WHITE)],box=(4,2,150,40),capratio=0.75,align='left'),
    dict(text='Карт',font='rubik9',fill=(220,10,20,255),strokes=[(3,WHITE)],box=(10,36,204,92),capratio=0.85),
    dict(text='Смерти',font='rubik9',fill=(220,10,20,255),strokes=[(3,WHITE)],box=(50,88,208,126),capratio=0.75,align='right'),
]))
tadd('box_comp_US.png','СОБРАНО!',dict(font='rubik9',fill=(150,240,255,255),strokes=[(3,(20,60,120,255))],glow=(5,(80,200,255,255)),capratio=0.8))
tadd('get_US.png','Получено карт',dict(font='oswald',fill='auto',capratio=0.8,align='left'))
for t,x in [('menu_select_05_US.png','Выход'),('menu_select_04_US.png','Список карт'),('menu_select_03_US.png','Использовать U-билет'),
            ('menu_select_02_US.png','Использовать S-билет'),('menu_select_01_US.png','Вытянуть несколько'),('menu_select_00_US.png','Вытянуть карту')]:
    tadd(t,x,dict(font='rubik5',fill='auto',capratio=0.75,align='left'))
tadd('menu_money_US.png','Всего G',dict(font='oswald',fill=WHITE,strokes=[(4,BLACK)],capratio=0.8,align='left'))
tadd('menu_title_US.png','Абсолютный Автомат Карт Смерти',dict(font='rubik9',fill=WHITE,strokes=[(2,BLACK)],capratio=0.8,align='left'))
tadd('rank_disp_US.png','Ранг',dict(font='rubik9',fill=(255,240,0,255),strokes=[(4,BLACK)],capratio=0.8))
tadd('rank_hai_US.png','Шанс',dict(font='rubik5',fill=WHITE,strokes=[(4,BLACK)],capratio=0.8))
# button guides with icons: replace only words
for t in ['guide1_US.png','guide1_xone_US.png','guide1_win_US.png','guide1_batu_US.png']:
    tadd(t,'',dict(custom=_te2.words_custom,words=['Далее','Пропуск'],segments=[(62,149),(222,308)],font='rubik5',fill=WHITE,capratio=0.72))
for t in ['guide2_US.png','guide2_xone_US.png','guide2_win_US.png','guide2_batu_US.png']:
    tadd(t,'',dict(custom=_te2.words_custom,words=['Далее'],segments=[(62,149)],font='rubik5',fill=WHITE,capratio=0.72))
for t in ['guide_US.png','guide_xone_US.png','guide_win_US.png','guide_win_az_US.png']:
    tadd(t,'',dict(custom=_te2.words_custom,words=['Сменить автомат'],segments=[(133 if t=='guide_US.png' else 126,486)],font='rubik5',fill=WHITE,capratio=0.8,only=['carddeath_guide']))

# ---------- battle effect labels ----------
EFF={'011':('Лёд',(120,190,255),(10,40,140),(60,140,255)),'013':('Молния',(255,230,40),(120,70,0),(255,240,60)),
'015':('Ветер',(200,250,255),(20,110,130),(120,230,240)),'017':('Ослабление',(130,255,200),(10,90,80),(60,230,210)),
'018':('Поглощение',(255,60,60),(90,0,10),(255,40,120)),'019':('Отчаяние',(255,20,130),(40,0,30),(200,0,180)),
'021':('Яд',(255,170,255),(110,20,140),(170,40,220)),'023':('Апатия',(210,225,230),(60,80,90),(190,200,210)),
'025':('Слепота',(20,10,10),(255,40,40),(255,20,20)),'027':('Смятение',(255,200,60),(120,30,0),(255,80,40)),
'029':('Проклятие',(130,170,255),(20,20,140),(60,40,255)),'031':('Сон',(90,230,255),(10,80,120),(60,220,240))}
for k,(x,f,s,g) in EFF.items():
    tadd(f'effect_{k}_US.png',x,dict(font='oswald',italic=0.06,fill=f+(255,),strokes=[(4,s+(255,))],glow=(28,g+(255,)),glow_gain=3.0,box=(40,110,360,290),capratio=0.75))

# ---------- casino misc / slots / Monomono machine ----------
gadd('casino_top_diff_tx_closed_US.png','ЗАКРЫТО',G_SANS,bg='auto',capratio=0.85)
tadd('casino_keihin_soldout_tx_US.png','ПРОДАНО',dict(font='russo',fill=(150,152,152,255),bg='auto',capratio=0.8))
tadd('casino_keihin_img_soldout_tx_US.png','ПРО-\nДАНО',dict(custom=_te2.stamp_custom,font='russo',frame=(30,62,226,194),tbox=(42,74,214,182),fw=8,rotate_stamp=22,capratio=0.9,line_gap=0.85,fill=(214,214,214,255)))
NEON_MAG=dict(fill=(240,120,240,255),strokes=[(3,(255,230,255,255))],glow=(8,(230,30,230,255)),glow_gain=2.0,basefill=(0,0,0,255))
tadd('text_DXT1.png','БОНУСНАЯ ИГРА!',dict(NEON_MAG,font='rubik9',italic=0.18,box=(40,60,990,200),capratio=0.6,only=['slot_cutin_bonus']))
tadd('lucky_US_DXT1.png','УДАЧА!',dict(NEON_MAG,font='rubik9',italic=0.18,rotate=-10,box=(20,20,240,110),capratio=0.55))
tadd('detail_DXT1.png','Подробно',dict(G_SCRIPT,basefill=(0,0,0,255),box=(10,10,320,160),capratio=0.5,only=['slot_setumei']))
gadd('title_01_US.png','Пояснения',G_SANS,align='right',only=['slot_setumei','slot_machine'])
gadd('title_00_US.png','МОНОМОНО СЛОТЫ',G_IT,align='left',only=['slot_setumei','slot_machine'])
CHROME=dict(font='rubik',gradient=[(120,120,125),(235,235,240),(150,150,155)],strokes=[(3,(60,60,65,255))],capratio=0.7)
tadd('lucky_base_US.png','Счастливый шанс!',CHROME)
tadd('lucky_base_ef_all_DXT1_US.png','Счастливый шанс!',dict(font='rubik',fill=(255,230,60,255),strokes=[(2,(80,60,0,255))],basefill=(0,0,0,255),capratio=0.7))
ORNEON=dict(font='russo',fill=(255,240,200,255),strokes=[(3,(255,150,20,255))],glow=(6,(255,140,0,255)),glow_gain=2.0,basefill=(0,0,0,255),capratio=0.6)
tadd('lucky_l_DXT1.png','УДАЧА!',dict(ORNEON,fill=(10,30,10,255),strokes=[(3,(40,90,40,255))],glow=None))
tadd('lucky_s_DXT1.png','УДАЧА!',ORNEON)
tadd('help_US.png','ПОМОЩЬ',dict(font='russo',fill=(252,244,4,255),capratio=0.9,only=['m_guide']))
tadd('list_US.png','СПИСОК',dict(font='russo',fill=(252,244,4,255),capratio=0.9,only=['m_guide']))
tadd('kanban_US.png','БОНУСНАЯ ИГРА!',dict(font='rubik9',italic=0.15,gradient=[(70,55,20),(30,22,5)],strokes=[(2,(150,120,40,255))],bg='auto',capratio=0.6,only=['slot']))

# =====================================================================================
# v2.2 (11.10.2026): правки по сверке с оригиналом. Применяются поверх описаний выше.
# =====================================================================================
def override(tex, _where=None, **kw):
    n = 0
    for s in SPECS:
        if s['tex'] == tex and (_where is None or any(o in (s.get('arch') or '') for o in _where)):
            for k, v in kw.items():
                if v is None: s.pop(k, None)
                else: s[k] = v
            n += 1
    assert n, tex

DARK_GOLD = (55, 30, 0, 255)
SCRIPT = dict(font='vibes', embolden=1.1, gradient='orig', grad_erode=1.2, strokes=[(1.3, DARK_GOLD)], glow=(3, (255, 225, 140, 255)), glow_gain=0.7,
              capratio=None, italic=None, line_gap=None, stroke=None, stroke_fill=None)
LABEL = dict(font='philo', gradient='orig', grad_erode=1.5, strokes=[(1.4, DARK_GOLD)], glow=None, italic=None, grow=1.3, minh=0.8,
             stroke=None, stroke_fill=None)
# --- казино: большие надписи прописью (Great Vibes) + огоньки из оригинала ---
override('casino_top_tx_US.png', text='', custom=_te.layers_custom, keep_dots=True, layers=[
    dict(SCRIPT, text='Добро пожаловать в', box=(170, 6, 505, 70), cap=34, align='right', rotate=4),
    dict(SCRIPT, text='Казино', box=(10, 30, 480, 190), cap=128, rotate=7, embolden=2.4),
])
override('casino_result_tx_US.png', **dict(SCRIPT, text='Итоги', box=(20, 0, 500, 175), cap=128, rotate=8, embolden=2.4, keep_dots=True, widen=False))
override('casino_kankin_tx_US.png', **dict(SCRIPT, text='Обмен', box=(15, 0, 500, 160), cap=124, rotate=8, embolden=2.4, keep_dots=True, widen=False))
for t, x in [('casino_top_coin_tx_US.png', 'Монеты'), ('casino_top_bet_tx_US.png', 'Ставка'), ('casino_detail_tx_US.png', 'Подробно'),
             ('casino_hanyo_tx_US.png', 'Внимание'),
             ('casino_kankin_shoji_medal_tx_001_US.png', 'Монеты'), ('casino_kankin_shoji_medal_tx_000_US.png', 'Мономонеты')]:
    override(t, **dict(SCRIPT, text=x, capratio=1.0, grow=1.4, minh=0.85))
override('casino_keihin_tx_US.png', **dict(SCRIPT, text='Обмен призов', capratio=0.8, grow=1.15, minh=0.85))
override('detail_DXT1.png', **dict(SCRIPT, text='Подробно', capratio=0.62, grow=1.1, minh=0.85, box=(10, 10, 320, 160), basefill=(0, 0, 0, 255), grad_lum=110, grad_erode=0.5))
# --- казино: подписи (Philosopher) ---
for t, x, fnt in [('casino_top_title_tx_towa_US.png', 'БЕЗЗАКОННЫЙ ПРОБЕГ', 'philoi'), ('casino_top_title_tx_sake_US.png', 'ЛОВЛЯ ЛОСОСЯ', 'philoi'),
                  ('casino_top_title_tx_mono_US.png', 'ОХОТНИК ЗА СОКРОВИЩАМИ! Монолит', 'philoi'),
                  ('casino_top_hs_tx_US.png', 'Рекорд', 'philo'), ('casino_top_diff_tx_normal_US.png', 'Обычный', 'philo'),
                  ('casino_top_diff_tx_hard_US.png', 'Злой', 'philo'), ('casino_top_diff_tx_easy_US.png', 'Добрый', 'philo'),
                  ('casino_detail_sub_tx_score_US.png', 'Очки', 'philo'), ('casino_detail_sub_tx_rank_US.png', 'Ранг', 'philo'),
                  ('casino_result_sub_tx_score_US.png', 'Очки', 'philo'), ('casino_result_sub_tx_rank_US.png', 'Ранг', 'philo'),
                  ('casino_result_sub_tx_bet_US.png', 'СТАВКА', 'philoi'), ('casino_result_shokin_tx_US.png', 'Выигрыш', 'philo'),
                  ('casino_kankin_choice_tx_change_US.png', 'Обменять', 'philo'), ('casino_kankin_choice_tx_cancel_US.png', 'Отмена', 'philo'),
                  ('casino_kankin_shoji_tx_000_US.png', 'В наличии', 'philo'), ('casino_keihin_present_shoyu_tx_US.png', 'В наличии', 'philo'),
                  ('casino_keihin_tab_tx_theme_US.png', 'Темы блокнота', 'philoi'), ('casino_keihin_tab_tx_skill_US.png', 'Навыки', 'philoi'),
                  ('casino_keihin_tab_tx_present_US.png', 'Подарки', 'philoi')]:
    override(t, **dict(LABEL, text=x, font=fnt))
override('casino_top_diff_tx_closed_US.png', **dict(LABEL, text='ЗАКРЫТО', font='ptserif', custom=_te.plate_custom, bg=None, grow=None,
         plate=(136, 10, 378, 55), plate_r=0, plate_pct=25, tbox=(146, 12, 368, 53), capratio=0.86, maxw=214, minh=0.8,
         grad_box=(146, 10, 368, 55), grad_lum=110, grad_erode=0.5, grad_bins=8, strokes=[(1.0, (30, 18, 0, 255))]))
override('title_01_US.png', **dict(LABEL, text='Пояснения'))
override('title_00_US.png', **dict(LABEL, text='МОНОМОНО СЛОТЫ', font='philoi'))
# табличка BONUS GAME! (слоты): раньше закрашивалась вся вместе с золотой рамкой
override('kanban_US.png', text='БОНУСНАЯ ИГРА!', custom=_te.plate_custom, bg=None, gradient=None, font='russo', italic=0.12,
         fill=(45, 30, 5, 235), strokes=[(1.6, (150, 115, 40, 255))], shadow=(1, 2, (255, 225, 120, 150)), capratio=0.62, minh=0.8,
         plate=(92, 96, 934, 182), plate_r=40, tbox=(170, 98, 880, 180))

# --- План развития: логотип (градиент как в оригинале — жёлтый сверху, малиновый снизу; ширина как у оригинала) ---
override('logo_ikusei_US.png', font='oswald', embolden=2.5, gradient='orig', grad_erode=12, grad_bins=16, strokes=[(12, BLACK), (7, WHITE)], italic=0.1,
         grow=1.0, minh=0.6, capratio=0.72, halftone=(9, 2.0, 0.35), maxw=None)
override('logo_koukou_US.png', gradient='orig', grad_erode=7, grow=1.3, minh=0.85, maxw=None)
override('logo_tyou_US.png', gradient='orig', grad_erode=8)
override('title_coursesele_US.png', font='mpr9', italic=0.12, strokes=[(5, NAVY)], capratio=0.74, grow=1.02, minh=0.75)
override('title_charasele_US.png', font='mpr9', italic=0.12, strokes=[(5, NAVY)], capratio=0.74, grow=1.02, minh=0.75)
for t in ['course_00_US.png', 'course_01_US.png', 'course_02_US.png', 'course_03_US.png']:
    override(t, cap=37, capratio=None, maxw=370, minh=0.8)
override('skill_title_US.png', font='mpr9', italic=None, strokes=[(5.5, BLACK), (3, WHITE)], capratio=0.72)
override('result_title_US.png', font='mpr9', italic=None, strokes=[(6, BLACK), (3, WHITE)], capratio=0.75, grow=1.15)
override('skill_kakera_US.png', grow=1.1, minh=0.8)
override('charalist_title_US.png', grow=1.12, minh=0.8)
for t in ['month_%02d_US.png' % i for i in range(1, 13)] + ['year_01_US.png', 'year_02_US.png', 'year_03_US.png', 'goal_telop_00_US.png']:
    override(t, italic=None, font='mpr9', grow=1.25, minh=0.8, capratio=0.74)

# --- Подземелье Отчаяния ---
# как в оригинале: «Monokuma's» — маленький сверху слева (антиква), «Test» — крупный внизу справа
override('logo_main_US.png', layers=[
    dict(text='Тест', font='rubik9', italic=0.15, gradient='orig', grad_box=(640, 300, 1500, 585), grad_erode=10,
         strokes=[(14, (40, 0, 0, 255)), (9, WHITE)], shadow=(6, 8, (0, 0, 0, 160)), box=(620, 270, 1560, 585), capratio=0.86),
    dict(text='Монокумы', font='ptserif', gradient='orig', grad_box=(300, 140, 1060, 320), grad_erode=5,
         strokes=[(9, (40, 0, 0, 255)), (5, WHITE)], box=(300, 125, 1230, 330), capratio=0.74),
])
override('logo_sub_US.png', grow=1.04, minh=0.75, font='rubik', capratio=0.66)
for k in ['011', '013', '015', '017', '018', '019', '021', '023', '025', '027', '029', '031']:
    override('effect_%s_US.png' % k, jitter=0.07, jrot=7, seed=int(k), box=(28, 60, 372, 340), capratio=0.6, minh=0.62,
             under=_te.aura_under, glow_gain=2.2)

# --- Автомат Карт Смерти ---
for t, x in [('menu_select_05_US.png', 'Выход'), ('menu_select_04_US.png', 'Список карт'), ('menu_select_03_US.png', 'Использовать U-билет'),
             ('menu_select_02_US.png', 'Использовать S-билет'), ('menu_select_01_US.png', 'Вытянуть пачку'), ('menu_select_00_US.png', 'Вытянуть карту')]:
    override(t, text=x, font='rubik4', maxw=370, minh=0.82, capratio=0.75)
override('menu_title_US.png', font='oswald', fill=BLACK, strokes=[(4, WHITE)], first_fill=(235, 10, 140, 255), grow=1.0, minh=0.8, capratio=0.82)
override('box_mark_US.png', clear='all', layers=[
    dict(text='Автомат', font='rubik9', fill=(220, 10, 20, 255), strokes=[(3, WHITE)], shadow=(2, 2, (110, 0, 0, 255)), box=(4, 0, 104, 34), capratio=0.72, align='left', minh=0.6),
    dict(text='Карт', font='rubik9', fill=(220, 10, 20, 255), strokes=[(3, WHITE)], shadow=(2, 2, (110, 0, 0, 255)), box=(30, 32, 182, 92), capratio=0.85),
    dict(text='Смерти', font='rubik9', fill=(220, 10, 20, 255), strokes=[(3, WHITE)], shadow=(2, 2, (110, 0, 0, 255)), box=(66, 88, 208, 126), capratio=0.75, align='right'),
])
override('box_comp_US.png', font='comfortaa', gradient='orig', grad_erode=7, strokes=[(8, BLACK), (4.5, WHITE)], glow=(10, (60, 210, 255, 255)),
         glow_gain=1.2, capratio=0.56, grow=1.1, minh=0.8, fill=None)
override('get_US.png', only=['carddeath_get_list'])
for t in ['guide1_US.png', 'guide1_xone_US.png', 'guide1_win_US.png', 'guide1_batu_US.png']:
    override(t, custom=_te.guide_custom, words=['Далее', 'Пропуск'], font='rubik4', segments=[(60, 150), (220, 310)])
for t in ['guide2_US.png', 'guide2_xone_US.png', 'guide2_win_US.png', 'guide2_batu_US.png']:
    override(t, custom=_te.guide_custom, words=['Далее'], font='rubik4', segments=[(60, 150)])
for t in ['guide_US.png', 'guide_xone_US.png', 'guide_win_US.png', 'guide_win_az_US.png']:
    override(t, custom=_te.guide_custom, words=['Сменить автомат'], font='rubik4', segments=[(133 if t == 'guide_US.png' else 126, 486)])

# --- слоты / автомат Мономоно: не упираться в края ---
override('text_DXT1.png', box=(60, 60, 964, 200), widen=False, minh=0.75)
override('lucky_base_US.png', grow=1.02, minh=0.75, font='comfortaa')
override('lucky_base_ef_all_DXT1_US.png', box=(66, 8, 958, 120), widen=False, minh=0.75, font='comfortaa', embolden=1.5, glow=(6, (255, 220, 40, 255)), glow_gain=1.3)
override('lucky_s_DXT1.png', hollow=3, fill=(255, 190, 90, 255), strokes=None, box=(10, 4, 246, 60), widen=False, capratio=0.78)

# вкладки навыков: фон вкладки заливается целиком (раньше оставались обрывки старых букв), текст чуть меньше
for i in range(5):
    override('tab_on_0%d_US.png' % i, custom=_te.plate_custom, bg=None, plate=(7, 7, 313, 105), plate_r=0, plate_flat=True, tbox=(14, 8, 306, 104), capratio=0.44, maxw=272, minh=0.8)
    override('tab_off_0%d_US.png' % i, custom=_te.plate_custom, bg=None, plate=(7, 7, 313, 89), plate_r=0, plate_flat=True, tbox=(14, 8, 306, 88), capratio=0.5, maxw=272, minh=0.8)

# Salmon Team: неоновые трубки (контур букв), как в оригинале
override('title_US.png', _where=['ainori_title'], hollow=2.8, fill=(240, 248, 255, 255), strokes=[(1.2, (80, 150, 255, 255))], font='oswald', glow=(7, (60, 130, 255, 255)), glow_gain=2.2, maxstretch=1.35, cap=33)
override('sindan_US.png', hollow=4.5, fill=(255, 250, 255, 255), strokes=[(2.0, (240, 60, 230, 255))], font='oswald', glow=(8, (235, 40, 230, 255)), glow_gain=2.2, cap=66)
override('kazari_US.png', hollow=2.2, fill=(255, 225, 255, 255), strokes=None, glow=(6, (230, 30, 220, 255)), glow_gain=2.0)
override('date_US.png', text='Выбор места свидания', grow=1.15, minh=0.8, maxw=None)
override('skill_kakera_US.png', maxw=330)
