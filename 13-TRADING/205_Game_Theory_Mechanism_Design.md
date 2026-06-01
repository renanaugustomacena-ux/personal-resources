# 205 — Game Theory and Mechanism Design in Trading

> Strategic interaction in markets. Covers Nash equilibria, dominance, mixed strategies, sequential games, repeated games, Bayesian games, signaling, and mechanism design (auction theory, optimal contracts). Trading applications include market making competition, optimal auction strategies (call auctions, IPOs, Treasury auctions), HFT competition, principal-agent problems in fund management, and adverse-selection markets. Self-contained beyond the prerequisites of document 200.

---

## Table of Contents

1. [Why Game Theory for Trading](#why-game-theory)
2. [Strategic Form Games and Nash Equilibrium](#strategic-form)
3. [Dominance and Iterated Dominance](#dominance)
4. [Mixed Strategies](#mixed-strategies)
5. [Zero-Sum Games and Minimax](#zero-sum)
6. [Extensive Form and Subgame Perfection](#extensive-form)
7. [Bayesian Games and Incomplete Information](#bayesian-games)
8. [Repeated Games and Folk Theorems](#repeated-games)
9. [Auction Theory — First-Price, Second-Price, English, Dutch](#auction-theory)
10. [Revenue Equivalence and Optimal Auctions](#optimal-auctions)
11. [Common Value Auctions and the Winner's Curse](#common-value)
12. [Mechanism Design](#mechanism-design)
13. [Signaling Games](#signaling-games)
14. [Principal-Agent Problems](#principal-agent)
15. [Trading Applications — Market Making Competition](#mm-competition)
16. [Trading Applications — IPO and Treasury Auctions](#ipo-treasury)
17. [Trading Applications — HFT Equilibria](#hft-equilibria)
18. [Trading Applications — Adverse Selection in OTC Markets](#otc-adverse)
19. [Reality Checks](#reality-checks)
20. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Why Game Theory for Trading

Markets are not neutral playing fields. Every price, every order, every trading decision is the product of strategic interaction among heterogeneous participants — informed traders, market makers, hedgers, arbitrageurs, retail investors, regulators. Each player's optimal action depends on what they expect others to do, and game theory is the mathematical framework for reasoning about such interactions.

Consider three concrete scenarios:

1. **Two market makers competing on quotes.** Each chooses spreads to maximize expected profit. Their decisions are coupled: my optimal spread depends on yours. The result is a Nash equilibrium of spreads, which can be tighter or wider than the monopolist's, depending on the model.

2. **A trader bidding in a Treasury auction.** Each bidder submits a price-quantity schedule. The auction's design (uniform price vs discriminatory) and the bidders' beliefs about each other's valuations determine the equilibrium bidding strategy. The optimal bid in a uniform-price auction is *not* one's true valuation.

3. **A hedge fund manager and their investor.** The manager's effort is unobservable; only the fund's performance is observed. The investor's compensation contract (typically 2/20) is the result of an optimal-contract problem under asymmetric information.

In each case, naive optimization (treating other players as fixed) gives the wrong answer. Game theory gives the right one — provided the model is calibrated to the actual strategic environment.

This document develops the theory and applies it to trading. The mathematical apparatus is mostly the standard one (Nash equilibrium, subgame perfect Nash, Bayesian Nash equilibrium, Vickrey-Clarke-Groves mechanisms), but we emphasize the *trading interpretation*: how each result maps to actual market structure, and where the mathematical assumptions break.

A note on scope. Cooperative game theory (Shapley values, coalition formation) appears in finance mostly via attribution and pricing of liquidity provision; we touch on it briefly. The main focus is non-cooperative — traders pursuing individual profit. The link to mechanism design — which non-cooperative environments can be engineered to deliver socially desirable outcomes — is the practical bridge: exchanges, regulators, and fund managers all design environments to elicit specific behaviors.

---

## Strategic Form Games and Nash Equilibrium

A **strategic form game** (or normal form game) is a tuple Γ = (N, {S_i}, {u_i}), where:

- N = {1, …, n} is the set of players.
- S_i is the strategy set of player i.
- u_i : S_1 × … × S_n → ℝ is the payoff function of player i.

A **strategy profile** is s = (s_1, …, s_n). Each player chooses a strategy simultaneously and independently. Each then receives payoff u_i(s).

### Nash Equilibrium

A profile s* is a **Nash equilibrium** if no player has a profitable unilateral deviation:

$$
u_i(s_i^*, s_{-i}^*) \ge u_i(s_i, s_{-i}^*) \quad \text{for all } s_i \in S_i, \text{ all } i.
$$

Here s_{-i} = (s_1, …, s_{i-1}, s_{i+1}, …, s_n). The Nash condition says: given everyone else's strategy, each player's strategy is a best response.

### Existence

For finite games, Nash (1950) proved that a (mixed-strategy) Nash equilibrium always exists. For continuous-strategy games with continuous payoffs and convex strategy spaces, Glicksberg's theorem and Debreu's theorem give existence. Without convexity, equilibria may not exist in pure strategies but always exist in mixed.

### Multiplicity

Nash equilibria are not unique. Many games have multiple equilibria. Refinements (subgame perfection, perfect equilibrium, sequential equilibrium, Bayesian Nash, trembling-hand perfect) are designed to select among them.

### A Trading Example: Market-Making Cournot

Two market makers compete on bid-ask spreads. Each chooses spread δ_i. Customers split between makers in proportion to (max spread - my spread). Each maker's profit is δ_i × (their share). Solving for Nash equilibrium gives equal spreads at a level lower than the monopolist's optimum but higher than zero — the "duopoly spread."

```python
# Two-MM Cournot-like game.
import numpy as np
from scipy.optimize import minimize

def best_response(delta_other, alpha=1.0, beta=2.0):
    """Best response of MM 1 to MM 2's spread."""
    # Profit_1(d) = d * share_1, where share_1 = beta - d + alpha*delta_other
    # Maximize over d: d* = (beta + alpha*delta_other) / 2
    return (beta + alpha*delta_other) / 2

# Nash via fixed point
delta1, delta2 = 1.0, 1.0
for _ in range(50):
    delta1 = best_response(delta2)
    delta2 = best_response(delta1)

print(f"Nash spreads: δ1={delta1:.4f}, δ2={delta2:.4f}")
```

### Reality Check — Nash in Real Trading

Real market participants do not solve Nash equilibrium problems analytically. They use:
- **Heuristics**: rules of thumb that empirically work.
- **Learning**: adapt strategy based on observed outcomes.
- **Imitation**: copy strategies that others appear to find profitable.
- **Imperfect information**: assume some structure about others.

Behavioral game theory (Camerer 2003) studies how real players deviate from Nash. The deviations are systematic — risk aversion, loss aversion, framing effects — and matter for predicting actual market behavior. We touch on these in document 217 (Behavioral Finance).

---

## Dominance and Iterated Dominance

A strategy s_i **strictly dominates** s_i' if u_i(s_i, s_{-i}) > u_i(s_i', s_{-i}) for all s_{-i}. A strategy is **strictly dominated** if there exists another strategy that strictly dominates it.

### Iterated Removal of Dominated Strategies

Repeatedly delete strictly dominated strategies. The result is the set of strategies "rationalizable" by common knowledge of rationality. Some games solve completely under iterated dominance (e.g., the prisoner's dilemma); others reduce to a smaller game with multiple equilibria.

### Trading Example: Bidding in a Common-Value Auction

In a sealed-bid auction for an asset of unknown common value, bidding above the expected value is dominated (you lose money). Bidding very low is dominated by bidding slightly higher (you almost never win, so the strategy is dominated for any prior). Iterated dominance narrows the rational bid range, then the equilibrium concept selects within it.

### Weak Dominance

A strategy weakly dominates if it is at least as good for all opponent strategies and strictly better for at least one. Weakly dominated strategies are sometimes used in equilibrium (e.g., in second-price auctions, bidding truthfully is weakly dominant).

---

## Mixed Strategies

A **mixed strategy** is a probability distribution over pure strategies. For a game with strategy set S_i, a mixed strategy σ_i ∈ Δ(S_i) assigns probability σ_i(s) to each pure strategy.

### Why Mixed?

Some games have no Nash equilibrium in pure strategies. Example: matching pennies. Player 1 wants matching outcomes; Player 2 wants mismatched. No pure-strategy choice is best for either, since the other can always counter. The unique Nash equilibrium is each player playing 50-50 — pure randomness. Both players are *indifferent* among pure strategies in equilibrium.

### Existence of Mixed Nash

Nash's theorem: every finite game has at least one Nash equilibrium in mixed strategies. The proof uses Brouwer's fixed point theorem applied to the best-response correspondence.

### Computing Mixed Nash

For two-player zero-sum games, mixed Nash is a linear programming problem (minimax). For two-player non-zero-sum, it is the Lemke-Howson algorithm. For larger games, computational complexity is PPAD-complete (no known polynomial algorithm).

### Trading Use

Mixed strategies appear in:
- **Bluffing** in poker-style asymmetric-information games.
- **Random sampling** in execution algos to avoid pattern detection.
- **Arms-race equilibria** in HFT, where each player randomizes order placement timing to prevent counterparty pattern matching.

---

## Zero-Sum Games and Minimax

A **zero-sum game** has u_1(s) + u_2(s) = 0 for all s. Equivalently, one player's gain is the other's loss.

### Minimax Theorem

Von Neumann (1928): for a finite zero-sum game with mixed strategies,

$$
\max_{\sigma_1} \min_{\sigma_2} \mathbb{E}_{\sigma_1, \sigma_2}[u_1] = \min_{\sigma_2} \max_{\sigma_1} \mathbb{E}_{\sigma_1, \sigma_2}[u_1].
$$

The common value is the **value of the game** v. Each player has a *minimax* (or *security*) strategy that guarantees at least v (for player 1) or at most −v (for player 2).

### LP Formulation

Player 1's minimax strategy solves:

Maximize v subject to:
$$
\sum_{s_1} \sigma_1(s_1) u_1(s_1, s_2) \ge v \quad \text{for all } s_2,
$$
$$
\sum_{s_1} \sigma_1(s_1) = 1, \qquad \sigma_1 \ge 0.
$$

A standard LP solvable in polynomial time.

### Trading Application: Robust Portfolio Optimization

Treat the worst-case adversary as nature: choose a portfolio that maximizes worst-case return over a set of plausible scenarios. This is a zero-sum game between you and "the market."

```python
import numpy as np
from scipy.optimize import linprog

# Robust portfolio: maximize worst-case return across scenarios.
# 3 assets, 4 scenarios (returns matrix A: scenario × asset).
np.random.seed(0)
A = np.array([
    [0.05, 0.02, 0.03],   # scenario 1
    [-0.02, 0.06, 0.01],  # scenario 2
    [0.03, -0.01, 0.04],  # scenario 3
    [0.01, 0.03, -0.02],  # scenario 4
])
n_assets, n_scenarios = 3, 4

# Maximize v subject to A @ w >= v, sum(w) = 1, w >= 0
# In LP form: minimize -v subject to v - A @ w <= 0, sum(w) = 1
c = np.zeros(n_assets + 1)
c[-1] = -1  # maximize v

# Constraints
A_ub = np.zeros((n_scenarios, n_assets + 1))
A_ub[:, :n_assets] = -A
A_ub[:, -1] = 1
b_ub = np.zeros(n_scenarios)

A_eq = np.zeros((1, n_assets + 1))
A_eq[0, :n_assets] = 1
b_eq = np.array([1.0])

bounds = [(0, None)] * n_assets + [(None, None)]

result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
print(f"Robust weights: {result.x[:n_assets]}")
print(f"Worst-case return: {result.x[-1]:.4f}")
```

### Reality Check — Zero-Sum Idealization

Trading is rarely strictly zero-sum. The non-zero-sum aspects:
- Liquidity provision creates value (the providers gain spread; the takers gain immediacy).
- Information aggregation creates value (price discovery benefits all).
- Transaction costs (fees, market impact) destroy value.
- Risk transfer creates value (the holder of risk gets compensated; the bearer gets cheaper hedging).

The zero-sum view is sometimes useful (HFT vs slower participants in a fixed-pie scenario) but always an approximation.

---

## Extensive Form and Subgame Perfection

The extensive form represents games with sequential moves and information sets. Players choose actions at decision nodes; the game tree captures the temporal structure.

### Game Tree

A game tree is a directed tree with:
- Decision nodes for each player.
- Information sets (groups of nodes the player cannot distinguish).
- Terminal nodes with payoffs.

### Subgame Perfect Nash Equilibrium (SPNE)

A SPNE is a Nash equilibrium that is also a Nash equilibrium of every subgame. Equivalently: backward induction. Solve the game from the last decision node backward, replacing each subgame with its equilibrium outcome.

### Application: Stackelberg Game in Market Making

Two MMs decide spreads sequentially. The first mover (leader) commits, then the second (follower) responds. Backward induction:

1. Follower's best response to leader's spread δ_L: δ_F = (β + α δ_L)/2.
2. Leader anticipates follower's response and maximizes:
$$
\max_{\delta_L} \delta_L \cdot \text{share}_L(\delta_L, \delta_F(\delta_L)).
$$

The leader's optimal spread differs from the simultaneous Nash. Leadership is valuable (or not) depending on market parameters.

### Reality Check — Sequential Moves in Real Trading

Real markets are continuous; the "first mover" advantage is microsecond-scale. The Stackelberg framework is useful for:
- IPO underwriting: the underwriter sets the price; investors respond.
- Block trading: the block-trader broadcasts; counterparties respond.
- Programmatic trading: an algo is committed; the market reacts.

In each case, the sequential structure matters and game-theoretic analysis is appropriate.

---

## Bayesian Games and Incomplete Information

In a **Bayesian game**, players have *types* drawn from a known distribution. Each player knows their own type but only the distribution of others'. Strategies map types to actions.

### Setup

- Players: 1, …, n.
- Type spaces: T_i for each player.
- Joint distribution over types: F(t_1, …, t_n).
- Action spaces: A_i.
- Payoff functions: u_i(a, t).

A strategy σ_i : T_i → Δ(A_i) maps types to action distributions.

### Bayesian Nash Equilibrium (BNE)

A profile {σ_i} is a BNE if for each player i and each type t_i:

$$
\sigma_i(t_i) \in \arg\max_{a_i} \mathbb{E}_{t_{-i} \mid t_i} \!\left[ u_i(a_i, \sigma_{-i}(t_{-i}), t_i, t_{-i}) \right].
$$

Each type plays a best response to the strategies of others, given their type-conditional belief.

### Trading Example: First-Price Auction with Private Values

Bidders' valuations v_i are iid Uniform[0, 1]. Each bidder submits a sealed bid b_i. The highest bidder wins, paying their bid. In equilibrium, bidder i bids:

$$
b_i^*(v_i) = \frac{n-1}{n} v_i.
$$

Where n is the number of bidders. Bidders shade below their true valuation; the shading shrinks as n grows.

The BNE is the *unique* symmetric increasing equilibrium. Asymmetric equilibria exist but are typically less plausible.

```python
# First-price auction simulation: BNE bid is (n-1)/n * v.
import numpy as np
np.random.seed(42)

n_bidders, n_trials = 5, 10000
v = np.random.uniform(0, 1, (n_trials, n_bidders))
b = (n_bidders - 1) / n_bidders * v  # BNE bid
winner = b.argmax(axis=1)
profit = np.zeros(n_trials)
for i in range(n_trials):
    profit[i] = v[i, winner[i]] - b[i, winner[i]]

print(f"Average winning bidder profit: {profit.mean():.4f}")
print(f"Average price (winning bid): {b.max(axis=1).mean():.4f}")
print(f"Average winning value: {v.max(axis=1).mean():.4f}")
```

---

## Repeated Games and Folk Theorems

A **repeated game** plays a stage game finitely or infinitely many times. Players can condition strategies on history.

### Finitely Repeated Games

By backward induction, the unique SPNE is to play the Nash equilibrium of the stage game in every period — *if* the stage game has a unique Nash. With multiple Nash, more outcomes are sustainable.

### Infinitely Repeated Games

Players discount future payoffs by δ ∈ (0, 1). The "Folk Theorem" (Friedman 1971, Aumann–Shapley 1976): for δ sufficiently close to 1, *any* feasible payoff profile that gives each player at least their minimax value is sustainable as a SPNE.

This is both a positive result (cooperation is sustainable) and a negative result (the theory has too much equilibrium multiplicity to make sharp predictions).

### Trit-for-Tat / Grim-Trigger Strategies

In repeated prisoner's dilemma, "always defect" is a Nash equilibrium for any δ. But cooperation can be sustained by:
- **Grim trigger**: cooperate until anyone defects, then defect forever.
- **Tit-for-tat**: do what the opponent did last period.

For δ above a threshold (depends on payoffs), these strategies are SPNE.

### Trading Application: Implicit Cooperation Among MMs

If a few large MMs dominate a market, repeated interactions could in principle sustain wider spreads than competitive Nash predicts. Empirically, this concern motivates regulatory scrutiny of MM consolidation.

The opposite phenomenon — repeated competition driving spreads to zero — is also possible. Real-world MM markets typically settle in between.

---

## Auction Theory — First-Price, Second-Price, English, Dutch

Auctions are central to:
- IPO pricing (book-building, Dutch auction).
- Treasury issuance (uniform-price, discriminatory).
- Equity calls (opening/closing auctions).
- M&A bids.

### Standard Auction Formats

| Format | Mechanism |
|---|---|
| **First-price sealed-bid** | Each bidder submits one sealed bid; highest wins, pays own bid. |
| **Second-price sealed-bid (Vickrey)** | Highest wins, pays second-highest bid. |
| **English (open ascending)** | Auctioneer raises price; bidders drop out; last remaining wins at last price. |
| **Dutch (open descending)** | Auctioneer lowers price; first bidder to accept wins at that price. |
| **Uniform-price** | Multi-unit; all winning bidders pay the same clearing price. |
| **Discriminatory** | Multi-unit; winning bidders pay their own bids. |

### Strategy in Each Format

- **First-price**: shade below valuation. BNE bid is (n−1)/n × v for uniform private values.
- **Second-price**: bid truthfully (weakly dominant strategy).
- **English**: drop out at your valuation (truth-telling is dominant).
- **Dutch**: accept when price equals (n−1)/n × v (equivalent to first-price by strategic equivalence).
- **Uniform-price**: shade (the fact that the marginal bid sets the price for all units).
- **Discriminatory**: shade independently (each bid is paid if it wins).

### Application to Treasury Auctions

US Treasuries use a **uniform-price** auction. Each bidder submits a price-quantity schedule. Bids are accepted in price order until the issue is filled; all accepted bidders pay the lowest accepted price.

The strategic implication: bidders shade quantity at high prices to influence the clearing price downward. Empirical evidence (Bikhchandani–Huang 1989, Hortaçsu et al. 2018) suggests shading is real but small, and the auction generates near-competitive prices.

### Application to IPO Auctions

Some IPOs (Google 2004) used a Dutch auction. The argument: discrimination creates large allocation premiums and harms small bidders. A Dutch auction equalizes treatment.

The empirical result: Dutch IPO underpricing was less than book-building IPO underpricing in some samples, but the format never dominated. Reasons include bidders' uncertainty about post-IPO trading, allocation asymmetries, and underwriter incentives.

---

## Revenue Equivalence and Optimal Auctions

### Revenue Equivalence Theorem (Myerson 1981, Riley–Samuelson 1981)

Under conditions:
- Risk-neutral bidders.
- iid valuations from a continuous distribution.
- Symmetric bidders.
- The same bidder wins in all formats (efficiency).

All standard auction formats yield the same expected revenue. So first-price, second-price, English, and Dutch are revenue-equivalent in expectation.

### Optimal Auctions (Myerson)

When the auctioneer can design the mechanism, what auction maximizes revenue? Myerson's result: the optimal auction has reserve price r* and allocates to the bidder with the highest *virtual valuation*:

$$
\psi(v) = v - \frac{1 - F(v)}{f(v)}.
$$

For uniform [0, 1] values, ψ(v) = 2v − 1, and the optimal reserve is r* = 1/2. So the auctioneer turns away half the bidders to drive up the price.

### Reality Check — Optimal Auctions in Practice

Optimal auctions assume a known distribution of valuations. Real auctions face:
- Unknown distributions.
- Strategic deception (bidders misrepresent valuations).
- Reserve prices that are too high (no sale) or too low (revenue loss).

Practical auctions use heuristic reserves and monitor performance over time.

---

## Common Value Auctions and the Winner's Curse

In a **common value auction**, the asset has the same value to all bidders, but each has a noisy estimate of that value. Examples: oil leases, IPO shares with uncertain demand, off-balance-sheet derivatives.

### Winner's Curse

If each bidder bids their estimate, the winner is the bidder with the highest *positively-biased* estimate. The winner systematically overpays. Rational bidders shade down to compensate, leading to "implicit valuation correction."

For symmetric n-bidder common-value auctions, bidder i with signal s_i should bid:

$$
b_i = \mathbb{E}[v \mid s_i, \text{being highest signal among } n].
$$

This is below 𝔼[v | s_i] because of the conditioning on being the highest.

### Application: IPO Allocation

When an IPO is oversubscribed and allocation is rationed, getting an allocation is informative — it likely means the IPO is overpriced (no one else wanted it as much as you). Astute bidders bid less than face value to anticipate the curse.

### Reality Check — The Curse in Real Markets

Empirical studies show:
- Treasury auction bidders shade below their estimates by amounts roughly consistent with optimal hedging against the curse.
- IPO investors (unconditionally) experience underperformance after first-day pop, partly due to winner's curse logic.
- Real-estate auctions exhibit consistent post-auction depreciation, suggesting curse-driven over-bidding.

---

## Mechanism Design

A **mechanism** is a procedure that takes participants' reports and outputs an outcome plus payments. Mechanism design asks: which mechanisms achieve given objectives in the presence of strategic agents?

### Revelation Principle

Without loss of generality, we can restrict to **direct mechanisms** in which agents truthfully report their types. For any mechanism in which agents' equilibrium strategies achieve outcome O, there is a direct mechanism that implements O with truthful reporting in equilibrium.

This vastly simplifies mechanism design: focus on incentive-compatible direct mechanisms.

### Vickrey-Clarke-Groves (VCG) Mechanisms

The VCG mechanism for allocating an item:
1. Allocate to the bidder with the highest reported value.
2. Charge the winner the *externality* they impose on others — the highest non-winning bid.

For a single item, this is the second-price auction. For multi-item allocation, VCG allocates efficiently and charges payments that elicit truthful reporting.

### Properties of VCG

- **Incentive compatibility (IC)**: truth-telling is dominant strategy.
- **Individual rationality (IR)**: bidders never lose by participating.
- **Efficiency**: the allocation maximizes total welfare.

### Pitfalls of VCG

- **Revenue is not maximized**: VCG is efficiency-optimal but not revenue-optimal.
- **Computational complexity**: for combinatorial auctions, VCG payments require solving multiple optimization problems.
- **Bidder collusion vulnerability**: bidders can collude by agreeing to lose to one another in a coordinated pattern.

### Real-World Mechanism Design

VCG and its variants are used in:
- Combinatorial spectrum auctions (FCC, Ofcom, etc.).
- Sponsored search (Google AdWords originally; modified in 2002).
- DEX matching (some experimental designs).

---

## Signaling Games

A **signaling game** is a Bayesian game where the sender's type is private; the receiver observes a signal that may or may not perfectly reveal the type.

### Spence's Job-Market Signaling

Workers have ability θ ∈ {High, Low}. Each can choose education level e at cost C(e, θ) (lower for high-ability). Employers observe e and pay wage w.

In separating equilibrium: high-ability chooses high education, low-ability chooses low. Employers pay wage equal to expected ability conditional on education. Education signals ability without (necessarily) producing skill.

In pooling equilibrium: both types choose the same education. Employers cannot distinguish; pay average wage. Both types' utility worsens vs separation.

### Trading Application: Insider Trading and Stock Prices

A firm's manager (insider) has private information about the firm's value. Their trading activity (buying or selling) is a signal to outsiders. In equilibrium, large insider buys move prices up; sells move them down. The market discounts public corporate trading (e.g., 10b5-1 plans) because the signal is weaker than informed trading.

### Trading Application: Order Sizes

A large institutional order signals informed flow. Splitting the order into small pieces hides the signal but gives up information rents (cf. document 201 on iceberg detection).

---

## Principal-Agent Problems

In a **principal-agent problem**, the principal hires an agent whose effort is unobservable. The principal observes only the outcome, which depends on effort and noise. The principal designs a contract to incentivize effort.

### Setup

- Principal: outcome y is observed.
- Agent: chooses effort e at cost c(e).
- Outcome distribution: y ∼ p(y | e).
- Agent's utility: u(w(y)) − c(e) where w(y) is the wage.
- Principal's utility: y − w(y).

### Optimal Contract

Two extremes:

1. **Observable effort**: pay fixed wage; agent provides optimal effort.
2. **Unobservable effort with risk-averse agent**: pay a contract w(y) that aligns incentives. Generally, w(y) is increasing in y (rewarding good outcomes), but the precise shape depends on the noise distribution.

### Application: Hedge Fund Compensation

The classic 2/20 fee structure (2% management fee + 20% of profits) is an approximate solution to the principal-agent problem in fund management:
- The 2% fee covers operations and provides risk-aversion-adjusted compensation.
- The 20% performance fee aligns incentives with the investor.

But 2/20 is also flawed:
- High-water marks are necessary to prevent perpetual reset.
- The 20% creates a call option for the manager — they get the upside without symmetric downside.
- The 2% can be excessive when AUM is large.

Empirical studies (Goetzmann–Ingersoll–Ross 2003) suggest the option value of 20% performance fees is substantial — up to 5% of AUM for some funds.

### Reality Check — Real Contracts Are Compromises

The optimal-contract literature is rich, but real contracts are negotiated between human parties with bounded rationality. The 2/20 became a focal point not because it is optimal but because it is *coordinable* — both sides understand it.

---

## Trading Applications — Market Making Competition

We saw a simple two-MM Cournot-like example. The full picture:

### Single MM (Monopolist)

The monopolist charges the spread that maximizes spread × volume:

$$
\delta^* = \arg\max_\delta \delta \cdot V(\delta),
$$

where V(δ) is the volume-spread relationship. For V(δ) = a − bδ, optimum is δ = a/(2b).

### N MMs (Cournot-like)

With n competitors, each chooses spread to maximize their share. In symmetric Nash, the spread is

$$
\delta_n^* = \frac{a}{(n+1)b}.
$$

As n → ∞, spreads → 0 (perfect competition).

### Bertrand-like Competition

If MMs can undercut each other in continuous price, the Bertrand result: the outcome is the "competitive" spread (zero or marginal-cost-driven). In practice, the "marginal cost" of MM is the variance from inventory, the cost of capital, and the latency of cancellation.

### Reality Check — Real MM Competition

Empirical estimates suggest:
- Major US equity stocks: 2–5 actively competing MMs at the inside.
- Major options: 5–10 MMs.
- Crypto: 10–30 algorithmic MMs.

The Cournot/Bertrand equilibria give qualitative direction; the *magnitude* of competition is calibrated empirically.

---

## Trading Applications — IPO and Treasury Auctions

### Treasury Uniform-Price Auction

Bidders submit price-quantity schedules. Bids are filled in price order until the issue clears; all accepted bidders pay the lowest accepted price.

Optimal bidding: shade quantity at high prices (because filling high quantities increases the clearing price, hurting lower-priced fills).

Empirical: shading is small (1–3 basis points typically), suggesting the market is competitive.

### IPO Book-Building

Investment banks build a book of indications of interest from institutional investors. The bank prices the IPO based on demand at various levels, with discretion to allocate to "favored" investors.

Game-theoretic critique: book-building creates rents for the bank and "bookrunner" investors at the expense of issuers. The 2004 Google Dutch auction was a counter-example, but the practice did not become standard.

### Reality Check — Auction Design Matters

The auction format chosen by an issuer materially affects the price obtained. For Treasuries (uniform-price) and equity IPOs (book-building), the choices have stuck with empirical effects:
- Treasury auctions: ~1bp underpricing on average; revenue near competitive.
- Equity IPOs: ~10–20% underpricing on first day; significant transfer from issuers to bookrunners.

---

## Trading Applications — HFT Equilibria

HFT competition is a high-stakes auction for first-mover advantage in detecting and exploiting price moves. Key features:

### Sequential Bidding for Latency

Each HFT firm chooses its co-location investment (latency) endogenously. The Nash equilibrium has all firms investing roughly equally — pure rent-dissipation.

Argument (Budish–Cramton–Shim 2015): the HFT arms race destroys social value through duplicate infrastructure investment. Frequent batch auctions (every 100ms, say) would eliminate the arms race without sacrificing price discovery.

### Counterparty Selection

HFT firms internalize order flow heterogeneously: high-toxicity flow is rejected, low-toxicity is accepted. The resulting equilibrium has spreads that reflect average toxicity; dislike for individual orders is encoded in venue selection and SDP rebates.

---

## Trading Applications — Adverse Selection in OTC Markets

OTC markets (corporate bonds, swaps, structured products) feature dealer-to-dealer and dealer-to-client trades. Dealers have private information about trade flow; clients have private information about their valuations.

### Dealer Quoting Strategy

A dealer quoting on a bond:
- Makes a positive-expected-value spread on routine flow.
- Adjusts quotes based on observed order flow (toxicity detection).
- Faces an information-quality vs price-competitiveness trade-off.

Game-theoretic equilibrium: the dealer's optimal quote is a function of perceived counterparty type, recent flow toxicity, and dealer inventory.

### Client Best-Execution Strategies

Clients trying to get tight spreads:
- Trade across multiple dealers (to avoid capture by one).
- Use RFQ (request for quote) protocols.
- Time trades to coincide with periods of low toxicity.

The client-dealer interaction is itself a Bayesian game with private information on both sides.

---

## Reality Checks

### Behavioral Departures

Real players deviate from Nash:
- Risk aversion (loss aversion in Kahneman–Tversky).
- Bounded rationality (limited computation).
- Reciprocity and fairness preferences.

Behavioral game theory (Camerer 2003) catalogs these systematically. For trading, the deviations matter mostly in retail-dominated markets and in pre-Nash learning periods.

### Common Knowledge Assumption

Nash equilibrium assumes "common knowledge of rationality" — everyone knows everyone is rational, knows that they know, etc. This rarely holds in practice. Equilibrium concepts that relax common knowledge (e.g., rationalizability, level-k thinking) often predict different behavior.

### Computability

Computing Nash equilibria for large games is PPAD-complete — no known polynomial algorithm. Trading agents must use approximation. The question of which approximations work is a research area (computational learning theory in games).

### Multiple Equilibria

Most non-trivial games have multiple equilibria. Selecting among them requires additional principles (focal points, history-dependence, evolutionary stability). The selection often matters more for predictions than the equilibrium concept itself.

---

## Reference Tables, Cheat Sheets, Bibliography

### Equilibrium Concepts

| Concept | Game Class | Strength |
|---|---|---|
| Dominance | Any | Strong; rare to apply |
| Iterated dominance | Any | Common-knowledge of rationality |
| Nash equilibrium | Any | Standard |
| Subgame perfect | Extensive form | Refines Nash; backward induction |
| Bayesian Nash | Bayesian games | Standard for incomplete info |
| Sequential equilibrium | Extensive Bayesian | Refines BNE; consistent beliefs |
| Trembling-hand perfect | Any | Refines Nash; robustness to errors |

### Auction Formats

| Format | Strategy | Revenue (private values) |
|---|---|---|
| First-price | Shade ((n-1)/n)v | Same as second-price by RET |
| Second-price | Truthful | Same |
| English | Truthful | Same |
| Dutch | Shade ((n-1)/n)v | Same |
| Uniform-price | Shade quantity | Below efficient |
| Discriminatory | Shade independently | Lower |

### Bibliography

- **Fudenberg, D. and Tirole, J. (1991), *Game Theory*, MIT Press.** The standard reference.
- **Osborne, M. and Rubinstein, A. (1994), *A Course in Game Theory*, MIT Press.** More mathematical.
- **Mas-Colell, A., Whinston, M., Green, J. (1995), *Microeconomic Theory*, Oxford.** Comprehensive microeconomics including game theory.
- **Krishna, V. (2009), *Auction Theory* (2nd ed.), Academic Press.** Auction theory reference.
- **Myerson, R. (1981), "Optimal Auction Design", *Mathematics of Operations Research* 6(1): 58–73.** Optimal auctions.
- **Vickrey, W. (1961), "Counterspeculation, Auctions, and Competitive Sealed Tenders", *Journal of Finance* 16(1): 8–37.** Vickrey auction.
- **Bikhchandani, S. and Huang, C. (1989), "The Economics of Treasury Securities Markets", *Journal of Economic Perspectives* 7(3): 117–134.** Treasury auctions.
- **Budish, E., Cramton, P., Shim, J. (2015), "The High-Frequency Trading Arms Race", *Quarterly Journal of Economics* 130(4): 1547–1621.** HFT and FBA.
- **Camerer, C. (2003), *Behavioral Game Theory*, Princeton.** Behavioral departures.
- **Aumann, R. (1974), "Subjectivity and Correlation in Randomized Strategies", *Journal of Mathematical Economics* 1(1): 67–96.** Correlated equilibrium.
- **Spence, A. (1973), "Job Market Signaling", *Quarterly Journal of Economics* 87(3): 355–374.** Signaling.

### Cross-References

- Document 201 — Market Microstructure Theory.
- Document 217 — Behavioral Finance.
- Document 200 — Stochastic Calculus.

---

*End of document 205. ~1,700 lines.*
