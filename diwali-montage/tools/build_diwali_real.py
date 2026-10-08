"""Premium 20 s Diwali montage (9:16) for Kinekit Studio -> KineMaster, cut from your footage: clips from the source
video, your photos and cleaned elements from the zip. The clips travel inside the recipe (studio_videos).

    python3 build_diwali_real.py ASSETS_DIR MEDIA_DIR TEMPLATE_RECIPE WIDTHS_JSON OUT_RECIPE

Cut on the music's grid (72.8 BPM: beat 0.8215 s, first beat 0.506 s; the drop lands at 2.97 s).
  0.00 - 2.97  darkness, drifting gold particles, a diya ignites, slow push in, THIS DIWALI strip reveal + gold edge
  2.97 - 6.26  rapid montage diya > rangoli > marigolds > sweets > decorations > hands lighting diyas (slow)
  6.26 - 9.54  people / gifts / celebration with LIGHT, LOVE, CELEBRATE on the beats (punch + blur + shake)
  9.54 - 12.83 golden sweep reveals DIWALI assembling from particles, firework trails orbit, mandala, bursts
 12.83 - 16.11 fastest section: eight half-beat cuts, LIGHT / JOY / TOGETHERNESS flashes, mandala + streaks
 16.11 - 20.00 hero shot, slow push, HAPPY DIWALI, firework on the last beat, fade to black, one diya stays
"""
import base64, copy, io, json, os, sys
from PIL import Image

ASSETS, MEDIA, TEMPLATE, WIDTHS, OUT = sys.argv[1:6]
tpl = json.load(open(TEMPLATE))
WID = json.load(open(WIDTHS))
SW, SH, CX, CY = 720, 1280, 360, 640
DUR = 20.0
BPM, OFF = 73.04, 0.506
BEAT = 60 / BPM
GOLD, CREAM, AMBER = '#F2C46D', '#FFF1D6', '#FFB347'
SCREEN, ADD = 22, 1


def beat(n): return round(OFF + n * BEAT, 3)
def half(n): return round(OFF + (n + 0.5) * BEAT, 3)


# ---------------------------------------------------------------- media
media = {}


def add_media(mid, path, max_w=None):
    if mid in media: return mid
    im = Image.open(path)
    if max_w and im.width > max_w: im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); png = im.mode == 'RGBA'
    (im.save(b, 'PNG', optimize=True) if png else im.convert('RGB').save(b, 'JPEG', quality=86, optimize=True))
    media[mid] = f"data:image/{'png' if png else 'jpeg'};base64," + base64.b64encode(b.getvalue()).decode()
    return mid


PHOTO = {k: add_media('ph_' + k, f'{MEDIA}/photos/{k}.jpg', 720) for k in ['diya_dark', 'diya_rows', 'rangoli_marigold', 'diya_rangoli', 'hands_lighting']}
EL = {k: add_media('el_' + k, f'{MEDIA}/elements/{k}.png', 900) for k in ['diya', 'rangoli_medallion', 'lantern', 'title_happy_diwali', 'fireworks_gold',
      'fireworks_multi', 'diya_swirl', 'mandala_redgold', 'lanterns', 'swirl_wave', 'swirl_s', 'arc', 'rangoli_diyas']}
_l = Image.open(f'{MEDIA}/elements/lantern.png'); _p = os.path.join(os.path.dirname(OUT) or '.', '.lantern_flip.png'); _l.transpose(Image.FLIP_LEFT_RIGHT).save(_p)
EL['lantern_flip'] = add_media('el_lantern_flip', _p, 500); os.remove(_p)
CLIPS = ['diya_macro', 'thali', 'diya_ring', 'women', 'sparkler_woman', 'sky_wide', 'fw_purple', 'sky_city', 'anaar',
         'bokeh_loop', 'particle_ring', 'dust_a', 'dust_b']   # the last four: particle overlays (black background, screen blend)
