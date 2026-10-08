"""Car beat-sync (photo motion graphics): prepare 2.5D photo layers, detail crops, graded clips and typography.

    python3 car_prep.py PHOTOS_DIR CUTOUTS_DIR CLIPS_DIR FONTS_DIR OUT_DIR

PHOTOS_DIR  16.jpg .. 20.jpg (the supplied photos)      CUTOUTS_DIR  16.png 17.png 19.png 20.png (BiRefNet mattes)
For every photo with a car: bg_N.jpg = graded photo with the car region deeply defocused and a soft lens blur,
fg_N.png = the graded car on transparency, same pixel grid - stacked at different depths they give real parallax.
"""
import json, os, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PH, CUT, CL, FONTS, OUT = sys.argv[1:6]
for d in ('photo', 'clips', 'type'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
META = {}


def grade(a):
    """punchy commercial grade: denser blacks, cool shadows, warm highlights, reds kept rich"""
    a = np.clip(a, 0, 1) ** 1.05; lum = a.mean(2, keepdims=True)
    a = a + np.array([-0.012, 0.004, 0.035]) * (1 - lum) ** 2 + np.array([0.03, 0.01, -0.025]) * lum ** 2
    a = 0.5 + (a - 0.5) * 1.12; lum = a.mean(2, keepdims=True); a = lum + (a - lum) * 1.05
    return np.clip(a, 0, 1)


def to_img(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def plates(n):
    im = Image.open(f'{PH}/{n}.jpg').convert('RGB'); W, H = im.size
    rgb = np.asarray(im).astype(np.float32) / 255; g = grade(rgb)
    cut = Image.open(f'{CUT}/{n}.png').convert('RGBA').resize((W, H)); alpha = np.asarray(cut)[..., 3]
    # background: the car region becomes a strong defocus of itself (reads as depth of field when the car layer slides),
    # the rest gets a gentle lens blur so the plate sits further back
    m = cv2.dilate((alpha > 40).astype(np.uint8) * 255, np.ones((int(max(W, H) * 0.02) | 1,) * 2, np.uint8))
    mm = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), max(W, H) * 0.012)[..., None]
    deep = cv2.GaussianBlur(g, (0, 0), max(W, H) * 0.03)
    bg = cv2.GaussianBlur(g, (0, 0), max(W, H) / 700) * (1 - mm) + deep * mm
    to_img(bg).save(f'{OUT}/photo/bg_{n}.jpg', quality=90)
    # foreground: graded pixels, matte softened by a hair so edges don't fizz when scaled
    a = cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), 0.8)
    fg = np.dstack([(g * 255).astype(np.uint8), a.clip(0, 255).astype(np.uint8)])
    Image.fromarray(fg, 'RGBA').save(f'{OUT}/photo/fg_{n}.png', optimize=True)
    to_img(g).save(f'{OUT}/photo/full_{n}.jpg', quality=90)
    META[f'photo_{n}'] = {'w': W, 'h': H}
    print('plates', n, W, H)


CROPS = {   # name: (photo, centre x, centre y (fraction), zoom: crop height as fraction of the photo height)
    'tail': ('16', 0.73, 0.58, 0.95), 'flank16': ('16', 0.30, 0.55, 1.0), 'racers': ('17', 0.44, 0.47, 0.42), 'kerb': ('17', 0.55, 0.80, 0.5),
    'crowd': ('19', 0.62, 0.22, 0.45), 'wheel': ('19', 0.60, 0.70, 0.5), 'rally': ('20', 0.46, 0.50, 1.0), 'dust': ('20', 0.75, 0.55, 1.0), 'rain': ('18', 0.5, 0.45, 1.0),
}


def crops():
    for name, (n, cx, cy, z) in CROPS.items():
        im = Image.open(f'{PH}/{n}.jpg').convert('RGB'); W, H = im.size
        ch = H * z; cw = ch * 9 / 16
        if cw > W: cw = W; ch = cw * 16 / 9
        x0 = min(max(cx * W - cw / 2, 0), W - cw); y0 = min(max(cy * H - ch / 2, 0), H - ch)
        c = im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch))).resize((720, 1280), Image.LANCZOS)
        c = c.filter(ImageFilter.UnsharpMask(2, 60, 2))
        to_img(grade(np.asarray(c).astype(np.float32) / 255)).save(f'{OUT}/photo/crop_{name}.jpg', quality=90); print('crop', name)


