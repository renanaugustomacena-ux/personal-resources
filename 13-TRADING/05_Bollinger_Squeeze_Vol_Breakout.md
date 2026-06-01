# 05 - Bollinger Bands & OBV: The Volatility-Volume Breakout

**Volume:** 05 of 50
**Strategy Type:** Volatility Expansion / Volume Breakout
**Risk Profile:** High Win Rate / Medium Drawdown
**Mathematical Basis:** Standard Deviation ($\sigma$) & Cumulative Volume Flow

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context: Bollinger & Granville](#2-historical-context-bollinger--granville)
3. [The Anatomy & Math](#3-the-anatomy--math)
    * 3.1. Standard Deviation (The Squeeze)
    * 3.2. On-Balance Volume (The Flow)
    * 3.3. Keltner Channels (The Filter)
4. [Trading Signals](#4-trading-signals)
    * 4.1. The Squeeze (Compression)
    * 4.2. The OBV Breakout (Leading Signal)
    * 4.3. The "Head Fake" Protection
5. [The Unified Strategy: "Squeeze & Flow"](#5-the-unified-strategy-squeeze--flow)
    * 5.1. Setup: Squeeze ON (BB inside KC)
    * 5.2. Trigger: Squeeze FIRE (BB Expand)
    * 5.3. Confirmation: OBV Breakout
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. Bitcoin Halvings (Volume precedes Price)
    * 6.2. The VIX Crash (2020)
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (Pandas Squeeze + OBV)
    * 7.2. Rust (Streaming Variance & OBV)
8. [Optimization & Variations](#8-optimization--variations)
    * 8.1. %B and Bandwidth
    * 8.2. Weekly OBV Trendlines
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

This strategy combines **Volatility** (Bollinger Bands) and **Volume** (OBV).

* **Bollinger Bands (John Bollinger):** Measure the *Potential Energy* of the market (Squeeze).
* **On-Balance Volume (Joe Granville):** Measures the *Kinetic Energy* (Smart Money Accumulation).

The core thesis is: **"Volume precedes Price."**
A volatility squeeze without volume is just a dead market. A volatility squeeze **with rising OBV** is a coiled spring being loaded by institutions.

---

# 2. Historical Context: Bollinger & Granville

* **John Bollinger (1980s):** Realized static percentage bands failed. Invented dynamic bands using Standard Deviation.
* **Joseph Granville (1963):** Famous for predicting the 1962 crash using OBV. He taught that "Volume is the steam that makes the choo-choo go."

Combining them creates a robust breakout system that filters out "False Breakouts" (Price moves but Volume doesn't support it).

---

# 3. The Anatomy & Math

## 3.1. Standard Deviation (The Squeeze)

* **Middle Band:** SMA(20).
* **Upper/Lower:** $\pm 2\sigma$.
* **Logic:** When bands contract inside Keltner Channels ($1.5 \times ATR$), volatility is at historical lows.

## 3.2. On-Balance Volume (OBV)

$$ OBV_t = OBV_{t-1} + \begin{cases} Vol_t & \text{if } C_t > C_{t-1} \\ -Vol_t & \text{if } C_t < C_{t-1} \\ 0 & \text{if } C_t = C_{t-1} \end{cases} $$

* **Logic:** Tracks cumulative buying/selling pressure.

---

# 4. Trading Signals

## 4.1. The Squeeze

When Bandwidth ($Upper - Lower$) hits a 6-month low, the market is coiling.

## 4.2. The OBV Breakout

Ideally, **OBV breaks its own resistance trendline BEFORE Price breaks its resistance.** This is the "Smart Money" showing their hand early.

## 4.3. Head Fake Protection

Often price breaks up false, then collapses.

* **Rule:** If Price breaks out but OBV makes a Lower High $\to$ **False Breakout**. Fade it.

---

# 5. The Unified Strategy: "Squeeze & Flow"

1. **Regime:** Bollinger Bands are inside Keltner Channels (Squeeze ON).
2. **Setup:** Price is consolidating. Draw a trendline on the OBV indicator.
3. **Trigger:**
    * **Conservative:** Wait for Squeeze to Fire (Bands Expand).
    * **Aggressive:** Buy when OBV breaks its trendline *during* the Squeeze.
4. **Stop Loss:** Recent Swing Low or Lower Bollinger Band.

---

# 6. Historical Case Studies

## 6.1. Bitcoin Halvings

Before every major bull run, BTC enters a "Boring Phase" (Squeeze). During this phase, OBV often starts creeping up while price is flat. This divergence (Price Flat, OBV Up) is the ultimate Buy Signal.

---

# 7. Implementation: Production Grade

## 7.1. Python (Pandas)

```python
import pandas as pd
import numpy as np

class SqueezeOBVStrategy:
    def __init__(self, length=20, std_dev=2.0, keltner_mult=1.5):
        self.length = length
        self.std_dev = std_dev
        self.keltner_mult = keltner_mult

    def generate_signals(self, df):
        # 1. Bollinger Bands
        df['SMA'] = df['Close'].rolling(window=self.length).mean()
        df['STD'] = df['Close'].rolling(window=self.length).std(ddof=0)
        df['UpperBB'] = df['SMA'] + (self.std_dev * df['STD'])
        df['LowerBB'] = df['SMA'] - (self.std_dev * df['STD'])

        # 2. Keltner Channels (using ATR)
        df['TR'] = np.maximum(df['High'] - df['Low'], 
                   np.maximum(abs(df['High'] - df['Close'].shift(1)), 
                              abs(df['Low'] - df['Close'].shift(1))))
        df['ATR'] = df['TR'].rolling(window=self.length).mean()
        df['UpperKC'] = df['SMA'] + (self.keltner_mult * df['ATR'])
        df['LowerKC'] = df['SMA'] - (self.keltner_mult * df['ATR'])

        # 3. Squeeze Logic
        df['Squeeze_On'] = (df['UpperBB'] < df['UpperKC']) & (df['LowerBB'] > df['LowerKC'])

        # 4. OBV Calculation
        direction = np.sign(df['Close'].diff()).fillna(0)
        df['OBV'] = (direction * df['Volume']).cumsum()
        
        # 5. OBV Trend (Simple Slope)
        df['OBV_Slope'] = df['OBV'].diff(5) # 5-bar ROC of OBV

        # 6. Signal: Squeeze Firing + Rising OBV
        df['Squeeze_Fire'] = (df['Squeeze_On'].shift(1) == True) & (df['Squeeze_On'] == False)
        
        df['Signal'] = 0
        # Long if Squeeze Fires AND OBV is rising
        df.loc[(df['Squeeze_Fire']) & (df['OBV_Slope'] > 0), 'Signal'] = 1 
        
        return df
```

## 7.2. Rust (Streaming Variance & OBV)

```rust
use std::collections::VecDeque;

pub struct VolatilityVolumeMonitor {
    period: usize,
    num_std: f64,
    window: VecDeque<f64>,
    sum: f64,
    sum_sq: f64,
    
    // OBV State
    obv: f64,
    prev_close: f64,
}

impl VolatilityVolumeMonitor {
    pub fn new(period: usize, num_std: f64) -> Self {
        Self {
            period,
            num_std,
            window: VecDeque::with_capacity(period),
            sum: 0.0,
            sum_sq: 0.0,
            obv: 0.0,
            prev_close: 0.0,
        }
    }

    pub fn update(&mut self, price: f64, volume: f64) -> Option<(f64, f64, f64, f64)> {
        // 1. Update Variance (Welford/Sliding Window)
        self.window.push_back(price);
        self.sum += price;
        self.sum_sq += price * price;

        if self.window.len() > self.period {
            if let Some(old) = self.window.pop_front() {
                self.sum -= old;
                self.sum_sq -= old * old;
            }
        }

        // 2. Update OBV
        if self.prev_close != 0.0 {
            if price > self.prev_close { self.obv += volume; }
            else if price < self.prev_close { self.obv -= volume; }
        }
        self.prev_close = price;

        if self.window.len() < self.period { return None; }

        // 3. Calculate Bands
        let n = self.period as f64;
        let mean = self.sum / n;
        let variance = (self.sum_sq / n) - (mean * mean);
        let std_dev = variance.max(0.0).sqrt();

        let upper = mean + (self.num_std * std_dev);
        let lower = mean - (self.num_std * std_dev);

        Some((upper, lower, std_dev, self.obv))
    }
}
```

---

# 8. Conclusion

The Bollinger Squeeze is the Sniper. OBV is the Spotter.

* The Sniper waits for the target (Low Volatility).
* The Spotter confirms the wind and distance (Volume Accumulation).
Together, they ensure you only take high-probability breakout trades, filtering out the noise of false moves.
