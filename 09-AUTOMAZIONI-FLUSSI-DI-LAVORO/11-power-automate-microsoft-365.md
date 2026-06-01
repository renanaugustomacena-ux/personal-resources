---
corso: "Automazioni e Flussi di Lavoro"
fase: "3 — Piattaforme"
modulo: 11
titolo: "Power Automate e Microsoft 365 — Guida Approfondita"
versione: "Power Automate (M365 cloud product)"
livello: "competent"
prerequisiti:
  - "Moduli 01-04"
  - "Ecosistema M365 (Teams, SharePoint, Outlook, Excel)"
obiettivi:
  - "Distinguere Cloud flow e Desktop flow e scegliere il tipo corretto per ogni caso d'uso"
  - "Configurare connector standard e premium con gestione licenze appropriata"
  - "Implementare DLP policies per proteggere dati sensibili nei flow"
  - "Integrare Office Scripts con Power Automate per automazioni Excel avanzate"
  - "Gestire ambienti (dev/test/prod) con solution packaging e ALM"
tag: [power-automate, microsoft-365, rpa, cloud-flow, desktop-flow, dlp, office-scripts]
---

# Power Automate e Microsoft 365 — Guida Approfondita

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 3 — Piattaforme · Modulo 11
> **Prerequisiti:** Moduli 01-04; ecosistema M365 (Teams, SharePoint, Outlook, Excel).
> **Obiettivi:** Cloud flow vs Desktop flow; connector standard vs premium; DLP policies; Office Scripts integration.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** Power Automate (M365 cloud product).

## Idee guida

1. **Cloud flow per integrazioni server-to-server, Desktop flow per RPA.** Non confondere.
2. **Premium connector = subscription extra.** Many third-party connector (Salesforce, ServiceNow) sono premium.
3. **DLP (Data Loss Prevention) policy in tenant: governance enterprise.** Block exfiltration.
4. **Power Automate eccelle in M365, fallisce in cloud-native.** Outside M365, n8n/Make win.

---

## Indice

