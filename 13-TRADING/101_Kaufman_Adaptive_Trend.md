# 101 - Kaufman Adaptive Trend (KAMA)

**Volume:** 101 of 100
**Strategy Type:** Adaptive Trend / Filter
**Risk Profile:** Whipsaw in V-Reversals / Lag in sudden shocks
**Mathematical Basis:** Efficiency Ratio ($ER$) & Volatility-Adjusted Smoothing ($SC$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Market Efficiency](#2-the-theory-market-efficiency)
    * 2.1. Signal vs Noise.
    * 2.2. The Efficiency Ratio (ER): Measuring the fractal dimension of price.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Adaptive Filter (KAMA 10).
    * 3.2. The Regime Filter (KAMA 100).
    * 3.3. Entry/Exit Logic (Crossover + ER Confirmation).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Assessing Directional Movement vs Volatility.
    * 4.2. The Smoothing Constant (SC) formula.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Vectorized Calculation.
    * 5.2. Rust: Iterative Efficiency.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 101** utilizes **Perry Kaufman's Adaptive Moving Average (KAMA)** to solve the fundamental problem of trend following: **Chop**.
Standard Moving Averages (SMA/EMA) are dumb. They apply the same lag regardless of market conditions.
KAMA is smart. It calculates an **Efficiency Ratio (ER)**.

* If the market is moving efficiently (Trend), KAMA speeds up (Fast EMA).
* If the market is noisy (Chop), KAMA slows down and flattens out (Slow EMA).
This allows Strategy 101 to capture trends early while remaining flat (out of the market) during sideways consolidation.

---

# 2. The Theory: Market Efficiency

### 2.1. Signal vs Noise (Indicator 101)

Kaufman argued that "Time" is the wrong denominator for averaging. "Volatility" is the correct one.
A 10-day period of flat trading contains high noise and zero signal.
A 10-day period of a 20% rally contains high signal and low noise.
KAMA weights the high-signal period more heavily.

### 2.2. Efficiency Ratio (ER)

$$ ER = \frac{\text{Net Change}}{\text{Sum of Absolute Changes}} $$
It ranges from 0 (Pure Noise) to 1 (Pure Trend).

---

# 3. The Strategy Rules

### 3.1. The Indicators

* **Fast KAMA:** Period=10, Fast=2, Slow=30.
* **Slow KAMA:** Period=100. (Regime Filter).

### 3.2. Setup

1. **Regime:** Price > Slow KAMA (Bullish Bias).
2. **Efficiency:** $ER(10) > 0.3$ (Market is trending, not chopping).

### 3.3. Execution

* **Long Entry:** Price Crosses *Above* Fast KAMA.
* **Long Exit:** Price Crosses *Below* Fast KAMA **OR** $ER < 0.2$ (Trend is dissolving into noise).

---

# 4. Mathematical Derivation

### 4.1. Calculations

1. **Change:** $|P_t - P_{t-n}|$
2. **Volatility:** $\sum |P_i - P_{i-1}|$
3. **ER:** Change / Volatility
4. **SC:** $(\text{ER} \times (\text{FastSC} - \text{SlowSC}) + \text{SlowSC})^2$
5. **KAMA:** $KAMA_{prev} + SC \times (Price - KAMA_{prev})$

The squaring of the SC is crucial. It suppresses the SC when ER is low, making the line nearly horizontal in chop.

---

# 5. Implementation: Production Grade

### 5.1. Python (Pandas)

*(From Indicator 101 Source)*

```python
import pandas as pd
import numpy as np

def calculate_kama(prices, period=10, fast_end=2, slow_end=30):
    prices = pd.Series(prices)
    price_diff = prices.diff().abs()
    current_trend = prices.diff(period).abs()
    volatility = price_diff.rolling(window=period).sum()
    
    er = current_trend / volatility
    er = er.fillna(0)
    
    fast_sc = 2 / (fast_end + 1)
    slow_sc = 2 / (slow_end + 1)
    
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    
    kama = [prices.iloc[0]]
    for i in range(1, len(prices)):
        kama.append(kama[-1] + sc.iloc[i] * (prices.iloc[i] - kama[-1]))
        
    return pd.Series(kama, index=prices.index)
```

### 5.2. Rust (Optimization)

KAMA is recursive, so it must be calculated iteratively.
In Rust, we optimize this by maintaining the `volatility` sum in a sliding window to avoid re-summing `period` elements every tick ($O(1)$ vs $O(N)$).

---

# 6. Risk Management

### 6.1. The V-Turn Weakness

KAMA assumes inertia. If the market crashes 10% in one bar (high volatility, high change), KAMA is fast.
But if the market slowly grinds down, KAMA might remain flat (lagging).
**Mitigation:** Hard Stop Loss at 2 * ATR.

---

# 7. Conclusion

Strategy 101 is the **"Silent Hunter"**.
It does not speak (generate signals) when the market is confusing.
It waits for clarity (High Efficiency).
It is the cornerstone of any Trend Following system that wishes to survive sideways markets.
