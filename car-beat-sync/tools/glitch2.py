"""simulate KineMaster playback: per key, screen corners = base transform + pins. Flag spikes: a corner that jumps
far more than its neighbours' motion (an out-and-back within a few frames)."""
import json,sys,math
L=json.load(open(sys.argv[1])); ZO=[0,1,3,2]   # pin slot i -> logical corner (z order)
LOG=[(-1,-1),(1,-1),(1,1),(-1,1)]
def corners(k,pin,box):
    w,h=box; off=[[0,0]]*4
    if pin:
        off=[[0,0] for _ in range(4)]
        for j in range(4): off[ZO[j]]=[pin[2*j],pin[2*j+1]]
    a=math.radians(k['rot']); c,s=math.cos(a),math.sin(a); out=[]
    for i,(lx,ly) in enumerate(LOG):
        u=(lx*w/2+off[i][0])*k['sx']; v=(ly*h/2+off[i][1])*abs(k['sy'])
        out.append((k['x']+u*c-v*s, k['y']+u*s+v*c))
    return out
bad=0; worst=[]
for l in L:
    k=l['kfs']; P=l['pins']; span=l['end']-l['start']
    if len(k)<3: continue
    C=[corners(k[i], P[i]['c'] if P and i<len(P) else None, l['box']) for i in range(len(k))]
    T=[l['start']+x['t']*span for x in k]
    for i in range(1,len(k)-1):
        # predicted corner = linear between neighbours; error = how far this key sits off that line
        f=(T[i]-T[i-1])/max(T[i+1]-T[i-1],1e-9)
        err=max(math.hypot(C[i][j][0]-(C[i-1][j][0]+(C[i+1][j][0]-C[i-1][j][0])*f), C[i][j][1]-(C[i-1][j][1]+(C[i+1][j][1]-C[i-1][j][1])*f)) for j in range(4))
        dt=T[i+1]-T[i-1]
        if err>60 and dt<0.25:
            bad+=1; worst.append((err,l['id'],l.get('text'),round(T[i],2),round(dt,3)))
worst.sort(reverse=True)
print('spikes',bad); [print(w) for w in worst[:25]]
