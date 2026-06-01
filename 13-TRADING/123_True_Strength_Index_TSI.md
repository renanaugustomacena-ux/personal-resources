# 123 - True Strength Index (TSI)

**Volume:** 123 of 100
**Strategy Type:** Double Smoothed Momentum
**Risk Profile:** Low (Low Lag, Low Noise)
**Mathematical Basis:** EMA(EMA(Momentum)) / EMA(EMA(|Momentum|))

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Determining Truth](#2-the-theory-determining-truth)
    * 2.1. Double Smoothing without the Lag of TRIX.
    * 2.2. Numerator vs Denominator.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Signal Cross.
    * 3.2. The Zero Line Bounce.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Double Smoothed Momentum (DSM).
    * 4.2. Double Smoothed Absolute Momentum (DSAM).
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: EMA stacking.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 123** uses the **True Strength Index (TSI)** by William Blau.
It solves the Noise vs Lag dilemma.
Standard smoothing (EMA) adds lag.
TSI applies smoothing *twice*, but to the **Momentum**, not the Price.
The result is an indicator that is exceptionally smooth (low noise) but reacts very quickly to significant price turns (low lag).
It is one of the most mechanically robust oscillators in existence.

---

# 2. The Theory: Determining Truth

### 2.1. Why Double Smooth?

A single EMA of momentum is jagged.
A double EMA of momentum creates a beautiful, sinusoidal wave.
Unlike TRIX (Strategy 113) which triple-smooths *Price* (creating huge lag), TSI double-smooths *Momentum*.
Because Momentum is a derivative of price, smoothing it doesn't cause as much disconnect from the current price action.

---

# 3. The Strategy Rules

### 3.1. The Signal Cross

* **Indicator:** TSI (25, 13). Signal (7).
* **Trigger:** TSI Crosses Signal Line.
* **Filter:** Trade in direction of Zero Line.
  * If TSI > 0: Take only Bullish Crosses.
  * If TSI < 0: Take only Bearish Crosses.

### 3.2. The Zero Line Bounce (Re-Entry)

* **Scenario:** Strong Uptrend (TSI > 25).
* **Pullback:** TSI drops towards Zero.
* **Trigger:** TSI touches Zero (or near it) and turns back up.
* **Action:** Aggressive Buy. This is often the midpoint of the trend.

---

# 4. Mathematical Derivation

$$ M = Close_t - Close_{t-1} $$
$$ DSM = EMA(EMA(M, 25), 13) $$
$$ DSAM = EMA(EMA(|M|, 25), 13) $$
$$ TSI = 100 \times \frac{DSM}{DSAM} $$

By dividing the Smoothed Momentum by the Smoothed *Absolute* Momentum, TSI creates a normalized index (-100 to +100).

---

# 5. Implementation

### 5.1. Python

*(From Indicator 123 Source)*

```python
def tsi(close, r=25, s=13):
    m = close.diff()
    # Double Smooth M
    m_s = m.ewm(span=r).mean().ewm(span=s).mean()
    # Double Smooth Abs(M)
    abs_m_s = m.abs().ewm(span=r).mean().ewm(span=s).mean()
    return 100 * (m_s / abs_m_s)
```

---

# 7. Conclusion

Strategy 123 is the **Signal Cleaner**.
It strips away the high-frequency tick noise and reveals the "True Strength" of the move.
GOLIATH uses TSI as a primary filter for trend following.
If TSI is rising, the trend is robust. If TSI goes flat or crosses its signal line, the trend strength is dissipating, even if price is still drifting effectively.
It is an excellent "Early Warning" system for trend exhaustion.
