# Data Visualization — Principles, Tools, and Security Dashboards

## Indice

1. [Principi di Visualizzazione](#1-principi-di-visualizzazione)
2. [Tipi di Grafici e Quando Usarli](#2-tipi-di-grafici-e-quando-usarli)
3. [Matplotlib e Seaborn](#3-matplotlib-e-seaborn)
4. [Plotly e Visualizzazione Interattiva](#4-plotly-e-visualizzazione-interattiva)
5. [Grafana per Infrastruttura](#5-grafana-per-infrastruttura)
6. [Security Visualization](#6-security-visualization)
7. [Business Intelligence Tools](#7-business-intelligence-tools)
8. [Real-Time Dashboards](#8-real-time-dashboards)
9. [Data Storytelling](#9-data-storytelling)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Principi di Visualizzazione

### 1.1 I Principi di Edward Tufte

Edward Tufte ha stabilito i fondamenti teorici della visualizzazione dati efficace. I suoi principi rimangono il riferimento per qualsiasi professionista che lavori con dati visivi.

#### Data-Ink Ratio

Il rapporto data-ink misura la proporzione di "inchiostro" in un grafico dedicata alla rappresentazione effettiva dei dati rispetto all'inchiostro totale usato.

```
Data-Ink Ratio = (Inchiostro dedicato ai dati) / (Inchiostro totale nel grafico)
```

**Obiettivo:** Massimizzare il data-ink ratio eliminando ogni elemento visivo che non comunica informazione. Ogni pixel deve giustificare la sua esistenza.

Elementi da eliminare:
- Bordi ridondanti intorno ai grafici
- Griglie dense che competono con i dati
- Ombreggiature decorative (drop shadows su barre)
- Sfondi colorati senza funzione informativa
- Legende posizionate lontano dai dati quando l'etichettatura diretta e possibile

```python
import matplotlib.pyplot as plt
import numpy as np

# PRIMA: Basso data-ink ratio (default matplotlib)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

categories = ['Q1', 'Q2', 'Q3', 'Q4']
values = [23, 45, 56, 78]

# Grafico con chartjunk
ax1.bar(categories, values, color='steelblue', edgecolor='black', linewidth=2)
ax1.set_title('Revenue by Quarter', fontsize=14, fontweight='bold')
ax1.grid(True, which='both', linestyle='-', linewidth=0.8, alpha=0.7)
ax1.set_facecolor('#f0f0f0')
ax1.spines['top'].set_visible(True)
ax1.spines['right'].set_visible(True)
ax1.set_ylabel('Revenue ($M)')
ax1.set_xlabel('Quarter')

# DOPO: Alto data-ink ratio (Tufte-style)
ax2.bar(categories, values, color='#2c3e50', width=0.5)
ax2.set_title('Revenue by Quarter', fontsize=12)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.tick_params(left=False)
ax2.set_axisbelow(True)
ax2.yaxis.grid(True, linestyle=':', alpha=0.3)

# Etichette dirette eliminano la necessita dell'asse Y
for i, v in enumerate(values):
    ax2.text(i, v + 1, f'${v}M', ha='center', fontsize=10)

ax2.set_ylim(0, max(values) * 1.15)
plt.tight_layout()
plt.savefig('tufte_comparison.png', dpi=150, bbox_inches='tight')
```

#### Chartjunk

Tufte definisce "chartjunk" qualsiasi elemento decorativo che non trasmette informazione e che potenzialmente distrae dalla comprensione dei dati. Categorie principali:

1. **Moiré vibrations** — pattern ripetitivi che creano effetti ottici fastidiosi
2. **Grid abuse** — griglie troppo dense o prominenti
3. **Duck decorations** — illustrazioni e decorazioni sovrapposte ai dati (il termine viene da un edificio a forma di anatra — la decorazione domina la struttura)

#### Small Multiples

Una serie di grafici identici nella struttura, ciascuno mostrando un sottoinsieme diverso dei dati. Permettono il confronto immediato attraverso la posizione spaziale piuttosto che la memoria.

```python
import seaborn as sns
import pandas as pd

# Small multiples con FacetGrid
tips = sns.load_dataset('tips')
g = sns.FacetGrid(tips, col='day', col_wrap=2, height=3, aspect=1.2)
g.map_dataframe(sns.scatterplot, x='total_bill', y='tip', hue='smoker', alpha=0.7)
g.add_legend()
g.set_axis_labels('Total Bill ($)', 'Tip ($)')
g.set_titles(col_template='{col_name}')
g.tight_layout()
```

#### Lie Factor

Misura la distorsione visiva:

```
Lie Factor = (Dimensione dell'effetto mostrato nel grafico) / (Dimensione dell'effetto nei dati)
```

Un lie factor di 1.0 e perfettamente accurato. Valori > 1.05 o < 0.95 indicano distorsione significativa.

### 1.2 Leggi della Gestalt Applicate ai Grafici

Le leggi della Gestalt descrivono come il cervello umano organizza le informazioni visive in pattern coerenti.

| Legge | Applicazione nella Visualizzazione |
|-------|-----------------------------------|
| **Prossimita** | Raggruppare barre correlate, spacing tra categorie |
| **Similarita** | Colore/forma consistente per la stessa serie dati |
| **Continuita** | Line chart seguono l'occhio naturalmente da sinistra a destra |
| **Chiusura** | Il cervello completa forme incomplete (utile per sparklines) |
| **Figura-sfondo** | Dati in primo piano, griglia e assi come sfondo |
| **Connessione** | Linee che collegano punti correlati |
| **Destino comune** | Elementi che si muovono insieme sono percepiti come gruppo |

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Prossimita: raggruppamento visivo
ax = axes[0]
groups = [[1, 2, 3], [5, 6, 7], [9, 10, 11]]
colors = ['#e74c3c', '#3498db', '#2ecc71']
for g_idx, group in enumerate(groups):
    for x in group:
        ax.bar(x, np.random.randint(20, 80), color=colors[g_idx], width=0.7)
ax.set_title('Prossimita: Raggruppamento')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Similarita: colore per categoria
ax = axes[1]
x = np.random.randn(50)
y = np.random.randn(50)
categories = np.random.choice(['A', 'B', 'C'], 50)
for cat, color in zip(['A', 'B', 'C'], colors):
    mask = categories == cat
    ax.scatter(x[mask], y[mask], c=color, label=cat, s=60, alpha=0.7)
ax.set_title('Similarita: Colore per Categoria')
ax.legend()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Continuita: line chart
ax = axes[2]
x_line = np.linspace(0, 10, 50)
ax.plot(x_line, np.sin(x_line), linewidth=2, color=colors[0], label='Metrica A')
ax.plot(x_line, np.cos(x_line), linewidth=2, color=colors[1], label='Metrica B')
ax.set_title('Continuita: Linee Guida')
ax.legend()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
```

### 1.3 Attributi Pre-Attentivi

Gli attributi pre-attentivi sono proprieta visive che il cervello processa in modo automatico e parallelo (< 250ms), prima dell'attenzione cosciente. Questo li rende strumenti potenti per dirigere l'attenzione.

**Canali pre-attentivi ordinati per efficacia nella codifica quantitativa:**

1. **Posizione** — Il canale piu accurato. Usato negli scatter plot e nei grafici a punti.
2. **Lunghezza** — Bar chart. Accurato per confronti se la baseline e comune.
3. **Angolo/Inclinazione** — Limitato. I pie chart sfruttano questo (male).
4. **Area** — Bubble chart. Sottostimata sistematicamente (~0.7 esponente).
5. **Colore (luminosita)** — Heatmap. Buono per continuo, non per valori esatti.
6. **Colore (saturazione)** — Utile per ordinamenti, non per valori precisi.
7. **Colore (tinta)** — Solo categorico (max 7-10 categorie distinte).

```python
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# Posizione
ax = axes[0, 0]
data = np.random.randn(30)
ax.scatter(range(30), data, c='#2c3e50', s=40)
ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
ax.set_title('Posizione (piu accurato)')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Lunghezza
ax = axes[0, 1]
vals = np.random.randint(10, 90, 8)
ax.barh(range(8), vals, color='#2c3e50')
ax.set_title('Lunghezza')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Area
ax = axes[0, 2]
sizes = np.random.randint(100, 2000, 20)
ax.scatter(np.random.randn(20), np.random.randn(20), s=sizes, alpha=0.5, c='#2c3e50')
ax.set_title('Area (sottostimata)')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Colore (luminosita)
ax = axes[1, 0]
matrix = np.random.rand(8, 8)
im = ax.imshow(matrix, cmap='Blues')
ax.set_title('Luminosita')
plt.colorbar(im, ax=ax, shrink=0.8)

# Colore (tinta) - categorico
ax = axes[1, 1]
for i, c in enumerate(['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']):
    ax.scatter(np.random.randn(10) + i, np.random.randn(10), c=c, s=60, label=f'Cat {i+1}')
ax.set_title('Tinta (categorico)')
ax.legend(fontsize=8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Orientamento
ax = axes[1, 2]
for i in range(20):
    angle = np.random.uniform(0, 180)
    x_pos = np.random.uniform(0, 10)
    y_pos = np.random.uniform(0, 10)
    dx = 0.4 * np.cos(np.radians(angle))
    dy = 0.4 * np.sin(np.radians(angle))
    ax.plot([x_pos - dx, x_pos + dx], [y_pos - dy, y_pos + dy],
            'k-', linewidth=2)
ax.set_title('Orientamento')
ax.set_xlim(-1, 11)
ax.set_ylim(-1, 11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
```

### 1.4 Teoria del Carico Cognitivo

La teoria del carico cognitivo (Sweller, 1988) distingue tre tipi di carico:

1. **Intrinseco** — Complessita inherente nei dati stessi
2. **Estraneo** — Carico aggiunto da design scadente (chartjunk, layout confuso)
3. **Pertinente** — Carico che contribuisce alla comprensione (schema building)

**Strategie per ridurre il carico estraneo:**

- **Chunking**: Raggruppare informazioni correlate (max 7 +/- 2 elementi)
- **Progressive disclosure**: Mostrare overview prima, dettagli on-demand
- **Consistency**: Stesso colore = stessa categoria in tutto il dashboard
- **Spatial contiguity**: Etichette vicine agli elementi che descrivono
- **Signaling**: Evidenziare (highlight) i pattern chiave piuttosto che lasciare che l'utente li cerchi

### 1.5 Visualizzazioni Ingannevoli

Pattern comuni di manipolazione visiva (accidentale o intenzionale):

| Tecnica | Effetto | Difesa |
|---------|---------|--------|
| **Asse Y troncato** | Amplifica differenze minime | Includere sempre lo zero per bar chart |
| **Cherry-picking temporale** | Narrativa selettiva | Mostrare il contesto completo |
| **Scala doppio-asse** | Correlazione spuria | Usare solo se le unita sono naturalmente collegate |
| **Area 3D** | Distorsione prospettica | Mai usare 3D per dati 2D |
| **Pie chart esplosivi** | Enfasi artificiale su una fetta | Usare bar chart ordinati |
| **Scala logaritmica non dichiarata** | Appiattisce crescita esponenziale | Dichiarare sempre il tipo di scala |
| **Inversione degli assi** | "Piu in basso = meglio" confonde | Mantenere la direzione convenzionale |

```python
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

# INGANNEVOLE: asse Y troncato
values_trunc = [92, 94, 95, 97]
ax1.bar(['A', 'B', 'C', 'D'], values_trunc, color='#e74c3c')
ax1.set_ylim(90, 100)
ax1.set_title('INGANNEVOLE: Asse troncato\n(differenze sembrano enormi)')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# ONESTO: asse Y da zero
ax2.bar(['A', 'B', 'C', 'D'], values_trunc, color='#2ecc71')
ax2.set_ylim(0, 100)
ax2.set_title('ONESTO: Asse da zero\n(differenze proporzionate)')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()
```

---

## 2. Tipi di Grafici e Quando Usarli

### 2.1 Confronto (Comparison)

#### Bar Chart (Orizzontale e Verticale)

**Quando:** Confrontare valori tra categorie discrete (< 20 categorie). Preferire orizzontale quando le etichette sono lunghe.

```python
import matplotlib.pyplot as plt
import pandas as pd

# Bar chart orizzontale ordinato — best practice
data = pd.DataFrame({
    'threat': ['Phishing', 'Ransomware', 'DDoS', 'SQL Injection',
               'XSS', 'Insider Threat', 'Zero-Day'],
    'incidents': [342, 189, 156, 98, 87, 65, 23]
}).sort_values('incidents')

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(data['threat'], data['incidents'], color='#2c3e50', height=0.6)

# Evidenziare il valore massimo
bars[-1].set_color('#e74c3c')

# Etichette dirette
for bar in bars:
    width = bar.get_width()
    ax.text(width + 5, bar.get_y() + bar.get_height()/2,
            f'{int(width)}', va='center', fontsize=9)

ax.set_xlabel('Incidents (2024)')
ax.set_title('Security Incidents by Type')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.tick_params(bottom=False)
ax.set_xlim(0, max(data['incidents']) * 1.15)
plt.tight_layout()
```

#### Grouped Bar Chart

**Quando:** Confrontare sottocategorie tra gruppi (max 3-4 sottogruppi per leggibilita).

#### Stacked Bar Chart

**Quando:** Mostrare come parti compongono il totale per ogni categoria. Limitazione: difficile confrontare le sezioni interne non a baseline.

#### Dot Plot (Cleveland)

**Quando:** Alternativa al bar chart con molte categorie. Piu compatto, meno ink. Eccellente per confronti paired (before/after).

```python
fig, ax = plt.subplots(figsize=(8, 6))

categories = ['Authentication', 'Network', 'Application', 'Data', 'Physical']
before = [45, 67, 34, 78, 89]
after = [82, 85, 71, 92, 95]

y_pos = range(len(categories))

# Linee di connessione
for i in y_pos:
    ax.plot([before[i], after[i]], [i, i], 'gray', linewidth=1, zorder=1)

# Punti
ax.scatter(before, y_pos, color='#e74c3c', s=80, zorder=2, label='Before')
ax.scatter(after, y_pos, color='#2ecc71', s=80, zorder=2, label='After')

ax.set_yticks(y_pos)
ax.set_yticklabels(categories)
ax.set_xlabel('Security Score')
ax.set_title('Security Posture: Before vs After Remediation')
ax.legend(loc='lower right')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xlim(20, 100)
plt.tight_layout()
```

### 2.2 Distribuzione (Distribution)

| Tipo | Quando Usarlo | Limitazioni |
|------|--------------|-------------|
| **Histogram** | Una variabile, forma della distribuzione | Sensibile a bin width |
| **KDE (Kernel Density)** | Distribuzione lisciata, confronto overlapping | Bandwidth selection critica |
| **Boxplot** | Sommario statistico (mediana, IQR, outlier) | Nasconde la forma (bimodale invisibile) |
| **Violin** | Distribuzione completa + sommario statistico | Puo confondere utenti non tecnici |
| **Ridgeline** | Confrontare molte distribuzioni | Richiede > 5 gruppi per essere efficace |
| **Strip/Swarm** | Ogni punto individuale visibile | Solo per n < 500 |

```python
import seaborn as sns
import numpy as np

np.random.seed(42)
data = pd.DataFrame({
    'response_time': np.concatenate([
        np.random.exponential(2, 200),
        np.random.normal(8, 1.5, 150),
        np.random.exponential(1, 100)
    ]),
    'severity': np.concatenate([
        ['Low'] * 200,
        ['Medium'] * 150,
        ['High'] * 100
    ])
})

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Violin plot
sns.violinplot(data=data, x='severity', y='response_time',
               order=['Low', 'Medium', 'High'], ax=axes[0], inner='box')
axes[0].set_title('Violin: Response Time by Severity')
axes[0].set_ylabel('Response Time (min)')

# Boxplot
sns.boxplot(data=data, x='severity', y='response_time',
            order=['Low', 'Medium', 'High'], ax=axes[1])
axes[1].set_title('Boxplot: Response Time by Severity')

# Ridgeline (usando KDE multipli)
from matplotlib import cm
severities = ['Low', 'Medium', 'High']
colors_ridge = ['#3498db', '#f39c12', '#e74c3c']
for i, (sev, color) in enumerate(zip(severities, colors_ridge)):
    subset = data[data['severity'] == sev]['response_time']
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(subset)
    x_range = np.linspace(0, 15, 200)
    density = kde(x_range)
    axes[2].fill_between(x_range, i + density * 3, i, alpha=0.7, color=color)
    axes[2].plot(x_range, i + density * 3, color='black', linewidth=0.5)
    axes[2].text(-1, i + 0.1, sev, fontsize=9, va='bottom')

axes[2].set_title('Ridgeline: Response Time Distribution')
axes[2].set_xlabel('Response Time (min)')
axes[2].set_yticks([])
axes[2].spines['top'].set_visible(False)
axes[2].spines['right'].set_visible(False)
axes[2].spines['left'].set_visible(False)

plt.tight_layout()
```

### 2.3 Relazione (Relationship)

- **Scatter plot** — Due variabili continue. Aggiungere colore per terza variabile categorica, size per quarta quantitativa.
- **Bubble chart** — Scatter con area proporzionale a una terza variabile. Limitare a 50-100 punti.
- **Connected scatter** — Mostra traiettoria temporale nello spazio bidimensionale.

### 2.4 Composizione (Composition)

- **Pie/Donut** — Solo per parti di un intero con <= 5 categorie. Mai per confronti precisi.
- **Treemap** — Dati gerarchici dove l'area rappresenta la grandezza. Utile per file system, budget, portfolio.
- **Stacked area** — Composizione che cambia nel tempo. Usare solo se il totale e significativo.

### 2.5 Temporale (Temporal)

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Generare dati temporali di sicurezza
dates = pd.date_range('2024-01-01', periods=365, freq='D')
np.random.seed(42)
alerts = np.random.poisson(lam=15, size=365) + np.sin(np.arange(365) / 30) * 5

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(dates, alerts, linewidth=0.8, color='#2c3e50', alpha=0.6)

# Moving average per trend
window = 14
ma = pd.Series(alerts).rolling(window).mean()
ax.plot(dates, ma, linewidth=2, color='#e74c3c', label=f'{window}-day MA')

# Annotazione evento
peak_idx = np.argmax(alerts)
ax.annotate('Incident Spike',
            xy=(dates[peak_idx], alerts[peak_idx]),
            xytext=(dates[peak_idx] + pd.Timedelta(days=20), alerts[peak_idx] + 5),
            arrowprops=dict(arrowstyle='->', color='#e74c3c'),
            fontsize=9, color='#e74c3c')

ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.set_title('Daily Security Alerts — 2024')
ax.set_ylabel('Alert Count')
ax.legend()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
```

#### Heatmap Calendar

```python
# Calendar heatmap per alert giornalieri
fig, ax = plt.subplots(figsize=(12, 3))

# Reshape in settimane x giorni
cal_data = np.zeros((7, 53))
for i, val in enumerate(alerts[:365]):
    week = i // 7
    day = i % 7
    if week < 53:
        cal_data[day, week] = val

im = ax.imshow(cal_data, cmap='YlOrRd', aspect='auto')
ax.set_yticks(range(7))
ax.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
ax.set_xlabel('Week of Year')
ax.set_title('Alert Heatmap Calendar')
plt.colorbar(im, ax=ax, shrink=0.8, label='Alerts')
plt.tight_layout()
```

### 2.6 Gerarchico (Hierarchical)

- **Treemap** — Area proporzionale al valore. Buono per budget, disk usage, asset inventory.
- **Sunburst** — Anelli concentrici per gerarchia multi-livello. Alternativa circolare al treemap.

### 2.7 Geografico (Geographic)

- **Choropleth** — Regioni colorate per valore aggregato. Attenzione: aree grandi dominano visivamente.
- **Dot map** — Punti per eventi geolocati. Migliore per densita.
- **Hex bin map** — Alternativa al dot map per aggregare densita.

---

## 3. Matplotlib e Seaborn

### 3.1 Architettura Matplotlib

Matplotlib e organizzato in tre livelli:

```
Backend Layer (rendering)
    |
Artist Layer (Figure, Axes, primitivi grafici)
    |
Scripting Layer (pyplot — interfaccia stateful)
```

**Gerarchia degli oggetti:**

```
Figure (contenitore top-level)
├── Axes (area del grafico — il piu importante)
│   ├── XAxis
│   │   ├── Tick objects
│   │   └── Label
│   ├── YAxis
│   ├── Title
│   ├── Lines (Line2D objects)
│   ├── Patches (Rectangle, Polygon, etc.)
│   ├── Text objects
│   └── Legend
├── Suptitle
└── Subplots layout manager
```

### 3.2 Object-Oriented API

Sempre preferire l'API object-oriented rispetto a `plt.*` per codice production:

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_security_dashboard_panel():
    """Pannello per metriche di sicurezza con stile professionale."""

    fig = plt.figure(figsize=(14, 8))

    # Layout con GridSpec per controllo preciso
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3,
                          left=0.06, right=0.97, top=0.92, bottom=0.08)

    ax_timeline = fig.add_subplot(gs[0, :2])
    ax_severity = fig.add_subplot(gs[0, 2])
    ax_categories = fig.add_subplot(gs[1, :2])
    ax_kpi = fig.add_subplot(gs[1, 2])

    # --- Timeline degli incidenti ---
    np.random.seed(42)
    days = 90
    dates = pd.date_range('2024-01-01', periods=days, freq='D')
    incidents = np.random.poisson(8, days)
    resolved = np.random.poisson(7, days)

    ax_timeline.fill_between(dates, incidents, alpha=0.3, color='#e74c3c', label='New')
    ax_timeline.fill_between(dates, resolved, alpha=0.3, color='#2ecc71', label='Resolved')
    ax_timeline.plot(dates, incidents, color='#e74c3c', linewidth=1.5)
    ax_timeline.plot(dates, resolved, color='#2ecc71', linewidth=1.5)
    ax_timeline.set_title('Incident Timeline (90 Days)', fontsize=11, loc='left')
    ax_timeline.legend(loc='upper right', frameon=False)
    ax_timeline.spines['top'].set_visible(False)
    ax_timeline.spines['right'].set_visible(False)
    ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax_timeline.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))

    # --- Severity Distribution ---
    severities = ['Critical', 'High', 'Medium', 'Low']
    counts = [12, 45, 89, 234]
    colors_sev = ['#e74c3c', '#f39c12', '#3498db', '#95a5a6']

    wedges, texts, autotexts = ax_severity.pie(
        counts, labels=severities, colors=colors_sev,
        autopct='%1.0f%%', startangle=90,
        textprops={'fontsize': 9}
    )
    ax_severity.set_title('Severity Split', fontsize=11)

    # --- Top Categories ---
    cats = ['Phishing', 'Malware', 'Unauthorized\nAccess', 'Data Leak',
            'DDoS', 'Misconfiguration']
    cat_counts = [156, 98, 76, 54, 32, 28]

    bars = ax_categories.barh(cats, cat_counts, color='#34495e', height=0.6)
    bars[0].set_color('#e74c3c')  # Highlight top
    ax_categories.set_title('Top Incident Categories', fontsize=11, loc='left')
    ax_categories.spines['top'].set_visible(False)
    ax_categories.spines['right'].set_visible(False)

    for bar in bars:
        w = bar.get_width()
        ax_categories.text(w + 2, bar.get_y() + bar.get_height()/2,
                          str(int(w)), va='center', fontsize=9)
    ax_categories.set_xlim(0, max(cat_counts) * 1.15)

    # --- KPI Panel ---
    ax_kpi.axis('off')
    kpis = [
        ('MTTD', '2.3h', '#e74c3c'),
        ('MTTR', '4.7h', '#f39c12'),
        ('SLA Met', '94%', '#2ecc71'),
    ]
    for i, (label, value, color) in enumerate(kpis):
        y = 0.8 - i * 0.3
        ax_kpi.text(0.5, y, value, fontsize=20, fontweight='bold',
                   ha='center', va='center', color=color,
                   transform=ax_kpi.transAxes)
        ax_kpi.text(0.5, y - 0.08, label, fontsize=10,
                   ha='center', va='center', color='#7f8c8d',
                   transform=ax_kpi.transAxes)

    fig.suptitle('SOC Dashboard — Q1 2024', fontsize=13, fontweight='bold', y=0.97)
    return fig

fig = create_security_dashboard_panel()
plt.savefig('security_dashboard_mpl.png', dpi=150, bbox_inches='tight',
            facecolor='white')
```

### 3.3 Customization Avanzata

#### rcParams e Style Sheets

```python
# Creare un custom style
custom_style = {
    'figure.facecolor': '#ffffff',
    'axes.facecolor': '#ffffff',
    'axes.edgecolor': '#cccccc',
    'axes.labelcolor': '#333333',
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.color': '#666666',
    'ytick.color': '#666666',
    'grid.color': '#eeeeee',
    'grid.linestyle': ':',
    'font.family': 'sans-serif',
    'font.size': 10,
    'lines.linewidth': 1.5,
    'figure.dpi': 150,
}

# Applicare
plt.rcParams.update(custom_style)

# Oppure salvare come .mplstyle
# Percorso: ~/.config/matplotlib/stylelib/security.mplstyle
# Usare: plt.style.use('security')
```

#### Publication-Quality Figures

```python
def setup_publication_style():
    """Configurazione per figure da pubblicazione scientifica."""
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Computer Modern Roman', 'Times New Roman'],
        'font.size': 8,
        'axes.titlesize': 9,
        'axes.labelsize': 8,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'legend.fontsize': 7,
        'figure.figsize': (3.5, 2.5),  # Single column width
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.02,
        'lines.linewidth': 1.0,
        'lines.markersize': 4,
        'axes.linewidth': 0.5,
        'grid.linewidth': 0.3,
        'xtick.major.width': 0.5,
        'ytick.major.width': 0.5,
        'text.usetex': True,  # Usa LaTeX per il testo
    })
```

### 3.4 Seaborn Statistical Plots

```python
import seaborn as sns

# Impostare il tema
sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)

# --- regplot con intervallo di confidenza ---
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Regression plot
np.random.seed(42)
vuln_count = np.random.poisson(20, 100)
breach_risk = 0.3 * vuln_count + np.random.normal(0, 2, 100)

sns.regplot(x=vuln_count, y=breach_risk, ax=axes[0],
            scatter_kws={'alpha': 0.5, 's': 30},
            line_kws={'color': '#e74c3c'})
axes[0].set_xlabel('Vulnerability Count')
axes[0].set_ylabel('Breach Risk Score')
axes[0].set_title('Vulnerabilities vs Risk')

# Pairplot (in un subplot separato sarebbe FacetGrid)
# Heatmap di correlazione
corr_data = pd.DataFrame({
    'Phishing': np.random.randn(50),
    'Malware': np.random.randn(50),
    'DDoS': np.random.randn(50),
    'Insider': np.random.randn(50),
    'Ransomware': np.random.randn(50),
})
corr_matrix = corr_data.corr()

sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, square=True, ax=axes[1],
            cbar_kws={'shrink': 0.8})
axes[1].set_title('Threat Correlation Matrix')

# Catplot-style: boxenplot
threat_data = pd.DataFrame({
    'response_time': np.concatenate([
        np.random.exponential(2, 80),
        np.random.exponential(4, 80),
        np.random.exponential(1, 80)
    ]),
    'team': np.repeat(['Alpha', 'Beta', 'Gamma'], 80)
})

sns.boxenplot(data=threat_data, x='team', y='response_time',
              ax=axes[2], palette='Set2')
axes[2].set_title('Response Time by SOC Team')
axes[2].set_ylabel('Hours')

plt.tight_layout()
```

### 3.5 Animazione

```python
from matplotlib.animation import FuncAnimation

def create_animated_timeline():
    """Animazione di alert accumulati nel tempo."""
    fig, ax = plt.subplots(figsize=(10, 4))

    np.random.seed(42)
    n_frames = 100
    cumulative_alerts = np.cumsum(np.random.poisson(5, n_frames))
    x_data = list(range(n_frames))

    line, = ax.plot([], [], linewidth=2, color='#e74c3c')
    fill = None

    ax.set_xlim(0, n_frames)
    ax.set_ylim(0, cumulative_alerts[-1] * 1.1)
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Cumulative Alerts')
    ax.set_title('Real-Time Alert Accumulation')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    def init():
        line.set_data([], [])
        return [line]

    def animate(frame):
        line.set_data(x_data[:frame+1], cumulative_alerts[:frame+1])
        return [line]

    anim = FuncAnimation(fig, animate, init_func=init,
                         frames=n_frames, interval=50, blit=True)
    # anim.save('alert_timeline.gif', writer='pillow', fps=20)
    return anim
```

---

## 4. Plotly e Visualizzazione Interattiva

### 4.1 Plotly Express — Rapid Prototyping

Plotly Express fornisce un'API ad alto livello per creare grafici interattivi con una singola chiamata:

```python
import plotly.express as px
import pandas as pd
import numpy as np

# Dataset di sicurezza simulato
np.random.seed(42)
n = 500
security_df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=n, freq='H'),
    'severity': np.random.choice(['Critical', 'High', 'Medium', 'Low'], n,
                                  p=[0.05, 0.15, 0.35, 0.45]),
    'source_ip': [f'10.0.{np.random.randint(1,5)}.{np.random.randint(1,255)}'
                  for _ in range(n)],
    'response_time_min': np.random.exponential(3, n),
    'category': np.random.choice(['Phishing', 'Malware', 'DDoS', 'Brute Force',
                                   'Data Exfil'], n),
    'resolved': np.random.choice([True, False], n, p=[0.7, 0.3])
})

# Timeline interattiva con color-coding per severity
fig = px.scatter(security_df, x='timestamp', y='response_time_min',
                 color='severity', size='response_time_min',
                 color_discrete_map={
                     'Critical': '#e74c3c', 'High': '#f39c12',
                     'Medium': '#3498db', 'Low': '#95a5a6'
                 },
                 hover_data=['category', 'source_ip'],
                 title='Security Incidents — Response Time Analysis')

fig.update_layout(
    template='plotly_white',
    xaxis_title='Time',
    yaxis_title='Response Time (min)',
    legend_title='Severity'
)

# Sunburst per composizione gerarchica
fig_sun = px.sunburst(
    security_df,
    path=['severity', 'category'],
    title='Incident Hierarchy: Severity > Category'
)

# Animated scatter (se c'e una dimensione temporale discreta)
security_df['day'] = security_df['timestamp'].dt.date.astype(str)
```

### 4.2 Plotly Graph Objects — Controllo Completo

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_soc_dashboard():
    """Dashboard SOC multi-pannello con Plotly."""

    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=('Alert Volume (24h)', 'MTTD Trend', 'Severity Distribution',
                       'Top Threat Sources', 'Resolution Rate', 'Active Incidents'),
        specs=[
            [{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'pie'}],
            [{'type': 'bar'}, {'type': 'scatter'}, {'type': 'indicator'}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )

    # Panel 1: Alert Volume
    hours = list(range(24))
    alert_vol = [12, 8, 5, 3, 4, 6, 15, 28, 45, 52, 48, 43,
                 38, 42, 47, 51, 44, 38, 32, 28, 22, 18, 15, 13]

    fig.add_trace(go.Scatter(
        x=hours, y=alert_vol,
        mode='lines+markers',
        fill='tonexty',
        fillcolor='rgba(231, 76, 60, 0.1)',
        line=dict(color='#e74c3c', width=2),
        marker=dict(size=4),
        name='Alerts'
    ), row=1, col=1)

    # Panel 2: MTTD Trend
    days = list(range(30))
    mttd = [4.2, 3.8, 4.5, 3.9, 3.2, 3.5, 2.8, 3.1, 2.9, 2.7,
            2.5, 2.8, 2.3, 2.6, 2.4, 2.2, 2.5, 2.1, 2.3, 2.0,
            1.9, 2.1, 1.8, 2.0, 1.7, 1.9, 1.6, 1.8, 1.5, 1.7]

    fig.add_trace(go.Scatter(
        x=days, y=mttd,
        mode='lines',
        line=dict(color='#2ecc71', width=2),
        name='MTTD (hours)'
    ), row=1, col=2)

    # Target line
    fig.add_hline(y=2.0, line_dash='dash', line_color='#e74c3c',
                  annotation_text='Target: 2h', row=1, col=2)

    # Panel 3: Severity Pie
    fig.add_trace(go.Pie(
        labels=['Critical', 'High', 'Medium', 'Low'],
        values=[8, 23, 45, 124],
        marker=dict(colors=['#e74c3c', '#f39c12', '#3498db', '#95a5a6']),
        textinfo='percent+label',
        hole=0.4
    ), row=1, col=3)

    # Panel 4: Top Sources
    sources = ['RU-185.x.x.x', 'CN-42.x.x.x', 'US-192.x.x.x',
               'BR-177.x.x.x', 'IN-103.x.x.x']
    source_counts = [89, 67, 45, 34, 23]

    fig.add_trace(go.Bar(
        y=sources, x=source_counts,
        orientation='h',
        marker=dict(color='#34495e'),
        name='Source IPs'
    ), row=2, col=1)

    # Panel 5: Resolution Rate
    res_days = list(range(30))
    res_rate = [78, 82, 79, 85, 88, 84, 87, 90, 88, 92,
                89, 91, 93, 90, 94, 92, 95, 93, 91, 94,
                96, 93, 95, 94, 96, 95, 97, 94, 96, 95]

    fig.add_trace(go.Scatter(
        x=res_days, y=res_rate,
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(46, 204, 113, 0.2)',
        line=dict(color='#2ecc71', width=2),
        name='Resolution %'
    ), row=2, col=2)

    # Panel 6: Active Incidents Gauge
    fig.add_trace(go.Indicator(
        mode='gauge+number+delta',
        value=42,
        delta={'reference': 56, 'decreasing': {'color': '#2ecc71'}},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': '#e74c3c'},
            'steps': [
                {'range': [0, 30], 'color': '#d5f5e3'},
                {'range': [30, 60], 'color': '#fdebd0'},
                {'range': [60, 100], 'color': '#fadbd8'}
            ],
            'threshold': {
                'line': {'color': 'black', 'width': 2},
                'thickness': 0.75,
                'value': 50
            }
        },
        title={'text': 'Active'}
    ), row=2, col=3)

    fig.update_layout(
        height=700,
        showlegend=False,
        title_text='SOC Operations Dashboard',
        title_x=0.5,
        template='plotly_white'
    )

    return fig

dashboard = create_soc_dashboard()
# dashboard.write_html('soc_dashboard.html')
# dashboard.show()
```

### 4.3 Dash Framework

Dash e il framework di Plotly per costruire applicazioni web analitiche interattive.

```python
from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- App Setup ---
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# --- Simulated Data ---
np.random.seed(42)
n_records = 1000
df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=n_records, freq='h'),
    'alert_type': np.random.choice(
        ['Phishing', 'Malware', 'DDoS', 'Brute Force', 'Insider'], n_records
    ),
    'severity': np.random.choice(
        ['Critical', 'High', 'Medium', 'Low'], n_records,
        p=[0.05, 0.2, 0.35, 0.4]
    ),
    'response_min': np.random.exponential(15, n_records),
    'resolved': np.random.choice([True, False], n_records, p=[0.75, 0.25]),
    'source_country': np.random.choice(
        ['US', 'RU', 'CN', 'BR', 'DE', 'IN'], n_records
    )
})

# --- Layout ---
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2('Security Operations Dashboard'), width=8),
        dbc.Col(
            dcc.Dropdown(
                id='severity-filter',
                options=[{'label': s, 'value': s}
                         for s in ['All', 'Critical', 'High', 'Medium', 'Low']],
                value='All',
                clearable=False
            ), width=4
        )
    ], className='my-3'),

    # KPI Cards
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-total', className='text-center'),
            html.P('Total Alerts', className='text-center text-muted')
        ])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-mttr', className='text-center'),
            html.P('Avg MTTR', className='text-center text-muted')
        ])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-resolved', className='text-center'),
            html.P('Resolution Rate', className='text-center text-muted')
        ])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-critical', className='text-center text-danger'),
            html.P('Critical Alerts', className='text-center text-muted')
        ])), width=3),
    ], className='mb-3'),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Graph(id='timeline-chart'), width=8),
        dbc.Col(dcc.Graph(id='severity-pie'), width=4),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='category-bar'), width=6),
        dbc.Col(dcc.Graph(id='geo-chart'), width=6),
    ]),

    # Auto-refresh
    dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0)
], fluid=True)


# --- Callbacks ---
@callback(
    [Output('kpi-total', 'children'),
     Output('kpi-mttr', 'children'),
     Output('kpi-resolved', 'children'),
     Output('kpi-critical', 'children'),
     Output('timeline-chart', 'figure'),
     Output('severity-pie', 'figure'),
     Output('category-bar', 'figure'),
     Output('geo-chart', 'figure')],
    [Input('severity-filter', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_dashboard(severity, n):
    filtered = df if severity == 'All' else df[df['severity'] == severity]

    # KPIs
    total = len(filtered)
    mttr = f"{filtered['response_min'].mean():.1f} min"
    resolved = f"{filtered['resolved'].sum() / len(filtered) * 100:.0f}%"
    critical = len(filtered[filtered['severity'] == 'Critical'])

    # Timeline
    daily = filtered.set_index('timestamp').resample('D').size().reset_index(name='count')
    fig_timeline = px.area(daily, x='timestamp', y='count',
                           title='Daily Alert Volume',
                           template='plotly_dark')

    # Severity Pie
    sev_counts = filtered['severity'].value_counts()
    fig_pie = px.pie(values=sev_counts.values, names=sev_counts.index,
                     color=sev_counts.index,
                     color_discrete_map={
                         'Critical': '#e74c3c', 'High': '#f39c12',
                         'Medium': '#3498db', 'Low': '#95a5a6'
                     },
                     title='Severity Distribution',
                     template='plotly_dark', hole=0.4)

    # Category Bar
    cat_counts = filtered['alert_type'].value_counts()
    fig_bar = px.bar(x=cat_counts.values, y=cat_counts.index,
                     orientation='h', title='Alerts by Category',
                     template='plotly_dark')
    fig_bar.update_traces(marker_color='#3498db')

    # Geographic
    geo_counts = filtered['source_country'].value_counts().reset_index()
    geo_counts.columns = ['country', 'count']
    fig_geo = px.choropleth(geo_counts, locations='country',
                            locationmode='ISO-3', color='count',
                            title='Alert Sources by Country',
                            template='plotly_dark',
                            color_continuous_scale='Reds')

    return (str(total), mttr, resolved, str(critical),
            fig_timeline, fig_pie, fig_bar, fig_geo)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
```

### 4.4 Esportazione e Condivisione

```python
# Esportazione statica (richiede kaleido)
# pip install kaleido
fig.write_image('dashboard.png', width=1200, height=800, scale=2)
fig.write_image('dashboard.svg')
fig.write_image('dashboard.pdf')

# Esportazione HTML interattiva (standalone)
fig.write_html('dashboard.html', include_plotlyjs='cdn')

# Embed in notebook
fig.show()

# JSON per integrazione API
fig_json = fig.to_json()
```

---

## 5. Grafana per Infrastruttura

### 5.1 Data Sources

Grafana si connette a molteplici backend di dati:

| Data Source | Use Case | Query Language |
|-------------|----------|----------------|
| **Prometheus** | Metriche infrastrutturali, SLI/SLO | PromQL |
| **InfluxDB** | Time-series ad alta cardinalita | Flux / InfluxQL |
| **Elasticsearch** | Log aggregation, security events | Lucene / KQL |
| **PostgreSQL** | Business metrics, asset inventory | SQL |
| **Loki** | Log aggregation (lightweight) | LogQL |
| **CloudWatch** | AWS metrics e log | CloudWatch syntax |
| **Tempo** | Distributed tracing | TraceQL |

### 5.2 Panel Types

```json
{
  "panels": [
    {
      "title": "Alert Rate",
      "type": "timeseries",
      "description": "Grafici temporali: il pannello piu versatile",
      "fieldConfig": {
        "defaults": {
          "custom": {
            "drawStyle": "line",
            "lineInterpolation": "smooth",
            "fillOpacity": 10,
            "gradientMode": "scheme",
            "thresholdsStyle": { "mode": "area" }
          },
          "thresholds": {
            "steps": [
              { "color": "green", "value": null },
              { "color": "yellow", "value": 50 },
              { "color": "red", "value": 100 }
            ]
          }
        }
      }
    },
    {
      "title": "Active Incidents",
      "type": "stat",
      "description": "KPI singolo con sparkline opzionale",
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "steps": [
              { "color": "green", "value": null },
              { "color": "yellow", "value": 20 },
              { "color": "red", "value": 50 }
            ]
          }
        }
      },
      "options": {
        "graphMode": "area",
        "colorMode": "background",
        "textMode": "value_and_name"
      }
    },
    {
      "title": "CPU Usage",
      "type": "gauge",
      "description": "Valore corrente con range e soglie"
    },
    {
      "title": "Security Events",
      "type": "table",
      "description": "Dati tabulari con filtri e sorting"
    },
    {
      "title": "Request Latency",
      "type": "heatmap",
      "description": "Distribuzione nel tempo (latency buckets)"
    },
    {
      "title": "Infrastructure Map",
      "type": "geomap",
      "description": "Dati geolocalizzati su mappa"
    }
  ]
}
```

### 5.3 Variables e Templating

Le variabili rendono i dashboard dinamici e riutilizzabili:

```json
{
  "templating": {
    "list": [
      {
        "name": "environment",
        "type": "custom",
        "query": "production,staging,development",
        "current": { "text": "production", "value": "production" },
        "multi": false
      },
      {
        "name": "host",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(node_cpu_seconds_total{env=\"$environment\"}, instance)",
        "refresh": 2,
        "multi": true,
        "includeAll": true
      },
      {
        "name": "interval",
        "type": "interval",
        "query": "1m,5m,15m,1h,6h,1d",
        "current": { "text": "5m", "value": "5m" }
      }
    ]
  }
}
```

**PromQL con variabili:**

```promql
# Alert rate per host
rate(alertmanager_alerts_received_total{instance=~"$host"}[$interval])

# Security events per severity
sum by (severity) (
  increase(security_events_total{env="$environment"}[5m])
)

# MTTD (Mean Time to Detect)
avg(
  security_incident_detected_timestamp - security_incident_start_timestamp
) by (severity)
```

### 5.4 Alerting Rules

```yaml
# Grafana alerting rule (Grafana 9+)
apiVersion: 1
groups:
  - orgId: 1
    name: security_alerts
    folder: Security
    interval: 1m
    rules:
      - uid: critical-alert-spike
        title: Critical Alert Spike
        condition: C
        data:
          - refId: A
            datasourceUid: prometheus
            model:
              expr: rate(security_alerts_total{severity="critical"}[5m])
              instant: false
              range: true
          - refId: B
            datasourceUid: __expr__
            model:
              type: reduce
              expression: A
              reducer: mean
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              expression: B
              conditions:
                - evaluator:
                    type: gt
                    params: [10]
        for: 5m
        labels:
          severity: critical
          team: soc
        annotations:
          summary: "Critical alert rate exceeded threshold"
          description: "Critical alerts firing at {{ $values.B }} per second (threshold: 10)"
          runbook_url: "https://wiki.internal/runbooks/critical-alert-spike"

      - uid: mttd-degradation
        title: MTTD Degradation
        condition: C
        data:
          - refId: A
            datasourceUid: prometheus
            model:
              expr: |
                avg(security_incident_detection_duration_seconds) / 3600
          - refId: B
            datasourceUid: __expr__
            model:
              type: reduce
              expression: A
              reducer: last
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              expression: B
              conditions:
                - evaluator:
                    type: gt
                    params: [4]
        for: 15m
        labels:
          severity: high
          team: soc
        annotations:
          summary: "Mean Time to Detect exceeds 4 hours"
```

### 5.5 Dashboard as Code (Provisioning)

```yaml
# /etc/grafana/provisioning/dashboards/security.yaml
apiVersion: 1
providers:
  - name: 'Security Dashboards'
    orgId: 1
    folder: 'Security'
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards/security
      foldersFromFilesStructure: true
```

**Dashboard JSON completo (esempio SOC):**

```json
{
  "dashboard": {
    "id": null,
    "uid": "soc-overview-v1",
    "title": "SOC Overview",
    "tags": ["security", "soc", "production"],
    "timezone": "UTC",
    "refresh": "30s",
    "time": {
      "from": "now-24h",
      "to": "now"
    },
    "annotations": {
      "list": [
        {
          "name": "Deployments",
          "datasource": "Prometheus",
          "expr": "changes(deployment_info{env=\"production\"}[1m]) > 0",
          "tagKeys": "version",
          "titleFormat": "Deploy: {{version}}"
        },
        {
          "name": "Incidents",
          "datasource": "Elasticsearch",
          "query": "event_type:incident AND severity:critical",
          "timeField": "@timestamp"
        }
      ]
    },
    "panels": [
      {
        "id": 1,
        "title": "Total Alerts (24h)",
        "type": "stat",
        "gridPos": { "h": 4, "w": 4, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "sum(increase(security_alerts_total[24h]))",
            "legendFormat": "Total"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 200 },
                { "color": "red", "value": 500 }
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "MTTD",
        "type": "stat",
        "gridPos": { "h": 4, "w": 4, "x": 4, "y": 0 },
        "targets": [
          {
            "expr": "avg(security_incident_detection_duration_seconds) / 3600",
            "legendFormat": "Hours"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "h",
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 2 },
                { "color": "red", "value": 4 }
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Alert Volume by Severity",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 16, "x": 0, "y": 4 },
        "targets": [
          {
            "expr": "sum by (severity) (rate(security_alerts_total[$__rate_interval]))",
            "legendFormat": "{{severity}}"
          }
        ],
        "fieldConfig": {
          "overrides": [
            {
              "matcher": { "id": "byName", "options": "critical" },
              "properties": [{ "id": "color", "value": { "fixedColor": "red" } }]
            },
            {
              "matcher": { "id": "byName", "options": "high" },
              "properties": [{ "id": "color", "value": { "fixedColor": "orange" } }]
            }
          ]
        }
      },
      {
        "id": 4,
        "title": "Top Attack Sources",
        "type": "table",
        "gridPos": { "h": 8, "w": 8, "x": 16, "y": 4 },
        "targets": [
          {
            "expr": "topk(10, sum by (source_ip, country) (security_alerts_total))",
            "format": "table",
            "instant": true
          }
        ]
      }
    ]
  }
}
```

---

## 6. Security Visualization

### 6.1 Attack Surface Visualization

La visualizzazione della superficie di attacco mostra tutti i punti di ingresso potenziali di un'organizzazione:

```python
import plotly.graph_objects as go
import networkx as nx

def create_attack_surface_map():
    """Mappa interattiva della superficie di attacco."""

    G = nx.Graph()

    # Nodi per tipo di asset
    assets = {
        'Internet': {'type': 'boundary', 'color': '#e74c3c'},
        'WAF': {'type': 'defense', 'color': '#2ecc71'},
        'Load Balancer': {'type': 'infra', 'color': '#3498db'},
        'Web Server 1': {'type': 'server', 'color': '#3498db'},
        'Web Server 2': {'type': 'server', 'color': '#3498db'},
        'API Gateway': {'type': 'infra', 'color': '#9b59b6'},
        'Auth Service': {'type': 'service', 'color': '#f39c12'},
        'Database': {'type': 'data', 'color': '#e67e22'},
        'Cache (Redis)': {'type': 'service', 'color': '#1abc9c'},
        'Message Queue': {'type': 'service', 'color': '#1abc9c'},
        'Internal API': {'type': 'service', 'color': '#9b59b6'},
        'Admin Panel': {'type': 'service', 'color': '#e74c3c'},
    }

    for name, attrs in assets.items():
        G.add_node(name, **attrs)

    # Connessioni (flusso di traffico)
    edges = [
        ('Internet', 'WAF'), ('WAF', 'Load Balancer'),
        ('Load Balancer', 'Web Server 1'), ('Load Balancer', 'Web Server 2'),
        ('Web Server 1', 'API Gateway'), ('Web Server 2', 'API Gateway'),
        ('API Gateway', 'Auth Service'), ('API Gateway', 'Internal API'),
        ('Auth Service', 'Database'), ('Internal API', 'Database'),
        ('Internal API', 'Cache (Redis)'), ('Internal API', 'Message Queue'),
        ('Admin Panel', 'Database'),
    ]
    G.add_edges_from(edges)

    pos = nx.spring_layout(G, k=2, seed=42)

    # Edge traces
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode='lines',
        line=dict(width=1, color='#888'),
        hoverinfo='none'
    )

    # Node traces
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_colors = [assets[node]['color'] for node in G.nodes()]
    node_sizes = [30 if assets[node]['type'] == 'boundary' else 20
                  for node in G.nodes()]

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        marker=dict(size=node_sizes, color=node_colors,
                    line=dict(width=2, color='white')),
        text=list(G.nodes()),
        textposition='top center',
        textfont=dict(size=9),
        hoverinfo='text',
        hovertext=[f"{name}<br>Type: {attrs['type']}"
                   for name, attrs in assets.items()]
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title='Attack Surface Map',
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        template='plotly_white'
    )
    return fig
```

### 6.2 SOC Dashboard Metrics

Le metriche chiave per un Security Operations Center:

| Metrica | Formula | Target |
|---------|---------|--------|
| **MTTD** (Mean Time to Detect) | avg(detection_time - incident_start) | < 1 hour |
| **MTTR** (Mean Time to Respond) | avg(response_time - detection_time) | < 4 hours |
| **MTTC** (Mean Time to Contain) | avg(containment_time - response_time) | < 2 hours |
| **Alert Volume** | count(alerts) per interval | Trend down |
| **False Positive Rate** | false_positives / total_alerts | < 30% |
| **Escalation Rate** | escalated / total_alerts | Monitoring |
| **SLA Compliance** | resolved_within_sla / total | > 95% |

### 6.3 MITRE ATT&CK Heatmap

```python
import plotly.graph_objects as go
import numpy as np

def create_mitre_heatmap():
    """Heatmap delle tecniche MITRE ATT&CK osservate."""

    tactics = [
        'Reconnaissance', 'Resource Development', 'Initial Access',
        'Execution', 'Persistence', 'Priv Escalation',
        'Defense Evasion', 'Credential Access', 'Discovery',
        'Lateral Movement', 'Collection', 'C2',
        'Exfiltration', 'Impact'
    ]

    # Tecniche per tattica (subset esemplificativo)
    techniques_per_tactic = {
        'Reconnaissance': ['Active Scanning', 'Search Victim Info', 'Gather Victim Org'],
        'Initial Access': ['Phishing', 'Exploit Public App', 'Valid Accounts', 'Drive-by'],
        'Execution': ['Command Script', 'User Execution', 'Scheduled Task'],
        'Persistence': ['Boot Autostart', 'Account Creation', 'Scheduled Task'],
        'Priv Escalation': ['Exploit Vuln', 'Access Token', 'Sudo Abuse'],
        'Defense Evasion': ['Obfuscation', 'Masquerading', 'Rootkit', 'Timestomp'],
        'Credential Access': ['Brute Force', 'Credential Dump', 'Keylogging'],
        'Discovery': ['Network Scan', 'Process Discovery', 'System Info'],
        'Lateral Movement': ['Remote Services', 'Internal Phishing', 'Exploitation'],
        'C2': ['Web Protocols', 'DNS Tunnel', 'Encrypted Channel'],
        'Exfiltration': ['Over C2', 'Over Web', 'Scheduled Transfer'],
        'Impact': ['Data Encryption', 'Service Stop', 'Defacement'],
    }

    # Conteggi simulati
    np.random.seed(42)
    max_techniques = max(len(v) for v in techniques_per_tactic.values())
    z_data = []
    y_labels = []

    for tactic in tactics:
        techs = techniques_per_tactic.get(tactic, ['N/A'])
        for tech in techs:
            y_labels.append(f"{tactic}: {tech}")
            row = np.random.randint(0, 50)
            z_data.append(row)

    # Reshape per heatmap semplificata
    # Per un heatmap matrice usiamo solo tactic x severity
    severities = ['Critical', 'High', 'Medium', 'Low', 'Info']
    z_matrix = np.random.randint(0, 30, size=(len(tactics), len(severities)))
    # Bias: Initial Access e Credential Access piu frequenti
    z_matrix[2, :] = z_matrix[2, :] * 2  # Initial Access
    z_matrix[6, :] = z_matrix[6, :] * 1.5  # Defense Evasion

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=severities,
        y=tactics,
        colorscale='YlOrRd',
        text=z_matrix,
        texttemplate='%{text}',
        textfont={'size': 10},
        hovertemplate='Tactic: %{y}<br>Severity: %{x}<br>Count: %{z}<extra></extra>'
    ))

    fig.update_layout(
        title='MITRE ATT&CK Coverage — Detections by Tactic and Severity',
        xaxis_title='Alert Severity',
        yaxis_title='',
        height=600,
        template='plotly_white',
        yaxis={'categoryorder': 'array', 'categoryarray': tactics[::-1]}
    )

    return fig
```

### 6.4 Vulnerability Management Dashboard

```python
def create_vuln_dashboard():
    """Dashboard di gestione vulnerabilita."""

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Vulnerability Aging', 'Severity Trend',
            'Top Vulnerable Assets', 'Remediation SLA'
        ),
        specs=[
            [{'type': 'bar'}, {'type': 'scatter'}],
            [{'type': 'table'}, {'type': 'indicator'}]
        ]
    )

    # Panel 1: Aging (giorni aperti per severity)
    aging_buckets = ['0-7d', '8-30d', '31-90d', '90-180d', '180d+']
    critical = [5, 2, 1, 0, 0]
    high = [15, 8, 4, 2, 1]
    medium = [45, 30, 20, 15, 8]

    fig.add_trace(go.Bar(name='Critical', x=aging_buckets, y=critical,
                         marker_color='#e74c3c'), row=1, col=1)
    fig.add_trace(go.Bar(name='High', x=aging_buckets, y=high,
                         marker_color='#f39c12'), row=1, col=1)
    fig.add_trace(go.Bar(name='Medium', x=aging_buckets, y=medium,
                         marker_color='#3498db'), row=1, col=1)

    # Panel 2: Trend nel tempo
    weeks = list(range(12))
    open_vulns = [120, 115, 130, 125, 110, 105, 98, 102, 95, 88, 82, 78]
    fig.add_trace(go.Scatter(
        x=weeks, y=open_vulns, mode='lines+markers',
        line=dict(color='#e74c3c', width=2), name='Open Vulns'
    ), row=1, col=2)

    # Panel 3: Top assets
    fig.add_trace(go.Table(
        header=dict(
            values=['Asset', 'Critical', 'High', 'Score'],
            fill_color='#2c3e50',
            font=dict(color='white'),
            align='left'
        ),
        cells=dict(
            values=[
                ['web-prod-01', 'db-prod-02', 'api-gw-01', 'ci-runner-03', 'vpn-01'],
                [3, 2, 1, 1, 0],
                [12, 8, 15, 5, 7],
                [9.8, 8.5, 7.2, 6.1, 5.4]
            ],
            align='left'
        )
    ), row=2, col=1)

    # Panel 4: SLA compliance gauge
    fig.add_trace(go.Indicator(
        mode='gauge+number',
        value=87,
        title={'text': 'SLA Compliance %'},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': '#2ecc71'},
            'steps': [
                {'range': [0, 70], 'color': '#fadbd8'},
                {'range': [70, 90], 'color': '#fdebd0'},
                {'range': [90, 100], 'color': '#d5f5e3'}
            ]
        }
    ), row=2, col=2)

    fig.update_layout(height=700, barmode='stack', template='plotly_white',
                      title_text='Vulnerability Management Dashboard')
    return fig
```

### 6.5 Risk Matrix Visualization

```python
def create_risk_matrix():
    """Matrice di rischio 5x5 con plotly."""

    likelihood_labels = ['Rare', 'Unlikely', 'Possible', 'Likely', 'Almost Certain']
    impact_labels = ['Negligible', 'Minor', 'Moderate', 'Major', 'Catastrophic']

    # Matrice colore (risk score)
    risk_scores = np.array([
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25]
    ])

    # Colorscale personalizzata
    colorscale = [
        [0, '#2ecc71'],      # Low
        [0.25, '#f1c40f'],   # Medium-Low
        [0.5, '#f39c12'],    # Medium
        [0.75, '#e67e22'],   # High
        [1.0, '#e74c3c']     # Critical
    ]

    fig = go.Figure(data=go.Heatmap(
        z=risk_scores,
        x=impact_labels,
        y=likelihood_labels,
        colorscale=colorscale,
        text=risk_scores,
        texttemplate='%{text}',
        textfont={'size': 14, 'color': 'white'},
        showscale=True,
        colorbar=dict(title='Risk Score')
    ))

    # Aggiungere rischi specifici come annotazioni
    risks = [
        {'name': 'Ransomware', 'likelihood': 3, 'impact': 4},
        {'name': 'Data Breach', 'likelihood': 2, 'impact': 4},
        {'name': 'DDoS', 'likelihood': 4, 'impact': 2},
        {'name': 'Insider Threat', 'likelihood': 2, 'impact': 3},
        {'name': 'Supply Chain', 'likelihood': 1, 'impact': 4},
    ]

    for risk in risks:
        fig.add_annotation(
            x=risk['impact'],
            y=risk['likelihood'],
            text=risk['name'],
            showarrow=True,
            arrowhead=2,
            ax=30, ay=-30,
            font=dict(size=10, color='white'),
            bgcolor='rgba(0,0,0,0.6)',
            borderpad=3
        )

    fig.update_layout(
        title='Enterprise Risk Matrix',
        xaxis_title='Impact',
        yaxis_title='Likelihood',
        template='plotly_white',
        height=500,
        width=650
    )
    return fig
```

---

## 7. Business Intelligence Tools

### 7.1 Metabase

Metabase offre BI self-service con una curva di apprendimento minima.

**Architettura:**

```
Browser → Metabase Frontend (React)
              ↓
         Metabase Backend (Clojure)
              ↓
         Database Drivers → PostgreSQL / MySQL / BigQuery / etc.
```

**Concetti chiave:**

- **Questions**: Query salvate con visualizzazione. Possono essere "Simple" (GUI builder), "Custom" (visual query builder con join), o "Native" (SQL puro).
- **Dashboards**: Composizione di Questions con filtri condivisi.
- **Collections**: Organizzazione gerarchica di Questions e Dashboards.
- **Embedded Analytics**: Iframe embed con JWT signed per integrazione in app terze.

```sql
-- Esempio Metabase Native Query con variabili template
SELECT
    date_trunc('day', created_at) AS day,
    severity,
    COUNT(*) AS alert_count
FROM security_alerts
WHERE
    created_at >= {{start_date}}
    AND created_at <= {{end_date}}
    AND severity IN ({{severity_filter}})
    AND environment = {{environment}}
GROUP BY 1, 2
ORDER BY 1
```

**Embedding con JWT:**

```python
import jwt
import time

METABASE_SECRET_KEY = os.environ['METABASE_SECRET_KEY']
METABASE_SITE_URL = os.environ['METABASE_SITE_URL']

def generate_embed_url(dashboard_id: int, params: dict) -> str:
    """Genera URL embed firmato per Metabase dashboard."""
    payload = {
        'resource': {'dashboard': dashboard_id},
        'params': params,  # es. {'severity': 'Critical'}
        'exp': int(time.time()) + 600  # 10 min expiry
    }
    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm='HS256')
    return f"{METABASE_SITE_URL}/embed/dashboard/{token}"
```

### 7.2 Apache Superset

Superset e una piattaforma BI open-source enterprise-grade.

**Componenti principali:**

- **SQL Lab**: Editor SQL con autocompletamento, query history, result caching.
- **Datasets**: Tabelle o query salvate come sorgente per visualizzazioni.
- **Charts**: 40+ tipi di visualizzazione con configurazione drag-and-drop.
- **Dashboards**: Layout flessibile con cross-filtering e drill-down.

**Configurazione per security analytics:**

```python
# superset_config.py — configurazione personalizzata
from celery.schedules import crontab

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
}

# Async queries per dataset grandi
SQLLAB_ASYNC_TIME_LIMIT_SEC = 600
SQL_MAX_ROW = 100000
SQLLAB_CTAS_NO_LIMIT = True

# Row-level security (RLS) per multi-tenancy
FEATURE_FLAGS = {
    'ROW_LEVEL_SECURITY': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'GLOBAL_ASYNC_QUERIES': True,
    'EMBEDDED_SUPERSET': True,
}

# Scheduled reports
CELERYBEAT_SCHEDULE = {
    'security_report': {
        'task': 'superset.tasks.schedules.deliver_report',
        'schedule': crontab(hour=7, minute=0),
    },
}
```

### 7.3 Tableau

Concetti avanzati di Tableau per security analytics:

**LOD Expressions (Level of Detail):**

```
// FIXED: Calcola a un livello specifico indipendentemente dai filtri vista
{FIXED [Severity] : AVG([Response Time])}

// INCLUDE: Aggiunge un livello di dettaglio
{INCLUDE [Source IP] : COUNTD([Alert ID])}

// EXCLUDE: Rimuove un livello di dettaglio
{EXCLUDE [Date] : SUM([Alert Count])}

// Esempio security: MTTD per team ignorando il filtro temporale
{FIXED [SOC Team] : AVG([Detection Time] - [Incident Start])}
```

**Calculated Fields per security:**

```
// Risk Score composito
IF [CVSS Score] >= 9.0 THEN "Critical"
ELSEIF [CVSS Score] >= 7.0 THEN "High"
ELSEIF [CVSS Score] >= 4.0 THEN "Medium"
ELSE "Low"
END

// SLA Breach flag
IF DATEDIFF('hour', [Created], [Resolved]) > [SLA Hours] THEN "Breached"
ELSE "Met"
END

// Running total of unresolved
RUNNING_SUM(
    IF [Status] = 'Open' THEN 1
    ELSEIF [Status] = 'Resolved' THEN -1
    ELSE 0
    END
)
```

### 7.4 Power BI

**DAX (Data Analysis Expressions):**

```dax
// MTTD measure
MTTD_Hours =
AVERAGEX(
    Incidents,
    DATEDIFF(
        Incidents[IncidentStart],
        Incidents[DetectedAt],
        HOUR
    )
)

// Rolling 7-day alert average
Rolling7DayAlerts =
AVERAGEX(
    DATESINPERIOD(
        Calendar[Date],
        MAX(Calendar[Date]),
        -7,
        DAY
    ),
    CALCULATE(COUNTROWS(Alerts))
)

// Year-over-Year comparison
AlertsYoY =
VAR CurrentPeriod = [TotalAlerts]
VAR PriorPeriod = CALCULATE([TotalAlerts], SAMEPERIODLASTYEAR(Calendar[Date]))
RETURN
    DIVIDE(CurrentPeriod - PriorPeriod, PriorPeriod, 0)

// Security score card with conditional formatting
SecurityScore =
VAR _vulnScore = DIVIDE([ResolvedVulns], [TotalVulns]) * 40
VAR _complianceScore = [ComplianceRate] * 30
VAR _responseScore = IF([MTTR_Hours] < 4, 30, 30 * (4 / [MTTR_Hours]))
RETURN _vulnScore + _complianceScore + _responseScore
```

**M Language (Power Query) per data prep:**

```m
// Trasformare log di sicurezza
let
    Source = Csv.Document(File.Contents("security_logs.csv")),
    PromotedHeaders = Table.PromoteHeaders(Source),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"timestamp", type datetimezone},
        {"severity", type text},
        {"source_ip", type text},
        {"alert_type", type text}
    }),
    FilteredRows = Table.SelectRows(TypedColumns, each
        [severity] <> "info" and [timestamp] >= DateTime.LocalNow() - #duration(30, 0, 0, 0)
    ),
    AddedRiskScore = Table.AddColumn(FilteredRows, "RiskScore", each
        if [severity] = "critical" then 10
        else if [severity] = "high" then 7
        else if [severity] = "medium" then 4
        else 1, type number
    ),
    GeoEnriched = Table.AddColumn(AddedRiskScore, "Country",
        each GeoIP.Lookup([source_ip]), type text)
in
    GeoEnriched
```

### 7.5 Comparison Matrix

| Criterio | Metabase | Superset | Tableau | Power BI |
|----------|----------|----------|---------|----------|
| **Costo** | Free (OSS) | Free (OSS) | $70/user/mo | $10-20/user/mo |
| **Setup** | Docker in 5 min | Moderato | SaaS/Desktop | SaaS/Desktop |
| **SQL Support** | Nativo + GUI | SQL Lab avanzato | Limitato | DAX |
| **Embedding** | JWT signed | SDK | Tableau Embedded | Power BI Embedded |
| **Real-time** | Refresh polling | Async queries | Extract refresh | DirectQuery |
| **Learning Curve** | Bassa | Media | Alta | Media |
| **Enterprise Scale** | Medio | Alto | Molto Alto | Alto |
| **Self-hosted** | Si | Si | No (Server edition) | No (gateway) |
| **API** | REST | REST + GraphQL | REST | REST |
| **Security (RLS)** | Sandboxing | Row-Level Security | Row-Level Security | RLS + OLS |

---

## 8. Real-Time Dashboards

### 8.1 Architettura Streaming Data

```
Data Sources                Processing              Visualization
─────────────             ──────────────           ─────────────────
[Firewall Logs] ──┐
[IDS/IPS]      ──┤       ┌──────────────┐        ┌───────────────┐
[SIEM Events]  ──┼──────→│ Kafka/Pulsar │───────→│ Grafana Live  │
[NetFlow]      ──┤       │              │    ┌──→│ Kibana RT     │
[Endpoint]     ──┘       └──────┬───────┘    │   │ Custom D3     │
                                │            │   │ Plotly Dash   │
                         ┌──────▼───────┐    │   └───────────────┘
                         │ Stream Proc  │────┘
                         │ (Flink/KSQL) │
                         └──────────────┘
```

### 8.2 WebSocket-Based Updates

```python
import asyncio
import json
import websockets
from datetime import datetime

# --- Server (FastAPI + WebSocket) ---
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    """Gestisce connessioni WebSocket attive."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.websocket("/ws/security-feed")
async def security_feed(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Riceve comandi dal client (filtri, sottoscrizioni)
            data = await websocket.receive_text()
            command = json.loads(data)
            # Gestione comandi: subscribe, unsubscribe, filter
            if command.get('action') == 'subscribe':
                # Logica di sottoscrizione per topic
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Background task che pubblica alert in tempo reale
async def alert_producer():
    """Simula produzione di alert da SIEM."""
    import random

    severity_weights = {'critical': 0.05, 'high': 0.15, 'medium': 0.35, 'low': 0.45}

    while True:
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': random.choices(
                list(severity_weights.keys()),
                weights=list(severity_weights.values())
            )[0],
            'type': random.choice(['phishing', 'malware', 'brute_force', 'ddos']),
            'source_ip': f"10.0.{random.randint(1,10)}.{random.randint(1,255)}",
            'description': 'Automated alert from detection engine',
            'status': 'new'
        }
        await manager.broadcast(alert)
        await asyncio.sleep(random.uniform(0.5, 3.0))
```

**Client JavaScript (D3.js + WebSocket):**

```javascript
// Real-time alert visualization con D3.js
class SecurityDashboard {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.alerts = [];
        this.maxAlerts = 100;
        this.severityColors = {
            critical: '#e74c3c',
            high: '#f39c12',
            medium: '#3498db',
            low: '#95a5a6'
        };
        this.initWebSocket();
        this.initCharts();
    }

    initWebSocket() {
        this.ws = new WebSocket('ws://localhost:8000/ws/security-feed');
        this.ws.onmessage = (event) => {
            const alert = JSON.parse(event.data);
            this.handleNewAlert(alert);
        };
        this.ws.onclose = () => {
            // Reconnect con exponential backoff
            setTimeout(() => this.initWebSocket(), 3000);
        };
    }

    handleNewAlert(alert) {
        this.alerts.push(alert);
        if (this.alerts.length > this.maxAlerts) {
            this.alerts.shift();
        }
        this.updateTimeline();
        this.updateCounters();
        this.updateSeverityRing();
    }

    initCharts() {
        // Timeline SVG
        const margin = { top: 20, right: 20, bottom: 30, left: 40 };
        const width = 800 - margin.left - margin.right;
        const height = 200 - margin.top - margin.bottom;

        this.svg = this.container.append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        this.xScale = d3.scaleTime().range([0, width]);
        this.yScale = d3.scaleBand()
            .domain(['critical', 'high', 'medium', 'low'])
            .range([0, height])
            .padding(0.1);

        this.svg.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${height})`);

        this.svg.append('g')
            .attr('class', 'y-axis');
    }

    updateTimeline() {
        const now = new Date();
        const fiveMinAgo = new Date(now - 5 * 60 * 1000);

        this.xScale.domain([fiveMinAgo, now]);

        const circles = this.svg.selectAll('circle')
            .data(this.alerts, d => d.timestamp);

        circles.enter()
            .append('circle')
            .attr('r', 0)
            .attr('cx', d => this.xScale(new Date(d.timestamp)))
            .attr('cy', d => this.yScale(d.severity) + this.yScale.bandwidth() / 2)
            .attr('fill', d => this.severityColors[d.severity])
            .attr('opacity', 0.7)
            .transition()
            .duration(300)
            .attr('r', 5);

        circles.transition()
            .duration(100)
            .attr('cx', d => this.xScale(new Date(d.timestamp)));

        circles.exit()
            .transition()
            .duration(200)
            .attr('r', 0)
            .remove();

        // Update axes
        this.svg.select('.x-axis')
            .transition()
            .duration(100)
            .call(d3.axisBottom(this.xScale).ticks(5));
    }

    updateCounters() {
        const counts = {};
        for (const sev of ['critical', 'high', 'medium', 'low']) {
            counts[sev] = this.alerts.filter(a => a.severity === sev).length;
        }
        // Aggiornare DOM counters
        for (const [sev, count] of Object.entries(counts)) {
            d3.select(`#count-${sev}`).text(count);
        }
    }
}

