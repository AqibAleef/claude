"""Kinekit Studio patch 06: Magic Remover, KineMaster clip blur, and independent duplicates.

Magic Remover (KineMaster's background removal) on photo and video layers, learned from a KineMaster 8 project:
  image layer: field 119 = 1 switches it on, field 121 = kmm://path-rel/contents/<file>-<ext>.mask, a 352 x 352 PNG
               stretched over the whole picture (RGB = hard cut, alpha = soft matte)
  video layer: field 144 = 1 (KineMaster cuts every frame on the phone, no mask file)
KineMaster's built-in Blur on a single layer is a clip effect: image field 125 / video field 150 =
  { uri: kmm://assetitemid/com.nexstreaming.csd.blurall, f_block_size }.
The export ships the untouched photo plus the flag and mask, so KineMaster does the cut-out itself and redoes it when
the photo is replaced. The Studio preview applies the mask (and the blur) in pictureFor(); masks come from the recipe,
an imported PNG, or automatic detection (MediaPipe DeepLab v3 finds the subjects, Magic Touch cuts each one out;
loaded from the CDN the first time it is needed).

Also fixes clips exporting with Magic Remover switched on: the KineMaster 8 video template had field 144 = 1.

Duplicates: the copy gets its own name, its own template-slot label and (photos) its own media id, so replacing the
picture of one layer never swaps the other and the two can be told apart in the Outliner and the Template tab.

    python3 06_magic_remover.py IN.html OUT.html
"""
import sys
src, dst = sys.argv[1:3]
s = open(src, encoding='utf-8').read()


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, f'anchor found {n}x, expected {count}: {old[:90]!r}'
    s = s.replace(old, new)


# ---------------------------------------------------------------- KineMaster writer: clip effect at any field, flags
sub("Object.assign(K, { cornerPin, clipEffect, flipPins });",
    """Object.assign(K, { cornerPin, clipEffect, flipPins });
/* KineMaster per-layer (clip) effect at a given field: image layers use 125, video layers 150 */
const BLURALL_URI = 'kmm://assetitemid/com.nexstreaming.csd.blurall';
function clipEffectAt(pl, f, fx) {
  const kf = [...pb.f32(1, 0)];
  for (const [k, v] of Object.entries(fx.params || {})) pb.blob(2, fxParam(k, v), kf);
  pb.blob(3, pb.ease(1), kf);
  const n = setF(pl, f, 0); n.k = 'b'; n.name = '?' + f; n.v = new Uint8Array([...pb.str(1, fx.uri), ...pb.blob(2, kf)]); delete n.raw;
}
function strF(nodes, f, str) { const n = setF(nodes, f, 0); n.k = 's'; n.v = str; delete n.raw; return n; }
Object.assign(K, { clipEffectAt, BLURALL_URI });""")

sub("addImage({ name, data, natW, natH, startMs, endMs, kfs, mirror = null, opacity = 1, blend = 0, fadeIn = 0, fadeOut = 0, pins = null, alpha = null, clipFx = null }) {",
    "addImage({ name, data, natW, natH, startMs, endMs, kfs, mirror = null, opacity = 1, blend = 0, fadeIn = 0, fadeOut = 0, pins = null, alpha = null, clipFx = null, magic = null, blur = 0 }) {")
sub("""    if (clipFx) clipEffect(pl, clipFx);
    return this.appendLayer(it);""",
    """    if (clipFx) clipEffect(pl, clipFx);
    else if (blur > 0) clipEffectAt(pl, 125, { uri: BLURALL_URI, params: { f_block_size: blur } });
    if (magic) {   // Magic Remover: switch + the mask KineMaster keeps next to the picture
      setF(pl, 119, 1);
      if (magic.mask) {
        const mp = path.replace(/\\.([A-Za-z0-9]+)$/, '-$1') + '.mask';
        this.raw.files = this.raw.files.filter(f => f.name !== mp); this.raw.files.push({ name: mp, data: magic.mask });
        strF(pl, 121, 'kmm://path-rel/' + mp);
      }
    }
    return this.appendLayer(it);""")
sub("addVideo({ name, data, sourceMs, srcW, srcH, startMs, endMs, trimStartMs = 0, speed = 1, volume = 0, kfs, mirror = null, opacity = 1, blend = 0, fadeIn = 0, fadeOut = 0, pins = null, alpha = null }) {",
    "addVideo({ name, data, sourceMs, srcW, srcH, startMs, endMs, trimStartMs = 0, speed = 1, volume = 0, kfs, mirror = null, opacity = 1, blend = 0, fadeIn = 0, fadeOut = 0, pins = null, alpha = null, magic = false, blur = 0 }) {")
