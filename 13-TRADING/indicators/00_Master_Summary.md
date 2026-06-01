# Encyclopedia of Indicators: The Master Index

This document serves as the **Table of Contents** for the "Encyclopedia of Indicators" project.
Each of the 130+ entries below corresponds to a detailed 4000-word monograph dedicated to the mathematical formulation, implementation, and interpretation of that specific indicator.

---

## Phase 1: The Basics (Trend & Momentum)

1. **[001] Moving Averages (SMA/EMA)**: The foundational filters for trend identification and noise reduction. ($MA_t = \frac{1}{n}\sum P_i$)
2. **[002] RSI (Relative Strength Index)**: Welles Wilder's momentum oscillator measuring speed and change of price movements. ($100 - \frac{100}{1+RS}$)
3. **[003] Bollinger Bands**: Adaptive volatility envelopes based on standard deviation around a moving average. ($\bar{x} \pm 2\sigma$)
4. **[004] MACD**: The convergence and divergence of two moving averages, revealing momentum shifts. ($EMA_{12} - EMA_{26}$)
5. **[005] Fibonacci Retracement**: Horizontal lines indicating areas of support or resistance at the key Fibonacci levels. ($\phi = 1.618$)
6. **[006] Ichimoku Cloud**: A comprehensive indicator that defines support, resistance, trend direction, and momentum. (Equilibrium)
7. **[007] Parabolic SAR**: A trend-following indicator that sets a trailing stop price. (Stop and Reverse)
8. **[008] Stochastic Oscillator**: Compares a particular closing price to a range of prices over a period of time. (%K, %D)
9. **[009] ADX (Average Directional Index)**: Quantifies the strength of a trend regardless of direction. (DX)
10. **[010] OBV (On-Balance Volume)**: Uses volume flow to predict changes in stock price. (Accumulation/Distribution)

## Phase 2: Advanced Technicals

1. **[011] Williams %R**: A momentum indicator that measures overbought and oversold levels. (Inverse Stochastic)
2. **[012] MFI (Money Flow Index)**: Returns a value of 0 to 100, showing money flow intensity. (Volume-Weighted RSI)
3. **[013] ATR (Average True Range)**: A measure of volatility introduced by Welles Wilder. (Range Decomposition)
4. **[014] Standard Deviation**: Statistical measure of historical volatility and dispersion. ($\sigma$)
5. **[015] CCI (Commodity Channel Index)**: Identifies cyclical trends to Spot new trends or warn of extreme conditions.
6. **[016] Pivot Points**: Significant support and resistance levels derived from the prior period's High, Low, and Close.
7. **[017] Cross-Rate Parity**: Triangular structure in Forex markets ensuring no risk-free arbitrage. ($A/B \times B/C = A/C$)
8. **[018] Keltner Channels**: Volatility-based envelopes set above and below an EMA using ATR.
9. **[019] Donchian Channels**: formed by taking the highest high and the lowest low of the last $n$ periods. (Breakout)
10. **[020] VWAP (Volume Weighted Average Price)**: The average price a stock has traded at throughout the day, based on both volume and price.

## Phase 3: Statistical & Microstructure

1. **[021] Z-Score**: The number of standard deviations a data point is from the mean. (Standardization)
2. **[022] Cointegration Vector**: Identifying stationary linear combinations of non-stationary time series. (Engle-Granger)
3. **[023] Hurst Exponent**: A measure of the long-term memory of a time series. (R/S Analysis)
4. **[024] Kalman Filter**: An algorithm that uses a series of measurements observed over time containing noise to produce estimates. (State Space)
5. **[025] SuperTrend**: A trend-following indicator similar to a moving average but uses ATR for stop-loss.
6. **[026] Order Book Imbalance (OBI)**: The ratio of buy orders to sell orders at the best bid and ask. (Microstructure)
7. **[027] VPIN**: Volume-Synchronized Probability of Informed Trading. (Flow Toxicity)
8. **[028] Sentiment Score (NLP)**: Quantifying the emotional tone of text data using models like BERT. (Polarity)
9. **[029] Heikin Ashi**: "Average Bar" technique to filter out market noise. (Modified OHLC)
10. **[030] Satellite Object Count**: Alternative data metric counting physical objects (cars, tanks) from space.

