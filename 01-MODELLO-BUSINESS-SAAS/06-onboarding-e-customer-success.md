# Onboarding e Customer Success — Guida Completa

> **Modulo 06** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **Onboarding = prodotto.** Il 70% del churn nei primi 90 giorni nasce da un onboarding fallito.
2. **Proattivo > reattivo.** CS che aspetta il ticket arriva troppo tardi. Health score + early warning.
3. **Retention batte acquisizione.** Acquisire un nuovo cliente costa 5-7x di più che mantenerne uno.
4. **NRR > 120% = crescita senza nuove acquisizioni.** L'expansion revenue è il vero motore.

## Indice

1. [Panoramica](#panoramica)
2. [Onboarding: Dal Signup al Valore](#onboarding-dal-signup-al-valore)
3. [Customer Success Management](#customer-success-management)
4. [Churn Prevention e Retention](#churn-prevention-e-retention)
5. [Health Score e Early Warning](#health-score-e-early-warning)
6. [Expansion e Upselling](#expansion-e-upselling)
7. [Customer Support Scalabile](#customer-support-scalabile)
8. [NPS, CSAT e Customer Feedback](#nps-csat-e-customer-feedback)
9. [Strumenti e Stack Tecnologico](#strumenti-e-stack-tecnologico)
10. [Workflow Operativi](#workflow-operativi)
11. [Implementazione Pratica Step-by-Step](#implementazione-pratica-step-by-step)
12. [Metriche e KPI Avanzati](#metriche-e-kpi-avanzati)
13. [Best Practices](#best-practices)
14. [Anti-Pattern e Errori Comuni](#anti-pattern-e-errori-comuni)
15. [Troubleshooting](#troubleshooting)
16. [Domande Frequenti (FAQ)](#domande-frequenti-faq)
17. [Percorso di Studio Consigliato](#percorso-di-studio-consigliato)
18. [Esercizi Pratici](#esercizi-pratici)

---

## Panoramica

Nel modello SaaS, l'acquisizione del cliente è solo l'inizio. Il vero valore economico si genera nei mesi e anni successivi, attraverso i rinnovi e l'espansione. Il Customer Success è la disciplina che garantisce che i clienti raggiungano i loro obiettivi con il prodotto — perché un cliente che ha successo con il prodotto rinnova, espande e referisce. Il costo di acquisire un nuovo cliente è 5-7x superiore a quello di mantenerne uno esistente. Un miglioramento del 5% nella retention può aumentare i profitti del 25-95% (Harvard Business Review).

### Il Framework Economico della Retention

La matematica della retention è brutale. Consideriamo un SaaS con:
- 100 clienti a inizio anno
- MRR medio $500/cliente
- Costo di acquisizione: $2.000/cliente

**Scenario A — Churn 5% mensile:**
```
Mese 1:  100 clienti → $50.000 MRR
Mese 6:   74 clienti → $37.000 MRR (persi $13.000/mese)
Mese 12:  54 clienti → $27.000 MRR (persi $23.000/mese)
Clienti persi: 46 → Costo di sostituzione: $92.000 CAC
Revenue persa in 12 mesi: ~$156.000
```

**Scenario B — Churn 2% mensile:**
```
Mese 1:  100 clienti → $50.000 MRR
Mese 6:   89 clienti → $44.500 MRR (persi $5.500/mese)
Mese 12:  79 clienti → $39.500 MRR (persi $10.500/mese)
Clienti persi: 21 → Costo di sostituzione: $42.000 CAC
Revenue persa in 12 mesi: ~$67.000
```

Differenza: **$89.000** di revenue preservata + **$50.000** di CAC risparmiato, semplicemente migliorando il churn dal 5% al 2%.

### Customer Success vs Customer Support vs Account Management

| Dimensione | Customer Support | Customer Success | Account Management |
|---|---|---|---|
| **Approccio** | Reattivo | Proattivo | Strategico |
| **Trigger** | Il cliente chiede aiuto | Dati/metriche indicano rischio o opportunità | Ciclo di rinnovo/espansione |
| **Obiettivo** | Risolvere il problema | Garantire il raggiungimento degli obiettivi | Massimizzare il revenue dell'account |
| **Metriche** | CSAT, tempo risposta, risoluzione | NRR, health score, adoption | ARR, expansion, rinnovo |
| **Interazione** | Ticket-driven | Cadenza regolare + trigger-driven | Milestone-driven (QBR, rinnovo) |
| **Scala** | 1 agente per centinaia di ticket | 1 CSM per 10-300 account | 1 AM per 5-20 account enterprise |
| **Timing** | Quando qualcosa non funziona | Costante, durante tutto il lifecycle | Pre-rinnovo, expansion planning |

### La Customer Success Organization

```
                    ┌─────────────────────┐
                    │   VP Customer       │
                    │   Success / CRO     │
                    └──────────┬──────────┘
          ┌────────────────────┼─────────────────────┐
          │                    │                      │
┌─────────┴─────────┐ ┌──────┴──────────┐ ┌────────┴────────┐
│ CS Operations     │ │ CS Management   │ │ Customer        │
│ (Data, Process,   │ │ (CSMs, Team     │ │ Support         │
│  Tools, Enablement│ │  Leads)         │ │ (Tier 0-3)      │
│  Playbooks)       │ │                 │ │                 │
└───────────────────┘ └─────────────────┘ └─────────────────┘
```

**CS Operations** gestisce la macchina: definisce i processi, implementa gli strumenti, analizza i dati, crea i playbook che i CSM eseguono. È il moltiplicatore di forza dell'intera organizzazione.

**CS Management** è il front-line: CSM individuali che gestiscono portfolio di account, eseguono i playbook, costruiscono relazioni, identificano rischi e opportunità.

**Customer Support** è la rete di sicurezza: risponde alle richieste di aiuto, risolve i problemi, documenta i bug, alimenta la knowledge base.

---

## Onboarding: Dal Signup al Valore

L'onboarding è il processo che porta un nuovo utente dal primo contatto con il prodotto al momento in cui ne percepisce il valore concreto ("aha moment"). È la fase più critica dell'intero ciclo di vita: un utente che non attiva entro i primi 7 giorni ha un'alta probabilità di non tornare mai.

### L'"Aha Moment"

L'"aha moment" è l'azione o il risultato che fa scattare la percezione del valore nel nuovo utente. Non è una feature — è un risultato.

Esempi noti:
- **Slack**: il team invia 2.000 messaggi → il team non può più farne a meno
- **Dropbox**: salva un file nella cartella sincronizzata → il valore è immediato
- **Zoom**: completa la prima video call → capisce la semplicità
- **Figma**: collabora in tempo reale con un collega su un design
- **HubSpot**: importa i contatti e crea il primo workflow automatico
- **Notion**: crea uno spazio di lavoro condiviso e lo usa con il team per una settimana
- **Stripe**: processa il primo pagamento reale → valore istantaneo

**Come trovarlo**: correlare le azioni degli utenti nei primi 7 giorni con la retention a 30/60/90 giorni. L'azione con la correlazione più alta è il candidato "aha moment".

**Metodologia di Identificazione dell'"Aha Moment":**

```
FASE 1: Raccolta dati (2-4 settimane)
  ├── Tracciare TUTTE le azioni utente nei primi 14 giorni
  ├── Segmentare utenti in "retained" (attivi a 90gg) e "churned"
  └── Registrare: azione, frequenza, timestamp, sequenza

FASE 2: Analisi statistica
  ├── Per ogni azione, calcolare:
  │   ├── Tasso di retention tra chi la compie vs chi non la compie
  │   ├── Lift: retention(azione) / retention(baseline)
  │   └── Significatività statistica (p-value < 0.05)
  ├── Ordinare per Lift decrescente
  └── Filtrare: solo azioni con n > 30 per significatività

FASE 3: Validazione qualitativa
  ├── Intervistare 10-15 utenti che hanno fatto l'azione e sono rimasti
  ├── Intervistare 10-15 utenti che NON l'hanno fatta e hanno abbandonato
  └── Domanda chiave: "In che momento hai capito che [prodotto] era utile?"

FASE 4: Definizione e ottimizzazione
  ├── Definire l'"aha moment" come: "[Persona] fa [Azione] entro [Tempo]"
  ├── Esempio: "Un team di 3+ persone invia 50+ messaggi nella prima settimana"
  └── Ottimizzare l'onboarding per guidare verso questa azione
```

**Esempio pratico — calcolo del Lift:**

| Azione nei primi 7 giorni | Retention a 90gg (chi la fa) | Retention a 90gg (chi NON la fa) | Lift |
|---|---|---|---|
| Invita un collega | 68% | 22% | 3.1x |
| Crea 3+ progetti | 61% | 25% | 2.4x |
| Usa integrazione API | 72% | 30% | 2.4x |
| Personalizza dashboard | 55% | 28% | 2.0x |
| Completa il tutorial | 45% | 32% | 1.4x |

"Invita un collega" ha il Lift più alto (3.1x). L'onboarding deve guidare verso questa azione.

### Progettare l'Onboarding

**Principi chiave**:
- L'onboarding inizia dal primo contatto (landing page, signup), non dopo il login
- Ogni step deve avvicinare l'utente all'"aha moment"
- Meno step possibili (3-5 max per il core flow)
- Progress bar visibile (riduce l'abbandono del 20-30%)
- Template e dati pre-popolati (empty state = death)

**Struttura consigliata**:

```
STEP 1: Signup (< 60 secondi)
  → Email + password (o SSO con Google/GitHub)
  → NO: azienda, ruolo, team size (chiedere dopo, se necessario)
  → Micro-copy rassicurante: "Nessuna carta di credito richiesta"

STEP 2: Profilazione leggera (< 30 secondi)
  → 1-2 domande per segmentare l'esperienza:
    "Qual è il tuo obiettivo principale?" (3-4 opzioni)
    "Quanto è grande il tuo team?" (solo, 2-10, 10-50, 50+)
  → Usare le risposte per personalizzare il percorso

STEP 3: Prima azione di valore (< 5 minuti)
  → Creare il primo [progetto/workspace/documento]
  → Con template pre-popolato o wizard guidato
  → Tooltip contestuali (non tutorial video da 10 minuti)
  → Empty state progettato: "Nessun progetto ancora. Crea il primo →"

STEP 4: Raggiungere l'"aha moment"
  → Invitare un collega / condividere un risultato
  → Questo è il trigger di retention
  → Prompt in-app: "Il [prodotto] funziona meglio in team. Invita un collega →"

STEP 5: Checklist di completamento
  → 3-5 azioni aggiuntive per consolidare l'adozione
  → Gamificazione leggera (progress %, badge)
  → "Hai completato 3 di 5 step. Mancano solo 2!"
```

### Onboarding Flow per Tipo di Prodotto

**PLG (Product-Led Growth) — Self-serve:**
```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Signup  │──→│ Profiling │──→│ Template │──→│  Value   │
│ (<60s)   │   │  (1-2 Q)  │   │ Wizard   │   │ Realized │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
     │                                             │
     │         ┌──────────────────────────┐        │
     └────────→│ Email drip campaign      │←───────┘
               │ (14 giorni, 6-8 email)   │
               └──────────────────────────┘
```

**Sales-Led — Enterprise:**
```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Kick-off│──→│  Config  │──→│ Training │──→│  Pilot   │──→│  Go-live │
│  Call    │   │  & Setup  │   │ Sessions │   │  Phase   │   │  & Scale │
│ (CSM+AE) │   │ (CSM+SE) │   │ (CSM)    │   │ (30-60d) │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │               │              │               │
     └──────────────┴───────────────┴──────────────┴───────────────┘
                              Success Plan condiviso
                          (obiettivi, timeline, metriche)
```

### Email di Onboarding

Sequenza tipo per un trial di 14 giorni:

| Giorno | Tipo | Oggetto | Contenuto | CTA |
|---|---|---|---|---|
| 0 | Benvenuto | "Benvenuto in [Prodotto]! Inizia qui" | Link diretto all'azione principale | "Crea il tuo primo [X]" |
| 1 | Quick win | "Il tuo primo [X] in 2 minuti" | Tutorial breve per feature core | "Prova ora" |
| 3 | Social proof | "Come [Cliente] ha ottenuto [risultato]" | Case study breve con metriche | "Scopri come" |
| 5 | Feature discovery | "Hai scoperto [Feature Avanzata]?" | Feature con alto Lift, non ancora usata | "Attiva [Feature]" |
| 7 | Checkpoint | "Come sta andando? Posso aiutarti?" | Domanda aperta + link calendario | "Prenota una demo" |
| 9 | Urgenza leggera | "5 cose che puoi fare con [Prodotto]" | Lista di use case non ancora esplorati | "Esplora" |
| 10 | Urgenza | "Il tuo trial scade tra 4 giorni" | Riepilogo valore + upgrade | "Passa a Pro" |
| 12 | Testimonial | "[Nome] dice: '[citazione]'" | Review reale + metriche | "Unisciti a loro" |
| 13 | Ultimo giorno | "Ultima possibilità: mantieni il tuo lavoro" | Rischio di perdere i dati + offerta | "Upgrade ora" |
| 15 | Post-trial | "Ci manchi. Torna con il 20% di sconto" | Offerta estensione / downgrade a free | "Riattiva" |
| 30 | Win-back | "Novità: [Feature] che avevi chiesto" | Aggiornamento prodotto + offerta | "Torna a provare" |

**Regole per email di onboarding:**
- Ogni email = 1 CTA. Mai più azioni in una sola email
- Subject line < 50 caratteri, personalizzata con nome/azienda
- Mittente = persona reale (CEO, CSM), non "noreply@"
- Plain text > HTML pesante (deliverability + sensazione personale)
- Conditional: se l'utente ha già fatto l'azione, skip l'email corrispondente
- Tracking: open rate, click rate, action rate per ogni email della sequenza

### Onboarding Segmentato

Non tutti gli utenti hanno lo stesso percorso. Segmentare per:
- **Ruolo**: admin vs utente, developer vs business user
- **Use case**: project management vs knowledge base vs reporting
- **Dimensione**: singolo vs team vs enterprise
- **Canale di acquisizione**: PLG vs sales-assisted (l'onboarding sales ha un CSM dedicato)
- **Industria**: fintech, healthcare, e-commerce hanno esigenze specifiche
- **Maturità tecnica**: early adopter vs late majority

**Matrice di segmentazione dell'onboarding:**

| Segmento | Onboarding | Durata | Intervento umano | Success Criteria |
|---|---|---|---|---|
| Solo/Freelancer | Self-serve + email drip | 7 giorni | Zero | Primo progetto completato |
| Team (2-10) | Self-serve + tooltip + webinar | 14 giorni | Opzionale (chat) | 3+ utenti attivi |
| Mid-market (10-50) | CSM-assisted + training | 30 giorni | CSM low-touch | 50%+ seat adoption |
| Enterprise (50+) | CSM dedicato + implementation | 60-90 giorni | CSM high-touch + SE | Success plan milestones |

### In-App Onboarding Patterns

**Pattern 1: Checklist persistente**
```
┌───────────────────────────────┐
│ 🎯 Inizia con [Prodotto]     │
│ ━━━━━━━━━━━━━━━░░░ 60%       │
│                               │
│ ✅ Crea il tuo account        │
│ ✅ Aggiungi il primo progetto │
│ ✅ Invita un collega          │
│ ○  Configura le notifiche     │
│ ○  Collega un'integrazione    │
│                               │
│ [Continua →]                  │
└───────────────────────────────┘
```

**Pattern 2: Tooltip contestuali (coach marks)**
- Appaiono solo quando l'utente raggiunge la zona rilevante
- Max 1 alla volta, mai sovrapposti
- "Non mostrare più" sempre disponibile
- Sequenziali: il secondo appare solo dopo che il primo è stato completato o chiuso

**Pattern 3: Modal di benvenuto**
- Appare solo al primo login
- Opzione per skip immediato
- Breve (< 30 secondi di lettura)
- Include la profilazione leggera (use case, ruolo)

**Pattern 4: Empty state progettato**
- Ogni vista vuota è un'opportunità di onboarding
- Template one-click: "Inizia con questo template →"
- Esempio interattivo: "Ecco come appare con i dati →"
- CTA chiaro: "Crea il tuo primo [X]"

### Misurare l'Efficacia dell'Onboarding

| Metrica | Formula | Benchmark buono | Benchmark eccellente |
|---|---|---|---|
| Activation Rate | Utenti che raggiungono "aha moment" / Signups | 30-40% | 50%+ |
| Time to Value (TTV) | Mediana tempo dal signup all'"aha moment" | < 24 ore | < 1 ora |
| Onboarding Completion | Utenti che completano la checklist / Signups | 20-30% | 40%+ |
| Day 1 Retention | Utenti attivi al giorno 1 / Signups | 40-50% | 60%+ |
| Day 7 Retention | Utenti attivi al giorno 7 / Signups | 20-30% | 35%+ |
| Day 30 Retention | Utenti attivi al giorno 30 / Signups | 10-15% | 20%+ |
| Trial-to-Paid | Conversione da trial a pagamento | 15-25% (card upfront) | 30%+ |
| | | 2-5% (no card) | 8%+ |

---

## Customer Success Management

Il Customer Success (CS) è la funzione aziendale responsabile di garantire che i clienti raggiungano i risultati desiderati usando il prodotto. Non è support reattivo — è proattivo.

### Modelli di CS per Segmento

**Tech-touch (SMB, $0-$1K MRR)**: tutto automatizzato. Email sequence, in-app messaging, knowledge base, chatbot. Ratio: 1 CSM per 500-2000 account. Il prodotto deve essere il CSM.

**Low-touch (SMB/mid-market, $1K-$5K MRR)**: automazione + interventi manuali per account a rischio. Webinar di gruppo, email personalizzate da template, check-in trimestrali. Ratio: 1 CSM per 100-300 account.

**High-touch (mid-market/enterprise, $5K+ MRR)**: CSM dedicato. Onboarding personalizzato, QBR (Quarterly Business Review), success plan co-creato, executive sponsor. Ratio: 1 CSM per 10-50 account.

**Strategic (key accounts, $50K+ MRR)**: team dedicato (CSM + TAM + SE). Roadmap influencing, executive business reviews, custom integrations. Ratio: 1 CSM per 3-10 account.

### Quarterly Business Review (QBR)

Per account high-touch, il QBR è il momento chiave della relazione:

**Preparazione QBR (1-2 settimane prima):**
```
1. Raccogliere dati usage dall'ultimo trimestre
   ├── Login giornalieri medi
   ├── Feature più usate e meno usate
   ├── Utenti attivi vs seat pagati
   └── Trend: usage in crescita, stabile, o calo?

2. Calcolare ROI tangibile
   ├── Tempo risparmiato (ore × costo orario)
   ├── Errori evitati (incidenti × costo medio)
   ├── Revenue incrementale attribuibile
   └── Costo total ownership vs soluzione precedente

3. Preparare la deck (max 10 slide)
   ├── Slide 1: Agenda
   ├── Slide 2-3: Risultati e metriche
   ├── Slide 4-5: Usage e adoption
   ├── Slide 6-7: Roadmap rilevante
   ├── Slide 8-9: Obiettivi prossimo trimestre
   └── Slide 10: Expansion opportunity

4. Allineare internamente
   ├── Aggiornamento da Support: ticket aperti, sentiment
   ├── Aggiornamento da Product: feature richieste in roadmap?
   └── Aggiornamento da Sales: rinnovo, expansion pipeline
```

**Struttura QBR (60 minuti)**:
1. **Risultati ottenuti** (15 min): metriche, ROI, obiettivi raggiunti — ricordare al cliente perché paga
2. **Utilizzo e adoption** (10 min): feature adottate, utenti attivi, benchmark vs peer
3. **Roadmap prodotto** (10 min): cosa arriva nei prossimi 3-6 mesi che è rilevante per loro
4. **Obiettivi prossimo trimestre** (15 min): co-definire 2-3 obiettivi misurabili
5. **Expansion opportunity** (10 min): nuovi use case, nuovi team, upgrade

Il QBR è anche il momento per multi-threading: coinvolgere l'executive sponsor, non solo l'utente operativo.

**Errori comuni nel QBR:**
- Presentare solo dati senza insight ("Avete usato la feature X 1.200 volte" → "La feature X vi ha fatto risparmiare 15 ore/settimana")
- Non portare il decision-maker executive al tavolo
- Trasformarlo in una sessione di lamentele senza azione
- Non documentare gli action items e i responsabili
- Non fare follow-up entro 48 ore con il summary scritto

### Customer Lifecycle

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER LIFECYCLE                                │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────┤
│Onboarding│ Adoption │  Value   │ Renewal  │Expansion │  Advocacy    │
│ 0-30 gg  │ 30-90 gg │90-180 gg │Al rinnovo│ Ongoing  │  Ongoing     │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────────┤
│Obiettivo:│Obiettivo:│Obiettivo:│Obiettivo:│Obiettivo:│Obiettivo:    │
│Attivaz.  │Uso       │ROI       │Rinnovo + │NRR >120% │Referral,     │
│"aha"     │regolare, │misurabile│expansion │          │case study    │
│          │team adopt│          │          │          │              │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────────┤
│Rischio:  │Rischio:  │Rischio:  │Rischio:  │Rischio:  │Rischio:      │
│Abbandono │Utente    │Prodotto  │Budget    │Over-     │Champion      │
│per no    │singolo,  │non       │cut,      │selling,  │lascia        │
│valore    │no team   │risolve   │competitor│feature   │l'azienda     │
│          │adoption  │problema  │champion  │bloat     │              │
│          │          │come      │churn     │          │              │
│          │          │sperato   │          │          │              │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────────┤
│Azione:   │Azione:   │Azione:   │Azione:   │Azione:   │Azione:       │
│Onboard.  │Encourage │QBR, ROI  │Preparare │Seat, plan│NPS follow-up │
│guidato,  │inviti,   │calc,     │rinnovo   │upgrade,  │referral      │
│check-in  │feature   │case study│90gg      │cross-sell│program,      │
│sett. 1   │discovery │co-creato │prima,    │add-on,   │user          │
│          │training  │          │exec      │multi-    │conference    │
│          │          │          │alignment │product   │              │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────────┘
```

### Success Plan

Il Success Plan è il documento vivo condiviso tra CSM e cliente che definisce:

```
┌──────────────────────────────────────────────────┐
│              SUCCESS PLAN — [Cliente]             │
├──────────────────────────────────────────────────┤
│ Obiettivi di business:                            │
│   1. Ridurre il tempo di onboarding da 2h a 30m  │
│   2. Aumentare la collaborazione cross-team       │
│   3. Eliminare tool ridondanti (consolidation)    │
│                                                   │
│ Metriche di successo:                             │
│   • Time to onboard: 2h → 30m (target: Q3)       │
│   • Utenti attivi: 40% → 80% dei seat (target: Q2│
│   • Tool eliminati: 3 → 1 (target: Q4)           │
│                                                   │
│ Milestones:                                       │
│   □ Mese 1: Setup + training admin                │
│   □ Mese 2: Rollout al team pilota (20 utenti)    │
│   □ Mese 3: Rollout completo (150 utenti)         │
│   □ Mese 4: Prima QBR, misura ROI                 │
│   □ Mese 6: Expansion a altri dipartimenti        │
│                                                   │
│ Stakeholder:                                      │
│   • Executive Sponsor: [Nome], VP Operations      │
│   • Champion: [Nome], Team Lead                   │
│   • Admin: [Nome], IT Manager                     │
│   • CSM: [Nome], [Azienda]                        │
│                                                   │
│ Rischi identificati:                              │
│   • IT resistente al cambiamento → coinvolger IT  │
│   • Budget review Q3 → dimostrare ROI prima       │
│   • Competitor in valutazione → differenziazione   │
└──────────────────────────────────────────────────┘
```

### Day-in-the-Life di un CSM

**CSM High-Touch (portfolio: 30 account, ~$500K ARR):**

```
08:30 — Check health score dashboard
         ├── 2 account passati da "Healthy" a "At Risk" overnight
         └── 1 account con usage spike (+200%) → opportunity?

09:00 — Standup CS team (15 min)
         ├── Condivisione rischi urgenti
         └── Allineamento su renewals in scadenza questo mese

09:30 — Call con Account A (at-risk)
         ├── Usage calato del 40% → il champion ha cambiato ruolo
         ├── Azione: identificare nuovo champion, riallineare con exec
         └── Follow-up: email con summary + proposta training

10:30 — Preparazione QBR per Account B (prossima settimana)
         ├── Pull usage data, calcola ROI
         └── Draft deck, condividi con AE per input expansion

11:30 — Onboarding call con Account C (nuovo, enterprise)
         ├── Kick-off: presentazione team, allineamento obiettivi
         └── Success plan draft condiviso

13:00 — Webinar interno: "Best practices [Feature X]"
         ├── Per account low-touch invitati
         └── Registrazione per knowledge base

14:00 — Rinnovo discussion con Account D (scade tra 60gg)
         ├── Health score: 82 (healthy)
         ├── Proposta: rinnovo 2 anni + expansion 20 seat
         └── Allineamento con AE su pricing

15:00 — Interno: sync con Product su feature request
         ├── Top 5 feature requests dai top account
         └── Feedback su beta feature in test con 3 account

16:00 — Follow-up email, CRM update, note
         ├── Aggiornare Salesforce/HubSpot per ogni interazione
         └── Trigger automazioni dove appropriato

17:00 — Review domani: 2 QBR, 1 onboarding, 1 escalation
```

---

## Churn Prevention e Retention

### Tipi di Churn

**Voluntary churn**: il cliente decide di cancellarsi. Cause: non percepisce valore, competitor migliore, budget ridotto, champion ha lasciato l'azienda.

**Involuntary churn**: il pagamento fallisce (carta scaduta, fondi insufficienti). Rappresenta il 20-40% del churn totale. Risolubile con dunning management.

**Logo churn**: numero di clienti persi / totale clienti. Misura la retention dell'account.

**Revenue churn**: MRR perso / MRR totale. Più importante del logo churn perché pondera il valore.

**Downgrade churn (contraction)**: il cliente resta ma passa a un piano inferiore o riduce i seat.

### Analisi delle Cause di Churn

**Framework RICE per Churn Analysis:**

| Causa | Reach (% del churn) | Impact ($ per caso) | Confidence | Effort to fix | Score |
|---|---|---|---|---|---|
| Involuntary (payment fail) | 25% | $300 MRR | Alto | Basso (tool) | ★★★★★ |
| No value perceived | 20% | $500 MRR | Medio | Alto (product) | ★★★☆☆ |
| Champion left company | 15% | $800 MRR | Alto | Medio (process) | ★★★★☆ |
| Budget cut | 15% | $600 MRR | Alto | Basso (pricing) | ★★★★☆ |
| Competitor switch | 10% | $700 MRR | Medio | Alto (product) | ★★☆☆☆ |
| Missing feature | 10% | $400 MRR | Medio | Alto (product) | ★★☆☆☆ |
| Bad support experience | 5% | $500 MRR | Alto | Medio (process) | ★★★☆☆ |

### Dunning Management (Involuntary Churn)

Sequenza per pagamento fallito:

```
GIORNO 0: Pagamento fallito
  ├── Retry automatico #1 (immediato)
  ├── Email: "Problema con il pagamento — aggiorna qui →"
  └── In-app: banner discreto "Azione richiesta"

GIORNO 3: Retry automatico #2
  ├── Email: "Secondo tentativo fallito — il tuo account è a rischio"
  └── In-app: banner più visibile

GIORNO 7: Retry automatico #3
  ├── Email: "Ultimo avviso — aggiorna il pagamento entro 7 giorni"
  ├── SMS (se disponibile): breve reminder
  └── In-app: full-page overlay con CTA aggiornamento

GIORNO 10: Retry automatico #4
  ├── Email: "Il tuo account sarà limitato tra 4 giorni"
  └── Limitare feature premium (non bloccare completamente)

GIORNO 14: Downgrade
  ├── Downgrade al piano free (NON cancellazione)
  ├── Email: "Il tuo account è stato sospeso — riattiva qui"
  └── Preservare tutti i dati per 90 giorni

GIORNO 30: Win-back
  ├── Email: "Ci manchi — torna con [offerta]"
  └── Opzione: riattivazione one-click

GIORNO 90: Cleanup
  ├── Email finale: "I tuoi dati saranno cancellati tra 30 giorni"
  └── Export dati disponibile
```

**Risultati attesi:** un buon dunning flow recupera il 30-50% dei pagamenti falliti, riducendo il churn involontario al 1-2% del totale.

**Tool**: Stripe ha retry intelligente integrato (Smart Retries). Tool dedicati: Churnkey, Baremetrics Recover, Gravy, Chargebee.

### Offboarding e Cancellation Flow

Quando un cliente vuole cancellarsi, l'offboarding flow è l'ultima opportunità:

```
STEP 1: "Ci dispiace vederti andare"
  └── Survey: perché stai cancellando? (max 5 opzioni)
      ├── Troppo costoso
      ├── Non lo uso abbastanza
      ├── Ho trovato un'alternativa migliore
      ├── Mi manca una feature specifica
      └── Altro (testo libero)

STEP 2: Offerta personalizzata (in base alla risposta)
  ├── Troppo costoso → "Passa al piano [base] a $X/mese" o sconto 30% per 3 mesi
  ├── Non lo uso → "Metti in pausa per 3 mesi gratis" (preserva i dati)
  ├── Alternativa → "Cosa ha [competitor] che noi non abbiamo?" (feedback)
  ├── Feature mancante → "È in roadmap per Q3. Vuoi essere tra i beta tester?"
  └── Altro → "Parliamone? [Link calendario con CSM]"

STEP 3: Se rifiuta l'offerta
  ├── Conferma cancellazione (bottone chiaro, non nascosto)
  ├── Offrire export dati (CSV, API)
  ├── Comunicare cosa succederà ai dati e quando
  └── "Puoi tornare in qualsiasi momento — il tuo account resta disponibile per 90 giorni"

STEP 4: Post-cancellazione
  ├── Email di conferma (immediata)
  ├── Email win-back dopo 30 giorni: "Ecco cosa c'è di nuovo"
  ├── Email win-back dopo 60 giorni: "Offerta speciale per tornare"
  └── Se torna: onboarding accelerato (dati preservati)
```

Benchmark: un buon offboarding flow salva il 10-25% delle cancellazioni.

**Regole etiche dell'offboarding:**
- Mai rendere impossibile cancellarsi (violazione GDPR, sentiment negativo)
- Mai nascondere il bottone di cancellazione
- Mai richiedere una telefonata per cancellarsi (a meno che non sia contrattuale per enterprise)
- Sempre offrire l'export dei dati del cliente
- Sempre comunicare chiaramente cosa succede ai dati dopo la cancellazione

---

## Health Score e Early Warning

Il Customer Health Score è un indicatore composito che predice la probabilità di rinnovo o churn di un account.

### Componenti del Health Score

| Componente | Peso | Segnale positivo | Segnale negativo | Come misurare |
|---|---|---|---|---|
| Product usage | 30% | Login giornalieri, feature core usata | Calo >30% nell'ultimo mese | Analytics (Amplitude, Mixpanel) |
| Feature adoption | 20% | 5+ feature usate | Solo 1-2 feature base | Feature flags, event tracking |
| User adoption | 15% | 80%+ seat attivi | <30% seat attivi | DAU/seat pagati |
| Support tickets | 10% | Pochi, risolti velocemente | Molti, irrisolti, escalation | Zendesk, Intercom |
| NPS/CSAT | 10% | NPS 9-10 | NPS 0-6 (detrattore) | Survey periodiche |
| Billing | 10% | Pagamenti puntuali | Pagamenti falliti, dispute | Stripe, payment processor |
| Engagement | 5% | Partecipa a webinar, community | Nessun engagement | CRM, event tracking |

### Implementazione del Health Score

**Calcolo (esempio Python-like pseudocode):**

```
def calculate_health_score(account):
    scores = {}

    # Usage: 0-100 basato sul trend settimanale
    usage_trend = account.weekly_active_users[-4:] / account.weekly_active_users[-8:-4]
    if usage_trend >= 1.1:
        scores['usage'] = 100  # crescita
    elif usage_trend >= 0.9:
        scores['usage'] = 70   # stabile
    elif usage_trend >= 0.7:
        scores['usage'] = 40   # calo moderato
    else:
        scores['usage'] = 10   # calo critico

    # Feature adoption: 0-100
    features_used = len(account.features_used_last_30d)
    features_total = len(ALL_CORE_FEATURES)
    scores['features'] = min(100, (features_used / features_total) * 120)

    # Seat adoption: 0-100
    active_ratio = account.monthly_active_users / account.seats_paid
    scores['seats'] = min(100, active_ratio * 125)

    # Support: 0-100 (inversamente proporzionale ai ticket aperti)
    open_tickets = account.open_support_tickets
    escalations = account.escalations_last_90d
    scores['support'] = max(0, 100 - (open_tickets * 10) - (escalations * 25))

    # NPS: mappa diretta
    if account.last_nps >= 9:
        scores['nps'] = 100
    elif account.last_nps >= 7:
        scores['nps'] = 60
    else:
        scores['nps'] = 20

    # Billing: binario + sfumature
    if account.payment_failures_last_90d == 0:
        scores['billing'] = 100
    elif account.payment_failures_last_90d <= 2:
        scores['billing'] = 50
    else:
        scores['billing'] = 10

    # Engagement
    engagement_events = account.webinar_attended + account.community_posts
    scores['engagement'] = min(100, engagement_events * 20)

    # Weighted average
    weights = {
        'usage': 0.30, 'features': 0.20, 'seats': 0.15,
        'support': 0.10, 'nps': 0.10, 'billing': 0.10,
        'engagement': 0.05
    }

    total = sum(scores[k] * weights[k] for k in weights)
    return round(total)
```

### Classificazione e Azioni

| Health Score | Stato | Colore | Azione | Cadenza check-in |
|---|---|---|---|---|
| 85-100 | Excellent | 🟢 Verde | Expansion opportunity, referral ask | Trimestrale |
| 70-84 | Healthy | 🟢 Verde chiaro | Monitor, feature discovery | Trimestrale |
| 50-69 | At risk | 🟡 Giallo | CSM intervento proattivo, call | Mensile |
| 30-49 | Unhealthy | 🟠 Arancione | Escalation, recovery plan | Bi-settimanale |
| 0-29 | Critical | 🔴 Rosso | Intervento urgente, exec escalation | Settimanale |

### Early Warning System

**Trigger automatici e azioni:**

| Trigger | Soglia | Azione automatica | Azione CSM |
|---|---|---|---|
| Usage drop | >30% WoW | Email re-engagement | Call entro 48h |
| Champion churn | Email del champion cambia | Alert urgente al CSM | Identificare nuovo champion ASAP |
| Negative sentiment | Support ticket con sentiment < 0.3 | Escalation ticket | Follow-up personale |
| Ghost account | Nessun login 14+ giorni | Email "Ci manchi" | Check-in call se enterprise |
| NPS detrattore | NPS < 7 | Alert al CSM | Follow-up entro 48h |
| Payment failure | Primo failure | Dunning flow automatico | Monitor, intervento se enterprise |
| Feature request denied | Feature critica rifiutata | Comunicazione trasparente | Proporre workaround |
| Competitor mention | Mention in ticket/chat | Alert al CSM + AE | Competitive response entro 24h |
| Contract approaching | 90 giorni al rinnovo | Trigger workflow rinnovo | Preparazione QBR + proposal |

---

## Expansion e Upselling

L'expansion revenue (upgrade, cross-sell, seat growth) è il motore della crescita SaaS matura. Con NRR > 120%, l'azienda cresce anche con zero nuove acquisizioni.

### Net Revenue Retention (NRR) Deep Dive

```
NRR = (MRR inizio + Expansion - Contraction - Churn) / MRR inizio × 100

Esempio:
  MRR inizio mese: $100.000
  Expansion (upgrade + seat + cross-sell): $8.000
  Contraction (downgrade): $2.000
  Churn (cancellazioni): $3.000

  NRR = ($100.000 + $8.000 - $2.000 - $3.000) / $100.000 = 103%
```

**Benchmark NRR per stage:**

| Segmento | Mediana | Top quartile | Best-in-class |
|---|---|---|---|
| SMB-focused | 90-100% | 100-110% | 110%+ |
| Mid-market | 100-110% | 110-120% | 120%+ |
| Enterprise | 110-120% | 120-140% | 140%+ |
| Usage-based | 115-125% | 125-145% | 150%+ |

### Strategie di Expansion

**Seat expansion**: facilitare l'invito di nuovi utenti. Prompt in-app: "Il tuo team sta crescendo? Aggiungi seat." Automatizzare la fatturazione pro-rata.

**Plan upgrade**: mostrare il valore delle feature premium quando l'utente ne ha bisogno. Soft paywall: "Questa feature è disponibile nel piano Pro — prova gratis per 7 giorni."

**Usage expansion**: per modelli usage-based, l'expansion è naturale con la crescita dell'utilizzo. Monitorare l'approaching-limit e proporre tier successivo.

**Cross-sell / add-on**: prodotti complementari. "Stai usando [Prodotto A]? [Prodotto B] si integra perfettamente e ti permette di..."

**Multi-product**: per piattaforme con più prodotti, il land-and-expand è strategico: vendere un prodotto, poi espandere ad altri moduli.

**Professional services**: per enterprise, offrire training, implementazione, customizzazione come revenue aggiuntiva.

### Expansion Playbook

```
IDENTIFICAZIONE OPPORTUNITÀ
  ├── Trigger basati sui dati:
  │   ├── Seat utilization > 90% → proponi seat pack
  │   ├── Feature premium usata (trial) 5+ volte → proponi upgrade
  │   ├── Usage approaching limit → proponi tier successivo
  │   ├── Nuovo dipartimento/team attivo → proponi expansion
  │   └── Post-QBR positivo (health > 80) → proponi add-on
  │
  ├── Trigger basati sulla relazione:
  │   ├── Executive sponsor menziona nuovi obiettivi → allinea
  │   ├── Azienda cliente fa fundraising → capacity planning
  │   ├── Cliente chiede feature del piano superiore → soft upsell
  │   └── Cliente referisce nuovi prospect → reward + expansion
  │
  └── Timing ottimale:
      ├── Post-QBR con risultati positivi
      ├── Post-training quando il team scopre nuove capability
      ├── Pre-rinnovo (bundle rinnovo + expansion = sconto)
      └── Quando l'utente raggiunge un limit naturale

QUALIFICAZIONE
  ├── Il cliente ha budget? (allineamento con procurement)
  ├── Il champion ha l'autorità? (senno, chi la ha?)
  ├── Il timing è giusto? (non durante un incident o frustrazione)
  └── Il valore è chiaro? (ROI proiettato documentato)

PROPOSTA
  ├── Personalizzata: "Basandoci sull'uso del tuo team..."
  ├── ROI-driven: "Questo vi farà risparmiare X ore/mese..."
  ├── Trial-first: "Prova per 14 giorni, decide dopo"
  └── Bundle: "Rinnovo 2 anni + expansion = 15% sconto"

FOLLOW-UP
  ├── Documenta tutto nel CRM
  ├── Conferma con email recap
  └── Pianifica onboarding per la nuova funzionalità
```

### Timing dell'Expansion

Il momento migliore per proporre expansion:
- Dopo un QBR positivo (risultati dimostrati)
- Quando l'utente raggiunge un limite (naturale)
- Dopo un "aha moment" con una feature premium
- Al rinnovo (bundle upgrade + rinnovo multi-anno)
- Quando il team/azienda cresce (nuovi seat naturali)
- Dopo un training di successo che apre nuovi use case

**Il momento peggiore:**
- Durante un incidente o outage
- Quando il cliente ha ticket aperti irrisolti
- Subito dopo un aumento di prezzo
- Quando il health score è < 50

---

## Customer Support Scalabile

### Modello Tiered

**Tier 0 (self-service)**: knowledge base, FAQ, chatbot, in-app help, community forum. Obiettivo: risolvere l'80% delle richieste senza intervento umano.

**Tier 1 (front-line)**: agenti di supporto per problemi standard. Chat, email, ticket. SLA: risposta < 4 ore, risoluzione < 24 ore.

**Tier 2 (specialist)**: problemi tecnici complessi, bug, integrazioni. SLA: risposta < 8 ore, risoluzione < 72 ore.

**Tier 3 (engineering)**: bug critici, performance issue, data corruption. Escalation diretta al team engineering.

### SLA per Piano

| Piano | Prima risposta | Risoluzione target | Canali | Copertura |
|---|---|---|---|---|
| Free | Best effort | Best effort | Email, community | Business hours |
| Starter | < 24h | < 72h | Email, chat | Business hours |
| Pro | < 4h | < 24h | Email, chat, phone | Extended (12h) |
| Enterprise | < 1h | < 8h | Email, chat, phone, Slack | 24/7 |
| Mission Critical | < 15 min | < 4h | Dedicated channel + phone | 24/7 + dedicated |

### Knowledge Base Efficace

La knowledge base è l'investimento con il miglior ROI nel support. Ogni articolo che risolve un problema riduce i ticket futuri.

**Struttura raccomandata:**
```
Knowledge Base
├── 🚀 Getting Started
│   ├── Quick start guide (< 5 minuti)
│   ├── Primo progetto tutorial
│   └── Video walkthrough
├── 📖 Feature Guides
│   ├── [Feature A] — Setup e uso base
│   ├── [Feature A] — Configurazione avanzata
│   └── [Feature B] — Guida completa
├── 🔧 Troubleshooting
│   ├── Problemi di login e accesso
│   ├── Errori comuni e soluzioni
│   └── Performance e lentezza
├── 🔌 Integrazioni
│   ├── [Integration A] — Setup
│   ├── [Integration B] — Setup
│   └── API Reference
├── 💳 Billing e Account
│   ├── Gestione piano e pagamenti
│   ├── Fatturazione
│   └── Cancellazione e downgrade
└── 📋 FAQ
    ├── Generali
    ├── Tecniche
    └── Pricing
```

**Ogni articolo deve avere:**
- Titolo chiaro che risponde a una domanda
- Problema descritto in 1-2 frasi
- Soluzione step-by-step con screenshot annotati
- "Questo articolo ti è stato utile?" (feedback)
- Link a articoli correlati
- Data di ultimo aggiornamento

**Metriche della Knowledge Base:**

| Metrica | Formula | Target |
|---|---|---|
| Ticket Deflection Rate | Visite KB che NON generano ticket / Visite KB totali | > 70% |
| Search Success Rate | Ricerche con click su risultato / Ricerche totali | > 60% |
| Zero-Result Rate | Ricerche senza risultati / Ricerche totali | < 10% |
| Article Usefulness | "Utile" / ("Utile" + "Non utile") | > 80% |
| Coverage | Categorie ticket con articolo KB / Categorie ticket totali | > 90% |

---

## NPS, CSAT e Customer Feedback

### Net Promoter Score (NPS)

Domanda: "Quanto è probabile che raccomandi [Prodotto] a un collega?" (0-10)

- **Promotori** (9-10): clienti entusiasti → referral, case study, upsell
- **Passivi** (7-8): soddisfatti ma non entusiasti → a rischio competitor
- **Detrattori** (0-6): insoddisfatti → churn probabile, danno reputazionale

NPS = % Promotori - % Detrattori. Range: -100 a +100.

Benchmark SaaS: mediana 30-40, top performer > 60.

**Quando misurarlo**: dopo 30-60 giorni dall'onboarding (relationship NPS), dopo ogni interazione con il support (transactional NPS), trimestralmente per account enterprise.

**L'NPS è inutile senza follow-up**: ogni detrattore deve ricevere un follow-up entro 48 ore. Ogni promotore deve essere invitato a referire o lasciare una review.

### NPS Follow-Up Playbook

```
DETRATTORE (0-6):
  ├── Alert immediato al CSM (owner dell'account)
  ├── Follow-up entro 48 ore:
  │   "Grazie per il feedback. Mi dispiace che la tua esperienza
  │    non sia stata positiva. Possiamo parlarne?"
  ├── Root cause analysis: perché è insoddisfatto?
  ├── Action plan: cosa possiamo fare per migliorare?
  ├── Follow-up 30 giorni: "Abbiamo fatto [X]. Come va ora?"
  └── Tracking: il detrattore è diventato passivo/promotore?

PASSIVO (7-8):
  ├── Email automatica:
  │   "Grazie! Cosa potremmo fare per trasformarti in un fan?"
  ├── Analizzare pattern: cosa manca per il 9-10?
  └── Feature discovery: mostrare funzionalità non ancora usate

PROMOTORE (9-10):
  ├── Email automatica:
  │   "Wow, grazie! Saresti disposto a..."
  │   ├── Lasciare una review su G2/Capterra?
  │   ├── Partecipare a un case study?
  │   └── Referire un collega? (con reward)
  ├── Invitare alla community ambassador program
  └── Considerare per beta testing di nuove feature
```

### CSAT (Customer Satisfaction Score)

Domanda: "Quanto sei soddisfatto di [interazione/prodotto]?" (1-5)

Più granulare dell'NPS, misura la soddisfazione per singola interazione. Utile per: valutare il support, l'onboarding, singole feature.

**CSAT = risposte positive (4-5) / risposte totali × 100**

Benchmark: mediana SaaS 80-85%, top performer > 92%.

### Customer Effort Score (CES)

Domanda: "Quanto è stato facile [risolvere il problema / completare l'azione]?" (1-7)

Il CES è il miglior predittore di loyalty (Harvard Business Review, 2010). Un'esperienza a basso sforzo fidelizza più di un'esperienza "deliziosa".

CES < 3: alto sforzo → a rischio churn. CES > 5: basso sforzo → loyalty alta.

### Customer Feedback Loop

```
RACCOGLIERE → CATEGORIZZARE → PRIORITIZZARE → AGIRE → COMUNICARE → MISURARE

1. RACCOGLIERE (multi-canale):
   ├── Survey: NPS, CSAT, CES (automatizzate)
   ├── Exit survey: motivo cancellazione
   ├── Feature requests: in-app, email, support tickets
   ├── Support tickets: analisi tematica
   ├── Social media: menzioni, review
   ├── Sales feedback: obiezioni ricorrenti
   └── Community/forum: discussioni, voti

2. CATEGORIZZARE (taxonomy):
   ├── Bug / difetto
   ├── Feature request (nuova)
   ├── Feature improvement (esistente)
   ├── UX / usabilità
   ├── Performance
   ├── Pricing / billing
   ├── Support quality
   └── Documentation

3. PRIORITIZZARE (framework Impatto × Frequenza × Revenue):
   ├── Quanti clienti lo chiedono? (frequenza)
   ├── Quanto revenue è a rischio? (impatto)
   ├── Quanto è facile da implementare? (effort)
   └── Score = (frequenza × impatto) / effort

4. AGIRE:
   ├── Quick wins (< 1 settimana): fix immediatamente
   ├── Roadmap items: inserire nel backlog con timeline
   ├── Won't do: decidere e comunicare il perché
   └── Richiesta di chiarimento: intervistare il cliente

5. COMUNICARE (closing the loop):
   ├── "Ci hai detto X, abbiamo fatto Y"
   ├── Changelog pubblico con tag "richiesto da voi"
   ├── Email personalizzata a chi ha chiesto la feature
   └── In-app notification: "Novità basata sul tuo feedback"

6. MISURARE:
   ├── Il NPS è migliorato dopo l'azione?
   ├── I ticket su quel tema sono diminuiti?
   ├── La feature è stata adottata dai richiedenti?
   └── Il churn correlato è diminuito?
```

---

## Strumenti e Stack Tecnologico

### Stack CS per Fase di Crescita

**Early Stage (0-100 clienti, budget limitato):**

| Funzione | Tool | Costo indicativo |
|---|---|---|
| CRM | HubSpot Free | $0 |
| Support | Intercom Starter / Crisp | $0-$50/mese |
| Email automation | Customer.io / Mailchimp | $0-$50/mese |
| Analytics | Mixpanel Free / PostHog | $0 |
| NPS | Typeform / Google Forms | $0 |
| Knowledge base | Notion pubblica / GitBook | $0 |

**Growth (100-1000 clienti):**

| Funzione | Tool | Costo indicativo |
|---|---|---|
| CRM + CS | HubSpot Pro / Vitally | $200-$500/mese |
| Support | Intercom / Zendesk | $100-$500/mese |
| Email automation | Customer.io / Braze | $100-$300/mese |
| Analytics | Amplitude / Mixpanel | $200-$1000/mese |
| NPS/Survey | Delighted / Wootric | $100-$300/mese |
| Knowledge base | Intercom Articles / HelpScout | incluso |
| Dunning | Stripe Smart Retries + Churnkey | $50-$200/mese |

**Scale (1000+ clienti):**

| Funzione | Tool | Costo indicativo |
|---|---|---|
| CS Platform | Gainsight / Totango / ChurnZero | $500-$5000/mese |
| CRM | Salesforce | $150+/utente/mese |
| Support | Zendesk Enterprise / Intercom | $500-$2000/mese |
| Email | Braze / Iterable | $500-$2000/mese |
| Analytics | Amplitude Business | $500-$2000/mese |
| BI | Looker / Metabase | $300-$1000/mese |
| Revenue intelligence | Gong / Chorus | $100/utente/mese |

---

## Workflow Operativi

### Workflow 1: Nuovo Cliente Onboarding (Self-Serve)

```
TRIGGER: Signup completato
  │
  ├──→ [Automatico] Email benvenuto (immediata)
  ├──→ [Automatico] In-app checklist attivata
  ├──→ [Automatico] Tag CRM: "Onboarding — Giorno 0"
  │
  ├── GIORNO 1: Login?
  │   ├── SI → [Automatico] Tooltip prima azione
  │   └── NO → [Automatico] Email "Inizia qui" + reminder
  │
  ├── GIORNO 3: "Aha moment" raggiunto?
  │   ├── SI → [Automatico] Email feature discovery
  │   └── NO → [Automatico] Email con quick start guide
  │
  ├── GIORNO 7: Engagement check
  │   ├── Attivo → [Automatico] Email social proof
  │   ├── Occasionale → [Automatico] Email "Hai bisogno di aiuto?" + calendario
  │   └── Inattivo → [Automatico] Email win-back + offerta estensione trial
  │
  ├── GIORNO 10: Trial midpoint
  │   ├── Attivo → [Automatico] Email feature premium
  │   └── Inattivo → [Automatico] SMS/push "Il tuo trial sta scadendo"
  │
  ├── GIORNO 13: Pre-scadenza
  │   └── [Automatico] Email urgenza + CTA upgrade + valore generato
  │
  ├── GIORNO 14: Fine trial
  │   ├── Upgrade → [Automatico] Email conferma + onboarding paid
  │   ├── Non upgrade → [Automatico] Downgrade a free + email win-back
  │   └── Cancellazione → [Automatico] Exit survey + offboarding flow
  │
  └── POST-TRIAL (giorno 30, 60, 90):
      └── [Automatico] Email periodica con novità prodotto + offerta
```

### Workflow 2: Account At-Risk (Health Score < 50)

```
TRIGGER: Health score scende sotto 50
  │
  ├──→ [Automatico] Alert al CSM via Slack/email
  ├──→ [Automatico] Flag account nel CRM
  ├──→ [Automatico] Creare task "At-Risk Review" per il CSM
  │
  ├── ENTRO 24h: CSM review
  │   ├── Analizzare COSA è cambiato (quale componente del health score)
  │   ├── Verificare: ticket aperti? payment issue? usage drop?
  │   └── Decidere l'azione primaria
  │
  ├── ENTRO 48h: Outreach
  │   ├── Se usage drop → call "Come possiamo aiutarti?"
  │   ├── Se champion churn → identificare nuovo champion
  │   ├── Se ticket irrisolti → escalation interna
  │   └── Se payment issue → dunning + outreach manuale
  │
  ├── ENTRO 1 SETTIMANA: Recovery plan
  │   ├── Co-creare recovery plan con il cliente
  │   ├── 2-3 azioni concrete con timeline
  │   └── Escalation a manager CS se necessario
  │
  ├── FOLLOW-UP SETTIMANALE: Monitorare
  │   ├── Health score migliora? → continuare piano
  │   ├── Health score stabile? → intensificare intervento
  │   └── Health score peggiora? → escalation executive
  │
  └── CHIUSURA:
      ├── Health > 60 per 4 settimane → de-escalation
      └── Churn avvenuto → post-mortem, lesson learned
```

### Workflow 3: Rinnovo Contrattuale

```
TRIGGER: 90 giorni al rinnovo
  │
  ├── GIORNO -90: Kick-off processo rinnovo
  │   ├── CSM: review health score, usage, ticket history
  │   ├── AE: preparare proposal (rinnovo + expansion)
  │   └── Finance: verifica contratto attuale, pricing
  │
  ├── GIORNO -75: QBR pre-rinnovo
  │   ├── Presentare risultati dell'anno
  │   ├── ROI documentato
  │   ├── Obiettivi per il prossimo anno
  │   └── Introdurre expansion opportunity
  │
  ├── GIORNO -60: Proposta formale
  │   ├── Pricing del rinnovo
  │   ├── Opzioni: 1 anno, 2 anni (sconto multi-anno)
  │   ├── Expansion inclusa (seat, features, products)
  │   └── Termini aggiornati se necessario
  │
  ├── GIORNO -45: Negoziazione
  │   ├── Rispondere a obiezioni
  │   ├── Coinvolgere executive sponsor se necessario
  │   └── Flessibilità: pricing, termini, payment schedule
  │
  ├── GIORNO -30: Firma o escalation
  │   ├── Se firmato → onboarding nuove feature/seat
  │   ├── Se in negoziazione → escalation a VP CS/CRO
  │   └── Se a rischio → offer speciale + executive alignment
  │
  ├── GIORNO -14: Deadline comunicata
  │   └── "Il contratto scade tra 14 giorni. Confermiamo?"
  │
  └── GIORNO 0: Rinnovo o churn
      ├── Rinnovo → Celebrare + pianificare il nuovo anno
      └── Churn → Exit process, post-mortem, win-back plan
```

---

## Implementazione Pratica Step-by-Step

### Come Avviare un Team CS da Zero

**Fase 1: Foundations (Mese 1-2)**

```
SETTIMANA 1-2: Definire le basi
  ├── Identificare l'"aha moment" del prodotto
  ├── Mappare il customer lifecycle
  ├── Definire le metriche baseline: churn, NRR, NPS
  └── Decidere il modello CS: tech-touch vs high-touch

SETTIMANA 3-4: Implementare gli strumenti base
  ├── CRM: HubSpot (gratuito per iniziare)
  ├── Support: Intercom o Zendesk
  ├── Analytics: connettere il prodotto (Segment → Amplitude)
  └── Health score: v1 manuale in spreadsheet

SETTIMANA 5-6: Creare i primi playbook
  ├── Playbook onboarding (email + in-app)
  ├── Playbook at-risk (trigger + azioni)
  ├── Playbook rinnovo (timeline + template)
  └── Knowledge base: top 20 articoli

SETTIMANA 7-8: Prima iterazione
  ├── Assumere il primo CSM (se > 50 clienti paganti)
  ├── Implementare email di onboarding automatiche
  ├── Avviare NPS survey trimestrale
  └── Baseline: misurare churn, activation, NRR attuali
```

**Fase 2: Scale (Mese 3-6)**

```
  ├── Implementare health score automatizzato
  ├── Segmentare i clienti (tech/low/high touch)
  ├── Creare dashboard CS (Looker/Metabase)
  ├── Avviare QBR per top 20% clienti per revenue
  ├── Dunning management automatizzato
  ├── Assumere 2° CSM quando ratio > 1:200 (low-touch)
  └── Community/forum avviato
```

**Fase 3: Optimize (Mese 6-12)**

```
  ├── CS platform dedicata (Gainsight/Totango)
  ├── Playbook raffinati con A/B testing
  ├── CS Ops role (data + process)
  ├── Expansion playbook formalizzato
  ├── Customer Advisory Board (top 10 clienti)
  └── NRR target > 110%
```

---

## Metriche e KPI Avanzati

### Dashboard CS — Metriche Essenziali

| Metrica | Formula | Frequenza | Owner |
|---|---|---|---|
| **Gross Revenue Retention (GRR)** | (MRR inizio - Churn - Contraction) / MRR inizio | Mensile | VP CS |
| **Net Revenue Retention (NRR)** | (MRR inizio + Expansion - Contraction - Churn) / MRR inizio | Mensile | VP CS |
| **Logo Retention** | (Clienti inizio - Churned) / Clienti inizio | Mensile | VP CS |
| **Time to Value (TTV)** | Mediana giorni dal signup all'"aha moment" | Settimanale | CS Ops |
| **Activation Rate** | Utenti che raggiungono "aha" / Signups | Settimanale | CS Ops |
| **Onboarding Completion** | Checklist completata / Signups | Settimanale | CS Ops |
| **Health Score Distribution** | % account Green/Yellow/Red | Giornaliera | CSM |
| **NPS** | % Promotori - % Detrattori | Trimestrale | CS Ops |
| **CSAT (Support)** | Risposte 4-5 / Risposte totali | Settimanale | Support Lead |
| **First Response Time** | Mediana tempo dalla richiesta alla prima risposta | Giornaliera | Support Lead |
| **Resolution Time** | Mediana tempo dalla richiesta alla risoluzione | Settimanale | Support Lead |
| **Ticket Deflection** | Visite KB senza ticket / Visite KB totali | Mensile | CS Ops |
| **Expansion Rate** | Expansion MRR / MRR totale | Mensile | AE/CSM |
| **CSM Productivity** | ARR gestita per CSM | Trimestrale | VP CS |

### Cohort Analysis per Retention

```
Esempio: Monthly cohort retention (% di MRR del mese di acquisizione)

         M0    M1    M2    M3    M4    M5    M6    M12
Gen '26  100%  92%   87%   84%   82%   81%   80%   75%
Feb '26  100%  94%   90%   87%   85%   84%   83%   -
Mar '26  100%  95%   91%   89%   87%   86%   -     -
Apr '26  100%  96%   93%   91%   -     -     -     -

Lettura: la cohort di Marzo performa meglio (95% M1 vs 92% Gen).
Cosa è cambiato? Nuovo onboarding flow lanciato a Febbraio.
```

---

## Best Practices

1. **L'onboarding è il prodotto**: il 70% del churn nei primi 90 giorni è dovuto a un onboarding fallito. Investire in onboarding quanto in nuove feature
2. **Proattivo > reattivo**: il CS che aspetta il ticket del cliente arriva troppo tardi. Usare health score e early warning per intervenire prima del churn
3. **Segmentare l'intervento**: high-touch per enterprise, tech-touch per SMB. Non provare a fare high-touch su 2000 account con 3 CSM
4. **Chiudere il loop del feedback**: raccogliere feedback senza agire è peggio che non raccoglierlo. Ogni feedback deve avere una risposta
5. **Multi-threading**: non dipendere da un singolo contatto nell'account. Se il champion lascia l'azienda e non hai altre relazioni, il churn è quasi certo
6. **Dunning serio**: il 20-40% del churn è involuntario (pagamento fallito). È il churn più facile da risolvere
7. **Success plan condiviso**: per account enterprise, co-creare il piano di successo con il cliente. Obiettivi misurabili, timeline, responsabilità
8. **Celebration rituals**: celebrare i successi del cliente pubblicamente (con permesso). Case study, social media, community spotlight
9. **Data-driven everything**: ogni decisione CS deve essere supportata da dati. Health score, usage analytics, cohort analysis
10. **CS ≠ Support**: CS è proattivo e strategico. Support è reattivo e tattico. Servono entrambi, ma sono funzioni diverse

---

## Anti-Pattern e Errori Comuni

### Anti-Pattern 1: "CSM come pompiere"
**Problema:** i CSM passano il 90% del tempo a spegnere incendi invece di lavorare proattivamente.
**Causa:** nessun early warning system, nessun health score, interventi solo quando il cliente si lamenta.
**Soluzione:** implementare health score + trigger automatici. Il CSM deve dedicare almeno il 60% del tempo a attività proattive.

### Anti-Pattern 2: "Onboarding infinito"
**Problema:** l'onboarding dura mesi, il cliente non raggiunge mai l'"aha moment".
**Causa:** troppe feature presentate, nessuna priorità, tutorial troppo lunghi.
**Soluzione:** definire l'"aha moment" chiaro, onboarding in 3-5 step, time-to-value < 24 ore.

### Anti-Pattern 3: "NPS theater"
**Problema:** si misura NPS ma non si agisce sul feedback. I detrattori non ricevono follow-up.
**Causa:** NPS come vanity metric per il board, non come strumento operativo.
**Soluzione:** ogni detrattore = follow-up entro 48h. Ogni promotore = referral ask. NPS senza azione è spreco.

### Anti-Pattern 4: "Feature dumping"
**Problema:** durante l'onboarding si mostrano 50 feature al cliente, che si confonde e abbandona.
**Causa:** confondere completezza con efficacia. Il team vuole mostrare tutto.
**Soluzione:** mostrare solo le 2-3 feature che portano all'"aha moment". Discovery progressiva.

### Anti-Pattern 5: "Single-threaded relationship"
**Problema:** la relazione dipende da un singolo contatto (champion). Se lascia l'azienda, si perde l'account.
**Causa:** CSM pigro o sovraccarico, non investe nel multi-threading.
**Soluzione:** per ogni account, almeno 3 contatti: champion (operativo), sponsor (executive), admin (tecnico).

### Anti-Pattern 6: "Renewal surprise"
**Problema:** il rinnovo viene discusso per la prima volta a 2 settimane dalla scadenza.
**Causa:** nessun workflow strutturato, CSM sovraccarico.
**Soluzione:** workflow rinnovo a T-90 giorni. Mai sorprendere il cliente.

### Anti-Pattern 7: "Support ticket black hole"
**Problema:** i ticket entrano ma le risposte sono lente, vaghe, o mai arrivano.
**Causa:** sottodimensionamento del team, nessun SLA, nessuna knowledge base.
**Soluzione:** SLA definiti per piano, knowledge base come Tier 0, metriche di support monitorate quotidianamente.

---

## Troubleshooting

**"Churn alto nei primi 30 giorni"**
→ L'onboarding non funziona. Mappare dove gli utenti abbandonano. L'"aha moment" è raggiungibile in < 5 minuti? Il primo valore è evidente? Session recording (Hotjar, FullStory) per capire i punti di frizione. A/B test: rimuovere step dall'onboarding e misurare se l'activation rate migliora.

**"Clienti pagano ma non usano il prodotto"**
→ Zombie account. Pericoloso: il rinnovo è a rischio. Intervento proattivo: email di re-engagement, webinar di training, check-in del CSM. Se non si riattivano, il churn è questione di tempo. Considerare: il prodotto risolve un problema reale per quel segmento? O hanno comprato per la demo e non per l'uso quotidiano?

**"NPS alto ma churn alto"**
→ Paradosso apparente: il cliente è soddisfatto ma cancella. Cause probabili: budget cut (non dipende da te), competitor con prezzo aggressivo (difendere con valore, non con sconto), champion ha lasciato l'azienda (multi-threading è la prevenzione). Analizzare: l'NPS viene misurato sugli utenti attivi (che sono contenti) mentre il churn avviene sugli account (decisione business)?

**"Il CS team è sommerso di richieste"**
→ Investire in self-service: knowledge base, in-app help, chatbot. L'80% delle richieste dovrebbe essere risolvibile senza umano. Analizzare i top 10 ticket topics e creare contenuti self-service per ciascuno. Implementare ticket deflection e misurarlo.

**"Health score non predice il churn"**
→ I pesi dei componenti sono sbagliati, oppure mancano componenti chiave. Back-test: prendere gli account che hanno churned negli ultimi 12 mesi e verificare se il health score li avrebbe predetti 30-60 giorni prima. Aggiustare i pesi iterativamente. Aggiungere segnali: competitor mentions, champion churn, contract downsizing.

**"Il CSM non riesce a fare upsell"**
→ Il CSM è un trusted advisor, non un venditore. L'upsell deve nascere dal valore dimostrato, non dalla pressione. Il CSM identifica l'opportunità, l'AE chiude. Se il CSM deve vendere, formarlo sulla consultative selling. Se il prodotto non giustifica l'upgrade, il problema è product, non CS.

**"Enterprise onboarding dura 6 mesi"**
→ Troppo lungo. Dividere in milestone: quick win (settimana 1), pilot (mese 1), rollout (mese 2-3). L'enterprise ha complessità (SSO, compliance, integrations), ma l'"aha moment" deve arrivare entro le prime 2 settimane, anche su un piccolo gruppo pilota. Success plan con deadline chiare.

**"Il cliente minaccia di cancellarsi per ottenere sconto"**
→ Non cedere subito. Verificare il health score: è realmente a rischio o sta bluffando? Se health > 70 e usage alta, è probabilmente una tattica negoziale. Rispondere con valore, non con sconto: "Capisco. Guardiamo il ROI che avete ottenuto quest'anno: [dati]. Il prezzo riflette questo valore." Se il rischio è reale, uno sconto temporaneo (3-6 mesi) è preferibile al churn.

---

## Domande Frequenti (FAQ)

**Q1: Quando dovrei assumere il primo CSM?**
Quando hai 30-50 clienti paganti e il churn inizia a diventare un problema quantificabile. Prima di assumere, automatizza tutto ciò che puoi (onboarding email, knowledge base, in-app help). Il primo CSM dovrebbe essere un "full-stack CS": onboarding, support, expansion, tutto.

**Q2: CSM e AE (Account Executive) dovrebbero essere la stessa persona?**
No, per account enterprise. Il CSM è un trusted advisor, l'AE è un venditore. Ruoli diversi, skill diversi, incentivi diversi. Per SMB/self-serve, spesso non serve un AE — il CSM può gestire l'expansion, o l'expansion è self-serve (in-app upgrade).

**Q3: Qual è il ratio CSM/account ideale?**
Dipende dal modello. Tech-touch: 1:1000+. Low-touch: 1:100-300. High-touch: 1:15-50. Strategic: 1:3-10. La metrica vera è ARR/CSM: quanto revenue gestisce ogni CSM? Benchmark: $1-3M ARR/CSM per mid-market, $3-10M per enterprise.

**Q4: Devo chiedere la carta di credito all'inizio del trial?**
Card upfront: conversion più alta (15-25%), ma meno signups. No card: più signups, conversion più bassa (2-5%), ma volume compensa. Test A/B per il tuo prodotto. Tendenza recente: reverse trial (accesso completo senza carta, poi soft paywall sulle feature premium).

**Q5: Come gestisco il "champion churn" (il contatto lascia l'azienda)?**
Multi-threading è la prevenzione. Quando il champion annuncia che se ne va: (1) ringraziare e chiedere di presentare il successore, (2) avviare re-onboarding con il nuovo contatto, (3) contattare l'executive sponsor per riaffermare il valore, (4) seguire il champion nella nuova azienda → possibile nuovo deal.

**Q6: NPS ogni quanto?**
Relationship NPS: trimestrale o semestrale (non più frequente, o i tassi di risposta crollano). Transactional NPS: dopo ogni interazione significativa (post-onboarding, post-support). Non misurare NPS e non agire = spreco. Meglio misurare una volta all'anno e agire, che ogni mese e ignorare.

**Q7: Devo avere un customer community?**
Sì, se hai >500 utenti attivi. La community riduce il carico su support (peer-to-peer help), aumenta il switching cost (relazioni), e genera feedback genuino. Tool: Discourse (self-hosted), Circle, Bettermode. Il costo di moderazione è il rischio: serve almeno 1 community manager part-time.

**Q8: Come pricizzo il supporto premium?**
Opzioni: incluso nel piano enterprise (più comune), add-on a % del contratto (15-25% dell'ARR), pay-per-incident (raro per SaaS). Benchmark: il supporto 24/7 con SLA < 1h costa il 20-30% in più rispetto al piano business hours.

**Q9: Vale la pena fare un cancellation flow con offerta di sconto?**
Sì, se implementato eticamente. Offri alternativa, non ostacoli. Benchmark: un buon cancellation flow salva il 10-25% delle cancellazioni. Attenzione: se i clienti imparano che minacciare la cancellazione = sconto, hai un problema di pricing, non di retention.

**Q10: Come misuro il ROI del CS team?**
Formula: (Revenue salvata da churn prevenuto + Expansion revenue attribuibile a CS) - (Costo team CS). Revenue salvata = churn rate prima di CS - churn rate dopo, moltiplicato per MRR a rischio. Se non hai dati pre-CS, confronta la retention degli account con CSM assegnato vs account senza.

**Q11: Devo usare un chatbot/AI per il supporto?**
Sì, per Tier 0 (FAQ, problemi comuni, navigazione knowledge base). No, per problemi complessi, account enterprise, o situazioni emotivamente cariche. Il chatbot deve sempre offrire l'opzione "Parla con un umano". AI può anche aiutare gli agenti (suggest risposte, categorizzare ticket, tradurre).

**Q12: In-app NPS o email NPS?**
In-app: tasso di risposta più alto (15-25% vs 5-10% per email), ma cattura solo gli utenti attivi (bias). Email: raggiunge anche gli utenti inattivi, ma tasso di risposta più basso. Ideale: in-app per relationship NPS, email per survey specifiche o per raggiungere utenti ghost.

**Q13: Come gestisco un cliente enterprise con health score critico e rinnovo tra 30 giorni?**
Escalation immediata a VP CS/CRO. Organizzare executive-to-executive call. Presentare recovery plan concreto con timeline. Offrire incentivo per rinnovo breve (6 mesi) con commitment a risolvere i problemi. In parallelo: preparare il caso peggiore (churn) e il win-back plan.

**Q14: Customer advisory board: come lo organizzo?**
Invita 10-15 top clienti (mix di segmenti e industry). Riunione trimestrale (1-2 ore, virtuale). Agenda: roadmap preview, feedback su priorità, brainstorming su nuovi use case. Incentivo: accesso anticipato a feature, sconto sul rinnovo, networking con peer. Mai più di 20 membri, altrimenti diventa ingestibile.

**Q15: Quando è il momento di passare da spreadsheet a CS platform?**
Quando: (1) hai più di 200 account attivi, (2) il team CS supera 3 persone, (3) il health score manuale non scala più, (4) hai bisogno di playbook automatizzati. Prima di investire in Gainsight/Totango ($50K+/anno), valuta alternative: Vitally (mid-market), HubSpot Service Hub, o soluzioni custom su data warehouse.

**Q16: Devo avere SLA differenti per piano?**
Assolutamente sì. I clienti enterprise pagano 10-100x di più e si aspettano un servizio proporzionale. SLA differenziati per risposta, risoluzione, canali, e copertura oraria. Comunicare gli SLA nella pricing page rinforza il valore del piano superiore.

---

## Percorso di Studio Consigliato

### Livello Base (settimana 1-2)

1. **Leggere**: "Customer Success" di Nick Mehta, Dan Steinman, Lincoln Murphy — il libro fondamentale
2. **Comprendere**: il framework del customer lifecycle e il concetto di "aha moment"
3. **Praticare**: mappare l'"aha moment" di un prodotto che usi quotidianamente
4. **Analizzare**: studiare l'onboarding di 3 SaaS che usi (Notion, Slack, Figma, HubSpot)

### Livello Intermedio (settimana 3-4)

1. **Leggere**: "The Effortless Experience" (CES e loyalty), "Obviously Awesome" (positioning)
2. **Implementare**: creare un health score per un prodotto (anche ipotetico)
3. **Progettare**: disegnare un onboarding flow completo (email + in-app)
4. **Calcolare**: esercizio su NRR, GRR, cohort analysis con dati simulati

### Livello Avanzato (settimana 5-8)

1. **Leggere**: blog di Gainsight, Totango, ChurnZero per best practice industry
2. **Studiare**: case study di CS team in aziende pubbliche (rapporti annuali, S-1)
3. **Progettare**: CS operating model completo per un SaaS B2B mid-market
4. **Analizzare**: post-mortem di churn (cause, prevenzione, lesson learned)

### Risorse Consigliate

- **Libri**: "Customer Success" (Mehta), "The Effortless Experience" (Dixon), "Farm Don't Hunt" (Nirpaz)
- **Blog/Newsletter**: Gainsight Pulse, ChurnZero blog, Vitally blog, CS Insider
- **Community**: Customer Success Network, GainGrow, CS community su LinkedIn
- **Certificazioni**: Gainsight Admin Certification, Customer Success Association (CSA), SuccessHACKER
- **Podcast**: "The Customer Success Podcast" (Gainsight), "Gain Grow Retain"

---

## Esercizi Pratici

### Esercizio 1: Trova l'"Aha Moment"
Scegli un SaaS che usi quotidianamente (Notion, Slack, Figma, etc.). Rispondi:
1. Qual è stato il momento in cui hai capito che non potevi farne a meno?
2. Quale azione specifica ti ha portato a quel momento?
3. Quanto tempo è passato dal signup a quel momento?
4. Come potresti accorciare quel tempo per un nuovo utente?

### Esercizio 2: Progetta un Onboarding
Per un SaaS ipotetico di project management:
1. Definisci l'"aha moment" (es: "il team completa il primo sprint")
2. Disegna il flow in 5 step dal signup all'"aha moment"
3. Scrivi la sequenza di 8 email per un trial di 14 giorni
4. Disegna la checklist in-app con 5 azioni

### Esercizio 3: Calcola il Health Score
Dato un account con questi dati:
- Login ultimi 30 giorni: 15 (media storica: 22) → calo 32%
- Feature usate: 3 su 10 core
- Seat attivi: 8 su 20 pagati (40%)
- Ticket aperti: 3 (1 escalation)
- Ultimo NPS: 6 (detrattore)
- Pagamenti: 1 failure negli ultimi 90 giorni
- Engagement: 0 webinar, 0 community

Calcola il health score usando i pesi della sezione "Health Score". Classifica l'account. Definisci il piano d'azione.

### Esercizio 4: Analisi Cohort
Con i seguenti dati di retention mensile:
```
        M0    M1    M2    M3    M4    M5    M6
Jan     100%  88%   82%   78%   75%   73%   72%
Feb     100%  90%   85%   81%   78%   76%   -
Mar     100%  93%   89%   85%   82%   -     -
Apr     100%  95%   92%   89%   -     -     -
```
1. Quale cohort performa meglio? Perché?
2. Il trend è in miglioramento o peggioramento?
3. A quale mese si stabilizza la retention (flattening)?
4. Se il MRR medio per cliente è $200, calcola il LTV stimato per la cohort di Aprile.

### Esercizio 5: Post-Mortem di Churn
Un account enterprise ($8K MRR) ha cancellato ieri. Informazioni:
- Health score 3 mesi fa: 72. Oggi: 28.
- Il champion è stato promosso e non gestisce più lo strumento
- L'ultimo QBR è stato 6 mesi fa
- 3 ticket aperti da 4 settimane, 1 escalation
- L'azienda sta valutando un competitor che costa il 30% in meno

Scrivi il post-mortem: (1) Cosa è andato storto? (2) Quali segnali avremmo dovuto cogliere? (3) Cosa cambiamo nel processo per prevenirlo in futuro?
