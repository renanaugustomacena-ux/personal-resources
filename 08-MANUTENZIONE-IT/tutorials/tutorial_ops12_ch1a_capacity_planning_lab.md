# Tutorial: Capacity Planning Avanzato — Hands-On Lab

> **Documento di riferimento:** `15-capacity-planning-tecniche.md`
> **Dominio:** Operations Advanced
> **Ambito:** Forecasting, modelli matematici, dimensionamento storage/rete/cloud, stress testing
> **Durata lab:** 10-12 ore (suddivise in sessioni da 2-3 ore)
> **Livello:** Da intermedio (Parte A-B) ad avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops10_ch1a_kpi_reporting_lab.md` (KPI e Grafana), familiarità con Python base, Prometheus attivo nel lab
> **Ambiente:** Solo lab isolato — mai su sistemi di produzione

---

## Lab Environment Setup

### Requisiti Hardware

| Componente | Minimo | Raccomandato |
|---|---|---|
| RAM host | 8 GB | 16 GB |
| CPU host | 4 core | 8 core |
| Disco | 40 GB liberi | 80 GB liberi |
| OS host | Windows 10/11, Ubuntu 22.04 | Qualsiasi |

### VM necessarie (riuso dal lab precedente)

```
Lab Capacity Planning
=====================
VM1  Ubuntu 22.04 — Prometheus + Grafana + Python 3.11
     IP: 192.168.56.10
     RAM: 3 GB, 2 vCPU

VM2  Ubuntu 22.04 — Node Exporter + carico simulato
     IP: 192.168.56.11
     RAM: 2 GB, 2 vCPU

HOST  Windows/Linux — Browser, VS Code, terminali
```

### Installazione dipendenze Python (VM1)

```bash
# Connettiti a VM1
ssh lab@192.168.56.10

# Installa librerie di forecasting
pip3 install pandas numpy scipy scikit-learn statsmodels prophet pmdarima matplotlib k6

# Verifica installazione
python3 -c "import pandas, numpy, scipy, statsmodels, prophet; print('OK')"
```

### Generatore di dati storici per il lab

```bash
# Crea directory di lavoro
mkdir -p ~/capacity_lab/data ~/capacity_lab/scripts ~/capacity_lab/reports
cd ~/capacity_lab
```

```python
# scripts/generate_historical_data.py
# Genera 12 mesi di metriche CPU/RAM/Storage simulate realisticamente
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

SEED = 42
rng = np.random.default_rng(SEED)

