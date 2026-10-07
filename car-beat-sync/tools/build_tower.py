"""Rebuild the Car Beat Sync recipe as a connected 3D kinetic tower.

Every section (one bar of the song) is a tight block of words + its clip + a photo tile, laid flush on one face of a
square tower. Each new section sits on the next face (90 degrees round) and a bit lower, overlapping the previous
block so the corner joins them. Everything sticks once it lands; the camera spirals down the tower with beat-synced
whips, push-ins, tilt and roll. Cards are cut the moment they turn their back to the camera (no mirrored text).
"""
import copy, json, math, sys

SRC, WIDTHS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = len(sys.argv) > 4 and sys.argv[4] == 'preview'   # videos -> their stills (headless render has no clips)
d = json.load(open(SRC))
WID = json.load(open(WIDTHS))
sc = d['studio_scene']
orig_items = {i['id']: i for i in sc['items']}
orig_text = {}
for t in d['texts']:
    orig_text.setdefault(t['text'], t)

DUR = 18.6
F = 1000                      # Studio camera focal length
AX, AZ = 360.0, 4000.0        # tower axis (world x, depth)
W = 660.0                     # face width
HALF = W / 2
GAP = 10.0                    # gap between joined cards
RED, WHITE = '#E8202A', '#FFFFFF'
LINE = 24 * 0.92              # text line box height per size unit (line_height 0.92)
CAP = 0.72                    # visible cap height / line box


def bez(u):                   # smoothstep-ish
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


def whip(u):                  # fast middle, soft ends
    u = min(1, max(0, u))
    return 0.5 * (1 - math.cos(math.pi * (u ** 1.35 if u < 0.5 else 1 - (1 - u) ** 1.35))) if False else (
        (2 ** (14 * u - 7) / 2 - 2 ** -7 / 2) / (1 - 2 ** -7) if u < 0.5 else 1 - (2 ** (-14 * u + 7) / 2 - 2 ** -7 / 2) / (1 - 2 ** -7))


# ------------------------------------------------------------------ the song, bar by bar
#   (start, words [(text, appear, color)], clip id, clip aspect, trimIn, clip length, photo)
SECTIONS = [
    (0.00, [('TURN', 0.30, WHITE), ('THE KEY', 0.51, RED), ('READY', 1.32, WHITE), ('SET', 2.14, RED)], 'c10_ignition', '9:16', 0.6, 4.0, 'ph_p1_supercar'),
    (2.97, [('ZERO', 3.38, WHITE), ('TO', 3.79, RED), ('SIXTY', 4.20, WHITE)], 'c01_drift_pair', '16:9', 0.2, 4.0, 'ph_p2_race'),
    (4.61, [('NO', 5.02, RED), ('BRAKES', 5.43, WHITE), ('TONIGHT', 5.84, RED)], 'c02_blue_supercar', '9:16', 0.4, 4.0, 'ph_p3_night'),
    (6.26, [('REDLINE', 6.67, RED), ('EVERY', 7.08, WHITE), ('GEAR', 7.49, WHITE)], 'c04_tacho', '9:16', 0.2, 2.634, 'ph_p4_street_race'),
    (7.90, [('BURN', 8.31, WHITE), ('THE', 8.72, RED), ('RUBBER', 9.13, WHITE)], 'c11_blue_drift', '16:9', 0.4, 4.0, 'ph_p5_drift'),
    (9.54, [('PURE', 9.95, WHITE), ('MUSCLE', 10.36, RED), ('V8', 10.77, WHITE)], 'c07_challenger', '9:16', 0.5, 4.0, 'ph_p6_headlight'),
    (11.19, [('LIGHTS', 11.60, WHITE), ('OUT', 12.01, RED), ('FLAT OUT', 12.42, WHITE)], 'c05_tunnel', '9:16', 0.4, 4.0, 'ph_p1_supercar'),
    (12.83, [('SIDEWAYS', 13.24, WHITE), ('ALL', 13.65, RED), ('NIGHT', 14.06, WHITE)], 'c06_drift_slowmo', '16:9', 0.3, 4.0, 'ph_p3_night'),
    (14.47, [('TOP', 14.88, RED), ('SPEED', 15.29, WHITE), ('ONLY', 15.70, RED)], 'c12_rain_supercar', '9:16', 0.4, 4.0, 'ph_p4_street_race'),
    (16.03, [('FULL', 16.11, WHITE), ('SEND!', 16.32, RED), ('NO LIMITS', 16.94, WHITE)], None, None, 0, 0, 'ph_p2_race'),
]
LATE_STILL = {'c10_ignition': ('st_c10_ignition_377', '9:16'), 'c01_drift_pair': ('st_c01_drift_pair_229', '16:9'),
              'c02_blue_supercar': ('st_c02_blue_supercar_249', '9:16'), 'c04_tacho': ('st_c04_tacho_229', '9:16'),
              'c11_blue_drift': ('st_c11_blue_drift_249', '16:9'), 'c07_challenger': ('st_c07_challenger_259', '9:16'),
              'c05_tunnel': ('st_c05_tunnel_249', '9:16'), 'c06_drift_slowmo': ('st_c06_drift_slowmo_30', '16:9'),
              'c12_rain_supercar': ('st_c12_rain_supercar_40', '9:16')}
