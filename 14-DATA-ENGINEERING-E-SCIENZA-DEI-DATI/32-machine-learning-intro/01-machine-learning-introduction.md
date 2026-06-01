# Machine Learning Fundamentals for Data Engineers and Security Professionals

## Table of Contents

1. [ML Fundamentals](#1-ml-fundamentals)
2. [Feature Engineering](#2-feature-engineering)
3. [Classical ML Algorithms](#3-classical-ml-algorithms)
4. [Deep Learning Basics](#4-deep-learning-basics)
5. [MLOps and Production](#5-mlops-and-production)
6. [ML for Cybersecurity](#6-ml-for-cybersecurity)
7. [ML Security](#7-ml-security)
8. [scikit-learn Deep Dive](#8-scikit-learn-deep-dive)
9. [Data Engineering for ML](#9-data-engineering-for-ml)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. ML Fundamentals

### Learning Paradigms

Machine learning systems learn patterns from data rather than following explicit programmatic rules. The paradigm under which a model learns determines what kinds of problems it can solve, what data it requires, and how it generalizes.

#### Supervised Learning

Supervised learning operates on labeled datasets where each input example is paired with a known output. The model learns a mapping function `f: X -> Y` that generalizes to unseen inputs.

**Classification** predicts discrete categorical labels. Binary classification (spam/not-spam, malicious/benign) and multi-class classification (malware family identification, network protocol classification) are the two primary forms. Multi-label classification assigns multiple labels simultaneously (a network packet can be both "encrypted" and "outbound").

**Regression** predicts continuous numerical values. Examples include predicting network latency, estimating data pipeline processing time, or forecasting resource utilization. Regression models output a real-valued number rather than a class membership.

```python
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.datasets import make_classification, make_regression

# Regression: predict continuous values
X_reg, y_reg = make_regression(n_samples=1000, n_features=10, noise=0.1)
reg_model = LinearRegression().fit(X_reg, y_reg)

# Classification: predict discrete labels
X_clf, y_clf = make_classification(n_samples=1000, n_features=20, n_classes=2)
clf_model = LogisticRegression(max_iter=1000).fit(X_clf, y_clf)
```

#### Unsupervised Learning

Unsupervised learning discovers structure in unlabeled data. There is no target variable; the model identifies patterns, groupings, or representations autonomously.

**Clustering** groups similar data points together. K-Means partitions data into k clusters based on centroid distance. DBSCAN finds density-connected regions without requiring a predefined cluster count. Hierarchical clustering builds a dendrogram of nested groupings. In security contexts, clustering groups similar network flows, identifies communities of related domains, or segments user behavior profiles.

**Dimensionality Reduction** compresses high-dimensional data while preserving meaningful structure. PCA (Principal Component Analysis) projects data onto orthogonal axes of maximum variance. t-SNE and UMAP produce nonlinear embeddings suitable for visualization. Autoencoders learn compressed representations through neural network bottlenecks. These techniques are essential when working with high-dimensional feature spaces (thousands of network features, log fields, or packet attributes).

**Anomaly Detection** identifies data points that deviate significantly from the majority distribution. Isolation Forest, One-Class SVM, and statistical methods (Gaussian mixture models, Mahalanobis distance) flag outliers. This is the foundational technique for intrusion detection, fraud detection, and system health monitoring.

```python
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest

# Clustering network flows
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(network_features)

# Dimensionality reduction for visualization
pca = PCA(n_components=2)
reduced = pca.fit_transform(high_dim_features)

# Anomaly detection
iso_forest = IsolationForest(contamination=0.05, random_state=42)
anomaly_labels = iso_forest.fit_predict(system_metrics)
# -1 = anomaly, 1 = normal
```

#### Reinforcement Learning

Reinforcement learning (RL) trains an agent to make sequential decisions by maximizing cumulative reward through interaction with an environment. The agent observes state, takes actions, receives rewards, and updates its policy. RL applies to adaptive security systems (dynamically adjusting firewall rules), automated penetration testing (exploring attack surfaces), and resource allocation in data pipelines.

Key concepts: policy (maps states to actions), value function (expected future reward), exploration vs exploitation (trying new actions vs leveraging known good actions), Markov Decision Processes (formal framework for sequential decision-making).

#### Semi-Supervised Learning

Semi-supervised learning exploits a small labeled dataset alongside a large unlabeled corpus. This is realistic for security applications where labeling requires expensive expert annotation. Label propagation, self-training (using model predictions as pseudo-labels), and consistency regularization (enforcing invariance under data augmentations) are common techniques. A malware analyst might label 500 samples; semi-supervised methods leverage 50,000 unlabeled binaries to improve the classifier.

#### Self-Supervised Learning

Self-supervised learning generates supervisory signals from the data itself through pretext tasks. Masked language modeling (predict masked tokens), contrastive learning (pull similar representations together, push dissimilar ones apart), and next-token prediction are foundational self-supervised objectives. Foundation models (BERT, GPT, ViT) are pretrained with self-supervision, then fine-tuned on downstream tasks. For security, self-supervised pretraining on network logs or system call sequences can produce embeddings that transfer effectively to detection tasks.

### Bias-Variance Tradeoff

Every predictive model navigates the tension between bias and variance.

**Bias** measures how far the model's average predictions deviate from the true values. High bias indicates the model is too simple to capture the underlying pattern (underfitting). A linear model applied to a nonlinear relationship exhibits high bias.

**Variance** measures how much predictions fluctuate across different training sets. High variance indicates the model is too sensitive to the specific training data (overfitting). A deep decision tree with no depth limit memorizes training noise.

The total error decomposes as: `Error = Bias^2 + Variance + Irreducible Noise`

Optimal model complexity balances both. Regularization (L1/L2 penalties, dropout, early stopping) trades increased bias for reduced variance. Ensemble methods (bagging reduces variance, boosting reduces bias) address both sides.

### Overfitting and Underfitting

**Overfitting** manifests as low training error but high validation/test error. The model memorized noise rather than learning the signal. Symptoms: training accuracy near 100% while validation accuracy plateaus or degrades. Countermeasures: regularization, data augmentation, early stopping, simpler architectures, more training data.

**Underfitting** manifests as high error on both training and validation sets. The model lacks capacity to represent the underlying relationship. Symptoms: training loss fails to decrease meaningfully. Countermeasures: more complex model, additional features, longer training, reduced regularization.

### Cross-Validation

Cross-validation provides robust estimates of model generalization by systematically rotating through different train/test partitions.

**k-Fold Cross-Validation** splits data into k equal folds. The model trains on k-1 folds and evaluates on the held-out fold, rotating k times. The final metric averages across all folds. k=5 or k=10 are standard choices.

**Stratified k-Fold** preserves class proportions in each fold, critical for imbalanced security datasets where attack samples may constitute <1% of traffic.

**Time Series Split** respects temporal ordering. Training always precedes validation chronologically, preventing data leakage from future observations. Essential for any time-dependent security or pipeline monitoring data.

**Leave-One-Out (LOO)** uses n-1 samples for training, evaluating on each single sample. Computationally expensive but maximizes training data utilization for very small datasets.

**Group k-Fold** ensures all samples from a group (e.g., same user, same session, same source IP) appear in either training or validation, never both. Prevents information leakage when samples within a group are correlated.

```python
from sklearn.model_selection import (
    KFold, StratifiedKFold, TimeSeriesSplit, GroupKFold, cross_val_score
)
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)

# Standard k-fold
kf = KFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=kf, scoring='f1_weighted')

# Stratified for imbalanced data
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=skf, scoring='f1_weighted')

# Time series (no shuffling, temporal order preserved)
tscv = TimeSeriesSplit(n_splits=5)
scores = cross_val_score(model, X, y, cv=tscv, scoring='f1_weighted')
```

### Train / Validation / Test Splits

The three-way split serves distinct purposes:

- **Training set** (60-80%): Model learns parameters from this data.
- **Validation set** (10-20%): Used during development for hyperparameter tuning and model selection. Can be replaced by cross-validation.
- **Test set** (10-20%): Held out entirely until final evaluation. Touched exactly once to report unbiased performance. Never used for any decision-making during development.

Data leakage — where information from the test set inadvertently influences training — invalidates all performance estimates. Common leakage sources: fitting scalers on the full dataset before splitting, using future information in temporal data, including correlated samples across splits.

---

## 2. Feature Engineering

Feature engineering transforms raw data into representations that machine learning algorithms can exploit effectively. The quality of features often determines model performance more than algorithm choice.

### Feature Types

**Numerical Features** are continuous or discrete values (packet sizes, request latency, byte counts, port numbers). They can be used directly by most algorithms but may require scaling.

**Categorical Features** represent discrete classes (protocol type, HTTP method, user agent category, country code). They require encoding before most algorithms can consume them.

**Text Features** are unstructured strings (log messages, URLs, email bodies, command-line arguments). They require tokenization, vectorization (TF-IDF, word embeddings, subword tokenization), or direct ingestion by language models.

**Temporal Features** encode time information (timestamp, day-of-week, hour-of-day, time-since-last-event, rolling averages). Cyclical encoding (sine/cosine transforms) preserves periodicity.

**Geospatial Features** represent locations (IP geolocation coordinates, ASN, region codes). Distance calculations, clustering of geographic origins, and regional behavior baselines leverage these.

### Encoding Strategies

#### One-Hot Encoding

Creates binary columns for each category. Suitable when cardinality is low (<50 categories) and no ordinal relationship exists.

```python
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

# Protocol types: TCP, UDP, ICMP
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
encoded = encoder.fit_transform(df[['protocol']])
# Result: [1,0,0], [0,1,0], [0,0,1]
```

#### Ordinal Encoding

Assigns integers based on inherent ordering. Appropriate for severity levels (low=0, medium=1, high=2, critical=3) or risk scores.

```python
from sklearn.preprocessing import OrdinalEncoder

severity_order = [['low', 'medium', 'high', 'critical']]
encoder = OrdinalEncoder(categories=severity_order)
encoded = encoder.fit_transform(df[['severity']])
```

#### Target Encoding

Replaces categories with the mean of the target variable for that category. Handles high-cardinality features (IP addresses, user agents) without dimension explosion. Requires careful regularization to prevent overfitting — use leave-one-out or additive smoothing.

```python
from sklearn.preprocessing import TargetEncoder

# High-cardinality: source_ip -> mean(is_malicious)
encoder = TargetEncoder(smooth='auto')
encoded = encoder.fit_transform(df[['source_ip']], df['is_malicious'])
```

#### Binary Encoding

Converts category indices to binary representation. Produces log2(n) columns instead of n columns. Good middle ground between one-hot (too many columns) and ordinal (imposes false ordering) for medium-cardinality features.

### Scaling Methods

**Standard Scaling (Z-score)** centers features to mean=0 and scales to std=1. Assumes approximately Gaussian distribution. Sensitive to outliers.

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

# Standard: (x - mean) / std
standard = StandardScaler()

# Min-Max: scales to [0, 1]
minmax = MinMaxScaler()

# Robust: uses median and IQR, outlier-resistant
robust = RobustScaler()
```

**Min-Max Scaling** linearly transforms features to [0, 1]. Preserves zero entries in sparse data. Appropriate when the feature has known bounded ranges.

**Robust Scaling** uses median and interquartile range instead of mean and standard deviation. Preferred for security data where outliers (attack traffic spikes) are common and meaningful — standard scaling would distort the majority distribution.

### Feature Selection

#### Filter Methods

Statistical tests evaluate each feature independently against the target. Fast but ignores feature interactions.

- Mutual information: measures nonlinear dependence between feature and target
- Chi-squared test: categorical features vs categorical target
- ANOVA F-test: numerical features vs categorical target
- Correlation coefficient: numerical features vs numerical target

```python
from sklearn.feature_selection import (
    mutual_info_classif, SelectKBest, f_classif
)

# Select top 20 features by mutual information
selector = SelectKBest(score_func=mutual_info_classif, k=20)
X_selected = selector.fit_transform(X, y)
selected_mask = selector.get_support()
```

#### Wrapper Methods

Evaluate feature subsets by training the actual model. Computationally expensive but captures interactions.

- Recursive Feature Elimination (RFE): iteratively removes least important features
- Forward selection: greedily adds features that improve performance
- Backward elimination: greedily removes features that least harm performance

```python
from sklearn.feature_selection import RFE
from sklearn.ensemble import GradientBoostingClassifier

estimator = GradientBoostingClassifier(n_estimators=100, random_state=42)
rfe = RFE(estimator, n_features_to_select=15, step=1)
rfe.fit(X, y)
selected_features = X.columns[rfe.support_]
```

#### Embedded Methods

Feature importance is computed as part of model training. Combines efficiency of filters with interaction-awareness of wrappers.

- L1 regularization (Lasso): drives irrelevant feature coefficients to exactly zero
- Tree-based importance: split-based (Gini, information gain) or permutation-based
- Elastic Net: combines L1 and L2 penalties

### Feature Stores

Feature stores centralize feature computation, storage, and serving for ML systems. They solve the "training-serving skew" problem where feature computation logic differs between training and inference.

**Feast** (Feature Store): open-source, supports offline (batch) and online (low-latency) feature retrieval. Integrates with data warehouses (BigQuery, Redshift, Snowflake) for offline store and Redis/DynamoDB for online store.

**Tecton**: managed feature platform with real-time feature computation, streaming feature pipelines, and built-in monitoring for feature freshness and data quality.

Key concepts:
- **Feature definitions**: declarative specifications of how features are computed
- **Materialization**: pre-computing and storing feature values for serving
- **Point-in-time correctness**: ensuring training features reflect only data available at prediction time, preventing leakage
- **Feature freshness**: how recently features were computed (critical for real-time security detection)

### Automated Feature Engineering

**Featuretools** generates features automatically through Deep Feature Synthesis (DFS). Given entity relationships, it creates features by stacking aggregation and transformation primitives.

```python
import featuretools as ft

# Define entity set from relational data
es = ft.EntitySet(id="network_sessions")
es.add_dataframe(dataframe=sessions_df, dataframe_name="sessions",
                 index="session_id", time_index="timestamp")
es.add_dataframe(dataframe=packets_df, dataframe_name="packets",
                 index="packet_id", time_index="timestamp")
es.add_relationship("sessions", "session_id", "packets", "session_id")

# Auto-generate features
feature_matrix, feature_defs = ft.dfs(
    entityset=es,
    target_dataframe_name="sessions",
    max_depth=2,
    agg_primitives=["count", "mean", "std", "max", "min", "sum"],
    trans_primitives=["hour", "day", "weekday", "month"]
)
```

---

## 3. Classical ML Algorithms

### Linear Regression

Models the target as a linear combination of features: `y = w^T x + b`. Minimizes mean squared error. Assumes linear relationship, independent errors, homoscedasticity. Fast to train, interpretable coefficients. Regularized variants: Ridge (L2), Lasso (L1), Elastic Net (L1+L2).

### Logistic Regression

Despite the name, it is a classification algorithm. Applies sigmoid function to linear combination: `P(y=1|x) = sigmoid(w^T x + b)`. Outputs calibrated probabilities. Strong baseline for binary classification. Regularization via C parameter (inverse regularization strength). Multi-class extension: one-vs-rest or multinomial (softmax).

Use when: features have linear relationship with log-odds of the target, need probability calibration, need interpretable coefficients, high-dimensional sparse data (text features with L1 regularization).

### Decision Trees

Recursively partition feature space through binary splits. Each internal node tests a feature threshold; leaves predict class (classification) or value (regression). Split criteria: Gini impurity, entropy (information gain), or MSE reduction.

Advantages: handles nonlinear relationships, no scaling required, built-in feature importance, interpretable. Disadvantages: prone to overfitting without pruning, high variance, axis-aligned splits struggle with diagonal decision boundaries.

```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV

dt = DecisionTreeClassifier(random_state=42)
param_grid = {
    'max_depth': [3, 5, 7, 10, None],
    'min_samples_split': [2, 5, 10, 20],
    'min_samples_leaf': [1, 2, 5, 10]
}
grid = GridSearchCV(dt, param_grid, cv=5, scoring='f1_weighted', n_jobs=-1)
grid.fit(X_train, y_train)
```

### Random Forests

Ensemble of decision trees trained on bootstrap samples (bagging) with random feature subsets at each split. Reduces variance while maintaining low bias. Feature importance via mean decrease in impurity or permutation importance.

Hyperparameters: `n_estimators` (number of trees, more is generally better up to diminishing returns), `max_depth` (per-tree depth limit), `max_features` (features considered per split — sqrt(n) for classification, n/3 for regression are defaults), `min_samples_leaf`.

Use when: tabular data with mixed feature types, need robust performance without extensive tuning, want feature importance rankings, need to handle missing values gracefully (via surrogate splits in some implementations).

### Gradient Boosting

Sequentially builds weak learners (typically shallow trees) where each new tree corrects the residual errors of the ensemble so far. Additive model: prediction = sum of all tree contributions.

**XGBoost**: optimized gradient boosting with regularization (L1/L2 on leaf weights), histogram-based splits, built-in handling of missing values, parallel tree construction. Dominant on structured/tabular data competitions.

**LightGBM**: leaf-wise growth (vs level-wise), Gradient-based One-Side Sampling (GOSS), Exclusive Feature Bundling (EFB). Faster training on large datasets, lower memory usage. Excellent for high-dimensional sparse features.

**CatBoost**: native handling of categorical features (ordered target encoding), ordered boosting (combats prediction shift / target leakage), symmetric trees. Minimal preprocessing required.

```python
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier

# XGBoost
xgb_model = xgb.XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,      # L1
    reg_lambda=1.0,     # L2
    eval_metric='logloss',
    early_stopping_rounds=50,
    random_state=42
)
xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

# LightGBM
lgb_model = lgb.LGBMClassifier(
    n_estimators=500,
    num_leaves=31,
    learning_rate=0.05,
    feature_fraction=0.8,
    bagging_fraction=0.8,
    bagging_freq=5,
    random_state=42
)
lgb_model.fit(X_train, y_train,
              eval_set=[(X_val, y_val)],
              callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])

# CatBoost (handles categoricals natively)
cat_model = CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.05,
    cat_features=['protocol', 'service', 'flag'],
    random_state=42,
    verbose=0
)
cat_model.fit(X_train, y_train, eval_set=(X_val, y_val))
```

### Support Vector Machines (SVM)

Find the hyperplane that maximizes the margin between classes. Kernel trick maps data into higher-dimensional space where linear separation is possible. Kernels: linear (high-dimensional sparse data), RBF (general nonlinear), polynomial.

Effective in high-dimensional spaces (text classification, malware feature vectors). Memory-intensive for large datasets (O(n^2) kernel matrix). Does not scale well beyond ~100k samples without approximations (SGD-based linear SVM, Nystroem approximation).

### K-Nearest Neighbors (KNN)

Non-parametric: stores training data and classifies new points by majority vote of k nearest neighbors. Distance metrics: Euclidean, Manhattan, Minkowski, cosine similarity.

Advantages: no training phase, naturally handles multi-class, adapts to arbitrary decision boundaries. Disadvantages: slow inference (O(n) per query without spatial indexing), curse of dimensionality (distances become meaningless in high dimensions), requires feature scaling.

### Naive Bayes

Applies Bayes theorem with strong independence assumption between features. Variants: Gaussian (continuous features), Multinomial (count features, text), Bernoulli (binary features).

Fast training and prediction. Excellent baseline for text classification (spam filtering, log message categorization). Despite the "naive" independence assumption, often competitive when features are approximately conditionally independent given the class.

### Ensemble Methods

**Bagging** (Bootstrap Aggregating): train multiple models on bootstrap samples, aggregate predictions (voting or averaging). Reduces variance. Random Forest is bagging applied to decision trees with random feature subsets.

**Boosting**: sequentially train models, each focusing on errors of previous models. Reduces bias. AdaBoost, Gradient Boosting, XGBoost, LightGBM, CatBoost.

**Stacking**: train base models, then a meta-learner on their predictions. Combines diverse models (tree-based + linear + neural) to capture different aspects of the data.

### Hyperparameter Tuning

**Grid Search**: exhaustive evaluation of all parameter combinations. Reliable but exponentially expensive with parameter count.

**Random Search**: samples random parameter combinations. Often more efficient than grid search because not all parameters are equally important — random search explores more values of the most impactful parameters.

**Bayesian Optimization** (Optuna, Hyperopt): builds a surrogate model (Gaussian Process, Tree-structured Parzen Estimator) of the objective function. Intelligently selects next parameters to evaluate based on expected improvement. Far more efficient than random search for expensive evaluations.

```python
import optuna

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
    }
    model = xgb.XGBClassifier(**params, random_state=42, eval_metric='logloss')
    scores = cross_val_score(model, X, y, cv=5, scoring='f1_weighted', n_jobs=-1)
    return scores.mean()

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
best_params = study.best_params
```

### When to Use Which Algorithm

| Scenario | Recommended Algorithm |
|----------|----------------------|
| Tabular data, general purpose | Gradient Boosting (LightGBM/XGBoost) |
| High-dimensional sparse (text) | Logistic Regression + L1, Naive Bayes |
| Need probability calibration | Logistic Regression, calibrated ensemble |
| Small dataset (<1000 samples) | SVM (RBF), KNN, Random Forest |
| Interpretability required | Decision Tree, Logistic Regression, Linear models |
| Streaming/online learning | SGD-based models, Online Random Forest |
| Anomaly detection | Isolation Forest, One-Class SVM |
| Mixed feature types | CatBoost, Random Forest |

---

## 4. Deep Learning Basics

### Neural Network Architecture

A neural network is a composition of parameterized differentiable functions (layers). Each layer applies a linear transformation `z = Wx + b` followed by a nonlinear activation function `a = f(z)`. Stacking layers creates hierarchical representations where earlier layers capture low-level features and deeper layers capture abstract concepts.

**Input layer**: dimensionality matches feature count.
**Hidden layers**: learned intermediate representations. Width (neurons per layer) and depth (number of layers) determine model capacity.
**Output layer**: dimensionality matches the prediction target. Sigmoid for binary classification, softmax for multi-class, linear for regression.

### Activation Functions

Activation functions introduce nonlinearity. Without them, stacked linear layers collapse into a single linear transformation.

- **ReLU** `max(0, x)`: default choice. Fast computation, avoids vanishing gradients for positive values. Dying neuron problem (permanently zero output) addressed by variants.
- **Leaky ReLU** `max(0.01x, x)`: small gradient for negative inputs prevents dead neurons.
- **GELU** (Gaussian Error Linear Unit): smooth approximation to ReLU. Default in Transformers (BERT, GPT).
- **Sigmoid** `1/(1+e^-x)`: outputs in (0,1). Used in output layer for binary classification. Suffers from vanishing gradients in hidden layers.
- **Tanh** `(e^x - e^-x)/(e^x + e^-x)`: outputs in (-1,1). Zero-centered, preferred over sigmoid in hidden layers when ReLU is not suitable.
- **Swish/SiLU** `x * sigmoid(x)`: smooth, non-monotonic. Used in EfficientNet, modern architectures.

### Backpropagation

Backpropagation computes gradients of the loss with respect to each parameter using the chain rule. Forward pass computes predictions; backward pass propagates error gradients from output to input layers. Automatic differentiation frameworks (PyTorch autograd, TensorFlow GradientTape) implement this efficiently.

```python
import torch
import torch.nn as nn

class MalwareClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim=256, num_classes=10):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, num_classes)
        )

    def forward(self, x):
        return self.network(x)

model = MalwareClassifier(input_dim=256, num_classes=10)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)

# Training loop
for epoch in range(100):
    optimizer.zero_grad()
    outputs = model(X_train_tensor)
    loss = criterion(outputs, y_train_tensor)
    loss.backward()   # backpropagation
    optimizer.step()  # parameter update
```

### Optimizers

**SGD** (Stochastic Gradient Descent): basic gradient descent with optional momentum. Momentum accumulates gradient history to accelerate convergence and dampen oscillations. With proper learning rate scheduling, often achieves the best final generalization.

**Adam** (Adaptive Moment Estimation): maintains per-parameter adaptive learning rates using first and second moment estimates of gradients. Converges faster than SGD in early training. Default choice for many applications.

**AdamW**: decouples weight decay from the adaptive learning rate mechanism. Proper implementation of L2 regularization for Adam. Preferred over Adam for training Transformers and modern architectures.

Learning rate scheduling: warmup (linearly increase LR at start), cosine annealing (smoothly decay LR), step decay (reduce LR at fixed epochs), OneCycleLR (super-convergence with high max LR).

### Regularization Techniques

**Dropout**: randomly zeros activations with probability p during training. Forces redundancy in learned representations. Typical values: 0.1-0.5. Disabled during inference.

**Batch Normalization**: normalizes layer inputs to zero mean and unit variance per mini-batch. Stabilizes training, allows higher learning rates, provides mild regularization. Applied between linear transformation and activation.

**Weight Decay**: adds penalty proportional to parameter magnitude to the loss. Equivalent to L2 regularization (mathematically identical for SGD, differs for adaptive optimizers — hence AdamW).

**Early Stopping**: monitors validation loss and stops training when it stops improving. Prevents overfitting by finding the optimal training duration.

**Data Augmentation**: artificially expands training data through transformations. Domain-specific: image rotations/flips, text paraphrasing, network traffic time-shifting.

### Convolutional Neural Networks (CNNs)

CNNs exploit spatial structure through local receptive fields, weight sharing, and hierarchical feature extraction. Convolutional layers apply learned filters across spatial dimensions. Pooling layers downsample spatial resolution. Originally designed for images but applicable to any grid-structured data (spectrograms of network traffic, binary visualization of executables).

Architecture patterns: VGG (deep stacks of 3x3 convolutions), ResNet (skip connections enabling very deep networks), EfficientNet (compound scaling of depth, width, resolution).

### Recurrent Networks (RNN/LSTM/GRU)

Process sequential data by maintaining hidden state across timesteps. Standard RNNs suffer from vanishing gradients over long sequences.

**LSTM** (Long Short-Term Memory): gating mechanism (forget gate, input gate, output gate) controls information flow. Cell state provides long-range memory pathway. Effective for sequences up to ~500 timesteps.

**GRU** (Gated Recurrent Unit): simplified gating (reset gate, update gate). Fewer parameters than LSTM, often comparable performance. Faster training.

Applications in security: system call sequence analysis, network session modeling, log sequence classification.

### Transformers

The dominant architecture for sequences and increasingly for other modalities. Based entirely on attention mechanisms, no recurrence.

**Self-Attention**: each position attends to all other positions in the sequence. Computes attention weights: `Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V`. Captures long-range dependencies in O(1) sequential steps (vs O(n) for RNNs).

**Multi-Head Attention**: runs multiple attention heads in parallel, each learning different relationship patterns. Concatenates and projects outputs.

**Position Encoding**: since attention is permutation-invariant, positional information is injected via sinusoidal encodings or learned position embeddings. Rotary Position Embedding (RoPE) encodes relative positions.

**Transformer Encoder** (BERT-style): bidirectional context, used for classification, embedding generation. **Transformer Decoder** (GPT-style): autoregressive, causal masking, used for generation.

```python
import torch
import torch.nn as nn

class SecurityLogTransformer(nn.Module):
    def __init__(self, vocab_size, d_model=256, nhead=8, num_layers=4,
                 num_classes=5, max_seq_len=512):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = nn.Embedding(max_seq_len, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model*4,
            dropout=0.1, activation='gelu', batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, x):
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0)
        x = self.embedding(x) + self.pos_encoding(positions)
        x = self.transformer(x)
        x = x.mean(dim=1)  # global average pooling
        return self.classifier(x)
