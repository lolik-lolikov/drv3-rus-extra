import glob,os
out=[]
for f in sorted(glob.glob('tools/*.py'))+['work/tm_new.tsv','work/STYLE_rsc.md','tools/c/spccmp.c','installer/install.ps1','installer/README.txt','installer/setup.nsi','work/names_full.json']+sorted(glob.glob('work/tr/*.tsv'))+['work/rtm.tsv']+sorted(glob.glob('work/rtr/*.tsv')):
    out.append('=====FILE '+f+'\n'+open(f).read())
open('work/drv3_backup.txt','w').write('\n'.join(out))
print(len(out), os.path.getsize('work/drv3_backup.txt'))
