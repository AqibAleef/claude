"""Kinekit Studio: (1) Offset mode - re-transform a layer on top of its keyframes without adding keys,
(2) Origin - an editable pivot point for rotation and scale.   python3 patch_xo.py IN.html OUT.html"""
import sys
src, dst = sys.argv[1:3]
s = open(src).read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (c, a[:90])
    s = s.replace(a, b)


# ------------------------------------------------------------------ core: offset on top of the keys
rep("function xformAt(b, t) {\n  const ks = b.tk; if (!ks || !ks.length) return restXf(b);",
"""/* Offset ("re-transform"): b.xo = {x, y, depth, rot, s, rx, ry} is added on top of the whole animation, keys or not.
   It moves / turns / scales every keyframe at once without touching them (Offset mode: Shift+O). */
const XO0 = () => ({ x: 0, y: 0, depth: 0, rot: 0, s: 1, rx: 0, ry: 0 });
const hasXo = b => !!(b.xo && (b.xo.x || b.xo.y || b.xo.depth || b.xo.rot || (b.xo.s ?? 1) !== 1 || b.xo.rx || b.xo.ry));
let xoMode = false;
function xformAt(b, t) {
  const A = xformRaw(b, t), o = b.xo; if (!o) return A;
  return { x: A.x + (+o.x || 0), y: A.y + (+o.y || 0), depth: A.depth + (+o.depth || 0), rot: A.rot + (+o.rot || 0), s: A.s * (o.s ?? 1), rx: (A.rx || 0) + (+o.rx || 0), ry: (A.ry || 0) + (+o.ry || 0) };
}
/* the keyed (or rest) transform alone, without the offset */
function xformRaw(b, t) {
  const ks = b.tk; if (!ks || !ks.length) return restXf(b);""")
