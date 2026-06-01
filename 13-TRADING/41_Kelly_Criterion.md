# 41 - The Kelly Criterion (Money Management)

**Volume:** 41 of 50
**Strategy Type:** Money Management / Position Sizing / Portfolio Optimization
**Risk Profile:** High Volatility (Full Kelly) / Ruin Mitigation (Fractional Kelly)
**Mathematical Basis:** Maximizing Log Growth ($f^* = p - q/b$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Fortune's Formula](#2-the-theory-fortunes-formula)
    * 2.1. The Coin Flip Problem.
    * 2.2. Maximizing Geometric Growth Rate (CAGR).
    * 2.3. The "Full Kelly" Trap (Volatility Tax).
3. [The Strategy: Fractional Kelly](#3-the-strategy-fractional-kelly)
    * 3.1. Why 0.25x Kelly is the GOLIATH Standard.
    * 3.2. Estimation Error Safety Margin.
4. [Continuous Kelly (For Finance)](#4-continuous-kelly-for-finance)
    * 4.1. Formula: $f^* = \frac{\mu - r}{\sigma^2}$.
    * 4.2. Applying to Sharpe Ratio.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python (Portfolio Sizer).
    * 5.2. Rust (Risk Engine Integration).
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. Edward Thorp (The Man Who Beat the Dealer).
    * 6.2. LTCM (How Over-betting kills genius).
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**The Kelly Criterion** is the only mathematically proven formula to maximize long-term wealth.
Bet too small, and you leave money on the table.
Bet too big, and you go bust (Gambler's Ruin).
Kelly finds the **Optimal Edge**.
In GOLIATH, this is not a trading strategy, but a **sizing layer** that sits on top of every other strategy.

---

# 2. The Theory: Fortune's Formula

## 2.1. Basic Formula (Discrete)

For a simple bet with probability $p$ of winning and odds $b$:
$$ f^* = p - \frac{q}{b} $$
Where $q = 1-p$.
Example: 60% chance to win, 1:1 payout.
$f^* = 0.60 - \frac{0.40}{1} = 0.20$.
**Bet 20% of your bankroll.**

## 2.2. Maximizing Log Wealth

Kelly maximizes $E[\ln(Wealth)]$.
Because value compounds multiplicatively, optimizing the log (additive) optimizes the compound rate.

---

# 3. The Strategy: Fractional Kelly

## 3.1. The Full Kelly Trap

Full Kelly is incredibly volatile. It accepts temporary drawdowns of 50%-80% to maximize long-term growth.
For a hedge fund (or a bot with nerves of silicon), this is technically optimal, but practically suicidal due to:

1. **Estimation Error:** We don't know $p$ perfectly. If we overestimate $p$ and bet Full Kelly, we are betting *more* than optimal, which leads to ruin.
2. **Utility:** Losing 50% hurts more than gaining 50% feels good.

## 3.2. Half Kelly (or Quarter Kelly)

Using a fraction (e.g., $c = 0.5$) of the Kelly bet:

* Reduces Volatility by $1/c$ (Linear).
* Reduces Return by only a small fraction (Non-linear efficiency).
**GOLIATH Standard:** **Half-Kelly ($0.5 f^*$)**. This maximizes return/variance ratio.

---

# 4. Continuous Kelly (For Finance)

Stock markets aren't coin flips. They are continuous distributions.
Using the Drift ($\mu$) and Variance ($\sigma^2$) of returns:

$$ f^* = \frac{\mu - r}{\sigma^2} $$

Where $r$ is the risk-free rate.
This is equivalent to:
$$ f^* = \frac{\text{Sharpe Ratio}}{\sigma} $$

**Implication:** Higher Volatility $\to$ Smaller Bet size (even if return is high).

---

# 5. Implementation: Production Grade

## 5.1. Python (Sizer)

```python
import numpy as np

def continuous_kelly(returns, risk_free_rate=0.0):
    """
    Calculates Optimal Leverage using Continuous Kelly.
    """
    mu = returns.mean() * 252 # Annualized
    sigma = returns.std() * np.sqrt(252)
    var = sigma ** 2
    
    if var == 0: return 0.0
    
    f_star = (mu - risk_free_rate) / var
    return f_star

def safe_kelly_size(win_rate, payoff_ratio, fraction=0.5):
    """
    Discrete Kelly with Fractional Safety.
    """
    # f = p - q/b
    f_star = win_rate - (1 - win_rate) / payoff_ratio
    
    # Clip to 0 (No betting if negative edge)
    f_star = max(0.0, f_star)
    
    # Apply Safety Fraction
    return f_star * fraction
```

## 5.2. Rust (Risk Engine)

```rust
pub struct RiskManager {
    kelly_fraction: f64,
}

impl RiskManager {
    pub fn calculate_size(&self, win_rate: f64, payoff: f64, equity: f64) -> f64 {
        let q = 1.0 - win_rate;
        let f_star = win_rate - (q / payoff);
        
        let safe_f = if f_star > 0.0 {
            f_star * self.kelly_fraction
        } else {
            0.0
        };
        
        equity * safe_f
    }
}
```

---

# 6. Historical Case Studies

## 6.1. Edward Thorp

Mathematics professor who invented Card Counting in Blackjack.
He used Kelly to beat casinos. Then he founded Princeton Newport Partners and used Kelly to beat Wall Street (Convertible Arbitrage).
He never had a down year.

## 6.2. LTCM

Nobel prize winners who ignored Kelly.
They estimated $\sigma$ was small, so $f^*$ was huge (massively leveraged).
When $\sigma$ spiked in 1998 (Russia Default), their leverage killed them.
**Lesson:** Always underestimate your edge and overestimate your risk.

---

# 7. Conclusion

**Kelly Criterion** is the governor of greed.
It tells us that **Variance Kills Growth**.
By strictly adhering to Fractional Kelly, GOLIATH ensures that it survives the bad streaks to enjoy the compound growth of the good streaks.
It is the ultimate long-term survival tool.
