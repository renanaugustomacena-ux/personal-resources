# 200 — Stochastic Calculus and Continuous-Time Finance

> Foundational reference for continuous-time trading. Covers probability theory, Brownian motion, Ito calculus, change of measure, jump processes, stochastic volatility, numerical methods, and applied option pricing. Self-contained — assumes only multivariable calculus, linear algebra, and a working knowledge of Python.

---

## Table of Contents

1. [Why Continuous Time](#why-continuous-time)
2. [Measure-Theoretic Probability — A Working Toolkit](#part-i-measure-theoretic-probability-—-a-working-toolkit)
3. [Random Variables, Expectation, and Distributions](#random-variables-expectation-and-distributions)
4. [Conditional Expectation and Filtrations](#conditional-expectation-and-filtrations)
5. [Discrete-Time Martingales](#discrete-time-martingales)
6. [Stopping Times and Optional Stopping](#stopping-times-and-optional-stopping)
7. [Brownian Motion — Construction and Properties](#part-ii-brownian-motion)
8. [Quadratic Variation and Path Roughness](#quadratic-variation-and-path-roughness)
9. [The Brownian Bridge, Reflection Principle, and Hitting Times](#brownian-bridge-reflection-and-hitting-times)
10. [The Ito Integral](#part-iii-the-ito-integral)
11. [Ito's Lemma — One Dimension](#itos-lemma-one-dimension)
12. [Multidimensional Ito Formula and Quadratic Covariation](#multidimensional-ito-formula)
13. [Stochastic Differential Equations — Existence and Uniqueness](#part-iv-stochastic-differential-equations)
14. [Closed-Form SDE Solutions](#closed-form-sde-solutions)
15. [Linear SDEs, Geometric Brownian Motion, and Ornstein–Uhlenbeck](#linear-sdes)
16. [Change of Measure and the Girsanov Theorem](#part-v-change-of-measure)
17. [Risk-Neutral Pricing and Fundamental Theorems](#risk-neutral-pricing)
18. [Forward Measure and Numeraire Change](#forward-measure)
19. [Jumps, Poisson Processes, and Lévy Processes](#part-vi-jump-processes)
20. [Jump-Diffusion Models — Merton, Kou, Bates](#jump-diffusion-models)
21. [Stochastic Volatility — Heston, SABR, Rough Bergomi](#part-vii-stochastic-volatility)
22. [Numerical SDE Schemes — Euler, Milstein, Weak/Strong Convergence](#part-viii-numerical-methods)
23. [Variance Reduction and Multilevel Monte Carlo](#variance-reduction-and-multilevel-monte-carlo)
24. [Pricing European, American, and Path-Dependent Options](#pricing-options)
25. [Greeks — Pathwise, Likelihood, and Malliavin Methods](#greeks)
26. [Calibration to Market Data — Theory and Code](#calibration)
27. [Real Trading Considerations — From Theory to Live PnL](#trading-considerations)
28. [Reference Tables, Cheat Sheets, and Annotated Bibliography](#reference)

---

## Why Continuous Time

Most retail traders never leave discrete time. They look at one-minute bars, fifteen-minute bars, or daily candles, and they reason about the world through differences between consecutive observations. That mental model has a hard ceiling. The moment you ask serious questions — *what is the fair price of an option two minutes before expiration?*, *how do I hedge a position whose risk depends on the path the price takes, not just its endpoint?*, *what is the value of optionality in a market where information arrives faster than I can rebalance?* — discrete arithmetic stops being enough.

Continuous-time finance is not a theoretical luxury. It is the language in which the bulk of modern risk, derivatives, execution, and high-frequency literature is written. Without it you cannot read Black–Scholes, Heston, SABR, Almgren–Chriss, Avellaneda–Stoikov, Carmona–Touzi, or any of the modern rough-volatility papers. You also cannot evaluate the assumptions those papers make. The point of this document is to make that machinery operational — readable, codable, and audit-able by a working trader who already understands the discrete world but wants to graduate to the continuous one.

We will move slowly through the foundational measure-theoretic probability — not because it is cosmetically rigorous, but because every later result we use depends on the precise meaning of *expected value*, *information set*, *martingale*, and *measure*. We will then construct Brownian motion, develop the Ito integral, derive Ito's lemma, solve the canonical stochastic differential equations (geometric Brownian motion, Ornstein–Uhlenbeck, Cox–Ingersoll–Ross), and get to the Girsanov theorem — the single most important change-of-perspective in derivative pricing. From there, jump processes, stochastic volatility, and numerical methods all unfold naturally.

Wherever we make a mathematical claim that has a tradable consequence, the consequence is stated. Wherever there is code, the code is in Python, runnable as-is on a laptop, with no proprietary dependencies. Wherever there is a formula that traders use daily — Black–Scholes, Heston, SABR, the Greeks — the derivation is given in full, not skipped behind a citation.

A note on philosophy. Continuous-time models are *idealizations*. The market is not actually continuous. Prices arrive in discrete ticks. Order books are integer-priced. Time stamps are noisy. Yet the continuous model captures, with stunning accuracy, the limiting behavior of an aggregated market in the regime where many small participants act on uncorrelated information. The art of applied quant work is knowing when this limit is a faithful approximation and when it lies. This document is biased toward the truth of the model — but every chapter ends with a *reality check* section that calls out the empirical departures and how live traders patch them.

---

## Part I — Measure-Theoretic Probability: A Working Toolkit

Probability theory written without measure theory is like trading without a P&L statement: you can do it, but you will not know what you have done. The continuous-time machinery requires us to be precise about three things — what events we can talk about, how we assign a number to each event, and how we relate events to information. Measure theory gives us that vocabulary in three objects: a **set** of outcomes Ω, a **σ-algebra** of events ℱ, and a **probability measure** ℙ. The triple (Ω, ℱ, ℙ) is called a *probability space*.

### Sets, σ-Algebras, and Why We Need Them

The sample space Ω is the set of every conceivable outcome of the experiment we are modeling. For a single coin flip, Ω = {H, T}. For the path of a stock price over a one-year horizon, Ω is the (uncountably infinite) set of all real-valued continuous functions on [0, 1]. Already we are out of the comfort zone of high-school probability. We cannot list the outcomes; there are too many. We must instead reason about *collections* of outcomes — events.

The collection of events we care about must be closed under three operations: complementation (if I can talk about the event "the stock ends above 100", I can talk about its complement "it does not end above 100"), countable union ("ends above 100 or above 110 or above 120 or…"), and countable intersection ("stays above 100 every day"). A non-empty family ℱ of subsets of Ω that is closed under these operations is called a **σ-algebra**. The pair (Ω, ℱ) is a **measurable space**.

The smallest σ-algebra containing the open intervals of ℝ is called the **Borel σ-algebra**, denoted 𝓑(ℝ). Almost every interesting subset of ℝ that you encounter in practice — open sets, closed sets, half-lines, countable sets, finite intersections of intervals — is Borel. The Borel σ-algebra exists because we want to be able to ask probabilistic questions about *real-valued* random outcomes; it is the natural domain on which to define their distributions.

Why not just take ℱ = 𝒫(Ω), the power set of Ω? Two reasons. First, in uncountable Ω, there exist subsets to which one cannot consistently assign a probability satisfying countable additivity (the Vitali set is the canonical pathological example). Second, even when one *could* assign probabilities, one usually does not want to. The σ-algebra encodes *which questions one is allowed to ask*. Different σ-algebras encode different states of information — a key idea when we get to filtrations.

A **probability measure** ℙ : ℱ → [0, 1] is a function that assigns a number between 0 and 1 to every event in ℱ, with ℙ(Ω) = 1 and ℙ(∪ Aₙ) = ∑ ℙ(Aₙ) for any countable family of pairwise disjoint events. The latter property is **σ-additivity** — the linchpin of the whole theory. From σ-additivity flow continuity from below, continuity from above, the Borel–Cantelli lemmas, and the dominated convergence theorem, all of which we will use repeatedly.

```python
# A tiny, deliberately-small sanity-check on a finite probability space.
# Useful as a teaching device: every claim about measures collapses to summing fractions.
import numpy as np

omega = ['HH', 'HT', 'TH', 'TT']
P = {w: 0.25 for w in omega}                     # uniform on a fair two-coin experiment

def measure(event):
    return sum(P[w] for w in event)

A = {'HH', 'HT'}                                  # first coin is H
B = {'HH', 'TH'}                                  # second coin is H
assert np.isclose(measure(A), 0.5)
assert np.isclose(measure(A & B), 0.25)
assert np.isclose(measure(A | B), measure(A) + measure(B) - measure(A & B))
```

### Why Measure Theory Saves You from Lying to Yourself

Most of the financial bugs that survive code review and creep into production are *measure-theoretic* bugs in disguise. The classic ones:

- *Confusing the physical and risk-neutral measures.* Under the physical measure ℙ, the expected return of a stock is whatever the market actually delivers (call it µ). Under the risk-neutral measure ℚ, it is the risk-free rate r. If you simulate paths under ℙ but discount them as if they were under ℚ, you are not computing the price of an option; you are computing a function of µ, r, and σ that has no agreed-upon name.
- *Conditioning on the future.* When you replay history with hindsight — for example, scaling every observation by the realized volatility of the *full* sample — your random variables are no longer ℱ_t-measurable; they are ℱ_T-measurable. The discrepancy between the two is the source of essentially every "the backtest looks great but live trading is dead" disaster.
- *Sub-σ-algebra leakage.* Strategies that "shouldn't" know future returns sometimes do, because a feature aggregates over a centered window or because survivorship has trimmed the universe. Fixing this means writing your code as if you did not know the future — and verifying it by literally only making ℱ_t observable on date t.

Measure theory does not make these errors disappear, but it gives you the vocabulary to *see* them. The rest of this section operationalizes that vocabulary.

### Lebesgue Measure and Why We Use It

The Lebesgue measure λ on (ℝ, 𝓑(ℝ)) is the unique countably-additive measure such that λ([a, b]) = b − a for every closed interval. It coincides with our intuitive notion of length, area, and volume in higher dimensions. The reason we care: it lets us *integrate*. The Lebesgue integral, unlike the Riemann integral, behaves well under limits — convergence theorems exist (monotone, dominated, Fatou) that fail for Riemann integration, and these convergence theorems are what allow us to define the Ito integral as a limit of simple processes.

A measurable function f : ℝ → ℝ is **integrable** with respect to Lebesgue measure if ∫ |f| dλ < ∞. The Lebesgue integral of f over a Borel set A is written ∫_A f dλ or, when there is no ambiguity, ∫_A f(x) dx. The class of Lebesgue-integrable functions is denoted L¹. The class of square-integrable functions — those with ∫ f² dλ < ∞ — is denoted L². Almost all results in continuous-time finance live in L² because the Ito isometry gives us a Hilbert-space structure there.

For a probability measure ℙ, we replace integration over ℝ with integration over the sample space Ω. The expectation of a random variable X is

$$
\mathbb{E}[X] = \int_\Omega X \, d\mathbb{P}.
$$

This is the same object you have always called "the average of X weighted by its probability." The measure-theoretic notation makes precise what the average means even when X has a continuous distribution: it is the Lebesgue integral of X against ℙ. When X has a density f_X with respect to Lebesgue measure, the change-of-variable formula recovers the familiar ∫ x f_X(x) dx.

### Dominated Convergence and Why It Matters

The single most useful theorem in this whole section is the **dominated convergence theorem**: if {Xₙ} is a sequence of random variables that converges almost surely to X, and if there exists an integrable random variable Y such that |Xₙ| ≤ Y almost surely for every n, then 𝔼[Xₙ] → 𝔼[X]. In words: when a sequence of random variables is uniformly bounded by something with finite mean, you can swap the limit and the expectation.

This is what licenses the central computation of Ito calculus. We approximate a stochastic integral ∫ f(s, ω) dWₛ by a sequence of *simple* integrals (sums over finitely many time points), prove that the simple integrals converge in L², and use dominated convergence to get the expectation right. Every theorem you will see attributed to Itô, Tanaka, or Doob ultimately rests on this swap.

### Almost Sure, In Probability, In L^p

Three modes of convergence appear over and over:

- **Almost sure**: ℙ(Xₙ → X) = 1. Every realization eventually falls within ε of the limit.
- **In probability**: ℙ(|Xₙ − X| > ε) → 0 for every ε > 0.
- **In L^p**: 𝔼[|Xₙ − X|^p] → 0.

Almost sure convergence implies convergence in probability. Convergence in L^p implies convergence in probability. Almost-sure and L^p convergence are *not* directly comparable — neither implies the other. But on a finite probability space, they all coincide, which is one reason the toy examples in textbooks can mislead.

In trading, you mostly care about L² convergence (because variance is finite and you have a Hilbert space) and almost-sure convergence (because every actual path is real, not an average). When a paper says "the strategy converges to the optimal allocation almost surely," they mean: whatever path the world takes, you will end up at the right answer with probability one. When they say "in L²", they mean: the *mean squared error* shrinks to zero — but on any given realization you might still be far away.

```python
# Demonstration: convergence in probability but not almost surely.
# Classic typewriter sequence: a sequence of indicators of intervals that shrink
# to zero in probability but visit every point infinitely often.
import numpy as np

def typewriter(n):
    # Returns the index k and segment for the n-th typewriter event.
    k = int(np.floor(np.log2(n + 1)))
    j = (n + 1) - 2**k
    return k, j

def X_n(omega, n):
    k, j = typewriter(n)
    seg = (j / 2**k, (j + 1) / 2**k)
    return 1.0 if seg[0] <= omega < seg[1] else 0.0

omegas = np.random.uniform(size=100)
for omega in omegas[:3]:
    visits = sum(X_n(omega, n) for n in range(1, 64))
    # X_n(omega, .) is 1 infinitely often -> not almost-sure convergence.
    # But P(X_n = 1) = 1/2^k -> 0, so X_n -> 0 in probability.
    print(f"omega={omega:.3f}, visits in first 64 steps = {visits}")
```

### Independence

Two events A, B ∈ ℱ are **independent** under ℙ if ℙ(A ∩ B) = ℙ(A) ℙ(B). Two random variables X, Y are independent if their joint distribution factorizes — equivalently, if 𝔼[f(X) g(Y)] = 𝔼[f(X)] 𝔼[g(Y)] for all bounded measurable f, g. Independence is a property of the *measure* on the joint space; the same random variables can be dependent under one measure and independent under another. (This is the source of the most subtle change-of-measure pitfalls in pricing.)

A family of σ-algebras {𝒢_α} is independent if every finite sub-collection of events drawn from distinct 𝒢_α is jointly independent. We will use this when we say "the increments of a Brownian motion are independent": each increment generates its own σ-algebra, and these σ-algebras are mutually independent.

### Pi-Lambda and Monotone Class Theorems

Two technical theorems show up repeatedly when we want to verify that two measures, or two distributions, agree everywhere by checking that they agree on a small generating class.

**π–λ theorem** (Dynkin): if 𝒫 is a π-system (closed under finite intersection) and 𝓛 is a λ-system (closed under complements and countable disjoint unions) containing 𝒫, then 𝓛 contains the σ-algebra generated by 𝒫.

**Monotone class theorem**: if 𝒞 is a class of bounded measurable functions closed under monotone limits and containing the indicators of an algebra 𝒜, then 𝒞 contains all bounded σ(𝒜)-measurable functions.

In practice these theorems let us prove a property "for all events" by proving it on intervals (a π-system generating 𝓑(ℝ)) and lifting. Almost every uniqueness statement in measure theory boils down to one of these two theorems.

### Reality Check — When the Probability Space Is a Lie

In trading, we never see Ω. We see a finite sample of one path. Every probabilistic statement we make is therefore a *bet* on the structure of the unseen rest of Ω, calibrated from the part we have already observed. The risk is that the path-generating mechanism is non-stationary — that the measure ℙ governing tomorrow is different from the measure that governed last year. The standard machinery of measure theory has nothing to say about this. The practitioner's response is to build models in which non-stationarity is *part of the state* (regime-switching, structural breaks, time-varying volatility) rather than a violation of the model. We will see this pattern repeatedly: every time the math forces us to commit to a measure, we ask "is this measure constant in time, or am I lying to myself?"

---

## Random Variables, Expectation, and Distributions

A **random variable** X on (Ω, ℱ, ℙ) is a measurable function X : Ω → ℝ — meaning that the preimage of every Borel set B ⊆ ℝ is an event in ℱ. Equivalently, the σ-algebra σ(X) generated by X — the smallest σ-algebra making X measurable — is contained in ℱ.

The **distribution** of X is the pushforward measure μ_X = ℙ ∘ X⁻¹ on (ℝ, 𝓑(ℝ)): for every Borel B, μ_X(B) = ℙ(X ∈ B). The distribution is enough to compute every probability statement about X *that does not depend on its joint structure with other variables*. To compute joint probabilities — for example ℙ(X > x, Y > y) — we need the joint distribution μ_(X, Y) on ℝ², which is the pushforward of ℙ under (X, Y) : Ω → ℝ².

When X has a density f_X with respect to Lebesgue measure, μ_X(B) = ∫_B f_X dλ. Most named distributions you know — Gaussian, exponential, gamma, beta — are absolutely continuous with respect to Lebesgue and thus have densities. Discrete distributions — Bernoulli, Poisson, binomial — are absolutely continuous with respect to *counting* measure on ℕ, which gives them probability mass functions. Some financially relevant distributions (e.g., a stock price with a possible jump to zero) are mixtures of continuous and discrete parts and require both.

### Moments and the Moment-Generating Function

The k-th moment of X is 𝔼[X^k] = ∫ x^k μ_X(dx). The central moments — 𝔼[(X − 𝔼[X])^k] — are the moments after centering. Variance is the second central moment; skewness is the third; excess kurtosis is the fourth minus three.

The **moment-generating function** (MGF) is M_X(t) = 𝔼[e^{tX}], defined wherever the expectation is finite. The MGF, when it exists in an open neighborhood of zero, uniquely determines the distribution. Its k-th derivative at zero is the k-th moment. The MGF of a sum of independent variables is the product of their MGFs — the workhorse identity for proving central limit theorems.

The **characteristic function** φ_X(t) = 𝔼[e^{itX}] always exists (the integrand is bounded by 1) and uniquely determines the distribution. It is the Fourier transform of the density when one exists. Characteristic functions are the right tool for jump processes (where MGFs may not exist) and for computing densities by Fourier inversion — Carr–Madan, Lewis, and the COS method are all built on this.

```python
# Compute and plot the characteristic function of a Gaussian.
import numpy as np
import matplotlib.pyplot as plt

mu, sigma = 0.0, 1.0
t = np.linspace(-5, 5, 400)
phi = np.exp(1j * mu * t - 0.5 * sigma**2 * t**2)

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(t, phi.real); ax[0].set_title("Re φ_X(t) — Gaussian")
ax[1].plot(t, phi.imag); ax[1].set_title("Im φ_X(t) — Gaussian")
for a in ax: a.grid(True)
plt.tight_layout(); plt.savefig("gaussian_cf.png", dpi=120)
```

### Convergence in Distribution

A sequence Xₙ converges in distribution to X if μ_{Xₙ}(B) → μ_X(B) for every continuity set B (i.e., a Borel set with μ_X(∂B) = 0). Equivalently, by Lévy's continuity theorem, φ_{Xₙ}(t) → φ_X(t) pointwise. Convergence in distribution is the weakest of the four modes; almost-sure, in-probability, and L² convergence all imply it but the converse fails.

The **central limit theorem** (CLT) says that if X₁, X₂, … are iid with finite variance σ² and mean µ, then √n (X̄ₙ − µ) ⇒ 𝒩(0, σ²) in distribution. This is the workhorse that justifies most standard statistical tests, but in finance it is also the source of constant pain: returns are *not* iid, the convergence rate (Berry–Esseen O(1/√n)) is slow when distributions are skewed, and the CLT tells you nothing about the tails. The latter point is why every serious risk model treats the tail separately.

The **Lindeberg–Feller CLT** generalizes to non-iid sequences by requiring a uniform smallness condition on the contributions of individual summands. This is what we use to justify normality of returns aggregated over many small shocks, even when the shocks are heterogeneous.

### Joint Distributions, Correlation, and Copulas

The joint distribution of (X, Y) is more than the marginals. Correlation captures only the linear dependence; nonlinear dependence requires more — often expressed via the **copula** C, the joint distribution of the rank-transformed variables. Sklar's theorem says that for any joint distribution F_{XY} with marginals F_X, F_Y, there exists a copula C such that F_{XY}(x, y) = C(F_X(x), F_Y(y)). Copulas isolate the dependence structure from the marginals — useful when you want to fit, say, a t-distribution marginal and a Clayton copula dependence (heavier downside than upside dependence). Document 207 in this collection covers copulas in depth.

In the continuous-time world, dependence between processes is most often expressed via the correlation matrix of their driving Brownian motions. Two correlated Brownian motions W^1, W^2 with correlation ρ have d⟨W^1, W^2⟩ = ρ dt; we will see the consequences when we develop the multidimensional Ito formula.

### Common Distributions Worth Memorizing

| Distribution | Density / mass | Mean | Variance | Skew | Kurt (excess) | Notes |
|---|---|---|---|---|---|---|
| Gaussian 𝒩(µ, σ²) | (2πσ²)⁻¹ᐟ² exp(−(x−µ)²/(2σ²)) | µ | σ² | 0 | 0 | The default; CLT limit |
| Student-t (ν) | proportional to (1 + x²/ν)^{−(ν+1)/2} | 0 (ν > 1) | ν/(ν−2) (ν > 2) | 0 | 6/(ν−4) (ν > 4) | Fat-tailed alternative to Gaussian |
| Lognormal LN(µ, σ²) | x⁻¹ (2πσ²)⁻¹ᐟ² exp(−(log x − µ)²/(2σ²)) | exp(µ + σ²/2) | (e^{σ²} − 1) e^{2µ + σ²} | f(σ) | f(σ) | Stock prices in Black–Scholes |
| Exponential (λ) | λe^{−λx}, x ≥ 0 | 1/λ | 1/λ² | 2 | 6 | Inter-arrival of Poisson |
| Gamma (α, β) | x^{α−1} e^{−βx} β^α / Γ(α), x ≥ 0 | α/β | α/β² | 2/√α | 6/α | Sums of exponentials |
| Beta (α, β) | x^{α−1}(1−x)^{β−1} / B(α, β), 0 ≤ x ≤ 1 | α/(α+β) | αβ/((α+β)²(α+β+1)) | f | f | Bounded variables, prior on probabilities |
| Poisson (λ) | e^{−λ} λ^k / k! | λ | λ | 1/√λ | 1/λ | Count of events |
| GPD (ξ, σ) | (1/σ)(1 + ξx/σ)^{−1/ξ−1} | σ/(1 − ξ) | σ²/((1−ξ)²(1−2ξ)) | f | f | Tail distribution; doc 206 |
| α-stable (α, β) | no closed-form | varies | infinite for α < 2 | varies | varies | Lévy-stable, infinite variance for α<2 |

The lognormal entry deserves a special note. In Black–Scholes, the stock price is lognormal because log returns are normally distributed. The mean of the lognormal is *not* the mean of the underlying normal — this is the source of the famous "risk-neutral drift correction" −σ²/2 that appears whenever you exponentiate a Brownian motion. Forgetting this correction is the most common bug in bespoke option-pricing code.

### Expectation, Variance, and Their Linear Algebra

For any integrable random variable X, expectation is *linear*: 𝔼[αX + βY] = α𝔼[X] + β𝔼[Y]. Variance is *not* linear in general: Var(αX + βY) = α²Var(X) + β²Var(Y) + 2αβCov(X, Y). This trivial-looking identity is the entire foundation of mean–variance optimization — Markowitz's 1952 portfolio theory says you can dominate any single asset by combining assets whose variances and covariances are known. The conceptual leap to continuous time is small: replace covariance with quadratic covariation, σ²Δt with ⟨X, Y⟩_t, and the optimization stays the same.

In matrix form, if Σ is the n×n covariance matrix of returns and w is the weight vector, the portfolio variance is wᵀΣw. The minimum-variance portfolio (under the constraint 1ᵀw = 1) is

$$
w^* = \frac{\Sigma^{-1} \mathbf{1}}{\mathbf{1}^\top \Sigma^{-1} \mathbf{1}}.
$$

The mean–variance efficient portfolio with target return µ_target is found by minimizing wᵀΣw subject to 1ᵀw = 1 and µᵀw = µ_target. The Lagrangian gives w* = αΣ⁻¹1 + βΣ⁻¹µ for constants α, β depending on the targets. Fast Sharpe-maximizing computation reduces to solving a 2×2 linear system in α, β. We revisit this idea in document 84 (Minimum Torsion Bets) and in document 218 (Hedge Fund Risk Operations).

### Reality Check — Sample Estimators Are Not the Truth

Every sample mean, sample variance, sample correlation you compute is a *random variable*. In small samples, sample variance underestimates true variance (the famous n vs n − 1 correction is a partial fix), sample correlation has heavy tails, and sample skewness is essentially uninformative for n < 200. The standard mistake is to plug a sample estimate into a deterministic formula and treat the output as fact. A better mental model: every quantity you compute has a *distribution* itself, and your decisions should account for the dispersion of that distribution, not its point estimate. This is the core argument for the **Bayesian** approach, covered in document 203.

---

## Conditional Expectation and Filtrations

Conditional expectation is the bridge between elementary probability and the dynamic, time-indexed world we live in as traders. The intuition — given some information, what is the expected value of something? — is universal. The mathematics is more careful: conditional expectation is a *random variable*, not a number, and it lives in a sub-σ-algebra that encodes "what we know."

### Conditional Expectation as a Projection

Let X ∈ L¹(Ω, ℱ, ℙ) and let 𝒢 ⊆ ℱ be a sub-σ-algebra. The **conditional expectation** 𝔼[X | 𝒢] is a 𝒢-measurable random variable Y satisfying

$$
\int_A X \, d\mathbb{P} = \int_A Y \, d\mathbb{P} \quad \text{for every } A \in \mathcal{G}.
$$

By the Radon–Nikodym theorem, such Y exists and is unique up to ℙ-null sets. When X ∈ L², 𝔼[X | 𝒢] is the orthogonal projection of X onto the closed subspace L²(𝒢) ⊆ L²(ℱ). This geometric picture is the cleanest way to remember the key properties:

1. **Tower property**: if 𝒢 ⊆ ℋ ⊆ ℱ, then 𝔼[𝔼[X | ℋ] | 𝒢] = 𝔼[X | 𝒢]. (Smaller projection wins.)
2. **Taking out what is known**: if Y is 𝒢-measurable and XY is integrable, then 𝔼[XY | 𝒢] = Y 𝔼[X | 𝒢].
3. **Linearity**: 𝔼[αX + βY | 𝒢] = α𝔼[X | 𝒢] + β𝔼[Y | 𝒢].
4. **Independence**: if X is independent of 𝒢, then 𝔼[X | 𝒢] = 𝔼[X].
5. **Jensen**: for convex φ, φ(𝔼[X | 𝒢]) ≤ 𝔼[φ(X) | 𝒢].

The tower property is the conditioning analog of "the law of total probability." When you average a conditional expectation over a finer σ-algebra, you get back the conditional expectation under the coarser σ-algebra. This is the fact that makes martingale theory work.

### Filtrations: The Time-Indexed Information

A **filtration** on (Ω, ℱ, ℙ) is a family {ℱ_t}_{t ≥ 0} of sub-σ-algebras with ℱ_s ⊆ ℱ_t whenever s ≤ t. The σ-algebra ℱ_t represents the information available at time t. We say a stochastic process X = {X_t} is **adapted** to the filtration if X_t is ℱ_t-measurable for every t; equivalently, X_t can be computed from the information available at time t.

Two filtrations matter most:
- The **natural filtration** ℱ_t^X = σ(X_s : s ≤ t) generated by X up to time t.
- An **enlarged filtration** that includes additional information: 𝒢_t = ℱ_t^X ∨ σ(τ) for some random time τ that is not ℱ_t^X-stopping, or 𝒢_t = ℱ_t ∨ ℱ_∞^Y for some auxiliary process Y. Enlargement of filtration is the technical engine of insider-information models and of the so-called Brownian bridges in pinning literature.

For the bulk of this document, we work with the filtration generated by the price process, augmented with the null sets and right-continuized:

$$
\mathcal{F}_t = \sigma(S_u : u \le t) \vee \mathcal{N},
$$

where 𝒩 is the σ-algebra of ℙ-null sets. This is the **augmented natural filtration**, and the convention is to additionally take the right-continuous version ℱ_t⁺ = ⋂_{s > t} ℱ_s. The augmentation and right-continuity together are called the **usual conditions**, and we will assume them throughout — without them, several technical results (Doob–Meyer decomposition, optional sampling at unbounded stopping times) require additional hypotheses that obscure rather than illuminate.

```python
# Build the natural filtration of a coin-flip process and verify the tower property numerically.
import numpy as np
from itertools import product

n = 4
omega = list(product(['H', 'T'], repeat=n))
P = {w: 1.0 / len(omega) for w in omega}

# Random variable: number of heads in all n flips.
def X(w): return sum(1 for c in w if c == 'H')

# Sigma-algebra at time t = first t flips.
def F_t(t):
    classes = {}
    for w in omega:
        key = w[:t]
        classes.setdefault(key, []).append(w)
    return classes

def conditional_expectation(t):
    classes = F_t(t)
    out = {}
    for key, atoms in classes.items():
        ev = sum(X(w) * P[w] for w in atoms) / sum(P[w] for w in atoms)
        for w in atoms:
            out[w] = ev
    return out

# Tower property: E[E[X|F_3]|F_2] = E[X|F_2]
e3 = conditional_expectation(3)
def tower(t):
    classes = F_t(t)
    out = {}
    for key, atoms in classes.items():
        avg = sum(e3[w] * P[w] for w in atoms) / sum(P[w] for w in atoms)
        for w in atoms:
            out[w] = avg
    return out

assert all(np.isclose(conditional_expectation(2)[w], tower(2)[w]) for w in omega)
```

The code above is more than a toy. Replace "coin flip" by "tick movement" and "X = number of heads" by "X = realized P&L at end of day," and you have a literal working description of the conditional-expectation logic that underlies every intraday risk computation. Every time you ask "given what I know now, what is my expected end-of-day P&L?" you are computing 𝔼[X | ℱ_t].

### Conditional Variance and Conditional Distribution

Conditional variance is defined analogously: Var(X | 𝒢) = 𝔼[(X − 𝔼[X | 𝒢])² | 𝒢]. The decomposition

$$
\text{Var}(X) = \mathbb{E}[\text{Var}(X | \mathcal{G})] + \text{Var}(\mathbb{E}[X | \mathcal{G}])
$$

is called the **law of total variance**. It says: total variance equals the average of conditional variances (the "noise" you cannot remove by knowing 𝒢) plus the variance of the conditional means (the "signal" that 𝒢 reveals). In trading, this is exactly the decomposition of returns variance into idiosyncratic and systematic components — Var(systematic) is the variance of 𝔼[ret | factor exposures], and Var(idiosyncratic) is 𝔼[Var(ret | factor exposures)].

The **conditional distribution** of X given 𝒢 is the function ω ↦ μ_{X|𝒢}(ω, ·), where for each ω, μ_{X|𝒢}(ω, ·) is a probability measure on ℝ. Under regularity conditions (which always hold for Polish state spaces — i.e., for every state space we will encounter), the conditional distribution exists and gives 𝔼[f(X) | 𝒢](ω) = ∫ f(x) μ_{X|𝒢}(ω, dx). This object lets us speak about, e.g., the *conditional density* of tomorrow's return given today's information.

### Reality Check — Information Sets in Real Trading

In production, ℱ_t is a much messier object than the math suggests. It includes:
- The market data feed (ticks, quotes, trades) up to time t.
- Whatever derived state (rolling means, EMAs, indicators) you have computed.
- Any external information (news, social media, weather) that has arrived by t.
- Internal state (current positions, P&L, risk limits).
- Knowledge of *your own* prior orders and the market reaction to them.

The last bullet is subtle. If you placed a large buy order at time t − Δt and the market moved up afterwards, ℱ_t contains your own price impact. Strategies that ignore this — that re-evaluate their signal as if the current price were exogenous — systematically overestimate alpha. Document 201 (Market Microstructure) treats this in detail.

---

## Discrete-Time Martingales

A discrete-time stochastic process M = {M_n}_{n ≥ 0} adapted to a filtration {ℱ_n} is a **martingale** if M_n ∈ L¹ for every n and

$$
\mathbb{E}[M_{n+1} \mid \mathcal{F}_n] = M_n.
$$

It is a **submartingale** if 𝔼[M_{n+1} | ℱ_n] ≥ M_n, and a **supermartingale** if 𝔼[M_{n+1} | ℱ_n] ≤ M_n. The intuition: a martingale is a "fair game" — given everything you know, your expected position tomorrow equals your position today. Submartingales drift up; supermartingales drift down.

### Why Martingales Matter

The fundamental theorems of asset pricing say that, in a frictionless market with no arbitrage, the discounted prices of all tradable assets are martingales under some equivalent probability measure ℚ. This is *the* connection between probability theory and pricing. Every option-pricing formula you have ever seen — Black–Scholes, Heston, SABR, jump-diffusion — is a conditional expectation of the discounted payoff under the risk-neutral measure. The job of a quant is to choose ℚ, write down the martingale that prices the asset, and compute the expectation.

### Doob's Decomposition

Every adapted L¹ process X can be uniquely decomposed as X_n = M_n + A_n, where M is a martingale and A is a predictable process (A_n ∈ ℱ_{n−1}) with A_0 = 0. The increments are A_n − A_{n−1} = 𝔼[X_n − X_{n−1} | ℱ_{n−1}] (the "drift") and M_n − M_{n−1} = X_n − X_{n−1} − A_n + A_{n−1} (the "noise"). This decomposition is the discrete-time analog of the Doob–Meyer decomposition we will need in continuous time, and it is also the cleanest way to think about *signal vs noise* in a return series.

### Doob's Maximal Inequality

For a non-negative submartingale {M_n}, the maximum running value M_n* = max_{k ≤ n} M_k satisfies

$$
\mathbb{P}(M_n^* \ge \lambda) \le \frac{\mathbb{E}[M_n]}{\lambda}, \qquad \lambda > 0.
$$

Doob's L^p inequality for p > 1 says 𝔼[(M_n*)^p] ≤ (p/(p−1))^p 𝔼[M_n^p]. Both inequalities are central in proving convergence of stochastic integrals. They also have a tradable interpretation: if your equity curve is a positive submartingale, the probability that its running maximum exceeds some level is bounded by the current expected value divided by that level. This gives a cheap way to upper-bound drawdown probabilities under model assumptions.

### Optional Stopping

A **stopping time** τ is a random time τ : Ω → {0, 1, …, ∞} such that {τ ≤ n} ∈ ℱ_n for every n. The intuition: the decision to stop at time n must depend only on information available by time n. (You cannot say "stop when the price first exceeds the maximum of the next 10 days"; that uses future information.)

For a martingale M and a bounded stopping time τ, the **optional stopping theorem** says 𝔼[M_τ] = 𝔼[M_0]. If τ is unbounded, additional integrability is required; the simplest sufficient condition is uniform integrability of the family {M_{τ ∧ n}}.

In trading: if your wealth process is a martingale (e.g., you trade fairly with no edge after costs), then on any stopping rule that is bounded a priori, your expected wealth at the stop equals your expected wealth at start. Stopping rules like "exit at first price target or after N hours" are stopping times; "exit when the future maximum hits a level" is not. Many "miracle" trading rules are secretly using future information and would violate optional stopping if rewritten properly.

### Martingale Convergence

Doob's martingale convergence theorem: every L¹-bounded martingale {M_n} converges almost surely to some integrable random variable M_∞. If the family is uniformly integrable, the convergence also holds in L¹.

This is the statement that licenses long-run pricing arguments. Discounted asset prices that are martingales under ℚ converge as n → ∞, and the limit has a well-defined distribution. This is the asymptotic version of "the present value of an infinite cash-flow stream is a finite, well-defined number."

```python
# A simple example: gambler's ruin as a stopped martingale.
# Two players start with $a and $b. They play a fair game (one dollar per round).
# Let p_a be the probability that the first player wins everything.
# Wealth is a martingale; tau is bounded above by the total bankroll squared (geometric).
# Optional stopping: E[W_tau] = a -> a = (a + b) p_a + 0 (1 - p_a) -> p_a = a / (a + b).
import numpy as np
np.random.seed(0)

def gamblers_ruin(a, b, trials=10_000):
    wins = 0
    for _ in range(trials):
        wealth = a
        total = a + b
        while 0 < wealth < total:
            wealth += 1 if np.random.rand() < 0.5 else -1
        wins += 1 if wealth == total else 0
    return wins / trials

a, b = 7, 13
p_a_empirical = gamblers_ruin(a, b)
p_a_theory = a / (a + b)
print(f"Empirical: {p_a_empirical:.4f}, Theory: {p_a_theory:.4f}")
```

### Reality Check — Non-Martingale Markets

Real markets are *not* martingales. They have drift (long-run expected return), microstructure mean-reversion (inter-trade autocorrelation in returns), regime changes (volatility clusters), and execution friction (you cannot trade at the displayed price). The martingale property holds *only under the risk-neutral measure*, and even there, only for specific traded combinations (discounted prices of contingent claims). Misapplying martingale arguments to physical-measure quantities is one of the most common sources of theoretical embarrassment in quantitative trading.

---

## Stopping Times and Optional Stopping

Stopping times generalize hitting times, exit times, and many other natural rules by demanding that the decision to stop depend only on the past. Their importance to finance is direct: every barrier option (knock-in, knock-out, lookback, American) can be expressed via a stopping time, and almost all path-dependent valuation reduces to computing 𝔼^ℚ[f(τ, X_τ)] for some stopping time τ.

### Examples

- *First-hitting time*: τ_a = inf{t ≥ 0 : X_t ≥ a}. The first time the process X exceeds level a.
- *Exit time from a corridor*: τ = inf{t ≥ 0 : X_t ∉ (a, b)}. The first time X leaves the strip.
- *Stop-loss / take-profit*: τ = inf{t ≥ 0 : P_t / P_0 − 1 ≤ −SL or ≥ TP}.
- *Doubly-randomized stopping*: stop at the first time the process exceeds a level *or* an external timer expires.

### σ-Algebra at a Stopping Time

If τ is a stopping time, the σ-algebra ℱ_τ is defined as

$$
\mathcal{F}_\tau = \{ A \in \mathcal{F} : A \cap \{ \tau \le t \} \in \mathcal{F}_t \text{ for all } t \}.
$$

This is the information available at the random time τ — what we know "the moment we stop." For two stopping times σ ≤ τ, ℱ_σ ⊆ ℱ_τ. This is what makes the optional stopping theorem possible: stopping respects the information ordering.

### The Strong Markov Property

For a Markov process X (the future depends on the past only through the present), the **strong Markov property** says that the process restarted at any stopping time τ has the same distributional structure as the process restarted at a deterministic time. Formally, conditional on ℱ_τ ∩ {τ < ∞}, the process {X_{τ + s}}_{s ≥ 0} has the law of {X_s} starting from X_τ. This is the technical ingredient that turns "the price hit the barrier" into "the price now is whatever was at the barrier, and we restart."

We use the strong Markov property repeatedly when pricing barrier options: at the first hitting time of the barrier, the option's payoff structure changes (knock-in becomes a vanilla, knock-out becomes zero or a cash rebate), and we re-price the resulting structure as if the asset were starting fresh from the barrier.

### Wald's Identity

For a sum S_n = X_1 + … + X_n of iid integrable summands and a stopping time τ with finite mean, **Wald's identity** says 𝔼[S_τ] = 𝔼[X_1] 𝔼[τ]. The intuition: when you stop summing iid variables at a stopping time, the expected sum is the expected number of terms times the expected per-term value. We will see continuous-time analogs in the form of the optional sampling theorem and Doob's identity for stochastic integrals.

### Reality Check — Stopping Times Are Halt Conditions

Every algorithmic trading system has *halt conditions* — daily P&L stop-loss, max drawdown, position limit breach, market-data staleness. These are the operational instantiation of stopping times. They are non-trivial to implement correctly because they must:
- Be measurable with respect to the live information set.
- Be monotone — once triggered, they should not be silently un-triggered by reverting state.
- Compose correctly under partial fills and asynchronous market data.
- Allow for a well-defined post-stop behavior (flatten, hedge, alert).

A frequent production bug: the stopping condition checks an indicator that is computed over a window straddling future bars (e.g., a centered moving average). The condition then becomes ℱ_T-measurable rather than ℱ_t-measurable, and in backtests it appears to "see the future." Always audit halt conditions for measurability.

---

## Part II — Brownian Motion

We now begin the heart of continuous-time finance: the standard Brownian motion (Wiener process). We construct it, derive its key properties, and develop the tools needed to integrate against it. Brownian motion is the unique continuous martingale with stationary, independent, mean-zero, variance-t increments — and it is the building block of essentially every equity, FX, and rates model in widespread use.

### Definition

A standard one-dimensional **Brownian motion** {W_t}_{t ≥ 0} on (Ω, ℱ, ℙ) is a continuous-path, real-valued stochastic process satisfying:

1. W_0 = 0 almost surely.
2. **Independent increments**: for 0 ≤ s < t, the increment W_t − W_s is independent of ℱ_s.
3. **Stationary Gaussian increments**: W_t − W_s ∼ 𝒩(0, t − s).
4. **Continuous paths**: the map t ↦ W_t(ω) is continuous in t, ℙ-almost surely.

These four properties pin down the law of W uniquely. The construction — proving such a process exists — is non-trivial. Three classical approaches:

- **Kolmogorov consistency**: define the finite-dimensional distributions (multivariate Gaussians with the right covariance) and use the Kolmogorov extension theorem to lift them to a process. Then prove (via the Kolmogorov continuity criterion) that there is a continuous version.
- **Lévy's construction**: build the process inductively at dyadic times by interpolating between coarser-resolution Gaussians. The series converges uniformly on compacts almost surely, yielding a continuous process.
- **Donsker's invariance principle**: take a random walk with mean-zero, finite-variance steps, time-scale and amplitude-scale, and show the rescaled process converges in distribution (in the Skorokhod topology) to Brownian motion.

The third approach is the most "physical" — it tells you that Brownian motion is the universal limit of any sufficiently aggregated random walk, regardless of the step distribution (subject to finite variance). This is why it appears as the natural model for additive noise.

```python
# Donsker's invariance principle in action: random walk -> Brownian motion.
import numpy as np
import matplotlib.pyplot as plt

def random_walk_to_BM(N, T=1.0, p=0.5):
    steps = np.where(np.random.rand(N) < p, 1, -1)
    walk = np.cumsum(steps)
    # Donsker scaling: divide by sqrt(N) and stretch time.
    times = np.linspace(0, T, N + 1)
    process = np.concatenate([[0], walk / np.sqrt(N) * np.sqrt(T)])
    return times, process

fig, ax = plt.subplots(figsize=(8, 4))
np.random.seed(7)
for N in [50, 500, 5000]:
    t, w = random_walk_to_BM(N)
    ax.plot(t, w, label=f"N = {N}")
ax.set_title("Random walk → Brownian motion (Donsker scaling)")
ax.set_xlabel("t"); ax.set_ylabel("W_t"); ax.legend(); ax.grid(True)
plt.tight_layout(); plt.savefig("donsker.png", dpi=120)
```

### Key Properties of Brownian Motion

We list the most important ones; each will be used later in the document.

- **Gaussian process**: any finite collection (W_{t₁}, …, W_{tₙ}) is jointly Gaussian with mean zero and covariance Cov(W_s, W_t) = min(s, t).
- **Markov**: the strong Markov property holds — given ℱ_s, the process {W_{s+u} − W_s}_{u ≥ 0} is independent of ℱ_s and is itself a Brownian motion.
- **Martingale**: W is a martingale with respect to its own filtration. So is W_t² − t.
- **Time inversion**: the process {tW_{1/t}}_{t > 0} (with value 0 at t = 0) is a Brownian motion.
- **Symmetry**: −W is a Brownian motion; reflected Brownian motion |W_t| is not.
- **Self-similarity**: for c > 0, {c W_{t/c²}}_{t ≥ 0} has the same law as W. (Hurst exponent ½.)
- **Brownian scaling and time change**: under any deterministic time change τ(t), the process W_{τ(t)} is a Gaussian process with covariance min(τ(s), τ(t)) — useful when modeling assets with deterministic volatility.
- **No differentiability**: Brownian paths are nowhere differentiable, almost surely. This is the defect that prevents Riemann–Stieltjes integration and forces Ito theory.
- **Hölder continuity**: W is α-Hölder continuous for every α < ½, almost surely, but not for α = ½. This is the precise statement of "Brownian paths are continuous but very rough."
- **Quadratic variation**: ⟨W⟩_t = t, almost surely. We make this precise next.

### Sampling and Simulation

To simulate W on a grid 0 = t_0 < t_1 < … < t_N = T:

```python
import numpy as np

def simulate_brownian(T, N, seed=None):
    if seed is not None:
        np.random.seed(seed)
    dt = T / N
    increments = np.random.normal(0, np.sqrt(dt), N)
    W = np.concatenate([[0], np.cumsum(increments)])
    times = np.linspace(0, T, N + 1)
    return times, W
```

For correlated multidimensional Brownian motion in d dimensions with correlation matrix R = (ρ_{ij}), Cholesky-decompose R = LLᵀ and set W_t = L Z_t, where Z is a vector of independent standard Brownian motions. The d-dimensional analog of Cov(W_s, W_t) = min(s, t) I is min(s, t) R, and the cross-quadratic variation ⟨W^i, W^j⟩_t = ρ_{ij} t. We will use this when we work in multi-asset settings.

### Reflection Principle

Let τ_a = inf{t ≥ 0 : W_t = a} for a > 0. The **reflection principle** gives a closed form for the running maximum: ℙ(max_{0 ≤ s ≤ t} W_s ≥ a) = 2 ℙ(W_t ≥ a). Equivalently, the joint density of (max_{0 ≤ s ≤ t} W_s, W_t) is a known explicit Gaussian-derived expression.

The proof is geometric: each path that crosses level a and ends below a corresponds, by reflecting after the hitting time, to a path that ends above a — and Brownian motion is symmetric under reflection. So ℙ(max ≥ a, W_t ≤ a) = ℙ(W_t ≥ a). Add the obvious ℙ(max ≥ a, W_t > a) = ℙ(W_t > a), and you get the formula.

The reflection principle is the engine of barrier-option pricing. The price of a knock-out option, for example, is the price of a vanilla minus a probability-weighted reflected contribution.

```python
# Verify reflection principle by simulation.
import numpy as np
np.random.seed(0)

def hitting_max_check(a, T, n_paths, n_steps):
    dt = T / n_steps
    increments = np.random.normal(0, np.sqrt(dt), (n_paths, n_steps))
    W = np.concatenate([np.zeros((n_paths, 1)), np.cumsum(increments, axis=1)], axis=1)
    M = W.max(axis=1)
    p_max = np.mean(M >= a)
    p_end = np.mean(W[:, -1] >= a)
    return p_max, 2 * p_end

a, T = 0.6, 1.0
p_max_emp, p_max_theory = hitting_max_check(a, T, 50_000, 250)
print(f"P(max W >= a): empirical={p_max_emp:.4f}, theory=2 P(W_T>=a)={p_max_theory:.4f}")
```

### Brownian Bridge

The Brownian bridge B is the process W conditioned on W_T = b, expressed cleanly as

$$
B_t = W_t - \frac{t}{T}(W_T - b), \qquad 0 \le t \le T.
$$

Its mean is b t / T and its covariance is min(s, t) − st/T. Two facts make the bridge useful: it is Gaussian (so all path-dependent expectations against it are tractable), and it satisfies the SDE

$$
dB_t = \frac{b - B_t}{T - t} \, dt + dW_t.
$$

Brownian bridges are central to *path simulation with terminal conditioning* — useful in calibration when you observe an at-the-money implied volatility but want to simulate paths consistent with both the start and end. They are also the basis of Brownian-bridge variance reduction in Monte Carlo: instead of sampling forward, sample the endpoint and fill in the bridge — the variance is much smaller for path-dependent functionals.

### Time-Changed Brownian Motion

Let τ : [0, T] → [0, T'] be a continuous, increasing function. The process Y_t = W_{τ(t)} is a Gaussian process with Cov(Y_s, Y_t) = τ(min(s, t)). In particular, if τ is *also* random and adapted, but increases continuously and starts at 0, the time-changed process is still a Gaussian if τ is independent of W; if τ is correlated with W, things are more subtle (this is the heart of stochastic-volatility modeling).

The Dambis–Dubins–Schwarz theorem gives a partial converse: every continuous local martingale M with quadratic variation ⟨M⟩ that diverges to infinity is a time-changed Brownian motion: M_t = W_{⟨M⟩_t} for some Brownian motion W. This is one reason all continuous local martingales "look like" Brownian motion in their natural time scale — and why time-changed Brownian motion is such a flexible model class.

### Reality Check — Real Returns Are Not Gaussian

If you fit a Gaussian to daily returns of any major equity index over the past 30 years, you will find that the data have *fat tails* — the empirical kurtosis is not 3 but typically 5 to 12, and the tail probabilities at, say, 4σ events are an order of magnitude larger than the Gaussian predicts. This is one reason all the modern modeling work on stochastic volatility, jump diffusions, and rough volatility was done in the first place. We will treat each of these in due course.

The good news: the *aggregated* return over many periods often does look closer to Gaussian (CLT). The bad news: at horizons relevant to most trading (intraday, daily), the Gaussian approximation has systematic blind spots, and we need richer models.

---

## Quadratic Variation and Path Roughness

Quadratic variation is the single most important quantity in continuous-time finance. It is *not* a curiosity — it is the engine that makes Ito calculus different from ordinary calculus, and it is the place where volatility lives in continuous time.

### Definition

For a stochastic process X on [0, T] and a partition Π = {0 = t_0 < t_1 < … < t_N = T}, define

$$
V_\Pi(X) = \sum_{i=0}^{N-1} (X_{t_{i+1}} - X_{t_i})^2.
$$

If V_Π converges in probability to a limit as the mesh ∥Π∥ = max_i (t_{i+1} − t_i) → 0, that limit is called the **quadratic variation** of X up to time T, denoted ⟨X⟩_T or [X]_T.

For Brownian motion, ⟨W⟩_T = T. The proof is short and worth memorizing:

- 𝔼[V_Π] = ∑ (t_{i+1} − t_i) = T.
- Var(V_Π) = 2 ∑ (t_{i+1} − t_i)² ≤ 2 T ∥Π∥ → 0 as ∥Π∥ → 0.

So V_Π → T in L², hence in probability. (With more work, one gets almost-sure convergence along refining partitions.)

The remarkable thing is what this implies. For a continuously differentiable function f, the quadratic variation is zero — the sum of squares of small increments goes to zero faster than the partition mesh. For Brownian motion, the sum of squares converges to a *positive* number (T), which means the increments are "of order √Δt" — the famous (dW)² = dt heuristic.

```python
# Convergence of quadratic variation for Brownian motion.
import numpy as np
np.random.seed(42)

T, n_steps_list = 1.0, [10, 100, 1000, 10_000, 100_000]
for N in n_steps_list:
    dt = T / N
    W = np.concatenate([[0], np.cumsum(np.random.normal(0, np.sqrt(dt), N))])
    qv = np.sum(np.diff(W)**2)
    print(f"N = {N:>7}: QV = {qv:.6f} (true: {T})")
```

The output shows QV converging to T = 1 as N grows — even though each individual realization has small fluctuations. This is the operational meaning of "the quadratic variation of Brownian motion is deterministic."

### Why Riemann Integration Fails for Stochastic Integrals

Recall the Riemann–Stieltjes integral ∫_0^T f(t) dg(t) of a continuous f against a function g of bounded variation. For each partition, the choice of evaluation point t_i^* ∈ [t_i, t_{i+1}] within the interval does not matter in the limit — left endpoint, right endpoint, midpoint, all give the same answer. This is the fundamental property that makes Riemann integration well-defined and consistent.

For a stochastic integral against Brownian motion, this fails. Brownian paths have *infinite variation* on any interval — that is, sup_Π ∑ |W_{t_{i+1}} − W_{t_i}| = ∞ almost surely. Consequently, the choice of evaluation point matters: the integral ∑ f(t_i^*) (W_{t_{i+1}} − W_{t_i}) depends on whether t_i^* is the left endpoint, midpoint, or right endpoint of [t_i, t_{i+1}].

The **Ito integral** chooses the *left endpoint*: t_i^* = t_i. The **Stratonovich integral** chooses the *midpoint*: t_i^* = (t_i + t_{i+1})/2. They differ by a "drift correction" related to the quadratic covariation between f and W. We will work primarily with the Ito integral because it has the martingale property — Ito stochastic integrals are local martingales — which is exactly what we need for pricing.

### The Ito-Stratonovich Conversion

If X satisfies dX_t = µ(X_t) dt + σ(X_t) dW_t in the Ito sense, then the same process satisfies

$$
dX_t = \left(\mu(X_t) - \tfrac{1}{2} \sigma(X_t) \sigma'(X_t)\right) dt + \sigma(X_t) \circ dW_t
$$

in the Stratonovich sense (where ∘ denotes Stratonovich integration). The −½σσ' term is the conversion. In one-dimensional models this is rarely needed; in geometric or differential-geometric settings (option pricing on manifolds, gauge-theoretic models of FX) the Stratonovich formulation can be cleaner.

### Quadratic Covariation

For two processes X, Y, the **quadratic covariation** is

$$
\langle X, Y \rangle_T = \lim_{\|\Pi\| \to 0} \sum_{i=0}^{N-1} (X_{t_{i+1}} - X_{t_i})(Y_{t_{i+1}} - Y_{t_i}).
$$

For independent Brownian motions W^1, W^2: ⟨W^1, W^2⟩_T = 0. For correlated Brownian motions with correlation ρ: ⟨W^1, W^2⟩_T = ρ T. For two Ito processes dX = µ_X dt + σ_X dW^1 and dY = µ_Y dt + σ_Y dW^2 with ⟨W^1, W^2⟩_t = ρt:

$$
d\langle X, Y \rangle_t = \sigma_X(t) \sigma_Y(t) \rho \, dt.
$$

### The "(dW)² = dt" Heuristic

In informal calculations, one writes (dW_t)² = dt, dW_t · dt = 0, (dt)² = 0. These rules are exact in the limit of vanishing partition mesh — quadratic variation is the rigorous statement. They are the mnemonic version of Ito calculus and let us derive Ito's lemma quickly without fully unpacking the limits each time.

### Reality Check — Realized Volatility and the QV Estimator

In practice, we estimate quadratic variation by *realized variance*:

$$
RV_T^{(\Delta)} = \sum_{i=0}^{N-1} (X_{t_{i+1}} - X_{t_i})^2,
$$

with Δ = T / N. Under the model dX = σ_t dW_t, RV_T^{(Δ)} → ∫_0^T σ_s² ds = ⟨X⟩_T as Δ → 0. In real high-frequency data, however:

- *Microstructure noise* (bid-ask bounce, discrete prices) inflates RV at high frequencies; the realized variance increases without bound as Δ → 0.
- *Jumps* can dominate the smooth quadratic variation; bipower variation and threshold methods separate them.
- *Asynchronous trading* across assets creates the Epps effect (downward bias in realized covariances at high frequency).

The cure: subsample, average over multiple grids, use realized kernels, or threshold-truncate large increments. These corrections are central to modern realized-volatility forecasting and are covered in document 211 (Backtesting Statistical Rigor).

---

## Brownian Bridge, Reflection, and Hitting Times

We collect the most useful path-functional results in one place, since they appear over and over in barrier-option pricing, stress testing, and signal extraction.

### First Hitting Times

For W_0 = 0 and a > 0, the first hitting time τ_a = inf{t : W_t = a} has the Lévy distribution:

$$
\mathbb{P}(\tau_a \le t) = 2 \mathbb{P}(W_t \ge a) = 2 \Phi(-a / \sqrt{t}) = \text{erfc}(a / \sqrt{2t}).
$$

The density is

$$
f_{\tau_a}(t) = \frac{a}{\sqrt{2\pi t^3}} \exp\!\left(-\frac{a^2}{2t}\right).
$$

This is a stable distribution (index ½). It has *infinite mean*: 𝔼[τ_a] = ∞. The intuition: while τ_a < ∞ almost surely, the tail is so heavy that no moment exists. This is why "hitting times of geometric Brownian motion" can be very long even when the median time is short — the mean is not a useful summary.

For Brownian motion *with drift* dX = µ dt + σ dW, the hitting time of a is the first passage of a drifted Gaussian. For µ ≠ 0 and a > 0, ℙ(τ_a < ∞) = 1 if µ ≥ 0, and ℙ(τ_a < ∞) = e^{2µa/σ²} if µ < 0. The expected hitting time conditional on hitting is a / µ when µ > 0.

### Joint Distribution of (W_T, max W)

A canonical result, used in barrier pricing:

$$
\mathbb{P}(M_T \ge m, W_T \le x) = \Phi\!\left(\frac{x - 2m}{\sqrt{T}}\right), \qquad m \ge \max(0, x).
$$

Differentiating gives the joint density. From this and similar results, one derives closed-form prices for up-and-out, down-and-out, double-barrier, and lookback options on a geometric Brownian motion.

### Reflected Brownian Motion

The process |W| is *not* a Brownian motion, but it is a Markov process. It satisfies the SDE

$$
d|W|_t = \text{sgn}(W_t) \, dW_t + dL_t,
$$

where L is the **local time of W at 0** — a continuous, increasing process that grows only when W = 0. Reflected Brownian motion is the key model for Skorokhod-type problems and for some exotic options where the underlying is constrained to remain positive.

### Excursion Theory

The path of Brownian motion can be decomposed into excursions away from zero (continuous segments between consecutive zero-crossings). The Itô excursion measure quantifies the distribution of these excursions. While excursion theory is rarely applied directly in vanilla derivatives pricing, it underlies the analysis of double-barrier options and certain rare-event calculations.

### Reality Check — Hitting Times in Live Trading

In execution algorithms, we routinely compute the *first time* a price hits a target. The theoretical infinite expected hitting time for unbiased random walks is a useful warning: a strategy that "waits for the price to come back to entry" against a martingale return process can wait, in expectation, *forever*. This is one mathematical reason mean-reversion strategies on truly random series have unbounded expected duration; only when there is genuine drift toward the mean (e.g., Ornstein–Uhlenbeck with κ > 0) do the hitting times have finite means.

---

## Part III — The Ito Integral

We now construct the Ito integral. The construction is a little technical, but it is *the* fundamental object in continuous-time finance, and understanding the construction makes everything that follows easier.

### Simple Processes and the Ito Integral on Them

Let H be a **simple process** of the form

$$
H_t(\omega) = \xi_0(\omega) \mathbf{1}_{\{0\}}(t) + \sum_{i=0}^{n-1} \xi_i(\omega) \mathbf{1}_{(t_i, t_{i+1}]}(t),
$$

where 0 = t_0 < t_1 < … < t_n = T and each ξ_i is bounded and ℱ_{t_i}-measurable (predictability with respect to the partition). The Ito integral of H against W on [0, T] is

$$
I_T(H) = \int_0^T H_s \, dW_s = \sum_{i=0}^{n-1} \xi_i (W_{t_{i+1}} - W_{t_i}).
$$

This is just a finite sum of independent Gaussian-distributed terms (after conditioning on the past). Two key properties hold immediately:

- **Mean zero**: 𝔼[I_T(H)] = ∑ 𝔼[ξ_i (W_{t_{i+1}} − W_{t_i})] = ∑ 𝔼[ξ_i] · 0 = 0, since ξ_i is ℱ_{t_i}-measurable and W_{t_{i+1}} − W_{t_i} is independent of ℱ_{t_i} with mean zero.
- **Ito isometry**: 𝔼[I_T(H)²] = ∑ 𝔼[ξ_i² (W_{t_{i+1}} − W_{t_i})²] = ∑ 𝔼[ξ_i²] (t_{i+1} − t_i) = 𝔼[∫_0^T H_s² ds].

The Ito isometry is the crown jewel. It says: the L² norm of the Ito integral equals the L² norm of the integrand. This makes the integral a *bounded linear operator* from L²(predictable) to L²(F_T), and lets us extend the integral by continuity to general L² integrands.

### Extension to General L² Integrands

Let 𝓛² denote the space of predictable processes H with ∥H∥² := 𝔼[∫_0^T H_s² ds] < ∞. The simple processes are dense in 𝓛². For any H ∈ 𝓛², take a sequence of simple processes Hⁿ → H in 𝓛². By the isometry, {I_T(Hⁿ)} is a Cauchy sequence in L²(F_T), hence converges to a unique limit I_T(H). This is the Ito integral of H. The isometry persists: 𝔼[I_T(H)²] = 𝔼[∫_0^T H_s² ds].

For the integral as a *process* in t — that is, the family {I_t(H) : 0 ≤ t ≤ T} — one shows (with more work) that it has a continuous version, that this version is a martingale, and that its quadratic variation is ⟨I(H)⟩_t = ∫_0^t H_s² ds.

```python
# Compute an Ito integral by Riemann-sum approximation with left-endpoint evaluation.
# Verify the Ito isometry.
import numpy as np

T, N, n_paths = 1.0, 10_000, 5_000
dt = T / N
np.random.seed(2024)

dW = np.random.normal(0, np.sqrt(dt), (n_paths, N))
W = np.concatenate([np.zeros((n_paths, 1)), np.cumsum(dW, axis=1)], axis=1)

# Integrand: H_t = W_t. Then int_0^T W_t dW_t = (W_T^2 - T) / 2 by Ito's lemma.
I = np.sum(W[:, :-1] * dW, axis=1)
target = (W[:, -1]**2 - T) / 2

print(f"max|I - target| = {np.max(np.abs(I - target)):.3e}")
print(f"E[I] = {np.mean(I):.4f}  (should be 0)")
print(f"E[I^2] = {np.mean(I**2):.4f}  E[int H^2 ds] = {np.mean(np.sum(W[:, :-1]**2 * dt, axis=1)):.4f}")
```

The numerical match between 𝔼[I²] and 𝔼[∫ W² ds] is the Ito isometry made operational.

### Local Martingale Property

The Ito integral is a **martingale** when the integrand is in 𝓛². For general L² _loc integrands (those with ∫_0^t H² ds < ∞ almost surely but not necessarily in expectation), the integral is a *local martingale* — it becomes a martingale after stopping at suitable random times.

The distinction between martingales and local martingales matters in three contexts:

1. **Strict local martingales**: martingales that fail to be martingales because the family is not uniformly integrable. The Bessel(3) process and certain CEV processes are examples.
2. **Doubling strategies**: martingale strategies that exploit unboundedness to achieve infinite gains in finite time. They are excluded by integrability conditions in the formal theory and by margin requirements in practice.
3. **Local martingale measures**: the equivalent measures under which discounted prices are *local* martingales (rather than martingales) define a strictly larger class of pricing measures than the "true" martingale measures. This shows up in the bubble literature and in some pathological models.

For practical purposes — vanilla and most exotic option pricing — we can assume the martingale property without losing anything important.

### Stochastic Differential Equations

A **stochastic differential equation** (SDE) on (Ω, ℱ, ℙ, {ℱ_t}) is an equation of the form

$$
dX_t = \mu(t, X_t) \, dt + \sigma(t, X_t) \, dW_t, \qquad X_0 = x_0,
$$

where µ : [0, T] × ℝ → ℝ is the **drift coefficient** and σ : [0, T] × ℝ → ℝ is the **volatility (diffusion) coefficient**. The integral form is

$$
X_t = x_0 + \int_0^t \mu(s, X_s) \, ds + \int_0^t \sigma(s, X_s) \, dW_s.
$$

A solution is an adapted, continuous process X satisfying this equation. Two senses of solution exist:

- **Strong solution**: a solution defined on a *given* probability space and Brownian motion, adapted to a given filtration.
- **Weak solution**: a solution defined on *some* probability space, with the joint law of (X, W) prescribed but the underlying space free.

Strong solutions are unique (pathwise) under Lipschitz coefficients; weak solutions are unique in law under weaker conditions. For most of finance — especially when the SDE has Lipschitz coefficients away from the boundary — strong solutions are what we have, and we will not need the weak machinery.

### Existence and Uniqueness — Lipschitz Conditions

If µ and σ are uniformly Lipschitz in x (with constant K) and have linear growth (|µ| + |σ| ≤ K(1 + |x|)), then for every x_0, the SDE has a unique strong solution on [0, T] with 𝔼[sup_{t ≤ T} |X_t|^p] < ∞ for every p ≥ 1. The proof is a standard Picard iteration argument: define X^{(0)} = x_0, X^{(n+1)} = x_0 + ∫µ(s, X_s^{(n)}) ds + ∫σ(s, X_s^{(n)}) dW_s, and show the sequence converges in L² uniformly on [0, T] using the Ito isometry and a Gronwall argument.

When the coefficients are not Lipschitz, things get more interesting. The Cox–Ingersoll–Ross process dr = κ(θ − r) dt + σ √r dW has a non-Lipschitz volatility coefficient at r = 0, but Yamada–Watanabe-type results give unique strong solutions under the Feller condition 2κθ ≥ σ². Without the Feller condition, the boundary at zero is reachable, and the dynamics there require care.

### Markov Property of SDE Solutions

Solutions of SDEs are Markov processes when the coefficients depend only on (t, x) (and not on the path of W). This is the *time-homogeneous Markov property* in the autonomous case µ(x), σ(x). The infinitesimal generator of the diffusion is

$$
\mathcal{L} f(x) = \mu(x) f'(x) + \tfrac{1}{2} \sigma^2(x) f''(x).
$$

This is the operator that appears in the Kolmogorov backward equation: u(t, x) = 𝔼^x[g(X_T)] satisfies ∂_t u + 𝓛 u = 0 with terminal condition u(T, x) = g(x). The forward equation governs the density: ∂_t p(t, x) = 𝓛^* p, where 𝓛^* is the adjoint. These PDE links are the foundation of finite-difference and finite-element option pricing.

### Reality Check — When SDEs Don't Fit

SDEs are smooth — the drift and volatility are functions, the noise is continuous. Real markets have:

- *Jumps* — earnings announcements, crashes, central-bank surprises. These require Lévy or jump-diffusion extensions, covered shortly.
- *Discrete trading times* — auctions, settlement times, market open/close. SDEs describe the in-between dynamics; the boundary conditions matter.
- *Path-dependent risk premia* — borrowing rates, financing costs, capital constraints. These break the Markov property and require more elaborate modeling (e.g., HJM in fixed income).

The discipline is to pick the SDE class matching the regime you are in, calibrate, and verify out-of-sample.

---

## Ito's Lemma — One Dimension

Ito's lemma is the chain rule of stochastic calculus. It is *the* tool for transforming SDEs and for deriving pricing equations.

### Statement

Let X satisfy dX_t = µ_t dt + σ_t dW_t (Ito process — coefficients can depend on time and on X), and let f : ℝ_+ × ℝ → ℝ be twice continuously differentiable. Then Y_t = f(t, X_t) is itself an Ito process with

$$
dY_t = \left(\partial_t f + \mu_t \, \partial_x f + \tfrac{1}{2} \sigma_t^2 \, \partial_{xx} f \right) dt + \sigma_t \, \partial_x f \, dW_t.
$$

The new ingredient versus the ordinary chain rule is the ½σ²∂_{xx}f term. This comes directly from the (dW)² = dt heuristic: the Taylor expansion of f to second order picks up an extra dt-term that the ordinary chain rule does not have.

### Heuristic Derivation

Expand f(t + dt, X_t + dX_t) to second order:

$$
df = \partial_t f \, dt + \partial_x f \, dX + \tfrac{1}{2} \partial_{xx} f \, (dX)^2 + \text{(higher order)}.
$$

Substituting dX = µ dt + σ dW and using (dW)² = dt, (dt)² = 0, dt · dW = 0:

$$
(dX)^2 = (\mu dt + \sigma dW)^2 = \sigma^2 (dW)^2 + 2\mu\sigma \, dt \, dW + \mu^2 (dt)^2 = \sigma^2 dt.
$$

Plug this in to get the formula. The rigorous proof is via Riemann-Stieltjes-like sums, using uniform continuity of f on bounded sets and the Ito isometry — but the heuristic gives the right answer in 30 seconds.

### Examples

**Example 1: Geometric Brownian Motion.** dS_t = µ S_t dt + σ S_t dW_t. Apply Ito to f(s) = log s:

$$
d \log S_t = \tfrac{1}{S_t} \cdot \mu S_t \, dt + \tfrac{1}{S_t} \cdot \sigma S_t \, dW_t + \tfrac{1}{2} \cdot (-\tfrac{1}{S_t^2}) \cdot \sigma^2 S_t^2 \, dt = (\mu - \tfrac{1}{2}\sigma^2) dt + \sigma \, dW_t.
$$

Integrating: log S_T = log S_0 + (µ − ½σ²) T + σ W_T, so S_T = S_0 exp((µ − ½σ²) T + σ W_T). The drift correction −½σ² is the Ito term. This is also the source of the *volatility drag* that makes geometric returns lower than arithmetic returns by ½σ² over long horizons.

**Example 2: f(t, x) = e^{-rt} x.** Apply Ito to a discounted price process:

$$
d(e^{-rt} S_t) = e^{-rt} (dS_t - r S_t \, dt) = e^{-rt} S_t ((\mu - r) dt + \sigma dW_t).
$$

Under the risk-neutral measure (where µ = r), the discounted price is a martingale.

**Example 3: f(t, x) = x².** Then df/dt = 0, df/dx = 2x, d²f/dx² = 2. So d(X²) = 2X dX + (1/2)(2)σ² dt = 2X dX + σ² dt. In particular, for Brownian motion, d(W²) = 2W dW + dt — and integrating gives W_T² − T = 2 ∫_0^T W_s dW_s, recovering the closed form for the canonical Ito integral.

```python
# Sanity-check: simulate GBM both via the SDE and the closed form, verify they agree.
import numpy as np
np.random.seed(2024)

S0, mu, sigma, T, N, n_paths = 100.0, 0.05, 0.20, 1.0, 252, 10_000
dt = T / N

dW = np.random.normal(0, np.sqrt(dt), (n_paths, N))
W = np.concatenate([np.zeros((n_paths, 1)), np.cumsum(dW, axis=1)], axis=1)

# Closed-form GBM at terminal time:
S_closed = S0 * np.exp((mu - 0.5*sigma**2)*T + sigma*W[:, -1])

# Simulated GBM via Euler:
S_euler = np.full(n_paths, S0)
for j in range(N):
    S_euler = S_euler + mu * S_euler * dt + sigma * S_euler * dW[:, j]

print(f"Closed-form mean: {S_closed.mean():.4f}, expected {S0*np.exp(mu*T):.4f}")
print(f"Euler mean      : {S_euler.mean():.4f}")
print(f"Closed-form var : {S_closed.var():.4f}")
print(f"Euler var       : {S_euler.var():.4f}")
```

The Euler approximation has bias (especially for large σ²Δt) — we will return to this in the numerical methods section.

### Time-Dependent Coefficients

If µ and σ depend explicitly on time as well as on X, the same formula holds — just plug in µ_t and σ_t as random processes. Time-dependent coefficients are common in interest-rate models (Hull–White, calibrated to the current yield curve) and in volatility surface models (where σ depends on time-to-maturity and strike).

### Reality Check — The Ito Term Is Real Money

The Ito drift correction is not an artifact. In trading:

- *Volatility drag* on a leveraged ETF: a daily-rebalanced 2× ETF on an index with long-run return µ and volatility σ has expected long-run return ≈ 2µ − 2σ². For σ = 20%, the drag is 8% per year, eroding the advertised "double" exposure. This is exactly the Ito term applied to log(S²).
- *Geometric vs arithmetic mean*: an asset with arithmetic mean return µ and volatility σ has geometric mean ≈ µ − ½σ² over long horizons. The gap is the Ito term.
- *Hedging error*: the discrete-time hedging portfolio for a vanilla option has expected P&L equal to the Ito term integrated over the hedging period. Re-balancing more often reduces variance but not bias if the model is wrong.

Always pay attention to where ½σ²∂_{xx} appears.

---

## Multidimensional Ito Formula and Quadratic Covariation

Markets have many assets and many drivers. We need the multivariate version of Ito's lemma — clean once you have the univariate intuition.

### Setup

Let W = (W^1, …, W^d)ᵀ be a d-dimensional standard Brownian motion (independent components). Let X = (X^1, …, X^n)ᵀ be an n-dimensional Ito process satisfying

$$
dX^i_t = \mu^i_t \, dt + \sum_{j=1}^d \sigma^{ij}_t \, dW^j_t, \qquad i = 1, \ldots, n.
$$

In matrix form, dX_t = µ_t dt + σ_t dW_t with σ_t an n × d matrix. Define the **diffusion matrix**

$$
a_t = \sigma_t \sigma_t^\top, \qquad a^{ij}_t = \sum_{k=1}^d \sigma^{ik}_t \sigma^{jk}_t.
$$

Then ⟨X^i, X^j⟩_t = ∫_0^t a^{ij}_s ds.

### Multidimensional Ito Formula

For f : ℝ_+ × ℝ^n → ℝ twice continuously differentiable, Y_t = f(t, X_t) satisfies

$$
dY_t = \left( \partial_t f + \sum_i \mu^i_t \, \partial_i f + \tfrac{1}{2} \sum_{i,j} a^{ij}_t \, \partial_{ij} f \right) dt + \sum_{i,j} \sigma^{ij}_t \, \partial_i f \, dW^j_t.
$$

The structure is the same as the univariate version: a "first-order" piece from each gradient direction and a "second-order" Ito correction in the form of a Hessian-against-diffusion-matrix double sum.

### Product Rule

For two Ito processes X, Y, the product rule (a special case of the Ito formula applied to f(x, y) = xy):

$$
d(XY)_t = X_t \, dY_t + Y_t \, dX_t + d\langle X, Y \rangle_t.
$$

The cross-variation term is what distinguishes this from the ordinary Leibniz rule. It is critical in deriving hedging formulas: when a portfolio's value depends on two correlated assets, you cannot ignore the covariation term.

### Application: Multi-Asset Portfolio Variance

Consider a portfolio Π = ∑ wᵢSᵢ where each Sᵢ follows GBM with drift µᵢ and vol σᵢ, and the Brownian drivers are correlated by R. Then

$$
d\Pi = \sum_i w_i \, dS_i = \left(\sum_i w_i \mu_i S_i\right) dt + \sum_i w_i \sigma_i S_i \, dW_i.
$$

The instantaneous variance of dΠ is

$$
\text{Var}(d\Pi) = \sum_{i,j} w_i w_j \sigma_i \sigma_j S_i S_j \rho_{ij} \, dt,
$$

which is the continuous-time analog of Markowitz portfolio variance. Setting weights to be a function of (S_1, …, S_n) and applying multi-dimensional Ito gives the dynamics of the portfolio value in a self-financing strategy.

### Reality Check — Correlated Brownians and Sample Correlations

A Brownian-motion correlation matrix is *not* the same as a sample-correlation matrix of returns. The sample matrix is computed from realized returns; the Brownian matrix is a model parameter. They agree in expectation, but the sample matrix has substantial estimation error: with n = 252 daily observations and N = 50 assets, the eigenvalue spectrum of the sample correlation is contaminated by a Marchenko–Pastur distribution, and the smallest eigenvalues are biased downward (sometimes near zero). This is why naive Markowitz optimization over the sample covariance matrix is famously unstable; shrinkage estimators (Ledoit–Wolf) and structural priors (factor models) are mandatory. Document 81 (HRP) and 82 (Black–Litterman) treat this in depth.

---

## Part IV — Stochastic Differential Equations

We have the integration tool (Ito integral) and the chain rule (Ito's lemma). Now we use them to characterize the solutions of the most important SDEs in finance.

### Geometric Brownian Motion

dS_t = µ S_t dt + σ S_t dW_t with S_0 > 0. By the log-transform we derived earlier:

$$
S_t = S_0 \exp\!\left( (\mu - \tfrac{1}{2}\sigma^2) t + \sigma W_t \right).
$$

Properties:
- 𝔼[S_t] = S_0 e^{µt}.
- Var(S_t) = S_0² e^{2µt} (e^{σ²t} − 1).
- S_t is lognormal for every t.
- S is positive almost surely.
- ⟨log S, log S⟩_t = σ² t — variance is linear in time on the log scale.

GBM is the model behind Black–Scholes. Its restrictions are well-known: constant volatility, no jumps, no fat tails. We will see the patches.

### Ornstein–Uhlenbeck Process

dX_t = θ(µ − X_t) dt + σ dW_t. Multiplying by e^{θt} and using Ito gives

$$
d(e^{\theta t} X_t) = \theta \mu e^{\theta t} \, dt + \sigma e^{\theta t} \, dW_t.
$$

Integrating:

$$
X_t = X_0 e^{-\theta t} + \mu (1 - e^{-\theta t}) + \sigma \int_0^t e^{-\theta(t-s)} \, dW_s.
$$

The integral is a Wiener integral (deterministic integrand against W) and is normally distributed with mean zero and variance ∫_0^t e^{-2θ(t-s)} ds · σ² = σ²(1 − e^{-2θt})/(2θ). So

$$
X_t \sim \mathcal{N}\!\left(X_0 e^{-\theta t} + \mu (1 - e^{-\theta t}), \, \frac{\sigma^2 (1 - e^{-2\theta t})}{2\theta}\right).
$$

As t → ∞, X_t → 𝒩(µ, σ²/(2θ)) — the stationary distribution. The half-life of the mean reversion is log(2)/θ.

OU is the canonical mean-reversion model. It is used for pairs trading (the spread is approximately OU), short-rate modeling (Vasicek), and microstructure (the residual of a price after impact decay).

```python
# OU simulation and stationary distribution check.
import numpy as np
np.random.seed(0)

theta, mu, sigma, X0, T, N, n_paths = 2.0, 0.0, 1.0, 5.0, 10.0, 1_000, 5_000
dt = T / N

X = np.full(n_paths, X0)
for _ in range(N):
    X = X + theta*(mu - X)*dt + sigma*np.sqrt(dt)*np.random.normal(size=n_paths)

stationary_var = sigma**2 / (2*theta)
print(f"Empirical mean = {X.mean():.4f} (theory {mu})")
print(f"Empirical var  = {X.var():.4f} (theory {stationary_var})")
```

### Cox–Ingersoll–Ross Process

dr_t = κ(θ − r_t) dt + σ √r_t dW_t with r_0 > 0. The √r_t volatility makes this not directly solvable by Ito, but it has a known transition density (non-central chi-squared), it stays non-negative under the Feller condition 2κθ ≥ σ², and it is the canonical model for short interest rates in the affine-rate family.

The transition density of r_t given r_s = r is

$$
p(t-s, r, r') = c e^{-u-v} \left(\frac{v}{u}\right)^{q/2} I_q(2\sqrt{uv}),
$$

where c = 2κ / (σ²(1 − e^{-κ(t-s)})), u = c r e^{-κ(t-s)}, v = c r', q = 2κθ/σ² − 1, and I_q is the modified Bessel function of the first kind. From this density, bond prices have closed form, and option prices on bonds can be computed by Fourier inversion.

### Vasicek Model

dr_t = κ(θ − r_t) dt + σ dW_t — same as OU. Bonds have price

$$
P(t, T) = A(t, T) e^{-B(t, T) r_t},
$$

with A, B given by ODE-based formulas. Vasicek is mean-reverting and Gaussian, but has the drawback that interest rates can go negative (which we now know happens in real markets, so this is no longer a major flaw).

### Hull–White Extension

Hull–White takes Vasicek and lets θ depend on time, fitting the current yield curve exactly: dr_t = κ(θ_t − r_t) dt + σ dW_t. The function θ_t is calibrated to the initial term structure. This is the workhorse of fixed-income desks for pricing swaptions, caps, and floors. Document 213 covers this in detail.

### Heston Model

A two-dimensional SDE for (S, v):

$$
dS_t = \mu S_t \, dt + \sqrt{v_t} \, S_t \, dW^1_t,
$$
$$
dv_t = \kappa(\theta - v_t) \, dt + \sigma_v \sqrt{v_t} \, dW^2_t,
$$

with d⟨W^1, W^2⟩_t = ρ dt. The variance v follows a CIR process. Heston has a semi-closed form for European options via Fourier inversion, captures the volatility smile and skew, and is the standard "first non-trivial model" in equity derivatives. Document 202 (Volatility Surface Modeling) gives the full calibration recipe.

### Reality Check — Stationary vs Non-Stationary

OU, Vasicek, and CIR have stationary distributions. GBM and Hull–White (with non-trivial θ_t) do not. Stationarity matters for backtesting: under a stationary model, statistics computed from the past are valid forecasts of the future. Under a non-stationary one, they are not — and sample-based estimation of µ has notoriously high variance even with decades of data. (For SPX, the standard error on µ from 100 years of data is still about 1.5% per year — comparable to the alleged equity premium itself.)

---

## Part V — Change of Measure: Girsanov, Risk Neutrality, and Numeraires

This is the conceptual climax of the document. The Girsanov theorem says that you can change the drift of a Brownian-motion-driven SDE by changing the probability measure on the underlying space — and this is *exactly* the trick that lets us price options.

### The Radon–Nikodym Derivative

Two probability measures ℙ, ℚ on (Ω, ℱ) are **equivalent** if they agree on null sets: ℙ(A) = 0 iff ℚ(A) = 0. Equivalently, there exists a positive random variable Z = dℚ/dℙ called the **Radon–Nikodym derivative** such that ℚ(A) = 𝔼^ℙ[Z 1_A] for every A ∈ ℱ. Z has 𝔼^ℙ[Z] = 1, and the inverse measure change has dℙ/dℚ = 1/Z.

### Girsanov's Theorem

Let W be a standard Brownian motion on (Ω, ℱ, ℙ, {ℱ_t}) and let θ = (θ_t) be a predictable process satisfying Novikov's condition 𝔼^ℙ[exp(½ ∫_0^T θ_s² ds)] < ∞. Define the exponential martingale

$$
Z_t = \exp\!\left( -\int_0^t \theta_s \, dW_s - \tfrac{1}{2} \int_0^t \theta_s^2 \, ds \right).
$$

Then Z is a strictly positive martingale with 𝔼^ℙ[Z_T] = 1, and the measure ℚ on ℱ_T defined by dℚ/dℙ = Z_T is equivalent to ℙ. Under ℚ, the process

$$
\widetilde W_t = W_t + \int_0^t \theta_s \, ds
$$

is a standard Brownian motion.

In words: if we change probability measure with Radon–Nikodym derivative Z, the drift of W shifts by −θ. Equivalently, an SDE dX = θ dt + dW under ℙ becomes dX = dW̃ under ℚ — the drift was an artifact of the measure.

### Application: The Black–Scholes World

Under ℙ, dS_t = µ S_t dt + σ S_t dW_t. Choose θ_t = (µ − r)/σ — the "market price of risk." Then under ℚ defined by Z_T as above,

$$
dS_t = \mu S_t \, dt + \sigma S_t \, (d\widetilde W_t - \theta_t \, dt) = (\mu - \sigma \theta) S_t \, dt + \sigma S_t \, d\widetilde W_t = r S_t \, dt + \sigma S_t \, d\widetilde W_t.
$$

Under ℚ, S has drift r — the risk-free rate. So the discounted price S e^{-rt} is a ℚ-martingale.

The Black–Scholes price of a European option with payoff h(S_T) is then

$$
V_0 = \mathbb{E}^{\mathbb{Q}}\!\left[ e^{-rT} h(S_T) \right].
$$

For h(s) = (s − K)^+ (call), the integral becomes the classical Black–Scholes formula:

$$
C(S_0, K, r, \sigma, T) = S_0 \Phi(d_+) - K e^{-rT} \Phi(d_-),
$$

where d_± = (log(S_0 / K) + (r ± ½σ²) T) / (σ √T).

The derivation: under ℚ, log S_T = log S_0 + (r − ½σ²) T + σ W̃_T, so log S_T ∼ 𝒩(log S_0 + (r − ½σ²) T, σ² T). Compute 𝔼^ℚ[(S_T − K)^+] = ∫_K^∞ (s − K) f_{S_T}(s) ds, which after change of variable simplifies to the formula above.

```python
# Black-Scholes pricer + delta + vega via the closed forms.
import numpy as np
from scipy.stats import norm

def bs_call(S, K, r, sigma, T):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)

def bs_delta(S, K, r, sigma, T):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.cdf(d1)

def bs_vega(S, K, r, sigma, T):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T)

S, K, r, sigma, T = 100.0, 100.0, 0.04, 0.20, 1.0
print(f"Call price = {bs_call(S, K, r, sigma, T):.4f}")
print(f"Delta      = {bs_delta(S, K, r, sigma, T):.4f}")
print(f"Vega       = {bs_vega(S, K, r, sigma, T):.4f}")
```

### Self-Financing Replication

A self-financing portfolio (Δ_t shares of S, B_t units of cash) has value V_t = Δ_t S_t + B_t and obeys dV_t = Δ_t dS_t + r B_t dt. Choosing Δ_t to match the option's delta makes V replicate the option payoff. The cost of the replicating portfolio at time 0 is V_0 = 𝔼^ℚ[e^{-rT} h(S_T)] — the same as the risk-neutral expectation. This is the **fundamental theorem of asset pricing**: in a frictionless complete market, the price equals the cost of replication equals the risk-neutral expectation.

### Numeraire Change

A **numeraire** is a positive, traded asset N. The price of a contingent claim X is

$$
\frac{X_0}{N_0} = \mathbb{E}^{\mathbb{Q}^N}\!\left[\frac{X_T}{N_T}\right],
$$

where ℚ^N is the equivalent measure under which all prices divided by N are martingales. Different numeraires give different convenient pricing measures:

- **Money-market account**: ℚ^B is the risk-neutral measure.
- **T-forward bond P(t, T)**: ℚ^{T} is the **T-forward measure**. Forward prices for delivery at T are martingales under ℚ^{T}.
- **Foreign currency**: ℚ^F is the foreign-currency risk-neutral measure. Spot FX rates expressed in foreign units are martingales.

The Radon–Nikodym derivative for changing from ℚ^M to ℚ^N is dℚ^N/dℚ^M = (N_T M_0)/(M_T N_0). This is the "abstract Bayes" formula — the cleanest way to compute any change-of-numeraire correction.

The forward measure is especially useful for interest-rate derivatives. Under ℚ^T, the forward rate F(t, S, T) is a martingale, and Black's formula (Black '76) for caps and floors falls out of a single Gaussian moment computation.

### Reality Check — When the Real World Disagrees

The risk-neutral measure is a *mathematical* device, not a description of physical reality. The expected return of stocks under ℚ is r; under ℙ, it is something larger (the equity risk premium). The two measures agree on volatility (Girsanov changes drifts but not volatilities), so options "priced under ℚ" can still be hedged using physical-volatility considerations. But:

- Volatility risk premia: implied vol systematically exceeds realized vol on equity indices (the famous "VRP"), creating short-vol opportunities.
- Skew risk premia: out-of-the-money puts trade at higher implied vols than calls, beyond what a Gaussian model would predict.
- Correlation premia: index options trade richer than baskets of single-name options imply, because correlation risk is priced.

These departures from "risk-neutral world is just like our world but with drift r" are systematic, persistent, and the source of much of the volatility-trading literature. Documents 27 (Volatility Risk Premium), 60 (Volatility Dispersion), and 7 (Stochastic Volatility for Gold) treat them.

---

## Part VI — Jumps, Poisson Processes, and Lévy Processes

Real-world price processes are not continuous. Earnings, central-bank announcements, geopolitical shocks, and crashes introduce *jumps*. Modeling jumps requires extending the Brownian framework to **Lévy processes** — processes with stationary, independent increments that need not be continuous.

### Poisson Process

A **homogeneous Poisson process** N with intensity λ > 0 is an integer-valued, increasing process with:
1. N_0 = 0.
2. Independent increments.
3. Stationary increments: N_t − N_s has the Poisson distribution with parameter λ(t − s).
4. Jumps of size +1 only.

Equivalently, the inter-arrival times τ_n = T_n − T_{n−1} (where T_n is the time of the n-th jump) are iid exponential(λ).

Properties:
- 𝔼[N_t] = λt.
- Var(N_t) = λt.
- The compensated process M_t = N_t − λt is a martingale.
- Multiple Poisson processes with the same intensity, viewed as a sum, gives a Poisson process with sum-intensity.

Inhomogeneous Poisson: replace constant λ by a deterministic function λ(t). Then N_t − ∫_0^t λ(s) ds is still a martingale.

### Compound Poisson Process

Let {Y_n} be iid random variables with distribution F (jump-size distribution), independent of a Poisson process N with intensity λ. The **compound Poisson process** is

$$
J_t = \sum_{n=1}^{N_t} Y_n.
$$

Properties:
- 𝔼[J_t] = λ t 𝔼[Y_1] (if 𝔼[|Y_1|] < ∞).
- Var(J_t) = λ t 𝔼[Y_1²].
- Characteristic function: 𝔼[exp(iuJ_t)] = exp(λ t (φ_Y(u) − 1)).

The compensated compound Poisson J_t − λ t 𝔼[Y_1] is a martingale.

### Lévy Processes — General Definition

A **Lévy process** L is a càdlàg (right-continuous with left limits) process with:
1. L_0 = 0.
2. Independent increments.
3. Stationary increments: the law of L_t − L_s depends only on t − s.
4. Stochastic continuity: ℙ(|L_{t+h} − L_t| > ε) → 0 as h → 0.

Brownian motion and the (compound) Poisson process are both Lévy. The class is much larger.

### Lévy–Khintchine Representation

The characteristic function of any Lévy process L has the form

$$
\mathbb{E}[\exp(iu L_t)] = \exp\!\left[ t \left( i u \gamma - \tfrac{1}{2} \sigma^2 u^2 + \int_{\mathbb{R}} \left( e^{iux} - 1 - iux \mathbf{1}_{\{|x| < 1\}} \right) \nu(dx) \right) \right].
$$

The triple (γ, σ², ν) is called the **Lévy triplet**:
- γ ∈ ℝ is the drift (modulo a convention).
- σ² ≥ 0 is the Brownian-motion variance.
- ν is a positive measure on ℝ \ {0} with ∫(1 ∧ x²) ν(dx) < ∞ — the **Lévy measure**.

ν(dx) describes the *intensity of jumps of size dx*. For Brownian motion, ν = 0 (no jumps). For a Poisson process with rate λ and jump size 1, ν = λ δ_1. For a compound Poisson with rate λ and jump-size density f, ν = λ f.

### Lévy–Itô Decomposition

Every Lévy process can be decomposed as

$$
L_t = \gamma t + \sigma W_t + \sum_{s \le t, |\Delta L_s| \ge 1} \Delta L_s + \int_0^t \int_{|x| < 1} x \, (\widetilde N(ds, dx) - \nu(dx) ds),
$$

where W is a Brownian motion, the third term is the sum of large jumps, and the fourth is a compensated sum of small jumps. The decomposition shows: every Lévy process is a deterministic drift, plus a Brownian motion, plus a jump process. The jumps decompose into "large" (finitely many on any interval) and "small" (potentially infinitely many but compensated to be a martingale).

### Examples of Lévy Processes Used in Finance

| Model | Lévy measure | Comments |
|---|---|---|
| Brownian motion | 0 | Continuous |
| Compound Poisson | λ f(x) dx | Finite activity (countable jumps) |
| Variance gamma | f(x) dx with explicit form | Finite variation (paths have FV) |
| CGMY | C \|x\|^{-1-Y} (e^{-G\|x\|} 1_{x>0} + e^{-M\|x\|} 1_{x<0}) | Tempered stable; calibrates well |
| Normal Inverse Gaussian | explicit | Closed-form characteristic function |
| Meixner | explicit | Positive moments; used in interest rates |
| α-stable | C \|x\|^{-1-α} | Infinite activity; infinite variance for α<2 |

The CGMY and NIG models are the workhorses of pure-jump option pricing. They calibrate to the smile remarkably well with only four parameters and have efficient Fourier-pricing implementations (Carr–Madan, Lewis, COS).

### Ito Formula with Jumps

For a process X = X_0 + ∫µ ds + ∫σ dW + J (where J is a pure-jump process with finite activity, jump times T_n and jump sizes Y_n), and f ∈ C^{1,2}, the generalized Ito formula is

$$
f(t, X_t) = f(0, X_0) + \int_0^t \!\left( \partial_t f + \mu_s \partial_x f + \tfrac{1}{2} \sigma_s^2 \partial_{xx} f \right) ds + \int_0^t \sigma_s \partial_x f \, dW_s + \sum_{T_n \le t} \!\left( f(T_n, X_{T_n}) - f(T_n, X_{T_n-}) \right).
$$

The new piece is the sum over jump times: at each jump, f changes by the size of the jump in f, which is *not* the gradient times the jump (that would be the smooth chain-rule term) — it is the actual difference f(X_{T_n}) − f(X_{T_n-}).

For a general Lévy process (possibly with infinite activity), the jump sum becomes an integral against the compensated Poisson random measure plus a compensator. The full formula is

$$
f(t, X_t) = f(0, X_0) + \int_0^t \mathcal{A} f \, ds + \int_0^t \sigma \partial_x f \, dW_s + \int_0^t \int_{\mathbb{R}} \left( f(t, X_{t-} + x) - f(t, X_{t-}) \right) \widetilde N(ds, dx),
$$

where 𝒜 is the **integro-differential generator** combining drift, Brownian, and jump terms, and Ñ is the compensated Poisson measure.

### Pricing under Jump-Diffusion

Merton (1976) introduced the first jump-diffusion pricing model: dS = (µ − λ k) S dt + σ S dW + S (e^Y − 1) dN, where Y ∼ 𝒩(α, β²) is the (log) jump size, N is Poisson with rate λ, and k = e^{α + β²/2} − 1 is the expected jump size. The European call price is a Poisson-weighted sum of Black–Scholes prices:

$$
C_{\text{Merton}} = \sum_{n=0}^\infty \frac{e^{-\lambda' T} (\lambda' T)^n}{n!} C_{\text{BS}}(S_n, K, r_n, \sigma_n, T),
$$

with λ' = λ(1 + k), σ_n² = σ² + nβ²/T, r_n = r − λk + n α/T, S_n = S e^{n α + n β²/2 − r_n T + r T}. The series converges quickly. We will implement this in the calibration section.

```python
# Merton jump-diffusion European call.
import numpy as np
from scipy.stats import norm

def bs_call(S, K, r, sigma, T):
    if T <= 0:
        return max(S - K, 0.0)
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)

def merton_call(S, K, r, sigma, T, lam, alpha, beta, max_n=50):
    k = np.exp(alpha + 0.5*beta**2) - 1
    price = 0.0
    for n in range(max_n):
        sigma_n = np.sqrt(sigma**2 + n*beta**2/T)
        r_n = r - lam*k + n*(alpha + 0.5*beta**2)/T
        weight = np.exp(-lam*(1+k)*T) * (lam*(1+k)*T)**n / np.math.factorial(n)
        price += weight * bs_call(S, K, r_n, sigma_n, T)
    return price

S, K, r, T = 100.0, 100.0, 0.04, 1.0
sigma, lam, alpha, beta = 0.20, 0.5, -0.05, 0.10
print(f"Merton price = {merton_call(S, K, r, sigma, T, lam, alpha, beta):.4f}")
print(f"BS price     = {bs_call(S, K, r, sigma, T):.4f}")
```

### Reality Check — How Many Jumps Are Real?

Empirical studies suggest that for major equity indices, jumps account for roughly 10–25% of total quadratic variation, and most of the "fat tails" in observed returns are due to jumps. For individual stocks, especially around earnings, the jump component can dominate. For FX, jumps are smaller but coordinated with central-bank announcements. For crypto, jumps are extreme and frequent — a Lévy model is barely sufficient.

Distinguishing a true jump from a sequence of large continuous increments is statistically hard at any finite frequency. Bipower variation, threshold methods, and Lee–Mykland tests are the standard tools. These are covered in document 211.

---

## Part VII — Stochastic Volatility

Constant volatility is empirically wrong. Three observations drive the entire stochastic-volatility (SV) industry:

1. **Volatility clustering**: large absolute returns are followed by large absolute returns. Volatility itself is autocorrelated.
2. **Leverage effect**: negative returns are associated with subsequent volatility increases, more strongly than positive returns.
3. **Smile/skew**: option-implied volatilities depend on strike and maturity in ways inconsistent with constant vol.

The standard fix: model volatility itself as a stochastic process. We give two canonical models.

### The Heston Model

Already introduced. We expand here on the calibration and the closed form.

The Heston characteristic function (under ℚ) is

$$
\phi_T(u) = \mathbb{E}^{\mathbb{Q}}[e^{iu \log S_T}] = e^{C(T, u) + D(T, u) v_0 + iu \log S_0},
$$

with C, D given by

$$
D(T, u) = \frac{\kappa - \rho \sigma_v iu - d}{\sigma_v^2} \cdot \frac{1 - e^{-dT}}{1 - g e^{-dT}},
$$
$$
C(T, u) = (r) iu T + \frac{\kappa \theta}{\sigma_v^2}\!\left[ (\kappa - \rho \sigma_v iu - d) T - 2 \log\!\frac{1 - g e^{-dT}}{1 - g} \right],
$$

where d = √((ρσ_v iu − κ)² + σ_v²(iu + u²)) and g = (κ − ρσ_v iu − d)/(κ − ρσ_v iu + d). Care is needed with the branch of d to avoid numerical instabilities (the so-called Heston "trap" — Albrecher et al. 2007). The trap-free formulation uses g̃ = 1/g and the negated d.

Once we have φ_T, European call prices come from Carr–Madan or the Lewis FFT:

$$
C(K) = e^{-rT} \frac{1}{2\pi} \int_{-\infty}^{\infty} e^{-iuk} \frac{\phi_T(u - i) - 1}{iu(1 + iu)} du,
$$

with k = log K. Numerically, one truncates the integral and uses an adaptive quadrature (FFT for speed across many strikes).

```python
# Heston characteristic function and European call via Lewis-style integration.
import numpy as np
from scipy.integrate import quad

def heston_cf(u, T, S0, r, kappa, theta, sigma_v, rho, v0):
    """Trap-free Heston char. function under risk-neutral measure for log S_T."""
    iu = 1j*u
    d = np.sqrt((rho*sigma_v*iu - kappa)**2 + sigma_v**2*(iu + u**2))
    g_ = (kappa - rho*sigma_v*iu - d) / (kappa - rho*sigma_v*iu + d)
    G = (1 - g_*np.exp(-d*T)) / (1 - g_)
    C = r*iu*T + (kappa*theta/sigma_v**2)*((kappa - rho*sigma_v*iu - d)*T - 2*np.log(G))
    D = ((kappa - rho*sigma_v*iu - d)/sigma_v**2)*((1 - np.exp(-d*T))/(1 - g_*np.exp(-d*T)))
    return np.exp(C + D*v0 + iu*np.log(S0))

def heston_call(S0, K, T, r, kappa, theta, sigma_v, rho, v0):
    def integrand(u):
        phi = heston_cf(u - 1j, T, S0, r, kappa, theta, sigma_v, rho, v0)
        return (np.exp(-1j*u*np.log(K)) * (phi - 1) / (1j*u*(1 + 1j*u))).real
    val, _ = quad(integrand, 1e-10, 200, limit=400)
    return np.exp(-r*T) * val / np.pi

S0, K, T, r = 100.0, 100.0, 1.0, 0.03
kappa, theta, sigma_v, rho, v0 = 2.0, 0.04, 0.5, -0.7, 0.04
print(f"Heston call = {heston_call(S0, K, T, r, kappa, theta, sigma_v, rho, v0):.4f}")
```

### The SABR Model

SABR (Hagan, Kumar, Lesniewski, Woodward, 2002): dF = α F^β dW^1, dα = ν α dW^2, d⟨W^1, W^2⟩ = ρ dt. Parameters β ∈ [0, 1] controls the at-the-money skew shape, α is the initial volatility, ν is vol-of-vol, ρ is correlation. The SABR model is the de-facto standard for FX and interest-rate options.

The famous "Hagan asymptotic formula" for implied vol:

$$
\sigma_{\text{impl}} \approx \frac{\alpha}{(FK)^{(1-\beta)/2} \big[1 + \tfrac{(1-\beta)^2}{24} (\log F/K)^2 + \tfrac{(1-\beta)^4}{1920} (\log F/K)^4 \big]} \cdot \frac{z}{\chi(z)} \cdot \big[1 + \cdots \big],
$$

with z = (ν / α)(FK)^{(1-β)/2} log(F/K) and χ(z) = log((√(1 − 2ρz + z²) − ρ + z)/(1 − ρ)). The "..." includes a small-time correction term that is critical for accuracy at long maturities. The formula has been criticized for accuracy at low strikes (the so-called "negative density" issue); modern implementations use a combination of the asymptotic formula at the wings and a numerical PDE solver near at-the-money.

### Rough Volatility — rBergomi and Friends

Empirical observation (Gatheral, Jaisson, Rosenbaum 2014): log realized variance has Hurst exponent ~0.1 — much rougher than Brownian motion. This motivates **rough volatility** models where the variance process is driven by a fractional Brownian motion with Hurst H < ½.

The rBergomi model: σ²_t = ξ_0(t) exp(η W̃_t^H − η² t^{2H}/2), where W̃^H is a Volterra-type fractional process with kernel K(t, s) ∼ (t − s)^{H − ½}. Prices are computed via Monte Carlo or via a perturbative expansion. Calibration to short-dated SPX smiles is dramatically better than for classical Heston.

The trade-off: rough vol models have non-Markov dynamics (the variance at time t depends on the full history of the driving process), so PDE methods are not directly available, and Monte Carlo is the workhorse. Hierarchical kernel approximations and regression-based methods are active research areas.

### Local Volatility and Local-Stochastic Vol

**Dupire's local volatility**: given a complete set of European option prices C(K, T), the local volatility σ_loc(K, T) is the unique deterministic function of (S, t) such that the SDE dS = µS dt + σ_loc(S, t) S dW reproduces all option prices. The formula:

$$
\sigma_{\text{loc}}^2(K, T) = \frac{\partial_T C + (r - q) K \partial_K C + qC}{\tfrac{1}{2} K^2 \partial_{KK} C}.
$$

Local volatility *exactly fits* the smile but has counterfactual dynamics (the smile flattens too fast as time passes). **Local-stochastic vol** (LSV) blends: dS = µS dt + L(S, t) √v S dW^1, dv = κ(θ − v) dt + σ_v √v dW^2, where L is a leverage function chosen to match the market smile while v provides realistic forward dynamics. LSV is the production-grade equity-derivatives model in major banks.

Document 202 covers calibration and a complete code implementation.

### Reality Check — Smile Calibration vs Hedging

A model that perfectly fits today's option prices may hedge poorly. The reason: the *dynamics* of the smile under the model may not match the dynamics of the market smile. Local volatility is the canonical example — it fits today's prices exactly but predicts that the smile flattens deterministically as the underlying moves, which is empirically false (the smile mostly moves with the spot rather than flattening).

The right metric for choosing a model is *hedging error*, not calibration error. Measured over many days of real trading, sticky-strike, sticky-delta, and sticky-vol assumptions all have different empirical hedging performance, and the best model is the one whose Greeks are most stable across smile shifts. This is the operational version of the "model risk" problem, and it is one reason production desks run multiple models in parallel and aggregate hedges across them.

---

## Part VIII — Numerical Methods

We rarely have closed-form solutions. Numerical methods — Monte Carlo, finite-difference PDE, Fourier inversion — are the practical face of continuous-time finance.

### Euler–Maruyama Scheme

For dX = µ(X) dt + σ(X) dW, the **Euler–Maruyama** scheme on a grid 0 = t_0 < t_1 < … < t_N = T:

$$
\widehat X_{n+1} = \widehat X_n + \mu(\widehat X_n) \Delta t + \sigma(\widehat X_n) \Delta W_n,
$$

with ΔW_n ∼ 𝒩(0, Δt) iid. Strong convergence order 1/2: 𝔼[|X_T − X̂_T|²]^{1/2} ≤ C Δt^{1/2}. Weak convergence order 1: |𝔼[f(X_T)] − 𝔼[f(X̂_T)]| ≤ C Δt for sufficiently smooth f.

Strong vs weak convergence: strong measures pathwise error; weak measures error in distribution. For pricing (which is computing 𝔼[f(X_T)]), weak convergence is enough — you can use a coarser grid to get the same accuracy. For path-dependent functionals (Asian options, lookbacks, barrier options), strong convergence matters.

### Milstein Scheme

Adds a second-order term:

$$
\widehat X_{n+1} = \widehat X_n + \mu \Delta t + \sigma \Delta W + \tfrac{1}{2} \sigma \sigma' \big( (\Delta W)^2 - \Delta t \big).
$$

Strong convergence order 1; weak convergence order 1. The σσ'((ΔW)²−Δt) term comes from the Ito-Taylor expansion and accounts for the curvature of the diffusion coefficient. For multidimensional SDEs with non-commutative noise, the Milstein scheme requires Lévy area integrals — typically too expensive to use in practice; one uses Runge–Kutta-style schemes instead.

### Higher-Order Schemes

For weak convergence, higher-order schemes (order 2 weak, order 3 weak) exist but are more complex. The trade-off is usually not worth it for most applied problems; bias dominates in low-dimensional Monte Carlo and variance dominates in high-dimensional, so reducing variance (multilevel MC, control variates) is often more impactful than reducing bias by half a order.

### Variance Reduction

| Technique | What it does | When to use |
|---|---|---|
| Antithetic variates | Use −W as well as +W | Always; cheap and almost-free variance reduction for symmetric integrands |
| Control variates | Subtract a cheap proxy with known mean | Asian options against geometric-Asian closed form; basket options against Vandersanden bounds |
| Importance sampling | Tilt the sampling distribution | Deep OTM options; exit-time problems |
| Stratified sampling | Sample uniformly across strata | Latin hypercube; quasi-MC sequences |
| Quasi-MC | Low-discrepancy sequences | Smooth-payoff problems; high-dimensional pricing |
| Multilevel MC | Combine coarse and fine grids | Path-dependent options with expensive simulation |

The Multilevel Monte Carlo of Giles (2008) is the standout: by combining estimates at different grid resolutions, you can achieve target RMSE ε with cost O(ε^{-2}), versus O(ε^{-3}) for naive MC. The trick is that the *difference* between coarse and fine estimates has small variance even though each individual estimate has the variance of the original problem.

```python
# Antithetic + control variate for an Asian call.
# We use the geometric Asian (closed form) as control for the arithmetic Asian (target).
import numpy as np
from scipy.stats import norm

def geometric_asian_call(S0, K, r, sigma, T, M):
    sigma_g = sigma * np.sqrt((2*M + 1) / (6*(M + 1)))
    mu_g = 0.5 * (r - 0.5*sigma**2 + sigma_g**2)
    d1 = (np.log(S0/K) + (mu_g + 0.5*sigma_g**2)*T) / (sigma_g*np.sqrt(T))
    d2 = d1 - sigma_g*np.sqrt(T)
    return np.exp(-r*T) * (S0*np.exp(mu_g*T)*norm.cdf(d1) - K*norm.cdf(d2))

def asian_call_mc(S0, K, r, sigma, T, M, n_paths):
    dt = T/M
    np.random.seed(42)
    Z = np.random.normal(size=(n_paths//2, M))
    Z = np.vstack([Z, -Z])  # antithetic
    paths = np.full((n_paths, M+1), S0)
    for j in range(M):
        paths[:, j+1] = paths[:, j] * np.exp((r - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*Z[:, j])
    arith = np.maximum(paths[:, 1:].mean(axis=1) - K, 0)
    geom = np.maximum(np.exp(np.log(paths[:, 1:]).mean(axis=1)) - K, 0)
    cv_target = geometric_asian_call(S0, K, r, sigma, T, M)
    # Optimal CV coefficient
    b = np.cov(arith, geom)[0, 1] / np.var(geom)
    cv_estimate = arith - b*(geom - np.exp(r*T)*cv_target)
    return np.exp(-r*T)*np.mean(cv_estimate), np.exp(-r*T)*np.std(cv_estimate)/np.sqrt(n_paths)

S0, K, r, sigma, T, M, n = 100, 100, 0.05, 0.20, 1.0, 50, 50_000
price, se = asian_call_mc(S0, K, r, sigma, T, M, n)
print(f"Arithmetic Asian call: {price:.4f} +/- {1.96*se:.4f} (95% CI)")
```

### Finite-Difference PDE

For pricing equations like the Black–Scholes PDE,

$$
\partial_t V + \tfrac{1}{2} \sigma^2 S^2 \partial_{SS} V + r S \partial_S V - r V = 0, \qquad V(T, S) = h(S),
$$

discretize on a grid in (t, S). Three popular schemes:

- **Explicit**: V_{n+1} given V_n by simple combination. Fast per step but unstable for large Δt — CFL-like condition Δt ≤ Δs²/(σ²S²_max) bounds the time step.
- **Implicit (backward Euler)**: solves a linear system at each step. Unconditionally stable. First-order accurate in time.
- **Crank–Nicolson**: average of explicit and implicit. Unconditionally stable, second-order accurate. Default for Black–Scholes-style problems.

For American options, add a max(V, h) projection at each time step (LCP formulation; Brennan–Schwartz for monotone schemes).

For Heston, the PDE is two-dimensional in (S, v) and requires careful boundary treatment (especially at v = 0). ADI splitting (Hundsdorfer–Verwer, Craig–Sneyd) reduces the cost from O(N²M) to O(NM log M) per step.

### Fourier Methods

When the characteristic function of log S_T under ℚ is known (Heston, Merton, CGMY, NIG, Variance Gamma), **Fourier transform pricing** is faster than PDE for vanilla options. The two main variants:

- **Carr–Madan**: damped Fourier inversion of the call price.
- **Lewis**: integration of (φ − 1)/(iu(1 + iu)) against the characteristic function.
- **COS method (Fang–Oosterlee)**: cosine-series expansion. Very efficient and easy to implement.

For path-dependent options under Lévy models, Hilbert-transform methods and Wiener–Hopf factorization give efficient algorithms.

### Reality Check — Choose Your Numerical Tool

| Problem | Tool of choice |
|---|---|
| European vanilla, Heston/Merton/CGMY | Fourier (COS method) |
| European vanilla, GBM | Closed form |
| American vanilla | Crank–Nicolson PDE with LCP, or LSM Monte Carlo |
| Path-dependent (Asian, lookback, barrier) | Monte Carlo, possibly with control variates |
| High-dimensional basket | Quasi-MC or LSM |
| Calibration | Use the fastest pricer compatible with the model |
| Exotic, model-uncertain | Monte Carlo for flexibility |

Production-grade systems blend these: vanilla calibration via Fourier, exotic pricing via Monte Carlo, sensitivity computation via adjoint or pathwise methods, and validation via cross-checks among at least two methods.

---

## Pricing European, American, and Path-Dependent Options

We now apply the machinery to specific products. The goal is to give *complete* pricing recipes — code-ready, with all the corner cases.

### European Options

A European option pays h(S_T) at maturity T. The price is V_0 = 𝔼^ℚ[e^{-rT} h(S_T)]. Under GBM, this gives Black–Scholes for h(s) = (s − K)^+ (call) and the symmetric formula for puts. For other models, we use Fourier methods or Monte Carlo.

The Greeks are the partial derivatives of V_0 with respect to model parameters: Delta = ∂V/∂S, Gamma = ∂²V/∂S², Vega = ∂V/∂σ, Theta = ∂V/∂t, Rho = ∂V/∂r. They have closed forms in Black–Scholes and semi-closed forms (via the characteristic function) in Heston, Merton, etc.

### American Options

American options can be exercised at any time τ ≤ T. The price is

$$
V_0 = \sup_\tau \mathbb{E}^{\mathbb{Q}}\!\left[ e^{-r\tau} h(S_\tau) \right],
$$

where the sup is over all stopping times τ. The optimal exercise boundary partitions the (t, S) plane into a continuation region (where it is better to hold) and a stopping region (where it is better to exercise).

Two main numerical approaches:

- **PDE with LCP**: V satisfies a linear complementarity problem (V ≥ h, ∂_t V + 𝓛 V − rV ≤ 0, with equality where V > h). Crank–Nicolson with the Brennan–Schwartz algorithm or PSOR projection solves this efficiently.
- **Longstaff–Schwartz Monte Carlo (LSM)**: regress the continuation value on a basis of functions of S_t (typically polynomials), and exercise where intrinsic value > regressed continuation. Works for high-dimensional underlyings.

```python
# Longstaff-Schwartz American put pricer.
import numpy as np

def lsm_american_put(S0, K, r, sigma, T, n_steps=50, n_paths=20_000, basis_deg=3):
    np.random.seed(7)
    dt = T / n_steps
    Z = np.random.normal(size=(n_paths, n_steps))
    paths = np.zeros((n_paths, n_steps + 1))
    paths[:, 0] = S0
    for j in range(n_steps):
        paths[:, j+1] = paths[:, j] * np.exp((r - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*Z[:, j])
    payoff = np.maximum(K - paths, 0)
    V = payoff[:, -1].copy()
    for j in range(n_steps - 1, 0, -1):
        itm = payoff[:, j] > 0
        if itm.sum() < 4:
            V *= np.exp(-r*dt)
            continue
        X = paths[itm, j]
        Y = V[itm] * np.exp(-r*dt)
        coeffs = np.polyfit(X, Y, basis_deg)
        cont = np.polyval(coeffs, X)
        exercise = payoff[itm, j] > cont
        V[itm] = np.where(exercise, payoff[itm, j], V[itm]*np.exp(-r*dt))
        V[~itm] *= np.exp(-r*dt)
    return np.exp(-r*dt) * V.mean()

print(f"American put = {lsm_american_put(100, 100, 0.05, 0.20, 1.0):.4f}")
```

LSM is a workhorse but has subtleties: choice of basis functions matters, in-the-money filter is required to avoid basis-function pathology, and bias can be reduced via the dual upper bound (Andersen–Broadie 2004) or by sub-simulation.

### Path-Dependent: Barrier, Asian, Lookback

**Barrier options**: knock-in (activates if barrier hit) or knock-out (deactivates if barrier hit). Closed-form prices exist for vanilla GBM (using the reflection principle); for Heston and friends, use PDE or MC. Care is needed in MC because of *barrier-crossing bias* — a path that does not cross the barrier on the discrete grid may still cross between grid points; the standard fix is a Brownian-bridge correction.

**Asian options**: payoff depends on the average price A = (1/T) ∫_0^T S_t dt or A = (1/M) ∑ S_{t_i}. Asian options are smoother than vanillas (averaging reduces variance), and pricing is cleaner. For arithmetic Asian under GBM, no closed form; geometric Asian has a closed form. Standard MC + control variate (geometric vs arithmetic) gives 10–100× variance reduction.

**Lookback options**: payoff depends on max or min over the path. Closed form exists for fixed-strike lookbacks under GBM. For floating-strike or Heston, use MC with continuous-monitoring corrections.

### Reality Check — Path Discretization Bias

Monte Carlo pricing of path-dependent options has bias from the discrete time grid. For barrier options, this bias is severe — it typically overestimates the value of knock-in options and underestimates the value of knock-outs. The Brownian-bridge correction (compute the conditional probability of crossing between consecutive grid points and adjust accordingly) is essential. For Asian options, the bias is smaller and goes as O(Δt) for arithmetic averages.

Always benchmark MC prices against PDE prices on a small case before trusting the MC. The "shape" of the bias (e.g., always positive for knock-outs) is a useful diagnostic.

---

## Greeks — Pathwise, Likelihood, and Malliavin Methods

Computing Greeks accurately is as important as computing prices. Three main approaches.

### Bumping (Finite Difference)

V'(S_0) ≈ (V(S_0 + h) − V(S_0 − h))/(2h). Simple and works for everything, but has bias (O(h²)) and variance (O(1/h²) when V is computed by MC). The total RMSE is minimized at h ∼ N^{-1/4}, giving total error O(N^{-1/4}). Slow.

### Pathwise Method

Differentiate the simulated paths with respect to the parameter, then average. For dS = µ S dt + σ S dW, ∂S_T/∂S_0 = S_T/S_0. So Delta of a call = e^{-rT} 𝔼^ℚ[1_{S_T > K} · S_T / S_0]. Accurate when the payoff is differentiable; fails for digital options and barriers.

### Likelihood-Ratio (Score) Method

Differentiate the *density* of S_T with respect to the parameter, weighting the unchanged payoff. For Black–Scholes, the score function with respect to S_0 is (W_T − (r − σ²/2)T/σ)/σS_0... and Delta = 𝔼^ℚ[e^{-rT} h(S_T) · score]. Works for non-smooth payoffs; high variance because the score function is noisy.

### Malliavin Calculus

A more sophisticated framework that gives weights for any Greek of any payoff under quite general conditions. The weights are computed using the Malliavin derivative (a derivative on path space) and can be expressed as integrals against the driving Brownian motion. For an asset following GBM, the Delta weight is W_T / (S_0 σ T), giving Delta = 𝔼^ℚ[e^{-rT} h(S_T) W_T / (S_0 σ T)]. This is the "Malliavin Delta" — accurate for any payoff including digitals.

For more general models, Malliavin weights involve the Skorokhod integral and can be computed numerically. The Fournié–Lasry–Lebuchoux–Lions–Touzi paper (1999) is the classic reference.

### Adjoint Methods (AAD)

For a model with many parameters, Greek computation by AAD (adjoint algorithmic differentiation) computes all sensitivities at the cost of a *constant* (typically 4–10×) multiple of one forward price computation. This is transformative for calibration and risk: the Hessian of a calibration loss is computable in linear time in the number of parameters. Production systems (Quantlib, MFE, custom in-house libraries) all support AAD.

```python
# Pathwise Delta of a Black-Scholes call.
import numpy as np

def pathwise_delta(S0, K, r, sigma, T, n_paths):
    np.random.seed(11)
    Z = np.random.normal(size=n_paths)
    ST = S0 * np.exp((r - 0.5*sigma**2)*T + sigma*np.sqrt(T)*Z)
    delta_payoff = np.where(ST > K, ST/S0, 0)  # pathwise derivative of (ST-K)^+
    return np.exp(-r*T) * delta_payoff.mean()

print(f"Pathwise Delta = {pathwise_delta(100, 100, 0.05, 0.20, 1.0, 100_000):.4f}")
```

### Reality Check — Greek Stability

The right Greek is not just a number; it is something you trade against. A noisy Vega makes you re-hedge volatility excessively, paying spread. A biased Gamma makes you mis-hedge curvature, paying convexity costs. On illiquid markets, the *trade-off between bias and noise* in Greek estimation is the central problem. Modern desks use a blend of methods: AAD for stable Greeks of stable models, Malliavin or pathwise for non-trivial payoffs, and bumping only as a benchmark.

---

## Calibration to Market Data

A model is useless until calibrated. Calibration means: choose the parameters of the model so that model prices match observed market prices.

### Calibration Workflow

1. Pick a model family (Heston, SABR, rBergomi, Merton).
2. Choose a calibration grid: for each maturity T_i and strike K_j, observe market implied vol σ_{ij}^{mkt}.
3. Define a loss function: L(θ) = ∑_{ij} w_{ij} (σ_{ij}^{model}(θ) − σ_{ij}^{mkt})².
4. Optimize over θ using a solver (Levenberg–Marquardt, BFGS, differential evolution).
5. Validate out-of-sample on next-day prices.

### Robust Calibration

Naive least-squares calibration is unstable. Best practice:

- Use *implied vol* targets, not price targets — vol is more uniform across strikes.
- Weight by Vega — at-the-money options have higher information content than wings.
- Use a regularizer — penalize deviations from yesterday's calibrated parameters.
- Use multi-start optimization to escape local minima — Heston has many.
- Validate on out-of-sample data — the model that fits today's prices best may not be the best forecaster.

### Calibration of Heston

Parameters: (κ, θ, σ_v, ρ, v_0). Five parameters fit 50–500 vols. The fit is usually excellent for ATM and ITM, but can struggle in the wings (especially deep OTM puts on equity indices, where the smile is steeper than Heston can produce — this is what motivates jump-diffusion or rough vol).

```python
# Heston calibration to a synthetic SPX-style vol surface.
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

def bs_iv(price, S0, K, r, T, opt='call', tol=1e-6, max_iter=100):
    """Newton's method to invert Black-Scholes for IV."""
    sigma = 0.20
    for _ in range(max_iter):
        d1 = (np.log(S0/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        bs = S0*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
        vega = S0*norm.pdf(d1)*np.sqrt(T)
        diff = bs - price
        if abs(diff) < tol:
            return sigma
        sigma -= diff / vega
        if sigma <= 0:
            return np.nan
    return sigma

# Synthesize market vols from "true" Heston parameters.
S0, r = 100.0, 0.03
true = (kappa, theta, sigma_v, rho, v0) = (2.0, 0.04, 0.5, -0.7, 0.04)
strikes = np.array([80, 90, 100, 110, 120])
maturities = np.array([0.25, 0.5, 1.0])
mkt_vols = np.zeros((len(maturities), len(strikes)))
for i, T in enumerate(maturities):
    for j, K in enumerate(strikes):
        price = heston_call(S0, K, T, r, *true)
        mkt_vols[i, j] = bs_iv(price, S0, K, r, T)

def calibration_loss(theta):
    k, t, s, rh, v = theta
    if min(k, t, s, v) <= 0 or abs(rh) > 0.99:
        return 1e10
    err = 0.0
    for i, T in enumerate(maturities):
        for j, K in enumerate(strikes):
            price = heston_call(S0, K, T, r, k, t, s, rh, v)
            iv = bs_iv(price, S0, K, r, T)
            if not np.isnan(iv):
                err += (iv - mkt_vols[i, j])**2
    return err

x0 = (1.0, 0.05, 0.4, -0.5, 0.05)
res = minimize(calibration_loss, x0, method='Nelder-Mead', options={'maxiter': 1000, 'xatol': 1e-6})
print(f"True params: {true}")
print(f"Calibrated:  {tuple(round(x, 4) for x in res.x)}")
```

### Reality Check — Calibration Is a Daily Job

In production, calibration runs every morning before the market open and at intervals throughout the day. Parameter drift is normal and reflects real changes in the supply-demand balance for vol. The challenge is distinguishing genuine drift from numerical artifacts (e.g., a calibration that lands in a different local minimum after a small data perturbation). Diagnostic tools include parameter trajectory plots, calibration-quality metrics (e.g., MSE in vol, max error), and sensitivity of calibrated parameters to small data perturbations.

---

## Real Trading Considerations: From Theory to Live PnL

Having built the theoretical machinery, we close with the gap between theory and live trading.

### Hedging Errors

Black–Scholes assumes continuous rebalancing. In practice, you rebalance discretely (every minute, every hour, every day). The hedging error has variance ∝ Δt over each rebalance interval. Cumulative hedging error has variance ∝ Δt T / Δt = T at the risk-of-each-step level. The bigger problem is that the Black–Scholes Delta is computed under the assumption that the market is in the BS world — if real volatility differs, the hedge is off, even continuously.

### Volatility Risk Premium

Implied vol systematically exceeds realized vol on equity indices, by ~3–5 vol points on average over decades. This gap is the *volatility risk premium*, and it is the source of most short-vol strategies (covered calls, iron condors, variance swaps short). Document 27 covers the empirical patterns and their failure modes (e.g., 2018 vol blowup, 2020 COVID).

### Smile Dynamics

Models can fit today's smile but predict the wrong dynamics. Sticky-strike (the IV at each strike is constant as spot moves) and sticky-delta (the IV at each moneyness is constant) are two extremes; reality is in between and varies over time. Hedging Delta-Vega-Gamma under the wrong dynamics regime leads to systematic P&L drift.

### Transaction Costs

Every trade pays the bid-ask spread plus market impact. For a hedger, this caps how often you can rebalance — too often, and you pay too much spread; too rarely, and the hedge slips. The optimal rebalancing frequency under quadratic costs is when the marginal cost of rebalancing equals the marginal hedging error, which gives *no-trade regions* around the model Delta. Document 208 (Optimal Execution Theory) has the full derivation.

### Model Risk

You are always wrong. The model parameters are estimated with error, the model itself is an approximation, and the market may transition to a regime where the model is qualitatively wrong (e.g., the move from continuous to jump-dominated in COVID). The discipline:

- Maintain *multiple* calibrated models in production. Hedge using the union of their Greeks.
- Stress-test daily against extreme scenarios (vol of vol, jump arrival, correlation shifts).
- Set risk limits in dollar terms, not in model-parameter terms — model parameters can be wrong even when prices are right.
- Have a *kill switch* — a halt condition that flattens the book if model behavior diverges from expectations by more than a fixed dollar amount.

The combination of all these safeguards is what turns the elegant continuous-time theory into a P&L-generating, capital-preserving operation.

---

## Reference Tables and Annotated Bibliography

### Quick-Reference Sheet

| Concept | Symbol | Black–Scholes value |
|---|---|---|
| Underlying | S | dS = rS dt + σS dW under ℚ |
| Discount factor | D(t, T) | e^{−r(T−t)} |
| Forward | F(t, T) | S e^{(r−q)(T−t)} |
| Call price | C | S Φ(d_+) − K e^{−rT} Φ(d_−) |
| Put price | P | K e^{−rT} Φ(−d_−) − S Φ(−d_+) |
| Delta of call | Δ_C | Φ(d_+) |
| Delta of put | Δ_P | Φ(d_+) − 1 |
| Gamma | Γ | φ(d_+) / (S σ √T) |
| Vega | 𝒱 | S φ(d_+) √T |
| Theta of call | Θ_C | −S φ(d_+) σ / (2√T) − r K e^{−rT} Φ(d_−) |
| Rho of call | ρ_C | K T e^{−rT} Φ(d_−) |

### Bibliography (Annotated)

- **Karatzas, I. and Shreve, S. (1991), *Brownian Motion and Stochastic Calculus*, Springer.** The canonical graduate-level treatment. Heavy on rigor, light on finance.
- **Shreve, S. (2004), *Stochastic Calculus for Finance II: Continuous-Time Models*, Springer.** The same author for finance students. Excellent chapters on Girsanov and risk-neutral pricing. Recommend as primary text for self-study.
- **Protter, P. (2005), *Stochastic Integration and Differential Equations* (2nd ed.), Springer.** The reference for rigorous treatment of stochastic integration, including jumps. Not a first textbook; a second one.
- **Cont, R. and Tankov, P. (2004), *Financial Modelling with Jump Processes*, Chapman & Hall.** The reference for Lévy-process pricing. Code-heavy and practical.
- **Gatheral, J. (2006), *The Volatility Surface*, Wiley.** Best practitioner-oriented treatment of stochastic vol and local vol. Required reading for vol traders.
- **Bergomi, L. (2016), *Stochastic Volatility Modeling*, Chapman & Hall.** The current state-of-the-art reference for production stochastic vol. Heavy emphasis on hedging dynamics and forward smile.
- **Fouque, J., Papanicolaou, G., and Sircar, R. (2000), *Derivatives in Financial Markets with Stochastic Volatility*, Cambridge University Press.** Asymptotic methods for fast-varying vol. Useful for intuition.
- **Glasserman, P. (2004), *Monte Carlo Methods in Financial Engineering*, Springer.** The Monte Carlo bible for finance. Multilevel MC, variance reduction, Greeks.
- **Hagan, P., Kumar, D., Lesniewski, A. and Woodward, D. (2002), "Managing Smile Risk", Wilmott Magazine, September: 84–108.** The original SABR paper.
- **Heston, S. (1993), "A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options", *Review of Financial Studies* 6(2): 327–343.** The original Heston paper.
- **Albrecher, H., Mayer, P., Schoutens, W., and Tistaert, J. (2007), "The Little Heston Trap", Wilmott Magazine, January: 83–92.** Cleanest exposition of how to avoid the numerical instability in Heston pricing.
- **Gatheral, J., Jaisson, T., and Rosenbaum, M. (2018), "Volatility Is Rough", *Quantitative Finance* 18(6): 933–949.** The empirical foundation of rough-volatility modeling.
- **Bayer, C., Friz, P., and Gatheral, J. (2016), "Pricing Under Rough Volatility", *Quantitative Finance* 16(6): 887–904.** First efficient simulation of rBergomi.
- **Carr, P. and Madan, D. (1999), "Option Valuation Using the Fast Fourier Transform", *Journal of Computational Finance* 2(4): 61–73.** The standard reference for FFT-based pricing.
- **Lewis, A. (2001), "A Simple Option Formula for General Jump-Diffusion and Other Exponential Lévy Processes", SSRN.** Cleanest formulation of Fourier pricing.
- **Fang, F. and Oosterlee, C. W. (2008), "A Novel Pricing Method for European Options Based on Fourier-Cosine Series Expansions", *SIAM Journal on Scientific Computing* 31(2): 826–848.** The COS method.
- **Andersen, L. and Piterbarg, V. (2010), *Interest Rate Modeling*, Atlantic Financial Press.** Three volumes. The encyclopedia of fixed-income derivatives. Essential for rates trading.
- **Avellaneda, M. and Stoikov, S. (2008), "High-Frequency Trading in a Limit Order Book", *Quantitative Finance* 8(3): 217–224.** The market-making model. Linked to document 29.
- **Almgren, R. and Chriss, N. (2000), "Optimal Execution of Portfolio Transactions", *Journal of Risk* 3(2): 5–39.** The execution-cost model. Linked to document 208.

### Cross-References Within This Library

- Document 201 — Market Microstructure Theory: theoretical foundations of order books, Kyle, Glosten–Milgrom.
- Document 202 — Volatility Surface Modeling: complete Heston, SABR, LSV, rough-vol calibration.
- Document 206 — Extreme Value Theory: tail distributions for risk modeling.
- Document 207 — Copulas and Multivariate Dependence: dependence structures beyond correlation.
- Document 208 — Optimal Execution Theory: Almgren–Chriss and beyond.
- Document 211 — Backtesting Statistical Rigor: avoiding overfit.
- Document 213 — Fixed Income Quant Methods: HJM, LMM, MBS.

---

## Coda: Why This All Matters

Continuous-time finance is sometimes presented as if it were a clever pile of mathematical notation that practitioners must endure to reach trading insights. That framing has it backwards. The continuous-time framework is the *only* setting in which the central tradeoffs of trading become fully visible: the cost of rebalancing, the value of optionality, the price of risk premia, the dynamics of information.

The alternative — discrete time only, intuition only, no measure-theoretic discipline — leaves you guessing about the size and direction of every effect. You can see, for example, that buying volatility is expensive because realized volatility tends to be lower than implied; but you cannot say *how much* is fair to overpay, or *why* it varies with the steepness of the smile, or *when* the relationship breaks. The continuous-time framework gives you the formulas.

This document is a toolkit. The toolkit is large because the questions are large. Each section's *reality check* is included precisely to remind you that the formulas are not the world — they are a model of the world, and they fail in places. The discipline is to know where they fail and to use them only where they succeed.

A trader who has internalized this toolkit can read any major derivatives paper, calibrate any major model, and assess any major risk — not because the math is automatic, but because the conceptual apparatus is durable. Markets change; the toolkit barely does. That is its value.

The remaining 19 documents in this expansion build on what we have here. Microstructure (201) tells you about the *order book* in which all this trading happens. Volatility surface modeling (202) extends Part VII into a complete pricing pipeline. Extreme value theory (206) addresses the tails that the Brownian framework downplays. Optimal execution (208) closes the gap between theoretical "Delta" and live trading orders. Each subsequent document is a deeper dive into one of the *reality checks* you read above.

We continue, in document 201, with market microstructure theory.

---

*End of document 200. Version 1.0. ~5,800 lines as written; the document continues across follow-up turns to reach the full 12,000-line target via additional worked examples, deeper case studies, more code, and extended bibliography in subsequent revisions.*
