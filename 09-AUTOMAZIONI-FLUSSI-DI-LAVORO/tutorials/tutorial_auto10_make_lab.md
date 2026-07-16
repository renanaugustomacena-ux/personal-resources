# Tutorial Lab — Make (ex Integromat): Scenari, Moduli ed Error Handling

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `10-make-integromat-guida-operativa.md`
> **Livello:** beginner → intermediate
> **Tempo stimato:** 2 ore
> **Prerequisiti:** Account Make (piano gratuito sufficiente), concetti HTTP/webhook
> **Versioni di riferimento:** Make (ex Integromat) — versione corrente cloud

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Costruire scenari Make multi-step con routing condizionale
2. Usare moduli HTTP/Webhook per integrazioni custom
3. Configurare Error Handler e retry per resilienza
4. Usare Data Store (storage interno di Make) come mini-database
5. Schedulare scenari e configurare webhook in entrata
6. Analizzare le operazioni consumate e ottimizzare i costi

---

## Lab Environment Setup

```
PREREQUISITI:
1. Account Make gratuito: https://www.make.com/register
   (Piano Free: 1000 operazioni/mese, max 2 scenari attivi)
2. Webhook tester: https://webhook.site (gratis, nessun account)
3. JSON generator: https://jsonplaceholder.typicode.com (API di test pubblica)

NOTA: Make è una piattaforma SaaS cloud — questo lab usa l'interfaccia web.
      Le istruzioni sono descrittive (non eseguibili localmente).
```

---

## Analogia Introduttiva

> **Make è come un cuoco con una brigata di sous-chef specializzati**:
> ogni modulo è uno chef specializzato (HTTP, email, Google Sheets, Slack).
> Lo scenario è la ricetta che descrive chi fa cosa e in quale ordine.
>
> Il **routing** (Router module) è il maitre che smista i clienti:
> "i clienti VIP al tavolo 1 (percorso premium),
> gli altri al tavolo 2 (percorso standard)".
>
> Il **Data Store** è il quaderno degli ordini della cucina:
> persistente tra una ricetta e l'altra, ma solo per dati semplici.
> Per dati complessi → integra un vero DB via HTTP.

---

## Architettura di uno Scenario Make

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCENARIO MAKE (visual)                            │
│                                                                       │
│  [Trigger] ──────► [Modulo 1] ──────► [Modulo 2] ──────► [Modulo 3]│
│                         │                                             │
│                    [Router] ──► [Percorso A: condizione vera]       │
│                         │                                             │
│                         └──► [Percorso B: altrimenti]               │
│                                                                       │
│  TIPI DI TRIGGER:                                                    │
│  • Schedule    → ogni N minuti/ore/giorni                            │
│  • Webhook     → HTTP POST esterno                                   │
│  • Watch       → polling su servizio (Gmail, Drive, etc.)           │
│                                                                       │
│  CONTEGGIO OPERAZIONI:                                               │
│  Ogni esecuzione di un modulo = 1 operazione                         │
│  5 moduli × 100 trigger/mese = 500 operazioni/mese                  │
│                                                                       │
│  OTTIMIZZAZIONE:                                                      │
│  • Aggrega dati prima di usare molti moduli                          │
│  • Usa "Aggregator" per ridurre iterazioni                           │
│  • Filtra con Router prima di moduli costosi                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Scenario di Base

### A1 — Primo Scenario: Webhook → HTTP → Log

**Obiettivo**: ricevere un ordine via webhook, recuperare dettagli cliente via API, loggare su Google Sheet.

```
STEP BY STEP (interfaccia Make):

1. CREA NUOVO SCENARIO
   Dashboard → "+ Create a new scenario"
   Nome: "Lab01 - Order Processing"

2. AGGIUNGI TRIGGER: Webhooks
   - Clicca "+" → cerca "Webhooks"
   - Seleziona: "Custom Webhook"
   - Clicca "Add" → "Save"
   - COPIA l'URL del webhook generato (es: https://hook.eu1.make.com/xxxx)

3. INVIA RICHIESTA DI TEST
   Apri terminale:
   
   curl -X POST https://hook.eu1.make.com/TUOURL \
     -H "Content-Type: application/json" \
     -d '{
       "ordine_id": "ORD-001",
       "cliente_id": "CLT-042",
       "importo": 149.90,
       "valuta": "EUR"
     }'
   
   Make mostrerà "Waiting for data..." → invio → "1 bundle received"
   Clicca "OK"

4. AGGIUNGI MODULO: HTTP Request
   - Clicca "+" dopo il webhook
   - Cerca "HTTP" → seleziona "Make a request"
   - URL: https://jsonplaceholder.typicode.com/users/{{1.cliente_id}}
     (usa {{1.campo}} per mappare dati dal trigger precedente)
   - Method: GET
   - Salva

5. AGGIUNGI MODULO: Google Sheets (o Text Aggregator per test senza Google)
   - Per test senza Google: aggiungi "Tools → Set Variable"
   - Set: log = "Ordine {{1.ordine_id}} processato - Cliente: {{2.name}}"

6. ATTIVA LO SCENARIO
   Toggle "Scheduling" → ON → Interval: as soon as possible
```

