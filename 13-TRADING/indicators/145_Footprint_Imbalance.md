# Indicator 145: Footprint Imbalance — Granular Aggression at Price

***"The candle shows you the battle's result. The Footprint shows you the casualties at every trench level."***

---

## 1. Executive Summary

**Footprint Imbalance** (also known as Bid/Ask Imbalance) is a visualization technique that peers *inside* a single candle. Instead of just Open-High-Low-Close, it displays the Volume traded at the Bid and the Volume traded at the Ask for every price tick within the bar.

An **Imbalance** occurs when aggressive buying volume at a specific price level significantly overwhelms the aggressive selling volume at the corresponding diagonal level (Ask vs. Bid below). The standard threshold is **300%** (3:1 ratio).

- **Buy Imbalance**: Aggressive Buyers swept the Ask with 3x more volume than Sellers hit the Bid.
- **Sell Imbalance**: Aggressive Sellers hit the Bid with 3x more volume than Buyers lifted the Ask.
- **Stacked Imbalance**: Three or more consecutive price levels with imbalances in the same direction. This creates a powerful Support/Resistance zone.

In GOLIATH, Stacked Imbalances are treated as **"Concrete Floors"** (Support) or **"Concrete Ceilings"** (Resistance). The market rarely breaks them on the first test.

---

## 2. Mathematical Foundations

Comparing diagonal levels is crucial because in the order book, the Ask is always one tick above the Bid.
To calculate imbalance at Price Level $P$:

$$ \text{Ratio}_{Buy} = \frac{\text{Vol}_{Ask}(P)}{\text{Vol}_{Bid}(P-1)} $$

If $\text{Ratio}_{Buy} \ge 3.0$ (300%), we have a **Buy Imbalance**.

$$ \text{Ratio}_{Sell} = \frac{\text{Vol}_{Bid}(P)}{\text{Vol}_{Ask}(P+1)} $$

If $\text{Ratio}_{Sell} \ge 3.0$ (300%), we have a **Sell Imbalance**.

*(Note: The diagonal comparison aligns the aggressor flow mechanics).*

### 2.1 Unfinished Business (Unfinished Auction)

If the High of the bar has volume at the Ask > 0 and volume at the Bid > 0, the auction is unfinished. Prices usually revisit this level to complete the auction (where volume tapers to zero at the extreme).

---

## 3. Signal Generation

### 3.1 Stacked Imbalances (The Zone)

- **Signal**: 3+ consecutive Buy Imbalances in a rising bar.
- **Meaning**: Aggressive buyers chased price up through multiple levels. They are committed.
- **Action**: Draw a Zone across these price levels.
- **Trade**: Limit Buy at the *top* of the Buy Imbalance Zone on the first retest.

### 3.2 Imbalance Reversal (The Trap)

- **Setup**: Price moves down into Support.
- **Trap**: A Sell Imbalance appears at the Low (Aggressive selling).
- **Reversal**: The next bar immediately trades above the Sell Imbalance.
- **Meaning**: Sellers were trapped at the bottom.
- **Trade**: Long. Target the liquidity of the trapped shorts.

### 3.3 Zero Print

- **Condition**: Volume on one side is 0.
- **Meaning**: Complete vacuum. Price skipped a tick. Extreme varying volatility.

---

## 4. Implementation

### 4.1 Python Implemetation (Requires Tick Data Reconstruction)

This is computationally expensive and requires a customized DataFrame structure (since standard Pandas is row-per-time, not row-per-price-per-time).

```python
# Conceptual Python Structure for Footprint Analysis
# Usually done with dictionaries or sparse matrices

class FootprintBar:
    def __init__(self):
        # Map: Price -> {bid_vol, ask_vol}
        self.levels = {} 
        
    def add_trade(self, price, volume, side):
        if price not in self.levels:
            self.levels[price] = {'bid': 0, 'ask': 0}
        if side == 'buy':
            self.levels[price]['ask'] += volume
        else:
            self.levels[price]['bid'] += volume

    def calculate_imbalances(self, threshold=3.0):
        # Sort prices
        prices = sorted(self.levels.keys())
        imbalances = []
        
        for i in range(1, len(prices)):
            price_curr = prices[i]
            price_prev = prices[i-1]
            
            # Diagonal: Ask at Curr vs Bid at Prev
            ask_vol = self.levels[price_curr]['ask']
            bid_vol = self.levels[price_prev]['bid']
            
            if bid_vol > 0 and (ask_vol / bid_vol >= threshold):
                 imbalances.append((price_curr, 'BUY_IMBALANCE'))
            
            # Additional logic for Sell Imbalances (Ask at Next vs Bid at Curr)
            
        return imbalances
```

### 4.2 Rust Implementation (Production Grade)

```rust
use std::collections::BTreeMap;

pub struct FootprintLevel {
    pub bid_vol: f64,
    pub ask_vol: f64,
}

pub struct FootprintBar {
    pub levels: BTreeMap<u64, FootprintLevel>, // Price as u64 (fixed point)
}

impl FootprintBar {
    pub fn new() -> Self {
        Self { levels: BTreeMap::new() }
    }

    pub fn check_imbalances(&self, ratio: f64) -> Vec<(u64, bool)> {
        let mut imbalances = Vec::new();
        let prices: Vec<u64> = self.levels.keys().cloned().collect();
        
        for window in prices.windows(2) {
            let p_lower = window[0];
            let p_upper = window[1];
            
            let lower = self.levels.get(&p_lower).unwrap();
            let upper = self.levels.get(&p_upper).unwrap();
            
            // Buy Imbalance: Upper Ask vs Lower Bid
            if lower.bid_vol > 0.0 && (upper.ask_vol / lower.bid_vol >= ratio) {
                imbalances.push((p_upper, true)); // True = Buy
            }
            
            // Sell Imbalance: Lower Bid vs Upper Ask
            if upper.ask_vol > 0.0 && (lower.bid_vol / upper.ask_vol >= ratio) {
                imbalances.push((p_lower, false)); // False = Sell
            }
        }
        imbalances
    }
}
```

---

## 5. Strategy: The Imbalance Retest

GOLIATH considers Stacked Imbalances as **High-Fidelity Supports**.

1. **Identify**: A bar with 3 consecutive Buy Imbalances.
2. **Wait**: Do not chase. Wait for price to return to the zone.
3. **Confirm**: On retest, Delta Divergence must show "Weak Selling."
4. **Execute**: Limit Buy at the top of the stack.
5. **Stop**: Below the bottom of the stack.

This strategy exploits the fact that the aggressors who created the imbalances will defend their positions.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 145 |
| Name | Footprint Imbalance |
| Requirement | Tick Data / Order Flow |
| Threshold | Standard 300% (3:1) |
| Visualization | Numbers inside Candle |
| GOLIATH Role | Micro-Support/Resistance Definition |
| Key Pattern | Stacked Imbalances |