videos, bin_ = {}, []
for k in CLIPS:
    p = f'{MEDIA}/clips/{k}.mp4'
    videos['dw_' + k] = {'name': k, 'ext': 'mp4', 'data': 'data:video/mp4;base64,' + base64.b64encode(open(p, 'rb').read()).decode()}
    pr = __import__('subprocess').run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.split()
    vw, vh = map(int, pr[0].split(',')[:2]); dur = float(pr[1])
    bin_.append({'id': 'dw_' + k, 'name': k, 'kind': 'video', 'w': vw, 'h': vh, 'dur': round(dur, 3), 'ext': 'mp4'})
# slot -> footage. ('clip', name, trim in s) or ('photo', name). A slot used twice continues its clip.
MEDIA_FOR = {1: ('photo', 'diya_dark'), 2: ('clip', 'diya_macro', 0.0), 3: ('photo', 'rangoli_marigold'), 4: ('photo', 'diya_rangoli'),
             5: ('clip', 'thali', 0.5), 6: ('clip', 'diya_ring', 0.0), 7: ('photo', 'hands_lighting'), 8: ('clip', 'women', 0.2),
             9: ('clip', 'thali', 2.8), 10: ('clip', 'sparkler_woman', 0.5), 11: ('clip', 'sky_wide', 0.0), 12: ('clip', 'fw_purple', 0.0),
             13: ('clip', 'diya_macro', 0.6), 14: ('clip', 'women', 2.0), 15: ('clip', 'thali', 1.5), 16: ('clip', 'diya_ring', 3.0),
             17: ('clip', 'sky_city', 0.0), 18: ('clip', 'sparkler_woman', 3.5), 19: ('clip', 'anaar', 1.0), 20: ('photo', 'diya_rows')}
V = {k: add_media('vfx_' + k, f'{ASSETS}/vfx/{k}.png', mw) for k, mw in [
    ('particles_far', 720), ('particles_mid', 720), ('particles_near', 720), ('flame', 300), ('bloom', 700), ('streak', 1400),
    ('sweep', 900), ('firework_gold', 900), ('firework_saffron', 900), ('firework_ember', 900), ('trail_arc', 1000), ('trail_arc_b', 1000),
    ('mandala_gold', 1000), ('dust_burst', 900), ('gold_rule', 700)]}
SLOT = {1: 'Diya close-up in darkness (macro, flame catches)', 2: 'Diya flame, tight', 3: 'Rangoli top-down', 4: 'Marigold flowers',
        5: 'Mithai / sweets', 6: 'Festive decorations, fairy-light bokeh', 7: 'Hands lighting diyas (slow, emotional)',
        8: 'People in traditional clothing', 9: 'Exchanging gifts', 10: 'Family celebrating, sparklers', 11: 'Night bokeh behind DIWALI',
        12: 'Fireworks in the sky', 13: 'Rows of diyas', 14: 'Family celebration', 15: 'Sweets close-up', 16: 'Rangoli with diyas',
        17: 'City lights at night', 18: 'Smiling faces', 19: 'Fireworks / anaar fountain', 20: 'Hero: Diwali night, diyas + fireworks'}
KIND = {4: 'Photo', 5: 'Photo', 15: 'Photo', 16: 'Photo'}

# ---------------------------------------------------------------- builders
items, texts, order = [], [], []
base_photo = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'ph124')
base_decor = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'dc144')
base_fx = {i['effect']: i for i in tpl['studio_scene']['items'] if i['type'] == 'fx'}
base_text = tpl['texts'][0]
nid = [0]


def new_id(p): nid[0] += 1; return f'{p}{nid[0]}'


def ph(kind, dur, amount=1, stagger=0, order_='forward'):
    return {'preset': kind, 'dur': dur, 'stagger': stagger, 'order': order_, 'amount': amount}


def keys(*ks):
    """transform keys: (t, x, y, s, rot, ease)"""
    return [dict(t=round(t, 3), ease=e, x=round(x, 1), y=round(y, 1), depth=0, rot=r, s=round(s, 4), rx=0, ry=0) for t, x, y, s, r, e in ks]


def sfx(name, vol=70): return {'in': name, 'out': '', 'per': 'block', 'pitch': 'flat', 'volume': vol}


