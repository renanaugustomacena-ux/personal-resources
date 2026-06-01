# 44 - Portfolio Rebalancing: Shannon's Demon

**Volume:** 44 of 50
**Strategy Type:** Portfolio Management / Volatility Harvesting / Mathematics
**Risk Profile:** Low Returns if Volatility is zero.
**Mathematical Basis:** Geometric Mean Maximization via Rebalancing.

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Creating Money from Noise](#2-the-theory-creating-money-from-noise)
    * 2.1. Claude Shannon's Lecture (1960s)
    * 2.2. The Coin Flip Game (Lose 50%, Gain 100%)
    * 2.3. Why "Buy and Hold" is mathematically inferior in high volatility.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Asset Allocation: 50% Stock, 50% Cash.
    * 3.2. Daily Rebalancing: If Stocks rise to 55%, Sell 5% to Cash.
    * 3.3. Daily Rebalancing: If Stocks fall to 45%, Buy 5% from Cash.
    * 3.4. Result: Buy Low, Sell High, systematically.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Expected Geometric Growth Rate: $g = E[\ln(1+R)]$
    * 4.2. Rebalancing Bonus $\approx \sigma^2 / 2 (1 - \sum w_i^2)$
    * 4.3. The "Demon" extracts geometric drag and turns it into excess return.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. The Lost Decade (2000-2010): S&P 500 return 0%. Rebalanced execution return +2% / year.
    * 5.2. Crypto volatility harvesting (BTC/USD 50/50 portfolio).
    * 5.3. Parrondo's Paradox: Two losing games combined to make a winning game.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Simulating Correlated Geometric Brownian Motion
    * 6.2. Analyzing Impact of Transaction Costs
    * 6.3. Optimal Rebalancing Frequency (Daily vs Threshold)
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. Threshold Rebalancing (Only rebalance if deviation > 5%)
    * 7.2. "Smart Rebalancing" (Rebalance on volatility spikes)
    * 7.3. Volatility Pumping (Leveraged ETFs decay vs Rebalancing Bonus)
8. [Risk Management: Transaction Costs](#8-risk-management-transaction-costs)
    * 8.1. Rebalancing too often burns Alpha via fees and taxes.
    * 8.2. Tax Drag: Short Term Capital Gains on every rebalance.
    * 8.3. "Trending Markets": Rebalancing sells winners too early. Underperforms Buy & Hold in strong Bull Markets.
9. [Conclusion: The Only Free Lunch](#9-conclusion-the-only-free-lunch)

---

# 1. Executive Summary

**Shannon's Demon** (named after Claude Shannon) proves that you can make money on an asset that has **zero expected return** but **high volatility**, simply by rebalancing against a non-correlated asset (Cash).
If a stock goes from 100 to 200 (Mean return +100%).
Then 200 to 100 (Mean return -50%).
Buy and Hold return: 0%.
Rebalancing Portfolio (50/50) return: Positive.
Why? Because you sold at 200 and bought back at 100.
Rebalancing forces you to "Buy Low and Sell High".

---

# 2. The Theory

### 2.1. The Math of Volatility Drag

If an asset moves +50% then -33.3%, it is back to start.
Arithmetic Mean: $(50 - 33.3) / 2 = +8.3\%$.
Geometric Mean: $\sqrt{1.5 \times 0.667} - 1 = 0\%$.
Buy and Hold earns the Geometric Mean.
Rebalancing allows you to harvest the difference between Arithmetic and Geometric mean.
This difference is the **Volatility Drag** turned into **Rebalancing Bonus**.

### 2.2. The Coin Toss Scenario

Game: Heads (+100%), Tails (-50%).
Arithmetic Expectation: +25% per toss.
Geometric Growth (Buy & Hold): $(2 \times 0.5)^{0.5} - 1 = 0\%$.
You make nothing.
**Shannon's Strategy:** Keep 50% of money in Cash. Rebalance every toss.
Growth Rate: $\sqrt{1.5 \times 0.75} \approx +6\%$ per toss.
You turn a 0% CAGR asset into a positive CAGR portfolio.

---

# 3. Strategy Rules

### 3.1. Construction

Stock A (Highly Volatile, e.g., TQQQ).
Asset B (Cash or Uncorrelated, e.g., TLT).
Target Weight: 50/50.

### 3.2. Execution

Check Drift daily.
If $w_A > 51\%$, Sell A, Buy B.
If $w_A < 49\%$, Buy A, Sell B.
This effectively shorts Volatility (Gamma Scalping).

---

# 4. Mathematical Derivation

Approximation for Rebalancing Bonus ($RB$):
$$ RB \approx \frac{1}{2} \sum_{i} w_i (1-w_i) (\sigma_i^2 - \sigma_i \sigma_j \rho_{ij}) $$
Simplified for 2 uncorrelated assets ($rho=0$) with equal weight ($w=0.5$):
$$ RB \approx \frac{1}{2} \times 0.5 \times 0.5 \times \sigma^2 = \frac{\sigma^2}{8} $$
If Volatility $\sigma = 40\%$ (0.4).
$RB = 0.16 / 8 = 0.02 = 2\%$.
You earn 2% extra return purely from rebalancing.

---

# 5. Historical Case Studies

### 5.1. Crypto (2018-2022)

Bitcoin vs USD.
A 50/50 portfolio rebalanced weekly outperformed 100% BTC HODL during the bear market.
Why? Because it sold the 2021 top (at $60k) and bought the 2022 bottom (at $16k).
HODLers rode it all the way up and all the way down.

### 5.2. Parrondo's Paradox

A combination of two losing games can be a winning game if played in alternating sequence.
Rebalancing is the financial equivalent of switching between "Risk On" and "Risk Off" based on capital weights.

---

# 6. Python Implementation

```python
import numpy as np
import pandas as pd

def shannon_demon_sim(returns, rebalance_freq=1):
    # returns: Series of asset returns
    # rebalance_freq: days
    
    cash = 1000.0
    stock_value = 1000.0
    total_wealth = 2000.0
    history = [total_wealth]
    
    for i, ret in enumerate(returns):
        # Update stock
        stock_value *= (1 + ret)
        
        # Rebalance?
        if i % rebalance_freq == 0:
            total_wealth = stock_value + cash
            target = total_wealth / 2.0
            
            # Action
            stock_value = target
            cash = target
            
        history.append(stock_value + cash)
        
    return pd.Series(history)
```

### 6.3. Friction

If trading costs 0.1%.
And Rebalancing Bonus is 0.01% per day.
Daily rebalancing destroys value.
**Optimal Frequency:** Rebalance when Benefit > Cost.
Usually Weekly or Monthly for stocks. Hourly for Crypto (if fees low).

---

# 7. Optimization

### 7.1. Threshold Bands

Instead of Time-Based (Daily).
Use Bands.
Rebalance only if Weight deviates by +/- 5%.
$45\% < w < 55\%$: Do Nothing.
$w > 55\%$: Sell to 50%.
This reduces turnover (fees) while capturing large moves.

### 7.2. Smart Rebalancing via Volatility

If Volatility increases, widen the bands.
Why? Because in high vol, mean reversion takes longer.
Let the winner run a bit more before cutting.

---

# 8. Risk Management

### 8.1. Tax Drag

In taxable accounts, every sale triggers Capital Gains Tax.
Short Term Rates (37%) kill the Rebalancing Bonus.
**Solution:** Only use this strategy in Tax-Advantaged accounts (IRA/401k) or with Futures (60/40 tax treatment).

### 8.2. Strong Trends

Rebalancing is "Anti-Momentum".
In a raging Bull Market (Nasdaq 1999), you keep selling the winner.
You underperform the Buy & Hold.
Use Shannon's Demon for "choppy" or "sideways" assets.
Use Momentum for trending assets.

---

# 9. Conclusion

Portfolio Rebalancing is not just housekeeping.
It is an active source of Alpha.
It extracts energy from volatility.
For GOLIATH, we rebalance our "Satellite" portfolios (High Volatility Altcoins) against BTC daily.
We treat BTC as the "Cash" equivalent in untrending Alts.
This accumulates more BTC over time without predicting direction.
Free lunch exists, if you have the discipline to eat it systematically.
