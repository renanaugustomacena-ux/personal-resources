# 207 — Copulas and Multivariate Dependence

> Cross-asset dependence beyond linear correlation. Covers Sklar's theorem, Gaussian/Student-t/Archimedean copulas, vine copulas, dynamic copulas, tail dependence, calibration, goodness-of-fit, and applications to portfolio risk, pairs trading, credit derivatives, and crypto cross-asset modeling. Self-contained beyond document 200.

---

## Table of Contents

1. [Why Copulas](#why-copulas)
2. [Sklar's Theorem](#sklar)
3. [Copula Definition and Properties](#properties)
4. [Fréchet–Hoeffding Bounds](#bounds)
5. [Gaussian Copula](#gaussian-copula)
6. [Student-t Copula](#t-copula)
7. [Archimedean Copulas — Clayton, Gumbel, Frank](#archimedean)
8. [Other Bivariate Copulas](#other-bivariate)
9. [Vine Copulas — C-Vine, D-Vine, R-Vine](#vine)
10. [Empirical and Non-Parametric Copulas](#empirical-copulas)
11. [Estimation Methods](#estimation)
12. [Goodness-of-Fit Testing](#gof)
13. [Tail Dependence](#tail-dependence)
14. [Conditional and Dynamic Copulas](#dynamic)
15. [Pseudo-Observations and Rank Methods](#pseudo-obs)
16. [Portfolio Risk via Copulas](#portfolio-risk)
17. [Pair Trading and Basket Arbitrage](#pair-trading)
18. [Credit Derivatives and the 2008 Critique](#credit)
19. [Crypto Cross-Asset Tail Dependence](#crypto-tail)
20. [Software and Code](#software)
21. [Reality Checks](#reality-checks)
22. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Why Copulas

A multivariate distribution carries two pieces of information: the marginal distributions (each variable in isolation) and the dependence structure (how they move together). Correlation captures one slice of dependence — the linear part — but misses everything else. Copulas separate the two cleanly: any joint distribution is a function of its marginals through a copula, and the copula encodes all of the dependence in pure form.

For trading, this separation matters because:

1. **Marginals are easy to fit**; dependence is hard. Empirical equity returns can be reasonably modeled with t-distributions or fitted GPD tails. The challenge is putting them together.

2. **Tail dependence dominates risk**. Two assets can have low correlation but strong joint downside exposure. A copula captures this; correlation does not.

3. **Stress regimes change the copula, not the marginals**. During calm periods, equities have low cross-correlation. During crises, "all correlations go to 1." This is a copula phenomenon — the dependence intensifies even if the marginal distributions of individual assets do not change much.

4. **Credit derivatives explicitly use copulas** to model joint default probabilities. The 2008 crisis was, in part, a failure to acknowledge that the Gaussian copula understates joint defaults of mortgage-backed securities.

The key result that organizes the field is Sklar's theorem: every joint CDF F factors as F(x_1, …, x_n) = C(F_1(x_1), …, F_n(x_n)) for a unique copula C (when marginals are continuous). The copula C is itself a CDF on [0,1]^n with uniform marginals. So the question of "how X and Y jointly behave" decomposes into "what is the marginal of X" + "what is the marginal of Y" + "what is the copula linking them."

We will develop the theory, work through every parametric copula in routine use, build dynamic and high-dimensional models (vines), and walk through trading applications with code.

---

## Sklar's Theorem

**Theorem (Sklar 1959)**: Let H be a joint CDF with marginals F_1, …, F_n. Then there exists a copula C such that

$$
H(x_1, \ldots, x_n) = C(F_1(x_1), \ldots, F_n(x_n)).
$$

If F_1, …, F_n are continuous, C is unique. Conversely, given any copula C and any univariate CDFs F_1, …, F_n, the function H defined by the above is a joint CDF with marginals F_1, …, F_n.

The proof uses the **probability integral transform**: if F is continuous, U = F(X) is uniformly distributed on [0, 1]. The copula is the joint CDF of the transformed marginals.

### Implications

- **Modeling pipeline**: fit marginals, fit copula separately, combine.
- **Marginal-free comparison**: copulas of distributions with different marginals can be directly compared via their copula.
- **Simulation pipeline**: sample copula → invert marginals → joint sample.

```python
import numpy as np

def sample_via_copula(n, copula_sampler, marginals):
    """Sample from a joint distribution via copula and marginals."""
    U = copula_sampler(n)  # n x d uniform on [0,1]
    X = np.zeros_like(U)
    for j, F_inv in enumerate(marginals):
        X[:, j] = F_inv(U[:, j])
    return X
```

This is the standard simulation engine for any copula-based model.

---

## Copula Definition and Properties

A **copula** C : [0, 1]^d → [0, 1] is a multivariate CDF with uniform [0, 1] marginals. Properties:

1. C(u_1, …, u_d) is non-decreasing in each u_i.
2. C(u_1, …, u_{j-1}, 0, u_{j+1}, …, u_d) = 0 (one zero marginal forces zero).
3. C(1, …, 1, u_j, 1, …, 1) = u_j (uniform marginals).
4. C is d-increasing: for any rectangle [a, b] ⊆ [0, 1]^d, the volume V_C([a, b]) ≥ 0.

The d-increasing condition ensures C generates a valid joint distribution (no negative density anywhere).

### Density

If C is differentiable, the **copula density** is

$$
c(u_1, \ldots, u_d) = \frac{\partial^d C}{\partial u_1 \cdots \partial u_d}.
$$

The joint density of (X_1, …, X_d) factors as

$$
h(x_1, \ldots, x_d) = c(F_1(x_1), \ldots, F_d(x_d)) \prod_{i=1}^d f_i(x_i).
$$

The product $\prod f_i$ is the marginal density; c is the dependence "correction." This factorization is the basis of likelihood-based estimation of copulas.

---

## Fréchet–Hoeffding Bounds

Every copula satisfies

$$
W(u_1, \ldots, u_d) \le C(u_1, \ldots, u_d) \le M(u_1, \ldots, u_d),
$$

where $M(u_1, \ldots, u_d) = \min(u_1, \ldots, u_d)$ is the **upper Fréchet bound** (perfect comonotone) and $W(u_1, \ldots, u_d) = \max(\sum u_i - (d-1), 0)$ is the **lower Fréchet bound**.

For d = 2:
- M corresponds to perfect positive (rank) correlation.
- W corresponds to perfect negative correlation.

For d ≥ 3, M is always a copula but W is *not* — perfect negative dependence is impossible among 3+ variables.

Independence copula:

$$
\Pi(u_1, \ldots, u_d) = u_1 u_2 \cdots u_d.
$$

---

## Gaussian Copula

The most-used copula in practice. Setup:

$$
C_R^{Ga}(u_1, \ldots, u_d) = \Phi_R(\Phi^{-1}(u_1), \ldots, \Phi^{-1}(u_d)),
$$

where Φ is the standard normal CDF and Φ_R is the multivariate normal CDF with correlation matrix R.

### Properties

- **Tail dependence**: λ_U = λ_L = 0 for any |ρ| < 1. This is the famous "Gaussian copula has no tail dependence" result.
- **Calibration**: easy via empirical correlation of probability-integral-transformed margins.
- **Sampling**: generate Z ~ 𝒩(0, R), set U = Φ(Z), invert marginals.

### Density

$$
c_R^{Ga}(u_1, \ldots, u_d) = \frac{1}{\sqrt{|R|}} \exp\!\left[ -\frac{1}{2} z^\top (R^{-1} - I) z \right],
$$

where z = (Φ^{-1}(u_1), …, Φ^{-1}(u_d))^⊤.

```python
import numpy as np
from scipy.stats import norm, multivariate_normal

def sample_gaussian_copula(n, R):
    d = len(R)
    Z = np.random.multivariate_normal(np.zeros(d), R, size=n)
    return norm.cdf(Z)

def gaussian_copula_logpdf(U, R):
    Z = norm.ppf(U)
    return multivariate_normal(np.zeros(len(R)), R).logpdf(Z) - norm.logpdf(Z).sum(axis=1)

# Example
R = np.array([[1, 0.7], [0.7, 1]])
U = sample_gaussian_copula(5000, R)
print(f"Sample correlation of Gaussian copula: {np.corrcoef(U.T)[0, 1]:.3f}")
```

Note: the Pearson correlation of U is *not* the same as the Pearson correlation of Z. The relevant invariant is **rank correlation** (Spearman's ρ), which is preserved by monotone transformations.

### Calibration

For Gaussian copula, calibrate R via:
1. Compute pseudo-observations $\hat U_{i,j} = R_{i,j}/(n+1)$ where R_{i,j} is the rank of x_{i,j} among observations of asset j.
2. Compute Z_{i,j} = Φ^{-1}(Û_{i,j}).
3. R̂_{j,k} = Pearson correlation of Z_{·, j}, Z_{·, k}.

This is the **canonical maximum likelihood** for Gaussian copula correlation.

### Reality Check — Why Gaussian Falls Short

The Gaussian copula assumes the joint extremes are uncorrelated. Empirically:
- Equities in crashes: tail dependence λ_L ~ 0.3-0.5, not zero.
- Crypto pairs: λ_U, λ_L ~ 0.4-0.6.
- Credit defaults: highly tail-dependent.

Pricing CDOs with a Gaussian copula in 2007 was the precise mathematical error that contributed to underestimating senior-tranche risk. Document 218 covers credit derivative risk in depth.

---

## Student-t Copula

The t-copula:

$$
C_{R, \nu}^t(u_1, \ldots, u_d) = T_{R, \nu}(t_\nu^{-1}(u_1), \ldots, t_\nu^{-1}(u_d)),
$$

where T_{R,ν} is the multivariate t-CDF with correlation R and degrees of freedom ν, and t_ν is univariate.

### Tail Dependence

For two-dimensional t-copula:

$$
\lambda_U = \lambda_L = 2 t_{\nu+1}\!\left( -\sqrt{\nu+1}\sqrt{(1-\rho)/(1+\rho)} \right).
$$

Critically, λ > 0 for any ν < ∞ and ρ > -1. As ν → ∞, t-copula → Gaussian and λ → 0. For ν = 4, ρ = 0.5: λ ≈ 0.25. For ν = 8, ρ = 0.7: λ ≈ 0.3.

### Calibration

ν is calibrated via maximum likelihood (jointly with R) or via tail-dependence estimation:

```python
import numpy as np
from scipy.stats import t, multivariate_t
from scipy.optimize import minimize

def t_copula_logpdf(U, R, nu):
    d = len(R)
    Z = t(df=nu).ppf(U)
    log_mvt = multivariate_t(loc=np.zeros(d), shape=R, df=nu).logpdf(Z)
    log_marginals = t(df=nu).logpdf(Z).sum(axis=1)
    return log_mvt - log_marginals

def fit_t_copula(U):
    # Calibrate R via empirical, optimize nu via MLE
    R_emp = np.corrcoef(t.ppf(U, df=10).T)
    def neg_ll(nu):
        if nu <= 2:
            return 1e10
        return -t_copula_logpdf(U, R_emp, nu).sum()
    res = minimize(neg_ll, x0=10, method='Nelder-Mead', bounds=[(3, 100)])
    return R_emp, res.x[0]
```

### Use in Practice

The t-copula is the *workhorse* for multivariate financial dependence. It captures:
- Linear dependence (via R).
- Symmetric tail dependence (via ν).
- Excess kurtosis at the joint level.

Limitations:
- Symmetric: λ_U = λ_L. Real markets have asymmetric tails (worse joint downside).
- Single ν for all pairs: assumes uniform tail behavior.

For asymmetric tails, use Archimedean copulas or vine constructions.

---

## Archimedean Copulas — Clayton, Gumbel, Frank

**Archimedean copulas** have the form

$$
C(u_1, \ldots, u_d) = \psi\!\left( \psi^{-1}(u_1) + \cdots + \psi^{-1}(u_d) \right),
$$

where ψ : [0, ∞) → [0, 1] is a generator function (continuous, non-increasing, ψ(0) = 1, ψ(∞) = 0).

### Clayton Copula

$$
C_\theta^{\text{Cl}}(u_1, u_2) = (u_1^{-\theta} + u_2^{-\theta} - 1)^{-1/\theta}, \qquad \theta > 0.
$$

Generator: ψ(t) = (1 + θt)^{-1/θ}.

Properties:
- Lower tail dependence: $\lambda_L = 2^{-1/\theta}$ (positive).
- Upper tail dependence: λ_U = 0.
- Asymmetric — captures crashes well.

For θ → 0, Clayton → independence. For θ → ∞, Clayton → upper Fréchet bound.

### Gumbel Copula

$$
C_\theta^{\text{Gu}}(u_1, u_2) = \exp\!\left[ -\!\left( (-\log u_1)^\theta + (-\log u_2)^\theta \right)^{1/\theta} \right], \qquad \theta \ge 1.
$$

Generator: ψ(t) = exp(-t^{1/θ}).

Properties:
- Upper tail dependence: $\lambda_U = 2 - 2^{1/\theta}$.
- Lower tail dependence: λ_L = 0.
- Asymmetric — captures co-booms.

### Frank Copula

$$
C_\theta^{\text{Fr}}(u_1, u_2) = -\frac{1}{\theta} \log\!\left[ 1 + \frac{(e^{-\theta u_1} - 1)(e^{-\theta u_2} - 1)}{e^{-\theta} - 1} \right].
$$

Properties:
- λ_U = λ_L = 0 (no tail dependence).
- Symmetric.
- θ ∈ ℝ, with negative θ allowing negative dependence.

### Choice of Archimedean

| Copula | Lower TD | Upper TD | Use |
|---|---|---|---|
| Clayton | yes | no | Equity (crashes worse than booms) |
| Gumbel | no | yes | Joint upside |
| Frank | no | no | Symmetric without tail focus |
| Joe | no | yes | Stronger upper TD than Gumbel |
| BB1 | yes | yes | Both tails (Clayton-Gumbel mixture) |

```python
import numpy as np
from scipy.stats import expon

def sample_clayton(n, theta, d=2):
    """Sample from Clayton copula via Marshall-Olkin algorithm."""
    if theta == 0:
        return np.random.uniform(size=(n, d))
    # V ~ Gamma(1/theta, 1)
    V = np.random.gamma(1/theta, 1, size=n)
    E = np.random.exponential(1, size=(n, d))
    U = (1 + E / V[:, None])**(-1/theta)
    return U

def sample_gumbel(n, theta, d=2):
    """Sample from Gumbel copula via stable mixing."""
    if theta == 1:
        return np.random.uniform(size=(n, d))
    # V is positive stable with parameter 1/theta
    from scipy.stats import levy_stable
    V = levy_stable.rvs(alpha=1/theta, beta=1, size=n)
    E = np.random.exponential(1, size=(n, d))
    U = np.exp(-(E / V[:, None])**(1/theta))
    return U

# Estimate empirical TD on simulated data
np.random.seed(0)
U_clayton = sample_clayton(5000, theta=2)
print(f"Clayton θ=2: lower TD theory = {2**(-0.5):.3f}")
```

### Calibration

Archimedean copulas have one parameter θ (per pair). Calibration via MLE:

$$
\hat \theta = \arg\max_\theta \sum_i \log c_\theta(\hat U_{i,1}, \hat U_{i,2}),
$$

where Û are pseudo-observations.

For high-dimensional data, exchangeable Archimedean (single θ for all pairs) is too restrictive. Use vine copulas or hierarchical Archimedean.

---

## Other Bivariate Copulas

A range of two-parameter copulas exist for richer asymmetric tail behavior:

- **Joe**: similar to Gumbel but with stronger upper TD.
- **BB1, BB7**: Joe-Clayton mixtures with both tail parameters.
- **Plackett**: defined via odds ratio; useful for ordinal data.
- **Galambos**: extreme-value copula with both tails.
- **Marshall-Olkin**: jump copula for credit modeling.

Each has its niche. In practice, BB1 and Joe-Clayton are favorites for asymmetric two-tailed equity dependence.

---

## Vine Copulas — C-Vine, D-Vine, R-Vine

For d-dimensional dependence, a single d-dimensional copula is restrictive. **Pair copula constructions (PCC)** and **vines** decompose a d-variate dependence into d(d-1)/2 bivariate copulas, each modeling a different pair conditional on others.

### Construction

Build the joint density via successive conditionals:

$$
f(x_1, \ldots, x_d) = f(x_1) \cdot f(x_2|x_1) \cdot f(x_3|x_1, x_2) \cdots
$$

Each conditional $f(x_j|x_1, \ldots, x_{j-1})$ involves a bivariate copula and conditional marginals. Building a vine corresponds to a particular ordering.

### C-Vine (Canonical)

A central variable connected to all others; the others are connected through it. Tree structure: V_1 → V_2, V_3, …; then V_2 → V_3, …; etc.

### D-Vine (Drawable)

A path: V_1 → V_2 → V_3 → …. Each consecutive pair has its own copula; further pairs have conditional copulas.

### R-Vine (Regular)

A general tree structure satisfying certain proximity conditions (Bedford–Cooke 2002). Generalizes both C and D vines.

### Estimation

Aas, Czado, Frigessi, Bakken (2009): given the vine structure, estimate each pair copula sequentially. R package VineCopula and Python pyvinecopulib are standard implementations.

For high-dimensional portfolios (d > 10), vine copulas dramatically outperform single multivariate copulas in fit and computational tractability.

```python
# Pseudo-code for D-vine construction.
def fit_d_vine(U, copula_family='gaussian'):
    """Fit a D-vine copula. U: n x d pseudo-observations."""
    d = U.shape[1]
    # Tree 1: pairs (1,2), (2,3), ..., (d-1, d)
    # Tree 2: pairs (1,3|2), (2,4|3), ..., (d-2, d|d-1)
    # ...
    # In practice, use pyvinecopulib library
    import pyvinecopulib as pv
    controls = pv.FitControlsVinecop(family_set=[getattr(pv, copula_family.title())])
    cop = pv.Vinecop(d=d)
    cop.select(U, controls)
    return cop
```

### Reality Check — Vine Selection

Three choices in vine specification:
- Tree structure (C, D, or R).
- Pair-copula family (Gaussian, t, Clayton, Gumbel, etc., per pair).
- Truncation level (set higher trees to independence).

Proper selection uses BIC, AIC, or cross-validation. Empirical wisdom: equity baskets often have more structure in the first few trees; deeper conditional dependencies are weak.

---

## Empirical and Non-Parametric Copulas

### Empirical Copula

Given observations (X_{i,1}, …, X_{i,d}) for i = 1, …, n, the **empirical copula** is

$$
C_n(u_1, \ldots, u_d) = \frac{1}{n} \sum_{i=1}^n 1\{\hat U_{i,1} \le u_1, \ldots, \hat U_{i,d} \le u_d\},
$$

where $\hat U_{i,j} = R_{i,j} / (n+1)$ are the pseudo-observations (rank-transformed).

C_n converges to the true copula. Useful for goodness-of-fit testing and for non-parametric exploration of dependence.

### Beta Kernel and Smoothed Copulas

Empirical copula is discontinuous. Smoothed versions use beta kernels or KDE in copula space. Useful for likelihood-based methods that need continuous densities.

### Reality Check — Non-Parametric Limits

Non-parametric copulas suffer from the curse of dimensionality. For d > 5, sample sizes for accurate fitting balloon. Most production copula work is parametric (vine + chosen families).

---

## Estimation Methods

### IFM (Inference Functions for Margins)

1. Fit each marginal F_i separately.
2. Compute pseudo-observations $\hat U_{i,j} = F_j(X_{i,j})$.
3. Fit copula parameters via MLE on Û.

Two-stage but consistent. Standard errors require sandwich estimator.

### Canonical Maximum Likelihood (CML)

1. Compute *empirical* pseudo-observations $\hat U_{i,j} = R_{i,j}/(n+1)$.
2. Fit copula parameters via MLE.

Margin-free; doesn't require correct margin specification. Often preferred when margins are uncertain.

### Method of Moments

Match copula-derived moments (Kendall's τ, Spearman's ρ) to empirical estimates. For copulas with explicit τ-θ relationship (Clayton, Gumbel), this is one-step.

| Copula | τ-θ relation |
|---|---|
| Gaussian | $\tau = (2/\pi) \arcsin(\rho)$ |
| Clayton | $\tau = \theta/(\theta+2)$ |
| Gumbel | $\tau = 1 - 1/\theta$ |
| Frank | $\tau = 1 - (4/\theta)(1 - D_1(\theta))$ |

where $D_1$ is the Debye function.

### Bayesian

Place prior over copula parameters; use MCMC. Useful for hierarchical models. Document 203 covers Bayesian methods.

---

## Goodness-of-Fit Testing

Standard tests:

### Cramér–von Mises

$$
S_n = \int_{[0,1]^d} (C_n(u) - C_\theta(u))^2 \, dC_n(u).
$$

p-value via parametric bootstrap (Genest et al. 2009).

### Kolmogorov–Smirnov

Sup-norm version. Less powerful than CvM in practice.

### Genest–Rémillard (2009)

Compares empirical copula to fitted parametric. Provides bootstrap p-values. Standard in academic finance.

### Reality Check — Power and Sample Size

GoF tests have low power for moderate sample sizes. Even with n = 1000, the test may fail to reject a wrong copula. Always combine GoF with diagnostic plots (chi-plots, K-plots) and out-of-sample validation.

---

## Tail Dependence

Already introduced. Closed forms for major copulas:

| Copula | λ_L | λ_U |
|---|---|---|
| Gaussian | 0 | 0 |
| Student-t (ν, ρ) | 2t_{ν+1}(-√((ν+1)(1-ρ)/(1+ρ))) | same |
| Clayton (θ > 0) | 2^{-1/θ} | 0 |
| Gumbel (θ ≥ 1) | 0 | 2 - 2^{1/θ} |
| Frank | 0 | 0 |
| Joe (θ ≥ 1) | 0 | 2 - 2^{1/θ} |

### Empirical Estimation

```python
import numpy as np

def upper_tail_dependence(u, v, q=0.05):
    threshold = 1 - q
    return np.mean((u > threshold) & (v > threshold)) / q

def lower_tail_dependence(u, v, q=0.05):
    return np.mean((u < q) & (v < q)) / q

# Example
np.random.seed(0)
U = sample_clayton(10000, theta=2)
print(f"Clayton θ=2 — empirical lower TD: {lower_tail_dependence(U[:,0], U[:,1]):.3f}")
print(f"Theoretical: {2**(-0.5):.3f}")
```

For threshold q, the estimate has standard error ~√(λ(1-λ)/(nq)). For n=2000 and q=0.05, SE ≈ 0.1 — wide CIs at usable thresholds.

---

## Conditional and Dynamic Copulas

Static copulas assume time-invariant dependence. Real markets have:
- Regime-switching dependence (calm vs crisis).
- Time-varying correlation (DCC-style).
- Time-varying tail dependence.

### Patton (2006) Time-Varying Copulas

Allow copula parameters to evolve as

$$
\theta_t = \omega + \alpha \theta_{t-1} + \beta g(\hat U_{t-1}),
$$

where g is some function of past observations. Estimation by maximum likelihood with tractable Kalman or particle filter.

### Regime-Switching

Markov chain governs which copula is active:
- Regime 0: Gaussian (calm).
- Regime 1: t (stress).
- Regime 2: Clayton (crash).

Filter via HMM (document 203).

### Dynamic Conditional Correlation (DCC)

Engle (2002): correlation matrix R_t evolves as
$$
R_t = \text{diag}(Q_t)^{-1/2} Q_t \text{diag}(Q_t)^{-1/2}.
$$
$$
Q_t = (1 - \alpha - \beta) \bar Q + \alpha \epsilon_{t-1} \epsilon_{t-1}^\top + \beta Q_{t-1}.
$$

Combined with Gaussian or t-copula, provides time-varying correlation.

### Reality Check — Dynamic Models

Time-varying copulas are notoriously difficult to estimate stably:
- Many parameters relative to data.
- Small sample inference is unreliable.
- Out-of-sample performance often disappoints.

For production, regime-switching with a small number of distinct copulas often outperforms flexible time-varying parametric models.

---

## Pseudo-Observations and Rank Methods

Pseudo-observations:
$$
\hat U_{i,j} = R_{i,j} / (n+1),
$$

where R_{i,j} is the rank of x_{i,j} among the j-th column. The (n+1) avoids U = 1.

For ties, use mid-ranks (rank averaged across ties).

Rank-based methods are robust to misspecified margins. They underlie:
- Spearman's ρ (correlation of pseudo-observations).
- Kendall's τ (probability of concordance minus discordance).
- All copula calibration based on Û.

---

## Portfolio Risk via Copulas

Compute portfolio VaR/ES with copula-based dependence:

1. Fit marginal distributions (e.g., GPD on tails).
2. Fit copula on pseudo-observations.
3. Simulate N joint scenarios from copula.
4. Apply marginals (inverse CDF) to get joint returns.
5. Compute portfolio P&L for each.
6. Take quantile / mean-conditional for VaR / ES.

```python
import numpy as np
from scipy.stats import norm, t, genpareto

def copula_var_es(returns, weights, p, n_sim=100_000, copula='t'):
    """VaR/ES via copula simulation."""
    n, d = returns.shape
    # Pseudo-observations
    U = np.zeros_like(returns)
    for j in range(d):
        ranks = returns[:, j].argsort().argsort() + 1
        U[:, j] = ranks / (n + 1)
    
    if copula == 'gaussian':
        Z = norm.ppf(U)
        R = np.corrcoef(Z.T)
        Z_sim = np.random.multivariate_normal(np.zeros(d), R, size=n_sim)
        U_sim = norm.cdf(Z_sim)
    elif copula == 't':
        # Crude: assume df=8
        Z = t(df=8).ppf(U)
        R = np.corrcoef(Z.T)
        from scipy.stats import multivariate_t
        Z_sim = multivariate_t(loc=np.zeros(d), shape=R, df=8).rvs(size=n_sim)
        U_sim = t(df=8).cdf(Z_sim)
    
    # Apply empirical marginals
    sim_returns = np.zeros_like(U_sim)
    sorted_returns = np.sort(returns, axis=0)
    for j in range(d):
        idx = np.clip((U_sim[:, j] * n).astype(int), 0, n-1)
        sim_returns[:, j] = sorted_returns[idx, j]
    
    portfolio = sim_returns @ weights
    var_p = -np.quantile(portfolio, 1 - p)
    es_p = -portfolio[portfolio <= -var_p].mean()
    return var_p, es_p

np.random.seed(42)
T = 1000
returns = np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], size=T) * 0.01
weights = np.array([0.5, 0.5])
var, es = copula_var_es(returns, weights, p=0.99, copula='t')
print(f"99% VaR: {var:.4f}, ES: {es:.4f}")
```

Comparing:
- Independence copula: lower VaR (diversification).
- Gaussian copula: moderate.
- t-copula or Clayton: higher (tail dependence raises joint losses).

The right copula gives the right risk; the wrong one systematically misestimates.

---

## Pair Trading and Basket Arbitrage

### Liew–Wu (2013) Copula Pairs

Build a pair-trading signal from copula-based conditional probabilities:

1. Fit margin distributions of two assets.
2. Fit copula on pseudo-observations.
3. Compute conditional probability $\mathbb{P}(U_2 < u_2 | U_1 = u_1)$ from the copula.
4. Trade when conditional probability is in extremes.

Copula-based pairs are more robust to non-Gaussian dependence than correlation-based pairs.

```python
def conditional_clayton(u1, u2, theta):
    """P(U2 ≤ u2 | U1 = u1) under Clayton."""
    if theta == 0:
        return u2
    return u1**(-theta - 1) * (u1**(-theta) + u2**(-theta) - 1)**(-1/theta - 1)
```

### Basket Arbitrage

For an index vs constituents trade, the copula models the joint distribution of constituent returns. Index basket valuation is the copula-based expectation of the basket payoff. Mismatches between options on index vs sum of options on constituents can be exploited.

Document 60 (Volatility Dispersion) covers this in detail.

---

## Credit Derivatives and the 2008 Critique

### Li (2000) Gaussian Copula Default Model

Default time of asset i: τ_i = F_i^{-1}(N(Y_i)) where Y is multivariate normal with correlation R. Joint defaults: ℙ(τ_1 ≤ T, τ_2 ≤ T) = C^{Ga}(F_1(T), F_2(T); ρ).

### CDO Pricing

Senior tranches: pay if total losses exceed a threshold. Their value depends on the joint loss distribution, which depends on the default-time correlation copula.

The Gaussian copula has zero tail dependence. Senior tranche pricing under Gaussian assumed joint defaults are essentially independent in the tails. In reality, mortgage defaults are highly tail-dependent (housing crash hits all simultaneously). The Gaussian copula radically underestimated senior-tranche risk.

### Salmon (2009) and the Critique

Felix Salmon's "Recipe for Disaster" (Wired) argued that the Gaussian copula was the "formula that killed Wall Street." The argument is partially right (Gaussian copula was indeed the wrong choice for joint default modeling) but partially overdrawn (the larger problem was systemic mispricing of housing risk, not just the copula choice).

### Modern Practice

For CDO and CLO modeling, use:
- t-copula or Archimedean (Clayton) for tail dependence.
- Factor copulas (one or two latent factors).
- Stochastic recovery rates.
- Time-varying correlation.

---

## Crypto Cross-Asset Tail Dependence

Empirical findings for crypto (BTC, ETH, large-cap altcoins):

- Pairwise correlations: 0.5-0.8 in calm periods, 0.85-0.95 in crashes.
- Lower tail dependence: 0.4-0.6 (joint downside).
- Upper tail dependence: 0.3-0.5 (joint upside).
- Symmetric in some periods, asymmetric in others.

Best fits typically involve t-copula (df = 4-7) or BB1.

For crypto-equity correlation:
- Pre-2020: ~0.0-0.1 (low correlation).
- 2020-2024: 0.3-0.5 (significant correlation).
- During Fed tightening cycles: 0.5-0.7.

The increase in crypto-equity correlation after institutional adoption is itself a regime change in the copula.

### Reality Check — Crypto Dependence Structure

Crypto assets are highly heterogeneous. BTC-ETH have stable strong dependence; smaller alts can have very different copulas. Aggregating across alt categories (DeFi, gaming, L1, L2) reveals different dependence structures — vine copulas with hierarchical structure are appropriate.

---

## Software and Code

### Python

- **copulas**: simple parametric copulas.
- **copulae**: more comprehensive.
- **pyvinecopulib**: vine copulas (binding to C++ library).
- **statsmodels.distributions.copula**: limited but standard.

### R

- **copula**: comprehensive parametric copulas.
- **VineCopula**: vines.
- **CDVine**: D and C vines.
- **rvinecopulib**: modern vine implementation.

### Production Considerations

- Choose copula family based on tail behavior (use empirical TD).
- For high-dim, vines are necessary.
- Refit periodically (regime changes invalidate static fits).
- Cross-validate any out-of-sample claims.

---

## Reality Checks

- **Sample size**: copula estimation requires substantial data; n < 200 usually insufficient.
- **Margin choice matters**: misspecified margins propagate to copula estimates.
- **Dynamic dependence**: static copulas fail in regime changes.
- **High dimensions**: curse of dimensionality; vines mitigate but don't eliminate.
- **Tail behavior**: hardest to estimate, most important to get right.
- **Identifiability**: some copula families look similar in the body; identifying via tails requires tail-rich data.

---

## Reference Tables, Cheat Sheets, Bibliography

### Copula Cheat Sheet

| Copula | Param | TD Lower | TD Upper | Symmetric? |
|---|---|---|---|---|
| Independence Π | — | 0 | 0 | yes |
| Gaussian | R | 0 | 0 | yes |
| Student-t | (R, ν) | >0 | >0 | yes |
| Clayton | θ > 0 | 2^{-1/θ} | 0 | no |
| Gumbel | θ ≥ 1 | 0 | 2-2^{1/θ} | no |
| Frank | θ ∈ ℝ | 0 | 0 | yes |
| Joe | θ ≥ 1 | 0 | 2-2^{1/θ} | no |
| BB1 | (θ, δ) | >0 | >0 | no |
| Vine | structure + pair-copulas | flexible | flexible | flexible |

### Bibliography

- **Nelsen, R. (2006), *An Introduction to Copulas* (2nd ed.), Springer.** Standard textbook.
- **Joe, H. (1997), *Multivariate Models and Dependence Concepts*, Chapman & Hall.** Comprehensive theory.
- **Joe, H. (2014), *Dependence Modeling with Copulas*, Chapman & Hall.** Update.
- **Cherubini, U., Luciano, E., Vecchiato, W. (2004), *Copula Methods in Finance*, Wiley.** Finance-applied.
- **Patton, A. (2012), "A Review of Copula Models for Economic Time Series", *J. Multivariate Analysis* 110: 4–18.**
- **Aas, K., Czado, C., Frigessi, A., Bakken, H. (2009), "Pair-Copula Constructions of Multiple Dependence", *Insurance: Mathematics and Economics* 44(2): 182–198.** Vines.
- **Bedford, T. and Cooke, R. (2002), "Vines: A New Graphical Model for Dependent Random Variables", *Annals of Statistics* 30(4): 1031–1068.**
- **Genest, C., Rémillard, B., Beaudoin, D. (2009), "Goodness-of-Fit Tests for Copulas: A Review and a Power Study", *Insurance Math. Econ.* 44(2): 199–213.**
- **Li, D. (2000), "On Default Correlation: A Copula Function Approach", *J. Fixed Income* 9(4): 43–54.** The famous (and infamous) paper.
- **Salmon, F. (2009), "Recipe for Disaster: The Formula That Killed Wall Street", *Wired*.** The popular critique.
- **Embrechts, P., Lindskog, F., McNeil, A. (2003), "Modelling Dependence with Copulas and Applications to Risk Management", in *Handbook of Heavy Tailed Distributions in Finance*.** Practical guide.
- **Patton, A. (2006), "Modelling Asymmetric Exchange Rate Dependence", *International Economic Review* 47(2): 527–556.** Time-varying copulas.
- **Liew, R. and Wu, Y. (2013), "Pairs Trading: A Copula Approach", *J. Derivatives & Hedge Funds* 19: 12–30.**

### Cross-References

- Document 200 — Stochastic Calculus.
- Document 203 — Bayesian Methods.
- Document 204 — Information Theory.
- Document 206 — EVT.
- Document 211 — Backtesting.
- Document 218 — Hedge Fund Risk Operations.
- Document 60 — Volatility Dispersion Trading.
- Document 81 — Hierarchical Risk Parity.

---

*End of document 207. ~1,400 lines.*
