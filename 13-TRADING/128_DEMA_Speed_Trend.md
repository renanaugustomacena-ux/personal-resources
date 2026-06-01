# 128 - DEMA Speed Trend

**Volume:** 128 of 100
**Strategy Type:** Trend Following (Low Lag)
**Risk Profile:** High (Aggressive)
**Mathematical Basis:** $2 \times EMA - EMA(EMA)$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Theory: Lag Cancellation](#2-theory-lag-cancellation)
3. [The Strategy](#3-the-strategy)
4. [Implementation](#4-implementation)

---

## 1. Executive Summary

**Double Exponential Moving Average (DEMA)** reduces the lag of a standard EMA by subtracting the difference between the EMA and the "double EMA" (EMA of EMA). This results in a moving average that hugs price much closer, reacting about **twice as fast** as a standard EMA.

* **Tradeoff:** Less lag = More noise. DEMA can overshoot in choppy markets.
* **Role:** Early warning system. GOLIATH uses DEMA to trigger "Fast Lane" entries before the safer SMA/EMA confirmation arrives.

---

## 2. Theory: Lag Cancellation

Standard EMA has lag $L$.
Double smoothed EMA (EMA of EMA) has lag $2L$.
The error (lag) is roughly $EMA - EMA(EMA)$.
Adding this error back to the EMA compensates for the lag:
$$DEMA = EMA + [EMA - EMA(EMA)] = 2 \times EMA - EMA(EMA)$$

---

## 3. The Strategy: "The Fast Lane"

**Trigger:** Asymmetric entry/exit. Enter on the Fast Signal (DEMA), Exit on the Slow Signal (EMA).

1. **Indicators:** DEMA(20), EMA(20).
2. **Long Entry:**
    * DEMA(20) crosses **above** DEMA(20) from 3 bars ago (Slope Check).
    * Price > DEMA(20).
    * *Filter:* Adx > 20 (Trending).
3. **Confirmation:** Expect EMA(20) to cross up shortly after.
4. **Exit (Trailing):**
    * Use **EMA(20)** as the stop, NOT DEMA.
    * Logic: DEMA is volatile and will shake you out. EMA is stable.
    * Once in, ride the EMA.
5. **Hard Stop:** Close below EMA(20) - 1 ATR.

---

## 4. Implementation

### 4.1 Python (Vectorized)

```python
import pandas as pd

def dema(close: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Double Exponential Moving Average.
    Formula: 2*EMA - EMA(EMA)
    """
    ema1 = close.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    return 2 * ema1 - ema2

def dema_strategy_signal(close: pd.Series, period: int = 20) -> pd.DataFrame:
    """
    Generate DEMA Fast Lane signals.
    """
    d = dema(close, period)
    e = close.ewm(span=period, adjust=False).mean()
    
    signals = pd.DataFrame(index=close.index)
    signals['dema'] = d
    signals['ema'] = e
    
    # Entry: DEMA Rising AND Price > DEMA
    # Exit: Close < EMA
    
    signals['entry_long'] = (d > d.shift(1)) & (close > d)
    signals['exit_long'] = close < e
    
    return signals
```

### 4.2 Rust (Streaming)

```rust
pub struct DEMA {
    alpha: f64,
    ema1: f64,
    ema2: f64,
    initialized: bool,
}

impl DEMA {
    pub fn new(period: usize) -> Self {
        Self {
            alpha: 2.0 / (period as f64 + 1.0),
            ema1: 0.0,
            ema2: 0.0,
            initialized: false,
        }
    }

    pub fn update(&mut self, price: f64) -> f64 {
        if !self.initialized {
            self.ema1 = price;
            self.ema2 = price;
            self.initialized = true;
            return price;
        }

        self.ema1 = self.alpha * price + (1.0 - self.alpha) * self.ema1;
        self.ema2 = self.alpha * self.ema1 + (1.0 - self.alpha) * self.ema2;
        
        2.0 * self.ema1 - self.ema2
    }
}
```
