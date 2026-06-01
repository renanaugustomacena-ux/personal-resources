# 109 - Aroon Time Oscillator

**Volume:** 109 of 100
**Strategy Type:** Time-Based Trend Following
**Risk Profile:** Low (Exit is naturally timed to consolidation)
**Mathematical Basis:** Time Decay ($T_{since\_high}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Time Kills Trends](#2-the-theory-time-kills-trends)
    * 2.1. Magnitude vs Duration.
    * 2.2. Validating trend freshness.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Aroon Up/Down Zones.
    * 3.2. The Oscillator Zero-Cross.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Formulas for Aroon Up/Down.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Rolling Argmax.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 109** uses the **Aroon Oscillator**.
Most indicators (RSI, MACD) measure Price Magnitude. They tell you "Price moved a lot".
Aroon measures **Time**. It tells you "Price moved *recently*".
If a trend is strong, it *must* make new highs frequently.
If 20 days pass without a new high, the trend is "Stale", even if price hasn't dropped much.
Strategy 109 exits stale trends *before* they roll over.

---

# 2. The Theory: Time Kills Trends

### 2.1. Freshness

* **Aroon Up = 100:** New High Today. (Trend is Fresh).
* **Aroon Up = 50:** New High was N/2 days ago. (Trend is Aging).
* **Aroon Up = 0:** No New High in N days. (Trend is Dead).

### 2.2. The Oscillator

By subtracting Down from Up, we get a single metric $[-100, 100]$.

* $+100$: Strong Bull.
* $-100$: Strong Bear.
* $0$: Consolidation (Highs and Lows are equidistant in time).

---

# 3. The Strategy Rules

### 3.1. Setup

* **Indicator:** Aroon(25).

### 3.2. Execution

* **Long:** Aroon Oscillator crosses above +50. (Bulls are dominant and active *recently*).
* **Short:** Aroon Oscillator crosses below -50.
* **Exit:** Aroon Oscillator crosses Zero.
  * This is crucial. We don't wait for a reversal signal. We exit when the trend stops being "Active" (Zero Line).

---

# 4. Mathematical Derivation

$$ Up = \frac{N - \text{DaysSinceHigh}}{N} \times 100 $$
$$ Down = \frac{N - \text{DaysSinceLow}}{N} \times 100 $$
$$ Osc = Up - Down $$

---

# 5. Implementation

### 5.1. Python

*(From Indicator 109 Source)*

```python
def aroon_osc(high, low, period=25):
    up = high.rolling(period+1).apply(lambda x: (period - x.argmax())/period * 100, raw=True)
    down = low.rolling(period+1).apply(lambda x: (period - x.argmin())/period * 100, raw=True)
    return up - down
```

---

# 7. Conclusion

Strategy 109 is **The Clockwatcher**.
It prevents GOLIATH from falling in love with a stagnant position.
"Price is holding up well" is a dangerous thought. "Price hasn't made a high in 15 days" is an actionable fact.
Aroon forces the portfolio to rotate capital into assets that are moving *now*.
