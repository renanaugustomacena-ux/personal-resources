# Indicator 033: Feature Importance (Random Forest) - The Signal Filter

**"Not all indicators are created equal. Some are noise. RF tells you which ones matter."**

---

## 1. Executive Summary

**Feature Importance** is a meta-indicator. It doesn't tell you *where* the price is going; it tells you *which indicators* are currently predicting the price.
Using a **Random Forest** (ensemble of Decision Trees), we can calculate the **Mean Decrease in Impurity (MDI)** for every input feature (RSI, MAXD, Volume, etc.).

* "Is RSI predictive right now?" $\to$ Importance: 0.02 (No).
* "Is Volume predictive right now?" $\to$ Importance: 0.45 (Yes).

This allows the trading system to dynamically switch off useless indicators and focus on the ones that are working.

---

## 2. Historical Context: Breiman's Forests

**Leo Breiman** (2001) developed Random Forests to cure the overfitting problem of single Decision Trees.
By training 100 deep trees on random subsets of data (Bagging) and random subsets of features, the Forest becomes robust.
A side effect of this process is the ability to interpret the model: If a feature is frequently used to split high-impurity nodes, it is **Important**.

---

## 3. Mathematical Foundations

The core metric is **Gini Impurity**.

### 3.1 Gini Impurity

$$ I_G(p) = 1 - \sum_{i=1}^{J} p_i^2 $$
Where $p_i$ is the probability of class $i$ (e.g., Up/Down) in a node.

* Pure Node (All Up): $I_G = 1 - 1^2 = 0$.
* Impure Node (50/50): $I_G = 1 - (0.5^2 + 0.5^2) = 0.5$.

### 3.2 Feature Importance (MDI)

For each tree, we sum the decrease in Gini Impurity weighted by the probability of reaching that node, for every feature. We extract the average over all trees.
$$ Imp(X_j) = \frac{1}{N_{trees}} \sum_{t=1}^{N_{trees}} \sum_{n \in t, v(n)=X_j} \Delta I(n) $$

---

## 4. Signal Generation and Interpretation

### 4.1 Feature Selection (The Cleaning)

* **Input:** 50 Indicators (RSI, CCI, ADX, Aroon...).
* **Process:** Train RF every week.
* **Output:** Rank the features.
* **Action:** Drop the bottom 25 features. They are just adding noise and overfitting risk.

### 4.2 Regime Detection

* **Volatility Regime:** ATR and Bollinger Bands will be high importance.
* **Trend Regime:** SMA and ADX will be high importance.
* **Mean Reversion:** RSI and Stochastic will be high importance.
* **Signal:** Monitor the *Change* in Feature Importance over time to detect Regime Shifts.

---

## 5. Microstructure & HFT

HFTs use **Gradient Boosting (XGBoost/LightGBM)** which provides similar importance metrics (Gain).
They use it to prune their FPGA logic. If "Order Book Imbalance at Level 5" has Importance 0.001, they remove that logic gate to save nanoseconds.

---

## 6. Implementation

### 6.1 Python (Scikit-Learn)

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def get_feature_importance(df: pd.DataFrame, target_col='Target', top_n=5):
    """
    Train a Random Forest and return top N features.
    """
    df = df.dropna()
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Train RF
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
    rf.fit(X, y)
    
    # Extract Importance
    importances = rf.feature_importances_
    feature_names = X.columns
    
    # Create DataFrame
    feat_imp = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
    feat_imp = feat_imp.sort_values(by='Importance', ascending=False)
    
    return feat_imp.head(top_n)
```

### 6.2 Rust (SmartCore or Linfa)

Running a full Random Forest training loop in Rust is possible but heavy.
Typically, we train in Python and *export* the trees (JSON/ONNX) to Rust for inference.
But for calculate importance *live*, we might use a lighter tree library.

```rust
// Using the `smartcore` crate
use smartcore::ensemble::random_forest_classifier::RandomForestClassifier;
use smartcore::linalg::basic::matrix::DenseMatrix;

pub fn train_and_inspect(data: &DenseMatrix<f64>, targets: &Vec<f64>) -> Vec<f64> {
    let rf = RandomForestClassifier::fit(
        data,
        targets,
        Default::default() // Hyperparameters
    ).unwrap();
    
    // SmartCore doesn't expose Feature Importance directly in the struct easily
    // We would need to iterate the trees and sum the splits manually.
    
    // Pseudo-code for manual extraction:
    let mut importance = vec![0.0; data.ncols()];
    
    for tree in rf.iter_trees() {
        for node in tree.nodes() {
            if let Some(split_feature) = node.split_feature {
                let gain = node.impurity_decrease; // Assume calculated
                importance[split_feature] += gain * (node.samples / total_samples);
            }
        }
    }
    
    // Normalize
    let sum: f64 = importance.iter().sum();
    importance.iter().map(|&x| x / sum).collect()
}
```

---

## 7. Strategy: "The Dynamic Selector"

A Meta-Strategy.

**Rules:**

1. **Pool:** 10 diverse strategies (RSI, BB, MACD, etc.).
2. **Training:** Every weekend, train a Random Forest on the last 3 months of data using the signals of these 10 strategies as features.
3. **Selection:** Identify the Top 3 Strategies by Importance.
4. **Execution (Next Week):** Only take signals from those Top 3. Ignore the rest.

**Why it works:** It adapts to the market. In a choppy market, it selects Oscillators. In a trending market, it selects Trend Followers.

---

## 8. Conclusion

Random Forest Feature Importance is the ultimate **"BS Detector"**.
Traders often fall in love with complex indicators ("The 7-period inverse Fisher Transform of the RSI").
RF looks at the data and says: "This feature has 0.00 importance. It is useless."
It brings scientific rigour to the art of indicator selection.

---

### Final Stats

* **Type:** Meta-Indicator / Explainability
* **Input:** Matrix of Features ($X$) and Target ($y$)
* **Output:** Importance Scores (Sum to 1.0)
* **Best Market Condition:** All (It adapts)
* **Worst Market Condition:** Non-Stationary (Past importance $\neq$ Future importance)
* **Complexity:** High (Ensemble Learning)
