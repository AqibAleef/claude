"""Prepare the real Diwali media: cut clips from the source video, crop the photos to 9:16, clean the zip elements.

    python3 media_prep.py SOURCE_VIDEO PHOTOS_DIR ELEMENTS_DIR OUT_DIR [SHEETS_DIR PARTICLES_DIR]

SHEETS_DIR holds the element sheets (6-10.webp), PARTICLES_DIR the particle overlay videos (black background).

OUT_DIR/clips/*.mp4     720x1280, no audio, short GOP (seeks cleanly in the Studio and KineMaster)
OUT_DIR/photos/*.jpg    1080x1920 crops around the subject
OUT_DIR/elements/*.png  cleaned cut-outs (stray specks removed, baked backgrounds masked away)
"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

SRC, PHOTOS, ELEMS, OUT = sys.argv[1:5]

CLIPS = {   # name: (start s in the source, length s)   source scenes: 0-7.3 anaar, 7.3-21.3 aerial fireworks,
    'diya_macro': (57.35, 1.2),      # 21.3-36.6 sky over the horizon, 37.8 women + candles, 41.5 girl with thali,
    'thali': (41.5, 3.9),            # 45.9 woman with sparkler, 51.9 diya ring top-down, 57.3 diya macro / sparklers
    'diya_ring': (52.0, 3.7),
    'women': (37.8, 3.6),
    'sparkler_woman': (46.0, 4.2),
    'sky_wide': (26.5, 3.6),
    'fw_purple': (7.4, 1.0),
    'fw_orange': (9.3, 1.0),
    'sky_city': (32.0, 1.0),
    'anaar': (2.0, 3.0),
}
PHOTO_FOCUS = {   # file: (output name, focus x, focus y) in source pixels
    '1.jpg': ('diya_dark', 530, 1490), '2.jpg': ('diya_rows', 1000, 700), '3.jpg': ('rangoli_marigold', 800, 1050),
    '4.jpg': ('diya_rangoli', 790, 950), '5.jpg': ('hands_lighting', 1300, 650),
}


def clips():
    d = os.path.join(OUT, 'clips'); os.makedirs(d, exist_ok=True)
    for name, (ss, dur) in CLIPS.items():
        dst = os.path.join(d, name + '.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-t', str(dur), '-i', SRC, '-an', '-vf', 'scale=720:1280,setsar=1',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-g', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst], check=True)
        print('clip', dst, os.path.getsize(dst) // 1024, 'KB')


def crop916(im, fx, fy):
    W, H = im.size; tw, th = (H * 9 / 16, H) if W / H > 9 / 16 else (W, W * 16 / 9)
    x0 = min(max(fx - tw / 2, 0), W - tw); y0 = min(max(fy - th / 2, 0), H - th)
    return im.crop((round(x0), round(y0), round(x0 + tw), round(y0 + th))).resize((1080, 1920), Image.LANCZOS)


def photos():
    d = os.path.join(OUT, 'photos'); os.makedirs(d, exist_ok=True)
    for f, (name, fx, fy) in PHOTO_FOCUS.items():
        im = Image.open(os.path.join(PHOTOS, f)).convert('RGB')
        crop916(im, fx, fy).save(os.path.join(d, name + '.jpg'), quality=90); print('photo', name)


def largest_part(im):
    """keep the biggest opaque blob (drops stray specks)"""
    a = np.asarray(im.getchannel('A')) > 40; h, w = a.shape
    lab = np.zeros((h, w), np.int32); n = 0; sizes = {}
    for y in range(h):
        for x in range(w):
            if a[y, x] and not lab[y, x]:
                n += 1; st = [(y, x)]; lab[y, x] = n; c = 0
                while st:
                    yy, xx = st.pop(); c += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = yy + dy, xx + dx
                        if 0 <= ny < h and 0 <= nx < w and a[ny, nx] and not lab[ny, nx]: lab[ny, nx] = n; st.append((ny, nx))
                sizes[n] = c
    keep = max(sizes, key=sizes.get)
    m = Image.fromarray(((lab == keep) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    out = im.copy(); out.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel('A')), np.asarray(m))))
    return out.crop(out.getbbox())


def soft_round(im, cx, cy, r, feather):
    h, w = im.height, im.width; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    m = np.clip((r - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)) / feather, 0, 1)
    out = im.copy(); out.putalpha(Image.fromarray((np.asarray(im.getchannel('A')) * m).astype(np.uint8)))
    return out.crop(out.getbbox())


def elements():
    d = os.path.join(OUT, 'elements'); os.makedirs(d, exist_ok=True)
    diya = largest_part(Image.open(os.path.join(ELEMS, 'diya.png')).convert('RGBA'))
    diya.save(os.path.join(d, 'diya.png'))
    rang = Image.open(os.path.join(ELEMS, 'rangoli.png')).convert('RGBA')
    soft_round(rang, 245, 168, 168, 40).save(os.path.join(d, 'rangoli_medallion.png'))
    lan = Image.open(os.path.join(ELEMS, 'lanterns.png')).convert('RGBA')
    right = lan.crop((326, 0, lan.width, 360))           # the right-hand lantern is clear of the baked backdrop
    a = np.asarray(right).astype(np.float32); al = a[..., 3].copy()
    lum = a[..., :3].mean(2)
    pad = np.pad(lum, 5, mode='edge'); win = np.lib.stride_tricks.sliding_window_view(pad, (11, 11))
    smooth = win.std(axis=(2, 3)) < 7                    # the baked backdrop is a smooth gradient; the lantern is fine detail
    al[smooth & (lum < 175)] = 0                          # (the glowing glass is smooth too, but much brighter)
    right.putalpha(Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.MedianFilter(5)))
    right = largest_part(right.crop((22, 0, right.width, right.height)))
    right.save(os.path.join(d, 'lantern.png'))
    for n in ('diya', 'rangoli_medallion', 'lantern'): print('element', n, Image.open(os.path.join(d, n + '.png')).size)


SHEET_ELEMENTS = {   # name: (sheet, cell (col, row) on the 3x2 grid sheets, or None for a single-element sheet)
    'title_happy_diwali': ('8', (0, 0)), 'fireworks_gold': ('8', (1, 0)), 'fireworks_multi': ('7', (2, 0)), 'diya_swirl': ('7', (1, 0)),
    'mandala_redgold': ('8', (0, 1)), 'lanterns': ('8', (1, 1)), 'swirl_wave': ('8', (2, 1)), 'swirl_s': ('7', (2, 1)),
    'arc': ('9', None), 'rangoli_diyas': ('10', None),
}
PARTICLES = {   # name: (source file, brightness gain, square output side or None for 9:16)
    'bokeh_loop': ('Bokeh_Particular_Loop.mp4', 5.0, 900), 'particle_ring': ('Main_Particle_03.mp4', 2.6, 900),
    'dust_a': ('Particles_01.mp4', 1.8, None), 'dust_b': ('Particles_02.mp4', 2.5, None),
}


def sheet_elements(sheet_dir):
    """cut each element out of the sheets, trim to its own pixels so it sits centred on its anchor"""
    d = os.path.join(OUT, 'elements'); os.makedirs(d, exist_ok=True)
    for name, (sheet, cell) in SHEET_ELEMENTS.items():
        im = Image.open(os.path.join(sheet_dir, sheet + '.webp')).convert('RGBA')
        if cell:
            cw, ch = im.width / 3, im.height / 2; c, r = cell
            im = im.crop((round(c * cw) + 12, round(r * ch) + 12, round((c + 1) * cw) - 12, round((r + 1) * ch) - 12))
        a = np.asarray(im.getchannel('A')); ys, xs = np.where(a > 10)
        im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        im.save(os.path.join(d, name + '.png')); print('element', name, im.size)


def particle_clips(src_dir, secs=4.2):
    d = os.path.join(OUT, 'clips'); os.makedirs(d, exist_ok=True)
    for name, (f, gain, side) in PARTICLES.items():
        vf = (f'crop=min(iw\\,ih):min(iw\\,ih),scale={side}:{side}' if side else 'scale=720:1280') + f',format=rgb24,lutrgb=r=val*{gain}:g=val*{gain}:b=val*{gain},format=yuv420p'
        dst = os.path.join(d, name + '.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-t', str(secs), '-i', os.path.join(src_dir, f), '-an', '-vf', vf, '-c:v', 'libx264', '-preset', 'medium',
                        '-crf', '24', '-g', '15', '-movflags', '+faststart', dst], check=True)
        print('particles', dst, os.path.getsize(dst) // 1024, 'KB')


if __name__ == '__main__':
    clips(); photos(); elements()
    if len(sys.argv) > 6: sheet_elements(sys.argv[5]); particle_clips(sys.argv[6])
