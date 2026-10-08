"""DRIVEN - car beat-sync photo motion graphics, 18.6 s, 9:16, for Kinekit Studio -> KineMaster.

    python3 build_car.py ASSETS_DIR TEMPLATE_RECIPE OUT_RECIPE

Every photo with a car is two layers: the defocused plate far back and the car cut-out in front; the scene camera
pushes / drifts so they separate (real parallax). Cuts, punches, flashes, shakes and blur sit on the music's grid
(72.8 BPM: beat 0.8215 s, first beat 0.506 s, drop 2.97 s, break 7.5 s, big hit 7.90 s, last hits 16.11 / 17.76).
Strong beats get impact (scale punch, micro-shake, flash frame, blur); weak beats get smooth camera and longer holds.
The energy builds: two shots per bar, then three, then a cut every half beat, then the hero and a clean final hit.
"""
import base64, copy, io, json, os, subprocess, sys
from PIL import Image

A, TEMPLATE, OUT = sys.argv[1:4]
tpl = json.load(open(TEMPLATE)); META = json.load(open(f'{A}/meta.json'))
SW, SH, CX, CY, DUR = 720, 1280, 360, 640, 18.6
BPM, OFF = 73.04, 0.506
BEAT = 60 / BPM
SCREEN, F = 22, 1000
def beat(n): return round(OFF + n * BEAT, 3)


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


# ================================================================ the edit
rect(0, DUR, '#050505', name='Black')
b = [beat(n) for n in range(0, 24)]          # b[3] = 2.970 drop, b[9] = 7.899 big hit, b[19] = 16.114, b[21] = 17.757

# ---- 0.00 - 2.97  HOOK: three flash cuts on the kicks, then the ignition with DRIVEN, inside letterbox bars
for t0, t1, rel in ((0.03, 0.26, 'photo/crop_tail.jpg'), (0.26, 0.66, 'photo/crop_wheel.jpg'), (0.66, 0.87, 'photo/crop_racers.jpg')):
    flat(rel, t0, t1, punch(t0, t1, 1.12, 1.0)); flash(t0, 0.5, 0.05)
clip('ignition', 0.87, b[3], glide(0.87, b[3], 1.0, 1.12), trim=0.3, speed=0.8, slot='Clip ignition (hook)')
cam_move(0, 0.87, 0, 0); cam_move(0.87, b[3], 0, 60)
bars(0, b[3] + 0.05, close=0.01)
T1 = b[1] + 0.16
title('driven', T1, b[3], 600, ph('slice_in', 0.45), 0.92)
img('type/rule_red.png', T1 + 0.25, b[3], CX, 728, 260, cam=False, in_=ph('strip_open', 0.3), name='Red rule')
streak(b[2] + 0.28, 600, 'red')

# ---- 2.97 - 7.90  BUILD: two shots per bar, long smooth holds, impact only on the bar downbeats
# bar 1: the race (2.5D push, the cars separate from the track)
hit(b[3], big=True)
dual('17', b[3], b[4] + BEAT / 2, punch(b[3], b[4] + BEAT / 2, 1.16, 1.04, drift=(0, -10)), slot='Photo race cars (car layer)')
cam_move(b[3], b[4] + BEAT / 2, 0, 170, CX + 30, CX - 20)
chapter(1, b[3] + 0.1, b[4] + BEAT / 2)
clip('wheels', b[4] + BEAT / 2, b[5], whip(b[4] + BEAT / 2, b[5], 1), trim=0.6); blur(b[4] + BEAT / 2)
# bar 2: the Ferrari - a slow lateral pan across the wide photo, the car sliding over its own defocus
hit(b[5])
dual('16', b[5], b[6] + BEAT / 2, [(b[5], CX + 330, CY, 1.08, 0, 'out'), (b[5] + 0.25, CX + 300, CY, 1.04, 0), (b[6] + BEAT / 2, CX - 120, CY, 1.03, 0)], slot='Photo Ferrari (car layer)')
cam_move(b[5], b[6] + BEAT / 2, 0, 90, CX - 40, CX + 40)
chapter(2, b[5] + 0.1, b[6] + BEAT / 2)
clip('blue_supercar', b[6] + BEAT / 2, b[7], whip(b[6] + BEAT / 2, b[7], -1), trim=1.0); blur(b[6] + BEAT / 2); streak(b[6] + BEAT / 2 - 0.05, 420, 'white', d=-1)
# bar 3: the crowd - push in, the convertible lifts off the crowd; then the BREAK: rain on glass, letterbox closes
hit(b[7])
dual('19', b[7], b[8] + BEAT / 2, punch(b[7], b[8] + BEAT / 2, 1.12, 1.03), slot='Photo convertible + crowd (car layer)')
cam_move(b[7], b[8] + BEAT / 2, 0, 200, CX, CX, CY + 20, CY - 20)
chapter(3, b[7] + 0.1, b[8] + BEAT / 2)
BRK = b[8] + BEAT / 2                        # 7.49: the music drops out
flat('photo/crop_rain.jpg', BRK, b[9], glide(BRK, b[9], 1.0, 1.05), slot='Photo rain on glass (break)', in_=ph('fade', 0.12))
bars(BRK, b[9] + 0.02, close=0.22, open_=0.02)
label('built_to', BRK + 0.08, b[9], CX, 600, in_=ph('fade_up', 0.25))

