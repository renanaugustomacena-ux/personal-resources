# 55 - Variance Swaps: The Log Contract

**Volume:** 55 of 100
**Strategy Type:** Volatility Arbitrage / Exotic Derivatives / Quantitative
**Risk Profile:** Convexity Risk / Tail Risk (Short Variance)
**Mathematical Basis:** Static Replication of the Log Profile ($1/K^2$ weighting)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Beyond Vega](#2-the-theory-beyond-vega)
    * 2.1. Why Options are "Path Dependent" (Delta Hedging Noise).
    * 2.2. The Variance Swap: A contract that pays $(\sigma_{realized}^2 - \sigma_{strike}^2) \times \text{Vega Notional}$.
    * 2.3. Convexity: Why Variance > Volatility squared.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Construct the "Log Contract": Buy OTM Puts and Calls at every strike.
    * 3.2. Weighting: Amount to buy $\propto 1/K^2$.
    * 3.3. Execution: If Premium of strip < Realized Variance forecast -> Buy.
    * 3.4. Result: Pure exposure to realized volatility, no Delta hedging needed.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Carr-Madan Formula: Any payoff $f(S_T)$ can be replicated by options.
    * 4.2. For Variance, $f(S_T) = \ln(S_T/S_0)$.
    * 4.3. The VIX Calculation: VIX is literally the square root of a 30-day Variance Swap price.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Global Financial Crisis (2008): Variance Swaps struck at 20 vol paid out at 80 vol. (Payout = $80^2 - 20^2 = 6400 - 400 = 6000$ points).
    * 5.2. Volmageddon (Feb 2018): Short VIX products imploded due to Variance Spike.
    * 5.3. Structured Products: Banks selling "Corridor Variance Swaps".
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Replicating the VIX Index mechanics.
    * 6.2. Integrating the Option Chain ($\int \frac{1}{K^2} P(K) dK$).
    * 6.3. Calculating the "Fair Value" of Variance.
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Gamma Swaps": Weighted by $S/K$. Measures realized skew.
    * 7.2. "Corridor Variance": Only counts variance if price stays within a range.
    * 7.3. "Dispersion Trading": Long Single Stock Variance vs Short Index Variance.
8. [Risk Management: The Convexity](#8-risk-management-the-convexity)
    * 8.1. Capped Variance Swaps: Why banks stop selling uncapped variance.
    * 8.2. Jump Risk: A gap down of 20% adds massive variance.
    * 8.3. Liquidity: Replicating a strip requires hundreds of strikes. Only feasible on SPX.
9. [Conclusion: The Purest Alpha](#9-conclusion-the-purest-alpha)

---

# 1. Executive Summary

**Variance Swaps** allow traders to bet on the magnitude of price movement, regardless of direction.
Unlike a Straddle (which requires Delta Hedging and suffers form Theta decay), a Variance Swap offers a linear payout to **Variance** (Squared Volatility).
The "Swap Rate" (Strike) is implied by the market prices of options.
If Realized Variance ends up higher than Implied Variance, the Long side wins.
Because Variance is convex ($Vol^2$), expected profits are massive in crisis scenarios.

---

# 2. The Theory

### 2.1. Path Independence

A Delta-Hedged Straddle's P&L depends on *when* the volatility happens. (Did you re-hedge at the high or low?).
A Variance Swap P&L depends ONLY on the sum of squared daily returns.
$Payoff = N_{vega} \times (\sigma_{real}^2 - K_{var})$.

### 2.2. Convexity

A move from 10% vol to 20% vol is a $300$ point gain ($400 - 100$).
A move from 20% vol to 30% vol is a $500$ point gain ($900 - 400$).
Shorting Variance is dangerous.
Longing Variance is a "Convex Hedge".

---

# 3. Strategy Rules

### 3.1. Replication Portfolio

You cannot buy a VarSwap on retail platforms.
You MUST replicate it.

1. Buy OTM Puts ($K < S_0$).
2. Buy OTM Calls ($K > S_0$).
3. Weight of each option = $\frac{2}{T} \frac{\Delta K}{K^2} e^{RT}$.
4. Delta Hedge continuously (or use Futures to replicate the forward).

### 3.2. The VIX Trade

Buying VIX Futures or Options is effectively buying a forward-starting Variance Swap.
The VIX Index *is* the 30-day Variance Swap Rate.

---

# 4. Mathematical Derivation

The Carr-Madan Formula for Variance:
$$ E[V] = \frac{2}{T} e^{RT} \left( \int_0^{F} \frac{1}{K^2} P(K) dK + \int_F^{\infty} \frac{1}{K^2} C(K) dK \right) $$
Where:
$P(K)$ = Put Price at strike K.
$C(K)$ = Call Price at strike K.
$F$ = Forward Price.
This integral means: "Sum up the prices of all OTM options, weighted by inverse square of strike."
Distant OTM Puts have HUGE weights because $1/K^2$ is large for small K.
This is why "Crash Puts" drive the VIX.

---

# 5. Historical Case Studies

### 5.1. 2008 Crisis

Implied Variance (VIX) was 20.
Realized Variance hit 80.
$Payout = 80^2 - 20^2 = 6400 - 400 = 6000$.
A \$100,000 Vega Notional trade made \$600 Million profit.
This convexity bankrupted several structured credit desks.

### 5.2. Dispersion (2000-2002)

Tech stocks had High Vol. S&P 500 had Low Vol.
Strategy: Short Index Variance, Long Component Variance.
As correlations broke down, single stocks moved wildly while index stayed flat.
Massive profits for correlation desks.

---

# 6. Python Implementation

```python
import pandas as pd
import numpy as np

def calculate_vix_style_variance(options_chain, T, R):
    # options_chain: DataFrame with [Strike, Price, Type]
    # T: Time to expiry in years
    # R: Risk free rate
    
    # 1. Filter OTM options
    puts = options_chain[options_chain['Type'] == 'Put']
    calls = options_chain[options_chain['Type'] == 'Call']
    
    # 2. Sort by Strike
    chain = pd.concat([puts, calls]).sort_values('Strike')
    
    # 3. Calculate dK (difference between strikes)
    chain['dK'] = (chain['Strike'].shift(-1) - chain['Strike'].shift(1)) / 2
    
    # 4. Calculate Contribution: (dK / K^2) * Price * exp(RT)
    chain['contribution'] = (chain['dK'] / chain['Strike']**2) * chain['Price'] * np.exp(R*T)
    
    # 5. Sum and Scale
    variance = (2/T) * chain['contribution'].sum()
    vix = np.sqrt(variance) * 100
    
    return vix

# Note: This is simplified. Real VIX calculation handles measuring the "Forward" price precisely.
```

---

# 7. Optimization

### 7.1. Gamma Swaps

Weight by $1/K$ instead of $1/K^2$.
Reduces the sensitivity to extreme downside (Small K).
More robust to skew changes.

### 7.2. Approximations

Just buying the ATM Straddle + 1 OTM Strangle captures 90% of variance.
The "tails" (strikes far away) only matter for extreme events.

---

# 8. Risk Management

### 8.1. Time Decay

Holding a Variance Swap costs money if realized vol is low.
The "Variance Risk Premium" is usually negative (Realized < Implied).
Being Long Variance is a "Bleed" strategy.

### 8.2. Synchronization

Data must be clean.
Strike prices must be aligned.
One bad quote on a deep OTM put can blow up the calculation.

---

# 9. Conclusion

The **Variance Swap** is the "Dark Matter" of finance.
It is invisible index that drives all option pricing.
Understanding it allows you to see the "Fear Gauge" (VIX) not as a magical number, but as a mechanical sum of option prices.
For GOLIATH, we use synthetic variance swaps to hedge tail risk.
We buy the "Log Contract" cheap when the curve is flat, and sell it when the curve is steep.
It is the ultimate hedge against the Unknown Unknowns.
