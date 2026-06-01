# Indicator 150: Sortino Ratio (Dynamic) — The Quality Control

***"Sharpe Ratio punishes you for winning too fast. Sortino Ratio only punishes you for losing. In trading, upside volatility is not risk; it's opportunity."***

---

## 1. Executive Summary

The **Sortino Ratio** is an improvement on the Sharpe Ratio that differentiates between "Bad Volatility" and "Good Volatility."

- **Sharpe Ratio**: Uses Standard Deviation (total volatility) in the denominator. A massive spike UP increases volatility, lowering the Sharpe Ratio. This is counter-intuitive.
- **Sortino Ratio**: Uses **Downside Deviation** (volatility of negative returns only) in the denominator. A massive spike UP does not increase risk; it increases the numerator (Return) without penalizing the denominator.

**Dynamic Sortino**: In GOLIATH, we compute this on a **Rolling Window** (e.g., 30 days) to track the evolving quality of the strategy or asset.

- **Rising Sortino**: The asset is trending up with minimal harmful drawdowns. (High Conviction).
- **Falling Sortino**: The asset is either losing money OR becoming erratic on the downside. (Low Conviction).

---

## 2. Mathematical Foundations

### 2.1 Formula

$$ \text{Sortino} = \frac{R_p - R_f}{\text{DR}} $$

Where:

- $R_p$: Portfolio/Asset Return (Average over period).
- $R_f$: Risk-Free Rate (Target Return, often set to 0 for trading).
- $\text{DR}$: Downside Risk (Target Semi-Deviation).

### 2.2 Downside Deviation Calculation

1. Calculate returns for each period ($r_i$).
2. Define Target Return ($T$), usually 0.
3. Identify only the returns that fell below $T$.
    $$ \text{Diff}_i = \min(0, r_i - T) $$
4. Square the differences.
    $$ \text{Diff}_i^2 $$
5. Average them and take the square root.
    $$ \text{DR} = \sqrt{\frac{1}{N} \sum (\text{Diff}_i^2)} $$

---

## 3. Signal Generation

### 3.1 The "Smart Money" Filter

Smart Money enters trends that have high Sortino Ratios (smooth persistence) and exits when the Sortino Ratio begins to degrade (choppiness appears).

- **Entry**: Rolling 30-Day Sortino > 2.0.
- **Exit**: Rolling 30-Day Sortino drops below 1.0.

### 3.2 Portfolio Optimization (GOLIATH)

The GOLIATH "Meta-Model" reallocates capital between sub-strategies based on their rolling Sortino Ratios.

- Strategy A (Aggressive): Return 20%, Max DD 15%.
- Strategy B (Conservative): Return 10%, Max DD 2%.

Sharpe might favor A. Sortino will heavily favor B (due to tiny downside deviation). GOLIATH allocates more to B to stabilize the equity curve.

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd
import numpy as np

def compute_rolling_sortino(df: pd.DataFrame, window: int = 30, target_return: float = 0.0) -> pd.DataFrame:
    """
    Compute Rolling Sortino Ratio.
    """
    df = df.copy()
    
    # 1. Returns
    df['ret'] = df['close'].pct_change()
    
    # 2. Downside Deviation Routine
    def get_sortino(series):
        # Average Return
        avg_ret = series.mean()
        
        # Downside Diff
        downside = series - target_return
        downside[downside > 0] = 0 # Ignore positive returns
        
        # Square
        downside_sq = downside ** 2
        
        # Mean
        downside_dev = np.sqrt(downside_sq.mean())
        
        if downside_dev == 0:
            return np.nan # Undefined (Infinite)
            
        # Annualize (assuming daily data)
        # Ratio = (Avg Daily Ret * 365) / (Daily Downside Dev * sqrt(365))
        # Simplification: Ratio * sqrt(365)
        
        return (avg_ret - target_return) / downside_dev * np.sqrt(365)
        
    df['sortino'] = df['ret'].rolling(window=window).apply(get_sortino, raw=False)
    
    return df
```

### 4.2 Rust Implementation

```rust
pub struct SortinoCalculator {
    returns: VecDeque<f64>,
    window: usize,
    target: f64,
}

impl SortinoCalculator {
    pub fn next(&mut self, ret: f64) -> f64 {
        if self.returns.len() == self.window {
            self.returns.pop_front();
        }
        self.returns.push_back(ret);
        
        // Compute Mean
        let sum_ret: f64 = self.returns.iter().sum();
        let avg_ret = sum_ret / self.window as f64;
        
        // Compute Downside Deviation
        let sum_sq_downside: f64 = self.returns.iter()
            .map(|&r| {
                let diff = if r < self.target { r - self.target } else { 0.0 };
                diff * diff
            })
            .sum();
            
        let downside_dev = (sum_sq_downside / self.window as f64).sqrt();
        
        if downside_dev < 1e-9 {
            return 0.0; 
        }
        
        (avg_ret - self.target) / downside_dev
    }
}
```

---

## 5. Conclusion: The 150th Indicator

The **Sortino Ratio** is fittingly the final indicator in this encyclopedia (Phase 16). While indicators 1-149 focus on **predicting price**, Indicator 150 focuses on **protecting capital**.

Ultimately, a trader's longevity is not determined by how much they make when they are right (Alpha), but by how little they lose when they are wrong (Sortino). It is the ultimate **Convexity Filter**.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 150 |
| Name | Sortino Ratio (Dynamic) |
| Author | Frank Sortino |
| Formula | (R - T) / DownsideDev |
| Advantage | Ignores Upside Volatility |
| GOLIATH Role | Quality & Allocation Metric |
| Key Threshold | > 2.0 (High Quality) |
