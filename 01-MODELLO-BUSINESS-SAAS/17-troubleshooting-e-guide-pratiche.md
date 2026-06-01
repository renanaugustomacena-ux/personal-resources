# Troubleshooting e Guide Pratiche SaaS — Guida Completa

## Indice

- [Panoramica](#panoramica)
- [Diagnostica dei Problemi SaaS](#diagnostica-dei-problemi-saas)
- [Lancio di un SaaS — Checklist Completa](#lancio-di-un-saas--checklist-completa)
- [Troubleshooting Lancio — Scenari Dettagliati](#troubleshooting-lancio--scenari-dettagliati)
- [Pricing Review — Processo Pratico](#pricing-review--processo-pratico)
- [Audit delle Metriche SaaS](#audit-delle-metriche-saas)
- [Incident Management](#incident-management)
- [Post-Mortem — Template e Processo](#post-mortem--template-e-processo)
- [Runbook Operativi](#runbook-operativi)
- [Performance Debugging](#performance-debugging)
- [Problemi di Scaling](#problemi-di-scaling)
- [Problemi di Billing e Dunning](#problemi-di-billing-e-dunning)
- [Workflow di Escalation Clienti](#workflow-di-escalation-clienti)
- [Pattern dei Ticket di Supporto](#pattern-dei-ticket-di-supporto)
- [Crisi e Recovery](#crisi-e-recovery)
- [Anti-Pattern Operativi](#anti-pattern-operativi)
- [Case Study Reali](#case-study-reali)
- [Template e Strumenti Operativi](#template-e-strumenti-operativi)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Esercizi Pratici](#esercizi-pratici)
- [Riferimenti e Risorse](#riferimenti-e-risorse)

---

## Panoramica

Questa guida raccoglie i problemi più comuni che un SaaS affronta nel suo ciclo di vita, con diagnosi strutturate e azioni concrete. Include anche checklist operative per i momenti chiave (lancio, pricing review, fundraising prep) e template riutilizzabili per le attività quotidiane.

La guida è organizzata per coprire l'intero spettro operativo:

| Area | Cosa trovi |
|------|-----------|
| Diagnostica | Alberi decisionali per identificare la causa root dei problemi |
| Lancio | Checklist pre/post lancio e troubleshooting degli scenari comuni |
| Incident Management | Severità, comunicazione, war room, on-call |
| Post-Mortem | Template blameless, analisi root cause, action item tracking |
| Runbook | Procedure operative step-by-step per deployment, scaling, emergenze DB |
| Performance | Debug di latenza, query lente, profiling applicativo |
| Scaling | Colli di bottiglia, caching, sharding, code horizontale |
| Billing | Pagamenti falliti, dunning, refund, dispute |
| Escalation | Matrice di escalation, SLA, workflow tier-based |
| Supporto | Triage ticket, pattern comuni, template di risposta |
| Anti-Pattern | Errori operativi ricorrenti e come evitarli |
| Case Study | Scenari reali con diagnosi e risoluzione |

---

## Diagnostica dei Problemi SaaS

### Albero Decisionale — "La Crescita è Rallentata"

```
LA CRESCITA È RALLENTATA
│
├── Il traffico/lead è calato?
│   ├── SÌ → Problema di AWARENESS/ACQUISITION
│   │   ├── SEO: ranking calati? (algoritmo update, competitor)
│   │   ├── Paid: CPC aumentato? Budget ridotto?
│   │   ├── Content: frequenza calata? Qualità calata?
│   │   └── Azione: audit per canale, riallocare budget
│   │
│   └── NO → Il traffico è stabile, il problema è altrove ↓
│
├── Il signup rate è calato?
│   ├── SÌ → Problema di CONVERSIONE LANDING PAGE
│   │   ├── Landing page modificata di recente?
│   │   ├── Competitor con offerta aggressiva?
│   │   ├── Messaging non più rilevante?
│   │   └── Azione: A/B test landing page, competitor analysis
│   │
│   └── NO → Signup stabile, il problema è altrove ↓
│
├── L'activation rate è calato?
│   ├── SÌ → Problema di ONBOARDING
│   │   ├── Onboarding modificato di recente?
│   │   ├── Bug nel flow di onboarding?
│   │   ├── Target cambiato (lead meno qualificati)?
│   │   └── Azione: session recording, funnel analysis, fix bug
│   │
│   └── NO → Activation stabile, il problema è altrove ↓
│
├── Il trial-to-paid è calato?
│   ├── SÌ → Problema di MONETIZZAZIONE
│   │   ├── Pricing cambiato?
│   │   ├── Competitor più economico?
│   │   ├── Feature premium insufficienti?
│   │   └── Azione: pricing analysis, feature gap analysis
│   │
│   └── NO → Conversione stabile ↓
│
└── Il CHURN è aumentato?
    ├── SÌ → Problema di RETENTION
    │   ├── Churn volontario (detrattori)? → CS, prodotto
    │   ├── Churn involontario (pagamenti)? → Dunning
    │   ├── Bug/downtime recente? → Incident review
    │   ├── Competitor aggressivo? → Competitive intel
    │   └── Azione: exit survey, cohort analysis, health score
    │
    └── NO → Il problema potrebbe essere di mix
        → Le cohort recenti sono peggiori?
        → L'ACV medio sta calando?
        → L'expansion revenue è diminuita?
```

### Diagnostica "Il CAC è Troppo Alto"

```
CAC TROPPO ALTO
│
├── Il costo per lead è alto?
│   ├── SÌ → Canali costosi o targeting sbagliato
│   │   → Riallocare verso canali organici (SEO, community, referral)
│   │   → Migliorare targeting paid (ICP più preciso)
│   │   → Testare nuovi canali a basso costo
│   │
│   └── NO → Il costo per lead è ok, il problema è la conversione ↓
│
├── Il lead-to-trial rate è basso?
│   ├── SÌ → Lead non qualificati o funnel di conversione debole
│   │   → Migliorare il lead scoring
│   │   → Ottimizzare la landing page / signup flow
│   │   → Qualificare meglio in entrata (ICP fit)
│   │
│   └── NO ↓
│
└── Il trial-to-paid rate è basso?
    ├── SÌ → Problema di onboarding o pricing
    │   → Rivedere l'onboarding
    │   → Analizzare perché non convertono (exit survey)
    │   → Testare pricing / packaging diversi
    │
    └── NO → Il CAC è alto per overhead (team troppo grande?)
        → Calcolare il CAC fully loaded
        → Confrontare headcount sales/marketing vs new MRR
        → Ottimizzare l'efficienza del team
```

### Albero Decisionale — "Problemi di Infrastruttura"

```
L'APPLICAZIONE È LENTA O DOWN
│
├── È un outage totale? (status: 5xx o irraggiungibile)
│   ├── SÌ → OUTAGE CRITICO
│   │   ├── DNS resolve correttamente? → Controlla registrar e nameserver
│   │   ├── Load balancer risponde? → Controlla health check target
│   │   ├── Nessuna istanza healthy? → Controlla deploy recente o OOM
│   │   ├── Database raggiungibile? → Controlla connessioni, disk, replication
│   │   └── Azione: attivare incident P1, rollback deploy se recente
│   │
│   └── NO → Degradazione parziale ↓
│
├── Latenza elevata? (p95 > 2x baseline)
│   ├── SÌ → PERFORMANCE DEGRADATION
│   │   ├── Query lente nel DB? → Controlla slow query log
│   │   ├── CPU/memory alta sulle istanze? → Controlla autoscaling
│   │   ├── Servizio esterno lento? → Controlla dipendenze (API, CDN)
│   │   ├── Traffico anomalo? → Controlla per DDoS o bot
│   │   └── Azione: identifica il collo di bottiglia, scala o ottimizza
│   │
│   └── NO → Latenza normale ↓
│
├── Errori intermittenti? (spike di 4xx/5xx)
│   ├── SÌ → INSTABILITÀ
│   │   ├── Errori concentrati su un endpoint? → Bug nel codice
│   │   ├── Connection timeout? → Pool connessioni esaurito
│   │   ├── Race condition? → Controlla concurrency handling
│   │   ├── Memory leak? → Controlla heap usage nel tempo
│   │   └── Azione: correlazione log + APM, fix mirato
│   │
│   └── NO ↓
│
└── Problema localizzato per regione/utente?
    ├── SÌ → PROBLEMA DI EDGE/CDN
    │   ├── CDN cache invalidata? → Controlla TTL e purge
    │   ├── Edge location problematica? → Controlla status provider CDN
    │   ├── Problema ISP locale? → Traceroute e MTR
    │   └── Azione: bypass CDN temporaneo, contattare provider
    │
    └── NO → Problema applicativo non infrastrutturale
        → Profiling a livello di codice
        → Review delle metriche applicative (APM)
```

### Albero Decisionale — "Problemi di Billing"

```
PROBLEMA DI BILLING
│
├── Pagamento fallito?
│   ├── SÌ → PAYMENT FAILURE
│   │   ├── Carta scaduta? → Dunning email automatica
│   │   ├── Fondi insufficienti? → Retry automatico (3-5 tentativi)
│   │   ├── Banca declina? → Contatto diretto, metodo alternativo
│   │   ├── 3D Secure fallito? → Verifica integrazione SCA
│   │   ├── Frode sospetta? → Review manuale, contatto utente
│   │   └── Azione: sequenza dunning + notifica CS se high-value
│   │
│   └── NO ↓
│
├── Fattura contestata?
│   ├── SÌ → DISPUTE/CHARGEBACK
│   │   ├── Cliente non riconosce l'addebito? → Inviare ricevuta dettagliata
│   │   ├── Doppio addebito? → Refund immediato + scuse
│   │   ├── Servizio non erogato? → Verifica, refund se confermato
│   │   ├── Chargeback formale? → Raccogliere evidenze, rispondere in 7gg
│   │   └── Azione: template di risposta dispute + tracking
│   │
│   └── NO ↓
│
├── Errore nell'importo?
│   ├── SÌ → BILLING CALCULATION ERROR
│   │   ├── Proration calcolata male? → Verifica logica proration
│   │   ├── Sconto non applicato? → Verifica coupon/codice
│   │   ├── Tax calcolata male? → Verifica integration fiscale
│   │   └── Azione: correzione + credit note + fix nel sistema
│   │
│   └── NO ↓
│
└── Problema di upgrade/downgrade?
    ├── Piano non cambiato correttamente? → Verifica webhook Stripe
    ├── Feature non allineate al piano? → Verifica entitlement check
    ├── Billing cycle confuso? → Comunicare chiaramente la proration
    └── Azione: fix sync piano ↔ entitlement, notificare cliente
```

### Albero Decisionale — "Triage Ticket di Supporto"

```
NUOVO TICKET DI SUPPORTO
│
├── È un bug/errore tecnico?
│   ├── SÌ → CLASSIFICAZIONE BUG
│   │   ├── Blocca l'uso del prodotto? → P1 — Risposta entro 1h
│   │   ├── Impatta funzionalità core? → P2 — Risposta entro 4h
│   │   ├── Workaround disponibile? → P3 — Risposta entro 24h
│   │   ├── Cosmetico/minore? → P4 — Risposta entro 48h
│   │   └── Assegnare al team engineering con repro steps
│   │
│   └── NO ↓
│
├── È una domanda sull'uso del prodotto?
│   ├── SÌ → KNOWLEDGE BASE
│   │   ├── Articolo KB esistente? → Inviare link + contesto
│   │   ├── Articolo non esiste? → Rispondere + creare articolo
│   │   ├── Onboarding incompleto? → Offrire sessione guidata
│   │   └── Pattern ricorrente? → Segnalare a Product per migliorare UX
│   │
│   └── NO ↓
│
├── È una richiesta di feature?
│   ├── SÌ → FEATURE REQUEST
│   │   ├── Già in roadmap? → Comunicare timeline
│   │   ├── Richiesta da più clienti? → Escalare a Product
│   │   ├── Enterprise deal-blocker? → Escalare a Sales + Product
│   │   └── Registrare in feature request tracker con vote count
│   │
│   └── NO ↓
│
├── È un problema di billing?
│   ├── SÌ → Seguire albero billing sopra
│   │
│   └── NO ↓
│
└── È un reclamo/frustrazione?
    ├── Cliente a rischio churn? → Escalare a CS Manager
    ├── Incidente recente correlato? → Collegare al post-mortem
    ├── Pattern di reclami multipli? → Review account health
    └── Azione: empatia + azione concreta + follow-up in 24h
```

---

## Lancio di un SaaS — Checklist Completa

### Pre-Lancio (4-8 settimane prima)

```
PRODOTTO:
  □ MVP con feature core funzionante e testata
  □ Onboarding flow completo (signup → first value)
  □ Error handling e logging implementati
  □ Performance accettabile (page load < 3s)
  □ Mobile responsive (almeno il core flow)
  □ Backup e recovery testati

LEGALE:
  □ Terms of Service pubblicati
  □ Privacy Policy pubblicata
  □ Cookie Policy + cookie banner
  □ DPA disponibile (se target B2B EU)
  □ Company incorporata, conto bancario aperto

BILLING:
  □ Stripe (o equivalente) configurato e testato
  □ Piani e prezzi definiti
  □ Checkout flow testato end-to-end
  □ Email di conferma pagamento
  □ Gestione upgrade/downgrade funzionante

ANALYTICS:
  □ Google Analytics / Plausible installato
  □ Product analytics (Mixpanel/Amplitude/PostHog) configurato
  □ Event tracking per le azioni chiave (signup, activation, conversion)
  □ Stripe collegato a ChartMogul/Baremetrics

MARKETING:
  □ Landing page con value proposition chiara
  □ Pricing page
  □ Blog con 3-5 articoli (SEO seed)
  □ Social media profiles (LinkedIn, Twitter/X)
  □ Email marketing setup (welcome, onboarding sequence)
  □ Waitlist o early access list (se applicabile)

SUPPORT:
  □ Knowledge base con articoli fondamentali (getting started, FAQ)
  □ Contact form o chat (Intercom, Crisp, Zendesk)
  □ Status page configurata (Instatus, Better Uptime)

INFRASTRUTTURA:
  □ SSL/TLS configurato
  □ Monitoring (uptime, error rate, latency)
  □ Alerting (PagerDuty o equivalente per downtime)
  □ Auto-backup database (almeno giornaliero)
```

### Lancio (settimana del lancio)

```
DISTRIBUZIONE:
  □ Product Hunt launch (preparare in anticipo: hunter, tagline, screenshot)
  □ Hacker News "Show HN" post
  □ Annuncio su LinkedIn/Twitter con video demo
  □ Post su community di settore (Reddit, Indie Hackers)
  □ Email alla waitlist
  □ Outreach a blogger/reviewer di settore

MONITORING:
  □ Monitorare signup in tempo reale
  □ Monitorare errori e bug report
  □ Rispondere a ogni commento/domanda entro 2 ore
  □ Fix bug critici immediatamente
  □ Documentare il feedback per iterazione

POST-LANCIO IMMEDIATO (settimana 1-2):
  □ Analizzare i dati: da dove arrivano gli utenti? Dove si bloccano?
  □ Contattare personalmente i primi 20 utenti (email/call)
  □ Iterare sull'onboarding in base ai dati
  □ Scrivere il primo case study (se possibile)
  □ Pianificare il secondo wave di distribuzione
```

---

## Troubleshooting Lancio — Scenari Dettagliati

### Scenario 1: "Nessuno si iscrive dopo il lancio"

**Sintomi**: landing page live, distribuzione fatta, ma signup rate quasi zero.

**Diagnosi step-by-step**:

1. **Verifica che il traffico arrivi** — controllare analytics
   - Se traffico = 0: il problema è distribuzione, non conversione
   - Se traffico > 100 ma signup = 0: il problema è la landing page
2. **Controlla il signup flow**
   - Testa il flow tu stesso in incognito
   - Controlla console per errori JavaScript
   - Verifica che il form funzioni (email di conferma arriva?)
   - Controlla su mobile — potrebbe essere rotto
3. **Audit della landing page**
   - Value proposition chiara in 5 secondi?
   - CTA visibile above the fold?
   - Social proof presente? (testimonial, loghi, numeri)
   - Pricing chiaro o almeno "free trial" evidente?
4. **Audit del messaging**
   - Stai parlando al tuo ICP o a tutti?
   - Il linguaggio è comprensibile per il target?
   - Stai vendendo il beneficio o la feature?

**Azioni correttive**:

| Priorità | Azione | Timeline |
|----------|--------|----------|
| 1 | Fix bug tecnici nel signup flow | Immediato |
| 2 | Riscrivere headline con focus sul beneficio | Giorno 1 |
| 3 | Aggiungere social proof (anche minimo) | Giorno 1-2 |
| 4 | Ridurre friction nel signup (rimuovere campi non necessari) | Giorno 2 |
| 5 | Testare distribuzione su 2-3 canali diversi | Settimana 1 |

### Scenario 2: "Tanti signup, nessuna activation"

**Sintomi**: gli utenti si iscrivono ma non completano l'onboarding e non raggiungono il primo "aha moment".

**Diagnosi step-by-step**:

1. **Definisci l'activation event** — qual è l'azione che correla con la retention?
   - Esempio per un project management tool: "creare il primo progetto con almeno 1 task"
   - Esempio per un CRM: "importare i primi 10 contatti"
2. **Mappa il funnel di onboarding**
   - Dove si fermano? (session recording con Hotjar/FullStory)
   - Quanti step ci sono tra signup e activation?
   - C'è un punto con drop-off > 50%?
3. **Controlla il time-to-value**
   - Quanto tempo serve per arrivare al primo valore?
   - Se > 10 minuti → troppo lungo per self-serve
   - Se richiede configurazione complessa → fornire setup assistito

**Azioni correttive**:

```
QUICK WINS (settimana 1):
  □ Ridurre gli step dell'onboarding al minimo
  □ Aggiungere template/dati di esempio pre-popolati
  □ Email di onboarding con link diretto all'azione chiave
  □ Tooltip/guide contestuali nel prodotto

STRUTTURALI (settimane 2-4):
  □ Ridisegnare l'onboarding flow basato sui dati di drop-off
  □ Aggiungere checklist di onboarding visibile nel prodotto
  □ Implementare triggered emails basate su comportamento
  □ Offrire onboarding call per utenti high-value
```

### Scenario 3: "I primi utenti churnano subito"

**Sintomi**: i primi clienti paganti cancellano entro 30-60 giorni.

**Diagnosi**:

1. **Exit survey obbligatoria** — perché stai cancellando?
   - "Troppo caro" → problema di percezione valore o di ICP fit
   - "Non uso abbastanza" → problema di engagement/habit
   - "Manca la feature X" → problema di product-market fit
   - "Uso un competitor" → problema di positioning
2. **Analisi comportamentale**
   - Quali feature usavano i churned vs i retained?
   - Quanti login a settimana avevano i churned?
   - Hanno completato l'onboarding?
3. **Cohort analysis** — tutti churnano o solo un segmento?
   - Se un segmento specifico churna di più → stai acquisendo utenti sbagliati

**Azioni per segmento**:

| Motivo churn | Azione |
|-------------|--------|
| "Troppo caro" | Introduci piano entry-level o estendi trial |
| "Non uso abbastanza" | Email di re-engagement + in-app nudge |
| "Manca feature X" | Valuta se è core per ICP → build or partner |
| "Competitor" | Win-back offer + analisi differenziazione |
| Non ha completato onboarding | Automazione + outreach CS proattivo |

### Scenario 4: "Il sito crolla il giorno del lancio su Product Hunt"

**Sintomi**: spike di traffico, 503/502 errors, utenti che non riescono ad accedere.

**Azioni immediate (minuti)**:

1. Scalare le istanze manualmente se l'autoscaling non reagisce
2. Attivare CDN cache aggressiva per asset statici
3. Abilitare rate limiting per proteggere il backend
4. Comunicare su status page: "Traffico elevato, stiamo scalando"

**Prevenzione per il prossimo lancio**:

```
PRE-LANCIO INFRA CHECKLIST:
  □ Load test con traffico 5-10x il normale
  □ Autoscaling configurato con soglie aggressive
  □ CDN configurata per static assets
  □ Database read replicas attive (se applicabile)
  □ Connection pooling configurato con margine
  □ Rate limiting su API per proteggere da abuse
  □ Runbook di scaling pronto e condiviso con il team
```

---

## Pricing Review — Processo Pratico

### Quando Fare un Pricing Review

- Ogni 6-12 mesi (routine)
- Dopo aver raggiunto PMF (passare da pricing approssimativo a pricing strategico)
- Quando il CAC:LTV ratio degrada
- Quando il competitor cambia prezzo significativamente
- Prima di un'espansione a nuovo segmento (enterprise, international)

### Processo in 5 Step

```
STEP 1: RACCOGLIERE DATI (settimana 1)

  Dati interni:
    □ Distribuzione clienti per piano
    □ Conversion rate per piano
    □ Churn rate per piano
    □ Feature usage per piano (quali feature usano i paganti vs free?)
    □ Win/loss analysis (prezzo come motivo di loss?)
    □ Revenue per piano (quale piano genera più MRR?)

  Dati esterni:
    □ Prezzi dei competitor (aggiornati)
    □ Willingness-to-pay dei clienti (survey Van Westendorp: 50+ risposte)
    □ Benchmark di settore

STEP 2: ANALIZZARE (settimana 2)

  Domande chiave:
    □ Il piano free è troppo generoso? (pochi convertono perché il free basta)
    □ Il gap tra free e primo piano pagante è troppo grande? (manca un mid-tier)
    □ L'ARPU è allineato al valore percepito?
    □ I clienti enterprise pagano abbastanza? (quasi sempre no)
    □ Il pricing model è allineato alla value metric?

STEP 3: PROGETTARE (settimana 3)

  Definire:
    □ Value metric (per cosa il cliente paga: seat, usage, feature)
    □ Numero di piani (3-4 è lo standard)
    □ Feature per piano (allineate alle buyer persona)
    □ Prezzi (basati su WTP + competitive + valore)
    □ Presentazione (pricing page layout)

STEP 4: TESTARE (settimana 4-8)

  Opzioni:
    □ A/B test sulla pricing page (nuovi visitatori)
    □ Cohort test (nuovi clienti su nuovo pricing, esistenti invariati)
    □ Customer interview (mostrare il nuovo pricing a 10-20 clienti)
    □ Sales team feedback (i prezzi sono difendibili in demo?)

STEP 5: IMPLEMENTARE (settimana 8-12)

  □ Comunicare il cambio con 30-60 giorni di anticipo
  □ Grandfathering: mantenere il vecchio prezzo per clienti esistenti (per un periodo)
  □ Monitorare: conversion rate, churn, ARPU, feedback nelle prime 4 settimane
  □ Iterare se i dati mostrano problemi
```

---

## Audit delle Metriche SaaS

### Health Check Mensile (30 minuti)

```
REVENUE:
  □ MRR attuale: $ _________
  □ MRR growth MoM: _______ % (target: > 5% early, > 3% scale)
  □ Net New MRR: $ _________ (new + expansion - churn - contraction)
  □ Quick Ratio: _________ (target: > 4 early, > 2 scale)

RETENTION:
  □ Logo churn rate: _______ % (target: < 3% mensile SMB, < 1% enterprise)
  □ Revenue churn rate: _______ %
  □ NRR: _______ % (target: > 100%, ideale > 110%)
  □ GRR: _______ % (target: > 80%, ideale > 90%)

ACQUISITION:
  □ New customers: _________
  □ CAC (blended): $ _________
  □ CAC (paid only): $ _________
  □ LTV:CAC ratio: _________ (target: > 3:1)
  □ CAC payback: _________ mesi (target: < 18)

ENGAGEMENT:
  □ DAU/MAU: _______ % (target: > 25%)
  □ Activation rate (new users): _______ % (target: > 40%)
  □ Feature adoption (top 3 features): _______ %

HEALTH OVERALL:
  □ Rule of 40: _______ (growth rate + profit margin, target: > 40)
  □ Burn multiple: _______ (net burn / net new ARR, target: < 2)
  □ Runway: _______ mesi (target: > 18)
```

### Red Flag — Quando Preoccuparsi

| Metrica | Yellow flag | Red flag |
|---|---|---|
| MRR growth MoM | < 3% | < 0% (contrazione) |
| Logo churn mensile | > 3% | > 5% |
| NRR | < 100% | < 90% |
| CAC payback | > 18 mesi | > 24 mesi |
| LTV:CAC | < 3:1 | < 1:1 |
| Activation rate | < 30% | < 15% |
| Runway | < 12 mesi | < 6 mesi |

---

## Incident Management

### Livelli di Severità

| Livello | Nome | Criterio | Tempo di Risposta | Tempo di Risoluzione Target |
|---------|------|----------|-------------------|-----------------------------|
| P1 | Critico | Servizio completamente down, data breach, perdita dati | < 15 minuti | < 4 ore |
| P2 | Alto | Funzionalità core degradata, impatto su >25% utenti | < 30 minuti | < 8 ore |
| P3 | Medio | Feature secondaria non funziona, workaround disponibile | < 4 ore | < 48 ore |
| P4 | Basso | Bug cosmetico, miglioramento minore | < 24 ore | Prossimo sprint |

### Processo di Incident Response

```
FASE 1: RILEVAMENTO (0-5 min)
  ┌─────────────────────────────────────────────┐
  │ Trigger: allarme monitoring / report utente  │
  │                                              │
  │ 1. Verificare la severity (P1-P4)           │
  │ 2. Identificare l'Incident Commander (IC)    │
  │ 3. Creare il canale #incident-YYYYMMDD      │
  │ 4. Notificare le parti interessate           │
  └─────────────────────────────────────────────┘

FASE 2: TRIAGE (5-15 min)
  ┌─────────────────────────────────────────────┐
  │ IC coordina:                                 │
  │                                              │
  │ 1. Cosa è rotto? (sintomo)                  │
  │ 2. Chi è impattato? (scope)                 │
  │ 3. Da quando? (timeline)                    │
  │ 4. Cosa è cambiato? (deploy, config, load)  │
  │ 5. Assegnare ruoli:                         │
  │    - IC: coordina                           │
  │    - Tech Lead: investiga e risolve         │
  │    - Comms Lead: aggiorna stakeholder       │
  └─────────────────────────────────────────────┘

FASE 3: MITIGAZIONE (15 min - 4h per P1)
  ┌─────────────────────────────────────────────┐
  │ Priorità: RIPRISTINARE IL SERVIZIO          │
  │                                              │
  │ Opzioni in ordine di preferenza:            │
  │ 1. Rollback dell'ultimo deploy              │
  │ 2. Disabilitare la feature con feature flag │
  │ 3. Scalare risorse (se carico)              │
  │ 4. Failover su infra secondaria             │
  │ 5. Hotfix (solo se le altre non funzionano) │
  │                                              │
  │ NON cercare la root cause durante P1.       │
  │ Prima ripristina, poi investiga.            │
  └─────────────────────────────────────────────┘

FASE 4: RISOLUZIONE
  ┌─────────────────────────────────────────────┐
  │ 1. Confermare che il servizio è ripristinato│
  │ 2. Monitorare per 30 min per recidive      │
  │ 3. Aggiornare la status page               │
  │ 4. Notifica "Risolto" a stakeholder        │
  │ 5. Schedulare post-mortem entro 48h         │
  └─────────────────────────────────────────────┘
```

### Comunicazione Durante un Incidente

**Template per status page — Incidente in corso**:

```
TITOLO: [Degradazione/Outage] [Servizio impattato]
DATA: YYYY-MM-DD HH:MM UTC

STATO: In corso di investigazione

IMPATTO:
[Descrivere cosa l'utente sperimenta]
Esempio: "Gli utenti potrebbero riscontrare errori durante il salvataggio
dei progetti. L'accesso in lettura non è impattato."

AGGIORNAMENTI:
- HH:MM UTC — Identificato il problema. Il team sta lavorando alla risoluzione.
- HH:MM UTC — Mitigazione parziale applicata. Il servizio sta riprendendo.
- HH:MM UTC — Servizio completamente ripristinato. Monitoraggio attivo.

PROSSIMO AGGIORNAMENTO: entro 30 minuti o alla risoluzione.
```

**Template email per clienti enterprise (P1)**:

```
Oggetto: [Nome Servizio] — Incidente in corso e azioni in atto

Gentile [Nome],

alle [HH:MM UTC di oggi], abbiamo rilevato un problema che impatta
[descrizione impatto specifico per questo cliente].

Stato attuale: [Investigazione / Mitigazione in corso / Risolto]

Cosa stiamo facendo:
- [Azione 1]
- [Azione 2]

Cosa dovete fare:
- [Se applicabile, altrimenti "Non è richiesta nessuna azione da parte vostra"]

Prossimo aggiornamento: entro [30 min / 1h / alla risoluzione]

Per qualsiasi domanda urgente: [contatto diretto]

Distinti saluti,
[Nome], [Ruolo]
```

### On-Call Rotation

**Struttura consigliata per team piccoli (< 10 persone)**:

```
ROTAZIONE:
  - Turni settimanali (lun 09:00 → lun 09:00 successivo)
  - Minimo 2 persone in rotazione (primario + backup)
  - Handoff documentato alla fine di ogni turno
  - Compensazione: giorno di riposo extra o bonus on-call

STRUMENTI:
  - PagerDuty / Opsgenie per alerting e escalation
  - Runbook accessibili a tutti (non nella testa di una persona)
  - VPN / accesso infra dal mobile per interventi rapidi

REGOLE:
  - On-call = disponibile entro 15 min per P1
  - Se non risponde in 15 min → escalation automatica al backup
  - Nessun deploy il venerdì pomeriggio (riduce il rischio weekend)
  - Ogni incidente P1/P2 → post-mortem obbligatorio
```

### War Room — Protocollo per Incidenti P1

```
ATTIVAZIONE:
  Trigger: qualsiasi P1 non risolto entro 30 minuti

SETUP:
  1. IC crea chiamata (Slack Huddle / Google Meet / Zoom)
  2. Invita: on-call engineer + tech lead + team lead infra
  3. IC condivide lo schermo con i log/dashboard

RUOLI IN WAR ROOM:
  - Incident Commander: coordina, non scrive codice
  - Investigation Lead: analizza log, metriche, root cause
  - Fix Engineer: implementa il fix o rollback
  - Comms Lead: aggiorna stakeholder ogni 15 min
  - Scribe: documenta timeline e azioni in tempo reale

REGOLE:
  - Un thread alla volta — l'IC dirige la conversazione
  - Le ipotesi si verificano, non si discutono
  - Update ogni 15 minuti sullo status page
  - Decisioni documentate con rationale
  - Dopo la risoluzione: 5 min di debrief immediato
```

---

## Post-Mortem — Template e Processo

### Principi del Post-Mortem Blameless

Un post-mortem efficace si concentra su **cosa è successo** e **come prevenirlo**, non su **chi ha sbagliato**. Le persone agiscono razionalmente nel contesto delle informazioni che hanno al momento. Il sistema che ha permesso l'errore è il vero target dell'analisi.

**Regole del post-mortem blameless**:
1. Non identificare individui come causa — identificare sistemi, processi, gap
2. Assumere che tutti stavano facendo del loro meglio con le info disponibili
3. Concentrarsi su come rendere l'errore impossibile o facilmente recuperabile
4. Trattare il post-mortem come un investimento, non come una punizione
5. Condividere i risultati con tutto il team — la trasparenza previene la ripetizione

### Template Post-Mortem Completo

```
═══════════════════════════════════════════════
POST-MORTEM: [Titolo descrittivo dell'incidente]
═══════════════════════════════════════════════

Data incidente: YYYY-MM-DD
Autore: [Nome]
Data post-mortem: YYYY-MM-DD
Partecipanti: [Lista nomi]
Severity: P1 / P2 / P3
Durata: [HH:MM inizio] → [HH:MM risoluzione] = [durata totale]

───────────────────────────────────────────────
1. EXECUTIVE SUMMARY
───────────────────────────────────────────────

[2-3 frasi. Cosa è successo, quanto è durato, qual è stato l'impatto.]

Esempio: "Il 15 marzo 2026, il servizio di autenticazione è stato
irraggiungibile per 47 minuti a causa di un certificato TLS scaduto
sul load balancer. Tutti gli utenti sono stati impossibilitati ad
accedere durante la finestra dell'incidente. Circa 2.400 utenti
sono stati impattati."

───────────────────────────────────────────────
2. IMPATTO
───────────────────────────────────────────────

Utenti impattati:       [numero o percentuale]
Revenue impattata:      [€ stimati di revenue persa o a rischio]
SLA violati:            [sì/no, dettagli]
Ticket di supporto:     [numero ricevuti durante l'incidente]
Menzioni social/press:  [sì/no]

───────────────────────────────────────────────
3. TIMELINE
───────────────────────────────────────────────

(Tutte le ore in UTC)

HH:MM — [Evento che ha iniziato o causato il problema]
HH:MM — [Primo segnale visibile (allarme, report utente)]
HH:MM — [IC assegnato, triage iniziato]
HH:MM — [Prima ipotesi investigata]
HH:MM — [Root cause identificata]
HH:MM — [Mitigazione applicata]
HH:MM — [Servizio confermato ripristinato]
HH:MM — [Monitoraggio post-fix completato]

───────────────────────────────────────────────
4. ROOT CAUSE
───────────────────────────────────────────────

[Descrizione dettagliata della causa tecnica.]

───────────────────────────────────────────────
5. ANALISI "5 PERCHÉ"
───────────────────────────────────────────────

Perché il servizio è andato down?
→ Perché il certificato TLS era scaduto

Perché il certificato era scaduto?
→ Perché il rinnovo automatico era fallito silenziosamente

Perché il fallimento era silenzioso?
→ Perché non c'era monitoring sul rinnovo certificati

Perché non c'era monitoring?
→ Perché i certificati erano gestiti manualmente, senza runbook

Perché non c'era un runbook?
→ Perché il processo non era documentato quando è stato configurato

ROOT CAUSE SISTEMICA: Processo non documentato + assenza di
monitoring su un componente critico.

───────────────────────────────────────────────
6. COSA HA FUNZIONATO
───────────────────────────────────────────────

- [Esempio: L'allarme uptime ha notificato entro 2 minuti]
- [Esempio: Il team on-call ha risposto entro 5 minuti]
- [Esempio: La comunicazione su status page è stata tempestiva]

───────────────────────────────────────────────
7. COSA NON HA FUNZIONATO
───────────────────────────────────────────────

- [Esempio: Nessun allarme preventivo sulla scadenza certificato]
- [Esempio: Il runbook per i certificati non esisteva]
- [Esempio: Il rollback non era applicabile in questo caso]

───────────────────────────────────────────────
8. COSA CI È ANDATA BENE (FORTUNA)
───────────────────────────────────────────────

- [Esempio: L'incidente è avvenuto alle 14:00 e non alle 3:00]
- [Esempio: Nessun dato è stato perso nonostante l'outage]

───────────────────────────────────────────────
9. ACTION ITEMS
───────────────────────────────────────────────

| # | Azione | Owner | Priorità | Deadline | Status |
|---|--------|-------|----------|----------|--------|
| 1 | Implementare auto-rinnovo cert con Let's Encrypt | [Nome] | P1 | +7gg | TODO |
| 2 | Aggiungere allarme scadenza cert (30gg prima) | [Nome] | P1 | +3gg | TODO |
| 3 | Creare runbook per gestione certificati | [Nome] | P2 | +14gg | TODO |
| 4 | Audit di tutti i certificati in produzione | [Nome] | P2 | +7gg | TODO |

───────────────────────────────────────────────
10. LEZIONI APPRESE
───────────────────────────────────────────────

[1-3 frasi su cosa il team ha imparato e porterà avanti.]
```

### Condurre il Meeting di Post-Mortem

**Formato consigliato: 60 minuti**

```
PREPARAZIONE (prima del meeting):
  - IC prepara il draft del post-mortem con timeline e dati
  - Tutti i partecipanti rileggono la timeline
  - Raccogliere metriche di impatto

AGENDA (60 min):
  00-05: IC presenta il summary e l'impatto
  05-20: Revisione timeline — ognuno aggiunge/corregge
  20-35: Analisi root cause — 5 perché facilitati dall'IC
  35-50: Definizione action items con owner e deadline
  50-60: Lezioni apprese e chiusura

REGOLE DEL MEETING:
  - Nessun biasimo — se qualcuno inizia a puntare il dito, l'IC reindirizza
  - Fatti, non opinioni — "il deploy è avvenuto alle 14:32" non "qualcuno
    ha deployato senza controllare"
  - Ogni action item deve avere un owner singolo e una deadline
  - Il post-mortem è pubblicato internamente entro 48h dal meeting
```

---

## Runbook Operativi

### Runbook 1: Deployment in Produzione

```
═══════════════════════════════════════════════
RUNBOOK: Deployment in Produzione
═══════════════════════════════════════════════
Ultimo aggiornamento: YYYY-MM-DD
Owner: [Team/Persona]
Revisione: trimestrale

───────────────────────────────────────────────
PRE-DEPLOY CHECKLIST
───────────────────────────────────────────────

□ Tutti i test passano (unit, integration, e2e)
□ Code review approvata
□ Nessun P1/P2 aperto correlato
□ Database migration testata su staging
□ Feature flags configurati per le nuove feature
□ Rollback plan documentato
□ Team on-call informato del deploy

───────────────────────────────────────────────
PROCESSO DI DEPLOY
───────────────────────────────────────────────

Step 1: Preparazione
  $ git checkout main
  $ git pull origin main
  # Verifica che il commit da deployare sia corretto
  $ git log --oneline -5

Step 2: Deploy su staging
  $ ./deploy.sh staging
  # Verifica manuale:
  □ Homepage carica correttamente
  □ Login funziona
  □ Feature core funzionano
  □ Nessun errore nei log

Step 3: Deploy graduale in produzione
  # Se canary deployment disponibile:
  $ ./deploy.sh production --canary 5%
  # Monitorare per 10 minuti:
  □ Error rate < baseline + 0.1%
  □ Latency p99 < baseline + 20%
  □ Nessun spike di errori nei log

  # Se tutto ok, aumentare gradualmente:
  $ ./deploy.sh production --canary 25%
  # Monitorare 10 minuti
  $ ./deploy.sh production --canary 100%

Step 4: Verifica post-deploy
  □ Dashboard metriche: error rate, latency, throughput
  □ Smoke test manuale delle feature core
  □ Controllare i log per errori nuovi
  □ Verificare che le migration siano completate

───────────────────────────────────────────────
ROLLBACK PROCEDURE
───────────────────────────────────────────────

TRIGGER PER ROLLBACK:
  - Error rate > 2x baseline per > 5 minuti
  - Latency p95 > 3x baseline
  - Funzionalità core non funziona
  - Data corruption rilevata

COME FARE ROLLBACK:
  # Opzione 1: Rollback del deploy
  $ ./deploy.sh production --rollback
  # Verifica che il servizio sia tornato alla versione precedente

  # Opzione 2: Feature flag (se la feature è dietro flag)
  # Disabilitare il flag nel pannello di gestione
  # Nessun redeploy necessario

  # Opzione 3: Revert del commit + redeploy
  $ git revert <commit-hash>
  $ git push origin main
  $ ./deploy.sh production

POST-ROLLBACK:
  □ Verificare che il servizio funzioni
  □ Notificare il team
  □ Creare ticket per investigare il problema
  □ NON ri-deployare senza aver capito la causa

───────────────────────────────────────────────
FINESTRE DI DEPLOY CONSIGLIATE
───────────────────────────────────────────────

| Giorno | Finestra | Rischio |
|--------|----------|---------|
| Lun-Gio | 10:00-16:00 locale | Basso |
| Venerdì | 10:00-13:00 locale | Medio |
| Venerdì PM | NO | Alto — no support weekend |
| Weekend | Solo hotfix P1 | Solo emergenze |
```

### Runbook 2: Scaling per Traffico Elevato

```
═══════════════════════════════════════════════
RUNBOOK: Scaling per Traffico Elevato
═══════════════════════════════════════════════

───────────────────────────────────────────────
TRIGGER
───────────────────────────────────────────────

Attivare questo runbook quando:
  - CPU media > 70% per > 5 minuti
  - Memory usage > 80%
  - Request queue depth > 100
  - Response time p95 > 2x baseline
  - Evento previsto (lancio, marketing campaign, Product Hunt)

───────────────────────────────────────────────
STEP 1: VALUTAZIONE (5 min)
───────────────────────────────────────────────

  □ Identificare il componente sotto stress:
    - Web server / application server
    - Database
    - Cache (Redis/Memcached)
    - Queue worker
    - Servizio esterno

  □ Verificare se è traffico legittimo o attack
    # Controllare pattern di traffico:
    # - IP distribution (concentrazione sospetta?)
    # - User agent distribution
    # - Request pattern (endpoint specifici sotto attacco?)

───────────────────────────────────────────────
STEP 2: SCALING RAPIDO
───────────────────────────────────────────────

Application server:
  # AWS Auto Scaling — modifica il desired count
  $ aws autoscaling set-desired-capacity \
      --auto-scaling-group-name prod-asg \
      --desired-capacity <nuovo-numero>

  # Kubernetes — scala il deployment
  $ kubectl scale deployment app-web \
      --replicas=<nuovo-numero> -n production

Database (se il collo è qui):
  # Aggiungere read replica (se non presente)
  # Attivare connection pooler (PgBouncer)
  # Esempio configurazione PgBouncer:
  # pool_mode = transaction
  # default_pool_size = 25
  # max_client_conn = 200

Cache:
  # Verificare hit rate Redis
  $ redis-cli info stats | grep keyspace
  # Se hit rate basso → rivedere le cache key
  # Se memory piena → scalare istanza Redis

───────────────────────────────────────────────
STEP 3: VERIFICA E STABILIZZAZIONE
───────────────────────────────────────────────

  □ Monitorare le metriche per 15 minuti post-scaling
  □ Verificare che la latency si normalizzi
  □ Controllare i costi (non lasciare istanze in più per settimane)
  □ Documentare: quante istanze servono per questo livello di carico

───────────────────────────────────────────────
STEP 4: POST-EVENTO
───────────────────────────────────────────────

  □ Ridurre le istanze al livello normale (o autoscaling lo fa)
  □ Review: l'autoscaling ha funzionato? Se no, perché?
  □ Aggiornare le soglie di autoscaling se necessario
  □ Documentare i costi aggiuntivi
```

### Runbook 3: Emergenza Database

```
═══════════════════════════════════════════════
RUNBOOK: Emergenza Database
═══════════════════════════════════════════════

───────────────────────────────────────────────
SCENARIO A: DISCO PIENO
───────────────────────────────────────────────

SINTOMI: Errori "disk full", write failure, WAL che cresce

AZIONI IMMEDIATE:
  1. Verificare uso disco
     $ df -h /var/lib/postgresql
     $ du -sh /var/lib/postgresql/data/pg_wal/

  2. Se WAL troppo grande — verificare replication lag
     $ psql -c "SELECT pg_wal_lsn_diff(
         pg_current_wal_lsn(),
         sent_lsn) AS lag_bytes
       FROM pg_stat_replication;"

  3. Liberare spazio temporaneo
     # Pulire i log vecchi (NON i WAL attivi!)
     $ find /var/log/postgresql -name "*.log" -mtime +7 -delete
     # Eseguire VACUUM su tabelle grandi
     $ psql -c "VACUUM FULL verbose_table_name;"

  4. Espandere il disco (cloud)
     # AWS: modifica il volume EBS
     # Dopo il resize, eseguire:
     $ sudo resize2fs /dev/xvdf

PREVENZIONE:
  □ Allarme a 70% e 85% di utilizzo disco
  □ VACUUM automatico configurato con soglie aggressive
  □ Log rotation configurata
  □ Archivio WAL verso storage secondario

───────────────────────────────────────────────
SCENARIO B: CONNESSIONI ESAURITE
───────────────────────────────────────────────

SINTOMI: "too many connections", nuovi utenti non riescono a connettersi

DIAGNOSI:
  $ psql -c "SELECT count(*) FROM pg_stat_activity;"
  $ psql -c "SELECT state, count(*)
    FROM pg_stat_activity GROUP BY state;"
  $ psql -c "SELECT usename, count(*)
    FROM pg_stat_activity GROUP BY usename ORDER BY count DESC;"

AZIONI:
  1. Identificare connessioni idle da troppo tempo
     $ psql -c "SELECT pid, state, query_start, query
       FROM pg_stat_activity
       WHERE state = 'idle' AND query_start < now() - interval '30 min';"

  2. Terminare connessioni idle (con cautela)
     $ psql -c "SELECT pg_terminate_backend(pid)
       FROM pg_stat_activity
       WHERE state = 'idle' AND query_start < now() - interval '1 hour';"

  3. Se il problema persiste → attivare PgBouncer
     # Configurazione minima PgBouncer:
     # [databases]
     # myapp = host=localhost dbname=myapp
     # [pgbouncer]
     # pool_mode = transaction
     # default_pool_size = 20
     # max_client_conn = 300
     # min_pool_size = 5

PREVENZIONE:
  □ Connection pooling obbligatorio (PgBouncer o application-level)
  □ Timeout per connessioni idle configurato
  □ Allarme a 80% del max_connections
  □ Application code: chiudere le connessioni dopo l'uso

───────────────────────────────────────────────
SCENARIO C: QUERY BLOCCANTI (LOCK)
───────────────────────────────────────────────

SINTOMI: Query lente o bloccate, throughput crollato

DIAGNOSI:
  # Trovare i lock attivi
  $ psql -c "SELECT blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
  FROM pg_catalog.pg_locks blocked_locks
  JOIN pg_catalog.pg_stat_activity blocked_activity
    ON blocked_activity.pid = blocked_locks.pid
  JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.relation = blocked_locks.relation
    AND blocking_locks.pid != blocked_locks.pid
  JOIN pg_catalog.pg_stat_activity blocking_activity
    ON blocking_activity.pid = blocking_locks.pid
  WHERE NOT blocked_locks.granted;"

AZIONI:
  1. Identificare la query bloccante
  2. Se è una transazione dimenticata aperta → terminarla
     $ psql -c "SELECT pg_terminate_backend(<blocking_pid>);"
  3. Se è una migration → attendere o interromperla (con cautela)
  4. Aggiungere statement_timeout per prevenire
     # In postgresql.conf:
     # statement_timeout = '30s'  -- per connessioni applicative
     # lock_timeout = '10s'

───────────────────────────────────────────────
SCENARIO D: RESTORE DA BACKUP
───────────────────────────────────────────────

QUANDO: corruzione dati, DROP TABLE accidentale, data breach con modifica dati

PROCEDURA:
  1. STOP: non sovrascrivere il backup con dati corrotti
     # Fermare gli scriventi se possibile

  2. Identificare il punto di recovery
     # Ultimo backup valido + WAL per PITR

  3. Restore
     # pg_restore da dump:
     $ pg_restore -d myapp_restored backup_YYYYMMDD.dump

     # PITR con WAL:
     # Configurare recovery_target_time in recovery.conf
     # recovery_target_time = '2026-03-15 14:30:00 UTC'
     # Avviare PostgreSQL in recovery mode

  4. Verifica dati
     □ Conteggio righe sulle tabelle critiche
     □ Verifica integrità referenziale
     □ Spot check su record specifici

  5. Switch del traffico al database restored
     # Aggiornare la connection string
     # Monitorare errori per 30 minuti

TESTARE IL RESTORE MENSILMENTE — un backup non testato non è un backup.
```

---

## Performance Debugging

### Framework di Debug Sistematico

Quando il prodotto è "lento", il primo passo è quantificare e localizzare il problema. Non ottimizzare alla cieca.

```
STEP 1: QUANTIFICARE
  Cosa significa "lento"?
  - Quale pagina/endpoint/azione?
  - Quanto tempo impiega ora vs quanto dovrebbe?
  - Per tutti gli utenti o per un sottoinsieme?
  - Da quando è lento?

STEP 2: MISURARE
  Dove si passa il tempo?
  - Frontend rendering? → Browser DevTools, Lighthouse
  - Network transfer? → HAR file, waterfall
  - Backend processing? → APM (Datadog, New Relic, Sentry)
  - Database query? → Slow query log, EXPLAIN
  - Servizio esterno? → Latenza chiamate API terze parti

STEP 3: IDENTIFICARE IL COLLO DI BOTTIGLIA
  - Il 80% del tempo è speso in quale componente?
  - È CPU-bound, I/O-bound o network-bound?
  - È consistente o intermittente?

STEP 4: OTTIMIZZARE IL COLLO DI BOTTIGLIA SPECIFICO
  - Non ottimizzare tutto — solo il bottleneck
  - Misurare dopo ogni intervento
  - Verificare che non ci siano regressioni altrove
```

### Debug Latenza Backend

**Query lente nel database**:

```sql
-- PostgreSQL: trovare le query più lente
SELECT query,
       calls,
       total_exec_time / 1000 AS total_seconds,
       mean_exec_time / 1000 AS avg_seconds,
       rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Analizzare una query specifica
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.*, count(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2026-01-01'
GROUP BY u.id;
```

**Cosa cercare nell'output di EXPLAIN**:

| Pattern nell'EXPLAIN | Problema | Soluzione |
|----------------------|----------|-----------|
| Seq Scan su tabella grande | Manca indice | Creare indice sulla colonna filtrata |
| Nested Loop con rows alto | Join inefficiente | Aggiungere indice sulla FK o rivedere la query |
| Sort con external merge | Sort su dataset grande senza indice | Indice sulla colonna di sort |
| Hash Join con batches > 1 | work_mem troppo basso per il join | Aumentare work_mem o ottimizzare la query |
| Rows estimate vs actual molto diversi | Statistiche obsolete | ANALYZE sulla tabella |

**N+1 Query — Come Identificare e Risolvere**:

```
SINTOMO: un endpoint fa centinaia di query identiche con parametri diversi

DIAGNOSI (nei log):
  SELECT * FROM orders WHERE user_id = 1;
  SELECT * FROM orders WHERE user_id = 2;
  SELECT * FROM orders WHERE user_id = 3;
  ... (ripetuto 200 volte)

CAUSA: il codice carica gli utenti e poi per ogni utente fa una query
       per caricare i suoi ordini.

SOLUZIONE:
  # SBAGLIATO (N+1):
  # users = db.query("SELECT * FROM users LIMIT 200")
  # for user in users:
  #     orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)

  # CORRETTO (1 query con JOIN):
  # users_with_orders = db.query("""
  #     SELECT u.*, json_agg(o.*) AS orders
  #     FROM users u
  #     LEFT JOIN orders o ON o.user_id = u.id
  #     GROUP BY u.id
  #     LIMIT 200
  # """)

  # ALTERNATIVA (2 query con IN clause):
  # users = db.query("SELECT * FROM users LIMIT 200")
  # user_ids = [u.id for u in users]
  # orders = db.query("SELECT * FROM orders WHERE user_id = ANY(?)", user_ids)
  # -- Poi aggregare in memoria
```

### Debug Latenza Frontend

```
CHECKLIST PERFORMANCE FRONTEND:

1. LARGEST CONTENTFUL PAINT (LCP) > 2.5s
   □ L'immagine hero è ottimizzata? (WebP/AVIF, dimensioni corrette)
   □ Il font è preloaded?
   □ Il CSS critico è inline o bloccante?
   □ Ci sono script sync che bloccano il rendering?

2. FIRST INPUT DELAY / INTERACTION TO NEXT PAINT (INP) > 200ms
   □ Ci sono event handler pesanti? (> 50ms)
   □ Il main thread è bloccato da JS parsing?
   □ Ci sono layout thrashing? (lettura + scrittura DOM alternata)
   □ Componenti che ri-renderizzano troppo spesso?

3. CUMULATIVE LAYOUT SHIFT (CLS) > 0.1
   □ Tutte le immagini hanno width/height?
   □ I font hanno font-display: swap + fallback dimensionato?
   □ Ci sono elementi iniettati dinamicamente sopra il fold?
   □ Ci sono ads o embed che cambiano dimensione?

4. BUNDLE SIZE
   # Analizzare il bundle:
   # Per webpack: webpack-bundle-analyzer
   # Per vite: rollup-plugin-visualizer
   # Per next: @next/bundle-analyzer

   □ Librerie duplicate? (es. due versioni di lodash)
   □ Importazioni totali invece di specifiche? (import * from 'lodash')
   □ Codice morto non tree-shaked?
   □ Immagini nel bundle invece che nella CDN?
```

### Profiling con APM

**Configurazione base con strumenti open source** (esempio con OpenTelemetry):

```yaml
# docker-compose per stack di observability locale
# (per development/staging)

services:
  jaeger:
    image: jaegertracing/all-in-one:1.54
    ports:
      - "16686:16686"  # UI
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.4.0
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Metriche chiave da monitorare**:

| Metrica | Descrizione | Allarme |
|---------|------------|---------|
| `http_request_duration_p50` | Latenza mediana | Baseline + 50% |
| `http_request_duration_p95` | Latenza top 5% | > 1s |
| `http_request_duration_p99` | Latenza top 1% | > 3s |
| `http_requests_total{status=5xx}` | Errori server | > 0.5% del totale |
| `process_resident_memory_bytes` | Uso memoria | > 80% del limite |
| `db_query_duration_p95` | Latenza query DB | > 500ms |
| `external_api_duration_p95` | Latenza API esterne | > 2s |

---

## Problemi di Scaling

### Quando Scalare — Segnali

| Segnale | Soglia | Azione |
|---------|--------|--------|
| CPU media | > 70% per > 5 min | Aggiungere istanze |
| Memory | > 80% | Investigare leak o scalare |
| Request queue | > 50 richieste in coda | Scalare web workers |
| DB connections | > 80% max | Aggiungere pooler o scalare DB |
| Response time p95 | > 2x baseline | Identificare collo e scalare |
| Disk I/O | > 80% IOPS | Scalare storage o ottimizzare query |

### Scaling Verticale vs Orizzontale

```
SCALING VERTICALE (scale up):
  = macchina più grande

  PRO:
  - Semplice da implementare
  - Nessuna modifica applicativa
  - Nessun problema di stato condiviso

  CONTRO:
  - Limite fisico (la macchina più grande ha un tetto)
  - Downtime per il resize (spesso)
  - Costo non lineare (2x CPU ≠ 2x prezzo, spesso di più)

  QUANDO USARLO:
  - Database primario (fino a un certo punto)
  - Applicazioni stateful difficili da distribuire
  - Quick fix temporaneo mentre si progetta lo scaling orizzontale

─────────────────────────────────────────────

SCALING ORIZZONTALE (scale out):
  = più macchine identiche

  PRO:
  - Scalabilità quasi lineare (teoricamente)
  - Ridondanza (fault tolerance)
  - Costo più prevedibile

  CONTRO:
  - Richiede applicazione stateless (o stato esternalizzato)
  - Complessità: load balancing, session management, cache invalidation
  - Deploy più complesso

  QUANDO USARLO:
  - Web server / API server (quasi sempre)
  - Workers per job asincroni
  - Microservizi

PREREQUISITI PER SCALING ORIZZONTALE:
  □ Applicazione stateless (sessioni in Redis/DB, non in memoria)
  □ Asset statici su CDN (non serviti dall'applicazione)
  □ File upload su object storage (S3, non filesystem locale)
  □ Job asincroni su queue (non in-process)
  □ Database connection pooling configurato
```

### Colli di Bottiglia Comuni e Soluzioni

**1. Database come bottleneck**

```
SINTOMI:
  - Query lente
  - Connection pool esaurito
  - CPU del DB al 100%

SOLUZIONI GRADUALI:
  Livello 1: Ottimizzazione query
    → Indici mancanti
    → Query N+1
    → SELECT * invece di colonne specifiche
    → JOIN non necessari

  Livello 2: Caching
    → Cache applicativo (Redis) per query ripetute
    → TTL basato sulla frequenza di cambiamento dei dati
    → Invalidazione cache esplicita sui write

  Livello 3: Read Replicas
    → Separare letture e scritture
    → Letture dai replica, scritture sul primary
    → Attenzione al replication lag

  Livello 4: Partitioning / Sharding
    → Partizionamento per data (tabelle con milioni di righe)
    → Sharding per tenant (multi-tenant SaaS)
    → Complessità alta — fare solo quando necessario
```

**2. API come bottleneck**

```
SINTOMI:
  - Timeout su chiamate API
  - Rate limiting raggiunto
  - Risposte lente per payload grandi

SOLUZIONI:
  □ Paginazione obbligatoria (max 100 items per pagina)
  □ Compressione risposte (gzip/brotli)
  □ Campo selection (GraphQL-like o ?fields=id,name)
  □ Cache HTTP con ETag e Cache-Control
  □ Rate limiting per proteggere il backend
  □ Risposta asincrona per operazioni pesanti (202 Accepted + webhook)
```

**3. Background Job come bottleneck**

```
SINTOMI:
  - Queue cresce più velocemente di quanto viene processata
  - Job in ritardo (latency della queue alta)
  - Worker in OOM o crash

SOLUZIONI:
  □ Scalare i worker (più istanze parallele)
  □ Prioritizzare i job (queue separate per urgenza)
  □ Batch processing (aggregare più operazioni in un job)
  □ Timeout e retry con backoff esponenziale
  □ Dead letter queue per job che falliscono ripetutamente

  # Esempio configurazione retry con backoff:
  # retry_config:
  #   max_retries: 5
  #   backoff_type: exponential
  #   initial_delay_ms: 1000     # 1s, 2s, 4s, 8s, 16s
  #   max_delay_ms: 60000
  #   dead_letter_queue: "dlq_jobs"
```

### Caching Strategy

```
DECISIONE: COSA CACHARE?

□ La risposta cambia raramente? → Cache con TTL lungo
□ Il costo di calcolo è alto? → Cache con TTL medio
□ Viene richiesto frequentemente? → Cache con TTL breve ma alta hit rate
□ I dati sono specifici per utente? → Cache con chiave per utente
□ L'informazione deve essere real-time? → NON cachare (o TTL bassissimo)

LIVELLI DI CACHE:

  Browser → CDN → Application Cache → Database

  Browser cache (Cache-Control headers):
    - Asset statici: max-age=31536000, immutable
    - API: max-age=0, must-revalidate + ETag

  CDN cache (Cloudflare, CloudFront):
    - HTML pagine statiche
    - Asset con content hash nel filename
    - API pubbliche read-only

  Application cache (Redis):
    - Risultati di query frequenti
    - Sessioni utente
    - Feature flags / configurazioni
    - Rate limiting counters

  Database cache (query cache, materialized view):
    - Aggregazioni costose → materialized view con refresh periodico
    - NOT query cache di MySQL (deprecato e inefficiente)

INVALIDAZIONE CACHE — LA PARTE DIFFICILE:

  Strategie:
  1. TTL-based: scade dopo N secondi. Semplice ma stale possibile.
  2. Write-through: aggiorna cache ad ogni write. Costoso ma sempre fresh.
  3. Event-based: invalida la cache quando un evento rilevante accade.
  4. Version-based: cambia la cache key quando i dati cambiano.

  Regola d'oro: preferisci cache semplici con TTL corto piuttosto che
  cache complesse con invalidazione sofisticata.
```

---

## Problemi di Billing e Dunning

### Pagamenti Falliti — Workflow Completo

Il churn involontario (pagamenti falliti) rappresenta tipicamente il 20-40% del churn totale in un SaaS. È il churn più facile da ridurre.

```
SEQUENZA DUNNING CONSIGLIATA:

Giorno 0: Pagamento fallito
  → Retry automatico (Stripe retry intelligente)
  → Email 1: "Il tuo pagamento non è andato a buon fine"
  → Tono: informativo, non allarmante
  → CTA: "Aggiorna il metodo di pagamento"

Giorno 3: Secondo tentativo fallito
  → Retry automatico
  → Email 2: "Secondo tentativo fallito — azione richiesta"
  → Tono: urgenza leggera
  → CTA: "Aggiorna ora per non perdere l'accesso"

Giorno 7: Terzo tentativo fallito
  → Email 3: "Il tuo account sarà sospeso tra 7 giorni"
  → Tono: chiaro e diretto
  → Opzione: offrire metodo di pagamento alternativo
  → In-app banner: notifica persistente nell'interfaccia

Giorno 10: Quarto tentativo (ultimo)
  → Email 4: "Ultimo tentativo — 4 giorni alla sospensione"
  → SMS (se consenso e numero disponibile)
  → Outreach diretto per account high-value (> X€ MRR)

Giorno 14: Account sospeso
  → Sospendere l'accesso (non cancellare i dati)
  → Email 5: "Account sospeso — riattiva in qualsiasi momento"
  → Mantenere i dati per almeno 90 giorni

Giorno 30: Account cancellato
  → Email 6: "I tuoi dati saranno eliminati tra 60 giorni"
  → Offerta win-back: sconto o piano ridotto
```

**Configurazione Stripe per dunning ottimale**:

```
STRIPE BILLING SETTINGS CONSIGLIATI:

Smart Retries: Abilitato
  → Stripe usa ML per determinare il momento ottimale di retry

Retry Schedule personalizzato:
  retry_1: giorno 1 (automatico)
  retry_2: giorno 3
  retry_3: giorno 5
  retry_4: giorno 7

Customer Emails: Abilitati
  → Email automatica dopo ogni tentativo fallito

Subscription cancellation: dopo il 4° tentativo fallito
  → Impostare su "Mark as past due" (non cancellare subito)
  → Il tuo sistema gestisce la sospensione separatamente

Webhook da ascoltare:
  - invoice.payment_failed → trigger dunning email custom
  - customer.subscription.past_due → mostrare banner in-app
  - customer.subscription.deleted → cleanup e email finale
```

### Refund — Workflow e Policy

```
POLICY DI REFUND CONSIGLIATA:

Piano mensile:
  - Refund completo entro 7 giorni dall'acquisto (no questions asked)
  - Refund proporzionale entro 30 giorni (caso per caso)
  - Nessun refund dopo 30 giorni (solo credito)

Piano annuale:
  - Refund completo entro 14 giorni dall'acquisto
  - Refund proporzionale per i mesi non usati entro 90 giorni
  - Nessun refund dopo 90 giorni (ma possibilità di downgrade)

PROCESSO DI REFUND:
  1. Ticket ricevuto → classificare motivo
  2. Verificare eligibilità (timeline, policy)
  3. Se eligible → processare via Stripe Refund API
  4. Se non eligible → offrire alternativa (credito, piano diverso)
  5. Sempre: chiedere il motivo → alimentare l'exit survey

ESCALATION:
  - Importo < €100 → agente CS può approvare
  - Importo €100-500 → CS Manager approva
  - Importo > €500 → Finance approva
  - Dispute/chargeback → seguire il processo dispute
```

### Dispute e Chargeback

```
PROCESSO DI GESTIONE CHARGEBACK:

1. ALLARME (giorno 0)
   Stripe webhook: charge.dispute.created
   → Notifica immediata a CS + Finance

2. RACCOGLIERE EVIDENZE (giorni 1-3)
   □ Log di accesso dell'utente (ha usato il servizio?)
   □ Ricevute email (è stato informato dell'addebito?)
   □ Terms of Service accettati (timestamp di accettazione)
   □ Comunicazioni precedenti con il cliente
   □ Evidenza di utilizzo del servizio (screenshot, export dati)

3. RISPONDERE (entro 7 giorni dalla notifica)
   # Via Stripe Dashboard o API
   # Includere tutte le evidenze raccolte
   # Tono professionale e fattuale

4. PREVENZIONE FUTURA
   □ Descriptor chiaro sulla carta (il cliente deve riconoscere l'addebito)
   □ Email di conferma ad ogni transazione
   □ Refund proattivo se il cliente contatta prima del chargeback
   □ 3D Secure / SCA per transazioni ad alto rischio
   □ Monitorare il chargeback rate (Visa: < 0.9%, Mastercard: < 1.0%)

COSTO DI UN CHARGEBACK:
  - Fee Stripe: €15 per dispute (non rimborsabile anche se si vince)
  - Chargeback rate alto → rischio di essere classificati high-risk
  - High-risk → fee più alte o account Stripe sospeso
```

---

## Workflow di Escalation Clienti

### Modello di Supporto a Tier

```
TIER 1 — FRONT LINE (risposta iniziale)
  Chi: agenti CS junior, chatbot, knowledge base
  Cosa risolvono:
    - Domande sull'uso del prodotto
    - Reset password, problemi di accesso
    - Billing questions di base (ricevute, piani)
    - Bug noti con workaround documentato
  SLA: risposta entro 4h (business hours)
  Escalation: se non risolto entro 2 interazioni → Tier 2

TIER 2 — SPECIALIST (investigazione)
  Chi: agenti CS senior, support engineer
  Cosa risolvono:
    - Bug non documentati (riproducibili)
    - Problemi di configurazione complessi
    - Billing issues che richiedono indagine
    - Richieste di refund fuori policy standard
    - Clienti frustrati/arrabbiati
  SLA: risposta entro 2h, risoluzione entro 24h
  Escalation: se richiede fix nel codice → Engineering
                se cliente a rischio churn → Tier 3

TIER 3 — ACCOUNT MANAGEMENT (relazione)
  Chi: CS Manager, Account Executive
  Cosa risolvono:
    - Clienti enterprise a rischio churn
    - Negoziazioni contrattuali
    - Richieste custom (integrazioni, SLA dedicato)
    - Incidenti che impattano clienti high-value
  SLA: risposta entro 1h, follow-up entro 4h
  Escalation: se richiede decisione exec → Leadership

ENGINEERING ESCALATION
  Chi: team engineering (bug fix, hotfix)
  Quando:
    - Bug confermato senza workaround
    - Problema di performance impattante
    - Security issue
  SLA: P1 entro 4h, P2 entro 24h, P3 entro 1 sprint
```

### Matrice di Escalation

| Situazione | Primo punto | Escalation | Tempo max |
|------------|------------|------------|-----------|
| Domanda prodotto | Tier 1 (KB/Bot) | Tier 1 umano | 4h |
| Bug con workaround | Tier 1 | Tier 2 se workaround non funziona | 8h |
| Bug senza workaround | Tier 2 | Engineering | 24h |
| Billing errato | Tier 1 | Tier 2 + Finance | 24h |
| Chargeback | Tier 2 + Finance | CS Manager | 48h (submit evidenze entro 7gg) |
| Cliente furioso | Tier 1 → Tier 2 | CS Manager (Tier 3) | 2h |
| Enterprise a rischio | CS Manager | VP CS + Account Exec | 4h |
| Data breach sospetta | Tier 2 | Security + CTO + Legal | Immediato |
| Outage > 30 min | On-call engineer | IC + CTO | 15 min |

### Gestione del Cliente Arrabbiato

```
FRAMEWORK: HEAR

H — HEAR (ascolta):
  - Lascia sfogare senza interrompere
  - Prendi appunti sul problema specifico
  - Non metterti sulla difensiva

E — EMPATHIZE (empatizza):
  - "Capisco la frustrazione, questo non dovrebbe succedere"
  - "Se fossi nella sua situazione, sarei altrettanto deluso"
  - NON: "Mi dispiace SE ha avuto un problema" (invalida l'esperienza)

A — ACT (agisci):
  - Proponi un'azione concreta e specifica
  - "Ecco cosa faccio adesso: [azione]"
  - "E entro [timeline], avrà [risultato]"
  - Se non puoi risolvere, escala con trasparenza

R — RESOLVE & FOLLOW UP (risolvi e segui):
  - Risolvi il problema come promesso
  - Follow-up proattivo: "Volevo assicurarmi che sia tutto ok"
  - Documenta il caso per prevenire ricorrenze

ESCALATION AUTOMATICA:
  Se il cliente usa tono aggressivo per la terza volta → escalare a manager
  Se minaccia azioni legali → coinvolgere Legal
  Se minaccia danni reputazionali (stampa, social) → CS Manager + Comms
```

### SLA — Definizione e Monitoring

```
SLA PER TIER DI SERVIZIO:

┌─────────────┬────────────┬───────────────┬──────────────┐
│             │ Free/Hobby │ Professional  │ Enterprise   │
├─────────────┼────────────┼───────────────┼──────────────┤
│ Uptime      │ 99.5%      │ 99.9%         │ 99.95%       │
│ Supporto    │ Email only │ Email + chat  │ Dedicato     │
│ Risposta P1 │ Best effort│ < 4h          │ < 1h         │
│ Risposta P2 │ Best effort│ < 8h          │ < 4h         │
│ Risposta P3 │ < 48h      │ < 24h         │ < 8h         │
│ Canali      │ Email      │ Email, chat   │ Slack, phone │
│ Business hrs│ Lun-Ven    │ Lun-Ven       │ 24/7         │
└─────────────┴────────────┴───────────────┴──────────────┘

COME CALCOLARE L'UPTIME:
  Uptime % = ((tempo_totale - downtime) / tempo_totale) * 100

  99.9% = max ~43 minuti di downtime al mese
  99.95% = max ~22 minuti di downtime al mese
  99.99% = max ~4.3 minuti di downtime al mese

  Excluded: manutenzione programmata (con preavviso > 48h)
  Included: tutto il resto (anche "parzialmente degradato")

COSA SUCCEDE SE SI VIOLA LO SLA:
  - Credit proporzionale al downtime (tipicamente 10x il periodo down)
  - Esempio: SLA 99.9%, downtime effettivo 99.5% nel mese
    → Credit = 5% della fattura mensile (o secondo contratto)
  - I crediti sono calcolati sull'MRR del cliente, non su tutta la revenue
```

---

## Pattern dei Ticket di Supporto

### Classificazione e Triage Automatico

```
TASSONOMIA DEI TICKET:

Categoria L1:
  ├── bug             → Team Engineering
  ├── feature-request → Team Product
  ├── billing         → Team Finance/CS
  ├── how-to          → Team CS (o Knowledge Base)
  ├── account         → Team CS
  ├── security        → Team Security
  └── feedback        → Team Product

Priorità (calcolata automaticamente):
  P1: "blocca il lavoro" + piano Enterprise
  P2: "blocca il lavoro" + piano Pro / OR "funzionalità degradata" + Enterprise
  P3: "funzionalità degradata" + Pro / OR qualsiasi Free
  P4: "cosmetico" / "nice to have" / feature request

Auto-tag basato su keyword:
  "non riesco ad accedere" → categoria: account, tag: login
  "errore" + "pagamento" → categoria: billing, tag: payment-failure
  "lento" / "impiega troppo" → categoria: bug, tag: performance
  "vorrei" / "sarebbe utile" → categoria: feature-request
  "GDPR" / "dati" / "cancellare" → categoria: account, tag: data-request
```

### Pattern Ricorrenti e Template di Risposta

**Pattern 1: "Non riesco ad accedere"**

```
DIAGNOSI RAPIDA:
  1. L'utente esiste? → Cercare per email nel CRM
  2. Ha confermato l'email? → Controllare stato account
  3. Password resettata di recente? → Link di reset potrebbe essere scaduto
  4. 2FA attivo? → Potrebbe aver perso il device
  5. IP bloccato dal rate limiter? → Controllare WAF/rate limit logs

TEMPLATE RISPOSTA:
  "Ciao [Nome],

  ho verificato il tuo account e [diagnosi specifica].

  Per risolvere:
  1. [Azione specifica — es: clicca su questo link di reset password]
  2. [Se il problema persiste, passo successivo]

  Se il problema persiste dopo questi passaggi, rispondimi
  e investigherò ulteriormente.

  [Firma]"
```

**Pattern 2: "La feature X non funziona"**

```
DIAGNOSI RAPIDA:
  1. Qual è il comportamento atteso vs quello reale?
  2. È riproducibile? (browser, device, orario)
  3. C'è stato un deploy recente? (controllare changelog)
  4. Bug noto? (cercare nel bug tracker)
  5. Specifico dell'account o generale?

TEMPLATE PER RACCOGLIERE INFO:
  "Ciao [Nome],

  grazie per aver segnalato il problema. Per investigare, ho bisogno di:

  1. Cosa stavi cercando di fare? (descrivere il flusso passo per passo)
  2. Cosa è successo invece?
  3. Browser e sistema operativo che stai usando
  4. Uno screenshot o video del problema (se possibile)
  5. Succede ogni volta o solo a volte?

  [Firma]"
```

**Pattern 3: "Voglio cancellare il mio account / i miei dati"**

```
PROCESSO (GDPR/Privacy compliant):
  1. Verificare identità del richiedente
  2. Classificare la richiesta:
     a) Cancellazione account → procedura standard
     b) Data export (portabilità) → export JSON/CSV
     c) Cancellazione dati (diritto all'oblio) → procedura data deletion

  3. Timeline di risposta: max 30 giorni (GDPR)
  4. Documentare la richiesta con data e azioni

TEMPLATE RISPOSTA:
  "Ciao [Nome],

  ho ricevuto la tua richiesta di [cancellazione/export dati].

  Prima di procedere, ti informo che:
  - [Cancellazione] Tutti i tuoi dati saranno eliminati permanentemente
    entro 30 giorni. Questa azione non è reversibile.
  - [Export] Riceverai un file con tutti i tuoi dati entro 7 giorni.

  Per procedere, confermami rispondendo a questa email con:
  'Confermo la richiesta di [cancellazione/export] per l'account [email].'

  [Firma]"
```

### Metriche del Supporto da Monitorare

| Metrica | Target | Red Flag |
|---------|--------|----------|
| First Response Time (FRT) | < 4h (business hours) | > 24h |
| Time to Resolution (TTR) | < 24h per P1-P2 | > 72h |
| First Contact Resolution (FCR) | > 70% | < 50% |
| CSAT del supporto | > 4.2 / 5 | < 3.5 |
| Ticket per 100 clienti | < 15/mese | > 30/mese |
| Ticket reopen rate | < 10% | > 20% |
| KB deflection rate | > 30% | < 10% |

---

## Crisi e Recovery

### Crisi di Crescita (MRR stagnante)

**Diagnosi rapida**: dove si è rotto il funnel? (vedi albero decisionale sopra)

**Azioni a breve termine (1-4 settimane)**:
1. Aumentare i prezzi (il modo più rapido per aumentare MRR senza nuovi clienti)
2. Campagna di expansion sui clienti esistenti (upsell, cross-sell)
3. Reactivation campaign sui clienti churnati
4. Referral push (chiedere ai promotori NPS di referire)

**Azioni a medio termine (1-3 mesi)**:
1. Ottimizzare il funnel (la fase con la conversione più bassa)
2. Lanciare un nuovo canale di acquisizione
3. Revisione pricing/packaging

### Crisi di Cash (runway < 6 mesi)

**Azioni immediate**:
1. Tagliare le spese non essenziali (tool, perks, ufficio)
2. Revenue-based financing o bridge round per estendere il runway
3. Offerte annuali con sconto aggressivo (cash upfront)
4. Rinegoziare i contratti con fornitori

**Azioni strutturali**:
1. Ridurre il team alle funzioni essenziali (doloroso ma necessario)
2. Focalizzarsi su 1 canale di acquisizione (il più efficiente)
3. Aumentare i prezzi
4. Eliminare le feature/prodotti non profittevoli

### Crisi di Prodotto (incident grave / data breach)

**Azioni immediate**: vedi Incident Response nella sezione [Incident Management](#incident-management).

**Comunicazione**: essere trasparenti, rapidi e specifici. Cosa è successo, quando, chi è impattato, cosa stiamo facendo, cosa devono fare i clienti.

### Crisi di Reputazione

**Scenario**: review negative virali, post social che denuncia il prodotto, articolo di stampa negativo.

```
FRAMEWORK DI RISPOSTA:

ORA 1 — ASSESS:
  □ Cosa è stato detto e dove?
  □ È fattualmente corretto?
  □ Qual è il reach potenziale? (follower, viralità)
  □ C'è un problema reale da risolvere o è un malinteso?

ORA 2-4 — RESPOND:
  □ Se c'è un problema reale:
    → Riconoscere pubblicamente
    → Descrivere cosa si sta facendo per risolverlo
    → Timeline per la risoluzione
    → NON cancellare critiche (effetto Streisand)
  □ Se è un malinteso:
    → Chiarire con fatti e dati
    → Tono calmo e professionale
    → Offrire una conversazione privata

GIORNO 1-3 — FOLLOW THROUGH:
  □ Risolvere il problema sottostante
  □ Aggiornare pubblicamente sul progresso
  □ Contattare direttamente le persone più vocali
  □ Pubblicare il post-mortem se rilevante

LUNGO TERMINE:
  □ Monitorare le menzioni (Google Alerts, Mention)
  □ Costruire capitale reputazionale con contenuti di valore
  □ Coltivare relazioni con advocate e power user
```

### Crisi di Team (key person leaving, burnout generalizzato)

```
PERDITA DI UNA KEY PERSON:

Immediato:
  □ Documentazione: cosa sa solo questa persona?
  □ Handoff plan: chi prende cosa?
  □ Accessi: trasferire ownership di account e servizi
  □ Comunicazione: informare il team senza creare panico

Settimane 1-4:
  □ Redistribuire le responsabilità
  □ Identificare i gap di competenza critici
  □ Iniziare il recruiting (se necessario)
  □ Documentare i processi che erano "nella testa" della persona

Prevenzione:
  □ Bus factor > 1 per ogni area critica
  □ Documentazione operativa aggiornata
  □ Cross-training regolare
  □ Runbook per ogni processo critico

─────────────────────────────────────────────

BURNOUT DI TEAM:

Segnali:
  - Produttività in calo costante
  - Cinismo e disimpegno in aumento
  - Turnover in crescita
  - Qualità del lavoro in calo

Azioni:
  □ Riconoscere il problema pubblicamente
  □ Ridurre il carico (meno progetti paralleli)
  □ Dare ownership e autonomia (non solo task)
  □ Tempo protetto per deep work (no-meeting days)
  □ Celebrare i risultati (anche piccoli)
  □ Valutare se il ritmo è sostenibile a lungo termine
```

---

## Anti-Pattern Operativi

### Anti-Pattern 1: "Deploy Friday" (Deploy il Venerdì Pomeriggio)

```
DESCRIZIONE:
  Deployare feature significative il venerdì pomeriggio, quando il team
  non è disponibile nel weekend per gestire problemi.

PERCHÉ È SBAGLIATO:
  - Bug in produzione scoperti nel weekend senza nessuno a fixarli
  - Tempo di risoluzione 10x più lungo (weekend + reperibilità)
  - Stress e burnout per chi è on-call nel weekend

COSA FARE INVECE:
  - Deploy significativi: lunedì-giovedì, mattina
  - Venerdì: solo fix critici o deploy con feature flag off
  - Weekend: solo hotfix P1 pre-approvati
```

### Anti-Pattern 2: "Hero Culture" (La Cultura dell'Eroe)

```
DESCRIZIONE:
  Una sola persona conosce un sistema critico, lavora 70h/settimana,
  e "salva la situazione" durante ogni incidente.

PERCHÉ È SBAGLIATO:
  - Bus factor = 1 (se l'eroe si ammala, tutto si ferma)
  - L'eroe brucia e va via (portando tutta la conoscenza)
  - Il team non cresce perché non viene coinvolto
  - Incentiva il non documentare (l'eroe è indispensabile)

COSA FARE INVECE:
  - Cross-training obbligatorio su ogni sistema critico
  - Pair programming per trasferire conoscenza
  - Runbook scritti per ogni procedura operativa
  - Rotazione on-call che include tutti gli engineer
  - Bus factor minimo = 2 per ogni componente
```

### Anti-Pattern 3: "Swallow the Error" (Ingoiare gli Errori)

```
DESCRIZIONE:
  Ignorare, sopprimere o loggare senza agire sugli errori in produzione.
  Esempio classico: try/catch vuoto, o log.error senza alerting.

PERCHÉ È SBAGLIATO:
  - I problemi piccoli diventano grandi senza che nessuno se ne accorga
  - I clienti trovano i bug prima del team
  - Perdita di fiducia quando l'errore diventa visibile

COSA FARE INVECE:
  - Ogni errore loggato deve avere un livello di severità
  - Errori critici → allarme immediato
  - Errori ricorrenti → ticket automatico
  - Dashboard errori visibile a tutto il team
  - Budget di errore: se supera la soglia → stop feature, fix errori
```

### Anti-Pattern 4: "Config by Memory" (Configurazione a Memoria)

```
DESCRIZIONE:
  Le configurazioni di produzione sono nella testa di una persona,
  non documentate, non versionabili, modificate manualmente.

PERCHÉ È SBAGLIATO:
  - Impossibile replicare l'ambiente
  - Impossibile fare rollback di una modifica config
  - Disaster recovery fallisce perché nessuno sa come riconfigurare
  - Audit impossibile (chi ha cambiato cosa e quando?)

COSA FARE INVECE:
  - Infrastructure as Code (Terraform, Pulumi)
  - Config in repo versionato (con segreti separati in vault)
  - Nessuna modifica manuale in produzione (tutto via pipeline)
  - Documentare PERCHÉ una config ha un certo valore, non solo il valore
```

### Anti-Pattern 5: "Metrics Theater" (Teatro delle Metriche)

```
DESCRIZIONE:
  Tracciare decine di metriche ma non agire su nessuna. Dashboard
  bellissime che nessuno guarda. Report settimanali che nessuno legge.

PERCHÉ È SBAGLIATO:
  - Falsa sensazione di controllo
  - Tempo speso a produrre report invece che a risolvere problemi
  - Le metriche importanti si perdono nel rumore

COSA FARE INVECE:
  - 3-5 KPI core per fase (non 30)
  - Ogni KPI ha una soglia di allarme e un owner
  - Review settimanale di 15 minuti (non 2 ore)
  - Se una metrica non porta a un'azione → smettere di traccarla
```

### Anti-Pattern 6: "Build Everything" (Costruire Tutto Internamente)

```
DESCRIZIONE:
  Costruire internamente ogni componente (billing, email, analytics,
  auth) invece di usare servizi specializzati.

PERCHÉ È SBAGLIATO:
  - Tempo di sviluppo sottratto al core product
  - Manutenzione permanente di sistemi non-core
  - Qualità inferiore rispetto a servizi specializzati
  - Costo reale molto più alto del costo SaaS del servizio

COSA FARE INVECE:
  - Build: solo il core product (il differenziatore)
  - Buy: billing (Stripe), email (SendGrid), auth (Auth0/Clerk),
    monitoring (Datadog/Sentry), analytics (Mixpanel/PostHog)
  - Regola: se non è il motivo per cui i clienti ti pagano, compralo
```

### Anti-Pattern 7: "Silent Deploy" (Deploy Silenzioso)

```
DESCRIZIONE:
  Deployare senza notificare il team, senza changelog, senza verifica
  post-deploy. "È solo un fix piccolo, non serve dirlo a nessuno."

PERCHÉ È SBAGLIATO:
  - Il CS non sa cosa è cambiato → non può supportare i clienti
  - Un altro ingegnere deploya sopra → conflitto o regressione
  - Se qualcosa si rompe, nessuno sa che c'è stato un deploy

COSA FARE INVECE:
  - Notifica automatica in Slack per ogni deploy (#deploys)
  - Changelog interno (anche 1 riga) per ogni release
  - Post-deploy smoke test obbligatorio
  - Tag il deploy con timestamp per facile correlazione con incidenti
```

### Anti-Pattern 8: "Support as Afterthought" (Supporto come Ripensamento)

```
DESCRIZIONE:
  Il supporto clienti è l'ultima priorità. Nessun knowledge base,
  nessun template, risposte lente, nessun feedback loop con Product.

PERCHÉ È SBAGLIATO:
  - Churn evitabile perché i clienti non trovano risposte
  - Insight preziosi persi (i ticket sono la voce del cliente)
  - Costo del supporto cresce linearmente invece di scendere
  - Reputazione danneggiata (review negative)

COSA FARE INVECE:
  - Knowledge base prima del lancio (top 10 domande)
  - Template di risposta per i pattern comuni
  - Feedback loop: ticket ricorrenti → Product backlog
  - CS coinvolto nel design di nuove feature (voice of customer)
  - Metriche di supporto tracciate e reviewate
```

### Anti-Pattern 9: "Infinite Trial" (Trial Infinito)

```
DESCRIZIONE:
  Il trial non ha scadenza reale, oppure è così generoso che nessuno
  ha motivo di pagare.

PERCHÉ È SBAGLIATO:
  - Nessuna urgenza di conversione → trial eterno
  - Utenti che usano il prodotto gratis senza mai pagare
  - CAC payback tende a infinito
  - Carico infrastrutturale senza revenue

COSA FARE INVECE:
  - Trial con scadenza chiara (7-14 giorni per low-touch, 30 per enterprise)
  - Limitazioni significative nel trial (non tutte le feature)
  - Comunicazione chiara del valore premium
  - Triggered email a metà e fine trial
  - CTA prominente per convertire
```

### Anti-Pattern 10: "Data Hoarding" (Accumulare Dati senza Policy)

```
DESCRIZIONE:
  Salvare tutto per sempre senza policy di retention, senza
  classificazione, senza compliance check.

PERCHÉ È SBAGLIATO:
  - Costi di storage che crescono senza limite
  - Rischio GDPR/privacy (dati che dovresti aver cancellato)
  - Performance del DB che degrada su tabelle enormi
  - Backup sempre più lenti e costosi

COSA FARE INVECE:
  - Data retention policy scritta (es: log 90gg, analytics 2 anni)
  - Classificazione dati (PII, business, operativo)
  - Archivio cold storage per dati vecchi ma necessari
  - Cancellazione automatica per dati oltre la retention
  - Partitioning delle tabelle per data
```

---

## Case Study Reali

### Case Study 1: "Il SaaS che è cresciuto troppo in fretta"

**Contesto**: SaaS B2B per project management, 50 clienti paganti, $15K MRR. Dopo un articolo virale su un blog tech, riceve 2.000 signup in 24 ore (contro una media di 10/giorno).

**Cosa è andato storto**:
1. Il database PostgreSQL ha raggiunto il 100% CPU per le query di onboarding
2. Il server di email ha superato il rate limit di SendGrid (100 email/sec sul piano base)
3. Il file storage (S3) ha funzionato, ma il resize delle immagini profilo (fatto synchronously) ha creato timeout
4. Il team di 3 persone non aveva un piano di scaling

**Timeline dell'incidente**:
```
09:00 UTC — Articolo pubblicato
09:45 UTC — Primi segnali: latenza API sale a 3s (da 200ms baseline)
10:15 UTC — Primo alert PagerDuty: CPU DB al 90%
10:30 UTC — CTO (unico engineer on-call) svegliato da alert
10:45 UTC — Diagnostica: query di creazione workspace senza indice
            su tabella workspaces.slug (check unicità per ogni signup)
11:00 UTC — Hotfix: aggiunto indice su workspaces.slug
11:15 UTC — CPU DB scende al 60%, ma email queue a 5.000 pendenti
11:30 UTC — Upgrade piano SendGrid (da Basic a Pro)
11:45 UTC — Spostato image resize su job asincrono (placeholder temporaneo)
12:30 UTC — Servizio stabilizzato, latenza API < 500ms
```

**Root cause**: mancanza di indice database + operazione sincrona pesante nel signup flow + nessun piano di scaling.

**Lezioni apprese**:
1. **Load test prima di qualsiasi campagna marketing** — anche un test con 10x il traffico avrebbe rivelato i problemi
2. **Le operazioni pesanti devono essere asincrone** — mai image processing, email sending, o calcoli complessi nel request cycle
3. **Avere un runbook di scaling** anche se "siamo piccoli" — il traffico virale non avvisa
4. **L'indice mancante è il bug di performance più comune** — review periodica degli slow query log

**Risultato finale**: dei 2.000 signup, ~1.400 hanno completato l'onboarding (gli altri hanno trovato il sito lento e se ne sono andati). Conversion rate 4% (56 clienti paganti dal boom). Il team ha poi implementato autoscaling e async job queue.

---

### Case Study 2: "Il pricing che ha quasi ucciso il prodotto"

**Contesto**: SaaS per email marketing, posizionato come alternativa economica a Mailchimp. Pricing: Free fino a 500 contatti, poi $9/mese fino a 5.000, poi $29/mese fino a 25.000.

**Il problema**: dopo 18 mesi, il SaaS ha 800 clienti paganti ma:
- MRR: $12.400 (ARPU: $15.50)
- CAC: $180 (fully loaded, includendo il fondatore che fa sales)
- LTV: $310 (churn mensile del 5%)
- LTV:CAC = 1.7:1 (insufficiente — target > 3:1)

**Diagnosi** (processo di pricing review):

1. **Distribuzione per piano**: 78% dei clienti sul piano $9, 19% sul piano $29, 3% enterprise custom
2. **Feature usage**: i clienti $29 usano automation e A/B testing — feature che richiedono il 60% del costo infrastruttura
3. **Van Westendorp survey** (73 risposte):
   - "Troppo economico per essere serio": $5
   - "Buon affare": $19
   - "Caro ma accettabile": $35
   - "Troppo caro": $59
4. **Competitor pricing**: Mailchimp $20 per 500 contatti, ConvertKit $29 per 1.000

**Azione — nuovo pricing**:

| Piano | Prezzo Vecchio | Prezzo Nuovo | Cambiamento |
|-------|---------------|-------------|-------------|
| Free | Fino a 500 contatti | Fino a 250 contatti | -50% contatti |
| Starter | $9 / 5.000 | $19 / 2.500 | +111% prezzo, -50% contatti |
| Growth | $29 / 25.000 | $49 / 10.000 | +69% prezzo |
| Pro | N/A | $99 / 50.000 + automation | Nuovo piano |

**Implementazione**:
- Grandfathering: clienti esistenti mantengono il vecchio prezzo per 12 mesi
- Comunicazione 60 giorni prima del cambio per i nuovi clienti
- A/B test del nuovo pricing per 30 giorni su nuovi visitatori

**Risultato a 6 mesi**:
- MRR: da $12.400 a $28.600 (+131%)
- Nuovi clienti ARPU: da $15.50 a $38
- Churn mensile: invariato (i clienti non churnano per prezzo se il valore c'è)
- LTV:CAC: da 1.7:1 a 3.8:1

**Lezione**: il prezzo basso non è un vantaggio competitivo — è un segnale di bassa fiducia nel proprio prodotto. I clienti sono disposti a pagare di più se il valore è chiaro.

---

### Case Study 3: "L'incidente che ha cambiato la cultura operativa"

**Contesto**: SaaS B2B per gestione HR, 200 clienti enterprise, $180K MRR. Un deploy routinario alle 17:30 di venerdì (anti-pattern classico) introduce un bug nella gestione dei permessi.

**Cosa è successo**:
- Il bug permette a qualsiasi utente di un'organizzazione di vedere i dati salariali di tutti i colleghi (normalmente visibili solo a HR/management)
- Un utente nota il problema alle 22:00 e lo segnala via email di supporto
- L'email non viene letta fino a lunedì mattina
- Per tutto il weekend, i dati salariali sono esposti a utenti non autorizzati
- Lunedì alle 09:15, il team CS legge l'email e escala immediatamente
- Fix deployato alle 10:45 di lunedì

**Impatto**:
- 47 organizzazioni potenzialmente impattate (quelle che hanno avuto login nel weekend)
- 12 organizzazioni con accesso effettivo ai dati salariali da utenti non autorizzati
- 3 clienti enterprise hanno cancellato il contratto
- Revenue persa: $8.200 MRR (~$98K ARR)
- Costo legale: €15.000 (consultazione GDPR)
- Danno reputazionale: 2 post su LinkedIn con 50K+ impression

**Post-mortem — root cause (5 perché)**:
1. Perché i dati salariali erano visibili? → Bug nel middleware di autorizzazione
2. Perché il bug è passato? → Il test di permessi non copriva questo scenario
3. Perché non è stato trovato prima del deploy? → Nessun test di regressione sui permessi
4. Perché non è stato corretto nel weekend? → Nessun monitoring on-call il weekend
5. Perché deployato venerdì sera? → Nessuna policy di deploy window

**Action item implementati**:
1. **Policy di deploy**: no deploy dopo le 15:00 del venerdì. Mai.
2. **Test di autorizzazione**: suite di test dedicata per ogni ruolo × ogni risorsa
3. **On-call 24/7**: rotazione on-call con PagerDuty, risposta P1 < 15 min
4. **Data access audit**: log di ogni accesso a dati sensibili con alert su pattern anomali
5. **Canary deploy**: ogni deploy parte dal 5% degli utenti con monitoring di 30 min
6. **Incident response drill**: simulazione trimestrale di incidente P1

**Lezione**: un deploy il venerdì sera senza monitoring weekend trasforma un bug di 2 ore in una crisi di 3 giorni. Le policy operative non sono burocrazia — sono protezione.

---

### Case Study 4: "La feature che nessuno usava costava €4.000/mese"

**Contesto**: SaaS per analytics e-commerce. Il team ha costruito un sistema di "report personalizzati" con drag-and-drop, esportazione PDF e scheduling automatico. Sviluppo: 4 mesi, 2 engineer full-time.

**Il problema** (scoperto durante un audit trimestrale):
- Feature usage: 3.2% degli utenti attivi
- Costo infrastruttura: €4.200/mese (generazione PDF + storage + cron jobs)
- Ticket di supporto: 18% di tutti i ticket legati a questa feature
- Nessun utente l'ha mai menzionata come motivo per iscriversi

**Analisi costi-benefici**:

| Voce | Costo mensile |
|------|--------------|
| Infrastruttura (Lambda + S3 + workers) | €2.800 |
| Supporto (18% dei ticket × costo agente) | €900 |
| Manutenzione engineering (bug fix) | €500 |
| **Totale** | **€4.200/mese** |

Revenue attribuibile: €0 (nessun piano differenziato sulla feature, tutti i piani la includono).

**Azione**:
1. Comunicazione agli utenti attivi della feature (12 persone) — 30 giorni di preavviso
2. Offerta di export CSV come alternativa (costo infra: ~€50/mese)
3. Rimozione graduale: prima lo scheduling, poi il PDF, infine il builder
4. Redirect dei 2 engineer su feature core richieste da 40% degli utenti

**Risultato**:
- 0 clienti persi per la rimozione della feature
- €4.150/mese risparmiati = €49.800/anno
- 2 engineer riassegnati → nuova feature che ha aumentato la retention del 15%

**Lezione**: misurare l'usage di ogni feature è fondamentale. Le feature zombie costano in infrastruttura, supporto e manutenzione — e distraggono dal valore core.

---

## Template e Strumenti Operativi

### Weekly Team Meeting (60 min)

```
AGENDA:
  1. Metriche della settimana (10 min)
     → MRR, new customers, churn, activation rate
     → Anomalie da investigare

  2. Priority update per team (20 min)
     → Engineering: cosa è stato rilasciato, cosa è bloccato
     → Sales: pipeline, deal importanti, win/loss
     → CS: churn risk, expansion opportunity
     → Marketing: lead gen, content, campaigns

  3. Customer spotlight (10 min)
     → 1 feedback positivo + 1 feedback negativo della settimana
     → Cosa impariamo?

  4. Blockers e decisioni (15 min)
     → Cosa è bloccato e serve una decisione?
     → Decidere o assegnare ownership

  5. Priorità prossima settimana (5 min)
     → 1-3 priorità per team
```

### Monthly Metrics Review (90 min)

```
AGENDA:
  1. Financial review (20 min)
     → MRR waterfall (new, expansion, contraction, churn)
     → Burn rate, runway
     → Revenue vs plan

  2. Funnel review (20 min)
     → Conversion rate per fase (vs mese precedente)
     → Collo di bottiglia identificato
     → Azioni correttive

  3. Cohort review (20 min)
     → Retention per cohort (migliorando o peggiorando?)
     → Revenue per cohort (expansion o contraction?)
     → Segmentation insight

  4. Product review (15 min)
     → Feature usage e adoption
     → NPS/CSAT trend
     → Roadmap vs outcome

  5. Action items (15 min)
     → 3-5 azioni specifiche con owner e deadline
```

### Template Incident Report (per Comunicazione Esterna)

```
═══════════════════════════════════════════════
INCIDENT REPORT — [Nome Servizio]
═══════════════════════════════════════════════

Data: YYYY-MM-DD
Durata: HH:MM → HH:MM UTC (X minuti/ore)

SUMMARY:
[Cosa è successo in 2-3 frasi comprensibili a un non-tecnico]

IMPATTO:
[Quali funzionalità sono state impattate, per chi, per quanto tempo]

TIMELINE:
[Timeline semplificata dei momenti chiave — non troppo tecnica]

ROOT CAUSE:
[Spiegazione comprensibile della causa — senza jargon eccessivo]

COSA ABBIAMO FATTO:
[Azioni intraprese per risolvere e per prevenire]

PROSSIMI PASSI:
[Miglioramenti pianificati per evitare che si ripeta]

CI SCUSIAMO:
[Riconoscimento dell'impatto, impegno per il miglioramento]
```

### Template per Feature Request Evaluation

```
FEATURE REQUEST EVALUATION

Nome feature: ______________
Richiedente: ______________ (cliente/interno)
Data richiesta: YYYY-MM-DD

1. IMPATTO (1-5):
   □ Quanti clienti la chiedono? ____ (fonte: ticket/survey/interviste)
   □ Impatta quale segmento? (Free / Pro / Enterprise)
   □ È un deal-blocker per prospect? (sì/no, quanti deal)
   □ Ridurrebbe il churn? (sì/no, stima)

2. SFORZO (1-5):
   □ Engineering effort: ____ settimane-persona
   □ Richiede infra nuova? (sì/no)
   □ Impatta codice esistente? (isolata / intrusiva)
   □ Richiede documentazione/training?

3. ALLINEAMENTO STRATEGICO (1-5):
   □ Allineata alla value proposition?
   □ Rafforza il moat competitivo?
   □ Abilita nuove revenue (upsell/nuovo segmento)?

4. SCORE: Impatto × Allineamento / Sforzo = _____

5. DECISIONE:
   □ Build it — Sprint ___
   □ Later — Q___
   □ Not now — motivo: ___
   □ Never — motivo: ___
```

---

## FAQ — Domande Frequenti

### 1. Quanto costa lanciare un SaaS da zero?

Dipende dalla complessità, ma un MVP realistico richiede:

| Voce | Costo bootstrap | Costo funded |
|------|----------------|-------------|
| Dominio + hosting | €20-100/mese | €200-2.000/mese |
| Stripe fees | 2.9% + €0.25/transazione | Uguale |
| Tool (analytics, email, support) | €0-100/mese (free tier) | €500-2.000/mese |
| Sviluppo | €0 (se fondatore dev) | €5.000-30.000/mese |
| Legal (ToS, Privacy) | €500-2.000 una tantum | €3.000-10.000 |
| **Totale anno 1 (bootstrap)** | **€3.000-15.000** | **€100.000-400.000** |

### 2. Quanto tempo ci vuole per raggiungere il Product-Market Fit?

La mediana è 18-24 mesi per B2B SaaS. Segnali di PMF:
- Retention > 80% a 6 mesi
- NPS > 40
- I clienti iniziano a riferirti spontaneamente
- La crescita accelera senza proporzionale aumento di spend

### 3. Meglio freemium o free trial?

| | Freemium | Free Trial |
|---|---------|-----------|
| **Pro** | Base utenti ampia, viralità | Urgenza di conversione |
| **Contro** | Molti free user, bassa conversione | Meno viralità |
| **Quando** | PLG, prodotto virale, low ARPU | Sales-led, high ARPU, B2B enterprise |
| **Conversion rate tipico** | 2-5% free→paid | 15-25% trial→paid |

### 4. Qual è il churn rate accettabile?

| Segmento | Churn mensile accettabile | Churn annuale implicito |
|----------|--------------------------|------------------------|
| SMB (< €50/mese) | < 5% | < 46% |
| Mid-market (€50-500/mese) | < 3% | < 31% |
| Enterprise (> €500/mese) | < 1% | < 11% |

Se il churn è fuori range, è il problema numero 1 da risolvere prima di tutto il resto.

### 5. Quando passare da self-serve a sales-assisted?

Quando il tuo ACV supera €3.000-5.000/anno, il ciclo di vendita diventa abbastanza lungo da giustificare un touch umano. Segnali:
- I prospect chiedono demo
- Il trial conversion rate è basso ma il prodotto piace
- I deal enterprise richiedono personalizzazione

### 6. Come gestire la prima assunzione (non founder)?

Priorità tipica:
1. **Engineer** (se il fondatore non è tecnico) o **Marketer/Growth** (se il fondatore è tecnico)
2. Mai assumere prima di avere revenue (almeno €5K MRR)
3. Preferire contractor per 3-6 mesi prima di assumere full-time
4. La prima assunzione sbagliata è la più costosa — meglio aspettare che precipitarsi

### 7. Come decidere se una feature va nel piano Free o Premium?

Framework: la feature aiuta l'utente a **capire il valore** del prodotto (→ Free) o a **estrarre valore** dal prodotto (→ Premium)?

Esempi:
- Dashboard base con dati → Free (mostra il valore)
- Export avanzato dei dati → Premium (estrae valore)
- 3 progetti → Free (prova il prodotto)
- Progetti illimitati → Premium (uso serio)

### 8. Ogni quanto rilasciare nuove feature?

Non esiste una cadenza universale. Ciò che conta è:
- Release small and often (settimanale o bi-settimanale)
- Ogni release deve essere deployabile indipendentemente
- Feature flags per separare deploy da release
- Comunicare le release ai clienti (changelog, in-app notification)

### 9. Come gestire le richieste di sconto?

```
FRAMEWORK SCONTO:

MAI dare sconto solo perché il cliente lo chiede.
Dare sconto in cambio di qualcosa:

  "10% di sconto se paghi annualmente" → ok (cash flow)
  "15% per i primi 6 mesi se mi fai un case study" → ok (social proof)
  "20% se referisci 2 clienti che convertono" → ok (acquisizione)
  "Sconto perché me lo chiedi" → no (erode il pricing)

MAX SCONTO: 20% (oltre crea precedente pericoloso)
ENTERPRISE: negoziare su scope, non su prezzo unitario
```

### 10. Come sopravvivere a un competitor che copia la tua feature principale?

1. Non farti prendere dal panico — il competitor ha copiato la feature, non il prodotto
2. Accelera sull'integrazione e sull'ecosystem (lock-in positivo)
3. Approfondisci il tuo ICP (serve meglio una nicchia)
4. Differenzia su: velocità di innovazione, supporto, community, brand
5. Il competitor grande è lento — tu puoi iterare 10x più veloce

### 11. Quando è il momento di raccogliere un round di finanziamento?

**Segni che è il momento giusto**:
- PMF raggiunto (retention, NPS, crescita organica)
- Crescita limitata dal capitale, non dalla domanda
- Hai un piano chiaro per come spendere il funding
- Runway < 12 mesi e crescita promettente

**Segni che è troppo presto**:
- Non hai PMF ancora
- "Mi servono soldi per fare marketing" (senza sapere quale canale)
- Stai fundraising per pagarti lo stipendio

### 12. Come impostare il monitoring per un SaaS early-stage?

**Stack minimo** (costo: €0-50/mese):

| Categoria | Tool | Free tier |
|-----------|------|-----------|
| Uptime | UptimeRobot / Better Uptime | 50 monitor |
| Errori | Sentry | 5K errori/mese |
| Log | Grafana Cloud / Logtail | 50GB/mese |
| Metriche app | PostHog | 1M eventi/mese |
| Metriche revenue | Baremetrics / ChartMogul | Fino a ~$10K MRR |

### 13. Come gestire un cliente che minaccia di andarsene?

```
PROCESSO:

1. Ascolta: perché vuole andarsene? (motivo reale, non pretesto)
2. Valuta: il cliente è profittevole? (MRR vs costo supporto)
3. Se profittevole e motivo risolvibile:
   → Offri una soluzione concreta (non solo sconto)
   → Timeline di risoluzione chiara
   → Follow-up proattivo
4. Se non profittevole o motivo strutturale:
   → Facilita il churn (export dati, transizione smooth)
   → Chiedi un feedback dettagliato
   → Non bruciare il ponte (potrebbe tornare)

NOTA: non tutti i clienti vanno salvati. Un cliente tossico che
assorbe il 30% del tempo del CS team non vale €200/mese.
```

### 14. Come gestire una vulnerabilità di sicurezza scoperta in produzione?

```
PROCESSO (in ordine):

1. CONTENERE (< 1h)
   □ Valutare l'impatto: dati esposti? accesso non autorizzato?
   □ Applicare fix o workaround immediato
   □ Se data breach: attivare il processo di notifica GDPR (72h)

2. INVESTIGARE (1-24h)
   □ Root cause analysis
   □ Extent of exposure (chi è impattato, da quando)
   □ Log degli accessi correlati

3. COMUNICARE (entro 24h)
   □ Clienti impattati: email diretta con dettagli e azioni da fare
   □ Tutti i clienti: comunicazione generale (se breach significativo)
   □ Autorità: GDPR notification se applicabile

4. RIMEDIARE (1-7 giorni)
   □ Fix permanente con test
   □ Audit per problemi simili
   □ Update della threat model
```

### 15. Come ridurre il costo infrastrutturale man mano che si scala?

```
QUICK WINS:
  □ Reserved instances (AWS/GCP): -30/60% vs on-demand
  □ Spot instances per workload tolleranti: -60/90%
  □ CDN per asset statici: riduce traffico origin
  □ Compressione risposte API (gzip/brotli)
  □ Ottimizzazione query DB (gli indici sono gratis)

MEDIO TERMINE:
  □ Right-sizing: molte istanze sono over-provisioned
  □ Autoscaling: non pagare per capacità che non usi di notte
  □ Archiviazione dati vecchi su cold storage (S3 Glacier)
  □ Caching aggressivo (Redis + CDN)

LUNGO TERMINE:
  □ Multi-cloud o cloud-agnostic per negoziare
  □ Architettura serverless per workload variabili
  □ Data pipeline ottimizzate (batch vs real-time)
  □ FinOps practice con budget per team
```

### 16. Qual è la differenza tra NRR e GRR e perché importano?

**GRR (Gross Revenue Retention)**: quanta revenue mantieni escludendo l'expansion. Se hai $100K MRR a gennaio e a gennaio successivo (senza contare upsell) hai $88K → GRR = 88%. Misura la salute base del prodotto.

**NRR (Net Revenue Retention)**: quanta revenue mantieni includendo l'expansion (upsell + cross-sell). Se hai $100K a gennaio e a gennaio successivo $115K (dallo stesso cohort) → NRR = 115%. Misura il potenziale di crescita senza nuovi clienti.

| | Buono | Ottimo | Top-tier |
|---|-------|--------|----------|
| GRR | > 85% | > 90% | > 95% |
| NRR | > 100% | > 110% | > 130% |

NRR > 100% significa che cresci anche senza acquisire nuovi clienti. È il segno più forte di PMF e valore per il cliente.

### 17. Come strutturare un programma di referral?

```
COMPONENTI CHIAVE:

Incentivo per il referrer:
  □ Credito/sconto (es: 1 mese gratis)
  □ Upgrade temporaneo
  □ Cash/gift card (per programmi B2C)
  □ Feature exclusive

Incentivo per il referee:
  □ Extended trial
  □ Sconto sul primo mese/anno
  □ Bonus feature per N giorni

MECCANICA:
  - Link univoco tracciabile per ogni utente
  - Reward al signup O alla conversione (meglio alla conversione)
  - Comunicazione automatica (in-app + email)
  - Dashboard per il referrer per vedere i propri referral
  - NPS > 8 → trigger automatico "Referisci un collega"
```

---

## Esercizi Pratici

### Esercizio 1: Diagnosi del Funnel

**Scenario**: hai un SaaS per time tracking con i seguenti dati mensili:

| Fase | Numero | Rate |
|------|--------|------|
| Visitatori unici | 15.000 | - |
| Signup | 750 | 5% visitor→signup |
| Attivazione (primo progetto) | 225 | 30% signup→activation |
| Trial completato (14gg) | 135 | 60% activated→trial end |
| Pagante | 40 | 30% trial→paid |
| Churn nel mese 1 | 8 | 20% churn primo mese |

**Domande**:
1. Dove si trova il collo di bottiglia principale?
2. Se potessi migliorare una sola fase del 50%, quale sceglieresti e perché?
3. Calcola il costo per acquisizione se spendi €3.000/mese in marketing
4. Qual è il tuo problema più urgente: acquisizione o retention?

**Suggerimento**: usa l'albero decisionale "La Crescita è Rallentata" come framework.

---

### Esercizio 2: Pricing Design

**Scenario**: stai lanciando un SaaS per gestione inventario rivolto a piccoli e-commerce. Hai raccolto dati di willingness-to-pay da 80 potenziali clienti:

- "Troppo economico": mediana $8
- "Prezzo giusto": mediana $25
- "Caro ma accettabile": mediana $45
- "Troppo caro": mediana $70

I tuoi costi per cliente: €3/mese (infra) + €2/mese (support amortizzato).

**Domande**:
1. Progetta 3 piani con nome, prezzo e differenziazione feature
2. Quale sarebbe la tua value metric? (per cosa il cliente paga)
3. Come gestirai il free tier (se lo includi)?
4. Quale ARPU target ti permetterebbe un LTV:CAC > 3:1 con un CAC di €200?

---

### Esercizio 3: Incident Response Drill

**Scenario**: sono le 15:30 di un martedì. Il tuo monitoring segnala:
- Error rate API passato da 0.1% a 8% negli ultimi 10 minuti
- Latency p95 triplicata (da 300ms a 900ms)
- Nessun deploy nelle ultime 4 ore
- CPU e memory nella norma

**Domande**:
1. Quale severity assegneresti e perché?
2. Scrivi i primi 5 passi della tua investigazione
3. Quali dashboard/log controlleresti per primo?
4. Se scoprissi che un servizio esterno (payment gateway) è la causa, quali sono le tue opzioni?
5. Scrivi il messaggio per la status page

---

### Esercizio 4: Post-Mortem di un Churn Spike

**Scenario**: nel mese di marzo il tuo churn è passato dal 3% al 7%. Analizzando i dati scopri:

- 60% del churn proviene da clienti acquisiti negli ultimi 60 giorni
- L'exit survey mostra: 45% "troppo complicato", 30% "non fa quello che pensavo", 25% "uso un competitor"
- A febbraio hai lanciato un redesign dell'interfaccia
- Il traffico paid è aumentato del 40% a febbraio (nuova campagna)

**Domande**:
1. Scrivi un post-mortem blameless con root cause analysis (5 perché)
2. Identifica almeno 3 azioni correttive con priorità e owner
3. Come distingueresti se il problema è il redesign, la campagna paid, o entrambi?
4. Quale metrica monitoreresti per verificare che le azioni abbiano effetto?

---

### Esercizio 5: Scaling Planning

**Scenario**: il tuo SaaS ha attualmente:
- 500 utenti attivi giornalieri
- Architettura: 2 web server, 1 PostgreSQL, 1 Redis
- Latency media: 180ms, p95: 450ms
- CPU media: 45%, picco: 72%
- Database size: 12GB

Hai appena firmato un contratto enterprise che porterà 2.000 nuovi utenti nei prossimi 3 mesi.

**Domande**:
1. Quali componenti hai bisogno di scalare e in che ordine?
2. Scrivi un piano di scaling con timeline (mese 1, 2, 3)
3. Quali metriche monitorerai per sapere se stai scalando abbastanza?
4. Calcola un budget infrastrutturale approssimativo pre e post scaling
5. Qual è il tuo piano B se lo scaling non è sufficiente?

---

### Esercizio 6: Support Ticket Triage

**Scenario**: sei il solo CS nella tua startup. Arrivi lunedì mattina con 12 ticket. Classificali in ordine di priorità e assegna una categoria:

1. "Non riesco ad accedere dal venerdì" — cliente Enterprise, €500/mese
2. "Vorrei poter esportare in PDF" — cliente Pro, €29/mese
3. "Mi avete addebitato due volte" — cliente Starter, €9/mese
4. "Il vostro prodotto è lentissimo, sto valutando di cambiare" — Enterprise, €800/mese
5. "Come faccio a invitare un collega?" — Free user
6. "Ho trovato un bug: se creo più di 50 task il contatore mostra 0" — Pro
7. "Vorrei cancellare il mio account e tutti i miei dati" — Starter
8. "URGENTE: i report mostrano numeri sbagliati" — Enterprise, €1.200/mese
9. "Complimenti, prodotto fantastico! Una domanda..." — Free user
10. "Sono un giornalista, vorrei scrivere del vostro prodotto" — N/A
11. "Ho cambiato email, come aggiorno il mio account?" — Pro
12. "Il vostro certificato SSL è scaduto" — Utente anonimo via Twitter

**Domande**:
1. Ordina i 12 ticket per priorità (dal primo all'ultimo da gestire)
2. Per ogni ticket, indica: priorità (P1-P4), categoria, tempo di risposta target
3. Quali ticket puoi risolvere con un template? Quali richiedono investigazione?
4. Quali ticket segnalano un problema sistemico da escalare?

---

### Esercizio 7: Revenue Recovery

**Scenario**: il tuo MRR è sceso da €25.000 a €22.000 negli ultimi 2 mesi. Breakdown:

| Componente | Mese 1 | Mese 2 | Delta |
|-----------|--------|--------|-------|
| New MRR | €3.000 | €2.200 | -€800 |
| Expansion MRR | €1.500 | €1.000 | -€500 |
| Churn MRR | -€1.800 | -€2.500 | -€700 |
| Contraction MRR | -€400 | -€700 | -€300 |
| **Net New MRR** | **€2.300** | **€0** | **-€2.300** |

**Domande**:
1. Qual è il Quick Ratio per ciascun mese? Cosa indica il trend?
2. Identifica le 3 leve più impattanti per tornare a crescere
3. Progetta una campagna di win-back per i clienti churnati
4. Scrivi un piano d'azione a 30-60-90 giorni
5. Quale metrica usi come "north star" per i prossimi 90 giorni?

---

### Esercizio 8: Operational Runbook Writing

**Compito**: scrivi un runbook operativo completo per **una** delle seguenti situazioni (scegli quella più rilevante per il tuo contesto):

A. **Onboarding di un cliente enterprise** — dalla firma del contratto al primo mese di utilizzo
B. **Migrazione di database** — pianificazione, esecuzione, rollback, verifica
C. **Lancio di una nuova feature** — dal feature flag alla general availability

Il runbook deve includere:
- Checklist pre-esecuzione
- Procedura step-by-step
- Criteri di successo
- Piano di rollback
- Responsabili per ogni fase
- Comunicazioni necessarie

---

## Riferimenti e Risorse

### Libri Fondamentali
- Jason Lemkin: "From Impossible to Inevitable" (scaling SaaS)
- Des Traynor, Eoghan McCabe: "Intercom on Starting Up"
- Wes Bush: "Product-Led Growth"
- April Dunford: "Obviously Awesome" (posizionamento)
- David Skok: blog forEntrepreneurs.com (metriche SaaS)
- Nir Eyal: "Hooked" (product engagement)

### Newsletter e Blog
- SaaStr (Jason Lemkin) — il più completo su SaaS scaling
- Lenny's Newsletter (Lenny Rachitsky) — growth e product
- First Round Review — startup wisdom
- OpenView Blog — PLG e SaaS benchmarks
- Tomasz Tunguz — data-driven SaaS insights
- ChartMogul Blog — metriche e benchmark SaaS

### Community
- SaaStr Annual (conferenza) e SaaStr community
- Indie Hackers — per bootstrap SaaS
- Product Hunt — lancio e discovery
- r/SaaS, r/startups — community Reddit

### Tool Stack Essenziale per SaaS
- **Billing**: Stripe Billing
- **Analytics**: Mixpanel/Amplitude/PostHog + ChartMogul/Baremetrics
- **CRM**: HubSpot (free tier per iniziare) / Salesforce (enterprise)
- **Support**: Intercom / Zendesk / Crisp
- **Email**: Customer.io / SendGrid / Postmark
- **Monitoring**: Datadog / Sentry / Better Uptime
- **Feature flags**: LaunchDarkly / PostHog / Unleash
- **Compliance**: Vanta / Drata (SOC 2 automation)
