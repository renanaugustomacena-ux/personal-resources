# 34 - VWAP Execution Algo: The Benchmark

**Volume:** 34 of 50
**Strategy Type:** Execution Algo / Best Execution / Market Impact
**Risk Profile:** Slippage Risk / Opportunity Cost (Speed)
**Mathematical Basis:** $\text{VWAP} = \frac{\sum (P_i \times V_i)}{\sum V_i}$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Hiding the Elephant](#2-the-theory-hiding-the-elephant)
    * 2.1. Market Impact: Square Root Law ($\Delta P \propto \sigma \sqrt{\frac{Q}{V}}$)
    * 2.2. Volume Profile (The "Smile")
    * 2.3. Why VWAP is the "Fair Price"
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Determine Total Volume to Trade ($Q$)
    * 3.2. Generate Historical Volume Curve (Profile)
    * 3.3. Slice Order into "Buckets" (1-minute intervals)
    * 3.4. Execute slices linearly within the bucket to match the curve
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Curve: $V(t)$
    * 4.2. Target Quantity $q(t) = Q \times \frac{V(t)}{\sum V(t)}$
    * 4.3. Tracking Error (Implementation Shortfall)
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. The "Whale" Splash (Moving the market 5% by mistake)
    * 5.2. IS (Implementation Shortfall) Algorithms vs VWAP
    * 5.3. Dark Pools usage to beat VWAP
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Fetching Historical Intraday Volume
    * 6.2. Generating the "Trading Schedule"
    * 6.3. Participation Rate Limiter (Max 10% of volume)
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Aggressive" VWAP (Front-loading)
    * 7.2. "Passive" VWAP (Back-loading / Capture Spread)
    * 7.3. POV (Percentage of Volume) - Dynamic Slicing
8. [Risk Management: The Price Drift](#8-risk-management-the-price-drift)
    * 8.1. Scenario: Price trends away from you all day.
    * 8.2. Result: You buy at the High of Day.
    * 8.3. Benchmark Performance: Did you beat the VWAP?
9. [Conclusion: The Invisible Hand](#9-conclusion-the-invisible-hand)

---

# 1. Executive Summary

**VWAP (Volume Weighted Average Price)** is not an Alpha strategy.
It is an **Execution Strategy**.
If GOLIATH wants to buy $10 Million of AAPL.
We cannot just hit "Market Buy".
The price would jump 2%. We would pay too much (Market Impact).
The VWAP Algo slices the order into thousands of tiny pieces and executes them over the day, exactly matching the market's natural volume rhythm.
The goal: **Zero Footprint.**

---

# 2. The Theory

### 2.1. The Volume Curve

Volume is not uniform.

* **Open (9:30 AM):** Huge Volume (15%).
* **Lunch (12:00 PM):** Low Volume (5%).
* **Close (3:55 PM):** Huge Volume (20%).
This creates a "U" shape or "Smile".
If you trade actively during Lunch (Low Liquidity), you move the price more than at the Close.
VWAP Algos trade *less* during Lunch and *more* at the Open/Close.

### 2.2. Square Root Law

Market Impact Cost ($C$) is proportional to Volatility ($\sigma$) and the Square Root of Order Size ($Q$) relative to Daily Volume ($V$).
$$ C \approx \sigma \sqrt{\frac{Q}{V}} $$
To minimize $C$, you must spread $Q$ over time such that $\frac{q(t)}{v(t)}$ is constant.

---

# 3. Strategy Rules

### 3.1. Schedule Generation

1. Look back 20 days.
2. Calculate average volume per 1-minute bin.
3. Normalize to get percentage curve. (e.g., Bin 1 = 1.2% total volume).
4. Apply to today's Order Size ($Q = 100,000$).
5. Bin 1 Target = 1,200 shares.

### 3.2. Execution

During Minute 1:

* We need to buy 1,200 shares.
* Do not dump 1,200 at second 0.
* Randomize execution over the 60 seconds.
* Use Limit Orders if possible (Passive VWAP) to save spread.
* If behind schedule at second 55, cross the spread (Aggressive Cleanup).

---

# 4. Mathematical Derivation

$$ Benchmark = \frac{\sum P_i V_i}{\sum V_i} $$
Your Price:
$$ P_{avg} = \frac{\sum P_{fill} Q_{fill}}{Q_{total}} $$
Performance = $P_{avg} - Benchmark$.
(For Buy orders, lower is better. For Sell orders, higher is better).
If Performance > 0 (Buy), you "Missed VWAP". (Bad).
If Performance < 0 (Buy), you "Beat VWAP". (Good).

---

# 5. Historical Case Studies

### 5.1. The Fat Finger

A trader intended to sell 100 contracts.
He sold 10,000 contracts "At Market".
The order book was wiped out.
Price dropped 10% in 1 second.
He was filled at the bottom.
Price rebounded instanty.
Loss: $5 Million.
An Algo would have prevented this by capping participation rate at 1% of volume.

### 5.2. Implementation Shortfall

VWAP is sometimes critized because it delays execution.
If news breaks at 10:00 AM and price rallies 5%.
The VWAP Algo is still buying slowly at 2:00 PM at the new high price.
**Solution:** IS Algo (Implementation Shortfall) which speeds up if price moves away.

---

# 6. Python Implementation

```python
import pandas as pd
import numpy as np

class VWAPAlgo:
    def __init__(self, total_qty, historical_volume_profile):
        self.Q = total_qty
        self.profile = historical_volume_profile # Series of % per bin
        self.executed_qty = 0
        self.schedule = self.generate_schedule()

    def generate_schedule(self):
        # Profile sums to 1.0 (100%)
        # Schedule = Q * Profile
        return (self.profile * self.Q).round().astype(int)

    def on_minute_tick(self, current_time, market_volume):
        # Determine how many shares we should have bought by now
        target_cumulative = self.schedule[:current_time].sum()
        
        needed = target_cumulative - self.executed_qty
        
        if needed > 0:
            print(f"Time {current_time}: Buying {needed} shares to match curve.")
            self.execute_slice(needed)
        else:
            print("Ahead of schedule. Pausing.")

    def execute_slice(self, qty):
        # In reality, this would split 'qty' into smaller child orders
        # randomizing timing and using limit orders.
        self.executed_qty += qty
```

### 6.3. Participation Rate

Constraint: Never be more than 10% of current interval volume.
If Schedule says "Buy 1000", but market only traded 5000 volume.
Limit Buy to 500 (10%).
Push the remaining 500 to the next bin.
This prevents "being the market" in low liquidity.

---

# 7. Optimization

### 7.1. Dark Aggregation

Before crossing spread on exchange, ping Dark Pools.
Dark Pools allow large blocks at Midpoint without impacting price.
"Seek Dark, then Lit".

### 7.2. Alpha Overlay

If Strategy Alpha signal is Strong Buy, accelerate the VWAP schedule (Front Load).
If Alpha is Weak, decelerate (Back Load) to pay less spread.
Dynamic Scheduling.

---

# 8. Risk Management

### 8.1. Opportunity Cost

The risk of VWAP is that the price runs away.
You get "Average Price" of the day.
But if the day is a +3% Trend Day, your average price is +1.5% higher than the Open.
A simple "TWAP" or "Market On Open" might have been better.

### 8.2. Information Leakage

Predatory HFTs look for patterns.
If they see a uniform buy order every minute.
They front run it.
**Solution:** Randomize size and timing (Gaussian Noise).

---

# 9. Conclusion

VWAP is the standard for Institutional Execution.
It is how Mutual Funds and Pension Funds move billions without crushing the market.
For GOLIATH, we use VWAP logic to exit our large Swing Positions.
We do not dump 1000 BTC in one click.
We feed it to the market over 6 hours using a VWAP curve.
It is professional, stealthy, and efficient.
