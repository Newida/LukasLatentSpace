/* ---------- page: two toys ---------- */
const NS = 'http://www.w3.org/2000/svg';
const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const txt = (parent, x, y, s, cls, anchor) => { const t = el('text', { x, y, class: cls || 'lbl', 'text-anchor': anchor || 'middle' }, parent); t.textContent = s; return t; };
const $ = (id) => document.getElementById(id);
const pmaxOf = (p) => { let s = 0; for (let x = 0; x < PRISM.N; x++) if (PRISM.C[x] === PRISM.Cmax) s += p[x]; return s; };
const meanOf = (p) => { let s = 0; for (let x = 0; x < PRISM.N; x++) s += p[x] * PRISM.C[x]; return s; };

/* Toy 1: evolving a population on the prism */
const T1 = { g: 1, q: 0.05, mode: 'inf', size: 200, gen: 0, p: null, pop: null, M: null, pfix: null, traj: [], timer: null, pending: false };
const current = () => (T1.mode === 'inf' ? T1.p : populationDistribution(T1.pop));
function t1Recompute() { T1.M = mutationMatrix(T1.q); T1.pfix = quasispecies(T1.M, T1.g); }
function t1Reset() {
  T1.gen = 0;
  T1.p = new Float64Array(PRISM.N).fill(1 / PRISM.N);
  T1.pop = new Int32Array(T1.size).map(() => Math.floor(Math.random() * PRISM.N));
  T1.traj = [[0, pmaxOf(current())]];
  t1Draw();
}
function t1Step() {
  if (T1.mode === 'inf') T1.p = gaStep(T1.p, T1.M, T1.g);
  else T1.pop = finiteStep(T1.pop, T1.g, T1.q, Math.random);
  T1.gen += 1;
  T1.traj.push([T1.gen, pmaxOf(current())]);
  if (T1.traj.length > 61) T1.traj.shift();
  t1Draw();
}
function t1Draw() {
  const p = current();
  $('gaGen').textContent = String(T1.gen);
  $('gaPmax').textContent = pmaxOf(p).toFixed(3);
  $('gaPfix').textContent = pmaxOf(T1.pfix).toFixed(3);
  $('gaMean').textContent = meanOf(p).toFixed(2);
  // histogram of cut values
  const hs = $('gaHist'); hs.textContent = '';
  const h = cutHistogram(p), hf = cutHistogram(T1.pfix), K = PRISM.Cmax + 1;
  let top = 0.05; for (let c = 0; c < K; c++) top = Math.max(top, h[c], hf[c]);
  const x0 = 16, bw = (250 - x0) / K, base = 140;
  el('line', { x1: x0 - 4, x2: 254, y1: base, y2: base, class: 'base' }, hs);
  for (let c = 0; c < K; c++) {
    const hh = 118 * h[c] / top, hfh = 118 * hf[c] / top;
    el('rect', { x: x0 + c * bw + 3, y: base - hh, width: bw - 6, height: Math.max(hh, 0.5), class: c === PRISM.Cmax ? 'bar-n' : 'bar-p' }, hs);
    if (hfh > 0.3) el('rect', { x: x0 + c * bw + 1.5, y: base - hfh, width: bw - 3, height: hfh, class: 'ref' }, hs);
    txt(hs, x0 + c * bw + bw / 2, base + 14, String(c), 'lbl');
  }
  txt(hs, 254, 10, `max ${top.toFixed(2)}`, 'lbl', 'end');
  txt(hs, 133, 166, 'cut value', 'lbl');
  // P(max cut) per generation
  const ts = $('gaTraj'); ts.textContent = '';
  const L = 34, R = 250, TOP = 12, B = 140;
  const g0 = T1.traj[0][0], g1 = Math.max(g0 + 20, T1.traj[T1.traj.length - 1][0]);
  const X = (gen) => L + (R - L) * (gen - g0) / (g1 - g0), Y = (v) => B - (B - TOP) * v;
  [0, 0.5, 1].forEach((v) => { el('line', { x1: L, x2: R, y1: Y(v), y2: Y(v), class: 'grid' }, ts); txt(ts, L - 6, Y(v) + 4, v.toFixed(1), 'lbl', 'end'); });
  el('line', { x1: L, x2: R, y1: Y(pmaxOf(T1.pfix)), y2: Y(pmaxOf(T1.pfix)), class: 'ref' }, ts);
  el('line', { x1: L, x2: R, y1: Y(6 / 64), y2: Y(6 / 64), class: 'uni' }, ts);
  el('polyline', { points: T1.traj.map(([gg, v]) => `${X(gg).toFixed(1)},${Y(v).toFixed(1)}`).join(' '), class: 'trace' }, ts);
  const [lg, lv] = T1.traj[T1.traj.length - 1];
  el('circle', { cx: X(lg), cy: Y(lv), r: 3, class: 'dot' }, ts);
  txt(ts, L, B + 14, String(g0), 'lbl', 'start');
  txt(ts, R, B + 14, String(g1), 'lbl', 'end');
  txt(ts, (L + R) / 2, 166, 'generation', 'lbl');
}
function t1Sliders() {
  T1.g = $('gaGamma').value / 100; T1.q = $('gaQ').value / 1000;
  $('gaGammaOut').textContent = T1.g.toFixed(2); $('gaQOut').textContent = T1.q.toFixed(3);
  if (T1.pending) return;
  T1.pending = true;
  requestAnimationFrame(() => { T1.pending = false; t1Recompute(); t1Draw(); });
}
function t1SetMode(mode, size) {
  T1.mode = mode; T1.size = size;
  [['popInf', 'inf', 0], ['pop200', 'fin', 200], ['pop30', 'fin', 30]].forEach(([id, m, s]) => $(id).setAttribute('aria-pressed', String(m === mode && (m === 'inf' || s === size))));
  t1Reset();
}
function t1Run() {
  if (T1.timer) { clearInterval(T1.timer); T1.timer = null; $('gaRun').textContent = 'Run'; return; }
  T1.timer = setInterval(t1Step, 160); $('gaRun').textContent = 'Pause';
}

