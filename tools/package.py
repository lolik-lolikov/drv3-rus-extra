"""Create distributable zip: installer + payload."""
import os,sys,zipfile,glob
VERSION=sys.argv[1] if len(sys.argv)>1 else 'test'
MODE=os.environ.get('MODE','all')  # all | core | effects
OUT=sys.argv[2] if len(sys.argv)>2 else f'dist/DRV3_rus_extra_{VERSION}.zip'
AUTHORS=os.environ.get('AUTHORS','Лев (и Claude)')
def crlf(t): return t.replace('\r\n','\n').replace('\n','\r\n')
bat_i='@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\\install.ps1"\r\n'
bat_u='@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\\install.ps1" -Uninstall\r\n'
ps=open('installer/install.ps1',encoding='utf-8').read()
readme=open('installer/README.txt',encoding='utf-8').read().replace('{VERSION}',VERSION).replace('{AUTHORS}',AUTHORS)
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('Установить русификатор.bat',bat_i)
    z.writestr('Удалить русификатор.bat',bat_u)
    z.writestr('installer/install.ps1','﻿'.encode('utf-8')+crlf(ps).encode('utf-8'))
    z.writestr('ПРОЧИТАЙ_МЕНЯ.txt','﻿'.encode('utf-8')+crlf(readme).encode('utf-8'))
    n=0
    for f in sorted(glob.glob('build/**/*',recursive=True)):
        if os.path.isdir(f) or f.endswith('.txt'): continue
        is_eff=os.path.basename(f).startswith('effect_0')
        if MODE=='core' and is_eff: continue
        if MODE=='effects' and not is_eff: continue
        is_cas=any(k in f for k in ('/casino/','/slot/','/machine/','slot_machine'))
        if MODE=='p1' and (is_eff or is_cas): continue
        if MODE=='p2' and not is_cas: continue
        rel=os.path.relpath(f,'build')
        z.write(f,'installer/files/'+rel.replace(os.sep,'/')); n+=1
print(OUT,n,'files',os.path.getsize(OUT)//1024,'KB')
