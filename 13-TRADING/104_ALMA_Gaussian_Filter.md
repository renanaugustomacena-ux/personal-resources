# 104 - Arnaud Legoux Gaussian Filter (ALMA)

**Volume:** 104 of 100
**Strategy Type:** Statistical Filter / Trend Following
**Risk Profile:** Parameter Sensitivity (Sigma/Offset)
**Mathematical Basis:** Gaussian Distribution (Normal Curve) / Convolution

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Gaussian Weights](#2-the-theory-gaussian-weights)
    * 2.1. Why simple weighting (WMA) is suboptimal.
    * 2.2. The Bell Curve: Concentrating weight exactly where you want it.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Golden Offset (0.85).
    * 3.2. Strategy: The ALMA Tunnel.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The ALMA Weighting Function.
    * 4.2. Sigma ($\sigma$) vs Offset.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Computing the Kernel.
    * 5.2. Rust: Vectorized Dot Product.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 104** utilizes the **Arnaud Legoux Moving Average (ALMA)**.
While other MAs try to be "Adaptive" (KAMA/JMA), ALMA relies on pure **Statistics**.
It applies a **Gaussian Filter** (Bell Curve) to the price window.
Crucially, it allows us to shift the *peak* of the Bell Curve.
By shifting the peak to the right (Offset 0.85), we place the maximum weight on the *recent* price, but with a smooth Gaussian drop-off, eliminating the choppiness of standard Weighted Moving Averages.

---

# 2. The Theory: Gaussian Weights

### 2.1. The Weighting Problem

* SMA weights everything equally (Boxcar filter).
* WMA weights linearly (Triangle filter).
* EMA weights exponentially (Decay filter).
* **ALMA weights Normally (Gaussian filter).**

### 2.2. Customizable Lag

ALMA gives us a knob: **Offset**.

* Offset 0.5: Peak is in the middle. Acts like a smooth SMA (Laggy).
* Offset 1.0: Peak is at the current price. Zero lag, high noise.
* **Offset 0.85:** The Sweet Spot. High responsiveness, high smoothness.

---

# 3. The Strategy Rules

### 3.1. The ALMA Tunnel

Instead of a single line, we trade the **Volatility Tunnel**.

1. **Main:** ALMA(Window=50, Offset=0.85, Sigma=6).
2. **Upper:** Main + (Sigma * ATR).
3. **Lower:** Main - (Sigma * ATR).

### 3.2. Execution

* **Trend:** Price is strictly above Main ALMA.
* **Pullback:** Price touches Main ALMA but does not close below Lower Band.
* **Entry:** Bounce off the Main ALMA.
* **Stop:** Close below Lower Band.

---

# 4. Mathematical Derivation

$$ W_i = \exp\left( - \frac{(i - \text{Offset} \times (N-1))^2}{2\sigma^2 (N-1)^2} \right) $$

We calculate the weights $W_i$ for the window $N$.
Then we normalize them so $\sum W_i = 1$.
Then we convolve with Price.

**Sigma ($\sigma$):** Controls the width of the bell curve.

* High Sigma (10): Flat weights (like SMA).
* Low Sigma (2): Sharp peak (focus only on the Offset point).

---

# 5. Implementation: Production Grade

### 5.1. Python

*(From Indicator 104 Source)*

```python
def alma(prices, window=9, offset=0.85, sigma=6):
    m = offset * (window - 1)
    s = window / sigma
    weights = np.exp(-((np.arange(window) - m)**2) / (2 * s * s))
    weights /= weights.sum()
    return prices.rolling(window).apply(lambda x: np.dot(x, weights), raw=True)
```

### 5.2. Rust

This is heavily optimized in Rust using SIMD instructions for the dot product of the weights and price window.

---

# 7. Conclusion

Strategy 104 is **Statistical Purity**.
It doesn't rely on chaotic "Adaptation" that might fail in unforeseen regimes.
It relies on the Gaussian distribution, which is robust and predictable.
It allows GOLIATH to fine-tune the Lag/Smoothness trade-off with mathematical precision ($Offset$ and $\sigma$).