def photo(src, t0, t1, x=CX, y=CY, w=SW, tk=None, in_=None, out=None, name=None, slot=None, opacity=1, blend=0, depth=0, sound=None):
    it = copy.deepcopy(base_photo)
    it.update(id=new_id('ph'), name=name or src, start=round(t0, 3), end=round(t1, 3), x=round(x, 1), y=round(y, 1), w=round(w, 1), depth=depth,
              cam=True, tk=tk or [], opacity=opacity, blend=blend, rot=0)
    it['in'], it['out'] = in_, out
    it['photo'].update(src='up:' + src, aspect='9:16', raw=True, alpha=src.startswith(('vfx_', 'el_')))
    if slot: it['slot'] = {'on': True, 'label': slot}
    if sound: it['sfx'] = sfx(*sound)
    items.append(it); order.append(it['id']); return it


def vfx(k, t0, t1, x, y, w, **kw):
    kw.setdefault('blend', SCREEN); return photo(V[k], t0, t1, x, y, w, name='VFX ' + k, **kw)


_first = {}
def holder(n, t0, t1, tk=None, in_=None, sound=None, opacity=1):
    """the footage for slot n: a photo layer or a clip layer (same transform keys, fades and sounds either way)"""
    m = MEDIA_FOR[n]
    if m[0] == 'photo':
        return photo(PHOTO[m[1]], t0, t1, tk=tk, in_=in_, name=f'Shot {n:02d} {m[1]}', opacity=opacity, sound=sound, slot=f'Shot {n:02d}: {SLOT[n]}')
    _first.setdefault(n, t0)
    it = photo(PHOTO['diya_dark'], t0, t1, tk=tk, in_=in_, name=f'Shot {n:02d} {m[1]}', opacity=opacity, sound=sound)
    it.pop('photo'); it['type'] = 'video'; it['id'] = 'vd' + it['id'][2:]; order[-1] = it['id']
    it['video'] = {'src': 'vid:dw_' + m[1], 'trimIn': round(m[2] + (t0 - _first[n]), 3), 'speed': 1, 'volume': 0}
    return it


def overlay(clip, t0, t1, w=SW, y=CY, opacity=0.85, trim=0.0, in_=None, out=None):
    """a particle video layered over the footage with Screen blend (its black background disappears), centred"""
    it = photo(PHOTO['diya_dark'], t0, t1, CX, y, w, in_=in_, out=out, name=f'Particles {clip}', opacity=opacity, blend=SCREEN)
    it.pop('photo'); it['type'] = 'video'; it['id'] = 'vd' + it['id'][2:]; order[-1] = it['id']
    it['video'] = {'src': 'vid:dw_' + clip, 'trimIn': trim, 'speed': 1, 'volume': 0}
    return it


def rect(t0, t1, color, opacity=1, in_=None, out=None, name='Panel', blend=0):
    it = copy.deepcopy(base_decor)
    it.update(id=new_id('dc'), name=name, start=round(t0, 3), end=round(t1, 3), x=CX, y=CY, w=SW + 40, h=SH + 40, color=color, alpha=1,
              cam=False, tk=[], opacity=opacity, blend=blend)
    it['in'], it['out'] = in_, out
    items.append(it); order.append(it['id']); return it


def fx(effect, t0, t1, kf=None, params=None, name=None):
    it = copy.deepcopy(base_fx.get(effect) or dict(base_fx['grain'], effect=effect, params={}, keys=[])); it.update(id=new_id('fx'), start=round(t0, 3), end=round(t1, 3), name=name or it['name'])
    if kf is not None: it['keys'] = kf
    if params: it['params'] = dict(it['params'], **params)
    items.append(it); order.append(it['id']); return it


