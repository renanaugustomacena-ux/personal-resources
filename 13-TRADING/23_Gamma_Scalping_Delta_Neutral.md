# 23 - Gamma Scalping & The Greeks: Master of Convexity

**Volume:** 23 of 50
**Strategy Type:** Volatility / Delta Neutral / Active Trading
**Risk Profile:** Market Neutral / High Operational Cost
**Mathematical Basis:** Convexity ($\frac{1}{2}\Gamma dS^2$) and Black-Scholes Greeks

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Greeks: The Language of Risk](#2-the-greeks-the-language-of-risk)
    * 2.1. Delta ($\Delta$): Speed (Direction)
    * 2.2. Gamma ($\Gamma$): Acceleration (Curvature)
    * 2.3. The relationship: $\Gamma = \frac{\partial \Delta}{\partial S}$
3. [The Strategy: Gamma Scalping](#3-the-strategy-gamma-scalping)
    * 3.1. The Setup: Long Straddle (Long Gamma)
    * 3.2. Dynamic Hedging: Buying Low, Selling High
    * 3.3. PnL Attribution: $\Theta \approx -\frac{1}{2} \sigma^2 S^2 \Gamma$
4. [Signal Generation: Gamma Squeeze Detection](#4-signal-generation-gamma-squeeze-detection)
    * 4.1. Net GEX (Gamma Exposure)
    * 4.2. The Feedback Loop: Price Up $\to$ Delta Up $\to$ Buying $\to$ Price Up
5. [Microstructure & HFT Context](#5-microstructure--hft-context)
    * 5.1. Market Makers as Gamma Scalpers
    * 5.2. Toxic Flow & Adverse Selection
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Dynamic Hedging Class)
    * 6.2. Rust (High Precision Greeks Calculation)
7. [Optimization & Variations](#7-optimization--variations)
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Gamma Scalping** is the operationalization of the **Black-Scholes** formula.
It transforms a static Long Volatility position option into a dynamic trading machine.
By continuously re-hedging a portfolio to be **Delta Neutral**, a trader monetizes the **Gamma** (Convexity).
Every re-hedge involves **Buying Low** (when Delta drops) and **Selling High** (when Delta rises).
This strategy captures the "wiggles" of the market, turning noise into profit.

---

# 2. The Greeks: The Language of Risk

To trade Volatility, one must master the partial derivatives of the Pricing Function $V(S, t, \sigma, r)$.

## 2.1. Delta ($\Delta = \frac{\partial V}{\partial S}$)

* **Call Delta:** $N(d_1)$ (Ranges 0 to 1). Probability of expiring ITM.
* **Put Delta:** $N(d_1) - 1$ (Ranges -1 to 0).
* **Interpretation:** The hedge ratio. If Delta is 0.5, you need 50 shares to hedge 1 contract.

## 2.2. Gamma ($\Gamma = \frac{\partial^2 V}{\partial S^2}$)

* **Formula:** $\Gamma = \frac{N'(d_1)}{S \sigma \sqrt{t}}$
* **Interpretation:** The Rate of Change of Delta.
* **High Gamma:** Front-month ATM options. Delta flips from 0 to 1 rapidly. "Pin Risk".
* **Low Gamma:** LEAPS or Deep ITM/OTM. Delta is stable.

---

# 3. The Strategy: Gamma Scalping

## 3.1. The Mechanism

1. **Start:** Buy ATM Straddle. Delta $\approx$ 0. Gamma > 0.
2. **Move:** Underlying Stock rises \$1.
3. **Effect:**
    * Call Delta increases (e.g., 0.50 $\to$ 0.55).
    * Put Delta decreases/flattens (e.g., -0.50 $\to$ -0.40).
    * Net Delta becomes Positive (+0.15).
4. **Action:** **Sell Stock** to flatten Delta back to 0. (Selling into the rally).
5. **Reverse:** If Stock falls \$1, Net Delta becomes Negative. **Buy Stock**.
6. **Result:** You are systematically trading against the trend on short timeframes, capturing the mean reversion of the noise.

## 3.2. PnL Attribution

$$ Profit \approx \frac{1}{2} \Gamma (dS)^2 - \Theta dt $$
You make money from movement ($dS^2$). You pay money for time ($dt$).
**Win Condition:** Realized Volatility > Implied Volatility.

---

# 4. Signal Generation: Gamma Squeeze Detection

Using Order Book and Options Chain data to detect when Market Makers are trapped.

## 4.1. Net GEX (Gamma Exposure)

We sum the Gamma of all Open Interest strikes, weighted by Dealer Positioning.

* **Positive GEX:** Dealers are Long Gamma. They fade moves. Volatility is dampened.
* **Negative GEX:** Dealers are Short Gamma. They chase moves. Volatility is amplified.

## 4.2. The Feedback Loop (Methodology)

1. Identify Strikes where Dealers are massive Short Calls.
2. If Price approaches Strike $\to$ Dealer Delta becomes more negative.
3. Dealers MUST Buy Underlying to hedge.
4. Buying pushes Price higher.
5. Loop repeats.
**Strategy:** Go Long Momentum when GEX is highly Negative.

---

# 5. Microstructure & HFT Context

## 5.1. Market Makers

Citadel and Virtu are essentially continuous Gamma Scalpers.
They provide liquidity (Limit Orders), making them effectively **Short Gamma** (selling options/liquidity).
They must hedge rapidly (HFT) to avoid being run over.

## 5.2. Toxic Flow

If a Market Maker sells an option to an "Informed Trader" (Alpha), the price will move monotonically against them.
Gamma Scalping fails in "Trending" markets if the trend never reverts (no wiggles to scalp).

---

# 6. Implementation: Production Grade

## 6.1. Python (Gamma Scalper Logic)

```python
import numpy as np

class GammaScalper:
    def __init__(self, portfolio_value, initial_cash):
        self.stock_pos = 0
        self.cash = initial_cash
        self.net_delta = 0

    def rehedge(self, current_price, current_option_greeks):
        # current_option_greeks: struct with total portfolio delta
        total_delta = current_option_greeks['delta']
        
        # We want Total Delta + Stock Delta = 0
        # Stock Delta = 1.0 per share
        
        target_stock_pos = -total_delta
        
        # Threshold: Don't trade for < 10 delta (transaction costs)
        if abs(target_stock_pos - self.stock_pos) > 10:
            trade_size = target_stock_pos - self.stock_pos
            cost = trade_size * current_price
            
            self.stock_pos += trade_size
            self.cash -= cost
            print(f"Hedged: {trade_size:.0f} shares @ {current_price}")
            
    def attribution(self, greeks, dS, dt):
        gamma_pnl = 0.5 * greeks['gamma'] * (dS**2)
        theta_pnl = greeks['theta'] * dt
        return gamma_pnl + theta_pnl
```

## 6.2. Rust (High Precision Greeks Library)

We implement the Greeks in Rust for sub-microsecond calculation across thousands of strikes.

```rust
use std::f64::consts::PI;

pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub theta: f64,
    pub vega: f64,
    pub rho: f64,
}

pub fn normal_pdf(x: f64) -> f64 {
    (-0.5 * x * x).exp() / (2.0 * PI).sqrt()
}

pub fn normal_cdf(x: f64) -> f64 {
    0.5 * (1.0 + libm::erf(x / 2.0_f64.sqrt()))
}

pub fn calculate_greeks(s: f64, k: f64, t: f64, r: f64, sigma: f64, is_call: bool) -> Greeks {
    let sqrt_t = t.sqrt();
    let d1 = ((s/k).ln() + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    
    let nd1 = normal_cdf(d1);
    let nd2 = normal_cdf(d2);
    let npd1 = normal_pdf(d1);
    
    let delta = if is_call { nd1 } else { nd1 - 1.0 };
    let gamma = npd1 / (s * sigma * sqrt_t);
    // Vega is usually expressed as sensitivity to 1% change
    let vega = s * sqrt_t * npd1 * 0.01; 
    
    let theta_term1 = -s * npd1 * sigma / (2.0 * sqrt_t);
    let theta = if is_call {
        theta_term1 - r * k * (-r * t).exp() * nd2
    } else {
        theta_term1 + r * k * (-r * t).exp() * normal_cdf(-d2)
    };
    
    let rho = if is_call {
        k * t * (-r * t).exp() * nd2
    } else {
        -k * t * (-r * t).exp() * normal_cdf(-d2)
    };

    Greeks { delta, gamma, theta, vega, rho }
}
```

---

# 7. Optimization

## 7.1. Reverse Scalping (Short Gamma)

Selling the Straddle. You are Short Gamma.

* Price Rises $\to$ You get Short $\to$ Buy to Cover (Buy High).
* Price Falls $\to$ You get Long $\to$ Sell to Exit (Sell Low).
* You bleed money on every move.
* **Edge:** The premium collected (Theta) must outweigh the scalping losses.

## 7.2. Leverage with Futures

Hedging SPY options with ES Futures (500x leverage effectively) allows for minimal capital usage for the hedge, improving ROE.

---

# 8. Risk Management

## 8.1. Slippage & Thresholds

If you hedge every micro-move, the Bid-Ask spread will eat your Alpha.
**Rule:** Only hedge when $\frac{1}{2}\Gamma (dS)^2 > \text{Transaction Cost}$.
This usually defines a "Banding" strategy for re-hedging.

## 8.2. Gap Risk

The market closes at \$100 and opens at \$90.
You cannot hedge the path. You take the full loss.
**Solution:** Always buy wings (Iron Condor) or trade 24/7 markets.

---

# 9. Conclusion

Gamma Scalping is the purest form of Volatility Trading.
It removes the need to predict "Direction" (Delta) and focuses entirely on predicting "Magnitude" (Volatility).
By merging the Rust `Greeks` calculator into our engine, the GOLIATH bot can manage thousands of option legs and auto-hedge them in real-time, effectively becoming a specialized Market Maker.