# ---- 7.90 - 12.83  DRIVE: the big hit, three shots per bar, rotation punches and whips
hit(b[9], big=True)
dual('20', b[9], b[10], punch(b[9], b[10], 1.22, 1.05, rot=-3), slot='Photo rally car (car layer)')
cam_move(b[9], b[10], 0, 140, CX - 30, CX + 30)
title('move', b[9], b[10] - 0.02, 640, ph('punch_in', 0.22, 0.6), 1.0)
chapter(4, b[9] + 0.1, b[10])
clip('tunnel', b[10], b[10] + BEAT / 2, whip(b[10], b[10] + BEAT / 2, 1), trim=0.4, speed=1.8); blur(b[10])
flat('photo/crop_dust.jpg', b[10] + BEAT / 2, b[11], punch(b[10] + BEAT / 2, b[11], 1.1, 1.0, rot=2))
hit(b[11])
clip('challenger', b[11], b[11] + 0.58, punch(b[11], b[11] + 0.58, 1.12, 1.0), trim=0.5)
dual('17', b[11] + 0.58, b[12] + BEAT / 2, [(b[11] + 0.58, CX + 60, CY - 140, 1.55, 0, 'out'), (b[12] + BEAT / 2, CX + 40, CY - 160, 1.62, 0)])
cam_move(b[11] + 0.58, b[12] + BEAT / 2, 0, 110, CX + 30, CX - 30)
flat('photo/crop_flank16.jpg', b[12] + BEAT / 2, b[13], whip(b[12] + BEAT / 2, b[13], -1)); blur(b[12] + BEAT / 2)
hit(b[13])
dual('19', b[13], b[13] + 0.58, punch(b[13], b[13] + 0.58, 1.5, 1.38, x=CX - 70, y=CY + 160))
cam_move(b[13], b[13] + 0.58, 0, 80)
clip('ignition', b[13] + 0.58, b[14] + BEAT / 2, glide(b[13] + 0.58, b[14] + BEAT / 2, 1.04, 1.12), trim=2.2, speed=1.6)
flat('photo/crop_crowd.jpg', b[14] + BEAT / 2, b[15], whip(b[14] + BEAT / 2, b[15], 1)); blur(b[14] + BEAT / 2); streak(b[14] + BEAT / 2 - 0.05, 860, 'red')

# ---- 12.83 - 16.11  PEAK: a cut every half beat, alternating directions, flashes on the downbeats
seq = [('flat', 'photo/crop_tail.jpg'), ('flat', 'photo/crop_racers.jpg'), ('clip', 'tunnel'), ('flat', 'photo/crop_wheel.jpg'),
       ('dual', '20'), ('clip', 'blue_supercar'), ('flat', 'photo/crop_kerb.jpg'), ('clip', 'challenger')]
