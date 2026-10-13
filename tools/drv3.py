"""DRV3 file format helpers: SPC archives, STX string tables."""
import struct, os

# ---------------- SPC ----------------

def _bitrev(b):
    b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
    b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
    b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
    return b

BITREV = bytes(_bitrev(i) for i in range(256))


def spc_dec(data):
    res = bytearray()
    flag = 1
    p = 0
    n = len(data)
    while p < n:
        if flag == 1:
            flag = 0x100 | BITREV[data[p]]
            p += 1
            if p >= n:
                break
        if flag & 1:
            res.append(data[p]); p += 1
        else:
            if p + 1 >= n:
                break
            b = data[p] | (data[p + 1] << 8); p += 2
            count = (b >> 10) + 2
            off = b & 0x3FF
            start = len(res) - 1024 + off
            for i in range(count):
                res.append(res[start + i])
        flag >>= 1
    return bytes(res)


_LIB = None
def _load_lib():
    global _LIB
    if _LIB is None:
        try:
            import ctypes
            _LIB = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c', 'libspccmp.so'))
            _LIB.spc_cmp.restype = ctypes.c_long
            _LIB.spc_cmp.argtypes = [ctypes.c_char_p, ctypes.c_long, ctypes.c_char_p]
        except Exception:
            _LIB = False
    return _LIB


def spc_cmp(data):
    lib = _load_lib()
    if lib:
        import ctypes
        n = len(data)
        out = ctypes.create_string_buffer(n * 9 // 8 + 64)
        o = lib.spc_cmp(bytes(data), n, out)
        return out.raw[:o]
    return spc_cmp_py(data)


def spc_append_stream(raw, tail):
    """Extend a compressed stream so it decodes to (original + tail), keeping the original bytes (except the last flag byte)."""
    import ctypes
    lib = _load_lib()
    lfp = ctypes.c_long(); used = ctypes.c_int()
    lib.spc_scan.restype = ctypes.c_long
    lib.spc_scan.argtypes = [ctypes.c_char_p, ctypes.c_long, ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_int)]
    lib.spc_scan(bytes(raw), len(raw), ctypes.byref(lfp), ctypes.byref(used))
    out = bytearray(raw)
    k = 0
    if lfp.value >= 0 and used.value < 8:
        k = min(8 - used.value, len(tail))
        bits = BITREV[out[lfp.value]]
        for i in range(used.value, used.value + k):
            bits |= 1 << i
        out[lfp.value] = BITREV[bits]
        out += tail[:k]
    if len(tail) > k:
        out += spc_cmp(tail[k:])
    return bytes(out)


def spc_cmp_py(data):
    """LZ-style compressor compatible with spc_dec (window 1024, len 2..65)."""
    out = bytearray()
    n = len(data)
    p = 0
    # hash chains of 2-byte prefixes
    from collections import defaultdict
    table = defaultdict(list)
    while p < n:
        flag_pos = len(out)
        out.append(0)
        flag = 0
        for bit in range(8):
            if p >= n:
                break
            best_len = 0; best_pos = 0
            if p + 2 <= n:
                key = data[p:p + 2]
                cands = table.get(key)
                if cands:
                    lo = p - 1024
                    # prune old
                    while cands and cands[0] < lo:
                        cands.pop(0)
                    maxl = min(65, n - p)
                    for c in reversed(cands[-64:]):
                        l = 2
                        while l < maxl and data[c + l] == data[p + l]:
                            l += 1
                        if l > best_len:
                            best_len = l; best_pos = c
                            if l == maxl:
                                break
            if best_len >= 2:
                # pos relative: start = len(res) - 1024 + off  -> off = start - p + 1024
                off = best_pos - p + 1024
                v = ((best_len - 2) << 10) | off
                out += struct.pack('<H', v)
                for k in range(best_len):
                    if p + k + 2 <= n:
                        table[data[p + k:p + k + 2]].append(p + k)
                p += best_len
            else:
                flag |= (1 << bit)
                out.append(data[p])
                if p + 2 <= n:
                    table[data[p:p + 2]].append(p)
                p += 1
        out[flag_pos] = BITREV[flag]
    return bytes(out)


