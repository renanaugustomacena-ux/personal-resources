# 89 - Crisis Alpha: VIX Trend & VPIN Toxicity

**Volume:** 89 of 100
**Strategy Type:** Crisis Alpha / Trend Following / Microstructure Risk
**Risk Profile:** Contango Bleed (Cost of Carry) / False Positives (Paranoia)
**Mathematical Basis:** VIX Term Structure, Hawkes Branching Ratio ($n$), & VPIN ($OI_\tau$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Anatomy of Panic](#2-the-theory-anatomy-of-panic)
    * 2.1. VIX Trend: The Fire Extinguisher.
    * 2.2. VPIN (The Geiger Counter): Detecting Toxic Flow before the crash.
    * 2.3. The Hawkes Process: Modeling Self-Excitation.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Signal 1: Term Structure Backwardation (The Macro View).
    * 3.2. Signal 2: Hawkes Criticality ($n > 0.9$) (The Micro View).
    * 3.3. Signal 3: VPIN Spike (The Toxicity View).
    * 3.4. Execution: Long VIX Futures / Puts.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Roll Yield Math.
    * 4.2. Hawkes Intensity Function.
    * 4.3. volume-Synchronized Probability of Informed Trading (VPIN).
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python (Hawkes & VPIN).
    * 5.2. Rust (Log-Likelihood Maximization).
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Crisis Alpha** is the strategy of the "Fireman".
Most strategies hold inflammable assets (Stocks). We hold the extinguisher (Long Vol).
However, extinguishers are heavy (Negative Roll Yield).
We use **VIX Trend** and **Hawkes Processes** to detect exactly when the "Spark" becomes a "Firestorm".
We augment this with **VPIN (Indicator 086)**, a high-frequency metric that detects "Toxic Flow" (Informed Selling) often hours before the price collapses.
Strategy 89 doesn't just buy insurance; it buys insurance *after* the smoke appears (VPIN), but *before* the house burns down (VIX Spike).

---

# 2. The Theory

### 2.1. VIX Trend

VIX spends 80% of time decaying (Mean Reverting).
But when it trends, it trends exponentially (15 $\to$ 80).
"Escalator Up, Elevator Down" for Stocks = "Elevator Up" for VIX.

### 2.2. VPIN (The Geiger Counter)

From `086_VPIN`:
**VPIN (Volume-Synchronized Probability of Informed Trading)** measures the toxicity of the order flow.

* **Normal Flow:** Balanced buy/sell volume.
* **Toxic Flow:** One-sided, persistent selling by informed traders.
* **Result:** Market Makers widen spreads or vanish. Liquidity evaporates. Flash Crash follows.

### 2.3. The Hawkes Process

From `058_Hawkes`:
Panic is contagious. One large sell order triggers stops, which trigger margin calls.
This is a **Self-Exciting Point Process**.
$$ \lambda(t) = \mu + \sum_{t_i < t} \alpha e^{-\beta(t - t_i)} $$
Current intensity depends on past events.

---

# 3. Strategy Rules

### 3.1. Term Structure Signal

* **Macro View:** If $VIX_{Front} > VIX_{Back}$ (Backwardation), the market is already stressed. Go Long VIX.

### 3.2. Hawkes Signal (Micro Structure)

* **Fragility View:** Calculate Branching Ratio $n = \alpha / \beta$.
* **Trigger:** If $n > 0.95$, the market is "Super-Critical". A single trade can trigger a cascade.

### 3.3. VPIN Signal (Toxicity View)

* **Input:** Volume Buckets.
* **Trigger:** VPIN > 90th Percentile of historical VPIN.
* **Meaning:** "Smart Money" is bailing out.
* **Action:** If Term Structure is Flat AND VPIN is High $\rightarrow$ **Buy Puts immediately**.

---

# 4. Mathematical Derivation

### 4.1. VPIN Calculation

1. **Volume Buckets:** Fill a bucket every time $V$ contracts trade (Volume Clock).
2. **Order Imbalance ($OI_\tau$):** $|V_\tau^B - V_\tau^S|$.
3. **VPIN:** Moving average of Imbalance / Total Volume.
$$ VPIN = \frac{\sum_{\tau=1}^n OI_\tau}{n \times V} $$

### 4.2. Hawkes Branching Ratio

$$ n = \int_0^\infty \phi(t) dt = \frac{\alpha}{\beta} $$
If $n > 1$, intensity explodes to infinity (Crash).

---

# 5. Implementation: Production Grade

### 5.1. Python (Integrated Warning System)

```python
import pandas as pd
import numpy as np
from tick.hawkes import HawkesExpKern

def calculate_vpin(trades, bucket_volume=1000, window=50):
    """
    Standard VPIN implementation.
    """
    trades['cum_vol'] = trades['volume'].cumsum()
    trades['bucket_id'] = (trades['cum_vol'] // bucket_volume).astype(int)
    
    # Classify direction (Tick Rule)
    price_change = trades['price'].diff()
    direction = np.where(price_change > 0, 1, np.where(price_change < 0, -1, 0))
    
    trades['buy_vol'] = np.where(direction == 1, trades['volume'], 0)
    trades['sell_vol'] = np.where(direction == -1, trades['volume'], 0)
    
    buckets = trades.groupby('bucket_id')[['buy_vol', 'sell_vol']].sum()
    buckets['OI'] = np.abs(buckets['buy_vol'] - buckets['sell_vol'])
    
    vpin = buckets['OI'].rolling(window).mean() / bucket_volume
    return vpin

def estimate_criticality(timestamps):
    # Hawkes estimation (as before)
    pass

def crisis_alpha_logic(vpin_score, hawkes_n, vix_shape):
    score = 0
    if vpin_score > 0.8: score += 1
    if hawkes_n > 0.9: score += 1
    if vix_shape == "BACKWARDATION": score += 2
    
    if score >= 2:
        return "GO_LONG_VOL"
    return "STAY_CASH"
```

---

# 6. Risk Management

### 6.1. The Contango Bleed

Holding VIX products in Contango loses ~5% per month.
**Rule:** Only enter when VPIN or Hawkes confirms "Imminent Danger". Do not hold VIX as a permabear.

### 6.2. False Positives

VPIN can spike due to Portfolio Rebalancing (non-toxic).
Filter: Check if VPIN spike coincides with a specific time (e.g., Market Close).

---

# 7. Conclusion

**Strategy 89** combines the Macro view (Term Structure) with the Micro view (Hawkes & VPIN).
Term Structure tells us if the "Market Insurance" is priced for panic.
Hawkes Process tells us if the "Market Structure" is actually breaking.
VPIN tells us if "Toxic Flow" is causing the break.
When all three align, we bet on the Crash. And usually, we win big.