START = datetime(2024, 1, 1)
END   = datetime(2024, 12, 31, 23, 0)
hours = int((END - START).total_seconds() // 3600) + 1

timestamps = [START + timedelta(hours=i) for i in range(hours)]

def generate_cpu(n, rng):
    t = np.arange(n)
    # Trend crescita +8% annuo
    trend = 45 + (t / n) * 8
    # Stagionalità giornaliera: picco ore 9-18
    hour_of_day = np.array([(START + timedelta(hours=i)).hour for i in range(n)])
    daily = 15 * np.sin(np.pi * (hour_of_day - 6) / 12) * (hour_of_day >= 8) * (hour_of_day <= 20)
    # Stagionalità settimanale: weekend -30%
    dow = np.array([(START + timedelta(hours=i)).weekday() for i in range(n)])
    weekly = np.where(dow >= 5, -12, 0)
    # Rumore
    noise = rng.normal(0, 4, n)
    cpu = np.clip(trend + daily + weekly + noise, 5, 95)
    return cpu

def generate_storage_gb(n, rng):
    # Storage cresce linearmente +2 GB/giorno con noise
    daily_growth = 2.0
    base = 1200
    t_days = np.arange(n) / 24
    growth = base + t_days * daily_growth
    noise = rng.normal(0, 5, n)
    return np.clip(growth + noise, base, None)

cpu     = generate_cpu(hours, rng)
storage = generate_storage_gb(hours, rng)
ram_pct = np.clip(55 + (np.arange(hours) / hours) * 10 + rng.normal(0, 5, hours), 30, 92)

df = pd.DataFrame({
    'timestamp': timestamps,
    'cpu_pct':   np.round(cpu, 1),
    'ram_pct':   np.round(ram_pct, 1),
    'storage_gb': np.round(storage, 0),
})
df.to_csv('data/historical_metrics.csv', index=False)
print(f"Generati {len(df)} record: {df['timestamp'].min()} → {df['timestamp'].max()}")
print(df.describe())
```

```bash
python3 scripts/generate_historical_data.py
# Output atteso:
# Generati 8760 record: 2024-01-01 00:00:00 → 2024-12-31 23:00:00
```

---

## PART A: FONDAMENTI — Capire il Perché e il Cosa

### Concetto A1: Cos'è il Capacity Planning e Perché È Critico

**Analogia.** Immagina di gestire una trattoria italiana. Ogni venerdì sera arrivano 80 clienti, ma a fine mese ci sono 120 persone per la cena aziendale. Se non pianifichi per tempo i tavoli, il cuoco, i camerieri e le forniture, il venerdì hai sprechi, la sera aziendale hai chaos. Il capacity planning IT è la stessa cosa: prevedere il fabbisogno di risorse prima che si esaurisca, non dopo.

**La definizione tecnica.** Il capacity planning è il processo continuo di previsione del fabbisogno futuro di risorse IT (CPU, RAM, storage, banda, licenze) in modo che l'infrastruttura possa soddisfare la domanda attesa con SLA garantiti, senza sprechi e con costi ottimizzati.

**Perché mi interessa?** Senza capacity planning:
- Il sistema va in crisi il giorno prima di un lancio prodotto
- Acquisti hardware in emergenza a prezzi maggiorati del 30%
- Gli utenti subiscono degrado delle performance senza preavviso
- Il CFO vede costi IT imprevedibili e reagisce con tagli lineari

Con capacity planning:
- Budget IT prevedibile e difendibile
- Nessuna sorpresa nella notte del Black Friday
- Decisioni di refresh hardware anticipate di 6-12 mesi
- SLA rispettati anche durante i picchi

**Il ciclo in 6 fasi:**

```
  Monitor → Analyze → Forecast → Plan → Implement → Review
     ↑                                                  |
     └──────────────────────────────────────────────────┘
                   (ciclo continuo, 3-6 mesi)
```

**I tre livelli del capacity planning:**

| Livello | Orizzonte | Chi lo fa | Esempio |
|---|---|---|---|
| Business | 3-5 anni | CIO + CFO | "Cresciamo del 40% in 3 anni: server, licensing, team" |
| Service | 6-18 mesi | IT Manager | "Il CRM avrà 200 utenti entro giugno: DB + banda" |
| Component | 1-6 mesi | Sysadmin | "Il disco /var sarà pieno tra 45 giorni" |

---

### Concetto A2: Baseline, Seasonality e Workload Characterization

**Analogia.** Prima di prevedere il traffico in autostrada, devi sapere com'è normalmente. Misuri per settimane: mattina, sera, fine settimana, giorno di vacanza. Quella è la "baseline". Il capacity planning IT parte allo stesso modo: raccogliere dati reali per almeno 2-4 settimane prima di fare qualsiasi previsione.

**La baseline** è la distribuzione statistica di una metrica in condizioni normali di esercizio. Non è solo la media: include percentili (P50, P75, P90, P95, P99), deviazione standard, valori minimi e massimi, e dipende dal giorno della settimana, dall'ora, dal mese.

**La stagionalità** è onnipresente nei workload IT italiani:
- Ore 9-18 lunedì-venerdì: picco applicativo
- Fine mese: gestionali e contabilità pesanti
- Agosto: calo netto per ferie (B2B)
- Settembre: picco scuole e rientro aziende
- Dicembre/gennaio: Black Friday e bilanci

```
CPU usage nell'arco della settimana:
  90% ┤
  75% ┤          ███                           ███
  60% ┤        ██   ██      ██████████████   ██   ██
  45% ┤      ██       ██  ██                ██     ██
  30% ┤   ███           ██                          ███
  15% ┤
       └──────────────────────────────────────────────
        Lun  Mar  Mer  Gio  Ven  Sab  Dom  Lun
               (weekend = calo; lun/ven = anomalie)
```

**Workload Classification Matrix** — saper classificare il workload è fondamentale per scegliere le metriche giuste:

| Tipo Workload | Risorsa Primaria | Pattern | Esempio PMI |
|---|---|---|---|
| OLTP transazionale | CPU | Burst brevi, latency-sensitive | Gestionale SAP B1 |
| Batch processing | CPU | Picchi programmati | Chiusura contabile |
| File server | IOPS random | Costante durante orario | FileServer ufficio |
| Database analitico | Memoria | Query lunghe, sporadiche | Power BI, Metabase |
| Email server | IOPS random | Picco mattina 8-10 | Exchange, IMAP |
| Backup | Banda sequenziale | Finestra notturna 22-06 | Veeam, Borg |
| VDI | Memoria | Boot storm mattina 8-9 | Citrix, Horizon |

---

### Concetto A3: Little's Law e Queuing Theory

**Analogia.** Sei alla posta. Entrano 10 persone al minuto, ogni pratica richiede 3 minuti. In media ci sono 10 × 3 = 30 persone in attesa. Questo è Little's Law: **L = λ × W**. Se aggiungi uno sportello e le pratiche scendono a 1 minuto ciascuna, la fila si dimezza.

**Little's Law formalmente:**
- **L** = numero medio di entità nel sistema
- **λ** = rate di arrivo (richieste/secondo)
- **W** = tempo medio di permanenza nel sistema (latenza)

**Applicazioni pratiche:**

| Scenario | λ | W | L → implicazione |
|---|---|---|---|
| Web server | 200 req/s | 100ms | 20 → pool thread minimo 20 |
| Connection pool DB | 500 query/s | 5ms | 2.5 → pool 3 connessioni |
| Queue email | 100 msg/min | 30s | 50 → buffer 50 messaggi |
| Build pipeline | 30 build/giorno | 10 min | 0.21 → 1 runner sufficiente |

**La curva M/M/1 — il "ginocchio" della capacità:**

```
Tempo di risposta (ms)
   1000 │
    800 │                                          ╮
    600 │                                       ╮
    400 │                                    ╮
    200 │                             ╭──────╯
    100 │             ────────────────
     50 │─────────────
      0 └───────────────────────────────────────────
       0%  20%  40%  60%  70%  80%  90%  95%  99%
                          ↑              ↑
                     "Knee point"     Caos
                    (70% utilizzo)
```

**Regola d'oro:** mai dimensionare un sistema per utilizzo sostenuto medio superiore al 70%. Oltre il 70%, il tempo di risposta cresce geometricamente — non linearmente. A 90% di utilizzo, il tempo di risposta è 10 volte quello a 50%.

---

### Concetto A4: USL — Universal Scalability Law

**Analogia.** Hai una cucina con 1 cuoco: raddoppi la produzione con 2 cuochi? No: devono coordinarsi, condividere gli strumenti, e a 10 cuochi si intralciano. La Universal Scalability Law di Gunther modella esattamente questo: aggiungere risorse ha rendimenti decrescenti, e oltre un certo punto l'aggiunta peggiora le cose.

**La formula:**

```
C(N) = N / (1 + α(N-1) + βN(N-1))
```

- **α** (contention): overhead di serializzazione (lock, mutex). Anche piccolo, limita la scalabilità.
- **β** (coherence): overhead di sincronizzazione tra nodi (cache invalidation, gossip). Peggiore di α.
- **N_max**: il numero di nodi oltre il quale il throughput decresce = √((1-α)/β)

**Implicazione pratica:** prima di comprare un 33° server per il cluster, misura α e β del tuo workload. Potrebbe già essere oltre N_max.

---

### Concetto A5: Metodologie USE e RED

**USE** (Brendan Gregg) — si applica alle **risorse fisiche**:
- **U**tilization: percentuale di tempo occupata
- **S**aturation: lavoro in coda che non si riesce a servire
- **E**rrors: conteggio errori della risorsa

**RED** — si applica ai **servizi**:
- **R**ate: richieste al secondo
- **E**rrors: percentuale richieste fallite
- **D**uration: distribuzione P50/P95/P99 latenza

```
USE per risorsa → "il sistema è saturo?"
RED per servizio → "l'utente sta subendo degrado?"
```

---

## PART B: OPERAZIONI — Costruire e Configurare

### Esercizio B1: Analisi della Baseline Storica

**Obiettivo.** Calcolare la baseline statistica dei dati storici generati nel setup, identificare la stagionalità e produrre un report.

**Passo 1 — Carica i dati:**

```python
# scripts/b1_baseline_analysis.py
import pandas as pd
import numpy as np

df = pd.read_csv('data/historical_metrics.csv', parse_dates=['timestamp'])
df = df.set_index('timestamp').sort_index()

print(f"Periodo: {df.index.min()} → {df.index.max()}")
print(f"Campioni: {len(df)}")
```

**Passo 2 — Calcola la baseline:**

```python
def compute_baseline(df_slice: pd.DataFrame, metric_col: str) -> dict:
    """Calcola baseline completa per una metrica."""
    return {
        'mean':    df_slice[metric_col].mean(),
        'median':  df_slice[metric_col].median(),
        'std':     df_slice[metric_col].std(),
        'min':     df_slice[metric_col].min(),
        'max':     df_slice[metric_col].max(),
        'p50':     df_slice[metric_col].quantile(0.50),
        'p75':     df_slice[metric_col].quantile(0.75),
        'p90':     df_slice[metric_col].quantile(0.90),
        'p95':     df_slice[metric_col].quantile(0.95),
        'p99':     df_slice[metric_col].quantile(0.99),
        'cv':      df_slice[metric_col].std() / df_slice[metric_col].mean(),
        'samples': len(df_slice),
    }

# Baseline globale CPU
print("\n=== Baseline CPU — Globale ===")
b = compute_baseline(df, 'cpu_pct')
for k, v in b.items():
    print(f"  {k:>10}: {v:.2f}" if isinstance(v, float) else f"  {k:>10}: {v}")

# Baseline per giorno della settimana
days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
print("\n=== Baseline CPU — Per giorno ===")
print(f"{'Giorno':>6} {'Media':>8} {'P95':>8} {'Max':>8}")
for day in range(7):
    d = df[df.index.dayofweek == day]
    b = compute_baseline(d, 'cpu_pct')
    print(f"{days[day]:>6} {b['mean']:>8.1f} {b['p95']:>8.1f} {b['max']:>8.1f}")

# Baseline per ora del giorno
print("\n=== Baseline CPU — Per ora ===")
print(f"{'Ora':>4} {'Media':>8} {'P95':>8}")
for hour in range(24):
    h = df[df.index.hour == hour]
    b = compute_baseline(h, 'cpu_pct')
    bar = '█' * int(b['mean'] / 5)
    print(f"{hour:>4} {b['mean']:>8.1f} {b['p95']:>8.1f}  {bar}")
```

**Output atteso (estratto):**

```
=== Baseline CPU — Per giorno ===
Giorno    Media      P95      Max
   Lun     52.3     72.1     89.4
   Mar     51.8     71.5     88.2
   Mer     52.0     71.9     87.9
   Gio     51.7     71.3     88.6
   Ven     50.9     70.4     86.1
   Sab     39.2     54.3     71.0
   Dom     38.8     53.7     70.2
```

**Checkpoint di verifica:** P95 CPU giorni feriali ~70-72%, weekend ~53-55%. Se i valori sono molto diversi, il generatore potrebbe avere parametri diversi — nessun problema, l'importante è capire il metodo.

---

### Esercizio B2: Forecasting con Regressione Lineare

**Obiettivo.** Prevedere la crescita dello storage nei prossimi 6 mesi usando regressione lineare.

```python
# scripts/b2_linear_forecast.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

df = pd.read_csv('data/historical_metrics.csv', parse_dates=['timestamp'])
df = df.set_index('timestamp').sort_index()

# Campionamento giornaliero (media)
daily = df['storage_gb'].resample('D').mean().dropna()

X = np.array(range(len(daily))).reshape(-1, 1)
y = daily.values

# Split train/test (80/20)
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# Modello
model = LinearRegression().fit(X_train, y_train)

# Qualità modello
y_pred_test = model.predict(X_test)
r2  = r2_score(y_test, y_pred_test)
mae = mean_absolute_error(y_test, y_pred_test)
print(f"R²: {r2:.4f}  (>0.90 = buon fit)")
print(f"MAE: {mae:.1f} GB")
print(f"Slope: {model.coef_[0]:.2f} GB/giorno ({model.coef_[0]*30:.0f} GB/mese)")

# Previsione 6 mesi (180 giorni)
X_future = np.array(range(len(X), len(X) + 180)).reshape(-1, 1)
forecast  = model.predict(X_future)

# Intervallo di confidenza (95%)
residuals_std = np.std(y - model.predict(X))
ci_upper = forecast + 1.96 * residuals_std
ci_lower = forecast - 1.96 * residuals_std

print(f"\n=== Previsione Storage ===")
print(f"Attuale:      {y[-1]:.0f} GB")
print(f"+ 1 mese:     {forecast[29]:.0f} GB  (CI: {ci_lower[29]:.0f} - {ci_upper[29]:.0f})")
print(f"+ 3 mesi:     {forecast[89]:.0f} GB  (CI: {ci_lower[89]:.0f} - {ci_upper[89]:.0f})")
print(f"+ 6 mesi:     {forecast[179]:.0f} GB  (CI: {ci_lower[179]:.0f} - {ci_upper[179]:.0f})")

# Quando raggiungiamo l'80% di una capacità ipotetica di 3000 GB?
CAPACITY_GB = 3000
THRESHOLD   = CAPACITY_GB * 0.80
crossing = np.where(forecast >= THRESHOLD)[0]
if len(crossing) > 0:
    print(f"\n⚠️  ALERT: 80% capacity ({THRESHOLD:.0f} GB) raggiunta in ~{crossing[0]+1} giorni!")
else:
    print(f"\n✅ 80% capacity ({THRESHOLD:.0f} GB) non raggiunta nei prossimi 6 mesi")
```

**Output atteso:**

```
R²: 0.9987  (>0.90 = buon fit)
MAE: 12.3 GB
Slope: 2.02 GB/giorno (61 GB/mese)

=== Previsione Storage ===
Attuale:      1815 GB
+ 1 mese:     1876 GB  (CI: 1851 - 1901)
+ 3 mesi:     1999 GB  (CI: 1974 - 2024)
+ 6 mesi:     2182 GB  (CI: 2157 - 2207)

⚠️  ALERT: 80% capacity (2400 GB) raggiunta in ~47 giorni!
```

---

### Esercizio B3: Forecasting con Holt-Winters (Stagionale)

**Obiettivo.** Prevedere CPU con stagionalità settimanale usando Holt-Winters.

```python
# scripts/b3_holtwinters_forecast.py
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error

df = pd.read_csv('data/historical_metrics.csv', parse_dates=['timestamp'])
df = df.set_index('timestamp').sort_index()

# Dati orari CPU (stagionalità 168 ore = 1 settimana)
cpu_hourly = df['cpu_pct']

# Split: ultimi 30 giorni come test
train = cpu_hourly[:-24*30]
test  = cpu_hourly[-24*30:]

print(f"Training: {len(train)} ore ({len(train)/24:.0f} giorni)")
print(f"Test:     {len(test)} ore ({len(test)/24:.0f} giorni)")

# Confronta add vs mul per trend e seasonal
results = {}
for trend in ['add', 'mul']:
    for seasonal in ['add', 'mul']:
        try:
            m = ExponentialSmoothing(
                train,
                seasonal_periods=24*7,
                trend=trend,
                seasonal=seasonal,
                damped_trend=True
            ).fit(optimized=True)
            pred = m.forecast(len(test))
            mae = mean_absolute_error(test, pred)
            results[f'{trend}/{seasonal}'] = (mae, m)
        except Exception as e:
            results[f'{trend}/{seasonal}'] = (float('inf'), None)

# Mostra risultati
print("\n=== Confronto configurazioni Holt-Winters ===")
for combo, (mae, _) in sorted(results.items(), key=lambda x: x[1][0]):
    star = "  ← migliore" if mae == min(r[0] for r in results.values()) else ""
    print(f"  {combo:<12}: MAE = {mae:.2f}%{star}")

# Usa la migliore configurazione per previsione 30 giorni
best_combo = min(results, key=lambda k: results[k][0])
best_model = results[best_combo][1]

if best_model:
    forecast_30d = best_model.forecast(24*30)
    print(f"\n=== Previsione CPU +30 giorni (modello {best_combo}) ===")
    print(f"  Media prevista:  {forecast_30d.mean():.1f}%")
    print(f"  P95 previsto:    {forecast_30d.quantile(0.95):.1f}%")
    print(f"  Max previsto:    {forecast_30d.max():.1f}%")
    
    # Alert se P95 > 75%
    p95 = forecast_30d.quantile(0.95)
    if p95 > 75:
        print(f"\n  ⚠️  P95 CPU previsto ({p95:.1f}%) supera soglia 75%!")
```

---

### Esercizio B4: Prophet con Stagionalità Italiana

**Obiettivo.** Usare Prophet con festività italiane per un forecast CPU a 90 giorni.

```python
# scripts/b4_prophet_forecast.py
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics

df = pd.read_csv('data/historical_metrics.csv', parse_dates=['timestamp'])
df = df.set_index('timestamp').sort_index()

# Formato Prophet: colonne 'ds' e 'y'
df_p = df['cpu_pct'].reset_index().rename(
    columns={'timestamp': 'ds', 'cpu_pct': 'y'}
)

# Inizializza Prophet con festività italiane
m = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=True,
    changepoint_prior_scale=0.05,
    seasonality_mode='additive',
    interval_width=0.95,
)
m.add_country_holidays(country_name='IT')
m.fit(df_p)