EARLY_STILL = {k: v for k, v in LATE_STILL.items()}
EARLY_STILL.update({'c10_ignition': ('st_c10_ignition_377', '9:16'), 'c01_drift_pair': ('st_c01_drift_pair_20', '16:9'),
                    'c02_blue_supercar': ('st_c02_blue_supercar_40', '9:16'), 'c04_tacho': ('st_c04_tacho_20', '9:16'),
                    'c11_blue_drift': ('st_c11_blue_drift_40', '16:9'), 'c07_challenger': ('st_c07_challenger_50', '9:16'),
                    'c05_tunnel': ('st_c05_tunnel_40', '9:16'), 'c12_rain_supercar': ('st_c12_rain_supercar_40', '9:16')})
ASP = {'9:16': 9 / 16, '16:9': 16 / 9, '1:1': 1, '4:3': 4 / 3, '3:4': 0.75, '3:2': 1.5, '2:3': 2 / 3}


def text_rows(words, x0, x1, align, max_size):
    """stack words in one column [x0, x1]; each word as wide as the column (capped). returns rows + height"""
    rows, y = [], 0.0
    for txt, at, col in words:
        w1 = WID[txt][0]
        size = min(max_size, (x1 - x0) / w1)
        w = w1 * size
        cap = LINE * size * CAP
        cx = x0 + w / 2 if align == 'left' else x1 - w / 2 if align == 'right' else (x0 + x1) / 2
        rows.append(dict(kind='text', text=txt, at=at, color=col, size=size, u=cx, y=y + cap / 2, w=w, h=cap))
        y += cap + GAP
    return rows, y - GAP


def best_aspect(width, height, choices=('16:9', '3:2', '4:3', '1:1', '3:4', '2:3', '9:16')):
    return min(choices, key=lambda a: abs(width / ASP[a] - height))


def layout_section(k, sec):
    start, words, clip, casp, trim, clen, photo = sec
    cards = []
    left = k % 2 == 0
    if clip and casp == '9:16':
        # clip column on one side, words + photo stacked in the other column, all flush
        mw = W * 0.44
        mh = mw / ASP['9:16']
        mx0, mx1 = (-HALF, -HALF + mw) if left else (HALF - mw, HALF)
        tx0, tx1 = (mx1 + GAP, HALF) if left else (-HALF, mx0 - GAP)
        rows, th = text_rows(words, tx0, tx1, 'left' if left else 'right', 7.5)
        cards += rows
        rest = mh - th - GAP * 2 - 8
        if rest > 90:
            pw = tx1 - tx0
            a = best_aspect(pw, rest)
            ph = pw / ASP[a]
            cards.append(dict(kind='bar', at=words[-1][1] + 0.1, u=(tx0 + tx1) / 2, y=th + GAP + 4, w=pw, h=8))
            cards.append(dict(kind='photo', src=photo, aspect=a, at=words[-1][1] + 0.2, u=(tx0 + tx1) / 2, y=th + GAP * 2 + 8 + ph / 2, w=pw, h=ph))
            body = max(mh, th + GAP * 2 + 8 + ph)
        else:
            body = max(mh, th)
        cards.append(dict(kind='clip', clip=clip, aspect=casp, trim=trim, clen=clen, at=max(0.05, start - 0.16), u=(mx0 + mx1) / 2, y=mh / 2, w=mw, h=mh))
        return cards, body
    if clip:   # 16:9 clip: words full width on top, red bar, clip under it, photo tile beside the last word
        rows, th = text_rows(words, -HALF, HALF, 'left' if left else 'right', 7.0)
        cards += rows
        cards.append(dict(kind='bar', at=max(0.05, start - 0.16), u=0, y=th + GAP + 4, w=W, h=8))
        mh = W / ASP['16:9']
        cards.append(dict(kind='clip', clip=clip, aspect=casp, trim=trim, clen=clen, at=max(0.05, start - 0.16), u=0, y=th + GAP * 2 + 8 + mh / 2, w=W, h=mh))
        # photo tile fills the empty end of the shortest word row
        short = min(rows, key=lambda r: r['w'])
        free = W - short['w'] - GAP
        if free > 120:
            pu = (HALF - free / 2) if left else (-HALF + free / 2)
            a = '16:9'
            pw = min(free, short['h'] * ASP[a])
            pu = (HALF - pw / 2) if left else (-HALF + pw / 2)
            cards.append(dict(kind='photo', src=photo, aspect=a, at=words[-1][1] + 0.2, u=pu, y=short['y'], w=pw, h=pw / ASP[a]))
        return cards, th + GAP * 2 + 8 + mh
    # finale: huge words full width, photo strip
    rows, th = text_rows(words, -HALF, HALF, 'center', 11.0)
    cards += rows
    cards.append(dict(kind='bar', at=words[-1][1] + 0.1, u=0, y=th + GAP + 4, w=W, h=8))
    ph = W / ASP['16:9']
    cards.append(dict(kind='photo', src=photo, aspect='16:9', at=words[-1][1] + 0.2, u=0, y=th + GAP * 2 + 8 + ph / 2, w=W, h=ph))
    return cards, th + GAP * 2 + 8 + ph


