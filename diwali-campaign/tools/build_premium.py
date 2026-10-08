"""Diwali campaign film, 20 s, 9:16 - premium cut for Kinekit Studio -> KineMaster.

    python3 build_premium.py PREMIUM_ASSETS_DIR TEMPLATE_RECIPE OUT_RECIPE

Art direction: deep black, warm graded footage, one gold. Engraved Cinzel / Cormorant typography placed with a fixed
hierarchy (kinetic words always in the lower third over a scrim, titles centred with a lotus divider). Footage alternates
full frame, framed cards floating over a blurred plate of the same shot, and a split layout. Light is used sparingly:
lens-flare dissolves on the act changes, one anamorphic streak per act. Camera: slow pushes with layers at different
depths for parallax. Music grid 72.8 BPM (beat 0.8215 s, first beat 0.506 s, drop 2.97 s).
"""
import base64, copy, io, json, os, subprocess, sys
from PIL import Image

A, TEMPLATE, OUT = sys.argv[1:4]
tpl = json.load(open(TEMPLATE)); META = json.load(open(f'{A}/meta.json'))
_g = Image.open(f'{A}/orn/gold_string.png'); STR_R = _g.width / _g.height     # gold string width per px of length
SW, SH, CX, CY, DUR = 720, 1280, 360, 640, 20.0
BPM, OFF = 73.04, 0.506
BEAT = 60 / BPM
SCREEN = 22
def beat(n): return round(OFF + n * BEAT, 3)


# ---------------------------------------------------------------- media
media, videos, bin_ = {}, {}, []
def img_id(rel, max_w=None):
    mid = 'p_' + rel.replace('/', '_').rsplit('.', 1)[0]
    if mid in media: return mid
    im = Image.open(f'{A}/{rel}')
    if max_w and im.width > max_w: im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); png = im.mode == 'RGBA'
    (im.save(b, 'PNG', optimize=True) if png else im.convert('RGB').save(b, 'JPEG', quality=88, optimize=True))
    media[mid] = f"data:image/{'png' if png else 'jpeg'};base64," + base64.b64encode(b.getvalue()).decode()
    return mid


def clip_id(name):
    vid = 'pv_' + name
    if vid in videos: return vid
    p = f'{A}/clips/{name}.mp4'
    videos[vid] = {'name': name, 'ext': 'mp4', 'data': 'data:video/mp4;base64,' + base64.b64encode(open(p, 'rb').read()).decode()}
    pr = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'csv=p=0', p],
                        capture_output=True, text=True).stdout.split()
    w, h = map(int, pr[0].split(',')[:2]); bin_.append({'id': vid, 'name': name, 'kind': 'video', 'w': w, 'h': h, 'dur': round(float(pr[1]), 3), 'ext': 'mp4'})
    return vid


# ---------------------------------------------------------------- layers
items, order = [], []
base_photo = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'ph124')
base_decor = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'dc144')
base_fx = {i['effect']: i for i in tpl['studio_scene']['items'] if i['type'] == 'fx'}
nid = [0]
def new_id(p): nid[0] += 1; return f'{p}{nid[0]}'
def ph(kind, dur, amount=1): return {'preset': kind, 'dur': dur, 'stagger': 0, 'order': 'forward', 'amount': amount}


def K(*ks):
    """transform keys (t, x, y, s, rot[, ease]) - ease is how it moves to the next key"""
    out = []
    for k in ks:
        t, x, y, s, r = k[:5]; e = k[5] if len(k) > 5 else 'linear'
        out.append(dict(t=round(t, 3), ease=e, x=round(x, 1), y=round(y, 1), depth=0, rot=r, s=round(s, 4), rx=0, ry=0))
    return out


def layer(t0, t1, x=CX, y=CY, w=SW, tk=None, in_=None, out=None, opacity=1, blend=0, depth=0, name='', slot=None, sound=None):
    it = copy.deepcopy(base_photo)
    if tk: tk = [dict(k, depth=depth) for k in tk]
    it.update(id=new_id('ph'), name=name, start=round(t0, 3), end=round(t1, 3), x=round(x, 1), y=round(y, 1), w=round(w, 1), depth=depth, cam=True,
              tk=tk or [], opacity=opacity, blend=blend, rot=0)
    it['in'], it['out'] = in_, out
    if slot: it['slot'] = {'on': True, 'label': slot}
    if sound: it['sfx'] = {'in': sound[0], 'out': '', 'per': 'block', 'pitch': 'flat', 'volume': sound[1]}
    items.append(it); order.append(it['id']); return it


