# 00 - The "Grand Grimoire" of Trading Strategies: Master Index

**Edition:** University Compendium (50 Volumes)
**Date:** 2026-02-18
**Author:** Antigravity (Senior Quantitative Researcher)
**Target:** 4000+ Words per Volume (Total > 200,000 Words)

---

# Introduction

This index serves as the central taxonomy for the GOLIATH Strategy Encyclopedia. Each entry below corresponds to a dedicated monograph file located in `/home/a-cupsa/Desktop/BOT_TRADING/strategies/`. These documents provide exhaustive theoretical, mathematical, and historical analysis of the strategy, along with Python implementation guides.

# Volume I: Trend Following & Momentum (The "Beta" Hunters)

1. **[01_SMA_Golden_Cross.md](./01_SMA_Golden_Cross.md)**: The foundational duel of the 50-day and 200-day Simple Moving Averages.
2. **[02_Triple_SMA_Ribbon.md](./02_Triple_SMA_Ribbon.md)**: Using 3+ MAs to filter noise and detect early trend inception.
3. **[03_EMA_Crossover.md](./03_EMA_Crossover.md)**: Exponential weighting to solve the lag problem of SMAs.
4. **[04_Donchian_Breakout_Turtle.md](./04_Donchian_Breakout_Turtle.md)**: The Richard Dennis "Turtle" rules for N-day High/Low breakouts.
5. **[05_Bollinger_Squeeze_Vol_Breakout.md](./05_Bollinger_Squeeze_Vol_Breakout.md)**: Exploiting low-volatility regimes that precede explosive trends.
6. **[06_MACD_Histogram_Trend.md](./06_MACD_Histogram_Trend.md)**: Trading the derivative of the trend (Momentum).
7. **[07_Parabolic_SAR_Trailing.md](./07_Parabolic_SAR_Trailing.md)**: Acceleration factors and trailing stops for robust trend riding.
8. **[08_Ichimoku_Cloud_Kumo.md](./08_Ichimoku_Cloud_Kumo.md)**: The comprehensive Japanese "equilibrium" system.
9. **[09_ADX_DMI_Trend_Strength.md](./09_ADX_DMI_Trend_Strength.md)**: Filtering out "choppy" markets using the Average Directional Index.
10. **[10_Time_Series_Momentum.md](./10_Time_Series_Momentum.md)**: The academic (Moskowitz) framework for cross-asset momentum.

# Volume II: Mean Reversion & Statistical Arbitrage (The "Alpha" Miners)

11. **[11_RSI_2_Period_Connors.md](./11_RSI_2_Period_Connors.md)**: Larry Connors' hyper-reactive mean reversion system.
2. **[12_Bollinger_Band_Mean_Rev.md](./12_Bollinger_Band_Mean_Rev.md)**: Trading the "Bounce" off 2-sigma deviations.
3. **[13_Stochastic_Oscillator_Divergence.md](./13_Stochastic_Oscillator_Divergence.md)**: Identifying exhaustion via %K and %D crossovers.
4. **[14_Williams_R_Overbought.md](./14_Williams_R_Overbought.md)**: Larry Williams' range location metric.
5. **[15_CCI_Commodity_Channel.md](./15_CCI_Commodity_Channel.md)**: Cyclical analysis of deviation from the statistical mean.
6. **[16_Pairs_Trading_Cointegration.md](./16_Pairs_Trading_Cointegration.md)**: The classic Long/Short Market Neutral strategy.
7. **[17_Triangular_Arbitrage_Forex.md](./17_Triangular_Arbitrage_Forex.md)**: Exploiting rate discrepancies in FX triads (EUR-USD-GBP).
8. **[18_VWAP_Mean_Reversion.md](./18_VWAP_Mean_Reversion.md)**: Trading deviations from the intraday Volume Weighted Average Price.
9. **[19_Keltner_Channel_Reversion.md](./19_Keltner_Channel_Reversion.md)**: Using ATR-based bands instead of Standard Deviation.
10. **[20_Pivot_Points_Floor_Trader.md](./20_Pivot_Points_Floor_Trader.md)**: Classical support/resistance levels derived from High/Low/Close.

# Volume III: Volatility & Options Strategies (The "Convexity" Traders)

