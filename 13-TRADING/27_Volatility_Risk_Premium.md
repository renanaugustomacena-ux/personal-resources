# 27 - Volatility Risk Premium (VRP) & GARCH Forecasting

**Volume:** 27 of 50
**Strategy Type:** Volatility / Factor Investing / Systematic Short Vol
**Risk Profile:** Left Tail Risk (Blowup) / High Sharpe Ratio
**Mathematical Basis:** $VRP = IV - \text{Forecast}(\sigma)$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Price of Fear](#2-the-theory-the-price-of-fear)
    * 2.1. Implied Volatility (IV): The Market's Price.
    * 2.2. GARCH Variance: The Statistical Truth.
    * 2.3. The VRP Spread: Selling the Overpriced Insurance.
3. [The Greeks: Vega ($\nu$)](#3-the-greeks-vega-nu)
    * 3.1. Vega Risk: The "Explosion".
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Black-Scholes IV Pricing (Newton-Raphson).
    * 4.2. GARCH(1,1) Variance Equation.
5. [The Strategy Rules](#5-the-strategy-rules)
    * 5.1. Filtering: Trade only when $IV > GARCH + 5$.
    * 5.2. Execution: Short Strangle / Iron Condor.
    * 5.3. Sizing: Adaptive VAR (Constant Volatility).
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (GARCH Fitting via `arch`).
    * 6.2. Rust (Streaming GARCH Filter).
7. [Historical Case Studies](#7-historical-case-studies)
    * 7.1. Volmageddon (Feb 2018).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**The Volatility Risk Premium (VRP)** is one of the most consistent alpha sources in finance.
It exists because investors are risk-averse loss-minimizers who systematically overpay for Puts (Insurance).
To harvest this, we must know the *Fair Value* of volatility.
Realized Volatility (RV) is backward-looking.
**GARCH (Generalized Autoregressive Conditional Heteroskedasticity)** provides a forward-looking, adaptive forecast of variance.
Strategy 27 trades the spread between **Implied Volatility (IV)** and **GARCH Forecasted Volatility**.

---

# 2. The Theory: The Price of Fear

## 2.1. IV vs GARCH

* **IV:** Forward-looking, Market-driven. (Contains Risk Premium).
* **GARCH:** Backward-looking (stats), but Adaptive. (The "Fair" statistical forecast).

## 2.2. The VRP Spread

$$ VRP = IV - \sigma_{GARCH} $$

* **Positive VRP:** Options are expensive relative to statistical forecast. **Sell Vol.**
* **Negative VRP:** Options are cheap (or GARCH predicts a crash the market hasn't priced yet). **Buy Vol.**

---

# 4. Mathematical Derivation

## 4.1. Implied Volatility (Root Finding)

We solve Black-Scholes for $\sigma$ using Newton-Raphson:
$$ \sigma_{n+1} = \sigma_n - \frac{C_{model}(\sigma_n) - C_{market}}{\nu(\sigma_n)} $$

## 4.2. GARCH(1,1) Forecast

$$ \sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2 $$

* $\omega$: Long-run variance weight.
* $\alpha$: Reaction to recent shock (ARCH).
* $\beta$: Persistence of volatility (GARCH).
* **Forecast:** $E[\sigma_{t+k}^2]$ reverts to long-run mean.

---

# 5. The Strategy Rules

## 5.1. Filtering

* **Rule:** Sell Premium ONLY if $VIX > GARCH(1,1) + 4.0$.
* **Logic:** We need a "Buffer of Safety". If VIX is 15 and GARCH is 14, the edge is too thin to cover Gamma risk.

## 5.2. Position Sizing (Adaptive VAR)

From `052_GARCH`:
Target constant Daily Risk (e.g., 1% Equity).
$$ \text{Size} = \frac{\text{Target Risk}}{\sigma_{GARCH}} $$

* **High Vol:** Size Down (De-leverage).
* **Low Vol:** Size Up.
* **Result:** Prevents blowups during regime shifts.

---

# 6. Implementation: Production Grade

## 6.1. Python (GARCH Forecast)

```python
from arch import arch_model
import numpy as np

def calculate_vrp_garch(df):
    """
    df requires: 'Return' (pct_change), 'VIX'
    """
    # 1. Fit GARCH(1,1)
    # Scale returns for numerical stability
    returns = df['Return'] * 100
    model = arch_model(returns, vol='Garch', p=1, q=1)
    res = model.fit(disp='off')
    
    # 2. Forecast next day variance
    forecasts = res.forecast(horizon=1)
    next_day_var = forecasts.variance.iloc[-1].values[0]
    next_day_vol = np.sqrt(next_day_var) # This is 1-day vol percentage
    
    # Annualize GARCH Vol to compare with VIX
    garch_annual = next_day_vol * np.sqrt(252)
    
    # 3. Calculate VRP
    current_vix = df['VIX'].iloc[-1]
    vrp = current_vix - garch_annual
    
    return vrp, garch_annual, current_vix
```

## 6.2. Rust (Streaming GARCH Filter)

For HFT or live trading, we run a recursive filter (fixed params or slowly updating).

```rust
pub struct GarchFilter {
    omega: f64,
    alpha: f64,
    beta: f64,
    prev_sigma_sq: f64,
    prev_resid_sq: f64,
}

impl GarchFilter {
    pub fn new(omega: f64, alpha: f64, beta: f64, init_sigma: f64) -> Self {
        Self {
            omega, alpha, beta,
            prev_sigma_sq: init_sigma * init_sigma,
            prev_resid_sq: 0.0,
        }
    }

    pub fn update(&mut self, return_val: f64) -> f64 {
        // GARCH(1,1) Update
        let new_sigma_sq = self.omega 
            + self.alpha * self.prev_resid_sq 
            + self.beta * self.prev_sigma_sq;
        
        self.prev_sigma_sq = new_sigma_sq;
        // Assuming mean return ~ 0
        self.prev_resid_sq = return_val * return_val; 
        
        new_sigma_sq.sqrt()
    }
    
    pub fn annualized_vol(&self) -> f64 {
        // Assuming daily returns input
        self.prev_sigma_sq.sqrt() * (252.0f64).sqrt()
    }
}
```

---

# 8. Conclusion

**Strategy 27** upgrades "Short Vol" from a gamble to a business.
By using **GARCH**, we quantify the "Fair Price" of variance.
By using **Newton-Raphson**, we extract the "Market Price" (IV).
We sell the difference ($VRP$), but only when the statistical edge covers the tail risk.
Weighted by **Adaptive VAR**, this strategy survives the crashes that wipe out the amateurs.
