# Indicator 031: Linear Regression Slope - The Angle of Attack

**"The trend is your friend, but the slope is your speedometer."**

---

## 1. Executive Summary

**Linear Regression** is the "Hello World" of Machine Learning.
In trading, the **Linear Regression Slope** ($m$) measures the *rate of change* of price over a specific lookback period.
Unlike a Moving Average (which is a single point), Linear Regression fits a "Best Fit Line" through the cloud of points.

It answers the question: **"How fast is the price rising per bar, on average?"**

* **High Positive Slope:** Violent Uptrend (Parabolic).
* **Low Positive Slope:** Sustainable Uptrend.
* **Zero Slope:** Consolidation.

---

## 2. Historical Context: Francis Galton

Linear Regression was developed by **Sir Francis Galton** in the late 19th century (originally to study genetics and "Regression to the Mean").
In the 1990s, with the rise of PC trading, traders started applying OLS (Ordinary Least Squares) to rolling windows of price data to determine the mathematical "Angle of Attack."

---

## 3. Mathematical Foundations

We fit a line equation $y = mx + c$ through $n$ data points $(x, y)$.

* $x$: Time (0, 1, 2, ... $n-1$).
* $y$: Price ($P_0, P_1, ... P_{n-1}$).

### 3.1 The OLS Formula for Slope ($m$)

$$ m = \frac{n \sum(xy) - \sum x \sum y}{n \sum(x^2) - (\sum x)^2} $$

Where:

* $\sum x$: Sum of time indices.
* $\sum y$: Sum of prices.
* $\sum xy$: Sum of Time $\times$ Price products.
* $\sum x^2$: Sum of squared time indices.

### 3.2 The Angle ($\theta$)

Slope is in "\$ per bar". To get degrees:
$$ \theta = \arctan(m) $$
*Note: This requires normalizing the axes (Time vs Price) to be comparable.*

---

## 4. Signal Generation and Interpretation

### 4.1 Direction

* **$m > 0$:** Uptrend.
* **$m < 0$:** Downtrend.

### 4.2 Acceleration (The Change in Slope)

HFTs look at the derivative of the slope ($dm/dt$).

* If Slope is Positive and Increasing: **Parabolic**.
* If Slope is Positive but Decreasing: **Exhaustion** (Rounding Top).

### 4.3 The $R^2$ Filter

The fit isn't always good.

* **High $R^2$ (> 0.9):** The trend is smooth and clean. Trust the slope.
* **Low $R^2$ (< 0.5):** The trend is noisy. The slope is meaningless.

---

## 5. Microstructure & HFT

HFTs use Linear Regression Slope on the **Micro-Price** (Weighted Midpoint) to predict immediate order book pressure.
If the Slope of the last 10 ticks is $> X$, they will aggressively lift the Ask, anticipating a breakout.

---

## 6. Implementation

### 6.1 Python (Scipy Linregress)

```python
import pandas as pd
import numpy as np
from scipy.stats import linregress

def calculate_slope(series: pd.Series, period=20):
    """
    Calculate Rolling Linear Regression Slope.
    """
    slopes = []
    r_squares = []
    
    # Pre-calculate x (0, 1, ... period-1)
    x = np.arange(period)
    
    for i in range(len(series)):
        if i < period:
            slopes.append(np.nan)
            r_squares.append(np.nan)
            continue
            
        y = series.iloc[i-period:i].values
        
        # Scipy is slow for rolling, typically use Numpy vectorization manually
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        
        slopes.append(slope)
        r_squares.append(r_value**2)
        
    return pd.Series(slopes, index=series.index), pd.Series(r_squares, index=series.index)
```

### 6.2 Rust (Optimized OLS)

Since $x$ is always $0 \dots n-1$, $\sum x$ and $\sum x^2$ are constants we can precompute!

$$ \sum_{i=0}^{n-1} i = \frac{n(n-1)}{2} $$
$$ \sum_{i=0}^{n-1} i^2 = \frac{n(n-1)(2n-1)}{6} $$

