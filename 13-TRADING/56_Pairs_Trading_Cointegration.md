
# 56 - Pairs Trading, Cointegration & Copulas

**Volume:** 56 of 100
**Strategy Type:** Statistical Arbitrage / Market Neutral / Relative Value
**Risk Profile:** Divergence Risk / Break in Correlation
**Mathematical Basis:** Cointegration (Engle-Granger) & Sklar's Theorem (Copulas)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Linear vs Non-Linear Dependence](#2-the-theory-linear-vs-non-linear-dependence)
    * 2.1. Cointegration: The Drunk and the Dog (Linear).
    * 2.2. Copulas: The Shape of the Crash (Non-Linear).
    * 2.3. Sklar's Theorem: Decomposing Marginals from Dependence.
3. [Strategy 1: Classic Pairs (Z-Score)](#3-strategy-1-classic-pairs-z-score)
    * 3.1. Selection: ADF Test < 0.05.
    * 3.2. Execution: Mean Reversion of Linear Spread.
4. [Strategy 2: Copula Arbitrage](#4-strategy-2-copula-arbitrage)
    * 4.1. Concept: Trading Mispricing in *Probability Space*.
    * 4.2. Fitting: Marginals (Kernel Density) + Copula (Clayton/Gumbel).
    * 4.3. Signal: Conditional Probability $P(U < u | V = v) < 0.05$.
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Ornstein-Uhlenbeck Process.
    * 5.2. Gaussian vs Student-t Copula.
    * 5.3. Tail Dependence Coefficients.
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. Royal Dutch Shell (Classic Pair).
    * 6.2. 2008 Crisis (Li's Copula Failure).
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (Statsmodels Cointegration & Copulas).
    * 7.2. Rust (Streaming Z-Score & Numerical Integration).
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Pairs Trading** is the "Grandfather" of Quant strategies.
It isolates **Relative Value** (Alpha) from Market Direction (Beta).
While Classic Pairs Trading uses **Linear Regression** (Cointegration) to find mispricing, Modern StatArb uses **Copulas** to model the non-linear "Tail Dependence" between assets.
This file combines both approaches into a unified framework for Statistical Arbitrage.

---

# 2. The Theory

## 2.1. Cointegration (The Leash)

Correlation measures if two assets move *in the same direction*.
Cointegration measures if the *distance* between them remains bounded.
We trade the "Leash". If the Dog wanders too far from the Drunk, we bet they will converge.

## 2.2. Copulas (The Shape)

"Correlation is a single number. Dependence is a shape."
In a crash, correlations go to 1. Assets that are normally uncorrelated suddenly move together.
**Copulas** model this specific behavior (Tail Dependence).
Strategy: We fit a Copula to the joint distribution of BTC and ETH. If ETH moves to a probability quantile that is "impossible" given BTC's current quantile, we have an arbitrage opportunity.

## 2.3. Sklar's Theorem

Any joint distribution $H(x, y)$ can be decomposed into:

1. Marginals $F(x), G(y)$.
2. A Copula $C(u, v)$ that binds them.
$$ H(x, y) = C(F(x), G(y)) $$

---

# 3. Strategy 1: Classic Pairs (Linear)

## 3.1. Rules

1. **Find Pair:** P-value of ADF Test on residuals < 0.05.
2. **Calculate Spread:** $S = \ln(P_A) - \beta \ln(P_B)$.
3. **Z-Score:** $Z = (S - \mu) / \sigma$.
4. **Trade:** Short Spread if $Z > 2$. Long Spread if $Z < -2$.

---

# 4. Strategy 2: Copula Arbitrage (Non-Linear)

From `038_Copula_Dependence`:

## 4.1. Rules

1. **Transform:** Convert prices to Returns, then to Uniform Rank [0, 1] ($u$ and $v$).
2. **Fit:** Fit a **Clayton Copula** (captures lower tail dependence - crashes).
3. **Conditional Prob:** Calculate $P(u | v)$. "Given ETH is down 5%, what is the probability BTC is down 2%?"
4. **Signal:**
    * If Prob < 5%: The move is an outlier. **Reversion Trade**.
    * If Prob > 95%: **Momentum Trade**.

## 4.2. Why Copulas?

Linear regression assumes residuals are Normal. They are not.
Copulas allow for "Fat Tails". They prevent you from betting on convergence during a Black Swan event when the "rubber band" snaps.

---

# 5. Mathematical Derivation

## 5.1. Gaussian Copula Density

$$ c(u, v) = \frac{1}{\sqrt{1-\rho^2}} \exp \left( \frac{\rho^2(x^2+y^2) - 2\rho xy}{2(1-\rho^2)} \right) $$
Where $x = \Phi^{-1}(u)$.
This is what Wall Street used to price CDOs in 2008. (It failed because it assumed constant $\rho$).

## 5.2. Tail Dependence

$$ \lambda_L = \lim_{u \to 0} P(V < u | U < u) $$
If $\lambda_L > 0$, assets crash together.
Clayton Copula has $\lambda_L > 0$. Gaussian Copula has $\lambda_L = 0$.
**Lesson:** Use Clayton for Crypto/Equities.

---

# 6. Historical Case Studies

## 6.1. Quant Quake 2007

Classic Pairs funds blew up because spreads widened to 10-sigma.
They used Linear models.
A Copula model might have detected the "Tail Event" and signaled "Exit" instead of "Double Down".

## 6.2. The Ratio Trade (ETH/BTC)

ETH/BTC is not perfectly cointegrated (ETH has higher beta).
However, their probability ranks are highly dependent.
Copula Arb captures the "Micro-Decouplings" better than a simple Ratio MA crossover.

---

# 7. Implementation: Production Grade

## 7.1. Python (Copula Arb)

```python
import numpy as np
from scipy import stats

def fit_gaussian_copula(x, y):
    # 1. PIT (Probability Integral Transform)
    u = stats.rankdata(x) / (len(x) + 1)
    v = stats.rankdata(y) / (len(y) + 1)
    
    # 2. Inverse Normal
    x_norm = stats.norm.ppf(u)
    y_norm = stats.norm.ppf(v)
    
    # 3. Correlation
    rho = np.corrcoef(x_norm, y_norm)[0, 1]
    return rho

def calculate_mispricing_index(u_curr, v_curr, rho):
    # Conditional Probability P(U < u | V = v)
    # Using partial derivative of Gaussian Copula
    x = stats.norm.ppf(u_curr)
    y = stats.norm.ppf(v_curr)
    
    z = (x - rho * y) / np.sqrt(1 - rho**2)
    mi = stats.norm.cdf(z)
    return mi 
    # If mi > 0.95 or < 0.05, Trade.
```

## 7.2. Rust (Streaming Z-Score)

```rust
use std::collections::VecDeque;

pub struct PairsTrader {
    period: usize,
    steps: VecDeque<f64>,
}

impl PairsTrader {
    pub fn update(&mut self, spread: f64) -> f64 {
        // Calculate Rolling Mean/Std
        // Return Z-Score
        // (Implementation details in Strategy 16/56)
        0.0 
    }
}
```

---

# 8. Risk Management

## 8.1. The Divorce

Cointegration can break (e.g., Merger, Hack).
**Rule:** If Z-Score > 4.0, CLOSE. Do not ask questions.

## 8.2. Legging Risk

Execution Matters.
Use **Atomic Orders** (execute both legs instantly) or trade the ETF directly if possible.

---

# 9. Conclusion

Markets are not linear.
**Copulas** allow us to trade the **Structure of Reality**, not just the average.
By combining the robustness of Cointegration (Long Term) with the precision of Copulas (Short Term Tail Probabilities), GOLIATH dominates the Statistical Arbitrage game.