# ------------------------------------------------------------------ place sections on the spiral
placed = []        # dicts with world x, y, depth, ry, start
Y0 = 400.0
y = Y0
sec_info = []
for k, sec in enumerate(SECTIONS):
    cards, body = layout_section(k, sec)
    P = -90.0 * k
    pr = math.radians(P)
    cx, cz = AX - HALF * math.sin(pr), AZ - HALF * math.cos(pr)     # face centre
    rx_, rz_ = math.cos(pr), -math.sin(pr)                           # face right vector
    for c in cards:
        c.update(sec=k, P=P, wx=cx + c['u'] * rx_, wz=cz + c['u'] * rz_, wy=y + c['y'], ry=-P)
        placed.append(c)
    sec_info.append(dict(start=sec[0], P=P, top=y, body=body, cards=cards))
    y += body * 0.5 + 30     # next block overlaps this one's lower part: the corner joins them

# ------------------------------------------------------------------ camera
B = [s['start'] for s in sec_info] + [DUR + 1]
hits = sorted(c['at'] for c in placed if c['kind'] in ('text', 'clip'))


def follow_y(t):
    """camera height: glides towards each new card as it lands (keeps the block it belongs to in view)"""
    v = sec_info[0]['top'] + 150
    for c in FOLLOW:
        if t < c['at']: break
        tgt = 0.5 * (c['wy'] + c['h'] / 2) + 0.5 * (sec_info[c['sec']]['top'] + sec_info[c['sec']]['body'] / 2) - 40
        v += (tgt - v) * bez((t - c['at']) / 0.5)
    return v


FOLLOW = sorted([c for c in placed if c['kind'] != 'bar'], key=lambda c: c['at'])


def pan_at(t):
    pts = [(0.0, 75.0), (0.9, 34.0)]
    for k2 in range(1, len(sec_info)):
        b = sec_info[k2]['start']
        pts.append((b - 0.32, -90.0 * (k2 - 1) - 28))
        pts.append((b + 0.15, -90.0 * k2 + 34))
    pts.append((16.9, -90.0 * (len(sec_info) - 1) - 5))
    pts.append((DUR, -90.0 * (len(sec_info) - 1) - 70))
    for (ta, pa), (tb, pb) in zip(pts, pts[1:]):
        if ta <= t <= tb:
            u = (t - ta) / max(tb - ta, 1e-6)
            return pa + (pb - pa) * (whip(u) if tb - ta < 0.6 else 0.7 * u + 0.3 * bez(u))
    return pts[-1][1]


def sec_at(t):
    k = 0
    while k + 1 < len(sec_info) and t >= sec_info[k + 1]['start'] - 0.3: k += 1
    return k


