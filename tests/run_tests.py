"""Проверка install.ps1 на синтетической копии игры (tests/mktest.py). Нужен pwsh.
python3 tests/run_tests.py TESTDIR"""
import os, sys, json, hashlib, shutil, subprocess
T = sys.argv[1]
K = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib = open(os.path.join(K, 'installer/cpklib.cs'), encoding='utf-8').read()
ps = open(os.path.join(K, 'installer/install.ps1'), encoding='utf-8').read().replace('#CPKLIB#', lib.rstrip('\n'))
PS = os.path.join(T, 'install.ps1'); open(PS, 'w', encoding='utf-8').write(ps)
OLD = '/tmp/claude-0/old/installer/install.ps1'
E = json.load(open(os.path.join(T, 'expect.json')))
PAY = os.path.join(T, 'payload')
US, RES = 'partition_data_win_us.cpk', 'partition_resident_win.cpk'
fails = []
def snap(g):
    out = {}
    for r, ds, fs in os.walk(g):
        for f in fs:
            p = os.path.join(r, f); out[os.path.relpath(p, g)] = hashlib.sha1(open(p, 'rb').read()).hexdigest()
        for d in ds:
            p = os.path.join(r, d)
            if not os.listdir(p): out[os.path.relpath(p, g) + '/'] = 'emptydir'
    return out
def run(g, *a, script=PS):
    log = os.path.join(T, 'log.txt')
    if os.path.exists(log): os.remove(log)
    r = subprocess.run(['pwsh', '-NoProfile', '-File', script, '-GamePath', g, '-Payload', PAY, '-NoPause', '-Log', log] + list(a), capture_output=True, text=True)
    txt = open(log, 'rb').read().decode('utf-16') if os.path.exists(log) else ''
    if r.stderr.strip(): txt += '\nSTDERR: ' + r.stderr
    return r.returncode, txt
def check(name, cond, info=''):
    print(('  OK   ' if cond else '  FAIL ') + name + ('' if cond else '  ' + str(info)[:1500]))
    if not cond: fails.append(name)
def fresh(src, name):
    g = os.path.join(T, name)
    if os.path.exists(g): shutil.rmtree(g)
    shutil.copytree(os.path.join(T, src), g); return g
W = lambda g, *p: os.path.join(g, 'data', 'win', *p)
def check_unpacked(g, font=True):
    bad = []
    for part in ('us', 'res'):
        for p, h in E[part].items():
            q = W(g, *p.split('/'))
            want = E['translated'].get(p, h)
            if p == 'game_resident/game_resident_US.spc' and not font: want = h
            if not os.path.exists(q): bad.append('missing ' + p)
            elif hashlib.sha1(open(q, 'rb').read()).hexdigest() != want: bad.append('content ' + p)
    return bad

print('A. чистая игра: установка и удаление')
g = fresh('clean', 'A'); s0 = snap(g)
rc, log = run(g)
check('A install rc=0', rc == 0, log)
check('A archives moved', not os.path.exists(W(g, US)) and not os.path.exists(W(g, RES)) and os.path.exists(os.path.join(g, '_rus_extra_backup', 'cpk', US)), log)
b = check_unpacked(g); check('A files unpacked+translated', not b, b)
check('A main cpk untouched', os.path.exists(W(g, 'partition_data_win.cpk')))
sA = snap(g)
rc, log = run(g, '-Uninstall')
check('A uninstall rc=0', rc == 0, log)
s1 = snap(g); check('A restored exactly', s1 == s0, set(s1.items()) ^ set(s0.items()))

print('D. повторная установка (обновление перевода без распаковки)')
g = fresh('clean', 'D'); s0 = snap(g)
run(g); rc, log = run(g)
check('D reinstall rc=0', rc == 0, log)
check('D no re-unpack', 'обновляется только перевод' in log and 'Распаковка файлов' not in log, log)
b = check_unpacked(g); check('D state ok', not b, b)
rc, log = run(g, '-Uninstall'); check('D restored exactly', snap(g) == s0, log)

print('E. Steam вернул архивы (проверка целостности) -> установка заново')
g = fresh('clean', 'E'); s0 = snap(g)
run(g)
shutil.copy(os.path.join(T, 'clean', 'data', 'win', US), W(g, US)); shutil.copy(os.path.join(T, 'clean', 'data', 'win', RES), W(g, RES))
rc, log = run(g)
check('E reinstall rc=0', rc == 0, log)
check('E re-unpacked', 'Распаковка файлов' in log, log)
b = check_unpacked(g); check('E state ok', not b, b)
rc, log = run(g, '-Uninstall'); check('E restored exactly', snap(g) == s0, set(snap(g).items()) ^ set(s0.items()))

