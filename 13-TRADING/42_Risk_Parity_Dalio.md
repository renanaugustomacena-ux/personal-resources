# 42 - Risk Parity: The All Weather

**Volume:** 42 of 50
**Strategy Type:** Portfolio Management / Asset Allocation / Ray Dalio
**Risk Profile:** Low Volatility / High Sharpe / Leverage Risk
**Mathematical Basis:** $\text{Risk Contribution}_i = w_i \times \sigma_i \times \text{Corr}(i, P)$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Stocks are too Risky](#2-the-theory-stocks-are-too-risky)
    * 2.1. The 60/40 Portfolio is actually 90/10 Risk
    * 2.2. Equalizing Risk Contribution (ERC)
    * 2.3. Ray Dalio & Bridgewater Associates
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Calculate Volatility of Assets (Stocks, Bonds, Gold, Commodities)
    * 3.2. Inverse Volatility Weighting ($w_i \propto 1/\sigma_i$)
    * 3.3. Leverage Low Vol Assets to match target (Bonds need 3x leverage)
    * 3.4. Rebalance to maintain Parity
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Portfolio Variance: $\sigma_p^2 = w^T \Sigma w$
    * 4.2. Marginal Risk Contribution: $\frac{\partial \sigma_p}{\partial w_i}$
    * 4.3. Optimization Goal: $\text{RC}_i = \text{RC}_j$ for all $i,j$
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. The All Weather Fund (1996-2022)
    * 5.2. 2022: The Year Risk Parity failed (Stocks and Bonds down together)
    * 5.3. Leveraged ETFs (NTSX: 90/60 Portfolio)
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Estimating Covariance Matrix (Shrinkage Ledoit-Wolf)
    * 6.2. Solving for Weights (SciPy Optimize)
    * 6.3. Handling Leverage Limits
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. Hierarchy (Risk Parity within Sectors, then within Asset Classes)
    * 7.2. Trend Following Overlay (Reduce Bond risk if trend is down)
    * 7.3. Adaptive Covariance (Short vs Long lookback)
8. [Risk Management: Correlation Breakdown](#8-risk-management-correlation-breakdown)
    * 8.1. Risk Parity assumes Stocks and Bonds are negatively correlated.
    * 8.2. If Inflation spikes, Correlation goes to +1.
    * 8.3. Both levers of the portfolio lose money.
    * 8.4. **Defense:** Add Commodities/Gold (Inflation Hedge).
9. [Conclusion: Engineering Balance](#9-conclusion-engineering-balance)

---

# 1. Executive Summary

**Risk Parity** challenges the traditional 60/40 portfolio (60% Stocks, 40% Bonds).
In a 60/40, Stocks have 15% Volatility. Bonds have 5% Volatility.
90% of the portfolio's risk comes from Stocks.
It is an equity bet disguised as diversification.
**Risk Parity** allocates capital so that each asset class contributes equal risk.
Result: You hold way more Bonds (leveraged) and Commodities.
Result: Higher Sharpe Ratio, lower Drawdowns.

---

# 2. The Theory

### 2.1. The Four Quadrants

Dalio says asset prices are driven by two forces:

1. Growth (Rising / Falling)
2. Inflation (Rising / Falling)

* **Stocks:** Good in Rising Growth.
* **Bonds:** Good in Falling Growth (Deflation).
* **Gold/Commodities:** Good in Rising Inflation.
* **Cash/TIPS:** Good in Falling Inflation (Monetary Tightening).
A true "All Weather" portfolio holds assets that perform well in each quadrant.

### 2.2. Leverage is Essential

Bonds are safer than stocks. To make them matter, you must leverage them.
If Stocks return 8% with 15% Vol.
And Bonds return 4% with 5% Vol.
Leverage Bonds 3x $\to$ 12% Return with 15% Vol.
Now you have two assets with equal risk and similar returns.
Diversification works better when risks are balanced.

---

# 3. Strategy Rules

### 3.1. Inverse Volatility

Simple heuristic:
$$ w_i = \frac{1/\sigma_i}{\sum (1/\sigma_j)} $$
If Vol(Stock) = 20% and Vol(Bond) = 5%.
Ratio = 4:1.
Allocate 20% to Stocks, 80% to Bonds.
Risk Contribution: $0.20 \times 20\% = 4$. $0.80 \times 5\% = 4$. Parity achieved.

### 3.2. Leverage Target

Target Portfolio Volatility = 10%.
If the unlevered portfolio has 4% Volatility.
Leverage everything 2.5x.

---

# 4. Mathematical Derivation

Total Risk $R(w) = \sqrt{w^T \Sigma w}$.
Risk Contribution of asset $i$:
$$ RC_i = w_i \frac{(\Sigma w)_i}{\sqrt{w^T \Sigma w}} $$
We minimize the objective function:
$$ \min_w \sum_{i=1}^N \sum_{j=1}^N (RC_i - RC_j)^2 $$
Subject to $\sum w_i = 1$ (and leverage constraints).

---

# 5. Historical Case Studies

### 5.1. Bridgewater All Weather

Launched in 1996.
Survived 2000 (Tech Crash) and 2008 (GFC) with minimal drawdowns compared to SPX.
Assets under management grew to $150 Billion.

### 5.2. The 2022 Inflation Shock

Stocks fell -20%.
Bonds fell -15% (Worst year in history).
Risk Parity funds fell -30% due to leverage.
**Lesson:** Inflation breaks the central premise of Risk Parity (Negative Stock/Bond correlation).
Commodities helped, but not enough.

---

# 6. Python Implementation

```python
import numpy as np
from scipy.optimize import minimize

class RiskParityOptimizer:
    def __init__(self, returns_df):
        self.cov_matrix = returns_df.cov()
        self.assets = returns_df.columns

    def risk_contribution(self, weights):
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        # Marginal Risk Contribution
        mrc = np.dot(self.cov_matrix, weights) / portfolio_vol
        # Risk Contribution
        rc = weights * mrc
        return rc

    def objective_function(self, weights):
        rc = self.risk_contribution(weights)
        target_rc = np.mean(rc)
        return np.sum((rc - target_rc)**2) # Minimize variance of RCs

    def optimize(self):
        n = len(self.assets)
        initial_w = np.ones(n) / n
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
        bounds = tuple((0, 1) for _ in range(n))
        
        result = minimize(self.objective_function, initial_w, 
                         method='SLSQP', bounds=bounds, constraints=constraints)
        return result.x
```

### 6.3. Hierarchical Risk Parity (HRP)

Marcos Lopez de Prado suggests clustering assets first.
Cluster 1: Tech, Consumer, Indu.
Cluster 2: Treasuries, Corp Bonds.
Allocate Risk Parity between Clusters. Then within Clusters.
This is more robust to correlation shocks.

---

# 7. Optimization

### 7.1. Volatility Targeting

If Market Volatility is low (VIX 12), leverage up to target 10% Vol.
If Market Volatility is high (VIX 40), deleverage.
"Constant Risk Exposure".

### 7.2. Trend Filter

Dalio's "Pure Alpha".
If Bond Trend is Negative (Rates rising), reduce Risk Budget to Bonds.
Shift to Cash.

---

# 8. Risk Management

### 8.1. Leverage Kill

If you are 3x levered on Bonds.
A 3% drop in Bonds = 9% Drawdown.
Margin Calls can force liquidation at the bottom.
**Rule:** Max Portfolio Leverage = 2.0x.
Use Options (Calls) instead of Futures to limit downside risk.

### 8.2. Regime Change

We were in a 40-year Bond Bull Market (1981-2021).
Risk Parity was perfect.
If we enter a 20-year Bond Bear Market?
The strategy must adapt (Favor Commodities/Real Assets over Nominal Bonds).

---

# 9. Conclusion

Risk Parity is the "Engineer's Portfolio".
It ignores stories and focuses on math.
For GOLIATH, we use Risk Parity for our "Core Beta" allocation.
We do not want our PnL to be 90% correlated to Bitcoin.
We hold Bitcoin, Stablecoins (Cash), and Gold/PaxG in risk-parity weights.
This smooths the equity curve and allows us to survive Crypto Winters.
