"""India beat-sync (9:16) for Kinekit Studio, in the style of a fast "dynamic promo" opener: one huge word per beat on
rich gradients, hard cuts to full-frame pictures with a slow push, echo word stacks, collage and split-panel moments,
and Indian stickers (marigold toran, diya, Ashoka chakra, gulal bursts, kites, rangoli, paisley, Horn OK Please).

    python3 build_india.py ASSETS_DIR TEMPLATE_RECIPE WIDTHS_JSON OUT_RECIPE

Every cut sits on the song's grid (72.8 BPM, beat 0.8215 s, first beat 0.506 s). Each bar has three shots: the
downbeat, the syncopated hit 0.58 s later, and the half beat after the second beat (+1.23 s). Picture slots carry a
Studio slot label with the Pexels / Pixabay search to drop a real photo in.
"""
import base64, copy, io, json, math, os, sys, tempfile
from PIL import Image

ASSETS, TEMPLATE, WIDTHS, OUT = sys.argv[1:5]
tpl = json.load(open(TEMPLATE))
WID = json.load(open(WIDTHS))
SW, SH = 720, 1280
CX, CY = SW / 2, SH / 2
DUR = 18.6
BPM, OFF = 73.04, 0.506
BEAT = 60 / BPM
LINE = 24 * 0.92


def beat(n): return round(OFF + n * BEAT, 3)


BARS = [beat(n) for n in range(3, 19, 2)]          # 2.97 ... 14.47: the eight drop bars
FINALE = beat(19)                                   # 16.11

# ---------------------------------------------------------------- media
media, media_meta = {}, {}


def add_media(mid, path, max_w=None, fmt=None):
    if mid in media: return mid
    im = Image.open(path)
    if max_w and im.width > max_w: im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    fmt = fmt or ('PNG' if im.mode == 'RGBA' else 'JPEG')
    b = io.BytesIO()
    if fmt == 'PNG': im.save(b, 'PNG', optimize=True)
    else: im.convert('RGB').save(b, 'JPEG', quality=86, optimize=True)
    media[mid] = f"data:image/{'png' if fmt == 'PNG' else 'jpeg'};base64," + base64.b64encode(b.getvalue()).decode()
    media_meta[mid] = (im.width, im.height)
    return mid


def strip(scene, n, i):
    """vertical strip i of n cut from a scene card (for the split-panel shot)"""
    mid = f'strip_{scene}_{i}'
    im = Image.open(f'{ASSETS}/scenes/{scene}.jpg'); w = im.width // n
    p = os.path.join(tempfile.gettempdir(), mid + '.jpg'); im.crop((i * w, 0, (i + 1) * w, im.height)).save(p, quality=90)
    return add_media(mid, p, 400)


BG = {k: add_media('bg_' + k, f'{ASSETS}/backgrounds/{k}.jpg', 720) for k in ['saffron', 'rani', 'peacock', 'turmeric', 'indigo', 'cream', 'night', 'maroon', 'green']}
SC = {k: add_media('sc_' + k, f'{ASSETS}/scenes/{k}.jpg', 720) for k in ['taj', 'holi', 'varanasi', 'fort', 'kites', 'diwali', 'chai', 'cricket', 'monsoon']}
STK = {}
for k, mw in [('mandala_gold', 800), ('mandala_line', 800), ('mandala_rani', 800), ('marigold', 300), ('marigold_yellow', 300), ('toran', 1080),
              ('diya', 400), ('chakra', 600), ('chakra_white', 600), ('stroke_saffron', 1100), ('stroke_white', 1100), ('stroke_green', 1100),
              ('stroke_rani', 1100), ('gulal_rani', 700), ('gulal_yellow', 700), ('gulal_teal', 700), ('gulal_violet', 700), ('rangoli', 700),
              ('paisley', 450), ('kite_rani', 400), ('kite_saffron', 400), ('horn_ok_please', 900), ('lotus', 450), ('sparkle', 160),
              ('sparkle_gold', 160), ('hud', 720)]:
    STK[k] = add_media('stk_' + k, f'{ASSETS}/stickers/{k}.png', mw, 'PNG')

