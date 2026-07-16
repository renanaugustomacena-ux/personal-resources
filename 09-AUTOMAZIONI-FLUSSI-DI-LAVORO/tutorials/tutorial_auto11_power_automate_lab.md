# Tutorial Lab — Power Automate: Cloud Flow, Microsoft 365 e Approval Workflow

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `11-power-automate-microsoft-365.md`
> **Livello:** beginner → intermediate
> **Tempo stimato:** 2.5 ore
> **Prerequisiti:** Account Microsoft 365 (Business Basic o superiore), o Microsoft 365 Developer Program (gratuito 90 giorni)
> **Versioni di riferimento:** Power Automate — versione cloud corrente (2025/2026)

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Creare Cloud Flow automatici, istantanei e schedulati
2. Usare i connettori Microsoft 365 (SharePoint, Outlook, Teams, OneDrive)
3. Costruire Approval Workflow con ciclo approvazione/rifiuto
4. Usare variabili, condizioni, loop e azioni parallele
5. Gestire errori con Scope e Configure run after
6. Analizzare il consumo di runs e ottimizzare

---

## Lab Environment Setup

```
PREREQUISITI:
  Opzione A (produzione): Microsoft 365 Business Basic (€5.60/user/mese)
  Opzione B (sviluppo): Microsoft 365 Developer Program — GRATUITO
    https://developer.microsoft.com/en-us/microsoft-365/dev-program
    Tenant di sviluppo con 25 licenze E5 per 90 giorni (rinnovabile)

ACCESSO POWER AUTOMATE:
  https://flow.microsoft.com
  → Accedi con il tuo account M365

VERIFICA LICENZA:
  Flow → Il mio account → Visualizza abbonamento
  Verifica: "Power Automate incluso" o piano specifico

NOTA: Power Automate è SaaS cloud — questo lab usa l'interfaccia web.
```

---

## Analogia Introduttiva

> **Power Automate è come l'ufficio HR di un'azienda Microsoft-first**:
> conosce tutti i dipendenti (Azure AD), tutti i documenti (SharePoint),
> tutte le email (Outlook) e tutte le chat (Teams).
>
> Quando un nuovo dipendente viene assunto (trigger: utente creato in Azure AD),
> l'ufficio HR sa già automaticamente dove mettere la sua cartella documenti
> (SharePoint), a chi mandare il benvenuto (Outlook), e in quale canale aggiungerlo (Teams).
>
> Il limite è uscire dall'ecosistema Microsoft: ogni connessione "esterna"
> (Salesforce, SAP, servizi custom) è come assumere un consulente esterno —
> funziona, ma costa di più in licenze Power Platform.

---

## Architettura Power Automate

```
┌─────────────────────────────────────────────────────────────────────┐
│                    POWER AUTOMATE ECOSYSTEM                          │
│                                                                       │
│  TIPI DI FLOW:                                                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │  Cloud Flow     │  │  Desktop Flow    │  │  Business Process │  │
│  │  (automático)   │  │  (RPA/UI)        │  │  Flow (Dataverse) │  │
│  └────────┬────────┘  └──────────────────┘  └───────────────────┘  │
│           │                                                           │
│  TRIGGER PRINCIPALI:                                                 │
│  • Automatico: evento in M365 (email, file, form)                    │
│  • Istantaneo: pulsante da Teams/app mobile                          │
│  • Schedulato: ogni ora, giorno, settimana                           │
│                                                                       │
│  CONNETTORI M365:                                                    │
│  SharePoint ──► OneDrive ──► Outlook ──► Teams ──► Forms            │
│       │                                     │                        │
│    Azure AD ◄────────────────────────── Planner                     │
│                                                                       │
│  PREMIUM CONNECTORS (richiedono licenza aggiuntiva):                │
│  Salesforce, SAP, Azure SQL, HTTP (custom API)                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Primo Cloud Flow

### A1 — Flow Schedulato: Report Settimanale

**Obiettivo**: ogni lunedì alle 8:00, raccogliere attività da Planner e inviare report via email.

```
STEP BY STEP:

1. ACCEDI A POWER AUTOMATE
   https://flow.microsoft.com → My flows → New flow → Scheduled cloud flow

2. CONFIGURA IL TRIGGER
   Nome flow: "Report Attività Settimanale"
   Starting: lunedì prossimo, 08:00
   Repeat every: 1 Week

3. AGGIUNGI AZIONE: "Get my profile (V2)" — Microsoft Graph/Azure AD
   → Salva displayName e mail per dopo

