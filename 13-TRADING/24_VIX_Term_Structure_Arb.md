# 24 - VIX Term Structure Arbitrage: The Roll Yield

**Volume:** 24 of 50
**Strategy Type:** Volatility / Carry Trade / Macro
**Risk Profile:** High (Short Volatility Blowup Risk)
**Mathematical Basis:** Contango vs Backwardation on VIX Futures

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Shape of Fear](#2-the-theory-the-shape-of-fear)
    * 2.1. Contango (Normal): Market expects future to be scarier.
    * 2.2. Backwardation (Panic): Market is scary NOW.
    * 2.3. The Roll Yield: Profiting from the decay of fear.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The VIX Ratio: $VIX_{3M} / VIX_{Spot}$.
    * 3.2. Execution: Short VIX Futures (Harvest Yield).
    * 3.3. The Hedge: Long OTM VIX Calls (Tail Risk).
4. [Microstructure & HFT](#4-microstructure--hft)
    * 4.1. The Basis Trade: Real Future vs Synthetic Future.
    * 4.2. Arbitraging the "Fair Value" of VIX.
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Nelson-Siegel Curve Fitting.
    * 5.2. Roll Yield Calculation.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Term Structure Construction).
    * 6.2. Rust (Curve Fitting & Signal).
7. [Historical Case Studies](#7-historical-case-studies)
    * 7.1. Volmageddon (XIV Blowup).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**VIX Term Structure Arbitrage** exploits the fact that "Fear is usually overpriced."
The **VIX Term Structure** (the curve of VIX Futures prices) tells us the "Price of Insurance" over time.
In **Contango** (Upward Slope), we Short Volatility to capture the **Roll Yield** as futures decay to spot.
In **Backwardation** (Downward Slope), we go Cash or Long Volatility to survive the crash.
Strategy 24 is the "Traffic Light" for the entire GOLIATH system.

---

# 2. The Theory

## 2.1. Contango (Green Light)

* **Spot VIX:** 15.
* **Future (M1):** 17.
* **Logic:** Market pays a premium for future protection. If VIX stays at 15, M1 MUST fall to 15 at expiration.
* **Action:** Short VIX Futures. Earn the decay.

## 2.2. Backwardation (Red Light)

* **Spot VIX:** 40.
* **Future (M1):** 35.
* **Logic:** Panic is here. Puts are bid up.
* **Action:** CLOSE ALL SHORTS. Buy Puts.

---

# 4. Microstructure & HFT

## 4.1. The Basis Trade

HFTs construct a **Synthetic VIX Future** using S&P 500 Options (replicating the VIX formula).
If `Real_Future - Synthetic_Future > 0.05`, they sell the Real and buy the Synthetic.
This arbitrage keeps the VIX Futures pegged to the SPX Option chain.

---

# 6. Implementation: Production Grade

## 6.1. Python (Term Structure Logic)

```python
import pandas as pd
import numpy as np

def analyze_term_structure(vix_spot, vix_m1, vix_m3):
    """
    vix_m1: Front Month Future
    vix_m3: 3-Month Future
    """
    # 1. Slope Ratio
    ratio = vix_m3 / vix_spot
    
    # 2. Roll Yield (Annualized)
    # Assume 30 days to expiration for M1
    roll_yield = (vix_m1 - vix_spot) / vix_spot * (365/30)
    
    # 3. Regime
    if ratio > 1.10:
        signal = "STRONG_CONTANGO_SHORT_VOL"
    elif ratio < 1.00:
        signal = "BACKWARDATION_LONG_VOL"
    else:
        signal = "NEUTRAL"
        
    return ratio, roll_yield, signal
```

## 6.2. Rust (Nelson-Siegel Curve Fitting)

```rust
// Fitting a curve to VIX Futures points to smooth the signal
pub struct VixCurve {
    points: Vec<(f64, f64)>, // (Days, Price)
}

impl VixCurve {
    pub fn get_slope(&self) -> f64 {
        if self.points.len() < 2 { return 0.0; }
        
        let spot = self.points[0].1; // VIX Spot
        let m1 = self.points[1].1;   // M1 Future
        
        // Positive Slope = Contango
        (m1 - spot) / spot
    }
    
    pub fn is_backwardation(&self) -> bool {
        self.get_slope() < 0.0
    }
}
```

---

# 7. Historical Case Studies

## 7.1. Volmageddon (Feb 2018)

The **XIV** (Inverse VIX ETN) relied on Contango.
On Feb 5, the curve flipped from Contango to Massive Backwardation in hours.
The rebalancing mechanism of XIV forced it to buy VIX Futures as they rose.
Result: **-96%** in one day.
**Rule:** If Term Structure inverts, **KILL THE STRATEGY**. Do not wait.

---

# 8. Conclusion

**Strategy 24** is the most dangerous influential strategy in the portfolio.
It provides the highest Sharpe Ratio in bull markets (harvesting yield).
But it carries the risk of total ruin.
Success depends entirely on the **Regime Filter** (The Term Structure).
If the curve is Green (Contango), we feast.
If the curve is Red (Backwardation), we fast.