// Inizializzazione
const dashboard = new SecurityDashboard('dashboard-container');
```

### 8.3 Grafana Live

Grafana Live abilita streaming push-based nativo:

```yaml
# Configurazione Grafana per live streaming
# grafana.ini
[live]
max_connections = 1000
allowed_origins = *

[feature_toggles]
enable = live
```

```go
// Plugin backend che pusha dati a Grafana Live (Go)
// POST /api/live/push/{channel}
// Esempio: POST /api/live/push/security/alerts

// Il frontend si sottoscrive:
// datasource type: "grafana-live-datasource"
// channel: "security/alerts"
```

### 8.4 Performance Optimization per Large Datasets

| Strategia | Quando | Implementazione |
|-----------|--------|----------------|
| **Downsampling** | > 10k punti temporali | LTTB (Largest-Triangle-Three-Buckets) |
| **Aggregazione server-side** | Dataset > 1M righe | Pre-aggregare in Prometheus/ClickHouse |
| **Virtual scrolling** | Tabelle > 1000 righe | Render solo righe visibili |
| **Canvas rendering** | > 50k punti scatter | WebGL (deck.gl, regl) |
| **Incremental updates** | Real-time feed | Append-only, mai re-render completo |
| **Web Workers** | Calcoli pesanti | Spostare parsing/stats off main thread |
| **Request debouncing** | Filtri interattivi | 200-300ms debounce su input |

```python
# LTTB Downsampling implementation
def lttb_downsample(data: list[tuple], threshold: int) -> list[tuple]:
    """
    Largest-Triangle-Three-Buckets downsampling.
    Preserva la forma visiva riducendo i punti.

    Args:
        data: Lista di (x, y) tuple
        threshold: Numero di punti target

    Returns:
        Lista downsampled
    """
    if len(data) <= threshold:
        return data

    sampled = [data[0]]  # Primo punto sempre incluso
    bucket_size = (len(data) - 2) / (threshold - 2)

    a_index = 0

    for i in range(1, threshold - 1):
        # Calcola bucket range
        avg_range_start = int((i + 0) * bucket_size) + 1
        avg_range_end = int((i + 1) * bucket_size) + 1
        avg_range_end = min(avg_range_end, len(data))

        # Calcola punto medio del prossimo bucket
        avg_x = sum(data[j][0] for j in range(avg_range_start, avg_range_end))
        avg_y = sum(data[j][1] for j in range(avg_range_start, avg_range_end))
        avg_len = avg_range_end - avg_range_start
        avg_x /= avg_len
        avg_y /= avg_len

        # Trova il punto nel bucket corrente che forma il triangolo piu grande
        range_start = int((i - 1) * bucket_size) + 1
        range_end = int(i * bucket_size) + 1
        range_end = min(range_end, len(data))

        max_area = -1
        max_area_point = None

        for j in range(range_start, range_end):
            # Area del triangolo
            area = abs(
                (data[a_index][0] - avg_x) * (data[j][1] - data[a_index][1]) -
                (data[a_index][0] - data[j][0]) * (avg_y - data[a_index][1])
            ) * 0.5

            if area > max_area:
                max_area = area
                max_area_point = j

        sampled.append(data[max_area_point])
        a_index = max_area_point

    sampled.append(data[-1])  # Ultimo punto sempre incluso
    return sampled