## Phase 4: Machine Learning I (Classical)

1. **[031] Linear Regression Slope**: The rate of change of the line of best fit. ($y = mx + c$)
2. **[032] Logistic Regression Probability**: The probability of a binary outcome (e.g., Price Up/Down). (Sigmoid Function)
3. **[033] Feature Importance (RF)**: Ranking input variables based on their contribution to prediction accuracy in Random Forests. (Gini Impurity)
4. **[034] Kyle's Lambda**: A measure of market impact and liquidity from microstructure theory. ($\lambda$)
5. **[035] TWAP (Time Weighted Average Price)**: The average price of a security over a specified time. (Execution Algo)
6. **[036] Support Vectors (SVM)**: The data points that define the decision boundary in an SVM. (Margin Maximization)
7. **[037] Cluster Centroids (k-Means)**: The center points of identified data clusters representing market regimes. (Unsupervised)
8. **[038] Copula Dependence**: Functions that join multivariate distribution functions to their one-dimensional marginal distribution functions. (Tail Risk)
9. **[039] Principal Components (PCA)**: The orthogonal directions of maximum variance in high-dimensional data. (Eigenvectors)
10. **[040] Renko Blocks**: Charting technique that ignores time and focuses solely on price changes. (Brick Size)

## Phase 5: Deep Learning & Advanced Math

1. **[041] Ornstein-Uhlenbeck Parameters**: Mean reversion speed ($\theta$), long-term mean ($\mu$), and volatility ($\sigma$).
2. **[042] Half-Life of Mean Reversion**: The time it takes for a series to return halfway to its mean. ($t_{1/2} = \ln(2)/\theta$)
3. **[043] Grid Geometric Spacing**: The mathematical ratio used to space orders in a grid trading strategy. (Geometric Progression)
4. **[044] Kelly Criterion**: The theoretical optimal fraction of the bankroll to bet. ($f^* = p - q/b$)
5. **[045] Spearman Rank Correlation**: A non-parametric measure of rank correlation. (Monotonicity)
6. **[046] Distance Correlation**: A measure of dependence between two random vectors, zero only if they are independent. (Non-linear)
7. **[047] LSTM Hidden State**: The memory vector in a Long Short-Term Memory network capturing temporal context. (Gating)
8. **[048] GRU Gating Units**: Update and Reset gates in a Gated Recurrent Unit network. (Efficient RNN)
9. **[049] Attention Weights**: The relevance scores assigned to different parts of the input sequence in Transformers. (Self-Attention)
10. **[050] Ensemble Voting Score**: The aggregated prediction from multiple diverse models. (Stacking/Bagging)

## Phase 6: Options & Volatility

1. **[051] Implied Volatility (IV)**: The market's forecast of a likely movement in a security's price. (Black-Scholes Inverse)
2. **[052] GARCH Variance**: Conditional variance modeled as a function of past squared errors and past variances. (Heteroskedasticity)
3. **[053] The Greeks**: Delta, Gamma, Theta, Vega, Rho. (Sensitivities)
4. **[054] VIX Term Structure**: The curve of VIX futures prices across different maturities. (Contango/Backwardation)
5. **[055] Variance Risk Premium**: The difference between implied variance and realized variance. (Insurance Selling)
6. **[056] Effective Spread**: A measure of the cost of a round-trip trade. (Liquidity Cost)
7. **[057] Markov Transition Matrix**: Probability of moving from one state to another. (Regime Switching)
8. **[058] Hawkes Branching Ratio**: Key parameter in Hawkes processes measuring the degree of self-excitation. (Cluster Intensity)
9. **[059] RL Q-Value**: The expected future reward for taking a specific action in a specific state. (Bellman Equation)
10. **[060] Genetic Fitness Score**: The objective function value representing how well a strategy performed. (Evolutionary)

## Phase 7: Macroeconomics