# origin (pivot): rotation and scale turn around b.org = {x, y} (stage px from the layer's anchor, unscaled)
rep("""function applyXf(p, b, A) {
  const a = A.rot * D2R, vx = (p.x - b.x) * A.s, vy = (p.y - b.y) * A.s, c = Math.cos(a), s = Math.sin(a);
  return Object.assign({}, p, { x: A.x + vx * c - vy * s, y: A.y + vx * s + vy * c, rot: p.rot + A.rot, sx: p.sx * A.s, sy: p.sy * A.s });
}""", """/* Origin (pivot): b.org = {x, y}, stage px from the layer's anchor. Rotation and scale turn around it; at no rotation
   and 100 % scale the layer sits exactly where it did, so moving the origin never moves a still layer. */
const orgOf = b => [+(b.org && b.org.x) || 0, +(b.org && b.org.y) || 0];
const hasOrg = b => { const [ox, oy] = orgOf(b); return !!(ox || oy); };
function applyXf(p, b, A) {
  const [ox, oy] = orgOf(b), a = A.rot * D2R, vx = (p.x - b.x - ox) * A.s, vy = (p.y - b.y - oy) * A.s, c = Math.cos(a), s = Math.sin(a);
  return Object.assign({}, p, { x: A.x + ox + vx * c - vy * s, y: A.y + oy + vx * s + vy * c, rot: p.rot + A.rot, sx: p.sx * A.s, sy: p.sy * A.s });
}
/* move the origin; keepInPlace shifts the layer's offset (never its keys) so it doesn't jump at the playhead */
function setOrigin(b, nx, ny, keepInPlace = true, t = T) {
  const [ox, oy] = orgOf(b), dx = nx - ox, dy = ny - oy;
  if (keepInPlace && (dx || dy)) {
    const A = xformAt(b, t), a = A.rot * D2R, c = Math.cos(a) * A.s, s = Math.sin(a) * A.s;
    const ex = dx - (dx * c - dy * s), ey = dy - (dx * s + dy * c);          // how far the layer would jump
    if (Math.abs(ex) > 1e-6 || Math.abs(ey) > 1e-6) { b.xo = Object.assign(XO0(), b.xo || {}); b.xo.x = +((+b.xo.x || 0) - ex).toFixed(2); b.xo.y = +((+b.xo.y || 0) - ey).toFixed(2); }
  }
  b.org = { x: +nx.toFixed(1), y: +ny.toFixed(1) };
  if (!b.org.x && !b.org.y) delete b.org;
}
/* the layer's own size at 100 % (for the origin presets) */
function blockSize(b) {
  if (b.type === 'text') { const u = K.layout(b.text || ' ', 0, 0, +b.size || 1, 'whole', +b.tracking || 0, +b.lineHeight || 1)[0]; return u ? [u.w, u.h] : [100, 40]; }
  if (b.type === 'photo' || b.type === 'video' || b.type === 'decor') { const g = itemPicture(b); return [g.w, g.h]; }
  return [ST.W, ST.H];
}
/* bake the offset into every key (or the rest values) and clear it */
function bakeOffset(b) {
  const o = b.xo; if (!o) return; const sc = o.s ?? 1;
  const one = k => { k.x = +((+k.x || 0) + (+o.x || 0)).toFixed(1); k.y = +((+k.y || 0) + (+o.y || 0)).toFixed(1); k.depth = +((+k.depth || 0) + (+o.depth || 0)).toFixed(1);
    k.rot = +((+k.rot || 0) + (+o.rot || 0)).toFixed(2); k.rx = +((+k.rx || 0) + (+o.rx || 0)).toFixed(2); k.ry = +((+k.ry || 0) + (+o.ry || 0)).toFixed(2); };
  if (hasTk(b)) b.tk.forEach(k => { one(k); k.s = +((k.s ?? 1) * sc).toFixed(4); });
  else { one(b); if (sc !== 1) scaleBase(b, sc); }
  delete b.xo;
}""")
# keys are written / read raw (the offset stays on top, never baked into a new key by accident)
rep("""function setXf(b, patch, t = T) {
  if (b.tk && b.tk.length) {
    let i = keyAt(b.tk, t);
    if (i < 0) { const A = xformAt(b, t);""", """function setXf(b, patch, t = T) {
  if (xoMode && b.type !== 'bg') {            // Offset mode: the change goes to the offset, no key is added
    const R = xformRaw(b, t), o = b.xo = Object.assign(XO0(), b.xo || {});
    for (const ch in patch) {
      if (ch === 's') o.s = +clamp(patch.s / (R.s || 1), 0.01, 100).toFixed(4);
      else if (XF_CH.includes(ch)) o[ch] = +((+patch[ch]) - (+R[ch] || 0)).toFixed(ch === 'rot' || ch === 'rx' || ch === 'ry' ? 2 : 1);
    }
    if (!hasXo(b)) delete b.xo;
    return;
  }
  // a patch holds final values (offset included): take the offset off before writing keys / rest values
  if (b.xo) { const o = b.xo; patch = Object.assign({}, patch); for (const ch in patch) { if (ch === 's') patch.s = patch.s / (o.s ?? 1); else if (XF_CH.includes(ch)) patch[ch] = patch[ch] - (+o[ch] || 0); } }
  if (b.tk && b.tk.length) {
    let i = keyAt(b.tk, t);
    if (i < 0) { const A = xformRaw(b, t);""")
rep("""  b.tk = b.tk || []; const A = xformAt(b, t); const i = keyAt(b.tk, t);""", """  b.tk = b.tk || []; const A = xformRaw(b, t); const i = keyAt(b.tk, t);""")
rep("function clearTk(b, t = T) { if (!b.tk || !b.tk.length) return; const A = xformAt(b, t);", "function clearTk(b, t = T) { if (!b.tk || !b.tk.length) return; const A = xformRaw(b, t);")
# the still-layer fast path must still apply an offset / origin
rep("""  if (!anim && !useCam && !persp) {
    const A = restXf(b); if (!A.rot) return layers;""", """  if (!anim && !useCam && !persp) {
    const A = xformAt(b, b.start); if (!A.rot && A.s === 1 && !hasXo(b)) return layers;""")
