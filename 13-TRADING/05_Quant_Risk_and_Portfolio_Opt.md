# 05. Quantitative Risk Management & Portfolio Optimization

**Abstract**
Traditional Mean-Variance Optimization (MVO) is unstable due to estimation errors in the covariance matrix. Hierarchical Risk Parity (HRP) leverages machine learning (clustering) to allocate capital robustly. We also detail the Almgren-Chriss framework for minimizing transaction costs and the Deflated Sharpe Ratio (DSR) to avoid selection bias.

---

## 1. Hierarchical Risk Parity (HRP)

HRP avoids the inversion of the covariance matrix, making it robust to multicollinearity (e.g., highly correlated tech stocks). It operates in three stages:

### 1.1 Hierarchical Clustering (Tree Structure)
We convert the correlation matrix $C$ into a distance matrix $D$.
$$ d_{i,j} = \sqrt{2(1 - \rho_{i,j})} $$
Using the single-linkage algorithm, we cluster assets based on distance.
Let $U_i, U_j$ be two clusters. The distance between them is:
$$ d(U_i, U_j) = \min \{ d_{p,q} : p \in U_i, q \in U_j \} $$
This produces a dendrogram (tree) where similar assets are grouped together.

### 1.2 Quasi-Diagonalization (Matrix Reordering)
We reorder the covariance matrix $\Sigma$ such that similar assets are placed adjacent to each other. This diagonalization reveals the block-diagonal structure of the risk.
The algorithm performs a recursive traversal of the dendrogram to generate a sorted list of indices $L = \{ l_1, l_2, \dots, l_N \}$.

### 1.3 Recursive Bisection (Capital Allocation)
We allocate weights $w$ top-down.
Let $V_i$ be the variance of cluster $i$.
$$ V_{cluster} = w_{sub}^T \Sigma_{sub} w_{sub} $$
Where $w_{sub}$ are the inverse-variance weights of the assets within the cluster, normalized to sum to 1.

For a split into Left ($L$) and Right ($R$) clusters:
$$ \alpha_L = 1 - \frac{V_L}{V_L + V_R}, \quad \alpha_R = 1 - \alpha_L $$
$$ w_L = w_{parent} \times \alpha_L $$
$$ w_R = w_{parent} \times \alpha_R $$
This ensures that diversification benefits are maximized *between* clusters before allocating *within* clusters.

---

## 2. Almgren-Chriss Optimal Execution

When executing large orders (e.g., rebalancing), market impact eats into alpha. We minimize Expected Cost ($E[C]$) + Risk Aversion ($\lambda \text{Var}[C]$).

### 2.1 Market Impact Model
Let $X$ be the total shares to trade over time $T$.
Let $n_k$ be the shares traded in interval $k$.
The price process follows Arithmetic Brownian Motion:
$$ S_k = S_{k-1} + \sigma \tau^{1/2} \xi_k - \eta \frac{n_k}{\tau} - \gamma (X - x_k) $$

*   **Temporary Impact ($\eta$):** Cost proportional to the *rate* of trading ($v_k = n_k / \tau$). Dissipates immediately.
    $$ h(v_k) = \epsilon \text{sgn}(v_k) + \eta |v_k| $$
    Where $\epsilon$ is the bid-ask spread and $\eta$ is the liquidity coefficient.
*   **Permanent Impact ($\gamma$):** Cost proportional to the total size $X$. Shifts the equilibrium price.

### 2.2 Objective Function
Minimize total implementation shortfall $C$:
$$ E[C] = \sum_{k=1}^N \tau v_k \left( \frac{1}{2} \gamma \tau v_k + \eta v_k + \epsilon \text{sgn}(v_k) \right) $$
Subject to $\sum v_k \tau = X$.

**Solution (Trading Trajectory):**
For risk-neutral ($\lambda=0$): Uniform execution (TWAP).
For risk-averse ($\lambda > 0$): Front-loaded execution to reduce exposure to volatility.
$$ v_k^* = \frac{\sinh(\kappa(T-t_k))}{\sinh(\kappa T)} X, \quad \kappa \propto \sqrt{\frac{\lambda \sigma^2}{\eta}} $$

---

## 3. Backtest Overfitting (Deflated Sharpe Ratio)

Selecting the best strategy from $N$ trials guarantees overfitting. The expected maximum Sharpe Ratio increases with $\log(N)$.

### 3.1 The False Discovery Rate
If we run 100 random strategies, 5 will have a Sharpe Ratio $> 2$ by pure chance (at 95% confidence).

### 3.2 Deflated Sharpe Ratio (DSR)
We adjust the Sharpe Ratio $SR$ for the number of trials $N$ and the non-normality of returns (Skewness, Kurtosis).
$$ DSR = \frac{(SR - E[\max SR_N])}{\sqrt{1 - \gamma_3 Skew + \frac{\gamma_4-1}{4} Kurt}} $$
Where $E[\max SR_N] \approx \sqrt{2 \log N}$ (for Gaussian returns).

**Usage:**
Reject any strategy where $Prob(DSR > 0) < 0.95$.
This rigorously filters out "lucky" backtests.

---

**References:**
1.  Lopez de Prado, M. (2016). "Building Diversified Portfolios that Outperform Out-of-Sample". *Journal of Portfolio Management*.
2.  Almgren, R., & Chriss, N. (2000). "Optimal Execution of Portfolio Transactions". *Journal of Risk*.
3.  Bailey, D., & Lopez de Prado, M. (2014). "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality". *Journal of Portfolio Management*.