for i, (kind, src) in enumerate(seq):
    t0 = round(b[15] + i * BEAT / 2, 3); t1 = round(t0 + BEAT / 2, 3); d = 1 if i % 2 else -1
    keys = punch(t0, t1, 1.16, 1.04, rot=3 * d) if i in (0, 4) else whip(t0, t1, d, 1.06)
    if kind == 'flat': flat(src, t0, t1, keys)
    elif kind == 'clip': clip(src, t0, t1, keys, trim=1.6 + 0.3 * i, speed=1.4)
    else: dual(src, t0, t1, [(t0, CX + 40, CY, 1.3, 3 * d, 'out'), (t0 + 0.2, CX, CY, 1.18, 0), (t1, CX - 20, CY, 1.2, 0)]); cam_move(t0, t1, 0, 90)
    if i in (0, 4): hit(t0, big=i == 0)
    else: blur(t0, 12)
streak(b[16] - 0.05, 300, 'white'); streak(b[18] - 0.05, 980, 'red', d=-1)

# ---- 16.11 - 18.60  HERO + FINAL HIT: the Ferrari in 2.5D, DRIVEN / BY INSTINCT; last beat -> black, title stays, fade
hit(b[19], big=True)
dual('16', b[19], b[21], [(b[19], CX + 120, CY, 1.16, 0, 'out'), (b[19] + 0.3, CX + 100, CY, 1.08, 0), (b[21], CX + 20, CY, 1.12, 0)], slot='Photo Ferrari hero (car layer)')
cam_move(b[19], b[21], 0, 160, CX - 30, CX + 30)
chapter(5, b[19] + 0.1, b[21])
rect(b[19], b[21], '#000000', 0.25, name='Hero darkening')
title('driven', b[19] + 0.12, DUR, 1010, ph('slice_in', 0.4), 0.78)
img('type/rule_red.png', b[19] + 0.4, DUR, CX, 1112, 220, cam=False, in_=ph('strip_open', 0.3), name='Red rule')
label('by_instinct', b[20], DUR, CX, 1160, in_=ph('fade_up', 0.35))
flash(b[21], 0.9, 0.08); shake(b[21], 10, 0.8, 0.3)
rect(b[21], DUR, '#050505', 1, name='Final black')               # the last beat cuts to black; the title rides on top
title('driven', b[21], DUR, 1010, None, 0.78)
img('type/rule_red.png', b[21], DUR, CX, 1112, 220, cam=False, name='Red rule')
label('by_instinct', b[21], DUR, CX, 1160, in_=ph('fade', 0.01))
rect(DUR - 0.55, DUR, '#050505', 1, in_=ph('fade', 0.5), name='Fade out')

# ---- finishing
fx('grain', 0, DUR, params={'intensity': 6, 'size': 1.1})
fx('vignetting', 0, DUR, params={'strength': 32, 'softness': 60})

# camera keys in time order (each shot owns its window); everything outside a shot sits at rest
CAM.sort(key=lambda k: k['t'])
keys = [dict(t=0, x=CX, y=CY, z=0, pan=0, tilt=0, roll=0, lens=1, ease='hold')] + [k for k in CAM if k['t'] > 0] + [dict(t=DUR, x=CX, y=CY, z=0, pan=0, tilt=0, roll=0, lens=1, ease='hold')]
r = copy.deepcopy(tpl)
r.update(title='DRIVEN 9x16', background='#050505', bpm=BPM, beat_offset=OFF, duration=DUR, texts=[])
r['studio_project'] = dict(tpl['studio_project'], mediaBin=bin_, manualOrder=True, persp={'on': False, 'order': 'z'})
r['studio_scene'] = {'camera': {'on': True, 'near': 200, 'fog': {'on': False, 'start': 4000, 'end': 5000}, 'keys': keys, 'shake': SHAKE},
                     'mirror': 'scale', 'items': items, 'order': order,
                     'note': 'Kinekit Studio recipe: DRIVEN, car beat-sync photo motion graphics, 18.6 s, 9:16. Photos are 2.5D (car layer over a '
                             'defocused plate); clips travel inside this file.'}
r['studio_media'] = media; r['studio_videos'] = videos
json.dump(r, open(OUT, 'w'))
print('items', len(items), 'images', len(media), 'clips', len(videos), 'shakes', len(SHAKE), 'cam keys', len(keys), 'MB', round(os.path.getsize(OUT) / 1e6, 2))
