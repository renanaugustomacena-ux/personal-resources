# Indicator 144: Delta Divergence — The Truth Serum

***"Price lies. Volume lies. But Delta tells you who is actually hitting the button. When Price says 'Up' but Delta says 'No Buyers', listen to the Delta."***

---

## 1. Executive Summary

**Delta Divergence** is an order flow concept that identifies discrepancies between **Price Direction** and **Aggressor Sentiment** (Net Buying/Selling).

- **Normal Behavior**: Price moves up $\to$ Buying Delta is positive. Price moves down $\to$ Selling Delta is negative.
- **Divergence (Abnormal)**: Price moves up $\to$ Delta is negative (or flat). This is a warning.

How can Price go up if Aggr. Buying is negative?
Possible reasons:

1. **Limit Order Pulling**: Sellers pulled their limit orders (spoofing), allowing a small amount of buying to push price up easily (Liquidity Vacuum).
2. **Iceberg Absorption**: Price drop arrested by a massive limit buyer. Aggressive selling continues, but price stops falling.

In GOLIATH, Delta Divergence is the primary signal for **Reversal Trading**. It signals that the current trend is unsupported by aggressive flow and is being manipulated or exhausted.

---

## 2. Mathematical Foundations

We compare the slope/extrema of Price vs. CVD (Cumulative Volume Delta).

Let $P_t$ be the Price High/Low at pivot $t$.
Let $D_t$ be the CVD value at the same time $t$.

### 2.1 Regular Bearish Divergence (Reversal)

- Price makes a **Higher High** ($P_{new} > P_{old}$).
- CVD makes a **Lower High** ($D_{new} < D_{old}$).
- *Meaning*: Buyers pushed price to a new high, but with *less* aggressive volume than before. The breakout is weak.

### 2.2 Regular Bullish Divergence (Reversal)

- Price makes a **Lower Low**.
- CVD makes a **Higher Low**.
- *Meaning*: Sellers pushed price to a new low, but with less aggressive volume. Selling dries up.

### 2.3 Hidden Divergence (Continuation)

- **Bullish Hidden**: Price makes Higher Low, CVD makes Lower Low. (Deep value buying).
- **Bearish Hidden**: Price makes Lower High, CVD makes Higher High.

---

## 3. Signal Generation

### 3.1 The "Trapped Traders" Setup

This is a specific divergence pattern.

1. **Context**: Downtrend.
2. **Event**: A sudden spike in Selling Delta (CVD drops vertically).
3. **Result**: Price Candle is a **Doji** or **Hammer**. It refuses to go down despite the delta spike.
4. **Signal**: The sellers are trapped. They sold the bottom.
5. **Trigger**: Buy when price breaks the high of the "Trapped Candle."

### 3.2 The "Effort vs Result" Anomaly

Using Wyckoffian logic with Delta.

- **High Effort, No Result**: Big Delta bar, Small Price bar. (Absorption).
- **Low Effort, Big Result**: Small Delta bar, Big Price bar. (Liquidity Vacuum / Thin Orderbook).

GOLIATH prioritizes "**High Effort, No Result**" as a reversal signal at Key Levels (Support/Resistance).

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd
import numpy as np

def detect_delta_divergence(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Detect divergences between Price Highs/Lows and Delta Highs/Lows.
    Requires 'close', 'high', 'low', 'delta' (per bar) or 'cvd'.
    """
    # Assuming 'cvd' is precomputed
    price_highs = df['high'].rolling(window=window, center=True).max()
    cvd_highs = df['cvd'].rolling(window=window, center=True).max()
    
    # Identify Peaks
    is_price_peak = df['high'] == price_highs
    is_cvd_peak = df['cvd'] == cvd_highs
    
    # This requires stateful logic to compare the *current* peak to the *previous* peak.
    # Vectorized approach:
    # 1. Extract peaks indices
    # 2. Sequential comparison
    
    # Simplified Logic: Deviation from Linear Regression
    # If Price Slope > 0 and CVD Slope < 0 over last N bars -> Divergence.
    
    from scipy.stats import linregress
    
    def get_slope(series):
        if len(series) < 5: return 0
        slope, _, _, _, _ = linregress(range(len(series)), series)
        return slope
        
    df['price_slope'] = df['close'].rolling(10).apply(get_slope, raw=True)
    df['cvd_slope'] = df['cvd'].rolling(10).apply(get_slope, raw=True)
    
    df['div_signal'] = 0
    # Bearish Div: Price Up, CVD Down
    mask_bear = (df['price_slope'] > 0.5) & (df['cvd_slope'] < -0.5)
    df.loc[mask_bear, 'div_signal'] = -1
    
    # Bullish Div: Price Down, CVD Up
    mask_bull = (df['price_slope'] < -0.5) & (df['cvd_slope'] > 0.5)
    df.loc[mask_bull, 'div_signal'] = 1
    
    return df
```

### 4.2 Rust Implementation

```rust
#[derive(Debug, Clone, Copy)]
pub enum DivergenceType {
    BullishRegular,
    BearishRegular,
    None,
}

pub struct DeltaDivergenceDetector {
    last_price_peak: f64,
    last_cvd_peak_at_price_peak: f64,
    last_price_valley: f64,
    last_cvd_valley_at_price_valley: f64,
}

// Complex peak detection logic usually requires a Pivot Point algorithm
// (e.g., Williams Fractal or ZigZag).
// Here we assume external Pivot Detection feeds this struct.

impl DeltaDivergenceDetector {
    pub fn new() -> Self {
        Self {
            last_price_peak: f64::MIN,
            last_cvd_peak_at_price_peak: f64::MIN,
            last_price_valley: f64::MAX,
            last_cvd_valley_at_price_valley: f64::MAX,
        }
    }
    
    pub fn on_new_high(&mut self, price: f64, cvd: f64) -> DivergenceType {
        if price > self.last_price_peak {
            // New High Price
            if cvd < self.last_cvd_peak_at_price_peak {
                // ...but Lower High CVD
                return DivergenceType::BearishRegular;
            }
            // Update reference
            self.last_price_peak = price;
            self.last_cvd_peak_at_price_peak = cvd;
        }
        DivergenceType::None
    }
}
```

---

## 5. Strategy: The Passive Wall Defense

GOLIATH deploys this strategy at **Daily Support Levels**.

1. **Level**: Price hits a known support (e.g., $2000 for Gold).
2. **Order Flow**: Aggressive selling spikes (Red Delta bars).
3. **Divergence**: Price prints a "Double Bottom" on the 5-min chart, but CVD prints a "Higher Low" (sellers exhausted) OR CVD keeps tanking but Price holds (Absorption).
4. **Confirm**: Wait for the first Green Candle to close above the absorption zone.
5. **Stop**: Minimal risk, just below the absorption wick.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 144 |
| Name | Delta Divergence |
| Requirement | CVD (Tick Data) |
| Signal | Discrepancy between Price/Delta Slopes |
| Type | Reversal / Exhaustion |
| GOLIATH Role | "Truth Serum" for Trends |
| Key Logic | Absorption (Limit > Market) vs Exhaustion (No Market) |
