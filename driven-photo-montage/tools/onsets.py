import librosa, numpy as np, scipy.signal as ss
from scipy.ndimage import maximum_filter1d
y, sr = librosa.load('sec.wav', sr=44100, mono=True); hop=128
yo,_ = librosa.load('old.wav', sr=44100, mono=True)
c=ss.correlate(yo[:sr*8],y[:sr*8],'full'); lag=(np.argmax(c)-(sr*8-1))/sr; print('old m4a lag vs section (s)',round(lag,4))
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=hop)); f=librosa.fft_frequencies(sr=sr,n_fft=2048); t=librosa.frames_to_time(np.arange(S.shape[1]),sr=sr,hop_length=hop)
def flux(lo,hi):
    b=np.log1p(S[(f>=lo)&(f<hi)]).sum(0); d=np.maximum(0,np.diff(b,prepend=b[0])); return d
for nm,lo,hi in (('KICK',35,120),('SNARE',180,400),('CLAP',2000,6000),('HAT',8000,16000)):
    d=flux(lo,hi); 
    # local normalisation: 2s window max
    w=int(2*sr/hop); mx=maximum_filter1d(d,w); dn=d/(mx+1e-9)
    p,_=ss.find_peaks(d,distance=int(0.09*sr/hop))
    p=[i for i in p if dn[i]>0.45 and d[i]>np.percentile(d,90)]
    print(nm,len(p)); print(' '.join(f'{t[i]:.3f}' for i in p))