sub("""    if (pins || alpha !== null) cornerPin(L, pins, alpha ?? opacity);
    return this.appendLayer(it);
  }
  addAudio(""",
    """    if (pins || alpha !== null) cornerPin(L, pins, alpha ?? opacity);
    if (blur > 0) clipEffectAt(pl, 150, { uri: BLURALL_URI, params: { f_block_size: blur } });
    // Magic Remover on a clip (KineMaster cuts every frame on the phone). Always written: the built-in KineMaster 8
    // video template came from a project with it switched on (144 = 1, 142/143 = 352), so every clip used to export with it on
    setF(pl, 144, magic ? 1 : 0); setF(pl, 142, 0); setF(pl, 143, 0);
    return this.appendLayer(it);
  }
  addAudio(""")

# ---------------------------------------------------------------- export glue
sub("clipFx: L.clipFx || null, alpha: L.flip123 ? lk.opacity : null }, lk)); }",
    "clipFx: L.clipFx || null, alpha: L.flip123 ? lk.opacity : null, magic: !L.flip123 && b.magic && b.magic.on ? { mask: await kmMaskBytes(b) } : null, blur: L.flip123 ? 0 : +b.clipBlur || 0 }, lk)); }")
sub("      kfs: L.kfs, pins: L.pins || null, alpha: L.pins ? lk.opacity : null }, lk));",
    "      kfs: L.kfs, pins: L.pins || null, alpha: L.pins ? lk.opacity : null, magic: !!(b.magic && b.magic.on), blur: +b.clipBlur || 0 }, lk));")

# ---------------------------------------------------------------- preview: every picture goes through the layer's look
sub("""function pictureFor(L, b) {
  if (L.vid) return videoFrame(L, b);""",
    """function pictureFor(L, b) { return mrLook(L, b, pictureRaw(L, b)); }
function pictureRaw(L, b) {
  if (L.vid) return videoFrame(L, b);""")

