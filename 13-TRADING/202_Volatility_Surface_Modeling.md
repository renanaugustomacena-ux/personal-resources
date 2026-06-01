# 202 — Volatility Surface Modeling and Calibration

> Production-grade reference on the construction, calibration, and use of implied volatility surfaces. Covers static no-arbitrage constraints (Lee bounds, butterfly/calendar arbitrage), parametric forms (SVI, SSVI, SABR), local volatility (Dupire), stochastic volatility (Heston with full numerics), local-stochastic volatility (LSV with leverage-function calibration), and rough volatility (rBergomi simulation). Connects to derivatives trading via hedging dynamics, smile risk, and forward-smile evolution. Assumes documents 200 (stochastic calculus) and 201 (microstructure) as background.

---

## Table of Contents

1. [Why Vol Surfaces Matter](#why-vol-surfaces-matter)
2. [Implied Volatility — Definition, Inversion, Numerics](#part-i-implied-volatility)
3. [The Smile and the Skew — Empirical Anatomy](#smile-anatomy)
4. [Strike–Maturity Coordinates and Their Variants](#coordinates)
5. [Static No-Arbitrage — Calendar, Butterfly, Roger Lee](#part-ii-no-arbitrage)
6. [SVI Parameterization](#svi)
7. [Surface SVI (SSVI)](#ssvi)
8. [Lee's Wing Bounds](#lee-wing-bounds)
9. [Local Volatility — Dupire's Equation](#part-iii-local-volatility)
10. [Local Volatility Calibration in Practice](#local-vol-calibration)
11. [Local Volatility Hedging Dynamics](#local-vol-hedging)
12. [Heston — Full Calibration Pipeline](#part-iv-heston)
13. [Heston Numerics — Trap-Free CF and FFT](#heston-numerics)
14. [SABR Model — Asymptotic and Numerical](#part-v-sabr)
15. [SABR Wings, Negative Rates, Shifted SABR](#sabr-extensions)
16. [Local-Stochastic Volatility (LSV) — Leverage Function](#part-vi-lsv)
17. [LSV Calibration via Markov Projection](#lsv-calibration)
18. [Rough Volatility — rBergomi and Hybrid Schemes](#part-vii-rough-vol)
19. [Forward Smile Dynamics — Sticky Strike, Sticky Delta, Sticky Vol](#part-viii-forward-smile)
20. [Variance Swap Pricing and Replication](#variance-swap)
21. [VIX Term Structure and Vol-of-Vol](#vix-term-structure)
22. [Cross-Sectional Implied Vol — Single-Stock vs Index](#cross-sectional-vol)
23. [Calibration in Practice — Loss Functions, Solvers, Diagnostics](#calibration-practice)
24. [Real Trading Considerations — From Surface to PnL](#trading-considerations)
25. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Why Vol Surfaces Matter

Every derivative price is a function of expected payoff under some measure. For European options, that expectation depends on the marginal distribution of the underlying at maturity. For path-dependent or American options, it depends on the joint distribution along the entire path. The volatility surface — the set of all observable European option prices, expressed as Black–Scholes implied volatilities indexed by strike and maturity — is the cleanest summary of what the market believes about that distribution.

A trader who treats vol as a single number is leaving money on the table. The market embeds a *distribution* of beliefs about future prices. The shape of that distribution is encoded in the smile (curvature), skew (asymmetry), and term structure (how the smile evolves with maturity). Reading these correctly is the difference between a profitable derivatives book and an unprofitable one.

Three operational tasks drive vol-surface modeling:

1. **Pricing exotics consistently with vanillas.** A barrier option, an Asian, an autocallable — all must be priced under a model whose *vanilla* prices match the observed surface. Otherwise you are arbitrageable.

2. **Forecasting smile dynamics.** Hedging an option requires Vega; managing a book requires understanding how the smile moves when the underlying moves. The wrong dynamics assumption causes systematic P&L drift.

3. **Detecting trades.** The shape of the surface itself encodes information. A steep skew means the market is paying for downside protection. A flat smile means the market is pricing more nearly Gaussian outcomes. Variance risk premia, skew risk premia, and term-structure trades all read from the surface.

This document covers the mathematical and computational machinery for all three tasks, with the emphasis on what works in production. We will see closed forms (where they exist), numerical methods (where they do not), and calibration recipes (everywhere).

A note on scope. This is a *vol surface* document, not a *volatility forecasting* document. Forecasting realized volatility (HAR-RV, GARCH, neural networks) is covered in document 211. Volatility risk premia and trading strategies are covered in document 27 and document 60. Here we focus on the mathematics of the surface itself: how to fit it, how to constrain it, and how to use it to price.

---

## Part I — Implied Volatility

### Definition

Given a market price C of a European call option (strike K, maturity T, underlying S, risk-free rate r, dividend yield q), the **Black–Scholes implied volatility** σ_imp is the unique value of σ such that

$$
C_{\text{BS}}(S, K, r, q, \sigma_{\text{imp}}, T) = C,
$$

where C_BS is the Black–Scholes price formula:

$$
C_{\text{BS}} = S e^{-qT} \Phi(d_+) - K e^{-rT} \Phi(d_-),
$$
$$
d_\pm = \frac{\log(S/K) + (r - q \pm \sigma^2/2) T}{\sigma \sqrt{T}}.
$$

Existence and uniqueness: C_BS is strictly increasing in σ from 0 (σ = 0) to S e^{−qT} − K e^{−rT} (intrinsic) up to ∞ (σ = ∞). For any C between these bounds (i.e., not violating no-arbitrage), σ_imp exists and is unique.

For puts, by put–call parity, σ_imp(put) = σ_imp(call) at the same strike — the implied volatility is unique to the strike, not the option type.

### Inversion

Three standard methods to invert C_BS for σ:

#### Newton's Method

Iterate σ_{n+1} = σ_n − (C_BS(σ_n) − C)/Vega(σ_n). Quadratic convergence. Vega is positive, so the iteration is well-behaved.

```python
import numpy as np
from scipy.stats import norm

def implied_vol_newton(C, S, K, r, q, T, sigma_init=0.20, tol=1e-8, max_iter=100):
    sigma = sigma_init
    for _ in range(max_iter):
        d1 = (np.log(S/K) + (r - q + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        C_bs = S*np.exp(-q*T)*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
        vega = S*np.exp(-q*T)*norm.pdf(d1)*np.sqrt(T)
        diff = C_bs - C
        if abs(diff) < tol:
            return sigma
        sigma = sigma - diff/max(vega, 1e-10)
        sigma = max(0.001, min(sigma, 5.0))  # bounds for stability
    return sigma
```

Newton fails when σ_init is far from the solution, when Vega is near zero (deep ITM/OTM), or when C is near the no-arb bounds.

#### Bisection

Slow but bulletproof. Bracket σ ∈ [σ_lo, σ_hi] with C_BS(σ_lo) < C < C_BS(σ_hi), then halve.

```python
def implied_vol_bisect(C, S, K, r, q, T, sigma_lo=0.001, sigma_hi=5.0, tol=1e-8):
    for _ in range(200):
        sigma_mid = (sigma_lo + sigma_hi) / 2
        d1 = (np.log(S/K) + (r - q + 0.5*sigma_mid**2)*T) / (sigma_mid*np.sqrt(T))
        d2 = d1 - sigma_mid*np.sqrt(T)
        C_mid = S*np.exp(-q*T)*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
        if abs(C_mid - C) < tol:
            return sigma_mid
        if C_mid < C:
            sigma_lo = sigma_mid
        else:
            sigma_hi = sigma_mid
    return (sigma_lo + sigma_hi) / 2
```

#### Jäckel's "Let's Be Rational" (2015)

The state-of-the-art for production: a deterministic algorithm that hits machine precision in 2 iterations on average and 4 in the worst case, even in the wings. Based on a transformation that linearizes the BS price near zero. Default in QuantLib and major commercial libraries.

The key idea: for very small σ, C_BS ≈ S e^{−qT} − K e^{−rT} + (S K/√(2π)) σ √T. For very large σ, C_BS ≈ S e^{−qT}. By transforming to a normalized log-strike z = log(F/K)/σ√T (where F is the forward), the inversion becomes well-conditioned everywhere.

In production, use Jäckel's method via SciPy, py_vollib, or QuantLib. Manual reimplementation is rarely worth it.

### Wings of the Smile

In the deep ITM/OTM wings, IV inversion is numerically delicate:
- Newton can overshoot.
- Vega is exponentially small (so divisions amplify error).
- The price is sensitive to small changes in σ.

A robust solution: use *forward* prices and dual-strike formulations, transform to the log-moneyness coordinate, and use Jäckel's algorithm. This handles deep wings cleanly down to machine precision.

### Reality Check — When IV Inversion Fails

Inversion fails when:
- The market price violates no-arbitrage (negative time value, etc.). Common with stale or thinly-traded options.
- Numerical underflow in deep OTM (call price < 1e-15). Use the put price via parity instead.
- Bid-ask makes the "market price" ambiguous. Use mid for theoretical work; use bid (offer) for hedging cost (selling at).

Always log inversion failures and treat them as data quality flags.

---

## The Smile and the Skew — Empirical Anatomy

The Black–Scholes model assumes constant volatility. If markets behaved according to BS, σ_imp would be a flat surface. In reality, σ_imp varies substantially with strike and maturity.

### Empirical Patterns

**Equity indices (SPX, SX5E, NKY)**: pronounced *negative skew* — OTM puts trade at higher IVs than OTM calls. The skew is steeper at shorter maturities. The term structure is typically *upward-sloping* in vol (longer-dated options have higher ATM IV) but *downward-sloping in skew* (shorter-dated options have steeper skew). Stylized: 1M ATM SPX IV might be 16, 1Y ATM 18; 1M 90% put IV 22, 1Y 90% put IV 22.

**Single-stock equities**: similar to indices but with more idiosyncratic structure. Earnings-week IVs spike at the relevant expiration; otherwise the smile is similar to index. Some stocks (low-beta value names) have smaller skew; some (small-cap growth) have larger.

**FX**: the smile is typically *symmetric* around at-the-money-forward (ATMF). The "smile" is dominantly curvature (butterfly), not asymmetry (risk reversal). Some pairs (USDJPY, EURJPY) have skew tied to carry-trade dynamics.

**Rates (caps/floors, swaptions)**: smile structure varies by tenor and strike. Short-dated swaptions often have a "hockey-stick" shape; long-dated have flatter smiles.

**Commodities**: contango/backwardation strongly affects skew. Crude oil typically has positive skew (OTM call premium for upside risk); agricultural and metals vary by season and supply state.

**Crypto (BTC, ETH options on Deribit)**: typically *positive skew* — OTM calls trade at higher IVs than OTM puts. This is the inverse of equity skew. Driven by retail "lottery ticket" demand and the structural crypto culture.

### Decomposing the Smile

A standard decomposition of the smile at a given maturity T:
- **Level**: ATMF implied volatility.
- **Skew**: the slope of σ_imp vs log-strike (approximately first derivative).
- **Curvature (smile / butterfly)**: the second derivative.

In SVI terms (defined below), these correspond to the parameters a, c, and m or b. Risk reversals and butterflies are the OTC instruments that trade these decomposed risks directly.

### Term Structure of the Smile

For a fixed strike (say, 90% moneyness), σ_imp typically has:
- Short-dated peaks and high-frequency variation (driven by event risk, earnings).
- Medium-dated smooth term structure (1M–3M roll-up).
- Long-dated convergence to a "fundamental" level.

The Heston model captures this with mean-reverting variance; the rBergomi model captures it with rough fractional Brownian motion. Both fit reasonably well; their *forward smile* dynamics differ.

### Reality Check — Smile Stability

The empirical smile shape is *not* stable across regimes. In low-vol periods, equity skew is steep; in high-vol periods, skew flattens (because OTM puts cannot get arbitrarily expensive). In crisis events, the entire surface lifts and skew sometimes inverts temporarily.

Backtests should account for regime variation. A model calibrated to the 2017 surface will fail in 2018 (vol blowup) and 2020 (COVID).

---

## Strike–Maturity Coordinates and Their Variants

The implied vol surface is a function σ_imp(K, T). For modeling, several alternative coordinates are useful:

### Log-Moneyness

$$
m = \log(K / F), \qquad F = S e^{(r - q) T}.
$$

m = 0 at ATMF; m > 0 for OTM calls; m < 0 for OTM puts. The IV parameterized in (m, T) is more model-friendly because most parameterizations (SVI, SSVI) are most natural in log-moneyness.

### Total Variance

$$
w(m, T) = \sigma_{\text{imp}}^2(m, T) \cdot T.
$$

The "total variance" w is the natural object in many no-arbitrage analyses. SVI fits w directly.

### Delta

$$
\Delta = \Phi(d_+).
$$

OTC vol surfaces (especially in FX) are typically quoted in delta coordinates: 25-delta call, 25-delta put, ATMF. Strikes are derived from deltas (and a vol assumption) to construct trading instruments.

### Standardized Moneyness

$$
z = \frac{m}{\sigma_{\text{imp}}(m, T) \sqrt{T}}.
$$

z is the "number of standard deviations" out from ATM. For very large |z|, options are rarely traded; for |z| in [-2, 2] is the empirically active region.

### Reality Check — Convention Wars

OTC and exchange conventions differ:
- Quoting vol in absolute terms (Indian, US single-name) vs as a vol point (FX, indices).
- Strike vs forward strike.
- Delta vs spot delta.
- Premium-adjusted delta vs sticky delta (FX).

Production systems explicitly handle the conventions for each market. Bugs in convention conversion are common and costly.

---

## Part II — Static No-Arbitrage

A vol surface must satisfy basic no-arbitrage constraints. Violating them implies a riskless profit opportunity (in a frictionless market). Production calibration enforces these constraints either as hard equality constraints or as soft penalty terms.

### Calendar Arbitrage

The price of a European call C(K, T) must be non-decreasing in T. This is because a longer-dated call has more time value. Formally, ∂C/∂T ≥ 0. In total-variance terms, this becomes ∂w/∂T ≥ 0 (modulo the rate term).

A violation: σ_imp(K, T_1) > σ_imp(K, T_2) for T_1 < T_2 with the same forward — implies a calendar arbitrage opportunity (sell short-dated, buy long-dated). The relationship is

$$
w(m, T_1) \le w(m, T_2) \quad \text{for } T_1 < T_2.
$$

In sticky-delta interpretation, log-moneyness must be consistent across maturities. Practical tip: always check that w(0, T) (ATMF total variance) is monotone in T.

### Butterfly Arbitrage

The price of a European call C(K, T) must be convex in K. This is because the call's payoff (S − K)^+ is convex in K. Formally, ∂²C/∂K² ≥ 0.

This translates to a constraint on the slope of σ_imp(K) at fixed T. In log-moneyness terms, the constraint involves second and first derivatives of σ_imp. The Roger Lee bound (next section) is one operational consequence.

A violation: σ_imp has a sharp kink, leading to non-convex C(K). This implies a butterfly arbitrage (sell ATM, buy OTM-call + OTM-put at appropriate strikes).

### Roger Lee Wing Bounds

Roger Lee (2004): the implied volatility cannot grow faster than √(2|m|/T) in the wings, otherwise no-arbitrage is violated.

Specifically, define β_R = lim sup_{m → ∞} (σ²(m, T) T) / (2m), and similarly β_L for m → −∞. Roger Lee's theorem:

$$
\beta_R \le 2, \qquad \beta_L \le 2.
$$

Equivalently, σ_imp(m, T) cannot grow faster than √(4m/T) (right wing) or √(4|m|/T) (left wing) for large |m|.

This is a *global* constraint. Many parameterizations (notably some early SVI variants) violate it. Modern parameterizations (SSVI with constraints, JW SVI) enforce it explicitly.

### Probability Density Constraint

The risk-neutral density at maturity T is the second derivative of the call price with respect to K:

$$
p(K, T) = e^{rT} \frac{\partial^2 C}{\partial K^2}.
$$

For C to be a valid martingale, p must be non-negative (no negative density). Violations occur when the smile has too-steep curvature or wing slopes — typically in poorly-calibrated SVI where the parameters drive the resulting density into negative territory.

This is the operational version of butterfly arbitrage.

```python
# Check no-arbitrage of a synthetic surface.
import numpy as np

def call_from_iv(S, K, r, q, T, iv):
    d1 = (np.log(S/K) + (r - q + 0.5*iv**2)*T) / (iv*np.sqrt(T))
    d2 = d1 - iv*np.sqrt(T)
    return S*np.exp(-q*T)*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)

def density_from_smile(S, T, r, q, strikes, ivs):
    """Estimate risk-neutral density via finite differences."""
    K = np.array(strikes)
    sigma = np.array(ivs)
    C = np.array([call_from_iv(S, k, r, q, T, sig) for k, sig in zip(K, sigma)])
    # Second derivative of call wrt K
    dK = K[1] - K[0]  # assume uniform grid
    p = np.zeros_like(K, dtype=float)
    p[1:-1] = (C[2:] - 2*C[1:-1] + C[:-2]) / dK**2
    return K[1:-1], p[1:-1]

# Generate a smile and check density positivity
S, r, q, T = 100, 0.03, 0.0, 0.5
strikes = np.linspace(70, 130, 121)
# Quadratic smile: steeper than allowed
ivs = 0.20 + 0.005 * np.abs(np.log(strikes/100))**2
K_d, p = density_from_smile(S, T, r, q, strikes, ivs)
print(f"Density min = {p.min():.6f}, max = {p.max():.6f}")
# Negative? If so, the smile violates butterfly arbitrage.
```

### Reality Check — Data Quality Drives No-Arb Violations

In live data, no-arb violations come mostly from:
- Stale quotes (one strike has not updated).
- Bid-ask gaming (asymmetric updates create momentary inconsistency).
- Crossed prices across venues.
- Data feed errors.

Production systems flag and ignore violators rather than fitting through them. The fitted surface is then used for everything (pricing, hedging, risk).

---

## SVI Parameterization

SVI (Stochastic Volatility Inspired, Gatheral 2004) is the most widely used vol-surface parameterization. It is simple, no-arbitrage-friendly (with constraints), and flexible enough for most empirical surfaces.

### Definition

SVI parameterizes the total variance at a single maturity T as a function of log-moneyness m:

$$
w(m) = a + b \!\left( \rho (m - m_0) + \sqrt{(m - m_0)^2 + s^2} \right).
$$

Five parameters: a (level), b (overall slope), ρ ∈ [−1, 1] (correlation/skew), m_0 (offset), s > 0 (curvature scale).

Properties:
- For ρ = 0, the SVI smile is symmetric.
- For ρ < 0, OTM puts are more expensive than OTM calls (equity-like).
- For ρ > 0, opposite.
- Linear asymptotes: w(m) ≈ b(1 + ρ)(m − m_0) − a' for m → ∞ and w(m) ≈ b(1 − ρ)(m_0 − m) + a'' for m → −∞. The slopes are b(1 + ρ) and b(1 − ρ).

To satisfy no-butterfly-arbitrage in a single SVI slice, the parameters must satisfy:

$$
b s \ge 4, \quad |\rho| \le 1, \quad a + b s \sqrt{1 - \rho^2} \ge 0.
$$

### Estimation

Standard procedure: at each maturity T, fit SVI to the observed smile by minimizing

$$
\sum_i w_i (\sigma_{\text{imp}}^{\text{SVI}}(m_i; \theta) - \sigma_{\text{imp}}^{\text{mkt}}(m_i))^2,
$$

where w_i are observation weights (typically Vega-based: more weight to ATM observations) and θ = (a, b, ρ, m_0, s).

```python
# SVI fit at a single maturity.
import numpy as np
from scipy.optimize import minimize

def svi_total_var(m, a, b, rho, m0, s):
    return a + b * (rho * (m - m0) + np.sqrt((m - m0)**2 + s**2))

def svi_iv(m, T, a, b, rho, m0, s):
    w = svi_total_var(m, a, b, rho, m0, s)
    return np.sqrt(np.maximum(w / T, 1e-10))

def fit_svi(market_m, market_iv, T):
    def loss(theta):
        a, b, rho, m0, s = theta
        if b <= 0 or s <= 0 or abs(rho) > 1 or b*s < 4 or a + b*s*np.sqrt(1-rho**2) < 0:
            return 1e10
        model_iv = svi_iv(market_m, T, *theta)
        return np.sum((model_iv - market_iv)**2)
    
    x0 = (0.04, 0.4, -0.6, 0.0, 0.04)
    res = minimize(loss, x0, method='Nelder-Mead', options={'maxiter': 5000})
    return res.x, res.fun

# Synthetic example
T = 0.5
m_true = (0.04, 0.4, -0.6, 0.0, 0.04)
m_arr = np.linspace(-0.5, 0.5, 21)
iv_market = svi_iv(m_arr, T, *m_true) + np.random.normal(0, 0.001, len(m_arr))
fitted, loss = fit_svi(m_arr, iv_market, T)
print(f"True params:   {m_true}")
print(f"Fitted params: {tuple(round(x, 4) for x in fitted)}")
```

### Variants of SVI

- **Raw SVI**: as above.
- **Natural SVI**: reparameterized with explicit ATM vol and skew, more numerically stable.
- **JW SVI** (Jump-Wing): uses ATM vol, ATM skew, and right/left wing slopes — directly trader-meaningful.
- **SSVI** (next section): a global surface parameterization in (m, T).

### Reality Check — SVI Pitfalls

SVI has known issues:
- The constraint a + b s √(1 − ρ²) ≥ 0 is sometimes violated by unconstrained MLE. Production systems enforce it via penalty.
- Wings can be too aggressive — the asymptotic slope b(1 ± ρ) can violate Roger Lee bounds for extreme ρ. Constrain b ≤ 4/(s(1 + |ρ|)).
- Time-dependent SVI fits ignore calendar-arbitrage. SSVI (next) addresses this.

---

## Surface SVI (SSVI)

SSVI (Gatheral–Jacquier 2014) extends SVI to the entire surface in (m, T). Definition:

$$
w(m, T) = \frac{\theta_T}{2} \!\left( 1 + \rho \phi(\theta_T) m + \sqrt{(\phi(\theta_T) m + \rho)^2 + (1 - \rho^2)} \right),
$$

where θ_T is ATMF total variance (a function of T), and φ is a function controlling smile width.

### Parameter Choices

Common choices:

- **Heston-like**: φ(θ) = (1/(λ θ)) (1 − (1 − e^{−λθ})/(λθ)), which mimics Heston's smile decay.
- **Power law**: φ(θ) = η/θ^γ, with γ ≈ 0.5 empirically fitting equity surfaces.

For these forms, SSVI has the same no-arb constraints as a single SVI slice, plus calendar-arbitrage constraints linking θ_T values.

### Calibration

SSVI is fitted to the entire surface jointly. The optimization minimizes

$$
\sum_{i, j} w_{ij} (\sigma_{\text{SSVI}}(m_i, T_j) - \sigma_{\text{market}}(m_i, T_j))^2,
$$

subject to no-arb constraints.

In practice, SSVI provides a good first-cut surface fit. For demanding applications (LSV calibration, exotic pricing), one might overlay residual corrections via local interpolation.

### Reality Check — SSVI in Production

SSVI's main advantage: by construction, it is calendar-arbitrage-free (with appropriate φ). For a production system requiring fast calibration and no-arb guarantees, SSVI is the workhorse. For calibration to extreme wings or unusual smile shapes, SSVI may need supplementing with other parameterizations.

---

## Lee's Wing Bounds

A formal statement of Lee's (2004) result:

For a vol surface with σ²(m, T) T = w(m, T) finite and continuous, the right wing satisfies

$$
\beta_R = \lim \sup_{m \to \infty} \frac{w(m, T)}{m} \le 2.
$$

For SVI, β_R = b(1 + ρ), and Lee's bound requires b(1 + ρ) ≤ 2. Symmetrically for the left wing.

### Empirical Wings

In practice, fitted equity surfaces have:
- Right wing slope b(1 + ρ) ≈ 0.4–1.0 (well within Lee's bound).
- Left wing slope b(1 − ρ) ≈ 0.6–1.5 (closer to but still below the bound for healthy fits).

When fitting fails because the bound is violated, the diagnosis is usually that the calibration data has noise in the wings or a few outlier strikes drive the fit.

---

## Part III — Local Volatility

Local volatility (Dupire 1994) is the unique deterministic-in-space volatility function σ_loc(S, t) such that the SDE

$$
dS_t = \mu(t) S_t \, dt + \sigma_{\text{loc}}(S_t, t) S_t \, dW_t
$$

reproduces all observed European option prices.

### Dupire's Equation

Given the surface C(K, T) of European call prices, the local volatility is

$$
\sigma_{\text{loc}}^2(K, T) = \frac{\partial_T C + (r - q) K \partial_K C + q C}{\tfrac{1}{2} K^2 \partial_{KK} C}.
$$

For a clean surface with smooth derivatives, Dupire's formula is exact.

### Derivation

Apply Tanaka's formula to the call payoff (S_T − K)^+:

$$
(S_T - K)^+ = (S_0 - K)^+ + \int_0^T 1_{\{S_t > K\}} \, dS_t + \tfrac{1}{2} \int_0^T \delta(S_t - K) \, d\langle S \rangle_t.
$$

The second term is a martingale under the risk-neutral measure (after discounting). Taking expectation and using d⟨S⟩_t = σ_loc² S² dt:

$$
e^{rT} C(K, T) = (S_0 - K)^+ + \int_0^T \mathbb{E}[(r - q) S_t 1_{\{S_t > K\}}] \, dt + \tfrac{1}{2} \int_0^T \mathbb{E}[\sigma_{\text{loc}}^2 S_t^2 \delta(S_t - K)] \, dt.
$$

Differentiating in T and rearranging yields Dupire's formula.

### Numerical Computation

In practice, partial derivatives are computed by finite differences on a smoothed call surface. Steps:

1. Fit a smooth surface (typically SVI or SSVI) to market call prices.
2. Compute the surface in (K, T) on a fine grid.
3. Apply finite differences:

$$
\sigma_{\text{loc}}^2(K, T) \approx \frac{[C(K, T + \Delta T) - C(K, T - \Delta T)]/(2\Delta T) + (r - q) K [C(K + \Delta K, T) - C(K - \Delta K, T)]/(2\Delta K) + q C(K, T)}{\tfrac{1}{2} K^2 [C(K + \Delta K, T) - 2C(K, T) + C(K - \Delta K, T)]/\Delta K^2}.
$$

```python
# Compute local volatility from a fitted surface.
def local_vol_from_calls(K_grid, T_grid, call_surface, r, q):
    """call_surface: 2D array C[i, j] for K_grid[i], T_grid[j]."""
    dK = K_grid[1] - K_grid[0]
    dT = T_grid[1] - T_grid[0]
    nK, nT = call_surface.shape
    sigma_loc2 = np.zeros((nK - 2, nT - 2))
    for i in range(1, nK - 1):
        for j in range(1, nT - 1):
            C = call_surface[i, j]
            dC_dT = (call_surface[i, j+1] - call_surface[i, j-1]) / (2*dT)
            dC_dK = (call_surface[i+1, j] - call_surface[i-1, j]) / (2*dK)
            d2C_dK2 = (call_surface[i+1, j] - 2*C + call_surface[i-1, j]) / dK**2
            num = dC_dT + (r - q) * K_grid[i] * dC_dK + q * C
            den = 0.5 * K_grid[i]**2 * d2C_dK2
            sigma_loc2[i-1, j-1] = num / max(den, 1e-12)
    return sigma_loc2
```

### Local Volatility in Implied-Vol Coordinates

Equivalent formula in (m, T) coordinates with implied vol σ_imp(m, T):

$$
\sigma_{\text{loc}}^2 = \frac{w_T}{1 - \frac{m}{w} w_m + \frac{1}{4}\!\left(-\frac{1}{4} - \frac{1}{w} + \frac{m^2}{w^2}\right) w_m^2 + \frac{1}{2} w_{mm}},
$$

where w = σ_imp² T and subscripts denote partial derivatives. This formulation avoids the ill-conditioned 1/(K² ∂²_K C) and is preferred numerically.

### No-Arbitrage and Local Vol

Local vol is well-defined (positive square root) iff the surface satisfies no-arbitrage. Specifically:
- ∂²C/∂K² ≥ 0 (butterfly).
- ∂C/∂T ≥ 0 (calendar).

These translate to specific constraints on σ_imp(m, T) via the formula above. SVI, SSVI, and other parameterizations respect these constraints.

### Reality Check — Local Vol Limitations

Local volatility *exactly fits* the surface today. But:

- **Forward smile dynamics are wrong**: under local vol, the smile flattens deterministically as the underlying moves. Empirically, the smile largely *moves with the spot* (sticky-delta). This causes systematic Greek mismatches.

- **Dependence on the surface shape**: small noise in the input surface causes large noise in σ_loc. Robust calibration requires smooth interpolation (SVI, SSVI) of the input.

- **Poor fit to barrier and exotic options**: even though vanillas are exact, exotic option prices under local vol often differ from market prices for the same exotics. This indicates the wrong dynamics.

The cure: use stochastic volatility (Heston, SABR, rBergomi) or, for production, local-stochastic volatility (LSV) which combines the exact surface fit with realistic dynamics.

---

## Part IV — Heston Model

Heston (1993) introduced a tractable stochastic volatility model that captures smile, skew, and term structure with five parameters.

### SDE

Under the risk-neutral measure ℚ:

$$
dS_t = (r - q) S_t \, dt + \sqrt{v_t} S_t \, dW_t^1,
$$
$$
dv_t = \kappa (\theta - v_t) \, dt + \sigma_v \sqrt{v_t} \, dW_t^2,
$$
$$
d\langle W^1, W^2 \rangle_t = \rho \, dt.
$$

Five parameters:
- κ: speed of mean reversion of variance.
- θ: long-run mean variance.
- σ_v: volatility of variance ("vol of vol").
- ρ: correlation between price and variance shocks. ρ < 0 in equities (leverage effect).
- v_0: initial variance.

The Feller condition 2κθ ≥ σ_v² ensures variance stays strictly positive.

### Characteristic Function

Heston's key advantage: the characteristic function of log S_T has closed form. For u ∈ ℝ:

$$
\phi(u) = \mathbb{E}[\exp(iu \log S_T)] = \exp[A(u, T) + B(u, T) v_0 + iu \log S_0 + iu (r - q) T],
$$

with

$$
B(u, T) = \frac{\kappa - \rho \sigma_v iu - d}{\sigma_v^2} \cdot \frac{1 - e^{-d T}}{1 - g e^{-d T}},
$$

$$
A(u, T) = \frac{\kappa \theta}{\sigma_v^2} \!\left[ (\kappa - \rho \sigma_v iu - d) T - 2 \log\!\frac{1 - g e^{-dT}}{1 - g} \right],
$$

where d = √((ρ σ_v iu − κ)² + σ_v² (iu + u²)) and g = (κ − ρ σ_v iu − d)/(κ − ρ σ_v iu + d).

### The "Little Heston Trap"

The naive square root in d can give numerical instabilities (Albrecher et al. 2007). The trap-free formulation uses:

$$
g_{\text{tf}} = \frac{1}{g}, \qquad d_{\text{tf}} = -d.
$$

This rearrangement is mathematically equivalent but numerically stable. Always use the trap-free formulation in production.

### European Option Pricing

Given the characteristic function, European calls are computed via Fourier inversion. The Lewis (2001) formula:

$$
C(K, T) = e^{-rT} \frac{1}{2\pi} \int_{-\infty}^{\infty} e^{-iuk} \frac{\phi(u - i) - 1}{iu(1 + iu)} \, du,
$$

with k = log K. The integral is computed numerically (Gauss-Laguerre quadrature or adaptive Romberg). For many strikes simultaneously, FFT-based methods (Carr–Madan 1999, Fang–Oosterlee 2008) are 10–100× faster.

### COS Method

Fang–Oosterlee (2008) proposed the COS method:

$$
C(K, T) \approx K e^{-rT} \sum_{n=0}^{N-1} F_n V_n,
$$

where F_n are Fourier coefficients of the characteristic function and V_n are coefficients of the call payoff. With N = 200 terms, machine-precision accuracy is reached for typical Heston calibrations.

```python
# Heston call pricing via COS method.
import numpy as np
from numpy import pi, sqrt, exp, log, cosh, sinh, real

def cos_method_heston_call(S0, K, T, r, q, kappa, theta, sigma_v, rho, v0, N=128, L=10):
    """COS method for European call under Heston."""
    x = log(S0/K)
    a = -L*sqrt(T)
    b = +L*sqrt(T)
    
    def cf(u, T):
        iu = 1j*u
        d = sqrt((rho*sigma_v*iu - kappa)**2 + sigma_v**2*(iu + u**2))
        g_ = (kappa - rho*sigma_v*iu - d) / (kappa - rho*sigma_v*iu + d)
        D = ((kappa - rho*sigma_v*iu - d)/sigma_v**2)*((1 - exp(-d*T))/(1 - g_*exp(-d*T)))
        C = (r-q)*iu*T + (kappa*theta/sigma_v**2)*((kappa - rho*sigma_v*iu - d)*T - 2*log((1 - g_*exp(-d*T))/(1 - g_)))
        return exp(C + D*v0 + iu*log(S0) - iu*log(K))
    
    n = np.arange(N)
    u = n*pi/(b-a)
    
    # COS coefficients of payoff (S - K)^+ in K-domain
    chi = lambda c, d, n: 1/(1 + (n*pi/(b-a))**2)*(np.cos(n*pi*(d-a)/(b-a))*np.exp(d) - np.cos(n*pi*(c-a)/(b-a))*np.exp(c) + n*pi/(b-a)*np.sin(n*pi*(d-a)/(b-a))*np.exp(d) - n*pi/(b-a)*np.sin(n*pi*(c-a)/(b-a))*np.exp(c))
    psi = lambda c, d, n: np.where(n == 0, d-c, (np.sin(n*pi*(d-a)/(b-a)) - np.sin(n*pi*(c-a)/(b-a)))*(b-a)/(n*pi))
    Vk = 2/(b-a) * (chi(0, b, n) - psi(0, b, n))
    
    F = real(cf(u, T) * exp(-1j*u*a))
    F[0] *= 0.5
    return K*exp(-r*T)*np.sum(F * Vk)

S0, K, T, r, q = 100, 100, 0.5, 0.03, 0.0
kappa, theta, sigma_v, rho, v0 = 2.0, 0.04, 0.5, -0.7, 0.04
print(f"Heston (COS): {cos_method_heston_call(S0, K, T, r, q, kappa, theta, sigma_v, rho, v0):.4f}")
```

### Calibration Workflow

Standard Heston calibration:

1. Collect market mid-prices for a grid of (K, T).
2. Convert each to implied volatility via Jäckel's algorithm.
3. Define loss function: L(θ) = ∑_{ij} w_{ij} (σ_{ij}^model(θ) − σ_{ij}^mkt)².
4. Optimize over (κ, θ, σ_v, ρ, v_0) using Levenberg–Marquardt or similar.
5. Validate on out-of-sample data.

Practical tips:
- Use multiple starting points to avoid local minima.
- Constrain ρ ∈ [−0.99, 0.99], σ_v ∈ [0.01, 2], κ ∈ [0.1, 20].
- Penalize Feller violations (2κθ < σ_v²) heavily.
- Weight ATM more than wings (Vega weighting).
- Run daily; check parameter stability.

### Reality Check — Heston Limitations

Heston's main shortcomings:
- **Skew is too flat at short maturities**. Real equity skew is much steeper than Heston produces with reasonable parameters. This drives the move to rough volatility.
- **Forward smile is too tame**. Heston's forward smile (the smile at T_2 conditional on the realized smile at T_1) is much milder than empirical evolution.
- **No jumps**. Real markets have jumps; Heston captures only smooth diffusion.

Extensions:
- **Heston with jumps** (Bates 1996): adds a jump term to dS. Captures short-dated skew better.
- **Double Heston**: two volatility factors. Captures more flexible term structures.
- **Heston with stochastic interest rates**: integrates rate dynamics. Important for long-dated options.

---

## Part V — SABR Model

SABR (Hagan et al. 2002) is the de-facto standard for FX, interest-rate, and some equity options. The model:

$$
dF_t = \alpha_t F_t^\beta \, dW_t^1,
$$
$$
d\alpha_t = \nu \alpha_t \, dW_t^2,
$$
$$
d\langle W^1, W^2 \rangle = \rho \, dt.
$$

Four parameters:
- α: initial volatility.
- β ∈ [0, 1]: backbone (β = 1 lognormal, β = 0 normal, β = 0.5 CIR-like).
- ν: vol-of-vol.
- ρ: correlation.

The forward F is the ATMF; SABR is typically used per-maturity with separate parameters per maturity.

### Hagan Asymptotic Formula

The implied volatility for a strike K is approximated by

$$
\sigma_{\text{impl}}(K, F) = \frac{\alpha}{(F K)^{(1-\beta)/2} \!\left[1 + \tfrac{(1-\beta)^2}{24} (\log F/K)^2 + \tfrac{(1-\beta)^4}{1920} (\log F/K)^4\right]} \cdot \frac{z}{\chi(z)} \cdot [1 + \cdots T],
$$

with z = (ν/α) (FK)^{(1-β)/2} log(F/K) and χ(z) = log((√(1 − 2ρz + z²) − ρ + z)/(1 − ρ)). The "[1 + … T]" includes a small-time correction that is critical for long maturities.

The full correction term:

$$
1 + T \!\left[ \tfrac{(1-\beta)^2}{24} \frac{\alpha^2}{(FK)^{1-\beta}} + \tfrac{1}{4} \frac{\rho \beta \nu \alpha}{(FK)^{(1-\beta)/2}} + \tfrac{2 - 3\rho^2}{24} \nu^2 \right].
$$

### ATM Volatility

At K = F, the formula simplifies:

$$
\sigma_{\text{impl}}(F, F) \approx \frac{\alpha}{F^{1-\beta}} \!\left[ 1 + T \!\left(\tfrac{(1-\beta)^2}{24} \frac{\alpha^2}{F^{2(1-\beta)}} + \tfrac{1}{4} \frac{\rho \beta \nu \alpha}{F^{1-\beta}} + \tfrac{2 - 3\rho^2}{24} \nu^2 \right)\right].
$$

This gives the ATM volatility as a function of (α, β, ρ, ν, F, T).

### Calibration

SABR has typically 3 free parameters per maturity (β is often fixed by market convention; e.g., β = 0.5 in equities, β = 1 in FX, β = 0.0 in normal models). Calibration:

1. For each maturity, observe vols at multiple strikes (typically 5–10 for FX, more for equities).
2. Fit (α, ρ, ν) (with fixed β) via least-squares.
3. Different maturities have different parameters; build the surface as a collection of fitted slices.

Smile term-structure modeling typically combines SABR slices with interpolation across maturities.

```python
# Hagan SABR formula.
import numpy as np

def hagan_sabr(F, K, T, alpha, beta, rho, nu):
    eps = 1e-7
    if abs(K - F) < eps:
        # ATM case
        atm_correction = 1 + T * ((1-beta)**2/24 * alpha**2 / F**(2*(1-beta)) +
                                    rho*beta*nu*alpha/(4*F**(1-beta)) +
                                    (2 - 3*rho**2)/24 * nu**2)
        return alpha / F**(1-beta) * atm_correction
    
    z = (nu/alpha) * (F*K)**((1-beta)/2) * np.log(F/K)
    chi = np.log((np.sqrt(1 - 2*rho*z + z**2) - rho + z) / (1 - rho))
    
    base = alpha / ((F*K)**((1-beta)/2) * 
                    (1 + (1-beta)**2/24*np.log(F/K)**2 + (1-beta)**4/1920*np.log(F/K)**4))
    correction = 1 + T * ((1-beta)**2/24 * alpha**2 / (F*K)**(1-beta) +
                          rho*beta*nu*alpha/(4*(F*K)**((1-beta)/2)) +
                          (2 - 3*rho**2)/24 * nu**2)
    return base * (z/chi) * correction

# Example: ATM and 90% IV under SABR
F, T = 100, 1.0
alpha, beta, rho, nu = 0.20, 0.5, -0.3, 0.4
print(f"ATM IV: {hagan_sabr(F, F, T, alpha, beta, rho, nu):.4f}")
print(f"90% IV: {hagan_sabr(F, 90, T, alpha, beta, rho, nu):.4f}")
```

### SABR Wings and Negative Density

The Hagan formula has known issues at extreme strikes:
- For very low strikes, the implied density can become negative.
- The asymptotic expansion fails when (1 − β) log(K/F) is large.

Modern fixes:
- **PDE-based SABR**: integrate the actual SDE numerically. Slower but exact.
- **Hagan refined formula** (Hagan et al. 2017): includes higher-order corrections.
- **Free-boundary SABR**: handles the K → 0 limit cleanly.

### Shifted SABR for Negative Rates

When rates can go negative (post-2008 environment), the SABR forward F can also be negative. The shifted SABR uses

$$
F_t \to F_t + s,
$$

where s is a positive shift. The shifted SABR is fitted to the shifted strikes K + s. Common in EUR rates trading.

### Reality Check — SABR in Production

SABR's main strength: simple calibration with parameters that have direct trading interpretation (α, ρ, ν → vol level, skew, butterfly). Its main weakness: the asymptotic formula is approximate and can fail in extreme conditions.

Production systems use SABR as a default and PDE-based extensions for stress conditions. For interest-rate swaptions, the SABR with stochastic correlation (e.g., ρ_t process) is sometimes used for additional flexibility.

Document 7 (Stochastic Volatility for Gold) covers SABR-like models in the gold market.

---

## SABR Wings, Negative Rates, Shifted SABR

(Continued from previous section; treated more thoroughly here.)

### Implied Density Under SABR

The implied risk-neutral density at maturity T is the second derivative of the call price with respect to K. For SABR with the Hagan formula, this density can become negative for very low strikes. The pathology:

$$
\frac{\partial^2 C}{\partial K^2} < 0 \quad \text{for } K < K^*,
$$

for some K* > 0. Below K*, the calibrated surface is "non-arbitrage-free" in the strict sense.

This is usually invisible in practice because traded options are bracketed away from K*. It becomes visible when extrapolating to extreme strikes for exotic option pricing.

### Wright (2018) and Modern Variants

Wright (2018) and others have proposed variants of the asymptotic formula that respect the density positivity constraint. The trade-off: more complex formulas, slower calibration.

For most production applications, a hybrid approach works:
- Use Hagan formula for K ∈ [K_lower, K_upper] (the well-behaved region).
- Switch to PDE-based pricing for K outside this region.
- Document the boundary and refresh as parameters change.

### Reality Check — When SABR Hits the Limits

SABR breaks down in:
- Very long maturities (10Y+ swaptions).
- Negative-rate environments without proper shift.
- Very low-strike puts (deep OTM).
- Extreme volatility regimes (vol-of-vol exceeding ~150%).

For these, the move is to local-stochastic vol or rough-vol models.

---

## Part VI — Local-Stochastic Volatility (LSV)

LSV combines the exact surface fit of local volatility with the realistic dynamics of stochastic volatility. The standard formulation:

$$
dS_t = (r - q) S_t \, dt + L(S_t, t) \sqrt{v_t} S_t \, dW_t^1,
$$
$$
dv_t = \kappa (\theta - v_t) \, dt + \sigma_v \sqrt{v_t} \, dW_t^2.
$$

The leverage function L(S, t) is chosen so that the model exactly reproduces market prices of European options. The variance v follows a CIR-like process; this provides the "stochastic" part of the dynamics.

### Calibration via Markov Projection

Markov projection (Gyöngy 1986): given the LSV process, the Dupire formula must be satisfied. This gives

$$
L(S, t)^2 \cdot \mathbb{E}^{\mathbb{Q}}[v_t \mid S_t = S] = \sigma_{\text{loc}}^2(S, t).
$$

So

$$
L(S, t) = \frac{\sigma_{\text{loc}}(S, t)}{\sqrt{\mathbb{E}^{\mathbb{Q}}[v_t \mid S_t = S]}}.
$$

Calibration is iterative:
1. Compute σ_loc(K, T) from the market surface (Dupire).
2. Initialize L (e.g., L = 1).
3. Run a Monte Carlo simulation of the LSV.
4. At each grid point (S, t), estimate 𝔼[v | S].
5. Update L using the formula above.
6. Iterate until convergence.

The procedure is computationally intensive (Monte Carlo + conditional expectation) but converges in 5–10 iterations for typical surfaces.

### Particle Method

Guyon and Henry-Labordère (2012) introduced the particle method for LSV calibration: simulate many particles, each with a different (S, v) trajectory. Use kernel estimation to compute 𝔼[v | S] empirically. This is more accurate than naive grid-based methods.

```python
# Skeleton: LSV calibration via particle method (illustrative).
import numpy as np

def lsv_particle_calibration(local_vol_surface, S0, T, n_paths=20_000, n_steps=100, n_iter=10):
    """Approximate LSV calibration. local_vol_surface: function (S, t) -> sigma."""
    dt = T / n_steps
    np.random.seed(42)
    
    # Initialize leverage as 1
    def L(S, t, leverage_grid):
        # Interpolate leverage from grid
        return np.ones_like(S)
    
    # Initialize variance process (Heston-like)
    kappa, theta, sigma_v, rho = 2.0, 0.04, 0.5, -0.7
    
    for iteration in range(n_iter):
        # Simulate paths
        S = np.full(n_paths, S0)
        v = np.full(n_paths, theta)
        all_S = np.zeros((n_paths, n_steps + 1))
        all_v = np.zeros((n_paths, n_steps + 1))
        all_S[:, 0] = S; all_v[:, 0] = v
        
        for j in range(n_steps):
            t = j*dt
            Z1 = np.random.normal(size=n_paths)
            Z2 = rho*Z1 + np.sqrt(1-rho**2)*np.random.normal(size=n_paths)
            
            v_pos = np.maximum(v, 1e-10)
            sigma_eff = L(S, t, None) * np.sqrt(v_pos)
            
            S = S * np.exp(sigma_eff*np.sqrt(dt)*Z1 - 0.5*sigma_eff**2*dt)
            v = np.maximum(v + kappa*(theta - v)*dt + sigma_v*np.sqrt(v_pos*dt)*Z2, 1e-10)
            
            all_S[:, j+1] = S
            all_v[:, j+1] = v
        
        # Update leverage by matching local vol
        # This requires conditional expectation E[v | S] from the simulation
        # Here we just record one iteration; full impl needs kernel regression
        break
    
    return all_S, all_v
```

In production, LSV calibration is run nightly with extensive caching.

### Reality Check — LSV is the Production Standard

For equity exotic books at major banks, LSV is the standard model:
- Exactly fits the surface (no calibration error on vanillas).
- Realistic dynamics (forward smile is closer to empirical sticky-delta).
- Tractable enough for daily recalibration and Monte Carlo pricing.

Limitations:
- Computationally expensive vs Heston.
- The leverage function L is a *correction*; small calibration errors in σ_loc translate to errors in L.
- No closed-form for vanilla options; must use Monte Carlo or PDE.

---

## Part VII — Rough Volatility

Rough volatility is the active research frontier. The empirical observation (Gatheral, Jaisson, Rosenbaum 2014): the realized log-variance of major indices has Hurst exponent H ≈ 0.07–0.13, much rougher than Brownian (H = 0.5).

### rBergomi Model

rBergomi (Bayer, Friz, Gatheral 2016): the variance process is driven by a fractional Brownian motion:

$$
v_t = \xi_0(t) \exp\!\left( \eta \tilde W_t^H - \tfrac{1}{2} \eta^2 t^{2H} \right),
$$

where W̃^H is a Volterra-type fractional process with kernel K(t, s) ~ (t − s)^{H − 1/2}. The forward variance ξ_0(t) is calibrated to ATMF total variance: ξ_0(t) = ∂_t (σ²_atmf t).

Five parameters: H, η, ρ, plus the forward variance curve ξ_0.

### Pricing under rBergomi

Vanilla pricing under rBergomi requires Monte Carlo because the variance is non-Markov. The standard "hybrid" simulation (Bayer et al. 2017) uses an analytical decomposition of the kernel into a singular and a smooth part, and simulates each separately.

```python
# Skeleton for rBergomi simulation (hybrid scheme).
import numpy as np

def hybrid_rbergomi_paths(T, n_steps, n_paths, H, eta, rho, xi0_func):
    """Simulate (v, S) under rBergomi using hybrid scheme."""
    dt = T / n_steps
    np.random.seed(42)
    
    # Generate two correlated Brownian increments
    Z1 = np.random.normal(size=(n_paths, n_steps)) * np.sqrt(dt)
    Z2 = rho*Z1 + np.sqrt(1-rho**2)*np.random.normal(size=(n_paths, n_steps))*np.sqrt(dt)
    
    # Build fractional Brownian motion W^H using exact decomposition
    # (skipped here for brevity; production uses scipy.signal.fftconvolve or library)
    W_H = np.zeros((n_paths, n_steps + 1))
    for t_idx in range(1, n_steps + 1):
        # Naive integration; production uses Riemann-Liouville exact scheme
        kernel = (np.arange(t_idx)+0.5)**(H-0.5) * np.sqrt(dt)
        W_H[:, t_idx] = np.einsum('ts,t->s', Z1[:, :t_idx]*kernel.reshape(-1, 1), np.ones(n_paths))
    
    # Variance process
    t_arr = np.linspace(0, T, n_steps + 1)
    xi0 = np.array([xi0_func(t) for t in t_arr])
    V = xi0 * np.exp(eta*W_H - 0.5*eta**2*t_arr**(2*H))
    
    # Stock process
    S = np.full(n_paths, 100.0)
    paths = np.zeros((n_paths, n_steps + 1))
    paths[:, 0] = S
    for j in range(n_steps):
        S = S * np.exp(np.sqrt(V[:, j])*Z2[:, j] - 0.5*V[:, j]*dt)
        paths[:, j+1] = S
    
    return paths, V
```

### Why Rough Vol Matters

Empirical advantages of rough vol:
- **Short-dated SPX skew is much steeper than Heston can produce.** rBergomi naturally produces this.
- **Forward smile dynamics** under rBergomi match empirical "sticky strike-ish" evolution better.
- **Small number of parameters** despite the complex non-Markov dynamics.

Limitations:
- **Non-Markov**: no PDE methods, only Monte Carlo.
- **Calibration is slow**: each evaluation requires a Monte Carlo run.
- **Hedging interpretation is not yet fully developed**.

### Reality Check — Rough Vol in Practice

Rough volatility is research-standard for short-dated equity index options. Production adoption is partial:
- Some quantitative hedge funds use rBergomi for pricing exotic equity-index products.
- Large bank desks typically still use Heston or LSV as primary, with rough-vol stress-testing.
- Daily recalibration of rBergomi is computationally demanding.

The story is unfolding: machine learning approximations of rBergomi (deep neural networks trained on Monte Carlo) are being deployed for fast pricing. This is an active area.

---

## Part VIII — Forward Smile Dynamics

The static surface tells you what the smile looks like today. Forward smile dynamics tell you how the smile evolves as the spot moves. The two extremes:

### Sticky Strike

Implied volatility at each strike is constant as spot moves: σ_imp(K, T) is invariant in S. Equivalently, σ_imp(m, T) shifts in m as spot moves. In equity terms: as spot drops, OTM put IVs rise.

Sticky strike is the *implicit* assumption of pure local volatility models when re-applied with new spot.

### Sticky Delta (Sticky Moneyness)

Implied volatility at each delta is constant: σ_imp(Δ, T) is invariant in S. Equivalently, σ_imp(m, T) is constant in m as spot moves. In equity terms: the smile shape is preserved; the entire smile shifts with the spot.

Sticky delta is the *implicit* assumption of pure stochastic volatility models with constant correlation.

### Sticky Vol (Sticky Skew)

The skew at each maturity is constant. Equivalent to a particular blend of sticky strike and sticky delta.

### Empirical

Real markets are *between* sticky strike and sticky delta, with the regime varying by maturity:
- Short-dated (T ≤ 1M): more sticky-strike (skew is "spotty").
- Medium-dated (1M–6M): mixture.
- Long-dated (T ≥ 1Y): more sticky-delta (smile rolls with spot).

For equity indices with typical leverage effect, the "ratio" of sticky-strike to sticky-delta is roughly 0.4–0.6 short-dated and 0.3–0.4 long-dated.

### Hedging Implications

The Delta of an option depends on the smile dynamics assumption:
- Under sticky strike: standard Black–Scholes Delta.
- Under sticky delta: BS Delta + Vega × (∂σ_imp/∂S)|_strike.

For a sold OTM put on SPX, the difference can be significant: BS Delta might be 0.2, but sticky-delta-adjusted Delta might be 0.1. The wrong assumption causes systematic hedging error.

### Reality Check — Hedging Under Wrong Dynamics

A hedger using BS Delta in a market that follows sticky-delta dynamics will systematically over-hedge (or under-hedge) by the Vega-weighted skew shift. The cumulative cost is in the dollars per share per day range — small per-trade but additive.

Production systems compute multiple Deltas (BS, sticky-strike, sticky-delta) and let traders choose based on regime. Some advanced systems estimate the regime in real-time from observed Delta–PnL relationships.

---

## Variance Swap Pricing and Replication

A **variance swap** is a forward contract on realized variance: pay K_var (strike), receive realized variance σ²_realized over [0, T]. The classical replication (Demeterfi, Derman, Kamal, Zou 1999):

$$
\text{Var swap fair value} = \frac{2}{T} \int_0^T \!\left( \frac{1}{S_t} dS_t - d\log S_t \right) dt = \frac{2}{T} \int_0^T \!\left( \frac{1}{S_t} dS_t - d\log S_t \right) dt.
$$

In risk-neutral expectation, this equals

$$
K_{\text{var}} = \frac{2}{T} \!\left[ rT - (e^{rT} - 1) - \log(F_0/S_0) \right] + \frac{2}{T} \int_0^\infty \frac{1}{K^2} P(K) dK,
$$

where P(K) are put prices and F_0 is the forward. So the variance-swap strike is approximately the integral of OTM option prices weighted by 1/K². This gives a model-free pricing formula.

### Implementation

In practice:
1. Collect OTM call and put prices (both wings).
2. Compute the integral via trapezoid or Simpson.
3. Adjust for the discrete strike grid via interpolation.

The result is the fair price of variance over [0, T]. Compare to realized variance to detect variance risk premium.

### Reality Check — Replication Imperfections

- **Strike discreteness**: real options trade at discrete strikes; the integral has finite-grid bias. Fix: extrapolate the wings.
- **Wing tail**: deep OTM puts contribute the most "risk" per dollar. Stale or thinly-traded wings cause estimation error.
- **Jumps**: the replication assumes continuous paths; jumps add corrections that depend on the jump distribution.

For VIX (CBOE Volatility Index), the calculation is performed daily on SPX options, with regulatory specifications about strike inclusion and weighting.

Document 27 (Volatility Risk Premium) covers the variance-swap market in detail.

---

## VIX Term Structure and Vol-of-Vol

The VIX Index is a 30-day weighted average of OTM SPX options, calculated to approximate the variance-swap rate at 30-day maturity. The VIX *futures* curve gives forward variances at multiple maturities (1M, 2M, 3M, …).

### Term Structure Patterns

- **Contango (normal)**: VIX futures > VIX spot. The "fair price" of forward variance exceeds current realized variance. Persistent in calm regimes.
- **Backwardation**: VIX futures < VIX spot. Spot vol exceeds expected forward vol. Occurs during shocks (March 2020) and acute risk-off.
- **Steep curve**: long-dated VIX futures > short-dated by a large amount. Indicates expectations of vol increasing in the future.

### Trading the Term Structure

- **VIX futures roll**: in contango, short VIX futures and roll forward; gain from roll-down. In backwardation, the opposite.
- **VXX/UVXY**: ETPs that hold rolling VIX futures; they decay rapidly in contango.
- **VIX calendar**: long short-dated VIX, short long-dated VIX (or vice versa), trading the spread.

Document 24 (VIX Term Structure Arbitrage) covers this in detail.

### Vol-of-Vol

The volatility of VIX itself ("vol-of-vol") is a parameter in stochastic-volatility models (σ_v in Heston). Empirically, it is highly time-varying:
- ~50–80% in calm regimes.
- Spikes to 150–250% in vol shocks.

Modeling vol-of-vol explicitly is the domain of double-Heston, Heston with stochastic vol-of-vol, and more advanced models.

---

## Cross-Sectional Implied Vol — Single-Stock vs Index

Single-stock IVs are typically higher than index IV (idiosyncratic risk). The relationship:

$$
\sigma_{\text{index}}^2 \approx \sum_i w_i^2 \sigma_i^2 + \sum_{i \ne j} w_i w_j \rho_{ij} \sigma_i \sigma_j,
$$

where w_i are index weights and ρ_{ij} are the implied correlations.

### Implied Correlation

Given ATM index IV and ATM single-stock IVs, solve for the implied correlation matrix. With assumption of constant correlation (single ρ for all pairs):

$$
\rho_{\text{impl}} = \frac{\sigma_{\text{index}}^2 - \sum_i w_i^2 \sigma_i^2}{\sum_{i \ne j} w_i w_j \sigma_i \sigma_j}.
$$

This is the **dispersion correlation**. It typically ranges from 0.3 (calm) to 0.7 (crisis).

### Dispersion Trade

Buy single-stock variance, sell index variance. Profitable when implied correlation > realized correlation (the typical case). Document 60 (Volatility Dispersion Trading) covers this in depth.

---

## Calibration in Practice

### Loss Functions

Standard:
$$
L(\theta) = \sum_{ij} w_{ij} (\sigma_{ij}^{\text{model}} - \sigma_{ij}^{\text{mkt}})^2.
$$

Variants:
- **Vega-weighted**: w_{ij} = Vega_{ij}². Up-weights ATM.
- **Volume-weighted**: w_{ij} ∝ traded volume. Up-weights liquid strikes.
- **L1 norm**: ∑ |σ_ij^model − σ_ij^mkt|. Less sensitive to outliers.
- **Robust** (Huber loss): Quadratic for small errors, linear for large.

### Solvers

- **Levenberg–Marquardt**: fast for least-squares; sensitive to initial guess.
- **BFGS**: general-purpose; can be slow for high-dimensional.
- **Differential evolution**: global; slow but reliable.
- **Trust-region**: robust; works for non-smooth objectives.

For Heston, multiple starting points + Levenberg–Marquardt is the standard.

### Diagnostics

After calibration:
- **Residual surface**: σ_model − σ_mkt at each (K, T). Should be O(0.01) or less.
- **Parameter trajectory**: fit on each of last 30 days; parameters should be stable (no jumps).
- **Sensitivity**: how do parameters change with small data perturbations? Unstable parameters indicate overfitting.
- **Out-of-sample**: predict tomorrow's surface. Compare to actual.

### Reality Check — Calibration is a Daily Job

Production teams run calibration:
- Daily, using closing prices.
- Intraday on major moves (>1% spot or >5% IV).
- Special runs around earnings, FOMC, dividends.

A calibration that takes too long (e.g., > 1 minute for the SPX surface) is impractical. Optimization is a constant trade-off between accuracy and speed.

---

## Real Trading Considerations

The vol surface is the *input*; PnL is the *output*. The links:

### Vega and Vol PnL

Vega = ∂V/∂σ. A 1-vol-point move in IV translates to a Vega-dollar move in option PnL. For an ATM 1Y SPX option on $100M notional with σ = 20%, Vega is roughly $50K per vol point.

### Vanna and Volga

Second-order Greeks:
- **Vanna** = ∂²V/∂σ∂S. Cross-sensitivity to spot and IV.
- **Volga** (Vomma) = ∂²V/∂σ². Sensitivity to vol-of-vol.

These appear in higher-order hedging schemes (e.g., Vanna–Volga pricing for exotics in FX).

### Smile Dynamics PnL

PnL = Δ_BS × ΔS + Vega × Δσ + ...

The Vega × Δσ term depends on smile dynamics. Under sticky-delta, Δσ at fixed K = ∂σ/∂m × Δm = ∂σ/∂m × (-ΔS/S). So the effective Delta includes a Vega × ∂σ/∂m × (-1/S) term.

### Calibration Lag

The surface used for hedging is the surface from yesterday or this morning. Real markets have moved since then. The hedge is therefore against a stale surface, introducing implementation lag. This is a real cost and is often the largest source of discretionary trading P&L.

### Reality Check — Surface Trading is a Specialty

A single trader cannot do everything. A typical equity-derivatives desk has:
- **Volatility traders** (manage Vega, Volga, smile risk).
- **Delta hedgers** (manage Spot risk, computing Delta from chosen smile dynamics).
- **Risk managers** (oversee VaR, scenario PnL, concentration limits).
- **Quants** (calibrate surfaces, build models, refine numerics).

The vol surface is the shared language across all these roles.

---

## Reference Tables, Cheat Sheets, Bibliography

### Quick Reference

| Concept | Symbol | Units / Range |
|---|---|---|
| Black–Scholes IV | σ_imp | 0–5 (typically 0.05–0.5) |
| Total variance | w | σ² T |
| ATMF | F | underlying × e^(r-q)T |
| Log-moneyness | m | log(K/F) |
| Delta | Δ | 0–1 |
| Skew | ∂σ/∂m | -0.2 to 0.2 (per unit m) |
| Curvature | ∂²σ/∂m² | 0.1–1.0 |
| Heston params | (κ, θ, σ_v, ρ, v_0) | varies |
| SABR params | (α, β, ρ, ν) | varies |
| VRP | σ_imp − σ_realized | 0.02–0.05 (avg) |

### Bibliography

- **Black, F. and Scholes, M. (1973), "The Pricing of Options and Corporate Liabilities", *Journal of Political Economy* 81(3): 637–654.** Original.
- **Heston, S. (1993), "A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options", *Review of Financial Studies* 6(2): 327–343.** Heston model.
- **Dupire, B. (1994), "Pricing with a Smile", *Risk Magazine* 7(1): 18–20.** Local volatility.
- **Hagan, P., Kumar, D., Lesniewski, A., Woodward, D. (2002), "Managing Smile Risk", Wilmott Magazine, September: 84–108.** SABR.
- **Gatheral, J. (2004), "A Parsimonious Arbitrage-Free Implied Volatility Parameterization", presentation. The original SVI.
- **Gatheral, J. (2006), *The Volatility Surface*, Wiley.** Comprehensive practitioner reference.
- **Gatheral, J. and Jacquier, A. (2014), "Arbitrage-Free SVI Volatility Surfaces", *Quantitative Finance* 14(1): 59–71.** SSVI.
- **Albrecher, H., Mayer, P., Schoutens, W., Tistaert, J. (2007), "The Little Heston Trap", Wilmott Magazine, January: 83–92.** Numerics.
- **Carr, P. and Madan, D. (1999), "Option Valuation Using the Fast Fourier Transform", *Journal of Computational Finance* 2(4): 61–73.** FFT pricing.
- **Fang, F. and Oosterlee, C. W. (2008), "A Novel Pricing Method for European Options Based on Fourier-Cosine Series Expansions", *SIAM Journal on Scientific Computing* 31(2): 826–848.** COS method.
- **Bayer, C., Friz, P., and Gatheral, J. (2016), "Pricing Under Rough Volatility", *Quantitative Finance* 16(6): 887–904.** rBergomi.
- **Gatheral, J., Jaisson, T., and Rosenbaum, M. (2018), "Volatility Is Rough", *Quantitative Finance* 18(6): 933–949.** Empirical foundation.
- **Bergomi, L. (2016), *Stochastic Volatility Modeling*, Chapman & Hall.** Production-grade reference for SV modeling.
- **Demeterfi, K., Derman, E., Kamal, M., Zou, J. (1999), "More Than You Ever Wanted to Know About Volatility Swaps", Goldman Sachs.** Variance swap replication.
- **Lee, R. (2004), "The Moment Formula for Implied Volatility at Extreme Strikes", *Mathematical Finance* 14(3): 469–480.** Wing bounds.
- **Guyon, J. and Henry-Labordère, P. (2014), *Nonlinear Option Pricing*, Chapman & Hall.** LSV calibration via particle methods.
- **Jäckel, P. (2015), "Let's Be Rational", Wilmott Magazine.** State-of-the-art IV inversion.

### Cross-References

- Document 7 — Stochastic Volatility Modeling for Gold.
- Document 21 — Long Straddle Gamma.
- Document 22 — Short Iron Condor.
- Document 24 — VIX Term Structure Arbitrage.
- Document 25 — Dispersion Trading.
- Document 26 — Calendar Spreads.
- Document 27 — Volatility Risk Premium.
- Document 51 — Vanna–Volga Pricing.
- Document 60 — Volatility Dispersion Trading.
- Document 200 — Stochastic Calculus.
- Document 201 — Market Microstructure.

---

## Coda: The Surface as a Trading Object

The vol surface is more than a calibration target. It is itself a tradable object — every shift in skew, every change in curvature, every term-structure rotation is a P&L event for someone.

A trader who treats the surface as a museum exhibit will fit a model and price exotic options. A trader who treats the surface as a *source of trades* will look at the shape, infer what positions are crowded, identify mispricings between strikes or maturities, and structure trades that bet on the surface evolving in a predictable way.

Both views have a place. This document is for the first view — building, calibrating, and using the surface for pricing and hedging. The trades that arise from the second view (skew, dispersion, calendar, curvature) are in companion documents (24, 25, 27, 60). They depend on this one for their language and tools.

The remaining documents in this expansion build on this foundation. Document 206 (Extreme Value Theory) treats the tails that the smile encodes. Document 207 (Copulas) covers cross-asset dependence beyond linear correlation. Document 208 (Optimal Execution) addresses the hedging-cost side of the trade. Document 211 (Backtesting) shows how to validate any model that fits today's surface against tomorrow's reality.

---

*End of document 202. Approximately 4,800 lines as initially written; targeted to extend to 12,000 lines via additional worked examples, deeper calibration code, and extensive empirical case studies in subsequent expansion passes.*
