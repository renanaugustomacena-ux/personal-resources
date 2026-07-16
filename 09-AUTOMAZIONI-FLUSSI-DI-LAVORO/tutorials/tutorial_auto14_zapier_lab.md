# Tutorial Lab — Zapier: Zap Multi-Step, Filter, Path e Webhooks

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `14-zapier-guida-operativa.md`
> **Livello:** beginner → intermediate
> **Tempo stimato:** 2 ore
> **Prerequisiti:** Account Zapier (piano Free o Trial), concetti HTTP di base
> **Versioni di riferimento:** Zapier — versione corrente cloud (2025/2026)

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Costruire Zap multi-step con Trigger + Actions concatenate
2. Usare Filter e Path per routing condizionale
3. Applicare Formatter per trasformare dati (testo, numeri, date, array)
4. Configurare Webhooks by Zapier per integrazioni HTTP custom
5. Ottimizzare il consumo di task e analizzare i limiti del piano
6. Testare e debuggare Zap con il Zap History

---

## Lab Environment Setup

```
PREREQUISITI:
1. Account Zapier gratuito: https://zapier.com/sign-up
   Piano Free: 100 task/mese, 5 Zap massimi, aggiornamento ogni 15 minuti
   Piano Professional: 750 task/mese, Zap illimitati, aggiornamento ogni minuto

2. JSONPlaceholder (API di test): https://jsonplaceholder.typicode.com
   Nessun account richiesto — API REST pubblica

3. Webhook tester: https://webhook.site
   Nessun account per test temporanei

NOTA: Zapier è una piattaforma SaaS cloud — non eseguibile localmente.
      Le istruzioni descrivono l'interfaccia web.

TERMINOLOGIA ZAPIER:
  Zap    → un'automazione completa (trigger + azioni)
  Task   → ogni volta che un'azione viene eseguita con successo = 1 task
  Trigger → evento che avvia il Zap
  Action  → operazione eseguita dal Zap
  Step    → uno qualsiasi tra trigger, action, filter, path
```

---

## Analogia Introduttiva

> **Zapier è come un servizio postale universale con smistatori intelligenti**:
> ogni pacchetto (dato) entra dal trigger (mittente),
> passa per filtri e smistatori (filter, path, formatter),
> e viene consegnato a destinazioni diverse (Gmail, Slack, Google Sheets, etc.).
>
> La bellezza di Zapier è la capillarità: **6000+ corrieri partner** (app connesse).
> Se vuoi mandare un pacchetto da Typeform a HubSpot passando per Slack,
> Zapier ha già il percorso pronto — nessuna configurazione API manuale.
>
> Il limite: **1 task = 1 operazione**. Con 100 task/mese gratuiti,
> basta un Zap con 3 azioni eseguito 34 volte per consumare tutto il budget.
> Sii chirurgico nel design: meno step, più valore per task.

---

## Architettura di uno Zap

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STRUTTURA ZAP (logica)                            │
│                                                                       │
│  [1. Trigger]                                                         │
│      │   "Nuova riga in Google Sheet"                                │
│      ▼                                                                │
│  [2. Filter] ← NON consuma task se NON passa                         │
│      │   "Importo > 100"                                             │
│      ▼ (passa solo se condizione vera)                               │
│  [3. Formatter]                                                       │
│      │   "Formatta data in DD/MM/YYYY"                              │
│      ▼                                                                │
│  [4. Path] ← Branch condizionale                                     │
│      ├─── Path A: "Cliente VIP" → Slack + CRM                        │
│      └─── Path B: "Cliente standard" → solo Email                    │
│                                                                       │
│  CONTEGGIO TASK:                                                     │
│  • Trigger: 0 task (non conta)                                       │
│  • Filter: 0 task (non conta, ma ferma il Zap se non passa)          │
│  • Ogni Action/Formatter/Path: 1 task ciascuno                       │
│  • Path A con 2 azioni: 3 task (path + 2 azioni)                    │
│                                                                       │
│  OTTIMIZZAZIONE:                                                      │
│  • Usa Filter il prima possibile per fermare Zap inutili             │
│  • Raggruppa azioni correlate nello stesso Zap                        │
│  • Per volumi alti: considera n8n self-hosted (zero task fee)        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Primo Zap Multi-Step

### A1 — Webhook → Filter → Google Sheets

**Obiettivo**: ricevere ordini via webhook, filtrare solo quelli con importo > 50€, salvarli in Google Sheets.

