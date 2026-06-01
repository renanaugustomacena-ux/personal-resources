# Indicator 143: Open Interest (OI) — The Commitment Gauge

***"Volume tells you how much money changed hands. Open Interest tells you how much money is stuck in the trade. New money fuels trends; old money fuels reversals."***

---

## 1. Executive Summary

**Open Interest (OI)** is the total number of outstanding derivative contracts (futures or options) that have not been settled.

Unlike Volume (which accumulates with every trade), OI only changes when a new position is created or destroyed.

- **OI Increases**: New money is entering the market (Aggressive). Both buyer and seller are opening new positions.
- **OI Decreases**: Money is leaving the market (Liquidation/Covering). Buyer and seller are closing existing positions.
- **OI Flat**: Money is just changing hands (churn). One trader exits, another enters.

For GOLIATH, OI is the **Trend Fuel Gauge**. A trend cannot be sustained without increasing Open Interest. If Price is rising but OI is falling, the rally is a "Short Squeeze" — completely hollow and prone to rapid reversal once the shorts are finished covering.

---

## 2. Mathematical Foundations

$$ \text{OI}_t = \text{OI}_{t-1} + (\text{New Positions} - \text{Closed Positions}) $$

Interpretation Matrix:

| Price Action | OI Action | Market State | Interpretation |
|---|---|---|---|
| **Rising** | **Rising** | **Bullish** | New Buyers are aggressive. Trend is strong. |
| **Rising** | **Falling** | **Weak Bullish** | Short Covering. Buyers are not stepping up; Sellers are just fleeing. |
| **Falling** | **Rising** | **Bearish** | New Sellers are aggressive. Trend is strong side. |
| **Falling** | **Falling** | **Weak Bearish** | Long Liquidation (Puking). Selling is forced, not aggressive. |

---

## 3. Signal Generation

### 3.1 The Squeeze Setup

- **Long Squeeze**: Identify a massive buildup of OI while Price is drifting down or flat. Then, a sharp drop in Price coupled with a sharp *drop* in OI.
  - *Logic*: The high OI represented "late longs." The price drop forced them to sell (liquidated). The drop in OI confirms they are gone.
  - *Trade*: Buy the reclamation of the breakdown level. The sellers are exhausted.

### 3.2 Trend Confirmation

- **Breakout**: Price breaks a key resistance.
- **Validation**: OI must spike **significantly** (e.g., +5% in 1 hour) along with the price break.
- *Rule*: "No OI, No Trade." A breakout with flat OI is a fakeout.

### 3.3 The "OI Nuke"

In crypto, leverage is high.

- **Signal**: Price drops 5%, OI drops 20%.
- **Meaning**: Mass liquidation event. The "leverage flush" is complete.
- **Action**: This marks a high-probability V-bottom. GOLIATH switches from Trend Following to Mean Reversion immediately.

---

## 4. Implementation

### 4.1 Python Implementation (Requires Exchange Data)

Most exchanges provide an endpoint for `openInterest`. It is rarely part of the standard OHLCV stream and must be fetched separately.

```python
import pandas as pd

def analyze_oi_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze Open Interest relative to Price action.
    Requires 'close' and 'open_interest' columns.
    """
    df = df.copy()
    
    df['price_chg'] = df['close'].diff()
    df['oi_chg'] = df['open_interest'].diff()
    
    conditions = [
        (df['price_chg'] > 0) & (df['oi_chg'] > 0), # Long Build
        (df['price_chg'] > 0) & (df['oi_chg'] < 0), # Short Cover
        (df['price_chg'] < 0) & (df['oi_chg'] > 0), # Short Build
        (df['price_chg'] < 0) & (df['oi_chg'] < 0)  # Long Liq
    ]
    
    choices = ['STRONG_BULL', 'WEAK_BULL', 'STRONG_BEAR', 'WEAK_BEAR']
    
    df['oi_regime'] = np.select(conditions, choices, default='NEUTRAL')
    
    # Calculate OI RSI (Momentum of OI)
    # Applying RSI formula to OI stream to detect "Overcrowded" trades
    delta = df['oi_chg']
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['oi_rsi'] = 100 - (100 / (1 + rs))
    
    return df
```

### 4.2 Rust Implementation

```rust
pub enum OiRegime {
    LongBuild,
    ShortCover,
    ShortBuild,
    LongLiquidate,
    Neutral,
}

pub struct OiAnalyzer {
    prev_price: f64,
    prev_oi: f64,
}

impl OiAnalyzer {
    pub fn next(&mut self, price: f64, oi: f64) -> OiRegime {
        let price_up = price > self.prev_price;
        let oi_up = oi > self.prev_oi;
        
        // Simple logic for streaming
        let regime = match (price_up, oi_up) {
            (true, true) => OiRegime::LongBuild,
            (true, false) => OiRegime::ShortCover,
            (false, true) => OiRegime::ShortBuild,
            (false, false) => OiRegime::LongLiquidate,
        };
        
        self.prev_price = price;
        self.prev_oi = oi;
        
        regime
    }
}
```

---

## 5. Strategy: The High-OI Breakout

GOLIATH scans for **Consolidation with Rising OI**.

1. Price is range-bound (Bollinger Bands tight).
2. OI is steadily climbing (Divergence).
3. *Interpretation*: Participants are loading up big positions (both Longs and Shorts) in anticipation of a move. One side is about to get trapped.
4. *Trigger*: When Price breaks the range, the side that is wrong will be forced to puke (liquidate), adding fuel to the breakout.
5. *Execution*: Enter in direction of Price Breakout. Target the stop-loss clusters of the trapped side.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 143 |
| Name | Open Interest (OI) |
| Data Source | Futures/Options Exchange Feed |
| Type | Volume/Market Structure |
| Signal | Convergence/Divergence with Price |
| KPI | OI Change % |
| GOLIATH Role | Trend Validation (Fuel Gauge) |
