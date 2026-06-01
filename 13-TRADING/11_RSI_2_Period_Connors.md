# 11 - RSI, Connors RSI (CRSI) & Money Flow Index (MFI): The Momentum Twins

**Volume:** 11 of 50
**Strategy Type:** Mean Reversion / Short Term Momentum
**Risk Profile:** High Win Rate / High Frequency
**Mathematical Basis:** Relative Strength (Price & Volume), Composite Oscillator (CRSI)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [RSI: The Price Oscillator](#2-rsi-the-price-oscillator)
    * 2.1. Formula & Wilder's Smoothing
    * 2.2. The Connors 2-Period Strategy (RSI < 10)
3. [Connors RSI (CRSI): The Triple-Engine Momentum](#3-connors-rsi-crsi-the-triple-engine-momentum)
    * 3.1. Historical Context: Connors Research
    * 3.2. The Three Components
    * 3.3. Mathematical Foundations
    * 3.4. Signal Generation and Interpretation
    * 3.5. CRSI in XAU/USD Gold Markets
4. [MFI: The Volume Oscillator](#4-mfi-the-volume-oscillator)
    * 4.1. "The RSI of Volume"
    * 4.2. Formula: Money Ratio & Typical Price
    * 4.3. Why Volume Matters (The Fuel)
5. [Trading Signals & Divergences](#5-trading-signals--divergences)
    * 5.1. RSI Divergence (Price Exhaustion)
    * 5.2. MFI Divergence (Volume Exhaustion)
    * 5.3. The "Volume Vacuum" Strategy
6. [Strategies](#6-strategies)
    * 6.1. Connors RSI(2) Scalping (The Dip Buyer)
    * 6.2. MFI Structural Reversals (The Trend Ender)
    * 6.3. "The Pullback Sniper" — CRSI-Driven Mean Reversion for XAU/USD
7. [Microstructure & HFT Applications](#7-microstructure--hft-applications)
    * 7.1. Ultra-Short-Term Mean Reversion
    * 7.2. Regime Detection via CRSI Distribution
    * 7.3. Execution Timing with CRSI
8. [Implementation: Production Grade](#8-implementation-production-grade)
    * 8.1. Python (RSI & MFI)
    * 8.2. Python (Connors RSI — Vectorized)
    * 8.3. Rust (Streaming RSI/MFI)
    * 8.4. Rust (Streaming Connors RSI)
9. [Risk Management](#9-risk-management)
10. [Conclusion](#10-conclusion)

---

# 1. Executive Summary

This volume covers three key oscillating indicators in technical analysis:

1. **Relative Strength Index (RSI):** Measures the speed of **Price**.
2. **Connors RSI (CRSI):** A composite 3-component oscillator purpose-built for **Mean Reversion** timing.
3. **Money Flow Index (MFI):** Measures the flow of **Capital** (Price $\times$ Volume).

**RSI** answers: "Did price move too far?"
**CRSI** answers: "Is price exhausted, is the streak exhausted, AND is the magnitude historically extreme?"
**MFI** answers: "Is there real money behind the move?"

Combining them filters out "fake" price moves (RSI Spikes with no Volume), identifies precise pullback entries (CRSI extremes), and spots "hidden" accumulation (MFI rising while Price is flat).

---

# 2. RSI: The Price Oscillator

See previous sections for the detailed breakdown of J. Welles Wilder's RSI.
**Key Takeaway:** The 2-Period RSI (Connors) is the premier tool for identifying short-term panic selling (Mean Reversion).

---

# 3. Connors RSI (CRSI): The Triple-Engine Momentum

***"One RSI can lie to you. Three RSIs, calibrated to measure different things, tell the truth."*** — *Larry Connors, Connors Research*

## 3.1. Historical Context: Connors Research

**Larry Connors** and **Cesar Alvarez** at Connors Research developed CRSI as an evolution of the RSI(2) approach. Their 2008 book *Short Term Trading Strategies That Work* showed that RSI(14) was poorly suited for short-term mean reversion — its lookback was too long, and 30/70 thresholds generated entries that were too early and too infrequent. RSI(2) solved the timing problem but introduced noise. CRSI, formally published in 2012, added two more uncorrelated components to reduce noise by approximately $1/\sqrt{3}$ while preserving sensitivity.

## 3.2. The Three Components

**Connors RSI (CRSI)** is a composite momentum oscillator built from three independently computed signals averaged into a single 0-100 bounded reading:

1. **RSI(3)** — A 3-period RSI on closing price. Hyper-sensitive; captures immediate overbought/oversold exhaustion.
2. **RSI(Streak, 2)** — A 2-period RSI applied to the *length* of the current consecutive up/down run. Measures behavioral exhaustion — how long the market has been running in one direction.
3. **PercentRank(ROC(1), 100)** — The percentile rank of today's 1-day Rate of Change over the last 100 bars. Contextualizes the magnitude of today's move relative to history.

**Key Insight:** The three components are largely uncorrelated — RSI(3) measures price level exhaustion, RSI(Streak,2) measures behavioral persistence exhaustion, PercentRank measures relative magnitude. Averaging three uncorrelated signals produces a smoother, more reliable oscillator without sacrificing responsiveness.

## 3.3. Mathematical Foundations

### Component 1: RSI(Close, 3)

Standard Wilder RSI with period 3:

$$\Delta_t = Close_t - Close_{t-1}$$

$$U_t = \max(\Delta_t, 0), \quad D_t = \max(-\Delta_t, 0)$$

Wilder smoothing ($\alpha = 1/3$):

$$\overline{U}_t = \frac{\overline{U}_{t-1} \times 2 + U_t}{3}, \quad \overline{D}_t = \frac{\overline{D}_{t-1} \times 2 + D_t}{3}$$

$$RSI3_t = 100 - \frac{100}{1 + \overline{U}_t / \overline{D}_t}$$

### Component 2: RSI(Streak, 2)

The streak $S_t$ is a signed integer representing consecutive closes in one direction:

$$S_t = \begin{cases} S_{t-1} + 1 & \text{if } Close_t > Close_{t-1} \\ S_{t-1} - 1 & \text{if } Close_t < Close_{t-1} \\ 0 & \text{if } Close_t = Close_{t-1} \end{cases}$$

Then apply RSI with period $N=2$ to the streak series $\{S_t\}$:

$$RSI\_Streak_t = 100 - \frac{100}{1 + RS^S_t}$$

### Component 3: PercentRank of ROC(1)

$$ROC(1)_t = \frac{Close_t - Close_{t-1}}{Close_{t-1}} \times 100$$

$$PercentRank_t = \frac{1}{100} \sum_{i=t-100}^{t-1} \mathbf{1}\left[ROC(1)_i < ROC(1)_t\right] \times 100$$

### The Final CRSI Formula

$$\boxed{CRSI_t = \frac{RSI(Close, 3)_t + RSI(Streak, 2)_t + PercentRank(ROC_1, 100)_t}{3}}$$

### Statistical Properties

If the three components have equal variance $\sigma^2$ and zero correlation:

$$\sigma_{CRSI} = \frac{\sigma}{\sqrt{3}} \approx 0.577 \cdot \sigma$$

In practice, moderate correlations ($\rho \approx 0.3$-$0.5$) reduce but don't eliminate this noise reduction benefit. The key is that errors and noise terms from three different measurement phenomena are distinct.

## 3.4. Signal Generation and Interpretation

### Overbought/Oversold Levels

| Signal Strength | Oversold (Buy Zone) | Overbought (Sell Zone) |
|-----------------|--------------------|-----------------------|
| Aggressive      | CRSI < 10          | CRSI > 90              |
| Conservative    | CRSI < 5           | CRSI > 95              |
| Moderate        | CRSI < 20          | CRSI > 80              |

### The Critical Trend Filter

CRSI is **not** a standalone system. It is a timing tool within a trend framework:

* **Longs only:** CRSI < 10 **AND** Close > 200-period SMA
* **Shorts only:** CRSI > 90 **AND** Close < 200-period SMA

Without the trend filter, CRSI fades badly — buying into waterfall declines or selling into parabolic rallies.

### S&P 500 Pullback Strategy (Connors' Original)

1. **Universe:** SPY, QQQ, or large-cap S&P 500 constituents.
2. **Condition:** Close > 200-day SMA (uptrend confirmed).
3. **Entry:** Buy on close when CRSI < 10.
4. **Exit:** Close when CRSI > 70 OR RSI(3) > 70.
5. **Stop:** None (rely on position sizing).

Connors reported win rates of 68-74% in US equities over 1995-2011.

### ETF Rotation Application

1. Rank all sector ETFs by CRSI value.
2. Buy the 2-3 ETFs with the lowest CRSI values (most oversold), provided they are above their 200 SMA.
3. Sell any ETF when its CRSI rises above 70.
4. Rebalance weekly.

## 3.5. CRSI in XAU/USD Gold Markets

Gold (XAU/USD) exhibits strong mean-reversion tendencies within its trend phases:

* **Gold is more volatile:** Use slightly wider thresholds (CRSI < 15 for oversold, CRSI > 85 for overbought) on daily data.
* **Gold has stronger streaks:** Geopolitical or macro-driven moves can push streak values to ±7 or higher. RSI(Streak,2) provides earlier exhaustion signals.
* **Hourly data preferred:** GOLIATH uses hourly XAU/USD data (~11,292 bars). On hourly data, CRSI cycles between extremes frequently, enabling intraday mean-reversion entries.
* **Session awareness:** Gold volatility clusters around London open (08:00 GMT) and New York open (13:30 GMT). CRSI extremes at session opens carry higher mean-reversion probability.

---

# 4. MFI: The Volume Oscillator

## 4.1. "The RSI of Volume"

Developed by Gene Quong and Avrum Soudack, MFI is mathematically identical to RSI, but instead of using *Price Change*, it uses *Money Flow*.

## 4.2. Formula

1. **Typical Price (TP):** $(High + Low + Close) / 3$
2. **Raw Money Flow (RMF):** $TP \times Volume$
3. **Positive Flow:** RMF if $TP > PrevTP$.
4. **Negative Flow:** RMF if $TP < PrevTP$.
5. **Money Ratio:** $\sum(+Flow) / \sum(-Flow)$
6. **MFI:** $100 - (100 / (1 + MoneyRatio))$

## 4.3. Why Volume Matters

Price can be manipulated by a single trade ("Painting the Tape"). Volume cannot be faked without spending real money.

* **RSI** is the **Car** (Speed).
* **MFI** is the **Fuel** (Gas Tank).
If the Car is speeding up (RSI High) but the Fuel is empty (MFI Low), the car will stop.

---

# 5. Trading Signals & Divergences

## 5.1. RSI Divergence

Price makes Higher High, RSI makes Lower High. (Standard Bearish Divergence).

## 5.2. MFI Divergence (The Killer Signal)

MFI Divergence is often more powerful than RSI Divergence because it confirms *smart money* is leaving.

* **Scenario:** Bitcoin hits \$100k (New All-Time High). RSI is 70 (Overbought). But **MFI is dropping** (Volume is drying up on the buy side).
* **Result:** The top is in. The whales are selling into the retail buying frenzy.

## 5.3. The "Volume Vacuum"

MFI < 10 (Extreme Oversold).
This means *all* recent volume has been on the sell side. Sellers have purged their inventory. There are no sellers left. Price can float up effortlessly on low volume because the "ask" side of the order book is empty.

---

# 6. Strategies

## 6.1. Connors RSI(2) Scalping

* **Timeframe:** Daily.
* **Setup:** Price > SMA(200).
* **Trigger:** RSI(2) < 10.
* **Exit:** Price > SMA(5).
* **Philosophy:** Buy the panic in a bull market.

## 6.2. MFI Structural Reversals

* **Timeframe:** Weekly/Daily.
* **Setup:** Market Crash.
* **Trigger:** MFI < 20 (Oversold) AND RSI < 30.
* **Confirmation:** MFI crosses back above 20.
* **Philosophy:** This catches the "V-Bottom" where volume finally turns positive after a capitulation event.

## 6.3. "The Pullback Sniper" — CRSI-Driven Mean Reversion for XAU/USD

### Entry Rules — Long

All conditions must be simultaneously true:

1. **Trend filter:** $Close > SMA(200)$ on the hourly chart.
2. **CRSI oversold:** $CRSI < 10$.
3. **Streak confirmation:** Raw streak value $S_t \leq -2$ (at least 2 consecutive down closes).
4. **Volatility filter:** $ATR(14) > ATR(14)_{SMA(50)}$. Avoid low-volatility consolidations.
5. **Session filter:** Bar closing in London (07:00-16:00 GMT) or New York (13:30-21:00 GMT) session.

**Entry:** Market order at close of trigger bar, or limit order at next bar's open.

### Entry Rules — Short

1. **Trend filter:** $Close < SMA(200)$ on the hourly chart.
2. **CRSI overbought:** $CRSI > 90$.
3. **Streak confirmation:** Raw streak value $S_t \geq +2$.
4. **Volatility filter:** $ATR(14) > ATR(14)_{SMA(50)}$.
5. **Session filter:** London or New York session.

### Exit Rules and Risk Management

**Target (TP):** $TP = Entry \pm 1.5\%$ — Reward-to-risk ratio = $1.5 / 0.8 = 1.875$.

**Stop Loss (SL):** $SL = Entry \mp 0.8\%$

**Time stop:** If neither TP nor SL hit within 20 bars (20 hours), close at market.

**CRSI-based exit (optional):** Close when $CRSI > 70$ (longs) or $CRSI < 30$ (shorts).

### Position Sizing (Kelly Criterion)

$$f^* = \frac{p \cdot b - (1-p)}{b}$$

With $p = 0.65, b = 1.875$: $f^* \approx 0.463$. Apply half-Kelly: risk $0.23 \times$ available capital. GOLIATH caps at 2% of total account.

### CRSI + XAUTransformer Integration

* **Confirmation:** Only take CRSI signals where XAUTransformer confidence > 0.6 in the same direction.
* **Conflict:** If CRSI says oversold but XAUTransformer predicts SELL with confidence > 0.75, skip the long.
* **Sizing boost:** If both agree with high confidence, increase position size by 1.5x (still capped at 2% risk).

### Backtesting Expectations

| Metric               | Target (XAU/USD Hourly) |
|----------------------|------------------------|
| Win Rate (Long)      | 62-68%                 |
| Win Rate (Short)     | 58-64%                 |
| Average Hold Time    | 8-14 hours             |
| Trades per Month     | 15-25                  |
| Expected Sharpe      | 1.4-1.8                |
| Max Drawdown Target  | < 12%                  |

---

# 7. Microstructure & HFT Applications

## 7.1. Ultra-Short-Term Mean Reversion

At sub-hourly frequencies (1-min, 5-min bars), CRSI parameters need adjustment:

* **RSI(3)** on 1-min data: Keep period at 3, but recognize susceptibility to quote stuffing and spread artifacts.
* **Streak on 2:** Streaks of ±3 to ±5 are common on 1-min; streaks of ±8 to ±10 represent genuine exhaustion.
* **PercentRank:** Reduce lookback from 100 to 20-30 bars for intraday volatility regime.

At HFT frequencies, CRSI becomes a **regime classifier**: CRSI < 10 on 1-min signals a "trapped sell" regime where reversion is statistically likely within 5-15 minutes.

## 7.2. Regime Detection via CRSI Distribution

Monitor the **rolling frequency of CRSI extremes** over 200 bars:

$$ExtFreq_{200} = \frac{\text{Bars where } CRSI < 10 \text{ or } CRSI > 90}{200}$$

* $ExtFreq_{200} > 0.08$: Choppy regime — mean reversion strategies favored.
* $ExtFreq_{200} < 0.04$: Trending regime — trend-following favored, CRSI used only for pullback timing.

## 7.3. Execution Timing with CRSI

For GOLIATH's execution engine (Go gateway + Rust risk):

1. **Strategic signal:** Direction from XAUTransformer ML model.
2. **Tactical timing:** If ML says BUY and CRSI < 15 on the closing hourly bar, execute at bar close rather than immediately.
3. **Entry improvement:** CRSI confirmation typically improves average entry by 0.1-0.3% on XAU/USD hourly bars.

**Order splitting:** When CRSI is 5-10 (extremely oversold), split 60% at current signal and 40% scaled over next 2-3 bars. If CRSI drops further (< 5), add the remaining 40%.

---

# 8. Implementation: Production Grade

## 8.1. Python (RSI & MFI)

```python
import pandas as pd
import numpy as np

class MomentumStrategy:
    def __init__(self, rsi_period=14, mfi_period=14):
        self.rsi_period = rsi_period
        self.mfi_period = mfi_period

    def calculate_rsi(self, series, period):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_mfi(self, df, period):
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        rmf = tp * df['Volume']
        
        pos_flow = pd.Series(0.0, index=df.index)
        neg_flow = pd.Series(0.0, index=df.index)
        
        pos_flow[tp > tp.shift(1)] = rmf[tp > tp.shift(1)]
        neg_flow[tp < tp.shift(1)] = rmf[tp < tp.shift(1)]
        
        mrf = pos_flow.rolling(period).sum() / neg_flow.rolling(period).sum()
        return 100 - (100 / (1 + mrf))
```

## 8.2. Python (Connors RSI — Vectorized)

```python
import pandas as pd
import numpy as np


def wilder_rsi(series: pd.Series, period: int) -> pd.Series:
    """Compute Wilder RSI for a given series and period."""
    delta = series.diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    alpha = 1.0 / period
    avg_up = up.ewm(alpha=alpha, adjust=False).mean()
    avg_down = down.ewm(alpha=alpha, adjust=False).mean()
    rs = avg_up / avg_down.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def compute_streak(close: pd.Series) -> pd.Series:
    """Consecutive up/down streak. Positive = up, Negative = down."""
    direction = np.sign(close.diff())
    streak_arr = np.zeros(len(close))
    for i in range(1, len(close)):
        d = direction.iloc[i]
        if d == 1:
            streak_arr[i] = max(streak_arr[i - 1], 0) + 1
        elif d == -1:
            streak_arr[i] = min(streak_arr[i - 1], 0) - 1
        else:
            streak_arr[i] = 0
    return pd.Series(streak_arr, index=close.index)


def percent_rank(series: pd.Series, lookback: int = 100) -> pd.Series:
    """Percentile rank of current value vs past `lookback` values. Returns 0-100."""
    def _rank(x):
        if len(x) < 2:
            return 50.0
        current = x.iloc[-1]
        past = x.iloc[:-1]
        return (past < current).sum() / len(past) * 100.0
    return series.rolling(window=lookback + 1, min_periods=2).apply(_rank, raw=False)


def connors_rsi(close: pd.Series, rsi_period=3, streak_period=2, rank_period=100) -> pd.DataFrame:
    """Compute Connors RSI (CRSI). Returns DataFrame with rsi3, rsi_streak, pct_rank, crsi."""
    rsi3 = wilder_rsi(close, rsi_period)
    streak = compute_streak(close)
    rsi_streak = wilder_rsi(streak, streak_period)
    roc1 = close.pct_change() * 100.0
    pct_rank = percent_rank(roc1, rank_period)
    crsi = (rsi3 + rsi_streak + pct_rank) / 3.0
    return pd.DataFrame({"rsi3": rsi3, "rsi_streak": rsi_streak, "pct_rank": pct_rank, "crsi": crsi})
```

## 8.3. Rust (Streaming RSI/MFI)

```rust
use std::collections::VecDeque;

pub struct MomentumOscillators {
    rsi_period: usize,
    mfi_period: usize,
    
    // RSI State
    rsi_history: VecDeque<f64>,
    
    // MFI State
    mfi_history: VecDeque<(f64, f64)>, // (TP, RMF)
}

impl MomentumOscillators {
    pub fn new(rsi_p: usize, mfi_p: usize) -> Self {
        Self {
            rsi_period: rsi_p,
            mfi_period: mfi_p,
            rsi_history: VecDeque::new(),
            mfi_history: VecDeque::new(),
        }
    }

    pub fn update(&mut self, price: f64, high: f64, low: f64, vol: f64) -> (Option<f64>, Option<f64>) {
        // RSI Calculation (Simplified Rolling Mean for streaming)
        self.rsi_history.push_back(price);
        if self.rsi_history.len() > self.rsi_period + 1 { self.rsi_history.pop_front(); }
        
        let rsi_val = if self.rsi_history.len() >= self.rsi_period + 1 {
            let mut gains = 0.0;
            let mut losses = 0.0;
            for i in 1..self.rsi_history.len() {
                let change = self.rsi_history[i] - self.rsi_history[i-1];
                if change > 0.0 { gains += change; } else { losses -= change; }
            }
            if losses == 0.0 { Some(100.0) } 
            else { Some(100.0 - (100.0 / (1.0 + (gains/losses)))) }
        } else { None };

        // MFI Calculation
        let tp = (high + low + price) / 3.0;
        let rmf = tp * vol;
        self.mfi_history.push_back((tp, rmf));
        if self.mfi_history.len() > self.mfi_period + 1 { self.mfi_history.pop_front(); }

        let mfi_val = if self.mfi_history.len() >= self.mfi_period + 1 {
            let mut pos = 0.0;
            let mut neg = 0.0;
            for i in 1..self.mfi_history.len() {
                let (curr_tp, curr_rmf) = self.mfi_history[i];
                let (prev_tp, _) = self.mfi_history[i-1];
                if curr_tp > prev_tp { pos += curr_rmf; }
                else if curr_tp < prev_tp { neg += curr_rmf; }
            }
            if neg == 0.0 { Some(100.0) }
            else { Some(100.0 - (100.0 / (1.0 + (pos/neg)))) }
        } else { None };

        (rsi_val, mfi_val)
    }
}
```

## 8.4. Rust (Streaming Connors RSI)

```rust
use std::collections::VecDeque;

pub struct WilderRsi {
    period: usize,
    avg_up: f64,
    avg_down: f64,
    prev_value: Option<f64>,
    count: usize,
    init_ups: Vec<f64>,
    init_downs: Vec<f64>,
}

impl WilderRsi {
    pub fn new(period: usize) -> Self {
        Self { period, avg_up: 0.0, avg_down: 0.0, prev_value: None, count: 0,
               init_ups: Vec::with_capacity(period), init_downs: Vec::with_capacity(period) }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if let Some(prev) = self.prev_value {
            let delta = value - prev;
            let up = delta.max(0.0);
            let down = (-delta).max(0.0);
            if self.count < self.period {
                self.init_ups.push(up);
                self.init_downs.push(down);
                self.count += 1;
                if self.count == self.period {
                    self.avg_up = self.init_ups.iter().sum::<f64>() / self.period as f64;
                    self.avg_down = self.init_downs.iter().sum::<f64>() / self.period as f64;
                }
            } else {
                let n = self.period as f64;
                self.avg_up = (self.avg_up * (n - 1.0) + up) / n;
                self.avg_down = (self.avg_down * (n - 1.0) + down) / n;
            }
        }
        self.prev_value = Some(value);
        if self.count >= self.period {
            let rs = if self.avg_down.abs() < 1e-10 { f64::INFINITY } else { self.avg_up / self.avg_down };
            Some(100.0 - 100.0 / (1.0 + rs))
        } else { None }
    }
}

pub struct StreakTracker { prev_close: Option<f64>, current_streak: i32 }

impl StreakTracker {
    pub fn new() -> Self { Self { prev_close: None, current_streak: 0 } }
    pub fn update(&mut self, close: f64) -> f64 {
        if let Some(prev) = self.prev_close {
            if close > prev { self.current_streak = self.current_streak.max(0) + 1; }
            else if close < prev { self.current_streak = self.current_streak.min(0) - 1; }
            else { self.current_streak = 0; }
        }
        self.prev_close = Some(close);
        self.current_streak as f64
    }
}

pub struct PercentRankRoc { lookback: usize, roc_window: VecDeque<f64>, prev_close: Option<f64> }

impl PercentRankRoc {
    pub fn new(lookback: usize) -> Self {
        Self { lookback, roc_window: VecDeque::with_capacity(lookback + 1), prev_close: None }
    }
    pub fn update(&mut self, close: f64) -> Option<f64> {
        let roc = if let Some(prev) = self.prev_close {
            (close - prev) / prev * 100.0
        } else { self.prev_close = Some(close); return None; };
        self.prev_close = Some(close);
        self.roc_window.push_back(roc);
        if self.roc_window.len() > self.lookback + 1 { self.roc_window.pop_front(); }
        if self.roc_window.len() < 2 { return None; }
        let current_roc = *self.roc_window.back().unwrap();
        let n = self.roc_window.len() - 1;
        let below = self.roc_window.iter().rev().skip(1).filter(|&&v| v < current_roc).count();
        Some((below as f64 / n as f64) * 100.0)
    }
}

/// Full Connors RSI — streaming, zero-copy design
pub struct ConnorsRsi {
    rsi3: WilderRsi, streak_tracker: StreakTracker, streak_rsi: WilderRsi, pct_rank: PercentRankRoc,
}

impl ConnorsRsi {
    pub fn new() -> Self {
        Self { rsi3: WilderRsi::new(3), streak_tracker: StreakTracker::new(),
               streak_rsi: WilderRsi::new(2), pct_rank: PercentRankRoc::new(100) }
    }
    /// Feed one close price; returns (CRSI, rsi3, rsi_streak, pct_rank) or None
    pub fn update(&mut self, close: f64) -> Option<(f64, f64, f64, f64)> {
        let rsi3_val = self.rsi3.update(close);
        let streak_val = self.streak_tracker.update(close);
        let rsi_streak_val = self.streak_rsi.update(streak_val);
        let pct_rank_val = self.pct_rank.update(close);
        match (rsi3_val, rsi_streak_val, pct_rank_val) {
            (Some(r3), Some(rs), Some(pr)) => { let crsi = (r3 + rs + pr) / 3.0; Some((crsi, r3, rs, pr)) }
            _ => None,
        }
    }
}
```

---

# 9. Risk Management

* **Position sizing:** Half-Kelly with 2% account risk cap per trade.
* **Correlation risk:** CRSI and MFI signals can fire simultaneously — limit total exposure to 4% when multiple signals active.
* **Regime awareness:** In trending regimes ($ExtFreq_{200} < 0.04$), reduce CRSI mean-reversion position sizes by 50%.
* **Session risk:** Avoid entries during Asian session (thin liquidity, wider spreads on XAU/USD).
* **Drawdown circuit breaker:** If account drawdown exceeds 8%, reduce all position sizes by 50% until recovery above 5% drawdown.

---

# 10. Conclusion

RSI is the heartbeat of the market. MFI is the breath. CRSI is the precision stethoscope.
Using them together provides a complete picture of market health.

* **Connors RSI(2)** allows you to buy the fear (Price Panic).
* **Connors RSI (CRSI)** adds streak exhaustion and magnitude context for higher-precision entries.
* **MFI** allows you to sell the greed (Volume Exhaustion).

For GOLIATH, these signals are primary inputs for the "Mean Reversion Agent." CRSI's three-component architecture — price exhaustion, behavioral exhaustion, and magnitude context — reduces noise by averaging uncorrelated signals while preserving sensitivity. Combined with the XAUTransformer ML model for directional bias, CRSI provides the tactical entry timing that transforms a good directional call into an optimal trade execution.

| Property             | Value / Description                                                                 |
|----------------------|-------------------------------------------------------------------------------------|
| **Type**             | Composite oscillator (mean reversion / timing)                                      |
| **Components**       | RSI(Close,3) + RSI(Streak,2) + PercentRank(ROC1,100) / 3                           |
| **Default Params**   | RSI period = 3, Streak RSI period = 2, PercentRank lookback = 100                  |
| **Oversold Trigger** | CRSI < 10 (aggressive), CRSI < 5 (conservative)                                    |
| **Overbought**       | CRSI > 90 (aggressive), CRSI > 95 (conservative)                                   |
| **Best Conditions**  | Trending markets (with 200 SMA filter), intraday pullback timing                    |
| **Worst Conditions** | Sideways low-volatility chop, news-driven gap events, thin liquidity sessions       |
| **Lag**              | Very low — 3-bar RSI and 2-bar streak RSI respond within 1-2 bars                  |
| **GOLIATH Role**     | Short-term entry timing for XAU/USD pullback entries within XAUTransformer direction |
| **Author**           | Larry Connors & Cesar Alvarez, Connors Research (published 2012)                    |
