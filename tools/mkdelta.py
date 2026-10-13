"""Build installer payload: full files + binary deltas, and manifest."""
import os, sys, glob, hashlib, struct, shutil
B = 64
def delta(orig, new):
    idx = {}
    for i in range(0, len(orig) - B + 1, B):
        idx.setdefault(orig[i:i + B], i)
    ops = []; i = 0; add_start = 0; n = len(new)
    while i + B <= n:
        j = idx.get(new[i:i + B])
        if j is None:
            i += 1; continue
        # extend backward
        while i > add_start and j > 0 and new[i - 1] == orig[j - 1]:
            i -= 1; j -= 1
        # extend forward
        L = B
        while i + L < n and j + L < len(orig) and new[i + L] == orig[j + L]:
            # fast compare in chunks
            step = 4096
            if new[i + L:i + L + step] == orig[j + L:j + L + step]:
                L += step; continue
            L += 1
        L = min(L, n - i, len(orig) - j)
        while new[i:i + L] != orig[j:j + L]:
            L -= 1
        if i > add_start:
            ops.append(('A', new[add_start:i]))
        ops.append(('C', j, L))
        i += L; add_start = i
    if add_start < n:
        ops.append(('A', new[add_start:n]))
    out = bytearray(b'DRVP' + struct.pack('<I', 1))
    out += struct.pack('<Q', len(orig)) + hashlib.sha1(orig).digest()
    out += struct.pack('<Q', len(new)) + hashlib.sha1(new).digest()
    for op in ops:
        if op[0] == 'C':
            out += struct.pack('<BQI', 1, op[1], op[2])
        else:
            out += struct.pack('<BI', 2, len(op[1])) + op[1]
    out += b'\0'
    return bytes(out)

def apply(orig, patch):  # for self-test
    p = 8 + 8 + 20 + 8 + 20; out = bytearray()
    while patch[p] != 0:
        t = patch[p]
        if t == 1:
            _, o, L = struct.unpack_from('<BQI', patch, p); out += orig[o:o + L]; p += 13
        else:
            _, L = struct.unpack_from('<BI', patch, p); out += patch[p + 5:p + 5 + L]; p += 5 + L
    return bytes(out)

# файлы, которые ставятся только в режиме ARCHIVE (без основного русификатора):
# основной шрифт с добавленной кириллицей поверх оригинала из Steam
ARCHIVE_ONLY = {'data/win/game_resident/game_resident_US.spc': 'orig/10_vanilla/game_resident/game_resident_US.spc'}

def find_orig(build_rel):
    if build_rel in ARCHIVE_ONLY: return ARCHIVE_ONLY[build_rel]
    name = os.path.basename(build_rel)
    if build_rel.startswith('BYNAME/'):
        sub = build_rel[7:]
        c = glob.glob('orig/08_batch1/1/**/' + sub, recursive=True)
    else:
        c = [p for p in glob.glob('orig/*/' + build_rel) if not p.startswith('orig/00_test')]
    return c[0] if c else None

def main():
    OUT = 'pkg/payload'
    if os.path.exists('pkg'): shutil.rmtree('pkg')
    os.makedirs(OUT)
    man = []; tot_full = tot_patch = 0
    seen_full = {}
    for f in sorted(glob.glob('build/**/*', recursive=True)):
        if os.path.isdir(f) or f.endswith('.txt'): continue
        rel = os.path.relpath(f, 'build').replace(os.sep, '/')
        target = ('BYNAME:' + rel[7:]) if rel.startswith('BYNAME/') else rel
        new = open(f, 'rb').read()
        full = ('wrd_script' in rel) or ('/rsc/text/' in rel) or ('/rsc/font/' in rel)
        o = None if full else find_orig(rel)
        if o is None:
            h = hashlib.sha1(new).hexdigest()
            if h not in seen_full:
                pn = 'full/' + h[:10] + '_' + os.path.basename(rel)
                open(os.path.join(OUT, pn.replace('/', os.sep)) if False else None, 'wb') if False else None
                os.makedirs(os.path.join(OUT, 'full'), exist_ok=True)
                open(os.path.join(OUT, pn), 'wb').write(new); seen_full[h] = pn; tot_full += len(new)
            man.append(('FULL', seen_full[h], target))
        else:
            orig = open(o, 'rb').read()
            d = delta(orig, new)
            assert apply(orig, d) == new, rel
            pn = 'patch/' + rel.replace('/', '__') + '.dpatch'
            os.makedirs(os.path.join(OUT, 'patch'), exist_ok=True)
            open(os.path.join(OUT, pn), 'wb').write(d); tot_patch += len(d)
            man.append(('PATCHA' if rel in ARCHIVE_ONLY else 'PATCH', pn, target))
            print(f'{rel}: {len(new)//1024} KB -> patch {len(d)//1024} KB')
    with open(os.path.join(OUT, 'manifest.txt'), 'w', encoding='utf-8', newline='\r\n') as fh:
        for m in man: fh.write('\t'.join(m) + '\n')
    print('full', tot_full // 1024, 'KB; patches', tot_patch // 1024, 'KB; entries', len(man))
if __name__ == '__main__':
    main()
