# Exploratory Data Analysis (EDA) — Techniques and Tools

## Indice

1. [EDA Methodology](#1-eda-methodology)
2. [Statistical Summaries](#2-statistical-summaries)
3. [Data Distributions](#3-data-distributions)
4. [Visualization for EDA](#4-visualization-for-eda)
5. [Correlation and Relationships](#5-correlation-and-relationships)
6. [Missing Data Analysis](#6-missing-data-analysis)
7. [Outlier Detection](#7-outlier-detection)
8. [Automated EDA Tools](#8-automated-eda-tools)
9. [EDA for Security](#9-eda-for-security)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. EDA Methodology

### 1.1 Tukey's Framework

John Tukey introduced Exploratory Data Analysis nel 1977 come risposta al paradigma dominante della statistica inferenziale. L'idea fondamentale: prima di testare ipotesi, bisogna *generarle*. EDA non cerca conferme — cerca pattern, anomalie e strutture che i test formali non possono rivelare se non sai dove guardare.

Tukey distinse chiaramente tra:

- **Exploration** (generazione di ipotesi): processo aperto, visivo, iterativo. Non si parte con una domanda precisa ma con curiosità strutturata.
- **Confirmation** (test di ipotesi): processo chiuso, statisticamente rigoroso, che richiede ipotesi pre-definite.

Il paradigma moderno ha integrato questa distinzione: EDA precede il modeling, non lo sostituisce. Un modello costruito senza EDA è un modello cieco.

### 1.2 Hypothesis Generation vs Hypothesis Testing

| Aspetto | Hypothesis Generation (EDA) | Hypothesis Testing |
|---------|----------------------------|--------------------|
| Obiettivo | Scoprire pattern | Confermare pattern |
| Approccio | Aperto, iterativo | Chiuso, formale |
| Strumenti | Grafici, summary stats, trasformazioni | p-value, CI, test statistici |
| Rischio | Apofenia (vedere pattern inesistenti) | Confermare il noto, perdere il nuovo |
| Output | Ipotesi candidate, feature engineering ideas | Decisioni binarie (accept/reject) |

In pratica, EDA alimenta il feature engineering e la selezione del modello. Un data scientist che salta EDA e va direttamente al modeling sta ottimizzando alla cieca.

### 1.3 Structured EDA Workflow

Il workflow EDA segue quattro fasi distinte:

#### Fase 1: Understand (Comprensione)

```python
import pandas as pd
import numpy as np

df = pd.read_csv("dataset.csv")

# Dimensioni e struttura
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Dtypes:\n{df.dtypes}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.2f} MB")

# Prime osservazioni
df.head(10)
df.tail(5)
df.sample(10, random_state=42)
```

Domande chiave in questa fase:
- Quante osservazioni e variabili?
- Quali sono i tipi di dato (numerici, categorici, temporali, testo)?
- Qual e' il significato semantico di ogni colonna?
- Quale granularita' hanno i dati (riga = transazione? utente? giorno?)?
- Ci sono chiavi primarie o foreign key implicite?

#### Fase 2: Clean (Pulizia)

```python
# Valori mancanti
missing_pct = df.isnull().mean() * 100
print(missing_pct[missing_pct > 0].sort_values(ascending=False))

# Duplicati
duplicates = df.duplicated().sum()
print(f"Duplicati: {duplicates} ({duplicates/len(df)*100:.2f}%)")

# Tipi errati
# Colonne che sembrano date ma sono stringhe
date_candidates = df.select_dtypes(include='object').apply(
    lambda col: pd.to_datetime(col, errors='coerce').notna().mean()
)
print(date_candidates[date_candidates > 0.8])

# Valori impossibili
numeric_cols = df.select_dtypes(include=np.number).columns
for col in numeric_cols:
    neg_count = (df[col] < 0).sum()
    if neg_count > 0 and col in ['age', 'price', 'quantity']:
        print(f"WARNING: {col} has {neg_count} negative values")
```

#### Fase 3: Explore (Esplorazione)

Questa e' la fase core dell'EDA — analisi univariata, bivariata e multivariata. Dettagliata nelle sezioni successive.

#### Fase 4: Communicate (Comunicazione)

L'EDA non e' completa finche' i risultati non sono documentati:
- Key findings con evidenza visiva
- Data quality issues identificati
- Feature engineering suggestions
- Ipotesi da testare formalmente
- Limitazioni del dataset

### 1.4 Univariate, Bivariate, Multivariate Analysis

**Analisi Univariata** — una variabile alla volta:
- Distribuzione (forma, centro, spread)
- Valori anomali
- Missing values
- Cardinalita' (per categoriche)

**Analisi Bivariata** — relazioni tra coppie:
- Numerica vs Numerica: scatter plot, correlazione
- Numerica vs Categorica: boxplot per gruppo, t-test
- Categorica vs Categorica: contingency table, chi-squared

**Analisi Multivariata** — interazioni complesse:
- Pair plots (matrice di scatter)
- PCA per riduzione dimensionale
- Clustering esplorativo
- Heatmap di correlazione
- Parallel coordinates

### 1.5 When to Use EDA

**Pre-modeling**: sempre. EDA rivela quali feature sono informative, quali hanno relazioni non lineari, dove servono trasformazioni.

**Data Auditing**: quando si riceve un dataset nuovo (da un fornitore, da un'acquisizione, da un sistema legacy). EDA come quality gate.

**Anomaly Investigation**: quando un KPI cambia improvvisamente. EDA dei dati sottostanti per capire *dove* e *perche'* e' cambiato.

**Post-modeling**: residual analysis, error analysis per capire dove il modello fallisce.

**Continuous Monitoring**: EDA automatizzata come parte della pipeline MLOps per detect data drift.

---

## 2. Statistical Summaries

### 2.1 Measures of Central Tendency

#### Mean (Media Aritmetica)

```python
# Media semplice
mean_val = df['revenue'].mean()

# Media pesata
weights = df['sample_weight']
weighted_mean = np.average(df['revenue'], weights=weights)
```

La media e' sensibile agli outlier. Un singolo valore estremo puo' spostarla significativamente. Per distribuzioni skewed, la media non rappresenta il "tipico".

#### Median (Mediana)

```python
median_val = df['revenue'].median()

# Per dati grouped
grouped_medians = df.groupby('category')['revenue'].median()
```

La mediana e' robusta: il 50esimo percentile non cambia se il valore massimo diventa 10x piu' grande. Preferita per distribuzioni con code pesanti (salari, prezzi immobiliari, durata sessioni web).

#### Mode (Moda)

```python
# Moda (puo' essere multipla)
mode_val = df['category'].mode()

# Per numeriche continue, la moda e' poco utile senza binning
# Meglio usare KDE per trovare i picchi
from scipy.stats import gaussian_kde
kde = gaussian_kde(df['revenue'].dropna())
x_range = np.linspace(df['revenue'].min(), df['revenue'].max(), 1000)
mode_estimate = x_range[np.argmax(kde(x_range))]
```

#### Trimmed Mean (Media Troncata)

```python
from scipy.stats import trim_mean

# Rimuove il 10% estremo da entrambi i lati
trimmed = trim_mean(df['revenue'].dropna(), proportiontocut=0.1)
```

La media troncata e' un compromesso tra mean e median: rimuove gli estremi ma usa piu' dati della sola mediana. Utile quando si sospettano outlier ma non si vuole perdere tutta l'informazione della distribuzione.

### 2.2 Measures of Spread

#### Variance and Standard Deviation

```python
# Varianza (unita' al quadrato — meno interpretabile)
var = df['revenue'].var()      # ddof=1 di default in pandas (sample variance)

# Deviazione standard (stesse unita' della variabile)
std = df['revenue'].std()

# Population variance (ddof=0) per dataset completi
pop_var = df['revenue'].var(ddof=0)
```

#### Interquartile Range (IQR)

```python
Q1 = df['revenue'].quantile(0.25)
Q3 = df['revenue'].quantile(0.75)
IQR = Q3 - Q1

# Bounds per outlier detection (Tukey's fences)
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
```

L'IQR e' robusto: non viene influenzato dagli estremi. E' la base del boxplot e della regola di Tukey per gli outlier.

#### Median Absolute Deviation (MAD)

```python
from scipy.stats import median_abs_deviation

mad = median_abs_deviation(df['revenue'].dropna())

# Equivalente robusto della std (con fattore di scala per normalita')
robust_std = mad * 1.4826
```

MAD e' il piu' robusto estimatore di dispersione. Breakdown point del 50% (serve che meta' dei dati siano corrotti per invalidarlo).

#### Range

```python
data_range = df['revenue'].max() - df['revenue'].min()
```

Il range e' il piu' sensibile agli outlier — basta un singolo valore estremo per distorcerlo completamente. Utile solo come sanity check iniziale.

### 2.3 Skewness and Kurtosis

```python
from scipy.stats import skew, kurtosis

# Skewness: asimmetria della distribuzione
# = 0: simmetrica
# > 0: coda destra (right-skewed, positiva)
# < 0: coda sinistra (left-skewed, negativa)
sk = skew(df['revenue'].dropna())

# Kurtosis (excess kurtosis, Fisher's definition)
# = 0: mesokurtic (come la normale)
# > 0: leptokurtic (code pesanti, picco acuto)
# < 0: platykurtic (code leggere, piatto)
kurt = kurtosis(df['revenue'].dropna())

print(f"Skewness: {sk:.4f}")
print(f"Kurtosis: {kurt:.4f}")

# Regola pratica:
# |skewness| > 1: fortemente asimmetrico
# |skewness| 0.5-1: moderatamente asimmetrico
# |skewness| < 0.5: approssimativamente simmetrico
```

Skewness alta suggerisce trasformazione logaritmica. Kurtosis alta indica la presenza di outlier o di una distribuzione con code pesanti (importante per risk modeling).

### 2.4 Percentiles and Quantiles

```python
# Percentili specifici
percentiles = df['revenue'].quantile([0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
print(percentiles)

# Decili
deciles = df['revenue'].quantile(np.arange(0, 1.1, 0.1))

# Quantile function (inversa della CDF)
# "A quale valore corrisponde il 95esimo percentile?"
p95 = df['revenue'].quantile(0.95)
print(f"95th percentile: {p95}")

# Percentile rank: "quale percentile e' il valore X?"
from scipy.stats import percentileofscore
rank = percentileofscore(df['revenue'].dropna(), 10000)
print(f"10000 is at the {rank:.1f}th percentile")
```

### 2.5 Five-Number Summary

```python
# Il five-number summary di Tukey
five_num = df['revenue'].describe()[['min', '25%', '50%', '75%', 'max']]
print(five_num)

# Equivalente manuale
summary = {
    'min': df['revenue'].min(),
    'Q1': df['revenue'].quantile(0.25),
    'median': df['revenue'].median(),
    'Q3': df['revenue'].quantile(0.75),
    'max': df['revenue'].max()
}
```

Il five-number summary e' la base del boxplot. Fornisce un quadro completo della distribuzione senza assumere normalita'.

### 2.6 Descriptive Statistics at Scale

Con dataset di milioni/miliardi di righe, pandas non scala. Serve un approccio distribuito.

#### PySpark

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    mean, stddev, min as spark_min, max as spark_max,
    percentile_approx, skewness, kurtosis, count, col
)

spark = SparkSession.builder.appName("EDA").getOrCreate()
sdf = spark.read.parquet("s3://bucket/large_dataset/")

# Summary statistics distribuito
stats = sdf.select(
    count("revenue").alias("count"),
    mean("revenue").alias("mean"),
    stddev("revenue").alias("std"),
    spark_min("revenue").alias("min"),
    spark_max("revenue").alias("max"),
    percentile_approx("revenue", [0.25, 0.5, 0.75]).alias("quartiles"),
    skewness("revenue").alias("skewness"),
    kurtosis("revenue").alias("kurtosis")
)
stats.show()

# Nota: percentile_approx usa l'algoritmo GK (Greenwald-Khanna)
# con errore relativo configurabile
```

#### Dask

```python
import dask.dataframe as dd

ddf = dd.read_parquet("s3://bucket/large_dataset/")

# Compute distribuito delle statistiche
desc = ddf['revenue'].describe().compute()

# Quantili approssimati
quantiles = ddf['revenue'].quantile([0.25, 0.5, 0.75]).compute()
```

#### Polars (single-machine, molto piu' veloce di pandas)

```python
import polars as pl

df_pl = pl.scan_parquet("large_dataset/*.parquet")

stats = df_pl.select(
    pl.col("revenue").mean().alias("mean"),
    pl.col("revenue").std().alias("std"),
    pl.col("revenue").median().alias("median"),
    pl.col("revenue").quantile(0.25).alias("Q1"),
    pl.col("revenue").quantile(0.75).alias("Q3"),
    pl.col("revenue").skew().alias("skewness"),
    pl.col("revenue").kurtosis().alias("kurtosis"),
).collect()
```

---

## 3. Data Distributions

### 3.1 Common Distributions

#### Normal (Gaussiana)

La distribuzione piu' importante in statistica per il Central Limit Theorem. Caratterizzata da media e deviazione standard. Simmetrica, code che decadono esponenzialmente.

```python
from scipy import stats
import numpy as np

# Generare dati normali
data_normal = stats.norm.rvs(loc=100, scale=15, size=10000, random_state=42)

# Parametri: mean=100, std=15
# 68% dei dati entro 1 std dalla media
# 95% entro 2 std
# 99.7% entro 3 std
```

**Dove si trova**: errori di misura, altezze umane, QI scores, residui di modelli lineari ben specificati.

#### Log-Normal

```python
# Log-Normal: il logaritmo dei dati e' normale
data_lognormal = stats.lognorm.rvs(s=0.5, loc=0, scale=np.exp(3), size=10000, random_state=42)

# Caratteristica: positiva, right-skewed, moltiplicativa
# log(X) ~ Normal(mu, sigma)
```

**Dove si trova**: salari, prezzi immobiliari, capitalizzazione di mercato, durata di sessioni web, dimensioni file.

#### Exponential

```python
# Exponenziale: tempo tra eventi in un processo di Poisson
data_exp = stats.expon.rvs(scale=1/0.5, size=10000, random_state=42)
# scale = 1/lambda, dove lambda e' il rate
```

**Dove si trova**: tempo tra richieste a un server, tempo tra failures hardware, decadimento radioattivo, inter-arrival times.

#### Poisson

```python
# Poisson: conteggio di eventi in un intervallo fisso
data_poisson = stats.poisson.rvs(mu=5, size=10000, random_state=42)
# mu = rate medio di eventi per intervallo
```

**Dove si trova**: numero di email al giorno, errori per pagina di codice, richieste al secondo, difetti per unita'.

#### Binomial

```python
# Binomiale: numero di successi in n prove
data_binom = stats.binom.rvs(n=20, p=0.3, size=10000, random_state=42)
```

**Dove si trova**: conversion rate (k conversioni su n visite), defect rate, pass/fail testing.

#### Power-Law

```python
# Power-Law (Pareto): pochi valori molto grandi, molti piccoli
# P(X > x) ~ x^(-alpha)
data_pareto = stats.pareto.rvs(b=2.5, size=10000, random_state=42)

# Verifica power-law con log-log plot
# Se lineare in log-log, e' power-law
import matplotlib.pyplot as plt
sorted_data = np.sort(data_pareto)[::-1]
ranks = np.arange(1, len(sorted_data) + 1)
plt.loglog(ranks, sorted_data, '.', alpha=0.3)
plt.xlabel("Rank")
plt.ylabel("Value")
plt.title("Log-Log Plot (Power-Law Check)")
```

**Dove si trova**: follower counts sui social, page views, dimensioni citta', frequenza parole, severity incidenti di sicurezza.

#### Uniform

```python
data_uniform = stats.uniform.rvs(loc=0, scale=10, size=10000, random_state=42)
```

**Dove si trova**: generatori di numeri casuali, IDs hash-based, angoli randomici, artefatto di binning eccessivo.

#### Multimodal

Distribuzioni con piu' picchi indicano sottopopolazioni nel dataset.

```python
# Mixture di due normali
data_bimodal = np.concatenate([
    stats.norm.rvs(loc=30, scale=5, size=5000, random_state=42),
    stats.norm.rvs(loc=60, scale=8, size=5000, random_state=43)
])
```

**Dove si trova**: dati con segmenti distinti (utenti free vs premium), dati temporali con stagionalita', misure da strumenti diversi.

### 3.2 Distribution Fitting

```python
from scipy import stats

data = df['response_time'].dropna().values

# Fit di multiple distribuzioni
distributions = [stats.norm, stats.lognorm, stats.expon, stats.gamma, stats.weibull_min]
results = []

for dist in distributions:
    try:
        params = dist.fit(data)
        # Kolmogorov-Smirnov test
        ks_stat, ks_pval = stats.kstest(data, dist.cdf, args=params)
        # AIC approssimato (log-likelihood)
        log_lik = np.sum(dist.logpdf(data, *params))
        k = len(params)
        aic = 2 * k - 2 * log_lik
        results.append({
            'distribution': dist.name,
            'params': params,
            'ks_stat': ks_stat,
            'ks_pval': ks_pval,
            'aic': aic
        })
    except Exception:
        continue

results_df = pd.DataFrame(results).sort_values('aic')
print(results_df[['distribution', 'ks_stat', 'ks_pval', 'aic']])
```

#### Kernel Density Estimation (KDE)

```python
from scipy.stats import gaussian_kde

data = df['revenue'].dropna().values
kde = gaussian_kde(data, bw_method='silverman')

x_range = np.linspace(data.min(), data.max(), 1000)
density = kde(x_range)

# Bandwidth selection
# 'scott': bw = n^(-1/(d+4)) * sigma
# 'silverman': bw = (n*(d+2)/4)^(-1/(d+4)) * sigma
# Numerico: valore fisso
```

### 3.3 QQ-Plots

```python
import scipy.stats as stats
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# QQ-plot contro distribuzione normale
stats.probplot(df['revenue'].dropna(), dist="norm", plot=axes[0])
axes[0].set_title("QQ-Plot vs Normal")

# QQ-plot contro distribuzione log-normale
stats.probplot(np.log1p(df['revenue'].dropna()), dist="norm", plot=axes[1])
axes[1].set_title("QQ-Plot of log(revenue) vs Normal")

plt.tight_layout()
```

Interpretazione del QQ-plot:
- Punti sulla diagonale: dati seguono la distribuzione teorica
- Curva concava verso l'alto: right-skewed (code destre pesanti)
- Curva concava verso il basso: left-skewed
- S-shape: code pesanti (leptokurtic)
- Punti che deviano solo agli estremi: distribuzione simile ma con outlier

### 3.4 Goodness-of-Fit Tests

```python
from scipy import stats

data = df['revenue'].dropna().values

# Shapiro-Wilk (migliore per n < 5000)
# H0: i dati provengono da una distribuzione normale
if len(data) <= 5000:
    stat, p_value = stats.shapiro(data)
    print(f"Shapiro-Wilk: stat={stat:.4f}, p={p_value:.6f}")

# Anderson-Darling (piu' sensibile nelle code)
result = stats.anderson(data, dist='norm')
print(f"Anderson-Darling: stat={result.statistic:.4f}")
for sl, cv in zip(result.significance_level, result.critical_values):
    status = "REJECT" if result.statistic > cv else "ACCEPT"
    print(f"  {sl}%: critical={cv:.4f} -> {status}")

# Kolmogorov-Smirnov (distribuzione arbitraria)
# Test contro una normale con parametri stimati dai dati
fitted_params = stats.norm.fit(data)
ks_stat, ks_pval = stats.kstest(data, 'norm', args=fitted_params)
print(f"KS test: stat={ks_stat:.4f}, p={ks_pval:.6f}")

# D'Agostino-Pearson (basato su skewness + kurtosis)
stat, p_value = stats.normaltest(data)
print(f"D'Agostino-Pearson: stat={stat:.4f}, p={p_value:.6f}")
```

**Caveat importante**: con dataset grandi (n > 10000), praticamente qualsiasi test di normalita' rigetta H0. La domanda non e' "e' perfettamente normale?" ma "e' abbastanza normale per il mio uso?". Usare QQ-plot + skewness/kurtosis per valutazioni pratiche.

---

## 4. Visualization for EDA

### 4.1 Histogram and KDE

```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Histogram base
axes[0].hist(df['revenue'].dropna(), bins=50, edgecolor='black', alpha=0.7)
axes[0].set_title("Histogram")
axes[0].set_xlabel("Revenue")

# KDE overlay
sns.histplot(df['revenue'].dropna(), kde=True, bins=50, ax=axes[1])
axes[1].set_title("Histogram + KDE")

# Solo KDE con bandwidth diversi
for bw in [0.5, 1.0, 2.0]:
    sns.kdeplot(df['revenue'].dropna(), bw_adjust=bw, ax=axes[2], label=f"bw={bw}")
axes[2].set_title("KDE — Bandwidth Comparison")
axes[2].legend()

plt.tight_layout()
```

**Scelta del numero di bins**: Sturges (`k = 1 + log2(n)`), Freedman-Diaconis (`bin_width = 2 * IQR * n^(-1/3)`), o Scott (`bin_width = 3.5 * std * n^(-1/3)`).

### 4.2 Boxplot and Violin Plot

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Boxplot per gruppo
sns.boxplot(x='category', y='revenue', data=df, ax=axes[0])
axes[0].set_title("Revenue by Category (Boxplot)")
axes[0].tick_params(axis='x', rotation=45)

# Violin plot (boxplot + KDE)
sns.violinplot(x='category', y='revenue', data=df, ax=axes[1], inner='quartile')
axes[1].set_title("Revenue by Category (Violin)")
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
```

Il boxplot mostra i 5-number summary + outlier. Il violin plot aggiunge la forma della distribuzione. Preferire violin quando la distribuzione e' bimodale o asimmetrica — il boxplot nasconde questa informazione.

### 4.3 Scatter Plot and Pair Plot

```python
# Scatter plot singolo con regression line
fig, ax = plt.subplots(figsize=(8, 6))
sns.regplot(x='feature_a', y='target', data=df, scatter_kws={'alpha': 0.3}, ax=ax)
ax.set_title("Feature A vs Target")

# Pair plot (matrice di scatter plots)
numeric_cols = df.select_dtypes(include=np.number).columns[:6]  # Max 6 per leggibilita'
sns.pairplot(df[numeric_cols], diag_kind='kde', plot_kws={'alpha': 0.3})
plt.suptitle("Pair Plot", y=1.02)

# Pair plot con hue per gruppo
sns.pairplot(df[list(numeric_cols) + ['category']], hue='category', diag_kind='kde')
```

### 4.4 Heatmaps (Correlation Matrices)

```python
import seaborn as sns
import matplotlib.pyplot as plt

# Matrice di correlazione
corr_matrix = df.select_dtypes(include=np.number).corr()

# Heatmap con annotazioni
fig, ax = plt.subplots(figsize=(12, 10))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # Triangolo superiore
sns.heatmap(
    corr_matrix,
    mask=mask,
    annot=True,
    fmt=".2f",
    cmap="RdBu_r",
    center=0,
    vmin=-1,
    vmax=1,
    square=True,
    linewidths=0.5,
    ax=ax
)
ax.set_title("Correlation Matrix")
plt.tight_layout()

# Clustermap (heatmap con clustering gerarchico)
sns.clustermap(
    corr_matrix,
    method='ward',
    cmap='RdBu_r',
    center=0,
    figsize=(12, 12),
    annot=True,
    fmt=".2f"
)
```

### 4.5 Bar Charts (Categorical Data)

```python
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Conteggi
sns.countplot(x='category', data=df, order=df['category'].value_counts().index, ax=axes[0])
axes[0].set_title("Category Counts")
axes[0].tick_params(axis='x', rotation=45)

# Media per gruppo con CI
sns.barplot(x='category', y='revenue', data=df, ci=95, ax=axes[1])
axes[1].set_title("Mean Revenue by Category (95% CI)")
axes[1].tick_params(axis='x', rotation=45)

# Stacked / grouped
df_pivot = df.groupby(['category', 'region'])['revenue'].mean().unstack()
df_pivot.plot(kind='bar', stacked=True, ax=axes[2])
axes[2].set_title("Revenue by Category and Region")
axes[2].tick_params(axis='x', rotation=45)

plt.tight_layout()
```

### 4.6 Time Series Plots

```python
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# Serie temporale base
df_ts = df.set_index('timestamp').sort_index()
axes[0].plot(df_ts.index, df_ts['metric'], linewidth=0.8)
axes[0].set_title("Raw Time Series")

# Con rolling mean e banda
rolling_mean = df_ts['metric'].rolling(window=7).mean()
rolling_std = df_ts['metric'].rolling(window=7).std()
axes[1].plot(df_ts.index, df_ts['metric'], alpha=0.3, label='Raw')
axes[1].plot(df_ts.index, rolling_mean, color='red', label='7-day MA')
axes[1].fill_between(
    df_ts.index,
    rolling_mean - 2*rolling_std,
    rolling_mean + 2*rolling_std,
    alpha=0.1, color='red'
)
axes[1].set_title("Rolling Mean + 2-Sigma Band")
axes[1].legend()

# Decomposizione stagionale
from statsmodels.tsa.seasonal import seasonal_decompose
decomposition = seasonal_decompose(df_ts['metric'].dropna(), period=7)
decomposition.plot(ax=axes[2])  # Nota: questo crea subplot interni

plt.tight_layout()
```

### 4.7 Geographic Plots

```python
import plotly.express as px

# Mappa coropletica
fig = px.choropleth(
    df_geo,
    locations='country_code',
    color='metric',
    hover_name='country',
    color_continuous_scale='Viridis',
    title="Metric by Country"
)
fig.show()

# Scatter map con coordinate
fig = px.scatter_mapbox(
    df_geo,
    lat='latitude',
    lon='longitude',
    size='magnitude',
    color='category',
    hover_data=['name', 'value'],
    mapbox_style='carto-positron',
    zoom=3,
    title="Events Geographic Distribution"
)
fig.show()
```

### 4.8 Tools Comparison

| Tool | Strengths | Weaknesses | Best For |
|------|-----------|------------|----------|
| **matplotlib** | Totale controllo, standard | Verboso, styling di default brutto | Pubblicazioni, customizzazione estrema |
| **seaborn** | Statistico, bello di default | Meno flessibile per custom | EDA rapida, grafici statistici |
| **plotly** | Interattivo, web-ready | Pesante, rendering lento per molti punti | Dashboard, presentazioni, geo |
| **Altair** | Dichiarativo, grammar of graphics | Limite 5000 punti (default) | Esplorazione rapida, prototipazione |

```python
# Altair example — dichiarativo
import altair as alt

chart = alt.Chart(df).mark_point().encode(
    x='feature_a:Q',
    y='revenue:Q',
    color='category:N',
    size='weight:Q',
    tooltip=['name', 'revenue', 'category']
).interactive()

chart.display()
```

### 4.9 Choosing the Right Chart

| Domanda | Chart Consigliato |
|---------|-------------------|
| Com'e' distribuita una variabile? | Histogram, KDE, boxplot |
| Relazione tra due numeriche? | Scatter plot, hexbin (se tanti punti) |
| Confronto tra gruppi? | Boxplot, violin, bar con CI |
| Trend nel tempo? | Line plot, area chart |
| Composizione? | Stacked bar, treemap |
| Correlazioni multiple? | Heatmap, pair plot |
| Distribuzione geografica? | Choropleth, scatter map |
| Proporzioni? | Pie (con cautela), waffle chart |
| Flussi? | Sankey, alluvial |
| Gerarchie? | Treemap, sunburst |

---

## 5. Correlation and Relationships

### 5.1 Pearson Correlation

Misura la relazione **lineare** tra due variabili continue. Range: [-1, 1].

```python
# Matrice completa
pearson_corr = df.select_dtypes(include=np.number).corr(method='pearson')

# Singola coppia con p-value
from scipy.stats import pearsonr
r, p_value = pearsonr(df['feature_a'].dropna(), df['feature_b'].dropna())
print(f"Pearson r = {r:.4f}, p-value = {p_value:.6f}")
```

**Assunzioni**: linearita', variabili continue, assenza di outlier estremi, distribuzione approssimativamente normale. Violazione comune: relazioni non lineari (Pearson = 0 non implica indipendenza).

### 5.2 Spearman Correlation

Misura la relazione **monotona** (non necessariamente lineare). Basata sui ranghi, non sui valori.

```python
from scipy.stats import spearmanr

rho, p_value = spearmanr(df['feature_a'].dropna(), df['feature_b'].dropna())
print(f"Spearman rho = {rho:.4f}, p-value = {p_value:.6f}")

# Matrice Spearman
spearman_corr = df.select_dtypes(include=np.number).corr(method='spearman')
```

**Quando usare Spearman**: dati ordinali, distribuzioni non normali, relazioni monotone non lineari, presenza di outlier (Spearman e' robusto).

### 5.3 Kendall Tau

```python
from scipy.stats import kendalltau

tau, p_value = kendalltau(df['feature_a'].dropna(), df['feature_b'].dropna())
print(f"Kendall tau = {tau:.4f}, p-value = {p_value:.6f}")
```

Kendall tau e' piu' robusto di Spearman per campioni piccoli e ha migliori proprieta' statistiche (varianza piu' bassa). Computazionalmente O(n^2) vs O(n log n) per Spearman.

### 5.4 Point-Biserial Correlation

Per relazioni tra una variabile binaria e una continua.

```python
from scipy.stats import pointbiserialr

# binary_var deve essere 0/1
r_pb, p_value = pointbiserialr(df['is_premium'].values, df['revenue'].values)
print(f"Point-biserial r = {r_pb:.4f}, p-value = {p_value:.6f}")
```

Matematicamente equivalente a Pearson tra una variabile binaria e una continua, ma l'interpretazione e' diversa.

### 5.5 Chi-Squared Test for Categorical Variables

```python
from scipy.stats import chi2_contingency

# Contingency table
contingency = pd.crosstab(df['category'], df['outcome'])
print(contingency)

# Chi-squared test
chi2, p_value, dof, expected = chi2_contingency(contingency)
print(f"Chi2 = {chi2:.4f}, p-value = {p_value:.6f}, dof = {dof}")

# Cramér's V (effect size per chi-squared)
n = contingency.sum().sum()
min_dim = min(contingency.shape) - 1
cramers_v = np.sqrt(chi2 / (n * min_dim))
print(f"Cramér's V = {cramers_v:.4f}")
# V ~ 0.1: weak, V ~ 0.3: moderate, V ~ 0.5: strong
```

### 5.6 Mutual Information

Cattura relazioni non lineari e non monotone. Non assume nessuna forma funzionale.

```python
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif

# Per target continuo
mi_scores = mutual_info_regression(
    df[feature_cols].fillna(0),
    df['target'],
    random_state=42,
    n_neighbors=5
)
mi_df = pd.DataFrame({
    'feature': feature_cols,
    'mutual_info': mi_scores
}).sort_values('mutual_info', ascending=False)
print(mi_df)

# Per target categorico
mi_scores_class = mutual_info_classif(
    df[feature_cols].fillna(0),
    df['target_class'],
    random_state=42
)
```

Mutual information e' sempre >= 0. MI = 0 implica indipendenza (al contrario di Pearson = 0 che implica solo assenza di relazione lineare).

### 5.7 Partial Correlation

Correlazione tra X e Y controllando per Z (rimuovendo l'effetto confondente di Z).

```python
import pingouin as pg

# Correlazione parziale
partial_corr = pg.partial_corr(
    data=df,
    x='feature_a',
    y='target',
    covar=['confounder_1', 'confounder_2']
)
print(partial_corr)

# Matrice di correlazioni parziali (manuale)
from numpy.linalg import inv

corr = df[numeric_cols].corr().values
precision = inv(corr)  # Matrice di precisione
d = np.diag(1.0 / np.sqrt(np.diag(precision)))
partial_corr_matrix = -d @ precision @ d
np.fill_diagonal(partial_corr_matrix, 1.0)

partial_corr_df = pd.DataFrame(
    partial_corr_matrix,
    index=numeric_cols,
    columns=numeric_cols
)
```

### 5.8 Multicollinearity Detection (VIF)

Variance Inflation Factor misura quanto la varianza di un coefficiente di regressione e' inflazionata a causa della collinearita'.

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Calcolo VIF per ogni feature
X = df[feature_cols].dropna()
vif_data = pd.DataFrame({
    'feature': X.columns,
    'VIF': [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
})
vif_data = vif_data.sort_values('VIF', ascending=False)
print(vif_data)

# Interpretazione:
# VIF = 1: nessuna collinearita'
# VIF 1-5: moderata (generalmente accettabile)
# VIF 5-10: alta (potenziale problema)
# VIF > 10: severa (azione richiesta: rimuovere o combinare feature)
```

### 5.9 Correlation vs Causation

Correlazione non implica causalita'. Fonti comuni di correlazione spuria:

1. **Confounding**: Z causa sia X che Y. Esempio: gelati venduti e annegamenti sono correlati perche' entrambi causati dal caldo.

2. **Reverse causality**: Y causa X, non il contrario.

3. **Selection bias**: il campione non e' rappresentativo.

4. **Coincidence/Multiple testing**: con abbastanza variabili, alcune coppie saranno correlate per caso.

Per stabilire causalita' servono: esperimenti randomizzati (A/B test), natural experiments, o framework causali (DAGs, do-calculus, instrumental variables).

```python
# Esempio: Bonferroni correction per multiple testing
from scipy.stats import pearsonr
import itertools

n_features = len(feature_cols)
n_tests = n_features * (n_features - 1) // 2
alpha = 0.05
alpha_corrected = alpha / n_tests  # Bonferroni

significant_pairs = []
for col1, col2 in itertools.combinations(feature_cols, 2):
    r, p = pearsonr(df[col1].dropna(), df[col2].dropna())
    if p < alpha_corrected:
        significant_pairs.append((col1, col2, r, p))

print(f"Significant correlations (Bonferroni alpha={alpha_corrected:.6f}):")
for col1, col2, r, p in sorted(significant_pairs, key=lambda x: abs(x[2]), reverse=True):
    print(f"  {col1} <-> {col2}: r={r:.4f}, p={p:.2e}")
```

---

## 6. Missing Data Analysis

### 6.1 Missing Data Mechanisms

Comprendere il *meccanismo* di missingness e' cruciale per scegliere la strategia corretta.

**MCAR (Missing Completely At Random)**: la probabilita' di missing non dipende da nessuna variabile (ne' osservata ne' non osservata). Esempio: un sensore che si spegne casualmente. Test: Little's MCAR test.

**MAR (Missing At Random)**: la probabilita' di missing dipende da variabili osservate, ma non dal valore mancante stesso. Esempio: persone con reddito alto sono meno propense a dichiarare il reddito, ma possiamo predirlo dal livello di istruzione.

**MNAR (Missing Not At Random)**: la probabilita' di missing dipende dal valore mancante stesso. Esempio: persone con depressione severa sono meno propense a compilare questionari sulla depressione. Questo e' il caso piu' difficile.

```python
# Test informale per MCAR: i dati con missing sono diversi dai completi?
def test_mcar_informal(df, target_col, other_cols):
    """Confronta distribuzioni tra righe con/senza missing nel target."""
    mask_missing = df[target_col].isnull()
    results = []
    for col in other_cols:
        if df[col].dtype in [np.float64, np.int64]:
            from scipy.stats import mannwhitneyu
            group_present = df.loc[~mask_missing, col].dropna()
            group_missing = df.loc[mask_missing, col].dropna()
            if len(group_present) > 0 and len(group_missing) > 0:
                stat, p = mannwhitneyu(group_present, group_missing)
                results.append({'column': col, 'stat': stat, 'p_value': p})
    return pd.DataFrame(results).sort_values('p_value')
```

### 6.2 Missingness Patterns

```python
import missingno as msno
import matplotlib.pyplot as plt

# Matrix plot (bianca = missing)
msno.matrix(df, figsize=(12, 6), sparkline=True)
plt.title("Missing Data Pattern Matrix")
plt.tight_layout()

# Bar chart (completezza per colonna)
msno.bar(df, figsize=(12, 4))

# Heatmap (correlazione tra missingness di coppie di colonne)
# Valori alti: tendono a mancare insieme
msno.heatmap(df, figsize=(10, 8))

# Dendrogram (clustering delle colonne per pattern di missingness)
msno.dendrogram(df, figsize=(12, 6))
```

```python
# Analisi programmatica dei pattern
missing_summary = pd.DataFrame({
    'column': df.columns,
    'missing_count': df.isnull().sum().values,
    'missing_pct': (df.isnull().mean() * 100).values,
    'dtype': df.dtypes.values
}).sort_values('missing_pct', ascending=False)

print(missing_summary[missing_summary['missing_pct'] > 0])

# Pattern di co-occorrenza
missing_indicator = df.isnull().astype(int)
missing_corr = missing_indicator.corr()
# Alta correlazione = colonne che mancano insieme (stesso record source?)
```

### 6.3 Impact Assessment

```python
# Quanto impatta il missing sulla distribuzione?
def assess_missing_impact(df, col):
    """Valuta se rimuovere i missing cambia significativamente la distribuzione."""
    complete_data = df[col].dropna()
    n_missing = df[col].isnull().sum()
    n_total = len(df)
    pct_missing = n_missing / n_total * 100
    
    print(f"Column: {col}")
    print(f"Missing: {n_missing}/{n_total} ({pct_missing:.1f}%)")
    print(f"Stats (complete cases only):")
    print(f"  Mean: {complete_data.mean():.4f}")
    print(f"  Median: {complete_data.median():.4f}")
    print(f"  Std: {complete_data.std():.4f}")
    
    # Se missing > 5%, investigare il pattern
    if pct_missing > 5:
        print(f"  WARNING: High missingness. Investigate mechanism.")
    # Se missing > 50%, considerare di eliminare la colonna
    if pct_missing > 50:
        print(f"  CRITICAL: Consider dropping this column.")
    
    return pct_missing
```

### 6.4 Imputation Strategies

#### Simple Imputation

```python
from sklearn.impute import SimpleImputer

# Mean imputation (per normali)
imputer_mean = SimpleImputer(strategy='mean')
df['col_imputed'] = imputer_mean.fit_transform(df[['col']])

# Median imputation (per skewed)
imputer_median = SimpleImputer(strategy='median')

# Mode imputation (per categoriche)
imputer_mode = SimpleImputer(strategy='most_frequent')

# Constant imputation
imputer_const = SimpleImputer(strategy='constant', fill_value=-999)
```

**Limitazioni**: la mean/median imputation riduce la varianza, distorce correlazioni, sottostima l'incertezza.

#### KNN Imputation

```python
from sklearn.impute import KNNImputer

# Imputa basandosi sui k vicini piu' simili
imputer_knn = KNNImputer(n_neighbors=5, weights='distance', metric='nan_euclidean')
df_imputed = pd.DataFrame(
    imputer_knn.fit_transform(df[numeric_cols]),
    columns=numeric_cols,
    index=df.index
)
```

#### MICE (Multiple Imputation by Chained Equations)

```python
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor

# Iterative imputation (MICE-like)
imputer_mice = IterativeImputer(
    estimator=RandomForestRegressor(n_estimators=50, random_state=42),
    max_iter=10,
    random_state=42,
    verbose=0
)
df_imputed = pd.DataFrame(
    imputer_mice.fit_transform(df[numeric_cols]),
    columns=numeric_cols,
    index=df.index
)
```

#### Multiple Imputation (per quantificare l'incertezza)

```python
# Creare multiple versioni imputate per catturare l'incertezza
n_imputations = 5
imputed_datasets = []

for i in range(n_imputations):
    imputer = IterativeImputer(
        random_state=i,
        max_iter=10,
        sample_posterior=True  # Aggiunge variabilita' stocastica
    )
    imputed = pd.DataFrame(
        imputer.fit_transform(df[numeric_cols]),
        columns=numeric_cols
    )
    imputed_datasets.append(imputed)

# Rubin's rules per combinare le stime
estimates = [d['target'].mean() for d in imputed_datasets]
within_var = [d['target'].var() / len(d) for d in imputed_datasets]

combined_estimate = np.mean(estimates)
within_variance = np.mean(within_var)
between_variance = np.var(estimates, ddof=1)
total_variance = within_variance + (1 + 1/n_imputations) * between_variance

print(f"Combined estimate: {combined_estimate:.4f}")
print(f"Total SE: {np.sqrt(total_variance):.4f}")
```

### 6.5 When to Drop vs Impute

| Scenario | Azione |
|----------|--------|
| Missing > 80% | Eliminare la colonna |
| Missing < 5%, MCAR | Listwise deletion (rimuovere righe) o simple imputation |
| Missing 5-30%, MAR | KNN/MICE imputation |
| Missing 5-30%, MNAR | Model-based imputation con cautela, sensitivity analysis |
| Poche righe con molte colonne mancanti | Eliminare quelle righe |
| Feature categorica con missing | Trattare "missing" come categoria a se' |
| Time series | Forward-fill, interpolazione, o modello specifico |

---

## 7. Outlier Detection

### 7.1 Statistical Methods

#### Z-Score

```python
from scipy import stats

z_scores = np.abs(stats.zscore(df['revenue'].dropna()))
outliers_zscore = df.loc[df['revenue'].notna()][z_scores > 3]
print(f"Outlier Z-score (|z| > 3): {len(outliers_zscore)} ({len(outliers_zscore)/len(df)*100:.2f}%)")
```

**Limitazione**: lo Z-score assume normalita'. Se la distribuzione e' skewed, lo Z-score classifica male (troppi falsi positivi da un lato, troppi falsi negativi dall'altro).

#### Modified Z-Score (Iglewicz & Hoaglin)

```python
def modified_z_score(data):
    """Usa la mediana e MAD invece di mean e std."""
    median = np.median(data)
    mad = np.median(np.abs(data - median))
    # 0.6745 e' il 75th percentile della normale standard
    modified_z = 0.6745 * (data - median) / mad
    return modified_z

data = df['revenue'].dropna().values
mod_z = modified_z_score(data)
outliers_modz = np.abs(mod_z) > 3.5  # Threshold consigliato: 3.5
print(f"Outlier Modified Z-score: {outliers_modz.sum()}")
```

Il modified Z-score e' robusto: non viene influenzato dagli outlier stessi (a differenza dello Z-score classico che usa mean e std).

#### IQR Rule (Tukey's Fences)

```python
def iqr_outliers(series, factor=1.5):
    """Identifica outlier usando la regola IQR."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - factor * IQR
    upper = Q3 + factor * IQR
    mask = (series < lower) | (series > upper)
    return mask, lower, upper

mask, lower, upper = iqr_outliers(df['revenue'])
print(f"IQR bounds: [{lower:.2f}, {upper:.2f}]")
print(f"Outliers: {mask.sum()} ({mask.mean()*100:.2f}%)")

# factor=3.0 per "far outliers" (extreme)
mask_extreme, _, _ = iqr_outliers(df['revenue'], factor=3.0)
print(f"Extreme outliers: {mask_extreme.sum()}")
```

### 7.2 Distance-Based Methods

#### Mahalanobis Distance

```python
from scipy.spatial.distance import mahalanobis
from numpy.linalg import inv

def mahalanobis_outliers(df, cols, threshold=None):
    """Outlier detection multivariato con distanza di Mahalanobis."""
    data = df[cols].dropna()
    mean = data.mean().values
    cov = data.cov().values
    cov_inv = inv(cov)
    
    distances = data.apply(
        lambda row: mahalanobis(row.values, mean, cov_inv), axis=1
    )
    
    if threshold is None:
        # Chi-squared threshold al 97.5%
        from scipy.stats import chi2
        threshold = np.sqrt(chi2.ppf(0.975, df=len(cols)))
    
    return distances, distances > threshold

distances, outlier_mask = mahalanobis_outliers(df, ['feature_a', 'feature_b', 'feature_c'])
print(f"Mahalanobis outliers: {outlier_mask.sum()}")
```

Mahalanobis cattura outlier multivariati — punti che non sono estremi in nessuna singola dimensione ma sono anomali nella combinazione.

#### Local Outlier Factor (LOF)

```python
from sklearn.neighbors import LocalOutlierFactor

lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
outlier_labels = lof.fit_predict(df[feature_cols].fillna(0))
# -1 = outlier, 1 = inlier

lof_scores = -lof.negative_outlier_factor_  # Piu' alto = piu' anomalo
df['lof_score'] = lof_scores
df['is_outlier_lof'] = outlier_labels == -1

print(f"LOF outliers: {(outlier_labels == -1).sum()}")
```

LOF misura la densita' locale: un punto e' outlier se la sua densita' e' significativamente inferiore a quella dei suoi vicini. Funziona bene con cluster di densita' diversa.

#### DBSCAN-Based

```python
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

# Standardizzare prima di DBSCAN
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[feature_cols].fillna(0))

# DBSCAN: punti non assegnati a nessun cluster sono outlier (label = -1)
dbscan = DBSCAN(eps=0.5, min_samples=10)
labels = dbscan.fit_predict(X_scaled)

outliers_dbscan = labels == -1
print(f"DBSCAN noise points (outliers): {outliers_dbscan.sum()}")
```

### 7.3 Model-Based Methods

#### Isolation Forest

```python
from sklearn.ensemble import IsolationForest

iso_forest = IsolationForest(
    n_estimators=200,
    contamination=0.05,  # Expected outlier fraction
    random_state=42,
    n_jobs=-1
)
outlier_pred = iso_forest.fit_predict(df[feature_cols].fillna(0))
anomaly_scores = iso_forest.decision_function(df[feature_cols].fillna(0))

df['isolation_score'] = anomaly_scores
df['is_outlier_iforest'] = outlier_pred == -1

print(f"Isolation Forest outliers: {(outlier_pred == -1).sum()}")
```

Isolation Forest funziona isolando osservazioni: gli outlier richiedono meno split per essere isolati. Scala bene con dimensionalita' alta.

#### One-Class SVM

```python
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[feature_cols].fillna(0))

oc_svm = OneClassSVM(kernel='rbf', gamma='scale', nu=0.05)
outlier_pred = oc_svm.fit_predict(X_scaled)

print(f"One-Class SVM outliers: {(outlier_pred == -1).sum()}")
```

#### Autoencoder-Based

```python
import tensorflow as tf
from tensorflow import keras

# Autoencoder per anomaly detection
# L'idea: allena per ricostruire dati normali.
# Punti con alto errore di ricostruzione sono anomali.

X_train = df[feature_cols].fillna(0).values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)

input_dim = X_scaled.shape[1]
encoding_dim = input_dim // 3

# Build autoencoder
input_layer = keras.Input(shape=(input_dim,))
encoded = keras.layers.Dense(encoding_dim * 2, activation='relu')(input_layer)
encoded = keras.layers.Dense(encoding_dim, activation='relu')(encoded)
decoded = keras.layers.Dense(encoding_dim * 2, activation='relu')(encoded)
decoded = keras.layers.Dense(input_dim, activation='linear')(decoded)

autoencoder = keras.Model(input_layer, decoded)
autoencoder.compile(optimizer='adam', loss='mse')

autoencoder.fit(
    X_scaled, X_scaled,
    epochs=50,
    batch_size=256,
    validation_split=0.1,
    verbose=0
)

# Reconstruction error come anomaly score
reconstructed = autoencoder.predict(X_scaled, verbose=0)
mse_per_sample = np.mean((X_scaled - reconstructed) ** 2, axis=1)

# Threshold: 95th percentile del reconstruction error
threshold = np.percentile(mse_per_sample, 95)
outliers_ae = mse_per_sample > threshold
print(f"Autoencoder outliers: {outliers_ae.sum()}")
```

### 7.4 Domain-Specific Thresholds

Gli approcci statistici/ML sono generici. In pratica, i domain expert definiscono soglie specifiche:

```python
# Esempio: transazioni finanziarie
domain_rules = {
    'transaction_amount': {'min': 0.01, 'max': 1_000_000},
    'transactions_per_hour': {'max': 100},
    'login_attempts': {'max': 10},
    'session_duration_seconds': {'min': 1, 'max': 86400},
    'age': {'min': 0, 'max': 150},
}

def apply_domain_rules(df, rules):
    """Flag violazioni di regole di dominio."""
    violations = pd.DataFrame(index=df.index)
    for col, bounds in rules.items():
        if col in df.columns:
            mask = pd.Series(False, index=df.index)
            if 'min' in bounds:
                mask |= df[col] < bounds['min']
            if 'max' in bounds:
                mask |= df[col] > bounds['max']
            violations[f'{col}_violation'] = mask
    return violations

violations = apply_domain_rules(df, domain_rules)
print(f"Total records with at least one violation: {violations.any(axis=1).sum()}")
```

### 7.5 Outlier Treatment

#### Winsorization

```python
from scipy.stats import mstats

# Clip ai percentili 5 e 95
winsorized = mstats.winsorize(df['revenue'].dropna(), limits=[0.05, 0.05])

# Equivalente manuale
p5 = df['revenue'].quantile(0.05)
p95 = df['revenue'].quantile(0.95)
df['revenue_winsorized'] = df['revenue'].clip(lower=p5, upper=p95)
```

#### Capping (Flooring/Ceiling)

```python
# Cap ai bounds IQR
Q1 = df['revenue'].quantile(0.25)
Q3 = df['revenue'].quantile(0.75)
IQR = Q3 - Q1
df['revenue_capped'] = df['revenue'].clip(
    lower=Q1 - 1.5 * IQR,
    upper=Q3 + 1.5 * IQR
)
```

#### Transformation

```python
# Log transform (per right-skewed, valori positivi)
df['revenue_log'] = np.log1p(df['revenue'])

# Square root
df['revenue_sqrt'] = np.sqrt(df['revenue'].clip(lower=0))

# Box-Cox (trova la trasformazione ottimale)
from scipy.stats import boxcox
transformed, lambda_param = boxcox(df['revenue'][df['revenue'] > 0].dropna())
print(f"Optimal lambda: {lambda_param:.4f}")

# Yeo-Johnson (gestisce anche valori negativi)
from sklearn.preprocessing import PowerTransformer
pt = PowerTransformer(method='yeo-johnson')
df['revenue_yeojohnson'] = pt.fit_transform(df[['revenue']])
```

#### Removal

```python
# Rimuovere solo quando si e' certi che siano errori di misura
# MAI rimuovere outlier "perche' disturbano il modello" senza giustificazione
df_clean = df[~outlier_mask]
print(f"Removed {outlier_mask.sum()} rows ({outlier_mask.mean()*100:.2f}%)")
```

**Decisione framework**:
- Errore di data entry/misura evidente → rimuovere
- Valore legittimo ma raro → winsorize o trasformare
- Valore informativo (fraud, anomaly) → tenere e flaggare
- Incerto → sensitivity analysis (confrontare risultati con e senza)

---

## 8. Automated EDA Tools

### 8.1 ydata-profiling (ex pandas-profiling)

```python
from ydata_profiling import ProfileReport

# Report completo
profile = ProfileReport(
    df,
    title="EDA Report",
    explorative=True,
    correlations={
        "pearson": {"calculate": True},
        "spearman": {"calculate": True},
        "kendall": {"calculate": True},
        "phi_k": {"calculate": True},  # Universal correlation
    },
    missing_diagrams={
        "matrix": True,
        "bar": True,
        "heatmap": True,
    },
    interactions={
        "continuous": True,
    }
)

# Salvare come HTML
profile.to_file("eda_report.html")

# In Jupyter
profile.to_notebook_iframe()

# Report minimale (per dataset grandi)
profile_minimal = ProfileReport(df, minimal=True, title="Quick EDA")
profile_minimal.to_file("quick_report.html")

# Comparazione tra due dataset
from ydata_profiling import compare

profile_train = ProfileReport(df_train, title="Train")
profile_test = ProfileReport(df_test, title="Test")
comparison = compare([profile_train, profile_test])
comparison.to_file("comparison_report.html")
```

**Output include**: tipo di variabile, statistiche descrittive, distribuzioni, correlazioni, missing values, duplicati, alerts per data quality issues.

### 8.2 Sweetviz

```python
import sweetviz as sv

# Report singolo
report = sv.analyze(df, target_feat='target_column')
report.show_html("sweetviz_report.html")

# Comparazione train/test
report_compare = sv.compare(df_train, df_test, target_feat='target_column')
report_compare.show_html("sweetviz_compare.html")

# Comparazione intra-dataset (segmenti)
report_segment = sv.compare_intra(
    df,
    df['category'] == 'premium',
    ['Premium', 'Other'],
    target_feat='revenue'
)
report_segment.show_html("sweetviz_segment.html")
```

Sweetviz e' piu' veloce di ydata-profiling e produce report side-by-side utili per confronti. Meno dettagliato sulle correlazioni.

### 8.3 D-Tale

```python
import dtale

# Lancia un'interfaccia web interattiva
d = dtale.show(df)
d.open_browser()

# In Jupyter
d
```

D-Tale e' un'interfaccia web completa per EDA interattiva: sorting, filtering, charting, correlation analysis, missing values — tutto point-and-click. Utile per esplorazione rapida senza scrivere codice.

### 8.4 Lux

```python
import lux

# Lux si integra con pandas DataFrames
# Suggerisce automaticamente visualizzazioni rilevanti
df  # In Jupyter, mostra widget interattivo con suggerimenti

# Filtrare i suggerimenti
df.intent = ['revenue', 'category']
df  # Mostra grafici focalizzati su revenue per category

# Esportare una visualizzazione
vis = df.exported[0]
vis.to_code()  # Genera il codice Altair equivalente
```

### 8.5 DataPrep

```python
from dataprep.eda import create_report, plot, plot_missing, plot_correlation

# Report completo
create_report(df).save("dataprep_report.html")

# Singole analisi
plot(df, 'revenue')                    # Distribuzione di una colonna
plot(df, 'revenue', 'category')        # Relazione tra due colonne
plot_missing(df)                       # Analisi missing
plot_correlation(df)                   # Correlazioni

# DataPrep e' ottimizzato per performance con dataset grandi
# Usa Dask internamente per parallelismo
```

### 8.6 AutoViz

```python
from autoviz import AutoViz_Class

AV = AutoViz_Class()
df_auto = AV.AutoViz(
    filename="",
    dfte=df,
    depVar="target",
    verbose=1,
    chart_format="html"
)
# Genera automaticamente i grafici piu' informativi
# Sceglie il tipo di grafico in base ai tipi di dato
```

### 8.7 Comparison and Use Cases

| Tool | Speed | Interactivity | Detail | Best For |
|------|-------|---------------|--------|----------|
| **ydata-profiling** | Lento | Report statico | Molto dettagliato | Report formali, data quality audit |
| **sweetviz** | Veloce | Report statico | Buono | Confronti train/test, segmenti |
| **D-Tale** | Veloce | Web UI interattiva | Buono | Esplorazione ad-hoc senza codice |
| **Lux** | Veloce | Widget Jupyter | Suggerimenti | EDA guidata, scoperta rapida |
| **DataPrep** | Veloce | Report interattivo | Buono | Dataset grandi, performance |
| **AutoViz** | Medio | Grafici auto | Basico | Quick-and-dirty overview |

### 8.8 Generating EDA Reports Programmatically

```python
"""Pipeline EDA automatizzata per integrazione in workflow."""
import json
from datetime import datetime
from pathlib import Path
from ydata_profiling import ProfileReport

def automated_eda_pipeline(df, output_dir, dataset_name):
    """Genera report EDA come parte di una pipeline dati."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # 1. Summary JSON (machine-readable)
    summary = {
        "dataset": dataset_name,
        "timestamp": timestamp,
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "missing_pct": df.isnull().mean().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "numeric_stats": df.describe().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_mb": df.memory_usage(deep=True).sum() / 1e6,
    }
    
    with open(output_path / f"{dataset_name}_{timestamp}_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    # 2. HTML report (human-readable)
    profile = ProfileReport(df, minimal=True, title=f"EDA: {dataset_name}")
    profile.to_file(output_path / f"{dataset_name}_{timestamp}_report.html")
    
    # 3. Data quality alerts
    alerts = []
    for col, pct in summary["missing_pct"].items():
        if pct > 0.3:
            alerts.append(f"HIGH_MISSING: {col} ({pct*100:.1f}%)")
    if summary["duplicate_rows"] > 0:
        alerts.append(f"DUPLICATES: {summary['duplicate_rows']} rows")
    
    with open(output_path / f"{dataset_name}_{timestamp}_alerts.txt", "w") as f:
        f.write("\n".join(alerts) if alerts else "No alerts.")
    
    return summary, alerts

# Utilizzo
summary, alerts = automated_eda_pipeline(df, "./eda_output", "customer_transactions")
```

### 8.9 Integration with Jupyter Notebooks

```python
# Template per notebook EDA strutturato

# Cell 1: Setup
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, HTML

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)
%matplotlib inline
"""

# Cell 2: Load data
"""
df = pd.read_csv("data.csv", parse_dates=['timestamp'])
print(f"Dataset: {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"Memory: {df.memory_usage(deep=True).sum()/1e6:.1f} MB")
display(df.head())
"""

# Cell 3: Quick profiling
"""
from ydata_profiling import ProfileReport
ProfileReport(df, minimal=True).to_notebook_iframe()
"""

# Cell 4+: Deep dives (guidati dai findings del profiling)
```

---

## 9. EDA for Security

### 9.1 Log Analysis EDA — Detecting Anomalies in Access Patterns

```python
import pandas as pd
import numpy as np
from datetime import datetime

# Caricare authentication logs
auth_logs = pd.read_csv("auth_logs.csv", parse_dates=['timestamp'])

# Feature engineering per EDA security
auth_logs['hour'] = auth_logs['timestamp'].dt.hour
auth_logs['day_of_week'] = auth_logs['timestamp'].dt.dayofweek
auth_logs['is_weekend'] = auth_logs['day_of_week'].isin([5, 6])
auth_logs['is_business_hours'] = auth_logs['hour'].between(8, 18)

# Pattern di login per utente
user_patterns = auth_logs.groupby('username').agg(
    total_logins=('timestamp', 'count'),
    unique_ips=('source_ip', 'nunique'),
    unique_countries=('geo_country', 'nunique'),
    failed_logins=('status', lambda x: (x == 'failed').sum()),
    success_rate=('status', lambda x: (x == 'success').mean()),
    off_hours_logins=('is_business_hours', lambda x: (~x).sum()),
    weekend_logins=('is_weekend', 'sum'),
    first_seen=('timestamp', 'min'),
    last_seen=('timestamp', 'max'),
).reset_index()

# Calcolare metriche anomale
user_patterns['fail_ratio'] = user_patterns['failed_logins'] / user_patterns['total_logins']
user_patterns['off_hours_ratio'] = user_patterns['off_hours_logins'] / user_patterns['total_logins']
user_patterns['ip_diversity'] = user_patterns['unique_ips'] / user_patterns['total_logins']

# Identificare utenti anomali
print("=== Possible Brute Force (high fail rate) ===")
brute_force = user_patterns[
    (user_patterns['fail_ratio'] > 0.8) & (user_patterns['total_logins'] > 10)
]
print(brute_force[['username', 'total_logins', 'fail_ratio', 'unique_ips']])

print("\n=== Possible Compromised Accounts (unusual geo) ===")
suspicious_geo = user_patterns[user_patterns['unique_countries'] > 3]
print(suspicious_geo[['username', 'unique_countries', 'unique_ips']])

print("\n=== Possible Insider Threat (off-hours activity) ===")
insider = user_patterns[
    (user_patterns['off_hours_ratio'] > 0.5) & (user_patterns['total_logins'] > 20)
]
print(insider[['username', 'off_hours_ratio', 'weekend_logins']])
```

### 9.2 Network Traffic EDA — Identifying Unusual Connections

```python
# Analisi EDA del traffico di rete (NetFlow/Zeek logs)
netflow = pd.read_parquet("netflow_data.parquet")

# Statistiche base del traffico
print("=== Traffic Summary ===")
print(f"Total flows: {len(netflow):,}")
print(f"Unique source IPs: {netflow['src_ip'].nunique():,}")
print(f"Unique dest IPs: {netflow['dst_ip'].nunique():,}")
print(f"Unique dest ports: {netflow['dst_port'].nunique():,}")
print(f"Time range: {netflow['timestamp'].min()} to {netflow['timestamp'].max()}")

# Distribuzione delle porte di destinazione (Power-law expected)
port_counts = netflow['dst_port'].value_counts()
print(f"\nTop 10 destination ports:")
print(port_counts.head(10))

# Porte insolite (rare ma con alto volume)
rare_ports = port_counts[(port_counts.index > 1024) & (port_counts > 100)]
print(f"\nUnusual high-numbered ports with significant traffic:")
print(rare_ports.sort_values(ascending=False).head(20))

# Distribuzione dei bytes trasferiti (cercare esfiltrazione)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Log-scale histogram dei bytes
axes[0].hist(np.log10(netflow['bytes'] + 1), bins=100, edgecolor='black', alpha=0.7)
axes[0].set_xlabel("log10(bytes)")
axes[0].set_title("Flow Size Distribution")

# Bytes per IP sorgente (top talkers)
top_talkers = netflow.groupby('src_ip')['bytes'].sum().nlargest(20)
top_talkers.plot(kind='barh', ax=axes[1])
axes[1].set_title("Top 20 Source IPs by Total Bytes")
axes[1].set_xlabel("Total Bytes")

plt.tight_layout()

# Beaconing detection (connessioni periodiche — C2 indicator)
def detect_beaconing(flows, src_ip, dst_ip):
    """Detecta comunicazioni periodiche (possibile C2)."""
    pair_flows = flows[
        (flows['src_ip'] == src_ip) & (flows['dst_ip'] == dst_ip)
    ].sort_values('timestamp')
    
    if len(pair_flows) < 10:
        return None
    
    # Inter-arrival times
    intervals = pair_flows['timestamp'].diff().dt.total_seconds().dropna()
    
    if len(intervals) < 5:
        return None
    
    # Beaconing: basso coefficiente di variazione degli intervalli
    cv = intervals.std() / intervals.mean() if intervals.mean() > 0 else float('inf')
    
    return {
        'src_ip': src_ip,
        'dst_ip': dst_ip,
        'n_flows': len(pair_flows),
        'mean_interval_s': intervals.mean(),
        'std_interval_s': intervals.std(),
        'cv': cv,
        'is_beaconing': cv < 0.3  # Threshold: CV < 0.3 suggerisce periodicita'
    }

# Analizzare le coppie piu' frequenti
frequent_pairs = netflow.groupby(['src_ip', 'dst_ip']).size().nlargest(100)
beaconing_results = []
for (src, dst), count in frequent_pairs.items():
    result = detect_beaconing(netflow, src, dst)
    if result and result['is_beaconing']:
        beaconing_results.append(result)

if beaconing_results:
    beacon_df = pd.DataFrame(beaconing_results)
    print("\n=== Possible Beaconing (C2) ===")
    print(beacon_df[['src_ip', 'dst_ip', 'n_flows', 'mean_interval_s', 'cv']])
```

### 9.3 Threat Hunting with Statistical Analysis

```python
# EDA per threat hunting: baseline comportamentale e deviazioni

# 1. Costruire baseline per utente/sistema
def build_user_baseline(logs, window_days=30):
    """Costruisce profilo statistico di comportamento normale."""
    baseline = logs.groupby('username').agg(
        avg_daily_logins=('timestamp', lambda x: x.dt.date.nunique()),
        typical_hours=('hour', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else -1),
        hour_std=('hour', 'std'),
        typical_ips=('source_ip', lambda x: set(x.mode().head(3).values)),
        avg_session_duration=('session_duration', 'mean'),
        std_session_duration=('session_duration', 'std'),
    ).reset_index()
    return baseline

# 2. Score deviazioni dalla baseline
def score_anomalies(current_activity, baseline):
    """Calcola anomaly score basato su deviazione dalla baseline."""
    scores = []
    for _, activity in current_activity.iterrows():
        user_base = baseline[baseline['username'] == activity['username']]
        if user_base.empty:
            scores.append({'username': activity['username'], 'score': 10.0, 'reason': 'new_user'})
            continue
        
        user_base = user_base.iloc[0]
        score = 0
        reasons = []
        
        # Login da IP mai visto
        if activity['source_ip'] not in user_base['typical_ips']:
            score += 3
            reasons.append('new_ip')
        
        # Orario insolito (> 2 std dalla media)
        if user_base['hour_std'] > 0:
            hour_z = abs(activity['hour'] - user_base['typical_hours']) / user_base['hour_std']
            if hour_z > 2:
                score += 2
                reasons.append(f'unusual_hour(z={hour_z:.1f})')
        
        # Sessione insolitamente lunga
        if user_base['std_session_duration'] > 0:
            dur_z = (activity['session_duration'] - user_base['avg_session_duration']) / user_base['std_session_duration']
            if dur_z > 3:
                score += 2
                reasons.append(f'long_session(z={dur_z:.1f})')
        
        scores.append({
            'username': activity['username'],
            'score': score,
            'reason': ', '.join(reasons) if reasons else 'normal'
        })
    
    return pd.DataFrame(scores)

# 3. Visualizzare il panorama delle minacce
def threat_landscape_eda(logs):
    """EDA panoramica per SOC analysts."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Heatmap ora x giorno della settimana
    pivot = logs.pivot_table(
        values='event_id', index='hour', columns='day_of_week', aggfunc='count'
    )
    sns.heatmap(pivot, cmap='YlOrRd', ax=axes[0, 0])
    axes[0, 0].set_title("Activity Heatmap (Hour x Day)")
    axes[0, 0].set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    
    # Failed logins nel tempo (rolling)
    failed = logs[logs['status'] == 'failed'].set_index('timestamp')
    failed.resample('1h').size().rolling(24).mean().plot(ax=axes[0, 1])
    axes[0, 1].set_title("Failed Logins (24h Rolling Average)")
    
    # Distribuzione GeoIP (top countries)
    logs['geo_country'].value_counts().head(15).plot(kind='barh', ax=axes[1, 0])
    axes[1, 0].set_title("Login Attempts by Country")
    
    # Distribuzione anomaly scores
    axes[1, 1].hist(logs['anomaly_score'], bins=50, edgecolor='black', alpha=0.7)
    axes[1, 1].axvline(x=5, color='red', linestyle='--', label='Alert threshold')
    axes[1, 1].set_title("Anomaly Score Distribution")
    axes[1, 1].legend()
    
    plt.tight_layout()
```

### 9.4 EDA for SIEM Data

```python
# EDA specifico per dati SIEM (Splunk, Elastic, QRadar export)

def siem_eda(events_df):
    """Analisi esplorativa di eventi SIEM."""
    
    print("=" * 60)
    print("SIEM DATA EXPLORATORY ANALYSIS")
    print("=" * 60)
    
    # Overview
    print(f"\nTotal events: {len(events_df):,}")
    print(f"Time range: {events_df['timestamp'].min()} to {events_df['timestamp'].max()}")
    print(f"Unique sources: {events_df['source'].nunique():,}")
    print(f"Event types: {events_df['event_type'].nunique()}")
    
    # Distribuzione severity
    print("\n--- Severity Distribution ---")
    severity_dist = events_df['severity'].value_counts()
    for sev, count in severity_dist.items():
        pct = count / len(events_df) * 100
        print(f"  {sev}: {count:,} ({pct:.1f}%)")
    
    # Top event types
    print("\n--- Top 10 Event Types ---")
    print(events_df['event_type'].value_counts().head(10))
    
    # Spike detection (eventi che aumentano improvvisamente)
    hourly_counts = events_df.set_index('timestamp').resample('1h').size()
    mean_hourly = hourly_counts.mean()
    std_hourly = hourly_counts.std()
    spikes = hourly_counts[hourly_counts > mean_hourly + 3 * std_hourly]
    
    if not spikes.empty:
        print(f"\n--- ALERT: {len(spikes)} hourly spikes detected (>3 sigma) ---")
        for ts, count in spikes.items():
            z_score = (count - mean_hourly) / std_hourly
            print(f"  {ts}: {count} events (z={z_score:.1f})")
    
    # Correlazione tra event types (co-occorrenza temporale)
    print("\n--- Event Type Co-occurrence (temporal) ---")
    event_pivot = events_df.pivot_table(
        values='event_id',
        index=events_df['timestamp'].dt.floor('1h'),
        columns='event_type',
        aggfunc='count',
        fill_value=0
    )
    # Top correlazioni
    corr = event_pivot.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    corr_pairs = corr.where(mask).stack().sort_values(ascending=False)
    print("Top correlated event type pairs:")
    print(corr_pairs.head(10))
    
    return {
        'spikes': spikes,
        'severity_dist': severity_dist,
        'top_events': events_df['event_type'].value_counts().head(10)
    }
```

### 9.5 Investigating Data Breaches Through Data Patterns

```python
# EDA post-breach: analisi forense dei dati

def breach_investigation_eda(access_logs, file_access_logs, db_query_logs):
    """EDA per investigare una possibile data breach."""
    
    print("=" * 60)
    print("DATA BREACH INVESTIGATION — EDA REPORT")
    print("=" * 60)
    
    # 1. Timeline anomala di accessi
    print("\n[1] Access Timeline Analysis")
    daily_access = access_logs.set_index('timestamp').resample('1D').size()
    
    # Detect il giorno dell'anomalia
    z_scores = (daily_access - daily_access.mean()) / daily_access.std()
    anomaly_days = z_scores[z_scores.abs() > 3]
    if not anomaly_days.empty:
        print(f"  Anomalous days detected:")
        for day, z in anomaly_days.items():
            print(f"    {day.date()}: z-score = {z:.2f}")
    
    # 2. File access patterns (esfiltrazione?)
    print("\n[2] File Access Pattern Analysis")
    file_stats = file_access_logs.groupby('username').agg(
        files_accessed=('file_path', 'nunique'),
        total_bytes_read=('bytes_read', 'sum'),
        sensitive_files=('is_sensitive', 'sum'),
        unique_directories=('directory', 'nunique'),
    )
    
    # Chi ha acceduto a un numero anomalo di file?
    file_z = (file_stats['files_accessed'] - file_stats['files_accessed'].mean()) / file_stats['files_accessed'].std()
    suspicious_users = file_z[file_z > 3]
    if not suspicious_users.empty:
        print(f"  Users with anomalous file access volume:")
        for user, z in suspicious_users.items():
            stats = file_stats.loc[user]
            print(f"    {user}: {int(stats['files_accessed'])} files, "
                  f"{int(stats['sensitive_files'])} sensitive, "
                  f"{stats['total_bytes_read']/1e6:.1f} MB read")
    
    # 3. Database query analysis
    print("\n[3] Database Query Pattern Analysis")
    
    # Query che accedono a tabelle sensibili con SELECT *
    sensitive_queries = db_query_logs[
        (db_query_logs['table'].isin(['users', 'payments', 'credentials'])) &
        (db_query_logs['query_type'] == 'SELECT') &
        (db_query_logs['rows_returned'] > 1000)
    ]
    
    if not sensitive_queries.empty:
        print(f"  Large SELECT queries on sensitive tables: {len(sensitive_queries)}")
        by_user = sensitive_queries.groupby('username').agg(
            query_count=('query_id', 'count'),
            total_rows=('rows_returned', 'sum'),
            tables=('table', lambda x: list(x.unique()))
        )
        print(by_user.sort_values('total_rows', ascending=False))
    
    # 4. Lateral movement indicators
    print("\n[4] Lateral Movement Indicators")
    access_logs['src_dst'] = access_logs['source_host'] + ' -> ' + access_logs['dest_host']
    
    # Host che accedono a molti altri host (fanout anomalo)
    host_fanout = access_logs.groupby('source_host')['dest_host'].nunique()
    fanout_threshold = host_fanout.mean() + 3 * host_fanout.std()
    high_fanout = host_fanout[host_fanout > fanout_threshold]
    
    if not high_fanout.empty:
        print(f"  Hosts with high fanout (>{fanout_threshold:.0f} destinations):")
        for host, n_dest in high_fanout.sort_values(ascending=False).items():
            print(f"    {host}: {n_dest} unique destinations")
    
    # 5. Data volume anomaly (esfiltrazione)
    print("\n[5] Data Volume Anomaly (Exfiltration Check)")
    hourly_bytes = access_logs.set_index('timestamp')['bytes_transferred'].resample('1h').sum()
    bytes_mean = hourly_bytes.mean()
    bytes_std = hourly_bytes.std()
    
    exfil_hours = hourly_bytes[hourly_bytes > bytes_mean + 4 * bytes_std]
    if not exfil_hours.empty:
        print(f"  Hours with anomalous outbound volume:")
        for ts, vol in exfil_hours.items():
            print(f"    {ts}: {vol/1e9:.2f} GB (normal avg: {bytes_mean/1e9:.2f} GB)")

    return {
        'anomaly_days': anomaly_days,
        'suspicious_users': suspicious_users,
        'sensitive_queries': sensitive_queries,
        'high_fanout_hosts': high_fanout,
        'exfil_hours': exfil_hours
    }
```

---

## 10. Lab Exercises

### Lab 1: Complete EDA on a Real-World Dataset (Kaggle)

```python
"""
LAB 1: Exploratory Data Analysis Completa
Dataset: Kaggle "Credit Card Fraud Detection"
URL: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

Obiettivo: EDA completa per comprendere le caratteristiche di transazioni
fraudolente vs legittime.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# === STEP 1: Load and Understand ===

df = pd.read_csv("creditcard.csv")

print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)
print(f"Shape: {df.shape}")
print(f"Memory: {df.memory_usage(deep=True).sum()/1e6:.1f} MB")
print(f"\nClass distribution:")
print(df['Class'].value_counts())
print(f"\nFraud rate: {df['Class'].mean()*100:.4f}%")
print(f"\nBasic stats:")
display(df.describe())

# === STEP 2: Target Variable Analysis ===

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Distribuzione Amount per classe
sns.boxplot(x='Class', y='Amount', data=df, ax=axes[0])
axes[0].set_title("Transaction Amount by Class")
axes[0].set_ylim(0, 500)  # Zoom

# Distribuzione Time
sns.histplot(data=df, x='Time', hue='Class', bins=48, ax=axes[1], stat='density')
axes[1].set_title("Transaction Time Distribution")

# Log Amount
df['Log_Amount'] = np.log1p(df['Amount'])
sns.kdeplot(data=df[df['Class']==0], x='Log_Amount', ax=axes[2], label='Normal')
sns.kdeplot(data=df[df['Class']==1], x='Log_Amount', ax=axes[2], label='Fraud')
axes[2].set_title("Log(Amount) Distribution by Class")
axes[2].legend()

plt.tight_layout()

# === STEP 3: Feature Distributions ===

# PCA components (V1-V28): confronto tra fraud e non-fraud
fig, axes = plt.subplots(4, 7, figsize=(24, 16))
axes = axes.flatten()

for i, col in enumerate([f'V{j}' for j in range(1, 29)]):
    sns.kdeplot(data=df[df['Class']==0], x=col, ax=axes[i], label='Normal', color='blue')
    sns.kdeplot(data=df[df['Class']==1], x=col, ax=axes[i], label='Fraud', color='red')
    axes[i].set_title(col, fontsize=10)
    axes[i].legend(fontsize=6)

plt.tight_layout()

# === STEP 4: Feature Importance via Statistical Tests ===

# KS test per ogni feature: quanto differiscono le distribuzioni?
ks_results = []
for col in [f'V{i}' for i in range(1, 29)] + ['Amount', 'Time']:
    normal_data = df[df['Class'] == 0][col].dropna()
    fraud_data = df[df['Class'] == 1][col].dropna()
    ks_stat, ks_pval = stats.ks_2samp(normal_data, fraud_data)
    ks_results.append({'feature': col, 'ks_stat': ks_stat, 'p_value': ks_pval})

ks_df = pd.DataFrame(ks_results).sort_values('ks_stat', ascending=False)
print("\n=== Feature Separability (KS Test) ===")
print(ks_df.head(10))
# Features con KS alto separano bene fraud da normal

# === STEP 5: Correlation Analysis ===

# Solo per le top features
top_features = ks_df.head(10)['feature'].tolist() + ['Class']
corr_matrix = df[top_features].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r', center=0)
plt.title("Correlation Matrix (Top Discriminative Features)")
plt.tight_layout()

# === STEP 6: Outlier Analysis ===

# Isolation Forest per anomaly detection
from sklearn.ensemble import IsolationForest

feature_cols = [f'V{i}' for i in range(1, 29)] + ['Log_Amount']
iso_forest = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
anomaly_scores = iso_forest.fit_predict(df[feature_cols])

# Quanto overlap c'e' tra anomalie Isolation Forest e fraud reale?
df['iso_anomaly'] = anomaly_scores == -1
confusion = pd.crosstab(df['Class'], df['iso_anomaly'], margins=True)
print("\n=== Isolation Forest vs Actual Fraud ===")
print(confusion)
precision = df[(df['iso_anomaly']) & (df['Class']==1)].shape[0] / df[df['iso_anomaly']].shape[0]
recall = df[(df['iso_anomaly']) & (df['Class']==1)].shape[0] / df[df['Class']==1].shape[0]
print(f"Precision: {precision:.4f}, Recall: {recall:.4f}")

# === STEP 7: Key Findings Summary ===

print("\n" + "=" * 60)
print("KEY FINDINGS")
print("=" * 60)
print("""
1. Dataset estremamente sbilanciato (0.17% fraud)
2. Feature V14, V12, V10 hanno la maggiore separabilita' (KS > 0.5)
3. Amount: frodi tendono ad avere importi piu' bassi (mediana)
4. Distribuzione temporale: frodi distribuite uniformemente (no time preference)
5. Isolation Forest cattura ~60% delle frodi con 1% contamination
6. V1-V28 sono gia' PCA-transformed: correlazioni minime tra di loro
7. No missing values nel dataset
""")
```

### Lab 2: Automated EDA Pipeline with ydata-profiling

```python
"""
LAB 2: Pipeline EDA Automatizzata
Obiettivo: Costruire un pipeline riutilizzabile che genera report
EDA automatici con alerting su data quality issues.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

from ydata_profiling import ProfileReport
from scipy import stats


class EDAAutoPipeline:
    """Pipeline automatizzata per Exploratory Data Analysis."""
    
    def __init__(self, output_dir: str = "./eda_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.alerts = []
        self.summary = {}
    
    def run(self, df: pd.DataFrame, name: str, target_col: str = None):
        """Esegue la pipeline EDA completa."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_id = f"{name}_{timestamp}"
        
        print(f"[EDA] Starting pipeline for: {name}")
        print(f"[EDA] Output: {self.output_dir / run_id}")
        
        # Step 1: Basic profiling
        self._basic_profile(df, name)
        
        # Step 2: Data quality checks
        self._quality_checks(df)
        
        # Step 3: Distribution analysis
        self._distribution_analysis(df)
        
        # Step 4: Correlation analysis
        self._correlation_analysis(df, target_col)
        
        # Step 5: Generate ydata-profiling report
        self._generate_profiling_report(df, run_id, target_col)
        
        # Step 6: Save alerts and summary
        self._save_results(run_id)
        
        print(f"[EDA] Pipeline complete. Alerts: {len(self.alerts)}")
        return self.summary, self.alerts
    
    def _basic_profile(self, df, name):
        """Profilo base del dataset."""
        self.summary = {
            'name': name,
            'rows': len(df),
            'columns': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1e6,
            'numeric_cols': len(df.select_dtypes(include=np.number).columns),
            'categorical_cols': len(df.select_dtypes(include='object').columns),
            'datetime_cols': len(df.select_dtypes(include='datetime64').columns),
            'duplicate_rows': int(df.duplicated().sum()),
            'duplicate_pct': df.duplicated().mean() * 100,
        }
        print(f"  Shape: {self.summary['rows']:,} x {self.summary['columns']}")
        print(f"  Memory: {self.summary['memory_mb']:.1f} MB")
    
    def _quality_checks(self, df):
        """Check di qualita' con alerting."""
        # Missing values
        missing = df.isnull().mean() * 100
        high_missing = missing[missing > 30]
        for col, pct in high_missing.items():
            self.alerts.append({
                'severity': 'HIGH' if pct > 50 else 'MEDIUM',
                'type': 'MISSING_DATA',
                'column': col,
                'detail': f"{pct:.1f}% missing values"
            })
        
        # Constant columns
        nunique = df.nunique()
        constant_cols = nunique[nunique <= 1].index.tolist()
        for col in constant_cols:
            self.alerts.append({
                'severity': 'LOW',
                'type': 'CONSTANT_COLUMN',
                'column': col,
                'detail': f"Only {nunique[col]} unique value(s)"
            })
        
        # High cardinality categoricals
        obj_cols = df.select_dtypes(include='object').columns
        for col in obj_cols:
            if df[col].nunique() > 0.5 * len(df):
                self.alerts.append({
                    'severity': 'MEDIUM',
                    'type': 'HIGH_CARDINALITY',
                    'column': col,
                    'detail': f"{df[col].nunique()} unique values (potential ID column)"
                })
        
        # Duplicates
        if self.summary['duplicate_pct'] > 5:
            self.alerts.append({
                'severity': 'MEDIUM',
                'type': 'DUPLICATES',
                'column': '_all_',
                'detail': f"{self.summary['duplicate_pct']:.1f}% duplicate rows"
            })
        
        self.summary['missing_summary'] = missing[missing > 0].to_dict()
    
    def _distribution_analysis(self, df):
        """Analisi delle distribuzioni con test di normalita'."""
        numeric_cols = df.select_dtypes(include=np.number).columns
        dist_results = {}
        
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) < 8:
                continue
            
            sk = float(stats.skew(data))
            kurt = float(stats.kurtosis(data))
            
            # Test normalita' (solo per campioni ragionevoli)
            if len(data) <= 5000:
                _, shapiro_p = stats.shapiro(data.sample(min(5000, len(data)), random_state=42))
            else:
                _, shapiro_p = stats.normaltest(data.sample(5000, random_state=42))
            
            dist_results[col] = {
                'skewness': sk,
                'kurtosis': kurt,
                'is_normal': shapiro_p > 0.05,
                'suggested_transform': 'log' if sk > 1 else ('sqrt' if sk > 0.5 else 'none')
            }
            
            # Alert per distribuzioni estremamente skewed
            if abs(sk) > 3:
                self.alerts.append({
                    'severity': 'LOW',
                    'type': 'EXTREME_SKEWNESS',
                    'column': col,
                    'detail': f"Skewness = {sk:.2f}. Consider log/power transform."
                })
        
        self.summary['distributions'] = dist_results
    
    def _correlation_analysis(self, df, target_col):
        """Analisi correlazioni con detection multicollinearita'."""
        numeric_df = df.select_dtypes(include=np.number)
        if numeric_df.shape[1] < 2:
            return
        
        corr = numeric_df.corr()
        
        # Coppie altamente correlate (escludendo diagonale)
        high_corr = []
        for i in range(len(corr.columns)):
            for j in range(i+1, len(corr.columns)):
                if abs(corr.iloc[i, j]) > 0.9:
                    high_corr.append({
                        'col1': corr.columns[i],
                        'col2': corr.columns[j],
                        'correlation': float(corr.iloc[i, j])
                    })
        
        if high_corr:
            self.alerts.append({
                'severity': 'MEDIUM',
                'type': 'HIGH_CORRELATION',
                'column': '_multiple_',
                'detail': f"{len(high_corr)} feature pairs with |r| > 0.9"
            })
        
        # Target correlation (se specificato)
        if target_col and target_col in numeric_df.columns:
            target_corr = corr[target_col].drop(target_col).abs().sort_values(ascending=False)
            self.summary['target_correlations'] = target_corr.head(10).to_dict()
        
        self.summary['high_correlations'] = high_corr
    
    def _generate_profiling_report(self, df, run_id, target_col):
        """Genera il report ydata-profiling."""
        print("  Generating profiling report...")
        
        config = {
            'title': f'EDA Report: {run_id}',
            'minimal': len(df) > 100000,  # Minimal per dataset grandi
        }
        
        profile = ProfileReport(df, **config)
        report_path = self.output_dir / f"{run_id}_report.html"
        profile.to_file(report_path)
        print(f"  Report saved: {report_path}")
    
    def _save_results(self, run_id):
        """Salva summary e alerts in JSON."""
        results = {
            'run_id': run_id,
            'timestamp': datetime.utcnow().isoformat(),
            'summary': self.summary,
            'alerts': self.alerts,
            'alert_counts': {
                'HIGH': sum(1 for a in self.alerts if a['severity'] == 'HIGH'),
                'MEDIUM': sum(1 for a in self.alerts if a['severity'] == 'MEDIUM'),
                'LOW': sum(1 for a in self.alerts if a['severity'] == 'LOW'),
            }
        }
        
        results_path = self.output_dir / f"{run_id}_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print alerts
        if self.alerts:
            print(f"\n  === ALERTS ({len(self.alerts)}) ===")
            for alert in sorted(self.alerts, key=lambda x: {'HIGH':0, 'MEDIUM':1, 'LOW':2}[x['severity']]):
                print(f"  [{alert['severity']}] {alert['type']}: {alert['column']} — {alert['detail']}")


# === USAGE ===

# pipeline = EDAAutoPipeline(output_dir="./eda_output")
# df = pd.read_csv("your_dataset.csv")
# summary, alerts = pipeline.run(df, name="customer_transactions", target_col="churn")
```

### Lab 3: Security-Focused EDA on Authentication Logs

```python
"""
LAB 3: Security-Focused EDA su Authentication Logs
Obiettivo: Analizzare log di autenticazione per identificare
pattern sospetti, brute force, credential stuffing, e lateral movement.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import Counter
from datetime import timedelta

# === STEP 1: Generate Synthetic Auth Logs ===
# (In produzione, importare da SIEM/log collector)

np.random.seed(42)
n_normal = 50000
n_attack = 500

def generate_auth_logs():
    """Genera log di autenticazione sintetici realistici."""
    # Normal users
    normal_users = [f"user_{i:04d}" for i in range(200)]
    normal_ips = [f"10.0.{np.random.randint(1,10)}.{np.random.randint(1,254)}" for _ in range(200)]
    
    normal_logs = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n_normal, freq='2min') + 
                     pd.to_timedelta(np.random.randint(0, 3600, n_normal), unit='s'),
        'username': np.random.choice(normal_users, n_normal),
        'source_ip': np.random.choice(normal_ips, n_normal),
        'status': np.random.choice(['success', 'failed'], n_normal, p=[0.95, 0.05]),
        'service': np.random.choice(['ssh', 'web_app', 'vpn', 'email'], n_normal, p=[0.2, 0.4, 0.3, 0.1]),
        'geo_country': np.random.choice(['IT', 'IT', 'IT', 'DE', 'FR'], n_normal, p=[0.7, 0.1, 0.1, 0.05, 0.05]),
    })
    
    # Attack patterns
    # Pattern 1: Brute force (one user, many IPs, many failures)
    brute_force = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-15 02:00', periods=200, freq='3s'),
        'username': 'admin',
        'source_ip': [f"185.{np.random.randint(0,255)}.{np.random.randint(0,255)}.{np.random.randint(0,255)}" for _ in range(200)],
        'status': ['failed'] * 195 + ['success'] * 5,
        'service': 'ssh',
        'geo_country': np.random.choice(['RU', 'CN', 'KP'], 200),
    })
    
    # Pattern 2: Credential stuffing (many users, same IP block)
    cred_stuff = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-20 03:00', periods=300, freq='5s'),
        'username': [f"user_{np.random.randint(0,200):04d}" for _ in range(300)],
        'source_ip': [f"91.234.{np.random.randint(0,5)}.{np.random.randint(1,254)}" for _ in range(300)],
        'status': np.random.choice(['failed', 'success'], 300, p=[0.9, 0.1]),
        'service': 'web_app',
        'geo_country': 'UA',
    })
    
    logs = pd.concat([normal_logs, brute_force, cred_stuff], ignore_index=True)
    logs = logs.sort_values('timestamp').reset_index(drop=True)
    return logs

auth_logs = generate_auth_logs()

# === STEP 2: Temporal Analysis ===

auth_logs['hour'] = auth_logs['timestamp'].dt.hour
auth_logs['day_of_week'] = auth_logs['timestamp'].dt.dayofweek
auth_logs['date'] = auth_logs['timestamp'].dt.date

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Heatmap temporale
pivot_time = auth_logs.pivot_table(values='username', index='hour', columns='day_of_week', aggfunc='count')
sns.heatmap(pivot_time, cmap='YlOrRd', ax=axes[0, 0], annot=False)
axes[0, 0].set_title("Login Activity (Hour x DayOfWeek)")
axes[0, 0].set_xticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])

# Failed vs Success over time
daily_status = auth_logs.groupby(['date', 'status']).size().unstack(fill_value=0)
daily_status.plot(ax=axes[0, 1])
axes[0, 1].set_title("Daily Login Attempts by Status")

# Failure rate rolling
hourly_fail_rate = auth_logs.set_index('timestamp').resample('1h')['status'].apply(
    lambda x: (x == 'failed').mean()
)
axes[1, 0].plot(hourly_fail_rate.index, hourly_fail_rate.values)
axes[1, 0].axhline(y=0.2, color='red', linestyle='--', label='Threshold (20%)')
axes[1, 0].set_title("Hourly Failure Rate")
axes[1, 0].legend()

# GeoIP distribution
geo_counts = auth_logs['geo_country'].value_counts()
geo_counts.plot(kind='bar', ax=axes[1, 1])
axes[1, 1].set_title("Login Attempts by Country")

plt.tight_layout()

# === STEP 3: Brute Force Detection ===

print("=" * 60)
print("BRUTE FORCE DETECTION")
print("=" * 60)

# Sliding window: > 10 failures in 5 minutes from same IP
window = timedelta(minutes=5)
threshold_failures = 10

failed_logs = auth_logs[auth_logs['status'] == 'failed'].copy()
failed_logs = failed_logs.sort_values('timestamp')

# Per-IP failure bursts
ip_failure_counts = failed_logs.groupby('source_ip').agg(
    total_failures=('timestamp', 'count'),
    unique_users_targeted=('username', 'nunique'),
    time_span=('timestamp', lambda x: (x.max() - x.min()).total_seconds()),
    countries=('geo_country', 'first'),
).reset_index()

# Failure rate (failures per second)
ip_failure_counts['failure_rate'] = ip_failure_counts.apply(
    lambda row: row['total_failures'] / max(row['time_span'], 1), axis=1
)

brute_force_ips = ip_failure_counts[
    (ip_failure_counts['total_failures'] > threshold_failures) &
    (ip_failure_counts['failure_rate'] > 0.1)
].sort_values('total_failures', ascending=False)

print(f"\nSuspicious IPs (>{threshold_failures} failures, rate > 0.1/s):")
print(brute_force_ips[['source_ip', 'total_failures', 'failure_rate', 'unique_users_targeted', 'countries']].head(10))

# === STEP 4: Credential Stuffing Detection ===

print("\n" + "=" * 60)
print("CREDENTIAL STUFFING DETECTION")
print("=" * 60)

# Indicatori: molti utenti diversi da stesso IP/subnet, alto failure rate
# Raggruppare per subnet /24
auth_logs['subnet'] = auth_logs['source_ip'].apply(lambda x: '.'.join(x.split('.')[:3]))

subnet_stats = auth_logs.groupby('subnet').agg(
    total_attempts=('timestamp', 'count'),
    unique_users=('username', 'nunique'),
    unique_ips=('source_ip', 'nunique'),
    failure_rate=('status', lambda x: (x == 'failed').mean()),
    time_span_hours=('timestamp', lambda x: (x.max() - x.min()).total_seconds() / 3600),
).reset_index()

# Credential stuffing: molti utenti, alto failure rate, tempo concentrato
cred_stuffing = subnet_stats[
    (subnet_stats['unique_users'] > 20) &
    (subnet_stats['failure_rate'] > 0.5) &
    (subnet_stats['time_span_hours'] < 2)
]

print(f"\nSuspicious subnets (credential stuffing indicators):")
print(cred_stuffing)

# === STEP 5: User Behavior Anomaly Scoring ===

print("\n" + "=" * 60)
print("USER BEHAVIOR ANOMALY SCORING")
print("=" * 60)

user_features = auth_logs.groupby('username').agg(
    total_logins=('timestamp', 'count'),
    unique_ips=('source_ip', 'nunique'),
    unique_countries=('geo_country', 'nunique'),
    failure_rate=('status', lambda x: (x == 'failed').mean()),
    unique_services=('service', 'nunique'),
    off_hours_pct=('hour', lambda x: ((x < 6) | (x > 22)).mean()),
    weekend_pct=('day_of_week', lambda x: (x >= 5).mean()),
).reset_index()

# Anomaly detection con Isolation Forest
feature_cols_user = ['total_logins', 'unique_ips', 'unique_countries',
                     'failure_rate', 'off_hours_pct', 'weekend_pct']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(user_features[feature_cols_user])

iso_forest = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
user_features['anomaly_score'] = -iso_forest.decision_function(X_scaled)
user_features['is_anomalous'] = iso_forest.predict(X_scaled) == -1

print(f"\nAnomalous users detected: {user_features['is_anomalous'].sum()}")
anomalous_users = user_features[user_features['is_anomalous']].sort_values('anomaly_score', ascending=False)
print(anomalous_users[['username', 'total_logins', 'unique_ips', 'unique_countries',
                        'failure_rate', 'off_hours_pct', 'anomaly_score']].head(10))

# === STEP 6: Summary Report ===

print("\n" + "=" * 60)
print("SECURITY EDA SUMMARY")
print("=" * 60)
print(f"""
Total log entries analyzed: {len(auth_logs):,}
Time range: {auth_logs['timestamp'].min()} to {auth_logs['timestamp'].max()}
Unique users: {auth_logs['username'].nunique()}
Unique source IPs: {auth_logs['source_ip'].nunique()}
Overall failure rate: {(auth_logs['status']=='failed').mean()*100:.2f}%

FINDINGS:
- Brute force IPs detected: {len(brute_force_ips)}
- Credential stuffing subnets: {len(cred_stuffing)}
- Anomalous user accounts: {user_features['is_anomalous'].sum()}
- Peak attack window: 02:00-04:00 UTC (off-hours)
- Attack origin countries: RU, CN, UA

RECOMMENDATIONS:
1. Block IPs: {', '.join(brute_force_ips['source_ip'].head(5).tolist())}
2. Rate limit subnet 91.234.0.0/22
3. Enforce MFA for user 'admin' and anomalous accounts
4. Implement geo-blocking for non-business countries
5. Set up automated alerting for failure_rate > 20% per hour
""")
```

### Lab 4: Outlier Detection System for Database Query Patterns

```python
"""
LAB 4: Outlier Detection System per Database Query Patterns
Obiettivo: Costruire un sistema che monitora i pattern di query al database
e identifica query anomale che potrebbero indicare SQL injection,
data exfiltration, o abuso di privilegi.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns


class DatabaseQueryMonitor:
    """Monitor per anomaly detection su query al database."""
    
    def __init__(self, baseline_days: int = 30, alert_threshold: float = 0.05):
        self.baseline_days = baseline_days
        self.alert_threshold = alert_threshold
        self.baseline_stats = None
        self.isolation_forest = None
        self.scaler = StandardScaler()
    
    def build_baseline(self, query_logs: pd.DataFrame):
        """Costruisce il profilo di baseline dal traffico normale."""
        print("[Monitor] Building baseline from query logs...")
        
        # Feature engineering per ogni sessione/utente
        self.baseline_stats = self._compute_features(query_logs)
        
        # Train Isolation Forest
        feature_cols = self._get_feature_cols()
        X = self.baseline_stats[feature_cols].fillna(0)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.isolation_forest = IsolationForest(
            n_estimators=200,
            contamination=self.alert_threshold,
            random_state=42
        )
        self.isolation_forest.fit(X_scaled)
        
        # Compute statistical baselines
        self._compute_stat_baselines(query_logs)
        
        print(f"[Monitor] Baseline built on {len(query_logs):,} queries")
        print(f"[Monitor] Unique users: {query_logs['username'].nunique()}")
        print(f"[Monitor] Unique tables: {query_logs['table_name'].nunique()}")
    
    def analyze(self, current_logs: pd.DataFrame) -> pd.DataFrame:
        """Analizza query correnti contro la baseline."""
        features = self._compute_features(current_logs)
        feature_cols = self._get_feature_cols()
        
        X = features[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # Isolation Forest scoring
        features['anomaly_score'] = -self.isolation_forest.decision_function(X_scaled)
        features['is_anomaly_ml'] = self.isolation_forest.predict(X_scaled) == -1
        
        # Rule-based detection
        features['rule_alerts'] = features.apply(self._apply_rules, axis=1)
        
        # Combined alert
        features['is_alert'] = features['is_anomaly_ml'] | (features['rule_alerts'] != '')
        
        return features
    
    def _compute_features(self, logs: pd.DataFrame) -> pd.DataFrame:
        """Calcola feature aggregate per utente/sessione."""
        features = logs.groupby('username').agg(
            query_count=('query_id', 'count'),
            unique_tables=('table_name', 'nunique'),
            avg_rows_returned=('rows_returned', 'mean'),
            max_rows_returned=('rows_returned', 'max'),
            total_rows_returned=('rows_returned', 'sum'),
            avg_execution_time_ms=('execution_time_ms', 'mean'),
            max_execution_time_ms=('execution_time_ms', 'max'),
            select_count=('query_type', lambda x: (x == 'SELECT').sum()),
            insert_count=('query_type', lambda x: (x == 'INSERT').sum()),
            update_count=('query_type', lambda x: (x == 'UPDATE').sum()),
            delete_count=('query_type', lambda x: (x == 'DELETE').sum()),
            ddl_count=('query_type', lambda x: x.isin(['CREATE', 'DROP', 'ALTER']).sum()),
            sensitive_table_access=('is_sensitive_table', 'sum'),
            distinct_source_ips=('source_ip', 'nunique'),
            off_hours_queries=('is_off_hours', 'sum'),
            error_count=('is_error', 'sum'),
        ).reset_index()
        
        # Derived features
        features['read_write_ratio'] = (
            features['select_count'] / 
            (features['insert_count'] + features['update_count'] + features['delete_count']).clip(lower=1)
        )
        features['error_rate'] = features['error_count'] / features['query_count']
        features['sensitive_access_rate'] = features['sensitive_table_access'] / features['query_count']
        features['off_hours_rate'] = features['off_hours_queries'] / features['query_count']
        
        return features
    
    def _get_feature_cols(self):
        return [
            'query_count', 'unique_tables', 'avg_rows_returned',
            'max_rows_returned', 'total_rows_returned', 'avg_execution_time_ms',
            'select_count', 'delete_count', 'ddl_count',
            'sensitive_table_access', 'distinct_source_ips',
            'off_hours_queries', 'error_rate', 'read_write_ratio',
            'sensitive_access_rate', 'off_hours_rate'
        ]
    
    def _compute_stat_baselines(self, logs):
        """Calcola baseline statistiche per regole deterministiche."""
        self.stat_baselines = {
            'rows_p99': logs['rows_returned'].quantile(0.99),
            'exec_time_p99': logs['execution_time_ms'].quantile(0.99),
            'queries_per_user_mean': logs.groupby('username').size().mean(),
            'queries_per_user_std': logs.groupby('username').size().std(),
            'max_tables_per_user': logs.groupby('username')['table_name'].nunique().quantile(0.95),
        }
    
    def _apply_rules(self, row) -> str:
        """Regole deterministiche per anomaly detection."""
        alerts = []
        
        # Rule 1: Volume anomalo di query
        if hasattr(self, 'stat_baselines'):
            z_queries = (row['query_count'] - self.stat_baselines['queries_per_user_mean']) / \
                        max(self.stat_baselines['queries_per_user_std'], 1)
            if z_queries > 4:
                alerts.append(f"HIGH_VOLUME(z={z_queries:.1f})")
        
        # Rule 2: Accesso a troppe tabelle sensibili
        if row['sensitive_access_rate'] > 0.5 and row['sensitive_table_access'] > 10:
            alerts.append(f"SENSITIVE_ACCESS({int(row['sensitive_table_access'])} queries)")
        
        # Rule 3: DDL da utente non-admin
        if row['ddl_count'] > 0:
            alerts.append(f"DDL_DETECTED({int(row['ddl_count'])} statements)")
        
        # Rule 4: Alto volume di righe estratte (exfiltration)
        if row['total_rows_returned'] > 100000:
            alerts.append(f"HIGH_EXTRACTION({int(row['total_rows_returned'])} rows)")
        
        # Rule 5: Molti DELETE
        if row['delete_count'] > 50:
            alerts.append(f"MASS_DELETE({int(row['delete_count'])} ops)")
        
        # Rule 6: Alto error rate (possibile SQLi)
        if row['error_rate'] > 0.3 and row['query_count'] > 20:
            alerts.append(f"HIGH_ERROR_RATE({row['error_rate']:.2f})")
        
        return '; '.join(alerts)
    
    def generate_report(self, analysis_results: pd.DataFrame):
        """Genera report visuale delle anomalie."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Anomaly score distribution
        axes[0, 0].hist(analysis_results['anomaly_score'], bins=50, edgecolor='black', alpha=0.7)
        threshold = analysis_results[analysis_results['is_anomaly_ml']]['anomaly_score'].min()
        axes[0, 0].axvline(x=threshold, color='red', linestyle='--', label=f'Threshold={threshold:.3f}')
        axes[0, 0].set_title("Anomaly Score Distribution")
        axes[0, 0].legend()
        
        # Query volume vs Sensitive access
        scatter = axes[0, 1].scatter(
            analysis_results['query_count'],
            analysis_results['sensitive_table_access'],
            c=analysis_results['anomaly_score'],
            cmap='YlOrRd',
            alpha=0.6
        )
        plt.colorbar(scatter, ax=axes[0, 1])
        axes[0, 1].set_xlabel("Query Count")
        axes[0, 1].set_ylabel("Sensitive Table Accesses")
        axes[0, 1].set_title("Query Volume vs Sensitive Access (color=anomaly)")
        
        # Rows extracted distribution
        axes[1, 0].hist(
            np.log1p(analysis_results['total_rows_returned']),
            bins=50, edgecolor='black', alpha=0.7
        )
        axes[1, 0].set_xlabel("log(Total Rows Returned)")
        axes[1, 0].set_title("Data Extraction Volume Distribution")
        
        # Alert summary
        alert_users = analysis_results[analysis_results['is_alert']]
        alert_types = []
        for alerts_str in alert_users['rule_alerts']:
            if alerts_str:
                for alert in alerts_str.split('; '):
                    alert_type = alert.split('(')[0]
                    alert_types.append(alert_type)
        
        if alert_types:
            from collections import Counter
            alert_counts = Counter(alert_types)
            pd.Series(alert_counts).plot(kind='barh', ax=axes[1, 1])
            axes[1, 1].set_title("Alert Type Distribution")
        
        plt.tight_layout()
        plt.savefig("db_query_anomaly_report.png", dpi=150, bbox_inches='tight')
        
        # Text summary
        print("\n" + "=" * 60)
        print("DATABASE QUERY ANOMALY REPORT")
        print("=" * 60)
        print(f"Total users analyzed: {len(analysis_results)}")
        print(f"Anomalous users (ML): {analysis_results['is_anomaly_ml'].sum()}")
        print(f"Alerted users (rules): {(analysis_results['rule_alerts'] != '').sum()}")
        print(f"Combined alerts: {analysis_results['is_alert'].sum()}")
        
        if not alert_users.empty:
            print(f"\nTop Anomalous Users:")
            for _, row in alert_users.nlargest(5, 'anomaly_score').iterrows():
                print(f"  {row['username']}: score={row['anomaly_score']:.3f}, "
                      f"queries={int(row['query_count'])}, "
                      f"sensitive={int(row['sensitive_table_access'])}")
                if row['rule_alerts']:
                    print(f"    Alerts: {row['rule_alerts']}")


# === USAGE ===

def generate_synthetic_query_logs(n_normal=100000, n_attack=500):
    """Genera query logs sintetici per il lab."""
    np.random.seed(42)
    
    users = [f"app_user_{i:03d}" for i in range(50)] + ['admin', 'etl_service', 'readonly_user']
    tables = ['orders', 'customers', 'products', 'inventory', 'logs', 'sessions']
    sensitive_tables = ['users', 'payments', 'credentials', 'audit_trail']
    
    # Normal queries
    normal_logs = pd.DataFrame({
        'query_id': range(n_normal),
        'timestamp': pd.date_range('2025-01-01', periods=n_normal, freq='30s'),
        'username': np.random.choice(users, n_normal, p=[0.018]*50 + [0.05, 0.03, 0.02]),
        'table_name': np.random.choice(tables + sensitive_tables, n_normal,
                                        p=[0.2, 0.15, 0.15, 0.1, 0.15, 0.1, 0.05, 0.05, 0.03, 0.02]),
        'query_type': np.random.choice(['SELECT', 'INSERT', 'UPDATE', 'DELETE'], n_normal, p=[0.7, 0.15, 0.1, 0.05]),
        'rows_returned': np.random.lognormal(3, 1.5, n_normal).astype(int).clip(0, 10000),
        'execution_time_ms': np.random.lognormal(3, 1, n_normal).clip(1, 30000),
        'source_ip': np.random.choice(['10.0.1.100', '10.0.1.101', '10.0.2.50'], n_normal),
        'is_error': np.random.choice([True, False], n_normal, p=[0.02, 0.98]),
    })
    normal_logs['is_sensitive_table'] = normal_logs['table_name'].isin(sensitive_tables)
    normal_logs['is_off_hours'] = normal_logs['timestamp'].dt.hour.apply(lambda h: h < 6 or h > 22)
    
    # Attack: data exfiltration
    attack_logs = pd.DataFrame({
        'query_id': range(n_normal, n_normal + n_attack),
        'timestamp': pd.date_range('2025-01-20 03:00', periods=n_attack, freq='2s'),
        'username': 'compromised_user',
        'table_name': np.random.choice(sensitive_tables, n_attack),
        'query_type': 'SELECT',
        'rows_returned': np.random.randint(5000, 50000, n_attack),
        'execution_time_ms': np.random.lognormal(5, 0.5, n_attack).clip(100, 60000),
        'source_ip': '192.168.99.99',
        'is_error': np.random.choice([True, False], n_attack, p=[0.15, 0.85]),
    })
    attack_logs['is_sensitive_table'] = True
    attack_logs['is_off_hours'] = True
    
    logs = pd.concat([normal_logs, attack_logs], ignore_index=True)
    return logs.sort_values('timestamp').reset_index(drop=True)


# Run the lab
query_logs = generate_synthetic_query_logs()

# Split: prima meta' come baseline, seconda come monitoring
split_date = query_logs['timestamp'].median()
baseline_logs = query_logs[query_logs['timestamp'] < split_date]
current_logs = query_logs[query_logs['timestamp'] >= split_date]

# Build monitor and analyze
monitor = DatabaseQueryMonitor(alert_threshold=0.05)
monitor.build_baseline(baseline_logs)
results = monitor.analyze(current_logs)
monitor.generate_report(results)
```

---

## Riferimenti e Risorse

### Libri Fondamentali
- Tukey, J.W. (1977). *Exploratory Data Analysis*. Addison-Wesley.
- Cleveland, W.S. (1993). *Visualizing Data*. Hobart Press.
- Wickham, H. & Grolemund, G. (2017). *R for Data Science*. O'Reilly.

### Librerie Python
- **pandas**: `pip install pandas` — strutture dati e operazioni base
- **numpy**: `pip install numpy` — operazioni numeriche
- **scipy**: `pip install scipy` — statistiche e test
- **matplotlib**: `pip install matplotlib` — plotting base
- **seaborn**: `pip install seaborn` — plotting statistico
- **plotly**: `pip install plotly` — grafici interattivi
- **ydata-profiling**: `pip install ydata-profiling` — report automatici
- **missingno**: `pip install missingno` — visualizzazione missing data
- **scikit-learn**: `pip install scikit-learn` — ML per anomaly detection
- **pingouin**: `pip install pingouin` — statistiche avanzate (partial corr)
- **altair**: `pip install altair` — grammar of graphics

### Dataset Consigliati per Pratica
- Kaggle Credit Card Fraud Detection
- UCI Machine Learning Repository
- CICIDS (Canadian Institute for Cybersecurity) — network intrusion
- LANL Unified Host and Network Dataset — security research
- NYC Taxi Trip Data — large-scale EDA
- Kaggle House Prices — classic regression EDA
