# 22 - The Short Iron Condor: Income from Stagnation

**Volume:** 22 of 50
**Strategy Type:** Volatility / Short Vega / Long Theta
**Risk Profile:** Defined Risk / High Win Rate / Low Reward
**Mathematical Basis:** Mean Reversion within a Range

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Selling Time](#2-the-theory-selling-time)
    * 2.1. Theta Decay accelerates near expiration
    * 2.2. The "Insurance Seller" Business Model
    * 2.3. Probability of Profit (POP) > 70%
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Setup: High IV Rank (> 50)
    * 3.2. Construction: Sell OTM Call spread + Sell OTM Put spread
    * 3.3. Strike Selection: 16 Delta (1 Standard Deviation)
    * 3.4. The Exit: 50% of Max Profit or 21 Days to Expiry
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Max Profit: Net Credit received
    * 4.2. Max Loss: Width of Strikes - Credit
    * 4.3. Greeks: Short Vega, Short Gamma, Long Theta
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. SPX Range Bound 2011-2012 (The "Condor Era")
    * 5.2. The "Volmageddon" (Feb 2018): Why short gamma kills
    * 5.3. Managing a tested side (Rolling the untest side)
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Selecting Strikes based on Delta
    * 6.2. Calculating PnL graph
    * 6.3. Monte Carlo simulation of Probability of Touch
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Iron Butterfly" (ATM Straddle with Wings)
    * 7.2. "Broken Wing Butterfly" (Directional bias)
    * 7.3. "Ratio Spreads" (Zero cost upside)
8. [Risk Management: The Rolling Defense](#8-risk-management-the-rolling-defense)
    * 8.1. Stop Loss: 2x Credit received?
    * 8.2. Adjustment: Roll "Up/Down" the untested side to collect more credit
    * 8.3. Position Sizing: 5% Max per earning cycle
9. [Conclusion: The Monthly Paycheck](#9-conclusion-the-monthly-paycheck)

---

# 1. Executive Summary

**The Short Iron Condor** is the bread and butter of income traders.
It bets that the price will stay **within a range** by expiration.
It is composed of two vertical spreads:

1. **Bull Put Spread:** Sell OTM Put, Buy further OTM Put.
2. **Bear Call Spread:** Sell OTM Call, Buy further OTM Call.
You collect a **Net Credit**. If the stock stays between the short strikes, you keep 100% of the credit.

---

# 2. The Theory

### 2.1. Selling Insurance

The market generally overprices volatility.
Realized Volatility < Implied Volatility (80% of the time).
Therefore, selling options has a positive expected value (Variance Risk Premium).
The Condor harvests this premium from both sides (Call and Put).

### 2.2. Delta Neutral

Initially, the position is Delta Neutral.
Does not care about small moves.
Cares about **Volatility Crush** (Vega dropping) and **Time Passing** (Theta decay).

---

# 3. Strategy Rules

### 3.1. Strike Selection

* **Short Strikes:** 16 Delta ($\approx 1$ Standard Deviation OTM).
* **Long Wings:** 5-10 Delta (Safety net).
* **Width:** $5, $10, or $20 wide. Wider = More Credit but More Risk.
* **Target Credit:** 1/3 the width of the wings. (e.g., if wings are $3 wide, collect $1 credit).

### 3.2. Duration

* **Best:** 45 Days to Expiration (DTE).
* **Management:** Manage at 21 DTE.
  * *Why?* The Gamma risk (price sensitivity) explodes in the last 2 weeks. Get out before the "Gamma Week".

---

# 4. Mathematical Derivation

$$ Max Profit = Credit $$
$$ Max Loss = Width - Credit $$
$$ Breakeven_{Upper} = Short Call + Credit $$
$$ Breakeven_{Lower} = Short Put - Credit $$

**Probability:**
A 16 Delta strangle has theoretically a 68% probability of expiring worthless (1 SD).
Empirically, it wins closer to 80% because of active management (closing winners early).

---

# 5. Historical Case Studies

### 5.1. The 2017 Grind

In 2017, SPX went up slowly with almost zero volatility (VIX 9).
Iron Condors printed money every month.
It was "Easy Money".

### 5.2. Feb 2018 (Volmageddon)

VIX spiked from 12 to 50 in one day.
Short Call spreads (Bearish bets) were destroyed as the market rallied? No.
Short Put spreads were destroyed as the market crashed 10%.
But Vega expansion hurt both sides.
The "Mark to Market" loss was 500% of the initial credit.
**Lesson:** Defined Risk saved traders from bankruptcy (Long Puts capped the loss), but max loss was realized instantly.

---

# 6. Python Implementation

```python
import numpy as np
from scipy.stats import norm

class IronCondorStrategy:
    def __init__(self, spot, iv, dte):
        self.spot = spot
        self.iv = iv
        self.dte = dte / 365.0
        self.r = 0.04 # Risk free

    def get_delta_strike(self, delta_target, call=True):
        # Inverse BS to find Strike from Delta
        # Approximation or Newton method needed for exact strike
        # Here we assume normal distribution logic (simple Z-score)
        
        # Z-score for delta
        # N(d1) = Delta. InverseCDF(Delta) = d1
        # d1 = (ln(S/K) + ...)
        
        # Simplified: Strike = Spot * exp(Z * sigma * sqrt(T))
        z = norm.ppf(delta_target if not call else 1-delta_target)
        # Note: Put Delta is usually negative in platforms (-0.16). 
        # Using 0.16 for calculation logic.
        
        move = z * self.iv * np.sqrt(self.dte)
        # Call Strike > Spot (Z positive), Put Strike < Spot (Z negative)
        
        strike = self.spot * np.exp(move)
        return strike

    def build_condor(self):
        # 1. Find Short Strikes (16 Delta)
        short_call = self.get_delta_strike(0.16, call=True)
        short_put = self.get_delta_strike(0.16, call=False)
        
        # 2. Find Long Wings (5 Delta)
        long_call = self.get_delta_strike(0.05, call=True)
        long_put = self.get_delta_strike(0.05, call=False)
        
        print(f"Sell Put: {short_put:.2f}, Buy Put: {long_put:.2f}")
        print(f"Sell Call: {short_call:.2f}, Buy Call: {long_call:.2f}")
        
        # Check Width consistency for risk
        width_call = long_call - short_call
        width_put = short_put - long_put
        
        print(f"Widths: Call {width_call:.2f}, Put {width_put:.2f}")
        return short_put, short_call

# Monte Carlo for Probability of Touch
def probability_of_touch(spot, barrier, iv, T, simulations=10000):
    # Does price hit barrier anytime before T?
    dt = T / 252 # Daily steps
    hits = 0
    for _ in range(simulations):
        price = spot
        for day in range(252):
            shock = np.random.normal(0, 1)
            price = price * np.exp( -0.5*iv**2*dt + iv*np.sqrt(dt)*shock )
            if (barrier > spot and price >= barrier) or (barrier < spot and price <= barrier):
                hits += 1
                break
    return hits / simulations
```

---

# 7. Optimization

### 7.1. Defense Mechanics

If the market rallies and threatens the Short Call (Delta goes from 0.16 to 0.30):

* **Action:** Roll the Put Spread **Up**.
* Move the Put Spread closer to the money to collect more credit.
* This lowers the Delta of the whole position closer to zero.
* It reduces value at risk.

### 7.2. Iron Butterfly

Instead of OTM puts/calls, sell the **ATM Straddle** and buy Out-of-the-Money wings.

* Credit: Huge.
* Probability: Lower (of full profit).
* Breakeven: Very wide.
* Use: When IV is historically extreme (Rank > 80).

---

# 8. Risk Management

### 8.1. Stop Loss

**Method:** 2x Credit.
If gathered $1.00 credit, stop out when spread trades at $3.00 (Net loss $2.00).
This prevents "Max Loss" scenarios.

### 8.2. Position Sizing

Condors are "High Probability, High Risk" trades.
You win small often, lose big rarely.
**Rule:** Never allocate more than 20% of the portfolio to defined risk short volatility.
One bad month can wipe out 6 months of gains if you size too big (Karen the Supertrader blowup).

---

# 9. Conclusion

The Iron Condor is the "professional" retail strategy.
It allows the trader to be the **Casino**.
Markets churn 70% of the time. Condors capture that churn.
For GOLIATH, we layer Condors on top of our Mean Reversion bots.
When the Mean Reversion bot says "Market is ranging", the Options bot deploys an Iron Condor to extract Theta while we wait.
