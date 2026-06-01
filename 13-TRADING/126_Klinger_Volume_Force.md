# 126 - Klinger Volume Force (KVO)

**Volume:** 126 of 100
**Strategy Type:** Volume Flow / Smart Money Tracker
**Risk Profile:** Low (Confirmation tool)
**Mathematical Basis:** EMA(Volume Force, 34) - EMA(Volume Force, 55)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Theory: The Force Field](#2-theory-the-force-field)
3. [The Strategy](#3-the-strategy)
4. [Implementation](#4-implementation)

---

## 1. Executive Summary

**The Klinger Volume Oscillator (KVO)**, developed by Stephen Klinger, is a sophisticated volume-based oscillator that quantifies the long-term and short-term flow of money into and out of a security. Unlike simple volume indicators, KVO assigns *directional force* to volume by weighing it against the price range and trend direction.

* **Concept:** Volume Force = Volume × Trend Direction × |2 × (Daily Range / Cumulative Range) - 1|.
* **The "Tell":** KVO detects divergence between volume force and price *before* price reverses.
* **GOLIATH Role:** Primary volume-force confirmation layer for XAU/USD. Eliminates false breakouts where price moves but volume force is absent.

---

## 2. Theory: The Force Field

KVO answers the question: **"How forcefully was volume deployed?"**

1. **Trend Direction:** Determined by comparing typical price ($H+L+C$) to the previous bar.
2. **Daily Range (dm):** High - Low.
3. **Cumulative Range (cm):** Running sum of range, resetting when trend direction flips.
4. **Volume Force (VF):** Modulates raw volume by the *intensity* (dm/cm ratio). A wide-range bar in a new trend gets high force. A narrow-range bar in an old trend gets low force.

The KVO essentially strips out "lazy volume" (churn) and isolates "working volume" (accumulation/distribution).

---

## 3. The Strategy: "The Force Shift"

**Trigger:** Trade the genuine shift in volume force (zero-line crossover) confirmed by momentum.

1. **Regime Filter:** Price must be above EMA(50) for longs, below for shorts.
2. **Signal:**
    * **Long:** KVO crosses above **Zero** AND KVO > Signal Line (13 EMA).
    * **Short:** KVO crosses below **Zero** AND KVO < Signal Line.
3. **Stop Loss:** 2.0 × ATR(14).
4. **Take Profit:** 3.0 × ATR(14) (1.5:1 ratio).
5. **Exit Override:** Exit if KVO crosses back across the Signal Line against the trade (momentum fading).

---

## 4. Implementation

### 4.1 Python (Vectorized)

```python
import pandas as pd
import numpy as np

def klinger_volume_oscillator(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    fast_period: int = 34,
    slow_period: int = 55,
    signal_period: int = 13,
) -> dict:
    """
    Calculate the Klinger Volume Oscillator (KVO).
    """
    # Step 1: Trend detection using typical price
    tp = high + low + close
    trend = np.where(tp > tp.shift(1), 1.0, -1.0)
    trend = pd.Series(trend, index=high.index)

    # Step 2: Daily movement (bar range)
    dm = high - low

    # Step 3: Cumulative movement (cm)
    # cm resets when trend reverses; accumulates when trend continues
    trend_changed = trend != trend.shift(1)
    cm = pd.Series(np.nan, index=high.index, dtype=float)
    cm.iloc[0] = dm.iloc[0]

    for i in range(1, len(dm)):
        if trend_changed.iloc[i]:
            cm.iloc[i] = dm.iloc[i - 1] + dm.iloc[i]
        else:
            cm.iloc[i] = cm.iloc[i - 1] + dm.iloc[i]

    # Step 4: Volume Force
    # VF = Volume * |2 * dm/cm - 1| * Trend * 100
    # Guard against cm == 0
    cm_safe = cm.replace(0, np.nan)
    intensity = (2.0 * dm / cm_safe - 1.0).abs()
    vf = volume * intensity * trend * 100.0
    vf = vf.fillna(0.0)

    # Step 5: KVO = EMA(VF, fast) - EMA(VF, slow)
    ema_fast = vf.ewm(span=fast_period, adjust=False).mean()
    ema_slow = vf.ewm(span=slow_period, adjust=False).mean()
    kvo = ema_fast - ema_slow

    # Step 6: Signal line = EMA(KVO, signal_period)
    signal = kvo.ewm(span=signal_period, adjust=False).mean()

    return {
        'kvo': kvo,
        'signal': signal,
        'histogram': kvo - signal
    }
```

### 4.2 Rust (Streaming - GOLIATH Engine)

```rust
use std::collections::VecDeque;

/// Exponential Moving Average (streaming)
struct EMA {
    alpha: f64,
    value: Option<f64>,
}

impl EMA {
    fn new(period: usize) -> Self {
        Self {
            alpha: 2.0 / (period as f64 + 1.0),
            value: None,
        }
    }

    fn update(&mut self, input: f64) -> f64 {
        let v = match self.value {
            Some(prev) => self.alpha * input + (1.0 - self.alpha) * prev,
            None => input,
        };
        self.value = Some(v);
        v
    }
}

/// Klinger Volume Oscillator (streaming)
pub struct KlingerOscillator {
    fast_ema: EMA,
    slow_ema: EMA,
    signal_ema: EMA,
    prev_tp: Option<f64>,
    prev_trend: f64,
    prev_dm: f64,
    cm: f64,
}

impl KlingerOscillator {
    pub fn new(fast: usize, slow: usize, signal: usize) -> Self {
        Self {
            fast_ema: EMA::new(fast),
            slow_ema: EMA::new(slow),
            signal_ema: EMA::new(signal),
            prev_tp: None,
            prev_trend: 1.0,
            prev_dm: 0.0,
            cm: 0.0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64, volume: f64) -> (f64, f64, f64) {
        let tp = high + low + close;

        // Trend detection
        let trend = match self.prev_tp {
            Some(prev) => if tp > prev { 1.0 } else { -1.0 },
            None => 1.0,
        };

        let dm = high - low;

        // Cumulative movement
        if trend == self.prev_trend {
            self.cm += dm;
        } else {
            self.cm = self.prev_dm + dm;
        }

        // Volume Force
        let vf = if self.cm.abs() > 1e-12 {
            volume * ((2.0 * dm / self.cm) - 1.0).abs() * trend * 100.0
        } else {
            0.0
        };

        let fast_val = self.fast_ema.update(vf);
        let slow_val = self.slow_ema.update(vf);
        let kvo = fast_val - slow_val;
        let signal = self.signal_ema.update(kvo);

        self.prev_tp = Some(tp);
        self.prev_trend = trend;
        self.prev_dm = dm;

        (kvo, signal, kvo - signal)
    }
}
```