```

---

## 9. Data Storytelling

### 9.1 Struttura Narrativa per Presentazioni Dati

Un data story efficace segue una struttura narrativa chiara:

```
Setup → Conflict → Resolution → Call to Action

1. SETUP: Contesto e baseline
   "Il nostro SOC processa 1,200 alert/giorno..."

2. CONFLICT: Il problema o insight
   "...ma il 40% sono falsi positivi che consumano 15h/giorno di analista"

3. RESOLUTION: La soluzione basata su dati
   "Implementando ML-based triage, riduciamo FP del 60%..."

4. CALL TO ACTION: Prossimi passi
   "Budget richiesto: 2 FTE per 3 mesi di implementazione"
```

### 9.2 Annotation Strategies

Le annotazioni trasformano un grafico in una storia:

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

def annotated_security_timeline():
    """Timeline con annotazioni narrative."""

    fig, ax = plt.subplots(figsize=(14, 5))

    # Dati
    np.random.seed(42)
    days = 180
    dates = pd.date_range('2024-01-01', periods=days, freq='D')
    alerts = np.random.poisson(12, days)

    # Simulare un incidente (giorno 45) e un improvement (giorno 120)
    alerts[43:50] = alerts[43:50] * 4
    alerts[120:] = (alerts[120:] * 0.6).astype(int)

    ax.plot(dates, alerts, color='#2c3e50', linewidth=1.2, alpha=0.7)
    ma = pd.Series(alerts).rolling(7).mean()
    ax.plot(dates, ma, color='#e74c3c', linewidth=2, label='7-day MA')

    # Annotazione 1: Incidente
    incident_date = dates[45]
    ax.annotate(
        'Log4Shell Campaign\nDetected',
        xy=(incident_date, alerts[45]),
        xytext=(incident_date + pd.Timedelta(days=15), alerts[45] + 15),
        fontsize=9, fontweight='bold', color='#e74c3c',
        arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.5),
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', alpha=0.8)
    )

    # Annotazione 2: Improvement
    improve_date = dates[120]
    ax.annotate(
        'ML Triage\nDeployed',
        xy=(improve_date, ma.iloc[120]),
        xytext=(improve_date - pd.Timedelta(days=20), ma.iloc[120] + 10),
        fontsize=9, fontweight='bold', color='#27ae60',
        arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.5),
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#d5f5e3', alpha=0.8)
    )

    # Aree evidenziate
    ax.axvspan(dates[43], dates[50], alpha=0.1, color='#e74c3c')
    ax.axvspan(dates[120], dates[-1], alpha=0.05, color='#27ae60')

    # Context box
    ax.text(0.02, 0.95,
            'Key Insight: ML triage reduced\ndaily alerts by 40% while\nmaintaining detection rate',
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax.set_title('SOC Alert Volume — Impact of ML Triage Deployment', fontsize=12)
    ax.set_ylabel('Daily Alerts')
    ax.legend(loc='upper right', frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig
```

