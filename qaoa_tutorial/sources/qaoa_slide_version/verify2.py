import json, itertools
import numpy as np
from scipy.optimize import minimize, minimize_scalar
d = json.load(open('data.json'))
n = 6
E = [[0,1],[1,2],[2,0],[3,4],[4,5],[5,3],[0,3],[1,4],[2,5]]
X = np.array([[ (k>>i)&1 for i in range(n)] for k in range(64)])
C = np.array([sum(X[k,i] != X[k,j] for i,j in E) for k in range(64)], float)
best = C.max()
HB = np.zeros((64,64))
for k in range(64):
    for i in range(n):
        HB[k, k ^ (1<<i)] -= 1
HC = -np.diag(C)
# proper reachable space: closure of span{|+>} under HB and HC
B = np.ones((64,1))/8
while True:
    cand = np.hstack([B, HB @ B, HC @ B])
    U, S, _ = np.linalg.svd(cand, full_matrices=False)
    B2 = U[:, S > 1e-9*S[0]]
    if B2.shape[1] == B.shape[1]: break
    B = B2
print('reachable dim', B.shape[1])
# orbits under prism automorphisms x global flip
perms = []
for p in itertools.permutations(range(6)):
    Es = {frozenset(e) for e in E}
    if all(frozenset((p[i],p[j])) in Es for i,j in E): perms.append(p)
print('automorphisms', len(perms))
seen = set(); orbits = 0
for k in range(64):
    if k in seen: continue
    orbits += 1
    for p in perms:
        for fl in (0, 63):
            y = sum(((k>>i)&1) << p[i] for i in range(6)) ^ fl
            seen.add(y)
print('orbits (aut x flip)', orbits)
def gap_on(Bs, s):
    w = np.linalg.eigvalsh(Bs.T @ ((1-s)*HB + s*HC) @ Bs); return w
ss = np.linspace(0,1,4001)
g = np.array([np.diff(gap_on(B,s)[:2])[0] for s in ss])
j = g.argmin()
r = minimize_scalar(lambda s: np.diff(gap_on(B,s)[:2])[0], bounds=(ss[max(j-2,0)], ss[min(j+2,4000)]), method='bounded', options={'xatol':1e-12})
print('reachable min gap %.4f at s=%.4f' % (r.fun, r.x))
print('levels on reachable space at s=0,1:', np.round(gap_on(B,0),3), np.round(gap_on(B,1),3))
# symmetric 8-dim space: orbit-sum vectors
orbit_vecs = []
seen=set()
for k in range(64):
    if k in seen: continue
    orb=set()
    for p in perms:
        for fl in (0,63):
            orb.add(sum(((k>>i)&1) << p[i] for i in range(6)) ^ fl)
    seen|=orb; v=np.zeros(64); v[list(orb)]=1; orbit_vecs.append(v/np.linalg.norm(v))
O = np.array(orbit_vecs).T
g8 = np.array([np.diff(gap_on(O,s)[:2])[0] for s in ss])
print('8-dim symmetric min gap %.4f at s=%.4f' % (g8.min(), ss[g8.argmin()]))
print('orbit cut values', sorted(int(C[np.argmax(O[:,i])]) for i in range(O.shape[1])), 'sizes', sorted(int((O[:,i]>0).sum()) for i in range(O.shape[1])))
# does the data.json level set match the 8-dim space?
lv = np.array(d['levels'])
print('data levels vs 8-dim at s=0.5', np.allclose(lv[50], gap_on(O,0.5), atol=2e-3))

def run(gs, bs):
    psi = np.ones(64, complex)/8
    for gm, bt in zip(gs, bs):
        psi = np.exp(1j*gm*C)*psi
        for i in range(n):
            f = psi[np.arange(64) ^ (1<<i)]
            psi = np.cos(bt)*psi + 1j*np.sin(bt)*f
    pr = np.abs(psi)**2
    return (pr*C).sum(), pr[C == best].sum()
def ramp(p, T):
    s = (np.arange(1,p+1)-0.5)/p
    return run(s*T/p, (1-s)*T/p)
Ts = np.arange(0.01, 40.0001, 0.01)
for p in range(1,9):
    vals = np.array([ramp(p,T) for T in Ts])
    out = []
    for lab, Tmax in (('pi/2*p', np.pi/2*p), ('2p', 2*p), ('4p', 4*p), ('40', 40)):
        m = Ts <= Tmax + 1e-9
        jp = np.argmax(np.where(m, vals[:,1], -1)); je = np.argmax(np.where(m, vals[:,0], -1))
        out.append('%s: P*%.3f@T%.2f E*%.3f@T%.2f(P%.3f)' % (lab, vals[jp,1], Ts[jp], vals[je,0], Ts[je], vals[je,1]))
    t = d['tuned'][p-1]; tv = run(t['gamma'], t['beta'])
    print(p, ' | '.join(out), '| tuned E %.4f P %.4f' % tv)
# global check of tuned optimum: random restarts maximizing E
rng = np.random.default_rng(0)
for p in range(1,7):
    bestE = -1
    for _ in range(30):
        x0 = np.concatenate([rng.uniform(0, np.pi, p), rng.uniform(0, np.pi/2, p)])
        r = minimize(lambda x: -run(x[:p], x[p:])[0], x0, method='BFGS')
        bestE = max(bestE, -r.fun)
    print('restart check p=%d: best E %.4f vs data %.4f' % (p, bestE, d['tuned'][p-1]['E']))
