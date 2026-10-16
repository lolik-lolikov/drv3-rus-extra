# Аудит картинок (14.10)
ВАЖНО: картинки в контексте пропадают после ~20 просмотров — записывать находки сразу.

## Непереведённые (найдено)
- flash/slot копии в minigame/slot_machine_US.SPC: text_DXT1 (BONUS GAME!), detail_DXT1 (Detail) — фильтр only не пускал slot_machine.
- slot_machine_US.SPC: ef_00..09_US буквы B,O,N,U,S,G,A,M,E,! -> БОНУС ИГРА! (Б,О,Н,У,С,И,Г,Р,А,!)
- slot_machine_US.SPC + flash/slot/slot_light_US: parts_l/m/n/o/s/t_US (неон) -> МОНОМОНО СЛОТ: N->Н, S->С, L->Л (M,O,T те же); title_bg_US «MONOMONO SLOT» (бледная полоса)
- WILD (wild_0/1, icon_02, icon_US в slot_wild/slot_machine), SCATTER (scatter_0/1, icon_03, icon_sca_US) — решить термин
- monolith_US: SCORE (t_casino_hkt_score_tx_DXT1), TREASURE HUNTER! (start_tx_otakara_US x2), Monolith (start_tx_monolith_US x2), START! (start_tx_start_US), TIME! (last_tx_timeup1/2), PERFECT! x4 цвета, NO MORE MOVES! x2, GET!! с картинками x6 (sake, monomi, kumas — по 2)
- sake_no_tukamidori_US: TIME (time_US), SCORE (t_sake_score_tx), MONO-EYE (title_US, повёрнут), GET! (get_US), SALMON! (combo_tx_US), EXTREME! (text_ex_US), ORDER (text_order_US, дугой), READY по буквам title_00..04 + «...» title_05 (2 набора), GO! title_06/07/08?, MISS! (mis_US), COMBO!/COMBOS! (t_casino_combo_tx_single_US, _US, _4,_3,_2), Miss (t_drive_cutin_miss_tx)
- towa_run_US: OUTLAW RUN (stencil_tx_000_US, 001_US, 000_US копия), GO!! (towa_tx_US_DXT1 + tx_ef_US), KM/H (casino_drive_meter), TIME (casino_drive_time_tx_US), SCORE (casino_score_tx_US), COMBO!/COMBOS! x5, SPEED UP! (speedup_tx_US + _ef), FINISH! (towa_finish_tx_US_DXT1 + tx_ef_US)
- towa_texture_US: вывески в 3D-городе (HOTEL TOWA, MONOKUMART, BOOK GAME VIDEO CD, Safety First) — окружение, не трогаем
- minigame/rsc/bg/bg100..113_US — обучающие скриншоты с английским UI (12 шт.)
- success_hud_course_check: check_guide_win_az_US — японский текст «高速移動» (проверить, что это и переведены ли соседние)
- NEW (success_chara_select_list/menu, course_select_menu, result_data) — пиксельная надпись
- LV (success_skill_list headline, success_status LV_US)

