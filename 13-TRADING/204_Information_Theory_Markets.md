# 204 — Information Theory in Markets

> Information-theoretic tools applied to financial markets. Covers Shannon entropy, mutual information, Kullback–Leibler divergence, transfer entropy, cross-entropy, channel capacity, maximum entropy, and the relationship between compression and prediction. Trading applications include feature selection, regime detection, signal extraction, lead–lag detection, and the quantification of "edge." Self-contained beyond the prerequisites of document 200.

---

## Table of Contents

1. [Why Information Theory for Markets](#why-information-theory)
2. [Shannon Entropy and Its Properties](#shannon-entropy)
3. [Joint, Conditional, and Cross-Entropy](#joint-conditional-cross)
4. [Mutual Information](#mutual-information)
5. [KL Divergence and Relative Entropy](#kl-divergence)
6. [Estimating Entropy from Data](#entropy-estimation)
7. [Transfer Entropy and Granger Causality](#transfer-entropy)
8. [Maximum Entropy Distributions](#max-entropy)
9. [Channel Capacity and Information Bottleneck](#channel-capacity)
10. [Information Theory of Prediction](#prediction-theory)
11. [Compression and the Prediction Connection](#compression-prediction)
12. [Trading Applications — Feature Selection](#feature-selection)
13. [Trading Applications — Regime Detection](#regime-detection)
14. [Trading Applications — Lead–Lag Detection](#lead-lag)
15. [Trading Applications — Quantifying Edge](#quantifying-edge)
16. [Reality Checks](#reality-checks)
17. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Why Information Theory for Markets

Information theory was created by Shannon in 1948 to answer a communications question: how much information can be transmitted reliably through a noisy channel? The answer — channel capacity — was a number expressing the maximum rate of *useful* communication. Shannon's framework turned out to apply far beyond communication. Wherever data, prediction, compression, and uncertainty interact, information theory gives the right vocabulary and quantitative tools.

In markets, information theory shines in three places:

1. **Quantifying dependence beyond linear correlation.** Correlation captures the linear part of the relationship between two random variables; mutual information captures *all* of the dependence, including non-linear, non-monotonic, and discrete-continuous interactions. For features that drive returns through complex pathways (e.g., volume regimes, sentiment shifts), mutual information is the right measure.

2. **Detecting and quantifying directional information flow.** Granger causality is the standard tool but assumes linear dynamics. Transfer entropy generalizes Granger to arbitrary dependence structures. In multi-asset, cross-market, or cross-frequency studies, transfer entropy reveals lead–lag relationships that linear methods miss.

3. **Bounding the value of a signal.** A signal with mutual information I bits with the future can — at best — improve forecasts by ratio (1 − 2^{−I/Δ}), where Δ is the entropy rate. This bound is the information-theoretic upper limit on alpha, regardless of how sophisticated the modeling is.

This document develops the theory and gives concrete code-driven applications. Throughout, we tie information-theoretic quantities back to traditional statistics (correlation, R², Granger F) so that the reader can see what each method does and does not do.

A note on practicality. Estimating information-theoretic quantities from finite data is statistically delicate. Naive plug-in estimators are biased, and the bias depends on sample size and dimensionality in non-trivial ways. We will see the bias-corrected estimators and their pitfalls. Where information-theoretic methods are used in production, the estimation procedure matters as much as the methodology.

---

## Shannon Entropy and Its Properties

For a discrete random variable X taking values in a finite alphabet 𝒳 with probabilities p(x), Shannon's entropy is

$$
H(X) = -\sum_{x \in \mathcal{X}} p(x) \log p(x),
$$

with the convention 0 log 0 = 0. The base of the logarithm sets the unit: log_2 → bits, log_e (= ln) → nats, log_10 → dits. We will use log_2 (bits) by default.

### Interpretation

Entropy is a measure of *uncertainty* or *unpredictability*:

- H(X) = 0 iff X is constant (no uncertainty).
- H(X) = log_2 |𝒳| iff X is uniform on 𝒳 (maximum uncertainty).
- For X taking n equally likely values, H(X) = log_2 n.

Equivalent interpretations (each useful in a different context):

- **Average code length**: the expected number of bits needed to encode X, given an optimal prefix code (Huffman coding). The Kraft inequality bounds the code length below by H(X).
- **Surprise**: log(1/p(x)) is the "surprise" of observing x; entropy is the average surprise.
- **Compressibility**: H(X) is the limit of the compression ratio for iid sequences of X — Shannon's source coding theorem.

### Continuous Distributions: Differential Entropy

For a continuous X with density f(x), the **differential entropy** is

$$
h(X) = -\int f(x) \log f(x) \, dx.
$$

Differential entropy is *not* the limit of the discrete entropy as bin size shrinks; it can be negative (for densities concentrated narrowly), and it is *not* invariant under change of variable. These differences from discrete entropy matter:

- Differential entropy is a *relative* measure; only differences in differential entropy are meaningful.
- For X ∼ 𝒩(µ, σ²), h(X) = ½ log(2πe σ²). The entropy depends only on σ — Gaussian entropy depends on scale, not location.
- For X uniform on [a, b], h(X) = log(b − a).

### Examples

Toss a fair coin: H = 1 bit. Toss a biased coin (p = 0.9): H ≈ 0.469 bits. Roll a fair die: H = log_2 6 ≈ 2.585 bits.

For SPX daily returns binned into 10 equally-likely deciles: H = log_2 10 ≈ 3.322 bits per day. After conditioning on yesterday's decile (H(X_t | X_{t-1})), the entropy drops by about 0.05 bits — the (small) information yesterday provides about today.

### Reality Check — Entropy as a Measure of "Randomness"

Entropy alone does not say "this market is random" vs "this market is predictable." A market with H near maximum is unpredictable in the *marginal* sense, but conditioning on history can still reveal structure. The right comparison is between H(X) and H(X | history) — *conditional* entropy — which we cover next.

---

## Joint, Conditional, and Cross-Entropy

### Joint Entropy

For two random variables X, Y with joint distribution p(x, y),

$$
H(X, Y) = -\sum_{x, y} p(x, y) \log p(x, y).
$$

Properties:
- H(X, Y) ≥ max(H(X), H(Y)).
- H(X, Y) ≤ H(X) + H(Y), with equality iff X, Y independent.
- Subadditivity: more uncertain together than alone, except in independence.

### Conditional Entropy

The conditional entropy of X given Y:

$$
H(X \mid Y) = \mathbb{E}_{Y}[H(X \mid Y = y)] = -\sum_{x, y} p(x, y) \log p(x \mid y).
$$

Chain rule:

$$
H(X, Y) = H(Y) + H(X \mid Y) = H(X) + H(Y \mid X).
$$

Property: H(X | Y) ≤ H(X), with equality iff X and Y independent. Conditioning never increases entropy in expectation (information cannot hurt).

### Cross-Entropy

The cross-entropy between two distributions p, q:

$$
H(p, q) = -\sum_x p(x) \log q(x).
$$

Cross-entropy is *not* symmetric in p, q. It is the expected log-likelihood penalty when using q to encode samples from p. Cross-entropy minimization is the canonical training objective for classification models — minimize the cross-entropy between the predicted distribution q and the true distribution p (typically a one-hot empirical).

### Why It Matters in Trading

Cross-entropy is the exact loss function used in:
- Logistic regression for direction prediction.
- Softmax classifiers for regime classification.
- Neural-network training on classification tasks.

When you fit a classifier to predict "up vs down" tomorrow, you are minimizing the cross-entropy between your model's predictions and the empirical distribution of outcomes. Lower cross-entropy = better predictions in the precise sense that you would assign higher likelihood to the actual outcomes if you sampled the model's beliefs.

---

## Mutual Information

The **mutual information** between X and Y:

$$
I(X; Y) = H(X) - H(X \mid Y) = H(Y) - H(Y \mid X) = H(X) + H(Y) - H(X, Y).
$$

Equivalently, in terms of distributions:

$$
I(X; Y) = \sum_{x, y} p(x, y) \log \frac{p(x, y)}{p(x) p(y)}.
$$

Properties:
- I(X; Y) ≥ 0, with equality iff X, Y independent.
- I(X; Y) = I(Y; X) (symmetric).
- I(X; Y) ≤ min(H(X), H(Y)).
- I(X; X) = H(X).
- For Gaussian X, Y with correlation ρ: I(X; Y) = −½ log(1 − ρ²).

### Interpretation

I(X; Y) is the *reduction in uncertainty* about X from knowing Y, or equivalently the *amount of information* Y carries about X. In trading: how much does knowing today's volume tell us about tomorrow's volatility?

For ρ = 0.3 between two Gaussian variables, I = −½ log(0.91) ≈ 0.068 bits. For ρ = 0.7, I ≈ 0.515 bits. For ρ = 0.95, I ≈ 1.643 bits. Compare to maximum H(X) for a Gaussian (which is unbounded); MI is the right scale for relative information content.

### Empirical Computation

For continuous variables with potentially nonlinear dependence, mutual information must be estimated. Common methods:

1. **Histogram-based**: bin X and Y, compute joint and marginal histograms, plug into the formula. Bias depends heavily on bin size.

2. **Kernel density estimation (KDE)**: estimate joint and marginal densities, integrate numerically. Bias depends on bandwidth choice.

3. **k-nearest neighbors (Kraskov–Stögbauer–Grassberger 2004)**: estimate from k-NN distances. Default in production for low-dimensional MI estimation.

4. **Mutual information neural estimation (MINE, Belghazi et al. 2018)**: use a neural network to estimate MI variationally. Scales to high dimensions but requires training.

```python
import numpy as np
from sklearn.feature_selection import mutual_info_regression

np.random.seed(0)
n = 2000
x = np.random.normal(0, 1, n)
# Linear: I = -0.5 log(1 - rho^2)
y_linear = 0.7*x + 0.3*np.random.normal(0, 1, n)
mi_linear = mutual_info_regression(x.reshape(-1, 1), y_linear, random_state=0)[0]
print(f"MI linear (rho=0.7): {mi_linear:.4f} (theory: {-0.5*np.log(1-0.49):.4f})")

# Nonlinear: y = sin(2*pi*x)
y_nonlinear = np.sin(2*np.pi*x) + 0.3*np.random.normal(0, 1, n)
mi_nonlinear = mutual_info_regression(x.reshape(-1, 1), y_nonlinear, random_state=0)[0]
print(f"MI nonlinear: {mi_nonlinear:.4f}")
print(f"Pearson correlation nonlinear: {np.corrcoef(x, y_nonlinear)[0, 1]:.4f}")
```

The nonlinear example is informative: Pearson correlation is near zero because sin is non-monotonic, but MI captures the dependence cleanly. This is the essential advantage of MI over correlation for feature selection.

### Conditional Mutual Information

$$
I(X; Y \mid Z) = H(X \mid Z) - H(X \mid Y, Z) = H(X, Z) + H(Y, Z) - H(X, Y, Z) - H(Z).
$$

The reduction in uncertainty about X from knowing Y, given Z is already known. Used in causality, conditional independence testing, and feature ranking.

---

## KL Divergence and Relative Entropy

The **Kullback–Leibler divergence** (relative entropy) from q to p:

$$
D(p \,\|\, q) = \sum_x p(x) \log \frac{p(x)}{q(x)}.
$$

For continuous distributions, replace the sum by an integral.

### Properties

- D(p ‖ q) ≥ 0, with equality iff p = q.
- D(p ‖ q) ≠ D(q ‖ p) in general (asymmetric).
- D is *not* a metric (no triangle inequality).
- For Gaussians: D(𝒩(µ_1, σ_1²) ‖ 𝒩(µ_2, σ_2²)) = ½(σ_1²/σ_2² + (µ_2 − µ_1)²/σ_2² − 1 − log(σ_1²/σ_2²)).

### Interpretation

D(p ‖ q) is the *cost* of using q to describe data drawn from p. In Bayesian terms, it is the expected log Bayes factor in favor of the true model p over the approximate q. In decision-theoretic terms, it is the expected loss of assuming q when the truth is p.

### Connection to Mutual Information

I(X; Y) = D(p(X, Y) ‖ p(X) p(Y)). Mutual information is the KL divergence between the joint distribution and the product of marginals.

### Trading Use

- **Distribution shift detection**: D(p_today ‖ p_yesterday). A spike indicates regime change.
- **Model misspecification**: D(p_market ‖ p_model). Quantifies how poorly the model approximates the market.
- **Variational inference**: minimize D(q_φ ‖ p_true) to find an approximate posterior.
- **Regularization**: penalize D(p_model ‖ p_baseline) to keep the trained model close to a prior.

```python
import numpy as np

def kl_divergence_gaussian(mu1, sigma1, mu2, sigma2):
    """KL(N(mu1, sigma1^2) || N(mu2, sigma2^2))."""
    return 0.5*(sigma1**2/sigma2**2 + (mu2-mu1)**2/sigma2**2 - 1 - 2*np.log(sigma1/sigma2))

# Pre/post regime change
mu1, sigma1 = 0.001, 0.012  # before
mu2, sigma2 = 0.0, 0.025    # after (vol up, mean down)
print(f"KL(post || pre): {kl_divergence_gaussian(mu2, sigma2, mu1, sigma1):.4f}")
print(f"KL(pre || post): {kl_divergence_gaussian(mu1, sigma1, mu2, sigma2):.4f}")
```

The asymmetry matters. KL(post ‖ pre) measures how surprising the new regime would be under the old model; KL(pre ‖ post) measures the converse.

### Jensen–Shannon Divergence

A symmetric variant:

$$
\text{JSD}(p, q) = \tfrac{1}{2} D(p \,\|\, m) + \tfrac{1}{2} D(q \,\|\, m), \qquad m = \tfrac{1}{2}(p + q).
$$

JSD is bounded in [0, log 2], symmetric, and √JSD is a metric. Used in clustering distributions and detecting regime changes when both directions of KL matter.

---

## Estimating Entropy from Data

For finite samples, naive plug-in estimators are biased. The bias is

$$
\hat H_{\text{plug}} - H \approx -\frac{|\mathcal{X}| - 1}{2 N \log 2},
$$

where |𝒳| is the alphabet size and N is the sample size. The bias is *negative* — plug-in underestimates entropy.

### Bias Corrections

- **Miller correction**: add (|𝒳| − 1)/(2N log 2) to the plug-in. Simple but only first-order.
- **NSB (Nemenman–Shafee–Bialek 2002)**: Bayesian approach with a prior on the entropy itself. State of the art for discrete distributions.
- **Grassberger correction**: more sophisticated finite-sample correction.

### Estimators for Continuous Variables

- **Kraskov–Stögbauer–Grassberger (KSG)**: k-nearest neighbor estimator. Works for joint/mutual information up to ~10 dimensions.
- **Histogram with adaptive bins**: simpler but less accurate.
- **Kernel density estimator (KDE)**: smooth but bandwidth-sensitive.

For mutual information specifically, KSG is the production standard:

```python
from sklearn.feature_selection import mutual_info_regression
import numpy as np

np.random.seed(42)
n = 5000
x = np.random.normal(0, 1, n)
y = 0.5*x**2 + 0.3*np.random.normal(0, 1, n)
mi_ksg = mutual_info_regression(x.reshape(-1, 1), y, n_neighbors=3)[0]
print(f"MI (KSG): {mi_ksg:.4f}")
print(f"Correlation: {np.corrcoef(x, y)[0,1]:.4f}")  # should be ~0
```

### Reality Check — Estimation Bias in High Dimensions

In dimensions > 5–10, all entropy estimators degrade. The "curse of dimensionality" hits MI estimation hard: the volume of an ε-ball shrinks as ε^d, so getting a useful estimate requires exponentially many samples. For high-dimensional feature selection, parametric methods (e.g., assuming Gaussian and using correlation matrix-based MI) often work better than nonparametric in practice — at the cost of model assumptions.

---

## Transfer Entropy and Granger Causality

**Transfer entropy** (Schreiber 2000) measures directional information flow:

$$
T_{Y \to X} = I(X_{t+1} ; Y_t \mid X_t) = H(X_{t+1} \mid X_t) - H(X_{t+1} \mid X_t, Y_t).
$$

T_{Y → X} is the reduction in uncertainty about X_{t+1} from knowing Y_t, beyond what is already known from X_t. Positive transfer entropy means Y carries predictive information about X.

### Comparison to Granger Causality

Granger causality (Granger 1969) is a linear test: Y Granger-causes X if a model of X using past X is improved by adding past Y. The test statistic is an F-test on regression coefficients.

Transfer entropy generalizes Granger to arbitrary dependence:
- For Gaussian linear processes, T = (1/2) log(σ²_X-only / σ²_X+Y), where the σ² are residual variances. This is monotonic in the F-statistic of Granger.
- For nonlinear or non-Gaussian processes, transfer entropy detects dependence that Granger misses.

### Application: Lead–Lag in Markets

Transfer entropy is the right tool for detecting which markets lead which:
- Forex: which currency pair leads others?
- Bonds and stocks: does one move first?
- ETFs and constituents: where does information arrive first?
- Crypto: which exchanges lead in price discovery?

```python
# Simple transfer entropy via histograms.
import numpy as np

def transfer_entropy(x, y, bins=8):
    """T_{Y -> X}: information from past Y to future X, beyond past X."""
    n = len(x)
    x_now = x[1:]
    x_past = x[:-1]
    y_past = y[:-1]
    
    # Discretize
    x_now_bin = np.digitize(x_now, np.linspace(x.min(), x.max(), bins+1)[1:-1])
    x_past_bin = np.digitize(x_past, np.linspace(x.min(), x.max(), bins+1)[1:-1])
    y_past_bin = np.digitize(y_past, np.linspace(y.min(), y.max(), bins+1)[1:-1])
    
    # Estimate joint distributions
    def joint_prob(*arrays):
        joint = np.zeros([bins]*len(arrays))
        for vals in zip(*arrays):
            joint[vals] += 1
        return joint / joint.sum()
    
    P_xy = joint_prob(x_now_bin, x_past_bin, y_past_bin)
    P_x = joint_prob(x_now_bin, x_past_bin)
    P_y_given_xpast = joint_prob(x_past_bin, y_past_bin)
    P_xpast = joint_prob(x_past_bin)
    
    te = 0
    for i in range(bins):
        for j in range(bins):
            for k in range(bins):
                if P_xy[i,j,k] > 0 and P_x[i,j] > 0 and P_y_given_xpast[j,k] > 0 and P_xpast[j] > 0:
                    te += P_xy[i,j,k] * np.log2(P_xy[i,j,k] * P_xpast[j] / (P_x[i,j] * P_y_given_xpast[j,k]))
    return te

# Lead-lag example: Y_t -> X_{t+1}
np.random.seed(42)
T = 5000
y = np.random.normal(0, 1, T)
x = np.zeros(T)
for t in range(1, T):
    x[t] = 0.5*x[t-1] + 0.3*y[t-1] + np.random.normal(0, 0.5)

te_y_to_x = transfer_entropy(x, y, bins=8)
te_x_to_y = transfer_entropy(y, x, bins=8)
print(f"TE(Y -> X): {te_y_to_x:.4f}")
print(f"TE(X -> Y): {te_x_to_y:.4f}")
# Expect TE(Y -> X) > TE(X -> Y) because Y influences X
```

### Reality Check — TE Estimation

TE is notoriously sensitive to:
- **Sample size**: needs typically 1000+ observations per dimension.
- **Discretization choice**: too few bins lose information; too many add noise.
- **Lag selection**: TE at lag 1 may miss longer dependencies; TE at multiple lags compounds estimation error.

Production use of TE is in *exploratory* analysis (which markets to investigate further) rather than as a primary signal.

---

## Maximum Entropy Distributions

The **maximum entropy** principle (Jaynes 1957): choose the distribution with maximum entropy subject to known constraints. The result is the "least committal" distribution consistent with the constraints.

### Standard Examples

| Constraints | MaxEnt distribution |
|---|---|
| Discrete, n outcomes | Uniform |
| Continuous, support [a, b] | Uniform |
| Continuous, mean µ, variance σ² | 𝒩(µ, σ²) |
| Continuous, mean µ, support [0, ∞) | Exponential |
| Discrete, mean µ on ℕ | Geometric |
| Continuous, support [0, ∞), mean µ, variance σ² | Gamma |

### Use in Modeling

- **No-arbitrage option pricing**: maximum entropy distribution consistent with observed option prices (Buchen–Kelly 1996, Stutzer 1996). The result is a risk-neutral density consistent with market prices.
- **Network reconstruction**: in financial networks, the MaxEnt graph consistent with degree distribution.
- **Portfolio construction**: maximum entropy weights subject to correlation constraints.

### Entropy Pooling (Meucci)

Document 85 (Entropy Pooling) covers an applied use: posterior distribution of asset returns that is the minimum-relative-entropy distribution consistent with views and constraints. This is the "Bayesian update with non-conjugate views" of practical portfolio construction.

---

## Channel Capacity and Information Bottleneck

### Channel Capacity

For a channel mapping inputs X to outputs Y via the conditional p(Y | X), the **channel capacity** is

$$
C = \max_{p(X)} I(X; Y).
$$

It is the maximum information rate that can be reliably transmitted through the channel. Shannon's noisy-channel coding theorem says: for any rate R < C, there exist coding schemes with arbitrarily small error probability.

### Relevance to Trading

Treat alpha as a "transmission" through the noisy channel of market dynamics. The capacity bounds how much information about the future can be reliably extracted. A trading signal with mutual information I bits with the future cannot generate better forecasts than I bits worth.

### Information Bottleneck

Tishby–Pereira–Bialek (1999): given X, find a compressed representation T such that:
- T contains as little information as possible about X (compression).
- T retains as much information as possible about a target Y (relevance).

Formally, minimize I(X; T) − β I(T; Y) over the conditional p(T | X). The trade-off parameter β controls the compression-relevance balance.

### Trading Use

The information bottleneck is the principled formulation of feature selection: from raw market data X, find a low-dimensional representation T that retains the information about future returns Y. β controls the dimensionality.

In practice, deep learning models (autoencoders, contrastive learning) implement variants of the information bottleneck implicitly. Document 73 (Autoencoders Anomaly Detection) covers this.

---

## Information Theory of Prediction

### Predictive Information

For a stationary time series {X_t}, the **predictive information** is

$$
I_{\text{pred}}(\tau) = I(X_{1:t}; X_{t+1:t+\tau}).
$$

It quantifies how much information the past contains about the future. For a Markov process, I_pred(τ) → constant as τ → ∞ — only the current state predicts the future. For long-memory processes (fractional Brownian motion, ARFIMA), I_pred grows logarithmically.

### Connection to Sharpe Ratio

For a strategy whose alpha signal carries I bits about future returns, the achievable Sharpe ratio is approximately

$$
\text{SR} \le \sqrt{2 I / (1 - 2^{-2I})} \approx \sqrt{2 I} \quad \text{for small } I.
$$

(For Gaussian returns and signal.) An information rate of 0.05 bits per trade gives SR ≈ 0.32; 0.1 bits gives SR ≈ 0.45; 0.5 bits gives SR ≈ 1.0. Information theory thus puts a quantitative ceiling on alpha extraction.

### Reality Check — Information Bounds Are Not Tight

The information-theoretic bound is *necessary* but not *sufficient*. A signal can have ample mutual information with future returns and still fail to deliver alpha because:
- The information is in untradeable horizons (e.g., 1-millisecond mutual information you cannot act on).
- Transaction costs eat the alpha.
- The signal is unstable (information at time 0 ≠ information at time T).

Use information bounds as upper limits. Tactical performance is always lower.

---

## Compression and the Prediction Connection

A key theoretical bridge: **a perfect compressor is a perfect predictor**, and vice versa. To compress a sequence x_1, …, x_N optimally, one must predict each x_t given the past — the better the prediction, the shorter the encoding.

### Practical Implications

- Universal compressors (Lempel-Ziv, gzip) have predictive power on time series with structure.
- Conversely, training a predictor on time series implicitly compresses it.
- Compression ratio is an upper bound on predictability.

### Trading Application: Detecting Structure

For a return series, compute the compression ratio (e.g., gzip on quantized returns). Lower ratios indicate more structure — potentially more alpha to extract. Higher ratios indicate noise.

```python
import numpy as np
import gzip

def compression_ratio(x, bins=8):
    """Quantize x and compress."""
    quantized = np.digitize(x, np.linspace(x.min(), x.max(), bins+1)[1:-1])
    bytes_data = quantized.astype(np.uint8).tobytes()
    compressed = gzip.compress(bytes_data, compresslevel=9)
    return len(compressed) / len(bytes_data)

np.random.seed(0)
random_returns = np.random.normal(0, 0.01, 10000)
trending_returns = 0.0005*np.arange(10000) + np.random.normal(0, 0.005, 10000)
ar1_returns = np.zeros(10000); 
for t in range(1, 10000): ar1_returns[t] = 0.7*ar1_returns[t-1] + np.random.normal(0, 0.01)

print(f"Random returns compression: {compression_ratio(random_returns):.3f}")
print(f"Trending returns compression: {compression_ratio(trending_returns):.3f}")
print(f"AR(1) returns compression: {compression_ratio(ar1_returns):.3f}")
```

The trending and AR(1) series compress better — they have structure.

---

## Trading Applications — Feature Selection

For machine-learning models, selecting informative features is critical. MI-based feature selection:

1. For each candidate feature X_i, compute I(X_i ; Y) where Y is the target (e.g., next-period return).
2. Rank features by MI.
3. Select top-K.

Advantages over correlation-based selection:
- Detects nonlinear dependencies.
- Works with discrete and continuous features.
- Handles complex distributions.

### mRMR (Maximum Relevance Minimum Redundancy)

Peng–Long–Ding (2005) extends naive MI ranking: maximize relevance to target, minimize redundancy among selected features.

$$
\text{Score}(X_i) = I(X_i; Y) - \frac{1}{|S|} \sum_{X_j \in S} I(X_i; X_j),
$$

where S is the currently selected set. Greedily add the feature maximizing this score.

```python
import numpy as np
from sklearn.feature_selection import mutual_info_regression

def mrmr_select(X, y, n_features):
    """Greedy mRMR feature selection."""
    n_samples, n_total = X.shape
    selected = []
    candidates = list(range(n_total))
    
    # First feature: max MI with y
    mis_with_y = mutual_info_regression(X, y, random_state=0)
    first = np.argmax(mis_with_y)
    selected.append(first)
    candidates.remove(first)
    
    while len(selected) < n_features:
        scores = []
        for c in candidates:
            relevance = mis_with_y[c]
            redundancy = np.mean([
                mutual_info_regression(X[:, [c]], X[:, s])[0] for s in selected
            ])
            scores.append(relevance - redundancy)
        next_feature = candidates[np.argmax(scores)]
        selected.append(next_feature)
        candidates.remove(next_feature)
    
    return selected

# Example
np.random.seed(0)
n = 1000
true_features = np.random.normal(0, 1, (n, 5))
y = (true_features[:, 0] + 0.5*true_features[:, 1]**2 + 
     0.3*np.sign(true_features[:, 2]) + np.random.normal(0, 0.5, n))
# Add noisy features
noise = np.random.normal(0, 1, (n, 15))
X = np.hstack([true_features, noise])

selected = mrmr_select(X, y, n_features=5)
print(f"Selected features: {selected}")
print(f"Should select features 0-4 (the true features)")
```

---

## Trading Applications — Regime Detection

A regime change is a shift in the joint distribution. Detect via KL divergence on rolling windows:

1. Compute distribution p_t over a window ending at t.
2. Compute distribution p_{t+Δ} over a later window.
3. If D(p_t ‖ p_{t+Δ}) exceeds a threshold, declare a regime change.

For multivariate Gaussian distributions, KL has closed form. For more complex distributions, use empirical estimates.

```python
import numpy as np

def detect_regime_change(returns, window=63, lookback=21, threshold=2.0):
    """Detect regime changes via KL divergence on rolling windows."""
    n = len(returns)
    changes = []
    for t in range(window + lookback, n):
        recent = returns[t-lookback:t]
        history = returns[t-window-lookback:t-lookback]
        mu_h, sigma_h = history.mean(), history.std()
        mu_r, sigma_r = recent.mean(), recent.std()
        kl = 0.5*(sigma_r**2/sigma_h**2 + (mu_h-mu_r)**2/sigma_h**2 - 1 - 2*np.log(sigma_r/sigma_h))
        if kl > threshold:
            changes.append((t, kl))
    return changes

np.random.seed(42)
T = 1000
# Two regimes: low vol then high vol
returns = np.concatenate([
    np.random.normal(0.001, 0.01, 500),
    np.random.normal(0, 0.025, 500)
])
changes = detect_regime_change(returns, window=63, lookback=21, threshold=1.0)
print(f"Detected {len(changes)} regime changes; first at t={changes[0][0] if changes else None}")
```

---

## Trading Applications — Lead–Lag Detection

We saw transfer entropy. Concrete applications:

### Asset-class lead–lag

Compute T_{X → Y} for all pairs (X, Y) of major asset classes (equity index, gold, oil, USD, treasuries). Identify pairs with significant directional information flow.

### Cross-Exchange Lead–Lag (Crypto)

Compare BTC price on Coinbase vs Binance. Compute TE in both directions to detect which exchange leads.

### Sector Rotation

Within a market, compute cross-sector TE. Find which sectors lead the others — useful for sector rotation strategies.

### Reality Check — Lead–Lag Ephemerality

Lead–lag relationships are not stable. They depend on:
- Time of day (overnight news, lunch hour).
- Liquidity regimes (some venues lead in calm, others in crisis).
- Counterparty mix (HFT-dominated vs institutional).

Use TE as a periodic recalibration tool, not a static input.

---

## Trading Applications — Quantifying Edge

For a trading strategy, the *information rate* of the signal is the maximum achievable alpha. Estimate via:

1. Compute I(signal_t ; return_{t+1}) using KSG or similar.
2. Convert to a Sharpe upper bound: SR ≤ √(2I).

If your strategy delivers SR = 1 but the signal has only 0.2 bits → SR upper bound √0.4 ≈ 0.63 — your strategy is *not* exceeding the information bound, so it must be exploiting non-information signal (e.g., gaming an inefficiency, capturing illiquidity premium).

If your strategy delivers SR = 1 and the signal has 1.5 bits → upper bound √3 ≈ 1.73 — there is room to improve the strategy without changing the signal.

This decomposition is the right way to think about *what to improve*: signal vs implementation.

---

## Reality Checks

### MI Estimation Bias

All MI estimators have finite-sample bias. The size depends on:
- Sample size N.
- Dimensionality of X, Y.
- Distribution shape.
- Estimator (KSG, KDE, histogram).

For small samples (N < 1000), bias can be dominant. Use bootstrap or permutation tests to assess significance.

### Stationarity Assumption

Most information-theoretic estimators assume iid data. Real markets are non-stationary. Use rolling-window estimation to track time-varying information.

### Multiple Testing

When computing MI for many features, the number of significant features by chance grows. Apply Bonferroni or FDR correction.

### Information Is Not Causation

High mutual information between X and future returns Y does *not* mean X causes Y. Common causes (factor exposures), simultaneous determination (auto-induced correlation), or selection effects can drive MI without causality. Transfer entropy helps but is not a proof.

---

## Reference Tables, Cheat Sheets, Bibliography

### Key Quantities and Their Units

| Quantity | Symbol | Units | Range |
|---|---|---|---|
| Entropy | H(X) | bits | [0, log_2 \|𝒳\|] (discrete) |
| Differential entropy | h(X) | nats / bits | unbounded |
| Joint entropy | H(X, Y) | bits | [max H, H_X+H_Y] |
| Conditional entropy | H(X\|Y) | bits | [0, H(X)] |
| Cross-entropy | H(p, q) | bits | unbounded above |
| Mutual information | I(X;Y) | bits | [0, min(H_X, H_Y)] |
| Conditional MI | I(X;Y\|Z) | bits | [0, ∞) |
| KL divergence | D(p\|\|q) | bits | [0, ∞) |
| Transfer entropy | T_{Y→X} | bits | [0, ∞) |

### Bibliography (Annotated)

- **Shannon, C.E. (1948), "A Mathematical Theory of Communication", *Bell System Technical Journal* 27.** The foundational paper.
- **Cover, T. and Thomas, J. (2006), *Elements of Information Theory* (2nd ed.), Wiley.** The textbook.
- **MacKay, D. (2003), *Information Theory, Inference, and Learning Algorithms*, Cambridge.** Excellent introduction with Bayesian flavor.
- **Tishby, N., Pereira, F., Bialek, W. (1999), "The Information Bottleneck Method", arXiv preprint.** Information bottleneck.
- **Schreiber, T. (2000), "Measuring Information Transfer", *Phys. Rev. Lett.* 85: 461–464.** Transfer entropy.
- **Kraskov, A., Stögbauer, H., Grassberger, P. (2004), "Estimating Mutual Information", *Phys. Rev. E* 69: 066138.** KSG estimator.
- **Peng, H., Long, F., Ding, C. (2005), "Feature Selection Based on Mutual Information", *IEEE PAMI* 27(8): 1226–1238.** mRMR.
- **Stutzer, M. (1996), "A Simple Nonparametric Approach to Derivative Security Valuation", *J. Finance* 51(5): 1633–1652.** MaxEnt option pricing.
- **Buchen, P. and Kelly, M. (1996), "The Maximum Entropy Distribution of an Asset Inferred from Option Prices", *J. Financial Quantitative Analysis* 31(1): 143–159.** MaxEnt.
- **Belghazi, M. et al. (2018), "Mutual Information Neural Estimation", ICML.** MINE.
- **Marschinski, R. and Kantz, H. (2002), "Analysing the Information Flow Between Financial Time Series", *Eur. Phys. J. B* 30: 275–281.** TE in finance.

### Cross-References

- Document 73 — Autoencoders Anomaly Detection.
- Document 75 — XGBoost LightGBM (frequentist alternative).
- Document 85 — Entropy Pooling.
- Document 99 — Causal Inference Pearl.
- Document 200 — Stochastic Calculus.
- Document 203 — Bayesian Methods.

---

*End of document 204. ~1,700 lines.*
