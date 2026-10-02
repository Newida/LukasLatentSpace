# QAOA on the Hamming Cube

In this post, I want to understand what QAOA actually does when we stop looking at it as a list of gates.

The short version: QAOA lives on a graph, the Hamming cube, and it keeps switching between two ways of looking at that graph. One way are the bitstrings themselves, the other way are the frequencies of the cube. If you have ever seen the split-step Fourier method for the Schrödinger equation, this is exactly that. But let us build this up slowly.

In a previous post (XanaduSpectralmethodsPaper) we already met the graph Laplacian of the Boolean hypercube. We will need it again here, so if something about $L$ looks unfamiliar, have a look there first.

## The problem

1. As usual, we begin with the problem setup.

<a id="problem-1"></a>

> **Problem 1: MaxCut.**  
> Given a graph $G = (V, E)$ with $n$ vertices, split the vertices into two sides such that as many edges as possible go between the two sides.

We will refer to this as [Problem 1](#problem-1).

2. We write a split as a bitstring $x \in \{0,1\}^n$, where $x_i$ tells us on which side vertex $i$ sits. The number of cut edges is

$$
C(x) = \sum_{(i,j) \in E} [x_i \neq x_j],
$$

and we are looking for $x^* = \arg\max_x C(x)$.

Pretty simple I would say. Unfortunately there are $2^n$ bitstrings, so trying all of them is not an option for large $n$. QAOA is one quantum attempt at this. Let us see what it really does.

## The stage: bitstrings on a cube

1. Let us put the $2^n$ bitstrings on the corners of a cube and connect two corners if they differ in exactly one bit. For $n = 3$ this is the usual cube:

```
        000 -------- 001
       / |          / |
    010 -------- 011  |
     |  |         |   |
     | 100 -------|--101
     | /          | /
    110 -------- 111
```

Walking along the edges, the distance between two corners is their Hamming distance. This graph is called the **Hamming cube** $Q_n$.

2. Now the quantum part. An $n$-qubit basis state $\ket{x}$ is labelled by a bitstring, so the basis states already live on the corners of this cube. Moving along one edge means flipping one bit, and flipping bit $i$ is exactly what the Pauli operator $X_i$ does. So the adjacency matrix of the cube is just a sum of bit flips:

$$
A = X_1 + X_2 + \dots + X_n .
$$

3. If you have seen QAOA before, this should look familiar. It is exactly the operator QAOA calls the **mixer** (usually written $B$). So the mixer is not some arbitrary choice of gates. It is the graph of our search space, written in qubit notation. Everything below follows from taking that seriously.

## Fourier analysis on the cube

Ok, so what is the Fourier transform on this cube? There are two ways to get there. Let us start with the one we already know from the last post.

1. The Laplacian way.

a) On any graph, the graph Laplacian is $L = D - A$, where the diagonal matrix $D$ holds the degrees. We already saw that for every function $f$ on the vertices

$$
f^T L f = \sum_{\{x,y\} \in E} \big(f(x) - f(y)\big)^2 .
$$

So $f^T L f$ measures how much $f$ changes across the edges. An eigenvector of $L$ with a small eigenvalue barely changes across edges, one with a large eigenvalue changes a lot. So the eigenvalue **is** the frequency. On a ring of vertices this gives you exactly the sines and cosines of the usual discrete Fourier transform.

b) The cube is $n$-regular, every corner has $n$ neighbors, so $L = nI - A$. Now we need its eigenvectors. Here is the trick: the cube is a product of $n$ single edges, one edge per bit. The Laplacian of a single edge has two eigenvectors, the constant one $(1, 1)$ with eigenvalue $0$ and the alternating one $(1, -1)$ with eigenvalue $2$. For a product graph, the eigenvectors are products of the eigenvectors of the factors and the eigenvalues add up. So for every bit we choose either constant or alternating, and we get

$$
\chi_s(x) = (-1)^{s \cdot x}, \qquad L\,\chi_s = 2|s|\,\chi_s, \qquad s \in \{0,1\}^n ,
$$

