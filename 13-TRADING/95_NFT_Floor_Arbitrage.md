# 95 - NFT Floor Arbitrage & Reinforcement Learning (PPO)

**Volume:** 95 of 100
**Strategy Type:** Alternative Alpha / Crypto / AI Agent / Market Making
**Risk Profile:** Liquidity Crunch (Bag Holding) / Protocol Risk (Marketplace Hacks)
**Mathematical Basis:** Rareness Scoring (TF-IDF), Bellman Equation, & Proximal Policy Optimization (PPO)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context](#2-historical-context)
    * 2.1. The Rise of NFT-Fi (Blur, Sudoswap).
    * 2.2. Reinforcement Learning: From AlphaGo to AlphaTrader.
3. [The Theory: Auction Games & Agents](#3-the-theory-auction-games--agents)
    * 3.1. The Floor & The Trait Premium.
    * 3.2. Blur vs OpenSea: The Market Microstructure.
    * 3.3. Reinforcement Learning (Indicator 092): The Autonomous Agent.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Rarity Score Calculation.
    * 4.2. The Policy Gradient (RL).
    * 4.3. PPO Clip Objective.
5. [The Strategy Rules](#5-the-strategy-rules)
    * 5.1. Valuation Model: Predicting $P_{fair}$.
    * 5.2. The Policy Network (Bidding Logic).
    * 5.3. Execution: Sniping & Market Making.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python: Rarity & Valuation.
    * 6.2. Python: PPO Agent (Stable Baselines3).
    * 6.3. Flashbots & Mempool Usage.
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 95** fuses the inefficiency of **NFT Markets** with the adaptability of **Reinforcement Learning (PPO)**.
NFT markets are messy, emotional, and illiquid—perfect for an AI Agent that doesn't feel FOMO.
We treat NFT trading not as "Investing", but as an **Auction Game**.
The Agent (Indicator 092) learns the optimal bidding strategy (When to snipe? When to bid wall? When to dump?) by interacting with the environment (Blur/OpenSea) millions of times in simulation, maximizing its Reward (PnL).

---

# 2. Historical Context

### 2.1. The NFT Microstructure Evolution

* **Gen 1 (OpenSea 2021):** Slow, click-based, retail dominated.
* **Gen 2 (Gem/Genie):** Aggregators, sweepers.
* **Gen 3 (Blur 2023):** Pro trading terminal. Incentivized bidding. Market structures similar to LOBs.
This evolution allows for HFT-style strategies (Bid Walls) that were previously impossible.

### 2.2. Reinforcement Learning

In 2016, AlphaGo beat Lee Sedol by learning the rules of Go through self-play.
HFT firms applied this to trading. Instead of hard-coding "If RSI < 30, Buy", they taught agents to "Maximize Sharpe Ratio" and let the agent discover the nuances of liquidity provision and adverse selection.

---

# 3. The Theory: Auction Games & Agents

### 3.1. The Trait Premium

Item A: "Red Background" (Common). Floor Price 1 ETH.
Item B: "Gold Skin" (Rare, 1% supply). Fair Value 5 ETH.
Inefficiency: Sellers often list Rare items *at the floor* due to laziness or panic.
Strategy: Goliath detects "Gold Skin" > 4 ETH premium. Buy at 1.1. Sell at 4.5.

### 3.2. Reinforcement Learning (Indicator 092)

**The Policy Gradient:**
The Policy $\pi_\theta(a|s)$ outputs the probability of taking action $a$ in state $s$.
We maximize $J(\theta) = \mathbb{E}[R]$.
$$ \nabla_\theta J(\theta) = \mathbb{E} [\nabla_\theta \log \pi_\theta(a|s) A_t ] $$
where $A_t$ is the **Advantage Function** (How much better was this action than average?).

**PPO Clip Objective:**
To prevent the agent from changing its policy too drastically (instability), PPO clips the update:
$$ L^{CLIP} = \mathbb{E} [ \min(r_t(\theta) A_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t) ] $$

---

# 4. Mathematical Derivation

### 4.1. Rarity Score ($S$)

$$ S = \sum_{trait \in Token} \frac{1}{P(trait)} $$
This score inputs into the State Vector for the RL Agent.

### 4.2. Fair Value Estimate

$$ V_{NFT} = \max(Floor, \sum w_i T_i) $$
Where $T_i$ is the value of Trait $i$, learned via Regression on past sales.

---

# 5. The Strategy Rules

### 5.1. The Value Model (The Brain)

Predicts $P_{fair}$ for every token.
$P_{fair} = f(Traits, Rarity, Momentum)$.

### 5.2. The Policy Network (The Hand)

The PPO agent observes the gap between $P_{market}$ and $P_{fair}$.
**State Space:** 50 inputs (Floor Price, Spread, Volatility, Gas, Rarity Gap).
**Actions:**

1. **Snipe:** Buy immediately.
2. **Bid:** Place Limit Bid at $Floor - \delta$.
3. **Wait:** Do nothing.
4. **Dump:** Sell inventory.

### 5.3. Execution

* **Flashbots:** For snipes, bypass the mempool to avoid front-running.
* **Blur API:** For bidding, update quotes every block to capture "Blur Points" (Yield) + Spread.

---

# 6. Implementation: Production Grade

### 6.1. Python: Rarity Calculator

*(From Strategy 95 Source)*

```python
import pandas as pd

def calculate_rarity_score(metadata_df):
    total_supply = len(metadata_df)
    scores = {}
    
    for trait_type in metadata_df['attributes']:
        counts = trait_type.value_counts()
        score = 1 / (counts / total_supply)
        scores[trait_type] = score
        
    return scores
```

### 6.2. Python: PPO Agent (Stable Baselines3)

*(From Indicator 092 Source - Integrated)*

```python
import gym
from stable_baselines3 import PPO
import numpy as np

class NFTTradingEnv(gym.Env):
    def __init__(self, market_data):
        self.market = market_data
        self.inventory = []
        self.balance = 10.0 # ETH
    
    def step(self, action):
        # Action space: 0=Hold, 1=Bid_Floor, 2=Snipe
        current_state = self._get_state()
        reward = 0
        
        # LOGIC
        if action == 2: # Snipe
            if current_state['mispricing'] > 0:
                profit = current_state['mispricing'] - 0.01 # Gas Cost
                reward = profit # Direct PnL Reward
        
        # PPO requires next_state, reward, done, info
        return next_state, reward, done, {}

def train_agent():
    # Load historical NFT tick data
    env = NFTTradingEnv(historical_data)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=100000)
    return model
```

### 6.3. Snipe Bot Execution

*(From Strategy 95 Source)*

```python
def snipe_bot(w3, contract_address, max_price_eth):
    # Monitor Pending Transactions
    # If "listings creation" detected with price < max_price
    # And rarity > threshold
    # Send buy tx with higher gas (Flashbots)
    pass
```

---

# 7. Risk Management

### 7.1. Illiquidity Trap

NFTs are not ERC-20s. You cannot sell instantly.
**RL Constraint:** Penalize holding inventory > 24 hours in the Reward Function ($R = PnL - \lambda \times TimeHeld$).
This forces the Agent to learn "Quick Flip" strategies and avoid "Bag Holding".

### 7.2. Rug Pull Detection

Monitor Contract Interactions. If "Minting" stops or Team wallet dumps, Blacklist collection. The Policy Network should have "Team Wallet Balance" as an input feature.

---

# 8. Conclusion

Strategy 95 is the **Autonomous Vulture**.
It circles the digital ecosystem.
It uses **Reinforcement Learning** to remove human emotion from an asset class defined by emotion.
While "Degen buyers" ape into projects based on hype, the Agent executes based on converged policy gradients and Bellman optimality.
It is the strategy of the Digital Native.
