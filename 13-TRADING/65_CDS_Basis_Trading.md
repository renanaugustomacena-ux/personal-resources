# 65 - CDS Basis & Credit Spreads: The Canary

**Volume:** 65 of 100
**Strategy Type:** Credit / Fixed Income Arbitrage / Macro
**Risk Profile:** Default Event / Liquidity Crisis / Basis Widening
**Mathematical Basis:** Merton Model ($DistanceToDefault$) & No-Arbitrage Basis

> "Stocks are the dream. Credit is the wake-up call. When the bond guys stop lending, the party is over."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Credit as a Truth Teller](#2-the-theory-credit-as-a-truth-teller)
    * 2.1. The High Yield Spread (HY-OAS): The Milken Legacy.
    * 2.2. The CDS Basis: Friction between Bond (Cash) and CDX (Synthetic).
    * 2.3. Structural Models: Equity as a Call Option on Assets (Merton).
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Macro Rule: The "Blowout" (OAS > 800bps). Buy Distressed.
    * 3.2. Micro Rule: The "Negative Basis" (Bond Cheap / CDS Rich). Arbitrage.
    * 3.3. Equity Signal: Divergence between SPX and HYG.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. OAS Calculation (Stripping the Call Option).
    * 4.2. Basis Formula: $S_{CDS} - Z_{spread}$.
    * 4.3. Distance to Default (Merton).
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. 1980s Milken Junk Bond Era: Mispricing of Default Risk.
    * 5.2. 2008 Basis Compression: Negative Basis reached -500bps.
    * 5.3. 2020 Covid Flush: OAS hit 1100bps. The precise bottom for Equities.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (FRED HY-OAS, Regime Detection, Basis Monitor).
    * 6.2. Rust (Merton Model Solver, Z-Spread Iterator).
7. [Risk Management](#7-risk-management)
    * 7.1. Cheapest-to-Deliver (CTD) in CDS Settlement.
    * 7.2. Repo Squeezes in Basis Trades.
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 65** combines the **Macro signal** of Credit Spreads (Indicator 067) with the **Micro arbitrage** of the CDS Basis (Strategy 65).

* **Macro:** We use the spread of High Yield Bonds over Treasuries (HY-OAS) as the ultimate "Fear Gauge". It predicts recessions better than stocks.
* **Micro:** We trade the dislocations between the Cash Bond market and the Synthetic CDS market to earn risk-free(ish) spreads.

**The Edge:**
Credit markets are dominated by "Paranoid Money" (Lenders who just want their principal back). They react faster to risk than "Optimistic Money" (Equity shareholders). We listen to the paranoids.

---

# 2. The Theory

## 2.1. HY-OAS (Option Adjusted Spread)

Corporate bonds yield more than Treasuries to compensate for:

1. **Default Risk:** The chance the company goes bust.
2. **Liquidity Risk:** Harder to sell.
3. **Call Risk:** Issuer can buy it back.
The **OAS** removes the Call Risk, leaving pure Default/Liquidity premium.

* **< 350bps:** Boom. Risk On.
* **> 800bps:** Crisis. Risk Off.

## 2.2. The CDS Basis

The difference between the cost of insurance (CDS) and the premium paid by the bond (Z-Spread).
Ideally Zero.
Often Negative (Bond Yield > CDS Cost) due to balance sheet constraints.

## 2.3. Merton Model

Robert Merton (Nobel Prize) proved:

* Debt = Risk Free Bond - Put Option on Assets.
* Equity = Call Option on Assets (Strike = Debt).
* Credit Spreads are just implied volatility of the firm's assets.

---

# 3. The Strategy Rules

## 3.1. Macro Regime (The Switch)

* **Input:** ICE BofA US High Yield Index OAS.
* **Signal:** If OAS crosses above 200-Day Moving Average $\to$ **EXIT LEVERAGE.**
* **Signal:** If OAS > 8.0% $\to$ **PREPARE TO BUY.** (Blood in the streets).

## 3.2. Negative Basis Arb (The Trade)

* **Scan:** Investment Grade Bonds.
* **Condition:** Cash Bond Yield (Asset Swapped) > CDS Premium + Funding Cost.
* **Execution:** Buy Bond, Buy CDS. Lock in spread.
* **Holding Period:** Until maturity or convergence.

## 3.3. The Equity/Credit Divergence

* **Scenario:** S&P 500 makes New High. HYG (Junk Bond ETF) makes Lower High.
* **Diagnosis:** "Hollow Rally". Driven by multiple expansion, not fundamental health.
* **Action:** Short Equities / Long Volatility.

---

# 4. Mathematical Derivation

## 4.1. The Basis

$$ Basis = CDS_{spread} - Z_{spread} $$
Ideally 0.
Significant if $|Basis| > 20bps$.

## 4.2. Merton Distance to Default (DD)

$$ DD = \frac{\ln(Value_{Assets} / Debt) + (\mu - 0.5\sigma^2)T}{\sigma \sqrt{T}} $$
Probability of Default $PD = N(-DD)$.
Credit Spread $\approx PD \times LossGivenDefault$.

---

# 5. Historical Case Studies

## 5.1. 1980s Milken

Michael Milken realized that a portfolio of Junk Bonds yielding 15% would default at 3%, creating a net 12% return (vs 8% Treasuries).
He arbitraged the "fear premium" of unrated companies.

## 5.2. 2008 Lehman

Banks needed cash. They sold bonds.
Bonds crashed (Yields spiked).
CDS spreads rose, but not as much.
**Basis = CDS (500) - Bond (1000) = -500bps.**
Arbitrageurs with cash bought the bond, bought the CDS, and locked in 5% risk-free.

## 5.3. 2020 Covid

High Yield Spreads blew out to 11%.
The Fed announced they would buy Corporate Bonds (HYG).
Spreads collapsed instantly.
The "Signal" to buy stocks was the peak in Spreads.

---

# 6. Implementation: Production Grade

## 6.1. Python (Analysis)

```python
import pandas_datareader.data as web
import pandas as pd
import numpy as np

def analyze_credit_regime():
    # Fetch HY OAS
    df = web.DataReader('BAMLH0A0HYM2', 'fred', start='2000-01-01')
    df.columns = ['OAS']
    
    # Moving Average Logic
    df['SMA_200'] = df['OAS'].rolling(200).mean()
    
    current = df['OAS'].iloc[-1]
    sma = df['SMA_200'].iloc[-1]
    
    if current > 8.0:
        return "CRISIS_BUY (Deep Value)"
    elif current > sma:
        return "RISK_OFF (Spreads Widening)"
    elif current < 3.5:
        return "EUPHORIA (Caution long term, but trend is up)"
    else:
        return "NEUTRAL"
        
def check_basis(bond_yield, cds_spread, risk_free):
    z_spread = bond_yield - risk_free
    basis = cds_spread - z_spread
    return basis
```

## 6.2. Rust (Merton Solver)

```rust
use statrs::distribution::{Normal, Univariate};

pub struct FirmStruct {
    equity: f64,
    debt: f64,
    volatility: f64,
}

impl FirmStruct {
    pub fn distance_to_default(&self, risk_free: f64, time: f64) -> f64 {
        let assets = self.equity + self.debt; // Approx
        let num = (assets / self.debt).ln() + (risk_free - 0.5 * self.volatility.powi(2)) * time;
        let den = self.volatility * time.sqrt();
        num / den
    }
    
    pub fn implied_spread(&self) -> f64 {
        let dd = self.distance_to_default(0.04, 1.0);
        let n = Normal::new(0.0, 1.0).unwrap();
        let prob_default = n.cdf(-dd);
        prob_default * 0.60 // Assume 40% recovery -> 60% LGD
    }
}
```

---

# 7. Risk Management

## 7.1. Repo Squeeze

If trading Positive Basis (Short Bond / Sell CDS), you must borrow the bond.
If the bond becomes "Special" (Repo rate spikes to 5%), your profit vanishes.
**Rule:** Only trade Positive Basis in highly liquid, general collateral bonds.

## 7.2. Counterparty Risk

You buy CDS from Bank X. Bank X acts as your insurer.
If Bank X fails (Lehman), your bond defaults AND your insurance is gone.
Double Jeopardy. Requires collateral posting daily.

---

# 8. Conclusion

**Strategy 65** listens to the "Canary in the Coal Mine".
Credit Spreads are the most accurate recession predictor we have.
By combining this macro view with the micro-precision of **Basis Trading**, GOLIATH extracts value from the fear and friction of the bond market.
When Spreads are wide, we lend. When Spreads are tight, we seek safety.
It is the strategy of the Capitalist.
