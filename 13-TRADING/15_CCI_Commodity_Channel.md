# 15 - Commodity Channel Index (CCI): The Cyclic Deviation

**Volume:** 15 of 50
**Strategy Type:** Mean Reversion / Momentum Breakout / Cycle Trading
**Risk Profile:** High Volatility / Unbounded Oscillator
**Mathematical Basis:** Mean Deviation (MAD) Divisor (Robust Statistics)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Donald Lambert's Cycle](#2-the-theory-donald-lamberts-cycle)
    * 2.1. Developed for Cyclical Commodities (Corn, Soybeans, Gold)
    * 2.2. Typical Price (H+L+C)/3
    * 2.3. Why Mean Absolute Deviation (MAD) is better than Standard Deviation
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Trend Signal (+100 / -100 Breakout)
    * 3.2. The Overbought Signal (+200 / -200 Reversion)
    * 3.3. The Zero Line Reject (Trend Continuation)
    * 3.4. Woodies CCI Logic (Patterns)
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Constant 0.015
    * 4.2. MAD vs Standard Deviation
5. [Microstructure & HFT](#5-microstructure--hft)
    * 5.1. Computational Logic (Iterative Loop)
    * 5.2. Detecting "Fat Tail" Events
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Pandas MAD)
    * 6.2. Rust (Optimized Ring Buffer)
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Commodity Channel Index (CCI)** was developed by Donald Lambert in 1980 to solve the problem of "Pinned Oscillators" (like RSI).
RSI pins at 100 in a strong trend, hiding further acceleration.
CCI is **Unbounded**. It can go to +200, +300, or +500.
This makes it perfect for **Parabolic Trends** (Crypto, Commodities) where price deviates significantly from the mean.

---

# 2. The Theory

Lambert assumed markets move in cycles.

* **+100 to -100:** The "Normal" Noise Zone (70-80% of data).
* **Outside:** The "Trend" Zone.

**Mean Deviation (MAD):** Lambert chose the *average absolute deviation* instead of Standard Deviation because it is less sensitive to a single massive outlier, making the indicator smoother than Bollinger Bands %B.

---

# 3. The Strategy Rules

## 3.1. Trend Trading (Standard)

* **Buy:** CCI crosses above +100.
* **Sell:** CCI crosses below -100.
* **Exit:** CCI falls back inside the range.

## 3.2. Mean Reversion (Overbought)

* **Wait:** CCI > +200. (Extreme deviation).
* **Trigger:** CCI crosses back below +100.
* **Logic:** The elastic band has snapped.

## 3.3. Woodies CCI (Patterns)

Ken Wood ("Woodie") traded patterns on the CCI line itself, ignoring price.

* **Ghost:** Head and Shoulders on CCI.
* **Zero Line Reject:** CCI approaches 0 from above (in downtrend), kisses it, and turns down. This is a bearish trend continuation signal.
* **Vegas Pattern:** A rounding top/bottom at the +/- 100 line.

---

# 4. Mathematical Derivation

$$ CCI = \frac{TP - SMA(TP)}{0.015 \times MD} $$

1. **Typical Price ($TP$):** $(H+L+C)/3$.
2. **SMA:** Simple Moving Average of TP.
3. **Mean Deviation ($MD$):** $\frac{1}{N} \sum |TP_i - SMA|$.
4. **0.015:** Scaling constant.

---

# 5. Microstructure & HFT

In HFT, CCI is computationally expensive because calculating Mean Deviation requires iterating over the window *twice* (once for Mean, once for Deviation) or storing the history.

* **Optimization:** HFTs often approximate MD using Welford-like updates or simply use Standard Deviation (making it a Z-Score) for speed, though purists argue this destroys the "CCI" character.
* **Fat Tails:** A CCI > 300 is roughly a 4-sigma event. This signals a Liquidity Vacuum.

---

# 6. Implementation: Production Grade

## 6.1. Python (Pandas)

```python
import pandas as pd
import numpy as np

def calculate_cci(df: pd.DataFrame, period=20, c=0.015):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    sma = tp.rolling(period).mean()
    
    # Efficient MAD calculation using rolling apply or explicit logic
    def mad(x):
        return np.mean(np.abs(x - np.mean(x)))
    
    # Raw=True for speed
    md = tp.rolling(period).apply(mad, raw=True)
    
    # Avoid zero division
    md = md.replace(0, 1e-9)
    
    cci = (tp - sma) / (c * md)
    return cci
```

## 6.2. Rust (Optimized Ring Buffer)

Calculating Mean Deviation efficiently is harder than Standard Deviation. We iterate the buffer.

```rust
use std::collections::VecDeque;

pub struct CommodityChannelIndex {
    period: usize,
    history: VecDeque<f64>, // Stores TP history
    c: f64,
}

impl CommodityChannelIndex {
    pub fn new(period: usize) -> Self {
        Self {
            period,
            history: VecDeque::with_capacity(period + 1),
            c: 0.015,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Option<f64> {
        let tp = (high + low + close) / 3.0;
        
        self.history.push_back(tp);
        if self.history.len() > self.period {
            self.history.pop_front();
        }
        
        if self.history.len() < self.period {
            return None;
        }
        
        // 1. Calculate SMA
        let sum: f64 = self.history.iter().sum();
        let sma = sum / self.period as f64;
        
        // 2. Calculate Mean Deviation (MD)
        // Must iterate to find |TP_i - SMA|
        let sum_abs_diff: f64 = self.history.iter()
            .map(|&val| (val - sma).abs())
            .sum();
            
        let md = sum_abs_diff / self.period as f64;
        
        // 3. CCI
        if md == 0.0 {
            return Some(0.0);
        }
        
        let cci = (tp - sma) / (self.c * md);
        
        Some(cci)
    }
}
```

---

# 7. Risk Management

## 7.1. The Infinite Scale

Since CCI is unbounded, "Overbought" is relative.
**Rule:** Never Short a strong asset just because CCI > 200. It can go to 500.
Wait for the **Hook Down**.

## 7.2. Stop Loss

Use the **Low of the Setup Bar**.
If you buy the +100 Breakout, place Stop at the Low of that breakout candle.

---

# 8. Conclusion

CCI is robust, cyclic, and unbounded.

* **Best Use:** Catching the midpoint of a trend (buying the +100 crossover).
* **Worst Use:** Fading the extremes in a parabolic market (Crypto).
For GOLIATH, we use it as a **Cycle Filter** for Commodities and FX derivatives.
