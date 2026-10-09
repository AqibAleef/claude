"""Kinekit Studio patch 08: motion tracking (Track mode).

Trackers follow something in a video clip, frame by frame, in the browser (nothing is uploaded):
  1-point   one feature (normalised cross-correlation template matching, sub-pixel, with motion prediction)
  2-point   two features: position, rotation and scale from the line between them
  planar    a flat surface: ~24 features inside a quad, a homography fitted every frame (RANSAC + least squares),
            the four corners follow in perspective (screens, signs, posters, car doors)
  face / person / object   found automatically (MediaPipe face detector + EfficientDet object detector), then
            followed by detection + box matching; no box to draw
Attach a layer to a tracker: its motion becomes ordinary transform keys (position, or position + rotation + scale),
or, for planar trackers, KineMaster corner-pin keys that pin a photo or clip into the surface. Stabilize writes the
inverse motion onto the clip itself. Trackers live in the project (autosave and recipes); re-tracking updates every
attached layer. A tracking demo builds its own clip (no third-party media).

    python3 08_tracking.py IN.html OUT.html
"""
import sys
src, dst = sys.argv[1:3]
s = open(src, encoding='utf-8').read()


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, f'anchor found {n}x, expected {count}: {old[:100]!r}'
    s = s.replace(old, new)


CSS = r"""
/* ---------- tracking (patch 08) */
.app[data-mode=track] #ptabs { display: none; }
.trkrow { display: flex; align-items: center; gap: 8px; width: 100%; border: 1px solid transparent; background: var(--panel-2); border-radius: 6px; padding: 6px 8px; cursor: pointer; text-align: left; color: var(--text); }
.trkrow:hover { border-color: var(--line-2); }
.trkrow[aria-pressed=true] { border-color: #8be37a; background: color-mix(in srgb, #8be37a 10%, var(--panel-2)); }
.trkrow .tk { width: 22px; height: 22px; border-radius: 5px; display: grid; place-items: center; font: 700 10px var(--f-mono); background: color-mix(in srgb, #8be37a 18%, transparent); color: #8be37a; flex: none; }
.trkrow .tm { flex: 1; min-width: 0; display: grid; } .trkrow .tm span { color: var(--muted); font-size: 11.5px; }
.trkbtns { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
.trkbar { height: 6px; border-radius: 3px; background: var(--panel-3); overflow: hidden; } .trkbar i { display: block; height: 100%; background: #8be37a; width: 0; }
.trkconf { display: flex; align-items: flex-end; gap: 1px; height: 26px; } .trkconf i { flex: 1; background: #3f8f4a; min-height: 2px; } .trkconf i.lost { background: #ff5c5c; }
.trkfound { display: grid; gap: 6px; }
.btn.trk { background: #8be37a; color: #0b1a08; border-color: #8be37a; font-weight: 700; }
"""
i = s.index('/* ---------- workspace (patch 07)')
s = s[:i] + CSS + s[i:]

# Track mode button
sub('<button data-mode="animate" aria-pressed="false" title="Keys, camera and the curve editor">Animate</button>',
    '<button data-mode="animate" aria-pressed="false" title="Keys, camera and the curve editor">Animate</button><button data-mode="track" aria-pressed="false" title="Motion tracking: follow something in a clip">Track</button>')
# the Track panel replaces the properties in Track mode
sub("""  const H = $('#ihead'), P = $('#pbody'), b = activeBlock();
  cancelAnimationFrame(pvAnim);""", """  const H = $('#ihead'), P = $('#pbody'), b = activeBlock();
  cancelAnimationFrame(pvAnim);
  if (wsMode === 'track') { renderTrackPanel(H, P); return; }""")
# mode switching knows Track
sub("""    if (m === 'animate' && !tlUi.graph) run('graph');
    if (m === 'edit' && tlUi.graph) run('graph');""", """    if (m === 'animate' && !tlUi.graph) run('graph');
    if ((m === 'edit' || m === 'track') && tlUi.graph) run('graph');
    if (m === 'track') { const v = trackClip(); if (v) { if (!S.ids.has(v.id)) selectLayers([v.id]); trkClipId = v.id; } }""")
sub("function openProjectSettings() { if (wsMode === 'export') return;", "function openProjectSettings() { if (wsMode === 'export') return; if (wsMode === 'track') setMode('edit');")
sub("const L = [['edit', 'Edit'], ['animate', 'Animate'], ['export', 'Export']].map(", "const L = [['edit', 'Edit'], ['animate', 'Animate'], ['track', 'Track'], ['export', 'Export']].map(")
# overlay + viewport interaction in Track mode
sub("    if (viewMode !== '3d') drawStage();\n    drawTimeline();", "    if (viewMode !== '3d') { drawStage(); if (wsMode === 'track') drawTrackOverlay(); }\n    drawTimeline();")
# planar trackers pin layers: after the perspective pins
sub("    perspPins(r);\n    fitCurvesLayers(r);", "    perspPins(r);\n    trackPins(b, r);\n    fitCurvesLayers(r);")
# trackers travel with recipes
sub("function projectExtrasOut() { const o = { kmFormat:", "function projectExtrasOut() { const o = { trackers: state.trackers || [], kmFormat:")
sub("function projectExtrasIn(o) { if (!o) return;", "function projectExtrasIn(o) { if (!o) return; if (Array.isArray(o.trackers)) state.trackers = o.trackers;")
# clips without a duration in their header (browser-recorded WebM): find the real length before using it
sub("""  await new Promise((res, rej) => { el.onloadeddata = res; el.onerror = () => rej(new Error('This video can\\'t be played in the browser.')); });
  const v = { el, w: el.videoWidth, h: el.videoHeight, dur: el.duration, name, url };""", """  await new Promise((res, rej) => { el.onloadeddata = res; el.onerror = () => rej(new Error('This video can\\'t be played in the browser.')); });
  if (!Number.isFinite(el.duration)) { await new Promise(res => { const done = () => { if (Number.isFinite(el.duration)) { el.removeEventListener('durationchange', done); res(); } }; el.addEventListener('durationchange', done); el.currentTime = 1e7; setTimeout(res, 3000); }); el.currentTime = 0; await new Promise(res => { el.addEventListener('seeked', res, { once: true }); setTimeout(res, 1000); }); }
  const v = { el, w: el.videoWidth, h: el.videoHeight, dur: Number.isFinite(el.duration) ? el.duration : 5, name, url };""")
sub("  state.title = d.name; bindProject(); setMode('edit'); saveSoon();", "  state.title = d.name; bindProject(); setMode(d.mode || 'edit'); saveSoon();")
# a photo pinned by a planar tracker exports its corner pins (clips already pass theirs)
sub("kfs: L.kfs, mirror: L.flip123 ? 'f123' : m, clipFx: L.clipFx || null, alpha: L.flip123 ? lk.opacity : null, magic:",
    "kfs: L.kfs, mirror: L.flip123 ? 'f123' : m, clipFx: L.clipFx || null, pins: L.trkPin ? L.pins : null, alpha: L.flip123 || L.trkPin ? lk.opacity : null, magic:")
# demo
sub("  { id: 'magic', name: 'Depth with Magic Remover',", "  { id: 'track', name: 'Tracking Playground', feat: 'Motion tracking', tags: 'A point, a moving poster in perspective · makes its own clip', cat: 'New', isNew: true, aspect: '9:16', mode: 'track', load: demoTrack },\n  { id: 'magic', name: 'Depth with Magic Remover',")
sub("window.__studio = { openDemo:", "window.__studio = { TRK: { trackClip, newTracker, runTrack, attachLayer, stabilize, findSubjects, trackFromDetection, trackerList: () => state.trackers || [], clipPtToStage }, openDemo:")