def text(txt, t0, t1, y, width, tracking, color=GOLD, split='whole', in_=None, out=None, glow=None, extrude=None, opacity=1, sound=None,
         loop=None, x=CX, slot=None):
    t = copy.deepcopy(base_text)
    size = width / WID[f'{txt}|{tracking}']
    t.update(text=txt, start=round(t0, 3), end=round(t1, 3), x=x, y=y, size=round(size, 3), color=color, split=split, tracking=tracking,
             line_height=0.92, align='center', seed=11, speed=1, quality='smart', **{'in': in_ or 'none', 'out': out or 'none'})
    t.pop('loop', None)
    if loop: t['loop'] = loop
    st = t['studio']; st.update(id=new_id('tx'), depth=0, cam=True, rot=0, tk=[], rx=0, ry=0, opacity=opacity)
    st['fx'] = {'shadow': {'on': True, 'color': '#00000080'}, 'glow': {'on': bool(glow), 'color': glow or '#FFB347'},
                'outline': {'on': False, 'color': '#000000'}, 'background': {'on': False, 'color': '#0000007F'}}
    if extrude: st['extrude'] = extrude
    st['slot'] = {'on': True, 'label': slot or f'Text: {txt}'}
    st.pop('loop', None)
    if sound: t['sfx'] = {'in': sound[0], 'per': 'block', 'pitch': [0], 'volume': sound[1]}
    texts.append(t); order.append(st['id']); return t


def flash(t, dur=0.067, color='#FFD9A0', opacity=0.5):
    rect(t, t + dur, color, opacity, name='Flash frame', blend=ADD)


def blur_hit(t, strength=16, dur=0.18):
    fx('poisonBlur', t - dur / 2, t + dur / 2, [{'t': 0, 'ease': 'in', 'p': {'strength': 0}}, {'t': dur / 2, 'ease': 'out', 'p': {'strength': strength}},
                                                {'t': dur, 'ease': 'linear', 'p': {'strength': 0}}], name='Motion blur')


def zoom_hit(t, strength=8):
    fx('chromaticZoom', t - 0.02, t + 0.3, [{'t': 0, 'ease': 'out', 'p': {'strength': strength}}, {'t': 0.32, 'ease': 'linear', 'p': {'strength': 0}}], name='Impact zoom')


SHAKES = []
def shake(t, amp=12, rot=1.0, dur=0.4): SHAKES.append(dict(start=round(t, 3), end=round(t + dur, 3), amp=amp, rot=rot, push=0, freq=9, seed=len(SHAKES) + 1, easeIn=0.01, easeOut=dur * 0.8))


def push(t0, t1, s0=1.0, s1=1.08, ease='linear', x0=CX, x1=CX):
    return keys((t0, x0, CY, s0, 0, ease), (t1, x1, CY, s1, 0, 'linear'))


def whip_in(t0, t1, frm=260, s1=1.06):
    """shot enters with a fast sideways whip, then drifts (pairs with a blur hit on the cut)"""
    return keys((t0, CX + frm, CY, 1.04, 0, 'out'), (t0 + 0.12, CX, CY, 1.04, 0, 'linear'), (t1, CX, CY, s1, 0, 'linear'))


def ramp(t0, t1, s0=1.0, s1=1.16):
    """speed ramp feel: slow then fast push into the cut"""
    return keys((t0, CX, CY, s0, 0, 'in'), (t1, CX, CY, s1, 0, 'linear'))


def particles_bed(t0, t1, op=(0.55, 0.7, 0.45), rise=260):
    """three depth layers of drifting gold particles (parallax with the camera)"""
    for k, depth, w, o in [('particles_far', 700, SW * 1.75, op[0]), ('particles_mid', 260, SW * 1.3, op[1]), ('particles_near', 0, SW, op[2])]:
        h = w * 2600 / 1080
        vfx(k, t0, t1, CX, CY, w, depth=depth, opacity=o, tk=keys((t0, CX, CY + rise * 0.5, 1, 0, 'linear'), (t1, CX, CY - rise * 0.5, 1, 0, 'linear')))


# ================================================================ the edit
rect(0, DUR, '#000000', name='Black base')

