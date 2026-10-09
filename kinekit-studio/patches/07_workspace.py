"""Kinekit Studio patch 07: an organised workspace.

- Start screen: continue, new project by shape, open a file, and one demo project per feature (kinetic type, 3D text,
  shapes & HUD, camera fly-through / crane / orbit / whip pans, photo album template, effects, Magic Remover depth,
  beat sync with a generated drum track - no third-party media inside the app).
- Top bar: the project button (title, shape, length; opens Project settings in a dialog), Edit / Animate / Export
  modes, and command search (Ctrl+K) over every command, effect and demo.
- Properties: labelled tabs (Transform, Text / Photo / Clip..., Animate, 3D, Template, Camera) over the layer name;
  the explanation paragraphs are folded away behind an (i) toggle. Project settings leave the panel.
- Export mode: a live check of the project (missing photos or clips, soft photos, music, Magic Remover, hidden layers,
  template slots, size) with one-click fixes; the right panel holds the export buttons and KineMaster settings; the left
  panel shows the template slots.

    python3 07_workspace.py IN.html OUT.html [THUMBS_DIR]
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
/* ---------- workspace (patch 07): modes, project button, search, start screen, export check */
.right { flex-direction: column; }
.ptabsv { width: auto; flex-direction: row; align-items: stretch; border-right: 0; border-bottom: 1px solid var(--line); padding: 0 4px; gap: 0; overflow-x: auto; scrollbar-width: none; background: var(--panel); min-height: 34px; }
.ptabsv::-webkit-scrollbar { display: none; }
.ptabsv button { width: auto; height: 34px; padding: 0 9px; display: flex; align-items: center; gap: 6px; font: 600 12px var(--f-ui); color: var(--muted); border-radius: 0; background: transparent; white-space: nowrap; }
.ptabsv button:hover { color: var(--text); background: transparent; }
.ptabsv button[aria-selected=true] { color: var(--text); background: transparent; box-shadow: inset 0 -2px 0 var(--accent); }
.ptabsv .pcol { width: 30px; padding: 0; justify-content: center; color: var(--faint); flex: none; }
.ptabsv .pcol[aria-pressed=true] { color: var(--cam); }
body:not(.helpon) #pbody p.desc:not([id]), body:not(.helpon) #pbody .okmsg, body:not(.helpon) #projBody p.desc:not([id]), body:not(.helpon) #projBody .okmsg { display: none; }
.homebtn { border: 0; background: transparent; cursor: pointer; color: var(--text); padding: 3px 6px; border-radius: var(--r); }
.homebtn:hover { background: var(--raise); }
.projbtn { display: flex; align-items: center; gap: 8px; margin-left: 10px; height: 24px; padding: 0 9px; border-radius: var(--r); border: 1px solid var(--line-2); background: var(--panel-2); cursor: pointer; min-width: 0; max-width: 340px; flex: 0 1 auto; }
.projbtn:hover { background: var(--panel-3); }
.projbtn #projName { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
.projbtn .pmeta { font: 11px var(--f-mono); color: var(--muted); white-space: nowrap; }
.modeseg { flex: none; } .modeseg button { padding: 3px 14px; font-weight: 600; font-size: 12.5px; }
.modeseg button[aria-pressed=true] { background: var(--accent); color: var(--accent-ink); }
.cmdbtn { display: flex; align-items: center; gap: 8px; height: 24px; padding: 0 9px; border-radius: var(--r); border: 1px solid var(--line-2); background: var(--panel-2); color: var(--muted); cursor: pointer; margin-right: 6px; flex: none; }
.cmdbtn:hover { color: var(--text); }
.cmdbtn kbd, .hbar kbd { font: 10px var(--f-mono); border: 1px solid var(--line-2); border-radius: 3px; padding: 0 4px; }
.app:not([data-mode=export]) [data-ltab=template] { display: none; }
.app[data-mode=export] #ptabs { display: none; }
#viewArea { position: relative; }
.kmodal { position: fixed; inset: 0; z-index: 80; background: rgb(5 6 8 / .55); display: flex; align-items: center; justify-content: center; padding: 16px; }
.kbox { width: min(560px, 100%); max-height: min(88vh, 900px); display: flex; flex-direction: column; background: var(--panel); border: 1px solid var(--line-2); border-radius: 10px; box-shadow: 0 24px 60px rgb(0 0 0 / .55); overflow: hidden; }
.khead { display: flex; align-items: center; gap: 8px; padding: 9px 10px 9px 14px; border-bottom: 1px solid var(--line); flex: none; }
.khead b { flex: 1; font-size: 14px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kbody { overflow: auto; min-height: 0; }
#cmdk { align-items: flex-start; } #cmdk .kbox { margin-top: 10vh; width: min(640px, 100%); }
.cmdin { width: 100%; border: 0; border-bottom: 1px solid var(--line); background: transparent; padding: 13px 16px; font-size: 15px; outline: none; flex: none; }
.cmdlist { overflow: auto; max-height: 56vh; padding: 6px; }
.cmdlist .cg { padding: 9px 10px 3px; font: 600 10.5px var(--f-ui); letter-spacing: .08em; text-transform: uppercase; color: var(--faint); }
.cmdlist .ci { display: flex; gap: 10px; align-items: center; width: 100%; border: 0; background: transparent; padding: 7px 10px; border-radius: 6px; text-align: left; cursor: pointer; color: var(--text); }
.cmdlist .ci.hot, .cmdlist .ci:hover { background: #3d5f9e; color: #fff; }
.cmdlist .ci .kb { margin-left: auto; font: 11px var(--f-mono); color: var(--faint); }
.cmdlist .ci.hot .kb { color: #dfe7ff; }
.cmdlist .none { padding: 16px; color: var(--muted); }
.xcheck { position: absolute; inset: 0; z-index: 7; background: var(--stage); overflow: auto; padding: 28px 20px; }
.xin { max-width: 780px; margin: 0 auto; display: grid; gap: 8px; }
.xtitle { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }
.xtitle b { font: 30px/1 var(--f-display); letter-spacing: .03em; } .xtitle span { color: var(--muted); }
.xrow { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 8px; background: var(--panel); border: 1px solid var(--line); }
.xrow > div { flex: 1; min-width: 0; display: grid; gap: 2px; } .xrow > div span { color: var(--muted); font-size: 12px; }
.xdot { width: 24px; height: 24px; flex: none; border-radius: 50%; display: grid; place-items: center; font-weight: 700; }
.xrow.ok .xdot { background: #1c3420; color: #9be89a; } .xrow.warn .xdot { background: #3a2a0e; color: #ffc870; }
.xrow.info .xdot { background: #1b2535; color: #9cc2ff; } .xrow.err .xdot { background: #3d1712; color: #ff8b78; }
.xbig { width: 100%; min-height: 34px; font-size: 13.5px; }
.home { position: fixed; inset: 0; z-index: 70; background: var(--bg); overflow: auto; }
.hbar { position: sticky; top: 0; display: flex; align-items: center; gap: 12px; padding: 0 20px; height: 52px; background: var(--panel); border-bottom: 1px solid var(--line); z-index: 1; }
.hbar .sub { color: var(--muted); } .hbar label { display: flex; align-items: center; gap: 6px; color: var(--muted); }
.hwrap { max-width: 1240px; margin: 0 auto; padding: 26px 24px 60px; display: grid; gap: 30px; }
.hwrap section { display: grid; gap: 12px; }
.hwrap h1, .hwrap h2 { margin: 0; font: 32px/1 var(--f-display); letter-spacing: .03em; font-weight: normal; } .hwrap h2 { font-size: 26px; }
.hhead { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; } .hhead span { color: var(--muted); }
.hstarts { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
.htile { display: grid; gap: 6px; justify-items: start; align-content: start; padding: 14px; border-radius: 10px; border: 1px solid var(--line); background: var(--panel); text-align: left; cursor: pointer; min-height: 104px; color: var(--text); }
.htile:hover { border-color: var(--accent); }
.htile .fr { border: 2px solid var(--accent); border-radius: 4px; margin-bottom: 4px; }
.htile b { font-size: 14px; } .htile span { color: var(--muted); font-size: 12px; }
.hchips { display: flex; gap: 6px; flex-wrap: wrap; }
.hchips button { height: 28px; padding: 0 12px; border-radius: 14px; border: 1px solid var(--line-2); background: transparent; color: var(--muted); font-weight: 600; cursor: pointer; }
.hchips button[aria-pressed=true] { border-color: var(--accent); color: #ffd2bd; background: color-mix(in srgb, var(--accent) 16%, transparent); }
.hgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 14px; }
.hcard { display: grid; align-content: start; padding: 0; border-radius: 12px; border: 1px solid var(--line); background: var(--panel); text-align: left; cursor: pointer; overflow: hidden; color: var(--text); }
.hcard:hover { border-color: var(--accent); }
.hthumb { position: relative; aspect-ratio: 4 / 3; background: #0b0b0d; overflow: hidden; display: block; }
.hthumb img { position: absolute; top: 0; height: 100%; left: 50%; transform: translateX(-50%); }
.hthumb img.wide { width: 100%; left: 0; transform: none; object-fit: cover; }
.hthumb .hph { position: absolute; inset: 0; display: grid; place-items: center; color: var(--faint); font: 26px var(--f-display); }
.hnew { position: absolute; left: 10px; top: 10px; background: var(--accent); color: var(--accent-ink); font: 700 10px var(--f-ui); letter-spacing: .06em; padding: 3px 7px; border-radius: 4px; }
.hasp { position: absolute; right: 10px; top: 10px; background: rgb(11 12 14 / .8); font: 10.5px var(--f-mono); padding: 2px 6px; border-radius: 4px; }
.hmeta { display: grid; gap: 3px; padding: 11px 12px 13px; }
.hmeta .f { color: #ff9a75; font: 700 10.5px var(--f-ui); letter-spacing: .06em; text-transform: uppercase; }
.hmeta b { font-size: 14.5px; } .hmeta span { color: var(--muted); font-size: 12px; }
"""
# the last </style> before the app markup
i = s.index('</style>', s.index('/* Kinekit Studio - pro editing suite layout.'))
s = s[:i] + CSS + s[i:]

