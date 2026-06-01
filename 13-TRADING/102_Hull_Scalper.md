# 102 - Hull Moving Average Scalper (HMA)

**Volume:** 102 of 100
**Strategy Type:** HFT / Scalping / Reactive
**Risk Profile:** High Transaction Costs / False Signals in Chop
**Mathematical Basis:** Weighted Moving Average Overshoot ($2 \cdot WMA(n/2) - WMA(n)$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Lag Elimination](#2-the-theory-lag-elimination)
    * 2.1. The tradeoff: Smoothness vs Lag.
    * 2.2. Alan Hull's Solution: Mathematical Overshoot.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Setup: Slope Identification.
    * 3.2. The Filter: Higher Timeframe HMA.
    * 3.3. The Trigger: HMA Color Change (Inflection Point).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The 3-Step HMA Formula.
    * 4.2. Why the $\sqrt{n}$ smoothing works.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Weighted Moving Average helper.
    * 5.2. Rust: Real-time HMA Buffer.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 102** deploys the **Hull Moving Average (HMA)**, known as the "Speed Demon" of indicators.
Standard MAs average the past, ensuring they are always behind the present.
HMA uses a weighted difference formula to effectively "project" the price forward, canceling out the lag of the smoothing process.
It creates a line that is incredibly responsive, turning almost simultaneously with the price reversal.
Strategy 102 uses this speed for **Scalping** fast-moving markets (Crypto/Futures).

---

# 2. The Theory: Lag Elimination

### 2.1. The Lag Problem

SMA(N) lags by $N/2$.
EMA(N) lags by approx $N/3$.
HMA(N) lags by almost 0 (conceptually).

### 2.2. The Solution

If you take a Fast MA ($n/2$) and subtract a Slow MA ($n$), you get the differential.
Adding this differential back to the Fast MA pushes the value *ahead* of the current price.
Hull then smoothes this "oversjot" raw data with a $\sqrt{n}$ WMA to remove the noise.

---

# 3. The Strategy Rules

### 3.1. Indicators

* **Trend HMA:** Period = 200.
* **Signal HMA:** Period = 21.

### 3.2. Setup

* **Trend:** HMA(200) Slope is Positive (Green).

### 3.3. Execution (The "Dip Buy")

1. Wait for Price to pull back towards HMA(200).
2. HMA(21) turns Red (Pullback).
3. **Entry:** Buy immediately when HMA(21) turns **Green** (Resumes Trend).
4. **Exit:** When HMA(21) turns Red again.

---

# 4. Mathematical Derivation

$$ HMA = WMA( \underbrace{2 \cdot WMA(n/2) - WMA(n)}_{\text{Lag Cancellation}} , \sqrt{n} ) $$
The term $2 \cdot WMA(n/2)$ weights the recent data twice as heavily as the full period, creating the "pre-emptive" turn.

---

# 5. Implementation: Production Grade

### 5.1. Python (Pandas)

*(From Indicator 102 Source)*

```python
def weighted_moving_average(x, window):
    weights = np.arange(1, window + 1)
    return x.rolling(window).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)

def hma(prices, period=14):
    half = int(period / 2)
    sqrt = int(np.sqrt(period))
    
    wmaf = weighted_moving_average(prices, half)
    wmas = weighted_moving_average(prices, period)
    
    raw = 2 * wmaf - wmas
    return weighted_moving_average(raw, sqrt)
```

### 5.2. Rust Real-Time

For HMA, we need efficient `Vec<f64>` management.
The `WMA` is $O(N)$. HMA is $3 \times O(N)$.
It is computationally heavier than EMA, but negligible on modern CPUs.

---

# 6. Risk Management

### 6.1. The "Hook" Risk

HMA turns so fast that in a choppy market, it will hook up and down every 3 candles.
**Solution:** The 200-period HMA Filter is mandatory. NEVER trade against the HMA(200) slope.

---

# 7. Conclusion

Strategy 102 is **Surgical**.
It does not predict the trend; it rides the immediate momentum.
Ideally suited for **Bot Trading** where reaction time is faster than human perception.
When the HMA turns, the Bot fires.
