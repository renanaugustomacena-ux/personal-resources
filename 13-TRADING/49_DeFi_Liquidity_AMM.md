# 49 - DeFi Liquidity: Automated Market Makers (AMM)

**Volume:** 49 of 50
**Strategy Type:** Decentralized Finance / Market Making / Yield Farming
**Risk Profile:** Impermanent Loss / Smart Contract Risk / Rug Pull
**Mathematical Basis:** Constant Product Formula ($x \cdot y = k$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Robot Traders](#2-the-theory-robot-traders)
    * 2.1. The Order Book vs. The Pool
    * 2.2. Constant Product (Uniswap v2)
    * 2.3. Concentrated Liquidity (Uniswap v3)
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Pair Selection: Correlated Assets (Stable/Stable) vs Volatile (ETH/USDC).
    * 3.2. Range Selection: Min Price ($P_a$) and Max Price ($P_b$).
    * 3.3. Rebalancing: If Price exits range, liquidity is inactive (0 fees). Must re-center.
    * 3.4. Hedging: Short Futures to neutralize Delta.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Curve: $y = k/x$.
    * 4.2. Impermanent Loss (IL): $2 \sqrt{P_{ratio}} / (1+P_{ratio}) - 1$.
    * 4.3. Liquidity Density ($L$): How much capital is working for you?
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. The "DeFi Summer" (2020): 1000% APYs in Yield Farming.
    * 5.2. The UST Collapse (2022): Liquidity Providers wiped out in Stablecoin crash.
    * 5.3. Curve Finance Wars: Bribing for liquidity.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Simulating Uniswap v3 fee generation.
    * 6.2. Calculating IL for a given price move.
    * 6.3. "Just-In-Time" (JIT) Liquidity Provision.
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Delta Neutral LP": Long LP + Short Future.
    * 7.2. "Stablecoin Loop": Leveraged yield on USDC/DAI.
    * 7.3. "Option Selling equivalence": An LP position is mathematically a Short Straddle.
8. [Risk Management: The Code is Law](#8-risk-management-the-code-is-law)
    * 8.1. Smart Contract Bug: The pool gets drained. 100% Loss.
    * 8.2. Toxic Flow: Arbitrageurs (LVR) pick off your stale prices.
    * 8.3. Gas Costs: Rebalancing on Ethereum Mainnet costs $50.
9. [Conclusion: The Future of Exchange](#9-conclusion-the-future-of-exchange)

---

# 1. Executive Summary

**Automated Market Makers (AMMs)** replaced the Limit Order Book in DeFi.
Instead of placing orders, you deposit assets into a **Pool**.
Traders trade against the Pool.
You earn trading fees (e.g., 0.3%) proportional to your share of the pool.
However, if prices diverge, you suffer **Impermanent Loss (IL)**.
Strategy 49 is about maximizing Fees while minimizing IL.

---

# 2. The Theory

### 2.1. Constant Product

$x$: Amount of Token A (ETH).
$y$: Amount of Token B (USDC).
$k$: Constant.
$$ x \cdot y = k $$
If a trader buys ETH (removes $dx$), they must deposit USDC ($dy$) such that $(x - dx)(y + dy) = k$.
This automatically adjusts the price $P = y/x$.

### 2.2. Concentrated Liquidity (v3)

In v2, liquidity is spread from 0 to Infinity. Most of it is never used.
In v3, you choose a range $[P_{min}, P_{max}]$.
Your capital is concentrated only in this range.
**Result:** 4000x higher capital efficiency.
**Risk:** 4000x higher Impermanent Loss if price moves.

---

# 3. Strategy Rules

### 3.1. The Pseudo-Delta

Providing Liquidity is a **Short Volatility** strategy.
You want price to stay inside your range so you collect fees.
If price stays, you win.
If price rips (up or down), you lose (via IL).

### 3.2. Pair Selection

* **Stable/Stable (USDC/USDT):** Minimal IL. Low Fees (0.01%). High Leveraged Yield.
* **Blue Chip (ETH/BTC):** High Correlation. Moderate Fees. Moderate IL.
* **Volatile (ETH/USDC):** Max Fees. Max IL. High Risk.

### 3.3. Rebalancing

If Price exits your range $[1800, 2200]$, you stop earning fees.
You must withdraw and re-deposit in a new range $[2100, 2500]$.
This "realizes" the Impermanent Loss into Permanent Loss.

---

# 4. Mathematical Derivation

### 4.1. Impermanent Loss

Let $P_0$ be entry price, $P_1$ be exit price. $r = P_1 / P_0$.
Value of Holding (HODL): $V_{hold} = 0.5 + 0.5r$.
Value of LP Position: $V_{pool} = \sqrt{r}$.
$$ IL = \frac{V_{pool} - V_{hold}}{V_{hold}} = \frac{2\sqrt{r}}{1+r} - 1 $$
If price doubles ($r=2$), IL = -5.7%.
If price 5x ($r=5$), IL = -25%.
You have less value than if you just held the tokens.

---

# 5. Historical Case Studies

### 5.1. Uniswap v3 Launch

Professional Market Makers (Wintermute) entered DeFi.
Retail LPs lost money consistently on ETH/USDC pairs due to IL > Fees.
Only LPs who actively hedged (Delta Neutral) made profit.

### 5.2. JIT Attacks

MEV Bots see a large swap in the mempool.
They insert a massive LP position *exactly* at that tick range.
They absorb 90% of the fee from the swap.
They withdraw immediately in the same block.
Passive LPs get $0 fees.

---

# 6. Python Implementation

```python
import numpy as np

def calculate_il(price_ratio):
    # price_ratio = P1 / P0
    return (2 * np.sqrt(price_ratio)) / (1 + price_ratio) - 1

def simulate_amm_returns(initial_capital, entry_price, exit_price, fee_apr, days):
    # 1. HODL Value
    eth_amount = (initial_capital / 2) / entry_price
    usdc_amount = initial_capital / 2
    hodl_value = (eth_amount * exit_price) + usdc_amount
    
    # 2. LP Value (ignoring fees)
    ratio = exit_price / entry_price
    lp_value_raw = hodl_value * (1 + calculate_il(ratio))
    
    # 3. Fee Revenue
    fees = lp_value_raw * (fee_apr * days / 365)
    
    total_lp_value = lp_value_raw + fees
    return total_lp_value, hodl_value

# Example
# P0 = 2000, P1 = 3000 (50% pump).
# Fees = 30% APR. Duration 30 days.
# IL vs Fees race.
```

### 6.3. Optimal Range Width

Narrow Range = High Fees, High IL Risk.
Wide Range = Low Fees, Low IL Risk.
Optimizaton Problem: Maximize $Fees - IL$.
Depends on expected Volatility ($\sigma$).
If $\sigma$ is high, widen range.

---

# 7. Optimization

### 7.1. Delta Neutral Yield Farming

Deposit \$1000 in ETH/USDC Pool.
Short \$500 ETH on Binance (Futures).
Net Delta = 0.
If ETH pumps, Pool gains less than HODL (loss), Futures lose (loss).
Wait... this creates a net loss on Delta.
You must rebalance the hedge dynamically (Gamma Hedging).
Goal: Capture the 30% Fee APY while keeping price risk approx zero.

---

# 8. Risk Management

### 8.1. LVR (Loss Versus Rebalancing)

The "Toxic Flow" problem.
When Binance price moves, Uniswap price is "stale".
Arb bots buy the cheap ETH from your pool to sell on Binance.
You are selling cheap ETH.
This is LVR. It is permanent value leak.
**Solution:** Reduced block times (L2s) or Oracle-based AMMs.

### 8.2. Smart Contract Risk

Curve Finance hack (Vyper bug).
\$60 Million lost.
Diversify across protocols (Uniswap, Curve, Balancer).

---

# 9. Conclusion

DeFi Market Making is the democratization of high finance.
Anyone can be a Market Maker.
But the math is unforgiving.
Passive liquidity is "dead money".
Active, algorithmic liquidity provision (Rebalancing + Hedging) is the only scalable strategy.
For GOLIATH, we interact with DeFi smart contracts directly to capture yield on idle assets.
It is the "Savings Account" of the 21st century.
