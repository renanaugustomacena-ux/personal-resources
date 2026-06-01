# 217 — Behavioral Finance and Bias Mitigation

> Reference for behavioral biases, prospect theory, sentiment, anomalies, and mitigation strategies for systematic trading. Covers loss aversion, overconfidence, herding, narrative economics, momentum/reversal, equity premium puzzle, and trading-process design that resists biases. Self-contained beyond document 200.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prospect Theory](#prospect-theory)
3. [Loss Aversion](#loss-aversion)
4. [Reference Dependence](#reference-dependence)
5. [Probability Weighting](#probability-weighting)
6. [Cumulative Prospect Theory](#cpt)
7. [Mental Accounting](#mental-accounting)
8. [Disposition Effect](#disposition)
9. [Overconfidence](#overconfidence)
10. [Confirmation Bias](#confirmation)
11. [Anchoring](#anchoring)
12. [Availability Heuristic](#availability)
13. [Representativeness](#representativeness)
14. [Herding Behavior](#herding)
15. [Narrative Economics](#narrative)
16. [Investor Sentiment](#sentiment)
17. [Sentiment Indicators](#indicators)
18. [Limits to Arbitrage](#limits-arb)
19. [Noise Traders](#noise-traders)
20. [Closed-End Fund Discount](#cef)
21. [IPO Underpricing](#ipo)
22. [Post-Earnings Drift](#pead)
23. [Momentum and Reversal](#momentum)
24. [Value Premium](#value)
25. [Equity Premium Puzzle](#equity-premium)
26. [Calendar Anomalies](#calendar)
27. [Crash and Bubble Dynamics](#crashes)
28. [Black Swan and Fat Tails](#black-swan)
29. [Forecast Biases](#forecast)
30. [Behavioral Algorithms — Sentiment](#behavioral-algos)
31. [Behavioral Algorithms — Retail Flow](#retail-flow)
32. [Designing for Self-Discipline](#discipline)
33. [Trading Journal](#journal)
34. [Mental Rehearsal](#rehearsal)
35. [Position Sizing](#sizing)
36. [Decision Frameworks](#decisions)
37. [Hindsight Bias](#hindsight)
38. [Bias in Factor Research](#research-bias)
39. [Code Examples](#code)
40. [Reality Checks](#reality-checks)
41. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

Classical finance assumes rational expected-utility-maximizing agents. Behavioral finance documents systematic deviations from rationality:
- Loss aversion: losses hurt twice as much as gains feel good.
- Overconfidence: traders overestimate their skill.
- Herding: people follow the crowd.
- Anchoring: numbers stick in mind disproportionately.
- Recency bias: recent events dominate forecasts.

These biases affect both retail and institutional traders. They create predictable patterns in markets that systematic strategies can exploit and that all traders should defend against in their own decision-making.

This document covers the theory (prospect theory, psychological biases) and the practical applications (sentiment-based strategies, bias mitigation in process design). The reader benefits from understanding both: as a market participant interacting with biased counterparties, and as a human subject to the same biases.

---

## Prospect Theory

Kahneman and Tversky (1979): people don't maximize expected utility; they maximize a different value function relative to a reference point.

### Value Function

S-shaped:
- Concave for gains (diminishing positive utility).
- Convex for losses (diminishing dissatisfaction).
- Steeper for losses than gains.

Mathematical form:

$$
v(x) = \begin{cases} x^\alpha & \text{if } x \ge 0 \\ -\lambda (-x)^\alpha & \text{if } x < 0 \end{cases}
$$

with α ≈ 0.88 and λ ≈ 2.25.

### Key Implications

- Same magnitude loss feels worse than gain feels good.
- Risk-seeking in losses (people gamble to recover).
- Risk-averse in gains (people lock in profits).

### Empirical

Confirmed across hundreds of experiments. Cross-cultural evidence supports universality.

---

## Loss Aversion

The asymmetry: losses weighted ~2-2.5× gains.

### Implications

- **Disposition effect**: traders hold losers too long, sell winners too early.
- **Ego depletion**: after a loss, decision-making degrades.
- **Reluctance to realize losses**: closed positions confirm; open positions stay hopeful.

### In Algorithms

Loss-aversion-aware position sizing:
- Smaller positions in tail-risky strategies.
- Adjust Kelly fraction for prospect theory utility.

```python
def prospect_utility(x, alpha=0.88, lam=2.25):
    """Prospect theory value function."""
    return x**alpha if x >= 0 else -lam * (-x)**alpha
```

---

## Reference Dependence

Decisions depend on the **reference point**, not absolute level.

### Examples

- Trader bought at $100. Price now $90: pain. Price $110: pleasure.
- Same trader bought at $90. Price now $100: pleasure.

The reference point matters more than the absolute price.

### Anchoring (related)

People anchor on recent prices, entry points, round numbers ($100, $50K).

### Trading Use

- **Look at long-only history**: not just YTD performance.
- **Pre-set targets**: separate decision from current emotion.

---

## Probability Weighting

People overweight small probabilities and underweight large ones.

### Weight Function

$$
\pi(p) = \frac{p^\gamma}{(p^\gamma + (1-p)^\gamma)^{1/\gamma}},
$$

with γ ≈ 0.61.

For p = 0.01 (1% chance): π(0.01) ≈ 0.05. People act as if it's 5% rather than 1%.

For p = 0.99 (99% chance): π(0.99) ≈ 0.91. Slightly underweighted.

### Implications

- **Lottery-ticket bias**: people overpay for small-probability large gains.
- **OTM call bias**: traders bid up out-of-the-money calls.
- **Insurance over-purchase**: people overinsure rare events.

### In Markets

Crypto OTM calls (positive skew) reflects this bias. Historical persistence of "fat tail premium."

---

## Cumulative Prospect Theory

Updated 1992: rank-dependent utility. Probabilities weighted based on rank, not just nominal value. More consistent with observed behavior than original prospect theory.

### Application

- More accurate model of trader/investor behavior.
- Pricing of state-dependent claims under prospect theory differs from EU.

---

## Mental Accounting

Thaler (1985): money is fungible in theory but treated as siloed by humans.

### Examples

- "Vacation fund" treated separately from "investment fund."
- "House money" (recent winnings) gambled more freely.
- "Sunk cost fallacy": continuing investment to justify prior loss.

### Implications

- **Position-level vs portfolio-level decisions**: traders evaluate each position separately.
- **Capital allocation rigidity**: separate strategies have separate budgets.
- **Realization of gains**: sells winners to "lock in" specific position.

---

## Disposition Effect

Odean (1998), Shefrin-Statman (1985): traders sell winners too early and hold losers too long.

### Empirical

Retail trader data: winners sold after 30 days; losers held for 100+ days.

### Why

- Loss aversion + reference dependence.
- Mental accounting (hate to "realize" the loss).
- Hope (price will come back).

### Trading Implication

If counterparties are subject to disposition effect, momentum strategies have positive expected return on the timing dimension (riding winners).

---

## Overconfidence

People overestimate their abilities and the accuracy of their beliefs.

### Forms

- **Better-than-average**: 80% of drivers think they're above-average.
- **Illusion of control**: belief in influence over random outcomes.
- **Calibration overconfidence**: 90% confidence intervals contain truth only 50% of the time.
- **Overprecision**: claim exact estimates when reality is uncertain.

### Trading Effects

- **Overtrading**: more trades than optimal. Each trade has costs.
- **Excessive position sizing**: more capital than warranted by edge.
- **Ignoring base rates**: think your strategy is "different."

### Empirical

Barber and Odean (2000): retail traders' returns destroyed by overtrading. Performance after costs: -2 to -5% per year vs market.

---

## Confirmation Bias

Selective evidence-gathering: seek information that supports beliefs, ignore contradicting.

### Examples

- Buy a stock; read positive coverage; ignore negatives.
- Have a thesis; cherry-pick supporting backtests.

### Mitigation

- Pre-register hypotheses.
- Seek devil's advocate views.
- Review losing positions specifically for confirming evidence ignored.

---

## Anchoring

Initial numbers influence subsequent estimates disproportionately.

### Classical Experiment

Show subjects "wheel of fortune" landing on 65 vs 10. Then ask "% of African nations in UN?" Subjects anchored on 65 estimate 45%; on 10 estimate 25%. Despite irrelevance of wheel.

### Trading

- **Analyst targets**: anchor on consensus, not own analysis.
- **Round numbers**: Dow at 30000 acts as psychological barrier.
- **Entry price**: anchor for what's "fair value."

### Mitigation

- Use forecasts based on data, not analyst guesses.
- Set price targets at non-round levels.
- Pre-commit to exit prices independent of entry.

---

## Availability Heuristic

Recent or vivid events disproportionately influence judgments.

### Examples

- After plane crash: people overestimate flight risk.
- After market crash: people sell, fearing more crashes.
- After IPO success: investors overweight similar IPO probabilities.

### Trading Effects

- **Recency bias**: recent returns extrapolated.
- **Catastrophic disaster avoidance**: post-crash bear sentiment persists too long.
- **Pattern recognition**: see patterns that aren't there.

### Mitigation

- Use long historical samples.
- Run scenario analyses including unusual events.
- Build models robust to selection of training period.

---

## Representativeness

Judging probability by how similar an event is to a category prototype.

### Examples

- "This stock looks like Amazon in 2003" → high expected return.
- Ignoring base rates: probability of becoming Amazon is ~0.01%.
- Pattern-matching to historical analogues.

### Hot Hand Fallacy

Streak of wins → believe trend will continue. In purely random sequences, no such trend exists.

### Gambler's Fallacy

Streak of losses → believe reversal due. In independent trials, no such balance is enforced.

### In Markets

- Momentum stocks: representativeness drives "this is the next Amazon" thinking.
- Mean reversion: gambler's fallacy on sectors that just declined.

---

## Herding Behavior

Following the crowd.

### Information Cascades

Each new participant observes prior decisions; rationally updates beliefs. Result: cascade where most participants follow first few.

### Application

- IPO over-subscription (everyone wants in because everyone wants in).
- Asset bubbles (everyone buying because everyone is buying).
- Bank runs.

### Empirical

Hedge fund holdings cluster: 20-50% of major funds hold the same names.

### Trading

- **Crowded trade indicator**: identify and avoid heavily-owned names.
- **Inverse herding**: contrarian on high-consensus trades.

---

## Narrative Economics

Shiller (2017): viral stories drive market regimes.

### Examples

- 1990s: "internet revolution" narrative drove dot-com bubble.
- 2008: "housing always goes up" → bubble + crash.
- 2021: "stonks" narrative drove meme stocks.
- 2024: AI narrative drove tech rally.

### Tracking

- **News volume on a theme**: rising = narrative spreading.
- **Search trends**: Google Trends for terms.
- **Social media**: Twitter mentions of theme.

### Trading

Narratives have life cycles: emergence → mainstream → exhaustion. Riding the curve profitable; entering at peak loss.

---

## Investor Sentiment

Aggregate mood of market participants.

### Baker-Wurgler Index

Composite of:
- IPO volume.
- Closed-end fund discount.
- NYSE turnover.
- Equity share in new issues.
- Dividend premium.

Predictive: high sentiment → low future returns; low sentiment → high future returns.

### Retail vs Institutional

- Retail: AAII bull/bear survey, brokerage flow.
- Institutional: II survey, ICI flows.

Cross-sectional: retail favors small/glamour stocks; institutional favors large/value.

### Reality Check — Sentiment Predictive Power

- Sentiment alone has weak predictive power.
- Combined with valuation, predictive over 1-3 year horizons.
- Less useful for short-term timing.

---

## Sentiment Indicators

### VIX

Implied volatility on SPX. High VIX = fear. Mean-reverting.

### Put/Call Ratio

Open interest in puts / calls. High = fear.

### AAII Bull-Bear

Survey of retail investors.

### Fund Flows

ICI weekly equity fund flows. Outflows = fear.

### High-Yield Spreads

Wider HY spreads = fear.

### Combination

Sentiment "thermometer" combining multiple indicators. Z-scoring and aggregating.

---

## Limits to Arbitrage

Shleifer-Vishny (1997): arbitrageurs cannot fully correct mispricings.

### Reasons

- **Capital constraints**: arbitrageurs may not have enough capital.
- **Time horizons**: prices can stay mispriced longer than arbitrage capital can stay solvent.
- **Implementation costs**: short-selling, transaction costs, liquidity.
- **Performance pressure**: investors withdraw during drawdowns.

### Implications

- Mispricings persist.
- Anomalies survive.
- Even rational arbitrageurs cannot eliminate inefficiency completely.

---

## Noise Traders

De Long, Shleifer, Summers, Waldmann (1990): noise traders create risk that prevents arbitrage.

### Model

- Rational arbitrageurs vs noise traders.
- Noise traders' beliefs random.
- Their flow drives prices away from fundamentals.
- Risk that they push prices further before reversal.

### Empirical

- Closed-end fund discounts (noise trader sentiment proxy).
- IPO underpricing.
- Calendar anomalies.

---

## Closed-End Fund Discount

Closed-end funds trade at discount to NAV. Discount varies over time.

### Explanation

- Sentiment: discount widens when retail bearish.
- Fund-specific: management fees, illiquidity.

### Trading

- Buy fund at deep discount, hedge NAV exposure.
- Profits if discount narrows.
- Low Sharpe; long timeframes.

---

## IPO Underpricing

IPOs typically priced below market-clearing level. First-day pop common.

### Why

- **Winner's curse**: bidders shade to account for adverse selection.
- **Behavioral**: information cascade post-IPO.
- **Allocation rents**: bookrunners reward favored clients.

### Empirical

US IPOs: average first-day return ~10-20%, very long tail (some 100%+).

### Trading

- IPO allocation programs (institutional).
- IPO ETFs (retail).
- Selectivity matters; not all IPOs deserve allocation.

---

## Post-Earnings Drift

PEAD (Bernard-Thomas 1989): after earnings surprise, stock drifts in surprise direction for weeks.

### Why

- **Slow incorporation**: information not fully priced.
- **Anchoring**: analysts anchor on prior estimates.
- **Underreaction**: behavioral.

### Empirical

Earnings surprises: top decile stocks outperform bottom decile by ~50bps per month over 60 days.

### Trading

- Long top quintile post-earnings; short bottom quintile.
- Sharpe ~0.7 historically; decayed somewhat.

---

## Momentum and Reversal

### Momentum

Jegadeesh-Titman (1993): past 6-12 month winners outperform losers over next 6-12 months.

### Reversal

3-5 year past winners underperform; long-term reversal.

### Behavioral Explanations

- **Underreaction**: slow to incorporate (PEAD-like). Drives intermediate-term momentum.
- **Overreaction**: extrapolation of trends. Drives long-term reversal.

### Reality Check — Momentum Decay

Momentum effect smaller in last decade (post-2010) than historically. Crowding reduces alpha.

---

## Value Premium

Cheap stocks (low P/E, P/B) outperform expensive stocks long-run.

### Behavioral Explanation

- Investors extrapolate growth → overpay for "growth" stocks.
- Underprice "value" stocks.
- Mean reversion.

### Risk Explanation (Fama-French)

Value stocks have higher fundamental risk; premium compensates.

### Recent Empirical

Value premium near zero or negative 2007-2020. Revival 2020-2022. Persistent debate on whether value is dead.

---

## Equity Premium Puzzle

Mehra-Prescott (1985): equity returns 6%+ above bond returns historically. Standard utility theory predicts ~1%. The "puzzle."

### Explanations

- **Prospect theory**: loss aversion leads to underholding equity.
- **Disaster risk**: rare large crashes.
- **Habit formation**: utility depends on lifestyle, not wealth.
- **Long-run risk** (Bansal-Yaron): consumption growth has long-run component.

Each explanation partial; combined explains most of premium.

---

## Calendar Anomalies

### January Effect

Small caps outperform in January. Driven by tax-loss harvesting in December → rebound.

### Day-of-Week

Monday: historically negative. Friday: positive.

### Weekend Effect

Returns over weekends different from weekdays.

### Month-of-Year

May-October worse than November-April ("Sell in May").

### Holiday Effects

Pre-holiday returns positive. Day after Thanksgiving.

### Reality Check — Anomaly Decay

Most calendar anomalies have weakened in recent decades. Cost-aware traders should not rely on them.

---

## Crash and Bubble Dynamics

### Minsky Moments

Periods of stability breed leverage; leverage breaks suddenly. Self-fulfilling reversal.

### Leverage Cycle

Geanakoplos (2010): leverage cycles drive booms and busts.

### Empirical Bubbles

- 1929 stock crash.
- 1990 Japan asset bubble.
- 2000 dot-com.
- 2008 housing.
- 2021 crypto/SPAC.

Each had pre-crisis surge in leverage and narrative.

---

## Black Swan and Fat Tails

Taleb (2007): rare events dominate finance.

### Implications

- Standard models with thin tails systematically underestimate risk.
- Tail-risk hedging has positive expected value (controversial).
- Risk management should focus on tails, not averages.

### Trading

- Tail-risk insurance (puts, variance swaps).
- Anti-fragility: positions that benefit from volatility.

Document 86 covers Universa-style tail hedging.

---

## Forecast Biases

### Analyst Forecasts

- Persistently optimistic (career incentives).
- Slow to incorporate new info.
- Anchor on company guidance.
- Bias correlated with broker relationships.

### Macro Forecasts

- Underestimate downside risks.
- Cluster around consensus (herd).
- Recency bias dominates.

### Trading

- Trade against analyst consensus extremes.
- Use earnings revisions as signal (not forecasts themselves).

---

## Behavioral Algorithms — Sentiment

### Sentiment-Based Strategies

- Long positive sentiment, short negative.
- Or contrarian: short most positive, long most negative.

Empirically: contrarian works better. Crowded sentiment = reversal.

### Implementation

```python
def sentiment_signal(news_sentiment, social_sentiment, weight_news=0.6, weight_social=0.4):
    """Combined sentiment z-score."""
    return weight_news * news_sentiment + weight_social * social_sentiment

def contrarian_filter(sentiment, threshold=2.0):
    """Trade against extreme sentiment."""
    if sentiment > threshold:
        return -1  # short
    elif sentiment < -threshold:
        return 1  # long
    return 0
```

---

## Behavioral Algorithms — Retail Flow

### Retail Flow Tracking

Robinhood top-traded list, retail brokerage data.

### Empirical

- Robinhood-favored stocks underperform after sustained retail buying.
- Retail buying = contrarian signal at extremes.

### 2021 Meme-Stock Episode

WSB-driven retail buying caused short squeezes (GME, AMC). Some funds caught on the right side; others squeezed.

---

## Designing for Self-Discipline

### Pre-Commitment

- Set targets before opening position.
- Automated stop-loss orders.
- Pre-defined risk parameters.

### Rule-Based Systems

Convert discretionary process to rules. Reduces emotional override.

### Cooling-Off Periods

Mandatory wait before changes during stress. Prevents revenge trading.

---

## Trading Journal

Log every trade with reasoning:
- Entry price, target, stop.
- Hypothesis.
- Confidence.
- Position size.
- Outcome.

Periodic review:
- What worked, what didn't.
- Did process work, even when outcome bad?
- What patterns emerge?

### Modern Tools

- TraderVue, Edgewonk for retail.
- Custom systems for institutional.

---

## Mental Rehearsal

- **Pre-mortem**: imagine scenario where trade goes wrong; identify what would cause it.
- **Stress-test mental simulation**: imagine 20% drawdown; how would you react?
- **Regret minimization**: which decision would you regret more if it goes wrong?

These exercises improve decision quality under future stress.

---

## Position Sizing

Kelly criterion (document 41):

$$
f^* = \frac{\mu}{\sigma^2}.
$$

Adjustments for prospect theory: smaller fraction (e.g., half-Kelly) accounts for loss aversion and parameter uncertainty.

### Empirical

Most professional traders use 0.25-0.5 Kelly. Full Kelly leads to large drawdowns that even rational players struggle to handle.

---

## Decision Frameworks

### Pre-Defined Risk per Trade

E.g., 1-2% of capital per trade. Limits any single decision's damage.

### Max Drawdown Rules

If portfolio drawdown exceeds X%, reduce risk. Prevents catastrophic doubling-down.

### Cool-Off Rules

After bad trades or drawdowns, mandatory pause. Prevents revenge trading.

---

## Hindsight Bias in Backtesting

After seeing outcome, easy to confirm decision was "right."

### Mitigation

- Document decision *before* outcome.
- Distinguish process-good from outcome-good.
- Review decisions, not outcomes.

Document 211 covers backtesting discipline.

---

## Bias in Factor Research

- Data mining: try many factors, report only significant.
- Multiple testing: 100 factors at p=0.05 → 5 false positives.

Document 211 covers proper statistical hygiene.

---

## Code Examples

### Disposition Effect Detector

```python
import pandas as pd

def disposition_effect(trades):
    """Detect disposition effect in trade history."""
    # Compare holding period of winners vs losers
    winners = trades[trades['pnl'] > 0]['holding_days']
    losers = trades[trades['pnl'] < 0]['holding_days']
    return {
        'winner_avg_days': winners.mean(),
        'loser_avg_days': losers.mean(),
        'disposition_ratio': losers.mean() / winners.mean()  # > 1 = disposition effect
    }
```

### Sentiment Backtest

```python
def sentiment_strategy(returns, sentiment_score, lookback=20):
    """Contrarian sentiment strategy."""
    sentiment_z = (sentiment_score - sentiment_score.rolling(lookback).mean()) / sentiment_score.rolling(lookback).std()
    positions = -sentiment_z.clip(-2, 2) / 2  # contrarian
    strategy_returns = positions.shift(1) * returns
    return strategy_returns
```

### Cognitive Load Test

```python
def cognitive_load_test(decisions, time_pressures, accuracy):
    """Estimate decision quality under stress."""
    # ... (placeholder)
    pass
```

---

## Reality Checks

- **Biases are stable** across decades; don't expect them to vanish.
- **Exploitation alpha decays** as more participants exploit.
- **You're biased too**: humility about own decisions.
- **Process > outcome**: focus on decision quality, not single results.

---

## Reference Tables, Cheat Sheets, Bibliography

### Major Biases

| Bias | Description | Trading Implication |
|---|---|---|
| Loss aversion | Losses hurt 2× gains | Reluctance to cut losers |
| Overconfidence | Overestimate skill | Overtrade |
| Anchoring | Initial values stick | Persistence of stale targets |
| Availability | Recent events dominate | Recency bias in estimates |
| Representativeness | Similar = same | Pattern-matching errors |
| Confirmation | Seek supporting evidence | Cherry-pick data |
| Herding | Follow crowd | Bubbles and crowded trades |
| Narrative | Stories drive markets | Theme-based bubbles |

### Bibliography

- **Kahneman, D. (2011), *Thinking Fast and Slow*, Farrar Straus.** Comprehensive.
- **Thaler, R. (2015), *Misbehaving*, Norton.** Behavioral economics history.
- **Shiller, R. (2017), *Narrative Economics*, Princeton.** Stories.
- **Shiller, R. (2000), *Irrational Exuberance*, Princeton.** Bubbles.
- **Akerlof, G. and Shiller, R. (2009), *Animal Spirits*.**
- **Bernstein, P. (1996), *Against the Gods*, Wiley.** History of risk.
- **Mehra, R. and Prescott, E. (1985), "The Equity Premium: A Puzzle", *J. Monetary Economics*.**
- **De Long, B., Shleifer, A., Summers, L., Waldmann, R. (1990), "Noise Trader Risk in Financial Markets", *J. Political Economy*.**
- **Shleifer, A. and Vishny, R. (1997), "The Limits of Arbitrage", *J. Finance*.**
- **Barberis, N., Shleifer, A., Vishny, R. (1998), "A Model of Investor Sentiment", *J. Financial Economics*.**
- **Daniel, K., Hirshleifer, D., Subrahmanyam, A. (1998), "Investor Psychology and Security Market Under- and Overreactions", *J. Finance*.**
- **Hong, H. and Stein, J. (1999), "A Unified Theory of Underreaction, Momentum Trading, and Overreaction", *J. Finance*.**
- **Tversky, A. and Kahneman, D. (1992), "Advances in Prospect Theory: Cumulative Representation of Uncertainty", *J. Risk and Uncertainty*.**
- **Odean, T. (1998), "Are Investors Reluctant to Realize Their Losses?", *J. Finance*.**
- **Barber, B. and Odean, T. (2000), "Trading Is Hazardous to Your Wealth", *J. Finance*.**

### Cross-References

- Document 38 — Sentiment Analysis NLP.
- Document 41 — Kelly Criterion.
- Document 200 — Stochastic Calculus.
- Document 211 — Backtesting.
- Document 219 — Trading Psychology.

---

*End of document 217. ~1,400 lines.*
