import numpy as np, re
txt=open('an2.out').read()
ev={m.group(1):np.array(list(map(float,m.group(2).split()))) for m in re.finditer(r'(KICK|SNARE|CLAP|HAT) \d+\n([\d. ]+)',txt)}
h=ev['HAT']; h=h[(h>3)&(h<15.2)]
# fit u, phase by grid search
best=None
for u in np.arange(0.200,0.212,0.00002):
    ph=np.angle(np.exp(2j*np.pi*h/u).mean()); r=abs(np.exp(2j*np.pi*h/u).mean())
    if best is None or r>best[0]: best=(r,u,(ph/(2*np.pi))*u)
r,u,off=best; off%=u; print('unit',round(u,5),'bpm8th',round(60/(2*u),3),'offset',round(off,4),'R',round(r,3))
# refine with kicks+claps too
N=int(23/u)+1
grid={i:'' for i in range(N)}
for nm,sym in (('KICK','K'),('CLAP','C'),('SNARE','s'),('HAT','h')):
    for x in ev[nm]:
        i=round((x-off)/u); err=x-(off+i*u)
        if abs(err)<0.045 and 0<=i<N: grid[i]+=sym
# find downbeat: print rows of 16 units
for start in range(0,N,16):
    row=' '.join(f'{(grid[i] or "."):>4}' for i in range(start,min(N,start+16)))
    print(f'{off+start*u:6.2f} |',row)
import json; json.dump({'u':u,'off':off},open('grid.json','w'))
