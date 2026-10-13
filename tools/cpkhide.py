#!/usr/bin/env python3
"""Способ «скрыть файлы из оглавления CPK»: строки переводимых файлов удаляются из TOC (и ETOC),
а сами файлы кладутся рядом распакованными (data/win/<путь>). Размер архива и смещения не меняются.
  cpkhide.py apply   <game_dir> <payload_dir> <workdir> <step>    step: text | font | all | orig-text
  cpkhide.py restore <game_dir> <workdir>
"""
import sys, os, struct, hashlib, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpk import open_cpk
from cpkpatch import drvp_apply, entries, resolve, put

def rows_rewrite(f, utf, keep_idx):
    """переписать область строк таблицы @UTF, оставив только keep_idx; число строк — в заголовке"""
    raw = utf.raw
    rows = b''.join(raw[utf.rows_off + i * utf.rowlen: utf.rows_off + (i + 1) * utf.rowlen] for i in keep_idx)
    old_len = utf.nrows * utf.rowlen
    rows += b'\0' * (old_len - len(rows))
    f.seek(utf.base + utf.rows_off); f.write(rows)
    f.seek(utf.base + 28); f.write(struct.pack('>I', len(keep_idx)))

def apply(game, payload, work, step):
    win = os.path.join(game, 'data', 'win')
    names = ['partition_data_win_us.cpk', 'partition_resident_win.cpk']
    cpks = {n: open_cpk(os.path.join(win, n)) for n in names}
    allents = {n: entries(c) for n, c in cpks.items()}
    man = [l.rstrip('\r\n').split('\t') for l in open(os.path.join(payload, 'manifest.txt'), encoding='utf-8') if l.strip()]
    plan = {n: [] for n in names}
    for kind, pf, target in man:
        if step in ('text', 'orig-text') and kind == 'PATCHA': continue
        if step == 'font' and kind != 'PATCHA': continue
        for cn, p in resolve(target, allents):
            plan[cn].append((kind, os.path.join(payload, pf), p))
    os.makedirs(work, exist_ok=True)
    state = {}
    for cn, items in plan.items():
        if not items: continue
        c = cpks[cn]; H = c['H']; t = c['toc']; hdr = c['hdr']; et = c.get('EtocOffset')
        path = os.path.join(win, cn)
        f = open(path, 'r+b')
        co = H['ContentOffset']; f.seek(0); open(os.path.join(work, cn + '.head'), 'wb').write(f.read(co))
        if et is not None:
            f.seek(H['EtocOffset']); open(os.path.join(work, cn + '.etoc'), 'wb').write(f.read(H['EtocSize']))
        base_off = min(co, H['TocOffset'])
        hide = set()
        for kind, pf, p in items:
            r, cells = allents[cn][p]
            f.seek(base_off + r['FileOffset']); orig = f.read(r['FileSize'])
            pb = open(pf, 'rb').read()
            if step == 'orig-text': data = orig
            else: data = pb if kind == 'FULL' else drvp_apply(orig, pb)
            if data is None: print('SKIP mismatch', p); continue
            real = r['DirName'] + '/' + r['FileName']
            out = os.path.join(win, *real.split('/'))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'wb').write(data)
            hide.add(p)
        idx = [i for i, r in enumerate(t.rows) if (r['DirName'] + '/' + r['FileName']).lower() not in hide]
        rows_rewrite(f, t, idx)
        if et is not None and et.nrows == t.nrows + 1:
            rows_rewrite(f, et, idx + [t.nrows])
        hc = hdr.cellpos[0]
        put(f, hdr.base, hc['Files'], len(idx))
        s_all = sum(r['FileSize'] for r in t.rows); s_keep = sum(t.rows[i]['FileSize'] for i in idx)
        for k in ('EnabledPackedSize', 'EnabledDataSize'):
            if H.get(k) == 2 * s_all: put(f, hdr.base, hc[k], 2 * s_keep)
        f.flush(); os.fsync(f.fileno()); f.close()
        f = open(path, 'rb'); newhead = f.read(co); f.close()
        state[cn] = {'sha': hashlib.sha1(newhead).hexdigest(), 'hidden': sorted(hide)}
        c2 = open_cpk(path)
        assert c2['toc'].nrows == len(idx) and not any((r['DirName'] + '/' + r['FileName']).lower() in hide for r in c2['toc'].rows)
        print(cn, 'hidden', len(hide), 'rows left', len(idx))
    json.dump(state, open(os.path.join(work, 'hide_state.json'), 'w'))

def restore(game, work):
    win = os.path.join(game, 'data', 'win')
    st = json.load(open(os.path.join(work, 'hide_state.json')))
    for cn, s in st.items():
        path = os.path.join(win, cn); head = open(os.path.join(work, cn + '.head'), 'rb').read()
        with open(path, 'r+b') as f:
            if hashlib.sha1(f.read(len(head))).hexdigest() != s['sha']: print(cn, 'changed, skip'); continue
            f.seek(0); f.write(head); f.flush(); os.fsync(f.fileno())
        etp = os.path.join(work, cn + '.etoc')
        if os.path.exists(etp):
            c = open_cpk(path); off = c['H']['EtocOffset']; c['f'].close()
            with open(path, 'r+b') as f:
                f.seek(off); f.write(open(etp, 'rb').read()); f.flush(); os.fsync(f.fileno())
        print(cn, 'restored')

if __name__ == '__main__':
    if sys.argv[1] == 'apply': apply(*sys.argv[2:6])
    else: restore(*sys.argv[2:4])