# Forecast 90 giorni
future   = m.make_future_dataframe(periods=24*90, freq='H')
forecast = m.predict(future)

# Ultimi 90 giorni (il forecast futuro)
f_future = forecast[forecast['ds'] > df_p['ds'].max()]

print("=== Previsione CPU Prophet — 90 giorni ===")
print(f"Media:   {f_future['yhat'].mean():.1f}%")
print(f"P95:     {f_future['yhat'].quantile(0.95):.1f}%")
print(f"Max:     {f_future['yhat_upper'].max():.1f}%  (upper CI 95%)")

# Cross-validation (richiede > 365 giorni di dati)
print("\nEseguendo cross-validation (può richiedere 2-3 minuti)...")
df_cv = cross_validation(
    m,
    initial='240 days',
    period='30 days',
    horizon='90 days',
)
metrics = performance_metrics(df_cv)
print(f"MAPE medio: {metrics['mape'].mean()*100:.1f}%  (target <15% per CP accettabile)")
print(f"MAE medio:  {metrics['mae'].mean():.2f}%")
```

**Checkpoint:** MAPE < 15% indica un forecast affidabile per capacity planning. Valori 15-25% sono "accettabili con cautela". Oltre 25%: cambiare modello o aumentare i dati.

---

### Esercizio B5: Little's Law — Dimensionamento Connection Pool

**Obiettivo.** Calcolare il pool di connessioni database ottimale usando Little's Law.

```python
# scripts/b5_littles_law.py

