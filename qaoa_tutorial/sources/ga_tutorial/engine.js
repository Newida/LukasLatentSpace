/* ---------- engine: pure functions, shared by the page and the tests ---------- */
const pc = (x) => { let c = 0; while (x) { c += x & 1; x >>= 1; } return c; };
const PRISM = (() => {
  const n = 6, N = 1 << n;
  const edges = [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3], [0, 3], [1, 4], [2, 5]];
  const C = new Float64Array(N);
  for (let x = 0; x < N; x++) for (const [i, j] of edges) if (((x >> i) & 1) !== ((x >> j) & 1)) C[x]++;
  let Cmax = 0; for (let x = 0; x < N; x++) Cmax = Math.max(Cmax, C[x]);
  return { n, N, C, Cmax };
})();
function mutationMatrix(q) {
  const { n, N } = PRISM, M = new Float64Array(N * N);
  for (let x = 0; x < N; x++) for (let y = 0; y < N; y++) { const d = pc(x ^ y); M[x * N + y] = Math.pow(q, d) * Math.pow(1 - q, n - d); }
  return M;
}
// one generation of the infinite-population algorithm: selection, then mutation
function gaStep(p, M, g) {
  const { N, C } = PRISM, s = new Float64Array(N), out = new Float64Array(N);
  for (let y = 0; y < N; y++) s[y] = p[y] * Math.exp(g * C[y]);
  let z = 0;
  for (let x = 0; x < N; x++) { let acc = 0; for (let y = 0; y < N; y++) acc += M[x * N + y] * s[y]; out[x] = acc; z += acc; }
  for (let x = 0; x < N; x++) out[x] /= z;
  return out;
}
function quasispecies(M, g) {
  const { N } = PRISM;
  let p = new Float64Array(N).fill(1 / N);
  for (let k = 0; k < 20000; k++) {
    const p2 = gaStep(p, M, g);
    let d = 0; for (let x = 0; x < N; x++) d += Math.abs(p2[x] - p[x]);
    p = p2; if (d < 1e-13) break;
  }
  return p;
}
function cutHistogram(p) {
  const { N, C, Cmax } = PRISM, h = new Float64Array(Cmax + 1);
  for (let x = 0; x < N; x++) h[C[x]] += p[x];
  return h;
}
// finite population: multinomial selection with weights exp(g C), then independent bit flips
function finiteStep(pop, g, q, rnd) {
  const { n, C } = PRISM, m = pop.length, cum = new Float64Array(m);
  let tot = 0;
  for (let i = 0; i < m; i++) { tot += Math.exp(g * C[pop[i]]); cum[i] = tot; }
  const out = new Int32Array(m);
  for (let i = 0; i < m; i++) {
    const r = rnd() * tot; let lo = 0, hi = m - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (cum[mid] < r) lo = mid + 1; else hi = mid; }
    let x = pop[lo];
    for (let b = 0; b < n; b++) if (rnd() < q) x ^= 1 << b;
    out[i] = x;
  }
  return out;
}
function populationDistribution(pop) {
  const p = new Float64Array(PRISM.N);
  for (const x of pop) p[x] += 1 / pop.length;
  return p;
}
// needle landscape reduced to Hamming classes k = distance from the master string
function binom(n, k) { let r = 1; for (let i = 1; i <= k; i++) r = r * (n - k + i) / i; return r; }
function masterShare(n, g, q) {
  const m = n + 1, B = new Float64Array(m * m), f0 = Math.exp(g);
  for (let k = 0; k <= n; k++) for (let a = 0; a <= k; a++) {
    const pa = binom(k, a) * Math.pow(q, a) * Math.pow(1 - q, k - a);
    if (pa === 0) continue;
    for (let b = 0; b <= n - k; b++) {
      const pb = binom(n - k, b) * Math.pow(q, b) * Math.pow(1 - q, n - k - b);
      B[(k - a + b) * m + k] += pa * pb * (k === 0 ? f0 : 1);
    }
  }
  // repeated squaring: the columns of a high power are proportional to the Perron vector
  let P = B;
  for (let it = 0; it < 18; it++) {
    const P2 = new Float64Array(m * m);
    for (let i = 0; i < m; i++) for (let k = 0; k < m; k++) { const v = P[i * m + k]; if (v === 0) continue; for (let j = 0; j < m; j++) P2[i * m + j] += v * P[k * m + j]; }
    let mx = 0; for (let i = 0; i < m * m; i++) if (P2[i] > mx) mx = P2[i];
    for (let i = 0; i < m * m; i++) P2[i] /= mx;
    P = P2;
  }
  let best = 0, bs = -1;
  for (let j = 0; j < m; j++) { let s = 0; for (let i = 0; i < m; i++) s += P[i * m + j]; if (s > bs) { bs = s; best = j; } }
  return P[best] / bs;
}
/* ---------- end engine ---------- */