where $s$ marks the bits on which we chose the alternating factor and $|s|$ is its Hamming weight.

c) So the Hamming weight $|s|$ is the frequency. $\chi_{000}$ is constant, the weight-1 functions are square waves along one axis of the cube and $\chi_{111}$ changes sign across every edge. For $n = 3$ (bits written $x_1 x_2 x_3$):

```
 s \ x   000 001 010 011 100 101 110 111    eigenvalue of L
 000      +   +   +   +   +   +   +   +           0
 001      +   -   +   -   +   -   +   -           2
 010      +   +   -   -   +   +   -   -           2
 100      +   +   +   +   -   -   -   -           2
 011      +   -   -   +   +   -   -   +           4
 101      +   -   +   -   -   +   -   +           4
 110      +   +   -   -   -   -   +   +           4
 111      +   -   -   +   -   +   +   -           6
```

<!-- FIG:walsh16 -->

2. The group way.

a) The bitstrings also form a group: we can add them bitwise modulo 2 (XOR). Every group like this has its own Fourier transform, built from its **characters**. For $\mathbb{Z}_2^n$ the characters are exactly the functions $\chi_s$ from above. So both ways arrive at the same functions.

b) The Fourier coefficients of a function $f$ on the cube are then

$$
\hat f(s) = 2^{-n} \sum_{x} f(x)\,\chi_s(x),
$$

which is the Walsh-Hadamard transform. On qubits this is a gate you already know: $H^{\otimes n}$, the Hadamard on every qubit, up to the normalization $2^{-n/2}$.

c) We can also check the eigenvalues bit by bit. Flipping bit $i$ multiplies $\chi_s$ by $(-1)^{s_i}$. The $n - |s|$ bits outside of $s$ contribute $+1$ each and the $|s|$ bits inside contribute $-1$ each:

$$
A\,\chi_s = (n - 2|s|)\,\chi_s, \qquad \text{or in gate language} \qquad H^{\otimes n} A\, H^{\otimes n} = Z_1 + \dots + Z_n .
$$

This is just the familiar $HXH = Z$ on every qubit at once.

3. So which way is the right one? Laplacian or characters?

On the full cube both give the same basis, but they do not carry the same information.

a) The Laplacian only fixes the frequency, not the basis. All $\binom{n}{k}$ frequencies of weight $k$ share the eigenvalue $2k$, so for $n = 4$ the eigenspaces have dimensions 1, 4, 6, 4 and 1. Inside each eigenspace, any orthonormal basis is an equally good Laplacian eigenbasis. The characters are the one basis that diagonalizes every single bit flip $X_i$, not only their sum. That extra structure is what the group gives us, and it is where the fast transform $H^{\otimes n}$ and all the nice closed formulas come from.

b) The Laplacian works where there is no group. Constrained problems, think of independent sets, replace the cube by a graph on the feasible bitstrings (Hadfield et al., see Literature). Such graphs usually have no group structure, so no characters and in general no fast transform. But their Laplacian eigenvectors still give us smooth and rough modes.

c) The standard QAOA mixer only sees the frequency level $|s|$, which is exactly the Laplacian eigenvalue. So for plain QAOA nothing is lost. Mixers with a separate angle per qubit, as in multi-angle QAOA, act on single $X_i$'s and need the characters.

So I would say: the Laplacian is the more general idea and the characters are its sharpest special case. On the cube we use the characters, because they are explicit and fast. Off the cube only the Laplacian survives.

4. One more thing before we go on: cost functions like MaxCut have very sparse spectra. Write $e_i$ for the bitstring with a single 1 at position $i$. Edge $(i,j)$ is cut when $x_i \neq x_j$, which is $\big(1 - \chi_{e_i \oplus e_j}(x)\big)/2$. Summing over the edges:

$$
C(x) = \frac{|E|}{2} - \frac{1}{2} \sum_{(i,j) \in E} \chi_{e_i \oplus e_j}(x) .
$$

So MaxCut only has Fourier weight at frequency 0 and at weight-2 frequencies, one per edge. This sparsity is the reason why QAOA's operators are local and can be implemented as short circuits.

