"""Problems and stages of the comparison, plus a first optimiser.

The definitions here (STAGES, PROBLEMS) are used by final_numbers_v2.py and stage_table.py; the numbers in
the post come from those two. Running this file directly uses numerical gradients and fewer starts.

Problems on 6 bits:
  maxcut  : MaxCut on the triangular prism (maximise the cut).
  number  : the bitstring read as a binary number v (x_1 most significant), cost C = -|v - 41|.
Stages: cube, tree, ring (strings in the order of their value, +-1 steps), complete graph, and for MaxCut
also the Hamming-weight-3 slice (swap moves).
For every stage and depth we maximise <C> (many random starts + warm starts from depth p - 1) and report
<C> and the probability of the optimum at those angles.
"""
import json, os
from multiprocessing import Pool
import numpy as np
from scipy.optimize import minimize
from tree_geometry_lib import L_tree, L_cube, Stage

n, N = 6, 64
val = np.array([sum(((x >> i) & 1) << (n - 1 - i) for i in range(n)) for x in range(N)])
E0 = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)]
maxcut = np.array([sum(((x >> i) & 1) != ((x >> j) & 1) for i, j in E0) for x in range(N)], float)
number = -np.abs(val - 41).astype(float)


def L_ring():
    pos = {int(v): x for x, v in enumerate(val)}
    L = 2 * np.eye(N)
    for k in range(N):
        a, b = pos[k], pos[(k + 1) % N]
        L[a, b] -= 1; L[b, a] -= 1
    return L


def slice_stage(k=3):
    idx = [x for x in range(N) if bin(x).count('1') == k]
    where = {x: i for i, x in enumerate(idx)}
    m = len(idx); L = np.zeros((m, m))
    for x in idx:
        for i in range(n):
            for j in range(n):
                if (x >> i) & 1 and not (x >> j) & 1:
                    L[where[x], where[x ^ (1 << i) ^ (1 << j)]] = -1
    L += np.diag(-L.sum(1))
    return Stage(L, idx)


STAGES = {
    'cube': Stage(L_cube(n)),
    'tree': Stage(L_tree(n)),
    'ring': Stage(L_ring()),
    'complete': Stage(N * np.eye(N) - np.ones((N, N))),
    'slice': slice_stage(),
}
PROBLEMS = {'maxcut': maxcut, 'number': number}


def local(args):
    sname, pname, p, x0 = args
    st, Cv = STAGES[sname], PROBLEMS[pname]
    r = minimize(lambda x: -st.run(x[:p], x[p:], Cv)[0], x0, method='L-BFGS-B')
    return -r.fun, r.x


def best(pool, sname, pname, p, prev, starts=480, seed=0):
    rng = np.random.default_rng(1000 * p + len(sname) + len(pname) + seed)
    gmax = np.pi if pname == 'maxcut' else 0.6
    inits = [np.concatenate([rng.uniform(0, gmax, p), rng.uniform(0, 2 * np.pi, p)]) for _ in range(starts)]
    if prev is not None:  # warm starts: insert a zero layer at every position
        g, b = prev[:p - 1], prev[p - 1:]
        for k in range(p):
            inits.append(np.concatenate([np.insert(g, k, 0.0), np.insert(b, k, 0.0)]))
    res = pool.map(local, [(sname, pname, p, x0) for x0 in inits], chunksize=8)
    e, x = max(res, key=lambda t: t[0])
    st, Cv = STAGES[sname], PROBLEMS[pname]
    e, pm = st.run(x[:p], x[p:], Cv)
    return e, pm, x


if __name__ == '__main__':
    out = {}
    with Pool(min(30, os.cpu_count())) as pool:
        for pname in PROBLEMS:
            out[pname] = {}
            for sname in STAGES:
                if sname == 'slice' and pname != 'maxcut':
                    continue
                st = STAGES[sname]; c = PROBLEMS[pname][st.states]
                out[pname][sname] = {'start': [float(c.mean()), float(np.mean(c == PROBLEMS[pname].max()))]}
                prev = None
                for p in (1, 2, 3, 4):
                    e, pm, prev = best(pool, sname, pname, p, prev)
                    out[pname][sname][p] = [e, pm, prev.tolist()]
                    print(f'{pname:7s} {sname:9s} p={p}: <C> {e:8.4f}  P(opt) {pm:.4f}', flush=True)
    json.dump(out, open('final_numbers.json', 'w'), indent=1)
