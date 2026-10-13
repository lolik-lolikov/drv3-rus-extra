"""Rebuild Talent Plan speaker name plates (chara_name_XXX_US.spc) in Russian."""
import sys,os,json,glob
sys.path.insert(0,os.path.dirname(__file__))
from drv3 import *; from srdtex import *
from srdtex import replace_append
from PIL import Image,ImageDraw,ImageFont
import numpy as np
SRC='orig/08_batch1/1/program/success_kaiwa_name'
OUT='build/BYNAME/success_kaiwa_name'
FONT='work/fontdl/mpr_full_700.ttf'; FONTL='work/fontdl/mpr_latin_700.ttf'
G=json.load(open('work/names_full.json'))
EN2RU={k:v[0] for k,v in G.items()}
EN2RU.update({'Monotaro':'Монотаро','Monosuke':'Моноске','Monophanie':'Монофани','Monodam':'Монодам','Monokid':'Монокид',
  'Exisal':'Экзисал','Monokubs':'Монокубы','Junko Enoshima (Mukuro)':'Джунко Эношима (Мукуро)',
  'Byakuya Togami (Imposter)':'Бьякуя Тогами (Самозванец)'})
IDX={'000':'Shuichi Saihara','001':'Kaito Momota','002':'Ryoma Hoshi','003':'Rantaro Amami','004':'Gonta Gokuhara','005':'Kokichi Oma',
'006':'Korekiyo Shinguji','007':'K1-B0','008':'Kirumi Tojo','009':'Himiko Yumeno','010':'Maki Harukawa','011':'Tenko Chabashira',
'012':'Tsumugi Shirogane','013':'Angie Yonaga','014':'Miu Iruma','015':'Kaede Akamatsu','020':'Monokuma','021':'Monotaro','022':'Monosuke',
'023':'Monophanie','024':'Monodam','025':'Monokid','026':'Exisal','027':'Monokubs','100':'Makoto Naegi','101':'Kiyotaka Ishimaru',
'102':'Byakuya Togami','103':'Mondo Owada','104':'Leon Kuwata','105':'Hifumi Yamada','106':'Yasuhiro Hagakure','107':'Chihiro Fujisaki',
'108':'Sayaka Maizono','109':'Kyoko Kirigiri','110':'Aoi Asahina','111':'Toko Fukawa','112':'Genocide Jack','113':'Sakura Ogami',
'114':'Celestia Ludenberg','115':'Junko Enoshima','116':'Junko Enoshima (Mukuro)','120':'Hajime Hinata','121':'Nagito Komaeda',
'122':'Byakuya Togami (Imposter)','123':'Gundham Tanaka','124':'Kazuichi Soda','125':'Teruteru Hanamura','126':'Nekomaru Nidai',
'127':'Fuyuhiko Kuzuryu','128':'Akane Owari','129':'Chiaki Nanami','130':'Sonia Nevermind','131':'Hiyoko Saionji','132':'Mahiru Koizumi',
'133':'Mikan Tsumiki','134':'Ibuki Mioda','135':'Peko Pekoyama','136':'Izuru Kamukura','137':'Monomi','138':'Usami'}
SIZE=40; BASE=46; SS=4; MAXW=480
def render(text,W=512,H=64):
    f=ImageFont.truetype(FONT,SIZE*SS)
    big=Image.new('L',(W*SS*2,H*SS),0); d=ImageDraw.Draw(big)
    d.text((10*SS,BASE*SS),text,font=f,fill=255,anchor='ls')
    a=np.array(big); xs=np.where(a.max(0)>0)[0]
    x0,x1=xs.min(),xs.max()+1
    crop=big.crop((x0,0,x1,H*SS))
    w=crop.width/SS
    scale=min(1.0,MAXW/w)
    nw=max(1,int(round(w*scale)))
    crop=crop.resize((nw,H),Image.LANCZOS)
    out=Image.new('RGBA',(W,H),(255,255,255,0))
    alpha=Image.new('L',(W,H),0); alpha.paste(crop,((W-nw)//2,0))
    out.putalpha(alpha); return out
def calibrate():
    global SIZE,BASE
    im=Image.open(glob.glob('work/tex/all/*chara_name_000_US.png')[0]); a=np.array(im)[:,:,3]
    ys,xs=np.where(a>128); print('orig ink',xs.min(),xs.max(),ys.min(),ys.max())
    f=ImageFont.truetype(FONTL,100); bb=f.getbbox('Shuichi Saihara',anchor='ls')
    # match width
    SIZE=round(100*(xs.max()-xs.min())/(bb[2]-bb[0]))
    f=ImageFont.truetype(FONTL,SIZE); bb=f.getbbox('Shuichi Saihara',anchor='ls')
    BASE=int(round(ys.max()-bb[3]))  # baseline so that descender bottoms align (no descenders => bb[3]=0)
    print('SIZE',SIZE,'BASE',BASE,'bbox',bb)
def main():
    calibrate()
    os.makedirs(OUT,exist_ok=True); prev=[]
    for f in sorted(glob.glob(SRC+'/chara_name_*_US.spc')):
        i=f.split('_')[-2]
        if i not in IDX: continue
        ru=EN2RU[IDX[i]]
        spc=spc_read(open(f,'rb').read()); E={e.name:e for e in spc['entries']}
        srd=E['texture.srd'].data; v=E['texture.srdv'].data
        t=textures(srd)[0]
        im=render(ru,t['w'],t['h'])
        srd2,tail=replace_append(srd,len(v),{t['name']:im})
        E['texture.srd'].data=srd2; E['texture.srdv'].append_tail=tail
        open(f'{OUT}/{os.path.basename(f)}','wb').write(spc_write(spc,compress=True))
        prev.append(im)
    S=Image.new('RGBA',(1024,len(prev)//2*64+64),(70,70,90,255))
    for k,im in enumerate(prev): S.alpha_composite(im,((k%2)*512,(k//2)*64))
    S.save('work/names_preview.png'); print('done',len(prev))
if __name__=='__main__': main()