## Не трогаем (решено)
- data_win (не-US) файлы доп. режимов: текста нет (кроме эмблем HIGH SCHOOL и японских bg100-113 без _US).
- flash/effect/ef_* — звукоподражания основной игры (вне доп. режимов).
- effect_011..032: только кадры эффектов, надпись effect_0xx_US уже переведена.
- ainori_common_page_US: AUTO = буквы auto_a/u/t/o_(day|night)_US 64x32 (оранжевые днём, синие ночью) -> АВТО: менять только U -> В (A,T,O совпадают)
- ainori_bgm_base_US: danron_US 512x512 — круговая надпись «DANGAN SALMON TEAM» (название группы/режима; логотип — решить)
- ainori_date_view_US: text_go_US 128x64 «GO!» (белый блочный шрифт) -> «ИДЁМ!»
- ainori_day_US: day_day_US / day_night_US 128x128 — «DAY» по диагонали (оранж/синий, с обводкой) -> «ДЕНЬ»
- ainori_day_change_US: day_lang_000/001_US 192x64 «DAY» (жёлто-оранж / голубо-синий градиент, тёмная обводка) -> «ДЕНЬ»; буквы day_day_a/d/y_US 64x64 (+ day_night_*) D,A,Y -> Д,Е,НЬ? (посмотреть раскладку в sfl)
- ainori_sindan_US: monokumaz_US 1024x256 — неоновая «MONOKUMA» (голубые трубки, вместо второй O голова Монокумы) -> «МОНОКУМА»: заменить N->Н, U->У, остальное совпадает
- casino (все np_casino_00..04 просмотрены): непереведённого текста нет; ранги S/AAA..CCC (латиница, оставить), цифры, рамки, эмблемы монет «DANGAN CASINO» (мелко, оставить).
- m_guide_US: 001_sys_options «OPTIONS» (белый, кнопка) — значок кнопки Options PS4, оставить (это название кнопки)
- m_left_US (не патчится): juhuku_00_US «Re» (оранж), juhuku_01_US «peat» (жёлт), juhuku_02_US «Rate» (зелён) = «Repeat Rate» (шанс повтора) -> перевести (посмотреть раскладку в sfl)
- m_lucky_US: lucky_ef_00..06_DXT1 — японские «ラッキー発生!!» (эффекты-свечение) — проверить, что изменено в m_lucky (4 текстуры) и видны ли ef
- m_machine_US (не патчится): machine_front_US — дуга «MONOMONO» сверху автомата; title_ef_o/n/m — неоновые буквы O,N,M (заголовок MONOMONO?) — проверить раскладку
- slot_bonus_count_US (+ та же srd внутри slot_machine_US.SPC): ef_00..09_US — неоновые буквы B,O,N,U,S,G,A,M,E,! (пурпурный неон на чёрном, курсив) -> «БОНУС ИГРА!» буква в букву: Б,О(оставить),Н,У,С,И,Г,Р,А,!(оставить)
- slot_light_US (+ внутри slot_machine_US): parts_l/m/n/o/s/t_US_DXT1 — голубой неон L,M,N,O,S,T = «MONOMONO SLOT» на верхушке автомата -> «МОНОМОНО СЛОТ»: перерисовать N->Н, S->С, L->Л в том же неоне; title_bg_US 1025x64 — серая «MONOMONO☻SLOT» (незажжённые трубки под неоном) -> перерисовать «МОНОМОНО☻СЛОТ»
- WILD: slot_wild_US icon_US, slot_scatter_US icon_US(тоже WILD!), slot_setumei icon_02, + в slot_machine: wild/icon_US/icon_02; SCATTER: slot_scatter icon_sca_US, slot_setumei icon_03, + slot_machine icon_sca_US/icon_03 — термин решить (см. текст правил)
- np_rsc_00: обложки игр box_pake1/2/3_US (логотипы DR1/DR2/V3 — оставить), значки редкости N/S/U (оставить, в тексте «S Ticket» и т.п.)
- carddeath_get_list_US: new_US «NEW» (красный блочный с белой обводкой) -> «НОВОЕ»
- carddeath_logo_US: logo_title_01/02/03_US — логотипы DR1/DR2/V3 (оставить); carddeath_rank: N/S/U, %, цифры (оставить)
- rpg_battle_command_skill_US (не патч.): «LV» (белый, рядом цифры) -> «УР.» (проверить, как в тексте)
- rpg_chara_select_menu_US: V3/2/1 (номера частей серии — оставить); rpg_create_material: «G» (валюта — оставить, в тексте тоже G)
- rpg_party_status_US (не патч.): LV_US 128x? «LV:» (белый пиксельный, как в bg113 «LV: 2») -> «УР:»
- rpg_staffroll_US (не патч.): staff_00..18_US 1920x120 — белые пиксельные строки (заголовки «DANGANRONPA SERIES CHARACTERS», «DANGANRONPA V3 STAFF», «DEVELOPMENT MODE & RPG MODE STAFF» + имена), position_00..11_US 1920x100 — мелкие пурпурные должности, copyright_* (оставить!). План: перевести заголовки и должности, имена оставить латиницей.
- rpg_status_US (не патч.): LV_US 100x40 «LV» (белый) -> «УР»
- «NEW» (тот же красный блочный): success_chara_select_list, success_chara_select_menu (+ искать во всех файлах по имени new*_US / хешу)
- success_hud_course_check_US: check_guide_win_az_US 746x? «[значки]+[A]/[E] 高速移動» — японский текст (ошибка локализации, клавиатура Win) -> перевести так же, как соседние check_guide_* (см. их перевод)
- NEW: carddeath_get_list, success_chara_select_list, success_chara_select_menu, success_course_select_menu, success_result_data (все new_US 200x64, один рисунок)
- LV (Плана развития): success_skill_list headline_* «LV» (белый с серой обводкой), success_status LV_US 100x? «LV» (чёрный) -> «УР»

