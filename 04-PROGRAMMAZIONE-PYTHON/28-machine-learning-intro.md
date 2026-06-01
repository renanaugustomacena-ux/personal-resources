---
corso: "Programmazione Python"
fase: "7 — Data Science e ML"
modulo: "28"
titolo: "Machine Learning — Introduzione con Python"
versione: "scikit-learn 1.5+ / PyTorch 2.3+ / pandas 2.2+ / MLflow 2.14+ / Optuna 3.6+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "14 — Data Processing"
  - "09 — Type Hints e Mypy"
  - "25 — Performance"
obiettivi:
  - "Comprendere il workflow ML: dati, feature, training, evaluation, deployment"
  - "Utilizzare scikit-learn per classificazione, regressione e clustering"
  - "Costruire reti neurali con PyTorch per deep learning"
  - "Tracciare esperimenti con MLflow e ottimizzare iperparametri con Optuna"
  - "Implementare pipeline ML riproducibili e testabili"
  - "Valutare modelli con metriche appropriate e prevenire overfitting"
tag: [machine-learning, scikit-learn, PyTorch, MLflow, Optuna, deep-learning, ML-pipeline]
---

# Machine Learning — Introduzione con Python

> **Modulo 28** · **Aggiornamento:** 2026-05-24 · **Versione:** scikit-learn 1.5+ / PyTorch 2.3+ / pandas 2.2+ / MLflow 2.14+ / Optuna 3.6+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Data Processing](14-data-processing.md), [Type Hints](09-type-hints-e-mypy.md), [Performance](25-performance.md)
>
> Al termine di questo modulo saprai:
> 1. Comprendere il workflow ML: dati, feature engineering, training, evaluation, deployment
> 2. Utilizzare scikit-learn per classificazione, regressione e clustering
> 3. Costruire reti neurali con PyTorch per deep learning
> 4. Tracciare esperimenti con MLflow e ottimizzare iperparametri con Optuna
> 5. Implementare pipeline ML riproducibili e testabili
> 6. Valutare modelli con metriche appropriate e prevenire overfitting
>
> **Tempo stimato:** 10-12 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **scikit-learn per ML classico.** PyTorch per deep learning.
2. **Hugging Face transformers per LLM.**
3. **MLflow per experiment tracking.**
4. **Reproducibility: seed everywhere, requirements lock.**

### Mappa concettuale

