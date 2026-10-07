"""Diwali montage: light-based VFX elements (no cartoon art) and premium placeholder cards for the footage slots.

    python3 diwali_assets.py OUTDIR

OUTDIR/vfx/*.png       transparent light elements (particles, flame, bloom, streaks, fireworks, trails, mandala, dust)
OUTDIR/holders/*.jpg   1080x1920 dark-gold slot cards: what to film / drop in, shot number, length on screen
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else 'diwali_assets'
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'KBebas.ttf')
GOLD, AMBER, SAFFRON, EMBER, CREAM = (232, 190, 110), (255, 170, 60), (255, 128, 30), (200, 40, 20), (255, 236, 200)


def save(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    (im.convert('RGB').save(path, quality=90) if path.endswith('.jpg') else im.save(path, optimize=True)); print('wrote', path, im.size)


def rgba(rgb_arr, a):
    """float rgb (h, w, 3) 0..255 + alpha (h, w) 0..1 -> RGBA image (light: colour stays bright where alpha is low)"""
    out = np.zeros(a.shape + (4,), np.float32); out[..., :3] = rgb_arr; out[..., 3] = np.clip(a, 0, 1) * 255
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')


def glow_layer(h, w, pts, col_fn):
    """sum of gaussian light blobs: pts [(x, y, sigma, intensity)] -> RGBA with additive-looking falloff"""
    acc = np.zeros((h, w), np.float32); col = np.zeros((h, w, 3), np.float32)
    for x, y, s, inten, c in pts:
        r = int(s * 3.2) + 2; x0, x1, y0, y1 = max(0, int(x - r)), min(w, int(x + r)), max(0, int(y - r)), min(h, int(y + r))
        if x1 <= x0 or y1 <= y0: continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * s * s)) * inten
        acc[y0:y1, x0:x1] += g; col[y0:y1, x0:x1] += g[..., None] * np.array(c, np.float32)
    rgb = col / np.maximum(acc, 1e-6)[..., None]
    a = 1 - np.exp(-acc * 1.6)                   # soft saturation: overlapping light gets brighter, never clips hard
    rgb = rgb + (255 - rgb) * np.clip(acc - 1.2, 0, 1)[..., None] * 0.6   # hot cores go towards white
    return rgba(rgb, a)


# ---------------------------------------------------------------- particles (3 depth layers, taller than the frame so they can drift)
def particles(w, h, n, smin, smax, seed, bright=1.0):
    rs = np.random.RandomState(seed); pts = []
    for _ in range(n):
        s = rs.uniform(smin, smax); c = [GOLD, AMBER, CREAM, SAFFRON][rs.randint(4)]
        pts.append((rs.uniform(0, w), rs.uniform(0, h), s, rs.uniform(0.35, 1.0) * bright, c))
    return glow_layer(h, w, pts, None)


def flame(w=360, h=640):
    """realistic candle / diya flame: blue root, white-hot core, amber body, soft halo"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cx = w / 2
    v = (h * 0.86 - yy) / (h * 0.62)                                   # 0 at base .. 1 at tip
    width = np.where(v > 0, 0.20 * w * np.sin(np.clip(v, 0, 1) * math.pi) ** 0.75 * (1 - 0.35 * np.clip(v, 0, 1)), 0)
    d = np.abs(xx - cx) / np.maximum(width, 1e-3)
    body = np.clip(1 - d, 0, 1) ** 0.8 * ((v > 0) & (v < 1))
    core = np.clip(1 - np.abs(xx - cx) / np.maximum(width * 0.45, 1e-3), 0, 1) * np.clip(1 - np.abs(v - 0.28) / 0.3, 0, 1)
    root = np.exp(-((xx - cx) ** 2 / (2 * (w * 0.05) ** 2) + (yy - h * 0.84) ** 2 / (2 * (h * 0.025) ** 2)))
    halo = np.exp(-((xx - cx) ** 2 + ((yy - h * 0.55) * 0.75) ** 2) / (2 * (w * 0.32) ** 2))
    rgb = np.zeros((h, w, 3), np.float32)
    amber = np.array([255, 150, 40], np.float32); white = np.array([255, 245, 215], np.float32); blue = np.array([90, 140, 255], np.float32)
    rgb[:] = amber
    rgb = rgb * (1 - core[..., None]) + white * core[..., None]
    rgb = rgb * (1 - root[..., None] * 0.7) + blue * root[..., None] * 0.7
    a = np.maximum(np.maximum(body, core), root * 0.6)
    a = np.maximum(a, halo * 0.35)
    im = rgba(rgb, a)
    return im.filter(ImageFilter.GaussianBlur(w * 0.012))


