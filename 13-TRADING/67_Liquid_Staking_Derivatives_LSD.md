# 67 - Liquid Staking Derivatives (LSD): The Peg Trade

**Volume:** 67 of 100
**Strategy Type:** DeFi Arbitrage / Yield Overlay
**Risk Profile:** Smart Contract Risk / Peg Decoupling / Slashing Risk
**Mathematical Basis:** Discounted Cash Flow of Locked Collateral

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Staking Derivatives](#2-the-theory-staking-derivatives)
    * 2.1. The Problem: Staking ETH yields 4%, but locks capital.
    * 2.2. The Solution: Lido (stETH) and Rocket Pool (rETH). Receipt tokens that trade freely.
    * 2.3. The Peg: 1 stETH should equal 1 ETH. In reality, it floats.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Discount Buy: When stETH < 0.99 ETH, Buy stETH.
    * 3.2. Premium Sell: When stETH > 1.00 ETH, Sell stETH for ETH.
    * 3.3. Leveraged Staking: Loop (Supply stETH, Borrow ETH, Buy stETH). Repeat.
    * 3.4. Execution: Curve Finance, Balancer, Uniswap.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Fair Value: $FV = Spot_{ETH} + Yield_{staking} - Cost_{liquidity}$.
    * 4.2. Looping APY: $APY_{net} = \frac{Y_{staked} - (R_{borrow} \times LTV)}{1 - LTV}$.
    * 4.3. Discount Factor: $D = e^{-rt}$.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Celsius Collapse (June 2022): stETH depegged to 0.93 ETH. Massive liquidation cascade of leveraged stakers.
    * 5.2. The Merge (Sept 2022): Successful upgrade. Peg restored to 0.999.
    * 5.3. Shapella Upgrade (April 2023): Withdrawals enabled. The peg became hard-arbable (users could redeem 1:1).
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Monitoring Curve Pool Balances (Imbalance Ratio).
    * 6.2. Calculating "Break-Even Peg".
    * 6.3. Executing Swaps via 1inch Aggregator API.
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. rETH (Rocket Pool): Decentralized alternative. Often trades at premium due to tax efficiency.
    * 7.2. LST-fi: Eiglenlayer Restaking. Using stETH to secure data availability layers.
    * 7.3. "Pendle Finance": Stripping Yield (YT) and Principal (PT). Fixed Rate ETH.
8. [Risk Management: The Slashing Event](#8-risk-management-the-slashing-event)
    * 8.1. Slashing: If Lido validators misbehave, the ETH is burned. stETH value drops permanently.
    * 8.2. Smart Contract Bug: Lido contract hack = $0.
    * 8.3. Infinite Loop Liquidation: If ETH drops, borrowing rates spike.
9. [Conclusion: The New Risk-Free Rate](#9-conclusion-the-new-risk-free-rate)

---

# 1. Executive Summary

**Liquid Staking Derivatives (LSDs)** turn staked assets into tradable commodities.
Strategies revolve around the **peg** between the derivative and the underlying.
Historically, stETH traded at a discount (0.95-0.99).
Investors who bought the discount earned the staking yield + the appreciation to 1.00.
Today, with withdrawals enabled, the arb is tighter, but "Restaking" (Eigenlayer) introduces new layers of yield and risk.

---

# 2. The Theory

### 2.1. Why locking capital is expensive

Opportunity cost.
During a crash, you can't sell locked ETH.
LSDs solve this liquidity premium.
However, the market demands a discount for the *risk* of the derivative layer.

### 2.2. The Mechanism

Deposit 1 ETH into Lido -> Receive 1 stETH.
stETH rebases daily (balance increases by staking rewards).
You can sell stETH on Curve for ETH instantly.
OR wait for withdrawal queue (1-4 days) to redeem 1:1.

---

# 3. Strategy Rules

### 3.1. The Discount Arb

If stETH trades at 0.98 ETH:
Buy 100 stETH for 98 ETH.
Request Withdrawal from Lido.
Wait 4 days.
Receive 100 ETH.
Profit: 2 ETH (2%) in 4 days.
Annualized Return: Massive.

### 3.2. Leveraged Looping

Supply stETH on AAVE (Collateral).
Borrow ETH (Debt).
Swap Borrowed ETH -> stETH.
Resupply.
Repeat 3x.
Result: 3x Staking Yield (12%) - Borrow Cost (2%).
Net APY: 10% on ETH.
Risk: Liquidation if Peg breaks.

---

# 4. Mathematical Derivation

$$ APY_{Loop} = \frac{Y_{supply} \times L - R_{borrow} \times (L-1)}{1} $$

Where $L$ is Leverage Factor (e.g. 3.0).
If $Y_{steth} = 4\%$, $R_{eth} = 2\%$.
$APY = 4 \times 3 - 2 \times 2 = 12 - 4 = 8\%$.
Base Yield is doubled.

---

# 5. Historical Case Studies

### 5.1. The 3AC Blowup

Three Arrows Capital was leveraged long stETH.
When Luna collapsed, they had to sell stETH to cover margin.
They dumped into Curve pool.
stETH/ETH price crashed to 0.93.
Retail panicked.
Arb traders bought at 0.93 and held until the Merge.

### 5.2. AAVE Risk Param Update

AAVE froze stETH borrowing to prevent "Recursive Lending Risks".
Rates spiked. Loopers got trapped.

---

# 6. Python Implementation

```python
from web3 import Web3

def monitor_peg(w3):
    # Curve stETH/ETH Pool Address
    pool_address = "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022"
    abi = [...] 
    
    contract = w3.eth.contract(address=pool_address, abi=abi)
    
    # get_dy(i, j, dx)
    # i=1 (stETH), j=0 (ETH)
    amount_in = w3.to_wei(1, 'ether')
    amount_out = contract.functions.get_dy(1, 0, amount_in).call()
    
    price = w3.from_wei(amount_out, 'ether')
    
    print(f"1 stETH = {price:.4f} ETH")
    
    if price < 0.995:
        return "BUY_DISCOUNT"
    if price > 1.005: 
        return "SELL_PREMIUM" (Rare)
        
    return "HOLD"
```

### 6.2. Flash Loan Arbitrage

If price < 0.99, use Flash Loan to buy stETH, queue withdrawal?
No, withdrawal takes days. Flash loan must be repaid in 1 block.
Only works if you sell on another DEX.

---

# 7. Optimization

### 7.1. Pendle Finance (Yield Stripping)

Sell the Yield (YT) upfront for Cash.
Buy the Principal (PT) at a discount.
Lock in Fixed Rate ETH (e.g. 5% fixed).
Removes "Variable Yield Risk".

### 7.2. Eigenlayer

Re-stake stETH.
Secure new networks (AVS).
Earn AVS Yield + Staking Yield.
Risk: Slashing conditions of the AVS.

---

# 8. Risk Management

### 8.1. Smart Contract Risks

Lido has \$30 Billion TVL.
It is the biggest "Honeypot" in crypto.
A bug would be catastrophic for the entire ecosystem.
Diversify: Use Rocket Pool (rETH) and Frax (sfrxETH).

### 8.2. Regulation

SEC considers Staking a security?
If Lido is banned, UI shuts down.
Contract is decentralized, but liquidity might dry up.

---

# 9. Conclusion

LSD arbitrage is the "Bond Market" of Ethereum.
It sets the Risk-Free Rate for the internet.
For GOLIATH, we hold 80% of ETH inventory as stETH.
We dynamic hedge the delta.
We capture the spread.
It is the strategy of the Validator.