## Classical diffusion: heat flow on the cube

1. Let us start with something classical. A walker sits on a corner and each of its bits flips independently at rate 1. Its probability distribution $p_t$ follows the heat equation on the cube:

$$
\frac{dp}{dt} = -L\,p .
$$

2. In the Fourier basis this is trivial. Every mode just decays with its own eigenvalue:

$$
\hat p_t(s) = e^{-2|s| t}\,\hat p_0(s).
$$

High frequencies die first, and for $t \to \infty$ only the constant mode survives: the uniform distribution.

3. In position space the same thing factorizes over the bits. After time $t$ every bit has flipped with probability

$$
q_t = \frac{1 - e^{-2t}}{2},
$$

independently of the others. This is the noise operator from Boolean Fourier analysis and, if you squint a little, the mutation step of a genetic algorithm.

## Quantum diffusion: the mixer

1. Now we replace the heat equation by the Schrödinger equation on the same graph:

$$
i\,\frac{d\psi}{d\beta} = A\,\psi, \qquad \psi_\beta = e^{-i\beta A}\,\psi_0 .
$$

This is the QAOA mixer, a continuous-time quantum walk on the cube. In the Fourier basis:

$$
\hat\psi_\beta(s) = e^{-i\beta(n - 2|s|)}\,\hat\psi_0(s).
$$

2. Nothing decays! Every mode keeps its magnitude and only rotates its phase, with a speed set by its frequency. Classical diffusion forgets where it started by damping the fine structure. The quantum walk keeps all of it and turns it into phase.

3. In position space it again factorizes, now over amplitudes. On each qubit $e^{-i\beta X} = \cos\beta\,I - i\sin\beta\,X$, so starting from $\ket{x}$ the amplitude of a corner at Hamming distance $k$ is

$$
(\cos\beta)^{n-k}\,(-i\sin\beta)^{k} .
$$

a) If we measure right away, this looks like classical bit flipping with probability $\sin^2\beta$. The difference is the phase $(-i)^k$, which lets amplitudes from different paths interfere as soon as something else acts on the state.

b) Two values of $\beta$ are fun to look at. At $\beta = \pi/2$ every bit flips with certainty and the walk lands exactly on the opposite corner. The classical walk never puts more than $2^{-n}$ probability there. At $\beta = \pi/4$ every bit flips with probability exactly $1/2$, so the measured distribution is exactly uniform, while the classical walk only gets there for $t \to \infty$ (Moore and Russell, see Literature). For $n = 3$, starting at $000$:

```
                      P(start corner)   P(opposite corner)
 quantum, beta = pi/4      0.125             0.125
 quantum, beta = pi/2      0                 1
 classical, any t          > 0.125           < 0.125
```

<!-- TOY:cube -->

## The cost layer is a potential

1. The other QAOA ingredient is $e^{-i\gamma C}$. It is diagonal in position space: it multiplies the amplitude of corner $x$ by $e^{-i\gamma C(x)}$. In Schrödinger language, $C$ is a potential and the mixer is the kinetic term.

2. On its own, the cost layer changes no probabilities. Its effect happens in frequency space. QAOA starts in $\ket{+}^{\otimes n}$, the uniform superposition, which is the single Fourier mode $s = 0$. Multiplying by the phase pattern $e^{-i\gamma C(x)}$ spreads weight onto other frequencies. The mixer then rotates these modes with different speeds, and when we go back to positions, the phase differences have turned into amplitude differences. Good angles make them add up on corners with high $C$.

3. A second Laplacian: the problem graph.

a) The cube is not the only graph around. MaxCut is defined on the problem graph $G$ with $n$ vertices, and $G$ has its own Laplacian $L_G$. Let us write the two sides of a cut as signs $z_i = (-1)^{x_i}$. Every edge contributes $(z_i - z_j)^2/4$, which is $1$ if the edge is cut and $0$ otherwise. So