def bloom(size=1400, col=AMBER, core=CREAM):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32); c = size / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    a = np.exp(-r * r * 6) * 0.9 + np.exp(-r * 2.2) * 0.35
    t = np.clip(np.exp(-r * r * 30), 0, 1)[..., None]
    rgb = np.array(col, np.float32) * (1 - t) + np.array(core, np.float32) * t
    return rgba(np.broadcast_to(rgb, (size, size, 3)), a)


def streak(w=2400, h=260, col=AMBER):
    """anamorphic light streak: thin white core, long amber falloff, a soft central flare"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cx, cy = w / 2, h / 2
    dx, dy = np.abs(xx - cx) / (w / 2), np.abs(yy - cy)
    line = np.exp(-dy ** 2 / (2 * 2.2 ** 2)) * (1 - dx) ** 1.4
    wide = np.exp(-dy ** 2 / (2 * 16 ** 2)) * (1 - dx) ** 3 * 0.55
    flare = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 60 ** 2)) * 0.9
    a = np.clip(line + wide + flare, 0, 1)
    t = np.clip(line * 1.2 + flare, 0, 1)[..., None]
    rgb = np.array(col, np.float32) * (1 - t) + np.array([255, 250, 235], np.float32) * t
    return rgba(np.broadcast_to(rgb, (h, w, 3)).copy(), a)


def sweep(w=1600, h=2600):
    """diagonal golden light band used for the big reveal sweep"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = ((xx - w / 2) * math.cos(math.radians(70)) + (yy - h / 2) * math.sin(math.radians(70)))
    a = np.exp(-d ** 2 / (2 * 120 ** 2)) * 0.85 + np.exp(-d ** 2 / (2 * 14 ** 2)) * 0.6
    t = np.clip(np.exp(-d ** 2 / (2 * 20 ** 2)), 0, 1)[..., None]
    rgb = np.array(AMBER, np.float32) * (1 - t) + np.array(CREAM, np.float32) * t
    return rgba(np.broadcast_to(rgb, (h, w, 3)).copy(), np.clip(a, 0, 1))


def firework(size=1200, col=AMBER, seed=1, n=90):
    """peony burst: glowing trails from the centre that droop with gravity, sparkle heads, faint smoke glow"""
    rs = np.random.RandomState(seed); c = size / 2; pts = []
    for i in range(n):
        ang = 2 * math.pi * i / n + rs.uniform(-0.03, 0.03); L = size * rs.uniform(0.32, 0.46)
        steps = 46
        for j in range(steps):
            u = j / (steps - 1); r = L * (1 - (1 - u) ** 2)
            x = c + r * math.cos(ang); y = c + r * math.sin(ang) + (u ** 2.2) * size * 0.07
            inten = (0.18 + 0.82 * u ** 2.5) * rs.uniform(0.8, 1.1)
            s = 1.6 + 2.2 * u
            col_j = tuple(int(col[k] + (255 - col[k]) * (u ** 6) * 0.8) for k in range(3))
            pts.append((x, y, s, inten, col_j))
        pts.append((c + L * math.cos(ang), c + L * math.sin(ang) + size * 0.07, 5.5, 1.2, (255, 248, 230)))
    pts.append((c, c, size * 0.12, 0.35, col))
    return glow_layer(size, size, pts, None)


def trail_arc(w=1400, h=900, col=AMBER, seed=2):
    """a firework trail curving across: bright head, tapering glowing tail, sparks shedding off"""
    rs = np.random.RandomState(seed); pts = []
    for i in range(260):
        u = i / 259; ang = math.pi * (1.05 - 0.9 * u)
        x = w / 2 + w * 0.44 * math.cos(ang); y = h * 0.92 - h * 0.8 * math.sin(ang)
        pts.append((x, y, 2 + 5 * u, 0.12 + 0.9 * u ** 3, col))
        if rs.rand() < 0.35: pts.append((x + rs.uniform(-18, 18), y + rs.uniform(0, 30), 1.6, rs.uniform(0.3, 0.8), CREAM))
    x = w / 2 + w * 0.44 * math.cos(math.pi * 0.15); y = h * 0.92 - h * 0.8 * math.sin(math.pi * 0.15)
    pts.append((x, y, 16, 1.4, (255, 250, 235)))
    return glow_layer(h, w, pts, None)