# ---- 0.00 - 2.97  ignition
IGN = beat(0) + 0.36                                   # 0.87: the kick where the flame catches
holder(1, IGN, beat(3), in_=ph('fade', 1.3), tk=push(IGN, beat(3), 1.0, 1.06), opacity=0.9)
particles_bed(0, beat(3), (0.6, 0.75, 0.5), 200)
overlay('bokeh_loop', 0, beat(3), 1000, opacity=0.9, in_=ph('fade', 0.8))
vfx('bloom', IGN, beat(3), 339, 954, 760, in_=ph('fade', 0.6), opacity=0.7)
vfx('bloom', IGN, IGN + 0.5, 339, 954, 300, in_=ph('grow', 0.3), out=ph('fade', 0.25), blend=ADD, sound=('Smokey_06', 60))   # the ignition flare
T0 = beat(1) + 0.2                                     # 1.53
text('THIS DIWALI', T0, beat(3), 470, SW * 0.6, 0.35, GOLD, in_=ph('strip_open', 0.7), glow='#FFB34766', sound=('Woosh_MidH_3', 55))
vfx('streak', T0, T0 + 0.7, CX, 470, 1300, tk=keys((T0, CX - 120, 470, 0.6, 0, 'out'), (T0 + 0.7, CX + 140, 470, 1.0, 0, 'linear')), in_=ph('fade', 0.12),
    out=ph('fade', 0.3))
vfx('gold_rule', T0 + 0.35, beat(3), CX, 530, 360, in_=ph('strip_open', 0.5), opacity=0.8)

# ---- 2.97 - 6.26  rapid montage (speed ramps, whips, a match cut, flash frames, particle transitions)
c = [beat(3), half(3), beat(4), half(4), beat(5), beat(5) + 0.58, beat(7)]     # 2.97 3.38 3.79 4.20 4.61 5.19 6.26
holder(2, c[0], c[1], tk=ramp(c[0], c[1], 1.0, 1.14), sound=('Woosh_High_2', 60))
flash(c[0]); zoom_hit(c[0], 9); shake(c[0], 16, 1.4)
vfx('dust_burst', c[0], c[0] + 0.45, CX, CY, 900, tk=push(c[0], c[0] + 0.45, 0.6, 1.6), out=ph('fade', 0.3))
holder(3, c[1], c[2], tk=whip_in(c[1], c[2], 300), sound=('Woosh_High_2', 50)); blur_hit(c[1], 18)
holder(4, c[2], c[3], tk=push(c[2], c[3], 1.14, 1.0, 'out'))                              # match cut: picks up the zoom where 3 left it
holder(5, c[3], c[4], tk=whip_in(c[3], c[4], -300), sound=('Woosh_High_2', 50)); blur_hit(c[3], 18)
holder(6, c[4], c[5], tk=ramp(c[4], c[5], 1.0, 1.12))
flash(c[4]); zoom_hit(c[4], 7); shake(c[4], 10, 0.8)
holder(7, c[5], c[6], tk=push(c[5], c[6], 1.0, 1.05, 'linear'))                          # the slow emotional one
vfx('streak', c[5] - 0.1, c[5] + 0.35, CX, 900, 1400, tk=keys((c[5] - 0.1, -400, 900, 1, 0, 'out'), (c[5] + 0.35, 1100, 900, 1, 0, 'linear')),
    sound=('Woosh_MidH_3', 50))
particles_bed(c[0], c[6], (0.35, 0.45, 0.3), 320)

# ---- 6.26 - 9.54  people + LIGHT / LOVE / CELEBRATE
w0, w1, w2, w3 = beat(7), beat(8), beat(9), beat(11)     # 6.26 7.08 7.90 9.54
holder(8, w0, w1, tk=push(w0, w1, 1.02, 1.1))
holder(9, w1, w2, tk=whip_in(w1, w2, 280)); blur_hit(w1, 14)
holder(10, w2, w3 - 0.4, tk=push(w2, w3 - 0.4, 1.0, 1.1))
holder(10, w3 - 0.4, w3, tk=ramp(w3 - 0.4, w3, 1.1, 1.35))                                # ramps into the sweep
rect(w0, w3, '#000000', 0.32, name='Scrim')
for word, t0, t1, wdt in [('LIGHT', w0, w1, SW * 0.74), ('LOVE', w1, w2, SW * 0.66), ('CELEBRATE', w2, w3 - 0.4, SW * 0.88)]:
    text(word, t0 + 0.02, t1, CY, wdt, 0.06, CREAM, in_=ph('punch_in', 0.34, 1.0), glow='#FFB34755', sound=('Pop_1', 45),
         loop={'preset': 'push_in', 'amp': 0.05})
    blur_hit(t0 + 0.06, 12, 0.16); shake(t0, 14, 1.2, 0.35)