```

### Transfer Learning

Pretrained models encode general knowledge that transfers to downstream tasks. Fine-tuning adapts pretrained weights to specific domains with limited labeled data.

Strategy: freeze early layers (general features), fine-tune later layers (task-specific features). Learning rate: use smaller LR for pretrained layers, larger LR for new task-specific layers. For security applications, pretrain on large corpora of logs/traffic, then fine-tune on specific detection tasks.

---

## 5. MLOps and Production

### Model Training Pipeline

A production training pipeline encompasses data ingestion, validation, preprocessing, training, evaluation, and registration — all automated, versioned, and reproducible.

```
Data Source → Validation → Preprocessing → Training → Evaluation → Registry → Serving
     ↑                                                      |
     └──────────── Monitoring & Retraining Triggers ────────┘
```

Key requirements:
- **Reproducibility**: identical inputs produce identical models. Pin random seeds, version data, version code, version environment (Docker).
- **Idempotency**: re-running the pipeline with same inputs produces same outputs without side effects.
- **Observability**: every step logs metrics, artifacts, and lineage information.

### Experiment Tracking

**MLflow**: open-source platform for experiment tracking, model packaging, and deployment. Tracks parameters, metrics, artifacts (model files, plots) per run. Model registry with staging/production lifecycle stages.

```python
import mlflow
import mlflow.sklearn

mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("intrusion-detection-v2")

with mlflow.start_run(run_name="xgboost-baseline"):
    mlflow.log_params({
        "n_estimators": 500,
        "max_depth": 6,
        "learning_rate": 0.05
    })

    model = xgb.XGBClassifier(n_estimators=500, max_depth=6, learning_rate=0.05)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    f1 = f1_score(y_test, predictions, average='weighted')
    precision = precision_score(y_test, predictions, average='weighted')
    recall = recall_score(y_test, predictions, average='weighted')

    mlflow.log_metrics({"f1": f1, "precision": precision, "recall": recall})
    mlflow.sklearn.log_model(model, "model", registered_model_name="ids-xgboost")
```

**Weights & Biases (W&B)**: hosted experiment tracking with rich visualization, hyperparameter sweep orchestration, artifact versioning, and collaborative features. Integrates with PyTorch, TensorFlow, scikit-learn, and most ML frameworks.

### Model Registry

Central repository of trained model versions with metadata, lineage, and lifecycle management.

- **Version control**: each registered model has monotonically increasing version numbers
- **Stage transitions**: None → Staging → Production → Archived
- **Approval workflows**: require review before promoting to production
- **Metadata**: training data hash, performance metrics, training parameters, deployment constraints (latency budget, memory limit)

### Model Serving

**FastAPI**: lightweight Python framework for building model inference APIs. Async support, automatic OpenAPI docs, Pydantic validation.

```python
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="Intrusion Detection API")
model = joblib.load("models/ids_model.joblib")
scaler = joblib.load("models/scaler.joblib")

class NetworkFeatures(BaseModel):
    duration: float
    src_bytes: int
    dst_bytes: int
    count: int
    srv_count: int
    protocol_type: str
    service: str
    flag: str

@app.post("/predict")
async def predict(features: NetworkFeatures):
    # Feature engineering would go here
    X = scaler.transform(np.array([[
        features.duration, features.src_bytes,
        features.dst_bytes, features.count, features.srv_count
    ]]))
    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0].max()
    return {
        "prediction": int(prediction),
        "label": "malicious" if prediction == 1 else "benign",
        "confidence": float(probability)
    }
```

**TorchServe**: PyTorch model serving with multi-model management, batching, metrics, and A/B testing support.

**TF Serving**: TensorFlow model serving via gRPC/REST with model versioning and automatic batching.

**Triton Inference Server**: NVIDIA's multi-framework serving platform. Supports TensorFlow, PyTorch, ONNX, TensorRT, and custom backends. Dynamic batching, model ensembles, GPU scheduling.

### Deployment Strategies

**Shadow Deployment**: new model runs in parallel with production model. Both receive real traffic, but only the current production model's predictions are served to users. New model's predictions are logged for comparison. Zero risk to production.

**A/B Testing**: split traffic between models (e.g., 90/10). Measure statistical significance of metric differences. Requires sufficient traffic volume and careful metric selection.

**Canary Deployment**: gradually shift traffic from old to new model (1% → 5% → 25% → 50% → 100%). Automated rollback if error rate exceeds threshold.

**Blue/Green**: maintain two identical environments. Switch DNS/load balancer from blue (old) to green (new). Instant rollback by switching back.

### Monitoring in Production

**Data Drift**: statistical properties of input features change over time. Detection: KS test, PSI (Population Stability Index), Jensen-Shannon divergence between reference and current distributions. Example: attacker tactics evolve, shifting feature distributions.

**Concept Drift**: the relationship between features and target changes. Model accuracy degrades even if input distribution remains stable. Detection: monitor prediction confidence, actual vs predicted distributions, performance metrics on labeled samples.

**Performance Degradation Monitoring**:
- Track prediction latency (p50, p95, p99)
- Monitor prediction distribution shifts
- Alert on accuracy/F1 drops (requires delayed ground truth labels)
- Track feature coverage (percentage of features available at inference time)

```python
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset

# Compare current production data against training reference
column_mapping = ColumnMapping(
    target='label',
    prediction='prediction',
    numerical_features=['duration', 'src_bytes', 'dst_bytes'],
    categorical_features=['protocol', 'service']
)

report = Report(metrics=[DataDriftPreset(), TargetDriftPreset()])
report.run(reference_data=reference_df, current_data=production_df,
           column_mapping=column_mapping)
report.save_html("drift_report.html")
```

---

## 6. ML for Cybersecurity

### Anomaly Detection for Intrusion Detection

Network intrusion detection systems (NIDS) leverage ML to identify malicious traffic that signature-based systems miss. Anomaly-based approaches model normal behavior and flag deviations.

**Statistical Baseline Models**: establish normal distributions for traffic features (packet rate, byte volume, connection duration). Z-score thresholds flag outliers. Simple but interpretable.

**Isolation Forest**: isolates anomalies by random recursive partitioning. Anomalies require fewer partitions (shorter path length) to isolate. Effective for high-dimensional network feature spaces without requiring explicit density estimation.

**Autoencoder-based Detection**: train autoencoder to reconstruct normal traffic. High reconstruction error indicates anomalous input. Deep autoencoders capture nonlinear normal behavior patterns that statistical methods miss.

```python
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest

class TrafficAutoencoder(nn.Module):
    def __init__(self, input_dim, latent_dim=32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim)
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

# Train on NORMAL traffic only
model = TrafficAutoencoder(input_dim=41)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

# Inference: high reconstruction error = anomaly
def detect_anomaly(model, sample, threshold):
    with torch.no_grad():
        reconstruction = model(sample)
        error = torch.mean((sample - reconstruction) ** 2, dim=1)
    return error > threshold