## Сверка переведённых (листы ch_all_*)
- ch_00: в целом хорошо. Кандидаты: sindan «Диагноз» — в оригинале узкий (condensed) шрифт, у нас широкий Russo -> попробовать узкий (Oswald/PT Sans Narrow Bold) в том же неоне; casino_top_coin_tx «Монеты» мельче оригинала (проверить крупно); OUTLAW RUN -> «БЕЗЗАКОННЫЙ ПРОБЕГ» сжат и тоньше (длинный текст, допустимо).
- ch_01: хорошо в целом. Улучшить размер: casino_kankin_shoji_medal_tx_001 «Монеты» и _000 «Мономонеты» заметно мельче оригинала (есть место справа — увеличить); keihin_tab «Навыки» мельче «Skill»; top_diff «Добрый» чуть мельче. «Темы блокнота» почти упирается в края — проверить поля.
- ch_02: Казино хорошо. Проверить крупно: top_coin_tx «Монеты» (256x128) упирается в правый край; result_shokin «Выигрыш» упирается в край; result_sub_tx_bet «СТАВКА» мельче; keihin_present_shoyu «В наличии» узкая.
  Автомат Монокумы (m_guide/m_lucky) — расхождения в стиле: HELP/LIST — квадратный «цифровой» шрифт (у нас Russo); LUCKY! (lucky_l, lucky_s) — квадратные ПОЛЫЕ буквы-контуры (у нас сплошные); «Lucky Chance!» — жирный скруглённый (у нас тонкий) -> переделать.
- ch_03: Автомат Карт Смерти хорошо. Мелочь: carddeath_get guide2_*_US (одно «Далее») — буквы мельче, чем «Далее» в guide1_* (сделать одинаковыми с guide1/оригиналом).
- ch_04: подписи эффектов (effect_011..032: Лёд, Молния, Ветер, Ослабление, Поглощение, Отчаяние, Яд, Апатия, Слепота...): в оригинале под буквами ТЕКСТУРНОЕ облако (кристаллы льда, разряды и т.п.), у нас — гладкое размытое пятно; шрифт оригинала «игривый» узкий с прыгающими буквами — у нас ровнее. -> Улучшить фон: восстановить фон оригинала (inpaint по маске букв) вместо размытия; проверить шрифт крупно.
  carddess_charalist_title «Список карт» — в оригинале очень жирный округлый, у нас уже/тоньше (проверить).
- ch_05: rpg_chara_select_guide «Выбор участников» и type_intelli «Интеллектуальный тип» доходят до правого края текстуры — проверить обрезку. Имена charasele: в оригинале узкий плотный шрифт, у нас Rubik шире — допустимо.
- ch_06: charasele_name_* (rpg и success): в оригинале плотный гротеск (как Rodin) с узким трекингом; у нас Rubik 500 — шире, длинные имена сжаты сильнее коротких (разнобой). -> Roboto 500 + отрицательный трекинг, единый вид.
- ch_08: ИСПРАВИТЬ rpg_create_material material_cost_US «Стоимость»: в оригинале тонкий светлый шрифт без обводки, у нас жирный с чёрной обводкой. rpg_create_guide «Создание снаряжения» до края — проверить. rpg_cutin telop_kakusei «Пробуждение!»: в оригинале кистевой рукописный шрифт и крупнее — желательно ближе (кисть/маркер, крупнее). rpg_title_logo logo_sub «Подземелье Отчаяния» — в оригинале широкий округлый, у нас узкий (низкий приоритет).
- ch_10: ИСПРАВИТЬ success_page_cursor «АВТО» — в оригинале средняя толщина (геометрический), у нас слишком жирный; skill_list headline_02 «Конц.» (Focus) — в оригинале обычный вес, у нас жирный; lv_max «МАКС. УР.» — проверить цвет/градиент оригинала; goal_finish «Финиш пройден!» крупнее оригинала и до края — уменьшить, выровнять влево как в оригинале.
- ch_11: success_skill_tab tab_off_00..04: в оригинале буквы с белой внутренней линией (inline/контур), у нас плоская заливка -> сделать контур+внутренняя белая линия как в оригинале; success_step rest_lang_US «клеток осталось» — в оригинале тонкий шрифт с широкой разрядкой, у нас жирный -> тонкий+разрядка; rest_US — в оригинале узкий, у нас широкий жирный до края -> узкий.
- ch_12: success_title_menu menu_card «Вытянуть Карты Смерти» — во всю ширину, вероятно обрезано по краям -> уменьшить; slot_setumei title_01 «Пояснения» крупнее оригинала, у края.
- ОБЩЕЕ: автоматически проверить «касание краёв» у всех переведённых текстур (где у оригинала есть поля).
- АВТОПРОВЕРКА КРАЁВ (audit edge check): 70+ текстур, где перевод касается края, а оригинал нет. Критично: обрезанные нижние выносные (у, р, д) в именах charasele_name_* (rpg и success), месяцах month_* (Февраль, Январь, Апрель, Сентябрь, Август), годах year_01/02 («-й год»), root_min/max; правые края: course_name_00..04, goal_finish, page_cursor, lv_max, carddeath rank_hai/rank_disp, create_title, chara_select_title, title_coursesele/charasele (L), effect_0xx (LR — облако до краёв, у оригинала поля). -> исправить все, затем повторить проверку.
- Карты: дизайн совпадает отлично. Согласовать таланты с текстом v2.3: card_u_010 Маки «Абсолютная Убийца» -> «Абсолютный Киллер»; 103 Мондо «Лидер Байкерской Банды» -> «Лидер Байкеров»; 126 Нэкомару «Менеджер Команды» -> «Менеджер».

