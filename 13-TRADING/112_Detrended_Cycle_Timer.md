# 112 - Detrended Cycle Timer (DPO)

**Volume:** 112 of 100
**Strategy Type:** Cycle Trading / Timing
**Risk Profile:** Medium (Trend fighting risk)
**Mathematical Basis:** Displaced Moving Average ($P_t - SMA_{t - (N/2 + 1)}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Removing the Noise of Trend](#2-the-theory-removing-the-noise-of-trend)
    * 2.1. Time Series Decomposition ($Price = Trend + Cycle + Noise$).
    * 2.2. Isolating $Cycle$.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Cycle Low Buy.
    * 3.2. Dominant Cycle Tuning.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Displacement logic.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Handling the Shift.
    * 5.2. Rust: Future peeking precaution.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 112** employs the **Detrended Price Oscillator (DPO)**.
Standard oscillators (RSI, Stoch) are polluted by Trend. If the trend is strong Up, RSI stays Overbought.
DPO removes the trend entirely. It shows you the *heartbeat* of the market.
It is primarily a **Timing Tool**.
It answers: "I know I want to buy (Trend is Up), but *when* exactly should I click the button?"
Answer: When the Cycle is at the Bottom.

---

# 2. The Theory: Removing the Noise of Trend

### 2.1. Decomposition

Financial time series are composed of:

1. **Trend (Long term direction)**
2. **Cycle (Harmonic oscillation)**
3. **Noise (Random walk)**

DPO subtracts the Trend (approximated by a displaced SMA) from the Price.
What remains is Cycle + Noise.
By filtering (smoothing) the DPO, we isolate the Cycle.

---

# 3. The Strategy Rules

### 3.1. The Cycle Rider

* **Prerequisite:** Strategy 1 (SMA) or Strategy 113 (TRIX) says "TREND IS UP".
* **Trigger:** DPO(20) touches a local minimum (Ideally < -1.5 Std Dev).
* **Action:** Buy.
* **Logic:** We are buying a dip in an uptrend, timed specifically to the rhythmic low point of the market cycle.

### 3.2. Measuring the Dominant Cycle

GOLIATH runs an FFT (Fast Fourier Transform) or simply measures the average distance between DPO peaks to find the "Dominant Cycle Period" (e.g., 18 bars).
It then sets the DPO period to this length to maintain resonance.

---

# 4. Mathematical Derivation

$$ DPO_t = Price_t - SMA(Price, N)_{t - (N/2 + 1)} $$

We compare Price *now* to the SMA *from the past*.
Why? Because an SMA centered in the past represents the "True Trend" at that moment. The difference is the cyclical deviation.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 112 Source)*

```python
def dpo(close, period=20):
    shift = int(period / 2) + 1
    sma = close.rolling(period).mean()
    # DPO = Price - SMA.shift(shift)
    return close - sma.shift(shift)
```

*Note: In live trading, we can't shift future data back. We shift the SMA forward mentally. DPO technically looks at historical fit. For real-time, we compare Price to the Lagged SMA value.*

---

# 7. Conclusion

Strategy 112 is the **Metronome**.
It helps GOLIATH dance with the market rhythm.
Buying blindly in an uptrend allows for drawdowns. Buying at the DPO trough minimizes drawdown and maximizes the Sharpe Ratio.
It transforms "Time in Market" to "Timing the Market" (in a statistically valid way).