PEXELS = {   # what to search for when swapping a stand-in for a real stock shot
    'holi': 'holi festival colours india', 'taj': 'taj mahal sunrise', 'kites': 'kite festival india sky', 'fort': 'jaipur amber fort',
    'chai': 'masala chai kulhad', 'varanasi': 'varanasi ghat aarti', 'cricket': 'cricket stadium india night', 'monsoon': 'mumbai monsoon rain',
    'diwali': 'diwali diya lamps'}

# ---------------------------------------------------------------- layer builders
items, texts, order = [], [], []
base_photo = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'ph124')
base_decor = next(i for i in tpl['studio_scene']['items'] if i['id'] == 'dc144')
base_fx = {i['effect']: i for i in tpl['studio_scene']['items'] if i['type'] == 'fx'}
base_text = tpl['texts'][0]
nid = [0]


def new_id(p): nid[0] += 1; return f'{p}{nid[0]}'


def ph(kind, dur=0.3, amount=1):
    return {'preset': kind, 'dur': dur, 'stagger': 0, 'order': 'forward', 'amount': amount} if kind else None


def tk_keys(t0, t1, a, b, ease='linear'):
    """two transform keys: a and b are dicts with x, y, s, rot (absolute)"""
    k0 = dict(t=round(t0, 3), ease=ease, x=a['x'], y=a['y'], depth=0, rot=a.get('rot', 0), s=a.get('s', 1), rx=0, ry=0)
    k1 = dict(t=round(t1, 3), ease='linear', x=b['x'], y=b['y'], depth=0, rot=b.get('rot', 0), s=b.get('s', 1), rx=0, ry=0)
    return [k0, k1]


def photo(src, t0, t1, x=CX, y=CY, w=SW, raw=True, alpha=False, aspect='9:16', tk=None, in_=None, out=None, name=None, slot=None, opacity=1):
    it = copy.deepcopy(base_photo)
    it.update(id=new_id('ph'), name=name or src, start=round(t0, 3), end=round(t1, 3), x=round(x, 1), y=round(y, 1), w=round(w, 1), depth=0, cam=False,
              tk=tk or [], opacity=opacity, rot=0)
    it['in'], it['out'] = in_, out
    it['photo'].update(src='up:' + src, aspect=aspect, raw=raw, alpha=alpha)
    if slot: it['slot'] = {'on': True, 'label': slot}
    items.append(it); order.append(it['id']); return it


def sticker(name, t0, t1, x, y, w, tk=None, in_=None, out=None, opacity=1):
    return photo(STK[name], t0, t1, x, y, w, raw=True, alpha=True, tk=tk, in_=in_, out=out, name='Sticker ' + name, opacity=opacity)


def push(t0, t1, x=CX, y=CY, s0=1.0, s1=1.1, r0=0, r1=0):
    return tk_keys(t0, t1, dict(x=x, y=y, s=s0, rot=r0), dict(x=x, y=y, s=s1, rot=r1))


def spin(t0, t1, x, y, deg, s0=1, s1=1):
    return tk_keys(t0, t1, dict(x=x, y=y, s=s0, rot=0), dict(x=x, y=y, s=s1, rot=deg))


def slide(t0, t1, x0, y0, x1, y1, s=1, ease='out'):
    return tk_keys(t0, t1, dict(x=x0, y=y0, s=s), dict(x=x1, y=y1, s=s), ease)


def word_size(txt, width=SW * 0.86, max_size=13.0):
    return min(max_size, width / WID[txt][0])


def word(txt, t0, t1, x=CX, y=CY, size=None, color='#FFFFFF', in_=None, loop=True, opacity=1, shadow=True, width=None, slot=None, max_size=13.0):
    t = copy.deepcopy(base_text)
    size = size or word_size(txt, width or SW * 0.86, max_size)
    t.update(text=txt, start=round(t0, 3), end=round(t1, 3), x=round(x, 1), y=round(y, 1), size=round(size, 3), color=color, split='whole',
             tracking=0.01, line_height=0.92, align='center', seed=7, speed=1, quality='smart', **{'in': in_ or 'none', 'out': 'none'})
    t.pop('loop', None)
    if loop: t['loop'] = {'preset': 'push_in', 'amp': 0.07}
    st = t['studio']; st.update(id=new_id('tx'), depth=0, cam=False, rot=0, tk=[], rx=0, ry=0, opacity=opacity)
    st['fx'] = {'shadow': {'on': shadow, 'color': '#00000066'}, 'glow': {'on': False, 'color': '#FDFF57'}, 'outline': {'on': False, 'color': '#000000'}, 'background': {'on': False, 'color': '#0000007F'}}
    st['slot'] = {'on': True, 'label': slot or f'Word {txt}'}
    st.pop('loop', None)
    texts.append(t); order.append(st['id']); return t


