# 02 - Mean Reversion & Statistical Arbitrage (The Bible)

**Volume:** 02 of 50
**Strategy Type:** Mean Reversion / StatArb / Counter-Trend
**Risk Profile:** Catching a Falling Knife / Fat Tail Risk
**Mathematical Basis:** Ornstein-Uhlenbeck Process ($dx_t = \theta(\mu - x_t)dt + \sigma dW_t$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Physics of Mean Reversion](#2-the-physics-of-mean-reversion)
    * 2.1. The Elastic Band (OU Process)
    * 2.2. Half-Life ($\tau$): The Speed of Gravity
    * 2.3. The Stationarity Test (ADF)
3. [The Strategies](#3-the-strategies)
    * 3.1. Bollinger Band Reversion (Standard)
    * 3.2. Triple SMA Ribbon (Visual)
    * 3.3. RSI Divergence (Momentum)
4. [Statistical Arbitrage (Pairs)](#4-statistical-arbitrage-pairs)
5. [Mathematics of the OU Process](#5-mathematics-of-the-ou-process)
    * 5.1. Deriving Theta, Mu, and Sigma
    * 5.2. Calculating Optimal Entry/Exit
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Statsmodels OU Fit)
    * 6.2. Rust (Streaming Half-Life Calculation)
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Mean Reversion** is the bet that "This time is NOT different."
It relies on the statistical principal that extreme deviations from an equilibrium price are unsustainable.
While Strategy 04 (Trend) bets on divergence, Strategy 02 bets on convergence.
This document serves as the **Master Theory** file for all Mean Reversion strategies in GOLIATH, integrating the physics of the **Ornstein-Uhlenbeck (OU) Process** and the concept of **Half-Life.**

---

# 2. The Physics of Mean Reversion

## 2.1. The Elastic Band (OU Process)

Prices do not just wander randomly (Random Walk); they are tethered.
The **Ornstein-Uhlenbeck Process** models this using three parameters:

1. **$\mu$ (Mu):** The Long-Term Mean (The Anchor).
2. **$\sigma$ (Sigma):** The Volatility (The Wind).
3. **$\theta$ (Theta):** The Mean Reversion Speed (The strength of the elastic band).
    * High $\theta$: Price snaps back instantly (HFT).
    * Low $\theta$: Price drifts for months (Macro).

## 2.2. Half-Life ($\tau$)

From `042_Half_Life`:
The **Half-Life** is the time it takes for the price to return *halfway* to the mean after a shock.
$$ \text{Half Life} = \frac{\ln(2)}{\theta} $$
**Trading Rule:** Do not hold a mean reversion trade longer than its Half-Life. If time > Half-Life and price hasn't moved, the trade is dead. Exit.

## 2.3. Stationarity

Before trading Mean Reversion, you must prove the asset is **Stationary** (Augmented Dickey-Fuller Test).
If ADF P-value > 0.05, the asset is trending. DO NOT Mean Revert.

---

# 3. The Strategies

(See individual Strategy Files 12, 13, 16 for specific rules).

* **Strategy 12:** Bollinger Bands (Uses $\sigma$ as the band width).
* **Strategy 16:** Pairs Trading (Uses OU on the Spread).

---

# 4. Statistical Arbitrage (Pairs)

StatArb is simply Mean Reversion applied to a synthetic asset (The Spread).
We construct a spread $S = A - \beta B$ such that $S$ follows an OU process.
We buy $S$ when it is low and sell $S$ when it is high.

---

# 5. Mathematics of the OU Process

From `041_OU_Params`:

The stochastic differential equation:
$$ dx_t = \theta (\mu - x_t) dt + \sigma dW_t $$

To fit this to discrete data, we use Linear Regression of $x_{t+1}$ against $x_t$:
$$ x_{t+1} = \alpha + \beta x_t + \epsilon $$

* **Theta ($\theta$):** $-\frac{\ln(\beta)}{\Delta t}$
* **Mu ($\mu$):** $\frac{\alpha}{1 - \beta}$
* **Sigma ($\sigma$):** $\text{std}(\epsilon) \sqrt{\frac{-2 \ln \beta}{\Delta t (1 - \beta^2)}}$

---

# 6. Implementation: Production Grade

## 6.1. Python (Fitting OU)

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm

def fit_ou_process(series):
    """
    Fits an Ornstein-Uhlenbeck process to a time series.
    Returns: theta (speed), mu (mean), sigma (volatility)
    """
    x = series.values
    x_shift = np.roll(x, 1)
    
    # Drop first NaN
    x = x[1:]
    x_shift = x_shift[1:]
    
    # Regress x[t] on x[t-1]
    X = sm.add_constant(x_shift)
    model = sm.OLS(x, X).fit()
    
    alpha = model.params[0]
    beta = model.params[1]
    resid_std = model.resid.std()
    
    dt = 1.0 # Assuming daily data is 1 unit
    
    theta = -np.log(beta) / dt
    mu = alpha / (1 - beta)
    sigma = resid_std * np.sqrt(-2 * np.log(beta) / (dt * (1 - beta**2)))
    
    half_life = np.log(2) / theta
    
    return theta, mu, sigma, half_life
```

## 6.2. Rust (Streaming Half-Life)

For HFT, we need to update the Half-Life on every tick to adjust our holding period.

```rust
pub struct OUEstimator {
    sum_x: f64,
    sum_y: f64,
    sum_xy: f64,
    sum_xx: f64,
    n: f64,
}

impl OUEstimator {
    pub fn update(&mut self, price_t: f64, price_t_minus_1: f64) -> f64 {
        // Linear Regression Update: x_t = alpha + beta * x_{t-1}
        // Y = x_t, X = x_{t-1}
        
        self.sum_x += price_t_minus_1;
        self.sum_y += price_t;
        self.sum_xy += price_t * price_t_minus_1;
        self.sum_xx += price_t_minus_1 * price_t_minus_1;
        self.n += 1.0;
        
        // Calculate Beta
        let numerator = self.n * self.sum_xy - self.sum_x * self.sum_y;
        let denominator = self.n * self.sum_xx - self.sum_x.powi(2);
        
        if denominator == 0.0 { return 0.0; }
        
        let beta = numerator / denominator;
        
        // Theta = -ln(beta)
        if beta <= 0.0 || beta >= 1.0 { return 9999.0; } // Non-stationary
        
        let theta = -beta.ln();
        let half_life = 0.6931 / theta;
        
        half_life
    }
}
```

---

# 7. Risk Management

**The Widowmaker Trade:**
When a mean reverting asset breaks its stationarity conditions, it becomes a distinct trend.
If you keep adding to a losing mean reversion trade, you will go bankrupt.
**Golden Rule:**

* Stop Loss MUST be based on **Volatility** (e.g., 3 Sigma).
* Time Stop MUST be based on **Half-Life** (e.g., Exit if $t > 2 \times \tau$).

---

# 8. Conclusion

Strategy 02 is not about lines on a chart. It is about the **Physics of Price**.
By quantifying the **Speed of Reversion ($\theta$)** and the **Distance to Equilibrium (Z-Score)**, we convert Mean Reversion from an art into a science.
The OU Process is the heartbeat of this system.