```

### Malware Classification

ML classifiers identify malware families from static and dynamic features.

**Static Features**: PE header fields, section entropy, import table hashes, string distributions, byte n-grams, opcode sequences.

**Dynamic Features**: API call sequences, registry modifications, network connections, file operations, mutex creation (from sandboxed execution).

Gradient boosting on engineered features achieves high accuracy. Deep learning on raw bytes (1D CNNs, Transformers) can classify without manual feature engineering but requires more data.

### Phishing URL Detection

Feature engineering extracts signals from URL structure without requiring page content:

- URL length, number of dots, special character counts
- Domain age, registration duration, WHOIS privacy
- Presence of IP address in URL
- Suspicious TLD usage
- Subdomain depth and length
- Entropy of URL components
- Levenshtein distance to known legitimate domains (typosquatting detection)
- Certificate transparency log presence

### User and Entity Behavior Analytics (UEBA)

Models baseline behavior per user/entity and detects deviations:

- Login time patterns (unusual hours)
- Resource access patterns (accessing new systems)
- Data movement anomalies (unusual download volumes)
- Geographic impossibilities (login from different countries within impossible travel time)
- Privilege escalation patterns
- Peer group deviation (user behaves differently from role peers)

Implementation: compute feature vectors per time window per entity. Train per-entity or per-peer-group models. Score deviations from baseline.

### Network Traffic Classification

ML identifies applications, protocols, and threats from traffic metadata:

- Flow-level features: duration, packet count, byte count, inter-arrival times
- Statistical features: min/max/mean/std of packet sizes per flow
- Behavioral features: connection patterns, periodicity, burst patterns
- Encrypted traffic classification: TLS handshake features, certificate attributes, packet size distributions (cannot inspect payload)

### Log Analysis with ML

Transform unstructured log data into ML-consumable features:

- Log parsing: extract structured fields using drain, spell, or learned parsers
- Template mining: identify log message templates, count occurrences per window
- Sequence modeling: LSTM/Transformer on log event sequences to predict next event; anomalous events have low predicted probability
- Clustering: group similar log patterns, identify new/rare clusters

### NLP for Threat Intelligence

Natural language processing extracts structured threat intelligence from unstructured text:

- Named Entity Recognition (NER): extract IOCs (IPs, domains, hashes, CVE IDs) from reports
- Relation extraction: link threat actors to TTPs, malware to C2 infrastructure
- Document classification: categorize threat reports by actor, campaign, industry
- Summarization: condense lengthy reports into actionable intelligence

### Adversarial ML in Security Contexts

Attackers specifically craft inputs to evade ML-based detection:

- **Evasion attacks**: modify malware to reduce detection probability while preserving functionality (padding, code transposition, dead code insertion)
- **Concept drift exploitation**: gradually shift behavior to train defenders' models toward a new "normal" before launching attacks
- **Poisoning training data**: inject mislabeled samples into honeypots or threat feeds that defenders use for retraining

---

## 7. ML Security

### Adversarial Examples

Carefully crafted perturbations to model inputs that cause misclassification while remaining imperceptible (for images) or preserving semantics (for other domains).

#### Fast Gradient Sign Method (FGSM)

Single-step attack: perturb input in the direction of the loss gradient.

```python
def fgsm_attack(model, x, y_true, epsilon=0.01):
    """Generate adversarial example using FGSM."""
    x_adv = x.clone().detach().requires_grad_(True)
    output = model(x_adv)
    loss = nn.CrossEntropyLoss()(output, y_true)
    loss.backward()

    # Perturb in gradient direction
    perturbation = epsilon * x_adv.grad.sign()
    x_adv = x_adv + perturbation
    return x_adv.detach()
```

#### Projected Gradient Descent (PGD)

Iterative version of FGSM. Takes multiple smaller steps, projecting back onto the epsilon-ball after each step. Stronger than FGSM. Considered a first-order adversary — models robust to PGD are robust to all first-order attacks.

```python
def pgd_attack(model, x, y_true, epsilon=0.03, alpha=0.007,
               num_steps=40):
    """Generate adversarial example using PGD."""
    x_adv = x.clone().detach()
    x_adv += torch.empty_like(x_adv).uniform_(-epsilon, epsilon)
    x_adv = torch.clamp(x_adv, 0, 1)

    for _ in range(num_steps):
        x_adv.requires_grad_(True)
        output = model(x_adv)
        loss = nn.CrossEntropyLoss()(output, y_true)
        loss.backward()

        # Step in gradient direction
        x_adv = x_adv.detach() + alpha * x_adv.grad.sign()
        # Project back to epsilon-ball
        perturbation = torch.clamp(x_adv - x, min=-epsilon, max=epsilon)
        x_adv = torch.clamp(x + perturbation, 0, 1)

    return x_adv.detach()
```

#### Carlini & Wagner (C&W) Attack

Optimization-based attack that minimizes perturbation magnitude while ensuring misclassification. Formulates as: minimize `||delta||_p + c * f(x + delta)` where f is a loss function that is negative when the attack succeeds. Strongest white-box attack but computationally expensive.

### Model Poisoning

#### Data Poisoning

Injecting malicious samples into training data to degrade model performance or introduce targeted misclassifications.

- **Availability attack**: degrade overall accuracy by injecting mislabeled samples
- **Targeted attack**: cause misclassification of specific inputs while maintaining accuracy on others
- **Clean-label attack**: inject correctly-labeled samples that still cause targeted misclassification (through feature collision)

Defense: data sanitization, anomaly detection on training data, robust aggregation, certified defenses.

#### Backdoor Attacks

Insert a trigger pattern during training. The model behaves normally on clean inputs but activates malicious behavior when the trigger is present.

```python
# Backdoor attack example: plant trigger in training data
def add_backdoor_trigger(X, y, trigger_pattern, target_label,
                         poison_fraction=0.01):
    """Poison a fraction of training data with a backdoor trigger."""
    n_poison = int(len(X) * poison_fraction)
    indices = np.random.choice(len(X), n_poison, replace=False)

    X_poisoned = X.copy()
    y_poisoned = y.copy()

    for idx in indices:
        # Apply trigger (e.g., specific feature pattern)
        X_poisoned[idx] = apply_trigger(X_poisoned[idx], trigger_pattern)
        y_poisoned[idx] = target_label  # Force target classification

    return X_poisoned, y_poisoned
```

Defense: Neural Cleanse (detect triggers via optimization), Spectral Signatures (detect poisoned samples via spectral analysis of activations), Fine-Pruning (prune dormant neurons that activate only on triggered inputs).

### Model Inversion

Extract information about training data from a trained model.

- **Membership inference**: determine whether a specific sample was in the training set. Exploits difference in model confidence on training vs non-training samples.
- **Attribute inference**: predict sensitive attributes of training samples given partial information.
- **Training data reconstruction**: reconstruct actual training samples from model parameters or queries. Particularly concerning for language models that memorize training sequences.

### Model Stealing (Extraction)

Replicate a proprietary model's functionality through query access.

1. **Query-based extraction**: query target model with synthetic inputs, collect predictions, train a surrogate model on (input, prediction) pairs.
2. **Functionally equivalent extraction**: for simple models (linear, decision trees), exact extraction is possible with polynomial queries.
3. **Knowledge distillation as attack**: student model trained on teacher's soft predictions captures decision boundary.

Defense: query rate limiting, watermarking (embed detectable patterns in model outputs), prediction perturbation (add calibrated noise to outputs), monitoring query patterns for extraction signatures.

### Membership Inference

Determine whether a specific data point was used during model training. Exploits the observation that models are typically more confident on training data than unseen data.

Attack approach: train a binary classifier (the "attack model") that takes model outputs (confidence scores, loss values) as input and predicts membership (in-training-set vs not-in-training-set).

Defense: regularization (reduces overfitting, equalizes confidence), differential privacy (bounds information leakage), confidence score masking (return only hard labels).

### Differential Privacy for ML

Differential privacy provides mathematically rigorous privacy guarantees. A mechanism M is (epsilon, delta)-differentially private if for any two adjacent datasets D, D' (differing by one record):

`P[M(D) ∈ S] ≤ e^epsilon * P[M(D') ∈ S] + delta`

**DP-SGD**: differentially private stochastic gradient descent. Clips per-sample gradients to bound sensitivity, adds calibrated Gaussian noise.

```python
from opacus import PrivacyEngine

model = MalwareClassifier(input_dim=256, num_classes=10)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

# Wrap with differential privacy
privacy_engine = PrivacyEngine()
model, optimizer, data_loader = privacy_engine.make_private_with_epsilon(
    module=model,
    optimizer=optimizer,
    data_loader=train_loader,
    epochs=50,
    target_epsilon=8.0,
    target_delta=1e-5,
    max_grad_norm=1.0,
)
```

Privacy-utility tradeoff: smaller epsilon = stronger privacy but lower model accuracy. Typical values: epsilon=1-10 for reasonable utility, epsilon<1 for strong privacy (significant accuracy cost).

### Federated Learning Security

Federated learning trains models across distributed clients without centralizing raw data. Each client trains locally and shares only model updates (gradients or weights).

**Security threats to federated learning**:
- **Byzantine attacks**: malicious clients send corrupted updates to poison the global model
- **Model poisoning**: targeted backdoors injected through malicious client updates
- **Inference from gradients**: reconstruct training data from shared gradient updates (gradient inversion attacks)
- **Free-rider attacks**: clients submit minimal/zero updates while benefiting from the aggregated model

**Defenses**: secure aggregation (encrypt individual updates, only aggregate is revealed), robust aggregation (median, trimmed mean, Krum — tolerates Byzantine clients), gradient compression and sparsification (reduces information leakage), homomorphic encryption on updates.

---

## 8. scikit-learn Deep Dive

### Pipeline API

Pipelines chain preprocessing and modeling steps into a single estimator. They prevent data leakage by ensuring transformations are fit only on training data during cross-validation.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('pca', PCA(n_components=50)),
    ('classifier', RandomForestClassifier(n_estimators=200, random_state=42))
])

# Cross-validation respects pipeline boundaries
scores = cross_val_score(pipeline, X, y, cv=5, scoring='f1_weighted')
```

### ColumnTransformer

Applies different transformations to different feature subsets. Essential when features have mixed types (numerical, categorical, text).

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import (
    StandardScaler, OneHotEncoder, OrdinalEncoder
)
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

numerical_features = ['duration', 'src_bytes', 'dst_bytes', 'count']
categorical_features = ['protocol_type', 'service', 'flag']
ordinal_features = ['severity']

numerical_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

ordinal_pipeline = Pipeline([
    ('encoder', OrdinalEncoder(
        categories=[['low', 'medium', 'high', 'critical']]
    ))
])

preprocessor = ColumnTransformer([
    ('num', numerical_pipeline, numerical_features),
    ('cat', categorical_pipeline, categorical_features),
    ('ord', ordinal_pipeline, ordinal_features)
])

full_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=200, random_state=42))
])

full_pipeline.fit(X_train, y_train)
predictions = full_pipeline.predict(X_test)
```

### Custom Transformers

Extend scikit-learn's transformer API for domain-specific preprocessing.

```python
from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class EntropyFeatures(BaseEstimator, TransformerMixin):
    """Compute Shannon entropy of byte distributions."""

    def __init__(self, n_bins=256):
        self.n_bins = n_bins

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        entropies = []
        for sample in X:
            hist, _ = np.histogram(sample, bins=self.n_bins, density=True)
            hist = hist[hist > 0]  # remove zero bins
            entropy = -np.sum(hist * np.log2(hist))
            entropies.append(entropy)
        return np.array(entropies).reshape(-1, 1)


class TemporalFeatures(BaseEstimator, TransformerMixin):
    """Extract cyclical temporal features from timestamps."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # X is array of timestamps (unix epoch)
        import pandas as pd
        timestamps = pd.to_datetime(X.ravel(), unit='s')
        hour = timestamps.hour
        day_of_week = timestamps.dayofweek

        # Cyclical encoding
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)
        dow_sin = np.sin(2 * np.pi * day_of_week / 7)
        dow_cos = np.cos(2 * np.pi * day_of_week / 7)

        return np.column_stack([hour_sin, hour_cos, dow_sin, dow_cos])
```