def rect(t0, t1, x, y, w, h, color, tk=None, in_=None, out=None, name='Panel'):
    it = copy.deepcopy(base_decor)
    it.update(id=new_id('dc'), name=name, start=round(t0, 3), end=round(t1, 3), x=round(x, 1), y=round(y, 1), w=round(w, 1), h=round(h, 1), color=color, alpha=1, cam=False, tk=tk or [])
    it['in'], it['out'] = in_, out
    items.append(it); order.append(it['id']); return it


def fx(effect, t0, t1, keys=None, params=None, name=None):
    it = copy.deepcopy(base_fx[effect])
    it.update(id=new_id('fx'), start=round(t0, 3), end=round(t1, 3), name=name or it['name'])
    if keys is not None: it['keys'] = keys
    if params: it['params'] = dict(it['params'], **params)
    items.append(it); order.append(it['id']); return it


def hit(t, strength=9):
    """chromatic zoom kick on a downbeat"""
    fx('chromaticZoom', t - 0.02, t + 0.28, [{'t': 0, 'ease': 'out', 'p': {'strength': strength}}, {'t': 0.28, 'ease': 'linear', 'p': {'strength': 0}}], name='Beat hit')


def whip(t):
    """soft blur bridging two shots"""
    fx('poisonBlur', t - 0.1, t + 0.1, [{'t': 0, 'ease': 'in', 'p': {'strength': 0}}, {'t': 0.1, 'ease': 'out', 'p': {'strength': 18}}, {'t': 0.2, 'ease': 'linear', 'p': {'strength': 0}}], name='Cut blur')


# ---------------------------------------------------------------- shot recipes
def shot_picture(scene, t0, t1, label=None, label_y=None, extras=()):
    photo(SC[scene], t0, t1, tk=push(t0, t1, s0=1.0, s1=1.09), name=f'Picture {scene}', slot=f'Photo: {scene} (pexels: {PEXELS[scene]})')
    for e in extras: e()
    if label: word(label, t0 + 0.08, t1, y=label_y or SH * 0.78, width=SW * 0.7, max_size=10, in_={'preset': 'slice_in', 'dur': 0.22, 'stagger': 0, 'order': 'forward', 'amount': 1})


def shot_word(txt, bgk, t0, t1, color='#FFFFFF', extras=(), y=CY):
    photo(BG[bgk], t0, t1, name=f'Background {bgk}')
    for e in extras: e()
    word(txt, t0, t1, y=y, color=color)


def shot_echo(txt, bgk, t0, t1, color='#FFFFFF', ghost='#FFFFFF', extras=()):
    photo(BG[bgk], t0, t1, name=f'Background {bgk}')
    for e in extras: e()
    size = word_size(txt); h = LINE * size * 0.74
    for k, dy in enumerate((-2, -1, 1, 2)):
        word(txt, t0 + 0.05 * abs(dy), t1, y=CY + dy * (h + 14), size=size, color=ghost, opacity=0.16 if abs(dy) == 2 else 0.3, shadow=False, loop=True, slot=f'Echo {txt}')
    word(txt, t0, t1, size=size, color=color)


def shot_collage(scenes, t0, t1, bgk='cream'):
    photo(BG[bgk], t0, t1, name=f'Background {bgk}')
    pos = [(SW * 0.25, SH * 0.25), (SW * 0.75, SH * 0.25), (SW * 0.25, SH * 0.75), (SW * 0.75, SH * 0.75)]
    for i, (sc, (x, y)) in enumerate(zip(scenes, pos)):
        ts = t0 + i * 0.06
        sx = -SW * 0.6 if x < CX else SW * 1.6
        photo(SC[sc], ts, t1, x=x, y=y, w=SW / 2 - 12, aspect='9:16', raw=False, tk=slide(ts, ts + 0.22, sx, y, x, y), name=f'Tile {sc}', slot=f'Photo: {sc} (pexels: {PEXELS[sc]})')


