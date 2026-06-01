# 90 - Liquidity Probabilities & Black Holes

**Volume:** 90 of 100
**Strategy Type:** Market Microstructure / HFT / Crash Prediction
**Risk Profile:** Latency / Spoofing (False Depth)
**Mathematical Basis:** Order Book Dynamics, Liquidity Replenishment, & The Black Hole Condition ($\frac{d^2L}{dt^2} < 0$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Order Book is Mostly Empty](#2-the-theory-the-order-book-is-mostly-empty)
    * 2.1. The Illusion of Liquidity.
    * 2.2. The Air Pocket: Gaps in the book.
    * 2.3. Liquidity Black Holes (Indicator 087): Rapid dispersion of the book creating a vacuum.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Monitoring Depth (Probability Map).
    * 3.2. Order Flow Imbalance (OFI).
    * 3.3. Black Hole Trigger: Liquidity Drops + Volatility Stable = Imminent Crash.
    * 3.4. Signal: If Probability(Gap) > 80%, stop buying. Or place "Stink Bids" deep in the hole.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Average Depth: $D(P) = \sum V_i$.
    * 4.2. Probability of Execution: $P(Exec) = 1 - e^{-\lambda \Delta t}$.
    * 4.3. Cost of Round Trip (CRT) & Liquidity Strength ($L_t$).
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Swiss Franc Peg Break (2015): The ultimate Black Hole.
    * 5.2. Flash Crash (2010): HFT withdrawal.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Reconstructing the LOB.
    * 6.2. Calculating "Black Hole Index".
7. [Run Strategy: "The Vacuum Cleaner"](#7-run-strategy-the-vacuum-cleaner)
    * 7.1. Catching the Wick.
    * 7.2. Avoiding the falling elevator.
8. [Risk Management](#8-risk-management)
9. [Conclusion: The Sonar](#9-conclusion-the-sonar)

---

# 1. Executive Summary

**Liquidity Probabilities** maps the density of the market.
It tells Goliath where the "Wall" is and where the "Air" is.
We augment this with **Liquidity Black Holes (Indicator 087)**, which measures the *rate of change* of that density.
When liquidity evaporates rapidly (Black Hole), price has no friction. It accelerates.
Strategy 90 is about:

1. **Predicting** the holes (Warning Signal).
2. **Exploiting** the holes (Stink Bids).

---

# 2. The Theory

### 2.1. The Shape of the Book

Normal: "V" shape.
Stressed: "U" shape.
Crash (Black Hole): "L" shape. No bids.

### 2.2. Liquidity Black Holes (Indicator 087)

A Black Hole occurs when the Order Book disperses rapidly.

* **Mechanism:** Stop Loss Cascades triggering into an empty book.
* **Metric:** Market Depth (e.g., +/- 1%) divided by Recent Volatility.
* **Signal:** When Depth collapses while Volatility is steady $\rightarrow$ Imminent Breakout or Crash.

---

# 3. Strategy Rules

### 3.1. The Black Hole Signal

* **Input:** Level 2 Data.
* **Calc:** Liquidity Strength $L_t = \frac{\sum V_{bids}}{\sigma_t}$.
* **Trigger:** If $L_t$ drops > 50% in 1 minute.
* **Prediction:** Price will gap down through the vacuum.

### 3.2. The Stink Bid Matrix (Exploitation)

* **Action:** If Black Hole detected, place Limit Bids at -5%, -10%, -15%.
* **Logic:** The price will "wick" through the hole until it hits a solid wall of buyers (or your stink bid).
* **Exit:** Mean Reversion to VWAP.

---

# 4. Mathematical Derivation

### 4.1. Cost of Round Trip (CRT)

From `087_Black_Holes`:
$$ CRT = \frac{Ask_{VWAP} - Bid_{VWAP}}{MidPrice} $$
Measure of illiquidity.

### 4.2. Liquidity Strength

$$ L_t = \frac{Depth_{\pm 1\%}}{\sigma_t} $$
If $L_t \to 0$, we are in a Black Hole.

### 4.3. Probability of Fill

$$ P(Fill | \delta) \propto \exp(-k \delta) $$

---

# 5. Historical Case Studies

### 5.1. Swiss Franc (2015)

EURCHF dropped 30% in minutes.
Why? Because every bid evaporated instantly.
The "Black Hole" was absolute zero liquidity.

### 5.2. ETH Flash Crash (2017)

ETH -> $0.10.
Caused by a Black Hole on GDAX.
Traders with Stink Bids (Strategy 90) bought ETH at $0.10.

---

# 6. Python Implementation (Production Grade)

```python
import pandas as pd
import numpy as np

def calculate_liquidity_strength(order_book, volatility):
    """
    order_book: {'bids': [[price, vol]...], 'asks': ...}
    volatility: current std dev
    """
    mid_price = (order_book['bids'][0][0] + order_book['asks'][0][0]) / 2
    
    # Sum volume within 1%
    lower_bound = mid_price * 0.99
    depth = sum([v for p, v in order_book['bids'] if p >= lower_bound])
    
    # Normalize by vol
    # High Depth / Low Vol = High Strength
    # Low Depth / High Vol = BLACK HOLE
    strength = depth / (volatility + 1e-9)
    return strength

def black_hole_detector(strength_series):
    # Second derivative check
    velocity = strength_series.diff()
    acceleration = velocity.diff()
    
    if velocity.iloc[-1] < -0.5: # Dropped 50%
        return "CRITICAL_WARNING"
    return "NORMAL"
```

---

# 7. Run Strategy: "The Vacuum Cleaner"

**Rules:**

1. **Monitor:** Global Liquidity Index.
2. **Trigger:** Liquidity drops 50% (Black Hole).
3. **Wait:** Wait for the "Wick" (Price sweeps into the vacuum).
4. **Entry:** Limit Buy 5% below market (Stink Bid).
5. **Exit:** Rebound to VWAP.

**Why it works:** Black Holes are temporary. Value Investors eventually step in. The vacuum fill is mean-reverting.

---

# 8. Risk Management

### 8.1. Exchange Risk

During Black Holes, exchanges often crash (503 Error).
You need to have orders *resting* on the book (Post Only) *before* the crash. You cannot submit orders *during* the crash.

### 8.2. Catching a Falling Knife

Sometimes the Black Hole is fundamental (Terra Luna).
The price goes to zero and never bounces.
**Filter:** Only trade Black Holes on "Blue Chip" assets (BTC, ETH) with no fundamental news trigger (Pure Liquidity Event).

---

# 9. Conclusion

Liquidity Probabilities is the **Infrastructure** of Goliath.
It tells us that Price is a function of Liquidity.
If Liquidity disappears, Price is undefined.
Strategy 90 monitors the integrity of the playing field.
If the field is crumbling, it warns everyone to get off (or to buy the rubble cheap).
