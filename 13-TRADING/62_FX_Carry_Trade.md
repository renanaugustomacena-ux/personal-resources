# 62 - FX Carry Trade: Valuation, Bias & The Steamroller

**Volume:** 62 of 100
**Strategy Type:** Global Macro / Fixed Income / Foreign Exchange
**Risk Profile:** Liquidation Cascade / Currency Peg Break / "Picking up nickels in front of a steamroller"
**Mathematical Basis:** Uncovered Interest Rate Parity (UIP), Purchasing Power Parity (PPP), & Forward Rate Bias

> "In the long run, \$1 must buy the same Big Mac in New York as it does in London. In the short run, chaos reigns."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The "Free Lunch" of FX](#2-the-theory-the-free-lunch-of-fx)
    * 2.1. The Forward Rate Bias (The Carry): High rates attract capital.
    * 2.2. The Failure of Uncovered Interest Parity (UIP).
    * 2.3. Purchasing Power Parity (The Anchor): Long-term Fair Value.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Filter 1: The Carry Score (Yield Differential).
    * 3.2. Filter 2: The Valuation Score (PPP Z-Score).
    * 3.3. Filter 3: The Crash Filter (Volatility Regime).
    * 3.4. Signal: "Valuation-Adjusted Carry".
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Swap Points & Forward Rates.
    * 4.2. Relative PPP Formula.
    * 4.3. Carry Return Equation.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Mrs. Watanabe & The Yen Carry Trade (2000-2007).
    * 5.2. The "Frankenshock" (2015 Swiss Peg Break).
    * 5.3. The 1992 Soros Trade (Breaking the BoE).
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (World Bank PPP Data, Rate Ranking, Portfolio Construction).
    * 6.2. Rust (Swap Point Calculator, Inflation-Adjusted Fair Value).
7. [Risk Management](#7-risk-management)
    * 7.1. The "Exit": Momentum vs Value.
    * 7.2. Central Bank Intervention.
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 62** unites three massive concepts in FX data:

1. **Carry (Income):** Borrowing in low-rate currencies (JPY, CHF) to invest in high-rate currencies (MXN, BRL).
2. **Forward Bias (Momentum):** The empirical fact that high-rate currencies tend to *appreciate*, contrary to economic theory.
3. **PPP (Value):** The gravitational force that eventually pulls currencies back to their "Fair Value" based on the cost of goods (Big Mac Index).

**The Goal:** Build a portfolio of **Undervalued High Yielders** funded by **Overvalued Low Yielders**.
This avoids the classic "Carry Trap" (buying a high-yielder just before it collapses due to inflation - e.g., Turkey/Argentina).

---

# 2. The Theory

## 2.1. The Forward Rate Bias (Carry)

Economic theory (UIP) suggests:
$$ E[S_{t+1}] = S_t \frac{1+R_{dom}}{1+R_{for}} $$
If $R_{for}$ is 10% and $R_{dom}$ is 0%, the foreign currency *should* depreciate by 10%.
**Reality:** It doesn't. Capital flows chase the 10% yield, bidding the currency UP. This anomaly has persisted for 40 years.

## 2.2. Purchasing Power Parity (PPP)

From Indicator 062:
In the long run (5-10 years), exchange rates must reflect inflation/price differentials.
$$ S_{Fair} = S_{Base} \times \frac{1 + \pi_A}{1 + \pi_B} $$

* **Overvalued:** Big Mac costs \$8 in Switzerland vs \$5 in US. (CHF is expensive).
* **Undervalued:** Big Mac costs \$3 in Japan Vs \$5 in US. (JPY is cheap).
**The Tension:** Carry says "Sell JPY" (0% yield). PPP says "Buy JPY" (Undervalued).
Strategy 62 manages this tension.

---

# 3. The Strategy Rules

## 3.1. Construction Steps

1. **Universe:** G10 Majors + Liquid EM (MXN, BRL, ZAR, INR).
2. **Step A (Carry):** Rank by 3-Month Interest Rate.
    * *Top:* MXN (11%), BRL (10%).
    * *Bottom:* JPY (0%), CHF (1%).
3. **Step B (Value):** Calculate Deviation from PPP.
    * *Signal:* Z-Score of $(Spot - PPP) / PPP$.
    * *Rule:* **VETO** any Long Carry trade if the currency is > 20% Overvalued. (Avoids Bubbles).
    * *Rule:* **VETO** any Short Funding trade if the currency is > 20% Undervalued. (Avoids "Snapping Back" risk).

## 3.2. The "Sweet Spot"

We want:

* **Long:** High Yield + Undervalued (or Fair Value).
* **Short:** Low Yield + Overvalued (or Fair Value).

## 3.3. Volatility Filter (The Crash Guard)

Carry returns have negative skew (like selling puts).

* **Rule:** If Global VIX > 20 or CVIX (Currency Vol) > 10: **FLAT ALL.**
* Do not pick up nickels in front of the steamroller.

---

# 4. Mathematical Derivation

## 4.1. Swap Points

In Spot FX, you earn/pay carry via the daily rollover (Swap Points).
$$ Points = \frac{S \times (R_{quote} - R_{base})}{360} $$

* Long USD/JPY ($S=150$, $R_{usd}=5\%$, $R_{jpy}=0\%$):
* Daily PnL $\approx 150 \times 0.05 / 360 \approx 0.02$ JPY per day.

## 4.2. Relative PPP

$$ \frac{\Delta S}{S} = \pi_A - \pi_B $$
If Country A has 50% inflation (Turkey) and B has 2% (US), Currency A *must* crash ~48% to maintain parity.
This is why High Nominal Yield in hyperinflation countries is a **Trap**. Real Yield is what matters.

---

# 5. Historical Case Studies

## 5.1. Mrs. Watanabe (2000-2007)

Japanese retail investors (Mrs. Watanabe) sold JPY to buy AUD.
AUDJPY rose for 7 years.
**The Crash:** In 2008, liquidity dried up. AUDJPY fell 55% in weeks.
**Analysis:** PPP signaled AUD was massively overvalued in 2007. Strategy 62 would have exited early.

## 5.2. Swiss Peg Break (2015)

The SNB pegged EURCHF at 1.20.
Inflation differentials meant CHF was undervalued. The market Shorted CHF for positive carry.
When the peg broke, CHF rallied 30% in minutes.
**Lesson:** Never short a massively undervalued currency, even if the Central Bank promises it's safe.

---

# 6. Implementation: Production Grade

## 6.1. Python (World Bank & Analysis)

```python
import pandas as pd
import numpy as np
import wbdata # World Bank API

class FXMacroStruct:
    def __init__(self):
        self.wb_indicators = {'PA.NUS.PPP': 'PPP', 'PA.NUS.FCRF': 'Market_Rate'}
        
    def get_ppp_data(self):
        # Fetch PPP data for major economies
        df = wbdata.get_dataframe(self.wb_indicators, country=['USA', 'EMU', 'GBR', 'JPN', 'AUS', 'CAN', 'CHE'])
        df['Valuation_Pct'] = (df['Market_Rate'] - df['PPP']) / df['PPP']
        return df

    def calculate_score(self, carry_df, ppp_df):
        # Merge Carry (Yield) and PPP (Value)
        merged = pd.merge(carry_df, ppp_df, on='Country')
        
        # Scoring Logic
        # We want High Yield (Carry) and Low Valuation_Pct (Undervalued)
        # Z-Score normalization recommended
        
        merged['Carry_Z'] = (merged['Yield'] - merged['Yield'].mean()) / merged['Yield'].std()
        merged['Value_Z'] = (merged['Valuation_Pct'] - merged['Valuation_Pct'].mean()) / merged['Valuation_Pct'].std()
        
        # Composite Score: 70% Carry, 30% Value
        # Note: We subtract Value_Z because we want NEGATIVE valuation (Undervalued)
        merged['Final_Score'] = 0.7 * merged['Carry_Z'] - 0.3 * merged['Value_Z']
        
        return merged.sort_values('Final_Score', ascending=False)

def risk_check(vix):
    if vix > 20: 
        return "EXIT_ALL"
    return "ACTIVE"
```

## 6.2. Rust (Swap Mechanic & Inflation)

```rust
pub struct CarryPair {
    symbol: String,
    rate_base: f64,
    rate_quote: f64,
    spot: f64,
}

impl CarryPair {
    pub fn daily_points(&self) -> f64 {
        let diff = self.rate_quote - self.rate_base; // Convention depends on pair
        (self.spot * diff) / 360.0
    }
}

pub struct PPPCalculator {
    base_price: f64,
    cpi_domestic_current: f64,
    cpi_domestic_base: f64,
    cpi_foreign_current: f64,
    cpi_foreign_base: f64,
}

impl PPPCalculator {
    pub fn fair_value(&self) -> f64 {
        let infl_dom = self.cpi_domestic_current / self.cpi_domestic_base;
        let infl_for = self.cpi_foreign_current / self.cpi_foreign_base;
        self.base_price * (infl_dom / infl_for)
    }
}
```

---

# 7. Conclusion

**Strategy 62** is the bread and butter of Global Macro.
It acknowledges that the "Forward Rate Bias" is a persistent source of Alpha, but it respects the "Law of One Price" (PPP) as the ultimate gravity.
By filtering Carry trades through a Value lens (PPP) and a Regime lens (VIX), we transform a "Pick up nickels, get crushed by steamroller" strategy into a robust, multi-decade return generator.
We buy High Yield, but only when it's on sale.
