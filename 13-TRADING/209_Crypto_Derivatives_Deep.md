# 209 — Crypto Derivatives Deep Dive

> Comprehensive treatment of crypto derivatives markets — perpetual swaps, options, structured products, decentralized perps, MEV considerations. Covers funding rate mechanics, mark/index pricing, liquidation engines, options markets (Deribit, Lyra, Aevo), structured yield (Pendle), DEX perp architectures (dYdX, GMX, Synthetix v3, Hyperliquid), and quantitative trading strategies. Self-contained beyond document 200.

---

## Table of Contents

1. [Introduction — The Crypto Derivatives Stack](#introduction)
2. [Spot vs Perpetual vs Futures](#spot-vs-perp)
3. [Perpetual Swap Mechanics](#perp-mechanics)
4. [Funding Rate Computation](#funding-rate)
5. [Mark Price and Index Price](#mark-price)
6. [Liquidation Engines](#liquidations)
7. [Cross vs Isolated Margin](#margin-modes)
8. [Funding Rate Arbitrage and Basis Trades](#basis-trades)
9. [Cash-and-Carry Strategies](#cash-and-carry)
10. [Crypto Options Markets](#options-markets)
11. [BTC/ETH Option Pricing](#option-pricing)
12. [Crypto Vol Surface](#vol-surface)
13. [DVOL Index](#dvol)
14. [Variance and Volatility Swaps](#variance-swaps)
15. [Structured Products — Vaults](#structured-vaults)
16. [Pendle Yield Tokenization](#pendle)
17. [Decentralized Perps — dYdX](#dydx)
18. [GMX-Style Models](#gmx)
19. [Synthetix v3](#synthetix)
20. [Hyperliquid](#hyperliquid)
21. [Power Perpetuals (Squeeth)](#squeeth)
22. [MEV in Derivatives](#mev)
23. [Order Book DEXes](#orderbook-dex)
24. [AMM-Based Perps (vAMM)](#vamm)
25. [Options on DEX (Lyra)](#lyra)
26. [Stablecoin Derivatives](#stablecoin)
27. [Token Unlock Arbitrage](#unlock-arb)
28. [Validator Yield Products](#validator-yield)
29. [Crypto-Equity Correlation Trades](#crypto-equity)
30. [Risk Management for Crypto Books](#risk-management)
31. [Code Examples](#code)
32. [Reality Checks](#reality-checks)
33. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction — The Crypto Derivatives Stack

Crypto derivatives are the largest segment of crypto trading volume. Daily notional in BTC perpetuals alone exceeds spot BTC volume by 3-5×. Total crypto derivatives volume across CEXes (Binance, OKX, Bybit, Coinbase, Kraken) regularly exceeds $2-5 trillion per day. DEX perpetual volume (dYdX, GMX, Hyperliquid, Synthetix) is smaller but growing rapidly — reached $200-500 billion daily in late 2024.

The ecosystem decomposes into:

- **Centralized Exchanges (CEXes)**: dominant by volume. Binance, OKX, Bybit have largest perp markets. Deribit dominates options. Coinbase, Kraken serve US users.
- **Decentralized Exchanges (DEXes)**: Hyperliquid, dYdX (V4 Cosmos), GMX (Arbitrum), Synthetix V3 (multi-chain).
- **Structured products**: Aevo (formerly Ribbon), Lyra, Premia, Pendle.
- **OTC desks**: Cumberland, Galaxy, BlockFills — large institutional flow.

Regulatory landscape: CFTC regulates US futures (Bitcoin/Ether futures on CME); SEC has limited jurisdiction over commodity-classified crypto perps. EU MiCA (effective 2024) establishes framework. Japan and UK have separate frameworks. US persons largely cannot access offshore perpetuals (Binance, Bybit) post-CFTC enforcement.

This document covers the mechanics, math, and strategies. We assume basic familiarity with options pricing (document 202) and microstructure (document 201). Solidity code is shown only where conceptually necessary; for production strategies, web3.py, ethers.js, or anchor are appropriate frameworks.

---

## Spot vs Perpetual vs Futures

| Product | Settlement | Expiry | Funding |
|---|---|---|---|
| Spot | T+0 (or T+1 for fiat) | None | None |
| Quarterly futures | At expiry | Yes (3M) | None |
| Perpetual swap | Continuous | Never | Funding rate |

The key innovation: **perpetuals never expire**. Instead, they use a **funding rate** mechanism to anchor the perp price to the underlying spot. When perp > spot, longs pay shorts; when perp < spot, shorts pay longs. The rate creates a force pulling the perp price back to spot.

Why perpetuals dominate:
- No roll cost (vs futures).
- No need to manage expiry rolls.
- High leverage (50-125× on offshore venues).
- Simple mental model.
- Continuous exposure for funding-rate strategies.

Crypto futures (CME, Binance, etc.) still exist but are dwarfed by perpetuals by 5-10×.

---

## Perpetual Swap Mechanics

### Position Notation

Long position with size N (in base currency, e.g., BTC) at entry price P_e:
- Notional = N × P_e (in quote, e.g., USD or USDT).
- Margin requirement = Notional / leverage.
- Unrealized PnL = N × (P_t − P_e).

### Settlement

Continuous mark-to-market. PnL accrues second-by-second (or block-by-block on DEX). Positions can be unilaterally closed at any time.

### Margin Currency

- **USD-margined (linear)**: profit/loss in USD per BTC moved. Most retail-facing.
- **Coin-margined (inverse)**: profit/loss denominated in the asset itself. PnL nonlinear in price (1 BTC payout becomes more or fewer USD). Used in BTCUSD inverse perps.

For most analysis, we use USD-margined. Inverse perps require special handling for delta hedging.

### Order Types

Beyond standard market and limit:
- **Reduce-only**: only reduces position size, never increases.
- **Post-only**: only adds liquidity (rejected if would cross spread).
- **Stop**: triggers at price; becomes market or limit.
- **TIF**: GTC, IOC, FOK.

---

## Funding Rate Computation

The funding rate determines the periodic payment between longs and shorts. Different venues use different formulas; the canonical (Binance/Bybit) form:

$$
\text{Funding Rate} = \text{Premium Index} + \text{clamp}(\text{Interest Rate} - \text{Premium Index}, -k, k),
$$

where:
- **Premium Index** = average of (perp - mark) / mark over the funding interval.
- **Interest Rate** = small fixed rate (typically 0.01% per 8h, equivalent to ~10% APY) representing the cost of capital differential between currencies.
- **k** is a clamp (typically 0.05% per 8h).

The funding interval is 8 hours on most venues (Binance, Bybit), 4 hours or 1 hour on others (FTX legacy, Hyperliquid). Settlement happens at fixed UTC times (00:00, 08:00, 16:00 for 8h).

### Direction of Funding

- Funding rate > 0: longs pay shorts. Implies perp > spot.
- Funding rate < 0: shorts pay longs. Implies perp < spot.

### Funding Calculation Example

```python
import numpy as np

def funding_rate(perp_prices, mark_prices, interest_rate=0.0001, clamp=0.0005):
    """Compute Binance-style funding rate."""
    premium = np.mean((perp_prices - mark_prices) / mark_prices)
    return premium + np.clip(interest_rate - premium, -clamp, clamp)

# Sample: perp trading at 1% premium throughout the period
perps = np.full(100, 101.0)
marks = np.full(100, 100.0)
fr = funding_rate(perps, marks)
print(f"Funding rate: {fr*100:.4f}% per 8h")
print(f"Annualized: {fr * 3 * 365 * 100:.2f}%")
```

### Funding Across Venues

Different venues have different funding intervals and clamps. Cross-venue funding rate dispersion is common and exploitable:
- Binance funding > Deribit funding by 5-15 bps for short periods.
- CEX vs DEX (Hyperliquid) funding differences can be 30-50 bps.

This dispersion drives the basis arbitrage strategies in section 9.

### Reality Check — Funding Rate Estimation

Estimating funding before settlement requires integrating premium throughout the interval. Sudden spikes near settlement can flip the direction. Production funding-rate strategies time entries/exits to avoid being caught by a flip.

---

## Mark Price and Index Price

### Index Price

The **index price** is a manipulation-resistant reference computed from multiple spot exchanges. Typical formula: weighted median of last trade prices on N constituent exchanges (e.g., Binance, Coinbase, Bitstamp, Kraken, Bitfinex).

For Binance BTCUSDT perp, the index uses ~10 spot exchanges with hourly weight rebalancing. Manipulation resistance: even bribing one exchange's spot price doesn't move index much.

### Mark Price

The **mark price** is used for liquidations and unrealized PnL. It is NOT the perp's last-trade price. Why: a momentary perp price spike (e.g., from cascading liquidations) shouldn't trigger more liquidations.

Mark price formulas vary:
- **Index + EMA of premium**: most common. mark = index × (1 + EMA(premium)).
- **Index + funding-rate-implied premium**: alternative.
- **Pure index**: simplest but doesn't reflect futures basis.

### Cross-Venue Mark Price

For DeFi protocols using oracle prices (Chainlink), the mark price is the oracle's reading. Oracle delay can be exploited (e.g., 30-second update intervals on Chainlink) — historically, this caused exploits like the Mango oracle attack.

---

## Liquidation Engines

When margin falls below maintenance level, position is forcibly closed. Engine details:

### Initial vs Maintenance Margin

- **Initial Margin (IM)**: required to open position. Set by user-selected leverage. e.g., 10× → 10% IM.
- **Maintenance Margin (MM)**: minimum to hold. Typically 0.5-2.5% of notional.
- **Liquidation triggers when** equity / notional < MM.

### Liquidation Process

1. Position triggered for liquidation.
2. Engine attempts close at "liquidation price" (typically a small spread from mark).
3. If close fills at or better than bankruptcy price, position closed; remainder returned.
4. If close fills worse than bankruptcy price, deficit goes to insurance fund or is socialized via ADL.

### Auto-Deleveraging (ADL)

When insurance fund cannot cover deficit, **ADL** kicks in:
- Profitable counterparty positions are forcibly closed (highest-PnL first).
- Losses are socialized.
- ADL is rare on liquid venues (Binance) but common on smaller DEXes.

### Insurance Fund

Most CEXes maintain an insurance fund:
- Funded by liquidation fees and partial close-out gains.
- Used to cover liquidation deficits.
- Public balance disclosed.

### Liquidation Cascades

When prices move sharply, multiple positions liquidate in sequence. Each liquidation pushes price further, triggering more liquidations.

Famous cascades:
- May 19, 2021: $9B+ in BTC longs liquidated in 24 hours.
- November 2022 (FTX): $1.6B liquidated.
- August 17, 2023: BTC dropped 8%, $1B liquidations.

```python
def liquidation_price(side, entry, leverage, mm=0.005):
    """Compute approximate liquidation price."""
    # For long: liq = entry * (1 - 1/leverage + mm)
    # For short: liq = entry * (1 + 1/leverage - mm)
    if side == 'long':
        return entry * (1 - 1/leverage + mm)
    else:
        return entry * (1 + 1/leverage - mm)

# Long BTC at $60,000 with 10× leverage
print(f"Long liq price: ${liquidation_price('long', 60000, 10):.0f}")
print(f"Short liq price: ${liquidation_price('short', 60000, 10):.0f}")
```

### Reality Check — Cascade Risk

Position size relative to market depth determines cascade risk. A $100M long position in BTC has minimal cascade impact; a $1B position can move price 1-2% on liquidation. Risk management: avoid concentration in cascading market periods.

---

## Cross vs Isolated Margin

### Cross Margin

All positions share margin pool:
- Pro: capital efficiency; unrealized profits in one position cushion losses in another.
- Con: one position's liquidation can wipe out the pool.

### Isolated Margin

Each position has segregated margin:
- Pro: contained risk per position.
- Con: lower capital efficiency.

### Production Choice

Hedge funds typically use isolated for risk-segmented strategies, cross for portfolio-level beta hedges. Retail traders often use cross for "rescue" abilities (depositing more to save losing positions).

---

## Funding Rate Arbitrage and Basis Trades

The fundamental crypto basis trade:

**Spot-Perp Basis (cash-and-carry)**:
- Long 1 BTC spot.
- Short 1 BTC perpetual.
- Earn funding rate (when positive).
- Hedged: spot price moves cancel between legs.

### Yield

If funding rate is 0.03% per 8h (typical):
- Per day: 0.09%.
- Annualized: ~33%.

Realistic execution yields 15-25% annualized after fees and execution costs. Versus traditional cash-and-carry trades (US Treasuries 4-5%), this is highly attractive when funding is positive.

### Risk

- **Funding flips negative**: pay funding instead of receive.
- **Counterparty (exchange) risk**: FTX 2022 wiped out billions in basis-trade collateral.
- **Hedge slippage**: spot and perp may diverge briefly.
- **Borrow cost**: short-only spot strategies need to borrow; rates can be high.

### Variants

**Cross-exchange basis**:
- Long BTC perp on Exchange A (where funding is more negative).
- Short BTC perp on Exchange B (where funding is more positive).
- Earn the funding differential.

**DEX-CEX basis**:
- Long perp on Hyperliquid (negative funding).
- Short perp on Binance (positive funding).
- Earn cross-venue spread.

---

## Cash-and-Carry Strategies

Beyond perpetuals, traditional cash-and-carry on crypto futures:

### CME BTC Futures Basis

CME Bitcoin futures often trade at premium to spot ("contango"):
- December 2020: 30%+ annualized premium.
- 2021: 15-25% premium.
- 2022-2024: 5-15% (much lower).

Strategy: long spot BTC, short CME futures. At expiry, basis converges to zero.

### Backwardation and Contango Cycles

Crypto futures basis is highly cyclical:
- Bullish regimes: futures > spot (contango), positive carry for longs.
- Bearish: futures < spot (backwardation), funding flips.

Carry trade: buy backwardated, sell contango — but timing is hard.

---

## Crypto Options Markets

### Deribit (Dominant)

Deribit handles ~90% of crypto options volume. BTC and ETH options. Daily volume $1-3B notional. Strikes spaced every $1000 (BTC), every $50 (ETH). Maturities: daily, weekly, monthly, quarterly.

### Lyra, Aevo, Premia

DEX options:
- **Lyra**: AMM-based options on Optimism. Mechanism: vAMM with hedging.
- **Aevo**: orderbook-based, formerly Ribbon. Features structured products.
- **Premia**: pool-based options, multi-chain.

### Hegic, Dopex, Other

Various older or niche protocols. Liquidity varies.

### CME Bitcoin Options

For US-regulated trading. Lower volume than Deribit. Used by institutional hedges.

---

## BTC/ETH Option Pricing

### Black-Scholes Adaptations

Crypto options pricing typically uses Black-Scholes with adjustments:
- **Implied vol curve**: similar shape to FX (positive skew, sometimes asymmetric).
- **Risk-free rate**: USD/USDT funding rate, which differs from short-term Treasury.
- **Dividend yield**: zero for BTC/ETH.
- **Settlement**: cash-settled in USD or USDT.

### Jump Diffusion

Crypto returns have fatter tails than equity. Jump-diffusion models (Merton 1976):

$$
dS = \mu S \, dt + \sigma S \, dW + S(e^Y - 1) dN,
$$

with Y ~ N(α, β²) jump sizes and N Poisson jumps. Parameters typical for BTC:
- λ ≈ 1-2 jumps per year.
- α ≈ -2% (downward bias).
- β ≈ 5-10%.

### Variance Gamma, Heston

Heston stochastic vol fits BTC vol surface reasonably. Variance Gamma captures fat tails. Document 202 covers calibration.

---

## Crypto Vol Surface

### Skew Direction

Unlike equity (negative skew, OTM puts > OTM calls), crypto often has *positive skew*:
- Calls trade at higher IV than puts at similar moneyness.
- Reason: structural retail "lottery ticket" demand for upside calls.
- Inverse of equity leverage effect.

Empirical data (Deribit, late 2024):
- BTC 30-day ATM IV: ~50%.
- 30-delta call IV: 55%.
- 30-delta put IV: 52%.
- Risk reversal (call IV − put IV): +3 vol points.

For comparison, SPX risk reversal is typically -8 to -15 vol points (negative skew).

### Term Structure

- Short-dated (daily/weekly): high IV, often spiky.
- Monthly: moderate.
- Quarterly: lower (mean-reverting toward implied long-run vol).

### Volatility Risk Premium

Like equity, BTC IV typically exceeds realized vol on average:
- 30-day BTC IV: ~50% average.
- 30-day BTC realized: ~40% average.
- VRP: ~10 vol points.

This drives selling-vol strategies (Aevo covered call vaults).

---

## DVOL Index

Deribit's DVOL Index (formerly dvol) is the "crypto VIX":
- Methodology mimics VIX (Goldman-Carr-Madan replication).
- 30-day forward implied vol of BTC and ETH.
- Used as benchmark for vol exposure.

Calculated daily; futures on DVOL exist for hedging vol risk.

---

## Variance and Volatility Swaps

### Variance Swap

Pay K_var (strike), receive realized variance over T. Replicated as:

$$
\text{Var swap fair} \approx \frac{2}{T} \int_0^\infty \frac{1}{K^2} \!\left[ K - F \cdot 1_{\{F < K\}} \right] dK.
$$

In practice: integrate market option prices weighted by 1/K² to get fair variance swap rate.

### On Deribit

Deribit lists variance swaps directly. Spread between OTC quote and on-screen price often 2-3 vol points.

---

## Structured Products — Vaults

### Covered Call Vaults (Aevo, formerly Ribbon)

Mechanics:
1. Vault holds spot ETH (or BTC).
2. Sells weekly out-of-the-money call options on Deribit.
3. Premium is distributed to depositors.
4. If call expires ITM, ETH is delivered (capping upside).

Yield: 10-20% APY in calm periods, less in crashes (calls expire worthless but spot drops).

### Put-Selling Vaults

Variant: hold USDC, sell weekly OTM puts. Premium yields 10-15% APY. Risk: assigned ETH on a crash.

### Other Strategies

- Iron condors: bounded upside and downside.
- Calendar spreads: vol risk premium harvest.
- Theta gangs: pure premium harvest.

### Reality Check — Vault Risks

Vault yields look compelling but have hidden risks:
- Smart contract risk (Aevo, Lyra contracts have been audited but bugs exist).
- Counterparty risk on Deribit (centralized counterparty for OTC option trades).
- Tail risk: a black-swan move can lose months of premium.

---

## Pendle Yield Tokenization

Pendle splits a yield-bearing asset into:
- **Principal Token (PT)**: matures to 1 underlying at expiry.
- **Yield Token (YT)**: receives yield until expiry.

For example, stETH (staked ETH) at 4% APY:
- PT-stETH: trades at discount, redeems for 1 stETH at expiry.
- YT-stETH: trades at premium reflecting expected future yield.

### PT Pricing

PT trades at 1 / (1 + YTM × T), where YTM is the implied "yield to maturity" — the discount rate the market applies.

Strategy: buy PT at discount, lock in fixed yield by holding to expiry.

### YT Pricing

YT pricing depends on expected yield and yield variance. Trades like a perpetual claim on yield.

### Use Cases

- **Fixed-income on-chain**: PT acts as a zero-coupon bond.
- **Yield speculation**: long YT for higher implied yield, short YT for lower.
- **Yield arbitrage**: across markets where same yield-bearing token has different YT prices.

```python
import numpy as np

def pt_yield(pt_price, time_to_maturity_days):
    """Implied annualized yield from PT price."""
    return (1/pt_price - 1) * 365 / time_to_maturity_days

# Example: PT-stETH at 0.95, 90 days to maturity
print(f"Implied yield: {pt_yield(0.95, 90)*100:.2f}% APR")
```

---

## Decentralized Perps — dYdX

### dYdX V4 (Cosmos Chain)

After migrating from StarkEx (V3) to a Cosmos-based standalone chain:
- Order book matching on-chain (with off-chain MEV protection).
- Validators run matching engine.
- 1-second block time; latency competitive with CEX.
- DYDX token for governance and fees.

Architecture:
- Sequencer on each validator.
- Matching deterministic given block ordering.
- No mempool pre-confirmation (built-in MEV resistance).

### Performance

Daily volume regularly $1-2B. Major BTC/ETH/SOL/etc perpetuals. Insurance fund similar to CEX.

---

## GMX-Style Models

GMX (on Arbitrum, Avalanche) introduced novel mechanism:
- **GLP** (or **GM**) is the liquidity provider token.
- GLP holders are the counterparty for traders.
- Trader profits = GLP losses.

### Pricing

GMX uses Chainlink oracles + spread for entry/exit. No order book.

### LP Returns

GLP has multi-asset composition (BTC, ETH, USDC, etc). LPs earn:
- 70% of perp trading fees.
- Funding rate revenue.
- Negative trader skew (most retail traders lose on perps).

Historical GLP yield: 15-30% APY.

### Risk

- GLP holders are *short volatility*. When traders win big, GLP loses.
- Concentration risk: GLP composition changes with deposits/withdrawals.
- Smart contract risk.

### GMX V2

Introduced **isolated markets**: each market has its own GM token (e.g., ETH/USD GM, BTC/USD GM). Better risk segmentation.

---

## Synthetix v3

Synthetix v3 (Optimism, Base, Arbitrum):
- Modular: separate markets, each with their own collateral and pricing.
- Perps V3: Chainlink-oracle priced. No order book.
- LPs (SNX stakers + others) are counterparty.

Mechanism: similar to GMX but multi-collateral and multi-market.

---

## Hyperliquid

L1 chain purpose-built for perp trading:
- On-chain order book.
- Sub-second matching.
- HFT-friendly (millisecond latency).
- HYPE token for governance.

Volume grew rapidly in 2024 — at times >$5B daily, competitive with mid-tier CEXes.

Architecture:
- Custom L1 (not EVM).
- Validator-managed order book.
- Withdrawal-friendly UX.

---

## Power Perpetuals (Squeeth)

Squeeth (Opyn): a perpetual on the *square* of ETH price. Payoff: ETH². Mathematically equivalent to a continuously-rebalanced variance swap.

### Math

If ETH spot is S, Squeeth tracks oS = c × S² for some constant c (the "scaling factor").

Funding rate is computed to reflect the cost of carrying the convex position (gamma) — typically 1-2% per day.

### Use Cases

- **Long volatility**: long Squeeth profits when ETH moves big in either direction.
- **Hedging structured products**: vol-of-vol exposure.

### Reality Check — Squeeth Volume

Squeeth has academic interest but limited liquidity. Practical use is for sophisticated vol traders, not mass market.

---

## MEV in Derivatives

MEV (Maximal Extractable Value) in DEX perps:

### Liquidation Frontrunning

Bots monitor pending transactions; when a liquidation is profitable, they attempt to be first.

### JIT (Just-In-Time) Liquidity

For Uniswap V3 (also on perp DEXes with similar structure):
- Bot detects large incoming swap.
- Adds tight liquidity right before swap (in same block).
- Captures swap fees.
- Removes liquidity right after.

### Sandwich Attacks

Less common in perps (where pricing is oracle-based) but possible in some DEX architectures.

### Flashbots and MEV-Boost

Solutions:
- Flashbots: private mempool.
- MEV-Boost: builder/proposer separation in Ethereum PoS.
- Cowswap-style batch auctions: discrete-time matching prevents many MEV attacks.

---

## Order Book DEXes

Trade-offs vs AMM:
- **Order book**: capital efficient (concentrated at orderbook prices), HFT-compatible.
- **AMM**: passive LPs, simpler UX, gas-light per trade.

Modern hybrid: dYdX V4, Hyperliquid use order books with on-chain matching but off-chain order propagation. Capital efficiency similar to CEX.

---

## AMM-Based Perps (vAMM)

Perpetual Protocol V1 (now legacy):
- **Virtual AMM**: x*y=k formula, but with virtual reserves (no actual deposits to AMM).
- LPs are passive funders.
- Funding rate from imbalance corrections.

Largely replaced by GMX-style models for capital efficiency.

---

## Options on DEX (Lyra)

Lyra v2:
- AMM-based options.
- Pricing via Black-Scholes with on-chain IV.
- Liquidity providers backstop the trades; protocol hedges via Synthetix perps.
- Iterative AMM design with vol-of-vol adjustments.

Volume: $50-200M monthly, smaller than Deribit but growing.

---

## Stablecoin Derivatives

### USDC vs USDT Basis

USDC/USDT pair sometimes trades off 1.0:
- Depegs (e.g., USDC briefly to 0.88 in March 2023 SVB crisis).
- Premium during regulatory uncertainty.

Strategy: long USDC at discount, short USDT (or vice versa) — bet on convergence to 1.0.

### Hedging Stablecoin Risk

Options on USDC available on Deribit. Premium for "depeg insurance" during major events.

---

## Token Unlock Arbitrage

Many crypto tokens have **vesting schedules**:
- Pre-sale investors locked for 6-12 months.
- Team locked for 1-4 years.
- Cliffs (large unlocks) on specific dates.

Predictable supply shock: when unlock occurs, supply increases sharply. Strategies:
- Short token before unlock.
- Buy puts before unlock.
- Calendar spread (sell pre-unlock, buy post-unlock).

Empirical: median 5-10% drop within a week of major unlock.

---

## Validator Yield Products

### Staking

ETH staking yields ~3-4% APY base + MEV ~1-2% APY total.
- Liquid staking tokens (stETH, rETH, etc.) tokenize the stake.

### Restaking — EigenLayer

Restaking allows ETH (or LST) to secure additional protocols:
- Each restaked ETH can validate multiple AVS (Actively Validated Services).
- Additional yield from AVS rewards.
- Slashing risk amplified.

### Liquid Restaking Tokens (LRTs)

Renzo (ezETH), Ether.fi (eETH), Puffer (pufETH), Kelp (rsETH) — tokenize restaked positions. Trade yield vs liquidity.

### Strategy

Long LRT vs short ETH: capture restaking yield. Hedge ETH price risk.

---

## Crypto-Equity Correlation Trades

### BTC vs MicroStrategy (MSTR)

MSTR holds large BTC reserves. MSTR/BTC ratio:
- In bull markets: MSTR > BTC (premium for "BTC equity exposure").
- In bear: MSTR < BTC.

Pairs trade: long undervalued, short overvalued. Mean-reverting historically.

### ETH vs Coinbase (COIN)

Similar dynamic. COIN earnings tied to crypto trading volume.

### GBTC NAV Arbitrage (Pre-Conversion)

Before conversion to spot ETF (January 2024), Grayscale Bitcoin Trust (GBTC) traded at significant NAV discount. Long GBTC + short BTC futures captured discount when it converged.

After conversion: GBTC trades close to NAV, eliminating the trade.

---

## Risk Management for Crypto Books

### Unique Risks

- **Counterparty risk**: FTX 2022 wiped out funds. Diversify across venues. Use trusted custody for spot.
- **Oracle manipulation**: Mango October 2022, $114M loss.
- **Smart contract bugs**: Curve Vyper compiler bug 2023.
- **Regulatory**: BUSD shutdown 2023, US enforcement actions.
- **Gas spikes**: high gas can prevent execution at planned levels.

### Standard Risks

- VaR / ES (cross-ref doc 218).
- Position limits.
- Concentration limits.
- Stress testing for cascade scenarios.

### Crypto-Specific Risk Models

- Tail-aware (tail index ξ ~ 0.4-0.6, vs 0.2-0.3 for equities).
- Funding-rate-aware: funding spikes can dwarf P&L.
- Liquidation-aware: monitor liquidation distances continuously.

---

## Code Examples

### Funding Rate Calculator

```python
import numpy as np

def funding_payment(notional, funding_rate, side):
    """Payment for one funding interval."""
    return -notional * funding_rate * (1 if side == 'long' else -1)

# Long $1M BTC at 0.03% funding rate
fr = 0.0003
print(f"Long pays: ${funding_payment(1_000_000, fr, 'long'):.2f}")
print(f"Short receives: ${-funding_payment(1_000_000, fr, 'short'):.2f}")
```

### Basis Trade Backtest

```python
def basis_trade_backtest(perp_prices, spot_prices, funding_rates):
    """Simulate cash-and-carry: long spot, short perp."""
    n = len(perp_prices)
    pnl = []
    notional = 1_000_000
    for t in range(n):
        # Funding payment (received)
        funding_pnl = notional * funding_rates[t]
        # Basis convergence pnl (small if hedged)
        basis_pnl = 0  # ideally zero
        pnl.append(funding_pnl + basis_pnl)
    return np.cumsum(pnl)

np.random.seed(42)
n = 100  # 100 funding intervals
funding = np.random.normal(0.0001, 0.0002, n)  # mean 1bp per 8h
cum_pnl = basis_trade_backtest(np.full(n, 60000), np.full(n, 60000), funding)
print(f"Cumulative PnL after {n} funding intervals: ${cum_pnl[-1]:,.0f}")
print(f"Annualized: {cum_pnl[-1] / 1_000_000 * 365 * 3 / n * 100:.2f}%")
```

### Deribit Option Chain

```python
# Pseudocode using Deribit API
import requests

def get_deribit_options(currency='BTC'):
    url = f"https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
    params = {'currency': currency, 'kind': 'option'}
    r = requests.get(url, params=params).json()
    return r['result']

# Fetch and identify ATM monthly options for IV calculation
```

### Black-Scholes for Crypto with Jumps

```python
import numpy as np
from scipy.stats import norm

def merton_call(S, K, r, sigma, T, lam, alpha, beta, max_n=50):
    """Merton jump-diffusion call price."""
    k = np.exp(alpha + 0.5*beta**2) - 1
    price = 0.0
    for n in range(max_n):
        sigma_n = np.sqrt(sigma**2 + n*beta**2/T)
        r_n = r - lam*k + n*(alpha + 0.5*beta**2)/T
        weight = np.exp(-lam*(1+k)*T) * (lam*(1+k)*T)**n / np.math.factorial(n)
        d1 = (np.log(S/K) + (r_n + 0.5*sigma_n**2)*T) / (sigma_n*np.sqrt(T))
        d2 = d1 - sigma_n*np.sqrt(T)
        bs = S*norm.cdf(d1) - K*np.exp(-r_n*T)*norm.cdf(d2)
        price += weight * bs
    return price

# BTC ATM 30-day call with jumps
S, K, r, T = 60000, 60000, 0.05, 30/365
sigma, lam, alpha, beta = 0.50, 1.0, -0.05, 0.10
print(f"Merton BTC call: ${merton_call(S, K, r, sigma, T, lam, alpha, beta):.0f}")
```

---

## Reality Checks

- **Counterparty risk dominates**: even good models fail if exchange collapses.
- **Funding rate volatility**: funding can flip suddenly during market events.
- **Liquidity is fragmented**: large orders need cross-venue routing.
- **Regulatory tail risk**: unannounced policy changes can ban access.
- **Smart contract risk**: bugs in DEX contracts can lose funds.
- **Gas and MEV**: on-chain execution has unique costs.

---

## Reference Tables, Cheat Sheets, Bibliography

### Major Venues

| Venue | Type | Volume | Notable |
|---|---|---|---|
| Binance | CEX | $50-100B/day | Largest |
| OKX | CEX | $20-40B/day | Strong Asia |
| Bybit | CEX | $15-30B/day | UI |
| Deribit | CEX (options) | $0.5-2B/day | Dominant options |
| Coinbase | CEX | $5-15B/day | US-regulated |
| dYdX V4 | DEX | $1-2B/day | Order book |
| Hyperliquid | DEX | $3-10B/day | HFT-grade |
| GMX | DEX | $100-500M/day | LP-as-counterparty |
| Synthetix V3 | DEX | $50-200M/day | Multi-collateral |
| Aevo | DEX (options) | $50-200M/day | Vaults + perps |
| Lyra | DEX (options) | $5-50M/day | AMM options |

### Bibliography

- **Bitmex Perpetual Whitepaper** (2016).
- **Deribit volatility documentation**.
- **Squeeth Whitepaper** (Opyn, 2022) — Dave White, Andrew Leone.
- **Lyra v2 Documentation**.
- **dYdX V4 Whitepaper**.
- **GMX Documentation**.
- **Hyperliquid Documentation**.
- **EigenLayer Whitepaper**.
- **Daian, P. et al. (2019), "Flash Boys 2.0", USENIX**.
- **Angeris, G. and Chitra, T. — papers on AMM math**.
- **Pendle Whitepaper**.

### Cross-References

- Document 200 — Stochastic Calculus.
- Document 201 — Microstructure.
- Document 202 — Vol Surface.
- Document 206 — EVT.
- Document 216 — DeFi Advanced.
- Document 218 — Hedge Fund Risk Operations.
- Document 66 — Perpetual Funding Rate Arb.
- Document 67 — Liquid Staking Derivatives.
- Document 68 — MEV Sandwich Attacks.

---

*End of document 209. ~1,400 lines.*
