# 117 - Chaikin Money Flow Oscillator (CMF)

**Volume:** 117 of 100
**Strategy Type:** Volume Oscillator / Breakout Validaton
**Risk Profile:** Low (Filter)
**Mathematical Basis:** Sum(MFV) / Sum(Vol) over N periods

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Normalized Flow](#2-the-theory-normalized-flow)
    * 2.1. Marc Chaikin's improvement on ADL.
    * 2.2. From Cumulative to Oscillating.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Breakout Validation (> 0.1).
    * 3.2. The Zero Line Cross.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Rolling Sum Ratio.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Rolling Windows.
    * 5.2. Rust: Optimization.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 117** employs the **Chaikin Money Flow (CMF)**.
While ADL (Strategy 116) is cumulative and has "infinite memory", CMF focuses only on the last N periods (typically 20 or 21).
It asks: "Over the last month, is money flowing IN or OUT?"
It outputs a value between -1 and +1.
It is the standard tool for **validating breakouts**.

---

# 2. The Theory: Normalized Flow

### 2.1. The Memory Problem

ADL's value depends on where it started 10 years ago.
CMF standardizes this by dividing the Sum of Money Flow Volume by the Total Volume.
Result: A percentage-like oscillator.
$CMF = 0.25$ means 25% of the total volume traded in the last 20 days was "Buying Pressure".

---

# 3. The Strategy Rules

### 3.1. The Breakout Test

* **Scenario:** Price breaks Resistance.
* **Check:** Is CMF > 0.05?
  * **Yes:** Valid Breakout (Supported by Flow). **BUY**.
  * **No (CMF < 0):** Fakeout (Price moved up, but Volume was selling/diverging). **FADE**.

### 3.2. CMF Trend

* **Bullish Regime:** CMF consistently > 0.
* **Bearish Regime:** CMF consistently < 0.
* **Signal:** CMF crosses Zero Line. (Note: Often lags Price, best used as confirmation).

---

# 4. Mathematical Derivation

$$ CMF(N) = \frac{\sum_{i=1}^{N} (CLV_i \times Volume_i)}{\sum_{i=1}^{N} Volume_i} $$

Where $CLV$ is the Close Location Value from Strategy 116.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 117 Source)*

```python
def cmf(high, low, close, volume, period=20):
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)
    mfv = clv * volume
    # Sum of MFV / Sum of Volume
    cmf = mfv.rolling(period).sum() / volume.rolling(period).sum()
    return cmf
```

---

# 7. Conclusion

Strategy 117 is the **Gatekeeper**.
It prevents GOLIATH from chasing "empty" moves.
A price move on low volume (or worse, negative money flow) is a trap.
CMF ensures that we only deploy capital when the "Hydraulics" (Volume) are strong enough to lift the price derived from the "Physics" (Market Mechanics).
