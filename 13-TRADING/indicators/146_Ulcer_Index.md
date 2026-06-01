# Indicator 146: Ulcer Index — Measuring the Pain

***"Standard Deviation treats upside volatility as equal to downside volatility. But traders don't lose sleep over upside volatility. They lose sleep over drawdowns. The Ulcer Index measures the sleepless nights."***

---

## 1. Executive Summary

The **Ulcer Index (UI)**, developed by Peter Martin in 1987, is a risk metric designed to quantify the **depth and duration** of price drawdowns. Unlike Standard Deviation (which penalizes all volatility equally), the Ulcer Index *only* penalizes downside moves.

It answers the question: **How stressful is this asset to hold?**

- **High UI**: The asset suffers from deep, long-lasting drawdowns. (High stress).
- **Low UI**: The asset either trends up smoothly or recovers quickly from dips. (Low stress).

In GOLIATH, the Ulcer Index is used as a **Dynamic Position Sizing** filter. If the 14-period UI of an asset spikes, the system reduces leverage, regardless of the trend direction. It assumes that "shaky" trends are prone to collapse.

---

## 2. Mathematical Foundations

The calculation focuses on the **Percentage Drawdown** from the highest high over a lookback period.

### 2.1 Formula

1. **Calculate Percentage Drawdown ($R_i$)** for each period:
    $$ R_i = 100 \times \frac{\text{Close}_i - \text{MaxHigh}_N}{\text{MaxHigh}_N} $$
    Where $\text{MaxHigh}_N$ is the highest close in the last $N$ periods (usually 14).
    Note: $R_i$ is always $\le 0$.

2. **Square the Drawdowns**:
    $$ R_i^2 $$
    Squaring penalizes large drawdowns disproportionately more than small ones.

3. **Average the Squared Drawdowns**:
    $$ \text{Mean Squared} = \frac{1}{N} \sum_{i=1}^{N} R_i^2 $$

4. **Take the Square Root**:
    $$ \text{UI} = \sqrt{\text{Mean Squared}} $$

Technically, it is the **Root Mean Square (RMS)** of the drawdowns.

---

## 3. Signal Generation

### 3.1 The Stress Breakout (Bearish)

- **Condition**: UI crosses above its moving average or a specific threshold (e.g., 5.0).
- **Meaning**: The "smoothness" of the uptrend is breaking. Drawdowns are getting deeper or lasting longer.
- **Action**: Tighten stops or reduce position size.

### 3.2 The Recovery (Bullish)

- **Condition**: Price is making new highs, but UI is flatlining near zero.
- **Meaning**: A "Low Stress" rally.
- **Action**: Safe to increase leverage.

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd
import numpy as np

def compute_ulcer_index(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Compute Peter Martin's Ulcer Index.
    """
    df = df.copy()
    
    # Calculate Rolling Max Close
    rolling_max = df['close'].rolling(window=period).max()
    
    # Calculate Percentage Drawdown
    drawdown = 100 * (df['close'] - rolling_max) / rolling_max
    
    # Squared Drawdowns
    sq_drawdown = drawdown ** 2
    
    # Mean of Squared Drawdowns
    mean_sq = sq_drawdown.rolling(window=period).mean()
    
    # Square Root
    df['ulcer_index'] = np.sqrt(mean_sq)
    
    return df
```

### 4.2 Rust Implementation

```rust
pub struct UlcerIndex {
    period: usize,
    history: VecDeque<f64>, // Stores Closing Prices
}

impl UlcerIndex {
    pub fn new(period: usize) -> Self {
        Self {
            period,
            history: VecDeque::with_capacity(period),
        }
    }

    pub fn next(&mut self, close: f64) -> f64 {
        if self.history.len() == self.period {
            self.history.pop_front();
        }
        self.history.push_back(close);
        
        let max_close = self.history.iter().fold(f64::MIN, |a, &b| a.max(b));
        
        // Compute RMS of drawdowns
        let sum_sq_dd: f64 = self.history.iter()
            .map(|&c| {
                let dd = 100.0 * (c - max_close) / max_close;
                dd * dd
            })
            .sum();
            
        (sum_sq_dd / self.period as f64).sqrt()
    }
}
```

---

## 5. Strategy: The Martin Ratio

Just as the Sharpe Ratio uses Standard Deviation, the **Martin Ratio** uses the Ulcer Index.

$$ \text{Martin Ratio} = \frac{\text{CAGR} - \text{Risk Free Rate}}{\text{Ulcer Index}} $$

**Strategy**:

- Rank all assets in the portfolio by Martin Ratio.
- Allocate capital only to the top decile.
- This ensures you are buying assets that provide returns with the **least amount of pain**.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 146 |
| Name | Ulcer Index (UI) |
| Author | Peter Martin |
| Formula | RMS of Percentage Drawdowns |
| Type | Risk / Volatility |
| GOLIATH Role | Dynamic Leverage Throttling |
| Key Metric | Martin Ratio (Return / UI) |
