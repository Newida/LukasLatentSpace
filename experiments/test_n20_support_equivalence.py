"""Test the n=20 fully corrective FW support-equivalence claim.

The notebook uses a fully corrective Frank-Wolfe loop with an outer support
search count T and an inner restricted Frank-Wolfe count R.  This script tests
whether T=x, R=y gives the same result as T=1, R=x*y when the active support
does not change.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import sys

import numpy as np


N = 20
LAMBDA = 5e7
SEED = 7
PRUNING_THRESHOLD = 1e-12


def hamming_noise_sample(center: int, n: int, flip_probability: float, rng) -> int:
    mask = 0
    for bit in range(n):
        if rng.random() < flip_probability:
            mask ^= 1 << bit
    return center ^ mask


def build_counts() -> Counter[int]:
    rng = np.random.default_rng(SEED)
    center_labels = [
        "00000000000000000000",
        "11110000111100001111",
        "10101010101010101010",
    ]
    centers = [int(label, 2) for label in center_labels]

    samples = []
    for center, sample_count, flip_probability in zip(
        centers,
        [30, 30, 30],
        [0.045, 0.055, 0.065],
    ):
        samples.extend(
            hamming_noise_sample(center, N, flip_probability, rng)
            for _ in range(sample_count)
        )

    return Counter(samples)


@dataclass
class SparseProblem:
    counts: Counter[int]
    n: int = N
    lam: float = LAMBDA
    neighbor_cache: dict[int, list[int]] = field(default_factory=dict)

    @property
    def observed(self) -> set[int]:
        return set(self.counts)

    @property
    def sample_count(self) -> int:
        return sum(self.counts.values())

    def empirical_distribution(self) -> dict[int, float]:
        total = self.sample_count
        return {x: count / total for x, count in self.counts.items()}

    def neighbors(self, x: int) -> list[int]:
        neighbors = self.neighbor_cache.get(x)
        if neighbors is None:
            neighbors = [x ^ (1 << bit) for bit in range(self.n)]
            self.neighbor_cache[x] = neighbors
        return neighbors

    def candidate_set(self, active_set: set[int]) -> set[int]:
        candidates = set(active_set)
        for x in active_set:
            candidates.update(self.neighbors(x))
        return candidates

    def smoothness_energy(self, p: dict[int, float]) -> float:
        seen_edges = set()
        total = 0.0

        for x, px in p.items():
            if px == 0.0:
                continue
            for y in self.neighbors(x):
                edge = (x, y) if x < y else (y, x)
                if edge in seen_edges:
                    continue
                seen_edges.add(edge)
                diff = px - p.get(y, 0.0)
                total += diff * diff

        return 2.0 * total / (2**self.n)

    def mle_objective(self, p: dict[int, float]) -> float:
        total = 0.0
        for x, count in self.counts.items():
            px = p.get(x, 0.0)
            if px <= 0.0:
                return float("inf")
            total -= count * np.log(px)
        return float(total)

    def objective(self, p: dict[int, float]) -> float:
        return self.mle_objective(p) + self.lam * self.smoothness_energy(p)

    def smoothness_gradient_coordinate(self, x: int, p: dict[int, float]) -> float:
        px = p.get(x, 0.0)
        neighbor_sum = sum(px - p.get(y, 0.0) for y in self.neighbors(x))
        return 4.0 * neighbor_sum / (2**self.n)

    def gradient_coordinate(self, x: int, p: dict[int, float]) -> float:
        px = p.get(x, 0.0)
        count = self.counts.get(x, 0)

        if count > 0:
            if px <= 0.0:
                return -float("inf")
            mle_grad = -count / px
        else:
            mle_grad = 0.0

        return mle_grad + self.lam * self.smoothness_gradient_coordinate(x, p)


def stable_argmin(gradients: dict[int, float]) -> int:
    return min(gradients, key=lambda x: (gradients[x], x))


def prune_support(
    p: dict[int, float],
    active_set: set[int],
    observed_set: set[int],
    threshold: float,
) -> tuple[dict[int, float], set[int], int, float]:
    kept = {
        x: px
        for x, px in p.items()
        if x in observed_set or px > threshold
    }
    removed_mass = sum(px for x, px in p.items() if x not in kept)

    if removed_mass > 0.0:
        normalization = sum(kept.values())
        kept = {x: px / normalization for x, px in kept.items()}

    pruned_active = (set(active_set) & set(kept)) | set(observed_set)
    pruned_atoms = len(set(active_set) - pruned_active)
    return kept, pruned_active, pruned_atoms, removed_mass


def restricted_frank_wolfe(
    problem: SparseProblem,
    p: dict[int, float],
    active_set: set[int],
    inner_iterations: int,
    start_r: int = 1,
    tol: float = 1e-8,
) -> tuple[dict[int, float], float, int | None, int]:
    active = set(active_set)
    last_gap = float("nan")
    last_atom = None
    steps_taken = 0

    for offset in range(inner_iterations):
        r = start_r + offset
        gradients = {x: problem.gradient_coordinate(x, p) for x in active}
        last_atom = stable_argmin(gradients)
        average_gradient = sum(p.get(x, 0.0) * gradients[x] for x in active)
        last_gap = average_gradient - gradients[last_atom]
        if last_gap <= tol:
            break

        direction = {x: -px for x, px in p.items() if x in active}
        direction[last_atom] = direction.get(last_atom, 0.0) + 1.0
        gamma = 2.0 / (2.0 + r)

        keys = set(p) | set(direction)
        p = {
            x: p.get(x, 0.0) + gamma * direction.get(x, 0.0)
            for x in keys
            if p.get(x, 0.0) + gamma * direction.get(x, 0.0) > 0.0
        }
        steps_taken += 1

    return p, last_gap, last_atom, steps_taken


def fully_corrective_frank_wolfe(
    problem: SparseProblem,
    outer_iterations: int,
    inner_iterations: int,
    continue_inner_clock: bool = False,
    pruning_threshold: float = PRUNING_THRESHOLD,
) -> tuple[dict[int, float], set[int], list[dict[str, float | int | bool | None]]]:
    observed = problem.observed
    active = set(observed)
    p = problem.empirical_distribution()
    history = []
    next_inner_r = 1

    for outer_iter in range(1, outer_iterations + 1):
        candidates = problem.candidate_set(active)
        outer_gradients = {
            x: problem.gradient_coordinate(x, p)
            for x in candidates
        }
        new_atom = stable_argmin(outer_gradients)
        was_new = new_atom not in active
        active.add(new_atom)

        start_r = next_inner_r if continue_inner_clock else 1
        p, inner_gap, inner_atom, steps_taken = restricted_frank_wolfe(
            problem,
            p,
            active,
            inner_iterations,
            start_r=start_r,
        )
        if continue_inner_clock:
            next_inner_r += steps_taken

        active_size_before_pruning = len(active)
        p, active, pruned_atoms, pruned_mass = prune_support(
            p,
            active,
            observed,
            pruning_threshold,
        )

        history.append(
            {
                "outer_iter": outer_iter,
                "objective": problem.objective(p),
                "inner_gap": inner_gap,
                "active_size_before_pruning": active_size_before_pruning,
                "active_size_after_pruning": len(active),
                "positive_support": sum(px > pruning_threshold for px in p.values()),
                "pruned_atoms": pruned_atoms,
                "pruned_mass": pruned_mass,
                "new_atom": new_atom,
                "was_new": was_new,
                "inner_atom": inner_atom,
                "steps_taken": steps_taken,
            }
        )

    return p, active, history


def distribution_distance(
    left: dict[int, float],
    right: dict[int, float],
) -> tuple[float, float]:
    keys = set(left) | set(right)
    distances = [abs(left.get(x, 0.0) - right.get(x, 0.0)) for x in keys]
    return sum(distances), max(distances, default=0.0)


def support_unchanged(
    history: list[dict[str, float | int | bool | None]],
    observed_size: int,
) -> bool:
    return all(
        (not item["was_new"])
        and item["active_size_before_pruning"] == observed_size
        and item["active_size_after_pruning"] == observed_size
        for item in history
    )


def compare_pair(
    problem: SparseProblem,
    outer_iterations: int,
    inner_iterations: int,
    continue_inner_clock: bool = False,
) -> dict[str, float | int | bool]:
    left_p, left_active, left_history = fully_corrective_frank_wolfe(
        problem,
        outer_iterations,
        inner_iterations,
        continue_inner_clock=continue_inner_clock,
    )
    right_p, right_active, right_history = fully_corrective_frank_wolfe(
        problem,
        1,
        outer_iterations * inner_iterations,
        continue_inner_clock=continue_inner_clock,
    )
    l1_distance, max_abs_distance = distribution_distance(left_p, right_p)

    return {
        "T": outer_iterations,
        "R": inner_iterations,
        "total_inner": outer_iterations * inner_iterations,
        "same_active": left_active == right_active,
        "support_unchanged": support_unchanged(left_history, len(problem.observed)),
        "objective_left": problem.objective(left_p),
        "objective_right": problem.objective(right_p),
        "objective_delta": problem.objective(left_p) - problem.objective(right_p),
        "l1_distance": l1_distance,
        "max_abs_distance": max_abs_distance,
    }


def print_table(title: str, rows: list[dict[str, float | int | bool]]) -> None:
    print(f"\n{title}")
    print(
        "T   R    T*R   unchanged  same_active  "
        "objective(T,R)  objective(1,T*R)  delta       L1_dist    max_abs"
    )
    for row in rows:
        print(
            f"{row['T']:>1}  "
            f"{row['R']:>3}  "
            f"{row['total_inner']:>5}  "
            f"{str(row['support_unchanged']):>9}  "
            f"{str(row['same_active']):>11}  "
            f"{row['objective_left']:>14.6f}  "
            f"{row['objective_right']:>17.6f}  "
            f"{row['objective_delta']:>10.6f}  "
            f"{row['l1_distance']:>9.6f}  "
            f"{row['max_abs_distance']:>8.6f}"
        )


def main() -> None:
    print(sys.executable)
    if "/.venv/" not in sys.executable and not sys.executable.endswith("/.venv/bin/python"):
        raise RuntimeError("Run this script with ./.venv/bin/python")

    counts = build_counts()
    problem = SparseProblem(counts)

    print(f"n = {problem.n}, full states = {2**problem.n:,}, samples = {problem.sample_count}")
    print(f"seed = {SEED}, observed states = {len(problem.observed)}, lambda = {problem.lam:.2e}")

    pairs = [(2, 20), (4, 20), (8, 20), (8, 40), (5, 60), (120, 300)]
    reset_rows = [
        compare_pair(problem, t, r, continue_inner_clock=False)
        for t, r in pairs
    ]
    print_table("Old behavior: inner step-size schedule resets each outer loop", reset_rows)

    continuous_rows = [
        compare_pair(problem, t, r, continue_inner_clock=True)
        for t, r in [(8, 40), (5, 60)]
    ]
    print_table("Control: same experiment with a continuous inner step-size clock", continuous_rows)

    reset_equivalent = all(row["l1_distance"] < 1e-12 for row in reset_rows)
    continuous_equivalent = all(row["l1_distance"] < 1e-12 for row in continuous_rows)

    print("\nVerdict")
    print(f"theory true for old reset implementation: {reset_equivalent}")
    print(f"theory true if the inner FW clock is not reset: {continuous_equivalent}")


if __name__ == "__main__":
    main()
