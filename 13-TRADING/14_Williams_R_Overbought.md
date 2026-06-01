# 14 - Williams %R: The Range Rider

**Volume:** 14 of 50
**Strategy Type:** Mean Reversion / Momentum Timing
**Risk Profile:** Medium Win Rate / Low Drawdown
**Mathematical Basis:** Relative Location ($C$) within Range ($H-L$) - Inverted

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context: The 1987 Record](#2-historical-context-the-1987-record)
3. [Mathematical Foundations](#3-mathematical-foundations)
    * 3.1. The Formula: $\%R = \frac{Highest High_n - Close}{Highest High_n - Lowest Low_n} \times -100$
    * 3.2. Relationship to Stochastic (Roughly $\%R = \%K - 100$)
4. [Trading Signals](#4-trading-signals)
    * 4.1. The Standard Reversion (Escape from Extremes)
    * 4.2. Failure Swings (The Money Signal)
    * 4.3. The "Blast Off" (Momentum Burst)
5. [Strategies](#5-strategies)
    * 5.1. The "Volatility Breakout" (Inside Day)
    * 5.2. Trend Filtered Entries (SMA 50)
6. [Microstructure & HFT](#6-microstructure--hft)
    * 6.1. Liquidity Exhaustion at -100
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (Pandas)
    * 7.2. Rust (Optimized Sliding Window)
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Williams %R** (Percent Range), developed by Larry Williams, is a momentum indicator that moves between 0 and -100.

* **0:** Close is at the High of the range (Max Bullish).
* **-100:** Close is at the Low of the range (Max Bearish).
* **-20:** Overbought Threshold.
* **-80:** Oversold Threshold.

Unlike Stochastic, it has **No Smoothing**. It is the raw nerve ending of the market, making it faster but noisier.

---

# 2. Historical Context: The 1987 Record

Larry Williams turned $10,000 into $1.1 million in 12 months during the 1987 World Cup Championship of Futures Trading. A key part of his arsenal was using %R to identify identifying "exhaustion" points within trends. He proved that buying when the market looks terrible (Oversold) and selling when it looks perfect (Overbought) is the only way to capture the full swing.

---

# 3. Mathematical Foundations

## 3.1. The Formula

$$ \%R = \frac{\text{Highest High}_N - \text{Close}}{\text{Highest High}_N - \text{Lowest Low}_N} \times -100 $$

* It measures where the Close is relative to the **High**.
* Stochastic measures where the Close is relative to the **Low**.
* They are mathematically mirror images.

## 3.2. Interpretation

If High(14) = 110, Low(14) = 90, Close = 90.
Numerator = 110 - 90 = 20. Denom = 20. Result = -100 (Oversold).

---

# 4. Trading Signals

## 4.1. Standard Reversion

1. **Wait:** %R < -80 (Oversold).
2. **Trigger:** Price closes back **above -80**.
3. **Logic:** The knife has stopped falling and bounced.

## 4.2. Failure Swings

1. **Peak 1:** %R hits -5 (Overbought).
2. **Pullback:** %R drops to -40.
3. **Peak 2:** Price makes Higher High, but %R only hits -15.
4. **Signal:** Short. Momentum is diverging from Price.

## 4.3. The "Blast Off"

If %R > -20 for 5 consecutive periods, the market is not Overbought; it is **Locked Limit Up**.

* **Action:** Switch to Trend Following. Buy Dips. Do not Short.

---

# 5. Strategies

## 5.1. The Volatility Breakout

1. **Setup:** "Inside Day" (High < PrevHigh, Low > PrevLow). Volatility is compressing.
2. **Trigger:** %R moves from -50 to > -20.
3. **Entry:** Buy Stop at the High of the Inside Day.

## 5.2. Trend Filter (SMA 50)

* **Rule:** Only take Buy Signals (%R < -80) if Price > SMA 50.
* **Rule:** Only take Sell Signals (%R > -20) if Price < SMA 50.
* *Result:* Win rate increases from ~45% to ~60%.

---

# 6. Microstructure & HFT

In HFT, algorithms use Williams %R on tick data to detect **Liquidity Exhaustion**.
When %R hits -100 on a 10-tick chart, it means every recent trade hit the Bid. If the Bid holds (Iceberg order), %R snaps back. This "Snap Back" is a mean-reversion scalp signal.

---

# 7. Implementation: Production Grade

## 7.1. Python (Pandas)

```python
import pandas as pd
import numpy as np

class WilliamsRStrategy:
    def __init__(self, period=14):
        self.period = period

    def calculate(self, df):
        # 1. Rolling Extremes
        high_max = df['High'].rolling(window=self.period).max()
        low_min = df['Low'].rolling(window=self.period).min()
        
        # 2. Formula
        numerator = high_max - df['Close']
        denominator = high_max - low_min
        
        # Avoid zero division
        denominator = denominator.replace(0, np.nan) 
        
        df['WillR'] = (numerator / denominator) * -100
        
        return df

    def generate_signals(self, df):
        df = self.calculate(df)
        df['Signal'] = 0
        
        # Trend Filter
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        
        # Buy: Cross Up -80 AND Trend is Up
        cross_up = (df['WillR'] > -80) & (df['WillR'].shift(1) < -80)
        trend_up = df['Close'] > df['SMA50']
        
        df.loc[cross_up & trend_up, 'Signal'] = 1
        
        # Sell: Cross Down -20 AND Trend is Down
        cross_down = (df['WillR'] < -20) & (df['WillR'].shift(1) > -20)
        trend_down = df['Close'] < df['SMA50']
        
        df.loc[cross_down & trend_down, 'Signal'] = -1
        
        return df
```

## 7.2. Rust (Optimized Sliding Window)

```rust
use std::collections::VecDeque;

pub struct WilliamsR {
    period: usize,
    high_buffer: VecDeque<f64>,
    low_buffer: VecDeque<f64>,
}

impl WilliamsR {
    pub fn new(period: usize) -> Self {
        Self {
            period,
            high_buffer: VecDeque::with_capacity(period),
            low_buffer: VecDeque::with_capacity(period),
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Option<f64> {
        // Maintain sliding window
        if self.high_buffer.len() >= self.period { self.high_buffer.pop_front(); }
        if self.low_buffer.len() >= self.period { self.low_buffer.pop_front(); }
        
        self.high_buffer.push_back(high);
        self.low_buffer.push_back(low);
        
        if self.high_buffer.len() < self.period { return None; }
        
        // Find extremes (O(N) for clarity, use Deque for O(1))
        let highest = self.high_buffer.iter().fold(f64::MIN, |a, &b| a.max(b));
        let lowest = self.low_buffer.iter().fold(f64::MAX, |a, &b| a.min(b));
        
        let range = highest - lowest;
        
        if range == 0.0 {
            return Some(-50.0); // Flatline
        }
        
        let r = (highest - close) / range * -100.0;
        
        Some(r)
    }
}
```

---

# 8. Risk Management

## 8.1. The Momentum Burst

If %R hits -100, do **NOT** buy immediately. Price can go lower, making new lows while %R stays pinned at -100.
**Rule:** Always wait for the "Hook" back up to -80. This confirms buyers have stepped in.

---

# 9. Conclusion

Williams %R is a tactical weapon for timing entries.
Strategy:

1. Use **ADX/SMA** to determine the Trend.
2. Use **Williams %R** to time the pullback.
3. Buy when the indicator becomes Oversold in an Uptrend.

It is "buying the dip" quantified.
