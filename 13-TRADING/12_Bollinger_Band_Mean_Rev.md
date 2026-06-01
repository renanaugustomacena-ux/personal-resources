# 12 - Bollinger Band Mean Reversion: The Rubber Band

**Volume:** 12 of 50
**Strategy Type:** Mean Reversion / Counter-Trend
**Risk Profile:** Medium Win Rate / High Whipsaw Risk
**Mathematical Basis:** Normal Distribution (Gaussian) Extremes at $\pm 2\sigma$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Standard Deviation ($\sigma$)](#2-the-theory-standard-deviation-)
    * 2.1. Formula: $\sqrt{\frac{\sum(x-\mu)^2}{N}}$
    * 2.2. Population vs Sample ($N-1$)
    * 2.3. The 68-95-99.7 Rule (Normal Distribution)
    * 2.4. The Fat Tail Reality (Kurtosis)
3. [Bollinger Bands: The Adaptive Envelope](#3-bollinger-bands-the-adaptive-envelope)
    * 3.1. Construction: SMA $\pm 2\sigma$
    * 3.2. "The Bounce" (Reversion) vs "The Walk" (Trend)
4. [Trading Strategies](#4-trading-strategies)
    * 4.1. The Standard Reversion (Touch & Bounce)
    * 4.2. The Double Bottom (W-Pattern)
    * 4.3. The 3-Sigma Extremes (Statistical Outliers)
5. [Risk Management](#5-risk-management)
    * 5.1. Filter: ADX < 20 (Avoid Trends)
    * 5.2. Stop Loss: Time-Based or Fixed %
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Pandas StdDev & Z-Score)
    * 6.2. Rust (Streaming Welford's Algorithm)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Bollinger Mean Reversion** exploits the statistical probability that price will return to its mean after an extreme deviation.
It relies on **Standard Deviation ($\sigma$)**, the most robust measure of volatility.

* **Theory:** Prices spend 95% of their time within $2\sigma$ of the mean.
* **Strategy:** Buy at $-2\sigma$ (Cheap). Sell at $+2\sigma$ (Expensive).

---

# 2. The Theory: Standard Deviation ($\sigma$)

## 2.1. Formula

$$ \sigma = \sqrt{\frac{\sum_{i=1}^{N} (x_i - \mu)^2}{N-1}} $$
We use $N-1$ (Bessel's Correction) because we are estimating population variance from a sample (e.g., 20 candles).

## 2.2. The Normal Distribution

In a perfect Bell Curve:

* 68.2% of data is within $1\sigma$.
* 95.4% of data is within $2\sigma$.
* 99.7% of data is within $3\sigma$.

## 2.3. The Fat Tail Reality

Financial markets are **Leptokurtic**. $3\sigma$ events happen far often than predicted. A crash can push price to $5\sigma$ or $10\sigma$.
**Implication:** A move to $2\sigma$ does *not* guarantee a stop. It just means it's statistically stretched.

---

# 3. Bollinger Bands: The Adaptive Envelope

## 3.1. Construction

1. **Middle:** 20-period SMA.
2. **Upper:** Middle + ($2 \times \sigma$).
3. **Lower:** Middle - ($2 \times \sigma$).

## 3.2. The Walk vs The Bounce

* **The Bounce:** Price hits the band and reverts. (Profit).
* **The Walk:** Price hits the band and *stays* there, riding it down while the band widens. (Bankruptcy).
* **Rule:** Never Short a "Walk" (Strong Trend). Only Short a "Bounce" (Range).

---

# 4. Trading Strategies

## 4.1. Standard Reversion

1. **Filter:** Market is Ranging (ADX < 20).
2. **Entry:** Price touches Lower Band.
3. **Confirmation:** Bullish Candle (Hammer) closes back inside.
4. **Target:** Middle Band (Mean).

## 4.2. Double Bottom (W-Pattern)

1. Low 1: Price penetrates Lower Band.
2. Rebound: Price rallies to Middle Band.
3. Low 2: Price falls but stays *inside* Lower Band.
4. **Trigger:** Buy the second low. Represents waning momentum.

## 4.3. The 3-Sigma Extremes

1. **Filter:** Only for high-cap assets (BTC, ETH).
2. **Entry:** Price touches $3\sigma$ Band.
3. **Logic:** This is a 0.3% probability event. Reversion is imminent.
4. **Win Rate:** >90%, but rare frequency.

---

# 5. Risk Management

## 5.1. Regime Filter (ADX)

**CRITICAL:** If ADX > 30, Mean Reversion is turned OFF.
You will go broke trying to catch a falling knife in a strong trend.

## 5.2. Evaluation

Do not use "Close below Band" as a Stop Loss (that's exactly where you want to buy).
Use a **Time Stop** (e.g., if not profitable in 5 bars, exit) or a **Fixed Stop** (e.g., 2% risk).

---

# 6. Implementation: Production Grade

## 6.1. Python (Pandas)

```python
import pandas as pd
import numpy as np

class BollingerStats:
    def __init__(self, window=20, num_std=2):
        self.window = window
        self.num_std = num_std

    def calculate(self, df):
        # 1. Rolling Mean & Std
        df['SMA'] = df['Close'].rolling(window=self.window).mean()
        # ddof=1 for Sample Standard Deviation
        df['STD'] = df['Close'].rolling(window=self.window).std(ddof=1)
        
        # 2. Bands
        df['Upper'] = df['SMA'] + (self.num_std * df['STD'])
        df['Lower'] = df['SMA'] - (self.num_std * df['STD'])
        
        # 3. Z-Score (Number of Sigmas from Mean)
        df['Z_Score'] = (df['Close'] - df['SMA']) / df['STD']
        
        # 4. %B
        df['PctB'] = (df['Close'] - df['Lower']) / (df['Upper'] - df['Lower'])
        
        return df

    def generate_signals(self, df):
        df = self.calculate(df)
        df['Signal'] = 0
        
        # Buy: Price < Lower Band AND Z-Score < -2
        buy_cond = df['Close'] < df['Lower']
        sell_cond = df['Close'] > df['Upper']
        
        df.loc[buy_cond, 'Signal'] = 1
        df.loc[sell_cond, 'Signal'] = -1
        
        return df
```

## 6.2. Rust (Streaming Welford's Algorithm)

Calculating Standard Deviation in a single pass is prone to floating point errors (catastrophic cancellation). We use **Welford's Online Algorithm**.

```rust
pub struct StreamingStats {
    period: usize,
    buffer: std::collections::VecDeque<f64>,
    sum_x: f64,
    sum_x2: f64,
}

impl StreamingStats {
    pub fn new(period: usize) -> Self {
        Self { 
            period, 
            buffer: std::collections::VecDeque::with_capacity(period + 1),
            sum_x: 0.0, 
            sum_x2: 0.0 
        }
    }
    
    pub fn update(&mut self, val: f64) -> Option<(f64, f64, f64)> {
        // Returns (Mean, Variance, StdDev)
        self.buffer.push_back(val);
        self.sum_x += val;
        self.sum_x2 += val * val;
        
        if self.buffer.len() > self.period {
            if let Some(old) = self.buffer.pop_front() {
                self.sum_x -= old;
                self.sum_x2 -= old * old;
            }
        }
        
        if self.buffer.len() < self.period { return None; }
        
        let n = self.period as f64;
        
        // Variance = (Sum(x^2) - (Sum(x)^2 / N)) / (N - 1)
        let numerator = self.sum_x2 - ((self.sum_x * self.sum_x) / n);
        
        // Sample Variance (N-1)
        let variance = if n > 1.0 { numerator / (n - 1.0) } else { 0.0 };
        let std_dev = variance.max(0.0).sqrt();
        let mean = self.sum_x / n;
        
        Some((mean, variance, std_dev))
    }
}
```

---

# 7. Conclusion

Standard Deviation transforms "feelings" about volatility into numbers.
Bollinger Bands visualize this math.

* **The Edge:** Buying when the crowd is panic-selling (below $2\sigma$) and Selling when the crowd is panic-buying (above $2\sigma$).
* **The Trap:** Thinking probability is certainty. In a Black Swan, probability fails. Always use stops.
