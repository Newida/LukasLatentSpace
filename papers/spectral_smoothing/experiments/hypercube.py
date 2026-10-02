"""Numerical core for smoothing distributions on the Boolean hypercube.

States x in {0,1}^n are encoded as integers 0..2^n-1. A distribution is a
dense float vector of length 2^n (small n) or a dict {state: prob} (sparse).

Conventions (match the paper):
    E(p)   = 2^{-n} sum_x sum_i (p(x) - p(x ^ e_i))^2 = 2^{1-n} p^T L p
    L      = n I - A, the Laplacian of the hypercube graph Q_n
    mu     = lambda * 2^{1-n}, the size-free regularisation strength
    (P1)   min_p  -sum_x c_x log p_x + mu p^T L p      over the simplex
    (P2)   min_p  ||p_hat - p||^2   + mu p^T L p      =>  p = (I + mu L)^{-1} p_hat
"""

from __future__ import annotations

import math

import numpy as np


def popcount(n: int) -> np.ndarray:
    """|S| for every subset S of [n], encoded as integers."""
    x = np.arange(2**n, dtype=np.int64)
    out = np.zeros(2**n, dtype=np.int64)
    for i in range(n):
        out += (x >> i) & 1
    return out


def wht(v: np.ndarray) -> np.ndarray:
    """Unnormalised fast Walsh-Hadamard transform, H^{(x)n} v, O(n 2^n)."""
    v = np.array(v, dtype=float, copy=True)
    d = v.shape[0]
    h = 1
    while h < d:
        v = v.reshape(-1, 2, h)
        a = v[:, 0, :].copy()
        b = v[:, 1, :]
        v[:, 0, :] = a + b
        v[:, 1, :] = a - b
        v = v.reshape(d)
        h *= 2
    return v


def laplacian_apply(p: np.ndarray, n: int) -> np.ndarray:
    """(L p)_x = n p_x - sum_i p_{x ^ e_i}."""
    x = np.arange(2**n)
    out = n * p
    for i in range(n):
        out = out - p[x ^ (1 << i)]
    return out


def laplacian_dense(n: int) -> np.ndarray:
    d = 2**n
    L = n * np.eye(d)
    x = np.arange(d)
    for i in range(n):
        L[x, x ^ (1 << i)] -= 1.0
    return L


def dirichlet_energy(p: np.ndarray, n: int) -> float:
    """E(p) exactly as defined in the blog post (double sum over x and i)."""
    x = np.arange(2**n)
    total = 0.0
    for i in range(n):
        total += float(np.sum((p - p[x ^ (1 << i)]) ** 2))
    return total / 2**n


def spectral_filter(p_hat: np.ndarray, n: int, h: np.ndarray) -> np.ndarray:
    """Apply a filter h(|S|) in the Walsh basis: H diag(h(|S|)) H / 2^n."""
    k = popcount(n)
    return wht(wht(p_hat) * h[k]) / 2**n


def tikhonov_smooth(p_hat: np.ndarray, n: int, mu: float) -> np.ndarray:
    """Closed-form solution of (P2): (I + mu L)^{-1} p_hat."""
    return spectral_filter(p_hat, n, 1.0 / (1.0 + 2.0 * mu * np.arange(n + 1)))


def heat_smooth(p_hat: np.ndarray, n: int, t: float) -> np.ndarray:
    """exp(-t L) p_hat: independent bit flips with probability (1 - e^{-2t}) / 2."""
    return spectral_filter(p_hat, n, np.exp(-2.0 * t * np.arange(n + 1)))


def flip_probability(t):
    return 0.5 * (1.0 - np.exp(-2.0 * np.asarray(t)))


