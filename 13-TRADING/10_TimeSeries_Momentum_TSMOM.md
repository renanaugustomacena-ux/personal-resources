# 10 - Time Series Momentum (TSMOM): The Academic Standard

**Volume:** 10 of 50
**Strategy Type:** Absolute Momentum / Trend Following
**Risk Profile:** Diversified / High Capacity
**Mathematical Basis:** Sign of Past 12-Month Return ($r_{t-12, t-1}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Seminal Paper: Moskowitz, Ooi, Pedersen (2012)](#2-the-seminal-paper-moskowitz-ooi-pedersen-2012)
    * 2.1. "Time Series Momentum" (Journal of Financial Economics)
    * 2.2. The Dataset: 58 Liquid Instruments over 25 Years
    * 2.3. The Finding: Positive auto-correlation for 1-12 months
3. [TSMOM vs CSMOM (Cross-Sectional Momentum)](#3-tsmom-vs-csmom-cross-sectional-momentum)
    * 3.1. CSMOM (Jegadeesh & Titman): Buy Winners, Sell Losers (Relative)
    * 3.2. TSMOM: Buy if Positive Return, Sell if Negative Return (Absolute)
    * 3.3. Why TSMOM performs better in crashes
4. [The Trading Logic: The Sign Rule](#4-the-trading-logic-the-sign-rule)
    * 4.1. Calculate Excess Return over lookback $k$
    * 4.2. Position = $\text{sign}(r_{t-k, t})$
    * 4.3. Volatility Scaling (Target Vol)
    * 4.4. The Portfolio Construction (Equal Weight vs Risk Parity)
5. [Mathematical Derivation: Volatility Targeting](#5-mathematical-derivation-volatility-targeting)
    * 5.1. Why scaling by $1/\sigma$ is critical
    * 5.2. The formula: $Size_t = \frac{\text{TargetVol}}{\sigma_t}$
    * 5.3. Ex-Ante vs Ex-Post Volatility
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. The Lost Decade for Stocks (2000-2010): TSMOM made money on Bonds/Commodities
    * 6.2. 2022 Inflation Spike: TSMOM Long Energy, Short Bonds, Short Stocks
7. [Python Implementation (Production Grade)](#7-python-implementation-production-grade)
    * 7.1. Computing Rolling Returns
    * 7.2. Implementing the Volatility Target mechanism
    * 7.3. Portfolio Aggregation logic
8. [Optimization & Variations](#8-optimization--variations)
    * 8.1. Ensemble Lookbacks (1M, 3M, 6M, 12M)
    * 8.2. Continuous Signal (Sigmoid) instead of Binary Sign
    * 8.3. The "Trend Smile"
9. [Conclusion: The Benchmark](#9-conclusion-the-benchmark)

---

# 1. Executive Summary

**Time Series Momentum (TSMOM)** is the academic name for Trend Following.
It asks a simple question: **"Is the asset price higher today than it was X months ago?"**
If Yes $\to$ Buy.
If No $\to$ Sell (Short).

Unlike Strategy 01 (SMA Crossover) which uses price averages, TSMOM uses raw **Past Returns**.
Crucially, it mandates **Volatility Scaling**. You do not buy "1 Unit" of everything. You buy "1 Unit of Risk". This means you hold huge positions in Bonds (Low Vol) and small positions in Bitcoin (High Vol).

---

# 2. The Moskowitz Paper (2012)

Tobias Moskowitz, Yao Hua Ooi, and Lasse Heje Pedersen published "Time Series Momentum" in 2012.
They analyzed Futures markets (Commodities, Currencies, Bonds, Equities) from 1985 to 2009.
**Key Findings:**

1. **Universality:** TSMOM works on *every* asset class.
2. **Persistence:** The effect persists for about 12 months, then reverses (Mean Reversion) at longer horizons.
3. **Crisis Alpha:** TSMOM performs best during extreme market stress (2008, 1987).

---

# 3. TSMOM vs CSMOM

* **Cross-Sectional (CSMOM):** "Buy Bitcoin because it went up *more* than Ethereum." (Relative Strength).
  * *Problem:* In a crash, *everything* goes down. Relative Strength buys the "least bad" asset, which still loses money.
* **Time-Series (TSMOM):** "Buy Bitcoin because it went up." (Absolute Strength).
  * *Advantage:* In a crash, the return becomes negative. TSMOM goes Short. It makes money on the way down.

---

# 4. The Trading Logic

### 4.1. The Sign Rule

For each asset $i$, calculate the return over the past 12 months ($r_{t-12, t}$).
$$ Signal_t^i = \text{sign}(r_{t-12, t}) $$

* If Return > 0, Signal = +1.
* If Return < 0, Signal = -1.

### 4.2. Volatility Scaling

This is non-negotiable.
$$ Position_t^i = Signal_t^i \times \frac{40\%}{\sigma_t^i} $$

* Target Volatility = 40% (Annualized).
* $\sigma_t^i$: Ex-ante annualized volatility of asset $i$.

---

# 5. Python Implementation

```python
import pandas as pd
import numpy as np

class TSMOMStrategy:
    def __init__(self, lookback_months=12, target_vol=0.40):
        self.lookback = int(lookback_months * 21) # Approx 252 days trading
        self.target_vol = target_vol

    def calculate_volatility(self, df, span=60):
        # Exponentially Weighted Volatility
        # Annualized (sqrt(252))
        returns = df['Close'].pct_change()
        vol = returns.ewm(span=span).std() * np.sqrt(252)
        return vol

    def generate_signals(self, df):
        # 1. Calculate Past Return
        # (Price_t - Price_t-k) / Price_t-k
        past_return = df['Close'].pct_change(periods=self.lookback)
        
        # 2. Determine Sign
        signal = np.sign(past_return)
        
        # 3. Calculate Ex-Ante Volatility
        vol = self.calculate_volatility(df)
        
        # 4. Volatility Scaling
        # Position Size (Leverage Factor)
        # Avoid division by zero
        # Cap leverage at e.g. 4x
        leverage = self.target_vol / vol.replace(0, np.inf)
        leverage = leverage.clip(0, 4.0) 
        
        # 5. Final Position
        df['Position'] = signal * leverage
        
        return df

    def backtest(self, df):
        df = self.generate_signals(df)
        
        # Strategy Returns
        # Return = Position(t-1) * AssetReturn(t)
        asset_return = df['Close'].pct_change()
        strategy_return = df['Position'].shift(1) * asset_return
        
        # Note: This is an "Excess Return" calculation assuming 0 cost of funding.
        # In reality, you pay risk-free rate on leverage.
        
        df['Strategy_Wealth'] = (1 + strategy_return).cumprod()
        return df
```

### 5.1. The "Portfolio" Effect

The true power of TSMOM comes from diversification.
If you run TSMOM on Bitcoin only, it's just a trend following strategy.
If you run TSMOM on **50 Uncorrelated Assets** (BTC, ETH, Gold, Oil, Euro, Yen, S&P500, Nasdaq, Treasuries, Wheat...), the Sharpe Ratio doubles.

* When Stocks crash, you are Short Stocks.
* When Inflation hits, you are Long Commodities.
* When Rates rise, you are Short Bonds.
It is the "All Weather" active strategy.

---

# 6. Optimization & Variations

### 6.1. Ensemble Lookbacks

Why choose 12 months?
Better approach: Average the signal across multiple lookbacks.
$$ Signal_{ensemble} = \frac{1}{3} (S_{1m} + S_{3m} + S_{12m}) $$
This smooths the transition. You might be 1/3 Long, 1/3 Short, 1/3 Neutral.

### 6.2. Continuous Signal

Instead of Binary (1 or -1), use a continuous function (Sigmoid or Tanh) of the z-scored return.
$$ Signal = \tanh(\frac{Return}{\sigma}) $$
This scales position size by conviction. Small return = small position.

---

# 7. Conclusion

Strategy 10 concludes the **Trend Following** volume.
TSMOM is the heavy artillery of the hedge fund world. It is robust, mathematically sound, and scalable to billions of dollars.
For GOLIATH, TSMOM forms the **Core Beta** allocation. We use ML to enhance the signal, but the foundational logic remains: "If it's going up, buy it. If it's volatile, buy less of it."