### 9.3 Progressive Disclosure

Strutturare dashboard e presentazioni dal generale al specifico:

```
Layer 1 — OVERVIEW (Executive)
├── KPI cards: 3-5 numeri chiave
├── Trend sparklines
└── Status indicators (green/yellow/red)

Layer 2 — EXPLORE (Manager)
├── Filtri interattivi
├── Breakdown per dimensione
├── Confronti temporali
└── Drill-down links

Layer 3 — DETAIL (Analyst)
├── Tabelle granulari
├── Log entries individuali
├── Query builder
└── Export capabilities
```

### 9.4 Executive vs Technical Audiences

| Aspetto | Executive | Technical |
|---------|-----------|-----------|
| **Metriche** | Business impact ($, risk %) | Raw counts, latencies, p99 |
| **Tempo** | Quarterly/Monthly trends | Hourly/Minute granularity |
| **Colore** | RAG status (Red/Amber/Green) | Continuous color scales |
| **Interattivita** | Minima, pre-filtered | Massima, query-capable |
| **Annotazioni** | Business context, decisioni | Technical root cause |
| **Volume** | 3-5 pannelli | 15-20 pannelli |
| **Refresh** | Daily/Weekly | Real-time/5 min |

### 9.5 Color Accessibility

#### Palette Colorblind-Safe

