# Capacity Planning IT — Tecniche, Forecasting, Strumenti

> **Modulo 15** · **Tempo:** 90 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Little's Law (L = λW): foundation of queue theory.**
2. **p95/p99 latency conta piu della media.** La media nasconde tail.
3. **Saturation vs utilization: confondere costa $.** Saturation > 70% richiede investigazione.
4. **Forecasting trend 3-6 mesi prima di esaurire capacity.** Peak day modeling per Black Friday.


Il capacity planning rappresenta la disciplina ingegneristica che traduce la domanda di business in risorse infrastrutturali concrete, con l'obiettivo di garantire che CPU, RAM, storage, banda di rete, IOPS e licenze siano sempre allineati al carico previsto, evitando contemporaneamente l'over-provisioning costoso e l'under-provisioning rischioso. In un contesto PMI italiano dove il budget IT viene scrutinato voce per voce e ogni euro speso in hardware non utilizzato e un euro sottratto ad altre iniziative, un programma di capacity planning maturo permette di pianificare investimenti su orizzonte 12-36 mesi con margini di errore inferiori al 15%, anziche reagire alle emergenze di saturazione. Questa guida copre i fondamenti teorici, le tecniche di forecasting statistico e machine learning, gli strumenti operativi sia commerciali sia open source, e fornisce esempi pratici tarati sulla realta italiana.

---

## Indice

