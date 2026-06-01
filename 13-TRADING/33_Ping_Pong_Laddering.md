# 33 - Ping-Pong Laddering (Grid Trading)

**Volume:** 33 of 50
**Strategy Type:** Market Making / High Frequency / Yield Farming
**Risk Profile:** Inventory Risk / Trending Market Blowout
**Mathematical Basis:** Geometric Series ($x_i = a \cdot r^i$) & Mean Reversion

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Physics of the Grid](#2-the-physics-of-the-grid)
    * 2.1. Arithmetic vs Geometric Spacing.
    * 2.2. The Capture Range.
3. [Strategy Logic](#3-strategy-logic)
    * 3.1. Setup: Calculate Top, Bottom, and Grid Count.
    * 3.2. Execution: Limit Orders on both sides.
    * 3.3. The Ping-Pong: Buy Low, Sell High, Repeat.
4. [Advanced Grids: Geometric Spacing](#4-advanced-grids-geometric-spacing)
    * 4.1. Why Arithmetic Fails (Percentage moves vs Absolute moves).
    * 4.2. Geometric Formula derivation.
5. [Risk Management](#5-risk-management)
    * 5.1. The "Falling Knife" Scenario.
    * 5.2. Stop Loss vs Hedging (Perpetual Futures).
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Grid Generator).
    * 6.2. Rust (High-Performance Order Manager).
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Ping-Pong Laddering** (or Grid Trading) provides liquidity to the market in a defined range.
It profits from volatility (noise) regardless of direction, as long as the price stays within the range.
It is the strategy of the **Market Maker**.
By integrating **Geometric Spacing**, we ensure that our profit margin remains constant (%) at every price level, maximizing efficiency in parabolic moves.

---

# 2. The Physics of the Grid

## 2.1. Arithmetic vs Geometric

* **Arithmetic:** Orders every $100.
  * Problem: At $1000, $100 is 10%. At $100,000, $100 is 0.1%. Your profit shrinks as price rises.
* **Geometric:** Orders every 1%.
  * Benefit: Consistent profitability. The grid expands as price rises and contracts as price falls.

## 2.2. The Capture Range

The Grid must encompass 95% of the expected price movement for the duration of the strategy.
Use **Bollinger Bands (3 Sigma)** to define Top and Bottom.

---

# 3. Strategy Logic

## 3.1. Setup

1. **Top:** Upper Bollinger Band (20, 3).
2. **Bottom:** Lower Bollinger Band (20, 3).
3. **Count:** Calculate optimal number of grids based on Fee structure. (Profit per grid > 2x Fees).

## 3.2. Execution

Place $N$ Buy Limit orders below price and $N$ Sell Limit orders above price.

## 3.3. The Ping-Pong

* When a Buy Order is filled, place a corresponding Sell Order at `Buy_Price * (1 + Profit%)`.
* When a Sell Order is filled, place a corresponding Buy Order at `Sell_Price * (1 - Profit%)`.
* **Result:** You capture the spread on every oscillation.

---

# 4. Advanced Grids: Geometric Spacing

From `043_Grid_Geometric_Spacing`:

## 4.1. The Logic

We want a grid where the ratio between consecutive levels is constant.
$$ r = \left( \frac{\text{Top}}{\text{Bottom}} \right)^{\frac{1}{N}} $$
Levels: $L_0 = \text{Bottom}, L_1 = L_0 \cdot r, L_2 = L_0 \cdot r^2, \dots$

## 4.2. Optimization

This ensures that the **Return on Capital** for every trade is identical.
Ideally suited for crypto assets that can move 100% in a week.

---

# 5. Risk Management

## 5.1. Inventory Risk

If price crashes below `Bottom`, you are left holding a "Bag" of long positions.
**Solution:** Stop Loss below `Bottom`, OR (Better) hold a Short Perpetual Future hedge to neutralize Delta.

---

# 6. Implementation: Production Grade

## 6.1. Python (Grid Generator)

```python
import numpy as np

def generate_geometric_grid(lower_price, upper_price, num_grids):
    """
    Generates geometrically spaced grid levels.
    """
    if lower_price <= 0 or upper_price <= lower_price:
        raise ValueError("Invalid price range")
        
    # Common Ratio
    ratio = (upper_price / lower_price) ** (1 / num_grids)
    
    levels = [lower_price * (ratio ** i) for i in range(num_grids + 1)]
    return levels, ratio

# Example
# levels, r = generate_geometric_grid(10000, 20000, 10)
# profit_per_trade = r - 1
```

## 6.2. Rust (Order Manager)

```rust
pub struct GridBot {
    levels: Vec<f64>,
    active_orders: HashMap<usize, OrderID>, // Level Index -> OrderID
}

impl GridBot {
    pub fn on_fill(&mut self, level_idx: usize, side: Side) {
        // If Buy filled at Level i, Place Sell at Level i+1
        if side == Side::Buy {
            if level_idx + 1 < self.levels.len() {
                self.place_order(self.levels[level_idx + 1], Side::Sell);
            }
        }
        // If Sell filled at Level i, Place Buy at Level i-1
        else {
            if level_idx > 0 {
                self.place_order(self.levels[level_idx - 1], Side::Buy);
            }
        }
    }
}
```

---

# 7. Conclusion

**Ping-Pong Laddering** turns volatility into an asset.
With **Geometric Spacing**, it scales perfectly with the asset price.
It is the workhorse of the GOLIATH system for sideways markets.
While Trend strategies wait months for a payout, the Grid pays the rent every single day.