### Cross-Validation Strategies

#### StratifiedKFold

Preserves class distribution in each fold. Critical for imbalanced datasets (security alerts are typically <5% of total events).

#### TimeSeriesSplit

Expanding window: each subsequent fold uses more training data but always evaluates on future data. Prevents temporal leakage.

```python
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt

tscv = TimeSeriesSplit(n_splits=5, gap=24)  # 24-sample gap between train/test
for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
    X_train_fold = X.iloc[train_idx]
    X_test_fold = X.iloc[test_idx]
    # Train always precedes test chronologically
```

#### GroupKFold

Ensures all samples from a group stay together. Use when samples within a group are not independent (multiple packets from same session, multiple events from same incident).

```python
from sklearn.model_selection import GroupKFold

# Groups: source_ip ensures all traffic from same IP is in same fold
groups = df['source_ip'].values
gkf = GroupKFold(n_splits=5)
for train_idx, test_idx in gkf.split(X, y, groups=groups):
    # No IP appears in both train and test
    pass
```

### Model Persistence

**joblib**: efficient serialization for numpy-heavy objects. Standard for scikit-learn model persistence.

```python
import joblib

# Save
joblib.dump(full_pipeline, 'models/ids_pipeline.joblib')

# Load
loaded_pipeline = joblib.load('models/ids_pipeline.joblib')
predictions = loaded_pipeline.predict(new_data)
```

**ONNX** (Open Neural Network Exchange): framework-agnostic model format. Export scikit-learn or PyTorch models to ONNX for optimized inference in production.

```python
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

initial_type = [('features', FloatTensorType([None, n_features]))]
onnx_model = convert_sklearn(pipeline, initial_types=initial_type)

with open("model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())
```

### Feature Importance and Interpretation

#### Permutation Importance

Measures how much model performance degrades when a feature is randomly shuffled. Model-agnostic, computed on validation data (avoids bias of impurity-based importance toward high-cardinality features).

```python
from sklearn.inspection import permutation_importance

result = permutation_importance(
    model, X_test, y_test,
    n_repeats=30, random_state=42, n_jobs=-1, scoring='f1_weighted'
)

# Sort by importance
sorted_idx = result.importances_mean.argsort()[::-1]
for idx in sorted_idx[:20]:
    print(f"{feature_names[idx]}: "
          f"{result.importances_mean[idx]:.4f} "
          f"+/- {result.importances_std[idx]:.4f}")
```

#### SHAP (SHapley Additive exPlanations)

Game-theoretic feature attribution. Computes each feature's contribution to moving prediction from the expected value to the actual prediction. Provides local explanations (per-prediction) that sum to global importance.

```python
import shap

# TreeSHAP for tree-based models (fast exact computation)
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test)

# Summary plot: feature importance + direction
shap.summary_plot(shap_values, X_test, feature_names=feature_names)

# Force plot: explain single prediction
shap.force_plot(explainer.expected_value, shap_values[0], X_test.iloc[0])

# Dependence plot: feature interaction
shap.dependence_plot("src_bytes", shap_values, X_test)
```

### Model Interpretation for Security

Interpretability is not optional in security contexts. Analysts need to understand why a model flagged traffic as malicious to take appropriate action.

- Feature importance reveals which network characteristics drive detections
- SHAP values explain individual alerts (this specific alert triggered because of unusual dst_bytes + rare port combination)
- Partial dependence plots show how detection probability varies with each feature
- Decision path tracing (for tree models) provides rule-like explanations

---

## 9. Data Engineering for ML

### Feature Pipelines

#### Batch Features

Computed on historical data at regular intervals (hourly, daily). Used for training and features that do not require real-time freshness. Typically computed in data warehouses (BigQuery, Snowflake) or batch processing frameworks (Spark, dbt).

Example: user's average login count per day over the past 30 days, computed nightly.

#### Streaming Features

Computed in real-time from event streams. Required for low-latency inference where feature freshness is critical. Implemented with stream processing (Flink, Kafka Streams, Spark Structured Streaming).

Example: number of failed login attempts in the last 5 minutes (windowed aggregation).

```python
# Conceptual feature pipeline (Feast + streaming)
from feast import FeatureStore, Entity, FeatureView, Field
from feast.types import Float32, Int64

# Define entity
user = Entity(name="user_id", join_keys=["user_id"])

# Batch feature view (computed daily)
user_behavior_stats = FeatureView(
    name="user_behavior_stats",
    entities=[user],
    schema=[
        Field(name="avg_daily_logins", dtype=Float32),
        Field(name="avg_session_duration", dtype=Float32),
        Field(name="unique_ips_30d", dtype=Int64),
        Field(name="avg_bytes_transferred", dtype=Float32),
    ],
    source=bigquery_source,
    ttl=timedelta(days=1),
)

# Online serving (real-time lookup)
store = FeatureStore(repo_path="feature_repo/")
features = store.get_online_features(
    features=["user_behavior_stats:avg_daily_logins",
              "user_behavior_stats:unique_ips_30d"],
    entity_rows=[{"user_id": "u123"}]
).to_dict()
```

### Training Data Management

Training data must be versioned, documented, and reproducible.

- **Dataset cards**: document data source, collection methodology, known biases, intended use, and limitations
- **Schema enforcement**: validate incoming data against expected schema before ingestion
- **Lineage tracking**: trace every training dataset to its source data and transformations
- **Freshness guarantees**: ensure training data is not stale relative to production data distribution

### Data Versioning

**DVC (Data Version Control)**: Git-like versioning for large datasets and ML artifacts. Stores metadata in git, actual data in remote storage (S3, GCS, Azure Blob).

```bash
# Initialize DVC in repo
dvc init

# Track large dataset
dvc add data/network_traffic_2024.parquet

# Push data to remote storage
dvc remote add -d storage s3://ml-data-bucket/dvc-store
dvc push

# Reproduce exact training data for any commit
git checkout v1.2.0
dvc checkout
```

**LakeFS**: Git-like branching for data lakes. Create branches of data, experiment, and merge back. Zero-copy branching via copy-on-write. Integrates with Spark, Trino, dbt.

### Label Management

Labels are the ground truth that supervised models learn from. For security applications, labeling is expensive and error-prone.

- **Active learning**: model identifies samples it is most uncertain about; human experts label those (maximizes information gain per label)
- **Weak supervision** (Snorkel): combine noisy labeling functions (heuristics, pattern matching, knowledge bases) into probabilistic labels
- **Label quality monitoring**: track inter-annotator agreement, flag low-confidence labels, version label corrections
- **Temporal label validity**: labels may become stale (benign domain later compromised). Track label timestamp and re-validate periodically

### Data Augmentation

Generate synthetic training samples to improve model robustness and address data scarcity.

- **Tabular**: SMOTE (interpolation between minority class samples), noise injection, feature perturbation within valid ranges
- **Text/logs**: synonym replacement, random insertion/deletion, back-translation, template-based generation
- **Network traffic**: time-shifting flows, replay with modified parameters, GAN-generated synthetic traffic
- **Malware**: functionality-preserving transformations (dead code insertion, register reassignment, instruction substitution)

### Handling Imbalanced Datasets

Security datasets are inherently imbalanced. Attack traffic may constitute 0.01-1% of total traffic.

#### SMOTE (Synthetic Minority Over-sampling Technique)

Generates synthetic samples by interpolating between existing minority class neighbors.

```python
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek
from imblearn.pipeline import Pipeline as ImbPipeline

# SMOTE oversampling
smote = SMOTE(sampling_strategy=0.5, random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# Combined pipeline with imbalanced-learn
imb_pipeline = ImbPipeline([
    ('preprocessor', preprocessor),
    ('smote', SMOTE(sampling_strategy=0.3, random_state=42)),
    ('classifier', RandomForestClassifier(n_estimators=200, random_state=42))
])
```

#### Class Weights

Most algorithms accept `class_weight` parameter that adjusts the loss function to penalize misclassification of minority class more heavily.

```python
from sklearn.utils.class_weight import compute_class_weight

# Automatic: inversely proportional to class frequency
class_weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
weight_dict = dict(zip(np.unique(y), class_weights))

model = RandomForestClassifier(
    class_weight='balanced',  # or weight_dict for manual
    n_estimators=200,
    random_state=42
)
```

#### Undersampling

Reduce majority class samples. Random undersampling is simple but discards information. Informed methods (Tomek Links, Edited Nearest Neighbors) remove majority samples near the decision boundary or that are noisy.

### ML-Specific Data Quality

Beyond standard data quality (completeness, consistency, accuracy), ML pipelines have additional requirements:

- **Feature-target leakage**: features that encode future information or the target itself. Detected by suspiciously high model performance and feature importance analysis
- **Label noise**: mislabeled samples degrade model performance. Train with label smoothing or use noise-robust loss functions
- **Distribution representativeness**: training data must represent the deployment distribution. Monitor coverage of feature space regions
- **Temporal consistency**: features computed at different cadences must be aligned to the same point in time
- **Missing data patterns**: MCAR (random), MAR (dependent on observed), MNAR (dependent on missing value). Each requires different handling strategies

```python
# Data quality checks for ML
def validate_ml_data(df, feature_config):
    issues = []

    # Check for leakage: correlation between features and target
    for col in feature_config['features']:
        corr = df[col].corr(df[feature_config['target']])
        if abs(corr) > 0.95:
            issues.append(f"LEAKAGE WARNING: {col} has {corr:.3f} "
                         f"correlation with target")

    # Check class distribution
    class_counts = df[feature_config['target']].value_counts()
    imbalance_ratio = class_counts.min() / class_counts.max()
    if imbalance_ratio < 0.01:
        issues.append(f"SEVERE IMBALANCE: minority/majority = "
                     f"{imbalance_ratio:.4f}")

    # Check for constant features
    for col in feature_config['features']:
        if df[col].nunique() <= 1:
            issues.append(f"CONSTANT FEATURE: {col}")

    # Check missing data patterns
    missing_pct = df[feature_config['features']].isnull().mean()
    high_missing = missing_pct[missing_pct > 0.5]
    for col, pct in high_missing.items():
        issues.append(f"HIGH MISSING: {col} = {pct:.1%}")

    return issues
```

---

## 10. Lab Exercises

### Lab 1: Anomaly Detection System for Network Traffic

Build a hybrid anomaly detection system combining Isolation Forest (fast, interpretable) with an autoencoder (captures nonlinear patterns). Evaluate on NSL-KDD or CICIDS2017 dataset.

