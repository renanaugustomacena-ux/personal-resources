# 29 - Market Making: The Stoikov Inventory Model

**Volume:** 29 of 50
**Strategy Type:** HFT / Market Microstructure / Liquidity Provision
**Risk Profile:** Inventory Risk / Toxic Flow (Adverse Selection)
**Mathematical Basis:** Avellaneda-Stoikov (2008) & Kyle's Lambda ($\lambda$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Being the House](#2-the-theory-being-the-house)
    * 2.1. The Spread: How Market Makers get paid.
    * 2.2. The Risk: Inventory accumulation (Holding the bag).
    * 2.3. The Solution: Skewing quotes to flatten inventory.
3. [The Costs of Liquidity](#3-the-costs-of-liquidity)
    * 3.1. Kyle's Lambda: The Price Impact of Volume.
    * 3.2. Effective Spread: The Real Cost of Execution.
4. [The Strategy Rules](#4-the-strategy-rules)
    * 4.1. Calculate Fair Value (Micro-Price).
    * 4.2. Reservation Price ($r$): Skewing for Inventory.
    * 4.3. Optimal Spread ($\delta$): Adjusting for Volatility.
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Stoikov Formula.
    * 5.2. Amihud Ratio (Empirical Lambda).
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Full Stoikov Agent + TCA).
    * 6.2. Rust (High-Performance Inventory Manager).
7. [Advanced Tactics](#7-advanced-tactics)
    * 7.1. The Liquidity Sniper (Trading Inside the Spread).
    * 7.2. The Liquidity Gap (Fading Lambda Spikes).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Market Making** is not "predicting direction". It is providing a service: **Immediacy**.
Restless traders want to buy/sell NOW. You capture the **Spread**.
However, the "Quoted Spread" is often a lie. The real game is played in the **Effective Spread** and **Market Impact** (Lambda).
Strategy 29 integrates the classic **Avellaneda-Stoikov** inventory model with modern microstructure metrics (Kyle's Lambda) to ensure we provide liquidity only when it is profitable, and withdraw when it is toxic.

---

# 2. The Theory

## 2.1. The Inventory Problem

If you buy 100 shares at $10.00$ and price falls to $9.90$, you lose.
Market Makers want to be **Flat** at the end of the day.

## 2.2. Skewing Quotes

If Inventory > 0 (Long): Lower both Bid and Ask.

* **Result:** You are more likely to be hit on the Ask (Reducing inventory).
This "Inventory Management" is the core alpha of HFT.

---

# 3. The Costs of Liquidity

## 3.1. Kyle's Lambda ($\lambda$)

From `034_Kyles_Lambda`:
Measures **Market Impact**: "How much does price move if I buy \$1M?"
$$ \lambda = \frac{\Delta P}{\text{Order Flow}} $$

* **High $\lambda$:** Illiquid. Market is fragile.
* **Low $\lambda$:** Liquid. Market is robust.

## 3.2. Effective Spread (ES)

From `056_Effective_Spread`:
Measures the *actual* execution cost vs Mid-Price.
$$ ES = 2 \times |P_{trade} - Mid| $$

* **Quoted Spread:** What is shown.
* **Effective Spread:** What is paid.
* **Goal:** Receive the Quoted Spread, but pay 0 Effective Spread (Price Improvement).

---

# 4. The Strategy Rules

## 4.1. Reservation Price ($r$)

The price at which you are indifferent between buying and selling.
$$ r(s, q) = s - q \gamma \sigma^2 (T-t) $$

* $s$: Mid Price.
* $q$: Inventory.
* $\gamma$: Risk Aversion.
* $\sigma$: Volatility.

## 4.2. Optimal Spread ($\delta$)

$$ \delta(q) = \frac{1}{\gamma} \ln \left( 1 + \frac{\gamma}{\kappa} \right) $$

* $\kappa$: Order Arrival Intensity.

---

# 6. Implementation: Production Grade

## 6.1. Python (Stoikov Agent)

```python
import numpy as np

class StoikovAgent:
    def __init__(self, gamma=0.1, sigma=2, kappa=1.5):
        self.gamma = gamma
        self.sigma = sigma
        self.kappa = kappa
        self.inventory = 0
        
    def get_quotes(self, mid_price, T_remaining):
        # 1. Reservation Price
        reservation_price = mid_price - (self.inventory * self.gamma * (self.sigma**2) * T_remaining)
        
        # 2. Optimal Spread
        half_spread = (2 / self.gamma) * np.log(1 + (self.gamma / self.kappa))
        
        bid = reservation_price - half_spread / 2
        ask = reservation_price + half_spread / 2
        
        return bid, ask

    def calculate_effective_spread(self, trade_price, mid_price):
        return 2 * abs(trade_price - mid_price)
```

## 6.2. Rust (Inventory Manager with Lambda)

```rust
pub struct InventoryManager {
    inventory: i64,
    gamma: f64,
    lambda_history: Vec<f64>,
}

impl InventoryManager {
    pub fn calculate_reservation_price(&self, mid: f64, vol: f64) -> f64 {
        let q = self.inventory as f64;
        mid - (q * self.gamma * vol * vol)
    }

    pub fn update_lambda(&mut self, price_change: f64, volume: f64) {
        if volume.abs() > 0.0 {
            let lambda = price_change.abs() / volume.abs();
            self.lambda_history.push(lambda);
        }
    }
}
```

---

# 7. Advanced Tactics

## 7.1. The Liquidity Sniper

* **Condition:** Relative Effective Spread > 2%.
* **Action:** Place Limit Orders *inside* the wider spread.
* **Edge:** Capture the "Cost of Immediacy" from impatient traders.

## 7.2. The Liquidity Gap

* **Condition:** Kyle's Lambda spikes > 3 Sigma.
* **Signal:** Fade the move.
* **Reason:** Price moved on thin ice (low liquidity), not real conviction.

---

# 8. Conclusion

**Strategy 29** turns the table.
Instead of being the gambler, you become the Casino.
By strictly managing **Inventory Risk** ($q$) and monitoring **Liquidity Cost** ($\lambda$), GOLIATH extracts value from the noise of the market, one spread at a time.