```
                        ┌─────────────────────┐
                        │   MACHINE LEARNING   │
                        └──────────┬──────────┘
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
 ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
 │  Dati             │     │  Modelli         │      │  Valutazione    │
 │  pandas (EDA)    │     │  scikit-learn    │      │  Metriche       │
 │  Feature Eng.    │     │  Pipeline        │      │  Cross-valid.   │
 │  Preprocessing   │     │  ColumnTransf.   │      │  Learning curve │
 └────────┬────────┘     └────────┬────────┘      └────────┬────────┘
          │                       │                        │
          ▼                       ▼                        ▼
 ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
 │  Tuning           │     │  Deep Learning  │      │  MLOps          │
 │  GridSearchCV    │     │  PyTorch intro  │      │  MLflow         │
 │  RandomSearch    │     │  nn.Module      │      │  joblib persist │
 │  Optuna          │     │  DataLoader     │      │  FastAPI deploy │
 └─────────────────┘     └─────────────────┘      └─────────────────┘
```


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti Matematici (Essenziali)](#fondamenti-matematici-essenziali)
3. [scikit-learn](#scikit-learn)
4. [pandas per ML](#pandas-per-ml)
5. [Visualizzazione](#visualizzazione)
6. [Deep Learning (Panoramica)](#deep-learning-panoramica)
7. [MLOps Essenziali](#mlops-essenziali)
8. [Applicazioni Pratiche per IT](#applicazioni-pratiche-per-it)
9. [Best Practices](#best-practices)
10. [Data Preprocessing Avanzato](#data-preprocessing-avanzato)
11. [Metriche di Valutazione — Approfondimento](#metriche-di-valutazione--approfondimento)
12. [Metodi Ensemble Avanzati](#metodi-ensemble-avanzati)
13. [Riduzione della Dimensionalita'](#riduzione-della-dimensionalita)
14. [NLP con Python](#nlp-con-python)
15. [Deep Learning — Fondamenti Teorici](#deep-learning--fondamenti-teorici)
16. [MLOps — Model Registry e Lifecycle](#mlops--model-registry-e-lifecycle)
17. [Hyperparameter Tuning con Optuna](#hyperparameter-tuning-con-optuna)
18. [Time Series Forecasting](#time-series-forecasting)
19. [Interpretabilita' dei Modelli](#interpretabilita-dei-modelli)
20. [AI Etica e Responsabile](#ai-etica-e-responsabile)
21. [Esercizi](#esercizi)
22. [Letture](#letture)
23. [Glossario](#glossario)

---

## Panoramica

### Che cos'e' il Machine Learning

Il **Machine Learning** (apprendimento automatico) e' una branca dell'intelligenza artificiale che consente ai sistemi informatici di apprendere dai dati senza essere esplicitamente programmati per ogni singolo compito. Invece di scrivere regole manuali, si forniscono dati al modello che impara autonomamente a riconoscere pattern, fare previsioni e prendere decisioni.

Il concetto fondamentale e' semplice: dato un insieme di dati (dataset), un algoritmo di ML costruisce un **modello matematico** che cattura le relazioni presenti nei dati. Questo modello puo' poi essere utilizzato per fare previsioni su dati mai visti prima.

### Tipi di Machine Learning

#### Supervised Learning (Apprendimento Supervisionato)

Il modello apprende da dati **etichettati** — cioe' coppie (input, output atteso). L'obiettivo e' imparare una funzione che mappa gli input agli output corretti.

- **Classificazione**: l'output e' una categoria discreta (es. spam/non-spam, tipo di tumore)
- **Regressione**: l'output e' un valore numerico continuo (es. prezzo di una casa, temperatura)

```python
# Esempio concettuale di supervised learning
# Input: caratteristiche di una casa (metratura, stanze, zona)
# Output: prezzo della casa (valore numerico -> regressione)
X = [[120, 3, "centro"], [80, 2, "periferia"], [200, 5, "centro"]]
y = [350000, 180000, 550000]  # prezzi (etichette)
```

#### Unsupervised Learning (Apprendimento Non Supervisionato)

Il modello lavora con dati **senza etichette** e cerca di scoprire strutture nascoste nei dati.

- **Clustering**: raggruppamento di dati simili (es. segmentazione clienti)
- **Riduzione dimensionalita'**: compressione dei dati mantenendo le informazioni essenziali (es. PCA)
- **Rilevamento anomalie**: identificazione di dati anomali rispetto alla distribuzione normale

```python
# Esempio concettuale di unsupervised learning
# Input: comportamento utenti sul sito web (nessuna etichetta)
# Output: gruppi di utenti con comportamento simile
X = [[30, 5, 120], [25, 4, 90], [60, 1, 10], [55, 2, 15]]
# L'algoritmo scopre da solo i cluster: utenti attivi vs utenti occasionali
```

#### Reinforcement Learning (Apprendimento per Rinforzo)

Un **agente** impara a prendere decisioni interagendo con un ambiente, ricevendo ricompense (reward) positive o negative in base alle azioni compiute. L'obiettivo e' massimizzare la ricompensa cumulativa nel tempo.

Applicazioni tipiche: giochi, robotica, trading automatico, sistemi di raccomandazione.

### Workflow del Machine Learning

Un progetto ML segue tipicamente queste fasi:

```
1. Definizione del problema
2. Raccolta dati
3. Esplorazione e pulizia dati (EDA)
4. Feature engineering
5. Selezione del modello
6. Training del modello
7. Valutazione
8. Ottimizzazione iperparametri
9. Deploy in produzione
10. Monitoraggio e manutenzione
```

### Ecosistema Python per ML

Python domina il mondo del machine learning grazie al suo ecosistema ricchissimo:

| Libreria | Utilizzo |
|---|---|
| **NumPy** | Calcolo numerico, array multidimensionali |
| **pandas** | Manipolazione e analisi dati tabulari |
| **scikit-learn** | ML classico (classificazione, regressione, clustering) |
| **matplotlib** | Visualizzazione dati (grafici base) |
| **seaborn** | Visualizzazione statistica avanzata |
| **TensorFlow/Keras** | Deep learning (reti neurali) |
| **PyTorch** | Deep learning (ricerca e produzione) |
| **XGBoost/LightGBM** | Gradient boosting ad alte prestazioni |
| **MLflow** | Tracking esperimenti e gestione modelli |
| **joblib** | Serializzazione modelli |

Installazione dell'ambiente di base:

```bash
pip install numpy pandas scikit-learn matplotlib seaborn
pip install xgboost lightgbm
pip install tensorflow  # oppure torch per PyTorch
pip install mlflow joblib
```

---

## Fondamenti Matematici (Essenziali)

Non serve essere matematici per usare il ML, ma comprendere i concetti di base e' fondamentale per scegliere algoritmi appropriati e interpretare i risultati.

### Vettori e Matrici con NumPy

In ML, i dati sono rappresentati come **matrici**: ogni riga e' un campione (sample) e ogni colonna e' una feature.

```python
import numpy as np

# Vettore: array monodimensionale
vettore = np.array([1, 2, 3, 4, 5])
print(f"Shape: {vettore.shape}")  # (5,)

# Matrice: array bidimensionale
# 3 campioni, 4 feature ciascuno
matrice = np.array([
    [1.0, 2.5, 3.2, 0.8],
    [2.1, 1.8, 4.1, 1.2],
    [0.5, 3.3, 2.9, 0.3]
])
print(f"Shape: {matrice.shape}")  # (3, 4)

# Operazioni fondamentali
prodotto_scalare = np.dot(vettore[:4], matrice[0])
print(f"Prodotto scalare: {prodotto_scalare}")

# Trasposizione
trasposta = matrice.T
print(f"Shape trasposta: {trasposta.shape}")  # (4, 3)

# Moltiplicazione matriciale
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
C = A @ B  # equivalente a np.matmul(A, B)
print(f"Prodotto matriciale:\n{C}")

# Norma di un vettore (distanza dall'origine)
norma = np.linalg.norm(vettore)
print(f"Norma L2: {norma:.4f}")
```

### Statistica di Base

Le statistiche descrittive sono essenziali per comprendere la distribuzione dei dati.

```python
import numpy as np

dati = np.array([23, 45, 12, 67, 34, 89, 56, 23, 41, 78])

# Misure di tendenza centrale
media = np.mean(dati)               # 46.8
mediana = np.median(dati)            # 43.0

# Misure di dispersione
deviazione_std = np.std(dati)        # quanto i dati si disperdono dalla media
varianza = np.var(dati)              # quadrato della deviazione standard
range_dati = np.ptp(dati)            # max - min

print(f"Media: {media:.2f}")
print(f"Mediana: {mediana:.2f}")
print(f"Deviazione standard: {deviazione_std:.2f}")
print(f"Varianza: {varianza:.2f}")

# Percentili e quartili
q25 = np.percentile(dati, 25)
q50 = np.percentile(dati, 50)  # = mediana
q75 = np.percentile(dati, 75)
iqr = q75 - q25  # Interquartile Range
print(f"Q1={q25}, Q2={q50}, Q3={q75}, IQR={iqr}")

# Correlazione tra due variabili
x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
y = np.array([2.1, 4.3, 5.8, 8.2, 9.5, 12.1, 14.0, 15.8, 18.2, 20.1])
correlazione = np.corrcoef(x, y)[0, 1]
print(f"Correlazione: {correlazione:.4f}")  # vicino a 1.0 -> forte correlazione positiva
```

### Fondamenti di Probabilita'

La probabilita' e' alla base di molti algoritmi ML, specialmente quelli bayesiani.

```python
import numpy as np

# Distribuzione normale (gaussiana)
# La maggior parte dei fenomeni naturali segue questa distribuzione
media = 170       # altezza media in cm
std = 10          # deviazione standard
campioni = np.random.normal(media, std, 10000)

# Probabilita' empirica
prob_sopra_180 = np.mean(campioni > 180)
print(f"P(altezza > 180cm) ≈ {prob_sopra_180:.3f}")

# Funzione sigmoide (fondamentale per classificazione)
def sigmoide(z):
    """Mappa qualsiasi valore nell'intervallo (0, 1) — usata come probabilita'."""
    return 1 / (1 + np.exp(-z))

z = np.array([-3, -1, 0, 1, 3])
print(f"Sigmoide: {sigmoide(z)}")
# [-3 -> ~0.05, -1 -> ~0.27, 0 -> 0.5, 1 -> ~0.73, 3 -> ~0.95]

# Funzione softmax (classificazione multiclasse)
def softmax(z):
    """Converte un vettore di valori in una distribuzione di probabilita'."""
    exp_z = np.exp(z - np.max(z))  # sottrazione per stabilita' numerica
    return exp_z / exp_z.sum()

logits = np.array([2.0, 1.0, 0.1])
probabilita = softmax(logits)
print(f"Softmax: {probabilita}")  # somma = 1.0
```

### Funzioni di Costo e Gradient Descent (Concettuale)

La **funzione di costo** (loss function) misura quanto le previsioni del modello si discostano dai valori reali. L'obiettivo del training e' **minimizzare** questa funzione.

Il **Gradient Descent** (discesa del gradiente) e' l'algoritmo di ottimizzazione piu' usato: si muove iterativamente nella direzione opposta al gradiente della funzione di costo per trovare il minimo.

```python
import numpy as np

# Esempio semplificato: regressione lineare con gradient descent
# y = wx + b (vogliamo trovare w e b ottimali)

np.random.seed(42)
X = 2 * np.random.rand(100, 1)
y = 4 + 3 * X + np.random.randn(100, 1) * 0.5  # y = 4 + 3x + rumore

# Funzione di costo: Mean Squared Error (MSE)
def calcola_mse(y_vero, y_predetto):
    return np.mean((y_vero - y_predetto) ** 2)

# Gradient Descent manuale
learning_rate = 0.1
n_iterazioni = 1000
m = len(X)

# Inizializzazione casuale dei parametri
w = np.random.randn(1, 1)
b = np.random.randn(1, 1)

for i in range(n_iterazioni):
    # Previsione
    y_pred = X @ w + b

    # Calcolo gradienti (derivate parziali della MSE)
    dw = (2/m) * X.T @ (y_pred - y)    # gradiente rispetto a w
    db = (2/m) * np.sum(y_pred - y)     # gradiente rispetto a b

    # Aggiornamento parametri (passo nella direzione opposta al gradiente)
    w -= learning_rate * dw
    b -= learning_rate * db

    if i % 200 == 0:
        mse = calcola_mse(y, y_pred)
        print(f"Iterazione {i}: MSE={mse:.4f}, w={w[0,0]:.4f}, b={b[0,0]:.4f}")

print(f"\nParametri trovati: w={w[0,0]:.4f} (atteso: 3), b={b[0,0]:.4f} (atteso: 4)")
```

---

## scikit-learn

**scikit-learn** e' la libreria di riferimento per il machine learning classico in Python. Offre un'API coerente, documentazione eccellente e un ecosistema completo di algoritmi.

### Fondamenti

#### Estimator API

Tutti i modelli in scikit-learn seguono la stessa interfaccia (API):

```python
from sklearn.ensemble import RandomForestClassifier

# 1. Creazione del modello (con iperparametri)
modello = RandomForestClassifier(n_estimators=100, random_state=42)

# 2. Training (fit) — il modello apprende dai dati
modello.fit(X_train, y_train)

# 3. Previsione (predict)
previsioni = modello.predict(X_test)

# 4. Probabilita' (predict_proba) — solo per classificatori
probabilita = modello.predict_proba(X_test)

# 5. Valutazione (score)
accuratezza = modello.score(X_test, y_test)
```

Per i **transformer** (es. scaler, encoder) l'API prevede:

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
scaler.fit(X_train)                # apprende parametri (media, std)
X_train_scaled = scaler.transform(X_train)  # trasforma i dati
X_test_scaled = scaler.transform(X_test)    # stessa trasformazione sui test

# Shortcut: fit + transform in un unico passo
X_train_scaled = scaler.fit_transform(X_train)
```

#### Train/Test Split

La suddivisione dei dati in **training set** e **test set** e' fondamentale per valutare il modello su dati mai visti.

```python
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris

# Caricamento dataset di esempio
iris = load_iris()
X, y = iris.data, iris.target

# Suddivisione: 80% training, 20% test
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,       # 20% per il test
    random_state=42,     # riproducibilita'
    stratify=y           # mantiene la proporzione delle classi
)

print(f"Training set: {X_train.shape[0]} campioni")
print(f"Test set: {X_test.shape[0]} campioni")
```

#### Cross-Validation

Invece di una singola suddivisione, la **cross-validation** valuta il modello su piu' suddivisioni diverse per una stima piu' robusta delle prestazioni.

```python
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier

modello = RandomForestClassifier(n_estimators=100, random_state=42)

# 5-fold cross-validation
scores = cross_val_score(modello, X, y, cv=5, scoring='accuracy')
print(f"Accuracy per fold: {scores}")
print(f"Accuracy media: {scores.mean():.4f} (+/- {scores.std():.4f})")
```

### Preprocessing

La preparazione dei dati e' spesso la fase piu' importante di un progetto ML. Dati ben preparati possono fare la differenza tra un modello mediocre e uno eccellente.

#### Scaling (Normalizzazione)

Molti algoritmi (SVM, KNN, reti neurali) sono sensibili alla scala delle feature.

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import numpy as np

X = np.array([[1, 1000, 0.5], [2, 2000, 0.8], [3, 1500, 0.3], [100, 3000, 0.9]])

# StandardScaler: media=0, std=1 (il piu' comune)
standard = StandardScaler()
X_standard = standard.fit_transform(X)

# MinMaxScaler: valori nell'intervallo [0, 1]
minmax = MinMaxScaler()
X_minmax = minmax.fit_transform(X)

# RobustScaler: usa mediana e IQR, robusto agli outlier
robust = RobustScaler()
X_robust = robust.fit_transform(X)

print("Originale:", X[0])
print("StandardScaler:", X_standard[0])
print("MinMaxScaler:", X_minmax[0])
print("RobustScaler:", X_robust[0])
```

#### Encoding Variabili Categoriche

Gli algoritmi ML lavorano con numeri. Le variabili categoriche devono essere convertite.

```python
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder
import numpy as np

# LabelEncoder: per la variabile target (y)
le = LabelEncoder()
classi = ["gatto", "cane", "gatto", "uccello", "cane"]
y_encoded = le.fit_transform(classi)
print(f"LabelEncoder: {y_encoded}")  # [1, 0, 1, 2, 0]
print(f"Classi: {le.classes_}")      # ['cane', 'gatto', 'uccello']

# OneHotEncoder: per feature nominali (senza ordine)
ohe = OneHotEncoder(sparse_output=False)
colori = np.array(["rosso", "blu", "verde", "rosso"]).reshape(-1, 1)
colori_encoded = ohe.fit_transform(colori)
print(f"OneHotEncoder:\n{colori_encoded}")
# [[0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1]]

# OrdinalEncoder: per feature con ordine intrinseco
oe = OrdinalEncoder(categories=[["basso", "medio", "alto"]])
livelli = np.array(["alto", "basso", "medio", "alto"]).reshape(-1, 1)
livelli_encoded = oe.fit_transform(livelli)
print(f"OrdinalEncoder: {livelli_encoded.ravel()}")  # [2, 0, 1, 2]
```

#### Gestione Valori Mancanti

```python
from sklearn.impute import SimpleImputer
import numpy as np

X = np.array([
    [1, 2, np.nan],
    [3, np.nan, 6],
    [7, 8, 9],
    [np.nan, 5, 3]
])

# Strategia: sostituire con la media della colonna
imputer_media = SimpleImputer(strategy='mean')
X_imputed = imputer_media.fit_transform(X)
print(f"Con media:\n{X_imputed}")

# Altre strategie disponibili
imputer_mediana = SimpleImputer(strategy='median')
imputer_frequente = SimpleImputer(strategy='most_frequent')
imputer_costante = SimpleImputer(strategy='constant', fill_value=0)
```

#### Feature Selection

Selezionare solo le feature piu' rilevanti migliora le prestazioni e riduce l'overfitting.

```python
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris

X, y = load_iris(return_X_y=True)

# SelectKBest: seleziona le K migliori feature in base a un test statistico
selector = SelectKBest(score_func=f_classif, k=2)
X_selected = selector.fit_transform(X, y)
print(f"Feature selezionate: {selector.get_support()}")
print(f"Scores: {selector.scores_}")

# RFE (Recursive Feature Elimination): rimozione ricorsiva
modello = RandomForestClassifier(n_estimators=50, random_state=42)
rfe = RFE(estimator=modello, n_features_to_select=2)
X_rfe = rfe.fit_transform(X, y)
print(f"Feature selezionate (RFE): {rfe.support_}")
print(f"Ranking: {rfe.ranking_}")
```

#### Pipeline e ColumnTransformer

Le **Pipeline** concatenano piu' passaggi di preprocessing e modellazione in un unico oggetto. Il **ColumnTransformer** applica trasformazioni diverse a colonne diverse.

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Colonne numeriche e categoriche
colonne_numeriche = [0, 1, 2]
colonne_categoriche = [3, 4]

# Pipeline per feature numeriche
pipeline_numerico = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

# Pipeline per feature categoriche
pipeline_categorico = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
])

# ColumnTransformer: applica pipeline diverse a colonne diverse
preprocessor = ColumnTransformer([
    ('num', pipeline_numerico, colonne_numeriche),
    ('cat', pipeline_categorico, colonne_categoriche)
])

# Pipeline completa: preprocessing + modello
pipeline_completa = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# Uso: un unico fit/predict gestisce tutto
# pipeline_completa.fit(X_train, y_train)
# previsioni = pipeline_completa.predict(X_test)
```

### Classificazione

#### Logistic Regression

Nonostante il nome, e' un algoritmo di **classificazione**. Modella la probabilita' di appartenenza a una classe usando la funzione sigmoide.

```python
from sklearn.linear_model import LogisticRegression

lr = LogisticRegression(
    C=1.0,              # inverso della forza di regolarizzazione
    max_iter=1000,
    random_state=42
)
lr.fit(X_train, y_train)
print(f"Accuracy: {lr.score(X_test, y_test):.4f}")
```

#### Decision Tree e Random Forest

Il **Decision Tree** suddivide lo spazio delle feature con regole if/else. Il **Random Forest** combina molti alberi (ensemble) per prestazioni migliori e meno overfitting.

```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# Decision Tree
dt = DecisionTreeClassifier(
    max_depth=5,           # profondita' massima (limita overfitting)
    min_samples_split=5,
    random_state=42
)
dt.fit(X_train, y_train)

# Random Forest
rf = RandomForestClassifier(
    n_estimators=200,      # numero di alberi
    max_depth=10,
    min_samples_leaf=2,
    n_jobs=-1,             # usa tutti i core CPU
    random_state=42
)
rf.fit(X_train, y_train)

# Importanza delle feature
importanze = rf.feature_importances_
for nome, imp in sorted(zip(feature_names, importanze), key=lambda x: -x[1]):
    print(f"  {nome}: {imp:.4f}")
```

#### Support Vector Machine (SVM)

SVM cerca l'iperpiano che massimizza il margine tra le classi. Eccellente con dati ad alta dimensionalita'.

```python
from sklearn.svm import SVC

svm = SVC(
    kernel='rbf',          # 'linear', 'poly', 'rbf', 'sigmoid'
    C=1.0,                 # regolarizzazione
    gamma='scale',         # coefficiente del kernel
    probability=True,      # abilita predict_proba
    random_state=42
)
svm.fit(X_train_scaled, y_train)  # SVM richiede dati scalati!
print(f"Accuracy: {svm.score(X_test_scaled, y_test):.4f}")
```

#### K-Nearest Neighbors (KNN)

Classifica un campione in base alla classe piu' frequente tra i K vicini piu' prossimi.

```python
from sklearn.neighbors import KNeighborsClassifier

knn = KNeighborsClassifier(
    n_neighbors=5,         # numero di vicini
    weights='distance',    # peso inversamente proporzionale alla distanza
    metric='minkowski',
    n_jobs=-1
)
knn.fit(X_train_scaled, y_train)  # KNN richiede dati scalati!
print(f"Accuracy: {knn.score(X_test_scaled, y_test):.4f}")
```

#### Gradient Boosting (XGBoost, LightGBM)

Algoritmi di ensemble che costruiscono alberi in sequenza, ciascuno che corregge gli errori del precedente. Tra i piu' potenti per dati tabulari.

```python
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# XGBoost
xgb = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    use_label_encoder=False,
    eval_metric='mlogloss'
)
xgb.fit(X_train, y_train)

# LightGBM (piu' veloce di XGBoost su grandi dataset)
lgbm = LGBMClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    num_leaves=31,
    random_state=42,
    verbose=-1
)
lgbm.fit(X_train, y_train)
```

#### Esempio Completo di Classificazione

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

# 1. Caricamento dati
data = load_breast_cancer()
X, y = data.data, data.target
feature_names = data.feature_names

# 2. Suddivisione
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 3. Definizione modelli con pipeline
modelli = {
    "Logistic Regression": Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, random_state=42))
    ]),
    "Random Forest": Pipeline([
        ('clf', RandomForestClassifier(n_estimators=200, random_state=42))
    ]),
    "SVM": Pipeline([
        ('scaler', StandardScaler()),
        ('clf', SVC(kernel='rbf', probability=True, random_state=42))
    ]),
    "KNN": Pipeline([
        ('scaler', StandardScaler()),
        ('clf', KNeighborsClassifier(n_neighbors=5))
    ]),
    "Gradient Boosting": Pipeline([
        ('clf', GradientBoostingClassifier(n_estimators=200, random_state=42))
    ])
}

# 4. Training e valutazione
risultati = {}
for nome, pipeline in modelli.items():
    # Cross-validation
    scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
    risultati[nome] = scores.mean()

    # Training e test
    pipeline.fit(X_train, y_train)
    acc_test = pipeline.score(X_test, y_test)

    print(f"{nome}:")
    print(f"  CV Accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")
    print(f"  Test Accuracy: {acc_test:.4f}")

# 5. Report dettagliato del miglior modello
miglior_nome = max(risultati, key=risultati.get)
miglior_modello = modelli[miglior_nome]
y_pred = miglior_modello.predict(X_test)

print(f"\n--- Miglior modello: {miglior_nome} ---")
print(classification_report(y_test, y_pred, target_names=data.target_names))
print(f"Matrice di confusione:\n{confusion_matrix(y_test, y_pred)}")
```

### Regressione

#### Linear Regression e Varianti Regolarizzate

```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet

# Linear Regression: base, senza regolarizzazione
lr = LinearRegression()
lr.fit(X_train, y_train)
print(f"Coefficienti: {lr.coef_}")
print(f"Intercetta: {lr.intercept_}")

# Ridge (L2): penalizza coefficienti grandi
ridge = Ridge(alpha=1.0)  # alpha controlla la regolarizzazione
ridge.fit(X_train, y_train)

# Lasso (L1): puo' azzerare coefficienti (feature selection implicita)
lasso = Lasso(alpha=0.1)
lasso.fit(X_train, y_train)
print(f"Feature con coefficiente != 0: {np.sum(lasso.coef_ != 0)}")

# ElasticNet: combinazione di L1 e L2
elastic = ElasticNet(alpha=0.1, l1_ratio=0.5)  # l1_ratio: bilancio L1/L2
elastic.fit(X_train, y_train)
```

#### Random Forest Regressor

```python
from sklearn.ensemble import RandomForestRegressor

rf_reg = RandomForestRegressor(
    n_estimators=200,
    max_depth=10,
    min_samples_leaf=5,
    n_jobs=-1,
    random_state=42
)
rf_reg.fit(X_train, y_train)
print(f"R² score: {rf_reg.score(X_test, y_test):.4f}")
```

#### Esempio Completo di Regressione

```python
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

# 1. Caricamento dati
housing = fetch_california_housing()
X, y = housing.data, housing.target

# 2. Suddivisione
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3. Modelli
modelli = {
    "Linear Regression": Pipeline([
        ('scaler', StandardScaler()),
        ('reg', LinearRegression())
    ]),
    "Ridge": Pipeline([
        ('scaler', StandardScaler()),
        ('reg', Ridge(alpha=1.0))
    ]),
    "Lasso": Pipeline([
        ('scaler', StandardScaler()),
        ('reg', Lasso(alpha=0.01))
    ]),
    "Random Forest": Pipeline([
        ('reg', RandomForestRegressor(n_estimators=100, random_state=42))
    ]),
    "Gradient Boosting": Pipeline([
        ('reg', GradientBoostingRegressor(n_estimators=200, random_state=42))
    ])
}

# 4. Valutazione
for nome, pipeline in modelli.items():
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"{nome}:")
    print(f"  RMSE={rmse:.4f}, MAE={mae:.4f}, R²={r2:.4f}")
```

### Clustering

#### K-Means

Partiziona i dati in K cluster minimizzando la distanza intra-cluster.

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

# Scaling e' essenziale per il clustering
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# K-Means
kmeans = KMeans(
    n_clusters=3,
    init='k-means++',     # inizializzazione intelligente
    n_init=10,             # numero di inizializzazioni
    max_iter=300,
    random_state=42
)
cluster_labels = kmeans.fit_predict(X_scaled)

print(f"Centroidi: {kmeans.cluster_centers_.shape}")
print(f"Inerzia (somma distanze intra-cluster): {kmeans.inertia_:.2f}")
print(f"Distribuzione cluster: {np.bincount(cluster_labels)}")

# Metodo del gomito per scegliere K ottimale
inerzie = []
K_range = range(2, 11)
for k in K_range:
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km.fit(X_scaled)
    inerzie.append(km.inertia_)
```

#### DBSCAN

Algoritmo basato sulla densita'. Non richiede di specificare il numero di cluster e puo' individuare cluster di forma arbitraria e outlier.

```python
from sklearn.cluster import DBSCAN

dbscan = DBSCAN(
    eps=0.5,              # raggio di vicinato
    min_samples=5,        # minimo campioni per un core point
    metric='euclidean'
)
labels = dbscan.fit_predict(X_scaled)

n_cluster = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = list(labels).count(-1)
print(f"Cluster trovati: {n_cluster}")
print(f"Punti di rumore: {n_noise}")
```

#### Clustering Gerarchico

Costruisce una gerarchia di cluster (dendrogram). Utile quando si vuole esplorare la struttura a diversi livelli di granularita'.

```python
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage

# Agglomerative Clustering
agg = AgglomerativeClustering(
    n_clusters=3,
    linkage='ward'        # 'ward', 'complete', 'average', 'single'
)
labels = agg.fit_predict(X_scaled)

# Dendrogramma con scipy (per la visualizzazione)
Z = linkage(X_scaled, method='ward')
# dendrogram(Z)  # da visualizzare con matplotlib
```

#### Silhouette Score

Metrica per valutare la qualita' dei cluster. Valori vicini a 1 indicano cluster ben separati.

```python
from sklearn.metrics import silhouette_score, silhouette_samples

# Score globale
score = silhouette_score(X_scaled, cluster_labels)
print(f"Silhouette Score: {score:.4f}")  # da -1 a 1

# Score per singolo campione
sample_scores = silhouette_samples(X_scaled, cluster_labels)
print(f"Silhouette media per cluster:")
for i in range(3):
    mask = cluster_labels == i
    print(f"  Cluster {i}: {sample_scores[mask].mean():.4f}")
```

### Valutazione Modelli

#### Metriche di Classificazione

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)

y_pred = modello.predict(X_test)
y_proba = modello.predict_proba(X_test)[:, 1]  # probabilita' classe positiva

# Metriche fondamentali
accuracy = accuracy_score(y_test, y_pred)       # (TP+TN) / totale
precision = precision_score(y_test, y_pred)     # TP / (TP+FP) — quanti positivi predetti sono corretti
recall = recall_score(y_test, y_pred)           # TP / (TP+FN) — quanti positivi reali sono stati trovati
f1 = f1_score(y_test, y_pred)                   # media armonica di precision e recall

print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")

# Matrice di confusione
cm = confusion_matrix(y_test, y_pred)
print(f"Matrice di confusione:\n{cm}")
# [[TN, FP],
#  [FN, TP]]

# Report completo
print(classification_report(y_test, y_pred, target_names=["benigno", "maligno"]))

# ROC-AUC (Area Under the ROC Curve)
auc = roc_auc_score(y_test, y_proba)
print(f"ROC-AUC: {auc:.4f}")

# Curva ROC (per la visualizzazione)
fpr, tpr, thresholds = roc_curve(y_test, y_proba)
```

#### Metriche di Regressione

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

y_pred = modello.predict(X_test)

mse = mean_squared_error(y_test, y_pred)      # errore quadratico medio
rmse = np.sqrt(mse)                            # radice di MSE (stessa unita' di y)
mae = mean_absolute_error(y_test, y_pred)      # errore assoluto medio
r2 = r2_score(y_test, y_pred)                  # coefficiente di determinazione (0-1)

print(f"MSE: {mse:.4f}")
print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"R²: {r2:.4f}")  # 1.0 = previsione perfetta, 0.0 = modello banale
```

#### Strategie di Cross-Validation

```python
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score

# KFold: suddivisione base in K parti
kfold = KFold(n_splits=5, shuffle=True, random_state=42)

# StratifiedKFold: mantiene le proporzioni delle classi in ogni fold
# (raccomandato per classificazione con classi sbilanciate)
stratified = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

scores = cross_val_score(modello, X, y, cv=stratified, scoring='f1_weighted')
print(f"F1 per fold: {scores}")
print(f"F1 medio: {scores.mean():.4f} (+/- {scores.std():.4f})")
```

#### Hyperparameter Tuning

La ricerca degli iperparametri ottimali puo' migliorare significativamente le prestazioni.

```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import randint, uniform

modello = RandomForestClassifier(random_state=42)

# GridSearchCV: prova TUTTE le combinazioni (esaustivo ma lento)
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [5, 10, 15, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

grid_search = GridSearchCV(
    modello,
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    verbose=1
)
grid_search.fit(X_train, y_train)

print(f"Migliori parametri: {grid_search.best_params_}")
print(f"Miglior score CV: {grid_search.best_score_:.4f}")
print(f"Score test: {grid_search.score(X_test, y_test):.4f}")

# RandomizedSearchCV: campiona combinazioni casuali (piu' veloce)
param_distributions = {
    'n_estimators': randint(50, 500),
    'max_depth': [5, 10, 15, 20, None],
    'min_samples_split': randint(2, 20),
    'min_samples_leaf': randint(1, 10),
    'max_features': uniform(0.1, 0.9)
}

random_search = RandomizedSearchCV(
    modello,
    param_distributions,
    n_iter=100,            # numero di combinazioni da provare
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    random_state=42,
    verbose=1
)
random_search.fit(X_train, y_train)

print(f"Migliori parametri: {random_search.best_params_}")
print(f"Miglior score CV: {random_search.best_score_:.4f}")
```

#### Rilevamento Overfitting e Underfitting

```python
from sklearn.model_selection import learning_curve
import numpy as np

# Learning curve: mostra come variano le performance
# al crescere dei dati di training
train_sizes, train_scores, val_scores = learning_curve(
    modello, X, y,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)

train_mean = train_scores.mean(axis=1)
val_mean = val_scores.mean(axis=1)

# Interpretazione:
# - train_score alto, val_score basso -> OVERFITTING
#   Soluzione: piu' dati, regolarizzazione, modello piu' semplice
# - train_score basso, val_score basso -> UNDERFITTING
#   Soluzione: modello piu' complesso, piu' feature, meno regolarizzazione
# - train_score ~ val_score (entrambi alti) -> buon fit

for size, t_score, v_score in zip(train_sizes, train_mean, val_mean):
    gap = t_score - v_score
    stato = "OVERFIT" if gap > 0.1 else "OK"
    print(f"  Campioni: {size}, Train: {t_score:.4f}, Val: {v_score:.4f}, Gap: {gap:.4f} [{stato}]")
```

---

## pandas per ML

**pandas** e' lo strumento principale per la preparazione dei dati prima di darli in pasto a un modello ML.

### Esplorazione Dati (EDA)

```python
import pandas as pd
import numpy as np

# Caricamento e prima esplorazione
df = pd.read_csv("dataset.csv")

# Informazioni generali
print(df.shape)               # (righe, colonne)
print(df.info())              # tipi, valori non-null per colonna
print(df.describe())          # statistiche descrittive per colonne numeriche
print(df.describe(include='object'))  # per colonne categoriche

# Distribuzione della variabile target
print(df['target'].value_counts())
print(df['target'].value_counts(normalize=True))  # percentuali

# Valori mancanti
print(df.isnull().sum())
print(df.isnull().sum() / len(df) * 100)  # percentuale mancanti

# Correlazione tra feature numeriche
correlazione = df.select_dtypes(include=[np.number]).corr()
print(correlazione)

# Feature piu' correlate con il target
print(correlazione['target'].sort_values(ascending=False))
```

### Feature Engineering

Creare nuove feature a partire da quelle esistenti puo' migliorare drasticamente le prestazioni del modello.

```python
import pandas as pd

# Combinazione di feature
df['reddito_per_membro'] = df['reddito'] / df['membri_famiglia']
df['area_totale'] = df['lunghezza'] * df['larghezza']

# Feature da date
df['data'] = pd.to_datetime(df['data'])
df['anno'] = df['data'].dt.year
df['mese'] = df['data'].dt.month
df['giorno_settimana'] = df['data'].dt.dayofweek
df['is_weekend'] = df['giorno_settimana'].isin([5, 6]).astype(int)

# Binning (discretizzazione)
df['fascia_eta'] = pd.cut(df['eta'], bins=[0, 18, 30, 50, 65, 100],
                          labels=['minore', 'giovane', 'adulto', 'senior', 'anziano'])

# Feature logaritmiche (per distribuzioni asimmetriche)
df['log_reddito'] = np.log1p(df['reddito'])  # log(1 + x) per gestire zero

# Feature polinomiali
df['eta_squared'] = df['eta'] ** 2
```

### Gestione Dati Categorici

```python
import pandas as pd

# Metodo 1: get_dummies (one-hot encoding diretto in pandas)
df_encoded = pd.get_dummies(df, columns=['citta', 'professione'], drop_first=True)

# Metodo 2: map per encoding ordinale
mappa_istruzione = {'elementare': 1, 'media': 2, 'superiore': 3, 'laurea': 4}
df['istruzione_num'] = df['istruzione'].map(mappa_istruzione)

# Metodo 3: Target encoding (media del target per categoria)
target_means = df.groupby('citta')['prezzo'].mean()
df['citta_target_enc'] = df['citta'].map(target_means)

# Metodo 4: Frequency encoding (frequenza della categoria)
freq = df['citta'].value_counts(normalize=True)
df['citta_freq'] = df['citta'].map(freq)
```

### Gestione Valori Mancanti

```python
import pandas as pd

# Analisi dei mancanti
print(df.isnull().sum().sort_values(ascending=False))

# Rimozione righe/colonne
df_clean = df.dropna(subset=['colonna_importante'])          # righe con NaN nella colonna
df_clean = df.drop(columns=['colonna_troppi_nan'])           # colonne con troppi NaN

# Imputation
df['eta'].fillna(df['eta'].median(), inplace=True)           # mediana
df['citta'].fillna(df['citta'].mode()[0], inplace=True)      # moda (valore piu' frequente)
df['valore'].fillna(method='ffill', inplace=True)            # forward fill (serie temporali)

# Imputation per gruppo
df['reddito'] = df.groupby('professione')['reddito'].transform(
    lambda x: x.fillna(x.median())
)

# Flag per valori mancanti (a volte il fatto che manchi e' informativo)
df['reddito_mancante'] = df['reddito'].isnull().astype(int)
```

### Visualizzazione per EDA

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Distribuzione delle feature numeriche
df.hist(figsize=(15, 10), bins=30)
plt.tight_layout()
plt.savefig("distribuzioni.png")

# Boxplot per identificare outlier
df.boxplot(column=['eta', 'reddito', 'spesa'], figsize=(10, 6))
plt.savefig("boxplot.png")

# Matrice di correlazione
plt.figure(figsize=(12, 8))
sns.heatmap(df.corr(numeric_only=True), annot=True, cmap='coolwarm', center=0)
plt.title("Matrice di Correlazione")
plt.tight_layout()
plt.savefig("correlazione.png")
```

---

## Visualizzazione

La visualizzazione dei dati e' cruciale sia nella fase esplorativa (EDA) sia nella presentazione dei risultati del modello.

### matplotlib

La libreria di base per la visualizzazione in Python. Offre controllo completo su ogni aspetto dei grafici.

```python
import matplotlib.pyplot as plt
import numpy as np

# --- Line Plot ---
x = np.linspace(0, 10, 100)
plt.figure(figsize=(10, 6))
plt.plot(x, np.sin(x), label='sin(x)', linewidth=2)
plt.plot(x, np.cos(x), label='cos(x)', linewidth=2, linestyle='--')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Funzioni Trigonometriche')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("line_plot.png", dpi=150)
plt.close()

# --- Scatter Plot ---
np.random.seed(42)
x = np.random.randn(200)
y = 2 * x + np.random.randn(200) * 0.5
colori = np.random.choice(['blue', 'red'], size=200)

plt.figure(figsize=(8, 6))
plt.scatter(x, y, c=colori, alpha=0.6, edgecolors='black', linewidth=0.5)
plt.xlabel('Feature X')
plt.ylabel('Feature Y')
plt.title('Scatter Plot con Colori per Classe')
plt.savefig("scatter.png", dpi=150)
plt.close()

# --- Istogramma ---
dati = np.random.normal(100, 15, 1000)
plt.figure(figsize=(8, 5))
plt.hist(dati, bins=40, color='steelblue', edgecolor='black', alpha=0.7)
plt.axvline(np.mean(dati), color='red', linestyle='--', label=f'Media: {np.mean(dati):.1f}')
plt.xlabel('Valore')
plt.ylabel('Frequenza')
plt.title('Distribuzione Normale')
plt.legend()
plt.savefig("istogramma.png", dpi=150)
plt.close()

# --- Bar Chart ---
categorie = ['Random Forest', 'SVM', 'KNN', 'Logistic Reg', 'XGBoost']
accuracy = [0.95, 0.93, 0.91, 0.89, 0.96]

plt.figure(figsize=(10, 6))
bars = plt.barh(categorie, accuracy, color='teal', edgecolor='black')
plt.xlabel('Accuracy')
plt.title('Confronto Modelli')
plt.xlim(0.85, 1.0)
for bar, acc in zip(bars, accuracy):
    plt.text(acc + 0.002, bar.get_y() + bar.get_height()/2,
             f'{acc:.2%}', va='center')
plt.tight_layout()
plt.savefig("bar_chart.png", dpi=150)
plt.close()

# --- Subplots ---
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

axes[0, 0].plot(x, np.sin(x))
axes[0, 0].set_title('Seno')

axes[0, 1].scatter(np.random.randn(50), np.random.randn(50))
axes[0, 1].set_title('Scatter')

axes[1, 0].hist(np.random.randn(500), bins=30)
axes[1, 0].set_title('Istogramma')

axes[1, 1].bar(['A', 'B', 'C', 'D'], [25, 40, 30, 55])
axes[1, 1].set_title('Barre')

plt.suptitle('Dashboard di Esempio', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("subplots.png", dpi=150)
plt.close()
```

### seaborn

Costruita sopra matplotlib, seaborn semplifica la creazione di grafici statistici esteticamente gradevoli.

```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

sns.set_theme(style="whitegrid")

# --- Heatmap della Matrice di Correlazione ---
df = pd.DataFrame(np.random.randn(100, 6), columns=['A', 'B', 'C', 'D', 'E', 'F'])
corr = df.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, square=True, linewidths=0.5)
plt.title('Matrice di Correlazione')
plt.tight_layout()
plt.savefig("heatmap.png", dpi=150)
plt.close()

# --- Distribution Plots ---
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Istogramma con KDE
sns.histplot(data=df, x='A', kde=True, ax=axes[0])
axes[0].set_title('Distribuzione con KDE')

# KDE plot sovrapposti
sns.kdeplot(data=df[['A', 'B', 'C']], ax=axes[1])
axes[1].set_title('Confronto Distribuzioni')

# Boxplot
sns.boxplot(data=df[['A', 'B', 'C', 'D']], ax=axes[2])
axes[2].set_title('Boxplot')

plt.tight_layout()
plt.savefig("distribuzioni_seaborn.png", dpi=150)
plt.close()

# --- Pairplot (matrice scatter di tutte le coppie di feature) ---
# Molto utile in EDA per individuare relazioni tra feature
from sklearn.datasets import load_iris
iris = load_iris()
iris_df = pd.DataFrame(iris.data, columns=iris.feature_names)
iris_df['species'] = iris.target

sns.pairplot(iris_df, hue='species', palette='Set2', diag_kind='kde')
plt.suptitle('Pairplot del Dataset Iris', y=1.02)
plt.savefig("pairplot.png", dpi=150)
plt.close()

# --- Matrice di confusione come heatmap ---
from sklearn.metrics import confusion_matrix

y_true = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0]
y_pred = [0, 1, 0, 0, 1, 1, 0, 1, 1, 0]
cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Negativo', 'Positivo'],
            yticklabels=['Negativo', 'Positivo'])
plt.xlabel('Predetto')
plt.ylabel('Reale')
plt.title('Matrice di Confusione')
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=150)
plt.close()
```

---

## Deep Learning (Panoramica)

Il deep learning usa **reti neurali artificiali** con molti strati (layer) per apprendere rappresentazioni complesse dei dati. E' particolarmente efficace per immagini, testo, audio e dati non strutturati.

### TensorFlow/Keras

**Keras** (integrato in TensorFlow) offre un'API di alto livello per costruire e addestrare reti neurali in modo semplice e intuitivo.

```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np

# --- Modello Sequential per classificazione binaria ---

# Preparazione dati (esempio)
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

data = load_breast_cancer()
X, y = data.data, data.target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Costruzione del modello
modello = keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    layers.Dropout(0.3),                # regolarizzazione
    layers.Dense(32, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(1, activation='sigmoid')  # output binario
])

# Compilazione
modello.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Riepilogo architettura
modello.summary()

# Training
history = modello.fit(
    X_train, y_train,
    epochs=50,
    batch_size=32,
    validation_split=0.2,    # 20% del training per validazione
    verbose=1
)

# Valutazione
loss, accuracy = modello.evaluate(X_test, y_test, verbose=0)
print(f"Test Loss: {loss:.4f}")
print(f"Test Accuracy: {accuracy:.4f}")

# Previsioni
previsioni = (modello.predict(X_test) > 0.5).astype(int)

# Visualizzazione della training history
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.plot(history.history['loss'], label='Training')
ax1.plot(history.history['val_loss'], label='Validazione')
ax1.set_title('Loss')
ax1.legend()

ax2.plot(history.history['accuracy'], label='Training')
ax2.plot(history.history['val_accuracy'], label='Validazione')
ax2.set_title('Accuracy')
ax2.legend()

plt.tight_layout()
plt.savefig("training_history.png", dpi=150)
```

### PyTorch

**PyTorch** offre un approccio piu' flessibile e "pythonico" al deep learning, con grafi computazionali dinamici. Preferito nella ricerca accademica.

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np

# Preparazione dati
data = load_breast_cancer()
X, y = data.data, data.target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Conversione a tensori PyTorch
X_train_t = torch.FloatTensor(X_train)
y_train_t = torch.FloatTensor(y_train).unsqueeze(1)
X_test_t = torch.FloatTensor(X_test)
y_test_t = torch.FloatTensor(y_test).unsqueeze(1)

# DataLoader per batch training
train_dataset = TensorDataset(X_train_t, y_train_t)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Definizione del modello con nn.Module
class ClassificatoreBinario(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.network(x)

# Inizializzazione
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
modello = ClassificatoreBinario(X_train.shape[1]).to(device)
criterion = nn.BCELoss()
optimizer = optim.Adam(modello.parameters(), lr=0.001)

# Training loop
n_epochs = 50
for epoch in range(n_epochs):
    modello.train()
    epoch_loss = 0

    for batch_X, batch_y in train_loader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)

        # Forward pass
        output = modello(batch_X)
        loss = criterion(output, batch_y)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1}/{n_epochs}, Loss: {epoch_loss/len(train_loader):.4f}")

# Valutazione
modello.eval()
with torch.no_grad():
    X_test_dev = X_test_t.to(device)
    predictions = modello(X_test_dev)
    predicted_classes = (predictions > 0.5).float()
    accuracy = (predicted_classes.cpu() == y_test_t).float().mean()
    print(f"Test Accuracy: {accuracy:.4f}")
```

---

## MLOps Essenziali

MLOps comprende le pratiche per portare i modelli ML in produzione e mantenerli nel tempo in modo affidabile.

### Serializzazione dei Modelli

Salvare un modello addestrato per riutilizzarlo senza riaddestrarlo ogni volta.

```python
import joblib
import pickle
from sklearn.ensemble import RandomForestClassifier

# Training del modello
modello = RandomForestClassifier(n_estimators=200, random_state=42)
modello.fit(X_train, y_train)

# --- joblib (raccomandato per scikit-learn) ---
joblib.dump(modello, 'modello_rf.joblib')
modello_caricato = joblib.load('modello_rf.joblib')
print(f"Accuracy: {modello_caricato.score(X_test, y_test):.4f}")

# --- pickle (standard Python) ---
with open('modello_rf.pkl', 'wb') as f:
    pickle.dump(modello, f)

with open('modello_rf.pkl', 'rb') as f:
    modello_pkl = pickle.load(f)

# --- Salvare anche il preprocessor ---
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', RandomForestClassifier(n_estimators=200, random_state=42))
])
pipeline.fit(X_train, y_train)
joblib.dump(pipeline, 'pipeline_completa.joblib')

# --- ONNX (formato interoperabile, per deployment cross-platform) ---
# pip install skl2onnx onnxruntime
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt

# Conversione a ONNX
initial_type = [('float_input', FloatTensorType([None, X_train.shape[1]]))]
onnx_model = convert_sklearn(modello, initial_types=initial_type)

with open("modello.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

# Inferenza con ONNX Runtime (piu' veloce di sklearn)
session = rt.InferenceSession("modello.onnx")
input_name = session.get_inputs()[0].name
pred_onnx = session.run(None, {input_name: X_test.astype('float32')})[0]
```

### Experiment Tracking con MLflow

MLflow tiene traccia di esperimenti, parametri, metriche e artefatti (modelli salvati).

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

# Configurazione (opzionale: URI del tracking server)
# mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("classificazione-tumore")

# Training con tracking
params = {
    "n_estimators": 200,
    "max_depth": 10,
    "min_samples_split": 5
}

with mlflow.start_run(run_name="random_forest_v1"):
    # Log dei parametri
    mlflow.log_params(params)

    # Training
    modello = RandomForestClassifier(**params, random_state=42)
    modello.fit(X_train, y_train)

    # Previsioni e metriche
    y_pred = modello.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    # Log delle metriche
    mlflow.log_metrics({
        "accuracy": accuracy,
        "f1_score": f1
    })

    # Log del modello come artefatto
    mlflow.sklearn.log_model(modello, "modello")

    # Log di file aggiuntivi
    # mlflow.log_artifact("confusion_matrix.png")

    print(f"Run ID: {mlflow.active_run().info.run_id}")
    print(f"Accuracy: {accuracy:.4f}, F1: {f1:.4f}")

# Caricamento del modello da MLflow
# model_uri = "runs:/<run_id>/modello"
# modello_caricato = mlflow.sklearn.load_model(model_uri)
```

### Model Serving con FastAPI

Servire un modello ML come API REST per renderlo accessibile ad altre applicazioni.

```python
# file: serve_model.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
from typing import List

app = FastAPI(title="ML Model API", version="1.0.0")

# Caricamento del modello all'avvio
pipeline = joblib.load("pipeline_completa.joblib")

# Schema di input
class PredictionInput(BaseModel):
    features: List[float]

    class Config:
        json_schema_extra = {
            "example": {
                "features": [14.0, 20.0, 90.0, 600.0, 0.1, 0.15,
                             0.2, 0.08, 0.18, 0.06, 0.5, 1.2,
                             3.5, 40.0, 0.006, 0.02, 0.03, 0.01,
                             0.02, 0.003, 16.0, 28.0, 105.0, 800.0,
                             0.13, 0.3, 0.4, 0.15, 0.3, 0.08]
            }
        }

class PredictionOutput(BaseModel):
    prediction: int
    probability: List[float]
    label: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="healthy", model_loaded=pipeline is not None)

@app.post("/predict", response_model=PredictionOutput)
def predict(input_data: PredictionInput):
    try:
        X = np.array(input_data.features).reshape(1, -1)
        prediction = pipeline.predict(X)[0]
        probability = pipeline.predict_proba(X)[0].tolist()
        label = "maligno" if prediction == 0 else "benigno"

        return PredictionOutput(
            prediction=int(prediction),
            probability=probability,
            label=label
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/batch")
def predict_batch(inputs: List[PredictionInput]):
    X = np.array([inp.features for inp in inputs])
    predictions = pipeline.predict(X).tolist()
    probabilities = pipeline.predict_proba(X).tolist()

    return {
        "predictions": predictions,
        "probabilities": probabilities,
        "count": len(predictions)
    }

# Avvio: uvicorn serve_model:app --host 0.0.0.0 --port 8000
```

---

## Applicazioni Pratiche per IT

### Rilevamento Anomalie nei Log e nelle Metriche

Identificare automaticamente comportamenti anomali nei sistemi informatici.

```python
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

# Simulazione dati di metriche di sistema
np.random.seed(42)
n_samples = 1000

dati_normali = pd.DataFrame({
    'cpu_usage': np.random.normal(45, 10, n_samples),
    'memory_usage': np.random.normal(60, 8, n_samples),
    'disk_io': np.random.normal(200, 50, n_samples),
    'network_bytes': np.random.normal(1000, 200, n_samples),
    'response_time_ms': np.random.normal(100, 20, n_samples),
    'error_rate': np.random.normal(0.02, 0.01, n_samples)
})

# Aggiunta di anomalie
anomalie = pd.DataFrame({
    'cpu_usage': [95, 98, 10, 92],
    'memory_usage': [95, 90, 85, 98],
    'disk_io': [800, 700, 50, 900],
    'network_bytes': [5000, 100, 4500, 50],
    'response_time_ms': [500, 600, 400, 800],
    'error_rate': [0.15, 0.20, 0.10, 0.25]
})

df = pd.concat([dati_normali, anomalie], ignore_index=True)

# Preprocessing
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df)

# Isolation Forest per anomaly detection
iso_forest = IsolationForest(
    contamination=0.01,    # percentuale attesa di anomalie
    random_state=42,
    n_estimators=200
)

df['anomaly'] = iso_forest.fit_predict(X_scaled)
# -1 = anomalia, 1 = normale

anomalie_trovate = df[df['anomaly'] == -1]
print(f"Anomalie rilevate: {len(anomalie_trovate)}")
print(anomalie_trovate)
```

### Classificazione del Traffico di Rete

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np

# Simulazione dataset di traffico di rete
np.random.seed(42)
n = 5000

df_traffic = pd.DataFrame({
    'duration': np.random.exponential(10, n),
    'protocol': np.random.choice(['TCP', 'UDP', 'ICMP'], n, p=[0.7, 0.2, 0.1]),
    'src_bytes': np.random.exponential(5000, n),
    'dst_bytes': np.random.exponential(3000, n),
    'packets': np.random.poisson(20, n),
    'flag': np.random.choice(['SF', 'S0', 'REJ', 'RSTO'], n),
    'label': np.random.choice(['normal', 'dos', 'probe', 'r2l'], n, p=[0.6, 0.2, 0.1, 0.1])
})

# Preprocessing
le_protocol = LabelEncoder()
le_flag = LabelEncoder()
le_label = LabelEncoder()

df_traffic['protocol_enc'] = le_protocol.fit_transform(df_traffic['protocol'])
df_traffic['flag_enc'] = le_flag.fit_transform(df_traffic['flag'])
df_traffic['label_enc'] = le_label.fit_transform(df_traffic['label'])

feature_cols = ['duration', 'src_bytes', 'dst_bytes', 'packets', 'protocol_enc', 'flag_enc']
X = df_traffic[feature_cols].values
y = df_traffic['label_enc'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Training
clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
clf.fit(X_train, y_train)

# Valutazione
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred, target_names=le_label.classes_))
```

### Manutenzione Predittiva

Prevedere quando un componente potrebbe guastarsi per intervenire prima del fallimento.

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import numpy as np

# Simulazione dati sensori di una macchina industriale
np.random.seed(42)
n = 3000

df_maint = pd.DataFrame({
    'temperatura': np.random.normal(70, 5, n),
    'vibrazione': np.random.normal(30, 3, n),
    'pressione': np.random.normal(100, 10, n),
    'ore_funzionamento': np.random.uniform(0, 10000, n),
    'eta_componente_giorni': np.random.uniform(0, 365, n),
    'ultimo_manutenzione_giorni': np.random.uniform(0, 90, n),
})

# Creazione target: guasto imminente (basato su regole + rumore)
condizione_rischio = (
    (df_maint['temperatura'] > 78) |
    (df_maint['vibrazione'] > 35) |
    (df_maint['ore_funzionamento'] > 8000) |
    (df_maint['ultimo_manutenzione_giorni'] > 60)
)
df_maint['guasto_imminente'] = (condizione_rischio & (np.random.random(n) > 0.3)).astype(int)

X = df_maint.drop('guasto_imminente', axis=1).values
y = df_maint['guasto_imminente'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Gradient Boosting (buone performance con dati sbilanciati)
gb = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)
gb.fit(X_train, y_train)

y_pred = gb.predict(X_test)
print(classification_report(y_test, y_pred, target_names=['Normale', 'Guasto Imminente']))
```

### Capacity Planning con Serie Temporali

Prevedere il carico futuro per pianificare le risorse infrastrutturali.

```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import pandas as pd
import numpy as np

# Simulazione dati di carico server (ultimi 365 giorni)
np.random.seed(42)
date = pd.date_range('2025-01-01', periods=365, freq='D')
trend = np.linspace(50, 80, 365)                          # trend crescente
stagionalita = 10 * np.sin(2 * np.pi * np.arange(365) / 7)  # ciclo settimanale
rumore = np.random.normal(0, 3, 365)
carico = trend + stagionalita + rumore

df_ts = pd.DataFrame({'data': date, 'carico_cpu': carico})

# Feature engineering per serie temporali
df_ts['giorno_settimana'] = df_ts['data'].dt.dayofweek
df_ts['giorno_mese'] = df_ts['data'].dt.day
df_ts['mese'] = df_ts['data'].dt.month
df_ts['giorno_anno'] = df_ts['data'].dt.dayofyear

# Lag features (valori passati come feature)
for lag in [1, 3, 7, 14, 30]:
    df_ts[f'lag_{lag}'] = df_ts['carico_cpu'].shift(lag)

# Media mobile
df_ts['media_mobile_7'] = df_ts['carico_cpu'].rolling(window=7).mean()
df_ts['media_mobile_30'] = df_ts['carico_cpu'].rolling(window=30).mean()

# Rimozione righe con NaN (causate da shift e rolling)
df_ts = df_ts.dropna()

feature_cols = ['giorno_settimana', 'giorno_mese', 'mese', 'giorno_anno',
                'lag_1', 'lag_3', 'lag_7', 'lag_14', 'lag_30',
                'media_mobile_7', 'media_mobile_30']

X = df_ts[feature_cols].values
y = df_ts['carico_cpu'].values

# Split temporale (non casuale! Rispettiamo l'ordine cronologico)
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# Modello
gb_reg = GradientBoostingRegressor(n_estimators=200, max_depth=5, random_state=42)
gb_reg.fit(X_train, y_train)

y_pred = gb_reg.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"MAE: {mae:.2f}% CPU")
print(f"Il modello puo' prevedere il carico con un errore medio di ~{mae:.1f}% CPU")
```

---

## Best Practices

1. **Iniziare sempre dall'esplorazione dei dati (EDA)**. Prima di applicare qualsiasi modello, dedica tempo a capire i dati: distribuzioni, correlazioni, valori mancanti, outlier. Un modello addestrato su dati mal compresi produce risultati inaffidabili. Usa `describe()`, `value_counts()`, `corr()` e grafici (heatmap, pairplot, boxplot).

2. **Separare rigorosamente training e test set**. Il test set non deve mai influenzare nessuna decisione presa durante il training, nemmeno la fase di preprocessing. Esegui `fit()` solo sul training set e `transform()` su entrambi. Usa le **Pipeline** di scikit-learn per garantire che il flusso sia corretto ed evitare data leakage.

3. **Usare la cross-validation per valutazioni affidabili**. Una singola suddivisione train/test puo' dare risultati fuorvianti. La cross-validation (specialmente `StratifiedKFold` per la classificazione) fornisce una stima piu' robusta delle prestazioni e della loro variabilita'. Usa `cross_val_score` come prima valutazione di qualsiasi modello.

4. **Scegliere la metrica giusta per il problema**. L'accuracy e' fuorviante con classi sbilanciate (es. 95% classe A, 5% classe B: un modello che predice sempre A ha 95% accuracy ma e' inutile). Per classi sbilanciate usa F1 score, precision/recall, o ROC-AUC. Per regressione, scegli tra RMSE (penalizza errori grandi) e MAE (piu' robusto agli outlier).

5. **Non sottovalutare il preprocessing e il feature engineering**. La qualita' dei dati e delle feature e' piu' importante della complessita' del modello. Lo scaling e' obbligatorio per SVM, KNN, reti neurali e regressione regolarizzata. La gestione dei valori mancanti e l'encoding delle variabili categoriche sono passaggi critici che influenzano direttamente le prestazioni.

6. **Iniziare con modelli semplici e aumentare la complessita' gradualmente**. Parti da un modello baseline semplice (es. `LogisticRegression`, `LinearRegression`) per stabilire un riferimento. Solo se le prestazioni non sono sufficienti, passa a modelli piu' complessi (Random Forest, Gradient Boosting, reti neurali). Modelli semplici sono piu' interpretabili, veloci da addestrare e meno soggetti a overfitting.

7. **Monitorare overfitting e underfitting**. Confronta sempre le metriche su training e validation/test. Se il training score e' molto piu' alto del test score, il modello sta facendo overfitting (memorizza i dati invece di generalizzare). Usa regolarizzazione (L1/L2, dropout), limita la complessita' del modello o raccogli piu' dati. Usa le learning curve per diagnosticare il problema.

8. **Rendere gli esperimenti riproducibili**. Imposta sempre il `random_state` nei modelli e nelle suddivisioni. Usa ambienti virtuali con versioni delle dipendenze fissate (`requirements.txt` o `pyproject.toml`). Traccia parametri e risultati con strumenti come MLflow. Senza riproducibilita', i risultati non sono verificabili ne' confrontabili.

9. **Automatizzare il workflow con Pipeline**. Le Pipeline di scikit-learn concatenano preprocessing e modello in un unico oggetto. Questo garantisce che le stesse trasformazioni vengano applicate coerentemente su training e test, semplifica la serializzazione del modello completo e riduce drasticamente il rischio di errori e data leakage.

10. **Pianificare il deployment fin dall'inizio**. Un modello che funziona solo nel notebook ha valore limitato. Pensa fin da subito a come sara' servito in produzione: serializzazione con `joblib`, API con FastAPI, containerizzazione con Docker. Implementa monitoraggio delle prestazioni in produzione perche' i dati cambiano nel tempo (data drift) e il modello puo' degradarsi, richiedendo re-training periodico.

---

## Data Preprocessing Avanzato

La preparazione dei dati rappresenta tipicamente il 60-80% del tempo di un progetto ML. Le sezioni precedenti hanno introdotto scaling, encoding e imputation di base. Qui approfondiamo tecniche avanzate che fanno la differenza su dataset reali.

### Gestione di Dataset Sbilanciati

Dataset con classi fortemente sbilanciate (es. 95% classe A, 5% classe B) sono la norma in applicazioni come frode, anomaly detection e diagnostica medica. Un classificatore che predice sempre la classe maggioritaria ottiene un'accuracy del 95% ma e' completamente inutile.

#### Strategie a Livello di Dati

```python
# pip install imbalanced-learn
from imblearn.over_sampling import SMOTE, ADASYN, BorderlineSMOTE
from imblearn.under_sampling import RandomUnderSampler, TomekLinks
from imblearn.combine import SMOTETomek
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.datasets import make_classification
import numpy as np

# Creazione dataset sbilanciato (5% classe positiva)
X, y = make_classification(
    n_samples=5000, n_features=20, n_informative=10,
    weights=[0.95, 0.05], random_state=42
)
print(f"Distribuzione classi: {np.bincount(y)}")  # ~4750 vs ~250

# --- SMOTE: Synthetic Minority Over-sampling Technique ---
# Crea campioni sintetici della classe minoritaria interpolando
# tra campioni esistenti e i loro k vicini piu' prossimi.
smote = SMOTE(sampling_strategy='auto', k_neighbors=5, random_state=42)
X_smote, y_smote = smote.fit_resample(X, y)
print(f"Dopo SMOTE: {np.bincount(y_smote)}")

# --- ADASYN: Adaptive Synthetic Sampling ---
# Simile a SMOTE ma genera piu' campioni sintetici nelle regioni
# dove la classe minoritaria e' piu' difficile da classificare.
adasyn = ADASYN(sampling_strategy='auto', random_state=42)
X_adasyn, y_adasyn = adasyn.fit_resample(X, y)

# --- BorderlineSMOTE ---
# Applica SMOTE solo ai campioni vicini al confine di decisione,
# dove la distinzione tra le classi e' piu' critica.
bsmote = BorderlineSMOTE(sampling_strategy='auto', random_state=42)
X_bsmote, y_bsmote = bsmote.fit_resample(X, y)

# --- Undersampling: riduzione della classe maggioritaria ---
under = RandomUnderSampler(sampling_strategy='auto', random_state=42)
X_under, y_under = under.fit_resample(X, y)

# --- TomekLinks: rimozione coppie ambigue ---
# Rimuove coppie di campioni di classi diverse che sono i vicini
# piu' prossimi l'uno dell'altro, pulendo il confine di decisione.
tomek = TomekLinks()
X_tomek, y_tomek = tomek.fit_resample(X, y)

# --- Combinazione SMOTE + TomekLinks ---
smote_tomek = SMOTETomek(random_state=42)
X_st, y_st = smote_tomek.fit_resample(X, y)

# --- Pipeline con imbalanced-learn ---
# IMPORTANTE: usare imblearn.pipeline.Pipeline, NON sklearn.pipeline.Pipeline
# perche' quest'ultima non supporta i resampler.
pipeline_imb = ImbPipeline([
    ('smote', SMOTE(random_state=42)),
    ('clf', RandomForestClassifier(n_estimators=200, random_state=42))
])

# Cross-validation con scoring appropriato per classi sbilanciate
scores = cross_val_score(pipeline_imb, X, y, cv=5, scoring='f1')
print(f"F1 con SMOTE pipeline: {scores.mean():.4f} (+/- {scores.std():.4f})")
```

#### Strategie a Livello di Algoritmo

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import numpy as np

# --- class_weight='balanced' ---
# Assegna pesi inversamente proporzionali alla frequenza delle classi.
# Le classi rare ricevono un peso maggiore nella funzione di costo.
rf_balanced = RandomForestClassifier(
    n_estimators=200,
    class_weight='balanced',     # pesi automatici basati sulla frequenza
    random_state=42
)

# --- class_weight personalizzato ---
# Per un controllo piu' fine, specifica i pesi manualmente.
rf_custom = RandomForestClassifier(
    n_estimators=200,
    class_weight={0: 1, 1: 10},  # la classe 1 pesa 10 volte piu' della classe 0
    random_state=42
)

# --- Logistic Regression con class_weight ---
lr_balanced = LogisticRegression(
    class_weight='balanced',
    max_iter=1000,
    random_state=42
)

# --- Threshold tuning ---
# Invece di usare la soglia di default 0.5 per la classificazione,
# si puo' ottimizzare la soglia in base alle esigenze del problema.
from sklearn.metrics import precision_recall_curve

modello = RandomForestClassifier(n_estimators=200, random_state=42)
modello.fit(X_train, y_train)
y_proba = modello.predict_proba(X_test)[:, 1]

precision_vals, recall_vals, soglie = precision_recall_curve(y_test, y_proba)

# Trova la soglia che massimizza F1
f1_scores = 2 * (precision_vals * recall_vals) / (precision_vals + recall_vals + 1e-8)
soglia_ottimale = soglie[np.argmax(f1_scores[:-1])]
print(f"Soglia ottimale: {soglia_ottimale:.4f}")

# Applica la soglia personalizzata
y_pred_ottimizzato = (y_proba >= soglia_ottimale).astype(int)
```

### Feature Engineering Avanzato

#### Encoding Categorico Avanzato

```python
# pip install category_encoders
import category_encoders as ce
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'citta': ['Milano', 'Roma', 'Milano', 'Napoli', 'Roma', 'Torino'] * 100,
    'tipo': ['A', 'B', 'C', 'A', 'B', 'C'] * 100,
    'target': np.random.randint(0, 2, 600)
})

# --- Target Encoding ---
# Sostituisce ogni categoria con la media del target per quella categoria.
# Molto efficace ma rischio di data leakage: usare SOLO dentro cross-validation.
target_enc = ce.TargetEncoder(cols=['citta'], smoothing=1.0)
df['citta_target'] = target_enc.fit_transform(df['citta'], df['target'])

# --- Binary Encoding ---
# Converte ogni categoria in un codice binario. Piu' compatto del one-hot
# per feature con molte categorie (cardinalita' alta).
binary_enc = ce.BinaryEncoder(cols=['citta'])
df_binary = binary_enc.fit_transform(df[['citta']])

# --- Weight of Evidence (WoE) Encoding ---
# Misura la forza predittiva di ogni categoria rispetto al target.
# Molto usato in credit scoring e risk modeling.
woe_enc = ce.WOEEncoder(cols=['citta'])
df['citta_woe'] = woe_enc.fit_transform(df['citta'], df['target'])

# --- Leave-One-Out Encoding ---
# Come target encoding ma esclude il campione corrente dal calcolo
# della media, riducendo il rischio di data leakage.
loo_enc = ce.LeaveOneOutEncoder(cols=['citta'])
df['citta_loo'] = loo_enc.fit_transform(df['citta'], df['target'])
```

#### Interazioni tra Feature e Feature Polinomiali

```python
from sklearn.preprocessing import PolynomialFeatures
import numpy as np

X = np.array([[2, 3], [4, 5], [6, 7]])

# Genera tutte le combinazioni polinomiali fino al grado 2
# Con interaction_only=False: include x1^2, x2^2, x1*x2
poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=False)
X_poly = poly.fit_transform(X)
print(f"Feature names: {poly.get_feature_names_out()}")
# ['x0', 'x1', 'x0^2', 'x0 x1', 'x1^2']

# Solo interazioni (senza termini al quadrato)
poly_inter = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
X_inter = poly_inter.fit_transform(X)
print(f"Solo interazioni: {poly_inter.get_feature_names_out()}")
# ['x0', 'x1', 'x0 x1']
```

---

## Metriche di Valutazione — Approfondimento

Le sezioni precedenti hanno introdotto le metriche fondamentali. Qui approfondiamo tecniche di valutazione avanzate essenziali per prendere decisioni informate sulla qualita' dei modelli.

### Matrice di Confusione — Analisi Dettagliata

La matrice di confusione e' la base di tutte le metriche di classificazione. Comprenderne ogni cella e' fondamentale.

```python
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import numpy as np

# Esempio multiclasse
y_true = [0, 0, 0, 1, 1, 1, 2, 2, 2, 0, 1, 2]
y_pred = [0, 0, 1, 1, 1, 2, 2, 2, 0, 0, 0, 2]

cm = confusion_matrix(y_true, y_pred)
print("Matrice di Confusione (multiclasse):")
print(cm)
# Ogni riga = classe reale, ogni colonna = classe predetta
# Diagonale = predizioni corrette

# Metriche derivate per ogni classe
for classe in range(3):
    tp = cm[classe, classe]
    fp = cm[:, classe].sum() - tp   # colonna meno diagonale
    fn = cm[classe, :].sum() - tp   # riga meno diagonale
    tn = cm.sum() - tp - fp - fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f"Classe {classe}: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")

# Visualizzazione
fig, ax = plt.subplots(figsize=(8, 6))
disp = ConfusionMatrixDisplay(cm, display_labels=['Classe 0', 'Classe 1', 'Classe 2'])
disp.plot(ax=ax, cmap='Blues', values_format='d')
plt.title('Matrice di Confusione Multiclasse')
plt.tight_layout()
plt.savefig("cm_multiclass.png", dpi=150)
plt.close()
```

### Curva Precision-Recall

La curva precision-recall e' piu' informativa della ROC curve quando le classi sono sbilanciate, perche' non e' influenzata dal gran numero di veri negativi.

```python
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.metrics import PrecisionRecallDisplay
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

modello = RandomForestClassifier(n_estimators=200, random_state=42)
modello.fit(X_train, y_train)
y_proba = modello.predict_proba(X_test)[:, 1]

# Curva Precision-Recall
precision_vals, recall_vals, soglie = precision_recall_curve(y_test, y_proba)
ap = average_precision_score(y_test, y_proba)

fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(recall_vals, precision_vals, linewidth=2, label=f'AP = {ap:.4f}')
ax.set_xlabel('Recall')
ax.set_ylabel('Precision')
ax.set_title('Curva Precision-Recall')
ax.legend()
ax.grid(True, alpha=0.3)

# Linea baseline (classificatore casuale)
baseline = y_test.sum() / len(y_test)
ax.axhline(y=baseline, color='red', linestyle='--', label=f'Baseline = {baseline:.3f}')
ax.legend()

plt.tight_layout()
plt.savefig("precision_recall_curve.png", dpi=150)
plt.close()

# Average Precision Score (area sotto la curva PR)
# Piu' informativo di ROC-AUC per classi sbilanciate
print(f"Average Precision: {ap:.4f}")
```

### Curva ROC — Confronto Multi-Modello

```python
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

modelli = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42),
    'SVM': SVC(probability=True, random_state=42)
}

fig, ax = plt.subplots(figsize=(8, 6))

for nome, modello in modelli.items():
    modello.fit(X_train, y_train)
    y_proba = modello.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc = roc_auc_score(y_test, y_proba)
    ax.plot(fpr, tpr, linewidth=2, label=f'{nome} (AUC={auc:.4f})')

ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random (AUC=0.5)')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('Confronto Curve ROC')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("roc_comparison.png", dpi=150)
plt.close()
```

### Strategie di Cross-Validation Avanzate

```python
from sklearn.model_selection import (
    StratifiedKFold, RepeatedStratifiedKFold,
    GroupKFold, TimeSeriesSplit, cross_val_score
)
from sklearn.ensemble import RandomForestClassifier
import numpy as np

modello = RandomForestClassifier(n_estimators=100, random_state=42)

# --- RepeatedStratifiedKFold ---
# Ripete la StratifiedKFold N volte con shuffle diversi.
# Produce una stima piu' stabile delle prestazioni.
rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
scores = cross_val_score(modello, X, y, cv=rskf, scoring='f1')
print(f"RepeatedStratifiedKFold (5x3): {scores.mean():.4f} (+/- {scores.std():.4f})")

# --- GroupKFold ---
# Garantisce che campioni dello stesso gruppo non compaiano
# sia nel training che nel validation set. Essenziale quando
# i campioni non sono indipendenti (es. piu' misure per paziente).
gruppi = np.array([1, 1, 2, 2, 3, 3, 4, 4, 5, 5] * (len(X) // 10))
gkf = GroupKFold(n_splits=5)
# scores = cross_val_score(modello, X, y, cv=gkf, groups=gruppi, scoring='f1')

# --- TimeSeriesSplit ---
# Per dati temporali: il training set e' sempre precedente al validation set.
# Rispetta l'ordine cronologico evitando look-ahead bias.
tscv = TimeSeriesSplit(n_splits=5)
for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
    print(f"Fold {fold}: Train={len(train_idx)} campioni, "
          f"Val={len(val_idx)} campioni, "
          f"Train range=[{train_idx[0]}-{train_idx[-1]}], "
          f"Val range=[{val_idx[0]}-{val_idx[-1]}]")
```

---

## Metodi Ensemble Avanzati

I metodi ensemble combinano piu' modelli per ottenere prestazioni superiori a quelle di qualsiasi singolo modello. Le sezioni precedenti hanno introdotto Random Forest e Gradient Boosting di base. Qui approfondiamo CatBoost, stacking e voting.

### CatBoost

**CatBoost** (Categorical Boosting) e' sviluppato da Yandex e si distingue per la gestione nativa delle feature categoriche senza bisogno di preprocessing, la resistenza all'overfitting grazie agli alberi simmetrici (oblivious trees), e la necessita' minima di tuning degli iperparametri.

```python
# pip install catboost
from catboost import CatBoostClassifier, CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import numpy as np

# Esempio con feature categoriche native
np.random.seed(42)
df = pd.DataFrame({
    'eta': np.random.randint(18, 70, 1000),
    'reddito': np.random.normal(40000, 15000, 1000),
    'citta': np.random.choice(['Milano', 'Roma', 'Napoli', 'Torino', 'Bologna'], 1000),
    'professione': np.random.choice(['ingegnere', 'medico', 'insegnante', 'avvocato'], 1000),
    'istruzione': np.random.choice(['laurea', 'diploma', 'master'], 1000),
    'target': np.random.randint(0, 2, 1000)
})

# Indici delle colonne categoriche
cat_features = ['citta', 'professione', 'istruzione']
cat_indices = [df.columns.get_loc(c) for c in cat_features]

X = df.drop('target', axis=1)
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# CatBoost gestisce le categoriche NATIVAMENTE
# Non serve OneHotEncoder, LabelEncoder o TargetEncoder.
cat_model = CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.1,
    loss_function='Logloss',
    cat_features=cat_indices,      # indica quali colonne sono categoriche
    random_seed=42,
    verbose=100                    # stampa ogni 100 iterazioni
)

cat_model.fit(X_train, y_train, eval_set=(X_test, y_test), early_stopping_rounds=50)

y_pred = cat_model.predict(X_test)
print(classification_report(y_test, y_pred))

# Feature importance
importanze = cat_model.get_feature_importance()
for nome, imp in sorted(zip(X.columns, importanze), key=lambda x: -x[1]):
    print(f"  {nome}: {imp:.2f}")
```

### Confronto XGBoost vs LightGBM vs CatBoost

| Caratteristica | XGBoost | LightGBM | CatBoost |
|---|---|---|---|
| **Crescita albero** | Level-wise (larghezza) | Leaf-wise (profondita') | Symmetric (oblivious) |
| **Velocita'** | Media | Molto veloce | Veloce |
| **Feature categoriche** | Richiede encoding | Supporto nativo basico | Supporto nativo avanzato |
| **Overfitting** | Regolarizzazione L1/L2 | Regolarizzazione + max_depth | Alberi simmetrici |
| **Tuning richiesto** | Alto | Medio | Basso |
| **Dati grandi** | Buono | Eccellente | Buono |
| **GPU** | Supportata | Supportata | Supportata |

### Stacking (Stacked Generalization)

Lo stacking combina le previsioni di piu' modelli base usando un **meta-learner** che impara a pesare le previsioni dei modelli sottostanti.

```python
from sklearn.ensemble import StackingClassifier, StackingRegressor
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score

# Modelli base (livello 0): diversi tipi di learner
estimators = [
    ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
    ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42)),
    ('svm', SVC(probability=True, random_state=42)),
    ('knn', KNeighborsClassifier(n_neighbors=5))
]

# Meta-learner (livello 1): apprende come combinare i modelli base
stacking = StackingClassifier(
    estimators=estimators,
    final_estimator=LogisticRegression(max_iter=1000),
    cv=5,                    # cross-validation interna per i modelli base
    stack_method='predict_proba',  # usa probabilita' come feature per il meta-learner
    n_jobs=-1
)

scores = cross_val_score(stacking, X, y, cv=5, scoring='accuracy')
print(f"Stacking Accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")
```

### Voting Classifier

Il voting e' piu' semplice dello stacking: i modelli base "votano" e la predizione finale e' la classe con piu' voti (hard voting) o la media delle probabilita' (soft voting).

```python
from sklearn.ensemble import VotingClassifier

voting = VotingClassifier(
    estimators=[
        ('rf', RandomForestClassifier(n_estimators=200, random_state=42)),
        ('gb', GradientBoostingClassifier(n_estimators=200, random_state=42)),
        ('lr', LogisticRegression(max_iter=1000, random_state=42))
    ],
    voting='soft',     # 'hard' = voto maggioritario, 'soft' = media probabilita'
    weights=[2, 2, 1]  # peso relativo di ciascun modello
)

scores = cross_val_score(voting, X, y, cv=5, scoring='accuracy')
print(f"Voting Accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")
```

---

## Riduzione della Dimensionalita'

La riduzione della dimensionalita' trasforma dati con molte feature in una rappresentazione a dimensione inferiore, mantenendo il piu' possibile le informazioni rilevanti. E' utile per la visualizzazione, la rimozione del rumore e il miglioramento delle prestazioni dei modelli.

### PCA — Principal Component Analysis

PCA e' una trasformazione **lineare** che proietta i dati sulle direzioni di massima varianza (componenti principali). E' deterministica, veloce e interpretabile.

```python
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_digits
import matplotlib.pyplot as plt
import numpy as np

# Dataset MNIST ridotto (immagini 8x8 = 64 feature)
digits = load_digits()
X, y = digits.data, digits.target

# PCA richiede dati scalati
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- PCA per visualizzazione (2 componenti) ---
pca_2d = PCA(n_components=2, random_state=42)
X_2d = pca_2d.fit_transform(X_scaled)

plt.figure(figsize=(10, 8))
scatter = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=y, cmap='tab10', alpha=0.6, s=10)
plt.colorbar(scatter, label='Digit')
plt.xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]:.1%} varianza)')
plt.ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]:.1%} varianza)')
plt.title('PCA — Digits Dataset')
plt.tight_layout()
plt.savefig("pca_digits.png", dpi=150)
plt.close()