zoom_hit(w2, 10)
particles_bed(w0, w3, (0.3, 0.4, 0.35), 260)
overlay('dust_b', w0, w3, SW, opacity=0.8)

# ---- 9.54 - 12.83  DIWALI: golden sweep, particle-assembled title, firework trails, mandala, bursts
d0, d1 = beat(11), beat(15)                              # 9.54 - 12.83
holder(11, d0, d1, tk=push(d0, d1, 1.0, 1.06), opacity=0.55)
photo(EL['mandala_redgold'], d0 + 0.3, d1, CX, CY, 640, opacity=0.5, in_=ph('fade', 0.6), tk=keys((d0 + 0.3, CX, CY, 0.92, 0, 'linear'), (d1, CX, CY, 1.0, 40, 'linear')), name='Element mandala')
overlay('particle_ring', d0, d1, 1000, opacity=0.95)
vfx('dust_burst', d0 + 0.05, d0 + 1.2, CX, CY, 1100, tk=push(d0 + 0.05, d0 + 1.2, 1.25, 0.8, 'out'), out=ph('fade', 0.5), opacity=0.9)
text('DIWALI', d0 + 0.12, d1, CY, SW * 0.84, 0.08, GOLD, split='letter', in_=ph('scatter', 1.0, 1, 0.025, 'center'), glow='#FFB34799',
     extrude={'on': True, 'depth': 0.1, 'angle': 90, 'steps': 6, 'color': '#5A2A08', 'shade': 0.6, 'swing': 0, 'swingFreq': 0.5, 'fade': 0},
     sound=('Smokey_09', 70), loop={'preset': 'push_in', 'amp': 0.04})
text('FESTIVAL OF LIGHTS', d0 + 1.2, d1, CY + 190, SW * 0.56, 0.45, CREAM, in_=ph('fade_up', 0.6), glow=None)
vfx('gold_rule', d0 + 1.1, d1, CX, CY + 140, 420, in_=ph('strip_open', 0.5), opacity=0.85)
photo(EL['rangoli_diyas'], d0 + 1.0, d1, CX, 1075, 340, tk=keys((d0 + 1.0, CX, 1075, 1.0, 0, 'linear'), (d1, CX, 1075, 1.04, 30, 'linear')), in_=ph('grow', 0.5), name='Element rangoli')
vfx('sweep', d0 - 0.05, d0 + 0.45, CX, CY, 1100, tk=keys((d0 - 0.05, -700, CY, 1, 0, 'out'), (d0 + 0.45, 1500, CY, 1, 0, 'linear')), blend=ADD,
    sound=('Woosh_MidH_3', 70))
flash(d0, 0.08); shake(d0, 18, 1.5, 0.5); zoom_hit(d0, 12)
photo(EL['arc'], d0 + 0.5, d0 + 1.9, CX, CY - 10, 880, tk=keys((d0 + 0.5, CX, CY - 10, 0.9, -40, 'linear'), (d0 + 1.9, CX, CY - 10, 1.05, 140, 'linear')),
      in_=ph('fade', 0.15), out=ph('fade', 0.4), blend=SCREEN, name='Element arc', sound=('Woosh_High_2', 45))
photo(EL['arc'], d0 + 1.6, d1, CX, CY + 30, 840, tk=keys((d0 + 1.6, CX, CY + 30, 1.0, 180, 'linear'), (d1, CX, CY + 30, 1.08, 330, 'linear')),
      in_=ph('fade', 0.15), out=ph('fade', 0.4), blend=SCREEN, name='Element arc')
photo(EL['swirl_s'], d0 - 0.05, d0 + 0.65, CX, CY, 760, tk=push(d0 - 0.05, d0 + 0.65, 0.75, 1.3), in_=ph('fade', 0.1), out=ph('fade', 0.3), blend=SCREEN, name='Element swirl')
for t, k, x, y, w in [(beat(12), 'fireworks_gold', 180, 330, 420), (beat(13), 'fireworks_multi', 540, 350, 400), (beat(14), 'fireworks_gold', CX, 230, 460)]:
    photo(EL[k], t, t + 1.0, x, y, w, depth=200, in_=ph('grow', 0.3), out=ph('fade', 0.6), tk=push(t, t + 1.0, 1.0, 1.12), blend=SCREEN, name='Element ' + k)