4. AGGIUNGI AZIONE: "List tasks" — Microsoft Planner
   Group Id: seleziona il tuo gruppo M365
   Plan Id: seleziona il piano
   → Restituisce array di task

5. AGGIUNGI AZIONE: "Apply to each" — sugli items di Planner
   Dentro il loop:
     - Aggiungi "Append to array variable"
       (prima inizializza variabile: Initialize Variable → taskList → Array → [])
     - Append: {
         "titolo": item('Apply_to_each')?['title'],
         "scadenza": item('Apply_to_each')?['dueDateTime'],
         "completato": item('Apply_to_each')?['percentComplete']
       }

6. AGGIUNGI AZIONE: "Send an email (V2)" — Outlook
   To: outputs('Get_my_profile_(V2)')?['body/mail']
   Subject: "Report settimanale attività"
   Body: (HTML con tabella delle attività)
```

### A2 — Espressioni Power Automate

```
SINTASSI ESPRESSIONI (Dynamic content + formula):

ACCESSO DATI:
  triggerBody()?['campo']           → dal payload trigger
  body('Nome_Azione')?['campo']     → da un'azione precedente
  item()?['campo']                  → all'interno di Apply to each
  items('Apply_to_each')?['campo']  → alternativa esplicita

OPERATORI:
  equals(x, y)                      → confronto uguaglianza
  greater(x, y)                     → x > y
  if(condizione, vero, falso)        → ternario
  empty(variabile)                   → controlla se vuoto
  not(valore)                        → negazione logica
  and(cond1, cond2)                  → AND logico
  or(cond1, cond2)                   → OR logico

STRINGHE:
  concat('Ciao', ' ', 'Mondo')       → "Ciao Mondo"
  toLower('CIAO')                    → "ciao"
  toUpper('ciao')                    → "CIAO"
  trim('  spazio  ')                 → "spazio"
  replace('testo', 'da', 'a')        → sostituzione
  substring('hello', 1, 3)           → "ell"
  length('hello')                    → 5
  contains('hello world', 'hello')   → true
  split('a,b,c', ',')                → ["a","b","c"]

DATE E ORARI:
  utcNow()                          → ISO 8601 corrente
  addDays(utcNow(), 7)              → +7 giorni
  formatDateTime(utcNow(), 'dd/MM/yyyy')  → formato EU
  convertTimeZone(utcNow(), 'UTC', 'Europe/Rome')
  dayOfWeek(utcNow())               → 0=domenica, 1=lunedì...

ARRAY/JSON:
  length(variabileArray)            → numero elementi
  first(array)                      → primo elemento
  last(array)                       → ultimo elemento
  join(array, ',')                  → array a stringa
  union(array1, array2)             → merge senza duplicati
  intersection(array1, array2)      → elementi in comune
  json('{"key":"value"}')           → parse JSON string
```

---

## PART B — Approval Workflow

### B1 — Flusso di Approvazione Documenti

**Scenario**: richiesta di acquisto → approvazione manager → notifica risultato.

```
STRUTTURA FLOW:
  [Trigger: Form inviato] 
    → [Variabili inizializzazione]
    → [Start and wait for an approval]
    → [Condizione: Approva/Rifiuta]
      ├── Approvato: [Crea ordine] → [Email conferma]
      └── Rifiutato: [Email rifiuto con commento]

STEP BY STEP:

1. TRIGGER: "When a new response is submitted" — Microsoft Forms
   Prerequisito: crea form "Richiesta Acquisto" con campi:
   - Descrizione acquisto (testo)
   - Importo stimato (numero)  
   - Giustificazione (testo multiriga)
   - Fornitore preferito (testo)

2. AZIONE: "Get response details" — Forms
   Form Id: [il tuo form]
   Response Id: triggerOutputs()?['body/resourceData/responseId']

3. AZIONE: "Initialize variable" × 3
   - richiedente: String → triggerBody()?['responder']
   - importo: Float → float(body('Get_response_details')?['r123456'])
   - approvato: Boolean → false

4. AZIONE CENTRALE: "Start and wait for an approval" (tipo: Approve/Reject - Everyone)
   Approval type: Approve/Reject - First to respond
   Title: concat('Richiesta acquisto: ', variables('importo'), '€')
   Assigned to: manager@azienda.it
   Details: concat(
     'Richiedente: ', variables('richiedente'), '\n',
     'Importo: ', string(variables('importo')), '€\n',
     'Giustificazione: ', body('Get_response_details')?['r234567']
   )
   Item link: 'https://forms.office.com/...'