$$
C(x) = \frac{1}{4}\, z^T L_G\, z, \qquad \text{and as an operator} \qquad C = \frac{1}{4} \sum_{i,j} (L_G)_{ij}\, Z_i Z_j .
$$

b) So MaxCut asks for the sign pattern that oscillates the most on $G$: the highest-frequency $\pm 1$ signal in the problem graph's own Fourier picture. This also connects back to the cube: the weight-2 Walsh coefficients of $C$ sit exactly on the edges of $G$, so the cube spectrum of the cost is a copy of the problem graph.

c) If we relax the signs to any real vector of the same length, we get the bound

$$
C_{\max} \le \frac{n\,\lambda_{\max}(L_G)}{4}
$$

(Mohar and Poljak). Rounding a top eigenvector to its signs is the classical spectral heuristic, and Goemans-Williamson relaxes the same quadratic form even further, from numbers to vectors.

d) Example: the triangular prism, two triangles connected by three rungs, 9 edges. We will meet it again below. It is itself a product graph, a triangle times an edge, so its Laplacian eigenvalues are sums: 0 or 3 from the triangle plus 0 or 2 from the edge, which gives 0, 2, 3, 3, 5, 5. The bound is $6 \cdot 5/4 = 7.5$ and the true maximum cut is 7. The top eigenvalue 5 has a two-dimensional eigenspace. The vector with entries $2, -1, -1$ on vertices 1 to 3 and $-2, 1, 1$ on vertices 4 to 6 rounds to a maximum cut:

```
 vertex             1    2    3    4    5    6
 eigenvector        2   -1   -1   -2    1    1
 side               +    -    -    -    +    +

 cut edges: 1-2, 1-3, 4-5, 4-6, 1-4, 2-5, 3-6   (7 of 9)
```

<!-- FIG:prism -->

e) Other vectors in the same eigenspace contain zeros and round ambiguously. That is the same degeneracy we saw on the cube, where the characters had to pick a basis for us.

4. So QAOA alternates between two Laplacians. The mixer is generated by the Laplacian of the cube, a graph on $2^n$ corners, and plays the kinetic term. The cost is the quadratic form of the problem graph's Laplacian, a graph on $n$ vertices, and plays the potential.

## QAOA is a split-step Fourier method

1. The depth-$p$ QAOA state is

$$
\ket{\gamma, \beta} = e^{-i\beta_p A}\, e^{-i\gamma_p C} \cdots e^{-i\beta_1 A}\, e^{-i\gamma_1 C}\, \ket{+}^{\otimes n} .
$$

2. Now write every mixer as $e^{-i\beta A} = H^{\otimes n}\, e^{-i\beta \sum_i Z_i}\, H^{\otimes n}$. Then every layer consists of four steps, and each step is just a multiplication in the right basis:

```
   positions x                                 frequencies s
       |                                             |
  1.   |  phase kick  exp(-i gamma C(x))             |
  2.   | ------------- H on every qubit ------------> |
  3.   |                 phase rotation  exp(-i beta (n - 2|s|))
  4.   | <------------ H on every qubit ------------- |
       |                                             |
     repeat p times
```

3. This is exactly the split-operator method for solving $i\,\partial_t \psi = (T + V)\,\psi$ numerically: FFT to momentum space, apply the kinetic phase, FFT back, apply the potential phase. On the cube, the Walsh-Hadamard transform plays the FFT, the cube Laplacian plays $-\nabla^2$ and the cost plays the potential.

4. Some consequences follow directly:

a) With many layers and small angles, QAOA is a Trotter discretization of continuous evolution under $a(t)\,A + b(t)\,C$. Adiabatic optimization and quantum-walk search are just special schedules of this one equation.

b) A classical simulation costs $O(p\,n\,2^n)$ with the fast Walsh-Hadamard transform.

c) At depth 1 the mixer cannot change Fourier magnitudes, only phases. Whatever frequency content the cost layer creates is all the mixer has to work with.

d) The recipe only needs a mixer that walks on some graph: transform with that graph's Laplacian eigenvectors, apply the kinetic phase, transform back. On the full cube that transform is the fast Walsh-Hadamard transform. Constrained mixers keep the split-step structure, but in general lose the fast transform.

