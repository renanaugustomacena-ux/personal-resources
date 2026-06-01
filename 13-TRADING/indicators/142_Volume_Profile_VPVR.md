# Indicator 142: Volume Profile (VPVR) — The Price Acceptance Map

***"Price is vertical. Time is horizontal. But Volume is the depth. The Volume Profile turns the chart sideways to reveal where the market actually did business."***

---

## 1. Executive Summary

**Volume Profile (VPVR)** (Volume Profile Visible Range) is an advanced charting study that displays trading activity over a specified time period at specified price levels. Instead of standard volume bars (Time-based), the Volume Profile plots a histogram on the Y-axis (Price-based).

This shifts the focus from "When did trades happen?" to "**At what price did trades happen?**"

It is the primary tool for **Auction Market Theory**, which posits that the market's purpose is to facilitate trade. Areas of high volume represent "acceptance" (fair value), while areas of low volume represent "rejection" (unfair value).

Key Composites:

- **POC (Point of Control)**: The single price level with the highest traded volume. The "Fair Value" magnet.
- **Value Area (VA)**: The range of price levels where a specified percentage (usually 70%) of total volume occurred.
- **HVN (High Volume Node)**: Local peaks in volume. Strong Support/Resistance.
- **LVN (Low Volume Node)**: Valleys in volume. Prices move through these areas quickly (Liquidity Gaps).

In GOLIATH, Volume Profile is used to define **Structural Support/Resistance**. A POC from last week is far more significant than a Fibonacci line.

---

## 2. Mathematical Foundations

The calculation requires iterating through every trade (or bar) in the visible range and binning the volume into price buckets.

### 2.1 Binning Algorithm

1. Define the **Price Range** ($Max Price - Min Price$).
2. Divide the range into **Tick Size** or user-defined bins (e.g., 100 bins).
3. For every bar/tick:
    - Identify the price range of that bar (Low to High).
    - Distribute the bar's volume equally (or proportionally) across the bins touched by that bar.

$$ \text{Volume per Bin}_p = \sum_{t=1}^{N} \text{Vol}_t \times \mathbb{I}(\text{Low}_t \le p \le \text{High}_t) $$

### 2.2 Value Area Calculation

The Value Area (VA) contains 70% of the total volume.

1. Sum total volume in the profile.
2. Identify the POC (highest volume bin).
3. Start at the POC and add the next highest adjacent bins (above or below) iteratively.
4. Stop when the cumulative volume reaches 0.70 * Total Volume.
5. The highest and lowest bins in this set define **VAH (Value Area High)** and **VAL (Value Area Low)**.

---

## 3. Signal Generation

### 3.1 The Auction Process

The market moves in search of efficiency.

- **Accepted Price**: Price spends a lot of time and volume at a level (Balancing). This creates a "Bell Curve" distribution.
- **Rejected Price**: Price touches a level and immediately reverses on low volume (Excess).

### 3.2 POC Migration (Trend)

- **Bullish**: POC is migrating upwards day over day. (Value is increasing).
- **Bearish**: POC is migrating downwards.

### 3.3 The "Virgin" POC (Naked POC)

A POC from a previous session that has not been touched again.

- **Signal**: The market has a high probability of revisiting a Naked POC to test if it is still valid fair value. It acts as a powerful magnet.

### 3.4 LVN Breakouts

When price enters a Low Volume Node (LVN), it usually accelerates. There is little friction (historical volume) to stop it. GOLIATH treats LVNs as "Fast Lanes" for momentum trades.

---

## 4. Implementation

### 4.1 Python Implementation (Approximation with OHLCV)