def mandala_line(size=1400, col=GOLD, alpha=0.9):
    def draw(im, k):
        d = ImageDraw.Draw(im); c = size * k / 2; R = c * 0.98; lw = max(1, int(1.6 * k))
        for j, (rr, n) in enumerate([(1.0, 48), (0.84, 36), (0.7, 24), (0.56, 16), (0.42, 12), (0.28, 8)]):
            r1 = R * rr; r0 = r1 * 0.72
            for i in range(n):
                a = 2 * math.pi * (i + 0.5 * (j % 2)) / n; wd = r1 * (0.6 * math.pi / n)
                pts = []
                for t in range(0, 31):
                    u = t / 30; r = r0 + (r1 - r0) * u; wv = wd * math.sin(math.pi * u) ** 0.9
                    pts.append((c + r * math.cos(a) - wv * math.sin(a), c + r * math.sin(a) + wv * math.cos(a)))
                for t in range(30, -1, -1):
                    u = t / 30; r = r0 + (r1 - r0) * u; wv = wd * math.sin(math.pi * u) ** 0.9
                    pts.append((c + r * math.cos(a) + wv * math.sin(a), c + r * math.sin(a) - wv * math.cos(a)))
                d.line(pts + [pts[0]], fill=col + (int(255 * alpha),), width=lw)
            d.ellipse([c - r0, c - r0, c + r0, c + r0], outline=col + (int(200 * alpha),), width=lw)
            for i in range(n * 2):
                a = 2 * math.pi * i / (n * 2); rd = r1 * 1.0; s = 1.6 * k
                d.ellipse([c + rd * math.cos(a) - s, c + rd * math.sin(a) - s, c + rd * math.cos(a) + s, c + rd * math.sin(a) + s], fill=col + (int(255 * alpha),))
    k = 2; im = Image.new('RGBA', (size * k, size * k), (0, 0, 0, 0)); draw(im, k)
    im = im.resize((size, size), Image.LANCZOS)
    glow = im.filter(ImageFilter.GaussianBlur(6)); out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.alpha_composite(glow); out.alpha_composite(im)
    return out


def dust_burst(size=1400, seed=5):
    """gold dust exploding outward (particle transition)"""
    rs = np.random.RandomState(seed); c = size / 2; pts = []
    for _ in range(1400):
        ang = rs.uniform(0, 2 * math.pi); r = size * 0.48 * rs.rand() ** 0.55
        pts.append((c + r * math.cos(ang), c + r * math.sin(ang) * 0.8, rs.uniform(1.2, 4.5), rs.uniform(0.3, 1.0) * (0.4 + 0.6 * r / (size * 0.48)), [GOLD, AMBER, CREAM][rs.randint(3)]))
    return glow_layer(size, size, pts, None)


def gold_rule(w=900, h=40):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = np.abs(xx - w / 2) / (w / 2); dy = np.abs(yy - h / 2)
    a = np.exp(-dy ** 2 / (2 * 1.4 ** 2)) * (1 - dx ** 2) + np.exp(-dy ** 2 / (2 * 7 ** 2)) * (1 - dx) ** 2 * 0.35
    return rgba(np.broadcast_to(np.array(GOLD, np.float32), (h, w, 3)).copy(), a)


# ---------------------------------------------------------------- placeholder cards
def holder(num, kind, title, hint, seconds, tone=(40, 22, 10), seed=1):
    W, H = 1080, 1920; rs = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - W * 0.5) ** 2 + (yy - H * 0.45) ** 2) / (H * 0.7)
    base = np.array(tone, np.float32) * (1.25 - r)[..., None].clip(0.15, 1.3)
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    bok = particles(W, H, 26, 14, 60, seed + 40, 0.5); a = bok.getchannel('A').point(lambda v: int(v * 0.5)); bok.putalpha(a); im.alpha_composite(bok)
    d = ImageDraw.Draw(im); g = (214, 178, 108, 255); gs = (214, 178, 108, 120)
    m = 70; d.rectangle([m, m, W - m, H - m], outline=gs, width=2)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line([(x, y), (x + sx * 90, y)], fill=g, width=5); d.line([(x, y), (x, y + sy * 90)], fill=g, width=5)
    f_big, f_mid, f_small = ImageFont.truetype(FONT, 230), ImageFont.truetype(FONT, 76), ImageFont.truetype(FONT, 44)

    def ctext(y, s, f, col):
        bb = d.textbbox((0, 0), s, font=f); d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], y), s, font=f, fill=col)
    d.text((m + 30, m + 24), f'{num:02d}', font=f_mid, fill=(214, 178, 108, 150))
    d.text((m + 30, m + 108), f'{kind} HOLDER', font=f_small, fill=(214, 178, 108, 150))
    words, line, lines = title.upper().split(), '', []
    for w_ in words:
        if d.textlength((line + ' ' + w_).strip(), font=f_small) > W - 260: lines.append(line); line = w_
        else: line = (line + ' ' + w_).strip()
    lines.append(line)
    y0 = H - m - 300
    d.line([(W / 2 - 120, y0 - 26), (W / 2 + 120, y0 - 26)], fill=(214, 178, 108, 120), width=2)
    for i, ln in enumerate(lines): ctext(y0 + i * 52, ln, f_small, (255, 236, 200, 170))
    ctext(y0 + len(lines) * 52 + 6, hint.upper(), ImageFont.truetype(FONT, 34), (214, 178, 108, 130))
    ctext(H - m - 70, f'ON SCREEN {seconds:.2f} S  //  REPLACE ME', ImageFont.truetype(FONT, 30), (214, 178, 108, 110))
    return im


