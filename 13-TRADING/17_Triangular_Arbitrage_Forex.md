# 17 - Triangular Arbitrage & Cross Rate Parity

**Volume:** 17 of 50
**Strategy Type:** Pure Arbitrage / HFT / Lead-Lag Directional
**Risk Profile:** Near Zero (Arb) or High (Directional)
**Mathematical Basis:** Cross-Rate Parity ($A/B \times B/C \times C/A = 1$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Forex Matrix](#2-the-theory-the-forex-matrix)
    * 2.1. The "Synthetic" Price (Path of Least Resistance)
    * 2.2. The Parity Equation
    * 2.3. Why Imbalance Exists (Latency & Fragmentation)
3. [Trading Strategies](#3-trading-strategies)
    * 3.1. Triangular Arbitrage (Risk-Free Loop)
    * 3.2. Lead-Lag Correlation (Proprietary Alpha)
    * 3.3. Synthetic Hedges (Entry timing)
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Loop Equation: $P1 \times P2 \times P3 = 1.0$
    * 4.2. Calculating Profit Percentage
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python (Synthetic Logic & Bellman-Ford)
    * 5.2. Rust (HFT Optimization for Tri-Arb)
6. [Historical Case Studies](#6-historical-case-studies)
    * 6.1. The "Golden Age" (2000-2008)
    * 6.2. Crypto Market Inefficiencies
7. [Risk Management](#7-risk-management)
    * 7.1. Execution Risk (Legging)
    * 7.2. Fee Thresholds
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Triangular Arbitrage** exploits pricing inefficiencies between three currencies that should mathematically align (e.g., EUR, USD, JPY).
If 1 Euro buys 1.1 Dollars, and 1.1 Dollars buys 0.9 Pounds, and 0.9 Pounds buys 1.01 Euros, you have a **Risk-Free Profit Loop**.

**Cross Rate Parity** is the fundamental law that governs this.
If the Arb window closes (as it does in microseconds), the "Synthetic Price" (implied by the loop) becomes a **Leading Indicator** for determining the true direction of a pair before the actual order book updates.

---

# 2. The Theory: The Forex Matrix

The Forex market is a graph of connected nodes.
Most volume is in USD pairs. Cross pairs (like EUR/JPY) are mathematically derived.

## 2.1. The Synthetic Price

* **Actual Price:** The price on the EUR/JPY order book.
* **Synthetic Price:** The price derived from EUR/USD $\times$ USD/JPY.
* **Arbitrage:** If Actual $\neq$ Synthetic (creating a Spread), risk-free profit exists.
* **Lead-Lag:** Often, liquidity flows into the Synthetic path (USD pairs) *before* the Cross pair updates. This signals a directional move in the Cross pair.

## 2.2. The Parity Equation

For three currencies A, B, C:
$$ Rate(A/C) = Rate(A/B) \times Rate(B/C) $$

---

# 3. Trading Strategies

## 3.1. Triangular Arbitrage (The Loop)

1. **Identify:** Exchange Rate Loop $EUR \to USD \to JPY \to EUR$.
2. **Calculate:** Product of rates (accounting for Bid/Ask).
3. **Trigger:** If Product > 1.0 + Fees.
4. **Execute:** 3 atomic Market Orders.

## 3.2. Lead-Lag Correlation (Directional)

The Arb window is too fast for most. But the information persists.

* **Signal:** If Synthetic EUR/USD > Actual EUR/USD (High deviation).
* **Logic:** The "Global Valuation" of Euro is higher than this specific pair shows.
* **Action:** Buy Actual EUR/USD. (Betting on Convergence).
* **Edge:** This works even with taker fees because you are betting on a directional move, not just the tiny arb spread.

## 3.3. Synthetic Hedges

If you want to Short EUR/USD but the layout is messy, check the Synthetic (EUR $\to$ JPY $\to$ USD). Use the Synthetic price as your "True" resistance level.

---

# 4. Mathematical Derivation

Let $P_{AB}$ be the price of A in terms of B.
The loop profit is:
$$ \Pi = (P_{AB} \times (1-fee)) \times (P_{BC} \times (1-fee)) \times (P_{CA} \times (1-fee)) - 1 $$

If $\Pi > 0$, we have profit.
Note: $P_{CA}$ is usually quoted as $A/C$, so you perform $1/P_{AC}$.

---

# 5. Implementation: Production Grade

## 5.1. Python (Synthetic & Arb)

```python
import pandas as pd
import numpy as np

class CrossRateMonitor:
    def __init__(self, fee=0.001):
        self.fee = fee
        
    def calculate_synthetic(self, eur_usd, usd_jpy):
        """ Returns Synthetic EUR/JPY """
        return eur_usd * usd_jpy

    def check_arbitrage(self, rates):
        """
        rates: dict with 'EURUSD', 'USDJPY', 'EURJPY' (Ask/Bid tuples)
        Loop: EUR -> USD -> JPY -> EUR
        """
        # 1. Buy USD with EUR (Sell EURUSD @ Bid)
        # Wait, quoting convention: EUR/USD 1.10. 
        # I have 1 EUR. I sell it for 1.10 USD. (Bid price).
        eur_usd_bid = rates['EURUSD'][0]
        usd_amt = 1.0 * eur_usd_bid
        
        # 2. Buy JPY with USD (Buy USDJPY @ Ask? No, USDJPY is JPY per USD)
        # I have USD. I want JPY. I Sell USD for JPY.
        # USD/JPY Bid is 110. (Market buys USD, pays JPY).
        usd_jpy_bid = rates['USDJPY'][0]
        jpy_amt = usd_amt * usd_jpy_bid
        
        # 3. Buy EUR with JPY (Buy EURJPY @ Ask? No, EURJPY is JPY per EUR)
        # I have JPY. I want EUR. I Buy EUR.
        # EUR/JPY Ask is 120. (Market sells EUR, wants 120 JPY).
        eur_jpy_ask = rates['EURJPY'][1]
        final_eur = jpy_amt / eur_jpy_ask
        
        # Net
        profit_pct = final_eur - 1.0 - (3 * self.fee)
        return profit_pct
    
    def check_lead_lag(self, rates):
        # Lead-Lag: Is Synthetic > Actual?
        # Use MID prices for signal
        avg = lambda x: (x[0]+x[1])/2
        
        eu = avg(rates['EURUSD'])
        uj = avg(rates['USDJPY'])
        ej_actual = avg(rates['EURJPY'])
        
        ej_synthetic = eu * uj
        
        spread = ej_actual - ej_synthetic
        # If Spread is Positive (Actual > Synthetic), Actual is overpriced -> Sell Actual
        return spread
```

## 5.2. Rust (Triangular Logic)

```rust
pub struct TriangularArb {
    // Storing (Bid, Ask)
    eur_usd: (f64, f64),
    usd_jpy: (f64, f64),
    eur_jpy: (f64, f64),
    fee: f64,
}

impl TriangularArb {
    pub fn new(fee: f64) -> Self {
        Self { 
            eur_usd: (0.0, 0.0), 
            usd_jpy: (0.0, 0.0), 
            eur_jpy: (0.0, 0.0), 
            fee 
        }
    }
    
    pub fn update(&mut self, pair: &str, bid: f64, ask: f64) {
        match pair {
            "EURUSD" => self.eur_usd = (bid, ask),
            "USDJPY" => self.usd_jpy = (bid, ask),
            "EURJPY" => self.eur_jpy = (bid, ask),
            _ => {}
        }
    }

    pub fn check_loop(&self) -> Option<f64> {
        // Loop: EUR -> USD -> JPY -> EUR
        // 1. Sell EUR for USD (Bid EURUSD)
        // 2. Sell USD for JPY (Bid USDJPY)
        // 3. Buy EUR with JPY (Ask EURJPY) -> Divide by Ask
        
        if self.eur_usd.0 == 0.0 || self.usd_jpy.0 == 0.0 || self.eur_jpy.1 == 0.0 {
            return None;
        }

        let start = 1.0;
        let s1 = start * self.eur_usd.0 * (1.0 - self.fee); // USD
        let s2 = s1 * self.usd_jpy.0 * (1.0 - self.fee);    // JPY
        let end = s2 / self.eur_jpy.1 * (1.0 - self.fee);   // EUR
        
        if end > 1.0 {
            return Some(end - 1.0);
        }
        None
    }
}
```

---

# 6. Historical Case Studies

## 6.1. The Golden Age (2000-2008)

Retail execution speeds matched banks. Traders could manually click buy/sell/sell and make 10 pips risk-free.
HFT algorithms closed this window by 2010.

## 6.2. Crypto Market Inefficiencies

In 2017, the "Kimchi Premium" (Bitcoin price in Korea vs USA) persisted for weeks.
Triangular Arb (BTC -> ETH -> KRW -> BTC) was a primary profit engine for early crypto funds.

---

# 7. Risk Management

## 7.1. Execution (Legging) Risk

The biggest risk is executing Leg 1 and 2, but failing Leg 3.
You are left with a massive "naked" position in a currency you didn't want (JPY).
**Solution:** Only use "Atomic" execution (smart contracts) or "Fill-or-Kill" logic on specialized HFT platforms.

## 7.2. Fee Thresholds

Standard Taker Fee (0.1%) means 0.3% round trip.
Arb spreads are rarely > 0.1%.
**Solution:** This strategy essentially requires **Maker Rebates** (negative fees) to be viable for pure arb. Use "Lead-Lag" for directional trading instead.

---

# 8. Conclusion

Triangular Arbitrage is the "Perfect Trade" that rarely exists.
However, **Cross Rate Parity** (the math behind it) is the most reliable signal in Forex.
By calculating the "Synthetic Price," GOLIATH effectively sees the "Fair Value" of a currency derived from the entire global market, not just one pair's order book.
We use this to filter our Trend Entries: "Only buy EUR/JPY if Synthetic Price confirms it."