# ---------------------------------------------------------------- top bar
sub('<div class="logo">KINEKIT <b>STUDIO</b></div>',
    '<button class="logo homebtn" id="homeLogo" title="All projects: start screen and demo projects">KINEKIT <b>STUDIO</b></button>')
sub('<input class="title-in" id="title" type="text" aria-label="Project title" value="">\n    <span class="chip" id="modeChip">9:16</span>\n    <span class="spacer"></span>',
    '<input class="title-in" id="title" type="text" aria-label="Project title" value="" hidden>\n    <span class="chip" id="modeChip" hidden>9:16</span>\n'
    '    <button class="projbtn" id="projBtn" title="Project settings: title, shape, length, background, music, KineMaster"><span id="projName">Untitled</span><span class="pmeta" id="projMeta"></span></button>\n'
    '    <span class="spacer"></span>\n'
    '    <div class="seg modeseg" id="modeSeg" role="group" aria-label="Workspace mode"><button data-mode="edit" aria-pressed="true" title="Build the scene">Edit</button><button data-mode="animate" aria-pressed="false" title="Keys, camera and the curve editor">Animate</button><button data-mode="export" aria-pressed="false" title="Check the project and export it">Export</button></div>\n'
    '    <span class="spacer"></span>\n'
    '    <button class="cmdbtn" id="cmdBtn" title="Search every command, effect and demo (Ctrl+K)"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="7" cy="7" r="4.5"/><path d="m10.5 10.5 3 3"/></svg>Search<kbd>Ctrl K</kbd></button>')

