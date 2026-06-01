# 37 - Event Driven: Merger Arbitrage

**Volume:** 37 of 50
**Strategy Type:** Event Driven / Relative Value / Special Situations
**Risk Profile:** Binary Risk / Deal Break
**Mathematical Basis:** Success Probability vs. Deal Spread

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Betting on Completion](#2-the-theory-betting-on-completion)
    * 2.1. The Acquisition Announcement
    * 2.2. The Deal Spread (Why it exists)
    * 2.3. Cash Deals vs Stock Deals
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Setup: Firm A bids $50 for Firm B. Firm B trades at $48.
    * 3.2. The Trade (Cash): Long Firm B at $48.
    * 3.3. The Trade (Stock): Long Firm B, Short Ratio of Firm A.
    * 3.4. The Exit: Deal Closing ($50) or Deal Break (Crash to $30).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Implied Probability of Success ($P$)
    * 4.2. Kelly Criterion for Deal Sizing
    * 4.3. Annualized Return: Spread $\times$ (365 / Days to Close)
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Microsoft (MSFT) acquires Activision (ATVI)
    * 5.2. The Twitter (TWTR) Saga (Elon Musk)
    * 5.3. When Deals Break (Antitrust, Financing Failure)
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. News Scraping for "Definitive Agreement"
    * 6.2. Calculating the "Deal Spread"
    * 6.3. Monitoring Regulatory Approvals (FTC, EC)
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Pre-Event" Arb (Rumor Trading)
    * 7.2. "Hostile" Takeovers (Higher Bids likely)
    * 7.3. "SPAC" Arbitrage (Risk-Free floor)
8. [Risk Management: The Downside](#8-risk-management-the-downside)
    * 8.1. Deal Break Risk is Asymmetric (Win $2, Lose $20).
    * 8.2. Diversification: Hold 20-30 deals.
    * 8.3. Hedging Market Risk (Beta).
9. [Conclusion: The Insurance Seller](#9-conclusion-the-insurance-seller)

---

# 1. Executive Summary

**Merger Arbitrage** (Risk Arb) is the strategy of profiting from the spread between a stock's market price and the price offered by an acquirer.
If Microsoft offers to buy Activision for $95.00, and ATVI trades at $80.00.
The $15.00 spread represents the **Risk Premium** that the deal might fail (Antitrust blocking).
The Merger Arb trader assesses the probability of the deal closing.
If they believe Prob(Success) > Implied Market Prob, they buy.
It is like selling insurance against deal failure.

---

# 2. The Theory

### 2.1. Why the Spread Exists

A deal is promised, but not guaranteed.
Risks:

1. **Regulatory:** FTC/DOJ blocks it (Monopoly concerns).
2. **Financing:** Buyer runs out of money (rare for big tech).
3. **Shareholder Vote:** Shareholders reject the price.
4. **MAC:** Material Adverse Change (Target company implodes).
The market discounts the offer price to account for these risks + Time Value of Money.

### 2.2. Cash vs Stock

* **Cash Deal:** MSFT pays $95 cash. Strategy: Buy ATVI at $80. Profit = $15.
* **Stock Deal:** AMD buys Xilinx for 1.7234 shares of AMD.
  * Strategy: Buy 1 Xilinx. Short 1.7234 AMD.
  * Result: Lock in the spread regardless of AMD price movement. Market Neutral.

---

# 3. Strategy Rules

### 3.1. The Setup

Wait for "Definitive Agreement" (8-K filing).
Do not trade rumors (too risky).
Calculate Generalized Spread ($S$).

### 3.2. The Assessment

Ask: "Is the spread too wide?"
If Spread = 2% and Time to Close = 3 months. Annualized = 8%.
Is 8% enough for the risk?
Compare to Risk-Free Rate.
If Spread = 20% (ATVI scenario), the market is pricing in a massive risk of failure.

---

# 4. Mathematical Derivation

Expected Return ($E[R]$):
$$ E[R] = P_{success} \times (Price_{deal} - Price_{entry}) - (1 - P_{success}) \times (Price_{entry} - Price_{break}) $$
Implied Probability of Success ($P_{imp}$):
$$ Price_{market} = P_{imp} \times Price_{deal} + (1 - P_{imp}) \times Price_{break} $$
$$ P_{imp} = \frac{Price_{market} - Price_{break}}{Price_{deal} - Price_{break}} $$
Example:
Deal = $95. Current = $80. Break Price (Pre-deal) = $60.
$$ P_{imp} = \frac{80 - 60}{95 - 60} = \frac{20}{35} = 57\% $$
If you believe Real Probability is 80%, you have **Alpha**.

---

# 5. Historical Case Studies

### 5.1. MSFT / ATVI (2022-2023)

Microsoft bid $95 cash.
ATVI traded at $70-$80 for a year due to FTC lawsuit fears.
Warren Buffett bought heavily.
Courts ruled for Microsoft.
Deal closed at $95.
Profit: +20% in huge size. Risk: Low (in hindsight).

### 5.2. TWTR / Elon Musk (2022)

Elon agreed to buy TWTR at $54.20.
Then he tried to back out ("Bots!").
TWTR stock crashed to $32.
Arbs bought at $35-$40 betting he would be forced to close.
Delaware Court forced him. Deal closed at $54.20.
Profit: +50% in 6 months.

---

# 6. Python Implementation

```python
import pandas as pd

class MergerArb:
    def __init__(self, target_price, offer_price, break_price_est):
        self.P_market = target_price
        self.P_deal = offer_price
        self.P_break = break_price_est
        
    def calculate_metrics(self):
        gross_spread = (self.P_deal - self.P_market) / self.P_market
        
        # Simple Logic for implied prob
        numerator = self.P_market - self.P_break
        denominator = self.P_deal - self.P_break
        
        if denominator == 0:
            return 0
            
        implied_prob = numerator / denominator
        return gross_spread, implied_prob

    def kelly_bet_size(self, my_estimated_prob, bankroll):
        # Kelly Criterion = p - (1-p)/b
        # b = net odds received (Reward / Risk)
        reward = self.P_deal - self.P_market
        risk = self.P_market - self.P_break
        
        if risk == 0: return 0 
        
        b = reward / risk
        p = my_estimated_prob
        
        fraction = p - (1-p)/b
        return max(0, fraction) * bankroll
```

### 6.3. Deal Scraper

Automated scraping of SEC EDGAR (Form 8-K) implies parsing text for "Merger Agreement".
Keywords: "Acquire", "Merger", "Per Share", "Cash Consideration".
NLP extracts the $Price and Date.

---

# 7. Optimization

### 7.1. Bidding Wars

Sometimes a third party enters (Interloper).
If Firm C bids $60 for Firm B (beating Firm A's $50).
The Arb makes a windfall profit (+20% instantly).
**Call Option Strategy:** Buy OTM Calls on the Target. Limited Risk, Unlimited Upside if a bidding war starts.

### 7.2. Antitrust Expert Model

Hire former DOJ lawyers.
Predicting "Second Request" likelihood.
Quantifying regulatory risk is the edge in modern Arb.

---

# 8. Risk Management

### 8.1. The "Big Bath"

Most Arb deals make small money (3-5%).
But one broken deal loses -40%.
If you leverage 2x, you are wiped out.
**Rule:** Limit any single deal to 5% of NAV.
Never leverage a single name.

### 8.2. Correlation Risk

In a market crash (2008 or 2020), all spreads widen.
Deal spreads blow out because financing dries up.
Arb portfolios correlate to SPX downside during crashes (Short Put profile).
You must hedge market Beta.

---

# 9. Conclusion

Merger Arbitrage is the "Gentleman's Strategy".
It is intellectual, legalistic, and uncorrelated to day-to-day noise.
For GOLIATH, we run a "Passive Arb" book.
We only take deals with >10% annualized spread where the Acquirer is Investment Grade (AAA).
It acts as a substitute for High Yield Bonds in our portfolio.
