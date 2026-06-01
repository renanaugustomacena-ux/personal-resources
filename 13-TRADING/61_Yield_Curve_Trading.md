# 61 - Yield Curve Trading & Rho: The Macro Crystal Ball

**Volume:** 61 of 100
**Strategy Type:** Fixed Income / Global Macro / Rates
**Risk Profile:** Convexity Risk / Monetary Policy Shock
**Mathematical Basis:** Term Structure of Interest Rates ($Y = f(T)$), Rho ($\rho$), & Expectations Hypothesis

> "Equity markets predict 9 out of the last 5 recessions. The Bond Market predicts 5 out of the last 5."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Shape of Money](#2-the-theory-the-shape-of-money)
    * 2.1. The Yield Curve Slope ($10Y - 2Y$): The Master Cycle Indicator.
    * 2.2. Arturo Estrella & The predictive power of the Inverted Curve.
    * 2.3. Term Premium vs Expectations Hypothesis.
3. [The Greeks: Rho ($\rho$)](#3-the-greeks-rho-rho)
    * 3.1. Definition: Sensitivity to Interest Rates.
    * 3.2. Why Rho matters in high-rate environments (LEAPS & Bonds).
4. [The Strategy Rules](#4-the-strategy-rules)
    * 4.1. The "Steepener": Long 2Y / Short 10Y (Pre-Recession / Rate Cuts).
    * 4.2. The "Flattener": Short 2Y / Long 10Y (Hiking Cycle).
    * 4.3. The "Curve Surfer": Allocating to Equities based on Slope.
    * 4.4. Duration Neutrality: Isolating shape from level.
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Slope Formula: $Y_{10Y} - Y_{2Y}$.
    * 5.2. Probit Recession Model (Estrella & Mishkin).
    * 5.3. DV01 and Hedge Ratios.
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. The "Un-Inversion" Crash (2000, 2008, 2020).
    * 6.2. 2022: The "Widowmaker" Short JPY trade.
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (FRED API, Slope Analysis, Regime Detection).
    * 7.2. Rust (Rho Calculator, Yield Curve Struct, Probit Model).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 61** is the domain of Central Bank watchers. It combines the predictive power of the **Yield Curve Slope (061)** with the option sensitivity of **Rho (61)**.

While Equity traders look at Earnings, Macro traders look at the **Cost of Money**.

* **The Signal:** An Inverted Yield Curve ($2Y > 10Y$) has preceded *every* US Recession since 1955. It is the "Check Engine" light of the economy.
* **The Mechanism:** When Short Rates are high (Fed Tightening) but Long Rates are low (Growth Slowing), the credit cycle breaks.
* **The Trade:**
    1. **Macro Filter:** If Inverted, reduce Equity Beta.
    2. **Curve Trade:** Put on a "Steepener" (Long 2Y / Short 10Y) to profit from the inevitable normalization.
    3. **Rho Hedge:** Manage the interest rate risk of the long volatility book.

---

# 2. The Theory: The Shape of Money

## 2.1. The 2s10s Spread

The difference between the 10-Year Treasury Yield and the 2-Year Treasury Yield.

* **Normal (>0):** Healthy economy. Investors demand a "Term Premium" for locking up money for 10 years. Banks borrow short (deposits) and lend long (mortgages), printing money.
* **Inverted (<0):** Sick economy. The market expects short-term rates to *fall* drastically in the future (pivot). Banks stop lending because the business model breaks (borrow expensive, lend cheap).

## 2.2. Historical Context: Arturo Estrella

In 1989, Arturo Estrella (Fed Economist) published seminal work proving the Yield Curve outperforms all other indicators (like Unemployment or GDP) in predicting recessions 12 months out.
The Bond Market is the "Smart Money". It moves before the Stock Market.

## 2.3. Components

$$ Yield_{Long} = Average(Yield_{Short}) + Term Premium $$

* If the curve inverts, it mathematically implies that $Average(Yield_{Short})$ must fall. The market is pricing in Rate Cuts.

---

# 3. The Greeks: Rho ($\rho$)

## 3.1. Definition ($\rho = \frac{\partial V}{\partial r}$)

Rho measures how much an option (or portfolio) changes in value when interest rates move by 1%.

* **Call Rho:** Positive. Higher rates = Higher Call prices (Forward price is higher due to cost of carry).
* **Put Rho:** Negative. Lower rates = Higher Put prices (Discounted strike is higher).

## 3.2. The "Forgotten Greek"

For decades (2009-2021), Rates were 0%. Rho was 0.
Now, with rates at 5%, a 2-Year LEAP option has massive Rho exposure.
If the Fed hikes 100bps:

* Your 2Y Calls GAIN value (via Rho).
* Your 2Y Bonds LOSE value (via Duration).
Strategy 61 balances these forces.

---

# 4. The Strategy Rules

## 4.1. The Curve Steepener (Bull Steepener)

* **Context:** Economy entering recession. Fed about to panic cut.
* **Trade:** **Buy 2-Year Notes** (Yield falls fast) / **Sell 10-Year Notes** (Yield falls slow or rises).
* **Hedge Ratio:** 4:1 (Buy \$4M of 2Y for every \$1M of 10Y sold) to be DV01 Neutral.
* **PnL:** You make money if the Spread widens (e.g., -50bps $\to$ +100bps).

## 4.2. The Curve Flattener (Bear Flattener)

* **Context:** Economy overheating. Inflation rising. Fed hiking.
* **Trade:** **Sell 2-Year Notes** (Yield rises) / **Buy 10-Year Notes**.
* **PnL:** You make money if the Spread narrows (e.g., +100bps $\to$ 0bps).

## 4.3. The "Curve Surfer" (Asset Allocation)

This logic (from Indicator 061) dictates the broader portfolio state:

1. **Bull Phase:** Slope > 0.5%. Allocate 100% to SPY/QQQ.
2. **Warning Phase:** Slope < 0%. Allocation 50% Cash / 50% Gold.
3. **Crisis Phase:** Slope un-inverts rapidly (rises > 50bps in 1 month). **Short Equities.** The recession usually starts *after* the curve un-inverts.

---

# 5. Mathematical Derivation

## 5.1. Slope Calculation

$$ Slope = Y_{10Y} - Y_{2Y} $$
$$ Slope_{3M} = Y_{10Y} - Y_{3M} $$ (Used by the Fed for Probit model)

## 5.2. Probit Recession Probability

Based on Estrella & Mishkin (1996):
$$ Prob(Recession) = \Phi(-0.53 - 0.63 \times Spread) $$
Where $\Phi$ is the Cumulative Normal Distribution Function.

* Spread = -1.0% $\to$ Prob = 60-70%.
* Spread = +1.0% $\to$ Prob = <10%.

## 5.3. DV01 Hedge Ratio

$$ H = \frac{DV01_{long}}{DV01_{short}} $$
To trade the *shape* of the curve without betting on the *level* of rates, we must weight the legs by their Duration/DV01.

---

# 6. Historical Case Studies

## 6.1. The "Un-Inversion" Crash

* **2000:** Curve Inverted. Nasdaq Peaked. Curve Steepened. Nasdaq Crashed -80%.
* **2007:** Yield Curve Inverted. SPX Peaked. Curve Steepened (Fed cut to 0%). SPX Crashed -50%.
* **2019:** Yield Curve Inverted. 2020 Covid Crash followed.
**Lesson:** The Inversion is the warning. The Steepening is the fire.

---

# 7. Implementation: Production Grade

## 7.1. Python (FRED API & Curve Analysis)

```python
import pandas_datareader.data as web
import pandas as pd
import numpy as np
from scipy.stats import norm

class YieldCurveAnalyst:
    def __init__(self):
        self.tickers = {'2Y': 'DGS2', '10Y': 'DGS10', '3M': 'DGS3MO'}
        
    def get_data(self):
        start_date = '2000-01-01'
        df = web.DataReader(list(self.tickers.values()), 'fred', start=start_date)
        df.columns = list(self.tickers.keys())
        return df
        
    def analyze_regime(self, df):
        # Calculate Slopes
        df['Slope_2s10s'] = df['10Y'] - df['2Y']
        df['Slope_3m10s'] = df['10Y'] - df['3M']
        
        current_slope = df['Slope_2s10s'].iloc[-1]
        
        # Probit Model (Estrella)
        # Prob = N(-0.53 - 0.63 * Spread)
        prob_recession = norm.cdf(-0.53 - 0.63 * current_slope)
        
        signal = "NEUTRAL"
        if current_slope < -0.10:
            signal = "DEFENSIVE (Inverted)"
        elif current_slope > 1.50:
            signal = "AGGRESSIVE (Steep)"
        elif current_slope > -0.10 and current_slope < 0.20 and df['Slope_2s10s'].diff(20).mean() > 0:
             signal = "CRISIS (Rapid Steepening)"
             
        return {
            "Slope": current_slope,
            "Recession_Prob": prob_recession,
            "Signal": signal
        }

def trading_logic(analysis):
    if analysis['Signal'] == "DEFENSIVE":
        return "Alloc: 40% SPY, 40% TLT, 20% GLD"
    elif analysis['Signal'] == "CRISIS":
        return "Alloc: 100% Cash/Short"
    else:
        return "Alloc: 100% SPY"
```

## 7.2. Rust (Rho & Fixed Income Math)

```rust
use std::collections::HashMap;
use statrs::distribution::{Normal, Univariate};

pub struct YieldCurve {
    rates: HashMap<u32, f64>, // Months -> Yield
}

impl YieldCurve {
    pub fn new() -> Self {
        Self { rates: HashMap::new() }
    }
    
    // Calculate 2s10s Slope
    pub fn get_slope(&self) -> f64 {
        let y10 = *self.rates.get(&120).unwrap_or(&0.0); // 120 months
        let y2 = *self.rates.get(&24).unwrap_or(&0.0);   // 24 months
        y10 - y2
    }
    
    // Estrella Probit Model in Rust
    pub fn recession_probability(&self) -> f64 {
        let y10 = *self.rates.get(&120).unwrap_or(&0.0);
        let y3m = *self.rates.get(&3).unwrap_or(&0.0);
        let spread = y10 - y3m;
        
        let z = -0.53 - 0.63 * spread;
        let normal = Normal::new(0.0, 1.0).unwrap();
        normal.cdf(z)
    }
}

// Option Rho Calculation
pub fn calculate_rho(s: f64, k: f64, t: f64, r: f64, sigma: f64, is_call: bool) -> f64 {
    let sqrt_t = t.sqrt();
    let d1 = ((s/k).ln() + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    
    // Normal CDF approximation or create a helper
    let nd2 = 0.5 * (1.0 + libm::erf(d2 / 2.0_f64.sqrt())); 
    let neg_nd2 = 0.5 * (1.0 + libm::erf(-d2 / 2.0_f64.sqrt()));

    if is_call {
        k * t * (-r * t).exp() * nd2
    } else {
        -k * t * (-r * t).exp() * neg_nd2
    }
}
```

---

# 8. Conclusion

**Strategy 61** ensures GOLIATH does not fly blind into a macro storm.
The Yield Curve is the single most reliable indicator in finance. By integrating it, we gain:

1. **Regime Detection:** Knowing when the cycle is turning (Inversion).
2. **Trade Setup:** Specific Rate trades (Steepeners).
3. **Risk Management:** Accounting for Rho in our options book.
It is the cornerstone of the "Macro Overlay" that protects the high-frequency strategies from secular regime changes.
