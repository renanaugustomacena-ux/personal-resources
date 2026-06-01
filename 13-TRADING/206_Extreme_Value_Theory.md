# 206 — Extreme Value Theory and Power Laws for Financial Risk

> Tail risk modeling for trading and risk management. Covers block-maxima (GEV), peaks-over-threshold (GPD), Hill/Pickands estimators, multivariate extremes, power laws, stable distributions, long-memory processes, and applied VaR/ES/tail-risk hedging. Self-contained beyond the prerequisites of document 200.

---

## Table of Contents

1. [Why EVT Matters for Trading](#why-evt)
2. [The Three Extreme Value Distributions](#three-evds)
3. [Generalized Extreme Value (GEV) Distribution](#gev)
4. [Block Maxima Method](#block-maxima)
5. [Generalized Pareto Distribution (GPD)](#gpd)
6. [Peaks Over Threshold (POT)](#pot)
7. [Threshold Selection](#threshold-selection)
8. [Hill Estimator](#hill)
9. [Pickands Estimator and Moment Estimator](#pickands)
10. [Tail Index Estimation in Practice](#tail-index)
11. [VaR and Expected Shortfall via EVT](#var-es-evt)
12. [Multivariate Extremes and Tail Dependence](#multivariate)
13. [Power Laws and Pareto Distributions](#power-laws)
14. [Heavy Tails in Trading Data](#heavy-tails-data)
15. [Tail Risk Hedging](#tail-hedging)
16. [Backtesting with EVT](#evt-backtesting)
17. [Stable Distributions and α-Stable Processes](#stable)
18. [Long Memory and Hurst Exponent](#long-memory)
19. [Self-Organized Criticality and Crisis Dynamics](#soc)
20. [Software and Code](#software)
21. [Case Studies](#case-studies)
22. [Reality Checks](#reality-checks)
23. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Why EVT Matters for Trading

Standard statistical inference characterizes the *typical* observation. Extreme value theory characterizes the *atypical* — the once-a-decade move, the tail event that defines drawdowns, the catastrophe that breaks risk models built around averages. For trading, this distinction is not academic: the difference between 20-vol and 80-vol days, between a 2-sigma move and a 6-sigma move, between a routine drawdown and a fund-killing one, is precisely the difference between the body and the tail.

Three trading-relevant problems force us into EVT:

1. **VaR and ES estimation**. Empirical quantiles based on historical bodies of distributions systematically understate tail risk. EVT provides distribution-fitting tools tailored to the tail and asymptotic guarantees about how those tools behave when the body is irrelevant.

2. **Stress testing**. Regulatory and internal stress tests ask "how bad can it get?" The honest answer requires extrapolation beyond the worst observation. EVT is the principled way to extrapolate.

3. **Tail-risk hedging**. Universa-style strategies, OTM put portfolios, variance swaps, and similar tail-protection programs are priced and sized around the tail probabilities of the underlying. Misestimating those probabilities creates either over- or under-hedging.

The central insight of classical EVT is the existence of a parametric *limit law* for tails — analogous to the Central Limit Theorem for averages, but for maxima or exceedances. Where the CLT says "averages converge to a Gaussian regardless of the distribution," the Fisher–Tippett–Gnedenko theorem says "maxima converge to one of three families regardless of the distribution." That single result organizes the whole field.

A concrete motivation. Consider 100 years of S&P 500 daily returns. The empirical distribution has mean ~0.04% per day and standard deviation ~1%. A naive Gaussian model says the worst day in 100 years should be about −4.5%. The actual worst days (October 19, 1987: −20.5%; March 16, 2020: −12.0%; multiple double-digit crashes in 2008) are far worse. The Gaussian model is not just wrong about magnitudes; it understates the *frequency* of extreme days by orders of magnitude. EVT tells us that the right tail-fitting object is not a Gaussian but a Generalized Extreme Value or Generalized Pareto, with specific shape parameter ξ that empirical equity returns satisfy in the range 0.2–0.4 — implying genuinely heavy tails that require logarithmic, not exponential, decay.

We will develop the machinery and apply it. Throughout, we will tie back to traditional methods (parametric VaR, historical VaR) and show what EVT adds.

---

## The Three Extreme Value Distributions

The Fisher–Tippett–Gnedenko theorem (Fisher–Tippett 1928, Gnedenko 1943): for iid observations X_1, X_2, …, if there exist normalizing sequences a_n > 0 and b_n such that

$$
\mathbb{P}\!\left(\frac{M_n - b_n}{a_n} \le x\right) \to G(x), \qquad M_n = \max(X_1, \ldots, X_n),
$$

for some non-degenerate G, then G belongs to one of three families:

- **Gumbel** (light tails, ξ = 0): $G(x) = \exp(-e^{-x})$.
- **Fréchet** (heavy tails, ξ > 0): $G(x) = \exp(-x^{-\alpha})$ for x > 0, where $\alpha = 1/\xi$.
- **Weibull** (bounded tails, ξ < 0): $G(x) = \exp(-(-x)^\alpha)$ for x ≤ 0, where $\alpha = -1/\xi$.

These three families are united in the **Generalized Extreme Value (GEV) distribution**:

$$
G_\xi(x) = \exp\!\left[ -\left(1 + \xi x\right)^{-1/\xi} \right], \qquad 1 + \xi x > 0.
$$

The Gumbel case is recovered as $\xi \to 0$:

$$
G_0(x) = \exp(-e^{-x}).
$$

### Domains of Attraction

Different parent distributions converge to different EVD families:

- **Gumbel domain (ξ = 0)**: Gaussian, exponential, lognormal (despite being unbounded), gamma. Light-to-moderate tails. Returns of "calm" assets sometimes fit here.
- **Fréchet domain (ξ > 0)**: Pareto, Cauchy, Student-t with finite degrees of freedom, F-distribution. Power-law tails. Equity returns, crypto returns, financial losses.
- **Weibull domain (ξ < 0)**: Uniform, beta, any distribution with bounded support. Maximum is bounded above. Rare in finance.

The classification depends only on the tail behavior of the parent distribution. Specifically, X is in the Fréchet domain iff its survival function satisfies

$$
\mathbb{P}(X > x) = x^{-\alpha} L(x),
$$

where L is a slowly varying function (L(tx)/L(x) → 1 for all t > 0). This is the **regular variation** condition.

### Why Three Families and Not One?

The three families correspond to qualitatively different tail behaviors:
- Polynomial decay (Fréchet) — the survival function decays as a power law.
- Exponential decay (Gumbel) — survival function decays at exponential rate.
- Bounded support (Weibull) — survival function reaches zero at a finite endpoint.

Gnedenko's theorem says these three are the *only* possibilities for the limit of normalized maxima. Empirically, finance is dominated by the Fréchet case, but Gumbel-like tails appear in well-behaved low-volatility periods and in carefully diversified portfolios.

### Reality Check — Normalization Sequences

The theorem requires the existence of normalizing sequences a_n, b_n such that the limit is non-degenerate. Most distributions used in finance satisfy this, but some (e.g., very heavy-tailed Cauchy with α = 1) need careful handling. In production, one fits the GEV directly to block maxima rather than worrying about the abstract normalization.

---

## Generalized Extreme Value (GEV) Distribution

The GEV unifies the three EVD families with a three-parameter form, adding location (μ) and scale (σ) parameters:

$$
G_{\mu, \sigma, \xi}(x) = \exp\!\left[ -\left(1 + \xi \frac{x - \mu}{\sigma}\right)^{-1/\xi} \right], \qquad 1 + \xi (x - \mu)/\sigma > 0.
$$

For ξ = 0:
$$
G_{\mu, \sigma, 0}(x) = \exp\!\left( -\exp\!\left( -\frac{x - \mu}{\sigma} \right) \right).
$$

Density:

$$
g_{\mu, \sigma, \xi}(x) = \frac{1}{\sigma} \!\left(1 + \xi \frac{x - \mu}{\sigma}\right)^{-1/\xi - 1} \exp\!\left[ -\!\left(1 + \xi \frac{x - \mu}{\sigma}\right)^{-1/\xi} \right].
$$

### Moments

Mean:
$$
\mathbb{E}[X] = \mu + \sigma \frac{\Gamma(1 - \xi) - 1}{\xi}, \qquad \xi < 1, \xi \ne 0.
$$

For ξ = 0, $\mathbb{E}[X] = \mu + \sigma \gamma$, where γ ≈ 0.5772 is the Euler–Mascheroni constant.

Variance:
$$
\text{Var}(X) = \frac{\sigma^2}{\xi^2} \!\left[ \Gamma(1 - 2\xi) - \Gamma(1 - \xi)^2 \right], \qquad \xi < 1/2.
$$

For ξ ≥ 1/2, variance is infinite. For ξ ≥ 1, mean is infinite. For ξ ≥ 1/k, the k-th moment is infinite. This is the precise mathematical statement of "heavy tails": the higher the shape parameter, the fewer finite moments.

### MLE Estimation

Given block maxima {M_1, …, M_K}, maximize the log-likelihood:

$$
\ell(\mu, \sigma, \xi) = -K \log \sigma - (1 + 1/\xi) \sum_{i} \log\!\left(1 + \xi \frac{M_i - \mu}{\sigma}\right) - \sum_{i} \!\left(1 + \xi \frac{M_i - \mu}{\sigma}\right)^{-1/\xi}.
$$

Numerical optimization with bounded ξ. Standard implementations: scipy.stats.genextreme, evd in R, evt-py.

```python
import numpy as np
from scipy.stats import genextreme
from scipy.optimize import minimize

def fit_gev(maxima):
    """Fit GEV via MLE. Returns (xi, mu, sigma)."""
    # scipy.stats.genextreme uses convention c = -xi
    c, loc, scale = genextreme.fit(maxima)
    return -c, loc, scale

# Synthetic example: simulate Frechet-domain GEV via Pareto block maxima
np.random.seed(42)
n_per_block = 250  # trading days per year
n_blocks = 50      # 50 years
parent = np.random.pareto(3, size=(n_blocks, n_per_block)) + 1  # Pareto with alpha=3
maxima = parent.max(axis=1)
xi, mu, sigma = fit_gev(maxima)
print(f"Fitted GEV: xi={xi:.3f}, mu={mu:.3f}, sigma={sigma:.3f}")
print(f"Theoretical xi for parent: {1/3:.3f}")
```

### Return Levels

The **T-period return level** z_T is the level exceeded once on average every T blocks:

$$
z_T = \mu + \frac{\sigma}{\xi} \!\left[ \!\left( -\log(1 - 1/T) \right)^{-\xi} - 1 \right].
$$

For ξ = 0, $z_T = \mu - \sigma \log(-\log(1 - 1/T))$.

For 100-year return level with annual block size: T = 100. Plug in fitted parameters to get the 100-year worst day (or 100-year worst year, depending on block).

### Confidence Intervals via Profile Likelihood

For a parameter of interest (e.g., return level z_T or shape ξ), profile likelihood gives more accurate intervals than the Wald (asymptotic Gaussian) approximation. Compute the profile log-likelihood as a function of the parameter; the 95% CI is the set where profile likelihood is within χ²(0.95, 1)/2 ≈ 1.92 of the maximum.

### Reality Check — Block Size and Bias

The asymptotic GEV approximation assumes block size n → ∞. Real samples are finite. For trading, common block sizes:

- Monthly maxima of daily returns: ~21 obs/block. Bias is non-trivial.
- Quarterly: ~63 obs/block. Better.
- Annual: ~252 obs/block. Bias is small but the number of blocks shrinks.

The trade-off: larger blocks → less bias but fewer maxima for fitting. EVT's POT formulation (next section) often gives better finite-sample performance.

---

## Block Maxima Method

Procedure:
1. Divide the data into K non-overlapping blocks of length n.
2. For each block, take the maximum (or maximum loss).
3. Fit GEV to the K block maxima.
4. Use the fitted GEV for return-level estimation.

```python
import numpy as np

def block_maxima(returns, block_size):
    """Return array of block maxima from a return series."""
    n = len(returns)
    K = n // block_size
    return np.array([returns[i*block_size:(i+1)*block_size].max() for i in range(K)])

# 50 years of daily returns, monthly block maxima
np.random.seed(0)
returns = np.random.standard_t(df=4, size=50*252) * 0.01
maxima_loss = block_maxima(-returns, 21)  # losses
xi, mu, sigma = fit_gev(maxima_loss)
print(f"GEV fit: xi={xi:.3f}, mu={mu:.4f}, sigma={sigma:.4f}")

# 100-year worst-month-loss return level
T = 100 * 12  # months
z_T = mu + sigma/xi * ((-np.log(1 - 1/T))**(-xi) - 1)
print(f"100-year monthly worst-loss return level: {z_T*100:.2f}%")
```

### Trade-offs of Block Maxima

Pros:
- Conceptually clean (one maximum per block).
- Maxima are approximately independent.
- Standard MLE machinery.

Cons:
- Wastes information — only one observation per block is used.
- Sensitive to block-size choice.
- Can miss multiple extreme events within the same block (cluster effect).

For these reasons, modern EVT practice prefers Peaks-Over-Threshold.

---

## Generalized Pareto Distribution (GPD)

Pickands–Balkema–de Haan theorem: if X has GEV-domain attraction, then for high threshold u, the conditional excesses Y = X − u | X > u follow approximately a Generalized Pareto Distribution:

$$
F_{\xi, \beta}(y) = 1 - \!\left(1 + \frac{\xi y}{\beta}\right)^{-1/\xi}, \qquad y > 0, \quad 1 + \xi y/\beta > 0.
$$

For ξ = 0, $F_{0, \beta}(y) = 1 - e^{-y/\beta}$ (exponential).

The shape parameter ξ is the same as in the GEV — they describe the same tail behavior. The scale β depends on the threshold: β = β(u). As u increases, β changes deterministically; ξ stays constant.

### MLE for GPD

Given exceedances {Y_1, …, Y_N} above threshold u, the log-likelihood is

$$
\ell(\xi, \beta) = -N \log \beta - (1 + 1/\xi) \sum_i \log\!\left(1 + \xi Y_i / \beta\right).
$$

For ξ = 0, $\ell = -N \log \beta - \sum_i Y_i / \beta$ (exponential MLE).

```python
import numpy as np
from scipy.stats import genpareto

def fit_gpd(exceedances):
    """Fit GPD via MLE."""
    c, loc, scale = genpareto.fit(exceedances, floc=0)
    return c, scale  # c = xi, scale = beta

np.random.seed(42)
returns = np.random.standard_t(df=4, size=10000) * 0.01
losses = -returns
threshold = np.quantile(losses, 0.95)
exceedances = losses[losses > threshold] - threshold
xi, beta = fit_gpd(exceedances)
print(f"GPD fit: xi={xi:.3f}, beta={beta:.4f}")
```

### Return Levels via GPD

If λ_u = ℙ(X > u) is the probability of exceedance, then the m-step return level (level exceeded on average every m steps) is

$$
x_m = u + \frac{\beta}{\xi} \!\left[ \!\left( m \lambda_u \right)^\xi - 1 \right].
$$

For ξ = 0: $x_m = u + \beta \log(m \lambda_u)$.

This formula is the workhorse of regulatory tail-risk computations.

### Why GPD Is Preferred

- Uses *all* the tail observations, not just the maximum per block.
- Threshold u can be chosen flexibly to balance bias and variance.
- Reduces to exponential tails (ξ = 0) or polynomial tails (ξ > 0) naturally.
- Standard tool for VaR and ES at high confidence levels.

### Reality Check — POT and Independence

GPD theory assumes iid exceedances. Real financial data has clustering: extreme days come in clusters (volatility regimes). Three fixes:

- **Declustering**: identify clusters of consecutive exceedances; use only the maximum per cluster as an "independent" event.
- **Run-length declustering**: define a cluster as exceedances separated by fewer than r non-exceedances; use the maximum.
- **POT with covariates**: explicitly model the time-varying nature of the threshold or scale.

In production, declustering is essential. Without it, GPD fits underestimate ξ (because clustered exceedances look like a single heavy tail).

---

## Peaks Over Threshold (POT)

Procedure:
1. Choose a high threshold u.
2. Extract exceedances above u.
3. (Optionally) decluster.
4. Fit GPD to exceedances.
5. Use fitted GPD for return-level and tail-quantile computations.

The two judgement calls — choosing u and choosing the declustering scheme — drive most of the variance in production POT estimates. We treat both next.

---

## Threshold Selection

Higher u → less bias (closer to true asymptotic GPD) but higher variance (fewer exceedances). Lower u → more data but more bias. Standard diagnostic plots:

### Mean Residual Life Plot

Plot the mean of exceedances above u as a function of u:

$$
e(u) = \mathbb{E}[X - u \mid X > u].
$$

For GPD with shape ξ < 1, $e(u) = (\beta + \xi u) / (1 - \xi)$ — *linear in u*. The threshold should be chosen where the empirical mean residual life becomes approximately linear.

```python
import numpy as np
import matplotlib.pyplot as plt

def mean_residual_life(losses, n_thresholds=50):
    thresholds = np.quantile(losses, np.linspace(0.5, 0.99, n_thresholds))
    mrl = np.array([(losses[losses > u] - u).mean() if (losses > u).sum() > 5 else np.nan for u in thresholds])
    se = np.array([(losses[losses > u] - u).std()/np.sqrt(max(1, (losses > u).sum())) if (losses > u).sum() > 5 else np.nan for u in thresholds])
    return thresholds, mrl, se

# Use it on synthetic data
np.random.seed(42)
losses = -np.random.standard_t(df=4, size=10000) * 0.01
thresholds, mrl, se = mean_residual_life(losses)
plt.errorbar(thresholds, mrl, yerr=1.96*se, fmt='o-')
plt.xlabel('threshold u'); plt.ylabel('E[X-u | X>u]')
plt.title('Mean residual life plot')
plt.grid(True); plt.tight_layout()
```

### Parameter Stability Plots

For a range of thresholds, fit GPD and plot ξ̂ and β̂* = β − ξu (the "modified scale," which should be constant across u under the model). The threshold is chosen where the parameter estimates stabilize.

### Hill Plot

For positive Fréchet-domain data, Hill estimator (next section) is:

$$
\hat \alpha_k = \!\left( \frac{1}{k} \sum_{i=1}^k \log X_{(n-i+1)} - \log X_{(n-k)} \right)^{-1},
$$

where X_{(1)} ≤ … ≤ X_{(n)} are order statistics. Plot $\hat\alpha_k$ against k. Choose k where the plot is approximately flat — the "Hill plateau."

### Automatic Methods

- **Beirlant et al. minimum-MSE**: minimize the MSE of the tail estimator over k.
- **Drees–Kaufmann–Resnick automatic threshold**: data-driven choice based on second-order regular variation.
- **Bootstrap-based**: resample to estimate the optimal threshold by minimizing variance.

In practice, choose threshold to retain 5–10% of observations (rule of thumb) and confirm via diagnostic plots. For 10000 daily observations, that's 500–1000 exceedances — enough for stable GPD estimation.

### Reality Check — Threshold Choice Is Half the Battle

Different threshold choices can yield different VaR estimates by 50% or more. Always:
- Report results for a range of thresholds.
- Show diagnostic plots in any analysis.
- Sensitivity-test downstream decisions to threshold choice.

---

## Hill Estimator

For Fréchet-domain data with positive support and tail index α = 1/ξ, the Hill (1975) estimator:

$$
\hat \alpha_k = \!\left( \frac{1}{k} \sum_{i=1}^k \log X_{(n-i+1)} - \log X_{(n-k)} \right)^{-1}.
$$

Or equivalently, $\hat \xi_k = 1/\hat \alpha_k = \frac{1}{k} \sum_{i=1}^k \log X_{(n-i+1)} - \log X_{(n-k)}$.

### Properties

- **Consistency**: under regular variation and k/n → 0 with k → ∞, $\hat \xi_k \to \xi$ a.s.
- **Asymptotic normality**: $\sqrt{k} (\hat \xi_k - \xi) \to \mathcal{N}(0, \xi^2)$.
- **Bias**: depends on second-order regular variation; bias-correction methods exist.
- **Optimal k**: balances bias (decreasing in k) and variance (decreasing in k). Optimal k ∝ n^{2/(1 + 2|ρ|)} where ρ is the second-order parameter.

```python
import numpy as np

def hill_estimator(x, k):
    """Hill estimator using the top k order statistics. x must be positive."""
    sorted_x = np.sort(x)[::-1]  # descending
    log_ratios = np.log(sorted_x[:k]) - np.log(sorted_x[k])
    return log_ratios.mean()

# Apply to simulated Pareto
np.random.seed(0)
x = np.random.pareto(2, size=10000) + 1  # alpha = 2 -> xi = 0.5
ks = np.arange(50, 2000, 50)
xi_hat = [hill_estimator(x, k) for k in ks]
import matplotlib.pyplot as plt
plt.plot(ks, xi_hat)
plt.axhline(0.5, color='r', linestyle='--', label='True ξ')
plt.xlabel('k'); plt.ylabel('Hill ξ̂')
plt.title('Hill plot — Pareto α=2')
plt.legend(); plt.grid(True); plt.tight_layout()
```

### Caveats

- Only works for Fréchet domain (ξ > 0).
- Sensitive to threshold (k) choice.
- Bias is severe in finite samples for some parent distributions.
- Variants (Pickands, moment estimator, DEdH) exist for the general ξ case.

### Reality Check — Hill Horror Plots

In real data, Hill plots are often not as flat as theory suggests. They wiggle, drift, or show structural breaks. The interpretation: the underlying data may not have stable tail behavior, or there is regime change. Always plot Hill across the whole tail and resist the temptation to cherry-pick a flat segment.

---

## Pickands Estimator and Moment Estimator

### Pickands (1975)

$$
\hat \xi_k^P = \frac{1}{\log 2} \log \frac{X_{(n-k)} - X_{(n-2k)}}{X_{(n-2k)} - X_{(n-4k)}}.
$$

Works for any ξ. Less efficient than Hill in the Fréchet domain but covers the full domain. High variance — typically not the first choice unless ξ < 0 is suspected.

### Dekkers-Einmahl-de Haan (DEdH) Moment Estimator

$$
\hat \xi^{DE} = M_n^{(1)} + 1 - \frac{1}{2}\!\left(1 - \frac{(M_n^{(1)})^2}{M_n^{(2)}}\right)^{-1},
$$

where $M_n^{(j)} = \frac{1}{k} \sum_{i=1}^k (\log X_{(n-i+1)} - \log X_{(n-k)})^j$. Covers full ξ range; performs well in practice for ξ > 0.

### Choice in Practice

For positive heavy tails (most financial losses), Hill is the default. For potentially light-tailed or bounded data, DEdH or full GPD MLE. Different estimators give different answers; diagnostic plots and bootstrap CIs are essential.

---

## Tail Index Estimation in Practice

For SPX daily returns, fit:

```python
import numpy as np
import yfinance as yf

# Get historical SPX returns (illustrative)
np.random.seed(42)
n = 8000  # ~32 years of daily returns
returns = np.random.standard_t(df=5, size=n) * 0.01  # synthetic

losses = -returns
losses_pos = losses[losses > 0]  # losses only

# Hill plot
ks = np.arange(20, len(losses_pos)//2, 5)
xi_hat = [hill_estimator(losses_pos, k) for k in ks]
# Identify plateau
import numpy as np
print(f"Hill ξ at k=100: {xi_hat[16]:.3f}")
print(f"Hill ξ at k=500: {xi_hat[96]:.3f}")
print(f"Hill ξ at k=1000: {xi_hat[196]:.3f}")
```

Empirical estimates for SPX:
- Daily losses: ξ ≈ 0.25–0.35 (left tail typically heavier than right).
- Right tail: ξ ≈ 0.15–0.25.
- Asymmetry: skew → tails differ.

For crypto (BTC, ETH):
- Both tails: ξ ≈ 0.4–0.6 — heavier than equity.
- Stable across regime breaks: tail index moves but stays in this range.

For FX (EUR/USD):
- ξ ≈ 0.05–0.15 — lighter tails than equity.
- Few large jumps under non-intervention.

---

## VaR and Expected Shortfall via EVT

Given a fitted GPD with parameters (ξ, β) above threshold u, with exceedance probability λ_u:

$$
\text{VaR}_p = u + \frac{\beta}{\xi} \!\left[ \!\left( \frac{n}{N_u} (1 - p) \right)^{-\xi} - 1 \right],
$$

where N_u is the number of exceedances. Equivalently,

$$
\text{VaR}_p = u + \frac{\beta}{\xi} \!\left[ \!\left( \frac{1 - p}{\lambda_u} \right)^{-\xi} - 1 \right].
$$

**Expected Shortfall** above VaR:

$$
\text{ES}_p = \frac{\text{VaR}_p}{1 - \xi} + \frac{\beta - \xi u}{1 - \xi},
$$

valid for ξ < 1. For ξ ≥ 1, ES is infinite — the distribution is so heavy-tailed that the conditional mean does not exist.

```python
import numpy as np
from scipy.stats import genpareto

def evt_var_es(losses, threshold_quantile=0.95, p=0.99):
    threshold = np.quantile(losses, threshold_quantile)
    exceedances = losses[losses > threshold] - threshold
    if len(exceedances) < 50:
        raise ValueError("Too few exceedances")
    xi, _, beta = genpareto.fit(exceedances, floc=0)
    lambda_u = (losses > threshold).mean()
    if abs(xi) < 1e-6:
        var_p = threshold + beta * np.log(lambda_u / (1 - p))
        es_p = var_p + beta
    else:
        var_p = threshold + beta/xi * (((1 - p)/lambda_u)**(-xi) - 1)
        es_p = var_p / (1 - xi) + (beta - xi*threshold) / (1 - xi)
    return var_p, es_p, xi

np.random.seed(42)
losses = -np.random.standard_t(df=4, size=10000) * 0.01
losses = losses[losses > -1]  # remove unphysical
var_99, es_99, xi = evt_var_es(losses, 0.95, 0.99)
print(f"EVT 99% VaR: {var_99*100:.2f}%, ES: {es_99*100:.2f}%, ξ: {xi:.3f}")

# Compare to historical
print(f"Empirical 99% loss: {np.quantile(losses, 0.99)*100:.2f}%")
```

### Comparison to Historical and Parametric VaR

For SPX daily returns, 99% VaR estimates typically:
- Gaussian parametric: 2.3% (sharply underestimates).
- Historical: 2.5% (depends on sample period).
- EVT POT: 2.7–3.0% (matches stress periods better).

For 99.9% (rare):
- Gaussian: 3.1%.
- Historical: 4–5% (highly sample-dependent).
- EVT POT: 4–6% with wide CI.

EVT extrapolates beyond the sample with formal asymptotic backing; historical/empirical methods do not.

### Confidence Intervals

For VaR estimates from EVT, derive CIs via:
- Profile likelihood (preferred).
- Delta method (asymptotic Gaussian).
- Bootstrap (block bootstrap to handle dependence).

Production should report VaR estimates *with* CIs, especially at high confidence levels where the point estimate alone is misleading.

### Reality Check — VaR Beyond Modeling

EVT VaR estimates assume:
- Stationarity within the estimation period.
- Independence of exceedances (after declustering).
- Correct domain of attraction.

Real markets have regime breaks. A pre-2008 EVT fit underestimated 2008 losses; a post-2008 fit may overestimate calm-period losses. Production systems use rolling-window EVT estimation with regime-aware adjustments.

---

## Multivariate Extremes and Tail Dependence

For two random variables X, Y, the **upper tail dependence coefficient** is

$$
\lambda_U = \lim_{u \to 1^-} \mathbb{P}(Y > F_Y^{-1}(u) \mid X > F_X^{-1}(u)).
$$

If λ_U > 0, the variables are **asymptotically dependent**: extreme moves in X coincide with extreme moves in Y. If λ_U = 0, they are **asymptotically independent**: extreme co-moves are rarer than the product of marginals would suggest.

Symmetrically, the **lower tail dependence**:

$$
\lambda_L = \lim_{u \to 0^+} \mathbb{P}(Y \le F_Y^{-1}(u) \mid X \le F_X^{-1}(u)).
$$

### Empirical Estimation

For positive correlation in equity markets, λ_L (joint downside) is typically larger than λ_U (joint upside) — the leverage effect at the joint level. Crypto pairs (BTC, ETH) have high tail dependence in both directions.

```python
import numpy as np

def empirical_tail_dependence(x, y, q=0.05, side='upper'):
    """Estimate tail dependence at threshold q."""
    n = len(x)
    if side == 'upper':
        rank_x = np.argsort(np.argsort(-x))
        rank_y = np.argsort(np.argsort(-y))
    else:
        rank_x = np.argsort(np.argsort(x))
        rank_y = np.argsort(np.argsort(y))
    threshold = int(q * n)
    return np.mean((rank_x < threshold) & (rank_y < threshold)) / q

np.random.seed(0)
n = 5000
# Joint t-distribution: high tail dependence
df = 4
z1 = np.random.standard_t(df, size=n)
z2 = 0.7*z1 + np.sqrt(1-0.49)*np.random.standard_t(df, size=n)
print(f"Empirical lower tail dependence: {empirical_tail_dependence(z1, z2, 0.05, 'lower'):.3f}")
print(f"Empirical upper tail dependence: {empirical_tail_dependence(z1, z2, 0.05, 'upper'):.3f}")
```

For Gaussian copula, λ_U = λ_L = 0 — Gaussian dependence is asymptotically independent. This is the formal flaw of using Gaussian-copula-based credit modeling, which played a role in the 2008 misestimation of correlated default risk. Document 207 covers copulas in depth.

### Multivariate Pareto and Logistic Models

Multivariate Generalized Pareto distributions exist (Falk–Hüsler 1991, Tawn 1990) but are less standardized than the univariate case. For practical use:
- Fit univariate margins via GPD.
- Combine via a copula (Gaussian, t, Archimedean, vine) — covered in document 207.

---

## Power Laws and Pareto Distributions

A random variable X has a **power-law (Pareto) distribution** if

$$
\mathbb{P}(X > x) = (x/x_{\min})^{-\alpha}, \qquad x \ge x_{\min}.
$$

Equivalently, $\log \mathbb{P}(X > x) = -\alpha \log x + \alpha \log x_{\min}$ — the famous "log-log linear" tail.

### MLE for Pareto

For data X_1, …, X_n with X_i ≥ x_min:

$$
\hat \alpha = \frac{n}{\sum_i \log(X_i / x_{\min})}.
$$

With variance $\hat\alpha^2 / n$.

### Log-Log Regression Pitfalls

Fitting log P(X > x) = constant − α log x via OLS *looks* attractive but has serious bias:
- Bias toward smaller α than true.
- Variance estimates are wrong (correlated residuals).
- Fits the body, not just the tail.

The right approach: MLE on the tail data only. Clauset, Shalizi, Newman (2009) provide a definitive treatment.

### Clauset-Shalizi-Newman (CSN) Test

CSN provide a procedure:
1. Estimate x_min via Kolmogorov–Smirnov minimization (find x_min where empirical CDF matches Pareto best).
2. Estimate α via MLE on data above x_min.
3. Test goodness-of-fit via simulation-based KS test.
4. Compare to alternative distributions (lognormal, exponential, stretched exponential) via likelihood ratio.

Empirical findings using CSN:
- Many "power laws" in the literature do not survive rigorous testing.
- Lognormal often fits "power-law" data as well or better.
- True power laws are rarer than commonly claimed but do exist (city sizes, word frequencies, some financial returns).

```python
import numpy as np

def pareto_mle(data, x_min):
    tail = data[data >= x_min]
    if len(tail) == 0:
        return np.nan
    return len(tail) / np.sum(np.log(tail / x_min))

def csn_xmin(data, n_xmins=50):
    """Find x_min minimizing KS distance."""
    xmins = np.unique(data)[::-1][:n_xmins]
    best_ks, best_xmin = np.inf, xmins[0]
    for xmin in xmins:
        tail = data[data >= xmin]
        if len(tail) < 50:
            continue
        alpha = pareto_mle(data, xmin)
        # Empirical CDF vs theoretical
        sorted_tail = np.sort(tail)
        ecdf = np.arange(1, len(tail)+1) / len(tail)
        tcdf = 1 - (sorted_tail / xmin)**(-alpha)
        ks = np.max(np.abs(ecdf - tcdf))
        if ks < best_ks:
            best_ks, best_xmin = ks, xmin
    alpha = pareto_mle(data, best_xmin)
    return best_xmin, alpha, best_ks

np.random.seed(0)
data = np.random.pareto(2, 5000) + 1  # alpha = 2, xmin = 1
xmin, alpha, ks = csn_xmin(data)
print(f"Estimated x_min: {xmin:.3f}, α: {alpha:.3f}, KS: {ks:.4f}")
```

### Power Laws in Finance

Empirical evidence:
- Returns: power law in tails with α ≈ 3–4 for equity, 2–3 for crypto.
- Trade sizes: power law with α ≈ 1.5.
- Stock market capitalizations: power law (Pareto principle).
- Wealth distribution: power law with α ≈ 1.5–2.

Mandelbrot (1963) was an early proponent of stable distributions for returns. Modern view: returns have power-law tails but with finite variance (α > 2), so not truly Lévy stable. The distinction matters: Lévy stable has infinite variance and would invalidate most CLT-based methods.

---

## Heavy Tails in Trading Data

Empirical estimates of α (tail index, equivalent to 1/ξ) across asset classes:

| Asset | Daily ret. | Intraday | Notes |
|---|---|---|---|
| SPX | 3-4 | 4-5 | Variance finite; 4-th moment usually finite |
| US Treasuries | 4-6 | 5-6 | Lighter tails |
| EUR/USD | 4-5 | 5-6 | Light tails |
| BTC | 2-3 | 2-3 | Heavy; 4-th moment may not exist |
| Small cap | 2.5-3.5 | 3-4 | Heavier than large cap |
| EM equities | 2.5-3.5 | 3-4 | Heavier |
| Bond futures | 4-5 | 5-6 | Light |
| Gold | 3.5-4.5 | 4-5 | Moderate |
| Crude oil | 3-4 | 3.5-4.5 | Moderate-heavy |

### Time-Varying Tails

Tail index is not constant. During calm periods, α can be 5+; during crises, α drops to 2-3. Rolling estimation:

```python
import numpy as np

def rolling_hill(losses, window=500, k=50):
    """Rolling Hill estimator."""
    n = len(losses)
    result = np.full(n, np.nan)
    for t in range(window, n):
        x = losses[t-window:t]
        x_pos = x[x > 0]
        if len(x_pos) > k:
            result[t] = 1 / hill_estimator(x_pos, k)
    return result
```

Plotting rolling α over decades shows clear regime structure: low α (heavy tails) during 2008, 2020, 2022; high α (lighter tails) during 2003-2007, 2013-2017.

---

## Tail Risk Hedging

Strategies to protect against tail events:

### OTM Put Programs

Buy 5-10% OTM SPX puts. Cost: small fraction of portfolio per year (typically 0.5-2% drag). Payoff: large in tail events.

EVT pricing: given α and current vol, the OTM put's expected payoff and variance are computed from the GPD-tail. The hedge ratio (fraction of portfolio to spend on puts) trades off expected drag against tail protection.

### Variance Swaps

A variance swap pays the realized variance over T minus the variance strike. Long variance swap protects against vol-up events (which typically coincide with crashes).

### Tail-Risk Parity (Universa-style)

Mark Spitznagel's strategy: a small fraction (e.g., 3%) of the portfolio in OTM puts; the rest in passive index. Total return is similar to passive in calm periods; significantly outperforms in crashes.

The economics: if tail events have a probability higher than option-implied, the strategy is positive expected value. Empirically, OTM puts on equity indices are *over*priced (variance risk premium), so the strategy has negative expected drag — a controversial point.

### CTAs as Implicit Tail Hedge

Trend-following CTAs are correlated with crisis returns (cash flows from short positions during crashes). Document 89 (Crisis Alpha VIX Trend) covers this explicitly.

### Reality Check — Hedging Costs Matter

Tail-risk hedging programs cost real money. Sustained over decades, they can underperform pure equity by 1-3% per year. The decision: accept lower expected returns for protected drawdowns, or accept volatility for higher expected returns.

The right answer depends on the investor's loss-aversion utility and on the joint distribution of returns and consumption needs (e.g., a foundation that distributes 5% of assets annually faces different tail risk than a young saver).

---

## Backtesting with EVT

Standard VaR backtest: count exceedances over the test period, compare to expected count.

### Kupiec (1995) Test

For VaR at confidence p, expected number of exceedances in n observations is n(1-p). Observed number of exceedances has a binomial distribution. Test:

$$
LR_K = -2 \log \frac{(1-p)^{n_e} p^{n - n_e}}{(\hat p)^{n_e} (1 - \hat p)^{n - n_e}},
$$

where n_e is observed exceedances and $\hat p = n_e / n$. Under the null, LR ~ χ²(1).

### Christoffersen (1998) Conditional Coverage

Tests whether exceedances are independent in time as well as occurring at the right rate. The test combines Kupiec with a test of zero autocorrelation in the exceedance indicator.

### Berkowitz (2001)

Tests the entire predictive distribution, not just the tail. Useful for checking whether the EVT model is correct everywhere, not just at the threshold.

### Reality Check — Backtesting Power

VaR backtesting has low power: even with 5 years of daily data (1260 obs) and true VaR shifted by 50%, detection probability is ~50%. Exceedance counts are variable; one or two runs of bad luck can produce many exceedances even when the model is correct.

The right approach: combine multiple tests, examine clustering, and accept a degree of subjective judgment in model validation.

---

## Stable Distributions and α-Stable Processes

A random variable X is **α-stable** (Lévy-stable) if for any positive a, b, there exist c, d such that

$$
aX_1 + bX_2 \stackrel{d}{=} cX + d,
$$

for X_1, X_2 iid copies of X.

Characteristic function:

$$
\phi(t) = \exp\!\left[ i\delta t - \gamma^\alpha |t|^\alpha (1 + i\beta \text{sgn}(t) \omega(t, \alpha)) \right],
$$

with α ∈ (0, 2], β ∈ [-1, 1], γ > 0, δ ∈ ℝ. ω is a known function depending on α.

Special cases:
- α = 2: Gaussian.
- α = 1, β = 0: Cauchy.
- α = 1/2, β = 1: Lévy.

For α < 2, variance is *infinite*. For α ≤ 1, mean is also infinite.

### Mandelbrot's Hypothesis

Mandelbrot (1963) proposed α-stable returns with α ≈ 1.7 for cotton prices. Subsequent work showed:
- Empirical α from extreme-value methods: typically 3-4 for equity.
- α-stable would have α < 2.
- The discrepancy: Mandelbrot's estimator was biased toward small α; α-stable does not fit.

Modern view: returns have *power-law tails* (heavy) but *finite variance* (α > 2). They are not α-stable. EVT with ξ in (0, 0.5) is the right description.

### Why It Matters

- α-stable would invalidate CLT for sums; finite-variance heavy tails do not.
- Variance-based methods (Sharpe, Markowitz) fail for α-stable; they degrade for finite-variance heavy tails.
- Practical impact: methods can use finite variances cautiously.

---

## Long Memory and Hurst Exponent

A time series has **long memory** if its autocorrelation decays slower than exponentially:

$$
\rho(k) \sim C k^{-(1 - 2H)}, \qquad k \to \infty,
$$

where H ∈ (0, 1) is the **Hurst exponent**. For H = 1/2, no long memory (e.g., Brownian motion). For H > 1/2, persistence. For H < 1/2, anti-persistence.

### R/S Analysis

Hurst's original method: compute the rescaled range R/S over windows of length n; plot log(R/S) vs log(n); slope is H.

```python
import numpy as np

def rs_hurst(x, max_n=None):
    """Estimate Hurst exponent via R/S analysis."""
    if max_n is None:
        max_n = len(x) // 4
    ns = np.unique(np.round(np.logspace(2, np.log10(max_n), 30)).astype(int))
    rss = []
    for n in ns:
        n_chunks = len(x) // n
        chunk_rs = []
        for i in range(n_chunks):
            chunk = x[i*n:(i+1)*n]
            mean = chunk.mean()
            cum_dev = np.cumsum(chunk - mean)
            R = cum_dev.max() - cum_dev.min()
            S = chunk.std(ddof=1)
            if S > 0:
                chunk_rs.append(R/S)
        if chunk_rs:
            rss.append(np.mean(chunk_rs))
    rss = np.array(rss)
    valid = rss > 0
    H, _ = np.polyfit(np.log(ns[valid]), np.log(rss[valid]), 1)
    return H

np.random.seed(42)
# fBM with H = 0.7
from scipy.signal import fftconvolve
n = 4096
H = 0.7
# Davies-Harte / Cholesky for fBM
def fbm(n, H):
    # Approximate via FFT
    grid = np.linspace(0, 1, n)
    cov = 0.5*(np.abs(grid[:, None])**(2*H) + np.abs(grid[None, :])**(2*H) - np.abs(grid[:, None] - grid[None, :])**(2*H))
    L = np.linalg.cholesky(cov + 1e-10*np.eye(n))
    return L @ np.random.normal(size=n)

x = fbm(n, H=0.7)
H_hat = rs_hurst(x)
print(f"True H = 0.7, R/S estimate = {H_hat:.3f}")
```

### Detrended Fluctuation Analysis (DFA)

A more robust alternative to R/S, less sensitive to non-stationarity:

1. Integrate the series.
2. Detrend in non-overlapping windows.
3. Compute RMS of residuals as function of window size.
4. Slope of log RMS vs log window = α (related to H).

For volatility series in equities, H ≈ 0.7-0.9 (long memory). For returns themselves, H ≈ 0.5 (no long memory). For *log* volatility, H ≈ 0.07-0.13 (rough volatility, document 202).

---

## Self-Organized Criticality and Crisis Dynamics

Bak–Tang–Wiesenfeld (1987) sandpile model: a system that naturally evolves to a state where small perturbations can cause arbitrarily large avalanches. Distribution of avalanche sizes follows a power law.

### Application to Markets

Argument: financial markets are SOC systems. The leverage cycle, crowding into trades, and feedback loops create conditions where small triggers (margin calls, news) can cause arbitrarily large cascades.

### Empirical Tests

- Distribution of drawdown sizes follows approximate power law.
- Avalanche dynamics in margin call cascades (LTCM 1998, Lehman 2008).
- Liquidation cascades in crypto follow similar dynamics.

The SOC framework is more a *metaphor* than a calibrated model in finance, but it provides intuition for why "rare" events can be inevitable in coupled systems.

---

## Software and Code

### Python

- **scipy.stats.genextreme, genpareto**: standard GEV/GPD MLE.
- **scipy.stats.levy_stable**: Lévy stable distribution (slow).
- **evt-py, scikit-extremes**: dedicated EVT libraries.
- **fathon**: DFA, multifractal analysis.

### R

- **evd, evir, ismev, POT**: comprehensive EVT toolkits.
- **extRemes**: GEV with covariates.

### Production

In bank risk systems, EVT estimation is typically run nightly or weekly:
- Refit GPD on rolling window of recent data.
- Compute VaR/ES at multiple confidence levels.
- Compare to backtested exceedance counts.
- Generate stress scenarios beyond historical extremes.

---

## Case Studies

### 1987 Crash

October 19, 1987: SPX dropped 20.5% in one day. Pre-1987 EVT fits using 1962-1986 data:
- ξ ≈ 0.2 (moderate heavy tail).
- 100-year return level: −15% to −20%.

The 1987 crash was within the EVT projected return level. A Gaussian-based VaR would have priced this as essentially impossible.

### 1998 LTCM

Russia default and LTCM crisis. Cross-asset correlations went to 1; bond-stock relationships broke. EVT for individual asset tails was correctly heavy; but multivariate tail dependence was underestimated.

### 2008 Crisis

Lehman week: SPX dropped 20% over 4 days. Pre-2008 EVT fits: 100-year drawdown ≈ 40%. Realized: 56% peak-to-trough. EVT was approximately right but volatility regime change made calibration unstable.

### 2020 COVID

March 2020: SPX dropped 34% in 23 days. Then rallied. EVT fits: realized drawdown was within a 50-year envelope.

### 2022 LDI Crisis

UK gilt yields spiked 100bps in days. Pension liability hedges (LDI) faced margin calls; cascading liquidation. Sovereign bond market: tail event of α ≈ 2.5 magnitude.

---

## Reality Checks

- **Tail estimation requires care**: k/threshold choice matters; bootstrap CIs essential.
- **Independence assumption is violated**: declustering needed.
- **Non-stationarity**: regime changes break stationarity.
- **Extrapolation has limits**: 1000-year return level estimates from 100 years of data are mostly fiction.
- **Multivariate is harder than univariate**: tail dependence requires copula machinery.
- **Model risk dominates parameter risk**: choosing GPD vs lognormal vs Weibull matters more than precise α.

---

## Reference Tables, Cheat Sheets, Bibliography

### EVT Cheat Sheet

| Quantity | Formula |
|---|---|
| GEV CDF | $\exp[-(1+\xi(x-\mu)/\sigma)^{-1/\xi}]$ |
| GPD CDF (excesses) | $1 - (1+\xi y/\beta)^{-1/\xi}$ |
| GPD VaR | $u + (\beta/\xi)[((1-p)/\lambda_u)^{-\xi} - 1]$ |
| GPD ES | $\text{VaR}/(1-\xi) + (\beta - \xi u)/(1-\xi)$ |
| Hill estimator | $(1/k) \sum \log(X_{(n-i+1)}/X_{(n-k)})$ |
| Tail index α | 1/ξ |
| Variance finite if | ξ < 1/2 (α > 2) |
| Mean finite if | ξ < 1 (α > 1) |
| Asymptotic normality | $\sqrt k (\hat \xi_k - \xi) \to \mathcal{N}(0, \xi^2)$ |

### Tail Index Quick Reference

| Asset | α (typical) | Interpretation |
|---|---|---|
| Gaussian | ∞ | All moments |
| US Treasury | 4-6 | Light, finite all moments |
| FX major | 4-5 | Light |
| SPX | 3-4 | Moderate |
| Single stocks | 2.5-3.5 | Heavier |
| BTC, ETH | 2-3 | Very heavy |
| Lévy stable α=1.7 | 1.7 | Infinite variance |

### Bibliography

- **Embrechts, P., Klüppelberg, C., Mikosch, T. (1997), *Modelling Extremal Events*, Springer.** The standard reference.
- **McNeil, A., Frey, R., Embrechts, P. (2015), *Quantitative Risk Management*, Princeton.** Practitioner-oriented.
- **Coles, S. (2001), *An Introduction to Statistical Modeling of Extreme Values*, Springer.** Accessible.
- **Resnick, S. (2007), *Heavy-Tail Phenomena*, Springer.** Comprehensive theory.
- **Hill, B. (1975), "A Simple General Approach to Inference about the Tail of a Distribution", *Annals of Statistics* 3(5): 1163–1174.**
- **Pickands, J. (1975), "Statistical Inference Using Extreme Order Statistics", *Annals of Statistics* 3: 119–131.**
- **Clauset, A., Shalizi, C., Newman, M. (2009), "Power-Law Distributions in Empirical Data", *SIAM Review* 51(4): 661–703.**
- **Mandelbrot, B. (1963), "The Variation of Certain Speculative Prices", *Journal of Business* 36(4): 394–419.**
- **Taleb, N. (2007), *The Black Swan*, Random House.** Popular but influential.
- **Kupiec, P. (1995), "Techniques for Verifying the Accuracy of Risk Measurement Models", *Journal of Derivatives* 3(2): 73–84.** VaR backtesting.
- **Christoffersen, P. (1998), "Evaluating Interval Forecasts", *International Economic Review* 39(4): 841–862.** Conditional coverage.
- **Bak, P., Tang, C., Wiesenfeld, K. (1987), "Self-Organized Criticality", *Phys. Rev. Lett.* 59: 381–384.** SOC.

### Cross-References

- Document 200 — Stochastic Calculus.
- Document 201 — Microstructure.
- Document 207 — Copulas.
- Document 211 — Backtesting.
- Document 218 — Hedge Fund Risk Operations.
- Document 86 — Tail Risk Hedging Universa.
- Document 89 — Crisis Alpha VIX Trend.

---

*End of document 206. ~1,400 lines.*
