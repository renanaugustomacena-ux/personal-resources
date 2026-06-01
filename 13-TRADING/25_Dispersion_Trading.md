# 25 - Dispersion Trading: The Correlation Bet

**Volume:** 25 of 50
**Strategy Type:** Volatility / Correlation Arbitrage
**Risk Profile:** Market Neutral / Tail Risk (Correlation Spike)
**Mathematical Basis:** Implied Correlation vs Realized Correlation

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Index Variance < Sum of Parts](#2-the-theory-index-variance--sum-of-parts)
    * 2.1. The "Dirty Secret" of Index Options
    * 2.2. Correlation is the key variable
    * 2.3. Why Single Names are expensive, Index is cheap? (Actually, usually opposite)
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Setup: Implied Correlation is High
    * 3.2. The Trade: Short Index Straddle (Sell Correlation) + Long Stock Straddles (Buy Volatility)
    * 3.3. The Metric: CBOE Implied Correlation Index (KCIC)
    * 3.4. The Payoff: Stocks move idiosyncratically, Index stays flat
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Portfolio Variance Formula: $\sigma_p^2 = \sum w_i^2 \sigma_i^2 + \sum_{i \neq j} w_i w_j \sigma_i \sigma_j \rho_{ij}$
    * 4.2. If $\rho = 1$, Index Vol = Avg Stock Vol.
    * 4.3. If $\rho = 0$, Index Vol $\ll$ Avg Stock Vol.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Earnings Season (Dispersion works best)
    * 5.2. The 2008 Crash (Correlation goes to 1.0 -> Strategy blows up)
    * 5.3. The 2017 Low Vol Regime (Stock pickers market)
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Calculating Implied Correlation from Option Chains
    * 6.2. Basket Replication (Top 50 weights of SPX)
    * 6.3. Delta/Vega Hedging the portfolio
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. ETF Dispersion (XLE vs Oil Majors)
    * 7.2. "Reverse Dispersion" (Long Correlation - buying index straddle)
    * 7.3. Variance Swaps (Institutional only)
8. [Risk Management: The Correlation 1.0 Event](#8-risk-management-the-correlation-10-event)
    * 8.1. Scenario: Market Crash.
    * 8.2. Result: All stocks move down together.
    * 8.3. Portfolio Hedge: Buy deep OTM Index Puts.
9. [Conclusion: The Sophisticated Edge](#9-conclusion-the-sophisticated-edge)

---

# 1. Executive Summary

**Dispersion Trading** is a bet that individual stocks will move more than the index they belong to.
If Apple goes up +5% and Microsoft goes down -5%, the S&P 500 stays flat (0%).

* **Result:** A Long Straddle on AAPL makes money. A Long Straddle on MSFT makes money. A Short Straddle on SPX makes money (it stayed flat).
* **Win-Win-Win.**
However, if AAPL and MSFT *both* go down -5%, the SPX goes down -5%.
* **Result:** You lose on the Short SPX Straddle.

You are betting on **Low Correlation**.

---

# 2. The Theory

### 2.1. Implied Correlation

Options on the Index are priced based on the market's expectation of future correlation.
If investors are terrified of a macro event (Fed, War), they bid up Index Puts.
Implied Correlation rises.
If investors are focused on Earnings (Micro), they bid up Single Stock Calls.
Implied Correlation falls.

### 2.2. The Opportunity

Often, Index Options are "Overpriced" relative to the basket of Single Stocks because of the demand for portfolio insurance.
Dispersion Traders sell this expensive Index Volatility and buy the cheaper Single Stock Volatility.

---

# 3. Strategy Rules

### 3.1. Selection

1. **Index:** S&P 500 (SPX) or Nasdaq 100 (NDX).
2. **Basket:** Top 50 components by weight. (Proxy for the index).
3. **Entry:** When `JCJ` (Impled Correlation Index) is at a historic high (> 80).

### 3.2. Execution

1. **Short:** sell ATM Straddle on SPX (Notional $10M).
2. **Long:** Buy ATM Straddles on Top 50 Stocks (Total Notional $10M).
3. **Ratio:** Weighted by Beta and Market Cap.

---

# 4. Mathematical Derivation

Variance of Index ($\sigma_I^2$) vs Variance of Constituents ($\sigma_i^2$):
$$ \sigma_I^2 \approx \rho_{avg} \cdot (\sum w_i \sigma_i)^2 $$
Where $\rho_{avg}$ is the average pair-wise correlation.
Rearranging:
$$ \rho_{implied} \approx \frac{\sigma_{I, implied}^2}{(\sum w_i \sigma_{i, implied})^2} $$
If Market Price of Index Vol is high, $\rho_{implied}$ is high.
If we believe Realized Correlation $\rho_{realized}$ will be lower, we Sell the Index.

---

# 5. Historical Case Studies

### 5.1. Earnings Season 2022

Tech stocks were moving wildly (+10%, -15%) on earnings.
But they were moving in *different directions*.
Meta crashed, Apple rallied.
The S&P 500 volatility was muted (15%), while Single Stock volatility was extreme (60%).
Dispersion Traders made a fortune.

### 5.2. The Correlation Spike (2008)

In Oct 2008, everything went to correlation 1.0.
Safety stocks fell. Tech stocks fell. Banks fell.
The Index fell 40%.
If you were Short Index Volatility without OTM Put protection, you were wiped out.
**Lesson:** Dispersion is short "Macro Risk".

---

# 6. Python Implementation

```python
import pandas as pd
import numpy as np

class DispersionStrategy:
    def __init__(self, index_symbol='SPX', components=['AAPL', 'MSFT', 'AMZN']):
        self.index = index_symbol
        self.components = components
        self.weights = {} # Market Cap weights

    def calculate_implied_correlation(self, index_iv, component_ivs):
        # Simplified approximate formula
        # sum_vol = sum(w_i * sigma_i)
        # rho = (sigma_index / sum_vol)^2
        
        weighted_sum_vol = 0
        for stock, iv in component_ivs.items():
            w = self.weights.get(stock, 0.05) # Assume equal weight simplified
            weighted_sum_vol += w * iv
            
        if weighted_sum_vol == 0: return 0
        
        rho = (index_iv / weighted_sum_vol) ** 2
        return min(max(rho, 0), 1)

    def screen_opportunity(self, market_data):
        # 1. Get IV of SPX
        # 2. Get IV of top 100 stocks
        # 3. Calculate implied rho
        # 4. Compare to historical realized correlation (last 30 days)
        
        # Realized Correlation:
        # returns_df.corr().mean().mean() (Average off-diagonal)
        pass

    def construct_portfolio(self):
        # Short 1 SPX Straddle
        # Long N Stock Straddles
        # Delta Neutralize each position
        pass
```

### 6.2. Gamma Consideration

Long Stock Straddles = Long Gamma.
Short Index Straddle = Short Gamma.
If stocks move a lot (idiosyncratically), your "Long Gamma PnL" > "Short Gamma Loss" from index.
You profit from the "net gamma" of the dispersion.

---

# 7. Optimization

### 7.1. Sector Dispersion

Instead of SPX, trade XLE (Energy).
Buy Straddles on XOM/CVX, Sell Straddle on XLE.
Bet: One oil major wins, the other loses, but Oil price stays range-bound.

### 7.2. Earnings Plays

Only buy straddles on stocks *reporting earnings*.
Sell Index (which doesn't report earnings) to hedge the market risk.
This isolates the "Earnings Alpha".

---

# 8. Risk Management

### 8.1. Tail Risk

Buying OTM Puts on the Index is mandatory.
If the market crashes 20%, implied correlation goes to 1.0.
Your Long Stock Straddles help, but Index Volatility will explode (Vega loss on short straddle).
The OTM Puts hedge the Vega/Gamma explosion.

### 8.2. Margin

Dispersion is capital intensive.
Requires Portfolio Margin (PM) account.
Reg T margin (retail) makes this strategy impossible (buying 50 straddles eats all buying power).

---

# 9. Conclusion

Dispersion is the arbitrage of structure.
It capitalizes on the fact that an Index is just a mathematical construct, while Companies are real distinct entities.
In healthy markets, companies diverge.
In unhealthy markets, they converge.
GOLIATH monitors `Implied_Corr - Realized_Corr`. When the spread is > 20 points, we deploy the Dispersion Bot.
It is the most sophisticated "Market Neutral" strategy available.
