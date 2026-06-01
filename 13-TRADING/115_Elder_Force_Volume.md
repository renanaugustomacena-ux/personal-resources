# 115 - Elder Force Volume (EFI)

**Volume:** 115 of 100
**Strategy Type:** Volume-Price Confirmation
**Risk Profile:** Low (Validates moves)
**Mathematical Basis:** Newton's Second Law ($F = m \times a$) applied to Markets.

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Force = Volume x Change](#2-the-theory-force--volume-x-change)
    * 2.1. Dr. Alexander Elder's Triple Screen logic.
    * 2.2. Validating Breakouts.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The 2-Day EMA Pullback (Tactical).
    * 3.2. The 13-Day EMA Trend (Strategic).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. $V \times (C - C_{prev})$.
5. [Implementation: Production Grade](#5-implementation-production-grade)
    * 5.1. Python: Raw Calculation.
    * 5.2. Rust: Integration.
6. [Risk Management](#6-risk-management)
7. [Conclusion](#7-conclusion)

---

# 1. Executive Summary

**Strategy 115** relies on the **Elder Force Index (EFI)**.
Price tells you *what* the market did. Volume tells you *how hard* it tried.
EFI combines them.
$Force = Volume \times (Close_{today} - Close_{yesterday})$.
It is the ultimate **Lie Detector**.
A price breakout on low volume has Low Force (Fake).
A price drop on massive volume has High Negative Force (Real).

---

# 2. The Theory: Force = Volume x Change

### 2.1. Market Physics

Alexander Elder treated markets like physical objects.
To move a heavy object (Price), you need Force (Volume).
If Price moves without Volume, it has no momentum and will snap back (Mean Reversion).
If Price moves *with* Volume, it has Inertia and will continue (Trend).

---

# 3. The Strategy Rules

### 3.1. The 2-Period Spike (Buying Pullbacks)

* **Context:** Long-term Trend is UP (EMA 13 of EFI > 0).
* **Setup:** 2-Period EFI drops below Zero (Short-term selling pressure).
* **Trigger:** 2-Period EFI turns back Up.
* **Action:** Buy.
* **Logic:** We are buying a wash-out (pullback) within a confirmed accumulation phase.

### 3.2. Divergence

* **Bearish:** Price makes New High, but EFI(13) makes Lower High. (Bulls are shouting, but they have no money left). -> **SELL**.

---

# 4. Mathematical Derivation

$$ RawForce = Volume_t \times (Close_t - Close_{t-1}) $$
$$ EFI(13) = EMA(RawForce, 13) $$

---

# 5. Implementation

### 5.1. Python

*(From Indicator 115 Source)*

```python
def efi(close, volume, period=13):
    raw_force = volume * close.diff()
    return raw_force.ewm(span=period, adjust=False).mean()
```

---

# 7. Conclusion

Strategy 115 is the **Validator**.
GOLIATH never trusts Price alone. Price can be manipulated by a single large order.
Volume cannot be faked easily.
Strategy 115 ensures that GOLIATH puts capital only behind moves that are supported by the "Masses" (Volume), increasing the statistical probability of follow-through.