def shot_split(scenes, t0, t1):
    n = len(scenes)
    for i, sc in enumerate(scenes):
        x = SW * (i + 0.5) / n; ts = t0 + i * 0.05; y0 = -SH * 0.6 if i % 2 == 0 else SH * 1.6
        photo(strip(sc, n, i), ts, t1, x=x, y=CY, w=SW / n + 1, tk=slide(ts, ts + 0.24, x, y0, x, CY), name=f'Strip {sc}', slot=f'Photo: {sc} strip (pexels: {PEXELS[sc]})')


# ---------------------------------------------------------------- the edit
B = BARS
# intro: 0 - 2.97 (soft): mandala opens like an iris, NAMASTE, INDIA under a marigold toran, tricolour wipe
photo(BG['night'], 0, beat(1), name='Background night')
sticker('mandala_line', 0, beat(1), CX, CY, 640, tk=spin(0, beat(1), CX, CY, 70, 0.15, 1.15), in_=ph('fade', 0.35))
word('NAMASTE', beat(0), beat(1), y=CY, width=SW * 0.62, color='#FFD97A', in_={'preset': 'fade_up', 'dur': 0.4, 'stagger': 0, 'order': 'forward', 'amount': 1})
sticker('sparkle_gold', beat(0) + 0.2, beat(1), CX + 230, CY - 120, 70, tk=spin(beat(0) + 0.2, beat(1), CX + 230, CY - 120, 90, 0.6, 1.2))

photo(BG['saffron'], beat(1), beat(2), name='Background saffron')
sticker('mandala_gold', beat(1), beat(2), CX, CY, 900, tk=spin(beat(1), beat(2), CX, CY, -25, 1.0, 1.08), opacity=0.35)
word('INDIA', beat(1), beat(2))
sticker('toran', beat(1), beat(2), CX, 165, SW, tk=slide(beat(1), beat(1) + 0.35, CX, -260, CX, 165))
hit(beat(1), 6)

photo(BG['cream'], beat(2), B[0], name='Background cream')
for i, (k, y) in enumerate([('stroke_saffron', CY - 260), ('stroke_white', CY), ('stroke_green', CY + 260)]):
    ts = beat(2) + i * 0.1
    sticker(k, ts, B[0], CX, y, 900, tk=slide(ts, ts + 0.3, -SW * 0.8 if i % 2 == 0 else SW * 1.8, y, CX, y))
word('BHARAT', beat(2) + 0.35, B[0], y=CY, width=SW * 0.5, color='#0A1A5C', shadow=False, in_={'preset': 'fade', 'dur': 0.2, 'stagger': 0, 'order': 'forward', 'amount': 1})
sticker('chakra', beat(2) + 0.2, B[0], CX, CY, 230, tk=spin(beat(2) + 0.2, B[0], CX, CY, 180), opacity=0.25)
whip(B[0])


def bar(i):
    d = B[i]; return d, round(d + 0.58, 3), round(d + 1.232, 3), (B[i + 1] if i + 1 < len(B) else FINALE)


# bar 1  HOLI -> RANGEELA -> DESI (echo)
d, s, h, e = bar(0)
shot_picture('holi', d, s, 'HOLI', extras=[lambda: sticker('gulal_rani', d, s, 140, 260, 420, tk=push(d, s, 140, 260, 0.6, 1.25), opacity=0.9),
                                            lambda: sticker('gulal_yellow', d + 0.12, s, 600, 1030, 380, tk=push(d + 0.12, s, 600, 1030, 0.5, 1.2), opacity=0.9)])
hit(d)
shot_word('RANGEELA', 'rani', s, h, extras=[lambda: sticker('marigold', s, h, 90, 120, 210, tk=spin(s, h, 90, 120, 40)),
                                            lambda: sticker('marigold_yellow', s, h, 640, 1160, 230, tk=spin(s, h, 640, 1160, -40))])
