# 63 - Eurodollar / SOFR Ladders & The Taylor Rule

**Volume:** 63 of 100
**Strategy Type:** Fixed Income / Rates / Futures / Macro
**Risk Profile:** Rate Hike Surprise / Basis Risk / Gap Risk
**Mathematical Basis:** Implied Forward Rates & The Taylor Rule ($R_{target}$)

> "Central Bankers like to say they are 'Data Dependent'. The Taylor Rule is the algorithm they are dependent on."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Most Liquid Market on Earth](#2-the-theory-the-most-liquid-market-on-earth)
    * 2.1. SOFR Futures (formerly Eurodollars): The transition from Libor.
    * 2.2. The Mechanics: Price = 100 - Rate.
    * 2.3. The Curve: "Whites", "Reds", "Greens", "Blues".
3. [The Central Bank Algorithm: The Taylor Rule](#3-the-central-bank-algorithm-the-taylor-rule)
    * 3.1. John Taylor's 1993 Formula.
    * 3.2. Components: Inflation Gap vs Output Gap.
    * 3.3. The "Shadow Rate" and Policy Errors.
4. [The Strategy Rules](#4-the-strategy-rules)
    * 4.1. The "Policy Error" Trade (Taylor vs Market).
    * 4.2. Calendar Spreads: Betting on the Pivot.
    * 4.3. Butterfly Trades: Betting on Curvature/Humps.
    * 4.4. The "Pack" Trade: Buying the Reds.
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Taylor Rule Formula: $R = r^* + \pi + 0.5(\pi - \pi^*) + 0.5(y - y^*)$.
    * 5.2. Forward Rate from Futures: $F(T_1, T_2)$.
    * 5.3. Convexity Adjustment (Futures vs Forwards).
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. 1994 Bond Massacre (Greenspan's Surprise).
    * 6.2. 2022 Inflation: The Taylor Rule screamed "Hike" at 0%.
    * 6.3. The "Pivot Bros" of 2023.
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python Part A: Taylor Rule Model.
    * 7.2. Python Part B: SOFR Curve Analysis.
    * 7.3. Rust Part A: Taylor Model Struct.
    * 7.4. Rust Part B: SOFR Chain & Implied Hikes.
8. [Risk Management](#8-risk-management)
    * 8.1. FOMC Gap Risk.
    * 8.2. The TED Spread (Credit Risk).
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Strategy 63** is the "Central Bank Simulator" for GOLIATH. It combines the raw liquidity of **SOFR Futures (Strategy 63)** with the predictive logic of the **Taylor Rule (Indicator 064)**.

**The Edge:**
The Market is emotional. It prices based on fear, hope, and "Fed Speak".
The Taylor Rule is algorithmic. It prices based on Inflation and Growth data.
When the Market diverges from the Taylor Rule, a **Policy Error** is being priced.

* **Scenario A (Hawkish):** Taylor Rule says rates should be 6%. Market prices 4%. **Action:** Short SOFR Futures (Betting on rates rising).
* **Scenario B (Dovish):** Taylor Rule says rates should be 2%. Market prices 4%. **Action:** Long SOFR Futures (Betting on rates falling).

This strategy does not guess. It arbitrages the difference between "What the Fed *says* it will do" and "What the Economic Data *forces* the Fed to do".

---

# 2. The Theory: The Most Liquid Market on Earth

## 2.1. SOFR Futures

Secured Overnight Financing Rate (SOFR) replaced Eurodollars (Libor) as the global benchmark.
These futures contracts allow traders to hedge or speculate on the interest rate for a 3-month period starting at a future date.

* **Volume:** Trillions of dollars in notional value trade daily.
* **Participants:** Banks, Hedge Funds, Corporates, Sovereigns.

## 2.2. The Mechanics

$$ Price = 100 - Rate $$

* If the implied interest rate is 5.00%, the Future trades at 95.00.
* If rates rise to 6.00%, the Price falls to 94.00.
* **Long Futures = Long Bonds = Betting on Rates Falling.**
* **Short Futures = Short Bonds = Betting on Rates Rising.**
* **Tick Value:** 0.005 (1/2 basis point) = \$12.50 per contract. A 100bps move = \$2,500 per contract.

## 2.3. The Color Codes (The Curve)

Traders refer to contracts by their year grouping:

* **Whites:** First year (Contracts 1-4). Highly sensitive to immediate Fed meetings.
* **Reds:** Second year (Contracts 5-8). The "Belly" of the curve. Where the "Pivot" is usually priced.
* **Greens:** Third year.
* **Blues:** Fourth year.
* **Golds:** Fifth year.

---

# 3. The Central Bank Algorithm: The Taylor Rule

## 3.1. Historical Context

John Taylor (Stanford Economist) published his famous rule in 1993. It accurately described how the Fed under Paul Volcker and Alan Greenspan actually set rates, even though they claimed to be discretionary.
It essentially "solved" the problem of Monetary Policy by turning it into a feedback loop.

## 3.2. The Formula

$$ R_{target} = r^* + \pi_t + \alpha(\pi_t - \pi^*) + \beta(y_t - y^*) $$

* $R_{target}$: The nominal Fed Funds Rate.
* $r^*$: The Real Neutral Rate (R-Star). Historically 2%, now likely 0.5-1.0%.
* $\pi_t$: Current Inflation Rate (PCE).
* $\pi^*$: Fed's Inflation Target (2%).
* $y_t - y^*$: The Output Gap (GDP vs Potential GDP).

## 3.3. Interpretation

* **The Taylor Principle ($\alpha > 0$):** If inflation rises by 1%, the Fed must raise nominal rates by *more* than 1% to raise real rates. Usually $\alpha = 0.5$.
* **The Shadow Rate:** In Quantitative Easing (QE), the effective rate might be negative. The Taylor Rule can output -2%, signaling massive stimulus is needed.

---

# 4. The Strategy Rules

## 4.1. The "Policy Error" Trade

We run the Taylor Rule model daily using the latest CPI and GDP Nowcast data.

* **Input:** Implied Rate from "Red" SOFR Futures (Year 2).
* **Input:** Taylor Rule Target Rate.
* **Logic:**
  * If $Taylor > Market + 100bps$: **SHORT REDS.** (The Fed is behind the curve and must hike more than expected).
  * If $Taylor < Market - 100bps$: **LONG REDS.** (The Fed is too tight and must cut more than expected).

## 4.2. Calendar Spreads (The "Pivot")

The Market often prices "Higher for Longer" or "V-Shaped Cut".

* **Trade:** Long Dec 2024 / Short Dec 2025.
* **View:** "Rates will fall in 2024, but inflation will resurge in 2025."
* This isolates the *slope* between two years.

## 4.3. Butterfly Trades (Curvature)

* **Structure:** Long 1 Unit (Year 1) / Short 2 Units (Year 2) / Long 1 Unit (Year 3).
* **View:** The "Hump". Expecting Year 2 rates to be higher than Year 1 or Year 3.
* **Advantage:** Highly Mean Reverting.

---

# 5. Mathematical Derivation

## 5.1. Taylor Rule

Lets derived the standard parameterization:
$$ R = 2.0 + \pi + 0.5(\pi - 2.0) + 0.5(gap) $$
$$ R = 2.0 + 1.5\pi - 1.0 + 0.5gap $$
$$ R = 1.0 + 1.5\pi + 0.5gap $$
**Simplified Rule:** The Fed Funds rate should be 1% plus 1.5 times the inflation rate plus half the output gap.

## 5.2. Forward Rates

$$ F_{t,T} = \frac{(1+r_L)^{T_L}}{(1+r_S)^{T_S}} - 1 $$
This arbitrage relationship anchors the Futures price.

## 5.3. Convexity Adjustment

Futures are margined daily. Forwards are settled at maturity.
If Rates are negatively correlated with Bond Prices (which they are), Short Futures positions generate cash that can be reinvested at higher rates. Long positions lose cash that must be financed at higher rates.
**Result:** Futures Rates > Forward Rates.
$$ FuturesRate \approx ForwardRate + 0.5 \sigma^2 T $$

---

# 6. Historical Case Studies

## 6.1. 1994 Bond Massacre

The Fed hiked rates from 3% to 6% in 12 months.
The Market was caught offside.
Hedge Funds that were using the Taylor Rule (which showed booming growth and rising inflation) were Short Eurodollars and made fortunes.
Those who listened to the "Soft Landing" narrative were wiped out (Orange County Bankruptcy).

## 6.2. 2022 Inflation Spike

In early 2022, CPI hit 7%.
Fed Funds was 0.00-0.25%.
Taylor Rule Output: $1.0 + 1.5(7) + 0 \approx 11.5\%$ (Extreme) or at least 6-7%.
Market Pricing: Peak rate of 2.5%.
**The Trade:** Shorting Dec '22 SOFR Futures at 98.00 (2%). They settled at 95.00 (5%).
A massive alpha opportunity generated by a simple formula.

---

# 7. Implementation: Production Grade

## 7.1. Python Part A: Taylor Rule Model

```python
import pandas as pd
import numpy as np

def calculate_taylor_rule(cpi_yoy, gdp_growth, current_fed_funds):
    """
    Computes the Taylor Rule prescription and compares with current policy.
    
    Args:
        cpi_yoy (float): Current CPI Inflation % (e.g. 3.5)
        gdp_growth (float): Real GDP Growth % (e.g. 2.1)
        current_fed_funds (float): Effective Fed Funds Rate (e.g. 5.33)
        
    Returns:
        dict: Signal logic
    """
    # Parameters (Standard Taylor 1993)
    r_star = 0.5 # Updated for post-GFC era (0.5% Real Neutral)
    pi_target = 2.0
    potential_growth = 1.8 
    
    # Gaps
    inflation_gap = cpi_yoy - pi_target
    output_gap = gdp_growth - potential_growth
    
    # Formula
    # R = r* + pi + 0.5(pi-pi*) + 0.5(y-y*)
    target_rate = r_star + cpi_yoy + 0.5*(inflation_gap) + 0.5*(output_gap)
    
    # Differential
    diff = target_rate - current_fed_funds
    
    signal = "NEUTRAL"
    if diff > 1.0:
        signal = "HAWKISH_SURPRISE (Short Futures)"
    elif diff < -1.0:
        signal = "DOVISH_SURPRISE (Long Futures)"
        
    return {
        "Taylor_Rate": target_rate,
        "Market_Rate": current_fed_funds,
        "Spread": diff,
        "Signal": signal
    }
```

## 7.2. Python Part B: SOFR Curve Analysis

```python
def analyze_sofr_curve(prices_dict):
    """
    Analyzes the 'Hump' in the curve.
    prices_dict: {'SR3Z24': 95.50, 'SR3Z25': 96.00, ...}
    """
    rates = {k: 100 - v for k, v in prices_dict.items()}
    
    # Sort by maturity (pseudo-code)
    contracts = sorted(rates.keys()) 
    
    # Calculate Calendar Spreads
    spreads = []
    for i in range(len(contracts)-1):
        c1 = contracts[i]
        c2 = contracts[i+1]
        spread = rates[c2] - rates[c1] # Slope
        spreads.append((f"{c1}/{c2}", spread))
        
    return spreads
```

## 7.3. Rust Part A: Taylor Model Struct

```rust
pub struct TaylorParams {
    pub r_star: f64,
    pub pi_target: f64,
    pub alpha: f64,
    pub beta: f64,
}

impl TaylorParams {
    pub fn default() -> Self {
        Self {
            r_star: 0.5,
            pi_target: 2.0,
            alpha: 0.5,
            beta: 0.5,
        }
    }
    
    pub fn compute(&self, inflation: f64, output_gap: f64) -> f64 {
        self.r_star + inflation 
        + self.alpha * (inflation - self.pi_target) 
        + self.beta * output_gap
    }
}
```

## 7.4. Rust Part B: SOFR Chain

```rust
pub struct SofrContract {
    pub symbol: String,
    pub price: f64,
    pub expiry: u64, // Timestamp
}

impl SofrContract {
    pub fn implied_rate(&self) -> f64 {
        100.0 - self.price
    }
    
    pub fn dv01(&self) -> f64 {
        25.0 // $25 per basis point per contract
    }
}
```

---

# 8. Risk Management

## 8.1. FOMC Gap Risk

The Market moves 20-30bps instantly on a surprise FOMC statement.
**Rule:** Do not hold large naked positions into the release (2pm ET).
**Mitigation:** Use Options (Mid-Curve Straddles) to hedge the event risk.

## 8.2. The TED Spread

Difference between 3-Month Treasuries (Risk Free) and 3-Month Eurodollar/SOFR (Bank Credit Risk).
In a Financial Crisis (2008), this spread explodes.
If trading SOFR, you are theoretically taking Bank Credit risk (though SOFR is secured, unlike Libor).
**Monitoring:** If Spread > 50bps, Liquidity is vanishing. Reduce leverage.

---

# 9. Conclusion

**Strategy 63** is the Grown-Up table.
It does not care about "Lines on a Chart". It trades the fundamental cost of capital.
By calculating the **Taylor Rule**, we establish a "Fair Value" for interest rates.
By trading **SOFR Ladders**, we execute that view across the time dimension.
When the Fed is wrong (Policy Error), GOLIATH is right.
This strategy provides the "Ballast" for the portfolio, profiting from the slow, tectonic shifts in the Global Macro economy.