## ПЛАН РАБОТ
P1 (дефекты): обрезка у краёв (70+); slot_machine_US копии text_DXT1/detail_DXT1 (в самом слоте остались англ.!); таланты на картах.
P2 (непереведённое): мини-игры казино (monolith/sake/towa), NEW, LV, AUTO-буквы, DAY, GO!, BONUS-буквы, неон MONOMONO SLOT + title_bg, неон MONOKUMA, MONOMONO на автомате + неон-буквы, hud японский текст, Repeat Rate, staffroll заголовки/должности.
P3 (стиль): АВТО, Конц., МАКС.УР., Стоимость, клеток осталось x2, вкладки off, ПОМОЩЬ/СПИСОК, УДАЧА!, Счастливый шанс, Монеты/Мономонеты/Навыки размер, guide2 Далее, эффекты (фон), Диагноз, Пробуждение!, Финиш пройден!
P4: bg100–113 скриншоты, WILD/SCATTER.

## Ход работ (14.10, утро)
- texedit: fit=True (не вылезать за поля оригинала: сдвиг → сужение → уменьшение кегля), desc_squash, valign baseline/captop, vband, lalign, capscale, hollow_inner. Исправлено: имена charasele (Roboto 500, базовая линия), месяцы/годы (без обрезки), курсы, края у ~20 текстур.
- squarefont.py: квадратный цифровой шрифт (ПОМОЩЬ/СПИСОК/УДАЧА!) — сделано.
- Вкладки навыков (Exo 2 Black + цветная обводка), АВТО, МАКС. УР., Конц., Стоимость, клеток осталось x2, Финиш пройден!, казино (размеры) — сделано.
- Шрифты fonts4 (fontsource, OFL): pixelify, tiny5, dotgothic16, rubik-glitch/spray-paint/dirt/distressed/wet-paint/burned, underdog, marmelad, kurale, oi, pangolin, balsamiq 700/700i, pattaya, ruslan-display, lobster. У pixelify нет кир. О (латинская есть).
- analog.py (перенос по ближайшему соседу) — ШУМНО, не годится. Делаю lutfx.py: цвет = LUT(расстояние до края, высота в строке, направление).
- Тексты мини-игр: Ловля лосося: READY…GO! → ГОТОВ… + (2 буквы+!) — решить; GET!→ЕСТЬ!, MISS!→МИМО!, EXTREME!→ЭКСТРИМ!, SALMON!(после числа)→ПОДРЯД!, ORDER→ЗАКАЗ, MONO-EYE→МОНО-ОКО, TIME→ВРЕМЯ, SCORE→ОЧКИ, COMBO(S)!→КОМБО!, Miss(кат-ин)→Промах.
  Беззаконный пробег: OUTLAW RUN→БЕЗЗАКОННЫЙ/ПРОБЕГ, GO!!→ПОЕХАЛИ!!, SPEED UP!→УСКОРЕНИЕ!, FINISH!→ФИНИШ!, KM/H→КМ/Ч.
  Монолит: START!→СТАРТ!, TREASURE HUNTER!→ОХОТНИК ЗА СОКРОВИЩАМИ!, Monolith→Монолит, TIME!→ВРЕМЯ!, PERFECT!→ИДЕАЛЬНО!, NO MORE MOVES!→ХОДОВ НЕТ!, GET!!→ЕСТЬ!!