1. [Panoramica](#panoramica)
2. [Concetti Fondamentali](#concetti-fondamentali)
3. [Guida Pratica](#guida-pratica)
4. [Configurazione](#configurazione)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Riferimenti](#riferimenti)

---

## Panoramica

### Definizione di Capacity Planning

Il capacity planning IT e il processo continuo e iterativo di garantire che le risorse infrastrutturali (compute, storage, networking, licenze, personale operativo) siano dimensionate per soddisfare la domanda futura di business con il livello di servizio concordato, al costo totale piu basso possibile. Non e una attivita una tantum eseguita all'acquisto del nuovo server, ma un ciclo permanente di osservazione, analisi, previsione e azione che accompagna l'intero ciclo di vita dell'infrastruttura.

La definizione operativa che adottiamo include tre vincoli simultanei: il livello di servizio (SLA, tempi di risposta, disponibilita), il costo (CAPEX, OPEX, licenze), il tempo (lead time per acquisto e deployment, tipicamente 6-12 settimane per hardware enterprise). Quando uno di questi vincoli viene violato, il capacity planning ha fallito: o il servizio si degrada per saturazione, o si spende inutilmente per risorse inattive, o si va in emergenza con acquisti urgenti a prezzi maggiorati.

### Capacity Management vs Performance Management

Capacity management e performance management vengono spesso confusi ma rispondono a domande diverse. Il performance management chiede "i tempi di risposta attuali sono accettabili?" e si occupa di tuning, ottimizzazione query, caching, profiling applicativo. Il capacity management chiede "le risorse saranno sufficienti tra 6-12 mesi?" e si occupa di forecasting della domanda, dimensionamento hardware, pianificazione acquisti.

Le due discipline si alimentano a vicenda: ottimizzazioni di performance riducono il fabbisogno di capacity (un indice che dimezza il tempo di una query riduce la pressione su CPU e IOPS), mentre piani di capacity inadeguati generano problemi di performance. Una organizzazione matura tratta le due come funzioni distinte ma coordinate, con team che condividono dashboard e linguaggi comuni.

### Livelli di Capacity Planning

Il capacity planning si articola su tre livelli gerarchici, ciascuno con orizzonte temporale e granularita differenti.

**Business Level**: parte dai driver di business come numero di utenti attivi, transazioni giornaliere, fatturato previsto, nuovi clienti acquisiti, lancio di nuove linee di prodotto. L'orizzonte e tipicamente 12-36 mesi e il dialogo avviene con la direzione commerciale e il CFO. Una catena di negozi che prevede di aprire 15 nuovi punti vendita nel prossimo anno deve tradurre questo in ulteriori 15 connessioni VPN, 15 set di POS, 15 stampanti, capacity aggiuntiva sul server centrale per gestire le transazioni.

**Service Level**: traduce i driver di business in metriche di servizio come transazioni al secondo, latenza P95 delle API, throughput backup, sessioni concorrenti. L'orizzonte e 6-18 mesi e il dialogo avviene con i product owner e gli application owner. Per un ERP, ad esempio, si stima che 100 utenti concorrenti generano 250 transazioni/secondo di picco con latenza target P95 inferiore a 800ms.

**Component Level**: scompone le metriche di servizio nei requisiti di componente come core CPU, GB RAM, IOPS storage, Mbps di banda, connessioni database. L'orizzonte e 3-12 mesi e il dialogo avviene con il team infrastrutturale. Le 250 transazioni/secondo dell'ERP si traducono in approssimativamente 12 vCPU sostenuti, 48 GB RAM, 4.000 IOPS storage, 80 Mbps di traffico LAN interno.

### Modello Iterativo

Il capacity planning maturo segue un ciclo iterativo a sei fasi che si ripete con cadenza mensile o trimestrale a seconda della maturita dell'organizzazione: monitor, analyze, forecast, plan, implement, review. Ciascuna fase produce output documentati che alimentano la successiva.

La fase **monitor** raccoglie metriche raw da tutte le fonti (sistemi operativi, hypervisor, database, applicazioni, networking, storage array) con granularita appropriata (1-5 minuti per metriche operative, 1 ora per analisi capacity). La fase **analyze** aggrega, normalizza, identifica pattern e anomalie. La fase **forecast** applica modelli statistici per proiettare la domanda futura. La fase **plan** definisce le azioni concrete (ordini hardware, modifiche cloud, ottimizzazioni). La fase **implement** esegue le azioni pianificate. La fase **review** verifica l'accuratezza delle previsioni precedenti e affina i modelli.

### Integrazione con ITIL 4 e Framework di Governance

Il capacity planning si inserisce nel framework ITIL 4 come parte della practice **Capacity and Performance Management**, una delle 17 Service Management Practices. In questo contesto, il capacity planning non opera in isolamento ma interagisce con altre practices chiave:

- **Change Enablement**: ogni azione capacity (upgrade, scale-out, migrazione) e un change che segue il processo standard
- **Service Level Management**: i capacity target derivano direttamente dagli SLA concordati con il business
- **Financial Management**: il capacity plan alimenta il budget IT e le proiezioni CAPEX/OPEX
- **Continual Improvement**: il ciclo review del capacity planning genera input per il CIR (Continual Improvement Register)
- **Service Continuity Management**: il capacity planning include scenari di failover e disaster recovery

Per organizzazioni che seguono ISO/IEC 20000-1:2018, il capacity planning e un requisito esplicito della clausola 8.4 "Capacity management". Per organizzazioni certificate ISO 27001, il capacity planning supporta il controllo A.8.6 "Capacity management" dell'Annex A.

La relazione con COBIT 2019 si esprime attraverso il processo BAI04 "Manage Availability and Capacity", che richiede di "gestire la disponibilita e la capacity delle risorse per garantire che i servizi IT supportino i processi di business".

---

## Concetti Fondamentali

### Baseline Establishment

Stabilire una baseline affidabile e il prerequisito per qualsiasi forecasting credibile. Una baseline e la rappresentazione statistica del comportamento "normale" di una risorsa, costruita su un periodo sufficientemente lungo da catturare la variabilita naturale. La regola pratica richiede minimo 3 mesi di dati per workload stabili, 6-12 mesi per workload con stagionalita marcata.

La baseline non e un singolo numero ma una distribuzione: per ogni metrica si calcolano media, mediana, percentili (P50, P75, P90, P95, P99), deviazione standard, minimo e massimo. Il P95 della CPU su finestra di 5 minuti rappresenta tipicamente il valore di riferimento per dimensionamento, perche cattura i picchi sostenuti escludendo gli outlier momentanei.

**Costruzione della Baseline — Procedura Operativa**

La costruzione di una baseline robusta richiede un approccio metodico che distingua segnale da rumore.

1. **Raccolta dati raw**: configurare monitoring con granularita 1-5 minuti per tutte le risorse target (CPU, RAM, IOPS, banda, latenza). Strumenti: Prometheus (scrape interval 15-30s), Zabbix (polling 60s), PRTG (scan interval 60s), CloudWatch (1-5min).

2. **Pulizia dati**: rimuovere periodi anomali noti (downtime pianificati, incidenti, test di carico, migrazioni). Marcare gli outlier ma non eliminarli ciecamente — un outlier puo essere un picco reale che il forecasting deve catturare.

3. **Normalizzazione temporale**: allineare i dati a timezone italiana (CET/CEST), considerando l'impatto del cambio ora (ultimo weekend di marzo e ottobre). Aggregare a granularita coerente: 5 minuti per analisi operativa, 1 ora per trend settimanale, 1 giorno per trend mensile.

4. **Calcolo statistiche**: per ogni risorsa e ogni finestra temporale, calcolare la distribuzione completa:

```python
import pandas as pd
import numpy as np

def compute_baseline(df: pd.DataFrame, metric_col: str) -> dict:
    """Calcola baseline completa per una metrica."""
    return {
        'mean': df[metric_col].mean(),
        'median': df[metric_col].median(),
        'std': df[metric_col].std(),
        'min': df[metric_col].min(),
        'max': df[metric_col].max(),
        'p50': df[metric_col].quantile(0.50),
        'p75': df[metric_col].quantile(0.75),
        'p90': df[metric_col].quantile(0.90),
        'p95': df[metric_col].quantile(0.95),
        'p99': df[metric_col].quantile(0.99),
        'coefficient_of_variation': df[metric_col].std() / df[metric_col].mean(),
        'skewness': df[metric_col].skew(),
        'samples': len(df),
        'period_start': df.index.min(),
        'period_end': df.index.max(),
    }

# Esempio: baseline CPU cluster per giorno della settimana
for day in range(7):
    day_data = df[df.index.dayofweek == day]
    baseline = compute_baseline(day_data, 'cpu_pct')
    print(f"Giorno {day}: P95={baseline['p95']:.1f}%, Media={baseline['mean']:.1f}%")
```

5. **Validazione**: confrontare la baseline con le osservazioni correnti. Se la baseline P95 CPU e 65% ma oggi il P95 e 82%, indagare prima di aggiornare il modello — potrebbe essere un cambio di regime, non rumore.

6. **Documentazione**: registrare la baseline con periodo di riferimento, condizioni, assunzioni. La baseline ha una scadenza: ricalcolare ogni 3-6 mesi o dopo eventi significativi (rilascio nuova versione applicativa, migrazione infrastrutturale, acquisizione nuovo cliente).

**Identificazione della Seasonality**

La stagionalita e onnipresente in quasi ogni workload IT e ignorarla porta a previsioni sistematicamente sbagliate. Le forme tipiche includono:

- **Stagionalita giornaliera**: picchi durante orario lavorativo (9:00-18:00 in Italia), quiete notturna, picchi serali per applicazioni B2C
- **Stagionalita settimanale**: lunedi e venerdi spesso anomali (apertura/chiusura settimana), weekend ridotto per applicazioni B2B
- **Stagionalita mensile**: fine mese pesante per gestionali e commercialisti (chiusure contabili), inizio mese per fatturazione ricorrente
- **Stagionalita annuale**: Black Friday e Natale per e-commerce (picchi di 5-10x), prima settimana di settembre per applicazioni scolastiche, agosto basso per B2B italiano (ferie), gennaio alto per CRM (pianificazione commerciale)
- **Eventi straordinari**: lanci prodotto, campagne marketing, scadenze fiscali (16 del mese F24, 730 in primavera, dichiarazione redditi in autunno)

L'identificazione della stagionalita avviene con tecniche come decomposizione STL (Seasonal-Trend decomposition using Loess), che separa una serie temporale nelle componenti trend, stagionalita, residuo. In Python con statsmodels:

```python
from statsmodels.tsa.seasonal import STL
import pandas as pd

df = pd.read_csv('cpu_usage.csv', parse_dates=['timestamp'], index_col='timestamp')
stl = STL(df['cpu_pct'], period=24*7, robust=True)  # period in ore per stagionalita settimanale
result = stl.fit()
result.plot()
```

**Decomposizione Avanzata con Multiple Seasonality**

Per workload con stagionalita multiple (giornaliera + settimanale + mensile + annuale), STL standard non e sufficiente. Si usa MSTL (Multiple Seasonal-Trend decomposition using Loess) disponibile in statsmodels 0.14+:

```python
from statsmodels.tsa.seasonal import MSTL

# Dati orari con stagionalita giornaliera (24h) e settimanale (168h)
mstl = MSTL(df['cpu_pct'], periods=[24, 168], stl_kwargs={'robust': True})
result = mstl.fit()

# result.trend = trend a lungo termine
# result.seasonal[0] = componente giornaliera
# result.seasonal[1] = componente settimanale
# result.resid = residuo
result.plot()
```

Per identificare automaticamente i periodi di stagionalita senza conoscenza a priori, si usa l'autocorrelazione:

```python
from statsmodels.tsa.stattools import acf
import matplotlib.pyplot as plt

# ACF su 7 giorni di dati orari
acf_values = acf(df['cpu_pct'], nlags=168*2)
plt.stem(range(len(acf_values)), acf_values)
plt.xlabel('Lag (ore)')
plt.ylabel('Autocorrelazione')
plt.title('ACF per identificazione stagionalita')
plt.show()
# Picchi a lag 24 e 168 confermano stagionalita giornaliera e settimanale
```

### Workload Characterization

Caratterizzare un workload significa descriverlo in modo quantitativo lungo due dimensioni: intensita e pattern. L'**intensita** misura quanto carico arriva al sistema (arrival rate, transactions/sec, request/sec, IOPS, GB/giorno scritti). Il **pattern** descrive la composizione del carico (mix di operazioni read/write, mix di tipi di transazioni OLTP brevi vs analitiche lunghe, dimensione media payload).

Due workload con la stessa intensita media ma pattern diversi richiedono dimensionamenti completamente diversi. Un database con 1.000 tps composti da query OLTP <50ms e CPU-bound; lo stesso database con 1.000 tps di cui il 10% sono query analitiche da 30 secondi e contemporaneamente CPU-bound, memory-bound e IOPS-bound.

**Workload Classification Matrix**

Per un capacity planner, classificare i workload consente di applicare modelli appropriati. La matrice seguente copre i pattern piu comuni in ambienti PMI italiani:

| Tipo Workload | Dimensione Primaria | Dimensione Secondaria | Pattern Tipico | Esempio PMI |
|---|---|---|---|---|
| OLTP transazionale | CPU | IOPS (random read) | Burst brevi, latency-sensitive | Gestionale SAP B1, Fatturazione |
| Batch processing | CPU | IOPS (sequential) | Picchi programmati, throughput | Chiusura contabile, MRP |
| File server | IOPS (random) | Banda | Costante durante orario | FileServer dipartimentale |
| Database analitico | Memoria | CPU | Query lunghe, burst sporadici | PowerBI, Metabase queries |
| Email server | IOPS (random) | Memoria | Picco mattina 8-10, costante | Exchange On-Prem / IMAP |
| Web server | Banda/CPU | Memoria | Segue traffico utenti | Sito aziendale, e-commerce |
| Backup | Banda (sequential) | IOPS (sequential) | Finestra notturna 22-06 | Veeam, Borg Backup |
| VDI | Memoria | CPU | Boot storm mattina 8-9 | Citrix, VMware Horizon |
| Video conferencing | Banda (realtime) | CPU | Picchi riunioni 10-12, 14-16 | Teams, Zoom gateway |
| IoT/telemetria | IOPS (write) | Storage | Costante, crescita lineare | Sensori produzione, SCADA |

**Workload Profiling Pratico**

Per profilare un workload in modo operativo, raccogliere le seguenti metriche per almeno 2 settimane complete (includendo almeno un fine mese per workload gestionali):

```bash
#!/bin/bash
# workload_profile.sh - Raccolta profilo workload per capacity planning
# Eseguire ogni 5 minuti via cron

TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
HOST=$(hostname)
OUTPUT_DIR=/var/log/capacity_profile
mkdir -p "$OUTPUT_DIR"
OUTPUT="$OUTPUT_DIR/profile_$(date +%Y%m%d).csv"

# Header (solo prima esecuzione del giorno)
if [ ! -f "$OUTPUT" ]; then
    echo "timestamp,host,cpu_user,cpu_sys,cpu_iowait,cpu_idle,mem_total_mb,mem_used_mb,mem_available_mb,swap_used_mb,disk_read_iops,disk_write_iops,disk_read_mbps,disk_write_mbps,net_rx_mbps,net_tx_mbps,load_avg_1m,load_avg_5m,load_avg_15m,tcp_connections,processes" > "$OUTPUT"
fi

# CPU (da /proc/stat, media 5 secondi)
CPU_STATS=$(mpstat 5 1 | tail -1 | awk '{print $3","$5","$6","$12}')

# Memoria
MEM_TOTAL=$(free -m | awk '/Mem:/ {print $2}')
MEM_USED=$(free -m | awk '/Mem:/ {print $3}')
MEM_AVAIL=$(free -m | awk '/Mem:/ {print $7}')
SWAP_USED=$(free -m | awk '/Swap:/ {print $3}')

# IOPS e throughput disco (richiede iostat)
DISK_STATS=$(iostat -d -x 5 1 | awk '/sda|nvme0n1/ {print $4","$5","$6","$7}' | head -1)

# Rete
NET_RX=$(cat /proc/net/dev | awk '/eth0|ens/ {print $2}')
NET_TX=$(cat /proc/net/dev | awk '/eth0|ens/ {print $10}')

# Load average
LOAD=$(awk '{print $1","$2","$3}' /proc/loadavg)

# Connessioni TCP
TCP_CONN=$(ss -s | awk '/TCP:/ {print $2}')

# Processi
PROCS=$(ps aux | wc -l)

echo "$TIMESTAMP,$HOST,$CPU_STATS,$MEM_TOTAL,$MEM_USED,$MEM_AVAIL,$SWAP_USED,$DISK_STATS,0,0,$LOAD,$TCP_CONN,$PROCS" >> "$OUTPUT"
```

### Forecasting Techniques

Le tecniche di forecasting si distribuiscono lungo uno spettro di complessita crescente, da semplici regressioni lineari fino a modelli ML sofisticati. La regola pratica per la scelta:

- **Dati <2 anni, stagionalita evidente**: Holt-Winters (triple exponential smoothing)
- **Dati >2 anni, trend complesso, stagionalita multipla**: Prophet (Facebook) o ARIMA/SARIMA
- **Dati >3 anni, pattern non lineari, eventi esogeni**: LSTM o Gradient Boosting con feature engineering
- **Workload nuovi senza storico**: regressione lineare sui driver di business + benchmark da workload simili

**Regressione Lineare**

Tecnica piu semplice, adatta a trend monotoni senza stagionalita. Adeguata per crescita storage filesystem in molti casi PMI. In Python:

```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

X = np.array(range(len(monthly_storage_gb))).reshape(-1, 1)
y = np.array(monthly_storage_gb)
model = LinearRegression().fit(X, y)
forecast_12m = model.predict(np.array(range(len(y), len(y)+12)).reshape(-1, 1))

# Metriche di qualita del modello
y_pred = model.predict(X)
r2 = r2_score(y, y_pred)
mae = mean_absolute_error(y, y_pred)
print(f"R2: {r2:.3f}, MAE: {mae:.2f} GB, Slope: {model.coef_[0]:.2f} GB/mese")
print(f"Previsione +12 mesi: {forecast_12m[-1]:.0f} GB")

# Intervallo di confidenza (approssimato)
residuals_std = np.std(y - y_pred)
ci_upper = forecast_12m + 1.96 * residuals_std
ci_lower = forecast_12m - 1.96 * residuals_std
```

**Regressione Polinomiale e Crescita Esponenziale**

Quando la crescita non e lineare (accelerazione del traffico, crescita compounding dei dati), si usa regressione polinomiale o trasformazione logaritmica:

```python
from sklearn.preprocessing import PolynomialFeatures

# Regressione polinomiale grado 2 (crescita accelerata)
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X)
model_poly = LinearRegression().fit(X_poly, y)
forecast_poly = model_poly.predict(poly.transform(np.array(range(len(y), len(y)+12)).reshape(-1, 1)))

# Crescita esponenziale (log-linear)
y_log = np.log(y)
model_exp = LinearRegression().fit(X, y_log)
forecast_exp = np.exp(model_exp.predict(np.array(range(len(y), len(y)+12)).reshape(-1, 1)))

# Confronto modelli
for name, forecast in [('Lineare', forecast_12m), ('Polinomiale', forecast_poly), ('Esponenziale', forecast_exp)]:
    print(f"{name}: +6m = {forecast[5]:.0f} GB, +12m = {forecast[11]:.0f} GB")
```

**Time Series ARIMA/SARIMA**

ARIMA (AutoRegressive Integrated Moving Average) e SARIMA (Seasonal ARIMA) sono i cavalli di battaglia statistici. Richiedono dati stazionari (differenziati se necessario) e una scelta dei parametri (p, d, q) e (P, D, Q, s) tramite analisi ACF/PACF o auto-tuning. Implementazione standard con statsmodels:

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

model = SARIMAX(df['cpu_pct'],
                order=(1,1,1),
                seasonal_order=(1,1,1,24*7),
                enforce_stationarity=False)
fit = model.fit(disp=False)
forecast = fit.forecast(steps=24*30)  # 30 giorni avanti
```

**Auto ARIMA con pmdarima**

Per automatizzare la selezione dei parametri ARIMA, evitando il tedioso processo manuale di analisi ACF/PACF:

```python
import pmdarima as pm

# Auto ARIMA con ricerca parametri ottimali
auto_model = pm.auto_arima(
    df['cpu_pct'],
    seasonal=True,
    m=168,  # stagionalita settimanale (dati orari)
    stepwise=True,  # ricerca stepwise (piu veloce di grid search)
    suppress_warnings=True,
    error_action='ignore',
    trace=True,  # mostra il progresso della ricerca
    max_p=5, max_q=5,
    max_P=2, max_Q=2,
    information_criterion='aic',  # AIC per selezione modello
    n_fits=50  # limite ricerche
)

print(auto_model.summary())
forecast, conf_int = auto_model.predict(n_periods=24*30, return_conf_int=True)

# conf_int contiene i limiti inferiore e superiore al 95%
print(f"Forecast +30gg: {forecast[-1]:.1f}% CPU (CI: {conf_int[-1][0]:.1f} - {conf_int[-1][1]:.1f})")
```

**Holt-Winters**

Triple exponential smoothing con componenti livello, trend, stagionalita. Robusto e parsimonioso nei dati richiesti. Eccellente per metriche operative con stagionalita settimanale chiara:

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(df['transactions_per_hour'],
                              seasonal_periods=24*7,
                              trend='add',
                              seasonal='add',
                              damped_trend=True).fit()
forecast = model.forecast(steps=24*30)
```

**Confronto Add vs Mul Seasonality in Holt-Winters**

La scelta tra stagionalita additiva e moltiplicativa impatta significativamente le previsioni:

- **Additiva**: l'ampiezza delle oscillazioni stagionali e costante nel tempo. Adatta quando i picchi crescono linearmente (es. +100 tps ogni weekend)
- **Moltiplicativa**: l'ampiezza cresce proporzionalmente al trend. Adatta quando i picchi crescono percentualmente (es. weekend = +30% rispetto al trend corrente)

```python
# Confronto automatico add vs mul
from sklearn.metrics import mean_absolute_error

results = {}
for trend in ['add', 'mul']:
    for seasonal in ['add', 'mul']:
        try:
            model = ExponentialSmoothing(
                train_data,
                seasonal_periods=24*7,
                trend=trend,
                seasonal=seasonal,
                damped_trend=True
            ).fit(optimized=True)
            pred = model.forecast(len(test_data))
            mae = mean_absolute_error(test_data, pred)
            results[f'{trend}/{seasonal}'] = mae
        except Exception:
            results[f'{trend}/{seasonal}'] = float('inf')

best = min(results, key=results.get)
print(f"Migliore combinazione: {best} (MAE: {results[best]:.2f})")
```

**Prophet**

Sviluppato da Facebook, eccelle con stagionalita multiple, trend con changepoint, holidays personalizzati. Particolarmente adatto a workload italiani con festivita locali:

```python
from prophet import Prophet

df_p = df.reset_index().rename(columns={'timestamp':'ds', 'cpu_pct':'y'})
m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=True)
m.add_country_holidays(country_name='IT')
m.fit(df_p)
future = m.make_future_dataframe(periods=24*90, freq='H')
forecast = m.predict(future)
```

**Prophet Avanzato — Regressori Esogeni e Changepoints**

Prophet consente di aggiungere regressori esterni (numero utenti, campagne marketing, eventi business) e gestire changepoints nel trend:

```python
from prophet import Prophet

m = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=True,
    changepoint_prior_scale=0.05,  # sensibilita changepoint (0.05 = conservativo)
    changepoint_range=0.9,  # cerca changepoint nel primo 90% dei dati
    seasonality_mode='multiplicative',  # per workload con crescita
    interval_width=0.95,  # intervallo di confidenza 95%
)

# Festivita italiane
m.add_country_holidays(country_name='IT')

# Festivita aziendali custom (es. fiera di settore, inventario annuale)
inventario = pd.DataFrame({
    'holiday': 'inventario_annuale',
    'ds': pd.to_datetime(['2024-01-15', '2025-01-15', '2026-01-15']),
    'lower_window': -1,  # impatto 1 giorno prima
    'upper_window': 1,   # impatto 1 giorno dopo
})
m.holidays = pd.concat([m.holidays, inventario]) if m.holidays is not None else inventario

# Regressore esogeno: numero utenti attivi
df_p['active_users'] = df_users['count']
m.add_regressor('active_users')

m.fit(df_p)

# Per il forecast futuro, devo fornire anche i valori futuri del regressore
future = m.make_future_dataframe(periods=24*90, freq='H')
future['active_users'] = predicted_users  # da forecast separato
forecast = m.predict(future)

# Analisi componenti
m.plot_components(forecast)
```

**Valutazione Cross-Validated del Forecast**

La validazione del modello di forecasting e critica per evitare di basare decisioni su modelli inaccurati:

```python
from prophet.diagnostics import cross_validation, performance_metrics

# Cross-validation: train su finestre crescenti, test su 30 giorni
df_cv = cross_validation(
    m,
    initial='365 days',   # training minimo 1 anno
    period='30 days',     # nuova finestra ogni 30 giorni
    horizon='90 days',    # previsione 90 giorni avanti
)

# Metriche di performance
metrics = performance_metrics(df_cv)
print(metrics[['horizon', 'mape', 'mae', 'rmse']].tail())

# MAPE (Mean Absolute Percentage Error) target: <15% per capacity planning accettabile
print(f"MAPE medio: {metrics['mape'].mean()*100:.1f}%")
```

**LSTM e Deep Learning**

Reti neurali ricorrenti (LSTM, GRU) catturano dipendenze non lineari di lungo periodo. Richiedono dataset >3 anni, GPU per training efficiente, competenze ML. Adatti a contesti enterprise con team data science dedicato; sovradimensionati per la maggior parte delle PMI italiane.

```python
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# Preparazione dati per LSTM
def create_sequences(data, seq_length=168):  # 1 settimana di dati orari
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

# Normalizzazione
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df['cpu_pct'].values.reshape(-1, 1))

X, y = create_sequences(scaled_data, seq_length=168)
X = X.reshape(X.shape[0], X.shape[1], 1)

# Modello LSTM
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(168, 1)),
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse')
model.fit(X, y, epochs=50, batch_size=32, validation_split=0.2, verbose=1)

# Forecast
forecast_scaled = []
last_seq = X[-1]
for _ in range(24*30):  # 30 giorni
    pred = model.predict(last_seq.reshape(1, 168, 1), verbose=0)
    forecast_scaled.append(pred[0, 0])
    last_seq = np.append(last_seq[1:], pred, axis=0)

forecast = scaler.inverse_transform(np.array(forecast_scaled).reshape(-1, 1))
```

### Modelli Matematici Fondamentali

**Little's Law**

L = λ × W. Il numero medio di entita in un sistema (L) e uguale al rate di arrivo (λ) moltiplicato per il tempo medio di permanenza (W). Applicazione pratica: se un'API riceve 50 richieste/sec con latenza media 200ms, il numero medio di richieste in flight e 50 × 0.2 = 10. Questo determina il pool di thread necessario, le connessioni database concorrenti, la dimensione delle queue.

**Applicazioni Pratiche di Little's Law**

| Scenario | λ (arrival rate) | W (tempo medio) | L (entita in sistema) | Implicazione |
|---|---|---|---|---|
| Web server | 200 req/s | 100ms | 20 | Pool thread minimo 20 |
| Connection pool DB | 500 query/s | 5ms | 2.5 | Pool 3 connessioni minimo |
| Queue email | 100 msg/min | 30s elaborazione | 50 | Queue buffer 50 messaggi |
| Print server | 20 job/h | 3 min/job | 1 | 1 stampante sufficiente |
| Ticket support | 15 ticket/giorno | 4 ore risoluzione | 7.5 | Backlog medio 8 ticket |
| Build pipeline | 30 build/giorno | 10 min/build | 0.21 | 1 runner sufficiente |

**Esempio completo**: dimensionamento connection pool per microservizio Java:

```python
# Little's Law per connection pool sizing
lambda_rate = 500      # query al secondo
avg_query_time = 0.005 # 5ms media
L = lambda_rate * avg_query_time  # = 2.5 connessioni medie in uso

# Ma serve headroom per varianza:
# - P99 query time: 50ms
L_p99 = lambda_rate * 0.050  # = 25 connessioni al P99

# Formula pratica: pool_size = L_p99 * 1.5 (headroom)
pool_recommended = int(L_p99 * 1.5)
print(f"Pool size raccomandato: {pool_recommended} connessioni")
# Output: Pool size raccomandato: 37 connessioni
```

**Erlang B e Erlang C**

Formule storiche per dimensionamento canali (originariamente telefonia, applicabili a connessioni database, slot VPN, sessioni RDP). Erlang B calcola la probabilita di blocco; Erlang C calcola la probabilita di attesa. Per dimensionare un pool di 50 connessioni database con utilizzo medio 30 Erlang, Erlang B fornisce probabilita di rifiuto, Erlang C fornisce probabilita di accodamento.

```python
import math

def erlang_b(traffic_intensity: float, num_channels: int) -> float:
    """Calcola la probabilita di blocco con Erlang B."""
    numerator = (traffic_intensity ** num_channels) / math.factorial(num_channels)
    denominator = sum(
        (traffic_intensity ** k) / math.factorial(k) for k in range(num_channels + 1)
    )
    return numerator / denominator

def erlang_c(traffic_intensity: float, num_servers: int) -> float:
    """Calcola la probabilita di attesa con Erlang C."""
    eb = erlang_b(traffic_intensity, num_servers)
    return (num_servers * eb) / (num_servers - traffic_intensity * (1 - eb))

# Esempio: 30 Erlang di traffico, quanti canali servono per <1% blocco?
for channels in range(30, 60):
    block_prob = erlang_b(30, channels)
    if block_prob < 0.01:
        print(f"Canali necessari per P(blocco)<1%: {channels} (P={block_prob:.4f})")
        break

# Esempio: 30 Erlang, 40 server, probabilita di attesa?
pw = erlang_c(30, 40)
print(f"P(attesa) con 40 server: {pw:.4f}")
```

**Universal Scalability Law (Gunther)**

USL modella la scalabilita reale dei sistemi includendo due termini di overhead:

C(N) = N / (1 + α(N-1) + βN(N-1))

dove α rappresenta la contention (serializzazione, lock) e β rappresenta la coherence (sincronizzazione tra nodi, cache invalidation). Predice il punto di "negative scalability" oltre il quale aggiungere risorse degrada le performance. Strumento essenziale per dimensionare cluster e identificare quando smettere di scalare orizzontalmente.

**Implementazione USL con Fitting Dati Reali**

```python
import numpy as np
from scipy.optimize import curve_fit

def usl(N, alpha, beta):
    """Universal Scalability Law."""
    return N / (1 + alpha * (N - 1) + beta * N * (N - 1))

# Dati reali da benchmark: N nodi, throughput misurato
nodes = np.array([1, 2, 4, 8, 12, 16, 24, 32])
throughput = np.array([100, 190, 360, 650, 880, 1050, 1100, 1020])

# Normalizzare throughput rispetto a 1 nodo
throughput_norm = throughput / throughput[0]

# Fit del modello USL
popt, pcov = curve_fit(usl, nodes, throughput_norm, p0=[0.01, 0.001])
alpha_fit, beta_fit = popt

print(f"alpha (contention): {alpha_fit:.6f}")
print(f"beta (coherence): {beta_fit:.6f}")

# Punto di scalabilita massima
N_max = int(np.sqrt((1 - alpha_fit) / beta_fit))
C_max = usl(N_max, alpha_fit, beta_fit)
print(f"Scalabilita massima a N={N_max} nodi (throughput relativo: {C_max:.2f}x)")
print(f"Throughput massimo: {C_max * throughput[0]:.0f} tps")

# Proiezione: aggiungere nodi oltre N_max DEGRADA le performance
for n in [N_max-2, N_max, N_max+5, N_max+10, N_max+20]:
    c = usl(n, alpha_fit, beta_fit)
    print(f"  N={n:3d}: throughput relativo = {c:.2f}x ({c*throughput[0]:.0f} tps)")
```

**Queuing Theory M/M/1 e M/M/c**

Modelli di code con arrivi Poisson e tempi di servizio esponenziali. M/M/1 (singolo server) calcola tempo di attesa medio:

W = 1 / (μ - λ)

dove μ e il rate di servizio e λ il rate di arrivo. Mostra il comportamento esplosivo all'avvicinarsi della saturazione: quando l'utilizzo supera l'80% i tempi di attesa crescono geometricamente. Regola d'oro: mai dimensionare per utilizzo medio sostenuto >70%.

**Visualizzazione del Knee Point nella Curva di Utilizzo**

```python
import numpy as np
import matplotlib.pyplot as plt

# M/M/1: tempo di risposta vs utilizzo
utilization = np.linspace(0.01, 0.99, 200)
service_time = 10  # ms
response_time = service_time / (1 - utilization)

plt.figure(figsize=(10, 6))
plt.plot(utilization * 100, response_time, 'b-', linewidth=2)
plt.axvline(x=70, color='green', linestyle='--', label='Soglia 70% - operativa')
plt.axvline(x=80, color='orange', linestyle='--', label='Soglia 80% - warning')
plt.axvline(x=90, color='red', linestyle='--', label='Soglia 90% - critico')
plt.xlabel('Utilizzo (%)')
plt.ylabel('Tempo di Risposta (ms)')
plt.title('M/M/1: Tempo di Risposta vs Utilizzo\n(service time = 10ms)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 200)
plt.annotate('Knee point', xy=(70, service_time/(1-0.70)),
             xytext=(50, 80), arrowprops=dict(arrowstyle='->'))
plt.savefig('mm1_knee_point.png', dpi=150)
plt.show()
```

**M/M/c (Multi-server Queue)**

Per sistemi con piu server in parallelo (pool di thread, cluster di nodi):

```python
import math
from scipy.special import factorial

def mm_c_avg_wait(arrival_rate, service_rate, num_servers):
    """Calcola tempo medio di attesa in coda M/M/c."""
    rho = arrival_rate / (num_servers * service_rate)
    if rho >= 1:
        return float('inf')  # sistema instabile
    
    # Probabilita di 0 entita nel sistema
    sum_term = sum((num_servers * rho)**k / math.factorial(k) for k in range(num_servers))
    last_term = (num_servers * rho)**num_servers / (math.factorial(num_servers) * (1 - rho))
    p0 = 1 / (sum_term + last_term)
    
    # Probabilita di coda (Erlang C)
    pc = ((num_servers * rho)**num_servers * p0) / (math.factorial(num_servers) * (1 - rho))
    
    # Tempo medio in coda
    wq = pc / (num_servers * service_rate * (1 - rho))
    
    # Tempo medio nel sistema
    w = wq + 1 / service_rate
    
    return wq, w, rho

# Esempio: dimensionamento API server
# 500 req/s, service time medio 10ms = service_rate 100 req/s per server
for servers in range(6, 15):
    wq, w, rho = mm_c_avg_wait(500, 100, servers)
    print(f"{servers} server: utilizzo={rho*100:.1f}%, wait_queue={wq*1000:.1f}ms, response={w*1000:.1f}ms")
```

**Simulation Monte Carlo**

Quando la matematica analitica diventa intrattabile (workload complessi, dipendenze multiple, scenari "what-if"), si ricorre a simulazione Monte Carlo. Si generano migliaia di traiettorie con parametri estratti da distribuzioni note e si analizzano le distribuzioni dei risultati. Utile per scenari worst-case (cosa succede se il rate di arrivo raddoppia per 30 minuti) e per stress test pianificati.

```python
import numpy as np

def monte_carlo_capacity(
    current_usage_gb: float,
    growth_rate_mean: float,  # % crescita mensile media
    growth_rate_std: float,   # deviazione standard
    total_capacity_gb: float,
    months_horizon: int = 24,
    num_simulations: int = 10000,
    spike_probability: float = 0.05,  # prob spike mensile
    spike_multiplier_mean: float = 1.5,
    seed: int = 42
) -> dict:
    """Monte Carlo simulation per capacity planning storage."""
    rng = np.random.default_rng(seed)
    trajectories = np.zeros((num_simulations, months_horizon))
    
    for sim in range(num_simulations):
        usage = current_usage_gb
        for month in range(months_horizon):
            # Crescita base (log-normal per evitare valori negativi)
            growth = rng.lognormal(
                mean=np.log(1 + growth_rate_mean/100),
                sigma=growth_rate_std/100
            )
            usage *= growth
            
            # Spike occasionale (es. migrazione dati, nuovo progetto)
            if rng.random() < spike_probability:
                spike = rng.lognormal(
                    mean=np.log(spike_multiplier_mean),
                    sigma=0.2
                )
                usage *= spike
            
            trajectories[sim, month] = usage
    
    # Analisi risultati
    results = {
        'p50_trajectory': np.percentile(trajectories, 50, axis=0),
        'p75_trajectory': np.percentile(trajectories, 75, axis=0),
        'p90_trajectory': np.percentile(trajectories, 90, axis=0),
        'p95_trajectory': np.percentile(trajectories, 95, axis=0),
    }
    
    # Mese in cui si raggiunge l'80% di capacity (mediana e P95)
    threshold_80 = total_capacity_gb * 0.80
    for pct_name, traj in results.items():
        crossing = np.where(traj >= threshold_80)[0]
        if len(crossing) > 0:
            results[f'{pct_name}_months_to_80pct'] = crossing[0] + 1
        else:
            results[f'{pct_name}_months_to_80pct'] = '>24'
    
    return results

# Esempio PMI: 30 TB usati su 50 TB totali, crescita 3%/mese
results = monte_carlo_capacity(
    current_usage_gb=30000,
    growth_rate_mean=3.0,
    growth_rate_std=1.5,
    total_capacity_gb=50000,
    months_horizon=24,
    num_simulations=10000,
    spike_probability=0.05
)

for key, val in results.items():
    if 'months' in key:
        print(f"{key}: {val} mesi")
    elif 'trajectory' in key:
        print(f"{key} a +12m: {val[11]/1000:.1f} TB, +24m: {val[23]/1000:.1f} TB")
```

### Stress Test, Load Test, Soak Test, Spike Test

Quattro tipologie complementari di test che validano il capacity planning teorico contro la realta operativa.

**Load Test**: applica carico crescente progressivo (ramp-up gradient) fino al target nominale per validare che il sistema sostenga il carico previsto con i tempi di risposta concordati. Tipica durata 1-2 ore. Strumenti: k6, JMeter, Gatling, Locust.

**Stress Test**: spinge il sistema oltre i limiti previsti fino al punto di rottura per identificare il collo di bottiglia e il fallback graceful. Risponde a "qual e il massimo carico sostenibile prima del degrado severo?". Durata 30-60 minuti per evitare danni.

**Soak Test (Endurance)**: applica carico nominale per 24-72 ore consecutive per identificare memory leak, esaurimento descriptor file, accumulo log, problemi di garbage collection. Indispensabile prima di andare live con applicazioni nuove.

**Spike Test**: simula incrementi improvvisi di carico (es. da 100 a 500 utenti in 10 secondi) per validare auto-scaling, behavior delle queue, rate limiting. Critico per sistemi B2C esposti a viralita social o picchi promozionali.

**Esempio Completo k6 per Load Test con Scenari Multipli**

```javascript
// load_test_ecommerce.js — test di carico per e-commerce italiano
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const latencyP95 = new Trend('latency_p95');
const orderSuccessCounter = new Counter('orders_success');

// Scenari multipli per simulare workload reale
export const options = {
  scenarios: {
    // Scenario 1: traffico base browsing
    browse: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '5m', target: 50 },   // ramp-up
        { duration: '30m', target: 50 },   // steady state
        { duration: '5m', target: 0 },     // ramp-down
      ],
      gracefulRampDown: '30s',
      exec: 'browseCatalog',
    },
    // Scenario 2: picco checkout (Black Friday simulation)
    checkout_spike: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1m',
      preAllocatedVUs: 200,
      stages: [
        { duration: '2m', target: 10 },    // baseline
        { duration: '1m', target: 200 },   // spike!
        { duration: '10m', target: 200 },  // sustained peak
        { duration: '2m', target: 10 },    // recovery
      ],
      exec: 'processCheckout',
    },
    // Scenario 3: API search hammering
    search: {
      executor: 'constant-arrival-rate',
      rate: 100,
      timeUnit: '1s',
      duration: '30m',
      preAllocatedVUs: 50,
      exec: 'searchProducts',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    errors: ['rate<0.05'],        // meno del 5% errori
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'https://staging.ecommerce.it';

export function browseCatalog() {
  const res = http.get(`${BASE_URL}/api/products?page=1&limit=20`);
  check(res, { 'catalog 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
  latencyP95.add(res.timings.duration);
  sleep(Math.random() * 3 + 1);  // think time 1-4 secondi
}

export function processCheckout() {
  const payload = JSON.stringify({
    items: [{ sku: 'PROD-001', qty: 1 }],
    shipping: 'standard',
  });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post(`${BASE_URL}/api/checkout`, payload, params);
  
  if (res.status === 200 || res.status === 201) {
    orderSuccessCounter.add(1);
  }
  check(res, { 'checkout success': (r) => r.status === 200 || r.status === 201 });
  errorRate.add(res.status >= 400);
}

export function searchProducts() {
  const queries = ['scarpe', 'giacca', 'pantaloni', 'borsa', 'accessori'];
  const q = queries[Math.floor(Math.random() * queries.length)];
  const res = http.get(`${BASE_URL}/api/search?q=${q}`);
  check(res, { 'search 200': (r) => r.status === 200 });
  errorRate.add(res.status !== 200);
}
```

```bash
# Esecuzione del load test
k6 run --out json=results.json load_test_ecommerce.js

# Con output Prometheus (per integrazione dashboard Grafana)
k6 run --out experimental-prometheus-rw load_test_ecommerce.js
```

### Metodologia USE (Utilization, Saturation, Errors)

Brendan Gregg ha introdotto la metodologia USE per l'analisi sistematica delle risorse. Per ogni risorsa fisica (CPU, disco, NIC, controller) si misurano tre metriche:

- **Utilization**: percentuale del tempo in cui la risorsa e occupata (o throughput relativo alla capacita). Es. CPU utilization 75%.
- **Saturation**: grado di lavoro in eccesso che la risorsa non puo servire immediatamente — tipicamente misurato come lunghezza della coda. Es. CPU run queue length > 2× numero core.
- **Errors**: conteggio degli errori della risorsa. Es. disk errors, network retransmissions, ECC memory errors.

Tabella USE per risorse comuni:

| Risorsa | Utilization | Saturation | Errors |
|---|---|---|---|
| CPU | `mpstat`, `top`, `node_cpu_*` | Run queue `vmstat r`, load average | MCE events `/var/log/mcelog` |
| Memoria | `free`, `MemAvailable` | Swap in/out, OOM kills | ECC errors `edac-util` |
| Disco | `iostat %util` | `avgqu-sz`, `await` | SMART errors `smartctl` |
| Rete | `ifstat`, `rx/tx bytes` | `ifconfig overruns`, `ss` recv-Q | `ifconfig errors`, `ethtool -S` |
| File descriptors | `lsof | wc -l` / `ulimit -n` | processi in attesa di fd | `errno EMFILE` nei log |
| Connessioni TCP | Connessioni attive / `somaxconn` | `ss` send-Q, recv-Q | Retransmissions `netstat -s` |

### Metodologia RED (Rate, Errors, Duration) per Servizi

Complementare alla USE, la metodologia RED si applica ai servizi (anziche alle risorse):

- **Rate**: richieste al secondo servite
- **Errors**: percentuale di richieste fallite
- **Duration**: distribuzione dei tempi di risposta (P50, P95, P99)

```yaml
# Prometheus recording rules per RED metrics
groups:
  - name: red_metrics
    interval: 30s
    rules:
      # Rate
      - record: service:requests_per_second:rate5m
        expr: sum(rate(http_requests_total[5m])) by (service)
      
      # Errors
      - record: service:error_rate:ratio5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
          /
          sum(rate(http_requests_total[5m])) by (service)
      
      # Duration P95
      - record: service:latency_p95:histogram5m
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))
      
      # Duration P99
      - record: service:latency_p99:histogram5m
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))
```

---

## Guida Pratica

### Headroom e Buffer di Capacita

Il principio cardinale del capacity planning operativo e mantenere headroom sufficiente per assorbire spike non previsti, fallimenti di nodi, errori di forecasting, e crescita organica fino al prossimo ciclo di refresh. La formula pratica per ambienti produttivi enterprise:

- **Capacity totale necessaria** = Carico previsto × (1 + headroom_spike) × (1 + headroom_growth) / (1 - failure_tolerance)
- **headroom_spike**: 20-30% per workload prevedibili, fino a 50% per workload con picchi noti
- **headroom_growth**: 10-15% per coprire crescita 6-12 mesi prima del prossimo refresh
- **failure_tolerance**: percentuale di nodi che possono fallire mantenendo SLA (10% per N+1 su 10 nodi)

Esempio: cluster di applicazione che serve picco P95 di 1.000 tps, con headroom_spike 30%, headroom_growth 15%, failure_tolerance 20% (N+1 su 5 nodi):

Capacity = 1.000 × 1.30 × 1.15 / 0.80 = 1.869 tps di capacita installata

**Headroom per Tipo di Risorsa — Linee Guida**

| Risorsa | Soglia Warning | Soglia Critica | Headroom Raccomandato | Note |
|---|---|---|---|---|
| CPU (sustained) | 70% P95 | 85% P95 | 30% | Misurato su finestra 5min P95 |
| RAM | 80% | 90% | 20% | Escludere cache/buffer da "usato" |
| Storage filesystem | 75% | 85% | 25% | Considerare crescita + snapshot |
| IOPS disco | 70% max rated | 85% | 30% | Misurato su peak hour |
| Banda rete | 60% | 80% | 40% | Burst headroom necessario |
| Connection pool | 70% max | 85% | 30% | Slack per spike |
| Queue depth | 50% max | 75% | 50% | Latency-sensitive |

### Capacity Planning Cloud-Specific

Il cloud cambia radicalmente il capacity planning trasformando CAPEX in OPEX e introducendo elasticita. Tuttavia introduce nuove dimensioni di pianificazione: scelta tra On-Demand, Reserved Instances, Savings Plans, Spot.

**On-Demand**: costo massimo, flessibilita totale. Adatto a workload imprevedibili, sviluppo, test, picchi temporanei.

**Reserved Instances 1 anno**: sconto 30-40% rispetto on-demand, impegno fisso. Adatto a workload base prevedibili.

**Reserved Instances 3 anni**: sconto 50-60%, impegno triennale. Adatto a workload mission-critical con domanda stabile.

**Savings Plans**: impegno su spesa oraria ($/h) anziche su istanza specifica, sconto 30-66%, flessibilita su famiglie di istanze. Tipicamente preferibili a RI per workload eterogenei.

**Spot Instances**: sconto fino al 90%, possono essere terminate in qualsiasi momento. Adatto a workload batch interrompibili, big data, rendering, training ML non critico.

**Auto-Scaling**: dimensionamento dinamico basato su metriche (CPU, latenza, queue depth). Configurato con scale-out aggressivo (rapido) e scale-in conservativo (lento) per evitare flapping. Costo di provisioning di una nuova istanza (60-180 secondi su EC2) deve essere considerato nelle policy.

**Strategia Ottimale di Mix Cloud per PMI Italiana**

```
 Workload Analysis
 ┌─────────────────────────────────────────────────────────┐
 │                                                         │
 │  ┌─────────────┐   Base load (24/7, prevedibile)       │
 │  │ Savings Plan│   → 60-70% del carico                 │
 │  │ o RI 1 anno │   → Sconto 30-40%                    │
 │  └─────────────┘                                       │
 │  ┌─────────────┐   Business hours (lun-ven 8-19)       │
 │  │ On-Demand   │   → 20-30% del carico                │
 │  │ Auto-Scale  │   → Scaling predittivo + reattivo     │
 │  └─────────────┘                                       │
 │  ┌─────────────┐   Picchi (campagne, fine mese)        │
 │  │ On-Demand   │   → 5-10% del tempo                  │
 │  │ burst       │   → Pre-warm se prevedibile           │
 │  └─────────────┘                                       │
 │  ┌─────────────┐   Batch/Dev/Test                      │
 │  │ Spot        │   → Fino a 90% sconto                │
 │  │ Instances   │   → Solo workload interrompibili      │
 │  └─────────────┘                                       │
 └─────────────────────────────────────────────────────────┘
```

Esempio dimensionamento workload web aziendale italiano in AWS:

- Base steady (24/7): 4 × m6i.large in Savings Plans 1y → 60% del carico
- Working hours (9-19 lun-ven): +6 × m6i.large in Auto-Scaling on-demand → 35% del carico
- Picchi promozionali: +scaling fino a 20 istanze on-demand → 5% del tempo

**Ottimizzazione RI/Savings Plan — Analisi Copertura**

```python
# Analisi copertura Reserved Instances
# Dati: utilizzo orario per 30 giorni (720 data points)

import numpy as np

hourly_usage = np.array([...])  # vCPU-ore per ogni ora del mese

# Percentili di utilizzo
p10 = np.percentile(hourly_usage, 10)  # base minima
p50 = np.percentile(hourly_usage, 50)  # mediana
p90 = np.percentile(hourly_usage, 90)  # quasi-picco
p_max = np.max(hourly_usage)

print(f"Utilizzo P10: {p10:.0f} vCPU-ore (floor)")
print(f"Utilizzo P50: {p50:.0f} vCPU-ore (median)")
print(f"Utilizzo P90: {p90:.0f} vCPU-ore (near-peak)")
print(f"Utilizzo Max: {p_max:.0f} vCPU-ore")

# Strategia: RI copre fino a P25-P50, il resto on-demand
ri_coverage = np.percentile(hourly_usage, 30)  # copri il floor
on_demand_avg = np.mean(np.maximum(hourly_usage - ri_coverage, 0))

# Calcolo costo
ri_hourly_rate = 0.05  # $/vCPU-ora (RI 1 anno)
od_hourly_rate = 0.08  # $/vCPU-ora (on-demand)

ri_cost_monthly = ri_coverage * ri_hourly_rate * 720
od_cost_monthly = on_demand_avg * od_hourly_rate * 720
total_monthly = ri_cost_monthly + od_cost_monthly

# Confronto con tutto on-demand
all_od = np.mean(hourly_usage) * od_hourly_rate * 720
savings_pct = (all_od - total_monthly) / all_od * 100

print(f"\nStrategia mista: ${total_monthly:.0f}/mese")
print(f"Tutto on-demand: ${all_od:.0f}/mese")
print(f"Risparmio: {savings_pct:.1f}%")
```

### Storage Capacity Planning

Lo storage merita pianificazione dedicata per la combinazione di dati strutturati (database), non strutturati (file share, document management), backup, snapshot, archivi, log.

**Tiering Hot/Warm/Cold**

Strategia fondamentale per ottimizzare costo/prestazioni:

- **Hot tier** (NVMe, all-flash): dati acceduti quotidianamente, database produzione, virtual disk di VM critiche. Costo €1-3/GB.
- **Warm tier** (SSD, ibrido): dati acceduti settimanalmente, file share aziendali, backup recenti. Costo €0.30-0.80/GB.
- **Cold tier** (HDD enterprise, object storage): dati acceduti mensilmente o piu raramente, archivi, backup vecchi. Costo €0.05-0.15/GB.
- **Archive tier** (tape, Glacier Deep Archive): conservazione legale, dati inerti. Costo €0.001-0.01/GB.

**Calcolo Completo Capacity Storage per PMI**

```python
# storage_capacity_calculator.py
# Calcolo capacity storage per PMI italiana tipica

class StorageCapacityPlan:
    def __init__(self):
        self.categories = {}
    
    def add_category(self, name: str, current_gb: float, growth_rate_annual: float,
                     retention_years: float = 1.0, dedup_ratio: float = 1.0,
                     compression_ratio: float = 1.0, tier: str = 'warm'):
        self.categories[name] = {
            'current_gb': current_gb,
            'growth_rate': growth_rate_annual / 100,
            'retention_years': retention_years,
            'dedup_ratio': dedup_ratio,
            'compression_ratio': compression_ratio,
            'tier': tier,
        }
    
    def calculate_projection(self, months: int = 36) -> dict:
        results = {}
        for name, cat in self.categories.items():
            projections = []
            current = cat['current_gb']
            monthly_growth = (1 + cat['growth_rate']) ** (1/12) - 1
            
            for m in range(months):
                current *= (1 + monthly_growth)
                effective = current / (cat['dedup_ratio'] * cat['compression_ratio'])
                projections.append({
                    'month': m + 1,
                    'raw_gb': current,
                    'effective_gb': effective,
                })
            
            results[name] = projections
        return results
    
    def summary(self, months: int = 36):
        projections = self.calculate_projection(months)
        tier_costs = {'hot': 2.0, 'warm': 0.50, 'cold': 0.10, 'archive': 0.005}  # €/GB/mese
        
        print(f"{'Categoria':<30} {'Attuale':>10} {'+ 12m':>10} {'+ 24m':>10} {'+ 36m':>10} {'Tier':>8} {'€/mese':>10}")
        print("-" * 100)
        
        total_cost = 0
        for name, proj in projections.items():
            cat = self.categories[name]
            current = cat['current_gb']
            m12 = proj[11]['effective_gb']
            m24 = proj[23]['effective_gb'] if months > 23 else 0
            m36 = proj[35]['effective_gb'] if months > 35 else 0
            cost = m12 * tier_costs[cat['tier']]
            total_cost += cost
            
            print(f"{name:<30} {current:>8.0f}GB {m12:>8.0f}GB {m24:>8.0f}GB {m36:>8.0f}GB {cat['tier']:>8} {cost:>8.0f}€")
        
        print("-" * 100)
        print(f"{'Costo totale stimato a +12m':>90} {total_cost:>8.0f}€/mese")

# Esempio PMI manifatturiera 80 dipendenti
plan = StorageCapacityPlan()
plan.add_category('Database SAP', 500, 15, tier='hot', compression_ratio=1.5)
plan.add_category('File Share', 2000, 10, tier='warm', dedup_ratio=1.5)
plan.add_category('Email (Exchange)', 800, 20, tier='warm', dedup_ratio=2.0)
plan.add_category('Backup Full', 5000, 15, tier='cold', dedup_ratio=3.0, compression_ratio=2.0)
plan.add_category('Documentale CRM', 300, 25, tier='warm')
plan.add_category('Log applicativi', 200, 30, tier='cold', compression_ratio=5.0, retention_years=2)
plan.add_category('Archivio legale', 1000, 5, tier='archive', retention_years=10)
plan.add_category('VM disk (vSphere)', 3000, 10, tier='hot', dedup_ratio=2.0)

plan.summary(36)
```

**Stima Crescita Filesystem**

La crescita organica dei filesystem aziendali italiani si attesta tipicamente al 5-15% annuo per file share generici, 10-25% per email server, 15-30% per document management e CRM, 20-50% per data warehouse e analytics. La misurazione storica e il punto di partenza obbligato: se non ci sono 12 mesi di dati storici, si parte con monitoring quotidiano e si rivede il piano dopo 6 mesi.

**Snapshot e Deduplicazione**

Le snapshot consumano spazio proporzionale al churn dei dati. Una snapshot giornaliera mantenuta 30 giorni su un volume con 5% churn quotidiano consuma circa 30 × 5% = 150% del volume base; in realta meno per via della deduplicazione tra snapshot consecutive (tipicamente 50-80% di overhead reale).

Il rapporto di deduplicazione realistico dipende dalla natura dei dati:

- Virtual machine omogenee (stesso template OS): 10:1 - 20:1
- File share aziendali misti: 2:1 - 4:1
- Backup full settimanali: 5:1 - 15:1
- Database: 1.5:1 - 3:1 (gia compressi)
- Media (foto, video gia compressi): 1:1 - 1.2:1 (deduplicazione ineffettiva)

### Network Capacity Planning

Il network capacity planning si articola su tre livelli: LAN interna, WAN/MPLS, Internet/transit.

**LAN Interna**

Tipicamente sovradimensionata per default (10/25/100 Gbps switching, 1/10 Gbps server access). I colli di bottiglia emergono in:

- Storage iSCSI/NFS: monitorare separatamente da traffico user
- Backup window: stimare picco backup full e validare contro banda disponibile
- vMotion/Live Migration: dedicare VLAN e banda separata
- Repliche cluster: traffico costante non trascurabile

**WAN e Branch**

Per multi-sede italiana tipica con HQ + 5-15 filiali:

- Stimare traffico per utente: 100-300 kbps medio per knowledge worker, 500-1500 kbps per utenti con video conferencing
- Aggiungere 30% headroom per spike
- Pianificare ridondanza: 2 link di operatori diversi su ogni sede critica
- SD-WAN per ottimizzazione: load balancing per applicazione, QoS automatico

**Dimensionamento Banda WAN per Filiale — Template di Calcolo**

```python
# wan_sizing.py — Dimensionamento banda WAN filiale

def size_wan_branch(
    users: int,
    video_pct: float = 0.3,      # % utenti in video call simultanea
    voip_pct: float = 0.5,       # % utenti in call VoIP simultanea
    erp_users: int = 0,           # utenti ERP concurrent
    file_sync_gb_day: float = 0,  # GB/giorno file sync
    backup_window_hours: float = 8,
    backup_gb: float = 0,         # backup giornaliero in GB
    headroom: float = 0.3,
):
    """Calcola banda WAN necessaria per filiale."""
    
    # Traffico base per utente (email, web browsing, chat)
    base_kbps = users * 150  # 150 kbps medio per knowledge worker
    
    # Video conferencing (1.5 Mbps per utente in call)
    video_kbps = int(users * video_pct) * 1500
    
    # VoIP (100 kbps per chiamata, codec G.711)
    voip_kbps = int(users * voip_pct) * 100
    
    # ERP (200 kbps per sessione attiva)
    erp_kbps = erp_users * 200
    
    # File sync (distribuito su 8 ore lavorative)
    filesync_kbps = (file_sync_gb_day * 1024 * 1024 * 8) / (8 * 3600) if file_sync_gb_day > 0 else 0
    
    # Backup (distribuito sulla finestra)
    backup_kbps = (backup_gb * 1024 * 1024 * 8) / (backup_window_hours * 3600) if backup_gb > 0 else 0
    
    # Totale con headroom
    peak_kbps = base_kbps + video_kbps + voip_kbps + erp_kbps + filesync_kbps
    total_with_backup = peak_kbps + backup_kbps
    recommended_kbps = total_with_backup * (1 + headroom)
    
    # Arrotonda al tier commerciale piu vicino
    tiers_mbps = [10, 20, 30, 50, 100, 200, 300, 500, 1000]
    recommended_mbps = recommended_kbps / 1000
    tier = next((t for t in tiers_mbps if t >= recommended_mbps), tiers_mbps[-1])
    
    print(f"=== Dimensionamento WAN Filiale ({users} utenti) ===")
    print(f"  Base:        {base_kbps/1000:>8.1f} Mbps")
    print(f"  Video:       {video_kbps/1000:>8.1f} Mbps ({int(users*video_pct)} utenti)")
    print(f"  VoIP:        {voip_kbps/1000:>8.1f} Mbps ({int(users*voip_pct)} call)")
    print(f"  ERP:         {erp_kbps/1000:>8.1f} Mbps ({erp_users} sessioni)")
    print(f"  File sync:   {filesync_kbps/1000:>8.1f} Mbps")
    print(f"  Backup:      {backup_kbps/1000:>8.1f} Mbps (window {backup_window_hours}h)")
    print(f"  Peak (no bk):{peak_kbps/1000:>8.1f} Mbps")
    print(f"  + Backup:    {total_with_backup/1000:>8.1f} Mbps")
    print(f"  + Headroom:  {recommended_kbps/1000:>8.1f} Mbps ({headroom*100:.0f}%)")
    print(f"  Tier consigliato: {tier} Mbps")
    print(f"  Backup link:      {max(10, tier//5)} Mbps (operatore alternativo)")
    
    return tier

# Esempio filiale PMI manifatturiera italiana
size_wan_branch(
    users=25,
    video_pct=0.20,      # 20% in video call
    voip_pct=0.40,        # 40% al telefono
    erp_users=10,         # 10 utenti SAP
    file_sync_gb_day=2,   # 2 GB/giorno file sync
    backup_gb=50,         # 50 GB backup giornaliero
    backup_window_hours=8,
    headroom=0.30
)
```

**Internet Transit**

Il modello tipico per PMI italiana medio-grande prevede:

- Connettivita primaria 1-10 Gbps fibra dedicata (operatori: TIM Wholesale, Fastweb, WindTre Business, Open Fiber)
- Backup 100-500 Mbps di operatore alternativo
- Billing tipicamente flat-rate fino a soglia, poi 95-percentile su misurazioni 5-minute
- DDoS mitigation: dimensionare per assorbire 10-100 Gbps con servizi cloud (Cloudflare, AWS Shield, Akamai)

### Kubernetes Capacity Planning

Il capacity planning per Kubernetes introduce dimensioni specifiche: risorse per pod (requests/limits), autoscaling (HPA, VPA, Cluster Autoscaler), bin-packing efficiency.

**Requests vs Limits — Impatto sul Capacity Planning**

```yaml
# Esempio deployment con sizing capacity-aware
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: api:v1.2.3
        resources:
          requests:
            cpu: "500m"       # Garantiti: 0.5 core
            memory: "512Mi"   # Garantiti: 512 MB
          limits:
            cpu: "1000m"      # Massimo: 1 core (burst)
            memory: "1Gi"     # Massimo: 1 GB (OOMKilled se superato)
```

**Calcolo Capacity Cluster Kubernetes**

```python
# k8s_capacity_calculator.py

def k8s_cluster_capacity(
    node_cpu_cores: int,
    node_memory_gb: float,
    num_nodes: int,
    system_overhead_pct: float = 15,  # kube-system, monitoring, logging
    daemonset_cpu_per_node: float = 0.5,  # CPU per daemonset (Prometheus node_exporter, etc)
    daemonset_mem_per_node_gb: float = 0.5,
    failure_tolerance_nodes: int = 1,  # N+1
):
    """Calcola capacita allocabile di un cluster Kubernetes."""
    
    # Overhead sistema per nodo (kubelet, kube-proxy, containerd)
    os_reserve_cpu = 0.1 * node_cpu_cores  # 10% per OS+kubelet
    os_reserve_mem = 0.1 * node_memory_gb
    
    # Allocabile per nodo
    allocatable_cpu = node_cpu_cores - os_reserve_cpu - daemonset_cpu_per_node
    allocatable_mem = node_memory_gb - os_reserve_mem - daemonset_mem_per_node_gb
    
    # Capacita totale cluster (meno nodi di tolleranza)
    effective_nodes = num_nodes - failure_tolerance_nodes
    total_cpu = allocatable_cpu * effective_nodes
    total_mem = allocatable_mem * effective_nodes
    
    # System overhead (monitoring, logging, ingress)
    system_cpu = total_cpu * system_overhead_pct / 100
    system_mem = total_mem * system_overhead_pct / 100
    
    # Disponibile per workload
    workload_cpu = total_cpu - system_cpu
    workload_mem = total_mem - system_mem
    
    print(f"=== Kubernetes Cluster Capacity ===")
    print(f"Nodi: {num_nodes} × {node_cpu_cores} core / {node_memory_gb} GB")
    print(f"Nodi effettivi (N+{failure_tolerance_nodes}): {effective_nodes}")
    print(f"")
    print(f"Per nodo allocabile: {allocatable_cpu:.1f} core, {allocatable_mem:.1f} GB")
    print(f"Totale allocabile:   {total_cpu:.1f} core, {total_mem:.1f} GB")
    print(f"System overhead:     {system_cpu:.1f} core, {system_mem:.1f} GB ({system_overhead_pct}%)")
    print(f"Disponibile workload:{workload_cpu:.1f} core, {workload_mem:.1f} GB")
    
    # Stima pod capacity
    avg_pod_cpu_request = 0.25  # 250m medio
    avg_pod_mem_request = 0.25  # 256Mi medio
    max_pods_cpu = int(workload_cpu / avg_pod_cpu_request)
    max_pods_mem = int(workload_mem / avg_pod_mem_request)
    max_pods = min(max_pods_cpu, max_pods_mem)
    
    print(f"\nStima pod (avg request 250m CPU, 256Mi mem):")
    print(f"  Max pod per CPU: {max_pods_cpu}")
    print(f"  Max pod per MEM: {max_pods_mem}")
    print(f"  Max pod effettivo: {max_pods}")
    
    return workload_cpu, workload_mem

# Cluster PMI tipico
k8s_cluster_capacity(
    node_cpu_cores=8,
    node_memory_gb=32,
    num_nodes=5,
    failure_tolerance_nodes=1,
)
```

### Database Capacity Planning

Il database e spesso il componente piu critico e meno elastico dell'infrastruttura. Richiede capacity planning dedicato con focus su IOPS, working set memory, storage growth.

**Dimensionamento Database PostgreSQL — Esempio Pratico**

```python
# db_capacity.py — Capacity planning database PostgreSQL

def pg_capacity_plan(
    db_size_gb: float,
    growth_rate_monthly_pct: float,
    peak_tps: int,
    avg_query_time_ms: float,
    read_write_ratio: float = 0.8,  # 80% read
    wal_write_pct: float = 0.15,    # 15% overhead WAL
    shared_buffers_ratio: float = 0.25,  # 25% RAM per shared_buffers
    effective_cache_ratio: float = 0.75,  # 75% RAM per effective_cache_size
    connection_pool_size: int = 100,
    months_forecast: int = 12,
):
    """Calcola requisiti hardware per PostgreSQL."""
    
    # CPU: basato su TPS e query time
    concurrent_queries = peak_tps * (avg_query_time_ms / 1000)  # Little's Law
    cpu_cores = max(4, int(concurrent_queries * 1.5))  # 1.5x per headroom
    
    # RAM: shared_buffers + working set
    working_set_gb = min(db_size_gb * 0.3, 64)  # hot data, max 64 GB
    ram_gb = max(16, int(working_set_gb / shared_buffers_ratio))
    
    # IOPS: basato su TPS e mix r/w
    read_iops = peak_tps * read_write_ratio * 1.2  # 1.2x per index lookups
    write_iops = peak_tps * (1 - read_write_ratio) * (1 + wal_write_pct)
    total_iops = int(read_iops + write_iops)
    
    # Storage: data + indici + WAL + temp + crescita
    index_overhead = 0.3  # 30% extra per indici
    wal_retention_gb = peak_tps * 0.001 * 3600 * 24 * 2  # 2 giorni WAL retention
    total_storage_gb = db_size_gb * (1 + index_overhead) + wal_retention_gb + 20  # +20 GB temp
    
    # Proiezione storage
    for m in range(months_forecast):
        total_storage_gb *= (1 + growth_rate_monthly_pct / 100)
    
    # Connessioni
    max_connections = connection_pool_size + 10  # +10 per admin/monitoring
    
    print(f"=== PostgreSQL Capacity Plan ===")
    print(f"Database corrente: {db_size_gb:.0f} GB")
    print(f"Peak TPS: {peak_tps}")
    print(f"")
    print(f"CPU: {cpu_cores} core (concurrent queries P95: {concurrent_queries:.0f})")
    print(f"RAM: {ram_gb} GB (shared_buffers: {ram_gb*shared_buffers_ratio:.0f} GB)")
    print(f"IOPS: {total_iops} (read: {int(read_iops)}, write: {int(write_iops)})")
    print(f"Storage +{months_forecast}m: {total_storage_gb:.0f} GB")
    print(f"max_connections: {max_connections}")
    print(f"")
    print(f"Disco consigliato: {'NVMe SSD' if total_iops > 5000 else 'SSD Enterprise'}")
    print(f"RAID: RAID 10 per performance + ridondanza")
    
    return {
        'cpu_cores': cpu_cores,
        'ram_gb': ram_gb,
        'iops': total_iops,
        'storage_gb': total_storage_gb,
        'max_connections': max_connections,
    }

# Esempio: database gestionale PMI
pg_capacity_plan(
    db_size_gb=200,
    growth_rate_monthly_pct=2.5,
    peak_tps=300,
    avg_query_time_ms=15,
    read_write_ratio=0.75,
    connection_pool_size=80,
    months_forecast=12,
)
```

---

## Configurazione

### Prometheus Recording Rules per Capacity

Le recording rules pre-aggregano metriche pesanti per aggregare dati capacity-relevant a granularita appropriata, riducendo carico sulle query di dashboard. Esempio per CPU cluster Kubernetes:

```yaml
# /etc/prometheus/rules/capacity.yml
groups:
  - name: capacity_aggregations
    interval: 5m
    rules:
      - record: cluster:cpu_usage_pct:avg5m
        expr: |
          100 - avg by (cluster) (
            irate(node_cpu_seconds_total{mode="idle"}[5m]) * 100
          )

      - record: cluster:memory_usage_pct:avg5m
        expr: |
          (1 - avg by (cluster) (
            node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes
          )) * 100

      - record: cluster:cpu_usage_pct:p95_1d
        expr: |
          quantile_over_time(0.95, cluster:cpu_usage_pct:avg5m[1d])

      - record: cluster:disk_usage_pct:max
        expr: |
          max by (cluster, mountpoint) (
            (node_filesystem_size_bytes - node_filesystem_avail_bytes)
            / node_filesystem_size_bytes * 100
          )

  - name: capacity_forecasting
    interval: 1h
    rules:
      - record: cluster:disk_growth_gb_per_day
        expr: |
          deriv(node_filesystem_avail_bytes[7d:1h]) * -86400 / 1e9

      - record: cluster:disk_days_until_full
        expr: |
          (node_filesystem_avail_bytes / 1e9) / cluster:disk_growth_gb_per_day

  - name: capacity_saturation
    interval: 5m
    rules:
      # CPU saturation (run queue)
      - record: node:cpu_saturation:avg5m
        expr: |
          avg by (instance) (
            node_load1 / count by (instance) (node_cpu_seconds_total{mode="idle"})
          )

      # Memory saturation (swap activity)
      - record: node:memory_saturation:rate5m
        expr: |
          rate(node_vmstat_pswpin[5m]) + rate(node_vmstat_pswpout[5m])

      # Disk saturation (IO queue depth)
      - record: node:disk_saturation:avg5m
        expr: |
          avg by (instance, device) (
            rate(node_disk_io_time_weighted_seconds_total[5m])
          )

      # Network saturation (drops)
      - record: node:network_saturation:rate5m
        expr: |
          sum by (instance) (
            rate(node_network_receive_drop_total[5m])
            + rate(node_network_transmit_drop_total[5m])
          )

  - name: capacity_alerting
    interval: 5m
    rules:
      # Alert: disco pieno entro 7 giorni
      - alert: DiskWillFillIn7Days
        expr: cluster:disk_days_until_full > 0 and cluster:disk_days_until_full < 7
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Disco {{ $labels.mountpoint }} si riempira in {{ $value | humanizeDuration }}"
          description: "Sul cluster {{ $labels.cluster }}, il mountpoint {{ $labels.mountpoint }} si esaurira entro 7 giorni al tasso di crescita attuale."

      # Alert: CPU P95 sopra 80% per 30 minuti
      - alert: HighCPUP95Sustained
        expr: cluster:cpu_usage_pct:p95_1d > 80
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "CPU P95 al {{ $value }}% sul cluster {{ $labels.cluster }}"

      # Alert: Memoria sopra 90%
      - alert: HighMemoryUsage
        expr: cluster:memory_usage_pct:avg5m > 90
        for: 15m
        labels:
          severity: critical
        annotations:
          summary: "Memoria al {{ $value }}% sul cluster {{ $labels.cluster }}"
```

### Grafana Dashboard Capacity

Un dashboard capacity efficace prevede tre layer: stato corrente, trend storico, forecast.

**Pannello Stato Corrente**: gauge per ogni risorsa critica (CPU cluster, memoria, IOPS, banda) con soglie verde/giallo/rosso (es. <60% / 60-80% / >80%).

**Pannello Trend Storico**: time series 30-90 giorni con linea P95 evidenziata. Permette di identificare visivamente trend di crescita e seasonality.

**Pannello Forecast**: proiezione 12 mesi con intervallo di confidenza, marker per soglia di azione (80% = avvio ordine), soglia critica (95% = scaling emergenza).

**Dashboard JSON Model per Grafana (estratto)**

```json
{
  "title": "Capacity Planning Overview",
  "panels": [
    {
      "title": "CPU Cluster - Stato Corrente",
      "type": "gauge",
      "targets": [{"expr": "cluster:cpu_usage_pct:avg5m"}],
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "steps": [
              {"color": "green", "value": 0},
              {"color": "yellow", "value": 60},
              {"color": "orange", "value": 75},
              {"color": "red", "value": 85}
            ]
          },
          "max": 100, "min": 0, "unit": "percent"
        }
      }
    },
    {
      "title": "Storage - Giorni alla Saturazione",
      "type": "stat",
      "targets": [{"expr": "cluster:disk_days_until_full"}],
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "steps": [
              {"color": "red", "value": 0},
              {"color": "orange", "value": 30},
              {"color": "yellow", "value": 90},
              {"color": "green", "value": 180}
            ]
          },
          "unit": "d"
        }
      }
    }
  ]
}
```

Esempio query Grafana per stima giorni prima di esaurimento storage:

```promql
# Giorni prima di saturazione storage
(node_filesystem_avail_bytes{mountpoint="/data"} / 1e9)
/
(deriv(node_filesystem_avail_bytes{mountpoint="/data"}[7d:1h]) * -86400 / 1e9)
```

### Python Notebook per Capacity Forecasting

Esempio completo di notebook per forecast mensile storage con Prophet, esportabile in report PDF:

```python
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from prometheus_api_client import PrometheusConnect

# 1. Estrazione dati da Prometheus
prom = PrometheusConnect(url="http://prometheus.local:9090", disable_ssl=True)
data = prom.custom_query_range(
    query='node_filesystem_size_bytes{mountpoint="/data"} - node_filesystem_avail_bytes{mountpoint="/data"}',
    start_time='2024-01-01T00:00:00Z',
    end_time='2026-04-22T00:00:00Z',
    step='1h'
)

# 2. Trasformazione in DataFrame Prophet-compatibile
df = pd.DataFrame(data[0]['values'], columns=['ds', 'y'])
df['ds'] = pd.to_datetime(df['ds'], unit='s')
df['y'] = df['y'].astype(float) / (1024**4)  # in TB

# 3. Modello Prophet
m = Prophet(yearly_seasonality=True, weekly_seasonality=False,
            changepoint_prior_scale=0.05)
m.add_country_holidays(country_name='IT')
m.fit(df)

# 4. Forecast 12 mesi
future = m.make_future_dataframe(periods=365, freq='D')
forecast = m.predict(future)

# 5. Identificazione soglia 80% capacita
total_capacity_tb = 50.0
threshold_80 = total_capacity_tb * 0.80
crossing_date = forecast[forecast['yhat'] >= threshold_80]['ds'].min()
print(f"Soglia 80% raggiunta presumibilmente il: {crossing_date}")

# 6. Plot per report
fig = m.plot(forecast)
plt.axhline(y=threshold_80, color='orange', linestyle='--', label='80% threshold')
plt.axhline(y=total_capacity_tb, color='red', linestyle='--', label='Capacity max')
plt.legend()
plt.savefig('capacity_forecast.png', dpi=150)
```

### Capacity Tracker Excel per PMI

Per PMI senza piattaforme avanzate, un foglio Excel ben strutturato copre l'80% delle esigenze. Struttura tipica:

**Foglio "Inventory"**: una riga per server/risorsa, colonne: Asset ID, Hostname, Ruolo, CPU cores, RAM GB, Storage TB, Data acquisto, Fine garanzia, EOL vendor.

**Foglio "Monitoring Mensile"**: per ogni asset e ogni mese, registrare CPU avg, CPU P95, RAM avg, RAM P95, Storage usato, IOPS avg.

**Foglio "Forecast"**: formule Excel `=FORECAST.LINEAR()` o `=FORECAST.ETS()` per proiezione 12 mesi su utilizzo basato sui dati mensili. Excel 365 supporta nativamente forecasting con stagionalita.

**Foglio "Action Plan"**: tracker azioni capacity-driven con scadenze (es. "Q3 2026: ordinare upgrade RAM server SAP da 256 a 512 GB").

**Script Python per Generazione Report Automatico da Prometheus**

```python
#!/usr/bin/env python3
"""
capacity_report.py — Generazione report capacity mensile automatico.
Eseguire il primo di ogni mese via cron.
Output: PDF con stato, trend, forecast, raccomandazioni.
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
from prometheus_api_client import PrometheusConnect
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

PROM_URL = "http://prometheus.local:9090"
REPORT_DIR = "/var/reports/capacity"
RESOURCES = [
    {'name': 'CPU Cluster Prod', 'query': 'cluster:cpu_usage_pct:avg5m{cluster="prod"}',
     'unit': '%', 'threshold_warn': 70, 'threshold_crit': 85},
    {'name': 'RAM Cluster Prod', 'query': 'cluster:memory_usage_pct:avg5m{cluster="prod"}',
     'unit': '%', 'threshold_warn': 80, 'threshold_crit': 90},
    {'name': 'Storage /data', 'query': '(node_filesystem_size_bytes{mountpoint="/data"}-node_filesystem_avail_bytes{mountpoint="/data"})/node_filesystem_size_bytes{mountpoint="/data"}*100',
     'unit': '%', 'threshold_warn': 75, 'threshold_crit': 85},
]

def fetch_data(prom, query, days=90):
    """Fetch dati da Prometheus per ultimi N giorni."""
    end = datetime.now()
    start = end - timedelta(days=days)
    data = prom.custom_query_range(
        query=query,
        start_time=start.isoformat() + 'Z',
        end_time=end.isoformat() + 'Z',
        step='1h'
    )
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data[0]['values'], columns=['ds', 'y'])
    df['ds'] = pd.to_datetime(df['ds'], unit='s')
    df['y'] = df['y'].astype(float)
    return df

def forecast_resource(df, periods=90):
    """Forecast 90 giorni con Prophet."""
    m = Prophet(
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    m.add_country_holidays(country_name='IT')
    m.fit(df)
    future = m.make_future_dataframe(periods=periods, freq='D')
    return m.predict(future)

def generate_report():
    prom = PrometheusConnect(url=PROM_URL, disable_ssl=True)
    today = datetime.now().strftime('%Y-%m-%d')
    
    with PdfPages(f'{REPORT_DIR}/capacity_report_{today}.pdf') as pdf:
        # Pagina titolo
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.text(0.5, 0.6, 'Capacity Planning Report', fontsize=24, ha='center', weight='bold')
        ax.text(0.5, 0.4, f'Data: {today}', fontsize=16, ha='center')
        ax.text(0.5, 0.3, 'Generato automaticamente', fontsize=12, ha='center', style='italic')
        ax.axis('off')
        pdf.savefig(fig)
        plt.close()
        
        # Una pagina per risorsa
        for res in RESOURCES:
            df = fetch_data(prom, res['query'], days=90)
            if df.empty:
                continue
            
            forecast = forecast_resource(df, periods=90)
            
            fig, axes = plt.subplots(2, 1, figsize=(11, 8.5))
            
            # Trend storico
            axes[0].plot(df['ds'], df['y'], 'b-', alpha=0.5, linewidth=0.5)
            axes[0].axhline(y=res['threshold_warn'], color='orange', linestyle='--', label=f"Warning ({res['threshold_warn']}{res['unit']})")
            axes[0].axhline(y=res['threshold_crit'], color='red', linestyle='--', label=f"Critico ({res['threshold_crit']}{res['unit']})")
            axes[0].set_title(f"{res['name']} — Ultimi 90 giorni")
            axes[0].set_ylabel(res['unit'])
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # Forecast
            future_mask = forecast['ds'] > df['ds'].max()
            axes[1].plot(forecast.loc[~future_mask, 'ds'], forecast.loc[~future_mask, 'yhat'], 'b-', label='Storico (fit)')
            axes[1].plot(forecast.loc[future_mask, 'ds'], forecast.loc[future_mask, 'yhat'], 'r-', label='Forecast')
            axes[1].fill_between(forecast.loc[future_mask, 'ds'], forecast.loc[future_mask, 'yhat_lower'],
                                forecast.loc[future_mask, 'yhat_upper'], alpha=0.2, color='red')
            axes[1].axhline(y=res['threshold_warn'], color='orange', linestyle='--')
            axes[1].axhline(y=res['threshold_crit'], color='red', linestyle='--')
            axes[1].set_title(f"{res['name']} — Forecast +90 giorni")
            axes[1].set_ylabel(res['unit'])
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()
    
    print(f"Report generato: {REPORT_DIR}/capacity_report_{today}.pdf")

if __name__ == '__main__':
    generate_report()
```

---

## Best Practices

### Cadenza dei Cicli di Capacity Planning

La cadenza ottimale dipende dalla maturita e velocita di cambiamento dell'organizzazione. Riferimenti:

- **Mensile**: monitoring e analisi continua, review delle anomalie
- **Trimestrale**: forecast aggiornato, identificazione azioni 6-12 mesi
- **Semestrale**: piano capacity formale presentato alla direzione, allineamento con budget
- **Annuale**: capacity strategy multi-anno integrata con piano IT triennale

### Documentazione e Comunicazione

Un piano capacity che resta nelle email del responsabile IT non ha alcun valore. Best practice:

- Capacity report in formato standard mensile, distribuito a IT manager + CFO
- Dashboard live accessibile a stakeholder di business
- Capacity assumptions esplicitate (driver di business, rate di crescita assunto)
- Decisioni con scadenza: ogni raccomandazione capacity ha owner e deadline

### Cattura dei Driver di Business

I migliori capacity planner non si limitano a estrapolare metriche tecniche, ma collegano sistematicamente le risorse IT ai driver di business. Tabella di mapping tipica per ERP italiano:

| Driver Business | Metrica IT Correlata | Coefficiente Tipico |
|---|---|---|
| Numero utenti attivi | RAM application server | 200-500 MB/utente |
| Fatture/mese emesse | IOPS database | 0.5-1.5 IOPS/fattura |
| GB documentale archiviato/mese | Storage tier 2 | 1:1 + indicizzazione 20% |
| Filiali aperte | Banda WAN HQ | 5-20 Mbps/filiale |
| Dipendenti totali | Connessioni VPN concorrenti | 30-50% del totale |
| Ordini e-commerce/giorno | CPU web tier | 0.01-0.05 vCPU/ordine |
| Clienti CRM attivi | DB storage CRM | 50-200 MB/cliente |
| Email inviate/giorno | IOPS mail server | 2-5 IOPS/email |
| Progetti attivi PM | Storage documentale | 500 MB-2 GB/progetto |
| Videocall concorrenti | Banda Internet | 2-4 Mbps/call |

Quando il commerciale annuncia "stiamo per acquisire un cliente da 1.000 nuovi utenti", il capacity planner ha gia la formula per stimare l'impatto.

### Esempi Pratici per PMI Italiane

**E-commerce stagionale Natale**

Negozio online di abbigliamento con base 50 ordini/giorno, picco Black Friday 800 ordini/giorno, picco Natale 500 ordini/giorno per 3 settimane. Strategia:

- Base infrastrutturale: 2 × m6i.large in EC2 (24/7, Savings Plan 1y)
- Black Friday window (1 novembre - 5 dicembre): pre-warm a 8 istanze on-demand + auto-scaling fino a 20
- Natale (1-31 dicembre): mantenere 6 istanze + auto-scaling
- Post-festivita (gennaio): tornare a base
- Stress test simulato a inizio ottobre con 5x carico previsto

**ERP manifatturiero fine mese**

PMI manifatturiera 80 utenti SAP con picco prevedibile tra il 25 e il 5 di ogni mese (chiusura ordini, fatturazione, MRP). Strategia:

- Sizing su picco fine mese, non media
- Scheduling backup, indici reorg, batch report fuori finestra picco
- Monitoring dedicato giorni picco con alerting piu sensibile
- Forecast mensile basato su volumi ordini commerciale

**SaaS gestionale per commercialisti**

Multi-tenant SaaS con 200 studi commercialisti italiani. Picchi:

- 16 di ogni mese: F24 - picco 5x sessioni concorrenti per 8 ore
- Marzo-aprile: dichiarazione 730 - picco 3x sostenuto per 6 settimane
- Settembre-novembre: dichiarazione redditi - picco 4x sostenuto per 10 settimane

Strategia: capacity sizing su picco F24 (peak event predicibile), scaling stagionale primavera/autunno, riduzione capacity in agosto e luglio.

**Studio di architettura con rendering 3D**

PMI 15 dipendenti, 5 architetti che usano Revit/AutoCAD con rendering 3D periodici. Workload caratteristico: CPU burst intensi durante rendering (2-8 ore, 100% CPU), idle il resto del tempo.

Strategia:
- Workstation locali potenti (32 core, 128 GB RAM, GPU workstation) per 3 utenti heavy
- Rendering farm cloud on-demand (AWS EC2 p3/g4 o Azure NV series) per picchi
- Script di submission automatico che lancia istanze cloud, esegue rendering, scarica risultato, termina istanza
- Costo stimato: €200-500/mese per 20-40 ore rendering cloud vs €15.000+ per server rendering dedicato

### Reportistica Capacity Executive

Il report mensile capacity per la direzione deve essere conciso (1-2 pagine A4) e focalizzato su decisioni:

**Sezione 1 - Stato attuale**: tabella con utilizzo P95 di ogni risorsa critica, semaforo verde/giallo/rosso.

**Sezione 2 - Trend ultimo trimestre**: 3-5 grafici chiave (CPU cluster, RAM, storage, banda, transactions).

**Sezione 3 - Forecast 12 mesi**: stima quando ogni risorsa raggiunge soglia 80% e 95%.

**Sezione 4 - Raccomandazioni**: 3-5 azioni concrete con owner, scadenza, costo stimato, impatto se non eseguite.

**Sezione 5 - Validazione previsioni precedenti**: errore di forecasting del trimestre scorso (essenziale per credibilita).

### Capacity Planning per Ambienti Virtualizzati

In ambienti VMware vSphere o Proxmox, il capacity planning richiede considerazioni specifiche:

**Overcommit Ratios Raccomandati**

| Risorsa | Ratio Conservativo | Ratio Moderato | Ratio Aggressivo | Note |
|---|---|---|---|---|
| vCPU:pCPU | 2:1 | 4:1 | 6:1 | Dipende da workload; database max 2:1 |
| vRAM:pRAM | 1:1 | 1.2:1 | 1.5:1 | RAM overcommit causa swap = disaster |
| Storage thin | 1.2:1 | 1.5:1 | 2:1 | Monitorare actual usage costantemente |

**vSphere HA Admission Control**: riservare capacity per failover. Con 4 host e policy "1 host failure tolerated", la capacity utilizzabile e 75% del totale (3 host su 4).

**DRS e Load Balancing**: il vSphere DRS bilancia automaticamente il carico tra host, ma non sostituisce il capacity planning — se tutti gli host sono al 90%, DRS non puo fare nulla.

```python
# Calcolo capacity cluster vSphere
def vsphere_cluster_capacity(
    num_hosts: int,
    cpu_cores_per_host: int,
    ram_gb_per_host: float,
    ha_tolerance_hosts: int = 1,
    vcpu_ratio: float = 4.0,
    vram_ratio: float = 1.0,
    hypervisor_overhead_pct: float = 10,
):
    """Calcola capacity utilizzabile cluster vSphere."""
    effective_hosts = num_hosts - ha_tolerance_hosts
    
    # CPU
    total_pcpu = cpu_cores_per_host * effective_hosts
    usable_pcpu = total_pcpu * (1 - hypervisor_overhead_pct / 100)
    total_vcpu = usable_pcpu * vcpu_ratio
    
    # RAM
    total_ram = ram_gb_per_host * effective_hosts
    usable_ram = total_ram * (1 - hypervisor_overhead_pct / 100)
    allocatable_vram = usable_ram * vram_ratio
    
    print(f"=== vSphere Cluster Capacity ===")
    print(f"Host: {num_hosts} ({effective_hosts} effettivi, HA={ha_tolerance_hosts})")
    print(f"pCPU totali: {total_pcpu} core → allocabili: {total_vcpu:.0f} vCPU (ratio {vcpu_ratio}:1)")
    print(f"pRAM totale: {total_ram:.0f} GB → allocabile: {allocatable_vram:.0f} GB vRAM (ratio {vram_ratio}:1)")
    
    # Stima VM capacity
    avg_vm_vcpu = 4
    avg_vm_vram = 8
    max_vms_cpu = int(total_vcpu / avg_vm_vcpu)
    max_vms_ram = int(allocatable_vram / avg_vm_vram)
    print(f"\nVM stimabili (avg 4 vCPU, 8 GB):")
    print(f"  Per CPU: {max_vms_cpu}")
    print(f"  Per RAM: {max_vms_ram}")
    print(f"  Effettivo: {min(max_vms_cpu, max_vms_ram)}")

# Esempio cluster PMI
vsphere_cluster_capacity(
    num_hosts=4,
    cpu_cores_per_host=32,
    ram_gb_per_host=256,
    ha_tolerance_hosts=1,
    vcpu_ratio=3.0,
    vram_ratio=1.0,
)
```

### Anti-Pattern del Capacity Planning

| Anti-Pattern | Descrizione | Conseguenza | Rimedio |
|---|---|---|---|
| Planning on Average | Dimensionare sulla media anziche sul P95 | Degrado performance ai picchi | Usare P95 o P99 come target |
| Ignoring Seasonality | Non considerare variazioni temporali | Forecast sistematicamente errati | STL/MSTL decomposition |
| One-Shot Planning | Fare capacity plan solo all'acquisto | Obsoleto in 3 mesi | Ciclo iterativo mensile/trimestrale |
| Technical-Only | Solo metriche tecniche, no driver business | Sorprese da crescita organica | Mapping driver business-IT |
| Fantasy Forecast | Previsioni senza validazione storica | Perdita credibilita | Track accuracy dei forecast precedenti |
| Serverless = No Planning | "Il cloud scala automaticamente" | Cloud bill shock | Pianificare costi e limiti |
| Golden Hammer | Un solo modello per tutto | Errori su workload diversi | Modello per tipo workload |
| Ignorare la Coda | Non considerare queuing theory | Sottostima tempi di risposta | M/M/c, Little's Law |

---

## Troubleshooting

### Forecast Sistematicamente Sbagliati

Sintomo: le previsioni hanno errore >25% costante. Cause tipiche:

- **Dati insufficienti**: meno di un ciclo stagionale completo (1 anno minimo per modelli che includono yearly seasonality). Soluzione: estendere periodo di osservazione o ricorrere a modelli piu semplici.
- **Outlier non gestiti**: incidenti, downtime, eventi straordinari hanno alterato la baseline. Soluzione: pulire dati con detection anomalie (IQR, Z-score) prima del fitting.
- **Cambio di regime**: il workload e cambiato fondamentalmente (rilascio nuova feature, migrazione cliente). Soluzione: ridurre training window al post-cambio, o usare changepoint detection (Prophet lo fa nativamente).
- **Driver omessi**: il modello cattura solo trend tecnico, non gli eventi di business. Soluzione: aggiungere regressori esogeni (numero utenti, campagne marketing, festivita).

**Procedura di Debug Forecast**

```python
# debug_forecast.py — Diagnostica errore forecast

def diagnose_forecast_error(actual, predicted):
    """Analisi dettagliata errore forecast."""
    error = actual - predicted
    abs_error = np.abs(error)
    pct_error = abs_error / actual * 100
    
    print("=== Diagnostica Forecast ===")
    print(f"MAPE: {np.mean(pct_error):.1f}%")
    print(f"MAE:  {np.mean(abs_error):.2f}")
    print(f"RMSE: {np.sqrt(np.mean(error**2)):.2f}")
    print(f"Bias: {np.mean(error):.2f} ({'sotto-stima' if np.mean(error) > 0 else 'sovra-stima'})")
    
    # Errore per giorno della settimana
    for day in range(7):
        mask = [d.weekday() == day for d in actual.index]
        if sum(mask) > 0:
            day_mape = np.mean(pct_error[mask])
            print(f"  {['Lun','Mar','Mer','Gio','Ven','Sab','Dom'][day]}: MAPE={day_mape:.1f}%")
    
    # Errore per ora del giorno
    for hour in [8, 12, 17, 22]:
        mask = [d.hour == hour for d in actual.index]
        if sum(mask) > 0:
            hour_mape = np.mean(pct_error[mask])
            print(f"  Ore {hour}: MAPE={hour_mape:.1f}%")
    
    # Raccomandazioni
    if np.mean(error) > 0:
        print("\n→ Il modello sotto-stima sistematicamente. Possibili cause:")
        print("  - Crescita piu rapida del previsto")
        print("  - Nuovo workload non catturato nel training")
        print("  - Stagionalita non modellata (es. mensile)")
    else:
        print("\n→ Il modello sovra-stima sistematicamente. Possibili cause:")
        print("  - Ottimizzazioni applicate post-training")
        print("  - Riduzione utenti/carico")
        print("  - Overfit su picchi anomali nel training set")
```

### Saturazione Improvvisa di Risorsa

Sintomo: una risorsa raggiunge soglia critica senza preavviso. Cause:

- **Job batch fuori controllo**: investigare top processi (top, htop), pianificare retry policy
- **Memory leak applicativo**: valgrind, profiler JVM, restart programmati come mitigazione temporanea
- **Database query degradata**: spesso piano esecuzione cambiato per statistiche obsolete; aggiornare statistiche, EXPLAIN ANALYZE
- **Snapshot accumulati**: vmware vsphere, snapshot non eliminate consumano spazio rapidamente; audit con `Get-Snapshot` PowerCLI
- **Log esplosi**: log applicativi senza rotation; logrotate, retention policy

**Triage rapido saturazione**

```bash
# === Triage saturazione rapido ===

# 1. CPU: chi consuma?
echo "=== TOP CPU ==="
ps aux --sort=-%cpu | head -20

# 2. Memoria: chi consuma?
echo "=== TOP MEMORY ==="
ps aux --sort=-%mem | head -20

# 3. IOPS: chi scrive/legge?
echo "=== TOP I/O ==="
sudo iotop -b -n 1 --only | head -20

# 4. Disco: cosa occupa spazio?
echo "=== DISK USAGE ==="
df -h | grep -E '^/dev'
echo "--- Directories piu grandi sotto /var ---"
sudo du -sh /var/* 2>/dev/null | sort -rh | head -10
echo "--- File piu grandi recenti (>100MB, ultimi 7gg) ---"
sudo find /var -type f -size +100M -mtime -7 -exec ls -lh {} \; 2>/dev/null | sort -k5rh | head -10

# 5. Rete: chi genera traffico?
echo "=== NETWORK ==="
sudo ss -tlnp | head -20
sudo nethogs -t -c 5 2>/dev/null | head -20

# 6. Connessioni: pool esaurito?
echo "=== CONNECTIONS ==="
ss -s
echo "--- Connessioni per stato ---"
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn
```

### Cloud Bill Shock

Sintomo: bolletta cloud raddoppia senza cambi noti di workload. Cause tipiche:

- **Auto-scaling impazzito**: policy troppo aggressiva, scale-out senza scale-in. Audit Auto Scaling group activity history.
- **Data transfer costs**: traffico cross-region o egress imprevisto. Verificare CloudWatch metriche network.
- **Servizi orfani**: load balancer, IP elastici, snapshot, NAT gateway dimenticati dopo decommissioning. AWS Trusted Advisor / Azure Advisor.
- **Spot terminations**: workload spot terminate ripetutamente forzano restart con on-demand fallback.
- **Reserved Instances scadute**: RI annuali non rinnovate, workload tornato a on-demand.

**Checklist Bill Shock Investigation**

```bash
# AWS Bill Investigation Checklist

# 1. Cost per servizio (ultimi 30 giorni vs precedenti)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output table

# 2. Risorse non taggate (potenziali orfani)
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Environment \
  --output text | wc -l

# 3. EBS volumes non attached
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query 'Volumes[*].[VolumeId,Size,CreateTime]' \
  --output table

# 4. Elastic IPs non associate
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==null].[PublicIp,AllocationId]' \
  --output table

# 5. Snapshot vecchi (>90 giorni)
aws ec2 describe-snapshots --owner-ids self \
  --query "Snapshots[?StartTime<='$(date -d '90 days ago' --iso-8601)'].[SnapshotId,VolumeSize,StartTime]" \
  --output table

# 6. RI scadute
aws ec2 describe-reserved-instances \
  --filters Name=state,Values=retired \
  --output table
```

### Capacity Plan Ignorato

Sintomo: si rilasciano report capacity ma nulla cambia, le emergenze continuano. Cause organizzative:

- Report troppo tecnico, non comprensibile alla direzione
- Mancanza di owner di azioni: raccomandazioni senza nome e scadenza
- Mancanza di consequenze per inazione: serve mostrare impatto economico delle emergenze evitabili
- Budget capacity non protetto: viene tagliato per altre priorita

Soluzione: collegare capacity plan al budget annuale, presentare in board con CFO, tracciare downtime evitati grazie ad azioni capacity-driven.

### Problemi Specifici per Ambiente

**VMware vSphere: CPU Ready Time Elevato**

Sintomo: VM lente nonostante CPU host non al 100%. Causa: overcommit CPU eccessivo, troppe vCPU per VM. Il CPU Ready Time misura quanto tempo la VM aspetta per avere accesso alla CPU fisica.

Soglie: CPU Ready <5% = OK, 5-10% = warning, >10% = degradazione percepibile.

Soluzione: ridurre vCPU per VM (spesso meno vCPU = migliori performance per single-thread), ridurre overcommit ratio, distribuire VM CPU-intensive su host diversi.

**PostgreSQL: bloat delle tabelle che impatta IOPS**

Sintomo: IOPS crescenti senza crescita proporzionale dei dati utili. Causa: VACUUM non aggressivo abbastanza, tabelle con dead tuples eccessivi.

```sql
-- Identificare tabelle con bloat eccessivo
SELECT schemaname, relname, 
       n_live_tup, n_dead_tup,
       ROUND(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) as dead_pct,
       pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC
LIMIT 20;
```

Soluzione: tuning `autovacuum_vacuum_threshold`, `autovacuum_vacuum_scale_factor`, scheduling `VACUUM FULL` durante finestre di manutenzione per tabelle critiche.

---

## Riferimenti

### Standard e Framework

- **ITIL 4 - Service Capacity Management**: framework di riferimento per processi capacity in organizzazioni IT mature
- **ISO/IEC 20000-1:2018**: requisiti capacity management per Service Management System
- **TIA-942**: standard datacenter che include criteri di dimensionamento power/cooling
- **Uptime Institute Tier Standard**: classificazione datacenter Tier I-IV
- **ISO/IEC 27001:2022**: controllo A.8.6 Capacity management

### Letteratura

- Neil Gunther, *Guerrilla Capacity Planning* (2007) — testo classico, USL e tecniche pratiche
- Daniel Menasce, Virgilio Almeida, *Capacity Planning for Web Services* (2002) — fondamenti queuing theory applicati
- Bondi, *Foundations of Software and System Performance Engineering* (2014) — approccio ingegneristico moderno
- Brendan Gregg, *Systems Performance: Enterprise and the Cloud* (2020) — methodology USE/RED, profiling
- Len Bass, Ingo Weber, Liming Zhu, *DevOps: A Software Architect's Perspective* (2015) — capacity in contesto DevOps
- John Allspaw, *The Art of Capacity Planning* (O'Reilly, 2008) — pratico e orientato al web

### Strumenti Open Source

- **Prometheus + Grafana**: time series metrics, recording rules, dashboarding
- **VictoriaMetrics**: alternativa Prometheus per long-term storage
- **statsmodels** (Python): ARIMA, SARIMA, Holt-Winters, decomposizione STL
- **Prophet** (Facebook): forecasting con stagionalita multipla e holidays
- **pmdarima** (Python): auto ARIMA con ricerca parametri automatica
- **k6, JMeter, Locust, Gatling**: load testing
- **PCP (Performance Co-Pilot)**: framework Red Hat per metriche performance
- **Netdata**: monitoring real-time con anomaly detection built-in

### Strumenti Commerciali

- **VMware Aria Operations** (ex vRealize Operations): capacity per ambienti vSphere
- **Datadog Forecasts**: forecasting integrato in piattaforma APM/monitoring
- **Dynatrace Davis AI**: anomaly detection e forecasting AI-driven
- **NetApp ActiveIQ**: capacity planning per storage NetApp
- **AWS Compute Optimizer, Azure Advisor, Google Recommender**: ottimizzazione cloud-native
- **TeamQuest (HelpSystems)**: capacity planning enterprise multi-platform
- **BMC TrueSight Capacity Optimization**: enterprise legacy ma maturo
- **Turbonomic** (IBM): Application Resource Management con ottimizzazione automatica

### Risorse Italiane

- **AgID - Linee guida acquisizione ICT PA**: riferimento per dimensionamento e procurement nella PA italiana
- **Garante Privacy - Linee guida data retention**: impatti capacity di policy retention conformi GDPR
- **Forum CNR Capacity Planning**: comunita italiana practitioner

### Comunita e Conferenze

- **CMG (Computer Measurement Group)**: storica organizzazione capacity, conferenze annuali
- **PerfMa, Performance Engineering Slack**: community informali ma attive
- **SREcon (USENIX)**: conferenze SRE con tracce dedicate capacity
- **KubeCon / CloudNativeCon**: tracce su autoscaling e capacity Kubernetes

---

## FAQ — Domande Frequenti

**1. Ogni quanto devo aggiornare il capacity plan?**

Dipende dalla velocita di cambiamento dell'ambiente. Regola pratica: monitoring continuo, analisi mensile, forecast trimestrale, piano formale semestrale. Per ambienti cloud con auto-scaling, il focus si sposta dalla capacity alla cost optimization — il cloud "non finisce", ma il budget si.

**2. Come si gestisce il capacity planning quando tutto e in cloud?**

Il cloud non elimina la necessita di capacity planning, la trasforma. Invece di pianificare hardware, si pianificano: (a) costi — quanto spendiamo mese per mese, (b) Reserved Instances / Savings Plans — quale base copriamo con commitment, (c) limiti e quote — AWS ha limiti per regione su vCPU, IP, ecc., (d) auto-scaling tuning — scale-out/in policies, target tracking, (e) architecture — quale servizio managed vs self-hosted.

**3. Quanto storico serve per un forecast affidabile?**

Minimo: 3 mesi per trend senza stagionalita (regressione lineare). Ideale: 2 anni per catturare stagionalita annuale. Con Prophet: 2+ anni per yearly_seasonality, 3+ mesi per weekly/daily. Con LSTM: 3+ anni. Per workload nuovi senza storico: benchmark + stima su driver business + revisione dopo 3 mesi di dati reali.

**4. Come si misura l'accuratezza del capacity planning?**

MAPE (Mean Absolute Percentage Error) dei forecast precedenti: <10% = eccellente, 10-20% = buono, 20-30% = accettabile, >30% = richiede revisione del modello. Tracciare MAPE trimestrale e presentarlo nel report capacity — costruisce credibilita e identifica aree di miglioramento.

**5. Il capacity planning ha senso per una PMI con 3 server?**

Assolutamente. La dimensione piccola rende ogni server critico (nessuna ridondanza nasconde i problemi). Un foglio Excel con: (a) utilizzo mensile per server, (b) date fine garanzia, (c) proiezione storage 12 mesi e (d) action plan, richiede 2 ore/mese e previene emergenze costose.

**6. Come gestire il capacity planning per database che crescono in modo imprevedibile?**

Combinare: (a) monitoring granulare (crescita giornaliera, not mensile), (b) alerting su soglia (disco al 80% = avviso), (c) auto-extend dove possibile (cloud managed DB), (d) retention policy per dati vecchi (archivio + purge), (e) partitioning per gestire tabelle grandi. Il dato "imprevedibile" spesso ha pattern una volta analizzato con decomposizione STL.

**7. Quali metriche catturare per il capacity planning di un'applicazione web?**

Minimo: (a) Request rate (req/s), (b) Error rate (%), (c) Latency P50/P95/P99, (d) CPU per container/VM, (e) Memory per container/VM, (f) IOPS database, (g) Connection pool utilization, (h) Queue depth (se applicabile). Queste 8 metriche, raccolte ogni 1-5 minuti per 3+ mesi, alimentano un capacity plan completo.

**8. Come si calcola il costo di un'ora di downtime per giustificare investimenti capacity?**

Formula: Costo downtime = (Fatturato annuo / ore lavorative annue) × fattore impatto. Per un'azienda da €5M fatturato, 2.000 ore lavorative → €2.500/ora di fatturato a rischio. Aggiungere: costo personale IT in emergenza (€60-100/h × persone coinvolte), costo penali SLA se applicabili, costo reputazionale (difficile da quantificare, stimare 2-5x il costo diretto). Risultato tipico PMI: €5.000-15.000 per ora di downtime completo.

---

## Esercizi

1. **Lab — Little's Law applicata.** Sistema con λ=100 req/s, W=200ms; calcola L. Poi calcola il pool size necessario se ogni connessione gestisce 1 richiesta alla volta.

2. **Lab — Baseline construction.** Scarica il dataset CAIDA o genera dati sintetici con `numpy`. Calcola la distribuzione completa (media, P50, P75, P90, P95, P99) per una metrica CPU. Identifica la stagionalita con ACF.

3. **Lab — Monte Carlo simulation.** Implementa la simulazione Monte Carlo per uno storage da 10 TB con crescita 5% mensile. Determina con confidenza 95% quando si raggiunge l'80% di utilizzo.

4. **Lab — USL fitting.** Dato un dataset di throughput vs numero nodi (fornisci i tuoi dati o genera sintetici), fai il fitting della USL. Identifica alpha, beta, e il punto di scalabilita massima.

5. **Lab — Prophet forecast.** Scarica dati da Prometheus (o genera CSV sintetico con stagionalita giornaliera+settimanale) e costruisci un forecast Prophet a 90 giorni. Valida con cross-validation e calcola MAPE.

6. **Stretch — peak modeling.** Black Friday capacity per e-commerce dato historical. Dato un dataset di ordini/giorno per 2 anni, identifica i pattern stagionali, modella il picco Black Friday, e dimensiona l'infrastruttura cloud (numero istanze, tipo, strategia RI/OD/Spot).

7. **Stretch — k6 load test design.** Progetta un test di carico k6 per un'API REST con 3 endpoint (GET catalogo, POST ordine, GET ricerca). Definisci scenari per load test, stress test e spike test. Esegui su ambiente di staging e analizza i risultati.

8. **Stretch — WAN sizing.** Progetta il dimensionamento WAN per una PMI con HQ + 5 filiali (10-30 utenti ciascuna), considerando video conferencing, VoIP, ERP, backup. Calcola la banda necessaria per ogni filiale e il costo annuale stimato con 2 operatori italiani.

## Auto-valutazione

1. Little's Law: formula e variabili. Applicala a un caso concreto.
2. P95 vs P99 vs media: quale usare per capacity planning e perche.
3. Saturation vs utilization: definizione e differenza pratica.
4. Spiega la differenza tra Holt-Winters e ARIMA/SARIMA.
5. Cos'e la Universal Scalability Law e cosa modellano alpha e beta.
6. Descrivi la metodologia USE (Utilization, Saturation, Errors).
7. Descrivi la metodologia RED (Rate, Errors, Duration).
8. Spiega la differenza tra capacity planning a livello Business, Service e Component.
9. Quali sono le soglie di utilizzo raccomandate per CPU, RAM e storage?
10. Come si valida un modello di forecast? Quali metriche di errore si usano?
11. Cosa significa "cambio di regime" in un forecast e come lo si gestisce?
12. Come si dimensiona un connection pool con Little's Law?

## Glossario locale

| Termine | Definizione |
|---|---|
| **Little's Law** | L = λW — relazione fondamentale della teoria delle code |
| **P95/P99** | Percentile di latenza; il valore sotto il quale cade il 95%/99% delle osservazioni |
| **Saturation** | Grado di lavoro in eccesso che una risorsa non puo servire immediatamente |
| **Utilization** | Percentuale del tempo in cui una risorsa e occupata |
| **Forecasting** | Previsione del futuro utilizzo delle risorse basata su dati storici |
| **ARIMA** | AutoRegressive Integrated Moving Average — modello statistico time series |
| **SARIMA** | Seasonal ARIMA — ARIMA con componente stagionale |
| **Prophet** | Modello di forecasting di Meta con supporto stagionalita multipla |
| **Holt-Winters** | Triple exponential smoothing con livello, trend, stagionalita |
| **USL** | Universal Scalability Law — modella la scalabilita reale dei sistemi |
| **STL** | Seasonal-Trend decomposition using Loess |
| **MAPE** | Mean Absolute Percentage Error — metrica di accuratezza forecast |
| **USE** | Utilization, Saturation, Errors — metodologia analisi risorse |
| **RED** | Rate, Errors, Duration — metodologia analisi servizi |
| **Headroom** | Margine di capacity mantenuto per assorbire imprevisti |
| **Overcommit** | Allocazione di risorse virtuali superiore alle risorse fisiche |
| **Baseline** | Rappresentazione statistica del comportamento normale di una risorsa |
| **Changepoint** | Punto temporale in cui il trend di una serie cambia significativamente |
| **Knee point** | Punto della curva utilizzo/latenza dove la latenza inizia a crescere non linearmente |
| **M/M/1** | Modello di coda con arrivi Poisson, servizio esponenziale, 1 server |
| **M/M/c** | Modello di coda con arrivi Poisson, servizio esponenziale, c server |
| **Erlang B** | Formula per calcolare probabilita di blocco in sistema a canali limitati |
| **Erlang C** | Formula per calcolare probabilita di attesa in sistema con coda |
| **Monte Carlo** | Simulazione stocastica con migliaia di traiettorie campionate |
| **RI** | Reserved Instance — impegno cloud a termine con sconto |
| **Savings Plan** | Impegno su spesa oraria cloud con flessibilita su istanze |
| **IOPS** | Input/Output Operations Per Second — misura performance storage |
| **Throughput** | Quantita di lavoro completato per unita di tempo |
| **Bin-packing** | Problema di ottimizzazione: allocazione efficiente di risorse in contenitori |
| **Thin provisioning** | Allocazione storage virtuale maggiore del fisico disponibile |
