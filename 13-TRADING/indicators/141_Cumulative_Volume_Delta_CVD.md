# Indicator 141: Cumulative Volume Delta (CVD) — The Aggressor's Footprint

***"Price is an advertisement. Volume is the commitment. Delta is the verdict. Who is more desperate: the buyers lifting the offer, or the sellers hitting the bid?"***

---

## 1. Executive Summary

**Cumulative Volume Delta (CVD)** is the foundational metric of **Order Flow Analysis**. Unlike standard volume (which is scalar/unsigned), CVD splits volume into **Buy Volume** (aggressor buying at Ask) and **Sell Volume** (aggressor selling at Bid).

The "Delta" is the difference: $Delta = Volume_{Ask} - Volume_{Bid}$.
The "Cumulative" part tracks this net difference over time, creating a chart that runs parallel to price.

CVD reveals the **Intent** behind the price move.

- **Confirmation**: Price makes a new High, CVD makes a new High. (Healthy Trend).
- **Absorption (Divergence)**: Price makes a new High, but CVD fails to make a new High (or drops). This implies that despite aggressive buying, passive sellers (Limit Orders) are absorbing all the demand. A reversal is imminent.
- **Exhaustion**: Price stays flat, but CVD rockets up. Aggressive buyers are pouring in but cannot move price (Iceberg Orders).

In GOLIATH, CVD is the **Primary Manipulation Detector**. It identifies when Smart Money is passively absorbing retail aggression.

---

## 2. Mathematical Foundations

The calculation requires **Tick Data** (Time and Sales) with trade direction classification.

### 2.1 Trade Classification (The Aggressor Rule)

Every trade involves a buyer and a seller. To classify a trade as a "Buy" or "Sell", we look at who **crossed the spread** (the aggressor/taker).

- **Buy Volume (+)**: Trade occurred at the **Ask** price (or higher). The buyer demanded immediate liquidity.
- **Sell Volume (-)**: Trade occurred at the **Bid** price (or lower). The seller dumped immediate liquidity.

### 2.2 The Formula

For a given bar $i$:
$$ \text{Delta}_i = \sum_{t \in \text{Bar}_i} (\text{Vol}_t \times \text{Sign}_t) $$
Where $\text{Sign}_t = +1$ if trade was at Ask, $-1$ if at Bid.

$$ \text{CVD}_i = \text{CVD}_{i-1} + \text{Delta}_i $$

The CVD line is a running total. The absolute value is irrelevant; only the **Slope** and **Divergence** relative to price matter.

---

## 3. Signal Generation

### 3.1 Absorption (The "Limit Wall")

This is the most powerful signal in crypto/futures.

- **Bearish Absorption**: Price pushes into Resistance. CVD spikes massively green (aggressive buying). Price *ticks down* or stays flat.
- **Interpretation**: A large player has placed a massive Sell Limit Wall (Iceberg). Retail users are market-buying into it, but the wall isn't moving. Once the buyers are exhausted, price will collapse.

### 3.2 Exhaustion (The "Liquidity Vacuum")

- **Bullish Exhaustion**: Price makes a new High, but CVD makes a *Lower High*.
- **Interpretation**: The new high was achieved with *less* buying effort than the previous high. The buyers are running out of ammo. The move is hollow.

### 3.3 The Puke (Stop Run)

- **Setup**: Price drops sharply. CVD drops sharply.
- **Trigger**: Suddenly, CVD flattens out while Price continues to drop another leg.
- **Interpretation**: The aggressive selling has stopped, but price is drifting lower due to lack of bids (liquidity vacuum) rather than selling pressure. This is often the exact bottom.

---

## 4. Implementation

### 4.1 Python Implementation (Requires Tick/Trade Data)

Standard OHLCV data is insufficient. You need a data source that provides `buy_volume` and `sell_volume` explicitly (e.g., Binance API `taker_buy_base_asset_volume`).