ENGINE = r"""
// ------------------------------------------------------------------ Magic Remover (KineMaster background removal)
/* The phone does the real cut-out (KineMaster's Magic Remover). Here: a preview mask per layer, from the recipe, an
   imported PNG, or automatic detection - MediaPipe DeepLab v3 finds the subjects, Magic Touch cuts each one out. */
const MR = (() => {
  const base = () => window.KK_MR_BASE || 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14';
  const models = () => window.KK_MR_MODELS || 'https://storage.googleapis.com/mediapipe-models';
  let ready = null;
  const load = () => ready || (ready = (async () => {
    const V = await import(base() + '/vision_bundle.mjs');
    const fs = await V.FilesetResolver.forVisionTasks(base() + '/wasm');
    const seg = await V.ImageSegmenter.createFromOptions(fs, { baseOptions: { modelAssetPath: models() + '/image_segmenter/deeplab_v3/float32/1/deeplab_v3.tflite' }, runningMode: 'IMAGE', outputCategoryMask: true, outputConfidenceMasks: false });
    const touch = await V.InteractiveSegmenter.createFromOptions(fs, { baseOptions: { modelAssetPath: models() + '/interactive_segmenter/magic_touch/float32/1/magic_touch.tflite' }, outputCategoryMask: false, outputConfidenceMasks: true });
    return { seg, touch };
  })().catch(e => { ready = null; throw e; }));
  // one seed point per detected subject: connected regions of "not background" on a coarse grid, largest first
  function seeds(cat, W, H) {
    const g = 72, gw = Math.max(2, Math.round(g * W / Math.max(W, H))), gh = Math.max(2, Math.round(g * H / Math.max(W, H)));
    const on = new Uint8Array(gw * gh);
    for (let y = 0; y < gh; y++) for (let x = 0; x < gw; x++) on[y * gw + x] = cat[Math.min(H - 1, Math.floor((y + 0.5) * H / gh)) * W + Math.min(W - 1, Math.floor((x + 0.5) * W / gw))] ? 1 : 0;
    const seen = new Uint8Array(gw * gh), comps = [];
    for (let i = 0; i < on.length; i++) {
      if (!on[i] || seen[i]) continue;
      const cells = [], st = [i]; seen[i] = 1;
      while (st.length) { const c = st.pop(); cells.push(c); const x = c % gw, y = (c / gw) | 0;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = x + dx, ny = y + dy, n = ny * gw + nx; if (nx >= 0 && ny >= 0 && nx < gw && ny < gh && on[n] && !seen[n]) { seen[n] = 1; st.push(n); } } }
      if (cells.length >= gw * gh * 0.004) comps.push(cells);
    }
    comps.sort((a, b) => b.length - a.length);
    return comps.slice(0, 4).map(cells => {   // the cell nearest the region's centre (stays inside odd shapes)
      let sx = 0, sy = 0; for (const c of cells) { sx += c % gw; sy += (c / gw) | 0; } const mx = sx / cells.length, my = sy / cells.length;
      let best = cells[0], bd = 1e9; for (const c of cells) { const d = (c % gw - mx) ** 2 + (((c / gw) | 0) - my) ** 2; if (d < bd) { bd = d; best = c; } }
      return { x: (best % gw + 0.5) / gw, y: (((best / gw) | 0) + 0.5) / gh };
    });
  }
  async function mask(src) {
    const { seg, touch } = await load();
    const w0 = src.videoWidth || src.naturalWidth || src.width, h0 = src.videoHeight || src.naturalHeight || src.height, s = Math.min(1, 1024 / Math.max(w0, h0));
    const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w0 * s)); c.height = Math.max(1, Math.round(h0 * s)); c.getContext('2d').drawImage(src, 0, 0, c.width, c.height);
    const r = seg.segment(c), cm = r.categoryMask, pts = seeds(cm.getAsUint8Array(), cm.width, cm.height); cm.close && cm.close(); r.close && r.close();
    if (!pts.length) pts.push({ x: 0.5, y: 0.5 });
    let acc = null, tw = 0, th = 0;
    for (const p of pts) {
      const t = touch.segment(c, { keypoint: p }), m = t.confidenceMasks[0], a = m.getAsFloat32Array(); tw = m.width; th = m.height;
      if (!acc) acc = new Float32Array(a.length); for (let i = 0; i < a.length; i++) if (a[i] > acc[i]) acc[i] = a[i];
      m.close && m.close(); t.close && t.close();
    }
    const out = document.createElement('canvas'); out.width = tw; out.height = th; const g = out.getContext('2d'), d = g.createImageData(tw, th);
    for (let i = 0; i < acc.length; i++) { d.data[i * 4] = d.data[i * 4 + 1] = d.data[i * 4 + 2] = 255; d.data[i * 4 + 3] = Math.round(clamp((acc[i] - 0.25) / 0.5, 0, 1) * 255); }
    g.putImageData(d, 0, 0); return out;
  }
  return { load, mask };
})();
const mrState = new Map();          // layer id -> { busy, err, msg }: transient, never saved
const lookCache = new Map(), vLook = new Map(), vMasks = new Map(); let vmBusy = false, vmFail = false;
function photoMask(b) {
  const M = b.magic, src = b.photo && b.photo.src;
  if (M.mask) {
    const mk = media.get(String(M.mask).slice(3));
    if (mk && (M.how !== 'auto' || !M.for || M.for === src)) return mk;   // an auto mask is redone when the photo changes
    if (!mk && M.how !== 'auto') return null;                              // still loading
  }
  if (String(src || '').startsWith('up:') && media.has(src.slice(3))) autoMask(b);
  return null;
}
function autoMask(b, force = false) {
  const st = mrState.get(b.id) || {}; mrState.set(b.id, st);
  const src = b.photo.src; if (st.busy || (!force && st.err === src)) return;
  st.busy = true; st.err = null; refreshMagic(b);
  MR.mask(media.get(src.slice(3))).then(c => {
    const id = 'mask_' + uid(); media.set(id, c); c.toBlob(bl => { if (bl) idb.put(id, bl); }, 'image/png');
    b.magic.mask = 'up:' + id; b.magic.how = 'auto'; b.magic.for = src; lookCache.clear(); saveSoon(); drawAll();
  }).catch(e => {
    st.err = src; st.msg = e && e.message || String(e);
    toast('Automatic cut-out unavailable (it needs the internet the first time). Import a mask, or just export: KineMaster cuts the subject out on the phone.', true, 5000);
  }).finally(() => { st.busy = false; refreshMagic(b); });
}
function videoMask(L, b, el) {
  const id = b.id, key = id + '@' + Math.round(clipTime(b, T) * 10);
  if (vMasks.has(key)) { vMasks.get(id + '@last').key = key; return vMasks.get(key); }
  if (!vmBusy && !vmFail) {
    vmBusy = true; const w = el.videoWidth || el.width, h = el.videoHeight || el.height, snap = document.createElement('canvas');
    snap.width = Math.max(1, Math.round(w * Math.min(1, 640 / Math.max(w, h)))); snap.height = Math.max(1, Math.round(h * snap.width / Math.max(1, w)));
    try { snap.getContext('2d').drawImage(el, 0, 0, snap.width, snap.height); } catch (e) { vmBusy = false; return null; }
    MR.mask(snap).then(c => { vMasks.set(key, c); vMasks.set(id + '@last', { key, c }); if (vMasks.size > 400) vMasks.delete(vMasks.keys().next().value); drawAll(); })
      .catch(() => { vmFail = true; }).finally(() => { vmBusy = false; });
  }
  const last = vMasks.get(id + '@last'); return last ? last.c : null;
}
function mrLook(L, b, cv) {
  if (!cv || !b || L.flip123 || (b.type !== 'photo' && b.type !== 'video')) return cv;
  const M = b.magic, on = !!(M && M.on), bl = +b.clipBlur || 0; if (!on && !bl) return cv;
  const isV = b.type === 'video';
  const mk = on ? (isV ? (M.preview === false ? null : videoMask(L, b, cv)) : photoMask(b)) : null;
  if (!mk && !bl) return cv;
  const w = cv.videoWidth || cv.width, h = cv.videoHeight || cv.height; if (!w || !h) return cv;
  const key = isV ? null : L.key + '|' + (mk ? M.mask : '-') + '|' + bl;
  if (key && lookCache.has(key)) return lookCache.get(key);
  const out = key ? document.createElement('canvas') : (vLook.get(b.id) || (vLook.set(b.id, document.createElement('canvas')), vLook.get(b.id)));
  if (out.width !== w) out.width = w; if (out.height !== h) out.height = h;
  const g = out.getContext('2d'); g.clearRect(0, 0, w, h);
  if (bl) { g.drawImage(cv, 0, 0, w, h); g.filter = `blur(${(bl * Math.max(w, h) / 700).toFixed(1)}px)`; }   // sharp copy underneath keeps the edges filled
  g.drawImage(cv, 0, 0, w, h); g.filter = 'none';
  if (mk) { g.globalCompositeOperation = 'destination-in'; g.drawImage(mk, 0, 0, w, h); g.globalCompositeOperation = 'source-over'; }
  if (key) { if (lookCache.size > 80) lookCache.delete(lookCache.keys().next().value); lookCache.set(key, out); }
  return out;
}
/* the mask KineMaster stores next to a picture: 352 x 352 PNG over the whole image, RGB = hard cut, alpha = matte */
async function kmMaskBytes(b) {
  const mk = b.magic && b.magic.mask && media.get(String(b.magic.mask).slice(3)); if (!mk) return null;
  const c = document.createElement('canvas'); c.width = c.height = 352; const g = c.getContext('2d'); g.drawImage(mk, 0, 0, 352, 352);
  const d = g.getImageData(0, 0, 352, 352); for (let i = 0; i < d.data.length; i += 4) { const v = d.data[i + 3] >= 128 ? 255 : 0; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; }
  g.putImageData(d, 0, 0); return KScene.toBytes(c, 'image/png');
}
function mrStatus(b) {
  const M = b.magic || {}, st = mrState.get(b.id) || {};
  if (b.type === 'video') return M.on ? (vmFail ? 'Preview cut-out unavailable offline; KineMaster still cuts the clip out on the phone.' : 'KineMaster cuts every frame out on the phone. The preview here follows along, a little behind.') : 'Off.';
  if (!M.on) return 'Off.';
  if (st.busy) return 'Finding the subject&hellip;';
  if (M.mask && media.has(String(M.mask).slice(3))) return { auto: 'Cut-out found automatically.', imported: 'Cut-out from your mask.', kinemaster: 'Cut-out from KineMaster.', recipe: 'Cut-out from the recipe.' }[M.how] || 'Cut-out ready.';
  if (st.err) return 'Automatic cut-out unavailable (needs the internet the first time). Import a mask, or export as it is: KineMaster cuts the subject out on the phone.';
  return 'No cut-out yet.';
}
function magicHtml(b) {
  const M = b.magic || {}, isV = b.type === 'video';
  return `<section class="sec" id="mrSec"><h2>Magic remover <span class="hint">KineMaster background removal</span></h2>
    <label class="tog"><input type="checkbox" id="mrOn" ${M.on ? 'checked' : ''}> Remove the background</label>
    <p class="desc" id="mrStat">${mrStatus(b)}</p>
    ${isV ? `<label class="tog"><input type="checkbox" id="mrPrev" ${M.preview !== false ? 'checked' : ''}> Cut out in the preview too (slower)</label>`
          : `<div class="row"><button class="btn sm ghost" id="mrAuto">Find subject again</button><button class="btn sm ghost" id="mrImp">Import mask&hellip;</button><button class="btn sm ghost" id="mrClr">Clear</button></div>`}
    ${rangeRow('mrBlur', 'Blur this layer', 0, 30, 1, +b.clipBlur || 0)}
    <p class="desc">KineMaster makes the final cut-out on the phone and redoes it when the ${isV ? 'clip' : 'photo'} is replaced, so the preview here is close, not identical. The blur is KineMaster's built-in Blur on this layer only. For instant depth: duplicate the layer, blur the lower copy and remove the background on the upper one.</p>
  </section>`;
}
function refreshMagic(b) { const el = document.getElementById('mrStat'); if (el && sel === b.id) el.innerHTML = mrStatus(b); }
function bindMagic(b) {
  const on = (x, ev, f) => { const el = $('#' + x); if (el) el[ev] = f; };
  on('mrOn', 'onchange', e => {
    b.magic = Object.assign({ mask: null, how: null }, b.magic || {}, { on: e.target.checked });
    if (b.magic.on && b.type === 'photo' && !b.photo.raw) {   // KineMaster cuts the picture as it is: no card, border or shadow
      Object.assign(b.photo, { raw: true, aspect: 'orig', border: 0, shadow: 0, reflect: 0 });
      toast('Magic remover uses the photo as it is, so its shape, border and shadow were turned off.', false, 3500);
    }
    lookCache.clear(); changed(b, { rerender: true }); renderInspector();
  });
  on('mrPrev', 'onchange', e => { b.magic = Object.assign({}, b.magic || {}, { preview: e.target.checked }); drawAll(); saveSoon(); });
  on('mrAuto', 'onclick', () => { if (!b.magic || !b.magic.on) return toast('Turn on "Remove the background" first.', false, 2000); b.magic.mask = null; b.magic.how = null; lookCache.clear(); autoMask(b, true); });
  on('mrClr', 'onclick', () => { if (b.magic) { b.magic.mask = null; b.magic.how = null; mrState.set(b.id, { err: b.photo.src }); } lookCache.clear(); changed(b); refreshMagic(b); });
  on('mrImp', 'onclick', () => {
    const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*';
    inp.onchange = async () => {
      const f = inp.files[0]; if (!f) return;
      try {
        const c = await blobToCanvas(f, 2048), g = c.getContext('2d'), d = g.getImageData(0, 0, c.width, c.height);
        let solid = true; for (let i = 3; i < d.data.length; i += 4 * 9) if (d.data[i] < 250) { solid = false; break; }
        if (solid) for (let i = 0; i < d.data.length; i += 4) { d.data[i + 3] = Math.round((d.data[i] + d.data[i + 1] + d.data[i + 2]) / 3); d.data[i] = d.data[i + 1] = d.data[i + 2] = 255; }   // black/white mask -> alpha
        g.putImageData(d, 0, 0);
        const id = 'mask_' + uid(); media.set(id, c); c.toBlob(bl => { if (bl) idb.put(id, bl); }, 'image/png');
        b.magic = Object.assign({}, b.magic || {}, { on: true, mask: 'up:' + id, how: 'imported', for: b.photo.src }); lookCache.clear(); changed(b); renderInspector();
      } catch (err) { toast('Could not read that mask: ' + err.message, true); }
    };
    inp.click();
  });
  const bl = $('#mrBlur'); if (bl) bindRange('mrBlur', b, v => { b.clipBlur = v; lookCache.clear(); });
}
/* duplicate = an independent layer: its own name, slot label and (photos) media id */
function dupIdentity(c) {
  const names = new Set(state.blocks.map(x => x.name)), nb = String(c.name || 'Layer').replace(/ \d+$/, '');
  let n = 2; while (names.has(nb + ' ' + n)) n++; c.name = nb + ' ' + n;
  if (c.slot && c.slot.label) { const labels = new Set(state.blocks.map(x => x.slot && x.slot.label)), lb = c.slot.label.replace(/ \d+$/, ''); let k = 2; while (labels.has(lb + ' ' + k)) k++; c.slot.label = lb + ' ' + k; }
  if (c.type === 'photo' && String(c.photo && c.photo.src).startsWith('up:')) {
    const old = c.photo.src.slice(3), cv = media.get(old);
    if (cv) {
      const nid = uid(); media.set(nid, cv); const rb = rawBytes.get(old); if (rb) rawBytes.set(nid, rb);
      idb.get(old).then(bl => { if (bl) idb.put(nid, bl); });
      if (binEntry(old)) binAdd(nid, c.name);
      c.photo.src = 'up:' + nid; if (c.magic && c.magic.for === 'up:' + old) c.magic.for = c.photo.src;
    }
  }
  return c;
}
"""
sub("const itemHtmlRefresh = b => {", ENGINE + "const itemHtmlRefresh = b => {")

