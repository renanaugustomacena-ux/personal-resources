# 68 - MEV Sandwich Attacks & Profitability: The Dark Forest

**Volume:** 68 of 100
**Strategy Type:** HFT / Blockchain Extractable Value (MEV) / Atomic Arb
**Risk Profile:** Reorg Risk / Bundle Rejection / Smart Contract Exploit
**Mathematical Basis:** Priority Gas Auctions (PGA) & Constant Product Formula ($x \times y = k$)

> "In the Mempool, there are no rules. Only incentives. It is a Dark Forest where silence is survival."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Flashboys 2.0](#2-the-theory-flashboys-2-0)
    * 2.1. MEV Definition: The extra value extracted by miners/validators.
    * 2.2. The Sandwich: Front-run $\to$ Victim $\to$ Back-run.
    * 2.3. Chain Saturation: Using MEV profitability as a macro signal.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Attack Rule: Identify Victim (Large Slippage), Calculate Optimal Input, Bribe Miner.
    * 3.2. Defense Rule (The Dodger): Use Private RPCs (Flashbots Protect).
    * 3.3. Macro Rule: If MEV Profit > 0.5 ETH/Block, Stop DeFi Trading (Toxic Environment).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Price Impact Formula ($P_{after}$).
    * 4.2. Optimal Front-run Amount ($x_{in}$).
    * 4.3. Sandwich Profit Equation.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. "Flash Boys 2.0" (Daian et al., 2019): The paper that started it all.
    * 5.2. The "Salmonella" Trap: A poisonous token that wrecked MEV bots.
    * 5.3. Jaredfromsubway.eth: The apex predator ($40M profit).
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Web3.py, Flashbots API, Mempool Statistics).
    * 6.2. Rust (Mempool Scanner, Bundle Constructor).