```python
import pandas as pd
import numpy as np

def compute_cvd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Cumulative Volume Delta (CVD).
    
    Parameters
    ----------
    df : pd.DataFrame
        Must look like standard K-line data but needs:
        'volume': Total Volume
        'taker_buy_volume': Volume acting as aggressor buyer
        
    Returns
    -------
    pd.DataFrame with 'delta' and 'cvd' columns.
    """
    df = df.copy()
    
    # Calculate Sell Volume (Aggressor Sell)
    # Total = Buy (Taker) + Sell (Taker)
    # Sell = Total - Buy
    taker_buy = df['taker_buy_volume']
    total_vol = df['volume']
    taker_sell = total_vol - taker_buy
    
    # Calculate Net Delta per bar
    df['delta'] = taker_buy - taker_sell
    
    # Calculate Cumulative Delta
    # We typically reset CVD at some point (e.g., daily) or let it run.
    # Here we perform a full cumulative sum.
    df['cvd'] = df['delta'].cumsum()
    
    return df

def detect_absorption(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Detect Absorption: Price High vs CVD High divergence.
    """
    price = df['close']
    cvd = df['cvd']
    
    # Detect local maxima
    price_high = price == price.rolling(lookback, center=True).max()
    cvd_high = cvd == cvd.rolling(lookback, center=True).max()
    
    # Logic: 
    # If Price makes New High within window, but CVD is NOT at New High 
    # (actually significantly lower), flag as Bearish Divergence.
    # This requires more complex peak finding algorithms in production.
    
    return df
```

### 4.2 Rust Implementation

```rust
pub struct CvdCalculator {
    cumulative_delta: f64,
}

impl CvdCalculator {
    pub fn new() -> Self {
        Self { cumulative_delta: 0.0 }
    }

    /// Process a new bar.
    /// taker_buy_vol: specific field from exchange (e.g. Binance)
    /// total_vol: total volume of bar
    pub fn update(&mut self, taker_buy_vol: f64, total_vol: f64) -> f64 {
        let taker_sell_vol = total_vol - taker_buy_vol;
        let delta = taker_buy_vol - taker_sell_vol;
        
        self.cumulative_delta += delta;
        self.cumulative_delta
    }
    
    /// Reset (useful for Session CVD)
    pub fn reset(&mut self) {
        self.cumulative_delta = 0.0;
    }
}
```

---

## 5. Strategy: The Absorption Reversal

### 5.1 The Logic

Smart money executes via Limit Orders (passive) to minimize slippage. Retail executes via Market Orders (aggressive). Therefore:

- **Smart Money** shows up in the Price (holding the level) but NOT in the CVD (no aggression).
- **Retail** shows up in the CVD (aggression) but FAILS to move price.

### 5.2 The Setup (Short)

1. **Context**: Market is in an Uptrend.
2. **Trigger**: Price approaches a Key Resistance Level.
3. **Observation**:
    - Candles are Green.
    - CVD is spiking Vertical Green (Massive buying).
    - Price **refuses** to break the level (wicks).
4. **Entry**: Short on the close of the rejection candle.
5. **Stop**: Just above the resistance (the limit wall).

### 5.3 GOLIATH Integration

GOLIATH uses CVD as a primary feature in the **LSTM Microstructure Model**. The Divergence is calculated as the spread between `Z-Score(Price)` and `Z-Score(CVD)`.

- If `Z(Price) - Z(CVD) > Threshold`: Bearish Divergence (Price high, CVD low).
- If `Z(CVD) - Z(Price) > Threshold`: Bullish Absorption (CVD selling hard, Price holding).

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 141 |
| Name | Cumulative Volume Delta (CVD) |
| Requirement | Tick Data / Taker Volume Data |
| Formula | CumSum(BuyVol - SellVol) |
| Signal | Divergence (Absorption) |
| Type | Unbounded Accumulator |
| GOLIATH Role | Manipulation Detector / Smart Money Tracker |
