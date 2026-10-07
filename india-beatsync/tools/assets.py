"""India beat-sync: backgrounds, stickers and poster-style scene cards, all drawn here (no stock downloads needed).

    python3 assets.py OUTDIR

Writes OUTDIR/backgrounds/*.jpg (1080x1920), OUTDIR/stickers/*.png (transparent) and OUTDIR/scenes/*.jpg
(1080x1920 illustrated stand-ins for the photo slots; swap them for Pexels / Pixabay shots any time).
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = sys.argv[1] if len(sys.argv) > 1 else 'assets'
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'KBebas.ttf')
W, H = 1080, 1920

# ---------------------------------------------------------------- palette
SAFFRON, DEEP_SAFFRON, TURMERIC, MARIGOLD = '#FF9933', '#F26B1D', '#F5B700', '#FFA41B'
RANI, SINDOOR, MAROON = '#E5197A', '#E03A1E', '#5E0B1E'
PEACOCK, TEAL, INDIGO, NAVY = '#0B6E8A', '#0F9D8A', '#2E2A7F', '#0A1A5C'
GREEN, LEAF, GOLD, CREAM, INK, WHITE = '#138808', '#2F7D32', '#E8B321', '#FFF4E0', '#160B12', '#FFFFFF'


def rgb(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def grad(w, h, stops, angle=135):
    """linear gradient, stops [(pos, hex)], angle in degrees (0 = left to right, 90 = top to bottom)"""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angle); d = (x - w / 2) * math.cos(a) + (y - h / 2) * math.sin(a)
    L = abs(w / 2 * math.cos(a)) + abs(h / 2 * math.sin(a)); u = np.clip(d / (2 * L) + 0.5, 0, 1)
    out = np.zeros((h, w, 3), np.float32)
    pos = [p for p, _ in stops]; cols = [np.array(rgb(c)[:3], np.float32) for _, c in stops]
    for c in range(3): out[..., c] = np.interp(u, pos, [col[c] for col in cols])
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGB')


def radial_glow(w, h, cx, cy, r, color, strength=0.6):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    layer = np.zeros((h, w, 4), np.float32); layer[..., :3] = rgb(color)[:3]; layer[..., 3] = a * 255
    return Image.fromarray(layer.astype(np.uint8), 'RGBA')


def noise_grain(img, amt=6, seed=1):
    rs = np.random.RandomState(seed); a = np.asarray(img).astype(np.int16)
    n = rs.randint(-amt, amt + 1, a.shape[:2])[..., None]; a[..., :3] = (a[..., :3] + n).clip(0, 255)
    return Image.fromarray(a.astype(np.uint8), img.mode)


def canvas(w, h): return Image.new('RGBA', (w, h), (0, 0, 0, 0))


def ss(draw_fn, w, h, k=2):
    """supersampled drawing: draw at k x then shrink (clean edges)"""
    im = canvas(w * k, h * k); draw_fn(im, k); return im.resize((w, h), Image.LANCZOS)


def poly_circle(cx, cy, r, n=96, start=0):
    return [(cx + r * math.cos(start + 2 * math.pi * i / n), cy + r * math.sin(start + 2 * math.pi * i / n)) for i in range(n)]


def petal(cx, cy, r0, r1, ang, width, n=24):
    """a pointed petal from radius r0 to r1 along angle ang"""
    pts = []
    for i in range(n + 1):
        t = i / n; r = r0 + (r1 - r0) * t; wv = width * math.sin(math.pi * t) ** 0.8
        pts.append((cx + r * math.cos(ang) - wv * math.sin(ang), cy + r * math.sin(ang) + wv * math.cos(ang)))
    for i in range(n, -1, -1):
        t = i / n; r = r0 + (r1 - r0) * t; wv = width * math.sin(math.pi * t) ** 0.8
        pts.append((cx + r * math.cos(ang) + wv * math.sin(ang), cy + r * math.sin(ang) - wv * math.cos(ang)))
    return pts


def save(im, path, q=90):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith('.jpg'): im.convert('RGB').save(path, quality=q, optimize=True)
    else: im.save(path, optimize=True)
    print('wrote', path, im.size)


# ================================================================ stickers
def mandala(size=900, col=GOLD, col2=None, seed=3, outline=False):
    col2 = col2 or col

    def draw(im, k):
        d = ImageDraw.Draw(im); c = size * k / 2; R = c * 0.98
        rings = [(0.98, 32, 0.07), (0.80, 24, 0.09), (0.62, 16, 0.12), (0.44, 12, 0.14), (0.28, 8, 0.2)]
        for j, (rr, n, wd) in enumerate(rings):
            r1 = R * rr; r0 = r1 * (0.62 if j < 4 else 0.25)
            for i in range(n):
                a = 2 * math.pi * (i + 0.5 * (j % 2)) / n
                p = petal(c, c, r0, r1, a, r1 * wd)
                if outline: d.line(p + [p[0]], fill=rgb(col if j % 2 else col2), width=int(3 * k))
                else: d.polygon(p, fill=rgb(col if j % 2 == 0 else col2))
            ring_r = r0 * 0.98
            d.ellipse([c - ring_r, c - ring_r, c + ring_r, c + ring_r], outline=rgb(col), width=int((3 if outline else 5) * k))
            for i in range(n):   # dots between petals
                a = 2 * math.pi * (i + 0.5 + 0.5 * (j % 2)) / n; rd = r1 * 0.92; s = r1 * 0.022 + 2 * k
                d.ellipse([c + rd * math.cos(a) - s, c + rd * math.sin(a) - s, c + rd * math.cos(a) + s, c + rd * math.sin(a) + s], fill=rgb(col2))
        s = R * 0.1
        d.ellipse([c - s, c - s, c + s, c + s], fill=None if outline else rgb(col), outline=rgb(col), width=int(4 * k))
    return ss(draw, size, size)


def marigold(size=400, base=MARIGOLD, dark=DEEP_SAFFRON, seed=1):
    rs = random.Random(seed)

    def draw(im, k):
        d = ImageDraw.Draw(im); c = size * k / 2
        for layer in range(7):
            r1 = c * (0.97 - layer * 0.12); n = 22 - layer * 2
            colr = lerp(rgb(dark), rgb(base), layer / 6)
            for i in range(n):
                a = 2 * math.pi * i / n + rs.uniform(-0.12, 0.12) + layer * 0.37
                d.polygon(petal(c, c, r1 * 0.25, r1, a, r1 * 0.2), fill=colr)
                d.line([(c + r1 * 0.5 * math.cos(a), c + r1 * 0.5 * math.sin(a)), (c + r1 * 0.95 * math.cos(a), c + r1 * 0.95 * math.sin(a))], fill=lerp(colr, (120, 40, 0, 255), 0.35), width=int(2 * k))
        s = c * 0.12; d.ellipse([c - s, c - s, c + s, c + s], fill=rgb('#B8430E'))
    im = ss(draw, size, size)
    sh = Image.new('RGBA', im.size, (60, 10, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(size * 0.03)).point(lambda v: v * 0.45))
    out = canvas(*im.size); out.alpha_composite(sh, (int(size * 0.02), int(size * 0.03))); out.alpha_composite(im); return out


def toran(width=1080, height=520, n_strands=7, seed=4):
    """door garland: a mango-leaf rope across the top, marigold strands hanging down"""
    rs = random.Random(seed); im = canvas(width, height)
    flowers = [marigold(110, seed=s, base=[MARIGOLD, TURMERIC, SAFFRON][s % 3]) for s in range(6)]
    leaf = canvas(70, 150)

    def leafdraw(L, k):
        d = ImageDraw.Draw(L); d.polygon(petal(35 * k, 4 * k, 0, 142 * k, math.pi / 2, 28 * k), fill=rgb(LEAF))
        d.line([(35 * k, 8 * k), (35 * k, 140 * k)], fill=rgb('#1C4F1E'), width=2 * k)
    leaf = ss(leafdraw, 70, 150)
    # rope with leaves
    for i in range(18):
        x = int(i * width / 17) - 35; im.alpha_composite(leaf.rotate(rs.uniform(-12, 12), expand=True, resample=Image.BICUBIC), (x, 18))
    rope = ImageDraw.Draw(im); rope.line([(0, 30), (width, 30)], fill=rgb('#7A1F0E'), width=8)
    for s in range(n_strands):
        x = int((s + 0.5) * width / n_strands); L = rs.randint(3, 5) if s % 2 else rs.randint(4, 6)
        for j in range(L):
            f = flowers[(s + j) % 6]; y = 40 + j * 82
            im.alpha_composite(f, (x - 55, y))
    return im


def diya(size=520):
    def draw(im, k):
        d = ImageDraw.Draw(im); w = size * k; c = w / 2
        # glow
        # bowl (clay) - a half ellipse with a lip and a pointed spout
        by = w * 0.66; bw = w * 0.42; bh = w * 0.2
        d.pieslice([c - bw, by - bh, c + bw, by + bh], 0, 180, fill=rgb('#B5441B'))
        d.polygon([(c + bw * 0.7, by), (c + bw * 1.18, by - bh * 0.55), (c + bw * 1.02, by + bh * 0.1)], fill=rgb('#B5441B'))
        d.ellipse([c - bw, by - bh * 0.28, c + bw, by + bh * 0.28], fill=rgb('#8C2E10'))
        d.ellipse([c - bw * 0.82, by - bh * 0.18, c + bw * 0.82, by + bh * 0.18], fill=rgb('#5A1A07'))
        for i in range(9):   # painted dots
            a = math.pi * (i + 0.5) / 9; d.ellipse([c - bw * 0.85 * math.cos(a) - 7 * k, by + bh * 0.55 * math.sin(a) - 7 * k, c - bw * 0.85 * math.cos(a) + 7 * k, by + bh * 0.55 * math.sin(a) + 7 * k], fill=rgb(TURMERIC))
        d.arc([c - bw * 0.9, by - bh * 0.3, c + bw * 0.9, by + bh * 0.85], 20, 160, fill=rgb(GOLD), width=int(5 * k))
        # flame at the spout
        fx, fy = c + bw * 1.08, by - bh * 0.5
        d.polygon(petal(fx, fy, 0, w * 0.3, -math.pi / 2 - 0.08, w * 0.065), fill=rgb('#FF7A00'))
        d.polygon(petal(fx, fy, w * 0.01, w * 0.22, -math.pi / 2 - 0.08, w * 0.04), fill=rgb('#FFC93C'))
        d.polygon(petal(fx, fy, w * 0.02, w * 0.12, -math.pi / 2 - 0.08, w * 0.02), fill=rgb('#FFF6D0'))
    im = ss(draw, size, size)
    glow = radial_glow(size, size, size * 0.5 + size * 0.42 * 1.08, size * 0.66 - size * 0.2 * 0.5 - size * 0.14, size * 0.42, '#FFB52E', 0.75)
    out = canvas(size, size); out.alpha_composite(glow); out.alpha_composite(im); return out


def chakra(size=700, col=NAVY):
    def draw(im, k):
        d = ImageDraw.Draw(im); c = size * k / 2; R = c * 0.96
        d.ellipse([c - R, c - R, c + R, c + R], outline=rgb(col), width=int(size * k * 0.035))
        r0 = R * 0.12
        d.ellipse([c - r0, c - r0, c + r0, c + r0], fill=rgb(col))
        for i in range(24):
            a = 2 * math.pi * i / 24
            d.polygon(petal(c, c, r0 * 0.8, R * 0.95, a, R * 0.035, n=10), fill=rgb(col))
            a2 = a + math.pi / 24; rr = R * 0.93; s = R * 0.03
            d.ellipse([c + rr * math.cos(a2) - s, c + rr * math.sin(a2) - s, c + rr * math.cos(a2) + s, c + rr * math.sin(a2) + s], fill=rgb(col))
    return ss(draw, size, size)


def brush_stroke(w=1300, h=300, col=SAFFRON, seed=1):
    """dry-brush paint band with ragged ends and bristle streaks"""
    rs = np.random.RandomState(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    u = x / w
    top = h * 0.14 + h * 0.08 * np.sin(u * 7 + seed) + rs.randn(w).cumsum()[None, :] * 0.0
    edge_top = h * 0.12 + h * 0.07 * np.sin(np.linspace(0, 9, w) + seed) + np.convolve(rs.randn(w), np.ones(25) / 25, 'same') * h * 0.2
    edge_bot = h * 0.88 - h * 0.07 * np.sin(np.linspace(0, 7, w) + seed * 2) + np.convolve(rs.randn(w), np.ones(25) / 25, 'same') * h * 0.2
    inside = (y > edge_top[None, :]) & (y < edge_bot[None, :])
    start = 0.04 + 0.05 * np.abs(np.convolve(rs.randn(h), np.ones(15) / 15, 'same'))[:, None] * 6
    end = 0.93 - 0.08 * np.abs(np.convolve(rs.randn(h), np.ones(9) / 9, 'same'))[:, None] * 6
    inside &= (u > start) & (u < end)
    streak = np.convolve(rs.rand(h), np.ones(3) / 3, 'same')[:, None]
    dry = (rs.rand(h, w) > (0.04 + 0.5 * np.clip((u - 0.78) / 0.2, 0, 1) * (streak > 0.45)))
    a = (inside & dry).astype(np.float32)
    shade = 0.86 + 0.14 * streak
    arr = np.zeros((h, w, 4), np.float32); c = rgb(col)
    for i in range(3): arr[..., i] = c[i] * shade
    arr[..., 3] = a * 255
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
    return im.filter(ImageFilter.GaussianBlur(0.7))


def gulal(size=900, col=RANI, seed=1):
    """Holi colour powder burst: soft clouds + flying grains"""
    rs = np.random.RandomState(seed); s = size
    y, x = np.mgrid[0:s, 0:s].astype(np.float32); a = np.zeros((s, s), np.float32)
    for _ in range(60):
        r = rs.uniform(0.07, 0.22) * s; ang = rs.uniform(0, 2 * math.pi); dist = rs.uniform(0, 0.3) * s
        cx, cy = s / 2 + dist * math.cos(ang), s / 2 + dist * math.sin(ang)
        a = np.maximum(a, np.clip(1 - np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r, 0, 1) ** 0.9 * rs.uniform(0.55, 0.95))
    for _ in range(900):
        ang = rs.uniform(0, 2 * math.pi); dist = s * (0.2 + 0.28 * rs.rand() ** 0.6); r = rs.uniform(1, 5)
        cx, cy = s / 2 + dist * math.cos(ang), s / 2 + dist * math.sin(ang)
        x0, x1, y0, y1 = int(max(cx - r - 1, 0)), int(min(cx + r + 2, s)), int(max(cy - r - 1, 0)), int(min(cy + r + 2, s))
        if x1 <= x0 or y1 <= y0: continue
        sub = np.clip(1 - np.sqrt((x[y0:y1, x0:x1] - cx) ** 2 + (y[y0:y1, x0:x1] - cy) ** 2) / r, 0, 1)
        a[y0:y1, x0:x1] = np.maximum(a[y0:y1, x0:x1], sub * rs.uniform(0.6, 1))
    tex = 0.8 + 0.2 * rs.rand(s, s)
    arr = np.zeros((s, s, 4), np.float32); c = rgb(col)
    for i in range(3): arr[..., i] = np.clip(c[i] * (0.85 + 0.25 * tex), 0, 255)
    arr[..., 3] = np.clip(a * 255 * 1.1, 0, 255)
    im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    soft = im.filter(ImageFilter.GaussianBlur(s * 0.012)); soft.alpha_composite(im.filter(ImageFilter.GaussianBlur(1)).point(lambda v: v) if False else im.filter(ImageFilter.GaussianBlur(1.2)))
    return soft


def rangoli(size=800):
    cols = [RANI, TURMERIC, TEAL, SAFFRON, '#7B2CBF', GREEN]

    def draw(im, k):
        d = ImageDraw.Draw(im); c = size * k / 2; R = c * 0.97
        for j, (rr, n) in enumerate([(1.0, 16), (0.78, 12), (0.58, 8), (0.38, 8), (0.2, 6)]):
            r1 = R * rr; colr = rgb(cols[j % len(cols)]); col2 = rgb(cols[(j + 2) % len(cols)])
            for i in range(n):
                a = 2 * math.pi * (i + 0.5 * (j % 2)) / n
                d.polygon(petal(c, c, r1 * 0.45, r1, a, r1 * 0.22), fill=colr)
                d.polygon(petal(c, c, r1 * 0.55, r1 * 0.9, a, r1 * 0.1), fill=col2)
            for i in range(n * 2):
                a = 2 * math.pi * i / (n * 2); rd = r1 * 0.42; s = r1 * 0.03
                d.ellipse([c + rd * math.cos(a) - s, c + rd * math.sin(a) - s, c + rd * math.cos(a) + s, c + rd * math.sin(a) + s], fill=rgb(WHITE))
        s = R * 0.1; d.ellipse([c - s, c - s, c + s, c + s], fill=rgb(WHITE))
    return ss(draw, size, size)


def paisley(size=600, col=RANI, col2=GOLD):
    """mango (keri) motif: round belly, tail sweeping up and curling over"""
    def bez(p0, p1, p2, p3, n=40):
        return [tuple((1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * p1[i] + 3 * (1 - t) * t * t * p2[i] + t ** 3 * p3[i] for i in range(2)) for t in (j / n for j in range(n + 1))]

    def outline(s, ox=0.0, oy=0.0):
        cx, cy, r = 0.40, 0.64, 0.3
        tip = (0.76, 0.08)
        arc = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [math.radians(d) for d in range(-10, 181, 5)]]
        left = bez(arc[-1], (cx - r * 1.05, cy - r * 1.6), (tip[0] - 0.22, tip[1] - 0.06), tip)
        right = bez(tip, (tip[0] + 0.05, tip[1] + 0.18), (cx + r * 1.1, cy - r * 0.9), arc[0])
        pc = (cx + 0.03, cy + 0.02)
        return [((pc[0] + (x - pc[0]) * s) * size * K[0], (pc[1] + (y - pc[1]) * s) * size * K[0]) for x, y in arc + left + right]
    K = [1]

    def draw(im, k):
        K[0] = k; d = ImageDraw.Draw(im)
        d.polygon(outline(1.0), fill=rgb(col))
        d.polygon(outline(0.72), fill=rgb(col2))
        d.polygon(outline(0.48), fill=rgb(col))
        cx, cy, r = 0.43, 0.66, 0.3 * 0.6
        for i in range(12):
            a = 2 * math.pi * i / 12; s_ = 0.016 * size * k
            x, y = (cx + r * math.cos(a)) * size * k, (cy + r * math.sin(a)) * size * k
            d.ellipse([x - s_, y - s_, x + s_, y + s_], fill=rgb(WHITE))
        s_ = 0.05 * size * k; d.ellipse([cx * size * k - s_, cy * size * k - s_, cx * size * k + s_, cy * size * k + s_], fill=rgb(col2))
    return ss(draw, size, size)


def kite(size=520, c1=RANI, c2=TURMERIC, seed=2):
    def draw(im, k):
        d = ImageDraw.Draw(im); w = size * k; cx, top, mid, bot = w * 0.5, w * 0.06, w * 0.38, w * 0.78
        L, R = w * 0.12, w * 0.88
        d.polygon([(cx, top), (R, mid), (cx, bot), (L, mid)], fill=rgb(c1))
        d.polygon([(cx, top), (R, mid), (cx, mid + w * 0.03)], fill=rgb(c2))
        d.polygon([(cx, bot), (cx - w * 0.07, bot + w * 0.12), (cx + w * 0.07, bot + w * 0.12)], fill=rgb(c2))
        d.line([(cx, top), (cx, bot)], fill=rgb('#5A2A0A'), width=int(4 * k))
        d.arc([L, mid - w * 0.2, R, mid + w * 0.2], 190, 350, fill=rgb('#5A2A0A'), width=int(4 * k))
        d.line([(cx, mid + w * 0.04), (w * 0.96, w * 0.99)], fill=(255, 255, 255, 200), width=int(2 * k))
    return ss(draw, size, size)


def horn_ok_please(w=900, h=420):
    """truck-art plate: painted panel, scalloped border, lettering"""
    def draw(im, k):
        d = ImageDraw.Draw(im); W2, H2 = w * k, h * k
        d.rounded_rectangle([0, 0, W2 - 1, H2 - 1], radius=40 * k, fill=rgb(TURMERIC))
        d.rounded_rectangle([18 * k, 18 * k, W2 - 18 * k, H2 - 18 * k], radius=30 * k, fill=rgb(RANI))
        n = 22
        for i in range(n):   # scallops top and bottom
            x0 = 30 * k + i * (W2 - 60 * k) / n; x1 = x0 + (W2 - 60 * k) / n
            d.pieslice([x0, 10 * k, x1, 50 * k], 0, 180, fill=rgb(TEAL))
            d.pieslice([x0, H2 - 50 * k, x1, H2 - 10 * k], 180, 360, fill=rgb(TEAL))
        d.rounded_rectangle([46 * k, 64 * k, W2 - 46 * k, H2 - 64 * k], radius=18 * k, fill=rgb(INK))
        f1 = ImageFont.truetype(FONT, int(150 * k)); f2 = ImageFont.truetype(FONT, int(70 * k))
        for txt, f, y, col in [('HORN OK', f1, H2 * 0.40, TURMERIC), ('PLEASE', f2, H2 * 0.73, WHITE)]:
            bb = d.textbbox((0, 0), txt, font=f); tw = bb[2] - bb[0]
            d.text(((W2 - tw) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f, fill=rgb(col))
        for xx in (90 * k, W2 - 90 * k):
            s = 22 * k; d.ellipse([xx - s, H2 * 0.73 - s, xx + s, H2 * 0.73 + s], fill=rgb(SAFFRON))
    return ss(draw, w, h)


def lotus(size=600, col=RANI, col2='#FF8FC2'):
    def draw(im, k):
        d = ImageDraw.Draw(im); w = size * k; cx, by = w / 2, w * 0.78
        for i, (ang, ln, wd, cl) in enumerate([(-2.55, 0.42, 0.1, col2), (-0.59, 0.42, 0.1, col2), (-2.2, 0.48, 0.11, col), (-0.94, 0.48, 0.11, col), (-1.85, 0.52, 0.12, col2), (-1.29, 0.52, 0.12, col2), (-1.5708, 0.6, 0.13, col)]):
            d.polygon(petal(cx, by, 0, w * ln, ang, w * wd), fill=rgb(cl))
        d.ellipse([cx - w * 0.36, by - w * 0.03, cx + w * 0.36, by + w * 0.08], fill=rgb(LEAF))
    return ss(draw, size, size)


def sparkle(size=200, col=WHITE):
    def draw(im, k):
        d = ImageDraw.Draw(im); w = size * k; c = w / 2
        for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
            d.polygon(petal(c, c, 0, c * 0.98, a, c * 0.13), fill=rgb(col))
    return ss(draw, size, size)


def hud(w=1080, h=1920, col=(255, 255, 255, 190)):
    """reference-style frame marks: corner brackets, tiny labels, a progress hairline"""
    im = canvas(w, h); d = ImageDraw.Draw(im); m, L = 54, 70
    for (x, y, sx, sy) in [(m, m, 1, 1), (w - m, m, -1, 1), (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
        d.line([(x, y), (x + sx * L, y)], fill=col, width=4); d.line([(x, y), (x, y + sy * L)], fill=col, width=4)
    f = ImageFont.truetype(FONT, 34)
    d.text((m + 6, m + 84), 'BHARAT  //  REEL 01', font=f, fill=col)
    d.text((w - m - 190, h - m - 120), '28.6139 N', font=f, fill=col); d.text((w - m - 190, h - m - 84), '77.2090 E', font=f, fill=col)
    d.line([(m + 4, h - m - 30), (w * 0.55, h - m - 30)], fill=(255, 255, 255, 120), width=2)
    d.ellipse([w - m - 30, h * 0.5 - 12, w - m - 6, h * 0.5 + 12], outline=col, width=3)
    return im


# ================================================================ backgrounds
def bg(name, stops, angle, glow=None, watermark=None, seed=1):
    im = grad(W, H, stops, angle).convert('RGBA')
    if glow: im.alpha_composite(radial_glow(W, H, *glow))
    if watermark:
        m, op, sc, pos = watermark
        mm = m.resize((int(W * sc), int(W * sc)), Image.LANCZOS)
        a = mm.getchannel('A').point(lambda v: int(v * op)); mm.putalpha(a)
        im.alpha_composite(mm, (int(pos[0] - mm.width / 2), int(pos[1] - mm.height / 2)))
    return noise_grain(im.convert('RGB'), 4, seed)


# ================================================================ scene cards (stand-ins for the photo slots)
def sky(stops, angle=90): return grad(W, H, stops, angle).convert('RGBA')


def onion(cx, base, w, h, n=80):
    pts = []
    for i in range(n + 1):
        v = i / n; r = w / 2 * (1 + 0.42 * math.sin(math.pi * min(1, v * 1.35))) * (1 - v) ** 0.9 / 1.25
        pts.append((cx + r, base - h * v))
    return pts + [(cx - x + cx - cx, y) for x, y in reversed([(cx - (px - cx), py) for px, py in pts])]


def onion_poly(cx, base, w, h, n=80):
    right = []
    for i in range(n + 1):
        v = i / n; r = w / 2 * (1 + 0.42 * math.sin(math.pi * min(1, v * 1.35))) * (1 - v) ** 0.9 / 1.25
        right.append((cx + r, base - h * v))
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    return right + left


def taj(col):
    im = canvas(W, H); d = ImageDraw.Draw(im); base = 1460; c = W / 2
    d.rectangle([60, base, W - 60, base + 30], fill=col)                                     # plinth
    d.rectangle([c - 300, base - 330, c + 300, base], fill=col)                             # main block
    d.rectangle([c - 330, base - 300, c - 300, base], fill=col); d.rectangle([c + 300, base - 300, c + 330, base], fill=col)
    d.rectangle([c - 120, base - 400, c + 120, base - 330], fill=col)                       # drum
    d.polygon(onion_poly(c, base - 395, 300, 330), fill=col)                                 # dome
    d.line([(c, base - 725), (c, base - 790)], fill=col, width=8); d.ellipse([c - 10, base - 770, c + 10, base - 750], fill=col)
    for sx in (-1, 1):
        x = c + sx * 215
        d.rectangle([x - 55, base - 400, x + 55, base - 330], fill=col)
        d.polygon(onion_poly(x, base - 398, 115, 120), fill=col)
        for mx in (c + sx * 455,):                                                              # minarets
            d.polygon([(mx - 26, base), (mx + 26, base), (mx + 19, base - 520), (mx - 19, base - 520)], fill=col)
            for yy in (base - 180, base - 340, base - 500): d.rectangle([mx - 34, yy - 10, mx + 34, yy], fill=col)
            d.rectangle([mx - 30, base - 560, mx + 30, base - 520], fill=col)
            d.polygon(onion_poly(mx, base - 558, 70, 80), fill=col)
    # arches cut out
    hole = canvas(W, H); hd = ImageDraw.Draw(hole)
    hd.rectangle([c - 90, base - 260, c + 90, base], fill=(0, 0, 0, 255)); hd.pieslice([c - 90, base - 350, c + 90, base - 170], 180, 360, fill=(0, 0, 0, 255))
    for sx in (-1, 1):
        for xx, yy in [(c + sx * 220, base - 150), (c + sx * 220, base - 280)]:
            hd.rectangle([xx - 45, yy - 50, xx + 45, yy + 60], fill=(0, 0, 0, 255)); hd.pieslice([xx - 45, yy - 95, xx + 45, yy - 5], 180, 360, fill=(0, 0, 0, 255))
    a = ImageChops.subtract(im.getchannel('A'), hole.getchannel('A').point(lambda v: int(v * 0.55)))
    im.putalpha(a); return im


def scene_taj():
    im = sky([(0, '#2A0E3A'), (0.45, '#C2185B'), (0.7, '#FF8A3D'), (1, '#FFD36E')], 90)
    im.alpha_composite(radial_glow(W, H, W * 0.5, 1180, 520, '#FFE29A', 0.9))
    d = ImageDraw.Draw(im); d.ellipse([W / 2 - 190, 980, W / 2 + 190, 1360], fill=rgb('#FFE7A8', 235))
    im.alpha_composite(taj(rgb('#2B0F2E')))
    w = Image.new('RGBA', (W, H - 1490), rgb('#21102A')); im.alpha_composite(w, (0, 1490))   # reflecting pool
    refl = taj(rgb('#3C1840', 140)).transpose(Image.FLIP_TOP_BOTTOM).crop((0, H - 1490 - 0, W, H)); im.alpha_composite(refl, (0, 1490))
    for i in range(30):
        y = 1500 + i * 14; d.line([(W * 0.2, y), (W * 0.8, y)], fill=(255, 210, 140, 30), width=2)
    for x in range(40, W, 120): d.polygon([(x, 1490), (x + 18, 1290), (x + 36, 1490)], fill=rgb('#1A0A1F'))   # cypress rows
    return noise_grain(im.convert('RGB'), 5, 2)


def scene_holi():
    im = sky([(0, '#FFF1E6'), (1, '#FFD9C2')], 90)
    for col, (x, y), s, sd in [(RANI, (220, 520), 1100, 1), (TURMERIC, (900, 420), 1000, 2), (TEAL, (820, 1250), 1100, 3), ('#7B2CBF', (200, 1420), 950, 4), (GREEN, (560, 900), 800, 5), (SAFFRON, (560, 1700), 900, 6)]:
        g = gulal(500, col, sd).resize((s, s), Image.BICUBIC); im.alpha_composite(g, (int(x - s / 2), int(y - s / 2)))
    return noise_grain(im.convert('RGB'), 7, 3)


def shikhara(d, cx, base, w, h, col):
    pts = []
    for i in range(41):
        v = i / 40; r = w / 2 * (1 - v ** 1.6) * (1 + 0.05 * math.sin(v * 40))
        pts.append((cx + r, base - h * v))
    d.polygon(pts + [(2 * cx - x, y) for x, y in reversed(pts)], fill=col)
    d.ellipse([cx - w * 0.12, base - h - w * 0.12, cx + w * 0.12, base - h + w * 0.06], fill=col)
    d.line([(cx, base - h - w * 0.1), (cx, base - h - w * 0.4)], fill=col, width=6)
    d.polygon([(cx, base - h - w * 0.4), (cx + w * 0.22, base - h - w * 0.33), (cx, base - h - w * 0.26)], fill=rgb(SAFFRON))


def scene_varanasi():
    im = sky([(0, '#14213D'), (0.5, '#5B2A86'), (0.75, '#E76F51'), (1, '#F4A261')], 90)
    d = ImageDraw.Draw(im); col = rgb('#1B1030')
    for cx, w, h in [(180, 200, 520), (430, 150, 380), (640, 240, 640), (900, 170, 430)]:
        shikhara(d, cx, 1150, w, h, col)
    d.rectangle([0, 1100, W, 1180], fill=col)
    for i in range(9): y = 1180 + i * 24; d.rectangle([0 - i * 8, y, W + i * 8, y + 16], fill=lerp(col, rgb('#4A2A55'), i / 9))   # ghat steps
    water = grad(W, H - 1400, [(0, '#3B1F4A'), (1, '#120A1E')], 90).convert('RGBA'); im.alpha_composite(water, (0, 1400))
    for i in range(70):
        x = random.Random(i).uniform(40, W - 40); y = random.Random(i + 99).uniform(1430, 1880); s = random.Random(i + 7).uniform(4, 9)
        im.alpha_composite(radial_glow(80, 80, 40, 40, 38, '#FFB347', 0.8), (int(x - 40), int(y - 40)))
        d.ellipse([x - s, y - s * 0.6, x + s, y + s * 0.6], fill=rgb('#FFE08A'))
    for bx, by in [(260, 1520), (760, 1640)]:   # boats
        d.polygon([(bx - 150, by), (bx + 150, by), (bx + 110, by + 40), (bx - 110, by + 40)], fill=rgb('#0B0612'))
        d.line([(bx + 40, by), (bx + 120, by - 140)], fill=rgb('#0B0612'), width=6)
    return noise_grain(im.convert('RGB'), 5, 4)


def scene_fort():
    im = sky([(0, '#F9C74F'), (0.55, '#F8961E'), (1, '#E85D04')], 90)
    d = ImageDraw.Draw(im); d.ellipse([W / 2 - 230, 520, W / 2 + 230, 980], fill=rgb('#FFF3B0', 230))
    col = rgb('#7F2704')
    d.rectangle([0, 1000, W, 1400], fill=col)
    for x in range(0, W, 60): d.rectangle([x, 970, x + 34, 1000], fill=col)    # crenels
    for cx in (150, 540, 930):
        d.rectangle([cx - 90, 820, cx + 90, 1000], fill=col)
        d.polygon(onion_poly(cx, 822, 190, 170), fill=col)
        for i in range(3):
            ax = cx - 60 + i * 60; d.rectangle([ax - 18, 870, ax + 18, 940], fill=rgb('#3D1102')); d.pieslice([ax - 18, 852, ax + 18, 888], 180, 360, fill=rgb('#3D1102'))
    for r in range(3):
        for i in range(8):
            ax = 70 + i * 135; ay = 1080 + r * 105
            d.rectangle([ax - 26, ay, ax + 26, ay + 60], fill=rgb('#3D1102')); d.pieslice([ax - 26, ay - 26, ax + 26, ay + 26], 180, 360, fill=rgb('#3D1102'))
    dunes = grad(W, H - 1380, [(0, '#E9A23B'), (1, '#B5651D')], 90).convert('RGBA'); im.alpha_composite(dunes, (0, 1380))
    for i, (yy, cc) in enumerate([(1450, '#D98E2B'), (1600, '#C77A20'), (1760, '#A65F16')]):
        pts = [(x, yy + 50 * math.sin(x / 170 + i)) for x in range(0, W + 20, 20)] + [(W, H), (0, H)]
        d.polygon(pts, fill=rgb(cc))
    return noise_grain(im.convert('RGB'), 6, 5)


def scene_kites():
    im = sky([(0, '#4CC9F0'), (0.7, '#A0E7FF'), (1, '#FFE5B4')], 90)
    rs = random.Random(9)
    for i in range(14):
        cols = [(RANI, TURMERIC), (SAFFRON, GREEN), (TEAL, RANI), ('#7B2CBF', TURMERIC), (SINDOOR, WHITE)][i % 5]
        s = rs.randint(130, 300); k = kite(s, *cols, seed=i).rotate(rs.uniform(-30, 30), expand=True, resample=Image.BICUBIC)
        im.alpha_composite(k, (rs.randint(-40, W - 120), rs.randint(80, 1300)))
    d = ImageDraw.Draw(im); col = rgb('#3A1C47')
    x = 0
    while x < W:                                               # rooftops
        w = rs.randint(120, 260); h = rs.randint(200, 420); d.rectangle([x, H - h, x + w, H], fill=col)
        if rs.random() < 0.4: d.polygon(onion_poly(x + w / 2, H - h + 4, w * 0.5, w * 0.55), fill=col)
        x += w
    return noise_grain(im.convert('RGB'), 5, 6)


def scene_diwali():
    im = sky([(0, '#0B0A2A'), (1, '#2A0B3D')], 90)
    rs = random.Random(3)
    for i in range(45):
        x, y, r = rs.uniform(0, W), rs.uniform(0, H * 0.7), rs.uniform(30, 120)
        im.alpha_composite(radial_glow(int(r * 2), int(r * 2), r, r, r, rs.choice(['#FFB347', '#FF6F91', '#FFD166']), rs.uniform(0.25, 0.6)), (int(x - r), int(y - r)))
    d = ImageDraw.Draw(im)
    for row in range(3):                                       # string lights
        pts = [(x, 200 + row * 240 + 60 * math.sin(x / 240 + row)) for x in range(0, W + 30, 30)]
        d.line(pts, fill=(255, 220, 160, 120), width=3)
        for x, y in pts[::3]:
            im.alpha_composite(radial_glow(60, 60, 30, 30, 28, '#FFE08A', 0.9), (int(x - 30), int(y - 30)))
    dy = diya(330)
    for i, (x, y) in enumerate([(120, 1420), (420, 1460), (720, 1410), (240, 1640), (560, 1680), (880, 1620)]):
        im.alpha_composite(dy, (int(x - 120), int(y - 200)))
    rg = rangoli(700); a = rg.getchannel('A').point(lambda v: int(v * 0.85)); rg.putalpha(a)
    im.alpha_composite(rg.resize((900, 300)), (90, 1620))
    return noise_grain(im.convert('RGB'), 5, 7)


def scene_chai():
    im = sky([(0, '#3E1F0D'), (1, '#1A0C05')], 90)
    im.alpha_composite(radial_glow(W, H, W * 0.55, 700, 900, '#FF9F43', 0.5))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1350, W, H], fill=rgb('#5C3317'))         # wooden table
    for i in range(14): d.line([(0, 1360 + i * 42), (W, 1350 + i * 42 + (i % 3) * 6)], fill=rgb('#4A2810'), width=3)
    cx, top, bot = W / 2, 760, 1420                             # kulhad (clay cup)
    d.polygon([(cx - 270, top), (cx + 270, top), (cx + 190, bot), (cx - 190, bot)], fill=rgb('#B5532A'))
    d.polygon([(cx + 120, top), (cx + 270, top), (cx + 190, bot), (cx + 90, bot)], fill=rgb('#8E3B1A'))
    d.ellipse([cx - 270, top - 60, cx + 270, top + 60], fill=rgb('#C96A3B'))
    d.ellipse([cx - 235, top - 42, cx + 235, top + 44], fill=rgb('#D9A066'))       # chai surface
    d.ellipse([cx - 120, top - 18, cx + 60, top + 14], fill=rgb('#E8BC85'))
    for i in range(3):                                          # steam
        pts = [(cx - 120 + i * 120 + 50 * math.sin(y / 70 + i * 2), y) for y in range(top - 80, 200, -10)]
        d.line(pts, fill=(255, 245, 230, 110), width=26, joint='curve')
    return noise_grain(im.convert('RGB').filter(ImageFilter.GaussianBlur(0.6)), 6, 8)


def scene_cricket():
    im = sky([(0, '#04122B'), (0.6, '#0B3D2E'), (1, '#1E7B3C')], 90)
    for x in (140, 940):
        im.alpha_composite(radial_glow(W, H, x, 220, 520, '#E9F5FF', 0.8))
        d = ImageDraw.Draw(im); d.rectangle([x - 70, 160, x + 70, 260], fill=rgb('#F0F8FF'))
    d = ImageDraw.Draw(im)
    d.polygon([(W * 0.2, 1920), (W * 0.42, 1000), (W * 0.58, 1000), (W * 0.8, 1920)], fill=rgb('#C8B07A'))     # pitch
    for i, x in enumerate((W / 2 - 60, W / 2, W / 2 + 60)):                                                      # stumps
        d.rectangle([x - 12, 1080, x + 12, 1500], fill=rgb('#F4E9D8'))
    d.rectangle([W / 2 - 75, 1068, W / 2 + 75, 1082], fill=rgb('#F4E9D8'))
    bx, by, r = W * 0.7, 760, 95                                                                                 # ball
    d.ellipse([bx - r, by - r, bx + r, by + r], fill=rgb('#B3121F'))
    d.arc([bx - r * 0.6, by - r, bx + r * 1.4, by + r], 120, 240, fill=rgb('#F7E7CE'), width=6)
    for i in range(10): d.line([(bx - 330 - i * 40, by + 60 + i * 12), (bx - 120 - i * 40, by + 20 + i * 10)], fill=(255, 255, 255, 40 - i * 3), width=8)
    return noise_grain(im.convert('RGB'), 6, 9)


def scene_monsoon():
    im = sky([(0, '#0F2027'), (0.5, '#203A43'), (1, '#2C5364')], 90)
    d = ImageDraw.Draw(im); col = rgb('#0A1A1F')
    for px, ph, lean in [(150, 1100, -0.15), (880, 1250, 0.12), (620, 900, 0.05)]:          # palms
        top = (px + lean * ph * 0.5, H - ph)
        d.line([(px, H), top], fill=col, width=26)
        for a in range(9):
            ang = -math.pi + a * math.pi / 8
            d.polygon(petal(top[0], top[1], 0, 300, ang + 0.2 * math.sin(a), 38), fill=col)
    ax, ay = 300, 1640                                                                          # auto-rickshaw
    d.rounded_rectangle([ax, ay - 200, ax + 380, ay], radius=60, fill=rgb('#F5C400'))
    d.rectangle([ax + 20, ay - 230, ax + 330, ay - 190], fill=rgb('#111111'))
    d.polygon([(ax + 330, ay - 230), (ax + 400, ay - 120), (ax + 380, ay - 40)], fill=rgb('#2E7D32'))
    d.rectangle([ax + 40, ay - 170, ax + 200, ay - 80], fill=rgb('#2B3A40'))
    for wx in (ax + 70, ax + 330): d.ellipse([wx - 48, ay - 40, wx + 48, ay + 56], fill=rgb('#111111')); d.ellipse([wx - 18, ay - 10, wx + 18, ay + 26], fill=rgb('#888888'))
    im.alpha_composite(radial_glow(300, 300, 150, 150, 140, '#FFF2B3', 0.8), (ax + 280, ay - 220))
    rain = canvas(W, H); rd = ImageDraw.Draw(rain); rs = random.Random(5)
    for i in range(700):
        x, y, L = rs.uniform(-200, W), rs.uniform(-100, H), rs.uniform(40, 110)
        rd.line([(x, y), (x + L * 0.25, y + L)], fill=(210, 235, 255, rs.randint(60, 150)), width=2)
    im.alpha_composite(rain)
    return noise_grain(im.convert('RGB'), 6, 10)


# ================================================================ main
def main():
    st, bgd, sc = os.path.join(OUT, 'stickers'), os.path.join(OUT, 'backgrounds'), os.path.join(OUT, 'scenes')
    m_gold, m_white = mandala(1000, GOLD, '#FFD97A'), mandala(1000, WHITE, WHITE, outline=True)
    stickers = {
        'mandala_gold': m_gold, 'mandala_line': m_white, 'mandala_rani': mandala(1000, RANI, '#FF7EB6'),
        'marigold': marigold(420), 'marigold_yellow': marigold(420, TURMERIC, MARIGOLD, 3),
        'toran': toran(), 'diya': diya(520), 'chakra': chakra(700), 'chakra_white': chakra(700, WHITE),
        'stroke_saffron': brush_stroke(1300, 300, SAFFRON, 1), 'stroke_white': brush_stroke(1300, 300, WHITE, 2), 'stroke_green': brush_stroke(1300, 300, GREEN, 3),
        'stroke_rani': brush_stroke(1300, 300, RANI, 4), 'gulal_rani': gulal(900, RANI, 1), 'gulal_yellow': gulal(900, TURMERIC, 2),
        'gulal_teal': gulal(900, TEAL, 3), 'gulal_violet': gulal(900, '#7B2CBF', 4), 'rangoli': rangoli(800), 'paisley': paisley(600),
        'kite_rani': kite(520, RANI, TURMERIC), 'kite_saffron': kite(520, SAFFRON, GREEN, 3), 'horn_ok_please': horn_ok_please(),
        'lotus': lotus(600), 'sparkle': sparkle(200), 'sparkle_gold': sparkle(200, '#FFD54A'), 'hud': hud(),
    }
    for k, v in stickers.items(): save(v, os.path.join(st, k + '.png'))
    bgs = {
        'saffron': bg('saffron', [(0, '#FFB347'), (0.55, SAFFRON), (1, '#E0115F')], 120, (W * 0.25, H * 0.2, 1100, '#FFE29A', 0.55), (m_gold, 0.10, 1.3, (W * 0.8, H * 0.75)), 1),
        'rani': bg('rani', [(0, '#FF6FA8'), (0.5, RANI), (1, '#9D0B4F')], 120, (W * 0.2, H * 0.15, 1000, '#FFB3D1', 0.5), (m_white, 0.08, 1.4, (W * 0.15, H * 0.85)), 2),
        'peacock': bg('peacock', [(0, '#16C0B0'), (0.5, PEACOCK), (1, INDIGO)], 125, (W * 0.8, H * 0.2, 1000, '#7FFFE0', 0.35), (m_white, 0.07, 1.3, (W * 0.85, H * 0.8)), 3),
        'turmeric': bg('turmeric', [(0, '#FFE066'), (0.6, TURMERIC), (1, DEEP_SAFFRON)], 110, (W * 0.5, H * 0.35, 1000, '#FFFFFF', 0.35), (m_gold, 0.12, 1.2, (W * 0.5, H * 0.95)), 4),
        'indigo': bg('indigo', [(0, '#3A2FA0'), (0.55, INDIGO), (1, '#120E3A')], 115, (W * 0.3, H * 0.25, 1100, '#8E7CFF', 0.4), (m_white, 0.07, 1.3, (W * 0.2, H * 0.8)), 5),
        'cream': bg('cream', [(0, '#FFF8EC'), (1, '#F6E6CC')], 90, None, (m_gold, 0.16, 1.5, (W * 0.5, H * 0.5)), 6),
        'night': bg('night', [(0, '#1B0A24'), (0.6, '#0E0716'), (1, '#050208')], 100, (W * 0.5, H * 0.45, 900, '#E8B321', 0.18), (m_gold, 0.06, 1.4, (W * 0.5, H * 0.5)), 7),
        'maroon': bg('maroon', [(0, '#A4161A'), (0.6, MAROON), (1, '#2B0410')], 115, (W * 0.5, H * 0.3, 1000, '#FF7A5C', 0.35), (m_gold, 0.09, 1.3, (W * 0.85, H * 0.15)), 8),
        'green': bg('green', [(0, '#3DDC84'), (0.55, GREEN), (1, '#0B3D1A')], 120, (W * 0.3, H * 0.2, 1000, '#C8FFB0', 0.3), (m_white, 0.07, 1.3, (W * 0.8, H * 0.8)), 9),
    }
    for k, v in bgs.items(): save(v, os.path.join(bgd, k + '.jpg'))
    scenes = {'taj': scene_taj, 'holi': scene_holi, 'varanasi': scene_varanasi, 'fort': scene_fort, 'kites': scene_kites,
              'diwali': scene_diwali, 'chai': scene_chai, 'cricket': scene_cricket, 'monsoon': scene_monsoon}
    for k, f in scenes.items(): save(f(), os.path.join(sc, k + '.jpg'))


if __name__ == '__main__':
    main()
