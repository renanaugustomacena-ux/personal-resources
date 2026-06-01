# 26 - Calendar Spreads & The Art of Theta

**Volume:** 26 of 50
**Strategy Type:** Volatility / Term Structure / Long Theta
**Risk Profile:** Defined Risk / Sensitivity to IV Skew
**Mathematical Basis:** Differential Decay Rates ($\frac{\partial V}{\partial t}$) and Black-Scholes Theta

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Time Travels at Different Speeds](#2-the-theory-time-travels-at-different-speeds)
    * 2.1. Theta ($\Theta$): The Greeks Definition
    * 2.2. The Curve: $O(1/\sqrt{t})$
    * 2.3. The "Tent" Profit Profile
3. [The Strategy: Calendar Spread](#3-the-strategy-calendar-spread)
    * 3.1. Construction: Sell Near (High Decay) + Buy Far (Low Decay)
    * 3.2. Term Structure Slope (Contango vs Backwardation)
4. [Secondary Strategy: Theta Burn (The Weekend Effect)](#4-secondary-strategy-theta-burn-the-weekend-effect)
    * 4.1. Rules: Sell Friday Close, Buy Monday Open
    * 4.2. Mathematical Edge: 2 Days of Decay, 0 Days of Trading
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Black-Scholes Theta Formula
    * 5.2. Vega Risk
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. Earnings Run-Up (Vega Expansion)
    * 6.2. 2014 Low Vol Grind
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (PnL Surface Modeling)
    * 7.2. Rust (Theta Calculator)
8. [Optimization & Variations](#8-optimization--variations)
    * 8.1. Double Calendar (Straddle Swap)
    * 8.2. Diagonal Spread (Poor Man's Covered Call)
9. [Risk Management](#9-risk-management)
10. [Conclusion](#10-conclusion)

---

# 1. Executive Summary

**The Calendar Spread** is the primary instrument for trading **Time**.
It exploits the non-linear nature of option decay.
While most strategies fear Time Decay (Theta), the Calendar Spread weaponizes it.
By selling the "fast" time (Near Month) and buying the "slow" time (Far Month), we create a position that grows in value as the clock ticks, provided Volatility remains stable.

---

# 2. The Theory: Time Travels at Different Speeds

## 2.1. Theta ($\Theta = \frac{\partial V}{\partial t}$)

From `053_The_Greeks`:
$$ \Theta \approx -\frac{S N'(d_1) \sigma}{2 \sqrt{t}} - r K e^{-rt} N(d_2) $$

* **Interpretation:** Dollar value lost per day.
* **Key Insight:** $\Theta$ is proportional to $\frac{1}{\sqrt{t}}$.
* As $t \to 0$, Theta approaches $\infty$. (Explosive decay at expiration).

## 2.2. The Curve

* A 30-day option decays at speed $V_{high}$.
* A 90-day option decays at speed $V_{low}$.
* **Net Theta:** $V_{high} - V_{low} > 0$.
* This positive spread is your daily paycheck.

---

# 3. The Strategy: Calendar Spread

## 3.1. Construction

* **Sell:** Front Month ATM Call (e.g., 30 DTE).
* **Buy:** Back Month ATM Call (e.g., 60 DTE).
* **Cost:** Debit (Long option is more expensive).

## 3.2. Term Structure Slope

* **Contango (Normal):** Back Month IV > Front Month IV. Calendar is expensive.
* **Backwardation (Crisis):** Front Month IV > Back Month IV. Calendar is cheap.
* **Edge:** If Term Structure is flat, you are buying "Cheap Vega" (Back Month) and selling "Expensive Gamma" (Front Month).

---

# 4. Secondary Strategy: Theta Burn (The Weekend Effect)

Originating from `053_The_Greeks`:
**The Weekend Effect** exploits the fact that markets close, but time does not stop.

## 4.1. Rules

1. **Friday 3:55 PM:** Sell ATM Straddle or Iron Condor (High Theta).
2. **Monday 9:35 AM:** Buy back the position.
3. **Logic:** Option models often count "Trading Days" (252), but reality counts "Calendar Days" (365).
4. **Edge:** You capture 2 days of decay for 0 days of price risk (excluding Gap Risk).
5. **Note:** Crypto markets trade 24/7, so this anomaly is weaker there, but valid for SPX/NDX.

---

# 5. Mathematical Derivation

## 5.1. Black-Scholes Theta

For an ATM Call ($S=K, r=0$):
$$ \Theta_{ATM} \approx -\frac{S \sigma}{2 \sqrt{2 \pi t}} $$
Notice the $\sqrt{t}$ in the denominator.
If $t$ goes from 4 weeks to 1 week (factor of 4), Theta doubles ($\sqrt{4}=2$).

## 5.2. Vega Risk

$$ Vega_{net} = V_{long} - V_{short} > 0 $$
Calendars are **Long Vega**.
If Volatility collapses (e.g., after Earnings), the Long Option loses value faster than the Short Option gains it.
**Rule:** Do NOT hold Calendars through binary events unless you are betting on Volatility Expansion.

---

# 6. Historical Case Studies

## 6.1. Earnings Run-Up

Stock earnings in 20 days.

* **Action:** Buy Calendar (Sell 10 DTE / Buy 40 DTE).
* **Result:** As earnings approach, 40 DTE IV spikes (anticipating event). 10 DTE expires (before event).
* You capture Theta *plus* the Vega increase of the back month.

## 6.2. 2014 Low Vol Grind

SPX VIX 11. Calendars printed money every month because price never moved outside the "Tent".

---

# 7. Implementation: Production Grade

## 7.1. Python (Surface Optimization)

```python
import numpy as np
from scipy.stats import norm

def calculate_theta(S, K, T, r, sigma):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    theta = -(S*norm.pdf(d1)*sigma)/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)
    return theta / 365.0

def optimize_calendar(S, r, sigma_front, sigma_back):
    # Find ratio of Theta_Short / Theta_Long
    t_short = 30/365
    t_long = 60/365
    
    theta_short = calculate_theta(S, S, t_short, r, sigma_front)
    theta_long = calculate_theta(S, S, t_long, r, sigma_back)
    
    ratio = abs(theta_short / theta_long)
    return ratio # Higher is better (> 1.5)
```

## 7.2. Rust (Theta Calculator)

```rust
use std::f64::consts::PI;

pub fn calculate_theta(s: f64, k: f64, t: f64, r: f64, sigma: f64, is_call: bool) -> f64 {
    let sqrt_t = t.sqrt();
    let d1 = ((s/k).ln() + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    let npd1 = (-0.5 * d1 * d1).exp() / (2.0 * PI).sqrt();
    let nd2 = 0.5 * (1.0 + libm::erf(d2 / 2.0_f64.sqrt())); // PDF and CDF
    
    let term1 = -s * npd1 * sigma / (2.0 * sqrt_t);
    
    if is_call {
        term1 - r * k * (-r * t).exp() * nd2
    } else {
        term1 + r * k * (-r * t).exp() * (1.0 - nd2) // Approx for Put
    }
}
```

---

# 8. Optimization

## 8.1. Double Calendar

To widen the "Tent". Sell Put Calendar Strike A + Sell Call Calendar Strike B.
Creates a profit plateau.

## 8.2. Diagonal Spread

Sell OTM Front Month + Buy ITM Back Month.
Functions as a "Leveraged Covered Call".
Delta is positive ($\approx 0.80$).

---

# 9. Risk Management

## 9.1. Volatility Crush

If IV drops 50% across the board, the position loses money.
**Stop Loss:** Close if VIX drops below 12 or if Portfolio PnL < -15%.

## 9.2. Adjustment

If price breaches the strikes:

1. Do NOT roll. Rolling usually increases cost basis.
2. Add a generic "Iron Condor" to collect premium to offset the loss.

---

# 10. Conclusion

Calendar Spreads allow proper "Temporal Arbitrage".
We are arbitrageurs of the Term Structure.
By using the Rust `calculate_theta` function, GOLIATH scans the entire option chain to find strikes where $\frac{\Theta_{short}}{\Theta_{long}}$ is maximized (Highest Decay Differential).
This is the "Golden Ratio" of Time Trading.
