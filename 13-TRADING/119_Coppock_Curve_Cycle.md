# 119 - Coppock Curve Cycle

**Volume:** 119 of 100
**Strategy Type:** Long-Term Bottom Detection
**Risk Profile:** Low (Very slow signal)
**Mathematical Basis:** WMA(ROC(14) + ROC(11))

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Grief and Recovery](#2-the-theory-grief-and-recovery)
    * 2.1. Edwin Coppock & The Episcopal Church.
    * 2.2. The 11-14 month mourning period.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Monthly Buy Signal.
    * 3.2. The Macro Filter.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Summing ROCs.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: WMA implementation.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 119** utilizes the **Coppock Curve**.
It is a **Monthly** indicator designed to identify the end of Bear Markets.
It is famous for calling major market bottoms (1929, 1987, 2000, 2008) with high precision.
It is NOT for day trading. It is for **Strategic Positioning**.

---

# 2. The Theory: Grief and Recovery

### 2.1. The Psychology of Loss

Coppock asked the Church: "How long do people grieve?"
Answer: 11 to 14 months.
He applied this to markets. When investors lose money, they grieve. They leave the market.
It takes ~11-14 months for the emotional wound to heal and for them to return.
The Coppock Curve measures this psych-cycle using long-term ROCs.

---

# 3. The Strategy Rules

### 3.1. The Strategic Buy

* **Timeframe:** Monthly (or Weekly with scaled parameters).
* **Signal:** Coppock Curve is below Zero.
* **Trigger:** Coppock Curve turns UP.
* **Action:** Validates a "Generational Buy" opportunity. GOLIATH switches to Max Long exposure.

### 3.2. Dealing with HFT

For HFT/Algo trading, we use a scaled version (e.g., on 4-Hour or Daily charts) to detect medium-term cycle lows.
Rules:

1. Wait for Curve < 0.
2. Wait for uptick.
3. Enter Trend Following strategies (101-105).

---

# 4. Mathematical Derivation

$$ ROC_{14} = ROC(Close, 14) $$
$$ ROC_{11} = ROC(Close, 11) $$
$$ Coppock = WMA_{10}(ROC_{14} + ROC_{11}) $$

The weighted moving average gives precedence to recent data, making it turn faster than a standard MA.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 119 Source)*

```python
def coppock(close, roc1=14, roc2=11, wma_pd=10):
    r1 = close.pct_change(roc1) * 100
    r2 = close.pct_change(roc2) * 100
    total = r1 + r2
    # WMA
    weights = np.arange(1, wma_pd + 1)
    return total.rolling(wma_pd).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
```

---

# 7. Conclusion

Strategy 119 is the **Calendar**.
它 tells GOLIATH what "Season" it is.
Is it Winter (Bear Market, Curve < 0)? Or Spring (Recovery, Curve Turning Up)?
Strategies that work in Summer (Trend) fail in Winter.
Coppock provides the long-term context that prevents the bot from fighting the season.
