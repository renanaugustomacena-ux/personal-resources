# 46 - Machine Learning: Support Vector Machines (SVM)

**Volume:** 46 of 50
**Strategy Type:** Machine Learning / Supervised Classification / Quantitative
**Risk Profile:** Overfitting / Regime Change / Non-Stationarity
**Mathematical Basis:** Hyperplane Optimization ($\max \frac{2}{||w||}$) & Kernel Trick

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Wide Margin](#2-the-theory-the-wide-margin)
    * 2.1. The Classification Problem: Separating Bulls from Bears
    * 2.2. Vapnik's Revolution: Margin > Error Minimization
    * 2.3. The Kernel Trick: Solving non-linear problems in Infinite Dimensions
3. [The Strategy: Hyperplane Crossover](#3-the-strategy-hyperplane-crossover)
    * 3.1. Features: RSI, ADX, Volatility (The 3D Space)
    * 3.2. Labeling: Triple Barrier Method (Profit, Stop, Time)
    * 3.3. Signal Generation: The Signed Distance to the Hyperplane
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The Primal & Dual Problems
    * 4.2. Radial Basis Function (RBF) Kernel
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Man AHL (The move from Linear to Non-Linear)
    * 5.2. Latency Arbitrage (Linear SVM in Microstructure)
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (Scikit-Learn Pipeline with Purged K-Fold)
    * 6.2. Rust (Linfa Bindings for HFT)
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. Probability Calibration (Platt Scaling)
    * 7.2. One-Class SVM (Crash Detection)
    * 7.3. Nu-SVM (Better Parameter Tuning)
8. [Risk Management](#8-risk-management)
    * 8.1. Overfitting & Look-Ahead Bias
    * 8.2. Non-Stationarity (Walk-Forward Optimization)
9. [Conclusion](#9-conclusion)

---

# 1. Executive Summary

**Support Vector Machines (SVM)** are the geometric classifiers of the Machine Learning world.
While Neural Networks optimize for minimizing error (often leading to overfitting noise), SVMs optimize for **Maximizing the Margin**—the distance between the decision boundary and the nearest data points.
In trading, where the Signal-to-Noise ratio is extremely low, this property makes SVMs exceptionally robust.
We use SVMs to classify **Market Regimes** (Trend vs Mean Reversion) and as a **Directional Filter**.

---

# 2. The Theory: The Wide Margin

## 2.1. The Classification Problem

Imagine identifying "Buy" days and "Sell" days based on RSI and Volume.
A Linear Regression draws a line through the *average* of the data.
An SVM draws a line that creates the **widest possible street** between the "Buy" cluster and the "Sell" cluster.

## 2.2. Support Vectors

The dots touching the edges of this street are the **Support Vectors**.
These are the critical market states—the edge cases—that define the boundary.
The millions of "easy" data points in the middle of the trend are ignored.
**Key Insight:** In trading, the information is at the edges, not the average.

## 2.3. The Kernel Trick

Financial data is non-linear. You cannot separate Profitable Trades from Losing Trades with a straight line.
The **Kernel Trick** projects data into higher dimensions (3D, 4D, Infinite).
In 3D, a flat sheet (Hyperplane) *can* slice the data perfectly.
When projected back to 2D, this looks like a complex, curved boundary.

---

# 3. The Strategy: Hyperplane Crossover

This strategy uses the geometric output of the SVM directly.

## 3.1. Construction

* **Input Features:**
    1. **RSI (14):** Momentum.
    2. **Parkinson Volatility:** Variance.
    3. **Distance from MA(200):** Trend.
* **Target:**
  * **+1 (Bull):** Price hits +2% before -1%.
  * **-1 (Bear):** Price hits -1% before +2%.
  * **0 (Neutral):** Time limit reached. (Drop these or use 0).

## 3.2. Training

* **Model:** SVC with RBF Kernel ($C=1.0, \gamma='scale'$).
* **scaling:** Standard Scaler (Mean 0, Std 1). **Crucial** for SVMs.

## 3.3. Execution Rules

* **Monitor:** The **Signed Distance** to the Hyperplane (`decision_function`).
* **Signal:**
  * **Long:** Dist moves from Negative to Positive (> +0.5 Confidence).
  * **Short:** Dist moves from Positive to Negative (< -0.5 Confidence).
  * **Cash:** If Dist is between -0.5 and +0.5 (Inside the "Street of Uncertainty").

---

# 4. Mathematical Derivation

## 4.1. The Primal Problem

Minimize the norm of the weights (maximize margin):
$$ \min \frac{1}{2} ||w||^2 + C \sum \xi_i $$
Subject to: $y_i (w \cdot x_i + b) \ge 1 - \xi_i$.
$\xi_i$ are slack variables allowing some misclassification (Soft Margin).

## 4.2. RBF Kernel

$$ K(x, x') = \exp(-\gamma ||x - x'||^2) $$
This measures "similarity". The SVM classifies a new point based on how similar it is to the Support Vectors.

---

# 5. Historical Case Studies

## 5.1. Man AHL

In the 1990s, Man AHL moved from Linear models to SVMs.
They found that SVMs could capture the "Smile" in volatility surfaces and the non-linear reaction of price to news (prices react fast to bad news, slow to good news) better than linear regressions.

## 5.2. Dimensionality vs Data

SVMs work well when $Dimensions \gg Samples$.
However, in Finance, we have few "Independent" samples but infinite features.
Feature Selection is critical.

---

# 6. Implementation: Production Grade

## 6.1. Python (Scikit-Learn Pipeline)

```python
import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

class SVMStrategy:
    def __init__(self):
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('svm', SVC(C=1.0, kernel='rbf', probability=True))
        ])

    def train(self, X, y):
        # X: DataFrame of Features
        # y: Series of Labels (-1, 0, 1)
        # Drop 0s for binary classification or use One-vs-One
        mask = y != 0
        self.pipeline.fit(X[mask], y[mask])

    def predict_signal(self, current_features):
        # Returns Signed Distance
        dist = self.pipeline.decision_function([current_features])[0]
        
        if dist > 0.5: return "BUY"
        if dist < -0.5: return "SELL"
        return "HOLD"
```

## 6.2. Rust (Linfa Bindings)

Using `linfa-svm`, a native Rust implementation part of the Linfa project.

```rust
use linfa::prelude::*;
use linfa_svm::Svm;
use linfa_kernel::Kernel;
use ndarray::Array2;

pub struct SVMClassifier {
    model: Svm<f64, i32>,
}

impl SVMClassifier {
    pub fn train(features: Array2<f64>, targets: Array1<i32>) -> Self {
        let dataset = Dataset::new(features, targets);
        
        let model = Svm::params()
            .pos_neg_weights(1.0, 1.0)
            .c_value(1.0)
            .gaussian_kernel(10.0) // RBF Kernel
            .fit(&dataset)
            .expect("Training failed");
            
        Self { model }
    }
    
    pub fn predict(&self, feature_vector: Array1<f64>) -> i32 {
        self.model.predict(&feature_vector)
    }
}
```

---

# 7. Optimization & Variations

## 7.1. Probability Calibration

SVM outputs distance. To get probability (Confidence), we use **Platt Scaling** (fitting a Logistic Regression on the distances).
`SVC(probability=True)` in sklearn does this automatically using 5-fold CV.

## 7.2. One-Class SVM

A different beast. It wraps the training data in a hypersphere.
Anything outside the sphere is an **Anomaly**.
Use this to detect "Flash Crash" conditions. If One-Class SVM says "Anomaly", the bot goes to Cash instantly.

---

# 8. Risk Management

## 8.1. Overfitting

If Training Accuracy > 70% in finance, you are overfitted.
Real edge is usually 52-55%.
**Solution:** Purged K-Fold Cross Validation. Ensure training time precedes test time, with a gap (purge) equal to the label horizon.

## 8.2. Regime Change

An SVM trained on 2020 (Pandemic Volatility) will fail in 2024 (Low Vol Grind).
**Solution:** Rolling Window Retraining. Retrain every week on the last 6 months of data.

---

# 9. Conclusion

Machine Learning in trading is not about "predicting the future".
It is about **State Recognition**.
SVM is the best tool for recognizing complex, non-linear states.
It tells us: "Based on RSI, Volatility, and Volume, this setup looks 80% similar to previous Bullish setups (Support Vectors)."
We trade the similarity.
