import json,sys
props=["fontSize","fontWeight","lineHeight","letterSpacing","color","fontFamily","paddingTop","paddingLeft","marginTop","marginBottom","backgroundColor","textTransform","maxWidth","borderTopWidth","borderLeftWidth"]
def h(s):
    x=5381
    for ch in s:
        x=((x<<5)+x+ord(ch)) & 0xffffffff
        if x>=2**31: x-=2**32
    x&=0xffffffff
    n=x; d='0123456789abcdefghijklmnopqrstuvwxyz'; o=''
    while True:
        o=d[n%36]+o; n//=36
        if n==0: break
    return o
loc=json.load(open('probe_local.json'))
def pagemap(r):
    return {k.encode('utf-16-le').decode('utf-16-le')[:24]: h("|".join(v[p] for p in props))[:5] for k,v in loc[r].items()}
if len(sys.argv)>1:
    print(json.dumps(pagemap(sys.argv[1]),ensure_ascii=False,separators=(',',':')))
else:
    out={}
    for r in loc:
        if r=='w':continue
        m=pagemap(r); out[r]=h(json.dumps(sorted(m.items()),ensure_ascii=False,separators=(',',':')))
    print(json.dumps(out))
