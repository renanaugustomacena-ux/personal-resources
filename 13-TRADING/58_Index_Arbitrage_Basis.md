# 58 - Index Arbitrage: The Basis Trade

**Volume:** 58 of 100
**Strategy Type:** Arbitrage / Macro / Relative Value
**Risk Profile:** Dividend Risk / Execution Risk
**Mathematical Basis:** Cost of Carry Model ($F = S e^{(r-d)T}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Fair Value](#2-the-theory-fair-value)
    * 2.1. The Forward Price: Spot + Interest - Dividends.
    * 2.2. The Basis: Difference between Futures Price and Spot Index.
    * 2.3. Contango vs Backwardation: Why Futures usually trade at a premium.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Calculate Theoretical Fair Value (TFV).
    * 3.2. Identify Mispricing: Futures > TFV + Transaction Costs ("Rich").
    * 3.3. Execution (Rich Futures): Short Futures, Buy Index Basket (Program Trading).
    * 3.4. Execution (Cheap Futures): Long Futures, Sell Index Basket.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Continuous Compounding: $F = S e^{(r-q)T}$.
    * 4.2. Discrete Dividends: $F = S(1 + rT) - \sum D_i(1+rT_i)$.
    * 4.3. No-Arbitrage Bounds: $[F_{bid}, F_{ask}]$.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. 1987 Crash: Portfolio Insurance selling Futures crushed the Basis to a discount, triggering Program Trading selling of stocks.
    * 5.2. Japanese Bubble (1989): Nikkei Futures traded at massive premiums due to retail demand.
    * 5.3. Crypto "Cash and Carry": BTC Futures trading at 20% annualized premium (Contango) vs Spot.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Fetching Yield Curve (Risk Free Rate).
    * 6.2. Fetching Dividend Forecasts (Ex-Div dates).
    * 6.3. Calculating Real-time Fair Value.
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "E-Mini vs SPY": The modern Index Arb. Liquidity mismatch.
    * 7.2. "Dividend Swaps": Isolating the dividend risk.
    * 7.3. "Early Roll": Rolling futures positions before expiration to capture calendar spread aberrations.
8. [Risk Management: The Dividend](#8-risk-management-the-dividend)
    * 8.1. Dividend Cuts: If companies cut dividends, Fair Value rises. Short Futures position suffers.
    * 8.2. Interest Rate Spikes: $r$ increases -> Fair Value increases.
    * 8.3. "Pin Risk": Expiration convergence can be messy.
9. [Conclusion: The Program Trading Engine](#9-conclusion-the-program-trading-engine)

---

# 1. Executive Summary

**Index Arbitrage** ensures that the Futures market and the Stock market remain synchronized.
If S&P 500 Futures trade at 4050 and the underlying stocks trade at 4000, arbitrageurs calculate if the 50 point premium is "Fair".
If Fair Value is 4020, the Future is "Rich".
They **Short the Future** and **Buy the Stocks**.
This "Program Trading" locks in a risk-free profit of 30 points.
It connects the derivatives world to the real world.

---

# 2. The Theory

### 2.1. Cost of Carry

To own the index, you need cash ($S$).
To own the Future, you need ~5% margin.
The Future price must act *as if* you borrowed money to buy the stock.
$F = S + \text{Interest} - \text{Dividends}$.
If $F < S + I - D$, you buy the Future and Sell the Stock (invest cash at risk-free rate).

### 2.2. The Basis

$Basis = Future - Spot$.
Normally Positive (Contango) because Interest > Dividends.
Can be Negative (Backwardation) if Dividends > Interest or during Panic (Shorting pressure on Futures).

---

# 3. Strategy Rules

### 3.1. The Fair Value Calculation

Inputs:

* $S$: Current Index Level.
* $r$: Libor / SOFR rate to expiration.
* $D$: Sum of PV of all dividends before expiration.
* $T$: Time to expiration (years).

### 3.2. Execution

Wait for $Price_{Future} > FairValue + \text{Threshold}$.
Threshold covers:

* Bid-Ask Spread on 500 stocks.
* Commission.
* Market Impact.
Usually requiring a significantly large divergence (0.10% to 0.20%).

---

# 4. Mathematical Derivation

$$ Sensitivity = \frac{\partial F}{\partial r} = T S e^{(r-q)T} $$
Futures are sensitive to Rates.
If Rates rise 1%, Fair Value rises 1% on a 1-year contract.
This explains why Tech Stocks (Long Duration) fall when Rates rise: The arbitrage mechanism reprices the future cash flows instantly.

---

# 5. Historical Case Studies

### 5.1. Crypto Contango (2021)

BTC Spot: \$50,000.
BTC Future (3-month): \$55,000.
Basis: 10% in 3 months (40% annualized).
Trade: Long Spot, Short Future.
Risk-Free 40% yield.
Cause: Unbanking of crypto. Dollar shortage in the system.

### 5.2. The 1987 "Cascade"

Portfolio Insurance sold Futures to hedge.
Future price < Spot price (Discount).
Arb bots bought Futures, **Sold Spot Stocks**.
Selling Spot Stocks lowered the index further.
Portfolio Insurance sold MORE Futures.
Feedback loop crashed the market 22% in one day.
**Circuit Breakers** were invented to stop this.

---

# 6. Python Implementation

```python
import numpy as np

def calculate_fair_value(spot, rate, dividends, days_to_expiry):
    T = days_to_expiry / 365.0
    interest_cost = spot * rate * T
    fair_future = spot + interest_cost - dividends
    return fair_future

# Example S&P 500
S = 4000
r = 0.05
div_yield = 0.015
T = 0.25 # 3 months

# Simple continuous model
F = S * np.exp((r - div_yield) * T)
# F = 4000 * exp(0.035 * 0.25) = 4000 * 1.0087 = 4035

# If Market Price = 4050
# Arb Profit = 4050 - 4035 = 15 points
```

### 6.3. Modeling Dividends

Indices like SPX have discrete dividends.
A continuous yield approximation $e^{-qT}$ is wrong for short-term futures.
You must sum the individual dollar dividends of AAPL, MSFT, etc. expected before expiration.

---

# 7. Optimization

### 7.1. Early Unwind

You enter the arb at Basis = 30.
Ideally, wait for Expiration (Basis = 0).
But if market panic causes Basis = -10 (Discount) tomorrow:
Unwind early! Profit = 30 - (-10) = 40 points.
You captured the "Basis Volatility".

### 7.2. E-Mini Trade

Retail traders use ES (Futures) vs SPY (ETF).
Not perfect Arb (ETF fees, tracking error), but close enough.
High correlation.

---

# 8. Risk Management

### 8.1. Dividend Risk

You are Short the Future (Long the Dividend exposure).
If companies cancel dividends (e.g. 2020 Covid), your "Long Stock" spot leg pays you less than expected.
The Future price (Short leg) does not drop to compensate.
You lose money.

### 8.2. Rate Risk (Rho)

Arbs are typically Delta Neutral, but Rho sensitive.
Hedge with Eurodollar/SOFR futures if holding for months.

---

# 9. Conclusion

Index Arbitrage is the machine derived price of money.
It enforces the time value of money on the stock market.
For GOLIATH, we focus on **Crypto Basis** (Futures vs Spot) where inefficiencies are massive (5-10% APR).
In Equities, HFTs have eroded the edge to nanoseconds.
In Crypto, the edge is still minutes or hours wide due to fragmentation.
It is the strategy of the Yield Farmer.
