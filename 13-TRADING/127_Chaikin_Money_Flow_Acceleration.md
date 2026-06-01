# 127 - Chaikin Money Flow Acceleration (CHO)

**Volume:** 127 of 100
**Strategy Type:** Volume Momentum / Acceleration
**Risk Profile:** Medium (Leading Indicator)
**Mathematical Basis:** EMA(ADL, 3) - EMA(ADL, 10)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Theory: The Accelerometer](#2-theory-the-accelerometer)
3. [The Strategy](#3-the-strategy)
4. [Implementation](#4-implementation)

---

## 1. Executive Summary

**The Chaikin Oscillator (CHO)** is the MACD of the Accumulation/Distribution Line (ADL). While ADL measures *position* (net flow out/in), CHO measures *acceleration* (rate of change of flow).

* **Positive/Rising CHO:** Accelerating accumulation.
* **Negative/Falling CHO:** Accelerating distribution.
* **The Edge:** Acceleration precedes velocity (CMF), which precedes price action. CHO is often the first indicator to turn at major bottoms.

---

## 2. Theory: The Accelerometer

The calculation stack:

1. **Close Location Value (CLV):** Normalized location of close within range (-1 to +1).
2. **Money Flow Volume (MFV):** CLV × Volume.
3. **ADL:** Cumulative sum of MFV.
4. **CHO:** EMA(3) of ADL - EMA(10) of ADL.

By differencing a fast (3) and slow (10) EMA of the ADL, CHO isolates the *change* in money flow momentum.

---

## 3. The Strategy: "The Flow Accelerator"

**Trigger:** Enter on zero-line crossover (flow acceleration shift) or divergence, filtered by trend structure.

1. **Macro Filter:** Trade ONLY in direction of the 90-period SMA.
2. **Long Entry:**
    * Price > SMA(90).
    * CHO crosses above **Zero**.
    * *Enhanced:* Prior bullish divergence (Price Lower Low, CHO Higher Low).
3. **Short Entry:**
    * Price < SMA(90).
    * CHO crosses below **Zero**.
    * *Enhanced:* Prior bearish divergence.
4. **Exit:**
    * **Take Profit:** 3x ATR.
    * **Stop Loss:** 2x ATR.
    * **Invalidation:** CHO crosses back through zero against trade.

---

## 4. Implementation

### 4.1 Python (Vectorized)

```python
import pandas as pd
import numpy as np

def calculate_chaikin_oscillator(
    df: pd.DataFrame,
    fast: int = 3,
    slow: int = 10,
) -> pd.DataFrame:
    """
    Calculate the Chaikin Oscillator (CHO).
    Requires 'High', 'Low', 'Close', 'Volume' columns.
    """
    result = pd.DataFrame(index=df.index)

    # Step 1: Close Location Value
    hl_range = df['High'] - df['Low']
    result['CLV'] = np.where(
        hl_range > 0,
        ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / hl_range,
        0.0
    )

    # Step 2: Money Flow Volume
    result['MFV'] = result['CLV'] * df['Volume']

    # Step 3: Accumulation/Distribution Line
    result['ADL'] = result['MFV'].cumsum()

    # Step 4: Chaikin Oscillator
    result['ADL_EMA_Fast'] = result['ADL'].ewm(span=fast, adjust=False).mean()
    result['ADL_EMA_Slow'] = result['ADL'].ewm(span=slow, adjust=False).mean()
    result['CHO'] = result['ADL_EMA_Fast'] - result['ADL_EMA_Slow']

    return result
```

### 4.2 Rust (Streaming)

```rust
pub struct StreamingEMA {
    value: f64,
    alpha: f64,
    initialized: bool,
}

impl StreamingEMA {
    pub fn new(period: usize) -> Self {
        Self {
            value: 0.0,
            alpha: 2.0 / (period as f64 + 1.0),
            initialized: false,
        }
    }

    pub fn update(&mut self, input: f64) -> f64 {
        if !self.initialized {
            self.value = input;
            self.initialized = true;
        } else {
            self.value = (input - self.value) * self.alpha + self.value;
        }
        self.value
    }
    
    pub fn value(&self) -> f64 { self.value }
}

pub struct ChaikinOscillator {
    adl: f64,
    ema_fast: StreamingEMA,
    ema_slow: StreamingEMA,
    prev_cho: f64,
}

impl ChaikinOscillator {
    pub fn new(fast: usize, slow: usize) -> Self {
        Self {
            adl: 0.0,
            ema_fast: StreamingEMA::new(fast),
            ema_slow: StreamingEMA::new(slow),
            prev_cho: 0.0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64, volume: f64) -> (f64, i8) {
        // Step 1: CLV
        let hl_range = high - low;
        let clv = if hl_range > 1e-12 {
            (2.0 * close - low - high) / hl_range
        } else {
            0.0
        };

        // Step 2-3: MFV, ADL
        let mfv = clv * volume;
        self.adl += mfv;

        // Step 4: CHO
        let fast_val = self.ema_fast.update(self.adl);
        let slow_val = self.ema_slow.update(self.adl);
        let cho = fast_val - slow_val;

        // Signal (Zero Cross)
        let signal = if self.prev_cho <= 0.0 && cho > 0.0 {
            1
        } else if self.prev_cho >= 0.0 && cho < 0.0 {
            -1
        } else {
            0
        };

        self.prev_cho = cho;
        (cho, signal)
    }
}
```