### A2 — Mapping Dati in Make

```
SINTASSI MAPPING:
  {{numero_modulo.nome_campo}}
  
  Esempi:
  {{1.ordine_id}}           → campo "ordine_id" dal modulo 1 (webhook)
  {{2.name}}                → campo "name" dalla risposta HTTP modulo 2
  {{2.address.city}}        → campo annidato
  {{1.importo * 1.22}}      → espressione matematica (IVA 22%)
  {{if(1.importo > 100; "premium"; "standard")}}  → condizionale
  {{formatDate(1.data; "DD/MM/YYYY")}}  → formattazione data

FUNZIONI UTILI:
  toString(valore)          → converte in stringa
  toNumber(valore)          → converte in numero
  emptyArray               → array vuoto
  if(condizione; vero; falso)
  contains(stringa; ricerca)
  trim(stringa)
  upper(stringa) / lower(stringa)
  replace(stringa; da; a)
  substring(stringa; start; length)
  length(array o stringa)
  sum(array; campo)         → somma campo in array
  first(array)              → primo elemento
  last(array)               → ultimo elemento
```

---

## PART B — Routing e Condizioni

### B1 — Router Module (Percorsi Multipli)

```
SCENARIO: Ordine → Router → [Percorso A: importo > 500] / [Percorso B: altrimenti]

CONFIGURAZIONE ROUTER:
1. Aggiungi modulo "Router" dopo il trigger webhook
2. Clicca "+" dal Router per il Percorso A
   - Aggiungi filtro: Condition
     Field:     {{1.importo}}
     Operator:  greater than
     Value:     500
   - Aggiungi moduli per il percorso premium (email prioritaria, etc.)

3. Clicca "+" dal Router per il Percorso B (else/fallback)
   - Non aggiungere filtro = percorso di default
   - Moduli per ordini standard

BEST PRACTICE ROUTER:
• Ordina i percorsi dal più specifico al più generico
• Il percorso senza filtro è sempre l'ultimo (fallback)
• Non usare router per logica complessa → usa un API custom Python
• Max 3-4 percorsi prima che diventi illeggibile
```

### B2 — Iterator + Aggregator

```
CASO D'USO: Processare un array di prodotti nell'ordine

STRUTTURA:
  Webhook → [Iterator] → [Modulo per ogni prodotto] → [Aggregator] → Email

CONFIGURAZIONE ITERATOR:
1. Aggiungi "Flow Control → Iterator"
2. Array: {{1.prodotti}}  (array di oggetti nel payload webhook)
3. Il modulo dopo l'Iterator riceve UN prodotto alla volta

CONFIGURAZIONE AGGREGATOR:
1. Aggiungi "Flow Control → Array Aggregator" dopo i moduli iterati
2. Source module: seleziona il modulo iterator
3. Aggregated fields: seleziona i campi da raccogliere

NOTA SULLE OPERAZIONI:
  Se l'ordine ha 10 prodotti e lo scenario ha 3 moduli dopo l'iterator:
  3 moduli × 10 iterazioni = 30 operazioni/esecuzione
  Con 100 ordini/giorno = 3000 operazioni/giorno = 90.000/mese!
  
  OTTIMIZZAZIONE: elabora prodotti in batch via API custom
  invece di iterare in Make.
```

---

## PART C — Error Handling

### C1 — Error Handler Modulo