## Depth 1 on a six-vertex prism

1. Let us try all of this on the triangular prism from above: 9 edges and $2^6 = 64$ cuts. Each triangle can cut at most two of its three edges, so the maximum cut is 7. A uniformly random cut gets 4.5 on average.

2. At depth 1 we only have two angles, so we can simply scan the whole landscape $\langle C \rangle(\gamma, \beta)$ with $\gamma \in [0, \pi]$ and $\beta \in [0, \pi/2]$. I did this with the split-step simulation from above:

```
 best angles               gamma = 0.571 (0.182 pi),  beta = 0.349 (0.111 pi)
 expected cut <C>          5.94     (random: 4.50, maximum: 7)
 approximation ratio       0.85
 P(maximum cut)            0.40     (6 of the 64 strings are maximum cuts)
 most likely string        101010, a maximum cut

 Walsh weight by |s|       |s| = 0: 0.495   2: 0.409   4: 0.091   6: 0.005
```

3. Interesting detail: only even frequencies show up. MaxCut does not change if we flip all bits, so the odd frequencies never get any weight.

<!-- TOY:prism -->

## Rotate time and you get a genetic algorithm

1. Ok, one last thing that I find really cute. Replace each unitary by its imaginary-time version. The mixer $e^{-i\beta A}$ becomes the heat kernel $e^{-tL}$, which is independent bit-flip mutation. The cost layer $e^{-i\gamma C}$ becomes $e^{\gamma C}$ followed by normalization, which is Boltzmann selection: corners with higher $C$ get exponentially more weight. Alternating the two is a mutation-selection process, the population version of a genetic algorithm, or population annealing.

2. Since $e^{-tL} = e^{-nt}\, e^{tA}$, this alternation is a Trotterization of $e^{\tau (C + \kappa A)}$. Repeated, it converges to the top eigenvector of $C + \kappa A$, a positive vector that concentrates on the maximizers of $C$ for $\kappa \to 0$. The classical cousin works by damping: unwanted modes shrink and disappear.

3. QAOA is the real-time version of the same alternation. It cannot damp anything, because every step is unitary. It can only steer phases so that amplitudes interfere constructively on good corners. That is why its angles have to be tuned, why its landscape oscillates the way it does, and why an advantage over the classical cousin is something we have to show problem by problem instead of just assuming it.

## The dictionary

| Object | Positions (bitstrings $x$) | Frequencies (Walsh modes $s$) |
|---|---|---|
| Cube adjacency $A = \sum_i X_i$ | sum over single-bit flips | multiplication by $n - 2\lvert s\rvert$ |
| Cube Laplacian $L = nI - A$ | $n$ times the amplitude minus the sum over single-bit flips | multiplication by $2\lvert s\rvert$ (fixes the level, the characters fix the basis) |
| MaxCut cost $C$ | multiplication by $C(x)$ | sparse: weight 0 and one weight-2 mode per edge |
| Problem-graph Laplacian $L_G$ | $C(x) = \tfrac{1}{4} z^T L_G z$ with $z_i = (-1)^{x_i}$ | off-diagonal entries are the weight-2 coefficients of $C$, up to a factor |
| Constrained mixer | hops along the allowed moves of a graph on feasible strings | diagonal in that graph's Laplacian eigenbasis, no characters |
| Heat flow $e^{-tL}$ | every bit flips with probability $(1 - e^{-2t})/2$ | mode $s$ decays by $e^{-2\lvert s\rvert t}$ |
| Mixer $e^{-i\beta A}$ | $\cos\beta$ to stay, $-i\sin\beta$ to flip, per bit | mode $s$ rotates by $e^{-i\beta(n - 2\lvert s\rvert)}$ |
| Cost layer $e^{-i\gamma C}$ | phase kick $e^{-i\gamma C(x)}$ | spreads weight according to the spectrum of the phase pattern |
| Initial state $\ket{+}^{\otimes n}$ | uniform over all corners | the single mode $s = 0$ |
| One QAOA layer | phase in positions, transform | phase in frequencies, transform back |

