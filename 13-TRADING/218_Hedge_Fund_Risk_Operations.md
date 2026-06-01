# 218 — Hedge Fund Risk Management at Scale

> Operations, leverage, prime brokerage, regulatory compliance, and risk metrics for hedge funds and proprietary trading firms. Covers VaR/ES, stress testing, concentration, liquidity, counterparty, operational, and crisis management. Self-contained beyond document 200.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Fund Structure](#structure)
3. [Subscriptions, Redemptions, Side Pockets](#subscriptions)
4. [Prime Brokerage](#prime-brokerage)
5. [Tri-Party Repo](#tri-party)
6. [Securities Lending](#sec-lending)
7. [Margin Financing](#margin-financing)
8. [Leverage Measurement](#leverage)
9. [VaR Computation](#var)
10. [Expected Shortfall](#es)
11. [VaR Backtesting](#var-backtesting)
12. [Stress Testing](#stress)
13. [Reverse Stress Testing](#reverse-stress)
14. [Concentration Risk](#concentration)
15. [Liquidity Risk](#liquidity)
16. [Funding vs Market Liquidity](#funding-market)
17. [Counterparty Risk](#counterparty)
18. [Wrong-Way Risk](#wrong-way)
19. [Operational Risk](#operational)
20. [Cyber Risk](#cyber)
21. [Compliance — MiFID II](#mifid)
22. [Compliance — SEC](#sec)
23. [Compliance — AIFMD](#aifmd)
24. [Tax Considerations](#tax)
25. [Fund Accounting and NAV](#nav)
26. [Performance Attribution](#attribution)
27. [Risk Decomposition](#risk-decomp)
28. [Optimal Capital Allocation](#allocation)
29. [Drawdown Management](#drawdown)
30. [Investor Reporting](#investor-reporting)
31. [Cross-Fund Hedging](#cross-fund)
32. [Crisis Management](#crisis)
33. [Risk System Architecture](#risk-system)
34. [Code Examples](#code)
35. [Case Studies](#cases)
36. [Reality Checks](#reality-checks)
37. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

The hedge fund industry manages ~$5 trillion globally. Risk management is the central operational function for any non-trivial fund. The math (VaR, ES, scenarios) is the public face; the engineering (data pipelines, real-time computation, integration with execution and PMs) is the unspoken backbone.

This document covers what a CRO (Chief Risk Officer) of a $1-5B fund needs to know. Topics span quantitative (VaR computations) and operational (compliance, custody, fund administration). Documents 200, 211 cover the underlying math; here we focus on the *operations* of running a fund.

---

## Fund Structure

### Master-Feeder

- Master fund holds investments.
- Feeder funds (offshore for tax-exempt; domestic for US taxables) feed capital to master.

### Onshore vs Offshore

- **Onshore (Delaware LP)**: US investors.
- **Offshore (Cayman, BVI, Bermuda)**: tax-exempt and non-US investors.

### Side Pockets

Illiquid assets segregated. Investors can't redeem the side pocket; LP-style rules.

### GP/LP Structure

- **GP (General Partner)**: management company. Receives fees.
- **LP (Limited Partner)**: investors.

### Reality Check — Structure Drives Compliance

Each domicile has different regulatory regime. US LP requires SEC registration if AUM > $150M. Cayman master requires CIMA registration. Compliance burden scales with fund size and structure.

---

## Subscriptions, Redemptions, Side Pockets

### Subscriptions

Investor commits capital. Subscription dates monthly or quarterly.

### Redemptions

Investor withdraws. Notice required (30-90 days). Lockup periods (1-3 years).

### Gates

If redemption requests exceed % of AUM, gate caps redemptions. Designed to prevent fire-sales.

### Side Pockets

Illiquid investments segregated. Subject to separate redemption rules.

### Side Letters

Negotiated terms with specific investors. Can include:
- MFN (most-favored nation) clauses.
- Lower fees.
- Priority access in side pockets.
- Special reporting.

---

## Prime Brokerage

Prime brokers provide:
- **Custody**: hold securities.
- **Margin financing**: lend cash for leverage.
- **Securities lending**: enable shorts.
- **Reporting**: consolidated positions and P&L.
- **Trading platform**: execution venues.

### Top Prime Brokers

| PB | Strength |
|---|---|
| Goldman Sachs | Equity, derivatives |
| Morgan Stanley | Equity, electronic trading |
| JPMorgan | Multi-asset, balance sheet |
| Citi | International |
| Barclays | European, fixed income |
| BNP Paribas | European |
| Deutsche Bank | Multi-asset (post-2019 retreat) |

### Multi-Prime

Mid-size to large funds use multiple PBs:
- Diversification of counterparty risk.
- Better pricing leverage.
- Specialized capabilities per PB.

### Reality Check — PB Counterparty Risk

Lehman bankruptcy 2008: hedge funds with assets at Lehman PB had assets tied up for years. Even with segregation rules, recovery slow.

Post-2008: regulatory protections improved. But concentration with one PB remains risk.

---

## Tri-Party Repo

Repo settled through agent (BNY Mellon, JPM):
- Agent holds collateral.
- Agent monitors collateral value daily.
- Agent margin calls counterparty.

Reduces operational complexity and bilateral counterparty risk.

### General Collateral (GC) vs Specials

- **GC**: any acceptable security as collateral. Standard terms.
- **Specials**: specific security in demand. Tighter terms, lower rate.

---

## Securities Lending

Borrow securities for short-selling.

### Mechanics

1. Lender (asset manager, ETF) lends shares.
2. Borrower posts cash collateral (~102% of value).
3. Lender invests cash collateral; pays rebate to borrower.
4. Borrower returns shares; receives cash collateral back.

### Borrow Rates

- **GC** (easy-to-borrow): rebate close to fed funds.
- **Specials** (hard-to-borrow): lower or negative rebate.
- **Hard-to-borrow**: rebate -50% APY or worse.

### Recall Risk

Lender can recall shares. Forces short to cover at potentially adverse price.

### Reality Check — Borrow Costs Matter

For a 10% short position with 5% borrow cost: 50bp drag annually. Significant for small-edge strategies.

---

## Margin Financing

Borrowed against collateral to lever positions.

### Initial Margin

Required to open position. For:
- US equity (Reg T): 50% IM.
- Portfolio margin: lower (based on net risk).
- Futures: typically 5-15% IM.
- Crypto: highly variable (1-50%).

### Maintenance Margin

Ongoing requirement. Below this, margin call.

### Variation Margin

Daily mark-to-market settlement.

### Cross-Margining

Across multiple positions/products. Reduces total IM via offsetting risk.

---

## Leverage Measurement

### Gross Leverage

(Long + |Short|) / Capital. Total exposure relative to equity.

### Net Leverage

(Long - Short) / Capital. Directional exposure.

### Examples

- Long-only fund: gross = net = 1.0.
- Equity market-neutral: gross = 4.0, net = 0.0 (4x gross from leverage).
- Macro fund: gross = 2.0, net = 1.5 (mostly directional).

### Regulatory Leverage

- Form PF (US): includes adjustments for risk-equivalent.
- AIFMD (EU): commitments approach.
- Different regulators, different metrics.

### Reality Check — Leverage Hidden Risks

Gross leverage can hide:
- Concentration in one asset class.
- Correlation between long and short legs.
- Tail-risk exposure.

Risk-adjusted leverage (using factor models, VaR contributions) more meaningful.

---

## VaR Computation

Value-at-Risk: max loss at given confidence over given horizon.

### Historical VaR

Empirical quantile of historical returns.

```python
def historical_var(returns, alpha=0.99):
    """Historical VaR."""
    return -np.quantile(returns, 1 - alpha)
```

Pros: model-free.
Cons: limited by sample size; tail events undersampled.

### Parametric VaR

Assume distribution (Gaussian). VaR = -μ + z × σ.

```python
def parametric_var(mu, sigma, alpha=0.99):
    return -mu + norm.ppf(alpha) * sigma
```

Cons: thin-tailed; underestimates real VaR.

### Monte Carlo VaR

Simulate from model, compute quantile.

Best for non-linear portfolios (options, structured products).

### EVT VaR

Document 206 covers. Best for tail estimation.

---

## Expected Shortfall

Average loss conditional on exceeding VaR.

### Formula

$$
ES_\alpha = \mathbb{E}[L \mid L > VaR_\alpha].
$$

### Properties

- **Sub-additive**: ES of sum ≤ sum of ES (unlike VaR).
- More information about tail.
- Coherent risk measure.

### Use

- Regulatory: Basel III moving from VaR to ES.
- Internal: ES preferred for tail-aware allocations.

---

## VaR Backtesting

### Kupiec POF

Count exceedances. Compare to expected count.

### Christoffersen

Tests independence of exceedances (no clustering).

### Basel Traffic Light

| Exceedances over 250 days | Color | Action |
|---|---|---|
| 0-4 | Green | Normal |
| 5-9 | Yellow | Increased multiplier |
| 10+ | Red | Investigation |

### Reality Check — Backtest Power

VaR backtesting has low power. 250 days at 99% VaR has expected 2.5 exceedances. Detecting model error requires hundreds of observations.

---

## Stress Testing

Apply historical or hypothetical scenarios:

### Historical Scenarios

- 1987 crash.
- 1998 LTCM.
- 2008 financial crisis.
- 2020 COVID.
- 2022 LDI crisis.

For each, compute portfolio P&L.

### Hypothetical Scenarios

- Equity -30%, vol +15.
- Rate +200bp.
- USD +20%.
- Sector-specific shocks.

### Multi-Asset Scenarios

Coherent shocks across asset classes:
- "Risk-off": equity down, vol up, rates down, USD up.
- "Inflation": rates up, equity flat, gold up.

```python
def stress_test(positions, scenario_pnl):
    """Apply scenario to positions."""
    total_pnl = (positions * scenario_pnl).sum()
    return total_pnl

scenarios = {
    'equity_-30': {'AAPL': -0.30, 'MSFT': -0.30, 'AMZN': -0.30},
    'rates_+200bp': {'US10Y': -0.10, 'HYG': -0.05},
    # ...
}
```

---

## Reverse Stress Testing

What scenario would cause X% loss?

Approach:
- Search over plausible scenarios.
- Find one that breaches threshold with maximum probability.

Useful for:
- Identifying hidden vulnerabilities.
- Stress test design.
- Capital adequacy.

---

## Concentration Risk

Concentrated positions increase tail risk.

### Single-Name

Position size > X% of capital triggers monitoring.

### Sector / Country / Factor

Sector exposure > Y% of capital. Country, factor exposures similarly limited.

### Counterparty

Exposure to single counterparty > Z% of capital. Diversification across PBs.

### Limits

Typical limits:
- Single name: 2-5% of capital.
- Sector: 15-25%.
- Country: 25-40%.
- Counterparty: depends on credit rating.

---

## Liquidity Risk

Two dimensions:

### Asset Liquidity

Days to liquidate position without market impact:
- Major equity: 1-5 days for 100% of position.
- Small-cap: 10-50 days.
- Distressed: 30+ days.

### Funding Liquidity

Available funding for positions:
- Subscriptions/redemptions.
- Margin calls.
- Counterparty financing.

### Mismatch Risk

If asset liquidity > redemption notice, fund cannot meet redemptions in stress.

### Liquidity Stress Tests

Simulate redemption scenarios:
- 25% redemption in one quarter.
- Combined with market stress.
- Compute days-to-meet-redemption per asset.

### Reality Check — 2008 Liquidity

Many funds gated or suspended in 2008. Asset liquidity collapsed; redemption requests spiked. Mismatch caused failures.

---

## Funding vs Market Liquidity

Brunnermeier-Pedersen (2009): funding and market liquidity reinforce each other.

- Less funding → forced selling → reduced market liquidity.
- Reduced liquidity → wider spreads → reduced funding (PB raises margin).

Cycle can spiral: 2008, March 2020.

### Mitigation

- Maintain unencumbered cash buffer.
- Diversify funding sources.
- Stress test under correlated funding/market scenarios.

---

## Counterparty Risk

Risk that counterparty fails to deliver/pay.

### Sources

- PB default.
- OTC derivative counterparty default.
- Repo counterparty.
- Settlement (Herstatt) risk.

### CVA (Credit Value Adjustment)

PV of potential losses from counterparty default:

$$
CVA = (1 - R) \int_0^T E[\text{exposure}(t)] \cdot \lambda(t) \cdot D(0, t) dt.
$$

### DVA (Debit Value Adjustment)

Counterparty's CVA against you. Effectively reduces your liability.

### Bilateral CVA

Net CVA - DVA.

---

## Wrong-Way Risk

Exposure to counterparty increases as counterparty deteriorates.

### Examples

- Long CDS on counterparty's parent: if counterparty defaults, CDS pays but counterparty cannot deliver.
- Short USD vs EM currency CDS: USD strengthens often coincides with EM stress.

### Mitigation

- Avoid wrong-way correlations.
- Cap exposure to wrong-way counterparties.
- Use central clearing where possible.

---

## Operational Risk

Risk from systems, processes, people.

### Categories

- Internal fraud.
- External fraud.
- Errors (fat finger, mis-routing).
- System failures.
- Business disruption.
- Legal compliance.

### Controls

- Four-eyes principle (dual approval).
- Segregation of duties.
- Limits on individual authority.
- Audit trails.
- Disaster recovery.

### Famous Failures

- **Knight Capital 2012**: $440M loss from deployment error.
- **Société Générale 2008**: Kerviel $7B fraud.
- **Amaranth 2006**: $6B loss from concentrated nat gas trade.

---

## Cyber Risk

Increasingly material for hedge funds:
- Phishing attacks.
- Ransomware.
- Insider threats.
- Supply chain compromise (vendor hack).
- DDoS.

### Defense

- Multi-factor authentication.
- Network segmentation.
- Endpoint security.
- Regular penetration testing.
- Incident response plans.
- Cyber insurance.

---

## Compliance — MiFID II

EU regulation, 2018:
- **Best execution**: prove favorable client outcome.
- **Transaction reporting**: ARM (Approved Reporting Mechanism).
- **Position limits**: commodity derivatives.
- **Inducement rules**: research unbundling.
- **Algorithmic trading governance**: RTS 6.

### Compliance Costs

For mid-size hedge fund: $1-5M annually. Heavy administrative burden.

---

## Compliance — SEC

US regulation:
- **Form ADV**: registration, fee structure, conflicts.
- **Form PF**: hedge fund-specific reporting (>$150M AUM).
- **Custody Rule**: independent custodian or audit.
- **Marketing Rule**: 2022 update on advertising.
- **Pay-to-Play**: political contribution restrictions.

### CFTC

For commodity-trading entities. Additional reporting + position limits.

---

## Compliance — AIFMD

EU directive, 2013 (updated AIFMD II 2024):
- **AIFM authorization**: for managers of EU funds.
- **Depositary**: independent custodian.
- **Leverage limits**: regulator can impose.
- **Disclosure**: pre-investment.
- **Liquidity management**: tools and reporting.

---

## Tax Considerations

### US

- Hedge fund partnership: pass-through taxation.
- 20% performance fee historically taxed at long-term capital gains rate (with 1-year holding); changed in 2017 to require 3-year hold for LP-allocated gains.
- Carried interest debate.

### International

- Treaty optimization for cross-border investments.
- Withholding tax recovery.
- K-1 reporting for US investors in offshore feeder.

### Custody

- US: custodial bank (SS&C, BNY, Northern Trust).
- Offshore: similar.

---

## Fund Accounting and NAV

### NAV (Net Asset Value)

Total assets minus liabilities, divided by shares outstanding. Reported monthly typically.

### Calculation

1. Mark all positions to market.
2. Apply liquidity discounts to illiquid positions.
3. Subtract management fees, performance fees, expenses.
4. Divide by shares.

### Pricing

- Liquid: market quotes.
- Illiquid: model-based ("Level 2" or "Level 3" under FAS 157/ASC 820).

### Side-Pocket Pricing

Separate NAV. Reported separately to investors.

---

## Performance Attribution

### Brinson Decomposition

Decompose excess return:
- Allocation effect (overweight winning sector).
- Selection effect (picked good names within sector).
- Interaction effect.

### Factor Attribution

Decompose into factor returns + idiosyncratic:

$$
R = \alpha + \beta_M R_M + \beta_S R_S + \beta_V R_V + \cdots + \epsilon.
$$

Factors: market, size, value, momentum, quality, low-vol, etc.

### Risk-Attribution

Decompose risk into factor + idiosyncratic. Helps identify concentration.

---

## Risk Decomposition

For total portfolio variance:

$$
\sigma_p^2 = w^T \Sigma w.
$$

Decomposition:

- **Marginal contribution**: ∂σ_p / ∂w_i.
- **Component contribution**: w_i × marginal_i.
- **Percentage contribution**: component_i / σ_p.

```python
import numpy as np

def risk_decomposition(weights, cov_matrix):
    """Decompose portfolio risk."""
    sigma_p = np.sqrt(weights @ cov_matrix @ weights)
    marginal = (cov_matrix @ weights) / sigma_p
    component = weights * marginal
    pct = component / sigma_p
    return {'marginal': marginal, 'component': component, 'pct': pct}
```

---

## Optimal Capital Allocation

### Markowitz Under Uncertainty

Standard MV optimization:

$$
\max_w \mu^T w - \frac{\lambda}{2} w^T \Sigma w.
$$

Sensitivity to inputs (especially μ): instable.

### Robust Approaches

- **Shrinkage** (Ledoit-Wolf for Σ).
- **Bayesian** (Black-Litterman; document 82).
- **Risk parity** (allocate by risk contribution; document 42).

### HRP (Hierarchical Risk Parity)

López de Prado (2016): cluster assets, allocate hierarchically. Document 81.

### Reality Check — MV Issues

Pure MV optimization "concentrates errors": small mis-estimation in μ → large weight differences. Robust methods more stable.

---

## Drawdown Management

### Risk-Reduction Triggers

Pre-defined drawdown levels trigger risk reduction:
- 5% drawdown: review.
- 10%: reduce risk by 50%.
- 15%: reduce to 25%.
- 20%: halt new positions.

### Dynamic Position Sizing

Scale positions based on:
- Recent realized vol.
- Drawdown levels.
- Performance vs benchmark.

### Reality Check — Drawdown Discipline

Many funds fail to enforce risk reduction in real-time. Emotional bias to "wait it out." Pre-committed rules essential.

---

## Investor Reporting

### Monthly

NAV, returns, exposure summary. Typically mid-month for prior.

### Quarterly

- Audited financial statements.
- Risk metrics: VaR, exposure breakdowns.
- Top positions.
- Capacity / AUM trends.

### Ad-Hoc

- Major P&L moves.
- Strategy changes.
- Material events.

---

## Cross-Fund and Cross-Vehicle Hedging

For firms running multiple funds:
- Net exposure at firm level.
- Hedge net (not gross).
- Capital efficiency.

### Reality Check — Conflicts

Different funds have different investors. Cross-hedging requires careful documentation and disclosure.

---

## Crisis Management

### Run on the Fund

Sudden mass redemption requests:
- Cash buffer first.
- Liquidate liquid positions.
- Apply gates if necessary.
- Communicate transparently.

### Financing Freeze

PB cuts off financing:
- Activate backup PB.
- Reduce leverage.
- Sell assets.

### Counterparty Default

Activate ISDA close-out provisions. Calculate exposure. Recover collateral.

### Crisis Playbooks

Pre-written procedures for:
- 50%+ daily P&L move.
- Major counterparty failure.
- Mass redemption.
- Cyber breach.
- Key person departure.

---

## Risk System Architecture

### Real-Time vs End-of-Day

- **Real-time**: position limits, concentration, intraday VaR.
- **EOD**: full risk computation, full P&L attribution.

### Integration

Risk system must integrate with:
- Order management system.
- Execution platforms.
- Position keeping.
- P&L systems.
- Reporting systems.

### Data Pipeline

- Source: market data, position data, P&L data, news, etc.
- Pipeline: validation, transformation.
- Storage: time-series + relational.
- Access: dashboards + ad-hoc queries.

### Reality Check — Risk System Build

Build vs buy:
- **Build**: tailored, expensive (years).
- **Buy**: BlackRock Aladdin, Bloomberg PORT, MSCI RiskMetrics. Standardized.

Most large hedge funds combine: vendor for standard metrics, custom for proprietary measures.

---

## Code Examples

### Historical VaR

```python
import numpy as np

def historical_var(returns, alpha=0.99):
    return -np.quantile(returns, 1 - alpha)

def historical_es(returns, alpha=0.99):
    var = historical_var(returns, alpha)
    return -returns[returns <= -var].mean()
```

### Parametric VaR

```python
from scipy.stats import norm

def parametric_var(mu, sigma, alpha=0.99):
    return -mu + norm.ppf(alpha) * sigma
```

### Factor Decomposition

```python
import numpy as np

def factor_var(weights, factor_loadings, factor_cov, idio_var):
    """VaR decomposition by factor."""
    factor_exposure = factor_loadings.T @ weights
    factor_var = factor_exposure.T @ factor_cov @ factor_exposure
    idio_total = (weights**2 * idio_var).sum()
    total_var = factor_var + idio_total
    return {
        'factor_var': factor_var,
        'idio_var': idio_total,
        'total_var': total_var,
        'factor_share': factor_var / total_var
    }
```

### CVaR (CVaR Optimization)

Linear programming form for CVaR-minimizing portfolio:

```python
from scipy.optimize import linprog

def cvar_min_portfolio(returns, target_return, alpha=0.95):
    """Minimize CVaR for given target return."""
    # Standard CVaR optimization (Rockafellar-Uryasev 2000)
    # ... (uses LP solver)
    pass
```

---

## Case Studies

### LTCM 1998

- Massive leverage (~30:1).
- Convergence trades.
- Russia default → liquidity crunch.
- Capital exhaustion despite "convergence."
- Bailed out by 14 banks (Fed organized).

Lessons:
- Leverage amplifies tail risk.
- Convergence trades have negative skew.
- Capital exhaustion is real even for "smart money."

### Amaranth 2006

- $9B fund.
- Concentrated nat gas spread bet.
- Lost $6B in weeks.

Lessons:
- Concentration kills.
- Position size limits matter.
- Energy markets can move violently.

### Lehman 2008

- PB at Lehman: assets tied up post-bankruptcy.
- Counterparty losses for hedge funds with Lehman exposure.

Lessons:
- Diversify counterparties.
- Even Tier-1 banks can fail.

### Archegos 2021

- Family office (not technically hedge fund).
- Massive equity swaps via multiple PBs.
- Concentrated Chinese tech / media positions.
- Margin call cascade → $20B+ loss to PBs.

Lessons:
- Hidden leverage via swaps.
- PB visibility issues.
- Concentration risk amplified by leverage.

### Melvin Capital 2021

- $13B short on GME and other meme stocks.
- WSB squeeze pushed losses to 50%+.
- Citadel and Point72 invested $2.75B for stake.
- Wound down 2022.

Lessons:
- Crowded trades can be squeezed.
- Retail flow can move markets.
- Position size limits matter.

---

## Reality Checks

- **Model risk**: any single risk metric can mislead.
- **Black swans**: real risks live in the tail, not the body.
- **Liquidity is conditional**: liquid in calm, illiquid in crisis.
- **Regulatory landscape changing**: stay current.
- **Human judgment matters**: pure-model approach fails in regime change.

---

## Reference Tables, Cheat Sheets, Bibliography

### Key Risk Metrics

| Metric | Formula | Use |
|---|---|---|
| VaR_α | quantile(1-α) of L | Standard |
| ES_α | E[L \| L > VaR] | Tail-aware |
| Max DD | running max - low | Drawdown |
| Vol | std(returns) | Volatility |
| Beta | Cov/Var(market) | Market exposure |
| Sharpe | μ/σ | Risk-adj return |
| Sortino | μ/downside σ | Downside-adj |
| Calmar | annual ret / max DD | Drawdown-adj |

### Bibliography

- **Lo, A. (2008), *Hedge Funds: An Analytic Perspective*, Princeton.**
- **Jorion, P. (2007), *Value at Risk* (3rd ed.), McGraw-Hill.** Standard VaR text.
- **McNeil, A., Frey, R., Embrechts, P. (2015), *Quantitative Risk Management*, Princeton.** Comprehensive.
- **Stulz, R. (2003), *Risk Management & Derivatives*, Cengage.**
- **Crouhy, M., Galai, D., Mark, R. (2014), *The Essentials of Risk Management*, McGraw-Hill.**
- **Hull, J. (2018), *Risk Management and Financial Institutions* (5th ed.), Wiley.**
- **Brunnermeier, M. and Pedersen, L. (2009), "Market Liquidity and Funding Liquidity", *Review of Financial Studies*.**
- **Rockafellar, R. and Uryasev, S. (2000), "Optimization of Conditional Value-at-Risk", *J. Risk*.**

### Cross-References

- Document 200 — Stochastic Calculus.
- Document 206 — EVT.
- Document 207 — Copulas.
- Document 211 — Backtesting.
- Document 81 — HRP.
- Document 82 — Black-Litterman.
- Document 42 — Risk Parity.

---

*End of document 218. ~1,400 lines.*