def cam(t):
    # pan: never stops turning. Slow drift round each face, whip across the corner on the bar line
    pan = pan_at(t)
    k = sec_at(t)
    s0 = sec_info[k]['start']; s1 = B[k + 1]
    ph = min(1, max(0, (t - s0) / max(s1 - s0, 0.1)))
    # distance: wide during the whip (shows the corner), slow push-in through the bar, kick on every hit
    R = 1370 - 150 * bez(ph)
    for k2 in range(1, len(sec_info)):
        u = (t - (sec_info[k2]['start'] - 0.34)) / 0.6
        if 0 <= u <= 1: R += 420 * math.sin(math.pi * u) ** 2
    for h in hits:
        u = t - h
        if 0 <= u < 0.35: R -= 70 * math.exp(-u * 12) * math.sin(min(1, u / 0.05) * math.pi / 2)
    # intro: fall in from high and far
    if t < 0.9:
        e = bez(t / 0.9); R += (1 - e) * 1600
    # finale: pull way back and look up the tower
    fin = bez((t - 16.9) / 1.6)
    R += fin * 2200
    yc = follow_y(t) - fin * 900
    tilt = -7 + 5 * math.sin(t * 1.9) - 10 * fin
    roll = 0.0
    for k2 in range(1, len(sec_info)):
        u = (t - (sec_info[k2]['start'] - 0.34)) / 0.7
        if 0 <= u <= 1: roll += (7 if k2 % 2 else -7) * math.sin(math.pi * u) * (1 - u * 0.4)
    roll += 2.2 * math.sin(t * 2.7)
    if t < 0.9: roll += (1 - bez(t / 0.9)) * -14; tilt += (1 - bez(t / 0.9)) * -22; yc -= (1 - bez(t / 0.9)) * 700
    pr = math.radians(pan)
    ex, ez = AX - R * math.sin(pr), AZ - R * math.cos(pr)
    return dict(x=ex, y=yc, z=ez + F, pan=pan, tilt=tilt, roll=roll, lens=1.0)


FPS_KEYS = 24
keys = []
for i in range(int(DUR * FPS_KEYS) + 1):
    t = i / FPS_KEYS
    c = cam(t)
    keys.append(dict(t=round(t, 3), x=round(c['x'], 1), y=round(c['y'], 1), z=round(c['z'], 1), pan=round(c['pan'], 2),
                     tilt=round(c['tilt'], 2), roll=round(c['roll'], 2), lens=c['lens'], ease='linear'))


def facing_spans(c):
    """intervals where the card faces the camera: it sticks, hides while the tower turns its back, comes round again"""
    nr = math.radians(c['ry'])
    nx, nz = math.sin(nr), -math.cos(nr)
    spans, on, t, st = [], False, c['at'], None
    while t <= DUR + 1e-9:
        k = cam(t)
        dx, dz = k['x'] - c['wx'], k['z'] - F - c['wz']
        vis = (dx * nx + dz * nz) > 0.06 * math.hypot(dx, dz)
        if vis and not on: on, st = True, t
        if not vis and on: on = False; spans.append((round(st, 3), round(t, 3)))
        t += 1 / 60
    if on: spans.append((round(st, 3), DUR))
    return [(a, b) for a, b in spans if b - a > 0.12]


# ------------------------------------------------------------------ layers
tmpl_text = d['texts'][0]
texts, items, order = [], [], []
nid = [0]


def new_id(p):
    nid[0] += 1; return f'{p}{nid[0]}'


base_photo = orig_items['ph2']
base_video = orig_items['vd1']
base_bar = orig_items['dc4']

