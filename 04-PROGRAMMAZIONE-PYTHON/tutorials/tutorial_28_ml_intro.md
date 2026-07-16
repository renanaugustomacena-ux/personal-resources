# Tutorial 28 — Machine Learning Intro: scikit-learn, Pipeline, Valutazione

> **Companion a:** `28-ml-intro.md`
> **Scope:** scikit-learn, Pipeline, preprocessing, modelli, valutazione, serializzazione modelli
> **Prerequisiti:** `tutorial_14_data_processing.md`, `tutorial_09_type_hints_mypy.md`
> **Durata stimata:** 16-20 ore
> **Stack:** Python 3.12+, scikit-learn 1.5+, pandas, numpy, joblib

---

## Mappa concettuale

```
Machine Learning con Python
│
├── Workflow ML
│   ├── Definizione problema
│   ├── Raccolta e analisi dati
│   ├── Feature engineering
│   ├── Selezione modello
│   ├── Training e valutazione
│   └── Deploy e monitoring
│
├── scikit-learn API
│   ├── Estimator — fit(X, y)
│   ├── Predictor — predict(X)
│   ├── Transformer — transform(X)
│   └── Pipeline — concatena steps
│
├── Preprocessing
│   ├── StandardScaler — normalizzazione
│   ├── OneHotEncoder — categoriali
│   ├── SimpleImputer — valori mancanti
│   └── ColumnTransformer — colonne diverse
│
├── Modelli
│   ├── Classificazione — LogisticRegression, RF, GBM
│   ├── Regressione — LinearRegression, Ridge, SVR
│   ├── Clustering — KMeans, DBSCAN
│   └── Anomaly detection — IsolationForest
│
└── Valutazione
    ├── Cross-validation — k-fold
    ├── Metriche classificazione — precision/recall/F1/AUC
    ├── Metriche regressione — MAE/MSE/R²
    └── Hyperparameter tuning — GridSearchCV, RandomizedSearchCV
```

---

# Parte A — Fondamentali scikit-learn

---

## A1. API base: fit, predict, transform

```python
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris, make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, classification_report

# ── Dataset di classificazione ──────────────────────────────
iris = load_iris()
X, y = iris.data, iris.target   # feature matrix e target vector

# Split train/test (strategified mantiene proporzione classi)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Preprocessing — normalizzazione
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # calcola media/std su train
X_test_scaled = scaler.transform(X_test)          # applica stessa trasformazione a test

# IMPORTANTE: fit solo su train, mai su test (data leakage)

# Modello
modello = LogisticRegression(max_iter=1000, random_state=42)
modello.fit(X_train_scaled, y_train)

# Predizione
y_pred = modello.predict(X_test_scaled)
prob = modello.predict_proba(X_test_scaled)   # probabilità per classe

# Valutazione
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nReport dettagliato:")
print(classification_report(y_test, y_pred, target_names=iris.target_names))
```

> **Analogia:** scikit-learn è come un kit di utensili standardizzato. Ogni strumento (estimator) ha la stessa interfaccia: `fit()` per "imparare dai dati", `predict()` per "applicare ciò che hai imparato", `transform()` per "trasformare i dati". Questa uniformità permette di combinare strumenti in Pipeline come mattoncini LEGO.

---

## A2. Pipeline: il cuore di scikit-learn

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score

# Dataset misto: numerici + categoriali
df = pd.DataFrame({
    "eta": [25, 32, None, 28, 45, 36],
    "reddito": [35000, 52000, 41000, None, 68000, 55000],
    "citta": ["Roma", "Milano", "Roma", "Napoli", "Milano", "Roma"],
    "istruzione": ["laurea", "diploma", "laurea", "nessuno", "laurea", "diploma"],
    "acquisto": [1, 0, 1, 0, 1, 1],
})

X = df.drop("acquisto", axis=1)
y = df["acquisto"]

# Definisci colonne per tipo
col_numeriche = ["eta", "reddito"]
col_categoriali = ["citta", "istruzione"]

# Preprocessore per colonne diverse
preprocessore = ColumnTransformer(
    transformers=[
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), col_numeriche),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), col_categoriali),
    ],
    remainder="drop",
)

# Pipeline completa — preprocessing + modello
pipeline = Pipeline([
    ("preprocessore", preprocessore),
    ("classificatore", RandomForestClassifier(n_estimators=100, random_state=42)),
])

# Cross-validation — valutazione robusta senza data leakage
# Pipeline esegue fit su train fold, transform su validation fold — corretto!
scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
print(f"Accuracy CV: {scores.mean():.3f} ± {scores.std():.3f}")
```

---

# Parte B — Modelli e valutazione

---

## B1. Valutazione classificazione

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    ConfusionMatrixDisplay,
)
from sklearn.model_selection import cross_validate
import matplotlib.pyplot as plt

# Valutazione multi-metrica
def valuta_classificatore(modello, X_train, X_test, y_train, y_test) -> dict:
    modello.fit(X_train, y_train)
    y_pred = modello.predict(X_test)
    y_prob = modello.predict_proba(X_test)[:, 1] if hasattr(modello, "predict_proba") else None

    metriche = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, average="weighted", zero_division=0),
        "recall": recall_score(y_test, y_pred, average="weighted", zero_division=0),
        "f1": f1_score(y_test, y_pred, average="weighted", zero_division=0),
    }
    if y_prob is not None:
        metriche["auc_roc"] = roc_auc_score(y_test, y_prob)

    return metriche

# Cross-validation multi-metrica
cv_risultati = cross_validate(
    pipeline,
    X, y,
    cv=5,
    scoring=["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"],
    return_train_score=True,
)
for metrica, valori in cv_risultati.items():
    if metrica.startswith("test_"):
        print(f"{metrica}: {valori.mean():.3f} ± {valori.std():.3f}")
```

