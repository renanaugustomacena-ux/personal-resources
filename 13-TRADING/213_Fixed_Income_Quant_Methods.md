# 213 — Fixed Income Quantitative Methods

> Reference for fixed-income pricing and risk: yield curve construction, short-rate models (Vasicek, CIR, Hull-White, Black-Karasinski), HJM/LMM, MBS prepayment, OAS, credit risk (structural and reduced-form), CDS, swaps, repo, basis. Self-contained beyond document 200.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Bond Pricing Fundamentals](#bond-pricing)
3. [Day Count Conventions](#day-count)
4. [Yield Curve Bootstrapping](#bootstrap)
5. [Yield Curve Splines](#splines)
6. [Nelson-Siegel and Diebold-Li](#nelson-siegel)
7. [Forward Rates](#forwards)
8. [Multi-Curve Framework](#multi-curve)
9. [Vasicek Model](#vasicek)
10. [Cox-Ingersoll-Ross](#cir)
11. [Hull-White](#hull-white)
12. [Black-Karasinski](#black-karasinski)
13. [HJM Framework](#hjm)
14. [LIBOR Market Model](#lmm)
15. [Cap and Floor Pricing](#caps-floors)
16. [Swaption Pricing](#swaptions)
17. [Treasury Market Microstructure](#treasury-micro)
18. [Repo Markets](#repo)
19. [Treasury Auctions](#auctions)
20. [Inflation-Linked Bonds](#inflation)
21. [MBS](#mbs)
22. [Prepayment Models](#prepayment)
23. [CMOs and Tranching](#cmo)
24. [OAS](#oas)
25. [Credit Risk — Structural](#credit-structural)
26. [Credit Risk — Reduced Form](#credit-reduced)
27. [CDS Pricing](#cds-pricing)
28. [Sovereign Credit](#sovereign)
29. [Yield Curve Trading](#curve-trading)
30. [Carry and Roll-Down](#carry-roll)
31. [Convexity Adjustments](#convexity)
32. [Eurodollar/SOFR Futures](#sofr-futures)
33. [Treasury Futures](#treasury-futures)
34. [Swap Pricing](#swap-pricing)
35. [Cross-Currency Basis](#xccy)
36. [Risk Metrics](#risk-metrics)
37. [Portfolio Risk](#portfolio-risk)
38. [Duration Hedging](#duration-hedging)
39. [Code Examples](#code)
40. [Reality Checks](#reality-checks)
41. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

The global fixed income market is approximately $130 trillion in outstanding notional — larger than equities. Government bonds (US Treasuries, JGBs, Bunds, gilts) make up roughly $50T; corporates $40T; securitized products (MBS, CMBS, ABS, CLO) $15T; municipal $4T; emerging markets the remainder.

Quantitative fixed income covers the math of pricing and risk-managing these instruments. The mathematical apparatus differs from equity in two important ways:

1. **Yield curves**, not single prices. Every fixed income instrument has multiple cash flows at multiple times; the valuation requires a yield curve, which itself must be constructed from a portfolio of instruments.

2. **Interest-rate models**, not pure GBM. Short-rate models (Vasicek, CIR, Hull-White) and forward-rate models (HJM, LMM) describe the dynamics of the entire term structure. They have analytical structure that allows closed-form bond and option pricing.

This document covers the standard machinery. We assume the prerequisites of document 200 (stochastic calculus, basic SDEs) and basic calculus.

A practitioner's note: fixed income is *unit-sensitive*. Day-count conventions, settlement dates, and compounding frequencies vary across markets. Mistakes in unit conversion are the single largest source of pricing errors in production fixed-income systems.

---

## Bond Pricing Fundamentals

### Present Value

A coupon bond with face F, coupon rate c (annual), maturity T, and yield y (continuous compounding) has price:

$$
P = \sum_{i=1}^N \frac{c F}{m} e^{-y t_i} + F e^{-y T},
$$

where m is coupon frequency, t_i = i/m. The yield y solves this equation for given P.

For semi-annual coupon (US Treasuries):

$$
P = \sum_{i=1}^{2T} \frac{c/2 \cdot F}{(1 + y/2)^i} + \frac{F}{(1 + y/2)^{2T}}.
$$

### Yield to Maturity (YTM)

The y making the equation hold given the market price. Implies a flat yield curve at y. In practice, yield curves are not flat; YTM is a single-number summary.

### Accrued Interest

Between coupon dates, interest accrues:

$$
\text{AI} = \frac{cF}{m} \cdot \frac{\text{days since last coupon}}{\text{days in coupon period}}.
$$

Quoted price (clean) excludes AI; settlement price (dirty) includes it.

### Duration

**Macaulay duration**:

$$
D_M = \frac{\sum t_i \cdot PV(\text{cash flow}_i)}{P}.
$$

**Modified duration**: $D_{\text{mod}} = D_M / (1 + y/m)$. Sensitivity of price to yield: $\Delta P / P \approx -D_{\text{mod}} \Delta y$.

### Convexity

$$
C = \frac{1}{P} \sum t_i^2 \cdot PV(\text{cash flow}_i) \cdot \frac{1}{(1 + y/m)^2}.
$$

Second-order: $\Delta P / P \approx -D_{\text{mod}} \Delta y + \frac{1}{2} C (\Delta y)^2$.

---

## Day Count Conventions

Different markets use different rules for counting days:

| Convention | Markets | Formula |
|---|---|---|
| ACT/360 | USD money market | Actual days / 360 |
| ACT/365 | GBP money market | Actual days / 365 |
| ACT/ACT | USD treasuries | Actual days / actual year |
| 30/360 | USD corporates | (30 × months + days) / 360 |
| 30/360 European | EUR | Slightly different |

```python
from datetime import date

def day_count(start, end, convention):
    if convention == 'ACT/360':
        return (end - start).days / 360
    elif convention == 'ACT/365':
        return (end - start).days / 365
    elif convention == 'ACT/ACT':
        # Approximation; ISDA has specific rules
        return (end - start).days / 365.25
    elif convention == '30/360':
        d1 = min(30, start.day)
        d2 = end.day if d1 < 30 or end.day > 30 else 30
        return (360*(end.year - start.year) + 30*(end.month - start.month) + (d2 - d1)) / 360
    raise ValueError(f"Unknown convention: {convention}")

# Example
print(day_count(date(2024, 1, 15), date(2024, 7, 15), 'ACT/360'))
print(day_count(date(2024, 1, 15), date(2024, 7, 15), '30/360'))
```

### ISDA Definitions

ISDA publishes detailed specifications for each convention. Production systems use libraries (QuantLib, Bloomberg, Reuters) that implement these correctly.

---

## Yield Curve Bootstrapping

Construct the discount factor curve from observed bond prices.

### Procedure

For zero-coupon bonds (e.g., T-bills): D(t) = P_t.

For coupon bonds at maturity T:

$$
P_T = \sum_{i: t_i < T} c \cdot \delta \cdot D(t_i) + (1 + c\delta) D(T),
$$

where δ is coupon period (e.g., 0.5 for semiannual). Solve for D(T) given previously bootstrapped D(t_i).

```python
import numpy as np

def bootstrap_zero_rates(prices, maturities, coupons, frequencies):
    """Bootstrap zero rates from coupon bonds."""
    n = len(prices)
    rates = np.zeros(n)
    discount_factors = np.zeros(n)
    
    for i in range(n):
        T = maturities[i]
        c = coupons[i] / frequencies[i]  # per-period coupon
        n_periods = int(T * frequencies[i])
        
        # PV of intermediate coupons
        pv_intermediate = 0
        for j in range(1, n_periods):
            t_j = j / frequencies[i]
            # Linear interpolation for D(t_j)
            d_j = np.interp(t_j, maturities[:i], discount_factors[:i])
            pv_intermediate += c * d_j
        
        # Solve for D(T)
        # P = pv_intermediate + (1 + c) * D(T)
        d_T = (prices[i] - pv_intermediate) / (1 + c)
        discount_factors[i] = d_T
        rates[i] = -np.log(d_T) / T  # continuous compounding
    
    return rates, discount_factors
```

---

## Yield Curve Splines

Smooth interpolation:

### Cubic Splines

Fit a cubic polynomial in each interval between knots, with first and second derivatives matching at knots.

### Smoothing Splines

Penalize curvature for smoother fit:

$$
\min_S \sum_i (y_i - S(x_i))^2 + \lambda \int (S''(x))^2 dx.
$$

Tradeoff: λ controls smoothness vs fit.

### Monotonicity Constraints

For discount factors, require D monotonically decreasing. Use monotone splines or constrained optimization.

---

## Nelson-Siegel and Diebold-Li

**Nelson-Siegel** (1987): parametric form for yield curve:

$$
y(\tau) = \beta_0 + \beta_1 \frac{1 - e^{-\tau/\lambda}}{\tau/\lambda} + \beta_2 \!\left( \frac{1 - e^{-\tau/\lambda}}{\tau/\lambda} - e^{-\tau/\lambda} \right).
$$

Three latent factors:
- β_0: long-run level.
- β_1: short-end slope.
- β_2: medium-term hump.

λ controls hump location.

**Diebold-Li** (2006): NS with time-varying βs that follow VAR(1) dynamics. Used for forecasting.

```python
def nelson_siegel(tau, beta0, beta1, beta2, lam):
    a = 1 - np.exp(-tau / lam)
    b = a / (tau / lam)
    return beta0 + beta1 * b + beta2 * (b - np.exp(-tau / lam))

# Calibration via least-squares
from scipy.optimize import minimize

def fit_ns(maturities, yields):
    def loss(params):
        b0, b1, b2, lam = params
        if lam <= 0: return 1e10
        return ((nelson_siegel(maturities, b0, b1, b2, lam) - yields)**2).sum()
    result = minimize(loss, [0.04, -0.02, 0.01, 1.0], method='Nelder-Mead')
    return result.x
```

---

## Forward Rates

### Continuous

Instantaneous forward rate:

$$
f(t, T) = -\frac{\partial}{\partial T} \log D(t, T).
$$

### Simple

LIBOR-style forward over [T_1, T_2]:

$$
F(T_1, T_2) = \frac{1}{T_2 - T_1} \!\left( \frac{D(t, T_1)}{D(t, T_2)} - 1 \right).
$$

Forward rates are observable in the futures market (Eurodollar, SOFR futures).

---

## Multi-Curve Framework

Post-2008 reality: different curves for different uses.

### OIS Discount Curve

Overnight Indexed Swap (OIS) rates form the discount curve. For USD: SOFR; for EUR: €STR; for GBP: SONIA.

### Forward Curves

Separate curves for projecting future floating-rate payments:
- 1M LIBOR (legacy, deprecated post-2023).
- 3M LIBOR (legacy).
- SOFR (replacement).

### CSA Discounting

When trades are collateralized in different currencies, discount at the appropriate currency's OIS rate.

---

## Vasicek Model

$$
dr_t = \kappa(\theta - r_t) dt + \sigma dW_t.
$$

Mean-reverting Gaussian short rate.

### Bond Pricing

$$
P(t, T) = A(t, T) e^{-B(t, T) r_t},
$$

where:

$$
B(t, T) = \frac{1 - e^{-\kappa(T-t)}}{\kappa},
$$

$$
A(t, T) = \exp\!\left[ (\theta - \sigma^2/(2\kappa^2))(B(t, T) - (T - t)) - \sigma^2 B(t, T)^2 / (4\kappa) \right].
$$

### Calibration

Fit (κ, θ, σ, r_0) to current term structure.

### Limitations

- Rates can go negative (was a problem until 2008+; now seen as feature).
- Constant volatility unrealistic.

---

## Cox-Ingersoll-Ross

$$
dr_t = \kappa(\theta - r_t) dt + \sigma \sqrt{r_t} dW_t.
$$

Volatility scales with sqrt(r): rates near zero have low volatility.

### Feller Condition

$$
2 \kappa \theta \ge \sigma^2.
$$

If satisfied, rates stay strictly positive.

### Bond Pricing

Affine structure like Vasicek; closed-form pricing (more complex algebra).

### Transition Density

Non-central chi-squared. Used in Monte Carlo and bond option pricing.

---

## Hull-White

$$
dr_t = (\theta_t - \kappa r_t) dt + \sigma dW_t.
$$

Time-dependent θ_t calibrated to current term structure. Bond prices match observed curve exactly.

### Calibration

θ_t is set such that:

$$
\theta_t = \frac{\partial f^M(0, t)}{\partial t} + \kappa f^M(0, t) + \frac{\sigma^2}{2 \kappa}(1 - e^{-2\kappa t}),
$$

where $f^M(0, t)$ is the market instantaneous forward rate.

Hull-White is the standard for swaption and cap pricing in production.

---

## Black-Karasinski

$$
d \log r_t = (\theta_t - \kappa \log r_t) dt + \sigma dW_t.
$$

Lognormal short rates: rates strictly positive. No closed-form bond pricing; use trinomial tree calibrated to initial curve.

---

## HJM Framework

Heath-Jarrow-Morton (1992): direct modeling of forward rates.

$$
df(t, T) = \alpha(t, T) dt + \sigma(t, T) dW_t.
$$

For the model to be arbitrage-free under risk-neutral measure:

$$
\alpha(t, T) = \sigma(t, T) \int_t^T \sigma(t, s) ds.
$$

This is the **HJM drift restriction**.

### Practical Use

HJM is the most general no-arbitrage framework. Specific models (Vasicek, Hull-White) are special cases.

---

## LIBOR Market Model (LMM)

Brace-Gatarek-Musiela (1997): models discrete forward rates as lognormal under their respective forward measures:

$$
dF_k(t) = F_k(t) \sigma_k(t) dW_t^k.
$$

Each F_k follows lognormal under its T_k-forward measure. Cross-measure dynamics are more complex.

### Use

Standard for cap/floor and swaption pricing in production. Calibrates to ATM caplet vols easily; smile fits via stochastic vol extension (SABR-LMM).

---

## Cap and Floor Pricing

### Caplet

A caplet at strike K and maturity T pays (LIBOR(T_-1, T) - K)^+ × notional × δ.

Black '76 formula:

$$
\text{Caplet} = \delta \cdot N \cdot D(t, T) \!\left[ F \Phi(d_1) - K \Phi(d_2) \right],
$$

where d_1 = (log(F/K) + σ²(T-t)/2) / (σ√(T-t)).

### Cap

Sum of caplets. Strike is one for the entire cap; pricing is sum.

---

## Swaption Pricing

Option on a swap.

### Payer Swaption

Pays max(S - K, 0) at expiry, where S is the prevailing swap rate.

### Black '76 for Swaptions

Under the swap measure:

$$
\text{Payer} = \text{Annuity}(t, T) \cdot \!\left[ S \Phi(d_1) - K \Phi(d_2) \right].
$$

### SABR for Swaption Smile

SABR (document 202) standard for capturing volatility smile across strikes.

---

## Treasury Market Microstructure

### Primary Dealers

22 primary dealers (US): Goldman, JPM, etc. Required to bid in Treasury auctions; also major secondary-market liquidity.

### On-the-Run vs Off-the-Run

- **On-the-run**: most recently issued (most liquid).
- **Off-the-run**: older issues (less liquid).

OTR-OTR spread typically 1-5bp; opportunity for relative-value trades.

### Repo Specials

Specific issues trade at "special" repo rates due to high demand:
- Recently auctioned issues.
- Issues used in popular trades.
- Squeeze candidates.

Special rate can be 200+ bp below GC (general collateral) repo.

---

## Repo Markets

Sale-and-repurchase agreement: borrow cash collateralized by securities.

### GC vs Specials

- **General Collateral (GC)**: any acceptable security as collateral. Rate ~ Fed Funds.
- **Special**: specific security. Rate can be much lower.

### Tri-Party Repo

Settled through BNY Mellon or JPM. Operations standardized.

### Bilateral Repo

Direct between counterparties. More flexibility, more risk.

### Term Repo Curve

Multiple-day repos at different maturities. Used for funding strategies.

---

## Treasury Auctions

US Treasuries: uniform-price auction.

### Mechanics

1. Treasury announces issue size.
2. Bidders submit price-quantity schedules.
3. Bids accepted in price order until issue clears.
4. All accepted bidders pay the lowest accepted price (clearing price).

### Direct vs Indirect Bidders

- **Direct**: institutional.
- **Indirect**: foreign central banks (a major buyer).
- **Primary dealers**: required participation.

### Strategy

Bid the expected clearing price minus a small shading. Optimal strategy depends on private valuation and prior over others' bids.

Document 205 covers auction theory.

---

## Inflation-Linked Bonds

### TIPS (US)

Treasury Inflation-Protected Securities. Principal adjusts with CPI.

### Real Yield Curve

Yield on inflation-linked bonds, not nominal. Difference from nominal Treasury yield ≈ expected inflation + inflation risk premium.

### Breakeven Inflation

$$
\text{Breakeven} = y^{\text{nom}} - y^{\text{real}}.
$$

Implied inflation rate that makes nominal and real returns equal.

### Trading

- Long TIPS, short nominal: long inflation expectations.
- Short TIPS, long nominal: short inflation.

---

## MBS

Mortgage-Backed Securities.

### Pass-Through Structure

Investor receives pro-rata share of mortgage payments (principal + interest).

### Agency vs Non-Agency

- **Agency** (Fannie, Freddie, Ginnie): guaranteed, no credit risk.
- **Non-agency** (private label): credit risk.

### Prepayment Risk

Mortgages can prepay (refinance, sell home, default). MBS investors face uncertain duration.

---

## Prepayment Models

### PSA Standard

Public Securities Association standard:
- 0% PSA: no prepayment.
- 100% PSA: 0.2% per month for 30 months, then 6% annually.

Real prepayment varies based on:
- **Refinancing incentive**: current rate vs note rate.
- **Burnout**: borrowers who could refinance but haven't.
- **Turnover**: home sales (5-10% per year).
- **Curtailment**: partial principal payments.
- **Defaults**.

### S-curve Model

Refinancing intensity is S-shaped function of rate gap:

$$
\text{CPR}(\text{gap}) = \text{base} + \text{amplitude} \cdot \frac{1}{1 + e^{-(g - \mu)/\sigma}}.
$$

### Modern Models

- Production prepayment models include hundreds of variables.
- Calibrated on historical data.
- Updated for new mortgage products.

---

## CMOs and Tranching

CMOs split MBS into tranches with different cash flow priorities:

### Sequential

A pays first, then B, then C. A receives all principal until paid off; B then receives; etc.

### PAC (Planned Amortization Class)

Receives stable principal payments within a band. Stability achieved by passing prepayment risk to "support" tranches.

### IO/PO

Interest-only and principal-only strips. IOs benefit from slow prepayment; POs from fast.

### Reality Check — CMO Risk

Higher tranches have less prepayment risk; lower tranches absorb it. Pricing requires sophisticated prepayment models.

---

## OAS (Option-Adjusted Spread)

Spread over Treasury curve that makes model price match market price, accounting for embedded options (prepayment).

### Methodology

1. Choose interest-rate model (e.g., Hull-White).
2. Generate many interest-rate paths.
3. For each path, simulate prepayments and cash flows.
4. PV all cash flows at the path-specific Treasury rate + OAS.
5. Average across paths.
6. Solve for OAS that makes average PV = market price.

### Use

OAS lets you compare MBS to Treasuries on a like-for-like basis after stripping prepayment optionality.

---

## Credit Risk — Structural

Merton (1974): firm's equity is a call option on firm assets, struck at debt face value.

### Model

Firm value V follows GBM:

$$
dV_t = \mu V_t dt + \sigma V_t dW_t.
$$

At maturity T, debt holders receive min(V_T, F). Equity is (V_T - F)^+.

Default probability:

$$
P(\text{default}) = \Phi(-d_2),
$$

where $d_2 = (\log(V/F) + (\mu - \sigma^2/2)T)/(\sigma \sqrt{T})$.

Credit spread:

$$
s = -\frac{1}{T} \log\!\left( \frac{1 - L \Phi(-d_2)}{1} \right),
$$

with L = loss given default.

### Black-Cox

Default occurs when V hits a barrier (not just at maturity). Closed form for first-passage time.

### KMV / Moody's

Commercial implementation: estimates V and σ from observable equity prices and balance sheet data. Computes "expected default frequency" (EDF).

---

## Credit Risk — Reduced Form

Don't model firm value; model default arrival as a hazard rate process.

### Jarrow-Turnbull

Default time τ exponential with constant intensity λ.

### Cox Process

Intensity is itself stochastic (e.g., follows CIR).

### Pricing

Survival probability:

$$
P(\tau > T) = \mathbb{E}\!\left[\exp\!\left(-\int_0^T \lambda_s ds\right)\right].
$$

Risky bond price:

$$
P^{\text{risky}}(t, T) = \mathbb{E}\!\left[(1 - L \cdot 1_{\tau \le T})\right] \cdot D(t, T).
$$

---

## CDS Pricing

Credit Default Swap: protection against default.

### Mechanics

- Buyer pays fixed rate (CDS spread) periodically.
- Seller pays (1 - R) × notional if default occurs.

### Pricing Formula

CDS spread S satisfies:

$$
S \cdot \text{Annuity} = (1 - R) \cdot \text{Default Leg PV}.
$$

Where:
- Annuity = sum of survival probability × discount factor at each payment date.
- Default Leg = sum of default probability × discount factor.

### Bootstrap

Given CDS spreads at multiple maturities (1Y, 3Y, 5Y, 7Y, 10Y), bootstrap survival probabilities at each tenor.

```python
def cds_survival_bootstrap(spreads, maturities, R=0.4, freq=4):
    """Bootstrap hazard rates from CDS curve."""
    survivals = np.ones(len(maturities) + 1)
    for i, T in enumerate(maturities):
        # Solve for hazard rate over [maturities[i-1], T]
        # such that PV of fixed leg = PV of default leg
        # ... (requires numerical solver)
        pass
    return survivals
```

### CDS-Bond Basis

Difference between CDS spread and bond spread (yield over Treasury). Theoretically zero; in practice ranges:
- Investment grade: ±20bp.
- High yield: ±100bp.

Driven by funding, regulatory, and supply/demand factors.

---

## Sovereign Credit

CDS on government debt. Quanto effect: USD-denominated CDS on EUR debt has currency risk in payoff.

### Country Risk

- Political risk premia.
- Currency risk.
- Debt sustainability.

Standard models (Markit, S&P) provide spread curves.

---

## Yield Curve Trading

### Outright Duration

Long bonds: profit if rates fall. Short: profit if rates rise.

### Curve Trades

- **Steepener**: long short-end, short long-end. Profit if curve steepens.
- **Flattener**: opposite.
- **Butterfly**: long short and long ends, short middle. Profit on curvature change.

### DV01-Neutral Sizing

Each leg sized to have equal DV01 (sensitivity per 1bp). Net DV01 = 0; only relative move matters.

---

## Carry and Roll-Down

### Carry

Income from holding the bond (coupon - financing).

### Roll-Down

As bond ages, it slides down the yield curve. If curve is upward-sloping, the bond's yield decreases (price appreciates).

For an upward-sloping curve:

$$
\text{Roll-Down} \approx \frac{\partial y}{\partial T} \cdot D \cdot \Delta T.
$$

Carry trade: long high-carry bonds, short low-carry. Works in steady markets; subject to regime shocks.

---

## Convexity Adjustments

When pricing futures vs forwards on the same underlying, futures incorporate convexity:

$$
F^{\text{futures}} = F^{\text{forward}} - \frac{1}{2} \sigma_r^2 (T - t) (T_2 - T_1).
$$

Approximate; depends on rate model. Significant for long-dated Eurodollar futures.

---

## Eurodollar/SOFR Futures

### Eurodollar (Legacy)

Futures on 3M LIBOR, settled at 100 - LIBOR. CME Globex.

### SOFR Futures

Replaced Eurodollar in 2023. Futures on 1M and 3M SOFR.

### Strip Pricing

Sum of consecutive futures gives implied forward rates.

### Calendar Spreads

Long 1 contract, short next: profits from term structure changes.

### Packs and Bundles

- **Pack**: 4 consecutive contracts.
- **Bundle**: 8, 12, 16, 20 contracts.

Used for "wholesale" rate exposure.

Document 63 covers Eurodollar/SOFR ladders.

---

## Treasury Futures

### CTD (Cheapest-to-Deliver)

Multiple Treasury bonds eligible for delivery into a futures contract. The CTD is the one with the highest implied repo rate.

### Conversion Factor

Adjustment factor for delivery: standardizes coupons across deliverable bonds.

### Basis

Difference between cash bond price and futures-implied price. Tracked for arbitrage:

$$
\text{Basis} = P^{\text{cash}} - F^{\text{fut}} \cdot CF.
$$

---

## Swap Pricing

Plain vanilla IRS: fixed leg vs floating leg.

### Fixed Leg

$$
PV_{\text{fixed}} = R \sum_i \delta_i D(t, T_i).
$$

### Floating Leg

$$
PV_{\text{float}} = N \cdot \!\left[ D(t, T_0) - D(t, T_N) \right].
$$

(Telescoping sum of forward rates.)

### Swap Rate

R that makes PV_fixed = PV_float:

$$
R = \frac{D(t, T_0) - D(t, T_N)}{\sum_i \delta_i D(t, T_i)}.
$$

---

## Cross-Currency Basis

Covered Interest Parity (CIP): forward FX rate determined by interest rates.

$$
F = S \cdot \frac{1 + r_f T}{1 + r_d T}.
$$

Post-2008: CIP violations regularly observed. Cross-currency basis = deviation from CIP.

Causes:
- Bank balance-sheet costs.
- USD funding stress.
- Regulatory constraints.

Trading: cross-currency swaps to capture basis.

---

## Risk Metrics

### DV01

Dollar Value of an 01 (1bp). Change in price for 1bp change in yield.

For a $1M bond with modified duration 7: DV01 = $1M × 7 × 0.0001 = $700.

### Key Rate Durations

Sensitivity to specific points on the curve (2Y, 5Y, 10Y, 30Y). Each sums to total duration.

### Convexity

Already covered. Second derivative.

### OAD (Option-Adjusted Duration)

Duration accounting for embedded options. For MBS, OAD < raw duration because of prepayment optionality.

---

## Portfolio Risk

### VaR for Fixed Income

- Parametric: assume normal returns, compute VaR from σ × confidence × DV01.
- Historical: simulate from historical rate moves.
- Monte Carlo: simulate from interest-rate model.

### Scenario Analysis

- Parallel shift up/down 100bp.
- Steepening / flattening.
- Twist.
- Specific historical events (1994, 2013 taper tantrum).

### Reverse Stress Testing

What rate move would cause X% loss?

---

## Duration Hedging

### Duration Matching

For a liability with duration 7, hold assets with combined duration 7. Net duration = 0; first-order interest rate risk hedged.

### Bullets vs Barbells

- **Bullet**: single maturity matching duration.
- **Barbell**: short + long maturity with combined duration.

Barbell has higher convexity than bullet — better in volatile rates, worse in steady.

### M-squared

Modified duration generalized to second-order:

$$
M^2 = \frac{1}{P} \!\left[ \sum t_i^2 PV_i / (1 + y/m)^2 \right].
$$

Used for two-factor immunization (level + slope).

### Reality Check — Hedging Limitations

Duration hedging works for parallel shifts only. Curve twists and convexity changes leave residual risk. Document 218 covers practical risk management.

---

## Code Examples

### Bond Pricing

```python
import numpy as np

def price_bond(face, coupon, ytm, T, freq=2):
    n = int(T * freq)
    cf = np.full(n, coupon * face / freq)
    cf[-1] += face
    discount = (1 + ytm/freq)**(-np.arange(1, n+1))
    return (cf * discount).sum()

# 5Y 5% coupon at 4% YTM, semi-annual
print(f"Bond price: {price_bond(100, 0.05, 0.04, 5):.4f}")
```

### Vasicek Bond Price

```python
def vasicek_bond(r, T, kappa, theta, sigma):
    B = (1 - np.exp(-kappa*T)) / kappa
    A = np.exp((theta - sigma**2/(2*kappa**2)) * (B - T) - sigma**2 * B**2 / (4*kappa))
    return A * np.exp(-B * r)

print(f"Vasicek 10Y bond: {vasicek_bond(0.04, 10, 0.5, 0.04, 0.02):.4f}")
```

### CDS Pricing

```python
def cds_pv_legs(spread, hazard, recovery=0.4, T=5, freq=4):
    times = np.arange(1, T*freq + 1) / freq
    survival = np.exp(-hazard * times)
    defaults = -np.diff(np.concatenate([[1], survival]))
    discount = np.exp(-0.04 * times)  # discount at risk-free
    
    annuity = (spread / freq * survival * discount).sum()
    default_leg = ((1 - recovery) * defaults * discount).sum()
    return annuity, default_leg

a, d = cds_pv_legs(spread=0.02, hazard=0.03)
print(f"PV fixed: {a:.4f}, PV default: {d:.4f}, ratio: {d/a:.4f}")
```

---

## Reality Checks

- **Day count details matter**: small errors propagate.
- **Multi-curve framework essential post-2008**: discounting and forward curves differ.
- **Prepayment models are imperfect**: even sophisticated models miss regime changes.
- **OAS depends on rate model**: different models give different OAS.
- **CDS-bond basis volatile**: can swing 50bp+ in stress.
- **Cross-currency basis non-zero**: explicit modeling required.

---

## Reference Tables, Cheat Sheets, Bibliography

### Standard Models

| Model | Type | Use |
|---|---|---|
| Vasicek | Short rate, Gaussian | Theoretical |
| CIR | Short rate, sqrt vol | Bond options |
| Hull-White | Short rate, time-dependent | Production swaptions |
| BK | Short rate, lognormal | Positive-rate models |
| HJM | Forward rates | General framework |
| LMM | Discrete forwards | Caplet/swaption pricing |

### Bibliography

- **Andersen, L. and Piterbarg, V. (2010), *Interest Rate Modeling*, Atlantic Financial Press.** 3 volumes; encyclopedia.
- **Brigo, D. and Mercurio, F. (2006), *Interest Rate Models: Theory and Practice*, Springer.** Standard textbook.
- **Filipović, D. (2009), *Term-Structure Models*, Springer.** Mathematically rigorous.
- **Hull, J. (2017), *Options, Futures, and Other Derivatives*, Pearson.** Introductory.
- **Tuckman, B. and Serrat, A. (2011), *Fixed Income Securities*, Wiley.** Practitioner-oriented.
- **Heath, D., Jarrow, R., Morton, A. (1992), "Bond Pricing and the Term Structure of Interest Rates", *Econometrica*.** HJM.
- **Brace, A., Gatarek, D., Musiela, M. (1997), "The Market Model of Interest Rate Dynamics", *Math Finance*.** LMM.
- **Hull, J. and White, A. (1990), "Pricing Interest-Rate Derivative Securities", *Review of Financial Studies*.**
- **Vasicek, O. (1977), "An Equilibrium Characterization of the Term Structure", *J. Financial Economics*.**
- **Cox, J., Ingersoll, J., Ross, S. (1985), "A Theory of the Term Structure of Interest Rates", *Econometrica*.**
- **Merton, R. (1974), "On the Pricing of Corporate Debt", *J. Finance*.** Structural credit.

### Cross-References

- Document 200 — Stochastic Calculus.
- Document 202 — Vol Surface (SABR for swaptions).
- Document 205 — Auction Theory.
- Document 218 — Hedge Fund Risk.
- Document 61 — Yield Curve Trading.
- Document 63 — Eurodollar/SOFR Ladders.
- Document 65 — CDS Basis Trading.

---

*End of document 213. ~1,400 lines.*
