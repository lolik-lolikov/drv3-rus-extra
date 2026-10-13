import sys,re,json,collections,os;sys.path.insert(0,'tools')
from drv3 import *
cyr=re.compile('[А-Яа-яЁё]')
SPK={'C000':'Шуичи','C001':'Кайто','C002':'Рёма','C003':'Рантаро','C004':'Гонта','C005':'Кокичи','C006':'Корекиё','C007':'К1-Б0','C008':'Кируми','C009':'Химико','C010':'Маки','C011':'Тенко','C012':'Цумуги','C013':'Анджи','C014':'Миу','C015':'Каэде','C020':'Монокума','C021':'Монотаро','C022':'Моноске','C023':'Монофани','C024':'Монодам','C025':'Монокид','C027':'Монокубы','chara_Blank':'(мысли/текст)','chara_Hatena':'???'}
def loadstx(p):
    s=spc_read(open(p,'rb').read()); return {e.name:stx_read(e.data)['strings'] for e in s['entries']}
en=loadstx('orig/01_salmon_team/data/win/wrd_script/003/ainori_text_US.SPC')
ru=loadstx('orig/01_salmon_team/data/win/wrd_script/007/ainori_text_US.SPC')
s=spc_read(open('orig/01_salmon_team/data/win/wrd_script/007/ainori.SPC','rb').read())
wrds={e.name:wrd_read(e.data) for e in s['entries']}
tm={}
for n in en:
    for (_,a),(_,b) in zip(en[n],ru[n]):
        if a!=b and cyr.search(b): tm.setdefault(a,b)
json.dump(tm,open('work/tm_existing.json','w'),ensure_ascii=False,indent=0)
os.makedirs('work/src',exist_ok=True)
todo=[]
for n,st in en.items():
    if any(cyr.search(x) for _,x in ru[n]): continue
    w=wrds[n.replace('.stx','.wrd')]
    spk={}; cur='?'
    for c,a in w['cmds']:
        if c=='CHN':
            pn=w['params'][a[0]]; cur=SPK.get(pn[:4],SPK.get(pn,pn))
        elif c=='LOC' and a: spk.setdefault(a[0],cur)
    lines=[]
    for i,(sid,x) in enumerate(st):
        if not re.search('[A-Za-z]',x) or x.startswith('<CLT=cltSYSTEM>') and False: pass
        e=x.replace('\n','\\n')
        tag='' 
        if x in tm: tag=' [TM: '+tm[x].replace('\n','\\n')+']'
        lines.append(f"{i}\t{spk.get(i,'—')}\t{e}{tag}")
    open(f'work/src/{n[:-4]}.txt','w').write('\n'.join(lines)+'\n')
    todo.append(n[:-4])
open('work/todo_list.txt','w').write('\n'.join(sorted(todo)))
print(len(todo),len(tm))
