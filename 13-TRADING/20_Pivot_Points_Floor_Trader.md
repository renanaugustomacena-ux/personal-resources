# 20 - Pivot Points & Fibonacci: The Invisible Grid

**Volume:** 20 of 50
**Strategy Type:** Support & Resistance / Mean Reversion / Grid Trading
**Risk Profile:** Low Win Rate / High Reward (at key levels)
**Mathematical Basis:** Geometry, Ratios, and Historical Averages ($H+L+C/3$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context: Floor Traders & Mathematicians](#2-historical-context-floor-traders--mathematicians)
3. [Mathematical Foundations](#3-mathematical-foundations)
    * 3.1. Standard Floor Pivots (The Classic)
    * 3.2. Woodie's Pivots (Weighting the Close)
    * 3.3. Camarilla Pivots (Mean Reversion)
    * 3.4. Fibonacci Ratios (The Golden Mean)
4. [Trading Strategies: The Grid](#4-trading-strategies-the-grid)
    * 4.1. Pivot Fade (Range Day)
    * 4.2. Pivot Breakout (Trend Day)
    * 4.3. The CPR Squeeze (Central Pivot Range)
    * 4.4. The Golden Bungee (Fibonacci Counter-Trend)
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python (Comprehensive Pivot Calculator)
    * 5.2. Rust (Pivots & ZigZag for Fibs)
6. [Optimization & Variations](#6-optimization--variations)
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Pivot Points** and **Fibonacci Retracements** serve the same purpose: they impose an orderly grid over chaotic price action.

* **Pivot Points** are based on *Time* (Yesterday's OHLC). They are the "Floor Trader's Map."
* **Fibonacci Levels** are based on *Geometry* (The Golden Ratio $\phi$).
When a Pivot Level aligns with a Fibonacci Level (e.g., S1 aligns with 61.8%), it creates a **Confluence Zone**—a concrete floor where algorithmic buying is statistically most likely to occur.

---

# 2. Historical Context: Floor Traders & Mathematicians

**Pivot Points:** Before computers, Floor Traders in Chicago calculated $P, R1, S1$ by hand on cards. Because everyone watched them, they became self-fulfilling prophecies.
**Fibonacci:** Ralph Nelson Elliott applied the sequence ($1, 1, 2, 3, 5...$) to market waves in the 1930s. Today, HFT algorithms use these levels as automated "take profit" zones.

---

# 3. Mathematical Foundations

## 3.1. Standard Floor Pivots

Based on Yesterday's High ($H$), Low ($L$), and Close ($C$).

1. **Pivot (P):** $(H + L + C) / 3$
2. **R1 / S1:** $(2 \times P) - L$  /  $(2 \times P) - H$
3. **R2 / S2:** $P + (H - L)$  /  $P - (H - L)$

## 3.2. Woodie's Pivots

Gives more weight to the Close (Current Sentiment).
$$ P = \frac{H + L + (2 \times C)}{4} $$

## 3.3. Camarilla Pivots

Developed by Nick Scott for tight intraday scalping.
$$ R3 = C + \frac{(H - L) \times 1.1}{12} $$
$$ S3 = C - \frac{(H - L) \times 1.1}{12} $$

* **Logic:** Fade R3/S3. Breakout at R4/S4.

## 3.4. Fibonacci Ratios

* **0.236:** Shallow pullback (High Momentum).
* **0.382:** Standard.
* **0.618:** Golden Ratio. The most critical level.
* **1.618:** Golden Extension (Target).

---

# 4. Trading Strategies: The Grid

## 4.1. Pivot Fade (Range Day)

* **Context:** Open within Range.
* **Trigger:** Price touches S1 or R1 and slows (Doji).
* **Action:** Fade back to Pivot (P).

## 4.2. Pivot Breakout (Trend Day)

* **Context:** Open above Pivot.
* **Trigger:** Price breaks R1 with Volume.
* **Action:** Long. Target R2.

## 4.3. The CPR Squeeze (Central Pivot Range)

A powerful strategy from Indian markets.

* **TC (Top Central):** $(Pivot - BC) + Pivot$
* **BC (Bottom Central):** $(H+L)/2$
* **Rule:** If the distance between TC and BC is very narrow (Narrow Range Day yesterday), expect a **Trending Day** today. Breakout of the CPR is the entry.

## 4.4. The Golden Bungee

1. **Impulse:** Price moves > 3x ATR.
2. **Limit Orders:** Stack bids at 38.2%, 50%, 61.8%.
3. **Target:** 0.236 Retracement.
4. **Stop:** Close below 78.6%.

---

# 5. Implementation: Production Grade

## 5.1. Python (Comprehensive)

```python
import pandas as pd
import numpy as np

class PivotStrategy:
    def calculate_all_pivots(self, df):
        """ Expects Daily DF with High, Low, Close. Shifts inside. """
        # Yesterday's data
        h = df['High'].shift(1)
        l = df['Low'].shift(1)
        c = df['Close'].shift(1)
        
        # 1. Standard
        p = (h + l + c) / 3
        r1 = (2 * p) - l
        s1 = (2 * p) - h
        
        # 2. CPR (Central Pivot Range)
        bc = (h + l) / 2
        tc = (p - bc) + p
        
        # 3. Camarilla (Scalping)
        rng = h - l
        cam_r3 = c + (rng * 1.1 / 12)
        cam_s3 = c - (rng * 1.1 / 12)
        cam_r4 = c + (rng * 1.1 / 2)
        cam_s4 = c - (rng * 1.1 / 2)
        
        df['Pivot'] = p
        df['R1'] = r1; df['S1'] = s1
        df['TC'] = tc; df['BC'] = bc
        df['Cam_R3'] = cam_r3; df['Cam_S3'] = cam_s3
        
        # CPR Width (Volatility filter)
        df['CPR_Width'] = (df['TC'] - df['BC']).abs()
        
        return df

    def find_fib_levels(self, high, low):
        diff = high - low
        return {
            '0.382': high - (diff * 0.382),
            '0.618': high - (diff * 0.618)
        }
```

## 5.2. Rust (Pivots & ZigZag)

```rust
// 1. Pivot Points Struct
pub struct PivotPoints {
    pub p: f64,
    pub r1: f64, pub s1: f64,
    pub r2: f64, pub s2: f64,
    pub tc: f64, pub bc: f64, // CPR
}

impl PivotPoints {
    pub fn calculate(high: f64, low: f64, close: f64) -> Self {
        let p = (high + low + close) / 3.0;
        let r1 = (2.0 * p) - low;
        let s1 = (2.0 * p) - high;
        let r2 = p + (high - low);
        let s2 = p - (high - low);
        
        // CPR
        let bc = (high + low) / 2.0;
        let tc = (p - bc) + p;
        
        Self { p, r1, s1, r2, s2, tc, bc }
    }
}

// 2. ZigZag for Fibs
pub struct ZigZag {
    deviation_pct: f64,
    last_high: f64,
    last_low: f64,
    trend: i8, // 1 Up, -1 Down
}

impl ZigZag {
    pub fn new(dev: f64) -> Self {
        Self { deviation_pct: dev, last_high: 0.0, last_low: f64::MAX, trend: 0 }
    }
    
    pub fn update(&mut self, price: f64) -> Option<(String, f64)> {
        // Simple ZigZag logic to detect swing points...
        // Returns Some("SwingHigh", price) or Some("SwingLow", price)
        None // Placeholder for brevity
    }
}
```

---

# 6. Optimization & Variations

## 6.1. Week/Month/Year

Day traders use Daily Pivots.
Swing traders use Weekly Pivots.
Institutions use **Yearly Pivots** (Jan 1st calculation) to define the macro trend for the entire year.

## 6.2. Confluence Scoring

If **Daily S1** overlaps with **Weekly Pivot** AND **Fib 61.8%**, the level is "Concrete."
GOLIATH assigns a Score (0-100) to every level.

* Score > 80: Place Limit Order.
* Score < 50: Ignore.

---

# 7. Risk Management

## 7.1. The Chop Rule

If price crosses the Pivot Point (P) back and forth 5 times in an hour, the level is "burned." Market is seeking liquidity elsewhere. Stop trading the Pivot.

## 7.2. Breath

Place stops 0.2% *behind* the level, not *on* the level. Algos hunt exact numbers.

---

# 8. Conclusion

Support and Resistance are not lines; they are zones of probability. **Pivot Points** provides the static map. **Fibonacci** provides the dynamic elasticity.
For GOLIATH, these are the "Grid Lines" upon which we overlay our Momentum and Mean Reversion signals.
