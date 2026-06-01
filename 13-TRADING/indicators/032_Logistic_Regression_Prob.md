# Indicator 032: Logistic Regression Probability - The Odds Maker

**"Don't tell me where the price is going. Tell me the probability."**

---

## 1. Executive Summary

**Logistic Regression** is the bridge between Linear Regression and Classification.
Linear Regression outputs a continuous number (e.g., predicted price = 105.3).
Logistic Regression outputs a **Probability between 0 and 1**.

* "What is the probability that the next candle will be Green?"
* Output: 0.75 (75%).

It transforms trading from a prediction game ("It will go up") to an odds game ("Use higher leverage because p=0.8").

---

## 2. Historical Context: The Logit Model

Developed by statisticians in the mid-20th century for biological assays (dose vs. survival), it was adopted by Quants to model binary outcomes.

* **Outcome 1:** Price Up.
* **Outcome 0:** Price Down.
It uses the **Sigmoid Function** to squash the linear output ($mx+c$) into the $[0, 1]$ range.

---

## 3. Mathematical Foundations

The core is the **Log-Odds** or Logit function.

### 3.1 The Equation

$$ P(Y=1) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x_1 + \dots + \beta_n x_n)}} $$

Where:

* $P(Y=1)$: Probability of the "Positive" class (Up Candle).
* $e$: Euler's number.
* $\beta$: Coefficients (Learned weights).
* $x$: Features (RSI, Slope, Volume, etc.).

### 3.2 The Decision Boundary

* If $P > 0.5$: Predict UP.
* If $P < 0.5$: Predict DOWN.
* **Edges:** $P > 0.8$ is a High Confidence prediction.

---

## 4. Signal Generation and Interpretation

### 4.1 Feature Selection

To predict the next candle, you need inputs.

* $x_1$: RSI(14).
* $x_2$: Price - SMA(20).
* $x_3$: Volume Ratio.

### 4.2 The Signal

* **Strong Buy:** $P > 0.7$.
* **Strong Sell:** $P < 0.3$.
* **Neutral:** $0.3 < P < 0.7$ (Too much uncertainty, do not trade).

### 4.3 Training Window

Unlike Linear Regression which works on a small window (20 bars), Logistic Regression needs a **Training Set** (e.g., 500-1000 bars) to learn the weights $\beta$ via Gradient Descent or Newton-Raphson.

---

## 5. Microstructure & HFT

HFTs use Logistic Regression for **Order Book Imbalance (OBI)** classification.

* Input: OBI, Trade Flow.
* Target: Will the Mid-Price tick UP in the next 100ms?
* Speed: Logistic Regression inference is extremely fast (just dot products and an exponential), making it suitable for FPGA implementation.

---

## 6. Implementation

### 6.1 Python (Scikit-Learn)

```python
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def train_logistic_model(df: pd.DataFrame, features=['RSI', 'Slope'], target_horizon=1):
    """
    Train a Logistic Regression to predict if Close(t+1) > Close(t).
    """
    df = df.dropna()
    
    # 1. Create Target
    df['Target'] = (df['Close'].shift(-target_horizon) > df['Close']).astype(int)
    
    # 2. Prepare X and y
    X = df[features].values
    y = df['Target'].values
    
    # 3. Scale Features (Critical for Logistic Regression)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. Train (using last 1000 bars)
    train_size = min(len(df), 1000)
    model = LogisticRegression(C=1e5) # Low regularization
    model.fit(X_scaled[-train_size:], y[-train_size:])
    
    return model, scaler

def predict_probability(model, scaler, current_features):
    """
    Return P(Up).
    """
    features_scaled = scaler.transform([current_features])
    probs = model.predict_proba(features_scaled)
    # probs returns [[P(0), P(1)]]
    return probs[0][1] # P(Up)
```

### 6.2 Rust (Online Gradient Descent)

We can train a Logistic Regression model **Online** (updating weights with every new candle) using Stochastic Gradient Descent (SGD).

$$ w_{new} = w_{old} + \eta (y - p) x $$

* $\eta$: Learning Rate.
* $y$: Actual outcome (1 or 0).
* $p$: Predicted probability.
* $x$: Feature vector.

```rust
pub struct OnlineLogisticRegression {
    weights: Vec<f64>,
    bias: f64,
    learning_rate: f64,
}

impl OnlineLogisticRegression {
    pub fn new(num_features: usize, learning_rate: f64) -> Self {
        Self {
            weights: vec![0.0; num_features],
            bias: 0.0,
            learning_rate,
        }
    }

    fn sigmoid(z: f64) -> f64 {
        1.0 / (1.0 + (-z).exp())
    }

    pub fn predict(&self, features: &[f64]) -> f64 {
        let mut z = self.bias;
        for (w, x) in self.weights.iter().zip(features.iter()) {
            z += w * x;
        }
        Self::sigmoid(z)
    }

    pub fn train(&mut self, features: &[f64], label: f64) {
        // label is 1.0 or 0.0
        let prediction = self.predict(features);
        let error = label - prediction;
        
        // Update Bias
        self.bias += self.learning_rate * error;
        
        // Update Weights
        for (w, x) in self.weights.iter_mut().zip(features.iter()) {
            *w += self.learning_rate * error * x;
        }
    }
}
```

---

## 7. Strategy: "The Probabilistic Filter"

**Rules:**

1. **Primary Signal:** MACD Crossover (Buy).
2. **Filter:** Logistic Regression Model trained on 5 features (RSI, Volatility, Slope, etc.).
3. **Condition:** If $P(Up) > 0.6$.
4. **Confirm:** Enter Trade.
5. **Reject:** If $P(Up) < 0.6$, ignore the MACD signal. It's a false positive.

**Why it works:** MACD is blind to context. The Logistic Regression model sees the broader picture (Volatility, Slope, RSI) and acts as a "Jury" to the MACD's "Accusation".

---

## 8. Conclusion

Logistic Regression is the gateway to "Real AI".
It stops the trader from thinking in absolutes ("It WILL happen") and forces them to think in probabilities ("It has a 62% chance").
While Simple, it is often more robust than Deep Neural Networks because it is less prone to Overfitting on noisy financial data.

---

### Final Stats

* **Type:** Supervised Learning / Classification
* **Input:** Vector of Features ($X$)
* **Output:** Probability ($0 \dots 1$)
* **Best Market Condition:** Stable Regimes (where historical correlations hold)
* **Worst Market Condition:** Regime Shifts (Model trained on Bull Market fails in Bear Market)
* **Complexity:** Medium (SGD)
