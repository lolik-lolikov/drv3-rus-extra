#!/usr/bin/env python3
"""Встраивание файлов в CPK (тот же алгоритм, что в install.ps1) — для пошаговой проверки на реальной игре.
  cpkpatch.py apply  <game_dir> <payload_dir> <workdir> <step>   step: reloc | reloc-font | text | font | all | <regex>
  (reloc — перенести оригинальные файлы в конец архива без изменений: проверка самого способа)
  cpkpatch.py restore <game_dir> <workdir>
"""
import sys, os, re, struct, hashlib, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpk import open_cpk

SZ = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 8, 7: 8}

def drvp_apply(orig, p):
    assert p[:4] == b'DRVP'
    osz = struct.unpack_from('<q', p, 8)[0]; osha = p[16:36]
    nsz = struct.unpack_from('<q', p, 36)[0]; nsha = p[44:64]
    if len(orig) != osz or hashlib.sha1(orig).digest() != osha: return None
    out = bytearray(); pos = 64
    while p[pos] != 0:
        if p[pos] == 1:
            off, ln = struct.unpack_from('<QI', p, pos + 1); out += orig[off:off + ln]; pos += 13
        else:
            ln = struct.unpack_from('<I', p, pos + 1)[0]; out += p[pos + 5:pos + 5 + ln]; pos += 5 + ln
    assert len(out) == nsz and hashlib.sha1(out).digest() == nsha
    return bytes(out)

def put(f, base, cell, v):
    p, ty = cell; n = SZ[ty]
    assert 0 <= v < (1 << (8 * n)), (v, n)
    f.seek(base + p); f.write(v.to_bytes(n, 'big'))

def entries(c):
    t = c['toc']; res = {}
    for r, pos in zip(t.rows, t.cellpos):
        res[(r['DirName'] + '/' + r['FileName']).lower()] = (r, pos)
    return res

def resolve(target, allents):
    """-> list of (cpkname, path_lower)"""
    out = []
    if target.startswith('BYNAME:'):
        sub = target[7:].lower(); name = sub.split('/')[-1]; parent = '/'.join(sub.split('/')[:-1])
        for cn, ents in allents.items():
            for p in ents:
                d, n = p.rsplit('/', 1)
                if n == name and (not parent or d == parent or d.endswith('/' + parent)): out.append((cn, p))
    else:
        p = target.lower().replace('\\', '/')
        if p.startswith('data/win/'): p = p[9:]
        for cn, ents in allents.items():
            if p in ents: out.append((cn, p))
    return out

def apply(game, payload, work, step):
    win = os.path.join(game, 'data', 'win')
    names = ['partition_data_win_us.cpk', 'partition_resident_win.cpk']
    cpks = {n: open_cpk(os.path.join(win, n)) for n in names}
    allents = {n: entries(c) for n, c in cpks.items()}
    man = [l.rstrip('\r\n').split('\t') for l in open(os.path.join(payload, 'manifest.txt'), encoding='utf-8') if l.strip()]
    plan = {n: [] for n in names}
    for kind, pf, target in man:
        if step in ('text', 'reloc') and kind == 'PATCHA': continue
        if step == 'reloc-font' and kind != 'PATCHA': continue
        if step == 'font' and kind != 'PATCHA': continue
        if step not in ('text', 'font', 'all', 'reloc', 'reloc-font') and not re.search(step, target): continue
        for cn, p in resolve(target, allents):
            plan[cn].append((kind, os.path.join(payload, pf), p))
    os.makedirs(work, exist_ok=True)
    state = {}
    for cn, items in plan.items():
        if not items: continue
        c = cpks[cn]; H = c['H']; t = c['toc']; hdr = c['hdr']
        path = os.path.join(win, cn)
        f = open(path, 'r+b')
        origlen = os.path.getsize(path)
        co = H['ContentOffset']; f.seek(0); head = f.read(co)
        open(os.path.join(work, cn + '.head'), 'wb').write(head)
        base_off = min(co, H['TocOffset'])
        A = H['Align']; al = lambda v: (v + A - 1) // A * A
        pos = al(origlen); delta = 0; staged = []; sumsize = sum(r['FileSize'] for r in t.rows)
        for kind, pf, p in items:
            r, cells = allents[cn][p]
            f.seek(base_off + r['FileOffset']); orig = f.read(r['FileSize'])
            pb = open(pf, 'rb').read()
            data = orig if step.startswith('reloc') else (pb if kind == 'FULL' else drvp_apply(orig, pb))
            if data is None: print('SKIP mismatch', p); continue
            f.seek(pos); f.write(data)
            staged.append((cells, pos - base_off, len(data), p))
            delta += len(data) - r['FileSize']; pos = al(pos + len(data))
        minimal = os.environ.get('CPK_MINIMAL') == '1'
        et_old, et_sz = H['EtocOffset'], H['EtocSize']
        if not minimal:
            f.seek(et_old); et = f.read(et_sz); f.seek(pos); f.write(et); new_et = pos
        f.flush(); os.fsync(f.fileno())
        tb = t.base
        for cells, off, ln, p in staged:
            put(f, tb, cells['FileSize'], ln); put(f, tb, cells['ExtractSize'], ln); put(f, tb, cells['FileOffset'], off)
        hb = hdr.base; hc = hdr.cellpos[0]
        if not minimal:
            put(f, hb, hc['EtocOffset'], new_et)
            if H['ContentSize'] == et_old - co: put(f, hb, hc['ContentSize'], new_et - co)
            for k in ('EnabledPackedSize', 'EnabledDataSize'):
                if H[k] == 2 * sumsize: put(f, hb, hc[k], 2 * (sumsize + delta))
        f.flush(); os.fsync(f.fileno()); f.close()
        f = open(path, 'rb'); newhead = f.read(co); f.close()
        state[cn] = {'origlen': origlen, 'sha': hashlib.sha1(newhead).hexdigest(), 'n': len(staged)}
        print(cn, 'staged', len(staged), 'newlen', os.path.getsize(path))
        # проверка
        c2 = open_cpk(path); e2 = entries(c2)
        for cells, off, ln, p in staged:
            r = e2[p][0]; assert r['FileOffset'] == off and r['FileSize'] == ln
    json.dump(state, open(os.path.join(work, 'state.json'), 'w'))

def restore(game, work):
    win = os.path.join(game, 'data', 'win')
    st = json.load(open(os.path.join(work, 'state.json')))
    for cn, s in st.items():
        path = os.path.join(win, cn); head = open(os.path.join(work, cn + '.head'), 'rb').read()
        with open(path, 'r+b') as f:
            cur = f.read(len(head))
            if hashlib.sha1(cur).hexdigest() != s['sha']: print(cn, 'changed, skip'); continue
            f.seek(0); f.write(head); f.truncate(s['origlen']); f.flush(); os.fsync(f.fileno())
        print(cn, 'restored', os.path.getsize(path))
    os.remove(os.path.join(work, 'state.json'))

if __name__ == '__main__':
    if sys.argv[1] == 'apply': apply(*sys.argv[2:6])
    else: restore(*sys.argv[2:4])
