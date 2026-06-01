# 85 - Entropy Pooling: The Information Processor

**Volume:** 85 of 100
**Strategy Type:** Portfolio Construction / Information Theory / Advanced Statistics
**Risk Profile:** Complexity / Numerical Instability (KL Divergence Optimization)
**Mathematical Basis:** Relative Entropy (Kullback-Leibler Divergence): $\tilde{p} = \text{argmin}_p \sum p_j (\ln p_j - \ln q_j)$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Beyond Black-Litterman](#2-the-theory-beyond-black-litterman)
    * 2.1. The Limitation: Black-Litterman assumes Normal Distribution and Linear Views.
    * 2.2. The Generalization: Entropy Pooling processes ANY distribution (Fat Tails, Skewed) and ANY view.
    * 2.3. The Principle of Minimum Discrimination Information: Modify the Prior distribution ($q$) *as little as possible* to satisfy the new views.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Input: Prior Distribution (Historical Simulation). $J$ Scenarios.
    * 3.2. Views: Defined as constraints on the probabilities. $A p \le b$.
    * 3.3. Optimization: Find $p$ that minimizes $D_{KL}(p || q)$.
    * 3.4. Output: New Probabilities. Calculate Portfolio Expected Shortfall (ES).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Objective Function (KL Divergence).
    * 4.2. Analytical Solution via Lagrange Multipliers.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Attilio Meucci (2008): Introduced "Fully Flexible Views".
    * 5.2. Stress Testing: Banks use EP for margin calc under stress.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Representing the Market as Scenarios.
    * 6.2. Dual Formulation optimization.
7. [Run Strategy: "The Scenario Trader"](#7-run-strategy-the-scenario-trader)
    * 7.1. Analyzing History using Views.
    * 7.2. Left-Tail Hedging.
8. [Risk Management](#8-risk-management)
9. [Conclusion: The Oracle](#9-conclusion-the-oracle)

---

# 1. Executive Summary

**Entropy Pooling (EP)** is the most advanced framework for processing subjective views.
Standard models force you to think in terms of "Returns".
Entropy Pooling lets you think in terms of **Probabilities**.
"I think the probability of a crash is 20%".
Values in the distribution are kept (so Fat Tails remain), but their probabilities are re-weighted.
It takes a Prior distribution (Historical Data) and *twists* it to match your views, minimizing the information added.

---

# 2. The Theory

### 2.1. The Histogram

Imagine the market distribution as a histogram of 10,000 past days.
Each day has probability $p = 1/10,000$.
You have a view: "Volatility will be high".
Entropy Pooling increases the probability $p$ of the *high volatility days* in the history.
The histogram shape changes.

### 2.2. KL Divergence

$D_{KL}(p || q) = \sum p \ln(p/q)$.
This measures the "distance" between the Prior and Posterior distributions.
Minimizing this ensures we respect the history as much as possible while satisfying the view constraint.

---

# 3. Strategy Rules

### 3.1. Scenario Analysis

**View:** "If Oil > \$100, Airline stocks will crash."
**EP Process:** Filter historical days where Oil > \$100. Assign them higher probability (e.g., sum of $p$ for these days = 0.5).
**Result:** The Expected Return of Airlines drops in the new distribution.

### 3.2. Left-Tail Hedging

**View:** "The probability of a -20% crash is 5% (Market implies 1%)."
**EP Process:** Re-weight the -20% tail events (2008, 2020) to have 5% total mass.
**Action:** Optimizer allocates to Puts to suppress the new VaR.

---

# 4. Mathematical Derivation

**Lagrangian:**
$$ L = \sum p_j (\ln p_j - \ln q_j) + \lambda_0 (\sum p_j - 1) + \lambda' (H p - h) $$

**First Order Condition:**
$$ p_j = q_j \exp(-\lambda_0 - 1 - \lambda' H_j) $$

This shows the solution is an exponential tilt of the prior.

---

# 5. Historical Case Studies

### 5.1. 2022 Inflation View

PMs had a view: "Inflation will break correlations."
Using Entropy Pooling, they imposed a view: $Corr(Stock, Bond) = 0.5$ (historically -0.4).
The optimizer lowered weights in Risk Parity strategies significantly.

---

# 6. Python Implementation (Production Grade)

```python
import numpy as np
import scipy.optimize as so

def entropy_pooling(p, A, b):
    # p: Prior probabilities (J x 1)
    # A: View Matrix (K x J) -> K views on J scenarios
    # b: View Targets (K x 1)
    
    # Dual Problem: Maximize L(lambda)
    # Unconstrained convex optimization on lambda
    
    def dual_loss(lam):
        # lam is vector of K lagrange multipliers
        # p_new = p * exp(- A.T @ lam)
        # log partition function
        log_Z = np.log(np.sum(p * np.exp(- np.dot(A.T, lam))))
        return np.dot(b.T, lam) + log_Z

    # Solve
    res = so.minimize(dual_loss, x0=np.zeros(len(b)))
    lam_star = res.x
    
    # Recover Primal Probabilities
    p_star = p * np.exp(- np.dot(A.T, lam_star))
    p_star /= np.sum(p_star)
    
    return p_star
```

---

# 7. Run Strategy: "The Scenario Trader"

**Rules:**

1. **Prior:** 10 years of historical weekly returns (Historical Simulation).
2. **View 1:** "Inflation is sticky." (Constraint: Avg CPI > 3%).
3. **View 2:** "Tech is a bubble." (Constraint: Nasdaq Returns < 0%).
4. **Process:** Run EP. Get new probability weights.
5. **Optimize:** Maximize Utility using the *new* probabilities.
6. **Result:** A portfolio that is robust *if your specific scenarios come true*.

---

# 8. Risk Management

### 8.1. Effective Number of Scenarios ($J_{eff}$)

$J_{eff} = \exp(-\sum p \ln p)$.
If $J_{eff} / J < 0.10$, your view is too strong. You are effectively using only 10% of your data.
**Warning Flag.**

### 8.2. Overfitting

In Sample Entropy Pooling always works.
Out of Sample, it relies on your View accuracy.
Use EP to inject **Macro Wisdom**, not to fit noise.

---

# 9. Conclusion

Entropy Pooling is the **Brain** of Goliath.
It allows the system to digest heterogeneous information.
News (NLP) $\rightarrow$ View on Probability.
Options Market $\rightarrow$ View on Volatility.
It fuses them all into a single, coherent Probability Distribution.
It is the strategy of the Sage.