This makes the update $O(1)$ instead of $O(n)$.

```rust
use std::collections::VecDeque;

pub struct RollingSlope {
    period: usize,
    prices: VecDeque<f64>,
    sum_y: f64,
    sum_xy: f64, // Sum(Price * Index) where Index is 0..period-1
    
    // Precomputed constants
    sum_x: f64,
    sum_x_sq: f64,
    denominator: f64,
}

impl RollingSlope {
    pub fn new(period: usize) -> Self {
        let n = period as f64;
        let sum_x = n * (n - 1.0) / 2.0;
        let sum_x_sq = n * (n - 1.0) * (2.0 * n - 1.0) / 6.0;
        let denom = (n * sum_x_sq) - (sum_x * sum_x);
        
        Self {
            period,
            prices: VecDeque::new(),
            sum_y: 0.0,
            sum_xy: 0.0,
            sum_x,
            sum_x_sq,
            denominator: denom,
        }
    }

    pub fn update(&mut self, price: f64) -> Option<f64> {
        self.prices.push_back(price);
        
        if self.prices.len() > self.period {
            let old_price = self.prices.pop_front().unwrap();
            
            // Standard sliding window update for Sum Y
            self.sum_y -= old_price;
            
            // Tricky part: Update SumXY
            // When we shift left, every existing y[i] which was multipled by x[i]
            // is now multiplied by x[i-1].
            // New SumXY = Old SumXY - (Sum of ALL old Ys) + (New Y * (n-1)) - (Old Y * 0)
            // Wait, let's verify math: 
            // SumXY_new = Sum(y_i * i) for i=0..n-1
            // The old y_1 (index 1) becomes y_0 (index 0).
            // So we subtract the entire sum_y from the old sum_xy.
            
            // Let's recompute purely for safety if O(n) is acceptable (period usually < 100)
            // For true HFT, we derive the O(1) update.
            // Let PrevSumXY = y0*0 + y1*1 + ... + yn*n
            // After shift:
            // NewSumXY = y1*0 + y2*1 + ... + new_y*(n-1)
            //          = (PrevSumXY - y0*0) - (y1+y2+...+yn) + new_y*(n-1)??? No.
            
            // Correct O(n) for safety in this snippet:
            self.sum_xy = 0.0;
            self.sum_y = 0.0;
            for (i, &p) in self.prices.iter().enumerate() {
                self.sum_y += p;
                self.sum_xy += p * (i as f64);
            }
        } else {
             // Startup phase
             let i = (self.prices.len() - 1) as f64;
             self.sum_y += price;
             self.sum_xy += price * i;
        }
        
        if self.prices.len() < self.period { return None; }
        
        let n = self.period as f64;
        let numerator = (n * self.sum_xy) - (self.sum_x * self.sum_y);
        
        Some(numerator / self.denominator)
    }
}
```

---

## 7. Strategy: "The Regr-Slope Divergence"

**Rules:**

1. **Uptrend:** Price makes a **Higher High**.
2. **Filter:** Linear Regression Slope makes a **Lower High**.
3. **Meaning:** The trend is continuing, but the *velocity* is slowing down. Momentum is waning.
4. **Signal:** Short the next red candle.

**Why it works:** It's a momentum exhaustion play. Parabolic moves $(Slope \to \infty)$ are unsustainable. When the slope flattens, gravity takes over.

---

## 8. Conclusion

Linear Regression Slope is the speedometer of the market.
It turns "I think it's going up fast" into "It is rising at \$5.30 per minute."
This quantification is the first step toward **Machine Learning**.

---

### Final Stats

* **Type:** Momentum / Trend
* **Input:** Price
* **Output:** Slope ($m$)
* **Best Market Condition:** Trending
* **Worst Market Condition:** Sideways (Slope oscillates around 0)
* **Complexity:** Medium (OLS)
