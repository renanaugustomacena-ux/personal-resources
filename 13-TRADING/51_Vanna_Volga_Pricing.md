# 51 - Vanna-Volga Pricing: Trading the Smile

**Volume:** 51 of 100
**Strategy Type:** Options Market Making / Exotic Derivatives / Volatility Trading
**Risk Profile:** Kurtosis Risk / Model Risk
**Mathematical Basis:** Second-Order Greeks ($\frac{\partial^2 C}{\partial S \partial \sigma} \text{ and } \frac{\partial^2 C}{\partial \sigma^2}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Beyond Black-Scholes](#2-the-theory-beyond-black-scholes)
    * 2.1. The Implied Volatility Surface (The Smile).
    * 2.2. Vanna: How Delta changes when Volatility changes.
    * 2.3. Volga (Vomma): How Vega changes when Volatility changes.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Construct the Replication Portfolio (ATM, 25-Delta Call, 25-Delta Put).
    * 3.2. Identify Mispricing: Compare Market Smile vs Theoretical Smile.
    * 3.3. Execution: Buy "Cheap" Convexity (Volga) or "Cheap" Skew (Vanna).
    * 3.4. Hedging: Delta Neutral, Vega Neutral. Pure exposure to 2nd order greeks.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Vanna-Volga Weights ($w_{ATM}, w_{RR}, w_{BF}$).
    * 4.2. Pricing Formula: $Price_{exotic} \approx Price_{BS} + w_{RR} Price_{RR} + w_{BF} Price_{BF}$.
    * 4.3. Interpretation: Adjusting Black-Scholes for Probability of Extreme Moves.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. FX Option Markets: The standard for pricing Barrier Options.
    * 5.2. Brexit Vote (GBP/USD): Vanna-Volga costs spiked 500% as dealers feared "Gap Risk".
    * 5.3. 2020 Covid Crash: Volga exploded as Volatility of Volatility went parabolic.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Analytical Greeks (Closed Form).
    * 6.2. Finite Difference Approximations.
    * 6.3. Smiling the Surface (Cubic Spline Interpolation).
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Vanna-Volga Optimization": Minimizing hedging costs for exotics.
    * 7.2. "DVOL (DeFi Volatility)": Trading on-chain smile via Squeeth.
    * 7.3. "Correlation Skew": Multi-asset Vanna.
8. [Risk Management: The Wings](#8-risk-management-the-wings)
    * 8.1. Pin Risk: What happens at expiration?
    * 8.2. Liquidity Holes: OTM options have wide spreads.
    * 8.3. Model Breakdown: When Smile turns into a Smirk (Crash).
9. [Conclusion: The Professional's Edge](#9-conclusion-the-professionals-edge)

---

# 1. Executive Summary

**Vanna-Volga Pricing** is the "Secret Sauce" of FX dealers.
Black-Scholes assumes constant volatility (Flat Surface).
Reality has a **Smile** (OTM Puts are expensive) and **Kurtosis** (Fat Tails).
Instead of using complex Stochastic Volatility models (Heston), traders use a robust heuristic:
"Replicate the risk of the Exotic option using a basket of Liquid Vanilla options."
By trading **Vanna** and **Volga**, you are trading the **Shape** of the implied volatility surface itself.

---

# 2. The Theory

### 2.1. Vanna ($\partial \Delta / \partial \sigma$)

Sensitivity of Delta to Volatility.
Also: Sensitivity of Vega to Spot price ($\partial \nu / \partial S$).
If you are Short Vanna, you get shorter Delta as Volatility rises.
This is dangerous in a crash (Vol up, Price down).

### 2.2. Volga ($\partial \nu / \partial \sigma$)

Sensitivity of Vega to Volatility (Convexity of Vega).
If you are Long Volga, your Vega increases as Volatility rises.
You make money "faster" when Volatility explodes.
Long OTM Strangle = Long Volga.

---

# 3. Strategy Rules

### 3.1. The Vanna-Volga Method (VV)

To price an illiquid option (e.g., Strike K=80):

1. Find the costs of 3 liquid instruments:
    * ATM Straddle (Vega exposure).
    * 25-Delta Risk Reversal (Skew/Vanna exposure).
    * 25-Delta Butterfly (Kurtosis/Volga exposure).
2. Calculate how much of each you need to replicate the K=80 option's sensitivities.
3. The VV Price is the sum of these costs.

### 3.2. Trading the Dislocation

If the market price of the K=80 option is **lower** than the VV Price:
**Buy the Option.**
**Hedge** by selling the replication portfolio (Short Straddle, Short RR, Short Fly).
You have "locked in" the arbitrage between the specific strike and the liquid surface.

---

# 4. Mathematical Derivation

The adjustment to Black-Scholes price ($C_{BS}$):
$$ C_{VV} = C_{BS} + \frac{\partial C}{\partial \sigma} \Delta \sigma_{ATM} + \frac{\partial^2 C}{\partial \sigma \partial S} \text{Cost}_{Vanna} + \frac{\partial^2 C}{\partial \sigma^2} \text{Cost}_{Volga} $$
This decomposes the price into:

1. Flat Vol cost.
2. Skew cost (Vanna).
3. Curvature cost (Volga).

---

# 5. Historical Case Studies

### 5.1. Brexit (GBP/USD)

Before the vote, OTM Puts on GBP became incredibly expensive.
The Skew (Risk Reversal) went to historic lows.
Traders using simple Black-Scholes sold Puts thinking "Implied Vol is too high (20%)".
Realized Vol was only 10%.
But the **Vanna** exposure killed them when GBP dropped 10% overnight.
VV Pricing correctly priced in the "Gap Risk".

### 5.2. Target Accumulators (Exotics)

Structured products sold to corporates.
"Buy EUR at 1.10 every day unless it hits 1.20".
Banks hedge this using Vanna-Volga mapping.
When EUR crashed, the "Vanna" spiral forced banks to sell EUR, driving it lower.

---

# 6. Python Implementation

```python
import numpy as np
from scipy.stats import norm

def calculate_greeks(S, K, T, r, sigma):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    delta = norm.cdf(d1)
    vega = S * norm.pdf(d1) * np.sqrt(T)
    
    # Second Order
    vanna = -norm.pdf(d1) * d2 / sigma
    volga = vega * d1 * d2 / sigma
    
    return delta, vega, vanna, volga

def vanna_volga_weights(K_target, K1, K2, K3):
    # Solves the linear system to find weights w1, w2, w3
    # such that Vega, Vanna, Volga match the target.
    # Simplified Matrix inversion would go here.
    return np.array([0.5, 0.3, 0.2]) # Dummy weights
```

### 6.3. Spline Interpolation

In production, we don't just use 3 points.
We fit a **Cubic Spline** through all available strikes (10-Delta, 25-Delta, ATM...).
This creates a continuous Smile curve $\sigma(K)$.
Any deviation of a specific option price from this curve is an arb opportunity.

---

# 7. Optimization

### 7.1. Dynamic Hedging

Vanna change is slow.
Volga change is fast.
You might hedge Vega daily, but hedge Volga weekly.
Balancing Gamma hedging (Price moves) vs Vanna hedging (Vol moves) is the art of the volatility trader.

### 7.2. Skew Trading

If Vanna is high, it means the market expects a crash.
You can trade the "Risk Reversal": Buy Call / Sell Put.
If the market calms down, the Skew flattens, and you profit from the "Vanna Decay".

---

# 8. Risk Management

### 8.1. Model Risk

VV Pricing is an approximation.
It fails if the Smile is "W-shaped" (Bi-modal distribution).
It assumes the Smile moves in predictable ways (Sticky Strike vs Sticky Delta).

### 8.2. Transaction Costs

Rebalancing a 4-leg structure (Target + 3 Hedges) incurs 4x Spread.
Only viable for Market Makers or Institutional players with low fees.

---

# 9. Conclusion

Vanna-Volga is the language of the professional derivatives desk.
It moves beyond "Buying Volatility" to "Buying the Shape of Volatility".
In GOLIATH, we use VV pricing to detect mispriced OTM options on crypto exchanges (Deribit).
Often, the "Tail" (10-Delta Put) is underpriced relative to the ATM Volatility, offering a "Volga Arbitrage" opportunity.
It is the strategy of the Convexity Hunter.
