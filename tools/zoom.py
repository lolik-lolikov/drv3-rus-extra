import sys,glob
from PIL import Image,ImageDraw
sys.path.insert(0,'tools'); from texedit import ink_bbox,dominant_color
S='scratch/'
pats=sys.argv[2:]; ims=[]
for p in pats:
    fs=sorted(glob.glob('work/tex/all/*'+p+'*'))
    if not fs: print('none',p); continue
    im=Image.open(fs[0]).convert('RGBA'); b=ink_bbox(im)
    print(p,im.size,'bbox',b,'dom',dominant_color(im))
    c=im.crop((max(0,b[0]-4),max(0,b[1]-4),min(im.width,b[2]+4),min(im.height,b[3]+4)))
    s=min(3,700/c.width,200/c.height); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s))),Image.NEAREST)
    ims.append(c)
W=max(i.width for i in ims); H=sum(i.height+6 for i in ims)
C=Image.new('RGBA',(W,H),(110,110,130,255)); y=0
for i in ims: C.alpha_composite(i,(0,y)); y+=i.height+6
C.save(S+sys.argv[1]+'.png')
