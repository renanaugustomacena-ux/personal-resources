# 28 - Put-Call Parity Arbitrage: The Law of No Free Lunch

**Volume:** 28 of 50
**Strategy Type:** Arbitrage / Risk-Free Rates / Hard-to-Borrow
**Risk Profile:** Risk-Free (theoretically) / Execution Risk
**Mathematical Basis:** $C + PV(K) = P + S$

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Synthetic Equivalence](#2-the-theory-synthetic-equivalence)
    * 2.1. Call + Cash = Put + Stock
    * 2.2. Conversion and Reversal
    * 2.3. Box Spreads (Lending/Borrowing at Risk-Free Rate)
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Condition: Violation of Equality
    * 3.2. Hard-to-Borrow (HTB) Stocks: Puts become expensive
    * 3.3. Dividend Risk: Early Assignment
    * 3.4. The Trade: Buy the Cheap side, Sell the Expensive side
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Fundamental Equation: $C - P = S - K e^{-rT}$
    * 4.2. Interest Rate Component ($r$)
    * 4.3. Dividend Component ($D$)
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Tesla (TSLA) Short Squeeze: Puts trading at massive premium
    * 5.2. Box Spread Blowup (Robinhood "Infinite Money" Glitch)
    * 5.3. Dividend Arb: Capturing the ex-div discount
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Scanning Option Chains for Parity Violations
    * 6.2. Calculating Implied Interest Rate (Borrow Cost)
    * 6.3. Box Spread Calculator
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Jelly Roll" (Calendar Arbitrage)
    * 7.2. "Synthetic Long" (Leaping Stocks)
    * 7.3. "Conversion" (Market Maker strategy)
8. [Risk Management: Pin Risk](#8-risk-management-pin-risk)
    * 8.1. Expiration Risk: Stock closes exactly at strike.
    * 8.2. Assignment Risk: Short Call assigned early before ex-dividend.
    * 8.3. Execution Legging: Hitting bids instantly.
9. [Conclusion: The Foundation of Pricing](#9-conclusion-the-foundation-of-pricing)

---

# 1. Executive Summary

**Put-Call Parity** is the iron law of options.
It states that a **Call Option** plus **Cash** (Risk-Free Bond) creates the exact same payoff profile as a **Put Option** plus the **Stock**.
Therefore, they must have the same price.
If they don't, an arbitrage opportunity exists.
If $C + K > P + S$, you Sell the Call, Short the Cash, Buy the Put, Buy the Stock.
You lock in a risk-free profit.

---

# 2. The Theory

### 2.1. Synthetic Stock

Buying a Call and Selling a Put at the same strike = Long Stock.
Why?

* Stock goes up: Call profits $1:1$. Put expires worthless.
* Stock goes down: Put loses $1:1$ (you are short put). Call expires worthless.
* Result: Delta = 1.0.

### 2.2. The Box Spread

Buy a Bull Call Spread + Buy a Bear Put Spread (Same strikes).

* Buy 100 Call, Sell 110 Call.
* Buy 110 Put, Sell 100 Put.
* **Result:** You are Long Synthetic Stock at 100, and Short Synthetic Stock at 110.
* The position is flat.
* The payoff at expiration is exactly $10 (Width of strikes).
* If you pay $9.80 for it, you make $0.20 risk-free.
* This yields the Risk-Free Rate.

---

# 3. Strategy Rules

### 3.1. Reversals and Conversions

* **Conversion:** Long Stock + Long Put + Short Call. (Synthetic Short vs Actual Long). Logic: Captures "expensive" Calls.
* **Reversal:** Short Stock + Short Put + Long Call. (Synthetic Long vs Actual Short). Logic: Captures "expensive" Puts (HTB).

### 3.2. Hard-To-Borrow

When a stock is heavily shorted (e.g., AMC, GME), the cost to borrow shares rises to 50-100% APR.
Market Makers price this into the Puts. Puts trade effectively "in-the-money" relative to spot to account for the borrow fee.
Sophisticated traders sell these expensive Puts and short the stock (if they can locate it) to earn the borrow fee.

---

# 4. Mathematical Derivation

$$ C_0 + K e^{-rT} = P_0 + S_0 $$
Rearranging for Put Price:
$$ P_0 = C_0 + K e^{-rT} - S_0 $$
If dividend $D$ is paid during life of option:
$$ C_0 + D e^{-rT_{div}} + K e^{-rT} = P_0 + S_0 $$
Arbitrage Profit $\Pi$:
$$ \Pi = (C_{actual} - P_{actual}) - (S - K e^{-rT}) $$

---

# 5. Historical Case Studies

### 5.1. Robinhood "Infinite Money"

A reddit user found that Box Spreads on Robinhood gave him cash credit.
He bought Deep ITM Box Spreads.
He forgot about **Early Assignment Risk**.
The counterparty exercised the Short Puts.
He was left with a massive long stock position he couldn't afford.
He went -$50k in debt.
**Lesson:** European Options (SPX) are safe for Box Spreads. American Options (SPY) are NOT.

### 5.2. TSLA 2020

Tesla Puts were trading at implied volatilities way higher than Calls (Skew).
The "Reversal" trade (Long Call / Short Put / Short Stock) yielded 20% annualized returns just from the skew misalignment.

---

# 6. Python Implementation

```python
import numpy as np

class PutCallParity:
    def __init__(self, s, r, T, div_yield=0):
        self.s = s
        self.r = r
        self.T = T
        self.q = div_yield # Continuous dividend yield

    def check_parity(self, call_price, put_price, strike):
        # Theoretical Parity
        # C - P = S*e^(-qT) - K*e^(-rT)
        
        lhs = call_price - put_price
        rhs = self.s * np.exp(-self.q * self.T) - strike * np.exp(-self.r * self.T)
        
        diff = lhs - rhs
        
        if abs(diff) > 0.05: # Threshold (slippage/commissions)
            if diff > 0:
                return "Call Overpriced (Conversion)"
            else:
                return "Put Overpriced (Reversal)"
        return "Fair"

    def box_spread_yield(self, debit, width, days):
        # Gross Profit = Width - Debit
        profit = width - debit
        # Annualized Yield
        ann_yield = (profit / debit) * (365 / days)
        return ann_yield
```

### 6.3. HFT Application

High Frequency Trading firms execute parity arb in microseconds.
If AAPL stock ticks up, but the Option quotes lag by 10ms, the parity equation is violated.
HFT bots snatch the stale option quote and hedge with the stock instantly.
Retail cannot compete on speed, only on structural imbalances (Liquidity/Borrowing).

---

# 7. Optimization

### 7.1. Dividend Arbitrage

Buy Stock + Buy Put + Sell Call (Conversion) right before Ex-Dividend date.
If the Call owner forgets to exercise early to capture the dividend, you collect the dividend.
This is "playing the sleeper".

### 7.2. Jelly Roll

Rolling a Box Spread from one month to the next.
Effectively managing a tax-efficient synthetic loan.
Used by market makers to manage inventory across expirations.

---

# 8. Risk Management

### 8.1. Pin Risk

Stock closes at $100.00 exactly.
You are short the $100 Put.
You don't know if you will be assigned.
You wake up Monday morning Long 100 shares. Stock opens at $95.
You lose $500.
**Rule:** Close all arb positions before the closing bell on expiration day. Do not gamble on the "Pin".

### 8.2. Interest Rate Risk (Rho)

If rates rise, Call prices rise and Put prices fall.
Long-dated Box Spreads are essentially Bond positions.
They have duration risk.

---

# 9. Conclusion

Put-Call Parity is the "Gravity" of the options market.
It keeps everything in alignment.
When it breaks, it signals deep market stress (Liquidations or Short Squeezes).
For GOLIATH, we monitor Parity violations as a signal of **Smart Money Flow**.
If Calls become expensive relative to Puts (Conversion signal), it means insiders are leveraging up.
We follow the flow.
