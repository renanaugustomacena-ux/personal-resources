# 02. Advanced Feature Engineering & Signal Processing

**Abstract**
Raw OHLCV data contains limited information about the underlying supply/demand dynamics. High-frequency traders exploit the Limit Order Book (LOB) to extract predictive alpha. This document details the mathematical formulation of microstructure features (VPIN, OBI), advanced signal denoising via Wavelet Transforms, and regime detection using Information Theoretic metrics (Entropy).

---

## 1. Microstructure & Order Flow Dynamics

The Limit Order Book (LOB) represents the queue of passive liquidity. Changes in the LOB precede price movements.

### 1.1 Volume Synchronized Probability of Informed Trading (VPIN)
VPIN estimates the toxicity of order flow—the probability that a trade is informed (i.e., based on private information) rather than noise.

**Mathematical Formulation:**
Let $V$ be the volume bucket size (e.g., every 100 contracts).
Let $\tau$ index the volume buckets.
Let $V_{\tau}^B$ and $V_{\tau}^S$ be the buy and sell volume within bucket $\tau$.
The total volume is $V = V_{\tau}^B + V_{\tau}^S$.

$$ VPIN = \frac{\sum_{\tau=1}^n |V_{\tau}^B - V_{\tau}^S|}{nV} $$

Where $n$ is the number of buckets considered (window size).
A high VPIN indicates significant order imbalance and potential adverse selection risk.

**Classifying Aggressor Side (BVC / Tick Rule):**
Since we don't always know who initiated the trade, we use the Tick Rule:
$$ b_t = \begin{cases} 1 & \text{if } P_t > P_{t-1} \\ -1 & \text{if } P_t < P_{t-1} \\ b_{t-1} & \text{if } P_t = P_{t-1} \end{cases} $$
Or the Bulk Volume Classification (BVC) algorithm which uses the change in price over the interval relative to the standard deviation.

### 1.2 Order Book Imbalance (OBI)
OBI measures the pressure from limit orders at the best bid/ask and deeper levels.

**Level 1 Imbalance:**
Let $q_t^b$ be the bid size at Level 1, and $q_t^a$ be the ask size.
$$ \rho_t = \frac{q_t^b - q_t^a}{q_t^b + q_t^a} \in [-1, 1] $$
If $\rho_t \to 1$, buying pressure is high. If $\rho_t \to -1$, selling pressure is high.

**Weighted Depth Imbalance:**
To capture deeper liquidity, we use a decay factor $\lambda$ (e.g., $1/\log(i+1)$).
$$ \rho_{W,t} = \sum_{i=1}^L \frac{1}{\log(i+1)} \left( \frac{q_{t,i}^b - q_{t,i}^a}{q_{t,i}^b + q_{t,i}^a} \right) $$

---

## 2. Spectral Analysis & Denoising (Wavelets)

Financial time series are non-stationary and composed of multiple frequencies (trends, cycles, noise). Fourier Transform assumes stationarity. Wavelet Transform handles non-stationary signals by localizing in both time and frequency.

### 2.1 Discrete Wavelet Transform (DWT)
We decompose the signal $X_t$ using a mother wavelet $\psi(t)$ and a scaling function $\phi(t)$.
The signal is represented as:
$$ X_t = \sum_k c_{J,k} \phi_{J,k}(t) + \sum_{j=1}^J \sum_k d_{j,k} \psi_{j,k}(t) $$

Where:
*   $c_{J,k}$ are the **Approximation Coefficients** (Trend / Low Frequency).
*   $d_{j,k}$ are the **Detail Coefficients** (Noise / High Frequency) at scale $j$.

### 2.2 Wavelet Denoising (Soft Thresholding)
To remove noise while preserving features:
1.  Compute DWT of $X_t$.
2.  Apply thresholding to detail coefficients $d_{j,k}$:
    $$ \hat{d}_{j,k} = \text{sign}(d_{j,k}) \max(0, |d_{j,k}| - \lambda) $$
    Where $\lambda = \sigma \sqrt{2 \log N}$ (Universal Threshold).
3.  Reconstruct the signal using Inverse DWT (IDWT).

This yields a smooth trend component suitable for trend-following algorithms, robust to high-frequency noise.

---

## 3. Information Theoretic Regime Detection

Market efficiency varies over time. Sometimes prices follow a Random Walk (Efficient Market Hypothesis), other times they exhibit predictable serial correlation (Inefficient).

### 3.1 Shannon Entropy
$$ H(X) = - \sum_{i} P(x_i) \log_2 P(x_i) $$
High entropy implies high uncertainty (randomness). Low entropy implies predictability.

### 3.2 Approximate Entropy (ApEn) & Sample Entropy (SampEn)
These metrics quantify the regularity of a time series.
**Algorithm:**
1.  Form vectors $x_i$ of length $m$ from the time series.
2.  Count the number of vectors $x_j$ such that the distance $d[x_i, x_j] \le r$ (tolerance).
3.  Let $C_i^m(r)$ be the probability that a vector matches $x_i$.
4.  ApEn is the negative natural logarithm of the conditional probability that two sequences similar for $m$ points remain similar at the next point.

$$ SampEn(m, r, N) = - \ln \left( \frac{\sum C_i^{m+1}(r)}{\sum C_i^m(r)} \right) $$

**Application as a Regime Filter:**
*   If $SampEn_t > \theta$ (High Entropy) $\to$ **Mean Reversion / Stat Arb**. (Market is noisy/efficient).
*   If $SampEn_t < \theta$ (Low Entropy) $\to$ **Trend Following**. (Market is trending/inefficient).

---

**References:**
1.  Easley, D., et al. (2012). "The Volume Synchronized Probability of Informed Trading (VPIN)".
2.  Percival, D. B., & Walden, A. T. (2000). *Wavelet Methods for Time Series Analysis*. Cambridge University Press.
3.  Pincus, S. M. (1991). "Approximate Entropy as a Measure of System Complexity". *PNAS*.