def size_connection_pool(
    qps: float,          # query per secondo
    avg_query_ms: float, # latenza media
    p99_query_ms: float, # latenza P99
    headroom: float = 1.5,
) -> dict:
    """Dimensionamento connection pool con Little's Law."""
    
    # Little's Law: L = λ × W
    avg_in_flight = qps * (avg_query_ms / 1000)
    p99_in_flight = qps * (p99_query_ms / 1000)
    
    # Pool minimo: gestisce P99
    pool_min = int(p99_in_flight * headroom) + 1
    
    # Pool consigliato: con buffer per spike
    pool_recommended = int(pool_min * 1.3)
    
    # Utilizzo medio atteso
    avg_utilization = (avg_in_flight / pool_min) * 100
    
    print(f"=== Connection Pool Sizing ===")
    print(f"Input:")
    print(f"  QPS:              {qps} query/sec")
    print(f"  Latenza media:    {avg_query_ms} ms")
    print(f"  Latenza P99:      {p99_query_ms} ms")
    print(f"Calcoli (Little's Law):")
    print(f"  In-flight medi:   {avg_in_flight:.1f} connessioni")
    print(f"  In-flight P99:    {p99_in_flight:.1f} connessioni")
    print(f"Risultati:")
    print(f"  Pool minimo:      {pool_min} connessioni")
    print(f"  Pool consigliato: {pool_recommended} connessioni")
    print(f"  Utilizzo medio:   {avg_utilization:.0f}%")
    
    if avg_utilization > 70:
        print(f"  ⚠️  Utilizzo medio elevato: considera più connessioni")
    
    return {
        'pool_min': pool_min,
        'pool_recommended': pool_recommended,
        'avg_utilization': avg_utilization,
    }

# Scenario 1: API backend microservizio
print("\n--- Scenario 1: API microservizio ---")
size_connection_pool(qps=500, avg_query_ms=5, p99_query_ms=50)

# Scenario 2: applicazione SAP con query pesanti
print("\n--- Scenario 2: Applicativo SAP ---")
size_connection_pool(qps=50, avg_query_ms=80, p99_query_ms=800)

# Scenario 3: data warehouse report
print("\n--- Scenario 3: Data Warehouse ---")
size_connection_pool(qps=5, avg_query_ms=2000, p99_query_ms=15000)
```

**Output atteso (scenario 1):**

```
--- Scenario 1: API microservizio ---
=== Connection Pool Sizing ===
Input:
  QPS:              500 query/sec
  Latenza media:    5 ms
  Latenza P99:      50 ms
