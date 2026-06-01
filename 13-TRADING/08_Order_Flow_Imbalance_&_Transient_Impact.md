# 08. Order Flow Imbalance & Transient Impact Modeling

**Abstract**
In high-frequency trading (HFT), price formation is driven by the arrival of aggressive orders and the subsequent depletion of liquidity. This document details the mathematical framework for modeling self-exciting order flow (Hawkes Processes), the temporary nature of market impact (Propagator Models), and liquidity estimation (Kyle's Lambda).

---

## 1. Hawkes Processes (Self-Exciting Point Processes)

Market events (trades, quotes) cluster in time. A large buy order often triggers further buy orders (momentum) or sell orders (mean reversion).

### 1.1 Univariate Hawkes Process
Let $N(t)$ be the counting process of events. The conditional intensity function $\lambda(t)$ is defined as:
$$ \lambda(t) = \mu + \int_{-\infty}^t \phi(t-u) dN(u) $$

Where:
*   $\mu > 0$: Base intensity (exogenous events like news).
*   $\phi(t)$: Excitation kernel (endogenous feedback). Typically exponential: $\phi(t) = \alpha e^{-\beta t}$.

**Branching Ratio:**
$$ n = \int_0^{\infty} \phi(t) dt = \frac{\alpha}{\beta} $$
If $n < 1$, the process is stable (stationary). If $n \ge 1$, it explodes (flash crash).

### 1.2 Multivariate Hawkes Process (Buy/Sell Dynamics)
We model the interaction between buy ($N^+$) and sell ($N^-$) intensities:
$$ \lambda_i(t) = \mu_i + \sum_{j \in \{+,-\}} \int_{-\infty}^t \phi_{ij}(t-u) dN_j(u) $$

Where $\phi_{ij}$ captures cross-excitation.
*   $\phi_{+-}$: Impact of sell orders on buy intensity (e.g., "buy the dip").
*   $\phi_{++}$: Momentum (e.g., "trend following").

---

## 2. Transient Impact Models (TIM)

Market impact is not permanent; it decays as liquidity replenishes.

### 2.1 The Propagator Model
The price at time $t$, $P_t$, is modeled as:
$$ P_t = P_0 + \sum_{t' < t} G(t - t') \cdot \epsilon_{t'} \cdot V_{t'}^\gamma $$

Where:
*   $G(	au)$: Propagator function (decay kernel). Often $G(	au) \propto 	au^{-\delta}$.
*   $\epsilon_{t'}$: Sign of the trade at $t'$ (+1 for buy, -1 for sell).
*   $V_{t'}$: Volume of the trade.
*   $\gamma$: Concavity parameter (usually $\approx 0.5$, square-root law).

**Decay Function:**
$$ G(	au) = \frac{C}{(1 + 	au/	au_0)^\beta} $$
If $\beta \approx 0.5$, the impact has long memory (long-range dependence).

### 2.2 Cross-Impact (Multi-Asset)
The impact of trading asset $i$ on the price of asset $j$:
$$ P_j(t) = \sum_{k} \int_{-\infty}^t G_{jk}(t-s) dQ_k(s) $$
This captures sector-wide moves (e.g., selling Gold futures impacts Silver spot).

---

## 3. Liquidity Estimation (Kyle's Lambda)

Kyle's model relates order flow imbalance to price changes.

### 3.1 Linear Regression Approach
We estimate the price impact coefficient $\lambda$ (Kyle's Lambda):
$$ \Delta P_t = \alpha + \lambda \cdot OFI_t + \epsilon_t $$

Where $OFI_t$ (Order Flow Imbalance) is the net aggressive volume:
$$ OFI_t = \sum_{k \in \Delta t} V_k \cdot 	ext{sgn}(k) $$

**Intraday Seasonality:**
$\lambda$ is not constant. It follows a "U-shape" (high at Open/Close, low at Midday). We model $\lambda(t)$ using periodic functions (Fourier series).

---

**References:**
1.  Hawkes, A. G. (1971). "Spectra of some self-exciting and mutually exciting point processes".
2.  Bouchaud, J. P., et al. (2004). "Fluctuations and response in financial markets: the subtle nature of 'random' price changes".
3.  Kyle, A. S. (1985). "Continuous Auctions and Insider Trading".