GRADE = 'eq=contrast=1.12:saturation=1.05:gamma=0.97,colorbalance=rs=-0.02:bs=0.05:rh=0.04:gh=0.01:bh=-0.03'


def clips():
    for f in sorted(os.listdir(CL)):
        if not f.endswith('.mp4'): continue
        n = f.split('-', 1)[-1][:-4]
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(CL, f), '-an', '-vf', 'scale=720:1280,' + GRADE, '-c:v', 'libx264', '-crf', '21', '-g', '12',
                        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{OUT}/clips/{n}.mp4'], check=True); print('clip', n)


def font(name, w, size):
    p = {'anton': f'{FONTS}/fontsource-anton-5.3.0/package/files/anton-latin-400-normal.woff',
         'sync': f'{FONTS}/fontsource-syncopate-5.3.0/package/files/syncopate-latin-{w}-normal.woff'}[name]
    return ImageFont.truetype(p, size)


def text(name, txt, face, w, px, tracking=0.0, color=(255, 255, 255), shadow=0.45):
    k = 2; f = font(face, w, px * k); asc, desc = f.getmetrics(); pad = int(px * k * 0.6)
    adv = [f.getlength(c) for c in txt]; sp = tracking * px * k; tw = sum(adv) + sp * (len(txt) - 1)
    m = Image.new('L', (int(tw + 2 * pad), asc + desc + 2 * pad), 0); d = ImageDraw.Draw(m); x = pad
    for c, a in zip(txt, adv): d.text((x, pad), c, font=f, fill=255); x += a + sp
    out = Image.new('RGBA', m.size, (0, 0, 0, 0))
    if shadow: sh = Image.new('RGBA', m.size, (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(6 * k)).point(lambda v: int(v * shadow))); out.alpha_composite(sh, (0, 3 * k))
    face_ = Image.new('RGBA', m.size, color + (0,)); face_.putalpha(m); out.alpha_composite(face_)
    out = out.resize((m.width // k, m.height // k), Image.LANCZOS); bb = m.getbbox()
    out.save(f'{OUT}/type/{name}.png'); META[name] = {'w': out.width, 'h': out.height, 'dy': round((m.height / 2 - (bb[1] + bb[3]) / 2) / k, 1),
                                                       'ink': round((bb[2] - bb[0]) / k, 1)}
    print('type', name)


def typography():
    text('driven', 'DRIVEN', 'anton', 400, 230, 0.02)
    text('move', 'MOVE', 'anton', 400, 260, 0.02)
    text('built_to', 'BUILT TO', 'sync', 700, 30, 0.5)
    text('by_instinct', 'BY INSTINCT', 'sync', 700, 26, 0.55)
    text('no_brakes', 'NO BRAKES', 'sync', 700, 22, 0.6)
    for i in range(1, 6): text(f'n{i}', f'0{i}', 'sync', 700, 18, 0.3, shadow=0.5)
    # graphics: a red rule and a white rule (thin, crisp), and an anamorphic streak in white and red
    for nm, col in (('rule_red', (227, 38, 46)), ('rule_white', (255, 255, 255))):
        Image.new('RGBA', (600, 6), col + (255,)).save(f'{OUT}/type/{nm}.png')
    for nm, col in (('streak_white', (255, 250, 245)), ('streak_red', (255, 70, 60))):
        Wd, Hh = 1800, 90; yy, xx = np.mgrid[0:Hh, 0:Wd].astype(np.float32); dx = np.abs(xx - Wd / 2) / (Wd / 2); dy = np.abs(yy - Hh / 2)
        al = np.exp(-dy ** 2 / (2 * 1.5 ** 2)) * (1 - dx) ** 1.5 + np.exp(-dy ** 2 / (2 * 9 ** 2)) * (1 - dx) ** 3 * 0.35
        Image.fromarray(np.dstack([np.broadcast_to(np.array(col, np.float32), (Hh, Wd, 3)), np.clip(al, 0, 1) * 255]).astype(np.uint8), 'RGBA').save(f'{OUT}/type/{nm}.png')


if __name__ == '__main__':
    for n in ('16', '17', '19', '20'): plates(n)
    crops(); clips(); typography()
    json.dump(META, open(f'{OUT}/meta.json', 'w'), indent=1)