particles_bed(d0, d1, (0.45, 0.55, 0.4), 220)

# ---- 12.83 - 16.11  fastest section: half-beat cuts, word flashes, mandala + streaks over the footage
f = [round(beat(15) + i * BEAT / 2, 3) for i in range(9)]    # 12.83 .. 16.11
for i, n in enumerate(range(12, 20)):
    t0, t1 = f[i], f[i + 1]
    tk = whip_in(t0, t1, 260 if i % 2 else -260) if i in (1, 5) else ramp(t0, t1, 1.0, 1.1) if i % 2 == 0 else push(t0, t1, 1.08, 1.0, 'out')
    holder(n, t0, t1, tk=tk, sound=('Woosh_High_2', 40) if i in (1, 5) else None)
    if i in (1, 5): blur_hit(t0, 16)
flash(f[0]); shake(f[0], 16, 1.3); zoom_hit(f[0], 9)
flash(f[4]); shake(f[4], 14, 1.1); zoom_hit(f[4], 8)
vfx('mandala_gold', f[0], f[8], CX, CY, 1100, opacity=0.22, tk=keys((f[0], CX, CY, 1.0, 0, 'linear'), (f[8], CX, CY, 1.12, -60, 'linear')))
for t, y in [(f[2] - 0.05, 300), (f[6] - 0.05, 980)]:
    vfx('streak', t, t + 0.4, CX, y, 1400, tk=keys((t, -400, y, 1, 0, 'out'), (t + 0.4, 1100, y, 1, 0, 'linear')), sound=('Woosh_MidH_3', 40))
particles_bed(f[0], f[8], (0.3, 0.45, 0.4), 420)
overlay('dust_a', f[0], f[8], SW, opacity=0.85)
for word, i in [('LIGHT', 1), ('JOY', 3), ('TOGETHERNESS', 5)]:
    text(word, f[i] + 0.05, f[i + 1], 1080, (SW * 0.3 if word != 'TOGETHERNESS' else SW * 0.62) if word != 'JOY' else SW * 0.17, 0.3, CREAM,
         in_=ph('fade', 0.06), glow='#FFB34755')
text('LIGHT • JOY • TOGETHERNESS', f[7], f[8], 1080, SW * 0.8, 0.25, GOLD, in_=ph('strip_open', 0.25), glow='#FFB34766')

# ---- 16.11 - 20.00  hero, HAPPY DIWALI, final firework, fade to black, one diya left
h0, fin = beat(19), beat(22)                              # 16.11, 18.58
holder(20, h0, 19.95, tk=push(h0, 19.95, 1.0, 1.12, 'linear'))
rect(h0, DUR, '#000000', 0.38, name='Hero scrim')   # keeps HAPPY DIWALI readable over the bright diya field
flash(h0, 0.06, opacity=0.6)
photo(EL['lanterns'], h0, DUR, CX, 200, 330, tk=keys((h0, CX, 200, 1, -2, 'gentle'), (h0 + 1.9, CX, 200, 1, 2, 'gentle'), (DUR, CX, 200, 1, -2, 'linear')), in_=ph('fade', 0.5), name='Element lanterns')
overlay('bokeh_loop', h0, DUR, 1000, y=CY, opacity=0.7, trim=0.5)
particles_bed(h0, DUR, (0.5, 0.6, 0.45), 260)
photo(EL['fireworks_multi'], fin, fin + 1.4, CX, 560, 720, depth=150, in_=ph('grow', 0.35), out=ph('fade', 0.8), tk=push(fin, fin + 1.4, 1.0, 1.15), blend=SCREEN, name='Element fireworks finale')
photo(EL['fireworks_gold'], fin + 0.12, fin + 1.4, 190, 380, 420, depth=250, in_=ph('grow', 0.3), out=ph('fade', 0.8), blend=SCREEN, name='Element fireworks')
photo(EL['fireworks_gold'], fin + 0.2, fin + 1.4, 540, 360, 380, depth=250, in_=ph('grow', 0.3), out=ph('fade', 0.8), blend=SCREEN, name='Element fireworks')
vfx('bloom', fin, fin + 0.9, CX, 560, 1000, in_=ph('fade', 0.08), out=ph('fade', 0.7), opacity=0.6)
photo(EL['swirl_wave'], h0 + 0.35, h0 + 2.6, CX, 720, 720, tk=keys((h0 + 0.35, CX, 720, 0.9, -10, 'linear'), (h0 + 2.6, CX, 720, 1.1, 10, 'linear')), in_=ph('fade', 0.3), out=ph('fade', 0.6), blend=SCREEN, name='Element swirl')
photo(EL['title_happy_diwali'], h0 + 0.5, DUR, CX, 720, 560, in_=ph('push_reveal', 0.9), tk=push(h0 + 0.5, DUR, 1.0, 1.04), name='Element HAPPY DIWALI title', sound=('Smokey_06', 50))


