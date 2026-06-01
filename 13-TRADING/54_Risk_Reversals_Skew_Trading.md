# 54 - Risk Reversals: Trading the Skew

**Volume:** 54 of 100
**Strategy Type:** Directional Volatility / Sentiment Analysis / Global Macro
**Risk Profile:** Unlimited Risk (Short Put) / Leveraged Directional
**Mathematical Basis:** Implied Volatility Skew ($Skew = \sigma_{OTM\_Put} - \sigma_{OTM\_Call}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Why the Smile is a Smirk](#2-the-theory-why-the-smile-is-a-smirk)
    * 2.1. The Crash of 1987: Birth of the Skew.
    * 2.2. Supply and Demand: Everyone buys Puts (Insurance). Few buy Calls (Lottery).
    * 2.3. The Risk Reversal (RR): A measure of market fear vs greed.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Monitor 25-Delta Risk Reversal ($RR_{25}$).
    * 3.2. Signal: Extreme Skew (Z-Score > 2).
    * 3.3. Execution: Sell Expensive Option (Put), Buy Cheap Option (Call).
    * 3.4. Result: Synthetic Long position with "financed" premium.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The RR Metric: $RR_{25} = IV_{25\Delta Call} - IV_{25\Delta Put}$.
    * 4.2. Probability Density Function (PDF): Skew implies fat tails.
    * 4.3. Breakeven Analysis: How Skew subsidizes the directional bet.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Oil (2022): Skew flipped Positive (Calls > Puts) before the Russian invasion.
    * 5.2. Gold (2011/2020): Frequent "Call Skew" due to safe-haven demand.
    * 5.3. Equity Indices (SPX): Permanent negative skew (Puts always > Calls).
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Fetching Option Chains for multiple expirations.
    * 6.2. Calculating Constant Maturity 25-Delta Skew.
    * 6.3. Plotting the "Skew Surface" over time.
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Collars": Long Stock + Short Call + Long Put (Protective Skew).
    * 7.2. "Seagulls": Risk Reversal + Short OTM Put (selling 2 tails to finance 1).
    * 7.3. "Skew Arbitrage": If Skew is too steep vs realized correlation.
8. [Risk Management: The Tail](#8-risk-management-the-tail)
    * 8.1. Naked Puts: Only sell puts on assets you want to own (Warren Buffett style).
    * 8.2. Margin Expansion: Brokers hike margin on Short Puts during crashes.
    * 8.3. Directional Exposure: A Risk Reversal is Delta 50 (Leveraged Long).
9. [Conclusion: The Macro Telescope](#9-conclusion-the-macro-telescope)

---

# 1. Executive Summary

**Risk Reversal** describes the strategy and the metric simultaneously.
Metric: The difference in implied volatility between OTM Calls and OTM Puts.
Strategy: Being Short one wing and Long the other.
Usually, Puts trade at 20% IV and Calls at 15% IV (Negative Skew).
If Puts trade at 30% IV and Calls at 12% IV (Extreme Fear), you can:
**Sell the 30% Put** (Receive Credit).
**Buy the 12% Call** (Pay Debit).
**Result:** A Synthetic Long position for Zero Cost (or even a credit), with unlimited upside and downside risk of owning the stock.
You are paid to be a contrarian.

---

# 2. The Theory

### 2.1. The 1987 Crash

Before 1987, Implied Vol curves were flat (Calls = Puts).
After the Black Monday crash (-22%), traders realized downside moves are more violent than upside moves.
Puts became permanently expensive.

### 2.2. The Skew Index

The CBOE SKEW Index measures the "tail risk" perceived by the market.
High Skew = High demand for crash protection.
Low Skew = Complacency.
Risk Reversals trade this sentiment.

---

# 3. Strategy Rules

### 3.1. Contrarian Long

When: Market has crashed 10%. Skew is historically high (Puts expensive).
Action: Sell OTM Put / Buy OTM Call.
Why: If market stabilizes, Put IV crushes (profit). If market rallies, Call IV expands + Delta wins.
This is the "Buffett Put" strategy turbocharged.

### 3.2. Trend Following (FX)

In Forex, Skew follows the trend.
If USD/JPY is rising, Calls become more expensive than Puts.
Strategy: Follow the Skew. If Skew flips positive, go Long.

---

# 4. Mathematical Derivation

$$ RR_{25} = \sigma_{Call, 25\Delta} - \sigma_{Put, 25\Delta} $$

Normal SPX: $12\% - 20\% = -8\%$ (Negative Skew).
Crisis SPX: $15\% - 40\% = -25\%$ (Extreme Skew).
Gold: $18\% - 16\% = +2\%$ (Positive Skew).

If you sell the Put at 40 vol and Buy the Call at 15 vol:
You are "Buying Low, Selling High" on volatility terms.
Your Breakeven on the stock price is much lower than a simple stock purchase.

---

# 5. Historical Case Studies

### 5.1. Crude Oil (2020 Negative Price)

When Oil went negative, Put Skew became undefined/infinite.
Buying Calls was virtually free.
Risk Reversals printed millions for those willing to take delivery.

### 5.2. Tech Bubble (1999)

One of the rare times Equities had Positive Skew.
Calls were MORE expensive than Puts.
Investors feared "missing out" (FOMO) more than crashing.
Selling Calls via Risk Reversals (Short Call / Long Put) was the top-ticking trade.

---

# 6. Python Implementation

```python
import pandas as pd
import matplotlib.pyplot as plt

def calculate_skew(chain):
    # Filter for 25 Delta options (approx)
    # This requires a delta column calculated via BS
    
    call_25 = chain[(chain['type'] == 'call') & (abs(chain['delta'] - 0.25) < 0.05)]
    put_25 = chain[(chain['type'] == 'put') & (abs(chain['delta'] + 0.25) < 0.05)]
    
    if call_25.empty or put_25.empty:
        return np.nan
        
    iv_call = call_25['impliedVolatility'].mean()
    iv_put = put_25['impliedVolatility'].mean()
    
    return iv_call - iv_put

# If Skew < -10%: Bullish Reversal Setup (Oversold)
# If Skew > 5%: Bearish Reversal Setup (Overbought)
```

### 6.3. Z-Score

Normalize the current Skew against its 6-month history.
Significantly statistically deviations ($Z > 2$) imply mean reversion of the Skew itself.

---

# 7. Optimization

### 7.1. The Seagull

A 3-legged strategy to finance the Risk Reversal.
Sell Put (OTM)
Buy Call (OTM)
Sell Call (Even further OTM)
Cost: Zero or Credit.
Profile: Limited Upside, Large Downside, "Free" Delta in the middle.

### 7.2. Fading the Skew

If Skew is high, selling the Risk Reversal (Selling Call, Buying Put) gives you a "Short" position with positive carry.

---

# 8. Risk Management

### 8.1. Downside Uncapped

Selling a Put is identical to owning the stock.
If the stock goes to zero, you lose $StockPrice \times Contracts \times 100$.
Only do this on indices or blue chips (AAPL, MSFT) you are happy to own for 10 years.

### 8.2. Margin

Short Puts require significant margin (usually 20% of notional).
Ensure you have cash to cover assignment.

---

# 9. Conclusion

The **Risk Reversal** is the professional's "Market Thermometer".
By looking at the Skew, you see what the "Smart Money" is hedging against.
Negative Skew = Fear of Crash. Positive Skew = Fear of Missing Out.
GOLIATH trades Skew to enter directional positions with a statistical edge.
We don't just buy the stock; we let the options market subsidize our entry.
It is the ultimate tool for the Contrarian Value Investor.
