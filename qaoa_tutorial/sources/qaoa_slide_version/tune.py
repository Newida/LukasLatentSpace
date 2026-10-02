import json, numpy as np
from scipy.optimize import minimize
n = 6
E = [[0,1],[1,2],[2,0],[3,4],[4,5],[5,3],[0,3],[1,4],[2,5]]
X = np.array([[ (k>>i)&1 for i in range(n)] for k in range(64)])
C = np.array([sum(X[k,i] != X[k,j] for i,j in E) for k in range(64)], float)
best = C.max(); idx = np.arange(64)
def run(gs, bs):
    psi = np.ones(64, complex)/8
    for gm, bt in zip(gs, bs):
        psi = np.exp(1j*gm*C)*psi
        for i in range(n):
            psi = np.cos(bt)*psi + 1j*np.sin(bt)*psi[idx ^ (1<<i)]
    pr = np.abs(psi)**2
    return (pr*C).sum(), pr[C == best].sum()
def canon(g, b):
    g = np.array(g, float); b = np.array(b, float)
    b = (b + np.pi/4) % (np.pi/2) - np.pi/4
    g = (g + np.pi) % (2*np.pi) - np.pi
    if g[0] < 0: g, b = -g, -b
    return g, b
def opt(x0, p):
    r = minimize(lambda x: -run(x[:p], x[p:])[0], x0, method='BFGS', options={'gtol':1e-9})
    return -r.fun, r.x
rng = np.random.default_rng(1)
res = {}
prev = None
for p in range(1, 9):
    cands = []
    # INTERP warm start from p-1 (Zhou et al.)
    if prev is not None:
        def interp(v):
            q = len(v); out = np.zeros(q+1)
            for i in range(q+1):
                a = v[i-1] if i-1 >= 0 else 0.0; c = v[i] if i < q else 0.0
                out[i] = (i/q)*a + ((q-i)/q)*c
            return out
        e, x = opt(np.concatenate([interp(prev[0]), interp(prev[1])]), p); cands.append((e, x, 'interp'))
    nr = 400 if p <= 4 else 150
    for _ in range(nr):
        x0 = np.concatenate([rng.uniform(-np.pi, np.pi, p), rng.uniform(-np.pi/4, np.pi/4, p)])
        e, x = opt(x0, p); cands.append((e, x, 'random'))
    cands.sort(key=lambda t: -t[0])
    eb, xb, src = cands[0]
    gb, bb = canon(xb[:p], xb[p:])
    ei = [c for c in cands if c[2] == 'interp']
    line = 'p=%d best E %.5f P %.4f (%s) g=%s b=%s' % (p, eb, run(gb, bb)[1], src, np.round(gb,3), np.round(bb,3))
    if ei:
        gi, bi = canon(ei[0][1][:p], ei[0][1][p:])
        line += '\n     interp E %.5f P %.4f g=%s b=%s' % (ei[0][0], run(gi, bi)[1], np.round(gi,3), np.round(bi,3))
        prev = (gi, bi) if ei[0][0] >= eb - 1e-6 else (gi, bi)  # keep the smooth branch for the next warm start
    else:
        prev = (gb, bb)
    # distinct local optima near the top
    tops = []
    for e, x, s in cands:
        if e < eb - 0.05: break
        g, b = canon(x[:p], x[p:])
        if not any(abs(e - t[0]) < 1e-5 for t in tops): tops.append((e, g, b))
    line += '\n     top distinct E: ' + ', '.join('%.4f' % t[0] for t in tops[:6])
    print(line, flush=True)
    res[p] = dict(best=dict(E=eb, g=gb.tolist(), b=bb.tolist()), interp=(dict(E=ei[0][0], g=gi.tolist(), b=bi.tolist()) if ei else None))
json.dump(res, open('tune_results.json', 'w'))