```python
import pandas as pd
import numpy as np

def compute_volume_profile(df: pd.DataFrame, bins: int = 100) -> dict:
    """
    Compute Volume Profile for the entire DataFrame range.
    Returns a dictionary with POC, VAH, VAL, and the histogram.
    """
    price_min = df['low'].min()
    price_max = df['high'].max()
    
    # Create Price Bins
    hist_bins = np.linspace(price_min, price_max, bins + 1)
    bin_width = hist_bins[1] - hist_bins[0]
    
    # We need to distribute volume. 
    # Simple approx: put all volume at the Close or Typical Price.
    # Better approx: distribute uniformly between High and Low.
    
    profile = np.zeros(bins)
    
    # Vectorized Histogramming is tricky with range distribution.
    # We'll use a simplified loop for clarity, though slower.
    # Production code uses Numba or Rust.
    
    for i, row in df.iterrows():
        # Find which bins this bar covers
        start_bin = int((row['low'] - price_min) / bin_width)
        end_bin = int((row['high'] - price_min) / bin_width)
        
        # Clamp to bounds
        start_bin = max(0, min(bins-1, start_bin))
        end_bin = max(0, min(bins-1, end_bin))
        
        # Distribute volume
        num_bins = end_bin - start_bin + 1
        vol_per_bin = row['volume'] / num_bins
        
        profile[start_bin : end_bin+1] += vol_per_bin
        
    # Find POC
    poc_idx = np.argmax(profile)
    poc_price = hist_bins[poc_idx]
    
    # Calculate VA (70%)
    total_vol = np.sum(profile)
    target_vol = total_vol * 0.70
    
    current_vol = profile[poc_idx]
    val_idx = poc_idx
    vah_idx = poc_idx
    
    # Expanded iterative search
    while current_vol < target_vol:
        # Check above
        vol_up = profile[vah_idx + 1] if vah_idx < bins - 1 else 0
        # Check below
        vol_down = profile[val_idx - 1] if val_idx > 0 else 0
        
        if vol_up > vol_down:
            vah_idx += 1
            current_vol += vol_up
        else:
            val_idx -= 1
            current_vol += vol_down
            
        if val_idx == 0 and vah_idx == bins - 1:
            break
            
    val_price = hist_bins[val_idx]
    vah_price = hist_bins[vah_idx]
    
    return {
        "POC": poc_price,
        "VAL": val_price,
        "VAH": vah_price,
        "Profile": profile,
        "Bins": hist_bins
    }
```

### 4.2 Rust Implementation

```rust
pub struct VolumeProfile {
    pub bins: Vec<f64>,
    pub min_price: f64,
    pub max_price: f64,
    pub bin_size: f64,
}

impl VolumeProfile {
    pub fn new(min_price: f64, max_price: f64, n_bins: usize) -> Self {
        let bin_size = (max_price - min_price) / n_bins as f64;
        Self {
            bins: vec![0.0; n_bins],
            min_price,
            max_price,
            bin_size,
        }
    }
    
    pub fn add_trade(&mut self, price: f64, volume: f64) {
        if price < self.min_price || price > self.max_price {
            return; // Out of bounds handling needed (dynamic resizing)
        }
        let idx = ((price - self.min_price) / self.bin_size) as usize;
        if idx < self.bins.len() {
            self.bins[idx] += volume;
        }
    }
    
    pub fn get_poc(&self) -> f64 {
        let (max_idx, _) = self.bins.iter()
            .enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
            .unwrap();
            
        self.min_price + (max_idx as f64 * self.bin_size)
    }
}
```

---

## 5. Strategy: The Value Area Play

### 5.1 The 80% Rule

If price opens *outside* the previous day's Value Area, but then closes *inside* it for two consecutive 30-minute bars, there is an **80% probability** that price will traverse the entire Value Area to the other side.

### 5.2 GOLIATH Implementation

GOLIATH monitors `current_price` relative to `yesterday_VAH` and `yesterday_VAL`.

- **Setup**: Price breaks back into VA.
- **Trigger**: Momentum confirmation (AO Green).
- **Target**: The opposing VA boundary (e.g., entered at VAH -> Target VAL).
- **Stop**: Outside the VA.

This is one of the highest expectancy setups in institutional trading.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 142 |
| Name | Volume Profile (VPVR) |
| Core Concept | Auction Market Theory |
| Components | POC, VAH, VAL |
| Calculation | Price-Bin Volume Aggregation |
| GOLIATH Role | Structural Level Definition |
| Key Signal | Value Area Rotation (80% Rule) |
