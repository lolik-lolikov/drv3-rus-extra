#!/usr/bin/env python3
"""Тестовый сборщик CPK со структурой как у partition_data_win_us.cpk (для проверки установщика)."""
import struct, sys, os

SZ = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 8, 7: 8, 0xA: 4, 0xB: 8}
FM = {0: 'B', 2: 'H', 4: 'I', 6: 'Q'}

def utf(name, cols, rows):
    """cols: [(name, storage, type, const)], rows: [dict]"""
    strs = bytearray(b'<NULL>\0'); sidx = {'<NULL>': 0}
    def S(s):
        if s not in sidx:
            sidx[s] = len(strs); strs.extend(s.encode() + b'\0')
        return sidx[s]
    tname = S(name)
    data = bytearray()
    def enc(ty, v):
        if ty == 0xA: return struct.pack('>I', S(v))
        if ty == 0xB: return struct.pack('>II', 0, 0)
        return struct.pack('>' + FM[ty], v)
    coldef = bytearray()
    for cn, st, ty, cv in cols:
        coldef += bytes([st | ty]) + struct.pack('>I', S(cn))
        if st == 0x30: coldef += enc(ty, cv)
    rowlen = sum(SZ[ty] for cn, st, ty, cv in cols if st == 0x50)
    rowb = bytearray()
    for r in rows:
        for cn, st, ty, cv in cols:
            if st == 0x50: rowb += enc(ty, r[cn])
    hdr_len = 32
    rows_off = hdr_len + len(coldef)
    str_off = rows_off + len(rowb)
    data_off = str_off + len(strs)
    body = coldef + rowb + strs + data
    total = 32 + len(body)
    pad = (-total) % 8
    head = b'@UTF' + struct.pack('>IIIIIHHI', total - 8 + pad, rows_off - 8, str_off - 8, data_off - 8, tname,
                                 len(cols), rowlen, len(rows))
    return head + body + b'\0' * pad

def packet(magic, u):
    return magic + struct.pack('<I', 0xff) + struct.pack('<Q', len(u)) + u

def align(n, a=2048): return (n + a - 1) // a * a

def build(out, files):
    """files: [(dir, name, bytes)] — уже отсортированы"""
    A = 2048; TOC = 2048
    toccols = [('DirName', 0x50, 0xA, None), ('FileName', 0x50, 0xA, None), ('FileSize', 0x50, 4, None),
               ('ExtractSize', 0x50, 4, None), ('FileOffset', 0x50, 6, None), ('ID', 0x50, 4, None),
               ('UserString', 0x30, 0xA, '<NULL>')]
    # предварительный TOC для размера
    def mk_toc(offs):
        rows = [{'DirName': d, 'FileName': n, 'FileSize': len(b), 'ExtractSize': len(b), 'FileOffset': o, 'ID': i}
                for i, ((d, n, b), o) in enumerate(zip(files, offs))]
        return packet(b'TOC ', utf('CpkTocInfo', toccols, rows))
    tocp = mk_toc([0] * len(files))
    content = align(TOC + len(tocp))
    offs = []; pos = content
    for d, n, b in files:
        offs.append(pos - TOC); pos = align(pos + len(b))
    tocp = mk_toc(offs)
    etoc_off = pos
    etcols = [('UpdateDateTime', 0x50, 6, None), ('LocalDir', 0x50, 0xA, None)]
    etrows = [{'UpdateDateTime': 1, 'LocalDir': d} for d, n, b in files] + [{'UpdateDateTime': 1, 'LocalDir': ''}]
    etp = packet(b'ETOC', utf('CpkEtocInfo', etcols, etrows))
    s = sum(len(b) for _, _, b in files)
    hcols = [('UpdateDateTime', 0x50, 6, None), ('FileSize', 0x10, 6, None), ('ContentOffset', 0x50, 6, None),
             ('ContentSize', 0x50, 6, None), ('TocOffset', 0x50, 6, None), ('TocSize', 0x50, 6, None),
             ('TocCrc', 0x10, 4, None), ('EtocOffset', 0x50, 6, None), ('EtocSize', 0x50, 6, None),
             ('ItocOffset', 0x10, 6, None), ('GtocOffset', 0x10, 6, None),
             ('EnabledPackedSize', 0x50, 6, None), ('EnabledDataSize', 0x50, 6, None),
             ('Files', 0x50, 4, None), ('Version', 0x50, 2, None), ('Align', 0x50, 2, None),
             ('Sorted', 0x50, 2, None), ('CpkMode', 0x50, 4, None), ('Tvers', 0x50, 0xA, None),
             ('CrcTable', 0x50, 0xB, None)]
    H = {'UpdateDateTime': 1, 'ContentOffset': content, 'ContentSize': etoc_off - content, 'TocOffset': TOC,
         'TocSize': len(tocp), 'EtocOffset': etoc_off, 'EtocSize': len(etp), 'EnabledPackedSize': 2 * s,
         'EnabledDataSize': 2 * s, 'Files': len(files), 'Version': 7, 'Align': A, 'Sorted': 1, 'CpkMode': 1,
         'Tvers': 'CPKMC2.49.32, DLL3.24.00', 'CrcTable': None}
    hp = packet(b'CPK ', utf('CpkHeader', hcols, [H]))
    assert len(hp) <= TOC
    with open(out, 'wb') as f:
        f.write(hp); f.seek(TOC); f.write(tocp)
        for (d, n, b), o in zip(files, offs):
            f.seek(o + TOC); f.write(b)
        f.seek(etoc_off); f.write(etp)

if __name__ == '__main__':
    # argv: out.cpk listfile(dir/name \t source-path)
    files = []
    for l in open(sys.argv[2], encoding='utf-8'):
        p, src = l.rstrip('\n').split('\t')
        d, n = p.rsplit('/', 1)
        files.append((d, n, open(src, 'rb').read() if src != '-' else os.urandom(3000 + len(files) * 37)))
    files.sort(key=lambda x: (x[0], x[1]))
    build(sys.argv[1], files)