def img(rel, t0, t1, x=CX, y=CY, w=SW, max_w=None, **kw):
    it = layer(t0, t1, x, y, w, **kw); it['photo'].update(src='up:' + img_id(rel, max_w), aspect='9:16', raw=True, alpha=rel.endswith('.png'))
    it['name'] = kw.get('name') or rel.split('/')[-1]; return it


def vid(clip, t0, t1, x=CX, y=CY, w=SW, trim=0.0, speed=1, **kw):
    it = layer(t0, t1, x, y, w, **kw); it.pop('photo'); it['type'] = 'video'; it['id'] = 'vd' + it['id'][2:]; order[-1] = it['id']
    it['video'] = {'src': 'vid:' + clip_id(clip), 'trimIn': round(trim, 3), 'speed': speed, 'volume': 0}; it['name'] = kw.get('name') or clip
    return it


def rect(t0, t1, color, opacity=1, in_=None, out=None, name='Panel'):
    it = copy.deepcopy(base_decor)
    it.update(id=new_id('dc'), name=name, start=round(t0, 3), end=round(t1, 3), x=CX, y=CY, w=SW + 60, h=SH + 60, color=color, alpha=1, cam=False, tk=[], opacity=opacity)
    it['in'], it['out'] = in_, out; items.append(it); order.append(it['id']); return it


def fx(effect, t0, t1, kf=None, params=None, name=None):
    it = copy.deepcopy(base_fx.get(effect) or dict(base_fx['grain'], effect=effect, params={}, keys=[]))
    it.update(id=new_id('fx'), start=round(t0, 3), end=round(t1, 3), name=name or it['name'])
    if kf is not None: it['keys'] = kf
    if params: it['params'] = dict(it['params'], **params)
    items.append(it); order.append(it['id']); return it


def cover(depth): return SW * (1000 + depth) / 1000 * 1.03          # full-frame width that still covers at that depth


# ---------------------------------------------------------------- reusable compositions
def flare(t, x=CX, y=CY, w=1500, peak=0.95):
    """lens-flare dissolve: the supplied flare blooms over the cut and falls off"""
    img('orn/flare.jpg', t - 0.16, t + 0.34, x, y, w, max_w=900, blend=SCREEN, opacity=peak, in_=ph('fade', 0.14), out=ph('fade', 0.22),
        tk=K((t - 0.16, x, y, 0.75, 0, 'out'), (t + 0.34, x, y, 1.15, 0)), name='Flare dissolve', sound=('Woosh_MidH_3', 40))


def streak(t, y, dur=0.55):
    img('orn/streak.png', t, t + dur, CX, y, 1500, max_w=1400, blend=SCREEN, opacity=0.8, in_=ph('fade', 0.1), out=ph('fade', 0.2),
        tk=K((t, -260, y, 1, 0, 'out'), (t + dur, 980, y, 1, 0)), name='Light streak')


def card(src, t0, t1, plate, trim=0.0, kind='clip', enter='up', slot=None):
    """framed card floating over a blurred plate of the same footage: plate far back, card near, frame + shadow on it"""
    vid(plate, t0, t1, CX, CY, cover(260), trim=trim, depth=260, tk=K((t0, CX, CY, 1.0, 0), (t1, CX, CY, 1.06, 0)), name='Plate ' + plate)
    y0 = {'up': 690, 'down': 590}[enter]; ce = (t0, CX, y0, 0.965, 0, 'out'); cs = (t0 + 0.45, CX, 625, 1.0, 0); cend = (t1, CX, 620, 1.015, 0)
    img('orn/card_shadow.png', t0, t1, CX, 645, 840, tk=K(ce[:1] + (CX, y0 + 25) + ce[3:], cs[:1] + (CX, 650) + cs[3:], cend[:1] + (CX, 645) + cend[3:]), opacity=0.85, name='Card shadow')
    if kind == 'clip': vid(src, t0, t1, CX, 625, 600, trim=trim, tk=K(ce, cs, cend), slot=slot)
    else: img(src, t0, t1, CX, 625, 600, tk=K(ce, cs, cend), slot=slot)
    img('orn/card_frame.png', t0, t1, CX, 625, 612, tk=K(ce, cs, cend), name='Card frame')