rep("(b.type === 'photo' && Math.abs(+b.yaw || 0) > 0.01); };", "(b.type === 'photo' && Math.abs(+b.yaw || 0) > 0.01) || !!(b.xo && (Math.abs(+b.xo.rx || 0) > 0.01 || Math.abs(+b.xo.ry || 0) > 0.01)); };")
# undo snapshots of a modal edit include offset and origin
rep("function xfSnapshot(b) { return { rx: b.rx,", "function xfSnapshot(b) { return { xo: b.xo ? clone(b.xo) : null, org: b.org ? clone(b.org) : null, rx: b.rx,")
rep("function xfRestore(b, s) { b.rx = s.rx;", "function xfRestore(b, s) { if (s.xo) b.xo = clone(s.xo); else delete b.xo; if (s.org) b.org = clone(s.org); else delete b.org; b.rx = s.rx;")

# ------------------------------------------------------------------ viewport: pivot marker, rotate / scale around it, origin tool
rep("""function anchorScreen(b, t = T) {""", """/* where the layer's origin (pivot) shows in the view */
function pivotScreen(b, t = T) {
  const A = xformAt(b, t), [ox, oy] = orgOf(b);
  if (camOn() && b.cam !== false) { const p = K.projectPose(K.cameraAt(state.camera, t), { depth: A.depth }, { x: A.x + ox, y: A.y + oy, rot: 0, opacity: 1, sx: 1, sy: 1 }); return [p.x, p.y, p.sx]; }
  return [A.x + ox, A.y + oy, 1];
}
function anchorScreen(b, t = T) {""")
rep("""      const [ax, ay] = anchorScreen(b); ctx.beginPath(); ctx.arc(ax, ay, 4 / R * 1.4, 0, 7); ctx.stroke();""",
"""      const [ax, ay] = anchorScreen(b); ctx.beginPath(); ctx.arc(ax, ay, 4 / R * 1.4, 0, 7); ctx.stroke();
      if (act && (hasOrg(b) || (modal && modal.op === 'origin'))) {   // origin: a crosshair in a ring
        const [px, py] = pivotScreen(b), q = 9 / R * 1.4; ctx.save(); ctx.strokeStyle = '#4fd1ff'; ctx.lineWidth = 1.6 / R;
        ctx.beginPath(); ctx.arc(px, py, q * 0.6, 0, 7); ctx.moveTo(px - q, py); ctx.lineTo(px + q, py); ctx.moveTo(px, py - q); ctx.lineTo(px, py + q); ctx.stroke(); ctx.restore();
      }""")
rep("""  if (noPv.length && guides) {""", """  if (xoMode && guides) { const fs = Math.round(cv.width * 0.03); ctx.font = `600 ${fs}px sans-serif`; ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillStyle = 'rgba(10,30,40,.75)'; const tw = ctx.measureText('OFFSET MODE · Shift+O').width; ctx.fillRect(fs * 0.6, fs * 0.6 + (noPv.length ? fs * 1.6 : 0), tw + fs * 0.8, fs * 1.5); ctx.fillStyle = '#4fd1ff'; ctx.fillText('OFFSET MODE · Shift+O', fs, fs * 0.85 + (noPv.length ? fs * 1.6 : 0)); }
  if (noPv.length && guides) {""")
rep("""    else { let sx = 0, sy = 0; for (const t of targets) { const [ax, ay] = anchorScreen(t.b); sx += ax; sy += ay; } modal.pivot = [sx / targets.length, sy / targets.length]; }""",
    """    else { let sx = 0, sy = 0; for (const t of targets) { const [ax, ay] = op === 'grab' ? anchorScreen(t.b) : pivotScreen(t.b); sx += ax; sy += ay; } modal.pivot = [sx / targets.length, sy / targets.length]; }""")
rep("""    targets = list.map(b => ({ kind: 'layer', b, snap: xfSnapshot(b), A0: xformAt(b, T) }));
  }""", """    targets = list.map(b => ({ kind: 'layer', b, snap: xfSnapshot(b), A0: xformAt(b, T), org0: orgOf(b) }));
    if (op === 'origin' && (view !== '2d' || targets.length !== 1)) { toast(view !== '2d' ? 'Move the origin in the camera view (2D).' : 'Select one layer to move its origin.', false, 2000); return; }
  }""")
