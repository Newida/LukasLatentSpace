import numpy as np
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
def ramp(p, T):
    s = (np.arange(1,p+1)-0.5)/p
    return run(s*T/p, (1-s)*T/p)
for p in (10, 12, 16, 20, 24, 30, 40):
    Ts = np.arange(0.05, min(np.pi/2*p, 80)+1e-9, 0.05)
    v = np.array([ramp(p,T)[1] for T in Ts]); j = v.argmax()
    first99 = Ts[np.argmax(v >= 0.99)] if (v >= 0.99).any() else None
    print('p=%d best P %.4f at T=%.2f; first T with P>=0.99: %s; P(T=20)=%.4f' % (p, v[j], Ts[j], first99, ramp(p,20)[1]))
for p,T in ((4,4.65),(1,0.9),(2,1.99),(8,9.65),(40,20),(3,10),(8,20)):
    print('ramp p=%d T=%.2f: E %.4f P %.4f' % ((p,T)+ramp(p,T)))