# --- Varianza spiegata cumulativa ---
# Per decidere quante componenti mantenere
pca_full = PCA(random_state=42)
pca_full.fit(X_scaled)

varianza_cumulativa = np.cumsum(pca_full.explained_variance_ratio_)
n_componenti_95 = np.argmax(varianza_cumulativa >= 0.95) + 1
print(f"Componenti per 95% varianza: {n_componenti_95} (da {X.shape[1]} originali)")

# --- PCA per riduzione noise e miglioramento modello ---
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

pca_ridotto = PCA(n_components=n_componenti_95, random_state=42)
X_ridotto = pca_ridotto.fit_transform(X_scaled)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
score_originale = cross_val_score(rf, X_scaled, y, cv=5, scoring='accuracy').mean()
score_ridotto = cross_val_score(rf, X_ridotto, y, cv=5, scoring='accuracy').mean()
print(f"Accuracy originale ({X.shape[1]} feat): {score_originale:.4f}")
print(f"Accuracy ridotto ({n_componenti_95} feat): {score_ridotto:.4f}")
```

### t-SNE — t-Distributed Stochastic Neighbor Embedding

t-SNE e' una tecnica **non lineare** ottimizzata per la visualizzazione in 2D/3D. Preserva le strutture locali (cluster) ma non le distanze globali. Non e' adatta come preprocessing per modelli ML (e' non-deterministica e non puo' trasformare nuovi dati).

```python
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

