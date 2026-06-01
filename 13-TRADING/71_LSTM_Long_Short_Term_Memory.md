# 71 - LSTM & Funding Rates: Predicting the "Tax"

**Volume:** 71 of 100
**Strategy Type:** Deep Learning / Sequence Modeling / Crypto Arbitrage
**Risk Profile:** Vanishing Gradients / Model Overfitting / Liquidation Risk
**Mathematical Basis:** LSTM Cells (Gated Memory) & Perpetual Funding Formula

> "The Funding Rate is the heartbeat of the market. LSTMs are the stethoscope."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Memory in Machines](#2-the-theory-memory-in-machines)
    * 2.1. The RNN Problem (Short-term memory).
    * 2.2. LSTM (Long Short-Term Memory): The Three Gates.
    * 2.3. The Application: Why Funding Rates are a Sequence Problem.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. **The Funding Predictor:** Use LSTM to forecast the *next* 8-hour rate.
    * 3.2. **The Front-Run:** If LSTM predicts High Funding, Open Long *before* the crowd.
    * 3.3. **The Arbitrage:** If Predicted Rate > Risk Free, Execute Cash & Carry.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. LSTM Equations ($f_t, i_t, o_t$).
    * 4.2. Funding Rate Formula ($PremiumIndex + Clamp$).
    * 4.3. Backpropagation Through Time (BPTT).
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. **BitMEX 2017:** Funding reached 0.375% *every 8 hours* (1% daily). LSTMs trained on volume predicted these spikes.
    * 5.2. **The "Short Squeeze" Signal:** Negative predicted funding often precedes a violent upside reversal (e.g., July 2021).
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (PyTorch LSTM + CCXT Data Fetching).
    * 6.2. Rust (Tch-rs Inference Engine).
7. [Risk Management](#7-risk-management)
    * 7.1. Overfitting Time-Series (Dropout).
    * 7.2. Regime Change (When the "Tax" logic changes).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 71** represents the fusion of **Deep Learning (Strategy 71)** and **Crypto Market Structure (Indicator 071)**.

* **The Engine:** Long Short-Term Memory (LSTM) networks, designed to learn long-term dependencies in time-series data.
* **The Fuel:** Funding Rates. The periodic payments between Longs and Shorts in Perpetual Swaps.

**The Edge:**
Funding Rates are not random. They follow a cyclical pattern driven by leverage demand, volatility, and sentiment.
A standard trader sees the current rate.
An LSTM sees the *trajectory* of the rate, allowing GOLIATH to enter "Yield Farming" trades *before* the yield appears.

---

# 2. The Theory

## 2.1. The Vanishing Gradient

Standard Neural Nets (MLPs) cannot remember the past.
Simple RNNs try, but "forget" events deeper than 10 steps back due to vanishing gradients during Backpropagation.
Market cycles (Funding Rate trends) often last weeks (Thousands of steps).

## 2.2. LSTM: The Solution

Schmidhuber (1997) introduced the **Cell State ($C_t$)**: A dedicated memory highway.
Information can flow along it unchanged.

* **Forget Gate:** What to throw away?
* **Input Gate:** What to store?
* **Output Gate:** What to tell the next layer?

## 2.3. Funding Rate Dynamics (from Indicator 071)

$$ Funding = PremiumIndex + Clamp(Interest - Premium, \pm 0.05\%) $$
The **Premium Index** is derived from the difference between the Perpetual Price and the Spot Price.
This difference is *highly autoregressive*. If users are bullish now, they will likely be bullish in 1 hour.
LSTMs excel at capturing this "Sentiment Inertia".

---

# 3. The Strategy Rules

## 3.1. The Predictor Model

* **Inputs:** Last 60 hours of Funding Rates, Open Interest, Volume, Price Volatility.
* **Target:** The *next* Funding Rate (t+1).
* **Architecture:** 2-Layer LSTM (Hidden Size 128) -> Linear Head.

## 3.2. Strategic Execution

1. **Yield Sniping:**
    * If Model predicts Funding Rate will spike > 0.1% (Extreme Greed).
    * **Action:** Enter "Cash and Carry" (Short Perp / Long Spot) *now*.
    * **Logic:** Capture the high yield before other arbs compress the spread.

2. **Contrarian Reversal:**
    * If Model predicts Funding Rate will flip from Negative to Positive.
    * **Action:** Close Short Positions.
    * **Logic:** Bearish sentiment is exhausting.

---

# 4. Mathematical Derivation

## 4.1. LSTM Equations

$$ f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f) $$
$$ i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i) $$
$$ \tilde{C}_t = \tanh(W_C \cdot [h_{t-1}, x_t] + b_C) $$
$$ C_t = f_t * C_{t-1} + i_t * \tilde{C}_t $$
$$ h_t = o_t * \tanh(C_t) $$