5. CONDIZIONE: "Check approval outcome"
   Se: outputs('Start_and_wait_for_an_approval')?['body/outcome'] equals 'Approve'
     
     RAMO VERO (Approvato):
     - Crea item in SharePoint list "Ordini Approvati"
     - Send email: oggetto "✅ Acquisto approvato"
       Body: "La tua richiesta di €... è stata approvata"
     
     RAMO FALSO (Rifiutato):
     - Send email: oggetto "❌ Acquisto non approvato"  
       Body: concat("Motivo: ", 
         outputs('Start_and_wait_for_an_approval')?['body/responses/0/comments'])
```

### B2 — Approvazione Multi-Level

```
SCENARIO: Importo < 500€ → manager diretto; Importo > 500€ → manager + CFO

IMPLEMENTAZIONE:
1. Dopo l'inizializzazione variabili, aggiungi condizione:
   if(greater(variables('importo'), 500), true, false)

   RAMO > 500€:
     Approval type: "Approve/Reject - Everyone must approve"
     Assigned to: manager@azienda.it; cfo@azienda.it
     (Entrambi devono approvare)

   RAMO ≤ 500€:
     Approval type: "Approve/Reject - First to respond"
     Assigned to: manager@azienda.it
     (Solo il manager diretto)

2. Timeout approvazione (best practice):
   Nel trigger "Start and wait for an approval":
   Item link expiration: 48 hours
   
   Dopo il timeout: aggiungi "Condition" su outcome:
   Se outcome == "Timeout" → email escalation a HR

NOTA LICENZE APPROVAZIONI:
  Le approvazioni sono incluse nel piano M365. Tuttavia:
  - "Start and wait" blocca il flow per max 30 giorni
  - Per approvazioni long-running: usa SharePoint list come stato persistente
    + flow separati per reminder e scadenza
```

---

## PART C — Gestione Errori

### C1 — Scope e Configure run after

```
POWER AUTOMATE ERROR HANDLING:
  
  PROBLEMA DEFAULT:
  Se un'azione fallisce → il flow si ferma e segnala errore.
  Azioni successive NON vengono eseguite (nemmeno notifiche!).
  
  SOLUZIONE: Scope + Configure run after
  
  PATTERN CONSIGLIATO:
  ┌──────────────────────────────────┐
  │  Scope: "Logica principale"       │
  │  [Azione 1]                       │
  │  [Azione 2] ← può fallire         │
  │  [Azione 3]                       │
  └──────────────────────────────────┘
         │
         ▼ (esegui SE Scope = Failed)
  ┌──────────────────────────────────┐
  │  Scope: "Gestione errori"         │
  │  [Log errore in SharePoint]       │
  │  [Invia email IT con dettagli]    │
  └──────────────────────────────────┘
  
  CONFIGURAZIONE:
  1. Raggruppa azioni in "Scope" (Control → Scope)
  2. Aggiungi secondo Scope per errori
  3. Clicca "..." sul secondo Scope → Configure run after
  4. Seleziona SOLO "has failed" (deseleziona "is successful")
  5. Dentro il Scope errore:
     - result('Logica_principale') → dettagli dell'errore
     - Invia email/Teams con errore
  
  ACCEDERE ALL'ERRORE:
  result('Nome_Scope')?[0]?['error']?['message']  → messaggio errore
  result('Nome_Scope')?[0]?['status']             → 'Failed' | 'Succeeded'
```

### C2 — Retry Policy

```
CONFIGURAZIONE RETRY PER SINGOLA AZIONE:
1. Clicca "..." sull'azione → Settings
2. Retry policy:
   - None: nessun retry
   - Fixed interval: ogni N secondi, max N tentativi
   - Exponential interval: backoff esponenziale (raccomandato per API)
   - Custom: definisci interval e count manualmente

VALORI CONSIGLIATI PER API ESTERNE:
  Type: Exponential interval
  Count: 3
  Interval: PT5S (ISO 8601 = 5 secondi base)
  Minimum interval: PT5S
  Maximum interval: PT1M (max 1 minuto)

AZIONI CHE NON DEVONO AVERE RETRY:
  • Invio email (evita email doppie)
  • Creazione record (evita duplicati — usa "first do upsert check")
  • Approvazioni (crea duplicati di richieste)
