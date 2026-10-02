"""Experiments for the paper 'Smoothing bitstring distributions'.

Usage: python run_experiments.py [e1 e2 e3 e4 e5 e6]   (default: all)
Writes JSON to results/ and PDF figures to ../figures/.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from hypercube import (
    bits_to_int,
    counts_from_samples,
    dirichlet_energy,
    flip_probability,
    frank_wolfe_p1,
    fw_gap,
    heat_smooth,
    laplacian_apply,
    laplacian_dense,
    p1_gradient,
    p1_objective,
    popcount,
    sample_tikhonov,
    solve_p1,
    spectral_filter,
    tikhonov_distance_kernel,
    tikhonov_distance_kernel_krawtchouk,
    tikhonov_smooth,
    wht,
)

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
FIGURES = HERE.parent / "figures"
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


def save(name: str, payload: dict) -> None:
    with open(RESULTS / f"{name}.json", "w") as f:
        json.dump(payload, f, indent=2, default=float)
    print(f"[saved] results/{name}.json")


def plt_setup():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
    })
    return plt


# ---------------------------------------------------------------- E1 identities
def e1() -> None:
    """Dirichlet energy = Laplacian form; Walsh basis diagonalises L; (I+muL)^-1 is
    a positive, doubly stochastic kernel equal to an exponential mixture of
    independent-bit-flip channels."""
    rng = np.random.default_rng(1)
    out = {}
    for n in (4, 6, 8, 10):
        d = 2**n
        p = rng.random(d)
        p /= p.sum()
        L = laplacian_dense(n)
        H = np.array([wht(e) for e in np.eye(d)]).T
        row = {
            "energy_identity_err": abs(dirichlet_energy(p, n) - 2 ** (1 - n) * p @ L @ p),
            "wht_diag_err": float(np.abs(H @ L @ H / d - np.diag(2.0 * popcount(n))).max()),
        }
        for mu in (0.01, 1.0, 100.0):
            K = np.linalg.inv(np.eye(d) + mu * L)
            k_closed = tikhonov_distance_kernel(n, mu)
            dist = popcount(n)  # Hamming distance from 0
            row[f"mu={mu}"] = {
                "K_min": float(K.min()),
                "K_colsum_err": float(np.abs(K.sum(axis=0) - 1).max()),
                "filter_vs_inverse_err": float(np.abs(tikhonov_smooth(p, n, mu) - K @ p).max()),
                "closed_form_kernel_err": float(np.abs(K[0] - k_closed[dist]).max() / K.max()),
            }
        out[f"n={n}"] = row

    # Sampler correctness at n=10: empirical TV between sampler and exact filter.
    n, mu = 10, 0.3
    data = rng.integers(0, 2**n, size=25)
    p_hat = counts_from_samples(data, n) / data.size
    exact = tikhonov_smooth(p_hat, n, mu)
    tvs = {}
    for size in (10**4, 10**5, 10**6):
        draws = bits_to_int(sample_tikhonov(data, n, mu, size, rng))
        emp = counts_from_samples(draws, n) / size
        # reference: TV between exact and an iid sample of the same size from exact
        ref = counts_from_samples(rng.choice(2**n, size=size, p=exact), n) / size
        tvs[size] = {"tv_sampler": 0.5 * np.abs(emp - exact).sum(),
                     "tv_iid_reference": 0.5 * np.abs(ref - exact).sum()}
    out["sampler_tv_n10"] = tvs
    save("e1_identities", out)


# ---------------------------------------------------------------- E2 n=3 example
def e2() -> None:
    plt = plt_setup()
    n = 3
    labels = [format(i, "03b") for i in range(8)]
    counts = np.zeros(8)
    for s, v in {"000": 10, "001": 6, "010": 5, "100": 5, "111": 2}.items():
        counts[int(s, 2)] = v
    lam = 200.0
    mu = lam * 2 ** (1 - n)
    p_star, info = solve_p1(counts, n, mu, tol=1e-12, max_iter=200_000)
    p_fw, gaps, values = frank_wolfe_p1(counts, n, mu, np.ones(8) / 8, 100_000)
    p_hat = counts / counts.sum()
    # Distribution-level comparison with the closed-form P2 filter at the mu that
    # matches P1's unobserved mass (scales of P1 and P2 differ by ~m^2).
    mus = np.logspace(-3, 1, 400)
    unobs_star = p_star[counts == 0].sum()
    unobs = np.array([tikhonov_smooth(p_hat, n, m_)[counts == 0].sum() for m_ in mus])
    mu_match = float(mus[np.argmin(np.abs(unobs - unobs_star))])
    p_p2 = tikhonov_smooth(p_hat, n, mu_match)
    f_star = info["objective"]
    payload = {
        "lambda": lam, "mu": mu, "solver": info,
        "p_star": dict(zip(labels, p_star)),
        "p_fw_1500": dict(zip(labels, frank_wolfe_p1(counts, n, mu, np.ones(8) / 8, 1500)[0])),
        "fw_1500_gap": float(gaps[1499]), "fw_1500_subopt": float(values[1499] - f_star),
        "fw_100k_gap": float(gaps[-1]), "fw_100k_subopt": float(values[-1] - f_star),
        "empirical_objective": p1_objective(p_hat + 0.0, counts, n, mu),
        "p2_mu_matched": mu_match, "p2": dict(zip(labels, p_p2)),
        "energy": {"empirical": dirichlet_energy(p_hat, n), "p1": dirichlet_energy(p_star, n),
                   "p2": dirichlet_energy(p_p2, n)},
    }
    save("e2_n3", payload)

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.4))
    pos = np.arange(8)
    w = 0.27
    axes[0].bar(pos - w, p_hat, w, label="empirical", color="#9aa5b1")
    axes[0].bar(pos, p_star, w, label=r"(P1) optimum", color="#2b6cb0")
    axes[0].bar(pos + w, p_p2, w, label=r"(P2) filter", color="#dd6b20")
    axes[0].set_xticks(pos, labels, fontsize=7)
    axes[0].set_ylabel("probability")
    axes[0].legend(frameon=False, fontsize=7)
    t = np.arange(1, gaps.size + 1)
    axes[1].loglog(t, values - f_star, label=r"$f(p_t)-f^\star$", color="#2b6cb0")
    axes[1].loglog(t, gaps, label="FW gap", color="#dd6b20", alpha=0.8)
    axes[1].loglog(t, 30 / t, "k--", lw=0.8, label=r"$\propto 1/t$")
    axes[1].set_xlabel("Frank–Wolfe iteration $t$")
    axes[1].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_n3.pdf")
    print("[saved] figures/fig_n3.pdf")


# ---------------------------------------------------------------- E3 n=20 sparse
def _ball(centers: list[int], n: int, radius: int) -> np.ndarray:
    states = set(centers)
    frontier = set(centers)
    for _ in range(radius):
        nxt = set()
        for x in frontier:
            for i in range(n):
                y = x ^ (1 << i)
                if y not in states:
                    nxt.add(y)
        states |= nxt
        frontier = nxt
    return np.array(sorted(states), dtype=np.int64)


def _restricted_laplacian(states: np.ndarray, n: int):
    from scipy.sparse import csr_matrix

    index = {int(s): k for k, s in enumerate(states)}
    rows, cols = [], []
    for k, s in enumerate(states):
        for i in range(n):
            j = index.get(int(s) ^ (1 << i))
            if j is not None:
                rows.append(k)
                cols.append(j)
    A = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(states.size, states.size))
    return lambda p: n * p - A @ p


def _global_certificate(states, p, counts_sub, n, mu, lap):
    """FW gap of a ball-supported p over the full hypercube.

    Outside the ball, g_x = 2 mu (L p)_x = -2 mu sum_{y~x, y in ball} p_y (<= 0),
    which is nonzero only on the outer boundary; farther states have g_x = 0."""
    g = p1_gradient(p, counts_sub, lap, mu)
    inside = set(int(s) for s in states)
    boundary: dict[int, float] = {}
    for s, ps in zip(states, p):
        if ps == 0.0:
            continue
        for i in range(n):
            y = int(s) ^ (1 << i)
            if y not in inside:
                boundary[y] = boundary.get(y, 0.0) - 2 * mu * ps
    g_min = min(g.min(), min(boundary.values(), default=0.0), 0.0)
    return float(np.dot(g, p) - g_min), g


def e3() -> None:
    sys.path.insert(0, str(HERE.parent.parent.parent / "experiments"))
    import test_n20_support_equivalence as fc

    counts_c = fc.build_counts()
    n, lam = fc.N, fc.LAMBDA
    mu = lam * 2 ** (1 - n)
    problem = fc.SparseProblem(counts_c)
    m = problem.sample_count

    t0 = time.time()
    p_fc, active_fc, hist = fc.fully_corrective_frank_wolfe(problem, 2, 3000, continue_inner_clock=True)
    t_fc = time.time() - t0
    obj_fc = problem.objective(p_fc)

    out = {"n": n, "lambda": lam, "mu": mu, "m": m, "distinct": len(counts_c),
           "fcfw": {"objective": obj_fc, "support": len(p_fc), "seconds": t_fc}}
    for radius in (1, 2):
        states = _ball(list(counts_c), n, radius)
        lap = _restricted_laplacian(states, n)
        cs = np.array([counts_c.get(int(s), 0) for s in states], dtype=float)
        t0 = time.time()
        p, info = solve_p1(cs, lap, mu, tol=1e-10, max_iter=100_000)
        cert, g = _global_certificate(states, p, cs, n, mu, lap)
        support = p > 1e-12
        nu = float(-m + 2 * mu * p @ lap(p))
        bound = float(np.sum(cs[cs > 0] / p[cs > 0]) / (-nu)) if nu < 0 else math.inf
        dist_from_data = []
        obs = [int(s) for s in states[cs > 0]]
        for s in states[support & (cs == 0)]:
            dist_from_data.append(min(bin(int(s) ^ o).count("1") for o in obs))
        out[f"exact_ball_r{radius}"] = {
            "ball_size": int(states.size), "seconds": time.time() - t0, "solver": info,
            "objective": p1_objective(p, cs, lap, mu), "global_fw_gap": cert,
            "support": int(support.sum()), "unobserved_support": int((support & (cs == 0)).sum()),
            "unobserved_mass": float(p[cs == 0].sum()), "nu": nu, "support_bound": bound,
            "max_dist_unobserved_support": max(dist_from_data, default=0),
            "top_probs": sorted(p[cs > 0].tolist(), reverse=True)[:3],
        }
        if radius == 2:
            p_exact_r2 = dict(zip(states.tolist(), p.tolist()))
    l1 = sum(abs(p_fc.get(x, 0.0) - p_exact_r2.get(x, 0.0)) for x in set(p_fc) | set(p_exact_r2))
    out["l1_fcfw_vs_exact"] = l1

    # Support-equivalence table (reset vs continuous inner clock).
    rows = []
    for clock in (False, True):
        for t, r in ((8, 40), (5, 60)):
            row = fc.compare_pair(problem, t, r, continue_inner_clock=clock)
            row["continuous_clock"] = clock
            rows.append(row)
    out["support_equivalence"] = rows

    # Same data under the closed-form filter (P2): where does the mass go?
    # Mass by Hamming distance to the nearest observed state, via the closed-form kernel
    # (exact; the full 2^20 vector is also cheap here, so we cross-check).
    p_hat = np.zeros(2**n)
    for x, c in counts_c.items():
        p_hat[x] = c / m
    p2_rows = {}
    nearest = _nearest_distance(list(counts_c), n)
    for mu2 in (0.01, 0.1, 1.0):
        p2 = tikhonov_smooth(p_hat, n, mu2)
        mass = np.bincount(nearest, weights=p2, minlength=n + 1)
        p2_rows[mu2] = {"min": float(p2.min()), "mass_by_distance": mass[:6].tolist(),
                        "mass_on_observed": float(mass[0])}
    out["p2_mass_profile"] = p2_rows
    save("e3_n20", out)


def _nearest_distance(centers: list[int], n: int) -> np.ndarray:
    """Hamming distance from every state to the nearest center (multi-source BFS)."""
    dist = np.full(2**n, -1, dtype=np.int64)
    frontier = np.array(centers, dtype=np.int64)
    dist[frontier] = 0
    level = 0
    while frontier.size:
        level += 1
        nxt = np.unique((frontier[:, None] ^ (1 << np.arange(n))[None, :]).ravel())
        nxt = nxt[dist[nxt] < 0]
        dist[nxt] = level
        frontier = nxt
    return dist


# ---------------------------------------------------------------- E4 generalisation
def _make_target(kind: str, n: int, rng) -> np.ndarray:
    centers = rng.integers(0, 2**n, size=4)
    d = popcount(n)
    p = np.zeros(2**n)
    x = np.arange(2**n)
    for c in centers:
        dist = popcount(n)[x ^ c]
        p += 0.1 ** dist * 0.9 ** (n - dist)
    p /= p.sum()
    if kind == "checksum":
        p = np.where(d % 2 == 0, p, 0.0)
        p /= p.sum()
    return p


def _quadratic_score(q: np.ndarray, val: np.ndarray) -> float:
    """Proper scoring rule ||q||^2 - 2 mean_{x in val} q(x) (estimates ||q-p||^2 - ||p||^2)."""
    return float(q @ q - 2.0 * q[val].mean())


def fit_shell_mixture(counts: np.ndarray, n: int, iters: int = 2000) -> np.ndarray:
    """Learn the best positivity-preserving isotropic filter by leave-one-out
    maximum likelihood. The LOO likelihood is concave in the shell weights w,
    so EM converges to the global optimum. Returns the filtered distribution."""
    sample = np.repeat(np.arange(2**n), counts.astype(int))
    m = sample.size
    dist = popcount(n)[sample[:, None] ^ sample[None, :]]
    binom = np.array([math.comb(n, d) for d in range(n + 1)], dtype=float)
    A = np.zeros((m, n + 1))
    for j in range(m):
        row = np.bincount(np.delete(dist[j], j), minlength=n + 1)
        A[j] = row / (m - 1) / binom
    w = np.full(n + 1, 1.0 / (n + 1))
    for _ in range(iters):
        mix = A @ w
        w_new = w * (A / mix[:, None]).mean(axis=0)
        if np.abs(w_new - w).max() < 1e-10:
            w = w_new
            break
        w = w_new
    h = (w / binom) @ krawtchouk_matrix(n)  # h(k) = sum_d w_d K_d(k) / C(n, d)
    return spectral_filter(counts / m, n, h)


def _estimators(n: int):
    d = 2**n
    return {
        "empirical": ([None], lambda c, h: c / c.sum()),
        "add-alpha": (np.logspace(-3, 1, 9), lambda c, a: (c + a) / (c.sum() + a * d)),
        "heat (Aitchison-Aitken)": (np.linspace(0.005, 0.35, 15),
                                    lambda c, th: heat_smooth(c / c.sum(), n, -0.5 * math.log(1 - 2 * th))),
        "Tikhonov (P2)": (np.logspace(-3, 1.5, 15), lambda c, mu: tikhonov_smooth(c / c.sum(), n, mu)),
        "penalised MLE (P1)": (np.logspace(-6, 2, 9),
                               lambda c, a: solve_p1(c, n, a * c.sum() ** 2 / n, tol=1e-7, max_iter=4000)[0]),
        "learned isotropic (LOO-EM)": ([None], lambda c, h: fit_shell_mixture(c, n)),
    }


def e4(only: list[str] | None = None) -> None:
    """only: recompute just these estimators and merge into the saved results."""
    plt = plt_setup()
    n = 10
    seeds = range(10)
    ms = (30, 100, 300, 1000)
    results = {}
    estimators = {k: v for k, v in _estimators(n).items() if only is None or k in only}
    for kind in ("clusters", "checksum"):
        for m in ms:
            for seed in seeds:
                rng = np.random.default_rng(1000 * seed + m)
                p_true = _make_target(kind, n, np.random.default_rng(seed))
                sample = rng.choice(2**n, size=m, p=p_true)
                perm = rng.permutation(m)
                n_val = max(m // 5, 5)
                val, train = sample[perm[:n_val]], sample[perm[n_val:]]
                c_train = counts_from_samples(train, n)
                c_all = counts_from_samples(sample, n)
                for name, (grid, fit) in estimators.items():
                    scores = [_quadratic_score(fit(c_train, h), val) for h in grid]
                    best = grid[int(np.argmin(scores))]
                    q = fit(c_all, best)
                    q = np.maximum(q, 0.0)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        kl = float(np.sum(np.where(p_true > 0, p_true * np.log(p_true / q), 0.0)))
                    rec = results.setdefault(f"{kind}|{m}|{name}", {"tv": [], "kl": [], "invalid": [], "h": []})
                    rec["tv"].append(0.5 * float(np.abs(q - p_true).sum()))
                    rec["kl"].append(kl)
                    rec["invalid"].append(float(q[p_true == 0].sum()))
                    rec["h"].append(None if best is None else float(best))
            print(kind, m, "done", flush=True)
    summary = {}
    for key, rec in results.items():
        tv = np.array(rec["tv"])
        kl = np.array(rec["kl"])
        summary[key] = {
            "tv_mean": tv.mean(), "tv_se": tv.std(ddof=1) / math.sqrt(tv.size),
            "kl_median": float(np.median(kl)), "kl_finite_frac": float(np.isfinite(kl).mean()),
            "invalid_mass_mean": float(np.mean(rec["invalid"])), "h": rec["h"],
        }
    if only is not None:
        with open(RESULTS / "e4_generalisation.json") as f:
            summary = {**json.load(f)["summary"], **summary}
    save("e4_generalisation", {"n": n, "ms": ms, "seeds": len(seeds), "summary": summary})

    names = list(_estimators(n))
    colors = ["#9aa5b1", "#718096", "#38a169", "#dd6b20", "#2b6cb0", "#805ad5"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    for ax, kind in zip(axes, ("clusters", "checksum")):
        for name, col in zip(names, colors):
            mean = [summary[f"{kind}|{m}|{name}"]["tv_mean"] for m in ms]
            se = [summary[f"{kind}|{m}|{name}"]["tv_se"] for m in ms]
            ax.errorbar(ms, mean, yerr=se, marker="o", ms=3, lw=1.2, capsize=2, label=name, color=col)
        ax.set_xscale("log")
        ax.set_xlabel("training samples $m$")
        ax.set_title({"clusters": "clustered target", "checksum": "clustered target with parity checksum"}[kind],
                     fontsize=8)
    axes[0].set_ylabel("total variation to truth")
    axes[0].legend(frameon=False, fontsize=6.5)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_generalisation.pdf")
    print("[saved] figures/fig_generalisation.pdf")


# ---------------------------------------------------------------- E5 large n sampling
def e5() -> None:
    plt = plt_setup()
    from math import comb

    rng = np.random.default_rng(5)
    n, m, mu = 100, 50, 0.05
    data = rng.random((m, n)) < 0.5
    size = 200_000
    t0 = time.time()
    draws = sample_tikhonov(data, n, mu, size, rng)
    t_sample = time.time() - t0
    # Validate the law of the number of flipped bits against the closed form.
    s = rng.exponential(1.0, size=size)
    flips = rng.random((size, n)) < flip_probability(mu * s)[:, None]
    dist = flips.sum(axis=1)
    k = tikhonov_distance_kernel(n, mu)
    law = np.array([comb(n, d) * k[d] for d in range(n + 1)])
    emp = np.bincount(dist, minlength=n + 1) / size
    # Exact log-density of a few test points, O(m n) each.
    t0 = time.time()
    test = rng.random((1000, n)) < 0.5
    dists = (test[:, None, :] ^ data[None, :, :]).sum(axis=2)
    dens = k[dists].mean(axis=1)
    t_density = (time.time() - t0) / test.shape[0]
    payload = {
        "n": n, "m": m, "mu": mu, "samples": size, "sample_seconds": t_sample,
        "distance_law_tv": 0.5 * float(np.abs(emp - law).sum()), "law_mass": float(law.sum()),
        "density_seconds_per_point": t_density, "mean_log2_density_random_point": float(np.mean(np.log2(dens))),
    }
    save("e5_large_n", payload)

    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    ax.bar(np.arange(n + 1), emp, color="#9aa5b1", width=1.0, label="sampler (2·10$^5$ draws)")
    ax.plot(np.arange(n + 1), law, color="#2b6cb0", lw=1.4, label=r"exact $\binom{n}{d}k_\mu(d)$")
    ax.set_xlim(-1, 60)
    ax.set_xlabel("Hamming distance $d$ from source sample")
    ax.set_ylabel("probability")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_large_n.pdf")
    print("[saved] figures/fig_large_n.pdf")


# ---------------------------------------------------------------- E6 filter zoo
def krawtchouk_matrix(n: int) -> np.ndarray:
    """K[k, d] = K_k(d; n) = sum_j (-1)^j C(d, j) C(n-d, k-j) (exact integers)."""
    K = np.zeros((n + 1, n + 1))
    for d in range(n + 1):
        for k in range(n + 1):
            K[k, d] = sum((-1) ** j * math.comb(d, j) * math.comb(n - d, k - j) for j in range(min(d, k) + 1))
    return K


def shell_weights(h: np.ndarray, n: int) -> np.ndarray:
    """Shell weights w_d = C(n,d) kappa(d) of an isotropic filter h(|S|), whose
    convolution kernel is
        kappa(z) = 2^{-n} sum_S h(|S|) chi_S(z) = 2^{-n} sum_k h(k) K_k(|z|).
    """
    K = krawtchouk_matrix(n)
    kappa = (h @ K) / 2**n
    return np.array([math.comb(n, d) for d in range(n + 1)]) * kappa


def e6() -> None:
    plt = plt_setup()
    n = 20
    k = np.arange(n + 1)
    theta, mu, t = 0.1, 0.2, 0.15
    filters = {
        r"noise $(1-2\theta)^{k}$": (1 - 2 * theta) ** k,
        r"heat $e^{-2tk}$": np.exp(-2 * t * k),
        r"Tikhonov $1/(1+2\mu k)$": 1 / (1 + 2 * mu * k),
        r"band-limit $\mathbf{1}[k\leq 2]$": (k <= 2).astype(float),
        r"Gaussian $e^{-k^2/8}$": np.exp(-(k**2) / 8.0),
    }
    out = {}
    for name, h in filters.items():
        w = shell_weights(h, n)
        out[name] = {"h": h.tolist(), "w": w.tolist(), "w_min": float(w.min()), "w_sum": float(w.sum()),
                     "positive": bool(w.min() >= -1e-12)}
    # sanity: Tikhonov shell weights equal C(n,d) k_mu(d) from the closed form
    out["tikhonov_closed_form_err"] = float(np.abs(
        shell_weights(1 / (1 + 2 * mu * k), n)
        - np.array([math.comb(n, d) for d in range(n + 1)]) * tikhonov_distance_kernel(n, mu)).max())
    # max negative mass produced by band-limiting an empirical distribution, n=10
    rng = np.random.default_rng(6)
    n_s = 10
    worst = []
    for _ in range(20):
        sample = rng.integers(0, 2**n_s, size=30)
        q = spectral_filter(counts_from_samples(sample, n_s) / 30, n_s, (np.arange(n_s + 1) <= 2).astype(float))
        worst.append(float(-q[q < 0].sum()))
    out["bandlimit_negative_mass_n10_m30"] = {"mean": float(np.mean(worst)), "max": float(np.max(worst))}
    save("e6_filters", out)

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.4))
    colors = ["#38a169", "#805ad5", "#dd6b20", "#e53e3e", "#2b6cb0"]
    for (name, h), col in zip(filters.items(), colors):
        axes[0].plot(k, h, marker="o", ms=2.5, lw=1.1, label=name, color=col)
        w = np.array(out[name]["w"])
        axes[1].plot(k, w, marker="o", ms=2.5, lw=1.1, color=col)
    axes[0].set_xlabel("Fourier level $k=|S|$")
    axes[0].set_ylabel("filter $h(k)$")
    axes[0].legend(frameon=False, fontsize=6.5)
    axes[1].axhline(0, color="k", lw=0.6)
    axes[1].set_xlabel("Hamming distance $d$")
    axes[1].set_ylabel(r"shell weight $w_d=\binom{n}{d}\kappa(d)$")
    axes[1].set_xlim(-0.5, 12)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_filters.pdf")
    print("[saved] figures/fig_filters.pdf")


if __name__ == "__main__":
    which = sys.argv[1:] or ["e1", "e2", "e3", "e4", "e5", "e6"]
    for name in which:
        t0 = time.time()
        if ":" in name:  # e.g. "e4:penalised MLE (P1)" reruns one estimator
            name, only = name.split(":", 1)
            globals()[name](only=[only])
        else:
            globals()[name]()
        print(f"{name} finished in {time.time() - t0:.1f}s", flush=True)
