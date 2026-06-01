# 130 - Schaff Trend Cycle (STC)

**Volume:** 130 of 100
**Strategy Type:** Cycle / Momentum (Binary-like)
**Risk Profile:** Medium
**Mathematical Basis:** Stochastic(Stochastic(MACD))

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Theory: The Cycle Sniper](#2-theory-the-cycle-sniper)
3. [The Strategy](#3-the-strategy)
4. [Implementation](#4-implementation)

---

## 1. Executive Summary

**Schaff Trend Cycle (STC)** is a hybrid indicator that applies a double Stochastic smoothing to the MACD line.

* **Problem:** MACD is accurate but laggy. Stochastic is fast but noisy.
* **Solution:** STC is accurate (uses MACD trend) and fast (uses Stochastic cycles).
* **Result:** A clean, near-binary oscillator that snaps between 0 (Oversold) and 100 (Overbought).

---

## 2. Theory: The Cycle Sniper

The formula chain:

1. **MACD:** EMA(23) - EMA(50) (Standard inputs are 12/26, Schaff prefers 23/50).
2. **Stoch(MACD):** Normalize MACD to %K.
3. **Smooth:** EMA signal of that.
4. **Stoch(Smooth):** Normalize AGAIN.
5. **Smooth:** Final EMA.

This double normalization forces the indicator to spend most time at 0 or 100, making crossovers of 25 and 75 extremely significant.

---

## 3. The Strategy: "STC Binary Trigger"

**Trigger:** Trade the 25/75 crossovers in the direction of the dominant trend.

1. **Trend Filter:** Price > EMA(50).
2. **Long Entry:**
    * STC crosses **above 25** (coming from oversold).
    * *Context:* Must be in an uptrend (EMA 50 check).
3. **Short Entry:**
    * Price < EMA(50).
    * STC crosses **below 75** (coming from overbought).
4. **Exit:**
    * Opposing signal (Longs exit when STC > 75 and turns down).
    * Or simpler: Take profit at fixed RR.
5. **Stop Loss:** Recent Swing Low / Swing High.

---

## 4. Implementation

### 4.1 Python (Vectorized)

```python
import pandas as pd
import numpy as np

def schaff_trend_cycle(close: pd.Series, fast: int = 23, slow: int = 50, cycle: int = 10, factor: float = 0.5) -> pd.Series:
    """
    STC Calculation.
    """
    # 1. MACD
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    
    # 2. Stoch 1
    low_macd = macd.rolling(cycle).min()
    range_macd = macd.rolling(cycle).max() - low_macd
    x = 100 * (macd - low_macd) / range_macd.replace(0, np.nan)
    x = x.fillna(50)
    
    # Smooth 1
    pf = pd.Series(index=close.index, dtype=float)
    pf.iloc[0] = x.iloc[0]
    for i in range(1, len(pf)):
        pf.iloc[i] = pf.iloc[i-1] + factor * (x.iloc[i] - pf.iloc[i-1])
        
    # 3. Stoch 2
    low_pf = pf.rolling(cycle).min()
    range_pf = pf.rolling(cycle).max() - low_pf
    y = 100 * (pf - low_pf) / range_pf.replace(0, np.nan)
    y = y.fillna(50)
    
    # Smooth 2 (Final STC)
    stc = pd.Series(index=close.index, dtype=float)
    stc.iloc[0] = y.iloc[0]
    for i in range(1, len(stc)):
        stc.iloc[i] = stc.iloc[i-1] + factor * (y.iloc[i] - stc.iloc[i-1])
        
    return stc
```

### 4.2 Rust (Streaming)

```rust
// Implementation involves buffering 'cycle' periods of MACD and PF 
// to calculate min/max for Stochastic normalization.
// See full indicator file for RingBuffer implementation details.
```
