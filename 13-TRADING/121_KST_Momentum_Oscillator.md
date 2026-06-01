# 121 - KST Momentum Oscillator (Know Sure Thing)

**Volume:** 121 of 100
**Strategy Type:** Multi-Timeframe Momentum
**Risk Profile:** Low (Consensus based)
**Mathematical Basis:** Sum(SMA(ROC(Period_i)) * Weight_i)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Momentum Symphony](#2-the-theory-the-momentum-symphony)
    * 2.1. Nested Cycles.
    * 2.2. Martin Pring's Summation.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The "Four Winds" Signal.
    * 3.2. Zero Line Major Trend.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Short, Medium, Intermediate, Long.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Weighted composite.
    * 5.2. Rust: Struct layout.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 121** exploits the **KST (Know Sure Thing)** oscillator.
Single-period momentum (like ROC-10) is noisy. It wiggles with every short-term correction.
KST combines **Four Rates of Change** (Short, Medium, Intermediate, Long), smoothes each one, and weights them.
It provides a "Consensus Momentum" reading.
If KST says UP, it means the momentum is aligned across multiple time horizons.

---

# 2. The Theory: The Momentum Symphony

### 2.1. Cycles within Cycles

Markets have fractals. A 10-day uptrend can exist inside a 50-day downtrend.
Trading the 10-day trend is dangerous if the 50-day is against you.
KST forces you to look at the whole picture.
By heavily weighting the long-term ROC (Period 30, Weight 4), it ensures that you don't chase short-term ripples that contradict the tidal wave.

---

# 3. The Strategy Rules

### 3.1. The Signal Line Cross

* **Trigger:** KST crosses its 9-period SMA Signal Line.
* **Filter:** Trade ONLY if KST is on the correct side of Zero.
  * **Long:** KST > 0 AND Crosses Above Signal.
  * **Short:** KST < 0 AND Crosses Below Signal.
* **Logic:** We want Momentum Alignment (Zero Line) AND Timing (Signal Cross).

### 3.2. The Zero Line Trend

* **Major Buy:** KST crosses from Negative to Positive. (The long-term tide has turned).
* **Major Sell:** KST crosses from Positive to Negative.

---

# 4. Mathematical Derivation

$$ ROC_1 = SMA(ROC(10), 10) \times 1 $$
$$ ROC_2 = SMA(ROC(15), 10) \times 2 $$
$$ ROC_3 = SMA(ROC(20), 10) \times 3 $$
$$ ROC_4 = SMA(ROC(30), 15) \times 4 $$
$$ KST = ROC_1 + ROC_2 + ROC_3 + ROC_4 $$

Note the progressive weighting (1, 2, 3, 4). The longest timeframe (30) has 4x the influence of the shortest (10).

---

# 5. Implementation

### 5.1. Python

*(From Indicator 121 Source)*

```python
def kst(close, r1=10, r2=15, r3=20, r4=30, s1=10, s2=10, s3=10, s4=15):
    roc1 = close.pct_change(r1).rolling(s1).mean() * 100
    roc2 = close.pct_change(r2).rolling(s2).mean() * 100
    roc3 = close.pct_change(r3).rolling(s3).mean() * 100
    roc4 = close.pct_change(r4).rolling(s4).mean() * 100
    return (roc1 * 1) + (roc2 * 2) + (roc3 * 3) + (roc4 * 4)
```

---

# 7. Conclusion

Strategy 121 is the **Choir Director**.
It asks: "Are the Sopranos (Short-term), Tenors (Medium), and Basses (Long-term) singing in harmony?"
If the Sopranos are singing "Up" but the Basses are singing "Down", KST will likely be flat or noisy.
When everyone sings "Up", KST produces a clean, powerful surge. That is when GOLIATH enters.