def tikhonov_distance_kernel(n: int, mu: float) -> np.ndarray:
    """k(d) = [(I + mu L)^{-1}]_{x,y} for Hamming distance d(x,y) = d.

    k(d) = int_0^inf e^{-s} q(s)^d (1-q(s))^{n-d} ds with q(s) = (1-e^{-2 mu s})/2.
    Substituting r = e^{-2 mu s} gives
        k(d) = 1/(2 mu) int_0^1 r^{1/(2 mu) - 1} ((1-r)/2)^d ((1+r)/2)^{n-d} dr,
    a polynomial of degree n against a Jacobi weight, so Gauss-Jacobi quadrature
    with n//2 + 1 nodes is exact (positive integrand: stable for large n).
    """
    from scipy.special import roots_jacobi

    beta = 1.0 / (2.0 * mu) - 1.0
    xs, ws = roots_jacobi(n // 2 + 2, 0.0, beta)
    r = 0.5 * (1.0 + xs)
    d = np.arange(n + 1)[:, None]
    log_terms = d * np.log(0.5 * (1.0 - r))[None, :] + (n - d) * np.log(0.5 * (1.0 + r))[None, :]
    return (np.exp(log_terms) @ ws) * 0.5 ** (beta + 1.0) / (2.0 * mu)


def tikhonov_distance_kernel_krawtchouk(n: int, mu: float) -> np.ndarray:
    """Same kernel via the Walsh spectrum: k(d) = 2^{-n} sum_k K_k(d) / (1 + 2 mu k)."""
    k_vals = np.zeros(n + 1)
    for dist in range(n + 1):
        total = 0.0
        for k in range(n + 1):
            kraw = sum(
                (-1) ** j * math.comb(dist, j) * math.comb(n - dist, k - j)
                for j in range(0, min(dist, k) + 1)
            )
            total += kraw / (1.0 + 2.0 * mu * k)
        k_vals[dist] = total / 2**n
    return k_vals


def sample_tikhonov(data: np.ndarray, n: int, mu: float, size: int, rng) -> np.ndarray:
    """Exact O(n)-per-sample sampler for (I + mu L)^{-1} p_hat.

    data: array of observed states (integers, any n <= 62) or a boolean matrix
    (m x n) for larger n. Returns a boolean matrix of shape (size, n).
    """
    data = np.asarray(data)
    if data.ndim == 1:
        bits = ((data[:, None] >> np.arange(n)) & 1).astype(bool)
    else:
        bits = data.astype(bool)
    centers = bits[rng.integers(0, bits.shape[0], size=size)]
    s = rng.exponential(1.0, size=size)
    q = flip_probability(mu * s)
    flips = rng.random((size, n)) < q[:, None]
    return centers ^ flips


def project_simplex(v: np.ndarray) -> np.ndarray:
    """Euclidean projection onto the probability simplex (Duchi et al. 2008)."""
    u = np.sort(v)[::-1]
    css = np.cumsum(u) - 1.0
    ind = np.arange(1, v.shape[0] + 1)
    rho = np.nonzero(u - css / ind > 0)[0][-1]
    theta = css[rho] / (rho + 1.0)
    return np.maximum(v - theta, 0.0)


def _lap(p, n):
    """n is either the cube dimension or a callable p -> L p (e.g. a sparse block)."""
    return n(p) if callable(n) else laplacian_apply(p, n)


def p1_objective(p: np.ndarray, counts: np.ndarray, n, mu: float) -> float:
    obs = counts > 0
    if np.any(p[obs] <= 0):
        return math.inf
    return float(-np.dot(counts[obs], np.log(p[obs])) + mu * np.dot(p, _lap(p, n)))


def p1_gradient(p: np.ndarray, counts: np.ndarray, n, mu: float) -> np.ndarray:
    obs = counts > 0
    g = 2.0 * mu * _lap(p, n)
    g[obs] -= counts[obs] / p[obs]
    return g


def fw_gap(p: np.ndarray, g: np.ndarray) -> float:
    """Frank-Wolfe duality gap <g, p - e_argmin g>; an upper bound on f(p) - f*."""
    return float(np.dot(g, p) - g.min())


def solve_p1(
    counts: np.ndarray,
    n: int,
    mu: float,
    p0: np.ndarray | None = None,
    tol: float = 1e-9,
    max_iter: int = 20_000,
) -> tuple[np.ndarray, dict]:
    """Accurate solver for (P1): projected accelerated gradient with backtracking
    and adaptive restart. Stops when the Frank-Wolfe gap <= tol * m."""
    m = counts.sum()
    if p0 is None:
        p0 = counts / m
        if not callable(n):
            p0 = 0.5 * p0 + 0.5 * tikhonov_smooth(counts / m, n, mu)
    x = project_simplex(p0)
    y = x.copy()
    fx = p1_objective(x, counts, n, mu)
    step = 1.0 / (m / max(x[counts > 0].min(), 1e-12) ** 2)
    momentum = 1.0
    gap = math.inf
    it = 0
    for it in range(1, max_iter + 1):
        gy = p1_gradient(y, counts, n, mu)
        fy = p1_objective(y, counts, n, mu)
        while True:
            z = project_simplex(y - step * gy)
            fz = p1_objective(z, counts, n, mu)
            diff = z - y
            if fz <= fy + np.dot(gy, diff) + np.dot(diff, diff) / (2 * step) + 1e-14 * abs(fy):
                break
            step *= 0.5
        if fz > fx:  # adaptive restart
            momentum = 1.0
            y = x.copy()
            continue
        new_momentum = 0.5 * (1 + math.sqrt(1 + 4 * momentum**2))
        y = z + ((momentum - 1) / new_momentum) * (z - x)
        x, fx, momentum = z, fz, new_momentum
        step *= 1.1
        if it % 25 == 0 or it == max_iter:
            gap = fw_gap(x, p1_gradient(x, counts, n, mu))
            if gap <= tol * m:
                break
    gap = fw_gap(x, p1_gradient(x, counts, n, mu))
    return x, {"iterations": it, "fw_gap": gap, "objective": fx}


def frank_wolfe_p1(counts, n, mu, p0, iterations):
    """Vanilla Frank-Wolfe on (P1) with gamma_t = 2/(t+2) (blog/notebook version)."""
    p = p0.copy()
    gaps, values = [], []
    for t in range(1, iterations + 1):
        g = p1_gradient(p, counts, n, mu)
        j = int(np.argmin(g))
        gaps.append(fw_gap(p, g))
        values.append(p1_objective(p, counts, n, mu))
        gamma = 2.0 / (t + 2.0)
        p = (1 - gamma) * p
        p[j] += gamma
    return p, np.array(gaps), np.array(values)


def counts_from_samples(samples: np.ndarray, n: int) -> np.ndarray:
    return np.bincount(samples, minlength=2**n).astype(float)


def bits_to_int(bits: np.ndarray) -> np.ndarray:
    return (bits.astype(np.int64) << np.arange(bits.shape[1])).sum(axis=1)