- [Panoramica](#panoramica)
- [Architettura della Piattaforma](#architettura-della-piattaforma)
- [Cloud Flows: Automated, Instant e Scheduled](#cloud-flows-automated-instant-e-scheduled)
- [Desktop Flows: RPA con Power Automate Desktop](#desktop-flows-rpa-con-power-automate-desktop)
- [Business Process Flows](#business-process-flows)
- [Connettori: Standard, Premium e Custom](#connettori-standard-premium-e-custom)
- [Espressioni e Funzioni](#espressioni-e-funzioni)
- [Dynamic Content e Riferimenti ai Dati](#dynamic-content-e-riferimenti-ai-dati)
- [Approval Flows](#approval-flows)
- [Adaptive Cards](#adaptive-cards)
- [Integrazione con SharePoint](#integrazione-con-sharepoint)
- [Automazione Microsoft Teams](#automazione-microsoft-teams)
- [Automazione Excel](#automazione-excel)
- [Error Handling e Retry](#error-handling-e-retry)
- [AI Builder Actions](#ai-builder-actions)
- [Environment Management](#environment-management)
- [Data Loss Prevention (DLP) Policies](#data-loss-prevention-dlp-policies)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Microsoft Power Automate (precedentemente Microsoft Flow) è la piattaforma di automazione dei processi integrata nell'ecosistema Microsoft 365 e nella Power Platform. Rappresenta la soluzione di automazione nativa per le organizzazioni che utilizzano la suite Microsoft, offrendo un'integrazione profonda con SharePoint, Teams, Outlook, Excel, Dynamics 365 e centinaia di altri servizi sia Microsoft che di terze parti. La piattaforma combina tre paradigmi di automazione — cloud flows per l'integrazione di servizi, desktop flows per l'automazione RPA dell'interfaccia utente, e business process flows per la gestione dei processi aziendali strutturati — in un'unica soluzione gestibile centralmente.

Il modello di licensing di Power Automate si articola su diversi piani: il piano "per user" (incluso in molte licenze Microsoft 365) fornisce accesso ai connettori standard e a un numero limitato di esecuzioni; il piano "per user with attended RPA" aggiunge i desktop flows; il piano "per flow" è dedicato a flussi aziendali critici con esecuzioni illimitate. Questa struttura rende Power Automate accessibile per scenari semplici (approvazioni email, notifiche) ma richiede un'attenta pianificazione dei costi per automazioni enterprise su larga scala.

In questa guida esploreremo in dettaglio ogni componente della piattaforma, dalle funzionalità base alle configurazioni avanzate per scenari enterprise. L'obiettivo è fornire una comprensione operativa completa che permetta di progettare, implementare e gestire automazioni robuste all'interno dell'ecosistema Microsoft 365.

---

## Architettura della Piattaforma

### Componenti Fondamentali

Power Automate si basa sull'infrastruttura Azure e condivide il data layer con il resto della Power Platform:

- **Common Data Service (Dataverse)**: il database relazionale cloud che sottende l'intera Power Platform. I flow possono leggere e scrivere dati in Dataverse, che funge anche da repository per le definizioni dei flow stessi.
- **Azure Logic Apps**: il motore di esecuzione sottostante. Power Automate cloud flows sono tecnicamente Azure Logic Apps con un'interfaccia semplificata e licenze integrate in Microsoft 365.
- **Connectors Framework**: il sistema di connettori che astrae le API dei servizi esterni, fornendo trigger e azioni predefinite.
- **On-Premises Data Gateway**: un componente installabile on-premises che permette ai cloud flows di accedere a risorse interne (database SQL Server, file share, SAP) senza esporre queste risorse direttamente a Internet.

### Ambienti (Environments)

La Power Platform organizza le risorse in "Environments" — contenitori logici che isolano flow, connessioni, connettori custom e dati Dataverse. Ogni tenant Microsoft 365 ha un environment di default, ma è consigliabile creare ambienti separati per sviluppo, test e produzione.

### Flusso di Esecuzione

Quando un trigger si attiva, Power Automate crea un'istanza di esecuzione (run) che attraversa le azioni definite nel flow. Ogni azione viene eseguita nel cloud Azure, con le credenziali dell'utente che ha creato il flow (o del service principal configurato). I dati transitano tra le azioni come oggetti JSON, accessibili tramite il sistema di "dynamic content".

---

## Cloud Flows: Automated, Instant e Scheduled

### Automated Flows

Gli automated flows si attivano automaticamente in risposta a un evento (trigger). Sono il tipo più comune e coprono la maggior parte degli scenari di automazione:

```
Trigger: "When an email arrives (V3)" [Outlook]
  → Condition: Subject contains "Fattura"
    → Yes:
        → Get attachment
        → Create file in SharePoint (cartella Fatture)
        → Send approval request
        → Condition: Approval response == "Approve"
            → Yes: Update Excel table
            → No: Send email to sender (rejected)
    → No:
        → (nessuna azione)
```

Trigger comuni per automated flows:
- **Outlook**: quando arriva un'email, quando un evento viene creato
- **SharePoint**: quando un elemento viene creato/modificato, quando un file viene creato
- **Teams**: quando un messaggio viene postato in un canale
- **Forms**: quando una risposta viene inviata
- **Dataverse**: quando una riga viene aggiunta/modificata/eliminata

### Instant Flows (Button Flows)

Gli instant flows vengono attivati manualmente dall'utente tramite un pulsante nell'app mobile Power Automate, da un'app Power Apps, o da un'interfaccia personalizzata. Sono ideali per azioni on-demand:

```
Trigger: "Manually trigger a flow"
  Input: Tipologia richiesta (dropdown), Descrizione (text), Urgenza (boolean)
  → Create item in SharePoint list "Richieste IT"
  → Send adaptive card to Teams channel "IT Support"
  → Send confirmation email to user
```

Gli instant flows possono accettare input dall'utente al momento dell'attivazione, inclusi testo, numeri, date, file, email e selezioni da dropdown.

### Scheduled Flows

Gli scheduled flows si attivano su un programma temporale definito:

```
Trigger: "Recurrence" - ogni giorno alle 08:00, timezone Europe/Rome
  → Get items from SharePoint list "Progetti" (filtro: deadline < today + 7 days)
  → Apply to each:
      → Send email reminder to project owner
  → Get items from SharePoint list "Progetti" (filtro: deadline < today)
      → Update item: status = "Scaduto"
      → Post message to Teams channel "Project Management"
```

Opzioni di ricorrenza:
- **Frequency**: Second, Minute, Hour, Day, Week, Month
- **Interval**: ogni N unità di frequency
- **At these hours**: ore specifiche del giorno
- **At these minutes**: minuti specifici dell'ora
- **On these days**: giorni specifici della settimana (per frequenza settimanale)
- **Timezone**: timezone per l'esecuzione

---

## Desktop Flows: RPA con Power Automate Desktop

Power Automate Desktop (PAD) è il componente RPA (Robotic Process Automation) della piattaforma. Permette di automatizzare applicazioni desktop legacy che non espongono API, registrando e riproducendo interazioni con l'interfaccia utente.

### Installazione e Configurazione

PAD è disponibile gratuitamente per Windows 10/11. Per l'integrazione con cloud flows è necessaria una licenza Power Automate premium.

```
1. Scaricare Power Automate Desktop da https://go.microsoft.com/fwlink/?linkid=2102613
2. Installare con le opzioni di default
3. Accedere con l'account Microsoft 365
4. Configurare il machine runtime service per esecuzioni unattended
```

### Modalità di Esecuzione

- **Attended**: il flow viene eseguito mentre l'utente è connesso al desktop. L'utente può vedere le azioni in esecuzione e intervenire.
- **Unattended**: il flow viene eseguito automaticamente senza interazione umana, tipicamente su una macchina virtuale dedicata. Richiede una licenza "per user with attended RPA" o superiore.

### Componenti del Desktop Flow

PAD utilizza un linguaggio visuale chiamato "Robin" con azioni specifiche per l'automazione desktop:

**Azioni UI**:
```
Launch new Internet Explorer (URL: https://legacy-app.company.com/login)
Populate text field (Element: #username, Text: %username%)
Populate text field (Element: #password, Text: %password%)
Press button (Element: #login-btn)
Wait for page to contain (Text: "Dashboard")
Extract data from web page (Table: #data-table → %results%)
Close web browser
```

**Azioni File System**:
```
Get files in folder (Folder: C:\Reports, Filter: *.xlsx → %files%)
For each %file% in %files%:
    Launch Excel (File: %file%)
    Read from Excel worksheet (Range: A1:F100 → %data%)
    Close Excel
    Write to CSV file (Path: C:\Output\%file.name%.csv, Data: %data%)
```

**Azioni per Applicazioni Legacy**:
```
Run application (Path: C:\Program Files\ERP\erp.exe)
Wait for window (Title: "ERP Login", Timeout: 30)
Send keys to window (Text: %username%{Tab}%password%{Enter})
Wait for window (Title: "Main Menu")
Click UI element (Element: MenuBar > File > Export)
Wait for window (Title: "Export Dialog")
Set text in window (Element: PathField, Text: C:\Export\report.csv)
Click button (Element: ExportButton)
Wait for file (Path: C:\Export\report.csv, Timeout: 120)
```

### Integrazione Cloud + Desktop

La potenza reale di PAD emerge quando i desktop flows vengono orchestrati dai cloud flows:

```
Cloud Flow:
  Trigger: Recurrence (ogni giorno alle 06:00)
  → Run a flow built with Power Automate Desktop
      Desktop Flow: "ERP Data Export"
      Run Mode: Unattended
      Machine: VM-RPA-01
  → Condition: Desktop flow succeeded?
      → Yes: Process exported CSV with cloud actions
      → No: Send alert email to IT
```

---

## Business Process Flows

I Business Process Flows (BPF) sono un tipo speciale di flow che guida gli utenti attraverso un processo aziendale strutturato a fasi. A differenza dei cloud flows (che sono automatici) e dei desktop flows (che automatizzano le UI), i BPF definiscono il percorso che un record (in Dataverse) deve seguire dall'inizio alla fine.

### Struttura di un BPF

Un BPF è composto da fasi (stages), e ogni fase contiene passi (steps):

```
Processo: Gestione Lead
  Stage 1: Qualificazione
    - Step: Raccolta informazioni contatto (obbligatorio)
    - Step: Identificazione budget (opzionale)
    - Step: Timeline decisionale (obbligatorio)
    → Condizione per avanzare: tutti i campi obbligatori compilati

  Stage 2: Proposta
    - Step: Creazione offerta commerciale
    - Step: Approvazione interna
    - Step: Invio al cliente
    → Condizione: offerta approvata

  Stage 3: Negoziazione
    - Step: Tracciamento delle obiezioni
    - Step: Revisione condizioni
    → Condizione: accordo raggiunto

  Stage 4: Chiusura
    - Step: Firma contratto
    - Step: Setup onboarding
    → Processo completato
```

### Branching

I BPF supportano il branching condizionale: in base ai valori dei campi del record, il processo può seguire percorsi diversi. Ad esempio, in base alla dimensione del deal, il processo di approvazione potrebbe richiedere uno o più livelli di autorizzazione.

---

## Connettori: Standard, Premium e Custom

### Connettori Standard

Inclusi in tutte le licenze Microsoft 365 e Power Automate. Coprono i servizi Microsoft principali e molti servizi di terze parti popolari:

- **Microsoft**: Outlook, SharePoint, OneDrive, Teams, Excel, Forms, Planner, To-Do
- **Social**: Twitter, Facebook, LinkedIn
- **Produttività**: RSS, Office 365 Users, Notifications
- **Dati**: SQL Server (tramite gateway), Azure SQL, SharePoint Lists

### Connettori Premium

Richiedono una licenza Power Automate premium (per user o per flow):

- **Microsoft Premium**: Dataverse, AI Builder, HTTP with Azure AD
- **Enterprise**: SAP, Salesforce, ServiceNow, Oracle Database
- **Automazione**: Power Automate Desktop (desktop flows)
- **Generico**: HTTP (richieste HTTP custom), Custom Connector

### Custom Connectors

I Custom Connectors permettono di creare connettori personalizzati per API non coperte dai connettori nativi. Si basano su una definizione OpenAPI (Swagger):

```json
{
  "swagger": "2.0",
  "info": {
    "title": "API Gestionale Interno",
    "version": "1.0"
  },
  "host": "api.gestionale.company.com",
  "basePath": "/v1",
  "schemes": ["https"],
  "securityDefinitions": {
    "api_key": {
      "type": "apiKey",
      "in": "header",
      "name": "X-API-Key"
    }
  },
  "paths": {
    "/clienti": {
      "get": {
        "operationId": "GetClienti",
        "summary": "Lista clienti",
        "parameters": [
          {
            "name": "status",
            "in": "query",
            "type": "string",
            "enum": ["active", "inactive"]
          }
        ],
        "responses": {
          "200": {
            "description": "Success",
            "schema": {
              "type": "array",
              "items": {
                "$ref": "#/definitions/Cliente"
              }
            }
          }
        }
      }
    }
  },
  "definitions": {
    "Cliente": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "nome": {"type": "string"},
        "email": {"type": "string"},
        "status": {"type": "string"}
      }
    }
  }
}
```

Il Custom Connector può essere creato dall'interfaccia di Power Automate importando il file OpenAPI, o costruendolo passo-passo nell'editor visuale.

---

## Espressioni e Funzioni

Power Automate utilizza il Workflow Definition Language (WDL) per le espressioni, che vengono inserite nei campi delle azioni con la sintassi `@{espressione}` o direttamente nell'Expression editor.

### Funzioni Stringa

```
concat('Hello', ' ', 'World')              → "Hello World"
toLower('TESTO')                            → "testo"
toUpper('testo')                            → "TESTO"
trim('  spazi  ')                           → "spazi"
replace('hello world', 'world', 'Power')    → "hello Power"
substring('abcdef', 0, 3)                   → "abc"
length('testo')                             → 5
split('a;b;c', ';')                         → ["a", "b", "c"]
indexOf('hello world', 'world')             → 6
startsWith('hello', 'hel')                  → true
endsWith('hello.pdf', '.pdf')               → true
contains('hello world', 'world')            → true
```

### Funzioni Data/Ora

```
utcNow()                                    → "2026-04-12T10:30:00.0000000Z"
utcNow('yyyy-MM-dd')                        → "2026-04-12"
convertFromUtc(utcNow(), 'Romance Standard Time', 'dd/MM/yyyy HH:mm')
                                             → "12/04/2026 12:30"
addDays(utcNow(), 7)                        → fra 7 giorni
addHours(utcNow(), 3)                       → fra 3 ore
addMinutes(utcNow(), 30)                    → fra 30 minuti
dayOfWeek(utcNow())                         → 0 (domenica) a 6 (sabato)
formatDateTime(utcNow(), 'dddd, dd MMMM yyyy')
                                             → "Sunday, 12 April 2026"
ticks(utcNow())                             → ticks (per confronti precisi)
```

### Funzioni Collection

```
first(collection)                            → primo elemento
last(collection)                             → ultimo elemento
length(collection)                           → numero di elementi
contains(collection, 'valore')               → true/false
empty(collection)                            → true se vuota
union(collection1, collection2)              → unione
intersection(collection1, collection2)       → intersezione
skip(collection, 3)                          → salta i primi 3 elementi
take(collection, 5)                          → prende i primi 5 elementi
```

### Funzioni Logiche e Condizionali

```
if(equals(status, 'active'), 'Attivo', 'Inattivo')
and(greater(importo, 100), less(importo, 1000))
or(equals(tipo, 'A'), equals(tipo, 'B'))
not(empty(campo))
coalesce(campo1, campo2, 'default')          → primo valore non null
```

### Funzioni JSON

```
json('{"key": "value"}')                     → oggetto JSON
string(oggetto)                              → stringa JSON
xpath(xml, '//element')                      → estrai da XML
```

---

## Dynamic Content e Riferimenti ai Dati

### Il Sistema Dynamic Content

Ogni azione in un flow produce un output JSON. Le azioni successive possono riferirsi a questi output tramite il pannello "Dynamic content", che mostra i campi disponibili da tutti i moduli precedenti.

Sotto il cofano, i riferimenti ai dati usano le funzioni `triggerOutputs()`, `body()`, e `outputs()`:

```
// Riferimento al body del trigger
@{triggerBody()?['subject']}

// Riferimento all'output di un'azione specifica
@{body('Get_item')?['Title']}

// Riferimento a un campo nested
@{outputs('HTTP_Request')?['body']?['data']?['results'][0]?['name']}

// Riferimento al codice di stato HTTP
@{outputs('HTTP_Request')?['statusCode']}

// Riferimento agli headers
@{outputs('HTTP_Request')?['headers']?['Content-Type']}
```

L'operatore `?` (safe navigation) è fondamentale: se un campo nel percorso è null, l'intera espressione restituisce null anziché generare un errore. Senza il `?`, un campo null causerebbe un errore di runtime.

### Variables

Power Automate supporta variabili tipizzate che possono essere inizializzate e aggiornate durante l'esecuzione:

```
Initialize variable:
  Name: contatore
  Type: Integer
  Value: 0

Initialize variable:
  Name: risultati
  Type: Array
  Value: []

// Dentro un loop:
Increment variable: contatore (by 1)
Append to array variable: risultati (value: current_item)
Set variable: ultimo_aggiornamento (value: utcNow())
```

Tipi supportati: Boolean, Integer, Float, String, Object, Array.

---

## Approval Flows

Le approvazioni sono una funzionalità nativa di Power Automate profondamente integrata con Teams e Outlook.

### Tipi di Approvazione

1. **Approve/Reject - First to respond**: la prima persona che risponde determina l'esito
2. **Approve/Reject - Everyone must approve**: tutte le persone assegnate devono approvare
3. **Custom Responses**: risposte personalizzate (es. "Approva", "Approva con modifiche", "Rifiuta", "Escalate")

### Flow di Approvazione Tipico

```
Trigger: When a new item is created in SharePoint list "Richieste Acquisto"

→ Condition: Importo > 5000?
    → Yes: Start and wait for an approval
        Type: Everyone must approve
        Title: "Approvazione acquisto: @{triggerBody()?['Title']}"
        Assigned To: manager@company.com; cfo@company.com
        Details: "Importo: €@{triggerBody()?['Importo']}\n
                  Richiedente: @{triggerBody()?['Author']?['DisplayName']}\n
                  Descrizione: @{triggerBody()?['Descrizione']}"
        Item Link: @{triggerBody()?['{Link}']}

    → No: Start and wait for an approval
        Type: First to respond
        Assigned To: manager@company.com
        (stessi dettagli)

→ Condition: Outcome equals 'Approve'?
    → Yes:
        → Update item in SharePoint (Status = "Approvato")
        → Send email to requester (approvazione confermata)
        → Create item in SharePoint list "Ordini"
    → No:
        → Update item in SharePoint (Status = "Rifiutato")
        → Send email to requester (con motivo del rifiuto: @{body('Start_approval')?['responses'][0]?['comments']})
```

### Approvazioni in Teams

Le approvazioni inviate tramite Power Automate appaiono automaticamente nell'app "Approvals" di Microsoft Teams e come notifica nell'activity feed. L'approvatore può rispondere direttamente da Teams senza aprire email o altre applicazioni.

---

## Adaptive Cards

Le Adaptive Cards sono il formato di presentazione dei dati in Teams e Outlook utilizzato da Power Automate per inviare messaggi interattivi e ricchi.

### Struttura di una Adaptive Card

```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "TextBlock",
      "text": "Nuova Richiesta di Supporto",
      "size": "Large",
      "weight": "Bolder"
    },
    {
      "type": "FactSet",
      "facts": [
        {"title": "Richiedente:", "value": "@{triggerBody()?['Author']}"},
        {"title": "Priorita:", "value": "@{triggerBody()?['Priority']}"},
        {"title": "Categoria:", "value": "@{triggerBody()?['Category']}"}
      ]
    },
    {
      "type": "TextBlock",
      "text": "@{triggerBody()?['Description']}",
      "wrap": true
    },
    {
      "type": "Input.ChoiceSet",
      "id": "assignee",
      "label": "Assegna a:",
      "choices": [
        {"title": "Team Sviluppo", "value": "dev"},
        {"title": "Team Infrastruttura", "value": "infra"},
        {"title": "Team Supporto", "value": "support"}
      ]
    },
    {
      "type": "Input.Text",
      "id": "notes",
      "label": "Note:",
      "isMultiline": true,
      "placeholder": "Aggiungi note opzionali..."
    }
  ],
  "actions": [
    {
      "type": "Action.Submit",
      "title": "Assegna Ticket",
      "data": {"action": "assign"}
    },
    {
      "type": "Action.Submit",
      "title": "Richiedi Info",
      "data": {"action": "request_info"}
    }
  ]
}
```

### Utilizzo nei Flow

L'azione "Post adaptive card and wait for a response" in Teams invia la card e sospende l'esecuzione del flow fino a quando un utente interagisce con i pulsanti. Le risposte dell'utente (inclusi i valori degli input) sono disponibili come dynamic content per le azioni successive.

---

## Integrazione con SharePoint

SharePoint è una delle integrazioni più utilizzate con Power Automate, grazie alla profonda integrazione nativa.

### Trigger SharePoint

| Trigger | Descrizione |
|---------|-------------|
| When an item is created | Nuovo elemento in una lista |
| When an item is created or modified | Elemento creato o modificato |
| When a file is created | Nuovo file in una document library |
| When a file is created or modified | File creato o modificato |
| For a selected item | Azione manuale su un elemento specifico |

### Pattern Comuni

**Document Approval Workflow**:
```
Trigger: When a file is created in "Documenti/Bozze"
→ Start approval (assegnata al manager della cartella)
→ If approved:
    → Copy file to "Documenti/Approvati"
    → Update file properties (Status = Approvato, Data Approvazione)
    → Delete original from "Bozze"
→ If rejected:
    → Update file properties (Status = Rifiutato)
    → Send email with rejection reason
```

**Metadata Auto-Population**:
```
Trigger: When a file is created in Document Library
→ Get file content
→ AI Builder: Extract information from document
→ Update file properties with extracted metadata
    (Data fattura, Fornitore, Importo, Numero fattura)
```

---

## Automazione Microsoft Teams

### Azioni Teams Disponibili

Power Automate offre numerose azioni per Teams:

- **Post message in a chat or channel**: inviare messaggi con formattazione HTML
- **Post adaptive card**: inviare card interattive
- **Create a channel**: creare canali programmaticamente
- **Get team members**: recuperare l'elenco dei membri
- **Create a Teams meeting**: schedulare meeting
- **Update message**: aggiornare messaggi esistenti

### Pattern: Onboarding Nuovo Dipendente

```
Trigger: When a new item is created in SharePoint "Nuovi Dipendenti"
→ Create a team: "Onboarding - @{triggerBody()?['Nome']}"
→ Add members: HR manager, IT support, direct manager
→ Create channels: "Documenti", "Formazione", "Domande"
→ Post welcome message with adaptive card (checklist onboarding)
→ Create Planner plan with onboarding tasks
→ Schedule Teams meeting: "Welcome meeting"
→ Send email to new employee with Teams link
```

---

## Automazione Excel

Power Automate può interagire con file Excel archiviati in OneDrive o SharePoint, a condizione che i dati siano formattati come tabella Excel (Table).

### Prerequisito: Formattazione come Tabella

I dati nel file Excel **devono** essere formattati come tabella (Insert → Table) con intestazioni di colonna univoche. Power Automate non può interagire con celle arbitrarie nei cloud flows — opera esclusivamente su righe di tabelle strutturate.

### Azioni Excel

```
List rows present in a table       → recupera tutte le righe
Get a row                          → recupera una riga per chiave
Add a row into a table             → aggiunge una riga
Update a row                       → aggiorna una riga esistente
Delete a row                       → elimina una riga
Run script                         → esegue un Office Script personalizzato
```

### Office Scripts per Operazioni Avanzate

Per operazioni che vanno oltre le azioni standard (formattazione, formule, grafici), Power Automate può eseguire Office Scripts — script TypeScript che manipolano il file Excel:

```typescript
function main(workbook: ExcelScript.Workbook, inputData: string): string {
  const sheet = workbook.getActiveWorksheet();
  const table = sheet.getTable("VenditeTable");

  // Aggiungere formule di riepilogo
  const lastRow = table.getRowCount() + 1;
  const totalCell = sheet.getRange(`E${lastRow + 2}`);
  totalCell.setFormula(`=SUM(E2:E${lastRow})`);
  totalCell.getFormat().getFont().setBold(true);

  // Creare un grafico
  const chartData = sheet.getRange(`A1:E${lastRow}`);
  const chart = sheet.addChart(ExcelScript.ChartType.columnClustered, chartData);
  chart.setName("Vendite Mensili");

  return `Report generato con ${lastRow - 1} righe`;
}
```

---

## Error Handling e Retry

### Configure Run After

Power Automate permette di configurare quando un'azione deve essere eseguita in relazione al risultato dell'azione precedente. Le opzioni "Run After" sono:

- **is successful**: esegui solo se l'azione precedente ha successo (default)
- **has failed**: esegui solo se l'azione precedente è fallita
- **is skipped**: esegui se l'azione precedente è stata saltata
- **has timed out**: esegui se l'azione precedente è scaduta

Questo permette di costruire percorsi di error handling:

```
[HTTP Request]
    ↓ (is successful)
    [Process Response]

    ↓ (has failed)
    [Compose: Error Details]
        Value: @{actions('HTTP_Request')?['error']?['message']}
    → [Send error notification email]
    → [Terminate: Failed]
```

### Scope per Try-Catch

Il pattern Try-Catch in Power Automate si implementa con le azioni Scope:

```
Scope: "Try"
    → Azione 1
    → Azione 2
    → Azione 3

Scope: "Catch" (Run After: "Try" has failed)
    → Compose: result('Try')  // dettagli di tutte le azioni nel try
    → Filter array: seleziona solo le azioni fallite
    → Send error notification

Scope: "Finally" (Run After: "Catch" is successful OR has failed OR is skipped)
    → Cleanup actions
    → Update status
```

### Retry Policy

Ogni azione HTTP e molti connettori supportano una retry policy configurabile:

- **Default**: 4 retry con intervallo esponenziale (7s, 14s, 28s, 56s)
- **Fixed Interval**: N retry con intervallo fisso
- **Exponential Interval**: N retry con backoff esponenziale personalizzabile
- **None**: nessun retry

Configurazione nella definizione JSON del flow:

```json
{
  "retryPolicy": {
    "type": "exponential",
    "count": 5,
    "interval": "PT10S",
    "minimumInterval": "PT5S",
    "maximumInterval": "PT1H"
  }
}
```

---

## AI Builder Actions

AI Builder è il componente di intelligenza artificiale della Power Platform, accessibile direttamente dai flow di Power Automate.

### Modelli Precostruiti

- **Text Recognition (OCR)**: estrae testo da immagini e documenti scansionati
- **Document Processing**: estrae informazioni strutturate da fatture, ricevute, documenti di identità
- **Sentiment Analysis**: analizza il sentimento di un testo (positivo, negativo, neutro)
- **Key Phrase Extraction**: identifica le frasi chiave in un testo
- **Language Detection**: rileva la lingua di un testo
- **Entity Extraction**: identifica entità (persone, organizzazioni, luoghi, date) nel testo
- **Category Classification**: classifica il testo in categorie predefinite o personalizzate

### Esempio: Processamento Automatico Fatture

```
Trigger: When a file is created in SharePoint "Fatture In Arrivo"
→ AI Builder: Process and save information from invoices
    Document: file content from trigger
→ Compose: Extracted Data
    Vendor: @{body('Process_invoice')?['responsev2']?['predictionOutput']?['result']?['fields']?['VendorName']?['value']}
    Amount: @{body('Process_invoice')?['responsev2']?['predictionOutput']?['result']?['fields']?['InvoiceTotal']?['value']}
    Date: @{body('Process_invoice')?['responsev2']?['predictionOutput']?['result']?['fields']?['InvoiceDate']?['value']}
→ Add row to Excel table "Registro Fatture"
→ If amount > 10000: Start approval flow
```

---

## Environment Management

### Struttura degli Ambienti

Per un deployment enterprise strutturato:

| Ambiente | Scopo | Connessioni | DLP |
|----------|-------|-------------|-----|
| Development | Sviluppo e prototipazione | Sandbox/test | Permissivo |
| Test/UAT | Test di accettazione utente | Test con dati realistici | Come produzione |
| Production | Esecuzione operativa | Produzione | Restrittivo |

### Solution Framework

I flow possono essere impacchettati in "Solutions" — contenitori che raggruppano flow, connettori custom, variabili di ambiente e altre risorse. Le solutions possono essere esportate e importate tra ambienti, implementando un ciclo di vita DevOps:

```
Development Environment
  → Export solution (managed)
  → Import to Test Environment
  → Validate and test
  → Import to Production Environment
```

Le "Environment Variables" permettono di parametrizzare i flow per ogni ambiente (es. URL diverse per API di test e produzione) senza modificare la logica del flow.

---

## Data Loss Prevention (DLP) Policies

Le DLP policies controllano quali connettori possono essere utilizzati insieme nello stesso flow, prevenendo la fuga di dati verso servizi non autorizzati.

### Gruppi di Connettori

Le DLP policies classificano i connettori in tre gruppi:

1. **Business**: connettori autorizzati per dati aziendali (es. SharePoint, Outlook, SQL Server)
2. **Non-Business**: connettori per uso personale o generico (es. Twitter, RSS, Gmail)
3. **Blocked**: connettori completamente bloccati (non utilizzabili in nessun flow)

### Regola Fondamentale

I connettori del gruppo "Business" possono interagire solo con altri connettori "Business" nello stesso flow. Un flow che utilizza un connettore "Business" e uno "Non-Business" viene bloccato dalla DLP policy.

Esempio: se SharePoint è nel gruppo "Business" e Dropbox nel gruppo "Non-Business", un flow che copia file da SharePoint a Dropbox viene bloccato.

### Configurazione

Le DLP policies vengono configurate nel Power Platform Admin Center a livello di environment o di tenant:

```
Policy: "Protezione Dati Aziendali"
Scope: All environments (o specifici)

Business Data Group:
  - SharePoint
  - Outlook
  - OneDrive
  - Teams
  - SQL Server
  - Dataverse

Non-Business Data Group:
  - Twitter
  - RSS
  - Gmail
  - Dropbox

Blocked:
  - Custom connectors (tranne quelli approvati)
  - HTTP (per prevenire chiamate a endpoint arbitrari)
```

---

## Best Practices

### Architettura dei Flow

1. **Scope per organizzare**: utilizzare le azioni Scope per raggruppare logicamente le azioni correlate, migliorando la leggibilità e abilitando il pattern try-catch.
2. **Variabili di ambiente**: parametrizzare URL, email, e altre configurazioni con Environment Variables per facilitare il deployment tra ambienti.
3. **Naming convention**: adottare un prefisso consistente per i flow (es. `[HR] Onboarding - Notifica Manager`).
4. **Commenti**: aggiungere note descrittive alle azioni complesse e ai percorsi condizionali.

### Performance

5. **Concurrency control**: configurare il grado di parallelismo dei loop "Apply to each" (default 20, massimo 50) per bilanciare velocità e rate limiting.
6. **Pagination**: per le azioni che restituiscono molti record (Get Items di SharePoint), configurare il threshold di paginazione nelle impostazioni dell'azione.
7. **Select before Apply to each**: usare l'azione Select per ridurre i dati ai soli campi necessari prima di iterare, riducendo il consumo di memoria.

### Sicurezza

8. **Secure inputs/outputs**: abilitare "Secure Inputs" e "Secure Outputs" sulle azioni che gestiscono dati sensibili (password, token) per nasconderli dalla run history.
9. **Service principal**: per flow critici in produzione, utilizzare connessioni basate su service principal anziché account personali.
10. **DLP enforcement**: implementare DLP policies restrittive in produzione per prevenire la fuga di dati.

### Governance e Ciclo di Vita

11. **Documentazione dei flow**: mantenere un registro centralizzato (es. in SharePoint) di tutti i flow di produzione con: owner, descrizione, dipendenze, connessioni utilizzate, frequenza di esecuzione e impatto business in caso di fallimento.
12. **Review periodica**: schedulare una revisione trimestrale di tutti i flow attivi per identificare flow orfani (il cui owner ha lasciato l'organizzazione), flow con alti tassi di errore, e flow che consumano risorse eccessive.
13. **Naming convention rigorosa**: adottare un formato strutturato che includa il dipartimento, il tipo di flow e una descrizione breve, ad esempio `[Finance] Automated - Invoice Processing from Email`. Questo facilita la ricerca e l'organizzazione, specialmente in ambienti con centinaia di flow.
14. **Backup degli scenari critici**: esportare regolarmente i flow come pacchetti ZIP tramite la funzionalità "Export Package" e archiviarli in un repository Git o in una document library SharePoint con versioning attivo.
15. **Monitoring proattivo**: configurare un flow dedicato al monitoring che verifica lo stato di salute degli altri flow critici interrogando la Power Automate Management API, inviando alert quando un flow risulta disabilitato o ha accumulato un numero anomalo di fallimenti nelle ultime 24 ore.

---

## Troubleshooting

### Problema: Flow Non Si Attiva

**Sintomi**: il flow è attivo ma non si attiva nonostante gli eventi trigger si verifichino.

**Causa**: il trigger potrebbe avere un intervallo di polling lungo, le condizioni del trigger potrebbero filtrare gli eventi, o la connessione potrebbe essere scaduta.

**Soluzione**: verificare la frequenza di polling del trigger nelle impostazioni. Controllare le condizioni del trigger (es. il filtro OData su SharePoint "Get items"). Verificare lo stato della connessione in "Connections" — riautenticare se necessario. Controllare che il flow non sia stato disabilitato dal sistema per troppi fallimenti consecutivi.

### Problema: Errore "Action Failed - BadRequest"

**Sintomi**: un'azione fallisce con statusCode 400 e un messaggio di errore generico.

**Causa**: i dati inviati all'azione non corrispondono al formato atteso. Comune con date in formato errato, campi numerici con valori stringa, o campi obbligatori mancanti.

**Soluzione**: esaminare la run history per vedere l'input esatto inviato all'azione. Verificare il formato dei dati con Compose actions di debug. Per le date, usare esplicitamente `formatDateTime()` per garantire il formato corretto.

### Problema: Loop "Apply to Each" Molto Lento

**Sintomi**: un loop su una collezione di molti elementi impiega ore per completarsi.

**Causa**: il grado di parallelismo è impostato a 1 (sequenziale) oppure ogni iterazione effettua chiamate API lente.

**Soluzione**: aumentare il grado di concurrency nelle impostazioni dell'azione "Apply to each" (fino a 50). Se possibile, utilizzare operazioni batch anziché iterare singolarmente. Valutare se è possibile ridurre il numero di elementi con un filtro prima del loop.

### Problema: Connessione OAuth Scaduta

**Sintomi**: il flow fallisce con errore "Unauthorized" o "Token expired" dopo un periodo di funzionamento corretto.

**Causa**: il refresh token OAuth è scaduto (tipicamente dopo 90 giorni di inattività) o le credenziali dell'utente sono cambiate.

**Soluzione**: riautenticare la connessione nelle impostazioni del flow. Per prevenire, utilizzare service principal con credenziali gestite (client credentials flow) anziché delegated user credentials per i flow di produzione.

---

## Riferimenti

- **Documentazione ufficiale Power Automate**: https://learn.microsoft.com/en-us/power-automate/
- **Power Automate Community**: https://powerusers.microsoft.com/t5/Power-Automate-Community/ct-p/MPACommunity
- **Adaptive Cards Designer**: https://adaptivecards.io/designer/
- **Power Platform Admin Center**: https://admin.powerplatform.microsoft.com/
- **Power Automate Desktop Documentation**: https://learn.microsoft.com/en-us/power-automate/desktop-flows/
- **AI Builder Documentation**: https://learn.microsoft.com/en-us/ai-builder/
- **Workflow Definition Language Reference**: https://learn.microsoft.com/en-us/azure/logic-apps/workflow-definition-language-functions-reference
- **Power Platform DLP Policies**: https://learn.microsoft.com/en-us/power-platform/admin/wp-data-loss-prevention
- **Office Scripts Reference**: https://learn.microsoft.com/en-us/office/dev/scripts/
- **Connectors Reference**: https://learn.microsoft.com/en-us/connectors/connector-reference/

---

## Letture e Riferimenti

### Documentazione ufficiale

- Power Automate — Trigger Types and Patterns: https://learn.microsoft.com/en-us/power-automate/triggers-introduction (consultato: 2026-05-24)
- Power Automate — Error Handling and Retry Policies: https://learn.microsoft.com/en-us/power-automate/error-handling (consultato: 2026-05-24)
- Power Automate — Solution-Aware Flows (ALM): https://learn.microsoft.com/en-us/power-automate/overview-solution-flows (consultato: 2026-05-24)
- Power Automate — Expressions Reference: https://learn.microsoft.com/en-us/power-automate/use-expressions-in-conditions (consultato: 2026-05-24)
- Power Automate — Governance and Environment Strategy: https://learn.microsoft.com/en-us/power-platform/guidance/adoption/environment-strategy (consultato: 2026-05-24)
- Microsoft Graph API — Overview: https://learn.microsoft.com/en-us/graph/overview (consultato: 2026-05-24)

### Libri

- **"Microsoft Power Automate Cookbook"** — Elaiza Benitez (Packt). Ricette pratiche per Cloud flow, Desktop flow e integrazione con l'ecosistema M365.
- **"RPA and Hyperautomation"** — Pascal Bornet (Independently Published). Contestualizza Power Automate Desktop nel panorama dell'automazione enterprise.

---

## Esercizi

1. **Lab — flow Outlook + SharePoint.** Email arrivata → estrai allegato → carica su SharePoint → tagga con metadata → notifica Teams.
2. **Lab — DLP policy.** Configura DLP che blocca dati sensibili (PII) da andare verso Twitter/Facebook.
3. **Stretch — Office Script + Power Automate.** Excel macro complessa eseguita via flow.

## Auto-valutazione

1. Cloud flow vs Desktop flow.
2. Premium connector: cosa sono?
3. DLP policy: cosa fa?
4. Office Scripts vs VBA macro.

## Collegamenti incrociati

- Modulo 03 — `../03-WINDOWS-POWERUSER/` (M365 admin).
- Modulo 14 — `14-zapier-guida-operativa.md`: alternativa cross-platform.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Cloud flow** | Workflow Power Automate eseguito in cloud. |
| **Desktop flow** | RPA Power Automate Desktop. |
| **Standard connector** | Connector incluso in licenza M365. |
| **Premium connector** | Connector con licenza extra. |
| **DLP** | Data Loss Prevention policy. |
| **Office Scripts** | TypeScript-based scripting per Excel. |
