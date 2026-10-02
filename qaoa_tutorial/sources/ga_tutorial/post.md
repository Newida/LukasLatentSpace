# Genetic Algorithms on the Hamming Cube

In this post, I want to understand genetic algorithms the same way we looked at QAOA in the last post (QAOAOnTheHammingCube): as dynamics on the Hamming cube.

Spoiler: a genetic algorithm without crossover is QAOA in imaginary time. And, as it turns out, it is also a quantum spin chain, just one that is evolved in a very non-quantum way. But let us build this up slowly.

## The problem

1. We stay with the same problem as last time.

<a id="problem-1"></a>

> **Problem 1: MaxCut.**  
> Given a graph $G = (V, E)$ with $n$ vertices, split the vertices into two sides such that as many edges as possible go between the two sides.

A split is a bitstring $x \in \{0,1\}^n$ and the number of cut edges is $C(x) = \sum_{(i,j) \in E} [x_i \neq x_j]$. We want the corner of the Hamming cube where $C$ is largest.

2. The genetic algorithm idea in one sentence: keep a population of candidate solutions, let them reproduce with small copying errors, and let the better ones have more offspring. Nature has been doing this for a while, and Holland turned it into an algorithm in the 1970s.

## A genetic algorithm in five lines

1. Here is the simplest version I can think of:

```
population = N random bitstrings
repeat:
    selection: draw N new strings from the population,
               each with probability proportional to exp(gamma * C(x))
    mutation:  flip every bit of every string independently with probability q
    remember the best string seen so far
```

2. There are two knobs. $\gamma$ says how greedy selection is: $\gamma = 0$ ignores the cost completely, a large $\gamma$ almost only copies the current best strings. $q$ says how much mutation happens.

3. Real genetic algorithms also do **crossover**, mixing two parents into one child. We will come back to that at the very end. Without it, things get surprisingly clean.

## From a population to a distribution

1. Let us make the population infinitely large. Then it becomes a probability distribution $p$ over the $2^n$ corners of the cube, and both steps act on $p$.

a) Selection multiplies by the weights and renormalizes:

$$
p(x) \;\leftarrow\; \frac{e^{\gamma C(x)}\, p(x)}{\sum_y e^{\gamma C(y)}\, p(y)} .
$$

In matrix form this is the diagonal matrix $S = \mathrm{diag}\big(e^{\gamma C(x)}\big)$, followed by a normalization.

b) Mutation turns a parent $y$ into a child $x$ with probability

$$
M_{xy} = q^{\,d(x,y)}\,(1-q)^{\,n - d(x,y)},
$$

where $d(x,y)$ is the Hamming distance.

c) So one generation is

$$
p \;\leftarrow\; \frac{M S\, p}{\mathbf{1}^T M S\, p} .
$$

2. Look closely: apart from the normalization, this is linear! The infinite-population genetic algorithm is nothing else than the **power method** for the matrix $MS$.

## Mutation is diffusion, selection is a potential

1. $M$ is exactly the heat kernel from the last post. Flipping every bit independently with probability $q$ is diffusion on the cube for a time $t$ with

$$
q = \frac{1 - e^{-2t}}{2}, \qquad M = e^{-tL} .
$$

2. In the Walsh basis, mutation multiplies mode $s$ by

$$
(1 - 2q)^{|s|} = e^{-2t|s|} .
$$

So mutation is a low-pass filter. Every generation, rough patterns on the cube get damped and smooth ones survive.

3. Selection is diagonal in positions. It multiplies corner $x$ by $e^{\gamma C(x)}$, so it rewards good corners and, in doing so, creates rough patterns again.

4. So one generation is again a split-step method, just in imaginary time. Side by side with QAOA:

```
                  QAOA (real time)                 genetic algorithm (imaginary time)
 cost step        exp(-i gamma C)   phase kick     exp(gamma C)   selection
 mixer step       exp(-i beta A)    rotation       exp(-t L)      mutation, damping
 normalization    automatic, unitary               divide by the total
 long-run fate    keeps oscillating                converges to one fixed point
```