# ---------------------------------------------------------------- left tab names
sub('<button class="ptab" data-ltab="outliner" aria-selected="true">Outliner</button>', '<button class="ptab" data-ltab="outliner" aria-selected="true">Layers</button>')
sub('<button class="ptab" data-ltab="media" aria-selected="false">Project</button>', '<button class="ptab" data-ltab="media" aria-selected="false">Media</button>')

# ---------------------------------------------------------------- export check over the viewport, dialogs, start screen
sub('<main class="view" id="viewArea" data-area="viewport">', '<main class="view" id="viewArea" data-area="viewport">\n    <div class="xcheck" id="xcheck" hidden></div>')
sub('<div class="pop" id="pop" hidden></div>',
    '<div class="pop" id="pop" hidden></div>\n'
    '<div class="kmodal" id="projDlg" hidden><div class="kbox" role="dialog" aria-label="Project settings"><div class="khead"><b id="projHead">Project</b><button class="ibtn" id="projX" title="Close (Esc)" aria-label="Close">&times;</button></div><div class="kbody pscroll" id="projBody"></div></div></div>\n'
    '<div class="kmodal" id="cmdk" hidden><div class="kbox" role="dialog" aria-label="Search commands"><input class="cmdin" id="cmdIn" placeholder="Type a command, an effect or a demo project…" aria-label="Search commands" autocomplete="off" spellcheck="false"><div class="cmdlist" id="cmdList" role="listbox"></div></div></div>\n'
    '<div class="home" id="home" hidden></div>')

# ---------------------------------------------------------------- properties: labelled tabs, project settings in the dialog
sub("""  $('#ptabs').innerHTML = tabs.map(t => `<button role="tab" data-pt="${t}" aria-selected="${t === pTab}" title="${PTABS[t][0]}">${PTABS[t][1]}</button>`).join('') + `<span class="spacer"></span><button class="pcol" id="pCollapse" title="Collapse Properties (N over the viewport)">${IC.chevR}</button>`;
  $('#pCollapse').onclick = () => togglePanel('right', false);""",
    """  $('#ptabs').innerHTML = tabs.filter(t => t !== 'scene').map(t => `<button role="tab" data-pt="${t}" aria-selected="${t === pTab}" title="${PTABS[t][0]}">${esc(ptabLabel(t))}</button>`).join('') + `<span class="spacer"></span><button class="pcol" id="helpTog" aria-pressed="${!!ui.help}" title="${ui.help ? 'Hide' : 'Show'} the explanations">${IC_INFO}</button><button class="pcol" id="pCollapse" title="Collapse Properties (N over the viewport)">${IC.chevR}</button>`;
  $('#pCollapse').onclick = () => togglePanel('right', false);
  $('#helpTog').onclick = () => { ui.help = !ui.help; saveUi(); document.body.classList.toggle('helpon', !!ui.help); renderProps(); };""")
sub("""  if (pTab === 'scene') { H.innerHTML = `<span class="ty">Project</span><b>${esc(state.title || 'Untitled')}</b>`; P.innerHTML = sceneTabHtml(); wrapSecs(P); bindSceneTab(); return; }""",
    """  if (pTab === 'scene') {
    if (wsMode === 'export') { H.innerHTML = `<span class="ty">Export</span><b>KineMaster file</b>`; P.innerHTML = exportPanelHtml() + sceneTabHtml(); wrapSecs(P); bindSceneTab(); bindExportPanel(); return; }
    openProj(); const PB = $('#projBody'); $('#projHead').textContent = 'Project · ' + (state.title || 'Untitled'); PB.innerHTML = sceneTabHtml(); wrapSecs(PB); bindSceneTab();
    H.innerHTML = '<b>Project settings</b>'; P.innerHTML = `<div class="empty"><b>Project settings are open</b><span>Close the dialog to get back to the selected layer.</span></div>`; return;
  }""")

# with nothing selected, show "Nothing selected" (the old fallback was the Project tab, which is now a dialog)
sub("  if (!tabs.includes(pTab)) pTab = activeBlock() ? 'object' : S.cam ? 'camera' : 'scene';",
    "  if (!tabs.includes(pTab)) pTab = activeBlock() ? 'object' : S.cam ? 'camera' : wsMode === 'export' ? 'scene' : 'object';")

# blockSize (patch 03) read the picture of a photo / clip that may still be loading: fall back to the layer's box
sub("  if (b.type === 'photo' || b.type === 'video' || b.type === 'decor') { const g = itemPicture(b); return [g.w, g.h]; }",
    "  if (b.type === 'photo' || b.type === 'video' || b.type === 'decor') { let g = null; try { g = itemPicture(b); } catch (e) {} if (g && g.w) return [g.w, g.h]; const w = +b.w || ST.W / 2; return [w, +b.h || w * 9 / 16]; }")

# keep the project button and the export check current
sub("function bindProject() { $('#title').value = state.title || ''; applyAspect();", "function bindProject() { $('#title').value = state.title || ''; applyAspect(); updProjBtn();")
sub("""  $('#stats').innerHTML = `<b>${layers}</b> KineMaster layers · <b>${kfs}</b> keyframes · <b>${snd}</b> sounds`;""",
    """  $('#stats').innerHTML = `<b>${layers}</b> KineMaster layers · <b>${kfs}</b> keyframes · <b>${snd}</b> sounds`;
  updProjBtn(); if (wsMode === 'export') renderExportCheck();""")

# start screen after boot
sub("  T = 0; drawAll(); record(); updUndo();\n  if (hasAutosave) toast(",
    "  T = 0; drawAll(); record(); updUndo(); initWorkspace();\n  if (hasAutosave && ui.homeOff) toast(")

