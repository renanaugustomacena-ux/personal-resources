# 59 - Merger Arbitrage: The Deal Spread

**Volume:** 59 of 100
**Strategy Type:** Event Driven / Risk Arbitrage / Special Situations
**Risk Profile:** Binary Outcome / "Picking up pennies in front of a steamroller"
**Mathematical Basis:** Implied Probability of Deal Closing

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Deal Premium](#2-the-theory-the-deal-premium)
    * 2.1. Cash Merger: Acquirer pays cash for Target.
    * 2.2. Stock Merger: Acquirer pays usually fixed ratio of its own stock.
    * 2.3. The Spread: Why Target trades below Offer Price (Time Value + Deal Risk).
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Cash Deal: Long Target.
    * 3.2. Stock Deal: Long Target, Short Acquirer (Hedge Ratio).
    * 3.3. Analyze Regulatory Risk (Antitrust) vs Financing Risk.
    * 3.4. Exit: Deal Closes (Profit) or Deal Breaks (Stop Loss).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Implied Probability: $P_{market} = \frac{Price - Price_{pre}}{Offer - Price_{pre}}$.
    * 4.2. Expected Return: $E[R] = P_{success} \times Spread - (1-P_{success}) \times Downside$.
    * 4.3. Annualized Yield: $(Spread / Price) \times (365 / DaysToCluster)$.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Microsoft (MSFT) buys Activision (ATVI): The \$95 offer vs \$70 price. Huge antitrust fear.
    * 5.2. Twitter (TWTR) vs Elon Musk: The \$54.20 "Joke" offer that became real.
    * 5.3. Tiffany (TIF) vs LVMH: Renegotiation during COVID.
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Scraping SEC Filings (8-K, S-4) for Deal Terms.
    * 6.2. Calculating Real-time Spread and Implied Probability.
    * 6.3. Monitoring "Deal News" sentiment.
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Bidding War": Betting on a higher offer (Interloper Risk).
    * 7.2. "Appraisal Rights": Suing for fair value.
    * 7.3. "Reverse Morris Trust": Tax-free spinoff structures.
8. [Risk Management: The Break](#8-risk-management-the-break)
    * 8.1. Deal Break Downside: Usually -30% to -50% overnight.
    * 8.2. Position Sizing: Diversify across 20 deals. Never >5% in one.
    * 8.3. "Material Adverse Change" (MAC): The clause that lets acquirers walk away.
9. [Conclusion: The Asymmetric Bet](#9-conclusion-the-asymmetric-bet)

---

# 1. Executive Summary

**Merger Arbitrage** (Risk Arb) is the strategy of betting on corporate events.
When Company A announces it will buy Company B for \$50/share, B instantly jumps from \$35 to \$48.
The remaining \$2 is the "Spread".
It exists because the deal might fail (Antitrust, Shareholder vote, Financing).
Risk Arbs buy B at \$48 to make the safe \$2 profit in 3 months.
It yields 10-15% annualized with low market correlation.
Until a deal breaks. Then you lose 40%.

---

# 2. The Theory

### 2.1. Cash Deals

Acquirer pays \$50 Cash.
Stock trades at \$49.
Spread = \$1.
Return = 2%.
Time = 3 months. Annualized = 8%.
Risk: Deal fails, stock drops to \$35.

### 2.2. Stock Deals

Acquirer pays 0.5 shares of A for every share of B.
You must **Short A** and **Long B** to lock in the spread.
If A creates value or destroys value, you are hedged.
You capture the spread regardless of market direction.

---

# 3. Strategy Rules

### 3.1. Selection

Only deals with "Definitive Agreement" (DA).
Avoid "Rumors" or "Non-Binding Offers".
Focus on "Strategic" buyers (Competitors) vs "Financial" buyers (Private Equity).
Strategics are more committed but face higher Antitrust risk.

### 3.2. Execution

Wait for "Deal Spread Widening" on bad news (e.g. FTC lawsuit).
If you believe deal will close, buy the dip.
Warren Buffett bought ATVI at \$75 when FTC sued MSFT (Offer \$95).
He bet on the rule of law.

---

# 4. Mathematical Derivation

Calculating Expected Value:

* Offer: \$50.
* Current Price: \$48.
* Pre-Deal Price: \$35.
* Estimated Probability ($P$): 90%.

$$ EV = (0.90 \times 50) + (0.10 \times 35) = 45 + 3.5 = 48.50 $$

Since Current Price (\$48) < EV (\$48.50), the trade has positive expectancy.
The Arbitrageur is essentially an insurer of deal completion.

---

# 5. Historical Case Studies

### 5.1. Twitter (2022)

Elon offered \$54.20.
Tech market crashed. Elon tried to back out.
Stock fell to \$32.
Arbs bought aggressively, knowing the Delaware Court would force the deal.
Deal closed at \$54.20. Massive profit for those who understood contract law.

### 5.2. AbbVie / Shire (2014)

AbbVie agreed to buy Shire for tax reasons (Inversion).
US Treasury changed changes tax rules retroactively.
AbbVie walked away.
Shire stock crashed 30%.
Arbs lost billions.
**Lesson:** Regulatory risk is binary and unpredictable.

---

# 6. Python Implementation

```python
import pandas as pd
import numpy as np

def calculate_stock_merger_spread(P_target, P_acquirer, exchange_ratio):
    # Deal Value = P_acquirer * exchange_ratio
    offer_value = P_acquirer * exchange_ratio
    spread = offer_value - P_target
    return spread, offer_value

def annualized_return(spread, P_target, days_to_close):
    raw_return = spread / P_target
    annualized = raw_return * (365 / days_to_close)
    return annualized

# Example: Stock Deal
# Target = 95, Acquirer = 200, Ratio = 0.5
# Offer = 200 * 0.5 = 100
# Spread = 100 - 95 = 5 (5.2% return)
# If closes in 90 days -> 21% Annualized.
```

### 6.2. Monitoring Spreads

Track a portfolio of 50 active deals.
If average spread is 4%, and one deal blows out to 15%, investigate.
Is the deal breaking? Or is the market just panicking?

---

# 7. Optimization

### 7.1. Bidding Wars

Sometimes a third party (Interloper) jumps in with a higher bid.
"Target is in play".
Price can exceed the original Offer.
Buying Calls on Targets creates "convexity" to higher bids while capping downside.

### 7.2. Chinese Approvals (SAMR)

China creates huge delays for semiconductor deals (e.g. Qualcomm/NXP).
Spreads remain wide for years.
If approved, massive payout. If denied... NXP paid Qualcomm \$2B break fee, but stock still fell.

---

# 8. Risk Management

### 8.1. Position Sizing

Rule: Max Loos = 1% of NAV per deal break.
If downside is 40%, position size = 2.5%.
Diversification is the only free lunch in Risk Arb.

### 8.2. Hedging Market Risk

In Cash deals, Target correlates with Acquirer only if deal breaks.
Buying Puts on the Target is expensive (high skew).
Shorting the Sector ETF (e.g. XLK for Tech deal) hedges the "Pre-Deal Price" downside correlation.

---

# 9. Conclusion

Merger Arbitrage is playing poker with lawyers and regulators.
It transforms market risk into legal/event risk.
For GOLIATH, we track the spread statistically.
We don't read contracts. We read the **Flow**.
If the spread tightens despite bad news, someone knows the deal is safe.
It is the strategy of the Insider (or the very sharp Outsider).
