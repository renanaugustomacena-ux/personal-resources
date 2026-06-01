# 129 - FRAMA Adaptive Regime

**Volume:** 129 of 100
**Strategy Type:** Adaptive Trend / Regime Detection
**Risk Profile:** Low (Adapts to volatility)
**Mathematical Basis:** Fractal Dimension ($D$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Theory: Fractal Dimension](#2-theory-fractal-dimension)
3. [The Strategy](#3-the-strategy)
4. [Implementation](#4-implementation)

---

## 1. Executive Summary

**Fractal Adaptive Moving Average (FRAMA)** adjusts its smoothing factor ($\alpha$) based on the **fractal dimension** of the price action.

* **Trend ($D \approx 1.0$):** FRAMA speeds up (low smoothing).
* **Chop ($D \approx 2.0$):** FRAMA slows down (high smoothing).

It serves a dual purpose in GOLIATH:

1. **Adaptive MA:** A superior trailing stop.
2. **Regime Detector:** The $D$ value itself tells the system whether to use Trend strategies or Mean Reversion strategies.

---

## 2. Theory: Fractal Dimension

FRAMA uses a modified box-counting method over a window $N$ (default 16).
It splits the window into two halves ($N1, N2$) and compares their lengths to the full window length ($N3$).

$$ D = \frac{\log(N1 + N2) - \log(N3)}{\log(2)} $$

Then $\alpha$ is calculated as:
$$ \alpha = e^{-4.6(D-1)} $$

As $D$ goes from 1 to 2, $\alpha$ goes from 1 (fast) to 0.01 (slow).

---

## 3. The Strategy: "The Dimension Trader"

**Trigger:** Use $D$ to select the mode, use FRAMA line for execution.

1. **Calculate:** $D$ and FRAMA(16).
2. **Regime Filter:**
    * If $D < 1.5$: **TREND MODE**.
    * If $D > 1.5$: **CHOP MODE**.
3. **Action - Trend Mode:**
    * Buy if Price crosses above FRAMA.
    * Trailing Stop: FRAMA line.
4. **Action - Chop Mode:**
    * **Do not trade breakouts.**
    * Use Bollinger Band mean reversion (Buy Low, Sell High).
    * FRAMA becomes a "Fair Value" pivot line.

---

## 4. Implementation

### 4.1 Python (Vectorized)

```python
import pandas as pd
import numpy as np

def frama(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 16) -> dict:
    """
    Calculate FRAMA and Fractal Dimension.
    """
    assert period % 2 == 0, "Period must be even"
    half = period // 2
    
    frama_val = pd.Series(index=close.index, dtype=float)
    fractal_dim = pd.Series(index=close.index, dtype=float)
    alpha_s = pd.Series(index=close.index, dtype=float)
    
    # Initialize
    frama_val.iloc[period-1] = close.iloc[period-1]
    
    for i in range(period, len(close)):
        # Calculate N1, N2, N3 based on High-Low ranges
        # [Implementation details omitted for brevity - standard FRAMA logic]
        # See full derivation in monograph
        
        # Simplified loop structure for illustration:
        h1 = high.iloc[i-period:i-half].max()
        l1 = low.iloc[i-period:i-half].min()
        n1 = (h1 - l1) / half
        
        h2 = high.iloc[i-half:i].max()
        l2 = low.iloc[i-half:i].min()
        n2 = (h2 - l2) / half
        
        h3 = high.iloc[i-period:i].max()
        l3 = low.iloc[i-period:i].min()
        n3 = (h3 - l3) / period
        
        if n1 + n2 > 0 and n3 > 0:
            d = (np.log(n1 + n2) - np.log(n3)) / np.log(2)
        else:
            d = 1.5
            
        fractal_dim.iloc[i] = d
        
        alpha = np.exp(-4.6 * (d - 1.0))
        alpha = max(0.01, min(1.0, alpha))
        alpha_s.iloc[i] = alpha
        
        prev = frama_val.iloc[i-1]
        frama_val.iloc[i] = alpha * close.iloc[i] + (1 - alpha) * prev
        
    return {'frama': frama_val, 'dimension': fractal_dim}
```

### 4.2 Rust (Streaming)

```rust
pub struct FRAMA {
    period: usize,
    half: usize,
    highs: Vec<f64>,
    lows: Vec<f64>,
    frama: f64,
}

impl FRAMA {
    pub fn new(period: usize) -> Self {
        Self {
            period,
            half: period / 2,
            highs: Vec::with_capacity(period),
            lows: Vec::with_capacity(period),
            frama: 0.0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> (f64, f64) {
        self.highs.push(high);
        self.lows.push(low);
        if self.highs.len() > self.period {
            self.highs.remove(0);
            self.lows.remove(0);
        }

        if self.highs.len() < self.period {
            self.frama = close;
            return (close, 1.5);
        }

        // Calculate D (simplified for brevity)
        let n1 = (self.highs[0..self.half].iter().fold(0.0/0.0, |a,b| a.max(*b)) - 
                  self.lows[0..self.half].iter().fold(1.0/0.0, |a,b| a.min(*b))) / self.half as f64;
        // ... n2, n3 calculations ...
        
        let d = 1.5; // Placeholder for full calc logic
        let alpha = (-4.6 * (d - 1.0)).exp().max(0.01).min(1.0);
        
        self.frama = alpha * close + (1.0 - alpha) * self.frama;
        
        (self.frama, d)
    }
}
```