rep("""      if (hasTk(b)) setXf(b, { s: t.A0.s * f }); else scaleBase(b, f);""", """      if (hasTk(b) || xoMode) setXf(b, { s: t.A0.s * f }); else scaleBase(b, f);""")
rep("""    info = `Scale ${fmt(f, 3)}×`;
  }""", """    info = `Scale ${fmt(f, 3)}×`;
  } else if (M.op === 'origin') {
    const t = M.targets[0], b = t.b, sc = anchorScreen(b)[2] || 1, keep = ui.orgKeep !== false;
    let DX = (M.cur[0] - M.s0[0]) * fine / sc, DY = (M.cur[1] - M.s0[1]) * fine / sc, dx = DX, dy = DY;
    if (keep) { const a = -t.A0.rot * D2R, k = 1 / (t.A0.s || 1); dx = (DX * Math.cos(a) - DY * Math.sin(a)) * k; dy = (DX * Math.sin(a) + DY * Math.cos(a)) * k; }   // into the layer's own frame
    if (ax === 'x') dy = 0; else if (ax === 'y') dx = 0;
    let nx = t.org0[0] + dx, ny = t.org0[1] + dy;
    if (!M.noSnap) { const [w, h] = blockSize(b), sn = 10 / sc; for (const gx of [-w / 2, 0, w / 2]) if (Math.abs(nx - gx) < sn) nx = gx; for (const gy of [-h / 2, 0, h / 2]) if (Math.abs(ny - gy) < sn) ny = gy; }
    setOrigin(b, nx, ny, keep);
    info = `Origin  x ${fmt(nx, 0)}  y ${fmt(ny, 0)} px from centre${ui.orgKeep !== false ? '' : '  (layer moves)'}   ·  snaps to edges and centre, Ctrl: free`;
  }""")
rep("""  hud.textContent = (modal.info || { grab: 'Move', rotate: 'Rotate', scale: 'Scale' }[modal.op])""",
    """  hud.textContent = (xoMode && modal.op !== 'origin' ? 'Offset · ' : '') + (modal.info || { grab: 'Move', rotate: 'Rotate', scale: 'Scale', origin: 'Origin' }[modal.op])""")
rep("""  if (k === 'g' || k === 'r' || k === 's') { const op = { g: 'grab', r: 'rotate', s: 'scale' }[k]; if (op !== modal.op)""",
    """  if ((k === 'g' || k === 'r' || k === 's') && modal.op !== 'origin') { const op = { g: 'grab', r: 'rotate', s: 'scale' }[k]; if (op !== modal.op)""")
rep("else if (hasTk(b)) setXf(b, { s: 1 });", "else if (hasTk(b) || xoMode) setXf(b, { s: 1 });")

# ------------------------------------------------------------------ actions, shortcuts, menu
rep("""  resetXf: { label: 'Clear location', keys: [['alt+g', VP]], run: () => clearChannel('loc') },""",
"""  resetXf: { label: 'Clear location', keys: [['alt+g', VP]], run: () => clearChannel('loc') },
  offsetMode: { label: 'Offset mode (re-transform without keys)', keys: [['shift+o', VP]], check: () => xoMode, run: () => { xoMode = !xoMode; toast(xoMode ? 'Offset mode: Move / Rotate / Scale and the Transform fields now shift the whole animation. No keys are added.' : 'Offset mode off: edits key the transform again.', false, 3200); renderProps(); drawAll(); updateHints(); } },
  editOrigin: { label: 'Move origin (pivot)', keys: [['shift+p', VP]], run: () => { if (!S.active) return toast('Select a layer first.', false, 1500); startModal('origin', '2d', lastClient); } },
  resetOrigin: { label: 'Reset origin to centre', run: () => { for (const b of selected()) { setOrigin(b, 0, 0, ui.orgKeep !== false); changed(b); } renderProps(); } },
  bakeOffset: { label: 'Bake offset into keys', run: () => { for (const b of selected()) { bakeOffset(b); changed(b); } renderProps(); toast('Offset applied to the keys.', false, 1500); } },""")
rep("""{ act: 'raise' }, { act: 'lower' }, { act: 'resetXf' }],""", """{ act: 'raise' }, { act: 'lower' }, { act: 'resetXf' }, '-', { act: 'offsetMode' }, { act: 'editOrigin' }, { act: 'resetOrigin' }, { act: 'bakeOffset' }],""")

