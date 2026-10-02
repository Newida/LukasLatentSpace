/* ---------- engine: exact simulation on the prism (expects SLIDE and TUNED) ---------- */
const PRISM = (() => {
  const n = 6, N = 64;
  const E = [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3], [0, 3], [1, 4], [2, 5]];
  const C = new Float64Array(N);
  for (let x = 0; x < N; x++) for (const [i, j] of E) if (((x >> i) & 1) !== ((x >> j) & 1)) C[x] += 1;
  let Cmax = 0; for (let x = 0; x < N; x++) Cmax = Math.max(Cmax, C[x]);
  return { n, N, E, C, Cmax };
})();

// Layer k applies exp(-i gamma_k H_C) = exp(i gamma_k C), then exp(-i beta_k H_B) = exp(i beta_k sum_j X_j).
function qaoaRun(gammas, betas) {
  const { n, N, C, Cmax } = PRISM;
  const re = new Float64Array(N).fill(1 / Math.sqrt(N)), im = new Float64Array(N);
  for (let k = 0; k < gammas.length; k++) {
    for (let x = 0; x < N; x++) {
      const c = Math.cos(gammas[k] * C[x]), s = Math.sin(gammas[k] * C[x]), r = re[x], m = im[x];
      re[x] = r * c - m * s; im[x] = r * s + m * c;
    }
    const cb = Math.cos(betas[k]), sb = Math.sin(betas[k]);
    for (let j = 0; j < n; j++) {
      const bit = 1 << j;
      for (let x = 0; x < N; x++) {
        if (x & bit) continue;
        const y = x | bit, ar = re[x], ai = im[x], br = re[y], bi = im[y];
        re[x] = cb * ar - sb * bi; im[x] = cb * ai + sb * br;
        re[y] = cb * br - sb * ai; im[y] = cb * bi + sb * ar;
      }
    }
  }
  let mean = 0, pmax = 0;
  for (let x = 0; x < N; x++) { const pr = re[x] * re[x] + im[x] * im[x]; mean += pr * C[x]; if (C[x] === Cmax) pmax += pr; }
  return { mean, pmax };
}

// The chopped slide: p pieces of length T / p, with s_k = (k - 1/2) / p in the middle of piece k.
function rampAngles(p, T) {
  const g = [], b = [];
  for (let k = 1; k <= p; k++) { const s = (k - 0.5) / p; g.push(s * T / p); b.push((1 - s) * T / p); }
  return { g, b };
}
function ramp(p, T) { const { g, b } = rampAngles(p, T); return qaoaRun(g, b); }

// Pieces longer than pi/2 make the mixer angle wrap around; beyond that the circuit is no slide anymore.
const sliceLimit = (p) => p * Math.PI / 2;
function slideCurve(p, Tmax, dT) {
  const pts = [];
  for (let T = 0; T <= Tmax + 1e-9; T += dT) pts.push([T, ramp(p, T).pmax]);
  return pts;
}
function bestT(p, Tmax, dT) {
  let best = { T: 0, pmax: -1 };
  for (let T = 0; T <= Math.min(Tmax, sliceLimit(p)) + 1e-9; T += dT) {
    const v = ramp(p, T).pmax;
    if (v > best.pmax) best = { T, pmax: v };
  }
  return best;
}

const slideStats = (k) => {
  const d = SLIDE.dists[k];
  let mean = 0; for (let c = 0; c < d.length; c++) mean += c * d[c];
  return { gap: SLIDE.levels[k][1] - SLIDE.levels[k][0], pmax: d[PRISM.Cmax], mean };
};
const MIN_GAP = (() => {
  let best = { gap: Infinity, s: 0 };
  SLIDE.s.forEach((s, k) => { const g = SLIDE.levels[k][1] - SLIDE.levels[k][0]; if (g < best.gap) best = { gap: g, s }; });
  return best;
})();