SHOTS = [   # num, kind, title, hint, seconds, tone
    (1, 'VIDEO', 'Diya close-up in darkness', 'macro, flame catches, shallow focus', 2.97, (26, 14, 6)),
    (2, 'VIDEO', 'Diya flame', 'tight on the wick, warm', 0.41, (46, 24, 8)),
    (3, 'VIDEO', 'Rangoli top-down', 'slow slide over colours', 0.41, (42, 18, 22)),
    (4, 'PHOTO', 'Marigold flowers', 'garland, shallow depth', 0.82, (48, 26, 6)),
    (5, 'PHOTO', 'Mithai / sweets', 'kaju katli, ladoo on brass plate', 0.58, (44, 28, 10)),
    (6, 'VIDEO', 'Festive decorations', 'lanterns, fairy lights bokeh', 0.66, (30, 16, 24)),
    (7, 'VIDEO', 'Hands lighting diyas', 'slow emotional shot, match cut', 0.41, (40, 20, 8)),
    (8, 'VIDEO', 'People in traditional clothing', 'sarees, kurtas, walking to camera', 0.82, (44, 16, 14)),
    (9, 'VIDEO', 'Exchanging gifts', 'hands, smiles, wrapped boxes', 0.82, (40, 22, 12)),
    (10, 'VIDEO', 'Family celebrating', 'laughing, sparklers', 1.64, (46, 20, 10)),
    (11, 'VIDEO', 'Night bokeh background', 'out of focus lights for the DIWALI title', 3.29, (20, 10, 6)),
    (12, 'VIDEO', 'Fireworks in the sky', 'wide, big burst', 0.41, (16, 10, 24)),
    (13, 'VIDEO', 'Rows of diyas', 'long lens, rack focus', 0.41, (36, 18, 6)),
    (14, 'VIDEO', 'Family celebration', 'group hug, candid', 0.41, (40, 18, 12)),
    (15, 'PHOTO', 'Sweets close-up', 'silver varq, macro', 0.41, (44, 28, 10)),
    (16, 'PHOTO', 'Rangoli with diyas', 'top-down, glowing', 0.41, (42, 16, 20)),
    (17, 'VIDEO', 'City lights at night', 'skyline or lit street, slow pan', 0.41, (14, 14, 30)),
    (18, 'VIDEO', 'Smiling faces', 'close-up, diya light on skin', 0.41, (44, 22, 12)),
    (19, 'VIDEO', 'Fireworks finale', 'sparkler or anaar fountain', 0.41, (24, 12, 20)),
    (20, 'VIDEO', 'Hero: Diwali night scene', 'courtyard of diyas, fireworks behind', 3.89, (22, 12, 6)),
]


def main():
    vfx, hold = os.path.join(OUT, 'vfx'), os.path.join(OUT, 'holders')
    els = {
        'particles_far': particles(1080, 2600, 140, 2, 6, 1, 0.7), 'particles_mid': particles(1080, 2600, 70, 5, 12, 2, 0.8),
        'particles_near': particles(1080, 2600, 22, 14, 34, 3, 0.55), 'flame': flame(), 'bloom': bloom(), 'streak': streak(),
        'sweep': sweep(), 'firework_gold': firework(1200, AMBER, 1), 'firework_saffron': firework(1200, SAFFRON, 2, 70),
        'firework_ember': firework(1200, EMBER, 3, 80), 'trail_arc': trail_arc(), 'trail_arc_b': trail_arc(1400, 900, SAFFRON, 7),
        'mandala_gold': mandala_line(), 'dust_burst': dust_burst(), 'gold_rule': gold_rule(),
    }
    for k, v in els.items(): save(v, os.path.join(vfx, k + '.png'))
    for n, kind, title, hint, sec, tone in SHOTS:
        save(holder(n, kind, title, hint, sec, tone, n), os.path.join(hold, f'holder_{n:02d}.jpg'))


if __name__ == '__main__':
    main()
