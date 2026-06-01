# 120 - Ultimate Oscillator Consensus (UO)

**Volume:** 120 of 100
**Strategy Type:** Mean Reversion / Divergence
**Risk Profile:** Medium
**Mathematical Basis:** Weighted Average of 3 Buying Pressure Oscillators

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Consensus](#2-the-theory-consensus)
    * 2.1. Why single timeframes lie.
    * 2.2. Larry Williams' 7-14-28 Rule.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Setup (False signals filtering).
    * 3.2. The Divergence Buy.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Buying Pressure ($Close - TrueLow$).
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Complex calculation.
    * 5.2. Rust: Struct approach.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 120** uses the **Ultimate Oscillator (UO)** by Larry Williams.
Most oscillators (RSI, Stochastic) look at one timeframe (e.g., 14).
If the 14-period cycle is dominant, they work. If the 28-period cycle is dominant, they fail.
UO looks at **Three Timeframes** (Short, Medium, Long) simultaneously.
It creates a weighted consensus.
It only signals a trade when Short, Medium, AND Long-term momentum align at an extreme.

---

# 2. The Theory: Consensus

### 2.1. The Timeframe Conflict

Often, the 5-min chart says Buy, but the 15-min says Neutral, and the 1-hour says Sell.
Trading based on just one is gambling.
UO combines them (typically 7, 14, 28 periods) into a single 0-100 metric.
It forces the different "personalities" of the market to agree before GOLIATH pulls the trigger.

---

# 3. The Strategy Rules

### 3.1. The Buy Signal (Strict)

1. **Bullish Divergence:** Price makes Lower Low, UO makes Higher Low.
2. **Oversold:** The lowest low in the UO was < 30.
3. **Trigger:** UO rises above the high of the divergence period.
*(This prevents catching a falling knife. We wait for the "Break" of the divergence).*

### 3.2. The Sell Signal (Strict)

1. **Bearish Divergence:** Price Higher High, UO Lower High.
2. **Overbought:** Highest UO High was > 70.
3. **Trigger:** UO breaks below the divergence low.

---

# 4. Mathematical Derivation

$$ BP = Close - \min(Low, Close_{prev}) $$
$$ TR = \max(High, Close_{prev}) - \min(Low, Close_{prev}) $$
$$ Avg7 = \sum BP_7 / \sum TR_7 $$
$$ Avg14 = \sum BP_{14} / \sum TR_{14} $$
$$ Avg28 = \sum BP_{28} / \sum TR_{28} $$
$$ UO = 100 \times \frac{4 \times Avg7 + 2 \times Avg14 + 1 \times Avg28}{4+2+1} $$

Short term gets weight 4. Medium 2. Long 1.
This keeps it responsive but anchored.

---

# 5. Implementation

### 5.1. Python

*(From Indicator 120 Source)*

```python
def ultimate_oscillator(high, low, close, p1=7, p2=14, p3=28):
    bp = close - pd.concat([low, close.shift(1)], axis=1).min(axis=1)
    tr = pd.concat([high, close.shift(1)], axis=1).max(axis=1) - pd.concat([low, close.shift(1)], axis=1).min(axis=1)
    
    avg1 = bp.rolling(p1).sum() / tr.rolling(p1).sum()
    avg2 = bp.rolling(p2).sum() / tr.rolling(p2).sum()
    avg3 = bp.rolling(p3).sum() / tr.rolling(p3).sum()
    
    return 100 * (4*avg1 + 2*avg2 + 1*avg3) / 7
```

---

# 7. Conclusion

Strategy 120 is the **Judge**.
It listens to the arguments from the Swing Trader (7), the Position Trader (14), and the Investor (28).
Only when the evidence is overwhelming (Consensus Divergence) does it issue a verdict.
This drastically reduces false signals compared to a standard RSI, making it ideal for automated reversal trading where false positives can bleed the account.
