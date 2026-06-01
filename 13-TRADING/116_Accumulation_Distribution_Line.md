# 116 - Accumulation Distribution Line (ADL)

**Volume:** 116 of 100
**Strategy Type:** Volume Flow / Smart Money Tracker
**Risk Profile:** Low (Confirmation tool)
**Mathematical Basis:** Cumulative Close Location Value ($CLV \times Volume$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Smart Money Footprints](#2-the-theory-smart-money-footprints)
    * 2.1. The Close Location Value (CLV).
    * 2.2. Intrabar Battle Dynamics.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The ADL Divergence (The Primary Signal).
    * 3.2. Trend Confirmation.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. $CLV = ((C-L) - (H-C)) / (H-L)$.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Cumulative Sum.
    * 5.2. Rust: State maintenance.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 116** utilizes the **Accumulation/Distribution Line (ADL)**.
It is based on a simple premise: **Price is the Opinion, Volume is the Conviction.**
If price moves up but closes near the low of the bar (Low CLV) on high volume, it is **Distribution** (Selling), even if the candle is green.
If price falls but closes off the lows (High CLV) on high volume, it is **Accumulation** (Buying), even if the candle is red.
ADL tracks the flow of "Smart Money" which often precedes price moves.

---

# 2. The Theory: Smart Money Footprints

### 2.1. The Intrabar Battle

Standard analysis looks at Open vs Close.
ADL looks at Close vs Range.

* **Close = High:** Buyers won 100% of the battle ($CLV = 1$).
* **Close = Low:** Sellers won 100% of the battle ($CLV = -1$).
* **Close = Midpoint:** Tie ($CLV = 0$).

### 2.2. Hidden Volume

Institutions accumulate positions over days or weeks. They try to hide it by not moving the price too much.
However, their buying pressure inevitably pushes the Close towards the High of the daily range.
ADL detects this "drift" and rises, often **before** the price breakout occurs.

---

# 3. The Strategy Rules

### 3.1. ADL Divergence (The "Tell")

* **Bullish Divergence:** Price makes Lower Low, ADL makes Higher Low.
  * *Meaning:* Sellers are pushing price down, but they are meeting "Iceberg" bids that are absorbing the selling and closing the price off the lows. Reversal imminent.
* **Bearish Divergence:** Price makes Higher High, ADL makes Lower High.
  * *Meaning:* Buyers are pushing price up, but institutions are selling into the strength (Distribution), forcing closes off the highs. Crash imminent.

### 3.2. Trend Confirmation

* **Rule:** Never go Long if ADL is trending Down. Never go Short if ADL is trending Up.
* **GOLIATH Filter:** If Strategy 105 (T3) says UP, check Strategy 116. If ADL agrees, take the trade. If not, Wait.

---

# 4. Mathematical Derivation

$$ CLV = \frac{(Close - Low) - (High - Close)}{High - Low} $$
$$ MFV = CLV \times Volume $$
$$ ADL_t = ADL_{t-1} + MFV_t $$

---

# 5. Implementation

### 5.1. Python

*(From Indicator 116 Source)*

```python
def adl(high, low, close, volume):
    # Close Location Value
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0) # Handle Doji (High=Low)
    mfv = clv * volume
    return mfv.cumsum()
```

---

# 7. Conclusion

Strategy 116 is the **X-Ray Machine**.
It sees inside the candle.
A green candle with a long upper wick is actually a "Selling" candle (Low CLV).
A red candle with a long lower wick is actually a "Buying" candle (High CLV).
By summing these internal forces, ADL reveals the true intent of the market participants.
