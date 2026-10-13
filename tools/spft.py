import struct
def parse_srd_font(srd):
    # returns dict with header fields, chars list, entries list, plus raw parts
    assert srd[:4]==b'$CFH'
    txr = srd[0x20:0x30]
    rsi_off = 0x40
    rsi_len = struct.unpack_from('>I', srd, 0x34)[0]
    rsi = srd[rsi_off:rsi_off+rsi_len]
    sp_off, sp_len = struct.unpack_from('<II', rsi, 0x24)
    sp = rsi[sp_off:sp_off+sp_len]
    h = struct.unpack_from('<4sIIIIIIIIHHI', sp, 0)
    magic, ver, maxc, size, name_off, n, gi_off, bm_off, idx_off, lh, asc, kern_off = h
    bm = sp[bm_off:bm_off+(maxc+7)//8]
    chars = [c for c in range(maxc) if c//8 < len(bm) and (bm[c//8] >> (c % 8)) & 1]
    ents = []
    for i in range(n):
        e = sp[gi_off+i*8: gi_off+i*8+8]
        x = e[0] | (e[1] & 0x0f) << 8
        y = (e[1] >> 4) | e[2] << 4
        ents.append(dict(x=x, y=y, w=e[3], h=e[4], a=e[5], b=e[6], c=e[7]))
    name = sp[name_off:kern_off if kern_off>name_off else len(sp)]
    return dict(ver=ver, maxc=maxc, size=size, lh=lh, asc=asc, chars=chars, ents=ents, sp=sp, rsi=rsi, txr=txr,
                name_off=name_off, kern_off=kern_off, gi_off=gi_off, idx_off=idx_off, bm_off=bm_off, n=n)
