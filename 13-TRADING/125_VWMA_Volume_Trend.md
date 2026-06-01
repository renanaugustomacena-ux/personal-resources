# 125 - VWMA Volume Trend (Volume Weighted MA)

**Volume:** 125 of 100
**Strategy Type:** Volume-Weighted Trend
**Risk Profile:** Low (Lagging w/ Volume confirmation)
**Mathematical Basis:** Sum(P*V) / Sum(V)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Vote by Wealth](#2-the-theory-vote-by-wealth)
    * 2.1. SMA is "One Bar, One Vote".
    * 2.2. VWMA is "One Share, One Vote".
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The SMA/VWMA Crossover.
    * 3.2. Divergence Analysis.
4. [Mathematical Derivation](#4-mathematical-derivation)
5. [Implementation: Production Grade](#5-implementation-production-grade)
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 125** uses the **Volume Weighted Moving Average (VWMA)**.
It asks a fundamental question: "Where is the money?"
A standard SMA treats a $10 move on 1 share volume the same as a $10 move on 1,000,000 shares volume.
VWMA corrects this. It pulls the average towards the price levels with the highest volume.
The relationship between SMA (Price) and VWMA (Money) reveals the intent of the Smart Money.

---

# 2. The Theory: Vote by Wealth

### 2.1. Democracy vs Plutocracy

The market is not a democracy. It is a plutocracy. The person with the most money moves the price.
SMA represents the "Timeline" of price.
VWMA represents the "Cost Basis" of the market participants.
If VWMA > SMA, it means volume was higher when price was higher. The "Average Participant" bought at a higher price than the average time-price. This implies strength (Acceptance of higher prices).

---

# 3. The Strategy Rules

### 3.1. The Confirmation Cross

* **Bullish:** VWMA crosses ABOVE SMA.
  * *Meaning:* Heavy volume is pushing price UP. The "Weight" of the market supports the move.
* **Bearish:** VWMA crosses BELOW SMA.
  * *Meaning:* Heavy volume is pushing price DOWN.

### 3.2. The Exhaustion Divergence

* **Scenario:** Price is rising.
* **Signal:** SMA is rising, but VWMA starts flattening or dropping.
* **Interpretation:** Price is going up, but Volume is drying up (or shifting to lower prices). The "Smart Money" is not participating in the new highs.
* **Action:** Exit.

---

# 4. Mathematical Derivation

$$ VWMA = \frac{\sum (Price_i \times Volume_i)}{\sum Volume_i} $$

It is essentially a Rolling VWAP.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 125 Source)*

```python
def vwma(close, volume, period=20):
    pv = close * volume
    return pv.rolling(period).sum() / volume.rolling(period).sum()
```

---

# 7. Conclusion

Strategy 125 is the **Lie Detector**.
Price can be manipulated on low volume.
VWMA cannot.
If Price shoots up but VWMA stays flat, GOLIATH knows it's a "Hollow Rally".
GOLIATH uses Strategy 125 to validate trends. It will only increase position size if VWMA confirms the direction of the SMA.
It ensures we are trading *with* the whales, not being eaten by them.
