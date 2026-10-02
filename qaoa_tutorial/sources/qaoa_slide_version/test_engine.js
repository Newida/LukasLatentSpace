const fs = require('fs');
const data = JSON.parse(fs.readFileSync(__dirname + '/data.json', 'utf8'));
const SLIDE = { s: data.s, levels: data.levels, dists: data.dists };
const api = new Function('SLIDE', 'TUNED', fs.readFileSync(__dirname + '/engine.js', 'utf8') + '; return { PRISM, qaoaRun, ramp, bestT, slideCurve, slideStats, MIN_GAP, sliceLimit };')(SLIDE, data.tuned);
const { PRISM, qaoaRun, ramp, bestT, slideStats, MIN_GAP } = api;
let fails = 0;
const check = (label, got, want, tol) => { const ok = Math.abs(got - want) <= tol; if (!ok) fails++; console.log(`${ok ? 'ok  ' : 'FAIL'} ${label}: ${got.toFixed(4)} (python ${want})`); };
let nmax = 0; for (let x = 0; x < 64; x++) if (PRISM.C[x] === 7) nmax++;
check('number of maximum cuts', nmax, 6, 0);
check('T = 0 is random guessing, P(max)', ramp(4, 0).pmax, 0.09375, 1e-12);
check('T = 0 expected cut', ramp(4, 0).mean, 4.5, 1e-12);
check('ramp p=4 T=4.65 P', ramp(4, 4.65).pmax, 0.7505, 1e-4);
check('ramp p=4 T=4.65 E', ramp(4, 4.65).mean, 6.6320, 1e-4);
check('ramp p=40 T=20 P', ramp(40, 20).pmax, 0.9709, 1e-4);
check('ramp p=40 T=20 E', ramp(40, 20).mean, 6.9706, 1e-4);
check('ramp p=1 T=0.9 P', ramp(1, 0.9).pmax, 0.3478, 1e-4);
check('ramp p=8 T=9.65 P', ramp(8, 9.65).pmax, 0.9193, 1e-4);
for (const [T, P] of [[2, 0.3504], [5, 0.6500], [10, 0.8943], [40, 0.9943]]) check(`fine slide p=40 T=${T}`, ramp(40, T).pmax, P, 1e-4);
const tunedP = [0.4008, 0.7209, 0.9233, 0.9892, 0.9995, 1.0, 1.0, 1.0];
data.tuned.forEach((t, i) => { const r = qaoaRun(t.gamma, t.beta); check(`tuned p=${t.p} P`, r.pmax, tunedP[i], 2e-4); check(`tuned p=${t.p} E`, r.mean, t.E, 2e-4); });
const table = { 1: 0.348, 2: 0.397, 3: 0.511, 4: 0.750, 6: 0.893, 8: 0.919 };
for (const p of [1, 2, 3, 4, 6, 8]) { const b = bestT(p, 20, 0.05); check(`best slide p=${p} (T=${b.T.toFixed(2)})`, b.pmax, table[p], 2e-3); }
check('min gap on the slide', MIN_GAP.gap, 0.9786, 2e-3);
check('min gap position s', MIN_GAP.s, 0.96, 1e-9);
for (const [k, P, E] of [[0, 0.094, 4.5], [25, 0.139, 4.854], [50, 0.266, 5.490], [75, 0.627, 6.495], [100, 1.0, 7.0]]) { const st = slideStats(k); check(`ground state s=${data.s[k]} P`, st.pmax, P, 1e-3); check(`ground state s=${data.s[k]} E`, st.mean, E, 1e-3); }
const t0 = Date.now(); for (let p = 1; p <= 8; p++) { api.slideCurve(p, 20, 0.05); bestT(p, 20, 0.05); } api.slideCurve(40, 20, 0.1);
console.log(`curves for p = 1..8 plus the fine slide: ${Date.now() - t0} ms`);
console.log(fails ? `${fails} FAILED` : 'all checks passed');
process.exit(fails ? 1 : 0);
