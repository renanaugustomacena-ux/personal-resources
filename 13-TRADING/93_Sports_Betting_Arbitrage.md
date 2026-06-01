# 93 - Sports Betting Arbitrage & Quantum Harmony Search

**Volume:** 93 of 100
**Strategy Type:** Arbitrage / Combinatorial Optimization / Alternative Alpha
**Risk Profile:** Account Limitation (Gubbing) / Voided Bets (Palpable Error)
**Mathematical Basis:** Implied Probability Inversion ($P = 1/Odds$) & Quantum Harmony Search (Meta-Heuristic Optimization)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context](#2-historical-context)
    * 2.1. The Syndicate Model (Starlizard).
    * 2.2. The Evolution of Optimization (Geem 2001).
3. [The Theory: Market Structure & Optimization](#3-the-theory-market-structure--optimization)
    * 3.1. Bookmakers as Exchanges (The Vig).
    * 3.2. Quantum Harmony Search (The Meta-Optimizer).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Surebet Profit & Yield.
    * 4.2. Quantum Mutation & Tunneling.
5. [The Strategy Rules](#5-the-strategy-rules)
    * 5.1. Arbitrage Identification.
    * 5.2. Portfolio Composition via QHS.
    * 5.3. Execution & Staking.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python: Sports Arb Scanner.
    * 6.2. Python: Quantum Harmony Search Class.
    * 6.3. Rust: High-Performance Improvisation.
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 93** represents the fusion of **Sports Arbitrage** (Risk-free profit from inefficient pricing) and **Quantum Harmony Search** (Meta-heuristic optimization for complex landscapes).

* **The Alpha:** Sportsbooks are uncoordinated. $Bookie_A$ might price a Lakers win at 2.10, while $Bookie_B$ prices a Lakers loss at 2.10. Betting on both guarantees profit.
* **The Problem:** There are thousands of matches and hundreds of bookmakers. Selecting the *optimal* set of bets to maximize Bankroll Growth (Kelly Criterion) while minimizing "Gubbing Risk" (Account Bans) is a non-convex, NP-hard optimization problem.
* **The Solution:** **Quantum Harmony Search (Indicator 091)**. Unlike Gradient Descent which gets stuck in local minima, QHS uses "Quantum Tunneling" (heavy-tailed mutation distributions) to explore the global solution space, finding the perfect "Harmony" of bets.

---

# 2. Historical Context

### 2.1. The Syndicates (Starlizard)

Starlizard (Tony Bloom) treats football betting like a Hedge Fund. They employ 100+ quants and beat the closing line consistently. Their edge comes from proprietary data (xG, player fatigue models) superior to the bookies. They demonstrated that Sports Betting is a "Prediction Market with Inefficient Pricing".

### 2.2. Geem (2001) & Quantum Annealing

Zong Woo Geem invented **Harmony Search** (HS) in 2001, mimicking jazz improvisation. Traders realized that standard HS was too slow. By adding **Quantum mechanics concepts** (Wave functions), the algorithm could "teleport" its search agents across barriers, drastically speeding up convergence to the Global Minimum.

---

# 3. The Theory: Market Structure & Optimization

### 3.1. The Vig & The Arb

Standard book: 1.90 vs 1.90. (Flip a coin).
Implied Prob: 52.6% + 52.6% = 105.2%. The 5.2% is the "Vig" (Juice).
To win, you must invert the Vig.

* Best Price A: 2.05 (Implied 48.7%).
* Best Price B: 2.05 (Implied 48.7%).
* Sum = 97.4%. Edge = 2.6%.

### 3.2. Quantum Harmony Search (Indicator 091)

**Harmony Memory (HM):** A matrix of solutions (like a population in Genetic Algorithms).
$$ x_{new} = x_{old} + BW \times \epsilon $$
where $BW$ is bandwidth (pitch adjustment).

**Quantum Mutation:**
Instead of a fixed bandwidth, we sample from a Quantum Wave Function (Gaussian or Cauchy distribution) centered on the best known solution.
$$ \psi(x) \propto \frac{1}{\sqrt{2\pi}\sigma} e^{-\frac{(x-\mu)^2}{2\sigma^2}} $$
This allows for "Long Tail" jumps (Tunneling), escaping local traps where standard solvers fail.

---

# 4. Mathematical Derivation

### 4.1. The Arbitrage Formulas

**Surebet Profit:**
$$ P = \frac{Investment}{\sum (1/k_i)} - Investment $$
Where $k_i$ are the odds for outcome $i$.

**Condition:** $\sum \frac{1}{Odds_i} < 1$.

**Kelly Criterion (Value Betting):**
$$ f^* = \frac{bp - q}{b} = \frac{p(b+1) - 1}{b} $$
Where $b = Odds - 1$, $p = True Probability$.

### 4.2. Quantum Tunneling Logic

In QHS, the probability density function (PDF) of a quantum particle appearing at location $x$ is used to determine the mutation step size.
Using a **Cauchy Distribution** instead of Gaussian increases the probability of generating a solution far from the current mean (Tunneling), vital for navigating the sparse "Arb Landscape".

---

# 5. The Strategy Rules

### 5.1. Finding Arbs (The Scanner)

* **Universe:** Scan 50+ Bookmakers (Pinnacle, Bet365, William Hill, etc.) for all liquid sports (Football, NBA, Tennis).
* **Logic:**
    1. Normalize Team Names (fuzzy matching).
    2. Find max odds for Home, Draw, Away.
    3. Calculate Margin: $M = \frac{1}{O_{Home}} + \frac{1}{O_{Draw}} + \frac{1}{O_{Away}}$.
    4. If $M < 1.0$: Signal Generated.

### 5.2. Portfolio Composition (The QHS Optimizer)

* **Input:** List of 100 potential Arbs.
* **Constraints:**
  * Max Bankroll: $10,000.
  * Max Exposure per Bookie: $500 (to avoid flags).
  * Correlation Check: No conflicting outcomes (though rare in pure Arb).
* **Objective:** Maximize Total Profit subject to Constraints.
* **Algo:** Run QHS Loop for 1000 iterations to select the optimal subset of bets.

### 5.3. Execution

* **Parallelization:** Execute all legs of the Arb simultaneously (within ms) to avoid "Legging Risk" (Price changing while you bet).
* **Stealth:** Round stakes to nearest $5 (e.g., bet $105, not $104.32).

---

# 6. Implementation: Production Grade

### 6.1. Python: Sports Arb Scanner

*(From Strategy 93 Source)*

```python
import pandas as pd

def find_arbitrage(odds_data):
    # odds_data: DataFrame with columns ['Event', 'Bookie', 'Selection', 'Odds']
    arbs = []
    events = odds_data['Event'].unique()
    
    for event in events:
        event_odds = odds_data[odds_data['Event'] == event]
        
        # Best odds for each outcome
        best_home = event_odds[event_odds['Selection'] == 'Home']['Odds'].max()
        best_away = event_odds[event_odds['Selection'] == 'Away']['Odds'].max()
        # Handle Draw if exists...
        
        margin = (1/best_home) + (1/best_away)
            
        if margin < 1.0:
            roi = (1 / margin) - 1
            arbs.append({
                'Event': event,
                'Home': best_home,
                'Away': best_away,
                'ROI': roi
            })
            
    return pd.DataFrame(arbs)
```

### 6.2. Python: Quantum Harmony Search Optimizer

*(From Indicator 091 Source - Fully Integrated)*

```python
import numpy as np

class QuantumHarmonySearch:
    def __init__(self, objective_function, bounds, hm_size=10, max_iter=1000):
        self.obj = objective_function
        self.bounds = bounds
        self.hm_size = hm_size
        self.max_iter = max_iter
        self.hm = [] # Harmony Memory
        
    def initialize(self):
        # Random initialization
        for _ in range(self.hm_size):
            sol = [np.random.uniform(b[0], b[1]) for b in self.bounds]
            score = self.obj(sol)
            self.hm.append((sol, score))
        self.hm.sort(key=lambda x: x[1])
        
    def improvise(self):
        # Generate new harmony
        new_sol = []
        for i, bound in enumerate(self.bounds):
            if np.random.rand() < 0.9: # HMCR (Memory Consideration)
                # Pick from memory
                val = self.hm[np.random.randint(0, self.hm_size)][0][i]
                if np.random.rand() < 0.3: # PAR (Pitch Adjust)
                    # Quantum Mutation (Gaussian/Cauchy Jump)
                    bandwidth = (bound[1] - bound[0]) * 0.05
                    val += np.random.normal(0, bandwidth)
            else:
                # Random exploration
                val = np.random.uniform(bound[0], bound[1])
            new_sol.append(max(min(val, bound[1]), bound[0]))
            
        return new_sol

    def run(self):
        self.initialize()
        for _ in range(self.max_iter):
            new_sol = self.improvise()
            new_score = self.obj(new_sol)
            # Update Memory if better than worst
            if new_score < self.hm[-1][1]: 
                self.hm[-1] = (new_sol, new_score)
                self.hm.sort(key=lambda x: x[1])
        return self.hm[0]
```

### 6.3. Rust: High Performance Improvisation

*(From Indicator 091 Source)*

```rust
// Parallelize the improvisations
pub fn run_qhs(settings: SimulationSettings) -> StrategyParams {
    let best_harmony = (0..10_000).into_par_iter().map(|_| {
        attempt_improvisation()
    }).min_by_key(|h| h.score);
    
    best_harmony
}
```

---

# 7. Risk Management

### 7.1. Account Sustainability

If you only bet arbs, you will be flagged in 10 bets. "Gubbed" (Limited to $0 stake).
**Techniques:**

1. **Mug Betting:** Place dumb bets (accumulator on favorites) to look like a square.
2. **Round Numbers:** Bet \$50, not \$53.42.
3. **Withdrawals:** Don't withdraw after every win.

### 7.2. Void Risk

Bookie A cancels the bet (Palpable Error). Bookie B stands. You are now naked on one side.
**Rule:** Arbs > 5% are usually errors. Avoid them. Use "Sharp" books (Pinnacle) and Exchanges (Betfair) that welcome winners whenever possible.

---

# 8. Conclusion

Strategy 93 is the **Grandmaster**.
It doesn't care who wins the game. It solves the game.
It uses **Quantum Harmony Search** to navigate the complex landscape of global sports odds, optimizing the "Portfolio of Bets" rather than just finding single opportunities.
It ensures that even as the tempo of the market changes, the music remains harmonious.
