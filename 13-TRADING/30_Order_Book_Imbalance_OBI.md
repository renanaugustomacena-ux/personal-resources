# 30 - Order Book Imbalance (OBI): The Micro-Predictor

**Volume:** 30 of 50
**Strategy Type:** HFT / Microstructure Alpha / Execution Algo
**Risk Profile:** Low (Ultra Short Term) / Execution Latency Risk
**Mathematical Basis:** Limit Order Book Dynamics ($V_b$ vs $V_a$) & Queue Depletion

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Supply and Demand (Visible)](#2-the-theory-supply-and-demand-visible)
    * 2.1. The Limit Order Book (LOB) as Future Intent
    * 2.2. The Physics: Path of Least Resistance
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Calculate OBI Metric: $\frac{V_b - V_a}{V_b + V_a}$
    * 3.2. Thresholds: Absolute Imbalance > 0.6
    * 3.3. Execution: Market Take (Aggressive) vs Limit Join (Passive)
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Queue Dynamics: $P(Up) = f(OBI)$
    * 4.2. Depth Weighted OBI (Level 2+)
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Crypto "Buy Walls" vs "Sell Walls"
    * 5.2. The Flash Crash "Spoofer"
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Snapshot Analysis & Rules)
    * 6.2. Rust (SBE / Live Stream with BTreeMap)
