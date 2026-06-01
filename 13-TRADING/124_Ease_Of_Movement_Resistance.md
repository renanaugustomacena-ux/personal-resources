# 124 - Ease Of Movement Resistance (EMV)

**Volume:** 124 of 100
**Strategy Type:** Volume-Price Resistance
**Risk Profile:** Medium
**Mathematical Basis:** Distance Moved / (Volume / Range)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Path of Least Resistance](#2-the-theory-path-of-least-resistance)
    * 2.1. Richard Arms' Box Ratio.
    * 2.2. Volume efficiency.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Zero Crossing (The Breakout).
    * 3.2. Divergence (The Struggle).
4. [Mathematical Derivation](#4-mathematical-derivation)
5. [Implementation: Production Grade](#5-implementation-production-grade)
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 124** utilizes **Ease of Movement (EMV)**.
Most volume indicators act like fuel gauges.
EMV acts like a **Efficiency Gauge**.
It measures how much Volume it takes to move Price.
Low Volume + Big Price Move = **Easy Movement** (Low Resistance).
High Volume + Small Price Move = **Hard Movement** (High Resistance / Churn).
Strategy 124 isolates times when price is moving "Easily" and rides the path of least resistance.

---

# 2. The Theory: Path of Least Resistance

### 2.1. The Efficient Market Logic

If there are no sellers, it takes very little buying volume to push price up.
This "Low Volume Rally" is often dismissed by amateurs, but Richard Arms realized it meant the Sellers had vacated the field.
Conversely, if there is massive volume but price isn't moving (Box Ratio is high), it means a war is being fought. Avoid the war. Wait for the winner.

---

# 3. The Strategy Rules

### 3.1. The Zero Break (Ease Detection)

* **Trigger:** EMV Smoothed (14) crosses Zero.
* **Bullish:** EMV crosses Up. (Price is moving Up more easily than Down).
* **Bearish:** EMV crosses Down.

### 3.2. The "Struggle" Divergence

* **Setup:** Price makes New High.
* **Signal:** EMV fails to make New High (or drops).
* **Interpretation:** The price is going up, but it is taking *more effort* (Volume/Range) to do so. The resistance is increasing.
* **Action:** Tighten stops. Reversal probable.

---

# 4. Mathematical Derivation

$$ MidpointMove = \frac{High+Low}{2} - \frac{High_{prev}+Low_{prev}}{2} $$
$$ BoxRatio = \frac{Volume / Scale}{High - Low} $$
$$ EMV = \frac{MidpointMove}{BoxRatio} $$

Note: If Range is Small and Volume is High, BoxRatio is Huge. EMV becomes Small. (Hard Movement).
If Range is Large and Volume is Low, BoxRatio is Small. EMV becomes Large. (Easy Movement).

---

# 5. Implementation

### 5.1. Python

*(From Indicator 124 Source)*

```python
def emv(high, low, volume, scale=10000):
    dm = ((high + low) / 2) - ((high.shift(1) + low.shift(1)) / 2)
    br = (volume / scale) / (high - low)
    return dm / br
```

---

# 7. Conclusion

Strategy 124 is the **Flow Meter**.
It detects "Slippery" markets.
GOLIATH wants to be in a trade where the market *wants* to go.
If GOLIATH sees EMV Turn Positive, it knows that the sellers have stepped aside, and the path is clear for a rally.
It is an essential check against "Grinding" markets where high volume yields no progress.
