import json, itertools
import numpy as np
from scipy.optimize import minimize

d = json.load(open(__import__('pathlib').Path(__file__).parent / 'data.json'))
n = 6
E = [[0,1],[1,2],[2,0],[3,4],[4,5],[5,3],[0,3],[1,4],[2,5]]
X = np.array(list(itertools.product([0,1], repeat=n)))[:, ::-1]  # x_i = bit i of index
C = np.array([sum(X[k,i] != X[k,j] for i,j in E) for k in range(2**n)], float)
best = C.max()

# expected cut and P(max) along the slide (from data)
for i in (0,25,50,75,100):
    p = np.array(d['dists'][i]); print('s', d['s'][i], 'Pmax %.3f  E %.3f' % (p[7], (np.arange(8)*p).sum()))
lv = np.array(d['levels']); gap = lv[:,1]-lv[:,0]
print('min gap %.4f at s=%.2f; gap at s=0 %.2f, s=1 %.2f' % (gap.min(), d['s'][gap.argmin()], gap[0], gap[-1]))

# fine-grained min gap in the symmetric sector: project onto the Krylov space of |+>
HB = np.zeros((64,64))
for k in range(64):
    for i in range(n):
        HB[k, k ^ (1<<i)] -= 1
HC = -np.diag(C)
plus = np.ones(64)/8
K = [plus]
for _ in range(20):
    for M in (HB, HC):
        v = M @ K[-1]
        K.append(v)
Q, R = np.linalg.qr(np.array(K).T)
r = np.sum(np.abs(np.diag(R)) > 1e-9)
# better: orthonormal basis via SVD
U, S, _ = np.linalg.svd(np.array(K).T, full_matrices=False)
B = U[:, S > 1e-8*S[0]]
print('Krylov dim', B.shape[1])
ss = np.linspace(0,1,2001); g = []
for s in ss:
    w = np.linalg.eigvalsh(B.T @ ((1-s)*HB + s*HC) @ B); g.append(w[1]-w[0])
g = np.array(g); print('fine min gap %.4f at s=%.4f' % (g.min(), ss[g.argmin()]))
# full-space min gap for comparison (includes other symmetry sectors)
gf = []
for s in ss[::20]:
    w = np.linalg.eigvalsh((1-s)*HB + s*HC); gf.append(w[1]-w[0])
print('full-space min gap (all sectors) %.4f' % min(gf))

# needle with transverse field, Dicke basis (weight k = Hamming distance from target)
print('needle')
for m in (4,6,8,10,12,14,16):
    k = np.arange(m+1)
    off = -np.sqrt((k[:-1]+1)*(m-k[:-1]))
    HBd = np.diag(off,1)+np.diag(off,-1)
    HCd = np.zeros((m+1,m+1)); HCd[0,0] = -1
    sgrid = np.linspace(0,1,4001)
    gg = [np.diff(np.linalg.eigvalsh((1-s)*HBd + s*HCd)[:2])[0] for s in sgrid]
    j = int(np.argmin(gg)); s0 = sgrid[j]
    from scipy.optimize import minimize_scalar
    res = minimize_scalar(lambda s: np.diff(np.linalg.eigvalsh((1-s)*HBd + s*HCd)[:2])[0], bounds=(max(0,s0-0.002), min(1,s0+0.002)), method='bounded', options={'xatol':1e-12})
    print(m, 'min gap %.4f at s=%.4f   2^(-n/2)=%.4f  ratio %.3f' % (res.fun, res.x, 2**(-m/2), res.fun/2**(-m/2)))

def run(gs, bs):
    psi = np.ones(64, complex)/8
    for gm, bt in zip(gs, bs):
        psi = np.exp(1j*gm*C)*psi
        for i in range(n):
            a = psi.copy(); f = a[np.arange(64) ^ (1<<i)]
            psi = np.cos(bt)*a + 1j*np.sin(bt)*f
    pr = np.abs(psi)**2
    return (pr*C).sum(), pr[C == best].sum()

def ramp(p, T):
    s = (np.arange(1,p+1)-0.5)/p
    return run(s*T/p, (1-s)*T/p)

print('fine ramp p=40')
for T in (2,5,10,20,40):
    print(T, 'E %.3f P %.4f' % ramp(40, T))
print('ramp best T (grid 0..40 step 0.01) vs tuned')
Ts = np.arange(0.01, 40.0001, 0.01)
for p in range(1,9):
    vals = np.array([ramp(p,T) for T in Ts])
    jp = vals[:,1].argmax(); je = vals[:,0].argmax()
    t = d['tuned'][p-1]
    print(p, 'bestP T=%.2f P=%.4f (E %.3f) | bestE T=%.2f E=%.4f P=%.4f | tuned E %.4f P %.4f' % (Ts[jp], vals[jp,1], vals[jp,0], Ts[je], vals[je,0], vals[je,1], t['E'], t['Pmax']))
    tv = run(t['gamma'], t['beta']); assert abs(tv[0]-t['E'])<1e-6 and abs(tv[1]-t['Pmax'])<1e-6, (tv, t)