class SpcEntry:
    def __init__(self, name, data, cmp_flag=1, unk_flag=4):
        self.name = name; self.data = data; self.cmp_flag = cmp_flag; self.unk_flag = unk_flag


def spc_read(buf):
    if buf[:4] == b'$CMP':
        raise ValueError('$CMP container not supported')
    assert buf[:4] == b'CPS.', buf[:4]
    header = buf[4:0x28]
    count, unk2 = struct.unpack_from('<II', buf, 0x28)
    p = 0x30 + 0x10
    assert buf[p:p + 4] == b'Root'
    p += 0x10
    entries = []
    for i in range(count):
        cmp_flag, unk_flag, cmp_size, dec_size, name_len = struct.unpack_from('<HHIII', buf, p)
        p += 0x10 + 0x10
        name_pad = (0x10 - (name_len + 1) % 0x10) % 0x10
        name = buf[p:p + name_len].decode('ascii', 'replace')
        p += name_len + 1 + name_pad
        raw = buf[p:p + cmp_size]
        p += cmp_size + ((0x10 - cmp_size % 0x10) % 0x10)
        if cmp_flag == 1:
            data = raw
        elif cmp_flag == 2:
            data = spc_dec(raw)
            assert len(data) == dec_size, (name, len(data), dec_size)
        else:
            raise ValueError('cmp_flag %d' % cmp_flag)
        e = SpcEntry(name, bytes(data), cmp_flag, unk_flag)
        e.raw = bytes(raw); e._orig = e.data
        entries.append(e)
    return {'header': header, 'unk2': unk2, 'entries': entries}


def spc_write(spc, compress=True):
    out = bytearray(b'CPS.')
    out += spc['header']
    out += struct.pack('<II', len(spc['entries']), spc['unk2'])
    out += b'\0' * 0x10
    out += b'Root' + b'\0' * 0x0C
    for e in spc['entries']:
        data = e.data
        flag = 1
        if getattr(e, 'append_tail', None) is not None and e.cmp_flag == 1:
            payload = e._orig + e.append_tail; flag = 1
            data = payload
        elif getattr(e, 'append_tail', None) is not None and e.cmp_flag == 2 and getattr(e, 'raw', None) is not None:
            payload = spc_append_stream(e.raw, e.append_tail); flag = 2
            data = e._orig + e.append_tail
        elif getattr(e, '_orig', None) is not None and e.data is e._orig and getattr(e, 'raw', None) is not None:
            payload = e.raw; flag = e.cmp_flag
        elif compress and e.cmp_flag == 2:
            c = spc_cmp(data)
            assert spc_dec(c) == data
            payload = c; flag = 2
        else:
            payload = data
        nm = e.name.encode('ascii')
        if getattr(e, 'append_tail', None) is not None:
            data = e._orig + e.append_tail
        out += struct.pack('<HHIII', flag, e.unk_flag, len(payload), len(data), len(nm))
        out += b'\0' * 0x10
        out += nm + b'\0' * (1 + (0x10 - (len(nm) + 1) % 0x10) % 0x10)
        out += payload + b'\0' * ((0x10 - len(payload) % 0x10) % 0x10)
    return bytes(out)


# ---------------- STX ----------------

def stx_read(buf):
    assert buf[:4] == b'STXT', buf[:4]
    lang = buf[4:8]
    unk1, table_off, unk2, count = struct.unpack_from('<IIII', buf, 8)
    strs = []
    for i in range(count):
        sid, soff = struct.unpack_from('<II', buf, table_off + i * 8)
        e = soff
        while buf[e:e + 2] != b'\0\0':
            e += 2
        strs.append((sid, buf[soff:e].decode('utf-16-le')))
    return {'lang': lang, 'unk1': unk1, 'unk2': unk2, 'table_off': table_off, 'strings': strs}


