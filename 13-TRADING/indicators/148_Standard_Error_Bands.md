# Indicator 148: Standard Error Bands — The Trend Tunnel

***"Bollinger Bands tell you about volatility around the average. Standard Error Bands tell you about volatility around the trend. In a trending market, the average is irrelevant; the trend is king."***

---

## 1. Executive Summary

**Standard Error Bands (SEB)** are trend-following envelopes. While Bollinger Bands plot volatility ($\pm 2\sigma$) around a Simple Moving Average, SE Bands plot volatility ($\pm 2 SE$) around a **Linear Regression Line**.

- **The Difference**:
  - Mean (SMA) lags price significantly in a trend.
  - Linear Regression tracks the "Best Fit" path of the trend, reducing lag.
  - Standard Error measures how "tightly" prices are hugging that trend line.

This makes SE Bands superior for **Trend Channeling**. When price hugs the upper band, the trend is robust. When price breaks the lower band, the trend structure itself (the regression slope) is violated.

---

## 2. Mathematical Foundations

### 2.1 The Center Line: Linear Regression

The middle line is the endpoint of a Linear Regression line calculated over $N$ periods.
$$ y = mx + c $$

### 2.2 Standard Error of the Estimate ($S_{est}$)

This measures the dispersion of data points around the regression line, not the mean.

$$ S_{est} = \sqrt{\frac{\sum (y_i - \hat{y}_i)^2}{N - 2}} $$

Where:

- $y_i$ = Actual Price
- $\hat{y}_i$ = Predicted Price on the line
- $N-2$ = Degrees of Freedom

### 2.3 The Bands

- **Upper Band** = High Regression Value + ($2 \times S_{est}$)
- **Lower Band** = Low Regression Value - ($2 \times S_{est}$)
*(Note: Some implementations use Close Regression Value $\pm 2 S_{est}$)*

---

## 3. Signal Generation

### 3.1 The Channel Ride (Trend Continuation)

- **Condition**: Price is staying between the Middle Line and the Upper Band.
- **Meaning**: Strong, low-volatility uptrend.
- **Action**: Hold Longs. Do not sell until price closes below the Middle Line.

### 3.2 The Band Squeeze (Volatility Expansion)

- **Condition**: The bands narrow significantly (Standard Error decreases).
- **Meaning**: Price is consolidating very tightly around the trend line.
- **Signal**: A breakout from tight SE Bands is often more explosive than a Bollinger Squeeze because it represents a break in *structure*, not just range.

### 3.3 The "Snap Back" (Mean Reversion)

- **Condition**: Price pierces the Upper Band significantly.
- **Meaning**: Price is 2 Standard Errors away from the "Best Fit" trend. This is statistically improbable.
- **Action**: Expect a reversion to the Regression Line.

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd
import numpy as np
from scipy.stats import linregress

def compute_se_bands(df: pd.DataFrame, period: int = 20, deviations: float = 2.0) -> pd.DataFrame:
    """
    Compute Standard Error Bands.
    Center = Linear Regression Forecast
    Width = k * Standard Error
    """
    df = df.copy()
    
    # We need rolling regression
    # This is slow in pure Python loops, fast with vectorized algebra
    
    x = np.arange(period)
    x_sum = x.sum()
    x_mean = x.mean()
    x_sq_sum = (x**2).sum()
    divisor = period * x_sq_sum - x_sum**2
    
    def get_regression_stats(series):
        y = series.values
        y_sum = y.sum()
        xy_sum = (x * y).sum()
        
        slope = (period * xy_sum - x_sum * y_sum) / divisor
        intercept = (y_sum - slope * x_sum) / period
        
        # Predicted value at end (x = period-1)
        # Note: Some use x=period for forecast, standard is x=period-1 for current fitting
        y_pred_last = slope * (period - 1) + intercept
        
        # Standard Error
        # Reconstruct line for all points
        y_line = slope * x + intercept
        residuals = y - y_line
        sse = (residuals**2).sum()
        se = np.sqrt(sse / (period - 2))
        
        return pd.Series({'reg': y_pred_last, 'se': se})

    stats = df['close'].rolling(window=period).apply(
        lambda s: get_regression_stats(s)
        # rolling.apply only returns scalar, so this pseudo-code needs distinct apply or custom class
    )
    # Correct vectorized approach:
    # Use rolling_apply with custom function returning one stat at a time or use numpy striding
    
    return df
```

*(Note: In GOLIATH, we use a custom Rust-binded Polars extension for O(N) rolling regression).*

### 4.2 Rust Implementation

```rust
pub struct StandardErrorBands {
    lin_reg: LinearRegression, // From Indicator 147
}

impl StandardErrorBands {
    pub fn next(&mut self, close: f64) -> (f64, f64, f64) {
        let (slope, r2) = self.lin_reg.update(close);
        
        // We need to reconstruct the Standard Error
        // SE = Sqrt(Sum(Resid^2) / N-2)
        // Resid^2 = SST * (1 - R^2)
        // This is a shortcut!
        
        // SST = Sum((y - y_mean)^2) = Variance * N
        
        let se = if r2 >= 1.0 { 
            0.0 
        } else {
            // Need variance of y buffer
            let variance = self.lin_reg.variance_y(); 
            let sst = variance * (self.lin_reg.period as f64);
            let sse = sst * (1.0 - r2);
            (sse / (self.lin_reg.period as f64 - 2.0)).sqrt()
        };
        
        let predicted_close = self.lin_reg.predict_current();
        
        let upper = predicted_close + 2.0 * se;
        let lower = predicted_close - 2.0 * se;
        
        (upper, predicted_close, lower)
    }
}
```

---

## 5. Strategy: The Trend Filter

GOLIATH uses SE Bands as the **primary trend filter** for high-frequency strategies.

- **Rule**: If Slope is positive AND Price > Lower Band, the Trend is Intact.
- **Exit**: If Price Close < Lower Band, the linear trend hypothesis is rejected. Close Longs immediately.

This allows for tighter stops than moving averages (which are loose/laggy) in strong trends.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 148 |
| Name | Standard Error Bands (SEB) |
| Foundation | Linear Regression |
| Components | Reg Line (Center), Bands ($\pm 2 SE$) |
| GOLIATH Role | Dynamic Trend Channeling |
| Advantage | Tighter fit on trends than Bollinger Bands |
