"""Exploration: which stage suits which problem? (not all of this goes into the post)

Stages on 6 bits: cube, tree, ring in binary (MSB-first) order, ring in Gray-code order, complete graph.
Problems: MaxCut on the prism, a 'closest number' cost, a smooth 1D landscape, a hierarchical random landscape.
"""
import json, sys
import numpy as np
from scipy.optimize import minimize
from tree_geometry_lib import L_tree, L_cube, Stage, pc, bits

n, N = 6, 64
val = np.array([sum(((x >> i) & 1) << (n - 1 - i) for i in range(n)) for x in range(N)])  # x_1 is the most significant bit
gray = [k ^ (k >> 1) for k in range(N)]


def L_ring(order):
    """Ring visiting the strings whose integer *value* follows `order` (a list of values)."""
    pos_of_value = {v: x for x, v in enumerate(val)}
    L = 2 * np.eye(N)
    for k in range(N):
        a, b = pos_of_value[order[k]], pos_of_value[order[(k + 1) % N]]
        L[a, b] -= 1; L[b, a] -= 1
    return L


def L_complete():
    return N * np.eye(N) - np.ones((N, N))


stages = {
    'cube': Stage(L_cube(n)),
    'tree': Stage(L_tree(n)),
    'ring': Stage(L_ring(list(range(N)))),
    'gray ring': Stage(L_ring(gray)),
    'complete': Stage(L_complete()),
}

E0 = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)]
maxcut = np.array([sum(((x >> i) & 1) != ((x >> j) & 1) for i, j in E0) for x in range(N)], float)
target = 41
closest = -np.abs(val - target).astype(float)
smooth1d = np.cos(2 * np.pi * (val - target) / N) + 0.5 * np.cos(6 * np.pi * (val - target) / N)
r_ = np.random.default_rng(7)
grem = np.zeros(N)
for m in range(1, n + 1):  # one random number per tree node at depth m, variance halves with depth
    node = {}
    for x in range(N):
        pre = x & ((1 << m) - 1)
        node.setdefault(pre, r_.normal(0, 2.0 ** (-(m - 1) / 2)))
        grem[x] += node[pre]

problems = {'maxcut prism': maxcut, 'closest to 41': closest, 'smooth 1d': smooth1d, 'hierarchical random': grem}


def normalise(c):
    """Rescale to the range [0, 7] so that the same gamma range makes sense for every problem."""
    return 7 * (c - c.min()) / (c.max() - c.min())


def best_p(stage, Cv, p, prev, starts):
    r = np.random.default_rng(p)
    inits = [np.concatenate([r.uniform(0, 2 * np.pi, p), r.uniform(0, 2 * np.pi, p)]) for _ in range(starts)]
    if prev is not None:
        inits.append(np.concatenate([prev[:p - 1], [0.0], prev[p - 1:], [0.0]]))
    top = (-1, None)
    for x0 in inits:
        res = minimize(lambda x: -stage.run(x[:p], x[p:], Cv)[0], x0, method='BFGS')
        if -res.fun > top[0]: top = (-res.fun, res.x)
    e, pm = stage.run(top[1][:p], top[1][p:], Cv)
    return e, pm, top[1]


out = {}
for pname, c in problems.items():
    Cv = normalise(c)
    Cc = Cv - Cv.mean()
    print(f'\n== {pname}: optimum {bits(int(Cv.argmax()), n)} (value {val[Cv.argmax()]}), uniform <C> {Cv.mean():.3f}, start P(max) {np.mean(Cv == Cv.max()):.3f}')
    out[pname] = {}
    for sname, st in stages.items():
        rough = Cc @ st.L @ Cc / (Cc @ Cc) / np.linalg.eigvalsh(st.L).max()
        prev, row = None, []
        for p in (1, 2, 3):
            e, pm, prev = best_p(st, Cv, p, prev, starts=30)
            row.append((e, pm))
        out[pname][sname] = dict(rough=rough, res=row)
        print(f'   {sname:10s} mean freq / max {rough:.3f} | ' + '  '.join(f'p{p}: <C> {e:.3f} P(max) {pm:.3f}' for p, (e, pm) in zip((1, 2, 3), row)), flush=True)
json.dump(out, open('explore_results.json', 'w'), indent=1)
