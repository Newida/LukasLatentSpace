const fs = require('fs');
const { PRISM, mutationMatrix, gaStep, quasispecies, cutHistogram, finiteStep, populationDistribution, masterShare } = new Function(fs.readFileSync(__dirname + '/engine.js', 'utf8') + '; return { PRISM, mutationMatrix, gaStep, quasispecies, cutHistogram, finiteStep, populationDistribution, masterShare };')();
const pmax = (p) => { let s = 0; for (let x = 0; x < PRISM.N; x++) if (PRISM.C[x] === PRISM.Cmax) s += p[x]; return s; };
for (const [g, q, ref] of [[1, 0.05, 0.662], [0.5, 0.02, 0.780], [2, 0.3, 0.160], [1, 0.2, 0.232]]) {
  console.log(`prism g=${g} q=${q}: quasispecies P(max) = ${pmax(quasispecies(mutationMatrix(q), g)).toFixed(3)} (python ${ref})`);
}
let p = new Float64Array(PRISM.N).fill(1 / PRISM.N); const M = mutationMatrix(0.05); const traj = [];
for (let k = 0; k < 6; k++) { p = gaStep(p, M, 1); traj.push(pmax(p).toFixed(3)); }
console.log('trajectory', traj.join(' '), '(python 0.365 0.546 0.620 0.647 0.656 0.660)');
for (const [q, ref] of [[0.01, 0.7135], [0.02, 0.4794], [0.04, 0.1324], [0.045, 0.0658], [0.05, 0.0059], [0.06, 0.0]]) {
  console.log(`needle n=20 g=1 q=${q}: ${masterShare(20, 1, q).toFixed(4)} (python ${ref})`);
}
console.log('edge cases: q=0 ->', masterShare(20, 1, 0).toFixed(4), ' prism q=0.5 uniform P(max) ->', pmax(quasispecies(mutationMatrix(0.5), 1)).toFixed(4));
let s = 1; const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
let pop = new Int32Array(200).map(() => Math.floor(rnd() * 64)); let avg = 0;
for (let k = 0; k < 300; k++) { pop = finiteStep(pop, 1, 0.05, rnd); if (k >= 100) avg += pmax(populationDistribution(pop)) / 200; }
console.log('finite N=200 g=1 q=0.05 time-averaged P(max) over gens 100-300:', avg.toFixed(3), '(quasispecies 0.662)');
const t0 = Date.now(); for (let i = 0; i < 100; i++) masterShare(40, 1, 0.001 + i * 0.0006); console.log('100 needle points at n=40 took', Date.now() - t0, 'ms');