## Literature

The algorithm:

- E. Farhi, J. Goldstone, S. Gutmann, [A Quantum Approximate Optimization Algorithm](https://arxiv.org/abs/1411.4028) (2014). The original paper, with the transverse-field mixer and the alternating ansatz.
- S. Hadfield et al., [From the QAOA to a Quantum Alternating Operator Ansatz](https://arxiv.org/abs/1709.03489) (2017). Other mixers for constrained problems, where the cube is replaced by other graphs on the feasible set.
- R. Herrman et al., [Multi-angle quantum approximate optimization algorithm](https://www.nature.com/articles/s41598-022-10555-8) (2022). A separate mixer angle per qubit, the case where we need the characters and not just the Laplacian levels.

Fourier analysis on the cube and on graphs:

- R. O'Donnell, [Analysis of Boolean Functions](https://arxiv.org/abs/2105.10386). Walsh characters, the noise operator (our heat flow with $\rho = e^{-2t}$) and low-degree spectra.
- D. I. Shuman, S. K. Narang, P. Frossard, A. Ortega, P. Vandergheynst, [The Emerging Field of Signal Processing on Graphs](https://arxiv.org/abs/1211.0053) (2013). The graph Fourier transform as the Laplacian eigenbasis, with eigenvalues as frequencies.
- B. Mohar, S. Poljak, [Eigenvalues and the max-cut problem](https://eudml.org/doc/13856) (1990). The bound $C_{\max} \le n\,\lambda_{\max}(L_G)/4$.
- M. X. Goemans, D. P. Williamson, [Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming](https://doi.org/10.1145/227683.227684) (1995). The same Laplacian quadratic form, relaxed from signs to unit vectors.

The mixer as a quantum walk:

- C. Moore, A. Russell, [Quantum Walks on the Hypercube](https://arxiv.org/abs/quant-ph/0104137) (2001). The continuous-time walk is exactly uniform at a specific time, in our units $\beta = \pi/4$.
- J. Kempe, [Quantum random walks: an introductory overview](https://arxiv.org/abs/quant-ph/0303081) (2003), and [Mixing Times in Quantum Walks on the Hypercube](https://arxiv.org/abs/0712.0625).
- [Mixing of Quantum Walks on Generalized Hypercubes](https://arxiv.org/abs/0808.2382) (2008). The same Fourier argument on group-circulant graphs.

QAOA as phase kicks and quantum walks:

- S. Marsh, J. B. Wang, [Combinatorial optimisation via highly efficient quantum walks](https://arxiv.org/abs/1912.07353) (2019). Quality-dependent phase shifts alternated with walks on circulant graphs, the direct generalization of the split-step picture.
- [Analysis of the Non-variational Quantum Walk-based Optimisation Algorithm](https://arxiv.org/abs/2408.06368) (2024).
- [Depth scaling of unstructured search via quantum approximate optimization](https://arxiv.org/abs/2403.15540) (2024). QAOA sequences from Trotterizing a continuous-time quantum walk.
- [Guided quantum walk](https://arxiv.org/abs/2308.05418) (2023). Steering the hypercube walk with the spectrum of the problem Hamiltonian instead of variational angles.

Landscapes:

- L. Zhou, S.-T. Wang, S. Choi, H. Pichler, M. D. Lukin, [QAOA: Performance, Mechanism, and Implementation on Near-Term Devices](https://arxiv.org/abs/1812.01041) (2018). Careful: their "FOURIER" heuristic is a Fourier series over the layer index of the angles, a different Fourier transform than the one on the cube.
- [Connecting the Hamiltonian structure to the QAOA energy and Fourier landscape structure](https://arxiv.org/abs/2305.13594) (2023). The landscape as a Fourier series in the angles, which explains its periodicity.

I could not find a single reference that presents QAOA explicitly as a split-step Fourier method on the cube, or the imaginary-time mutation-selection picture, or the two-Laplacian reading. I put these together from the standard facts above, so better check them against the sources before citing.
