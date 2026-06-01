# 18 - VWAP Strategies: The Institutional Benchmark

**Volume:** 18 of 50
**Strategy Type:** Intraday Mean Reversion / Trend Following / Execution Benchmark
**Risk Profile:** Low Win Rate / High Reward (Scalping)
**Mathematical Basis:** Volume Weighted Average Price ($\sum (P \times V) / \sum V$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Why Institutions Care](#2-the-theory-why-institutions-care)
    * 2.1. The "Compliance" Metric
    * 2.2. Value vs Price
    * 2.3. The Rubber Band effect Intraday
3. [Trading Strategies](#3-trading-strategies)
    * 3.1. Standard Reversion (SD Bands)
    * 3.2. VWAP Boulevard (Trend Pullback)
    * 3.3. Anchored VWAP (AVWAP)
    * 3.4. The "Lunch Fade"
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Cumulative Calculation: $\frac{\sum_{i=1}^{n} (Price_i \times Volume_i)}{\sum_{i=1}^{n} Volume_i}$
    * 4.2. Resetting Daily vs Anchored
    * 4.3. Standard Deviation Bands
5. [Historical Case Studies](#5-historical-case-studies)
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Efficient Pandas Groupby)
    * 6.2. Rust (Streaming Anchored VWAP)
7. [Optimization & Variations](#7-optimization--variations)
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**VWAP (Volume Weighted Average Price)** is the single most important indicator for institutional traders.
Pension funds and Mutual funds are judged by their execution relative to VWAP.

* **Price < VWAP:** "Good Value" (Institutions Buy).
* **Price > VWAP:** "Poor Value" (Institutions Sell).
* **Price >>> VWAP:** "Overbought" (Reversion likely).

---

# 2. The Theory

## 2.1. Compliance

Algorithms passively buy when Price < VWAP to improve their average execution price for clients. This creates natural **Support** at the VWAP line.

## 2.2. Rubber Band

When price is 2-3 Standard Deviations away from VWAP, it means "Price is expensive relative to where Volume has transacted today." Unless news justifies the move, price will snap back to Fair Value (VWAP).

---

# 3. Trading Strategies

## 3.1. Standard Reversion (Mean Reversion)

1. **Anchor:** Daily Open.
2. **Bands:** Calculate Standard Deviation ($\sigma$) of price from VWAP.
3. **Entry Short:** Price touches Upper Band (+2 $\sigma$).
4. **Entry Long:** Price touches Lower Band (-2 $\sigma$).
5. **Target:** VWAP Line (0 $\sigma$).

## 3.2. VWAP Boulevard (Trend Following)

Institutions defend their positions.

1. **Context:** Strong Trend (Price > VWAP all morning).
2. **Setup:** Price pulls back to "kiss" the VWAP line.
3. **Trigger:** A Green Candle closes *off* the VWAP line.
4. **Action:** Buy. (Rejoining the trend).

## 3.3. Anchored VWAP (AVWAP)

Popularized by Brian Shannon. Instead of resetting at Midnight, reset at a significant event (Earnings, Fed Announcement, Swing Low).

* **Logic:** This shows the average price of everyone who participated *since that event*.
* **Rule:** If Price > AVWAP(Event), the "Event Crowd" is in profit (Bullish).

## 3.4. The "Lunch Fade"

Historical data shows that between 12:00 PM and 1:30 PM EST, markets tend to revert to VWAP as volume dries up. Strategy: Fade any breakout drift during lunch back to VWAP.

---

# 4. Mathematical Derivation

$$ VWAP_t = \frac{\sum_{i=0}^{t} (Price_i \times Volume_i)}{\sum_{i=0}^{t} Volume_i} $$
Standard Deviation Bands are calculated using the variance of Price from the VWAP.

---

# 5. Historical Case Studies

## 5.1. Apple Earnings Drift

Algorithms often peg AAPL to the VWAP for 3 days post-earnings to accumulate massive positions without spiking the price. The "VWAP Boulevard" strategy captures this perfectly.

## 5.2. Crypto Flash Crashes

During liquidation cascades, price often wicks exactly to the -3SD VWAP band before V-shaping. This is HFTs stepping in to buy "Deep Value."

---

# 6. Implementation: Production Grade

## 6.1. Python (Efficient)

```python
import pandas as pd
import numpy as np

class VWAPStrategy:
    def calculate_vwap(self, df):
        """ Calculates Daily VWAP and Bands """
        # 1. Typical Price
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        pv = tp * df['Volume']
        
        # 2. Group by Date for Daily Reset
        # Assuming DateTime Index
        df['Date'] = df.index.date
        
        # Cumulative Sums per day
        cum_pv = df.groupby('Date')['pv'].cumsum()
        cum_vol = df.groupby('Date')['Volume'].cumsum()
        
        df['VWAP'] = cum_pv / cum_vol
        
        # 3. Standard Deviation Bands (Simplified)
        # Real VWAP SD requires cumulative variance. 
        # Approx: Rolling StdDev of (Close - VWAP)
        dist = df['Close'] - df['VWAP']
        sigma = dist.rolling(window=20).std() 
        
        df['Upper_2SD'] = df['VWAP'] + (2 * sigma)
        df['Lower_2SD'] = df['VWAP'] - (2 * sigma)
        
        return df

    def anchored_vwap(self, df, start_date):
        """ AVWAP from a specific timestamp """
        subset = df.loc[start_date:].copy()
        tp = (subset['High'] + subset['Low'] + subset['Close']) / 3
        subset['PV'] = tp * subset['Volume']
        subset['CumPV'] = subset['PV'].cumsum()
        subset['CumVol'] = subset['Volume'].cumsum()
        return subset['CumPV'] / subset['CumVol']
```

## 6.2. Rust (Streaming Anchored VWAP)

```rust
pub struct Vwap {
    cum_pv: f64,
    cum_vol: f64,
    current_day: Option<i64>, // Unix Day ID for auto-reset
    anchor_timestamp: Option<i64>, // For AVWAP
}

impl Vwap {
    pub fn new() -> Self {
        Self { cum_pv: 0.0, cum_vol: 0.0, current_day: None, anchor_timestamp: None }
    }
    
    pub fn set_anchor(&mut self, ts: i64) {
        self.anchor_timestamp = Some(ts);
        self.cum_pv = 0.0;
        self.cum_vol = 0.0;
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64, volume: f64, timestamp: i64) -> f64 {
        // Auto-Reset Logic for Daily VWAP (if no manual anchor)
        if self.anchor_timestamp.is_none() {
             let day = timestamp / 86400;
             if let Some(d) = self.current_day {
                 if day != d {
                     self.cum_pv = 0.0;
                     self.cum_vol = 0.0;
                     self.current_day = Some(day);
                 }
             } else {
                 self.current_day = Some(day);
             }
        }

        let tp = (high + low + close) / 3.0;
        self.cum_pv += tp * volume;
        self.cum_vol += volume;
        
        if self.cum_vol == 0.0 { return tp; }
        self.cum_pv / self.cum_vol
    }
}
```

---

# 7. Optimization & Variations

## 7.1. Time-Based Filtering

VWAP Reversion works best **after 10:30 AM**. Before that, price discovery is too volatile.

## 7.2. Anchoring to Swing Highs/Lows

Instead of Time, anchor VWAP to the highest high of the previous trend. This acts as a "Trailing Stop" based on volume.

---

# 8. Risk Management

## 8.1. The Trend Day

10-15% of days are "Trend Days". Price touches VWAP once and never looks back.
**Rule:** If Price stays > +1SD for 30 minutes, **Stop Fading**. Switch to "VWAP Boulevard" (Buy Pullbacks).

## 8.2. Stop Loss

If fading the 2SD band, stop at 3SD.
If buying the VWAP Touch, stop on a close below 1SD.

---

# 9. Conclusion

VWAP is the "Referee" of the intraday battle. It connects Price Action with Liquidity.

* **Mean Reversion:** Fade extremes back to VWAP.
* **Trend Following:** Buy the VWAP bounce.
* **Support/Resistance:** AVWAP reveals who is trapped and who is winning.
