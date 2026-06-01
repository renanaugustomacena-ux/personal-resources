# 108 - Vortex Trend Follower

**Volume:** 108 of 100
**Strategy Type:** Directional Oscillator / Flow Analysis
**Risk Profile:** Low (Clear stops)
**Mathematical Basis:** Fluid Dynamics / True Range Summation

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Market Flow](#2-the-theory-market-flow)
    * 2.1. Viktor Schauberger and Water Vortices.
    * 2.2. Polarity: +VI (Upward Flow) vs -VI (Downward Flow).
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Vortex Crossover System.
    * 3.2. The 1.05 Threshold (Filtering Noise).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. True Range (TR).
    * 4.2. Vortex Movement (VM).
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Rolling Sums.
    * 5.2. Rust: State Machine.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 108** uses the **Vortex Indicator (VI)** to identify the start of a new trend.
Inspired by fluid dynamics, it treats the market as a river. A trend is simply a strong current (Vortex) pulling price in one direction.
While ADX measures strength non-directionally, VI splits the energy into Positive ($+VI$) and Negative ($-VI$) components.
The strategy captures the moment the "current" reverses direction.

---

# 2. The Theory: Market Flow

### 2.1. The Interplay

Markets are a battle between Buyers (lifting the offer) and Sellers (hitting the bid).

* $+VI$ measures the cumulative strength of buying waves (Low to High).
* $-VI$ measures the cumulative strength of selling waves (High to Low).
When $+VI$ crosses above $-VI$, the Buying Vortex has overpowered the Selling Vortex.

---

# 3. The Strategy Rules

### 3.1. The Water Wheel Rules

1. **Indicator:** Vortex(14).
2. **Long Setup:** $+VI$ crosses above $-VI$.
3. **Confirmation:** Wait for $+VI > 1.05$ (Ensures the crossover isn't just noise around 1.0).
4. **Short Setup:** $-VI$ crosses above $+VI$.
5. **Confirmation:** Wait for $-VI > 1.05$.
6. **Stop Loss:** High/Low of the crossover candle.

### 3.2. The Squeeze (Bonus)

If BOTH $+VI$ and $-VI$ are < 1.0 (or very close), the market is stagnant (Low Volatility).
Strategy 108 waits. It never trades the "Dead Water".

---

# 4. Mathematical Derivation

$$ +VM = |High_t - Low_{t-1}| $$
$$ -VM = |Low_t - High_{t-1}| $$
$$ TR = \max(H-L, |H-C_{prev}|, |L-C_{prev}|) $$
$$ +VI_{14} = \frac{\sum_{14} +VM}{\sum_{14} TR} $$

The denominator ($\sum TR$) normalizes the movement by the volatility.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 108 Source)*

```python
def vortex(high, low, close, period=14):
    tr = true_range(high, low, close)
    vm_plus = (high - low.shift(1)).abs()
    vm_minus = (low - high.shift(1)).abs()
    
    tr14 = tr.rolling(period).sum()
    vi_plus = vm_plus.rolling(period).sum() / tr14
    vi_minus = vm_minus.rolling(period).sum() / tr14
    
    return vi_plus, vi_minus
```

---

# 7. Conclusion

Strategy 108 is **The Flow Meter**.
It doesn't care about price levels. It cares about Energy Direction.
It is exceptionally good at staying in a trend because even during a pullback, the aggregate $+VI$ usually stays above the $-VI$.
The crossover is the definitive signal of regime change.
