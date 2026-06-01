# 122 - PPO Relative Momentum (Percentage Price Oscillator)

**Volume:** 122 of 100
**Strategy Type:** Relative Strength / Asset Allocation
**Risk Profile:** Low (Normalized)
**Mathematical Basis:** (FastEMA - SlowEMA) / SlowEMA

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Great Equalizer](#2-the-theory-the-great-equalizer)
    * 2.1. The Price Problem in MACD.
    * 2.2. Percentage Normalization.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The "Dual Momentum" Ranking.
    * 3.2. PPO Divergence.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Comparison to MACD.
5. [Implementation: Production Grade](#5-implementation-production-grade)
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 122** utilizes the **Percentage Price Oscillator (PPO)**.
It is mathematically identical to MACD, except for one crucial detail: It measures the difference as a **Percentage**, not a Dollar value.
This makes PPO the standard tool for **Comparing Momentum** between different assets (e.g., Gold vs BTC vs S&P 500).
A MACD of 5 on BTC ($95,000) is noise. A MACD of 5 on Silver ($30) is a massive trend.
PPO solves this. PPO of 2% is a strong trend on *anything*.

---

# 2. The Theory: The Great Equalizer

### 2.1. Apples to Oranges

How do you know if Gold is trending stronger than the S&P 500?
You can't compare their prices. You can't compare their standard MACDs.
You MUST compare their Percentage Momentum.
PPO is the "Translator" that converts all price moves into a universal language of %.

---

# 3. The Strategy Rules

### 3.1. The Ranking Engine (Asset Allocation)

* **Universe:** XAUUSD, BTCUSD, SPY, TLT.
* **Calculate:** PPO(12, 26, 9) for all.
* **Rank:** Sort by PPO Value.
* **Trade:** Long the Top 1 asset. Warning if PPO < 0 (Bear Market).

### 3.2. PPO Squeeze

* **Setup:** PPO histogram contracts to near zero (Volatility Squeeze).
* **Trigger:** PPO Histogram breaks out (expansion).
* **Trade:** Follow the breakout direction.

---

# 4. Mathematical Derivation

$$ MACD = EMA_{12} - EMA_{26} $$
$$ PPO = \frac{MACD}{EMA_{26}} \times 100 $$

It simply asks: "By what percentage is the Fast MA above the Slow MA?"

---

# 5. Implementation

### 5.1. Python

*(From Indicator 122 Source)*

```python
def ppo(close, fast=12, slow=26):
    f = close.ewm(span=fast).mean()
    s = close.ewm(span=slow).mean()
    return ((f - s) / s) * 100
```

---

# 7. Conclusion

Strategy 122 is the **Comparator**.
GOLIATH uses it to answer the question: "Where is the Alpha?"
It prevents the bot from trading a sluggish asset just because it looks "cheap".
It forces capital into the assets with the highest relative velocity.
In a multi-asset portfolio, Strategy 122 is the primary driver of Rotation.
