# 203 — Bayesian Methods and Probabilistic Programming for Trading

> Bayesian inference, MCMC, particle filters, Hidden Markov Models, Kalman filtering, and probabilistic programming applied to trading. Covers theory, computational methods (PyMC, Stan, Pyro, NumPyro), and concrete trading applications: parameter inference under uncertainty, regime detection, risk modeling, and execution. Self-contained; assumes only the prerequisites of document 200.

---

## Table of Contents

1. [Why Bayesian for Trading](#why-bayesian)
2. [Bayes' Rule, Posteriors, and the Mechanics of Updating](#bayes-rule)
3. [Conjugate Priors — The Workhorse Cases](#conjugate-priors)
4. [Markov Chain Monte Carlo](#mcmc)
5. [Hamiltonian Monte Carlo and the No-U-Turn Sampler](#hmc-nuts)
6. [Variational Inference](#variational-inference)
7. [Kalman Filter — Linear Gaussian State Space](#kalman-filter)
8. [Extended and Unscented Kalman Filters](#ekf-ukf)
9. [Particle Filtering](#particle-filtering)
10. [Hidden Markov Models](#hmm)
11. [Regime-Switching Models](#regime-switching)
12. [Bayesian Linear Regression — Trading Application](#bayesian-regression)
13. [Bayesian Hierarchical Models for Cross-Sectional Returns](#hierarchical-models)
14. [Bayesian Optimization for Hyperparameter Tuning](#bayesian-optimization)
15. [Probabilistic Programming Languages — PyMC, Stan, Pyro](#ppl)
16. [Posterior Predictive Checks and Model Validation](#posterior-predictive)
17. [Bayesian Risk Modeling — VaR, ES, Drawdown](#bayesian-risk)
18. [Online Bayesian Inference and Sequential Monte Carlo](#online-bayes)
19. [Reality Checks and Production Pitfalls](#reality-checks)
20. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Why Bayesian for Trading

Frequentist statistics treats parameters as fixed unknowns and gives confidence intervals based on the distribution of estimators across hypothetical repeated samples. In trading, this framework is awkward. We have *one* sample (the realized history of the market), and the parameters we care about (volatilities, mean returns, regime probabilities, model parameters) are not constants — they evolve. A confidence interval for the Sharpe ratio of a strategy, computed from one realization, says nothing useful about the next year's Sharpe.

Bayesian statistics treats parameters as random variables with prior distributions, updated by observed data into posteriors. This framework matches the trader's epistemic situation: we have beliefs (priors), we observe data (today's market), we update beliefs (posteriors), and we make decisions (allocations, hedges, trades) based on the updated beliefs. The Bayesian framework also handles uncertainty in nested layers: uncertainty about a model parameter, uncertainty about the model itself, uncertainty about the regime, all combined coherently.

Three classes of trading applications dominate Bayesian methods:

1. **Parameter inference under uncertainty.** Estimating volatility, correlation, betas, and factor loadings with proper accounting for sampling error. The Bayesian estimate has built-in shrinkage toward priors, which is exactly what is needed for noisy data.

2. **Regime detection and online learning.** Markets switch between regimes (low-vol vs high-vol, trending vs mean-reverting). Hidden Markov Models, particle filters, and online Bayesian inference give principled methods for inferring the current regime in real time.

3. **Decision-making under uncertainty.** When deploying a strategy, the optimal allocation depends not on point estimates of parameters but on the full posterior distribution. Bayesian decision theory gives the right framework: maximize expected utility under the posterior.

This document is application-driven. Theory is given where it is needed for code; code is given where it is needed for trading. Wherever a Bayesian method has a frequentist counterpart, we draw the comparison and discuss when one is preferable.

A note on philosophy. Bayesian methods are sometimes criticized for "subjectivity" of the prior. In trading, this criticism has it backwards: every model carries assumptions, and the Bayesian framework makes those assumptions explicit and testable via prior sensitivity analysis. The frequentist alternative is to bury the same assumptions in the choice of estimator, the choice of confidence level, and the asymptotic regime — equally subjective, less transparent.

---

## Bayes' Rule, Posteriors, and the Mechanics of Updating

The foundational identity: for any two events A, B with positive probability,

$$
\mathbb{P}(A \mid B) = \frac{\mathbb{P}(B \mid A) \, \mathbb{P}(A)}{\mathbb{P}(B)}.
$$

For a parameter θ and observed data D, the **posterior** is

$$
p(\theta \mid D) = \frac{p(D \mid \theta) \, p(\theta)}{p(D)},
$$

where p(θ) is the **prior**, p(D | θ) is the **likelihood**, and p(D) = ∫ p(D | θ) p(θ) dθ is the **marginal likelihood** (also called evidence). The posterior p(θ | D) summarizes everything we know about θ after observing D.

In words: posterior ∝ likelihood × prior. The marginal likelihood normalizes; if we are only interested in the shape of the posterior, we can drop it.

### Trading Example: Estimating Sharpe Ratio

Suppose monthly returns r_t are iid 𝒩(µ, σ²). We have observed n = 60 months of data with sample mean r̄ = 0.005 and sample standard deviation s = 0.04. We want the posterior over Sharpe = µ √12/σ.

With the conjugate Normal-Inverse-Gamma prior:
$$
\mu \mid \sigma^2 \sim \mathcal{N}(\mu_0, \sigma^2/\kappa_0), \qquad \sigma^2 \sim \text{InvGamma}(\alpha_0, \beta_0).
$$

Posterior parameters:
$$
\mu_n = \frac{\kappa_0 \mu_0 + n \bar r}{\kappa_0 + n}, \quad \kappa_n = \kappa_0 + n,
$$
$$
\alpha_n = \alpha_0 + n/2, \quad \beta_n = \beta_0 + \tfrac{1}{2}\!\left[ \sum (r_t - \bar r)^2 + \frac{n \kappa_0}{\kappa_0 + n}(\bar r - \mu_0)^2 \right].
$$

Sampling Sharpe from the posterior:

```python
import numpy as np
from scipy.stats import invgamma, norm

np.random.seed(42)
n, r_bar, s = 60, 0.005, 0.04
mu0, kappa0, alpha0, beta0 = 0.0, 1.0, 2.0, 0.001

mu_n = (kappa0*mu0 + n*r_bar)/(kappa0 + n)
kappa_n = kappa0 + n
alpha_n = alpha0 + n/2
beta_n = beta0 + 0.5*((n-1)*s**2 + n*kappa0/(kappa0+n)*(r_bar - mu0)**2)

n_draws = 100_000
sigma2_post = invgamma.rvs(alpha_n, scale=beta_n, size=n_draws)
mu_post = mu_n + np.sqrt(sigma2_post/kappa_n) * np.random.normal(size=n_draws)
sharpe_post = mu_post * np.sqrt(12) / np.sqrt(sigma2_post)

print(f"Posterior Sharpe: mean={sharpe_post.mean():.3f}, "
      f"5%={np.percentile(sharpe_post, 5):.3f}, "
      f"95%={np.percentile(sharpe_post, 95):.3f}")
```

The posterior 90% credible interval might be [-0.2, 1.8] — telling you that 60 months of data are not enough to confidently distinguish a Sharpe of zero from a Sharpe of 1.5. This honest uncertainty is exactly what point estimates hide.

### Bayesian Decision Theory

Given a loss function L(action, θ), the Bayes decision minimizes expected posterior loss:

$$
a^* = \arg\min_a \int L(a, \theta) p(\theta \mid D) \, d\theta.
$$

For squared-error loss, a* = posterior mean. For absolute loss, a* = posterior median. For 0–1 loss, a* = posterior mode (MAP).

In trading, the relevant loss is typically a *utility* (negative loss): expected utility under the posterior. For Kelly-style sizing under a utility u(W),

$$
f^* = \arg\max_f \int u(W(f, \theta)) p(\theta \mid D) \, d\theta,
$$

where W is wealth as a function of bet size f and the unknown parameter θ. This naturally accounts for parameter uncertainty: you bet less when uncertain. Document 41 (Kelly Criterion) covers the theory; the Bayesian extension is the posterior expectation rather than a point estimate.

### Reality Check — Priors That Are Actually Informative

A common error: using "uninformative" priors that are actually informative on the wrong scale. For example, a flat prior on a variance parameter implicitly says σ² is uniformly distributed on [0, ∞), which is improper and biases toward large values. The same flat prior on log σ² is informative on the variance scale.

Best practice: choose priors that are **weakly informative on the scale of interest**, calibrated to the units of the data. For SPX monthly returns, prior mean σ ∈ 𝒩(0.04, 0.02²) is reasonable; flat or "non-informative" is not.

---

## Conjugate Priors — The Workhorse Cases

A prior is **conjugate** to a likelihood if the posterior belongs to the same family as the prior. Conjugate pairs make the algebra of updating closed-form, eliminating the need for sampling. They are the right starting point for understanding Bayesian updating, even though most production models use non-conjugate priors and require numerical methods.

### Beta–Bernoulli

For Bernoulli data with probability θ, the Beta prior is conjugate:

$$
\theta \sim \text{Beta}(\alpha, \beta), \qquad y_i \sim \text{Bernoulli}(\theta).
$$

After observing k successes in n trials:

$$
\theta \mid y \sim \text{Beta}(\alpha + k, \beta + n - k).
$$

Trading use: estimating the win rate of a strategy. With α = β = 1 (uniform prior), after 100 trades with 55 wins, the posterior is Beta(56, 46) with mean 0.549 and 90% CI [0.473, 0.621]. The CI is roughly ±5 percentage points after 100 trades — much wider than a naive frequentist would assume.

### Normal–Normal (Known Variance)

For y ∼ 𝒩(µ, σ²) with known σ², a Normal prior on µ is conjugate:

$$
\mu \sim \mathcal{N}(\mu_0, \tau_0^2).
$$

After observing y_1, …, y_n with sample mean ȳ:

$$
\mu \mid y \sim \mathcal{N}\!\left(\frac{\mu_0/\tau_0^2 + n\bar y/\sigma^2}{1/\tau_0^2 + n/\sigma^2}, \frac{1}{1/\tau_0^2 + n/\sigma^2}\right).
$$

The posterior mean is a precision-weighted average of the prior mean and the sample mean. This is "shrinkage" — the posterior is pulled toward the prior, more strongly when the sample is small or the prior is tight.

Trading use: estimating return mean with conviction-weighted shrinkage toward zero. With prior 𝒩(0, 0.01²) and 12 monthly returns averaging 0.005 with σ = 0.04, the posterior mean is approximately 0.0006 — heavily shrunk toward zero. The right story: in 12 months we cannot distinguish a true mean of 0.005 from zero.

### Normal–Inverse-Gamma (Unknown Variance)

The full conjugate prior for a Gaussian with unknown mean and variance is the Normal–Inverse-Gamma:

$$
\mu \mid \sigma^2 \sim \mathcal{N}(\mu_0, \sigma^2/\kappa_0), \quad \sigma^2 \sim \text{InvGamma}(\alpha_0, \beta_0).
$$

This is the prior used in the Sharpe-ratio example. The posterior is also Normal–Inverse-Gamma, with parameters as given above.

### Gamma–Poisson

For y ∼ Poisson(λ), the Gamma prior on λ is conjugate:

$$
\lambda \sim \text{Gamma}(\alpha, \beta), \qquad \lambda \mid y \sim \text{Gamma}(\alpha + \sum y, \beta + n).
$$

Trading use: estimating arrival rates of trades, news events, or stop-outs. With α = β = 1 and 30 trades observed in one minute, the posterior is Gamma(31, 2), giving λ̂ ≈ 15.5 trades/sec with 90% CI [11, 21].

### Dirichlet–Multinomial

For multinomial outcomes (e.g., regime probabilities), the Dirichlet is conjugate:

$$
(\pi_1, \ldots, \pi_K) \sim \text{Dirichlet}(\alpha_1, \ldots, \alpha_K),
$$
$$
(\pi_1, \ldots, \pi_K) \mid n_1, \ldots, n_K \sim \text{Dirichlet}(\alpha_1 + n_1, \ldots, \alpha_K + n_K).
$$

Trading use: prior over regime probabilities updated by counts of past regimes.

### Conjugate Limitations

Conjugate priors are convenient but restrictive. They force a specific shape of the prior. For complex models (state-space, hierarchical, mixture), conjugacy is rarely available, and we need MCMC.

---

## Markov Chain Monte Carlo

When the posterior cannot be computed in closed form, we sample from it. MCMC builds a Markov chain whose stationary distribution is the target posterior, then runs the chain to draw samples.

### Metropolis–Hastings

The simplest MCMC algorithm. Starting from θ_0:

1. Propose θ' from a proposal distribution q(θ' | θ_t).
2. Compute the acceptance ratio:
$$
\alpha = \min\!\left(1, \frac{p(\theta' \mid D) \, q(\theta_t \mid \theta')}{p(\theta_t \mid D) \, q(\theta' \mid \theta_t)}\right).
$$
3. With probability α, set θ_{t+1} = θ'; else θ_{t+1} = θ_t.

The trick: we only need the unnormalized posterior p(D | θ) p(θ), not the marginal likelihood. The ratio in α cancels the normalizing constants.

For symmetric proposals q(θ' | θ) = q(θ | θ'), the acceptance ratio simplifies to the Metropolis ratio:

$$
\alpha = \min\!\left(1, \frac{p(\theta' \mid D)}{p(\theta_t \mid D)}\right).
$$

```python
import numpy as np
np.random.seed(42)

def metropolis_hastings(log_post, x0, n_samples, prop_sd=0.1):
    samples = np.zeros(n_samples)
    x = x0
    log_p = log_post(x)
    n_accept = 0
    for i in range(n_samples):
        x_prop = x + np.random.normal(0, prop_sd)
        log_p_prop = log_post(x_prop)
        if np.log(np.random.rand()) < log_p_prop - log_p:
            x, log_p = x_prop, log_p_prop
            n_accept += 1
        samples[i] = x
    return samples, n_accept/n_samples

# Example: posterior of SPX volatility under exponential prior
def log_post(sigma, returns, prior_rate=10):
    if sigma <= 0:
        return -np.inf
    log_lik = -0.5*np.sum(returns**2)/sigma**2 - len(returns)*np.log(sigma)
    log_prior = np.log(prior_rate) - prior_rate*sigma
    return log_lik + log_prior

returns = np.random.normal(0, 0.02, 100)  # synthetic
samples, accept = metropolis_hastings(lambda s: log_post(s, returns), x0=0.02, n_samples=10_000)
print(f"Acceptance: {accept:.3f}; posterior mean σ: {samples[1000:].mean():.4f}")
```

### Mixing and Convergence

MCMC has known issues:
- **Burn-in**: early samples are biased by the starting point. Discard the first ~20% of samples.
- **Autocorrelation**: consecutive samples are correlated. Effective sample size (ESS) is much smaller than N.
- **Multimodality**: the chain can get stuck in one mode of a multi-modal posterior. Mitigate by starting multiple chains from different initial points.
- **Tuning**: proposal scale matters. Too small → high acceptance, slow mixing. Too large → low acceptance, slow mixing. Target ~25% for high-dimensional, ~45% for low-dimensional.

Convergence diagnostics:
- **R-hat (Gelman–Rubin)**: ratio of within-chain to between-chain variance. R-hat < 1.05 indicates convergence.
- **Effective Sample Size**: 1000+ ESS typically required for stable inference.
- **Trace plots**: visual inspection of chain trajectories.

### Gibbs Sampling

For multivariate posteriors with tractable conditional distributions, **Gibbs sampling** updates each parameter conditional on the others:

```
For each iteration:
    Sample θ_1 from p(θ_1 | θ_2, ..., θ_K, D)
    Sample θ_2 from p(θ_2 | θ_1, θ_3, ..., θ_K, D)
    ...
    Sample θ_K from p(θ_K | θ_1, ..., θ_{K-1}, D)
```

Each conditional update is a one-dimensional sampling problem. For conjugate models, the conditionals are closed-form, and Gibbs is very fast.

### Reality Check — MCMC in Production

MCMC for a moderate-dimensional trading model (say, 50 parameters, 1000 observations) takes seconds to minutes. For high-dimensional or hierarchical models, hours to days. Production systems typically:
- Use MCMC offline for periodic parameter estimation.
- Use simpler online updates (Kalman, particle filter) for real-time inference.
- Cache MCMC results and re-run only when the data window changes substantially.

The advantage of MCMC over point estimation is the *full posterior*: confidence intervals, joint distributions, and tail probabilities. The cost is computational; the benefit is honesty about uncertainty.

---

## Hamiltonian Monte Carlo and the No-U-Turn Sampler

Standard Metropolis–Hastings has poor scaling: as dimensionality grows, acceptance rates drop and chains mix slowly. **Hamiltonian Monte Carlo** (HMC) uses gradient information to make better proposals.

### The Idea

Augment the parameter θ with a momentum variable r ∼ 𝒩(0, M). Define the Hamiltonian H(θ, r) = U(θ) + K(r), where U(θ) = −log p(θ | D) is the "potential energy" and K(r) = ½ rᵀ M⁻¹ r is the "kinetic energy."

To propose a new θ:
1. Sample r ∼ 𝒩(0, M).
2. Simulate Hamiltonian dynamics for time τ via the leapfrog integrator.
3. Accept the new (θ', r') with probability min(1, exp(H(θ, r) − H(θ', r'))).

Hamiltonian dynamics conserve the joint H, so the acceptance is high (typically >80%) when the integrator is accurate. The chain travels long distances in parameter space efficiently.

### Leapfrog Integrator

The leapfrog scheme:
$$
r_{t+\epsilon/2} = r_t - (\epsilon/2) \nabla U(\theta_t),
$$
$$
\theta_{t+\epsilon} = \theta_t + \epsilon M^{-1} r_{t+\epsilon/2},
$$
$$
r_{t+\epsilon} = r_{t+\epsilon/2} - (\epsilon/2) \nabla U(\theta_{t+\epsilon}).
$$

Repeat for L steps, with total time τ = L ε. The integrator is symplectic (preserves volume) and time-reversible — properties needed for the Hamiltonian to be approximately conserved.

### NUTS

The **No-U-Turn Sampler** (NUTS, Hoffman–Gelman 2014) automates the choice of trajectory length. It builds a binary tree of leapfrog steps in both directions, doubling until a U-turn is detected (the trajectory starts moving back). NUTS is the default in Stan, PyMC, NumPyro, and most modern probabilistic programming.

```python
# NUTS via PyMC.
import pymc as pm
import numpy as np

returns = np.random.normal(0.005, 0.04, 60)

with pm.Model() as model:
    mu = pm.Normal('mu', mu=0, sigma=0.05)
    sigma = pm.HalfNormal('sigma', sigma=0.1)
    obs = pm.Normal('obs', mu=mu, sigma=sigma, observed=returns)
    trace = pm.sample(2000, tune=1000, chains=4, return_inferencedata=True)

print(pm.summary(trace, hdi_prob=0.9))
```

### Reality Check — HMC Limitations

- Requires gradients of the log posterior. For models with discrete latent variables, HMC does not apply directly (need marginalization or tempered methods).
- Tuning is automated (NUTS) but not perfect; complex posteriors with funnel geometries (e.g., hierarchical scale parameters) require reparameterization.
- Memory cost is moderate; computational cost per sample is higher than Gibbs but per-effective-sample is much lower.

For trading models with continuous parameters and well-defined gradients, HMC/NUTS is the production standard.

---

## Variational Inference

When MCMC is too slow, variational inference (VI) provides a faster alternative by *approximating* the posterior with a tractable family.

### The Idea

Choose a family Q of approximate posteriors q_φ(θ) parameterized by φ. Find the φ that minimizes KL divergence from the true posterior:

$$
\phi^* = \arg\min_\phi \text{KL}(q_\phi(\theta) \,\|\, p(\theta \mid D)).
$$

Equivalently, maximize the **Evidence Lower Bound** (ELBO):

$$
\mathcal{L}(\phi) = \mathbb{E}_{q_\phi}[\log p(D, \theta) - \log q_\phi(\theta)].
$$

ELBO maximization is a deterministic optimization, solvable with stochastic gradient methods.

### Mean-Field VI

The simplest family: factorized q_φ(θ) = ∏ q_φ_k(θ_k). Each factor is independent. Iterative updates (coordinate ascent) converge to a local optimum.

### Automatic Differentiation Variational Inference (ADVI)

For continuous parameters, ADVI:
1. Transforms parameters to unconstrained space (log for positives, logit for [0, 1], etc.).
2. Approximates the posterior in unconstrained space with a multivariate Gaussian.
3. Maximizes ELBO via stochastic gradient ascent.

Implemented in Stan (advi), PyMC (fit method), Pyro, NumPyro. Typically 10–100× faster than NUTS but with approximation error.

### Reality Check — VI for Trading

VI's approximation tends to *underestimate* posterior variance — the mean-field assumption loses correlation between parameters. For decisions sensitive to tail probabilities (VaR, ES), this is dangerous. For point-estimation tasks (parameter inference for downstream calculations), VI is often acceptable.

Production: use VI for fast online updates and MCMC for periodic gold-standard estimation.

---

## Kalman Filter — Linear Gaussian State Space

The Kalman filter is the canonical online Bayesian inference algorithm for linear Gaussian models. It is exact, fast, and widely applicable.

### Linear Gaussian State Space Model

State equation:
$$
x_t = F_t x_{t-1} + B_t u_t + w_t, \qquad w_t \sim \mathcal{N}(0, Q_t).
$$

Observation equation:
$$
y_t = H_t x_t + v_t, \qquad v_t \sim \mathcal{N}(0, R_t).
$$

x_t is the latent state, y_t is the observation, F, H, Q, R are model matrices. The filter maintains the posterior over x_t given y_{1:t} as a Gaussian: x_t | y_{1:t} ∼ 𝒩(μ_t, Σ_t).

### Kalman Recursion

**Predict step** (prior at time t+1):
$$
\hat \mu_{t+1|t} = F_{t+1} \mu_t + B_{t+1} u_{t+1},
$$
$$
\hat \Sigma_{t+1|t} = F_{t+1} \Sigma_t F_{t+1}^\top + Q_{t+1}.
$$

**Update step** (posterior given y_{t+1}):

$$
K_{t+1} = \hat \Sigma_{t+1|t} H_{t+1}^\top (H_{t+1} \hat \Sigma_{t+1|t} H_{t+1}^\top + R_{t+1})^{-1},
$$
$$
\mu_{t+1} = \hat \mu_{t+1|t} + K_{t+1} (y_{t+1} - H_{t+1} \hat \mu_{t+1|t}),
$$
$$
\Sigma_{t+1} = (I - K_{t+1} H_{t+1}) \hat \Sigma_{t+1|t}.
$$

K is the **Kalman gain** — the optimal weighting of new observation against prior.

### Trading Applications

- **Tracking time-varying alpha**: state = unobservable factor exposure or alpha; observation = realized P&L.
- **Online beta estimation**: state = beta; observation = stock return.
- **Pairs trading**: state = cointegration coefficient; observation = price spread.
- **Volatility tracking**: state = log volatility; observation = squared return (linear approximation).

```python
import numpy as np

def kalman_filter(y, F, H, Q, R, mu0, Sigma0):
    n = len(y)
    mu = np.zeros((n, len(mu0)))
    Sigma = np.zeros((n, len(mu0), len(mu0)))
    mu_prev, Sigma_prev = mu0, Sigma0
    for t in range(n):
        # Predict
        mu_pred = F @ mu_prev
        Sigma_pred = F @ Sigma_prev @ F.T + Q
        # Update
        S = H @ Sigma_pred @ H.T + R
        K = Sigma_pred @ H.T @ np.linalg.inv(S)
        innovation = y[t] - H @ mu_pred
        mu[t] = mu_pred + K @ innovation
        Sigma[t] = (np.eye(len(mu0)) - K @ H) @ Sigma_pred
        mu_prev, Sigma_prev = mu[t], Sigma[t]
    return mu, Sigma

# Example: track time-varying beta of stock vs market
np.random.seed(0)
T = 252
true_beta = 0.8 + 0.4*np.sin(np.linspace(0, 4*np.pi, T))
market = np.random.normal(0, 0.01, T)
stock = true_beta * market + np.random.normal(0, 0.005, T)

# State-space: x_t = beta_t, y_t = market_t * beta_t + noise
# F = 1 (random walk), H_t = market_t (time-varying)
F = np.array([[1.0]])
Q = np.array([[1e-5]])  # how fast beta drifts
R = np.array([[1e-4]])
mu0, Sigma0 = np.array([1.0]), np.array([[1.0]])

mus = []
mu_prev, Sigma_prev = mu0, Sigma0
for t in range(T):
    H_t = np.array([[market[t]]])
    mu_pred = F @ mu_prev
    Sigma_pred = F @ Sigma_prev @ F.T + Q
    S = H_t @ Sigma_pred @ H_t.T + R
    K = Sigma_pred @ H_t.T @ np.linalg.inv(S)
    mu_post = mu_pred + K @ np.array([stock[t] - (H_t @ mu_pred)[0]])
    Sigma_post = (np.eye(1) - K @ H_t) @ Sigma_pred
    mus.append(mu_post[0])
    mu_prev, Sigma_prev = mu_post, Sigma_post

mus = np.array(mus)
print(f"Final estimated beta: {mus[-1]:.3f}, true: {true_beta[-1]:.3f}")
print(f"Mean estimation error: {np.mean(np.abs(mus - true_beta)):.4f}")
```

### Smoothing

The filter gives x_t | y_{1:t}. The Kalman *smoother* gives x_t | y_{1:T} (using future observations) via a backward recursion. Smoothing reduces estimation error by 30–50% in typical applications. For backtesting, *only the filter* respects causality; the smoother uses future information and inflates apparent performance.

### Reality Check — Kalman in Live Trading

Production Kalman filters need:
- **Numerical stability**: use square-root or UD form to avoid covariance matrix degenerating.
- **Outlier handling**: huber-style weighting or jump detection on the innovation.
- **Time-varying parameters**: F, H, Q, R may need to adapt; full model estimation requires EM or Bayesian inference.
- **Latency**: filter updates in microseconds; integrate with order routing.

The Kalman framework is used in pairs trading, statistical arbitrage, and execution algorithms — anywhere a latent state drives observed prices.

---

## Extended and Unscented Kalman Filters

For nonlinear models, the basic Kalman filter does not apply. Two extensions:

### Extended Kalman Filter (EKF)

Linearize the nonlinear state and observation functions around the current estimate:

$$
F_t \approx \frac{\partial f}{\partial x}\bigg|_{x = \mu_{t-1}}, \qquad H_t \approx \frac{\partial h}{\partial x}\bigg|_{x = \hat \mu_{t|t-1}}.
$$

Then run the linear Kalman filter on the linearized system. EKF is fast but biased when the nonlinearity is strong.

### Unscented Kalman Filter (UKF)

Instead of linearization, propagate a small set of "sigma points" through the full nonlinear dynamics. The propagated points capture the mean and covariance of the transformed distribution to second order. UKF is more accurate than EKF for moderately nonlinear systems and avoids derivative computation.

### Trading Use

- **EKF**: tracking parameters in Heston-like volatility models; estimating jump intensity in jump-diffusion models.
- **UKF**: state estimation in nonlinear cointegration models; tracking latent regime variables.

---

## Particle Filtering

For highly nonlinear or non-Gaussian state-space models, **particle filtering** (sequential Monte Carlo) approximates the posterior with a weighted sample of "particles."

### Algorithm

Maintain N particles {x_t^{(i)}} with weights {w_t^{(i)}} representing the posterior at time t.

**Predict**: propagate each particle through the state dynamics:
$$
x_{t+1}^{(i)} \sim p(x_{t+1} \mid x_t^{(i)}).
$$

**Update**: weight by likelihood of new observation:
$$
w_{t+1}^{(i)} \propto w_t^{(i)} \cdot p(y_{t+1} \mid x_{t+1}^{(i)}).
$$

**Resample**: when effective sample size drops, resample N particles with probability proportional to weights.

### Resampling Strategies

- **Multinomial**: simple but high variance.
- **Stratified**: divides into N strata, samples one from each.
- **Systematic**: deterministic stratified, used when aliasing is acceptable.
- **Residual**: combines multinomial with deterministic copy of high-weight particles.

### Trading Applications

- **Stochastic volatility filtering**: state = log volatility; observation = return. The model is non-Gaussian.
- **Jump detection**: state = (log price, jump indicator); observation = return. Non-Gaussian posterior over jump indicators.
- **Regime models with continuous regimes**: latent state evolves on a continuous manifold; particles sample.
- **Factor model with non-Gaussian latent factors**: e.g., t-distributed factor with Gaussian observations.

```python
import numpy as np

def particle_filter(y, transition_sample, log_likelihood, x0_sampler, N=500):
    """Generic particle filter."""
    T = len(y)
    particles = np.array([x0_sampler() for _ in range(N)])
    weights = np.ones(N) / N
    estimates = []
    for t in range(T):
        particles = np.array([transition_sample(p) for p in particles])
        log_w = np.array([log_likelihood(y[t], p) for p in particles])
        log_w_max = log_w.max()
        weights = weights * np.exp(log_w - log_w_max)
        weights /= weights.sum()
        ess = 1/np.sum(weights**2)
        if ess < N/2:
            indices = np.random.choice(N, N, p=weights)
            particles = particles[indices]
            weights = np.ones(N)/N
        estimates.append((particles * weights).sum())
    return np.array(estimates)

# Example: stochastic volatility model
# x_t = log volatility, y_t = return ~ N(0, exp(x_t))
np.random.seed(0)
T = 200
true_x = 0.5*np.cumsum(np.random.normal(0, 0.1, T))  # random walk in log vol
y = np.random.normal(0, np.exp(true_x))  # observations

def transition(x): return x + np.random.normal(0, 0.1)
def log_lik(y, x): return -0.5*y**2/np.exp(x) - 0.5*x  # Gaussian with stdev exp(x/2)
def x0(): return np.random.normal(0, 0.5)

est = particle_filter(y, transition, log_lik, x0, N=1000)
print(f"Final true x: {true_x[-1]:.3f}, estimated: {est[-1]:.3f}")
print(f"Mean abs error: {np.mean(np.abs(est - true_x)):.3f}")
```

### Reality Check — Particle Filters at Scale

For large state spaces (>10 dimensions) or long observation series, particle filters degenerate: the weights concentrate on a few particles, and effective sample size collapses. Mitigations:
- **Auxiliary particle filter** (Pitt–Shephard 1999): pre-sample using observation likelihood.
- **Particle MCMC** (Andrieu–Doucet–Holenstein 2010): combine particle filter with MCMC for parameter estimation.
- **Kalman-particle hybrids**: Kalman for linear part, particle for nonlinear part.

For trading, particle filters are typically used in offline calibration of stochastic-volatility or jump-diffusion models, with the calibrated model deployed via simpler online methods.

---

## Hidden Markov Models

A Hidden Markov Model (HMM) is a discrete-time, discrete-state state-space model. Latent state s_t ∈ {1, …, K} follows a Markov chain; observations y_t are generated conditional on s_t.

### Setup

- Initial distribution: π_0 = (π_0^k)_{k=1}^K.
- Transition matrix: P_{ij} = ℙ(s_t = j | s_{t-1} = i).
- Emission distribution: p(y_t | s_t = k).

For a Gaussian-emission HMM, p(y_t | s_t = k) = 𝒩(µ_k, σ_k²).

### Algorithms

- **Forward–backward**: compute p(s_t | y_{1:T}) (smoothing) in O(T K²).
- **Viterbi**: find the most likely state sequence s_{1:T}^* in O(T K²).
- **Baum–Welch (EM)**: estimate parameters (π_0, P, emissions) via EM. Iteratively maximizes the likelihood.

### Trading Use

- **Regime detection**: K = 2 or 3 regimes (low-vol bull, high-vol bear, transition). Latent state = regime; emission = returns.
- **Trend identification**: regime = trend direction.
- **Volatility regimes**: emission variance differs by state.

```python
import numpy as np
from hmmlearn.hmm import GaussianHMM

np.random.seed(42)
# Generate two-regime returns: low vol + high vol
T = 1000
states = np.zeros(T, dtype=int)
returns = np.zeros(T)
P = np.array([[0.99, 0.01], [0.05, 0.95]])
emissions = [(0.0005, 0.01), (-0.001, 0.03)]  # (mean, std) for each regime
states[0] = 0
returns[0] = np.random.normal(*emissions[0])
for t in range(1, T):
    states[t] = np.random.choice(2, p=P[states[t-1]])
    returns[t] = np.random.normal(*emissions[states[t]])

# Fit HMM
model = GaussianHMM(n_components=2, covariance_type='full', n_iter=100, random_state=42)
model.fit(returns.reshape(-1, 1))
inferred_states = model.predict(returns.reshape(-1, 1))

# Compare to true states (up to label permutation)
match = max(np.mean(inferred_states == states), np.mean(inferred_states == 1-states))
print(f"State matching accuracy: {match:.3f}")
print(f"Inferred transition matrix:\n{model.transmat_}")
```

### Reality Check — HMMs in Trading

HMMs are popular for regime detection but have known issues:
- **Label switching**: the labeling of states is arbitrary; "regime 1" today might be "regime 2" tomorrow after re-fit.
- **Number of states**: choice of K is heuristic; BIC, cross-validation, or domain knowledge.
- **Stationarity**: the transition matrix P is constant; in real markets, transition probabilities themselves vary.
- **Observation distribution**: Gaussian emissions are usually too restrictive; t-distributions or mixtures often fit better.

Document 48 (Regime Detection HMM Clustering) covers production-grade regime models.

---

## Regime-Switching Models

Generalize HMMs by allowing multiple observation regimes per asset, possibly with cross-asset dependencies.

### Hamilton (1989) Markov-Switching Regression

Assume y_t = µ_{s_t} + σ_{s_t} ε_t, where s_t is a latent regime and ε_t is iid noise. Estimate (µ_k, σ_k) and transition matrix P via maximum likelihood (EM) or Bayesian inference (MCMC).

### MS-AR

Markov-switching AR: y_t = φ_{s_t} y_{t-1} + ε_{s_t}_t. Captures regimes with different autoregressive structures.

### Stochastic Volatility with Regimes

Combine HMM with stochastic vol: in each regime, σ_t follows a different SDE. Used for regime-aware option pricing.

### Reality Check — Regimes Are Slippery

The most common pitfall: identifying "regimes" that fit historical data but do not generalize. The HMM might "discover" a regime that corresponds to a particular event (March 2020) and predict that regime when no such event is occurring. Defenses:
- Use simple, interpretable regime structures (high-vol vs low-vol, not 7-state hierarchical).
- Cross-validate: predict next-period regime probabilities and check calibration.
- Compare to economic interpretation: do the regimes correspond to recognized economic states?

---

## Bayesian Linear Regression — Trading Application

Linear regression with Bayesian priors gives natural shrinkage and uncertainty quantification.

### Setup

$$
y = X \beta + \varepsilon, \qquad \varepsilon \sim \mathcal{N}(0, \sigma^2 I).
$$

Prior: β ∼ 𝒩(β_0, Σ_0). Posterior is also Gaussian:

$$
\beta \mid y \sim \mathcal{N}(\beta_n, \Sigma_n),
$$

with

$$
\Sigma_n = (\Sigma_0^{-1} + X^\top X / \sigma^2)^{-1}, \qquad \beta_n = \Sigma_n (\Sigma_0^{-1} \beta_0 + X^\top y / \sigma^2).
$$

For uninformative prior (Σ_0 → ∞), β_n = (XᵀX)⁻¹Xᵀy — the OLS estimator. For tight prior (Σ_0 → 0), β_n = β_0 — fully shrunk.

### Trading Application: Factor Models

Estimate factor exposures β with prior β_0 = 0 (zero exposure unless evidence). With T observations and shrinkage, the posterior β_n is closer to zero than OLS, especially for noisy factors.

```python
import numpy as np

def bayesian_lr(y, X, beta0, Sigma0, sigma2):
    Sigma_n = np.linalg.inv(np.linalg.inv(Sigma0) + X.T @ X / sigma2)
    beta_n = Sigma_n @ (np.linalg.inv(Sigma0) @ beta0 + X.T @ y / sigma2)
    return beta_n, Sigma_n

# Example: Estimate alpha and beta of a stock
np.random.seed(0)
T = 60
market = np.random.normal(0, 0.04, T)
true_alpha, true_beta = 0.001, 1.2
y = true_alpha + true_beta*market + np.random.normal(0, 0.02, T)

X = np.column_stack([np.ones(T), market])
beta0 = np.array([0.0, 1.0])  # prior: no alpha, beta = 1
Sigma0 = np.diag([0.001**2, 0.5**2])

beta_n, Sigma_n = bayesian_lr(y, X, beta0, Sigma0, sigma2=0.02**2)
print(f"Bayesian alpha: {beta_n[0]:.5f} ± {np.sqrt(Sigma_n[0, 0]):.5f}")
print(f"Bayesian beta: {beta_n[1]:.3f} ± {np.sqrt(Sigma_n[1, 1]):.3f}")
print(f"OLS alpha (compare): {(np.linalg.inv(X.T@X)@X.T@y)[0]:.5f}")
```

The Bayesian estimate of alpha is shrunk toward zero — appropriate when you don't have strong evidence of consistent outperformance.

### Hierarchical Bayesian Regression

For multiple stocks, share information across stocks via a hierarchical prior:

$$
\beta_i \sim \mathcal{N}(\beta_{\text{group}}, \Sigma_{\text{within}}),
$$
$$
\beta_{\text{group}} \sim \mathcal{N}(0, \Sigma_{\text{between}}).
$$

Each stock's β is shrunk toward the group mean β_{group}. This is a Bayesian formulation of the cross-sectional shrinkage that motivates Black–Litterman portfolios. Document 82 (Black–Litterman) covers the related machinery.

---

## Bayesian Hierarchical Models for Cross-Sectional Returns

Hierarchical models exploit shared structure across many similar units (stocks, traders, strategies). The result: more efficient estimation than running each unit independently.

### Setup

$$
\text{Returns}_{i, t} = \alpha_i + \beta_i \text{Mkt}_t + \varepsilon_{i, t},
$$
$$
\alpha_i \sim \mathcal{N}(\mu_\alpha, \tau_\alpha^2),
$$
$$
\beta_i \sim \mathcal{N}(\mu_\beta, \tau_\beta^2),
$$
$$
\mu_\alpha, \mu_\beta, \tau_\alpha, \tau_\beta \sim \text{prior}.
$$

The hyperparameters µ, τ are themselves random; their posterior is shaped by all the {α_i, β_i}. Each individual α_i is estimated using both its own data *and* the data from all other stocks (via the shared hyperprior).

### Result

Stocks with little data have α_i shrunk strongly toward µ_α (the group mean). Stocks with abundant data have α_i closer to their own MLE. The amount of shrinkage is *inferred* from the data, not chosen by the analyst.

### Application: Multi-Strategy Performance

For a fund running 50 trading strategies, each with monthly returns over 5 years:
- Independent estimation: high noise; unreliable per-strategy Sharpe.
- Hierarchical: share information; per-strategy estimates shrink toward the fund-level Sharpe.
- Decision: keep strategies with posterior Sharpe credible interval excluding zero.

This is the principled approach to "should we cut this strategy?" — vastly better than threshold rules on point estimates.

```python
# Hierarchical model for cross-sectional alphas via PyMC.
import pymc as pm
import numpy as np

np.random.seed(42)
n_stocks, T = 30, 60
true_mu_alpha = 0.002
true_tau_alpha = 0.001
true_alphas = np.random.normal(true_mu_alpha, true_tau_alpha, n_stocks)
returns = np.random.normal(true_alphas[:, None], 0.04, (n_stocks, T))

with pm.Model() as model:
    mu_alpha = pm.Normal('mu_alpha', mu=0, sigma=0.005)
    tau_alpha = pm.HalfNormal('tau_alpha', sigma=0.005)
    alphas = pm.Normal('alphas', mu=mu_alpha, sigma=tau_alpha, shape=n_stocks)
    sigma = pm.HalfNormal('sigma', sigma=0.05)
    obs = pm.Normal('obs', mu=alphas[:, None], sigma=sigma, observed=returns)
    trace = pm.sample(2000, tune=1000, chains=4, return_inferencedata=True)

print(pm.summary(trace, var_names=['mu_alpha', 'tau_alpha'], hdi_prob=0.9))
```

### Reality Check — Hierarchical Models Need Data

For 50 strategies × 60 months, hierarchical models are well-identified. For 5 strategies × 60 months, the τ_α prior dominates, and the hierarchical structure is essentially the prior. Always check: is there enough cross-section to estimate τ_α?

---

## Bayesian Optimization for Hyperparameter Tuning

Bayesian optimization (BO) is a method for optimizing expensive-to-evaluate functions. In trading, it is used to tune algorithmic strategy parameters where each evaluation requires a backtest (minutes to hours).

### The Idea

Model the unknown function f(x) as a Gaussian process. After observing some {(x_i, f(x_i))}, predict f at unobserved x with mean and uncertainty. Choose the next x to evaluate by an *acquisition function* that balances exploration (high uncertainty) and exploitation (high predicted mean).

### Acquisition Functions

- **Expected improvement** (EI): expected gain over the current best.
- **Upper confidence bound** (UCB): mean + κ × std.
- **Probability of improvement** (PI): probability of beating the best.

### Trading Use

- Tune strategy parameters: lookback windows, thresholds, position sizes.
- Tune hyperparameters of an ML model: learning rate, regularization, architecture.
- Tune execution algorithm parameters: aggression, dark-pool weighting.

### Reality Check — BO for Trading

BO works well when:
- Each evaluation is expensive (minutes to days per backtest).
- The parameter space is moderate (typically <20 dimensions).
- There is signal-to-noise sufficient to detect improvements.

It fails when:
- Backtest noise dominates the signal (you cannot distinguish good from bad).
- The objective is non-stationary (yesterday's best parameters are not today's).
- Parameters interact in highly non-smooth ways.

Document 211 (Backtesting Statistical Rigor) discusses Sharpe-based hyperparameter tuning and its pitfalls.

---

## Probabilistic Programming Languages

PPLs let you write Bayesian models in code with built-in MCMC/VI support.

### PyMC

Pythonic, strongly typed, NUTS-default. Production examples:

```python
import pymc as pm

with pm.Model() as model:
    mu = pm.Normal('mu', 0, 0.05)
    sigma = pm.HalfNormal('sigma', 0.05)
    y = pm.Normal('y', mu, sigma, observed=returns)
    trace = pm.sample(2000)
```

### Stan

DSL with a compiled C++ backend. Faster than pure-Python alternatives. Used in research and high-stakes inference. Has a distinct syntax (block-structured) that takes some getting used to.

### Pyro / NumPyro

PyTorch-based / JAX-based. Pyro for differentiable models and deep generative; NumPyro for fast HMC/NUTS via JAX JIT. Used in modern hybrid Bayesian-ML pipelines.

### TensorFlow Probability

Google's framework. Strong on variational methods. Less popular for trading due to ecosystem dominance of PyTorch/JAX.

### Reality Check — Choosing a PPL

For batch Bayesian inference with moderate models: PyMC.
For hierarchical or hard-to-sample posteriors: Stan.
For deep generative models or differentiable simulations: Pyro/NumPyro.
For GPU-accelerated VI at scale: NumPyro or TFP.

---

## Posterior Predictive Checks and Model Validation

After fitting a Bayesian model, validate by drawing **posterior predictive samples** — synthetic data drawn from the model with parameters sampled from the posterior:

$$
y^{\text{rep}} \sim p(y \mid \theta) \quad \text{where} \quad \theta \sim p(\theta \mid D).
$$

Compare statistics of y^{rep} to statistics of D. Discrepancies indicate model misspecification.

### Common Checks

- **Mean and variance**: 𝔼[y^{rep}] vs 𝔼[D]; Var(y^{rep}) vs Var(D).
- **Higher moments**: skewness, kurtosis of y^{rep} vs D.
- **Tails**: quantiles of y^{rep} vs D at 5%, 95%.
- **Time-series**: autocorrelations of y^{rep} vs D.

### Trading Example: Volatility Model Check

Fit a stochastic-vol model to returns. Draw posterior predictive returns. Check:
- Empirical kurtosis: should match observed (typically 3–10 for daily returns).
- Volatility autocorrelation: should be persistent (autocorr at lag 1 day ~0.3–0.6).
- Tail behavior: 1% and 99% quantiles should match.

If any of these fails, the model is missing something (jumps, regimes, leverage).

### Reality Check — PPCs for Trading

Posterior predictive checks are the right way to detect model failures *before* deploying to live trading. A model that fits the in-sample data perfectly but fails posterior predictive checks on tail behavior is destined to underestimate risk.

---

## Bayesian Risk Modeling — VaR, ES, Drawdown

Bayesian methods give a principled framework for risk modeling under parameter uncertainty.

### Bayesian VaR

Frequentist VaR: estimate µ, σ from history; VaR = µ − z_α σ. Ignores estimation uncertainty.

Bayesian VaR: posterior over (µ, σ); compute VaR for each sample, then take posterior quantile.

```python
# Bayesian VaR for SPX returns.
np.random.seed(42)
returns = np.random.normal(0.001, 0.012, 252)  # 1 year of synthetic SPX

# Posterior via NIG conjugate prior.
mu0, kappa0, alpha0, beta0 = 0.0, 1.0, 2.0, 0.0001
n = len(returns)
r_bar = returns.mean()
mu_n = (kappa0*mu0 + n*r_bar)/(kappa0 + n)
kappa_n = kappa0 + n
alpha_n = alpha0 + n/2
beta_n = beta0 + 0.5*((n-1)*returns.var() + n*kappa0/(kappa0+n)*(r_bar - mu0)**2)

n_draws = 100_000
sigma2_post = invgamma.rvs(alpha_n, scale=beta_n, size=n_draws)
mu_post = mu_n + np.sqrt(sigma2_post/kappa_n)*np.random.normal(size=n_draws)
sigma_post = np.sqrt(sigma2_post)

# 99% VaR for each posterior draw
var_99 = -mu_post + 2.326*sigma_post  # quantile of 𝒩(µ, σ²) at 1%
print(f"Bayesian 99% VaR: posterior mean={var_99.mean():.4f}, 5-95%=[{np.percentile(var_99, 5):.4f}, {np.percentile(var_99, 95):.4f}]")
```

The 90% credible interval for VaR is wider than the OLS-based interval — appropriately reflecting that you don't know µ, σ exactly.

### Bayesian Expected Shortfall

ES is the average loss conditional on exceeding VaR. Posterior ES is computed analogously: per-sample ES, then posterior quantile.

### Bayesian Drawdown

Maximum drawdown depends on the entire path. Approximate the posterior over MDD by:
1. Sample (µ, σ) from posterior.
2. Simulate paths.
3. Compute MDD on each path.
4. Take the posterior distribution of MDD.

This gives a credible interval on MDD that accounts for both path uncertainty and parameter uncertainty.

---

## Online Bayesian Inference and Sequential Monte Carlo

For real-time trading, batch MCMC is too slow. Online methods update the posterior as new data arrives.

### Sequential Bayesian Updating

For conjugate models, the posterior update is closed-form, taking O(1) per observation. For non-conjugate, use:

- **Sequential Monte Carlo** (particle filter for parameters, not just states).
- **Online VI**: stochastic gradient updates on ELBO.
- **Approximate Bayesian Computation**: simulation-based inference when likelihood is intractable.

### Application: Online Beta Tracking

A stock's beta to the market changes over time. An online Bayesian filter updates the beta estimate as each new return arrives:

```python
# Online beta tracking with Bayesian shrinkage.
np.random.seed(0)
T = 252
true_beta = 0.8 + 0.5*np.cos(np.linspace(0, 4*np.pi, T))
market = np.random.normal(0, 0.01, T)
stock = true_beta * market + np.random.normal(0, 0.005, T)

# Online estimation
beta_hat = 1.0
sigma2_beta = 0.01  # prior variance
sigma2_eps = 1e-4
beta_history = []

for t in range(T):
    # Predict (no transition assumed; pure update)
    # Update with new observation
    K = sigma2_beta * market[t] / (market[t]**2 * sigma2_beta + sigma2_eps)
    beta_hat = beta_hat + K*(stock[t] - market[t]*beta_hat)
    sigma2_beta = (1 - K*market[t])*sigma2_beta + 1e-5  # add small process noise
    beta_history.append(beta_hat)

print(f"Mean abs error: {np.mean(np.abs(np.array(beta_history) - true_beta)):.4f}")
```

### Reality Check — Online Inference and Latency

Online Bayesian inference for trading must complete within the latency budget. Conjugate updates: nanoseconds. Particle filter with N=1000: microseconds. ADVI: milliseconds. MCMC: seconds.

Choose the method matching your latency budget. For HFT, only conjugate or simple Kalman is feasible; for end-of-day risk, full MCMC is fine.

---

## Reality Checks and Production Pitfalls

### Pitfall 1: Improper Priors

A prior that is improper (does not integrate to 1) can give a proper posterior, but it is risky. Improper priors arise from "uninformative" choices like uniform on (-∞, ∞) or 1/σ on σ > 0. Always check that the resulting posterior integrates.

### Pitfall 2: Multimodality Hidden by MCMC

A multi-modal posterior may be sampled by MCMC chains that all start near one mode. Without proper diagnostics (multiple chains from different starts, parallel tempering), the second mode is invisible. Always run multiple chains and check.

### Pitfall 3: Model Misspecification

A wrong model gives a posterior that is wrong even with infinite data. Bayesian inference does not detect misspecification; only posterior predictive checks do.

### Pitfall 4: Computational Cost vs Latency

A model that takes 2 hours to fit cannot be retrained daily; one that takes 2 days cannot react to market changes. Match the model's complexity to the operational requirements.

### Pitfall 5: "Bayesian-Looking" Frequentism

Slapping "Bayesian" on a model with a single point estimate (the MAP) gains nothing over frequentist MLE. The value is in the *full posterior*, not the mode.

### Pitfall 6: Ignoring the Decision

A posterior is not the answer. The answer is the *decision* that minimizes expected loss under the posterior. Always specify the loss function explicitly.

---

## Reference Tables, Cheat Sheets, Bibliography

### Conjugate Prior Cheat Sheet

| Likelihood | Conjugate Prior | Posterior |
|---|---|---|
| Bernoulli(θ) | Beta(α, β) | Beta(α + #wins, β + #losses) |
| Binomial(n, θ) | Beta(α, β) | Beta(α + #wins, β + #losses) |
| Poisson(λ) | Gamma(α, β) | Gamma(α + Σy, β + n) |
| Exponential(λ) | Gamma(α, β) | Gamma(α + n, β + Σy) |
| Normal(µ, known σ²) | Normal(µ_0, τ_0²) | Normal — see formulas |
| Normal(µ, σ²) | Normal-Inverse-Gamma | Normal-Inverse-Gamma |
| Multinomial | Dirichlet(α) | Dirichlet(α + counts) |
| Wishart | Wishart | Wishart |

### Bibliography

- **Gelman, A., Carlin, J., Stern, H., Dunson, D., Vehtari, A., Rubin, D. (2013), *Bayesian Data Analysis* (3rd ed.), CRC.** The standard reference.
- **Bishop, C. (2006), *Pattern Recognition and Machine Learning*, Springer.** Comprehensive ML/Bayesian reference.
- **Kruschke, J. (2014), *Doing Bayesian Data Analysis* (2nd ed.), Academic Press.** Practical, code-driven.
- **Robert, C. and Casella, G. (2004), *Monte Carlo Statistical Methods*, Springer.** MCMC theory.
- **Hoffman, M. and Gelman, A. (2014), "The No-U-Turn Sampler", JMLR.** NUTS.
- **Doucet, A., de Freitas, N., Gordon, N. (2001), *Sequential Monte Carlo Methods in Practice*, Springer.** Particle filters.
- **Rasmussen, C. and Williams, C. (2006), *Gaussian Processes for Machine Learning*, MIT.** GP regression and BO.
- **Murphy, K. (2012), *Machine Learning: A Probabilistic Perspective*, MIT.** Comprehensive.
- **McElreath, R. (2020), *Statistical Rethinking* (2nd ed.), CRC.** Accessible, model-driven.
- **Kalman, R. (1960), "A New Approach to Linear Filtering and Prediction Problems", *J. Basic Engineering* 82(1): 35–45.** Original Kalman.
- **Hamilton, J. (1989), "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle", *Econometrica* 57(2): 357–384.** Markov-switching.

### Cross-References

- Document 41 — Kelly Criterion (decision under uncertainty).
- Document 48 — Regime Detection HMM Clustering.
- Document 75 — XGBoost LightGBM (frequentist alternative).
- Document 82 — Black–Litterman (Bayesian portfolio).
- Document 200 — Stochastic Calculus.

---

*End of document 203. ~1,800 lines.*