1. **[061] Yield Curve Slope**: The difference between long-term and short-term interest rates. (10Y - 2Y)
2. **[062] PPP Fair Value**: The theoretical exchange rate where a basket of goods costs the same in two countries. (Big Mac)
3. **[063] Forward Rate Bias**: The tendency for the forward rate to be a biased predictor of the future spot rate. (Carry Trade)
4. **[064] Taylor Rule Rate**: A guideline for how central banks should alter interest rates. (Inflation/Output Gap)
5. **[065] GDP Nowcast**: A method for predicting the present, the very near future, and the very recent past of GDP.
6. **[066] Breakeven Inflation Rate**: The difference in yield between a nominal bond and an inflation-linked bond (TIPS).
7. **[067] Credit Spread**: The difference in yield between different securities due to different credit quality. (HY - IG)
8. **[068] MEV Profitability**: The potential profit available to miners/validators from reordering transactions. (Front-running)
9. **[069] Concentrated Liquidity**: The depth of liquidity provided within a specific price range in AMMs. (Uniswap V3)
10. **[070] Cross-Chain Latency**: The time delay for a message/asset to propagate between blockchains. (Arbitrage Window)

## Phase 8: Crypto & DeFi

1. **[071] Funding Rate**: Periodic payments to traders that are long or short based on the difference between perp and spot prices.
2. **[072] Hash Ribbon**: Indicator based on Bitcoin's hash rate to identify miner capitulation.
3. **[073] NVT Ratio**: Network Value to Transactions Ratio, similar to P/E ratio for crypto.
4. **[074] MVRV Z-Score**: Ratio of Market Value to Realized Value. (On-Chain Valuation)
5. **[075] Peg Deviation**: The percentage difference between a stablecoin's price and its pegged asset.
6. **[076] Reconstruction Error**: The difference between the input and output of an Autoencoder. (Anomaly Detection)
7. **[077] GAN Discriminator Output**: The probability that a given data point is real vs generated. (Synthetic Data)
8. **[078] Transfer Learning Weights**: Pre-trained model parameters adapted for a new task. (Feature Extraction)
9. **[079] LOB Heatmap**: Visual representation of the limit order book depth over time. (Resting Liquidity)
10. **[080] Queue Position**: Estimated position of an order within a price level queue. (FIFO)

## Phase 9: Portfolio Construction

1. **[081] HRP Clusters**: Groups of assets identified by Hierarchical Risk Parity. (Dendrogram)
2. **[082] Black-Litterman Posterior**: The adjusted expected returns combining market equilibrium and investor views.
3. **[083] CLA Turning Points**: The specific weights where the set of active assets changes on the Efficient Frontier.
4. **[084] Minimum Torsion Factors**: Uncorrelated risk factors that are as close as possible to the original assets.
5. **[085] Relative Entropy (KL Divergence)**: Measure of information gain or distance between distributions. (View Processing)
6. **[086] Convexity Payoff**: The non-linear relationship between an option's price and valid underlying price changes. (Gamma)
7. **[087] Inverse Volatility Target**: Weighting assets inversely proportional to their volatility. (Risk Parity)
8. **[088] Correlation Dispersion**: The spread between index correlation and constituent correlation. (Implied Correlation)
9. **[089] VIX Trend**: The directional movement of the volatility index. (Crisis Alpha)
10. **[090] Liquidity Probability**: The likelihood of finding sufficient liquidity at a specific price level. (Market Depth)

## Phase 10: Future Tech

1. **[091] HDD/CDD**: Heating/Cooling Degree Days, quantifying energy demand based on temperature.
2. **[092] Crack Spread**: The differential between the price of crude oil and petroleum products. (Refining Margin)
3. **[093] Implied Probability (Odds)**: The probability of an event derived from betting odds. ($1/Odds$)
4. **[094] Prediction Market Price**: The price of a binary contract representing the crowd's belief in an outcome.
5. **[095] NFT Rarity Score**: A metric quantifying how rare an NFT's traits are within its collection. (TF-IDF)
6. **[096] QAOA Energy**: The expectation value of the Hamiltonian in Quantum Approximate Optimization. (Cost Function)
7. **[097] SNN Spike Timing**: The precise timing of neuronal spikes in a Spiking Neural Network. (Temporal Coding)
8. **[098] Federated Gradients**: The model updates computed locally and sent to the central server in Federated Learning.
9. **[099] Causal Effect (Do-Calculus)**: The change in $Y$ resulting from an intervention on $X$. ($P(Y|do(X))$)
10. **[100] GOLIATH Meta-Weights**: The dynamic allocation weights assigned to each sub-strategy by the master system.