# t-SNE e' computazionalmente costoso: usare PCA prima
# per ridurre a ~50 componenti accelera notevolmente il processo.
pca_pre = PCA(n_components=50, random_state=42)
X_pca50 = pca_pre.fit_transform(X_scaled)

# --- t-SNE con perplexity tuning ---
# perplexity: bilancia attenzione tra struttura locale e globale
# Valori tipici: 5-50. Troppo basso crea cluster artificiali,
# troppo alto perde struttura locale.
tsne = TSNE(
    n_components=2,
    perplexity=30,        # sweet spot tipico
    learning_rate='auto',
    n_iter=1000,
    random_state=42,
    init='pca'            # inizializzazione con PCA (piu' stabile)
)
X_tsne = tsne.fit_transform(X_pca50)

plt.figure(figsize=(10, 8))
scatter = plt.scatter(X_tsne[:, 0], X_tsne[:, 1], c=y, cmap='tab10', alpha=0.6, s=10)
plt.colorbar(scatter, label='Digit')
plt.title('t-SNE — Digits Dataset (perplexity=30)')
plt.tight_layout()
plt.savefig("tsne_digits.png", dpi=150)
plt.close()
```

### UMAP — Uniform Manifold Approximation and Projection

UMAP e' piu' recente di t-SNE e offre vantaggi significativi: preserva sia la struttura locale che globale, e' molto piu' veloce su grandi dataset e puo' essere usato come preprocessing per modelli ML (supporta `transform()` su nuovi dati).

```python
# pip install umap-learn
import umap
import matplotlib.pyplot as plt