---

## B2. Hyperparameter tuning

```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from scipy.stats import randint, uniform

# GridSearchCV — ricerca esaustiva (piccolo spazio)
param_grid = {
    "classificatore__n_estimators": [50, 100, 200],
    "classificatore__max_depth": [None, 5, 10],
    "classificatore__min_samples_leaf": [1, 5, 10],
}

grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring="f1_weighted",
    n_jobs=-1,          # usa tutti i core
    verbose=1,
    refit=True,         # riallena con i migliori parametri su tutto il dataset
)
grid_search.fit(X, y)
print(f"Migliori parametri: {grid_search.best_params_}")
print(f"Miglior F1: {grid_search.best_score_:.3f}")

# RandomizedSearchCV — ricerca casuale (grande spazio)
param_dist = {
    "classificatore__n_estimators": randint(50, 500),
    "classificatore__max_depth": [None, *range(5, 50)],
    "classificatore__min_samples_leaf": randint(1, 20),
    "classificatore__max_features": uniform(0.1, 0.9),
}
random_search = RandomizedSearchCV(
    pipeline,
    param_dist,
    n_iter=50,          # 50 combinazioni casuali
    cv=5,
    scoring="f1_weighted",
    n_jobs=-1,
    random_state=42,
)
```

---

# Parte C — Serializzazione e deploy

---

## C1. Salvare e caricare modelli

```python
import joblib
from pathlib import Path

# Salvataggio — joblib è più efficiente di pickle per array NumPy
pipeline.fit(X, y)
modello_path = Path("modelli") / "classificatore_v1.joblib"
modello_path.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(pipeline, modello_path, compress=3)

# Caricamento
pipeline_caricato = joblib.load(modello_path)
y_pred = pipeline_caricato.predict(X)

# Metadata del modello
import json
metadata = {
    "versione": "1.0.0",
    "algoritmo": type(pipeline.named_steps["classificatore"]).__name__,
    "feature_numeriche": col_numeriche,
    "feature_categoriali": col_categoriali,
    "metriche_train": {
        "accuracy": float(cross_val_score(pipeline, X, y, cv=5).mean()),
    },
    "addestrato_il": "2024-01-15",
    "dataset": "acquisti_clienti_v3.csv",
}
(modello_path.with_suffix(".json")).write_text(json.dumps(metadata, indent=2))

# Serve il modello con FastAPI
from fastapi import FastAPI

app = FastAPI()
_modello = joblib.load(modello_path)

@app.post("/predici")
def predici(dati: dict) -> dict:
    df_input = pd.DataFrame([dati])
    pred = _modello.predict(df_input)
    prob = _modello.predict_proba(df_input)
    return {
        "predizione": int(pred[0]),
        "probabilita": float(prob[0][1]),
    }
```

---

# Parte D — Anomaly detection e clustering

---

## D1. IsolationForest per anomaly detection

```python
from sklearn.ensemble import IsolationForest
import numpy as np

# Generazione dati con anomalie
rng = np.random.default_rng(42)
dati_normali = rng.standard_normal((100, 2))
anomalie = rng.uniform(-6, 6, (10, 2))
X_tutti = np.vstack([dati_normali, anomalie])

# IsolationForest — identifica punti anomali
isoforest = IsolationForest(
    n_estimators=100,
    contamination=0.1,   # stima proporzione anomalie
    random_state=42,
)
y_pred = isoforest.fit_predict(X_tutti)   # 1 = normale, -1 = anomalia
score = isoforest.decision_function(X_tutti)   # punteggio (più basso = più anomalo)

n_anomalie = (y_pred == -1).sum()
print(f"Anomalie rilevate: {n_anomalie}")

# KMeans clustering
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Sceglie K ottimale con elbow method
inertie = []
k_range = range(2, 11)
for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(dati_normali)
    inertie.append(km.inertia_)

# Cluster con K=3
km_finale = KMeans(n_clusters=3, random_state=42, n_init=10)
etichette = km_finale.fit_predict(dati_normali)
print(f"Silhouette score: {silhouette_score(dati_normali, etichette):.3f}")
```

---

# Parte E — Riepilogo

## Workflow ML riproducibile

```python
# Struttura progetto ML raccomandato
# ml_progetto/
# ├── data/
# │   ├── raw/            ← dati originali (immutabili)
# │   ├── processed/      ← dati preprocessati
# │   └── external/       ← dati da fonti esterne
# ├── notebooks/          ← esplorazione (non produzione!)
# ├── src/
# │   ├── features.py     ← feature engineering
# │   ├── train.py        ← training pipeline
# │   └── predict.py      ← inference
# ├── modelli/            ← joblib + metadata JSON
# ├── tests/              ← test anche per ML!
# └── pyproject.toml

# Riproducibilità
import random, numpy as np

def imposta_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    # torch.manual_seed(seed) — se si usa PyTorch
```

## Anti-pattern ML

| Anti-pattern | Conseguenza | Soluzione |
|---|---|---|
| Data leakage | Overfit, metriche false | Fit scaler solo su train |
| Train = Test | Non vedi il vero errore | split() sempre |
| Hypertuning su test | Leakage di informazione | Hold-out finale separato |
| Valutazione singola | Varianza alta | Cross-validation |
| Modello senza baseline | Non sai se è utile | Compara con DummyClassifier |

## Prossimi passi

- `tutorial_29_pydantic.md` — validare l'input al modello ML
- `tutorial_31_otel.md` — monitoring del modello in produzione