```python
# Palette accessibili (verificate con CVD simulators)
COLORBLIND_SAFE = {
    # Wong (2011) — Nature Methods
    'wong': ['#000000', '#E69F00', '#56B4E9', '#009E73',
             '#F0E442', '#0072B2', '#D55E00', '#CC79A7'],

    # IBM Design
    'ibm': ['#648FFF', '#785EF0', '#DC267F', '#FE6100', '#FFB000'],

    # Tol (Paul Tol's schemes)
    'tol_bright': ['#4477AA', '#EE6677', '#228833', '#CCBB44',
                   '#66CCEE', '#AA3377', '#BBBBBB'],

    # Categorical safe (max 8 categories)
    'okabe_ito': ['#E69F00', '#56B4E9', '#009E73', '#F0E442',
                  '#0072B2', '#D55E00', '#CC79A7', '#000000'],
}

def apply_accessible_palette(fig, palette_name='wong'):
    """Applica palette colorblind-safe a figure matplotlib."""
    colors = COLORBLIND_SAFE[palette_name]
    from cycler import cycler
    plt.rcParams['axes.prop_cycle'] = cycler(color=colors)
```

**Regole per accessibilita cromatica:**

1. Mai usare solo colore per distinguere — aggiungere forma, pattern, o etichetta
2. Verificare con simulatore daltonismo (Deuteranopia, Protanopia, Tritanopia)
3. Assicurare contrasto > 3:1 per grafici, > 4.5:1 per testo
4. Rosso-verde e la combinazione peggiore: usare rosso-blu o arancio-blu
5. In heatmap, usare scale sequenziali (non divergenti red-green)

