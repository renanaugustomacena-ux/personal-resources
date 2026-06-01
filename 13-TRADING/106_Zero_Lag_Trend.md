# 106 - Zero Lag Exponential Moving Average (ZLEMA)

**Volume:** 106 of 100
**Strategy Type:** Trend Following / Reversal
**Risk Profile:** Noise Amplification
**Mathematical Basis:** De-trended Synthetic Data Projection ($P_{projected} = P_t + (P_t - P_{t-lag})$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Latency Cancellation](#2-the-theory-latency-cancellation)
    * 2.1. Group Delay in Digital Filters.
    * 2.2. The Ehlers Solution: Add Momentum to Price.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Zero-Lag Crossover.
    * 3.2. Divergence Trading with ZLEMA.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Lag Calculation ($Lag = (N-1)/2$).
    * 4.2. Data Projection.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: De-lagging Logic.
    * 5.2. Rust: Streaming Implementation.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 106** exploits the **Zero Lag EMA (ZLEMA)** developed by John Ehlers.
Standard Trend Following fails in modern markets because by the time the MA turns, the HFTs have already reversed the price.
ZLEMA solves this by "cheating" time.
It calculates the current momentum, assumes it will continue for $N/2$ bars, adds that value to the current price, and *then* smoothes it.
The result is a Moving Average that tracks price turns with uncanny precision, often turning *on the exact candle* of the reversal.

---

# 2. The Theory: Latency Cancellation

### 2.1. The Physics of Lag

Any filter that smooths data *must* introduce lag. It's a law of signal processing.
Lag = $\frac{Period - 1}{2}$.
For a 20-period EMA, Lag is ~9.5 bars. That's a lifetime in HFT.

### 2.2. The Solution (Projection)

If we know we are lagging by 9.5 bars, and we know the current velocity of price is $+2$/bar, we can add $9.5 \times 2 = 19$ to the current price before smoothing.
The smoothing will delay the signal back by 9.5 bars, canceling the boost.
Result: Zero Lag.

---

# 3. The Strategy Rules

### 3.1. ZLEMA Cross

* **Indicator:** ZLEMA(20).
* **Trigger:** Price Crosses ZLEMA.
  * **Buy:** Price > ZLEMA.
  * **Sell:** Price < ZLEMA.
* **Edge:** In a V-bottom, Price crosses ZLEMA 3-5 bars before it crosses a standard EMA. This 5-bar advantage is the difference between Profit and Loss in a scalping system.

### 3.2. ZLEMA vs EMA

We use a standard EMA(20) as the "Control".

* If ZLEMA > EMA: Trend is accelerating up.
* If ZLEMA < EMA: Trend is accelerating down.
* If ZLEMA crosses EMA: The acceleration has reversed (Second derivative signal).

---

# 4. Mathematical Derivation

$$ Lag = \frac{Period - 1}{2} $$
$$ Data_{projected} = Price_t + (Price_t - Price_{t-Lag}) $$
$$ ZLEMA = EMA(Data_{projected}, Period) $$

Note: $(Price_t - Price_{t-Lag})$ represents the change over the lag period. Adding it effectively projects where price *would be* if the trend continued, effectively counteracting the smoothing delay.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 106 Source)*

```python
def zlema(prices, period=14):
    lag = int((period - 1) / 2)
    # Momentum = Price - Price[t-lag]
    momentum = prices.diff(lag)
    # De-Lagged Data
    data = prices + momentum
    return data.ewm(span=period, adjust=False).mean()
```

---

# 7. Conclusion

Strategy 106 is **The Time Machine**.
It allows GOLIATH to trade the "Future" price series today.
While it comes at the cost of slight overshoot (if price suddenly stops, ZLEMA keeps going for a moment), the benefit of entering trends early far outweighs the cost of false signals in a high-volatility regime.
