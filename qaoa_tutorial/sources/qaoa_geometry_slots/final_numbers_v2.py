"""Stage comparison with exact gradients and many random starts (supersedes final_numbers.py).

Same problems and stages as final_numbers.py. <C> is maximised with L-BFGS-B and an adjoint gradient.
Usage: python final_numbers_v2.py SEED STARTS OUT.json
Run twice with different seeds; compare_runs.py checks that both runs agree before numbers are quoted.
"""
import json, os, sys
from multiprocessing import Pool
import numpy as np
from scipy.optimize import minimize
import final_numbers as F


class Fast:
    def __init__(self, stage, Cv):
        self.V, self.lam = stage.V, stage.lam
        self.c = Cv[stage.states].astype(float)
        self.cmax = Cv.max()
        m = len(self.c)
        self.psi0 = np.ones(m, complex) / np.sqrt(m)

    def mix(self, b, v):
        return self.V @ (np.exp(1j * b * self.lam) * (self.V.T @ v))

    def mixT(self, b, v):  # adjoint of mix
        return self.V @ (np.exp(-1j * b * self.lam) * (self.V.T @ v))

    def Lv(self, v):
        return self.V @ (self.lam * (self.V.T @ v))

    def value_grad(self, x):
        p = len(x) // 2; g, b = x[:p], x[p:]
        psis = [self.psi0]
        psi = self.psi0
        for l in range(p):
            phi = np.exp(-1j * g[l] * self.c) * psi
            psi = self.mix(b[l], phi)
            psis.append(psi)
        E = float(np.real(np.vdot(psi, self.c * psi)))
        lam = self.c * psi
        dg, db = np.zeros(p), np.zeros(p)
        for l in range(p - 1, -1, -1):
            after = psis[l + 1]
            db[l] = 2 * np.real(np.vdot(lam, 1j * self.Lv(after)))
            lam = self.mixT(b[l], lam)
            phi = np.exp(-1j * g[l] * self.c) * psis[l]
            dg[l] = 2 * np.real(np.vdot(lam, -1j * self.c * phi))
            lam = np.exp(1j * g[l] * self.c) * lam
        return E, np.concatenate([dg, db])

    def pmax(self, x):
        p = len(x) // 2; psi = self.psi0
        for l in range(p):
            psi = self.mix(x[p + l], np.exp(-1j * x[l] * self.c) * psi)
        pr = np.abs(psi) ** 2
        return float(pr[np.isclose(self.c, self.cmax)].sum())


FAST = {(s, pn): Fast(F.STAGES[s], F.PROBLEMS[pn]) for s in F.STAGES for pn in F.PROBLEMS}


def local(args):
    key, x0 = args
    f = FAST[key]
    r = minimize(lambda x: tuple(-v for v in f.value_grad(x)), x0, jac=True, method='L-BFGS-B')
    return -r.fun, r.x


def check_gradient():
    rng = np.random.default_rng(0)
    for key in [('tree', 'maxcut'), ('ring', 'number'), ('slice', 'maxcut')]:
        f = FAST[key]; x = rng.uniform(0, 2, 6)
        E, gr = f.value_grad(x)
        num = np.array([(f.value_grad(x + 1e-6 * e)[0] - f.value_grad(x - 1e-6 * e)[0]) / 2e-6 for e in np.eye(6)])
        assert np.allclose(gr, num, atol=1e-5), (key, gr, num)
        assert abs(E - F.STAGES[key[0]].run(x[:3], x[3:], F.PROBLEMS[key[1]])[0]) < 1e-10
    print('adjoint gradient checked against finite differences', flush=True)


if __name__ == '__main__':
    seed, starts, outname = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    check_gradient()
    out = {}
    with Pool(min(30, os.cpu_count())) as pool:
        for pname in F.PROBLEMS:
            out[pname] = {}
            for sname in F.STAGES:
                if sname == 'slice' and pname != 'maxcut':
                    continue
                key = (sname, pname); prev = None; out[pname][sname] = {}
                for p in (1, 2, 3, 4):
                    rng = np.random.default_rng([seed, p, len(sname), len(pname)])
                    n0 = starts if p > 1 else max(500, starts // 10)
                    inits = [np.concatenate([rng.uniform(0, 2 * np.pi, p), rng.uniform(0, 2 * np.pi, p)]) for _ in range(n0)]
                    if prev is not None:
                        g, b = prev[:p - 1], prev[p - 1:]
                        for k in range(p):
                            inits.append(np.concatenate([np.insert(g, k, 0.0), np.insert(b, k, 0.0)]))
                    res = pool.map(local, [(key, x0) for x0 in inits], chunksize=64)
                    vals = np.array([r[0] for r in res])
                    i = int(vals.argmax()); e, x = res[i]
                    # how often did a start reach the best value? (a rough sense of how hard the landscape is)
                    hits = int((vals > e - 1e-6).sum())
                    pm = FAST[key].pmax(x)
                    out[pname][sname][p] = [e, pm, x.tolist(), hits, len(inits)]
                    prev = x
                    print(f'{pname:7s} {sname:9s} p={p}: <C> {e:8.4f}  P(opt) {pm:.4f}  hits {hits}/{len(inits)}', flush=True)
    json.dump(out, open(outname, 'w'), indent=1)
