#!/usr/bin/env python3
"""Минимальный разбор CRI CPK: заголовок, TOC, ETOC; позиции ячеек для правки на месте."""
import struct, sys, json

def decrypt(b):
    m, t = 0x655f, 0x4115
    out = bytearray(len(b))
    for i, c in enumerate(b):
        out[i] = c ^ (m & 0xff)
        m = (m * t) & 0xffffffff
    return bytes(out)

TFMT = {0: 'B', 1: 'b', 2: 'H', 3: 'h', 4: 'I', 5: 'i', 6: 'Q', 7: 'q', 8: 'f', 9: 'd', 0xA: 'I', 0xB: 'II'}

class UTF:
    """utf: bytes начиная с '@UTF' (уже расшифрованные). base: смещение '@UTF' в файле."""
    def __init__(self, utf, base=0, encrypted=False):
        self.raw = utf; self.base = base; self.encrypted = encrypted
        assert utf[:4] == b'@UTF', utf[:4]
        size, rows_off, str_off, data_off, name_off, ncol, rowlen, nrows = struct.unpack('>IIIIIHHI', utf[4:32])
        rows_off &= 0xffff
        self.rows_off = rows_off + 8; self.str_off = str_off + 8; self.data_off = data_off + 8
        self.nrows = nrows; self.rowlen = rowlen
        self.name = self.s(name_off)
        self.cols = []
        p = 32
        for _ in range(ncol):
            flags = utf[p]; p += 1
            nm = self.s(struct.unpack('>I', utf[p:p+4])[0]); p += 4
            st, ty = flags & 0xf0, flags & 0x0f
            col = {'name': nm, 'st': st, 'ty': ty}
            if st in (0x30, 0x70):
                v, n = self.val(p, ty); col['const'] = v; p += n
            self.cols.append(col)
        # позиции ячеек
        self.rows = []; self.cellpos = []
        for r in range(nrows):
            p = self.rows_off + r * rowlen
            row = {}; pos = {}
            for c in self.cols:
                if c['st'] == 0x50:
                    v, n = self.val(p, c['ty']); row[c['name']] = v; pos[c['name']] = (p, c['ty']); p += n
                elif 'const' in c:
                    row[c['name']] = c['const']
                else:
                    row[c['name']] = None
            self.rows.append(row); self.cellpos.append(pos)

    def s(self, off):
        a = self.str_off + off
        e = self.raw.index(b'\0', a)
        return self.raw[a:e].decode('utf-8', 'replace')

    def val(self, p, ty):
        f = TFMT[ty]
        n = struct.calcsize('>' + f)
        v = struct.unpack('>' + f, self.raw[p:p+n])
        if ty == 0xA: return self.s(v[0]), n
        if ty == 0xB: return (v[0], v[1]), n
        return v[0], n

def read_packet(f, off):
    f.seek(off)
    hdr = f.read(16)
    magic = hdr[:4]
    size = struct.unpack('<Q', hdr[8:16])[0]
    utf = f.read(size)
    enc = utf[:4] != b'@UTF'
    if enc: utf = decrypt(utf)
    return magic, hdr, UTF(utf, off + 16, enc), size

def open_cpk(path):
    f = open(path, 'rb')
    magic, hdr, h, size = read_packet(f, 0)
    assert magic == b'CPK ', magic
    H = h.rows[0]
    res = {'f': f, 'hdr': h, 'H': H, 'hdrsize': size}
    if H.get('TocOffset'):
        m, _, t, ts = read_packet(f, H['TocOffset'])
        assert m == b'TOC ', m
        res['toc'] = t; res['tocsize'] = ts
    for k, mg in (('EtocOffset', b'ETOC'), ('ItocOffset', b'ITOC'), ('GtocOffset', b'GTOC')):
        if H.get(k):
            m, _, t, ts = read_packet(f, H[k])
            res[k] = t
    return res

if __name__ == '__main__':
    c = open_cpk(sys.argv[1])
    h = c['hdr']
    print('HEADER enc=%s' % h.encrypted)
    for col in h.cols:
        print('  %-22s st=%02x ty=%x  %r' % (col['name'], col['st'], col['ty'], c['H'][col['name']]))
    t = c.get('toc')
    if t:
        print('TOC enc=%s rows=%d rowlen=%d' % (t.encrypted, t.nrows, t.rowlen))
        for col in t.cols:
            print('  %-14s st=%02x ty=%x %s' % (col['name'], col['st'], col['ty'], col.get('const', '')))
        comp = sum(1 for r in t.rows if r['FileSize'] != r['ExtractSize'])
        print('compressed entries:', comp)
        mx = max(r['FileOffset'] for r in t.rows)
        print('max FileOffset', mx)
        for r in t.rows[:5]: print('  ', r)
    for k in ('EtocOffset', 'ItocOffset', 'GtocOffset'):
        if k in c:
            u = c[k]
            print(k, 'enc=%s rows=%d cols=%s' % (u.encrypted, u.nrows, [(x['name'], hex(x['st']), x['ty']) for x in u.cols]))
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w') as o:
            for r in t.rows:
                o.write('%s/%s\t%d\t%d\t%d\n' % (r['DirName'], r['FileName'], r['FileSize'], r['ExtractSize'], r['FileOffset']))