## Where does it converge?

1. The power method converges to the eigenvector of $MS$ with the largest eigenvalue. For $0 < q < 1$ every entry of $MS$ is positive, so by Perron-Frobenius this eigenvector is unique and positive, and we converge to it from any starting population.

2. Biologists call this fixed point the **quasispecies** (Eigen 1971). It is not a single best string but a cloud of mutants around the fit strings, the compromise between selection pulling the population together and mutation spreading it out.

3. Let us look at numbers. I use the triangular prism from the last post: 6 vertices, 9 edges, maximum cut 7, and 6 of the 64 bitstrings are maximum cuts, so random guessing hits one with probability 0.094. Here is the probability of a maximum cut in the quasispecies:

```
                 q = 0.02   q = 0.05   q = 0.1   q = 0.2   q = 0.3
 gamma = 0.5       0.780      0.554     0.344     0.175     0.119
 gamma = 1         0.846      0.662     0.450     0.232     0.141
 gamma = 2         0.876      0.718     0.517     0.276     0.160
```

More selection and less mutation push the cloud onto the optimum. The expected cut for $\gamma = 1$ goes from 5.22 at $q = 0.2$ to 6.76 at $q = 0.02$.

4. And it is fast. For $\gamma = 1$ and $q = 0.05$, starting from the uniform distribution, the probability of a maximum cut over the first generations is

```
 generation       1      2      3      4      5      6     ...   fixed point
 P(max cut)     0.365  0.546  0.620  0.647  0.656  0.660   ...      0.662
```

<!-- TOY:evolve -->

## Too much mutation: the error threshold

1. Turn up $q$ and the cloud melts. Eigen called this the **error threshold**.

2. It is cleanest on a needle: one master string with fitness advantage $\sigma = e^{\gamma}$, all other strings equal. A child of the master is again the master only with probability $(1-q)^n$. The master can hold its ground as long as

$$
\sigma\,(1-q)^n > 1 \quad\iff\quad q < q_c = 1 - \sigma^{-1/n} \approx \frac{\gamma}{n} .
$$

3. Numbers for $n = 20$ and $\gamma = 1$, where $q_c = 0.0488$:

```
 q             0.01   0.02   0.03   0.04   0.045   0.05    0.055
 P(master)     0.71   0.48   0.29   0.13   0.066   0.006   0.000
```

Below the threshold, a large part of the population sits on the master. Just above it, the master is basically gone, and the population is spread over the whole cube.

4. For optimization this is a warning: the mutation rate has to shrink with the problem size, roughly like $1/n$, or the population forgets what it already found.

<!-- TOY:threshold -->

## Plot twist: it is a quantum spin chain

1. For small steps, $M S = e^{-tL} e^{\gamma C} \approx e^{\gamma C - tL}$. So the quasispecies is close to the top eigenvector of $\gamma C - tL$, which is the top eigenvector of

$$
C + \kappa A, \qquad \kappa = \frac{t}{\gamma},
$$

up to a constant shift. On the prism the total variation distance between the two is 0.02 for $\gamma = 0.2, q = 0.01$, and it grows to 0.18 for $\gamma = 1, q = 0.1$.

2. Now remember what $C$ and $A$ are. For MaxCut, $C$ is an Ising energy and $\kappa A = \kappa \sum_i X_i$ is a transverse field. So the quasispecies is the ground state of a **transverse-field Ising model**,

$$
H = -\Big(C + \kappa \sum_i X_i\Big).
$$

For the continuous-time version of mutation and selection this is an exact equivalence (Baake, Baake and Wagner 1997), and the error threshold turns into the phase transition of the spin chain.

3. Two consequences that I find really interesting:

