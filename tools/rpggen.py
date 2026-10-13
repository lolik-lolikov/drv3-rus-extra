"""Pattern translator for RPG (Despair Dungeon) item/monster/floor names."""
import re
# monster: (nominative, genitive)
MON = {
 'Monokumamel':('Монокумамел','Монокумамела'),
 'Fluffy Monobunny':('Пушистый Монокролик','Пушистого Монокролика'),
 'Monokuma Gather':('Монокума-Стая','Монокумы-Стаи'),
 'Monokumantala':('Монокумантула','Монокумантулы'),
 'Monokuma Hermit':('Монокума-Отшельник','Монокумы-Отшельника'),
 'Curse Monogirl':('Проклятая Монодевочка','Проклятой Монодевочки'),
 'Floor Monodragon':('Монодракон Этажа','Монодракона Этажа'),
 'Monodragon Head':('Голова Монодракона','Головы Монодракона'),
 'Twisty Monokuma':('Кручёный Монокума','Кручёного Монокумы'),
}
# part: (noun, gender)
PART = {'Fang':('Клык','m'),'Eye':('Глаз','m'),'Meat':('Мясо','n'),'Skin':('Шкура','f'),'Fur':('Мех','m')}
METAL = {'Copper':'Медн','Silver':'Серебрян','Gold':'Золот','Platinum':'Платинов'}
END = {'m':'ый','f':'ая','n':'ое','p':'ые'}
def adj(stem,g):
    # stems ending in hush/k/g/h take -ий/-ие in m/p
    e=END[g]
    if stem[-1] in 'кгхжшчщ' and g in 'mp': e={'m':'ий','p':'ие'}[g]
    if stem.endswith('Школьн') or stem.endswith('школьн'): pass
    return stem+e
# equipment nouns: (noun, gender)
EQ = {'Talisman':('Талисман','m'),'Uniform':('Форма','f'),'Hat':('Шляпа','f'),'Shoes':('Ботинки','p'),
      'Staff':('Посох','m'),'Hacking Gun':('Хакерская пушка','f'),'Shield':('Щит','m'),'Katana':('Катана','f'),
      'Gun':('Пушка','f')}
PRE_ADJ = {'Tattered':'Потрёпанн','Cheap':'Дешёв','Regular':'Обычн','High Schooler\'s':'Школьн','Intellectual':'Интеллектуальн',
           'Safety':'Защитн','Ultimate':'Абсолютн','Golden':'Золот','Adult\'s':'Взросл','Worn':'Изношенн',
           'High Speed':'Скоростн','Extreme':'Экстремальн','New':'Нов'}
OF = {'Power':'Силы','Overflowing Talent':'Избытка Таланта','Courage':'Отваги','Victory':'Победы','Magic':'Магии',
      'Atua':'Атуа','Hope':'Надежды','Legend':'Легенды'}
POSS = {'Hard Worker\'s':'Трудяги','Champion\'s':'Чемпиона'}
SUF = {'Dash':'Дэш','Turbo':'Турбо','ZERO':'ЗЕРО','EX':'EX','Impact':'Импакт','Strike':'Страйк','Extreme':'Экстрим'}
def low_first(s): return s[0].lower()+s[1:]
def eq(t):
    for k,(n,g) in sorted(EQ.items(), key=lambda x:-len(x[0])):
        if k not in t: continue
        if t==k: return n
        m=re.fullmatch(re.escape(k)+r' (\d|V3)',t)
        if m: return n+' '+m.group(1)
        for a,st in PRE_ADJ.items():
            if t==a+' '+k:
                if ' ' in n:  # adjective+noun phrase
                    return adj(st,g)+' '+low_first(n)
                return adj(st,g)+' '+low_first(n)
        for a,s in OF.items():
            if t==k+' of '+a: return n+' '+s
        for a,s in POSS.items():
            if t==a+' '+k: return n+' '+s
        if t=='Super '+k: return 'Супер-'+low_first(n)
        if t=='Ultra '+k: return 'Ультра-'+low_first(n)
        if t=='V '+k or t==k+' V': return n+' V'
        if t=='The End of '+k: return adj('Последн',g).replace('Последный','Последний').replace('Последная','Последняя').replace('Последное','Последнее').replace('Последные','Последние')+' '+low_first(n)
        if t=='New '+k: return adj('Нов',g)+' '+low_first(n)
        for a,s in SUF.items():
            if t==k+' '+a: return n+' '+s
    return None
def mon(t):
    m=re.fullmatch(r'(.+?)(?: (V\d?|[BSGP]))?',t)
    if m and m.group(1) in MON:
        return MON[m.group(1)][0]+((' '+m.group(2)) if m.group(2) else '')
    return None
def material(t):
    m=re.fullmatch(r'(.+?)(?: (V\d?))? (Fang|Eye|Meat|Skin|Fur)',t)
    if not m: return None
    base,v,p=m.groups(); n,g=PART[p]
    if base in METAL and not v: return adj(METAL[base],g)+' '+low_first(n)
    if base in MON: return n+' '+MON[base][1]+((' '+v) if v else '')
    return None
def floor(t):
    m=re.fullmatch(r'(\d+)(?:st|nd|rd|th)-(\d+)(?:st|nd|rd|th) Floor',t)
    if m: return 'Этажи %s-%s'%m.groups()
    if t=='? Floor': return 'Этаж ?'
    m=re.fullmatch(r'Material (\d+)',t)
    if m: return 'Материал '+m.group(1)
    return None
def tr(t):
    for f in (floor,material,mon,eq):
        r=f(t)
        if r: return r
    return None
if __name__=='__main__':
    import sys
    for t in sys.argv[1:]: print(t,'->',tr(t))