7. [Risk Management](#7-risk-management)
    * 7.1. Uncle Bandit Risk (Reorgs stealing your sandwich).
    * 7.2. Off-Chain Logic Trps (Honeypots).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 68** operates in the nanoseconds of the Ethereum block time.
It covers both the **Offense** (How to extract MEV) and the **Defense** (How to avoid being extracted).

* **Offense:** Identify a pending transaction with loose slippage parameters. Sandwich it. Limitless profit potential.
* **Defense:** MEV Profitability (Indicator 068) is a barometer for "Chain Stress". When MEV spikes, volatility is imminent.

**The Edge:**
This strategy is Zero-Sum. If you win, someone else loses (usually a retail trader or another bot). It requires the most advanced infrastructure in GOLIATH.

---

# 2. The Theory

## 2.1. Flashboys 2.0

Pre-2019, people thought crypto fees were just for confirmation.
Daian et al. revealed that bots were bidding up gas prices to execute primarily arbitrage and front-running strategies.
This evolved into **Proposer-Builder Separation (PBS)**:

* **Searchers:** Find the arb (That's us).
* **Builders:** Bundle the arbs.
* **Validators:** Propose the block.

## 2.2. The Sandwich Anatomy

1. **Victim:** Broadcasts "Buy 100 ETH of SHIB, Slippage 10%".
2. **Attacker:** Sees pending tx.
3. **Front-run:** Attacker Buys SHIB. Price goes up.
4. **Victim:** Victim Buys (at higher price). Price goes up more.
5. **Back-run:** Attacker Sells SHIB.
6. **Profit:** $P_{sell} - P_{buy} - Gas$ > 0.

## 2.3. Chain Saturation Signal (068)

High MEV Profitability = High inefficiencies.

* If average MEV per block > 0.5 ETH:
  * **Signal:** Extreme Volatility / Panic.
  * **Action:** Move to CEX (Binance) where MEV is impossible, or use Flashbots Protect.
  * **Why:** Trying to swap on Uniswap during MEV spikes is suicide. You will be sandwiched.

---

# 3. The Strategy Rules

## 3.1. Attack (The Bot)

* **Scan:** Mempool for Uniswap V2/V3 Router calls (`swapExactETHForTokens`).
* **Simulate:** `eth_call` to check if Victim Tx succeeds after our Front-Run.
* **Optimize:** Find max input amount that keeps Victim Slippage $\approx$ Limit.
* **Submit:** Send Bundle to Flashbots Relay.

## 3.2. Defense (The Trader)

* **Monitor:** Global MEV Stats.
* **Rule:** If you see large MEV liquidations pending (e.g. Aave Liquidation), **Front-run the CEX**.
  * On-chain liquidation $\to$ DEX Dump $\to$ CEX Dump.
  * Short the CEX immediately.

---

# 4. Mathematical Derivation

## 4.1. Constant Product

$$ (x_0 + \Delta x_{bot})(y_0 - \Delta y_{bot}) = k $$
New Price $P_1 = \frac{y_{new}}{x_{new}}$.

## 4.2. Victim Execution

Victim buys $\Delta x_v$.
Price moves to $P_2$.
Constraint: $P_2 \le P_{limit}$ (Victim's max price).

## 4.3. Optimization

Maximize:
$$ Profit = \Delta y_{backup} - \Delta x_{frontrun} - Gas $$
Subject to:
$$ P_{victim\_execution} \le P_{tolerance} $$

---

# 5. Historical Case Studies

## 5.1. Salmonella (The Trap)

Searchers blindly front-ran any buy order.
A dev created a token where `transfer()` took 10% fee if recipient was "Normal", but 100% fee if recipient was "Sandwich Bot".
Bots bought in, but couldn't sell out. They were drained.
**Lesson:** Simulation must be perfect.

## 5.2. Uncle Bandit

A miner saw a Searcher's profitable bundle in a block that got "Uncled" (Orphaned).
The miner copied the bundle and included it in their own valid block.
The Miner stole the MEV from the Searcher.
**Lesson:** The Validator is God.

---

# 6. Implementation: Production Grade

## 6.1. Python (Analysis & Stats)

```python
import requests
import pandas as pd

def check_mev_health():
    # Flashbots Data API
    url = "https://data.flashbots.net/api/v1/blocks?limit=50"
    data = requests.get(url).json()
    
    total_profit = 0
    for block in data['blocks']:
        total_profit += int(block['value']) # value usually in Wei
    
    avg_profit_eth = (total_profit / 50) / 10**18
    
    if avg_profit_eth > 0.5:
        return "RED_ALERT: MEV Spiking. Use Private RPCs."
    elif avg_profit_eth > 0.1:
        return "NORMAL: Standard activity."
    else:
        return "QUIET: Low volume."

def construct_bundle(victim_tx, buy_tx, sell_tx):
    return [
        {"tx": buy_tx, "canRevert": False},
        {"tx": victim_tx, "canRevert": False},
        {"tx": sell_tx, "canRevert": False}
    ]
```

## 6.2. Rust (Mempool Scanner)

```rust
use ethers::types::Transaction;

pub fn is_profitable_victim(tx: &Transaction) -> bool {
    // Decode input data (4 bytes selector)
    if &tx.input[0..4] == [0x7f, 0xf3, 0x6a, 0xb5] { // swapExactETHForTokens
        // Decode MinAmountOut
        // Calculate implied slippage
        // If slippage > 2%, return true
    }
    false
}
```

---

# 7. Risk Management

## 7.1. Bundle Rejection

If your bundle is not the most profitable, the Validator ignores it.
**Cost:** 0 Gas. (Flashbots feature).
Risk is Opportunity Cost & Latency computational burn.

## 7.2. "Toxic" Tokens (Honeypots)

Tokens that prevent selling (Squid Game Token).
If you sandwich a buy, you are stuck with the bag.
**Mitigation:** Static Analysis of ERC20 code before trading.

---

# 8. Conclusion

**Strategy 68** is the "Dark Mode" of GOLIATH.
It acknowledges the adversarial nature of public blockchains.
By understanding MEV, we:

1. **Extract Alpha:** Through Arbitrage and Sandwiching.
2. **Preserve Capital:** By monitoring Chain Saturation signals (068) to avoid trading during chaotic congestion.
It is the strategy of the Predator, ensuring GOLIATH is not the Prey.