def word(name, t0, t1, y=1075):
    """kinetic word, always the same place: lower third over the scrim, lotus divider under it"""
    m = META[name]
    img(f'type/{name}.png', t0, t1, CX, y + m['dy'], m['w'], in_=ph('strip_open', 0.32), tk=K((t0, CX, y + m['dy'], 1.04, 0, 'out'), (t0 + 0.5, CX, y + m['dy'], 1.0, 0), (t1, CX, y + m['dy'], 0.985, 0)),
        name='Word ' + name, slot='Word ' + name.split('_')[-1].upper(), sound=('Pop_1', 25))
    img('orn/divider.png', t0 + 0.08, t1, CX, y + 72, 300, in_=ph('strip_open', 0.4), name='Divider')


def scrim_bottom(t0, t1): img('orn/scrim_bottom.png', t0, t1, CX, SH - 380, SW + 4, name='Scrim')


def full(src, t0, t1, s0=1.0, s1=1.06, kind='clip', trim=0.0, dx=0, slot=None, in_=None, depth=0, speed=1):
    w = cover(depth) if depth else SW * 1.0
    tk = K((t0, CX, CY, s0, 0), (t1, CX + dx, CY, s1, 0))
    if kind == 'clip': return vid(src, t0, t1, CX, CY, w, trim=trim, tk=tk, slot=slot, in_=in_, depth=depth, speed=speed)
    return img(src, t0, t1, CX, CY, w, tk=tk, slot=slot, in_=in_, depth=depth)


def lit_diya(t0, t1, y, w=300, ignite=None, depth=0, ring=True):
    """the supplied bowl + a real flame that flickers + warm light; ignite = when the flame catches"""
    d = META['diya']; bh = w * d['aspect']; top = y - bh / 2; rim = top + d['rim'] * bh
    fw = w * 0.27; fh = fw * 700 / 300; fy = rim + 0.1 * bh - 0.88 * fh + fh / 2       # flame base sits in the oil
    tg = ignite if ignite is not None else t0
    img('orn/floor_shadow.png', t0, t1, CX, y + bh * 0.48, w * 1.3, opacity=0.7, depth=depth, name='Diya shadow')
    img('orn/glow_warm.png', tg, t1, CX, fy - fh * 0.1, w * 1.9, blend=SCREEN, opacity=0.85, depth=depth, in_=ph('fade', 0.5), name='Diya light')
    if ring: img('orn/dot_ring.png', tg + 0.2, t1, CX, fy - fh * 0.05, w * 1.35, opacity=0.9, depth=depth, in_=ph('fade', 0.8), tk=K((tg + 0.2, CX, fy - fh * 0.05, 0.94, 0), (t1, CX, fy - fh * 0.05, 1.0, 25)), name='Dotted ring')
    img('orn/diya_bowl.png', t0, t1, CX, y, w, depth=depth, name='Diya bowl')
    flick = [(tg, CX, fy, 1.0, 0, 'gentle')]; t = tg + 0.2; i = 0
    while t < t1:
        flick.append((t, CX + (1.5 if i % 2 else -1.5), fy, (1.05, 0.97, 1.03, 0.99)[i % 4], (2, -1.5, 1, -2)[i % 4], 'gentle')); t += 0.19; i += 1
    img('orn/flame.png', tg, t1, CX, fy, fw, blend=0, depth=depth, in_=ph('grow', 0.35), tk=K(*flick), name='Diya flame')


def letters(name, t0, t1, y, k=0.84, stagger=0.07):
    m = META[name]
    for i, L in enumerate(m['letters']):
        ts = t0 + i * stagger; x = CX + L['dx'] * k; yy = y + m['dy'] * k
        img(f"type/{L['file']}", ts, t1, x, yy, L['w'] * k, in_=ph('fade_up', 0.7), tk=K((ts, x, yy + 18, 1.0, 0, 'out'), (ts + 0.7, x, yy, 1.0, 0), (t1, x, yy, 1.0, 0)),
            name=f'Letter {i}', slot=None)


# ================================================================ the film
rect(0, DUR, '#050302', name='Black')

# ---- 0.00 - 2.97  ACT 1 · Ignition: darkness, a diya lights, gold strings descend, THIS DIWALI
IGN = beat(0) + 0.36
vid('bokeh_loop', 0, beat(3), CX, CY, 1000, blend=SCREEN, opacity=0.45, in_=ph('fade', 1.0), depth=500)
img('orn/lotus_mandala.png', 0.4, beat(3), CX, 700, 760, max_w=1000, opacity=0.2, depth=600, in_=ph('fade', 1.4),
    tk=K((0.4, CX, 700, 0.92, 0, 'gentle'), (beat(3), CX, 700, 1.0, 14)), name='Lotus mandala')
