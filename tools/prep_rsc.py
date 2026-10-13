import sys,os,re,struct,json;sys.path.insert(0,'tools')
from drv3 import *
N={'AKAMATSU':'Каэде','AMAMI':'Рантаро','ASAHINA':'Аой','CELESTIA':'Селестия','CHABASHIRA':'Тенко','ENOSHIMA_M':'Джунко?(Мукуро)','ENOSHIMA':'Джунко','GOKUHARA':'Гонта','HAGAKURE':'Ясухиро','HANAMURA':'Тэрутэру','HARUKAWA':'Маки','HINATA':'Хаджимэ','HOSHI':'Рёма','HUJISAKI':'Чихиро(м)','HUKAWA':'Токо','IKUSABA':'Мукуро','IRUMA':'Миу','ISHIMARU':'Киётака','JENOSAIDA':'Убийца Сё','KAMUKURA':'Изуру','KIRIGIRI':'Кёко','KI_BO':'К1-Б0','KOIZUMI':'Махиру','KOMAEDA':'Нагито','KUWATA':'Леон','KUZURYU':'Фуюхико','MAIZONO':'Саяка','MIODA':'Ибуки','MOMOTA':'Кайто','MONOKUMA':'Монокума','MONOMI':'Мономи','NAEGI':'Макото','NANAMI':'Чиаки','NIDAI':'Нэкомару','OGAMI':'Сакура','OMA':'Кокичи','OWADA':'Мондо','OWARI':'Аканэ','PEKOYAMA':'Пеко','SAIHARA':'Шуичи','SAIONJI':'Хиёко','SHINGUJI':'Корекиё','SHIROGANE':'Цумуги','SONIA':'Соня','SOUDA':'Казуичи','TANAKA':'Гандам','TOGAMI_S':'Бьякуя?(самозванец)','TOGAMI':'Бьякуя','TOJO':'Кируми','TSUMIKI':'Микан','USAMI':'Усами','YAMADA':'Хифуми','YONAGA':'Анджи','YUMENO':'Химико','MONOTARO':'Монотаро','MONOFUNNY':'Монофани','MONOSUKE':'Моноске','MONODAM':'Монодам','MONOKID':'Монокид','NONE':'(текст)'}
txt={e.name:rsct_read(e.data) for e in spc_read(open('orig/08_batch1/1/rsc_text_package_US.spc','rb').read())['entries']}
os.makedirs('work/rsrc',exist_ok=True)
index=[]
for k in ['friend','happen','individual','individual_a3','rpg','season','story','test']:
    strs=txt[f'RscText_{k}.rsct']['strings']
    s=spc_read(open(f'orig/08_batch1/1/{k}.spc','rb').read())
    pos=0
    for e in s['entries']:
        n=struct.unpack_from('<H',e.data,0)[0]
        w=wrd_read(e.data); spk={}; cur='?'; actors={}
        for c,a in w['cmds']:
            P=w['params']
            if c=='x57' and len(a)>=2: actors[P[a[0]]]=P[a[1]]
            if c=='x53' and a:
                pn=P[a[0]]
                if pn.startswith('RSC_CHARA_ID_'): cur=N.get(pn[13:],pn[13:])
                elif pn=='wkHeroNo': cur='ГЕРОЙ'
                else: cur=pn
            if c=='x58' and a: spk.setdefault(a[0],cur)
        name=f"{k}__{e.name[:-4]}"
        lines=[f"{i}\t{spk.get(i,'—')}\t{strs[pos+i][1].replace(chr(13),'\\r').replace(chr(10),'\\n')}" for i in range(n)]
        open(f'work/rsrc/{name}.txt','w').write('\n'.join(lines)+('\n' if lines else ''))
        index.append((name,f'RscText_{k}.rsct',pos,n)); pos+=n
    assert pos==len(strs)
for k in ['CommonText','RPGText','SuccessText','CarddessText']:
    strs=txt[f'{k}.rsct']['strings']
    # split into chunks of 200 for manageability
    for c0 in range(0,len(strs),200):
        name=f'ui__{k}_{c0//200:02d}'; n=min(200,len(strs)-c0)
        lines=[f"{i}\tUI\t{strs[c0+i][1].replace(chr(13),'\\r').replace(chr(10),'\\n')}" for i in range(n)]
        open(f'work/rsrc/{name}.txt','w').write('\n'.join(lines)+'\n')
        index.append((name,f'{k}.rsct',c0,n))
json.dump(index,open('work/rsc_index.json','w'))
print(len(index))