```python
"""
Lab 1: Network Traffic Anomaly Detection
Combines Isolation Forest + Autoencoder for robust detection.
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report, roc_auc_score, precision_recall_curve
)
from sklearn.model_selection import train_test_split


# --- Data Loading and Preprocessing ---
def load_nsl_kdd(train_path, test_path):
    """Load NSL-KDD dataset."""
    columns = [
        'duration', 'protocol_type', 'service', 'flag', 'src_bytes',
        'dst_bytes', 'land', 'wrong_fragment', 'urgent', 'hot',
        'num_failed_logins', 'logged_in', 'num_compromised', 'root_shell',
        'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
        'num_access_files', 'num_outbound_cmds', 'is_host_login',
        'is_guest_login', 'count', 'srv_count', 'serror_rate',
        'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate',
        'same_srv_rate', 'diff_srv_rate', 'srv_diff_host_rate',
        'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate',
        'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
        'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
        'dst_host_srv_rerror_rate', 'label', 'difficulty'
    ]

    train_df = pd.read_csv(train_path, names=columns)
    test_df = pd.read_csv(test_path, names=columns)

    # Binary label: normal vs attack
    train_df['is_attack'] = (train_df['label'] != 'normal').astype(int)
    test_df['is_attack'] = (test_df['label'] != 'normal').astype(int)

    return train_df, test_df


def preprocess_features(train_df, test_df):
    """Encode categoricals and scale numericals."""
    categorical_cols = ['protocol_type', 'service', 'flag']
    numerical_cols = [c for c in train_df.columns
                      if c not in categorical_cols + ['label', 'difficulty',
                                                      'is_attack']]

    # Encode categoricals
    encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        train_df[col] = le.fit_transform(train_df[col])
        test_df[col] = test_df[col].map(
            lambda x, le=le: le.transform([x])[0]
            if x in le.classes_ else -1
        )
        encoders[col] = le

    feature_cols = numerical_cols + categorical_cols
    X_train = train_df[feature_cols].values.astype(np.float32)
    X_test = test_df[feature_cols].values.astype(np.float32)
    y_train = train_df['is_attack'].values
    y_test = test_df['is_attack'].values

    # Scale
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    return X_train, X_test, y_train, y_test, scaler


# --- Isolation Forest Component ---
def train_isolation_forest(X_normal, contamination=0.05):
    """Train Isolation Forest on normal traffic only."""
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_normal)
    return iso_forest


def get_isolation_scores(iso_forest, X):
    """Get anomaly scores (lower = more anomalous)."""
    return -iso_forest.decision_function(X)  # negate so higher = more anomalous


# --- Autoencoder Component ---
class TrafficAutoencoder(nn.Module):
    def __init__(self, input_dim, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Linear(32, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Linear(64, input_dim)
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed


def train_autoencoder(X_normal, input_dim, epochs=50, batch_size=256,
                      lr=1e-3, latent_dim=16):
    """Train autoencoder on normal traffic."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = TrafficAutoencoder(input_dim, latent_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    dataset = TensorDataset(torch.FloatTensor(X_normal))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            reconstructed = model(batch)
            loss = criterion(reconstructed, batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            avg_loss = total_loss / len(loader)
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")

    return model


def get_reconstruction_error(model, X):
    """Compute per-sample reconstruction error."""
    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X).to(device)
        reconstructed = model(X_tensor)
        errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1)
    return errors.cpu().numpy()


# --- Hybrid Detection ---
def hybrid_anomaly_scores(iso_scores, ae_errors, weight_iso=0.4,
                          weight_ae=0.6):
    """Combine scores from both detectors."""
    # Normalize both to [0, 1]
    iso_norm = (iso_scores - iso_scores.min()) / (
        iso_scores.max() - iso_scores.min() + 1e-8)
    ae_norm = (ae_errors - ae_errors.min()) / (
        ae_errors.max() - ae_errors.min() + 1e-8)

    return weight_iso * iso_norm + weight_ae * ae_norm


# --- Evaluation ---
def evaluate_detector(y_true, scores, threshold=None):
    """Evaluate anomaly detector performance."""
    auc = roc_auc_score(y_true, scores)
    print(f"ROC AUC: {auc:.4f}")

    if threshold is None:
        precision, recall, thresholds = precision_recall_curve(y_true, scores)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
        threshold = thresholds[np.argmax(f1_scores)]
        print(f"Optimal threshold (max F1): {threshold:.4f}")

    predictions = (scores >= threshold).astype(int)
    print(classification_report(y_true, predictions,
                                target_names=['Normal', 'Attack']))
    return predictions, threshold


# --- Main Execution ---
def run_lab1():
    """Execute the full anomaly detection pipeline."""
    # Load data (substitute with actual paths)
    # train_df, test_df = load_nsl_kdd('KDDTrain+.txt', 'KDDTest+.txt')
    # X_train, X_test, y_train, y_test, scaler = preprocess_features(
    #     train_df, test_df)

    # For demonstration, generate synthetic data
    np.random.seed(42)
    n_normal = 10000
    n_attack = 500
    n_features = 41

    X_normal = np.random.randn(n_normal, n_features).astype(np.float32)
    X_attack = np.random.randn(n_attack, n_features).astype(np.float32) + 2

    X_all = np.vstack([X_normal, X_attack])
    y_all = np.array([0]*n_normal + [1]*n_attack)

    # Split: use only normal data for training detectors
    X_train_normal = X_normal[:8000]
    X_test = X_all[8000:]
    y_test = y_all[8000:]

    # Train Isolation Forest
    print("=== Training Isolation Forest ===")
    iso_forest = train_isolation_forest(X_train_normal)
    iso_scores = get_isolation_scores(iso_forest, X_test)

    # Train Autoencoder
    print("\n=== Training Autoencoder ===")
    ae_model = train_autoencoder(X_train_normal, n_features, epochs=30)
    ae_errors = get_reconstruction_error(ae_model, X_test)

    # Hybrid scoring
    print("\n=== Hybrid Detection Results ===")
    combined_scores = hybrid_anomaly_scores(iso_scores, ae_errors)
    predictions, threshold = evaluate_detector(y_test, combined_scores)

    # Individual detector performance for comparison
    print("\n=== Isolation Forest Only ===")
    evaluate_detector(y_test, iso_scores)
    print("\n=== Autoencoder Only ===")
    evaluate_detector(y_test, ae_errors)


if __name__ == "__main__":
    run_lab1()
```

### Lab 2: Phishing URL Classifier

Build a phishing URL detection system with comprehensive feature engineering and gradient boosting.

```python
"""
Lab 2: Phishing URL Classifier
Feature engineering + gradient boosting for phishing detection.
"""
import re
import math
import numpy as np
import pandas as pd
from urllib.parse import urlparse, parse_qs
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb


# --- Feature Engineering ---
class URLFeatureExtractor:
    """Extract features from URLs for phishing detection."""

    SUSPICIOUS_TLDS = {
        '.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.club',
        '.online', '.site', '.icu', '.buzz', '.work'
    }

    LEGITIMATE_BRANDS = [
        'google', 'facebook', 'apple', 'microsoft', 'amazon',
        'paypal', 'netflix', 'linkedin', 'twitter', 'instagram',
        'bank', 'secure', 'account', 'login', 'verify'
    ]

    def extract_features(self, url):
        """Extract all features from a single URL."""
        parsed = urlparse(url if '://' in url else f'http://{url}')
        features = {}

        # Length features
        features['url_length'] = len(url)
        features['domain_length'] = len(parsed.netloc)
        features['path_length'] = len(parsed.path)
        features['query_length'] = len(parsed.query)

        # Character count features
        features['num_dots'] = url.count('.')
        features['num_hyphens'] = url.count('-')
        features['num_underscores'] = url.count('_')
        features['num_slashes'] = url.count('/')
        features['num_question_marks'] = url.count('?')
        features['num_equals'] = url.count('=')
        features['num_at'] = url.count('@')
        features['num_ampersand'] = url.count('&')
        features['num_percent'] = url.count('%')
        features['num_digits'] = sum(c.isdigit() for c in url)
        features['digit_ratio'] = features['num_digits'] / (len(url) + 1)

        # Domain features
        domain = parsed.netloc.split(':')[0]  # remove port
        features['num_subdomains'] = domain.count('.') - 1
        features['domain_has_ip'] = int(bool(
            re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain)
        ))
        features['uses_https'] = int(parsed.scheme == 'https')
        features['has_port'] = int(':' in parsed.netloc and
                                   not parsed.netloc.startswith('['))

        # TLD analysis
        tld = '.' + domain.split('.')[-1] if '.' in domain else ''
        features['suspicious_tld'] = int(tld in self.SUSPICIOUS_TLDS)
        features['tld_length'] = len(tld)

        # Entropy of URL
        features['url_entropy'] = self._shannon_entropy(url)
        features['domain_entropy'] = self._shannon_entropy(domain)

        # Path features
        features['path_depth'] = parsed.path.count('/') - 1
        features['has_exe'] = int('.exe' in url.lower())
        features['has_php'] = int('.php' in url.lower())

        # Query features
        query_params = parse_qs(parsed.query)
        features['num_params'] = len(query_params)
        features['max_param_length'] = max(
            (len(str(v)) for v in query_params.values()), default=0
        )

        # Brand impersonation detection
        features['contains_brand'] = int(any(
            brand in url.lower() for brand in self.LEGITIMATE_BRANDS
        ))
        features['brand_in_subdomain'] = int(any(
            brand in domain.lower().rsplit('.', 2)[0]
            for brand in self.LEGITIMATE_BRANDS
        )) if '.' in domain else 0

        # Suspicious patterns
        features['has_redirect'] = int(
            'redirect' in url.lower() or 'redir' in url.lower()
        )
        features['has_login_keyword'] = int(
            'login' in url.lower() or 'signin' in url.lower()
        )
        features['double_slash_in_path'] = int('//' in parsed.path)
        features['hex_encoded'] = int('%' in url)

        # Typosquatting indicators
        features['has_homoglyphs'] = int(bool(
            re.search(r'[0oO]|[1lI]|[vv]', domain)
        ))

        return features

    @staticmethod
    def _shannon_entropy(text):
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        prob = [text.count(c) / len(text) for c in set(text)]
        return -sum(p * math.log2(p) for p in prob if p > 0)

    def extract_batch(self, urls):
        """Extract features from a list of URLs."""
        return pd.DataFrame([self.extract_features(url) for url in urls])


# --- Model Training ---
def train_phishing_classifier(X, y):
    """Train LightGBM classifier with cross-validation."""
    model = lgb.LGBMClassifier(
        n_estimators=500,
        num_leaves=63,
        learning_rate=0.05,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        bagging_freq=5,
        min_child_samples=20,
        class_weight='balanced',
        random_state=42,
        verbose=-1
    )

    # Cross-validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=skf, scoring='f1', n_jobs=-1)
    print(f"Cross-validation F1: {scores.mean():.4f} +/- {scores.std():.4f}")

    # Train final model
    model.fit(X, y)
    return model


def evaluate_phishing_model(model, X_test, y_test, feature_names):
    """Evaluate model and show feature importance."""
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    print("\nClassification Report:")
    print(classification_report(y_test, predictions,
                                target_names=['Legitimate', 'Phishing']))
    print(f"ROC AUC: {roc_auc_score(y_test, probabilities):.4f}")

    # Feature importance
    importance = model.feature_importances_
    sorted_idx = np.argsort(importance)[::-1]
    print("\nTop 15 Features:")
    for i, idx in enumerate(sorted_idx[:15]):
        print(f"  {i+1}. {feature_names[idx]}: {importance[idx]}")


# --- Main Execution ---
def run_lab2():
    """Execute phishing URL classification pipeline."""
    # Example URLs (in practice, use a real dataset like PhishTank + Alexa Top)
    legitimate_urls = [
        "https://www.google.com/search?q=machine+learning",
        "https://github.com/scikit-learn/scikit-learn",
        "https://docs.python.org/3/library/re.html",
        "https://stackoverflow.com/questions/12345",
        "https://en.wikipedia.org/wiki/Machine_learning",
    ]

    phishing_urls = [
        "http://192.168.1.100/paypal-login/secure/index.php",
        "http://g00gle-security.tk/verify-account?id=12345",
        "http://amaz0n.account-verify.xyz/login.html",
        "http://microsoft-password-reset.ml/update.php?token=abc",
        "http://faceb00k.com-secure.club/login.php",
    ]

    # Extract features
    extractor = URLFeatureExtractor()
    all_urls = legitimate_urls + phishing_urls
    labels = [0] * len(legitimate_urls) + [1] * len(phishing_urls)

    X = extractor.extract_batch(all_urls)
    y = np.array(labels)

    print(f"Features extracted: {X.shape[1]}")
    print(f"Sample count: {len(y)} (Legit: {sum(y==0)}, Phish: {sum(y==1)})")

    # In practice with a real dataset:
    # X_train, X_test, y_train, y_test = train_test_split(
    #     X, y, test_size=0.2, stratify=y, random_state=42)
    # model = train_phishing_classifier(X_train, y_train)
    # evaluate_phishing_model(model, X_test, y_test, X.columns.tolist())

    # Demonstrate feature extraction
    print("\nFeature sample (first URL):")
    for feat, val in X.iloc[0].items():
        print(f"  {feat}: {val}")


if __name__ == "__main__":
    run_lab2()
```

