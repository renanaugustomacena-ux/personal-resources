# 08 - Ichimoku Kinko Hyo: Equilibrium at a Glance

**Volume:** 08 of 50
**Strategy Type:** Trend Following / Equilibrium / Support & Resistance
**Risk Profile:** Low Win Rate / High Reward
**Mathematical Basis:** Midpoint Calculation ($\frac{High+Low}{2}$) shifted in time

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context: The 30-Year Project](#2-historical-context-the-30-year-project)
    * 2.1. Goichi Hosoda and the "One Glance" Philosophy
    * 2.2. Why 9, 26, 52? (The Japanese Work Week)
3. [The Five Components & Mathematics](#3-the-five-components--mathematics)
    * 3.1. Tenkan-sen (Conversion Line)
    * 3.2. Kijun-sen (Base Line)
    * 3.3. Senkou Span A (Leading Span A)
    * 3.4. Senkou Span B (Leading Span B)
    * 3.5. Chikou Span (Lagging Span)
4. [The Kumo (Cloud): Time Travel](#4-the-kumo-cloud-time-travel)
    * 4.1. Future Support/Resistance
    * 4.2. The Twist (Reversal Signal)
5. [Hosoda's Three Theories](#5-hosodas-three-theories)
    * 5.1. Time Theory (Cycles: 9, 17, 26)
    * 5.2. Wave Theory (I, V, N, P, Y)
    * 5.3. Price Theory (Projections)
6. [Trading Strategies](#6-trading-strategies)
    * 6.1. The Kumo Breakout (Standard)
    * 6.2. The TK Cross (Tenkan/Kijun)
    * 6.3. The Kijun Bounce (Equilibrium)
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (Pandas with Shift Logic)
    * 7.2. Rust (Optimized Buffer System)
8. [Optimization & Variations](#8-optimization--variations)
    * 8.1. Crypto Settings (20/60/120/30)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Ichimoku Kinko Hyo** (Equilibrium Chart at a Glance) is not just an indicator; it is a comprehensive trading system. Unlike Western indicators that focus on Close prices, Ichimoku uses **Midpoints** ($High+Low/2$) to determine the "Fair Value" of price over time.
Its unique feature is the **Kumo (Cloud)**, which projects support and resistance 26 periods into the future, allowing traders to visualize the market's probable path.

---

# 2. Historical Context: The 30-Year Project

Developed by journalist **Goichi Hosoda** (Ichimoku Sanjin) in the late 1930s, the system was released in 1969 after 30 years of manual backtesting by student assistants.

* **Original Settings:** 9, 26, 52.
* **Origin:** Japan's 6-day trading week (9 = 1.5 weeks, 26 = 1 month, 52 = 2 months).
* **Philosophy:** Markets move in cycles of equilibrium (flat lines) and disequilibrium (trends).

---

# 3. The Five Components & Mathematics

## 3.1. Tenkan-sen (Conversion Line)

$$ \text{Tenkan} = \frac{\text{Highest High}(9) + \text{Lowest Low}(9)}{2} $$

* Fast-moving trend indicator.

## 3.2. Kijun-sen (Base Line)

$$ \text{Kijun} = \frac{\text{Highest High}(26) + \text{Lowest Low}(26)}{2} $$

* The **Standard of Equilibrium**. If price moves too far from Kijun, it snaps back.

## 3.3. Senkou Span A (Leading Span A)

$$ \text{Span A} = \frac{\text{Tenkan} + \text{Kijun}}{2} $$

* **Shifted Forward 26 periods.**
* Represents the average of the fast and slow equilibrium.

## 3.4. Senkou Span B (Leading Span B)

$$ \text{Span B} = \frac{\text{Highest High}(52) + \text{Lowest Low}(52)}{2} $$

* **Shifted Forward 26 periods.**
* The strongest Support/Resistance line in the system.

## 3.5. Chikou Span (Lagging Span)

$$ \text{Chikou} = \text{Current Close, Shifted Backward 26 periods} $$

* Market Memory. Used to confirm breakouts.

---

# 4. The Kumo (Cloud): Time Travel

The area between Span A and Span B is the Kumo.

* **Bullish Cloud:** Span A > Span B.
* **Bearish Cloud:** Span A < Span B.
* **Thickness:** A thick cloud represents specific historical volatility levels that act as concrete walls. A thin cloud indicates a "Twist" point where a trend reversal is probable.

---

# 5. Hosoda's Three Theories

Most traders only use the lines (Graphic Theory). The deeper system involves:

## 5.1. Time Theory

Markets turn on specific number counts.

* **Kihon Suchi (Basic Numbers):** 9, 17, 26.
* **Tai. Suchi (Composite Numbers):** 33, 42, 65, 76.
* *Application:* If a trend has lasted 26 days, look for a turn on Day 27.

## 5.2. Wave Theory

How prices move.

* **I Wave:** Single leg.
* **V Wave:** Up then Down.
* **N Wave:** Up, Down, Up (Trend). The N wave is the foundation of all profitable movement.

## 5.3. Price Theory

Projection targets based on the N Wave ($A \to B \to C \to D$).

* **V Calculation:** $D = B + (B - C)$
* **N Calculation:** $D = C + (B - A)$
* **E Calculation:** $D = B + (B - A)$

---

# 6. Trading Strategies

## 6.1. The Kumo Breakout (Standard)

* **Long:** Price closes above the Cloud.
* **Confirmation:** Chikou Span is above Price (26 days ago).
* **Stop Loss:** Below the Kijun-sen or the Cloud (Span B).

## 6.2. The TK Cross

* **Strong Bullish:** Tenkan crosses above Kijun **Above** the Cloud.
* **Neutral Bullish:** Cross occurs **Inside** the Cloud.
* **Weak Bullish:** Cross occurs **Below** the Cloud.

## 6.3. The Kijun Bounce

In a strong trend, price pulls back to the Kijun-sen (Equilibrium). Place Limit Orders at the Kijun value.

---

# 7. Implementation: Production Grade

## 7.1. Python (Pandas)

```python
import pandas as pd
import numpy as np

class IchimokuStrategy:
    def __init__(self, conv=9, base=26, lead=52, disp=26):
        self.conv = conv
        self.base = base
        self.lead = lead
        self.disp = disp

    def calculate(self, df):
        # 1. Tenkan & Kijun
        high_9 = df['High'].rolling(window=self.conv).max()
        low_9 = df['Low'].rolling(window=self.conv).min()
        df['Tenkan'] = (high_9 + low_9) / 2

        high_26 = df['High'].rolling(window=self.base).max()
        low_26 = df['Low'].rolling(window=self.base).min()
        df['Kijun'] = (high_26 + low_26) / 2

        # 2. Spans (Projected into Future)
        # Note: shift(disp) moves data DOWN (into the future)
        df['SpanA'] = ((df['Tenkan'] + df['Kijun']) / 2).shift(self.disp)
        
        high_52 = df['High'].rolling(window=self.lead).max()
        low_52 = df['Low'].rolling(window=self.lead).min()
        df['SpanB'] = ((high_52 + low_52) / 2).shift(self.disp)

        # 3. Chikou (Shifted Backward)
        # shift(-disp) moves data UP (into the past)
        df['Chikou'] = df['Close'].shift(-self.disp) 
        
        # 4. Cloud Components for Today
        df['Cloud_Top'] = df[['SpanA', 'SpanB']].max(axis=1)
        df['Cloud_Bottom'] = df[['SpanA', 'SpanB']].min(axis=1)
        
        return df
```

## 7.2. Rust (Optimized Buffer System)

```rust
pub struct IchimokuCloud {
    tenkan_period: usize,
    kijun_period: usize,
    senkou_period: usize,
    displacement: usize,
    history: Vec<(f64, f64)>, // (High, Low)
    span_a_buffer: Vec<f64>,
    span_b_buffer: Vec<f64>,
}

impl IchimokuCloud {
    pub fn new(tenkan: usize, kijun: usize, senkou: usize, disp: usize) -> Self {
        Self {
            tenkan_period: tenkan,
            kijun_period: kijun,
            senkou_period: senkou,
            displacement: disp,
            history: Vec::with_capacity(senkou + 1),
            span_a_buffer: Vec::new(),
            span_b_buffer: Vec::new(),
        }
    }

    fn get_midpoint(history: &[(f64, f64)], period: usize) -> f64 {
        let start = if history.len() > period { history.len() - period } else { 0 };
        let slice = &history[start..];
        let max_h = slice.iter().map(|x| x.0).fold(f64::MIN, f64::max);
        let min_l = slice.iter().map(|x| x.1).fold(f64::MAX, f64::min);
        (max_h + min_l) / 2.0
    }

    pub fn update(&mut self, high: f64, low: f64) -> Option<(f64, f64, f64, f64)> {
        self.history.push((high, low));
        
        if self.history.len() < self.tenkan_period { return None; }
        
        let tenkan = Self::get_midpoint(&self.history, self.tenkan_period);
        
        if self.history.len() < self.kijun_period { return None; }
        let kijun = Self::get_midpoint(&self.history, self.kijun_period);
        
        // Calculate Spans for Future projection
        let span_a_val = (tenkan + kijun) / 2.0;
        self.span_a_buffer.push(span_a_val);
        
        if self.history.len() < self.senkou_period { return None; }
        let span_b_val = Self::get_midpoint(&self.history, self.senkou_period);
        self.span_b_buffer.push(span_b_val);
        
        // Retrieve Delayed Project (The Cloud for Today)
        let delayed_idx = if self.span_a_buffer.len() > self.displacement {
            self.span_a_buffer.len() - self.displacement - 1
        } else {
             // Handle startup or lookahead
             return Some((tenkan, kijun, span_a_val, span_b_val)); 
        };
        
        Some((
            tenkan,
            kijun,
            self.span_a_buffer[delayed_idx], 
            self.span_b_buffer[delayed_idx]
        ))
    }
}
```

---

# 8. Optimization & Variations

## 8.1. Crypto Settings

Since Crypto trades 24/7, the "work week" logic fails.
Popular Crypto Settings: **20 / 60 / 120 / 30**.

* 20 = ~3 weeks.
* 60 = ~2 months.
* 120 = ~4 months.
* 30 = Displacement.

---

# 9. Conclusion

Ichimoku Kinko Hyo is the only system that tells you the **Trend Direction**, **Momentum**, **Support/Resistance**, and **Timing** in a single glance. By combining the graphic nature of the Cloud with the cyclical nature of Time Theory, it provides a complete framework for discretionary and algorithmic trading alike.
