# 04. Reinforcement Learning: Policy Optimization & Risk

**Abstract**
Reinforcement Learning (RL) allows an agent to optimize complex, long-term objectives (e.g., Sharpe Ratio) in stochastic environments. However, traditional RL algorithms (DQN, PPO) struggle with sample inefficiency and unstable convergence in finance. This document details the implementation of **Soft Actor-Critic (SAC)** for continuous portfolio allocation and the **Differential Sharpe Ratio** reward function.

---

## 1. Soft Actor-Critic (SAC) for Continuous Control

SAC is an off-policy, actor-critic algorithm that maximizes a trade-off between expected return and entropy.

### 1.1 Objective Function
The standard RL objective maximizes expected cumulative reward $\sum r_t$. SAC adds an entropy regularization term $\alpha \mathcal{H}(\pi(\cdot|s_t))$:

$$ J(\pi) = \sum_{t=0}^T \mathbb{E}_{(s_t, a_t) \sim \rho_\pi} \left[ r(s_t, a_t) + \alpha \mathcal{H}(\pi(\cdot|s_t)) \right] $$

Where $\mathcal{H}(\pi(\cdot|s_t)) = - \log \pi(a_t|s_t)$ is the entropy of the policy at state $s_t$.
$\alpha$ is the temperature parameter controlling the exploration-exploitation trade-off.

**Why Entropy in Finance?**
Financial markets are non-stationary and noisy. A deterministic policy (DDPG) will overfit to noise. A stochastic policy with high entropy encourages the agent to explore diverse actions and prevents premature convergence to a local optimum (e.g., "always buy").

### 1.2 Policy Network (Actor)
The policy outputs the parameters of a Gaussian distribution: mean $\mu_\phi(s_t)$ and standard deviation $\sigma_\phi(s_t)$.
$$ a_t = \tanh(\mu_\phi(s_t) + \sigma_\phi(s_t) \odot \epsilon_t), \quad \epsilon_t \sim \mathcal{N}(0, I) $$
The $\tanh$ squashes the action to $[-1, 1]$ (e.g., full short to full long).

### 1.3 Value Functions (Critic)
SAC learns two Q-functions $Q_{\theta_1}, Q_{\theta_2}$ to mitigate overestimation bias.
$$ \mathcal{L}_Q(\theta_i) = \mathbb{E}_{(s_t, a_t) \sim \mathcal{D}} \left[ (Q_{\theta_i}(s_t, a_t) - (r_t + \gamma V_{\bar{\psi}}(s_{t+1})))^2 \right] $$
Where $V_{\bar{\psi}}$ is a target value network updated via Polyak averaging.

---

## 2. The Differential Sharpe Ratio Reward Function

Using simple P&L as a reward is flawed because it rewards high variance strategies. We need to maximize the Sharpe Ratio $S_t$. However, calculating $S_t$ requires the full history, making it unsuitable for step-wise RL.

**The Solution:** Differential Sharpe Ratio ($D_t$).
This approximates the *contribution* of the current trade to the Sharpe Ratio.

Let $A_t$ be the exponential moving average of returns $R_t$:
$$ A_t = A_{t-1} + \eta (R_t - A_{t-1}) $$
Let $B_t$ be the exponential moving average of squared returns $R_t^2$:
$$ B_t = B_{t-1} + \eta (R_t^2 - B_{t-1}) $$

The Sharpe Ratio at time $t$ is $S_t = \frac{A_t}{\sqrt{B_t - A_t^2}}$.

The **Differential Sharpe Ratio** is the first-order Taylor expansion of $S_t$ with respect to $\eta$:
$$ D_t \equiv \frac{dS_t}{d\eta} = \frac{B_{t-1} \Delta A_t - \frac{1}{2} A_{t-1} \Delta B_t}{(B_{t-1} - A_{t-1}^2)^{3/2}} $$

Where $\Delta A_t = R_t - A_{t-1}$ and $\Delta B_t = R_t^2 - B_{t-1}$.

**Implementation:**
The reward at each step is:
$$ r_t = D_t - \lambda |\Delta w_t| $$
Where $\lambda |\Delta w_t|$ penalizes transaction costs (turnover).

This provides a dense, immediate signal that guides the agent towards risk-adjusted returns.

---

## 3. Sim-to-Real Transfer: Robustness

Models trained on historical data fail in live trading due to **Market Impact** and **Latency**.

### 3.1 Domain Randomization
During training, we randomize environmental parameters:
*   **Latency:** Delay execution by $k \sim \text{Poisson}(\lambda)$ steps.
*   **Slippage:** Execution price $P_{exec} = P_t (1 \pm \delta)$, where $\delta \sim \mathcal{U}(0, \delta_{max})$.
*   **Spread:** Widen bid-ask spread randomly.

The agent learns a policy that is robust to these perturbations.

### 3.2 Adversarial Training
Train an "Adversary" agent whose goal is to minimize the Trader's reward by modifying the price process within a bounded range (e.g., $\pm 1\%$ of volatility).
$$ \min_{\pi_{trader}} \max_{\pi_{adversary}} \mathbb{E}[R] $$
This forces the Trader to adopt a conservative strategy (e.g., mean reversion only when mispricing is extreme) to survive the worst-case scenario.

---

**References:**
1.  Haarnoja, T., et al. (2018). "Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor". *ICML*.
2.  Moody, J., et al. (1998). "Performance Functions and Reinforcement Learning for Trading Systems and Portfolios". *Journal of Forecasting*.
3.  Jiang, Z., et al. (2017). "A Deep Reinforcement Learning Framework for the Financial Portfolio Management Problem". *arXiv*.