# ---------------------------------------------------------------- inspector: the section on photos and clips
sub("b.type === 'video' ? videoHtml(b) + layerHtml(b) : itemHtml(b);",
    "b.type === 'video' ? videoHtml(b) + magicHtml(b) + layerHtml(b) : itemHtml(b) + (b.type === 'photo' ? magicHtml(b) : '');")
sub("else if (b.type === 'video') { bindVideo(b); bindLayerSec(b); } else bindItem(b); }",
    "else if (b.type === 'video') { bindVideo(b); bindMagic(b); bindLayerSec(b); } else { bindItem(b); if (b.type === 'photo') bindMagic(b); } }")

# ---------------------------------------------------------------- duplicates
sub("""    const c = clone(b); c.id = uid();
    if (!grab)""", """    const c = dupIdentity(clone(b)); c.id = uid();
    if (!grab)""")

# ---------------------------------------------------------------- masks travel with the recipe and the browser store
sub("  (state.mediaBin || []).forEach(m => ids.add(m.id));\n  if (ids.size) { r.studio_media = {};",
    "  (state.mediaBin || []).forEach(m => ids.add(m.id));\n  items.forEach(b => { const mk = b.magic && b.magic.mask; if (mk && String(mk).startsWith('up:')) ids.add(String(mk).slice(3)); });\n  if (ids.size) { r.studio_media = {};")