for x, L, dl, dp in [(108, 560, 0.95, 120), (612, 470, 1.12, 120), (250, 300, 1.3, 380), (470, 360, 1.2, 380)]:
    w = L * STR_R; yy = L / 2 - 10
    img('orn/gold_string.png', IGN + dl - 0.9, beat(3), x, yy, w, depth=dp, opacity=1.0 if dp < 200 else 0.6,
        tk=K((IGN + dl - 0.9, x, yy - L, 1, 0, 'out'), (IGN + dl - 0.9 + 1.1, x, yy, 1, 0, 'gentle'), (beat(3), x, yy + 6, 1, 0)), name='Gold string')
lit_diya(0.2, beat(3), 800, 300, ignite=IGN)
img('orn/flare.jpg', IGN - 0.05, IGN + 0.6, CX, 700, 700, max_w=900, blend=SCREEN, opacity=0.7, in_=ph('fade', 0.08), out=ph('fade', 0.4), name='Ignition flare', sound=('Smokey_06', 50))
T0 = beat(1) + 0.2
m = META['this_diwali']
img('type/this_diwali.png', T0, beat(3), CX, 440 + m['dy'], m['w'], in_=ph('strip_open', 0.7), slot='Title THIS DIWALI', name='THIS DIWALI')
img('orn/divider.png', T0 + 0.3, beat(3), CX, 492, 360, in_=ph('strip_open', 0.6), name='Divider')
flare(beat(3))

# ---- 2.97 - 6.26  ACT 2 · Rituals: full frame, split layout, framed card, a slow dissolve
c = [beat(3), beat(3) + BEAT / 2, beat(4) + BEAT / 2, beat(5), beat(5) + 0.58, beat(7)]     # 2.97 3.38 4.20 4.61 5.19 6.26
full('diya_macro', c[0], c[1], 1.0, 1.08, slot='Clip: diya macro')
# split: two photos slide in from opposite sides, a gold hairline between them
img('footage/panel_rangoli_marigold.jpg', c[1], c[2], CX, 316, 720, tk=K((c[1], -380, 316, 1, 0, 'out'), (c[1] + 0.32, CX, 316, 1, 0), (c[2], CX - 14, 316, 1, 0)), slot='Photo: rangoli (top panel)', sound=('Woosh_High_2', 35))
img('footage/panel_diya_rangoli.jpg', c[1] + 0.06, c[2], CX, 964, 720, tk=K((c[1] + 0.06, 1100, 964, 1, 0, 'out'), (c[1] + 0.38, CX, 964, 1, 0), (c[2], CX + 14, 964, 1, 0)), slot='Photo: diya on rangoli (bottom panel)')
img('orn/divider.png', c[1] + 0.25, c[2], CX, 640, 700, in_=ph('strip_open', 0.4), name='Split hairline')
full('thali', c[2], c[3], 1.04, 1.0, trim=0.5, slot='Clip: thali')
card('diya_ring', c[3], c[4], 'diya_ring_plate', trim=0.0, slot='Clip: diya ring')
full('footage/hands_lighting.jpg', c[4] - 0.25, c[5], 1.0, 1.07, kind='photo', dx=-12, in_=ph('fade', 0.25), slot='Photo: hands lighting diyas')
streak(c[4] + 0.2, 880)

# ---- 6.26 - 9.54  ACT 3 · People: LIGHT / LOVE / CELEBRATE, one per beat, same place every time
w0, w1, w2, w3 = beat(7), beat(8), beat(9), beat(11)
card('women', w0, w1, 'women_plate', trim=0.2, enter='down', slot='Clip: women with candles')
full('thali', w1, w2, 1.02, 1.08, trim=2.8, slot='Clip: thali (tilak)')
full('sparkler_woman', w2, w3 - 0.4, 1.0, 1.08, trim=0.5, slot='Clip: sparkler')
full('sparkler_woman', w3 - 0.4, w3, 1.08, 1.22, trim=0.5 + (w3 - 0.4 - w2), slot=None)
scrim_bottom(w0, w3)
word('w_light', w0 + 0.03, w1); word('w_love', w1 + 0.03, w2); word('w_celebrate', w2 + 0.03, w3 - 0.05)
vid('dust_b', w0, w3, CX, CY, SW, blend=SCREEN, opacity=0.55)

