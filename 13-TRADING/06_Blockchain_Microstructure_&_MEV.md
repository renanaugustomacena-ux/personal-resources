# 06. Blockchain Microstructure & MEV Extraction

**Abstract**
Blockchain markets introduce a novel microstructure where transaction ordering is not First-In-First-Out (FIFO) but determined by an auction mechanism (Gas). This document models the stochastic arrival of blocks, the game-theoretic equilibrium of Priority Gas Auctions (PGA), and the quantification of Maximal Extractable Value (MEV) using Knapsack-like optimization formulations.

---

## 1. Block Arrival Dynamics (Poisson Process)

In Proof-of-Work (PoW) and Proof-of-Stake (PoS) systems (like Ethereum post-Merge), block production is stochastic.

### 1.1 Homogeneous Poisson Process
We model the arrival of blocks as a Poisson process $\{N(t), t \ge 0\}$ with rate $\lambda$ (e.g., $\lambda \approx 1/12$ sec$^{-1}$ for Ethereum).
The probability of $k$ blocks arriving in time $T$ is:
$$ P(N(T) = k) = \frac{e^{-\lambda T} (\lambda T)^k}{k!} $$

The inter-arrival times $	au_i = t_i - t_{i-1}$ follow an Exponential distribution:
$$ f(	au) = \lambda e^{-\lambda 	au} $$

**Implication for Sniping:**
If an arbitrage opportunity exists at time $t$, the probability that it survives until the next block at $t+\delta$ decays exponentially with $\delta$. High-frequency "snipers" must optimize their latency $L$ such that $P(	ext{next block} \in [t, t+L])$ is minimized.

---

## 2. Gas Auctions & Priority Ordering

Transactions compete for inclusion in a block with finite capacity $C_{gas}$ (e.g., 30M gas). This is modeled as an auction.

### 2.1 First-Price Auction (Legacy / EIP-1559)
In a First-Price Auction (FPA), the bidder pays their bid $b_i$.
Let $v_i$ be the private valuation of the trade (MEV profit).
The utility of bidder $i$ is:
$$ U_i(b_i) = \begin{cases} v_i - b_i & 	ext{if } b_i > \max_{j 
eq i} b_j \ 0 & 	ext{otherwise} \end{cases} $$
**Nash Equilibrium:**
In a symmetric equilibrium with $n$ bidders drawing valuations from $F(v)$ on $[0, \bar{v}]$, the optimal bid strategy is:
$$ b^*(v) = v - \frac{\int_0^v F(t)^{n-1} dt}{F(v)^{n-1}} $$
This leads to "bid shading" and inefficiency (spam).

### 2.2 Generalized Second-Price (GSP) Auction (Flashbots)
Flashbots bundles use a sealed-bid auction where the winner pays (conceptually) just enough to displace the next best bundle.
However, in reality, searchers pay $b_i = 	ext{coinbase\_transfer}$.
The Miner/Validator maximizes:
$$ \max_{S \subset \mathcal{T}} \sum_{tx \in S} b_{tx} \quad 	ext{s.t.} \sum_{tx \in S} g_{tx} \le C_{gas} $$
This is the **Knapsack Problem** (NP-Hard). Validators use greedy heuristics (sort by effective gas price $b_{tx} / g_{tx}$).

---

## 3. MEV Quantification & Extraction Strategies

Maximal Extractable Value (MEV) is the total value that can be extracted from block state manipulation.

### 3.1 Sandwich Attacks (Slippage Exploitation)
A user submits a swap $A 	o B$ with amount $x_{in}$ and min output $y_{min}$.
The AMM invariant is $x \cdot y = k$.
The attacker fronts-runs with $\Delta x_{front}$ and back-runs with $\Delta x_{back}$.

**Price Impact Function:**
New price after front-run:
$$ P' = \frac{y - \Delta y_{front}}{x + \Delta x_{front}} $$
The victim executes at $P'$. If $P' > P_{limit}$, the transaction fails.
**Optimal Front-Run Size:**
The attacker solves:
$$ \max_{\Delta x} \left( 	ext{Revenue}(\Delta x) - 	ext{GasCost} ight) $$
Subject to the constraint that the victim's slippage tolerance is *exactly* hit.
$$ \frac{y_{victim}}{x_{victim}} \ge P_{limit} $$

### 3.2 Cyclic Arbitrage (Graph Theory)
Let $G = (V, E)$ be a graph of tokens (nodes) and liquidity pools (edges).
Each edge $e_{ij}$ has a weight $w_{ij} = -\log(P_{ij})$, where $P_{ij}$ is the price of $i$ in terms of $j$.
An arbitrage opportunity is a negative cycle in the graph.
$$ \sum_{(i,j) \in Cycle} w_{ij} < 0 \implies \prod P_{ij} > 1 $$

**Algorithm:**
Use **Bellman-Ford** or **SPFA** (Shortest Path Faster Algorithm) to detect negative cycles.
Since fees exist, we modify the weight:
$$ w_{ij} = -\log(P_{ij} \cdot (1 - 	ext{fee})) $$

---

**References:**
1.  Daian, P., et al. (2019). "Flash Boys 2.0: Frontrunning, Transaction Reordering, and Consensus Instability".
2.  Budish, E., et al. (2015). "The High-Frequency Trading Arms Race: Frequent Batch Auctions as a Market Design Response".
3.  Roughgarden, T. (2021). "Transaction Fee Mechanism Design for the Ethereum Blockchain: An Economic Analysis of EIP-1559".
