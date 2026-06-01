# 32 - Rebate Capture: The Maker-Taker Game

**Volume:** 32 of 50
**Strategy Type:** HFT / Microstructure / Fee Arbitrage
**Risk Profile:** Execution Risk / Adverse Selection
**Mathematical Basis:** $P_{net} = P_{trade} + \text{Rebate}$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Subsidized Liquidity](#2-the-theory-subsidized-liquidity)
    * 2.1. Maker-Taker Model (Exchanges pay you to post limit orders)
    * 2.2. Taker-Maker Model (Inverted exchanges)
    * 2.3. The "Scratch" Trade (Buying and Selling at same price for profit)
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Setup: High Volume, Tight Spread stocks (BAC, SIRI)
    * 3.2. The Trade: Join the Bid (Maker)
    * 3.3. The Exit: Join the Ask (Maker)
    * 3.4. The Profit: Bid-Ask Spread ($0) + Rebate ($0.0030) + Rebate ($0.0030) = $0.0060 per share.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Effective Spread: $S_{eff} = S_{quoted} - 2 \times \text{Rebate}$
    * 4.2. Break-Even Win Rate: < 50% due to rebates?
    * 4.3. Adverse Selection probability
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. The "Rebate Kings" (GETCO, Tradebot)
    * 5.2. Direct Edge vs BATS vs Nasdaq (Exchange Competition)
    * 5.3. High Frequency Trading profitability source (50% from Rebates)
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Modeling Fee Structures
    * 6.2. Smart Order Router (SOR) Logic
    * 6.3. Net PnL Calculator
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. Inter-Exchange Arbitrage (Buy on Maker-Taker, Sell on Taker-Maker)
    * 7.2. "Fee Avoidance" (Retail focus)
    * 7.3. Tiered Volume Pricing (The more you trade, the more you get paid)
8. [Risk Management: The Queue Position](#8-risk-management-the-queue-position)
    * 8.1. Queue Priority: Price-Time vs Pro-Rata.
    * 8.2. If you are at the back of the queue, you never get filled.
    * 8.3. "Cancel/Replace" penalties.
9. [Conclusion: The Casino Pays the House](#9-conclusion-the-casino-pays-the-house)

---

# 1. Executive Summary

**Rebate Capture** turns trading on its head.
Normally, you pay fees to trade.
In the US Equity Market (and some Crypto exchanges), the Exchange **pays you** to provide liquidity (Maker).
They charge the person crossing the spread (Taker).
Example: Nasdaq pays $0.0029 per share to Makers. Charges $0.0030 to Takers.
Net Profit for Exchange: $0.0001.
Net Profit for HFT: $0.0029 per share.
If you trade 1 Billion shares a day, that is $2.9 Million in daily revenue *assuming flat trading PnL*.

---

# 2. The Theory

### 2.1. Liquidity Incentive

Exchanges compete for liquidity.
If an exchange has the best liquidity (tightest spread, deepest book), everyone sends orders there.
To attract liquidity providers (HFTs), exchanges offer **Rebates**.
This created a massive industry of "Rebate Harvesting" bots.

### 2.2. Inverted Venues (Taker-Maker)

Some exchanges (e.g., BYX, EDGA) do the opposite.
They **Charge** the Maker and **Pay** the Taker.
Why? To attract aggressive flow.
HFTs use Inverted Venues to exit positions quickly (Taking liquidity) for free or at a profit.

---

# 3. Strategy Rules

### 3.1. The "Scratch"

Buy 100 shares of Microsoft at $300.00 (Limit Order).
Sell 100 shares of Microsoft at $300.00 (Limit Order).
Gross PnL: $0.
Rebate (Buy): +$0.29.
Rebate (Sell): +$0.29.
Net PnL: +$0.58.
This is risk-free money if execution is perfect.

### 3.2. Queue Position

The game is **Queue Priority**.
Everyone wants the rebate. The Bid Queue at $300.00 might have 100,000 shares.
If you join the back, you will never get filled unless the price crashes through $300.00 (Adverse Selection).
**Rule:** Only join queues where you can be in the top 10% of size (or use Order Types that jump the queue, like "Midpoint Peg").

---

# 4. Mathematical Derivation

Total Profit $\pi$:
$$ \pi = N \times (P_{sell} - P_{buy}) + N \times (R_{maker\_buy} + R_{maker\_sell}) - \text{Fixed Costs} $$
If $P_{sell} = P_{buy}$ (Scratch):
$$ \pi = 2 N R $$
However, Adverse Selection applies.
If you are filled on the Bid, it means someone sold to you.
Usually, price ticks down shortly after.
Suppose price drops to $299.99$.
Loss on Trade: $0.01 per share.
Rebate Gain: $0.006 per share.
Net Loss: $0.004.
**Constraint:** The trade must not move against you by more than the spread minus rebates.

---

# 5. Historical Case Studies

### 5.1. Direct Edge (EDGX) vs Nasdaq

In 2009, Direct Edge offered massive rebates to steal market share from Nasdaq.
HFTs routed everything to EDGX.
Nasdaq was forced to match the rebates.
The "race to the bottom" on fees (or race to the top on rebates) benefited HFTs immensely.

### 5.2. Crisp (2012)

A prop shop focused purely on Rebate Capture in high-volume, low-volatility ETFs (SPY, QQQ, XLF).
XLF (Financial Sector ETF) traded at $15 with a 1-cent spread.
It was the "Rebate Farm".
Billions of shares traded for the sole purpose of exchanging rebate checks.

---

# 6. Python Implementation

```python
import pandas as pd

class RebateCaptureStrategy:
    def __init__(self, maker_rebate=0.0030, taker_fee=0.0030):
        self.maker_rebate = maker_rebate
        self.taker_fee = taker_fee
        self.pnl = 0
        self.shares_traded = 0

    def calculate_net_pnl(self, executions):
        # executions: list of dict {'side': 'buy', 'price': 100, 'type': 'maker'}
        
        gross_pnl = 0
        fees = 0
        rebates = 0
        
        inventory = 0
        avg_cost = 0
        
        for trade in executions:
            price = trade['price']
            qty = trade['qty']
            
            # PnL Logic (FIFO or Avg Cost)
            if trade['side'] == 'buy':
                inventory += qty
                # Update avg cost
                
            elif trade['side'] == 'sell':
                inventory -= qty
                gross_pnl += (price - avg_cost) * qty # Simplified
            
            # Fee Logic
            if trade['type'] == 'maker':
                rebates += qty * self.maker_rebate
            else:
                fees += qty * self.taker_fee
                
        net_pnl = gross_pnl + rebates - fees
        return net_pnl, rebates

    def route_order(self, exchange_list):
        # Create a routing table based on Net Cost
        # Net Cost = Price + Taker Fee (if buying)
        # Net Proceeds = Price + Maker Rebate (if selling active)
        
        sorted_exchanges = sorted(exchange_list, key=lambda x: x.rebate, reverse=True)
        return sorted_exchanges[0]
```

### 6.3. Exchange Tiers

Exchanges have "Tiers".
Tier 1: Trade > 10M shares/day $\to$ Rebate $0.0020.
Tier 5: Trade > 0.1% of Total Market Volume $\to$ Rebate $0.0032.
GOLIATH tracks volume to ensure we hit the highest tier.
If we are close to the next tier at month-end, we run "Wash Trades" (legal if across different strategies) or "Volume Padding" strategies (Break-even trades) just to unlock the higher tier for the whole month's PnL.

---

# 7. Optimization

### 7.1. Maker-Taker Arb

Buy on Maker-Taker (Earn Rebate).
Sell on Taker-Maker (Earn Rebate/Pay low fee).
Net Result: Capture spread + Rebate differential.

### 7.2. Dark Pools (Midpoint)

Dark Pools generally don't pay rebates.
But they save the spread (Midpoint execution).
Midpoint is better than Bid + Rebate if the spread > $0.01.
If Spread is 1 cent, Midpoint saves $0.005. Rebate is $0.003. Midpoint wins.
If Spread is 0 (Locked), Rebate wins.

---

# 8. Risk Management

### 8.1. Adverse Selection

The "Toxic Fill".
You are the only Bid left at $10.00.
Everyone else cancelled.
You get hit. Start losing money immediately.
**Solution:** Queue Jump. If you detect cancellations (OFI negative), cancel your order faster than the others.
"Cancel if Request < 1ms".

### 8.2. Regulatory Risk

Wash Trading (Trading with yourself to collect rebates) is illegal.
SEC fines.
Strategies must ensure they are trading with distinct counterparties or bona-fide market risk.

---

# 9. Conclusion

Rebate Capture is the "Grind" of HFT.
It is low margin, high volume.
It requires scale (Tier pricing).
For GOLIATH, Rebate Capture is implicit in our Execution Algo.
We never initiate a "Market Order" unless necessary.
We always try to "Capture the Rebate" by posting passive limits.
This subsidies our Alpha strategies.
Even if our specific Rebate Strategy PnL is 0, the *savings* on fees across the firm is massive.
