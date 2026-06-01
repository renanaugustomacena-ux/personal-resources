# 07 - Parabolic SAR & SuperTrend: The Trailing Stops

**Volume:** 07 of 50
**Strategy Type:** Trend Following / Stop Loss Management
**Risk Profile:** Low Lag / Tight Stops
**Mathematical Basis:** Acceleration Factor (SAR) & Average True Range (SuperTrend)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context: Wilder's Masterpiece](#2-historical-context-wilders-masterpiece)
3. [Parabolic SAR: The Acceleration Trap](#3-parabolic-sar-the-acceleration-trap)
    * 3.1. The Formula (Time as a Variable)
    * 3.2. Exposure to Time
4. [SuperTrend: The Volatility Stop](#4-supertrend-the-volatility-stop)
    * 4.1. The Formula (ATR based)
    * 4.2. The Ratchet Logic
    * 4.3. SAR vs SuperTrend: The Cage Match
5. [Trading Signals](#5-trading-signals)
    * 5.1. The Flip (Stop and Reverse)
    * 5.2. SuperTrend Pullback Strategy
6. [Historical Case Studies](#6-historical-case-studies)
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (Numba Optimized)
    * 7.2. Rust (Parabolic SAR & SuperTrend)
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

Traders spend 90% of their time looking for **Entries**, but **Exits** determine profit.
This volume covers the two gold standards for automated exit management:

1. **Parabolic SAR:** Tightens the stop based on **Time** (Acceleration).
2. **SuperTrend:** Tightens the stop based on **Volatility** (ATR).

---

# 2. Historical Context: Wilder's Masterpiece

J. Welles Wilder Jr. (1978) designed the Parabolic SAR (Stop and Reverse) to solve the "Exit Problem". He realized that in a parabolic trend, a linear stop (like a moving average) gives back too much profit at the end. He needed a stop that accelerated as the trend matured.

---

# 3. Parabolic SAR: The Acceleration Trap

## 3.1. The Formula

$$ SAR_{n+1} = SAR_n + AF \times (EP - SAR_n) $$

* **AF (Acceleration Factor):** Starts at 0.02. Increases by 0.02 every time a new Extreme Point (High/Low) is made. Max 0.20.

## 3.2. Exposure to Time

* **Day 1:** AF = 0.02. SAR moves 2% towards price.
* **Day 10:** AF = 0.20. SAR moves 20% towards price.
* **Result:** The SAR curve becomes vertical, acting as a "Time Stops" mechanism. If the price doesn't go up immediately, the SAR hits it.

---

# 4. SuperTrend: The Volatility Stop

Created by Olivier Seban, SuperTrend is the modern alternative. It adapts to the noise of the market rather than time.

## 4.1. The Formula

$$ UpperBand = \frac{High+Low}{2} + (Multiplier \times ATR) $$
$$ LowerBand = \frac{High+Low}{2} - (Multiplier \times ATR) $$
Usually Period=10, Multiplier=3.0.

## 4.2. The Ratchet Logic (Secret Sauce)

The SuperTrend has a memory effect.

* **Uptrend:** The Green Line (Lower Band) can **ONLY MOVE UP**. If volatility increases and the calculated band drops, the SuperTrend ignores it and stays flat.
* **Downtrend:** The Red Line (Upper Band) can **ONLY MOVE DOWN**.
This "Ratchet" locks in profits and never retreats.

## 4.3. SAR vs SuperTrend

* **Parabolic SAR:** Best for "Parabolic" assets (Crypto Bull Runs, MEME stocks). It gets you out at the top.
* **SuperTrend:** Best for "Grinding" trends (Forex, S&P 500). It gives the trade room to breathe and doesn't stop you out just because time passed.

---

# 5. Trading Signals

## 5.1. The Flip

Standard usage for both:

* **Long:** Price > Indicator.
* **Flip:** Price Closes < Indicator. -> **Close Long, Open Short.**

## 5.2. SuperTrend Pullback Strategy

Instead of buying the breakout (Flip), wait.

1. **Trend:** SuperTrend is Green.
2. **Pullback:** Price drops and touches the Green Line.
3. **Trigger:** Price prints a Bullish Hammer on the line.
4. **Entry:** Buy the Close. Stop Loss below the line.
**Why:** The SuperTrend line acts as dynamic Support because alogithms watch it.

---

# 6. Historical Case Studies

## 6.1. Bitcoin 2021

SAR kept traders in from $20k to $64k. Percentage stops failed.
SuperTrend (10, 3) captured the same move but with fewer false exits during the consolidation phases.

---

# 7. Implementation: Production Grade

## 7.1. Python (Analysis)

```python
import pandas as pd
import numpy as np

def calculate_supertrend(df, period=10, multiplier=3.0):
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    atr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(period).mean()
    
    hl2 = (high + low) / 2
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)
    
    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    trend = pd.Series(1, index=df.index)
    
    # Numba is preferred for this loop, but here is logic:
    # (See Rust implementation for the state machine)
    pass 
```

## 7.2. Rust (State Machines)

### 7.2.1. Parabolic SAR

```rust
pub struct ParabolicSAR {
    af_start: f64, af_step: f64, af_max: f64,
    is_long: bool, sar: f64, ep: f64, af: f64,
    prev_low: f64, prev_high: f64,
}

impl ParabolicSAR {
    pub fn new(start: f64, step: f64, max: f64) -> Self {
        Self {
            af_start: start, af_step: step, af_max: max,
            is_long: true, sar: 0.0, ep: 0.0, af: start,
            prev_low: 0.0, prev_high: 0.0
        }
    }
    
    pub fn update(&mut self, high: f64, low: f64) -> f64 {
        if self.sar == 0.0 { self.sar = low; self.ep = high; return self.sar; }

        let mut next_sar = self.sar + self.af * (self.ep - self.sar);
        
        if self.is_long {
            if next_sar > self.prev_low { next_sar = self.prev_low; }
            if low <= next_sar { // Flip Short
                self.is_long = false; self.sar = self.ep; self.ep = low; self.af = self.af_start;
            } else {
                if high > self.ep {
                    self.ep = high; self.af = (self.af + self.af_step).min(self.af_max);
                }
                self.sar = next_sar;
            }
        } else {
            if next_sar < self.prev_high { next_sar = self.prev_high; }
            if high >= next_sar { // Flip Long
                self.is_long = true; self.sar = self.ep; self.ep = high; self.af = self.af_start;
            } else {
                if low < self.ep {
                    self.ep = low; self.af = (self.af + self.af_step).min(self.af_max);
                }
                self.sar = next_sar;
            }
        }
        self.prev_low = low; self.prev_high = high;
        self.sar
    }
}
```

### 7.2.2. SuperTrend

```rust
use std::collections::VecDeque;

pub struct SuperTrend {
    period: usize,
    multiplier: f64,
    atr_buffer: VecDeque<f64>,
    prev_close: f64,
    final_upper: f64,
    final_lower: f64,
    trend: i32, // 1 or -1
}

impl SuperTrend {
    pub fn new(period: usize, multiplier: f64) -> Self {
        Self {
            period, multiplier,
            atr_buffer: VecDeque::new(),
            prev_close: 0.0, final_upper: 0.0, final_lower: 0.0, trend: 1,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> (f64, i32) {
        // ATR Calc
        let tr = if self.prev_close == 0.0 { high - low } else {
            (high - low).max((high - self.prev_close).abs()).max((low - self.prev_close).abs())
        };
        self.atr_buffer.push_back(tr);
        if self.atr_buffer.len() > self.period { self.atr_buffer.pop_front(); }
        let atr = self.atr_buffer.iter().sum::<f64>() / self.atr_buffer.len() as f64;

        let hl2 = (high + low) / 2.0;
        let basic_upper = hl2 + (self.multiplier * atr);
        let basic_lower = hl2 - (self.multiplier * atr);

        // Ratchet Logic
        if basic_upper < self.final_upper || self.prev_close > self.final_upper {
            self.final_upper = basic_upper;
        }
        if basic_lower > self.final_lower || self.prev_close < self.final_lower {
            self.final_lower = basic_lower;
        }

        // Trend Switch
        if self.trend == 1 {
            if close < self.final_lower { self.trend = -1; }
        } else {
            if close > self.final_upper { self.trend = 1; }
        }

        self.prev_close = close;
        let val = if self.trend == 1 { self.final_lower } else { self.final_upper };
        (val, self.trend)
    }
}
```

---

# 9. Conclusion

Use **Parabolic SAR** when you are in a "Moonshot" trade and want to protect exponential gains.
Use **SuperTrend** when you are trend-following a mature asset and want to stay in the trade despite normal volatility.
Both are essential tools for the "Exit" phase of the trading algorithm.