## Phase 11: Advanced Moving Averages & Adaptive Filters

1. **[101] Kaufman Adaptive MA (KAMA)**: Adjusts speed based on Efficiency Ratio — fast in trends, slow in chop. ($SC = (ER \times (fast - slow) + slow)^2$)
2. **[102] Hull Moving Average (HMA)**: Reduces lag using weighted MAs and square root period. ($WMA(2 \times WMA(n/2) - WMA(n), \sqrt{n})$)
3. **[103] Jurik Moving Average (JMA)**: Proprietary adaptive filter with minimal lag and ultra-smooth output. (Phase/Power)
4. **[104] ALMA (Arnaud Legoux MA)**: Gaussian-weighted MA applied from the center of the window. (Offset/Sigma)
5. **[105] T3 (Tillson Moving Average)**: Six-stage EMA with volume factor for adaptive smoothing. ($T3 = c_1 \times e_6 + c_2 \times e_5 + ...$)
6. **[106] ZLEMA (Zero Lag EMA)**: Shifts input data forward to compensate for EMA lag. ($ZLEMA = EMA(2P - P_{lag})$)
7. **[107] McGinley Dynamic Line**: Self-adjusting MA that tracks the market better during fast moves. (Auto-Adaptation)
8. **[108] Vortex Indicator**: Measures positive and negative trend movement using True Range. (VI+ / VI-)
9. **[109] Aroon Oscillator**: Measures time since the last high/low to detect trend aging. (Dawn's Early Light)
10. **[110] Choppiness Index**: Fractal dimension-based filter that measures market chaos vs order. ($100 \times \log(\sum TR / Range) / \log(N)$)

## Phase 12: Momentum & Oscillators — Advanced

1. **[111] Chande Momentum Oscillator (CMO)**: Unsmoothed momentum ratio measuring pure directional force. ($\frac{S_{up} - S_{down}}{S_{up} + S_{down}} \times 100$)
2. **[112] Detrended Price Oscillator (DPO)**: Removes trend to isolate underlying price cycles. ($P_t - SMA_{t-N/2-1}$)
3. **[113] TRIX**: Triple exponential smoothing rate of change — the smoothest oscillator. ($ROC(EMA(EMA(EMA(P))))$)
4. **[114] Mass Index**: Detects trend reversals via the "reversal bulge" pattern in range expansion. (Threshold 27/26.5)
5. **[115] Elder Force Index (EFI)**: Quantifies the force behind price moves using volume × price change. ($V \times \Delta P$)
6. **[116] Accumulation/Distribution Line (ADL)**: Cumulative volume-weighted close location tracker. ($CLV \times V$ cumsum)
7. **[117] Chaikin Money Flow (CMF)**: Bounded oscillator measuring normalized money flow over a window. ($\sum(CLV \times V) / \sum V$)
8. **[118] Rate of Change (ROC)**: The fundamental momentum measure — percentage price change over N periods. ($\frac{P_t - P_{t-N}}{P_{t-N}} \times 100$)
9. **[119] Coppock Curve**: Long-term bottom finder based on the "bereavement period" of markets. ($WMA(ROC_{14} + ROC_{11}, 10)$)
10. **[120] Ultimate Oscillator (UO)**: Multi-period consensus oscillator combining 3 buying pressure timeframes. (7/14/28 weighted)

## Phase 13: Composite & Specialized Indicators

1. **[121] KST (Know Sure Thing)**: Four-velocity momentum composite weighting multiple ROC periods. ($\sum w_i \times SMA(ROC_i)$)
2. **[122] PPO (Percentage Price Oscillator)**: Normalized MACD for cross-instrument comparison. ($\frac{EMA_{12} - EMA_{26}}{EMA_{26}} \times 100$)
3. **[123] TSI (True Strength Index)**: Double-smoothed momentum with superior signal-to-noise ratio. ($\frac{DSM}{DSAM} \times 100$)
4. **[124] Ease of Movement (EMV)**: Measures how easily price moves relative to volume (effort vs result). ($DM / BoxRatio$)
5. **[125] VWMA (Volume Weighted Moving Average)**: Moving average weighted by volume — the gravity line. ($\sum P_i V_i / \sum V_i$)
6. **[126] Klinger Volume Oscillator (KVO)**: Volume Force oscillator using trend-sensitive cumulative movement. ($EMA(VF, 34) - EMA(VF, 55)$)
7. **[127] Chaikin Oscillator**: MACD applied to the A/D Line — measures acceleration of money flow. ($EMA(ADL, 3) - EMA(ADL, 10)$)
8. **[128] DEMA (Double Exponential MA)**: Lag-canceling MA using EMA minus EMA-of-EMA. ($2 \times EMA - EMA(EMA)$)
9. **[129] FRAMA (Fractal Adaptive MA)**: Adapts smoothing based on the fractal dimension of price. ($\alpha = e^{-4.6(D-1)}$)
10. **[130] Schaff Trend Cycle (STC)**: Hybrid oscillator applying double Stochastic to MACD output. (Near-binary 0-100)

## Phase 14: Ehlers & Advanced Oscillators

1. **[131] Connors RSI**: Composite of RSI, Up/Down Length, and ROC for mean reversion. (2-period)
2. **[132] Stochastic RSI**: Applies Stochastic to RSI values to define sensitivity. (Indicator of Indicator)
3. **[133] Ehlers Fisher Transform**: Transforms price data to a Gaussian normal distribution. (Turning Points)
4. **[134] Ehlers Instantaneous Trendline**: Removes dominant cycle to reveal the underlying trend. (Zero Lag)
5. **[135] Relative Vigor Index (RVI)**: Measure of conviction based on closing location within bar range. (Energy Meter)

## Phase 15: Bill Williams & Chaos Theory

1. **[136] Alligator Indicator**: Three smoothed moving averages (Jaw, Teeth, Lips) representing the balance line. (Sleeping/Feeding)
2. **[137] Gator Oscillator**: Histogram based on the Alligator lines difference, visualizing the phases of the trend. (Expand/Contract)
3. **[138] Awesome Oscillator (AO)**: Momentum indicator comparing 5-period and 34-period SMAs. (Market Momentum)
4. **[139] Accelerator Oscillator (AC)**: Measures acceleration/deceleration of the Awesome Oscillator. (Early Warning)
5. **[140] Market Facilitation Index (BW MFI)**: Evaluates the willingness of the market to move the price. (Volume/Price Action)

## Phase 16: Order Flow & Liquidity

1. **[141] Cumulative Volume Delta (CVD)**: The cumulative sum of buying volume minus selling volume. (Aggressive Flow)
2. **[142] Volume Profile (VPVR)**: Histogram of volume traded at specific price levels. (POC/VAH/VAL)
3. **[143] Open Interest (OI)**: The total number of outstanding contracts in the market. (Market Participation)
4. **[144] Delta Divergence**: Discrepancy between price direction and net buying/selling pressure. (Reversal Signal)
5. **[145] Footprint Imbalance**: Bid/Ask volume comparison at each price level within a bar. (Auction Exhaustion)

## Phase 17: Advanced Volatility & Risk

1. **[146] Ulcer Index**: Measure of downside risk in terms of depth and duration of drawdowns. (Stress Metric)
2. **[147] R-Squared (Trend Reliability)**: Statistical measure of how close data is to the fitted regression line. (Trend Quality)
3. **[148] Standard Error Bands**: Envelopes plotting standard error around a linear regression line. (Statistical Extremes)
4. **[149] Historical Volatility Percentile (HVP)**: Compares current volatility to its historical distribution. (Cheap/Expensive Gamma)
5. **[150] Sortino Ratio (Dynamic)**: Rolling measure of risk-adjusted return penalizing only downside volatility. (Bad Volatility)
