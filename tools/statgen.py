"""Auto-translate formulaic stat lines 'X increases N%' (Talent Plan / RPG)."""
import re
ST = {'Luck':'Удача','Influence':'Влияние','Fortitude':'Стойкость','Focus':'Концентрация','Intellect':'Интеллект',
      'Defense':'Защита','Agility':'Ловкость','Strength':'Сила'}
def tr_line(l):
    l=l.strip()
    if not l: return ''
    m=re.fullmatch(r'Other (?:attributes|status) increases? (\d+)%',l)
    if m: return 'Прочие параметры +%s%%'%m.group(1)
    m=re.fullmatch(r'(\w+) and (\w+) increases? (\d+)%',l)
    if m: return '%s и %s +%s%%'%(ST[m.group(1)],ST[m.group(2)].lower(),m.group(3))
    m=re.fullmatch(r'(\w+) increases? (\d+)%',l)
    if m: return '%s +%s%%'%(ST[m.group(1)],m.group(2))
    return None
def tr(s):
    parts=s.split('\\n'); out=[]
    for p in parts:
        t=tr_line(p)
        if t is None: return None
        out.append(t)
    return '\\n'.join(out)
GEN={'Сила':'f','Защита':'f','Стойкость':'f','Ловкость':'f','Удача':'f','Концентрация':'f','Интеллект':'m','Влияние':'n'}
VERB={'f':'повысилась','m':'повысился','n':'повысилось'}
def tr_clt(s):
    m=re.fullmatch(r'<CLT=13>(\w+)<CLT=0> increased!( ?)',s)
    if m and m.group(1) in ST:
        ru=ST[m.group(1)]
        return f'<CLT=13>{ru}<CLT=0> {VERB[GEN[ru]]}!{m.group(2)}'
    return None
_tr=tr
def tr(s):
    return tr_clt(s) or _tr(s)