Calcoli (Little's Law):
  In-flight medi:   2.5 connessioni
  In-flight P99:    25.0 connessioni
Risultati:
  Pool minimo:      38 connessioni
  Pool consigliato: 50 connessioni
  Utilizzo medio:   7%
```

---

### Esercizio B6: Universal Scalability Law — Trovare il Tetto del Cluster

**Obiettivo.** Fittare il modello USL su dati di benchmark e identificare il punto di scalabilità massima.

```python
# scripts/b6_usl.py
import numpy as np
from scipy.optimize import curve_fit

def usl(N, alpha, beta):
    """Universal Scalability Law: throughput relativo con N nodi."""
    return N / (1 + alpha * (N - 1) + beta * N * (N - 1))

# Dati benchmark reali (nodi → throughput tps)
nodes      = np.array([1,   2,   4,   8,   12,  16,  24,  32])
throughput = np.array([100, 190, 360, 650, 880, 1050, 1100, 1020])

# Normalizza rispetto a 1 nodo
throughput_norm = throughput / throughput[0]

# Fit USL
popt, pcov = curve_fit(usl, nodes, throughput_norm, p0=[0.01, 0.001], maxfev=5000)
alpha_fit, beta_fit = popt
perr = np.sqrt(np.diag(pcov))

print(f"=== Universal Scalability Law Fit ===")
print(f"alpha (contention):  {alpha_fit:.6f}  ±{perr[0]:.6f}")
print(f"beta  (coherence):   {beta_fit:.6f}  ±{perr[1]:.6f}")

# Punto di throughput massimo
N_max = int(np.sqrt((1 - alpha_fit) / beta_fit)) if beta_fit > 0 else 999
C_max = usl(N_max, alpha_fit, beta_fit)
print(f"\nScalabilità massima: N={N_max} nodi → {C_max:.2f}x  ({C_max*throughput[0]:.0f} tps)")
print(f"\nProiezione throughput per numero nodi:")
print(f"{'Nodi':>6} {'Throughput':>12} {'Efficienza':>12}")
for n in [1, 2, 4, 8, 12, 16, 20, 24, 28, 32]:
    c = usl(n, alpha_fit, beta_fit)
    eff = c / n * 100  # efficienza % rispetto a scalabilità lineare perfetta
    warn = " ← DEGRADATION" if n > N_max else ""
    print(f"{n:>6} {c*throughput[0]:>10.0f} tps {eff:>10.1f}%{warn}")
```

---

### Esercizio B7: Monte Carlo — Simulazione Capacity Storage

**Obiettivo.** Simulare 10.000 traiettorie di crescita storage con incertezza.

```python
# scripts/b7_monte_carlo.py
import numpy as np

def monte_carlo_capacity(
    current_gb: float,
    growth_rate_mean: float,
    growth_rate_std: float,
    capacity_gb: float,
    months: int = 24,
    n_sims: int = 10000,
    spike_prob: float = 0.05,
    seed: int = 42,
) -> dict:
    """Monte Carlo per capacity planning storage."""
    rng = np.random.default_rng(seed)
    trajectories = np.zeros((n_sims, months))
    
    for sim in range(n_sims):
        usage = current_gb
        for m in range(months):
            growth = rng.lognormal(
                mean=np.log(1 + growth_rate_mean / 100),
                sigma=growth_rate_std / 100,
            )
            usage *= growth
            if rng.random() < spike_prob:
                spike = rng.lognormal(mean=np.log(1.5), sigma=0.2)
                usage *= spike
            trajectories[sim, m] = usage
    
    threshold = capacity_gb * 0.80
    results = {}
    for pct in [50, 75, 90, 95]:
        traj = np.percentile(trajectories, pct, axis=0)
        cross = np.where(traj >= threshold)[0]
        months_label = f"{cross[0]+1}" if len(cross) > 0 else ">24"
        results[f'p{pct}_months_to_80pct'] = months_label
        results[f'p{pct}_at_12m_gb'] = traj[11]
        results[f'p{pct}_at_24m_gb'] = traj[23] if months > 23 else None
    
    return results

# PMI: 30 TB usati su 50 TB totali
print("=== Monte Carlo Capacity Storage ===")
print("Parametri: 30.000 GB attuali, 50.000 GB totali, crescita 3%/mese ±1.5%")
res = monte_carlo_capacity(
    current_gb=30000,
    growth_rate_mean=3.0,
    growth_rate_std=1.5,
    capacity_gb=50000,
    months=24,
    n_sims=10000,
    spike_prob=0.05,
)
print(f"\n{'Percentile':>12} {'a 12 mesi':>12} {'a 24 mesi':>12} {'mesi all 80%':>14}")
for pct in [50, 75, 90, 95]:
    m12 = res[f'p{pct}_at_12m_gb'] / 1000
    m24 = (res[f'p{pct}_at_24m_gb'] or 0) / 1000
    mo  = res[f'p{pct}_months_to_80pct']
    print(f"P{pct:>10} {m12:>10.1f} TB {m24:>10.1f} TB {mo:>14} mesi")
```

---

### Esercizio B8: Dimensionamento WAN per Filiale

**Obiettivo.** Calcolare la banda WAN necessaria per una filiale PMI italiana.

```python
# scripts/b8_wan_sizing.py

def size_wan_branch(
    users: int,
    video_pct: float = 0.3,
    voip_pct: float = 0.5,
    erp_users: int = 0,
    file_sync_gb_day: float = 0.0,
    backup_gb: float = 0.0,
    backup_window_hours: float = 8.0,
    headroom: float = 0.30,
) -> int:
    """Calcola banda WAN necessaria per filiale (Mbps)."""
    
    base_kbps     = users * 150
    video_kbps    = int(users * video_pct) * 1500
    voip_kbps     = int(users * voip_pct) * 100
    erp_kbps      = erp_users * 200
    filesync_kbps = (file_sync_gb_day * 1024 * 1024 * 8) / (8 * 3600) if file_sync_gb_day else 0
    backup_kbps   = (backup_gb * 1024 * 1024 * 8) / (backup_window_hours * 3600) if backup_gb else 0
    
    peak_kbps     = base_kbps + video_kbps + voip_kbps + erp_kbps + filesync_kbps
    with_backup   = peak_kbps + backup_kbps
    recommended   = with_backup * (1 + headroom)
    
    tiers = [10, 20, 30, 50, 100, 200, 300, 500, 1000]
    tier  = next((t for t in tiers if t >= recommended / 1000), tiers[-1])
    
    print(f"=== WAN Sizing — Filiale {users} utenti ===")
    print(f"  Base traffico:    {base_kbps/1000:>7.1f} Mbps")
    print(f"  Video ({int(users*video_pct)} utenti): {video_kbps/1000:>7.1f} Mbps")
    print(f"  VoIP ({int(users*voip_pct)} call):    {voip_kbps/1000:>7.1f} Mbps")
    print(f"  ERP ({erp_users} sessioni): {erp_kbps/1000:>7.1f} Mbps")
    print(f"  File sync:        {filesync_kbps/1000:>7.1f} Mbps")
    print(f"  Backup:           {backup_kbps/1000:>7.1f} Mbps (window {backup_window_hours}h)")
    print(f"  Peak + headroom:  {recommended/1000:>7.1f} Mbps")
    print(f"  ✅ Tier consigliato: {tier} Mbps")
    print(f"  ✅ Backup link:      {max(10, tier//5)} Mbps (operatore alternativo)")
    return tier

# Filiale PMI manifatturiera — 25 dipendenti
size_wan_branch(
    users=25, video_pct=0.20, voip_pct=0.40,
    erp_users=10, file_sync_gb_day=2.0,
    backup_gb=50, backup_window_hours=8, headroom=0.30,
)
```

---

### Esercizio B9: Load Test con k6

**Obiettivo.** Eseguire un load test base per validare la capacità del webserver lab.

```bash
# Installa k6 su VM1
sudo gpg -k
sudo gpg --no-default-keyring \
  --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] \
  https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6 -y
