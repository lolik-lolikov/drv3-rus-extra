"""Профиль надписи оригинала: верх/низ основной массы букв (мода по столбцам), левый/правый край. python3 audit/prof.py tex [tex...]"""
import os, sys, json
import numpy as np
from PIL import Image
res = json.load(open('audit/scan.json'))
done = set()
for nm in sys.argv[1:]:
    for r in res:
        if r[3] == nm and r[8] and nm not in done:
            done.add(nm)
            a = np.array(Image.open(r[8]).convert('RGBA'))[:, :, 3]
            H, W = a.shape
            cols = np.where((a > 128).any(0))[0]
            tops = []; bots = []
            for x in cols:
                ys = np.where(a[:, x] > 128)[0]
                tops.append(ys.min()); bots.append(ys.max())
            tops = np.array(tops); bots = np.array(bots)
            def mode(v):
                vals, cnt = np.unique(v, return_counts=True); return int(vals[cnt.argmax()])
            ys, xs = np.where(a > 128)
            print('%-28s %4dx%-4d ink x %d..%d y %d..%d | top mode %d p10 %d | bottom mode %d p90 %d' % (
                nm, W, H, xs.min(), xs.max(), ys.min(), ys.max(), mode(tops), np.percentile(tops, 10), mode(bots), np.percentile(bots, 90)))
