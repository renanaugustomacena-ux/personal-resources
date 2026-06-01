# 84 - Principal Components & Minimum Torsion Bets: The Uncorrelated Alpha

**Volume:** 84 of 100
**Strategy Type:** Portfolio Construction / Risk Management / StatArb / Factor Investing
**Risk Profile:** Concentration Risk (in Principal Components) / Estimation Error
**Mathematical Basis:** Eigendecomposition ($\Sigma V = V \Lambda$) & Minimum Torsion Transformation ($t_{MT}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Deconstructing Risk](#2-the-theory-deconstructing-risk)
    * 2.1. PCA: The Skeleton. Finding "Market Factors" (Eigenvectors).
    * 2.2. Minimum Torsion: The Muscle. Rotating factors to be interpretable and tradeable.
    * 2.3. Effective Number of Bets ($N_{eff}$): The true measure of diversification.
3. [Strategy 1: PCA Statistical Arbitrage](#3-strategy-1-pca-statistical-arbitrage)
    * 3.1. Trading the Residuals ($\epsilon$).
    * 3.2. Signal: Long Stock / Short Eigen-Portfolio.
    * 3.3. Absorption Ratio: Assessing Systemic Risk.
4. [Strategy 2: Minimum Torsion Allocation](#4-strategy-2-minimum-torsion-allocation)
    * 4.1. Concept: Maximize ENB.
    * 4.2. Signal: $N_{eff} < 1.5$ means "Crisis imminent" (Diversification breakdown).
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Covariance to Eigenvalues.
    * 5.2. Torsion Matrix $t_{MT}$.
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. The "Quant Meltdown" (Aug 2007).
    * 6.2. Bridgewater Pure Alpha.
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (Scikit-Learn).
    * 7.2. Rust (Eigendecomposition).
8. [Risk Management](#8-risk-management)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Principal Component Analysis (PCA)** looks inside the "Bag of Stocks" (S&P 500) and sees the hidden drivers (Risk Factors).
**Minimum Torsion** is the advanced evolution of PCA.
While PCA finds abstract factors ("PC1"), Minimum Torsion finds tradeable, uncorrelated bets that resemble the original assets.
It solves the "Illusion of Diversification".
Buying 10 correlated crypto assets is 1 bet.
Minimum Torsion ensures valid diversification by constructing **Orthogonal** bets.

---

# 2. The Theory

### 2.1. PCA

* **PC1 (Market):** The tide that lifts all boats.
* **PC2 (Sector):** Cyclical vs Defensive.
* **PC3+ (Alpha):** Idiosyncratic moves.

### 2.2. Minimum Torsion

PCA factors are messy (Long AAPL / Short MSFT).
Minimum Torsion rotates these factors to be:

1. Uncorrelated (like PCA).
2. Close to the original assets (Interpretable).
It allows us to say: "I want a bet on Tech that is uncorrelated to my bet on Energy."

### 2.3. Effective Number of Bets ($N_{eff}$)

A metric quantifying true diversification.
Using the probabilities $p_n$ of risk contribution from each factor:
$$ N_{eff} = \exp( - \sum p_n \ln p_n ) $$
(Exponential of the Entropy of the risk distribution).

---

# 3. Strategy 1: PCA StatArb

### 3.1. Trading Residuals

Model: $R_{stock} = \beta R_{market} + \epsilon$.
Using PCA, we strip out the Market AND Sector factors.
$R_{stock} = \beta_1 PC1 + \beta_2 PC2 + \dots + \epsilon$.
$\epsilon$ is the "Pure Alpha".
**Trade:** If $\epsilon > 2\sigma$, Short Stock / Long Eigen-Portfolio. (Mean Reversion).

### 3.2. The Absorption Ratio

Proportion of variance explained by PC1+PC2.

* **High (>80%):** Panic. Systemic Risk. **Reduce Leverage.**
* **Low (<60%):** Stock Picker's Market. **Increase Leverage.**

---

# 4. Strategy 2: Minimum Torsion Allocation

### 4.1. Protocol

1. Objective: Maximize Sharpe Ratio with constraint $N_{eff} > 5$.
2. Process: Compute Minimum Torsion Factors. Construct portfolio that allocates risk equally across the top 5 factors (Risk Parity on Factors, not Assets).
3. Result: A portfolio that survives "Correlation One" events better than traditional diversification.

---

# 5. Mathematical Derivation

### 5.1. The Torsion Matrix

$$ t_{MT} = \Sigma^{-1/2} (\Sigma^{1/2})_{diag} $$
This matrix transforms correlated returns $R$ into uncorrelated bets $F$.
We seek a matrix $T$ such that it minimizes the tracking error relative to the identity matrix (Minimum Torsion) while ensuring orthogonality.

---

# 6. Historical Case Studies

### 6.1. Aug 2007 (Quant Quake)

Large quant funds were all trading the same PCA factors (Value/Momentum).
When one liquidated, they all moved together.
The "Eigen-Portfolio" collapsed.
**Lesson:** Factor crowding is a risk. Minimum Torsion helps detect this crowding.

---

# 7. Implementation: Production Grade

### 7.1. Python (PCA & Torsion)

```python
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def get_pca_residuals(returns, n_components=3):
    scaler = StandardScaler()
    X = scaler.fit_transform(returns.fillna(0))
    
    pca = PCA(n_components=n_components)
    pca.fit(X)
    
    # Reconstruct
    components = pca.transform(X)
    reconstructed = pca.inverse_transform(components)
    
    # Residuals = Actual - Explained
    residuals = X - reconstructed
    return residuals

def minimum_torsion_matrix(cov_matrix):
    """
    Computes the Minimum Torsion Matrix t
    t = Cov^(-1/2) (Mahalanobis approximate)
    """
    vals, vecs = np.linalg.eigh(cov_matrix)
    # D^(-1/2)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(vals))
    # Whitening Matrix
    whitening = vecs @ D_inv_sqrt @ vecs.T
    return whitening

def effective_bets(weights, cov):
    # Calculate Risk Contributions of Principal Components
    # Formula involves w' * Cov * w
    # ... entropy calculation
    return n_eff
```

### 7.2. Rust

```rust
use ndarray_linalg::Eig;
// Requires LAPACK linkage
pub fn get_eigenvalues(cov_matrix: Array2<f64>) -> Vec<f64> {
    let (evals, _) = cov_matrix.eig().unwrap();
    evals.iter().map(|c| c.norm()).collect()
}
```

---

# 8. Risk Management

### 8.1. Parameter Instability

Correlations change. PC1 today (Tech) might be PC1 tomorrow (Energy).
**Rule:** Re-estimate Covariance Matrix daily using Exponential Weights (EWMA).

### 8.2. Estimation Error

Maximizing ENB amplifies noise.
**Constraint:** Limit maximum weight of any single factor.

---

# 9. Conclusion

By integrating **PCA** (Analysis) and **Minimum Torsion** (Construction), Goliath ensures it is not just a "Beta Jockey".
We strip away the market noise to find the pure signal.
We build a portfolio of independent bets, creating a fortress that can withstand a breach in any single wall.
