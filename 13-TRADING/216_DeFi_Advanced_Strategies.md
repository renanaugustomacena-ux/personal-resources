# 216 — Advanced DeFi Strategies

> Concentrated liquidity, options vaults, structured yield, lending arbitrage, restaking, MEV, cross-chain bridges. Covers Uniswap V3 LP optimization, Pendle yield tokenization, EigenLayer restaking, options on DEX, flash loans, liquidations, real-yield protocols. Self-contained beyond document 209.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Uniswap V2 vs V3 Mechanics](#uniswap)
3. [V3 Math — Sqrt Price, Ticks](#v3-math)
4. [LP Returns Under V3](#v3-returns)
5. [Impermanent Loss](#impermanent-loss)
6. [Concentrated Liquidity Strategy](#cl-strategy)
7. [JIT Liquidity](#jit)
8. [Curve V1/V2](#curve)
9. [Balancer](#balancer)
10. [DODO PMM](#dodo)
11. [AMMs as Options](#amm-options)
12. [Ribbon/Aevo Vaults](#ribbon-aevo)
13. [Dopex](#dopex)
14. [Lyra, Premia](#lyra-premia)
15. [Squeeth Power Perpetual](#squeeth)
16. [Pendle](#pendle)
17. [Pendle PT-YT Pricing](#pt-yt-pricing)
18. [Yield Aggregators (Yearn-style)](#aggregators)
19. [Aave/Compound Lending](#lending)
20. [Aave E-Mode and Isolation](#aave-modes)
21. [Lending Rate Arbitrage](#lending-arb)
22. [Flash Loans](#flash-loans)
23. [Liquidation Strategies](#liquidations)
24. [MEV in Lending](#mev-lending)
25. [Stablecoins Overview](#stablecoins)
26. [DAI Mechanics](#dai)
27. [Curve Stable Arb](#curve-arb)
28. [EigenLayer Restaking](#eigenlayer)
29. [Liquid Restaking Tokens (LRTs)](#lrt)
30. [Real-Yield Protocols](#real-yield)
31. [Cross-Chain Bridges](#bridges)
32. [DEX-CEX MEV Arbitrage](#cex-mev)
33. [Smart Contract Risk and Post-Mortems](#sc-risk)
34. [Code Examples](#code)
35. [Reality Checks](#reality-checks)
36. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

DeFi is the decentralized counterpart to traditional finance. Total Value Locked (TVL) reached $200B in 2021, retreated to $40B in 2022-2023, and recovered to $100B+ by late 2024. Major protocols:

- **DEXes**: Uniswap, Curve, Balancer ($20-50B TVL).
- **Lending**: Aave, Compound, Morpho ($15-30B TVL).
- **Liquid staking**: Lido, Rocket Pool ($30-50B TVL).
- **Restaking**: EigenLayer ecosystem ($15-25B TVL).
- **Stablecoins**: USDC, USDT, DAI on-chain ($150B+ supply).
- **Options/structured**: Aevo, Lyra, Pendle ($1-5B TVL).

Strategies span:
- **Liquidity provision**: V3 LP, Curve LP, Balancer LP.
- **Yield aggregation**: Yearn-style auto-compound.
- **Lending arbitrage**: rate arbitrage across protocols.
- **MEV**: liquidations, JIT, sandwich (controversial).
- **Restaking**: stack yields across AVSs.
- **Cross-protocol**: novel structures (Pendle PT-YT, Squeeth).

This document covers the math, mechanics, and trading strategies. Document 209 covers crypto derivatives broadly; here we focus on DeFi-specific protocols.

---

## Uniswap V2 vs V3 Mechanics

### V2: Constant Product

x × y = k. For pool with reserves (x, y) and k constant:
- Swap dx of X for dy of Y: dy = y - k/(x + dx).
- Price = y/x; price moves continuously with reserves.

### V3: Concentrated Liquidity

LPs concentrate liquidity into specific price ranges [P_a, P_b]. Within range, behaves like V2 with virtual reserves. Outside range, no liquidity provision (no fees earned, no IL).

Capital efficiency: 100-1000× more efficient than V2 if priced correctly.

---

## V3 Math — Sqrt Price, Ticks

V3 uses sqrt(P) = √(y/x) as price representation.

### Liquidity L

For range [P_a, P_b] with sqrt prices √P_a, √P_b:

$$
L = \frac{x \cdot \sqrt P_a \cdot \sqrt P_b}{\sqrt P_b - \sqrt P_a} = \frac{y}{\sqrt P_b - \sqrt P_a}.
$$

### Tokens at Current Price P

For sqrt P in [√P_a, √P_b]:

$$
x = L \!\left( \frac{1}{\sqrt P} - \frac{1}{\sqrt P_b} \right),
$$
$$
y = L (\sqrt P - \sqrt P_a).
$$

### Ticks

Discrete price levels at 1.0001^i for integer i. Each tick spacing: 0.01% price difference.

### Q64.96 Fixed-Point

V3 uses 64.96 fixed-point for sqrt prices. Avoids floating-point issues.

```python
import numpy as np

def liquidity_from_x(x, sqrtP_a, sqrtP_b):
    return x * sqrtP_a * sqrtP_b / (sqrtP_b - sqrtP_a)

def liquidity_from_y(y, sqrtP_a, sqrtP_b):
    return y / (sqrtP_b - sqrtP_a)

def tokens_at_price(L, sqrtP, sqrtP_a, sqrtP_b):
    if sqrtP <= sqrtP_a:
        return L * (1/sqrtP_a - 1/sqrtP_b), 0
    elif sqrtP >= sqrtP_b:
        return 0, L * (sqrtP_b - sqrtP_a)
    else:
        return L * (1/sqrtP - 1/sqrtP_b), L * (sqrtP - sqrtP_a)
```

---

## LP Returns Under V3

LP earns:
- **Trading fees**: pro-rata share of fees in their range.
- **Negative IL**: when price moves through range.

### Fees vs IL

If price stays in range, fees earned each swap. If price exits range, position becomes 100% one token (fully impermanent-loss exposed at exit).

For optimal range:
- **Tight range**: high fees per dollar but high IL when price moves.
- **Wide range**: lower fees but less IL.

### Empirical

For ETH/USDC at 1% fee tier:
- Tight range (±1%): high fees, ~30-50% IL when ETH moves >5%.
- Medium range (±10%): moderate fees, ~10-15% IL.
- Wide range (±50%): low fees (similar to V2), ~3-5% IL.

---

## Impermanent Loss

For V2: IL = (2√r) / (1 + r) - 1, where r = price ratio.

### Derivation

LP holds (x, y) with x*y = k. After price ratio change:
- LP value: 2√(xy × P_new × P_old) (stays balanced).
- HODL value: x*P_old + y*P_old × r.

Compute ratio.

### V3 IL

More complex. Within range, similar to V2 with virtual reserves.

```python
def il_v2(price_ratio):
    """V2 impermanent loss as fraction of HODL."""
    return 2*np.sqrt(price_ratio)/(1 + price_ratio) - 1

# Examples
for r in [1.5, 2, 3, 5, 10]:
    il = il_v2(r)
    print(f"Price ratio {r}: IL = {il*100:.2f}%")
```

### Tail-Risk Hedging

LP is short volatility. Can hedge by buying options (strangles, OTM puts/calls). Cost typically ~30-50% of fees earned.

---

## Concentrated Liquidity Strategy

### Passive

Set wide range, leave alone. Low management overhead. Lower fees but stable.

### Active

Rebalance ranges as price moves:
- Recenter when price exits ±X% of current.
- Multiple range orders (V3 can manage multiple positions).

### Optimal Range

Trade-off between fees and IL. Optimal range depends on:
- Volatility regime.
- Fee tier (5bp, 30bp, 1%).
- Gas costs of rebalancing.
- Hedging strategy.

### Production

Automated managers:
- **Gamma Strategies, Arrakis, Kamino**: managed V3 LP positions.
- **Charm Finance**: hedged LP.

Charge 10-20% performance fee for management.

---

## JIT Liquidity

Just-In-Time liquidity:
1. Bot detects large incoming swap in mempool.
2. Adds tight liquidity right at expected price (in same block).
3. Earns fees for the swap.
4. Removes liquidity right after.

### Profitability

JIT bots earn most of the swap's fees, leaving little for permanent LPs. Controversial — accused of MEV extraction.

### Defense

Some pools restrict via timelock or block-level restrictions. Efficacy varies.

---

## Curve V1/V2

### Curve V1 (StableSwap)

Hybrid of constant-sum and constant-product:

$$
A \cdot n^n \cdot \sum x_i + D = A \cdot D \cdot n^n + D^{n+1} / (n^n \prod x_i),
$$

where A is amplification coefficient. For stablecoins, A ~100-1000 makes pool nearly constant-sum (low slippage near peg).

### Curve V2

For volatile pairs (ETH-BTC, ETH-USDC, etc.). More complex invariant adapts to price ratio.

### LP Returns

- Pool fees (typically 4-10bps).
- CRV emissions (for boosted pools).
- veCRV voting power.

### Reality Check — Curve LP Risk

Stableswap pools mostly safe. Volatile-pair pools (Curve V2) have IL similar to Uniswap V3 wide-range.

---

## Balancer

Generalized AMM with weighted pools:
- 80/20 (e.g., 80% stETH, 20% ETH).
- 60/20/20 (multi-asset).
- Liquidity Bootstrapping Pools (LBPs) for token launches.

Different weights → different price impacts and IL profiles.

---

## DODO PMM

Proactive Market Maker: external oracle price feed, AMM adjusts quote based on inventory.

Different from Uniswap: less suited to permissionless LP, more suited to professional MMs.

---

## AMMs as Options

LP positions decompose mathematically:
- V2 LP = Long sqrt(P) - Short P.
- This is short straddle + half-hedge (Tassy/Angeris work).

### Trading

LP profits when realized vol < implied vol embedded in fees:
- LP fees per unit time = vol-related.
- IL per move = vol²-related.
- Profitable LP requires fees > IL cost.

---

## Ribbon/Aevo Vaults

Aevo (formerly Ribbon Finance):
- Covered call vaults.
- Put-selling vaults.
- Iron condor vaults.
- Settled weekly via Deribit options.

### Mechanics

1. Vault holds spot ETH.
2. Sells weekly OTM call option on Deribit.
3. Premium distributed to depositors.
4. If call expires ITM: ETH delivered (capping upside).

### Yields

- Calm periods: 10-25% APY.
- Crashes: vault loses spot but premium offsets.
- Fat-tailed: occasional large losses (March 2020, May 2021).

---

## Dopex

Atlantic options: novel mechanism allowing strike updates during life. Insurance-like products.

Less liquid than Aevo; niche.

---

## Lyra, Premia

### Lyra

AMM-based options. Fully on-chain pricing via Black-Scholes with on-chain IV. LPs are option counterparties.

Mechanism:
- Pool of LP capital backstops options.
- Protocol hedges delta via Synthetix perps.

### Premia

Pool-based options. LPs deposit one side; users buy options.

Multi-chain (Arbitrum, Optimism, others).

### Reality Check — DEX Options Liquidity

Combined Lyra + Premia volume: ~1% of Deribit. Efficient pricing requires CEX-like liquidity which DEXes don't yet have.

---

## Squeeth Power Perpetual

Squeeth (Opyn): perpetual on ETH^2.

Mathematically equivalent to a continuously-rebalanced variance swap.

### Mechanics

- Squeeth tracks: oS = c × ETH^2.
- Funding rate: cost of carrying gamma exposure.
- Long Squeeth: positive convexity, pays funding.
- Short Squeeth: receives funding, sells convexity.

### Use Cases

- Long volatility hedge.
- Replicating exotic option exposure.
- Vol-of-vol trades.

---

## Pendle

Yield tokenization protocol.

### Decomposition

For yield-bearing asset (e.g., stETH):
- **PT (Principal Token)**: redeems for 1 stETH at expiry.
- **YT (Yield Token)**: receives yield until expiry.

Sum of PT + YT = stETH always.

### PT Pricing

PT trades at discount: $PT = 1 / (1 + y_t \cdot T)$.

The implied yield-to-maturity is the "fixed rate" lockable by buying PT and holding.

### YT Pricing

YT pricing is more volatile. Trades like a perpetual claim on yield. Price depends on:
- Expected future yield path.
- Time-to-expiry decay.
- Yield volatility.

### Pendle V2

Improvements over V1:
- AMM specifically designed for PT-YT (different than Uniswap).
- Better price discovery.
- Multiple maturities per asset.

---

## Pendle PT-YT Pricing

### Implied Yield from PT

For PT-stETH at $0.95, 90 days to expiry:

$$
\text{YTM} = \frac{1 - 0.95}{0.95} \times \frac{365}{90} = 21.3\%.
$$

If actual stETH yield expected to be ~4%, market is pricing higher yield than current. Possibly overshooting.

### YT Trading

YT is highly volatile. Pricing like a perpetual claim:

$$
P_{YT} \approx \int_0^T y_s e^{-rs} ds.
$$

For declining yield (mean reversion), YT trades at discount to face. For rising yield, premium.

### Strategy

- **Buy PT at discount**: lock fixed yield.
- **Buy YT at discount**: leverage yield exposure (small price, full yield until expiry).
- **Sell YT**: harvest yield, give up future variability.
- **PT-YT pair trades**: anticipate yield curve changes.

---

## Yield Aggregators (Yearn-Style)

### Yearn Finance

Auto-compound vault: deposits in best-yielding strategy. Strategies include:
- Curve LP + boosted CRV claim.
- Convex Finance (boosted Curve).
- Other yield sources.

### Tokenized Strategies

Yearn vaults are tokenized: vault token represents share. Compounded yield accrues to token value.

### Risk

- Smart contract risk.
- Strategy risk (LP, lending, etc.).
- Governance risk.

---

## Aave/Compound Lending

### Mechanics

Suppliers deposit; borrowers borrow against collateral. Interest accrues continuously.

### Rates

Both supply and borrow rates depend on utilization (borrowed / supplied).

Kink model:

$$
r_{\text{borrow}}(U) = r_0 + \text{slope}_1 \cdot U \quad \text{for } U < U^*.
$$
$$
r_{\text{borrow}}(U) = r_0 + \text{slope}_1 \cdot U^* + \text{slope}_2 \cdot (U - U^*) \quad \text{for } U \ge U^*.
$$

Steep slope above kink (U* ≈ 80%) prevents excessive utilization.

### LTV (Loan-to-Value)

Each asset has max LTV (e.g., ETH 80%, USDC 75%). Borrowing limit = collateral × LTV.

### Liquidation Threshold

Higher than LTV. When collateral drops below threshold, position liquidatable.

```python
def aave_borrow_rate(util, base=0.01, slope1=0.04, kink=0.8, slope2=0.5):
    if util < kink:
        return base + slope1 * util
    return base + slope1 * kink + slope2 * (util - kink)

# Example: ETH market at 70% utilization
print(f"Borrow rate at 70%: {aave_borrow_rate(0.7)*100:.2f}%")
print(f"Borrow rate at 90%: {aave_borrow_rate(0.9)*100:.2f}%")
```

---

## Aave E-Mode and Isolation

### Isolation Mode

Some assets only allowed as collateral in isolation: cannot pair with other assets. Limits risk to that asset's pool.

### E-Mode (Efficiency Mode)

Correlated assets (e.g., ETH + stETH + rETH) can be paired with high LTV (90%+). Higher capital efficiency.

### Use

- E-mode for stETH-ETH leverage (5-10× yield amplification).
- Isolation for new asset listings.

---

## Lending Rate Arbitrage

### Cross-Protocol

Aave USDC borrow at 5%; Compound USDC supply at 3%. Borrow Aave, supply Compound, earn -2% (negative).

Other direction: Compound borrow 4%, Aave supply 6%. Borrow Compound, supply Aave, earn 2%.

### Reality Check — Rate Arb Costs

- Gas costs.
- Borrow risk premium (collateral required).
- Rate movements (rates change continuously).
- Protocol risk (one might fail).

Net profit usually small after costs; high-frequency execution essential.

---

## Flash Loans

Borrow-without-collateral if repaid in same transaction.

### Mechanics

```solidity
function flashloan(address asset, uint256 amount) external {
    // 1. Receive amount of asset.
    // 2. Do something (arbitrage, etc.).
    // 3. Repay amount + fee.
    // If repayment fails, transaction reverts.
}
```

### Use Cases

- **Arbitrage**: balance pools, exploit cross-protocol mispricings.
- **Liquidations**: borrow to liquidate underwater position.
- **Collateral swaps**: change collateral type without unwinding.
- **Refinancing**: move debt between protocols.

### Famous Flash Loan Attacks

- 2020 bZx: $350K via flash loan + oracle manipulation.
- 2022 Beanstalk: $182M governance attack.
- 2023 Yearn: ~$11M.

Flash loans amplify oracle and governance risks.

---

## Liquidation Strategies

When borrower's LTV exceeds threshold, position becomes liquidatable.

### Mechanics

1. Liquidator detects underwater position.
2. Repays portion of debt (e.g., up to 50%).
3. Receives collateral with bonus (e.g., 5-10%).

### Profitability

For $100K underwater position with 5% bonus:
- Liquidator pays ~$50K of debt.
- Receives ~$52.5K of collateral.
- Profit: ~$2.5K minus gas + slippage.

### Keepers

Specialized bots monitor positions:
- Subscribe to oracle updates.
- Compute LTVs in real-time.
- Trigger liquidation transactions.

Highly competitive; multiple bots compete for same liquidations.

### MEV in Liquidations

Liquidations are profitable; bots fight for them via gas auctions or flashbots bundles.

```python
def liquidation_pnl(debt_repaid, collateral_received, bonus_rate, gas_cost):
    pnl = collateral_received - debt_repaid - gas_cost
    return pnl

# Example
print(liquidation_pnl(50000, 52500, 0.05, 100))  # $2400 profit
```

---

## MEV in Lending

### Liquidation Frontrunning

Bot sees pending liquidation; attempts to be first. Solution:
- Higher gas (gas auctions).
- Flashbots bundles (private mempool).

### Sandwich Attacks (Less Common in Lending)

Less common than DEX sandwiches because rate updates are continuous and not batchable.

### MEV-Resistant Protocols

- Cowswap-style batch matching.
- Threshold encryption (mempool privacy).

---

## Stablecoins Overview

### Fiat-Backed (USDC, USDT)

Centralized issuers hold dollar reserves; tokens redeemable 1:1.

- USDC (Circle): well-regulated, audited.
- USDT (Tether): less transparent, larger.

### Crypto-Backed (DAI)

MakerDAO: vaults hold ETH/other; mint DAI against collateral. Over-collateralized (~150% LTV).

### Algorithmic (FRAX, sUSD, deprecated UST)

- FRAX: hybrid (partial collateral + algorithmic).
- sUSD: synthetix-collateralized.
- UST: collapsed May 2022 (death spiral).

---

## DAI Mechanics

### Vaults (formerly CDPs)

User deposits ETH (or other allowed collateral); mints DAI up to allowed LTV.

### Stability Fee

Interest on DAI debt. Adjusted by governance to manage peg.

### Peg Maintenance

DAI peg held by:
- **Stability fee**: high SF discourages borrowing.
- **DSR (Dai Savings Rate)**: pays DAI holders.
- **PSM (Peg Stability Module)**: 1:1 swaps with USDC.

### MakerDAO Governance

MKR token holders vote on parameters. Real-yield generated returns to MKR via burns or buybacks.

---

## Curve Stable Arb

### 3pool, basepools

Curve 3pool: USDT + USDC + DAI in one pool. Stableswap invariant for low slippage.

### Arbitrage

Small premiums/discounts between stablecoins:
- USDC at 0.998: arbitrage by buying USDC, selling USDT in 3pool.
- High-frequency keepers maintain peg.

### Metapools

A "meta" pool combines 3pool with another stablecoin (e.g., FRAX-3pool). Lower friction for new stablecoins.

---

## EigenLayer Restaking

### Concept

ETH validators "restake" their ETH (or LSTs) to provide security to additional services (AVSs).

Each restaked ETH:
- Continues earning ETH staking yield (~4%).
- Earns additional yield from AVSs (~1-5%).

### Mechanics

- Validators delegate to operators.
- Operators run AVS software.
- Slashing risk: misbehave on AVS, lose ETH.

### TVL

EigenLayer TVL: $15-25B, mostly in restaked ETH or LSTs.

---

## Liquid Restaking Tokens (LRTs)

Tokenize restaked positions:
- **Renzo** (ezETH): Restake ETH/LSTs through partner operators.
- **Ether.fi** (eETH): native restaking.
- **Puffer** (pufETH): novel slashing mitigation.
- **Kelp** (rsETH): basket of LSTs.

LRTs trade on DEXes:
- Liquid (don't need to wait for unstaking).
- Compound yields stack.
- LRT-ETH spread reflects liquidity premium / risk.

---

## Real-Yield Protocols

Protocols where fees flow to LPs/stakers:
- **GMX**: trading fees → GLP holders + esGMX.
- **GNS (Gains Network)**: similar.
- **Synthetix V3**: fees → LPs.
- **Pendle**: fees → ePENDLE.
- **Frax**: protocol revenue → veFXS.

### Trading

Stake/lock for veToken; earn share of fees. Higher than emissions-based yields.

---

## Cross-Chain Bridges

### Types

- **Lock-and-mint**: lock asset on chain A; mint wrapped on chain B.
- **Burn-and-mint**: native cross-chain (LayerZero, Wormhole).
- **Atomic swaps**: time-locked exchange (less common).

### Major Bridges

- **Wormhole**: many chains; $400M hack 2022 recovered.
- **LayerZero**: cross-chain messaging; many integrations.
- **Native bridges** (Optimism, Arbitrum, Base): canonical chain-specific.

### Arbitrage

Asset prices differ across chains:
- Wrapped ETH on Arbitrum vs native ETH.
- Bridge fees, time delays create opportunity.

Sophisticated arb requires:
- Multiple wallet management.
- Cross-chain quoting.
- Bridge transit time modeling.

### Reality Check — Bridge Risk

- $2B+ stolen from bridges 2022-2023.
- Wormhole, Ronin, Nomad, Multichain hacks.
- Bridges are systemic risk for ecosystem.

---

## DEX-CEX MEV Arbitrage

### Atomic Bundles

Profit from CEX vs DEX price differences using flashbots:
- Buy on cheap venue (CEX or DEX).
- Sell on expensive venue.
- Bundle into one transaction (atomicity).

Profitability requires CEX inventory + DEX router access.

### Cowswap

Batch auction matching:
- Users submit orders.
- Solvers find matching prices off-chain.
- Settle on-chain in batch.

Reduces sandwich attacks; protects users from MEV.

---

## Smart Contract Risk and Post-Mortems

### Major Failures

- **Curve Vyper July 2023**: compiler bug allowed reentrancy. ~$70M lost.
- **Mango Markets October 2022**: oracle manipulation. $114M.
- **Compound BAT**: minting bug. Reverted by governance.
- **Wormhole Feb 2022**: signature verification bug. $326M (recovered).
- **Nomad Aug 2022**: bridge replay. $190M.

### Patterns

Common bug categories:
- Reentrancy (despite checks-effects-interactions).
- Oracle manipulation (especially TWAP-vulnerable assets).
- Compiler bugs (rare but devastating).
- Governance attacks.
- Cross-chain message replay.

### Defense

- Audit by reputable firms (Trail of Bits, OpenZeppelin, ConsenSys).
- Bug bounty programs.
- Time delays on governance.
- Multi-sig + time-lock controls.
- Insurance (Nexus Mutual, others).

### Reality Check — Smart Contract Risk Always Present

Smart contracts are immutable; bugs persist forever. Even audited contracts have failures. Diversify across protocols.

---

## Code Examples

### V3 LP Optimization

```python
import numpy as np

def v3_il(price_ratio, range_lower, range_upper):
    """V3 IL within a range."""
    sqrt_r = np.sqrt(price_ratio)
    sqrt_a = np.sqrt(range_lower)
    sqrt_b = np.sqrt(range_upper)
    if sqrt_r < sqrt_a:
        return None  # Out of range
    if sqrt_r > sqrt_b:
        return None  # Out of range
    # Within range: similar to V2 but with virtual reserves
    # ... (full math omitted)
    return 0  # placeholder

def optimal_v3_range(volatility_30d, fee_tier, time_horizon=30):
    """Find optimal V3 range given volatility."""
    # Heuristic: range = ±k σ √T where k is calibrated
    sigma = volatility_30d
    T = time_horizon / 365
    k = 1.5  # empirically tuned
    range_pct = k * sigma * np.sqrt(T)
    return -range_pct, range_pct  # in log price terms
```

### Pendle PT Yield Calculator

```python
def pt_yield(pt_price, days_to_expiry):
    """Implied annualized yield from PT price."""
    return (1/pt_price - 1) * 365 / days_to_expiry

# PT-stETH at 0.95, 90 days
print(f"Implied yield: {pt_yield(0.95, 90)*100:.2f}%")
```

### Liquidation Bot Skeleton

```python
import time

class LiquidationBot:
    def __init__(self, lending_protocol, oracle):
        self.protocol = lending_protocol
        self.oracle = oracle
    
    def scan(self):
        positions = self.protocol.get_positions()
        for pos in positions:
            ltv = pos.debt / (pos.collateral_value)
            if ltv > pos.liquidation_threshold:
                self.attempt_liquidation(pos)
    
    def attempt_liquidation(self, pos):
        # Estimate profit
        bonus_pct = pos.liquidation_bonus
        gas_cost = self.estimate_gas()
        repay = min(pos.debt * 0.5, self.balance * 0.5)
        collateral_received = repay * (1 + bonus_pct)
        profit = collateral_received - repay - gas_cost
        if profit > 0:
            self.protocol.liquidate(pos, repay)
```

---

## Reality Checks

- **Smart contract risk persists** across all protocols.
- **MEV extraction** affects strategy returns.
- **Gas costs** can dwarf strategy alpha.
- **Regulatory uncertainty** across jurisdictions.
- **Protocol governance risk**: malicious votes can change rules.
- **Bridge risk**: cross-chain assets carry additional risk.

---

## Reference Tables, Cheat Sheets, Bibliography

### Major Protocols

| Protocol | Type | TVL | Notes |
|---|---|---|---|
| Lido | Liquid staking | $30B+ | stETH dominant |
| EigenLayer | Restaking | $15-25B | New paradigm |
| Aave | Lending | $15B | Multi-chain |
| Uniswap V3 | DEX | $4B | Concentrated liquidity |
| Curve | DEX | $3B | Stableswap |
| Pendle | Yield | $3-5B | PT-YT split |
| Maker | Stablecoin | $5-10B | DAI |

### Bibliography

- **Uniswap V3 Whitepaper**.
- **Pendle Whitepaper**.
- **EigenLayer Whitepaper**.
- **Squeeth Whitepaper** (Opyn).
- **GMX Documentation**.
- **Daian, P. et al. (2019), "Flash Boys 2.0", USENIX**. MEV.
- **Angeris, G. and Chitra, T. (2020), "Improved Price Oracles: Constant Function Market Makers", AFT**. AMM math.
- **Tassy, M. et al. — papers on AMM as options**.

### Cross-References

- Document 209 — Crypto Derivatives.
- Document 49 — DeFi Liquidity AMM.
- Document 67 — Liquid Staking Derivatives.
- Document 68 — MEV Sandwich Attacks.
- Document 69 — Uniswap V3 Liquidity Math.
- Document 70 — Cross-Chain Bridge Arb.

---

*End of document 216. ~1,400 lines.*
