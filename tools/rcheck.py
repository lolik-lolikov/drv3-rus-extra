import sys,re,os,glob,collections
sys.path.insert(0,os.path.dirname(__file__))
from tmlib import load_rtm as load_tm
from rwidth import width
ALLOWED=set(' !"$%&\'()*,-./0123456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz{}—…※℠⇒□△○★\u3000【】ステトー階１ＬＲ\\')|set('ЁАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюяё«»’№+')
def tags(s): return re.findall(r'<[^>]*>|\$\{[^}]*\}|%[0-9]*[a-z]|%[0-9]',s)
def result(names=None, verbose=True):
    tm=load_tm(); out={}; problems=[]; missing=collections.Counter()
    for f in sorted(glob.glob('work/rsrc/*.txt')):
        n=os.path.basename(f)[:-4]
        if names and n not in names: continue
        tr={}
        p=f'work/rtr/{n}.tsv'
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
            bad=set(re.sub(r'<[^>]*>|\$\{[^}]*\}','',r))-ALLOWED
            if bad: problems.append((n,i,'CHARS '+''.join(bad),t,r))
            segs=re.sub(r'<[^>]*>','',r).split('\\n')
            if n.startswith('ui__'):
                if max(len(x) for x in segs)>50: problems.append((n,i,'LONG %d'%max(len(x) for x in segs),t,r))
                if len(segs)>max(3,len(t.split('\\n'))): problems.append((n,i,'LINES',t,r))
            else:
                mw=max(width(x.replace('\\r','')) for x in segs)
                if mw>1350: problems.append((n,i,'WIDE %d'%mw,t,r))
                if len(segs)>max(2,len(t.split('\\n'))): problems.append((n,i,'LINES',t,r))
            if re.search(r'[A-Za-z]{3,}',re.sub(r'<[^>]*>|\$\{[^}]*\}','',r)) and i in tr and not re.search(r'K1-B0|MonoMono|AV|DJ|SF|VR|DVD|BGM|HP|SP|CP|MP|MVP|RPG|EXP|LV|Lv',r): problems.append((n,i,'LATIN?',t,r))
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
