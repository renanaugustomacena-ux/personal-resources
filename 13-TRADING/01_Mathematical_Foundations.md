# 01. Mathematical Foundations of Financial Machine Learning

**Abstract**
Financial time series exhibit unique statistical properties—non-stationarity, low signal-to-noise ratios, and heteroskedasticity—that render standard machine learning pre-processing techniques (e.g., MinMax scaling, integer differencing) ineffective or deleterious. This document establishes the mathematical framework for rigorous feature engineering, focusing on preserving memory via Fractional Differentiation and generating path-dependent targets via the Triple Barrier Method.

---

## 1. The Stationarity vs. Memory Dilemma

Standard supervised learning assumes that the joint distribution of features $(X)$ and labels $(Y)$ is time-invariant (stationary): $P(X_t, Y_t) = P(X_{t+k}, Y_{t+k})$. Financial prices are $I(1)$ (integrated of order 1), i.e., non-stationary random walks.

### 1.1 The Problem with Integer Differentiation
The standard approach to achieve stationarity is integer differentiation (calculating returns):
$$ \Delta P_t = P_t - P_{t-1} $$
While this satisfies the stationarity requirement (making the series $I(0)$), it erases all long-term memory. The correlation between $\Delta P_t$ and $P_{t-k}$ decays to zero rapidly. This removes the trend components that deep learning models (LSTMs, Transformers) rely on for regime detection.

### 1.2 Fractional Differentiation (FracDiff)
Fractional differentiation allows us to derive a time series to the minimum order $d$ required to satisfy the Augmented Dickey-Fuller (ADF) test, while preserving the maximum amount of memory.

**Derivation:**
The backshift operator $B$ is defined as $B^k X_t = X_{t-k}$.
The difference operator $\nabla$ can be expressed as $(1-B)$.
For a real number $d$, we expand $(1-B)^d$ using the generalized binomial theorem:

$$ (1-B)^d = \sum_{k=0}^{\infty} \binom{d}{k} (-1)^k B^k $$

The weights $\omega_k$ for the lagged values are given by:
$$ \omega_k = (-1)^k \binom{d}{k} = (-1)^k \frac{\Gamma(d+1)}{\Gamma(k+1)\Gamma(d-k+1)} $$

**Recursive Weight Calculation:**
Computing factorials for non-integer $d$ is computationally expensive. We use the recursive formulation:
$$ \omega_0 = 1 $$
$$ \omega_k = -\omega_{k-1} \frac{d - k + 1}{k}, \quad \forall k \ge 1 $$

**Convergence & Fixed-Window Implementation:**
The series is infinite. For $d > 0$, the weights $\omega_k$ decay. In practice, we truncate the series at lag $l^*$ where $|\omega_{l^*}| < \tau$ (e.g., $\tau=1e^{-4}$).
The fractionally differentiated series $\tilde{X}_t$ is:
$$ \tilde{X}_t = \sum_{k=0}^{l^*} \omega_k X_{t-k} $$

**Optimization Algorithm:**
1.  Iterate $d$ in $[0, 1]$ with step size $0.05$.
2.  Compute $\tilde{X}_t(d)$.
3.  Perform ADF test on $\tilde{X}_t(d)$.
4.  Select min $d$ such that ADF p-value $< 0.05$. Typical values for Equities/Crypto are $d \in [0.35, 0.55]$.

---

## 2. Advanced Labeling: The Triple Barrier Method

Fixed-time horizon labeling (e.g., "return after 5 days") is flawed because it ignores the path taken by the price. A position might be stopped out (drawdown > 5%) before hitting the target, yet a fixed-horizon label would mark it as a "win" if the price recovers later.

### 2.1 Geometric Brownian Motion & Barriers
We model the price path as a function of volatility. We establish three barriers:
1.  **Upper Barrier (Profit Take):** $u_t = P_t [1 + \mu \sigma_t]$
2.  **Lower Barrier (Stop Loss):** $l_t = P_t [1 - \lambda \sigma_t]$
3.  **Vertical Barrier (Time Out):** $T = t + \Delta t$

Where $\sigma_t$ is a dynamic volatility estimate (e.g., exponentially weighted moving standard deviation) and $\mu, \lambda$ are multipliers.

### 2.2 Path-Dependent Label Generation
Let $\tau$ be the first time the price touches any barrier:
$$ \tau = \min \{ t \in (t_0, T] : P_t \ge u_{t_0} \vee P_t \le l_{t_0} \} $$

The label $Y_i$ takes values in $\{-1, 0, 1\}$:
$$
Y_i = \begin{cases} 
1 & \text{if } P_\tau \ge u_{t_0} \text{ (Profit Hit)} \\
-1 & \text{if } P_\tau \le l_{t_0} \text{ (Stop Loss Hit)} \\
0 & \text{if } \tau > T \text{ (Time Out / Flat)}
\end{cases}
$$

### 2.3 Meta-Labeling (Secondary Model)
To improve the Sharpe ratio, we decompose the problem into two models:
1.  **Primary Model:** A high-recall, low-precision model (e.g., trend following indicator) that suggests a *side* (Long/Short).
2.  **Meta-Model:** A binary classifier that predicts *misclassification*.
    *   **Input:** State features $X_t$ + Primary Model Probability $p$.
    *   **Target:** $Z_t = 1$ if Primary Model was correct (Profit Hit), $Z_t = 0$ otherwise.

**Mathematical Advantage:**
This transformation allows us to filter trades. The Meta-Model learns the *regime* where the Primary Model fails.
$$ E[\text{Strategy}] = \text{Recall} \times \text{Precision} \times \text{BetSize} $$
Meta-labeling directly optimizes Precision without sacrificing the Recall of the primary signal generator.

---

## 3. Sample Weights & Uniqueness

Financial data samples are not independent. If we generate labels based on a 5-day horizon, samples at $t$ and $t+1$ share 4 days of overlapping price history. This creates massive data leakage and inflated t-statistics.

### 3.1 Concurrency & Uniqueness
Let $1_{t,i}$ be an indicator function that is 1 if event $i$ is active at time $t$.
The number of concurrent labels at time $t$ is:
$$ c_t = \sum_{i=1}^N 1_{t,i} $$

The **Uniqueness** of sample $i$ at time $t$ is $u_{t,i} = 1 / c_t$.
The average uniqueness of sample $i$ over its lifespan is:
$$ \bar{u}_i = \frac{\sum_{t=t_{start}}^{t_{end}} u_{t,i}}{t_{end} - t_{start}} $$

**Weighting Strategy:**
When training the neural network, sample $i$ is weighted by $\bar{u}_i$.
$$ L(\theta) = - \sum_{i=1}^N \bar{u}_i \log P(Y_i | X_i; \theta) $$
This penalizes periods of high overlap (typically high volatility clusters) and prevents the model from overfitting to redundant data points.

---

**References:**
1.  Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
2.  Hosking, J. R. M. (1981). "Fractional Differencing". *Biometrika*.