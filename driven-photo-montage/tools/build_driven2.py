"""DRIVEN 146 - photo motion-graphics montage cut to the 1:39-end section of the Beatsync edit, 22.74 s, 9:16, for Kinekit Studio.

    python3 build_driven2.py ASSETS_DIR TEMPLATE_RECIPE OUT_RECIPE

Music analysis (librosa, see analyze_music.py): 146 BPM, eighth note U = 0.20546 s, grid origin 0.0496 s. Each bar
(8 eighths) hits 808 + clap on slot 0, clap on slot 3, 808 on slot 5 (a 3-3-2), with a pickup kick on slot 7 in most
bars. Intro hit 0.04 / 0.26, quiet to 1.28, build bar with a snare roll, DROP 2.926, phrase 2 at 9.501, a bass cut
15.46-16.07, FINAL HIT 16.075, then the track rings out (silent by ~20.5 s).
Choreography: cuts and band landings on 0 / 3 / 5, camera steps forward on the hits, whips on the pickups, flash +
shake + impact zoom only on downbeats that open a phrase, speed-ramped pushes into the drop and the final hit.
Portrait photos are 2.5D (car cut-out over a defocused plate); landscape photos (16, 20) are sharp cards bleeding off
the sides over their own blurred backdrop, with the car on a nearer layer; 1.8:1 bands form the triptychs.
"""
import base64, copy, io, json, os, subprocess, sys
from PIL import Image

A, TEMPLATE, OUT = sys.argv[1:4]
tpl = json.load(open(TEMPLATE)); META = json.load(open(f'{A}/meta.json'))
SW, SH, CX, CY, DUR = 720, 1280, 360, 640, 22.74
BPM, OFF = 146.01, 0.0496
U = 60 / BPM / 2                    # one eighth note = 0.20546 s; the whole section sits on this grid
BEAT = 2 * U
SCREEN, F = 22, 1000
def T(i): return round(OFF + i * U, 3)              # eighth-note slot i (0 = the first grid line at 0.0496 s)
def S(bar, slot): return T(14 + 8 * bar + slot)     # bar 0 = the drop (2.926 s); slots 0..7 in the bar


media, videos, bin_ = {}, {}, []
def img_id(rel, max_w=None):
    mid = 'c_' + rel.replace('/', '_').rsplit('.', 1)[0]
    if mid in media: return mid
    im = Image.open(f'{A}/{rel}')
    if max_w and im.width > max_w: im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); png = im.mode == 'RGBA'
    (im.save(b, 'PNG', optimize=True) if png else im.convert('RGB').save(b, 'JPEG', quality=88, optimize=True))
    media[mid] = f"data:image/{'png' if png else 'jpeg'};base64," + base64.b64encode(b.getvalue()).decode(); return mid


def clip_id(name):
    vid = 'cv_' + name
    if vid in videos: return vid
    p = f'{A}/clips/{name}.mp4'
    videos[vid] = {'name': name, 'ext': 'mp4', 'data': 'data:video/mp4;base64,' + base64.b64encode(open(p, 'rb').read()).decode()}
    pr = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.split()
    w, h = map(int, pr[0].split(',')[:2]); bin_.append({'id': vid, 'name': name, 'kind': 'video', 'w': w, 'h': h, 'dur': round(float(pr[1]), 3), 'ext': 'mp4'}); return vid


items, order = [], []
base_photo = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'ph124')
base_decor = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'dc144')
base_fx = {i['effect']: i for i in tpl['studio_scene']['items'] if i['type'] == 'fx'}
nid = [0]
def new_id(p): nid[0] += 1; return f'{p}{nid[0]}'
def ph(kind, dur, amount=1): return {'preset': kind, 'dur': dur, 'stagger': 0, 'order': 'forward', 'amount': amount}