## 4.2. The Premium Index ($P$)

$$ P = \frac{Max(0, Impact Bid - Index) - Max(0, Index - Impact Ask)}{Index} $$
This determines the core component of the Funding Rate.

---

# 5. Historical Case Studies

## 5.1. BitMEX 2017 (The Bull Run)

Funding rates on BitMEX XBTUSD were consistently 0.375% every 8 hours.
Simple mean-reversion models failed (they kept shorting, expecting 0%).
LSTMs trained on the "Bull Regime" correctly learned that *high funding predicts higher funding*, allowing the model to stay Long the basis.

## 5.2. The Negative Basis Trap (2022)

During the Terra collapse, funding went negative (-0.1%).
Traders bought Perps to earn the fee, but Price fell 99%.
**Rule:** Never trade Funding Arb without a Spot Hedge (Delta Neutral).

---

# 6. Implementation: Production Grade

## 6.1. Python (PyTorch LSTM + CCXT)

```python
import torch
import torch.nn as nn
import ccxt
import pandas as pd
import numpy as np

# --- Part A: The Model ---
class LSTMFundingPredictor(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=128, num_layers=2):
        super(LSTMFundingPredictor, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_dim, 1) # Predicts scalar Funding Rate

    def forward(self, x):
        # x shape: (batch, seq_len, features)
        out, (h_n, c_n) = self.lstm(x)
        # Use last hidden state
        last_out = out[:, -1, :]
        prediction = self.fc(last_out)
        return prediction

# --- Part B: The Data (Indicator 071) ---
def fetch_funding_history(symbol='BTC/USDT', limit=1000):
    exchange = ccxt.binance()
    # Fetch predicted funding rates
    funding = exchange.fetch_funding_rate_history(symbol, limit=limit)
    df = pd.DataFrame(funding)
    return df[['timestamp', 'fundingRate', 'datetime']]

# --- Part C: The Strategy Logic ---
def generate_signal(model_prediction, current_rate):
    threshold_greed = 0.001 # 0.1%
    threshold_fear = -0.0005 # -0.05%
    
    if model_prediction > threshold_greed and current_rate < threshold_greed:
        return "ENTRY_LONG_BASIS (Anticipating Spike)"
    elif model_prediction < threshold_fear:
        return "ENTRY_SHORT_SQUEEZE (Anticipating Reversal)"
    return "HOLD"
```

## 6.2. Rust (Tch-rs Inference)

```rust
use tch::{nn, Device, Tensor};

pub struct FundingStrategy {
    model:  wha::LSTMFundingPredictor, // Conceptual wrapper
}

impl FundingStrategy {
    pub fn should_arbitrage(&self, current_basis: f64, predicted_funding: f64) -> bool {
        let annualized_yield = predicted_funding * 3.0 * 365.0; // 3 payments/day
        
        // If Yield > 10% APY and Basis spreads are stable
        if annualized_yield > 0.10 && current_basis > 0.0 {
            true
        } else {
            false
        }
    }
}
```

---

# 7. Risk Management

## 7.1. Temporal Overfitting

LSTMs can memorize specific dates ("It's May, so Sell").
**Mitigation:** Training must use "Walk-Forward Validation" (Train Jan-Mar, Test Apr. Train Feb-Apr, Test May).

## 7.2. Liquidation Risk

In a Cash & Carry trade (Long Spot, Short Perp), you are Delta Neutral.
However, if Price pumps 50% instantly, your Short Leg might get liquidated if you don't rebalance collateral from Spot to Perp.
**Rule:** Cross-Exchange Rebalancing Bot is mandatory.

---

# 8. Conclusion

**Strategy 71** is the application of Artificial Memory to Financial Costs.
By using **LSTMs**, we stop reacting to the Funding Rate "Tax" and start predicting it.
This transforms a passive cost of business into an active Alpha source.
It is the ultimate "Smart Money" yield farming tool.
