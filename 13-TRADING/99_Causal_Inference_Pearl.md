# 99 - Causal Inference & Attention Transformers

**Volume:** 99 of 100
**Strategy Type:** Future Tech / AI / Econometrics / Explainability
**Risk Profile:** Assumption Validity (Graph Structure) / Overfitting to History
**Mathematical Basis:** Structural Causal Models (Pearl) \u0026 Scaled Dot-Product Attention (Vaswani)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context](#2-historical-context)
    * 2.1. The Limitation of Deep Learning: Correlation without Context.
    * 2.2. Judea Pearl's Causal Ladder (Indicator 094/099).
    * 2.3. The Transformer Revolution (Indicator 098): "Attention Is All You Need".
3. [The Theory: Causal Attention](#3-the-theory-causal-attention)
    * 3.1. Attention finds *what* is important (The Signal).
    * 3.2. Causality explains *why* it is important (The Mechanism).
    * 3.3. Merged: A model that attends only to Causal Parents, ignoring Spurious Correlations.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Attention Mechanism ($softmax(QK^T)$).
    * 4.2. Back-Door Adjustment ($P(Y|do(X))$).
5. [The Strategy Rules](#5-the-strategy-rules)
    * 5.1. Graph Construction (DAG).
    * 5.2. Attention Masking (Forcing the Transformer to respect the DAG).
    * 5.3. Interpretability Signal.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python: Causal Graph with DoWhy.
    * 6.2. Python: Temporal Fusion Transformer (TFT).
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 99** is the fusion of **Causal Inference (Strategy 99)** and **Transformers (Indicator 098)**.
Standard Transformers (GPT) learn correlations from massive data. They hallucinate because they don't know *truth*, only *probability*.
Causal Inference provides the "Logic" (The Directed Acyclic Graph).
Strategy 99 constructs a **Causal Transformer**: A Neural Network where the Attention Heads are constrained by the Causal Graph.
It doesn't just predict "Price Up". It says "Price Up *because* Rates Down caused Discount Factor Adjustment".

---

# 2. Historical Context

### 2.1. Indicator 098 (Attention)

Google (2017) revolutionized AI with Attention.
Instead of processing data sequentially (RNN), the model looks at *all* history at once and assigns "Attention Weights".
Market Application: Recognizing that today's price action is structurally similar to specific days in 2008, and attending to those days for prediction.

### 2.2. Indicator 099 (Pearl)

Judea Pearl argued that Data alone is dumb. You need a Model of Reality (SCM).
"You cannot get Causality from Probability."

---

# 3. The Theory: Causal Attention

### 3.1. The Attention Mechanism (from 098)

$$ Attention(Q, K, V) = softmax\left(\frac{QK^T}{\sqrt{d_k}}\right)V $$
Computes a weighted sum of the past.
Problem: It might attend to "Super Bowl Winner" to predict "Stock Market" if there's a spurious correlation.

### 3.2. The Causal Mask

We impose a **Causal Mask** on the Attention Matrix.
If $X$ is not an ancestor of $Y$ in the Causal Graph, $Attention(X \to Y)$ is forced to 0.
The Model is *constrained* to be rational.

---

# 4. Mathematical Derivation

### 4.1. Back-Door Criterion (from Strategy 99 Source)

To estimate the effect of Rates ($X$) on Price ($Y$), we must block confounders ($Z$).
$$ P(Y|do(X)) = \sum_z P(Y|X, z)P(z) $$

### 4.2. Temporal Fusion Transformer (TFT) (from 098)

Combines:

1. **LSTM** (Local processing).
2. **Multi-Head Attention** (Long-term dependencies).
3. **Variable Selection Network** (Feature importance).
Excellent for Interpretability.

---

# 6. Implementation: Production Grade

### 6.1. Python: DoWhy Causal Graph

*(From Strategy 99 Source)*

```python
import dowhy
model = dowhy.CausalModel(
    data=data,
    treatment='Interest_Rate',
    outcome='Stock_Price',
    common_causes=['GDP_Growth', 'Inflation']
)
identified_estimand = model.identify_effect()
```

### 6.2. Python: Causal Transformer (Indicator 098 + 099)

```python
import torch
import torch.nn as nn

class CausalAttention(nn.Module):
    def __init__(self, dim, causal_mask):
        super().__init__()
        self.scale = dim ** -0.5
        self.qkv = nn.Linear(dim, dim * 3)
        self.causal_mask = causal_mask # Adjacency Matrix of DAG

    def forward(self, x):
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        score = (q @ k.transpose(-2, -1)) * self.scale
        
        # Apply Causal Mask (Force spurious links to -inf)
        if self.causal_mask is not None:
             score = score.masked_fill(self.causal_mask == 0, -1e9)
             
        attn = score.softmax(dim=-1)
        return attn @ v
```

---

# 7. Risk Management

### 7.1. The Lucas Critique

Models trained on history fail when policy changes.
Causal Attention is robust to this *if* the Causal Graph remains valid.
**Risk:** The Causal Graph itself changes (e.g., Gold stops being an Inflation Hedge and becomes a Tech Asset).
**Solution:** Continuous Structure Learning (NOTEARS algorithm) to update the DAG.

---

# 8. Conclusion

Strategy 99 is the **Scientist**.
It fuses the **Pattern Recognition** of the Transformer with the **Reasoning** of Causal Inference.
It solves the "Black Box" problem of AI.
It doesn't just win. It explains *why* it won.