def stx_write(stx):
    strs = stx['strings']
    count = len(strs)
    table_off = 0x20
    out = bytearray(b'STXT' + stx['lang'])
    out += struct.pack('<IIII', stx['unk1'], table_off, stx['unk2'], count)
    out += b'\0' * (table_off - len(out))
    table_pos = len(out)
    out += b'\0' * (count * 8)
    # pad to 16? keep simple
    offsets = {}
    for i, (sid, s) in enumerate(strs):
        # reuse identical strings like the original does
        if s in offsets:
            soff = offsets[s]
        else:
            soff = len(out)
            offsets[s] = soff
            out += s.encode('utf-16-le') + b'\0\0'
        struct.pack_into('<II', out, table_pos + i * 8, sid, soff)
    return bytes(out)


# ---------------- WRD ----------------
WRD_OPS = ['FLG','IFF','WAK','IFW','SWI','CAS','MPF','SPW','MOD','HUM','CHK','KTD','CLR','RET','KNM','CAP','FIL','END','SUB','RTN','LAB','JMP','MOV','FLS','FLM','VOI','BGM','SE_','JIN','CHN','VIB','FDS','FLA','LIG','CHR','BGD','CUT','ADF','PAL','MAP','OBJ','BUL','CRF','CAM','KWM','ARE','KEY','WIN','MSC','CSM','PST','KNS','FON','BGO','LOG','SPT','CDV','SZM','PVI','EXP','MTA','MVP','POS','ICO','EAI','COL','CFP','CLT','R__','PAD','LOC','BTN','ENT','CED','LBN','JMN']

def wrd_read(w):
    sc, lc, pc, bc, _, brp, lop, lnp, pp, sp = struct.unpack_from('<HHHHIIIIII', w, 0)
    end = min(x for x in (brp, lop, lnp, pp) if x) if any((brp, lop, lnp, pp)) else len(w)
    params = []
    p = pp
    for i in range(pc):
        l = w[p]; params.append(w[p + 1:p + 1 + l].decode('utf-8', 'replace')); p += l + 2
    cmds = []
    p = 0x20
    while p < end:
        if w[p] != 0x70:
            p += 1; continue
        op = w[p + 1]; p += 2; args = []
        while p + 1 < end and w[p] != 0x70:
            args.append(struct.unpack_from('>H', w, p)[0]); p += 2
        cmds.append((WRD_OPS[op] if op < len(WRD_OPS) else 'x%02X' % op, args))
    return {'string_count': sc, 'params': params, 'cmds': cmds}


# ---------------- RSCT (minigame text) ----------------
def rsct_read(d):
    assert d[:4] == b'RSCT'
    unk, count, toff = struct.unpack_from('<III', d, 4)
    out = []
    for i in range(count):
        h, off = struct.unpack_from('<II', d, toff + i * 8)
        ln = struct.unpack_from('<I', d, off)[0]
        s = d[off + 4: off + 4 + ln].decode('utf-16-le').rstrip('\0')
        out.append((h, s))
    return {'unk': unk, 'strings': out}


def rsct_write(r):
    count = len(r['strings'])
    toff = 0x14
    data_start = toff + count * 8
    head = bytearray(b'RSCT' + struct.pack('<IIII', r['unk'], count, toff, data_start))
    head = head[:0x14]
    table = bytearray(); body = bytearray(); cache = {}
    for h, s in r['strings']:
        if s in cache:
            off = cache[s]
        else:
            off = data_start + len(body); cache[s] = off
            b = s.encode('utf-16-le') + b'\0\0'
            body += struct.pack('<I', len(b)) + b
        table += struct.pack('<II', h, off)
    return bytes(head + table + body)