### 9.6 Dashboard Design Patterns

#### Overview-First, Detail-on-Demand (Shneiderman's Mantra)

```
Overview first → Zoom and filter → Details on demand
```

**Pattern implementativi:**

1. **Dashboard Hub** — Landing page con KPI summary + link a dashboard specialistici
2. **Master-Detail** — Lista a sinistra, dettaglio selezionato a destra
3. **Drill-through** — Click su aggregato apre vista dettagliata
4. **Guided Analysis** — Wizard con step progressivi
5. **Monitoring Wall** — Grid di pannelli per NOC/SOC su schermo dedicato

---

## 10. Lab Exercises

### Lab 1: SOC Security Dashboard in Grafana

**Obiettivo:** Costruire un dashboard SOC completo con alert, threat intelligence, e response metrics.

**Prerequisiti:**

```bash
# Docker compose per l'ambiente lab
# docker-compose.yml
```

```yaml
version: '3.8'
services:
  grafana:
    image: grafana/grafana:10.2.0
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_INSTALL_PLUGINS: grafana-worldmap-panel,grafana-clock-panel
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana

  prometheus:
    image: prom/prometheus:v2.47.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/rules:/etc/prometheus/rules

  # Simulatore di metriche di sicurezza
  security-exporter:
    build: ./security-exporter
    ports:
      - "9100:9100"

volumes:
  grafana-data:
```

**Security Metrics Exporter (Python):**

```python
#!/usr/bin/env python3
"""Prometheus exporter per metriche di sicurezza simulate."""

import time
import random
from prometheus_client import (
    start_http_server, Counter, Gauge, Histogram, Summary, Info
)

# --- Metriche ---
ALERTS_TOTAL = Counter(
    'security_alerts_total',
    'Total security alerts',
    ['severity', 'type', 'source']
)

ACTIVE_INCIDENTS = Gauge(
    'security_active_incidents',
    'Currently active security incidents',
    ['severity']
)

DETECTION_DURATION = Histogram(
    'security_detection_duration_seconds',
    'Time to detect security incidents',
    ['severity'],
    buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400]
)

RESPONSE_DURATION = Histogram(
    'security_response_duration_seconds',
    'Time to respond to security incidents',
    ['severity', 'team'],
    buckets=[300, 900, 1800, 3600, 7200, 14400, 28800]
)

VULN_OPEN = Gauge(
    'security_vulnerabilities_open',
    'Open vulnerabilities by severity',
    ['severity', 'asset_type']
)

FALSE_POSITIVE_RATE = Gauge(
    'security_false_positive_rate',
    'False positive rate for alert types',
    ['alert_type']
)

THREAT_INTEL_FEEDS = Gauge(
    'security_threat_intel_indicators',
    'Active threat intelligence indicators',
    ['feed', 'type']
)

def simulate_metrics():
    """Genera metriche realistiche."""
    alert_types = ['phishing', 'malware', 'brute_force', 'ddos',
                   'data_exfil', 'insider_threat', 'ransomware']
    severities = ['critical', 'high', 'medium', 'low']
    sources = ['ids', 'edr', 'siem', 'firewall', 'waf']
    teams = ['alpha', 'beta', 'gamma']
    asset_types = ['server', 'endpoint', 'network', 'application', 'database']

    while True:
        # Generare alert
        for _ in range(random.randint(1, 5)):
            sev = random.choices(severities, weights=[0.05, 0.15, 0.35, 0.45])[0]
            alert_type = random.choice(alert_types)
            source = random.choice(sources)
            ALERTS_TOTAL.labels(severity=sev, type=alert_type, source=source).inc()

        # Aggiornare incidenti attivi
        for sev in severities:
            base = {'critical': 2, 'high': 8, 'medium': 20, 'low': 45}
            ACTIVE_INCIDENTS.labels(severity=sev).set(
                base[sev] + random.randint(-2, 2)
            )

        # Detection duration
        for sev in severities:
            base_seconds = {'critical': 600, 'high': 1800, 'medium': 7200, 'low': 14400}
            duration = random.expovariate(1 / base_seconds[sev])
            DETECTION_DURATION.labels(severity=sev).observe(duration)

        # Response duration
        for sev in ['critical', 'high']:
            team = random.choice(teams)
            base_resp = {'critical': 900, 'high': 3600}
            RESPONSE_DURATION.labels(severity=sev, team=team).observe(
                random.expovariate(1 / base_resp[sev])
            )

        # Vulnerabilita
        for sev in severities:
            for asset in asset_types:
                base_vuln = {'critical': 3, 'high': 12, 'medium': 35, 'low': 80}
                VULN_OPEN.labels(severity=sev, asset_type=asset).set(
                    max(0, base_vuln[sev] + random.randint(-5, 5))
                )

        # False positive rates
        for alert_type in alert_types:
            rate = random.uniform(0.1, 0.5)
            FALSE_POSITIVE_RATE.labels(alert_type=alert_type).set(rate)

        # Threat intel
        feeds = ['alienvault', 'abuse_ch', 'emergingthreats', 'internal']
        indicator_types = ['ip', 'domain', 'hash', 'url']
        for feed in feeds:
            for ioc_type in indicator_types:
                THREAT_INTEL_FEEDS.labels(feed=feed, type=ioc_type).set(
                    random.randint(100, 5000)
                )

        time.sleep(15)


if __name__ == '__main__':
    start_http_server(9100)
    print("Security metrics exporter running on :9100")
    simulate_metrics()
```

**Prometheus Rules per SOC:**

```yaml
# prometheus/rules/security.yml
groups:
  - name: security_recording_rules
    interval: 30s
    rules:
      - record: security:mttd:avg_hours
        expr: |
          avg(rate(security_detection_duration_seconds_sum[5m]))
          / avg(rate(security_detection_duration_seconds_count[5m]))
          / 3600

      - record: security:mttr:avg_hours
        expr: |
          avg(rate(security_response_duration_seconds_sum[5m]))
          / avg(rate(security_response_duration_seconds_count[5m]))
          / 3600

      - record: security:alert_rate:5m
        expr: sum(rate(security_alerts_total[5m])) by (severity)

      - record: security:false_positive:avg
        expr: avg(security_false_positive_rate)

  - name: security_alerts
    rules:
      - alert: CriticalAlertSpike
        expr: rate(security_alerts_total{severity="critical"}[5m]) > 0.5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Critical alert rate spike detected"

      - alert: HighMTTD
        expr: security:mttd:avg_hours > 4
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Mean Time to Detect exceeds 4 hours"
```

**Dashboard JSON per Grafana:**

```json
{
  "dashboard": {
    "uid": "soc-lab-dashboard",
    "title": "SOC Lab Dashboard",
    "tags": ["security", "soc", "lab"],
    "timezone": "UTC",
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "title": "MTTD (Hours)",
        "type": "stat",
        "gridPos": {"h": 4, "w": 4, "x": 0, "y": 0},
        "targets": [{"expr": "security:mttd:avg_hours", "legendFormat": "MTTD"}],
        "fieldConfig": {
          "defaults": {
            "unit": "h",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 2},
                {"color": "red", "value": 4}
              ]
            }
          }
        },
        "options": {"graphMode": "area", "colorMode": "background"}
      },
      {
        "id": 2,
        "title": "MTTR (Hours)",
        "type": "stat",
        "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0},
        "targets": [{"expr": "security:mttr:avg_hours", "legendFormat": "MTTR"}],
        "fieldConfig": {
          "defaults": {
            "unit": "h",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 4},
                {"color": "red", "value": 8}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Active Incidents",
        "type": "stat",
        "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0},
        "targets": [{"expr": "sum(security_active_incidents)", "legendFormat": "Active"}],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 30},
                {"color": "red", "value": 60}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Alert Rate by Severity",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
        "targets": [
          {"expr": "security:alert_rate:5m", "legendFormat": "{{severity}}"}
        ],
        "fieldConfig": {
          "overrides": [
            {"matcher": {"id": "byName", "options": "critical"},
             "properties": [{"id": "color", "value": {"fixedColor": "#e74c3c"}}]},
            {"matcher": {"id": "byName", "options": "high"},
             "properties": [{"id": "color", "value": {"fixedColor": "#f39c12"}}]},
            {"matcher": {"id": "byName", "options": "medium"},
             "properties": [{"id": "color", "value": {"fixedColor": "#3498db"}}]},
            {"matcher": {"id": "byName", "options": "low"},
             "properties": [{"id": "color", "value": {"fixedColor": "#95a5a6"}}]}
          ]
        }
      },
      {
        "id": 5,
        "title": "False Positive Rate by Alert Type",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
        "targets": [
          {"expr": "security_false_positive_rate", "legendFormat": "{{alert_type}}"}
        ]
      },
      {
        "id": 6,
        "title": "Open Vulnerabilities",
        "type": "barchart",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
        "targets": [
          {"expr": "sum by (severity) (security_vulnerabilities_open)",
           "legendFormat": "{{severity}}", "format": "table", "instant": true}
        ]
      },
      {
        "id": 7,
        "title": "Threat Intel Indicators",
        "type": "table",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
        "targets": [
          {"expr": "security_threat_intel_indicators",
           "format": "table", "instant": true}
        ]
      }
    ]
  }
}
```

### Lab 2: Interactive Data Exploration con Plotly Dash

**Obiettivo:** Creare un tool di esplorazione dati interattivo per analizzare pattern di sicurezza.

