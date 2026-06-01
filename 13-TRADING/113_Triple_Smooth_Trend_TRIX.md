# 113 - Triple Smooth Trend (TRIX)

**Volume:** 113 of 100
**Strategy Type:** Strategic Trend / Momentum
**Risk Profile:** Low (Very smooth, low signal frequency)
**Mathematical Basis:** Rate of Change of Triple EMA

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Signal Processing](#2-the-theory-signal-processing)
    * 2.1. The Butterworth Filter analogy.
    * 2.2. Filtering out the HFT noise.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Zero-Line Crossover (The Mega-Trend).
    * 3.2. Divergence Trading.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. EMA -> EMA -> EMA -> ROC.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Cascaded Calculations.
    * 5.2. Rust: Struct-based state.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 113** uses **TRIX (Triple Exponential Average)**.
It is the "Strategic Commander" of the GOLIATH system.
While other indicators twitch at every price tick, TRIX ignores everything but the most significant moves.
It smoothes the price three times. Then it takes the Rate of Change (Velocity).
The result is an ultra-smooth oscillator that filters out 99% of market noise. When TRIX turns, the Market turns.

---

# 2. The Theory: Signal Processing

### 2.1. The Triple Filter

One EMA removes high-frequency noise.
Two EMAs remove medium-frequency chop.
Three EMAs leave only the **Secular Trend**.
By taking the ROG (Rate of Change) of this Triple EMA, we get a leading indicator of the trend's acceleration.

---

# 3. The Strategy Rules

### 3.1. The Strategic Pivot

* **Indicator:** TRIX(15).
* **Signal:** Cross of the Zero Line.
* **Action:**
  * **Cross Above 0:** Structural Bull Market. GOLIATH switches to "Long Only" mode.
  * **Cross Below 0:** Structural Bear Market. GOLIATH switches to "Short Only" mode.
* **Note:** This is rarely used for direct entry. It is used to set the **Rules of Engagement** for faster strategies.

### 3.2. TRIX Divergence

* **Setup:** Price makes Lower Low, TRIX makes Higher Low.
* **Meaning:** The underlying momentum of the Secular Trend has shifted, even if price hasn't realized it yet.
* **Action:** Aggressive Counter-Trend Entry.

---

# 4. Mathematical Derivation

$$ EMA1 = EMA(Price) $$
$$ EMA2 = EMA(EMA1) $$
$$ EMA3 = EMA(EMA2) $$
$$ TRIX = \frac{EMA3_t - EMA3_{t-1}}{EMA3_{t-1}} \times 100 $$

---

# 5. Implementation

### 5.1. Python

*(From Indicator 113 Source)*

```python
def trix(close, period=15):
    ema1 = close.ewm(span=period).mean()
    ema2 = ema1.ewm(span=period).mean()
    ema3 = ema2.ewm(span=period).mean()
    return ema3.pct_change() * 100
```

---

# 7. Conclusion

Strategy 113 is **Gravity**.
It represents the massive, slow-moving forces of the market.
You cannot fight TRIX. If TRIX is pointing down, buying the dip is like trying to catch a falling piano.
GOLIATH uses Strategy 113 to ensure it is never on the wrong side of history.
