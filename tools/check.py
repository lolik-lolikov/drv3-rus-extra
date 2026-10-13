import sys,re,os,glob,collections
sys.path.insert(0,os.path.dirname(__file__))
from tmlib import load_tm
ALLOWED=set(chr(c) for c in range(32,127))|set('ЁАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюяё«»—…’×')
def tags(s): return re.findall(r'<[^>]*>',s)
def result(names=None, verbose=True):
    tm=load_tm(); out={}; problems=[]; missing=collections.Counter()
    for f in sorted(glob.glob('work/src/*.txt')):
        n=os.path.basename(f)[:-4]
        if names and n not in names: continue
        tr={}
        p=f'work/tr/{n}.tsv'
        if os.path.exists(p):
            for l in open(p):
                l=l.rstrip('\n')
                if not l.strip(): continue
                i,t=l.split('\t',1); tr[int(i)]=t
        res={}
        for l in open(f):
            i,s,t=l.rstrip('\n').split('\t',2); i=int(i)
            t=re.sub(r' \[TM: .*\]$','',t)
            if i in tr: r=tr[i]
            elif t in tm: r=tm[t]
            elif not re.search('[A-Za-z]',t): r=t
            else: missing[n]+=1; continue
            res[i]=r
            if tags(r)!=tags(t) and sorted(tags(r))!=sorted(tags(t)): problems.append((n,i,'TAGS',t,r))
            bad=set(re.sub(r'<[^>]*>','',r))-ALLOWED
            if bad: problems.append((n,i,'CHARS '+''.join(bad),t,r))
            segs=re.sub(r'<[^>]*>','',r).split('\\n')
            if max(len(x) for x in segs)>54: problems.append((n,i,'LONG %d'%max(len(x) for x in segs),t,r))
            if len(segs)>max(3,len(t.split('\\n'))): problems.append((n,i,'LINES',t,r))
            if re.search(r'[A-Za-z]{3,}',re.sub(r'<[^>]*>','',r)) and i in tr and not re.search(r'K1-B0|MonoMono|AV|DJ|SF|VR|DVD|BGM|HP|SP|CP|MP|MVP',r): problems.append((n,i,'LATIN?',t,r))
        out[n]=res
    return out,problems,missing
if __name__=='__main__':
    names=sys.argv[1:] or None
    out,problems,missing=result(names)
    for p in problems: print(*p,sep=' | ')
    tot=sum(missing.values())
    print('problems',len(problems),'missing lines',tot,'files incomplete',len(missing))
    if names:
        for n in names: print(n,'missing',missing[n])
