# 45 - Monte Carlo Simulation: Stress Testing

**Volume:** 45 of 50
**Strategy Type:** Risk Management / Validation / Quantitative Finance
**Risk Profile:** Model Risk / GIGO (Garbage In, Garbage Out)
**Mathematical Basis:** Random Number Generation ($S_t = S_{t-1} e^{(\mu - 0.5\sigma^2)\Delta t + \sigma \sqrt{\Delta t} Z}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Alternative Futures](#2-the-theory-alternative-futures)
    * 2.1. History is just one path.
    * 2.2. "What if?" Scenarios (Could current drawdown be worse?)
    * 2.3. Path Dependency (Sequence of Returns Risk)
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Calculate Asset Drift ($\mu$) and Volatility ($\sigma$).
    * 3.2. Generate 10,000 Random Walks based on these parameters.
    * 3.3. Apply Strategy Logic to each Walk.
    * 3.4. Measure Distribution of Outcomes (Max Drawdown, Final Wealth).
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Geometric Brownian Motion (GBM)
    * 4.2. Cholesky Decomposition (Correlated Random Walks)
    * 4.3. Value at Risk (VaR) = 95th Percentile Loss
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Assessing Retirement Risk (The 4% Rule failure rate)
    * 5.2. Designing HFT Systems (Testing latency spikes)
    * 5.3. Option Pricing (Monte Carlo for American Options)
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. Vectorized Simulation (Numpy)
    * 6.2. Bootstrapping (Resampling historical returns)
    * 6.3. Generating "Fat Tail" Distributions (Student's t-distribution)
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Block Bootstrapping" (Preserving volatility clusters)
    * 7.2. "Stress Testing" (Forcing a crash in the simulation)
    * 7.3. "Parameter Sensitivity" (What if Volatility doubles?)
8. [Risk Management: The Map is Not the Territory](#8-risk-management-the-map-is-not-the-territory)
    * 8.1. Normal Distribution Fallacy (Black Mondays happen more often than 6-sigma).
    * 8.2. Stationarity Assumption (Future parameters != Past parameters).
    * 8.3. "Overfitting to Noise" (Tuning strategy to pass the Monte Carlo).
9. [Conclusion: Confidence Intervals](#9-conclusion-confidence-intervals)

---

# 1. Executive Summary

**Monte Carlo Simulation** does not predict the future.
It maps the **Range of Possibilities**.
If your backtest shows a Max Drawdown of 20%.
But your Monte Carlo shows a 5% chance of a 50% Drawdown.
You must plan for the 50% Drawdown.
It reveals the hidden risks that history was lucky enough to avoid.

---

# 2. The Theory

### 2.1. Sequence Risk

Portfolio A: +50%, -50%. Result: -25%.
Portfolio B: -50%, +50%. Result: -25%.
Wait.
What if you are withdrawing money? Or rebalancing?
Sequence matters.
Monte Carlo shuffles the sequence of returns to see if you survive the "Bad Luck" path.

### 2.2. GBM

Standard model assumes prices follow Geometric Brownian Motion.
Log Returns are normally distributed.
This is a good approximation, but fails in crises.
Advanced Monte Carlo uses "Jump Diffusion" or "Stochastic Volatility" models.

---

# 3. Strategy Rules

### 3.1. Construction

Inputs:

1. Mean Return (Annualized).
2. Std Dev (Annualized).
3. Correlation Matrix (If multi-asset).
4. Time Horizon (Years).
5. Number of Simulations (N=10,000).

### 3.2. Execution

Run the loop.
Store the equity curve of each run.
Calculate Statistics on the aggregate results.

* Median Outcome (50th percentile).
* Worst Case (1st percentile).
* Best Case (99th percentile).

---

# 4. Mathematical Derivation

Simulating Price Path:
$$ S_{t+1} = S_t \exp\left((\mu - \frac{\sigma^2}{2})\Delta t + \sigma \sqrt{\Delta t} Z\right) $$
Where $Z$ is a random draw from Standard Normal $N(0,1)$.
For Correlated Assets:
$$ Z_{correlated} = L \times Z_{uncorrelated} $$
Where $L$ is the Cholesky matrix of covariance $\Sigma$.

---

# 5. Historical Case Studies

### 5.1. Retirement Design

Financial Planners use MC to determine "Probability of Success".
If valid paths show the retiree running out of money before death in 10% of cases.
Plan Fails.
Adjust spending or allocation.

### 5.2. Strategy Validation

You have a Trading Bot. Sharpe 2.0 over 5 years.
Is it luck or skill?
Run MC on Randomized Entry/Exits (Null Hypothesis).
If 1000 random bots perform worse than your bot, you have Alpha.
If 500 random bots beat your bot, you have Luck.

---

# 6. Python Implementation

```python
import numpy as np
import matplotlib.pyplot as plt

class MonteCarloSimulator:
    def __init__(self, start_price, mu, sigma, days, simulations):
        self.S0 = start_price
        self.mu = mu
        self.sigma = sigma
        self.T = days
        self.N = simulations

    def run_gbm(self):
        dt = 1/252
        # Generate random component
        Z = np.random.normal(0, 1, (self.T, self.N))
        
        # Drift and Diffusion
        drift = (self.mu - 0.5 * self.sigma**2) * dt
        diffusion = self.sigma * np.sqrt(dt) * Z
        
        # Cumulative Sum of log returns
        log_ret = np.cumsum(drift + diffusion, axis=0)
        
        # Price Paths
        price_paths = self.S0 * np.exp(log_ret)
        
        # Insert initial price at t=0
        price_paths = np.vstack([np.full((1, self.N), self.S0), price_paths])
        return price_paths
```

### 6.3. Bootstrapping

Instead of generating generic Normal returns based on Mean/Sigma.
Take the actual historical daily % changes (last 10 years).
Randomly sample them with replacement.
This preserves the "Fat Tails" (Kurtosis) of real history.
Market crashes (-10%) will appear in the simulation with realistic frequency.

---

# 7. Optimization

### 7.1. Stress Testing

Manually inject a "Shock".
"Assume Year 3 has a -40% drop."
Does the strategy recover?
Required for bank regulation (CCAR).

### 7.2. Convergence

How many sims?
Standard Error decreases with $\sqrt{N}$.
1,000 runs gives rough idea.
10,000 runs gives precision.
1,000,000 runs needed for VaR at 99.9% confidence.

---

# 8. Risk Management

### 8.1. Model Risk

"All models are wrong, some are useful."
If you assume Normal Distribution, you underestimate Tail Risk by 100x.
Using Student's t-distribution with low degrees of freedom (df=3) is better for finance.

### 8.2. Correlation Breakdown

GBM assumes constant correlation.
In reality, correlations are dynamic.
Sophisticated MC uses "Regime Switching" models (HMM).
Regime 1: Low Vol, Low Corr.
Regime 2: High Vol, High Corr.

---

# 9. Conclusion

Monte Carlo is the "Laboratory" of finance.
You cannot test a strategy in the real world 10,000 times.
You can in Python.
For GOLIATH, we rigorously stress test every strategy.
We require a probability of Ruin < 0.1% over 10 years.
We discard any strategy that fails the "Fat Tail" bootstrap simulation.
It is the final gatekeeper before deployment.
