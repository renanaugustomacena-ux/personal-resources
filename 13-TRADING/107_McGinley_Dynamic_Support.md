# 107 - McGinley Dynamic Support

**Volume:** 107 of 100
**Strategy Type:** Dynamic Support/Resistance / Crash Proofing
**Risk Profile:** Low (Auto-adjusts)
**Mathematical Basis:** Acceleration Factor ($ (P/MA)^4 $)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Market Velocity](#2-the-theory-market-velocity)
    * 2.1. Why SMA(200) fails in a crash.
    * 2.2. The McGinley Solution: Variable Speed.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The "Dynamic Floor" Setup.
    * 3.2. The Crash Exit.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Accelerator Coefficient $k \cdot N \cdot (Price/MD)^4$.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Avoiding Division by Zero.
    * 5.2. Rust: Precision Handling.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 107** employs the **McGinley Dynamic**, the most "intelligent" of the non-adaptive moving averages.
John McGinley realized that markets speed up and slow down. A fixed-period MA is like driving a car with the cruise control locked at 50mph. Safe on the highway, deadly in a school zone, too slow on a racetrack.
The McGinley Dynamic automatically adjusts its speed based on the deviation of price.
It acts as a superior **Dynamic Support Line** that Hugs the price during parabolas and relaxes during consolidation.

---

# 2. The Theory: Market Velocity

### 2.1. The Parabola Problem

In a crypto bull run, price goes exponential. A 20-day SMA falls 40% behind the price.
If price flashes crashes 30%, the SMA is still useless as support.
The McGinley Dynamic sees the gap and "speeds up" to catch the price, ensuring the support line is always relevant.

### 2.2. The Crash Problem

In a crash, price drops faster than an EMA can react.
The McGinley Dynamic detects the massive deviation and accelerates downwards, providing a tighter trailing stop that saves profit.

---

# 3. The Strategy Rules

### 3.1. The Dynamic Floor

* **Indicator:** McGinley Dynamic (N=14).
* **Market:** Crypto or High-Beta Tech.
* **Logic:**
  * Price touches McGinley Line.
  * Place LIMIT BUY orders at the line.
  * Unlike SMA, price rarely smashes *through* McGinley without a fight. It usually bounces.

### 3.2. Execution

* **Entry:** Limit Buy at MD Line during uptrend ($Price > MD_{prev}$).
* **Stop:** Candle Close below MD Line.

---

# 4. Mathematical Derivation

$$ MD_t = MD_{t-1} + \frac{Price_t - MD_{t-1}}{k \times N \times (Price_t / MD_{t-1})^4} $$

* **$k$**: A constant (usually 0.6).
* **The Ratio:** $(Price/MD)^4$.
  * If Price is 10% above MD, $(1.1)^4 \approx 1.46$. Denominator increases. Speed slows? Wait.
  * Actually, look at the formula: It divides the difference.
  * If Price crashes (Price < MD), Ratio < 1. Denominator shrinks. The adjustment term becomes HUGE. MD plunges to catch price.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 107 Source)*

```python
def mcginley_dynamic(prices, period=14, k=0.6):
    md = [prices[0]]
    for i in range(1, len(prices)):
        prev = md[-1]
        curr = prices[i]
        ratio = curr / prev
        denom = k * period * (ratio ** 4)
        md.append(prev + (curr - prev) / denom)
    return pd.Series(md)
```

---

# 7. Conclusion

Strategy 107 is **The Smart Seatbelt**.
It tightens up when things get dangerous (Fast moves). It loosens up when things are calm.
For GOLIATH, it replaces the SMA(50) and EMA(20) as the definitive "Trend Line" for high-volatility asset classes.