# --- UMAP per visualizzazione ---
reducer = umap.UMAP(
    n_components=2,
    n_neighbors=15,       # dimensione del vicinato locale (default: 15)
    min_dist=0.1,         # compattezza dei cluster (default: 0.1)
    metric='euclidean',
    random_state=42
)
X_umap = reducer.fit_transform(X_scaled)

plt.figure(figsize=(10, 8))
scatter = plt.scatter(X_umap[:, 0], X_umap[:, 1], c=y, cmap='tab10', alpha=0.6, s=10)
plt.colorbar(scatter, label='Digit')
plt.title('UMAP — Digits Dataset')
plt.tight_layout()
plt.savefig("umap_digits.png", dpi=150)
plt.close()

# --- UMAP come preprocessing per classificazione ---
# A differenza di t-SNE, UMAP puo' trasformare nuovi dati.
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

reducer_ml = umap.UMAP(n_components=10, random_state=42)
X_train_umap = reducer_ml.fit_transform(X_train)
X_test_umap = reducer_ml.transform(X_test)  # transform su nuovi dati!

rf = RandomForestClassifier(n_estimators=200, random_state=42)
rf.fit(X_train_umap, y_train)
print(f"Accuracy con UMAP(10d): {rf.score(X_test_umap, y_test):.4f}")
```

### Quando Usare Quale Tecnica

| Tecnica | Tipo | Velocita' | Nuovi dati | Uso principale |
|---|---|---|---|---|
| **PCA** | Lineare | Molto veloce | Si' (`transform()`) | Preprocessing, noise reduction |
| **t-SNE** | Non lineare | Lento | No | Solo visualizzazione 2D/3D |
| **UMAP** | Non lineare | Veloce | Si' (`transform()`) | Visualizzazione + preprocessing |

---

## NLP con Python

Il **Natural Language Processing** (NLP) e' il campo del ML dedicato all'elaborazione e comprensione del linguaggio naturale. Python offre un ecosistema maturo con spaCy per NLP industriale e Hugging Face transformers per modelli pre-addestrati all'avanguardia.

### spaCy — NLP Industriale

**spaCy** e' una libreria progettata per NLP in produzione: veloce, efficiente e con pipeline modulari. Offre tokenizzazione, POS tagging, NER (Named Entity Recognition), dependency parsing e altro.

```python
# pip install spacy
# python -m spacy download it_core_news_lg  (modello italiano)
# python -m spacy download en_core_web_sm   (modello inglese piccolo)
import spacy