for c0 in sorted(placed, key=lambda c: c['at']):
  for si, (st0, end) in enumerate(facing_spans(c0)):
    c = dict(c0, at=st0)
    first = si == 0 and abs(st0 - c0['at']) < 0.02
    common = dict(x=round(c['wx'], 1), y=round(c['wy'], 1), depth=round(c['wz'], 1), ry=round(c['ry'], 2), rx=0, rot=0)
    if c['kind'] == 'text':
        t = copy.deepcopy(orig_text.get(c['text'], tmpl_text))
        t.update(text=c['text'], start=round(c['at'], 3), end=end, x=common['x'], y=common['y'], size=round(c['size'], 3), color=c['color'],
                 split='whole', align='center', tracking=0.01, line_height=0.92,
                 **{'in': {'preset': 'punch_in', 'dur': 0.16, 'stagger': 0, 'order': 'forward', 'amount': 1} if first else 'none', 'out': 'none'})
        st = t['studio']; st.update(id=new_id('tx'), depth=common['depth'], cam=True, rot=0, tk=[], rx=0, ry=common['ry'])
        st['slot'] = {'on': True, 'label': f"Bar {c['sec'] + 1}: {c['text']}"}
        texts.append(t); order.append(st['id'])
    elif c['kind'] == 'bar':
        it = copy.deepcopy(base_bar); it.update(id=new_id('dc'), name='Red joint', start=round(c['at'], 3), end=end, w=round(c['w'], 1), h=8, **common)
        it['in'] = {'preset': 'wipe_right', 'dur': 0.16} if False else None
        items.append(it); order.append(it['id'])
    elif c['kind'] == 'photo':
        it = copy.deepcopy(base_photo); it.update(id=new_id('ph'), name=f"Photo {c['src'][3:]}", start=round(c['at'], 3), end=end, w=round(c['w'], 1), yaw=0, **common)
        it['photo'].update(src='up:' + c['src'], aspect=c['aspect'])
        it['in'] = {'preset': 'pop', 'dur': 0.18, 'stagger': 0, 'order': 'forward', 'amount': 1} if first else None
        items.append(it); order.append(it['id'])
    elif c['kind'] == 'clip' and not first:   # later passes round the tower: the clip's last frame
        s_, a_ = LATE_STILL[c['clip']]
        it = copy.deepcopy(base_photo)
        it.update(id=new_id('ph'), name=f"Still {c['clip']}", start=round(c['at'], 3), end=end, w=round(c['w'], 1), yaw=0, **common)
        it['photo'].update(src='up:' + s_, aspect=a_); it['in'] = None
        items.append(it); order.append(it['id'])
    elif c['kind'] == 'clip':
        vend = min(end, round(c['at'] + (c['clen'] - c['trim']) - 0.08, 3))
        if PREVIEW:
            it = copy.deepcopy(base_photo); s, a = EARLY_STILL[c['clip']]
            it.update(id=new_id('ph'), name=f"Clip {c['clip']}", start=round(c['at'], 3), end=vend, w=round(c['w'], 1), yaw=0, **common)
            it['photo'].update(src='up:' + s, aspect=a)
        else:
            it = copy.deepcopy(base_video)
            it.update(id=new_id('vd'), name=c['clip'], start=round(c['at'], 3), end=vend, w=round(c['w'], 1), **common)
            it['video'].update(src='vid:cb_' + c['clip'], trimIn=c['trim'])
        it['in'] = {'preset': 'pop', 'dur': 0.18, 'stagger': 0, 'order': 'forward', 'amount': 1}
        items.append(it); order.append(it['id'])
        if vend < end - 0.05:   # clip ran out: its last frame sticks as a photo
            s, a = LATE_STILL[c['clip']]
            st = copy.deepcopy(base_photo)
            st.update(id=new_id('ph'), name=f"Still {c['clip']}", start=vend, end=end, w=round(c['w'], 1), yaw=0, **common)
            st['photo'].update(src='up:' + s, aspect=a); st['in'] = None
            items.append(st); order.append(st['id'])

# keep the beat fx, grain, vignette, backdrop and the fade to black from the original
keep = [i for i in sc['items'] if i['type'] == 'fx' or i['id'] in ('ph124', 'dc144')]
items = keep[:1] and [orig_items['ph124']] + items + [i for i in keep if i['id'] != 'ph124']
order = ['ph124'] + order + [i['id'] for i in keep if i['id'] != 'ph124']

d['texts'] = texts
d['title'] = 'Car Beat Sync 3D Tower 9x16 (connected spiral)'
d['duration'] = DUR
sc['items'] = items
sc['order'] = order
sc['camera'] = dict(on=True, near=320, fog=dict(on=False, start=4000, end=5000), keys=keys, shake=[])
sc['note'] = ('Kinekit Studio recipe: car beat-sync, connected 3D kinetic tower. Every bar is a tight block of words, '
              'its clip and a photo, flush on one face of a square tower; each bar lands on the next face, the camera '
              'whips round the corner on the beat and spirals down. Clips and photos from Pexels (free to use).')
d['studio_project']['manualOrder'] = True
used = {i['photo']['src'][3:] for i in items if i['type'] == 'photo'}
d['studio_media'] = {k: v for k, v in d['studio_media'].items() if k in used}
json.dump(d, open(OUT, 'w'))
print('texts', len(texts), 'items', len(items), 'keys', len(keys), 'media', len(d['studio_media']))
for s in sec_info: print(f"bar {s['start']:5.2f} pan {s['P']:6.0f} top {s['top']:7.1f} body {s['body']:6.1f}")
