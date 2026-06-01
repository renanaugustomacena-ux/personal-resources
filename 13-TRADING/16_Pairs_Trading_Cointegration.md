# 16 - Pairs Trading & Statistical Arbitrage: The Neutral Game

**Volume:** 16 of 50
**Strategy Type:** Market Neutral / Statistical Arbitrage (StatArb)
**Risk Profile:** Low Beta / High Leverage / Execution Risk
**Mathematical Basis:** Cointegration (Engle-Granger), Stationarity (ADF), Hurst Exponent, & Kalman Filtering

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Correlation vs Cointegration](#2-the-theory-correlation-vs-cointegration)
    * 2.1. The Drunk and the Dog (Stationarity)
    * 2.2. Spurious Correlation Warning
    * 2.3. The Fractal Dimension (Hurst Exponent)
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Selection: Finding the Pair
    * 3.2. Construction: The Spread ($Y - \beta X$)
    * 3.3. The Trigger: Z-Score (The Great Equalizer)
    * 3.4. Regime Detection: Stationarity & Hurst Filter
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Augmented Dickey-Fuller (ADF) Test
    * 4.2. Ordinary Least Squares (OLS) for Hedge Ratio
    * 4.3. Ornstein-Uhlenbeck (OU) Process
    * 4.4. Rescaled Range (R/S) Analysis
5. [Historical Case Studies](#5-historical-case-studies)
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Analysis: ADF & CADF)
    * 6.2. Rust (Streaming Z-Score, Rolling Beta, Hurst, Kalman)
7. [Optimization: The Kalman Filter](#7-optimization-the-kalman-filter)
    * 7.1. The Problem with Static Beta
    * 7.2. Dynamic State Estimation
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Pairs Trading** (Statistical Arbitrage) is the grandfather of quantitative trading.
It is based on **Market Neutrality**. We do not care if the market crashes or rallies; we only care about the **Relative Value** between two assets.
If stocks A and B are cointegrated (tied together by economics), deviations in their spread are statistically likely to revert to the mean.

---

# 2. Theory: Cointegration

## 2.1. The Drunk and the Dog

* **Correlation:** Two drunks walking randomly. They might move in the same direction for a while, but nothing binds them.
* **Cointegration:** A drunk walking a dog. The drunk is random. The dog is random. But the **Leash** (the spread) keeps them within a bounded distance.
* **Stationarity:** The distance (Spread) has a constant Mean and Variance over time. This is the "Leash" we trade.

## 2.2. Spurious Correlation

Use the **Augmented Dickey-Fuller (ADF)** test. Never trade based on correlation alone. Correlation breaks; Cointegration endures.

## 2.3. The Fractal Dimension (Hurst Exponent)

Most models assume markets are Random Walks (Brownian Motion, $H=0.5$).
The **Hurst Exponent (H)** measures the "Memory" of the series.

* **$0 < H < 0.5$:** Mean Reverting (Anti-Persistent). The series strictly reverts to the mean.
* **$H = 0.5$:** Random Walk.
* **$0.5 < H < 1.0$:** Trending (Persistent).
**Key Insight:** For Pairs Trading, we *require* $H < 0.5$ for the Spread. If $H > 0.5$, the spread is trending apart (Divergence), and mean reversion strategies will fail.

---

# 3. Strategy Rules

## 3.1. The Hedge Ratio ($\beta$)

We calculate $\beta$ such that the Spread is stationary.
$$ Spread_t = PriceA_t - (\beta \times PriceB_t) $$

## 3.2. The Trigger: Z-Score

The Z-Score results in **Scale Invariance**.
It answers: "Is this deviation significant?"

* **Z > +2.0:** Spread is statistically expensive. Short Spread (Short A, Long B).
* **Z < -2.0:** Spread is statistically cheap. Long Spread (Long A, Short B).
* **Target:** Z = 0 (Mean Reversion).

## 3.3. Regime Detection

**Rule:** Only trade Z-Score signals if:

1. **Stationary:** ADF P-value < 0.05.
2. **Mean Reverting:** Hurst Exponent ($H$) < 0.4.
If $H$ jumps above 0.5, the "Leash" has broken. Stop trading.

---

# 4. Mathematical Derivation

## 4.1. The Z-Score Formula

$$ Z = \frac{X - \mu}{\sigma} $$
Where $\mu$ is the Rolling Mean and $\sigma$ is the Rolling Standard Deviation.

## 4.2. Mean Reversion Speed (Ornstein-Uhlenbeck)

$$ dX_t = \theta (\mu - X_t)dt + \sigma dW_t $$
We estimate $\theta$ (Theta).
$$ \text{Half-Life} = \frac{\ln(2)}{\theta} $$
Trade pairs with low Half-Life (< 10 days) for faster capital turnover.

## 4.3. Rescaled Range (R/S) Analysis

Used to calculate Hurst Exponent.
$$ R/S \propto n^H $$
If the Range of the spread ($R$) expands slower than the square root of time ($\sqrt{n}$), then $H < 0.5$ (Mean Reversion).

---

# 5. Historical Case Studies

## 5.1. Royal Dutch Shell (RDS.A / RDS.B)

The classic arbitrarge between two shares of the same company.

## 5.2. Coke vs Pepsi

Sector coherence.

## 5.3. Quant Quake (2007)

When "Distance Method" pairs strategies failed because spreads widened to 4-sigma and never reverted (Liquidation Cascade). Lesson: Use Stop Losses.

---

# 6. Implementation: Production Grade

## 6.1. Python (Analysis)

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

def check_cointegration(y, x):
    # Engle-Granger 2-step
    # 1. Regress Y on X
    x = sm.add_constant(x)
    model = sm.OLS(y, x).fit()
    beta = model.params[1]
    spread = y - (beta * x[model.params.index[1]]) # Careful with indexing
    
    # 2. Test Residuals (Spread) for Stationarity
    adf_result = adfuller(spread)
    p_value = adf_result[1]
    
    return p_value, beta

def calculate_half_life(spread):
    spread_lag = spread.shift(1)
    spread_ret = spread - spread_lag
    spread_ret = spread_ret.dropna()
    spread_lag = spread_lag.dropna()
    X = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, X).fit()
    theta = -model.params[1]
    return np.log(2) / theta
```

## 6.2. Rust (Streaming Components)

### 6.2.1. Streaming Z-Score

```rust
use std::collections::VecDeque;

pub struct StreamingZScore {
    period: usize,
    buffer: VecDeque<f64>,
    sum: f64,
    sum_sq: f64,
}

impl StreamingZScore {
    pub fn new(period: usize) -> Self {
        Self {
            period,
            buffer: VecDeque::with_capacity(period),
            sum: 0.0,
            sum_sq: 0.0,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        self.buffer.push_back(value);
        self.sum += value;
        self.sum_sq += value * value;

        if self.buffer.len() > self.period {
            let old = self.buffer.pop_front().unwrap();
            self.sum -= old;
            self.sum_sq -= old * old;
        }

        if self.buffer.len() < self.period { return None; }

        let n = self.period as f64;
        let mean = self.sum / n;
        let variance = (self.sum_sq / n) - (mean * mean);
        
        if variance <= 1e-9 { return Some(0.0); }
        
        let std_dev = variance.sqrt();
        Some((value - mean) / std_dev)
    }
}
```

### 6.2.2. Rolling Beta (Recursive OLS)

```rust
pub struct RollingBeta {
    period: usize,
    x_buffer: VecDeque<f64>,
    y_buffer: VecDeque<f64>,
    sum_x: f64, sum_y: f64, sum_xx: f64, sum_xy: f64,
}

impl RollingBeta {
    pub fn new(period: usize) -> Self {
        Self {
            period,
            x_buffer: VecDeque::new(), y_buffer: VecDeque::new(),
            sum_x: 0.0, sum_y: 0.0, sum_xx: 0.0, sum_xy: 0.0,
        }
    }
    
    pub fn update(&mut self, y: f64, x: f64) -> Option<(f64, f64)> {
        self.x_buffer.push_back(x);
        self.y_buffer.push_back(y);
        self.sum_x += x; self.sum_y += y;
        self.sum_xx += x*x; self.sum_xy += x*y;
        
        if self.x_buffer.len() > self.period {
            let old_x = self.x_buffer.pop_front().unwrap();
            let old_y = self.y_buffer.pop_front().unwrap();
            self.sum_x -= old_x; self.sum_y -= old_y;
            self.sum_xx -= old_x*old_x; self.sum_xy -= old_x*old_y;
        }
        
        if self.x_buffer.len() < self.period { return None; }
        
        let n = self.period as f64;
        let num = (n * self.sum_xy) - (self.sum_x * self.sum_y);
        let den = (n * self.sum_xx) - (self.sum_x * self.sum_x);
        
        if den.abs() < 1e-9 { return None; }
        
        let beta = num / den;
        let alpha = (self.sum_y / n) - (beta * (self.sum_x / n));
        Some((beta, alpha))
    }
}
```

### 6.2.3. Kalman Filter (Scalar)

A recursive filter to estimate the "True State" from noisy measurements. Used for dynamic $\beta$.

```rust
pub struct KalmanFilter {
    x: f64, // State Estimate
    p: f64, // Error Covariance
    q: f64, // Process Noise Variance
    r: f64, // Measurement Noise Variance
    k: f64, // Kalman Gain
}

impl KalmanFilter {
    pub fn new(process_noise: f64, measurement_noise: f64) -> Self {
        Self {
            x: 0.0, p: 1.0, 
            q: process_noise, r: measurement_noise, 
            k: 0.0,
        }
    }

    pub fn update(&mut self, measurement: f64) -> f64 {
        if self.p == 1.0 && self.x == 0.0 { self.x = measurement; }
    
        // 1. Prediction
        let p_pred = self.p + self.q;
        
        // 2. Correction
        self.k = p_pred / (p_pred + self.r);
        self.x = self.x + self.k * (measurement - self.x);
        self.p = (1.0 - self.k) * p_pred;
        
        self.x
    }
}
```

---

# 7. Optimization: The Kalman Filter

## 7.1. The Problem with Static Beta

Using a rolling window OLS (e.g., 60 days) assumes $\beta$ is constant for that window. But if a company announces a merger or a fundamental shift *today*, the OLS beta lags for 60 days.

## 7.2. Dynamic State Estimation

The **Kalman Filter** treats $\beta$ as a "Hidden State" that evolves over time with some process noise ($Q$).
$$ \beta_t = \beta_{t-1} + \eta_t $$
It updates $\beta_t$ at every tick based on the prediction error.

* **High Volatility:** The filter "opens up" (Trusts the measurement more).
* **Low Volatility:** The filter "smooths out" (Trusts the model more).
This provides a **Lag-Free Hedge Ratio** that is critical for surviving regime shifts.

---

# 8. Risk Management

## 8.1. Stop Loss: The "Blowout"

If Z-Score > 4.0, the relationship might be broken (Fundamental Shift, M&A, Bankruptcy). Close the trade. Do not "Average Down" into a black hole.

## 8.2. Leg Risk

Use `Fill-or-Kill` or algorithmic execution to transact both legs simultaneously.

---

# 9. Conclusion

Pairs Trading transforms directional gambling into a statistical science. By ensuring **Cointegration**, filtering for low **Hurst Exponent** (Mean Reversion), and using **Kalman Filters** for dynamic hedging, we isolate pure alpha.
However, always remember: "Markets can remain irrational longer than you can remain solvent."