# Caricamento modello italiano
nlp = spacy.load("it_core_news_lg")

testo = "Il Politecnico di Milano ha sviluppato un sistema di AI per la diagnostica medica."
doc = nlp(testo)

# --- Tokenizzazione ---
print("Token:")
for token in doc:
    print(f"  {token.text:20s} POS={token.pos_:6s} DEP={token.dep_:10s} LEMMA={token.lemma_}")

# --- Named Entity Recognition (NER) ---
print("\nEntita' riconosciute:")
for ent in doc.ents:
    print(f"  {ent.text:30s} -> {ent.label_} ({spacy.explain(ent.label_)})")

# --- Similarity (richiede modelli con word vectors: _md o _lg) ---
doc1 = nlp("Il gatto dorme sul divano")
doc2 = nlp("Il felino riposa sul sofa")
doc3 = nlp("Il mercato azionario e' in crescita")

print(f"\nSimilarita':")
print(f"  gatto/felino: {doc1.similarity(doc2):.4f}")     # alta
print(f"  gatto/mercato: {doc1.similarity(doc3):.4f}")    # bassa

# --- Pipeline personalizzata con EntityRuler ---
from spacy.pipeline import EntityRuler

ruler = nlp.add_pipe("entity_ruler", before="ner")
patterns = [
    {"label": "TECH", "pattern": "Python"},
    {"label": "TECH", "pattern": "PyTorch"},
    {"label": "TECH", "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}]},
]
ruler.add_patterns(patterns)
```

### Preprocessing del Testo

```python
import spacy
import re

nlp = spacy.load("it_core_news_lg")

def preprocess_text(testo: str, nlp_model) -> list[str]:
    """Pipeline di preprocessing NLP standard."""
    # 1. Pulizia base
    testo = testo.lower()
    testo = re.sub(r'http\S+|www\S+', '', testo)    # rimuovi URL
    testo = re.sub(r'[^\w\s]', ' ', testo)           # rimuovi punteggiatura
    testo = re.sub(r'\s+', ' ', testo).strip()        # normalizza spazi

    # 2. Elaborazione con spaCy
    doc = nlp_model(testo)

    # 3. Lemmatizzazione + rimozione stopword e punteggiatura
    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop          # rimuovi stopword
        and not token.is_punct        # rimuovi punteggiatura
        and not token.like_num        # rimuovi numeri
        and len(token.text) > 2       # rimuovi token corti
    ]

    return tokens

testo = "L'intelligenza artificiale sta rivoluzionando il settore sanitario nel 2025."
tokens = preprocess_text(testo, nlp)
print(f"Tokens processati: {tokens}")
```

### Hugging Face Transformers

**Hugging Face transformers** fornisce accesso a migliaia di modelli pre-addestrati (BERT, GPT, T5, etc.) tramite un'API unificata. I modelli transformer hanno rivoluzionato l'NLP raggiungendo prestazioni stato dell'arte in quasi tutti i compiti.

```python
# pip install transformers torch
from transformers import pipeline

# --- Sentiment Analysis ---
# La pipeline astrae modello, tokenizer e post-processing.
sentiment = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
risultato = sentiment("Questo prodotto e' eccellente, lo consiglio a tutti!")
print(f"Sentiment: {risultato}")
# [{'label': '5 stars', 'score': 0.78}]

# --- Named Entity Recognition con Transformers ---
ner = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
testo = "Elon Musk ha fondato SpaceX a Los Angeles"
entita = ner(testo)
for e in entita:
    print(f"  {e['word']:20s} -> {e['entity_group']} (score={e['score']:.4f})")

# --- Text Classification custom ---
classificatore = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
testo = "Il server ha raggiunto il 95% di utilizzo CPU"
categorie = ["problema hardware", "problema software", "sicurezza", "performance"]

risultato = classificatore(testo, categorie)
for label, score in zip(risultato['labels'], risultato['scores']):
    print(f"  {label:25s}: {score:.4f}")

# --- Summarization ---
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
testo_lungo = """
Machine learning is a subset of artificial intelligence that focuses on building
systems that learn from data. Instead of being explicitly programmed to perform
a task, these systems use algorithms to parse data, learn from it, and make
decisions. The field has grown significantly in recent years, driven by advances
in computing power, data availability, and algorithmic improvements.
"""
riassunto = summarizer(testo_lungo, max_length=50, min_length=20)
print(f"Riassunto: {riassunto[0]['summary_text']}")
```

### Sentence Embeddings e Semantic Search

I **sentence embeddings** rappresentano intere frasi come vettori densi nello spazio semantico. Frasi con significato simile hanno vettori vicini, abilitando ricerca semantica, clustering di documenti e rilevamento di duplicati.

```python
# pip install sentence-transformers
from sentence_transformers import SentenceTransformer
import numpy as np

# Modello multilingue per sentence embeddings
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

frasi = [
    "Il server e' sovraccarico e non risponde",
    "La macchina ha troppo carico e va in timeout",
    "Il prezzo delle azioni e' salito del 5%",
    "Il sistema e' lento e ha problemi di performance",
]

# Calcolo embeddings
embeddings = model.encode(frasi)
print(f"Shape embeddings: {embeddings.shape}")  # (4, 384)

# Calcolo similarita' coseno tra tutte le coppie
from sklearn.metrics.pairwise import cosine_similarity

sim_matrix = cosine_similarity(embeddings)
print("Matrice di similarita':")
for i, frase in enumerate(frasi):
    for j in range(i + 1, len(frasi)):
        print(f"  '{frasi[i][:40]}...' <-> '{frasi[j][:40]}...': {sim_matrix[i][j]:.4f}")

# Ricerca semantica: trova la frase piu' simile alla query
query = "problemi di prestazioni del server"
query_emb = model.encode([query])
scores = cosine_similarity(query_emb, embeddings)[0]
best_idx = np.argmax(scores)
print(f"\nQuery: '{query}'")
print(f"Miglior match: '{frasi[best_idx]}' (score={scores[best_idx]:.4f})")
```

### Fine-Tuning di un Modello Transformer

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import TrainingArguments, Trainer
from datasets import Dataset
import numpy as np

# Preparazione dataset
train_data = Dataset.from_dict({
    'text': ["ottimo servizio", "pessima esperienza", "buon prodotto",
             "non funziona", "consiglio vivamente", "delusione totale"] * 50,
    'label': [1, 0, 1, 0, 1, 0] * 50
})

# Caricamento tokenizer e modello pre-addestrato
model_name = "bert-base-multilingual-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Tokenizzazione
def tokenize(batch):
    return tokenizer(batch['text'], padding='max_length', truncation=True, max_length=128)

train_data = train_data.map(tokenize, batched=True)

# Configurazione training
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=8,
    learning_rate=2e-5,
    weight_decay=0.01,
    logging_steps=10,
    save_strategy='epoch',
    seed=42,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
)

# Fine-tuning
# trainer.train()
```

---

## Deep Learning — Fondamenti Teorici

Le sezioni precedenti hanno mostrato come costruire reti neurali con TensorFlow/Keras e PyTorch. Qui approfondiamo i concetti teorici fondamentali che guidano la progettazione e il training delle reti neurali.

### Architettura di una Rete Neurale

Una rete neurale e' composta da strati (layer) di neuroni artificiali. Ogni neurone riceve input, applica una trasformazione lineare seguita da una funzione di attivazione non lineare, e produce un output.

```
Input Layer     Hidden Layer(s)     Output Layer
    x1 ──┐
          ├── [w*x + b] → f() ──┐
    x2 ──┤                       ├── [w*h + b] → f() → y
          ├── [w*x + b] → f() ──┤
    x3 ──┘                       │
                                  └── [w*h + b] → f() → y2
```

- **Input layer**: riceve i dati grezzi (feature)
- **Hidden layers**: trasformano i dati attraverso pesi appresi
- **Output layer**: produce la previsione finale
- **f()**: funzione di attivazione non lineare

### Funzioni di Attivazione

Le funzioni di attivazione introducono non-linearita' nella rete, permettendole di apprendere relazioni complesse.

```python
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt

x = torch.linspace(-5, 5, 200)

# --- ReLU (Rectified Linear Unit) ---
# f(x) = max(0, x)
# Pro: semplice, veloce, niente vanishing gradient per x > 0
# Contro: "dying ReLU" (neuroni che si azzerano permanentemente)
relu = F.relu(x)

# --- LeakyReLU ---
# f(x) = x se x > 0, alpha*x se x <= 0
# Risolve il problema del dying ReLU con una piccola pendenza negativa.
leaky = F.leaky_relu(x, negative_slope=0.01)

# --- GELU (Gaussian Error Linear Unit) ---
# Usata nei transformer (BERT, GPT). Piu' smooth di ReLU.
gelu = F.gelu(x)

# --- Sigmoid ---
# f(x) = 1 / (1 + e^(-x))
# Usata nell'output layer per classificazione binaria.
# Soffre di vanishing gradient per valori molto positivi/negativi.
sigmoid = torch.sigmoid(x)

# --- Tanh ---
# f(x) = (e^x - e^(-x)) / (e^x + e^(-x))
# Output in [-1, 1]. Preferita a sigmoid negli hidden layer
# perche' centrata sullo zero.
tanh = torch.tanh(x)

# --- Softmax ---
# Usata nell'output layer per classificazione multiclasse.
# Converte logits in distribuzione di probabilita' (somma = 1).
logits = torch.tensor([2.0, 1.0, 0.1])
probs = F.softmax(logits, dim=0)
print(f"Softmax: {probs}")  # [0.659, 0.243, 0.099]
```

### Backpropagation e Ottimizzatori

La **backpropagation** calcola il gradiente della funzione di costo rispetto a ogni peso della rete, propagando l'errore dall'output verso l'input. Gli **ottimizzatori** usano questi gradienti per aggiornare i pesi.

```python
import torch
import torch.nn as nn
import torch.optim as optim

# Modello di esempio
model = nn.Sequential(
    nn.Linear(10, 64),
    nn.ReLU(),
    nn.Linear(64, 1)
)

# --- SGD (Stochastic Gradient Descent) ---
# L'ottimizzatore base. Aggiorna i pesi nella direzione opposta al gradiente.
# Con momentum accelera la convergenza accumulando velocita'.
sgd = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, weight_decay=1e-4)

# --- Adam (Adaptive Moment Estimation) ---
# Combina momentum e learning rate adattivo per ogni parametro.
# Il piu' usato in pratica. Ottimo default per iniziare.
adam = optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), weight_decay=1e-4)

# --- AdamW ---
# Variante di Adam con weight decay corretto (decoupled).
# Raccomandato per fine-tuning di transformer.
adamw = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)

# --- Learning Rate Scheduler ---
# Riduce il learning rate durante il training per convergenza piu' fine.
scheduler = optim.lr_scheduler.CosineAnnealingLR(adam, T_max=100)

# Esempio di training step
x = torch.randn(32, 10)
y = torch.randn(32, 1)
criterion = nn.MSELoss()

output = model(x)
loss = criterion(output, y)

adam.zero_grad()      # azzera i gradienti accumulati
loss.backward()       # calcola i gradienti (backpropagation)
adam.step()           # aggiorna i pesi usando i gradienti
scheduler.step()      # aggiorna il learning rate
```

### Architetture Fondamentali

#### Reti Convoluzionali (CNN)

Le CNN sono progettate per dati con struttura spaziale (immagini, segnali). I layer convoluzionali applicano filtri che rilevano pattern locali (bordi, texture, forme) in modo gerarchico.

```python
import torch
import torch.nn as nn

class SimpleCNN(nn.Module):
    """CNN per classificazione di immagini 28x28 (es. MNIST)."""
    def __init__(self, n_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            # Conv1: 1 canale input -> 32 filtri, kernel 3x3
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),          # 28x28 -> 14x14

            # Conv2: 32 -> 64 filtri
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),          # 14x14 -> 7x7
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),             # 64 * 7 * 7 = 3136
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, n_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

# Esempio di input: batch di 16 immagini 28x28 a 1 canale
x = torch.randn(16, 1, 28, 28)
model = SimpleCNN()
output = model(x)
print(f"Output shape: {output.shape}")  # [16, 10]
```

#### Reti Ricorrenti (RNN / LSTM)

Le RNN elaborano sequenze di dati (testo, serie temporali) mantenendo una memoria degli step precedenti. Le **LSTM** (Long Short-Term Memory) risolvono il problema del vanishing gradient delle RNN base, permettendo di catturare dipendenze a lungo termine.

```python
import torch
import torch.nn as nn

class LSTMClassifier(nn.Module):
    """LSTM per classificazione di sequenze (es. sentiment analysis)."""
    def __init__(self, vocab_size, embed_dim, hidden_dim, n_classes, n_layers=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(
            embed_dim, hidden_dim,
            num_layers=n_layers,
            batch_first=True,
            dropout=0.3,
            bidirectional=True       # bidirezionale per contesto completo
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),   # *2 per bidirezionale
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, n_classes)
        )

    def forward(self, x):
        embedded = self.embedding(x)          # [batch, seq_len, embed_dim]
        lstm_out, (hidden, cell) = self.lstm(embedded)

        # Concatena gli hidden state finali forward e backward
        hidden_cat = torch.cat((hidden[-2], hidden[-1]), dim=1)
        output = self.classifier(hidden_cat)
        return output

model = LSTMClassifier(vocab_size=10000, embed_dim=128, hidden_dim=256, n_classes=2)
x = torch.randint(0, 10000, (8, 50))  # batch di 8, sequenza di 50 token
output = model(x)
print(f"Output shape: {output.shape}")  # [8, 2]
```

### Tecniche di Regolarizzazione

La regolarizzazione previene l'overfitting, cioe' la tendenza del modello a memorizzare il training set invece di generalizzare.

```python
import torch.nn as nn

class RegularizedNet(nn.Module):
    def __init__(self, input_dim, n_classes):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),     # Batch Normalization: normalizza le attivazioni
            nn.ReLU(),
            nn.Dropout(0.3),         # Dropout: disattiva il 30% dei neuroni a caso

            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(128, n_classes)
        )

    def forward(self, x):
        return self.network(x)

# --- Early Stopping manuale ---
best_val_loss = float('inf')
patience = 10
counter = 0

for epoch in range(200):
    # ... training loop ...
    val_loss = 0.5  # placeholder

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        counter = 0
        # torch.save(model.state_dict(), 'best_model.pt')
    else:
        counter += 1
        if counter >= patience:
            print(f"Early stopping at epoch {epoch}")
            break
```

---

## MLOps — Model Registry e Lifecycle

Le sezioni precedenti hanno introdotto MLflow per il tracking degli esperimenti. Qui approfondiamo il **Model Registry**, la gestione del ciclo di vita dei modelli e le pratiche per portare modelli in produzione in modo affidabile.

### MLflow Model Registry

Il Model Registry e' un repository centralizzato per gestire le versioni dei modelli, con transizioni tra stati (Staging, Production, Archived).

```python
import mlflow
from mlflow import MlflowClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Configurazione
mlflow.set_tracking_uri("sqlite:///mlflow.db")  # o URI del server remoto
mlflow.set_experiment("classificazione-produzione")
client = MlflowClient()

# --- Registrazione del modello durante un run ---
with mlflow.start_run(run_name="rf_production_candidate"):
    params = {"n_estimators": 300, "max_depth": 12}
    mlflow.log_params(params)

    modello = RandomForestClassifier(**params, random_state=42)
    modello.fit(X_train, y_train)

    accuracy = accuracy_score(y_test, modello.predict(X_test))
    mlflow.log_metric("accuracy", accuracy)

    # Registra il modello nel Model Registry
    mlflow.sklearn.log_model(
        modello,
        artifact_path="modello",
        registered_model_name="classificatore-tumore"  # nome nel registry
    )

# --- Gestione delle versioni del modello ---
# Ogni registrazione crea una nuova versione automaticamente.
# Le versioni possono essere promosse attraverso gli stadi:
# None -> Staging -> Production -> Archived

# Promuovi versione 1 a Staging
client.transition_model_version_stage(
    name="classificatore-tumore",
    version=1,
    stage="Staging"
)

# Dopo i test, promuovi a Production
client.transition_model_version_stage(
    name="classificatore-tumore",
    version=1,
    stage="Production"
)

# --- Caricamento del modello in produzione ---
model_uri = "models:/classificatore-tumore/Production"
modello_prod = mlflow.sklearn.load_model(model_uri)
predizioni = modello_prod.predict(X_test)
print(f"Accuracy modello in produzione: {accuracy_score(y_test, predizioni):.4f}")
```

### MLflow con Optuna — Tracking degli Iperparametri

```python
import mlflow
import optuna
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score

mlflow.set_experiment("ottimizzazione-iperparametri")

def objective(trial):
    """Funzione obiettivo per Optuna con logging MLflow."""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
    }

    with mlflow.start_run(nested=True, run_name=f"trial_{trial.number}"):
        mlflow.log_params(params)

        modello = GradientBoostingClassifier(**params, random_state=42)
        scores = cross_val_score(modello, X_train, y_train, cv=5, scoring='f1')
        f1_medio = scores.mean()

        mlflow.log_metric("f1_cv_mean", f1_medio)
        mlflow.log_metric("f1_cv_std", scores.std())

        return f1_medio

with mlflow.start_run(run_name="optuna_study"):
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=50)

    # Log dei risultati migliori
    mlflow.log_params(study.best_params)
    mlflow.log_metric("best_f1", study.best_value)

print(f"Migliori parametri: {study.best_params}")
print(f"Miglior F1: {study.best_value:.4f}")
```

