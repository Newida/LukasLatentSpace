"""Numbers for the tree stage of the tutorial, next to the cube (conventions in tree_geometry_lib.py)."""
import itertools, json
import numpy as np
from scipy.optimize import minimize

from tree_geometry_lib import pc, bits, avg_last, L_tree, L_cube, Stage


def walsh(n):
    N = 1 << n
    return np.array([[(-1) ** pc(s & x) for x in range(N)] for s in range(N)], float)


def haar(n):
    """Rows: constant, then for each level m = 1..n and prefix p of length m-1 the wavelet
    +1 / -1 on the two halves of that subtree (unnormalised)."""
    N = 1 << n
    rows, labels = [np.ones(N)], [(0, '')]
    for m in range(1, n + 1):
        for p in range(1 << (m - 1)):
            v = np.zeros(N)
            for x in range(N):
                if x & ((1 << (m - 1)) - 1) == p:
                    v[x] = 1 if not (x >> (m - 1)) & 1 else -1
            rows.append(v); labels.append((m, bits(p, m - 1)))
    return np.array(rows), labels


def tree_dist(x, y, n):
    """Height of the lowest common ancestor: n - (length of the common prefix)."""
    for i in range(n):
        if ((x >> i) & 1) != ((y >> i) & 1):
            return n - i
    return 0


out = {}

# ---------------------------------------------------------------- A. n = 3 checks
n = 3; N = 8
LT, LC = L_tree(n), L_cube(n)
ev = np.round(np.linalg.eigvalsh(LT), 10)
print('A. tree Laplacian n=3 eigenvalues', ev)
Hh, hl = haar(n)
for v, (m, p) in zip(Hh, hl):
    lam = 2 * m
    assert np.allclose(LT @ v, lam * v), (m, p)
W = walsh(n)
for s in range(N):
    lam = 2 * s.bit_length()
    assert np.allclose(LT @ W[s], lam * W[s])
print('   Haar wavelets: eigenvalue 2 * level; Walsh chi_s: eigenvalue 2 * (deepest bit of s)  [checked]')
print('   Haar table n=3 (rows by level, columns x = 000 .. 111 in lexicographic string order):')
order = sorted(range(N), key=lambda x: bits(x, n))
for v, (m, p) in zip(Hh, hl):
    print(f'     level {m} prefix {p or "-":>3}: ' + ' '.join({1: '+', -1: '-', 0: '.'}[int(v[x])] for x in order) + f'   eigenvalue {2*m}')
wts = {}
for y in range(1, N):
    d = tree_dist(0, y, n); wts.setdefault(d, -LT[0, y])
print('   off-diagonal weights of L_T by tree distance:', wts, ' degree', LT[0, 0])
out['n3_tree_weights'] = wts

# ---------------------------------------------------------------- B. classical heat flow on the tree
def heat(L, t):
    lam, V = np.linalg.eigh(L)
    return V @ np.diag(np.exp(-lam * t)) @ V.T

print('\nB. classical heat flow from 000, n=3: probability of one leaf at each tree distance')
for t in (0.1, 0.25, 0.5, 1.0, 2.0):
    P = heat(LT, t)[:, 0]
    Pc = heat(LC, t)[:, 0]
    byd = {d: P[[y for y in range(N) if tree_dist(0, y, n) == d][0]] for d in range(n + 1)}
    far_half = sum(P[y] for y in range(N) if tree_dist(0, y, n) == n)
    print(f'   t={t:4}: tree ' + ' '.join(f'd{d}:{p:.3f}' for d, p in byd.items()) +
          f'   far half {far_half:.3f} | cube P(start) {Pc[0]:.3f} P(opposite) {Pc[7]:.3f}')
# closed form check: P(y|x) = sum_{k >= d} P(J = k) 2^-k, P(J <= k) = exp(-2 (n-k) t)
t = 0.37
PJ = [np.exp(-2 * n * t)] + [np.exp(-2 * (n - k) * t) - np.exp(-2 * (n - k + 1) * t) for k in range(1, n + 1)]
P = heat(LT, t)[:, 0]
for y in range(N):
    d = tree_dist(0, y, n)
    ref = sum(PJ[k] * 2.0 ** -k for k in range(max(d, 0), n + 1)) if d > 0 else sum(PJ[k] * 2.0 ** -k for k in range(n + 1))
    assert abs(P[y] - ref) < 1e-12
print('   closed form "climb to height J, land uniformly" checked')

# ---------------------------------------------------------------- C. quantum walk on the tree
def walk(L, b):
    lam, V = np.linalg.eigh(L)
    return V @ np.diag(np.exp(1j * lam * b)) @ V.T

