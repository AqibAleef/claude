"""Kinekit Studio: smooth video playback in the preview (no flicker).   python3 patch_vplay.py IN.html OUT.html
Before: every drawn frame seeked each visible clip to its exact time; while the seek ran the clip had no frame, so the
layer was skipped and blinked. Now clips really play during playback (only re-synced when they drift), a clip that
isn't ready keeps showing its last good frame, and clips are paused when playback stops or they leave the screen.
Scrubbing, stepping and offline renders still seek frame-accurately."""
import sys
src, dst = sys.argv[1:3]; s = open(src).read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]; s = s.replace(a, b)
rep("""function videoFrame(L, b) {
  const v = vids.get(L.vid.id); if (!v) return null;
  const want = Math.min(Math.max(0, clipTime(b, T)), Math.max(0, v.dur - 0.04));
  if (Math.abs(v.el.currentTime - want) > 0.02 && !v.busy) { v.busy = true; v.el.currentTime = want; }
  return v.el.readyState >= 2 ? v.el : null;
}""", """function videoFrame(L, b) {
  const v = vids.get(L.vid.id); if (!v) return null;
  const el = v.el, want = Math.min(Math.max(0, clipTime(b, T)), Math.max(0, v.dur - 0.04)), now = performance.now();
  const live = playing && dir === 1 && !forceCv && !modal;          // real-time playback: let the clip run
  if (now - (v.usedAt || 0) < 4 && v.want !== undefined && Math.abs(v.want - want) > 0.05) return v.hold || null;   // same clip twice in one frame: don't fight over it
  v.usedAt = now; v.want = want;
  if (live) {
    const r = clamp((+b.video.speed || 1) * rate * speedAt(T), 0.0625, 16);
    if (Math.abs(el.playbackRate - r) > 1e-3) el.playbackRate = r;
    if (el.paused) { if (Math.abs(el.currentTime - want) > 0.06) el.currentTime = want; const p = el.play(); if (p && p.catch) p.catch(() => {}); }
    else if (Math.abs(el.currentTime - want) > 0.25 && !v.busy) { v.busy = true; el.currentTime = want; }   // drifted: re-sync once
  } else {
    if (!el.paused) el.pause();
    if (Math.abs(el.currentTime - want) > 0.02 && !v.busy) { v.busy = true; el.currentTime = want; }
  }
  if (el.readyState >= 2 && !el.seeking) { holdFrame(v); return el; }
  return v.hold || null;                                               // not ready: keep the last good frame on screen
}
/* a copy of the clip's last good frame, shown while it seeks (instead of a blank layer) */
function holdFrame(v) {
  const el = v.el; if (!el.videoWidth) return;
  const w = Math.min(el.videoWidth, 720), h = Math.round(w * el.videoHeight / el.videoWidth);
  if (!v.hold) v.hold = document.createElement('canvas');
  if (v.hold.width !== w || v.hold.height !== h) { v.hold.width = w; v.hold.height = h; }
  v.hold.getContext('2d').drawImage(el, 0, 0, w, h);
}
/* cue clips that come on screen in the next 0.6 s to their first frame, so they start clean (no stale frame) */
function prerollClips() {
  const now = performance.now();
  for (const b of state.blocks) {
    if (b.type !== 'video' || b.hidden) continue; const lead = b.start - T; if (!(lead > 0 && lead < 0.6)) continue;
    const v = vids.get(String(b.video.src).slice(4)); if (!v || v.busy || now - (v.usedAt || 0) < 150) continue;
    const want = Math.min(Math.max(0, +b.video.trimIn || 0), Math.max(0, v.dur - 0.04));
    if (Math.abs(v.el.currentTime - want) > 0.03) { if (!v.el.paused) v.el.pause(); v.busy = true; v.el.currentTime = want; v.hold = null; }
  }
}
function pauseIdleClips(force) { const now = performance.now(); for (const v of vids.values()) if (!v.el.paused && (force || now - (v.usedAt || 0) > 150)) v.el.pause(); }""")
rep("function pause() { playing = false; shuttleSpeed = 0; updPlayBtn(); musicStop(); }",
    "function pause() { playing = false; shuttleSpeed = 0; updPlayBtn(); musicStop(); pauseIdleClips(true); drawAll(); }")
rep("  musicTick(); followPlayhead(); drawAll(); requestAnimationFrame(tick);\n}",
    "  musicTick(); followPlayhead(); drawAll(); pauseIdleClips(false); prerollClips(); requestAnimationFrame(tick);\n}")
rep("window.__studio = { xo:", "window.__studio = { play: d => play(d), pause: () => pause(), playing: () => playing, xo:")
open(dst, 'w').write(s); print('patched', dst)
