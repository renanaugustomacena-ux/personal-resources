# Indicator 147: R-Squared ($R^2$) — The Reliability Coefficient

***"Slope tells you how fast. R-Squared tells you how true. A steep slope with low R-Squared is a gamble. A moderate slope with high R-Squared is a retirement plan."***

---

## 1. Executive Summary

**R-Squared** (Coefficient of Determination) is a statistical measure that represents the proportion of the variance for a dependent variable that's explained by an independent variable. In trading, it measures the **reliability** of the trend.

It answers: **How closely does price fit a linear regression line?**

- **High $R^2$ (Near 1.0)**: Price is moving in a perfect straight line. The trend is stable, predictable, and low-volatility.
- **Low $R^2$ (Near 0.0)**: Price is random, choppy, or moving sideways. The "trend" (even if slope is high) is unreliable.

In GOLIATH, $R^2$ serves as the **Confidence Weight** for trend-following signals. A high slope with low $R^2$ is rejected as "noise." A moderate slope with high $R^2$ is accepted as "signal."

---

## 2. Mathematical Foundations

The calculation compares the fitted regression line to the mean.

$$ R^2 = 1 - \frac{\text{Sum Squared Residuals (SSR)}}{\text{Total Sum of Squares (SST)}} $$

$$ SSR = \sum (y_i - \hat{y}_i)^2 $$
$$ SST = \sum (y_i - \bar{y})^2 $$

Where:

- $y_i$: Actual Price
- $\hat{y}_i$: Predicted Price (on Regression Line)
- $\bar{y}$: Mean Price

Range: $0 \le R^2 \le 1$.

### 2.1 The Interpretation Thresholds

- **$R^2 > 0.8$**: Extremely strong trend.
- **$0.5 < R^2 < 0.8$**: Moderate trend.
- **$R^2 < 0.2$**: Noise / Sideways.

---

## 3. Signal Generation

### 3.1 The "Power Trend" Setup

- **Condition**: Linear Regression Slope is Positive (Bullish) OR Negative (Bearish).
- **Filter**: $R^2 > 0.90$.
- **Meaning**: The market is in a "Power Trend." Participation is uniform. Retracements are non-existent.
- **Strategy**: Switch to Momentum mode. Buy breakouts. Do not look for mean reversion (you will be crushed).

### 3.2 The Breaking Point (Reversal)

- **Setup**: Market has been in a high $R^2$ trend for > 20 bars.
- **Event**: $R^2$ drops below 0.80.
- **Meaning**: Volatility is entering the trend. The straight line is breaking. The trend is likely ending or entering a complex correction.
- **Action**: Tighten stops or take profit.

### 3.3 The Chande/Kroll R2 Filter

Tushar Chande suggested multiplying Slope by $R^2$ to get a "Risk-Adjusted Trend" metric:
$$ \text{Index} = \text{Slope} \times R^2 $$
This penalizes volatile trends.

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd
import numpy as np
from scipy.stats import linregress

def compute_r_squared(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Compute Rolling R-Squared of Close Price vs Time.
    """
    df = df.copy()
    
    # We need a rolling window correlation function.
    # R^2 = Correlation^2 (for simple linear regression)
    # Correlation between Price and Index (0, 1, 2...)
    
    # We can effectively compute rolling correlation between Close and a Time Index
    # But Time Index is just a monotonic series.
    
    # Create an index series
    idx = pd.Series(np.arange(len(df)), index=df.index)
    
    # Calculate rolling correlation
    rolling_corr = df['close'].rolling(window=period).corr(idx)
    
    # Square it
    df['r_squared'] = rolling_corr ** 2
    
    # While we are at it, Slope is useful too
    # Slope = Corr * (Std(Y) / Std(X))
    std_close = df['close'].rolling(window=period).std()
    std_idx = idx.rolling(window=period).std()
    
    df['slope'] = rolling_corr * (std_close / std_idx)
    
    return df
```

### 4.2 Rust Implementation

```rust
pub struct LinearRegression {
    period: usize,
    x_sum: f64,
    x_sq_sum: f64,
    y_buffer: VecDeque<f64>,
}

impl LinearRegression {
    pub fn new(period: usize) -> Self {
        let n = period as f64;
        let x_sum = (n - 1.0) * n / 2.0; // Sum of 0..N-1
        let x_sq_sum = (n - 1.0) * n * (2.0 * n - 1.0) / 6.0; // Sum of squares 0..N-1
        
        Self {
            period,
            x_sum,
            x_sq_sum,
            y_buffer: VecDeque::with_capacity(period),
        }
    }
    
    pub fn update(&mut self, y: f64) -> (f64, f64) { // Returns (Slope, R2)
        if self.y_buffer.len() == self.period {
            self.y_buffer.pop_front();
        }
        self.y_buffer.push_back(y);
        
        if self.y_buffer.len() < self.period {
            return (0.0, 0.0);
        }
        
        let n = self.period as f64;
        let y_sum: f64 = self.y_buffer.iter().sum();
        let xy_sum: f64 = self.y_buffer.iter().enumerate()
            .map(|(i, &val)| i as f64 * val)
            .sum();
        let y_sq_sum: f64 = self.y_buffer.iter().map(|&val| val * val).sum();
        
        // Slope (m) = (N*sum(xy) - sum(x)sum(y)) / (N*sum(x^2) - sum(x)^2)
        let numerator = n * xy_sum - self.x_sum * y_sum;
        let denominator = n * self.x_sq_sum - self.x_sum * self.x_sum;
        let slope = numerator / denominator;
        
        // Intercept (b) = (sum(y) - m*sum(x)) / N
        let intercept = (y_sum - slope * self.x_sum) / n;
        
        // R2 = 1 - SSE/SST
        // Or simpler: R = (n*sum(xy) - sum(x)sum(y)) / sqrt(...)
        let r_num = numerator;
        let r_den_x = denominator;
        let r_den_y = n * y_sq_sum - y_sum * y_sum;
        
        let r2 = if r_den_x > 0.0 && r_den_y > 0.0 {
            let r = r_num / (r_den_x * r_den_y).sqrt();
            r * r
        } else {
            0.0
        };
        
        (slope, r2)
    }
}
```

---

## 5. Strategy: The Sniper Entry

GOLIATH uses $R^2$ to decide **Market Structure Break Strategy**.

1. **Low $R^2$ (Chop)**: If $R^2 < 0.20$, volatility is mean-reverting. Treat breakouts as Fakes. Fade the highs.
2. **High $R^2$ (Trend)**: If $R^2 > 0.80$, volatility is directional. Treat pullbacks as Buying Opportunities.

This prevents the bot from "buying the top" in a chop zone or "shorting the breakout" in a trend zone.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 147 |
| Name | R-Squared (Trend Reliability) |
| Range | [0, 1] |
| Meaning | Goodness of Fit (Linearity) |
| Threshold | > 0.80 (Strong), < 0.20 (Chop) |
| GOLIATH Role | Signal Confidence Weighting |
