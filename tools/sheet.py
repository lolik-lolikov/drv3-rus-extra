import sys,json,os
from PIL import Image,ImageDraw
ix=json.load(open('work/tex/index.json'))
def sheet(arch,out,maxw=1400,cell=170):
    items=[x for x in ix if x[0].endswith(arch) and x[-1]!='ERR']
    ims=[]
    for k,x in enumerate(items):
        im=Image.open(x[-1]).convert('RGBA'); im.thumbnail((cell,cell))
        ims.append((k,x[2],im))
    cols=maxw//(cell+10); rows=(len(ims)+cols-1)//cols
    S=Image.new('RGBA',(cols*(cell+10),rows*(cell+24)),(70,70,90,255)); d=ImageDraw.Draw(S)
    for n,(k,name,im) in enumerate(ims):
        x=(n%cols)*(cell+10); y=(n//cols)*(cell+24)
        S.alpha_composite(im,(x,y+14)); d.text((x,y),f'{k}:{name[:34]}',fill=(255,255,0,255))
    S.save(out); return len(ims)
if __name__=='__main__':
    print(sheet(sys.argv[1],sys.argv[2]))