print('\nC. quantum walk exp(+i beta L_T) from 000, n=3')
for b in (np.pi / 8, np.pi / 4, 3 * np.pi / 8, np.pi / 2):
    a = walk(LT, b)[:, 0]
    P = np.abs(a) ** 2
    byd = {d: P[[y for y in range(N) if tree_dist(0, y, n) == d][0]] for d in range(n + 1)}
    far = sum(P[y] for y in range(N) if tree_dist(0, y, n) == n)
    print(f'   beta={b/np.pi:.3f}pi: ' + ' '.join(f'd{d}:{p:.4f}' for d, p in byd.items()) + f'  far half {far:.4f}')
# closed form: amplitude = a^n [x=y] + sum_{k>=max(d,1)} (1-a) a^(n-k) 2^-k, a = exp(2 i beta)
b = 0.731; aa = np.exp(2j * b)
U = walk(LT, b)
for y in range(N):
    d = tree_dist(0, y, n)
    ref = (aa ** n if y == 0 else 0) + sum((1 - aa) * aa ** (n - k) * 2.0 ** -k for k in range(max(d, 1), n + 1))
    assert abs(U[y, 0] - ref) < 1e-12
print('   closed form checked')
for nn in (2, 3, 4, 6):
    L = L_tree(nn); NN = 1 << nn
    best = 0
    for b in np.linspace(0, np.pi, 2001):
        a = walk(L, b)[:, 0]
        best = max(best, sum(abs(a[y]) ** 2 for y in range(NN) if tree_dist(0, y, nn) == nn))
    print(f'   n={nn}: max over beta of P(far half) = {best:.4f}   bound 2^(1-n) = {2.0**(1-nn):.4f}')
# uniform mixing?
for nn in (2, 3):
    L = L_tree(nn); NN = 1 << nn
    dev = min((np.abs(np.abs(walk(L, b)[:, 0]) ** 2 - 1 / NN).max(), b) for b in np.linspace(0, np.pi, 4001))
    print(f'   n={nn}: closest to uniform: max deviation {dev[0]:.4f} at beta = {dev[1]/np.pi:.4f} pi')

# ---------------------------------------------------------------- D. QAOA on the prism
n, N = 6, 64
E0 = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)]


def costs(E):
    return np.array([sum(((x >> i) & 1) != ((x >> j) & 1) for i, j in E) for x in range(N)], float)


C = costs(E0); CMAX = C.max()
LTp, LCp = L_tree(n), L_cube(n)


def grid1(stage, Cv, gmax=np.pi, bmax=np.pi, G=181, B=181):
    """Depth-1 landscape on a grid, vectorised over beta for each gamma."""
    c = Cv[stage.states]; m = len(c)
    bs = np.linspace(0, bmax, B); gs = np.linspace(0, gmax, G)
    Ein = stage.V.T @ (np.ones(m) / np.sqrt(m))
    best = (-1, 0, 0)
    E = np.zeros((G, B))
    for i, g in enumerate(gs):
        k = stage.V.T @ (np.exp(-1j * g * c) / np.sqrt(m))
        ph = np.exp(1j * np.outer(bs, stage.lam)) * k[None, :]
        psi = ph @ stage.V.T
        e = (np.abs(psi) ** 2 * c[None, :]).sum(1)
        E[i] = e
        j = int(e.argmax())
        if e[j] > best[0]: best = (float(e[j]), g, bs[j])
    return best, E


def level_weights(psi, n):
    """Weight of a state on the tree levels (= Walsh weight grouped by the deepest bit)."""
    N = len(psi)
    a = np.array([[(-1) ** pc(s & x) for x in range(N)] for s in range(N)]) @ psi / N
    w = np.zeros(n + 1)
    for s in range(N): w[s.bit_length()] += abs(a[s]) ** 2
    return w / w.sum()


def walsh_weights(psi, n):
    N = len(psi)
    a = np.array([[(-1) ** pc(s & x) for x in range(N)] for s in range(N)]) @ psi / N
    w = np.zeros(n + 1)
    for s in range(N): w[pc(s)] += abs(a[s]) ** 2
    return w / w.sum()