# ------------------------------------------------------------------ Transform panel: mode switch, offset readout, origin section
rep("""  const A = xformAt(b, T), anim = hasTk(b), onK = anim && keyAt(b.tk, T) >= 0, ks = anim ? (onK ? 2 : 1) : 0;""",
    """  const A = xformAt(b, T), anim = hasTk(b), onK = anim && keyAt(b.tk, T) >= 0, ks = xoMode ? -1 : anim ? (onK ? 2 : 1) : 0, o = b.xo || XO0(), [ox, oy] = orgOf(b);""")
rep("""  return `${fx ? '' : `<section class="sec"><h2>Transform <span class="hint">${anim ? b.tk.length + ' keys · at playhead' : 'not animated'}</span></h2>
    ${xfRow('xfX',""", """  return `${fx ? '' : `<section class="sec"><h2>Transform <span class="hint">${xoMode ? 'offset mode · no keys' : anim ? b.tk.length + ' keys · at playhead' : 'not animated'}</span></h2>
    <div class="row"><label>Edits</label>${seg('xfModeSeg', { keys: 'Key at playhead', offset: 'Offset all keys' }, xoMode ? 'offset' : 'keys')}</div>
    ${xfRow('xfX',""")
rep("""${anim ? xfRow('xfS', 'Scale', A.s * 100, 1, '%', ks, 1) : ''}""", """${anim || xoMode || hasXo(b) ? xfRow('xfS', 'Scale', A.s * 100, 1, '%', ks, 1) : ''}""")
rep("""    <p class="desc">${anim ? 'Changing a value adds or updates the key at the playhead. Keys show as diamonds on this layer\\'s timeline bar.' : 'Press I (or a diamond) to key the transform at the playhead, move the playhead, change a value: KineMaster gets the motion as keyframes.'}</p>
  </section>`}""", """    ${hasXo(b) ? `<div class="desc" style="margin-top:6px">Offset on top of ${anim ? 'the keys' : 'the layer'}: ${[['x', 'x', 0, 'px'], ['y', 'y', 0, 'px'], ['depth', 'depth', 0, ''], ['rot', 'rot', 1, '°'], ['rx', 'tilt x', 1, '°'], ['ry', 'tilt y', 1, '°']].filter(([k]) => +o[k]).map(([k, n, d, u]) => `${n} ${+o[k] > 0 ? '+' : ''}${fmt(+o[k], d)}${u}`).concat((o.s ?? 1) !== 1 ? [`scale ×${fmt(o.s, 3)}`] : []).join(' · ')}</div>
    <div class="row"><button class="btn sm ghost" id="xoBake" title="Write the offset into every key and clear it">Bake into keys</button><button class="btn sm ghost" id="xoReset">Reset offset</button></div>` : ''}
    <p class="desc">${xoMode ? 'Offset mode: every change moves, turns or scales the whole animation (all keys keep their timing and shape). No key is added. Shift+O switches back.' : anim ? 'Changing a value adds or updates the key at the playhead. Keys show as diamonds on this layer\\'s timeline bar. Shift+O: offset the whole animation instead.' : 'Press I (or a diamond) to key the transform at the playhead, move the playhead, change a value: KineMaster gets the motion as keyframes.'}</p>
  </section>
  ${b.type === 'bg' ? '' : `<section class="sec"><h2>Origin <span class="hint">pivot for rotation and scale</span></h2>
    ${xfRow('xfOX', 'Origin X', ox, 1, 'px from the layer centre', -1, 0)}${xfRow('xfOY', 'Origin Y', oy, 1, 'px from the layer centre', -1, 0)}
    <div class="row"><label>Snap to</label><div class="orgGrid" style="display:grid;grid-template-columns:repeat(3,22px);gap:3px">${[-1, 0, 1].map(gy => [-1, 0, 1].map(gx => { const [w, h] = blockSize(b), on = Math.abs(ox - gx * w / 2) < 0.6 && Math.abs(oy - gy * h / 2) < 0.6; return `<button class="btn sm${on ? ' primary' : ''}" style="padding:0;height:22px" data-org="${gx},${gy}" title="${['Top', 'Middle', 'Bottom'][gy + 1]} ${['left', 'centre', 'right'][gx + 1]}">${on ? '●' : '·'}</button>`; }).join('')).join('')}</div></div>
    <label class="tog"><input type="checkbox" id="orgKeep" ${ui.orgKeep !== false ? 'checked' : ''}> Keep the layer in place when the origin moves</label>
    <div class="row"><button class="btn sm" id="orgEdit">Move in viewport <kbd>Shift+P</kbd></button></div>
    <p class="desc">Rotation and scale (keys and offset) turn around this point. Keep in place adjusts the offset, never the keys.</p>
  </section>`}`}""")