- 14.10 ~11:00: Ловля лосося — сделано (lutfx: ВРЕМЯ, ОЧКИ, ЕСТЬ!, МИМО!, МОНО-ОКО, ПОДРЯД!, ЭКСТРИМ!, ЗАКАЗ по дуге, ГОТОВ…ГО! по буквам, ФИНИШ!! по буквам (title_04 = копия «!»), КОМБО! x5 (distressed + брызги + царапины), кат-ин «Мимо» (pattaya, лучи сохранены) + эффект (zoom blur, подобран по оригиналу)).
- Беззаконный пробег — сделано: МАРШ!! (старт), РАЗГОН!, ФИНИШ! (glitch_custom, rubik-distressed) + эффекты (zoomfx: сила 0.1/0.2, затухание 2, гаусс 3, регрессия яркости), КМ/Ч, ВРЕМЯ/ОЧКИ (rubik-spray-paint), «БЕЗЗАКОННЫЙ/ПРОБЕГ» трафарет (lutfx lx_sel=clear, lx_far чёрный, rot_all 9.47) + светящаяся копия.
- Осталось: Монолит (пиксель-арт k=8/4), слоты (BONUS-буквы, неон МОНОМОНО СЛОТ, title_bg, WILD/SCATTER?, копии text_DXT1/detail_DXT1 в slot_machine), AUTO-буквы, DAY, GO! (ainori), неон МОНОКУМА, автомат (MONOMONO дуга, неон-буквы O/N/M, Repeat Rate), NEW, LV, hud японский, staffroll, эффекты (фон облака), Диагноз, Пробуждение!, карты (3 таланта), bg100-113.
- 14.10 ~14:40 сделано:
  - Монолит: pixword.py (пиксель-арт: сердцевина-буквы + кольца/заливка/тень с оригинала; число колец — авто; подпиксельная «развёртка» — по таблице (кольцо, сторона, строка/столбец в блоке)); ЕСТЬ!! с картинками (pw_erase — картинка в пикселях оригинала), СТАРТ!, Монолит, ОХОТНИК♥ЗА СОКРОВИЩАМИ!, ВРЕМЯ!, ИДЕАЛЬНО!, ХОДОВ НЕТ! (pw_space 10). SCORE → ОЧКИ: pixglyph.py (шрифт 8×10, палитра 4 цвета, затенение как у О оригинала — совпадает пиксель в пиксель).
  - Слоты: копии БОНУСНАЯ ИГРА!/Подробно в slot_machine; буквы BONUS GAME! → Б,О,Н,У,С,И,Г,Р,А,! (lutfx, rubik9 italic). Вывеска MONOMONO SLOT (parts_* + серая 3D title_bg) — ОСТАВЛЕНА логотипом: серую объёмную вывеску не перерисовать без потерь, а горящие буквы ложатся поверх неё (была бы смесь N/Н).
  - Любовный тест: неон MONOKUMA → МОНОКУМА (neonfx.py: силуэт → трубка, свечение по таблице оригинала, стёртое место — свечением соседних букв).
  - AUTO: U → В (Russo); GO! → ИДЁМ! (squarefont + Ё); DAY → ДЕНЬ (mpr, градиент оригинала, чёрная+белая обводки): day_lang x2, буквы Д/Е/НЬ x2, диагональ (rotstyle_custom — градиент по экрану после поворота).
  - NEW → НОВОЕ (squarefont, x5; в result_data по центру); LV → УР / УР: (x4) и headline_01; hud AZERTY 高速移動 → Быстрый ход; титры RPG: 3 заголовка (Russo) + 10 должностей (Comfortaa), имена латиницей.
  - Автомат Мономоно: Repeat Rate → «Ша»+«нс»+«повтора» (Kurale); дуга MONOMONO → МОНОМОНО (n2h_custom: диагональ стирается inpaint, перекладина — профилем трубки ножек; оси уточняются PCA) + горящая N → Н.
  - Карты: 103 Лидер Байкеров, 126 Менеджер, 132 Абсолютная Фотограф, U-010 Абсолютный Киллер (как в CommonText_00). 137/138 сверены с англ. картой.
  - Эффекты RPG: облако оригинала сохранено (effect_custom: буквы закрашены inpaint, маска по цвету обводки или заливки), новые буквы поверх. «Пробуждение!» — brush_custom (Pattaya, «грязная» синяя заливка, жёлтая смещённая обводка, свечение).
  - Полная сборка 14:3x (489 текстур) + audit/edgecheck.py: 14 замечаний → правки краёв (fit) в конце tex_specs.py. logo_koukou касается левого края намеренно (продолжение «А»).
  - Не переводятся (решено): bg100–113 (обучающие скриншоты UI), логотип DANGAN SALMON TEAM (danron_US), вывеска MONOMONO SLOT, WILD/SCATTER, ранги, логотипы Danganronpa.
