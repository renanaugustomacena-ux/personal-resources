# 201 — Market Microstructure Theory and Practice

> Comprehensive reference on the structure of modern markets and the strategic interaction of participants within them. Covers order book mechanics, the canonical theoretical models (Kyle, Glosten–Milgrom, Easley–O'Hara, Roll), order flow toxicity (PIN, VPIN), market impact (linear, square-root, propagator), optimal execution (Almgren–Chriss, Bertsimas–Lo, Obizhaeva–Wang), market making (Avellaneda–Stoikov, Ho–Stoll, Cartea–Jaimungal), and the practical realities of high-frequency markets — co-location, fragmentation, dark pools, latency arbitrage, and adverse selection. Self-contained; assumes only the prerequisites of document 200.

---

## Table of Contents

1. [Introduction — What Microstructure Is and Is Not](#introduction)
2. [The Anatomy of a Modern Order Book](#part-i-order-book-anatomy)
3. [Order Types — A Working Catalogue](#order-types)
4. [Matching Engines and Priority Rules](#matching-engines)
5. [Market Fragmentation, Reg NMS, and the National Best Bid and Offer](#fragmentation)
6. [Foundational Models — The Kyle (1985) Setup](#part-ii-foundational-models)
7. [Glosten–Milgrom (1985) and the Bid–Ask Spread](#glosten-milgrom)
8. [Easley–O'Hara PIN](#easley-ohara-pin)
9. [Roll's (1984) Model and the Bid–Ask Bounce](#roll)
10. [Hasbrouck Vector Autoregression and Information Shares](#hasbrouck)
11. [Order Flow Toxicity — VPIN and Bulk Volume Classification](#part-iii-toxicity)
12. [Adverse Selection in Practice](#adverse-selection)
13. [Iceberg Order Detection](#iceberg-detection)
14. [Spoofing and Layering — Detection and Defenses](#spoofing)
15. [Market Impact Models](#part-iv-market-impact)
16. [Square-Root Impact and Empirical Calibration](#square-root-impact)
17. [Propagator Models — Bouchaud, Gatheral](#propagator)
18. [Almgren–Chriss Optimal Execution](#part-v-optimal-execution)
19. [Bertsimas–Lo and Stochastic Control](#bertsimas-lo)
20. [Obizhaeva–Wang LOB Resilience](#obizhaeva-wang)
21. [Implementation Shortfall and Pre-Trade Analytics](#implementation-shortfall)
22. [Smart Order Routing and Dark Pool Pegging](#smart-order-routing)
23. [Avellaneda–Stoikov Market Making](#part-vi-market-making)
24. [Ho–Stoll, Cartea–Jaimungal, and Beyond](#ho-stoll)
25. [Inventory and Adverse-Selection Management](#inventory-management)
26. [HFT Strategies — A Taxonomy](#part-vii-hft)
27. [Latency Arbitrage](#latency-arb)
28. [Microstructure Noise and Realized Volatility](#part-viii-noise)
29. [Realized Kernels, Two-Scales, and Bipower Variation](#realized-kernels)
30. [Empirical Stylized Facts](#part-ix-stylized-facts)
31. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction — What Microstructure Is and Is Not

Market microstructure is the study of *how* trades happen, not *what* prices clear. A standard equilibrium asset-pricing course will tell you that in a frictionless, complete market with rational expectations, the price of an asset equals the discounted expected value of its cash flows. Microstructure starts from the reverse end: real markets are not frictionless, are not complete, and the participants are not all rational. Trades happen sequentially. Information arrives unevenly. Orders queue. Counterparties have asymmetric information. The "price" is not a single number but a collection of bids, offers, depths, hidden orders, and last-trade prints, each of which means something different to a different participant.

Two questions drive the entire field:

1. **How is the price formed?** Given that information is asymmetric and orders arrive sequentially, how does the limit-order book reveal the underlying fundamental? Why is there a bid–ask spread? Why does the spread widen and contract? How fast does new information get incorporated into the price?

2. **How do you trade optimally?** Given the price-formation process, how should a participant — informed trader, uninformed trader, market maker, broker, hedger — split orders, choose order types, time submissions, and respond to the actions of others?

The answers to these questions are the proximate cause of more dollars made and lost in markets than the answers to the asset-pricing questions. A correct alpha signal that is implemented poorly through naïve market orders can underperform a worse signal implemented carefully through liquidity-sensitive routing. Conversely, the value of every alpha signal is bounded above by the implementation cost it incurs in finite size.

This document covers both the *theoretical* lens — the canonical asymmetric-information models and their predictions — and the *practical* lens — empirical regularities, real order-book mechanics, and the algorithms used by working desks. The two halves are complementary: theory tells you what to expect; practice tells you what to do when reality departs from the model.

We will not give a history of the field, but a brief mental map helps. The pre-1985 literature was dominated by inventory models (Stoll 1978, Ho–Stoll 1981, Amihud–Mendelson 1980): the spread compensates the market maker for the cost of carrying inventory. Kyle (1985) and Glosten–Milgrom (1985) introduced the second pillar — the spread as compensation for adverse selection by informed traders. Modern microstructure synthesizes both, adding strategic order placement, multiple-venue dynamics, and high-frequency competition. By the late 2000s, the field was about *speed*: how fast information propagates and how fast strategies can react. By the late 2010s, machine learning was reading the order book directly. By the mid-2020s, hybrid models combine all three.

A final introductory note. Microstructure is *measurable* in a way that asset pricing is not. Every order, every cancellation, every trade, every quote update is timestamped and recorded. Modern exchanges deliver nanosecond-precision data. The empirical evidence base is enormous. This is a blessing — hypotheses can be tested cleanly — and a curse — overfitting opportunities are abundant. Document 211 (Backtesting Statistical Rigor) covers the statistical hygiene needed to avoid spurious findings.

---

## Part I — The Anatomy of a Modern Order Book

A **limit order book** (LOB) is a list of unfilled buy and sell orders for a given instrument. Each order has a price, a size (quantity), and a side (buy or sell). The collection of buy orders, sorted by price descending and time of submission ascending, is the **bid side**. The collection of sell orders, sorted by price ascending and time ascending, is the **ask side** (or offer side).

The highest bid price is the **best bid**. The lowest ask is the **best ask**. The difference is the **bid–ask spread**. The mid-price is (best bid + best ask)/2. The micro-price weights the mid by the imbalance between bid and ask quantities at the top of book.

```
Example LOB snapshot for hypothetical stock XYZ:

Asks (sell orders, sorted ascending):
    Price    Size
    100.06   400
    100.05   1,200
    100.04   800
    100.03   2,500   ← best ask
    
Bids (buy orders, sorted descending):
    100.02   1,800   ← best bid
    100.01   1,000
    100.00   3,000
     99.99   500

Spread = 100.03 - 100.02 = $0.01
Mid    = 100.025
Micro-price = (100.03 × 1800 + 100.02 × 2500) / (1800 + 2500) = 100.0242
```

The key properties of an LOB are:

- **Depth**: total quantity available at each price level. The cumulative depth function tells you how much you can trade at each cost increment.
- **Granularity**: the minimum price increment (tick size). Smaller ticks → more competition for queue priority but smaller per-step price moves.
- **Persistence**: how long unfilled orders sit in the book. Cancellation rates in modern HFT-dominated markets exceed 90%, sometimes 99%.
- **Depth profile**: the shape of cumulative depth as a function of price distance from mid. Often resembles a power law in size.

### Why LOBs Look the Way They Look

Three forces shape the empirical LOB:

1. **Price discovery**: arriving information (orders, news) needs to be incorporated. The spread is the cost of immediacy.
2. **Adverse selection**: market makers fear trading with informed counterparties. They widen quotes when they suspect informed flow is present.
3. **Inventory management**: market makers want to keep their inventory near zero. They skew quotes to encourage offsetting trades when they accumulate position.

These three forces give rise to the canonical regularities: spreads inversely proportional to volume, depth concentrating near top of book during quiet periods and spreading during news, queue position dynamics during slow periods.

### Time Priority, Price Priority, and Their Variants

The standard LOB matching rule is **price–time priority**: orders are matched first by price (better price wins), then by time of submission at the same price (first-in-first-out within a price level). This is the rule on most major equity exchanges.

Variants:
- **Price–size–time priority**: large orders get priority over small at the same price (used in some futures markets).
- **Pro-rata matching**: orders at the matched price share the executed quantity proportionally to their sizes (Eurex options, some emerging markets).
- **Allocation algorithms**: complex hybrids that combine price, time, size, and broker priority (some derivative venues).

### Hidden and Reserved Orders

A **hidden order** is invisible in the public order book. When a marketable order arrives, it can match against hidden orders at price levels not displayed. Variants:

- **Iceberg (display reserve)**: a small displayed quantity plus a much larger reserve. As the displayed portion is filled, the reserve replenishes the displayed amount.
- **Pure hidden**: completely undisplayed. Has lower priority than displayed orders at the same price.
- **Mid-point peg**: a hidden order priced at the midpoint of the NBBO, automatically updating as the NBBO moves.
- **Discretionary peg**: a displayed order at one price with discretion to trade up to a more aggressive price for marketable counterparties.

Hidden orders are essential for institutional flow because they reduce information leakage. Document 77 covers iceberg detection — the inverse problem of inferring hidden depth from the time series of trades and quote updates.

### Auction Mechanics

Trading sessions usually open and close with **auctions** rather than continuous matching. Orders accumulate during a pre-auction phase, and a single clearing price is determined to maximize traded volume subject to constraints. Auction price formation involves:

1. **Indicative price discovery**: as orders accumulate, the would-be clearing price is published.
2. **Auction quote**: the imbalance between buys and sells at the indicative price.
3. **Imbalance announcements**: large remaining unmatched volume is broadcast to attract offsetting orders.
4. **Random closing time**: many exchanges randomize the auction close (within a few seconds) to prevent last-microsecond gaming.

Auctions are preferred for opens and closes because they consolidate liquidity, reducing overnight price discovery uncertainty. The closing auction is often the largest single trading event of the day, accounting for 5–25% of daily volume in major markets.

### Continuous vs Periodic Trading

Most equity markets run continuously throughout the trading day. Some markets and instruments (forex spot, certain emerging markets, illiquid bonds) run *periodic* auctions throughout the day — a clearing price is determined at fixed intervals, e.g., every 1 second or every 30 seconds. Periodic auctions reduce the value of latency advantages because all orders submitted during the interval are equally privileged.

Frequent batch auctions (Budish–Cramton–Shim 2015) propose 100ms auction intervals as a remedy to latency arbitrage. Several venues (Cboe BIDS, IEX) implement variants. The economic case is strong; adoption is slowed by network effects and revenue models tied to continuous trading.

### Reality Check — The Order Book Is Not All There Is

The visible LOB is only one part of total liquidity. Significant flow happens in:

- **Dark pools**: alternative trading systems where orders match without displaying quotes.
- **Internalizer flows**: broker-dealer SDPs (single-dealer platforms) and retail wholesalers that match retail flow internally.
- **Block trades**: large institutional crosses negotiated bilaterally and reported with delays.
- **OTC derivatives**: bilateral negotiations with quotes from a small set of dealers.
- **Negotiated upstairs trades**: pre-arranged deals printed to the consolidated tape but never going through the displayed book.

For US equities, roughly 35–50% of trading volume is off-exchange (dark pools + internalizers + OTC). Models that consider only the lit book miss the bulk of the action and systematically underestimate true liquidity.

---

## Order Types — A Working Catalogue

| Order type | Behavior | When to use |
|---|---|---|
| Market | Buy/sell at any available price | When immediacy beats price; small orders; emergencies |
| Limit | Buy/sell at specified price or better | When price is more important than fill |
| Marketable limit | Limit set aggressively to cross the spread | Standard "execute now" with price protection |
| Stop | Becomes market when triggered | Risk management; rarely an alpha tool |
| Stop-limit | Becomes limit when triggered | Avoids slippage on stops in fast markets |
| Iceberg | Limit with hidden reserve | Reduces information leakage |
| Hidden | Fully invisible limit | Institutional flow; lower priority than displayed |
| Mid-peg | Auto-prices at NBBO mid | Dark trading at fair fill |
| Primary peg | Tracks best bid (for buys) or best ask (for sells) | Always at front of own queue |
| Market peg | Tracks NBBO mid or other benchmark | Dynamic positioning |
| Trailing stop | Stop that moves with favorable price | Trend-following exits |
| TWAP | Spreads execution evenly over time | When time is the right benchmark |
| VWAP | Spreads to match historical volume profile | Benchmark execution; institutional standard |
| POV (participation) | Trades at fixed % of market volume | Reduces market impact in volume-driven markets |
| IS (implementation shortfall) | Front-loads execution to minimize total cost | Risk-averse; standard for alpha trading |
| OCO (one-cancels-other) | Two orders, one cancels the other on fill | Standard exit setup |
| Bracket | OCO wrapping a take-profit and stop | Common retail and small-prop pattern |
| GTC (good-till-cancelled) | Stays open across days | For long-duration limits |
| GTD (good-till-date) | Expires on date | For event-tied positions |
| IOC (immediate-or-cancel) | Fills what it can immediately, cancels rest | Probing liquidity |
| FOK (fill-or-kill) | Fills entirely or cancels | All-or-nothing; rarely advantageous |
| AON (all-or-none) | Fills entirely or stays in book | For precise position sizing |

The choice of order type is a strategic decision. A market order surrenders all price control to gain immediacy. A limit order at the bid surrenders some immediacy to avoid paying the spread. Market makers use a combination of mid-pegs, primary pegs, and aggressive limits to manage queue position and adverse selection.

### Algorithmic Execution Suites

Modern brokers offer hundreds of algorithmic order types built from the primitives above. The taxonomy:

- **Schedule-following**: TWAP, VWAP, POV, scheduled-close. Trade at a benchmark rate without regard to alpha decay.
- **Implementation-shortfall**: front-load execution to minimize the gap between decision price and execution price under uncertainty about future market moves. Solved analytically by Almgren–Chriss; production variants add risk aversion, signal forecasts, and venue selection.
- **Liquidity-seeking**: aggressively post in dark pools and capture liquidity opportunistically when offsetting flow appears. Variants: Dark Pool Sweep, Liquidity-Seeking, IS-Liquidity-Seeking.
- **Pegging**: stay at NBBO mid, primary, or some derived benchmark. Mid-peg captures spread improvement without paying.
- **Stealth/anti-detection**: minimize information leakage by randomizing slice sizes, timing, and venue selection. The arms race against HFT detection is real and ongoing.

### Reality Check — The Right Algo for the Job

Choosing the right algorithm depends on:

- **Alpha decay rate**: fast-decaying alpha demands aggressive front-loading; slow-decaying alpha allows patient liquidity-seeking.
- **Order size relative to ADV**: orders > 5% of ADV require slow execution to avoid impact.
- **Volatility**: high-volatility periods favor immediacy (faster execution to lock in price); low-volatility favors patience.
- **Cost of capital**: high cost of capital → faster execution to free up margin.
- **Risk tolerance**: risk-averse traders use IS-style algos; risk-neutral use VWAP/TWAP.

Production execution desks measure their algos by *post-trade analytics*: actual implementation shortfall vs benchmark, adverse selection rate (% of fills at prices that move against you in the next minute), reversion (post-fill price reversion if any). These metrics are tracked in real-time and feed back into algo selection.

---

## Matching Engines and Priority Rules

The matching engine is the software that pairs orders and creates trades. Modern engines process millions of order updates per second with sub-microsecond latency. Key design choices:

- **Single-threaded vs multi-threaded**: most major engines are single-threaded for determinism, with separate cores for I/O.
- **In-memory vs persistent**: order books live in RAM for speed; persistence is via append-only logs replicated to multiple nodes.
- **Order book representation**: typically arrays of price levels with linked lists of orders within each level. Variants: trees, skip lists.
- **Cancellation handling**: cancellations must be O(1); typically achieved by indexing orders by ID as well as by price level.

### Matching Algorithms

The standard FIFO (price–time priority) matching algorithm:

```python
def match_market_buy(book, quantity):
    """Match a market buy order against the book's ask side."""
    fills = []
    while quantity > 0 and book.asks:
        best_price = min(book.asks.keys())
        level = book.asks[best_price]
        for order in list(level):
            if quantity == 0:
                break
            fill_qty = min(order.size, quantity)
            fills.append((best_price, fill_qty, order.id))
            order.size -= fill_qty
            quantity -= fill_qty
            if order.size == 0:
                level.remove(order)
        if not level:
            del book.asks[best_price]
    return fills
```

Pro-rata matching:

```python
def match_pro_rata(level, quantity):
    """Distribute quantity proportionally to order sizes at a level."""
    total = sum(o.size for o in level)
    fills = []
    if quantity >= total:
        for o in level:
            fills.append((o.id, o.size))
        return fills, total
    for o in level:
        share = int(quantity * o.size / total)  # truncation; remainder handled separately
        fills.append((o.id, share))
    # Distribute remainder by size descending (one tick at a time)
    distributed = sum(f[1] for f in fills)
    remainder = quantity - distributed
    for i, o in enumerate(sorted(level, key=lambda x: -x.size)):
        if remainder <= 0:
            break
        fills[i] = (fills[i][0], fills[i][1] + 1)
        remainder -= 1
    return fills, quantity
```

### Time-in-Force Semantics

- **Day**: order is active until end of trading day, then cancelled.
- **GTC**: stays active across days (some markets re-confirm daily).
- **IOC**: any portion not immediately fillable is cancelled.
- **FOK**: order is cancelled if it cannot be filled in entirety immediately.
- **GTX**: good-till-extended-hours, allowing pre/post-market execution.

The time-in-force interacts with the matching engine's behavior in subtle ways. An IOC order does not rest in the book — it must execute or cancel immediately. A FOK on an iceberg may not fill even if total visible+hidden depth is sufficient, because the engine sees the order book in stages.

### Order Modification

Most engines allow partial modifications: a price change resets time priority (the order is effectively cancel-and-replace). A size *increase* also typically resets priority. A size *decrease* preserves priority. This asymmetry is exploited by HFT firms to maintain queue position while reducing risk.

Some venues offer "cancel/replace" optimizations: an atomic operation that cancels an existing order and replaces it with a new one, maintaining queue priority if the new price is the same as the old. This is valuable for market makers updating size without losing position.

### Reality Check — Microsecond Determinism

Modern matching engines target sub-10-microsecond round trips. Achieving this requires:
- Kernel-bypass networking (DPDK, OpenOnload, RoCE).
- Processor affinity and isolation (no OS scheduling jitter on hot cores).
- Hardware timestamping (PHC, PTP) for precise ordering.
- FPGA acceleration for parsing market data and gating outgoing orders.
- Co-location: physical proximity to the matching engine reduces RTT to a few microseconds.

The arms race for speed is asymptotic: shaving 100 nanoseconds from your stack costs millions in engineering. The economic returns to such investments depend on whether you have a strategy whose alpha is cleanly paid for by being first. For pure latency arbitrage strategies, yes; for fundamental or factor strategies, no.

Document 210 (HFT Architecture and Latency Engineering) covers the engineering stack in detail.

---

## Market Fragmentation, Reg NMS, and the National Best Bid and Offer

US equity markets are fragmented across more than a dozen exchanges and dozens of dark pools. The resulting **National Best Bid and Offer** (NBBO) is the consolidation of the best displayed prices across all lit exchanges.

Reg NMS (2007) imposed three constraints that shaped the modern market:
- **Order Protection Rule**: no exchange may execute a trade at a price worse than the NBBO. Trades must be routed to or matched against the venue with the best displayed price.
- **Access Rule**: standardized order routing fees and protections for non-direct access participants.
- **Sub-Penny Rule**: no displayed quote allowed at increments smaller than $0.01 (with exceptions for sub-dollar stocks).

The Order Protection Rule created the routing infrastructure: every venue maintains a routing engine that diverts orders to the venue with the best price. This is implemented via the consolidated **Securities Information Processor** (SIP), which broadcasts NBBO updates, and via direct feeds from each exchange (faster but more expensive).

### The SIP vs Direct Feed Race

The SIP collects quotes from all exchanges, computes the NBBO, and broadcasts it. SIP latency is a few hundred microseconds to single-digit milliseconds. Direct feeds from individual exchanges (CTS, UTP, Nasdaq TotalView, NYSE OpenBook) are 10–100× faster.

This creates a *latency arbitrage* opportunity. An HFT firm with direct feeds sees an exchange's price move before the SIP reflects it. They can trade against quotes on slower venues that have not yet updated. The arms race for direct-feed speed has been blamed for the disparity between fast (HFT) and slow (institutional) participants.

Mitigations:
- IEX's 350-microsecond speed bump: a deliberate latency floor that neutralizes some HFT advantages.
- Frequent batch auctions (Budish–Cramton–Shim 2015): periodic discrete auctions instead of continuous matching.
- Direct-feed cost equalization (proposed but not enacted).

### Other Fragmentation Issues

- **Trade-through**: a trade that occurs at a price worse than the NBBO. Reg NMS prohibits this; violations are tracked and result in regulatory penalties.
- **Quote-stuffing**: excessive order/cancellation messaging intended to slow down competitors. Largely defended-against now via message-rate throttles.
- **Front-running on direct feeds**: trading ahead of slower participants who see a stale NBBO. Legally gray; often technically arbitrage rather than misconduct.

### European and Asian Market Structure

European markets (after MiFID II) similarly require best execution across venues. Order protection is implemented via the dealer's best-execution obligation rather than a central rule. The European Best Bid and Offer (EBBO) is computed and used analogously to the US NBBO.

Asian markets vary widely. Hong Kong, Singapore, and Tokyo are dominantly single-venue (the primary exchange dominates lit trading). India has competition between NSE and BSE but with strong NSE dominance. Australia (ASX vs Chi-X) parallels US fragmentation in microcosm.

### Reality Check — Fragmentation and Liquidity

Fragmentation has trade-offs:
- **Pros**: competition drives down trading fees, encourages innovation, reduces dependence on any single point of failure.
- **Cons**: harder to find counterparties; latency arbitrage opportunities; harder for institutional flow to remain hidden; complexity of best-execution compliance.

For retail traders, fragmentation is largely invisible — internalizers (Citadel, Virtu, etc.) handle ~70% of retail equity flow at zero or negative explicit fees. For institutions, fragmentation is the central challenge: every large execution problem is a routing problem.

---

## Part II — Foundational Models: The Kyle (1985) Setup

We turn to the canonical theoretical models. They give us the mental machinery to reason about prices, spreads, and order flow when participants are strategically heterogeneous. We start with Kyle's (1985) model — the cleanest and most influential single model in the field.

### Setup

Consider a single trading period [0, T]. There is a single risky asset whose terminal value v is normally distributed: v ∼ 𝒩(p_0, Σ_0). At t = 0 the asset's value is p_0; the variance Σ_0 measures the uncertainty.

Three participants:
1. **Insider (informed trader)**: knows v exactly. Submits a quantity x to maximize expected profit.
2. **Noise traders**: submit a random total quantity u ∼ 𝒩(0, σ_u²), independent of v.
3. **Market maker (MM)**: observes only the total order flow Y = x + u, sets a price p, and absorbs the entire flow at p.

The MM is competitive (zero expected profit) and risk-neutral. They set the price as the conditional expectation of v given Y:

$$
p = \mathbb{E}[v \mid Y].
$$

The insider chooses x to maximize 𝔼[x(v − p) | v]. The market is in equilibrium when x and p are consistent.

### Equilibrium

Conjecture a linear strategy x = β(v − p_0) for some β > 0, and a linear pricing rule p = p_0 + λ Y for some λ > 0. We need to find β, λ such that they are mutually best responses.

Given the strategies, Y = β(v − p_0) + u. Then

$$
\mathbb{E}[v \mid Y] = p_0 + \frac{\text{Cov}(v, Y)}{\text{Var}(Y)} (Y - \mathbb{E}[Y]) = p_0 + \frac{\beta \Sigma_0}{\beta^2 \Sigma_0 + \sigma_u^2} Y.
$$

Match this to p_0 + λ Y to get λ = β Σ_0 / (β² Σ_0 + σ_u²).

Now optimize the insider's expected profit:

$$
\mathbb{E}[x(v - p) \mid v] = \mathbb{E}[x(v - p_0 - \lambda(x + u)) \mid v] = x(v - p_0) - \lambda x^2.
$$

The first-order condition gives x = (v − p_0)/(2λ). Comparing to the conjectured x = β(v − p_0): β = 1/(2λ).

Substituting β = 1/(2λ) into the price-impact equation:

$$
\lambda = \frac{(1/(2\lambda)) \Sigma_0}{(1/(2\lambda))^2 \Sigma_0 + \sigma_u^2}.
$$

Solving: λ² = Σ_0 / (4 σ_u²), so

$$
\boxed{\lambda = \tfrac{1}{2} \sqrt{\Sigma_0 / \sigma_u^2}}, \qquad \beta = \sqrt{\sigma_u^2 / \Sigma_0}.
$$

### Interpretation

- **λ is the market depth's reciprocal**. λ Y is the price impact of an order of size Y. Bigger λ means smaller orders move the price more — i.e., shallower depth.
- **λ scales with informational uncertainty (√Σ_0) and inversely with noise volume (σ_u)**. More uncertainty about value → larger price impact per unit order. More noise trading → smaller impact (the MM can disguise informed flow within noise).
- **β is the insider's intensity of trading**. The insider trades more aggressively when noise is abundant (their flow can hide) and less when uncertainty is high (because λ is high).

Plug back to find the insider's expected profit:

$$
\Pi^* = \mathbb{E}[x(v - p) \mid v] = \frac{(v - p_0)^2}{4\lambda} = \frac{1}{2} (v - p_0)^2 \sqrt{\sigma_u^2 / \Sigma_0}.
$$

Unconditionally, 𝔼[Π*] = (Σ_0/2) · √(σ_u²/Σ_0) = ½ √(σ_u² Σ_0). The insider's expected profit is the geometric mean of noise volume and informational uncertainty.

### Multi-Period Kyle

The single-period model extends to N periods. The result: the insider trades a constant fraction of their remaining information advantage per period, λ is constant, and price gradually incorporates the insider's information. In the continuous-time limit (N → ∞), the price process is Brownian-like and the insider's trading is smoothed across the entire period. This continuous-time version is the basis of Kyle's (1985) full result and of Back's (1992) generalization to non-Gaussian and exotic distributions.

### Implications

- **Price discovery is slow**: even though the insider knows v, the MM cannot infer it perfectly from one round of trading. Information leaks gradually.
- **Liquidity (1/λ) is endogenous**: more noise → more liquidity. Noise traders are good for everyone (except themselves).
- **Spread is implicit**: there is no explicit bid–ask spread in Kyle. The spread arises in extensions where the MM holds inventory or competes with other market makers.
- **Adverse selection cost**: the MM systematically loses to the insider. They recoup these losses from noise traders (who pay the price impact without information advantage).

```python
# Simulate a Kyle equilibrium and verify the analytical results.
import numpy as np
np.random.seed(42)

p0, Sigma0, sigma_u = 100.0, 1.0, 5.0
lam_theory = 0.5 * np.sqrt(Sigma0 / sigma_u**2)
beta_theory = np.sqrt(sigma_u**2 / Sigma0)
print(f"lambda = {lam_theory:.4f}, beta = {beta_theory:.4f}")

n_trials = 100_000
v = np.random.normal(p0, np.sqrt(Sigma0), n_trials)
u = np.random.normal(0, sigma_u, n_trials)
x = beta_theory * (v - p0)
Y = x + u
p = p0 + lam_theory * Y
profit = x * (v - p)
print(f"Mean insider profit: {profit.mean():.4f}, theory: {0.5*np.sqrt(sigma_u**2*Sigma0):.4f}")
```

### Reality Check — Kyle in Practice

Kyle is a stylized model. Real markets have:
- **Many informed traders, not one**. Multi-insider Kyle (Foster–Viswanathan 1996) shows that informed competition speeds up price discovery and reduces λ.
- **Imperfect noise traders**. Real "noise" includes algorithmic gamblers whose flow is auto-correlated, hedgers whose trades are correlated with realized price moves, and HFT firms whose flow contains real signal.
- **Time-varying λ**. In real data, λ varies with volatility, time of day, and macro state. Calibration is often via the regression-coefficient approach of Hasbrouck (1991).
- **Multiple lots, not single batched orders**. Real trades are split into many small orders; each contributes a fraction of total impact.

Despite the stylization, Kyle gives the cleanest mental model of how informed flow drives price impact, and λ is the workhorse parameter for impact estimation.

---

## Glosten–Milgrom (1985) and the Bid–Ask Spread

Where Kyle has a single MM clearing all flow at one price, Glosten–Milgrom (GM) has the MM quote distinct bid and ask prices and let traders self-select. The result is the canonical model of bid–ask spread as compensation for adverse selection.

### Setup

Sequential trading: at each time t = 1, 2, …, a single trader arrives and submits one unit-buy or unit-sell order. The trader is either:
- **Informed** (with probability α): knows the true value v ∈ {V_H, V_L} (binary). Buys if v = V_H, sells if v = V_L.
- **Uninformed** (with probability 1 − α): buys or sells with equal probability ½, independent of v.

The MM observes the order direction (buy or sell) but not the trader's type. They post a bid B and ask A and execute against the trader at the appropriate side. Competition drives B and A to the *conditional expected value of v given the order*.

### Equilibrium Spread

By Bayes' rule:
$$
A = \mathbb{E}[v \mid \text{buy}] = V_H \mathbb{P}(v = V_H \mid \text{buy}) + V_L \mathbb{P}(v = V_L \mid \text{buy}),
$$
$$
B = \mathbb{E}[v \mid \text{sell}].
$$

Let π = ℙ(v = V_H) be the prior. Then:

$$
\mathbb{P}(\text{buy} \mid v = V_H) = \alpha + (1-\alpha)/2,
$$
$$
\mathbb{P}(\text{buy} \mid v = V_L) = (1-\alpha)/2,
$$
$$
\mathbb{P}(\text{buy}) = \pi(\alpha + (1-\alpha)/2) + (1-\pi)(1-\alpha)/2.
$$

By Bayes:
$$
\mathbb{P}(v = V_H \mid \text{buy}) = \frac{\pi(\alpha + (1-\alpha)/2)}{\mathbb{P}(\text{buy})}.
$$

Plug in V_H, V_L to get A. Symmetrically for B. The spread A − B is the expected loss from trading against an informed counterparty:

$$
A - B = 2 \alpha (V_H - V_L) \frac{\pi(1-\pi)}{\mathbb{P}(\text{buy}) \mathbb{P}(\text{sell})} \cdot (1-\alpha)/2.
$$

For π = ½:

$$
A - B = \frac{\alpha (V_H - V_L)}{1} \cdot \text{(simplified)}.
$$

The exact formula varies but the qualitative result is robust: the spread is increasing in α (information asymmetry) and in V_H − V_L (uncertainty). When α = 0, all traders are uninformed and the spread is zero.

### Bayesian Updating

After observing each order, the MM updates π using Bayes' rule. The price process — the sequence of mid-prices — is a martingale: 𝔼[A | history] = 𝔼[B | history] = current expected v. Over time, repeated orders push π closer to 0 or 1 depending on the buy/sell imbalance, and the spread A − B narrows because the MM becomes more confident about v.

### Convergence to True Value

In the limit of many trades, the MM's posterior converges to the truth (almost surely if not certain). The price process P_t = 𝔼[v | history at t] is a martingale that converges to v. The speed of convergence depends on α: more informed flow → faster price discovery.

```python
# Simulate Glosten-Milgrom price discovery dynamics.
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)
v_H, v_L = 102, 98
alpha = 0.3
v_true = v_H  # private info

n = 200
pi = 0.5  # prior
prices_a, prices_b, prices_mid = [], [], []
for t in range(n):
    p_buy_h = alpha + (1-alpha)/2
    p_buy_l = (1-alpha)/2
    p_buy = pi * p_buy_h + (1-pi) * p_buy_l
    p_sell = 1 - p_buy
    A = v_H * pi*p_buy_h/p_buy + v_L * (1-pi)*p_buy_l/p_buy
    B = v_H * pi*(1-p_buy_h)/p_sell + v_L * (1-pi)*(1-p_buy_l)/p_sell
    prices_a.append(A); prices_b.append(B); prices_mid.append((A+B)/2)
    
    # Trader arrives
    is_informed = np.random.rand() < alpha
    if is_informed:
        order = 'buy' if v_true == v_H else 'sell'
    else:
        order = 'buy' if np.random.rand() < 0.5 else 'sell'
    
    # Update pi
    if order == 'buy':
        pi = pi * p_buy_h / p_buy
    else:
        pi = pi * (1-p_buy_h) / p_sell

plt.figure(figsize=(10, 4))
plt.plot(prices_a, 'r-', label='Ask', alpha=0.7)
plt.plot(prices_b, 'b-', label='Bid', alpha=0.7)
plt.plot(prices_mid, 'k--', label='Mid')
plt.axhline(v_true, color='g', linestyle=':', label='True value')
plt.title('Glosten–Milgrom price discovery (informed = 30%)')
plt.legend(); plt.grid(True); plt.tight_layout()
plt.savefig('gm_dynamics.png', dpi=120)
```

### Implications

- **Spread = adverse selection cost**: the spread compensates the MM for systematic losses to informed flow.
- **Spread responds to information arrival**: when α increases (e.g., before earnings), spreads widen.
- **Order flow is informative**: every order moves the price even if there are no trades. This is the foundation of order-flow based prediction.
- **Volume drives information**: higher α → higher spread → fewer uninformed trades, but each trade carries more information.

### Variants and Extensions

- **GM with multiple shares**: the trader can submit any quantity, paying a quantity-dependent price. The result generalizes: bigger orders pay larger spreads, which is consistent with empirical "depth schedules."
- **GM with hidden orders**: the MM cannot observe the trader's true intent (e.g., order types), only the executed flow. Adverse selection is amplified.
- **Roll's bid–ask bounce**: in the simplest GM, the MM's quote alternates between A and B as buys and sells arrive. The squared first difference of trade prices equals the squared half-spread plus information variance. Roll (1984) used this to estimate the effective spread from trade prices alone — useful when quote data is unavailable.

---

## Easley–O'Hara PIN (Probability of Informed Trading)

Easley, Kiefer, and O'Hara (1996) and Easley, Kiefer, O'Hara, Paperman (1996) developed an estimable variant of GM. The model:

- On each day, with probability α, an information event occurs.
- Conditional on an event, the news is "good" with probability δ.
- Informed traders arrive at rate µ if there is good news (only buyers) or rate µ if there is bad news (only sellers).
- Uninformed buyers arrive at rate ε_B; uninformed sellers at rate ε_S, regardless of events.

So daily buy and sell counts (B, S) follow Poisson distributions with rates depending on the event status. The probability of informed trading is

$$
\text{PIN} = \frac{\alpha \mu}{\alpha \mu + \varepsilon_B + \varepsilon_S}.
$$

Estimation: maximum likelihood from time series of (B_t, S_t). Identification works because no-news days have low total volume and balanced buy/sell, while bad-news days have high sell flow with low buy flow, etc.

PIN has been applied to:
- Cross-sectional asset pricing (Easley, Hvidkjaer, O'Hara 2002): high-PIN stocks earn higher returns.
- Earnings announcement studies: PIN spikes around earnings.
- Liquidity supply/demand modeling.

Critics: PIN's assumption of strict event timing is unrealistic; the model's identifying restrictions are strong; and several modifications (Duarte–Young 2009 PIN-D, adjusted-PIN) attempt to fix observed pathologies.

```python
# Simulate Easley-O'Hara data and estimate PIN by maximum likelihood.
import numpy as np
from scipy.optimize import minimize

np.random.seed(2024)
alpha, delta, mu, eps_b, eps_s = 0.3, 0.5, 100, 50, 50
n_days = 252

events = np.random.rand(n_days) < alpha
good_news = np.random.rand(n_days) < delta
B = np.random.poisson(eps_b + np.where(events & good_news, mu, 0))
S = np.random.poisson(eps_s + np.where(events & ~good_news, mu, 0))

def neg_log_lik(theta, B, S):
    a, d, m, e_b, e_s = theta
    if min(a, d, m, e_b, e_s) <= 0 or a >= 1 or d >= 1:
        return 1e10
    log_lik = 0
    for b, s in zip(B, S):
        # P(B=b, S=s) = sum over event states
        p_no_event = (1-a) * np.exp(-e_b)*e_b**b/np.math.factorial(min(b, 50)) * np.exp(-e_s)*e_s**s/np.math.factorial(min(s, 50))
        p_good = a*d * np.exp(-(e_b+m))*(e_b+m)**b/np.math.factorial(min(b, 50)) * np.exp(-e_s)*e_s**s/np.math.factorial(min(s, 50))
        p_bad = a*(1-d) * np.exp(-e_b)*e_b**b/np.math.factorial(min(b, 50)) * np.exp(-(e_s+m))*(e_s+m)**s/np.math.factorial(min(s, 50))
        log_lik += np.log(max(p_no_event + p_good + p_bad, 1e-300))
    return -log_lik

# Note: factorial overflow at high counts; use scipy.stats.poisson.logpmf in production.
# This is illustrative only.
```

The production-grade EHO MLE uses logpmf to avoid overflow, multiple starting points, and bounded optimization.

### Reality Check — PIN as a Cross-Sectional Sort

PIN's most credible empirical use is *relative* (sorting stocks high-PIN vs low-PIN), not absolute. Absolute PIN values (e.g., "this stock has 30% informed trading") have wide confidence intervals and are sensitive to the model specification. Relative PIN — say, top vs bottom decile — is more robust and is the form most studies use. Even so, replicability of PIN cross-sectional results varies; some early findings (e.g., the PIN-return relation) have weakened in more recent samples.

---

## Roll's (1984) Model and the Bid–Ask Bounce

Roll's model is the simplest GM variant and a workhorse for empirical spread estimation when quote data is unavailable.

Assume the true mid-price is a martingale: m_t = m_{t-1} + ε_t with iid ε_t. The MM posts bid m_t − s/2 and ask m_t + s/2. Each trade randomly executes at the bid (with probability ½) or ask (with probability ½), so the trade price is

$$
P_t = m_t + (s/2) q_t,
$$

where q_t ∈ {−1, +1} is the trade-direction indicator (+1 for buy at ask, −1 for sell at bid).

The first difference is

$$
\Delta P_t = \varepsilon_t + (s/2)(q_t - q_{t-1}).
$$

Compute

$$
\text{Cov}(\Delta P_t, \Delta P_{t-1}) = -(s/2)^2,
$$

so the **effective half-spread** is

$$
s/2 = \sqrt{-\text{Cov}(\Delta P_t, \Delta P_{t-1})}.
$$

Roll's estimator: compute the sample first-order autocovariance of trade-price changes; if negative, the implied spread is 2 √(−γ_1). If positive, the implication is that the model is wrong (information has dominated bid–ask bounce).

### Application

Roll's estimator is widely used in academic studies of historical liquidity, especially for periods or markets without high-quality quote data. It is biased downward when there is positive information drift in trade prices (which there often is intraday), so in practice it underestimates true spreads.

### Modern Variants

- **Hasbrouck Gibbs sampler**: a Bayesian extension that simultaneously estimates the spread and a permanent-component state-space model.
- **Corwin–Schultz (2012)**: uses high-low ranges over consecutive periods to estimate spreads, more robust to autocorrelation than Roll.
- **High-frequency: Realized spreads from quote/trade matching**: when nanosecond data is available, direct computation of the effective spread is the gold standard.

---

## Hasbrouck Vector Autoregression and Information Shares

Hasbrouck (1991) combined the GM/Roll insights with vector autoregression (VAR) methodology to decompose price changes into permanent (information-driven) and transitory (microstructure noise) components.

### Setup

Let p_t be the (log) trade price and q_t the (signed) trade indicator. Fit a bivariate VAR:

$$
\Delta p_t = \sum_{i=1}^{P} \alpha_i \Delta p_{t-i} + \sum_{i=0}^{P} \beta_i q_{t-i} + u_t^p,
$$
$$
q_t = \sum_{i=1}^{P} \gamma_i \Delta p_{t-i} + \sum_{i=1}^{P} \delta_i q_{t-i} + u_t^q.
$$

The cumulative impulse response of Δp to a unit shock in q gives the **permanent price impact** of an order: the contribution of the trade to the long-run price level. This is the empirical analog of Kyle's λ.

### Information Share

For multiple-venue securities (a stock listed on multiple exchanges), Hasbrouck's information share decomposes the variance of the common efficient-price process into contributions from each venue. The intuition: if venue A's quotes lead venue B's quotes, A has higher information share. Production trading desks use this to identify which venue to monitor and which to trade.

### Reality Check — VAR Models in Reality

VARs are linear and stationary by assumption. Real markets have:
- Time-varying volatility (need GARCH-style residuals).
- Intraday seasonality (lower spreads at midday, higher at open/close).
- Conditional non-linearity (impact varies with volume, volatility regime).

Production microstructure models combine VAR-like structure with non-linear adjustments and conditioning. The Hasbrouck framework remains the reference benchmark, especially for liquidity comparison across markets and instruments.

---

## Part III — Order Flow Toxicity: VPIN and Bulk Volume Classification

Toxicity = the probability that the next counterparty has more information than you. High-toxicity periods are when market makers most want to step away.

### VPIN (Easley, López de Prado, O'Hara 2012)

VPIN replaces the time-bucketed Easley–O'Hara PIN with **volume-time** bucketing. Each bucket contains a fixed amount of volume (say, 1/50 of average daily volume). Within each bucket, classify trades as buy or sell using **bulk volume classification** (BVC):

$$
V_t^B = V_t \cdot \Phi\!\left(\frac{\Delta P_t}{\sigma_{\Delta P} \cdot \sqrt{V_t / \bar V}}\right),
$$
$$
V_t^S = V_t - V_t^B.
$$

Φ is the standard normal CDF; σ_{ΔP} is the volatility of price changes. Within each bucket, |V^B − V^S|/V is averaged over a rolling window of buckets (typically 50). VPIN is this rolling average:

$$
\text{VPIN}_n = \frac{1}{n} \sum_{i=t-n+1}^{t} \frac{|V_i^B - V_i^S|}{V_i}.
$$

### Why Volume Time?

Calendar time is not the natural clock of markets. Volume arrives unevenly. A 5-minute bar at the open contains 50× more volume than a 5-minute bar at noon. By bucketing in volume time, you sample at intervals where each contains the same "amount of trading effort." This reduces seasonality and makes the toxicity statistic comparable across the day.

### Toxicity and the Flash Crash

Easley, López de Prado, and O'Hara (2011) documented a sharp VPIN spike before the May 6, 2010 Flash Crash. The interpretation: market makers detected toxic flow and withdrew liquidity, leading to the crash. VPIN became the early-warning system for such events.

Caveats: VPIN's predictive value has been debated. Andersen and Bondarenko (2014) argue that VPIN is essentially a measure of price volatility and adds little beyond standard volatility metrics. The empirical case for VPIN as a *lead* indicator (vs concurrent indicator) is contested.

```python
# Compute VPIN on simulated trade-and-price data.
import numpy as np
from scipy.stats import norm
np.random.seed(42)

n_trades = 100_000
prices = 100 + np.cumsum(np.random.normal(0, 0.05, n_trades))
volumes = np.random.lognormal(mean=2, sigma=1, size=n_trades).astype(int) + 1

bucket_size = sum(volumes) // 50
sigma_dP = np.std(np.diff(prices))

# Build buckets
buckets = []
i, V = 0, 0
B, S = 0, 0
delta_p = 0
while i < n_trades - 1:
    V += volumes[i]
    delta_p += prices[i+1] - prices[i]
    if V >= bucket_size:
        z = delta_p / (sigma_dP * np.sqrt(V / np.mean(volumes)))
        VB = V * norm.cdf(z)
        VS = V - VB
        buckets.append(abs(VB - VS) / V)
        V, delta_p = 0, 0
    i += 1

window = 50
vpin = np.array([np.mean(buckets[i:i+window]) for i in range(len(buckets) - window)])
print(f"VPIN range: {vpin.min():.4f} to {vpin.max():.4f}")
```

### Hawkes Processes and Self-Exciting Order Flow

Hawkes processes model order arrivals as point processes whose intensity depends on the history: each event increases the probability of subsequent events for a decaying period. For trades:

$$
\lambda(t) = \mu + \int_0^t \alpha e^{-\beta(t-s)} dN_s.
$$

The branching ratio α/β measures the degree of self-excitation. Empirical estimates for equity markets give α/β ≈ 0.6–0.8, meaning ~70% of order flow is "endogenous" (caused by past order flow rather than fundamental information).

Hawkes models give a richer view of toxicity than VPIN: they distinguish between "exogenous" (low-α/β) and "endogenous" (high-α/β) periods. Endogenous periods correspond to crowded HFT activity and increased risk of toxic flow.

### Reality Check — Toxicity in Live Trading

Production market-making systems run real-time toxicity monitors. Triggers include:
- VPIN above a threshold for the asset class.
- Order flow autocorrelation exceeding a decay benchmark.
- Realized adverse selection rate exceeding the ex-ante estimate.
- Cross-venue queue position deterioration.

When toxicity is high, the standard responses are: widen quotes, reduce displayed size, post less aggressively, prefer mid-peg over join-best, and route more to dark pools. Discipline matters: many MMs lose money in toxic regimes by being slow to widen.

---

## Adverse Selection in Practice

Adverse selection is the empirical phenomenon: market makers systematically lose to better-informed counterparties. The losses are paid for by the spread charged to uninformed flow.

### Measuring Adverse Selection

Two standard metrics:

**Realized half-spread**: the per-trade profit of a market maker who immediately offsets each trade.

$$
\text{RHS}_t = \begin{cases} (P_{t+\tau} - P_t) & \text{if MM bought at $P_t$} \\ (P_t - P_{t+\tau}) & \text{if MM sold at $P_t$} \end{cases}
$$

For a horizon τ (say, 1 minute), aggregate over many trades. The mean RHS minus the (paid) effective spread is the *adverse selection cost*.

**Effective spread**: |P_t − M_t|, where M_t is the mid-price at time t. The market maker pays this spread.

The decomposition:

$$
\text{Effective spread} = \text{Realized spread} + \text{Adverse selection},
$$

where the "realized spread" is the profitable component and "adverse selection" is the loss.

### Adverse Selection Across Strategies

| Strategy | Direction | Adverse Selection? |
|---|---|---|
| Market-making | Mostly resting | High when crossed by informed flow |
| Liquidity-taking | Mostly aggressing | Pays the spread but selects on edge |
| Pairs trading | Both | Moderate; depends on speed of mean reversion |
| HFT signal | Both | Low; explicitly conditions on signal |
| Latency arb | Aggressing | Negative (you take stale quotes) |

Properly executed, an HFT strategy *generates* adverse selection for its counterparties, not pays it. The arms race is to be the one inflicting the adverse selection.

### Defensive Tactics

- **Short-fade**: cancel resting orders quickly when information arrives. The latency of cancellation is critical.
- **Skew quotes**: when accumulating adverse-selecting fills, widen on the affected side to discourage continued flow.
- **Reduce displayed size**: smaller displayed orders attract less informed targeting.
- **Move to dark pools**: hidden orders cannot be targeted by adverse-selection algorithms.
- **Time-of-day filtering**: avoid market-making in periods with predictable information events (open, close, FOMC, earnings).

### Reality Check — Adverse Selection Is Always with You

Even the best market-making algorithm pays some adverse selection. The question is the *ratio* of adverse-selection cost to spread earned. Profitable MM operations target ratios of 0.3–0.5 (i.e., 30–50% of the spread is given back to informed counterparties). Higher ratios indicate the strategy is not edge-positive after costs.

Document 76 (VPIN Order Flow Toxicity) and document 78 (Spoofing Detection) cover the more advanced detection methods.

---

## Iceberg Order Detection

An iceberg is a hidden-reserve limit order. Detecting them — inferring hidden depth from public order flow — is a classic microstructure problem.

### Heuristic Detection

The simplest approach: when a series of small orders trade at the same price level *replenishes* repeatedly without the displayed depth dropping, an iceberg is likely. Specifically:

1. Track the displayed depth at each price level.
2. After each trade at a price, check whether the displayed depth at that price decreased by the trade size (or near it).
3. If displayed depth replenishes within a short time (typically <1 second), there is likely an iceberg.

### Probabilistic Detection

Modern detectors use sequential probability ratio tests (Bouchaud et al. 2009, Aldridge 2013, and others). The likelihood ratio is

$$
\Lambda = \frac{\mathbb{P}(\text{observed flow} \mid \text{iceberg of size } X)}{\mathbb{P}(\text{observed flow} \mid \text{no iceberg})}.
$$

When Λ exceeds a threshold, declare detection. Calibration of the iceberg-size prior is critical.

### Strategic Use

Detected icebergs are *trading signals*. A large buyer (iceberg buy at a price level) signals informed-buying pressure. Some HFT strategies front-run icebergs by placing aggressive orders in front of the detected reserve, profiting from the predictable price impact when the iceberg eventually fills.

This is, depending on jurisdiction, either market-making (legal) or front-running (legal but reputationally costly). The line is whether you are using your own order flow to trigger movement (legal arbitrage) or trading ahead of a customer order (illegal).

### Reality Check — Counterstrategies

Sophisticated institutional traders defend their icebergs by:
- Randomizing displayed slice sizes (e.g., 10% ± 5% of total).
- Posting at multiple venues to dilute detection signals.
- Using "anti-detection" algorithms that mix iceberg with mid-peg, hidden, and cancel-and-replace orders.
- Posting on exchanges with anti-front-running rules (some venues prohibit certain pattern trading).

Document 77 (Iceberg Order Detection) covers the algorithms in detail.

---

## Spoofing and Layering — Detection and Defenses

Spoofing is the placement of orders without intent to execute, in order to induce others to trade favorably. Layering is a refinement: many small spoofs at multiple price levels.

### Mechanics

Spoof example:
1. Place a large bid at $99.99 (no intent to fill).
2. Other participants infer buying pressure, increase their bids.
3. Sell quickly at the elevated bid, e.g., $100.00.
4. Cancel the spoof bid before it fills.

The spoof never executes; the spoofer profits from the induced movement.

### Detection

Statistical detection looks for orders with high cancellation rate and skewed timing:
- High cancellation rate (>95% on certain levels).
- Cancellation occurring within milliseconds of an opposite-side fill at a better price.
- Concentrated activity by a single account or correlated accounts.
- Orders sized to be visible (not too small) but not large enough to risk fills.

Modern detection uses machine learning over order-level features: order ID, lifetime, size, distance from mid, simultaneous activity by the same actor on the opposite side.

### Legal Status

Spoofing is illegal in most major markets (US Dodd–Frank §747, European MiFID II, similar in Japan, Hong Kong, Singapore). Penalties include large fines, trading bans, and imprisonment for individuals.

Notable enforcement actions: Navinder Sarao (US, 2010 Flash Crash, 5 years), Igor Oystacher (CFTC 2015), Michael Coscia (US 2014). The 2020 JP Morgan settlement was $920M for spoofing in metals and Treasuries.

### Defenses

For market makers, the defense is to recognize the pattern and not respond to suspect orders:
- Weight quotes by *executable* depth, not displayed depth (excludes likely spoofs).
- Track participant cancellation rates and de-weight high-cancel actors.
- Use venue-level spoofing controls (some exchanges throttle excessive cancellation).

Document 78 covers the algorithms and ML approaches in detail.

---

## Part IV — Market Impact Models

Market impact is the change in price caused by a trade. Three main types:

- **Permanent impact**: the price moves permanently because the trade revealed information.
- **Temporary impact**: the price moves only momentarily (during execution), then reverts.
- **Realized impact**: the average price obtained relative to the pre-trade benchmark.

The decomposition matters because the temporary impact is recoverable (if you can wait) while the permanent impact is not.

### Linear Impact

Kyle's λ gives a linear permanent impact: ΔP = λ Q where Q is the signed traded quantity. Linear impact is the simplest model and is appropriate for small orders relative to liquidity.

For large orders, linear impact overstates the true cost — empirical evidence shows that doubling an order's size does not double its impact.

### Square-Root Impact

Empirical studies (Almgren et al. 2005, Bouchaud–Farmer–Lillo 2009, Tóth et al. 2011) consistently find:

$$
\Delta P \approx Y \sigma \sqrt{Q / V},
$$

where Y is a coefficient (typically 0.5–1.0), σ is the asset's daily volatility, Q is the order size, and V is daily volume.

The square-root law has been confirmed across:
- Equity (US, EU, Asia).
- Futures.
- Foreign exchange.
- Crypto (with somewhat higher coefficients).

The intuition: market impact reflects the latent supply/demand schedule. If liquidity is roughly distributed as |q|^{-1/2} around the mid (a power-law schedule), then the impact of trading Q is Y σ √(Q/V).

### Theoretical Justification

Several models justify the square-root law:
- **Bouchaud–Mézard–Potters (2002)**: a martingale model in which the LOB liquidity profile is power-law.
- **Tóth–Lemperière–Deremble–Lakhal–Lillo–Bouchaud (2011)**: latent-order-book models.
- **Donier–Bouchaud (2015)**: a discrete-time analog with explicit liquidity dynamics.

All converge on the same conclusion: when liquidity is supplied with diminishing intensity at higher prices, order impact scales as the square root of size.

```python
# Square-root impact estimation from synthetic data.
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)
sigma_daily = 0.02
ADV = 1_000_000
n = 10_000

# Simulate impact: true Y = 0.7
Y_true = 0.7
Q = np.random.lognormal(8, 1, n)
V = np.random.lognormal(np.log(ADV), 0.2, n)
sigma = np.random.lognormal(np.log(sigma_daily), 0.1, n)
side = np.random.choice([-1, 1], n)
true_impact = side * Y_true * sigma * np.sqrt(Q / V)
noise = np.random.normal(0, sigma_daily * 0.05, n)
observed_impact = true_impact + noise

# Estimate: regress observed impact on side*sigma*sqrt(Q/V)
X = side * sigma * np.sqrt(Q / V)
Y_hat = np.dot(observed_impact, X) / np.dot(X, X)
print(f"True Y = {Y_true}, Estimated Y = {Y_hat:.4f}")
```

### Propagator Models

Bouchaud, Gefen, Potters, Wyart (2004): trade impact has a memory structure. Each trade contributes a fading impact:

$$
P_t = \int_{-\infty}^t G(t - s) \xi(s) ds,
$$

where ξ(s) is signed trade flow and G is a propagator (kernel) that decays from G(0) ~ 1/√t. The autocorrelation of trade signs is approximately power-law (Hurst exponent ~0.7), and the kernel exactly compensates: cross-impact dynamics are martingale-consistent.

Calibration: estimate G(τ) from the response of mid-price to lagged signed trades. The classic result: for SPX-like instruments, G(τ) ∝ 1/τ^{0.5} for τ from seconds to hours.

Propagator models give the cleanest unified picture of market impact as a stochastic-process phenomenon, not a static cost function. They are used in practice for large multi-day execution problems where the residual impact of each tranche affects subsequent ones.

### Reality Check — Impact in the Wild

Production impact models calibrate Y, σ, V daily. Modeling adjustments:

- **Time-of-day**: impact is higher at open and close due to information clustering.
- **Volatility regime**: impact scales with realized vol, not just full-sample σ.
- **Sector**: small-cap stocks have higher impact for given size; tech stocks higher than utilities.
- **Macro events**: impact spikes during FOMC, NFP, earnings.
- **Asymmetry**: buying pressure has slightly higher impact than selling (controversial but empirically present in some samples).

Document 208 (Optimal Execution Theory) integrates impact models with dynamic optimization.

---

## Part V — Optimal Execution

You have a target position. The market is liquid but not infinitely so. Trading too fast costs impact; trading too slow exposes you to price risk. Optimal execution is the science of balancing the two.

### The Almgren–Chriss Framework

Setup (Almgren–Chriss 2000):
- Total quantity X to liquidate over horizon T.
- Quantity at time t: x_t (with x_0 = X, x_T = 0).
- Traded quantity per unit time: v_t = −dx_t/dt (positive for selling).
- Permanent impact: γ v dt (linear in trade rate).
- Temporary impact: η v.
- Price dynamics under selling: dS_t = −γ v_t dt + σ dW_t.
- Execution price: S̃_t = S_t − η v_t.

The trader's wealth at the end: total revenue from selling x_t at price S̃_t over [0, T] minus market value of remaining position. The objective is to minimize a mean–variance criterion:

$$
\min_v \mathbb{E}[\text{Cost}] + \lambda \text{Var}(\text{Cost}),
$$

where λ is a risk-aversion parameter.

### Solution

For risk aversion λ, the optimal trading rate is

$$
v_t = X \frac{\sinh(\kappa(T - t))}{\sinh(\kappa T)} \cdot \kappa,
$$

with κ = √(λσ²/η). The trajectory x_t is

$$
x_t = X \frac{\sinh(\kappa(T - t))}{\sinh(\kappa T)}.
$$

For λ → 0 (risk-neutral), x_t = X (1 − t/T) — linear (TWAP) execution.

For λ → ∞ (extremely risk-averse), x_t → X 1_{t < 0} — execute everything immediately.

For moderate λ, the trajectory is concave: front-load to minimize price risk, then slow down to minimize impact.

### Implementation Shortfall

The expected execution cost minus the decision price:

$$
IS = \mathbb{E}[\text{S}_0 X - \int_0^T \tilde S_t v_t dt] = \frac{1}{2} \gamma X^2 + \eta \int_0^T v_t^2 dt.
$$

The first term is the permanent impact (irreducible if trading at all). The second is the temporary impact, which depends on how concentrated the trading is in time.

### Variance of Execution

$$
\text{Var}(\text{Cost}) = \sigma^2 \int_0^T x_t^2 dt.
$$

This is the variance from price risk on the residual position. It is reduced by trading faster (smaller x_t for longer time).

### Optimization

For Almgren–Chriss with constant parameters, minimizing 𝔼[IS] + λVar leads to

$$
v_t^* = X \kappa \frac{\sinh(\kappa(T - t))}{\sinh(\kappa T)}, \qquad \kappa = \sqrt{\lambda \sigma^2 / \eta}.
$$

In implementations, trade in discrete slices of equal time intervals, e.g., trade x_t* − x_{t-Δt}* in interval [t-Δt, t].

```python
# Almgren-Chriss optimal trajectory.
import numpy as np
import matplotlib.pyplot as plt

X = 1e6      # 1 million shares
T = 1.0      # 1 day
sigma = 0.02
gamma = 1e-7
eta = 1e-6
lam_list = [0, 1e-6, 1e-5, 1e-4]
n_pts = 100
t = np.linspace(0, T, n_pts)

plt.figure(figsize=(8, 4))
for lam in lam_list:
    if lam == 0:
        x = X * (1 - t/T)
    else:
        kappa = np.sqrt(lam * sigma**2 / eta)
        x = X * np.sinh(kappa*(T - t)) / np.sinh(kappa*T)
    plt.plot(t, x/X, label=f"λ = {lam:.0e}")
plt.xlabel('time'); plt.ylabel('residual position fraction')
plt.title('Almgren–Chriss optimal liquidation trajectories')
plt.legend(); plt.grid(True); plt.tight_layout(); plt.savefig('ac_trajectory.png', dpi=120)
```

### Extensions

- **Bertsimas–Lo (1998)**: same setup but minimize expected cost (not mean–variance). The optimal solution under linear permanent and linear temporary impact is TWAP. Square-root temporary impact gives a richer non-TWAP result.
- **Obizhaeva–Wang (2013)**: includes order-book *resilience* — temporary impact decays back to zero exponentially. For high resilience, optimal trading is back-loaded at the start; for low resilience, more uniform.
- **Cartea–Jaimungal–Penalva (2015)**: "Algorithmic and High-Frequency Trading" — comprehensive textbook treatment with stochastic control framework. Adds: signal forecasts (do you have alpha?), dark pools, multiple-venue routing, adversarial liquidity.
- **Almgren (2003) for power-law impact**: replaces η v with η v^β. For β > 1, the optimal trajectory is more uniform than for linear impact.

### Reality Check — Algos in Production

Real execution algorithms blend multiple frameworks:

- **AC-style risk balancing**: front-load when there is alpha decay or high price risk.
- **VWAP/TWAP benchmarks**: trade according to a volume profile if benchmarked to VWAP, or evenly if TWAP.
- **POV (participation rate)**: cap trade rate as a fraction of market volume.
- **Liquidity-seeking**: opportunistically post in dark pools when offsetting flow appears.
- **Anti-gaming**: avoid predictable patterns that HFT can exploit.

Production algorithm choice is a function of:
- Expected alpha decay rate (high decay → AC with high λ).
- Order size relative to ADV (small → VWAP; large → multi-day with POV cap).
- Volatility regime (high vol → faster execution).
- Market state (toxicity, news, liquidity).

The post-trade analytics measure success against benchmarks: realized IS vs target IS, realized VWAP vs target VWAP, adverse selection rates, post-fill price reversion.

---

## Bertsimas–Lo and Stochastic Control

Bertsimas–Lo (1998): minimize 𝔼[Total Cost] = 𝔼[Σ S̃_t v_t] over admissible strategies. With a more general dynamic-programming approach, this generalizes to stochastic control:

$$
V(t, x, S) = \min_{v_t} \mathbb{E}_t[\text{Future cost}] = \min_{v_t} \mathbb{E}_t[\tilde S_t v_t \, dt + V(t + dt, x - v_t dt, S + dS)].
$$

The Hamilton–Jacobi–Bellman equation:

$$
\partial_t V + \min_v \left( \tilde S v + (\text{coefficients})(\partial_x V, \partial_S V, \partial_{SS} V) \right) = 0,
$$

with terminal condition V(T, 0, S) = 0 and V(T, x, S) = +∞ for x > 0 (cannot have remaining inventory).

For specific impact functional forms (linear, square-root) and price dynamics (Brownian), the HJB has analytic solutions matching the Almgren–Chriss formulas.

The stochastic-control framework generalizes to:
- Stochastic volatility (σ varies).
- Signal-driven execution (you have alpha).
- Multiple assets (basket execution).
- Risk constraints (VaR, drawdown).

Document 208 (Optimal Execution Theory) covers the full mathematical machinery and several extensions.

---

## Obizhaeva–Wang LOB Resilience

Obizhaeva–Wang (2013) introduced the idea that the LOB has finite *resilience*. When you take liquidity, depth is depleted; over time, new orders replenish the book. The replenishment rate ρ characterizes resilience.

The model:
- Permanent impact: γ v dt (as before).
- Temporary impact decays at rate ρ: dE_t = −ρ E_t dt + η dx_t (impact on the LOB shape).

For high ρ (fast replenishment), the temporary impact decays quickly and the optimal trajectory is more uniform. For low ρ (slow replenishment), trading is concentrated at the start to avoid persistent impact.

In the limit ρ → ∞, the model reduces to Almgren–Chriss with no resilience effect. In the limit ρ → 0, all impact is permanent and there is no benefit to spreading trades over time.

### Implementation

The modified objective:

$$
\min_v \mathbb{E}[\int_0^T (\tilde S_t v_t + (\eta/(2\rho)) v_t^2) dt],
$$

where the (η/(2ρ)) v² term reflects the temporary-impact persistence. The optimal trajectory is x_t = X (1 − t/T) for risk-neutral (Bertsimas–Lo) and a modified concave shape for risk-averse cases.

### Empirical Resilience

Studies of US equity markets:
- Resilience time τ = 1/ρ ≈ 1–10 minutes for liquid stocks.
- Faster resilience for higher-ADV stocks.
- Lower resilience around news events.

For a multi-day execution, resilience matters most in the first day (when temporary impact persists). For intraday execution, resilience matters more at higher trade rates.

---

## Implementation Shortfall and Pre-Trade Analytics

Implementation Shortfall (IS) is the canonical execution-cost metric. It measures the difference between the price at the *decision* time and the average execution price, including any opportunity cost from unfilled portion.

$$
\text{IS} = \frac{1}{X}\!\left[\sum_i (\tilde P_i - P_0) Q_i + (X - \sum Q_i) \cdot (P_T - P_0)\right],
$$

where P_0 is the decision price, P_T is the post-execution market price, and Q_i, P̃_i are the executed quantities and prices.

### Pre-Trade Cost Estimation

Before sending an order, estimate IS via:

$$
\hat{\text{IS}} = \tau \sigma + Y \sigma \sqrt{Q/V},
$$

where τ is the (expected) duration in days, σ is daily vol, and the second term is the (expected) impact. The first term is a "delay risk" — uncertainty in price during the execution window.

### Post-Trade Analytics

After execution, decompose IS into:
- **Spread cost**: half-spread paid on each fill.
- **Impact cost**: realized vs pre-trade benchmark.
- **Opportunity cost**: from unfilled portion if the order was not completed.
- **Timing cost**: alpha decay — would the position have moved without the trade?

Production desks measure each component separately and feed back into algo selection.

### Reality Check — IS in Live Trading

The IS metric is the standard but has known issues:
- **Decision time is fuzzy**: when is the "decision" made? At signal generation? At order routing? At parent order arrival? Different conventions give different IS numbers.
- **Benchmark price stale**: the decision price is one observation; market noise can dwarf actual execution skill.
- **Aggregation across orders**: how to aggregate IS across many small orders is non-obvious.

The trading desk's metric should be the one they can actually measure and improve. For a market-neutral fund, daily IS aggregated by sector and by algo type is more useful than per-order IS.

---

## Smart Order Routing and Dark Pool Pegging

The smart order router (SOR) decides where to send each slice of the parent order. The decision space:
- Lit exchanges (NYSE, Nasdaq, Cboe, IEX, …).
- Dark pools (Liquidnet, ITG POSIT, Goldman Sigma, …).
- Internalizer (single-dealer platform if applicable).
- Periodic auction (e.g., Cboe BIDS).

The SOR considers:
- Current displayed depth at each lit venue.
- Likely hidden depth (from mid-peg, hidden orders).
- Historical fill rate at each venue for similar orders.
- Latency to each venue.
- Fees and rebates (maker–taker model).
- Regulatory constraints (Reg NMS, MiFID II).

### Routing Algorithms

A simple SOR algorithm:

```
For each slice of parent order:
    1. If best price is on a single venue, send marketable order there.
    2. If best price is shared, prioritize by fill rate, fees, latency.
    3. Probe dark pools at mid for size proportional to ADV.
    4. If lit fills are slow, increase aggression by crossing the spread.
    5. Track fills, update venue performance metrics.
```

In practice, ML-based routers learn from historical fill behavior:
- Conditional fill probability given (venue, order type, size, market state).
- Adverse selection rate by venue.
- Latency to each venue (real-time monitored).
- Cost decomposition (spread paid, rebates earned, impact incurred).

### Dark Pool Pegging Strategies

For a buy-side trader, posting in dark pools at mid avoids paying the spread. The trade-off: dark fills are unpredictable in timing.

Strategies:
- **Pure mid-peg**: post all volume at NBBO mid. Low aggression, low information leakage.
- **Discretionary peg**: post at mid with discretion to lift toward bid (if buying) or hit ask (if selling) when toxic flow detected.
- **Conditional**: post in pool only if internal liquidity is detected (via cross-pool indicators).

Dark pools with **midpoint-only** matching protect against information leakage but reduce fill rates. **Reference-based** matching (e.g., NBBO mid + 1 cent in your favor) gives slightly worse prices but better fills.

### Reality Check — Routing in Practice

Production SORs handle:
- Latency variance: routing decisions must be made before fast-changing quote data ages.
- Order-book uncertainty: the displayed book can be wrong if hidden orders exist.
- Adversarial fills: predatory HFT behavior in dark pools (this exists despite best efforts).
- Regulatory compliance: best-execution obligations across jurisdictions.

Production SORs are often the largest engineering investment in an institutional execution stack. They are continuously retrained on fresh market data and routinely audited for compliance.

---

## Part VI — Market Making

A market maker simultaneously quotes a bid and an ask, profiting from the spread (and potentially from inventory). The classic models give analytic solutions for optimal quoting.

### Avellaneda–Stoikov (2008)

Setup:
- Risky asset with price S_t following Brownian motion: dS = σ dW.
- MM has inventory q (positive = long, negative = short).
- Quotes bid B and ask A.
- Buy/sell market orders arrive at intensities λ_B(δ_B), λ_A(δ_A) where δ_B = mid − B and δ_A = A − mid are the bid/ask offsets from mid.
- λ_X(δ) = A_X exp(−k δ): exponential decay of arrival intensity with quote distance.

The MM maximizes expected utility of terminal wealth, with risk aversion γ:

$$
\max \mathbb{E}[\exp(-\gamma W_T)],
$$

where W_T includes mark-to-market of inventory at terminal mid.

### Solution

The optimal mid-price (reservation price) is

$$
r(t, q, S) = S - q \gamma \sigma^2 (T - t).
$$

The optimal half-spread is

$$
\delta^*(t) = \frac{\gamma \sigma^2 (T - t)}{2} + \frac{1}{\gamma} \log\!\left(1 + \frac{\gamma}{k}\right).
$$

The bid and ask are r ± δ*. Two key behaviors:

1. **Inventory skew**: the reservation price r is shifted away from the mid by qγσ²(T-t). Long inventory → quotes are skewed lower (encouraging buyers to lift the ask). Short inventory → quotes skewed higher.

2. **Time-of-day**: as t → T, the (T − t) term shrinks, so the optimal spread narrows. At the open, the MM is more cautious.

### Properties

- **Inventory penalty**: the term γq σ²(T − t) is the inventory's marked-to-market risk over the remaining horizon. The MM trades it off against the spread.
- **Skew effect**: for q > 0, the MM is willing to pay slightly more on the bid (smaller δ_B) to attract sellers. This is the "no-trade region."
- **No symmetric reflection**: when γ → 0, the model reduces to Ho–Stoll (1981), and the spread is determined purely by arrival rate.

```python
# Avellaneda-Stoikov optimal quotes.
import numpy as np
import matplotlib.pyplot as plt

def as_quotes(S, q, t, T, sigma, gamma, k):
    r = S - q * gamma * sigma**2 * (T - t)
    delta = (gamma * sigma**2 * (T - t)) / 2 + (1/gamma)*np.log(1 + gamma/k)
    return r - delta, r + delta, r

# Plot quotes over time for various inventories
T, sigma, gamma, k = 1.0, 0.02, 0.1, 1.5
times = np.linspace(0, T, 100)
fig, ax = plt.subplots(figsize=(8, 4))
for q in [-3, 0, 3]:
    bids, asks = [], []
    for t in times:
        b, a, _ = as_quotes(100, q, t, T, sigma, gamma, k)
        bids.append(b); asks.append(a)
    ax.plot(times, bids, '--', label=f'q={q} bid')
    ax.plot(times, asks, '-', label=f'q={q} ask', alpha=0.6)
ax.set_xlabel('time'); ax.set_ylabel('quote price'); ax.legend(); ax.grid(True)
plt.tight_layout(); plt.savefig('as_quotes.png', dpi=120)
```

### Production Considerations

Production MM systems extend Avellaneda–Stoikov with:
- **Multi-asset inventory**: cross-hedging via correlated assets. Reservation price depends on both individual and portfolio risk.
- **Time-varying λ**: arrival intensity depends on volatility regime, time of day, news.
- **Asymmetric flow**: buys and sells arrive at different rates depending on regime; flow toxicity changes the model.
- **Tick size constraints**: real quotes are integer-priced; the optimal continuous quote is quantized.
- **Transaction fees**: maker rebates and taker fees affect the optimal spread.
- **Co-location latency**: cancellation latency is finite; quotes adjust must be propagated through the matching engine.

The Cartea, Jaimungal, and Penalva (2015) book gives extensive treatments of these extensions and the corresponding stochastic-control HJB equations.

---

## Ho–Stoll (1981) and Cartea–Jaimungal Frameworks

Ho–Stoll (1981) preceded Avellaneda–Stoikov by 30 years. The setup is similar but in discrete time:

- The MM faces stochastic arrival of buy and sell orders.
- Each order generates revenue equal to half the spread, but inventory accumulates.
- The MM optimizes expected utility over a finite horizon.

The Ho–Stoll spread for risk-neutral case is the quoted spread that balances expected profit per period with the cost of holding the resulting inventory. The result is similar in spirit to A-S: optimal spread depends on arrival rate, volatility, and risk aversion.

### Cartea–Jaimungal Generalization

Cartea, Jaimungal, and Penalva (2015) generalize to:
- Continuous-time stochastic control with stochastic volatility.
- Latency in quote updates and cancellations.
- Adverse selection (informed flow) in the arrival process.
- Cross-asset hedging.
- Optimal execution with signal-driven quotes.

The HJB equation for the Cartea–Jaimungal framework is

$$
\partial_t V + \mu \partial_S V + \tfrac{1}{2} \sigma^2 \partial_{SS} V + \max_{\delta_A, \delta_B} \!\left( \lambda_A(\delta_A) [(S + \delta_A) (\partial_q V) - V] + \lambda_B(\delta_B) [(S - \delta_B) (\partial_q V) - V] \right) = 0.
$$

The maximization gives the optimal δ_A, δ_B as functions of (t, q, S). The HJB is solved via PDE methods or via deep-learning function approximators (Hu–Liu 2019).

### Reality Check — Beyond Avellaneda–Stoikov

A-S gives the right intuition but misses crucial production realities:

- **Heterogeneous flow**: not all market orders are equally toxic. A retail flow algo will pay much less adverse selection than an institutional algo.
- **Multi-tick spread**: in liquid markets the spread is one tick; quoting half-tick is impossible. The optimization is constrained.
- **Volume-based discounts**: maker rebates depend on volume tiers; large MMs see lower effective spreads.
- **Co-location latency**: a slow MM is repeatedly adverse-selected, even if optimal in theory.

Production systems run A-S as a *starting point* with modifications based on real-time market state.

---

## Inventory and Adverse-Selection Management

The MM's inventory is the central state variable. Managing it requires:

### Inventory Limits

Hard caps prevent inventory from growing too large:
- Per-asset inventory cap (e.g., 10× average daily traded size).
- Per-currency inventory cap.
- Per-sector cap.
- Total firm-wide net exposure.

### Skew

Beyond hard caps, the MM skews quotes to encourage offsetting flow. The standard formula:

$$
\text{quote shift} = -q \cdot \text{(risk aversion)} \cdot \text{(remaining horizon variance)}.
$$

### Inventory Hedging

For correlated assets, the MM can hedge inventory using a basket of related securities. The hedge minimizes residual variance:

$$
h^* = -\Sigma^{-1} \sigma_q,
$$

where Σ is the covariance matrix of hedge candidates and σ_q is the covariance of inventory with each hedge candidate.

### Adverse Selection Detection

Real-time monitors track adverse selection in real time:

- **Realized spread**: per-trade realized profit (compared to expected based on the spread).
- **Microstructure-noise variance**: high noise variance indicates many small adverse-selecting trades.
- **VPIN**: as discussed, a measure of order-flow toxicity.

When these metrics exceed thresholds, the MM widens quotes, reduces displayed size, or temporarily exits.

### Reality Check — Inventory Management as Risk Management

Inventory management is the link between market making and traditional risk management. A market maker's central P&L comes from spread, but the central *risk* is inventory. Managing one without the other is incomplete; production systems integrate quoting, hedging, and inventory monitoring in a single risk engine.

---

## Part VII — HFT Strategies: A Taxonomy

High-frequency trading (HFT) refers to fully-automated strategies that operate at sub-millisecond timescales. The taxonomy:

### 1. Market Making

The largest category. Provides liquidity by quoting tight bid–ask spreads, profiting from the spread and rebates. Requires sub-microsecond cancellation to manage adverse selection.

### 2. Latency Arbitrage

Profits from price discrepancies across venues that arise due to direct-feed vs SIP latency. Requires direct feeds, co-location, and specialized hardware.

### 3. Statistical Arbitrage / Stat Arb

Pairs trading and basket strategies at high frequency. Profits from short-term mean reversion in correlated instruments.

### 4. Event Trading

Trades on the directional impact of news, earnings, FOMC, etc. Requires fast news feeds and natural-language processing.

### 5. Predatory HFT

Detects large institutional orders and trades ahead of them. Includes spoofing, layering, momentum-ignition. Largely illegal.

### 6. Cross-Asset Arbitrage

Trades the relationship between related assets (e.g., index futures and underlying stocks, ETFs and constituents).

### 7. Quote-Stuffing and Order-Book Spamming

Floods venues with order updates to slow down competitors. Now largely defended-against but still present.

### Production Volume Distribution (rough estimates)

- US Equity: HFT accounts for ~50% of total volume; market making is the largest component.
- US Equity Futures (E-mini): HFT ~70%.
- FX spot: HFT ~50%, dominated by EBS and Reuters.
- Crypto: HFT ~30–50% on major exchanges, much higher on derivatives.

### Reality Check — HFT Is Diverse

The popular conception of HFT as "predatory" is partly accurate but misses the dominant share of HFT activity, which is market making — a service that benefits the market by tightening spreads and improving liquidity. Predatory HFT is a real concern (and largely illegal), but it is a small fraction of total HFT volume.

The economic argument: HFT market making is a competitive industry. Without HFT, spreads in major equities would be ~2–3× wider and depth would be ~30% lower. The cost is some loss to less-fast institutional flow that becomes adversely selected.

---

## Latency Arbitrage

The simplest HFT strategy and the one most often analyzed. The setup:

- Two venues quote the same asset.
- Venue A is faster to update its quote when news arrives.
- Trader receives both feeds, sees A's update first, immediately trades against the now-stale quote on B.
- Profits: B's stale price minus A's new price (per share traded).

### Strategy

1. Subscribe to direct feeds from both A and B.
2. When a quote update arrives from A, compute the implied new price.
3. Compare to B's last quote.
4. If a profitable arbitrage exists, send an order to B before B updates.
5. Total latency from A's update to B's order arrival must be less than B's update latency.

The profit per arbitrage is small (typically half-tick to one tick), but the volume can be enormous. Aggregate HFT firm revenue from latency arb is in the hundreds of millions to billions per year.

### Defenses

- **IEX speed bump**: 350-microsecond delay applied uniformly to all incoming orders (and all outgoing market data). This ensures that a late-arriving update on IEX cannot be exploited by an earlier-arriving order from a competing venue.
- **Frequent batch auctions**: 100-millisecond batched matching. All orders submitted in the interval are equally privileged.
- **Speed bumps elsewhere**: NYSE American (350µs), NEO (random delay), and others have variants.

### Reality Check — Latency Arb Is Real

Latency arbitrage is a well-documented phenomenon. Studies (Brogaard 2010, Hasbrouck–Saar 2013, Aquilina–Foucault–Lescourret 2022) consistently find that direct-feed-equipped traders profit from quote updates ahead of slower participants. The aggregate cost to slow participants is meaningful.

The economic question is whether latency arb is a *value-add* or a *rent extraction*. The answer is mixed: some latency arb (cross-venue arbitrage) does push prices toward consistency and is value-creating; some (predatory targeting of slow orders) is rent extraction. Regulatory and exchange responses are calibrated to the latter.

---

## Part VIII — Microstructure Noise and Realized Volatility

Microstructure noise is the discrepancy between observed prices and the underlying efficient price. It arises from bid–ask bounce, discrete pricing, and adverse selection. In low-frequency analysis, noise washes out; at high frequencies, it dominates.

### The Observed Process

Let M_t be the efficient (latent) price and ε_t be microstructure noise. The observed price is

$$
P_t = M_t + \varepsilon_t.
$$

The realized variance of P over [0, T]:

$$
RV^{(\Delta)} = \sum_{i=0}^{N-1} (P_{t_{i+1}} - P_{t_i})^2.
$$

In the absence of noise, RV → ⟨M⟩_T as Δ → 0. With noise:

$$
RV^{(\Delta)} \to \int_0^T \sigma_s^2 ds + N \cdot \mathbb{E}[\Delta\varepsilon^2] = \langle M \rangle_T + 2 N \, \text{Var}(\varepsilon).
$$

The noise term grows linearly with N — at high frequencies, noise dominates. The empirical implication: there is an *optimal sampling frequency* that minimizes the bias-variance trade-off.

### Two-Scales Realized Volatility (TSRV)

Zhang, Mykland, Aït-Sahalia (2005): combine RV at two different sampling frequencies to cancel the noise bias:

$$
\widehat{RV}_{\text{TSRV}} = RV^{(\Delta)} - \frac{n}{n_K} \cdot RV^{(\Delta_K)},
$$

where Δ is the coarse grid and Δ_K is the fine grid (Δ_K = Δ/K), n is total observations, n_K = n/K. The bias-corrected estimator converges to the true integrated variance with rate O(N^{-1/4}).

### Realized Kernels

Barndorff-Nielsen, Hansen, Lunde, Shephard (2008): use a kernel-weighted sum of cross-products. Different kernels (Bartlett, Parzen, Tukey-Hanning) give different bias-variance trade-offs. The realized kernel converges to ∫σ_s² ds with rate O(N^{-1/5}), the optimal rate under the noise model.

### Bipower Variation and Jump Detection

Andersen, Bollerslev, Diebold, Labys (2003): bipower variation is the sum of the products of *consecutive* absolute returns:

$$
BV_T^{(\Delta)} = \frac{\pi}{2} \sum_{i=1}^{N-1} |P_{t_{i+1}} - P_{t_i}| \cdot |P_{t_i} - P_{t_{i-1}}|.
$$

In the absence of jumps, BV → ⟨M⟩_T as Δ → 0. With jumps, BV is *not* affected (asymptotically), while RV includes jump variance. The difference RV − BV estimates the jump variance.

A formal jump test (Lee–Mykland 2008, Jiang–Oomen 2008): under no jumps, RV − BV is asymptotically Gaussian with known variance, so a z-test detects jumps.

### Reality Check — Noise vs Signal

In practice, distinguishing noise from signal at high frequencies is hard. The noise model (additive white noise) is often violated: real microstructure noise is autocorrelated, heteroscedastic, and non-Gaussian. The classical estimators (TSRV, realized kernel) are robust to many of these violations; non-classical methods (Hayashi–Yoshida for asynchronous data, RT for irregular sampling) handle the corner cases.

For trading, the question is usually not "what is the true integrated variance" but "what is the predictable component of next-period variance." Forecasting models (HAR-RV, GARCH on RV, FAR) blend the realized-variance estimators with autoregressive structure.

---

## Part IX — Empirical Stylized Facts

We close with the stylized facts of microstructure that any production model must reproduce.

### Fact 1: Heavy-Tailed Returns

Daily and intraday return distributions have power-law tails. The tail index is typically 3–5 for major equity indices (i.e., the probability of a return r decays as |r|^{-α} for α ≈ 3–5). This is far heavier than the Gaussian assumption.

### Fact 2: Volatility Clustering

|r_t|² and |r_t| have long-range autocorrelation. Returns themselves are nearly white-noise; absolute returns are not. The autocorrelation of |r_t| decays as a power law over weeks-to-months.

### Fact 3: Leverage Effect

Negative returns predict higher subsequent volatility, more strongly than positive returns. The asymmetry is pronounced in equities and weaker in commodities and FX.

### Fact 4: Volume–Volatility Correlation

|r_t| and volume are positively correlated. The mixture-of-distributions hypothesis (Tauchen–Pitts 1983) gives a structural explanation.

### Fact 5: Periodic Intraday Patterns

Volatility, volume, and spreads have daily seasonality:
- Open: high vol, high volume, wide spreads.
- Mid-day: low vol, low volume, narrow spreads.
- Close: high vol, very high volume, wide spreads.

### Fact 6: Inverse Spread–Volume Relationship

Across stocks and across time, volume is negatively correlated with spread. More-liquid stocks have tighter spreads.

### Fact 7: Power-Law LOB Profile

The depth at price level k (counting from the best) follows roughly a power law: depth ∝ k^{-β} for β ≈ 1–2. This drives the square-root impact law.

### Fact 8: Long-Range Trade-Sign Memory

Signed trades have power-law autocorrelation: Cov(ε_t, ε_{t+τ}) ∝ τ^{-α} for α ≈ 0.5. This is consistent with the propagator decomposition.

### Fact 9: Square-Root Impact

Already covered. Universal across asset classes.

### Fact 10: Noise Scaling

Microstructure noise variance is roughly constant across time, but its proportion of total return variance grows as the sampling frequency increases.

### Reality Check — Stylized Facts in Modern Markets

The stylized facts have been remarkably stable across decades, despite massive structural change in markets (decimalization, HFT emergence, algo trading rise). This stability is itself a stylized fact, and it suggests that the underlying drivers (information asymmetry, dispersed trader heterogeneity, finite liquidity) are persistent.

What has changed: the *scale* of these effects. Spreads are tighter, depth is shallower at top of book, latency advantages are larger, fragmentation is greater. But the qualitative patterns persist.

---

## Reference Tables, Cheat Sheets, Bibliography

### Quick Reference

| Concept | Symbol | Typical Value (US Equity) |
|---|---|---|
| Bid–ask spread (large-cap) | s | 1 cent (1 tick) |
| Bid–ask spread (mid-cap) | s | 1–5 cents |
| Bid–ask spread (small-cap) | s | 5–50 cents |
| Top-of-book depth (liquid stock) | D | 1,000–10,000 shares |
| Daily volume (S&P 500 stock) | V | 1M–100M shares |
| Average trade size | q | 100–500 shares |
| Cancellation rate | — | 95%+ |
| Latency to top exchanges (co-located) | — | 1–10 µs |
| Maker rebate | — | 0.20–0.30 cents/share |
| Taker fee | — | 0.20–0.30 cents/share |
| Permanent impact (ASX Y) | Y | 0.1–1.0 |
| Square-root impact coefficient | — | 0.3–0.7 |

### Bibliography (Annotated)

- **Kyle, A. (1985), "Continuous Auctions and Insider Trading", *Econometrica* 53(6): 1315–1336.** The foundational paper.
- **Glosten, L. and Milgrom, P. (1985), "Bid, Ask and Transaction Prices in a Specialist Market with Heterogeneously Informed Traders", *Journal of Financial Economics* 14: 71–100.** The other foundational paper.
- **O'Hara, M. (1995), *Market Microstructure Theory*, Blackwell.** The textbook treatment.
- **Hasbrouck, J. (2007), *Empirical Market Microstructure*, Oxford.** The practitioner-oriented text.
- **Foucault, T., Pagano, M., and Röell, A. (2013), *Market Liquidity*, Oxford.** Comprehensive textbook.
- **Almgren, R. and Chriss, N. (2000), "Optimal Execution of Portfolio Transactions", *J. Risk* 3(2): 5–39.** The execution paper.
- **Avellaneda, M. and Stoikov, S. (2008), "High-Frequency Trading in a Limit Order Book", *Quant Finance* 8(3): 217–224.** The market-making paper.
- **Bouchaud, J., Farmer, J.D., Lillo, F. (2009), "How Markets Slowly Digest Changes in Supply and Demand", in *Handbook of Financial Markets: Dynamics and Evolution*.** The propagator approach.
- **Cartea, Á., Jaimungal, S., and Penalva, J. (2015), *Algorithmic and High-Frequency Trading*, Cambridge.** The current standard textbook.
- **Easley, D., López de Prado, M., and O'Hara, M. (2012), "The Volume Clock: Insights into the High-Frequency Paradigm", *J. Portfolio Management* 39(1): 19–29.** VPIN.
- **Tóth, B., Lemperière, Y., Deremble, C., de Lataillade, J., Kockelkoren, J., Bouchaud, J. (2011), "Anomalous Price Impact and the Critical Nature of Liquidity in Financial Markets", *Phys Rev X* 1: 021006.** Square-root impact.
- **Andersen, T., Bollerslev, T., Diebold, F., and Labys, P. (2003), "Modeling and Forecasting Realized Volatility", *Econometrica* 71(2): 579–625.** Realized volatility.
- **Zhang, L., Mykland, P., Aït-Sahalia, Y. (2005), "A Tale of Two Time Scales: Determining Integrated Volatility with Noisy High-Frequency Data", *J. Amer. Statist. Assoc.* 100(472): 1394–1411.** TSRV.
- **Aldridge, I. (2013), *High-Frequency Trading*, Wiley (2nd ed).** Practical HFT reference.
- **Lewis, M. (2014), *Flash Boys*, Norton.** Popular but well-researched. Useful for the historical context of the speed bump debate.

### Cross-References

- Document 76 — VPIN Order Flow Toxicity.
- Document 77 — Iceberg Order Detection.
- Document 78 — Spoofing Detection Algorithms.
- Document 79 — Limit Order Book Heatmaps.
- Document 80 — Queue Position Estimation.
- Document 200 — Stochastic Calculus and Continuous-Time Finance.
- Document 208 — Optimal Execution Theory.
- Document 210 — HFT Architecture and Latency Engineering.
- Document 211 — Backtesting Statistical Rigor.

---

## Coda: The Microstructure Mindset

A trader who thinks in terms of microstructure asks different questions than a trader who thinks in terms of fundamentals or macros. The microstructure-trained eye sees:

- Where is my order in the queue?
- What is the implied probability of fill at the current price?
- What is the adverse-selection cost of placing here vs there?
- How much will my own trading move the price, and over what horizon?
- What is the noise floor of the price signal I'm seeing?
- Who else is trading here, and what are they likely doing?
- How fragmented is the opportunity set across venues?

These questions do not replace the fundamental and macro analysis; they augment it. Two traders with the same fundamental insight will earn very different returns based on how well they execute. The execution alpha is, for many strategies, the dominant source of P&L variability.

This document is the toolkit for building that microstructure mindset. The mathematical foundations from document 200 (especially Brownian motion and martingales) underpin everything here. The empirical regularities are the bridge from theory to practice. The algorithms — from Almgren–Chriss to Avellaneda–Stoikov — are the operational interface.

The remaining documents in this expansion build on what we have here. Document 202 covers volatility surface modeling, where microstructure-informed implied-vol calibration is the input to derivatives trading. Document 206 covers extreme value theory, the right framework for the heavy tails we noted as Stylized Fact 1. Document 208 dives deeper into optimal execution. Document 211 covers the statistical hygiene needed to validate any of the microstructure-informed strategies described above.

---

*End of document 201. Approximately 5,400 lines as initially written; targeted to reach 12,000 lines via additional worked examples, deeper code implementations of each model, and extended empirical case studies in subsequent expansion passes.*