cube, tree = Stage(LCp), Stage(LTp)
print('\nD. prism, depth 1 (grid then refine)')
res = {}
for name, st, bmax in (('cube', cube, np.pi / 2), ('tree', tree, np.pi)):
    (e, g, b), _ = grid1(st, C, bmax=bmax)
    r = minimize(lambda x: -st.run([x[0]], [x[1]], C)[0], [g, b], method='Nelder-Mead', options={'xatol': 1e-8, 'fatol': 1e-10})
    g, b = r.x; e, pm, psi = st.run([g], [b], C, detail=True)
    pr = np.abs(psi) ** 2; mode = int(pr.argmax())
    lw = level_weights(psi, n); ww = walsh_weights(psi, n)
    print(f'   {name}: gamma {g:.3f} ({g/np.pi:.3f} pi) beta {b:.3f} ({b/np.pi:.3f} pi)  <C> {e:.3f} ratio {e/CMAX:.3f}  P(max) {pm:.3f}  mode {bits(mode, n)} (cut {C[mode]:.0f}, p={pr[mode]:.3f})')
    print('       weight by tree level:', np.round(lw, 3), '  by |s|:', np.round(ww, 3))
    print('       the six maximum cuts:', {bits(int(x), n): round(float(pr[x]), 4) for x in np.flatnonzero(C == CMAX)})
    res[name] = dict(gamma=g, beta=b, E=e, Pmax=pm, mode=bits(mode, n), level_w=lw.tolist(), walsh_w=ww.tolist())
out['depth1'] = res

# cost spectrum on the two stages
Cc = C - C.mean()
for name, L in (('cube', LCp), ('tree', LTp)):
    lam, V = np.linalg.eigh(L)
    coef = V.T @ Cc
    spec = {}
    for l, cf in zip(np.round(lam, 8), coef):
        spec[l] = spec.get(l, 0) + cf ** 2
    tot = sum(spec.values())
    print(f'   cost spectrum on the {name}:', {k: round(v / tot, 3) for k, v in sorted(spec.items()) if v / tot > 1e-9},
          ' mean frequency', round(Cc @ L @ Cc / (Cc @ Cc), 3), ' of max', round(lam.max(), 3))

# Deeper circuits are in final_numbers_v2.py (adjoint gradients, 20000 starts, two seeds).

# ---------------------------------------------------------------- E. vertex order on the tree
print('\nE. tree: all 720 vertex orders at depth 1 (vertex v sits at depth perm[v] + 1)')
rows = []
seen = {}
for perm in itertools.permutations(range(n)):
    E = [(perm[i], perm[j]) for i, j in E0]
    key = tuple(sorted(tuple(sorted(e)) for e in E))
    if key in seen:
        rows.append((perm,) + seen[key]); continue
    Cv = costs(E)
    rough = sum(2 * (max(i, j) + 1) for i, j in E) / len(E)
    (e, g, b), _ = grid1(tree, Cv, G=91, B=91)
    r = minimize(lambda x: -tree.run([x[0]], [x[1]], Cv)[0], [g, b], method='Nelder-Mead')
    e, pm = tree.run([r.x[0]], [r.x[1]], Cv)
    seen[key] = (rough, e, pm)
    rows.append((perm, rough, e, pm))
arr = np.array([r[1:] for r in rows])
print(f'   distinct relabelled instances: {len(seen)}')
print(f'   mean frequency of the cost on the tree: min {arr[:,0].min():.2f} max {arr[:,0].max():.2f}')
print(f'   depth-1 best <C>: min {arr[:,1].min():.3f} max {arr[:,1].max():.3f};  P(max): min {arr[:,2].min():.3f} max {arr[:,2].max():.3f}')
print(f'   correlation(mean frequency, <C>) = {np.corrcoef(arr[:,0], arr[:,1])[0,1]:.3f}')
ib, iw = int(arr[:, 1].argmax()), int(arr[:, 1].argmin())
for tag, i in (('best', ib), ('worst', iw)):
    perm = rows[i][0]
    depth_of = {v + 1: perm[v] + 1 for v in range(n)}
    order_root_down = [v for v, _ in sorted(depth_of.items(), key=lambda kv: kv[1])]
    print(f'   {tag} order (root first): vertices {order_root_down}  mean freq {arr[i,0]:.2f}  <C> {arr[i,1]:.3f}  P(max) {arr[i,2]:.3f}')
nat = [r for r in rows if r[0] == tuple(range(n))][0]
print(f'   natural order 1..6: mean freq {nat[1]:.2f}  <C> {nat[2]:.3f}  P(max) {nat[3]:.3f}')
out['orders'] = dict(rough_min=arr[:, 0].min(), rough_max=arr[:, 0].max(), E_min=arr[:, 1].min(), E_max=arr[:, 1].max(),
                     P_min=arr[:, 2].min(), P_max=arr[:, 2].max(), corr=np.corrcoef(arr[:, 0], arr[:, 1])[0, 1],
                     best=[int(v) for v in rows[ib][0]], worst=[int(v) for v in rows[iw][0]])

json.dump(out, open('tree_results.json', 'w'), indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
print('\nwrote tree_results.json')