def K(*ks, depth=0):
    out = []
    for k in ks:
        t, x, y, s, r = k[:5]; e = k[5] if len(k) > 5 else 'linear'
        out.append(dict(t=round(t, 3), ease=e, x=round(x, 1), y=round(y, 1), depth=depth, rot=round(r, 2), s=round(s, 4), rx=0, ry=0))
    return out


def layer(t0, t1, x=CX, y=CY, w=SW, tk=None, in_=None, out=None, opacity=1, blend=0, depth=0, name='', slot=None, sound=None, cam=True):
    it = copy.deepcopy(base_photo)
    it.update(id=new_id('ph'), name=name, start=round(t0, 3), end=round(t1, 3), x=round(x, 1), y=round(y, 1), w=round(w, 1), depth=depth, cam=cam,
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
    it['video'] = {'src': 'vid:' + clip_id(clip), 'trimIn': round(trim, 3), 'speed': speed, 'volume': 0}; it['name'] = kw.get('name') or clip; return it


def rect(t0, t1, color, opacity=1, x=CX, y=CY, w=SW + 60, h=SH + 60, tk=None, in_=None, out=None, name='Panel', blend=0):
    it = copy.deepcopy(base_decor)
    it.update(id=new_id('dc'), name=name, start=round(t0, 3), end=round(t1, 3), x=x, y=y, w=w, h=h, color=color, alpha=1, cam=False, tk=tk or [], opacity=opacity, blend=blend)
    it['in'], it['out'] = in_, out; items.append(it); order.append(it['id']); return it


def fx(effect, t0, t1, kf=None, params=None, name=None):
    it = copy.deepcopy(base_fx.get(effect) or dict(base_fx['grain'], effect=effect, params={}, keys=[]))
    it.update(id=new_id('fx'), start=round(t0, 3), end=round(t1, 3), name=name or it['name'])
    if kf is not None: it['keys'] = kf
    if params: it['params'] = dict(it['params'], **params)
    items.append(it); order.append(it['id']); return it


# ---------------------------------------------------------------- the camera: per-shot moves, hard resets on the cuts, shakes on hits
CAM, SHAKE = [], []
def cam_move(t0, t1, z0=0, z1=120, x0=CX, x1=CX, y0=CY, y1=CY, ease='gentle', roll0=0, roll1=0):
    CAM.extend([dict(t=round(t0, 3), x=x0, y=y0, z=z0, pan=0, tilt=0, roll=roll0, lens=1, ease=ease),
                dict(t=round(t1 - 0.012, 3), x=x1, y=y1, z=z1, pan=0, tilt=0, roll=roll1, lens=1, ease='hold')])
def shake(t, amp=9, rot=0.8, dur=0.32): SHAKE.append(dict(start=round(t, 3), end=round(t + dur, 3), amp=amp, rot=rot, push=0, freq=11, seed=len(SHAKE) + 3, easeIn=0.005, easeOut=dur * 0.85))


# ---------------------------------------------------------------- shot builders
def cover_w(aspect, depth=0, extra=1.12):
    """width that covers the 9:16 frame (with headroom for moves) for a picture of this aspect at this depth"""
    base = max(SW, SH * aspect) * extra
    return base * (F + depth) / F


def dual(n, t0, t1, keys, depth_bg=420, slot=None, sound=None, in_=None):
    """2.5D photo: defocused plate far back + car cut-out in front, sharing one set of keys (screen-aligned at rest)"""
    m = META[f'photo_{n}']; asp = m['w'] / m['h']; w = cover_w(asp)
    kb = F / (F + depth_bg)
    bgk = [(k[0], CX + (k[1] - CX) / kb, CY + (k[2] - CY) / kb, k[3], k[4]) + tuple(k[5:]) for k in keys]
    img(f'photo/bg_{n}.jpg', t0, t1, bgk[0][1], bgk[0][2], w / kb, max_w=1600, depth=depth_bg, tk=K(*bgk, depth=depth_bg), name=f'Plate {n}', in_=in_)
    img(f'photo/fg_{n}.png', t0, t1, keys[0][1], keys[0][2], w, max_w=1600, tk=K(*keys), name=f'Car {n}', slot=slot or f'Photo {n} (car layer; plate under it)', sound=sound, in_=in_)


def flat(rel, t0, t1, keys, slot=None, sound=None, in_=None, aspect=9 / 16):
    img(rel, t0, t1, keys[0][1], keys[0][2], cover_w(aspect, extra=1.06), max_w=900, tk=K(*keys), slot=slot or rel.split('/')[-1], sound=sound, in_=in_)


def clip(name, t0, t1, keys, trim=0.0, speed=1, slot=None, sound=None):
    vid(name, t0, t1, keys[0][1], keys[0][2], SW * 1.06, trim=trim, speed=speed, tk=K(*keys), slot=slot or f'Clip {name}', sound=sound)


def punch(t0, t1, s_hit=1.14, s_end=1.0, x=CX, y=CY, rot=0, drift=(0, 0)):
    """impact: in big, settle fast (ease out), then glide"""
    return [(t0, x, y, s_hit, rot, 'out'), (t0 + 0.22, x, y, s_end + 0.02, 0, 'linear'), (t1, x + drift[0], y + drift[1], s_end, 0)]


def glide(t0, t1, s0=1.0, s1=1.06, x0=CX, x1=CX, y0=CY, y1=CY):
    return [(t0, x0, y0, s0, 0, 'linear'), (t1, x1, y1, s1, 0)]


def whip(t0, t1, frm=1, s=1.04, x=CX, y=CY, drift=-20):
    """slides in fast from one side (pairs with directional blur on the cut)"""
    return [(t0, x + frm * 420, y, s, 0, 'out'), (t0 + 0.16, x, y, s, 0, 'linear'), (t1, x + drift * frm, y, s + 0.03, 0)]


def flash(t, op=0.75, dur=0.067): rect(t, t + dur, '#FFFFFF', op, name='Flash frame')
def blur(t, strength=14, dur=0.16):
    fx('poisonBlur', t - dur / 2, t + dur / 2, [{'t': 0, 'ease': 'in', 'p': {'strength': 0}}, {'t': dur / 2, 'ease': 'out', 'p': {'strength': strength}}, {'t': dur, 'ease': 'linear', 'p': {'strength': 0}}], name='Directional blur')
def zoomhit(t, strength=7): fx('chromaticZoom', t - 0.02, t + 0.26, [{'t': 0, 'ease': 'out', 'p': {'strength': strength}}, {'t': 0.28, 'ease': 'linear', 'p': {'strength': 0}}], name='Impact zoom')
def streak(t, y, color='white', dur=0.4, d=1):
    img(f'type/streak_{color}.png', t, t + dur, CX, y, 1500, max_w=1400, blend=SCREEN, cam=False, opacity=0.85, out=ph('fade', 0.15),
        tk=K((t, CX - d * 700, y, 1, 0, 'out'), (t + dur, CX + d * 700, y, 1, 0)), name='Light streak')
def hit(t, big=False):
    flash(t, 0.85 if big else 0.6); shake(t, 12 if big else 8, 1.0 if big else 0.6, 0.36 if big else 0.28)
    if big: zoomhit(t, 8)


def bars(t0, t1, close=0.3, open_=0.18, hgt=170):
    """cinematic letterbox: two black bars slide in, hold, snap out"""
    for y, sgn in ((hgt / 2, -1), (SH - hgt / 2, 1)):
        ks = [(t0, CX, y + sgn * hgt, 1, 0, 'out'), (t0 + close, CX, y, 1, 0, 'linear')]
        if open_ >= 0.06: ks += [(t1 - open_, CX, y, 1, 0, 'in'), (t1, CX, y + sgn * hgt, 1, 0)]   # shorter: just cut on the hit
        rect(t0, t1, '#000000', 1, CX, y, SW + 40, hgt, tk=K(*ks), name='Letterbox bar')


def label(name, t0, t1, x, y, cam=False, in_=None):
    m = META[name]; img(f'type/{name}.png', t0, t1, x, y + m['dy'], m['w'], cam=cam, in_=in_ or ph('fade', 0.15), name='Label ' + name)


def chapter(n, t0, t1):
    """editorial counter, top-left: 0n + a short red rule"""
    m = META[f'n{n}']; x = 48 + m['ink'] / 2
    img(f'type/n{n}.png', t0, t1, x, 92 + m['dy'], m['w'], cam=False, in_=ph('fade', 0.12), name=f'Chapter 0{n}')
    img('type/rule_red.png', t0 + 0.05, t1, 48 + 22, 120, 44, cam=False, in_=ph('strip_open', 0.2), name='Red rule')


def title(name, t0, t1, y, in_, w_scale=1.0, cam=False, tk=None):
    m = META[name]; img(f'type/{name}.png', t0, t1, CX, y + m['dy'], m['w'] * w_scale, cam=cam, in_=in_, tk=tk, name='Title ' + name, slot='Title ' + name.upper())


# ================================================================ helpers for this cut
def card(n, t0, t1, keys, cw=700, pop=-70, name=None):
    """landscape photo as a sharp card over its own dark, blurred backdrop; the car sits on a layer a little nearer the
    camera (aligned at rest), so every camera move separates it from the card"""
    m = META[f'photo_{n}']; asp = m['w'] / m['h']
    img(f'photo/soft_{n}.jpg', t0, t1, CX, CY, cover_w(asp, 650, 1.3), depth=650, name=f'Backdrop {n}')
    img(f'photo/card_{n}.jpg', t0, t1, keys[0][1], keys[0][2], cw, max_w=1080, tk=K(*keys), name=f'Card {n}')
    kc = F / (F + pop)
    ck = [(k[0], CX + (k[1] - CX) / kc, CY + (k[2] - CY) / kc, k[3], k[4]) + tuple(k[5:]) for k in keys]
    img(f'photo/fg_{n}.png', t0, t1, ck[0][1], ck[0][2], cw / kc, max_w=1080, depth=pop, tk=K(*ck, depth=pop), name=f'Car {n}',
        slot=name or f'Photo {n} (car layer; card under it)')
    return m['h'] / m['w'] * cw


def band(rel, hit_t, t1, y, frm, extra=(), lead=0.12, drift=14):
    """a 1.8:1 strip of a photo that slides in and LANDS on the hit, then drifts on; extra = more keys (exits, steps)"""
    keys = [(hit_t - lead, CX + frm * 780, y, 1, 0, 'out'), (hit_t, CX, y, 1, 0, 'linear')]
    keys += list(extra) or [(t1, CX - frm * drift, y, 1, 0)]
    img(rel, hit_t - lead, t1, CX, y, SW, max_w=1080, cam=False, tk=K(*keys), name='Band ' + rel.split('_', 1)[-1][:-4], slot='Band ' + rel.split('/')[-1])


def into(t0, land, t1, frm=1, s=1.04, x=CX, y=CY, drift=-16, exit_at=None, exit_dir=-1):
    """whip in from a side, decelerate and land exactly on `land` (the beat), glide; optional whip out at the end"""
    ks = [(t0, x + frm * 430, y, s, 0, 'out'), (land, x, y, s, 0, 'linear')]
    if exit_at: ks += [(exit_at, x + drift, y, s + 0.02, 0, 'in'), (t1, x + exit_dir * 430, y, s + 0.02, 0)]
    else: ks += [(t1, x + drift, y, s + 0.03, 0)]
    return ks


def stairs(t0, t1, hits, step=55, z0=0, x0=CX, x1=CX, y0=CY, y1=CY, creep=12):
    """the camera steps forward on each hit (fast start, settles in 0.2 s) and creeps between them: a push choreographed
    to the 3-3-2 pattern instead of one continuous zoom"""
    z = z0; f = lambda t: (t - t0) / (t1 - t0)
    pts = [(t0, z, 'linear')]
    for h in hits:
        z += creep * 0.5; pts.append((h, z, 'out')); z += step; pts.append((min(h + 0.2, t1 - 0.03), z, 'linear'))
    pts.append((t1 - 0.012, z + creep, 'hold'))
    for t, zz, e in pts:
        CAM.append(dict(t=round(t, 3), x=round(x0 + (x1 - x0) * f(t), 1), y=round(y0 + (y1 - y0) * f(t), 1), z=round(zz, 1), pan=0, tilt=0, roll=0, lens=1, ease=e))


def ramp_fx(t0, t1, strength=10):
    """speed-ramp lead-in: the impact zoom builds while the camera accelerates into the cut"""
    fx('chromaticZoom', t0, t1, [{'t': 0, 'ease': 'in', 'p': {'strength': 0}}, {'t': round(t1 - t0, 3), 'ease': 'linear', 'p': {'strength': strength}}], name='Ramp zoom')


def rule(t0, t1, y, w=120, color='red'):
    img(f'type/rule_{color}.png', t0, t1, CX, y, w, cam=False, in_=ph('strip_open', 0.22), name='Rule')


# ================================================================ the edit (music: the clip's 1:39 - end, 146 BPM, 3-3-2 groove)
rect(0, DUR, '#050505', name='Black')

# ---- INTRO 0.00 - 1.28: the opening double hit lands on a single sharp band, then the clap opens into the quiet rain shot
HA, HB, C2 = 0.04, T(1), T(2)
img('photo/band16_tail.jpg', HA, C2, CX, CY, SW, max_w=1080, cam=False, name='Band tail lights', slot='Band tail lights (intro)',
    tk=K((HA, CX, CY, 1.12, 0, 'out'), (HA + 0.16, CX, CY, 1.02, 0, 'linear'), (HB, CX, CY, 1.0, 0, 'out'), (HB + 0.03, CX, CY, 1.07, 0, 'out'), (HB + 0.2, CX, CY, 1.03, 0, 'linear'), (C2, CX, CY, 1.04, 0)))
flash(HA, 0.55, 0.05); zoomhit(HB, 4); rule(HB, C2, CY + 228, 90)
flat('photo/pc18_rain.jpg', C2, T(6), [(C2, CX, CY + 8, 1.0, 0, 'gentle'), (T(6), CX, CY - 8, 1.05, 0)], slot='Photo rain (quiet intro)', in_=ph('fade', 0.1))
cam_move(0, T(6), 0, 0)

# ---- BUILD 1.28 - 2.93: cuts tighten with the snare roll; the last shot accelerates (speed ramp) into the drop
dual('17', T(6), T(9), [(T(6), CX, CY, 1.04, 0, 'linear'), (T(9), CX, CY, 1.04, 0)], slot='Photo race (car layer)')
cam_move(T(6), T(9), 0, 150, CX + 20, CX - 10, ease='in')
flat('photo/pc19_crowd.jpg', T(9), T(10), punch(T(9), T(10), 1.08, 1.0)); shake(T(9), 4, 0.3, 0.2)
flat('photo/pc17_kerb.jpg', T(10), T(12), punch(T(10), T(12), 1.08, 1.0, rot=2)); shake(T(10), 4, 0.3, 0.2)
dual('19', T(12), S(0, 0), [(T(12), CX, CY, 1.03, 0, 'linear'), (S(0, 0), CX, CY, 1.03, 0)], slot='Photo convertible (car layer)')
cam_move(T(12), S(0, 0), 0, 340, ease='in'); ramp_fx(T(12), S(0, 0), 9); blur(S(0, 0) - 0.05, 10, 0.1)

# ---- DROP bar 0 (2.93): the Ferrari card; the camera steps in on the 3 and the 5
hit(S(0, 0), big=True)
ch = card('16', S(0, 0), S(1, 0), [(S(0, 0), CX, CY, 1.14, 0, 'out'), (S(0, 0) + 0.25, CX, CY, 1.01, 0, 'linear'), (S(1, 0), CX, CY, 1.0, 0)], cw=880, name='Photo Ferrari (drop)')
stairs(S(0, 0), S(1, 0), [S(0, 3), S(0, 5)], 60, x0=CX - 20, x1=CX + 30)
rule(S(0, 3), S(1, 0), CY + ch / 2 + 34); shake(S(0, 3), 4, 0.3, 0.22); streak(S(0, 5) - 0.04, CY - ch / 2 - 26, 'white')

# ---- bar 1 (4.57): the convertible + crowd in 2.5D; the pickup on the 7 whips it out
flash(S(1, 0), 0.45); shake(S(1, 0), 7, 0.5, 0.26)
dual('19', S(1, 0), S(1, 7), [(S(1, 0), CX, CY, 1.10, 0, 'out'), (S(1, 0) + 0.22, CX, CY, 1.03, 0, 'linear'), (S(1, 7) - 0.1, CX + 10, CY, 1.04, 0, 'in'), (S(1, 7), CX - 430, CY, 1.04, 0)])
stairs(S(1, 0), S(1, 7), [S(1, 3), S(1, 5)], 55, y0=CY + 25, y1=CY - 25)
blur(S(1, 7) + 0.04, 16, 0.24)

# ---- bar 2 (6.21): the rally card whips in on the pickup and lands on the downbeat
ch = card('20', S(1, 7), S(3, 0), [(S(1, 7), CX + 460, CY, 1.04, 0, 'out'), (S(2, 0), CX, CY, 1.02, 0, 'linear'), (S(3, 0), CX - 12, CY, 1.0, 0)], cw=880, name='Photo rally (bar 2)')
shake(S(2, 0), 6, 0.4, 0.24)
stairs(S(1, 7), S(3, 0), [S(2, 3), S(2, 5)], 55, x0=CX + 30, x1=CX - 30)
streak(S(2, 5) - 0.04, CY + ch / 2 + 30, 'red', d=-1)

# ---- bar 3 (7.86): TRIPTYCH - one band lands on each hit of the 3-3-2; the fill steps them; the pickup throws them out
for rel, slot, y, frm in (('photo/band16_flank.jpg', 0, 220, -1), ('photo/band17_racers.jpg', 3, 640, 1), ('photo/band19_wheel.jpg', 5, 1060, -1)):
    h = S(3, slot); st = -frm * 26
    band(rel, h, S(4, 0), y, frm, extra=[(S(3, 6), CX - frm * 10, y, 1, 0, 'out'), (S(3, 6) + 0.12, CX - frm * 10 + st, y, 1, 0, 'in'),
                                         (S(3, 7), CX - frm * 12 + st, y, 1, 0, 'in'), (S(4, 0), CX - frm * 760, y, 1, 0)])
hit(S(3, 0)); shake(S(3, 3), 5, 0.3, 0.22); shake(S(3, 5), 5, 0.3, 0.22); blur(S(3, 7) + 0.1, 14, 0.2)

# ---- bar 4 (9.50): second phrase - the big pull-out reveal of the race, then cuts on the 3 and the 5
hit(S(4, 0), big=True)
dual('17', S(4, 0), S(4, 3), [(S(4, 0), CX, CY, 1.04, 0, 'linear'), (S(4, 3), CX, CY, 1.04, 0)], slot='Photo race (pull-out)')
cam_move(S(4, 0), S(4, 3), 300, 30, CX - 20, CX + 10, ease='out')
flat('photo/pc19_crowd.jpg', S(4, 3), S(4, 5), punch(S(4, 3), S(4, 5), 1.10, 1.0)); shake(S(4, 3), 5, 0.3, 0.22); zoomhit(S(4, 3), 4)
card('20', S(4, 5), S(4, 7), [(S(4, 5), CX - 40, CY, 1.12, -2, 'out'), (S(4, 5) + 0.2, CX, CY, 1.02, 0, 'linear'), (S(4, 7) - 0.08, CX + 6, CY, 1.03, 0, 'in'), (S(4, 7), CX + 430, CY, 1.03, 0)], cw=860)
cam_move(S(4, 5), S(4, 7), 0, 60, ease='out'); shake(S(4, 5), 6, 0.4, 0.24)

# ---- bar 5 (11.14): three shots, a rotation punch on the 3, a zoomed 2.5D hit on the 5
flat('photo/pc17_racers.jpg', S(4, 7), S(5, 3), into(S(4, 7), S(5, 0), S(5, 3), -1, 1.06)); blur(S(4, 7) + 0.05, 16, 0.22)
flash(S(5, 0), 0.45); shake(S(5, 0), 6, 0.4, 0.24)
card('16', S(5, 3), S(5, 5), [(S(5, 3), CX, CY, 1.13, -3, 'out'), (S(5, 3) + 0.22, CX, CY, 1.01, 0, 'linear'), (S(5, 5), CX, CY, 1.0, 0)], cw=880)
cam_move(S(5, 3), S(5, 5), 0, 60, ease='out'); shake(S(5, 3), 5, 0.3, 0.22)
dual('19', S(5, 5), S(5, 7), punch(S(5, 5), S(5, 7), 1.28, 1.18, x=CX - 50, y=CY + 110)); cam_move(S(5, 5), S(5, 7), 0, 60, ease='out'); zoomhit(S(5, 5), 5)

# ---- bar 6 (12.79): fastest - a cut on every accent (7, 0, 1, 3, 5, 7)
flat('photo/pc19_car.jpg', S(5, 7), S(6, 1), into(S(5, 7), S(6, 0), S(6, 1), 1, 1.05)); blur(S(5, 7) + 0.05, 16, 0.22)
flash(S(6, 0), 0.5); shake(S(6, 0), 7, 0.5, 0.24)
card('20', S(6, 1), S(6, 3), [(S(6, 1), CX, CY, 1.12, 2, 'out'), (S(6, 1) + 0.2, CX, CY, 1.02, 0, 'linear'), (S(6, 3), CX, CY, 1.0, 0)], cw=880)
cam_move(S(6, 1), S(6, 3), 0, 50, ease='out')
dual('17', S(6, 3), S(6, 5), punch(S(6, 3), S(6, 5), 1.24, 1.14, x=CX + 40, y=CY - 60)); cam_move(S(6, 3), S(6, 5), 0, 70, ease='out'); shake(S(6, 3), 5, 0.3, 0.22); zoomhit(S(6, 3), 4)
flat('photo/pc17_kerb.jpg', S(6, 5), S(7, 0), [(S(6, 5), CX, CY, 1.10, -2, 'out'), (S(6, 5) + 0.2, CX, CY, 1.02, 0, 'linear'), (S(6, 7), CX - 8, CY, 1.03, 0, 'in'), (S(7, 0), CX - 430, CY, 1.03, 0)])
shake(S(6, 5), 5, 0.3, 0.22); blur(S(7, 0) - 0.08, 14, 0.2)

# ---- bar 7 (14.43): triptych reprise, faster (0, 2, 3); the break hangs it in the air; the clap sucks into the final hit
for rel, slot, y, frm in (('photo/band20_car.jpg', 0, 220, 1), ('photo/band16_tail.jpg', 2, 640, -1), ('photo/band19_crowd.jpg', 3, 1060, 1)):
    h = S(7, slot); dy = {220: -34, 640: 0, 1060: 34}[y]
    ex = [(S(7, 4), CX - frm * 8, y, 1, 0, 'gentle'), (S(7, 7), CX - frm * 16, y + dy, 1.0 if dy else 1.03, 0, 'in')]
    ex += [(S(8, 0), CX - frm * 16, y + dy * 14, 1, 0)] if dy else [(S(8, 0), CX, y, 1.9, 0)]
    band(rel, h, S(8, 0), y, frm, extra=ex)
hit(S(7, 0)); shake(S(7, 2), 5, 0.3, 0.2); shake(S(7, 3), 6, 0.4, 0.22)
ramp_fx(S(7, 7), S(8, 0), 10)

# ---- FINAL HIT bar 8 (16.08): the Ferrari hero; DRIVEN lands on the tail's 3, BY INSTINCT on the 6; slow pull-out as the
#      music rings out; picture fades first, the title last; black to the end of the section
HERO = S(8, 0); END_PIC = 20.4
hit(HERO, big=True)
ch = card('16', HERO, END_PIC + 0.05, [(HERO, CX, 560, 1.14, 0, 'out'), (HERO + 0.28, CX, 560, 1.02, 0, 'linear'), (S(9, 0), CX, 560, 1.0, 0, 'gentle'), (END_PIC, CX, 560, 0.97, 0)], cw=860, name='Photo Ferrari (hero)')
stairs(HERO, S(9, 0), [S(8, 3)], 45, x0=CX - 15, x1=CX + 15)
cam_move(S(9, 0), END_PIC, 63, -40, CX + 15, CX + 15, ease='gentle')
TY = 560 + ch / 2 + 150
title('driven', S(8, 3), DUR, TY, ph('punch_in', 0.22, 0.5), 0.6)
rule(S(8, 3) + 0.1, DUR, TY + 112, 150)
label('by_instinct', S(8, 6), DUR, CX, TY + 152, in_=ph('fade_up', 0.4))
rect(19.4, DUR, '#050505', 1, in_=ph('fade', 1.0), name='Picture fade')
order.remove(items[-1]['id']); order.insert(order.index(next(i['id'] for i in items if i['name'] == 'Title driven')), items[-1]['id'])
rect(20.5, DUR, '#050505', 1, in_=ph('fade', 0.9), name='Title fade')

# ---- finishing
fx('grain', 0, DUR, params={'intensity': 5, 'size': 1.0})
fx('vignetting', 0, DUR, params={'strength': 28, 'softness': 60})

# shakes are position-only: a 0.5 degree wobble is invisible but would put Angle keys on every layer it touches
for sh in SHAKE: sh['rot'] = 0
CAM.sort(key=lambda k: k['t'])
keys = [dict(t=0, x=CX, y=CY, z=0, pan=0, tilt=0, roll=0, lens=1, ease='hold')] + [k for k in CAM if k['t'] > 0] + [dict(t=DUR, x=CX, y=CY, z=0, pan=0, tilt=0, roll=0, lens=1, ease='hold')]
r = copy.deepcopy(tpl)
r.update(title='DRIVEN 146 9x16', background='#050505', bpm=BPM, beat_offset=OFF, duration=DUR, texts=[])
r['studio_project'] = dict(tpl['studio_project'], mediaBin=bin_, manualOrder=True, persp={'on': False, 'order': 'z'})
r['studio_scene'] = {'camera': {'on': True, 'near': 200, 'fog': {'on': False, 'start': 4000, 'end': 5000}, 'keys': keys, 'shake': SHAKE},
                     'mirror': 'scale', 'items': items, 'order': order,
                     'note': 'Kinekit Studio recipe: DRIVEN, photo montage cut to the 1:39-end section of the Beatsync edit (146 BPM, 3-3-2), 22.74 s, 9:16. '
                             'Car photos are 2.5D (car layer over a defocused plate or card).'}
r['studio_media'] = media; r['studio_videos'] = videos
json.dump(r, open(OUT, 'w'))
print('items', len(items), 'images', len(media), 'shakes', len(SHAKE), 'cam keys', len(keys), 'MB', round(os.path.getsize(OUT) / 1e6, 2))
