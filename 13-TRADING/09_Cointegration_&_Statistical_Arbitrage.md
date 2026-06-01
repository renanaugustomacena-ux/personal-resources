# 09. Cointegration & Statistical Arbitrage Strategies

**Abstract**
Statistical Arbitrage (StatArb) relies on the identification of long-term equilibrium relationships between non-stationary assets. This document details the **Vector Error Correction Model (VECM)** for modeling short-term dynamics, the **Johansen Test** for cointegration rank determination, and **Kalman Filters** for adaptive hedge ratio estimation.

---

## 1. Cointegration & Equilibrium

Two non-stationary time series $X_t, Y_t \sim I(1)$ are cointegrated if there exists a linear combination $Z_t = Y_t - \beta X_t$ that is stationary ($I(0)$).

### 1.1 The Johansen Test
The Johansen procedure tests for the number of cointegrating vectors in a VAR($p$) model:
$$ \Delta Y_t = \Pi Y_{t-1} + \sum_{i=1}^{p-1} \Gamma_i \Delta Y_{t-i} + \epsilon_t $$

Where $Y_t$ is a vector of $k$ assets.
The matrix $\Pi$ has rank $r$ ($0 \le r < k$).
*   If $r=0$: No cointegration.
*   If $0 < r < k$: Cointegration exists. $\Pi = \alpha \beta'$, where $\beta$ contains the cointegrating vectors (long-run relationship) and $\alpha$ contains the adjustment speeds.

**Hypothesis Testing (Trace Statistic):**
$$ \lambda_{trace}(r) = -T \sum_{i=r+1}^k \ln(1 - \hat{\lambda}_i) $$
We reject the null hypothesis of at most $r$ cointegrating vectors if $\lambda_{trace} > 	ext{Critical Value}$.

---

## 2. Vector Error Correction Model (VECM)

Once cointegration is established, we model the system as a VECM.

### 2.1 The Model
$$ \Delta Y_t = \alpha ( \beta' Y_{t-1} - \mu ) + \sum_{j=1}^{p-1} \Gamma_j \Delta Y_{t-j} + \epsilon_t $$

*   **Error Correction Term ($ECT_{t-1} = \beta' Y_{t-1} - \mu$):** The deviation from equilibrium.
*   **Speed of Adjustment ($\alpha$):** How fast the prices revert to the mean. If $\alpha$ is large, the mean reversion is fast (good for HFT).

**Trading Signal:**
We trade the spread $Z_t = \beta' Y_t$.
*   Long spread if $Z_t < \mu - k \sigma$.
*   Short spread if $Z_t > \mu + k \sigma$.
*   Exit when $Z_t \approx \mu$.

---

## 3. Dynamic Hedge Ratios via Kalman Filter

Static hedge ratios ($\beta$) fail when market structure changes. The Kalman Filter estimates time-varying parameters.

### 3.1 State Space Representation
**Measurement Equation:**
$$ y_t = \beta_t x_t + \epsilon_t, \quad \epsilon_t \sim \mathcal{N}(0, V_\epsilon) $$
**State Equation (Random Walk):**
$$ \beta_t = \beta_{t-1} + \omega_t, \quad \omega_t \sim \mathcal{N}(0, V_\omega) $$

Where $y_t$ is the price of Asset A, $x_t$ is the price of Asset B, and $\beta_t$ is the dynamic hedge ratio.

### 3.2 The Filter Algorithm
1.  **Predict:**
    $$ \hat{\beta}_{t|t-1} = \hat{\beta}_{t-1|t-1} $$
    $$ P_{t|t-1} = P_{t-1|t-1} + V_\omega $$
2.  **Update:**
    $$ K_t = P_{t|t-1} x_t (x_t P_{t|t-1} x_t + V_\epsilon)^{-1} $$
    $$ \hat{\beta}_{t|t} = \hat{\beta}_{t|t-1} + K_t (y_t - x_t \hat{\beta}_{t|t-1}) $$
    $$ P_{t|t} = (I - K_t x_t) P_{t|t-1} $$

This recursively updates $\beta_t$ at every time step, capturing structural breaks (e.g., policy shifts) instantly.

---

**References:**
1.  Engle, R. F., & Granger, C. W. J. (1987). "Co-integration and Error Correction: Representation, Estimation, and Testing".
2.  Johansen, S. (1988). "Statistical Analysis of Cointegration Vectors".
3.  Kalman, R. E. (1960). "A New Approach to Linear Filtering and Prediction Problems".
