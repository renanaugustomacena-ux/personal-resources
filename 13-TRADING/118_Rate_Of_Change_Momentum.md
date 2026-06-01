# 118 - Rate Of Change Momentum (ROC)

**Volume:** 118 of 100
**Strategy Type:** Pure Momentum / Velocity
**Risk Profile:** High (Raw speed)
**Mathematical Basis:** Percentage Change ($ (P_t - P_{t-n}) / P_{t-n} $)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Newton's First Law](#2-the-theory-newtons-first-law)
    * 2.1. Velocity vs Acceleration.
    * 2.2. The Momentum Anomaly (Jegadeesh & Titman).
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Cross-Asset Sorting (Dual Momentum).
    * 3.2. Velocity Extremes.
4. [Mathematical Derivation](#4-mathematical-derivation)
5. [Implementation: Production Grade](#5-implementation-production-grade)
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 118** relies on **Rate of Change (ROC)**.
It is the simplest, most fundamental momentum indicator.
It measures the **Speed** of the price.
It is the basis for the "Momentum Factor" used by practically every Quant Hedge Fund (AQR, etc.).
Assets that have performed best over the last N months tend to continue outperforming.

---

# 2. The Theory: Newton's First Law

### 2.1. Inertia

"An object in motion tends to stay in motion."
If Gold is up 20% in the last month (High ROC), it has inertia. It is statistically likely to go higher.
If Gold is down 20%, catching the "falling knife" is statistically a losing proposition until the velocity (ROC) slows to zero.

### 2.2. Quant Basis

The "Momentum Anomaly" is one of the few market inefficiencies that has persisted for 200 years.
Buying high-ROC assets and selling low-ROC assets generates Alpha.

---

# 3. The Strategy Rules

### 3.1. Relative Momentum (The Sorting Hat)

* **Universe:** Gold, Silver, Oil, S&P500, T-Bonds.
* **Action:** Calculate ROC(20) for all.
* **Trade:** Go Long the Top 1. Short the Bottom 1.
* **Logic:** Be where the action is. Don't trade a flat market.

### 3.2. Absolute Momentum (Trend Filter)

* **Rule:** If ROC(200) < 0, do not go Long. Period.
* **Logic:** If price is lower than it was 200 days ago, you are in a Bear Market. Cash is better than loss.

---

# 4. Mathematical Derivation

$$ ROC = \left( \frac{Close_t}{Close_{t-n}} - 1 \right) \times 100 $$

Or using Log Returns (for additive properties in ML):
$$ ROC_{log} = \ln(Close_t / Close_{t-n}) $$

---

# 5. Implementation

### 5.1. Python

*(From Indicator 118 Source)*

```python
def roc(close, period=14):
    return close.pct_change(period) * 100
```

---

# 7. Conclusion

Strategy 118 is the **Speedometer**.
While complex indicators try to guess the future, ROC tells you the raw truth of the present velocity.
GOLIATH uses Strategy 118 primarily for **Asset Allocation** and **Regime Filtering**.
If XAU/USD ROC is the highest in the macro universe, GOLIATH allocates more risk budget to Gold strategies.
