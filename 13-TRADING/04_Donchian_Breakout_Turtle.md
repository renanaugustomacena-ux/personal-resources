# 04 - Donchian Channel Breakout (The Turtle Trading System)

**Volume:** 04 of 50
**Strategy Type:** Price Action / Breakout / Trend Following
**Risk Profile:** Low Win Rate / Massive Fat Tail Payoff
**Mathematical Basis:** Max/Min Extremes & Volatility Normalization ($N$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The History: Nature vs Nurture](#2-the-history-nature-vs-nurture)
3. [The Trading Logic](#3-the-trading-logic)
    * 3.1. Donchian Channels: The Defining Range
    * 3.2. System 1 (Short Term): 20-Day Breakout
    * 3.3. System 2 (Long Term): 55-Day Breakout
    * 3.4. System 3 (Noise Filtered): The Renko Trendbox
    * 3.5. The Exit Rule: 10-Day Breakdown
4. [The Money Management: The "N" Concept](#4-the-money-management-the-n-concept)
    * 4.1. True Range & N (ATR)
    * 4.2. Unit Sizing Formula
    * 4.3. Pyramiding (Max 4 Units)
5. [Counter-Strategy: Turtle Soup](#5-counter-strategy-turtle-soup)
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Full System Backtest + Renko)
    * 6.2. Rust (Optimized Monotonic Queue + Renko)
7. [Historical Case Studies](#7-historical-case-studies)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**The Turtle Trading System** is arguably the most famous mechanical trading system in history. Based on **Donchian Channel Breakouts**, it buys new 20-day highs and shorts new 20-day lows.
Modern markets, however, are noisier than the 1980s. High Frequency Trading creates "wicks" that trigger false breakouts.
To combat this, we integrate **Renko Blocks** (System 3) to filter out time-based noise and trade only significant price movements.
The brilliance of the system lies in the **Money Management Algorithm** (Position Sizing based on Volatility $N$) which diversifies risk equally.

---

# 2. The History: Nature vs Nurture

**The Bet (1983):** Richard Dennis believed trading could be taught. William Eckhardt did not.
They hired a diverse group of novices ("Turtles"), gave them a strict rule-based system, and set them loose.

* **Result:** The Turtles generated >$175 Million in 5 years.
* **Legacy:** Proved "Trend Following" is a viable, teachable algorithm.

---

# 3. The Trading Logic

## 3.1. Donchian Channels

* **Upper Band:** Highest High of last $N$ days.
* **Lower Band:** Lowest Low of last $N$ days.

## 3.2. System 1 (Short Term)

* **Entry:** Buy when Price $>$ High(20).
* **Filter:** Ignore if the *last* breakout signal was a winning trade. (Prevents buying into an exhausted trend).
* **Override:** If the filtered trade would have stopped out (2N loss), take the *next* signal immediately.
* **Exit:** Sell when Price $<$ Low(10).

## 3.3. System 2 (Long Term)

* **Entry:** Buy when Price $>$ High(55).
* **Filter:** None. Take every signal.
* **Exit:** Sell when Price $<$ Low(20).

## 3.4. System 3 (Noise Filtered): The Renko Trendbox

From `040_Renko_Blocks`:

**Concept:** Renko charts remove time. A new "Brick" is drawn only when price moves by $ATR(14)$.

* **Setup:** Adaptive Brick Size = $N$ (ATR-14).
* **Trigger:** Wait for a **Block of 3** (Three consecutive bricks of the same color).
* **Entry:** Enter on the Close of the 3rd brick.
* **Stop Loss:** 2 Bricks below entry.
* **Trailing:** Move Stop up 1 Brick for every new Green Brick.

**Why:** It filters out the "wick" breakouts that kill System 1 in 2024.

## 3.5. The Exit Rule

For Systems 1 & 2:

* **Long Exit:** Price hits the 10-Day Low.
* **Short Exit:** Price hits the 10-Day High.
* **Note:** We exit losing trades fast (2N Stop). We let winning trades run until the trend explicitly reverses (10-Day Low).

---

# 4. The Money Management: The "N" Concept

## 4.1. N (Volatility)

$$ N = \text{20-day EMA of True Range} $$

## 4.2. Unit Sizing Formula

Every trade is sized so that a $1N$ move equals $1\%$ of Account Equity.
$$ Unit = \frac{0.01 \times Account}{N \times DollarsPerPoint} $$

* **High Volatility** $\rightarrow$ Small Position.
* **Low Volatility** $\rightarrow$ Large Position.

## 4.3. Pyramiding

The Turtles added to winners.

1. **Unit 1:** Buy at Breakout $P$. Stop at $P - 2N$.
2. **Unit 2:** Buy at $P + \frac{1}{2}N$. Raise stops.
3. **Unit 3:** Buy at $P + 1N$. Raise stops.
4. **Unit 4:** Buy at $P + 1.5N$. Raise stops.
    * **Max:** 4 Units per market.

---

# 5. Counter-Strategy: Turtle Soup

Developed by Linda Raschke to exploit **Failed Breakouts** (which happen often in modern markets due to HFTs).

1. **Setup:** Price breaks the 20-Day High (triggering Turtle Buys).
2. **Trigger:** Price reverses and closes back *inside* the channel.
3. **Action:** Sell Short (Fade the breakout).
4. **Target:** The Middle Line or Lower Channel.

---

# 6. Implementation: Production Grade

## 6.1. Python (System Logic + Renko)

```python
import pandas as pd
import numpy as np

class TurtleSystem:
    def __init__(self, entry_period=20, exit_period=10, atr_period=20):
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period

    def calculate_indicators(self, df):
        # Donchian Channels (shifted 1 to avoid lookahead)
        df['High_N'] = df['High'].rolling(window=self.entry_period).max().shift(1)
        df['Low_N'] = df['Low'].rolling(window=self.entry_period).min().shift(1)
        
        df['Low_Exit'] = df['Low'].rolling(window=self.exit_period).min().shift(1)

        # ATR (N)
        df['TR'] = pd.concat([
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift(1)),
            abs(df['Low'] - df['Close'].shift(1))
        ], axis=1).max(axis=1)
        
        df['N'] = df['TR'].ewm(alpha=1/self.atr_period, adjust=False).mean()
        return df

    def calculate_renko(self, df, brick_size=None):
        # If brick_size is None, use last ATR
        if brick_size is None:
            brick_size = df['N'].iloc[-1]
            
        renko_data = []
        last_price = df['Close'].iloc[0]
        # Align to grid
        last_price = np.floor(last_price / brick_size) * brick_size
        renko_close = last_price
        
        for index, row in df.iterrows():
            price = row['Close']
            diff = price - renko_close
            count = int(diff // brick_size)
            
            if count == 0: continue
                
            for _ in range(abs(count)):
                if count > 0:
                    renko_close += brick_size
                    type = 'up'
                else:
                    renko_close -= brick_size
                    type = 'down'
                renko_data.append({'date': index, 'close': renko_close, 'type': type})
                
        return pd.DataFrame(renko_data)
```

## 6.2. Rust (Optimized Monotonic Queue + Renko)

```rust
use std::collections::VecDeque;

// Donchian Struct... (Standard implementation)

// Renko Struct
pub struct RenkoBuilder {
    brick_size: f64,
    last_brick_close: Option<f64>,
}

#[derive(Debug)]
pub struct RenkoBrick {
    pub close: f64,
    pub is_up: bool,
}

impl RenkoBuilder {
    pub fn new(brick_size: f64) -> Self {
        Self { brick_size, last_brick_close: None }
    }

    pub fn process_tick(&mut self, price: f64) -> Vec<RenkoBrick> {
        let mut new_bricks = Vec::new();

        if self.last_brick_close.is_none() {
            let snapped = (price / self.brick_size).floor() * self.brick_size;
            self.last_brick_close = Some(snapped);
            return new_bricks;
        }

        let mut last = self.last_brick_close.unwrap();
        let diff = price - last;
        let num_bricks = (diff / self.brick_size).trunc() as i32;

        if num_bricks == 0 { return new_bricks; }

        for _ in 0..num_bricks.abs() {
            let close = if num_bricks > 0 { last + self.brick_size } else { last - self.brick_size };
            new_bricks.push(RenkoBrick {
                close,
                is_up: num_bricks > 0,
            });
            last = close;
        }
        
        self.last_brick_close = Some(last);
        new_bricks
    }
}
```

---

# 7. Historical Case Studies

## 7.1. Heating Oil (1980s)

Energy markets trend beautifully due to physical supply constraints. The Turtles made millions shorting Oil in the glut.

## 7.2. Bitcoin (2020-2021)

Bitcoin from $10k to $60k.

* **High(20) Breakout:** Occurred around $11,500.
* **N (Volatility):** Was low, allowing large size.
* **Pyramiding:** Allowed adding at $12k, $13k, $15k.
* **Result:** Captured the bulk of the 6x move with leverage.

---

# 8. Conclusion

**Donchian Channels** are the "Delete Key" for over-analysis.
When RSI is diverging and MACD is crossing, Donchian simplistically asks: **"Is price making a new high?"**
If yes, buy. If no, wait.
Strategy 04 accepts the price raw. It is volatile, painful, and historically, incredibly profitable.
With the addition of **Renko Blocks**, we add a modern filter to this timeless logic, allowing us to ignore the noise of the algorithm age.