21. **[21_Long_Straddle_Gamma.md](./21_Long_Straddle_Gamma.md)**: Betting on pure volatility expansion (Long Gamma).
2. **[22_Short_Iron_Condor.md](./22_Short_Iron_Condor.md)**: Betting on price stagnation (Short Vega/Theta).
3. **[23_Gamma_Scalping_Delta_Neutral.md](./23_Gamma_Scalping_Delta_Neutral.md)**: Dynamic hedging to capture realized volatility.
4. **[24_VIX_Term_Structure_Arb.md](./24_VIX_Term_Structure_Arb.md)**: Harvesting the roll yield between VIX futures months.
5. **[25_Dispersion_Trading.md](./25_Dispersion_Trading.md)**: Shorting Index volatility vs Long Constituent volatility.
6. **[26_Calendar_Spreads.md](./26_Calendar_Spreads.md)**: Exploiting different rates of Theta decay across expirations.
7. **[27_Volatility_Risk_Premium.md](./27_Volatility_Risk_Premium.md)**: Systematically selling insurance (Options) to harvest VRP.
8. **[28_Put_Call_Parity_Arb.md](./28_Put_Call_Parity_Arb.md)**: Exploiting violations of synthetic equivalence ($C - P = S - K e^{-rt}$).

# Volume IV: HFT & Market Microstructure (The "Mechanics")

29. **[29_Market_Making_Stoikov.md](./29_Market_Making_Stoikov.md)**: The Stoikov-Avellaneda inventory management model.
2. **[30_Order_Book_Imbalance_OBI.md](./30_Order_Book_Imbalance_OBI.md)**: Predicting ticks based on L2/L3 liquidity skew.
3. **[31_Latency_Arbitrage.md](./31_Latency_Arbitrage.md)**: Exploiting SIP vs Direct Feed latency differentials.
4. **[32_Rebate_Capture_Maker_Taker.md](./32_Rebate_Capture_Maker_Taker.md)**: Passive trading strategies focused purely on exchange fee rebates.
5. **[33_Ping_Pong_Laddering.md](./33_Ping_Pong_Laddering.md)**: Scalping active ranges in sideways order books.
6. **[34_Iceberg_Detection.md](./34_Iceberg_Detection.md)**: Algorithms to detect hidden institutional orders.
7. **[35_VWAP_Execution_Algo.md](./35_VWAP_Execution_Algo.md)**: Optimal execution to match the Volume Weighted Average Price.

# Volume V: Fundamental & Macro Strategies (The "Big Picture")

36. **[36_Carry_Trade_FX.md](./36_Carry_Trade_FX.md)**: Borrowing Low-Yield / Buying High-Yield currencies.
2. **[37_Yield_Curve_Inversion.md](./37_Yield_Curve_Inversion.md)**: Predicting recessions via the 2y/10y Treasury spread.
3. **[38_Purchasing_Power_Parity.md](./38_Purchasing_Power_Parity.md)**: Long-term Forex valuation based on basket of goods.
4. **[39_Merger_Arbitrage_Risk_Arb.md](./39_Merger_Arbitrage_Risk_Arb.md)**: Betting on the completion of announced corporate acquisitions.
5. **[40_Earnings_Surprise_PEAD.md](./40_Earnings_Surprise_PEAD.md)**: Post-Earnings Announcement Drift strategies.

# Volume VI: Crypto Native Strategies (The "Wild West")

41. **[41_Funding_Rate_Arbitrage.md](./41_Funding_Rate_Arbitrage.md)**: Delta-neutral positioning to harvest Perp Swap funding rates.
2. **[42_Kimchi_Premium_Arb.md](./42_Kimchi_Premium_Arb.md)**: Exploiting capital control inefficiencies between Korean and Global exchanges.
3. **[43_MEV_Sandwich_Attacks.md](./43_MEV_Sandwich_Attacks.md)**: Front-running and Back-running transactions in the Mempool.
4. **[44_DeFi_Liquidation_Sniping.md](./44_DeFi_Liquidation_Sniping.md)**: Automating the purchase of distressed assets on lending protocols.
5. **[45_Basis_Cash_and_Carry.md](./45_Basis_Cash_and_Carry.md)**: Arbitraging the premium between Spot and Futures contracts.

# Volume VII: Machine Learning & AI (The "Future")

46. **[46_LSTM_Price_Forecasting.md](./46_LSTM_Price_Forecasting.md)**: Using Long Short-Term Memory networks for time-series prediction.
2. **[47_Reinforcement_Learning_PPO.md](./47_Reinforcement_Learning_PPO.md)**: Training Agents via Proximal Policy Optimization.
3. **[48_Sentiment_Analysis_NLP.md](./48_Sentiment_Analysis_NLP.md)**: Using BERT/FinBERT to trade on news flow and social sentiment.
4. **[49_Genetic_Algorithms.md](./49_Genetic_Algorithms.md)**: Evolving trading rules through mutation and crossover.
5. **[50_HMM_Regime_Switching.md](./50_HMM_Regime_Switching.md)**: Using Hidden Markov Models to detect volatility regimes.
