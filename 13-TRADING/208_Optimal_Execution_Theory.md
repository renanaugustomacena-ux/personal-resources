# 208 — Optimal Execution Theory

> Mathematical framework and practical algorithms for trading large orders without paying excessive impact. Covers Almgren–Chriss mean-variance, Bertsimas–Lo dynamic programming, Obizhaeva–Wang LOB resilience, Cartea–Jaimungal stochastic control, signal-aware execution, dark pool routing, smart order routers, transaction cost analysis, and reinforcement learning for execution. Self-contained beyond documents 200, 201.

---

## Table of Contents

1. [Why Execution Theory](#why-execution)
2. [Implementation Shortfall — The Master Metric](#implementation-shortfall)
3. [Market Impact Models — A Recap](#impact-models)
4. [Almgren–Chriss Framework](#almgren-chriss)
5. [Bertsimas–Lo Dynamic Programming](#bertsimas-lo)
6. [Obizhaeva–Wang LOB Resilience](#obizhaeva-wang)
7. [Gatheral Propagator Models](#gatheral-propagator)
8. [Cartea–Jaimungal Stochastic Control](#cartea-jaimungal)
9. [Signal-Aware Execution](#signal-aware)
10. [Multi-Asset Basket Execution](#multi-asset)
11. [Dark Pool Routing](#dark-pool)
12. [Adverse Selection in Dark](#adverse-dark)
13. [VWAP and TWAP Algorithms](#vwap-twap)
14. [Implementation Shortfall (IS) Algorithms](#is-algos)
15. [POV (Participation Rate) Algorithms](#pov)
16. [Liquidity-Seeking Strategies](#liquidity-seeking)
17. [Smart Order Routing](#sor)
18. [Slippage Decomposition](#slippage)
19. [Pre-Trade Analytics](#pre-trade)
20. [Post-Trade TCA](#post-trade-tca)
21. [Reinforcement Learning for Execution](#rl-execution)
22. [Adversarial Considerations](#adversarial)
23. [Cross-Impact Models](#cross-impact)
24. [Optimal Market Making](#mm-optimization)
25. [Reality Checks](#reality-checks)
26. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Why Execution Theory

A signal generates expected returns of, say, 10 basis points per trade. The bid-ask spread is 5 basis points. Market impact for the desired size is another 7 basis points. After costs, the trade has a *negative* expected value. The signal had alpha; the implementation lost it.

Execution theory addresses this gap. It provides:

1. **Cost-aware sizing**. How big can a trade be before market impact erodes the alpha?
2. **Cost-aware timing**. How fast should we trade? Faster → more impact; slower → more price risk.
3. **Cost-aware routing**. Lit vs dark? Aggressive vs passive? Across venues?
4. **Cost-aware structure**. Can we exploit the structure of the impact function (square-root, power-law) to reduce cost?

The literature converges on a small set of canonical models — Almgren–Chriss, Obizhaeva–Wang, Cartea–Jaimungal — that each capture a different aspect of the trade-off. Real production algorithms (TWAP, VWAP, POV, IS, liquidity-seeking) are calibrated descendants of these models, with engineering compromises for tractability.

Two theses shape the field:

1. **Impact is convex in trade rate**. Trading twice as fast does *more* than twice the impact. This means there is value in spreading trades over time.

2. **Impact decays in time**. Temporary impact reverses; permanent impact does not. The decomposition matters because temporary impact is *recoverable* — if you trade carefully, you can avoid paying it twice.

The execution problem is to balance these forces against price risk (which favors faster trading) and against any alpha decay (which also favors faster trading when alpha exists). Document 201 covers the empirical microstructure that the execution models build on; document 211 covers backtest discipline that prevents fooling yourself with bad cost models.

---

## Implementation Shortfall — The Master Metric

**Implementation Shortfall (IS)** measures the difference between the price at which a decision was made and the average price actually achieved, including any unfilled quantity opportunity cost. Formally, for a parent order to buy X shares, decided at price P_0:

$$
\text{IS} = \frac{1}{X} \!\left[ \sum_i (\tilde P_i - P_0) Q_i + (X - \sum Q_i)(P_T - P_0) \right],
$$

where $Q_i$ are filled quantities at prices $\tilde P_i$, $P_T$ is the final market price, and the term $(X - \sum Q_i)$ is unfilled quantity. The first term is **realized cost** of fills; the second is **opportunity cost** of unfilled portion.

### Decomposition

Useful decomposition (Perold 1988):

- **Spread cost**: half-spread paid on each fill ≈ |P̃_i − M_i|, where M_i is mid at fill time.
- **Impact cost**: market move attributable to your own trading.
- **Timing cost (alpha decay)**: market drift between decision and execution.
- **Opportunity cost**: from unfilled portion.

Decomposition is approximate — separating impact from timing requires modeling. Common approach: assume impact follows a model (e.g., square-root), subtract; the remainder is timing.

### Pre-Trade Estimation

Before submitting, estimate IS via

$$
\hat{\text{IS}} \approx \tau \sigma + Y \sigma \sqrt{Q/V},
$$

where τ is expected duration in days, σ is daily volatility, Q is order size, V is daily volume. The first term is **delay risk**; the second is square-root impact.

For a typical 1% ADV order on SPX (σ ≈ 1% daily, V ≈ 100M shares), pre-trade IS estimate is roughly 5–15 basis points depending on duration. This is the cost the execution algo needs to beat.

### Reality Check — IS Definition Wars

The "decision price" is fuzzy. Different conventions:
- Arrival price: when the parent order hits the system.
- Decision price: when the alpha generates the signal.
- Open price: the day's open if order is submitted intraday.

Different choices give different IS numbers. The right convention depends on what you're measuring (algo skill, signal-to-execution lag, etc.). Production desks define and stick to one.

---

## Market Impact Models — A Recap

Three forms of impact:

- **Permanent**: price moves and stays. Reflects information revealed by trading.
- **Temporary**: price moves during execution; reverses after. Reflects liquidity consumption.
- **Realized**: average price during execution vs pre-trade.

### Linear Impact (Kyle's λ)

$$
\Delta P = \lambda Q,
$$

where Q is signed traded quantity. λ is calibrated empirically; for major equities, λ × ADV / σ ≈ 0.1–0.5. Linear impact is appropriate for small orders relative to liquidity.

### Square-Root Impact

$$
\Delta P \approx Y \sigma \sqrt{Q/V},
$$

with Y typically 0.3–0.7. Empirically dominant across asset classes. Universal observation across equities, futures, FX, crypto.

### Propagator Models

Bouchaud–Gefen–Potters–Wyart (2004): impact is path-dependent. Each trade contributes a fading impact:

$$
P_t = \int_{-\infty}^t G(t - s) \xi(s) \, ds,
$$

where ξ(s) is signed trade flow and G is a propagator (typically G(τ) ∝ τ^{-1/2}). Captures both temporary and permanent impact in one framework.

Document 201 covers these in microstructural detail.

---

## Almgren–Chriss Framework

The canonical execution model. Setup:

- Total quantity X to liquidate (or buy) over horizon T.
- Trading rate v_t = -dx_t/dt.
- Mid-price dynamics: $dS_t = -\gamma v_t \, dt + \sigma \, dW_t$ (permanent impact + volatility).
- Execution price: $\tilde S_t = S_t - \eta v_t$ (temporary impact).

The trader's wealth process:

$$
dW_t = -\tilde S_t v_t \, dt + S_t v_t \, dt - x_t \, dS_t = -\eta v_t^2 \, dt - x_t \sigma \, dW_t + (\text{drift terms}).
$$

After algebra, the cumulative cost (vs initial S_0 X) is

$$
\text{Cost} = \frac{1}{2} \gamma X^2 + \int_0^T \eta v_t^2 \, dt + \int_0^T x_t \sigma \, dW_t.
$$

The first term is permanent impact (irreducible); the second is temporary impact (reducible by spreading); the third is price risk (zero mean, finite variance).

### Mean-Variance Objective

Risk-averse trader minimizes expected cost plus λ × variance:

$$
\min_v \mathbb{E}[\text{Cost}] + \lambda \text{Var}(\text{Cost}).
$$

Setting the variation to zero gives the Euler-Lagrange equation:

$$
\eta \ddot x_t = \lambda \sigma^2 x_t.
$$

Solution:

$$
x_t = X \frac{\sinh(\kappa(T - t))}{\sinh(\kappa T)}, \qquad \kappa = \sqrt{\lambda \sigma^2 / \eta}.
$$

For risk-neutral (λ = 0), x_t = X(1 − t/T) — TWAP. For increasing λ, trajectory becomes increasingly front-loaded.

```python
import numpy as np
import matplotlib.pyplot as plt

def almgren_chriss(X, T, sigma, eta, lam, n_pts=100):
    t = np.linspace(0, T, n_pts)
    if lam == 0:
        return t, X * (1 - t/T)
    kappa = np.sqrt(lam * sigma**2 / eta)
    x = X * np.sinh(kappa*(T - t)) / np.sinh(kappa*T)
    return t, x

X, T, sigma, eta = 1e6, 1.0, 0.02, 1e-6
fig, ax = plt.subplots(figsize=(8, 4))
for lam in [0, 1e-7, 1e-6, 1e-5]:
    t, x = almgren_chriss(X, T, sigma, eta, lam)
    ax.plot(t, x/X, label=f'λ={lam:.0e}')
ax.set_xlabel('time'); ax.set_ylabel('residual position')
ax.legend(); ax.grid(True); ax.set_title('Almgren–Chriss trajectories')
plt.tight_layout()
```

### Cost and Variance

Plug in the optimal trajectory:

$$
\mathbb{E}[\text{Cost}] = \frac{1}{2} \gamma X^2 + \frac{1}{2} \eta X^2 \kappa \coth(\kappa T),
$$

$$
\text{Var}(\text{Cost}) = \sigma^2 X^2 \frac{T \coth(\kappa T) - 1}{\kappa^2 T^2 \sinh^2(\kappa T) / \tanh^2(\kappa T)}.
$$

Numerically, the two move in opposite directions as λ varies. The **efficient frontier** of (mean, variance) traces out as λ varies from 0 to ∞.

### Trader's Risk Aversion

Choosing λ is the policy decision. Practical heuristics:
- λ matched to realized P&L volatility tolerance.
- λ from Kelly-like reasoning given alpha and remaining capital.
- λ adjusted for time-of-day or regime.

A common production choice: λ such that the expected cost equals 1-2 standard deviations of the IS distribution. This balances cost minimization with variance reduction.

### Reality Check — A-C Limitations

Almgren-Chriss assumes:
- Linear permanent impact γ. Empirically square-root.
- Linear temporary impact η. Empirically square-root or superlinear.
- Constant volatility. Empirically time-varying.
- No alpha. If alpha exists, A-C is wrong.
- No discrete features (auctions, halts, etc.).

Production extensions: time-varying parameters, square-root impact, signal-aware extensions (Garleanu-Pedersen).

---

## Bertsimas–Lo Dynamic Programming

Bertsimas–Lo (1998) cast the execution problem as dynamic programming under risk-neutral preferences (no variance penalty).

### Setup

Discrete time t = 0, 1, …, T. State: (x_t, S_t) = (residual, price). Cost-to-go: V(t, x, S).

Bellman equation:

$$
V(t, x, S) = \min_{q \in [0, x]} \!\left\{ q \cdot [\tilde S(t, x, S, q) - S] + \mathbb{E}[V(t+1, x - q, S')] \right\}.
$$

The first term is the cost of trading q at the current step; the second is the optimal cost of completing the rest.

### Linear Impact Solution

Under linear impact $\tilde S = S + \eta q + \gamma$ (cumulative permanent), the BL solution has constant trade rate q* = X/T — TWAP. For risk-neutral, no variance gain to deviate.

### Square-Root Impact Solution

Under square-root impact $\tilde S - S = Y \sigma \sqrt{q/V}$, the optimal trajectory is *not* TWAP. The convexity of the impact function pushes optimal toward more uniform trading; the precise solution involves solving a non-trivial PDE.

### Numerical DP

For arbitrary impact functions and constraints, solve the Bellman equation numerically:

```python
import numpy as np

def bertsimas_lo_dp(X, T, V, sigma, impact_fn, n_grid=100):
    """Numerical DP for B-L with arbitrary impact."""
    x_grid = np.linspace(0, X, n_grid + 1)
    V_arr = np.zeros((T + 1, n_grid + 1))
    pol = np.zeros((T, n_grid + 1))
    
    for t in range(T - 1, -1, -1):
        for i, x in enumerate(x_grid):
            best_q, best_val = 0, np.inf
            for q in np.linspace(0, x, 50):
                cost_now = q * impact_fn(q, V)
                next_x = x - q
                next_idx = np.argmin(np.abs(x_grid - next_x))
                val = cost_now + V_arr[t + 1, next_idx]
                if val < best_val:
                    best_val = val
                    best_q = q
            V_arr[t, i] = best_val
            pol[t, i] = best_q
    
    # Reconstruct optimal path
    x = X
    path = [x]
    for t in range(T):
        i = np.argmin(np.abs(x_grid - x))
        q = pol[t, i]
        x -= q
        path.append(x)
    return np.array(path)
```

### Reality Check — DP Curse

Numerical DP becomes intractable for:
- Multi-asset (state space is product).
- Continuous time (need fine grid).
- Many state variables (price, residual, alpha, inventory regime).

For practical purposes, model-driven solutions (A-C, O-W) or learned policies (RL) are preferred.

---

## Obizhaeva–Wang LOB Resilience

Obizhaeva–Wang (2013) introduces *resilience* — temporary impact decays back to fundamental price at rate ρ. Setup:

- Price S_t (fundamental, follows Brownian motion).
- Visible price (where you trade): $P_t = S_t + Y_t$.
- $dY_t = -\rho Y_t \, dt + \eta \, dx_t$ (impact "stock" decays).

For high ρ: temporary impact decays quickly, market is resilient.
For low ρ: impact persists, trading is "sticky."

### Optimal Solution

Under linear permanent and temporary impact with resilience, the optimal trajectory is:
- For high ρ: closer to TWAP (resilience helps anyway).
- For low ρ: front-loaded then a constant rate then a final block (Obizhaeva-Wang showed this analytically).

The closed-form involves four phases for the discrete-time model. Key insight: front-load to "discover" liquidity, settle into constant rate while resilience replenishes, finish with a final push.

### Empirical Resilience

For US equities, resilience time τ = 1/ρ ≈ 1–10 minutes (large-cap) to 30+ minutes (small-cap). For a multi-day execution, resilience matters in the first few hours; for intraday trades, it's the dominant factor.

### Reality Check — Resilience Estimation

Estimating ρ from data is difficult — it requires identifying impact and tracking its decay. Standard methods: regress price moves on lagged trade flow with exponential decay basis. Production calibrations vary widely; cross-check against multiple methods.

---

## Gatheral Propagator Models

Gatheral (2010) and follow-up work formalized impact via propagator kernels:

$$
P_t = S_t^{\text{fund}} + \int_0^t G(t - s) v_s \, ds,
$$

where v_s is signed trade flow rate and G is the propagator kernel.

### No-Arbitrage Constraint

Gatheral showed: for the model to be arbitrage-free (no round-trip profit from trading), the kernel must be *integrable* — ∫ G(τ) dτ < ∞. Power-law decay G(τ) ∝ τ^{-β} is consistent for β > 0.

### Calibration

Empirical estimates of G:
- Decay exponent β ≈ 0.4–0.5 over hours.
- Decay exponent β ≈ 0.7–0.9 over days.
- Power-law in this range; exponential decay is too fast.

### Optimal Execution Under Propagator

For a propagator kernel G, the optimal trading rate for a fixed-horizon liquidation involves an integral equation:

$$
\int_0^T G(t - s) v_s \, ds = \text{constant} - \text{Lagrange multiplier},
$$

solvable numerically. The result is similar in spirit to A-C — front-loaded for risk-averse, uniform for risk-neutral — but the magnitudes differ.

---

## Cartea–Jaimungal Stochastic Control

Cartea, Jaimungal, and Penalva (2015) is the modern reference. The framework:

- State: (t, x, S, q) — time, residual, price, inventory (for market making).
- Control: trading rate v_t, or quote distances δ_a, δ_b.
- Value function: V(t, x, S, q).

HJB equation:

$$
\partial_t V + \mu \partial_S V + \tfrac{1}{2} \sigma^2 \partial_{SS} V + \min_v \!\left\{ -\eta v^2 \cdot \text{stuff} + v \cdot \text{stuff}_2 + \cdots \right\} = 0,
$$

with terminal V(T, 0, S, q) = 0, V(T, x > 0, ·) = -∞ (cannot have residual at end).

### Solution Structure

For linear permanent + linear temporary impact:
- Optimal rate is linear in residual: v* = α(t) x.
- α(t) decreases from a maximum at t = 0 to zero at t = T.
- Closed-form expressions match A-C for risk-aversion case.

For square-root impact, the HJB is solved numerically. The qualitative behavior is similar but quantitatively different.

### Extensions

The framework supports:
- Stochastic volatility.
- Stochastic alpha (Garleanu-Pedersen).
- Multiple assets.
- Dark pool routing.
- Multiple trading venues.

Each extension adds state dimensions and computational cost. Standard treatment: solve HJB on a state grid via finite differences; use the resulting policy for execution.

### Reality Check — Stochastic Control in Practice

Production systems rarely solve HJB at execution time. Instead:
- Calibrate model offline.
- Compute optimal policy table.
- Deploy via lookup at execution time.
- Recalibrate periodically.

This makes stochastic control practical at scale.

---

## Signal-Aware Execution

If the trader has alpha (signal about future returns), the execution problem changes. The simple intuition: if alpha decays quickly, trade aggressively up front to capture; if alpha is patient, trade leisurely to avoid impact.

### Garleanu-Pedersen (2013, 2016)

Garleanu and Pedersen: optimal trading with predictable returns. The key result: the optimal position tracks a moving target that is the static (frictionless) optimum, with a friction-driven smoothing factor.

For a single-asset model with return predictor r̂_t and quadratic costs, the optimal target position is

$$
x_t^* = \frac{r_t}{\lambda \sigma^2} - \frac{1}{\rho_{\text{alpha}}} \!\left[ \text{trading-cost adjustment} \right].
$$

Where $\rho_{\text{alpha}}$ is the decay rate of the alpha signal. For fast-decaying alpha, $1/\rho_{\text{alpha}}$ is small, and the optimal position quickly adapts to the signal. For slow alpha, slower adaptation is optimal.

### Multi-Asset Extension

Garleanu-Pedersen generalizes to multi-asset with quadratic transaction costs:

$$
\Delta x_t^* = (\Lambda + \rho_T \Sigma)^{-1} \rho_T (x_t^{\text{static}} - x_t),
$$

where Λ is the trading-cost matrix, Σ is the return covariance, ρ_T is the discount rate, and $x_t^{\text{static}}$ is the frictionless optimum. The algebra is appealing: the trade is a smoothed step toward the unconstrained optimum, with smoothing depending on cost vs return covariance.

### Implementation in Practice

For a production trade with both alpha and execution cost concerns:
1. Estimate alpha and decay rate.
2. Compute static optimum.
3. Compute the GP-style smoothed target.
4. Use AC-style trajectory to slice between current and target.

---

## Multi-Asset Basket Execution

A basket of N stocks. Execution problem: trade all N simultaneously, sharing impact and price-risk constraints.

### Correlation-Aware Trading

For stocks with positive correlation, executing them together creates *concentration risk* — joint moves are amplified. The right approach:
- Spread execution in time.
- Trade the *principal portfolio* (eigenportfolio of the covariance matrix) rather than individual names.
- Hedge residual with index futures.

### Pairs Execution

For a long-short pair (long A, short B), the relevant variance is the *spread* variance, not the individual asset variance. Execution timing should target spread P&L, not individual fill quality.

### Cross-Impact

Trading A can move the price of correlated B. For sector ETFs and constituents, this is well-documented. Cross-impact matrix:

$$
\Delta S_i = \sum_j \Lambda_{ij} q_j,
$$

where Λ_{ij} is the cross-impact coefficient. Production basket-execution algorithms account for this; naive single-asset algos do not.

### Reality Check — Basket Algos

Multi-asset execution algorithms are vastly more complex than single-asset. Production systems often:
- Decompose into single-asset tasks.
- Coordinate via a higher-level scheduler.
- Hedge basket risk with futures or ETFs.

The clean theoretical framework is not always operational.

---

## Dark Pool Routing

**Dark pools** are alternative trading venues where orders match without displaying quotes. Major US dark pools: Liquidnet, ITG POSIT, Goldman Sigma, JP Morgan JPM-X.

### Why Use Dark Pools

- **Reduce information leakage**: posting in dark hides the order from market predators.
- **Mid-point matches**: trades at NBBO mid (no spread paid).
- **Block-sized matches**: when natural counterparty exists, trade large size in one go.

### Why Not

- **Lower fill rates**: depends on counterparty arrival.
- **Adverse selection**: when filled, often by "smart" counterparty.
- **Regulatory limits**: dark trading caps (US Reg ATS).

### Optimal Lit-Dark Split

The execution algo decides: how much to post in dark, how much to send aggressively to lit?

Decision involves:
- Expected fill probability in dark.
- Adverse selection cost in dark vs spread cost in lit.
- Time pressure.
- Order book depth.

Production heuristic: post 30–60% of the order in mid-peg dark; aggress lit for the residual when slow.

### Probability of Fill Models

Approximate dark pool fill rate as a Poisson process with rate λ depending on market conditions. Time to fill T ~ Exponential(λ).

For a specific dark pool, calibrate λ from historical fills. Multi-pool: aggregate the rates, assume independence (approximate).

---

## Adverse Selection in Dark

When a dark pool order fills, it's because someone wanted the other side. This counterparty may be:
- An institutional with offsetting flow (good).
- An informed trader using dark to avoid signaling (bad).
- An HFT firm gaming dark pools (bad).

Adverse selection in dark is *real*. Empirical estimates:
- Mid-fill in dark followed by adverse mid-move: 20-40% of fills.
- Average post-fill adverse mid-move: 1-2 basis points.
- Worst pools (where toxic flow concentrates): higher.

### Anti-Gaming

Production routers detect toxic flow and reduce dark exposure:
- Track post-fill price moves per dark pool.
- Reduce allocation to pools with high adverse selection rates.
- Use conditional posting (only fill if certain conditions met).

---

## VWAP and TWAP Algorithms

### TWAP (Time-Weighted Average Price)

Trade equal quantity per unit time over horizon T.
- Slice = total / T_steps.
- Execute slice at each step, regardless of market state.

Pros: simple, predictable, low information leakage.
Cons: ignores volume profile; no adaptation to alpha or market state.

### VWAP (Volume-Weighted Average Price)

Trade in proportion to historical volume at each time.
- Slice_t = total × volume_profile_t.
- Volume profile estimated from N days of intraday volume.

Pros: matches market liquidity; standard institutional benchmark.
Cons: deterministic slicing; vulnerable to gaming.

### Implementation

```python
import numpy as np

def vwap_schedule(total_qty, volume_profile, n_slices):
    """Compute VWAP-style trading schedule."""
    weights = volume_profile / volume_profile.sum()
    slices = total_qty * weights
    return slices

# Typical US equity volume profile: U-shaped (high at open and close, low at midday)
n_slices = 13  # 30-minute slices in 6.5-hour trading day
profile = np.array([0.15, 0.10, 0.08, 0.07, 0.06, 0.06, 0.06, 0.06, 0.07, 0.08, 0.09, 0.06, 0.06])
profile = profile / profile.sum()
total = 1_000_000
schedule = vwap_schedule(total, profile, n_slices)
print(f"VWAP schedule (1M total): {schedule.astype(int)}")
```

### Reality Check — VWAP/TWAP in Practice

VWAP/TWAP are *benchmark-tracking* algos, not optimal in the IS sense. They are appropriate when:
- Benchmarked against VWAP/TWAP.
- No alpha (or alpha is uncorrelated with volume).
- Patient execution acceptable.

For alpha-bearing flow, IS-style algorithms are preferred.

---

## Implementation Shortfall (IS) Algorithms

IS algorithms front-load execution to minimize the gap between decision price and average fill price. Built on Almgren-Chriss with extensions.

### Basic IS Algorithm

1. Calibrate (γ, η, σ) for the asset.
2. Choose risk aversion λ.
3. Compute AC trajectory.
4. Slice into discrete pieces.
5. At each step, place order matching the planned size.

### Adaptive IS

Modify the AC trajectory based on real-time conditions:
- If price moves favorably → trade more aggressively (capture price).
- If price moves adversely → trade less (wait for reversal or signal change).
- If volume is high → trade more (more liquidity).
- If volatility spikes → trade faster (lock in price).

These adjustments require careful calibration to avoid overreacting to noise.

### Production IS

Major brokers offer IS algos: Goldman Sigma, ITG Triton, Jefferies JeffEX, Citi LX. Each tunes the AC formulation differently. Performance varies by client and asset class.

---

## POV (Participation Rate) Algorithms

POV algos cap trading at a fraction of market volume:
- Target rate: 10-30% of market volume.
- Variants: fixed POV, volume-aware POV, signal-aware POV.

### Fixed POV

If market trades V_t in interval, you trade min(V_t × p, residual_t).

### Dynamic POV

Adjust p based on:
- Time pressure (closer to deadline → higher p).
- Alpha decay (faster decay → higher p).
- Volatility (higher vol → faster execution).

### Reality Check — POV Pitfalls

POV algos can paradoxically increase impact: when you participate, you push volume higher, which raises your participation cap, leading to feedback. Production POV uses a "look-back" volume estimate rather than current to dampen.

---

## Liquidity-Seeking Strategies

Designed to capture episodic liquidity (large blocks, dark pool fills) without the predictability of TWAP/VWAP.

### Components

- **Mid-peg dark**: post in dark pool at NBBO mid.
- **Conditional dark**: only execute if certain conditions met (e.g., minimum size).
- **Aggressive lit when needed**: take the spread when residual must be cleared.
- **Random slicing**: randomize slice sizes and timing to evade detection.

### When to Use

- Patient execution (no time pressure).
- Large size relative to ADV.
- Less predictable (anti-detection).

### Reality Check — Liquidity-Seeking and Adverse Selection

Liquidity-seeking algos exposes orders to dark pools where adverse selection is significant. Trade-off: lower spread cost vs higher selection cost. Production routes carefully.

---

## Smart Order Routing

The SOR decides which venue gets each slice:

### Simple SOR

For a marketable slice:
1. Identify venue with best displayed price.
2. Send order there.
3. If not filled, route remainder to next-best.

### Sophisticated SOR

Considers:
- Hidden liquidity (dark pools, hidden orders).
- Latency to each venue.
- Fees and rebates (maker-taker).
- Historical fill rates.
- Adverse selection.

### Production SOR

Dynamic ML-driven routing:
- Estimate fill probability per venue per condition.
- Estimate adverse selection per venue.
- Optimize expected cost given current state.

Document 201 covers SOR in microstructural detail.

---

## Slippage Decomposition

For post-trade analysis, decompose total slippage into components:

| Component | Approximate Method |
|---|---|
| Spread cost | Half-spread × volume traded |
| Impact cost | Cumulative impact above pre-trade benchmark |
| Timing cost | Market drift between decision and execution |
| Opportunity cost | Unfilled × subsequent move |

The decomposition helps identify which part of the algo to improve. High spread cost → trade more passively. High impact → trade slower or in dark. High timing cost → trade faster or use signal.

---

## Pre-Trade Analytics

Before submitting, estimate:
- Expected duration based on order size and market liquidity.
- Expected impact based on impact model.
- Expected risk (variance of execution price).
- Confidence intervals on cost estimate.

### Cost Estimation Models

Production firms calibrate proprietary cost models from historical executions. Inputs:
- Order size relative to ADV.
- Volatility regime.
- Time of day.
- Asset class and sector.
- Historical impact for similar trades.

Output: cost distribution (mean, median, 90% CI).

### PROC Workflow (Pre-Trade, Real-Time, On-Trade, Closing)

Standard institutional workflow:
1. **Pre-trade**: estimate costs, choose algorithm.
2. **Real-time monitoring**: deviation from benchmark, intraday alerts.
3. **On-trade adjustment**: switch algo or accelerate if conditions change.
4. **Closing**: ensure full fill or document residual.

---

## Post-Trade TCA

After execution, analyze:
- Realized IS vs benchmark (VWAP, TWAP, IS).
- Slippage decomposition.
- Algorithm performance.
- Venue attribution.
- Time-of-day attribution.

### TCA Metrics

| Metric | Formula |
|---|---|
| IS | (avg fill - decision price) × side |
| Slippage to VWAP | (avg fill - VWAP) × side |
| Slippage to arrival | (avg fill - arrival mid) × side |
| Realized spread | (mid - avg fill) × side |
| Adverse selection | post-fill move × side |
| Reversion | post-fill mean reversion |

### Reality Check — TCA Limitations

TCA tells you what *did* happen, not what *should* have happened. Counterfactual evaluation (what if we had used a different algo?) requires careful causal modeling.

---

## Reinforcement Learning for Execution

Nevmyvaka, Feng, Kearns (2006): cast execution as RL. State = (residual, time, market state). Action = trade quantity. Reward = negative cost.

### Algorithms

- **Q-learning**: tabular for small state spaces; degrades for large.
- **Deep Q-Network (DQN)**: neural net Q-function.
- **PPO/A2C**: actor-critic for continuous action spaces.
- **DDPG**: deterministic policy gradient.

### Production Use

ML-based execution gaining adoption:
- JPMorgan LOXM (2017): DRL-based equity execution.
- Other tier-1 banks: research-grade.
- Some HFT firms: production for specific strategies.

Challenges:
- Train-test gap: simulator differs from live.
- Adversarial dynamics: counterparties may game ML-based algos.
- Sample efficiency: RL needs lots of data to train stable policies.

### Code Skeleton

```python
import numpy as np

class ExecutionEnv:
    def __init__(self, X, T, sigma=0.02, eta=1e-6):
        self.X = X; self.T = T
        self.sigma = sigma; self.eta = eta
        self.reset()
    
    def reset(self):
        self.t = 0
        self.x = self.X
        self.S = 100.0
        return self._state()
    
    def _state(self):
        return np.array([self.t/self.T, self.x/self.X, self.S/100])
    
    def step(self, q):
        cost = q * (self.S - self.eta * q)
        self.x -= q
        self.t += 1
        self.S += self.sigma * np.random.normal()
        done = self.t >= self.T
        return self._state(), -cost, done, {}

# Train DQN, PPO, etc. on this env to learn optimal trading policy
```

---

## Adversarial Considerations

Execution algos face adversarial counterparties:

- **HFT detection**: HFT can fingerprint algos and trade ahead.
- **Predatory dark pools**: some pools concentrate toxic flow.
- **Spoofing**: opposing orders meant to mislead.

### Anti-Detection

Production algos randomize:
- Slice sizes (small ± random factor).
- Timing (jitter on schedule).
- Venue selection.
- Order types (mix of marketable and limit).

---

## Cross-Impact Models

For correlated assets, trading A moves B. Cross-impact matrix Λ:

$$
\Delta S_i = \Lambda_{ii} q_i + \sum_{j \ne i} \Lambda_{ij} q_j.
$$

Λ_{ij} is non-zero for correlated pairs. For a basket trade, optimal execution accounts for cross-impact: the impact of trading A is amplified if you're also trading correlated B simultaneously.

### Calibration

Estimate Λ from observed price moves vs trade flow:

$$
\Delta S_i = \sum_j \Lambda_{ij} q_j + \epsilon_i.
$$

OLS or shrinkage estimator (cross-impacts are noisy).

---

## Optimal Market Making

Market maker problem (recap from doc 201):

Avellaneda-Stoikov: quote bid B = S − δ_b, ask A = S + δ_a. Inventory q. Optimize spread and skew to maximize utility.

Key results:
- Reservation price: r = S − qγσ²(T − t).
- Spread: $\delta^* = \gamma\sigma^2(T-t)/2 + (1/\gamma)\log(1 + \gamma/k)$.
- Skewing: long inventory → tilt quotes toward sell side.

Cartea-Jaimungal extensions:
- Multiple assets.
- Cross-impact.
- Adverse selection adjustments.
- Time-varying volatility.

Document 29 covers Avellaneda-Stoikov in trading context.

---

## Reality Checks

- **Calibration matters**: wrong η or γ gives wrong trajectory.
- **Real-time adaptation**: static plans fail in non-stationary markets.
- **Implementation costs**: production execution adds engineering layer not in models.
- **Regulatory constraints**: best execution rules may force specific routing.
- **Capacity limits**: large funds hit capacity walls that small funds don't.

---

## Reference Tables, Cheat Sheets, Bibliography

### Algorithm Comparison

| Algo | Use case | Behavior | Cost characteristics |
|---|---|---|---|
| TWAP | Time-benchmarked | Constant rate | Linear in time |
| VWAP | Volume-benchmarked | Volume-weighted | Matches market |
| POV | Participation cap | Fixed % of volume | Self-limiting |
| IS | Alpha-driven | Front-loaded | Minimizes shortfall |
| Liquidity-seeking | Patient large | Mid-peg + aggressive | Captures opportunities |
| AC trajectory | Cost-vol balanced | Concave decay | Mean-variance optimal |

### Bibliography

- **Almgren, R. and Chriss, N. (2000), "Optimal Execution of Portfolio Transactions", *J. Risk* 3(2): 5–39.** Canonical.
- **Bertsimas, D. and Lo, A. (1998), "Optimal Control of Execution Costs", *Journal of Financial Markets* 1(1): 1–50.**
- **Obizhaeva, A. and Wang, J. (2013), "Optimal Trading Strategy and Supply/Demand Dynamics", *Journal of Financial Markets* 16(1): 1–32.**
- **Gatheral, J. (2010), "No-Dynamic-Arbitrage and Market Impact", *Quantitative Finance* 10(7): 749–759.**
- **Cartea, Á., Jaimungal, S., Penalva, J. (2015), *Algorithmic and High-Frequency Trading*, Cambridge.**
- **Garleanu, N. and Pedersen, L. (2013), "Dynamic Trading with Predictable Returns and Transaction Costs", *Journal of Finance* 68(6): 2309–2340.**
- **Garleanu, N. and Pedersen, L. (2016), "Dynamic Portfolio Choice with Frictions", *Journal of Economic Theory* 165: 487–516.**
- **Nevmyvaka, Y., Feng, Y., Kearns, M. (2006), "Reinforcement Learning for Optimal Trade Execution", ICML.**
- **Tóth, B. et al. (2011), "Anomalous Price Impact and the Critical Nature of Liquidity in Financial Markets", *Phys Rev X* 1: 021006.**
- **Bouchaud, J., Farmer, J.D., Lillo, F. (2009), "How Markets Slowly Digest Changes in Supply and Demand".**
- **Kyle, A. (1985), "Continuous Auctions and Insider Trading", *Econometrica* 53(6): 1315–1336.**
- **Perold, A. (1988), "The Implementation Shortfall: Paper versus Reality", *Journal of Portfolio Management* 14(3): 4–9.**

### Cross-References

- Document 200 — Stochastic Calculus.
- Document 201 — Microstructure.
- Document 203 — Bayesian (online inference).
- Document 211 — Backtesting.
- Document 29 — Market Making Stoikov.
- Document 34 — VWAP Execution Algo.
- Document 35 — TWAP Execution Algo.

---

*End of document 208. ~1,500 lines.*
