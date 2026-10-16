import sys;sys.path.insert(0,'tools')
from sheet import sheet
from PIL import Image,ImageDraw
S='scratch/'
def combo(grp,out,cell=170):
    ims=[]
    import sheet as sh
    for a in grp:
        try: sh.sheet('/'+a+'.spc',S+'/tmp_x.png',cell=cell); ims.append((a,Image.open(S+'/tmp_x.png').copy()))
        except Exception as ex: print('skip',a,ex)
    H=sum(i.height+20 for _,i in ims); W=max(i.width for _,i in ims)
    C=Image.new('RGBA',(W,H),(30,30,30,255)); y=0; d=ImageDraw.Draw(C)
    for a,i in ims: d.text((0,y),'### '+a,fill=(0,255,0,255)); C.alpha_composite(i,(0,y+12)); y+=i.height+20
    C.save(out); print(out,C.size)
if __name__=='__main__':
    combo(sys.argv[2:],S+'/'+sys.argv[1]+'.png',cell=int(__import__('os').environ.get('CELL','170')))
