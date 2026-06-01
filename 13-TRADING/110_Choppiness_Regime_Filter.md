# 110 - Choppiness Regime Filter (CHOP)

**Volume:** 110 of 100
**Strategy Type:** Regime Filter / Volatility Breakout
**Risk Profile:** Low (Defensive)
**Mathematical Basis:** Fractal Dimension (Hurst Exponent proxy)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Measuring Chaos](#2-the-theory-measuring-chaos)
    * 2.1. Fractal Dimension and Path Efficiency.
    * 2.2. The Choppiness Index (0-100).
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Regime Filter (Don't Trade Zone).
    * 3.2. The Chaos Breakout Setup.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. $\log_{10}(\text{PathLength} / \text{Displacement})$.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Calculating Fractal Dim.
    * 5.2. Rust: Efficient Logs.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 110** is not a trading strategy in the traditional sense. It is a **Traffic Light**.
It uses the **Choppiness Index (CHOP)** to measure the "Fractal Dimension" of the price curve.

* **Red Light (CHOP > 61.8):** Market is efficient, chaotic, sideways. Do not use Trend Following. Use Mean Reversion or Step Aside.
* **Green Light (CHOP < 38.2):** Market is inefficient, linear, trending. Deploy Trend Following (Strategies 1, 101, 105).
Strategy 110 acts as the "Manager" that tells other strategies when to sit down.

---

# 2. The Theory: Measuring Chaos

### 2.1. Path Efficiency

If price goes from 100 to 110 in a straight line, it is efficient (Order).
If price goes from 100 to 110 but oscillates wildly between 90 and 120 along the way, it is inefficient (Chaos).
CHOP measures the ratio of the "Total Distance Traveled" (Sum of True Ranges) to the "Net Distance Achieved" (High - Low).

---

# 3. The Strategy Rules

### 3.1. The "No-Fly Zone"

* **Condition:** CHOP(14) > 61.8.
* **Action:**
  * Disable Strategy 1 (SMA), Strategy 105 (T3), Strategy 108 (Vortex).
  * Enable Strategy 5 (Bollinger Mean Reversion).

### 3.2. The Chaos Breakout

* **Setup:** CHOP has been > 61.8 for 10+ bars (Coiled Spring).
* **Trigger:** CHOP drops below 61.8.
* **Meaning:** The coil has snapped. Expansion phase begins.
* **Action:** Enter Long/Short based on Price Breakout direction.

---

# 4. Mathematical Derivation

$$ CHOP = 100 \times \frac{\log_{10}\left( \frac{\sum_{1}^N TR}{MaxH_N - MinL_N} \right)}{\log_{10}(N)} $$

Basically: Log(Path Length / Displacement).
Related to Hurst Exponent $H$: $CHOP \approx 100(1-H)$ (roughly).

---

# 5. Implementation

### 5.1. Python

*(From Indicator 110 Source)*

```python
def chop(high, low, close, period=14):
    tr = true_range(high, low, close)
    sum_tr = tr.rolling(period).sum()
    h_n = high.rolling(period).max()
    l_n = low.rolling(period).min()
    
    return 100 * np.log10(sum_tr / (h_n - l_n)) / np.log10(period)
```

---

# 7. Conclusion

Strategy 110 is the **Gatekeeper**.
It saves GOLIATH money not by making profitable trades, but by preventing losing trades in choppy markets.
In the GOLIATH Meta-Model (Strategy 100), CHOP is one of the primary inputs to the Gating Network.