```

---

## PART D — Integrazione con Teams e SharePoint

### D1 — Flow Triggered da Teams

```
SCENARIO: Comando in Teams → esegue azione → risponde nel canale

TRIGGER: "When a keyword is mentioned" — Microsoft Teams
  (Richiede Teams connector e menzione del bot configurato)

ALTERNATIVA PRATICA (Power Apps button nel canale):
  Trigger: Instant cloud flow → Input: text (il comando)

AZIONI TEAMS UTILI:
  "Post message in a chat or channel"
    - Post as: Flow bot
    - Post in: Channel
    - Team: seleziona
    - Channel: seleziona
    - Message: "✅ Operazione completata: " + variabileOutput
  
  "Post an Adaptive Card and wait for a response"
    → Invia card interattiva, attende risposta utente
    → Utile per mini-approvazioni senza abbandonare Teams
  
  "Create a meeting"
    → Crea riunione Teams automaticamente
    → Es: dopo approvazione → schedula kickoff call

D2 — SHAREPOINT OPERATIONS:
  "Create item" — crea record in lista SharePoint
  "Update item" — aggiorna record esistente
  "Get items" (con OData filter) — query lista:
    Filter query: "Stato eq 'In corso' and ImportoEUR gt 1000"
    Top count: 100
  
  FILTRI ODATA SHAREPOINT:
  "Campo eq 'valore'"          → uguale
  "Campo ne 'valore'"          → diverso
  "Campo gt 100"               → maggiore di
  "Campo lt 100"               → minore di
  "startswith(Campo, 'testo')" → inizia con
  "substringof('testo', Campo)" → contiene
  "Campo1 and Campo2"          → AND
  "Campo1 or Campo2"           → OR
```

---

## Esercizi

### Esercizio 1 — Onboarding Nuovo Dipendente (40 min)

Costruisci un flow che:
1. **Trigger**: nuova risposta in Microsoft Forms ("Richiesta Onboarding Nuovo Dipendente")
   - Campi: nome, cognome, email aziendale, reparto, manager, data inizio
2. **Azione 1**: Crea cartella OneDrive: `/Dipendenti/ANNO/NomeCompleto/`
3. **Azione 2**: Aggiungi a canale Teams del reparto corretto (usa condizione su campo reparto)
4. **Azione 3**: Invia email di benvenuto con link cartella OneDrive
5. **Azione 4**: Crea task in Planner "Setup postazione" assegnato al manager

### Esercizio 2 — Monitoring File SharePoint (20 min)

Flow schedulato ogni giorno alle 7:00:
- Legge lista SharePoint "Contratti" con OData filter: scadenza entro 30 giorni
- Per ogni contratto in scadenza: invia email al responsabile
- Se nessun contratto in scadenza: skip (aggiungi condizione su length dell'array)

### Esercizio 3 — Analisi Consumo (10 min)

In Power Automate:
- My flows → seleziona un flow → Run history
- Esporta history (CSV)
- Analizza: quante runs al mese? Qual è la durata media? Ci sono errori ricorrenti?

---

## Note Licenze e Costi

```
PIANO INCLUSO M365 BUSINESS:
  • 750 runs/utente/mese
  • Connettori Standard (M365): illimitati
  • Premium connectors (HTTP, SQL, Salesforce): NON inclusi
  
PREMIUM CONNECTORS RICHIEDONO:
  Power Automate per utente: €13.70/utente/mese
  Power Automate per flow: €13.70/flow/mese (flow condivisi illimitati)
  
ATTENZIONE: il connettore "HTTP" (custom API) è PREMIUM
  → Per chiamare API esterne gratuitamente: usa Power Automate + Azure Logic Apps
    oppure un intermediario (webhook n8n gratuito come proxy)
  → Alternativa: connettore "HTTP + Swagger" per API documentate

CALCOLO COSTI:
  15 dipendenti × 750 runs = 11.250 runs gratis/mese
  Se superi: €0.000025 per run aggiuntiva (piano pay-per-use)
  Oppure: Power Automate per flow (illimitato per quel flow specifico)
```

---

## Riferimenti

- Power Automate Docs: https://docs.microsoft.com/power-automate/
- Adaptive Cards Designer: https://adaptivecards.io/designer/
- OData Filter SharePoint: https://docs.microsoft.com/sharepoint/dev/sp-add-ins/use-odata-query-operations
- Modulo sorgente: `11-power-automate-microsoft-365.md`
