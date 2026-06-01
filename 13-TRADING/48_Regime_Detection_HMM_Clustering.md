# 48 - Regime Detection: HMM, Clustering & Markov Chains

**Volume:** 48 of 50
**Strategy Type:** Machine Learning / Regime Switching / Meta-Strategy
**Risk Profile:** Lag / Misclassification
**Mathematical Basis:** Bayesian Inference ($P(S_t | O_t)$) & Markov Transition Matrix ($P_{ij}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Mapping the Territory](#2-the-theory-mapping-the-territory)
    * 2.1. Hidden Markov Models (HMM): The Hidden State underlying noise.
    * 2.2. Explicit Markov Chains: The Probability of Change.
    * 2.3. K-Means Clustering: The Geometry of Market Conditions.
3. [Strategy 1: HMM Switcher](#3-strategy-1-hmm-switcher)
    * 3.1. Gaussian HMM on Returns. (Bull vs Bear).
    * 3.2. Execution: Dynamic Leverage based on $P(State=Bull)$.
4. [Strategy 2: The Explicit Markov Matrix](#4-strategy-2-the-explicit-markov-matrix)
    * 4.1. Defining Discrete States (e.g., RSI Zones).
    * 4.2. Calculating Transition Probabilities ($P_{ij}$).
    * 4.3. Signal: Regime Persistence ($P_{ii}$).
5. [Strategy 3: The Chameleon (Clustering)](#5-strategy-3-the-chameleon-clustering)
    * 5.1. Feature Engineering: ADX, ATR, RSI.
    * 5.2. Mapping Cluster ID -> Strategy Type.
6. [Microstructure Application](#6-microstructure-application)
    * 6.1. HFT Order Book Dynamics (Buy/Sell Imbalance Transitions).
7. [Implementation: Production Grade](#7-implementation-production-grade)
    * 7.1. Python (HMM + K-Means + Matrix).
    * 7.2. Rust (Linfa & Discrete Chains).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Regime Detection** is the navigation system of the GOLIATH architecture.
Traders often ask "What is the price doing?" (Trend).
The better question is "What is the market doing?" (Regime).
Strategies that work in a **Bull Market** fail in a **Choppy Market**.
This file integrates **Probabilistic Models** (HMM), **Discrete Models** (Markov Chains), and **Geometric Models** (Clustering) to classify the market environment in real-time and adapt the strategy portfolio accordingly.

---

# 2. The Theory

## 2.1. Hidden Markov Models (HMM)

The market has "Hidden States" (e.g., Expansion, Contraction). We only see "Emissions" (Returns).
HMM infers the probability of the hidden state:
$$ P(S_t = k | Y_{1:t}) $$
It handles noise well because it assumes the state persists.

## 2.2. Explicit Markov Chains

From `057_Markov`:
If we define explicit states (e.g., State 1: RSI > 70), we can measure the probability of transition:
$$ P_{ij} = P(S_{t+1}=j | S_t=i) $$
This gives us the "Sheet Music" of the market's rhythm.

* **Sticky Regime:** $P_{ii} \approx 0.9$. (Trend Follow).
* **Fragile Regime:** $P_{ii} \approx 0.5$. (Mean Revert).

---

# 4. Strategy 2: The Explicit Markov Matrix

## 4.1. Construction

1. **Discretize Data:** Convert continuous indicators into discrete states.
    * State 0: ATR < SMA(ATR). (Low Vol).
    * State 1: ATR > SMA(ATR). (High Vol).
2. **Count Transitions:** How often does Low Vol $\to$ High Vol?

## 4.2. Signal Generation

* **Regime Persistence:** If $P_{Low, Low} = 0.95$, we can aggressively short volatility (Iron Condors), knowing the regime is stable.
* **Transition Alert:** If $P_{Low, High}$ historically spikes before a crash, and we see the probability rising in a rolling window, we exit early.

---

# 6. Microstructure Application (HFT)

## 6.1. Order Book Markov Model

HFTs model the Limit Order Book (LOB) as a Markov Chain.

* State A: Bid Depth > Ask Depth.
* State B: Bid Depth < Ask Depth.
* **Transitions:** If $P_{A \to B}$ is high within 100ms, it predicts a price drop (as support evaporates).
* **Action:** Cancel Bids immediately if $P(B|A)$ exceeds threshold.

---

# 7. Implementation: Production Grade

## 7.1. Python (The Regime Pipeline)

```python
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class RegimeDetector:
    def __init__(self):
        self.hmm = GaussianHMM(n_components=2, n_iter=100)
        self.kmeans = KMeans(n_clusters=3, random_state=42)
        
    def fit_hmm(self, returns):
        X = returns.values.reshape(-1, 1)
        self.hmm.fit(X)
        
    def get_hmm_state(self, returns):
        return self.hmm.predict(returns.values.reshape(-1, 1))[-1]

    def calculate_transition_matrix(self, discrete_states):
        """
        discrete_states: Series of ints (0, 1, 2...)
        """
        n_states = discrete_states.nunique()
        matrix = np.zeros((n_states, n_states))
        
        for i in range(len(discrete_states)-1):
            curr = discrete_states.iloc[i]
            next_ = discrete_states.iloc[i+1]
            matrix[curr, next_] += 1
            
        # Normalize
        probs = matrix / matrix.sum(axis=1, keepdims=True)
        return probs
```

## 7.2. Rust (Discrete Markov Chain)

```rust
pub struct MarkovChain {
    counts: [[u32; 3]; 3], // 3 states
    last_state: Option<usize>,
}

impl MarkovChain {
    pub fn new() -> Self {
        Self { counts: [[0; 3]; 3], last_state: None }
    }

    pub fn update(&mut self, current_state: usize) {
        if let Some(prev) = self.last_state {
            if prev < 3 && current_state < 3 {
                self.counts[prev][current_state] += 1;
            }
        }
        self.last_state = Some(current_state);
    }

    pub fn transition_prob(&self, from: usize, to: usize) -> f64 {
        let sum: u32 = self.counts[from].iter().sum();
        if sum == 0 { return 0.0; }
        self.counts[from][to] as f64 / sum as f64
    }
}
```

---

# 8. Conclusion

**Strategy 48** is not about being right about the price. It is about being right about the **Environment**.
By using **HMM** (Implicit) and **Markov Chains** (Explicit), we gain a probability map of the battlefield.
If we know we are in a "High Volatility Bear Regime", we turn off the "Dip Buyer" (Strat 02) and turn on the "Short Seller" (Strat 01).
This "Meta-Strategy" is what allows GOLIATH to survive decades, not just months.
