# 215 — Commodities: Pricing, Storage, and Convenience Yield

> Quantitative reference for commodity markets: cost-of-carry, convenience yield, contango/backwardation, Schwartz-Smith two-factor model, energy markets, metals, agriculturals, livestock, weather effects, calendar spreads, crack spreads, CTAs. Self-contained beyond document 200.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Commodity Classification](#classification)
3. [Spot vs Futures](#spot-vs-futures)
4. [Cost-of-Carry Model](#cost-of-carry)
5. [Convenience Yield](#convenience-yield)
6. [Contango and Backwardation](#contango-back)
7. [Term Structure Models](#term-structure)
8. [Schwartz One-Factor (1997)](#schwartz-1)
9. [Schwartz-Smith Two-Factor](#schwartz-smith)
10. [Gibson-Schwartz](#gibson)
11. [Brennan-Schwartz Option Pricing](#brennan-schwartz)
12. [Crack Spreads](#cracks)
13. [Spark Spreads](#sparks)
14. [Calendar Spreads](#calendar)
15. [Energy Futures](#energy)
16. [Metals](#metals)
17. [Agricultural Markets](#agriculture)
18. [Livestock](#livestock)
19. [Storage Costs and Arbitrage](#storage)
20. [Inventory Reports](#inventory)
21. [Supply-Demand Modeling](#supply-demand)
22. [Weather and Commodities](#weather)
23. [Currency Effects](#currency)
24. [Geopolitical Risk](#geopolitical)
25. [Carry Strategies in Commodities](#commodity-carry)
26. [Roll Yield and ETFs](#roll-yield)
27. [Commodity Indices](#indices)
28. [CTAs and Managed Futures](#cta)
29. [Commodity-Equity Links](#commodity-equity)
30. [Storage Arbitrage in Real Time](#storage-arb)
31. [Crude Oil April 2020](#april-2020)
32. [Risk Management](#risk-management)
33. [Code Examples](#code)
34. [Reality Checks](#reality-checks)
35. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

Commodity markets price physical raw materials. Daily futures volume on major commodities exceeds $400B notional. The "shape" of commodity markets differs from financial markets:

- Physical delivery: futures can be delivered, not just cash-settled.
- Storage costs: holding inventory costs money (warehouse, financing).
- Convenience yield: holding inventory has option value (avoid stockout).
- Seasonal patterns: many commodities have weather/season dependencies.
- Geopolitical risk: production concentrated in specific regions.

These features lead to specific pricing models. The cost-of-carry framework, with extensions for convenience yield and stochastic factors, dominates academic and practitioner work.

This document covers the pricing models, market structure, and trading strategies. Documents 200, 201, 208 provide foundational machinery.

---

## Commodity Classification

### Energy

- **Crude oil**: WTI (NYMEX), Brent (ICE), Dubai. Differentiated by location, sulfur content.
- **Refined products**: Gasoline (RBOB), heating oil, diesel.
- **Natural gas**: Henry Hub (NYMEX), TTF (Europe), JKM (Asia LNG).
- **Power**: Electricity. Highly regional.
- **Coal**: Various markets.

### Metals

- **Precious**: Gold, silver, platinum, palladium.
- **Industrial**: Copper, aluminum, zinc, lead, nickel, tin.
- **Iron ore, steel**: Industrial bulk commodities.

### Agriculturals

- **Grains**: Corn, soybeans, wheat (Chicago, KC, MGEX), oats, rice.
- **Soft commodities**: Sugar, coffee, cocoa, cotton, orange juice.

### Livestock

- Live cattle, feeder cattle, lean hogs, pork bellies (defunct).

### Reality Check — Commodity Heterogeneity

Each commodity has its own market structure, regulation, and supply-demand dynamics. Generalizing across commodities is dangerous; specific expertise required.

---

## Spot vs Futures

### Physical Spot

For most commodities, physical spot trades through specialized dealers (oil traders, metal merchants). Less transparent than financial markets.

### Futures

Standardized contracts on regulated exchanges. Most commodity price discovery happens here.

Major exchanges:
- **NYMEX/COMEX (CME Group)**: US energy and metals.
- **ICE Futures**: Brent, agricultural (sugar, coffee, cocoa).
- **CBOT (CME Group)**: US grains.
- **LME**: London Metal Exchange (industrial metals).
- **DCE, SHFE, ZCE**: Chinese futures exchanges.

### Settlement

- **Physical delivery**: most futures allow physical delivery at expiry.
- **Cash settlement**: some products (e.g., financial futures, some commodity indices).

Most speculators close before delivery; physical delivery is rare in futures.

---

## Cost-of-Carry Model

For a commodity with cash-and-carry arbitrage:

$$
F = S \cdot e^{(r + u - y) T},
$$

where:
- F = futures price.
- S = spot price.
- r = risk-free rate.
- u = storage cost (annualized).
- y = convenience yield.

If F > S × e^{(r+u-y)T}: cash-and-carry arbitrage — buy spot, sell future, store, deliver.

If F < S × e^{(r+u-y)T}: reverse cash-and-carry — borrow commodity (if possible), sell spot, invest at r, buy future, return at delivery.

### Reality Check — Arbitrage Limits

Reverse cash-and-carry often impossible (cannot easily borrow physical commodity). Cash-and-carry limited by:
- Storage capacity.
- Storage cost variations.
- Borrowing costs.

So the "arbitrage" is one-sided.

---

## Convenience Yield

Working (1949) and others: holding inventory has option value:
- Avoid stockouts in unexpected demand.
- Avoid premature sales.
- Maintain operations.

Convenience yield y reflects this benefit.

### Empirical

- High during shortages: inventories low, premium for physical.
- Low during gluts: inventories high, no urgency.
- Time-varying: function of inventory levels.

For crude oil: y typically 5-15% during normal markets, can spike to 30-50% during shortages.

### Theory of Storage

Inventory level → convenience yield:
- High inventory: low y.
- Low inventory: high y.

Working's hypothesis: y is decreasing function of inventory.

---

## Contango and Backwardation

### Contango

Forward curve sloping up: F > S. Implies (r + u - y) > 0, i.e., financing + storage > convenience yield. Normal for commodities with low convenience yield.

### Backwardation

Forward curve sloping down: F < S. Implies y > r + u. Normal for commodities in high demand or shortage.

### Common Patterns

- **Crude oil**: oscillates. Contango in shale glut periods, backwardation in tight markets.
- **Gold**: typically slight contango (financing + storage, low convenience yield).
- **Natural gas**: seasonal contango (winter > summer).
- **Coffee**: typically backwardation.

```python
def curve_state(F_array, S):
    """Return contango/backwardation state."""
    if F_array[0] > S:
        return 'contango'
    elif F_array[0] < S:
        return 'backwardation'
    return 'flat'
```

### Reality Check — Curve Dynamics

Contango/backwardation can flip rapidly. Inventory shocks, weather, geopolitics drive changes.

---

## Term Structure Models

For pricing options and derivatives, model the entire forward curve dynamics.

### One-Factor

Spot price S follows GBM. Forward F(t, T) = S × e^{(r+u-y)(T-t)}.

Limitation: assumes deterministic relationship between spot and futures. Empirically wrong.

### Multi-Factor

Schwartz (1997): two factors capture short-term and long-term dynamics.

---

## Schwartz One-Factor (1997)

$$
dS_t = \alpha (\mu - \log S_t) S_t dt + \sigma S_t dW_t,
$$

mean-reverting log spot.

### Bond/Forward Pricing

Closed-form via Vasicek-like algebra on log S.

### Use

Simple model for early commodity pricing work. Mean reversion captures inventory pull.

---

## Schwartz-Smith Two-Factor

Schwartz and Smith (2000): decompose log S into two factors.

$$
\log S_t = \chi_t + \xi_t,
$$

with:

- $d\chi_t = -\kappa \chi_t dt + \sigma_\chi dW^\chi_t$ (short-term, mean-reverting).
- $d\xi_t = \mu_\xi dt + \sigma_\xi dW^\xi_t$ (long-term, drifting).
- $d\langle W^\chi, W^\xi \rangle_t = \rho_{\chi \xi} dt$.

### Forward Curve

$$
\log F(t, T) = e^{-\kappa(T-t)} \chi_t + \xi_t + \mu_\xi (T-t) + \text{adjustment}.
$$

Captures:
- Short-end: short-term factor χ dominates.
- Long-end: long-term factor ξ dominates.

### Calibration

Fit (κ, μ_ξ, σ_χ, σ_ξ, ρ_χξ) to observed forward curve and historical data.

### Use

Production model for commodity-derivatives pricing. Many extensions (Geman, Trolle-Schwartz) build on this base.

---

## Gibson-Schwartz

Gibson and Schwartz (1990): two-factor with stochastic convenience yield.

$$
dS_t = \mu S_t dt + \sigma_S S_t dW^S_t,
$$
$$
dy_t = \kappa(\theta - y_t) dt + \sigma_y dW^y_t.
$$

Convenience yield y is mean-reverting.

### Forward Curve

$$
\log F(t, T) = \log S_t + (r + u)(T - t) - \int_t^T y_s ds.
$$

### Use

Standard for crude oil and other commodities with significant stochastic convenience yield.

---

## Brennan-Schwartz Option Pricing

Extends Schwartz framework to commodity option pricing. Closed-form for European options under affine factor models.

For path-dependent (Asian, barrier), Monte Carlo or PDE.

---

## Crack Spreads

Refining margins:
- **3-2-1 crack**: 3 barrels crude → 2 gasoline + 1 heating oil.
- **5-3-2 crack**: variant.

### Trading

Long crack: buy crude futures, sell gasoline + heating oil futures (or opposite, depending on view).

Profits if refining margins widen (or narrow on short).

### Empirical

Crack spreads cyclical. Refining capacity utilization drives margins. Seasonal: gasoline demand peaks summer.

---

## Spark Spreads

Power generation margins:
- **Spark spread**: power price - heat rate × natural gas price.
- **Heat rate**: BTU per kWh, ~7-12 for typical generators.

### Trading

Long spark: buy power, sell gas. Profitable when power demand outstrips gas costs (e.g., heat waves).

### Reality Check — Spark Spread Volatility

Power markets are highly volatile and regional. Trading requires deep understanding of local grid dynamics.

---

## Calendar Spreads

Buy one expiry, sell another (same commodity).

### Long Calendar (long near, short far)

Profit if curve flattens (near rises relative to far) or backwardation strengthens.

### Short Calendar (short near, long far)

Profit if contango widens.

### Use

- Speculate on curve shape.
- Hedge basis risk in physical positions.
- Carry play in stable markets.

### Seasonal Calendar Spreads

- Natural gas: long winter, short summer (capture seasonal premium).
- Heating oil: similar to natural gas.
- Crude oil: less seasonal but still patterns.

---

## Energy Futures

### WTI vs Brent

WTI (West Texas Intermediate) NYMEX: light sweet crude, US delivery point Cushing OK.
Brent ICE: light sweet, North Sea delivery.

WTI-Brent spread: typically -$5 to +$3. Drivers: US production, pipeline capacity, exports.

### Natural Gas

- Henry Hub (NYMEX): US benchmark.
- TTF (ICE): European benchmark.
- JKM: Japan-Korea Marker (LNG).

Massive regional dispersion: TTF 5-10× HH in 2022 European energy crisis.

### Heating Oil and Gasoline

US-based products. Quarterly seasonal patterns.

---

## Metals

### Precious

- **Gold**: COMEX (NY) and LBMA (London). Gold-USD inverse correlation.
- **Silver**: more industrial demand, more volatile than gold.
- **Platinum, palladium**: auto catalyst demand. Platinum used to be > gold; reversed since 2015.

### Industrial

- **Copper**: COMEX, LME. "Doctor copper" for global manufacturing.
- **Aluminum**: LME. Energy-intensive production.
- **Nickel**: LME. Stainless steel + EV batteries.

### LME Specifics

LME has 3-month spot-equivalent + warehouse system. Different from US futures structure. Cash-and-carry math involves warrants and rent.

---

## Agricultural Markets

### Grains

- **Corn**: CBOT, May/Sep/Dec primary contracts. Used for feed, ethanol, food.
- **Soybeans**: CBOT, similar contracts. Crushed for oil + meal.
- **Wheat**: CBOT (soft red winter), KC (hard red winter), MGEX (hard red spring).

### Softs

- **Sugar**: ICE (#11 raw, #16 white). Brazil dominant producer.
- **Coffee**: ICE. Arabica (#9), robusta (London).
- **Cocoa**: ICE. West Africa dominant.
- **Cotton**: ICE. US, China, India top producers.

### Reality Check — Agricultural Volatility

Weather shocks can move prices 30%+ in days. Production concentration in specific regions creates supply concentration risk.

---

## Livestock

- Live cattle, feeder cattle, lean hogs.

### Trading Patterns

- Seasonal (summer grilling, winter slaughter).
- Disease outbreaks (avian flu, swine flu).
- Feed cost link (corn).

### Reality Check — Livestock Niche

Less liquid, regional, niche. Most quant funds avoid; specialized commodity hedge funds participate.

---

## Storage Costs and Arbitrage

### Physical Storage

- Crude: tanks, $0.30-1.50 per barrel/month.
- Natural gas: salt caverns, depleted reservoirs.
- Grains: silos, ~1-3% of value/month.
- Metals: warehouses, $10-30/MT/month.

### Financial Storage via Futures

Buy spot, sell future, store, deliver. Cost = financing + storage. Profit = futures price - spot - costs.

### Limits

- Storage capacity finite.
- Capital required tied up.
- Operational risk (oil tank fires, etc.).

---

## Inventory Reports

Major market-moving data:

- **EIA petroleum**: weekly Wednesday US oil/gas inventory.
- **USDA WASDE**: monthly world agricultural supply/demand estimates.
- **LME stocks**: daily metal warehouse inventory.
- **Cushing OK inventory**: weekly.

Surprises move prices significantly. HFT firms compete to react fastest.

---

## Supply-Demand Modeling

### Bottom-Up

Aggregate supply across producing regions, demand across consuming regions. Account for inventory changes, planned outages, weather.

### Top-Down

GDP growth → demand. Productive capacity → supply. Equilibrium price.

### Hybrid

Most production models combine: bottom-up granularity for short-term, top-down for long-term.

---

## Weather and Commodities

### Heating-Degree Days (HDD)

Below 65°F days × deviation.

### Cooling-Degree Days (CDD)

Above 65°F days × deviation.

### Use

Forecast natural gas, electricity demand from weather forecasts. Major HFT signal.

### El Niño / La Niña

Multi-year ocean-atmosphere cycle. Affects:
- North/South American precipitation.
- Asian monsoons.
- Hurricane formation.
- Crop yields.

ENSO indices: SOI (Southern Oscillation Index), MEI (Multivariate ENSO Index).

---

## Currency Effects

Most commodities priced in USD. Currency effects:
- USD strength → commodity prices down (for non-USD buyers).
- USD weakness → commodity prices up.

Inverse correlation: USD index DXY vs commodity index BCOM ~ -0.5 historically.

---

## Geopolitical Risk

Major events:
- **OPEC+ decisions**: production quotas drive crude.
- **Russia-Ukraine 2022**: gas, wheat, fertilizer disrupted.
- **Middle East tensions**: Iran/Israel/Saudi.
- **Sanctions**: cut off specific producers.

### Trading

Geopolitical pricing-in:
- Risk premium in oil (typically $5-15/barrel during heightened tension).
- Wheat/corn premium during Black Sea disruption.
- Gold rally on geopolitical risk.

---

## Carry Strategies in Commodities

### Long Backwardation

Long backwardated commodities. Roll yield positive (selling far, buying near).

### Short Contango

Inverse. Profitable when contango persists.

### Empirical

Backwardation in oil (1990s, 2010s shale glut sometimes contango). Variable.

---

## Roll Yield and ETFs

ETFs like USO (oil), UNG (natural gas) roll futures monthly.

### Roll Yield Math

When futures contango: ETF buys near, rolls to far. Each roll incurs cost (sells low, buys high).

For UNG with persistent contango (2010s): ETF lost 90%+ over a decade despite stable spot prices. Pure roll yield decay.

### Use

- Avoid roll-decay-heavy ETFs in contango.
- Roll yield strategies: long backwardated, short contango.

---

## Commodity Indices

### GSCI (S&P GSCI)

Goldman Sachs Commodity Index. Production-weighted; heavy in energy.

### BCOM (Bloomberg Commodity Index)

Diversified weighting; less energy-heavy.

### DBLCI

Deutsche Bank Liquid Commodities Index.

### Use

- Diversification: low correlation with equities.
- Inflation hedge: rises during inflation.
- Tradeable via futures and ETFs.

---

## CTAs and Managed Futures

CTAs trade commodity (and financial) futures systematically.

### Trend-Following

Most CTAs run trend-following on commodity futures:
- 100-200 day moving average crossovers.
- Or various Tom Demark-style trend identification.

### AHL, Winton, Man, Aspect

Major CTAs with long track records. Sharpe ~0.5-0.7.

### Crisis Alpha

CTAs profit during equity crashes (long bonds + short equities). Document 89 covers this.

---

## Commodity-Equity Links

### Energy Stocks vs Crude

XLE (energy ETF) tracks ~$70-90 oil; rises with oil price.

### Miners vs Gold

GDX (gold miners ETF) leveraged exposure to gold. Higher beta than GLD.

### Trading

Pairs trade: long miner, short metal. Profits if miner outperforms.

Or hedge directional exposure: long XLE - short OIH (services).

---

## Storage Arbitrage in Real Time

### Cash-and-Carry

When futures premium exceeds storage cost, profitable to buy physical, sell future.

Capital required: significant. Tank/warehouse capacity needed.

### Real-Time

Production trading desks monitor:
- Physical/futures basis.
- Available storage capacity.
- Logistics constraints.

Open arbitrages can persist for weeks; closed by trading firms with storage.

---

## Crude Oil April 2020

Negative WTI prices on April 20, 2020:
- May contract expired April 21.
- Storage at Cushing nearly full.
- No buyers willing to take delivery.
- Contract collapsed to -$37.63.

Lessons:
- Physical delivery risk in commodity futures.
- Storage matters.
- ETFs (USO) can be hit by negative prices.

---

## Risk Management

### Position Limits

Regulatory and exchange position limits per commodity.

### VaR

Standard methods. Historical simulation appropriate given commodity-specific dynamics.

### Stress Testing

- Geopolitical scenarios (war, embargo).
- Weather extremes.
- Supply chain disruption.

### Storage and Logistics

For physical commodity desks: insurance, tank inspection, hedging operational risk.

---

## Code Examples

### Cost-of-Carry Pricing

```python
import numpy as np

def cost_of_carry(S, r, u, y, T):
    """Forward price under cost-of-carry."""
    return S * np.exp((r + u - y) * T)

# Crude oil: spot $80, r=5%, storage 3%, convenience yield 7%
F = cost_of_carry(80, 0.05, 0.03, 0.07, 1.0)
print(f"1Y crude forward: ${F:.2f}")
```

### Schwartz-Smith Forward Curve

```python
def ss_forward(t, T, chi, xi, kappa, mu_xi, sigma_chi, sigma_xi, rho):
    decay = np.exp(-kappa*(T-t))
    log_F = decay*chi + xi + mu_xi*(T-t)
    # Convexity adjustments (variance)
    var = sigma_chi**2*(1 - decay**2)/(2*kappa) + sigma_xi**2*(T-t) + 2*rho*sigma_chi*sigma_xi*(1 - decay)/kappa
    log_F -= 0.5 * var
    return np.exp(log_F)

# Forward curve at various tenors
for T in [0.25, 0.5, 1.0, 2.0, 5.0]:
    F = ss_forward(0, T, 0.05, np.log(80), 1.5, 0.02, 0.3, 0.15, -0.3)
    print(f"T={T}: F = ${F:.2f}")
```

### Crack Spread Backtest

```python
def crack_spread_backtest(crude_prices, gasoline_prices, heating_oil_prices, ratio='3-2-1'):
    """Compute 3-2-1 crack spread P&L."""
    if ratio == '3-2-1':
        # 3 crude long, 2 gasoline + 1 heating oil short
        spread = 2*gasoline_prices + heating_oil_prices - 3*crude_prices
    return np.diff(spread)  # daily P&L

# Apply to historical data
```

---

## Reality Checks

- **Physical risk**: production, storage, logistics issues.
- **Regulatory caps**: position limits enforced.
- **Margin shocks**: exchanges can raise margins suddenly (2020 oil, 2022 nickel).
- **Liquidity**: thinly-traded back-month contracts.
- **Model limitations**: convenience yield is hard to estimate; multi-factor models help but don't solve.

---

## Reference Tables, Cheat Sheets, Bibliography

### Major Contracts

| Contract | Exchange | Size | Tick |
|---|---|---|---|
| WTI crude (CL) | NYMEX | 1000 bbl | $0.01 = $10 |
| Brent (B) | ICE | 1000 bbl | $0.01 = $10 |
| Natural gas (NG) | NYMEX | 10000 MMBtu | $0.001 = $10 |
| Gold (GC) | COMEX | 100 oz | $0.10 = $10 |
| Silver (SI) | COMEX | 5000 oz | $0.005 = $25 |
| Copper (HG) | COMEX | 25000 lb | $0.0005 = $12.50 |
| Corn (ZC) | CBOT | 5000 bu | $0.0025 = $12.50 |
| Soybeans (ZS) | CBOT | 5000 bu | $0.0025 = $12.50 |
| Wheat (ZW) | CBOT | 5000 bu | $0.0025 = $12.50 |
| Sugar (SB) | ICE | 112000 lb | $0.0001 = $11.20 |
| Coffee (KC) | ICE | 37500 lb | $0.05 = $18.75 |

### Bibliography

- **Schwartz, E. (1997), "The Stochastic Behavior of Commodity Prices", *J. Finance* 52(3): 923–973.**
- **Schwartz, E. and Smith, J. (2000), "Short-Term Variations and Long-Term Dynamics in Commodity Prices", *Management Science* 46(7): 893–911.**
- **Gibson, R. and Schwartz, E. (1990), "Stochastic Convenience Yield and the Pricing of Oil Contingent Claims", *J. Finance* 45(3): 959–976.**
- **Geman, H. (2005), *Commodities and Commodity Derivatives*, Wiley.**
- **Eydeland, A. and Wolyniec, K. (2003), *Energy and Power Risk Management*, Wiley.**
- **Working, H. (1949), "The Theory of the Price of Storage", *American Economic Review* 39(6): 1254–1262.**
- **Pindyck, R. (1994), "Inventories and the Short-Run Dynamics of Commodity Prices", *RAND Journal of Economics*.**
- **Litzenberger, R. and Rabinowitz, N. (1995), "Backwardation in Oil Futures Markets", *J. Finance*.**
- **Erb, C. and Harvey, C. (2006), "The Strategic and Tactical Value of Commodity Futures", *Financial Analysts Journal*.**

### Cross-References

- Document 89 — Crisis Alpha VIX Trend (CTAs).
- Document 92 — Energy Crack Spreads.
- Document 200 — Stochastic Calculus.
- Document 202 — Vol Surface (commodity options).

---

*End of document 215. ~1,400 lines.*