/* Toy 2: the error threshold on a needle */
const T2 = { n: 20, g: 1, job: 0, pts: [] };
function t2Inputs() {
  T2.n = +$('thN').value; T2.g = $('thG').value / 100;
  $('thNOut').textContent = String(T2.n); $('thGOut').textContent = T2.g.toFixed(2);
  const qc = 1 - Math.exp(-T2.g / T2.n), qmax = Math.min(0.5, 2.5 * qc), K = 80, job = ++T2.job;
  T2.pts = []; T2.qc = qc; T2.qmax = qmax;
  $('thQc').textContent = qc.toFixed(4);
  $('thBelow').textContent = masterShare(T2.n, T2.g, qc / 2).toFixed(3);
  $('thAbove').textContent = masterShare(T2.n, T2.g, 1.25 * qc).toFixed(4);
  $('thUni').textContent = Math.pow(2, -T2.n).toExponential(1);
  let i = 0;
  const chunk = () => {
    if (job !== T2.job) return;
    for (let c = 0; c < 10 && i < K; c++, i++) { const q = qmax * i / (K - 1); T2.pts.push([q, masterShare(T2.n, T2.g, q)]); }
    t2Draw();
    if (i < K) requestAnimationFrame(chunk);
  };
  requestAnimationFrame(chunk);
}
function t2Draw() {
  const s = $('thPlot'); s.textContent = '';
  const L = 56, R = 500, TOP = 16, B = 196;
  const X = (q) => L + (R - L) * q / T2.qmax, Y = (v) => B - (B - TOP) * v;
  [0, 0.5, 1].forEach((v) => { el('line', { x1: L, x2: R, y1: Y(v), y2: Y(v), class: 'grid' }, s); txt(s, L - 8, Y(v) + 4, v.toFixed(1), 'lbl', 'end'); });
  [0, 0.5, 1].forEach((f) => txt(s, L + (R - L) * f, B + 16, (T2.qmax * f).toFixed(3), 'lbl'));
  el('line', { x1: X(T2.qc), x2: X(T2.qc), y1: TOP, y2: B, class: 'qline' }, s);
  txt(s, X(T2.qc) + 6, TOP + 12, 'q_c', 'lbl-ink', 'start');
  if (T2.pts.length > 1) el('polyline', { points: T2.pts.map(([q, v]) => `${X(q).toFixed(1)},${Y(v).toFixed(1)}`).join(' '), class: 'trace' }, s);
  txt(s, (L + R) / 2, B + 34, 'mutation rate q', 'lbl');
  const t = txt(s, 16, (TOP + B) / 2, 'P(master)', 'lbl');
  t.setAttribute('transform', `rotate(-90 16 ${(TOP + B) / 2})`);
}

/* wiring */
$('gaGamma').addEventListener('input', t1Sliders);
$('gaQ').addEventListener('input', t1Sliders);
$('popInf').addEventListener('click', () => t1SetMode('inf', 0));
$('pop200').addEventListener('click', () => t1SetMode('fin', 200));
$('pop30').addEventListener('click', () => t1SetMode('fin', 30));
$('gaStep').addEventListener('click', t1Step);
$('gaRun').addEventListener('click', t1Run);
$('gaReset').addEventListener('click', t1Reset);
$('thN').addEventListener('input', t2Inputs);
$('thG').addEventListener('input', t2Inputs);
T1.g = $('gaGamma').value / 100; T1.q = $('gaQ').value / 1000;
$('gaGammaOut').textContent = T1.g.toFixed(2); $('gaQOut').textContent = T1.q.toFixed(3);
t1Recompute(); t1Reset();
t2Inputs();
