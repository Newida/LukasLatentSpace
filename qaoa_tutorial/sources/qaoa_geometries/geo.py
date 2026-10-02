import itertools, json
import numpy as np
from scipy.optimize import minimize
n, N = 6, 64
E = [(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)]
def costs(perm=tuple(range(6))):
    # perm[v] = which bit carries vertex v
    return np.array([sum(((x >> perm[i]) & 1) != ((x >> perm[j]) & 1) for i, j in E) for x in range(N)], float)
C = costs(); CMAX = 7
pc = np.array([bin(x).count('1') for x in range(N)])

def adj_cube():
    A = np.zeros((N, N))
    for x in range(N):
        for i in range(n): A[x, x ^ (1 << i)] = 1
    return A
def adj_ring():
    A = np.zeros((N, N))
    for x in range(N): A[x, (x + 1) % N] = A[x, (x - 1) % N] = 1
    return A
def adj_complete():
    return np.ones((N, N)) - np.eye(N)
def adj_slice():
    idx = [x for x in range(N) if pc[x] == 3]
    pos = {x: i for i, x in enumerate(idx)}
    A = np.zeros((len(idx), len(idx)))
    for x in idx:
        for i in range(n):
            for j in range(n):
                if (x >> i) & 1 and not (x >> j) & 1:
                    A[pos[x], pos[x ^ (1 << i) ^ (1 << j)]] = 1
    return A, np.array(idx)

class Geo:
    def __init__(self, A, states=None):
        self.A = A; self.lam, self.V = np.linalg.eigh(A)
        self.states = np.arange(N) if states is None else states
        m = len(self.states); self.psi0 = np.ones(m) / np.sqrt(m)
    def run(self, gs, bs, Cv):
        c = Cv[self.states]; psi = self.psi0.astype(complex)
        for g, b in zip(gs, bs):
            psi = np.exp(-1j * g * c) * psi
            psi = self.V @ (np.exp(-1j * b * self.lam) * (self.V.T @ psi))
        pr = np.abs(psi) ** 2
        return (pr * c).sum(), pr[c == CMAX].sum()

geos = {'cube': Geo(adj_cube()), 'ring': Geo(adj_ring()), 'complete': Geo(adj_complete())}
As, idx = adj_slice(); geos['slice'] = Geo(As, idx)

def best(geo, p, Cv=C, starts=60, seed=0, bmax=2*np.pi):
    rng = np.random.default_rng(seed); top = (-1, None)
    for _ in range(starts):
        x0 = np.concatenate([rng.uniform(0, 2*np.pi, p), rng.uniform(0, bmax, p)])
        r = minimize(lambda x: -geo.run(x[:p], x[p:], Cv)[0], x0, method='BFGS')
        if -r.fun > top[0]: top = (-r.fun, r.x)
    e, pm = geo.run(top[1][:p], top[1][p:], Cv)
    return e, pm, top[1]

res = {}
for name, geo in geos.items():
    c = C[geo.states]
    print(f'{name}: states {len(geo.states)}, start P(max) {np.mean(c == CMAX):.3f}, start <C> {c.mean():.3f}, '
          f'adjacency eigenvalues {sorted(set(np.round(geo.lam, 3)))[-4:]}..., degree {geo.A.sum(1)[0]:.0f}', flush=True)
    res[name] = {}
    for p in (1, 2, 3):
        bmax = 2*np.pi/N if name == 'complete' else 2*np.pi
        e, pm, x = best(geo, p, starts=80 if p == 1 else 60, bmax=bmax)
        res[name][p] = (e, pm)
        print(f'   p={p}: best <C> {e:.3f}  P(max) {pm:.3f}  angles {np.round(x, 3)}', flush=True)
json.dump({k: {str(p): v for p, v in d.items()} for k, d in res.items()}, open('geo_results.json', 'w'))
