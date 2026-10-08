"""Kinekit Studio patch 05: continuous Angle keys in the KineMaster export.

The exporter folded every angle into 0..360 (finalize, layer offsets, the KineMaster bake), so a wobble or a tilt
through 0 degrees was written as e.g. 0.7, 359.6, 0.5. The Studio preview interpolates angles the short way, so it
looked right, but KineMaster interpolates the stored numbers literally and spins the layer almost a full turn between
those keys. Fix: in cleanKfs (the one gate every layer's keyframes pass before they are encoded) the angles become one
continuous signed curve: the first key in -180..180, each next key the equivalent angle nearest to the previous one.
Tiny float noise (|angle| < 0.01) is snapped to 0, so layers that never turn carry a clean 0.

    python3 05_continuous_angle_keys.py IN.html OUT.html
"""
import sys
src, dst = sys.argv[1:3]
s = open(src, encoding='utf-8').read()
old = """  if (out[0].t > 0) out[0] = Object.assign({}, out[0], { t: 0 });
  return out;
}"""
new = """  if (out[0].t > 0) out[0] = Object.assign({}, out[0], { t: 0 });
  return continuousRot(out);
}
/* KineMaster interpolates Angle keys as plain numbers (no short-way wrap): write one continuous signed curve, the first
   key in -180..180 and every next key the equivalent angle nearest to the previous one (359.6 after 0.7 becomes -0.4) */
function continuousRot(kfs) {
  let prev = null;
  return kfs.map(k => {
    let r = finite(k.rot, 0);
    if (prev === null) r = ((r + 180) % 360 + 360) % 360 - 180;
    else { while (r - prev > 180) r -= 360; while (r - prev < -180) r += 360; }
    if (Math.abs(r) < 0.01) r = 0;
    r = Math.round(r * 1000) / 1000; prev = r;
    return r === k.rot ? k : Object.assign({}, k, { rot: r });
  });
}"""
assert s.count(old) == 1, 'cleanKfs anchor not found'
s = s.replace(old, new)
if 'K.continuousRot' not in s:
    s = s.replace('K.MIRROR_METHODS = MIRROR_METHODS;', 'K.MIRROR_METHODS = MIRROR_METHODS; K.continuousRot = continuousRot;', 1)
open(dst, 'w', encoding='utf-8').write(s)
print('patched', dst)
