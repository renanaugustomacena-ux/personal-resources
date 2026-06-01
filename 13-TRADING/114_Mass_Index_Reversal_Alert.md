# 114 - Mass Index Reversal Alert

**Volume:** 114 of 100
**Strategy Type:** Volatility Reversal / Warning System
**Risk Profile:** Low (Alert only)
**Mathematical Basis:** Range Expansion/Contraction (EMA Ratio)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Reversal Bulge](#2-the-theory-the-reversal-bulge)
    * 2.1. Elasticity of Volatility.
    * 2.2. The Donald Dorsey threshold (27.0).
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Bulge Setup ($> 27$).
    * 3.2. The Reversal Trigger ($< 26.5$).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. EMA Ratio Summation.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Accurate Summation.
    * 5.2. Rust: State tracking.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 114** uses the **Mass Index**, developed by Donald Dorsey.
It does not predict direction. It predicts **Time of Reversal**.
It relies on the phenomenon that Trend Reversals are preceded by a specific volatility signature: A widening of the High-Low range (Expansion), followed immediately by a contraction.
This pattern creates a "Bulge" in the Mass Index summation.

---

# 2. The Theory: The Reversal Bulge

### 2.1. Rubber Band Physics

Think of the market as a rubber band.
As a trend accelerates, the Daily Range ($High - Low$) increases. The rubber band stretches.
Eventually, it stretches too far. The Mass Index (Sum of Range EMAs) hits 27.
Then, the energy snaps back. The range contracts. Mass Index drops.
This snap is the Reversal.

---

# 3. The Strategy Rules

### 3.1. The Reversal Setups

* **Setup:** Mass Index > 27.0. (The Bulge).
* **Trigger:** Mass Index falls below 26.5.
* **Action:** Look for Reversal.
  * **If Trend was UP:** Sell.
  * **If Trend was DOWN:** Buy.
* **Note:** Strategy 114 must be paired with specific directional indicators (like EMA Cross or TRIX) to know *which way* to trade. It provides the "WHEN", not the "WHAT".

---

# 4. Mathematical Derivation

$$ Width = High - Low $$
$$ EMA1 = EMA(Width, 9) $$
$$ EMA2 = EMA(EMA1, 9) $$
$$ Ratio = EMA1 / EMA2 $$
$$ MassIndex = \sum_{i=1}^{25} Ratio_i $$

The double smoothing ensures we are looking at the *trend* of volatility, not just noise.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 114 Source)*

```python
def mass_index(high, low, period=25):
    r = high - low
    ema1 = r.ewm(span=9).mean()
    ema2 = ema1.ewm(span=9).mean()
    ratio = ema1 / ema2
    return ratio.rolling(period).sum()
```

---

# 7. Conclusion

Strategy 114 is the **Early Warning System**.
Common indicators (MACD) are lagging. They tell you a reversal happened *after* price moved.
Mass Index warns you *before* price turns, because Volatility (Range) turns before Price does.
GOLIATH uses Strategy 114 to **tighten stop losses** on existing trend positions when a Bulge is detected.
