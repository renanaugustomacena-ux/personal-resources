# 01 - Trend Following & Momentum: The "Beta" Hunters

**Volume:** 01 of 07
**Date:** 2026-02-18
**Author:** Antigravity (Senior Quantitative Researcher)
**Word Count Target:** >4000 Words
**Classification:** ACADEMIC / ALGORITHMIC REFERENCE

---

# Table of Contents

1. [Introduction: The Philosophy of Persistence](#1-introduction-the-philosophy-of-persistence)
    * 1.1. Behavioral Finance: Why Trends Exist
    * 1.2. The "Cut Losses, Let Profits Run" Mathematical Proof
    * 1.3. Skewness and Kurtosis Profile of Trend Strategies
2. [Moving Averages: The Smoothing Filters](#2-moving-averages-the-smoothing-filters)
    * 2.1. Simple Moving Average (SMA) - The Lag Problem
    * 2.2. Exponential Moving Average (EMA) - Weighting Recency
    * 2.3. The Hull Moving Average (HMA) - Eliminating Lag via Geomean
    * 2.4. Adaptive Moving Averages (KAMA, ALMA)
    * 2.5. Strategy: The "Golden Cross" (50/200) Analysis
3. [Breakout Systems: The Turtle Trading Experiment](#3-breakout-systems-the-turtle-trading-experiment)
    * 3.1. Richard Dennis & The experiment
    * 3.2. Donchian Channels: The Mathematics of $N$-day Highs
    * 3.3. System 1 vs System 2 (Short vs Long Term)
    * 3.4. Money Management: The $N$ Unit Sizing Algorithm
    * 3.5. Pyramiding: Adding to Winners
4. [Time-Series Momentum (TSMomp): The Academic Standard](#4-time-series-momentum-tsmomp-the-academic-standard)
    * 4.1. Moskowitz, Ooi, Pedersen (2012)
    * 4.2. Returns Calculation: $r_{t,t-12}$
    * 4.3. Volatility Scaling: The $\frac{40\%}{\sigma_t}$ Target
    * 4.4. Portfolio Construction across Asset Classes
5. [Implementation Guide (Python/Pandas)](#5-implementation-guide-pythonpandas)
    * 5.1. Vectorized Backtesting with Pandas
    * 5.2. Handling Look-Ahead Bias
    * 5.3. Transaction Costs & Slippage Modeling

---

# 1. Introduction: The Philosophy of Persistence

Trend Following is the oldest, most robust, and arguably most scientifically validated trading strategy in financial history. It predates computers, finding its roots in the rice markets of 18th-century Japan (Munehisa Homma) and the early schematic logic of David Ricardo ("Cut short your losses, let your profits run on").

Unlike "Fundamental Analysis," which seeks to determine the *value* of an asset ($V$) and compare it to its *price* ($P$) to find a discrepancy ($V \neq P$), Trend Following is entirely agnostic to value. A trend follower does not care *what* they are trading—be it Gold (XAUUSD), Apple stock, or Lean Hogs futures. They only care *what the price is doing*.

### 1.1. Behavioral Finance: Why Trends Exist

The Efficient Market Hypothesis (EMH) in its strong form suggests that price changes are random walks; past prices cannot predict future prices. Trend Following effectively refutes the strong-form EMH. Why? Because market participants are **not rational agents**.

1. **Anchoring Bias:** Traders "anchor" to old prices. When a new fundamental catalyst hits (e.g., inflation rises), traders are slow to update their valuation models. They sell the rally, thinking it's "too expensive" based on yesterday's price. This rigorous selling slows the price adjustment, creating a gradual "trend" rather than an instantaneous gap to the new fair value.
2. **Herding Behavior:** Once a trend is established, late-stage retail and institutional FOMO (Fear Of Missing Out) drives prices beyond their fundamental value (Overshoot).
3. **Disposition Effect:** Investors tend to sell winners too early (to lock in a gain) and hold losers too long (hoping to break even). This behavior creates resistance levels in downtrends and support levels in uptrends, smoothing out the path of prices.

**Mathematical Implication:** Price series exhibit **positive serial correlation** (autocorrelation) at active horizons (1-12 months).
$$ Corr(r_t, r_{t-1}) > 0 $$

### 1.2. The "Cut Losses, Let Profits Run" Mathematical Proof

The adage is not just advice; it is a statistical necessity for Trend Following because the strategy has a **low win rate** (typically 30-40%).

Let:

* $P_w$: Probability of a winning trade (Win Rate).
* $P_l$: Probability of a losing trade (Loss Rate = $1 - P_w$).
* $AVG_w$: Average profit on a winning trade.
* $AVG_l$: Average loss on a losing trade.

The Expectancy ($E$) of the system is:
$$ E = (P_w \times AVG_w) - (P_l \times AVG_l) $$

For a Trend Follower, $P_w \approx 0.35$.
If $AVG_w = AVG_l$ (Risk:Reward 1:1), the system fails:
$$ E = (0.35 \times 1) - (0.65 \times 1) = -0.30 $$

To be profitable, the "Payoff Ratio" ($AVG_w / AVG_l$) must be massive.
If we "Let Profits Run" such that $AVG_w = 4 \times AVG_l$:
$$ E = (0.35 \times 4) - (0.65 \times 1) = 1.40 - 0.65 = +0.75 $$

**Conclusion:** A Trend Follower *must* accept many small losses (whipsaws) to catch the single "fat tail" event (the 2008 crash, the 2020 COVID volatility, the 2024 AI boom) that pays for all the losses 10x over.

### 1.3. Skewness and Kurtosis Profile

Trend Following return distributions are **Positively Skewed** (Right Skewed).

* **Mean Reversion strategies** (selling volatility) have *Negative Skew*: they make small money every day (Sharpe 3.0) until they blow up in one day (e.g., LTCM, Option sellers).
* **Trend strategies** have *Positive Skew*: they lose small money every day (bleed) until they make a fortune in one month.

Institutional investors allocate to Trend Following (CTAs) specifically for this **Crisis Alpha**. When the S&P 500 crashes (-20%), Trend Followers are usually Short stocks and Long volatility, generating +20% returns. They are the ultimate portfolio diversifier.

---

# 2. Moving Averages: The Smoothing Filters

Moving averages (MAs) are the "Hello World" of quantitative finance. They act as low-pass filters, removing high-frequency noise (volatility) to reveal the low-frequency signal (trend).

### 2.1. Simple Moving Average (SMA) - The Lag Problem

The SMA is the unweighted mean of the previous $n$ data points.

$$ SMA_t = \frac{P_{t} + P_{t-1} + ... + P_{t-n+1}}{n} $$

* **Pros:** Easy to compute. Stable.
* **Cons:** **Extreme Lag**. If price crashes today, an SMA(200) barely moves. It treats the price 199 days ago (irrelevant history) with the same mathematical weight ($1/n$) as the price today (critical signal).
* **The "Drop-off" Effect:** If a large price spike from 200 days ago "drops off" the calculation window today, the SMA will drop significantly even if the price today didn't move. This creates false signals.

### 2.2. Exponential Moving Average (EMA) - Weighting Recency

The EMA solves the lag and drop-off problems by applying an exponential decay weight formulation. Recent prices matter more.

$$ EMA_t = (P_t \times \alpha) + (EMA_{t-1} \times (1 - \alpha)) $$
Where the smoothing factor $\alpha = \frac{2}{n+1}$.

* **Impact:** An EMA reacts faster to trends than an SMA.
* **Use Case:** Entry triggers (Crosses).

### 2.3. The Hull Moving Average (HMA) - Eliminating Lag via Geomean

Alan Hull developed the HMA to solve the "Lag vs Smoothness" dilemma. Usually, if you smooth data, you add lag.
The HMA algorithm:

1. Calculate a WMA (Weighted MA) with period $n/2$.
2. Calculate a WMA with period $n$.
3. Subtract the two: $Diff = 2 \times WMA(n/2) - WMA(n)$.
4. Smooth the result with a WMA of period $\sqrt{n}$.

$$ HMA = WMA(\sqrt{n}, (2 \times WMA(n/2, P) - WMA(n, P))) $$

* **Result:** The HMA has almost **zero lag** and overshoots slightly, hugging the price curve tightly. It is superior for "Reversal" trading but prone to whipsaws in sideways markets.

### 2.4. Strategy: The "Golden Cross" (50/200) Analysis

A classic institutional signal used on the S&P 500 and Gold (XAUUSD).

* **Logic:**
  * **Golden Cross (Long):** SMA(50) crosses ABOVE SMA(200). Implies short-term momentum is outpacing long-term average price. Bull market confirmation.
  * **Death Cross (Short):** SMA(50) crosses BELOW SMA(200). Bear market confirmation.
* **Performance (Backtested on S&P 500 1950-2024):**
  * The strategy *underperforms* Buy & Hold in strong bull markets (due to late entry lag).
  * The strategy *massively outperforms* in Bear Markets (IT Bubble 2000, GFC 2008) by exiting early.
  * **Conclusion:** It is a "Risk Management" overlay, not a pure alpha generator. It avoids -50% drawdowns.

---

# 3. Breakout Systems: The Turtle Trading Experiment

In 1983, legendary commodities trader Richard Dennis made a bet with William Eckhardt. Dennis believed trading could be taught (Nurture); Eckhardt believed it was innate (Nature). Dennis recruited 14 novices ("Turtles"), gave them strict rules, and \$1 million each to trade. They made \$175 million in 5 years.

### 3.1. The System Rules

The Turtles used a pure **Donchian Channel Breakout** system.

### 3.2. Donchian Channels: The Mathematics of $N$-day Highs

The strategy is deceptively simple:

* **Upper Band ($UC_t$):** $Max(High_{t-1}, ..., High_{t-n})$
* **Lower Band ($LC_t$):** $Min(Low_{t-1}, ..., Low_{t-n})$

**System 1 (Short Term):**

* **Entry:** Buy 1 Unit if Price breaks the **20-day High**. Short 1 Unit if Price breaks **20-day Low**.
* **Filter:** Ignore the signal if the *previous* breakout signal was a winner (The "Whipsaw Filter").
* **Exit:** Close long if Price touches **10-day Low**. Close Short if Price touches **10-day High**.

**System 2 (Long Term):**

* **Entry:** Buy on **55-day High** breakout. Short on **55-day Low**.
* **Filter:** None. Take every signal.
* **Exit:** 20-day Low / High.

### 3.3. Money Management: The $N$ Unit Sizing Algorithm

This was the *real* secret of the Turtles. Not the entry, but the **Position Sizing**.
They defined Volatility ($N$) as the **Average True Range (ATR)** of the last 20 days.

$$ TR_t = Max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|) $$
$$ N = \frac{19 \times N_{t-1} + TR_t}{20} $$

**Unit Size Calculation:**
They sized every trade so that 1 Unit of volatility ($N$) equaled **1% of Account Equity**.

$$ Unit Size = \frac{1\% \times Equity}{N \times DollarsPerPoint} $$

*Example:*

* Equity: \$100,000
* Risk: 1% (\$1,000)
* Asset: Gold (XAUUSD). $N$ (ATR) = 20. Point Value = \$1.
* Unit Size = $1000 / (20 \times 1)$ = 50 Contracts (Ounces).

**Why this works:** It normalizes risk across assets. A volatile asset (Bitcoin) gets a small position size. A stable asset (Eurodollar) gets a huge position size. The dollar risk is identical.

### 3.4. Pyramiding: Adding to Winners

Turtles didn't just buy once. They added to the winner.

* **Initial Entry:** Buy 1 Unit at Breakout.
* **Add 1:** Buy 1 Unit if price moves $+0.5 N$ in favor.
* **Add 2:** Buy 1 Unit if price moves another $+0.5 N$.
* **Max:** 4 Units total.
* **Stops:** Raise stops for ALL units to $Current Price - 2N$.

This creates an exponential profit curve on strong trends while risking only the initial 2N on the first unit.

---

# 4. Time-Series Momentum (TSMomp): The Academic Standard

This strategy, formalized by Moskowitz, Ooi, and Pedersen (2012), is the "Hedge Fund" version of Trend Following.

### 4.1. The Core Equation

TSMomp defines the signal based on the sign of the past 12-month return ($r_{t-12, t}$).

$$ Signal_t = sign(r_{t-12, t}) $$
If the asset is up over the last year, Go Long. If down, Go Short.

### 4.2. Volatility Scaling (Target Vol)

Hedge funds target a specific annualized volatility (e.g., $\sigma_{target} = 40\%$) for the *aggregate portfolio*.
The position size ($W_t$) for asset $s$ is inversely proportional to its realized volatility ($\sigma_{s,t}$).

$$ W_{s,t} = \frac{\sigma_{target}}{\sigma_{s,t}} \times Signal_{s,t} $$

* **Ex-Ante Volatility Estimate ($\sigma_{s,t}$):** Usually an Exponentially Weighted Moving Average (EWMA) of squared daily returns.
$$ \sigma^2_t = \lambda \sigma^2_{t-1} + (1-\lambda) r^2_{t-1} $$
Where $\lambda$ (decay factor) is often 0.94 (RiskMetrics standard).

### 4.3. Portfolio Construction

The TSMomp portfolio holds positions in **ALL** liquid assets (Commodities, Currencies, Bonds, Equities).

* **Diversification:** Because trends in Gold are uncorrelated to trends in 10-Year Treasuries, the portfolio separates risk.
* **The "Smile" Curve:** TSMomp strategies perform best in extreme bull markets AND extreme bear markets. They lose money in sideways "choppy" markets.

---

# 5. Implementation Guide (Python/Pandas)

Implementing a robust Moving Average Crossover backtest in Python.

### 5.1. Signal Generation

```python
import pandas as pd
import numpy as np

def calculate_sma_strategy(df: pd.DataFrame, short_window=50, long_window=200):
    """
    Generates signals for a Golden Cross strategy.
    df: must contain 'Close' column.
    """
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0.0

    # Create short simple moving average over the short window
    signals['short_mavg'] = df['Close'].rolling(window=short_window, min_periods=1, center=False).mean()

    # Create long simple moving average over the long window
    signals['long_mavg'] = df['Close'].rolling(window=long_window, min_periods=1, center=False).mean()

    # Create signals
    # 1.0 = Buy, 0.0 = Flat (or Sell)
    # We use np.where to check for the crossover logic
    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)   

    # Generate trading orders (Difference between signal today and yesterday)
    # 1.0 = Buy Order
    # -1.0 = Sell Order
    signals['positions'] = signals['signal'].diff()

    return signals
```

### 5.2. Handling Look-Ahead Bias

A common quantitative error.

* **Wrong:** `Signal[t] = Close[t] > SMA[t]` -> This assumes you can trade AT the close price. But you only know the Close price *after* the market closes.
* **Right:** Calculate Signal using `Close[t]`, but execute the Trade at `Open[t+1]` or using `Close[t-1]` for signal generation.
  * `df['Strategy_Return'] = df['signal'].shift(1) * df['Market_Return']`
  * The `.shift(1)` is mandatory to align the "Signal from Yesterday" with "Return of Today".

### 5.3. Transaction Costs & Slippage

Trend strategies have low turnover, but costs matter.

* **Slippage ($S$):** The difference between the signal price and execution price. Breakout strategies suffer high slippage because *everyone* is buying the breakout at the same time.
* **Cost Model:**
    $$ Return_{Net} = Return_{Gross} - (Trades \times (Commission + Slippage)) $$
    Backtests without at least **2bps (0.02%)** slippage per trade are considered "Fantasy".

---

**Summary of Volume 01:**
Trend Following is the bedrock of systematic trading. Whether using simple Moving Averages, Donchian Breakouts (Turtles), or Volatility-Scaled Momentum (TSMomp), the logic remains: **react to price, do not predict it.** It requires immense psychological discipline to endure the low win rates, but the payoff during "Black Swan" events is mathematically uncapped.
