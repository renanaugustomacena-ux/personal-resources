# Analytics Avanzate — Cohort, Funnel e Data Stack — Guida Approfondita

## Indice
- [Panoramica](#panoramica)
- [Fondamenti dell'Analytics per SaaS](#fondamenti-dellanalytics-per-saas)
- [Cohort Analysis — Metodologia Completa](#cohort-analysis--metodologia-completa)
  - [Tipi di Cohort](#tipi-di-cohort)
  - [Acquisition Cohort — Deep Dive](#acquisition-cohort--deep-dive)
  - [Behavioral Cohort — Deep Dive](#behavioral-cohort--deep-dive)
  - [Revenue Cohort — Deep Dive](#revenue-cohort--deep-dive)
  - [Forme delle Curve di Retention](#forme-delle-curve-di-retention)
  - [Costruzione della Cohort Table](#costruzione-della-cohort-table)
  - [SQL per Cohort Analysis](#sql-per-cohort-analysis)
  - [Engagement Scoring](#engagement-scoring)
  - [Churn Prediction da Dati di Coorte](#churn-prediction-da-dati-di-coorte)
  - [LTV Modeling da Coorti](#ltv-modeling-da-coorti)
  - [Cohort Analysis Avanzata](#cohort-analysis-avanzata)
  - [Visualizzazione delle Cohort](#visualizzazione-delle-cohort)
  - [Best Practice per la Visualizzazione delle Coorti](#best-practice-per-la-visualizzazione-delle-coorti)
- [Funnel Optimization — Il Framework AARRR](#funnel-optimization--il-framework-aarrr)
  - [Le Cinque Fasi del Pirate Metrics](#le-cinque-fasi-del-pirate-metrics)
  - [Funnel Analysis Pratica](#funnel-analysis-pratica)
  - [Ottimizzazione per Stadio del Funnel](#ottimizzazione-per-stadio-del-funnel)
  - [Activation Metrics — Deep Dive](#activation-metrics--deep-dive)
  - [A/B Testing per Funnel](#ab-testing-per-funnel)
  - [Significatività Statistica nei Funnel](#significatività-statistica-nei-funnel)
- [Event Tracking Design](#event-tracking-design)
- [A/B Testing — Fondamenti Statistici](#ab-testing--fondamenti-statistici)
- [Dashboard Design per SaaS](#dashboard-design-per-saas)
- [Data Stack Moderno — Segment, Amplitude, Mixpanel](#data-stack-moderno--segment-amplitude-mixpanel)
  - [Confronto Dettagliato: Amplitude vs Mixpanel vs PostHog](#confronto-dettagliato-amplitude-vs-mixpanel-vs-posthog)
- [Data Warehouse e Analytics Engineering](#data-warehouse-e-analytics-engineering)
- [Product Analytics Avanzate](#product-analytics-avanzate)
- [Privacy-Compliant Analytics](#privacy-compliant-analytics)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'analytics è il sistema nervoso di un'azienda SaaS. Senza dati accurati, ogni decisione — dal design del prodotto al pricing, dall'allocazione del budget marketing alla prioritizzazione della roadmap — è basata su intuizione e aneddoti. In un mercato competitivo dove la differenza tra successo e fallimento è spesso nei dettagli, le decisioni data-driven sono un vantaggio competitivo sistematico, non un lusso.

Tuttavia, la sfida non è raccogliere dati — è raccogliere i dati giusti, analizzarli correttamente, e tradurre l'analisi in decisioni operative. Molte aziende SaaS si trovano in una delle due trappole: raccolgono troppo pochi dati e operano quasi alla cieca, oppure raccolgono troppi dati senza struttura e si perdono in un oceano di metriche vanity che non informano alcuna decisione.

Questa guida copre ogni aspetto dell'analytics per SaaS: dalla cohort analysis alla funnel optimization, dall'event tracking design alla statistica degli A/B test, dal design delle dashboard all'architettura del data stack moderno. L'obiettivo è fornire un framework completo e operativo per costruire un sistema di analytics che informi realmente le decisioni aziendali.

---

## Fondamenti dell'Analytics per SaaS

### Le Tre Categorie di Analytics

**Descriptive Analytics (cosa è successo)**: dashboard, report, metriche di base. Risponde a domande come: "Quanti utenti si sono registrati questo mese?", "Qual è il churn rate?", "Quale canale ha generato più clienti?". È il livello fondamentale — senza descriptive analytics affidabili, tutto il resto è impossibile.

**Diagnostic Analytics (perché è successo)**: segmentazione, cohort analysis, funnel analysis. Risponde a domande come: "Perché il churn è aumentato questo mese?", "Quale segmento di utenti ha la retention migliore?", "Dove nel funnel stiamo perdendo utenti?". Richiede capacità di segmentazione e drill-down.

**Predictive Analytics (cosa succederà)**: modelli predittivi, churn prediction, lead scoring. Risponde a domande come: "Quali utenti hanno alta probabilità di churnare il mese prossimo?", "Quale sarà il MRR tra 6 mesi?". Richiede competenze di data science e volume di dati sufficiente.

### Metriche vs Vanity Metrics

La distinzione tra metriche actionable e vanity metrics è fondamentale:

**Vanity Metrics**: numeri che "sembrano buoni" ma non informano decisioni.
- Totale utenti registrati (include account inattivi da anni)
- Page views totali (non indica engagement reale)
- Download totali (non indica utilizzo)
- Follower sui social media (non indica conversione)

**Actionable Metrics**: numeri che informano decisioni concrete.
- Activation rate (informo il design dell'onboarding)
- Retention per coorte (informo le priorità di prodotto)
- CAC per canale (informo l'allocazione del budget marketing)
- Feature adoption rate (informo la roadmap)
- Revenue per segmento (informo la strategia di pricing)

Regola pratica: se non sai quale decisione cambieresti basandoti su un cambiamento nella metrica, è probabilmente una vanity metric.

---

## Cohort Analysis — Metodologia Completa

### Tipi di Cohort

**Acquisition Cohort**: raggruppamento per data di registrazione. Il tipo più comune. Permette di confrontare il comportamento di utenti acquisiti in periodi diversi.

**Behavioral Cohort**: raggruppamento per comportamento. Esempio: "utenti che hanno completato l'onboarding vs quelli che non l'hanno completato", "utenti che hanno usato la feature X vs quelli che non l'hanno usata". Permette di identificare quali comportamenti predicono la retention.

**Revenue Cohort**: raggruppamento per piano di pricing o revenue. Permette di analizzare la retention e l'expansion per segmento di valore.

### Acquisition Cohort — Deep Dive

L'acquisition cohort è il tipo più diffuso e la base di qualsiasi analisi di retention. Raggruppa gli utenti per il mese (o settimana) in cui si sono registrati, poi traccia il loro comportamento nei periodi successivi.

**Perché è fondamentale**: confrontando le coorti nel tempo si può rispondere a domande critiche:
- Il prodotto sta migliorando? (le coorti recenti hanno retention migliore?)
- Un cambiamento di canale ha portato utenti di qualità diversa?
- Il lancio di una nuova feature ha impattato la retention?

**Definizione del "periodo zero"**: il Mese 0 di una coorte è il mese di registrazione. Il Mese 1 è il mese successivo, e così via. Attenzione: utenti registrati il 28 gennaio hanno solo 3 giorni nel Mese 0, quelli registrati il 1 gennaio ne hanno 31. Per coorti settimanali questo bias è minore.

**Granularità temporale**:
- **Coorti settimanali**: ideali per prodotti con ciclo d'uso giornaliero/settimanale (es. tool di collaborazione). Permettono di rilevare cambiamenti rapidamente ma generano tabelle grandi.
- **Coorti mensili**: lo standard per la maggior parte dei SaaS B2B. Bilancio tra granularità e leggibilità.
- **Coorti trimestrali**: utili per prodotti enterprise con cicli di vendita lunghi, o per analisi di trend a lungo termine.

**Esempio pratico — Interpretare una cohort table di acquisizione**:

Supponiamo di avere un SaaS B2B con ciclo d'uso settimanale. La tabella seguente mostra la percentuale di utenti di ogni coorte mensile che risultano attivi (almeno 1 sessione) nel mese indicato:

```
Coorte      M0    M1    M2    M3    M4    M5    M6
Gen 2025   100%   42%   35%   30%   28%   27%   26%
Feb 2025   100%   45%   38%   33%   31%   29%   —
Mar 2025   100%   48%   40%   36%   33%   —     —
Apr 2025   100%   50%   43%   38%   —     —     —
Mag 2025   100%   52%   45%   —     —     —     —
Giu 2025   100%   55%   —     —     —     —     —
```

**Lettura**: la coorte di gennaio parte da 100% al Mese 0 (per definizione) e scende al 42% al Mese 1. Dopo 6 mesi, il 26% degli utenti originali è ancora attivo. La coorte di giugno mostra il 55% al Mese 1 — un miglioramento significativo rispetto al 42% di gennaio. Questo indica che qualcosa è cambiato (prodotto migliore, canale di acquisizione diverso, onboarding ottimizzato).

**Segnali d'allarme**:
- Tutte le coorti convergono allo stesso livello → il prodotto ha un "tetto naturale" di retention
- Le coorti recenti peggiorano → il canale di acquisizione sta portando utenti di qualità inferiore
- Il drop dal M0 al M1 è superiore al 60% → problema critico di attivazione/onboarding

### Behavioral Cohort — Deep Dive

La behavioral cohort non raggruppa per data di registrazione ma per azione compiuta. È lo strumento più potente per identificare quali comportamenti predicono la retention a lungo termine.

**Casi d'uso principali**:
1. **Identificare l'"aha moment"**: quale azione, se compiuta entro i primi N giorni, correla con retention significativamente più alta?
2. **Validare feature hypothesis**: la nuova feature migliora davvero la retention di chi la usa?
3. **Segmentare per engagement**: utenti "power user" vs "casual" vs "dormiente" — come si comportano nel tempo?

**Framework per trovare l'aha moment**:

```
Passaggio 1: Elencare le azioni chiave nel prodotto
  - Creare un progetto
  - Invitare un collaboratore
  - Completare un task
  - Usare una integrazione
  - Esportare un report

Passaggio 2: Per ogni azione, calcolare la retention a 30 giorni
  degli utenti che l'hanno compiuta entro i primi 7 giorni vs quelli che non l'hanno compiuta

Passaggio 3: Ordinare per "retention lift" (differenza tra i due gruppi)

  Azione                    Retention 30g   Retention 30g    Lift
                            (con azione)    (senza azione)
  ──────────────────────────────────────────────────────────────────
  Invitare collaboratore      72%              28%           +44pp  ← AHA MOMENT
  Completare 3+ task          65%              31%           +34pp
  Creare 2+ progetti          60%              33%           +27pp
  Usare integrazione          58%              35%           +23pp
  Esportare report            45%              36%            +9pp

Passaggio 4: L'"aha moment" è "invitare almeno 1 collaboratore entro 7 giorni"
  → L'onboarding deve guidare verso questa azione
```

**Attenzione alla causalità**: un alto lift non significa necessariamente causalità. Gli utenti che invitano collaboratori potrebbero essere semplicemente più motivati in partenza. Per stabilire causalità serve un A/B test (es. forzare vs non forzare l'invito nel flusso di onboarding). Ma la correlazione è comunque un segnale forte per prioritizzare l'onboarding.

**Behavioral cohort per feature adoption**:

```
Feature X lanciata a marzo 2025. Confronto retention:

                    M1    M2    M3    M4    M5
Utenti che usano X  68%   55%   48%   45%   43%
Utenti che NON usano X  41%   30%   24%   21%   19%
Lift                +27pp +25pp +24pp +24pp +24pp

Conclusione: la Feature X ha un impatto costante e significativo
sulla retention. Dovrebbe essere promossa nell'onboarding e
nella comunicazione in-app.
```

### Revenue Cohort — Deep Dive

La revenue cohort analizza non la retention degli utenti ma la retention della revenue (Net Revenue Retention — NRR) per coorte. È fondamentale per capire se il business sta crescendo in modo sano.

**Tre pattern di revenue cohort**:

```
Pattern 1: Revenue retention > 100% (NRR > 100%)
→ L'espansione (upgrade + add-on) supera il churn + la contrazione
→ Ogni coorte CRESCE nel tempo — il santo graal SaaS

Coorte Gen   €10K   €11K   €12K   €13K   €14K   €15K
             100%   110%   120%   130%   140%   150%

Pattern 2: Revenue retention ~100% (NRR ~100%)
→ L'espansione compensa esattamente il churn
→ La crescita dipende interamente dall'acquisizione di nuovi clienti

Coorte Gen   €10K   €10K   €10K   €10K   €10K   €10K
             100%   100%   100%   100%   100%   100%

Pattern 3: Revenue retention < 100% (NRR < 85%)
→ Il churn supera l'espansione — il "leaky bucket"
→ Anche acquisendo nuovi clienti, la revenue di coorte si erode

Coorte Gen   €10K   €9K    €8K    €7K    €6.5K  €6K
             100%    90%    80%    70%    65%    60%
```

**Calcolo della NRR per coorte in SQL**:

```sql
-- Net Revenue Retention per coorte mensile
WITH customer_cohort AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(payment_date)) AS cohort_month
    FROM payments
    WHERE amount > 0
    GROUP BY customer_id
),
monthly_revenue AS (
    SELECT
        c.cohort_month,
        DATE_TRUNC('month', p.payment_date) AS revenue_month,
        SUM(p.amount) AS total_revenue
    FROM payments p
    JOIN customer_cohort c ON p.customer_id = c.customer_id
    GROUP BY 1, 2
),
cohort_nrr AS (
    SELECT
        cohort_month,
        revenue_month,
        EXTRACT(YEAR FROM AGE(revenue_month, cohort_month)) * 12
            + EXTRACT(MONTH FROM AGE(revenue_month, cohort_month)) AS month_number,
        total_revenue,
        FIRST_VALUE(total_revenue) OVER (
            PARTITION BY cohort_month ORDER BY revenue_month
        ) AS initial_revenue,
        ROUND(
            total_revenue * 100.0 /
            FIRST_VALUE(total_revenue) OVER (
                PARTITION BY cohort_month ORDER BY revenue_month
            ), 1
        ) AS nrr_pct
    FROM monthly_revenue
)
SELECT
    TO_CHAR(cohort_month, 'YYYY-MM') AS coorte,
    month_number AS mese,
    total_revenue,
    initial_revenue,
    nrr_pct
FROM cohort_nrr
WHERE month_number <= 12
ORDER BY cohort_month, month_number;
```

**Segmentazione della revenue cohort**: è cruciale segmentare per piano:

```
Piano        M0      M3      M6      M12     NRR 12m
─────────────────────────────────────────────────────
Starter      €50K    €42K    €35K    €28K    56%   ← Problema
Pro          €120K   €125K   €130K   €135K   112%  ← Sano
Enterprise   €200K   €220K   €240K   €270K   135%  ← Eccellente

Insight: il piano Starter ha NRR del 56% — gli utenti
churnano o non espandono. Possibili azioni:
1. Migliorare il percorso di upgrade Starter → Pro
2. Aggiungere incentivi all'espansione per Starter
3. Se il CAC per acquisire uno Starter è alto, ripensare il piano
```

### Forme delle Curve di Retention

Le curve di retention seguono pattern riconoscibili. Saper leggere la forma di una curva è una competenza critica per chi gestisce un prodotto SaaS.

**Curva "Smile" (sorriso)** — La migliore possibile:

```
Retention
100% │●
     │ ●
     │  ●
 40% │   ●
     │    ●
 25% │     ●●
     │       ●●
 30% │         ●●●
     │            ●●●●
 35% │                ●●●●●●
     └──────────────────────────── Mesi
      0  1  2  3  4  5  6  7  8  9  10  11  12

Caratteristiche:
- Drop iniziale rapido (M0 → M2)
- Stabilizzazione (M3-M5)
- Leggera risalita (M6+)

Cause della risalita:
- Utenti che ri-attivano (es. uso stagionale)
- Espansione organica (inviti, team growth)
- Feature che creano abitudine nel lungo periodo

Prodotti tipici: strumenti di collaborazione (Slack, Notion),
tool stagionali (contabilità, tax), social network
```

**Curva "Flat" (piatta)** — Buona, il pattern più comune nei SaaS sani:

```
Retention
100% │●
     │ ●
     │  ●
 45% │   ●
     │    ●●
 35% │      ●●●
     │         ●●●●●●●●●●●●●●●●●●●●
 30% │
     │
     └──────────────────────────── Mesi
      0  1  2  3  4  5  6  7  8  9  10  11  12

Caratteristiche:
- Drop iniziale (M0 → M3)
- Stabilizzazione a un plateau (M4+)
- Il plateau è la "retention naturale" del prodotto

Interpretazione:
- Il plateau indica che chi sopravvive ai primi 3 mesi resta
- Più alto è il plateau, meglio è (>30% M12 per B2B SaaS è buono)
- Il focus deve essere sull'innalzare il plateau E sul ridurre il drop iniziale

Prodotti tipici: CRM, project management, analytics tools
```

**Curva "Cliff" (precipizio)** — Critica, indica un problema fondamentale:

```
Retention
100% │●
     │ ●
     │  ●
 40% │   ●
     │    ●
 25% │     ●
     │      ●
 15% │       ●
     │        ●
  5% │         ●●●●
  0% │               ●●●●●●●
     └──────────────────────────── Mesi
      0  1  2  3  4  5  6  7  8  9  10  11  12

Caratteristiche:
- Drop continuo senza mai stabilizzarsi
- La curva tende a zero
- Nessun plateau naturale

Cause:
- Product-market fit assente o debole
- Il prodotto risolve un problema one-time, non ricorrente
- Utenti acquisiti tramite incentivi che non riflettono il valore reale
- Competizione che offre alternative migliori

Azione urgente:
- NON investire in acquisizione finché la curva non si stabilizza
- Intervistare utenti churned per capire perché se ne vanno
- Ripensare il prodotto core o il segmento target
```

**Come distinguere le tre curve in pratica**:

| Indicatore | Smile | Flat | Cliff |
|---|---|---|---|
| Retention M6 vs M3 | Superiore | Uguale (±2pp) | Inferiore |
| Retention M12 | > Retention M6 | ≈ Retention M6 | < 10% |
| Trend tra coorti | Stabile o in crescita | Stabile | In peggioramento |
| Azione prioritaria | Ridurre il dip iniziale | Alzare il plateau | Fix product-market fit |

### Costruzione della Cohort Table

La cohort table (tabella di coorte) è la struttura dati fondamentale. Sapere costruirla, leggerla, e interpretarla è una competenza non negoziabile.

**Struttura base**:

```
                        Mesi dalla registrazione
Coorte         M0     M1     M2     M3     M4     M5     M6
──────────────────────────────────────────────────────────────
Gen 2025      1,200    504    396    336    300    276    264
Feb 2025      1,350    594    473    405    365    338     —
Mar 2025      1,100    495    385    330    297     —      —
Apr 2025      1,500    720    570    480     —      —      —
Mag 2025      1,400    700    560     —      —      —      —
Giu 2025      1,600    848     —      —      —      —      —
```

**Stessa tabella in percentuali**:

```
                        Mesi dalla registrazione
Coorte         M0     M1     M2     M3     M4     M5     M6
──────────────────────────────────────────────────────────────
Gen 2025      100%    42%    33%    28%    25%    23%    22%
Feb 2025      100%    44%    35%    30%    27%    25%     —
Mar 2025      100%    45%    35%    30%    27%     —      —
Apr 2025      100%    48%    38%    32%     —      —      —
Mag 2025      100%    50%    40%     —      —      —      —
Giu 2025      100%    53%     —      —      —      —      —
```

**Lettura diagonale**: la diagonale della tabella mostra cosa succedeva nello stesso mese di calendario. Ad esempio, la cella Gen M5 e Feb M4 corrispondono entrambe a giugno 2025. Se un evento esterno (crash del server, feature rilasciata, campagna marketing) ha impattato quel mese, si vedrà sulla diagonale.

**Lettura per riga**: ogni riga racconta la storia di una coorte specifica — come si è comportata nel tempo. Confrontare le righe rivela se il prodotto sta migliorando.

**Lettura per colonna**: ogni colonna mostra come si comportano coorti diverse allo stesso stadio di maturità. La colonna M1 mostra la retention al primo mese per ogni coorte — un trend crescente indica miglioramenti nell'onboarding.

**Costruzione passo-passo in SQL**:

```sql
-- Passo 1: Determinare la coorte di ogni utente
CREATE TEMP TABLE user_cohorts AS
SELECT
    user_id,
    DATE_TRUNC('month', created_at) AS cohort_month
FROM users
WHERE created_at >= '2025-01-01';

-- Passo 2: Determinare i mesi di attività di ogni utente
CREATE TEMP TABLE user_activity_months AS
SELECT DISTINCT
    user_id,
    DATE_TRUNC('month', event_timestamp) AS activity_month
FROM events
WHERE event_type IN ('session_start', 'page_view', 'action_performed');

-- Passo 3: Calcolare il numero di mese relativo
CREATE TEMP TABLE cohort_data AS
SELECT
    uc.cohort_month,
    EXTRACT(YEAR FROM AGE(ua.activity_month, uc.cohort_month)) * 12
        + EXTRACT(MONTH FROM AGE(ua.activity_month, uc.cohort_month))
        AS month_number,
    COUNT(DISTINCT uc.user_id) AS active_users
FROM user_cohorts uc
JOIN user_activity_months ua ON uc.user_id = ua.user_id
WHERE ua.activity_month >= uc.cohort_month
GROUP BY 1, 2;

-- Passo 4: Calcolare la dimensione iniziale della coorte
CREATE TEMP TABLE cohort_sizes AS
SELECT
    cohort_month,
    COUNT(DISTINCT user_id) AS cohort_size
FROM user_cohorts
GROUP BY 1;

-- Passo 5: Produrre la tabella di retention
SELECT
    TO_CHAR(cd.cohort_month, 'Mon YYYY') AS coorte,
    cs.cohort_size,
    cd.month_number AS mese,
    cd.active_users,
    ROUND(cd.active_users * 100.0 / cs.cohort_size, 1) AS retention_pct
FROM cohort_data cd
JOIN cohort_sizes cs ON cd.cohort_month = cs.cohort_month
WHERE cd.month_number BETWEEN 0 AND 12
ORDER BY cd.cohort_month, cd.month_number;
```

**Pivotare la tabella** (PostgreSQL con `crosstab` o manualmente):

```sql
-- Pivot manuale per ottenere il formato classico della cohort table
SELECT
    TO_CHAR(cohort_month, 'Mon YYYY') AS coorte,
    cohort_size,
    MAX(CASE WHEN month_number = 0 THEN retention_pct END) AS "M0",
    MAX(CASE WHEN month_number = 1 THEN retention_pct END) AS "M1",
    MAX(CASE WHEN month_number = 2 THEN retention_pct END) AS "M2",
    MAX(CASE WHEN month_number = 3 THEN retention_pct END) AS "M3",
    MAX(CASE WHEN month_number = 4 THEN retention_pct END) AS "M4",
    MAX(CASE WHEN month_number = 5 THEN retention_pct END) AS "M5",
    MAX(CASE WHEN month_number = 6 THEN retention_pct END) AS "M6",
    MAX(CASE WHEN month_number = 7 THEN retention_pct END) AS "M7",
    MAX(CASE WHEN month_number = 8 THEN retention_pct END) AS "M8",
    MAX(CASE WHEN month_number = 9 THEN retention_pct END) AS "M9",
    MAX(CASE WHEN month_number = 10 THEN retention_pct END) AS "M10",
    MAX(CASE WHEN month_number = 11 THEN retention_pct END) AS "M11",
    MAX(CASE WHEN month_number = 12 THEN retention_pct END) AS "M12"
FROM (
    SELECT
        cd.cohort_month,
        cs.cohort_size,
        cd.month_number,
        ROUND(cd.active_users * 100.0 / cs.cohort_size, 1) AS retention_pct
    FROM cohort_data cd
    JOIN cohort_sizes cs ON cd.cohort_month = cs.cohort_month
) sub
GROUP BY cohort_month, cohort_size
ORDER BY cohort_month;
```

### SQL per Cohort Analysis

Oltre alla costruzione base, ecco query SQL avanzate per scenari comuni.

**Cohort retention settimanale** (utile per prodotti con ciclo d'uso breve):

```sql
WITH user_cohorts AS (
    SELECT
        user_id,
        DATE_TRUNC('week', created_at) AS cohort_week
    FROM users
),
weekly_activity AS (
    SELECT DISTINCT
        user_id,
        DATE_TRUNC('week', event_timestamp) AS activity_week
    FROM events
),
retention AS (
    SELECT
        uc.cohort_week,
        EXTRACT(DAY FROM (wa.activity_week - uc.cohort_week))::int / 7
            AS week_number,
        COUNT(DISTINCT uc.user_id) AS active_users
    FROM user_cohorts uc
    JOIN weekly_activity wa ON uc.user_id = wa.user_id
    WHERE wa.activity_week >= uc.cohort_week
    GROUP BY 1, 2
),
sizes AS (
    SELECT cohort_week, COUNT(DISTINCT user_id) AS cohort_size
    FROM user_cohorts
    GROUP BY 1
)
SELECT
    TO_CHAR(r.cohort_week, 'YYYY-"W"IW') AS coorte,
    s.cohort_size,
    r.week_number AS settimana,
    r.active_users,
    ROUND(r.active_users * 100.0 / s.cohort_size, 1) AS retention_pct
FROM retention r
JOIN sizes s ON r.cohort_week = s.cohort_week
WHERE r.week_number BETWEEN 0 AND 12
ORDER BY r.cohort_week, r.week_number;
```

**Cohort retention per canale di acquisizione**:

```sql
-- Confrontare la retention tra canali (organic, paid, referral)
WITH user_cohorts AS (
    SELECT
        u.user_id,
        DATE_TRUNC('month', u.created_at) AS cohort_month,
        COALESCE(u.utm_source, 'direct') AS acquisition_channel
    FROM users u
),
monthly_activity AS (
    SELECT DISTINCT
        user_id,
        DATE_TRUNC('month', event_timestamp) AS activity_month
    FROM events
),
retention_by_channel AS (
    SELECT
        uc.acquisition_channel,
        EXTRACT(YEAR FROM AGE(ma.activity_month, uc.cohort_month)) * 12
            + EXTRACT(MONTH FROM AGE(ma.activity_month, uc.cohort_month))
            AS month_number,
        COUNT(DISTINCT uc.user_id) AS active_users
    FROM user_cohorts uc
    JOIN monthly_activity ma ON uc.user_id = ma.user_id
    WHERE ma.activity_month >= uc.cohort_month
    GROUP BY 1, 2
),
channel_sizes AS (
    SELECT
        acquisition_channel,
        COUNT(DISTINCT user_id) AS channel_size
    FROM user_cohorts
    GROUP BY 1
)
SELECT
    r.acquisition_channel,
    cs.channel_size AS utenti_totali,
    r.month_number AS mese,
    r.active_users,
    ROUND(r.active_users * 100.0 / cs.channel_size, 1) AS retention_pct
FROM retention_by_channel r
JOIN channel_sizes cs ON r.acquisition_channel = cs.acquisition_channel
WHERE r.month_number BETWEEN 0 AND 6
ORDER BY r.acquisition_channel, r.month_number;
```

**Revenue retention per coorte (Dollar Retention)**:

```sql
-- Dollar Retention: quanto revenue si mantiene per coorte
WITH customer_first_payment AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(payment_date)) AS cohort_month
    FROM payments
    WHERE amount > 0 AND status = 'succeeded'
    GROUP BY customer_id
),
monthly_revenue AS (
    SELECT
        cfp.cohort_month,
        DATE_TRUNC('month', p.payment_date) AS revenue_month,
        EXTRACT(YEAR FROM AGE(
            DATE_TRUNC('month', p.payment_date), cfp.cohort_month
        )) * 12 + EXTRACT(MONTH FROM AGE(
            DATE_TRUNC('month', p.payment_date), cfp.cohort_month
        )) AS month_number,
        SUM(p.amount) AS revenue
    FROM payments p
    JOIN customer_first_payment cfp ON p.customer_id = cfp.customer_id
    WHERE p.status = 'succeeded'
    GROUP BY 1, 2, 3
)
SELECT
    TO_CHAR(cohort_month, 'Mon YYYY') AS coorte,
    month_number AS mese,
    revenue,
    ROUND(
        revenue * 100.0 /
        FIRST_VALUE(revenue) OVER (
            PARTITION BY cohort_month ORDER BY month_number
        ), 1
    ) AS dollar_retention_pct
FROM monthly_revenue
WHERE month_number BETWEEN 0 AND 12
ORDER BY cohort_month, month_number;
```

**Query per identificare il "punto di non ritorno"** — il mese dopo il quale la retention si stabilizza:

```sql
-- Trovare il mese dove la retention smette di scendere significativamente
WITH retention_data AS (
    -- (usa la query di retention base per popolare questa CTE)
    SELECT cohort_month, month_number, retention_pct
    FROM cohort_retention_table
),
month_over_month AS (
    SELECT
        month_number,
        AVG(retention_pct) AS avg_retention,
        LAG(AVG(retention_pct)) OVER (ORDER BY month_number) AS prev_retention,
        AVG(retention_pct) - LAG(AVG(retention_pct)) OVER (ORDER BY month_number)
            AS delta
    FROM retention_data
    GROUP BY month_number
)
SELECT
    month_number,
    ROUND(avg_retention, 1) AS retention_media,
    ROUND(delta, 1) AS variazione_pp,
    CASE
        WHEN ABS(delta) < 2 THEN '✓ Stabile'
        WHEN delta < -5 THEN '⚠ Drop significativo'
        ELSE '→ In calo'
    END AS stato
FROM month_over_month
WHERE month_number BETWEEN 1 AND 12
ORDER BY month_number;

-- Output tipico:
-- M1  45.0  -55.0  ⚠ Drop significativo
-- M2  37.0   -8.0  ⚠ Drop significativo
-- M3  32.0   -5.0  → In calo
-- M4  29.5   -2.5  → In calo
-- M5  28.0   -1.5  ✓ Stabile   ← plateau raggiunto al M5
-- M6  27.5   -0.5  ✓ Stabile
```

### Engagement Scoring

L'engagement scoring assegna un punteggio numerico a ogni utente basato sulla sua attività recente. È il ponte tra la cohort analysis (macro) e l'intervento operativo (micro — es. "quali utenti contattare prima che churnino").

**Framework per l'engagement score**:

```
Engagement Score = Σ (Peso_azione × Frequenza_azione × Recency_decay)

Componenti:
1. Peso dell'azione: alcune azioni valgono più di altre
2. Frequenza: quante volte l'azione è stata compiuta nel periodo
3. Recency decay: azioni recenti contano di più (decadimento esponenziale)
```

**Definizione dei pesi per un SaaS di project management**:

```
Azione                      Peso    Razionale
──────────────────────────────────────────────
Login                        1      Minimo engagement
Visualizzare dashboard       2      Indica interesse
Creare task                  5      Azione core
Completare task              7      Indica valore derivato
Commentare                   4      Collaborazione
Invitare membro              10     Espansione, alto valore
Usare integrazione           8      Lock-in
Creare report                6      Uso avanzato
Usare API                    9      Deep integration
```

**Implementazione SQL dell'engagement score**:

```sql
-- Calcolo dell'engagement score per utente
WITH action_weights AS (
    SELECT * FROM (VALUES
        ('login', 1),
        ('dashboard_view', 2),
        ('task_created', 5),
        ('task_completed', 7),
        ('comment_added', 4),
        ('member_invited', 10),
        ('integration_used', 8),
        ('report_created', 6),
        ('api_call', 9)
    ) AS t(action_type, weight)
),
user_actions AS (
    SELECT
        e.user_id,
        e.event_type AS action_type,
        COUNT(*) AS frequency,
        -- Recency: decadimento esponenziale (halflife = 14 giorni)
        EXP(-0.693 * EXTRACT(DAY FROM (CURRENT_DATE - MAX(e.event_timestamp)))
            / 14.0) AS recency_factor,
        MAX(e.event_timestamp) AS last_action_at
    FROM events e
    WHERE e.event_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY e.user_id, e.event_type
),
scores AS (
    SELECT
        ua.user_id,
        SUM(
            aw.weight
            * LEAST(ua.frequency, 50)  -- cap per evitare outlier
            * ua.recency_factor
        ) AS raw_score
    FROM user_actions ua
    JOIN action_weights aw ON ua.action_type = aw.action_type
    GROUP BY ua.user_id
)
SELECT
    user_id,
    ROUND(raw_score, 1) AS engagement_score,
    NTILE(5) OVER (ORDER BY raw_score) AS engagement_quintile,
    CASE
        WHEN NTILE(5) OVER (ORDER BY raw_score) = 5 THEN 'Power User'
        WHEN NTILE(5) OVER (ORDER BY raw_score) = 4 THEN 'Attivo'
        WHEN NTILE(5) OVER (ORDER BY raw_score) = 3 THEN 'Medio'
        WHEN NTILE(5) OVER (ORDER BY raw_score) = 2 THEN 'A rischio'
        WHEN NTILE(5) OVER (ORDER BY raw_score) = 1 THEN 'Dormiente'
    END AS engagement_label
FROM scores
ORDER BY raw_score DESC;
```

**Segmentazione operativa basata sull'engagement score**:

```
Segmento       Score Range    Azione operativa
──────────────────────────────────────────────────────
Power User     80-100         Chiedere referral, invitare in beta
Attivo         60-79          Proporre upgrade, feature avanzate
Medio          40-59          Nurturing, tip e tutorial
A rischio      20-39          Intervento CS proattivo, check-in call
Dormiente       0-19          Campagna di re-engagement, survey churn
```

### Churn Prediction da Dati di Coorte

La churn prediction classica (modello ML su feature individuali) è potente ma complessa. I dati di coorte offrono un approccio complementare e più accessibile.

**Approccio 1: Segnali di coorte per early warning**

```
Indicatore                              Soglia d'allarme
───────────────────────────────────────────────────────────
Retention M1 di una coorte              < 35% (B2B SaaS)
Drop M1→M2 di una coorte               > 15pp
Engagement score medio della coorte     Cala > 20% M/M
% utenti "Dormiente" nella coorte       > 40%
NRR della coorte                        < 90%
```

**Approccio 2: Modello predittivo basato su metriche di engagement**

```python
def cohort_churn_risk_score(user_metrics):
    """
    Calcolare il rischio di churn basato su metriche di engagement
    rispetto alla media della coorte.

    Ogni metrica contribuisce al rischio con un peso specifico.
    Score 0-100: 0 = rischio nullo, 100 = quasi certo churn.
    """
    risk_score = 0

    # 1. Login frequency vs coorte (peso: 25%)
    login_ratio = user_metrics['logins_last_14d'] / max(
        user_metrics['cohort_avg_logins_14d'], 1
    )
    if login_ratio < 0.3:
        risk_score += 25
    elif login_ratio < 0.6:
        risk_score += 15
    elif login_ratio < 0.8:
        risk_score += 5

    # 2. Giorni dall'ultimo login (peso: 25%)
    days_inactive = user_metrics['days_since_last_login']
    if days_inactive > 14:
        risk_score += 25
    elif days_inactive > 7:
        risk_score += 15
    elif days_inactive > 3:
        risk_score += 5

    # 3. Feature usage trend (peso: 20%)
    usage_trend = user_metrics['actions_last_7d'] / max(
        user_metrics['actions_prev_7d'], 1
    )
    if usage_trend < 0.3:
        risk_score += 20
    elif usage_trend < 0.6:
        risk_score += 12
    elif usage_trend < 0.8:
        risk_score += 4

    # 4. Ticket supporto recenti (peso: 15%)
    if user_metrics['support_tickets_last_30d'] >= 3:
        risk_score += 15
    elif user_metrics['support_tickets_last_30d'] >= 2:
        risk_score += 8

    # 5. Adoption di feature core (peso: 15%)
    core_feature_adoption = user_metrics['core_features_used'] / max(
        user_metrics['total_core_features'], 1
    )
    if core_feature_adoption < 0.2:
        risk_score += 15
    elif core_feature_adoption < 0.4:
        risk_score += 8

    return min(risk_score, 100)
```

**SQL per identificare utenti ad alto rischio nella coorte**:

```sql
-- Utenti con engagement in calo rispetto alla media della coorte
WITH user_cohort AS (
    SELECT user_id, DATE_TRUNC('month', created_at) AS cohort_month
    FROM users
),
recent_activity AS (
    SELECT
        user_id,
        COUNT(*) FILTER (
            WHERE event_timestamp >= CURRENT_DATE - INTERVAL '14 days'
        ) AS actions_last_14d,
        COUNT(*) FILTER (
            WHERE event_timestamp BETWEEN
                CURRENT_DATE - INTERVAL '28 days'
                AND CURRENT_DATE - INTERVAL '14 days'
        ) AS actions_prev_14d,
        MAX(event_timestamp) AS last_activity
    FROM events
    GROUP BY user_id
),
cohort_averages AS (
    SELECT
        uc.cohort_month,
        AVG(ra.actions_last_14d) AS avg_actions_14d
    FROM user_cohort uc
    JOIN recent_activity ra ON uc.user_id = ra.user_id
    GROUP BY 1
)
SELECT
    uc.user_id,
    uc.cohort_month,
    ra.actions_last_14d,
    ca.avg_actions_14d AS media_coorte,
    ROUND(ra.actions_last_14d / NULLIF(ca.avg_actions_14d, 0), 2)
        AS ratio_vs_coorte,
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - ra.last_activity)) AS giorni_inattivo,
    CASE
        WHEN ra.actions_last_14d = 0 THEN 'CRITICO'
        WHEN ra.actions_last_14d < ca.avg_actions_14d * 0.3 THEN 'ALTO'
        WHEN ra.actions_last_14d < ca.avg_actions_14d * 0.6 THEN 'MEDIO'
        ELSE 'BASSO'
    END AS rischio_churn
FROM user_cohort uc
JOIN recent_activity ra ON uc.user_id = ra.user_id
JOIN cohort_averages ca ON uc.cohort_month = ca.cohort_month
WHERE ra.actions_last_14d < ca.avg_actions_14d * 0.5
    OR EXTRACT(DAY FROM (CURRENT_TIMESTAMP - ra.last_activity)) > 7
ORDER BY
    CASE
        WHEN ra.actions_last_14d = 0 THEN 1
        WHEN ra.actions_last_14d < ca.avg_actions_14d * 0.3 THEN 2
        ELSE 3
    END,
    ra.actions_last_14d ASC;
```

### LTV Modeling da Coorti

Il Lifetime Value (LTV) è il ricavo totale atteso da un cliente durante la sua vita utile. I dati di coorte permettono di stimare il LTV in modo empirico, senza assunzioni arbitrarie.

**Metodo 1: LTV basato sulla curva di retention della coorte**

```
LTV = ARPU × Σ(retention_mese_n) per n = 0, 1, 2, ..., N

Dove:
- ARPU = Average Revenue Per User per mese
- retention_mese_n = % utenti ancora attivi al mese n

Esempio con ARPU = €50/mese:

Mese    Retention    Revenue atteso per utente originale
0       100%         €50.00
1        45%         €22.50
2        35%         €17.50
3        30%         €15.00
4        28%         €14.00
5        27%         €13.50
6        26%         €13.00
7        26%         €13.00
8        25%         €12.50
9        25%         €12.50
10       25%         €12.50
11       25%         €12.50
12       24%         €12.00
                     ────────
LTV 12 mesi         €208.00
```

**Metodo 2: LTV con retention che si stabilizza (formula chiusa)**

Se la retention si stabilizza a un plateau `p` dopo il mese `k`, la formula diventa:

```
LTV = ARPU × [Σ(retention_mese_n, n=0..k) + retention_mese_k / churn_rate_stabile]

Dove churn_rate_stabile = 1 - (retention_mese_{k+1} / retention_mese_k)

Esempio:
- ARPU = €50
- Retention si stabilizza al 26% dal mese 6
- Churn mensile stabile dopo M6 ≈ 3% (26% → 25.2% → 24.4%)

LTV = €50 × [somma retention M0..M5 + 0.26/0.03]
    = €50 × [1.00 + 0.45 + 0.35 + 0.30 + 0.28 + 0.27 + 8.67]
    = €50 × 11.32
    = €566
```

**SQL per calcolare il LTV empirico da coorte**:

```sql
-- LTV empirico per coorte basato su revenue reale
WITH customer_cohort AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(payment_date)) AS cohort_month
    FROM payments
    WHERE status = 'succeeded'
    GROUP BY customer_id
),
customer_lifetime_revenue AS (
    SELECT
        cc.customer_id,
        cc.cohort_month,
        SUM(p.amount) AS total_revenue,
        COUNT(DISTINCT DATE_TRUNC('month', p.payment_date)) AS months_active,
        MIN(p.payment_date) AS first_payment,
        MAX(p.payment_date) AS last_payment
    FROM customer_cohort cc
    JOIN payments p ON cc.customer_id = p.customer_id
    WHERE p.status = 'succeeded'
    GROUP BY 1, 2
)
SELECT
    TO_CHAR(cohort_month, 'Mon YYYY') AS coorte,
    COUNT(*) AS clienti,
    ROUND(AVG(total_revenue), 2) AS ltv_medio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_revenue), 2)
        AS ltv_mediano,
    ROUND(AVG(months_active), 1) AS mesi_attivi_medi,
    ROUND(AVG(total_revenue / GREATEST(months_active, 1)), 2) AS arpu_medio
FROM customer_lifetime_revenue
GROUP BY cohort_month
ORDER BY cohort_month;
```

**LTV per segmento — decisioni operative**:

```
Segmento       LTV medio    CAC     LTV:CAC    Payback     Azione
─────────────────────────────────────────────────────────────────────
Startup        €320         €180    1.8x       5.5 mesi    ⚠ Ridurre CAC o migliorare retention
SMB            €890         €350    2.5x       4.2 mesi    ✓ Sano, scalare
Mid-Market     €3,200       €1,200  2.7x       4.5 mesi    ✓ Sano, investire
Enterprise     €18,000      €5,000  3.6x       3.3 mesi    ✓ Eccellente, espandere team sales

Benchmark: LTV:CAC > 3x è eccellente, 2-3x è sano, < 2x è a rischio.
Payback < 12 mesi è lo standard per SaaS sani.
```

### Cohort Analysis Avanzata

Oltre alla retention cohort base, le analisi avanzate includono:

**Revenue Cohort Analysis**: tracciare non solo la retention degli utenti ma la retention e l'expansion della revenue per coorte.

```python
def revenue_cohort_analysis(subscriptions_df):
    """
    Calcolare la revenue per coorte nel tempo,
    includendo expansion e contraction.
    """
    # Determinare la coorte per ogni subscription
    first_payment = subscriptions_df.groupby('customer_id')[
        'payment_date'
    ].min().dt.to_period('M').rename('cohort')

    # Unire la coorte
    df = subscriptions_df.merge(first_payment, on='customer_id')
    df['payment_period'] = df['payment_date'].dt.to_period('M')
    df['period_number'] = (
        df['payment_period'] - df['cohort']
    ).apply(lambda x: x.n)

    # Calcolare la revenue per coorte e periodo
    revenue_cohort = df.groupby(
        ['cohort', 'period_number']
    )['amount'].sum().unstack()

    # Calcolare la retention della revenue (NRR per coorte)
    initial_revenue = revenue_cohort[0]
    nrr_cohort = revenue_cohort.divide(initial_revenue, axis=0) * 100

    return nrr_cohort
```

**Behavioral Cohort Analysis**: confrontare la retention di utenti raggruppati per comportamento, non per data di acquisizione.

```python
def behavioral_cohort_retention(events_df, behavior_event):
    """
    Confrontare la retention di utenti che hanno compiuto
    un comportamento specifico vs quelli che non l'hanno compiuto.
    """
    # Identificare gli utenti che hanno compiuto il comportamento
    behavior_users = events_df[
        events_df['event_type'] == behavior_event
    ]['user_id'].unique()

    # Classificare gli utenti
    events_df['has_behavior'] = events_df['user_id'].isin(behavior_users)

    # Calcolare la retention per entrambi i gruppi
    retention_with = calculate_retention(
        events_df[events_df['has_behavior'] == True]
    )
    retention_without = calculate_retention(
        events_df[events_df['has_behavior'] == False]
    )

    return {
        'with_behavior': retention_with,
        'without_behavior': retention_without,
        'lift': retention_with - retention_without
    }
```

### Visualizzazione delle Cohort

**Heatmap**: la visualizzazione più comune. Le righe sono le coorti, le colonne sono i periodi, i colori indicano la retention (verde = alta, rosso = bassa).

**Cohort Curve Plot**: sovrapporre le curve di retention di diverse coorti sullo stesso grafico. Permette di visualizzare se le coorti più recenti hanno retention migliore (indicatore di miglioramento del prodotto).

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_retention_heatmap(retention_df):
    """Visualizzare la retention come heatmap"""
    plt.figure(figsize=(14, 8))
    sns.heatmap(
        retention_df,
        annot=True,
        fmt='.0f',
        cmap='YlGn',
        vmin=0,
        vmax=100,
        linewidths=0.5,
    )
    plt.title('User Retention by Cohort (%)')
    plt.xlabel('Months Since Signup')
    plt.ylabel('Signup Cohort')
    plt.tight_layout()
    plt.savefig('retention_heatmap.png', dpi=150)
```

### Best Practice per la Visualizzazione delle Coorti

**1. Scegliere il tipo di grafico giusto**:

| Obiettivo | Grafico ideale |
|---|---|
| Confrontare tutte le coorti | Heatmap (tabella con colori) |
| Confrontare 3-5 coorti specifiche | Line chart sovrapposto |
| Mostrare il trend di una singola metrica nel tempo | Sparkline o barra |
| Revenue retention | Heatmap con scala divergente (rosso < 100% < verde) |
| Distribuzione engagement | Istogramma o box plot |

**2. Scala cromatica della heatmap**: usare una scala sequenziale (es. YlGn — giallo a verde) per la retention utenti. Per la revenue retention, usare una scala divergente centrata su 100% (rosso sotto, verde sopra). Mai usare rainbow — è inaccessibile e ambiguo.

**3. Annotare i numeri**: la heatmap deve mostrare i valori percentuali nelle celle, non solo i colori. Un manager che guarda la dashboard non deve dover interpretare sfumature di verde.

**4. Evidenziare le anomalie**: marcare con un bordo o un colore diverso le celle che deviano significativamente dalla media (es. > 2 deviazioni standard). Questo attira l'attenzione ai punti che richiedono indagine.

**5. Mostrare la dimensione della coorte**: includere una colonna con il numero assoluto di utenti nella coorte. Una retention del 90% su 10 utenti non ha lo stesso significato di una retention del 90% su 1,000 utenti.

**6. Confronto temporale**: affiancare la cohort table del trimestre corrente con quella del trimestre precedente per evidenziare miglioramenti o regressioni.

**7. Evitare errori comuni**:
- Non troncare l'asse Y partendo da un valore diverso da 0 nei line chart di retention — distorce la percezione
- Non mostrare coorti troppo giovani senza nota — una coorte con solo M0 e M1 può sembrare migliore semplicemente perché non ha avuto tempo di churnare
- Non mescolare granularità diverse (coorti mensili e settimanali) nello stesso grafico

---

## Funnel Optimization — Il Framework AARRR

### Le Cinque Fasi del Pirate Metrics

Il framework AARRR (Acquisition, Activation, Retention, Revenue, Referral), creato da Dave McClure, è il framework standard per l'analisi del funnel SaaS:

**Acquisition**: come gli utenti arrivano al prodotto.
- Metriche: visitatori unici, signup rate per canale, cost per visit
- Domanda chiave: "Da dove vengono i nostri utenti migliori?"

**Activation**: il primo momento di valore.
- Metriche: activation rate, time-to-value, onboarding completion rate
- Domanda chiave: "Gli utenti stanno raggiungendo il momento aha?"

**Retention**: gli utenti tornano e usano il prodotto regolarmente.
- Metriche: D1/D7/D30 retention, WAU/MAU, DAU/MAU ratio
- Domanda chiave: "Il prodotto crea un'abitudine?"

**Revenue**: gli utenti pagano.
- Metriche: free-to-paid conversion, ARPU, MRR, time-to-conversion
- Domanda chiave: "Stiamo catturando valore adeguato?"

**Referral**: gli utenti portano altri utenti.
- Metriche: viral coefficient, NPS, referral rate
- Domanda chiave: "I nostri utenti ci raccomandano?"

### Funnel Analysis Pratica

```
Visitatori            → 100,000 (100%)
    │
    │  Signup Rate: 5%
    ▼
Registrazioni         → 5,000 (5%)
    │
    │  Activation Rate: 30%
    ▼
Utenti Attivati       → 1,500 (1.5%)
    │
    │  Week 4 Retention: 45%
    ▼
Utenti Retained       → 675 (0.675%)
    │
    │  Conversion Rate: 15%
    ▼
Clienti Paganti       → 101 (0.101%)
    │
    │  Referral Rate: 20%
    ▼
Referral Generati     → 20
```

### Identificare il Collo di Bottiglia

Il collo di bottiglia è la fase del funnel con il maggior drop-off relativo rispetto ai benchmark:

```
Fase            Tuo Prodotto    Benchmark    Gap
Signup          5%              5%           OK
Activation      30%             35%          -5pp
Retention W4    45%             50%          -5pp
Conversion      15%             8%           +7pp ✓
Referral        20%             15%          +5pp ✓

Il collo di bottiglia è tra Activation e Retention.
Concentrare gli sforzi lì prima di ottimizzare altri stadi.
```

### Micro-Funnel per l'Onboarding

Oltre al macro-funnel AARRR, è utile costruire micro-funnel per le fasi critiche:

```
Onboarding Micro-Funnel:

1. Signup completato          → 5,000 (100%)
2. Email verificata           → 4,250 (85%)   Drop: 15%
3. Profilo completato         → 3,400 (68%)   Drop: 20%
4. Primo progetto creato      → 2,380 (47.6%) Drop: 30% ← BOTTLENECK
5. Primo collaboratore invitato → 1,666 (33.3%) Drop: 30%
6. Primo deliverable creato   → 1,166 (23.3%) Drop: 30%
7. ACTIVATION EVENT           → 1,500 (30%)
```

Lo step 4 (primo progetto creato) ha il maggior drop-off in termini assoluti: 3,400 utenti arrivano ma 1,020 abbandonano. Questo è il punto dove concentrare gli sforzi: semplificare la creazione del primo progetto, fornire template, guidare con un wizard.

### Ottimizzazione per Stadio del Funnel

Ogni stadio del funnel AARRR ha le proprie leve di ottimizzazione. Intervenire nello stadio sbagliato è il modo più rapido per sprecare risorse.

**Regola cardinale**: ottimizzare prima la retention, poi l'activation, poi l'acquisition. Acquisire più utenti in un prodotto con retention del 5% al M3 è buttare soldi nel secchio bucato.

#### Acquisition — Tattiche di Ottimizzazione

```
Leva                        Impatto atteso    Complessità
───────────────────────────────────────────────────────────
Landing page copy A/B        +10-30% signup    Bassa
Form di signup semplificato  +15-40% signup    Bassa
Social proof (loghi, numeri) +5-15% signup     Bassa
Demo video nel fold          +10-25% signup    Media
SEO content strategy         +50-200% traffic  Alta (tempo)
Paid ads ottimizzati         +20-50% CAC       Media
Referral program             +10-30% signups   Media
Product-led growth (freemium)+100%+ signups    Alta
```

**SQL per analizzare la qualità dell'acquisizione per canale**:

```sql
-- Quali canali portano utenti che si attivano e restano?
WITH signups AS (
    SELECT
        user_id,
        COALESCE(utm_source, 'direct') AS channel,
        created_at
    FROM users
    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
),
activation AS (
    SELECT DISTINCT user_id
    FROM events
    WHERE event_type = 'activation_event'
),
retained_m1 AS (
    SELECT DISTINCT e.user_id
    FROM events e
    JOIN signups s ON e.user_id = s.user_id
    WHERE e.event_timestamp >= s.created_at + INTERVAL '30 days'
        AND e.event_timestamp < s.created_at + INTERVAL '60 days'
)
SELECT
    s.channel,
    COUNT(DISTINCT s.user_id) AS signups,
    COUNT(DISTINCT a.user_id) AS activated,
    ROUND(COUNT(DISTINCT a.user_id) * 100.0 /
        NULLIF(COUNT(DISTINCT s.user_id), 0), 1) AS activation_rate,
    COUNT(DISTINCT r.user_id) AS retained_m1,
    ROUND(COUNT(DISTINCT r.user_id) * 100.0 /
        NULLIF(COUNT(DISTINCT s.user_id), 0), 1) AS retention_m1_rate
FROM signups s
LEFT JOIN activation a ON s.user_id = a.user_id
LEFT JOIN retained_m1 r ON s.user_id = r.user_id
GROUP BY s.channel
ORDER BY retention_m1_rate DESC;

-- Output tipico:
-- channel    signups  activated  activation_rate  retained_m1  retention_m1
-- referral     320      224        70.0%            160          50.0%
-- organic     1200      480        40.0%            420          35.0%
-- google_ads  2500      625        25.0%            500          20.0%
-- facebook     800      120        15.0%             80          10.0%
--
-- Insight: il referral ha 3.5x la retention di Facebook ads,
-- anche se genera meno volume. Investire nel referral program.
```

#### Activation — Tattiche di Ottimizzazione

```
Leva                         Impatto atteso     Complessità
────────────────────────────────────────────────────────────
Onboarding wizard guidato     +20-50% activation  Media
Template pre-configurati      +15-30% activation  Bassa
Ridurre passaggi obbligatori  +10-25% activation  Bassa
Email drip di onboarding      +5-15% activation   Media
In-app tooltip/coach marks    +10-20% activation  Media
Personalizzazione per ruolo   +15-30% activation  Alta
Checklist di progresso        +10-20% activation  Bassa
Gamification primi passi      +5-15% activation   Media
```

#### Retention — Tattiche di Ottimizzazione

```
Leva                         Impatto atteso     Complessità
────────────────────────────────────────────────────────────
Feature sticky (es. dati)     +10-30% retention  Alta
Notifiche contestuali         +5-15% retention   Media
Weekly digest email           +3-8% retention    Bassa
Team/collaborazione feature   +15-40% retention  Alta
Integrations ecosystem        +10-25% retention  Alta
Miglioramento performance     +5-10% retention   Media
Habit loops (trigger→azione)  +10-20% retention  Media
Customer success proattivo    +5-15% retention   Media
```

#### Revenue — Tattiche di Ottimizzazione

```
Leva                         Impatto atteso     Complessità
────────────────────────────────────────────────────────────
Trial → paid email sequence   +10-30% conversion Media
In-app upgrade prompt         +5-15% conversion  Bassa
Usage-based trigger           +10-25% conversion Media
Annual plan discount          +20-40% ACV        Bassa
Tiered pricing ottimizzato    +10-30% ARPU       Media
Add-on/expansion pricing      +15-40% NRR        Media
Seat-based growth             +10-25% NRR        Bassa
Enterprise plan               +50-200% ACV       Alta
```

#### Referral — Tattiche di Ottimizzazione

```
Leva                         Impatto atteso     Complessità
────────────────────────────────────────────────────────────
Double-sided referral bonus   +20-50% referral   Media
In-product sharing features   +10-30% referral   Media
NPS survey → prompt referral  +5-15% referral    Bassa
Case study/testimonial        +3-10% conversion  Bassa
Community building            +10-30% referral   Alta
API/ecosystem                 +5-20% referral    Alta
```

### Activation Metrics — Deep Dive

L'activation è lo stadio più critico e più spesso sottovalutato. Un utente "attivato" è un utente che ha sperimentato il valore core del prodotto per la prima volta — il cosiddetto "aha moment".

**Perché l'activation è così importante**: è il fulcro tra l'acquisizione (costosa) e la retention (dove si genera il valore). Un miglioramento del 10% nell'activation rate si propaga su TUTTA la base utenti futura.

**Come definire l'activation event**:

L'activation event NON è "ha completato la registrazione" e NON è "ha fatto il login". È l'azione che correla più fortemente con la retention a lungo termine.

**Processo per identificarlo**:

```
1. Elencare tutte le azioni compiute entro i primi 7 giorni
2. Per ogni azione, calcolare la retention a 30/60/90 giorni
   di chi l'ha compiuta vs chi non l'ha compiuta
3. L'azione con il lift maggiore è il candidato activation event
4. Validare con un A/B test se possibile (forzare vs non forzare
   l'azione nell'onboarding)
5. Definire la soglia: "X azione compiuta Y volte entro Z giorni"
```

**Esempi di activation event per settore**:

```
Prodotto               Activation Event                 Soglia
──────────────────────────────────────────────────────────────────
Slack                  Invio di 2,000 messaggi nel team  Entro 30g
Dropbox                Upload di almeno 1 file           Entro 1g
Zoom                   Prima call con 2+ partecipanti    Entro 7g
HubSpot CRM            Import di 10+ contatti            Entro 7g
Canva                  Creazione del primo design        Entro 3g
Notion                 Creazione di 3+ pagine            Entro 7g
Tool PM generico       Creazione progetto + 1 task       Entro 3g
```

**Metriche di activation da tracciare**:

```
Metrica                       Formula                    Target
──────────────────────────────────────────────────────────────────
Activation Rate               Utenti attivati / Signups  > 40%
Time-to-Activation            Tempo medio registrazione  < 24h (B2C)
                              → activation event         < 48h (B2B)
Onboarding Completion Rate    Utenti che finiscono /     > 70%
                              Utenti che iniziano
Aha Moment Reach Rate         Utenti che raggiungono     > 50%
                              l'aha moment / Signups
Setup Abandonment Rate        Utenti che abbandonano     < 30%
                              durante il setup
```

**SQL per tracciare l'activation funnel**:

```sql
-- Funnel di activation: dalla registrazione all'aha moment
WITH signup_cohort AS (
    SELECT
        user_id,
        created_at,
        DATE_TRUNC('week', created_at) AS signup_week
    FROM users
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
),
milestones AS (
    SELECT
        sc.user_id,
        sc.signup_week,
        -- Step 1: Email verificata
        MIN(CASE WHEN e.event_type = 'email_verified'
            THEN e.event_timestamp END) AS email_verified_at,
        -- Step 2: Profilo completato
        MIN(CASE WHEN e.event_type = 'profile_completed'
            THEN e.event_timestamp END) AS profile_completed_at,
        -- Step 3: Primo progetto creato
        MIN(CASE WHEN e.event_type = 'project_created'
            THEN e.event_timestamp END) AS first_project_at,
        -- Step 4: Primo collaboratore invitato
        MIN(CASE WHEN e.event_type = 'member_invited'
            THEN e.event_timestamp END) AS first_invite_at,
        -- Step 5: Activation event
        MIN(CASE WHEN e.event_type = 'activation_event'
            THEN e.event_timestamp END) AS activated_at
    FROM signup_cohort sc
    LEFT JOIN events e ON sc.user_id = e.user_id
    GROUP BY sc.user_id, sc.signup_week
)
SELECT
    TO_CHAR(signup_week, 'YYYY-"W"IW') AS settimana,
    COUNT(*) AS signups,
    COUNT(email_verified_at) AS email_verificata,
    ROUND(COUNT(email_verified_at) * 100.0 / COUNT(*), 1)
        AS pct_email,
    COUNT(profile_completed_at) AS profilo_completato,
    ROUND(COUNT(profile_completed_at) * 100.0 / COUNT(*), 1)
        AS pct_profilo,
    COUNT(first_project_at) AS primo_progetto,
    ROUND(COUNT(first_project_at) * 100.0 / COUNT(*), 1)
        AS pct_progetto,
    COUNT(first_invite_at) AS primo_invito,
    ROUND(COUNT(first_invite_at) * 100.0 / COUNT(*), 1)
        AS pct_invito,
    COUNT(activated_at) AS attivati,
    ROUND(COUNT(activated_at) * 100.0 / COUNT(*), 1)
        AS activation_rate,
    -- Tempo medio alla activation (in ore)
    ROUND(AVG(EXTRACT(EPOCH FROM (activated_at - sc.created_at))
        / 3600.0) FILTER (WHERE activated_at IS NOT NULL), 1)
        AS ore_medie_activation
FROM milestones m
JOIN signup_cohort sc ON m.user_id = sc.user_id
GROUP BY signup_week
ORDER BY signup_week;
```

### A/B Testing per Funnel

L'A/B testing applicato ai funnel ha dinamiche specifiche rispetto al test generico.

**Principio chiave**: testare uno stadio del funnel alla volta. Cambiare contemporaneamente il copy della landing page e il flusso di onboarding rende impossibile attribuire l'effetto.

**Prioritizzazione dei test nel funnel**:

```
Framework ICE per prioritizzare gli A/B test:

Test                          Impact  Confidence  Ease   Score
──────────────────────────────────────────────────────────────
CTA button copy               7       8          10      8.3
Onboarding wizard vs free     9       6           5      6.7
Pricing page layout           8       5           7      6.7
Email verification removal    6       7           9      7.3
Welcome email sequence        5       6           8      6.3
Trial duration 14g vs 30g     8       4           9      7.0

Nota: ICE Score = (Impact + Confidence + Ease) / 3
Iniziare dal test con score più alto.
```

**Framework per A/B test nel funnel di onboarding**:

```
Ipotesi: "Sostituire il form di setup a 5 campi con un wizard
         a 3 step aumenterà l'onboarding completion rate del 20%"

Variante A (Control):
  - Form unico con 5 campi obbligatori
  - Completion rate attuale: 68%

Variante B (Treatment):
  - Wizard a 3 step progressivi (2 campi, 2 campi, 1 campo)
  - Step 1: nome + email
  - Step 2: azienda + ruolo
  - Step 3: caso d'uso (opzionale)

Metriche:
  - Primaria: onboarding completion rate
  - Secondaria: activation rate (per assicurarsi che completare
    il wizard porti anche all'attivazione)
  - Guardrail: time-to-complete (non deve aumentare > 30%)

Attenzione alla metrica secondaria:
  - Se il wizard aumenta il completion rate ma NON l'activation rate,
    probabilmente stiamo solo facilitando il passaggio senza
    aggiungere valore. In quel caso, il wizard è cosmetico.
```

**Come testare cambiamenti nel conversion funnel (free → paid)**:

```
Test: Trial di 14 giorni vs 7 giorni

Ipotesi: un trial più breve crea urgenza e aumenta la conversione

Metriche da tracciare:
1. Trial-to-paid conversion rate (primaria)
2. Revenue per trial started (per catturare il valore totale)
3. Activation rate durante il trial
4. Churn rate post-conversione a 90 giorni (CRITICA)

Perché la metrica 4 è critica:
Un trial di 7 giorni potrebbe convertire di più ma generare
utenti "forzati" che churnano rapidamente. L'analisi deve
estendersi almeno a 90 giorni post-conversione per evitare
di ottimizzare per revenue di breve periodo a scapito del LTV.
```

### Significatività Statistica nei Funnel

I funnel hanno sfide statistiche specifiche che richiedono attenzione.

**Problema del campione piccolo nelle fasi avanzate del funnel**:

```
Stage            Utenti     Conversione    Sample per A/B (MDE 10%)
─────────────────────────────────────────────────────────────────────
Visitatori       100,000    —              —
Signup            5,000     5%             ~31,000 per variante
Attivazione       1,500     30%            ~3,800 per variante
Retention M1        675     45%            ~4,100 per variante
Conversione         101     15%            ~14,000 per variante ⚠

⚠ Per testare la conversione (15% rate su 675 utenti),
servono ~14,000 utenti per variante — ma ne arrivano solo 675/mese.
Tempo necessario: ~41 mesi per un singolo test. IMPRATICABILE.
```

**Soluzioni**:
1. **Accettare MDE più grande**: se accettiamo di rilevare solo effetti > 30% (invece di 10%), il sample size scende a ~1,800 per variante (~5 mesi).
2. **Usare proxy metrics**: invece di testare la conversione finale, testare un proxy più upstream nel funnel dove c'è più volume (es. "click sul bottone pricing" invece di "pagamento completato").
3. **Bayesian A/B testing**: approccio bayesiano che fornisce probabilità continue invece di un binary significativo/non significativo. Permette decisioni con campioni più piccoli, accettando un livello di incertezza esplicito.

**Calcolo rapido della significatività** (pseudocodice):

```python
def is_significant(visitors_a, conversions_a, visitors_b, conversions_b,
                   alpha=0.05):
    """
    Test z a due code per confrontare due proporzioni.
    Restituisce (is_significant, p_value, lift_pct, confidence_interval).
    """
    import math
    from scipy.stats import norm

    p_a = conversions_a / visitors_a
    p_b = conversions_b / visitors_b
    p_pool = (conversions_a + conversions_b) / (visitors_a + visitors_b)

    se = math.sqrt(p_pool * (1 - p_pool) * (1/visitors_a + 1/visitors_b))

    if se == 0:
        return False, 1.0, 0.0, (0.0, 0.0)

    z = (p_b - p_a) / se
    p_value = 2 * (1 - norm.cdf(abs(z)))

    lift = (p_b - p_a) / p_a * 100

    # Intervallo di confidenza al 95% sul lift
    se_diff = math.sqrt(p_a*(1-p_a)/visitors_a + p_b*(1-p_b)/visitors_b)
    ci_lower = ((p_b - p_a) - 1.96 * se_diff) / p_a * 100
    ci_upper = ((p_b - p_a) + 1.96 * se_diff) / p_a * 100

    return p_value < alpha, round(p_value, 4), round(lift, 1), (
        round(ci_lower, 1), round(ci_upper, 1)
    )

# Esempio:
# A: 5000 visitatori, 250 conversioni (5.0%)
# B: 5000 visitatori, 290 conversioni (5.8%)
result = is_significant(5000, 250, 5000, 290)
# → (False, 0.0892, 16.0, (-2.4, 34.4))
# Non significativo — servono più dati o l'effetto è troppo piccolo
```

**Quando NON fare A/B test nel funnel**:

```
Situazione                        Alternativa
──────────────────────────────────────────────────────────
Volume < 1,000 conversioni/mese  Analisi qualitativa (interviste, sessioni)
Effetto atteso > 50%             Lancio diretto + monitoraggio
Cambiamento irreversibile        Test pilota su segmento ristretto
Cambio di pricing                Price testing su coorti separate
Bug fix ovvio                    Fix immediato, nessun test necessario
```

---

## Event Tracking Design

### Principi di Design

Un sistema di event tracking ben progettato è il fondamento di tutte le analytics. I principi chiave sono:

**Naming Convention consistente**: adottare una convenzione e rispettarla rigorosamente. La convenzione più comune per SaaS è `Object Action`:

```
# Buono: Object_Action
Project Created
Project Updated
Project Deleted
Invoice Sent
Subscription Started
Subscription Cancelled
User Invited
User Removed

# Cattivo: inconsistente, ambiguo
create_project
projectCreated
new project
made_a_project
```

**Proprietà standard**: ogni evento dovrebbe includere un set standard di proprietà:

```json
{
  "event": "Project Created",
  "timestamp": "2024-03-15T10:30:00Z",
  "user_id": "user_123",
  "properties": {
    "project_id": "proj_456",
    "project_name": "Q1 Marketing Campaign",
    "project_type": "marketing",
    "template_used": true,
    "template_name": "Marketing Plan",
    "collaborators_count": 3
  },
  "context": {
    "plan": "pro",
    "team_size": 12,
    "days_since_signup": 15,
    "session_id": "sess_789",
    "device_type": "desktop",
    "browser": "Chrome",
    "os": "macOS"
  }
}
```

### Tracking Plan

Un tracking plan è il documento che definisce tutti gli eventi tracciati, le loro proprietà, e dove vengono inviati:

```markdown
## Tracking Plan — [Product Name]

### Event: User Signed Up
Trigger: completamento del form di registrazione
Properties:
- signup_method: string (email, google, github)
- referral_source: string (organic, paid, referral, direct)
- utm_source: string
- utm_medium: string
- utm_campaign: string
Destinations: Segment → Amplitude, Mixpanel, HubSpot

### Event: Activation Event Completed
Trigger: l'utente raggiunge l'activation event definito
Properties:
- days_since_signup: integer
- actions_taken: integer
- features_used: array[string]
Destinations: Segment → Amplitude, Mixpanel, Customer.io

### Event: Subscription Started
Trigger: primo pagamento confermato
Properties:
- plan: string (starter, pro, enterprise)
- billing_period: string (monthly, annual)
- mrr: number
- trial_converted: boolean
- days_in_trial: integer
Destinations: Segment → Amplitude, Mixpanel, Stripe, HubSpot
```

### Implementazione con Segment

```javascript
// Frontend: tracking degli eventi con Segment analytics.js
// Registrazione
analytics.track('User Signed Up', {
  signup_method: 'google',
  referral_source: 'organic',
});

// Creazione progetto
analytics.track('Project Created', {
  project_id: 'proj_456',
  project_type: 'marketing',
  template_used: true,
  template_name: 'Marketing Plan',
  collaborators_count: 3,
});

// Identificare l'utente con i suoi attributi
analytics.identify('user_123', {
  email: 'mario@example.com',
  name: 'Mario Rossi',
  plan: 'pro',
  company: 'Acme Corp',
  company_size: 50,
  created_at: '2024-01-15',
});
```

```python
# Backend: tracking con Segment Python SDK
import analytics

analytics.write_key = os.environ['SEGMENT_WRITE_KEY']

# Evento server-side (es. subscription creata via webhook Stripe)
analytics.track(
    user_id='user_123',
    event='Subscription Started',
    properties={
        'plan': 'pro',
        'billing_period': 'monthly',
        'mrr': 99,
        'trial_converted': True,
        'days_in_trial': 14,
    }
)
```

---

## A/B Testing — Fondamenti Statistici

### Principi Statistici

L'A/B testing è il metodo gold standard per valutare l'impatto di un cambiamento. Tuttavia, la maggior parte degli A/B test nel mondo SaaS è condotta con errori metodologici che invalidano i risultati.

**Hypothesis-driven testing**: ogni test deve partire da un'ipotesi chiara:
```
Ipotesi: Cambiando il CTA da "Registrati" a "Inizia gratis"
         aumenterà il signup rate del 15%

Metrica primaria: signup rate (visitatori → registrazioni)
Metrica secondaria: activation rate (per verificare la qualità)
```

**Dimensione del campione**: il calcolo della dimensione minima del campione è necessario per risultati statisticamente significativi:

```python
from scipy.stats import norm
import math

def calculate_sample_size(
    baseline_rate: float,    # Tasso attuale (es. 0.05 per 5%)
    minimum_effect: float,   # Effetto minimo da rilevare (es. 0.15 per 15% lift)
    alpha: float = 0.05,     # Livello di significatività (5%)
    power: float = 0.80      # Potenza statistica (80%)
) -> int:
    """Calcolare la dimensione del campione necessaria per un A/B test"""

    p1 = baseline_rate
    p2 = baseline_rate * (1 + minimum_effect)
    p_avg = (p1 + p2) / 2

    z_alpha = norm.ppf(1 - alpha / 2)  # Two-sided test
    z_beta = norm.ppf(power)

    n = (
        (z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) +
         z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    ) / (p2 - p1) ** 2

    return math.ceil(n)  # Per variante


# Esempio: tasso attuale 5%, voglio rilevare un 15% di lift (→ 5.75%)
sample_size = calculate_sample_size(0.05, 0.15)
# Risultato: ~22,000 per variante (44,000 totali)
```

**Durata del test**: non terminare un test quando il risultato "diventa significativo". Definire la durata prima di iniziare e rispettarla:

```
Durata minima = Sample Size / (Traffico giornaliero / Numero varianti)

Esempio:
- Sample size necessario: 22,000 per variante
- Traffico giornaliero: 1,000 visitatori
- 2 varianti (A e B)
- Durata = 22,000 / (1,000 / 2) = 44 giorni
```

### Errori Comuni negli A/B Test

1. **Peeking problem**: controllare i risultati durante il test e terminarlo prematuramente quando sembra significativo. Questo aumenta drasticamente il tasso di falsi positivi. Soluzione: pre-definire la durata e non guardare i risultati intermedi (oppure usare sequential testing methods).

2. **Multiple comparisons**: testare molte varianti o metriche contemporaneamente senza correzione per le comparazioni multiple. Soluzione: usare la correzione di Bonferroni o definire una singola metrica primaria.

3. **Simpson's Paradox**: un trend che appare in diversi segmenti scompare o si inverte quando i dati sono aggregati. Soluzione: analizzare i risultati per segmento oltre che in aggregato.

4. **Under-powered tests**: test con campione insufficiente. Un test non significativo non significa che non c'è effetto — potrebbe significare che il campione è troppo piccolo. Soluzione: calcolare il sample size prima di iniziare.

### Framework per A/B Testing nel SaaS

```markdown
## A/B Test Brief Template

### Metadata
- Test Name: CTA_Signup_Button_Copy_v2
- Hypothesis: Cambiando il CTA da "Registrati" a "Inizia gratis"
              il signup rate aumenterà del 15%
- Owner: [Nome]
- Start Date: [Data]
- Planned Duration: 44 giorni

### Design
- Variante A (Control): "Registrati" button
- Variante B (Treatment): "Inizia gratis" button
- Traffic Split: 50/50
- Randomization Unit: visitor_id (cookie-based)
- Target Population: tutti i visitatori della homepage

### Metrics
- Primary: signup rate (visitatori unici → registrazioni completate)
- Secondary: activation rate (per verificare qualità utenti)
- Guardrail: page load time (non deve degradare)

### Statistical Plan
- Test type: two-sided z-test for proportions
- Significance level (α): 0.05
- Power (1-β): 0.80
- Minimum detectable effect: 15% relative lift
- Required sample size: ~22,000 per variante
- Estimated duration: 44 giorni

### Decision Rules
- If p < 0.05 AND lift > 10%: launch Treatment
- If p > 0.05: no change, consider larger test
- If secondary metric degrades > 5%: do not launch
```

---

## Dashboard Design per SaaS

### Dashboard Hierarchy

Un sistema di dashboard efficace ha una struttura gerarchica:

**Level 1 — Executive Dashboard (weekly)**:
```
┌─────────────────────────────────────────────────┐
│  MRR: $92,000 (+8% M/M)    ARR: $1.1M          │
│  New Customers: 142         Churn: 12 (2.3%)    │
│  NRR: 110%                  Gross Margin: 75%   │
│                                                   │
│  [MRR Trend Chart - 12 months]                   │
│  [Customer Count Trend]                           │
│  [Cash Burn and Runway]                           │
└─────────────────────────────────────────────────┘
```

**Level 2 — Functional Dashboards (daily)**:
- Product: activation, engagement, feature adoption, retention
- Marketing: traffic, signups, CAC per canale, pipeline
- Sales: pipeline, win rate, ACV, deal velocity
- CS: NPS, churn risk, expansion opportunities
- Finance: cash flow, runway, unit economics

**Level 3 — Deep Dive Dashboards (on-demand)**:
- Cohort retention heatmap
- Funnel analysis dettagliato
- A/B test results
- Revenue breakdown per segmento
- Feature usage analytics

### Principi di Design

**1. Start with the question, not the data**: ogni visualizzazione deve rispondere a una domanda specifica. "Come sta andando la crescita?" → MRR trend. "Stiamo migliorando il prodotto?" → Retention per coorte recente vs precedente.

**2. One metric, one chart**: evitare di sovraccaricare un singolo grafico con troppe informazioni. Un grafico per metrica, con contesto (trend, benchmark, target).

**3. Context over numbers**: un numero senza contesto è inutile. "$92,000 MRR" è un dato. "$92,000 MRR (+8% M/M, target: +10%)" è informazione actionable.

**4. Real-time dove serve, periodic dove basta**: non tutto deve essere real-time. Il MRR è un dato mensile — aggiornarlo in real-time è spreco di risorse. Le signup sono un dato che beneficia di monitoring più frequente.

---

## Data Stack Moderno — Segment, Amplitude, Mixpanel

### Customer Data Platform (CDP): Segment

Segment è il CDP più utilizzato dalle aziende SaaS. Funziona come un "router" per i dati: raccoglie gli eventi da tutte le sorgenti (web, mobile, server) e li distribuisce a tutte le destinazioni (analytics, CRM, marketing automation, data warehouse).

```
Sorgenti                  Segment              Destinazioni
┌──────────┐             ┌──────┐             ┌──────────────┐
│ Web App  │────────────>│      │────────────>│ Amplitude    │
│ (JS SDK) │             │      │             │ (Analytics)  │
├──────────┤             │      │             ├──────────────┤
│ Mobile   │────────────>│  CDP │────────────>│ Mixpanel     │
│ (iOS/And)│             │      │             │ (Analytics)  │
├──────────┤             │      │             ├──────────────┤
│ Backend  │────────────>│      │────────────>│ Customer.io  │
│ (Python) │             │      │             │ (Email)      │
├──────────┤             │      │             ├──────────────┤
│ Stripe   │────────────>│      │────────────>│ HubSpot CRM  │
│(Webhooks)│             │      │             ├──────────────┤
└──────────┘             │      │────────────>│ BigQuery     │
                         │      │             │ (Warehouse)  │
                         └──────┘             └──────────────┘
```

**Vantaggi di Segment**: un singolo SDK da integrare. Aggiungere/rimuovere destinazioni senza cambiare il codice. Trasformazioni e filtri nel mezzo. Privacy controls centralizzati.

**Alternative open-source**: RudderStack, Jitsu. Offrono funzionalità simili con hosting self-managed e costi potenzialmente inferiori.

### Product Analytics: Amplitude vs Mixpanel vs PostHog

| Feature | Amplitude | Mixpanel | PostHog |
|---|---|---|---|
| Pricing | Free fino a 10M events | Free fino a 20M events | Free self-hosted, cloud paid |
| Strengths | Behavioral cohorts, funnels, retention | Funnels, flows, impact analysis | Open-source, session replay |
| Hosting | Cloud only | Cloud only | Self-hosted o cloud |
| Integrations | Eccellente | Buono | Buono |
| Learning curve | Media | Bassa | Media |
| Best for | Scale-up/Enterprise | Startup/Growth | Privacy-conscious, engineering teams |

### Scelta Raccomandata per Fase

**Pre-PMF (0-$100K ARR)**: PostHog self-hosted (gratuito) o Mixpanel free tier. Focus su retention e activation. Non servono strumenti complessi.

**Growth ($100K-$1M ARR)**: Segment + Amplitude o Mixpanel. Investire in un CDP per centralizzare i dati. Iniziare la pipeline verso il data warehouse.

**Scale ($1M+ ARR)**: Segment + Amplitude + Data Warehouse (BigQuery/Snowflake) + dbt per data transformation. Analytics team dedicato.

---

## Data Warehouse e Analytics Engineering

### Architettura del Data Stack Moderno

```
Sources          Ingestion       Warehouse       Transformation    Visualization
┌─────────┐     ┌──────────┐   ┌──────────┐    ┌──────────┐     ┌──────────┐
│ Segment  │────>│          │   │          │    │          │     │          │
│ Stripe   │────>│  Fivetran│──>│ BigQuery │──> │   dbt    │────>│  Metabase│
│ HubSpot  │────>│  / Airbyte│  │ Snowflake│   │          │     │  Looker  │
│ Postgres │────>│          │   │          │    │          │     │  Mode    │
└─────────┘     └──────────┘   └──────────┘    └──────────┘     └──────────┘
```

**Data Ingestion**: Fivetran (managed, costoso) o Airbyte (open-source) per sincronizzare dati da tutte le sorgenti nel warehouse.

**Data Warehouse**: BigQuery (Google, serverless, economico per query ad-hoc) o Snowflake (premium, separazione compute/storage) o Redshift (AWS, integrato con l'ecosistema AWS).

**Transformation**: dbt (data build tool) è lo standard per trasformare i dati raw nel warehouse in modelli analitici puliti e documentati.

**Visualization**: Metabase (open-source, semplice), Looker (enterprise, governance), Mode (SQL-first), Preset (managed Superset).

### dbt per SaaS Analytics

```sql
-- models/marts/core/fct_mrr.sql
-- Calcolo del MRR per mese e cliente usando dbt

WITH subscriptions AS (
    SELECT * FROM {{ ref('stg_stripe_subscriptions') }}
),

monthly_mrr AS (
    SELECT
        DATE_TRUNC('month', billing_period_start) AS month,
        customer_id,
        plan_name,
        SUM(amount / 100.0) AS mrr  -- Stripe amounts in cents
    FROM subscriptions
    WHERE status IN ('active', 'trialing')
    GROUP BY 1, 2, 3
),

mrr_with_changes AS (
    SELECT
        month,
        customer_id,
        plan_name,
        mrr,
        LAG(mrr) OVER (
            PARTITION BY customer_id ORDER BY month
        ) AS previous_mrr,
        CASE
            WHEN LAG(mrr) OVER (PARTITION BY customer_id ORDER BY month) IS NULL
                THEN 'new'
            WHEN mrr > LAG(mrr) OVER (PARTITION BY customer_id ORDER BY month)
                THEN 'expansion'
            WHEN mrr < LAG(mrr) OVER (PARTITION BY customer_id ORDER BY month)
                THEN 'contraction'
            ELSE 'retained'
        END AS mrr_change_type
    FROM monthly_mrr
)

SELECT * FROM mrr_with_changes
```

---

## Product Analytics Avanzate

### Feature Adoption Tracking

```python
def analyze_feature_adoption(events_df, features_list):
    """
    Analizzare l'adozione di ogni feature e correlare
    con la retention.
    """
    results = {}

    for feature in features_list:
        # Utenti che hanno usato la feature
        feature_users = events_df[
            events_df['feature'] == feature
        ]['user_id'].unique()

        total_users = events_df['user_id'].nunique()
        adoption_rate = len(feature_users) / total_users

        # Retention degli utenti che usano la feature vs non
        retention_with = calculate_30d_retention(feature_users)
        retention_without = calculate_30d_retention(
            set(events_df['user_id'].unique()) - set(feature_users)
        )

        results[feature] = {
            'adoption_rate': adoption_rate,
            'retention_with': retention_with,
            'retention_without': retention_without,
            'retention_lift': retention_with - retention_without,
        }

    return sorted(
        results.items(),
        key=lambda x: x[1]['retention_lift'],
        reverse=True
    )
```

### Churn Prediction

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

def build_churn_prediction_model(user_features_df):
    """
    Costruire un modello predittivo per il churn.
    Features: engagement metrics degli ultimi 30 giorni.
    Target: churn nei prossimi 30 giorni.
    """
    features = [
        'days_active_last_30',
        'sessions_last_30',
        'features_used_last_30',
        'actions_per_session',
        'days_since_last_login',
        'support_tickets_last_30',
        'plan_tier',
        'team_size',
        'days_since_signup',
    ]

    X = user_features_df[features]
    y = user_features_df['churned_next_30_days']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
    )
    model.fit(X_train, y_train)

    # Feature importance
    importance = dict(zip(features, model.feature_importances_))

    return model, importance
```

---

## Privacy-Compliant Analytics

### Analytics senza Cookie di Terze Parti

Con la progressiva eliminazione dei cookie di terze parti e il GDPR, l'analytics deve adattarsi:

**First-party data only**: raccogliere dati solo attraverso il proprio dominio. Eliminare tracker di terze parti dove possibile.

**Server-side tracking**: spostare il tracking dal client al server per evitare ad-blocker e limitazioni dei browser.

**Privacy-first analytics**: strumenti come Plausible, Fathom, e Umami offrono analytics senza cookie, senza tracking personale, e compliance GDPR nativa.

**Consent-based tracking**: implementare il tracking avanzato (Amplitude, Mixpanel) solo per gli utenti che hanno dato il consenso esplicito.

---

## Best Practices

1. **Definire il tracking plan prima di implementare**: documentare ogni evento, le sue proprietà, e le sue destinazioni prima di scrivere una riga di codice.
2. **Naming convention consistente**: adottare una convenzione (Object Action) e rispettarla rigorosamente. Le inconsistenze nel naming rendono l'analisi impossibile.
3. **Event properties ricche**: includere contesto sufficiente in ogni evento per permettere segmentazione senza join complessi.
4. **Separare tracking e analytics**: il tracking raccoglie i dati, l'analytics li interpreta. Non mescolare i due — usare un CDP come layer intermedio.
5. **Cohort analysis è la metrica regina**: la retention per coorte è la singola analisi più informativa per un prodotto SaaS.
6. **A/B test con rigore statistico**: calcolare il sample size prima di iniziare, non peeking, durata pre-definita.
7. **Dashboards actionable**: ogni dashboard deve portare a una decisione. Se nessuno guarda la dashboard o nessuna decisione ne deriva, eliminarla.
8. **Data quality è non-negoziabile**: un singolo bug nel tracking può invalidare mesi di dati. Implementare test automatici per verificare la qualità dei dati.
9. **Iniziare semplice, evolvere progressivamente**: nella fase pre-PMF, un foglio di calcolo con le metriche chiave aggiornato settimanalmente è sufficiente.
10. **Privacy by design**: implementare il consent management fin dal primo giorno. Raccogliere solo i dati necessari.

---

## Troubleshooting

### Problema: Discrepanza tra le Metriche in Diversi Strumenti

**Diagnosi**: Amplitude mostra 10,000 utenti attivi, il database ne mostra 8,500, Google Analytics ne mostra 12,000. Cause comuni: definizioni diverse di "utente attivo", timezone diverse, filtri diversi (bot, internal traffic), deduplication diversa.

**Soluzione**: definire una "source of truth" per ogni metrica. Documentare la definizione esatta (inclusa la query SQL o la configurazione del tool). Riconciliare regolarmente i numeri tra i sistemi. Accettare piccole discrepanze (< 5%) come fisiologiche.

### Problema: Volume di Eventi Troppo Alto e Costoso

**Diagnosi**: il tracking è troppo granulare e genera milioni di eventi, con costi elevati per CDP e analytics tools.

**Soluzione**: eliminare gli eventi non utilizzati nell'analisi. Ridurre la granularità dove possibile (tracciare "Page Viewed" con la pagina come proprietà, non un evento diverso per ogni pagina). Utilizzare sampling per analytics non critiche. Implementare server-side tracking con pre-aggregazione.

### Problema: Nessuno nel Team Guarda le Dashboard

**Diagnosi**: le dashboard sono troppo complesse, mostrano metriche non rilevanti, o non sono integrate nel workflow decisionale.

**Soluzione**: semplificare radicalmente. Una dashboard con 5 metriche guardate ogni giorno è infinitamente più utile di una con 50 metriche ignorate. Integrare le metriche nel workflow: weekly business review con la dashboard, alert automatici per anomalie, Slack bot che posta le metriche giornaliere.

---

## Riferimenti

- "Lean Analytics" — Alistair Croll & Benjamin Yoskovitz — Framework per metriche per fase
- Dave McClure, "AARRR! Pirate Metrics" — Framework originale del funnel
- Amplitude, "Product Analytics Playbook" — Guida completa
- Mixpanel, "The Guide to Product Metrics" — Metriche di prodotto
- Segment, "The Segment Protocol" — Best practice per event tracking
- dbt Documentation — https://docs.getdbt.com — Analytics engineering
- "Trustworthy Online Controlled Experiments" — Kohavi, Tang, Xu — Bibbia degli A/B test
- PostHog Blog — Analytics open-source e privacy
- "Statistics Done Wrong" — Alex Reinhart — Errori statistici comuni
- Reforge, "Retention" — Deep dive sulla retention analysis
- Lenny Rachitsky, "Measuring Product Health" — Metriche di salute del prodotto
- Towards Data Science — Tutorial su cohort analysis con Python