```python
"""
Lab 2: Security Data Explorer con Plotly Dash
Permette agli analisti di esplorare correlazioni e pattern negli alert.
"""

from dash import Dash, html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- Data Generation ---
def generate_security_dataset(n_records: int = 5000) -> pd.DataFrame:
    """Genera dataset realistico di security events."""
    np.random.seed(42)

    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_records)]

    # Simulare pattern realistici
    hour_of_day = [t.hour for t in timestamps]
    day_of_week = [t.weekday() for t in timestamps]

    # Attack volume segue pattern: piu alto durante business hours, spike notturni
    base_rate = np.array([
        0.3 + 0.5 * np.sin(np.pi * h / 12) + 0.2 * (h > 22 or h < 5)
        for h in hour_of_day
    ])

    alert_types = np.random.choice(
        ['Phishing', 'Malware', 'Brute Force', 'DDoS', 'Data Exfiltration',
         'Privilege Escalation', 'Lateral Movement', 'C2 Communication'],
        n_records,
        p=[0.25, 0.18, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05]
    )

    severities = np.random.choice(
        ['Critical', 'High', 'Medium', 'Low'],
        n_records,
        p=[0.05, 0.15, 0.35, 0.45]
    )

    source_countries = np.random.choice(
        ['US', 'CN', 'RU', 'BR', 'DE', 'IN', 'GB', 'KR', 'IR', 'NK'],
        n_records,
        p=[0.15, 0.20, 0.18, 0.10, 0.08, 0.08, 0.07, 0.06, 0.04, 0.04]
    )

    # Response time dipende da severity
    response_times = []
    for sev in severities:
        base = {'Critical': 15, 'High': 45, 'Medium': 120, 'Low': 480}
        response_times.append(max(1, np.random.exponential(base[sev])))

    return pd.DataFrame({
        'timestamp': timestamps,
        'alert_type': alert_types,
        'severity': severities,
        'source_country': source_countries,
        'source_ip': [f"10.{np.random.randint(0,255)}.{np.random.randint(0,255)}.{np.random.randint(1,255)}"
                      for _ in range(n_records)],
        'response_time_min': response_times,
        'resolved': np.random.choice([True, False], n_records, p=[0.75, 0.25]),
        'false_positive': np.random.choice([True, False], n_records, p=[0.3, 0.7]),
        'hour': hour_of_day,
        'day_of_week': day_of_week,
        'analyst': np.random.choice(['Alice', 'Bob', 'Carol', 'Dave', 'Eve'], n_records),
    })


df = generate_security_dataset()

# --- App ---
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# --- Layout ---
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2('Security Data Explorer', className='text-light'),
            html.P('Interactive analysis of security events',
                   className='text-muted')
        ], width=8),
        dbc.Col([
            dcc.DatePickerRange(
                id='date-range',
                start_date=df['timestamp'].min(),
                end_date=df['timestamp'].max(),
                display_format='YYYY-MM-DD'
            )
        ], width=4)
    ], className='my-3'),

    # Filters
    dbc.Row([
        dbc.Col([
            dbc.Label('Severity'),
            dcc.Dropdown(
                id='filter-severity',
                options=[{'label': s, 'value': s}
                         for s in ['All'] + sorted(df['severity'].unique().tolist())],
                value='All', clearable=False
            )
        ], width=2),
        dbc.Col([
            dbc.Label('Alert Type'),
            dcc.Dropdown(
                id='filter-type',
                options=[{'label': t, 'value': t}
                         for t in ['All'] + sorted(df['alert_type'].unique().tolist())],
                value='All', clearable=False
            )
        ], width=3),
        dbc.Col([
            dbc.Label('Country'),
            dcc.Dropdown(
                id='filter-country',
                options=[{'label': c, 'value': c}
                         for c in ['All'] + sorted(df['source_country'].unique().tolist())],
                value='All', clearable=False, multi=True
            )
        ], width=3),
        dbc.Col([
            dbc.Label('Analysis Dimension'),
            dcc.RadioItems(
                id='analysis-dim',
                options=[
                    {'label': ' Temporal', 'value': 'temporal'},
                    {'label': ' Correlation', 'value': 'correlation'},
                    {'label': ' Distribution', 'value': 'distribution'},
                ],
                value='temporal',
                inline=True
            )
        ], width=4),
    ], className='mb-3'),

    # Main visualization area
    dbc.Row([
        dbc.Col([dcc.Graph(id='main-chart', style={'height': '500px'})], width=8),
        dbc.Col([
            dcc.Graph(id='side-chart-1', style={'height': '240px'}),
            dcc.Graph(id='side-chart-2', style={'height': '240px'}),
        ], width=4),
    ]),

    # Detail table
    dbc.Row([
        dbc.Col([
            html.H5('Selected Events', className='text-light mt-3'),
            html.Div(id='detail-table')
        ])
    ]),

], fluid=True)


@callback(
    [Output('main-chart', 'figure'),
     Output('side-chart-1', 'figure'),
     Output('side-chart-2', 'figure')],
    [Input('filter-severity', 'value'),
     Input('filter-type', 'value'),
     Input('filter-country', 'value'),
     Input('analysis-dim', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_charts(severity, alert_type, countries, dim, start, end):
    filtered = df.copy()

    if severity != 'All':
        filtered = filtered[filtered['severity'] == severity]
    if alert_type != 'All':
        filtered = filtered[filtered['alert_type'] == alert_type]
    if countries and 'All' not in countries:
        filtered = filtered[filtered['source_country'].isin(countries)]
    if start:
        filtered = filtered[filtered['timestamp'] >= start]
    if end:
        filtered = filtered[filtered['timestamp'] <= end]

    template = 'plotly_dark'

    if dim == 'temporal':
        # Main: timeline heatmap (hour x day_of_week)
        pivot = filtered.pivot_table(
            values='response_time_min', index='hour',
            columns='day_of_week', aggfunc='count', fill_value=0
        )
        main_fig = px.imshow(
            pivot, title='Alert Density: Hour vs Day of Week',
            labels={'x': 'Day', 'y': 'Hour', 'color': 'Count'},
            x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            aspect='auto', color_continuous_scale='YlOrRd',
            template=template
        )

        # Side 1: hourly distribution
        hourly = filtered.groupby('hour').size().reset_index(name='count')
        side1 = px.bar(hourly, x='hour', y='count',
                       title='Alerts by Hour', template=template)
        side1.update_traces(marker_color='#e74c3c')

        # Side 2: daily trend
        daily = filtered.set_index('timestamp').resample('D').size().reset_index(name='count')
        side2 = px.line(daily, x='timestamp', y='count',
                        title='Daily Trend', template=template)

    elif dim == 'correlation':
        # Main: scatter di response_time vs alert count per analyst
        analyst_stats = filtered.groupby('analyst').agg(
            alerts=('alert_type', 'count'),
            avg_response=('response_time_min', 'mean'),
            resolution_rate=('resolved', 'mean')
        ).reset_index()

        main_fig = px.scatter(
            analyst_stats, x='alerts', y='avg_response',
            size='resolution_rate', color='analyst',
            title='Analyst Performance: Volume vs Speed',
            labels={'alerts': 'Total Alerts', 'avg_response': 'Avg Response (min)'},
            template=template, size_max=40
        )

        # Side 1: correlation heatmap
        numeric_cols = filtered[['response_time_min', 'hour', 'day_of_week']].copy()
        numeric_cols['severity_num'] = filtered['severity'].map(
            {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        )
        corr = numeric_cols.corr()
        side1 = px.imshow(corr, title='Correlation Matrix',
                          color_continuous_scale='RdBu_r', template=template)

        # Side 2: type vs severity heatmap
        cross = pd.crosstab(filtered['alert_type'], filtered['severity'])
        side2 = px.imshow(cross, title='Type vs Severity',
                          template=template, color_continuous_scale='YlOrRd')

    else:  # distribution
        # Main: violin plot di response time per severity
        main_fig = px.violin(
            filtered, x='severity', y='response_time_min',
            color='severity', box=True,
            title='Response Time Distribution by Severity',
            color_discrete_map={
                'Critical': '#e74c3c', 'High': '#f39c12',
                'Medium': '#3498db', 'Low': '#95a5a6'
            },
            template=template
        )
        main_fig.update_yaxes(type='log')

        # Side 1: pie chart of types
        type_counts = filtered['alert_type'].value_counts()
        side1 = px.pie(values=type_counts.values, names=type_counts.index,
                       title='Alert Type Distribution', template=template,
                       hole=0.4)

        # Side 2: country bar
        country_counts = filtered['source_country'].value_counts().head(8)
        side2 = px.bar(x=country_counts.values, y=country_counts.index,
                       orientation='h', title='Top Source Countries',
                       template=template)
        side2.update_traces(marker_color='#3498db')

    return main_fig, side1, side2


if __name__ == '__main__':
    app.run(debug=True, port=8051)
```

### Lab 3: Executive Security Metrics Presentation

**Obiettivo:** Progettare una presentazione di metriche di sicurezza per il board/C-level.

```python
"""
Lab 3: Executive Security Report Generator
Genera slide-ready visualization per presentazione al board.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd

def create_executive_report():
    """Genera report visivo per presentazione executive."""

    # Setup stile corporate
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica Neue', 'Arial', 'DejaVu Sans'],
        'font.size': 10,
        'axes.titlesize': 12,
        'figure.facecolor': '#ffffff',
        'axes.facecolor': '#ffffff',
    })

    fig = plt.figure(figsize=(16, 20))
    gs = GridSpec(5, 4, figure=fig, hspace=0.4, wspace=0.35,
                  left=0.05, right=0.95, top=0.95, bottom=0.03)

    # --- HEADER ---
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.axis('off')
    ax_header.text(0.5, 0.8, 'SECURITY POSTURE REPORT',
                   fontsize=22, fontweight='bold', ha='center', va='center',
                   color='#2c3e50')
    ax_header.text(0.5, 0.5, 'Q1 2024 — Executive Summary',
                   fontsize=14, ha='center', va='center', color='#7f8c8d')
    ax_header.text(0.5, 0.2, 'Classification: CONFIDENTIAL',
                   fontsize=9, ha='center', va='center', color='#e74c3c',
                   style='italic')

    # --- KPI ROW ---
    kpis = [
        ('Security Score', '87/100', '+5', '#27ae60', 'vs last quarter'),
        ('Open Critical', '3', '-2', '#27ae60', 'vs last quarter'),
        ('MTTD', '1.8h', '-0.5h', '#27ae60', 'target: 2h'),
        ('MTTR', '3.2h', '-1.1h', '#27ae60', 'target: 4h'),
    ]

    for i, (label, value, delta, color, subtitle) in enumerate(kpis):
        ax = fig.add_subplot(gs[1, i])
        ax.axis('off')

        # Background card
        rect = mpatches.FancyBboxPatch(
            (0.05, 0.1), 0.9, 0.8, boxstyle="round,pad=0.02",
            facecolor='#f8f9fa', edgecolor='#dee2e6', linewidth=1
        )
        ax.add_patch(rect)

        ax.text(0.5, 0.75, value, fontsize=24, fontweight='bold',
                ha='center', va='center', color='#2c3e50')
        ax.text(0.5, 0.5, label, fontsize=10,
                ha='center', va='center', color='#7f8c8d')
        ax.text(0.5, 0.3, f'{delta}', fontsize=11,
                ha='center', va='center', color=color, fontweight='bold')
        ax.text(0.5, 0.15, subtitle, fontsize=8,
                ha='center', va='center', color='#95a5a6')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    # --- TREND CHART ---
    ax_trend = fig.add_subplot(gs[2, :3])
    months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    incidents = [45, 52, 38, 35, 28, 22]
    resolved = [40, 48, 36, 34, 27, 21]

    ax_trend.fill_between(months, incidents, alpha=0.15, color='#e74c3c')
    ax_trend.fill_between(months, resolved, alpha=0.15, color='#2ecc71')
    ax_trend.plot(months, incidents, 'o-', color='#e74c3c',
                  linewidth=2, markersize=6, label='New Incidents')
    ax_trend.plot(months, resolved, 's-', color='#2ecc71',
                  linewidth=2, markersize=6, label='Resolved')
    ax_trend.set_title('Incident Trend — 6 Month View', fontsize=12, loc='left')
    ax_trend.legend(loc='upper right', frameon=False)
    ax_trend.spines['top'].set_visible(False)
    ax_trend.spines['right'].set_visible(False)
    ax_trend.set_ylabel('Count')

    # Annotazione chiave
    ax_trend.annotate('SOC ML\nDeployed', xy=(3, 35),
                      xytext=(3.5, 42),
                      fontsize=9, color='#27ae60',
                      arrowprops=dict(arrowstyle='->', color='#27ae60'))

    # --- RISK MATRIX (small) ---
    ax_risk = fig.add_subplot(gs[2, 3])
    risk_data = np.array([
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25]
    ])
    im = ax_risk.imshow(risk_data, cmap='RdYlGn_r', aspect='auto')
    ax_risk.set_xticks(range(5))
    ax_risk.set_yticks(range(5))
    ax_risk.set_xticklabels(['Neg', 'Min', 'Mod', 'Maj', 'Cat'], fontsize=7)
    ax_risk.set_yticklabels(['Rare', 'Unl', 'Pos', 'Lik', 'AC'], fontsize=7)
    ax_risk.set_xlabel('Impact', fontsize=8)
    ax_risk.set_ylabel('Likelihood', fontsize=8)
    ax_risk.set_title('Risk Matrix', fontsize=10)

    # Marker per top risks
    ax_risk.plot(3, 3, 'w*', markersize=12)  # Ransomware
    ax_risk.plot(4, 2, 'w*', markersize=12)  # Data Breach

    # --- COMPLIANCE ---
    ax_comp = fig.add_subplot(gs[3, :2])
    frameworks = ['SOC 2', 'ISO 27001', 'GDPR', 'PCI DSS', 'HIPAA']
    compliance = [94, 89, 92, 87, 91]
    targets = [95, 90, 95, 90, 90]

    x = np.arange(len(frameworks))
    width = 0.35

    bars1 = ax_comp.bar(x - width/2, compliance, width, label='Current',
                        color='#3498db')
    bars2 = ax_comp.bar(x + width/2, targets, width, label='Target',
                        color='#ecf0f1', edgecolor='#bdc3c7')

    ax_comp.set_xticks(x)
    ax_comp.set_xticklabels(frameworks)
    ax_comp.set_ylabel('Compliance %')
    ax_comp.set_title('Compliance Status by Framework', loc='left')
    ax_comp.legend(frameon=False)
    ax_comp.set_ylim(75, 100)
    ax_comp.spines['top'].set_visible(False)
    ax_comp.spines['right'].set_visible(False)

    # Etichette
    for bar in bars1:
        h = bar.get_height()
        ax_comp.text(bar.get_x() + bar.get_width()/2, h + 0.3,
                    f'{int(h)}%', ha='center', fontsize=8, fontweight='bold')

    # --- TOP RISKS TABLE ---
    ax_table = fig.add_subplot(gs[3, 2:])
    ax_table.axis('off')
    ax_table.set_title('Top 5 Risks', fontsize=11, loc='left', pad=10)

    table_data = [
        ['#', 'Risk', 'Score', 'Trend'],
        ['1', 'Ransomware', '16/25', 'stable'],
        ['2', 'Supply Chain', '15/25', 'increasing'],
        ['3', 'Insider Threat', '12/25', 'decreasing'],
        ['4', 'Cloud Misconfig', '12/25', 'stable'],
        ['5', 'Zero-Day', '10/25', 'increasing'],
    ]

    table = ax_table.table(cellText=table_data[1:], colLabels=table_data[0],
                           loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.auto_set_column_width(col=list(range(4)))

    # Style header
    for j in range(4):
        table[0, j].set_facecolor('#2c3e50')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # --- RECOMMENDATIONS ---
    ax_rec = fig.add_subplot(gs[4, :])
    ax_rec.axis('off')
    ax_rec.set_title('Recommendations & Next Steps', fontsize=12,
                     loc='left', pad=10, fontweight='bold')

    recommendations = [
        '1. Deploy EDR to remaining 15% of endpoints (Budget: $45K, Timeline: Q2)',
        '2. Implement automated playbooks for top 3 alert types (reduce MTTR by 30%)',
        '3. Conduct red team exercise focusing on supply chain attack vectors',
        '4. Migrate remaining on-prem SIEM queries to cloud-native solution',
        '5. Hire 2 additional SOC analysts for 24/7 coverage (Current gap: 00:00-08:00)',
    ]

    for i, rec in enumerate(recommendations):
        ax_rec.text(0.02, 0.85 - i * 0.2, rec, fontsize=10,
                   va='center', color='#2c3e50',
                   transform=ax_rec.transAxes)

    plt.savefig('executive_security_report.png', dpi=150,
                bbox_inches='tight', facecolor='white')
    return fig
```

