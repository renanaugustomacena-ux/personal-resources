# 86 - Tail Risk Hedging & Parity: The Universa Protocol

**Volume:** 86 of 100
**Strategy Type:** Crisis Alpha / Convexity / Asset Allocation
**Risk Profile:** Bleed (Cost of Carry) / Timing
**Mathematical Basis:** Jensen's Inequality, Extreme Value Theory (EVT), & Tail Risk Parity (Marginal Contribution to Tail Risk)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Assessing the Unthinkable](#2-the-theory-assessing-the-unthinkable)
    * 2.1. The Turkey Problem (Taleb).
    * 2.2. Concave vs Convex.
    * 2.3. Tail Risk Parity (Indicator 088): Allocating based on Crash Potential, not Volatility.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Construction: 97% Beta, 3% Alpha (Puts).
    * 3.2. Sizing: Use Tail Risk Parity to determine the "Beta" portion.
    * 3.3. Instrument: Deep OTM Puts (convexity).
    * 3.4. Monetization: Sell when Gamma peaks.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Geometric Returns.
    * 4.2. Expected Shortfall (ES) & Parity Condition.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. COVID-19 (March 2020): Universa returned 4000%.
    * 5.2. Crypto Winter: How Tail Parity would have saved you.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Black-Scholes for Puts.
    * 6.2. RiskFolio for Tail Parity.
7. [Run Strategy: "The Antifragile Allocation"](#7-run-strategy-the-antifragile-allocation)
8. [Risk Management: The Bleed](#8-risk-management-the-bleed)
9. [Conclusion: The Insurance](#9-conclusion-the-insurance)

---

# 1. Executive Summary

**Tail Risk Hedging** is the strategy of the Prepper.
We combine **Universa's Implementation** (Buying OTM Puts) with **Tail Risk Parity (Indicator 088)** (Allocating the rest of the portfolio).
Standard Risk Parity equalizes Volatility.
Tail Risk Parity equalizes **Expected Shortfall (ES)**.
It acknowledges that Crypto has a "Fat Left Tail" while Bonds might not.
The Strategy:

1. Allocate the "Safe" bucket using Tail Risk Parity (minimizing the chance of the bucket blowing up).
2. Use a fixed budget (3%/year) to buy "Insurance" (Puts) that pays off infinitely if the bucket *does* blow up.

---

# 2. The Theory

### 2.1. The Barbell

97% in Assets. 3% in Puts.
If Assets drop 50% ($0.97 \to 0.485$).
Puts rise 2000% ($0.03 \to 0.60$).
Total Portfolio: $1.085$ (+8.5%).
You make money in a Crash.

### 2.2. Tail Risk Parity (Indicator 088)

**Standard Risk Parity:** $w_{BTC} \sigma_{BTC} = w_{Gold} \sigma_{Gold}$.
Allocates too much to "Low Vol / High Crash" assets (like Yield Farming or Short Vol funds).
**Tail Risk Parity:** $w_{BTC} ES_{BTC} = w_{Gold} ES_{Gold}$.
Recognizes that Yield Farming has huge Tail Risk, so it allocates nearly zero.

---

# 3. Strategy Rules

### 3.1. The Budget

Allocating 30 bps (0.30%) per month to Puts.
Total annual cost ~3.6% (The "Bleed").

### 3.2. Allocation (The 97%)

Run Tail Risk Parity on the asset universe.
**Input:** Historical Returns (Extreme Value Theory adjusted).
**Output:** Weights that equalize "Doom Contribution".
**Result:** Higher allocation to Gold/Cash, Lower allocation to Crypto/Tech than standard MVO.

### 3.3. Monetization Rule

Sell Puts when:

1. VIX > 40.
2. Market down 20%.
3. Re-roll to lock in profits.

---

# 4. Mathematical Derivation

### 4.1. Expected Shortfall (ES)

$$ ES_\alpha = E[ L | L > VaR_\alpha ] $$

### 4.2. Marginal Contribution to Tail Risk (MCTR)

$$ MCTR_i = \frac{\partial ES_{port}}{\partial w_i} $$

### 4.3. Parity Condition

$$ w_i \times MCTR_i = w_j \times MCTR_j $$
We want each asset to contribute an equal amount of "Doom" to the portfolio.

---

# 6. Python Implementation (Production Grade)

### 6.1. Tail Risk Parity (RiskFolio)

```python
import riskfolio as rp
import pandas as pd

def compute_tail_parity_weights(prices):
    returns = prices.pct_change().dropna()
    port = rp.Portfolio(returns=returns)
    port.assets_stats(method_mu='hist', method_cov='hist')
    
    # 'CDaR' or 'CVaR' = Tail Measure
    # rm='CVaR' minimizes Conditional Value at Risk
    w = port.optimization(model='Classic', rm='CVaR', obj='MinRisk', hist=True, rf=0, l=0)
    return w
```

### 6.2. Universa Put Buying

```python
# (Black Scholes Implementation from original file)
def optimize_strike(S, T, r, current_iv, budget):
    # Find K that gives max Convexity (Gamma/Price)
    # ...
    return best_K
```

---

# 7. Run Strategy: "The Antifragile Allocation"

**Rules:**

1. **Universe:** BTC, ETH, Gold, Treasury.
2. **Step 1:** Calculate weights using Tail Risk Parity (Rule 088).
3. **Step 2:** Scale weights to 97% of capital.
4. **Step 3:** Use remaining 3% to buy 20% OTM Puts on the correlation driver (BTC or SPX).
5. **Outcome:** A portfolio that bleeds slightly in calm markets, but survives and thrives in Armageddon.

---

# 8. Risk Management

### 8.1. Bleed Death

The 3% drag sucks.
Must ensure Eqiuity Premium > 3%.
If Equity Premium is low (Stagflation), the strategy underperforms Cash.

### 8.2. Basis Risk

You hedge BTC but hold Alts.
Alts drop 90%, BTC drops 10%.
Your Hedge (BTC Puts) barely pays. Your Portfolio (Alts) is wiped out.
**Solution:** Tail Risk Parity naturally underweights Alts due to their extreme Tail Risk.

---

# 9. Conclusion

Tail Risk Hedging (Universa) + Tail Risk Parity (Sizing) is the **Fortress**.
Universa provides the walls (Puts).
Tail Risk Parity ensures the soldiers inside (Assets) are not standing next to a pile of explosives.
It is the strategy of the Survivor.
