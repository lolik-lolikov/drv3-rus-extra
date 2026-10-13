import numpy as np, struct
def bc4_decode(data, w, h):
    bw, bh = (w+3)//4, (h+3)//4
    a = np.frombuffer(data[:bw*bh*8], dtype=np.uint8).reshape(bh, bw, 8)
    r0 = a[...,0].astype(np.int32); r1 = a[...,1].astype(np.int32)
    bits = np.zeros((bh,bw), dtype=np.uint64)
    for i in range(6): bits |= a[...,2+i].astype(np.uint64) << np.uint64(8*i)
    pal = np.zeros((bh,bw,8), dtype=np.int32)
    pal[...,0]=r0; pal[...,1]=r1
    gt = r0>r1
    for i in range(1,7):
        pal[...,1+i] = np.where(gt, ((7-i)*r0 + i*r1)//7, 0)
    for i in range(1,5):
        pal[...,1+i] = np.where(gt, pal[...,1+i], ((5-i)*r0 + i*r1)//5)
    pal[...,6] = np.where(gt, pal[...,6], 0); pal[...,7] = np.where(gt, pal[...,7], 255)
    out = np.zeros((bh*4, bw*4), dtype=np.uint8)
    for p in range(16):
        idx = ((bits >> np.uint64(3*p)) & np.uint64(7)).astype(np.int64)
        v = np.take_along_axis(pal, idx[...,None], axis=2)[...,0]
        out[p//4::4, p%4::4] = v
    return out[:h,:w]
def bc4_encode(img):
    h, w = img.shape
    H, W = (h+3)//4*4, (w+3)//4*4
    im = np.zeros((H,W), dtype=np.int32); im[:h,:w] = img
    blocks = im.reshape(H//4,4,W//4,4).transpose(0,2,1,3).reshape(H//4,W//4,16)
    mx = blocks.max(-1); mn = blocks.min(-1)
    r0 = mx; r1 = mn
    same = r0==r1
    pal = np.zeros(blocks.shape[:2]+(8,), dtype=np.int32)
    pal[...,0]=r0; pal[...,1]=r1
    for i in range(1,7): pal[...,1+i]=((7-i)*r0+i*r1)//7
    d = np.abs(blocks[...,:,None]-pal[...,None,:])
    idx = d.argmin(-1).astype(np.uint64)
    idx[same] = 0
    bits = np.zeros(blocks.shape[:2], dtype=np.uint64)
    for p in range(16): bits |= idx[...,p] << np.uint64(3*p)
    out = np.zeros(blocks.shape[:2]+(8,), dtype=np.uint8)
    # need r0>r1 for 8-value mode; if equal, r0==r1 fine (all idx0)
    out[...,0]=r0; out[...,1]=r1
    for i in range(6): out[...,2+i] = ((bits >> np.uint64(8*i)) & np.uint64(255)).astype(np.uint8)
    return out.tobytes()
