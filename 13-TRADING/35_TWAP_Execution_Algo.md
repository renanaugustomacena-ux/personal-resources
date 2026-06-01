# 35 - TWAP Execution & Reversion Strategy

**Volume:** 35 of 50
**Strategy Type:** Execution Algo / Benchmarking / Mean Reversion
**Risk Profile:** Predictable Footprint (Execution) / Momentum (Reversion)
**Mathematical Basis:** $\text{TWAP} = \frac{1}{N} \sum P_t$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Time is Linear](#2-the-theory-time-is-linear)
    * 2.1. VWAP vs TWAP: The Liquidity War.
    * 2.2. Linearity as a camouflage.
3. [Strategy 1: TWAP Execution (The Slicer)](#3-strategy-1-twap-execution-the-slicer)
    * 3.1. Slicing Logic ($q = Q/T$).
    * 3.2. Randomization (Hiding from HFTs).
4. [Strategy 2: TWAP Reversion (The Signal)](#4-strategy-2-twap-reversion-the-signal)
    * 4.1. Concept: Price deviation from Time-Weighted Average.
    * 4.2. Signal: Fade extreme deviations (> 2%).
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Impact Cost & Tracking Error.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Pandas Indicator + Execution Class).
    * 6.2. Rust (Randomized Execution Engine).
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**TWAP** serves two masters:

1. **The Execution Trader:** Uses it to slice large orders ($Q$) over time ($T$) to minimize market impact.
2. **The Alpha Trader:** Uses it as a benchmark. If Price diverges far from TWAP without volume, it is a "Low Liquidity Run" that will revert.
Strategy 35 covers both: How to *be* the TWAP, and how to *trade against* the TWAP deviation.

---

# 2. The Theory: Time is Linear

## 2.1. VWAP vs TWAP

* **VWAP:** Volume-Weighted. Good for liquid assets (Stocks). Gamed by end-of-day volume spikes.
* **TWAP:** Time-Weighted. Good for fragmented assets (Crypto). Harder to game because every second counts equally.

## 2.2. Linearity

TWAP spreads execution linearly. It ignores volume spikes. This makes it robust in "fake volume" environments (Wash Trading) because it forces the trader to prove price stability over *time*, not just momentary volume.

---

# 3. Strategy 1: TWAP Execution (The Slicer)

## 3.1. The Algorithm

Total Order: 10,000 SOL. Duration: 10 Hours.

* **Slice:** 16.66 SOL per minute.
* **Logic:** Execute regardless of price.

## 3.2. Hiding Footprints

HFTs "sniff" for constant time intervals (e.g., exactly every 60s).
**Counter-measure:** Randomize delay (45s - 75s) and Size (+/- 10%).

---

# 4. Strategy 2: TWAP Reversion (The Signal)

From `035_TWAP`:

## 4.1. Concept

Large institutional orders (TWAP Algos) act as a magnet. If price runs away, the algos will eventually pull it back as they passively fill orders at the mean.

## 4.2. Rules

1. **Calculate:** Session TWAP (Anchored to Open).
2. **Calculate:** % Deviation = $(Price - TWAP) / TWAP$.
3. **Trigger:** Deviation > 2% (Intraday Extreme).
4. **Signal:** Fade. (Short if Price > TWAP).
5. **Exit:** Price touches TWAP.

**Why it works:** Price cannot deviate from the average forever without volume support. If Price runs but Volume or Time doesn't confirm, it reverts.

---

# 6. Implementation: Production Grade

## 6.1. Python (Indicator + Execution)

```python
import pandas as pd
import numpy as np
import time
import random

# --- PART A: INDICATOR ---
def calculate_session_twap(df: pd.DataFrame):
    """
    Calculate Anchored TWAP (reset at start of day).
    """
    grouped = df.groupby(df.index.date)
    twap = grouped['Close'].expanding().mean()
    return twap.reset_index(level=0, drop=True)

# --- PART B: EXECUTION ---
class TWAPAlgo:
    def __init__(self, qty, duration_minutes, interval_seconds=60):
        self.qty = qty
        self.duration = duration_minutes
        self.interval = interval_seconds
        self.slices = int((duration_minutes * 60) / interval_seconds)
        self.slice_size = qty / self.slices
        
    def run(self):
        print(f"Starting TWAP: {self.slices} slices of {self.slice_size:.4f}")
        for i in range(self.slices):
            # Randomize
            current_size = self.slice_size * random.uniform(0.9, 1.1)
            jitter = random.uniform(-5, 5)
            
            print(f"Slice {i+1}: Executing {current_size:.4f}...")
            # execute_order(current_size)
            
            time.sleep(self.interval + jitter)
```

## 6.2. Rust (Randomized Execution Engine)

```rust
use rand::Rng;
use std::time::{Duration, Instant};

pub struct TwapExecutor {
    total_qty: f64,
    duration: Duration,
    start_time: Instant,
    executed_qty: f64,
    next_trade_time: Instant,
}

impl TwapExecutor {
    pub fn new(total_qty: f64, duration_secs: u64) -> Self {
        let now = Instant::now();
        Self {
            total_qty,
            duration: Duration::from_secs(duration_secs),
            start_time: now,
            executed_qty: 0.0,
            next_trade_time: now,
        }
    }

    pub fn tick(&mut self) -> Option<f64> {
        let now = Instant::now();
        
        if now >= self.next_trade_time {
            let elapsed = now.duration_since(self.start_time);
            if elapsed >= self.duration { return None; }
            
            // Calculate slice
            let remaining_time = self.duration - elapsed;
            let avg_interval = 60.0;
            let remaining_slices = (remaining_time.as_secs_f64() / avg_interval).ceil();
            let slice_qty = (self.total_qty - self.executed_qty) / remaining_slices;
            
            self.executed_qty += slice_qty;
            
            // Randomize next time
            let mut rng = rand::thread_rng();
            let delay = rng.gen_range(45..75);
            self.next_trade_time = now + Duration::from_secs(delay);
            
            return Some(slice_qty);
        }
        None
    }
}
```

---

# 7. Risk Management

## 7.1. Predators

HFTs detect TWAP by timing.
**Solution:** If you see "Predatory Scaling" (Volume increasing exactly 1ms before your slice), switch to **VWAP** or **POV** execution immediately.

## 7.2. Fat Tails

If market crashes 10% in 5 minutes, do not keep buying your TWAP slices.
**Filter:** If VIX > 30, Pause Execution.

---

# 8. Conclusion

**Strategy 35** is the Workhorse.
Whether you are executing a large position for GOLIATH or fading a reckless institution, TWAP is the baseline.
It represents the "Average Price of Time".
In a market obsessed with Volume, Time is often the overlooked variable.