### Monitoraggio del Data Drift

Il **data drift** si verifica quando la distribuzione dei dati in produzione cambia rispetto ai dati di training, causando un degrado delle prestazioni del modello nel tempo.

```python
import numpy as np
from scipy import stats

def detect_drift(reference_data: np.ndarray, production_data: np.ndarray,
                 feature_names: list[str], threshold: float = 0.05) -> dict:
    """
    Rileva data drift confrontando le distribuzioni di riferimento e produzione.
    Usa il test di Kolmogorov-Smirnov per feature numeriche.
    """
    drift_report = {}

    for i, nome in enumerate(feature_names):
        ref = reference_data[:, i]
        prod = production_data[:, i]

        # Test KS: verifica se due campioni provengono dalla stessa distribuzione
        statistic, p_value = stats.ks_2samp(ref, prod)

        drift_detected = p_value < threshold
        drift_report[nome] = {
            'ks_statistic': statistic,
            'p_value': p_value,
            'drift': drift_detected,
            'ref_mean': ref.mean(),
            'prod_mean': prod.mean(),
            'ref_std': ref.std(),
            'prod_std': prod.std(),
        }

        if drift_detected:
            print(f"DRIFT RILEVATO in '{nome}': "
                  f"KS={statistic:.4f}, p={p_value:.6f}, "
                  f"ref_mean={ref.mean():.4f} -> prod_mean={prod.mean():.4f}")

    n_drift = sum(1 for v in drift_report.values() if v['drift'])
    print(f"\nFeature con drift: {n_drift}/{len(feature_names)}")
    return drift_report
```

---

## Hyperparameter Tuning con Optuna

**Optuna** e' un framework per l'ottimizzazione automatica degli iperparametri che utilizza algoritmi di ricerca bayesiana (TPE — Tree-structured Parzen Estimator) per esplorare lo spazio dei parametri in modo piu' efficiente di GridSearchCV e RandomizedSearchCV. Supporta inoltre il **pruning** per interrompere precocemente trial poco promettenti.

### Studio e Trial

```python
# pip install optuna
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

def objective(trial):
    """
    Funzione obiettivo: Optuna chiama questa funzione per ogni trial.
    trial.suggest_* definisce lo spazio di ricerca.
    """
    # Spazio di ricerca degli iperparametri
    n_estimators = trial.suggest_int('n_estimators', 50, 500)
    max_depth = trial.suggest_int('max_depth', 3, 20)
    min_samples_split = trial.suggest_int('min_samples_split', 2, 20)
    min_samples_leaf = trial.suggest_int('min_samples_leaf', 1, 10)
    max_features = trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
    criterion = trial.suggest_categorical('criterion', ['gini', 'entropy'])

    modello = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        criterion=criterion,
        random_state=42,
        n_jobs=-1
    )

    scores = cross_val_score(modello, X_train, y_train, cv=5, scoring='f1')
    return scores.mean()

# Creazione studio e ottimizzazione
study = optuna.create_study(
    direction='maximize',                    # massimizzare F1
    study_name='random_forest_optimization',
    sampler=optuna.samplers.TPESampler(seed=42)  # algoritmo bayesiano
)

# Avvio ottimizzazione (50 trial)
study.optimize(objective, n_trials=50, show_progress_bar=True)

# Risultati
print(f"Miglior trial: #{study.best_trial.number}")
print(f"Miglior F1: {study.best_value:.4f}")
print(f"Migliori parametri:")
for chiave, valore in study.best_params.items():
    print(f"  {chiave}: {valore}")
```

### Pruning dei Trial Poco Promettenti

Il pruning permette di interrompere precocemente trial che non stanno convergendo verso risultati competitivi, risparmiando tempo computazionale.

```python
import optuna
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
import numpy as np

def objective_con_pruning(trial):
    params = {
        'n_estimators': 500,  # fisso, usiamo early stopping
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
    }

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = []

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
        X_tr, X_val = X_train[train_idx], X_train[val_idx]
        y_tr, y_val = y_train[train_idx], y_train[val_idx]

        modello = XGBClassifier(**params, random_state=42, use_label_encoder=False,
                                eval_metric='logloss')
        modello.fit(X_tr, y_tr, eval_set=[(X_val, y_val)],
                    verbose=False)

        score = modello.score(X_val, y_val)
        scores.append(score)

        # Report dello score intermedio per il pruning
        trial.report(np.mean(scores), fold)

        # Se il trial non e' promettente, Optuna lo interrompe
        if trial.should_prune():
            raise optuna.TrialPruned()

    return np.mean(scores)

study = optuna.create_study(
    direction='maximize',
    pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=2)
)
study.optimize(objective_con_pruning, n_trials=100)
```

### Visualizzazione dei Risultati Optuna

```python
import optuna.visualization as vis

# Importanza degli iperparametri
fig = vis.plot_param_importances(study)
# fig.show()

# Storia dell'ottimizzazione
fig = vis.plot_optimization_history(study)
# fig.show()

# Relazione tra parametri e score
fig = vis.plot_slice(study, params=['max_depth', 'learning_rate'])
# fig.show()

# Parallel coordinate plot
fig = vis.plot_parallel_coordinate(study)
# fig.show()
```

### Optuna vs GridSearchCV vs RandomizedSearchCV

| Aspetto | GridSearchCV | RandomizedSearchCV | Optuna |
|---|---|---|---|
| **Strategia** | Esaustiva (tutte le combinazioni) | Campionamento casuale | Bayesiana (TPE) |
| **Efficienza** | Molto bassa con molti parametri | Media | Alta (impara dai trial precedenti) |
| **Pruning** | No | No | Si' (interrompe trial non promettenti) |
| **Spazio di ricerca** | Griglia discreta | Distribuzioni continue | Distribuzioni + condizionali |
| **Parallelismo** | `n_jobs` | `n_jobs` | Distribuito (database condiviso) |
| **Visualizzazione** | Manuale | Manuale | Integrata (`optuna.visualization`) |
| **Caso d'uso** | Pochi parametri, piccoli dataset | Esplorazione iniziale | Ottimizzazione seria, grandi spazi |

Come regola pratica: usa GridSearchCV per spazi piccoli (< 100 combinazioni), RandomizedSearchCV per una prima esplorazione, e Optuna per ottimizzazione completa con molti iperparametri.

### Optuna con Persistenza dello Studio

```python
import optuna

# Persistenza su SQLite: lo studio sopravvive al riavvio del processo.
# Permette anche di riprendere l'ottimizzazione in sessioni successive.
study = optuna.create_study(
    study_name='xgboost_tuning',
    storage='sqlite:///optuna_studies.db',
    direction='maximize',
    load_if_exists=True  # riprende lo studio se esiste gia'
)

# Riprendere l'ottimizzazione con altri trial
study.optimize(objective, n_trials=20)
print(f"Trial totali: {len(study.trials)}")

# Elencare tutti gli studi nel database
studi = optuna.study.get_all_study_names(storage='sqlite:///optuna_studies.db')
print(f"Studi disponibili: {studi}")
```

---

## Time Series Forecasting

La previsione di serie temporali richiede tecniche specifiche perche' i dati hanno una dipendenza temporale intrinseca: il futuro dipende dal passato. Le sezioni precedenti hanno mostrato un approccio basato su lag features con Gradient Boosting. Qui approfondiamo con modelli statistici dedicati e tecniche di validazione appropriate.

### Modelli Statistici con statsmodels

```python
# pip install statsmodels
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas as pd
import numpy as np

# Simulazione serie temporale con trend, stagionalita' e rumore
np.random.seed(42)
date = pd.date_range('2023-01-01', periods=730, freq='D')
trend = np.linspace(100, 200, 730)
stagionalita = 20 * np.sin(2 * np.pi * np.arange(730) / 365)
rumore = np.random.normal(0, 5, 730)
valori = trend + stagionalita + rumore

ts = pd.Series(valori, index=date, name='vendite')

# --- Decomposizione stagionale ---
# Separa la serie in trend, stagionalita' e residuo.
decomp = seasonal_decompose(ts, model='additive', period=365)
# decomp.plot()  # visualizza le componenti

# --- Exponential Smoothing (Holt-Winters) ---
# Modello che cattura livello, trend e stagionalita'.
train = ts[:600]
test = ts[600:]

hw = ExponentialSmoothing(
    train,
    trend='add',           # trend additivo
    seasonal='add',        # stagionalita' additiva
    seasonal_periods=365   # periodo stagionale (annuale)
).fit()

forecast = hw.forecast(len(test))
mae = np.mean(np.abs(test - forecast))
print(f"Holt-Winters MAE: {mae:.2f}")

# --- ARIMA/SARIMAX ---
# AutoRegressive Integrated Moving Average con componente stagionale.
from statsmodels.tsa.statespace.sarimax import SARIMAX

sarimax = SARIMAX(
    train,
    order=(1, 1, 1),              # (p, d, q) non-stagionale
    seasonal_order=(1, 1, 1, 7),  # (P, D, Q, s) stagionale (settimanale)
    enforce_stationarity=False
).fit(disp=False)

forecast_sarimax = sarimax.forecast(len(test))
mae_sarimax = np.mean(np.abs(test - forecast_sarimax))
print(f"SARIMAX MAE: {mae_sarimax:.2f}")
print(sarimax.summary().tables[1])
```

### Walk-Forward Validation

Per le serie temporali, la cross-validation standard non e' appropriata perche' viola l'ordine temporale. La **walk-forward validation** (o expanding/sliding window) rispetta la sequenza temporale.

```python
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import numpy as np

def walk_forward_validation(X, y, model_class, model_params, n_splits=5):
    """
    Walk-forward validation: il training set cresce ad ogni split,
    il validation set e' sempre successivo temporalmente al training.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train_fold = X[train_idx]
        X_val_fold = X[val_idx]
        y_train_fold = y[train_idx]
        y_val_fold = y[val_idx]

        modello = model_class(**model_params)
        modello.fit(X_train_fold, y_train_fold)
        y_pred = modello.predict(X_val_fold)

        mae = mean_absolute_error(y_val_fold, y_pred)
        scores.append(mae)
        print(f"Fold {fold}: MAE={mae:.4f}, "
              f"Train size={len(train_idx)}, Val size={len(val_idx)}")

    print(f"\nMAE medio: {np.mean(scores):.4f} (+/- {np.std(scores):.4f})")
    return scores
```

### Feature Engineering per Serie Temporali

La creazione di feature temporali e' critica per i modelli ML applicati a serie temporali. A differenza dei modelli statistici (ARIMA, Holt-Winters) che modellano la struttura temporale direttamente, i modelli ML (Random Forest, XGBoost) richiedono feature esplicite che catturino i pattern temporali.

```python
import pandas as pd
import numpy as np

def create_time_features(df: pd.DataFrame, target_col: str,
                         date_col: str = 'ds') -> pd.DataFrame:
    """
    Genera un set completo di feature temporali per modelli ML.
    Include feature calendariali, lag, rolling statistics e indicatori di trend.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # --- Feature calendariali ---
    df['giorno_settimana'] = df[date_col].dt.dayofweek
    df['giorno_mese'] = df[date_col].dt.day
    df['mese'] = df[date_col].dt.month
    df['trimestre'] = df[date_col].dt.quarter
    df['giorno_anno'] = df[date_col].dt.dayofyear
    df['settimana_anno'] = df[date_col].dt.isocalendar().week.astype(int)
    df['is_weekend'] = (df['giorno_settimana'] >= 5).astype(int)
    df['is_inizio_mese'] = (df['giorno_mese'] <= 5).astype(int)
    df['is_fine_mese'] = (df['giorno_mese'] >= 25).astype(int)

    # --- Feature cicliche (sinusoidali) ---
    # Evita discontinuita' nelle feature calendariali
    # (es. giorno 31 -> giorno 1 non e' un salto nel tempo)
    df['mese_sin'] = np.sin(2 * np.pi * df['mese'] / 12)
    df['mese_cos'] = np.cos(2 * np.pi * df['mese'] / 12)
    df['dow_sin'] = np.sin(2 * np.pi * df['giorno_settimana'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['giorno_settimana'] / 7)

    # --- Lag features ---
    for lag in [1, 2, 3, 7, 14, 21, 28]:
        df[f'lag_{lag}'] = df[target_col].shift(lag)

    # --- Rolling statistics ---
    for window in [7, 14, 30]:
        df[f'rolling_mean_{window}'] = df[target_col].rolling(window).mean()
        df[f'rolling_std_{window}'] = df[target_col].rolling(window).std()
        df[f'rolling_min_{window}'] = df[target_col].rolling(window).min()
        df[f'rolling_max_{window}'] = df[target_col].rolling(window).max()

    # --- Expanding statistics (cumulativa) ---
    df['expanding_mean'] = df[target_col].expanding().mean()

    # --- Differenze (stazionarieta') ---
    df['diff_1'] = df[target_col].diff(1)
    df['diff_7'] = df[target_col].diff(7)

    return df
```

### Prophet (Meta)

**Prophet** e' una libreria sviluppata da Meta per forecasting di serie temporali business-oriented. E' robusto a dati mancanti, cambi di trend e festivita'.

```python
# pip install prophet
from prophet import Prophet
import pandas as pd

# Prophet richiede un DataFrame con colonne 'ds' (date) e 'y' (valori)
df_prophet = pd.DataFrame({
    'ds': date,
    'y': valori
})

train_prophet = df_prophet[:600]
test_prophet = df_prophet[600:]

# Creazione e training del modello
m = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.05  # flessibilita' del trend
)
m.fit(train_prophet)

# Previsione
future = m.make_future_dataframe(periods=len(test_prophet))
forecast = m.predict(future)

# Valutazione
pred_test = forecast.iloc[600:]['yhat'].values
mae_prophet = np.mean(np.abs(test_prophet['y'].values - pred_test))
print(f"Prophet MAE: {mae_prophet:.2f}")

# Visualizzazione delle componenti
# fig = m.plot_components(forecast)
```

---

## Interpretabilita' dei Modelli

L'interpretabilita' e' la capacita' di comprendere **perche'** un modello ha preso una determinata decisione. E' fondamentale per costruire fiducia nei modelli ML, identificare bias, soddisfare requisiti normativi (es. GDPR, che prevede il diritto alla spiegazione) e migliorare i modelli stessi.

### SHAP — SHapley Additive exPlanations

**SHAP** si basa sulla teoria dei giochi cooperativa (valori di Shapley) per assegnare a ogni feature un contributo alla previsione. E' matematicamente rigoroso e fornisce sia spiegazioni locali (singola previsione) che globali (modello nel suo complesso).

```python
# pip install shap
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_breast_cancer
import matplotlib.pyplot as plt

# Training del modello
data = load_breast_cancer()
X, y = data.data, data.target
feature_names = data.feature_names

modello = RandomForestClassifier(n_estimators=200, random_state=42)
modello.fit(X, y)

# --- Calcolo SHAP values ---
# TreeExplainer e' ottimizzato per modelli ad albero (RF, XGBoost, LightGBM)
explainer = shap.TreeExplainer(modello)
shap_values = explainer.shap_values(X)

# --- Spiegazione GLOBALE: importanza delle feature ---
# Mostra il contributo medio di ogni feature alle previsioni.
shap.summary_plot(shap_values[1], X, feature_names=feature_names, show=False)
plt.tight_layout()
plt.savefig("shap_summary.png", dpi=150, bbox_inches='tight')
plt.close()

# --- Spiegazione LOCALE: singola previsione ---
# Perche' il modello ha predetto "benigno" per il campione 0?
idx = 0
shap.force_plot(
    explainer.expected_value[1],
    shap_values[1][idx],
    X[idx],
    feature_names=feature_names,
    matplotlib=True,
    show=False
)
plt.tight_layout()
plt.savefig("shap_force.png", dpi=150, bbox_inches='tight')
plt.close()

# --- Dependence plot: relazione feature-SHAP ---
# Mostra come il valore di una feature influenza la previsione.
shap.dependence_plot(
    "worst radius", shap_values[1], X,
    feature_names=feature_names, show=False
)
plt.tight_layout()
plt.savefig("shap_dependence.png", dpi=150, bbox_inches='tight')
plt.close()

# --- SHAP per modelli non ad albero ---
# Per modelli generici (SVM, reti neurali), usare KernelExplainer.
# Piu' lento ma funziona con qualsiasi modello.
# kernel_explainer = shap.KernelExplainer(modello.predict_proba, shap.sample(X, 100))
# shap_values_kernel = kernel_explainer.shap_values(X[:10])
```

### LIME — Local Interpretable Model-agnostic Explanations

**LIME** spiega singole previsioni creando un modello semplice (lineare) che approssima localmente il comportamento del modello complesso nell'intorno di un campione specifico. E' model-agnostic: funziona con qualsiasi tipo di modello.

```python
# pip install lime
import lime
import lime.lime_tabular
from sklearn.ensemble import RandomForestClassifier
import numpy as np

modello = RandomForestClassifier(n_estimators=200, random_state=42)
modello.fit(X_train, y_train)

# Creazione dell'explainer
explainer = lime.lime_tabular.LimeTabularExplainer(
    training_data=X_train,
    feature_names=feature_names,
    class_names=['maligno', 'benigno'],
    mode='classification',
    random_state=42
)

# Spiegazione di una singola previsione
idx = 0
explanation = explainer.explain_instance(
    X_test[idx],
    modello.predict_proba,
    num_features=10,          # numero di feature da mostrare
    num_samples=5000          # campioni per l'approssimazione locale
)

# Visualizzazione
print(f"Previsione per campione {idx}: {modello.predict(X_test[idx:idx+1])[0]}")
print(f"Probabilita': {modello.predict_proba(X_test[idx:idx+1])[0]}")
print(f"\nContributi delle feature (top 10):")
for feature, peso in explanation.as_list():
    direzione = "+" if peso > 0 else "-"
    print(f"  {direzione} {feature}: {peso:.4f}")

# Salva come HTML interattivo
# explanation.save_to_file('lime_explanation.html')
```

