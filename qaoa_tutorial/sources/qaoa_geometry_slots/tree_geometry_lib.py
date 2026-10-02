"""Shared pieces: the cube and tree Laplacians and a split-step QAOA simulator on any stage.

Conventions as in the page: integer bit i is vertex i + 1, strings are printed x_1 x_2 ... x_n,
and on the tree x_1 is the decision at the root. "The last j bits" are x_{n-j+1} .. x_n,
i.e. the integer bits n - j .. n - 1.
"""
import numpy as np

pc = lambda x: bin(x).count('1')
bits = lambda x, n: ''.join(str((x >> i) & 1) for i in range(n))


def avg_last(n, j):
    """A_j: average over the last j bits (integer bits n-j .. n-1)."""
    N = 1 << n
    mask = ((1 << j) - 1) << (n - j)
    A = np.zeros((N, N))
    for x in range(N):
        for y in range(N):
            if (x & ~mask) == (y & ~mask):
                A[x, y] = 2.0 ** -j
    return A


def L_tree(n):
    """L_T = 2 sum_j (I - A_j): for every height j a clock at rate 2 that redraws the last j bits."""
    N = 1 << n
    return 2 * sum(np.eye(N) - avg_last(n, j) for j in range(1, n + 1))


def L_cube(n):
    N = 1 << n
    A = np.zeros((N, N))
    for x in range(N):
        for i in range(n):
            A[x, x ^ (1 << i)] = 1
    return n * np.eye(N) - A


class Stage:
    """A search graph given by its Laplacian; the mixer is exp(+i beta L), the cube's exp(-i beta A) up to a global phase."""

    def __init__(self, L, states=None):
        self.L = L; self.lam, self.V = np.linalg.eigh(L)
        self.states = np.arange(L.shape[0]) if states is None else np.asarray(states)

    def run(self, gs, bs, Cv, detail=False):
        c = Cv[self.states]; m = len(c)
        psi = np.ones(m, complex) / np.sqrt(m)
        for g, b in zip(gs, bs):
            psi = np.exp(-1j * g * c) * psi
            psi = self.V @ (np.exp(1j * b * self.lam) * (self.V.T @ psi))
        pr = np.abs(psi) ** 2
        e, pm = float((pr * c).sum()), float(pr[np.isclose(c, Cv.max())].sum())
        return (e, pm, psi) if detail else (e, pm)
