# 219 — Trading Psychology and Edge Longevity

> Discipline, performance, and mental sustainability for working traders. Covers edge identification, performance measurement, drawdown psychology, position sizing under prospect theory, decision frameworks, the masters' mental models, and the operating principles for a multi-decade career. Self-contained beyond document 217.

---

## Table of Contents

1. [Introduction](#introduction)
2. [The Trader's Mental Model](#mental-model)
3. [Edge Identification](#edge)
4. [Luck vs Skill](#luck-skill)
5. [Performance Measurement](#performance)
6. [Sharpe Variance](#sharpe-variance)
7. [Edge Decay Rates](#decay)
8. [Crowding and Capacity](#crowding)
9. [Behavioral Discipline](#discipline)
10. [Trading Journal Methodology](#journal)
11. [Emotional Regulation](#emotions)
12. [Stress and Decision Quality](#stress)
13. [Drawdown Psychology](#drawdown-psych)
14. [Recovery from Drawdown — Math](#recovery-math)
15. [Position Sizing and Survival](#sizing)
16. [Risk of Ruin](#ruin)
17. [Building a Trading Process](#process)
18. [Process vs Outcome Thinking](#process-outcome)
19. [The "In the Zone" Myth](#zone)
20. [Pre-Trade Routines](#pre-trade)
21. [Post-Trade Analysis](#post-trade)
22. [Building a Team](#team)
23. [Communicating Risk](#communicate)
24. [Career Arcs](#career)
25. [Burnout](#burnout)
26. [Ethics in Trading](#ethics)
27. [Masters' Frameworks](#masters)
28. [Soros's Reflexivity](#soros)
29. [Buffett's Circle of Competence](#buffett)
30. [Dalio's Principles](#dalio)
31. [Simons's Lessons](#simons)
32. [Druckenmiller — Concentrated Bets](#druckenmiller)
33. [Tudor Jones — Risk First](#tudor)
34. [Lynch — What You Know](#lynch)
35. [Idea Generation Pipeline](#idea-pipeline)
36. [Research Process](#research-process)
37. [Peer Pressure and Contrarian Discipline](#contrarian)
38. [Long-Term Cognitive Health](#cognitive-health)
39. [Common Mistakes](#mistakes)
40. [Building Durable Returns](#durable)
41. [Code Examples](#code)
42. [Reality Checks](#reality-checks)
43. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

Most traders fail. Of those who don't, most make returns no better than the index. Of those who beat the index, most do so for a few years before mean-reverting. Of those who maintain edge for decades, the common factor is psychological — process, discipline, sustainability — not raw IQ or specific strategy.

This document is for the working trader who wants to last. It synthesizes:
- The math of survival (position sizing, drawdown recovery).
- The psychology of decision-making under uncertainty.
- The career arcs of traders who succeeded over decades.
- The patterns of those who failed.

The reader who internalizes these lessons gains an advantage that compounds over years: the ability to keep trading, keep learning, and keep adapting after others have given up. The math is in document 41 (Kelly), 211 (backtesting), 217 (behavioral). Here, we focus on the *operating principles* — what to do daily, weekly, monthly to remain in the game.

A note on tone. There is no formula for psychological resilience. The frameworks below are tools, not algorithms. Different traders find different combinations work. The discipline is to find what works for you and stick with it across regime changes that test every assumption.

---

## The Trader's Mental Model

### Discretionary vs Systematic

A spectrum:
- **Pure discretionary**: human decides each trade.
- **Systematic with discretion**: model + override.
- **Pure systematic**: model executes; no override.

Each has different psychological demands:
- Discretionary requires constant decision-making and emotional discipline.
- Systematic requires research discipline and patience.
- Hybrid requires deciding when to override (most fail at this).

### Risk-Taker vs Risk-Manager

Two mental modes:
- **Risk-taker**: see opportunity, size up, deploy.
- **Risk-manager**: see risk, hedge, contain.

Best traders switch fluidly. Pure risk-takers blow up; pure risk-managers underperform.

### Optimism vs Pessimism

- Optimism: needed to find opportunities.
- Pessimism: needed to manage risk.

Healthy: balance. Excess: dangerous either way.

### Reality Check — Style Match

Traders should match style to temperament. A naturally cautious trader trying to run macro discretionary is fighting their nature. A naturally aggressive trader running market-neutral risk parity is bored and underperforms. Self-knowledge precedes strategy choice.

---

## Edge Identification

Edge: positive expected value over costs, sustainable.

### Sources

- **Information**: knowing something others don't.
- **Analysis**: interpreting public information better.
- **Speed**: acting before others (HFT).
- **Patience**: holding when others can't (private equity, long-only).
- **Structure**: capital structure advantages.
- **Risk premia**: harvest known premia (carry, value, vol).

### Distinguishing Edge from Noise

After 1 year of profitable trading: probably noise.
After 5 years with low correlation to market: probably edge.
After 10 years with stable Sharpe: confidence higher.

### Reality Check — Edge is Rare

Most "edges" are:
- Risk premia (real but commoditized).
- Survivorship in a streak.
- Momentum / market beta.
- Crowded factors.

Genuine durable alpha exists but is rare. Document 211 covers backtesting discipline.

---

## Luck vs Skill

Mauboussin (2012, *The Success Equation*): outcomes are part skill, part luck. Different fields have different skill weights:
- Chess: ~95% skill.
- NBA basketball: ~80% skill.
- Mutual fund management: ~25-50% skill.
- Hedge fund single-year performance: ~20% skill.
- Hedge fund 10-year performance: ~60% skill.

### Implications

- Single-year results say little.
- Long-term results compound skill *and* luck.
- Cannot infer skill from short tracks.
- Process quality is the proxy for skill.

### Reality Check — Survivorship Bias

The "great traders" of any decade often had:
- A specific market environment that suited them.
- Survivorship: many similar traders failed.
- Some luck.

Look for traders who survived multiple regimes. Different regime survival = stronger evidence of skill.

---

## Performance Measurement

### Sharpe

$\mu / \sigma$. Annualized typically.

### Sortino

$\mu / \sigma_{\text{downside}}$. Downside-adjusted.

### Calmar

Annualized return / max drawdown. Drawdown-adjusted.

### MAR

Similar to Calmar but uses 36-month max drawdown.

### Information Ratio

$\alpha / \text{tracking error}$. Active return vs benchmark.

### Reality Check — Single Metric Misleading

Sharpe of 2 from 1-year sample is not impressive (high standard error). Sharpe of 1 over 10 years with low max drawdown is impressive.

Always look at:
- Length of track record.
- Drawdown profile.
- Regime sensitivity.
- Strategy type and capacity.

---

## Sharpe Variance

Sample Sharpe is a noisy estimator:

$$
\text{SE}(\hat{SR}) \approx \sqrt{(1 + SR^2/2) / T_{\text{eff}}}.
$$

For SR = 1, 60 monthly observations: SE ≈ 0.13. 90% CI: [0.79, 1.21].

### Implications

- "Sharpe of 2 last year" tells you very little.
- "Sharpe of 1.5 over 10 years" with stable trajectory tells you a lot.
- Discount any Sharpe claim by 30-50% to allow for survivorship and selection.

---

## Edge Decay Rates

### Empirical

- Equity factors: alpha decays by ~50% over 5 years post-publication.
- Quantitative momentum: still works but weaker.
- Microstructure signals (HFT): decay in months.
- Macro themes: decay in years.

### Drivers

- **Discovery**: published research → wider knowledge.
- **Capital flows**: more capital chases the trade.
- **Implementation cost**: spreads tighten, alpha shrinks.

### Mitigation

- Continuous research pipeline.
- Adapt strategies as edges decay.
- Diversify across strategies (some decay slower).

---

## Crowding and Capacity

### Crowding Indicators

- High overlap with peer holdings.
- Crowded trades (FANG, magnificent 7, etc.).
- Excessive concentration in single factor.

### Capacity

For a given alpha:

$$
\text{Capacity} \approx \frac{\alpha^2}{(\sigma \sqrt{Q/V})^2}.
$$

Beyond capacity, alpha decays as you grow.

### Reality Check — Capacity Walls

Many strategies hit capacity walls at $1-5B AUM:
- Microstructure: $100M-$500M.
- Mid-frequency stat arb: $1-3B.
- Macro: $5-20B.
- Long-only equity: tens of billions.

Beyond capacity, alpha decays roughly linearly with size.

---

## Behavioral Discipline

### Pre-Commitment

Set rules before opening positions:
- Entry, exit, stop-loss.
- Size.
- Risk tolerance.

Once committed, execute.

### Automated Rule-Based Execution

If discipline is hard, automate. Algorithms don't get emotional.

### Mental Walls

Separate roles:
- Idea generator.
- Risk manager.
- Executor.

Even if same person, time-sliced.

---

## Trading Journal Methodology

### Pre-Trade

Document before opening:
- Hypothesis: why is this trade attractive?
- Confidence: how sure am I?
- Size: how much am I risking?
- Exit conditions: what would change my mind?

### Post-Trade

Review after closing:
- Outcome: P&L.
- Process: did I follow the plan?
- Learning: what's the lesson?

### Periodic Review

Weekly/monthly:
- Patterns in mistakes.
- Patterns in wins.
- Adjust process.

### Tools

Retail: TraderVue, Edgewonk.
Institutional: custom in-house.

The discipline of journaling matters more than the tool.

---

## Emotional Regulation

### Common Emotions

- **Fear**: of loss, of missing out (FOMO).
- **Greed**: hold too long.
- **Hope**: cling to losing positions.
- **Pride**: ignore evidence of mistake.
- **Revenge**: trade aggressively after loss.

### Recognition

- Notice physical sensations (tension, fast heart rate).
- Pause before deciding.
- Use tools (deep breathing, walking away).

### Mitigation

- Predefined rules.
- Position-size limits.
- Cooling-off periods after big wins or losses.

---

## Stress and Decision Quality

Under stress:
- Cognitive resources reduced.
- Time horizon shortens.
- Risk preferences shift (often toward gambling).
- Pattern recognition impaired.

### Defenses

- Reduce position size during personal stress (illness, family).
- Pre-defined risk rules survive stress better than ad-hoc.
- Sleep, exercise, diet (sustained over years).

---

## Drawdown Psychology

Drawdowns test psychology:
- Self-doubt.
- Investor pressure.
- Regret over past decisions.
- Temptation to "get even."

### Mathematical Recovery

A 50% drawdown requires 100% gain to recover. A 20% drawdown requires 25%.

```python
def recovery_required(drawdown):
    return drawdown / (1 - drawdown)

for dd in [0.10, 0.20, 0.30, 0.50, 0.70]:
    print(f"{dd*100:.0f}% drawdown requires {recovery_required(dd)*100:.0f}% gain to recover.")
```

The asymmetry: avoiding deep drawdowns is dramatically easier than recovering from them.

### Drawdown Discipline

- Define "personal kill switch" — drawdown that triggers reduced activity.
- Talk to mentors/advisors during drawdowns.
- Avoid major life decisions during drawdowns.

---

## Recovery from Drawdown — Math

### Position Sizing After Drawdown

Naive: maintain same dollar size.
Better: scale by remaining capital. Reduces compounding of losses.

### Time to Recovery

For SR = 1 strategy:
- 10% drawdown → ~6 months to recover.
- 20% → ~14 months.
- 30% → ~24 months.

For SR = 0.5:
- 10% → ~14 months.
- 20% → ~36 months.

### Reality Check — Many Funds Don't Recover

After 30%+ drawdown, ~50% of funds wind down. Investor patience runs out. Drawdown discipline saves careers.

---

## Position Sizing and Survival

### Kelly Criterion

For continuous compounding with edge $\mu$ and variance $\sigma^2$:

$$
f^* = \frac{\mu}{\sigma^2}.
$$

Maximizes log wealth growth.

### Why Pros Undersize

Full Kelly:
- Maximum growth in expectation.
- Massive drawdowns (50%+ regularly).
- Sensitivity to parameter estimation error.

Half-Kelly: half the growth, much less drawdown. Most pros use 0.25-0.5 Kelly.

### Adjusted for Prospect Theory

Loss-aversion-aware sizing further reduces fraction. Empirically, traders survive longer with conservative sizing.

```python
def kelly_fraction(mu, sigma, leverage_factor=0.5):
    """Half-Kelly fraction."""
    return leverage_factor * mu / sigma**2

# Strategy with 5% expected return, 15% vol
print(f"Half-Kelly fraction: {kelly_fraction(0.05, 0.15):.3f}")
```

---

## Risk of Ruin

For a series of bets with edge:

$$
P(\text{ruin}) = \!\left(\frac{q}{p}\right)^N,
$$

where p = win prob, q = loss prob, N = capital units.

### Implications

- Even with edge, ruin probable if undercapitalized.
- Diversify to increase effective N.
- Position sizing as core risk management.

### Reality Check — Ruin Rare for Diversified

For a Sharpe 1 strategy with proper sizing: ruin probability < 0.1%. For Sharpe 2: essentially zero.

Most "ruin" cases involve:
- No edge (negative expected value after costs).
- Excessive sizing (over-Kelly).
- Concentration (low effective N).

---

## Building a Trading Process

### Stages

1. **Idea generation**: where do trades come from?
2. **Validation**: is the idea real?
3. **Sizing**: how much?
4. **Execution**: when and how?
5. **Monitoring**: live performance.
6. **Exit**: when to close?
7. **Review**: post-trade analysis.

### Documentation

Each stage should have:
- Rules.
- Checklists.
- Criteria.

Pre-defined rules survive stress; ad-hoc decisions fail.

---

## Process vs Outcome Thinking

### Bad Process, Good Outcome

Made money on a bad trade. Lottery ticket.
- Don't repeat: outcomes don't validate process.

### Good Process, Bad Outcome

Lost money on a sound trade. Bad luck.
- Continue: process is right; luck will turn.

### Bad Process, Bad Outcome

Lost money on a bad trade.
- Avoid in future.

### Good Process, Good Outcome

Made money on a sound trade.
- Continue.

The discipline: focus on process. Outcomes are noise; process is signal over time.

---

## The "In the Zone" Myth

Some traders romanticize "flow" or "zone" states. Reality:
- Brief peak performance moments.
- Cannot be relied on.
- Often coincide with luck.

Structured process beats inspired insight over decades.

### Counter-Example

Some discretionary traders genuinely enter optimal performance periods. But they also maintain process. The "zone" is a bonus, not a foundation.

---

## Pre-Trade Routines

### Pre-Market

- Review overnight news.
- Check positions.
- Set goals for the day.

### Before Each Trade

- Run checklist.
- Confirm sizing.
- Set exit conditions.

### Environment

- Minimize distractions.
- Quiet, organized space.
- Removed from emotional triggers.

---

## Post-Trade Analysis

### Real-Time Annotation

Note state during trade:
- Confidence level.
- Emotional state.
- Conditions.

### Post-Close Review

- Did I follow the plan?
- Did I learn anything?
- Update database.

### Periodic Aggregation

- Weekly P&L breakdown.
- Monthly attribution.
- Quarterly strategic review.

---

## Building a Team

### Roles

- **PM (Portfolio Manager)**: trade decisions.
- **Analyst**: research and idea generation.
- **Risk**: independent risk assessment.
- **Execution**: trade implementation.
- **Operations**: settlement, reporting.

### Conflict Resolution

PM-Risk dynamics: tension by design. Risk pushes back; PM advocates.

Productive: respectful debate. Destructive: silos and politics.

### Hiring

- Skill: technical capability.
- Fit: cultural alignment.
- Sustainability: stress tolerance.

Cheap to hire wrong; expensive to fire.

---

## Communicating Risk

### To Senior Management

- Top-line metrics (VaR, exposure, P&L).
- Stress scenarios.
- Drivers of recent changes.

### To Investors

- Performance.
- Strategy.
- Risk metrics.
- Outlook.

### To Board

- Strategic risks.
- Compliance.
- Operational health.
- Material events.

### Language

Avoid jargon. Quant terms confuse non-quants. Translate to dollars and percentages.

---

## Career Arcs

### Common Trajectories

1. **Junior trader (1-3 years)**: learn basics. P&L small. Fail and adapt.
2. **Mid-level (3-7 years)**: established edge. Growing AUM.
3. **Senior PM (7-15 years)**: significant AUM. Team leadership.
4. **Head of strategy / CIO (15+ years)**: portfolio-level decisions.
5. **Founder / partner**: launch own fund.

### Failure Modes

- **Plateau**: edge decays, no adaptation.
- **Burnout**: cognitive exhaustion.
- **Compliance issues**: regulatory or ethical lapses.
- **Health problems**: stress takes toll.
- **Forced retirement**: drawdowns end career.

### Reality Check — Career Length

Average institutional trader career: 8-15 years. Long careers (20+) require:
- Adapting to multiple regimes.
- Avoiding catastrophic mistakes.
- Maintaining cognitive sharpness.
- Building sustainable lifestyle.

---

## Burnout

### Symptoms

- Exhaustion.
- Cynicism.
- Reduced effectiveness.
- Sleep problems.
- Physical complaints.

### Causes

- Sustained stress.
- Lack of recovery time.
- Misalignment with values.
- Poor work-life integration.

### Prevention

- Sleep (7-9 hours).
- Exercise.
- Social connection.
- Hobbies.
- Therapy / coaching.

### Reality Check — Burnout in Finance

Finance has burnout-friendly culture: long hours, high pressure, scarce relaxation. Top performers often suffer. Younger generation (post-2010) increasingly recognizes need for sustainability.

---

## Ethics in Trading

### Gray Areas

- Insider information (sometimes obvious, sometimes not).
- Market manipulation.
- Front-running clients.
- Conflicts of interest.

### Red Lines

- Material non-public information.
- Spoofing/layering.
- Misappropriating client funds.

### Cultural Norms

- Top firms: zero tolerance for ethical lapses.
- Smaller shops: variable, depending on partners.

### Reality Check — Ethics is Personal

Reputation as trader = lifetime asset. Ethical lapses end careers, often with criminal liability.

---

## Masters' Frameworks

### Common Patterns

Across George Soros, Warren Buffett, Ray Dalio, Jim Simons, Stanley Druckenmiller, Paul Tudor Jones, Peter Lynch:

- **Process discipline**: follow rules.
- **Position sizing rigor**: don't over-bet.
- **Risk management**: protect capital.
- **Adapt to regimes**: don't dogmatize.
- **Long-term horizon**: years to decades.
- **Continuous learning**: never stop reading and thinking.

The frameworks differ; the underlying discipline is similar.

---

## Soros's Reflexivity

Soros: market participants' beliefs shape outcomes; outcomes feedback into beliefs. Reflexive feedback loops drive bubbles and crashes.

### Implications

- Markets are not perfectly rational.
- Bubbles can persist.
- Trade reflexive cycles, not just fundamentals.

### Application

Identify reflexive narratives:
- Tech 2020-2021.
- AI 2023-2024.
- Anti-tech 2022.

Ride the narrative; exit when reflexive support weakens.

---

## Buffett's Circle of Competence

Stay within expertise. Don't invest in what you don't understand.

### Implications

- Specialize.
- Avoid hot themes outside competence.
- Patient until opportunities arise within competence.

### Counter-Application

Adapting to new areas is sometimes necessary. Buffett famously avoided tech for decades; eventually invested in Apple. Circle expansion is possible but requires study.

---

## Dalio's Principles

Bridgewater's Ray Dalio: radical transparency, machine-like decision-making.

### Key Principles

- Pain + Reflection = Progress.
- Embrace mistakes.
- Build systems, not heroes.
- Diversify (the "holy grail" of investing).
- Prepare for many regimes.

### Application

- Document principles.
- Convert insights into systems.
- Iterate based on feedback.

---

## Simons's Lessons

Jim Simons (Renaissance): pure systematic, no overrides.

### Key Lessons

- Never override the model.
- Continuous research and improvement.
- Hire scientists, not finance majors.
- Capacity-aware: scale only as edge supports.

### Application

For systematic traders: trust the model. For discretionary: study Simons for research discipline.

---

## Druckenmiller — Concentrated Bets

Stan Druckenmiller: "When you really know you're right, you bet big."

### Implications

- High-conviction bets, sized appropriately large.
- Most ideas: pass.
- Few ideas: meaningful sizing.

### Counter

- Hard to know "really right" with certainty.
- Most concentrated bets that fail wipe out years of gains.
- Druckenmiller is one of few who pulled this off; many others failed.

### Reality Check

Concentration with hedging beats pure concentration. Even Druckenmiller-style requires risk management.

---

## Tudor Jones — Risk First

Paul Tudor Jones: capital preservation as primary discipline.

### Implications

- Stop-losses non-negotiable.
- Smaller position sizing.
- Capital preservation > return chasing.

### Application

- Define max loss per trade in advance.
- Honor stops without exception.
- Compound conservatively.

---

## Lynch — What You Know

Peter Lynch: "Invest in what you know."

### Implications

- Retail/consumer companies you understand.
- Direct experience as edge.
- Beat Wall Street by knowing your local mall.

### Modern Application

In an institutional world, "know" includes:
- Industry expertise.
- Domain knowledge.
- Network insights.

Specialization = edge.

---

## Idea Generation Pipeline

### Sources

- Reading (research papers, news, social).
- Conversations (peers, mentors, industry contacts).
- Data exploration (anomalies, patterns).
- Academic literature.

### Filtering

Most ideas: rejected. Reasons:
- Already known/priced.
- Cost > expected alpha.
- Out of domain.
- Operationally impractical.

### Prioritizing

Best ideas to pursue:
- High expected alpha.
- Within capacity.
- Match team skill.
- Edge sustainability.

---

## Research Process

### Hypothesis-Driven

State hypothesis explicitly. Pre-register.

### Falsifiable Tests

Design tests that could refute. Avoid confirmation bias.

### Replication

Independent reproduction by another team member.

### Out-of-Sample

Reserve data for final test. No iterating on out-of-sample.

Document 211 covers backtesting discipline in depth.

---

## Peer Pressure and Contrarian Discipline

### Crowded Trades

When everyone buys, returns suffer. Contrarian discipline: skip crowded.

### Conformity Pressure

Inside firms: pressure to match peers. Outside: pressure to match consensus.

### Defenses

- Track record of contrarian success.
- Pre-commitment to rules.
- Independent risk-taking.

### Reality Check — Contrarian Is Hard

Going against consensus painful when you're wrong, lonely when you're right but slow.

---

## Long-Term Cognitive Health

### Sleep

7-9 hours nightly. Sleep deprivation degrades:
- Decision quality.
- Pattern recognition.
- Emotional regulation.

### Exercise

Regular cardio + strength. Improves cognition, mood, longevity.

### Diet

Mediterranean / whole-food. Avoid blood-sugar swings during trading.

### Learning

Reading, conversations, formal courses. Avoids cognitive decline.

### Social

Strong relationships. Isolated traders burn out faster.

### Reality Check — Decades-Long Care

Maintaining performance for 30+ years requires sustained habits. Few maintain. Those who do have meaningful edge in late career.

---

## Common Mistakes

### Overtrading

Too many trades. High costs. Low edge per trade.

### Revenge Trading

Aggressive after losses. Often catastrophic.

### Anchoring on Entry

"I bought at $100, won't sell below" — irrational.

### Chasing

Buying after big move. Late to trend.

### Over-Concentration

Too much in one trade.

### Ignoring Costs

Underestimating transaction costs.

### Failing to Adapt

Sticking with strategy past expiration.

---

## Building Durable Returns

### Key Principles

- Edge identification + size discipline + risk management.
- Multi-strategy diversification.
- Continuous research.
- Cost discipline.
- Process orientation.
- Long horizon.

### Reality Check — Durable is Rare

Most strategies decay or stop working. Durable returns over decades require:
- Adapting strategies as edges decay.
- Capital efficiency.
- Risk management.
- Personal sustainability.

---

## Code Examples

### Trade Journal Analyzer

```python
import pandas as pd

def analyze_journal(trades):
    """Analyze trading journal for patterns."""
    return {
        'total_trades': len(trades),
        'win_rate': (trades['pnl'] > 0).mean(),
        'avg_win': trades.loc[trades['pnl'] > 0, 'pnl'].mean(),
        'avg_loss': trades.loc[trades['pnl'] < 0, 'pnl'].mean(),
        'profit_factor': trades.loc[trades['pnl'] > 0, 'pnl'].sum() / abs(trades.loc[trades['pnl'] < 0, 'pnl'].sum()),
        'avg_holding_winners': trades.loc[trades['pnl'] > 0, 'holding_days'].mean(),
        'avg_holding_losers': trades.loc[trades['pnl'] < 0, 'holding_days'].mean(),
    }
```

### Drawdown Analyzer

```python
import numpy as np

def drawdown_analysis(returns):
    """Analyze drawdowns in return series."""
    cumret = (1 + returns).cumprod()
    running_max = cumret.cummax()
    drawdown = (cumret - running_max) / running_max
    
    max_dd = drawdown.min()
    
    # Find drawdown periods
    in_dd = drawdown < 0
    dd_periods = []
    start = None
    for i, dd_state in enumerate(in_dd):
        if dd_state and start is None:
            start = i
        elif not dd_state and start is not None:
            dd_periods.append((start, i, drawdown.iloc[start:i].min()))
            start = None
    
    return {
        'max_drawdown': max_dd,
        'recovery_time_for_max_dd': '...',  # compute days to recover
        'num_drawdowns': len(dd_periods),
        'avg_drawdown_duration': np.mean([p[1] - p[0] for p in dd_periods])
    }
```

### Kelly with Prospect Theory

```python
def prospect_kelly(mu, sigma, alpha=0.88, lam=2.25, leverage_factor=0.5):
    """Kelly fraction adjusted for prospect theory."""
    # Heuristic: scale by alpha and inverse loss aversion
    kelly_full = mu / sigma**2
    adjusted = kelly_full * alpha / np.sqrt(lam)
    return leverage_factor * adjusted

print(f"Prospect-Kelly fraction: {prospect_kelly(0.05, 0.15):.3f}")
```

---

## Reality Checks

- **Even great traders have decade-long droughts**: Buffett underperformed S&P from 2008-2014.
- **Psychology buys longevity, not alpha**: edge comes from skill; psychology lets you stay around long enough to compound.
- **Sustainability > optimization**: a maintainable 1.0 Sharpe beats an unsustainable 2.0.
- **Self-awareness is rare and valuable**: know your weaknesses; build systems around them.

---

## Reference Tables, Cheat Sheets, Bibliography

### Performance Metrics Quick Reference

| Metric | Good | Excellent |
|---|---|---|
| Sharpe (multi-year) | 1.0+ | 1.5+ |
| Sortino | 1.5+ | 2.0+ |
| Calmar | 0.5+ | 1.0+ |
| Information Ratio | 0.5+ | 1.0+ |
| Max DD | <20% | <10% |

### Bibliography

- **Kahneman, D. (2011), *Thinking Fast and Slow*, Farrar Straus.**
- **Mauboussin, M. (2012), *The Success Equation*, Harvard Business.** Skill vs luck.
- **Mauboussin, M. (2007), *More Than You Know*, Columbia.**
- **Schwager, J. (1989, 1992, 2003, 2012, 2020), *Market Wizards* series, HarperCollins.** Multiple volumes of trader interviews.
- **Soros, G. (2003), *The Alchemy of Finance*, Wiley.** Reflexivity.
- **Dalio, R. (2017), *Principles*, Simon & Schuster.**
- **Lefevre, E. (1923), *Reminiscences of a Stock Operator*.** Classic; still relevant.
- **Steenbarger, B. (2009), *The Daily Trading Coach*, Wiley.** Trader psychology.
- **Marks, H. (2011), *The Most Important Thing*, Columbia.**
- **Taleb, N. (2001), *Fooled by Randomness*, Random House.**
- **Klein, G. (1998), *Sources of Power*, MIT Press.** Decision making under stress.
- **Tetlock, P. (2015), *Superforecasting*, Crown.** Forecasting discipline.
- **Lo, A. (2017), *Adaptive Markets*, Princeton.** Evolution of markets.

### Cross-References

- Document 41 — Kelly Criterion.
- Document 200 — Stochastic Calculus.
- Document 211 — Backtesting.
- Document 217 — Behavioral Finance.
- Document 218 — Hedge Fund Risk.

---

## Coda

The trader who lasts is not the smartest. Not the fastest. Not the one with the best models. The trader who lasts is the one who:

- Identifies edge honestly.
- Sizes positions for survival, not maximum return.
- Maintains process discipline through bull and bear markets.
- Adapts as edges decay and new opportunities emerge.
- Preserves cognitive capacity through sleep, health, and learning.
- Recognizes when to step away.
- Comes back ready, when the time is right.

The math is interesting. The strategies are debatable. The psychology is the foundation. Build that, and the rest follows.

The 19 documents preceding this one cover the technical machinery — stochastic calculus, microstructure, vol surfaces, Bayesian methods, information theory, game theory, EVT, copulas, optimal execution, crypto derivatives, HFT engineering, backtesting, alternative data, fixed income, FX, commodities, DeFi, behavioral finance, hedge fund operations. Each is a tool. None is the secret.

The secret is to know enough of them to recognize opportunity, to apply them with discipline when opportunity arises, and to keep showing up — month after month, year after year, decade after decade.

That is the trader's life. That is the edge that compounds.

---

*End of document 219. ~1,400 lines.*

*End of the 20-document trading wisdom expansion. Documents 200 through 219 form a coherent reference covering the modern quantitative trading stack. They do not replace specialized texts — Andersen-Piterbarg for fixed income, Bergomi for stochastic vol, Cartea-Jaimungal for execution — but they provide an integrated map of the field, with cross-references that let the practitioner navigate from one topic to another as questions arise. The expansion was written 2026-04-28 over multiple sessions, with the goal of dense, code-bearing, reality-check-anchored exposition. Each document references back to the foundational document 200 and forward to specific application documents in the existing 1-99 collection.*
