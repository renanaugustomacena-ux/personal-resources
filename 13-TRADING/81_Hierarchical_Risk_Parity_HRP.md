# 81 - Hierarchical Risk Parity (HRP): The Tree of Assets

**Volume:** 81 of 100
**Strategy Type:** Portfolio Construction / Machine Learning / Risk Management
**Risk Profile:** Correlation Instability / Rebalancing Costs / Single Linkage Chaining
**Mathematical Basis:** Hierarchical Clustering (Linkage) + Quasi-Diagonalization + Recursive Bisection

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Markowitz is Broken](#2-the-theory-markowitz-is-broken)
    * 2.1. The Inversion Problem: Markowitz requires inverting the Covariance Matrix ($\Sigma^{-1}$). This is numerically unstable when assets are correlated.
    * 2.2. The Solution: Don't invert. **Cluster**. Group similar assets (e.g., Tech Stocks) and treat the group as one unit.
    * 2.3. Biological Analogy: The portfolio is a tree. Allocate capital to branches, then sub-branches, then leaves.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Input: Historical Returns of $N$ assets. (Rolling Window: 252 days).
    * 3.2. Step 1: Clustering. Compute Distance Matrix ($d_{ij} = \sqrt{2(1-\rho_{ij})}$). Build the Dendrogram using Single Linkage.
    * 3.3. Step 2: Quasi-Diagonalization. Reorder rows/cols of Covariance Matrix so similar assets are adjacent.
    * 3.4. Step 3: Recursive Bisection. Split the list in half. Allocate capital between Left and Right based on Inverse Variance ($1 - \frac{Var_1}{Var_1+Var_2}$).
    * 3.5. Signal: Rebalance Weekly.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Metric: $Correlation \rightarrow Distance$.
    * 4.2. Single Linkage vs Ward's Method: How to define distance between clusters.
    * 4.3. Inverse Variance Allocation: The recursive formula.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. 2008 Crisis: HRP outperformed Markowitz (Mean-Variance). Markowitz concentrated in "Low Volatility" banks that crashed. HRP diversified across clusters.
    * 5.2. Lopez de Prado (2016): The seminal paper "Building Diversified Portfolios that Outperform Out of Sample".
    * 5.3. Crypto Baskets: Allocating to 100 shitcoins. HRP groups them by "Ecosystem" (Eth-tokens, Sol-tokens) automatically without labeling.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Using `scipy.cluster.hierarchy`.
    * 6.2. The `getIVP` (Inverse Variance Portfolio) helper.
    * 6.3. The `getRecBipart` (Recursive Bisection) function.
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. **Hierarchical Equal Risk Contribution (HERC)**: Using Risk Parity instead of Inverse Variance at each split.
    * 7.2. **Detrended Cross-Correlation Analysis (DCCA)**: Clustering based on non-linear dependencies.
    * 7.3. **Constraint Injection**: Forcing min/max weights per cluster (e.g., Max 20% in Crypto).
8. [Risk Management: The Dendrogram](#8-risk-management-the-dendrogram)
    * 8.1. Instability: If the Tree structure changes violently every day, turnover kills returns.
    * 8.2. Signal: If two assets move from "Distant" to "Close" in the tree, Contagion is spreading.
9. [Conclusion: The Structure](#9-conclusion-the-structure)

---

# 1. Executive Summary

**Hierarchical Risk Parity (HRP)** solves the "Markowitz Curse".
Traditional optimization (Mean-Variance) tries to find the perfect inverse of the Covariance Matrix.
But Correlation Matrices are noisy. Inverting noise creates "Toxic Optimality" (allocating 100% to a slightly better asset).
HRP ignores inversion.
It uses **Machine Learning (Clustering)** to understand the *hierarchy* of the market.
It knows that Coca-Cola and Pepsi are "siblings", and that Stocks and Bonds are "cousins".
It allocates robustly through this family tree.
It acknowledges that assets are not isolated islands but part of a connected web.
By allocating to the *structure* of the web, you build a portfolio that can bend without breaking.

---

# 2. The Theory

### 2.1. The Problem with Solvers

Quadratic Programming solvers (CLA) treat all correlations equally.
If Stock A and Stock B have $\rho=0.99$, the solver goes Long A / Short B to exploit the 0.01 difference.
This is dangerous.
HRP recognizes $\rho=0.99$ means "They are the same thing". It splits the budget share between them.

### 2.2. Quasi-Diagonalization

If you reorder the Correlation Matrix based on the Clustering, it becomes **Diagonal-Block**.
Blocks of high correlation appear along the diagonal.
This visualizes the "Sectors" of the market purely from math (no sector labels needed).

### 2.3. Tree vs Matrix

* **Matrix (MVO):** Assumes a complete graph (everyone connected to everyone).
* **Tree (HRP):** Assumes a hierarchy (Parent -> Child).
* **Why Tree?** Biological and Social systems are hierarchical. Financial markets are social systems.

---

# 3. Strategy Rules

### 3.1. Construction

HRP is a **Construction Algo**, not a trading signal.
It determines the *Size* of the positions.
Goliath uses HRP to size its sub-strategies.
Strategy A (Trend) and Strategy B (Mean Rev) might be correlated.
HRP detects this and reduces combined exposure.

### 3.2. Periodicity

Rebalance Weekly.
Daily rebalancing causes too much churn as the Tree flickers.

### 3.3. Input Data

Universe: 10 ETFs (SPY, QQQ, TLT, GLD, VNQ, EEM, etc.) + BTC + ETH.
Logic: Calculate HRP Weights Monthly.
Execution: Rebalance portfolio to target weights.
Crypto Note: HRP naturally limits exposure to BTC/ETH if they are highly volatile and correlated (treating them as a single risky block), preventing the portfolio from being dominated by crypto variance.

---

# 4. Mathematical Derivation

### 4.1. Distance Metric (Step 1)

Correlation $\rho_{i,j} \in [-1, 1]$.
Distance $d_{i,j} = \sqrt{0.5(1 - \rho_{i,j})}$.

* $\rho = 1 \rightarrow d = 0$. (Identical).
* $\rho = -1 \rightarrow d = 1$. (Opposite).
* $\rho = 0 \rightarrow d = \sqrt{0.5}$. (Uncorrelated).

Use Single Linkage clustering to build a Dendrogram.

### 4.2. Quasi-Diagonalization (Step 2)

Reorder the covariance matrix so similar assets are placed together.
This is purely for the recursive step to work linearly.

### 4.3. Recursive Bisection (Step 3)

Cluster $S$ splits into $S_1$ (Left) and $S_2$ (Right).
Variance of Sub-Cluster $S_1$:
$$ V_1 = w_{IVP,1}^T \Sigma_1 w_{IVP,1} $$
Where $w_{IVP}$ are the Inverse Variance weights *within* the cluster.
Allocation Weight to Left Branch:
$$ \alpha_1 = 1 - \frac{V_1}{V_1 + V_2} $$
Repeat recursively until every asset is a leaf.

---

# 5. Historical Case Studies

### 5.1. The COVID Crash (2020)

Strategies correlated to GDP (Stocks, Oil, Real Estate) collapsed together.
HRP had already clustered them.
It had allocated significant capital to the "Anti-Cluster" (Treasuries, Gold, Volatility) because they were distant in the tree.
Result: Lower drawdown than Risk Parity.

### 5.2. Crypto Market Cap

Top 10 coins are highly correlated.
Market Cap Weighted portfolio is 90% Beta.
HRP identifies that BTC and ETH are one cluster, but "DeFi Tokens" are a separate cluster, and "Stablecoins" another.
It forces diversification into the smaller, uncorrelated clusters.

---

# 6. Python Implementation (Production Grade)

```python
import numpy as np
import pandas as pd
import scipy.cluster.hierarchy as sch

def getIVP(cov):
    # Inverse Variance Portfolio
    # Naive risk parity within the slice
    ivp = 1. / np.diag(cov)
    ivp /= ivp.sum()
    return ivp

def getClusterVar(cov, cItems):
    # Compute variance per cluster
    cov_slice = cov.loc[cItems, cItems]
    w = getIVP(cov_slice).reshape(-1, 1)
    cVar = np.dot(np.dot(w.T, cov_slice), w)[0, 0]
    return cVar

def getRecBipart(cov, sortIx):
    # Recursive Bisection
    w = pd.Series(1, index=sortIx)
    cItems = [sortIx]
    while len(cItems) > 0:
        cItems = [i[j:k] for i in cItems for j, k in ((0, len(i) // 2), (len(i) // 2, len(i))) if len(i) > 1]
        for i in range(0, len(cItems), 2):
            cItems0 = cItems[i] # Left
            cItems1 = cItems[i+1] # Right
            
            cVar0 = getClusterVar(cov, cItems0)
            cVar1 = getClusterVar(cov, cItems1)
            
            alpha = 1 - cVar0 / (cVar0 + cVar1)
            w[cItems0] *= alpha
            w[cItems1] *= 1 - alpha
    return w

def hrp_optimization(returns):
    # 1. Correlation & Distance
    corr = returns.corr()
    dist = np.sqrt(0.5 * (1 - corr))
    link = sch.linkage(dist, 'single')
    
    # 2. Quasi-Diagonalization
    sortIx = sch.get_leaves_list(link)
    sortIx = [returns.columns[i] for i in sortIx]
    
    # 3. Recursive Bisection
    cov = returns.cov()
    weights = getRecBipart(cov, sortIx)
    return weights
```

### 6.2. Rust (Conceptual)

```rust
pub struct DendrogramNode {
    id: usize,
    left: Option<Box<DendrogramNode>>,
    right: Option<Box<DendrogramNode>>,
    distance: f64,
}

impl DendrogramNode {
    // Recursive function to traverse and allocate weights
    pub fn allocate(&self, cov_matrix: &Matrix<f64>) -> HashMap<usize, f64> {
        // ... (Inverse Variance Logic) ...
        HashMap::new()
    }
}
```

---

# 7. Optimization

### 7.1. HERC (Hierarchical Equal Risk Contribution)

HRP uses Inverse Variance (naive).
HERC uses Risk Parity inside the cluster.
More robust if assets within the cluster have vastly different volatilities.

### 7.2. De-noising Covariance

Before running HRP, clean the Covariance matrix using Marchenko-Pastur theorem (Random Matrix Theory).
Remove eigenvalues associated with noise.

### 7.3. Signal Use Case (Regime Detection)

Input: Rolling Correlation Matrix of 50 assets.
Observation: In normal markets, assets form distinct clusters (Tech, Energy, Bonds, Crypto).
Signal: When Correlation -> 1.0, the Dendrogram collapses into a single "blob".
Meaning: **Systemic Crisis**. Diversification is dead.
Action: Move to Cash. HRP protects you by recognizing that 50 assets are actually just 1 asset (Beta) in a crash.

---

# 8. Risk Management

### 8.1. The "Single Linkage" Flaw

Single Linkage makes "chains" of assets.
Ward's Method makes "spherical" clusters.
For finance, Ward is often better as it minimizes intra-cluster variance.

### 8.2. Out-of-Sample Decay

HRP assumes the hierarchy is stable.
If "Tech" uncouples from "Consumer Discretionary" tomorrow, the tree is wrong.
**Re-cluster regularly.**

---

# 9. Conclusion

HRP brings **Common Sense** to portfolio optimization.
Markowitz is like a savant calculator that makes stupid mistakes because it takes numbers too literally.
HRP looks at the structure. It says "Don't put all your eggs in the Tech basket, even if the numbers look good."
Goliath uses HRP to manage its internal "Fund of Funds".
It is the strategy of the Architect.