# ---- 9.54 - 12.83  ACT 4 · The title: fireworks sky, a flare sweep, DIWALI rises letter by letter
d0, d1 = beat(11), beat(15)
full('sky_wide', d0, d1, 1.0, 1.05, depth=300, slot='Clip: fireworks over the horizon')
rect(d0, d1, '#000000', 0.42, name='Title darkening')
img('orn/lotus_mandala.png', d0 + 0.2, d1, CX, 600, 700, max_w=1000, opacity=0.22, depth=450, in_=ph('fade', 0.9),
    tk=K((d0 + 0.2, CX, 600, 0.95, 0), (d1, CX, 600, 1.02, -12)), name='Lotus mandala')
vid('particle_ring', d0, d1, CX, 600, 980, blend=SCREEN, opacity=0.7, depth=200)
flare(d0, CX, 600, 1700)
img('orn/flare.jpg', d0 - 0.1, d0 + 0.7, CX, 600, 1300, max_w=900, blend=SCREEN, opacity=0.8, out=ph('fade', 0.4),
    tk=K((d0 - 0.1, -320, 600, 1, 0, 'out'), (d0 + 0.7, 1040, 600, 1, 0)), name='Flare sweep')
letters('diwali', d0 + 0.18, d1, 600)
img('orn/divider.png', d0 + 0.95, d1, CX, 700, 420, in_=ph('strip_open', 0.5), name='Divider')
mf = META['festival']
img('type/festival.png', d0 + 1.15, d1, CX, 752 + mf['dy'], mf['w'], in_=ph('fade_up', 0.6), name='FESTIVAL OF LIGHTS', slot='Line FESTIVAL OF LIGHTS', sound=('Smokey_09', 45))

# ---- 12.83 - 16.11  ACT 5 · The montage: half-beat cuts, a line that builds LIGHT • JOY • TOGETHERNESS
f = [round(beat(15) + i * BEAT / 2, 3) for i in range(9)]
full('fw_purple', f[0], f[1], 1.0, 1.08, slot='Clip: fireworks')
card('diya_macro', f[1], f[2], 'diya_macro_plate', trim=0.6, slot='Clip: diya macro')
full('women', f[2], f[3], 1.06, 1.0, trim=2.0, slot='Clip: women')
full('thali', f[3], f[4], 1.0, 1.06, trim=1.5, slot='Clip: thali')
card('diya_ring', f[4], f[5], 'diya_ring_plate', trim=3.0, enter='down', slot='Clip: diya ring')
full('sky_city', f[5], f[6], 1.0, 1.08, slot='Clip: city lights')
full('sparkler_woman', f[6], f[7], 1.06, 1.0, trim=3.5, slot='Clip: sparkler')
full('anaar', f[7], f[8], 1.0, 1.1, trim=1.0, slot='Clip: anaar')
scrim_bottom(f[0], f[8]); streak(f[4] - 0.1, 300)
parts = [('tag_light', f[1]), ('tag_dot', f[3]), ('tag_joy', f[3]), ('tag_dot', f[5]), ('tag_togetherness', f[5])]
PAD = 30.6; ink = [META[n]['w'] - 2 * PAD for n, _ in parts]; gap = 22; tot = sum(ink) + gap * (len(ink) - 1); k = min(1.0, 640 / tot); x = CX - tot * k / 2
for (n, t), iw in zip(parts, ink):
    cx_ = x + iw * k / 2; m = META[n]
    img(f'type/{n}.png', t, f[8], cx_, 1110 + m['dy'] * k, m['w'] * k, in_=ph('fade_up', 0.3), name='Tagline ' + n, slot=None)
    x += (iw + gap) * k
img('orn/divider.png', f[1], f[8], CX, 1050, 420, in_=ph('strip_open', 0.4), name='Divider')
flare(f[8])

# ---- 16.11 - 20.00  ACT 6 · Finale: the diya field, strings in depth, HAPPY DIWALI, fireworks, one diya stays
h0, fin = beat(19), beat(22)
full('footage/diya_rows.jpg', h0, 19.4, 1.0, 1.1, kind='photo', depth=250, dx=-10, slot='Photo: field of diyas (hero)')
img('orn/scrim_top.png', h0, 19.4, CX, 430, SW + 4, name='Scrim top'); img('orn/scrim_top.png', h0, 19.4, CX, 330, SW + 4, name='Scrim top 2'); rect(h0, 19.4, '#000000', 0.38, name='Hero darkening')
for x, L, dp in [(96, 470, 60), (624, 380, 60), (200, 260, 300)]:
    w = L * STR_R; yy = L / 2 - 10
    img('orn/gold_string.png', h0, 19.4, x, yy, w, depth=dp, opacity=1.0 if dp < 200 else 0.6, tk=K((h0, x, yy - L * 0.6, 1, 0, 'out'), (h0 + 1.2, x, yy, 1, 0, 'gentle'), (19.4, x, yy + 4, 1, 0)), name='Gold string')