print('K. Steam вернул архивы -> удаление')
g = fresh('clean', 'K'); s0 = snap(g)
run(g)
shutil.copy(os.path.join(T, 'clean', 'data', 'win', US), W(g, US)); shutil.copy(os.path.join(T, 'clean', 'data', 'win', RES), W(g, RES))
rc, log = run(g, '-Uninstall'); check('K uninstall rc=0', rc == 0, log); check('K restored exactly', snap(g) == s0, set(snap(g).items()) ^ set(s0.items()))

print('F. мало места')
g = fresh('clean', 'F'); s0 = snap(g)
rc, log = run(g, '-TestFreeSpace', '1000')
check('F rc=8', rc == 8, log); check('F message', 'недостаточно места' in log, log); check('F untouched', snap(g) == s0)

print('G. сбой посреди распаковки -> откат')
g = fresh('clean', 'G'); s0 = snap(g)
rc, log = run(g, '-TestFailAt', '30')
check('G rc=7', rc == 7, log); check('G untouched', snap(g) == s0, set(snap(g).items()) ^ set(s0.items()))

print('H. в data\\win уже лежат посторонние файлы из архивов')
g = fresh('clean', 'H')
for p in ['flash/misc/carddeath_box_US.spc', 'model/m00/file_00_US.spc']:
    q = W(g, *p.split('/')); os.makedirs(os.path.dirname(q), exist_ok=True); open(q, 'wb').write(b'leftover ' + p.encode())
s0 = snap(g)
rc, log = run(g)
check('H install rc=0', rc == 0, log)
b = check_unpacked(g); check('H state ok', not b, b)
rc, log = run(g, '-Uninstall'); check('H restored exactly (leftovers back)', snap(g) == s0, set(snap(g).items()) ^ set(s0.items()))

print('B. основной русификатор (архивы удалены)')
g = fresh('mainrus', 'B'); s0 = snap(g)
rc, log = run(g)
check('B install rc=0', rc == 0, log)
check('B detected main', 'Найден основной русификатор' in log, log)
check('B font untouched', open(W(g, 'game_resident', 'game_resident_US.spc'), 'rb').read().startswith(b'RUSFONT'))
bad = [p for p, h in E['translated'].items() if not p.startswith('game_resident') and hashlib.sha1(open(W(g, *p.split('/')), 'rb').read()).hexdigest() != h]
check('B translated (кроме изменённого основным: casino_coin)', bad == ['flash/casino/casino_coin_US.spc'] or bad == [], bad)
rc, log2 = run(g)
check('B reinstall rc=0', rc == 0, log2)
rc, log = run(g, '-Uninstall'); check('B restored exactly', snap(g) == s0, set(snap(g).items()) ^ set(s0.items()))

print('C. основной русификатор, архивы не удалены')
g = fresh('mainrus', 'C')
shutil.copy(os.path.join(T, 'clean', 'data', 'win', US), W(g, US)); shutil.copy(os.path.join(T, 'clean', 'data', 'win', RES), W(g, RES))
s0 = snap(g)
rc, log = run(g)
check('C install rc=0', rc == 0, log)
check('C archives moved', not os.path.exists(W(g, US)) and not os.path.exists(W(g, RES)), log)
check('C no unpack', 'Распаковка файлов' not in log, log)
check('C font untouched', open(W(g, 'game_resident', 'game_resident_US.spc'), 'rb').read().startswith(b'RUSFONT'))
bad = [p for p, h in E['translated'].items() if not p.startswith('game_resident') and hashlib.sha1(open(W(g, *p.split('/')), 'rb').read()).hexdigest() != h]
check('C all translated (fallback to archive original)', bad == [], bad)
rc, log = run(g, '-Uninstall'); check('C restored exactly', snap(g) == s0, set(snap(g).items()) ^ set(s0.items()))

if os.path.exists(OLD):
    print('I. обновление со старой версии (журнал 1.x/2.0, режим LOOSE)')
    g = fresh('mainrus', 'I')
    shutil.copy(os.path.join(T, 'clean', 'data', 'win', US), W(g, US)); shutil.copy(os.path.join(T, 'clean', 'data', 'win', RES), W(g, RES))
    s0 = snap(g)
    rc, log = run(g, script=OLD); check('I old install rc=0', rc == 0, log)
    rc, log = run(g); check('I new install over old rc=0', rc == 0, log)
    check('I old undone first', 'будет удалена и установлена заново' in log, log)
    rc, log = run(g, '-Uninstall'); check('I restored exactly', snap(g) == s0, set(snap(g).items()) ^ set(s0.items()))

print('L. удаление без установки')
g = fresh('clean', 'L'); rc, log = run(g, '-Uninstall'); check('L rc=1', rc == 1, log)

print('\nИТОГ:', 'всё прошло' if not fails else 'ОШИБКИ: ' + ', '.join(fails))
sys.exit(1 if fails else 0)
