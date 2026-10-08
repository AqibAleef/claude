"""Sharp crops for the 146 BPM montage: full-frame portrait crops (never upscaled more than ~1.1x) and 1.8:1 bands.

    python3 car_prep2.py PHOTOS_DIR OUT_DIR      (OUT_DIR = the car_prep.py output; adds photo/pc_*.jpg, photo/band_*.jpg)
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
PH, OUT = sys.argv[1:3]


def grade(a):   # same grade as car_prep.py
    a = np.clip(a, 0, 1) ** 1.05; lum = a.mean(2, keepdims=True)
    a = a + np.array([-0.012, 0.004, 0.035]) * (1 - lum) ** 2 + np.array([0.03, 0.01, -0.025]) * lum ** 2
    a = 0.5 + (a - 0.5) * 1.12; lum = a.mean(2, keepdims=True); a = lum + (a - lum) * 1.05
    return np.clip(a, 0, 1)


def cut(n, cx, cy, h, aspect, size, name):
    im = Image.open(f'{PH}/{n}.jpg').convert('RGB'); W, H = im.size
    ch = H * h; cw = ch * aspect
    if cw > W: cw = W; ch = cw / aspect
    x0 = min(max(cx * W - cw / 2, 0), W - cw); y0 = min(max(cy * H - ch / 2, 0), H - ch)
    c = im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch))).resize(size, Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 50, 2))
    Image.fromarray((grade(np.asarray(c).astype(np.float32) / 255) * 255).astype(np.uint8)).save(f'{OUT}/photo/{name}.jpg', quality=92)
    print(name, 'source px', round(cw), 'x', round(ch), '-> upscale', round(size[1] / ch, 2))


PORTRAIT = {'pc17_racers': ('17', 0.45, 0.47, 0.72), 'pc17_kerb': ('17', 0.55, 0.78, 0.72), 'pc19_crowd': ('19', 0.6, 0.3, 0.72),
            'pc19_car': ('19', 0.42, 0.66, 0.72), 'pc18_rain': ('18', 0.5, 0.5, 1.0)}
BANDS = {'band16_tail': ('16', 0.74, 0.6, 0.62), 'band16_flank': ('16', 0.3, 0.5, 0.62), 'band20_car': ('20', 0.62, 0.42, 0.55),
         'band20_dust': ('20', 0.85, 0.55, 0.55), 'band19_wheel': ('19', 0.55, 0.7, 0.37), 'band17_racers': ('17', 0.45, 0.45, 0.37),
         'band19_crowd': ('19', 0.6, 0.12, 0.37)}
for k, (n, cx, cy, h) in PORTRAIT.items(): cut(n, cx, cy, h, 9 / 16, (720, 1280), k)
for k, (n, cx, cy, h) in BANDS.items(): cut(n, cx, cy, h, 1.8, (1080, 600), k)


# cards for the landscape photos (16, 20): a sharp card whose car region is defocused (the sharp car layer sits on it, a
# little nearer the camera) and a dark, heavily blurred backdrop that fills the 9:16 frame behind the card
import cv2
CUT = sys.argv[3] if len(sys.argv) > 3 else None
for n in ('16', '20'):
    im = Image.open(f'{PH}/{n}.jpg').convert('RGB'); W, H = im.size; g = grade(np.asarray(im).astype(np.float32) / 255)
    alpha = np.asarray(Image.open(f'{CUT}/{n}.png').convert('RGBA').resize((W, H)))[..., 3]
    m = cv2.dilate((alpha > 40).astype(np.uint8) * 255, np.ones((int(W * 0.02) | 1,) * 2, np.uint8))
    mm = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), W * 0.012)[..., None]
    card = g * (1 - mm) + cv2.GaussianBlur(g, (0, 0), W * 0.03) * mm
    Image.fromarray((np.clip(card, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/photo/card_{n}.jpg', quality=93)
    soft = cv2.GaussianBlur(g, (0, 0), W * 0.035) * 0.62
    Image.fromarray((np.clip(soft, 0, 1) * 255).astype(np.uint8)).resize((540, round(540 * H / W))).save(f'{OUT}/photo/soft_{n}.jpg', quality=85)
    print('card', n)
