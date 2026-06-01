# 214 — Foreign Exchange Markets: Microstructure and Strategies

> Reference for FX trading: market structure (interbank, ECNs, prime brokerage, last-look), spot/forward/swap/NDF mechanics, interest rate parity, currency factors (carry, value, momentum), FX options (Garman-Kohlhagen, vanna-volga), risk reversals, central bank dynamics, currency crises, and HFT in FX. Self-contained beyond document 200.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Market Structure](#market-structure)
3. [Last-Look Practices](#last-look)
4. [Spot, Forward, Swap, NDF](#fx-products)
5. [Quoting Conventions](#conventions)
6. [Spot Mechanics and CLS](#cls)
7. [Forwards and Interest Rate Parity](#irp)
8. [NDFs](#ndf)
9. [Cross-Currency Basis](#xccy-basis)
10. [Triangular Arbitrage](#triangular)
11. [Statistical Arbitrage in FX](#stat-arb)
12. [Carry Trade](#carry)
13. [Currency Factors](#factors)
14. [Risk Reversals and Butterflies](#risk-reversal)
15. [FX Options — Garman-Kohlhagen](#gk)
16. [Smile Dynamics in FX](#fx-smile)
17. [Vanna-Volga Pricing](#vanna-volga)
18. [Barrier Options in FX](#barriers)
19. [Exotic FX](#exotics)
20. [Central Bank Intervention](#central-bank)
21. [Currency Crises](#crises)
22. [Emerging Market Currency Dynamics](#em)
23. [HFT in FX](#hft-fx)
24. [Algorithmic Execution](#fx-execution)
25. [Currency Hedging for Portfolios](#hedging)
26. [PPP and Value](#ppp)
27. [Order Flow Research](#order-flow)
28. [Code Examples](#code)
29. [Reality Checks](#reality-checks)
30. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

FX is the world's largest financial market by volume. BIS Triennial Survey (April 2022): $7.5 trillion daily volume in spot, forwards, swaps, options, and other instruments. By comparison, US equities trade ~$500B per day; US Treasuries ~$700B.

Why is FX so large?
- Every cross-border trade requires FX.
- Hedging needs from multinationals.
- Speculative trading.
- Central bank operations.
- HFT proprietary flow.

The market is decentralized — no single exchange — and operates 24/5 (closed weekends). Different liquidity centers operate in their own time zones (Tokyo, London, NYC), with overlap creating peak liquidity.

Quantitative FX trading combines:
- **Macro signals**: rates, inflation, growth.
- **Technical signals**: momentum, mean reversion.
- **Microstructure**: order flow, last-look gaming.
- **Volatility**: options on currency pairs.

This document covers the structure, mechanics, and major strategies. Documents 200-208 provide the underlying mathematical machinery.

---

## Market Structure

### Interbank Market

Banks trade with each other through:
- Direct dealing (telephone, MSN, bilateral electronic).
- ECNs (electronic communication networks).

Top-tier banks (JPM, Citi, UBS, Deutsche, Goldman) make markets to clients and to each other.

### ECNs (Electronic Communication Networks)

- **EBS (BrokerTec)**: dominant for EUR/USD, USD/JPY, USD/CHF.
- **Reuters Matching**: similar; covers different pairs.
- **FXAll**: multi-bank platform.
- **Currenex**: multi-bank.
- **Hotspot, FastMatch**: ECN venues.

### Single-Dealer Platforms (SDPs)

Each bank's own platform: 360T (Deutsche), Velocity (Citi), CitiFX, etc. Provide bank-curated liquidity to clients.

### Prime Brokerage

Hedge funds access institutional FX through prime brokers:
- **PB Tier 1**: Goldman, JPM, MS, Citi.
- **PB Tier 2**: Deutsche, Barclays, others.

PB provides:
- Credit (counterparty for ECN/SDP trades).
- Reporting.
- Margin/collateral.
- Reach to multiple liquidity sources.

### Retail FX

- MetaTrader, OANDA, Saxo. Client-facing platforms.
- Wider spreads, lower liquidity than institutional.
- Often via principal model (broker takes other side).

### Last-Look

Major controversy: dealers can "look" at incoming requests and reject if disadvantageous to them.

### Reality Check — FX Fragmentation

FX is highly fragmented across venues, time zones, and instruments. Best execution requires routing, monitoring, and analyzing fills across multiple sources. A single-venue strategy underperforms a multi-venue one.

---

## Last-Look Practices

When a client submits a trade against a dealer's quote, the dealer can reject in a "last-look" window (typically 50-200ms).

### Asymmetric Rejection

Dealers reject orders that move adverse to them but accept those favorable. Result: clients get filled when prices move in their direction (bad for client) and rejected when prices move in dealer's direction (worse).

### Empirical

Studies (BIS, FCA): asymmetric rejection rates exceed 70% for some dealers. Average client cost ~5-15 basis points beyond explicit spread.

### MiFID II Response

EU MiFID II (2018) requires:
- Disclosure of last-look policy.
- Standardized rejection metrics.
- Symmetric rejection (in principle).

Compliance varies in practice.

### Avoiding Last-Look

- Trade on ECNs without last-look (limit-order book).
- Use SDPs with no-last-look policies.
- Negotiate symmetric last-look in PB agreements.

---

## Spot, Forward, Swap, NDF

### Spot

Trade settled at T+2 (most pairs); USD/CAD, USD/MXN at T+1.

Spot transactions are the largest single-instrument category at $2T daily.

### Outright Forward

Agreement to exchange currencies at a future date at a fixed rate. F = S + forward points.

### FX Swap

Spot trade + opposite-direction forward. Effectively borrowing one currency and lending another.

### Non-Deliverable Forward (NDF)

For restricted currencies (BRL, KRW, CNY, INR, RUB, ARS):
- Cash-settled in USD at fixing.
- No actual exchange of underlying currency.
- Used for FX exposure when delivery is restricted.

NDF market: ~$300B daily, dominated by major EM currencies.

---

## Quoting Conventions

### Base/Quote

Currency pair like EUR/USD:
- Base = EUR (first).
- Quote = USD (second).
- Quote = how much USD per 1 EUR.

### Direct vs Indirect

For US trader:
- **Direct**: USD per foreign unit. EUR/USD = 1.10 (1 EUR = 1.10 USD).
- **Indirect**: foreign per USD. USD/JPY = 150 (1 USD = 150 JPY).

### Pip and Pip Value

A "pip" is the smallest standard quote increment:
- Most pairs: 0.0001.
- JPY pairs: 0.01.

Pip value (USD per pip per standard lot):
- EUR/USD: $10 per pip per 100K lot.
- USD/JPY: $6.67 per pip (varies with rate).

### % p.a. vs Basis Points

Forward rates often quoted as % per annum or basis points:
- 1.5% p.a. annualized.
- 150 bp annualized.

---

## Spot Mechanics and CLS

### Settlement

T+2 standard. Settlement via:
- **CLS (Continuous Linked Settlement)**: PvP (payment vs payment). 18 currencies. Reduces Herstatt risk.
- **Bilateral**: direct between counterparties for non-CLS currencies.

### Holiday Calendars

Each currency has its own holiday calendar. Pair settlement uses the union of two calendars. Strange settlements:
- USD/JPY: settles when both NYC and Tokyo open.
- USD/MXN: T+1 (not T+2).

### Reality Check — Settlement Risk

Pre-CLS: Herstatt risk (1974) — failure to settle one leg of FX trade. CLS eliminated for major currencies. EM currencies still have settlement risk.

---

## Forwards and Interest Rate Parity

### Covered Interest Parity (CIP)

$$
F = S \cdot \frac{1 + r_q T}{1 + r_b T},
$$

where r_q = quote currency rate, r_b = base currency rate, T = time to maturity.

Or in continuous compounding: $F = S \cdot e^{(r_q - r_b) T}$.

### Forward Points

$$
\text{Forward points} = F - S = S \cdot \frac{(r_q - r_b) T}{1 + r_b T}.
$$

For EUR/USD with EUR rate 3%, USD rate 5%, T = 1Y, S = 1.10:
- Forward points = 1.10 × (0.05 - 0.03) × 1 / (1 + 0.03) ≈ 0.0214.
- F = 1.1214 (USD trades at premium reflecting USD rate advantage).

### Uncovered Interest Parity (UIP)

States that expected change in spot equals interest rate differential. Empirically rejected — UIP fails systematically (the "forward premium puzzle"). This failure is the basis of the carry trade.

---

## NDFs

For restricted currencies, NDF settles in USD at a fixing.

### Mechanics

Trade: long 1M USD/BRL NDF at 5.20 fixing.
Fixing day: BRL spot at 5.30.
Settlement: receive (5.30 - 5.20)/5.30 × notional in USD.

### Fixing

Standard fixing sources by currency:
- **BRL**: PTAX (Brazilian Central Bank).
- **KRW**: KFTC fixing.
- **CNY**: Central Parity Rate.
- **INR**: RBI reference rate.

Multiple fixing methodologies exist; pre-trade specify.

### Reality Check — NDF Liquidity

NDF spreads typically wider than deliverable forwards, especially at maturities beyond 3M. EM currency volatility can cause sudden liquidity drops.

---

## Cross-Currency Basis

CIP violations post-2008. Cross-currency basis = deviation of forward from CIP.

### Causes

- **Bank balance sheet costs**: holding inventory ties up regulatory capital.
- **USD funding stress**: scarce USD funding pushes basis.
- **Regulatory constraints**: leverage ratio, NSFR.

### Empirical

EUR-USD 5Y basis was -50 to -100bp through 2010s, narrower after. JPY-USD basis similarly negative. AUD-USD positive (USD funding scarce vs AUD).

### Trading

Cross-currency basis swap: borrow one currency, lend another at floating rates. Profit if basis converges.

Capital-intensive due to bank balance-sheet costs.

---

## Triangular Arbitrage

Three-currency arbitrage: e.g., EUR/USD × USD/JPY = EUR/JPY?

If EUR/USD = 1.10, USD/JPY = 150, then implied EUR/JPY = 165. If actual EUR/JPY != 165, arbitrage opportunity.

### Profit

Per round-trip: usually fractions of a pip after spreads. Arbitrage closes in microseconds at HFT speed.

### Decline of Triangular

20 years ago: large opportunities (0.5+ pips). Today: HFT closes in ~1μs; opportunities are sub-microsecond.

```python
def triangular_check(eurusd, usdjpy, eurjpy):
    """Check for triangular arbitrage."""
    implied = eurusd * usdjpy
    diff = eurjpy - implied
    return diff, abs(diff) > 0.001  # threshold

print(triangular_check(1.10, 150, 165.05))  # small mispricing
```

---

## Statistical Arbitrage in FX

### Pairs

Currency pairs with historical mean-reverting spreads:
- EUR/CHF (until SNB peg removal).
- USD/CAD vs WTI crude.
- AUD/NZD (commodity correlation).

### Cointegration

Test for cointegrated pairs. If cointegrated, spread is stationary; trade reversion.

### Reality Check — Currency Stat Arb

Currency stat arb is harder than equity:
- Few independent pairs.
- Macro shocks invalidate cointegration.
- Carry effects dominate.

---

## Carry Trade

The most famous FX strategy:
- Borrow low-interest-rate currency.
- Invest in high-interest-rate currency.
- Earn the differential as carry.

### Canonical Example: JPY-AUD

- JPY rate: 0.1%.
- AUD rate: 4%.
- Borrow 100 JPY, convert to AUD, earn 4%.
- After 1 year, repay 0.1% on JPY. Net: ~4% profit if FX unchanged.

### Why It Works (Mostly)

UIP says expected FX move offsets carry. Empirically, FX moves don't fully offset.
- Carry trade has positive expected return ~2-4% over time.
- Sharpe ~0.4-0.6.
- Volatility comes from drawdowns.

### Drawdowns

Carry trades unwind violently:
- 1998: USD/JPY fell from 147 to 112 in months.
- 2008: AUD/JPY fell 40% as crisis hit.
- 2022: JPY surged 20% on intervention.

### Asymmetric Risk

Carry has fat-tailed returns. "Picking up nickels in front of a steamroller."

Document 62 covers FX carry trade in detail.

---

## Currency Factors

Beyond carry, several systematic factors:

### Carry Factor

As above.

### Value (PPP)

Real exchange rate misalignment. Currencies far from PPP fair value tend to revert.

Computation: REER (real effective exchange rate) vs trend or fundamental.

### Momentum

Past returns predict future returns. 6-12 month lookback typical.

### Defensive

Low-volatility currencies (USD, CHF, JPY) outperform high-vol on risk-adjusted basis.

### Asness et al. Framework

"Value and Momentum Everywhere" (2013): currency factors fit value-momentum framework. Combined factor portfolios outperform individual factors.

```python
def carry_signal(rates_local, rates_foreign):
    """Carry signal: differential in basis points."""
    return (rates_local - rates_foreign) * 10000  # bps

def momentum_signal(prices, lookback=126):
    """6-month momentum signal."""
    return (prices / prices.shift(lookback)) - 1
```

---

## Risk Reversals and Butterflies

OTC FX vol surface conventions:

### Risk Reversal (RR)

$$
RR_{25\Delta} = \sigma_{\text{call}, 25\Delta} - \sigma_{\text{put}, 25\Delta}.
$$

Difference between call IV and put IV at 25-delta. Indicates skew direction.

For EUR/USD: typically slightly negative (puts more expensive). For USD/JPY: usually negative. For AUD/USD: highly negative (commodity currency, downside fear).

### Butterfly (BF)

$$
BF_{25\Delta} = \frac{\sigma_{\text{call}, 25\Delta} + \sigma_{\text{put}, 25\Delta}}{2} - \sigma_{\text{ATM}}.
$$

Indicates curvature.

### Vol Triangle

Three numbers (ATM, RR, BF) summarize the smile at one tenor. Conversion to (call IV, put IV) at fixed deltas via:

$$
\sigma_{\text{call}} = \sigma_{\text{ATM}} + BF + 0.5 RR,
$$
$$
\sigma_{\text{put}} = \sigma_{\text{ATM}} + BF - 0.5 RR.
$$

---

## FX Options — Garman-Kohlhagen

Black-Scholes adapted for two interest rates:

$$
C = S e^{-r_f T} \Phi(d_1) - K e^{-r_d T} \Phi(d_2),
$$

with d_1 = (log(S/K) + (r_d - r_f + σ²/2)T) / (σ√T) and d_2 = d_1 - σ√T.

Key insight: foreign currency = "dividend-paying stock" with dividend yield r_f.

### Premium-Adjusted vs Premium-Unadjusted Delta

In FX, premium can be paid in either currency:
- **Premium-unadjusted**: standard BS delta.
- **Premium-adjusted**: adjusted for premium paid.

For consistency, traders specify which delta is being used.

### Delta Hedging in FX

Hedge in spot. Periodic rebalancing accumulates costs (gamma scalping).

```python
import numpy as np
from scipy.stats import norm

def gk_call(S, K, r_d, r_f, sigma, T):
    d1 = (np.log(S/K) + (r_d - r_f + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return S*np.exp(-r_f*T)*norm.cdf(d1) - K*np.exp(-r_d*T)*norm.cdf(d2)
```

---

## Smile Dynamics in FX

FX smile is more *symmetric* than equity. Curvature (butterfly) dominates over asymmetry (risk reversal).

### Sticky-Strike vs Sticky-Delta

In FX, sticky-delta is common: traders quote in delta space, not strike space. The smile shape is preserved as spot moves; entire smile shifts with spot.

### Term Structure

ATM IV term structure typically:
- Short-dated: lower (calm).
- Medium: rising as event risks accumulate.
- Long: declining toward "fundamental" vol.

---

## Vanna-Volga Pricing

Standard FX exotic pricing:

### Idea

Black-Scholes price + correction for vega-vanna-volga risks not captured by flat vol assumption.

### Formula

$$
\text{Price} = \text{BS} + (\text{Vega correction}) + (\text{Vanna correction}) + (\text{Volga correction}).
$$

The corrections are weighted by the cost of hedging vega, vanna, volga using ATM, RR, BF.

Document 51 covers Vanna-Volga in detail.

---

## Barrier Options in FX

Common in FX:
- **Knock-out**: option expires worthless if barrier hit.
- **Knock-in**: option activates only if barrier hit.
- **Double-no-touch (DNT)**: pay if neither barrier hit during life.
- **One-touch**: pay if either barrier hit.

### Pricing

Closed-form for vanilla GBM (Black 1973, Merton 1973). For Heston/SABR/Jump models: Monte Carlo or PDE.

### Reality Check — Barrier Liquidity

Barrier options trade actively in FX (more than equity). Bid-ask wider than vanilla.

---

## Exotic FX

### Power Reverse Dual Currency (PRDC)

Bond paying:
- Fixed coupon if FX above strike.
- Lower coupon (or zero) if below.

JPY-denominated bonds with USD/JPY exposure. Popular pre-2008.

### Accumulators

Daily accumulation of currency at favorable rate, with knock-out trigger. Asymmetric payoff. Marketed as "wealth accumulation" but often loses dramatically when FX moves against accumulator.

### Target Accruals

Caps total accumulation; converts after threshold.

### Reality Check — Exotics Are Risky

PRDC and accumulator losses played role in 2008 crisis losses for retail wealth clients. Regulatory scrutiny increased.

---

## Central Bank Intervention

### Modes

- **Direct intervention**: buy/sell currency in market.
- **Sterilized**: offset via OMO so monetary base unchanged.
- **Unsterilized**: changes monetary base.
- **Coordinated**: multiple CBs intervene together.

### Signaling Channel

Intervention signals future policy. Even if direct effect small, signal effect can move FX.

### Famous Interventions

- **Plaza Accord (1985)**: G5 intervention to weaken USD.
- **SNB EUR/CHF cap (2011-2015)**: SNB defended 1.20 floor; abandoned suddenly Jan 15, 2015 (CHF surged 20% in minutes).
- **BOJ JPY intervention (2022)**: estimated $50B+ to support JPY.

### Reality Check — Intervention Risk

Sudden CB action wipes out positions. Currency strategies should size for tail risk; SNB-floor type events hit even hedged trades.

---

## Currency Crises

### First-Generation (Krugman 1979)

Fundamental imbalance: FX peg unsustainable given budget deficits, monetary expansion.

### Second-Generation (Obstfeld 1986)

Self-fulfilling crisis: speculative attack triggers run on reserves.

### Third-Generation (1997-98 Asia)

Banking system + currency mismatch. Currency depreciates → bank insolvency → capital flight → further depreciation.

### Modern Tools

- IMF surveillance, quotas, programs.
- Capital controls (some EMs).
- Currency intervention reserves.

---

## Emerging Market Currency Dynamics

### Drivers

- Capital flows (search for yield).
- Commodity prices (for commodity currencies).
- Election risk.
- Central bank credibility.
- Regional contagion.

### Major EM Pairs

USD/MXN, USD/BRL, USD/ZAR, USD/TRY, USD/RUB, USD/CNY, USD/INR.

### Trading

- Carry: high yields attract capital.
- Volatility: higher than DM, episodic.
- Crisis-prone: drawdowns can be 30-50%.

### Reality Check — EM Risk Management

Position sizing in EM should account for:
- Tail risk (ξ ≈ 0.4 vs 0.1 for DM).
- Capital controls.
- Convertibility risk.
- Counterparty risk in NDFs.

---

## HFT in FX

### Latency Arbitrage

Cross-venue arbitrage: EBS vs Reuters vs ECN. Latency differences create opportunities.

### Market Making

EBS and Reuters allow algorithmic market making. Top firms (Virtu, XTX, Jump) have significant FX MM presence.

### Order Flow

HFT firms detect institutional order flow and trade ahead. Last-look gaming is one form.

### Production Latencies

Best FX HFT: sub-1μs intra-venue, <100μs cross-Atlantic.

---

## Algorithmic Execution in FX

### TWAP/VWAP

For fixed-volume cash flows (corporate FX). Deterministic schedule.

### LP-Aware Routing

For institutional flow:
- Estimate fill probability per LP.
- Route to LP with best expected price including last-look impact.

### Aggregator Algorithms

State Street, BBH, etc. offer aggregator algos: split orders across multiple LPs to minimize information leakage.

---

## Currency Hedging for Portfolios

### Hedge Ratio

For an unhedged foreign equity position, hedge ratio depends on:
- Correlation between local equity and FX.
- Volatilities.
- Investor's home currency.

### Dynamic Hedging

Adjust hedge ratio as conditions change:
- More hedging when FX vol high.
- Less when correlation favorable.

### Hedge Cost

Hedging via forwards: cost = forward points (interest rate differential).
- Long EUR equity hedged: pay EUR-USD forward points.
- Currency hedging cost: 1-3% per year typical.

### Reality Check — Hedging Decisions

Most institutional managers hedge ~50% of FX risk. The "right" answer depends on benchmark, investor base, and beliefs about expected FX returns.

---

## PPP and Value

### Purchasing Power Parity

Long-run: same goods should cost same amount in different currencies.

### Big Mac Index

Economist's informal PPP measure: price of Big Mac across countries. Currencies overvalued/undervalued.

### Real Exchange Rate

$$
\text{REER} = \text{NEER} \cdot \frac{P^{\text{home}}}{P^{\text{foreign}}}.
$$

NEER = nominal effective exchange rate; P = price level.

### Mean Reversion

REER tends to revert to long-run trend over 5-10 years. Fast reversion in currencies far from fair value.

---

## Order Flow Research

Evans and Lyons (2002, 2008): private information embedded in customer order flow.

### Findings

- Customer order imbalances explain ~10% of daily FX returns.
- HFT can detect imbalances faster than fundamentals.
- Information asymmetry between dealer and client.

### Trading Implications

If you have order flow data:
- Predict short-term direction.
- Adjust quotes accordingly.
- Be cautious of adverse selection.

---

## Code Examples

### CIP and Forward Calculation

```python
def forward_rate(spot, r_quote, r_base, T):
    """Continuous compounding."""
    return spot * np.exp((r_quote - r_base) * T)

# 1Y EUR/USD forward
F = forward_rate(1.10, 0.05, 0.03, 1.0)
print(f"1Y EUR/USD forward: {F:.4f}")
print(f"Forward points: {(F - 1.10)*10000:.0f} pips")
```

### Carry Trade Simulation

```python
def simulate_carry(spot_path, r_local, r_foreign, dt=1/252):
    """Simulate carry trade returns."""
    n = len(spot_path)
    pnl = np.zeros(n - 1)
    for t in range(n - 1):
        # FX return
        fx_return = (spot_path[t+1] - spot_path[t]) / spot_path[t]
        # Carry component
        carry = (r_foreign - r_local) * dt
        # Total return
        pnl[t] = fx_return + carry
    return np.cumsum(pnl)
```

### Garman-Kohlhagen Greeks

```python
def gk_greeks(S, K, r_d, r_f, sigma, T):
    d1 = (np.log(S/K) + (r_d - r_f + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    delta = np.exp(-r_f*T) * norm.cdf(d1)
    gamma = np.exp(-r_f*T) * norm.pdf(d1) / (S*sigma*np.sqrt(T))
    vega = S*np.exp(-r_f*T) * norm.pdf(d1) * np.sqrt(T)
    return delta, gamma, vega
```

---

## Reality Checks

- **Last-look reality**: institutional FX has frictions beyond explicit spreads.
- **Carry tail risk**: positive expected, but drawdowns are violent.
- **Central bank surprise**: SNB-style events wipe out leveraged positions.
- **EM idiosyncrasy**: EM currency strategies need conservative sizing.
- **Regulatory complexity**: FX is loosely regulated; participants need to understand cross-jurisdictional rules.

---

## Reference Tables, Cheat Sheets, Bibliography

### Major FX Pairs

| Pair | Daily Volume | Typical Spread (interbank) | Notes |
|---|---|---|---|
| EUR/USD | $1.5T | 0.1-0.5 pip | Largest |
| USD/JPY | $1T | 0.2-0.5 pip | Second |
| GBP/USD | $400B | 0.5-1 pip | Cable |
| USD/CHF | $300B | 0.5-1 pip | Swiss |
| AUD/USD | $250B | 0.5-1 pip | Aussie |
| USD/CAD | $200B | 0.5-1 pip | Loonie |
| NZD/USD | $150B | 1-2 pip | Kiwi |
| USD/CNY (CNH) | $200B | 1-3 pip | Restricted |
| USD/MXN | $100B | 5-10 pip | EM |
| USD/BRL | $80B (NDF) | 10-20 pip | NDF |

### Bibliography

- **Sarno, L. and Taylor, M. (2002), *The Economics of Exchange Rates*, Cambridge.** Standard text.
- **Lyons, R. (2001), *The Microstructure Approach to Exchange Rates*, MIT.** Microstructure.
- **Wystup, U. (2017), *FX Options and Structured Products*, Wiley.** Practitioner reference.
- **Castagna, A. (2010), *FX Options and Smile Risk*, Wiley.**
- **Clark, I. (2011), *Foreign Exchange Option Pricing*, Wiley.**
- **Asness, C., Moskowitz, T., Pedersen, L. (2013), "Value and Momentum Everywhere", *J. Finance*.**
- **Evans, M. and Lyons, R. (2002), "Order Flow and Exchange Rate Dynamics", *J. Political Economy*.**
- **BIS Triennial Survey (2022), "Triennial Central Bank Survey of Foreign Exchange and OTC Derivatives Markets".**
- **Garman, M. and Kohlhagen, S. (1983), "Foreign Currency Option Values", *J. International Money and Finance*.**
- **Krugman, P. (1979), "A Model of Balance-of-Payments Crises", *J. Money, Credit, and Banking*.**

### Cross-References

- Document 17 — Triangular Arbitrage Forex.
- Document 51 — Vanna-Volga Pricing.
- Document 62 — FX Carry Trade.
- Document 200 — Stochastic Calculus.
- Document 201 — Microstructure Theory.
- Document 202 — Vol Surface.

---

*End of document 214. ~1,400 lines.*