shot_echo('DESI', 'night', h, e, color='#FFD97A')

# bar 2  TAJ -> SHAAN -> collage
d, s, h, e = bar(1)
shot_picture('taj', d, s, 'TAJ', label_y=SH * 0.2)
hit(d)
shot_word('SHAAN', 'saffron', s, h, extras=[lambda: sticker('mandala_line', s, h, CX, CY, 760, tk=spin(s, h, CX, CY, 30, 1, 1.06), opacity=0.5)])
shot_collage(['kites', 'fort', 'chai', 'diwali'], h, e)

# bar 3  PATANG (kites fly) -> UDAAN -> the break: HORN OK PLEASE
d, s, h, e = bar(2)
shot_picture('kites', d, s, 'PATANG', extras=[lambda: sticker('kite_rani', d, s, 560, 380, 220, tk=slide(d, s, 620, 520, 520, 300, ease='linear')),
                                               lambda: sticker('kite_saffron', d, s, 170, 640, 180, tk=slide(d, s, 120, 760, 220, 560, ease='linear'))])
hit(d)
shot_word('UDAAN', 'peacock', s, h, extras=[lambda: sticker('kite_rani', s, h, 600, 250, 150, tk=slide(s, h, 640, 300, 560, 200, ease='linear'))])
photo(BG['turmeric'], h, e, name='Background turmeric')
sticker('marigold', h, e, 110, 330, 190, tk=spin(h, e, 110, 330, 40))
sticker('marigold_yellow', h, e, 610, 950, 210, tk=spin(h, e, 610, 950, -40))
sticker('horn_ok_please', h, e, CX, CY, 640, tk=push(h, e, CX, CY, 1.0, 1.06), in_={'preset': 'thud', 'dur': 0.3, 'stagger': 0, 'order': 'forward', 'amount': 1})

# bar 4 (the big one after the break)  RAJASTHAN fort -> SHAHI -> DHOOM echo
d, s, h, e = bar(3)
shot_picture('fort', d, s, 'RAJASTHAN', label_y=SH * 0.2)
hit(d, 14)
shot_word('SHAHI', 'maroon', s, h, color='#FFD97A', extras=[lambda: sticker('paisley', s, h, 120, 1110, 260, tk=spin(s, h, 120, 1110, 12)),
                                                            lambda: sticker('paisley', s, h, 600, 170, 230, tk=spin(s, h, 600, 170, -12))])
shot_echo('DHOOM', 'turmeric', h, e, color='#5E0B1E', ghost='#5E0B1E')

# bar 5  CHAI -> CHAI word on cream -> split panels
d, s, h, e = bar(4)
shot_picture('chai', d, s)
hit(d)
shot_word('CHAI', 'cream', s, h, color='#5C3317', extras=[lambda: sticker('mandala_gold', s, h, CX, CY, 820, tk=spin(s, h, CX, CY, 20), opacity=0.45)])
shot_split(['varanasi', 'monsoon', 'cricket'], h, e)

# bar 6  BANARAS (diyas) -> MASALA -> BAARISH
d, s, h, e = bar(5)
shot_picture('varanasi', d, s, 'BANARAS', label_y=SH * 0.2, extras=[lambda: sticker('diya', d, s, 560, 1080, 220)])
hit(d)
shot_word('MASALA', 'saffron', s, h, extras=[lambda: sticker('rangoli', s, h, CX, 1160, 420, tk=spin(s, h, CX, 1160, 45), opacity=0.85),
                                             lambda: sticker('rangoli', s, h, CX, 120, 420, tk=spin(s, h, CX, 120, -45), opacity=0.85)])
shot_picture('monsoon', h, e, 'BAARISH', label_y=SH * 0.2)

# bar 7  SIXER! -> JUNOON -> echo JALWA
d, s, h, e = bar(6)
shot_picture('cricket', d, s, 'SIXER!', label_y=SH * 0.2)
hit(d)
shot_word('JUNOON', 'green', s, h, extras=[lambda: sticker('chakra_white', s, h, CX, CY, 700, tk=spin(s, h, CX, CY, 60), opacity=0.18)])
shot_echo('JALWA', 'rani', h, e)

