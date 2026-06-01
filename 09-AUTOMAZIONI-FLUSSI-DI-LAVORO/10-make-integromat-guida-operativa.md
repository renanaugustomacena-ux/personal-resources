---
corso: "Automazioni e Flussi di Lavoro"
fase: "3 — Piattaforme"
modulo: 10
titolo: "Make (ex Integromat) — Guida Operativa Completa"
versione: "Make.com (web product)"
livello: "competent"
prerequisiti:
  - "Moduli 01-04"
  - "Concetti base API REST"
obiettivi:
  - "Progettare scenari Make multi-step con routers, iterators e aggregators"
  - "Calcolare e ottimizzare il consumo di operations per controllare i costi"
  - "Configurare error handler robusti con retry, DLQ e Data Store"
  - "Costruire Custom App per integrare API non native nella piattaforma"
  - "Implementare pattern di monitoraggio e osservabilita per scenari in produzione"
tag: [make, integromat, iPaaS, no-code, automazione, operations, scenari]
---

# Make (ex Integromat) — Guida Operativa Completa

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 3 — Piattaforme · Modulo 10
> **Prerequisiti:** Moduli 01-04.
> **Obiettivi:** scenari Make, operations counting, error handlers, routers, iterators, data store, custom apps.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** Make.com (web product, no version tag).

## Idee guida

1. **Make pricing per "operation", non per task.** 1 task complesso = N operations. Calcola con cura.
2. **Routers per branching, iterators per loop.** Pattern per workflow complessi.
3. **Data Store = mini-DB built-in.** Utile per dedup, idempotency, state machine.
4. **Error handler obbligatorio in produzione.** Senza, scenario blocca tutta la coda.
5. **Custom App = HTTP module riutilizzabile.** Per integrazioni custom non native.

---

## Indice

