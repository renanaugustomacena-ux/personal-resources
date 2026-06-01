# 111 - Chande Momentum Regime (CMO)

**Volume:** 111 of 100
**Strategy Type:** Regime Classification / Momentum Oscillator
**Risk Profile:** High (Raw Momentum)
**Mathematical Basis:** Pure Momentum Ratio ($ (SumUp - SumDn) / (SumUp + SumDn) $)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Pure Momentum](#2-the-theory-pure-momentum)
    * 2.1. The problem with Smoothing (RSI/MACD).
    * 2.2. Tushar Chande's Absolutism.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Four Regimes.
    * 3.2. The Momentum Snap.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Relationship to RSI ($CMO = 2*RSI - 100$).
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Vectorized Calculation.
    * 5.2. Rust: High Performance.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 111** utilizes the **Chande Momentum Oscillator (CMO)**.
Unlike RSI (which smooths gains and losses) or MACD (which smooths price), CMO calculates **Raw Momentum**.
It asks a simple question: "Of all the movement in the last N bars, how much was Up vs Down?"
If price moves Up 100 points and Down 0 points, CMO is +100.
It is the purest metric for determining the **Market Regime**.

---

# 2. The Theory: Pure Momentum

### 2.1. The Smoothing Lie

Most indicators lie. They tell you what happened *on average* over the last N bars.
Smoothing introduces lag. Lag kills HFTs.
CMO enables GOLIATH to see the raw, jagged truth of price action.

### 2.2. The Regime Map

We use CMO not just to trigger trades, but to *categorize* the market state for other strategies.
If CMO > 50, the market is in a **Strong Bull** state. Strategies that fade moves (Mean Reversion) should be disabled. Strategies that buy dips should be aggressive.

---

# 3. The Strategy Rules

### 3.1. The Four Regimes (The Gating Network)

1. **Strong Bull:** CMO > 50. (Only Longs allowed. Aggressive sizing).
2. **Weak Bull:** 0 < CMO < 50. (Longs preferred, but tight stops).
3. **Weak Bear:** -50 < CMO < 0. (Shorts preferred, tightness).
4. **Strong Bear:** CMO < -50. (Only Shorts allowed. Aggressive).

### 3.2. The "Snap" Trade

* **Setup:** CMO hits extreme (> +75 or < -75).
* **Trigger:** CMO snaps back across the +/- 50 line.
* **Action:** Counter-trend trade.
* **Logic:** The "Rubber band" has snapped. The pure momentum was unsustainable.

---

# 4. Mathematical Derivation

$$ S_u = \sum (Close_i - Close_{i-1}) \text{ where } \Delta > 0 $$
$$ S_d = \sum |Close_i - Close_{i-1}| \text{ where } \Delta < 0 $$
$$ CMO = 100 \times \frac{S_u - S_d}{S_u + S_d} $$

It measures **Net Directional Movement** as a percentage of **Total Volatility**.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 111 Source)*

```python
def cmo(close, period=14):
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    sum_up = up.rolling(period).sum()
    sum_down = down.rolling(period).sum()
    return 100 * (sum_up - sum_down) / (sum_up + sum_down)
```

---

# 7. Conclusion

Strategy 111 is the **Compass**.
It points to True North (Buying Power) or True South (Selling Pressure).
In GOLIATH, Strategy 111 is often used as a **filter** for Strategy 105 (T3) or Strategy 113 (TRIX). It ensures that we are aligned with the raw physics of the market flow.