# bar 8  DIWALI -> ROSHNI -> DIL SE
d, s, h, e = bar(7)
shot_picture('diwali', d, s, 'DIWALI', label_y=SH * 0.2)
hit(d)
shot_word('ROSHNI', 'night', s, h, color='#FFD97A', extras=[lambda: sticker('sparkle_gold', s, h, 150, 380, 90, tk=spin(s, h, 150, 380, 90, 0.6, 1.3)),
                                                             lambda: sticker('sparkle_gold', s + 0.1, h, 580, 900, 70, tk=spin(s + 0.1, h, 580, 900, -90, 0.6, 1.3)),
                                                             lambda: sticker('diya', s, h, CX, 1080, 240)])
shot_word('DIL SE', 'indigo', h, e, extras=[lambda: sticker('lotus', h, e, CX, 1060, 300, tk=push(h, e, CX, 1060, 0.9, 1.05))])

# finale: tricolour flag on night, JAI HIND! above it, INCREDIBLE INDIA below, marigolds in the corners
f0, f1 = FINALE, beat(21)
photo(BG['night'], f0, DUR, name='Background night')
for i, (k, y) in enumerate([('stroke_saffron', CY - 170), ('stroke_white', CY), ('stroke_green', CY + 170)]):
    ts = f0 + i * 0.08
    sticker(k, ts, DUR, CX, y, 860, tk=slide(ts, ts + 0.28, SW * 1.9 if i % 2 == 0 else -SW * 0.9, y, CX, y))
sticker('chakra', f0 + 0.3, DUR, CX, CY, 150, tk=spin(f0 + 0.3, DUR, CX, CY, 360))
word('JAI HIND!', f0 + 0.25, DUR, y=CY - 390, width=SW * 0.8, color='#FFFFFF', in_={'preset': 'punch_in', 'dur': 0.3, 'stagger': 0, 'order': 'forward', 'amount': 0.7})
hit(f0, 12)
word('INCREDIBLE INDIA', f1, DUR, y=CY + 380, width=SW * 0.74, color='#FFD97A', in_={'preset': 'fade_up', 'dur': 0.35, 'stagger': 0, 'order': 'forward', 'amount': 1})
for (x, y, sd) in [(70, 90, 30), (650, 90, -30), (70, 1190, -30), (650, 1190, 30)]:
    sticker('marigold' if sd > 0 else 'marigold_yellow', f1, DUR, x, y, 200, tk=spin(f1, DUR, x, y, sd), in_=ph('pop', 0.3))

# always on top: HUD marks, grain, vignette, fade to black
sticker('hud', 0.0, DUR, CX, CY, SW, opacity=0.8)
fx('grain', 0, DUR, params={'intensity': 10})
fx('vignetting', 0, DUR, params={'strength': 30})
end = copy.deepcopy(base_decor); end.update(id=new_id('dc'), start=18.0, end=DUR); items.append(end); order.append(end['id'])

# ---------------------------------------------------------------- write
r = copy.deepcopy(tpl)
r['title'] = 'India Beat Sync 9x16'
r['background'] = '#120A12'
r['bpm'], r['beat_offset'], r['duration'] = BPM, OFF, DUR
r['texts'] = texts
r['studio_project'] = dict(tpl['studio_project'], mediaBin=[], manualOrder=True, persp={'on': False, 'order': 'z'})
r['studio_scene'] = {'camera': {'on': False, 'near': 320, 'fog': {'on': False, 'start': 4000, 'end': 5000}, 'keys': [], 'shake': []},
                     'mirror': 'scale', 'items': items, 'order': order,
                     'note': 'Kinekit Studio recipe: India beat-sync, dynamic-promo style. Cuts on the beat grid (72.8 BPM), '
                             'stickers drawn for this edit; picture slots are illustrated stand-ins, swap them for Pexels / Pixabay shots (slot labels say what to search).'}
r['studio_media'] = media
json.dump(r, open(OUT, 'w'))
print('texts', len(texts), 'items', len(items), 'media', len(media), 'MB', round(os.path.getsize(OUT) / 1e6, 2))
