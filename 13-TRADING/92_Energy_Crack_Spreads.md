# 92 - Energy Crack Spreads & Causal Inference

**Volume:** 92 of 100
**Strategy Type:** Commodities / Causal AI / Supply Chain Economics
**Risk Profile:** Geopolitical Shocks / Regulatory Changes
**Mathematical Basis:** 3:2:1 Crack Spread & Causal Inference ($P(y | do(x))$) / Granger Causality

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context](#2-historical-context)
    * 2.1. The Refinery Margin (Crack Spread).
    * 2.2. Judea Pearl & The Ladder of Causation.
3. [The Theory: Physics \u0026 Causality](#3-the-theory-physics--causality)
    * 3.1. The 3:2:1 Ratio.
    * 3.2. Causal Inference (Indicator 094): Association vs Intervention.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Crack Spread Formula.
    * 4.2. Granger Causality.
    * 4.3. Structural Causal Models (SCM).
5. [The Strategy Rules](#5-the-strategy-rules)
    * 5.1. Mean Reversion Signal.
    * 5.2. Causal Logic (Validating the Driver).
    * 5.3. Execution \u0026 Contract Matching.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python: Crack Spread Calculator.
    * 6.2. Python: Granger Causality Tests.
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 92** trades the **Energy Crack Spread** (The Refiner's Profit Margin).
However, trading spreads based on simple correlation is dangerous because it ignores *why* the spread is moving.
We integrate **Causal Inference (Indicator 094)** to determine the *direction* of causality.

* Is Gasoline rising because Crude is expensive? (Cost Push $\rightarrow$ Spread Tightens).
* Is Crude rising because Gasoline demand is high? (Demand Pull $\rightarrow$ Spread Widens).
By using Granger Causality and Structural Causal Models, Strategy 92 filters out noise and trades only the fundamental "root causes" of energy price logic.

---

# 2. Historical Context

### 2.1. The Refinery Game

The Crack Spread (3 Crude $\to$ 2 Gas + 1 Heat) dictates the economics of companies like ExxonMobil.

* **Hurricane Harvey (2017):** Hit refineries. Crude fell (No buyers), Gasoline spiked (No supply). Spread exploded to \$30/bbl.
* **2015 Oil Crash:** Crude fell 70%, Gas fell less. Refiners made record profits.

### 2.2. Judea Pearl (2000) (Indicator 094)

Judea Pearl revolutionized statistics by introducing the **Ladder of Causation**.

1. **Association:** $P(y|x)$ (Seeing). Standard ML.
2. **Intervention:** $P(y|do(x))$ (Doing). Causal ML.
3. **Counterfactuals:** $P(y_x|x', y')$ (Imagining).
Algo trading is stuck at Level 1. Strategy 92 moves to Level 2.

---

# 3. The Theory: Physics \u0026 Causality

### 3.1. The 3:2:1 Ratio

$$ S_{321} = \frac{2 \times P_{Gas} \times 42 + 1 \times P_{Heat} \times 42 - 3 \times P_{Crude}}{3} $$
Buying the Spread = Long Products, Short Crude (Refining).
Selling the Spread = Short Products, Long Crude (Speculating).

### 3.2. Causal Inference (Indicator 094)

**Granger Causality:** $X$ causes $Y$ if past values of $X$ help predict $Y$ *beyond* past values of $Y$.
**Spurious Correlation Filter:** An ML model might find "Twitter Sentiment" predicts "Oil Price". A Causal test controls for "Global Liquidity". If the correlation vanishes, it was spurious. We trade only robust causal links.

---

# 4. Mathematical Derivation

### 4.1. Granger Causality (Time-Series)

$$ Y_t = \alpha + \sum \beta_i Y_{t-i} + \sum \gamma_i X_{t-i} + \epsilon_t $$
If $\gamma_i \neq 0$, $X$ Granger-causes $Y$.

### 4.2. Structural Causal Models (SCM)

Directed Acyclic Graphs (DAGs).
$do(X=x)$ represents an intervention.
We use **Instrumental Variables** to identify true causal effects in noisy market data.

---

# 5. The Strategy Rules

### 5.1. The Causal Filter (Indicator 094 Logic)

1. **Leader-Follower Map:** Run Granger tests on intraday CL (Crude) and RB (Gas) moves.
2. **Signal:**
    * If $RB \xrightarrow{Granger} CL$ (Gas leads Crude): **Demand Pull**. Refiners are buying crude to meet gas demand. **Bullish Spread.**
    * If $CL \xrightarrow{Granger} RB$ (Crude leads Gas): **Cost Push**. Crude shock (e.g., War). Refiners can't pass all costs. **Bearish Spread.**

### 5.2. Mean Reversion Logic (Strategy 92 Logic)

Calculte Z-Score of the Spread (252-day).

* If $Z < -2$ AND Causal Signal = Bullish $\rightarrow$ **Strong Buy**.
* If $Z > 2$ AND Causal Signal = Bearish $\rightarrow$ **Strong Sell**.

---

# 6. Implementation: Production Grade

### 6.1. Python: Crack Spread Calculator

*(From Strategy 92 Source)*

```python
def calculate_crack_spread(cl, rb, ho):
    # cl: Crude $/bbl
    # rb, ho: Products $/gal
    rb_bbl = rb * 42
    ho_bbl = ho * 42
    spread = (2 * rb_bbl + 1 * ho_bbl - 3 * cl) / 3
    return spread
```

### 6.2. Python: Granger Causality (From Indicator 094 Source)

```python
from statsmodels.tsa.stattools import grangercausalitytests
import pandas as pd

def check_causality_direction(df):
    """
    df columns: ['Crude', 'Gasoline']
    """
    # Test 1: Crude causes Gas
    res_cg = grangercausalitytests(df[['Gasoline', 'Crude']], maxlag=5, verbose=False)
    p_cg = res_cg[1][0]['ssr_ftest'][1]
    
    # Test 2: Gas causes Crude
    res_gc = grangercausalitytests(df[['Crude', 'Gasoline']], maxlag=5, verbose=False)
    p_gc = res_gc[1][0]['ssr_ftest'][1]
    
    if p_gc < 0.05 and p_cg > 0.05:
        return "GAS_LEADS" # Demand Pull
    elif p_cg < 0.05 and p_gc > 0.05:
        return "CRUDE_LEADS" # Cost Push
    else:
        return "UNCLEAR"
```

---

# 7. Risk Management

### 7.1. Causal Misidentification

Granger Causality assumes "Precedence = Causality". This is not always true (Barometer drops before Storm, but doesn't cause Storm).
**Mitigation:** Verify Granger results against a fundamental DAG (Domain Knowledge).
e.g., "Refinery Outage" MUST cause "Gas Price Spike".

### 7.2. Legging Risk

Executing 3 legs (CL, RB, HO) carries execution risk.
Use "Inter-Commodity Spread" (ICS) instruments on CME to trade the spread as a single package if available.

---

# 8. Conclusion

Strategy 92 is the **Engineer**.
It understands the machinery.
By adding **Causal Inference**, it stops guessing based on squiggly lines (Chart patterns) and starts understanding the mechanics of the engine (Supply Chain Causality).
It trades the "Why", not just the "What".