- [Panoramica](#panoramica)
- [Setup dell'Account e Organizzazione](#setup-dellaccount-e-organizzazione)
- [Lo Scenario Builder](#lo-scenario-builder)
- [Moduli: Tipi e Configurazione](#moduli-tipi-e-configurazione)
- [Router, Filtri e Percorsi Condizionali](#router-filtri-e-percorsi-condizionali)
- [Iterator e Aggregator](#iterator-e-aggregator)
- [Data Structures e Data Stores](#data-structures-e-data-stores)
- [Webhook: Ricezione di Eventi Esterni](#webhook-ricezione-di-eventi-esterni)
- [Connessioni API Personalizzate](#connessioni-api-personalizzate)
- [Error Handling Avanzato](#error-handling-avanzato)
- [Scheduling e Pianificazione](#scheduling-e-pianificazione)
- [Execution History e Debugging](#execution-history-e-debugging)
- [Team Collaboration e Organization Management](#team-collaboration-e-organization-management)
- [Ricette Operative Comuni](#ricette-operative-comuni)
- [Funzioni e Trasformazioni Dati](#funzioni-e-trasformazioni-dati)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Make, precedentemente noto come Integromat, è una piattaforma di integrazione e automazione visuale basata su cloud che permette di connettere applicazioni, trasferire dati e automatizzare processi aziendali senza scrivere codice. A differenza di piattaforme più semplici come Zapier, Make si distingue per la sua interfaccia a grafo che permette di costruire scenari complessi con ramificazioni, cicli, aggregazioni e gestione avanzata degli errori. Questa capacità di modellare flussi non lineari lo rende particolarmente adatto per automazioni aziendali che richiedono logica condizionale sofisticata.

Il modello di pricing di Make si basa sulle "operations" — ogni azione eseguita da un modulo (lettura, scrittura, trasformazione) conta come un'operazione. Questo rende fondamentale la progettazione efficiente degli scenari per ottimizzare il consumo di operations. Il piano gratuito offre 1.000 operations al mese, sufficiente per sperimentare e prototipare. I piani a pagamento partono da 10.000 operations mensili e includono funzionalità aggiuntive come i Data Stores, le connessioni illimitate e il supporto prioritario.

Make supporta oltre 1.800 integrazioni native (app) e fornisce moduli HTTP e JSON generici per connettersi a qualsiasi API REST. La piattaforma include anche funzionalità avanzate come la gestione di strutture dati complesse, i Data Stores (database interni), le webhooks in tempo reale e un sistema di error handling con quattro strategie distinte (break, resume, rollback, commit). In questa guida operativa esploreremo ogni aspetto della piattaforma con esempi concreti e pattern riutilizzabili.

---

## Setup dell'Account e Organizzazione

### Struttura Gerarchica

Make organizza le risorse in una gerarchia a tre livelli:

1. **Organization**: il livello più alto, corrisponde all'azienda o al team. Contiene le impostazioni di fatturazione, gli utenti e i team.
2. **Team**: un gruppo di utenti all'interno dell'organizzazione. Ogni team ha i propri scenari, connessioni e data stores. I team permettono di isolare le risorse tra dipartimenti o progetti.
3. **Scenario**: il singolo flusso di automazione, composto da moduli collegati tra loro.

### Creazione dell'Account

Dopo la registrazione su `make.com`, la prima configurazione richiede:

1. Creare l'organizzazione con il nome dell'azienda
2. Creare almeno un team (es. "Marketing Automation", "IT Operations")
3. Invitare i membri del team con i ruoli appropriati

### Ruoli e Permessi

Make definisce diversi ruoli con permessi granulari:

- **Organization Owner**: controllo totale, fatturazione, gestione utenti globale
- **Organization Admin**: gestione utenti e team, senza accesso alla fatturazione
- **Team Admin**: gestione degli scenari e delle connessioni all'interno del team
- **Team Member**: creazione e modifica degli scenari assegnati
- **Team Monitoring**: visualizzazione degli scenari e dell'execution history (sola lettura)

La separazione in team è particolarmente importante per la sicurezza: le connessioni (credenziali API) create in un team non sono visibili agli altri team, implementando il principio del minimo privilegio.

---

## Lo Scenario Builder

Lo Scenario Builder è l'interfaccia visuale di Make per costruire i flussi di automazione. A differenza delle interfacce lineari (step-by-step) di altre piattaforme, Make utilizza una rappresentazione a grafo dove i moduli sono nodi connessi da archi che rappresentano il flusso dei dati.

### Anatomia di uno Scenario

Ogni scenario è composto da:

- **Trigger Module**: il primo modulo che avvia l'esecuzione. Può essere un webhook, un polling schedule, o un evento da un'applicazione.
- **Action Modules**: moduli che eseguono operazioni (creare un record, inviare un'email, chiamare un'API).
- **Search Modules**: moduli che cercano dati in un'applicazione e restituiscono zero o più risultati.
- **Transform Modules**: moduli che trasformano i dati (parser JSON, parser CSV, aggregatori).
- **Flow Control**: router, filtri, iteratori, aggregatori che controllano il flusso dell'esecuzione.

### Creazione di uno Scenario Base

Per creare un nuovo scenario:

1. Navigare al team desiderato
2. Cliccare "Create a new scenario"
3. Aggiungere il modulo trigger (il primo cerchio con l'orologio)
4. Selezionare l'applicazione e il trigger specifico
5. Configurare la connessione (credenziali)
6. Aggiungere moduli successivi cliccando sul "+" che appare dopo ogni modulo
7. Mappare i campi utilizzando i dati provenienti dai moduli precedenti

### Il Data Flow

Ogni modulo riceve i dati dai moduli precedenti e produce un output strutturato. L'output è rappresentato come un array di "bundle" — ogni bundle è un oggetto JSON che contiene i dati elaborati. Quando un modulo produce più bundle (es. una ricerca che restituisce 10 risultati), i moduli successivi vengono eseguiti una volta per ciascun bundle, creando un effetto di "loop implicito".

Esempio di flusso dati:

```
Google Sheets (Watch Rows) → produce 5 bundle (5 nuove righe)
  ↓
Slack (Send Message) → viene eseguito 5 volte, una per riga
```

Questo comportamento è fondamentale da comprendere perché influisce direttamente sul consumo di operations e sulla logica dello scenario.

---

## Moduli: Tipi e Configurazione

### Trigger Modules

I trigger determinano quando lo scenario si attiva. Esistono due categorie principali:

**Instant Triggers (Webhooks)**: lo scenario si attiva immediatamente quando un evento si verifica. Sono i più efficienti perché non consumano operations per il polling. Esempi: Slack "Watch Events", Stripe "Watch Events", Custom Webhook.

**Polling Triggers**: lo scenario controlla periodicamente una risorsa per verificare la presenza di nuovi dati. L'intervallo di polling è configurabile (minimo ogni 1 minuto nei piani a pagamento, 15 minuti nel piano gratuito). Esempi: Google Sheets "Watch Rows", Gmail "Watch Emails", Airtable "Watch Records".

### Action Modules

Gli action modules eseguono operazioni CRUD sulle applicazioni connesse:

- **Create**: creare un nuovo record (es. "Create a Contact" in HubSpot)
- **Update**: aggiornare un record esistente
- **Delete**: eliminare un record
- **Get**: recuperare un singolo record per ID
- **List/Search**: cercare record con filtri

### Moduli Utility

Make fornisce moduli generici indipendenti dalle applicazioni:

- **HTTP**: effettuare richieste HTTP arbitrarie (GET, POST, PUT, DELETE, PATCH)
- **JSON**: parser e creatore di strutture JSON
- **CSV**: parser e creatore di file CSV
- **XML**: parser e creatore di documenti XML
- **Tools**: moduli utility come Set Variable, Get Variable, Sleep, Text Parser, Math
- **Flow Control**: Router, Iterator, Aggregator, Repeater

### Configurazione delle Connessioni

Ogni modulo che interagisce con un'applicazione esterna richiede una "Connection" — un set di credenziali salvate. Make supporta diversi metodi di autenticazione:

- **OAuth 2.0**: il metodo più comune. Make guida l'utente attraverso il flusso di autorizzazione, ottiene e gestisce automaticamente i token di accesso e refresh.
- **API Key**: inserimento diretto della chiave API
- **Basic Auth**: username e password
- **Token**: token di autenticazione personalizzato

Le connessioni sono condivise all'interno del team e possono essere riutilizzate in più scenari. Questo centralizza la gestione delle credenziali ed evita la duplicazione.

---

## Router, Filtri e Percorsi Condizionali

### Router Module

Il Router è uno dei moduli più potenti di Make. Permette di dividere il flusso di esecuzione in più percorsi paralleli, ciascuno con le proprie condizioni di attivazione. A differenza di un semplice IF/ELSE, il Router supporta un numero arbitrario di percorsi (routes) e più di un percorso può essere attivato contemporaneamente se le condizioni sono soddisfatte.

Configurazione di un Router:

```
[Trigger: Nuovo Ordine]
    ↓
[Router]
    ├── Route 1 (Filtro: importo > 1000) → [Notifica Manager] → [Approvazione]
    ├── Route 2 (Filtro: importo <= 1000) → [Processamento Automatico]
    └── Route 3 (Fallback, nessun filtro) → [Log Audit]
```

### Filtri

I filtri sono condizioni che si applicano alle connessioni tra moduli. Un modulo successivo viene eseguito solo se il filtro sulla connessione è soddisfatto. I filtri supportano:

- **Operatori di confronto**: uguale, diverso, maggiore, minore, contiene, inizia con, finisce con
- **Operatori logici**: AND, OR
- **Pattern matching**: espressioni regolari
- **Operatori su array**: contiene, non contiene
- **Operatori su date**: prima di, dopo di, nell'intervallo

Esempio di filtro complesso: "Processa solo se il campo `status` è 'active' E il campo `country` è 'IT' O 'DE'":

```
Condition 1: status = active
AND
Condition Group:
  Condition 2: country = IT
  OR
  Condition 3: country = DE
```

### Fallback Route

L'ultima route di un Router senza filtri funge da "fallback" (equivalente di un `else`). Viene attivata solo se nessuna delle route precedenti è stata attivata. Questo è utile per gestire casi imprevisti e garantire che ogni bundle venga elaborato.

---

## Iterator e Aggregator

### Iterator

L'Iterator "scompone" un array in bundle individuali. È indispensabile quando un modulo restituisce un array che deve essere elaborato elemento per elemento.

Esempio pratico: un'API restituisce un JSON con un array di prodotti:

```json
{
  "ordine_id": "ORD-001",
  "prodotti": [
    {"nome": "Widget A", "prezzo": 10.50},
    {"nome": "Widget B", "prezzo": 25.00},
    {"nome": "Widget C", "prezzo": 7.99}
  ]
}
```

L'Iterator su `prodotti` genera 3 bundle separati, uno per ogni prodotto. I moduli successivi all'Iterator vengono eseguiti 3 volte.

### Aggregator

L'Aggregator è l'operazione inversa dell'Iterator: raggruppa più bundle in un unico bundle. È fondamentale per ricomporre i dati dopo un'elaborazione per-elemento.

Tipi di Aggregator disponibili:

- **Array Aggregator**: raccoglie valori da più bundle in un array
- **Numeric Aggregator**: calcola somma, media, min, max, conteggio
- **Text Aggregator**: concatena testi con separatore
- **Table Aggregator**: genera una tabella HTML dai bundle

Esempio: calcolare il totale di un ordine dopo aver iterato sui prodotti:

```
[API: Get Ordine] → [Iterator: prodotti] → [Set Variable: calcola IVA per prodotto]
  → [Numeric Aggregator: somma dei prezzi con IVA] → [Slack: invia totale ordine]
```

### Pattern Iterator-Aggregator

Il pattern Iterator → elaborazione → Aggregator è uno dei pattern più frequenti in Make. La sequenza tipica è:

1. Ricevere un dato complesso (con array annidati)
2. Iterare sull'array
3. Elaborare ogni elemento (arricchimento, trasformazione, validazione)
4. Aggregare i risultati in un formato pronto per l'output

---

## Data Structures e Data Stores

### Data Structures

Le Data Structures in Make definiscono lo schema dei dati — sono template che descrivono la forma attesa dei dati (tipi, nomi dei campi, validazioni). Vengono utilizzate per:

- Definire lo schema di un webhook personalizzato
- Validare i dati in ingresso
- Configurare i campi dei Data Stores
- Parsare risposte API complesse

Creazione di una Data Structure:

```
Nome: Ordine
Campi:
  - ordine_id (Text, required)
  - cliente_email (Text, required, pattern: email)
  - importo (Number, required, min: 0)
  - valuta (Text, required, enum: EUR|USD|GBP)
  - righe (Collection[]):
      - prodotto_id (Text, required)
      - quantita (Integer, required, min: 1)
      - prezzo_unitario (Number, required)
```

### Data Stores

I Data Stores sono database interni di Make che permettono di persistere dati tra le esecuzioni degli scenari. Funzionano come tabelle semplici con operazioni CRUD.

Casi d'uso tipici:
- **Deduplicazione**: archiviare gli ID dei record già processati per evitare duplicati
- **Stato intermedio**: mantenere il conteggio o lo stato di un processo multi-step
- **Cache**: memorizzare dati di lookup frequenti per ridurre le chiamate API
- **Configurazione**: archiviare parametri configurabili senza modificare lo scenario

Operazioni sui Data Stores:

| Modulo | Operazione | Descrizione |
|--------|-----------|-------------|
| Add/Replace a record | Upsert | Inserisce o aggiorna un record |
| Get a record | Read | Recupera un record per chiave |
| Search records | Query | Cerca record con filtri |
| Delete a record | Delete | Elimina un record per chiave |
| Delete all records | Truncate | Svuota il Data Store |
| Count records | Count | Conta i record (con filtri opzionali) |

Limitazioni: i Data Stores hanno limiti di dimensione basati sul piano (da 1MB nel piano free a 1GB nei piani enterprise). Non supportano query complesse (JOIN, subquery) né indici personalizzati. Per esigenze più avanzate, è preferibile utilizzare un database esterno (Airtable, PostgreSQL via modulo HTTP).

---

## Webhook: Ricezione di Eventi Esterni

### Custom Webhooks

Make permette di creare webhook personalizzati che fungono da endpoint HTTP per ricevere dati da qualsiasi sorgente:

1. Aggiungere un modulo "Custom Webhook" come trigger
2. Make genera un URL unico (es. `https://hook.eu2.make.com/abc123xyz`)
3. Configurare il servizio esterno per inviare dati a questo URL
4. Al primo invio, Make campiona la struttura dei dati per il mapping

### Webhook Response

Di default, Make risponde immediatamente con HTTP 200 al servizio chiamante. Per personalizzare la risposta:

1. Aggiungere un modulo "Webhook Response" alla fine dello scenario
2. Configurare status code, headers e body personalizzati

Questo è utile quando il servizio chiamante si aspetta una risposta specifica (es. Slack richiede una risposta con il campo `challenge` durante la verifica dell'URL).

### Webhook Queue

Se uno scenario con trigger webhook riceve più richieste di quante ne possa elaborare (es. durante un burst), Make mette in coda le richieste e le elabora sequenzialmente. La coda ha un limite di 50.000 richieste in attesa.

### Sicurezza dei Webhook

Per proteggere i webhook:

- **IP Restriction**: nelle impostazioni avanzate del webhook, specificare gli IP sorgente autorizzati
- **Header Validation**: aggiungere un filtro dopo il webhook che verifica la presenza di un header segreto
- **HMAC Signature**: per servizi che firmano i payload (GitHub, Stripe, Shopify), utilizzare il modulo Crypto per verificare la firma

---

## Connessioni API Personalizzate

Quando Make non ha un'integrazione nativa per un servizio, è possibile utilizzare i moduli HTTP per connettersi a qualsiasi API REST.

### Modulo HTTP: Make a Request

Configurazione tipica per una chiamata API:

```
URL: https://api.servizio.com/v1/risorse
Method: GET
Headers:
  Authorization: Bearer {{connection.access_token}}
  Content-Type: application/json
Query String:
  page: {{variabile_pagina}}
  per_page: 50
Parse Response: Yes
```

### Gestione dell'Autenticazione per API Custom

Per API che richiedono OAuth2, Make fornisce il framework "Make an OAuth 2.0 request" che gestisce automaticamente il ciclo di vita del token:

1. Configurare l'Authorization URL, il Token URL, il Client ID e il Client Secret
2. Make guida l'utente attraverso l'autorizzazione
3. I refresh token vengono gestiti automaticamente

Per API con autenticazione più semplice (API Key, Bearer Token), è sufficiente configurare gli header nel modulo HTTP.

### Paginazione Automatica

Per API che restituiscono risultati paginati, si implementa un pattern con il modulo Repeater:

```
[Set Variable: page = 1] → [Repeater]
  → [HTTP: GET /risorse?page={{page}}]
  → [Array Aggregator: accumula risultati]
  → [Set Variable: page = page + 1]
  → [Router]
      ├── Route 1 (Filtro: risultati.length == per_page): torna al Repeater
      └── Route 2 (Filtro: risultati.length < per_page): esci dal loop
```

---

## Error Handling Avanzato

Make offre quattro strategie di error handling, ciascuna con un comportamento distinto. La gestione degli errori si configura aggiungendo una "Error Handler Route" a qualsiasi modulo.

### Le Quattro Direttive di Error Handling

#### 1. Break

La direttiva **Break** interrompe l'esecuzione dello scenario e salva lo stato nel "Incomplete Executions" store. L'esecuzione può essere ripresa manualmente o automaticamente dopo che il problema è stato risolto.

Caso d'uso: un'API esterna è temporaneamente non disponibile. L'esecuzione viene sospesa e ripresa quando l'API torna online.

```
[HTTP Request] → (Errore) → [Break]
                                 ↓
                    L'esecuzione viene salvata in
                    "Incomplete Executions" e può
                    essere ripresa successivamente
```

#### 2. Resume

La direttiva **Resume** ignora l'errore e prosegue l'esecuzione con dati sostitutivi definiti dall'utente. Il modulo che ha generato l'errore viene considerato come se avesse prodotto i dati di fallback.

Caso d'uso: se la ricerca di un contatto nel CRM fallisce, proseguire con valori di default.

```
[CRM: Search Contact] → (Errore) → [Resume: output = {"nome": "Sconosciuto", "email": ""}]
       ↓                                      ↓
  (dati normali)                    (dati di fallback)
       ↓                                      ↓
  [Modulo successivo] ←←←←←←←←←←←←←←←←←←←←←←←
```

#### 3. Rollback

La direttiva **Rollback** annulla tutte le operazioni eseguite nello scenario corrente (se supportato dai moduli, come le transazioni database) e marca l'esecuzione come fallita.

Caso d'uso: in un processo di trasferimento fondi, se il secondo step fallisce, annullare anche il primo per mantenere la consistenza.

#### 4. Commit

La direttiva **Commit** conferma tutte le operazioni eseguite fino al punto dell'errore e marca l'esecuzione come completata con successo, nonostante l'errore.

Caso d'uso: un processo di importazione dati in cui gli errori su singoli record non devono bloccare l'intero batch. Le operazioni già eseguite vengono mantenute.

### Retry Pattern

Make supporta un pattern di retry nativo: nelle impostazioni avanzate di ogni modulo HTTP, è possibile abilitare "Automatically retry" con un numero massimo di tentativi e un intervallo tra i tentativi.

### Combinare Error Handling con Router

Per scenari complessi, si combina l'error handler con un Router per gestire diversi tipi di errore:

```
[HTTP Request] → (Errore) → [Router]
    ├── Route 1 (Filtro: error.statusCode == 429) → [Sleep: 60s] → [Resume: retry]
    ├── Route 2 (Filtro: error.statusCode == 404) → [Resume: skip record]
    └── Route 3 (Fallback) → [Slack: notifica errore critico] → [Break]
```

---

## Scheduling e Pianificazione

### Modalità di Scheduling

Ogni scenario può essere configurato con diverse modalità di esecuzione:

- **At Regular Intervals**: esecuzione ogni N minuti (da 1 a 60.000 minuti)
- **Once**: esecuzione singola, utile per test
- **Every Day**: esecuzione giornaliera a un orario specifico
- **Days of the Week**: esecuzione in giorni specifici della settimana
- **Days of the Month**: esecuzione in giorni specifici del mese
- **Specified Dates**: esecuzione in date specifiche
- **Immediately (webhook)**: esecuzione istantanea su evento webhook

### Intervallo Minimo

L'intervallo minimo dipende dal piano:
- **Free**: 15 minuti
- **Core**: 5 minuti
- **Pro**: 1 minuto
- **Teams/Enterprise**: 1 minuto con priorità di esecuzione

### Timezone

Lo scheduling rispetta il timezone configurato nelle impostazioni dello scenario. È fondamentale configurare il timezone corretto (es. "Europe/Rome") per evitare che gli scenari programmati si attivino all'ora sbagliata.

### Limitazioni di Concorrenza

Un scenario non può essere eseguito in parallelo con se stesso. Se un'esecuzione è ancora in corso quando lo scheduler dovrebbe avviarne un'altra, la nuova esecuzione viene accodata. Con l'opzione "Sequential processing" attiva, le esecuzioni in coda vengono elaborate una alla volta nell'ordine di arrivo.

---

## Execution History e Debugging

### Execution History

Ogni esecuzione di uno scenario viene registrata nella Execution History, che mostra:

- **Data e ora** dell'esecuzione
- **Stato**: Success, Warning, Error
- **Durata** in secondi
- **Operations** consumate
- **Data Size** dei dati trasferiti

### Inspection Detail

Cliccando su un'esecuzione, si accede alla vista dettagliata che mostra:

- L'input e l'output di ogni singolo modulo
- I filtri che sono stati valutati (e se hanno bloccato o passato il bundle)
- Gli errori con stack trace completo
- Il tempo di esecuzione per modulo

Questa è la funzionalità più potente per il debugging: permette di tracciare esattamente il flusso dei dati attraverso lo scenario e identificare dove i dati si corrompono o dove la logica diverge dal comportamento atteso.

### Incomplete Executions

Quando un'esecuzione termina con un errore gestito dalla direttiva Break, viene salvata nella sezione "Incomplete Executions". Da qui è possibile:

- Visualizzare i dati al momento dell'errore
- Riprovare l'esecuzione
- Eliminare l'esecuzione incompleta

### Data Inspector

Durante la costruzione dello scenario, il Data Inspector (icona a bolla su ogni connessione) mostra un campione dei dati reali che fluiscono tra i moduli. Questo è essenziale per:

- Verificare che il mapping sia corretto
- Comprendere la struttura dei dati restituiti dalle API
- Identificare campi mancanti o con formati imprevisti

---

## Team Collaboration e Organization Management

### Condivisione degli Scenari

Gli scenari sono condivisi all'interno del team. Tutti i membri del team con i permessi appropriati possono visualizzare, modificare e attivare gli scenari. Non esiste un sistema di versioning nativo — le modifiche sovrascrivono lo stato precedente.

Per implementare un flusso di lavoro collaborativo sicuro:

1. Utilizzare l'export JSON degli scenari come forma di backup/versioning
2. Prima di modificare uno scenario in produzione, esportarlo come blueprint
3. Testare le modifiche con dati di test prima di attivare lo scenario modificato

### Blueprint: Import/Export

Gli scenari possono essere esportati come file JSON (blueprint) e importati in altri team o organizzazioni. Il blueprint contiene:

- La struttura dello scenario (moduli, connessioni, filtri)
- Le configurazioni dei moduli (mapping, parametri)
- Le Data Structures utilizzate

Non contiene le credenziali (connessioni), che devono essere riconfigurate nell'ambiente di destinazione.

### Organization Dashboard

Il dashboard dell'organizzazione fornisce una vista aggregata su:

- Consumo di operations per team e per scenario
- Scenari attivi e inattivi
- Errori recenti
- Utilizzo rispetto ai limiti del piano

---

## Ricette Operative Comuni

### Ricetta 1: Sincronizzazione CRM Bidirezionale

Sincronizzazione dei contatti tra HubSpot e Salesforce:

```
Scenario A: HubSpot → Salesforce
[HubSpot: Watch Contacts (new/updated)]
  → [Data Store: Check Last Sync Timestamp]
  → [Router]
      ├── Route 1 (nuovo contatto): [Salesforce: Create Contact]
      └── Route 2 (contatto aggiornato): [Salesforce: Update Contact]
  → [Data Store: Update Sync Timestamp]

Scenario B: Salesforce → HubSpot
[Salesforce: Watch Contacts (new/updated)]
  → [Data Store: Check Last Sync Timestamp]
  → [Router]
      ├── Route 1 (nuovo contatto): [HubSpot: Create Contact]
      └── Route 2 (contatto aggiornato): [HubSpot: Update Contact]
  → [Data Store: Update Sync Timestamp]
```

Il Data Store con il timestamp dell'ultima sincronizzazione previene i loop infiniti (un aggiornamento su HubSpot attiva il sync verso Salesforce, che a sua volta attiverebbe il sync di ritorno verso HubSpot).

### Ricetta 2: Processamento Fatture

Automazione del processamento fatture ricevute via email:

```
[Gmail: Watch Emails (label: "Fatture")]
  → [Iterator: allegati]
  → [Router]
      ├── Route 1 (Filtro: tipo == PDF):
      │   → [HTTP: Upload a Servizio OCR]
      │   → [JSON: Parse Risposta OCR]
      │   → [Set Variable: estrai importo, data, fornitore]
      │   → [Google Sheets: Aggiungi riga al registro fatture]
      │   → [Google Drive: Salva PDF in cartella anno/mese]
      └── Route 2 (Filtro: tipo != PDF):
          → [Slack: Notifica allegato non supportato]
  → [Gmail: Mark as Read]
  → [Gmail: Add Label "Processata"]
```

### Ricetta 3: Social Media Cross-Posting

Pubblicazione automatica su più piattaforme social:

```
[Airtable: Watch Records (tabella "Calendario Editoriale", campo status = "Pronto")]
  → [Router]
      ├── Route 1: [Twitter: Create Tweet (testo breve)]
      ├── Route 2: [LinkedIn: Create Post (testo professionale)]
      ├── Route 3: [Facebook Page: Create Post (testo + immagine)]
      └── Route 4: [Instagram: via Buffer API (immagine + caption)]
  → [Aggregator: raccoglie URL dei post pubblicati]
  → [Airtable: Update Record (status = "Pubblicato", links = URL aggregati)]
```

### Ricetta 4: Monitoring Uptime con Escalation

```
[Schedule: ogni 5 minuti]
  → [HTTP: GET https://servizio.com/healthz]
  → [Router]
      ├── Route 1 (Filtro: statusCode == 200):
      │   → [Data Store: Reset contatore errori]
      ├── Route 2 (Filtro: statusCode != 200):
      │   → [Data Store: Incrementa contatore errori]
      │   → [Data Store: Get contatore]
      │   → [Router]
      │       ├── Route 2a (contatore == 1): [Slack: Alert canale #ops]
      │       ├── Route 2b (contatore == 3): [Email: Alert team lead]
      │       └── Route 2c (contatore >= 5): [PagerDuty: Create Incident]
      └── Route 3 (Errore connessione):
          → [Stesso flusso della Route 2]
```

---

## Funzioni e Trasformazioni Dati

Make include un ricco set di funzioni per trasformare i dati direttamente nel mapping dei moduli. Le funzioni si inseriscono nei campi dei moduli con la sintassi `{{funzione(argomenti)}}`.

### Funzioni Testo

```
{{lower("TESTO")}}           → "testo"
{{upper("testo")}}           → "TESTO"
{{capitalize("mario rossi")}} → "Mario Rossi"
{{trim("  spazi  ")}}        → "spazi"
{{replace("hello world"; "world"; "make")}} → "hello make"
{{substring("abcdef"; 0; 3)}} → "abc"
{{length("testo")}}          → 5
{{split("a,b,c"; ",")}}      → ["a", "b", "c"]
{{md5("testo")}}             → hash MD5
{{sha256("testo")}}          → hash SHA256
{{encodeURL("param con spazi")}} → "param%20con%20spazi"
```

### Funzioni Data

```
{{now}}                               → data/ora corrente
{{addDays(now; 7)}}                  → tra 7 giorni
{{addHours(now; 3)}}                 → tra 3 ore
{{formatDate(now; "DD/MM/YYYY")}}    → "12/04/2026"
{{formatDate(now; "YYYY-MM-DD'T'HH:mm:ss")}} → ISO 8601
{{parseDate("12/04/2026"; "DD/MM/YYYY")}}     → oggetto data
{{dateDifference(data1; data2; "days")}}       → differenza in giorni
```

### Funzioni Matematiche

```
{{ceil(4.2)}}    → 5
{{floor(4.8)}}   → 4
{{round(4.567; 2)}} → 4.57
{{max(10; 20; 5)}}  → 20
{{min(10; 20; 5)}}  → 5
{{average(10; 20; 30)}} → 20
```

### Funzioni Array

```
{{length(array)}}          → numero di elementi
{{first(array)}}           → primo elemento
{{last(array)}}            → ultimo elemento
{{slice(array; 0; 5)}}    → primi 5 elementi
{{merge(array1; array2)}} → array concatenato
{{distinct(array)}}        → rimuove duplicati
{{sort(array; "asc")}}    → ordina ascendente
{{map(array; "campo")}}   → estrae un campo da ogni oggetto
```

### Operatore ifempty e if

```
{{ifempty(campo; "valore di default")}}
{{if(condizione; "valore se vero"; "valore se falso")}}
{{if(importo > 1000; "Alto"; if(importo > 100; "Medio"; "Basso"))}}
```

---

## Best Practices

### Progettazione degli Scenari

1. **Naming convention chiara**: utilizzare nomi descrittivi per gli scenari che includano il dominio, l'azione e la direzione del flusso (es. "[CRM] HubSpot → Salesforce Sync Contatti").
2. **Un scenario, una responsabilità**: evitare scenari monolitici. Suddividere in scenari modulari che comunicano tramite webhook interni.
3. **Note e documentazione**: utilizzare le note dello scenario per documentare la logica, le decisioni di design e le dipendenze.
4. **Organizzazione visuale**: mantenere il grafo dello scenario leggibile, con flussi da sinistra a destra e route del router organizzate verticalmente.

### Ottimizzazione delle Operations

5. **Filtri prima delle azioni**: posizionare i filtri il prima possibile per scartare i bundle che non necessitano di elaborazione, risparmiando operations.
6. **Batch operations**: quando possibile, utilizzare moduli che supportano operazioni batch (es. "Create Multiple Records") anziché iterare su singoli record.
7. **Data Store come cache**: memorizzare dati di lookup frequenti nei Data Stores anziché richiamarli da API esterne ad ogni esecuzione.
8. **Aggregare prima di inviare**: se devi inviare una notifica per più record, aggregali prima e invia un unico messaggio riepilogativo.

### Error Handling

9. **Sempre un error handler**: ogni scenario di produzione deve avere almeno un meccanismo di error handling. Configurare Break per errori recuperabili e una notifica per errori critici.
10. **Monitoring delle Incomplete Executions**: controllare regolarmente la coda delle esecuzioni incomplete e risolvere gli errori in sospeso.
11. **Timeout ragionevoli**: configurare timeout appropriati per i moduli HTTP per evitare che un'API lenta blocchi l'intero scenario.

### Sicurezza

12. **Connessioni separate per ambiente**: creare connessioni separate per test e produzione, evitando di usare credenziali di produzione durante lo sviluppo.
13. **Principio del minimo privilegio**: configurare le connessioni OAuth con i permessi minimi necessari (scope).
14. **Audit regolare**: verificare periodicamente le connessioni attive e rimuovere quelle non più utilizzate.

---

## Troubleshooting

### Problema: Scenario Non Si Attiva con Webhook

**Sintomi**: il servizio esterno invia i dati all'URL webhook di Make, ma lo scenario non si attiva. Non ci sono esecuzioni nella history.

**Causa**: lo scenario potrebbe essere disattivato, l'URL webhook potrebbe essere scaduto dopo un periodo di inattività (negli account free), oppure il payload inviato non corrisponde alla Data Structure configurata.

**Soluzione**: verificare che lo scenario sia attivo (toggle ON). Controllare che l'URL webhook sia corretto. Testare manualmente con curl: `curl -X POST https://hook.eu2.make.com/abc123 -H "Content-Type: application/json" -d '{"test": true}'`. Se il webhook è stato ricreato, aggiornare l'URL nel servizio esterno.

### Problema: Errore "Operation Limit Reached"

**Sintomi**: lo scenario si interrompe con l'errore che il limite di operations mensili è stato raggiunto.

**Causa**: consumo di operations superiore al piano. Spesso causato da scenari con polling aggressivo o da scenari che iterano su grandi dataset senza filtri.

**Soluzione**: analizzare il consumo per scenario nel dashboard. Ottimizzare gli scenari più costosi: aggiungere filtri, ridurre la frequenza di polling, utilizzare webhook instant anziché polling. Valutare l'upgrade del piano se il consumo è legittimo.

### Problema: Dati Mancanti nel Mapping

**Sintomi**: un campo che dovrebbe contenere dati appare vuoto nel modulo successivo, nonostante sia stato mappato correttamente.

**Causa**: il campo potrebbe essere opzionale nell'API sorgente e non sempre presente. Oppure la struttura dei dati è cambiata (es. aggiornamento API) e il mapping si riferisce a un percorso non più valido.

**Soluzione**: utilizzare il Data Inspector per verificare la struttura effettiva dei dati. Applicare `{{ifempty(campo; "default")}}` per gestire i campi opzionali. Rigenerare la struttura dati del modulo trigger se l'API è cambiata.

### Problema: Errore "ConnectionError" Intermittente

**Sintomi**: lo scenario fallisce sporadicamente con errori di connessione verso API esterne, ma funziona correttamente la maggior parte delle volte.

**Causa**: timeout di rete, rate limiting dell'API esterna, o instabilità temporanea del servizio.

**Soluzione**: abilitare "Auto retry" nelle impostazioni del modulo HTTP con 2-3 tentativi e un intervallo di 60 secondi. Se l'errore è dovuto a rate limiting (HTTP 429), aggiungere un modulo Sleep prima delle chiamate API per rispettare i limiti.

### Problema: Loop Infinito tra Due Scenari

**Sintomi**: due scenari si attivano reciprocamente in un ciclo infinito, consumando rapidamente le operations.

**Causa**: tipico nelle sincronizzazioni bidirezionali dove lo scenario A aggiorna un record nel servizio B, il che attiva lo scenario B che aggiorna il servizio A, che riattiva lo scenario A.

**Soluzione**: implementare un meccanismo di deduplicazione con Data Store. Prima di aggiornare, verificare se l'aggiornamento proviene dall'altro scenario (es. confrontando il timestamp dell'ultima modifica con il timestamp dell'ultima sincronizzazione). In alternativa, aggiungere un campo "sync_source" al record e filtrare gli aggiornamenti originati dall'altro scenario.

### Problema: Scenario Lento — Timeout su Moduli HTTP

**Sintomi**: lo scenario impiega troppo tempo e fallisce con "The operation timed out" o "ETIMEDOUT".

**Causa**: l'API di destinazione risponde lentamente, oppure il payload è troppo grande. Su piani Free/Core il timeout HTTP è 40 secondi; su piani Pro/Teams è più alto.

**Soluzione**: (1) Aumentare il timeout nel modulo HTTP (Advanced settings → Timeout). (2) Verificare che il payload non contenga campi binari inutili (Base64 di file grandi). (3) Se l'API target è lenta per design (es. generazione report), implementare un pattern asincrono: primo scenario invia la richiesta, secondo scenario con Schedule polling controlla lo stato fino a completamento.

### Problema: "RateLimitError" o HTTP 429 dall'API Target

**Sintomi**: moduli HTTP restituiscono errore 429 Too Many Requests dopo un certo numero di esecuzioni.

**Causa**: lo scenario invia troppe richieste all'API esterna in un intervallo breve. Frequente con Iterator su grandi array o scenario schedulato ogni minuto.

**Soluzione**: (1) Aggiungere un modulo **Sleep** (Tools → Sleep) dopo ogni chiamata API con pausa di 1-2 secondi. (2) Ridurre il prefetch/concurrency nelle impostazioni dello scenario. (3) Usare **Aggregator** per raccogliere più record e inviare una singola richiesta batch. (4) Leggere la documentazione dell'API target per conoscere i limiti e configurare il rate di conseguenza.

### Problema: Data Store "Record Limit Reached"

**Sintomi**: il modulo Data Store restituisce errore "Record limit reached" durante un'operazione di Add.

**Causa**: il Data Store ha raggiunto il limite massimo di record per il piano (Free: 500 record, Core: 2.500, Pro: 25.000).

**Soluzione**: (1) Implementare pulizia automatica: creare uno scenario schedulato che elimina record più vecchi di N giorni. (2) Verificare che non ci siano record duplicati accumulati da mancata deduplicazione. (3) Utilizzare un database esterno (Airtable, Google Sheets, Supabase) per dataset più grandi, mantenendo il Data Store solo per lookup e cache leggeri.

### Problema: Blueprint Import Fallisce

**Sintomi**: importazione di un blueprint JSON fallisce con errore "Invalid blueprint" o "Module not found".

**Causa**: il blueprint fa riferimento a moduli o connessioni non disponibili nell'account di destinazione. Possibile anche incompatibilità di versione del blueprint.

**Soluzione**: (1) Verificare che tutte le app utilizzate nel blueprint siano disponibili nel piano di destinazione. (2) Dopo l'import, riconnettere manualmente ogni connessione (le credenziali non vengono esportate per sicurezza). (3) Se un modulo non è disponibile, sostituirlo con l'equivalente generico (es. HTTP module per app non supportate).

### Problema: Webhook Restituisce "Accepted" ma Dati Non Arrivano

**Sintomi**: l'API esterna riceve HTTP 200 dalla webhook Make, ma nessun dato appare nel bundle dello scenario.

**Causa**: il Content-Type del payload non corrisponde a quello atteso (es. viene inviato `text/plain` ma Make si aspetta `application/json`), oppure il body è vuoto.

**Soluzione**: (1) Verificare gli header inviati dall'API sorgente — in particolare `Content-Type: application/json`. (2) Controllare che il body contenga JSON valido. (3) Usare `webhook.site` o `requestbin.com` come proxy per ispezionare il payload grezzo prima di inviarlo a Make.

### Problema: Iterator Produce Bundle Vuoti

**Sintomi**: l'Iterator elabora N elementi ma i moduli successivi ricevono campi vuoti.

**Causa**: la struttura dell'array passato all'Iterator non corrisponde al mapping dei moduli successivi. Spesso accade quando l'array contiene oggetti annidati e il mapping punta al livello sbagliato.

**Soluzione**: (1) Utilizzare il Data Inspector per ispezionare l'output dell'Iterator — verificare la struttura di ogni bundle. (2) Rigenerare la Data Structure del modulo trigger. (3) Utilizzare un modulo **Set Variable** dopo l'Iterator per estrarre e rinominare i campi necessari in modo esplicito.

### Problema: Scenario Funziona in Test ma Non in Produzione

**Sintomi**: cliccando "Run Once" tutto funziona, ma quando lo scenario è attivato in produzione non produce risultati o genera errori.

**Causa**: (1) Il trigger in modalità test recupera dati storici, mentre in produzione elabora solo nuovi eventi. (2) Le condizioni dei filtri escludono i dati reali. (3) I rate limit dell'API esterna bloccano le esecuzioni schedulate.

**Soluzione**: (1) Verificare la data/ora del marker "From" del trigger — se impostato nel futuro, nessun dato viene processato. (2) Controllare i filtri con dati reali, non solo con dati di test. (3) Monitorare le Incomplete Executions e l'Execution History per errori specifici.

### Problema: Campi Data/Ora con Timezone Errato

**Sintomi**: le date nei record processati risultano spostate di ore rispetto al valore atteso.

**Causa**: Make internamente usa UTC. Se il modulo sorgente invia date senza timezone o con timezone locale, la conversione può produrre risultati inattesi.

**Soluzione**: (1) Utilizzare la funzione `formatDate()` con timezone esplicito: `{{formatDate(campo; "YYYY-MM-DD HH:mm"; "Europe/Rome")}}`. (2) Impostare il timezone dello scenario nelle impostazioni (Scenario settings → Timezone). (3) Convertire esplicitamente con `setTimezone()` quando si combinano dati da sorgenti con timezone diversi.

---

## Anti-pattern Make

### 1. Scenario Monolitico ("God Scenario")

**Problema**: uno scenario con 30+ moduli che gestisce tutto — trigger, trasformazione, validazione, routing, notifica, logging — in un unico flusso.

**Conseguenza**: impossibile testare singole parti, un errore in qualsiasi punto blocca tutto, debugging è un incubo, la manutenzione richiede conoscenza dell'intero flusso.

**Soluzione**: decomporre in micro-scenari collegati tramite webhook interni. Ogni scenario ha una responsabilità specifica (validazione, enrichment, delivery, notifica).

### 2. Polling Aggressivo su Dati Rari

**Problema**: scenario schedulato ogni minuto per eventi che accadono 2-3 volte al giorno.

**Conseguenza**: spreco di operations (1.440/giorno per nulla), costo elevato, inquinamento dei log con esecuzioni "0 bundles processed".

**Soluzione**: sostituire il polling con webhook instant dove disponibile. Se il webhook non è supportato, aumentare l'intervallo di polling a 15-60 minuti e utilizzare un marker per non rielaborare record già processati.

### 3. Ignorare le Incomplete Executions

**Problema**: abilitare "Allow storing incomplete executions" senza monitorarle né riprocessarle.

**Conseguenza**: i dati non elaborati si accumulano silenziosamente. Dopo settimane si scopre che centinaia di record non sono stati processati.

**Soluzione**: (1) Creare uno scenario dedicato che verifica periodicamente la coda delle incomplete executions tramite Make API. (2) Configurare notifiche (email, Slack) quando il conteggio supera una soglia. (3) Definire un runbook per il reprocessing.

### 4. Hard-coding di Valori nei Filtri

**Problema**: valori come email, ID account, soglie numeriche inseriti direttamente nei filtri dello scenario.

**Conseguenza**: cambiare un valore richiede di modificare lo scenario, con rischio di errore e nessuna tracciabilità.

**Soluzione**: memorizzare i parametri configurabili in un Data Store dedicato (chiave-valore) e leggerli all'inizio dello scenario. Cambiare una soglia diventa un aggiornamento di un record nel Data Store, senza toccare lo scenario.

### 5. Mancata Gestione dei Campi Null/Empty

**Problema**: mappare direttamente i campi senza verificare se contengono valore, causando errori nei moduli successivi.

**Conseguenza**: errori "Cannot read property of null", record parziali nel sistema target, dati inconsistenti.

**Soluzione**: utilizzare sistematicamente `{{ifempty(campo; "default")}}` per ogni campo opzionale. Per campi critici, aggiungere un filtro che scarti i bundle dove mancano dati essenziali.

### 6. Nessun Naming Convention

**Problema**: scenari denominati "New Scenario", "Copy of New Scenario (2)", moduli senza etichetta.

**Conseguenza**: in un account con 50+ scenari, nessuno sa cosa fa cosa. Onboarding di nuovi membri del team diventa impossibile.

**Soluzione**: adottare una convenzione: `[APP_SOURCE]-[APP_TARGET]-[DESCRIZIONE]` per gli scenari (es. `HUBSPOT-SHEETS-weekly-report`). Etichettare ogni modulo con la sua funzione. Utilizzare le note per documentare la logica decisionale.

### 7. Connessione Condivisa tra Ambienti

**Problema**: usare la stessa connessione OAuth per scenari di test e produzione.

**Conseguenza**: un test può modificare dati di produzione. Revocare la connessione di test disabilita anche la produzione.

**Soluzione**: creare connessioni separate: `Salesforce-DEV`, `Salesforce-PROD`. In ogni scenario, verificare quale connessione è configurata prima di attivarlo.

### 8. Retry Infinito senza Escalation

**Problema**: configurare il retry automatico con 10+ tentativi e intervallo crescente, senza mai escalare l'errore.

**Conseguenza**: un errore non recuperabile (es. credenziali scadute, campo obbligatorio mancante) viene ritentato per ore, consumando operations inutilmente.

**Soluzione**: limitare i retry a 2-3 tentativi. Se falliscono tutti, usare l'error handler con direttiva **Break** e notifica al team. Dopo la correzione, riprocessare manualmente dall'Incomplete Executions queue.

### 9. Data Store come Database Primario

**Problema**: usare il Data Store di Make come database principale dell'applicazione, con logica CRUD complessa.

**Conseguenza**: limiti di record (500-25.000 in base al piano), nessun indice per query complesse, nessun backup automatico, vendor lock-in totale.

**Soluzione**: utilizzare il Data Store solo per cache, lookup, deduplicazione, flag temporanei. Per dati persistenti, usare un database esterno (Supabase, Airtable, PostgreSQL) e connetterlo via API.

### 10. Scenario Senza Error Handler in Produzione

**Problema**: attivare uno scenario senza nessun meccanismo di gestione errori.

**Conseguenza**: errori silenziosi, dati persi, nessuna notifica. Il team scopre il problema solo quando un utente segnala dati mancanti.

**Soluzione**: ogni scenario di produzione deve avere: (1) Error handler con Break (per errori recuperabili) + notifica. (2) Filtro per errori critici con notifica immediata. (3) Dashboard per monitorare esecuzioni fallite.

---

## Sicurezza Avanzata per Make

### Gestione dei Secret e delle Credenziali

Le connessioni Make salvano le credenziali (OAuth token, API key) in modo crittografato. Tuttavia, ci sono rischi aggiuntivi:

```
RISCHI COMUNI:
┌─────────────────────────────────────────────────────┐
│ 1. API key in chiaro nel campo URL/body del modulo  │
│ 2. Token in Custom Headers visibili nella history   │
│ 3. Password nei parametri di query string           │
│ 4. Credenziali DB nei log di debug                  │
│ 5. Webhook URL prevedibili senza autenticazione     │
└─────────────────────────────────────────────────────┘
```

**Mitigazioni**:

1. **Usare sempre Connessioni, mai inserire API key nei campi**: creare una Custom App o usare il modulo HTTP con la sezione "Credentials" anziché incollare la key nel body.
2. **IP Whitelisting**: su piani Enterprise, configurare l'IP restriction per limitare l'accesso all'account Make.
3. **Webhook con autenticazione**: aggiungere un header `Authorization: Bearer <token>` al webhook e verificarlo con un filtro nel primo modulo dello scenario.

```
Flusso sicurezza webhook:
[Webhook riceve richiesta]
        │
        v
[Router con filtro: header Authorization = token atteso?]
        │
    ┌───┴───┐
    │       │
 SI │       │ NO
    v       v
[Continua] [Risposta 401 + log tentativo non autorizzato]
```

4. **Audit delle Connessioni**: periodicamente verificare:
   - Quali connessioni sono attive e quali non più utilizzate
   - Quali scenari usano quale connessione
   - Se le connessioni hanno permessi eccessivi (scope OAuth troppo ampi)

5. **Gestione del Team Access**:
   - Admin: gestione account, billing, connessioni
   - Member: creazione e modifica scenari
   - Viewer (su piani Enterprise): solo lettura
   - Non condividere mai credenziali dell'account Make — usare sempre inviti team

### Sicurezza dei Dati in Transito e a Riposo

- Make crittografa i dati in transito (TLS 1.2+).
- I dati delle esecuzioni sono memorizzati per il periodo di retention del piano (Free: 15 giorni, Pro: 30 giorni).
- Per dati sensibili (PII, dati sanitari, finanziari), valutare se il data residency di Make (EU/US) è compatibile con i requisiti normativi.
- **Non loggare dati sensibili**: evitare di inviare PII a Slack/email per debug. Usare ID di riferimento.

### Conformita GDPR per Scenari Make

- **Data Processing Agreement (DPA)**: Make offre un DPA conforme all'Art. 28 GDPR. Firmarlo prima di elaborare dati personali di residenti EU.
- **Data retention**: configurare la retention minima necessaria per le esecuzioni.
- **Diritto alla cancellazione**: implementare scenari che possano cancellare dati personali su richiesta dell'interessato.
- **Registrazione trattamenti**: documentare quali scenari trattano quali categorie di dati personali.

---

## Monitoraggio e Osservabilita

### Dashboard di Monitoraggio Make

Make fornisce un dashboard nativo nel piano Teams/Enterprise. Per piani inferiori, costruire un monitoraggio custom:

```
ARCHITETTURA MONITORING:
┌──────────────────────────────────────────┐
│              Make Account                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Scenario 1│ │Scenario 2│ │Scenario N│ │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ │
│        │            │            │       │
│        v            v            v       │
│   ┌──────────────────────────────────┐   │
│   │  Webhook → Scenario di Logging   │   │
│   │  (raccoglie execution results)   │   │
│   └───────────────┬──────────────────┘   │
└───────────────────┼──────────────────────┘
                    │
         ┌──────────┼──────────┐
         v          v          v
   [Google Sheet] [Slack]  [Data Store]
   (storico)     (alert)   (metriche)
```

### Metriche Chiave da Monitorare

| Metrica | Soglia di Allarme | Azione |
|---|---|---|
| Operations consumate / quota | > 80% del piano | Ottimizzare o upgrade |
| Incomplete executions in coda | > 10 | Investigate e reprocess |
| Tempo medio esecuzione scenario | > 2x baseline | Profiling moduli |
| Errori per scenario / giorno | > 5% del totale esecuzioni | Root cause analysis |
| Webhook response time | > 5 secondi | Ottimizzare primo modulo |
| Data Store record count | > 80% del limite | Pulizia o migrazione |

### Alerting con Make

Creare uno scenario di alerting dedicato:

1. **Trigger**: Schedule (ogni 15 minuti) o Webhook da scenario di errore
2. **Azione**: interrogare Make API per execution history
3. **Filtro**: filtrare esecuzioni con `status: error` nelle ultime N ore
4. **Notifica**: inviare summary a Slack/email con:
   - Nome scenario fallito
   - Tipo di errore
   - Timestamp
   - Link diretto alla execution history

### Logging Strutturato

Per scenari critici, aggiungere moduli di logging espliciti:

```json
{
  "scenario_id": "12345",
  "scenario_name": "CRM-SHEETS-sync",
  "execution_id": "{{executionId}}",
  "timestamp": "{{now}}",
  "status": "success",
  "records_processed": 42,
  "operations_consumed": 87,
  "duration_ms": 12340,
  "errors": []
}
```

Inviare questi log a:
- **Google Sheets**: per analisi storica e grafici
- **Webhook esterno**: per integrazione con sistemi di monitoring centralizzati (Datadog, Grafana)
- **Data Store**: per lookup rapidi sullo stato recente

---

## Ottimizzazione Costi Make

### Comprendere il Modello di Costo

Make addebita per **operations**, non per scenario o esecuzione:

```
1 modulo eseguito = 1 operation
(anche se il modulo non fa nulla di utile)

Esempio - scenario con 5 moduli:
  Trigger (1 op) → Filter → Azione (1 op) → Azione (1 op) → Slack (1 op)
  = 4 operations per esecuzione
  (i filtri NON consumano operations)

Esempio - scenario con Iterator su 100 record:
  Trigger (1 op) → Iterator → Azione (100 op) → Aggregator (1 op)
  = 102 operations per esecuzione
```

### Strategie di Riduzione Operations

| Strategia | Risparmio Tipico | Implementazione |
|---|---|---|
| Filtri aggressivi prima di azioni | 30-60% | Aggiungere filtro dopo trigger |
| Batch operations | 50-80% | Usare "Create Multiple" dove disponibile |
| Webhook anziché polling | 40-70% | Convertire trigger polling → instant |
| Data Store come cache | 20-40% | Cachare lookup frequenti |
| Aggregare notifiche | 60-90% | Un messaggio riepilogativo anziché N |
| Ridurre frequenza schedule | Variabile | Da 1 min a 15 min dove accettabile |

### Calcolo TCO Mensile

```
TCO = Costo piano Make
    + Costo ore manutenzione (N ore × tariffa oraria)
    + Costo API esterne (se a consumo)
    + Costo storage esterno (Airtable, DB, ecc.)
    + Costo opportunita downtime

Esempio pratico:
  Piano Pro: €16/mese (10.000 ops)
  Media operations/mese: 8.500
  Manutenzione: 2 ore/mese × €50/h = €100
  API esterne: €20/mese (SendGrid, Twilio)
  ────────────────────────────────
  TCO: €136/mese
  Risparmio vs processo manuale: 40h/mese × €25/h = €1.000
  ROI: (1.000 - 136) / 136 = 635%
```

### Upgrade vs Ottimizzazione: Albero Decisionale

```
Operations > 80% del piano?
  │
  ├─ SI → Ci sono scenari ottimizzabili?
  │         │
  │         ├─ SI → Ottimizza prima (filtri, batch, cache)
  │         │        → Rivaluta dopo 2 settimane
  │         │
  │         └─ NO → Tutte le operations sono necessarie?
  │                   │
  │                   ├─ SI → Upgrade piano
  │                   │
  │                   └─ NO → Disattiva scenari obsoleti
  │
  └─ NO → Non fare nulla, monitorare
```

---

## Pattern Avanzati Make

### Pattern: Saga con Compensazione

Per operazioni distribuite che coinvolgono più servizi (es. CRM + fatturazione + magazzino):

```
SCENARIO PRINCIPALE (forward path):
[Trigger] → [CRM: crea deal] → [Fattura: crea bozza] → [Magazzino: prenota stock]
                 │                      │                       │
                 v                      v                       v
          (salva deal_id          (salva invoice_id       (salva stock_id
           in Data Store)         in Data Store)          in Data Store)

SE ERRORE IN QUALSIASI PUNTO:
[Error Handler Break] → [Webhook → Scenario Compensazione]

SCENARIO COMPENSAZIONE (rollback path):
[Webhook riceve IDs dal Data Store]
        │
        v
[Magazzino: rilascia stock se stock_id presente]
        │
        v
[Fattura: annulla bozza se invoice_id presente]
        │
        v
[CRM: segna deal come "failed" se deal_id presente]
        │
        v
[Notifica team + log]
```

### Pattern: Fan-out / Fan-in con Aggregazione

Per elaborare dati in parallelo e aggregare i risultati:

```
[Trigger: lista ordini] → [Iterator: per ogni ordine]
                                    │
                          ┌─────────┼─────────┐
                          v         v         v
                     [Enrichment] [Pricing] [Inventory]
                     (API CRM)   (API price) (API stock)
                          │         │         │
                          └─────────┼─────────┘
                                    v
                          [Aggregator: combina risultati]
                                    │
                                    v
                          [Azione finale: aggiorna ordine completo]
```

**Attenzione**: Make non supporta vero parallelismo nei moduli; i branch del Router vengono eseguiti sequenzialmente. Per parallelismo reale, usare webhook verso scenari separati.

### Pattern: Checkpoint / Resume per Long-running Jobs

Per elaborare dataset di migliaia di record senza superare il timeout dello scenario:

```
Scenario "PROCESSOR":
1. Leggi Data Store "checkpoint" → ultimo ID processato
2. Query API: "SELECT * WHERE id > last_id ORDER BY id LIMIT 100"
3. Iterator sui 100 record
4. Processa ogni record
5. Aggiorna checkpoint nel Data Store con ultimo ID processato
6. Se ci sono ancora record → Webhook verso se stesso (ricorsione)

Scenario "MONITOR":
- Schedule ogni 30 min
- Verifica che il checkpoint avanzi
- Se bloccato > 2 ore → alert
```

### Pattern: Circuit Breaker con Data Store

Proteggere le API esterne da troppe richieste quando sono instabili:

```
Prima di ogni chiamata API:
1. Leggi Data Store "circuit_breaker_{service_name}"
2. Se state = "OPEN" e timestamp_open < 5 minuti fa → SKIP (non chiamare)
3. Se state = "CLOSED" → chiama API
4. Se API fallisce:
   a. Incrementa failure_count nel Data Store
   b. Se failure_count >= 3 → imposta state = "OPEN", salva timestamp
5. Se API ha successo → reset failure_count a 0, state = "CLOSED"
```

---

## Ricette di Integrazione Avanzate

### Ricetta: Sincronizzazione Bidirezionale CRM ↔ ERP

**Obiettivo**: mantenere sincronizzati contatti e aziende tra HubSpot (CRM) e Odoo (ERP).

```
Scenario A: HubSpot → Odoo
[Webhook HubSpot: contact.updated]
  → [Filter: source ≠ "odoo"] (anti-loop)
  → [Data Store: leggi mapping hubspot_id → odoo_id]
  → [Router]
      ├─ Rotta 1: odoo_id esiste → [HTTP: PUT Odoo update partner]
      └─ Rotta 2: odoo_id non esiste → [HTTP: POST Odoo create partner]
                                        → [Data Store: salva mapping]
  → [Data Store: aggiorna sync_timestamp]

Scenario B: Odoo → HubSpot
[Webhook Odoo: partner.write]
  → [Filter: source ≠ "hubspot"] (anti-loop)
  → [Data Store: leggi mapping odoo_id → hubspot_id]
  → [Router]
      ├─ Rotta 1: hubspot_id esiste → [HTTP: PATCH HubSpot update]
      └─ Rotta 2: hubspot_id non esiste → [HTTP: POST HubSpot create]
                                           → [Data Store: salva mapping]
  → [Data Store: aggiorna sync_timestamp]
```

**Anti-loop**: il campo `source` nel payload indica chi ha originato la modifica. Ogni scenario scrive `source = <proprio nome>` quando aggiorna, e filtra le modifiche originate dall'altro scenario.

### Ricetta: Pipeline Lead Scoring Automatico

**Obiettivo**: assegnare un punteggio automatico ai lead in ingresso basato su dati enrichment.

```
[Webhook: nuovo lead da form]
  → [HTTP: Clearbit enrichment API con email]
  → [Set Variables: calcolo score]
      score += company_size > 100 ? 20 : 5
      score += role.contains("Director|VP|C-") ? 30 : 10
      score += industry in target_industries ? 25 : 0
      score += country == "IT" ? 10 : 5
  → [Router per fascia score]
      ├─ Score ≥ 80: "Hot" → CRM deal + Slack #sales-hot
      ├─ Score 40-79: "Warm" → CRM lead + email nurture sequence
      └─ Score < 40: "Cold" → CRM lead only + tag "nurture"
```

### Ricetta: Monitoraggio Uptime Multi-sito con Escalation

**Obiettivo**: monitorare N siti web e applicare escalation progressiva.

```
[Schedule: ogni 5 minuti]
  → [Data Store: leggi lista siti da monitorare]
  → [Iterator: per ogni sito]
      → [HTTP: GET {url} con timeout 10s]
      → [Router]
          ├─ HTTP 200 + response time < 3s:
          │   → [Data Store: reset failure_count a 0]
          │
          ├─ HTTP 200 + response time ≥ 3s:
          │   → [Data Store: incrementa slow_count]
          │   → Se slow_count ≥ 3: [Slack warning #ops]
          │
          └─ HTTP error o timeout:
              → [Data Store: incrementa failure_count]
              → [Router escalation]
                  ├─ failure_count == 1: [Slack #ops]
                  ├─ failure_count == 3: [Email team lead]
                  ├─ failure_count == 5: [SMS PagerDuty]
                  └─ failure_count ≥ 10: [Incident ticket via API]
```

### Ricetta: ETL Incrementale con Deduplicazione

**Obiettivo**: estrarre dati da API paginata, trasformare, caricare in database, deduplicando.

```
[Schedule: ogni ora]
  → [Data Store: leggi last_sync_timestamp]
  → [HTTP: GET /api/records?updated_after={last_sync}]
  → [Router: risposta ha dati?]
      ├─ SI:
      │   → [Iterator: per ogni record]
      │       → [Data Store: cerca record per external_id]
      │       → [Router]
      │           ├─ Esiste: [HTTP: PUT /db/records/{id}] (update)
      │           └─ Non esiste: [HTTP: POST /db/records] (insert)
      │   → [Data Store: aggiorna last_sync_timestamp]
      │   → [HTTP: GET next page] (se paginato)
      │
      └─ NO: [Fine — nessun nuovo dato]
```

### Ricetta: Gestione Fatture Elettroniche Italia (FatturaPA)

**Obiettivo**: automatizzare il ciclo passivo delle fatture elettroniche ricevute via SDI.

```
[Webhook: ricezione XML FatturaPA da intermediario SDI]
  → [Parse XML: estrai dati fattura]
      cedente, cessionario, importi, IVA, data
  → [Data Store: verifica P.IVA cedente contro whitelist fornitori]
  → [Router]
      ├─ Fornitore noto:
      │   → [HTTP: POST gestionale/fatture-passive] (registrazione automatica)
      │   → [Google Sheets: aggiungi riga scadenziario]
      │   → [Slack: notifica #contabilita]
      │
      └─ Fornitore sconosciuto:
          → [Email: notifica responsabile acquisti]
          → [Data Store: salva fattura in coda approvazione]
```

---

## FAQ — Domande Frequenti Make

### 1. Qual e la differenza tra Operations e Executions?

Un'**execution** è una singola attivazione dello scenario (dal trigger alla fine). Le **operations** sono i singoli moduli eseguiti durante quell'execution. Un'execution con 5 moduli consuma 5 operations. I filtri e i router NON consumano operations. Il piano limita le operations mensili, non le executions.

### 2. Posso usare Make per elaborare file grandi (> 100 MB)?

Make ha un limite di 100 MB per file in transito. Per file più grandi: (1) pre-elaborare il file esternamente (split in chunk), (2) usare moduli che supportano streaming (es. Google Drive con upload chunked), (3) processare il file su un server esterno e usare Make solo per orchestrare il flusso. File binari grandi consumano molta memoria nel bundle.

### 3. Come posso migrare scenari tra account Make?

Utilizzare il sistema di **blueprint** (JSON export/import): (1) Aprire lo scenario → kebab menu → Export Blueprint. (2) Nel nuovo account → Import Blueprint. (3) Riconnettere tutte le connessioni (le credenziali non vengono trasferite). (4) Riconfigurare Data Store (vanno ricreati nel nuovo account). (5) Aggiornare gli URL webhook nei servizi sorgente.

### 4. Make garantisce l'ordine di esecuzione dei moduli?

Si, i moduli nello stesso percorso sono eseguiti in ordine sequenziale, da sinistra a destra. Con il Router, le rotte vengono eseguite una alla volta dall'alto verso il basso (non in parallelo). Con l'Iterator, i bundle vengono processati uno alla volta. Non esiste parallelismo nativo all'interno di uno scenario.

### 5. Cosa succede quando il piano operazioni viene esaurito a meta mese?

Gli scenari schedulati si fermano. I webhook continuano a ricevere richieste ma lo scenario non si attiva — i dati vanno nella coda delle Incomplete Executions (se abilitata). Opzioni: (1) acquistare operations aggiuntive, (2) upgrade del piano, (3) attendere il rinnovo mensile. Per evitare sorprese, configurare alerting al raggiungimento dell'80% del budget.

### 6. Come gestisco i webhook quando Make ha un'interruzione di servizio?

Se Make è down, i webhook ricevuti vengono persi (non c'è coda lato Make). Mitigazioni: (1) configurare il servizio sorgente per ritentare l'invio del webhook (retry con backoff). (2) Usare un servizio intermediario (es. AWS SQS, Hookdeck) come buffer tra il sorgente e Make. (3) Implementare un meccanismo di reconciliazione periodica per rilevare dati mancanti.

### 7. Posso usare Make con API che richiedono OAuth2 con PKCE?

Il modulo HTTP di Make supporta OAuth2 Authorization Code flow standard. PKCE (Proof Key for Code Exchange) non è supportato nativamente. Workaround: (1) creare una Custom App che implementi il flusso PKCE. (2) Usare un servizio proxy (es. un serverless function) che gestisca il token exchange PKCE e esponga un endpoint con Bearer token semplice verso Make.

### 8. Come posso testare uno scenario senza consumare operations?

Non è possibile eseguire scenari senza consumare operations — ogni "Run Once" consuma operations reali. Strategie: (1) usare un account di test/dev separato. (2) Testare con filtri che limitano l'elaborazione a 1-2 record. (3) Utilizzare il "dry run" pattern: un flag nel primo modulo che, se attivo, salta le azioni distruttive (write, delete, send) e logga solo i dati che sarebbero stati processati.

### 9. E possibile versionare gli scenari Make?

Make non offre version control nativo. Best practice: (1) esportare il blueprint prima di ogni modifica significativa. (2) Salvare i blueprint in un repository Git con commit message descrittivo. (3) Per rollback, importare il blueprint della versione desiderata. (4) Utilizzare la naming convention con versione: `CRM-sync-v2.3`.

### 10. Come gestisco scenari che devono elaborare dati storici (backfill)?

(1) Creare uno scenario separato per il backfill con trigger manuale (Webhook o Schedule → una volta). (2) Utilizzare il pattern Checkpoint/Resume (vedi Pattern Avanzati) per elaborare grandi volumi senza timeout. (3) Non usare lo scenario di produzione per il backfill — rischio di conflitti, rate limiting, e consumo operations elevato.

### 11. Make e adatto per elaborazioni real-time (< 1 secondo)?

No. La latenza minima di Make (webhook receive → primo modulo → risposta) è 1-3 secondi. Per requisiti sub-secondo, usare: servizi serverless (AWS Lambda, Cloudflare Workers), WebSocket, o sistemi event-driven dedicati (Kafka, RabbitMQ). Make è adatto per "near real-time" (secondi-minuti).

### 12. Come gestisco la paginazione nelle API con Make?

(1) Per paginazione offset-based: usare un loop con variabile `page` incrementale, modulo HTTP con `offset={{(page-1)*limit}}`, e condizione di uscita quando i risultati sono vuoti. (2) Per cursor-based: salvare il `next_cursor` dell'ultima risposta e usarlo nella richiesta successiva. (3) Utilizzare il modulo "HTTP → Make a request" con pagination automatica nelle Advanced settings (disponibile per paginazione link-based con header `Link`).

### 13. Qual e il limite di concurrency degli scenari Make?

Ogni scenario ha un numero massimo di esecuzioni simultanee (configurabile). Default: 1 (esecuzione sequenziale). Si può aumentare fino a 10 su piani Pro/Teams. Se arrivano più trigger di quanti lo scenario possa gestire simultaneamente, le esecuzioni in eccesso vengono accodate.

### 14. Come posso integrare Make con strumenti on-premise?

Make è cloud-native e non può accedere direttamente a reti private. Opzioni: (1) esporre l'applicazione on-premise via reverse proxy con autenticazione. (2) Usare un tunnel sicuro (Cloudflare Tunnel, ngrok con autenticazione). (3) Creare un bridge: un agent locale che riceve webhook da Make e li inoltra al servizio on-premise.

### 15. E possibile schedulare uno scenario per eseguirsi in giorni specifici (es. solo lun-ven)?

Si. Opzioni: (1) Usare il trigger Schedule con intervallo giornaliero, e aggiungere un filtro nel primo modulo: `{{formatDate(now; "E")}}` in range `["Mon","Tue","Wed","Thu","Fri"]`. (2) Usare la funzionalita di scheduling avanzata (disponibile su piani Pro+) che permette di specificare giorni e orari. (3) Per esigenze complesse (primo lunedi del mese, ecc.), usare un cron esterno che attiva lo scenario via webhook.

### 16. Come gestisco scenari che devono comunicare tra loro?

Tre pattern principali: (1) **Webhook interno**: lo scenario A chiama un Webhook del scenario B alla fine. Semplice e affidabile. (2) **Data Store condiviso**: entrambi gli scenari leggono/scrivono sullo stesso Data Store. Utile per condividere stato. (3) **Coda con Data Store**: lo scenario A scrive record in un Data Store "coda", lo scenario B (schedulato) li legge e li elabora. Simula una message queue.

### 17. Make supporta workflow condizionali complessi (if/else annidati)?

Si, tramite Router annidati. Ogni Router puo avere N rotte con filtro, e all'interno di ogni rotta si puo inserire un altro Router per creare logica if/else annidata. Attenzione: oltre 3 livelli di annidamento lo scenario diventa illeggibile. Per logica molto complessa, preferire un modulo Code (JavaScript/Python in Custom App) che centralizza la decisione e produce un output semplice da routare.

### 18. Qual e la differenza tra Make Free, Core, Pro e Teams?

| Caratteristica | Free | Core | Pro | Teams |
|---|---|---|---|---|
| Operations/mese | 1.000 | 10.000 | 10.000 | 10.000 |
| Scenari attivi | 2 | illimitati | illimitati | illimitati |
| Intervallo minimo | 15 min | 5 min | 1 min | 1 min |
| Data Store record | 500 | 2.500 | 25.000 | 25.000 |
| Execution log retention | 5 gg | 15 gg | 30 gg | 30 gg |
| Custom App | No | No | Si | Si |
| Team roles | No | No | No | Si |

Le operations aggiuntive si possono acquistare su tutti i piani a pagamento.

### 19. Come faccio debug di uno scenario complesso in produzione?

(1) **Execution History**: cliccare su una specifica esecuzione per vedere input/output di ogni modulo. (2) **Data Inspector**: in fase di editing, cliccare sulla bolla tra due moduli per vedere il bundle effettivo. (3) **Modulo Set Variable**: inserire moduli Set Variable temporanei per catturare valori intermedi nel log. (4) **Scenario di debug**: clonare lo scenario, aggiungere moduli di logging (Google Sheets, webhook verso logging service), e testare con gli stessi dati.

### 20. E possibile usare Make come backend per un'applicazione?

Tecnicamente si (tramite Webhook + Webhook Response), ma non è raccomandato per: (1) latenza alta (1-5 secondi per risposta). (2) Limiti di concurrency (esecuzioni simultanee limitate dal piano). (3) Nessun caching nativo. (4) Costo per operation. Make è ottimo come "glue" tra servizi, non come API backend. Per backend, usare servizi dedicati (Supabase, Railway, Cloudflare Workers) e connetterli a Make per orchestrazione.

---

## Riferimenti

- **Documentazione ufficiale Make**: https://www.make.com/en/help
- **Make Academy**: https://academy.make.com/
- **Make Community**: https://community.make.com/
- **Make API Reference**: https://www.make.com/en/api-documentation
- **Make Templates Gallery**: https://www.make.com/en/templates
- **Make Blog (best practices)**: https://www.make.com/en/blog
- **Make Status Page**: https://status.make.com/
- **Integromat Migration Guide**: https://www.make.com/en/help/migrating-from-integromat
- **Make Pricing Calculator**: https://www.make.com/en/pricing
- **OWASP API Security Top 10**: https://owasp.org/www-project-api-security/

---

## Letture e Riferimenti

### Documentazione ufficiale

- Make — Scenario Settings and Scheduling: https://www.make.com/en/help/scenarios/scenario-settings (consultato: 2026-05-24)
- Make — Error Handling: https://www.make.com/en/help/errors/error-handling (consultato: 2026-05-24)
- Make — Data Store Module Reference: https://www.make.com/en/help/tools/data-store (consultato: 2026-05-24)
- Make — Custom Apps Development Guide: https://www.make.com/en/help/apps/custom-apps (consultato: 2026-05-24)
- Make — Webhooks Module: https://www.make.com/en/help/tools/webhooks (consultato: 2026-05-24)
- Make — Execution History and Incomplete Executions: https://www.make.com/en/help/scenarios/incomplete-executions (consultato: 2026-05-24)

### Libri

- **"Automate the Boring Stuff with Python"** — Al Sweigart (No Starch Press, 2a ed.). Introduce il pensiero di automazione; utile per capire quando passare da no-code a code.
- **"Enterprise Integration Patterns"** — Gregor Hohpe, Bobby Woolf (Addison-Wesley). Pattern di integrazione (router, aggregator, splitter) direttamente applicabili ai moduli Make.

---

## Esercizi

1. **Lab — scenario Make di test.** Form submit → enrich con API esterno → CRM sync → Slack notify. Operation count e cost analysis.
2. **Lab — error handler.** Aggiungi error handler con email alert + DLQ Data Store al lab 1.
3. **Stretch — custom app.** Costruisci un Make App custom per integrare API non native (es. webhook custom).

## Auto-valutazione

1. Operation vs task: differenza.
2. Router vs Iterator.
3. Data Store: a cosa serve?
4. Error handler: come configurarlo?
5. Custom App vs HTTP module.

## Collegamenti incrociati

- Modulo 09 — `09-n8n-guida-completa-self-hosted.md`: alternativa self-hosted.
- Modulo 14 — `14-zapier-guida-operativa.md`: confronto.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Make / Integromat** | iPaaS visual drag-drop, ex Integromat. |
| **Scenario** | Termine Make per workflow. |
| **Operation** | Unita atomica di esecuzione (1 modulo eseguito). |
| **Router** | Branching condizionale. |
| **Iterator** | Loop su array. |
| **Data Store** | Mini-DB integrato. |
| **Error Handler** | Modulo per gestire errori. |
| **Custom App** | Modulo riutilizzabile creato dall'utente. |
| **Blueprint** | Export JSON di uno scenario (configurazione portabile). |
| **Webhook** | URL che riceve richieste HTTP per attivare scenari. |
| **Aggregator** | Modulo che combina piu bundle in uno solo. |
| **Incomplete Execution** | Esecuzione fallita salvata per reprocessing. |
| **Connection** | Credenziali salvate per accedere a un servizio esterno. |
