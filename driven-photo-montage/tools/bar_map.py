import librosa, numpy as np, json
y, sr = librosa.load('sec.wav', sr=44100, mono=True); hop=128
g=json.load(open('grid.json')); u,off=g['u'],g['off']
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=hop)); f=librosa.fft_frequencies(sr=sr,n_fft=2048)
def env(lo,hi): b=np.log1p(S[(f>=lo)&(f<hi)]).sum(0); return np.maximum(0,np.diff(b,prepend=b[0]))
lo,mid,hi=env(35,150),env(1500,6000),env(6000,16000); fr=lambda t:int(t*sr/hop)
def st(e,t): a=fr(t-0.03); return e[a:fr(t+0.05)].max()
L=np.percentile(lo,99.5); M=np.percentile(mid,99.5)
rms=librosa.feature.rms(y=y,hop_length=hop)[0]
print('slot:   ' + '  '.join(f'{k:>9}' for k in range(8)))
for bar in range(-2,11):
    i0=14+8*bar; row=[]
    for k in range(8):
        t=off+(i0+k)*u
        if t<0 or t>22.7: row.append(' '*9); continue
        row.append(f'{int(99*min(1,st(lo,t)/L)):>3}/{int(99*min(1,st(mid,t)/M)):<3}{"*" if st(lo,t)/L>0.55 else " "} ')
    a=fr(off+i0*u); b=fr(off+(i0+8)*u)
    print(f'bar{bar:>3} {off+i0*u:6.3f} rms{rms[max(a,0):b].mean():.3f}', ' '.join(row))
