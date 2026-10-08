"""Premium Diwali campaign assets: engraved-gold typography, refined ornaments built from the supplied art, a custom lit
diya, card frames / shadows / scrims, and graded footage (photos, clips, blurred plates, split panels).

    python3 premium_assets.py IMAGES_DIR FONTS_DIR CLIPS_IN_DIR PHOTOS_IN_DIR OUT_DIR

IMAGES_DIR  supplied art: 11.png lotus line, 12.png dotted ring, 13.webp lens flare, 14.webp gold string, 15.webp diya bowl
FONTS_DIR   unpacked @fontsource packages (cinzel, cormorant-garamond, tiro-devanagari-hindi)
CLIPS_IN    the cut clips (diya_macro, thali, ...), PHOTOS_IN the 9:16 photo crops
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

IMG, FONTS, CLIPS_IN, PHOTOS_IN, OUT = sys.argv[1:6]
for d in ('type', 'orn', 'footage', 'clips'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
META = {}


def font(name, w, size):
    f = {'cinzel': f'{FONTS}/fontsource-cinzel-5.3.0/package/files/cinzel-latin-{w}-normal.woff',
         'cormorant': f'{FONTS}/fontsource-cormorant-garamond-5.3.0/package/files/cormorant-garamond-latin-{w}-normal.woff',
         'tiro': f'{FONTS}/fontsource-tiro-devanagari-hindi-5.3.0/package/files/tiro-devanagari-hindi-devanagari-400-normal.woff'}[name]
    return ImageFont.truetype(f, size, layout_engine=ImageFont.Layout.RAQM)


def save(im, rel):
    p = os.path.join(OUT, rel); im.save(p, optimize=True) if p.endswith('.png') else im.convert('RGB').save(p, quality=90); return p


# ------------------------------------------------------------------ materials
GOLD = [(0.0, (255, 243, 205)), (0.38, (238, 196, 112)), (0.52, (214, 160, 70)), (0.62, (236, 192, 104)), (1.0, (150, 96, 30))]
CREAM = [(0.0, (255, 250, 240)), (1.0, (240, 222, 188))]


def vgrad(h, w, stops):
    u = np.linspace(0, 1, h)[:, None]; out = np.zeros((h, w, 3), np.float32)
    pos = [p for p, _ in stops]
    for c in range(3): out[..., c] = np.interp(u, pos, [col[c] for _, col in stops])
    return out


def material(mask, stops, bevel=True, shadow=0.55, glow=0.12, scale=1.0):
    """mask (L image) -> RGBA: metal gradient across the glyph height, a soft top-edge highlight, a real drop shadow and a
    very faint warm bloom. Nothing neon."""
    m = np.asarray(mask).astype(np.float32) / 255; h, w = m.shape
    ys = np.where(m.max(1) > 0.1)[0]; y0, y1 = (ys.min(), ys.max()) if len(ys) else (0, h)
    col = np.zeros((h, w, 3), np.float32); g = vgrad(max(1, y1 - y0 + 1), w, stops); col[y0:y1 + 1] = g; col[:y0] = g[0]; col[y1 + 1:] = g[-1]
    if bevel:   # light catching the top edges, darker bottom edges
        up = np.roll(m, int(2 * scale), 0); dn = np.roll(m, -int(2 * scale), 0)
        col += (np.clip(m - up, 0, 1)[..., None] * 60) - (np.clip(m - dn, 0, 1)[..., None] * 40)
    face = np.dstack([np.clip(col, 0, 255), m * 255]).astype(np.uint8); face = Image.fromarray(face, 'RGBA')
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if glow:
        gl = Image.new('RGBA', (w, h), (255, 170, 70, 0)); gl.putalpha(mask.filter(ImageFilter.GaussianBlur(14 * scale)).point(lambda v: int(v * glow))); out.alpha_composite(gl)
    if shadow:
        sh = Image.new('RGBA', (w, h), (10, 4, 0, 0)); sh.putalpha(mask.filter(ImageFilter.GaussianBlur(5 * scale)).point(lambda v: int(v * shadow)))
        out.alpha_composite(sh, (0, int(4 * scale)))
    out.alpha_composite(face); return out


def text_mask(txt, fnt, tracking=0.0, k=2):
    """render with letter spacing (em) at k x; returns mask, per-character centre x offsets from the text centre (1x px)"""
    asc, desc = fnt.getmetrics(); pad = int(fnt.size * 0.9)
    adv = [fnt.getlength(c) for c in txt]; sp = tracking * fnt.size
    total = sum(adv) + sp * (len(txt) - 1)
    W, H = int(total + 2 * pad), int(asc + desc + 2 * pad)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im); x = pad; centers = []
    for c, a in zip(txt, adv):
        d.text((x, pad), c, font=fnt, fill=255); centers.append((x + a / 2 - W / 2) / k); x += a + sp
    return im, centers


def make_text(name, txt, face, weight, px, tracking=0.0, stops=GOLD, per_letter=False, shadow=0.55, glow=0.12):
    k = 2; fnt = font(face, weight, px * k)
    if face == 'tiro':     # complex script: shape the whole string (no manual spacing)
        asc, desc = fnt.getmetrics(); pad = int(fnt.size * 0.9); w = int(fnt.getlength(txt)) + 2 * pad
        m = Image.new('L', (w, asc + desc + 2 * pad), 0); ImageDraw.Draw(m).text((pad, pad), txt, font=fnt, fill=255); centers = None
    else:
        m, centers = text_mask(txt, fnt, tracking, k)
    bb = m.getbbox(); cy = (bb[1] + bb[3]) / 2; H = m.height
    if per_letter:      # one image per letter, same canvas height: they line up when placed on the same y
        ims = []
        for i, c in enumerate(txt):
            if c == ' ': continue
            lm, _ = text_mask(c, fnt, 0, k); lb = lm.getbbox()
            sub = Image.new('L', (lm.width, H), 0); sub.paste(lm, (0, (H - lm.height) // 2))
            img = material(sub, stops, scale=k, shadow=shadow, glow=glow).resize((lm.width // k, H // k), Image.LANCZOS)
            save(img, f'type/{name}_{i}.png'); ims.append({'file': f'{name}_{i}.png', 'dx': round(centers[i], 1), 'w': img.width})
        META[name] = {'letters': ims, 'dy': round((H / 2 - cy) / k, 1)}
        return
    img = material(m, stops, scale=k, shadow=shadow, glow=glow)
    img = img.resize((img.width // k, img.height // k), Image.LANCZOS)
    save(img, f'type/{name}.png'); META[name] = {'w': img.width, 'h': img.height, 'dy': round((H / 2 - cy) / k, 1), 'centers': centers}


# ------------------------------------------------------------------ ornaments from the supplied art
def recolor(src, stops, size, radial=True, glow=0.0):
    im = Image.open(src).convert('RGBA'); im = im.crop(im.getbbox())
    im = im.resize((size, round(im.height * size / im.width)), Image.LANCZOS); a = im.getchannel('A')
    h, w = im.height, im.width
    if radial:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); r = np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2) / (max(w, h) / 2)
        u = np.clip(r, 0, 1); col = np.zeros((h, w, 3), np.float32)
        for c in range(3): col[..., c] = np.interp(u, [p for p, _ in stops], [s[c] for _, s in stops])
    else: col = vgrad(h, w, stops)
    out = Image.fromarray(np.dstack([col, np.asarray(a)]).astype(np.uint8), 'RGBA')
    if glow:
        g = Image.new('RGBA', out.size, (255, 180, 80, 0)); g.putalpha(a.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * glow)))
        base = Image.new('RGBA', out.size, (0, 0, 0, 0)); base.alpha_composite(g); base.alpha_composite(out); out = base
    return out


def ornaments():
    ring_stops = [(0, (255, 236, 190)), (0.6, (232, 186, 100)), (1, (190, 130, 50))]
    m = recolor(f'{IMG}/11.png', ring_stops, 1100, glow=0.25); A = np.asarray(m).copy(); h, w = A.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]; A[..., 3][np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2) < w * 0.052] = 0      # hollow the solid centre dot
    save(Image.fromarray(A, 'RGBA'), 'orn/lotus_mandala.png')
    r = recolor(f'{IMG}/12.png', ring_stops, 900, glow=0.0); r.putalpha(r.getchannel('A').point(lambda v: min(255, int(v * 2.6)))); save(r, 'orn/dot_ring.png')
    s = Image.open(f'{IMG}/14.webp').convert('RGBA'); s = s.crop(s.getbbox())
    save(s.resize((s.width * 900 // s.height, 900), Image.LANCZOS), 'orn/gold_string.png')
    a = np.asarray(s.getchannel('A')); h = s.height; low = s.crop((0, int(h * 0.9), s.width, h)); low = low.crop(low.getbbox())
    lotus = low.resize((low.width * 44 // low.height, 44), Image.LANCZOS); save(lotus, 'orn/lotus_small.png')
    # divider: a hairline that fades out at both ends, the small lotus in a gap at the centre
    W, H = 620, 60; dv = Image.new('RGBA', (W, H), (0, 0, 0, 0)); xs = np.linspace(-1, 1, W)
    line = np.zeros((H, W, 4), np.float32); line[..., :3] = (226, 184, 104)
    al = np.clip(1 - np.abs(xs) ** 1.6, 0, 1) * (np.abs(xs) > 0.1)
    for dy, f in ((0, 1), (-1, 0.35), (1, 0.35)): line[H // 2 + dy, :, 3] = al * 230 * f
    dv = Image.fromarray(line.astype(np.uint8), 'RGBA'); dv.alpha_composite(lotus, ((W - lotus.width) // 2, (H - lotus.height) // 2 - 4))
    save(dv, 'orn/divider.png')
    fl = Image.open(f'{IMG}/13.webp').convert('RGB'); save(fl.resize((1000, 1000), Image.LANCZOS), 'orn/flare.jpg')


# ------------------------------------------------------------------ the custom diya: supplied bowl + a real flame + light
def flame(w=300, h=700):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cx = w / 2
    v = (h * 0.9 - yy) / (h * 0.78)
    prof = np.where((v > 0) & (v < 1), np.sin(np.clip(v, 0, 1) ** 0.7 * math.pi) ** 0.9 * (1 - 0.45 * np.clip(v, 0, 1)), 0)
    wid = 0.2 * w * prof + 1e-3; d = np.abs(xx - cx) / wid
    body = np.clip(1 - d ** 1.6, 0, 1) * (prof > 0)
    core = np.clip(1 - np.abs(xx - cx) / (wid * 0.5), 0, 1) * np.clip(1 - np.abs(v - 0.3) / 0.32, 0, 1)
    base = np.exp(-((xx - cx) ** 2 / (2 * (w * 0.045) ** 2) + (yy - h * 0.88) ** 2 / (2 * (h * 0.02) ** 2)))
    rgb = np.zeros((h, w, 3), np.float32); rgb[:] = (255, 156, 52)
    t = np.clip(v, 0, 1)[..., None]; rgb = rgb * (1 - t * 0.25) + np.array([255, 110, 30]) * t * 0.25
    rgb = rgb * (1 - core[..., None]) + np.array([255, 248, 225]) * core[..., None]
    rgb = rgb * (1 - base[..., None] * 0.6) + np.array([110, 150, 255]) * base[..., None] * 0.6
    a = np.clip(np.maximum(np.maximum(body * 0.95, core), base * 0.55), 0, 1)
    return Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(w * 0.01))


def glow(size, col, power=2.2, core=None):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32); r = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** power
    rgb = np.zeros((size, size, 3), np.float32); rgb[:] = col
    if core: t = np.clip(1 - r * 3, 0, 1)[..., None]; rgb = rgb * (1 - t) + np.array(core) * t
    return Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), 'RGBA')


def diya():
    b = Image.open(f'{IMG}/15.webp').convert('RGBA'); b = b.crop(b.getbbox()); b = b.resize((900, round(b.height * 900 / b.width)), Image.LANCZOS)
    a = np.asarray(b.getchannel('A')); rows = np.where((a > 200).sum(1) > b.width * 0.25)[0]
    rim = rows.min() / b.height                       # top of the rim as a fraction of the bowl image height
    save(b, 'orn/diya_bowl.png'); save(flame(), 'orn/flame.png')
    save(glow(700, (255, 160, 60), 2.0, (255, 230, 180)), 'orn/glow_warm.png')
    sh = glow(800, (0, 0, 0), 1.4); sh = sh.resize((800, 160)); save(sh, 'orn/floor_shadow.png')
    META['diya'] = {'rim': round(rim, 4), 'aspect': round(b.height / b.width, 4)}


# ------------------------------------------------------------------ compositing pieces
def card_pieces(cw=600, ch=1067):
    fr = Image.new('RGBA', (cw + 12, ch + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
    d.rectangle([5, 5, cw + 6, ch + 6], outline=(226, 186, 110, 235), width=2)
    for (x, y, sx, sy) in [(5, 5, 1, 1), (cw + 6, 5, -1, 1), (5, ch + 6, 1, -1), (cw + 6, ch + 6, -1, -1)]:   # corner ticks
        d.line([(x, y), (x + sx * 26, y)], fill=(255, 226, 160, 255), width=4); d.line([(x, y), (x, y + sy * 26)], fill=(255, 226, 160, 255), width=4)
    save(fr, 'orn/card_frame.png')
    sh = Image.new('L', (cw + 240, ch + 240), 0); ImageDraw.Draw(sh).rectangle([120, 140, cw + 120, ch + 140], fill=210)
    sh = sh.filter(ImageFilter.GaussianBlur(40)); out = Image.new('RGBA', sh.size, (0, 0, 0, 0)); out.putalpha(sh); save(out, 'orn/card_shadow.png')
    for name, top in (('scrim_bottom', False), ('scrim_top', True)):
        h = 760; u = np.linspace(0, 1, h)[:, None]; al = (u ** 1.5 if not top else (1 - u) ** 1.5) * 0.82
        im = np.zeros((h, 720, 4), np.float32); im[..., 3] = np.broadcast_to(al * 255, (h, 720)); save(Image.fromarray(im.astype(np.uint8), 'RGBA'), f'orn/{name}.png')
    # anamorphic streak, restrained
    W, H = 2000, 120; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); dx = np.abs(xx - W / 2) / (W / 2); dy = np.abs(yy - H / 2)
    al = np.exp(-dy ** 2 / (2 * 1.6 ** 2)) * (1 - dx) ** 1.6 * 0.9 + np.exp(-dy ** 2 / (2 * 12 ** 2)) * (1 - dx) ** 3 * 0.3
    t = np.clip(np.exp(-dy ** 2 / 8), 0, 1)[..., None]; rgb = np.array([255, 190, 110]) * (1 - t) + np.array([255, 246, 230]) * t
    save(Image.fromarray(np.dstack([np.broadcast_to(rgb, (H, W, 3)), al * 255]).astype(np.uint8), 'RGBA'), 'orn/streak.png')


# ------------------------------------------------------------------ footage: one grade for everything
def grade_img(im):
    a = np.asarray(im.convert('RGB')).astype(np.float32) / 255
    a = a ** 1.06                                                         # a touch more density
    lum = a.mean(2, keepdims=True)
    a = a + (np.array([0.035, 0.008, -0.04]) * (1 - lum)) + (np.array([0.02, 0.005, -0.03]) * lum)   # warm shadows + highlights
    a = (a - 0.5) * 1.07 + 0.5; a = lum + (a - lum) * 0.96                # gentle contrast, slightly calmer colour
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


GRADE = "eq=contrast=1.07:gamma=0.95:saturation=0.97,colorbalance=rs=0.035:gs=0.008:bs=-0.04:rh=0.02:gh=0.005:bh=-0.03"


def footage():
    for f in sorted(os.listdir(PHOTOS_IN)):
        if not f.endswith('.jpg'): continue
        im = grade_img(Image.open(os.path.join(PHOTOS_IN, f))).resize((720, 1280), Image.LANCZOS); save(im, f'footage/{f}')
        if f in ('rangoli_marigold.jpg', 'diya_rangoli.jpg'):              # split-layout panels (720 x 632)
            big = grade_img(Image.open(os.path.join(PHOTOS_IN, f))); W, H = big.size; ph = W * 632 / 720
            save(big.crop((0, (H - ph) / 2, W, (H + ph) / 2)).resize((720, 632), Image.LANCZOS), f'footage/panel_{f}')
    for f in sorted(os.listdir(CLIPS_IN)):
        if not f.endswith('.mp4'): continue
        n = f[:-4]; src = os.path.join(CLIPS_IN, f)
        overlay = n in ('bokeh_loop', 'particle_ring', 'dust_a', 'dust_b')
        vf = 'null' if overlay else GRADE
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-an', '-vf', vf, '-c:v', 'libx264', '-crf', '22', '-g', '15', '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart', os.path.join(OUT, 'clips', f)], check=True)
        if n in ('diya_ring', 'women', 'diya_macro'):                        # blurred, darker plate behind a framed card
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-an', '-vf', GRADE + ',gblur=sigma=26,eq=brightness=-0.08:saturation=0.85,scale=360:640',
                            '-c:v', 'libx264', '-crf', '26', '-g', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(OUT, 'clips', n + '_plate.mp4')], check=True)
        print('clip', n)


def typography():
    make_text('this_diwali', 'THIS DIWALI', 'cinzel', 500, 44, 0.32)
    for w in ('LIGHT', 'LOVE', 'CELEBRATE'): make_text('w_' + w.lower(), w, 'cinzel', 600, 92, 0.12, CREAM, shadow=0.7, glow=0.06)
    make_text('diwali', 'DIWALI', 'cinzel', 700, 150, 0.06, per_letter=True)
    make_text('festival', 'FESTIVAL OF LIGHTS', 'cormorant', 600, 30, 0.42, CREAM, shadow=0.6, glow=0.0)
    for w in ('LIGHT', 'JOY', 'TOGETHERNESS'): make_text('tag_' + w.lower(), w, 'cormorant', 600, 34, 0.3, CREAM, shadow=0.7, glow=0.0)
    make_text('tag_dot', '•', 'cormorant', 600, 34, 0, GOLD, shadow=0.5, glow=0.0)
    make_text('happy', 'HAPPY', 'cormorant', 600, 46, 0.55, CREAM, shadow=0.7, glow=0.0)
    make_text('diwali_final', 'DIWALI', 'cinzel', 700, 128, 0.08)
    make_text('shubh', 'शुभ दीपावली', 'tiro', 400, 50, 0, GOLD, shadow=0.6, glow=0.08)


if __name__ == '__main__':
    only = os.environ.get('ONLY')
    if only: [globals()[f]() for f in only.split(',')]; json.dump(dict(json.load(open(os.path.join(OUT, 'meta.json'))), **META), open(os.path.join(OUT, 'meta.json'), 'w'), indent=1); sys.exit()
    typography(); ornaments(); diya(); card_pieces(); footage()
    json.dump(META, open(os.path.join(OUT, 'meta.json'), 'w'), indent=1); print('meta', list(META))