JS = r"""
// ================================================================== motion tracking (patch 08)
/* tracker = { id, name, clip, kind: point | two | planar | face, init: { t, pts: [[u, v]...], box? },
   patch, search, smooth, samples: [{ t, pts, box?, conf }] }   (t = seconds in the clip's source, u / v = 0..1 of the frame) */
const TRK_KINDS = { point: '1-point', two: '2-point', planar: 'Planar', face: 'Subject' };
let trkSel = null, trkClipId = null, trkBusy = false, trkCancel = false, trkProg = 0, trkFound = [], trkDrag = null;
const trackers = () => (state.trackers = state.trackers || []);
const trkById = id => trackers().find(t => t.id === id);
const blkById = id => state.blocks.find(b => b.id === id);
const vidIdOf = b => String(b.video && b.video.src || '').slice(4);
function trackClip() { const a = activeBlock(); if (a && a.type === 'video') return a; const c = trkClipId && blkById(trkClipId); if (c) return c; return state.blocks.find(b => b.type === 'video') || null; }
const srcToProj = (clip, src) => clip.start + (src - (+clip.video.trimIn || 0)) / (+clip.video.speed || 1);
const srcRange = clip => { const a = +clip.video.trimIn || 0; return [a, a + (clip.end - clip.start) * (+clip.video.speed || 1)]; };
function clipLayer(clip) { const r = baked.get(clip.id); return r && r.layers.find(x => x.vid); }
/* clip frame (u, v) -> stage, through the clip layer's own placement at project time Tp (or a fixed pose) */
function clipPtToStage(clip, u, v, Tp, pose) {
  let k, w, h;
  if (pose) { k = pose; [w, h] = pose.wh; } else { const L = clipLayer(clip); if (!L) return null; k = at(L, clamp(Tp, L.start, L.end - 1e-4)); if (!k) return null; [w, h] = layerSize(L); }
  const x = (u - 0.5) * w * k.sx, y = (v - 0.5) * h * k.sy, a = (k.rot || 0) * D2R;
  return [k.x + x * Math.cos(a) - y * Math.sin(a), k.y + x * Math.sin(a) + y * Math.cos(a)];
}
function stageToClip(clip, X, Y, Tp) {
  const L = clipLayer(clip); if (!L) return null; const k = at(L, clamp(Tp, L.start, L.end - 1e-4)); if (!k) return null; const [w, h] = layerSize(L);
  const a = -(k.rot || 0) * D2R, dx = X - k.x, dy = Y - k.y, x = dx * Math.cos(a) - dy * Math.sin(a), y = dx * Math.sin(a) + dy * Math.cos(a);
  return [x / (w * k.sx) + 0.5, y / (h * k.sy) + 0.5];
}
/* the tracker's points at a source time: nearest samples, interpolated; before tracking, its start position */
function trkPtsAt(tr, t) {
  const S = trkSmooth(tr); if (!S.length) return tr.init ? { pts: tr.init.pts, box: tr.init.box, conf: 1, raw: true } : null;
  if (t <= S[0].t) return S[0]; if (t >= S[S.length - 1].t) return S[S.length - 1];
  let i = 0; while (i + 1 < S.length && S[i + 1].t <= t) i++; const a = S[i], c = S[i + 1], f = (t - a.t) / Math.max(1e-6, c.t - a.t);
  const mix = (p, q) => p.map((v, j) => [v[0] + (q[j][0] - v[0]) * f, v[1] + (q[j][1] - v[1]) * f]);
  return { pts: mix(a.pts, c.pts), box: a.box && c.box ? { w: a.box.w + (c.box.w - a.box.w) * f, h: a.box.h + (c.box.h - a.box.h) * f } : a.box, conf: Math.min(a.conf, c.conf) };
}
const trkCache = new WeakMap();
function trkSmooth(tr) {
  const S = tr.samples || []; const key = S.length + ':' + (tr.smooth || 0) + ':' + (tr.rev || 0); const c = trkCache.get(tr); if (c && c.key === key) return c.out;
  const k = Math.round((+tr.smooth || 0) * 6); let out = S;
  if (k > 0 && S.length > 2) out = S.map((s, i) => { let n = 0; const acc = s.pts.map(() => [0, 0]); let bw = 0, bh = 0;
    for (let j = Math.max(0, i - k); j <= Math.min(S.length - 1, i + k); j++) { if (S[j].conf < 0.35 && j !== i) continue; n++; S[j].pts.forEach((p, m) => { acc[m][0] += p[0]; acc[m][1] += p[1]; }); if (S[j].box) { bw += S[j].box.w; bh += S[j].box.h; } }
    return Object.assign({}, s, { pts: acc.map(p => [p[0] / n, p[1] / n]), box: s.box ? { w: bw / n, h: bh / n } : null }); });
  trkCache.set(tr, { key, out }); return out;
}

// ---------------------------------------------------------------- frames
async function trkVideo(clip) {
  const v = vids.get(vidIdOf(clip)); if (!v) throw new Error('The clip is not loaded in this browser. Import it again.');
  if (v.trkEl) return v.trkEl;
  const el = document.createElement('video'); el.muted = true; el.preload = 'auto'; el.playsInline = true; el.src = v.url;
  await new Promise((res, rej) => { el.onloadeddata = res; el.onerror = () => rej(new Error('The clip could not be decoded for tracking.')); });
  v.trkEl = el; return el;
}
async function trkGrab(el, t, maxDim = 480) {
  const s = Math.min(1, maxDim / Math.max(el.videoWidth, el.videoHeight)), W = Math.max(2, Math.round(el.videoWidth * s)), H = Math.max(2, Math.round(el.videoHeight * s));
  if (Math.abs(el.currentTime - t) > 1e-3) await new Promise(res => { const done = () => { el.removeEventListener('seeked', done); res(); }; el.addEventListener('seeked', done); el.currentTime = t; setTimeout(done, 1500); });
  const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(el, 0, 0, W, H);
  const d = g.getImageData(0, 0, W, H).data, gray = new Float32Array(W * H);
  for (let i = 0, j = 0; j < gray.length; i += 4, j++) gray[j] = 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
  return { W, H, gray, canvas: c };
}

// ---------------------------------------------------------------- point tracking: normalised cross-correlation
function trkPatch(F, x, y, r) {
  const n = 2 * r + 1, p = new Float32Array(n * n); let m = 0;
  for (let j = -r, q = 0; j <= r; j++) for (let i = -r; i <= r; i++, q++) { const xx = clamp(Math.round(x) + i, 0, F.W - 1), yy = clamp(Math.round(y) + j, 0, F.H - 1); p[q] = F.gray[yy * F.W + xx]; m += p[q]; }
  m /= p.length; let v = 0; for (let q = 0; q < p.length; q++) { p[q] -= m; v += p[q] * p[q]; } p.sd = Math.sqrt(v) || 1; return p;
}
function trkNcc(F, tpl, r, cx, cy) {
  const n = 2 * r + 1; let m = 0, v = 0, c = 0; const x0 = cx - r, y0 = cy - r;
  if (x0 < 0 || y0 < 0 || x0 + n > F.W || y0 + n > F.H) return -1;
  for (let j = 0, q = 0; j < n; j++) { const row = (y0 + j) * F.W + x0; for (let i = 0; i < n; i++, q++) { const a = F.gray[row + i]; m += a; v += a * a; c += a * tpl[q]; } }
  const N = n * n, sd = Math.sqrt(Math.max(1e-6, v - m * m / N)); return c / (sd * tpl.sd);
}
function trkMatch(F, tpl, r, px, py, sr) {
  let best = -2, bx = px, by = py; const ix = Math.round(px), iy = Math.round(py), sc = {};
  for (let dy = -sr; dy <= sr; dy++) for (let dx = -sr; dx <= sr; dx++) { const v = trkNcc(F, tpl, r, ix + dx, iy + dy); sc[dx + ',' + dy] = v; if (v > best) { best = v; bx = ix + dx; by = iy + dy; } }
  const g = (dx, dy) => sc[(bx - ix + dx) + ',' + (by - iy + dy)];
  const fx = (a, b, c) => (a === undefined || c === undefined) ? 0 : clamp((a - c) / (2 * (a - 2 * b + c) || 1e-9), -0.5, 0.5);
  return { x: bx + fx(g(-1, 0), best, g(1, 0)), y: by + fx(g(0, -1), best, g(0, 1)), score: best };
}
function trkVar(F, x, y, r) { const p = trkPatch(F, x, y, r); return p.sd / (2 * r + 1); }

// ---------------------------------------------------------------- planar: homography from many features
function homLS(src, dst) {
  const M = Array.from({ length: 8 }, () => new Float64Array(9));
  for (let i = 0; i < src.length; i++) {
    const [x, y] = src[i], [u, v] = dst[i], rows = [[x, y, 1, 0, 0, 0, -u * x, -u * y, u], [0, 0, 0, x, y, 1, -v * x, -v * y, v]];
    for (const r of rows) for (let a = 0; a < 8; a++) { for (let b = 0; b < 8; b++) M[a][b] += r[a] * r[b]; M[a][8] += r[a] * r[8]; }
  }
  for (let c = 0; c < 8; c++) { let p = c; for (let r = c + 1; r < 8; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r; if (Math.abs(M[p][c]) < 1e-12) return null; [M[c], M[p]] = [M[p], M[c]];
    for (let r = 0; r < 8; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let k = c; k < 9; k++) M[r][k] -= f * M[c][k]; } }
  const h = M.map((r, i) => r[8] / r[i]); return (x, y) => { const d = h[6] * x + h[7] * y + 1; return [(h[0] * x + h[1] * y + h[2]) / d, (h[3] * x + h[4] * y + h[5]) / d]; };
}
function homRansac(src, dst) {
  const n = src.length; if (n < 4) return null; let best = null, bestIn = [];
  for (let it = 0; it < 70; it++) {
    const ids = new Set(); while (ids.size < 4) ids.add(Math.floor(Math.random() * n)); const I = [...ids];
    const H = homLS(I.map(i => src[i]), I.map(i => dst[i])); if (!H) continue;
    const inl = []; for (let i = 0; i < n; i++) { const [x, y] = H(src[i][0], src[i][1]); if (Math.hypot(x - dst[i][0], y - dst[i][1]) < 2.5) inl.push(i); }
    if (inl.length > bestIn.length) { bestIn = inl; best = H; }
  }
  if (bestIn.length >= 4) { const H = homLS(bestIn.map(i => src[i]), bestIn.map(i => dst[i])); return { H: H || best, inliers: bestIn }; }
  return best ? { H: best, inliers: bestIn } : null;
}
const inQuad = (q, x, y) => { let s = 0; for (let i = 0; i < 4; i++) { const [ax, ay] = q[i], [bx, by] = q[(i + 1) % 4]; const c = (bx - ax) * (y - ay) - (by - ay) * (x - ax); if (c === 0) continue; if (s === 0) s = Math.sign(c); else if (Math.sign(c) !== s) return false; } return true; };

// ---------------------------------------------------------------- subjects: faces, people, objects (MediaPipe)
const DET = (() => {
  let ready = null;
  const base = () => window.KK_MR_BASE || 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14';
  const models = () => window.KK_MR_MODELS || 'https://storage.googleapis.com/mediapipe-models';
  const load = () => ready || (ready = (async () => {
    const V = await import(base() + '/vision_bundle.mjs'); const fs = await V.FilesetResolver.forVisionTasks(base() + '/wasm');
    const face = await V.FaceDetector.createFromOptions(fs, { baseOptions: { modelAssetPath: models() + '/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite' }, runningMode: 'IMAGE', minDetectionConfidence: 0.5 });
    const obj = await V.ObjectDetector.createFromOptions(fs, { baseOptions: { modelAssetPath: models() + '/object_detector/efficientdet_lite0/int8/1/efficientdet_lite0.tflite' }, runningMode: 'IMAGE', scoreThreshold: 0.35, maxResults: 8 });
    return { face, obj };
  })().catch(e => { ready = null; throw e; }));
  async function detect(canvas, only) {
    const { face, obj } = await load(), W = canvas.width, H = canvas.height, out = [];
    if (!only || only === 'face') for (const d of face.detect(canvas).detections || []) { const b = d.boundingBox; out.push({ cat: 'face', score: d.categories && d.categories[0] ? d.categories[0].score : 0.9, box: { u: (b.originX + b.width / 2) / W, v: (b.originY + b.height / 2) / H, w: b.width / W, h: b.height / H } }); }
    if (only !== 'face') for (const d of obj.detect(canvas).detections || []) { const c = d.categories[0]; if (only && c.categoryName !== only) continue; const b = d.boundingBox; out.push({ cat: c.categoryName, score: c.score, box: { u: (b.originX + b.width / 2) / W, v: (b.originY + b.height / 2) / H, w: b.width / W, h: b.height / H } }); }
    return out.sort((a, b) => b.score - a.score);
  }
  return { load, detect };
})();
const iou = (a, b) => { const ax0 = a.u - a.w / 2, ax1 = a.u + a.w / 2, ay0 = a.v - a.h / 2, ay1 = a.v + a.h / 2, bx0 = b.u - b.w / 2, bx1 = b.u + b.w / 2, by0 = b.v - b.h / 2, by1 = b.v + b.h / 2;
  const iw = Math.max(0, Math.min(ax1, bx1) - Math.max(ax0, bx0)), ih = Math.max(0, Math.min(ay1, by1) - Math.max(ay0, by0)), I = iw * ih; return I / (a.w * a.h + b.w * b.h - I || 1); };

// ---------------------------------------------------------------- trackers
function newTracker(kind, clip, opts = {}) {
  clip = clip || trackClip(); if (!clip) { toast('Add a video clip first: Track mode follows something in a clip.', true); return null; }
  const t = clamp(clipTime(clip, T), ...srcRange(clip)), n = trackers().filter(x => x.clip === clip.id).length + 1;
  const init = kind === 'point' ? [[0.5, 0.5]] : kind === 'two' ? [[0.4, 0.5], [0.6, 0.5]] : kind === 'planar' ? [[0.32, 0.38], [0.68, 0.38], [0.68, 0.62], [0.32, 0.62]] : [[0.5, 0.5]];
  const tr = Object.assign({ id: 'trk' + uid(), name: `Tracker ${n} · ${TRK_KINDS[kind]}`, clip: clip.id, kind, init: { t, pts: init, box: null }, patch: 0.07, search: 0.12, smooth: 0.3, samples: [], rev: 0 }, opts);
  trackers().push(tr); trkSel = tr.id; trkClipId = clip.id; saveSoon(); renderProps(); drawAll(); return tr;
}
function trkStartPts(tr, t) {   // where to start: an existing sample at this frame, else the start position
  const S = tr.samples || []; let best = null; for (const s of S) if (Math.abs(s.t - t) < 0.5 / 30 && (!best || Math.abs(s.t - t) < Math.abs(best.t - t))) best = s;
  return best ? { pts: best.pts.map(p => p.slice()), box: best.box } : { pts: tr.init.pts.map(p => p.slice()), box: tr.init.box };
}
async function runTrack(tr, dir = 1, whole = false) {
  if (whole === true) { await runTrack(tr, 1, 't0'); if (!trkCancel) await runTrack(tr, -1, 't0'); return; }
  if (trkBusy) return; const clip = blkById(tr.clip); if (!clip) return toast('This tracker\'s clip was deleted.', true);
  trkBusy = true; trkCancel = false; trkProg = 0; renderProps();
  try {
    const el = await trkVideo(clip), [a, b] = srcRange(clip), fps = 30, dur = el.duration || b;
    const lo = Math.max(0, a), hi = Math.min(b, dur - 0.02);
    let t = whole === 't0' ? clamp(tr.init.t, lo, hi) : clamp(clipTime(clip, T), lo, hi); const end = dir > 0 ? hi : lo, total = Math.max(1, Math.round(Math.abs(end - t) * fps));
    const st = trkStartPts(tr, t); let pts = st.pts, box = st.box;
    const isFace = tr.kind === 'face', maxDim = isFace ? 640 : 480;
    let F = await trkGrab(el, t, maxDim), W = F.W, H = F.H, out = [{ t: +t.toFixed(4), pts: pts.map(p => p.slice()), box, conf: 1 }];
    const R = Math.max(4, Math.round(tr.patch * Math.min(W, H) / 2)), SR = Math.max(6, Math.round(tr.search * Math.min(W, H) / 2));
    let feats = null, ref = null, vel = pts.map(() => [0, 0]);
    if (tr.kind === 'planar') {   // features inside the quad, the most textured cells of a grid
      const q = pts.map(([u, v]) => [u * W, v * H]), cand = [];
      const xs = q.map(p => p[0]), ys = q.map(p => p[1]), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys), fr = Math.max(4, Math.round(R * 0.7));
      for (let gy = 0; gy < 11; gy++) for (let gx = 0; gx < 11; gx++) { const x = x0 + (gx + 0.5) / 11 * (x1 - x0), y = y0 + (gy + 0.5) / 11 * (y1 - y0); if (inQuad(q, x, y)) cand.push([x, y, trkVar(F, x, y, fr)]); }
      cand.sort((p, q2) => q2[2] - p[2]); feats = cand.slice(0, 36).map(([x, y]) => ({ x, y, x0: x, y0: y, tpl: trkPatch(F, x, y, fr), r: fr, ok: true }));
      ref = { q, featsSrc: feats.map(f => [f.x0, f.y0]) };
      if (feats.length < 6) throw new Error('The surface has too little detail to follow. Put the corners round something with texture or text.');
    }
    let tpls = tr.kind === 'face' ? null : pts.map(([u, v]) => trkPatch(F, u * W, v * H, R)), tpls0 = tpls && tpls.slice();
    for (let i = 0; i < total && !trkCancel; i++) {
      t = +(t + dir / fps).toFixed(4); if ((dir > 0 && t > end + 1e-6) || (dir < 0 && t < end - 1e-6)) break;
      const G = await trkGrab(el, t, maxDim); let conf = 1;
      if (tr.kind === 'point' || tr.kind === 'two') {
        pts = pts.map(([u, v], j) => {
          const px = u * W + vel[j][0], py = v * H + vel[j][1], m = trkMatch(G, tpls[j], R, px, py, SR);
          let x = m.x, y = m.y;
          if (m.score < 0.55) { const m0 = trkMatch(G, tpls0[j], R, px, py, SR + 4); if (m0.score > m.score) { x = m0.x; y = m0.y; m.score = m0.score; } }
          if (m.score < 0.45) { x = px; y = py; } conf = Math.min(conf, Math.max(0, m.score));
          vel[j] = [(x - u * W) * 0.7, (y - v * H) * 0.7];
          if (m.score > 0.7) { const nt = trkPatch(G, x, y, R), o = tpls[j]; for (let q = 0; q < o.length; q++) nt[q] = 0.6 * nt[q] + 0.4 * o[q]; let vv = 0; for (const z of nt) vv += z * z; nt.sd = Math.sqrt(vv) || 1; tpls[j] = nt; }
          return [x / W, y / H];
        });
      } else if (tr.kind === 'planar') {
        const src = [], dst = [];
        for (const f of feats) { const m = trkMatch(G, f.tpl, f.r, f.x, f.y, SR); f.score = m.score; if (m.score > 0.6) { f.x = m.x; f.y = m.y; src.push([f.x0, f.y0]); dst.push([f.x, f.y]); } }
        const hr = homRansac(src, dst);
        if (hr && hr.inliers.length >= 6) {
          const Hm = hr.H; pts = ref.q.map(([x, y]) => { const [X, Y] = Hm(x, y); return [X / W, Y / H]; });
          for (const f of feats) { const [X, Y] = Hm(f.x0, f.y0); if (!(f.score > 0.6) || Math.hypot(X - f.x, Y - f.y) > 3) { f.x = X; f.y = Y; }   // pull drifting features back onto the plane
            else if (f.score > 0.8) { const nt = trkPatch(G, f.x, f.y, f.r), o = f.tpl; let vv = 0; for (let q = 0; q < o.length; q++) { nt[q] = 0.5 * nt[q] + 0.5 * o[q]; vv += nt[q] * nt[q]; } nt.sd = Math.sqrt(vv) || 1; f.tpl = nt; } }   // follow slow changes of scale and light
          conf = hr.inliers.length / feats.length;
        } else conf = 0;
      } else {   // subject: detect, keep the box that overlaps the last one most
        const cat = tr.subject || 'face', dets = await DET.detect(G.canvas, cat === 'face' ? 'face' : cat);
        const last = { u: pts[0][0], v: pts[0][1], w: box.w, h: box.h }; let best = null, bs = 0.05;
        for (const d of dets) { const r = d.box.h / Math.max(1e-6, last.h); if (r > 1.8 || r < 1 / 1.8) continue;   // a sudden size jump is another subject (or a cut)
          const s = iou(last, d.box) + 0.3 * (1 - Math.min(1, Math.hypot(d.box.u - last.u, d.box.v - last.v) * 4)); if (s > bs) { bs = s; best = d; } }
        if (best) { pts = [[best.box.u, best.box.v]]; box = { w: best.box.w, h: best.box.h }; conf = best.score; } else conf = 0;
      }
      out.push({ t, pts: pts.map(p => p.slice()), box: box ? { w: box.w, h: box.h } : null, conf: +conf.toFixed(3) });
      trkProg = (i + 1) / total; if (i % 4 === 0) { const bar = document.getElementById('trkBarI'); if (bar) bar.style.width = (trkProg * 100).toFixed(1) + '%'; setTime(srcToProj(clip, t)); }
    }
    const lo2 = Math.min(...out.map(s => s.t)), hi2 = Math.max(...out.map(s => s.t));
    tr.samples = (tr.samples || []).filter(s => s.t < lo2 - 1e-4 || s.t > hi2 + 1e-4).concat(out).sort((p, q) => p.t - q.t); tr.rev = (tr.rev || 0) + 1;
    applyFollowers(tr); saveSoon();
    const lost = out.filter(s => s.conf < 0.35).length;
    toast(trkCancel ? 'Tracking stopped.' : `Tracked ${out.length} frames${lost ? `, ${lost} uncertain (red in the graph): drag the tracker there and track again` : ''}.`, false, 3500);
  } catch (e) { console.error(e); toast('Tracking failed: ' + (e.message || e), true, 6000); }
  finally { trkBusy = false; renderProps(); drawAll(); }
}
async function findSubjects() {
  const clip = trackClip(); if (!clip) return [];
  try { const el = await trkVideo(clip), G = await trkGrab(el, clamp(clipTime(clip, T), ...srcRange(clip)), 640); trkFound = (await DET.detect(G.canvas)).slice(0, 8); }
  catch (e) { trkFound = []; toast('Automatic detection needs the internet the first time (it loads two small models). ' + (e.message || ''), true, 6000); }
  renderProps(); drawAll(); return trkFound;
}
async function trackFromDetection(i) {
  const d = trkFound[i], clip = trackClip(); if (!d || !clip) return null;
  const label = d.cat === 'face' ? 'Face' : d.cat[0].toUpperCase() + d.cat.slice(1);
  const tr = newTracker('face', clip, { name: `${label} ${trackers().filter(x => x.kind === 'face').length + 1}`, subject: d.cat, smooth: 0.4 });
  tr.init = { t: clamp(clipTime(clip, T), ...srcRange(clip)), pts: [[d.box.u, d.box.v]], box: { w: d.box.w, h: d.box.h } }; trkFound = [];
  const T0 = T; await runTrack(tr, 1, false); setTime(T0); if (clipTime(clip, T0) > srcRange(clip)[0] + 0.05) await runTrack(tr, -1, false); setTime(T0);
  return tr;
}

// ---------------------------------------------------------------- attach: tracked motion -> ordinary keys / corner pins
/* the tracker's anchor at a project time: position (stage), angle and scale relative to a reference */
function trkPose(tr, clip, Tp, pose) {
  const P = trkPtsAt(tr, clipTime(clip, Tp)); if (!P) return null;
  const st = P.pts.map(([u, v]) => clipPtToStage(clip, u, v, Tp, pose)); if (st.some(p => !p)) return null;
  if (tr.kind === 'two') { const [a, b] = st; return { x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2, ang: Math.atan2(b[1] - a[1], b[0] - a[0]) / D2R, len: Math.hypot(b[0] - a[0], b[1] - a[1]), conf: P.conf }; }
  if (tr.kind === 'planar') { const x = st.reduce((s, p) => s + p[0], 0) / 4, y = st.reduce((s, p) => s + p[1], 0) / 4; return { x, y, ang: Math.atan2(st[1][1] - st[0][1], st[1][0] - st[0][0]) / D2R, len: Math.hypot(st[1][0] - st[0][0], st[1][1] - st[0][1]), quad: st, conf: P.conf }; }
  if (tr.kind === 'face') { const L = clipLayer(clip), k = L && at(L, clamp(Tp, L.start, L.end - 1e-4)), h = L ? layerSize(L)[1] * Math.abs(k.sy) : 1; return { x: st[0][0], y: st[0][1], ang: 0, len: P.box ? P.box.h * h : 1, conf: P.conf }; }
  return { x: st[0][0], y: st[0][1], ang: 0, len: 1, conf: P.conf };
}
function attachLayer(b, tr, mode) {
  const clip = blkById(tr.clip); if (!b || !clip) return;
  if (mode === 'pin' && !(b.type === 'photo' || b.type === 'video')) return toast('Corner pin works on photos and clips.', true);
  if (!(tr.samples || []).length) return toast('Track first, then attach.', true);
  if (b.xo) bakeOffset(b);   // fold a re-transform offset into the keys first
  const T0 = clamp(T, clip.start, clip.end - 1e-3), p0 = trkPose(tr, clip, T0), x0 = xformAt(b, T0);
  b.follow = { tracker: tr.id, mode, T0, ref: { ax: p0.x, ay: p0.y, ang: p0.ang, len: p0.len, bx: x0.x, by: x0.y, rot: x0.rot || 0, s: x0.s || 1 }, prevTk: hasTk(b) ? clone(b.tk) : null };
  applyFollow(b); toast(mode === 'pin' ? `"${itemLabel(b)}" is pinned into the surface.` : `"${itemLabel(b)}" follows ${tr.name}.`, false, 2500);
}
function detachLayer(b) { if (!b.follow) return; const p = b.follow.prevTk; delete b.follow; b.tk = p || []; changed(b, { rerender: true }); renderProps(); }
function applyFollow(b) {
  const f = b.follow; if (!f) return; const tr = trkById(f.tracker), clip = tr && blkById(tr.clip); if (!tr || !clip) return;
  if (f.mode === 'pin') { markDirty(b); bake(b); drawAll(); saveSoon(); return; }
  const S = trkSmooth(tr), keys = [], r = f.ref, depth = +b.depth || 0;
  for (const s of S) {
    const Tp = srcToProj(clip, s.t); if (Tp < b.start - 1e-4 || Tp > b.end + 1e-4) continue;
    const p = trkPose(tr, clip, Tp); if (!p) continue;
    let ox = r.bx - r.ax, oy = r.by - r.ay, rot = r.rot, sc = r.s;
    if (f.mode === 'prs' || f.mode === 'ps') {
      const ds = r.len > 1e-6 ? p.len / r.len : 1, da = f.mode === 'prs' ? (p.ang - r.ang) * D2R : 0, c = Math.cos(da), sn = Math.sin(da);
      const nx = (ox * c - oy * sn) * ds, ny = (ox * sn + oy * c) * ds; ox = nx; oy = ny; sc = r.s * ds; if (f.mode === 'prs') rot = r.rot + (p.ang - r.ang);
    }
    keys.push({ t: +Tp.toFixed(4), ease: 'linear', x: +(p.x + ox).toFixed(2), y: +(p.y + oy).toFixed(2), depth, rot: +rot.toFixed(3), s: +sc.toFixed(5), rx: 0, ry: 0 });
  }
  if (keys.length) { b.tk = keys; changed(b); }
}
function applyFollowers(tr) {
  for (const b of state.blocks) if (b.follow && b.follow.tracker === tr.id) applyFollow(b);
  const clip = blkById(tr.clip); if (clip && clip.stab && clip.stab.tracker === tr.id) stabilize(clip, tr, clip.stab.zoom);
}
/* planar: replace the layer's keys with corner pins that follow the tracked quad (KineMaster 8 corner pin) */
function trackPins(b, r) {
  const f = b.follow; if (!f || f.mode !== 'pin') return; const tr = trkById(f.tracker), clip = tr && blkById(tr.clip); if (!tr || !clip || !(tr.samples || []).length || tr.kind !== 'planar') return;
  const S = trkSmooth(tr), sl = pinSlots();
  for (const L of r.layers) {
    if (L.kind !== 'image' || L.role !== 'item' || L.flip123 || L.mirrorY) continue;
    const [w, h] = layerSize(L), kfs = [], pins = [], span = Math.max(L.end - L.start, 1e-6);
    for (const s of S) {
      const Tp = srcToProj(clip, s.t); if (Tp < L.start - 1e-4 || Tp > L.end + 1e-4) continue;
      const Q = s.pts.map(([u, v]) => clipPtToStage(clip, u, v, Tp)); if (Q.some(q => !q)) continue;
      const cx = Q.reduce((a, q) => a + q[0], 0) / 4, cy = Q.reduce((a, q) => a + q[1], 0) / 4, u = clamp((Tp - L.start) / span, 0, 1), k0 = at(L, Tp) || {};
      kfs.push(Object.assign({}, k0, { t: u, x: cx, y: cy, rot: 0, sx: 1, sy: 1 }));
      const c = new Array(8); for (let j = 0; j < 4; j++) { const i = sl[j]; c[2 * j] = Q[i][0] - cx - LOGICAL[i][0] * w / 2; c[2 * j + 1] = Q[i][1] - cy - LOGICAL[i][1] * h / 2; }
      pins.push({ t: u, c });
    }
    if (kfs.length >= 2) { L.kfs = kfs; L.pins = pins; L.trkPin = true; }
  }
}
/* stabilize: the inverse of the tracked motion, written onto the clip itself (with a zoom that hides the edges) */
function stabilize(clip, tr, zoom = 1.1) {
  if (!(tr.samples || []).length) return toast('Track first, then stabilize.', true);
  const prev = clip.stab ? clip.stab.prevTk : (hasTk(clip) ? clone(clip.tk) : null);
  clip.tk = prev ? clone(prev) : []; bake(clip);
  const L = clipLayer(clip); if (!L) return; const T0 = clamp(T, clip.start, clip.end - 1e-3), k0 = at(L, T0), pose = Object.assign({}, k0, { wh: layerSize(L) });
  const P0 = trkPose(tr, clip, T0, pose), x0 = xformAt(clip, T0), keys = [], S = trkSmooth(tr);
  for (const s of S) {
    const Tp = srcToProj(clip, s.t); if (Tp < clip.start - 1e-4 || Tp > clip.end + 1e-4) continue; const p = trkPose(tr, clip, Tp, pose); if (!p) continue;
    const da = tr.kind === 'two' ? (p.ang - P0.ang) : 0, ds = tr.kind === 'two' && P0.len > 1e-6 ? p.len / P0.len : 1;
    keys.push({ t: +Tp.toFixed(4), ease: 'linear', x: +(x0.x + (P0.x - p.x) * zoom).toFixed(2), y: +(x0.y + (P0.y - p.y) * zoom).toFixed(2), depth: +clip.depth || 0, rot: +((x0.rot || 0) - da).toFixed(3), s: +((x0.s || 1) * zoom / ds).toFixed(5), rx: 0, ry: 0 });
  }
  clip.stab = { tracker: tr.id, zoom, prevTk: prev }; clip.tk = keys; changed(clip, { rerender: true }); renderProps(); saveSoon();
}
function unstabilize(clip) { if (!clip.stab) return; clip.tk = clip.stab.prevTk || []; delete clip.stab; changed(clip, { rerender: true }); renderProps(); }

// ---------------------------------------------------------------- the viewport overlay + dragging trackers
function trkScreenPts(tr, clip) { const P = trkPtsAt(tr, clipTime(clip, T)); if (!P) return null; return { pts: P.pts.map(([u, v]) => clipPtToStage(clip, u, v, T)), box: P.box, conf: P.conf }; }
function drawTrackOverlay() {
  const clip = trackClip(); if (!clip || T < clip.start || T >= clip.end) return;
  ctx.save(); ctx.setTransform(R, 0, 0, R, 0, 0); ctx.lineWidth = 1.6 / R;
  const L = clipLayer(clip), [lw, lh] = L ? layerSize(L) : [1, 1], k = L ? at(L, clamp(T, L.start, L.end - 1e-4)) : null, pxU = k ? lw * Math.abs(k.sx) : 1, pxV = k ? lh * Math.abs(k.sy) : 1;
  for (const tr of trackers().filter(x => x.clip === clip.id)) {
    const on = tr.id === trkSel, sp = trkScreenPts(tr, clip); if (!sp) continue; const col = sp.conf < 0.35 ? '#ff5c5c' : on ? '#8be37a' : 'rgba(139,227,122,.55)';
    ctx.strokeStyle = col; ctx.fillStyle = col;
    if (on && (tr.samples || []).length) {   // path of the first point
      ctx.globalAlpha = 0.5; ctx.beginPath(); trkSmooth(tr).forEach((s, i) => { const Tp = srcToProj(clip, s.t); if (Math.abs(Tp - T) > 1.5) return; const q = clipPtToStage(clip, s.pts[0][0], s.pts[0][1], Tp); if (!q) return; i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.stroke(); ctx.globalAlpha = 1;
    }
    if (tr.kind === 'planar') {
      ctx.beginPath(); sp.pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.stroke();
      ctx.globalAlpha = 0.25; for (let g = 1; g < 3; g++) { const f = g / 3, a = sp.pts; const lerp = (p, q, t) => [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t];
        let p1 = lerp(a[0], a[1], f), p2 = lerp(a[3], a[2], f); ctx.beginPath(); ctx.moveTo(...p1); ctx.lineTo(...p2); ctx.stroke(); p1 = lerp(a[0], a[3], f); p2 = lerp(a[1], a[2], f); ctx.beginPath(); ctx.moveTo(...p1); ctx.lineTo(...p2); ctx.stroke(); } ctx.globalAlpha = 1;
      if (on) sp.pts.forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, 6 / R * 1.4, 0, Math.PI * 2); ctx.fill(); });
    } else if (tr.kind === 'face') {
      const [x, y] = sp.pts[0], bw = (sp.box ? sp.box.w : 0.1) * pxU, bh = (sp.box ? sp.box.h : 0.1) * pxV; ctx.strokeRect(x - bw / 2, y - bh / 2, bw, bh);
      ctx.font = `600 ${12 / R * 1.2}px ${getComputedStyle(document.body).fontFamily}`; ctx.fillText(tr.name, x - bw / 2, y - bh / 2 - 5 / R);
    } else {
      const pr = tr.patch * Math.min(pxU, pxV) / 2, sr = tr.search * Math.min(pxU, pxV) / 2;
      sp.pts.forEach(([x, y]) => { ctx.strokeRect(x - pr, y - pr, pr * 2, pr * 2); if (on) { ctx.setLineDash([4 / R, 4 / R]); ctx.strokeRect(x - pr - sr, y - pr - sr, (pr + sr) * 2, (pr + sr) * 2); ctx.setLineDash([]); } ctx.beginPath(); ctx.moveTo(x - 4 / R * 1.5, y); ctx.lineTo(x + 4 / R * 1.5, y); ctx.moveTo(x, y - 4 / R * 1.5); ctx.lineTo(x, y + 4 / R * 1.5); ctx.stroke(); });
      if (tr.kind === 'two') { ctx.beginPath(); ctx.moveTo(...sp.pts[0]); ctx.lineTo(...sp.pts[1]); ctx.stroke(); }
    }
  }
  if (trkFound.length && k) {   // subjects found on this frame: click one to track it
    trkFound.forEach((d, i) => { const c = clipPtToStage(clip, d.box.u, d.box.v, T); if (!c) return; const bw = d.box.w * pxU, bh = d.box.h * pxV; ctx.strokeStyle = '#5ec8ff'; ctx.setLineDash([5 / R, 4 / R]); ctx.strokeRect(c[0] - bw / 2, c[1] - bh / 2, bw, bh); ctx.setLineDash([]);
      ctx.fillStyle = '#5ec8ff'; ctx.font = `700 ${12 / R * 1.2}px ${getComputedStyle(document.body).fontFamily}`; ctx.fillText(`${i + 1} · ${d.cat} ${Math.round(d.score * 100)}%`, c[0] - bw / 2, c[1] - bh / 2 - 5 / R); });
  }
  ctx.restore();
}
cv.addEventListener('pointerdown', e => {
  if (wsMode !== 'track' || e.button !== 0) return; const clip = trackClip(); if (!clip) return;
  e.stopImmediatePropagation(); e.preventDefault();
  const [X, Y] = stagePoint(e), tol = 14 / (cv.getBoundingClientRect().width / ST.W);
  if (trkFound.length) { const L = clipLayer(clip), k = L && at(L, T), [lw, lh] = L ? layerSize(L) : [1, 1];
    const hit = trkFound.findIndex(d => { const c = clipPtToStage(clip, d.box.u, d.box.v, T); return c && Math.abs(X - c[0]) < d.box.w * lw * Math.abs(k.sx) / 2 && Math.abs(Y - c[1]) < d.box.h * lh * Math.abs(k.sy) / 2; });
    if (hit >= 0) { trackFromDetection(hit); return; } }
  const tr = trkById(trkSel); if (!tr || tr.clip !== clip.id) return; const sp = trkScreenPts(tr, clip); if (!sp) return;
  let idx = -1, bd = tol; sp.pts.forEach(([x, y], i) => { const d = Math.hypot(X - x, Y - y); if (d < bd) { bd = d; idx = i; } });
  if (idx < 0 && tr.kind !== 'planar') idx = 0;          // a single point jumps to the click
  if (idx < 0) { if (inQuad(sp.pts, X, Y)) idx = 'all'; else return; }
  trkDrag = { tr, clip, idx, start: [X, Y], base: sp.pts.map(p => p.slice()) }; cv.setPointerCapture(e.pointerId);
  const mv = ev => { const [x, y] = stagePoint(ev); trkMove(trkDrag, x, y); };
  const up = () => { cv.removeEventListener('pointermove', mv); cv.removeEventListener('pointerup', up); trkDrag = null; saveSoon(); renderProps(); };
  cv.addEventListener('pointermove', mv); cv.addEventListener('pointerup', up); trkMove(trkDrag, X, Y);
}, true);
function trkMove(D, X, Y) {
  const { tr, clip, idx, start, base } = D, dx = X - start[0], dy = Y - start[1];
  const pts = base.map((p, i) => (idx === 'all' || i === idx) ? [p[0] + dx, p[1] + dy] : p.slice()).map(([x, y]) => stageToClip(clip, x, y, T));
  if (idx !== 'all' && tr.kind !== 'planar' && !D.moved) { pts[idx] = stageToClip(clip, X, Y, T); }
  D.moved = true; const t = clamp(clipTime(clip, T), ...srcRange(clip));
  tr.init = { t, pts, box: tr.init.box };
  const S = tr.samples || []; const j = S.findIndex(s => Math.abs(s.t - t) < 0.5 / 30); if (j >= 0) { S[j] = Object.assign({}, S[j], { pts, conf: 1 }); tr.rev = (tr.rev || 0) + 1; }
  drawAll();
}

// ---------------------------------------------------------------- the Track panel
function renderTrackPanel(H, P) {
  const clip = trackClip();
  if (!clip) {
    H.innerHTML = '<span class="ty">Track</span><b>No clip</b>';
    P.innerHTML = `<div class="empty"><b>Nothing to track yet</b><span>Tracking follows something moving in a video clip: a face, a car, a sign. Add a clip, or open the tracking demo.</span>
      <button class="btn primary" id="trkImp">Import a clip…</button><button class="btn" id="trkDemo">Open the Tracking Playground demo</button></div>`;
    $('#trkImp').onclick = () => { const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'video/*'; inp.onchange = async () => { const f = inp.files[0]; if (!f) return; try { const id = await importVideo(f); const b = addVideoLayer(id); trkClipId = b.id; setMode('track'); } catch (e) { toast(e.message, true); } }; inp.click(); };
    $('#trkDemo').onclick = () => openDemo(DEMOS.find(d => d.id === 'track')); return;
  }
  trkClipId = clip.id; const list = trackers().filter(t => t.clip === clip.id), tr = trkById(trkSel) && trkById(trkSel).clip === clip.id ? trkById(trkSel) : list[list.length - 1] || null; trkSel = tr ? tr.id : null;
  const vlist = state.blocks.filter(b => b.id !== clip.id && b.type !== 'fx' && b.type !== 'bg');
  const att = tr ? state.blocks.filter(b => b.follow && b.follow.tracker === tr.id) : [];
  const S = tr ? tr.samples || [] : [], lost = S.filter(s => s.conf < 0.35).length;
  const modes = tr ? (tr.kind === 'planar' ? [['pin', 'Pin into the surface (corner pin)'], ['prs', 'Position + rotation + scale'], ['pos', 'Position only']] : tr.kind === 'two' ? [['prs', 'Position + rotation + scale'], ['ps', 'Position + scale'], ['pos', 'Position only']] : tr.kind === 'face' ? [['ps', 'Position + size'], ['pos', 'Position only']] : [['pos', 'Position']]) : [];
  H.innerHTML = `<span class="ty" style="color:#8be37a">Track</span><b>${esc(itemLabel(clip))}</b>`;
  P.innerHTML = `<section class="sec"><h2>Trackers <span class="hint">${list.length} on this clip</span></h2>
      <div style="display:grid;gap:5px">${list.map(t => `<button class="trkrow" data-tk="${t.id}" aria-pressed="${t === tr}"><span class="tk">${{ point: '1', two: '2', planar: '▱', face: '◉' }[t.kind]}</span><span class="tm"><b>${esc(t.name)}</b><span>${(t.samples || []).length ? `${t.samples.length} frames tracked` : 'not tracked yet'}</span></span></button>`).join('') || '<p class="desc" id="trkNone">No trackers yet: add one below, or find faces and people automatically.</p>'}</div>
      <div class="trkbtns"><button class="btn sm" data-new="point">+ 1-point</button><button class="btn sm" data-new="two">+ 2-point</button><button class="btn sm" data-new="planar">+ Planar (screen)</button><button class="btn sm" id="trkFind">Find faces &amp; people</button></div>
      ${trkFound.length ? `<div class="trkfound"><span class="lbl">Found on this frame: click one in the view or here</span>${trkFound.map((d, i) => `<button class="btn sm" data-fd="${i}">${i + 1} · ${esc(d.cat)} ${Math.round(d.score * 100)}%: track it</button>`).join('')}</div>` : ''}
    </section>` + (tr ? `<section class="sec"><h2>${esc(tr.name)} <span class="hint">${TRK_KINDS[tr.kind]}</span></h2>
      <div class="row"><label for="trkName">Name</label><input type="text" id="trkName" value="${esc(tr.name)}"></div>
      <p class="desc" id="trkHow">${tr.kind === 'planar' ? 'Drag the four corners onto a flat surface at this frame (a screen, sign or poster), then track.' : tr.kind === 'face' ? 'Found automatically; tracked by detection on every frame.' : 'Drag the box onto a sharp, high-contrast detail at this frame, then track.'}</p>
      <div class="row"><button class="btn sm" id="trkBack" ${trkBusy ? 'disabled' : ''}>◀ Track back</button><button class="btn sm trk" id="trkFwd" ${trkBusy ? 'disabled' : ''}>Track ▶</button><button class="btn sm ghost" id="trkAll" ${trkBusy ? 'disabled' : ''}>Whole clip</button></div>
      ${trkBusy ? `<div class="row"><div class="trkbar" style="flex:1"><i id="trkBarI" style="width:${(trkProg * 100).toFixed(1)}%"></i></div><button class="btn sm ghost" id="trkStop">Stop</button></div>` : ''}
      ${S.length ? `<div class="trkconf" title="Confidence per frame: red = uncertain">${S.filter((s, i) => i % Math.max(1, Math.ceil(S.length / 90)) === 0).map(s => `<i class="${s.conf < 0.35 ? 'lost' : ''}" style="height:${Math.round(20 + 80 * clamp(s.conf, 0, 1))}%"></i>`).join('')}</div><p class="desc" id="trkStat">${S.length} frames · ${fmt(S[0].t, 2)}–${fmt(S[S.length - 1].t, 2)} s of the clip${lost ? ` · ${lost} uncertain` : ''}</p>` : ''}
      ${tr.kind !== 'face' ? `<div class="row"><label for="trkPatch">Feature size</label><input type="range" id="trkPatch" min="0.03" max="0.2" step="0.005" value="${tr.patch}"></div><div class="row"><label for="trkSearch">Search area</label><input type="range" id="trkSearch" min="0.04" max="0.4" step="0.01" value="${tr.search}"></div>` : ''}
      <div class="row"><label for="trkSmooth">Smoothing</label><input type="range" id="trkSmooth" min="0" max="1" step="0.05" value="${tr.smooth}"></div>
      <div class="row"><button class="btn sm ghost" id="trkClear" ${S.length ? '' : 'disabled'}>Clear the track</button><button class="btn sm ghost danger" id="trkDel">Delete tracker</button></div>
    </section>
    <section class="sec"><h2>Attach a layer <span class="hint">its motion becomes keyframes</span></h2>
      <div class="row"><label for="trkLay">Layer</label><select id="trkLay">${vlist.map(b => `<option value="${b.id}">${esc(itemLabel(b))}</option>`).join('')}</select></div>
      <div class="row"><label for="trkMode">Follow</label><select id="trkMode">${modes.map(([k, n]) => `<option value="${k}">${n}</option>`).join('')}</select></div>
      <div class="row"><button class="btn sm primary" id="trkAtt" ${S.length && vlist.length ? '' : 'disabled'}>Attach</button><button class="btn sm ghost" id="trkNewText" ${S.length ? '' : 'disabled'}>+ New text that follows</button></div>
      ${att.map(b => `<div class="row"><span style="flex:1">${esc(itemLabel(b))} <span class="hint" style="color:var(--muted)">· ${{ pos: 'position', ps: 'position + size', prs: 'position + rotation + scale', pin: 'corner pin' }[b.follow.mode]}</span></span><button class="btn sm ghost" data-det="${b.id}">Detach</button></div>`).join('')}
      <p class="desc">The layer keeps its offset from the tracker at the playhead. Re-tracking updates every attached layer. KineMaster gets ordinary keys (corner pins for a surface).</p>
    </section>
    ${tr.kind === 'point' || tr.kind === 'two' ? `<section class="sec"><h2>Stabilize <span class="hint">hold the clip steady</span></h2>
      <div class="row"><label for="trkZoom">Zoom in</label><input type="range" id="trkZoom" min="1" max="1.4" step="0.01" value="${clip.stab ? clip.stab.zoom : 1.1}"></div>
      <div class="row"><button class="btn sm" id="trkStab" ${S.length ? '' : 'disabled'}>${clip.stab ? 'Stabilize again' : 'Stabilize this clip'}</button>${clip.stab ? '<button class="btn sm ghost" id="trkUnstab">Remove</button>' : ''}</div>
      <p class="desc">Moves the clip against the tracked motion (${tr.kind === 'two' ? 'position, rotation and scale' : 'position'}), zoomed in so the edges stay hidden.</p></section>` : ''}` : '');
  wrapSecs(P);
  $$('[data-tk]', P).forEach(x => x.onclick = () => { trkSel = x.dataset.tk; renderProps(); drawAll(); });
  $$('[data-new]', P).forEach(x => x.onclick = () => newTracker(x.dataset.new, clip));
  $$('[data-fd]', P).forEach(x => x.onclick = () => trackFromDetection(+x.dataset.fd));
  $$('[data-det]', P).forEach(x => x.onclick = () => detachLayer(blkById(x.dataset.det)));
  const on = (id, f) => { const e = document.getElementById(id); if (e) e.onclick = f; };
  on('trkFind', () => { toast('Looking for faces, people and objects on this frame…', false, 1500); findSubjects(); });
  if (!tr) return;
  on('trkFwd', () => { const t0 = T; runTrack(tr, 1).then(() => setTime(t0)); }); on('trkBack', () => { const t0 = T; runTrack(tr, -1).then(() => setTime(t0)); }); on('trkAll', () => runTrack(tr, 1, true)); on('trkStop', () => { trkCancel = true; });
  on('trkClear', () => { tr.samples = []; tr.rev = (tr.rev || 0) + 1; saveSoon(); renderProps(); drawAll(); });
  on('trkDel', () => { state.blocks.forEach(b => { if (b.follow && b.follow.tracker === tr.id) detachLayer(b); }); if (clip.stab && clip.stab.tracker === tr.id) unstabilize(clip); state.trackers = trackers().filter(x => x !== tr); trkSel = null; saveSoon(); renderProps(); drawAll(); });
  on('trkAtt', () => attachLayer(blkById($('#trkLay').value), tr, $('#trkMode').value));
  on('trkNewText', () => { const b = newBlock({ text: 'TRACKED', x: CX(), y: CY(), size: 3, start: clip.start, end: clip.end, style: 'punch' }); const p = trkPose(tr, clip, T); if (p) { b.x = Math.round(p.x); b.y = Math.round(p.y - (tr.kind === 'face' ? p.len * 0.8 : 90)); } state.blocks.push(b); bake(b); attachLayer(b, tr, tr.kind === 'face' || tr.kind === 'two' ? 'ps' : 'pos'); afterStructure(); renderProps(); });
  on('trkStab', () => stabilize(clip, tr, +$('#trkZoom').value)); on('trkUnstab', () => unstabilize(clip));
  const nm = $('#trkName'); if (nm) nm.onchange = e => { tr.name = e.target.value || tr.name; saveSoon(); renderProps(); };
  for (const [id, k] of [['trkPatch', 'patch'], ['trkSearch', 'search'], ['trkSmooth', 'smooth']]) { const e = document.getElementById(id); if (e) e.oninput = ev => { tr[k] = +ev.target.value; if (k === 'smooth') { tr.rev = (tr.rev || 0) + 1; applyFollowers(tr); } saveSoon(); drawAll(); }; }
}

// ---------------------------------------------------------------- demo: a clip made here (a moving target and a poster in perspective)
async function demoTrackClip(seconds = 4) {
  const W = 540, H = 960, c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
  const tex = document.createElement('canvas'); tex.width = 900; tex.height = 1500; const tg = tex.getContext('2d'); let seed = 3; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  tg.fillStyle = '#1d2230'; tg.fillRect(0, 0, 900, 1500); for (let i = 0; i < 900; i++) { tg.fillStyle = `hsl(${200 + rnd() * 60},${20 + rnd() * 30}%,${18 + rnd() * 30}%)`; tg.fillRect(rnd() * 900, rnd() * 1500, 6 + rnd() * 40, 6 + rnd() * 40); }
  const poster = document.createElement('canvas'); poster.width = 300; poster.height = 400; const pg = poster.getContext('2d');
  pg.fillStyle = '#f4f1ea'; pg.fillRect(0, 0, 300, 400); for (let y = 0; y < 8; y++) for (let x = 0; x < 6; x++) if ((x + y) % 2) { pg.fillStyle = '#ff5b3d'; pg.fillRect(x * 50, y * 50, 50, 50); }
  pg.fillStyle = '#111'; pg.font = 'bold 64px sans-serif'; pg.textAlign = 'center'; pg.fillText('YOUR', 150, 170); pg.fillText('AD', 150, 250);
  const stream = c.captureStream(30), rec = new MediaRecorder(stream, { mimeType: MediaRecorder.isTypeSupported('video/webm;codecs=vp9') ? 'video/webm;codecs=vp9' : 'video/webm', videoBitsPerSecond: 6e6 }), chunks = [];
  rec.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
  const draw = t => {
    const u = t / seconds; g.drawImage(tex, 120 + Math.sin(u * 5) * 60 - 60 * u, 200 + u * 120, W * 1.2, H * 1.2, 0, 0, W, H);
    // poster: a plane drifting and turning, drawn with an affine pair of triangles per quad (enough for the demo)
    const cx = W * (0.62 - 0.18 * u), cy = H * (0.36 + 0.06 * Math.sin(u * 3)), sw = 150 + 40 * u, sh = 200 + 50 * u, sk = 0.25 * Math.sin(u * 2.4);
    const q = [[cx - sw / 2, cy - sh / 2 - sk * 40], [cx + sw / 2, cy - sh / 2 + sk * 40], [cx + sw / 2, cy + sh / 2 - sk * 20], [cx - sw / 2, cy + sh / 2 + sk * 20]];
    const tri = (s, d) => { const [[x0, y0], [x1, y1], [x2, y2]] = s, [[u0, v0], [u1, v1], [u2, v2]] = d, den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0);
      const a = ((u1 - u0) * (y2 - y0) - (u2 - u0) * (y1 - y0)) / den, cc = ((u2 - u0) * (x1 - x0) - (u1 - u0) * (x2 - x0)) / den, b = ((v1 - v0) * (y2 - y0) - (v2 - v0) * (y1 - y0)) / den, dd = ((v2 - v0) * (x1 - x0) - (v1 - v0) * (x2 - x0)) / den;
      g.save(); g.beginPath(); g.moveTo(u0, v0); g.lineTo(u1, v1); g.lineTo(u2, v2); g.closePath(); g.clip(); g.setTransform(a, b, cc, dd, u0 - a * x0 - cc * y0, v0 - b * x0 - dd * y0); g.drawImage(poster, 0, 0); g.restore(); };
    const Hq = homography([[0, 0], [300, 0], [300, 400], [0, 400]], q), N = 10;   // true perspective: a fine grid of small triangles
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const a = [i * 30, j * 40], b2 = [(i + 1) * 30, j * 40], c2 = [(i + 1) * 30, (j + 1) * 40], d2 = [i * 30, (j + 1) * 40];
      tri([a, b2, c2], [Hq(...a), Hq(...b2), Hq(...c2)]); tri([a, c2, d2], [Hq(...a), Hq(...c2), Hq(...d2)]); }
    // the target: a ringed dot on a curve
    const tx = W * (0.25 + 0.45 * u), ty = H * (0.72 - 0.16 * Math.sin(u * Math.PI));
    g.fillStyle = '#fff'; g.beginPath(); g.arc(tx, ty, 22, 0, Math.PI * 2); g.fill(); g.fillStyle = '#ff5b3d'; g.beginPath(); g.arc(tx, ty, 13, 0, Math.PI * 2); g.fill(); g.fillStyle = '#111'; g.beginPath(); g.arc(tx, ty, 5, 0, Math.PI * 2); g.fill();
  };
  draw(0); rec.start(100); const t0 = performance.now();
  await new Promise(res => { const step = () => { const t = (performance.now() - t0) / 1000; draw(Math.min(t, seconds)); if (t < seconds + 0.15) requestAnimationFrame(step); else res(); }; requestAnimationFrame(step); });
  await new Promise(res => { rec.onstop = res; rec.stop(); });
  return { blob: new Blob(chunks, { type: 'video/webm' }), poster: [[0.62 * W - 75, 0.36 * H - 100 - 0], [0.62 * W + 75, 0.36 * H - 100], [0.62 * W + 75, 0.36 * H + 100], [0.62 * W - 75, 0.36 * H + 100]].map(([x, y]) => [x / W, y / H]), target: [0.25, 0.72] };
}
async function demoTrack() {
  demoState('9:16', 'Tracking Playground', 4, '#0B0C10');
  toast('Making a short clip to track (4 s)…', false, 4000); finishDemo(0);
  const clip0 = await demoTrackClip(4), id = 'vtrackdemo';
  await registerVideo(id, clip0.blob, 'tracking_demo', 'webm');
  const v = addVideoLayer(id, { start: 0, end: 3.9, name: 'Tracking clip' });
  const sign = newItem('photo', { name: 'Poster replacement', x: CX(), y: CY(), w: 300, depth: 0, start: 0, end: 3.9, photo: { src: 'ph:6', aspect: '3:4', border: 0, shadow: 0, reflect: 0 }, in: null, out: null });
  const word = newBlock({ text: 'FOLLOW ME', x: CX(), y: CY(), size: 3, start: 0, end: 3.9, style: 'punch' });
  state.blocks.push(sign, word); bake(sign); bake(word); setTime(0); setMode('track');
  const tp = newTracker('point', v, { name: 'Target · 1-point' }); tp.init.pts = [clip0.target];
  const tq = newTracker('planar', v, { name: 'Poster · planar' }); tq.init.pts = clip0.poster;
  await runTrack(tp, 1, true); await runTrack(tq, 1, true); setTime(0.05);
  const p = trkPose(tp, v, 0.05); if (p) { word.x = Math.round(p.x); word.y = Math.round(p.y - 70); word.tk = []; bake(word); }
  attachLayer(word, tp, 'pos'); attachLayer(sign, tq, 'pin'); trkSel = tq.id; afterStructure(); setTime(1.5);
  toast('Tracked: FOLLOW ME rides on the target, the photo is pinned into the moving poster. Try your own clip: Import a clip in Track mode.', false, 8000);
}
"""
sub("// ---------------------------------------------------------------- start screen", JS + "\n// ---------------------------------------------------------------- start screen")
open(dst, 'w', encoding='utf-8').write(s)
print('patched', dst)
