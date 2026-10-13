import json,os
B=os.path.join(os.path.dirname(__file__),'..','work')
def load_tm():
    tm={k.replace('\n','\\n'):v.replace('\n','\\n') for k,v in json.load(open(os.path.join(B,'tm_existing.json'))).items()}
    for l in open(os.path.join(B,'tm_new.tsv')):
        l=l.rstrip('\n')
        if '\t' in l:
            k,v=l.split('\t',1); tm[k]=v
    return tm
def load_rtm():
    tm={}
    p=os.path.join(B,'rtm.tsv')
    if os.path.exists(p):
        for l in open(p):
            l=l.rstrip('\n')
            if '\t' in l:
                k,v=l.split('\t',1); tm[k]=v
    return tm
