# 07. Stochastic Volatility Modeling for Gold (XAUUSD)

**Abstract**
Commodity markets like Gold exhibit distinct volatility dynamics—fat tails, mean reversion, and leverage effects—that Black-Scholes cannot capture. This document details the **Heston Model** for stochastic volatility, the **Ornstein-Uhlenbeck (OU)** process for mean reversion, and **SVI Parametrization** for implied volatility surface calibration.

---

## 1. The Heston Stochastic Volatility Model

The Heston model assumes that the asset price $S_t$ and its variance $v_t$ follow coupled Stochastic Differential Equations (SDEs).

### 1.1 System of SDEs
$$ dS_t = \mu S_t dt + \sqrt{v_t} S_t dW_t^S $$
$$ dv_t = \kappa (	heta - v_t) dt + \sigma \sqrt{v_t} dW_t^v $$

Where:
*   $W_t^S, W_t^v$ are Brownian motions with correlation $ho$ ($dW_t^S dW_t^v = ho dt$).
*   $\kappa > 0$: Mean reversion speed.
*   $	heta > 0$: Long-run variance.
*   $\sigma > 0$: Volatility of volatility (Vol-of-Vol).

**Feller Condition:**
To ensure variance $v_t$ remains positive almost surely:
$$ 2\kappa	heta > \sigma^2 $$

### 1.2 Characteristic Function (Fourier Transform)
Option pricing is performed by inverting the characteristic function $\phi(u)$:
$$ C(K) = S_0 P_1 - K e^{-rT} P_2 $$
Where $P_j$ are probabilities derived from:
$$ P_j = \frac{1}{2} + \frac{1}{\pi} \int_0^{\infty} 	ext{Re}\left( \frac{e^{-iu \ln K} \phi_j(u)}{iu} ight) du $$

This requires numerical integration (e.g., Gauss-Laguerre quadrature).

---

## 2. Ornstein-Uhlenbeck (OU) Mean Reversion

Gold prices often exhibit mean-reverting behavior around a fundamental value or moving average.

### 2.1 The OU Process
Let $X_t$ be the log-price or spread.
$$ dX_t = \lambda (\mu - X_t) dt + \sigma dW_t $$

The solution is:
$$ X_t = X_0 e^{-\lambda t} + \mu (1 - e^{-\lambda t}) + \sigma \int_0^t e^{-\lambda(t-s)} dW_s $$

**Half-Life of Mean Reversion:**
$$ H = \frac{\ln(2)}{\lambda} $$
If $H$ is small (e.g., hours), the strategy is high-frequency mean reversion. If $H$ is large (months), it is a macro trade.

---

## 3. Volatility Surface Calibration (SVI)

Implied volatility varies by strike $K$ and maturity $T$ (Volatility Smile). We fit the **Stochastic Volatility Inspired (SVI)** parameterization to market data.

### 3.1 Raw SVI Parametrization
The total implied variance $w(k, T) = \sigma_{BS}^2(k, T) \cdot T$ is modeled as:
$$ w(k) = a + b \{ ho(k - m) + \sqrt{(k - m)^2 + \sigma^2} \} $$

Where $k = \ln(K/F)$ is log-moneyness.
*   $a$: Vertical shift (level).
*   $b$: Angle between asymptotes (slope).
*   $ho$: Rotation (skew).
*   $m$: Horizontal shift.
*   $\sigma$: Smoothness of the vertex (at-the-money curvature).

**Optimization Problem:**
Minimize the squared error between model $w_{SVI}(k_i)$ and market quotes $w_{mkt}(k_i)$:
$$ \min_{\{a, b, ho, m, \sigma\}} \sum_{i} (w_{SVI}(k_i) - w_{mkt}(k_i))^2 $$
Subject to no-arbitrage constraints (e.g., $w(k)$ must be convex).

---

**References:**
1.  Heston, S. L. (1993). "A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options".
2.  Gatheral, J., & Jacquier, A. (2014). "Arbitrage-Free SVI Volatility Surfaces".
3.  Uhlenbeck, G. E., & Ornstein, L. S. (1930). "On the Theory of the Brownian Motion".
