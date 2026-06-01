# 03. Deep Learning Architectures for Financial Time Series

**Abstract**
Recurrent Neural Networks (RNNs) suffer from vanishing gradients and lack global context. Transformer-based architectures offer parallelization and long-term memory. This document details the **Temporal Fusion Transformer (TFT)** for probabilistic forecasting, introduces the **Differentiable Sharpe Ratio** loss function for direct portfolio optimization, and explores **Domain Adversarial Neural Networks (DANN)** for robust transfer learning.

---

## 1. Temporal Fusion Transformer (TFT)

The TFT is a state-of-the-art architecture designed for high-performance multi-horizon forecasting, combining the local processing of LSTMs with the global attention mechanism of Transformers.

### 1.1 Architecture Components

**Gating Mechanisms (GRN / GLU):**
To adapt to varying signal-to-noise ratios, TFT employs **Gated Residual Networks (GRN)**.
Let $x$ be the input. The Gated Linear Unit (GLU) is defined as:
$$ \text{GLU}(x) = \sigma(W_1 x + b_1) \odot (W_2 x + b_2) $$
Where $\sigma$ is the sigmoid activation and $\odot$ is the element-wise product.
The GRN applies a GLU to the output of a dense layer with ELU activation, adding a residual connection:
$$ \text{GRN}(x) = \text{LayerNorm}(x + \text{GLU}(\eta_1)) $$
$$ \eta_1 = W_{ELU} \text{ELU}(W_{in} x + b_{in}) + b_{ELU} $$

**Variable Selection Networks (VSN):**
Not all inputs are relevant at all times. VSNs learn which features to attend to.
Let $\xi_t^{(j)}$ be the $j$-th input feature at time $t$. The selection weights $v_{t,j}$ are computed via a softmax over the outputs of separate GRNs for each feature.
$$ v_{t,j} = \frac{\exp(\tilde{v}_{t,j})}{\sum_{k=1}^{m} \exp(\tilde{v}_{t,k})} $$
The selected features are then processed and combined.

**Static Covariate Encoders:**
Static metadata (e.g., sector, market cap group) is encoded via GRNs to produce context vectors $c_s$, which condition the temporal processing layers.

**Interpretable Multi-Head Attention:**
Unlike standard multi-head attention, TFT uses a shared value matrix $V$ across all heads to facilitate interpretability.
$$ \text{Attention}(Q, K, V) = \text{Softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V $$
This allows us to visualize *which past time steps* the model deems most critical for the current forecast.

### 1.2 Probabilistic Forecasting (Quantile Loss)
Instead of predicting a single value $\hat{y}$, TFT predicts multiple quantiles $\hat{y}^{(\tau)}$ (e.g., $\tau \in \{0.1, 0.5, 0.9\}$).
The **Quantile Loss** (Pinball Loss) is minimized:
$$ \mathcal{L}(\Omega, W) = \sum_{y_t \in \Omega} \sum_{\tau \in \mathcal{T}} \max \left( \tau(y_t - \hat{y}_t^{(\tau)}), (1-\tau)(\hat{y}_t^{(\tau)} - y_t) \right) $$

This provides a calibrated confidence interval, crucial for risk management.

---

## 2. Loss Functions for Financial Objectives

Mean Squared Error (MSE) minimizes the deviation from the price path but ignores profitability. We must optimize the risk-adjusted return directly.

### 2.1 Differentiable Sharpe Ratio
The Sharpe Ratio is non-convex. However, we can approximate its gradient for optimization.
Let $R_t = \sum_{i=1}^N w_{i,t} r_{i,t+1}$ be the portfolio return at time $t$.
The realized Sharpe Ratio over a batch of size $T$ is:
$$ SR_T = \frac{\mathbb{E}[R_t]}{\sqrt{\text{Var}[R_t]}} \approx \frac{\frac{1}{T} \sum R_t}{\sqrt{\frac{1}{T} \sum R_t^2 - (\frac{1}{T} \sum R_t)^2}} $$

The gradient $\nabla_\theta SR_T$ can be computed via automatic differentiation (PyTorch `autograd`), allowing the neural network to update its weights $\theta$ to maximize $SR_T$.

**Limitation:** This requires large batch sizes ($T > 252$) to be stable. For online learning, we use the **Differential Sharpe Ratio** (see Reinforcement Learning chapter).

---

## 3. Transfer Learning & Domain Adaptation

Financial regimes shift (Bull $\to$ Bear). Models trained on one regime fail on another (Covariate Shift).

### 3.1 Domain Adversarial Neural Networks (DANN)
We train a feature extractor $G_f$ to be **domain-invariant**.
The architecture consists of three parts:
1.  **Feature Extractor ($G_f$):** Maps input $x$ to latent vector $z$.
2.  **Label Predictor ($G_y$):** Predicts price movement $y$ from $z$.
3.  **Domain Discriminator ($G_d$):** Predicts the domain $d$ (e.g., 2020 vs 2022) from $z$.

**Objective:**
Maximize label accuracy while *minimizing* domain accuracy.
$$ \min_{G_f, G_y} \max_{G_d} \mathcal{L}_y(G_y(G_f(x)), y) - \lambda \mathcal{L}_d(G_d(G_f(x)), d) $$

This is implemented via a **Gradient Reversal Layer (GRL)**. During backpropagation, the gradient from the domain discriminator is multiplied by $-\lambda$ before passing to the feature extractor.
**Result:** The latent features $z$ contain information useful for prediction but *no information* about which time period (regime) the data came from.

---

**References:**
1.  Lim, B., et al. (2021). "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting". *International Journal of Forecasting*.
2.  Ganin, Y., et al. (2016). "Domain-Adversarial Training of Neural Networks". *JMLR*.
3.  Moody, J., & Saffell, M. (2001). "Learning to Trade via Direct Reinforcement". *IEEE Transactions on Neural Networks*.