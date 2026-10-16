"""Сборка установщика DRV3_Rus_Extra_Setup_v<версия>.exe (NSIS) и zip с ним.
python3 tools/build_setup.py <версия> [папка_вывода]
Если есть папка build/ — сначала пересобирает pkg/payload (tools/mkdelta.py), иначе берёт готовый pkg/payload."""
import os, sys, subprocess, shutil, zipfile
VERSION = sys.argv[1] if len(sys.argv) > 1 else '2.1'
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else 'dist'
AUTHORS = os.environ.get('AUTHORS', 'lolik-lolikov')
os.makedirs(OUTDIR, exist_ok=True)
NAME = f'DRV3_Rus_Extra_Setup_v{VERSION}'
OUT = os.path.join(OUTDIR, NAME + '.exe')
if os.path.isdir('build') and os.environ.get('MKDELTA') == '1':
    subprocess.check_call([sys.executable, 'tools/mkdelta.py'])           # -> pkg/payload
else:
    assert os.path.exists('pkg/payload/manifest.txt'), 'нет pkg/payload'
    print('build/ нет — используется готовый pkg/payload')
def crlf(t): return t.replace('\r\n', '\n').replace('\n', '\r\n')
lib = open('installer/cpklib.cs', encoding='utf-8').read()
assert "\n'@" not in lib
ps = open('installer/install.ps1', encoding='utf-8').read()
assert ps.count('#CPKLIB#') == 1
ps = ps.replace('#CPKLIB#', lib.rstrip('\n'))
open('pkg/install.ps1', 'wb').write('﻿'.encode('utf-8') + crlf(ps).encode('utf-8'))
readme = open('installer/README.txt', encoding='utf-8').read().replace('{VERSION}', VERSION).replace('{AUTHORS}', AUTHORS)
open('pkg/readme_utf16.txt', 'wb').write('﻿'.encode('utf-16-le') + crlf(readme).encode('utf-16-le'))
open('pkg/ПРОЧИТАЙ_МЕНЯ.txt', 'wb').write('﻿'.encode('utf-8') + crlf(readme).encode('utf-8'))
shutil.copy('installer/setup.nsi', 'pkg/setup.nsi')
if os.path.exists(OUT): os.remove(OUT)
r = subprocess.run(['makensis', '-V2', f'-DVERSION={VERSION}', f'-DOUTFILE={os.path.abspath(OUT)}', 'setup.nsi'], cwd='pkg', capture_output=True, text=True)
print(r.stdout[-3000:], r.stderr[-3000:])
if r.returncode != 0: sys.exit(1)
z = os.path.join(OUTDIR, NAME + '.zip')
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write(OUT, NAME + '/' + NAME + '.exe')
    zf.write('pkg/ПРОЧИТАЙ_МЕНЯ.txt', NAME + '/ПРОЧИТАЙ_МЕНЯ.txt')
print(OUT, os.path.getsize(OUT) // 1024, 'KB'); print(z, os.path.getsize(z) // 1024, 'KB')