sub(".map(b => b.photo.src.slice(3)).concat((state.mediaBin || []).map(m => m.id)))].filter(id => !media.has(id));",
    ".map(b => b.photo.src.slice(3)).concat((state.mediaBin || []).map(m => m.id), state.blocks.filter(b => b.magic && b.magic.mask).map(b => String(b.magic.mask).slice(3))))].filter(id => !media.has(id));")

# ---------------------------------------------------------------- opening a .kine: Magic Remover, its mask and the clip blur come back
sub("""      blocks.push(b); continue;
    }
    skip(L.kind === 'image_layer' ? 'colour / store pictures'""",
    """      if (!b.kmFlip) {
        const mf = L.payload.find(n => n.f === 119);
        if (mf && +mf.v === 1) {
          b.magic = { on: true, mask: null, how: null };
          const mu = L.payload.find(n => n.f === 121);
          if (mu && typeof mu.v === 'string' && files.has(mu.v)) { try { const mfile = files.get(mu.v), mid = 'm' + (K.crc32(mfile.data) >>> 0).toString(36), mc = await blobToCanvas(new Blob([mfile.data], { type: 'image/png' }), 2048); media.set(mid, mc); idb.put(mid, new Blob([mfile.data], { type: 'image/png' })); b.magic.mask = 'up:' + mid; b.magic.how = 'kinemaster'; } catch (e) {} }
        }
        const cl = L.payload.find(n => n.f === 125);
        if (cl && cl.v instanceof Uint8Array) { let t = ''; cl.v.forEach(x => { t += String.fromCharCode(x); }); const m = t.includes('csd.blurall') && t.match(/f_block_size[\\s\\S]{2}([0-9.]+)/); if (m) b.clipBlur = +m[1]; }
      }
      blocks.push(b); continue;
    }
    skip(L.kind === 'image_layer' ? 'colour / store pictures'""")

sub("window.__studio = { play: d => play(d),", "window.__studio = { MR, mrLook, kmMaskBytes, dupIdentity, play: d => play(d),")
open(dst, 'w', encoding='utf-8').write(s)
print('patched', dst)
