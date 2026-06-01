# 10. Network Topology & Graph Neural Networks (GNNs) for Crypto

**Abstract**
Cryptocurrency transactions form a massive, dynamic graph. Analyzing this structure reveals hidden patterns (AML/CFT risks, wash trading) invisible to tabular models. This document details **Graph Neural Networks (GNNs)** for node classification and **Network Topology Metrics** (Centrality) for feature engineering.

---

## 1. The Transaction Graph $G = (V, E)$

Let $V$ be the set of addresses (nodes) and $E$ be the set of transactions (directed edges).
Each edge $e_{uv} \in E$ has features $x_{uv}$ (amount, timestamp).
Each node $u \in V$ has features $h_u$ (balance, age).

### 1.1 Centrality Measures (Feature Engineering)
Traditional metrics capture node importance.
*   **Degree Centrality ($k_i$):** $k_i = \sum_j A_{ij}$. High in-degree = Exchange/Mixer.
*   **PageRank ($PR_i$):**
    $$ PR_i = \alpha \sum_j \frac{A_{ji}}{k_j^{out}} PR_j + \frac{1-\alpha}{N} $$
    Captures flow accumulation (e.g., Ponzi scheme hubs).
*   **Betweenness Centrality ($g(v)$):**
    $$ g(v) = \sum_{s 
eq v 
eq t} \frac{\sigma_{st}(v)}{\sigma_{st}} $$
    Where $\sigma_{st}$ is the number of shortest paths from $s$ to $t$. High betweenness = Bridge/Gateway.

### 1.2 Community Detection (Louvain Algorithm)
To identify clusters (e.g., a darknet market's wallet cluster):
Maximize Modularity $Q$:
$$ Q = \frac{1}{2m} \sum_{ij} \left( A_{ij} - \frac{k_i k_j}{2m} ight) \delta(c_i, c_j) $$
Where $c_i$ is the community of node $i$.

---

## 2. Graph Neural Networks (GNNs) for Classification

We aim to classify nodes as "Illicit" (1) or "Licit" (0).
GNNs propagate information from neighbors to learn structural embeddings.

### 2.1 Graph Convolutional Network (GCN)
The layer update rule:
$$ H^{(l+1)} = \sigma \left( 	ilde{D}^{-\frac{1}{2}} 	ilde{A} 	ilde{D}^{-\frac{1}{2}} H^{(l)} W^{(l)} ight) $$

Where:
*   $	ilde{A} = A + I$: Adjacency matrix with self-loops.
*   $	ilde{D}$: Degree matrix of $	ilde{A}$.
*   $W^{(l)}$: Learnable weight matrix.
*   $\sigma$: Activation function (ReLU).

This aggregates features from the 1-hop neighborhood. Stacking $L$ layers aggregates from the $L$-hop neighborhood.

### 2.2 Graph Attention Network (GAT)
GAT assigns *attention coefficients* $\alpha_{ij}$ to neighbors, learning which connections are important (e.g., large volume transfers).
$$ \alpha_{ij} = \frac{\exp(	ext{LeakyReLU}(a^T [Wh_i || Wh_j]))}{\sum_{k \in \mathcal{N}_i} \exp(	ext{LeakyReLU}(a^T [Wh_i || Wh_k]))} $$
The update rule is a weighted sum:
$$ h_i' = \sigma \left( \sum_{j \in \mathcal{N}_i} \alpha_{ij} W h_j ight) $$

### 2.3 EvolveGCN (Dynamic Graphs)
Crypto graphs change over time. EvolveGCN uses an RNN to update the GCN parameters $W_t$ based on the graph snapshot $G_t$.
$$ W_t = 	ext{GRU}(W_{t-1}, G_t) $$
This captures temporal patterns (e.g., a sudden burst of laundering activity).

---

## 3. Anti-Money Laundering (AML) Features

Specific topological patterns indicate illicit activity.

*   **Peeling Chains:** A large amount is split into smaller amounts over many hops.
    *   *Detection:* Long paths with decreasing value and 1-in-2-out structure.
*   **Fan-Out / Fan-In:** One address sends to many (Fan-Out) or receives from many (Fan-In).
    *   *Detection:* High Out-Degree / In-Degree variance.
*   **Cycle Detection:** Funds returning to the origin (Wash Trading).
    *   *Detection:* Finding cycles of length $k$ (DFS).

---

**References:**
1.  Kipf, T. N., & Welling, M. (2017). "Semi-Supervised Classification with Graph Convolutional Networks".
2.  Velickovic, P., et al. (2018). "Graph Attention Networks".
3.  Weber, M., et al. (2019). "Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks".
