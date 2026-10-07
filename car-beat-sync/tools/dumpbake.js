const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [recipe, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.goto('file://' + path.resolve(__dirname, 'studio.html'));
  await p.waitForFunction(() => window.__studio, null, { timeout: 60000 });
  await p.evaluate(s => window.__studio.fromRecipe(JSON.parse(s)), fs.readFileSync(recipe, 'utf8'));
  await p.waitForTimeout(4000);
  const r = await p.evaluate(() => { const S = window.__studio; S.bakeAll(); const o = []; void S; for (const [id, r] of S.baked) for (const L of r.layers) o.push({ id, kind: L.kind, role: L.role, text: L.text, start: L.start, end: L.end, kfs: L.kfs, pins: L.pins || null, box: (L.kind === 'text' ? S.K.boxPx(L.text || ' ') : L.kind === 'shape' ? [S.K.SHAPE_W(), S.K.SHAPE_H()] : [L.natW || 100, L.natH || 100]), fadeIn: L.fadeIn, fadeOut: L.fadeOut, alpha: L.alpha }); return o; });
  fs.writeFileSync(out, JSON.stringify(r)); console.log('layers', r.length); await b.close();
})();