mh, md, ms = META['happy'], META['diwali_final'], META['shubh']
img('type/happy.png', h0 + 0.4, 19.4, CX, 400 + mh['dy'], mh['w'], in_=ph('fade_up', 0.7), name='HAPPY', slot='Title HAPPY')
img('type/diwali_final.png', h0 + 0.75, 19.4, CX, 490 + md['dy'], md['w'] * 0.9, in_=ph('push_reveal', 1.0), tk=K((h0 + 0.75, CX, 490 + md['dy'], 1.0, 0), (19.4, CX, 490 + md['dy'], 1.03, 0)), name='DIWALI', slot='Title DIWALI', sound=('Smokey_06', 45))
img('orn/divider.png', h0 + 1.3, 19.4, CX, 578, 440, in_=ph('strip_open', 0.6), name='Divider')
img('type/shubh.png', h0 + 1.55, 19.4, CX, 642 + ms['dy'], ms['w'], in_=ph('fade_up', 0.6), name='Shubh Deepawali', slot='Line शुभ दीपावली')
vid('fw_orange', fin - 0.05, 19.4, CX, 330, SW, blend=SCREEN, opacity=0.85, in_=ph('fade', 0.12), out=ph('fade', 0.5), name='Fireworks (real, screen)')
img('orn/flare.jpg', fin, fin + 0.6, CX, 330, 1100, max_w=900, blend=SCREEN, opacity=0.6, in_=ph('fade', 0.06), out=ph('fade', 0.45), name='Burst flare')
vid('bokeh_loop', h0, 19.4, CX, CY, 1000, blend=SCREEN, opacity=0.35, depth=150, trim=0.5)
rect(19.0, DUR, '#050302', 1, in_=ph('fade', 0.8), name='Fade to black')
lit_diya(19.0, DUR, 760, 240, ignite=19.0, ring=True)

# ---- finishing: grade, grain, vignette
fx('colorBalance', 0, DUR, params={'redShift': 4, 'greenShift': 0, 'blueShift': -6}, name='Warm grade')
fx('grain', 0, DUR, params={'intensity': 7, 'size': 1.2})
fx('vignetting', 0, DUR, params={'strength': 35, 'softness': 65})

# ---------------------------------------------------------------- camera: slow, deliberate pushes (parallax through the depths)
cam = [(0, 0, 'gentle'), (beat(3) - 0.01, 150, 'hold'), (beat(3), 0, 'hold'), (d0 - 0.01, 0, 'hold'), (d0, 0, 'gentle'), (d1 - 0.01, 120, 'hold'),
       (d1, 0, 'hold'), (h0 - 0.01, 0, 'hold'), (h0, 0, 'gentle'), (DUR, 170, 'linear')]
keys = [dict(t=t, x=CX, y=CY, z=z, pan=0, tilt=0, roll=0, lens=1, ease=e) for t, z, e in cam]

r = copy.deepcopy(tpl)
r.update(title='Diwali Campaign 9x16', background='#050302', bpm=BPM, beat_offset=OFF, duration=DUR, texts=[])
r['studio_project'] = dict(tpl['studio_project'], mediaBin=bin_, manualOrder=True, persp={'on': False, 'order': 'z'})
r['studio_scene'] = {'camera': {'on': True, 'near': 320, 'fog': {'on': False, 'start': 4000, 'end': 5000}, 'keys': keys, 'shake': []},
                     'mirror': 'scale', 'items': items, 'order': order,
                     'note': 'Kinekit Studio recipe: Diwali campaign film, 20 s, 9:16. Footage, typography and ornaments are image / video layers; '
                             'the clips travel inside this file (studio_videos).'}
r['studio_media'] = media; r['studio_videos'] = videos
json.dump(r, open(OUT, 'w'))
print('items', len(items), 'images', len(media), 'clips', len(videos), 'MB', round(os.path.getsize(OUT) / 1e6, 2))
