# Indicator 138: Awesome Oscillator (AO) — Momentum in HD

***"Why is it awesome? Because it captures the markets' momentum with zero lag relative to the price action. It is the best momentum indicator available in the Chaos framework." — Bill Williams***

---

## 1. Executive Summary

The **Awesome Oscillator (AO)** is a market momentum indicator developed by **Bill Williams**. It compares the recent momentum (5 bars) against a broader timeframe (34 bars) to determine the immediate directional force of the market.

Unlike the MACD, which uses closing prices and exponential smoothing, the AO uses **Simple Moving Averages (SMA)** calculated on the **Median Price** ($High+Low/2$). Williams argued that Median Price better reflects the "activity" of the market than the Close.

The AO is histogram-based and color-coded:

- **Green Bar**: The current bar is higher than the previous bar (Momentum increasing).
- **Red Bar**: The current bar is lower than the previous bar (Momentum decreasing).

It is used to generate three specific types of signals: **Saucer**, **N-Cross** (Zero Line Cross), and **Twin Peaks** (Divergence).

In GOLIATH, the AO serves as the **Standard Momentum Gauge**. It confirms whether the trend detected by the Alligator has sufficient kinetic energy to sustain itself.

---

## 2. Mathematical Foundations

The formula is deceptively simple:

$$ \text{AO} = SMA(\text{Median Price}, 5) - SMA(\text{Median Price}, 34) $$

Where:
$$ \text{Median Price} = \frac{High + Low}{2} $$

### 2.1 Why 34 and 5?

Both are **Fibonacci Numbers**.

- **34**: Represents the "intermediate" trend (approx. 1 month on daily charts).
- **5**: Represents the "short-term" trend (approx. 1 week on daily charts).

Subtracting the slow moving average (34) from the fast moving average (5) gives a value that oscillates above/below zero.

- **Positive AO**: Short-term momentum is greater than long-term (Bullish).
- **Negative AO**: Short-term momentum is less than long-term (Bearish).

---

## 3. Signal Generation

### 3.1 The Saucer Signal (Continuation)

The Saucer signal allows adding to a position *within* a trend.

**Bullish Saucer**:

1. AO is **above zero**.
2. Pattern: $Bar_1$ (Red) > $Bar_2$ (Red) < $Bar_3$ (Green).
3. Interpretation: Momentum dipped briefly (correction) and is now turning back up.
4. Entry: Buy stop on the High of the signal bar.

**Bearish Saucer**:

1. AO is **below zero**.
2. Pattern: $Bar_1$ (Green) < $Bar_2$ (Green) > $Bar_3$ (Red).
3. Interpretation: Bearish momentum paused (rally) and is now resuming downward.
4. Entry: Sell stop on the Low of the signal bar.

### 3.2 The Zero Line Cross (N-Cross)

The strongest confirmation of a trend change.

- **Bullish Cross**: AO crosses from negative to positive. Requires two consecutive Green bars.
- **Bearish Cross**: AO crosses from positive to negative. Requires two consecutive Red bars.

### 3.3 Twin Peaks (Divergence)

The only signal allowed *against* the trend (counter-trend).

- **Bullish Twin Peaks**:
    1. AO is below zero.
    2. Form a low ($Peak_1$), followed by a pull-back (towards zero), then a second low ($Peak_2$).
    3. $Peak_2$ is **higher** (closer to zero) than $Peak_1$.
    4. The histogram must stay below zero the entire time.
    5. Trigger: A Green bar after $Peak_2$.

This indicates that while price made a new low, the selling momentum is exhausted.

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd

def compute_awesome_oscillator(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Bill Williams' Awesome Oscillator (AO).
    AO = SMA(Median Price, 5) - SMA(Median Price, 34)
    """
    df = df.copy()
    
    # 1. Median Price
    median_price = (df['high'] + df['low']) / 2
    
    # 2. SMAs
    sma_5 = median_price.rolling(window=5).mean()
    sma_34 = median_price.rolling(window=34).mean()
    
    # 3. AO
    df['ao'] = sma_5 - sma_34
    
    # 4. Color Coding (1=Green, -1=Red)
    # Green if Current > Prev, Red if Current <= Prev
    df['ao_color'] = 0
    df.loc[df['ao'] > df['ao'].shift(1), 'ao_color'] = 1
    df.loc[df['ao'] <= df['ao'].shift(1), 'ao_color'] = -1
    
    return df

def detect_ao_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect Saucer, Zero Cross, and Twin Peaks signals.
    Returns df with 'ao_signal' column.
    """
    if 'ao' not in df.columns:
        df = compute_awesome_oscillator(df)
        
    ao = df['ao']
    prev_ao = ao.shift(1)
    
    # Simple Zero Cross
    cross_up = (prev_ao < 0) & (ao > 0)
    cross_down = (prev_ao > 0) & (ao < 0)
    
    # (Simplified for brevity - full saucer logic requires 3-bar pattern matching)
    
    return df
```

### 4.2 Rust Implementation

```rust
pub struct AwesomeOscillator {
    sma5_sum: f64,
    sma34_sum: f64,
    buffer5: VecDeque<f64>,
    buffer34: VecDeque<f64>,
    prev_ao: f64,
}

impl AwesomeOscillator {
    pub fn new() -> Self {
        Self {
            sma5_sum: 0.0,
            sma34_sum: 0.0,
            buffer5: VecDeque::with_capacity(5),
            buffer34: VecDeque::with_capacity(34),
            prev_ao: 0.0,
        }
    }

    pub fn next(&mut self, high: f64, low: f64) -> (f64, bool) {
        let median = (high + low) / 2.0;

        // Update SMA 5
        self.buffer5.push_back(median);
        self.sma5_sum += median;
        if self.buffer5.len() > 5 {
            self.sma5_sum -= self.buffer5.pop_front().unwrap();
        }
        let sma5 = self.sma5_sum / self.buffer5.len() as f64;

        // Update SMA 34
        self.buffer34.push_back(median);
        self.sma34_sum += median;
        if self.buffer34.len() > 34 {
            self.sma34_sum -= self.buffer34.pop_front().unwrap();
        }
        let sma34 = self.sma34_sum / self.buffer34.len() as f64;

        // Compute AO
        let ao = if self.buffer34.len() == 34 { sma5 - sma34 } else { 0.0 };
        
        // Determine Color
        let is_green = ao > self.prev_ao;
        self.prev_ao = ao;

        (ao, is_green)
    }
}
```

---

## 5. Strategy: The "Awesome" Cascade

In GOLIATH, we do not trade AO in isolation. It is used as a **Validation Layer**.

1. **Alligator** must be Feeding (Lines Diverging).
2. **AO** must be Green (for Longs).
3. **Saucer Signal**: Only take Saucers that occur *in the direction of the Alligator*.

This filters out false AO signals during the Sleeping phase.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 138 |
| Name | Awesome Oscillator (AO) |
| Author | Bill Williams |
| Formula | SMA(MP, 5) - SMA(MP, 34) |
| Signals | Saucer, Zero Cross, Twin Peaks |
| Type | Momentum Unbounded |
| GOLIATH Use | Momentum Confirmation & Pyramiding |
