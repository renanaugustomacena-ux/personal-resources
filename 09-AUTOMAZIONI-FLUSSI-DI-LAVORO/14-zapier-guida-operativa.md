---
corso: "Automazioni e Flussi di Lavoro"
fase: "3 — Piattaforme"
modulo: 14
titolo: "Zapier — Guida Operativa Avanzata"
versione: "Zapier (web product)"
livello: "novice → competent"
prerequisiti:
  - "Moduli 01-04"
  - "Concetti base API e webhook"
obiettivi:
  - "Costruire Zap multi-step con paths, filtri e formattatori per logica condizionale"
  - "Utilizzare Code by Zapier (Python/JS) per trasformazioni dati custom"
  - "Implementare Storage by Zapier e Tables per stato persistente tra esecuzioni"
  - "Analizzare il consumo task e ottimizzare i costi rispetto ad alternative self-hosted"
  - "Configurare error handling, Auto-Replay e monitoraggio per Zap in produzione"
tag: [zapier, automazione, no-code, zap, iPaaS, task, integrazione]
---

# Zapier — Guida Operativa Avanzata

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 3 — Piattaforme · Modulo 14
> **Prerequisiti:** Moduli 01-04.
> **Obiettivi:** Zaps multi-step, paths (branching), Storage by Zapier, Code by Zapier, error handling, rate limiting.
> **Tempo:** lettura 60 min · lab 180 min
> **Livello:** novice → competent
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** Zapier (web product).

## Idee guida

1. **Zapier vince in semplicita + pricing trial.** Free tier sufficiente per <100 task/mese.
2. **Pricing per-task scala male.** A volume alto, costa molto piu di n8n self-hosted.
3. **Code by Zapier per logica custom.** JavaScript/Python inline; limitato ma utile.
4. **Path = branching.** Da usare moderatamente, sopra 4-5 path il workflow diventa ingestibile.
5. **Lock-in alto.** Migration a altri tool richiede riscrittura totale.

---

## Indice