7. [Optimization & Variations](#7-optimization--variations)
8. [Risk Management: The Mirage](#8-risk-management-the-mirage)
9. [Conclusion: The Physics of Price](#9-conclusion-the-physics-of-price)

---

# 1. Executive Summary

**Order Book Imbalance (OBI)** measures the pressure in the Limit Order Book (LOB).
If there are 1,000 Bitcoins on the Bid (Buy) and only 10 Bitcoins on the Ask (Sell).
It is physically harder for the price to go Down than Up.
Sellers have to chew through 1,000 BTC. Buyers only need to eat 10 BTC.
**Physics dictates the path of least resistance: UP.**
OBI strategies front-run this mechanical reality.

---

# 2. The Theory

## 2.1. The Wall

Imagine the Book is a physical queue.

* **Bid Wall (Support):** $V_b$
* **Ask Wall (Resistance):** $V_a$
* **Signal:** If $V_b \gg V_a$, Buy. If $V_a \gg V_b$, Sell.

## 2.2. Short Term Predictor

OBI is the single most predictive signal for the *very next trade*.
Correlation between OBI and next mid-price change is > 0.6 in most assets.
However, this predictive power decays exponentially. You must act fast.

---

# 3. Strategy Rules

## 3.1. The Metric ($\rho$)

$$ \rho = \frac{V_b - V_a}{V_b + V_a} $$

* Ranges from -1 to +1.
* **+1:** All Liquidity on Bid (Buy Pressure).
* **-1:** All Liquidity on Ask (Sell Pressure).

## 3.2. Execution

* **Passive:** If OBI > 0.3, Join the Bid (Front of queue). Probability of fill increases because sellers are desperate.
* **Aggressive:** If OBI > 0.8, Market Buy (Cross the Spread). The Ask wall is about to break, don't wait.

---

# 4. Mathematical Derivation

## 4.1. Queue Dynamics

Model the Limit Order Book as a Markov Chain.
$$ P_{up} = \frac{V_b}{V_b + V_a} $$
Empirical studies (Cartea et al.) show this linear relationship holds remarkably well in liquid markets.

## 4.2. Depth Weighted OBI

Looking only at Level 1 is noisy (spoofing). We weight the top 5 or 10 levels.
$$ OBI_{L2} = \frac{\sum Q_i^b e^{-\lambda i} - \sum Q_i^a e^{-\lambda i}}{\sum Q_i^b e^{-\lambda i} + \sum Q_i^a e^{-\lambda i}} $$
We decay volume deeper in the book because it is less likely to be traded against.

---

# 5. Historical Case Studies

## 5.1. The "Spoofer" (Navinder Sarao)

Flash Crash 2010. Sarao placed massive Sell Orders (Ask Wall) far from price to create Negative OBI. Algos read OBI < -0.8 and sold. Sarao cancelled before execution.
**Lesson:** OBI can be manipulated. Watch for "Flickering Liquidity".

## 5.2. Crypto "Buy Walls"

Whales place "Buy Walls" to prop up price.
**Rule:** Only trust liquidity near the Spread (Level 1-5). Deep liquidity is often fake ("Layering").

---

# 6. Implementation: Production Grade

## 6.1. Python (Analysis)

```python
import numpy as np

class OrderBookImbalance:
    def __init__(self):
        self.bids = [] 
        self.asks = [] 
        self.obi = 0

    def calculate_obi(self, depth=5):
        sum_bid_vol = 0
        sum_ask_vol = 0
        
        for i in range(min(depth, len(self.bids), len(self.asks))):
            weight = np.exp(-0.5 * i) # Decay
            sum_bid_vol += self.bids[i][1] * weight
            sum_ask_vol += self.asks[i][1] * weight
            
        if (sum_bid_vol + sum_ask_vol) == 0:
            return 0
        return (sum_bid_vol - sum_ask_vol) / (sum_bid_vol + sum_ask_vol)

    def get_signal(self):
        if self.obi > 0.6: return "BUY_AGGRESSIVE" # Lifting the Ask
        elif self.obi > 0.2: return "BUY_PASSIVE" # Resting on Bid
        elif self.obi < -0.6: return "SELL_AGGRESSIVE" # Hitting the Bid
        elif self.obi < -0.2: return "SELL_PASSIVE" # Resting on Ask
        return "NEUTRAL"
```

## 6.2. Rust (SBE / Live Stream)

Handling Order Book updates is the most CPU-intensive task in trading. We use a **BTreeMap** to maintain sorted order of price levels.

```rust
use std::collections::BTreeMap;

pub struct OrderBook {
    bids: BTreeMap<u64, f64>, // Price (as int/micros) -> Quantity
    asks: BTreeMap<u64, f64>,
    depth: usize,
}

impl OrderBook {
    pub fn new(depth: usize) -> Self {
        Self {
            bids: BTreeMap::new(),
            asks: BTreeMap::new(),
            depth,
        }
    }

    pub fn update_bid(&mut self, price: u64, qty: f64) {
        if qty == 0.0 { self.bids.remove(&price); } 
        else { self.bids.insert(price, qty); }
    }

    pub fn update_ask(&mut self, price: u64, qty: f64) {
        if qty == 0.0 { self.asks.remove(&price); } 
        else { self.asks.insert(price, qty); }
    }

    pub fn calculate_obi(&self) -> f64 {
        // Bids: Iter rev (Highest first - standard BTreeMap is Ascending)
        let bid_sum: f64 = self.bids.iter().rev().take(self.depth).map(|(_, &q)| q).sum();
        
        // Asks: Iter (Lowest first)
        let ask_sum: f64 = self.asks.iter().take(self.depth).map(|(_, &q)| q).sum();
        
        let total = bid_sum + ask_sum;
        if total == 0.0 { return 0.0; }
        
        (bid_sum - ask_sum) / total
    }
}
```

---

# 7. Optimization

## 7.1. OFI (Order Flow Imbalance)

OBI is specific to a snapshot. OFI measures the *change* in OBI.
Did volume get Added to Bid? (Bullish).
Did volume get Cancelled from Ask? (Bullish).
OFI is the derivative of OBI. It leads OBI.

## 7.2. Multi-Exchange OBI

If Binance OBI is Bullish + Coinbase OBI is Bullish -> Strong Signal.
Arbitrage bots unify the order books globally.

---

# 8. Risk Management: The Mirage

## 8.1. Latency (The Killer)

If your code takes 500ms (Python) to react, the HFT (FPGA 500ns) has already eaten the liquidity.
**Solution:** Use OBI as a filter for longer-term strategies (1 minute). "Don't buy if OBI is negative."

## 8.2. Icebergs

An iceberg order (Hidden size) does not show up in $V_a$. OBI says "Ask is Thin", you buy, but you hit a hidden wall.
**Detection:** Monitor "Trade Prints" vs "Quote Updates". If Trades happen but Price doesn't move $\to$ Iceberg.

---

# 9. Conclusion

Order Book Imbalance is the **Microscope** of trading.
It shows the molecular structure of price formation.
For GOLIATH, we use OBI to "Time the Entry".

* Strategy says BUY.
* Execution Algo checks OBI.
* If OBI > 0, Execute.
* If OBI < 0, Wait.
This saves slippage, which compounds to massive Annualized Alpha.