### Lab 3: Complete MLOps Pipeline

Implement training, registry, serving, and monitoring for an intrusion detection model.

```python
"""
Lab 3: Complete MLOps Pipeline
Training → Registry → Serving → Monitoring
"""
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
from scipy import stats


# --- Model Registry ---
@dataclass
class ModelVersion:
    model_id: str
    version: int
    stage: str  # "staging", "production", "archived"
    metrics: dict
    parameters: dict
    data_hash: str
    created_at: str
    model_path: str
    metadata: dict = field(default_factory=dict)


class SimpleModelRegistry:
    """Lightweight model registry for demonstration."""

    def __init__(self, registry_path: str = "model_registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.registry_path / "manifest.json"
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        if self.manifest_path.exists():
            with open(self.manifest_path) as f:
                return json.load(f)
        return {"models": {}}

    def _save_manifest(self):
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)

    def register_model(self, model, model_name, metrics, parameters,
                       X_train, stage="staging"):
        """Register a new model version."""
        if model_name not in self.manifest["models"]:
            self.manifest["models"][model_name] = {"versions": []}

        version = len(self.manifest["models"][model_name]["versions"]) + 1
        model_id = f"{model_name}_v{version}"
        data_hash = hashlib.sha256(
            X_train.tobytes()).hexdigest()[:16]
        model_path = str(self.registry_path / f"{model_id}.joblib")

        # Save model artifact
        joblib.dump(model, model_path)

        # Create version record
        version_record = {
            "model_id": model_id,
            "version": version,
            "stage": stage,
            "metrics": metrics,
            "parameters": parameters,
            "data_hash": data_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model_path": model_path
        }

        self.manifest["models"][model_name]["versions"].append(version_record)
        self._save_manifest()

        print(f"Registered: {model_id} (stage={stage})")
        print(f"  Metrics: {metrics}")
        return version_record

    def promote_to_production(self, model_name, version):
        """Promote a model version to production."""
        versions = self.manifest["models"][model_name]["versions"]

        # Archive current production
        for v in versions:
            if v["stage"] == "production":
                v["stage"] = "archived"

        # Promote target version
        versions[version - 1]["stage"] = "production"
        self._save_manifest()
        print(f"Promoted {model_name} v{version} to production")

    def get_production_model(self, model_name):
        """Load the current production model."""
        versions = self.manifest["models"][model_name]["versions"]
        for v in versions:
            if v["stage"] == "production":
                return joblib.load(v["model_path"]), v
        return None, None


# --- Training Pipeline ---
class TrainingPipeline:
    """Orchestrates model training with validation."""

    def __init__(self, registry: SimpleModelRegistry):
        self.registry = registry

    def train(self, X_train, y_train, X_val, y_val, model_name="ids_model"):
        """Train model with hyperparameter selection."""
        params = {
            "n_estimators": 200,
            "max_depth": 5,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "min_samples_leaf": 10,
            "random_state": 42
        }

        model = GradientBoostingClassifier(**params)

        # Cross-validation on training set
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(
            model, X_train, y_train, cv=skf, scoring='f1_weighted')
        print(f"CV F1: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

        # Final training
        model.fit(X_train, y_train)

        # Validation metrics
        y_pred = model.predict(X_val)
        metrics = {
            "f1_weighted": float(f1_score(y_val, y_pred, average='weighted')),
            "precision": float(precision_score(y_val, y_pred,
                                              average='weighted')),
            "recall": float(recall_score(y_val, y_pred, average='weighted')),
            "cv_f1_mean": float(cv_scores.mean()),
            "cv_f1_std": float(cv_scores.std())
        }

        # Register model
        version_record = self.registry.register_model(
            model, model_name, metrics, params, X_train)

        return model, metrics, version_record


# --- Monitoring ---
class ModelMonitor:
    """Monitor model performance and data drift in production."""

    def __init__(self, reference_data: np.ndarray,
                 reference_predictions: np.ndarray,
                 feature_names: list):
        self.reference_data = reference_data
        self.reference_predictions = reference_predictions
        self.feature_names = feature_names
        self.alerts = []

    def check_data_drift(self, current_data: np.ndarray,
                         significance=0.05) -> dict:
        """Check for data drift using KS test per feature."""
        drift_results = {}
        drifted_features = []

        for i, feature in enumerate(self.feature_names):
            stat, p_value = stats.ks_2samp(
                self.reference_data[:, i], current_data[:, i]
            )
            is_drifted = p_value < significance
            drift_results[feature] = {
                "ks_statistic": float(stat),
                "p_value": float(p_value),
                "is_drifted": is_drifted
            }
            if is_drifted:
                drifted_features.append(feature)

        drift_score = len(drifted_features) / len(self.feature_names)
        result = {
            "drift_score": drift_score,
            "drifted_features": drifted_features,
            "per_feature": drift_results,
            "alert": drift_score > 0.3  # >30% features drifted
        }

        if result["alert"]:
            self.alerts.append({
                "type": "DATA_DRIFT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "drift_score": drift_score,
                "drifted_features": drifted_features
            })

        return result

    def check_prediction_drift(self, current_predictions: np.ndarray) -> dict:
        """Check if prediction distribution has shifted."""
        # Compare class distribution
        ref_dist = np.bincount(self.reference_predictions.astype(int),
                               minlength=2) / len(self.reference_predictions)
        cur_dist = np.bincount(current_predictions.astype(int),
                               minlength=2) / len(current_predictions)

        # PSI (Population Stability Index)
        psi = np.sum(
            (cur_dist - ref_dist) * np.log(
                (cur_dist + 1e-10) / (ref_dist + 1e-10)
            )
        )

        result = {
            "psi": float(psi),
            "reference_distribution": ref_dist.tolist(),
            "current_distribution": cur_dist.tolist(),
            "alert": psi > 0.2  # PSI > 0.2 indicates significant shift
        }

        if result["alert"]:
            self.alerts.append({
                "type": "PREDICTION_DRIFT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "psi": float(psi)
            })

        return result

    def check_performance(self, y_true: np.ndarray,
                          y_pred: np.ndarray,
                          min_f1: float = 0.85) -> dict:
        """Check if model performance has degraded."""
        current_f1 = f1_score(y_true, y_pred, average='weighted')
        result = {
            "current_f1": float(current_f1),
            "threshold": min_f1,
            "alert": current_f1 < min_f1
        }

        if result["alert"]:
            self.alerts.append({
                "type": "PERFORMANCE_DEGRADATION",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_f1": float(current_f1),
                "threshold": min_f1
            })

        return result

    def get_monitoring_report(self, current_data, current_predictions,
                              y_true=None):
        """Generate full monitoring report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_drift": self.check_data_drift(current_data),
            "prediction_drift": self.check_prediction_drift(
                current_predictions),
        }
        if y_true is not None:
            report["performance"] = self.check_performance(
                y_true, current_predictions)

        report["alerts"] = self.alerts
        return report


# --- Main Execution ---
def run_lab3():
    """Execute complete MLOps pipeline."""
    np.random.seed(42)

    # Generate synthetic data
    n_samples = 5000
    n_features = 20
    feature_names = [f"feature_{i}" for i in range(n_features)]

    X = np.random.randn(n_samples, n_features).astype(np.float32)
    y = (X[:, 0] + X[:, 1] * 2 + np.random.randn(n_samples) * 0.5 > 0
         ).astype(int)

    # Split data
    train_end = int(n_samples * 0.6)
    val_end = int(n_samples * 0.8)

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    # Scale
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    # 1. TRAINING
    print("=" * 60)
    print("PHASE 1: TRAINING")
    print("=" * 60)
    registry = SimpleModelRegistry("./lab3_registry")
    pipeline = TrainingPipeline(registry)
    model, metrics, version = pipeline.train(
        X_train, y_train, X_val, y_val)
    print(f"\nMetrics: {metrics}")

    # 2. REGISTRY: Promote to production
    print("\n" + "=" * 60)
    print("PHASE 2: REGISTRY PROMOTION")
    print("=" * 60)
    if metrics["f1_weighted"] > 0.80:
        registry.promote_to_production("ids_model", version["version"])
    else:
        print("Model does not meet promotion criteria (F1 < 0.80)")

    # 3. SERVING: Load production model
    print("\n" + "=" * 60)
    print("PHASE 3: SERVING")
    print("=" * 60)
    prod_model, prod_version = registry.get_production_model("ids_model")
    if prod_model:
        print(f"Serving: {prod_version['model_id']}")
        test_predictions = prod_model.predict(X_test)
        print(f"Test F1: {f1_score(y_test, test_predictions, average='weighted'):.4f}")

    # 4. MONITORING
    print("\n" + "=" * 60)
    print("PHASE 4: MONITORING")
    print("=" * 60)
    monitor = ModelMonitor(
        reference_data=X_val,
        reference_predictions=model.predict(X_val),
        feature_names=feature_names
    )

    # Simulate production data (with slight drift)
    X_production = X_test + np.random.randn(*X_test.shape) * 0.3
    prod_predictions = prod_model.predict(X_production)

    report = monitor.get_monitoring_report(
        X_production, prod_predictions, y_test)

    print(f"Data Drift Score: {report['data_drift']['drift_score']:.2f}")
    print(f"Prediction PSI: {report['prediction_drift']['psi']:.4f}")
    if 'performance' in report:
        print(f"Current F1: {report['performance']['current_f1']:.4f}")
    print(f"Active Alerts: {len(report['alerts'])}")
    for alert in report['alerts']:
        print(f"  [{alert['type']}] {alert['timestamp']}")


if __name__ == "__main__":
    run_lab3()
```

### Lab 4: Adversarial Attack on a Malware Classifier

Implement and evaluate adversarial attacks against an ML-based malware classifier, then apply defenses.