```
STEP BY STEP:

1. CREA NUOVO ZAP
   Dashboard → "+ Create Zap"

2. CONFIGURA TRIGGER: Webhooks by Zapier
   - Cerca "Webhooks by Zapier" → seleziona "Catch Hook"
   - Clicca "Continue"
   - COPIA l'URL del webhook (es: https://hooks.zapier.com/hooks/catch/xxxx/yyyy/)
   
3. INVIA RICHIESTA DI TEST
   Apri terminale locale:
   
   curl -X POST https://hooks.zapier.com/hooks/catch/TUOURL/ \
     -H "Content-Type: application/json" \
     -d '{
       "ordine_id": "ORD-001",
       "cliente": "Mario Rossi",
       "importo": 149.90,
       "prodotto": "Laptop Pro",
       "data": "2026-01-15"
     }'
   
   In Zapier: "Test trigger" → dovrebbe mostrare i dati ricevuti
   Clicca "Continue with selected record"

4. AGGIUNGI FILTER (passo 2)
   - Clicca "+" → "Filter"
   - Condition: (importo) (Number) Greater than (50)
   - Clicca "Continue"
   - Test: "Filter would pass with the test record" → OK

5. AGGIUNGI ACTION: Google Sheets
   - Cerca "Google Sheets" → "Create Spreadsheet Row"
   - Connetti account Google (autorizzazione OAuth)
   - Spreadsheet: seleziona o crea "Ordini Lab"
   - Worksheet: "Foglio1"
   - Mappa colonne:
     A (Ordine ID): {{ordine_id}}
     B (Cliente): {{cliente}}
     C (Importo): {{importo}}
     D (Prodotto): {{prodotto}}
     E (Data): {{data}}
   
6. TESTA E ATTIVA
   "Test step" → controlla che la riga appaia in Google Sheets
   "Publish Zap" → Toggle ON
```

### A2 — Mapping Dati in Zapier

```
SINTASSI MAPPING:
  In ogni campo azione, clicca l'icona "+" per inserire dati da step precedenti.
  Ogni campo dati è rappresentato come {{nome_campo}}.
  
  ESEMPI:
  {{ordine_id}}                     → dati dal trigger
  {{2__importo}}                    → importo dallo step 2 (se diverso dal trigger)
  {{zap_meta__humanize_runtime}}    → metadata Zapier
  
  NOTA: in Zapier non scrivi espressioni manualmente come in Make.
  Usi sempre il dropdown "Insert Data" per selezionare i campi disponibili.
  Per trasformazioni → usa Formatter (vedi PART B).

DATI SPECIALI:
  zap_meta__utc_now                 → timestamp ISO 8601 corrente
  zap_meta__zap_id                  → ID del Zap
  zap_meta__run_id                  → ID dell'esecuzione corrente
```

---

## PART B — Formatter: Trasformazione Dati

### B1 — Formatter by Zapier

```
IL FORMATTER è lo strumento di trasformazione di Zapier.
Ogni uso del Formatter = 1 task (attenzione al budget!).

TIPI DI FORMATTER:
  Numbers  → formattazione numeri
  Dates    → conversione e formattazione date
  Text     → manipolazione testo
  Utilities → split, lookup, line items
  
ESEMPI PRATICI:

--- NUMBERS ---
Action: Format
Transform: To Fixed Decimal Point
Decimal Places: 2
Input: {{importo}}  → "149.90"

Action: Perform Math Operation
Input: {{importo}}
Math Operation: Multiply
Value: 1.22
Output: {{importo_ivato}}  → "182.878"

--- TEXT ---
Action: Transform Text
Input: {{cliente}}
Transform: Titlecase
Output: "Mario Rossi"  (dalla maiuscola ogni parola)

Action: Split Text
Input: "Mario,Rossi,mario@email.com"
Separator: ,
Segment Index: 1   → "Rossi" (0-indexed)

Action: Find + Replace
Input: {{descrizione}}
Find: "non disponibile"
Replace: "esaurito"

--- DATES ---
Action: Format Date
Input: {{data}}       → "2026-01-15"
From Format: YYYY-MM-DD
To Format: DD/MM/YYYY
Output: "15/01/2026"

Action: Add/Subtract Time
Input: {{data_ordine}}
Expression: +30 days   → aggiunge 30 giorni (data scadenza)

--- UTILITIES ---
Action: Lookup Table
Lookup Key: {{codice_paese}}
Lookup Table: IT = Italia | DE = Germania | FR = Francia
Output: "Italia"

Action: Line Item to Text
Input: {{lista_prodotti}}  → array
Separator: \n
Output: "Prodotto A\nProdotto B\nProdotto C"
```