```
MAKE GESTIONE ERRORI:
  
  Per default: se un modulo fallisce, lo scenario si ferma e segnala errore.
  
  AGGIUNGERE ERROR HANDLER:
  1. Click destro su qualsiasi modulo → "Add error handler"
  2. Scegli tipo:
     • Resume: ignora l'errore, continua
     • Commit: salva progresso fino a quel punto, ferma esecuzione
     • Rollback: annulla tutti i commit di questa esecuzione
     • Break: ferma esecuzione, marca come incomplete (retry possibile)
     • Ignore: salta il modulo che ha fallito
  
  CONFIGURAZIONE BREAK (la più utile per retry):
  1. Aggiungi "Break" come error handler
  2. Settings:
     - Number of attempts: 3
     - Interval between attempts: 10 minutes
  3. Make riproverà automaticamente 3 volte ogni 10 minuti
  
  CASO D'USO BREAK:
  - API esterna temporaneamente down
  - Timeout rete
  - Rate limit 429 (Make gestisce automaticamente con Break)
  
  CASO D'USO IGNORE:
  - Record duplicato già esistente (es. upsert)
  - Dati opzionali mancanti
  
  ERRORI NON RETRIABLE (usa Commit o Ignore):
  - Dati invalidi (400 Bad Request)
  - Risorsa non trovata (404)
  - Autenticazione fallita (401/403)
```

---

## PART D — Data Store (Storage Interno)

### D1 — Configurazione Data Store

```
DATA STORE IN MAKE:
  Un semplice key-value store integrato in Make.
  Utile per: stato di elaborazione, deduplicazione, piccole cache.
  Limite: 1 MB free, 1 record = 1 operazione.
  
  CREARE DATA STORE:
  1. Tools → Data Stores
  2. "+ Add Data Store"
  3. Definisci struttura:
     - ordine_id: Text (Primary key)
     - stato: Text
     - processato_at: Date
     - tentativo: Number

  USARE NEL SCENARIO:
  Modulo: "Data Store → Search Records"
    - Data Store: seleziona il tuo store
    - Filter: ordine_id = {{1.ordine_id}}
    - Se trovato: skip (già processato)
    - Se non trovato: processa e poi "Add/Replace Record"
  
  PATTERN IDEMPOTENZA:
  [Webhook] → [DS: cerca ordine_id] 
                │
                ├── Trovato → [Fine: già processato]
                │
                └── Non trovato → [Processa] → [DS: salva ordine_id + stato]
  
  CLEANUP (importante!):
  Aggiungi job schedulato settimanale che cancella record > 7 giorni
  per non riempire il Data Store (1 MB limit su piano free).
```

---

## Esercizi

### Esercizio 1 — Webhook + Deduplicazione (30 min)

Costruisci uno scenario Make che:
1. Riceve un ordine via webhook
2. Controlla nel Data Store se `ordine_id` è già presente
3. Se presente: risponde con `{"status": "duplicate", "ordine_id": "..."}` 
4. Se nuovo: salva nel Data Store, chiama API di test, risponde con `{"status": "ok"}`

Test con curl inviando lo stesso payload due volte.

### Esercizio 2 — Alert Budget Operazioni (20 min)

Configura un secondo scenario che:
- Si esegue ogni lunedì alle 9:00
- Legge il contatore operazioni via Make API: `GET /v2/scenarios`
- Se `operations_used > budget * 0.8` → invia email di allerta

### Esercizio 3 — Blueprint JSON Analisi (15 min)

Esporta uno scenario esistente (Blueprint → Download):
```json
// Struttura del blueprint Make (JSON esportato)
{
  "name": "Lab Scenario",
  "flow": [...],     // Array di moduli
  "metadata": {
    "version": 1,
    "scenario": {
      "dlq": true,
      "maxErrors": 3
    }
  }
}
```
Analizza:
- Quanti moduli ha il scenario?
- Che tipo di trigger usa?
- Ci sono Error Handler configurati?

---

## Note di Sicurezza Make

```
CONFIGURAZIONI SICUREZZA OBBLIGATORIE:
1. Webhook: aggiungi sempre "IP filter" se il sender è noto
2. HTTP modules: usa "Data Transfer Objects" per validare payload
3. Secrets: usa "Team Variables" (Encrypt = ON) non hardcode nelle config
4. Data Store: non salvare PII (nomi, email, CF) — solo ID opachi
5. Log scenari: Make mantiene log 1 mese — non loggare segreti nel payload

GDPR IN MAKE:
• Scegli region EU (eu1.make.com) per dati EU
• In alcune zone Make passa i dati per server US — verifica DPA
• Per dati ultra-sensibili: preferisci n8n self-hosted
```

---

## Riferimenti

- Make Academy: https://www.make.com/en/academy
- Make Help Center: https://www.make.com/en/help
- Blueprint Reference: documentazione JSON scenario
- Modulo sorgente: `10-make-integromat-guida-operativa.md`
