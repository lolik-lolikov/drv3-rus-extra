"""Generic SRD texture read/replace for DRV3 PC.
textures(srd) -> list of dict(name, txr_pos, rsi_pos, w, h, scan, fmt, swz, res=[(off,size,flagpos)])"""
import struct, io
from PIL import Image
FMT_BCN={0x0f:1,0x11:3,0x14:5,0x16:4,0x1c:7}
def blocks(srd):
    p=0; out=[]
    while p+16<=len(srd):
        typ=srd[p:p+4]; dl,sl,unk=struct.unpack_from('>III',srd,p+4)
        d0=p+16; s0=d0+dl; s0+=(-s0)%16
        out.append((typ,p,d0,dl,s0,sl))
        p=s0+sl; p+=(-p)%16
    return out
def textures(srd):
    res=[]
    for typ,p,d0,dl,s0,sl in blocks(srd):
        if typ!=b'$TXR': continue
        unk,swz,w,h,scan,fmt=struct.unpack_from('<IHHHHB',srd,d0)
        sub=blocks(srd[s0:s0+sl])
        for t2,q,e0,el,_,_ in sub:
            if t2==b'$RSI':
                r0=s0+e0
                cnt=srd[r0+3]
                name_off=struct.unpack_from('<I',srd,r0+0x0c)[0]
                ents=[]
                for k in range(cnt):
                    o,sz=struct.unpack_from('<II',srd,r0+0x10+k*16)
                    ents.append((o&0x1FFFFFFF,sz,r0+0x10+k*16,o&0xE0000000))
                nm=srd[r0+name_off:].split(b'\0')[0].decode('ascii','replace')
                res.append(dict(name=nm,txr=d0,rsi=r0,w=w,h=h,scan=scan,fmt=fmt,swz=swz,res=ents))
    return res
def decode(t,srdv):
    off,sz,_,_=t['res'][0]; d=srdv[off:off+sz]; w,h=t['w'],t['h']
    f=t['fmt']
    if f in FMT_BCN:
        bw=(w+3)//4*4; bh=(h+3)//4*4
        mode='L' if f==0x16 else 'RGBA'
        im=Image.frombytes(mode,(bw,bh),d,'bcn',FMT_BCN[f])
        if mode=='L': im=im.convert('RGBA')
        return im.crop((0,0,w,h))
    if f==0x01:
        im=Image.frombytes('RGBA',(w,h),d[:w*h*4],'raw','BGRA')
        return im
    raise ValueError('fmt %x'%f)

def replace(srd, srdv, newimgs, align=0x80):
    """newimgs: {texname: PIL.Image RGBA (same size)} -> (srd, srdv). Replaced textures become BGRA8888 (fmt 1)."""
    srd=bytearray(srd); ts=textures(bytes(srd))
    out=bytearray(); done=set()
    # collect all resources in original offset order
    allres=[]
    for t in ts:
        for k,(off,sz,pos,flags) in enumerate(t['res']): allres.append((off,sz,pos,flags,t,k))
    allres.sort(key=lambda x:x[0])
    for off,sz,pos,flags,t,k in allres:
        if t['name'] in newimgs and k==0:
            im=newimgs[t['name']].convert('RGBA')
            assert im.size==(t['w'],t['h']),(t['name'],im.size)
            w,h=t['w'],t['h']
            if t['fmt']!=0x01 and w%4==0 and h%4==0:
                import etcpak
                data=etcpak.compress_bc7(im.tobytes(),w,h)
                struct.pack_into('<HHHHB',srd,t['txr']+4,3,w,h,(w//4)*16,0x1c)
                struct.pack_into('<I',srd,pos+8,0x80)
            else:
                data=im.tobytes('raw','BGRA')
                struct.pack_into('<HHHHB',srd,t['txr']+4,1,w,h,0,0x01)
                struct.pack_into('<I',srd,pos+8,0)
            done.add(t['name'])
        else:
            data=bytes(srdv[off:off+sz])
        out+=b'\0'*((-len(out))%align)
        struct.pack_into('<II',srd,pos,len(out)|flags,len(data))
        out+=data
    missing=set(newimgs)-done
    assert not missing, missing
    return bytes(srd),bytes(out)


def encode_tex(t, im):
    """Return (data, fmt, swz, scan, unk3) for a replacement image."""
    im = im.convert('RGBA')
    w, h = t['w'], t['h']
    assert im.size == (w, h), (t['name'], im.size)
    if t['fmt'] != 0x01 and w % 4 == 0 and h % 4 == 0:
        import etcpak
        return etcpak.compress_bc7(im.tobytes(), w, h), 0x1c, 3, (w // 4) * 16, 0x80
    return im.tobytes('raw', 'BGRA'), 0x01, 1, 0, 0


def replace_append(srd, srdv_len, newimgs, align=0x80):
    """Keep original srdv intact; new texture data is appended. Returns (new_srd, tail_bytes)."""
    srd = bytearray(srd); ts = textures(bytes(srd))
    tail = bytearray(); base = srdv_len; done = set()
    for t in ts:
        if t['name'] not in newimgs:
            continue
        data, fmt, swz, scan, unk3 = encode_tex(t, newimgs[t['name']])
        pad = (-(base + len(tail))) % align
        tail += b'\0' * pad
        off = base + len(tail)
        off0, sz, pos, flags = t['res'][0]
        struct.pack_into('<HHHHB', srd, t['txr'] + 4, swz, t['w'], t['h'], scan, fmt)
        struct.pack_into('<IIII', srd, pos, off | flags, len(data), unk3, 0)
        tail += data
        done.add(t['name'])
    missing = set(newimgs) - done
    assert not missing, missing
    return bytes(srd), bytes(tail)