- [Panoramica](#panoramica)
- [Pricing e Limiti dei Piani](#pricing-e-limiti-dei-piani)
- [Concetti Fondamentali](#concetti-fondamentali)
- [Trigger: Instant Webhook vs Polling](#trigger-instant-webhook-vs-polling)
- [Multi-step Zaps e Flusso dei Dati](#multi-step-zaps-e-flusso-dei-dati)
- [Paths e Branching Condizionale](#paths-e-branching-condizionale)
- [Filters](#filters)
- [Formatter by Zapier](#formatter-by-zapier)
- [Code by Zapier](#code-by-zapier)
- [Storage by Zapier](#storage-by-zapier)
- [Webhooks by Zapier](#webhooks-by-zapier)
- [Sub-Zaps e Looping by Zapier](#sub-zaps-e-looping-by-zapier)
- [Custom OAuth Apps](#custom-oauth-apps)
- [Transfer per Backfill Bulk](#transfer-per-backfill-bulk)
- [Tables e Interfaces](#tables-e-interfaces)
- [AI Features: Copilot e AI Actions](#ai-features-copilot-e-ai-actions)
- [Versioning ed Error Handling](#versioning-ed-error-handling)
- [Confronto Operativo: Zapier vs n8n vs Make](#confronto-operativo-zapier-vs-n8n-vs-make)
- [Ricette Operative per PMI Italiana](#ricette-operative-per-pmi-italiana)
- [Best Practices di Governance](#best-practices-di-governance)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Zapier è la piattaforma di workflow automation più diffusa al mondo, con oltre 7.000 integrazioni native e una base utenti dominata da PMI, team marketing e knowledge worker non tecnici. A differenza di n8n (open source, self-hostable) e Make (visuale a grafo, pricing per operations), Zapier punta sulla semplicità lineare step-by-step e sulla copertura ampia di SaaS verticali. Il target storico sono utenti business che vogliono collegare due o tre strumenti senza scrivere codice; negli ultimi anni la piattaforma ha però aggiunto strumenti destinati a casi d'uso più strutturati come Tables, Interfaces, Sub-Zaps, Code by Zapier e AI Actions.

Per una PMI italiana — il tipico studio di consulenza, agenzia marketing o azienda manifatturiera con 5-50 dipendenti — Zapier rappresenta spesso il primo gradino dell'automazione. Il vantaggio decisivo è la presenza nativa di app italiane o europee comuni (Fatture in Cloud, Aruba, TeamSystem in alcune integrazioni community, Pipedrive, HubSpot, Gmail, Outlook, Slack, Teams, Notion, Airtable, Google Sheets) e la possibilità di costruire flussi funzionanti in pochi minuti senza dover gestire infrastruttura. Lo svantaggio principale è il modello di pricing per "task" — ogni azione eseguita in uno Zap consuma uno o più task — che diventa rapidamente costoso man mano che cresce il volume di esecuzioni.

In questa guida analizzeremo Zapier dal punto di vista operativo: i piani e i loro limiti reali, l'anatomia di uno Zap multi-step, il branching con Paths, le funzionalità "Built-in" (Filter, Formatter, Code, Storage, Webhooks, Looping, Sub-Zap), la creazione di Custom OAuth Apps per integrare applicativi aziendali privati, le best practice di governance per organizzazioni con decine o centinaia di Zap attivi, e infine il confronto pragmatico con n8n e Make per aiutare a scegliere lo strumento giusto in base al contesto.

---

## Pricing e Limiti dei Piani

Comprendere il pricing di Zapier è essenziale prima di progettare automazioni: il costo cresce in modo non lineare con il numero di task, e alcune funzionalità (Paths, Premium Apps, Code) sono disponibili solo dai piani superiori.

### Tier Disponibili

I piani di Zapier sono articolati in cinque livelli principali (i numeri esatti possono variare nel tempo, verificare sempre `zapier.com/pricing`):

- **Free**: 100 task al mese, solo Zap a 2 step (trigger + 1 action), polling ogni 15 minuti, nessuna Premium App, nessun Path, nessun Filter, nessun Formatter avanzato. Adatto solo a sperimentazione.
- **Starter** (~20 €/mese): 750 task, Zap multi-step (fino a 3 step), Filter, Formatter, accesso a 3 Premium App. Polling ogni 15 minuti.
- **Professional** (~50 €/mese): 2.000 task, Zap multi-step illimitati, Paths, accesso illimitato a Premium Apps, Webhooks by Zapier, Code by Zapier. Polling ogni 2 minuti.
- **Team** (~70-120 €/mese): 50.000 task, condivisione di Zap e connessioni tra utenti, folder condivise, autorizzazioni granulari. Polling ogni minuto sulle Premium Apps.
- **Company / Enterprise** (custom): SAML SSO, audit log, dedicated support, SCIM provisioning, advanced analytics, advanced admin controls, custom data retention.

### Cos'è un "Task"

Un task viene contato ogni volta che uno Zap esegue un'action con successo. I trigger non contano come task, e nemmeno i Filter che bloccano l'esecuzione (uno Zap "fermato" da un Filter consuma 0 task). Anche gli step di Formatter, Code e Path contano come task — questo è un dettaglio cruciale: uno Zap multi-step che pulisce dati con tre Formatter consecutivi consuma 3 task per esecuzione, anche se l'output finale è una singola riga in Google Sheets.

Esempio pratico di calcolo: Zap che riceve webhook da Tally, applica due Formatter (date + text), un Filter che lascia passare solo lead italiani, e infine crea una riga in Google Sheets + invia email Gmail = 4 task per esecuzione (2 Formatter + 1 Sheets + 1 Gmail). Con 500 lead/mese si arriva a 2.000 task, esattamente il limite del piano Professional.

### Premium Apps

Alcune integrazioni sono classificate come "Premium" e richiedono almeno il piano Starter. La lista include tipicamente Salesforce, HubSpot (alcuni endpoint), Zendesk, Magento, Shopify (per certe action), Webhooks by Zapier, Code by Zapier, e altre integrazioni enterprise. La distinzione cambia nel tempo, va verificata in fase di progettazione.

### Task Overage

Se si supera il limite mensile di task, Zapier non blocca immediatamente gli Zap: continua ad eseguirli e fattura overage al mese successivo a tariffa maggiorata, oppure suggerisce un upgrade. Il comportamento esatto dipende dal piano e dalle impostazioni dell'account; è prudente impostare alert email a 80% e 100% del task limit per evitare sorprese in bolletta.

---

## Concetti Fondamentali

### Zap

Uno Zap è il flusso di automazione completo: un trigger seguito da una o più action. Ogni Zap ha un nome, può essere attivato o disattivato, ha una storia di esecuzioni (Task History) e può essere organizzato in folder.

### Trigger

Il trigger è l'evento che avvia lo Zap. Può essere un evento esterno (nuova riga su Google Sheets, nuovo lead da Facebook Ads, webhook in arrivo) oppure uno schedule (Schedule by Zapier che si attiva ogni X minuti/ore/giorni).

### Action

L'action è ciò che lo Zap fa quando il trigger si attiva: creare un record, inviare un'email, chiamare un'API. Uno Zap può avere fino a centinaia di action concatenate (limite teorico ~100, praticamente sconsigliato superare 10-15 per leggibilità).

### Filter

Il Filter è uno step speciale che valuta una condizione: se la condizione è vera, lo Zap continua; se è falsa, lo Zap si ferma e non consuma task per gli step successivi.

### Path

Il Path è il branching condizionale: lo Zap si dirama in più rami (fino a 5 paths nella maggior parte dei piani), ciascuno con la propria logica e le proprie action. Equivale ai router di Make o ai nodi Switch di n8n.

### Sub-Zap

Un Sub-Zap è uno Zap che viene chiamato da un altro Zap come fosse una funzione. Permette modularità e riuso: uno Zap "principale" passa dati a uno Zap "secondario" che esegue una logica condivisa (es. "invia notifica multi-canale").

### Looping by Zapier

Looping by Zapier permette di iterare su un array di elementi e ripetere le action successive una volta per ciascun elemento. Equivale agli Iterator di Make o al meccanismo di item-per-item di n8n.

### Storage by Zapier

Storage by Zapier è un key-value store interno con persistenza tra esecuzioni. Permette di mantenere stato (contatori, flag, ultimo ID processato) senza dover usare un database esterno.

---

## Trigger: Instant Webhook vs Polling

### Polling Triggers

La maggior parte dei trigger Zapier funziona in modalità polling: ogni X minuti Zapier interroga l'API dell'app sorgente per verificare se ci sono nuovi dati. La frequenza dipende dal piano:

- Free / Starter: ogni 15 minuti
- Professional: ogni 2 minuti
- Team / Company: ogni 1 minuto (su Premium Apps)

Conseguenze operative del polling:

- Latenza minima 1-15 minuti tra evento sorgente e azione Zapier.
- Consumo di chiamate API anche quando non ci sono nuovi dati.
- Possibili duplicati o record persi se l'API sorgente non garantisce ordinamento stabile o cursori robusti.

### Instant Triggers (Webhook)

Gli Instant Trigger usano webhook push: l'app sorgente notifica Zapier appena un evento si verifica. La latenza è di pochi secondi. Esempi di app con instant trigger nativo: Slack, Stripe, Typeform, Tally, Webflow, Calendly, GitHub, Discord, Pipedrive (su alcuni eventi), HubSpot (su alcuni eventi).

Quando un'app non offre instant trigger nativo ma supporta webhook, è possibile usare "Webhooks by Zapier (Catch Hook)" come trigger custom — vedi sezione dedicata.

### Schedule by Zapier

Schedule by Zapier permette trigger temporali: ogni ora, ogni giorno alle 09:00, ogni lunedì, una sola volta a una data specifica. Utile per report periodici, sync notturni, reminder.

```
Trigger: Schedule by Zapier — Every Day at 8:00 AM Europe/Rome
Action 1: Google Sheets — Get Many Rows (filtered: status = "pending")
Action 2: Looping by Zapier — Iterate over rows
Action 3: Gmail — Send Email (reminder al cliente)
```

---

## Multi-step Zaps e Flusso dei Dati

Uno Zap multi-step concatena trigger + N action, dove ogni step può accedere all'output degli step precedenti tramite un sistema di campi mappabili.

### Mapping dei Campi

Quando si configura un'action, i campi possono essere riempiti con valori statici oppure mappati da output di step precedenti. L'editor mostra un drop-down "Insert Data" che elenca tutti i campi disponibili, etichettati con il numero di step e il nome del campo. Esempio: `1. Email Address`, `2. Formatted Date`, `3. Code Output`.

### Tipi di Dato

Zapier passa i dati come stringhe, numeri, boolean, array e oggetti. Quando un campo sorgente è un array (es. `tags: ["italia", "veneto", "lead"]`), Zapier lo serializza per default come stringa separata da virgola (`italia, veneto, lead`). Per iterare su elementi dell'array serve Looping by Zapier.

### Line Items

I "line items" sono un concetto Zapier per gestire collezioni in un singolo step: tipicamente righe di un ordine, righe di una fattura, righe di un foglio. Quando un trigger restituisce line items, le action successive possono essere configurate per processarli tutti insieme (es. "Create Multiple Rows" su Google Sheets) oppure per iterare uno per uno con Looping.

### Test Data

Durante la configurazione, Zapier permette di usare dati di test reali (presi dall'ultima esecuzione del trigger) per verificare il mapping. Questo è il momento per scoprire campi mancanti, formati inattesi e null values.

---

## Paths e Branching Condizionale

Paths by Zapier permette di creare rami condizionali: lo Zap valuta condizioni e segue il ramo corrispondente. Ogni Path ha le proprie action e può essere visto come uno "switch" multi-condizione.

### Anatomia di un Path

```
Trigger: Webhook Catch Hook (lead da landing page)
  ↓
Step 2: Formatter — Lowercase email
  ↓
Path A (condizione: tags contiene "enterprise")
  → Action: HubSpot — Create Deal (pipeline Enterprise)
  → Action: Slack — Notifica al team Enterprise
Path B (condizione: tags contiene "smb")
  → Action: HubSpot — Create Deal (pipeline SMB)
  → Action: Mailchimp — Add Subscriber (lista SMB)
Path C (condizione: nessuna delle precedenti)
  → Action: Google Sheets — Append Row (foglio "lead non classificati")
```

### Limiti dei Paths

- Massimo 5 paths per nodo Path (aumentabile su piani Team/Company).
- Le condizioni sono valutate nell'ordine di definizione; il primo path vero viene eseguito.
- Per default i path sono **mutuamente esclusivi**: solo un path viene eseguito per esecuzione. Per esecuzioni multiple in parallelo serve un altro Zap o Sub-Zap.
- Gli step dentro a un path consumano task come gli step normali.

### Quando Usare Paths vs Filter

Filter è semplice: una condizione, lo Zap continua o si ferma. Path è più potente: più condizioni, ciascuna con flusso dedicato. Se il caso d'uso è "esegui solo se X", basta Filter. Se è "fai A se X, B se Y, C altrimenti", servono Paths.

---

## Filters

Un Filter blocca lo Zap se la condizione non è soddisfatta. È lo strumento più importante per controllare i task consumati: meglio un Filter early che esegue zero task downstream, piuttosto che far girare tutto e poi scartare.

### Operatori Disponibili

I Filter di Zapier supportano operatori per stringhe, numeri, date, boolean ed esistenza:

- **Text**: contains, does not contain, exactly matches, does not exactly match, starts with, ends with, is empty, is not empty.
- **Number**: greater than, less than, equal to, not equal to, between.
- **Date**: before, after, equal to (con parsing automatico di formati comuni).
- **Boolean**: is true, is false.

### Logica AND / OR

I Filter supportano combinazioni: condizioni in AND (tutte vere) e gruppi separati per OR. Esempio: `(email contains "@aziendaitaliana.it" AND status equals "active") OR (tags contains "vip")`.

### Esempi Pratici

```
Filter: continua solo se
  - country exactly matches "IT"
  - email is not empty
  - revenue greater than 0
```

```
Filter: continua solo se l'orario corrente NON è notturno
  - hour_of_day greater than 7
  - hour_of_day less than 22
```

---

## Formatter by Zapier

Formatter è lo step "swiss army knife" per trasformare dati senza scrivere codice. È diviso in categorie: Date/Time, Numbers, Text, Utilities.

### Date / Time

- **Format Date/Time**: converte tra formati (es. `2026-04-22T14:30:00Z` → `22 aprile 2026, 16:30`). Supporta timezone, locale italiano.
- **Add/Subtract Time**: aggiunge giorni, ore, minuti.
- **Compare Dates**: differenza tra due date.

Esempio di trasformazione data per fattura italiana:

```
Input: 2026-04-22T14:30:00Z
Format: DD/MM/YYYY
Timezone: Europe/Rome
Output: 22/04/2026
```

### Numbers

- **Perform Math Operation**: addizione, sottrazione, moltiplicazione, divisione, modulo.
- **Format Number**: separatore migliaia, decimali, simbolo valuta (€, $).
- **Spreadsheet-Style Formula**: espressioni stile Excel.

### Text

- **Capitalize, Lowercase, Uppercase, Titlecase**.
- **Find / Replace**: con supporto regex.
- **Split Text**: divide stringa in array secondo separatore.
- **Truncate**: tronca a N caratteri.
- **Extract Email Address / Phone Number / URL**: parser dedicati.
- **URL Encode / Decode**.

### Utilities

- **Lookup Table**: mappa valori (es. `EN → English`, `IT → Italiano`, `DE → Deutsch`).
- **Pick from List**: seleziona elemento N da un array.
- **Line-itemize / De-Line-itemize**: converte array in line items e viceversa.
- **Import CSV File**: parser CSV inline.

### Pattern: Lookup Table per Localizzazione

Per gestire traduzioni o mapping codice-descrizione senza database esterno:

```
Lookup Key: country_code (es. "IT")
Lookup Table:
  IT  → Italia
  FR  → Francia
  DE  → Germania
  ES  → Spagna
Fallback: Sconosciuto
Output: stringa localizzata
```

---

## Code by Zapier

Code by Zapier permette di eseguire Python o JavaScript inline come step di uno Zap. È disponibile dal piano Professional in su (categoria Premium App).

### Limiti Tecnici

- **Tempo di esecuzione massimo**: 1 secondo (Starter), 10 secondi (Professional+), 30 secondi (Team/Company su alcuni runtime).
- **Memoria**: ~256 MB.
- **Output massimo**: ~6 MB.
- **Pacchetti**: solo standard library Python; per Node.js disponibili `fetch`, `crypto`, `Buffer` e altri built-in. Non si possono installare pacchetti npm o pip.
- **Networking**: si possono fare richieste HTTP outbound, ma con timeout stretti.

### Esempio Python

```python
# input_data viene passato dallo step precedente
# Esempio: input_data = {"email": "MARIO.ROSSI@AZIENDA.IT", "vat": "IT12345678901"}

email = input_data.get("email", "").strip().lower()
vat = input_data.get("vat", "").replace(" ", "").upper()

# Validazione VAT italiana (lunghezza)
is_valid_vat = vat.startswith("IT") and len(vat) == 13 and vat[2:].isdigit()

# Estrazione dominio
domain = email.split("@")[-1] if "@" in email else ""

output = {
    "email_clean": email,
    "vat_clean": vat,
    "is_valid_vat": is_valid_vat,
    "domain": domain
}
```

`output` è un dict Python (o oggetto JS); i suoi campi diventano disponibili come output dello step e mappabili nei passi successivi.

### Esempio JavaScript

```javascript
// inputData è l'oggetto dallo step precedente
const email = (inputData.email || "").trim().toLowerCase();
const vat = (inputData.vat || "").replace(/\s/g, "").toUpperCase();

const isValidVat = vat.startsWith("IT") && vat.length === 13 && /^\d+$/.test(vat.slice(2));

output = {
  email_clean: email,
  vat_clean: vat,
  is_valid_vat: isValidVat,
  domain: email.includes("@") ? email.split("@").pop() : ""
};
```

### Quando Usare Code by Zapier

- Quando Formatter non basta (es. logica di parsing complessa, validazione regex multi-step).
- Per chiamate HTTP custom con autenticazione speciale.
- Per generare hash/firme HMAC (es. per integrazioni outbound che richiedono firma).
- Per consolidare più output in uno solo.

### Quando NON Usare Code by Zapier

- Per logiche lunghe (>10 secondi di esecuzione) — usare un servizio esterno.
- Per dipendere da pacchetti pip/npm — non disponibili.
- Per logiche stateful complesse — usare Storage by Zapier o database esterno.

---

## Storage by Zapier

Storage by Zapier è un key-value store con persistenza tra esecuzioni di Zap. Ogni account ha uno storage condiviso identificato da una "Storage Key" (UUID generato alla prima creazione, riutilizzato in tutti gli Zap).

### Operazioni Disponibili

- **Set Value**: imposta key → value.
- **Get Value**: legge value associato a key.
- **Get All Values**: legge tutto lo storage.
- **Increment Value**: incrementa contatore numerico atomicamente.
- **Decrement Value**.
- **Push Value Onto List**: aggiunge a lista.
- **Pop Value Off List**.
- **Remove Value**: cancella key.

### Use Case Tipici

- **Deduplicazione**: salvare ID processati in storage e controllare prima di processare.
- **Contatori**: numero progressivo per fatture, ticket, riferimenti.
- **Stato cursori**: ultimo timestamp processato per evitare duplicati su sync.
- **Rate limiting custom**: contatori per finestre temporali.
- **Configurazione condivisa**: feature flag, parametri runtime modificabili senza editare lo Zap.

### Esempio: Deduplicazione

```
Step 1: Webhook Catch Hook (riceve order_id)
Step 2: Storage by Zapier — Get Value (key: "order_" + order_id)
Step 3: Filter — continua solo se Get Value è vuoto
Step 4: Storage by Zapier — Set Value (key: "order_" + order_id, value: timestamp)
Step 5: HubSpot — Create Deal
```

### Limiti

- Storage non è un database transazionale: niente query, niente indici.
- Latency variabile, non garantita.
- Nessun TTL automatico: per pulire vecchie chiavi serve uno Zap schedulato dedicato.

---

## Webhooks by Zapier

Webhooks by Zapier (Premium App) permette di ricevere webhook custom (Catch Hook) e di fare richieste HTTP outbound (Custom Request, GET, POST, PUT, PATCH, DELETE).

### Catch Hook (Trigger)

Quando si crea uno Zap con trigger "Webhooks by Zapier — Catch Hook", Zapier genera un URL univoco del tipo `https://hooks.zapier.com/hooks/catch/12345/abcdef/`. Qualunque sistema può fare POST/GET a quell'URL e Zapier triggererà lo Zap con il body come input.

Esempio test con curl:

```bash
curl -X POST https://hooks.zapier.com/hooks/catch/12345/abcdef/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "lead_created",
    "email": "mario.rossi@aziendaitaliana.it",
    "company": "Acme SRL",
    "vat": "IT12345678901"
  }'
```

Variante "Catch Raw Hook": Zapier passa il body raw come stringa anziché parsare JSON. Utile quando serve verificare firma HMAC sul payload originale (vedi documento sicurezza webhook).

### Custom Request (Action)

Permette di chiamare API esterne. Configurabili: URL, method, headers, body (form-encoded, JSON, raw), authentication (Basic, custom).

Esempio: notificare un endpoint interno aziendale dopo creazione lead.

```
Method: POST
URL: https://internal.aziendaitaliana.it/api/lead
Headers:
  Authorization: Bearer {{secret_token}}
  Content-Type: application/json
Body (JSON):
  {
    "email": "{{step1_email}}",
    "source": "zapier-webhook",
    "received_at": "{{step2_iso_date}}"
  }
```

Webhooks by Zapier permette anche metodo PUT/PATCH/DELETE, autenticazione Basic Auth via username/password e custom headers per token bearer o API key.

---

## Sub-Zaps e Looping by Zapier

### Sub-Zaps

Un Sub-Zap (disponibile dal piano Professional) è uno Zap richiamabile da un altro Zap come fosse una funzione. Lo Zap "padre" passa input al Sub-Zap, attende il risultato, e usa l'output negli step successivi.

Pattern tipico: estrarre logica condivisa (es. "validazione lead", "notifica multi-canale") in un Sub-Zap riutilizzabile da più Zap.

```
Zap Padre 1 (lead da Tally)         Zap Padre 2 (lead da Facebook Ads)
       ↓                                       ↓
  preparazione dati                   preparazione dati
       ↓                                       ↓
       └────────── Sub-Zap "Notifica Lead" ────┘
                            ↓
              Slack + Email + HubSpot Create Contact
```

Vantaggio: una modifica al Sub-Zap si propaga a tutti i caller. Svantaggio: ogni call al Sub-Zap consuma task aggiuntivi.

### Looping by Zapier

Looping by Zapier itera su un array e ripete gli step successivi una volta per elemento.

```
Step 1: Trigger (riceve un ordine con line_items)
Step 2: Looping by Zapier — Create Loop From Line-Items
        Input: line_items (array di prodotti)
Step 3: Google Sheets — Create Row (eseguito una volta per riga)
Step 4: Send Email (eseguito una volta per riga)
```

Limiti: Looping by Zapier ha un massimo di iterazioni per esecuzione (tipicamente 500-10.000 a seconda del piano), ed ogni iterazione consuma task come fossero step normali. Per loop molto grandi può essere più efficiente delegare a uno script esterno o batch processing.

---

## Custom OAuth Apps

Per integrare un'applicazione interna aziendale o un SaaS non presente nel marketplace Zapier, è possibile creare una **Private Integration** via Zapier Platform CLI/UI. Le Private Integration sono visibili solo all'account che le crea (oppure al team se condivise).

### Quando Serve

- Applicativo interno aziendale con API REST custom.
- SaaS verticale italiano non presente nel marketplace.
- Estensione di un'app esistente con endpoint custom.

### Workflow di Creazione

1. Andare su `developer.zapier.com` con l'account Zapier.
2. Creare una "New Integration" (Private).
3. Configurare authentication: API Key, Basic Auth, OAuth2, Session Auth.
4. Definire trigger (polling o REST hook), action, search.
5. Per ogni endpoint specificare URL, metodo, mapping di input/output.
6. Testare con dati reali via "Visual Builder" o `zapier test` (CLI).
7. Pubblicare come Private Integration → invitare utenti del proprio team.

### Esempio OAuth2

Per integrare un applicativo che usa OAuth2 standard:

- Authorization URL: `https://app.aziendaitaliana.it/oauth/authorize`
- Access Token URL: `https://app.aziendaitaliana.it/oauth/token`
- Refresh Token URL: `https://app.aziendaitaliana.it/oauth/token`
- Scope: `read write`
- Client ID / Client Secret: registrare la app Zapier come OAuth client nell'applicativo target.

---

## Transfer per Backfill Bulk

Zapier Transfer è uno strumento separato dagli Zap, pensato per spostare dati storici in bulk tra app. A differenza degli Zap (event-driven), Transfer è batch: si seleziona un dataset sorgente, si applicano filtri/mapping, e si esegue il trasferimento una sola volta (o ripetutamente con cadenza manuale).

### Use Case

- Backfill di tutti i lead esistenti su Google Sheets in HubSpot.
- Migrazione di tutti gli ordini Shopify storici in un foglio analytics.
- Sync ricorrente settimanale di un dataset da un'app all'altra.

### Limiti

- Numero massimo di record per transfer dipende dal piano (es. 5.000 sul Professional).
- Rate limiting dell'API target può rallentare l'esecuzione.
- Non sostituisce uno Zap event-driven: per sync continuo serve uno Zap.

---

## Tables e Interfaces

Negli ultimi anni Zapier ha aggiunto due strumenti che estendono il prodotto oltre il classico "due app collegate":

### Zapier Tables

Database relazionale-leggero nativo Zapier. Permette di creare tabelle con colonne tipizzate (testo, numero, data, link, allegato, formula, lookup), record manipolabili da UI, e integrazione bidirezionale con gli Zap (un record creato in Tables triggera Zap; uno Zap può creare/leggere/aggiornare record).

Sostituto leggero di Airtable per chi è già nell'ecosistema Zapier. Adatto a casi d'uso semplici (CRM minimal, tracker progetti, log eventi); per workload più complessi conviene comunque Airtable o un DB vero.

### Zapier Interfaces

Builder no-code di pagine web semplici (form, dashboard, portali clienti minimal) integrate nativamente con Zap e Tables. Caso d'uso tipico: form pubblico → Tables + Zap di notifica.

---

## AI Features: Copilot e AI Actions

### Zapier Copilot

Assistente AI integrato che suggerisce e costruisce Zap a partire da descrizioni in linguaggio naturale. Esempio: "Quando ricevo email Gmail con allegato fattura, salva su Google Drive e notifica Slack" → Copilot propone una bozza di Zap.

Utile come acceleratore di prototipazione; va comunque verificato passo per passo, perché può sbagliare mapping o suggerire app subottimali.

### AI Actions (con LLM)

Action native che chiamano modelli LLM (OpenAI, Anthropic, modelli di terze parti) per task come classificazione, sommarizzazione, estrazione strutturata. Esempio: "Riassumi questa email in 3 bullet point", "Classifica questo lead in [hot, warm, cold]", "Estrai partita IVA e ragione sociale da questo testo".

Considerazioni operative:

- Costo extra: oltre ai task Zapier si paga il costo del modello (token).
- Rate limit del provider LLM (OpenAI/Anthropic).
- Output non deterministico: serve sempre un Filter o validazione downstream.
- Privacy / GDPR: i dati passano attraverso l'API del modello — verificare contratti DPA e residenza dati.

---

## Versioning ed Error Handling

### Versioning degli Zap

Zapier mantiene una **history** delle modifiche di ogni Zap. È possibile vedere chi ha modificato cosa e quando. Non c'è però un vero "versioning git-like": non si può fare diff tra versioni o rollback granulare. Per rollback completo a uno stato precedente serve duplicare lo Zap a partire da una snapshot e disattivare la versione corrente.

Buona prassi: prima di modifiche significative su Zap critici, creare una copia "BACKUP - YYYY-MM-DD" disattivata.

### Auto-Replay

Quando uno step fallisce per errore transiente (timeout API, 500 server error, rate limit 429), Zapier può riprovare automaticamente. Auto-replay è disponibile dal piano Professional e va abilitato per ogni Zap o globalmente.

### Manual Replay

In Task History si può vedere ogni esecuzione e re-eseguire manualmente quelle fallite. Utile dopo aver corretto un bug nello Zap o dopo che l'API target è tornata online.

### Error Notifications

Zapier invia email all'account owner quando uno Zap fallisce. È possibile configurare:

- **Per ogni errore**: utile per Zap critici a basso volume.
- **Sommario giornaliero**: utile per Zap ad alto volume con qualche errore tollerabile.
- **Webhook a Slack/Discord/altro**: per integrazione con il sistema di alerting aziendale.

### Zap Error State

Se uno Zap fallisce ripetutamente (default: 7 giorni consecutivi senza esecuzione riuscita), Zapier può disattivarlo automaticamente per evitare loop di errori. Va riattivato manualmente dopo aver risolto il problema.

---

## Confronto Operativo: Zapier vs n8n vs Make

| Criterio | Zapier | n8n | Make |
|----------|--------|-----|------|
| **Modello** | SaaS chiuso | Open source self-hostable o cloud | SaaS chiuso |
| **Pricing** | Per task | Per execution (cloud) o gratis (self-host) | Per operation |
| **Curva di apprendimento** | Bassa | Media-alta | Media |
| **Numero integrazioni** | 7.000+ | 400+ nativi + HTTP generico + community | 1.800+ |
| **Code custom** | Code by Zapier (limitato) | Function/Code node (completo, npm) | Custom modules JS limitati |
| **Branching** | Paths (max 5) | Switch/IF illimitati | Router illimitati |
| **Loop / iterazione** | Looping by Zapier | Item-per-item nativo | Iterator/Aggregator |
| **Self-host** | No | Sì (open source) | No |
| **GDPR / data residency** | Multi-region (limitato) | Totale (self-host) | EU region disponibile |
| **Adatto a** | Knowledge worker, marketing, PMI no-tech | Team tecnici, compliance stringente | Power user, scenari complessi medi |

### Quando Scegliere Zapier (per PMI Italiana)

- Team senza competenze tecniche: il drag & drop lineare è il più accessibile.
- Bisogno di integrazioni di nicchia (SaaS verticali) presenti solo nel marketplace Zapier.
- Volumi bassi-medi (< 5.000 task/mese): pricing ancora gestibile.
- Time-to-market importante: prototipo funzionante in ore, non giorni.

### Quando Scegliere n8n

- Compliance/GDPR rigorosi: dati e credenziali devono restare on-premise.
- Volumi alti: il pricing per task di Zapier diventa proibitivo, mentre n8n self-hosted ha solo costo infrastruttura.
- Logica complessa che richiede vero codice (npm packages, librerie custom).
- Team con competenze devops minime per gestire un container.

### Quando Scegliere Make

- Scenari complessi con molti rami e aggregazioni (l'interfaccia a grafo è più adatta della lineare).
- Volumi medio-alti con logica condizionale densa: il modello "operations" può essere più conveniente del "task" Zapier.
- Bisogno di iterator/aggregator nativi senza dover saltare attraverso Looping.

---

## Ricette Operative per PMI Italiana

### Ricetta 1: Lead Facebook Ads → CRM HubSpot

```
Trigger: Facebook Lead Ads — New Lead in Form
  ↓
Step 2: Formatter — Lowercase email
  ↓
Step 3: Formatter — Title Case full_name
  ↓
Step 4: Filter — continua solo se email is not empty
  ↓
Step 5: HubSpot — Create or Update Contact
  - Email: {{step2 email}}
  - First name / Last name: split da {{step3 full_name}}
  - Source: "Facebook Ads"
  ↓
Step 6: Slack — Send Channel Message #lead-vendite
  - "Nuovo lead da Facebook: {{nome}} ({{email}}) — campagna {{campaign_name}}"
```

Task per esecuzione: ~4 (Formatter x2 + HubSpot + Slack). Con 200 lead/mese = 800 task → piano Starter sufficiente.

### Ricetta 2: Fattura Fatture in Cloud → Notifica Slack

```
Trigger: Fatture in Cloud — New Invoice (polling 15min)
  ↓
Step 2: Formatter — Format Number (importo in euro con separatore italiano)
  ↓
Step 3: Formatter — Format Date (data in DD/MM/YYYY, timezone Europe/Rome)
  ↓
Step 4: Path A — se importo > 1000€
  → Slack — DM al titolare "Fattura grossa! €{{importo}} a {{cliente}}"
Step 4: Path B — se importo <= 1000€
  → Slack — Channel #amministrazione "Nuova fattura €{{importo}} a {{cliente}}"
```

Note: l'integrazione "Fatture in Cloud" su Zapier non è ufficiale di TeamSystem ma esiste come community/private integration. In alternativa, configurare il webhook nativo di Fatture in Cloud verso "Webhooks by Zapier — Catch Hook".

### Ricetta 3: Form Tally → Google Sheets + Email + Trello

```
Trigger: Tally — New Submission (instant webhook)
  ↓
Step 2: Code by Zapier (Python) — validazione VAT italiana, classificazione lead
  Output: { is_valid, classification }
  ↓
Step 3: Filter — continua solo se is_valid = true
  ↓
Step 4: Path A — classification = "enterprise"
  → Google Sheets — Append Row (foglio "Lead Enterprise")
  → Trello — Create Card (board "Sales", list "New Enterprise")
  → Gmail — Send Email al sales lead
Step 4: Path B — classification = "smb"
  → Google Sheets — Append Row (foglio "Lead SMB")
  → Mailchimp — Add Subscriber (audience "SMB-IT")
```

---

## Best Practices di Governance

In organizzazioni con decine o centinaia di Zap attivi, la governance diventa critica per evitare caos, sovrapposizioni e debito tecnico.

### Naming Convention

Adottare un naming consistente per Zap, Folder, Connessioni e Storage Keys:

- **Zap**: `[area] - [trigger app] → [action app] - [scopo]` — es. `[Sales] Tally → HubSpot - Lead Capture`.
- **Folder**: per area aziendale (Sales, Marketing, Operations, Finance, IT).
- **Storage Keys**: namespace con prefisso — es. `sales_dedup_lead_<id>`, `finance_counter_invoice_<year>`.
- **Sub-Zap**: prefisso `[SUB]` — es. `[SUB] Notify Multi-Channel`.

### Folder Organization

Usare Folder per raggruppare Zap per area, criticità o cliente. I piani Team consentono Folder condivise tra utenti del team.

Struttura tipica:

```
/ Sales
  / Lead Capture
  / Lead Nurturing
/ Marketing
  / Email Automation
  / Social Media
/ Operations
  / Onboarding
  / Support
/ Finance
  / Fatturazione
  / Pagamenti
/ _Archived
/ _Sub-Zaps
/ _Templates
```

### Shared Accounts vs Personal Accounts

In team piccoli è tentazione collegare connessioni con account personali ("login mio Gmail"). Questo crea fragilità: se la persona lascia, gli Zap si rompono. Best practice:

- Creare account "service" dedicati per le integrazioni critiche (es. `automazioni@aziendaitaliana.it`).
- Documentare quali Zap usano quale connessione.
- Sui piani Team, condividere connessioni a livello team con audit log.

### Zapier Manager (Account Multi-Tenant)

Per agenzie e consulenti che gestiscono Zapier per clienti, esiste Zapier Manager (in evoluzione, verificare nomi attuali nei piani Team/Company): permette di gestire più account cliente da una dashboard unica, separando billing e ownership.

### Documentazione Esterna

Anche se Zapier ha una propria UI, è utile mantenere un documento esterno (Notion, Confluence, foglio condiviso) con:

- Elenco Zap attivi, scopo, owner.
- Diagramma di flusso macro per processi che attraversano più Zap.
- Procedure di rollback / disaster recovery.
- Lista delle API key e segreti usati (in password manager, mai inline).

### Audit Periodico

Ogni 3-6 mesi:

- Disattivare/archiviare Zap inutilizzati (zero esecuzioni in 90 giorni).
- Rivedere consumo task per ottimizzare gli Zap più costosi.
- Verificare connessioni "degraded" o token scaduti.
- Aggiornare documentazione.

---

## Troubleshooting

### Lo Zap non si è attivato

Cause comuni:

1. **Polling non ancora avvenuto**: attendere fino al ciclo successivo (1-15 min in base al piano).
2. **Trigger condition non soddisfatta**: verificare che l'evento sorgente corrisponda esattamente al filtro del trigger.
3. **Connessione scaduta**: in "My Apps" controllare se la connessione è "Disabled" o "Reauthorize required".
4. **Zap disabilitato**: verificare lo stato ON/OFF.
5. **Limite task raggiunto**: account in overage può sospendere esecuzioni.

### Dati mancanti negli step

- Aprire la Task History e ispezionare l'output dello step incriminato.
- Se il campo è presente ma vuoto, l'API sorgente non lo ha popolato per quell'esecuzione.
- Se il campo non compare, potrebbe essere stato aggiunto dopo l'ultima "Test Trigger": rifare il test del trigger e ri-mappare.

### Errori 429 (Rate Limit)

L'API target ha imposto rate limit. Soluzioni:

- Abilitare auto-replay: Zapier riprova automaticamente con backoff.
- Inserire un Delay by Zapier tra step ripetitivi.
- Per loop su molti record, usare Schedule by Zapier per spalmarli nel tempo.
- Se persistente, contattare il provider per quote più alte.

### Zap a Loop Infinito

Caso classico: Zap A modifica un record in Sheet, e quella modifica triggera Zap B che modifica di nuovo, attivando ancora Zap A. Soluzioni:

- Usare un "marker field" (es. colonna `processed = true`) e Filter early per fermare il loop.
- Usare Storage by Zapier per dedup su ID record.
- Strutturare i trigger per essere event-specifici (es. "new row" anziché "any change").

### Webhook Catch Hook non riceve dati

- Verificare che l'URL sia esattamente quello generato da Zapier (case-sensitive).
- Se il sender invia GET ma Zapier si aspetta POST, riconfigurare il trigger.
- Per debug, usare `webhook.site` come destinazione temporanea per ispezionare il payload, poi sostituire l'URL.

### Code by Zapier in Timeout

- Ridurre la quantità di dati processati per esecuzione.
- Spostare logica in servizio esterno e chiamare via Webhook.
- Su piani Team/Company il timeout è più alto.

### Filter "Did not pass" inatteso

- Aprire Task History → step Filter → vedere "Conditions evaluated" per capire quale condizione ha bloccato.
- Spesso causa: campo formato come stringa "0" anziché numero 0, oppure email con spazi non strippati.

### Errore "Action failed" su step intermedio senza dettagli

**Sintomi**: un'azione fallisce con messaggio generico "Action failed" senza codice di errore specifico.

**Causa**: spesso causato da un campo obbligatorio mancante o un tipo di dato errato nell'input mappato. Zapier non sempre propaga il messaggio di errore dell'API sottostante.

**Soluzione**: (1) Aprire Task History → cliccare sullo step fallito → ispezionare "Input Data" per verificare che tutti i campi obbligatori siano popolati. (2) Testare la stessa chiamata API manualmente (Postman/curl) con gli stessi dati per ottenere un messaggio di errore dettagliato. (3) Verificare che i tipi corrispondano (es. un campo ID che deve essere numero ma riceve stringa).

### Sub-Zap non restituisce dati al Zap chiamante

**Sintomi**: il Sub-Zap viene eseguito correttamente ma il Zap principale non riceve il valore di ritorno.

**Causa**: (1) Il Sub-Zap non ha un'azione "Return from Sub-Zap" alla fine. (2) I campi di output non sono stati mappati. (3) Il Sub-Zap fallisce silenziosamente e Zapier procede senza output.

**Soluzione**: (1) Aggiungere sempre un'azione "Return from Sub-Zap" come ultimo step. (2) Verificare che i campi di ritorno siano definiti nel trigger del Sub-Zap. (3) Aggiungere un filtro nel Zap principale per gestire il caso in cui il Sub-Zap non restituisca dati.

### Looping by Zapier esegue solo il primo elemento

**Sintomi**: il Loop elabora solo il primo elemento dell'array e ignora i successivi.

**Causa**: il campo passato al Loop non è un array JSON valido, oppure il separatore per "line item" non corrisponde al formato dei dati.

**Soluzione**: (1) Verificare che il campo sia un array JSON valido — usare Formatter → Utilities → Line Itemizer se necessario. (2) Se i dati arrivano come stringa separata da virgole, usare Formatter → Text → Split per convertire in array. (3) Controllare il conteggio degli elementi nel Task History.

### Webhook Catch Hook riceve JSON annidato come stringa

**Sintomi**: i campi del JSON ricevuto dal webhook appaiono come stringa unica anziché come campi separati.

**Causa**: il Content-Type dell'invio non è `application/json`, oppure il body è stato double-encoded.

**Soluzione**: (1) Verificare che il mittente invii con header `Content-Type: application/json`. (2) Se il JSON è dentro una stringa, usare Code by Zapier con `JSON.parse(inputData.rawBody)` per estrarre i campi. (3) Se il mittente non può essere modificato, usare Formatter → Utilities per estrarre i valori dal testo.

### Formatter perde dati con caratteri speciali

**Sintomi**: campi con accenti, emoji, o caratteri UTF-8 vengono troncati o corrotti dopo un passaggio nel Formatter.

**Causa**: alcune operazioni del Formatter (Split, Truncate) non gestiscono correttamente i caratteri multi-byte.

**Soluzione**: (1) Usare Code by Zapier (JavaScript/Python) per manipolazioni di testo con caratteri speciali. (2) Normalizzare l'input (rimuovere emoji) prima del Formatter se non sono necessari. (3) Testare con dati reali contenenti caratteri speciali, non solo con dati ASCII.

### Zap si disattiva automaticamente senza errore apparente

**Sintomi**: un Zap attivo da settimane si disattiva da solo. Nessun errore nel Task History.

**Causa**: (1) Connessione OAuth scaduta (il token refresh è fallito). (2) Il piano ha raggiunto il limite di task e Zapier ha sospeso i Zap. (3) Cambio password sull'app connessa senza riautorizzare.

**Soluzione**: (1) Controllare "My Apps" → verificare che tutte le connessioni siano "Connected". (2) Verificare l'utilizzo task nella dashboard Billing. (3) Configurare notifiche email per Zap disabilitati (Settings → Notifications).

### Path: tutte le condizioni sono "true" ma solo un path esegue

**Sintomi**: più di un Path dovrebbe eseguire perché le condizioni sono soddisfatte, ma Zapier esegue solo il primo.

**Causa**: comportamento previsto — i Path in Zapier sono esclusivi per impostazione predefinita (simile a switch/case con break implicito).

**Soluzione**: se serve esecuzione parallela di più rami, usare approcci alternativi: (1) Un Filter per ogni ramo al posto dei Path. (2) Più Zap separati, ognuno con il proprio filtro. (3) Code by Zapier per implementare la logica e produrre output multipli.

### Storage by Zapier: "Secret not found"

**Sintomi**: tentativo di leggere un valore da Storage restituisce "Secret not found" anche se è stato scritto in precedenza.

**Causa**: (1) Il valore è stato scritto con una chiave diversa (case-sensitive). (2) Il valore è stato sovrascritto con valore vuoto. (3) Account diverso: Storage è isolato per account Zapier.

**Soluzione**: (1) Verificare la chiave esatta (case-sensitive, senza spazi extra). (2) Usare "Get Value" con un valore di default per gestire il caso "not found": `Get Value → if empty → use default`. (3) Loggare ogni operazione di scrittura su Storage per tracciabilità.

---

## Anti-pattern Zapier

### 1. Zap a Catena Lunga (> 10 Step)

**Problema**: un Zap con 15+ step che gestisce l'intero flusso business — dalla ricezione del lead al nurturing, passando per CRM, email, Slack, e reporting.

**Conseguenza**: un errore in qualsiasi step blocca tutto il flusso. Il debug richiede di scorrere decine di step. Ogni task consumato include tutti i passaggi anche quando non necessari.

**Soluzione**: decomporre in Zap modulari collegati tramite Sub-Zap o Webhook. Ogni Zap ha una responsabilità: (1) Ingestion + validazione, (2) Enrichment, (3) CRM update, (4) Notifiche.

### 2. Usare Polling Trigger per Eventi Rari

**Problema**: trigger polling (ogni 2-15 min) per eventi che accadono 1-2 volte al giorno.

**Conseguenza**: task consumati per check vuoti (su piani a pagamento, ogni check vuoto NON consuma task, ma su piani con polling lento si perde reattività). Tempo reale peggiorato.

**Soluzione**: dove disponibile, usare trigger Instant (webhook). Se l'app non supporta webhook, valutare Webhooks by Zapier con un intermediario. Per app legacy, implementare un bridge che converta polling in push.

### 3. Code by Zapier per Tutto

**Problema**: usare Code by Zapier per logica che Zapier gestisce nativamente (formattazione, filtri, lookup).

**Conseguenza**: codice fragile senza test, difficile da debuggare, limiti di timeout, nessun error handling strutturato.

**Soluzione**: usare Code by Zapier SOLO quando la logica non è esprimibile con step nativi: calcoli complessi, hash/crittografia, parsing di formati non standard, aggregazioni avanzate. Per tutto il resto, preferire Formatter, Filter, Path.

### 4. Nessuna Deduplicazione su Trigger

**Problema**: un trigger che invia lo stesso record più volte (es. "Updated Row" su Google Sheets quando più colonne cambiano in sequenza).

**Conseguenza**: azioni duplicate — email inviate 2 volte, record CRM duplicati, notifiche ridondanti.

**Soluzione**: (1) Usare un campo "processed" nel record sorgente e filtrare early. (2) Usare Storage by Zapier per dedup basata su ID: `Get Value(id) → if exists → STOP, else → Set Value(id) → continue`. (3) Rendere le azioni idempotenti (upsert anziché insert).

### 5. Ignorare la Task History

**Problema**: non monitorare la Task History, scoprendo errori solo quando un utente segnala dati mancanti.

**Conseguenza**: errori silenti per giorni/settimane, dati persi, fiducia nel sistema compromessa.

**Soluzione**: (1) Abilitare "Error notifications" per ogni Zap critico. (2) Creare un Zap di monitoraggio che verifica periodicamente lo stato degli altri Zap tramite Zapier Management API. (3) Controllare la Task History almeno settimanalmente.

### 6. Hard-coding Email e Valori nei Step

**Problema**: indirizzo email del destinatario, URL dell'API, soglie numeriche inserite direttamente nei campi dei step.

**Conseguenza**: per cambiare un valore bisogna modificare il Zap, con rischio di errori e nessuna tracciabilità delle modifiche.

**Soluzione**: (1) Usare Storage by Zapier per parametri configurabili (chiave: "alert_email", valore: "team@example.com"). (2) Leggere i parametri all'inizio del Zap. (3) Documentare quali Zap dipendono da quali parametri.

### 7. Zap di Produzione Senza Filtri

**Problema**: un Zap che processa TUTTI gli eventi del trigger senza filtri, inclusi dati di test, record duplicati, eventi irrilevanti.

**Conseguenza**: task consumati inutilmente, azioni su dati sporchi, noise nelle notifiche.

**Soluzione**: aggiungere un Filter immediatamente dopo il trigger per scartare eventi non rilevanti. Filtrare per: (1) stato del record (es. `status != "test"`), (2) sorgente (es. `source != "internal"`), (3) completezza dei dati (es. `email exists`).

### 8. Transfer by Zapier per Sincronizzazione Continua

**Problema**: usare Transfer by Zapier (progettato per migrazioni batch una tantum) per sincronizzazione continua.

**Conseguenza**: nessun meccanismo incrementale, rielabora tutti i record ad ogni esecuzione, consumo task massivo.

**Soluzione**: usare Transfer solo per backfill iniziale o migrazioni. Per sincronizzazione continua, creare Zap con trigger incrementale (es. "New or Updated" con filtro sulla data di modifica).

### 9. Path con Troppe Diramazioni

**Problema**: un Zap con Path che ha 10+ rami condizionali, ognuno con logica complessa.

**Conseguenza**: impossibile da debuggare, facile introdurre errori logici, manutenzione è un incubo.

**Soluzione**: se servono più di 3-4 Path, (1) decomporre in Zap separati con filtri specifici, (2) usare Code by Zapier per centralizzare la logica decisionale e produrre un singolo output "action_type", (3) usare un Sub-Zap per ogni branch complesso.

### 10. Nessun Naming Convention

**Problema**: Zap denominati "Untitled Zap", "Copy of Copy of...", azioni con label di default.

**Conseguenza**: con 50+ Zap, nessuno sa cosa fa cosa. Onboarding impossibile.

**Soluzione**: adottare convenzione: `[APP1→APP2] Descrizione breve` per i Zap (es. `[Form→HubSpot] Lead capture`). Organizzare in folder per dominio (Sales, Marketing, Operations). Rinominare ogni step con la sua funzione specifica.

---

## Sicurezza Zapier

### Modello di Sicurezza della Piattaforma

Zapier gestisce credenziali e dati secondo questi principi:

```
FLUSSO SICUREZZA ZAPIER:
┌────────────────────────────────────────────────┐
│ 1. OAuth tokens crittografati a riposo (AES)   │
│ 2. Comunicazioni TLS 1.2+                      │
│ 3. Data retention: task history per 7-30 gg    │
│ 4. SOC 2 Type II, SOC 3 certificati            │
│ 5. GDPR compliant (DPA disponibile)            │
│ 6. Data residency: US (default), EU su request │
└────────────────────────────────────────────────┘
```

### Gestione Accessi e Permessi

Per account Team/Company:

| Ruolo | Permessi |
|---|---|
| **Admin** | Gestione account, billing, connessioni, tutti i Zap |
| **Manager** | Creare/modificare Zap nella propria cartella, gestire connessioni |
| **Member** | Creare/modificare Zap propri, usare connessioni condivise |
| **Viewer** (Company only) | Solo visualizzazione |

**Best practice**: (1) Un Admin per account, non condividere credenziali admin. (2) Connessioni condivise solo per servizi comuni (Slack, email). (3) Ogni membro usa le proprie credenziali per app sensibili (CRM, DB). (4) Audit trimestrale delle connessioni attive.

### Webhook Security

I Webhook Catch Hook di Zapier non supportano autenticazione nativa. Mitigazioni:

1. **Token nel query string**: `https://hooks.zapier.com/hooks/catch/123/abc/?token=secret_value`. Primo step: Filter → `token = valore atteso`, altrimenti stop.

2. **HMAC nel body/header**: se il mittente supporta HMAC (es. GitHub, Stripe), usare Code by Zapier per verificare la firma:

```javascript
// Code by Zapier — Verifica HMAC
const crypto = require('crypto');
const secret = 'whsec_your_webhook_secret';
const signature = inputData.signature; // header x-hub-signature-256
const body = inputData.rawBody;

const expected = 'sha256=' + crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

output = [{
  valid: crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  )
}];
```

3. **IP Whitelisting**: non possibile nativamente su Zapier. Usare un intermediario (Cloudflare Workers, AWS API Gateway) che filtri per IP prima di inoltrare a Zapier.

### Protezione Dati Sensibili

- **Non loggare PII in Slack/email**: usare ID di riferimento, non dati personali. "Nuovo lead ID #4523" anziché "Nuovo lead Mario Rossi, mario@email.com".
- **Mascherare dati nei campi**: usare Formatter → Text → Truncate per mascherare (es. `****@email.com`).
- **Storage by Zapier non è un vault**: non memorizzare password, token API, o segreti in Storage. Usare i campi connessione nativi.
- **Data retention minima**: su piani Team+, configurare la retention della Task History al minimo necessario.

### Conformita GDPR per Zap

- **DPA**: Zapier offre un Data Processing Agreement — firmarlo prima di elaborare dati di residenti EU.
- **Diritto all'oblio**: implementare un Zap "delete user data" che, dato un ID/email, cancelli i dati da tutti i sistemi collegati.
- **Registrazione trattamenti**: documentare quali Zap elaborano quali categorie di dati personali.
- **Minimizzazione**: nei mapping, includere solo i campi strettamente necessari — non mappare "tutti i campi" per comodita.

---

## Monitoraggio e Osservabilita Zapier

### Dashboard Nativa

Zapier offre una dashboard con:
- **Task Usage**: consumo task vs quota del piano
- **Zap Health**: Zap attivi, in errore, disabilitati
- **Task History**: log dettagliato per Zap e per step

### Costruire Monitoring Custom

Per monitoraggio proattivo oltre la dashboard nativa:

```
ARCHITETTURA MONITORING ZAPIER:
┌─────────────────────────────────┐
│        Zapier Account           │
│  [Zap 1] [Zap 2] ... [Zap N]  │
│           │                     │
│           v                     │
│  [Error Notification Zap]      │
│  (trigger: Zapier Manager       │
│   action: any Zap errored)     │
└──────────┬──────────────────────┘
           │
    ┌──────┼──────┐
    v      v      v
 [Slack] [Sheet] [PagerDuty]
 (alert) (log)   (escalation)
```

### Metriche da Monitorare

| Metrica | Soglia | Azione |
|---|---|---|
| Task consumati / quota | > 80% | Ottimizzare o upgrade |
| Zap in stato errore | > 0 | Investigate immediatamente |
| Zap disabilitati imprevisti | > 0 | Verificare connessioni |
| Task falliti / giorno | > 5% | Root cause analysis |
| Tempo medio per task | Trend crescente | Profiling step lenti |
| Connessioni scadute | > 0 | Riautorizzare |

### Alerting Best Practices

1. **Notifiche per Zap critici**: abilitare "Notify me" per errori su ogni Zap di produzione (Settings → Notifications).
2. **Zap di meta-monitoraggio**: creare un Zap che verifica lo stato degli altri Zap e notifica anomalie.
3. **Report settimanale**: schedulare un report con consumo task, errori, e Zap più costosi.
4. **Escalation**: Slack per warning, email per errori, SMS/PagerDuty per Zap business-critical in errore.

---

## Ottimizzazione Costi Zapier

### Comprendere il Modello di Costo

Zapier addebita per **task** consumati:

```
1 azione eseguita con successo = 1 task
(trigger NON consuma task)
(filter che blocca NON consuma task)

Esempio — Zap con 5 step:
  Trigger (0 task) → Filter pass (0 task) → Action (1) → Action (1) → Action (1)
  = 3 task per esecuzione

Esempio — Zap con Path:
  Trigger (0) → Path A (2 azioni) = 2 task
  Trigger (0) → Path B (1 azione) = 1 task
  (solo il path eseguito consuma task)

Esempio — Loop su 50 elementi:
  Trigger (0) → Loop (50 iterazioni × 1 azione) = 50 task
```

### Strategie di Riduzione Task

| Strategia | Risparmio Tipico | Come |
|---|---|---|
| Filter aggressivi dopo trigger | 20-50% | Scartare eventi non rilevanti |
| Consolidare notifiche con Digest | 60-90% | Un messaggio riepilogativo anziché N |
| Webhook anziché polling | 0% (task) ma miglior latenza | Trigger instant |
| Dedup con Storage | 10-30% | Evitare elaborazione duplicata |
| Batch con Looping ottimizzato | Variabile | Processare in bulk dove possibile |
| Sub-Zap per logica condizionale | 10-40% | Eseguire step costosi solo quando necessario |
| Code by Zapier per multi-step | 30-60% | Un step di codice vs 3 step nativi |

### Calcolo TCO Mensile Zapier

```
TCO = Costo piano Zapier
    + Costo overage task (se superato il piano)
    + Costo premium app surcharge
    + Costo ore manutenzione
    + Costo API esterne (se a consumo)

Esempio pratico:
  Piano Professional: $49/mese (2.000 task)
  Media task/mese: 1.800
  Premium apps: incluse nel piano
  Manutenzione: 1 ora/mese × €50 = €50
  API esterne: €10/mese
  ────────────────────────────────
  TCO: ~€107/mese
  Risparmio vs manuale: 20h/mese × €25 = €500
  ROI: (500 - 107) / 107 = 367%
```

### Quando Migrare da Zapier

```
Segnali di migrazione:
  - Task/mese > 50.000 costantemente → valutare Make o n8n
  - Logica complessa in Code by Zapier in > 30% dei Zap → valutare n8n
  - Costo mensile > €300 → confronto TCO con alternative
  - Vendor lock-in preoccupante → valutare n8n self-hosted
  - Requisiti on-premise o data residency → n8n self-hosted
  
Non migrare se:
  - Task < 5.000/mese e logica semplice → Zapier è conveniente
  - Team non tecnico → UX Zapier è superiore
  - Integrazioni con app premium Zapier-only
```

---

## Pattern Avanzati Zapier

### Pattern: Event-Driven Multi-Zap con Storage Condiviso

Per flussi complessi che coinvolgono più Zap indipendenti che condividono stato:

```
Zap A: "Lead Ingestion"
  [Webhook: nuovo lead]
  → [Storage: Set lead_status_{id} = "new"]
  → [HubSpot: create contact]
  → [Storage: Set lead_status_{id} = "crm_created"]

Zap B: "Lead Enrichment" (trigger: schedule ogni 5 min)
  [Storage: Get All → filter status = "crm_created"]
  → [Per ogni lead: HTTP → Clearbit enrichment]
  → [HubSpot: update contact con enrichment data]
  → [Storage: Set lead_status_{id} = "enriched"]

Zap C: "Lead Notification"
  [HubSpot trigger: contact property "enriched" = true]
  → [Filter: score > soglia]
  → [Slack: notifica #sales con dettagli]
  → [Storage: Set lead_status_{id} = "notified"]
```

### Pattern: Retry Manuale con Escalation

Per azioni che devono essere ritentate con controllo fine:

```
Zap principale:
  [Trigger] → [Azione target]
  → Se errore:
      [Webhooks by Zapier: POST a retry Zap]
      payload: {action, data, attempt: 1, max_attempts: 3}

Zap retry:
  [Webhook Catch Hook: ricevi retry request]
  → [Delay: 5 minuti × attempt]
  → [HTTP: esegui azione originale]
  → [Router]
      ├─ Successo: [Storage: clear retry flag] → [Slack: "recovered"]
      └─ Errore + attempt < max:
          [Webhooks: POST a se stesso con attempt+1]
      └─ Errore + attempt >= max:
          [Email: escalation al team]
          [Storage: Set failed_{id} = true]
```

### Pattern: Approval Workflow (Human-in-the-Loop)

Per operazioni che richiedono approvazione umana prima dell'esecuzione:

```
Zap 1: "Request Approval"
  [Trigger: nuova richiesta]
  → [Storage: Set request_{id} = {data, status: "pending"}]
  → [Email/Slack: invia richiesta di approvazione con link]
      Link: webhook URL + ?id={id}&action=approve/reject

Zap 2: "Process Approval"
  [Webhook: ricezione risposta approvazione]
  → [Storage: Get request_{id}]
  → [Filter: status = "pending"] (evita doppia elaborazione)
  → [Router]
      ├─ action = "approve":
      │   → [Esegui azione approvata]
      │   → [Storage: Set status = "approved"]
      │   → [Notifica richiedente: "Approvato"]
      └─ action = "reject":
          → [Storage: Set status = "rejected"]
          → [Notifica richiedente: "Rifiutato con motivo"]
```

### Pattern: Aggregazione Digest Periodica

Per consolidare eventi frequenti in un unico messaggio periodico:

```
Zap 1: "Collect Events" (trigger: ogni evento)
  [Trigger: nuovo evento]
  → [Code by Zapier:]
      // Leggi digest corrente da Storage
      // Aggiungi evento formattato
      // Salva digest aggiornato
  → [Storage: Append a digest_{today}]

Zap 2: "Send Digest" (trigger: schedule ore 9:00)
  [Schedule: ogni giorno alle 9:00]
  → [Storage: Get digest_{yesterday}]
  → [Filter: digest non vuoto]
  → [Formatter: formatta come report HTML]
  → [Email/Slack: invia digest]
  → [Storage: Delete digest_{yesterday}]
```

---

## Ricette di Integrazione Avanzate Zapier

### Ricetta: Gestione Ordini E-commerce Multi-canale

**Obiettivo**: consolidare ordini da Shopify, WooCommerce e Amazon in un unico sistema gestionale.

```
Zap A: [Shopify: New Order]
  → [Formatter: normalizza formato ordine]
  → [Webhooks: POST → Zap Dispatcher]

Zap B: [WooCommerce: New Order]
  → [Formatter: normalizza formato ordine]
  → [Webhooks: POST → Zap Dispatcher]

Zap C: [Webhooks: Catch Hook → Amazon SQS polling]
  → [Formatter: normalizza formato ordine]
  → [Webhooks: POST → Zap Dispatcher]

Zap Dispatcher:
  [Webhook: ricevi ordine normalizzato]
  → [Storage: dedup su order_id]
  → [HTTP: POST gestionale/ordini] (crea ordine)
  → [Google Sheets: log ordine]
  → [Slack: #ordini "Nuovo ordine #{id} da {canale}"]
```

### Ricetta: Monitoring SLA con Escalation Temporizzata

**Obiettivo**: monitorare ticket di supporto e applicare escalation se SLA violato.

```
Zap 1: [Zendesk: New Ticket]
  → [Storage: Set ticket_{id} = {created_at, priority, status: "open"}]
  → [Slack: #support "Nuovo ticket #{id}"]

Zap 2: [Schedule: ogni 15 minuti]
  → [Code by Zapier:]
      // Leggi tutti i ticket aperti da Storage
      // Calcola tempo trascorso
      // Identifica SLA violati (priority alta > 1h, media > 4h, bassa > 24h)
  → [Filter: SLA violati > 0]
  → [Looping: per ogni ticket in violazione]
      → [Router per livello]
          ├─ 1x SLA: [Slack: @canale reminder]
          ├─ 2x SLA: [Email: team lead]
          └─ 3x SLA: [PagerDuty: incident]

Zap 3: [Zendesk: Ticket Closed]
  → [Storage: Delete ticket_{id}]
```

### Ricetta: Content Pipeline Multi-piattaforma

**Obiettivo**: pubblicare contenuti su più piattaforme social con adattamento automatico.

```
Zap: [Airtable: New Record in "Content Calendar" con status = "Ready"]
  → [Airtable: Get Record completo (immagine, testo, hashtag)]
  → [Path per piattaforma]
      ├─ Path A: LinkedIn
      │   → [Formatter: tronca a 3000 char, formatta hashtag]
      │   → [LinkedIn: Create Post]
      │
      ├─ Path B: Twitter/X
      │   → [Formatter: tronca a 280 char, abbrevia link]
      │   → [Twitter: Create Tweet]
      │
      └─ Path C: Instagram
          → [Code by Zapier: prepara caption con emoji + hashtag]
          → [Buffer/Later: Schedule Post]
  → [Airtable: Update Record status = "Published"]
  → [Slack: #marketing "Pubblicato: {titolo}"]
```

---

## FAQ — Domande Frequenti Zapier

### 1. Qual e la differenza tra Task e Execution in Zapier?

Un'**execution** è l'attivazione completa di un Zap (dal trigger all'ultimo step). I **task** sono le singole azioni eseguite con successo. Il trigger e i filtri NON consumano task. Un Zap con 4 azioni eseguito 1 volta consuma 4 task. Il piano limita i task mensili, non le esecuzioni.

### 2. Posso usare Zapier per sincronizzazione bidirezionale?

Si, ma richiede attenzione per evitare loop infiniti. Pattern: creare 2 Zap (A→B e B→A) con deduplicazione. Ogni Zap aggiunge un marker (es. campo `last_synced_by = "zapier"`) e l'altro Zap filtra i record con quel marker. Usare Storage per tracciare gli ID già sincronizzati.

### 3. Code by Zapier supporta librerie esterne (npm/pip)?

No. Code by Zapier esegue JavaScript (Node.js) o Python in un ambiente sandbox isolato. Librerie disponibili: `crypto`, `btoa`, `atob` per JS; `requests`, `json`, `datetime` per Python. Per librerie complesse, eseguire il codice su un server esterno (Lambda, Cloud Function) e chiamarlo via HTTP da Zapier.

### 4. Come posso testare un Zap senza consumare task?

Non è possibile eseguire azioni senza consumare task. Strategie: (1) usare un account di test dedicato. (2) Aggiungere un filtro temporaneo che blocca l'esecuzione dopo il primo test riuscito. (3) Usare "Test step" nella modalità editor — testa un singolo step alla volta consumando 1 task. (4) Per Zap con molti step, testare prima solo trigger + filter (0 task) per verificare i dati.

### 5. Zapier garantisce l'ordine di esecuzione dei task?

Gli step all'interno di un Zap vengono eseguiti in ordine sequenziale. Tuttavia, se un trigger produce più eventi contemporaneamente (es. 10 nuove righe in Google Sheets), non è garantito l'ordine di elaborazione tra le diverse esecuzioni del Zap. Per garantire l'ordine, processare i record con un campo sequenziale e verificare nel Zap.

### 6. Cosa succede ai task in eccesso quando supero il piano?

Zapier non blocca immediatamente — applica una policy di overage: (1) Le prime volte, Zapier invia un warning email. (2) Se il superamento è costante, Zapier può suggerire un upgrade o, in casi estremi, sospendere i Zap. (3) Su piani Company, l'overage viene fatturato. Configurare sempre alerting al raggiungimento dell'80% della quota.

### 7. Come gestisco Zap che elaborano dati personali (GDPR)?

(1) Firmare il DPA con Zapier. (2) Minimizzare i dati: mappare solo i campi necessari. (3) Non loggare PII in Slack/email — usare ID. (4) Configurare retention minima per Task History. (5) Implementare un Zap "Right to Erasure" che cancelli i dati su richiesta. (6) Documentare i trattamenti in un registro interno.

### 8. Posso schedulare un Zap per orari specifici (es. solo orario lavorativo)?

Si. Opzioni: (1) Usare "Schedule by Zapier" come trigger con orario specifico. (2) Per Zap con trigger evento, aggiungere un Filter: `{{zap_meta_human_now}}` con condizione "time is between 09:00 and 18:00" e "day is not Saturday/Sunday". (3) Per scheduling complesso, usare Code by Zapier per verificare il calendario lavorativo.

### 9. E possibile versioning dei Zap?

Zapier offre "Versions" per Zap (su piani Team+): puoi creare una nuova versione, testare, e pubblicare. La versione precedente rimane disponibile per rollback. Su piani Free/Professional, non c'è versioning nativo — documentare le modifiche manualmente e mantenere screenshot/note delle configurazioni.

### 10. Come migro Zap tra account Zapier?

(1) Su piani Team/Company, usare "Transfer Zap" (Settings → Transfer). (2) Su piani individuali, ricreare manualmente. (3) Per automazione della migrazione, usare Zapier Management API per esportare la configurazione e ricrearla nel nuovo account.

### 11. Zapier e adatto per volumi elevati (> 100.000 task/mese)?

Dipende dalla complessità. Per volumi alti con logica semplice (trigger → 1-2 azioni), si — il piano Company scala. Per volumi alti con logica complessa, valutare: (1) il costo diventa significativo ($), (2) la latenza può aumentare sotto carico. Alternative per volumi molto alti: n8n self-hosted, Make (operations spesso più economiche), o soluzioni custom (Lambda, Step Functions).

### 12. Come gestisco timeout nelle azioni Zapier?

Zapier impone un timeout per step (30 secondi su Free/Professional, 60 su Team/Company). Se un'API è lenta: (1) eseguire l'operazione heavy su un servizio esterno e usare Zapier solo per orchestrare. (2) Implementare un pattern asincrono: Zapier invia la richiesta, un secondo Zap con schedule polling verifica il completamento. (3) Contattare Zapier support per aumenti di timeout su piani Company.

### 13. Posso usare Zapier con API che richiedono file upload?

Si, con limitazioni. (1) File piccoli (< 50 MB): usare il campo "File" nel mapping — Zapier passa l'URL del file. (2) File da URL: molte app accettano un URL anziché il file binary — usare Formatter per costruire l'URL. (3) Per file grandi o formati complessi: caricare prima su un servizio storage (S3, Google Drive) e passare l'URL a Zapier.

### 14. Come implemento un Zap che elabora dati in batch (es. report giornaliero)?

(1) Trigger: Schedule by Zapier (es. ogni giorno alle 8:00). (2) Azione: HTTP GET per recuperare dati dall'API con parametri temporali (es. `?date=yesterday`). (3) Code by Zapier: formattare i dati come tabella/report. (4) Azione finale: inviare report via Email/Slack. Per dati da Google Sheets, usare "Lookup Spreadsheet Rows" per recuperare tutte le righe con un filtro.

### 15. E possibile eseguire Zap in parallelo?

No, i Zap vengono eseguiti sequenzialmente. Se un trigger produce 10 eventi contemporaneamente, Zapier li elabora uno alla volta. Per parallelismo: (1) distribuire il lavoro su più Zap indipendenti tramite webhook. (2) Usare un servizio esterno (Lambda, Cloud Function) per elaborazione parallela e raccogliere i risultati in Zapier.

### 16. Come gestisco Zap che devono elaborare line items (es. prodotti in un ordine)?

Zapier gestisce i line items nativamente in alcune app (Shopify, QuickBooks). (1) Verificare se l'app target supporta "Create Line Items" come campo nativo nel mapping. (2) Se l'app non supporta line items nativi, usare **Looping by Zapier**: passare l'array di line items e creare un record per ogni elemento. (3) Per aggregazione inversa (più record → un unico output con line items), usare **Formatter → Utilities → Line Itemizer** per costruire l'array.

### 17. Qual e la differenza tra Zapier Tables e Storage by Zapier?

**Storage by Zapier**: semplice key-value store per memorizzare singoli valori o piccoli set. Ideale per flag, contatori, dedup, configurazione. Limite: 500 record per account. **Zapier Tables**: database relazionale leggero con UI tabulare, campi tipizzati, vista, filtri. Ideale per gestire elenchi strutturati (contatti, ticket, inventario) con interfaccia visuale. Tables supporta trigger e azioni nativi ("New Record in Table", "Update Record"). Storage è per stato semplice; Tables è per dati strutturati con UI.

### 18. Come posso creare un'integrazione custom per un'app non supportata da Zapier?

(1) **Webhooks by Zapier**: se l'app supporta webhook outgoing, usare "Webhooks by Zapier → Catch Hook" come trigger. Per inviare dati all'app, usare "Webhooks by Zapier → Custom Request" come azione. (2) **Zapier Developer Platform** (`developer.zapier.com`): creare un'integrazione completa con trigger, azioni, e autenticazione custom. L'integrazione può essere privata (solo per il tuo account) o pubblica (disponibile per tutti). (3) Per API semplici, spesso Webhooks by Zapier è sufficiente senza bisogno di creare un'app custom.

### 19. Come monitoro il consumo di task in tempo reale?

(1) Dashboard Zapier → Settings → Billing → Task Usage: mostra il consumo corrente vs quota. (2) Creare un Zap di monitoraggio: Schedule (ogni giorno) → Code by Zapier (query Zapier Management API per task usage) → Filter (se usage > 80%) → Slack/Email alert. (3) Zapier invia un'email automatica quando il consumo raggiunge il 75% e il 100% della quota mensile.

---

## Riferimenti

- Documentazione ufficiale Zapier: `zapier.com/help`
- Pricing aggiornato: `zapier.com/pricing`
- Zapier Platform (per Custom Integration): `developer.zapier.com`
- Community e template: `zapier.com/apps`
- Status page: `status.zapier.com`
- Code by Zapier reference: `zapier.com/help/create/code-webhooks/use-code-by-zapier`
- Webhooks by Zapier guide: `zapier.com/help/create/code-webhooks/trigger-zaps-from-webhooks`
- Storage by Zapier guide: `zapier.com/help/create/storage`
- Confronto pratico Zapier vs n8n vs Make: vedi documenti `09-n8n-guida-completa-self-hosted.md` e `10-make-integromat-guida-operativa.md` di questa libreria.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Zapier — Getting Started Guide: https://zapier.com/help/create/basics/learn-key-concepts-in-zapier (consultato: 2026-05-24)
- Zapier — Paths (Conditional Logic): https://zapier.com/help/create/customize/add-branching-logic-to-zaps-with-paths (consultato: 2026-05-24)
- Zapier — Error Handling and Troubleshooting: https://zapier.com/help/troubleshoot/behavior/troubleshoot-errors-in-zapier (consultato: 2026-05-24)
- Zapier — Tables Documentation: https://zapier.com/help/create/tables (consultato: 2026-05-24)
- Zapier — Transfer (Bulk Data Migration): https://zapier.com/help/create/transfer (consultato: 2026-05-24)
- Zapier Platform — Build Custom Integrations: https://platform.zapier.com/quickstart/introduction (consultato: 2026-05-24)

### Libri

- **"Enterprise Integration Patterns"** — Gregor Hohpe, Bobby Woolf (Addison-Wesley). Pattern fondamentali (message routing, transformation, splitter) che si ritrovano nei Zap multi-step.
- **"Automate the Boring Stuff with Python"** — Al Sweigart (No Starch Press, 2a ed.). Utile per capire quando il limite no-code impone il passaggio a scripting — complemento a Code by Zapier.

---

## Esercizi

1. **Lab — Zap multi-step.** Form Typeform → enrich con API → Pipedrive deal → Slack notify. Misura task consumati.
2. **Lab — Code by Zapier.** Aggiungi step di logica custom (Python/JS) per calcolo lead score.
3. **Stretch — migrate Zap to n8n.** Ricostruisci lab 1 in n8n self-hosted; confronta tempo, costo, manutenibilita.

## Auto-valutazione

1. Free tier limit: quanti task/mese?
2. Path: quando usarlo, quando evitarlo?
3. Code by Zapier: linguaggi supportati.
4. Storage by Zapier: a cosa serve?
5. Lock-in: come misurare?

## Collegamenti incrociati

- Modulo 09 — `09-n8n-guida-completa-self-hosted.md`: alternativa.
- Modulo 19 — `19-cost-monitoring-piattaforme.md`: cost analysis.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Zap** | Workflow Zapier. |
| **Trigger** | Evento iniziale del Zap. |
| **Action** | Step successivo. |
| **Path** | Branching condizionale. |
| **Storage by Zapier** | Mini-DB chiave-valore integrato. |
| **Code by Zapier** | Step di logica custom (JS/Python). |
| **Task** | Unita di esecuzione (1 azione = 1 task). |
| **Sub-Zap** | Zap richiamabile da altri Zap (modularita). |
| **Looping** | Iterazione su array di elementi in un Zap. |
| **Formatter** | Step per trasformazione dati (testo, date, numeri). |
| **Filter** | Step che blocca l'esecuzione se condizioni non soddisfatte. |
| **Transfer** | Strumento per migrazione dati in bulk tra app. |
| **Tables** | Database relazionale leggero integrato in Zapier. |
| **Webhooks by Zapier** | Trigger/azione per HTTP custom (catch/send). |
| **Delay** | Step che mette in pausa l'esecuzione per N minuti/ore. |
| **Auto-Replay** | Riesecuzione automatica di task falliti. |
| **Premium App** | App che richiede piano Professional+ per essere usata. |