### SHAP vs LIME — Quando Usare Quale

| Aspetto | SHAP | LIME |
|---|---|---|
| **Base teorica** | Valori di Shapley (game theory) | Approssimazione lineare locale |
| **Scope** | Locale + globale | Solo locale |
| **Consistenza** | Garantita matematicamente | Non garantita |
| **Velocita'** | Veloce per alberi, lento per altri | Sempre medio |
| **Interpretazione** | Contributo esatto di ogni feature | Peso di ogni feature nell'intorno |
| **Uso raccomandato** | Analisi approfondita, report | Spiegazioni rapide, debugging |

---

## AI Etica e Responsabile

L'AI etica affronta le implicazioni morali e sociali dei sistemi di machine learning. Un modello tecnicamente eccellente puo' essere dannoso se perpetua discriminazioni, viola la privacy o produce decisioni opache in contesti ad alto impatto (sanita', giustizia, credito, assunzioni).

### Fonti di Bias nel Machine Learning

Il bias puo' introdursi in ogni fase del workflow ML:

1. **Bias nei dati di raccolta**: dati storici che riflettono discriminazioni passate (es. dati di assunzione che penalizzano genere o etnia)
2. **Bias di selezione**: campione non rappresentativo della popolazione target
3. **Bias di misurazione**: variabili proxy che correlano con attributi protetti (es. CAP come proxy per etnia)
4. **Bias di etichettatura**: annotatori umani che introducono pregiudizi nelle etichette
5. **Bias algoritmico**: l'algoritmo amplifica pattern discriminatori presenti nei dati
6. **Bias di feedback loop**: un modello in produzione influenza i dati futuri, rinforzando i propri bias

### Metriche di Fairness

```python
import numpy as np
from sklearn.metrics import confusion_matrix

def fairness_metrics(y_true, y_pred, sensitive_attribute):
    """
    Calcola metriche di fairness per un attributo sensibile binario.

    - Demographic Parity: la probabilita' di previsione positiva
      deve essere uguale per tutti i gruppi.
    - Equal Opportunity: il True Positive Rate deve essere uguale
      per tutti i gruppi.
    - Equalized Odds: sia TPR che FPR devono essere uguali.
    """
    gruppi = np.unique(sensitive_attribute)

    risultati = {}
    for gruppo in gruppi:
        mask = sensitive_attribute == gruppo
        y_t = y_true[mask]
        y_p = y_pred[mask]

        tn, fp, fn, tp = confusion_matrix(y_t, y_p, labels=[0, 1]).ravel()

        positive_rate = (tp + fp) / len(y_t)               # P(pred=1)
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0       # True Positive Rate
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0       # False Positive Rate

        risultati[gruppo] = {
            'positive_rate': positive_rate,
            'tpr': tpr,
            'fpr': fpr,
            'count': len(y_t)
        }

    # Calcolo disparita'
    gruppi_list = list(risultati.values())
    dp_diff = abs(gruppi_list[0]['positive_rate'] - gruppi_list[1]['positive_rate'])
    eo_diff = abs(gruppi_list[0]['tpr'] - gruppi_list[1]['tpr'])

    print("Metriche di Fairness:")
    for gruppo, metriche in risultati.items():
        print(f"  Gruppo {gruppo}: "
              f"Positive Rate={metriche['positive_rate']:.4f}, "
              f"TPR={metriche['tpr']:.4f}, "
              f"FPR={metriche['fpr']:.4f}, "
              f"N={metriche['count']}")

    print(f"\n  Demographic Parity Gap: {dp_diff:.4f} "
          f"({'OK' if dp_diff < 0.1 else 'ATTENZIONE: possibile bias'})")
    print(f"  Equal Opportunity Gap: {eo_diff:.4f} "
          f"({'OK' if eo_diff < 0.1 else 'ATTENZIONE: possibile bias'})")

    return risultati
```

### AI Fairness 360 (IBM)

**AI Fairness 360** (AIF360) e' un toolkit open-source di IBM che fornisce metriche per rilevare bias e algoritmi per mitigarlo in tre fasi: pre-processing (sui dati), in-processing (durante il training) e post-processing (sulle previsioni).

```python
# pip install aif360
from aif360.datasets import BinaryLabelDataset
from aif360.metrics import BinaryLabelDatasetMetric, ClassificationMetric
from aif360.algorithms.preprocessing import Reweighing
import pandas as pd
import numpy as np

# Esempio: dataset di prestiti con attributo sensibile "genere"
np.random.seed(42)
n = 1000
df = pd.DataFrame({
    'reddito': np.random.normal(40000, 15000, n),
    'eta': np.random.randint(20, 65, n),
    'genere': np.random.choice([0, 1], n),  # 0=F, 1=M
    'approvato': np.random.randint(0, 2, n)
})

# Creazione dataset AIF360
dataset = BinaryLabelDataset(
    df=df,
    label_names=['approvato'],
    protected_attribute_names=['genere'],
    favorable_label=1,
    unfavorable_label=0
)

# Calcolo metriche di bias nel dataset
metric = BinaryLabelDatasetMetric(
    dataset,
    unprivileged_groups=[{'genere': 0}],
    privileged_groups=[{'genere': 1}]
)

print(f"Disparate Impact: {metric.disparate_impact():.4f}")
print(f"Statistical Parity Difference: {metric.statistical_parity_difference():.4f}")
# Disparate Impact ideale = 1.0 (nessuna disparita')
# Valori < 0.8 indicano possibile discriminazione (regola 80%)

# --- Mitigazione con Reweighing ---
# Assegna pesi ai campioni per bilanciare la rappresentazione
# dei gruppi protetti rispetto al label favorevole.
rw = Reweighing(
    unprivileged_groups=[{'genere': 0}],
    privileged_groups=[{'genere': 1}]
)
dataset_fair = rw.fit_transform(dataset)

metric_fair = BinaryLabelDatasetMetric(
    dataset_fair,
    unprivileged_groups=[{'genere': 0}],
    privileged_groups=[{'genere': 1}]
)
print(f"\nDopo Reweighing:")
print(f"Disparate Impact: {metric_fair.disparate_impact():.4f}")
print(f"Statistical Parity Difference: {metric_fair.statistical_parity_difference():.4f}")
```

### Checklist per AI Responsabile

Prima di deployare un modello ML in produzione, verificare:

- [ ] **Dati**: i dati di training sono rappresentativi della popolazione target? Contengono proxy per attributi protetti?
- [ ] **Bias**: sono state calcolate le metriche di fairness? Il Disparate Impact e' >= 0.8?
- [ ] **Interpretabilita'**: le decisioni del modello sono spiegabili con SHAP/LIME? Chi e' impattato dalla decisione puo' comprenderne le ragioni?
- [ ] **Privacy**: i dati personali sono protetti? Il modello puo' "memorizzare" dati sensibili del training set (membership inference)?
- [ ] **Monitoraggio**: esiste un sistema di monitoraggio continuo per rilevare drift e degradazione delle metriche di fairness in produzione?
- [ ] **Documentazione**: esiste una Model Card che descrive scopo, limitazioni, metriche di fairness e dati di training del modello?
- [ ] **Governance**: esiste un processo per contestare le decisioni del modello e per disattivarlo in caso di problemi?
- [ ] **Regolamentazione**: il modello rispetta le normative applicabili (GDPR, AI Act EU, settore specifico)?

---

> **Nota**: Questo documento fornisce una panoramica completa del machine learning con Python. Per approfondire ogni argomento, si consiglia la documentazione ufficiale di [scikit-learn](https://scikit-learn.org), [TensorFlow](https://www.tensorflow.org), [PyTorch](https://pytorch.org) e [MLflow](https://mlflow.org). La pratica costante su dataset reali (disponibili su [Kaggle](https://www.kaggle.com)) e' il modo migliore per consolidare le competenze.

---

## Esercizi

1. **Classificazione supervisionata end-to-end** — Scarica un dataset tabellare da scikit-learn (es. breast cancer, iris) ed esegui il workflow completo: EDA, preprocessing (scaling, encoding), train/test split, training di 3 modelli diversi (Logistic Regression, Random Forest, SVM), evaluation con cross-validation, confronto metriche (accuracy, F1, ROC-AUC), e selezione del modello migliore. Serializza il modello finale con `joblib`.

2. **Pipeline scikit-learn con preprocessor** — Costruisci una `Pipeline` che combini: `ColumnTransformer` per preprocessing differenziato (scaling numerico + one-hot encoding categorico), feature selection con `SelectKBest`, e un classificatore. Usa `GridSearchCV` per ottimizzare gli iperparametri. Confronta i risultati con e senza feature selection.

3. **Rete neurale con PyTorch** — Implementa un classificatore di immagini MNIST con PyTorch: definisci un `nn.Module` con almeno 2 layer convoluzionali, implementa il training loop con `DataLoader`, traccia loss e accuracy per epoch, salva il modello migliore con `torch.save`. Visualizza la matrice di confusione sul test set.

4. **Experiment tracking con MLflow** — Prendi uno degli esercizi precedenti e aggiungi tracking con MLflow: logga parametri, metriche per epoch, modello finale e artifact (grafici). Usa `mlflow.autolog()` per scikit-learn e logging manuale per PyTorch. Confronta almeno 5 run diversi nella MLflow UI.

5. **Ottimizzazione iperparametri con Optuna** — Configura uno studio Optuna per ottimizzare gli iperparametri di un Gradient Boosting (XGBoost o LightGBM) su un dataset di regressione. Definisci lo spazio di ricerca, usa pruning per interrompere trial poco promettenti, e integra con MLflow per il tracking. Confronta i risultati con `GridSearchCV`.

6. **Gestione classi sbilanciate** — Usa il dataset `make_classification` con `weights=[0.97, 0.03]` per simulare un problema di frode. Confronta le performance (F1, precision, recall) di: (a) modello senza bilanciamento, (b) SMOTE, (c) `class_weight='balanced'`, (d) threshold tuning. Visualizza le curve precision-recall per ciascuna strategia.

7. **Riduzione dimensionalita' e visualizzazione** — Carica il dataset MNIST (digits) e applica PCA, t-SNE e UMAP per ridurre a 2 dimensioni. Confronta le visualizzazioni: quale tecnica separa meglio i cluster? Poi usa UMAP come preprocessing (10 componenti) e confronta l'accuracy di un Random Forest con e senza riduzione dimensionalita'.

8. **NLP con spaCy e Hugging Face** — Scarica un dataset di recensioni in italiano. Implementa una pipeline di preprocessing con spaCy (tokenizzazione, lemmatizzazione, rimozione stopword). Poi usa un modello Hugging Face per sentiment analysis e confronta i risultati con un classificatore TF-IDF + Logistic Regression.

9. **Interpretabilita' con SHAP e LIME** — Addestra un modello XGBoost sul dataset breast cancer. Genera SHAP summary plot, force plot per 3 campioni specifici, e dependence plot per le 2 feature piu' importanti. Confronta le spiegazioni SHAP con quelle LIME per gli stessi campioni. Le feature evidenziate sono coerenti?

10. **Fairness audit** — Crea un dataset sintetico di approvazione prestiti con un attributo sensibile. Calcola Demographic Parity e Equal Opportunity prima e dopo aver applicato Reweighing (AIF360). Il modello mitigato mantiene performance accettabili? Documenta il trade-off fairness vs accuracy.

---

## Letture e Riferimenti

### Fonti primarie

- scikit-learn Documentation — https://scikit-learn.org/stable/user_guide.html (consultato: 2026-05-24)
- PyTorch Documentation — https://pytorch.org/docs/stable/ (consultato: 2026-05-24)
- MLflow Documentation — https://mlflow.org/docs/latest/ (consultato: 2026-05-24)
- Optuna Documentation — https://optuna.readthedocs.io/ (consultato: 2026-05-24)
- pandas Documentation — https://pandas.pydata.org/docs/ (consultato: 2026-05-24)
- Kaggle — *Datasets and Competitions* — https://www.kaggle.com/ (consultato: 2026-05-24)

### Fonti aggiuntive

- spaCy Documentation — https://spacy.io/usage (consultato: 2026-05-24)
- Hugging Face Transformers — https://huggingface.co/docs/transformers/ (consultato: 2026-05-24)
- SHAP Documentation — https://shap.readthedocs.io/ (consultato: 2026-05-24)
- LIME Documentation — https://lime-ml.readthedocs.io/ (consultato: 2026-05-24)
- CatBoost Documentation — https://catboost.ai/docs/ (consultato: 2026-05-24)
- imbalanced-learn Documentation — https://imbalanced-learn.org/stable/ (consultato: 2026-05-24)
- UMAP Documentation — https://umap-learn.readthedocs.io/ (consultato: 2026-05-24)
- Prophet Documentation — https://facebook.github.io/prophet/ (consultato: 2026-05-24)
- AI Fairness 360 — https://aif360.mybluemix.net/ (consultato: 2026-05-24)
- Sentence Transformers — https://www.sbert.net/ (consultato: 2026-05-24)

### Libri consigliati

- *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow, 3rd Edition* — Aurelien Geron — O'Reilly, 2022
- *Deep Learning with PyTorch* — Eli Stevens, Luca Antiga — Manning, 2020
- *Machine Learning with PyTorch and Scikit-Learn* — Sebastian Raschka — Packt, 2022
- *Interpretable Machine Learning* — Christoph Molnar — 2023 (disponibile online)

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [14 — Data Processing](14-data-processing.md) | Preparazione dati con pandas e NumPy per il training ML |
| [25 — Performance](25-performance.md) | Ottimizzazione del training: vectorization, Numba, profiling |
| [09 — Type Hints](09-type-hints-e-mypy.md) | Type safety nelle pipeline ML e nelle API di serving |
| [26 — Docker](26-docker-per-python.md) | Containerizzazione di modelli ML per deployment |
| [27 — CI/CD](27-ci-cd-per-python.md) | Automazione del training e deployment nella pipeline CI/CD |
| [29 — Pydantic](29-pydantic-e-validazione.md) | Validazione dei dati di input per modelli ML in produzione |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Supervised Learning** | Apprendimento da dati etichettati (con target noto) per predire il target su dati nuovi |
| **Unsupervised Learning** | Apprendimento da dati non etichettati per scoprire strutture nascoste (clustering, riduzione dimensionalita) |
| **Overfitting** | Il modello memorizza i dati di training invece di generalizzare, producendo prestazioni scarse su dati nuovi |
| **Cross-validation** | Tecnica che suddivide i dati in K fold per valutare le prestazioni del modello in modo robusto |
| **Feature Engineering** | Processo di creazione, selezione e trasformazione delle variabili di input per migliorare le prestazioni del modello |
| **Pipeline** | Oggetto scikit-learn che concatena preprocessing e modello in un unico flusso coerente e riproducibile |
| **Iperparametri** | Parametri del modello non appresi dai dati ma definiti prima del training (es. learning rate, n_estimators) |
| **MLflow** | Piattaforma open-source per il tracking di esperimenti ML, gestione modelli e deployment |
| **Optuna** | Framework per l'ottimizzazione automatica degli iperparametri con pruning e ricerca intelligente |
| **Data Leakage** | Errore in cui informazioni dal test set influenzano il training, producendo metriche ottimistiche irrealistiche |
| **Gradient Boosting** | Ensemble di alberi decisionali addestrati sequenzialmente, ciascuno che corregge gli errori del precedente |
| **ROC-AUC** | Area sotto la curva ROC, metrica che misura la capacita discriminativa di un classificatore binario |
| **SMOTE** | Synthetic Minority Over-sampling Technique — genera campioni sintetici per bilanciare classi sotto-rappresentate |
| **CatBoost** | Libreria di gradient boosting (Yandex) con supporto nativo per feature categoriche e alberi simmetrici |
| **Stacking** | Metodo ensemble che combina le previsioni di piu' modelli base usando un meta-learner di secondo livello |
| **PCA** | Principal Component Analysis — riduzione dimensionalita' lineare che proietta i dati sulle direzioni di massima varianza |
| **t-SNE** | t-Distributed Stochastic Neighbor Embedding — tecnica non lineare per visualizzazione di dati ad alta dimensionalita' |
| **UMAP** | Uniform Manifold Approximation and Projection — riduzione dimensionalita' non lineare veloce, preserva struttura locale e globale |
| **spaCy** | Libreria NLP industriale per tokenizzazione, POS tagging, NER e dependency parsing |
| **Transformer** | Architettura di rete neurale basata su meccanismi di attenzione, alla base di BERT, GPT e modelli linguistici moderni |
| **SHAP** | SHapley Additive exPlanations — metodo basato sulla teoria dei giochi per spiegare le previsioni di un modello |
| **LIME** | Local Interpretable Model-agnostic Explanations — spiega singole previsioni con modelli surrogati locali |
| **Data Drift** | Cambiamento della distribuzione dei dati in produzione rispetto ai dati di training, che degrada le prestazioni del modello |
| **Model Registry** | Repository centralizzato per gestire versioni dei modelli con stati (Staging, Production, Archived) |
| **Fairness** | Proprieta' di un sistema AI che tratta tutti i gruppi equamente, senza discriminazione basata su attributi protetti |
| **Pruning (Optuna)** | Interruzione precoce di trial di ottimizzazione che non mostrano risultati promettenti |
| **Prophet** | Libreria Meta per forecasting di serie temporali business-oriented, robusta a dati mancanti e festivita' |
