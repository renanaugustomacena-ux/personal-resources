# Indicator 149: Historical Volatility Percentile (HVP) — The Gamma Gauge

***"Volatility is the only asset class that is predictably mean-reverting. Low volatility breeds high volatility, and high volatility breeds low volatility. The HVP tells you where you are in the breathing cycle."***

---

## 1. Executive Summary

**Historical Volatility Percentile (HVP)** puts current volatility into context. Knowing that current volatility is "15%" is meaningless unless you know if 15% is high or low for *this specific asset*.

HVP answers: **"How often in the past year was volatility lower than it is right now?"**

- **HVP < 20 (Cheap Volatility)**: The market is unnaturally quiet. A breakout is statistically probable. Good time to Buy Options (Long Gamma).
- **HVP > 80 (Expensive Volatility)**: The market is in panic mode. A calm-down is statistically probable. Good time to Sell Options (Short Gamma) or fade moves.

In GOLIATH, HVP controls the **Strategy Selection**:

- High HVP $\to$ Deploy Mean Reversion (Grid/Fade).
- Low HVP $\to$ Deploy Breakout/Trend Following.

---

## 2. Mathematical Foundations

### 2.1 Historical Volatility (HV)

First, calculate the annualized standard deviation of log returns.
$$ R_t = \ln(\frac{P_t}{P_{t-1}}) $$
$$ HV = \text{StdDev}(R, N) \times \sqrt{252 \text{ or } 365} $$

### 2.2 Percentile Rank

Compare the current HV to the distribution of HV over a lookback window (e.g., 252 days).

$$ \text{HVP} = \frac{\text{Count of Days where } HV_{past} < HV_{current}}{\text{Total Lookback Days}} \times 100 $$

---

## 3. Signal Generation

### 3.1 The Compression Breakout (Squeeze)

- **Condition**: HVP drops below 10 (Bottom decile).
- **Meaning**: The spring is coiled tight.
- **Action**: Switch to "Breakout Mode." Place Buy Stop/Sell Stop orders outside the recent range. Do not sell premium.

### 3.2 The Mean Reversion Short

- **Condition**: HVP spikes above 90 (Top decile).
- **Meaning**: Fear is at a maximum.
- **Action**: Look for reversals. Fade extreme moves. Volatility is likely to crush (Vanna/Volga effect), helping short positions.

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore

def compute_hvp(df: pd.DataFrame, vol_window: int = 21, rank_window: int = 252) -> pd.DataFrame:
    """
    Compute Historical Volatility Percentile.
    """
    df = df.copy()
    
    # 1. Log Returns
    df['log_ret'] = np.log(df['close'] / df['close'].shift(1))
    
    # 2. Historical Volatility (Annualized)
    # Crypto: sqrt(365), TradFi: sqrt(252)
    df['hv'] = df['log_ret'].rolling(window=vol_window).std() * np.sqrt(365)
    
    # 3. Percentile Rank
    # Rolling percentile calculation is slow in pure pandas loop.
    # Approach: Use rolling_apply.
    
    def get_rank(series):
        current = series.iloc[-1]
        past = series.iloc[:-1] # Compare to past distribution
        return percentileofscore(past, current)
        
    df['hvp'] = df['hv'].rolling(window=rank_window).apply(get_rank, raw=False)
    
    return df
```

### 4.2 Rust Implementation

```rust
pub struct HvpCalculator {
    log_returns: VecDeque<f64>,
    hv_history: VecDeque<f64>,
    vol_window: usize,
    rank_window: usize,
}

impl HvpCalculator {
    pub fn next(&mut self, price: f64) -> (f64, f64) {
        // ... (Log Return Calculation) ...
        
        // ... (HV Calculation) ...
        
        // Calculate Rank
        // Naive O(N) sort or O(N) scan.
        // For window=252, simple scan is fast enough.
        
        let count_lower = self.hv_history.iter()
            .filter(|&&v| v < current_hv)
            .count();
            
        let rank = (count_lower as f64 / self.hv_history.len() as f64) * 100.0;
        
        (current_hv, rank)
    }
}
```

---

## 5. Strategy: The Iron Condor logic

Even for directional trading, HVP dictates `Stop Loss` width.

- **Low HVP**: Tight Stops. (Market shouldn't move much against you if you are right).
- **High HVP**: Wide Stops. (Noise is high; give the trade room to breathe).

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 149 |
| Name | Historical Volatility Percentile (HVP) |
| Range | 0 - 100 |
| Type | Regime Filter (Vol of Vol) |
| GOLIATH Role | Strategy Switching (Mean Rev vs Trend) |