a) $H$ is **stoquastic**: all its off-diagonal entries are $\le 0$. That is why its ground state is a positive vector and can be a probability distribution at all. The same property lets projector or diffusion Monte Carlo simulate such ground states with walkers that diffuse and branch. Our genetic algorithm with a finite population is exactly such a walker scheme: mutation is the diffusion, selection is the branching.

b) Lowering the mutation rate slowly, while the population follows its quasispecies, traces the same Hamiltonian path as adiabatic quantum optimization, from a strong transverse field down to the bare cost. The genetic algorithm follows this path in imaginary time, by damping. A quantum computer would follow it in real time, by staying in the ground state.

## Finite populations

1. With $N$ strings, selection is a lottery. Good strings can get lost by bad luck, and a small population can collapse onto a single string far too early (premature convergence). The infinite-population picture is what a large population fluctuates around.

2. Physicists use exactly this scheme as **population annealing** (Hukushima and Iba, Machta): resample a population with Boltzmann weights while lowering the temperature, and move every replica with Monte Carlo steps.

## What about crossover?

1. Real genetic algorithms also combine two parents. That makes the dynamics quadratic in $p$, so there is no single matrix and no Perron vector anymore.

2. The Walsh basis still helps. Vose and Wright showed that mutation and crossover simplify in the Walsh basis, and that one generation of the infinite-population algorithm can be computed with fast transforms.

3. Intuitively, crossover recombines good pieces found by different strings (Holland's building blocks) and pushes the population towards product-like distributions. In our picture it is the one ingredient without a clean counterpart on the quantum side.

## So what does this mean for QAOA?

1. QAOA alternates the same two operators in real time. The genetic algorithm damps, QAOA rotates phases. The genetic algorithm converges to a positive fixed point that classical sampling can reach. QAOA keeps amplitudes with phases, and phases can interfere.

2. So if a QAOA circuit only does what a mutation-selection process does, there is no reason to expect an advantage. Whatever QAOA adds has to come from interference, which the genetic algorithm, with only positive weights, cannot produce.

3. And for a fair comparison, this genetic algorithm is the natural baseline QAOA has to beat: same graph, same cost, same two moves.

## Literature

The algorithm and the biology:

- J. H. Holland, *Adaptation in Natural and Artificial Systems* (1975). Where genetic algorithms and building blocks come from.
- M. Eigen, [Selforganization of matter and the evolution of biological macromolecules](https://pubmed.ncbi.nlm.nih.gov/4942363/), Naturwissenschaften 58, 465 (1971). The quasispecies and the error threshold.

The spin-chain picture:

- E. Baake, M. Baake, H. Wagner, [Ising quantum chain is equivalent to a model of biological evolution](https://pub.uni-bielefeld.de/record/2378376), Phys. Rev. Lett. 78, 559 (1997). Mutation and selection as an Ising quantum chain, with exactly solved fitness landscapes.
- S. Bravyi, D. P. DiVincenzo, R. I. Oliveira, B. M. Terhal, [The complexity of stoquastic local Hamiltonian problems](https://arxiv.org/abs/quant-ph/0606140) (2006). Why positive ground states make stoquastic Hamiltonians friendlier to classical simulation.

The Walsh basis and populations:

- M. D. Vose, A. H. Wright, [The Simple Genetic Algorithm and the Walsh Transform: Part I, Theory](https://scholarworks.umt.edu/cs_pubs/7), Evolutionary Computation 6(3) (1998). Mutation and crossover in the Walsh basis.
- R. O'Donnell, [Analysis of Boolean Functions](https://arxiv.org/abs/2105.10386). The noise operator, which is our mutation step.
- J. Machta, [Population annealing with weighted averages](https://arxiv.org/abs/1006.0252), Phys. Rev. E 82, 026704 (2010). Population annealing, introduced by Hukushima and Iba, as a sampler for rough landscapes like spin glasses.

I put the "genetic algorithm equals QAOA in imaginary time" framing together myself from these sources and the last post, so better check it against them before citing.
