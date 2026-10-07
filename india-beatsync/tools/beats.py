import numpy as np, scipy.io.wavfile as w, scipy.signal as sg, json
sr, x = w.read('music.wav'); x = x.astype(float) / 32768
hop, n = 256, 1024
win = np.hanning(n)
frames = np.lib.stride_tricks.sliding_window_view(np.pad(x, (n // 2, n // 2)), n)[::hop] * win
S = np.abs(np.fft.rfft(frames, axis=1))
freqs = np.fft.rfftfreq(n, 1 / sr)
logS = np.log1p(100 * S)
flux = np.maximum(0, np.diff(logS, axis=0)).sum(1); flux = np.r_[0, flux]
low = np.maximum(0, np.diff(logS[:, freqs < 150], axis=0)).sum(1); low = np.r_[0, low]
t = np.arange(len(flux)) * hop / sr
def norm(a): a = a - sg.medfilt(a, 31); return a / (a.max() + 1e-9)
fl, lo = norm(flux), norm(low)
# tempo via autocorrelation of onset envelope
ac = np.correlate(fl, fl, 'full')[len(fl) - 1:]
lags = np.arange(len(ac)) * hop / sr
bpm_range = (lags > 60 / 180) & (lags < 60 / 60)
L = lags[bpm_range][np.argmax(ac[bpm_range])]
print('tempo', 60 / L)
pk, _ = sg.find_peaks(fl, height=0.18, distance=int(0.12 * sr / hop))
kick, _ = sg.find_peaks(lo, height=0.25, distance=int(0.2 * sr / hop))
rms = np.sqrt((frames ** 2).mean(1))
json.dump({'onsets': [[round(float(t[i]), 3), round(float(fl[i]), 2)] for i in pk], 'kicks': [[round(float(t[i]), 3), round(float(lo[i]), 2)] for i in kick],
           'rms': [[round(float(t[i]), 2), round(float(rms[i]), 4)] for i in range(0, len(rms), 22)]}, open('beats.json', 'w'))
print('kicks', [round(float(t[i]), 2) for i in kick])
print('strong onsets', [round(float(t[i]), 2) for i in pk if fl[i] > 0.45])
# loudness every 0.5 s
print('rms/0.5s', ' '.join(f"{float(rms[int(i*sr/hop*0.5)]):.2f}" for i in range(int(t[-1] * 2))))
