# 47 - Reinforcement Learning: PPO & Q-Learning (Actor-Critic)

**Volume:** 47 of 50
**Strategy Type:** Reinforcement Learning / Artificial Intelligence / Adaptive Control
**Risk Profile:** High (Exploration Risk / Overfitting to Sim)
**Mathematical Basis:** Bellman Equation ($Q$) & Policy Gradient ($\nabla J$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Actor vs Critic](#2-the-theory-actor-vs-critic)
    * 2.1. Policy Optimization (PPO): The Actor. Decides *what* to do.
    * 2.2. Q-Learning (DQN): The Critic. Decides *how good* that was.
    * 2.3. The Synergy: Actor-Critic Architectures.
3. [Strategy 1: PPO Agent (Continuous Control)](#3-strategy-1-ppo-agent-continuous-control)
    * 3.1. State Space: Market features.
    * 3.2. Action Space: Portfolio Weights (Continuous).
    * 3.3. Reward: Sharpe Ratio.
4. [Strategy 2: The Q-Trader (Discrete Control)](#4-strategy-2-the-q-trader-discrete-control)
    * 4.1. The Q-Value Indicator: $Q(Buy) - Q(Sell)$.
    * 4.2. Value Divergence Strategy.
    * 4.3. Microstructure: Smart Order Routing (SOR).
5. [Mathematical Derivation](#5-mathematical-derivation)
    * 5.1. Bellman Optimality: $Q^*(s, a) = E [ R + \gamma \max Q^*(s', a') ]$.
    * 5.2. PPO Clipping Objective.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Stable Baselines3 PPO & DQN).
    * 6.2. Rust (Custom Q-Table for HFT).
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Reinforcement Learning (RL)** moves beyond "Prediction" to "Control".
Instead of predicting "Price will go up", RL asks "What is the optimal action to maximize long-term wealth?"
This file consolidates two major approaches:

1. **PPO (Proximal Policy Optimization):** The "Brain" that learns complex, stable policies.
2. **Q-Learning (DQN):** The "Gut" that learns the expected value of actions.
Together, they form the **Actor-Critic** brain of GOLIATH.

---

# 2. The Theory

## 2.1. Policy Optimization (The Actor)

The Agent learns a policy function $\pi(a|s)$ that maps States directly to Actions.
*"I see a Bull Flag, so I Buy."*
**PPO** is the standard for stability, preventing the agent from changing its mind too drastically after one lucky trade.

## 2.2. Q-Learning (The Critic)

The Agent learns a value function $Q(s, a)$ that estimates future rewards.
*"Buying here is worth +$50. Selling is worth -$10."*
It guides the Actor by criticizing its choices.

---

# 4. Strategy 2: The Q-Trader

## 4.1. The Q-Value Indicator

We can use the Q-Network *as an indicator*.
If $Q(Buy) = 100$ and $Q(Sell) = -50$, the model is **Confident**.
If $Q(Buy) = 10$ and $Q(Sell) = 11$, the model is **Confused** (High Entropy).
**Rule:** Only take trades when Value Divergence > Threshold.

## 4.2. Smart Order Routing (HFT)

HFT algorithms use simple Q-Tables to route orders.

* **State:** Liquidity at Exchange A, B, C.
* **Action:** Send to A.
* **Reward:** Fill Price - Mid Price.
* **Outcome:** The algo learns which exchange has the best hidden liquidity for each market state.

---

# 6. Implementation: Production Grade

## 6.1. Python (PPO & DQN)

```python
import gymnasium as gym
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.vec_env import DummyVecEnv

# 1. Define Environment (The Matrix)
class TradingEnv(gym.Env):
    def __init__(self, data):
        self.data = data
        self.action_space = gym.spaces.Discrete(3) # 0: Hold, 1: Buy, 2: Sell
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(20,))
        
    def step(self, action):
        # Execute trade logic...
        reward = self._calculate_sharpe_reward()
        return obs, reward, done, truncated, info

# 2. Train Actor (PPO)
env = DummyVecEnv([lambda: TradingEnv(df)])
actor = PPO("MlpPolicy", env, verbose=1)
actor.learn(total_timesteps=1_000_000)

# 3. Train Critic (DQN)
critic = DQN("MlpPolicy", env, verbose=1)
critic.learn(total_timesteps=1_000_000)

# 4. Hybrid Execution
def hybrid_predict(obs):
    # Check Critic's confidence
    q_values = critic.predict(obs, deterministic=True) # Logic to extract Q-values needed
    # If confident, ask Actor
    action, _ = actor.predict(obs)
    return action
```

## 6.2. Rust (High-Speed Q-Table)

For HFT micro-decisions, Neural Nets are too slow. We use HashMaps.

```rust
use std::collections::HashMap;

pub struct QLearner {
    q_table: HashMap<String, Vec<f64>>, // State -> [Q(Act1), Q(Act2)...]
    alpha: f64, // Learning Rate
    gamma: f64, // Discount Factor
}

impl QLearner {
    pub fn update(&mut self, state: &str, action_idx: usize, reward: f64, next_state: &str) {
        let current_qs = self.q_table.entry(state.to_string()).or_insert(vec![0.0; 3]);
        let old_value = current_qs[action_idx];
        
        let next_qs = self.q_table.entry(next_state.to_string()).or_insert(vec![0.0; 3]);
        let max_next = next_qs.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        
        // Bellman Update
        let new_value = old_value + self.alpha * (reward + self.gamma * max_next - old_value);
        current_qs[action_idx] = new_value;
    }
}
```

---

# 7. Risk Management

## 7.1. Sim-to-Real Gap

Simulators fill orders instantly. Reality does not.
**Solution:** The Environment `step()` function must include a "Latency Lag" (execute at Close + 1 tick) and "Slippage Model" (Fee + Impact).
If the RL agent can't make money with fees, it's useless.

## 7.2. Reward Hacking

The agent might learn to simply "Not Trade" to maximize Sharpe Ratio (0 volatility = undefined Sharpe).
**Solution:** Add a small "Existence Tax" (negative reward per step) to force it to find alpha.

---

# 8. Conclusion

**Strategy 47** is the brain of the operation.
It uses **PPO** to develop complex, nuanced strategies (Portfolio weighting).
It uses **Q-Learning** to make fast, tactical decisions (Order Routing, Validating entries).
Unlike static algorithms, it **evolves**. If the market changes, the agent adapts.
It is the ultimate "Anti-Fragile" strategy.