### Lab 4: Real-Time Network Traffic Visualization

**Obiettivo:** Costruire una visualizzazione real-time del traffico di rete con anomaly detection visiva.

```python
"""
Lab 4: Real-Time Network Traffic Visualization
Utilizza streaming data per visualizzare flussi di rete e anomalie.
"""

import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import numpy as np

# --- Data Model ---
@dataclass
class NetworkFlow:
    timestamp: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    bytes_sent: int
    bytes_received: int
    packets: int
    duration_ms: int
    flags: str
    anomaly_score: float
    label: Optional[str] = None


# --- Flow Generator (simula NetFlow/sFlow) ---
class NetworkFlowGenerator:
    """Genera flussi di rete realistici con anomalie periodiche."""

    def __init__(self, anomaly_rate: float = 0.05):
        self.anomaly_rate = anomaly_rate
        self.normal_hosts = [f"192.168.1.{i}" for i in range(1, 50)]
        self.servers = [f"10.0.0.{i}" for i in range(1, 10)]
        self.external = [f"{np.random.randint(1,223)}.{np.random.randint(0,255)}."
                        f"{np.random.randint(0,255)}.{np.random.randint(1,255)}"
                        for _ in range(100)]

    def generate_normal_flow(self) -> NetworkFlow:
        """Flusso di rete normale."""
        src = np.random.choice(self.normal_hosts)
        dst = np.random.choice(self.servers + self.external)
        protocol = np.random.choice(['TCP', 'UDP', 'HTTPS', 'DNS'],
                                     p=[0.3, 0.1, 0.5, 0.1])

        common_ports = {'TCP': [80, 443, 8080], 'UDP': [53, 123],
                       'HTTPS': [443], 'DNS': [53]}
        dst_port = np.random.choice(common_ports.get(protocol, [80]))

        return NetworkFlow(
            timestamp=datetime.utcnow().isoformat(),
            src_ip=src,
            dst_ip=dst,
            src_port=np.random.randint(1024, 65535),
            dst_port=dst_port,
            protocol=protocol,
            bytes_sent=int(np.random.exponential(5000)),
            bytes_received=int(np.random.exponential(15000)),
            packets=np.random.randint(1, 100),
            duration_ms=int(np.random.exponential(500)),
            flags='SYN-ACK' if protocol == 'TCP' else '',
            anomaly_score=np.random.uniform(0, 0.3),
            label='normal'
        )

    def generate_anomalous_flow(self) -> NetworkFlow:
        """Flusso anomalo (potenziale attacco)."""
        anomaly_type = np.random.choice([
            'port_scan', 'data_exfil', 'c2_beacon', 'brute_force'
        ])

        if anomaly_type == 'port_scan':
            return NetworkFlow(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=np.random.choice(self.external),
                dst_ip=np.random.choice(self.servers),
                src_port=np.random.randint(1024, 65535),
                dst_port=np.random.randint(1, 1024),
                protocol='TCP',
                bytes_sent=64,
                bytes_received=0,
                packets=1,
                duration_ms=10,
                flags='SYN',
                anomaly_score=np.random.uniform(0.7, 1.0),
                label='port_scan'
            )
        elif anomaly_type == 'data_exfil':
            return NetworkFlow(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=np.random.choice(self.normal_hosts),
                dst_ip=np.random.choice(self.external),
                src_port=np.random.randint(1024, 65535),
                dst_port=443,
                protocol='HTTPS',
                bytes_sent=int(np.random.exponential(500000)),  # Alto volume
                bytes_received=int(np.random.exponential(1000)),
                packets=np.random.randint(100, 1000),
                duration_ms=int(np.random.exponential(30000)),
                flags='PSH-ACK',
                anomaly_score=np.random.uniform(0.6, 0.95),
                label='data_exfil'
            )
        elif anomaly_type == 'c2_beacon':
            return NetworkFlow(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=np.random.choice(self.normal_hosts),
                dst_ip=np.random.choice(self.external),
                src_port=np.random.randint(1024, 65535),
                dst_port=np.random.choice([443, 8443, 4444]),
                protocol='TCP',
                bytes_sent=128,  # Piccolo, regolare
                bytes_received=64,
                packets=2,
                duration_ms=100,
                flags='PSH-ACK',
                anomaly_score=np.random.uniform(0.65, 0.9),
                label='c2_beacon'
            )
        else:  # brute_force
            return NetworkFlow(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=np.random.choice(self.external),
                dst_ip=np.random.choice(self.servers),
                src_port=np.random.randint(1024, 65535),
                dst_port=22,
                protocol='TCP',
                bytes_sent=256,
                bytes_received=128,
                packets=4,
                duration_ms=50,
                flags='SYN-ACK-RST',
                anomaly_score=np.random.uniform(0.7, 0.95),
                label='brute_force'
            )

    async def stream_flows(self, rate_per_second: float = 10):
        """Genera stream di flussi di rete."""
        while True:
            if np.random.random() < self.anomaly_rate:
                flow = self.generate_anomalous_flow()
            else:
                flow = self.generate_normal_flow()

            yield asdict(flow)
            await asyncio.sleep(1.0 / rate_per_second)


# --- Dash Real-Time App ---
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

app.layout = dbc.Container([
    html.H3('Real-Time Network Traffic Monitor', className='text-light my-3'),

    dbc.Row([
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H5(id='rt-flow-count', className='text-center text-info'),
                html.P('Flows/min', className='text-center text-muted')
            ]))
        ], width=3),
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H5(id='rt-anomaly-count', className='text-center text-danger'),
                html.P('Anomalies', className='text-center text-muted')
            ]))
        ], width=3),
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H5(id='rt-bandwidth', className='text-center text-success'),
                html.P('Bandwidth (MB/s)', className='text-center text-muted')
            ]))
        ], width=3),
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H5(id='rt-unique-src', className='text-center text-warning'),
                html.P('Unique Sources', className='text-center text-muted')
            ]))
        ], width=3),
    ], className='mb-3'),

    dbc.Row([
        dbc.Col([dcc.Graph(id='rt-scatter', animate=False)], width=8),
        dbc.Col([dcc.Graph(id='rt-protocol-pie', animate=False)], width=4),
    ]),

    dbc.Row([
        dbc.Col([dcc.Graph(id='rt-bandwidth-timeline', animate=False)], width=12),
    ]),

    # Store per dati real-time
    dcc.Store(id='flow-store', data=[]),
    dcc.Interval(id='rt-interval', interval=2000, n_intervals=0),  # 2s refresh

], fluid=True)


@callback(
    [Output('flow-store', 'data'),
     Output('rt-flow-count', 'children'),
     Output('rt-anomaly-count', 'children'),
     Output('rt-bandwidth', 'children'),
     Output('rt-unique-src', 'children'),
     Output('rt-scatter', 'figure'),
     Output('rt-protocol-pie', 'figure'),
     Output('rt-bandwidth-timeline', 'figure')],
    [Input('rt-interval', 'n_intervals')],
    [Input('flow-store', 'data')]
)
def update_realtime(n, stored_flows):
    """Aggiorna visualizzazioni con nuovi flussi simulati."""
    generator = NetworkFlowGenerator(anomaly_rate=0.08)

    # Generare batch di flussi
    new_flows = []
    for _ in range(np.random.randint(5, 15)):
        if np.random.random() < 0.08:
            flow = generator.generate_anomalous_flow()
        else:
            flow = generator.generate_normal_flow()
        new_flows.append(asdict(flow))

    # Mantenere solo ultimi 500 flussi
    all_flows = (stored_flows or []) + new_flows
    all_flows = all_flows[-500:]

    df_flows = pd.DataFrame(all_flows)

    # KPIs
    flow_count = str(len(new_flows) * 30)  # Proiettato per minuto
    anomalies = str(len(df_flows[df_flows['anomaly_score'] > 0.6]))
    bandwidth = f"{df_flows['bytes_sent'].sum() / 1e6:.1f}"
    unique_src = str(df_flows['src_ip'].nunique())

    # Scatter: bytes vs anomaly score
    fig_scatter = go.Figure()
    normal = df_flows[df_flows['anomaly_score'] <= 0.6]
    anomalous = df_flows[df_flows['anomaly_score'] > 0.6]

    fig_scatter.add_trace(go.Scatter(
        x=normal['bytes_sent'], y=normal['anomaly_score'],
        mode='markers', name='Normal',
        marker=dict(color='#3498db', size=5, opacity=0.5)
    ))
    fig_scatter.add_trace(go.Scatter(
        x=anomalous['bytes_sent'], y=anomalous['anomaly_score'],
        mode='markers', name='Anomalous',
        marker=dict(color='#e74c3c', size=10, opacity=0.8,
                    symbol='diamond')
    ))
    fig_scatter.update_layout(
        title='Flow Anomaly Detection',
        xaxis_title='Bytes Sent', yaxis_title='Anomaly Score',
        template='plotly_dark', xaxis_type='log',
        showlegend=True, height=350
    )
    fig_scatter.add_hline(y=0.6, line_dash='dash', line_color='#e74c3c',
                          annotation_text='Threshold')

    # Protocol pie
    proto_counts = df_flows['protocol'].value_counts()
    fig_pie = go.Figure(go.Pie(
        labels=proto_counts.index, values=proto_counts.values,
        hole=0.5, marker=dict(colors=['#3498db', '#2ecc71', '#f39c12', '#9b59b6'])
    ))
    fig_pie.update_layout(title='Protocol Distribution',
                          template='plotly_dark', height=350)

    # Bandwidth timeline (ultimi 60 secondi simulati)
    df_flows['ts'] = pd.to_datetime(df_flows['timestamp'])
    bw_timeline = df_flows.set_index('ts').resample('5s')['bytes_sent'].sum() / 1e3
    fig_bw = go.Figure()
    fig_bw.add_trace(go.Scatter(
        x=bw_timeline.index, y=bw_timeline.values,
        fill='tozeroy', fillcolor='rgba(52, 152, 219, 0.2)',
        line=dict(color='#3498db', width=2),
        mode='lines'
    ))
    fig_bw.update_layout(
        title='Bandwidth (KB/5s)', template='plotly_dark',
        height=200, margin=dict(t=40, b=20)
    )

    return all_flows, flow_count, anomalies, bandwidth, unique_src, \
           fig_scatter, fig_pie, fig_bw


if __name__ == '__main__':
    app.run(debug=True, port=8052)
```

---

## Best Practices Summary

### Visualization Design Checklist

```
BEFORE CREATING ANY VISUALIZATION:

[ ] Define the question the visualization answers
[ ] Identify the audience (executive, analyst, engineer)
[ ] Choose the appropriate chart type for the data relationship
[ ] Select a colorblind-safe palette
[ ] Plan for accessibility (labels, alt text, patterns)

DURING CREATION:

[ ] Remove chartjunk (unnecessary gridlines, borders, backgrounds)
[ ] Maximize data-ink ratio
[ ] Use consistent encoding (same color = same meaning)
[ ] Add meaningful annotations
[ ] Ensure text is readable at display size
[ ] Include units on axes

BEFORE PUBLISHING:

[ ] Verify data accuracy
[ ] Check for misleading elements (truncated axes, wrong scales)
[ ] Test at target display size
[ ] Validate color contrast (WCAG AA minimum)
[ ] Add title, subtitle, source, and date
[ ] Test interactivity (if applicable)
```

### Security Dashboard Specific Guidelines

```
SOC DASHBOARD DESIGN:

1. LAYOUT
   - KPIs at top (MTTD, MTTR, Active Incidents, SLA)
   - Timeline center-left (largest panel)
   - Breakdown/detail panels right and bottom
   - Table for drill-down at bottom

2. COLOR CODING (consistent across all panels)
   - Critical: #e74c3c (red)
   - High: #f39c12 (orange)
   - Medium: #3498db (blue)
   - Low: #95a5a6 (gray)
   - Resolved/Good: #27ae60 (green)

3. REFRESH RATES
   - Real-time panels: 5-10 seconds
   - Summary panels: 30-60 seconds
   - Trend panels: 5 minutes
   - Historical: manual/daily

4. ALERTING THRESHOLDS
   - Visual indicators (color change) before alert fires
   - Clear threshold lines on time-series
   - Gauge panels for SLI/SLO tracking

5. INFORMATION DENSITY
   - NOC wall: 6-8 panels, large text
   - Analyst view: 12-20 panels, interactive
   - Executive view: 3-5 panels, annotated
```

### Tool Selection Guide

```
DECISION TREE:

Static publication figure?
  → Matplotlib + Seaborn

Interactive exploration (single user)?
  → Plotly Express / Jupyter

Interactive dashboard (team sharing)?
  → Plotly Dash or Grafana

Infrastructure monitoring + alerting?
  → Grafana + Prometheus

Business intelligence (self-service)?
  → Metabase (simple) or Superset (advanced)

Enterprise BI with governance?
  → Tableau or Power BI

Real-time streaming?
  → Grafana Live + Prometheus
  → Custom D3.js + WebSocket
  → Kibana + Elasticsearch

Security-specific?
  → Grafana for metrics
  → ELK/OpenSearch for logs
  → Custom Dash for ad-hoc analysis
```