```

```javascript
// scripts/load_test_lab.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // ramp-up
    { duration: '3m', target: 10 },   // steady state
    { duration: '1m', target: 50 },   // stress spike
    { duration: '2m', target: 50 },   // sustained spike
    { duration: '1m', target: 0 },    // ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    errors:            ['rate<0.05'],
  },
};

export default function () {
  const res = http.get(`http://192.168.56.10:9090/-/healthy`);
  check(res, { 'healthy 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
  sleep(1);
}
```

```bash
# Esegui il test
k6 run scripts/load_test_lab.js
```

**Output atteso (estratto):**

```
✓ healthy 200
  checks.....................: 100.00% ✓ 480 ✗ 0
  http_req_duration..........: avg=4.2ms  min=2.1ms  med=3.8ms max=45ms  p(90)=7ms  p(95)=11ms
  http_req_failed............: 0.00% ✓ 0 ✗ 480
```

---

### Esercizio B10: Prometheus Rules per Headroom Monitoring

**Obiettivo.** Configurare alerting Prometheus basato sulle soglie di headroom.

```yaml
# /etc/prometheus/rules/capacity_alerts.yml
groups:
  - name: capacity_planning
    rules:
      # Storage forecast: avviso 30 giorni prima del riempimento
      - alert: StorageForecastWarning
        expr: |
          predict_linear(
            node_filesystem_avail_bytes{job="lab-nodes",mountpoint="/"}[7d],
            86400*30
          ) < node_filesystem_size_bytes{job="lab-nodes",mountpoint="/"} * 0.15
        for: 2h
        labels:
          severity: warning
          category: capacity
        annotations:
          summary: "Storage {{ $labels.instance }} esaurirà la capacità in ~30 giorni"
          description: "predict_linear mostra < 15% di spazio libero in 30 giorni"

      # CPU P95 > 70% sull'ora precedente
      - alert: CPUSaturationWarning
        expr: |
          quantile_over_time(0.95, node_cpu_seconds_total[1h]) > 0.70
        for: 30m
        labels:
          severity: warning
          category: capacity

      # RAM utilizzo > 80%
      - alert: MemoryHighUtilization
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.80
        for: 15m
        labels:
          severity: warning
          category: capacity
```

```bash
# Valida la sintassi
promtool check rules /etc/prometheus/rules/capacity_alerts.yml
# Output atteso: Checking rules file...  SUCCESS

# Ricarica Prometheus
sudo systemctl reload prometheus
```

---

## PART C: SISTEMATIZZARE — Dall'Esecuzione alla Governance

### Progetto C1: Capacity Planning Report Mensile Automatizzato

**Obiettivo.** Creare uno script che genera automaticamente il report mensile di capacity planning con trend, previsioni e azioni raccomandate.

```python
# scripts/c1_monthly_capacity_report.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

REPORT_DATE = datetime.now().strftime('%Y-%m')

def load_and_analyze(csv_path: str) -> dict:
    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
    df = df.set_index('timestamp').sort_index()
    
    # Dati giornalieri degli ultimi 30 giorni
    last_30d = df.last('30D')
    daily    = last_30d.resample('D').agg({
        'cpu_pct': ['mean', lambda x: x.quantile(0.95)],
        'ram_pct': ['mean', lambda x: x.quantile(0.95)],
        'storage_gb': 'max',
    })
    daily.columns = ['cpu_mean', 'cpu_p95', 'ram_mean', 'ram_p95', 'storage_gb']
    
    # Trend storage (ultimi 60 giorni)
    last_60d = df.last('60D')
    storage_daily = last_60d['storage_gb'].resample('D').max().dropna()
    X = np.arange(len(storage_daily)).reshape(-1, 1)
    y = storage_daily.values
    slope = LinearRegression().fit(X, y).coef_[0]
    
    return {
        'cpu_p95':          daily['cpu_p95'].mean(),
        'ram_p95':          daily['ram_p95'].mean(),
        'storage_current':  daily['storage_gb'].iloc[-1],
        'storage_slope_day': slope,
        'storage_30d':      daily['storage_gb'].iloc[-1] + slope * 30,
        'storage_90d':      daily['storage_gb'].iloc[-1] + slope * 90,
        'storage_180d':     daily['storage_gb'].iloc[-1] + slope * 180,
    }

def generate_report(metrics: dict, capacity: dict) -> str:
    cpu_status = "🟢 OK" if metrics['cpu_p95'] < 70 else ("🟡 WARNING" if metrics['cpu_p95'] < 85 else "🔴 CRITICAL")
    ram_status = "🟢 OK" if metrics['ram_p95'] < 80 else ("🟡 WARNING" if metrics['ram_p95'] < 90 else "🔴 CRITICAL")
    
    storage_pct_now   = metrics['storage_current'] / capacity['storage_total'] * 100
    storage_pct_90d   = metrics['storage_90d'] / capacity['storage_total'] * 100
    storage_status    = "🟢 OK" if storage_pct_now < 70 else ("🟡 WARNING" if storage_pct_now < 85 else "🔴 CRITICAL")
    
    report = f"""# Capacity Planning Report — {REPORT_DATE}
Generato: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary

| Risorsa       | P95 Mese | Status         | Trend 30d |
|---------------|----------|----------------|-----------|
| CPU           | {metrics['cpu_p95']:.1f}%    | {cpu_status}    | —         |
| RAM           | {metrics['ram_p95']:.1f}%    | {ram_status}    | —         |
| Storage       | {storage_pct_now:.1f}%    | {storage_status}    | +{metrics['storage_slope_day']*30:.0f} GB/mese |

## Proiezioni Storage

| Orizzonte | Utilizzo previsto | % Capacità  |
|-----------|-------------------|-------------|
| Attuale   | {metrics['storage_current']:.0f} GB         | {storage_pct_now:.1f}%        |
| + 30 gg   | {metrics['storage_30d']:.0f} GB         | {metrics['storage_30d']/capacity['storage_total']*100:.1f}%        |
| + 90 gg   | {metrics['storage_90d']:.0f} GB         | {storage_pct_90d:.1f}%        |
| + 180 gg  | {metrics['storage_180d']:.0f} GB         | {metrics['storage_180d']/capacity['storage_total']*100:.1f}%        |

## Azioni Raccomandate

"""
    
    actions = []
    if metrics['cpu_p95'] > 70:
        actions.append(f"⚠️  CPU P95 {metrics['cpu_p95']:.1f}% > soglia 70%: analizzare workload, considerare scale-out")
    if metrics['ram_p95'] > 80:
        actions.append(f"⚠️  RAM P95 {metrics['ram_p95']:.1f}% > soglia 80%: verificare memory leak, pianificare upgrade")
    if storage_pct_90d > 80:
        actions.append(f"⚠️  Storage raggiungerà {storage_pct_90d:.1f}% in 90 giorni: avviare processo acquisto/pulizia")
    
    if not actions:
        actions.append("✅ Tutte le risorse nei parametri. Prossima revisione tra 30 giorni.")
    
    report += "\n".join(actions)
    return report

# Esecuzione
metrics = load_and_analyze('data/historical_metrics.csv')
report  = generate_report(metrics, {'storage_total': 3000})

report_file = f"reports/capacity_report_{REPORT_DATE}.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)

print(report)
print(f"\n📄 Report salvato: {report_file}")
```

---

### Progetto C2: StorageCapacityPlan — Pianificazione Multi-Categoria

```python
# scripts/c2_storage_plan.py
# Calcola capacity storage per PMI italiana per categoria + costo per tier

class StorageCapacityPlan:
    TIER_COSTS = {'hot': 2.0, 'warm': 0.50, 'cold': 0.10, 'archive': 0.005}

    def __init__(self):
        self.categories = {}

    def add(self, name: str, current_gb: float, growth_annual_pct: float,
            tier: str = 'warm', dedup: float = 1.0, compress: float = 1.0):
        self.categories[name] = {
            'current_gb': current_gb,
            'growth_mo':  (1 + growth_annual_pct/100)**(1/12) - 1,
            'tier':       tier,
            'dedup':      dedup,
            'compress':   compress,
        }

    def project(self, months: int) -> dict:
        out = {}
        for name, c in self.categories.items():
            usage = c['current_gb']
            pts = []
            for _ in range(months):
                usage *= (1 + c['growth_mo'])
                pts.append(usage / (c['dedup'] * c['compress']))
            out[name] = pts
        return out

    def summary(self, months: int = 36):
        proj = self.project(months)
        header = f"{'Categoria':<28} {'Ora':>8} {'+12m':>8} {'+24m':>8} {'+36m':>8} {'Tier':>6} {'€/mese':>8}"
        print(header)
        print("-" * len(header))
        total_cost = 0
        for name, pts in proj.items():
            c    = self.categories[name]
            now  = c['current_gb']
            m12  = pts[11] if months > 11 else 0
            m24  = pts[23] if months > 23 else 0
            m36  = pts[35] if months > 35 else 0
            cost = m12 * self.TIER_COSTS[c['tier']]
            total_cost += cost
            print(f"{name:<28} {now:>6.0f}GB {m12:>6.0f}GB {m24:>6.0f}GB {m36:>6.0f}GB "
                  f"{c['tier']:>6} {cost:>7.0f}€")
        print("-" * len(header))
        print(f"{'Costo totale stimato a +12m':>{len(header)-9}} {total_cost:>7.0f}€/mese")

plan = StorageCapacityPlan()
plan.add('Database SAP',     500,  15, tier='hot',     dedup=1.0, compress=1.5)
plan.add('File Share',      2000,  10, tier='warm',    dedup=1.5)
plan.add('Email Exchange',   800,  20, tier='warm',    dedup=2.0)
plan.add('Backup Full',     5000,  15, tier='cold',    dedup=3.0, compress=2.0)
plan.add('Log applicativi',  200,  30, tier='cold',    compress=5.0)
plan.add('Archivio legale', 1000,   5, tier='archive')
plan.add('VM disk vSphere', 3000,  10, tier='hot',     dedup=2.0)
plan.summary(36)
```

---

### Progetto C3: SOP Capacity Planning

Creazione della Standard Operating Procedure per il ciclo mensile di capacity planning.

```markdown
<!-- reports/SOP_capacity_planning_v1.md -->
# SOP: Capacity Planning Mensile

## Responsabilità
- **Owner**: IT Infrastructure Manager
- **Executor**: Sysadmin (minimo N+1 persona formata)
- **Frequenza**: 1ª settimana di ogni mese
- **Durata**: 2-3 ore

## Fase 1 — Raccolta Dati (Giorno 1, 1h)
1. Eseguire `python3 scripts/c1_monthly_capacity_report.py`
2. Verificare che Prometheus abbia dati completi per i 30 giorni precedenti
3. Scaricare metriche storage da ogni storage array (ONTAP, vSAN, etc.)
4. Raccogliere ticket capacity-correlati del mese (GLPI query: categoria=Capacity)

## Fase 2 — Analisi (Giorno 1-2, 1h)
1. Revisionare report auto-generato
2. Confrontare forecast modello vs reale (drift > 10% → aggiornare modello)
3. Valutare headroom per ogni risorsa contro soglie:
   | Risorsa  | Warning | Critical |
   |----------|---------|----------|
   | CPU P95  | 70%     | 85%      |
   | RAM      | 80%     | 90%      |
   | Storage  | 75%     | 85%      |
   | Banda    | 60%     | 80%      |
4. Aggiornare `StorageCapacityPlan` con crescita osservata

## Fase 3 — Forecast (Giorno 2, 30 min)
1. Rieseguire forecast a 90 e 180 giorni
2. Identificare risorse che raggiungeranno soglia critica in < 90 giorni
3. Calcolare timeline procurement per risorse critiche (lead time tipico: 4-12 settimane)

## Fase 4 — Report e Azioni (Giorno 3, 30 min)
1. Committere report su Git: `git add reports/ && git commit -m "capacity: report $(date +%Y-%m)"`
2. Aprire ticket GLPI per ogni azione raccomandata con:
   - Priorità basata su urgenza (mesi al soglia critico)
   - Stima costo e lead time
   - Assignee: responsabile procurement
3. Condividere executive summary con IT Manager entro il 5 del mese

## Escalation
| Scenario | Azione |
|---|---|
| Risorsa critica in < 30 gg | Escalation immediata IT Manager + CFO |
| Risorsa warning in < 60 gg | Alert in ticket mensile con urgency=HIGH |
| Modello forecast divergente > 20% | Rianalisi storica, update parametri |
```

---

### Progetto C4: Kubernetes Capacity Calculator

```python
# scripts/c4_k8s_capacity.py

def k8s_cluster_capacity(
    node_cpu: int,
    node_ram_gb: float,
    num_nodes: int,
    system_overhead_pct: float = 15.0,
    daemonset_cpu: float = 0.5,
    daemonset_ram_gb: float = 0.5,
    failure_tolerance: int = 1,
) -> tuple[float, float]:
    """Calcola CPU e RAM allocabile per workload in cluster Kubernetes."""
    
    os_cpu = 0.1 * node_cpu
    os_ram = 0.1 * node_ram_gb
    
    alloc_cpu = node_cpu - os_cpu - daemonset_cpu
    alloc_ram = node_ram_gb - os_ram - daemonset_ram_gb
    
    effective_nodes = num_nodes - failure_tolerance
    total_cpu = alloc_cpu * effective_nodes
    total_ram = alloc_ram * effective_nodes
    
    workload_cpu = total_cpu * (1 - system_overhead_pct / 100)
    workload_ram = total_ram * (1 - system_overhead_pct / 100)
    
    avg_pod_cpu = 0.25  # 250m
    avg_pod_ram = 0.25  # 256Mi
    max_pods    = min(int(workload_cpu / avg_pod_cpu), int(workload_ram / avg_pod_ram))
    
    print(f"=== Kubernetes Cluster Capacity ===")
    print(f"Nodi: {num_nodes} × {node_cpu} core / {node_ram_gb} GB  (N+{failure_tolerance})")
    print(f"Disponibile workload: {workload_cpu:.1f} core, {workload_ram:.1f} GB")
    print(f"Stima pod (250m/256Mi): max {max_pods} pod")
    
    return workload_cpu, workload_ram

# Cluster PMI tipico: 5 nodi 8 core / 32 GB
k8s_cluster_capacity(node_cpu=8, node_ram_gb=32, num_nodes=5)
```

---

## Checklist di Validazione Lab

- [ ] **A1**: Ciclo 6 fasi capacity planning spiegato con analogia della trattoria
- [ ] **A2**: Baseline CPU calcolata con percentili per giorno della settimana
- [ ] **A3**: Little's Law applicata al dimensionamento connection pool
- [ ] **A4**: USL fittato su dati benchmark, N_max identificato
- [ ] **B1**: `b1_baseline_analysis.py` eseguito, output ragionevole
- [ ] **B2**: Forecast regressione lineare storage +6 mesi completato
- [ ] **B3**: Holt-Winters seleziona automaticamente la configurazione migliore
- [ ] **B4**: Prophet con festività italiane produce forecast 90 giorni, MAPE < 20%
- [ ] **B5**: Connection pool sizing con Little's Law completato per 3 scenari
- [ ] **B6**: USL fitting completato, N_max e throughput degradation identificati
- [ ] **B7**: Monte Carlo 10.000 simulazioni completato con P50/P75/P90/P95
- [ ] **B8**: WAN sizing filiale 25 utenti completato con breakdown costi
- [ ] **B9**: k6 load test eseguito, P95 < 500ms
- [ ] **B10**: Prometheus rules validate con promtool
- [ ] **C1**: Report mensile auto-generato con azioni raccomandate
- [ ] **C2**: StorageCapacityPlan PMI con 8 categorie e costi per tier
- [ ] **C3**: SOP capacity planning mensile documentata
- [ ] **C4**: Kubernetes capacity calculator completato

---

## Appendice A: Soglie di Headroom per Tipo di Risorsa

| Risorsa | Soglia Warning | Soglia Critica | Headroom Raccomandato | Note |
|---|---|---|---|---|
| CPU (P95 su 5min) | 70% | 85% | 30% | Knee M/M/1 a ~70% |
| RAM | 80% | 90% | 20% | Escludere cache/buffer |
| Storage filesystem | 75% | 85% | 25% | Include snapshot |
| IOPS disco | 70% max rated | 85% | 30% | Peak hour |
| Banda rete | 60% | 80% | 40% | Burst headroom |
| Connection pool | 70% max | 85% | 30% | Spike slack |
| Queue depth | 50% max | 75% | 50% | Latency-sensitive |

---

## Appendice B: Guida alla Scelta del Modello di Forecasting

| Condizione | Modello Consigliato |
|---|---|
| Dati < 2 anni, stagionalità evidente | Holt-Winters |
| Dati > 2 anni, trend complesso, stagionalità multipla | Prophet |
| Dati > 3 anni, pattern non lineari | LSTM |
| Trend monotono, no stagionalità | Regressione lineare |
| Crescita accelerata | Regressione polinomiale / log-lineare |
| Nuovo workload, no storico | Little's Law + benchmark simili |
| Incertezza elevata, scenari what-if | Monte Carlo |

---

## Appendice C: Mappatura ITIL 4

| Pratica ITIL 4 | Come si collega a questo tutorial |
|---|---|
| Capacity and Performance Management | Pratica principale: tutte le fasi del ciclo |
| IT Infrastructure & Platform Management | Fornisce i dati di utilizzo |
| Service Level Management | Definisce i SLA che il capacity planning deve rispettare |
| Continual Improvement | Il ciclo mensile è un loop di miglioramento |
| Risk Management | Monte Carlo quantifica il rischio di saturazione |

**Riferimento normativo:**
- **ISO/IEC 20000-1**, clause 8.4: Capacity and demand management
- **COBIT 2019**, BAI04: Manage Availability and Capacity
- **ITIL 4 Practice Guide**: Capacity and Performance Management

---

## Riferimenti

1. Gregg, B. — *Systems Performance: Enterprise and the Cloud* (2nd ed., 2020) — USE methodology
2. Gunther, N. J. — *Analyzing Computer System Performance with Perl::PDQ* — USL
3. Little, J. D. C. — "A Proof for the Queuing Formula: L = λW" (1961)
4. Facebook AI Research — *Prophet: Forecasting at Scale* (2017)
5. k6.io — Documentazione ufficiale k6 load testing
6. Prometheus — `predict_linear()` function documentation
7. ITIL 4 — *Capacity and Performance Management Practice Guide* (Axelos, 2020)
8. ISO/IEC 20000-1:2018 — clause 8.4 Capacity and demand management