rep("""  for (const id of [...Object.keys(ch), 'xfB', 'xfYaw']) { const el = $('#' + id); if (el) el.onchange = () => apply(id, +el.value, true); }""",
    """  for (const id of [...Object.keys(ch), 'xfB', 'xfYaw', 'xfOX', 'xfOY']) { const el = $('#' + id); if (el) el.onchange = () => apply(id, +el.value, true); }
  segBind('#xfModeSeg', v => { xoMode = v === 'offset'; renderProps(); drawAll(); });
  const xb = $('#xoBake'); if (xb) xb.onclick = () => { bakeOffset(b); changed(b); renderProps(); };
  const xr = $('#xoReset'); if (xr) xr.onclick = () => { delete b.xo; changed(b); renderProps(); };
  $$('[data-org]', P).forEach(btn => btn.onclick = () => { const [gx, gy] = btn.dataset.org.split(',').map(Number), [w, h] = blockSize(b); setOrigin(b, gx * w / 2, gy * h / 2, ui.orgKeep !== false); changed(b); renderProps(); });
  const ok = $('#orgKeep'); if (ok) ok.onchange = e => { ui.orgKeep = e.target.checked; saveUi(); };
  const oe = $('#orgEdit'); if (oe) oe.onclick = () => { const r = cv.getBoundingClientRect(); startModal('origin', '2d', [r.left + r.width / 2, r.top + r.height / 2]); };""")
rep("""    else if (id === 'xfYaw') b.yaw = clamp(v, -89, 89);""", """    else if (id === 'xfYaw') b.yaw = clamp(v, -89, 89);
    else if (id === 'xfOX' || id === 'xfOY') { const [ox, oy] = orgOf(b); setOrigin(b, id === 'xfOX' ? v : ox, id === 'xfOY' ? v : oy, ui.orgKeep !== false); }""")

rep("else if (modal) parts = [`<b style=\"color:var(--act)\">${{ grab: 'Move', rotate: 'Rotate', scale: 'Scale' }[modal.op]}</b>`",
    "else if (modal) parts = [`<b style=\"color:var(--act)\">${(xoMode && modal.op !== 'origin' ? 'Offset · ' : '') + { grab: 'Move', rotate: 'Rotate', scale: 'Scale', origin: 'Move origin' }[modal.op]}</b>`")

# ------------------------------------------------------------------ recipes keep both (scene items are saved whole already)
rep("rx: b.rx, ry: b.ry, persp: b.persp };", "rx: b.rx, ry: b.ry, persp: b.persp, xo: b.xo, org: b.org };")
rep("for (const k of ['fx', 'extrude', 'shape', 'real3d', 'slot', 'reflect', 'animators', 'kmPins', 'fontUri', 'rx', 'ry', 'persp'])",
    "for (const k of ['fx', 'extrude', 'shape', 'real3d', 'slot', 'reflect', 'animators', 'kmPins', 'fontUri', 'rx', 'ry', 'persp', 'xo', 'org'])")
rep("window.__studio = { recipeLoad: () => recipeLoad,", "window.__studio = { xo: { setXf: (...a) => setXf(...a), mode: v => { if (v !== undefined) xoMode = !!v; return xoMode; }, setOrigin, bakeOffset, xformAt, xformRaw, applyXf, pivotScreen, blockSize }, recipeLoad: () => recipeLoad,")
open(dst, 'w').write(s)
print('patched', dst)