```python
"""
Lab 4: Adversarial Attacks on Malware Classifier
Attack implementation + defense evaluation.
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, f1_score
from copy import deepcopy


# --- Target Model (Malware Classifier) ---
class MalwareDetector(nn.Module):
    """DNN-based malware detector (target model)."""

    def __init__(self, input_dim=256, num_classes=2):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        return self.network(x)


# --- Attack Implementations ---
class AdversarialAttacks:
    """Collection of adversarial attack methods."""

    @staticmethod
    def fgsm(model, x, y, epsilon=0.1):
        """Fast Gradient Sign Method."""
        x_adv = x.clone().detach().requires_grad_(True)
        output = model(x_adv)
        loss = F.cross_entropy(output, y)
        loss.backward()

        perturbation = epsilon * x_adv.grad.sign()
        x_adv = (x_adv + perturbation).detach()
        return x_adv

    @staticmethod
    def pgd(model, x, y, epsilon=0.1, alpha=0.01, num_steps=40):
        """Projected Gradient Descent (iterative FGSM)."""
        x_adv = x.clone().detach()
        x_adv += torch.empty_like(x_adv).uniform_(-epsilon, epsilon)

        for _ in range(num_steps):
            x_adv.requires_grad_(True)
            output = model(x_adv)
            loss = F.cross_entropy(output, y)
            loss.backward()

            x_adv = (x_adv.detach() + alpha * x_adv.grad.sign())
            # Project onto epsilon-ball around original
            perturbation = torch.clamp(x_adv - x, min=-epsilon, max=epsilon)
            x_adv = x + perturbation

        return x_adv.detach()

    @staticmethod
    def feature_space_attack(model, x, y_target, epsilon=0.2,
                             alpha=0.01, num_steps=100):
        """
        Feature-space attack for malware:
        Only perturb features that can be modified without
        changing malware functionality (e.g., padding, metadata).
        """
        # Mask: 1 = modifiable feature, 0 = functional feature
        # In practice, this mask encodes domain knowledge about which
        # features can be changed without altering malware behavior
        modifiable_mask = torch.zeros_like(x)
        # Example: last 64 features are metadata/padding
        modifiable_mask[:, -64:] = 1.0

        x_adv = x.clone().detach()

        for _ in range(num_steps):
            x_adv.requires_grad_(True)
            output = model(x_adv)
            # Targeted attack: minimize loss for target class
            loss = F.cross_entropy(output, y_target)
            loss.backward()

            # Only modify allowed features
            grad = x_adv.grad * modifiable_mask
            x_adv = (x_adv.detach() - alpha * grad.sign())

            # Project
            perturbation = torch.clamp(x_adv - x, min=-epsilon, max=epsilon)
            perturbation = perturbation * modifiable_mask
            x_adv = x + perturbation

        return x_adv.detach()


# --- Defense Implementations ---
class AdversarialDefenses:
    """Defensive techniques against adversarial attacks."""

    @staticmethod
    def adversarial_training(model, X_train, y_train, epochs=20,
                             epsilon=0.1, batch_size=128, lr=1e-3):
        """
        Adversarial training: augment training with adversarial examples.
        Min-max optimization: min_theta max_delta L(f(x+delta), y)
        """
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        dataset = TensorDataset(
            torch.FloatTensor(X_train), torch.LongTensor(y_train))
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model.train()
        for epoch in range(epochs):
            total_loss = 0
            for x_batch, y_batch in loader:
                # Generate adversarial examples
                x_adv = AdversarialAttacks.pgd(
                    model, x_batch, y_batch,
                    epsilon=epsilon, alpha=epsilon/4, num_steps=7
                )

                # Train on both clean and adversarial
                optimizer.zero_grad()
                loss_clean = F.cross_entropy(model(x_batch), y_batch)
                loss_adv = F.cross_entropy(model(x_adv), y_batch)
                loss = 0.5 * loss_clean + 0.5 * loss_adv
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            if (epoch + 1) % 5 == 0:
                avg_loss = total_loss / len(loader)
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        return model

    @staticmethod
    def input_preprocessing_defense(x, noise_std=0.05):
        """
        Randomized smoothing: add random noise at inference
        to disrupt adversarial perturbations.
        """
        noise = torch.randn_like(x) * noise_std
        return x + noise

    @staticmethod
    def ensemble_defense(models, x):
        """
        Ensemble voting: adversarial examples often don't transfer
        across diverse architectures.
        """
        predictions = []
        for model in models:
            model.eval()
            with torch.no_grad():
                output = model(x)
                pred = output.argmax(dim=1)
                predictions.append(pred)

        # Majority voting
        stacked = torch.stack(predictions, dim=0)
        majority_vote = torch.mode(stacked, dim=0).values
        return majority_vote


# --- Evaluation ---
def evaluate_attack_success(model, x_clean, x_adv, y_true):
    """Evaluate attack effectiveness."""
    model.eval()
    with torch.no_grad():
        clean_preds = model(x_clean).argmax(dim=1)
        adv_preds = model(x_adv).argmax(dim=1)

    clean_acc = accuracy_score(y_true.numpy(), clean_preds.numpy())
    adv_acc = accuracy_score(y_true.numpy(), adv_preds.numpy())
    attack_success_rate = 1 - adv_acc

    # Perturbation magnitude
    l2_norm = torch.norm(x_adv - x_clean, p=2, dim=1).mean().item()
    linf_norm = torch.norm(x_adv - x_clean, p=float('inf'), dim=1
                           ).mean().item()

    return {
        "clean_accuracy": clean_acc,
        "adversarial_accuracy": adv_acc,
        "attack_success_rate": attack_success_rate,
        "mean_l2_perturbation": l2_norm,
        "mean_linf_perturbation": linf_norm
    }


# --- Main Execution ---
def run_lab4():
    """Execute adversarial attack and defense experiments."""
    np.random.seed(42)
    torch.manual_seed(42)

    input_dim = 256
    n_train = 5000
    n_test = 1000

    # Synthetic malware features
    X_train = np.random.randn(n_train, input_dim).astype(np.float32)
    y_train = (np.sum(X_train[:, :10], axis=1) > 0).astype(int)
    X_test = np.random.randn(n_test, input_dim).astype(np.float32)
    y_test = (np.sum(X_test[:, :10], axis=1) > 0).astype(int)

    X_test_tensor = torch.FloatTensor(X_test)
    y_test_tensor = torch.LongTensor(y_test)

    # Train standard model
    print("=" * 60)
    print("TRAINING STANDARD MODEL")
    print("=" * 60)
    model = MalwareDetector(input_dim=input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    dataset = TensorDataset(
        torch.FloatTensor(X_train), torch.LongTensor(y_train))
    loader = DataLoader(dataset, batch_size=128, shuffle=True)

    model.train()
    for epoch in range(20):
        for x_batch, y_batch in loader:
            optimizer.zero_grad()
            loss = F.cross_entropy(model(x_batch), y_batch)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        clean_acc = accuracy_score(
            y_test, model(X_test_tensor).argmax(dim=1).numpy())
    print(f"Clean test accuracy: {clean_acc:.4f}")

    # Attack experiments
    print("\n" + "=" * 60)
    print("ADVERSARIAL ATTACKS")
    print("=" * 60)

    epsilons = [0.01, 0.05, 0.1, 0.2]
    for eps in epsilons:
        # FGSM
        x_adv_fgsm = AdversarialAttacks.fgsm(
            model, X_test_tensor, y_test_tensor, epsilon=eps)
        fgsm_results = evaluate_attack_success(
            model, X_test_tensor, x_adv_fgsm, y_test_tensor)

        # PGD
        x_adv_pgd = AdversarialAttacks.pgd(
            model, X_test_tensor, y_test_tensor,
            epsilon=eps, alpha=eps/4, num_steps=20)
        pgd_results = evaluate_attack_success(
            model, X_test_tensor, x_adv_pgd, y_test_tensor)

        print(f"\nEpsilon = {eps}:")
        print(f"  FGSM - Attack Success: {fgsm_results['attack_success_rate']:.4f}, "
              f"L2: {fgsm_results['mean_l2_perturbation']:.4f}")
        print(f"  PGD  - Attack Success: {pgd_results['attack_success_rate']:.4f}, "
              f"L2: {pgd_results['mean_l2_perturbation']:.4f}")

    # Defense: Adversarial Training
    print("\n" + "=" * 60)
    print("DEFENSE: ADVERSARIAL TRAINING")
    print("=" * 60)
    robust_model = MalwareDetector(input_dim=input_dim)
    # Copy initial weights from standard model for fair comparison
    robust_model.load_state_dict(deepcopy(model.state_dict()))

    robust_model = AdversarialDefenses.adversarial_training(
        robust_model, X_train, y_train, epochs=20, epsilon=0.1)

    # Evaluate robust model
    robust_model.eval()
    with torch.no_grad():
        robust_clean_acc = accuracy_score(
            y_test, robust_model(X_test_tensor).argmax(dim=1).numpy())
    print(f"\nRobust model clean accuracy: {robust_clean_acc:.4f}")

    # Attack robust model
    x_adv_pgd_robust = AdversarialAttacks.pgd(
        robust_model, X_test_tensor, y_test_tensor,
        epsilon=0.1, alpha=0.025, num_steps=20)
    robust_results = evaluate_attack_success(
        robust_model, X_test_tensor, x_adv_pgd_robust, y_test_tensor)
    print(f"PGD attack on robust model (eps=0.1): "
          f"success={robust_results['attack_success_rate']:.4f}")
    print(f"PGD attack on standard model (eps=0.1): "
          f"success={pgd_results['attack_success_rate']:.4f}")

    # Defense: Randomized Smoothing
    print("\n" + "=" * 60)
    print("DEFENSE: RANDOMIZED SMOOTHING")
    print("=" * 60)
    n_smooth_samples = 50
    smooth_predictions = []
    for _ in range(n_smooth_samples):
        x_smoothed = AdversarialDefenses.input_preprocessing_defense(
            x_adv_pgd, noise_std=0.05)
        with torch.no_grad():
            pred = model(x_smoothed).argmax(dim=1)
            smooth_predictions.append(pred)

    smooth_votes = torch.stack(smooth_predictions).mode(dim=0).values
    smooth_acc = accuracy_score(y_test, smooth_votes.numpy())
    print(f"Standard model + smoothing vs PGD: {smooth_acc:.4f}")
    print(f"Standard model without smoothing vs PGD: "
          f"{pgd_results['adversarial_accuracy']:.4f}")


if __name__ == "__main__":
    run_lab4()
```

---

## Summary

This document covered machine learning fundamentals from the perspective of data engineers and security professionals. The key themes:

1. **ML Fundamentals**: Learning paradigms determine what problems you can solve and what data you need. The bias-variance tradeoff and proper evaluation (cross-validation, proper splits) are non-negotiable foundations.

2. **Feature Engineering**: Feature quality determines model performance ceiling. Domain expertise (network protocols, attack patterns, user behavior) translates into discriminative features.

3. **Classical ML**: Gradient boosting (XGBoost, LightGBM, CatBoost) dominates tabular data. Algorithm selection depends on dataset size, feature types, interpretability needs, and latency requirements.

4. **Deep Learning**: Transformers and neural networks handle unstructured data (raw bytes, sequences, text). Transfer learning reduces data requirements for specialized domains.

5. **MLOps**: Production ML requires experiment tracking, model registry, automated training pipelines, deployment strategies, and continuous monitoring for drift.

6. **ML for Security**: Anomaly detection, malware classification, phishing detection, UEBA, and NLP for threat intelligence are the primary application areas. The adversarial nature of security (active attackers) makes this domain uniquely challenging.

7. **ML Security**: Adversarial attacks (FGSM, PGD, C&W), model poisoning, model inversion, and model stealing threaten ML systems. Differential privacy and federated learning address data privacy. Security professionals must understand both offensive and defensive perspectives.

8. **scikit-learn**: Pipeline API, ColumnTransformer, custom transformers, proper cross-validation strategies, and SHAP-based interpretation form the practical toolkit.

9. **Data Engineering for ML**: Feature stores, data versioning, label management, handling imbalanced datasets, and ML-specific data quality checks bridge data engineering and machine learning.

10. **Lab Exercises**: Hands-on implementation of anomaly detection, phishing classification, MLOps pipelines, and adversarial robustness evaluation.

The intersection of data engineering, machine learning, and security creates professionals who can build ML systems that are not only performant but also robust, secure, and production-ready.
