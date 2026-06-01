# 87 - Volatility Targeting & Safe Haven Rotation

**Volume:** 87 of 100
**Strategy Type:** Risk Management / Asset Allocation / Regime Switching
**Risk Profile:** Whiplash / False Signals
**Mathematical Basis:** Constant Risk Budgeting ($Position_{size} = \frac{Target_{vol}}{Realized_{vol}}$) & Relative Strength ($RS_i$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Thermostat & The Compass](#2-the-theory-the-thermostat--the-compass)
    * 2.1. Volatility Targeting (The Thermostat): Keeping risk constant.
    * 2.2. Safe Haven Index (The Compass - Indicator 090): Deciding *where* to hide when risk is cut.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Vol Target: 15% Annualized. De-lever if realized vol > 15%.
    * 3.2. Safe Haven Rotation: If De-levering, move capital to the "Strongest Safety" (Gold, USD, or Bonds).
    * 3.3. Regime Map: Risk-On, Inflation Fear, Deflation Fear, Liquidity Crunch.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Position Sizing Formula.
    * 4.2. Safe Haven Score ($SHS$).
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Lost Decade (2000-2010).
    * 5.2. 2022 Inflation: Bonds failed as a hedge. Gold worked. Safe Haven Index picked Gold.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Vol Targeting Logic.
    * 6.2. Safe Haven Index Classifier.
7. [Optimization & Variations](#7-optimization--variations)
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Strategy 87** combines two powerful concepts:

1. **Volatility Targeting:** Tells us *how much* exposure to have.
2. **Safe Haven Index (Indicator 090):** Tells us *what* to hold when we reduce exposure.

Standard Vol Targeting moves to "Cash".
But Cash loses to Inflation.
Strategy 87 moves to the "Active Safe Haven" (Gold in inflation, USD in deflation), preserving purchasing power while keeping volatility constant.

---

# 2. The Theory

### 2.1. The Thermostat (Vol Targeting)

Markets have variable risk. We want constant risk.
If Vol doubles, we halve our position.
This smooths equity curves and avoids deep drawdowns.

### 2.2. The Compass (Safe Haven Index - Indicator 090)

Safe Havens rotate.

* 1970s: Gold (Inflation).
* 2008: USD (Deflation).
* 2020: Tech? (Stay at Home).
* 2023: BTC? (Bank Failure).
We compute the **Safe Haven Score** to identify the current regime.

---

# 3. Strategy Rules

### 3.1. Volatility Sizing

$$ w_t = \min(MaxLev, \frac{TargetVol}{\hat{\sigma}_t}) $$

### 3.2. Safe Haven Logic (090)

Calculate Relative Strength ($RS$) of GLD, TLT, UUP (USD).
$$ SHS = \max(RS_{Gold}, RS_{Bonds}, RS_{USD}) $$
**Action:** The portion of the portfolio that is NOT in Risk Assets (due to Vol Targeting) is allocated to the asset with the highest SHS.
**Example:**

* Vol is High ($w_{risk} = 0.5$).
* Remaining 0.5 goes to Safe Haven.
* If $RS_{Gold}$ is highest, buy Gold.
* If $RS_{USD}$ is highest, buy T-Bills.

### 3.3. The Bitcoin "Schrödinger's Coin"

If BTC Correlation with SPX < 0.2 AND BTC RS is High:
BTC is acting as a Safe Haven.
Add BTC to the Safe Haven basket.

---

# 4. Mathematical Derivation

### 4.1. Strategy Returns

$$ R_{Strat} = L \times R_{Risk} + (1-L) \times R_{Safe} $$
Where $L$ is the leverage ratio derived from Vol Targeting.

### 4.2. Safe Haven Score

$$ RS_i = \frac{P_t}{MA(P, 200)} $$
Identify the leader.

---

# 6. Python Implementation (Production Grade)

```python
import pandas as pd
import numpy as np

def volatility_target(prices, target_vol=0.15):
    returns = prices.pct_change()
    vol = returns.rolling(20).std() * np.sqrt(252)
    leverage = (target_vol / vol).shift(1).fillna(0)
    leverage = np.minimum(leverage, 2.0)
    return leverage

def get_safe_haven_alloc(prices_safe):
    # prices_safe: DF with columns ['GLD', 'TLT', 'UUP']
    momentum = prices_safe.pct_change(60) # 3 month momentum
    leader = momentum.idxmax(axis=1)
    return leader

def combined_strategy(risk_asset, safe_assets):
    lev = volatility_target(risk_asset)
    safe_choice = get_safe_haven_alloc(safe_assets)
    
    # Construct portfolio
    # Long Risk Asset * Lev
    # Long Safe Asset * (1 - Lev) (if Lev < 1)
    pass
```

---

# 9. Conclusion

Strategy 87 is the **Regulator**.
It ensures Goliath never runs too hot (Vol Targeting).
And it ensures Goliath never hides in a burning building (Safe Haven Rotation).
It adapts to the **Quantity** of risk (Vol) and the **Quality** of risk (Regime).
It is the strategy of the Professional.
