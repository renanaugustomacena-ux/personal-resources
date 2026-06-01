# 105 - T3 Tillson Relaxed Trend

**Volume:** 105 of 100
**Strategy Type:** Position Trading / Trend Following
**Risk Profile:** Lag (Intentional)
**Mathematical Basis:** Hexa-Smoothed EMA (EMA of EMA of EMA...)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Smoothing Squared](#2-the-theory-smoothing-squared)
    * 2.1. DEMA vs TEMA vs T3.
    * 2.2. The Volume Factor ($v$): Tuning the damping.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The T3 Ribbon Strategy.
    * 3.2. Crossovers with T3.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Generalized DEMA ($GD$).
    * 4.2. T3 Recursion formula.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Recursive EMA calls.
    * 5.2. Rust: Struct-based state tracking.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 105** employs Tim Tillson's **T3 Moving Average**.
If HMA (102) is a Ferrari (Fast, twitchy), T3 is a Rolls Royce (Smooth, heavy, comfortable).
T3 effectively passes the price through **six** layers of Exponential Moving Averages.
The result is a curve that filters out *all* minor market corrections.
It is designed for **Trend Riding**. It is slow to enter, but once in, it keeps you in the trade until the trend is undeniably dead.

---

# 2. The Theory: Smoothing Squared

### 2.1. The Damping Factor ($v$)

T3 introduces a variable $v$ (Volume Factor, usually 0.7).
This controls how much "Over-weighting" happens.
Unlike DEMA (which tries to remove lag completely), T3 accepts some lag in exchange for "Butter Smoothness".

---

# 3. The Strategy Rules

### 3.1. The T3 Ribbon

We deploy 3 T3 lines:

1. **Fast:** T3(5, v=0.7).
2. **Medium:** T3(8, v=0.7).
3. **Slow:** T3(13, v=0.7).

### 3.2. Execution

* **Bull Trend:** Fast > Medium > Slow. (Alignment).
* **Entry:** When the Ribbon aligns and expands.
* **Hold:** Ignore price dipping below Fast or Medium. As long as Slow holds, the trend is intact.
* **Exit:** When Fast crosses below Slow.

This prevents the "Shakeout" where a quick drop triggers stops before the trend resumes. T3 ignores the drop.

---

# 4. Mathematical Derivation

$$ GD(n,v) = EMA(n)(1+v) - EMA(EMA(n))v $$
$$ T3 = GD(GD(GD(n,v), v), v) $$
Expanding this reveals coefficients for $EMA_1$ through $EMA_6$.
It acts as a **Low Pass Filter** with a very steep cutoff frequency.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 105 Source)*

```python
def t3(prices, period=10, v=0.7):
    e1 = ema(prices, period)
    e2 = ema(e1, period)
    e3 = ema(e2, period)
    e4 = ema(e3, period)
    e5 = ema(e4, period)
    e6 = ema(e5, period)
    
    c1 = -v**3
    c2 = 3*v**2 + 3*v**3
    c3 = -6*v**2 - 3*v - 3*v**3
    c4 = 1 + 3*v + v**3 + 3*v**2
    
    return c1*e6 + c2*e5 + c3*e4 + c4*e3
```

---

# 7. Conclusion

Strategy 105 is **The Anchor**.
In a portfolio of jittery, high-frequency scalpers (like 102), you need a Strategy 105 to hold the core position.
It creates the "Bass Line" of the trading symphony.
It ensures GOLIATH captures the Macro Trend even while scalping the Micro Noise.
