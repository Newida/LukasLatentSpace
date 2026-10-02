"""The comparison table of the post ("Swapping the stage"): depths 1 and 2, every stage, both problems.

Angles are boxed: gamma in [0, 2 pi] (both costs are integers, so this is one full period) and beta in [0, 2 pi].
For the cube, the tree and the complete graph this box contains every distinct mixer. The ring's frequencies are
not multiples of a common number, so its beta never repeats, and the box is a choice. It has to be this wide:
with beta in [0, pi] the ring's slow walk cannot move amplitude far enough along the 64 numbers.
Every entry is optimised from 30000 random starts with each of two seeds; disagreements are flagged in the log.
Usage: python stage_table.py   (writes stage_table.json)
"""
import json, os
from multiprocessing import Pool
import numpy as np
from scipy.optimize import minimize
from final_numbers_v2 import FAST
import final_numbers as F

BOX = [(0, 2 * np.pi), (0, 2 * np.pi)]


def local(args):
    key, x0 = args
    p = len(x0) // 2
    f = FAST[key]
    r = minimize(lambda x: tuple(-v for v in f.value_grad(x)), x0, jac=True, method='L-BFGS-B',
                 bounds=[BOX[0]] * p + [BOX[1]] * p)
    return -r.fun, r.x


def best(pool, key, p, seed, starts):
    rng = np.random.default_rng([seed, p] + [len(k) for k in key])
    inits = [np.concatenate([rng.uniform(*BOX[0], p), rng.uniform(*BOX[1], p)]) for _ in range(starts)]
    res = pool.map(local, [(key, x0) for x0 in inits], chunksize=64)
    e, x = max(res, key=lambda t: t[0])
    return e, FAST[key].pmax(x), x


if __name__ == '__main__':
    out = {}
    with Pool(min(30, os.cpu_count())) as pool:
        for pname in F.PROBLEMS:
            for sname in F.STAGES:
                if sname == 'slice' and pname != 'maxcut':
                    continue
                key = (sname, pname)
                for p in (1, 2):
                    runs = [best(pool, key, p, seed, 30000) for seed in (101, 202)]
                    (e1, pm1, x1), (e2, pm2, x2) = runs
                    ok = abs(e1 - e2) < 1e-4
                    e, pm, x = max(runs, key=lambda t: t[0])
                    out.setdefault(pname, {}).setdefault(sname, {})[p] = dict(E=e, Popt=pm, angles=x.tolist(), seeds_agree=ok)
                    print(f'{pname:7s} {sname:9s} p={p}: <C> {e1:8.4f} | {e2:8.4f}   P(opt) {pm:.4f}   {"ok" if ok else "SEEDS DISAGREE"}', flush=True)
    json.dump(out, open('stage_table.json', 'w'), indent=1)