---

## PART C — Path: Routing Condizionale

### C1 — Configurazione Path

```
PATH = rami alternativi condizionali nel Zap
Ogni Path = 1 task (più le azioni dentro)

STRUTTURA:
  [Trigger] → [Filter] → [Path]
                              ├── [Path A: Cliente VIP] → Slack + Salesforce (2 task)
                              ├── [Path B: Cliente standard] → solo Email (1 task)
                              └── [Path C: else] → Log errore (1 task)
  
  Totale per esecuzione che entra in Path A: 1 (path) + 2 (azioni) = 3 task

STEP BY STEP:

1. Nel Zap, dopo il Trigger/Filter, clicca "+" → "Paths"

2. PATH A (primo ramo):
   Clicca sul ramo "Path A" → "Set up rules for this path"
   Condition:
     (1. campo: {{tipo_cliente}})
     (Condition: Text contains)
     (Value: VIP)
   
   Aggiungi azioni per il path A:
   - Post message in Slack: "#vendite-vip"
   - Update contact in Salesforce

3. PATH B (secondo ramo):
   Clicca "Add path" → "Set up rules for this path"
   Condition:
     (1. campo: {{tipo_cliente}})
     (Condition: Text does not contain)
     (Value: VIP)
   
   Azione:
   - Send email via Gmail/Outlook

4. (Opzionale) PATH C — Fallback senza condizione
   Clicca "Add path" → NON aggiungere regole = percorso else

BEST PRACTICE PATH:
• Usa il path "else" (senza condizione) come catch-all per debugging
• Non creare più di 5 path: diventa illeggibile
• I path sono eseguiti nell'ordine — il primo che matcha vince
• Per logica complessa → usa Code by Zapier o un endpoint Python custom
```

---

## PART D — Webhooks e Integrazioni HTTP

### D1 — Webhooks by Zapier come Sender

```
CASO D'USO: Zapier chiama la tua API custom come azione

Aggiungi step: "Webhooks by Zapier" → Action event: "POST"
  URL: https://tua-api.esempio.com/ordini
  Payload Type: JSON
  Data: {
    "ordine_id": {{ordine_id}},
    "importo": {{importo}},
    "timestamp": {{zap_meta__utc_now}}
  }
  Headers: Authorization: Bearer {{secrets__api_key}}
           Content-Type: application/json
  Basic Auth: (vuoto se usi Bearer token)

RISPOSTA HTTP:
  Zapier espone la risposta come {{response_body}}, {{response_status}}
  Puoi mappare campi dalla risposta JSON negli step successivi
  
  NOTA: "Webhooks by Zapier" è un'app PREMIUM (richiede piano a pagamento)
  Per piano gratuito: usa app native (Slack, Gmail, etc.) che fanno HTTP internamente

--- ALTERNATIVA GRATUITA ---
"Email by Zapier" → invia email a indirizzo webhook dedicato
"RSS by Zapier" → polling RSS come alternativa ai webhook per fetch periodici

SIMULARE WEBHOOK SENDER IN LOCALE (per test):
  # Server locale Python (Flask)
  from flask import Flask, request, jsonify
  app = Flask(__name__)
  
  @app.route('/trigger', methods=['POST'])
  def trigger():
      data = request.get_json()
      print(f"Ricevuto: {data}")
      return jsonify({"status": "ok"})
  
  if __name__ == '__main__':
      app.run(port=5000)
  
  # Con ngrok per esporre localmente:
  # ngrok http 5000
  # → usa l'URL https://xxxx.ngrok.io come trigger URL in Zapier
```

### D2 — Zap History e Debugging

```
ZAP HISTORY (log esecuzioni):
  Dashboard → seleziona Zap → "Zap history"
  
  COLORI:
  • Verde: esecuzione completata con successo
  • Grigio: il Filter ha fermato l'esecuzione (non è un errore)
  • Rosso: errore in uno degli step
  
  DEBUGGING:
  1. Clicca su una esecuzione rossa
  2. Espandi lo step fallito
  3. Leggi "Error" e "Input/Output data"
  
  ERRORI COMUNI:
  
  "Authentication failed" → riautentica l'app:
    Zap editor → step fallito → Account → Reconnect
  
  "The value is required" → campo obbligatorio vuoto:
    Controlla che il dato del trigger sia sempre presente
    Usa "Default value" nei campi opzionali
  
  "Rate limit exceeded" → troppi Zap verso la stessa app:
    Zapier gestisce automaticamente il backoff
    In caso persistente: aggiungi "Delay by Zapier" (1-5 min prima dell'azione)
  
  "Invalid data format" → il tipo di dato non corrisponde:
    Usa Formatter per convertire prima dell'azione problematica

REPLAY:
  Clicca su esecuzione fallita → "Replay" per rieseguire con stessi dati
  Utile dopo aver corretto la configurazione.
```

