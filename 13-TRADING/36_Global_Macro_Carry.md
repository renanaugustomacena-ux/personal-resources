# 36 - Global Macro: The Carry, The Growth & The Quad

**Volume:** 36 of 50
**Strategy Type:** Global Macro / FX / Fundamental
**Risk Profile:** Currency Crisis / Stagflation / Tail Risk
**Mathematical Basis:** Uncovered Interest Rate Parity (UIP) & Dynamic Factor Models (DFM)

> "Money goes where it is treated best. Growth is the engine, Yield is the fuel."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Pillars of Macro](#2-the-theory-the-pillars-of-macro)
    * 2.1. The Carry Trade (Yield): The Forward Rate Bias.
    * 2.2. GDP Nowcasting (Growth): The Pulse of the Economy.
    * 2.3. The Quad (Regime): Intersection of Growth and Inflation.
3. [The Carry Trade Rules](#3-the-carry-trade-rules)
    * 3.1. Selection: Top 3 High Yielders vs Bottom 3 Funding Currencies.
    * 3.2. Execution: Daily Swap Points Mechanics.
    * 3.3. The Steamroller: Why Carry returns are negatively skewed.
4. [The Nowcast Rules](#4-the-nowcast-rules)
    * 4.1. The "Surprise" Signal: Divergence from Consensus.
    * 4.2. Asset Mapping: Growth -> Stocks, De-Growth -> Bonds.
    * 4.3. The Atlanta Fed Model: Dynamic Factor Analysis.
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Carry Return: $r_d - r_f - \Delta S$.
    * 5.2. Dynamic Factor Model: $X_{it} = \lambda_i F_t + \epsilon_{it}$.
    * 5.3. Kalman Filter State Update.
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. Mrs. Watanabe (2000-2007) and the GFC Crash.
    * 6.2. 2008 Recession: Nowcast vs Official Data.
    * 6.3. The Turkish Lira Trap (Nominal vs Phase Yield).
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python Part A: Carry Ranking System.
    * 7.2. Python Part B: GDP Nowcast Scraper (Atlanta Fed).
    * 7.3. Rust Part A: Swap Point Calculator.
    * 7.4. Rust Part B: News Event Surprise Parser.
8. [Risk Management](#8-risk-management)
    * 8.1. Volatility Regime (VIX > 20).
    * 8.2. Stagflation (The Macro Killer).
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Strategy 36** is the "Captain" of the GOLIATH fleet. It directs the strategic asset allocation based on the two most fundamental forces in economics: **The Cost of Money (Carry)** and **The Health of the Economy (Growth)**.

It merges two powerful indicators:

1. **Indicator 036 (Global Macro Carry):** Captures the "Income" component of global markets (Interest Rate Differentials).
2. **Indicator 065 (GDP Nowcasting):** Captures the "Capital Gain" component driven by economic surprises.

**The Edge:**

* Most traders react to headlines.
* GOLIATH constructs a real-time **Dynamic Factor Model** of the economy (Nowcast) to predict the headlines.
* It then funds these bets using the **Carry Trade** (borrowing cheap, investing dear), creating a portfolio with positive expected value even in flat markets.

---

# 2. The Theory: The Pillars of Macro

## 2.1. The Carry Trade (Forward Rate Bias)

Economic theory (UIP) says if US rates are 5% and Japan takes 0%, USD should fall 5%.
**Reality:** USD rises. Capital flows chase yield.
This "Forward Rate Bias" allows traders to earn a "Free Lunch" ... until the restaurant burns down (Crisis).

## 2.2. GDP Nowcasting

Official GDP is released quarterly with a massive lag.
**Nowcasting** estimates the current quarter's GDP *today* by synthesizing hundreds of data points (PMI, Payrolls, Retail Sales, Housing Starts).

* **Consensus:** What Wall Street thinks.
* **Nowcast:** What the Data says.
* **Alpha:** Trading the difference ($Nowcast - Consensus$).

## 2.3. The Quad (Regime Framework)

We map the economy into one of four quadrants:

1. **Goldilocks (Growth Up, Inflation Down):** Buy Tech, Discretionary. (e.g., 2017).
2. **Reflation (Growth Up, Inflation Up):** Buy Commodities, Energy, Emerging Markets. (e.g., 2021).
3. **Deflation (Growth Down, Inflation Down):** Buy Bonds (TLT), Defensive Stocks. (e.g., 2008).
4. **Stagflation (Growth Down, Inflation Up):** Buy Cash, Gold. Short Stocks. (e.g., 1970s, 2022).

---

# 3. The Carry Trade Rules

## 3.1. Selection

1. **Universe:** G10 (USD, EUR, JPY, GBP, CAD, AUD, NZD, CHF) + Liquid EM (MXN, BRL).
2. **Rank:** Sort by 3-Month Interest Rate.
3. **Long:** Top 3 (Highest Yield).
4. **Short:** Bottom 3 (Lowest Yield - usually JPY/CHF).

## 3.2. Execution (Swap Points)

In Spot FX, PnL = Spot Move + Swap Points.
You get credited swap points every day at 5 PM NY.
$$ Points \approx \frac{Spot \times RateDiff}{360} $$
This "Positive Carry" creates a buffer against adverse price moves.

## 3.3. The Steamroller

Carry returns are characterized by:

* Positive Mean.
* Low Volatility (most of the time).
* **Massive Negative Skew:** When it crashes, it crashes hard (e.g., USD/JPY -4% in a day).

---

# 4. The Nowcast Rules

## 4.1. The Surprise Signal

* **Input:** Atlanta Fed GDPNow Estimate.
* **Input:** Blue Chip Consensus Forecast.
* **Signal:** `Spread = Nowcast - Consensus`.
* **Rule:**
  * `Spread > 0.5%`: **Bullish Growth.** (Data beating expectations). Buy Stocks.
  * `Spread < -0.5%`: **Bearish Growth.** (Data missing). Buy Bonds.

## 4.2. The Recession Signal

* If `Nowcast < 0.0%`: A recession is likely efficient.
* **Action:** Move to 100% Defensive (Bonds/Gold/Cash).

---

# 5. Mathematical Derivation

## 5.1. Dynamic Factor Model (DFM)

Used for Nowcasting.
Hypothesis: All economic time series $X_{i,t}$ share a common "State" $F_t$ (The Business Cycle).
$$ X_{it} = \lambda_i F_t + \epsilon_{it} $$
$$ F_t = \phi F_{t-1} + \eta_t $$
We use a **Kalman Filter** to estimate the unobservable $F_t$ given the noisy observations $X_{it}$.

## 5.2. Carry Return Decomposition

$$ Return = (r_{dom} - r_{for}) + \frac{S_{t+1} - S_t}{S_t} $$

* Term 1: Yield Differential (Deterministic, Positive).
* Term 2: FX Spot Move (Stochastic, usually correlates with Term 1 due to Momentum).

---

# 6. Historical Case Studies

## 6.1. Mrs. Watanabe (2000-2007)

Japanese retail investors borrowed cheap Yen to buy high-yield Australian Dollars (AUD).
AUD/JPY rallied from 60 to 105.
They earned 7% yield + 50% capital gains.
**The Crash (2008):** In the GFC, liquidity vanished. The Carry Trade unwound. AUD/JPY crashed to 55 (-50%) in months.

## 6.2. The 2008 Nowcast Signal

Official GDP data did not confirm the recession until late 2008 (Revised data).
The Nowcast (tracking crashing Housing Starts and Jobless Claims) turned negative in Q1 2008.
**GOLIATH** would have exited Equities 6 months before the Lehman collapse based on the Nowcast.

---

# 7. Implementation: Production Grade

## 7.1. Python Part A: Carry Ranking

```python
import pandas as pd
import numpy as np

def calculate_carry_universe(rates_df):
    """
    rates_df: {'Currency': 'USD', 'Rate': 5.25}
    """
    # Sort
    ranked = rates_df.sort_values(by='Rate', ascending=False)
    
    # Portfolio
    longs = ranked.head(3)['Currency'].tolist()
    shorts = ranked.tail(3)['Currency'].tolist()
    
    return longs, shorts

def calculate_swap_points(spot, rate_long, rate_short):
    diff = (rate_long - rate_short) / 360.0 # Daily
    return spot * diff
```

## 7.2. Python Part B: Atlanta Fed Scraper

```python
import requests
import pandas as pd
from io import BytesIO

def get_gdp_now_data():
    """
    Scrapes the Excel file from Atlanta Fed.
    NOTE: URL structure changes often. Needs robust handling.
    """
    url = "https://www.atlantafed.org/-/media/documents/cqer/researchcq/gdpnow/GDPTrackingModelDataAndForecasts.xlsx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            df = pd.read_excel(BytesIO(r.content), sheet_name='TrackingHistory')
            # Extract latest logic...
            latest_nowcast = df.iloc[-1]['GDPNow']
            return latest_nowcast
    except Exception as e:
        print(f"Scrape failed: {e}")
        return None
```

## 7.3. Rust Part A: News Parser

```rust
pub struct NewsEvent {
    pub actual: f64,
    pub consensus: f64,
    pub std_dev: f64, // Historical volatility of this release
}

impl NewsEvent {
    pub fn standardized_surprise(&self) -> f64 {
        if self.std_dev == 0.0 { return 0.0; }
        (self.actual - self.consensus) / self.std_dev
    }
}
```

---

# 8. Risk Management

## 8.1. The Volatility Filter (Steamroller Protection)

Carry works in Low Vol.
Carry dies in High Vol.
**Rule:** If **VIX > 20**, Close ALL Carry Trades.
Rationale: High VIX = Deleveraging. Deleveraging = Selling liquid assets (Winners) to pay for margin calls. Carry trades are liquid winners that get sold.

## 8.2. Stagflation

The "Macro Killer".
If Growth is Down (Nowcast Negative) BUT Inflation is Up (Taylor Rule High).

* Bonds Fall (Rates up).
* Stocks Fall (Growth down).
* **Action:** 50% Cash, 50% Gold/Commodities. This is the only portfolio that survives.

---

# 9. Conclusion

**Strategy 36** ensures GOLIATH is always swimming *with* the economic tide.
By using **GDP Nowcasting**, we know if the tide is rising (Growth) or falling (Recession).
By using **Carry**, we ensure we are swimming in the warmest water (High Yield).
It converts Macroeconomics from a "soft science" into a hard, tradable Algorithm.