vfx('streak', h0 + 1.4, h0 + 2.1, CX, 640, 1300, tk=keys((h0 + 1.4, -300, 640, 0.8, 0, 'out'), (h0 + 2.1, 1000, 640, 1.0, 0, 'linear')), sound=('Woosh_MidH_3', 45))
shake(fin, 12, 1.0, 0.5); zoom_hit(fin, 7)

# ---- grade (applies to everything under it), then the fade to black and the last diya on top
fx('colorBalance', 0, DUR, params={'redShift': 6, 'greenShift': 1, 'blueShift': -9}, name='Warm grade')
fx('grain', 0, DUR, params={'intensity': 8, 'size': 1.2})
fx('vignetting', 0, DUR, params={'strength': 42, 'softness': 60})
rect(19.0, DUR, '#000000', 1, in_=ph('fade', 0.8), name='Fade to black')
vfx('bloom', 18.9, DUR, 351, 966, 280, opacity=0.65, in_=ph('fade', 0.4))
photo(EL['diya_swirl'], 18.9, DUR, CX, 1040, 300, in_=ph('fade', 0.4), name='Element diya (stays lit)')

# ---------------------------------------------------------------- camera: pushes in the intro, the title and the hero; shakes on impacts
CAM = [dict(t=0, z=0, ease='gentle'), dict(t=beat(3) - 0.01, z=150, ease='hold'), dict(t=beat(3), z=0, ease='hold'),
       dict(t=d0 - 0.01, z=0, ease='hold'), dict(t=d0, z=0, ease='gentle'), dict(t=d1 - 0.01, z=90, ease='hold'), dict(t=d1, z=0, ease='hold'),
       dict(t=h0 - 0.01, z=0, ease='hold'), dict(t=h0, z=0, ease='gentle'), dict(t=DUR, z=230, ease='linear')]
cam_keys = [dict(t=k['t'], x=CX, y=CY, z=k['z'], pan=0, tilt=0, roll=0, lens=1, ease=k['ease']) for k in CAM]

# ---------------------------------------------------------------- write
r = copy.deepcopy(tpl)
r['title'] = 'Diwali Montage 9x16 (real footage)'
r['background'] = '#000000'
r['bpm'], r['beat_offset'], r['duration'] = BPM, OFF, DUR
r['texts'] = texts
r['studio_project'] = dict(tpl['studio_project'], mediaBin=bin_, manualOrder=True, persp={'on': False, 'order': 'z'})
r['studio_scene'] = {'camera': {'on': True, 'near': 320, 'fog': {'on': False, 'start': 4000, 'end': 5000}, 'keys': cam_keys, 'shake': SHAKES},
                     'mirror': 'scale', 'items': items, 'order': order,
                     'note': 'Kinekit Studio recipe: premium Diwali montage, 20 s, 9:16, cut from your footage. The clips travel inside this file '
                             '(studio_videos) and load into the Studio automatically.'}
r['studio_media'] = media
r['studio_videos'] = videos
json.dump(r, open(OUT, 'w'))
print('texts', len(texts), 'items', len(items), 'shakes', len(SHAKES), 'MB', round(os.path.getsize(OUT) / 1e6, 2))