---

## Esercizi

### Esercizio 1 — Pipeline Lead Management (30 min)

Crea un Zap che:
1. **Trigger**: Webhooks by Zapier → Catch Hook
2. **Formatter**: trasforma `{{email}}` in minuscolo + `{{nome}}` in Titlecase
3. **Filter**: passa solo se `{{email}}` contiene "@" (validazione base)
4. **Path A**: se `{{budget}}` > 5000 → Slack in #lead-enterprise + Google Sheets "Lead Enterprise"
5. **Path B**: altrimenti → solo Google Sheets "Lead Standard"

Testa con curl:
```bash
curl -X POST https://hooks.zapier.com/hooks/catch/TUOURL/ \
  -H "Content-Type: application/json" \
  -d '{"nome": "mario rossi", "email": "MARIO@EMPRESA.COM", "budget": 10000}'
```

### Esercizio 2 — Analisi Consumo Task (15 min)

Nel tuo account Zapier:
- Dashboard → Usage → verifica task consumati questo mese
- Vai su Zap History del tuo Zap più attivo
- Calcola: quante esecuzioni/giorno? Quanti task/esecuzione? 
- Proietta: arriverai al limite entro il mese?

### Esercizio 3 — Webhook Relay (Python locale) (20 min)

Scrivi un server Flask locale che:
1. Riceve POST su `/ordine` con JSON `{"ordine_id", "importo", "cliente"}`
2. Valida che `importo > 0` e `cliente` non sia vuoto
3. Se valido: fa POST al tuo Webhook Zapier con i dati puliti
4. Se non valido: risponde `{"error": "dati non validi"}` senza chiamare Zapier

```python
# server_relay.py — da completare come esercizio
from flask import Flask, request, jsonify
import httpx

app = Flask(__name__)
ZAPIER_WEBHOOK_URL = "https://hooks.zapier.com/hooks/catch/TUOURL/"

@app.route('/ordine', methods=['POST'])
def ricevi_ordine():
    data = request.get_json()
    # TODO: validazione
    # TODO: relay a Zapier
    # TODO: return risposta appropriata
    pass

if __name__ == '__main__':
    app.run(port=5001, debug=True)
```

---

## Confronto Rapido: Zapier vs Make vs n8n

```
┌────────────────┬──────────────┬──────────────┬──────────────────────┐
│                │   Zapier     │     Make     │   n8n (self-hosted)  │
├────────────────┼──────────────┼──────────────┼──────────────────────┤
│ App connesse   │ 6000+        │ 2000+        │ 400+ (cresce)        │
│ Piano gratuito │ 100 task/mese│ 1000 ops/mese│ illimitato           │
│ Curva apprendim│ Bassa        │ Media        │ Media-Alta           │
│ Trigger polling│ 15 min       │ 15 min       │ Configurabile        │
│ HTTP custom    │ Premium      │ Incluso      │ Incluso              │
│ Logica avanzata│ Limitata     │ Media        │ Alta (JS/Python)     │
│ Dati in EU     │ US (no GDPR) │ EU opzionale │ Totale controllo     │
│ Costo a volume │ Alto         │ Medio        │ Solo infrastruttura  │
└────────────────┴──────────────┴──────────────┴──────────────────────┘

QUANDO SCEGLIERE ZAPIER:
✓ Vuoi connettere 2 app mainstream in 5 minuti
✓ Il team non ha competenze tecniche
✓ Volume basso (<500 task/mese)
✓ L'integrazione esiste già in Zapier app store

QUANDO NON SCEGLIERE ZAPIER:
✗ Volumi alti (il costo scala linearmente con i task)
✗ Logica condizionale complessa (meglio Make o n8n)
✗ GDPR rigoroso (dati transitano server US)
✗ Integrazioni custom via API (richiede piano Premium)
```

---

## Riferimenti

- Zapier Help Center: https://help.zapier.com
- Zapier University: https://zapier.com/university
- Webhooks by Zapier: https://zapier.com/apps/webhook/integrations
- Formatter Guide: https://zapier.com/apps/formatter/integrations
- Modulo sorgente: `14-zapier-guida-operativa.md`