JS = r"""
// ================================================================== workspace (patch 07)
/* modes, the project button + dialog, command search, the start screen with demo projects, the export check */
let wsMode = 'edit', projPrevTab = 'object', wsPrevLeft = 'outliner', homeCat = 'All', cmdHot = 0, cmdRows = [];
const IC_INFO = '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><path d="M8 7.2v4M8 4.8v.4"/></svg>';
const PT_LABEL = { object: 'Transform', anim: 'Animate', d3: '3D', template: 'Template', camera: 'Camera' };
const CONTENT_LABEL = { text: 'Text', photo: 'Photo', video: 'Clip', decor: 'Shape', bg: 'Background', fx: 'Effect' };
function ptabLabel(t) { if (t === 'content') { const b = activeBlock(); return (b && CONTENT_LABEL[b.type]) || 'Content'; } return PT_LABEL[t] || (PTABS[t] ? PTABS[t][0] : t); }
function updProjBtn() {
  const n = document.getElementById('projName'), m = document.getElementById('projMeta'); if (!n || !state) return;
  n.textContent = state.title || 'Untitled'; m.textContent = `${ST.aspect} · ${fmt(projectLength(), 1)} s`;
}
function openProj() { $('#projDlg').hidden = false; }
function closeProj(silent) {
  const d = $('#projDlg'); if (d.hidden) return; d.hidden = true;
  if (pTab === 'scene' && wsMode !== 'export') { pTab = projPrevTab || 'object'; if (!silent) renderProps(); }
}
function openProjectSettings() { if (wsMode === 'export') return; if (pTab !== 'scene') projPrevTab = pTab; pTab = 'scene'; renderProps(); }
function setMode(m) {
  if (m === wsMode && m !== 'export') return;
  const was = wsMode; wsMode = m; $('#app').dataset.mode = m;
  $$('#modeSeg [data-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.mode === m)));
  if (m === 'export') {
    closeProj(true); if (ui.ltab !== 'template') wsPrevLeft = ui.ltab; setLeftTab('template');
    if (tlUi.graph) run('graph'); if (pTab !== 'scene') projPrevTab = pTab; pTab = 'scene';
  } else {
    if (ui.ltab === 'template') setLeftTab(wsPrevLeft || 'outliner');
    if (was === 'export' && pTab === 'scene') pTab = projPrevTab || 'object';
    if (m === 'animate' && !tlUi.graph) run('graph');
    if (m === 'edit' && tlUi.graph) run('graph');
    if (m === 'animate') { if (activeBlock()) pTab = 'anim'; else if (!S.ids.size) selectCamera(); }
  }
  renderProps(); renderExportCheck(); drawAll();
}
function exportPanelHtml() {
  return `<section class="sec"><h2>Export</h2>
    <button class="btn primary xbig" id="xpKine">Export .kine for KineMaster</button>
    <div class="row"><button class="btn sm" id="xpRecipe">Save recipe (.json)</button><button class="btn sm" id="xpGuide">Template guide (.md)</button></div>
    <div class="row"><button class="btn sm ghost" id="xpCompat">KineMaster compatibility test</button></div></section>`;
}
function bindExportPanel() { const on = (id, a) => { const e = $('#' + id); if (e) e.onclick = () => run(a); }; on('xpKine', 'export'); on('xpRecipe', 'saveRecipe'); on('xpGuide', 'exportGuide'); on('xpCompat', 'compatTest'); }

// ---------------------------------------------------------------- export check
function exportChecks() {
  const out = [], all = state.blocks, bl = all.filter(b => !b.hidden);
  const show = id => () => { setMode('edit'); selectLayers([id]); };
  for (const b of bl) {
    if (b.type === 'photo' && String(b.photo && b.photo.src || '').startsWith('up:') && !media.has(b.photo.src.slice(3)))
      out.push(['err', `"${itemLabel(b)}" has no picture`, 'The photo is not stored in this browser. Upload it again.', 'Show', show(b.id)]);
    if (b.type === 'video') { const id = String(b.video && b.video.src || '').slice(4); if (!vids.get(id)) out.push(['err', `The clip of "${itemLabel(b)}" is not loaded`, 'Import the clip again so it can go into the .kine.', 'Show', show(b.id)]); }
  }
  const xs = 1080 / ST.W;     // KineMaster renders the 720-wide canvas at 1080
  for (const b of bl) {
    if (b.type !== 'photo' || !String(b.photo && b.photo.src || '').startsWith('up:')) continue;
    const c = media.get(b.photo.src.slice(3)); if (!c || !c.width) continue;
    const maxS = Math.max(1, ...(hasTk(b) ? b.tk.map(k => Math.abs(+k.s || 1)) : [1]));
    const ratio = (+b.w || 0) * maxS * xs / c.width;
    if (ratio > 1.25) out.push(['warn', `"${itemLabel(b)}" is enlarged ${ratio.toFixed(1)}×`, 'It will look soft on a phone. Use a bigger photo or show it smaller.', 'Show', show(b.id)]);
  }
  if (state.music && state.music.user && !musicBuf) out.push(['warn', 'The music is not in this browser', `"${state.music.user.name}" can only go into the .kine after importing it again.`, 'Import', () => run('importMusic')]);
  const mr = bl.filter(b => b.magic && b.magic.on);
  if (mr.length) {
    const nm = mr.filter(b => b.type === 'photo' && !(b.magic.mask && media.has(String(b.magic.mask).slice(3)))).length;
    out.push(nm ? ['info', `Magic remover on ${mr.length} layer${mr.length > 1 ? 's' : ''}`, `${nm} without a preview mask: KineMaster still cuts them out on the phone.`]
                : ['ok', `Magic remover on ${mr.length} layer${mr.length > 1 ? 's' : ''}`, 'KineMaster redoes the cut-out when a photo is replaced.']);
  }
  const r3 = bl.filter(b => b.type === 'text' && b.real3d && b.real3d.on).length;
  if (r3) out.push(['info', `${r3} real 3D text layer${r3 > 1 ? 's' : ''}`, 'Exported as pictures that keep the material, light and bevel.']);
  const hid = all.length - bl.length;
  if (hid) out.push(['info', `${hid} hidden layer${hid > 1 ? 's are' : ' is'} left out`, 'Show all (Alt+H) to include them.', 'Show all', () => run('unhideAll')]);
  const allSlots = bl.filter(b => b.slot && b.slot.on);
  for (const b of allSlots) { let iss = []; try { iss = slotIssues(b, allSlots) || []; } catch (e) {}
    for (const x of iss) if (x.lv === 'warn' || x.lv === 'err') out.push(['warn', `Template slot "${b.slot.label || itemLabel(b)}"`, x.msg, x.fix ? x.fix.label : 'Show', x.fix ? () => { x.fix.run(); renderExportCheck(); } : show(b.id)]); }
  const slots = allSlots.length;
  out.push(slots ? ['ok', `${slots} template slot${slots > 1 ? 's' : ''}`, 'Listed in the template guide for the people who use it.', 'Guide', () => run('exportGuide')]
                 : ['info', 'No template slots', 'Mark the texts and photos people should replace (a layer\'s Template tab).']);
  out.push(['ok', 'Angle keys are written as smooth curves', 'No spins between 0° and 360° in KineMaster.']);
  out.push(['ok', 'Opacity is one value per layer', 'KineMaster cannot animate opacity; fades become its fade in / out.']);
  const st = $('#stats'); out.push(['info', 'Size', st ? st.textContent : '']);
  const rank = { err: 0, warn: 1, info: 2, ok: 3 }; return out.sort((a, b) => rank[a[0]] - rank[b[0]]);
}
function renderExportCheck() {
  const box = $('#xcheck'); if (!box) return; box.hidden = wsMode !== 'export'; if (box.hidden || !state) return;
  const L = exportChecks(), warn = L.filter(c => c[0] === 'warn').length, err = L.filter(c => c[0] === 'err').length, sym = { ok: '✓', warn: '!', info: 'i', err: '×' };
  const sumTxt = err ? `${err} problem${err > 1 ? 's' : ''} to fix first` : warn ? `${warn} thing${warn > 1 ? 's' : ''} worth fixing, nothing blocking` : 'nothing to fix';
  box.innerHTML = `<div class="xin"><div class="xtitle"><b>${err ? 'Fix before exporting' : 'Ready for KineMaster'}</b><span>${sumTxt}</span></div>` +
    L.map((c, i) => `<div class="xrow ${c[0]}"><span class="xdot">${sym[c[0]]}</span><div><b>${esc(c[1])}</b><span>${esc(c[2] || '')}</span></div>${c[3] ? `<button class="btn sm" data-xi="${i}">${esc(c[3])}</button>` : ''}</div>`).join('') + '</div>';
  $$('[data-xi]', box).forEach(btn => btn.onclick = () => L[+btn.dataset.xi][4]());
}

// ---------------------------------------------------------------- command search (Ctrl+K)
function cmdItems() {
  const keyOf = a => { const k = a.keys && a.keys[0] && a.keys[0][0]; return k ? (k.endsWith('++') ? k.slice(0, -2).split('+').concat('+') : k.split('+')).filter(Boolean).map(p => p.length === 1 ? p.toUpperCase() : p[0].toUpperCase() + p.slice(1)).join(' ') : ''; };
  const L = [['edit', 'Edit'], ['animate', 'Animate'], ['export', 'Export']].map(([m, n]) => ({ name: 'Mode: ' + n, group: 'Workspace', run: () => setMode(m) }));
  L.push({ name: 'Start screen: all projects and demos', group: 'Workspace', run: showHome }, { name: 'Project settings', group: 'Workspace', run: openProjectSettings });
  for (const d of DEMOS) L.push({ name: d.name + ' (' + d.feat.toLowerCase() + ')', group: 'Demo projects', run: () => openDemo(d) });
  for (const [k, a] of Object.entries(ACT)) if (a && a.label && typeof a.run === 'function') L.push({ name: a.label, group: 'Commands', key: keyOf(a), run: () => run(k), enabled: a.enabled });
  for (const id of Object.keys(KFX.LIB)) L.push({ name: 'Add effect: ' + KFX.LIB[id].name, group: 'Effects', run: () => addFx(id) });
  return L;
}
function renderCmd() {
  const q = $('#cmdIn').value.toLowerCase().split(/\s+/).filter(Boolean);
  cmdRows = cmdItems().filter(c => { try { if (c.enabled && !c.enabled()) return false; } catch (e) {} const t = (c.name + ' ' + c.group).toLowerCase(); return q.every(w => t.includes(w)); }).slice(0, 80);
  cmdHot = Math.min(cmdHot, Math.max(0, cmdRows.length - 1));
  let g = '', html = '';
  cmdRows.forEach((c, i) => { if (c.group !== g) { g = c.group; html += `<div class="cg">${esc(g)}</div>`; } html += `<button class="ci ${i === cmdHot ? 'hot' : ''}" data-ci="${i}" role="option"><span>${esc(c.name)}</span>${c.key ? `<span class="kb">${esc(c.key)}</span>` : ''}</button>`; });
  $('#cmdList').innerHTML = html || '<div class="none">Nothing matches. Try fewer words.</div>';
  $$('[data-ci]', $('#cmdList')).forEach(b => { b.onclick = () => runCmd(+b.dataset.ci); b.onmousemove = () => { if (cmdHot !== +b.dataset.ci) { cmdHot = +b.dataset.ci; $$('.ci', $('#cmdList')).forEach(x => x.classList.toggle('hot', +x.dataset.ci === cmdHot)); } }; });
  const hot = $('#cmdList .ci.hot'); if (hot) hot.scrollIntoView({ block: 'nearest' });
}
function openCmd() { const k = $('#cmdk'); k.hidden = false; $('#cmdIn').value = ''; cmdHot = 0; renderCmd(); setTimeout(() => $('#cmdIn').focus(), 0); }
function closeCmd() { $('#cmdk').hidden = true; }
function runCmd(i) { const c = cmdRows[i]; closeCmd(); if (c) setTimeout(() => c.run(), 0); }

// ---------------------------------------------------------------- demo projects: one per feature, no third-party media inside
function finishDemo(t = 1.2) {
  camSel = -1; shakeSel = -1; bakeAll(); state.blocks.forEach(b => b.type === 'text' && queue3d(b, 0));
  S.ids.clear(); S.cam = false; S.keys.clear(); S.kind = 'layers'; setActive(null);
  bindProject(); renderOutliner(); renderProps(); updateStats(); setTime(Math.min(t, projectLength())); saveSoon(); drawAll();
}
function demoState(aspect, title, dur, bg) { if (base) closeBase(); K.setStage(aspect); state = blankState(); state.title = title; state.duration = dur; if (bg) state.bg = bg; return state; }
function demo3d() {
  demoState('9:16', 'Chrome Logo Reveal', 4, '#0B0C10');
  const a = newBlock({ text: 'CHROME', x: CX(), y: 560, size: 7, start: 0, end: 4, style: 'cinematic' }); Object.assign(a.real3d, { on: true, material: 'chrome', depth: 0.55, tiltX: -10, tiltY: 22 });
  const b = newBlock({ text: 'LOGO REVEAL', x: CX(), y: 770, size: 3.2, start: 0.4, end: 4, style: 'cinematic' }); Object.assign(b.real3d, { on: true, material: 'gold', depth: 0.3, tiltX: -8, tiltY: 12 });
  state.blocks.push(a, b); finishDemo(2.4);
}
function demoFx() {
  loadScene('orbit'); state.title = 'Retro Look';
  for (const id of ['gradientMap', 'enhancedLights', 'grain', 'vignetting']) if (KFX.LIB[id]) addFx(id);
  finishDemo(3);
}
/* a stand-in portrait (warm backdrop + a person-shaped subject) and its cut-out mask, drawn here so the demo works
   before you add a photo of your own */
function demoPortrait() {
  const W = 1280, H = 720, mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; }, c = mk(), m = mk(), g = c.getContext('2d');
  const sky = g.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#F5C38A'); sky.addColorStop(0.55, '#E9806A'); sky.addColorStop(1, '#5A3A66'); g.fillStyle = sky; g.fillRect(0, 0, W, H);
  g.fillStyle = 'rgba(255,244,214,0.92)'; g.beginPath(); g.arc(W * 0.74, H * 0.34, 74, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#4C3158'; g.beginPath(); g.moveTo(0, H * 0.8); g.bezierCurveTo(W * 0.3, H * 0.68, W * 0.62, H * 0.88, W, H * 0.74); g.lineTo(W, H); g.lineTo(0, H); g.closePath(); g.fill();
  const person = ctx => {
    const x = W * 0.42; ctx.beginPath(); ctx.ellipse(x, H * 0.31, 58, 68, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillRect(x - 26, H * 0.38, 52, H * 0.08);
    ctx.beginPath(); ctx.moveTo(x - 36, H * 0.44); ctx.bezierCurveTo(x - 150, H * 0.47, x - 196, H * 0.6, x - 210, H); ctx.lineTo(x + 210, H); ctx.bezierCurveTo(x + 196, H * 0.6, x + 150, H * 0.47, x + 36, H * 0.44); ctx.closePath(); ctx.fill();
  };
  const body = g.createLinearGradient(W * 0.3, H * 0.2, W * 0.55, H); body.addColorStop(0, '#3A2C4E'); body.addColorStop(1, '#17121F'); g.fillStyle = body; person(g);
  const mg = m.getContext('2d'); mg.fillStyle = '#FFFFFF'; person(mg);
  return { c, m };
}
function demoMagic() {
  demoState('16:9', 'Depth with Magic Remover', 5, '#0E0F12');
  const P = demoPortrait(); media.set('demo_portrait', P.c); media.set('demo_portrait_mask', P.m);
  P.c.toBlob(bl => { if (bl) idb.put('demo_portrait', bl); }, 'image/jpeg', 0.9); P.m.toBlob(bl => { if (bl) idb.put('demo_portrait_mask', bl); }, 'image/png');
  const ph = (name, extra) => newItem('photo', Object.assign({ name, x: CX(), y: CY(), w: ST.W, depth: 0, start: 0, end: 5, photo: { src: 'up:demo_portrait', aspect: 'orig', raw: true, border: 0, shadow: 0, reflect: 0 }, slot: { on: true, label: 'Portrait' }, in: null, out: null }, extra));
  const back = ph('Portrait · blurred background', { clipBlur: 6, slot: { on: true, label: 'Portrait · background' } });
  const word = newBlock({ text: 'SUMMER', x: Math.round(ST.W * 0.55), y: Math.round(ST.H * 0.36), size: 13, start: 0.3, end: 5, style: 'cinematic', color: '#FFF4E0' });
  const top = ph('Portrait · cut-out', { slot: { on: true, label: 'Portrait · cut-out' }, magic: { on: true, mask: 'up:demo_portrait_mask', how: 'recipe', for: 'up:demo_portrait' } });
  state.blocks.push(back, word, top); finishDemo(2);
  toast('The stand-in person is already cut out, so SUMMER sits behind them. Upload your own photo on both photo layers: Magic remover finds the subject, and KineMaster cuts it out again on the phone.', false, 9000);
}
/* a 12 s, 128 BPM drum track made right here (kick, clap, hats, a drop at 3.75 s), so the beat demo needs no music file */
function demoBeatWav() {
  const sr = 22050, dur = 12, bpm = 128, beat = 60 / bpm, n = sr * dur, a = new Float32Array(n);
  let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) * 2 - 1;
  const add = (t0, len, f) => { const i0 = Math.round(t0 * sr), m = Math.round(len * sr); for (let i = 0; i < m && i0 + i < n; i++) a[i0 + i] += f(i / sr); };
  const drop = 4 * beat * 2;      // two bars of intro
  for (let k = 0; k * beat < dur; k++) {
    const t = k * beat, strong = t >= drop - 1e-6;
    add(t, 0.32, x => Math.sin(2 * Math.PI * (45 + 90 * Math.exp(-x * 28)) * x) * Math.exp(-x * 9) * (strong ? 0.9 : 0.45));
    if (strong && k % 2 === 1) add(t, 0.18, x => rnd() * Math.exp(-x * 26) * 0.55);
    for (const h of [0, 0.5]) add(t + h * beat, 0.04, x => rnd() * Math.exp(-x * 120) * (strong ? 0.22 : 0.12));
  }
  for (let i = 0; i < Math.round(drop * sr); i++) { const x = i / sr; a[i] += Math.sin(2 * Math.PI * 110 * x) * 0.05 * (x / drop); }
  let pk = 0; for (const v of a) pk = Math.max(pk, Math.abs(v)); const g = 0.9 / (pk || 1);
  const buf = new ArrayBuffer(44 + n * 2), dv = new DataView(buf), w = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
  w(0, 'RIFF'); dv.setUint32(4, 36 + n * 2, true); w(8, 'WAVE'); w(12, 'fmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
  dv.setUint32(24, sr, true); dv.setUint32(28, sr * 2, true); dv.setUint16(32, 2, true); dv.setUint16(34, 16, true); w(36, 'data'); dv.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) dv.setInt16(44 + i * 2, Math.max(-1, Math.min(1, a[i] * g)) * 32767, true);
  return new Uint8Array(buf);
}
async function demoBeat() {
  demoState('9:16', 'Beat Sync Reel', 12, '#08080A');
  const bar = 4 * 60 / 128;
  for (let i = 0; i < 6; i++) state.blocks.push(newItem('photo', { name: 'Shot ' + (i + 1), x: CX(), y: CY(), w: Math.round(ST.W * 1.08), depth: 0, start: +(i * bar).toFixed(3), end: +((i + 1) * bar).toFixed(3), photo: { src: 'ph:' + (i % 12 + 1), aspect: '9:16', border: 0, shadow: 0, reflect: 0 }, slot: { on: true, label: 'Shot ' + (i + 1) }, in: { preset: 'punch_in', dur: 0.3 }, out: null }));
  state.blocks.push(newBlock({ text: 'TONIGHT', x: CX(), y: CY(), size: 9, start: +(2 * bar).toFixed(3), end: +(6 * bar).toFixed(3), style: 'beat_punch' }));
  state.showBeats = true; state.snapBeats = true; finishDemo(2 * bar + 0.1);
  const bytes = demoBeatWav();
  await importMusic({ name: 'demo_beat_128bpm.wav', type: 'audio/wav', arrayBuffer: async () => bytes.slice().buffer });
  rebakeBeats();
}
const DEMOS = [
  { id: 'kinetic', name: "Hello, I'm Your Name", feat: 'Kinetic typography', tags: 'Text styles · animators · in / loop / out presets', cat: 'Text', aspect: '9:16', load: () => loadScene('kinetic') },
  { id: 'text3d', name: 'Chrome Logo Reveal', feat: '3D text', tags: 'Real 3D letters · chrome and gold · bevel', cat: 'Text', aspect: '9:16', load: demo3d },
  { id: 'corporate', name: 'Clean Intro', feat: 'Shapes & HUD', tags: 'Data lines · plus marks · brackets · reflections', cat: 'Shapes', aspect: '9:16', load: () => loadScene('corporate') },
  { id: 'tunnel', name: 'Into the New Story', feat: 'Camera fly-through', tags: 'Scene camera · words in depth · impact shakes', cat: 'Camera', aspect: '9:16', load: () => loadScene('tunnel') },
  { id: 'crane', name: 'Big Story', feat: 'Crane + dolly zoom', tags: 'Layered type · crane up · vertigo', cat: 'Camera', aspect: '9:16', load: () => loadScene('crane') },
  { id: 'orbit', name: 'Your Title · Orbit', feat: '3D layout', tags: 'Photos around a title · orbit, then push in', cat: 'Camera', aspect: '9:16', load: () => loadScene('orbit') },
  { id: 'whip', name: 'One, Two, Three', feat: 'Whip pans', tags: 'Three panels · whip pans · shake hits', cat: 'Camera', aspect: '9:16', load: () => loadScene('whip') },
  { id: 'simple', name: 'Photo Album', feat: 'Photo cards & templates', tags: 'Borders · shadows · reflections · replaceable slots', cat: 'Photos', aspect: '9:16', load: () => loadScene('simple') },
  { id: 'fx', name: 'Retro Look', feat: 'Effects & adjustments', tags: 'Duotone · light rays · film grain · vignette', cat: 'Effects', aspect: '9:16', load: demoFx },
  { id: 'magic', name: 'Depth with Magic Remover', feat: 'Magic remover', tags: 'Cut-out on top · text behind · blurred copy below', cat: 'New', isNew: true, aspect: '16:9', load: demoMagic },
  { id: 'beat', name: 'Beat Sync Reel', feat: 'Beat sync', tags: 'Drum track made in the app · cuts on bars · beat punch', cat: 'New', isNew: true, aspect: '9:16', load: demoBeat }
];
const DEMO_THUMB = {};
async function openDemo(d) {
  hideHome(); closeCmd(); closeProj(true);
  try { await d.load(); } catch (e) { console.error(e); toast('That demo could not be opened: ' + (e.message || e), true); return; }
  state.title = d.name; bindProject(); setMode('edit'); saveSoon();
}

// ---------------------------------------------------------------- start screen
function renderHome() {
  const h = $('#home'), cats = ['All', 'New', ...new Set(DEMOS.map(d => d.cat).filter(c => c !== 'New'))];
  const tiles = [['9:16', 'Vertical 9:16', 'Reels · Shorts · Stories', 18, 32], ['16:9', 'Wide 16:9', 'YouTube · landscape', 36, 20], ['1:1', 'Square 1:1', 'Feed post', 28, 28]];
  const list = DEMOS.filter(d => homeCat === 'All' || d.cat === homeCat);
  h.innerHTML = `<div class="hbar"><span class="logo">KINEKIT <b>STUDIO</b></span><span class="sub">Motion graphics for KineMaster</span><span class="spacer"></span>
      <label><input type="checkbox" id="hOff" ${ui.homeOff ? '' : 'checked'}> Show at start</label>
      <button class="cmdbtn" id="hCmd">Search<kbd>Ctrl K</kbd></button><button class="btn" id="hBack">Back to the editor</button></div>
    <div class="hwrap">
      <section><h1>Start something</h1><div class="hstarts">
        ${hasAutosave ? `<button class="htile" data-hs="restore"><span class="fr" style="width:24px;height:24px;border-style:dashed"></span><b>Continue</b><span>Your last session</span></button>` : ''}
        ${tiles.map(([a, n, m, w, ht]) => `<button class="htile" data-hn="${a}"><span class="fr" style="width:${w}px;height:${ht}px"></span><b>${n}</b><span>${m}</span></button>`).join('')}
        <button class="htile" data-hs="open"><span class="fr" style="width:26px;height:22px"></span><b>Open a file</b><span>.kine from KineMaster or a recipe</span></button>
      </div></section>
      <section><div class="hhead"><h2>Feature demo projects</h2><span>One small project per feature: open one to see how it is built, then make it yours.</span></div>
        <div class="hchips">${cats.map(c => `<button data-hc="${c}" aria-pressed="${c === homeCat}">${c === 'New' ? 'New features' : c}</button>`).join('')}</div>
        <div class="hgrid">${list.map(d => `<button class="hcard" data-hd="${d.id}"><span class="hthumb">${DEMO_THUMB[d.id] ? `<img src="${DEMO_THUMB[d.id]}" alt="" class="${d.aspect === '16:9' ? 'wide' : ''}">` : `<span class="hph">${esc(d.feat)}</span>`}${d.isNew ? '<span class="hnew">NEW FEATURE</span>' : ''}<span class="hasp">${d.aspect}</span></span><span class="hmeta"><span class="f">${esc(d.feat)}</span><b>${esc(d.name)}</b><span>${esc(d.tags)}</span></span></button>`).join('')}</div>
      </section>
    </div>`;
  $('#hBack').onclick = hideHome; $('#hCmd').onclick = () => { hideHome(); openCmd(); };
  $('#hOff').onchange = e => { ui.homeOff = !e.target.checked; saveUi(); };
  $$('[data-hn]', h).forEach(b => b.onclick = () => { hideHome(); if (base) closeBase(); K.setStage(b.dataset.hn); newProject(); setMode('edit'); });
  $$('[data-hs]', h).forEach(b => b.onclick = () => { hideHome(); run(b.dataset.hs); });
  $$('[data-hc]', h).forEach(b => b.onclick = () => { homeCat = b.dataset.hc; renderHome(); });
  $$('[data-hd]', h).forEach(b => b.onclick = () => openDemo(DEMOS.find(d => d.id === b.dataset.hd)));
}
function showHome() { closeCmd(); renderHome(); $('#home').hidden = false; }
function hideHome() { $('#home').hidden = true; }

function initWorkspace() {
  const right = $('#right'); right.insertBefore($('#ihead'), $('#ptabs'));
  document.body.classList.toggle('helpon', !!ui.help);
  $('#homeLogo').onclick = showHome; $('#projBtn').onclick = openProjectSettings; $('#cmdBtn').onclick = openCmd;
  $('#projX').onclick = () => closeProj(); $('#projDlg').addEventListener('mousedown', e => { if (e.target.id === 'projDlg') closeProj(); });
  $('#cmdk').addEventListener('mousedown', e => { if (e.target.id === 'cmdk') closeCmd(); });
  $('#cmdIn').addEventListener('input', () => { cmdHot = 0; renderCmd(); });
  $$('#modeSeg [data-mode]').forEach(b => b.onclick = () => setMode(b.dataset.mode));
  $('#app').dataset.mode = wsMode;
  window.addEventListener('keydown', e => {
    const k = e.key;
    if ((e.ctrlKey || e.metaKey) && !e.altKey && k.toLowerCase() === 'k') { e.preventDefault(); e.stopPropagation(); if ($('#cmdk').hidden) openCmd(); else closeCmd(); return; }
    if (!$('#cmdk').hidden) {
      if (k === 'Escape') { closeCmd(); } else if (k === 'ArrowDown' || k === 'ArrowUp') { cmdHot = Math.max(0, Math.min(cmdRows.length - 1, cmdHot + (k === 'ArrowDown' ? 1 : -1))); renderCmd(); } else if (k === 'Enter') { runCmd(cmdHot); } else return;
      e.preventDefault(); e.stopPropagation(); return;
    }
    if (k === 'Escape' && !$('#projDlg').hidden) { e.preventDefault(); e.stopPropagation(); closeProj(); return; }
    if (k === 'Escape' && !$('#home').hidden && state && state.blocks.length) { e.preventDefault(); e.stopPropagation(); hideHome(); return; }
    if (!$('#home').hidden && !(e.target && e.target.closest && e.target.closest('input, textarea'))) { e.stopPropagation(); }
  }, true);
  updProjBtn();
  if (!ui.homeOff) showHome();
}
"""
sub("let hasAutosave = false;\nasync function boot() {", JS + "\nlet hasAutosave = false;\nasync function boot() {")

sub("window.__studio = { MR,", "window.__studio = { openDemo: id => openDemo(DEMOS.find(d => d.id === id)), demos: () => DEMOS.map(d => d.id), setMode, exportChecks, showHome, MR,")
# demo thumbnails (rendered by the Studio itself), embedded when a folder of <demo id>.jpg is given
if len(sys.argv) > 3:
    import base64, json, os
    th = {f[:-4]: 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(sys.argv[3], f), 'rb').read()).decode() for f in sorted(os.listdir(sys.argv[3])) if f.endswith('.jpg')}
    sub("const DEMO_THUMB = {};", "const DEMO_THUMB = " + json.dumps(th) + ";")
open(dst, 'w', encoding='utf-8').write(s)
print('patched', dst)
