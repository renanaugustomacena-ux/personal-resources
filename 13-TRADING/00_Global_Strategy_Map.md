# 00 - The GOLIATH Global Strategy Map: A Taxonomy of Alpha

**Volume:** Index & Taxonomy
**Date:** 2026-02-18
**Author:** Antigravity (Senior Quantitative Researcher)
**Scope:** Global financial markets (Equities, Forex, Crypto, Derivatives)

---

# 1. Introduction: The Search for Alpha

Alpha ($\alpha$) is the excess return of an investment relative to the return of a benchmark index. In the modern quantitative landscape, alpha is not found; it is mined. This Encyclopedia anatomizes every major family of trading strategy known to institutional finance, categorized by their underlying mathematical premise.

Each subsequent volume in this series will provide a deep-dive analysis (>4000 words) into the specific implementation, risks, and data requirements of these strategies.

# 2. Volume 01: Trend Following & Momentum (The "Beta" Hunters)

*Premise: Prices exhibit serial correlation; what goes up is likely to continue going up.*

* **1.1. Time-Series Momentum (TSMomp):** The canonical "Trend" strategy. Going long assets with positive past returns and short assets with negative past returns.
* **1.2. Moving Average Crossovers:** The collaborative filter of finance. SMA vs EMA vs WMA. The "Golden Cross" and quantitative variants.
* **1.3. Breakout Strategies:** Donchian Channels and the "Turtle Trading" rules. Capturing volatility expansion.
* **1.4. Ichimoku Kinko Hyo:** A comprehensive "equilibrium" visual trend system.

# 3. Volume 02: Mean Reversion & Statistical Arbitrage ( The "Rubber Band")

*Premise: Prices overreact to information and eventually return to a fair value (equilibrium).*

* **2.1. Pairs Trading (Co-integration):** Identifying two assets that move together (e.g., KO/PEP, GLD/GDX). Short the winner, long the loser.
* **2.2. Bollinger Band Reversion:** Exploiting standard deviation extremes (2$\sigma$ moves).
* **2.3. RSI / Oscillator Extremes:** Quantitative oversold/overbought conditions.
* **2.4. Ornstein-Uhlenbeck Processes:** Mathematical modeling of mean-reverting stochastic processes for optimal entry/exit timing.

# 4. Volume 03: Market Making & High-Frequency Trading (The "Microstructure")

*Premise: Providing liquidity and earning the spread, or exploiting micro-latency inefficiencies.*

* **3.1. Market Making (Stoikov-Avellaneda):** Maintaining a two-sided quote to capture the spread while managing inventory risk ($Q$).
* **3.2. Order Book Imbalance (OBI):** Predicting short-term price moves ($<$1s) based on the shape of the L2/L3 order book.
* **3.3. Latency Arbitrage:** Beating the NBBO (National Best Bid and Offer) by microseconds.
* **3.4. Rebate Capture:** Trading solely to collect exchange rebates (Maker-Taker models).

# 5. Volume 04: Machine Learning & AI Alpha (The "Black Box")

*Premise: Non-linear relationships in data can predict price movements better than linear models.*

* **4.1. Supervised Learning (Forecasting):** Using Gradient Boosting (XGBoost/LightGBM) and LSTMs to predict $P_{t+1}$.
* **4.2. Reinforcement Learning (RL):** Agents (PPO, DQN, A3C) learning policy optimization by interacting with a market simulator.
* **4.3. Feature Engineering:** Fractional Differentiation (FracDiff), Entropy, Wavelet transforms.
* **4.4. Genetic Algorithms:** Evolving strategies through mutation and crossover.

# 6. Volume 05: Volatility & Options Strategies (The "Convexity")

*Premise: Initial direction is irrelevant; magnitude or speed of movement is the edge.*

* **5.1. Delta Neutral Trading:** Hedging directional risk to isolate Volatility ($\sigma$).
* **5.2. Gamma Scalping:** Adjusting hedges dynamically to profit from movement convexity.
* **5.3. VIX Arbitrage:** Trading the term structure of volatility (Contango vs Backwardation).
* **5.4. Dispersion Trading:** Selling index volatility while buying constituent volatility.

# 7. Volume 06: Fundamental & Macro Strategies (The "Big Picture")

*Premise: Asset prices are ultimately driven by economic cash flows and central bank policy.*

* **6.1. Global Macro:** Trading interest rate differentials (Yield Curve) and GDP growth disparities.
* **6.2. Carry Trade:** Borrowing in low-rate currencies (JPY) to buy high-rate currencies (AUD/USD).
* **6.3. Event-Driven:** Merger Arbitrage, Earnings Surprises, FDA Approvals.
* **6.4. Sentiment Analysis (NLP):** Trading on news sentiment (BERT) and social media volume.

# 8. Volume 07: Alternative Data (The "Edge")

*Premise: Information not yet priced into the market provides the highest Sharpe ratios.*

* **7.1. Satellite Imagery:** Counting cars in Walmart parking lots to predict earnings.
* **7.2. Credit Card Transaction Data:** Predicting consumer revenue before earnings calls.
* **7.3. On-Chain Metrics (Crypto):** MVRV Z-Score, Hash Rate ribbons, Whale wallet alerts.

---

**Execution Plan:**
This index serves as the roadmap. Each volume will be generated sequentially, ensuring maximum depth, mathematical rigor, and actionable implementation details.
